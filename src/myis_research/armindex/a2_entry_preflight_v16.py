"""Read-only A2 entry preflight from the hash-bound current A1.2 terminal state.

This module performs no provider, SSH, remote-root, or A2 execution action.
It only reports the preparation still required after a complete A1 closeout.
"""

from __future__ import annotations

import argparse
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ..kernel.canonical import canonical_json
from ..projections.read_model import build_read_model
from ..report_records import build_report_records
from .a1_2_terminal_attempt_v16 import (
    TerminalAttemptV16Error,
    validate_current_attempt_pointer,
)

_SUCCESS_HASHES = (
    "safe_return_sha256",
    "evaluator_receipt_sha256",
    "promotion_receipt_sha256",
)
_SHA256_PATTERN = re.compile(r"[a-f0-9]{64}")
_POST_FREEZE_STATUS = "complete_audit_passed_measured_a2_closed"
_POST_FREEZE_COUNTS = {
    "candidate_count": 52,
    "matched_candidate_count": 40,
    "conditional_reserve_candidate_count": 12,
}
_POST_FREEZE_HASHES = (
    "manifest_sha256",
    "manifest_file_sha256",
    "freeze_receipt_sha256",
    "freeze_receipt_file_sha256",
    "lock_sha256",
    "lock_file_sha256",
    "independent_audit_receipt_sha256",
    "independent_audit_receipt_file_sha256",
)
_POST_FREEZE_FALSE_FLAGS = (
    "measured_a2_started",
    "rep_dev_accessed_for_measurement",
    "gpu_work_performed",
    "provider_admission_performed",
    "provider_execution_adoption_performed",
    "protected_data_accessed",
)
_POST_FREEZE_ZERO_COUNTERS = (
    "harness_dev_accesses",
    "selection_accesses",
    "final_accesses",
)


class A2EntryPreflightV16Error(ValueError):
    """Raised when the current A1 terminal state cannot authorize A2 preparation."""


def _phase(model: Mapping[str, Any], phase_id: str) -> Mapping[str, Any]:
    armindex = model.get("armindex")
    if not isinstance(armindex, Mapping):
        raise A2EntryPreflightV16Error("ArmIndex read model is missing")
    phases = armindex.get("phases")
    if not isinstance(phases, list):
        raise A2EntryPreflightV16Error("ArmIndex phase projection is missing")
    for phase in phases:
        if isinstance(phase, Mapping) and phase.get("phase_id") == phase_id:
            return phase
    raise A2EntryPreflightV16Error(f"read model phase is missing: {phase_id}")


def _validated_post_freeze_state(armindex: Mapping[str, Any]) -> Mapping[str, Any]:
    """Require the only blocked A2 state that is safe to prepare from."""

    freeze = armindex.get("a2_candidate_freeze")
    if not isinstance(freeze, Mapping):
        raise A2EntryPreflightV16Error("A2 blocked phase is missing candidate-freeze evidence")
    if (
        freeze.get("validated") is not True
        or freeze.get("status") != _POST_FREEZE_STATUS
        or freeze.get("independent_audit_status") != "PASS"
    ):
        raise A2EntryPreflightV16Error("A2 blocked phase lacks a validated PASS candidate-freeze audit")
    if any(freeze.get(key) != value for key, value in _POST_FREEZE_COUNTS.items()):
        raise A2EntryPreflightV16Error("A2 blocked phase candidate-freeze counts are not exactly 40+12")
    if any(
        not isinstance(freeze.get(key), str)
        or _SHA256_PATTERN.fullmatch(freeze[key]) is None
        for key in _POST_FREEZE_HASHES
    ):
        raise A2EntryPreflightV16Error("A2 blocked phase immutable candidate-freeze hashes are invalid")
    if any(freeze.get(key) is not False for key in _POST_FREEZE_FALSE_FLAGS):
        raise A2EntryPreflightV16Error("A2 blocked phase candidate-freeze safety flags are invalid")
    if any(freeze.get(key) != 0 for key in _POST_FREEZE_ZERO_COUNTERS):
        raise A2EntryPreflightV16Error("A2 blocked phase candidate-freeze access counters are invalid")
    return freeze


def _validated_execution_readiness(armindex: Mapping[str, Any]) -> Mapping[str, Any]:
    readiness = armindex.get("a2_execution_readiness")
    if (
        not isinstance(readiness, Mapping)
        or readiness.get("validated") is not True
        or readiness.get("status")
        != "READY_FOR_FRESH_ADMISSION_AND_STAGING_MEASUREMENT_LOCKED"
        or readiness.get("candidate_count") != 52
        or readiness.get("matched_candidate_count") != 40
        or readiness.get("conditional_reserve_candidate_count") != 12
        or readiness.get("diagnostic_non_advancing_arms") != ["ARM-01", "ARM-02"]
        or readiness.get("provider_admission_performed") is not False
        or readiness.get("provider_execution_adoption_performed") is not False
        or readiness.get("remote_staging_performed") is not False
        or readiness.get("measured_a2_started") is not False
    ):
        raise A2EntryPreflightV16Error(
            "A2 ready phase lacks validated measurement-locked execution readiness"
        )
    counters = readiness.get("counters")
    if not isinstance(counters, Mapping) or any(value != 0 for value in counters.values()):
        raise A2EntryPreflightV16Error("A2 readiness counters must remain zero")
    return readiness


def evaluate_a2_entry_preflight(repository_root: Path) -> dict[str, Any]:
    """Validate completed A1 closeout and report only A2 preparation obligations."""

    try:
        current = validate_current_attempt_pointer(repository_root)
    except TerminalAttemptV16Error as error:
        raise A2EntryPreflightV16Error(str(error)) from error
    receipt = current["receipt"]
    if not isinstance(receipt, Mapping):
        raise A2EntryPreflightV16Error("current terminal receipt is invalid")
    coverage = receipt.get("coverage")
    if receipt.get("status") != "PASS" or not isinstance(coverage, Mapping):
        raise A2EntryPreflightV16Error("A2 preparation requires a PASS A1 terminal receipt")
    if coverage.get("required_logical_cells") != 25 or coverage.get("completed_logical_cells") != 25:
        raise A2EntryPreflightV16Error("A2 preparation requires complete A1 25/25 coverage")
    disposition = receipt.get("provider_disposition_status")
    if disposition not in {"REUSE_ELIGIBLE", "DESTROYED"}:
        raise A2EntryPreflightV16Error("A2 preparation requires reusable or destroyed provider disposition")
    if receipt.get("scientific_authority") is not True:
        raise A2EntryPreflightV16Error("A2 preparation requires scientific A1 terminal authority")
    for field in _SUCCESS_HASHES:
        value = receipt.get(field)
        if not isinstance(value, str) or len(value) != 64:
            raise A2EntryPreflightV16Error(f"A1 terminal {field} is missing")
    counters = receipt.get("access_counters")
    if not isinstance(counters, Mapping):
        raise A2EntryPreflightV16Error("A1 access counters are invalid")
    if counters.get("selection_accesses") != 0 or counters.get("final_accesses") != 0:
        raise A2EntryPreflightV16Error("Selection and Final counters must remain zero")
    if counters.get("harness_dev_accesses") != 0:
        raise A2EntryPreflightV16Error("HARNESS-DEV counter must remain zero")

    try:
        model = build_read_model(repository_root)
        reports = build_report_records(repository_root, model)
    except (OSError, TypeError, ValueError) as error:
        raise A2EntryPreflightV16Error(
            f"A1 closeout read-model/report validation failed: {error}"
        ) from error
    armindex = model.get("armindex")
    if not isinstance(armindex, Mapping):
        raise A2EntryPreflightV16Error("ArmIndex read model is missing")
    projected_attempt = armindex.get("a1_2_current_attempt")
    if (
        not isinstance(projected_attempt, Mapping)
        or projected_attempt.get("validated") is not True
        or projected_attempt.get("attempt_id") != receipt.get("attempt_id")
        or projected_attempt.get("receipt_file_sha256")
        != current.get("receipt_file_sha256")
        or projected_attempt.get("status") != "PASS"
    ):
        raise A2EntryPreflightV16Error(
            "A1 terminal pointer and read-model projection do not agree"
        )
    measured_summary = projected_attempt.get("measured_result_summary")
    if (
        not isinstance(measured_summary, Mapping)
        or measured_summary.get("status") != "PASS"
        or measured_summary.get("attempt_id") != receipt.get("attempt_id")
        or not isinstance(measured_summary.get("summary_file_sha256"), str)
        or not isinstance(measured_summary.get("summary_sha256"), str)
        or not isinstance(measured_summary.get("promoted_arm_ids"), list)
        or len(measured_summary["promoted_arm_ids"]) != 3
    ):
        raise A2EntryPreflightV16Error(
            "validated A1 measured-result summary and promoted-arm set are missing"
        )
    a1_phase = _phase(model, "A1_BASELINES_AND_MULTI_ARM_SCREENING")
    a2_phase = _phase(model, "A2_PER_ARM_AUTOINDEX")
    if a1_phase.get("status") != "complete":
        raise A2EntryPreflightV16Error("A1 phase is not complete in the read model")
    post_freeze = None
    readiness = None
    if a2_phase.get("status") == "blocked":
        post_freeze = _validated_post_freeze_state(armindex)
    elif a2_phase.get("status") == "ready":
        post_freeze = _validated_post_freeze_state(armindex)
        readiness = _validated_execution_readiness(armindex)
    elif a2_phase.get("status") != "planned":
        raise A2EntryPreflightV16Error(
            "A2 phase must be planned and no longer locked until A1"
        )
    projected_counters = armindex.get("counters")
    if (
        not isinstance(projected_counters, Mapping)
        or projected_counters.get("measured_runs") != 1
        or projected_counters.get("selection_accesses") != 0
        or projected_counters.get("final_accesses") != 0
    ):
        raise A2EntryPreflightV16Error(
            "read-model Selection and Final counters must remain zero"
        )
    a1_report = next(
        (
            item
            for item in reports
            if isinstance(item, Mapping) and item.get("report_id") == "task-a1-2"
        ),
        None,
    )
    if (
        not isinstance(a1_report, Mapping)
        or a1_report.get("status") != "completed"
        or a1_report.get("scientific_authority") is not True
        or not isinstance(a1_report.get("claim_boundary"), str)
        or not a1_report["claim_boundary"].strip()
    ):
        raise A2EntryPreflightV16Error(
            "validated completed A1.2 report with claim boundary is missing"
        )
    return {
        "status": "PASS_A2_ENTRY_PREFLIGHT",
        "a1_attempt_id": receipt["attempt_id"],
        "a1_terminal_receipt_file_sha256": current["receipt_file_sha256"],
        "a1_terminal_receipt_sha256": receipt["receipt_sha256"],
        "provider_disposition_status": disposition,
        "reuse_existing_instance_permitted": disposition == "REUSE_ELIGIBLE",
        "fresh_a2_provider_admission_required": True,
        "fresh_a2_execution_adoption_required": True,
        "new_isolated_remote_root_required": True,
        "a2_execution_authorized": False,
        "candidate_evaluation_authorized": False,
        "safe_return_sha256": receipt["safe_return_sha256"],
        "evaluator_receipt_sha256": receipt["evaluator_receipt_sha256"],
        "promotion_receipt_sha256": receipt["promotion_receipt_sha256"],
        "measured_result_summary_sha256": measured_summary["summary_sha256"],
        "measured_result_summary_file_sha256": measured_summary[
            "summary_file_sha256"
        ],
        "promoted_arm_ids": measured_summary["promoted_arm_ids"],
        "read_model_revision": model["read_model_revision"],
        "a1_report_sha256": a1_report["report_sha256"],
        "a2_phase_status": a2_phase["status"],
        "candidate_freeze": (
            {
                "status": post_freeze["status"],
                "independent_audit_status": post_freeze["independent_audit_status"],
                **_POST_FREEZE_COUNTS,
                "diagnostic_non_advancing_arms": ["ARM-01", "ARM-02"],
                **{key: post_freeze[key] for key in _POST_FREEZE_HASHES},
            }
            if post_freeze is not None
            else None
        ),
        "execution_readiness": (
            {
                "status": readiness["status"],
                "candidate_count": readiness["candidate_count"],
                "matched_candidate_count": readiness["matched_candidate_count"],
                "conditional_reserve_candidate_count": readiness[
                    "conditional_reserve_candidate_count"
                ],
                "diagnostic_non_advancing_arms": readiness[
                    "diagnostic_non_advancing_arms"
                ],
                "forward_hard_stop_usd": readiness["forward_hard_stop_usd"],
                "owner_ttl_hours": readiness["owner_ttl_hours"],
            }
            if readiness is not None
            else None
        ),
        "access_counters": {
            "harness_dev_accesses": 0,
            "selection_accesses": 0,
            "final_accesses": 0,
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-a2-entry-preflight-v16")
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    try:
        result = evaluate_a2_entry_preflight(args.repository_root)
    except A2EntryPreflightV16Error as error:
        parser.error(str(error))
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["A2EntryPreflightV16Error", "evaluate_a2_entry_preflight", "main"]
