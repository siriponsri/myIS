from __future__ import annotations

import copy
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_whole_workload_budget_extension_v17 import (
    WholeWorkloadBudgetExtensionV17Error,
    current_status,
    evaluate_payload,
    validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]
ONE_ATTEMPT_ALL_FEE_USD = 22.469444444444443


def _payload(
    *,
    observed: str = "2026-08-11T00:00:00Z",
    evaluated: str = "2026-08-11T00:15:00Z",
    prior_common_screen: float = ONE_ATTEMPT_ALL_FEE_USD,
    prior_a1_total: float = ONE_ATTEMPT_ALL_FEE_USD,
    prior_campaign: float = ONE_ATTEMPT_ALL_FEE_USD,
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
        "prior_attempt_spend_usd": {
            "attempt_count": 1,
            "accounting_basis": "ALL_FEE_DESTROYED_ATTEMPT_TOTAL",
            "common_screen": prior_common_screen,
            "a1_total": prior_a1_total,
            "campaign": prior_campaign,
        },
        "workload": {
            "arm_ids": ["ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05"],
            "expected_program_arm_runs": 25,
            "partial_arm_admission": False,
        },
        "evaluated_at_utc": evaluated,
    }


def test_v17_policy_requires_prior_destroyed_attempt_and_keeps_execution_locked() -> None:
    policy = validate_contract(ROOT)
    assert policy["historical_v16"]["hard_stops_usd"] == {
        "common_screen": 27,
        "a1_total": 32,
        "campaign": 150,
    }
    assert policy["approved_limits"] == {
        "currency": "USD",
        "hard_stops_usd": {"common_screen": 55, "a1_total": 60, "campaign": 150},
        "owner_ttl_hours": 40,
        "ttl_basis": "FROM_INSTANCE_PROVISION",
        "whole_workload_required": True,
        "partial_arm_admission_allowed": False,
        "quote_max_age_seconds": 900,
    }
    assert policy["prior_attempt_accounting"] == {
        "required_prior_attempt_count": 1,
        "accounting_basis": "ALL_FEE_DESTROYED_ATTEMPT_TOTAL",
        "current_ttl_charge_added_to_every_hard_stop": True,
        "aggregate_only": True,
    }
    status = current_status(ROOT)
    assert status["required_prior_attempt_count"] == 1
    assert status["provider_contact_allowed"] is False
    assert status["launch_allowed"] is False
    assert status["adopted_for_execution"] is False
    assert status["measured_runs"] == 0


def test_two_attempt_conservative_all_fee_admission_passes() -> None:
    receipt = evaluate_payload(
        ROOT,
        _payload(),
        receipt_id="a1.2-whole-workload-budget-extension-two-attempt-pass-v17",
    )
    assert receipt["status"] == "PASS_BUDGET_ADMISSION_LOCKED"
    assert receipt["admitted"] is True
    assert receipt["prior_attempt_count"] == 1
    assert receipt["prior_attempt_spend_usd"] == {
        "common_screen": pytest.approx(ONE_ATTEMPT_ALL_FEE_USD),
        "a1_total": pytest.approx(ONE_ATTEMPT_ALL_FEE_USD),
        "campaign": pytest.approx(ONE_ATTEMPT_ALL_FEE_USD),
    }
    assert receipt["ttl_hours"] == 40
    assert receipt["billable_seconds"] == 144000
    assert receipt["worst_case_ttl_charge_usd"] == pytest.approx(
        ONE_ATTEMPT_ALL_FEE_USD
    )
    assert receipt["projected_spend_usd"] == {
        "common_screen": pytest.approx(44.93888888888889),
        "a1_total": pytest.approx(44.93888888888889),
        "campaign": pytest.approx(44.93888888888889),
    }
    assert receipt["failure_reasons"] == []
    assert receipt["provider_contact_allowed"] is False
    assert receipt["launch_allowed"] is False
    assert receipt["adopted_for_execution"] is False


@pytest.mark.parametrize(
    ("spend_field", "value", "reason"),
    [
        ("prior_common_screen", 32.6, "common_screen_hard_stop_exceeded"),
        ("prior_a1_total", 37.6, "a1_total_hard_stop_exceeded"),
        ("prior_campaign", 127.6, "campaign_hard_stop_exceeded"),
    ],
)
def test_conservative_two_attempt_over_cap_is_blocked(
    spend_field: str, value: float, reason: str
) -> None:
    receipt = evaluate_payload(
        ROOT,
        _payload(**{spend_field: value}),
        receipt_id="a1.2-whole-workload-budget-extension-over-cap-v17",
    )
    assert receipt["status"] == "BLOCKED_BUDGET"
    assert receipt["admitted"] is False
    assert reason in receipt["failure_reasons"]


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value["prior_attempt_spend_usd"].update({"attempt_count": 0}),
        lambda value: value["prior_attempt_spend_usd"].update(
            {"accounting_basis": "INCOMPLETE"}
        ),
        lambda value: value["prior_attempt_spend_usd"].pop("campaign"),
        lambda value: value["quote"].pop("tax_or_surcharge_usd"),
        lambda value: value.update({"provider_instance_id": "forbidden"}),
    ],
)
def test_missing_or_nonconservative_prior_accounting_is_rejected(
    mutate: object,
) -> None:
    payload = _payload()
    mutate(payload)  # type: ignore[operator]
    with pytest.raises(WholeWorkloadBudgetExtensionV17Error):
        evaluate_payload(
            ROOT,
            payload,
            receipt_id="a1.2-whole-workload-budget-extension-invalid-v17",
        )


def test_quote_over_900_seconds_old_is_blocked() -> None:
    receipt = evaluate_payload(
        ROOT,
        _payload(
            observed="2026-08-11T00:00:00Z",
            evaluated="2026-08-11T00:15:01Z",
        ),
        receipt_id="a1.2-whole-workload-budget-extension-stale-v17",
    )
    assert receipt["status"] == "BLOCKED_BUDGET"
    assert receipt["failure_reasons"] == ["stale_quote"]


def test_result_is_deterministic_and_self_hash_bound() -> None:
    first = evaluate_payload(
        ROOT,
        _payload(),
        receipt_id="a1.2-whole-workload-budget-extension-repeat-v17",
    )
    second = evaluate_payload(
        ROOT,
        copy.deepcopy(_payload()),
        receipt_id="a1.2-whole-workload-budget-extension-repeat-v17",
    )
    assert first == second
    assert len(first["receipt_sha256"]) == 64
