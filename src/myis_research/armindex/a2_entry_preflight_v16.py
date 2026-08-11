"""Read-only A2 entry preflight from the hash-bound current A1.2 terminal state.

This module performs no provider, SSH, remote-root, or A2 execution action.
It only reports the preparation still required after a complete A1 closeout.
"""

from __future__ import annotations

import argparse
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
    if a2_phase.get("status") != "planned":
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
