from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_whole_workload_budget_extension_v16 import (
    WholeWorkloadBudgetExtensionV16Error,
    current_status,
    evaluate_payload,
    validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]


def _payload(
    *,
    observed: str = "2026-08-09T00:00:00Z",
    evaluated: str = "2026-08-09T00:15:00Z",
) -> dict[str, object]:
    return {
        "quote": {
            "quote_observed_at_utc": observed,
            "compute_hourly_rate_usd": 0.56,
            "billing_granularity_seconds": 60,
            "minimum_billable_seconds": 60,
            "storage_fee_usd": 0.06944444444444443,
            "network_fee_usd": 0.0,
            "platform_or_other_fee_usd": 0.0,
            "tax_or_surcharge_usd": 0.0,
        },
        "prior_spend_usd": {
            "common_screen": 0.0,
            "a1_total": 0.0,
            "campaign": 0.0,
        },
        "workload": {
            "arm_ids": ["ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05"],
            "expected_program_arm_runs": 25,
            "partial_arm_admission": False,
        },
        "evaluated_at_utc": evaluated,
    }


def test_v16_policy_and_status_are_locked_until_fresh_live_admission() -> None:
    policy = validate_contract(ROOT)
    assert policy["approved_limits"] == {
        "currency": "USD",
        "hard_stops_usd": {"common_screen": 27, "a1_total": 32, "campaign": 150},
        "owner_ttl_hours": 40,
        "ttl_basis": "FROM_INSTANCE_PROVISION",
        "whole_workload_required": True,
        "partial_arm_admission_allowed": False,
        "quote_max_age_seconds": 900,
    }
    status = current_status(ROOT)
    assert status["provider_contact_allowed"] is False
    assert status["launch_allowed"] is False
    assert status["adopted_for_execution"] is False
    assert status["measured_runs"] == 0
    assert status["charged_usd"] == 0


def test_v16_keeps_historical_v15_caps_and_ttl_unchanged() -> None:
    historical = json.loads(
        (ROOT / "control/armindex/a1.2/whole-workload-budget-model.v15.json").read_text(
            encoding="utf-8"
        )
    )
    assert historical["frozen_hard_stops_usd"] == {
        "common_screen": 18,
        "a1_total": 23,
        "campaign": 100,
    }
    assert historical["execution_window"]["owner_ttl_hours"] == 20


def test_exact_forty_hour_all_fee_formula_passes_budget_only() -> None:
    receipt = evaluate_payload(
        ROOT,
        _payload(),
        receipt_id="a1.2-whole-workload-budget-extension-pass-v16",
    )
    assert receipt["status"] == "PASS_BUDGET_ADMISSION_LOCKED"
    assert receipt["admitted"] is True
    assert receipt["ttl_hours"] == 40
    assert receipt["billable_seconds"] == 144000
    assert receipt["worst_case_ttl_charge_usd"] == pytest.approx(
        22.469444444444443
    )
    assert receipt["hard_stops_usd"] == {
        "common_screen": 27,
        "a1_total": 32,
        "campaign": 150,
    }
    assert receipt["failure_reasons"] == []
    assert receipt["provider_contact_allowed"] is False
    assert receipt["launch_allowed"] is False
    assert receipt["adopted_for_execution"] is False
    assert receipt["preparation_counters"]["measured_runs"] == 0


def test_common_screen_overrun_is_blocked() -> None:
    payload = _payload()
    payload["prior_spend_usd"] = {
        "common_screen": 5.0,
        "a1_total": 0.0,
        "campaign": 0.0,
    }
    receipt = evaluate_payload(
        ROOT,
        payload,
        receipt_id="a1.2-whole-workload-budget-extension-common-blocked-v16",
    )
    assert receipt["admitted"] is False
    assert receipt["status"] == "BLOCKED_BUDGET"
    assert "common_screen_hard_stop_exceeded" in receipt["failure_reasons"]


def test_stale_quote_and_partial_workload_are_blocked() -> None:
    payload = _payload(
        observed="2026-08-08T00:00:00Z", evaluated="2026-08-09T00:00:01Z"
    )
    payload["workload"]["partial_arm_admission"] = True  # type: ignore[index]
    receipt = evaluate_payload(
        ROOT,
        payload,
        receipt_id="a1.2-whole-workload-budget-extension-stale-v16",
    )
    assert receipt["status"] == "BLOCKED_BUDGET"
    assert "stale_quote" in receipt["failure_reasons"]
    assert "partial_workload_admission_forbidden" in receipt["failure_reasons"]


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value["quote"].pop("tax_or_surcharge_usd"),
        lambda value: value["quote"].update({"unknown_fee_usd": 0.0}),
        lambda value: value["quote"].update({"network_fee_usd": -0.1}),
        lambda value: value.update({"provider_instance_id": "forbidden"}),
    ],
)
def test_missing_unknown_negative_or_provider_inputs_are_rejected(
    mutate: object,
) -> None:
    payload = _payload()
    mutate(payload)  # type: ignore[operator]
    with pytest.raises(WholeWorkloadBudgetExtensionV16Error):
        evaluate_payload(
            ROOT,
            payload,
            receipt_id="a1.2-whole-workload-budget-extension-invalid-v16",
        )


def test_result_is_deterministic_and_self_hash_bound() -> None:
    first = evaluate_payload(
        ROOT,
        _payload(),
        receipt_id="a1.2-whole-workload-budget-extension-repeat-v16",
    )
    second = evaluate_payload(
        ROOT,
        copy.deepcopy(_payload()),
        receipt_id="a1.2-whole-workload-budget-extension-repeat-v16",
    )
    assert first == second
    assert len(first["receipt_sha256"]) == 64
