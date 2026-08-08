"""Validate sanitized A1.2 v12 live-provider admission inputs without provider access.

This validator checks a future Owner-supplied identity/quote shape locally.  A
valid input remains ``PENDING_LIVE_PROVIDER`` and does not constitute admission.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only


TEMPLATE_PATH = Path("control/armindex/a1.2/provider-admission-input-template.v12.json")
SCHEMA_PATH = Path("schemas/armindex/a1.2-provider-admission-input.v12.json")
STATUS = "PENDING_LIVE_PROVIDER"
MAXIMUM_AGE_SECONDS = 900
_HASH = re.compile(r"^[a-f0-9]{64}$")
_FORBIDDEN_KEY = re.compile(r"(?:^|_)(?:raw_)?instance(?:_id)?s?$|credential|secret|password|api_?key|private_?key|token|endpoint|ssh", re.IGNORECASE)
_SECRET = re.compile(r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\bsk-[A-Za-z0-9_-]{12,}|\bBearer\s+[A-Za-z0-9._~+/-]{12,})", re.IGNORECASE)


class ProviderAdmissionInputV12Error(ValueError):
    """Raised when a candidate is not a safe, exact, fresh admission input."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProviderAdmissionInputV12Error(f"invalid JSON: {path.as_posix()}") from error
    if not isinstance(value, dict):
        raise ProviderAdmissionInputV12Error(f"JSON object required: {path.as_posix()}")
    return value


def _utc(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        raise ProviderAdmissionInputV12Error(f"{label} must be a UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ProviderAdmissionInputV12Error(f"{label} must be a UTC timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ProviderAdmissionInputV12Error(f"{label} must be a UTC timestamp")
    return parsed.astimezone(timezone.utc)


def _safe(value: Mapping[str, Any]) -> None:
    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise ProviderAdmissionInputV12Error(str(error)) from error
    def walk(item: object) -> None:
        if isinstance(item, Mapping):
            for key, child in item.items():
                if _FORBIDDEN_KEY.search(str(key)):
                    raise ProviderAdmissionInputV12Error(f"unsafe provider field: {key}")
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)
    walk(value)
    if _SECRET.search(json.dumps(value, ensure_ascii=True, sort_keys=True)):
        raise ProviderAdmissionInputV12Error("credential-like value is forbidden")


def _template(root: Path) -> dict[str, Any]:
    template = _load(root / TEMPLATE_PATH)
    body = {key: value for key, value in template.items() if key != "template_sha256"}
    if template.get("template_sha256") != canonical_sha256(body):
        raise ProviderAdmissionInputV12Error("provider-admission template self-hash mismatch")
    if any(template.get(key) != value for key, value in {
        "schema_version": "myis.armindex-a1.2-provider-admission-input-template.v12",
        "status": STATUS,
        "provider_contacted": False,
        "gpu_reserved": False,
        "launch_allowed": False,
        "adopted_for_execution": False,
    }.items()):
        raise ProviderAdmissionInputV12Error("provider-admission template authorization drift")
    if template.get("freshness") != {"maximum_age_seconds": MAXIMUM_AGE_SECONDS, "timestamps_must_be_utc": True}:
        raise ProviderAdmissionInputV12Error("provider-admission template freshness drift")
    return template


def validate_candidate(repository_root: Path, candidate: Mapping[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    """Validate a sanitized future live-admission input locally and fail closed."""
    root = repository_root.resolve()
    if not isinstance(candidate, Mapping):
        raise ProviderAdmissionInputV12Error("provider admission input must be an object")
    _safe(candidate)
    template = _template(root)
    schema = _load(root / SCHEMA_PATH)
    errors = sorted(Draft202012Validator(schema).iter_errors(dict(candidate)), key=lambda error: list(error.path))
    if errors:
        raise ProviderAdmissionInputV12Error(f"provider admission schema failure: {errors[0].message}")
    if candidate["template_file_sha256"] != file_sha256(root / TEMPLATE_PATH) or candidate["template_sha256"] != template["template_sha256"]:
        raise ProviderAdmissionInputV12Error("provider admission input is not bound to the current template")

    evaluated_at = now or datetime.now(timezone.utc)
    if evaluated_at.tzinfo is None:
        raise ProviderAdmissionInputV12Error("now must be timezone-aware")
    evaluated_at = evaluated_at.astimezone(timezone.utc)
    timestamps = {
        "observed_at_utc": _utc(candidate["observed_at_utc"], "observed_at_utc"),
        "provider_identity.observed_at_utc": _utc(candidate["provider_identity"]["observed_at_utc"], "provider_identity.observed_at_utc"),
        "quote.quote_observed_at_utc": _utc(candidate["quote"]["quote_observed_at_utc"], "quote.quote_observed_at_utc"),
    }
    if timestamps["observed_at_utc"] != timestamps["provider_identity.observed_at_utc"]:
        raise ProviderAdmissionInputV12Error("identity observation timestamp must match top-level observation")
    for label, observed in timestamps.items():
        age = (evaluated_at - observed).total_seconds()
        if age < 0 or age > MAXIMUM_AGE_SECONDS:
            raise ProviderAdmissionInputV12Error(f"{label} is stale or from the future")

    quote = candidate["quote"]
    if quote["minimum_billable_seconds"] % quote["billing_granularity_seconds"] != 0:
        raise ProviderAdmissionInputV12Error("minimum billing must align with billing granularity")
    if not all(isinstance(quote[field], (int, float)) and not isinstance(quote[field], bool) and quote[field] >= 0 for field in ("compute_hourly_rate_usd", "storage_fee_usd", "network_fee_usd", "platform_or_other_fee_usd", "tax_or_surcharge_usd", "worst_case_total_charge_usd")):
        raise ProviderAdmissionInputV12Error("all fee values must be known non-negative numbers")
    if not _HASH.fullmatch(str(candidate["provider_identity"]["instance_identity_sha256"])) or not _HASH.fullmatch(str(candidate["provider_identity"]["gpu_uuid_set_sha256"])):
        raise ProviderAdmissionInputV12Error("provider identity commitments must be SHA-256")
    return {
        "status": STATUS,
        "provider_contact_allowed": False,
        "launch_allowed": False,
        "adopted_for_execution": False,
        "template_file_sha256": candidate["template_file_sha256"],
        "input_sha256": canonical_sha256(dict(candidate)),
        "maximum_age_seconds": MAXIMUM_AGE_SECONDS,
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-provider-admission-input-v12")
    parser.add_argument("validate", nargs="?")
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate_candidate(args.repository_root, _load(args.input)), ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
