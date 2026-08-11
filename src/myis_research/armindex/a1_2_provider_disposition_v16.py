"""Write and validate aggregate-safe A1.2 v16 provider-disposition receipts.

This utility never contacts a provider, opens SSH, or changes provider state.
It accepts only a small Owner-sanitized closeout observation and writes one
immutable receipt outside the repository.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_json, canonical_sha256
from ..protection import assert_aggregate_only

SCHEMA_PATH = Path("schemas/armindex/a1.2-provider-disposition-receipt.v16.json")
RECEIPT_NAME = "provider-disposition.receipt.v16.json"
_ATTEMPT = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
_INSTANCE = re.compile(r"^[1-9][0-9]{3,18}$")
_HASH = re.compile(r"^[a-f0-9]{64}$")
_CHARGE = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,6})?$")


class ProviderDispositionV16Error(ValueError):
    """Raised when closeout evidence is incomplete, unsafe, or mutable."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProviderDispositionV16Error(f"invalid ASCII JSON: {path.as_posix()}") from error
    if not isinstance(value, dict):
        raise ProviderDispositionV16Error(f"JSON object required: {path.as_posix()}")
    return value


def _exact(value: object, fields: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise ProviderDispositionV16Error(f"{label} fields are incomplete or unsafe")
    return value


def _utc_timestamp(value: object) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ProviderDispositionV16Error("observed_at_utc must be an RFC3339 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ProviderDispositionV16Error("observed_at_utc must be an RFC3339 UTC timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ProviderDispositionV16Error("observed_at_utc must be UTC")
    return value


def _schema(repository_root: Path, receipt: Mapping[str, Any]) -> None:
    schema = _load(repository_root / SCHEMA_PATH)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(receipt)),
        key=lambda error: list(error.path),
    )
    if errors:
        raise ProviderDispositionV16Error(f"schema validation failed: {errors[0].message}")


def _self_hash(receipt: Mapping[str, Any]) -> None:
    body = dict(receipt)
    actual = body.pop("receipt_sha256", None)
    if actual != canonical_sha256(body):
        raise ProviderDispositionV16Error("receipt_sha256 mismatch")


def _validate_input(value: Mapping[str, Any]) -> dict[str, Any]:
    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise ProviderDispositionV16Error(str(error)) from error
    top = _exact(
        value,
        {"attempt_id", "instance_id", "observed_at_utc", "provider_authentication", "ssh_endpoint", "final_charge_usd", "final_quote_sha256"},
        "provider disposition input",
    )
    attempt_id = top["attempt_id"]
    if not isinstance(attempt_id, str) or _ATTEMPT.fullmatch(attempt_id) is None:
        raise ProviderDispositionV16Error("attempt_id is invalid")
    instance_id = top["instance_id"]
    if not isinstance(instance_id, str) or _INSTANCE.fullmatch(instance_id) is None:
        raise ProviderDispositionV16Error("instance_id is invalid")
    observed_at_utc = _utc_timestamp(top["observed_at_utc"])
    provider = _exact(top["provider_authentication"], {"authenticated", "destroy_outcome", "provider_absence_verified"}, "provider authentication")
    if provider != {"authenticated": True, "destroy_outcome": "DESTROYED_CONFIRMED", "provider_absence_verified": True}:
        raise ProviderDispositionV16Error("authenticated provider destruction and absence are required")
    endpoint = _exact(top["ssh_endpoint"], {"post_destroy_observation"}, "SSH endpoint")
    if endpoint != {"post_destroy_observation": "connection_refused"}:
        raise ProviderDispositionV16Error("post-destroy SSH observation must be connection_refused")
    charge = top["final_charge_usd"]
    if charge is not None and (not isinstance(charge, str) or _CHARGE.fullmatch(charge) is None):
        raise ProviderDispositionV16Error("final_charge_usd must be a canonical non-negative decimal or null")
    quote = top["final_quote_sha256"]
    if quote is not None and (not isinstance(quote, str) or _HASH.fullmatch(quote) is None):
        raise ProviderDispositionV16Error("final_quote_sha256 must be a lowercase SHA-256 or null")
    return {
        "attempt_id": attempt_id,
        "instance_id": instance_id,
        "observed_at_utc": observed_at_utc,
        "provider_authentication": dict(provider),
        "ssh_endpoint": dict(endpoint),
        "final_charge_usd": charge,
        "final_quote_sha256": quote,
    }


def build_provider_disposition_receipt(repository_root: Path, value: Mapping[str, Any]) -> dict[str, Any]:
    """Build a receipt from one already-sanitized Owner-local observation."""

    inputs = _validate_input(value)
    receipt = {
        "schema_version": "myis.armindex-a1.2-provider-disposition-receipt.v16",
        "receipt_id": f"{inputs['attempt_id']}-provider-disposition-v16",
        "attempt_id": inputs["attempt_id"],
        "status": "PASS",
        "evidence_class": "aggregate_safe_provider_disposition",
        "scientific_authority": False,
        "claim_boundary": "Authenticated provider destruction and instance absence plus a post-destroy SSH connection-refused observation; lifecycle evidence only, with no retrieval-quality, execution-adoption, or publication claim.",
        "instance_id": inputs["instance_id"],
        "observed_at_utc": inputs["observed_at_utc"],
        "provider_authentication": inputs["provider_authentication"],
        "ssh_endpoint": inputs["ssh_endpoint"],
        "final_charge_usd": inputs["final_charge_usd"],
        "final_quote_sha256": inputs["final_quote_sha256"],
        "access_counters": {"harness_dev_accesses": 0, "selection_accesses": 0, "final_accesses": 0},
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    return validate_provider_disposition_receipt(repository_root, receipt)


def validate_provider_disposition_receipt(repository_root: Path, receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a portable receipt without contacting any external system."""

    if not isinstance(receipt, Mapping):
        raise ProviderDispositionV16Error("provider disposition receipt must be an object")
    try:
        assert_aggregate_only(receipt)
    except ValueError as error:
        raise ProviderDispositionV16Error(str(error)) from error
    root = repository_root.resolve()
    _schema(root, receipt)
    _self_hash(receipt)
    values = _validate_input({key: receipt[key] for key in ("attempt_id", "instance_id", "observed_at_utc", "provider_authentication", "ssh_endpoint", "final_charge_usd", "final_quote_sha256")})
    if receipt.get("receipt_id") != f"{values['attempt_id']}-provider-disposition-v16":
        raise ProviderDispositionV16Error("receipt_id does not bind attempt_id")
    if receipt.get("status") != "PASS" or receipt.get("scientific_authority") is not False:
        raise ProviderDispositionV16Error("provider disposition receipt status drifted")
    counters = receipt.get("access_counters")
    if counters != {"harness_dev_accesses": 0, "selection_accesses": 0, "final_accesses": 0}:
        raise ProviderDispositionV16Error("protected access counters must remain zero")
    return dict(receipt)


def _external_receipt_path(repository_root: Path, receipt_path: Path) -> Path:
    root = repository_root.resolve()
    target = receipt_path.resolve()
    if target == root or target.is_relative_to(root):
        raise ProviderDispositionV16Error("provider disposition receipt must remain outside the repository")
    if target.name != RECEIPT_NAME:
        raise ProviderDispositionV16Error(f"receipt file must be named {RECEIPT_NAME}")
    if target.parent.is_symlink():
        raise ProviderDispositionV16Error("provider disposition receipt directory must not be a symlink")
    return target


def write_provider_disposition_receipt(repository_root: Path, receipt_path: Path, receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Write the receipt once to an explicit Owner-local path outside Git."""

    validated = validate_provider_disposition_receipt(repository_root, receipt)
    target = _external_receipt_path(repository_root, receipt_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.parent.is_symlink():
        raise ProviderDispositionV16Error("provider disposition receipt directory must not be a symlink")
    payload = canonical_json(validated) + "\n"
    if target.exists():
        if target.is_symlink() or target.read_text(encoding="ascii") != payload:
            raise ProviderDispositionV16Error("immutable provider disposition receipt already differs")
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


def read_provider_disposition_receipt(repository_root: Path, receipt_path: Path) -> dict[str, Any]:
    """Read and validate a receipt from the explicit Owner-local path."""

    target = _external_receipt_path(repository_root, receipt_path)
    if not target.is_file() or target.is_symlink():
        raise ProviderDispositionV16Error("provider disposition receipt is missing or unsafe")
    return validate_provider_disposition_receipt(repository_root, _load(target))


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-provider-disposition-v16")
    parser.add_argument("command", choices=("build", "validate"))
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--receipt-path", required=True, type=Path)
    parser.add_argument("--input", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "build":
            if args.input is None:
                raise ProviderDispositionV16Error("--input is required for build")
            result = write_provider_disposition_receipt(
                args.repository_root,
                args.receipt_path,
                build_provider_disposition_receipt(args.repository_root, _load(args.input)),
            )
        else:
            if args.input is not None:
                raise ProviderDispositionV16Error("--input is only valid for build")
            result = read_provider_disposition_receipt(args.repository_root, args.receipt_path)
    except (ProviderDispositionV16Error, OSError) as error:
        parser.error(str(error))
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "RECEIPT_NAME",
    "SCHEMA_PATH",
    "ProviderDispositionV16Error",
    "build_provider_disposition_receipt",
    "read_provider_disposition_receipt",
    "validate_provider_disposition_receipt",
    "write_provider_disposition_receipt",
]
