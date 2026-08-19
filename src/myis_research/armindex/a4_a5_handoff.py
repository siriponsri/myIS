"""Pointer-only A5 handoff construction after A4 Selection."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import re
from typing import Any

from ..kernel.canonical import canonical_sha256
from ..protection import assert_aggregate_only

_HASH = re.compile(r"^[a-f0-9]{64}$")


class A4A5HandoffError(ValueError):
    """Raised when a protected or incomplete A5 pointer bundle is requested."""


def build_pending_a5_handoff_template(
    *,
    expected_final_query_count: int = 872,
) -> dict[str, Any]:
    """Build a local-only A5 preparation template before A4 Selection.

    This artifact deliberately contains no A4 receipt, finalist, Final pointer,
    or budget admission. It is a fail-closed interface template, not an A5
    authorization or measured bundle.
    """

    if expected_final_query_count != 872:
        raise A4A5HandoffError("A5 final query count is frozen at 872")
    body = {
        "schema_version": "myis.armindex-a5-pending-a4-selection.v1",
        "status": "PENDING_A4_SELECTION",
        "execution_permitted": False,
        "selection_accesses": 0,
        "final_accesses": 0,
        "expected_final_query_count": expected_final_query_count,
        "final_registry": [],
        "final_input_pointer": None,
        "protected_payload_included": False,
        "claim_boundary": "No A4 Selection, D2, Final access, or A5 result exists.",
    }
    return {**body, "template_sha256": canonical_sha256(body)}


def validate_pending_a5_handoff_template(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the pre-Selection template without opening any protected path."""

    if not isinstance(value, Mapping):
        raise A4A5HandoffError("A5 pending template must be an object")
    item = deepcopy(dict(value))
    expected = {
        "schema_version", "status", "execution_permitted", "selection_accesses",
        "final_accesses", "expected_final_query_count", "final_registry",
        "final_input_pointer", "protected_payload_included", "claim_boundary",
        "template_sha256",
    }
    if set(item) != expected:
        raise A4A5HandoffError("A5 pending template fields are invalid")
    if item["schema_version"] != "myis.armindex-a5-pending-a4-selection.v1" or item["status"] != "PENDING_A4_SELECTION":
        raise A4A5HandoffError("A5 pending template status is invalid")
    if item["execution_permitted"] is not False or item["selection_accesses"] != 0 or item["final_accesses"] != 0:
        raise A4A5HandoffError("A5 pending template opens a gated operation")
    if item["expected_final_query_count"] != 872 or item["final_registry"] or item["final_input_pointer"] is not None:
        raise A4A5HandoffError("A5 pending template contains provisional Final state")
    if item["protected_payload_included"] is not False:
        raise A4A5HandoffError("A5 pending template crossed protected boundary")
    try:
        assert_aggregate_only(item)
    except ValueError as error:
        raise A4A5HandoffError("A5 pending template contains protected payload") from error
    _hash(item.get("template_sha256"), "template_sha256")
    if item["template_sha256"] != canonical_sha256({key: value for key, value in item.items() if key != "template_sha256"}):
        raise A4A5HandoffError("A5 pending template self-hash mismatch")
    return item


def build_a5_pointer_bundle(
    *,
    attempt_id: str,
    a4_coverage_sha256: str,
    selection_receipt_sha256: str,
    result_audit_sha256: str,
    safe_return_sha256: str,
    final_split_commitment_sha256: str,
    final_input_pointer: str,
    evaluator_handoff_sha256: str,
    a5_reserved_usd: str | float,
    finalists: Sequence[Mapping[str, Any]],
    statistical_plan: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a complete provenance manifest with an opaque Final pointer."""

    if not isinstance(attempt_id, str) or not attempt_id.startswith("a4-goal001-"):
        raise A4A5HandoffError("A4 attempt identity is invalid")
    for field, value in (("a4_coverage_sha256", a4_coverage_sha256), ("selection_receipt_sha256", selection_receipt_sha256), ("result_audit_sha256", result_audit_sha256), ("safe_return_sha256", safe_return_sha256), ("final_split_commitment_sha256", final_split_commitment_sha256), ("evaluator_handoff_sha256", evaluator_handoff_sha256)):
        _hash(value, field)
    _opaque_pointer(final_input_pointer)
    _positive_decimal(a5_reserved_usd, "a5_reserved_usd")
    rows = [_finalist(row) for row in finalists]
    if len(rows) != 2 or {row["role"] for row in rows} != {"static_common_baseline", "research_champion"}:
        raise A4A5HandoffError("A5 Final registry must contain exactly comparator and research champion")
    if len({row["system_sha256"] for row in rows}) != 2:
        raise A4A5HandoffError("A5 Final registry systems must be distinct")
    plan = deepcopy(dict(statistical_plan or {
        "paired_deltas": "aggregate_only",
        "paired_bootstrap_resamples": 10_000,
        "confidence_level": 0.95,
        "rank_biserial_effect": "aggregate_only",
        "win_tie_loss": {"wins": 0, "ties": 0, "losses": 0},
        "correction_rule": "holm_bonferroni_preregistered_family",
    }))
    _validate_statistical_plan(plan)
    try:
        assert_aggregate_only(plan)
    except ValueError as error:
        raise A4A5HandoffError("A5 statistical plan contains protected payload") from error
    body = {
        "schema_version": "myis.armindex-a4-a5-pointer-bundle.v1",
        "status": "PASS_A4_A5_POINTER_ONLY_BUNDLE",
        "attempt_id": attempt_id,
        "a4_coverage_sha256": a4_coverage_sha256,
        "selection_receipt_sha256": selection_receipt_sha256,
        "result_audit_sha256": result_audit_sha256,
        "safe_return_sha256": safe_return_sha256,
        "final_split_commitment_sha256": final_split_commitment_sha256,
        "final_input_pointer": final_input_pointer,
        "evaluator_handoff_sha256": evaluator_handoff_sha256,
        "a5_reserved_usd": str(a5_reserved_usd),
        "final_registry": sorted(rows, key=lambda row: row["role"]),
        "statistical_plan": plan,
        "claim_boundary": "No A5 Final result exists before valid D2 and measured closeout.",
        "protected_payload_included": False,
    }
    return {**body, "bundle_sha256": canonical_sha256(body)}


def validate_a5_pointer_bundle(value: Mapping[str, Any]) -> dict[str, Any]:
    """Fail closed on bundle drift, protected fields, or an expanded registry."""

    if not isinstance(value, Mapping):
        raise A4A5HandoffError("A5 bundle must be an object")
    item = deepcopy(dict(value))
    expected = {
        "schema_version", "status", "attempt_id", "a4_coverage_sha256",
        "selection_receipt_sha256", "result_audit_sha256", "safe_return_sha256",
        "final_split_commitment_sha256", "final_input_pointer",
        "evaluator_handoff_sha256", "a5_reserved_usd", "final_registry",
        "statistical_plan", "claim_boundary", "protected_payload_included",
        "bundle_sha256",
    }
    if set(item) != expected:
        raise A4A5HandoffError("A5 bundle fields are incomplete or unexpected")
    try:
        assert_aggregate_only(item)
    except ValueError as error:
        raise A4A5HandoffError("A5 bundle contains protected payload") from error
    if item.get("schema_version") != "myis.armindex-a4-a5-pointer-bundle.v1" or item.get("status") != "PASS_A4_A5_POINTER_ONLY_BUNDLE":
        raise A4A5HandoffError("A5 bundle schema is invalid")
    _hash(item.get("bundle_sha256"), "bundle_sha256")
    if item["bundle_sha256"] != canonical_sha256({key: value for key, value in item.items() if key != "bundle_sha256"}):
        raise A4A5HandoffError("A5 bundle self-hash mismatch")
    if item.get("protected_payload_included") is not False:
        raise A4A5HandoffError("A5 bundle crossed protected boundary")
    if not isinstance(item.get("attempt_id"), str) or not item["attempt_id"].startswith("a4-goal001-"):
        raise A4A5HandoffError("A4 attempt identity is invalid")
    for field in ("a4_coverage_sha256", "selection_receipt_sha256", "result_audit_sha256", "safe_return_sha256", "final_split_commitment_sha256", "evaluator_handoff_sha256"):
        _hash(item.get(field), field)
    _opaque_pointer(item.get("final_input_pointer"))
    _positive_decimal(item.get("a5_reserved_usd"), "a5_reserved_usd")
    _validate_statistical_plan(item.get("statistical_plan"))
    rows = item.get("final_registry")
    if not isinstance(rows, list) or len(rows) != 2 or {row.get("role") for row in rows} != {"static_common_baseline", "research_champion"}:
        raise A4A5HandoffError("A5 Final registry is not exactly two systems")
    for row in rows:
        _finalist(row)
    if len({row["system_sha256"] for row in rows}) != 2:
        raise A4A5HandoffError("A5 Final registry systems must be distinct")
    return item


def _finalist(value: Mapping[str, Any]) -> dict[str, Any]:
    item = deepcopy(dict(value))
    if set(item) != {"role", "system_sha256", "program_sha256", "license_scope"}:
        raise A4A5HandoffError("A5 finalist fields are invalid")
    if item["role"] not in {"static_common_baseline", "research_champion"}:
        raise A4A5HandoffError("A5 finalist role is invalid")
    _hash(item["system_sha256"], "system_sha256")
    _hash(item["program_sha256"], "program_sha256")
    if item["license_scope"] not in {"commercial_capable", "research_only"}:
        raise A4A5HandoffError("A5 finalist license scope is invalid")
    expected_scope = {
        "static_common_baseline": "commercial_capable",
        "research_champion": "research_only",
    }[item["role"]]
    if item["license_scope"] != expected_scope:
        raise A4A5HandoffError("A5 finalist license scope does not match role")
    return item


def _opaque_pointer(value: Any) -> str:
    if not isinstance(value, str) or not value or "://" in value or "\\" in value or value.startswith("/"):
        raise A4A5HandoffError("A5 final input must be an opaque relative pointer")
    if any(part in {"", ".", ".."} for part in value.split("/")):
        raise A4A5HandoffError("A5 final input pointer contains traversal")
    return value


def _positive_decimal(value: Any, field: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise A4A5HandoffError(f"{field} must be a positive decimal") from None
    if not parsed.is_finite() or parsed <= 0:
        raise A4A5HandoffError(f"{field} must be a positive decimal")
    return parsed


def _validate_statistical_plan(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise A4A5HandoffError("A5 statistical plan is invalid")
    required = {
        "paired_deltas", "paired_bootstrap_resamples", "confidence_level",
        "rank_biserial_effect", "win_tie_loss", "correction_rule",
    }
    if not required.issubset(value):
        raise A4A5HandoffError("A5 statistical plan is incomplete")
    if value["paired_bootstrap_resamples"] != 10_000 or value["confidence_level"] != 0.95:
        raise A4A5HandoffError("A5 statistical plan is not preregistered")
    if not isinstance(value["correction_rule"], str) or not value["correction_rule"]:
        raise A4A5HandoffError("A5 correction rule is invalid")
    counts = value["win_tie_loss"]
    if not isinstance(counts, Mapping) or any(not isinstance(counts.get(key), int) or counts[key] < 0 for key in ("wins", "ties", "losses")):
        raise A4A5HandoffError("A5 win/tie/loss summary is invalid")


def _hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise A4A5HandoffError(f"{field} must be SHA-256")
    return value


__all__ = [
    "A4A5HandoffError",
    "build_a5_pointer_bundle",
    "build_pending_a5_handoff_template",
    "validate_a5_pointer_bundle",
    "validate_pending_a5_handoff_template",
]
