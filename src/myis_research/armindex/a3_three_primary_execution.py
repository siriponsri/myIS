"""Post-admission, aggregate-safe runtime contracts for three-primary A3."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from itertools import product
import re
from typing import Any

from ..kernel.canonical import canonical_sha256
from ..protection import assert_aggregate_only
from .a3_three_primary_preparation import (
    validate_three_primary_authority,
    validate_three_primary_budget_extension,
    validate_three_primary_manifest,
)
from .harnessopt import HarnessOptError, validate_harness_batch


PRIMARY_ARMS = ("ARM-03", "ARM-04", "ARM-05")
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_ADMISSION_KEYS = {
    "schema_version",
    "status",
    "budget_extension_sha256",
    "authority_sha256",
    "manifest_sha256",
    "a2_closeout_receipt_sha256",
    "provider_identity_sha256",
    "all_fee_quote_sha256",
    "campaign_budget_amendment_receipt_sha256",
    "quote_age_seconds",
    "target_ttl_seconds",
    "a3_projected_total_usd",
    "campaign_projected_total_usd",
    "admission_sha256",
}
_WINNER_KEYS = {"winner_program_sha256", "winner_selection_receipt_sha256"}
_PACKAGE_BINDING_KEYS = {
    "corpus_sha256",
    "query_bundle_sha256",
    "split_commitment_sha256",
    "evaluator_sha256",
    "qrels_commitment_sha256",
    "membership_commitment_sha256",
    "runtime_lock_sha256",
    "data_handoff_sha256",
}
_FIXED_UNION_KEYS = {
    "schema_version",
    "status",
    "frozen_runtime_bindings_sha256",
    "evaluation_depth_by_arm",
    "control_ids",
    "commercial_only_fixed_union_arm_ids",
    "aggregate_only",
    "fixed_union_sha256",
}


class A3ThreePrimaryExecutionError(ValueError):
    """Raised when A3 runtime inputs are unsafe or insufficient for execution."""


def validate_three_primary_admission(
    value: Mapping[str, Any],
    *,
    budget: Mapping[str, Any],
    authority: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate fresh aggregate-safe admission evidence without contacting a provider."""

    admission = _aggregate_copy(value, role="A3 admission")
    if set(admission) != _ADMISSION_KEYS:
        raise A3ThreePrimaryExecutionError("A3 admission fields are incomplete")
    if admission["schema_version"] != "myis.armindex-a3-three-primary-admission.v1":
        raise A3ThreePrimaryExecutionError("A3 admission schema is invalid")
    if admission["status"] != "PASS_A3_FRESH_ADMISSION":
        raise A3ThreePrimaryExecutionError("A3 execution requires a passing fresh admission")
    expected_hashes = {
        "budget_extension_sha256": budget["budget_extension_sha256"],
        "authority_sha256": authority["authority_sha256"],
        "manifest_sha256": manifest["manifest_sha256"],
        "a2_closeout_receipt_sha256": authority["a2_predecessor_bindings"][
            "a2_closeout_receipt_sha256"
        ],
    }
    for field, expected in expected_hashes.items():
        if admission[field] != expected:
            raise A3ThreePrimaryExecutionError(f"A3 admission {field} does not bind frozen evidence")
    for field in (
        "provider_identity_sha256",
        "all_fee_quote_sha256",
        "campaign_budget_amendment_receipt_sha256",
    ):
        _require_sha256(admission[field], field)
    quote_age = admission["quote_age_seconds"]
    ttl = admission["target_ttl_seconds"]
    if isinstance(quote_age, bool) or not isinstance(quote_age, int) or not 0 <= quote_age <= 900:
        raise A3ThreePrimaryExecutionError("A3 admission quote age must be at most 900 seconds")
    if isinstance(ttl, bool) or not isinstance(ttl, int) or ttl < 48 * 60 * 60:
        raise A3ThreePrimaryExecutionError("A3 admission must preserve the 48-hour target TTL")
    _require_ceiling(admission["a3_projected_total_usd"], ceiling=Decimal("35"), field="A3")
    _require_ceiling(admission["campaign_projected_total_usd"], ceiling=Decimal("180"), field="campaign")
    _self_hash(admission, "admission_sha256", role="A3 admission")
    return admission


def build_three_primary_runtime_bindings(
    budget: Mapping[str, Any],
    authority: Mapping[str, Any],
    manifest: Mapping[str, Any],
    admission: Mapping[str, Any],
    winner_bindings: Mapping[str, Mapping[str, Any]],
    target_adapter_sha256s: Mapping[str, str],
    package_bindings: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Bind admissible winners and adapter identities using hashes only."""

    checked_budget = validate_three_primary_budget_extension(budget)
    checked_authority = validate_three_primary_authority(authority)
    checked_manifest = validate_three_primary_manifest(manifest, authority=checked_authority)
    checked_admission = validate_three_primary_admission(
        admission,
        budget=checked_budget,
        authority=checked_authority,
        manifest=checked_manifest,
    )
    winners = _validate_winner_bindings(winner_bindings, authority=checked_authority)
    adapters = _validate_hash_mapping(target_adapter_sha256s, role="target adapter")
    body = {
        "schema_version": "myis.armindex-a3-three-primary-runtime-bindings.v1",
        "primary_arm_scope": list(PRIMARY_ARMS),
        "budget_extension_sha256": checked_budget["budget_extension_sha256"],
        "authority_sha256": checked_authority["authority_sha256"],
        "manifest_sha256": checked_manifest["manifest_sha256"],
        "admission_sha256": checked_admission["admission_sha256"],
        "winner_bindings": winners,
        "target_adapter_sha256s": adapters,
    }
    if package_bindings is not None:
        body["package_bindings"] = _validate_package_bindings(package_bindings)
    return {**body, "runtime_bindings_sha256": canonical_sha256(body)}


def validate_fixed_union_contract(
    value: Mapping[str, Any], *, runtime_bindings_sha256: str
) -> dict[str, Any]:
    """Require preregistered equal-depth controls before adaptive work."""

    fixed_union = _aggregate_copy(value, role="fixed union contract")
    if set(fixed_union) != _FIXED_UNION_KEYS:
        raise A3ThreePrimaryExecutionError("fixed union contract fields are incomplete")
    if (
        fixed_union["schema_version"] != "myis.armindex-a3-three-primary-fixed-union.v1"
        or fixed_union["status"] != "frozen_before_evaluation"
        or fixed_union["frozen_runtime_bindings_sha256"] != runtime_bindings_sha256
        or fixed_union["aggregate_only"] is not True
    ):
        raise A3ThreePrimaryExecutionError("fixed union contract is not bound and frozen")
    depths = fixed_union["evaluation_depth_by_arm"]
    if not isinstance(depths, Mapping) or set(depths) != set(PRIMARY_ARMS):
        raise A3ThreePrimaryExecutionError("fixed union must set one evaluation depth per primary arm")
    if any(isinstance(depth, bool) or not isinstance(depth, int) or depth <= 0 for depth in depths.values()):
        raise A3ThreePrimaryExecutionError("fixed union evaluation depths are invalid")
    if len(set(depths.values())) != 1:
        raise A3ThreePrimaryExecutionError("fixed union requires equal depth across primary arms")
    if fixed_union["control_ids"] != [
        "best_single",
        "all_primary_rrf60",
        "top_two_rrf60",
        "top_three_rrf60",
        "commercial_only_fixed_union",
    ]:
        raise A3ThreePrimaryExecutionError("fixed union controls drifted from the preregistration")
    if fixed_union["commercial_only_fixed_union_arm_ids"] != ["ARM-04", "ARM-05"]:
        raise A3ThreePrimaryExecutionError("commercial-only union must remain ARM-04 plus ARM-05")
    _self_hash(fixed_union, "fixed_union_sha256", role="fixed union contract")
    return fixed_union


def build_three_primary_execution_contract(
    runtime_bindings: Mapping[str, Any],
    fixed_union: Mapping[str, Any],
    harness_batches: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build a no-I/O post-admission execution plan for a 3x3 A3 workload.

    This function only returns immutable execution intent. A remote runner must
    consume this contract separately and produce aggregate-safe receipts.
    """

    bindings = _validate_runtime_bindings(runtime_bindings)
    binding_hash = bindings["runtime_bindings_sha256"]
    union = validate_fixed_union_contract(fixed_union, runtime_bindings_sha256=binding_hash)
    batches = _validate_harness_batches(harness_batches, runtime_bindings_sha256=binding_hash)
    matrix = [
        {
            "source_arm_id": source,
            "target_arm_id": target,
            "post_admission_action": (
                "reuse_self_winner" if source == target else "validate_cross_arm_transfer"
            ),
            "winner_program_sha256": bindings["winner_bindings"][source]["winner_program_sha256"],
            "target_adapter_sha256": bindings["target_adapter_sha256s"][target],
            "result_scope": "aggregate_only",
        }
        for source, target in product(PRIMARY_ARMS, repeat=2)
    ]
    body = {
        "schema_version": "myis.armindex-a3-three-primary-execution-contract.v1",
        "status": "READY_FOR_POST_ADMISSION_EXECUTION",
        "runtime_bindings_sha256": binding_hash,
        "transfer_matrix": matrix,
        "fixed_union_sha256": union["fixed_union_sha256"],
        "harness_batch_sha256s": [batch["batch_sha256"] for batch in batches],
        "execution_order": ["transfer_matrix", "fixed_union_controls", "complete_harnessopt_batches"],
        "selection_permitted": False,
        "final_permitted": False,
        "provider_contact_performed": False,
        "remote_execution_performed": False,
    }
    return {**body, "execution_contract_sha256": canonical_sha256(body)}


def _validate_runtime_bindings(value: Mapping[str, Any]) -> dict[str, Any]:
    bindings = _aggregate_copy(value, role="runtime bindings")
    required = {
        "schema_version",
        "primary_arm_scope",
        "budget_extension_sha256",
        "authority_sha256",
        "manifest_sha256",
        "admission_sha256",
        "winner_bindings",
        "target_adapter_sha256s",
        "runtime_bindings_sha256",
    }
    extended_required = required | {"package_bindings"}
    if (
        set(bindings) not in (required, extended_required)
        or bindings.get("schema_version")
        != "myis.armindex-a3-three-primary-runtime-bindings.v1"
    ):
        raise A3ThreePrimaryExecutionError("runtime bindings fields are incomplete")
    if bindings["primary_arm_scope"] != list(PRIMARY_ARMS):
        raise A3ThreePrimaryExecutionError("runtime bindings changed the primary-arm scope")
    for field in ("budget_extension_sha256", "authority_sha256", "manifest_sha256", "admission_sha256"):
        _require_sha256(bindings[field], field)
    _validate_hash_mapping(bindings["target_adapter_sha256s"], role="target adapter")
    if "package_bindings" in bindings:
        _validate_package_bindings(bindings["package_bindings"])
    _validate_winner_shapes(bindings["winner_bindings"])
    _self_hash(bindings, "runtime_bindings_sha256", role="runtime bindings")
    return bindings


def _validate_package_bindings(value: Mapping[str, Any]) -> dict[str, str]:
    bindings = _aggregate_copy(value, role="A3 package bindings")
    if set(bindings) != _PACKAGE_BINDING_KEYS:
        raise A3ThreePrimaryExecutionError("A3 package bindings fields are incomplete")
    result = {str(key): str(item) for key, item in bindings.items()}
    for field, digest in result.items():
        _require_sha256(digest, f"package binding {field}")
    return result


def _validate_winner_bindings(
    value: Mapping[str, Mapping[str, Any]], *, authority: Mapping[str, Any]
) -> dict[str, dict[str, Any]]:
    winners = _aggregate_copy(value, role="winner bindings")
    _validate_winner_shapes(winners)
    expected_receipts = authority["a2_predecessor_bindings"]["primary_winner_receipt_sha256s"]
    for arm_id in PRIMARY_ARMS:
        if winners[arm_id]["winner_selection_receipt_sha256"] != expected_receipts[arm_id]:
            raise A3ThreePrimaryExecutionError("winner receipt does not match the amended A2 authority")
    return winners


def _validate_winner_shapes(value: Any) -> None:
    if not isinstance(value, Mapping) or set(value) != set(PRIMARY_ARMS):
        raise A3ThreePrimaryExecutionError("winner bindings must cover exactly the three primary arms")
    for arm_id in PRIMARY_ARMS:
        winner = value[arm_id]
        if not isinstance(winner, Mapping) or set(winner) != _WINNER_KEYS:
            raise A3ThreePrimaryExecutionError("winner binding fields are incomplete")
        for field in _WINNER_KEYS:
            _require_sha256(winner[field], f"{arm_id}.{field}")


def _validate_harness_batches(
    values: Sequence[Mapping[str, Any]], *, runtime_bindings_sha256: str
) -> list[dict[str, Any]]:
    if not 1 <= len(values) <= 3:
        raise A3ThreePrimaryExecutionError(
            "A3 Extended requires one to three complete HarnessOpt batches"
        )
    validated: list[dict[str, Any]] = []
    for expected_iteration, value in enumerate(values, start=1):
        try:
            batch = validate_harness_batch(value)
        except HarnessOptError as error:
            raise A3ThreePrimaryExecutionError(str(error)) from error
        if batch["iteration"] != expected_iteration:
            raise A3ThreePrimaryExecutionError("HarnessOpt batches must be contiguous from iteration one")
        if batch["frozen_bindings_sha256"] != runtime_bindings_sha256:
            raise A3ThreePrimaryExecutionError("HarnessOpt batch changed the runtime bindings")
        for candidate in batch["candidates"]:
            arms = candidate["configuration"]["arm_ids"]
            if not set(arms) <= set(PRIMARY_ARMS):
                raise A3ThreePrimaryExecutionError("HarnessOpt cannot reintroduce diagnostic arms")
        validated.append(batch)
    return validated


def _validate_hash_mapping(value: Any, *, role: str) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != set(PRIMARY_ARMS):
        raise A3ThreePrimaryExecutionError(f"{role} hashes must cover exactly the three primary arms")
    result = {str(key): str(item) for key, item in value.items()}
    for arm_id, digest in result.items():
        _require_sha256(digest, f"{role} {arm_id}")
    return result


def _aggregate_copy(value: Mapping[str, Any], *, role: str) -> dict[str, Any]:
    result = deepcopy(dict(value))
    try:
        assert_aggregate_only(result)
    except ValueError as error:
        raise A3ThreePrimaryExecutionError(f"{role}: {error}") from error
    return result


def _require_sha256(value: Any, field: str) -> None:
    if not _SHA256.fullmatch(str(value)):
        raise A3ThreePrimaryExecutionError(f"{field} must be a SHA-256 digest")


def _require_ceiling(value: Any, *, ceiling: Decimal, field: str) -> None:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise A3ThreePrimaryExecutionError(f"{field} projected total is invalid") from error
    if not amount.is_finite() or amount < 0 or amount > ceiling:
        raise A3ThreePrimaryExecutionError(f"{field} projected total exceeds its hard stop")


def _self_hash(value: Mapping[str, Any], field: str, *, role: str) -> None:
    _require_sha256(value.get(field), field)
    unsigned = {key: item for key, item in value.items() if key != field}
    if value[field] != canonical_sha256(unsigned):
        raise A3ThreePrimaryExecutionError(f"{role} self-hash does not bind its contents")


__all__ = [
    "A3ThreePrimaryExecutionError",
    "PRIMARY_ARMS",
    "build_three_primary_execution_contract",
    "build_three_primary_runtime_bindings",
    "validate_fixed_union_contract",
    "validate_three_primary_admission",
]
