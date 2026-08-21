"""Hash-bound aggregate-safe contracts for ArmIndex A4 and its A5 handoff.

This module deliberately owns no qrels, split membership, raw queries, rankings,
or model payloads.  Those inputs remain in the Owner Store and are represented
here only by validated hashes, counts, and opaque pointers.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import re
from typing import Any

from ..kernel.canonical import canonical_sha256


_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_GIT_ID = re.compile(r"^[a-f0-9]{40}(?:[a-f0-9]{24})?$")
_ATTEMPT = re.compile(r"^a[45]-goal001-[0-9]{8}T[0-9]{6}Z(?:-[a-z0-9]+)?$")
PRIMARY_ARMS = ("ARM-03", "ARM-04", "ARM-05")
COMMERCIAL_ARMS = ("ARM-01", "ARM-02", "ARM-04", "ARM-05")
PROFILES = ("FAST", "BALANCED", "DEEP")
FINALIST_ROLES = (
    "static_common_baseline",
    "single_arm_autoindex",
    "research_champion",
    "commercial_production_champion",
)
_PROTECTED_KEY_PARTS = (
    "credential",
    "family_id",
    "final_feedback",
    "membership",
    "per_query",
    "provider_payload",
    "qrel",
    "query_id",
    "ranking",
    "raw_query",
    "secret",
    "selection_feedback",
)


class A4ExecutionError(ValueError):
    """Raised when a measurement or Final-continuity boundary is invalid."""


def validate_a4_predecessor_binding(binding: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the current A3 closeout binding, not its historical draft files."""

    value = _copy_safe(binding, role="A4 predecessor binding")
    required = {
        "a3_attempt_id",
        "a3_closeout_verified",
        "a3_harnessopt_evaluation_sha256",
        "a3_result_integrity_audit_sha256",
        "a3_safe_return_receipt_sha256",
        "binding_sha256",
        "claim_boundary",
        "final_permitted",
        "fixed_control_count",
        "harnessopt_candidate_count",
        "harnessopt_complete_batch_count",
        "harnessopt_unique_action_signature_count",
        "measured_execution",
        "phase_id",
        "primary_arm_scope",
        "protected_payload_included",
        "runtime_bindings_sha256",
        "schema_version",
        "selection_permitted",
        "status",
        "train250_query_count",
        "transfer_operation_count",
        "winner_program_sha256s",
    }
    if set(value) != required:
        raise A4ExecutionError("A4 predecessor binding fields are incomplete")
    if (
        value["schema_version"] != "myis.armindex-a4-readiness-binding.v1"
        or value["phase_id"] != "A4_PRODUCTION_TRANSFER_AND_SELECTION"
        or value["status"] != "contract_only_ready"
        or value["a3_closeout_verified"] is not True
        or value["measured_execution"] is not False
        or value["selection_permitted"] is not False
        or value["final_permitted"] is not False
        or value["protected_payload_included"] is not False
        or value["primary_arm_scope"] != list(PRIMARY_ARMS)
        or value["transfer_operation_count"] != 9
        or value["fixed_control_count"] != 5
        or value["train250_query_count"] != 250
    ):
        raise A4ExecutionError("A4 predecessor binding has scientific-state drift")
    for field in (
        "a3_harnessopt_evaluation_sha256",
        "a3_result_integrity_audit_sha256",
        "a3_safe_return_receipt_sha256",
        "binding_sha256",
        "runtime_bindings_sha256",
    ):
        _hash(value[field], field)
    winners = value["winner_program_sha256s"]
    if not isinstance(winners, Mapping) or set(winners) != set(PRIMARY_ARMS):
        raise A4ExecutionError("A4 predecessor winner scope is invalid")
    for arm_id in PRIMARY_ARMS:
        _hash(winners[arm_id], f"{arm_id} winner program")
    return value


def build_d1_continuation_receipt(
    *, attempt_id: str, predecessor_binding_sha256: str, goal_revision: str, recorded_at_utc: datetime
) -> dict[str, Any]:
    """Record the Owner's current A4 instruction without rewriting D1 history."""

    _attempt(attempt_id)
    _hash(predecessor_binding_sha256, "predecessor_binding_sha256")
    if not isinstance(goal_revision, str) or not _GIT_ID.fullmatch(goal_revision):
        raise A4ExecutionError("goal revision must be the clean Git commit SHA-1 or SHA-256")
    body = {
        "schema_version": "myis.armindex-a4-d1-continuation-receipt.v1",
        "status": "PASS_A4_D1_CONTINUATION_RECORDED",
        "attempt_id": attempt_id,
        "owner_decision_id": "D1_START_CAMPAIGN",
        "authority_scope": "A4_PRODUCTION_TRANSFER_AND_SELECTION",
        "historical_d1_reused": False,
        "predecessor_binding_sha256": predecessor_binding_sha256,
        "goal_revision": goal_revision,
        "recorded_at_utc": _timestamp(recorded_at_utc),
        "selection_accesses": 0,
        "final_accesses": 0,
        "protected_payload_included": False,
    }
    return {**body, "receipt_sha256": canonical_sha256(body)}


def build_a4_admission(
    *,
    attempt_id: str,
    predecessor: Mapping[str, Any],
    d1_receipt: Mapping[str, Any],
    provider_identity: Mapping[str, Any],
    observed_at_utc: datetime,
    now_utc: datetime,
    all_fee_usd_per_hour: Decimal | str | float,
    target_ttl_seconds: int,
    ttl_seconds_remaining: int | None,
    current_campaign_accrued_usd: Decimal | str | float,
    a4_projected_usd: Decimal | str | float,
    a5_reserved_usd: Decimal | str | float,
    campaign_hard_stop_usd: Decimal | str | float = "180",
) -> dict[str, Any]:
    """Create a fresh admission including the A5 reserve required for auto-D2."""

    _attempt(attempt_id)
    checked = validate_a4_predecessor_binding(predecessor)
    d1 = _validate_d1(d1_receipt, attempt_id=attempt_id, binding=checked["binding_sha256"])
    identity = _provider_identity(provider_identity)
    observed, current = _utc(observed_at_utc), _utc(now_utc)
    quote_age = int((current - observed).total_seconds())
    if quote_age < 0 or quote_age > 900:
        raise A4ExecutionError("A4 provider quote is stale")
    if isinstance(target_ttl_seconds, bool) or target_ttl_seconds < 48 * 60 * 60:
        raise A4ExecutionError("A4 target TTL must be at least 48 hours")
    if ttl_seconds_remaining is not None and (
        isinstance(ttl_seconds_remaining, bool) or ttl_seconds_remaining < 24 * 60 * 60
    ):
        raise A4ExecutionError("A4 remaining TTL is below the 24-hour floor")
    rate = _amount(all_fee_usd_per_hour, "all_fee_usd_per_hour")
    accrued = _amount(current_campaign_accrued_usd, "current_campaign_accrued_usd")
    a4 = _amount(a4_projected_usd, "a4_projected_usd")
    a5 = _amount(a5_reserved_usd, "a5_reserved_usd")
    cap = _amount(campaign_hard_stop_usd, "campaign_hard_stop_usd")
    if rate <= 0 or a5 <= 0:
        raise A4ExecutionError("A4 quote and A5 reserve must be positive")
    projection = accrued + a4 + a5
    if projection > cap:
        raise A4ExecutionError("A4 plus required A5 reserve exceeds campaign hard stop")
    provider_body = {
        "schema_version": "myis.armindex-a4-provider-observation.v1",
        "status": "PASS_A4_PROVIDER_IDENTITY",
        "observed_at_utc": _timestamp(observed),
        "provider_identity": identity,
    }
    provider_receipt = {**provider_body, "receipt_sha256": canonical_sha256(provider_body)}
    quote_body = {
        "schema_version": "myis.armindex-a4-all-fee-quote.v1",
        "status": "PASS_A4_FRESH_ALL_FEE_QUOTE",
        "provider_identity_receipt_sha256": provider_receipt["receipt_sha256"],
        "observed_at_utc": _timestamp(observed),
        "quote_age_seconds": quote_age,
        "currency": "USD",
        "all_fee_usd_per_hour": _decimal(rate),
        "target_ttl_seconds": target_ttl_seconds,
        "ttl_seconds_remaining": "unlimited" if ttl_seconds_remaining is None else ttl_seconds_remaining,
    }
    quote_receipt = {**quote_body, "receipt_sha256": canonical_sha256(quote_body)}
    budget_body = {
        "schema_version": "myis.armindex-a4-campaign-budget-admission.v1",
        "status": "PASS_A4_BUDGET_ADMISSION",
        "current_campaign_accrued_usd": _decimal(accrued),
        "a4_projected_usd": _decimal(a4),
        "a5_reserved_usd": _decimal(a5),
        "campaign_projected_usd": _decimal(projection),
        "campaign_hard_stop_usd": _decimal(cap),
        "automatic_a5_continuity_eligible": True,
    }
    budget_receipt = {**budget_body, "receipt_sha256": canonical_sha256(budget_body)}
    body = {
        "schema_version": "myis.armindex-a4-fresh-admission.v1",
        "status": "PASS_A4_FRESH_ADMISSION",
        "attempt_id": attempt_id,
        "predecessor_binding_sha256": checked["binding_sha256"],
        "d1_continuation_receipt_sha256": d1["receipt_sha256"],
        "provider_identity_receipt_sha256": provider_receipt["receipt_sha256"],
        "all_fee_quote_receipt_sha256": quote_receipt["receipt_sha256"],
        "budget_admission_receipt_sha256": budget_receipt["receipt_sha256"],
        "quote_age_seconds": quote_age,
        "selection_accesses": 0,
        "final_accesses": 0,
        "protected_payload_included": False,
    }
    return {
        "provider_identity": provider_receipt,
        "all_fee_quote": quote_receipt,
        "budget_admission": budget_receipt,
        "admission": {**body, "admission_sha256": canonical_sha256(body)},
    }


def build_profile_registry(
    *,
    attempt_id: str,
    predecessor_binding_sha256: str,
    hdev_commitment_sha256: str,
    evaluator_binding_sha256: str,
    runtime_binding_sha256: str,
    license_binding_sha256: str,
    profiles: Sequence[Mapping[str, Any]],
    research_reference: Mapping[str, Any],
) -> dict[str, Any]:
    """Freeze exactly three commercial profiles plus one research-only reference."""

    _attempt(attempt_id)
    for name, value in (
        ("predecessor_binding_sha256", predecessor_binding_sha256),
        ("hdev_commitment_sha256", hdev_commitment_sha256),
        ("evaluator_binding_sha256", evaluator_binding_sha256),
        ("runtime_binding_sha256", runtime_binding_sha256),
        ("license_binding_sha256", license_binding_sha256),
    ):
        _hash(value, name)
    checked = [_profile(row) for row in profiles]
    if len(checked) != len(PROFILES) or {item["profile_id"] for item in checked} != set(PROFILES):
        raise A4ExecutionError("A4 requires FAST, BALANCED, and DEEP exactly once")
    reference = _research_reference(research_reference)
    body = {
        "schema_version": "myis.armindex-a4-profile-registry.v1",
        "status": "FROZEN_A4_PROFILE_REGISTRY",
        "attempt_id": attempt_id,
        "predecessor_binding_sha256": predecessor_binding_sha256,
        "hdev_commitment_sha256": hdev_commitment_sha256,
        "expected_hdev_query_count": 100,
        "evaluator_binding_sha256": evaluator_binding_sha256,
        "runtime_binding_sha256": runtime_binding_sha256,
        "license_binding_sha256": license_binding_sha256,
        "profiles": sorted(checked, key=lambda item: item["profile_id"]),
        "research_reference": reference,
        "selection_accesses": 0,
        "final_accesses": 0,
        "protected_payload_included": False,
    }
    return {**body, "registry_sha256": canonical_sha256(body)}


def freeze_selection_registry(
    candidates: Sequence[Mapping[str, Any]], *, profile_registry_sha256: str
) -> dict[str, Any]:
    """Freeze the at-most-four preregistered Selection roles before exposure."""

    _hash(profile_registry_sha256, "profile_registry_sha256")
    if len(candidates) > len(FINALIST_ROLES):
        raise A4ExecutionError("Selection registry exceeds four finalists")
    rows = []
    used_systems: set[str] = set()
    used_roles: set[str] = set()
    for raw in candidates:
        item = _copy_safe(raw, role="Selection finalist")
        required = {"role", "system_sha256", "license_scope", "source_receipt_sha256"}
        if set(item) != required or item["role"] not in FINALIST_ROLES:
            raise A4ExecutionError("Selection finalist role is invalid")
        if item["role"] in used_roles:
            raise A4ExecutionError("Selection finalist role is duplicated")
        _hash(item["system_sha256"], "Selection system")
        _hash(item["source_receipt_sha256"], "Selection source receipt")
        if item["license_scope"] not in {"research_only", "commercial_capable"}:
            raise A4ExecutionError("Selection finalist license scope is invalid")
        if item["system_sha256"] in used_systems:
            continue
        used_roles.add(item["role"])
        used_systems.add(item["system_sha256"])
        rows.append(item)
    body = {
        "schema_version": "myis.armindex-a4-selection-registry.v1",
        "status": "FROZEN_BEFORE_SELECTION",
        "profile_registry_sha256": profile_registry_sha256,
        "finalists": sorted(rows, key=lambda item: FINALIST_ROLES.index(item["role"])),
        "selection_accesses": 0,
        "final_accesses": 0,
        "protected_payload_included": False,
    }
    return {**body, "registry_sha256": canonical_sha256(body)}


def build_conditional_d2_receipt(
    *,
    a4_result_audit_sha256: str,
    a4_safe_return_sha256: str,
    a5_bundle_sha256: str,
    final_registry_sha256: str,
    final_split_commitment_sha256: str,
    clean_git_commit: str,
    clean_git_tree: str,
    selection_accesses: int,
    final_accesses: int,
    a5_provenance_audit_sha256: str,
    automatic_pass: Mapping[str, bool],
) -> dict[str, Any]:
    """Emit D2 only after A4 predicates and A5 provenance have passed.

    The provenance receipt is aggregate-safe and hash-bound. Requiring it at
    this constructor boundary prevents structural A5 validation from being
    mistaken for launch-ready Final provenance.
    """

    for field, value in (
        ("a4_result_audit_sha256", a4_result_audit_sha256),
        ("a4_safe_return_sha256", a4_safe_return_sha256),
        ("a5_bundle_sha256", a5_bundle_sha256),
        ("final_registry_sha256", final_registry_sha256),
        ("final_split_commitment_sha256", final_split_commitment_sha256),
        ("a5_provenance_audit_sha256", a5_provenance_audit_sha256),
    ):
        _hash(value, field)
    if not re.fullmatch(r"[a-f0-9]{40}", clean_git_commit) or not re.fullmatch(r"[a-f0-9]{40}", clean_git_tree):
        raise A4ExecutionError("D2 requires clean Git commit and tree identities")
    required = {
        "all_a4_coverage",
        "selection_count_valid",
        "legal_isolation",
        "safe_return",
        "independent_audit",
        "a5_bundle_clean_pushed",
        "finalist_frozen",
        "protected_boundary",
        "a5_budget_reserve",
        "a5_provenance_pass",
    }
    if set(automatic_pass) != required or any(value is not True for value in automatic_pass.values()):
        raise A4ExecutionError("A4 automatic PASS predicates are incomplete")
    if selection_accesses not in (0, 1) or final_accesses != 0:
        raise A4ExecutionError("conditional D2 access counters are invalid")
    body = {
        "schema_version": "myis.armindex-a4-conditional-d2-receipt.v1",
        "status": "PASS_CONDITIONAL_D2_OPEN_FINAL",
        "owner_decision_id": "D2_OPEN_FINAL",
        "owner_conditional_approval": True,
        "a4_result_audit_sha256": a4_result_audit_sha256,
        "a4_safe_return_sha256": a4_safe_return_sha256,
        "a5_bundle_sha256": a5_bundle_sha256,
        "a5_provenance_audit_sha256": a5_provenance_audit_sha256,
        "final_registry_sha256": final_registry_sha256,
        "final_split_commitment_sha256": final_split_commitment_sha256,
        "clean_git_commit": clean_git_commit,
        "clean_git_tree": clean_git_tree,
        "selection_accesses": selection_accesses,
        "final_accesses": 0,
        "protected_payload_included": False,
    }
    return {**body, "receipt_sha256": canonical_sha256(body)}


def _profile(value: Mapping[str, Any]) -> dict[str, Any]:
    item = _copy_safe(value, role="A4 profile")
    required = {"profile_id", "system_sha256", "arm_ids", "mode", "candidate_depth", "commercial_only"}
    if set(item) != required or item["profile_id"] not in PROFILES:
        raise A4ExecutionError("A4 profile schema is invalid")
    _hash(item["system_sha256"], "profile system")
    arms = item["arm_ids"]
    if not isinstance(arms, list) or not arms or len(arms) != len(set(arms)) or any(arm not in COMMERCIAL_ARMS for arm in arms):
        raise A4ExecutionError("commercial profile has invalid arms")
    if item["commercial_only"] is not True or item["mode"] not in {"synchronous", "asynchronous"}:
        raise A4ExecutionError("commercial profile mode is invalid")
    if not isinstance(item["candidate_depth"], int) or isinstance(item["candidate_depth"], bool) or not 100 <= item["candidate_depth"] <= 2000:
        raise A4ExecutionError("commercial profile candidate depth is invalid")
    if item["profile_id"] == "FAST" and (item["mode"] != "synchronous" or "ARM-01" not in arms or len(arms) > 2):
        raise A4ExecutionError("FAST must use BM25 plus at most one dense arm")
    if item["profile_id"] == "BALANCED" and item["mode"] != "synchronous":
        raise A4ExecutionError("BALANCED must be synchronous")
    return item


def _research_reference(value: Mapping[str, Any]) -> dict[str, Any]:
    item = _copy_safe(value, role="research reference")
    required = {"system_sha256", "arm_ids", "license_scope", "label"}
    if set(item) != required or item["license_scope"] != "research_only" or item["label"] != "ARM-03_RESEARCH_REFERENCE":
        raise A4ExecutionError("research reference schema is invalid")
    _hash(item["system_sha256"], "research reference system")
    if item["arm_ids"] != ["ARM-03"]:
        raise A4ExecutionError("research reference must be ARM-03 only")
    return item


def _validate_d1(value: Mapping[str, Any], *, attempt_id: str, binding: str) -> dict[str, Any]:
    item = _copy_safe(value, role="D1 continuation")
    if (
        item.get("schema_version") != "myis.armindex-a4-d1-continuation-receipt.v1"
        or item.get("status") != "PASS_A4_D1_CONTINUATION_RECORDED"
        or item.get("attempt_id") != attempt_id
        or item.get("predecessor_binding_sha256") != binding
        or item.get("historical_d1_reused") is not False
        or item.get("selection_accesses") != 0
        or item.get("final_accesses") != 0
        or item.get("protected_payload_included") is not False
    ):
        raise A4ExecutionError("D1 continuation receipt is invalid")
    _self_hash(item, "receipt_sha256", role="D1 continuation")
    return item


def _provider_identity(value: Mapping[str, Any]) -> dict[str, Any]:
    item = _copy_safe(value, role="provider identity")
    required = {"provider", "instance_id", "machine_id", "status", "gpu_count", "gpu_model", "ssh_runtime_sha256"}
    if set(item) != required or item["provider"] != "vast" or item["instance_id"] != 47790578 or item["machine_id"] != 134131 or item["status"] != "running" or item["gpu_count"] != 4 or item["gpu_model"] != "RTX_3090":
        raise A4ExecutionError("provider identity does not match the authorized instance")
    _hash(item["ssh_runtime_sha256"], "ssh_runtime_sha256")
    return item


def _copy_safe(value: Mapping[str, Any], *, role: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise A4ExecutionError(f"{role} must be an object")
    result = deepcopy(dict(value))

    def scan(node: Any) -> None:
        if isinstance(node, Mapping):
            for key, child in node.items():
                lowered = str(key).lower()
                if any(part in lowered for part in _PROTECTED_KEY_PARTS):
                    raise A4ExecutionError(f"{role} contains protected field")
                scan(child)
        elif isinstance(node, list):
            for child in node:
                scan(child)

    scan(result)
    return result


def _self_hash(value: Mapping[str, Any], field: str, *, role: str) -> None:
    _hash(value.get(field), field)
    if value[field] != canonical_sha256({key: item for key, item in value.items() if key != field}):
        raise A4ExecutionError(f"{role} self-hash mismatch")


def _hash(value: Any, field: str) -> None:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise A4ExecutionError(f"{field} must be SHA-256")


def _attempt(value: Any) -> None:
    if not isinstance(value, str) or not _ATTEMPT.fullmatch(value):
        raise A4ExecutionError("A4/A5 attempt ID is invalid")


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise A4ExecutionError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc).replace(microsecond=0)


def _timestamp(value: datetime) -> str:
    return _utc(value).isoformat().replace("+00:00", "Z")


def _amount(value: Decimal | str | float, field: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise A4ExecutionError(f"{field} is invalid") from error
    if not parsed.is_finite() or parsed < 0:
        raise A4ExecutionError(f"{field} is invalid")
    return parsed


def _decimal(value: Decimal) -> str:
    return format(value.normalize(), "f")


__all__ = [
    "A4ExecutionError",
    "COMMERCIAL_ARMS",
    "FINALIST_ROLES",
    "PRIMARY_ARMS",
    "PROFILES",
    "build_a4_admission",
    "build_conditional_d2_receipt",
    "build_d1_continuation_receipt",
    "build_profile_registry",
    "freeze_selection_registry",
    "validate_a4_predecessor_binding",
]
