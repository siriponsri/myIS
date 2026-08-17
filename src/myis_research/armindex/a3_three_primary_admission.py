"""Build hash-bound live admission evidence for the three-primary A3 run.

This module accepts only allowlisted provider facts.  It deliberately records
neither credentials nor provider payloads, and it performs no provider I/O.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import re
from typing import Any

from ..kernel.canonical import canonical_sha256
from .a3_three_primary_execution import validate_three_primary_admission
from .a3_three_primary_preparation import (
    validate_three_primary_authority,
    validate_three_primary_budget_extension,
    validate_three_primary_manifest,
)


_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_IDENTITY_KEYS = {
    "provider",
    "instance_id",
    "machine_id",
    "status",
    "gpu_count",
    "gpu_model",
    "ssh_runtime_sha256",
}


class A3ThreePrimaryAdmissionError(ValueError):
    """Raised when live A3 evidence is incomplete, stale, or over budget."""


def build_three_primary_live_admission(
    *,
    budget: Mapping[str, Any],
    authority: Mapping[str, Any],
    manifest: Mapping[str, Any],
    provider_identity: Mapping[str, Any],
    observed_at_utc: datetime,
    all_fee_usd_per_hour: Decimal | str | float,
    target_ttl_seconds: int = 48 * 60 * 60,
    a1_actual_usd: Decimal | str | float,
    extra_a3_contingency_usd: Decimal | str | float = "0",
    now_utc: datetime | None = None,
) -> dict[str, dict[str, Any]]:
    """Return provider, quote, budget, and final admission receipts.

    ``observed_at_utc`` is measured from the authenticated allowlisted Vast
    status observation.  The quote is accepted for at most the 900 seconds
    specified by the immutable A3 control.
    """

    checked_budget = validate_three_primary_budget_extension(budget)
    checked_authority = validate_three_primary_authority(authority)
    checked_manifest = validate_three_primary_manifest(manifest, authority=checked_authority)
    identity = _validate_provider_identity(provider_identity)
    observed = _utc(observed_at_utc, field="observed_at_utc")
    current = _utc(now_utc or datetime.now(timezone.utc), field="now_utc")
    quote_age_seconds = int((current - observed).total_seconds())
    if quote_age_seconds < 0 or quote_age_seconds > 900:
        raise A3ThreePrimaryAdmissionError("A3 provider quote is stale")
    if isinstance(target_ttl_seconds, bool) or target_ttl_seconds < 48 * 60 * 60:
        raise A3ThreePrimaryAdmissionError("A3 target TTL must be at least 48 hours")

    rate = _amount(all_fee_usd_per_hour, field="all_fee_usd_per_hour")
    contingency = _amount(extra_a3_contingency_usd, field="extra_a3_contingency_usd")
    if rate <= 0:
        raise A3ThreePrimaryAdmissionError("all-fee hourly rate must be positive")
    a3_projection = rate * Decimal(target_ttl_seconds) / Decimal(3600) + contingency
    if a3_projection > Decimal("35"):
        raise A3ThreePrimaryAdmissionError("A3 projected spend exceeds the hard stop")
    a1_actual = _amount(a1_actual_usd, field="a1_actual_usd")
    a2_actual = _amount(
        checked_budget["a2_closeout_bindings"]["a2_whole_workload_total_usd"],
        field="a2_actual_usd",
    )
    campaign_projection = a1_actual + a2_actual + a3_projection
    if campaign_projection > Decimal("180"):
        raise A3ThreePrimaryAdmissionError("campaign projected spend exceeds the hard stop")

    provider_body = {
        "schema_version": "myis.armindex-a3-three-primary-provider-identity.v1",
        "status": "PASS_A3_PROVIDER_IDENTITY",
        "observed_at_utc": _iso(observed),
        "provider_identity": identity,
    }
    provider_receipt = {**provider_body, "receipt_sha256": canonical_sha256(provider_body)}
    quote_body = {
        "schema_version": "myis.armindex-a3-three-primary-all-fee-quote.v1",
        "status": "PASS_A3_FRESH_ALL_FEE_QUOTE",
        "provider_identity_receipt_sha256": provider_receipt["receipt_sha256"],
        "observed_at_utc": _iso(observed),
        "currency": "USD",
        "all_fee_usd_per_hour": _decimal(rate),
        "target_ttl_seconds": target_ttl_seconds,
        "a3_compute_projection_usd": _decimal(rate * Decimal(target_ttl_seconds) / Decimal(3600)),
        "extra_a3_contingency_usd": _decimal(contingency),
        "a3_projected_total_usd": _decimal(a3_projection),
    }
    quote_receipt = {**quote_body, "receipt_sha256": canonical_sha256(quote_body)}
    budget_body = {
        "schema_version": "myis.armindex-a3-three-primary-campaign-budget-amendment.v1",
        "status": "PASS_A3_CAMPAIGN_BUDGET_ADMISSION",
        "budget_extension_sha256": checked_budget["budget_extension_sha256"],
        "a2_closeout_receipt_sha256": checked_authority["a2_predecessor_bindings"]["a2_closeout_receipt_sha256"],
        "a1_actual_usd": _decimal(a1_actual),
        "a2_actual_usd": _decimal(a2_actual),
        "a3_projected_total_usd": _decimal(a3_projection),
        "campaign_projected_total_usd": _decimal(campaign_projection),
        "a3_hard_stop_usd": "35",
        "campaign_hard_stop_usd": "180",
    }
    budget_receipt = {**budget_body, "receipt_sha256": canonical_sha256(budget_body)}
    admission_body = {
        "schema_version": "myis.armindex-a3-three-primary-admission.v1",
        "status": "PASS_A3_FRESH_ADMISSION",
        "budget_extension_sha256": checked_budget["budget_extension_sha256"],
        "authority_sha256": checked_authority["authority_sha256"],
        "manifest_sha256": checked_manifest["manifest_sha256"],
        "a2_closeout_receipt_sha256": checked_authority["a2_predecessor_bindings"]["a2_closeout_receipt_sha256"],
        "provider_identity_sha256": provider_receipt["receipt_sha256"],
        "all_fee_quote_sha256": quote_receipt["receipt_sha256"],
        "campaign_budget_amendment_receipt_sha256": budget_receipt["receipt_sha256"],
        "quote_age_seconds": quote_age_seconds,
        "target_ttl_seconds": target_ttl_seconds,
        "a3_projected_total_usd": _decimal(a3_projection),
        "campaign_projected_total_usd": _decimal(campaign_projection),
    }
    admission = {**admission_body, "admission_sha256": canonical_sha256(admission_body)}
    validate_three_primary_admission(
        admission,
        budget=checked_budget,
        authority=checked_authority,
        manifest=checked_manifest,
    )
    return {
        "provider_identity": provider_receipt,
        "all_fee_quote": quote_receipt,
        "campaign_budget_amendment": budget_receipt,
        "admission": admission,
    }


def _validate_provider_identity(value: Mapping[str, Any]) -> dict[str, Any]:
    identity = dict(value)
    if set(identity) != _IDENTITY_KEYS:
        raise A3ThreePrimaryAdmissionError("provider identity fields are incomplete")
    if (
        identity["provider"] != "vast"
        or identity["status"] != "running"
        or identity["gpu_count"] != 4
        or identity["gpu_model"] != "RTX_3090"
        or isinstance(identity["instance_id"], bool)
        or not isinstance(identity["instance_id"], int)
        or identity["instance_id"] <= 0
        or isinstance(identity["machine_id"], bool)
        or not isinstance(identity["machine_id"], int)
        or identity["machine_id"] <= 0
    ):
        raise A3ThreePrimaryAdmissionError("provider identity does not match the authorized runtime")
    _hash(identity["ssh_runtime_sha256"], field="ssh_runtime_sha256")
    return identity


def _utc(value: datetime, *, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise A3ThreePrimaryAdmissionError(f"{field} must be timezone-aware")
    return value.astimezone(timezone.utc).replace(microsecond=0)


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _amount(value: Decimal | str | float, *, field: str) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise A3ThreePrimaryAdmissionError(f"{field} is invalid") from error
    if not amount.is_finite() or amount < 0:
        raise A3ThreePrimaryAdmissionError(f"{field} is invalid")
    return amount


def _decimal(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _hash(value: Any, *, field: str) -> None:
    if not _SHA256.fullmatch(str(value)):
        raise A3ThreePrimaryAdmissionError(f"{field} must be SHA-256")


__all__ = ["A3ThreePrimaryAdmissionError", "build_three_primary_live_admission"]
