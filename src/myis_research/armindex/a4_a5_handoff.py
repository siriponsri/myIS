"""Pointer-only A5 handoff construction after A4 Selection."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import re
from typing import Any

from ..kernel.canonical import canonical_sha256
from ..protection import assert_aggregate_only

_HASH = re.compile(r"^[a-f0-9]{64}$")


class A4A5HandoffError(ValueError):
    """Raised when a protected or incomplete A5 pointer bundle is requested."""


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
    if not isinstance(final_input_pointer, str) or not final_input_pointer or "://" in final_input_pointer or "\\" in final_input_pointer or final_input_pointer.startswith("/"):
        raise A4A5HandoffError("A5 final input must be an opaque relative pointer")
    rows = [_finalist(row) for row in finalists]
    if len(rows) != 2 or {row["role"] for row in rows} != {"static_common_baseline", "research_champion"}:
        raise A4A5HandoffError("A5 Final registry must contain exactly comparator and research champion")
    if len({row["system_sha256"] for row in rows}) != 2:
        raise A4A5HandoffError("A5 Final registry systems must be distinct")
    plan = deepcopy(dict(statistical_plan or {"paired_bootstrap_resamples": 10_000, "confidence_level": 0.95, "correction_rule": "holm_bonferroni_preregistered_family"}))
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
    return item


def _hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise A4A5HandoffError(f"{field} must be SHA-256")
    return value


__all__ = ["A4A5HandoffError", "build_a5_pointer_bundle", "validate_a5_pointer_bundle"]
