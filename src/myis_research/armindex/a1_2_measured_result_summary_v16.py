"""Project validated Owner-local A1.2 aggregates into one repository-safe summary."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_json, canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a1_2_evaluator_closeout_v16 import (
    RECEIPT_NAME,
    RESULT_SCHEMA_PATH,
    validate_evaluator_closeout_inputs,
    validate_evaluator_closeout_receipt,
)
from .a1_2_owner_local_evaluator_v16 import ARM_IDS, CELL_IDS

SCHEMA_PATH = Path("schemas/armindex/a1.2-measured-result-summary.v16.json")
SUMMARY_DIRECTORY = Path(
    "campaigns/armindex-multiretriever-v2/evidence/a1.2-result-summaries"
)


class MeasuredResultSummaryV16Error(ValueError):
    """Raised when aggregate A1.2 evidence cannot form a safe summary."""


def summary_path(attempt_id: str) -> Path:
    return SUMMARY_DIRECTORY / f"{attempt_id}.summary.v16.json"


def _load(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise MeasuredResultSummaryV16Error(f"{role} is invalid") from error
    if not isinstance(value, dict):
        raise MeasuredResultSummaryV16Error(f"{role} must be an object")
    return value


def _schema(repository_root: Path, schema_path: Path, value: Mapping[str, Any]) -> None:
    errors = sorted(
        Draft202012Validator(_load(repository_root / schema_path, role="schema")).iter_errors(
            dict(value)
        ),
        key=lambda error: list(error.path),
    )
    if errors:
        raise MeasuredResultSummaryV16Error(
            f"schema validation failed: {errors[0].message}"
        )


def _self_hash(value: Mapping[str, Any], field: str) -> None:
    body = dict(value)
    if body.pop(field, None) != canonical_sha256(body):
        raise MeasuredResultSummaryV16Error(f"{field} mismatch")


def _mean(values: list[float]) -> float:
    return math.fsum(values) / len(values)


def _validated_cells(
    repository_root: Path, evaluation_attempt_root: Path
) -> tuple[dict[str, dict[str, Any]], str]:
    receipts: dict[str, dict[str, Any]] = {}
    receipt_hashes: dict[str, str] = {}
    receipt_root = evaluation_attempt_root / "receipts"
    if not receipt_root.is_dir() or receipt_root.is_symlink():
        raise MeasuredResultSummaryV16Error(
            "aggregate receipt directory is missing or unsafe"
        )
    for cell in CELL_IDS:
        path = receipt_root / f"{cell}.json"
        if not path.is_file() or path.is_symlink():
            raise MeasuredResultSummaryV16Error(
                f"aggregate receipt {cell} is missing or unsafe"
            )
        try:
            payload = path.read_bytes()
            value = json.loads(payload.decode("ascii"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise MeasuredResultSummaryV16Error(
                f"aggregate receipt {cell} is invalid"
            ) from error
        if not isinstance(value, dict):
            raise MeasuredResultSummaryV16Error(
                f"aggregate receipt {cell} must be an object"
            )
        try:
            assert_aggregate_only(value)
        except ValueError as error:
            raise MeasuredResultSummaryV16Error(str(error)) from error
        _schema(repository_root, RESULT_SCHEMA_PATH, value)
        _self_hash(value, "receipt_sha256")
        receipts[cell] = value
        receipt_hashes[cell] = hashlib.sha256(payload).hexdigest()
    if {path.name for path in receipt_root.iterdir()} != {
        f"{cell}.json" for cell in CELL_IDS
    }:
        raise MeasuredResultSummaryV16Error(
            "aggregate receipt directory has extra or missing members"
        )
    return receipts, canonical_sha256(receipt_hashes)


def load_validated_cell_receipts(
    repository_root: Path, evaluation_attempt_root: Path
) -> tuple[dict[str, dict[str, Any]], str]:
    """Return the 25 aggregate-safe cell receipts and their set commitment."""

    root = repository_root.resolve(strict=True)
    evaluation = evaluation_attempt_root.resolve(strict=True)
    return _validated_cells(root, evaluation)


def build_measured_result_summary(
    repository_root: Path, evaluation_attempt_root: Path
) -> dict[str, Any]:
    """Build one safe arm-level summary from exactly 25 validated receipts."""

    root = repository_root.resolve(strict=True)
    evaluation = evaluation_attempt_root.resolve(strict=True)
    try:
        validated = validate_evaluator_closeout_inputs(root, evaluation)
        closeout = validate_evaluator_closeout_receipt(
            root,
            _load(evaluation / RECEIPT_NAME, role="evaluator closeout receipt"),
        )
    except ValueError as error:
        if isinstance(error, MeasuredResultSummaryV16Error):
            raise
        raise MeasuredResultSummaryV16Error(str(error)) from error
    closeout_bindings = {
        "attempt_id": validated["attempt_id"],
        "safe_return_archive_sha256": validated["safe_return_archive_sha256"],
        "evaluation_lineage_sha256": validated["evaluation_lineage_sha256"],
        "cell_receipt_count": validated["cell_receipt_count"],
        "cell_receipt_set_sha256": validated["cell_receipt_set_sha256"],
        "promotion_receipt_sha256": validated["promotion_receipt_sha256"],
        "promotion_policy_sha256": validated["promotion_policy_sha256"],
        "admitted_quote_receipt_sha256": validated[
            "admitted_quote_receipt_sha256"
        ],
        "admitted_quote_sha256": validated["admitted_quote_sha256"],
        "cost_allocation_sha256": validated["cost_allocation_sha256"],
        "promoted_arm_ids": validated["promoted_arm_ids"],
    }
    if any(closeout.get(key) != value for key, value in closeout_bindings.items()):
        raise MeasuredResultSummaryV16Error(
            "evaluator closeout does not bind the current evaluation inputs"
        )
    cells, current_cell_receipt_set_sha256 = _validated_cells(root, evaluation)
    if current_cell_receipt_set_sha256 != validated["cell_receipt_set_sha256"]:
        raise MeasuredResultSummaryV16Error(
            "aggregate receipts changed during measured summary construction"
        )
    arm_results = []
    for arm_id in ARM_IDS:
        arm_cells = [value for cell, value in cells.items() if cell.startswith(f"{arm_id}--")]
        if len(arm_cells) != 5:
            raise MeasuredResultSummaryV16Error(f"{arm_id} does not contain five programs")
        arm_results.append(
            {
                "arm_id": arm_id,
                "program_count": 5,
                "out_recall_at_100_mean": _mean(
                    [float(value["quality"]["recall_at_100_out"]) for value in arm_cells]
                ),
                "out_ndcg_at_100_mean": _mean(
                    [float(value["quality"]["ndcg_at_100_out"]) for value in arm_cells]
                ),
                "out_ndcg_at_10_mean": _mean(
                    [float(value["quality"]["ndcg_at_10_out"]) for value in arm_cells]
                ),
                "search_latency_p95_ms_mean": _mean(
                    [float(value["performance"]["search_latency_ms"]["p95"]) for value in arm_cells]
                ),
                "wall_seconds_sum": math.fsum(
                    float(value["performance"]["wall_seconds"]) for value in arm_cells
                ),
                "failure_rate_mean": _mean(
                    [float(value["quality"]["failure_rate"]) for value in arm_cells]
                ),
            }
        )
    summary = {
        "schema_version": "myis.armindex-a1.2-measured-result-summary.v16",
        "summary_id": f"{validated['attempt_id']}-measured-result-summary-v16",
        "attempt_id": validated["attempt_id"],
        "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
        "task_id": "A1.2",
        "status": "PASS",
        "evidence_class": "measured_development_aggregate",
        "scientific_authority": True,
        "claim_boundary": (
            "Aggregate-only REP-DEV A1.2 arm summary; protected qrels, membership, "
            "rankings, identifiers, and per-query outcomes remain Owner-local."
        ),
        "metric_contract": {
            "primary": "OUT Recall@100",
            "secondary": ["OUT nDCG@100", "OUT nDCG@10"],
        },
        "coverage": {
            "arm_count": 5,
            "programs_per_arm": 5,
            "completed_logical_cells": 25,
            "required_logical_cells": 25,
        },
        "arm_results": arm_results,
        "promoted_arm_ids": validated["promoted_arm_ids"],
        "lineage": {
            "safe_return_archive_sha256": validated["safe_return_archive_sha256"],
            "cell_receipt_set_sha256": validated["cell_receipt_set_sha256"],
            "promotion_receipt_sha256": validated["promotion_receipt_sha256"],
            "evaluator_closeout_receipt_sha256": closeout["receipt_sha256"],
        },
        "access_counters": {
            "harness_dev_accesses": 0,
            "selection_accesses": 0,
            "final_accesses": 0,
        },
    }
    summary["summary_sha256"] = canonical_sha256(summary)
    validate_measured_result_summary(root, summary)
    return summary


def validate_measured_result_summary(
    repository_root: Path, value: Mapping[str, Any]
) -> dict[str, Any]:
    root = repository_root.resolve(strict=True)
    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise MeasuredResultSummaryV16Error(str(error)) from error
    _schema(root, SCHEMA_PATH, value)
    _self_hash(value, "summary_sha256")
    arms = value.get("arm_results")
    if not isinstance(arms, list) or [item.get("arm_id") for item in arms] != list(ARM_IDS):
        raise MeasuredResultSummaryV16Error("arm result order or identity drifted")
    attempt_id = value.get("attempt_id")
    if value.get("summary_id") != f"{attempt_id}-measured-result-summary-v16":
        raise MeasuredResultSummaryV16Error("summary_id does not bind attempt_id")
    return dict(value)


def write_measured_result_summary(
    repository_root: Path, evaluation_attempt_root: Path
) -> tuple[Path, dict[str, Any]]:
    root = repository_root.resolve(strict=True)
    summary = build_measured_result_summary(root, evaluation_attempt_root)
    path = root / summary_path(summary["attempt_id"])
    payload = canonical_json(summary) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_text(encoding="ascii") != payload:
            raise MeasuredResultSummaryV16Error("immutable measured summary already differs")
        return path, summary
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return path, summary


def validate_measured_result_summary_file(
    repository_root: Path, attempt_id: str
) -> dict[str, Any]:
    root = repository_root.resolve(strict=True)
    path = root / summary_path(attempt_id)
    if not path.is_file() or path.is_symlink():
        raise MeasuredResultSummaryV16Error("measured result summary is missing or unsafe")
    value = validate_measured_result_summary(root, _load(path, role="measured result summary"))
    if value.get("attempt_id") != attempt_id:
        raise MeasuredResultSummaryV16Error("measured result summary attempt drifted")
    return {**value, "summary_uri": summary_path(attempt_id).as_posix(), "summary_file_sha256": file_sha256(path)}


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-measured-result-summary-v16")
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--evaluation-attempt-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        path, summary = write_measured_result_summary(
            args.repository_root, args.evaluation_attempt_root
        )
    except (MeasuredResultSummaryV16Error, OSError, ValueError) as error:
        parser.error(str(error))
    print(
        canonical_json(
            {
                "status": "PASS",
                "attempt_id": summary["attempt_id"],
                "summary_uri": path.relative_to(args.repository_root.resolve()).as_posix(),
                "summary_sha256": summary["summary_sha256"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "SCHEMA_PATH",
    "SUMMARY_DIRECTORY",
    "MeasuredResultSummaryV16Error",
    "build_measured_result_summary",
    "load_validated_cell_receipts",
    "main",
    "summary_path",
    "validate_measured_result_summary",
    "validate_measured_result_summary_file",
    "write_measured_result_summary",
]
