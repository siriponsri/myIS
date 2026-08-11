"""Build aggregate-safe provider-continuation receipts after A1.2 closeout.

This module deliberately never calls a provider, opens SSH, launches work, or
changes lifecycle state. It only validates a narrow Owner-sanitized observation
and writes an immutable receipt outside the repository.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_json, canonical_sha256
from ..protection import assert_aggregate_only

SCHEMA_PATH = Path("schemas/armindex/a1.2-provider-continuation-receipt.v16.json")
RECEIPT_NAME = "provider-continuation.receipt.v16.json"
FRESHNESS_SECONDS = 900
_ATTEMPT = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
_INSTANCE = re.compile(r"^[1-9][0-9]{3,18}$")
_HASH = re.compile(r"^[a-f0-9]{64}$")
_AMOUNT = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,6})?$")


class ProviderContinuationV16Error(ValueError):
    """Raised when continuation evidence is incomplete, unsafe, or mutable."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProviderContinuationV16Error(f"invalid ASCII JSON: {path.as_posix()}") from error
    if not isinstance(value, dict):
        raise ProviderContinuationV16Error(f"JSON object required: {path.as_posix()}")
    return value


def _exact(value: object, fields: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise ProviderContinuationV16Error(f"{label} fields are incomplete or unsafe")
    return value


def _hash(value: object, label: str) -> str:
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise ProviderContinuationV16Error(f"{label} must be a lowercase SHA-256")
    return value


def _amount(value: object, label: str, *, positive: bool = False) -> str:
    if not isinstance(value, str) or _AMOUNT.fullmatch(value) is None:
        raise ProviderContinuationV16Error(f"{label} must be a canonical non-negative USD decimal")
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise ProviderContinuationV16Error(f"{label} is invalid") from error
    if positive and parsed <= 0:
        raise ProviderContinuationV16Error(f"{label} must be positive")
    return value


def _utc(value: object, label: str, *, now: datetime) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ProviderContinuationV16Error(f"{label} must be an RFC3339 UTC timestamp")
    try:
        observed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ProviderContinuationV16Error(f"{label} must be an RFC3339 UTC timestamp") from error
    if observed.tzinfo is None or observed.utcoffset() != UTC.utcoffset(observed):
        raise ProviderContinuationV16Error(f"{label} must be UTC")
    age = now - observed.astimezone(UTC)
    if age < timedelta(0) or age > timedelta(seconds=FRESHNESS_SECONDS):
        raise ProviderContinuationV16Error(f"{label} is not fresh")
    return value


def _schema(repository_root: Path, receipt: Mapping[str, Any]) -> None:
    schema = _load(repository_root / SCHEMA_PATH)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(receipt)),
        key=lambda error: list(error.path),
    )
    if errors:
        raise ProviderContinuationV16Error(f"schema validation failed: {errors[0].message}")


def _self_hash(receipt: Mapping[str, Any]) -> None:
    body = dict(receipt)
    actual = body.pop("receipt_sha256", None)
    if actual != canonical_sha256(body):
        raise ProviderContinuationV16Error("receipt_sha256 mismatch")


def _validate_input(value: Mapping[str, Any], *, now: datetime) -> dict[str, Any]:
    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise ProviderContinuationV16Error(str(error)) from error
    top = _exact(
        value,
        {
            "attempt_id", "instance_id", "expected_instance_identity_sha256",
            "provider_identity", "ssh_endpoint", "current_quote", "accrued_a1_charge_usd",
            "watchdog", "safe_return_archive_sha256", "evaluator_closeout_receipt_sha256",
        },
        "provider continuation input",
    )
    attempt_id = top["attempt_id"]
    if not isinstance(attempt_id, str) or _ATTEMPT.fullmatch(attempt_id) is None:
        raise ProviderContinuationV16Error("attempt_id is invalid")
    instance_id = top["instance_id"]
    if not isinstance(instance_id, str) or _INSTANCE.fullmatch(instance_id) is None:
        raise ProviderContinuationV16Error("instance_id is invalid")
    expected_identity = _hash(top["expected_instance_identity_sha256"], "expected instance identity")
    provider = _exact(
        top["provider_identity"],
        {"observed_at_utc", "authenticated", "provider_status", "instance_identity_sha256", "provider_evidence_sha256"},
        "provider identity",
    )
    _utc(provider["observed_at_utc"], "provider identity observation", now=now)
    if provider["authenticated"] is not True or provider["provider_status"] != "RUNNING_VERIFIED":
        raise ProviderContinuationV16Error("authenticated running provider identity is required")
    provider_identity = _hash(provider["instance_identity_sha256"], "provider instance identity")
    _hash(provider["provider_evidence_sha256"], "provider evidence")
    ssh = _exact(
        top["ssh_endpoint"],
        {"observed_at_utc", "observation", "instance_identity_sha256", "ssh_evidence_sha256"},
        "SSH endpoint",
    )
    _utc(ssh["observed_at_utc"], "SSH observation", now=now)
    if ssh["observation"] != "reachable":
        raise ProviderContinuationV16Error("SSH endpoint must be reachable")
    ssh_identity = _hash(ssh["instance_identity_sha256"], "SSH instance identity")
    _hash(ssh["ssh_evidence_sha256"], "SSH evidence")
    if expected_identity != provider_identity or expected_identity != ssh_identity:
        raise ProviderContinuationV16Error("provider and SSH identity hashes must remain unchanged")
    quote = _exact(
        top["current_quote"],
        {"observed_at_utc", "quote_sha256", "all_fee_hourly_rate_usd"},
        "current quote",
    )
    _utc(quote["observed_at_utc"], "current quote observation", now=now)
    _hash(quote["quote_sha256"], "current quote hash")
    _amount(quote["all_fee_hourly_rate_usd"], "current all-fee hourly rate", positive=True)
    accrued = _amount(top["accrued_a1_charge_usd"], "accrued A1 charge")
    watchdog = _exact(
        top["watchdog"],
        {"observed_at_utc", "status", "remaining_ttl_seconds", "watchdog_evidence_sha256"},
        "watchdog",
    )
    _utc(watchdog["observed_at_utc"], "watchdog observation", now=now)
    if watchdog["status"] != "PASS":
        raise ProviderContinuationV16Error("watchdog must pass")
    if type(watchdog["remaining_ttl_seconds"]) is not int or watchdog["remaining_ttl_seconds"] < 1:
        raise ProviderContinuationV16Error("remaining TTL must be a positive integer seconds")
    _hash(watchdog["watchdog_evidence_sha256"], "watchdog evidence")
    safe_return = _hash(top["safe_return_archive_sha256"], "safe return archive")
    evaluator = _hash(top["evaluator_closeout_receipt_sha256"], "evaluator closeout receipt")
    return {
        "attempt_id": attempt_id,
        "instance_id": instance_id,
        "expected_instance_identity_sha256": expected_identity,
        "provider_identity": dict(provider),
        "ssh_endpoint": dict(ssh),
        "current_quote": dict(quote),
        "accrued_a1_charge_usd": accrued,
        "watchdog": dict(watchdog),
        "safe_return_archive_sha256": safe_return,
        "evaluator_closeout_receipt_sha256": evaluator,
    }


def build_provider_continuation_receipt(
    repository_root: Path, value: Mapping[str, Any], *, now: datetime | None = None
) -> dict[str, Any]:
    """Build a reuse-eligible receipt from fresh, already-sanitized evidence."""

    observed_now = (now or datetime.now(UTC)).astimezone(UTC)
    inputs = _validate_input(value, now=observed_now)
    receipt = {
        "schema_version": "myis.armindex-a1.2-provider-continuation-receipt.v16",
        "receipt_id": f"{inputs['attempt_id']}-provider-continuation-v16",
        "attempt_id": inputs["attempt_id"],
        "status": "PASS",
        "provider_continuation_status": "REUSE_ELIGIBLE",
        "evidence_class": "aggregate_safe_provider_continuation",
        "scientific_authority": False,
        "claim_boundary": "Aggregate-safe provider continuation evidence after A1.2 closeout only; it requires fresh A2 provider admission and execution adoption in a new isolated remote root and supports no A2, HARNESS-DEV, Selection, Final, or publication claim.",
        **inputs,
        "next_phase": {
            "phase_id": "A2_PER_ARM_AUTOINDEX",
            "fresh_a2_provider_admission_required": True,
            "fresh_a2_execution_adoption_required": True,
            "new_isolated_remote_root_required": True,
        },
        "access_counters": {"harness_dev_accesses": 0, "selection_accesses": 0, "final_accesses": 0},
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    return validate_provider_continuation_receipt(repository_root, receipt, now=observed_now)


def validate_provider_continuation_receipt(
    repository_root: Path, receipt: Mapping[str, Any], *, now: datetime | None = None
) -> dict[str, Any]:
    """Validate a portable receipt without contacting provider or SSH."""

    if not isinstance(receipt, Mapping):
        raise ProviderContinuationV16Error("provider continuation receipt must be an object")
    try:
        assert_aggregate_only(receipt)
    except ValueError as error:
        raise ProviderContinuationV16Error(str(error)) from error
    root = repository_root.resolve()
    _schema(root, receipt)
    _self_hash(receipt)
    observed_now = (now or datetime.now(UTC)).astimezone(UTC)
    inputs = _validate_input(
        {key: receipt[key] for key in (
            "attempt_id", "instance_id", "expected_instance_identity_sha256", "provider_identity",
            "ssh_endpoint", "current_quote", "accrued_a1_charge_usd", "watchdog",
            "safe_return_archive_sha256", "evaluator_closeout_receipt_sha256",
        )},
        now=observed_now,
    )
    if receipt.get("receipt_id") != f"{inputs['attempt_id']}-provider-continuation-v16":
        raise ProviderContinuationV16Error("receipt_id does not bind attempt_id")
    if receipt.get("status") != "PASS" or receipt.get("provider_continuation_status") != "REUSE_ELIGIBLE":
        raise ProviderContinuationV16Error("provider continuation status drifted")
    if receipt.get("scientific_authority") is not False:
        raise ProviderContinuationV16Error("provider continuation cannot carry scientific authority")
    if receipt.get("next_phase") != {
        "phase_id": "A2_PER_ARM_AUTOINDEX",
        "fresh_a2_provider_admission_required": True,
        "fresh_a2_execution_adoption_required": True,
        "new_isolated_remote_root_required": True,
    }:
        raise ProviderContinuationV16Error("next phase safeguards drifted")
    if receipt.get("access_counters") != {
        "harness_dev_accesses": 0,
        "selection_accesses": 0,
        "final_accesses": 0,
    }:
        raise ProviderContinuationV16Error("protected access counters must remain zero")
    return dict(receipt)


def _external_receipt_path(repository_root: Path, receipt_path: Path) -> Path:
    root = repository_root.resolve()
    target = receipt_path.resolve()
    if target == root or target.is_relative_to(root):
        raise ProviderContinuationV16Error("provider continuation receipt must remain outside the repository")
    if target.name != RECEIPT_NAME:
        raise ProviderContinuationV16Error(f"receipt file must be named {RECEIPT_NAME}")
    if target.parent.is_symlink():
        raise ProviderContinuationV16Error("provider continuation receipt directory must not be a symlink")
    return target


def write_provider_continuation_receipt(
    repository_root: Path, receipt_path: Path, receipt: Mapping[str, Any], *, now: datetime | None = None
) -> dict[str, Any]:
    """Write one immutable Owner-local receipt outside the repository."""

    validated = validate_provider_continuation_receipt(repository_root, receipt, now=now)
    target = _external_receipt_path(repository_root, receipt_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.parent.is_symlink():
        raise ProviderContinuationV16Error("provider continuation receipt directory must not be a symlink")
    payload = canonical_json(validated) + "\n"
    if target.exists():
        if target.is_symlink() or target.read_text(encoding="ascii") != payload:
            raise ProviderContinuationV16Error("immutable provider continuation receipt already differs")
        return validated
    descriptor, temporary_name = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.", suffix=".tmp")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return validated


def read_provider_continuation_receipt(
    repository_root: Path, receipt_path: Path, *, now: datetime | None = None
) -> dict[str, Any]:
    """Read and validate one explicit Owner-local continuation receipt."""

    target = _external_receipt_path(repository_root, receipt_path)
    if not target.is_file() or target.is_symlink():
        raise ProviderContinuationV16Error("provider continuation receipt is missing or unsafe")
    return validate_provider_continuation_receipt(repository_root, _load(target), now=now)


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-provider-continuation-v16")
    parser.add_argument("command", choices=("build", "validate"))
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--receipt-path", required=True, type=Path)
    parser.add_argument("--input", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "build":
            if args.input is None:
                raise ProviderContinuationV16Error("--input is required for build")
            result = write_provider_continuation_receipt(
                args.repository_root,
                args.receipt_path,
                build_provider_continuation_receipt(args.repository_root, _load(args.input)),
            )
        else:
            if args.input is not None:
                raise ProviderContinuationV16Error("--input is only valid for build")
            result = read_provider_continuation_receipt(args.repository_root, args.receipt_path)
    except (ProviderContinuationV16Error, OSError) as error:
        parser.error(str(error))
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "FRESHNESS_SECONDS",
    "RECEIPT_NAME",
    "SCHEMA_PATH",
    "ProviderContinuationV16Error",
    "build_provider_continuation_receipt",
    "read_provider_continuation_receipt",
    "validate_provider_continuation_receipt",
    "write_provider_continuation_receipt",
]
