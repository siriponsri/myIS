from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from myis_research.armindex import a2_three_primary_closeout as closeout
from myis_research.armindex.a2_execution_readiness import frozen_candidates
from myis_research.armindex.a2_measured_adapter import canonical_a1_incumbents
from myis_research.kernel.canonical import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
ATTEMPT = "a2-goal004-20260816-005"
PRIMARY_ARMS = ("ARM-03", "ARM-04", "ARM-05")
DIAGNOSTIC_ARMS = ("ARM-01", "ARM-02")


def _signed(value: dict[str, Any], field: str) -> dict[str, Any]:
    return {**value, field: canonical_sha256(value)}


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _receipts() -> dict[str, dict[str, Any]]:
    """Build only aggregate-safe synthetic candidate receipts for closeout validation."""

    candidates = frozen_candidates(ROOT)
    incumbents = canonical_a1_incumbents(ROOT)
    selected: dict[str, str] = {}
    for arm_id in PRIMARY_ARMS:
        selected[arm_id] = next(
            candidate_id
            for candidate_id, candidate in candidates.items()
            if candidate["arm_id"] == arm_id and candidate["tier"] == "matched"
        )
    diagnostic_ties = {
        arm_id: {
            candidate_id
            for candidate_id, candidate in candidates.items()
            if candidate["arm_id"] == arm_id and candidate["tier"] == "matched"
        }
        for arm_id in DIAGNOSTIC_ARMS
    }
    for arm_id in DIAGNOSTIC_ARMS:
        diagnostic_ties[arm_id] = set(sorted(diagnostic_ties[arm_id])[:3])

    receipts: dict[str, dict[str, Any]] = {}
    for candidate_id, candidate in candidates.items():
        arm_id = str(candidate["arm_id"])
        tier = str(candidate["tier"])
        active_reserve = tier == "conditional_reserve" and arm_id == "ARM-03"
        dormant_reserve = tier == "conditional_reserve" and arm_id != "ARM-03"
        status = "DORMANT_CONDITIONAL_RESERVE" if dormant_reserve else "PASS_A2_CANDIDATE_RESULT"
        score = Decimal("0")
        if arm_id in DIAGNOSTIC_ARMS and candidate_id in diagnostic_ties[arm_id]:
            score = Decimal("0.9")
        elif candidate_id == selected.get(arm_id):
            incumbent = Decimal(incumbents[arm_id]["primary_metric"])
            assert incumbent > 0
            score = incumbent if arm_id == "ARM-05" else incumbent + Decimal("0.01")
        reserve_evidence = "d" * 64 if tier == "conditional_reserve" else None
        body = {
            "schema_version": "myis.armindex-a2-candidate-result-receipt.v1",
            "receipt_id": f"{ATTEMPT}-{candidate_id.removeprefix('a2-')}-candidate-result-v1",
            "attempt_id": ATTEMPT,
            "status": status,
            "evidence_class": "measured_development_aggregate",
            "scientific_authority": True,
            "candidate_id": candidate_id,
            "arm_id": arm_id,
            "tier": tier,
            "program_sha256": "a" * 64,
            "executor_output_sha256": "b" * 64,
            "evaluator_input_sha256": "c" * 64,
            "evaluator_sha256": "d" * 64,
            "code_sha256": "e" * 64,
            "model_sha256": "f" * 64,
            "data_sha256": "0" * 64,
            "primary_metric": None if dormant_reserve else {"name": "recall_at_100/out", "value": _decimal_text(score)},
            "secondary_metrics": None,
            "latency": None,
            "cost": None,
            "coverage": {"expected_units": 1, "completed_units": 0 if dormant_reserve else 1},
            "resume_count": 0,
            "failure_count": 0,
            "reserve_activation_passed": active_reserve,
            "reserve_activation_evidence_sha256": reserve_evidence,
            "train_only": False,
            "rep_dev_measured": True,
            "protected_payload_included": False,
            "per_query_outcomes_included": False,
            "freeze_bindings": closeout._FROZEN_BINDINGS,
        }
        receipts[candidate_id] = _signed(body, "receipt_sha256")
    return receipts


def test_three_primary_exact_44_plus_8_zero_failure_and_dispositions() -> None:
    coverage = closeout.build_three_primary_coverage(ROOT, receipts_by_candidate=_receipts())

    assert (
        coverage["candidate_count"],
        coverage["measured_candidate_count"],
        coverage["dormant_conditional_reserve_count"],
        coverage["failed_candidate_count"],
    ) == (52, 44, 8, 0)
    assert set(coverage["primary_winner_receipts"]) == set(PRIMARY_ARMS)
    for arm_id in DIAGNOSTIC_ARMS:
        receipt = coverage["diagnostic_no_winner_receipts"][arm_id]
        assert receipt["top_tie_count"] == 3
        assert receipt["strict_tie_rejected"] is True
        assert receipt["advancement_eligible"] is False
    arm_five_proof = coverage["primary_improvement_proofs"]["ARM-05"]
    assert arm_five_proof["strict_primary_improvement"] is False
    assert arm_five_proof["a1_comparison"] == "NO_STRICT_IMPROVEMENT"
    assert coverage["coverage_sha256"] == canonical_sha256(
        {key: value for key, value in coverage.items() if key != "coverage_sha256"}
    )


def test_diagnostic_arm_unique_top_is_rejected_instead_of_making_a_winner() -> None:
    receipts = _receipts()
    candidate_id = next(
        candidate_id
        for candidate_id, candidate in frozen_candidates(ROOT).items()
        if candidate["arm_id"] == "ARM-01" and candidate["tier"] == "matched"
        and receipts[candidate_id]["primary_metric"]["value"] != "0.9"
    )
    body = {key: value for key, value in receipts[candidate_id].items() if key != "receipt_sha256"}
    body["primary_metric"] = {"name": "recall_at_100/out", "value": "1"}
    receipts[candidate_id] = _signed(body, "receipt_sha256")

    with pytest.raises(closeout.A2ThreePrimaryCloseoutError, match="diagnostic arm must retain"):
        closeout.build_three_primary_coverage(ROOT, receipts_by_candidate=receipts)


def test_candidate_and_coverage_receipt_hash_and_schema_drift_are_rejected() -> None:
    receipts = _receipts()
    receipts[next(iter(receipts))]["receipt_sha256"] = "0" * 64
    with pytest.raises(closeout.A2ThreePrimaryCloseoutError, match="candidate receipt self-hash drift"):
        closeout.build_three_primary_coverage(ROOT, receipts_by_candidate=receipts)

    coverage = closeout.build_three_primary_coverage(ROOT, receipts_by_candidate=_receipts())
    malformed = deepcopy(coverage)
    malformed["failed_candidate_count"] = 1
    malformed["coverage_sha256"] = canonical_sha256(
        {key: value for key, value in malformed.items() if key != "coverage_sha256"}
    )
    with pytest.raises(closeout.A2ThreePrimaryCloseoutError, match="does not satisfy its schema"):
        closeout._validate_coverage(ROOT, malformed)

    nested_hash_drift = deepcopy(coverage)
    nested_hash_drift["diagnostic_no_winner_receipts"]["ARM-01"]["receipt_sha256"] = "0" * 64
    nested_hash_drift["coverage_sha256"] = canonical_sha256(
        {key: value for key, value in nested_hash_drift.items() if key != "coverage_sha256"}
    )
    with pytest.raises(closeout.A2ThreePrimaryCloseoutError, match="self-hash drift"):
        closeout._validate_coverage(ROOT, nested_hash_drift)
