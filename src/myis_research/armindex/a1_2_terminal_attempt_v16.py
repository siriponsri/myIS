"""Immutable aggregate-safe terminal receipts for one A1.2 v16 attempt.

This module deliberately has no provider, SSH, executor, evaluator, or launch
dependency.  It validates the repository-safe terminal boundary after those
systems have completed their own work.  The mutable current-attempt pointer is
the only projection selector; receipt files themselves are write-once.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_json, canonical_sha256
from ..protection import assert_aggregate_only

TERMINAL_SCHEMA_PATH = Path("schemas/armindex/a1.2-terminal-attempt-receipt.v16.json")
POINTER_SCHEMA_PATH = Path("schemas/armindex/a1.2-current-attempt-pointer.v16.json")
CURRENT_POINTER_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/a1.2-current-attempt.v16.json"
)
TERMINAL_RECEIPT_DIRECTORY = Path(
    "campaigns/armindex-multiretriever-v2/evidence/a1.2-terminal-attempts"
)

_ATTEMPT = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
_HASH = re.compile(r"^[a-f0-9]{64}$")
_CHARGE = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,6})?$")
_SUCCESS_HASH_FIELDS = (
    "safe_return_sha256",
    "evaluator_receipt_sha256",
    "promotion_receipt_sha256",
)
_COUNTER_FIELDS = ("harness_dev_accesses", "selection_accesses", "final_accesses")


class TerminalAttemptV16Error(ValueError):
    """Raised when terminal A1.2 evidence is incomplete, unsafe, or mutable."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise TerminalAttemptV16Error(f"invalid ASCII JSON: {path.as_posix()}") from error
    if not isinstance(value, dict):
        raise TerminalAttemptV16Error(f"JSON object required: {path.as_posix()}")
    return value


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _schema(repository_root: Path, path: Path, value: Mapping[str, Any]) -> None:
    schema = _load_json(repository_root / path)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(value)),
        key=lambda error: list(error.path),
    )
    if errors:
        raise TerminalAttemptV16Error(f"schema validation failed: {errors[0].message}")


def _require_hash(value: object, label: str) -> str:
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise TerminalAttemptV16Error(f"{label} must be a lowercase SHA-256")
    return value


def _require_self_hash(value: Mapping[str, Any], field: str) -> None:
    body = dict(value)
    actual = body.pop(field, None)
    if actual != canonical_sha256(body):
        raise TerminalAttemptV16Error(f"{field} mismatch")


def _terminal_uri(attempt_id: str) -> Path:
    return TERMINAL_RECEIPT_DIRECTORY / f"{attempt_id}.receipt.v16.json"


def build_terminal_attempt_receipt(
    *,
    repository_root: Path,
    attempt_id: str,
    status: str,
    completed_logical_cells: int,
    provider_disposition_receipt_sha256: str,
    provider_disposition_status: str,
    final_charge_usd: str,
    claim_boundary: str,
    safe_return_sha256: str | None = None,
    evaluator_receipt_sha256: str | None = None,
    promotion_receipt_sha256: str | None = None,
    failure_evidence_sha256: str | None = None,
) -> dict[str, Any]:
    """Build one terminal receipt; validation defines the allowed state space."""

    receipt = {
        "schema_version": "myis.armindex-a1.2-terminal-attempt-receipt.v16",
        "receipt_id": f"{attempt_id}-terminal-v16",
        "attempt_id": attempt_id,
        "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
        "task_id": "A1.2",
        "status": status,
        "evidence_class": (
            "aggregate_safe_live_attempt_terminal"
            if status == "PASS"
            else "aggregate_safe_live_attempt_failure"
        ),
        "scientific_authority": status == "PASS",
        "claim_boundary": claim_boundary,
        "coverage": {
            "required_logical_cells": 25,
            "completed_logical_cells": completed_logical_cells,
            "partial_results_promotable": False,
        },
        "provider_disposition_receipt_sha256": provider_disposition_receipt_sha256,
        "provider_disposition_status": provider_disposition_status,
        "access_counters": {
            "harness_dev_accesses": 0,
            "selection_accesses": 0,
            "final_accesses": 0,
        },
        "final_charge_usd": final_charge_usd,
    }
    if status == "PASS":
        receipt.update(
            {
                "safe_return_sha256": safe_return_sha256,
                "evaluator_receipt_sha256": evaluator_receipt_sha256,
                "promotion_receipt_sha256": promotion_receipt_sha256,
            }
        )
    elif status == "FAILED_CLOSED":
        receipt["failure_evidence_sha256"] = failure_evidence_sha256
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    validate_terminal_attempt_receipt(repository_root, receipt)
    return receipt


def validate_terminal_attempt_receipt(
    repository_root: Path, receipt: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate one terminal state without reading protected inputs or outputs."""

    root = repository_root.resolve()
    if not isinstance(receipt, Mapping):
        raise TerminalAttemptV16Error("terminal receipt must be an object")
    try:
        assert_aggregate_only(receipt)
    except ValueError as error:
        raise TerminalAttemptV16Error(str(error)) from error
    _schema(root, TERMINAL_SCHEMA_PATH, receipt)
    _require_self_hash(receipt, "receipt_sha256")
    attempt_id = receipt["attempt_id"]
    if not isinstance(attempt_id, str) or _ATTEMPT.fullmatch(attempt_id) is None:
        raise TerminalAttemptV16Error("attempt_id is invalid")
    if receipt["receipt_id"] != f"{attempt_id}-terminal-v16":
        raise TerminalAttemptV16Error("receipt_id does not bind attempt_id")
    _require_hash(
        receipt["provider_disposition_receipt_sha256"],
        "provider_disposition_receipt_sha256",
    )
    coverage = receipt["coverage"]
    if not isinstance(coverage, Mapping):
        raise TerminalAttemptV16Error("coverage must be an object")
    completed = coverage["completed_logical_cells"]
    if type(completed) is not int or not 0 <= completed <= 25:
        raise TerminalAttemptV16Error("completed logical-cell count is invalid")
    counters = receipt["access_counters"]
    if not isinstance(counters, Mapping) or set(counters) != set(_COUNTER_FIELDS):
        raise TerminalAttemptV16Error("access counters are incomplete")
    if any(type(counters[key]) is not int or counters[key] != 0 for key in _COUNTER_FIELDS):
        raise TerminalAttemptV16Error("protected access counters must remain zero")
    charge = receipt["final_charge_usd"]
    if not isinstance(charge, str) or _CHARGE.fullmatch(charge) is None:
        raise TerminalAttemptV16Error("final charge must be a nonnegative USD decimal")
    status = receipt["status"]
    if status == "PASS":
        if completed != 25 or receipt["scientific_authority"] is not True:
            raise TerminalAttemptV16Error("PASS requires complete 25/25 coverage and authority")
        for field in _SUCCESS_HASH_FIELDS:
            _require_hash(receipt.get(field), field)
        if "failure_evidence_sha256" in receipt:
            raise TerminalAttemptV16Error("PASS cannot carry failure evidence")
    elif status == "FAILED_CLOSED":
        if receipt["scientific_authority"] is not False:
            raise TerminalAttemptV16Error("FAILED_CLOSED cannot carry scientific authority")
        _require_hash(receipt.get("failure_evidence_sha256"), "failure_evidence_sha256")
        if any(receipt.get(field) is not None for field in _SUCCESS_HASH_FIELDS):
            raise TerminalAttemptV16Error("FAILED_CLOSED cannot carry success-only hashes")
    else:
        raise TerminalAttemptV16Error("terminal status is invalid")
    return dict(receipt)


def build_current_attempt_pointer(
    receipt: Mapping[str, Any], *, target_sha256: str
) -> dict[str, Any]:
    """Build the sole mutable selector for a validated terminal receipt."""

    attempt = receipt.get("attempt_id")
    if not isinstance(attempt, str):
        raise TerminalAttemptV16Error("terminal receipt attempt_id is required")
    pointer = {
        "schema_version": "myis.armindex-a1.2-current-attempt-pointer.v16",
        "pointer_id": "a1.2-current-attempt-v16",
        "attempt_id": attempt,
        "status": receipt.get("status"),
        "target_uri": _terminal_uri(attempt).as_posix(),
        "target_sha256": target_sha256,
    }
    pointer["pointer_sha256"] = canonical_sha256(pointer)
    return pointer


def _validate_pointer_shape(repository_root: Path, pointer: Mapping[str, Any]) -> Path:
    root = repository_root.resolve()
    try:
        assert_aggregate_only(pointer)
    except ValueError as error:
        raise TerminalAttemptV16Error(str(error)) from error
    _schema(root, POINTER_SCHEMA_PATH, pointer)
    _require_self_hash(pointer, "pointer_sha256")
    target_uri = pointer["target_uri"]
    if not isinstance(target_uri, str) or "\\" in target_uri:
        raise TerminalAttemptV16Error("pointer target URI is invalid")
    relative = PurePosixPath(target_uri)
    if relative.is_absolute() or ".." in relative.parts or ":" in target_uri:
        raise TerminalAttemptV16Error("pointer target URI escapes the repository")
    target = root.joinpath(*relative.parts)
    expected = _terminal_uri(str(pointer["attempt_id"]))
    if relative.as_posix() != expected.as_posix():
        raise TerminalAttemptV16Error("pointer target does not bind attempt_id")
    return target


def validate_current_attempt_pointer(
    repository_root: Path, pointer_path: Path | None = None
) -> dict[str, Any]:
    """Read the one hash-bound current attempt; never scan receipt directories."""

    root = repository_root.resolve()
    path = (pointer_path or root / CURRENT_POINTER_PATH).resolve()
    if not path.is_file() or path.is_symlink():
        raise TerminalAttemptV16Error("current attempt pointer is missing or unsafe")
    try:
        path.relative_to(root)
    except ValueError as error:
        raise TerminalAttemptV16Error("current attempt pointer escapes repository") from error
    pointer = _load_json(path)
    target = _validate_pointer_shape(root, pointer)
    if not target.is_file() or target.is_symlink():
        raise TerminalAttemptV16Error("terminal receipt is missing or unsafe")
    if _file_sha256(target) != pointer["target_sha256"]:
        raise TerminalAttemptV16Error("terminal receipt file hash mismatch")
    receipt = validate_terminal_attempt_receipt(root, _load_json(target))
    if receipt["attempt_id"] != pointer["attempt_id"] or receipt["status"] != pointer["status"]:
        raise TerminalAttemptV16Error("pointer and terminal receipt disagree")
    return {
        "pointer": dict(pointer),
        "receipt": receipt,
        "pointer_file_sha256": _file_sha256(path),
        "receipt_file_sha256": _file_sha256(target),
    }


def _write_immutable(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = canonical_json(dict(value)) + "\n"
    if path.exists():
        if path.is_symlink() or path.read_text(encoding="ascii") != text:
            raise TerminalAttemptV16Error(f"immutable receipt differs: {path.name}")
        return
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_terminal_attempt_receipt(repository_root: Path, receipt: Mapping[str, Any]) -> Path:
    """Write an immutable receipt to the canonical repository-safe receipt root."""

    root = repository_root.resolve()
    validated = validate_terminal_attempt_receipt(root, receipt)
    path = root / _terminal_uri(str(validated["attempt_id"]))
    _write_immutable(path, validated)
    return path


def write_current_attempt_pointer(repository_root: Path, pointer: Mapping[str, Any]) -> Path:
    """Atomically update the current selector only after its target validates."""

    root = repository_root.resolve()
    target = _validate_pointer_shape(root, pointer)
    if not target.is_file() or target.is_symlink():
        raise TerminalAttemptV16Error("pointer target must be an existing immutable receipt")
    if _file_sha256(target) != pointer["target_sha256"]:
        raise TerminalAttemptV16Error("pointer target file hash mismatch")
    receipt = validate_terminal_attempt_receipt(root, _load_json(target))
    if receipt["attempt_id"] != pointer["attempt_id"] or receipt["status"] != pointer["status"]:
        raise TerminalAttemptV16Error("pointer and receipt do not match")
    path = root / CURRENT_POINTER_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="") as handle:
            handle.write(canonical_json(dict(pointer)) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


__all__ = [
    "CURRENT_POINTER_PATH",
    "POINTER_SCHEMA_PATH",
    "TERMINAL_RECEIPT_DIRECTORY",
    "TERMINAL_SCHEMA_PATH",
    "TerminalAttemptV16Error",
    "build_current_attempt_pointer",
    "build_terminal_attempt_receipt",
    "validate_current_attempt_pointer",
    "validate_terminal_attempt_receipt",
    "write_current_attempt_pointer",
    "write_terminal_attempt_receipt",
]
