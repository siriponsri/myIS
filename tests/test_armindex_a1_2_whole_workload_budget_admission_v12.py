from __future__ import annotations

import copy
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_whole_workload_budget_admission_v12 import (
    WholeWorkloadBudgetAdmissionV12Error,
    current_status,
    evaluate_payload,
)


ROOT = Path(__file__).resolve().parents[1]


def _payload() -> dict[str, object]:
    return {
        "quote": {
            "quote_observed_at_utc": "2026-08-08T00:00:00Z",
            "compute_hourly_rate_usd": 0.6,
            "billing_granularity_seconds": 60,
            "minimum_billable_seconds": 60,
            "storage_fee_usd": 0.12,
            "network_fee_usd": 0.03,
            "platform_or_other_fee_usd": 0.05,
            "tax_or_surcharge_usd": 0.0,
        },
        "prior_spend_usd": {"common_screen": 0.0, "a1_total": 0.0, "campaign": 0.0},
        "workload": {"arm_ids": ["ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05"], "expected_program_arm_runs": 25, "partial_arm_admission": False},
        "evaluated_at_utc": "2026-08-08T00:15:00Z",
    }


def test_status_is_pending_and_execution_locked() -> None:
    status = current_status(ROOT)
    assert status["status"] == "PENDING_LIVE_PROVIDER"
    assert status["provider_contact_allowed"] is False
    assert status["launch_allowed"] is False
    assert status["adopted_for_execution"] is False


def test_exact_six_hour_all_fee_formula_and_prior_spend_admit_budget_only() -> None:
    payload = _payload()
    payload["prior_spend_usd"] = {"common_screen": 10.0, "a1_total": 12.0, "campaign": 30.0}
    receipt = evaluate_payload(ROOT, payload, receipt_id="a1.2-whole-workload-budget-admission-pass-v12")

    assert receipt["status"] == "PASS_BUDGET_ADMISSION_LOCKED"
    assert receipt["admitted"] is True
    assert receipt["billable_seconds"] == 21600
    assert receipt["worst_case_ttl_charge_usd"] == pytest.approx(3.8)
    assert receipt["projected_spend_usd"] == {"common_screen": 13.8, "a1_total": 15.8, "campaign": 33.8}
    assert receipt["failure_reasons"] == []
    assert receipt["provider_contact_allowed"] is False
    assert receipt["launch_allowed"] is False
    assert receipt["adopted_for_execution"] is False


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (lambda value: value.update({"evaluated_at_utc": "2026-08-08T00:15:01Z"}), "stale_quote"),
        (lambda value: value["workload"].update({"arm_ids": ["ARM-01", "ARM-02"]}), "partial_or_noncanonical_arm_set"),
        (lambda value: value["workload"].update({"partial_arm_admission": True}), "partial_workload_admission_forbidden"),
        (lambda value: value["prior_spend_usd"].update({"common_screen": 15.0}), "common_screen_hard_stop_exceeded"),
        (lambda value: value["prior_spend_usd"].update({"a1_total": 20.0}), "a1_total_hard_stop_exceeded"),
        (lambda value: value["prior_spend_usd"].update({"campaign": 99.0}), "campaign_hard_stop_exceeded"),
    ],
)
def test_policy_failures_return_blocked_budget(mutation: object, reason: str) -> None:
    payload = _payload()
    mutation(payload)  # type: ignore[operator]
    receipt = evaluate_payload(ROOT, payload, receipt_id="a1.2-whole-workload-budget-admission-blocked-v12")
    assert receipt["status"] == "BLOCKED_BUDGET"
    assert receipt["admitted"] is False
    assert reason in receipt["failure_reasons"]


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value["quote"].pop("tax_or_surcharge_usd"),
        lambda value: value["quote"].update({"unexpected_fee_usd": 0}),
        lambda value: value["quote"].update({"network_fee_usd": None}),
        lambda value: value["quote"].update({"storage_fee_usd": -0.01}),
        lambda value: value["quote"].update({"billing_granularity_seconds": 0}),
        lambda value: value.update({"provider_instance_id": "forbidden"}),
    ],
)
def test_missing_unknown_negative_or_unsafe_inputs_are_rejected(mutate: object) -> None:
    payload = _payload()
    mutate(payload)  # type: ignore[operator]
    with pytest.raises(WholeWorkloadBudgetAdmissionV12Error):
        evaluate_payload(ROOT, payload, receipt_id="a1.2-whole-workload-budget-admission-invalid-v12")


def test_future_quote_is_rejected() -> None:
    payload = _payload()
    payload["quote"]["quote_observed_at_utc"] = "2026-08-08T00:15:01Z"
    with pytest.raises(WholeWorkloadBudgetAdmissionV12Error, match="after evaluated"):
        evaluate_payload(ROOT, payload, receipt_id="a1.2-whole-workload-budget-admission-future-v12")


def test_result_is_deterministic_and_self_hash_bound() -> None:
    first = evaluate_payload(ROOT, _payload(), receipt_id="a1.2-whole-workload-budget-admission-repeat-v12")
    second = evaluate_payload(ROOT, copy.deepcopy(_payload()), receipt_id="a1.2-whole-workload-budget-admission-repeat-v12")
    assert first == second
    assert len(first["receipt_sha256"]) == 64
