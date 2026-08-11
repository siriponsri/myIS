"""Aggregate-only closeout receipt for an already completed v16 evaluation.

The evaluator remains the sole component that reads protected qrels, membership,
or rankings.  This bridge only validates the evaluator's existing aggregate
receipts and promotion decision, then writes one immutable hash summary that a
terminal A1.2 receipt can bind.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_json, canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a1_2_owner_local_evaluator_v16 import ARM_IDS, CELL_IDS, PROMOTION_RULE

SCHEMA_PATH = Path("schemas/armindex/a1.2-evaluator-closeout-receipt.v16.json")
RESULT_SCHEMA_PATH = Path("schemas/armindex/a1.2-aggregate-result-receipt.v11.json")
RECEIPT_NAME = "evaluator-closeout.receipt.v16.json"
_ATTEMPT = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
_HASH = re.compile(r"^[a-f0-9]{64}$")


class EvaluatorCloseoutV16Error(ValueError):
    """Raised when an evaluator output cannot be safely summarized."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise EvaluatorCloseoutV16Error(f"invalid aggregate JSON: {path.name}") from error
    if not isinstance(value, dict):
        raise EvaluatorCloseoutV16Error(f"aggregate JSON object required: {path.name}")
    return value


def _schema(repository_root: Path, schema_path: Path, value: Mapping[str, Any]) -> None:
    errors = sorted(
        Draft202012Validator(_load(repository_root / schema_path)).iter_errors(dict(value)),
        key=lambda error: list(error.path),
    )
    if errors:
        raise EvaluatorCloseoutV16Error(f"schema validation failed: {errors[0].message}")


def _self_hash(value: Mapping[str, Any], field: str) -> None:
    body = dict(value)
    if body.pop(field, None) != canonical_sha256(body):
        raise EvaluatorCloseoutV16Error(f"{field} mismatch")


def _hash(value: object, label: str) -> str:
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise EvaluatorCloseoutV16Error(f"{label} must be a lowercase SHA-256")
    return value


def _cell_filename(cell: str) -> str:
    return f"{cell}.json"


def _validate_cell(
    repository_root: Path, path: Path, *, cell: str, attempt_id: str | None
) -> tuple[dict[str, Any], str]:
    if not path.is_file() or path.is_symlink():
        raise EvaluatorCloseoutV16Error(f"missing or unsafe aggregate receipt: {cell}")
    value = _load(path)
    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise EvaluatorCloseoutV16Error(str(error)) from error
    _schema(repository_root, RESULT_SCHEMA_PATH, value)
    _self_hash(value, "receipt_sha256")
    arm, program = cell.split("--", 1)
    if value.get("arm_id") != arm or value.get("program_id") != program:
        raise EvaluatorCloseoutV16Error(f"cell identity drifted: {cell}")
    lineage = value.get("lineage")
    if not isinstance(lineage, Mapping):
        raise EvaluatorCloseoutV16Error(f"cell lineage is invalid: {cell}")
    archive_hash = _hash(lineage.get("safe_return_archive_sha256"), "safe return archive")
    if attempt_id is not None and value.get("receipt_id", "").split("--", 1)[0] != archive_hash[:16]:
        raise EvaluatorCloseoutV16Error(f"cell receipt identity is inconsistent: {cell}")
    return value, file_sha256(path)


def _validate_promotion(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise EvaluatorCloseoutV16Error("promotion receipt is missing or unsafe")
    value = _load(path)
    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise EvaluatorCloseoutV16Error(str(error)) from error
    required = {
        "schema_version",
        "status",
        "rule",
        "policy_sha256",
        "quote_receipt_sha256",
        "quote_sha256",
        "allocation_sha256",
        "max_promoted_arms",
        "promoted_arm_ids",
        "candidate_arm_count",
        "tie_rejected",
        "receipt_sha256",
    }
    if (
        set(value) != required
        or value.get("schema_version") != "myis.armindex-a1.2-arm-promotion.v16"
        or value.get("status") != "PASS"
        or value.get("rule") != PROMOTION_RULE
        or value.get("max_promoted_arms") != 3
        or value.get("candidate_arm_count") != 5
        or value.get("tie_rejected") is not True
    ):
        raise EvaluatorCloseoutV16Error("promotion receipt contract drifted")
    arms = value.get("promoted_arm_ids")
    if not isinstance(arms, list) or len(arms) != 3 or len(set(arms)) != 3 or any(arm not in ARM_IDS for arm in arms):
        raise EvaluatorCloseoutV16Error("promotion receipt arm set is invalid")
    for field in ("policy_sha256", "quote_receipt_sha256", "quote_sha256", "allocation_sha256"):
        _hash(value.get(field), field)
    _self_hash(value, "receipt_sha256")
    return value


def validate_evaluator_closeout_inputs(
    repository_root: Path, evaluation_attempt_root: Path
) -> dict[str, Any]:
    """Validate exactly 25 existing aggregate receipts and one frozen promotion."""

    root = repository_root.resolve()
    attempt_root = evaluation_attempt_root.resolve(strict=True)
    if attempt_root.is_symlink() or attempt_root.is_relative_to(root):
        raise EvaluatorCloseoutV16Error("evaluation output must remain outside the repository")
    attempt_id = attempt_root.name
    if _ATTEMPT.fullmatch(attempt_id) is None:
        raise EvaluatorCloseoutV16Error("evaluation output directory must be an attempt ID")
    receipt_root = attempt_root / "receipts"
    if not receipt_root.is_dir() or receipt_root.is_symlink():
        raise EvaluatorCloseoutV16Error("aggregate receipt directory is missing or unsafe")
    cell_hashes: dict[str, str] = {}
    lineage: Mapping[str, Any] | None = None
    safe_return_archive_sha256: str | None = None
    for cell in CELL_IDS:
        receipt, digest = _validate_cell(root, receipt_root / _cell_filename(cell), cell=cell, attempt_id=attempt_id)
        candidate_lineage = receipt["lineage"]
        candidate_safe_return = _hash(candidate_lineage["safe_return_archive_sha256"], "safe return archive")
        if lineage is None:
            lineage = candidate_lineage
            safe_return_archive_sha256 = candidate_safe_return
        elif candidate_lineage != lineage or candidate_safe_return != safe_return_archive_sha256:
            raise EvaluatorCloseoutV16Error("aggregate receipts do not share frozen lineage")
        cell_hashes[cell] = digest
    if {path.name for path in receipt_root.iterdir()} != {
        _cell_filename(cell) for cell in CELL_IDS
    }:
        raise EvaluatorCloseoutV16Error("aggregate receipt directory has extra or missing members")
    promotion = _validate_promotion(attempt_root / "promotion.json")
    if lineage is None or safe_return_archive_sha256 is None:
        raise EvaluatorCloseoutV16Error("aggregate receipt set is empty")
    return {
        "attempt_id": attempt_id,
        "safe_return_archive_sha256": safe_return_archive_sha256,
        "evaluation_lineage_sha256": canonical_sha256(dict(lineage)),
        "cell_receipt_count": len(cell_hashes),
        "cell_receipt_set_sha256": canonical_sha256(cell_hashes),
        "promotion_receipt_sha256": promotion["receipt_sha256"],
        "promotion_policy_sha256": promotion["policy_sha256"],
        "admitted_quote_receipt_sha256": promotion["quote_receipt_sha256"],
        "admitted_quote_sha256": promotion["quote_sha256"],
        "cost_allocation_sha256": promotion["allocation_sha256"],
        "promoted_arm_ids": list(promotion["promoted_arm_ids"]),
    }


def build_evaluator_closeout_receipt(
    repository_root: Path, evaluation_attempt_root: Path
) -> dict[str, Any]:
    """Build one immutable aggregate receipt from an already complete evaluation."""

    values = validate_evaluator_closeout_inputs(repository_root, evaluation_attempt_root)
    receipt = {
        "schema_version": "myis.armindex-a1.2-evaluator-closeout-receipt.v16",
        "receipt_id": f"{values['attempt_id']}-evaluator-closeout-v16",
        "attempt_id": values["attempt_id"],
        "status": "PASS",
        "evidence_class": "measured_development_aggregate",
        "scientific_authority": True,
        "claim_boundary": "Aggregate-only Owner-local A1.2 evaluation closeout; protected qrels, membership, rankings, identifiers, and per-query outcomes remain outside this receipt.",
        "safe_return_archive_sha256": values["safe_return_archive_sha256"],
        "evaluation_lineage_sha256": values["evaluation_lineage_sha256"],
        "cell_receipt_count": values["cell_receipt_count"],
        "cell_receipt_set_sha256": values["cell_receipt_set_sha256"],
        "promotion_receipt_sha256": values["promotion_receipt_sha256"],
        "promotion_policy_sha256": values["promotion_policy_sha256"],
        "admitted_quote_receipt_sha256": values["admitted_quote_receipt_sha256"],
        "admitted_quote_sha256": values["admitted_quote_sha256"],
        "cost_allocation_sha256": values["cost_allocation_sha256"],
        "promoted_arm_ids": values["promoted_arm_ids"],
        "access_counters": {
            "harness_dev_accesses": 0,
            "selection_accesses": 0,
            "final_accesses": 0,
        },
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    validate_evaluator_closeout_receipt(repository_root, receipt)
    return receipt


def validate_evaluator_closeout_receipt(
    repository_root: Path, receipt: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate a portable aggregate closeout receipt before terminal binding."""

    root = repository_root.resolve()
    try:
        assert_aggregate_only(receipt)
    except ValueError as error:
        raise EvaluatorCloseoutV16Error(str(error)) from error
    _schema(root, SCHEMA_PATH, receipt)
    _self_hash(receipt, "receipt_sha256")
    attempt_id = receipt.get("attempt_id")
    if not isinstance(attempt_id, str) or _ATTEMPT.fullmatch(attempt_id) is None:
        raise EvaluatorCloseoutV16Error("attempt ID is invalid")
    if receipt.get("receipt_id") != f"{attempt_id}-evaluator-closeout-v16":
        raise EvaluatorCloseoutV16Error("closeout receipt ID does not bind attempt")
    for field in (
        "safe_return_archive_sha256",
        "evaluation_lineage_sha256",
        "cell_receipt_set_sha256",
        "promotion_receipt_sha256",
        "promotion_policy_sha256",
        "admitted_quote_receipt_sha256",
        "admitted_quote_sha256",
        "cost_allocation_sha256",
    ):
        _hash(receipt.get(field), field)
    return dict(receipt)


def write_evaluator_closeout_receipt(
    repository_root: Path, evaluation_attempt_root: Path
) -> dict[str, Any]:
    """Write the closeout receipt once next to its already immutable evaluation output."""

    attempt_root = evaluation_attempt_root.resolve(strict=True)
    receipt = build_evaluator_closeout_receipt(repository_root, attempt_root)
    path = attempt_root / RECEIPT_NAME
    payload = canonical_json(receipt) + "\n"
    if path.exists():
        if path.is_symlink() or path.read_text(encoding="ascii") != payload:
            raise EvaluatorCloseoutV16Error("immutable evaluator closeout already differs")
        return receipt
    descriptor, temporary_name = tempfile.mkstemp(dir=attempt_root, prefix=f".{RECEIPT_NAME}.", suffix=".tmp")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-evaluator-closeout-v16")
    parser.add_argument("--evaluation-attempt-root", required=True, type=Path)
    parser.add_argument("--repository-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = write_evaluator_closeout_receipt(
            args.repository_root, args.evaluation_attempt_root
        )
    except (EvaluatorCloseoutV16Error, OSError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "RECEIPT_NAME",
    "EvaluatorCloseoutV16Error",
    "build_evaluator_closeout_receipt",
    "validate_evaluator_closeout_inputs",
    "validate_evaluator_closeout_receipt",
    "write_evaluator_closeout_receipt",
]
