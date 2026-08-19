"""Fail-closed preparation for post-confirmatory A6 materialization."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from ..kernel.canonical import canonical_sha256
from ..protection import assert_aggregate_only


class A6MaterializationError(ValueError):
    """Raised when an A6 preparation artifact crosses its frozen boundary."""


_REQUIRED_METRICS = (
    "source_document_count",
    "family_count",
    "chunk_count",
    "representation_count",
    "coverage_rate",
    "throughput_documents_per_second",
    "latency_p50_ms",
    "latency_p95_ms",
    "latency_p99_ms",
    "ram_bytes_peak",
    "vram_bytes_peak",
    "index_size_bytes",
    "cost_usd",
    "checkpoint_recovery_count",
    "determinism_sha256",
    "failure_taxonomy",
)


def build_pending_a6_materialization_template(
    a6_contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the local-only A6 template before A5 determines its target."""

    contract = _validate_a6_contract(a6_contract)
    body = {
        "schema_version": "myis.armindex-a6-pending-a5-closeout.v1",
        "status": "PENDING_A5_CLOSEOUT",
        "execution_permitted": False,
        "a6_contract_sha256": contract["contract_sha256"],
        "authorized_instance_id": contract["provider_admission"]["authorized_instance_id"],
        "fresh_a6_attempt_required": True,
        "reuse_a4_a5_workers_caches_pids_or_partials_forbidden": True,
        "selection_accesses": 0,
        "final_accesses": 0,
        "a5_frozen_winner_configuration": None,
        "full_corpus_source_sha256": None,
        "owner_store_root": None,
        "required_aggregate_metrics": list(_REQUIRED_METRICS),
        "safe_return_allowlist": list(contract["safe_return"]["git_and_projection_allowlist"]),
        "protected_payload_included": False,
        "claim_boundary": contract["claim_boundary"],
    }
    return {**body, "template_sha256": canonical_sha256(body)}


def validate_pending_a6_materialization_template(
    value: Mapping[str, Any],
    a6_contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Fail closed unless the template stays pre-A5 and aggregate-only."""

    contract = _validate_a6_contract(a6_contract)
    if not isinstance(value, Mapping):
        raise A6MaterializationError("A6 pending template must be an object")
    item = deepcopy(dict(value))
    expected_fields = {
        "schema_version", "status", "execution_permitted", "a6_contract_sha256",
        "authorized_instance_id", "fresh_a6_attempt_required",
        "reuse_a4_a5_workers_caches_pids_or_partials_forbidden",
        "selection_accesses", "final_accesses", "a5_frozen_winner_configuration",
        "full_corpus_source_sha256", "owner_store_root", "required_aggregate_metrics",
        "safe_return_allowlist", "protected_payload_included", "claim_boundary",
        "template_sha256",
    }
    if set(item) != expected_fields:
        raise A6MaterializationError("A6 pending template fields are invalid")
    if item["schema_version"] != "myis.armindex-a6-pending-a5-closeout.v1" or item["status"] != "PENDING_A5_CLOSEOUT":
        raise A6MaterializationError("A6 pending template status is invalid")
    if item["execution_permitted"] is not False or item["selection_accesses"] != 0 or item["final_accesses"] != 0:
        raise A6MaterializationError("A6 pending template opens a protected operation")
    if item["a6_contract_sha256"] != contract["contract_sha256"]:
        raise A6MaterializationError("A6 pending template contract hash drifted")
    if item["authorized_instance_id"] != contract["provider_admission"]["authorized_instance_id"]:
        raise A6MaterializationError("A6 pending template instance is not authorized")
    if item["fresh_a6_attempt_required"] is not True or item["reuse_a4_a5_workers_caches_pids_or_partials_forbidden"] is not True:
        raise A6MaterializationError("A6 pending template permits stale runtime reuse")
    if any(item[field] is not None for field in ("a5_frozen_winner_configuration", "full_corpus_source_sha256", "owner_store_root")):
        raise A6MaterializationError("A6 pending template contains pre-A5 materialization input")
    if item["required_aggregate_metrics"] != list(_REQUIRED_METRICS):
        raise A6MaterializationError("A6 pending template metric contract drifted")
    if item["safe_return_allowlist"] != contract["safe_return"]["git_and_projection_allowlist"]:
        raise A6MaterializationError("A6 pending template export allowlist drifted")
    if item["protected_payload_included"] is not False or item["claim_boundary"] != contract["claim_boundary"]:
        raise A6MaterializationError("A6 pending template crossed claim or protected boundary")
    try:
        assert_aggregate_only(item)
    except ValueError as error:
        raise A6MaterializationError("A6 pending template contains protected payload") from error
    _sha256(item.get("template_sha256"), "template_sha256")
    body = {key: value for key, value in item.items() if key != "template_sha256"}
    if item["template_sha256"] != canonical_sha256(body):
        raise A6MaterializationError("A6 pending template self-hash mismatch")
    return item


def _validate_a6_contract(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise A6MaterializationError("A6 execution contract must be an object")
    contract = deepcopy(dict(value))
    if contract.get("schema_version") != "myis.armindex-a6-full-dapfam-execution-contract.v1":
        raise A6MaterializationError("A6 execution contract schema is invalid")
    _sha256(contract.get("contract_sha256"), "contract_sha256")
    body = {key: item for key, item in contract.items() if key != "contract_sha256"}
    if contract["contract_sha256"] != canonical_sha256(body):
        raise A6MaterializationError("A6 execution contract self-hash mismatch")
    if contract.get("status") != "blocked_until_valid_a5_closeout" or contract.get("launch_allowed") is not False:
        raise A6MaterializationError("A6 execution contract does not remain pre-A5 blocked")
    provider = contract.get("provider_admission")
    if not isinstance(provider, Mapping) or provider.get("authorized_instance_id") != 47790578:
        raise A6MaterializationError("A6 execution contract has no approved same-instance policy")
    if provider.get("same_instance_reuse_permitted_only_after_a5_closeout") is not True or provider.get("fresh_a6_attempt_root_required") is not True or provider.get("reuse_a4_a5_workers_caches_pids_or_partials_forbidden") is not True:
        raise A6MaterializationError("A6 execution contract permits unsafe runtime reuse")
    if tuple(contract.get("required_aggregate_metrics", ())) != _REQUIRED_METRICS:
        raise A6MaterializationError("A6 execution contract metric set drifted")
    safe_return = contract.get("safe_return")
    if not isinstance(safe_return, Mapping) or not isinstance(safe_return.get("git_and_projection_allowlist"), list):
        raise A6MaterializationError("A6 execution contract safe-return policy is invalid")
    return contract


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise A6MaterializationError(f"{field} must be SHA-256")
    return value


__all__ = [
    "A6MaterializationError",
    "build_pending_a6_materialization_template",
    "validate_pending_a6_materialization_template",
]
