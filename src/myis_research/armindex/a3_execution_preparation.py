"""Fail-closed local preparation checks for the extended five-arm A3 workload."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from itertools import product
import re
from typing import Any

from ..kernel.canonical import canonical_sha256
from ..protection import assert_aggregate_only
from .a3_train_headroom import ARM_IDS, FROZEN_A2_BINDINGS
from .harnessopt import HARNESS_BATCH_ROLES


_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_BUDGET_KEYS = {
    "schema_version",
    "extension_id",
    "status",
    "owner_authorization",
    "supersedes_after_a2_closeout",
    "a3_workload",
    "hard_stops",
    "activation_requirements",
    "pre_closeout_safety",
    "budget_extension_sha256",
}
_AUTHORITY_KEYS = {
    "schema_version",
    "authority_id",
    "authority_state",
    "purpose",
    "a2_predecessor_requirements",
    "frozen_a2_bindings",
    "budget_extension_uri",
    "five_arm_scope",
    "post_closeout_execution_boundary",
    "pre_closeout_forbidden_actions",
    "execution_permitted",
    "authority_sha256",
}
_MANIFEST_KEYS = {
    "schema_version",
    "bundle_id",
    "authority_id",
    "authority_state",
    "budget_extension_uri",
    "arms",
    "transfer_matrix",
    "complementarity_controls",
    "harnessopt_plan",
    "pending_runtime_inputs",
    "safety",
    "manifest_sha256",
}
_ARM_KEYS = {"arm_id", "winner_program_sha256", "winner_selection_receipt_sha256"}
_TRANSFER_KEYS = {
    "source_arm_id",
    "target_arm_id",
    "post_closeout_action",
    "transfer_classification",
    "result_receipt_sha256",
}


class A3PreparationError(ValueError):
    """Raised when the pending extended A3 bundle is not safe to carry forward."""


def validate_a3_budget_extension(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the Owner-approved A3/campaign extension without opening spend."""

    budget = deepcopy(dict(value))
    if set(budget) != _BUDGET_KEYS:
        raise A3PreparationError("A3 budget extension fields are incomplete")
    if (
        budget["schema_version"] != "myis.armindex-budget-extension.v1"
        or budget["extension_id"] != "armindex-a3-budget-extension-v1"
        or budget["status"] != "PENDING_A2_CLOSEOUT"
    ):
        raise A3PreparationError("A3 budget extension is not pending A2 closeout")
    authorization = budget["owner_authorization"]
    if not isinstance(authorization, Mapping) or authorization != {
        "authorized_at_utc": "2026-08-17T00:00:00Z",
        "authorized_scope": (
            "A3 five-arm transfer, complementarity, and HarnessOpt preparation "
            "and post-A2 execution"
        ),
        "a3_whole_workload_hard_stop_usd": 35,
        "campaign_hard_stop_usd": 180,
    }:
        raise A3PreparationError("A3 budget extension does not preserve Owner authority")
    superseded = budget["supersedes_after_a2_closeout"]
    if not isinstance(superseded, Mapping) or superseded != {
        "campaign_hard_stop_usd": 150,
        "a2_forward_hard_stop_usd": 60,
        "recorded_a1_charge_usd": 11.161632,
    }:
        raise A3PreparationError("A3 budget extension predecessor ceiling is invalid")
    workload = budget["a3_workload"]
    expected_workload = {
        "whole_workload_admission_required": True,
        "partial_arm_admission_allowed": False,
        "fresh_all_fee_quote_required": True,
        "fresh_provider_identity_required": True,
        "quote_max_age_seconds": 900,
        "target_ttl_hours": 48,
        "same_instance_reuse_allowed_only_after_a2_closeout": True,
        "additional_instance_creation_allowed": False,
        "planned_cross_arm_evaluation_cells_maximum": 20,
        "planned_harnessopt_batches_maximum": 3,
        "harnessopt_candidates_per_batch": 4,
    }
    if workload != expected_workload:
        raise A3PreparationError("A3 extended workload budget is invalid")
    hard_stops = budget["hard_stops"]
    if hard_stops != {
        "a3_forward_usd": 35,
        "campaign_usd": 180,
        "a2_must_close_at_or_below_usd": 60,
        "worst_case_remaining_campaign_ceiling_after_a1_a2_a3_usd": 73.838368,
    }:
        raise A3PreparationError("A3 hard-stop values are invalid")
    if not isinstance(budget["activation_requirements"], list) or set(budget["activation_requirements"]) != {
        "PASS_A2_EXECUTION_CLOSEOUT",
        "PASS_A2_RESULT_AUDIT",
        "A2_SAFE_RETURN_AND_WORKER_REAP",
        "fresh_A3_all_fee_quote_at_or_below_hard_stop",
        "fresh_A3_provider_identity",
        "post_A2_campaign_budget_amendment_receipt",
        "five_arm_A3_bundle_validation_pass",
    }:
        raise A3PreparationError("A3 budget activation requirements are incomplete")
    if budget["pre_closeout_safety"] != {
        "launch_allowed": False,
        "provider_contact_allowed": False,
        "remote_execution_allowed": False,
        "spend_allowed": False,
        "selection_allowed": False,
        "final_allowed": False,
    }:
        raise A3PreparationError("A3 budget extension opens a forbidden action")
    _validate_self_hash(budget, "budget_extension_sha256", "A3 budget extension")
    return budget


def validate_a3_preparation_authority(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate that the A3 package cannot execute before A2 result closeout."""

    authority = deepcopy(dict(value))
    try:
        assert_aggregate_only(authority)
    except ValueError as error:
        raise A3PreparationError(str(error)) from error
    if set(authority) != _AUTHORITY_KEYS:
        raise A3PreparationError("A3 preparation authority fields are incomplete")
    if (
        authority["schema_version"] != "myis.armindex-a3-five-arm-preparation-authority.v1"
        or authority["authority_id"] != "A3_FIVE_ARM_TRANSFER_HARNESSOPT_POST_A2"
        or authority["authority_state"] != "PENDING_A2_CLOSEOUT"
        or authority["execution_permitted"] is not False
    ):
        raise A3PreparationError("A3 preparation authority is not fail-closed")
    if authority["frozen_a2_bindings"] != FROZEN_A2_BINDINGS:
        raise A3PreparationError("A3 preparation authority changed frozen A2 bindings")
    if authority["budget_extension_uri"] != "control/budgets/armindex-budget-extension-a3-v1.json":
        raise A3PreparationError("A3 preparation authority budget binding is invalid")
    if authority["five_arm_scope"] != list(ARM_IDS):
        raise A3PreparationError("A3 preparation authority five-arm scope is invalid")
    required_predecessors = {
        "PASS_A2_EXECUTION_CLOSEOUT",
        "PASS_A2_RESULT_AUDIT",
        "five_frozen_winner_selection_receipts",
        "safe_return_validated",
        "workers_reaped",
    }
    if not isinstance(authority["a2_predecessor_requirements"], list) or set(authority["a2_predecessor_requirements"]) != required_predecessors:
        raise A3PreparationError("A3 predecessor requirements are incomplete")
    expected_forbidden = {
        "candidate_mutation",
        "retrieval",
        "transfer_evaluation",
        "complementarity_evaluation",
        "harnessopt_evaluation",
        "provider_contact",
        "remote_execution",
        "spend",
        "selection",
        "final",
    }
    if not isinstance(authority["pre_closeout_forbidden_actions"], list) or set(authority["pre_closeout_forbidden_actions"]) != expected_forbidden:
        raise A3PreparationError("A3 forbidden-action boundary is incomplete")
    _validate_self_hash(authority, "authority_sha256", "A3 preparation authority")
    return authority


def validate_a3_preparation_manifest(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the static five-arm extended A3 work package before A2 closes."""

    manifest = deepcopy(dict(value))
    try:
        assert_aggregate_only(manifest)
    except ValueError as error:
        raise A3PreparationError(str(error)) from error
    if set(manifest) != _MANIFEST_KEYS:
        raise A3PreparationError("A3 preparation manifest fields are incomplete")
    if (
        manifest["schema_version"] != "myis.armindex-a3-five-arm-preparation-manifest.v1"
        or manifest["bundle_id"] != "A3_FIVE_ARM_TRANSFER_HARNESSOPT_PENDING"
        or manifest["authority_id"] != "A3_FIVE_ARM_TRANSFER_HARNESSOPT_POST_A2"
        or manifest["authority_state"] != "PENDING_A2_CLOSEOUT"
        or manifest["budget_extension_uri"] != "control/budgets/armindex-budget-extension-a3-v1.json"
    ):
        raise A3PreparationError("A3 preparation manifest identity is invalid")
    _validate_pending_arms(manifest["arms"])
    _validate_pending_transfer_matrix(manifest["transfer_matrix"])
    expected_controls = {
        "same_depth_required": True,
        "control_ids": [
            "best_single",
            "all_eligible_rrf60",
            "top_two_rrf60",
            "top_three_rrf60",
            "commercial_only_fixed_union",
        ],
        "aggregate_outputs": [
            "union_recall",
            "best_arm_recall",
            "unique_relevant_pairs",
            "overlap",
            "oracle_recall",
            "incremental_cost",
            "incremental_latency",
        ],
    }
    if manifest["complementarity_controls"] != expected_controls:
        raise A3PreparationError("A3 complementarity controls are invalid")
    expected_harness = {
        "maximum_batches": 3,
        "candidates_per_batch": 4,
        "roles": list(HARNESS_BATCH_ROLES),
        "adaptive_scope": "Train-250 only",
        "hdev100_role": "non_adaptive_diagnostic_only",
    }
    if manifest["harnessopt_plan"] != expected_harness:
        raise A3PreparationError("A3 extended HarnessOpt plan is invalid")
    if manifest["pending_runtime_inputs"] != [
        "a2_execution_closeout_receipt",
        "a2_result_integrity_audit_receipt",
        "five_winner_selection_receipts",
        "a1_incumbent_aggregate_receipt",
        "fresh_a3_provider_admission",
        "post_a2_campaign_budget_amendment_receipt",
    ]:
        raise A3PreparationError("A3 preparation runtime inputs are incomplete")
    if manifest["safety"] != {
        "measured_execution_started": False,
        "protected_data_accessed": False,
        "provider_contacted": False,
        "remote_execution_started": False,
        "spend_permitted": False,
        "candidate_mutation_permitted": False,
        "selection_permitted": False,
        "final_permitted": False,
    }:
        raise A3PreparationError("A3 preparation manifest opens a forbidden action")
    _validate_self_hash(manifest, "manifest_sha256", "A3 preparation manifest")
    return manifest


def build_a3_pending_preflight(
    budget: Mapping[str, Any], authority: Mapping[str, Any], manifest: Mapping[str, Any]
) -> dict[str, Any]:
    """Return a self-hashed local-only readiness record, never a launch permit."""

    validated_budget = validate_a3_budget_extension(budget)
    validated_authority = validate_a3_preparation_authority(authority)
    validated_manifest = validate_a3_preparation_manifest(manifest)
    body: dict[str, Any] = {
        "schema_version": "myis.armindex-a3-pending-preflight.v1",
        "status": "PENDING_A2_CLOSEOUT",
        "authority_state": "PENDING_A2_CLOSEOUT",
        "launch_permitted": False,
        "budget_extension_sha256": validated_budget["budget_extension_sha256"],
        "authority_sha256": validated_authority["authority_sha256"],
        "manifest_sha256": validated_manifest["manifest_sha256"],
        "five_arm_count": len(ARM_IDS),
        "transfer_matrix_cell_count": len(validated_manifest["transfer_matrix"]),
        "planned_cross_arm_evaluation_count": 20,
        "maximum_harnessopt_batches": 3,
        "maximum_harnessopt_candidates": 12,
        "protected_payload_included": False,
        "provider_contacted": False,
        "remote_execution_started": False,
        "spend_permitted": False,
    }
    return {**body, "preflight_sha256": canonical_sha256(body)}


def _validate_pending_arms(value: Any) -> None:
    if not isinstance(value, list) or len(value) != len(ARM_IDS):
        raise A3PreparationError("A3 preparation manifest must cover five arms")
    seen: set[str] = set()
    for row in value:
        if not isinstance(row, Mapping) or set(row) != _ARM_KEYS:
            raise A3PreparationError("A3 preparation arm row is invalid")
        arm_id = row["arm_id"]
        if arm_id not in ARM_IDS or arm_id in seen:
            raise A3PreparationError("A3 preparation arm IDs are incomplete")
        if row["winner_program_sha256"] is not None or row["winner_selection_receipt_sha256"] is not None:
            raise A3PreparationError("pending A3 preparation cannot contain A2 winner material")
        seen.add(arm_id)
    if seen != set(ARM_IDS):
        raise A3PreparationError("A3 preparation arm IDs are incomplete")


def _validate_pending_transfer_matrix(value: Any) -> None:
    if not isinstance(value, list) or len(value) != len(ARM_IDS) ** 2:
        raise A3PreparationError("A3 transfer matrix must contain all twenty-five cells")
    expected_pairs = set(product(ARM_IDS, repeat=2))
    seen: set[tuple[str, str]] = set()
    for row in value:
        if not isinstance(row, Mapping) or set(row) != _TRANSFER_KEYS:
            raise A3PreparationError("A3 transfer matrix row is invalid")
        pair = (row["source_arm_id"], row["target_arm_id"])
        if pair not in expected_pairs or pair in seen:
            raise A3PreparationError("A3 transfer matrix pairs are incomplete")
        expected_action = "reuse_self_winner" if pair[0] == pair[1] else "validate_cross_arm_transfer"
        if (
            row["post_closeout_action"] != expected_action
            or row["transfer_classification"] is not None
            or row["result_receipt_sha256"] is not None
        ):
            raise A3PreparationError("pending A3 transfer matrix contains materialized results")
        seen.add(pair)
    if seen != expected_pairs:
        raise A3PreparationError("A3 transfer matrix pairs are incomplete")


def _validate_self_hash(value: Mapping[str, Any], field: str, name: str) -> None:
    supplied = value.get(field)
    if not _SHA256.fullmatch(str(supplied)):
        raise A3PreparationError(f"{name} self-hash is invalid")
    unsigned = {key: item for key, item in value.items() if key != field}
    if supplied != canonical_sha256(unsigned):
        raise A3PreparationError(f"{name} self-hash does not bind its contents")


__all__ = [
    "A3PreparationError",
    "build_a3_pending_preflight",
    "validate_a3_budget_extension",
    "validate_a3_preparation_authority",
    "validate_a3_preparation_manifest",
]
