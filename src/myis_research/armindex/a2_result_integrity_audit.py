"""Aggregate-only integrity audit for a completed A2 execution closeout.

This is an independent closeout consumer.  It deliberately does not evaluate
candidate outputs, rankings, queries, qrels, or protected membership data.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only

AUDIT_SCHEMA_VERSION = "myis.armindex-a2-result-integrity-audit.v1"
_REQUIRED_ARMS = ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")
_AUDIT_OUTPUT_ROOT = Path("outputs/audits/rigor")
_COVERAGE_KEYS = frozenset(
    {
        "status",
        "attempt_id",
        "candidate_count",
        "matched_candidate_count",
        "conditional_reserve_candidate_count",
        "candidate_result_set_sha256",
        "winner_receipts",
        "winners",
        "freeze_bindings",
        "checkpoint_sha256",
        "execution_adoption_receipt_sha256",
        "measurement_authority_sha256",
        "reserve_activation_decision_receipt_sha256",
        "reserve_continuation_authority_sha256",
        "workers_reaped",
    }
)


class A2ResultIntegrityAuditError(ValueError):
    """A closeout receipt cannot support an aggregate-only integrity audit."""


def _load_json(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise A2ResultIntegrityAuditError(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise A2ResultIntegrityAuditError(f"{role} must be an object")
    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise A2ResultIntegrityAuditError(f"{role} contains raw or protected content") from error
    return value


def _validate_schema(root: Path, name: str, value: Mapping[str, Any], *, role: str) -> None:
    schema = _load_json(root / "schemas/armindex" / name, role=f"{role} schema")
    errors = sorted(Draft202012Validator(schema).iter_errors(dict(value)), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        path = ".".join(str(item) for item in error.path) or "<root>"
        raise A2ResultIntegrityAuditError(
            f"{role} does not satisfy its schema at {path}: {error.message}"
        )


def _self_hash(value: Mapping[str, Any], *, field: str, role: str) -> str:
    expected = value.get(field)
    actual = canonical_sha256({key: item for key, item in value.items() if key != field})
    if expected != actual:
        raise A2ResultIntegrityAuditError(f"{role} self-hash mismatch")
    return actual


def _relative_uri(root: Path, path: Path) -> str:
    try:
        relative = path.resolve(strict=True).relative_to(root.resolve())
    except (OSError, ValueError) as error:
        raise A2ResultIntegrityAuditError("evidence path must be a regular repository-local file") from error
    if path.is_symlink() or not path.is_file():
        raise A2ResultIntegrityAuditError("evidence path must be a regular repository-local file")
    return relative.as_posix()


def _same_attempt_and_freeze(
    expected_attempt: object,
    expected_freeze: object,
    value: Mapping[str, Any],
    *,
    role: str,
) -> None:
    if value.get("attempt_id") != expected_attempt:
        raise A2ResultIntegrityAuditError(f"{role} attempt binding drift")
    if value.get("freeze_bindings") != expected_freeze:
        raise A2ResultIntegrityAuditError(f"{role} freeze binding drift")


def _winner_hashes(
    root: Path,
    coverage: Mapping[str, Any],
    *,
    attempt_id: object,
    freeze_bindings: object,
) -> dict[str, str]:
    winners = coverage.get("winner_receipts")
    if not isinstance(winners, Mapping) or set(winners) != set(_REQUIRED_ARMS):
        raise A2ResultIntegrityAuditError("coverage must contain exactly five winner receipts")
    result: dict[str, str] = {}
    for arm_id in _REQUIRED_ARMS:
        winner = winners[arm_id]
        if not isinstance(winner, Mapping):
            raise A2ResultIntegrityAuditError("winner receipt must be an object")
        try:
            assert_aggregate_only(winner)
        except ValueError as error:
            raise A2ResultIntegrityAuditError("winner receipt contains raw or protected content") from error
        _validate_schema(root, "a2-winner-selection-receipt.v1.json", winner, role="winner receipt")
        if winner.get("arm_id") != arm_id:
            raise A2ResultIntegrityAuditError("winner receipt arm identity drift")
        _same_attempt_and_freeze(attempt_id, freeze_bindings, winner, role="winner receipt")
        result[arm_id] = _self_hash(winner, field="receipt_sha256", role="winner receipt")
    return result


def audit_completed_closeout(
    repository_root: Path,
    *,
    closeout_path: Path,
    coverage_path: Path,
    safe_return_path: Path,
    terminal_checkpoint_path: Path,
) -> dict[str, Any]:
    """Audit one completed closeout using only aggregate-safe receipt objects."""

    root = repository_root.resolve()
    paths = {
        "closeout": closeout_path,
        "coverage": coverage_path,
        "safe_return": safe_return_path,
        "terminal_checkpoint": terminal_checkpoint_path,
    }
    for role, path in paths.items():
        _relative_uri(root, path)
    closeout = _load_json(closeout_path, role="closeout receipt")
    safe_return = _load_json(safe_return_path, role="safe-return receipt")
    terminal_checkpoint = _load_json(terminal_checkpoint_path, role="terminal checkpoint")
    coverage = _load_json(coverage_path, role="coverage receipt")
    unexpected_coverage_keys = set(coverage) - _COVERAGE_KEYS
    if unexpected_coverage_keys:
        raise A2ResultIntegrityAuditError("coverage receipt contains unallowlisted or raw fields")

    _validate_schema(root, "a2-execution-closeout-receipt.v1.json", closeout, role="closeout receipt")
    _validate_schema(root, "a2-safe-return-receipt.v1.json", safe_return, role="safe-return receipt")
    _validate_schema(root, "a2-lifecycle-checkpoint.v1.json", terminal_checkpoint, role="terminal checkpoint")
    closeout_hash = _self_hash(closeout, field="receipt_sha256", role="closeout receipt")
    safe_return_hash = _self_hash(safe_return, field="receipt_sha256", role="safe-return receipt")
    checkpoint_hash = _self_hash(terminal_checkpoint, field="checkpoint_sha256", role="terminal checkpoint")

    attempt_id = closeout["attempt_id"]
    freeze_bindings = closeout["freeze_bindings"]
    for role, value in (("safe-return receipt", safe_return), ("terminal checkpoint", terminal_checkpoint), ("coverage receipt", coverage)):
        _same_attempt_and_freeze(attempt_id, freeze_bindings, value, role=role)
    if closeout["safe_return_receipt_sha256"] != safe_return_hash:
        raise A2ResultIntegrityAuditError("closeout safe-return binding drift")
    if closeout["terminal_checkpoint_sha256"] != checkpoint_hash:
        raise A2ResultIntegrityAuditError("closeout terminal checkpoint binding drift")
    if safe_return.get("protected_payload_included") is not False:
        raise A2ResultIntegrityAuditError("safe-return receipt includes protected payload")
    if terminal_checkpoint.get("status") != "SAFE_RETURNED" or terminal_checkpoint.get("completed_candidate_count") != 52 or terminal_checkpoint.get("failed_candidate_count") != 0 or terminal_checkpoint.get("resume_allowed") is not False:
        raise A2ResultIntegrityAuditError("terminal checkpoint is not a complete safe return")
    if closeout.get("workers_reaped") is not True or closeout.get("protected_scan_passed") is not True:
        raise A2ResultIntegrityAuditError("closeout worker-reap or protected scan invariant failed")

    exact_counts = (coverage.get("candidate_count"), coverage.get("matched_candidate_count"), coverage.get("conditional_reserve_candidate_count"))
    if exact_counts != (52, 40, 12):
        raise A2ResultIntegrityAuditError("coverage receipt does not prove exact 52/40/12 coverage")
    if coverage.get("candidate_result_set_sha256") != closeout.get("candidate_result_set_sha256"):
        raise A2ResultIntegrityAuditError("closeout candidate-result-set binding drift")
    winner_hashes = _winner_hashes(root, coverage, attempt_id=attempt_id, freeze_bindings=freeze_bindings)
    if closeout.get("arm_winner_receipt_sha256s") != winner_hashes:
        raise A2ResultIntegrityAuditError("closeout winner receipt bindings drift")

    audit: dict[str, Any] = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "audit_id": f"{attempt_id}-result-integrity-audit-v1",
        "status": "PASS_A2_RESULT_INTEGRITY",
        "evidence_class": "measured_development_aggregate_result_audit",
        "scientific_authority": False,
        "claim_boundary": "Aggregate-only integrity audit. It validates receipt lineage and supports no per-query, protected-membership, or publication performance claim by itself.",
        "closeout": {
            "uri": _relative_uri(root, closeout_path),
            "file_sha256": file_sha256(closeout_path),
            "receipt_sha256": closeout_hash,
            "attempt_id": attempt_id,
            "freeze_bindings": freeze_bindings,
            "candidate_count": 52,
            "matched_candidate_count": 40,
            "conditional_reserve_candidate_count": 12,
            "arm_winner_receipt_sha256s": winner_hashes,
            "workers_reaped": True,
            "protected_scan_passed": True,
        },
        "coverage": {
            "uri": _relative_uri(root, coverage_path),
            "file_sha256": file_sha256(coverage_path),
            "candidate_result_set_sha256": closeout["candidate_result_set_sha256"],
            "candidate_count": 52,
            "matched_candidate_count": 40,
            "conditional_reserve_candidate_count": 12,
            "winner_receipt_sha256s": winner_hashes,
            "freeze_bindings": freeze_bindings,
        },
        "safe_return": {
            "uri": _relative_uri(root, safe_return_path),
            "file_sha256": file_sha256(safe_return_path),
            "receipt_sha256": safe_return_hash,
            "attempt_id": attempt_id,
            "freeze_bindings": freeze_bindings,
            "protected_payload_included": False,
            "aggregate_artifact_count": safe_return["aggregate_artifact_count"],
        },
        "terminal_checkpoint": {
            "uri": _relative_uri(root, terminal_checkpoint_path),
            "file_sha256": file_sha256(terminal_checkpoint_path),
            "receipt_sha256": checkpoint_hash,
            "attempt_id": attempt_id,
            "freeze_bindings": freeze_bindings,
            "status": "SAFE_RETURNED",
            "completed_candidate_count": 52,
            "failed_candidate_count": 0,
            "resume_allowed": False,
        },
        "protection": {
            "aggregate_only_scan_passed": True,
            "raw_or_protected_content_observed": False,
        },
    }
    assert_aggregate_only(audit)
    audit["audit_sha256"] = canonical_sha256(audit)
    _validate_schema(root, "a2-result-integrity-audit.v1.json", audit, role="result-integrity audit")
    return audit


def write_audit(repository_root: Path, *, output_path: Path, **kwargs: Path) -> dict[str, Any]:
    """Write a passed audit only to the designated aggregate-safe audit root."""

    root = repository_root.resolve()
    output = output_path.resolve()
    allowed_root = (root / _AUDIT_OUTPUT_ROOT).resolve()
    try:
        output.relative_to(allowed_root)
    except ValueError as error:
        raise A2ResultIntegrityAuditError("audit output must stay under outputs/audits/rigor") from error
    if output.exists() or output.is_symlink():
        raise A2ResultIntegrityAuditError("audit output already exists or is unsafe")
    result = audit_completed_closeout(root, **kwargs)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n", encoding="ascii")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a2-result-integrity-audit")
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--closeout", required=True, type=Path)
    parser.add_argument("--coverage", required=True, type=Path)
    parser.add_argument("--safe-return", required=True, dest="safe_return", type=Path)
    parser.add_argument("--terminal-checkpoint", required=True, dest="terminal_checkpoint", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = write_audit(
        args.repository_root,
        output_path=args.output,
        closeout_path=args.closeout,
        coverage_path=args.coverage,
        safe_return_path=args.safe_return,
        terminal_checkpoint_path=args.terminal_checkpoint,
    )
    print(json.dumps({"status": result["status"], "audit_sha256": result["audit_sha256"]}, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
