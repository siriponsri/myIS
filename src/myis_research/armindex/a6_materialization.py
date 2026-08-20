"""Fail-closed preparation for post-confirmatory A6 materialization."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import re
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
_A6_ATTEMPT = re.compile(r"^a6-goal001-[0-9]{8}T[0-9]{6}Z(?:-[a-z0-9]+)?$")


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


def validate_a5_frozen_winner_binding(
    value: Mapping[str, Any],
    a6_contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the single hash-closed winner that A6 is allowed to consume."""

    contract = _validate_a6_contract(a6_contract)
    if not isinstance(value, Mapping):
        raise A6MaterializationError("A5 winner binding must be an object")
    item = deepcopy(dict(value))
    required_receipts = tuple(contract["predecessor_binding"]["required_receipts"])
    expected = {
        "schema_version", "status", "a5_terminal_state", "winner_count", "winner",
        *required_receipts, "selection_accesses", "final_accesses",
        "protected_payload_included", "claim_boundary", "binding_sha256",
    }
    if set(item) != expected:
        raise A6MaterializationError("A5 winner binding fields are incomplete or unexpected")
    if item["schema_version"] != "myis.armindex-a6-a5-winner-binding.v1" or item["status"] != "PASS_A5_FROZEN_WINNER_BOUND":
        raise A6MaterializationError("A5 winner binding status is invalid")
    if item["a5_terminal_state"] != "PASS_A5_FINAL_CONFIRMATION" or item["winner_count"] != 1:
        raise A6MaterializationError("A6 requires exactly one PASS_A5 frozen winner")
    winner_fields = set(contract["frozen_input_contract"]["must_match_a5"])
    winner = item["winner"]
    if not isinstance(winner, Mapping) or set(winner) != winner_fields:
        raise A6MaterializationError("A5 winner configuration does not match the A6 frozen input contract")
    for field in winner_fields:
        _sha256(winner[field], f"winner.{field}")
    for field in required_receipts:
        _sha256(item[field], field)
    if item["a5_frozen_winner_configuration_sha256"] != canonical_sha256(winner):
        raise A6MaterializationError("A5 frozen winner configuration hash drifted")
    if item["selection_accesses"] not in (0, 1) or item["final_accesses"] != 1:
        raise A6MaterializationError("A5 winner binding counters are invalid")
    if item["protected_payload_included"] is not False or item["claim_boundary"] != contract["claim_boundary"]:
        raise A6MaterializationError("A5 winner binding crossed the A6 claim boundary")
    try:
        assert_aggregate_only(item)
    except ValueError as error:
        raise A6MaterializationError("A5 winner binding contains protected payload") from error
    _sha256(item["binding_sha256"], "binding_sha256")
    if item["binding_sha256"] != canonical_sha256({key: value for key, value in item.items() if key != "binding_sha256"}):
        raise A6MaterializationError("A5 winner binding self-hash mismatch")
    return item


def validate_a6_attempt_admission(
    value: Mapping[str, Any],
    a6_contract: Mapping[str, Any],
    winner_binding: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate a fresh A6 admission without permitting stale runtime reuse."""

    contract = _validate_a6_contract(a6_contract)
    winner = validate_a5_frozen_winner_binding(winner_binding, contract)
    if not isinstance(value, Mapping):
        raise A6MaterializationError("A6 attempt admission must be an object")
    item = deepcopy(dict(value))
    expected = {
        "schema_version", "status", "execution_permitted", "launch_allowed",
        "a6_contract_sha256", "a5_winner_binding_sha256", "attempt_id",
        "attempt_root_pointer", "authorized_instance_id", "provider_identity_sha256",
        "fresh_quote_sha256", "budget_admission_sha256", "runtime_health_sha256",
        "gpu_health_sha256", "disk_health_sha256", "safe_export_manifest_sha256",
        "fresh_attempt_root_required", "stale_runtime_reuse_forbidden",
        "selection_accesses", "final_accesses", "protected_payload_included",
        "claim_boundary", "admission_sha256",
    }
    if set(item) != expected:
        raise A6MaterializationError("A6 attempt admission fields are incomplete or unexpected")
    if item["schema_version"] != "myis.armindex-a6-attempt-admission.v1" or item["status"] != "PASS_A6_FRESH_ATTEMPT_ADMISSION":
        raise A6MaterializationError("A6 attempt admission status is invalid")
    if item["execution_permitted"] is not True or item["launch_allowed"] is not True:
        raise A6MaterializationError("A6 attempt admission does not authorize the frozen workload")
    if item["a6_contract_sha256"] != contract["contract_sha256"]:
        raise A6MaterializationError("A6 attempt admission contract hash drifted")
    if item["a5_winner_binding_sha256"] != winner["binding_sha256"]:
        raise A6MaterializationError("A6 attempt admission winner binding drifted")
    if not isinstance(item["attempt_id"], str) or not _A6_ATTEMPT.fullmatch(item["attempt_id"]):
        raise A6MaterializationError("A6 attempt identity is invalid")
    _opaque_pointer(item["attempt_root_pointer"])
    if item["authorized_instance_id"] != contract["provider_admission"]["authorized_instance_id"]:
        raise A6MaterializationError("A6 attempt admission instance is not authorized")
    for field in (
        "provider_identity_sha256", "fresh_quote_sha256", "budget_admission_sha256",
        "runtime_health_sha256", "gpu_health_sha256", "disk_health_sha256",
        "safe_export_manifest_sha256",
    ):
        _sha256(item[field], field)
    if item["fresh_attempt_root_required"] is not True or item["stale_runtime_reuse_forbidden"] is not True:
        raise A6MaterializationError("A6 attempt admission permits stale runtime reuse")
    if item["selection_accesses"] not in (0, 1) or item["final_accesses"] != 1:
        raise A6MaterializationError("A6 attempt admission counters are invalid")
    if item["protected_payload_included"] is not False or item["claim_boundary"] != contract["claim_boundary"]:
        raise A6MaterializationError("A6 attempt admission crossed the protected or claim boundary")
    try:
        assert_aggregate_only(item)
    except ValueError as error:
        raise A6MaterializationError("A6 attempt admission contains protected payload") from error
    _sha256(item["admission_sha256"], "admission_sha256")
    if item["admission_sha256"] != canonical_sha256({key: value for key, value in item.items() if key != "admission_sha256"}):
        raise A6MaterializationError("A6 attempt admission self-hash mismatch")
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
    frozen = contract.get("frozen_input_contract")
    if not isinstance(frozen, Mapping) or not isinstance(frozen.get("must_match_a5"), list) or not frozen["must_match_a5"]:
        raise A6MaterializationError("A6 execution contract has no frozen A5 input contract")
    predecessor = contract.get("predecessor_binding")
    if not isinstance(predecessor, Mapping) or not isinstance(predecessor.get("required_receipts"), list) or not predecessor["required_receipts"]:
        raise A6MaterializationError("A6 execution contract has no A5 predecessor receipt contract")
    return contract


def _opaque_pointer(value: Any) -> str:
    if not isinstance(value, str) or not value or "://" in value or "\\" in value or value.startswith("/"):
        raise A6MaterializationError("A6 attempt root must be an opaque relative pointer")
    if any(part in {"", ".", ".."} for part in value.split("/")):
        raise A6MaterializationError("A6 attempt root pointer contains traversal")
    return value


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise A6MaterializationError(f"{field} must be SHA-256")
    return value


__all__ = [
    "A6MaterializationError",
    "build_pending_a6_materialization_template",
    "validate_a5_frozen_winner_binding",
    "validate_a6_attempt_admission",
    "validate_pending_a6_materialization_template",
]
