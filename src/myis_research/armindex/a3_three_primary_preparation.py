"""Fail-closed local preparation checks for the amended three-primary A3 workload."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from itertools import product
import re
from typing import Any

from ..kernel.canonical import canonical_sha256
from ..protection import assert_aggregate_only
from .harnessopt import HARNESS_BATCH_ROLES


_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_PRIMARY_ARMS = ("ARM-03", "ARM-04", "ARM-05")
_DIAGNOSTIC_ARMS = ("ARM-01", "ARM-02")
_FROZEN_A2_BINDINGS = {
    "manifest_sha256": "f6276e3a15e760187152270418e00ce4cae4d8efe45b13edb02c4742e3b3049e",
    "freeze_receipt_sha256": "ea93db368c3e740f7914e07e2bdfc15052991f6f05976f6924acdce717392e10",
    "lock_sha256": "c01f683b909e6f4c6310c01855b3f79319a183b7950f91338d43baa8a2d57952",
}
_A2_PREDECESSOR = {
    "a2_closeout_receipt_sha256": "e4bc663d7ee09282c334f25945ede247a50b81742a690c214e0f2aa9ffb81d1d",
    "a2_result_integrity_audit_sha256": "7d31b80d4dab6897f3110ee629ddf8f9d12fd5f0522b0d8ccd175ba892986642",
    "a2_amendment_sha256": "4c48d6f30713ea391148694cab6e0fe15b5bd2f99866bb8778ace558272c0168",
    "primary_winner_receipt_sha256s": {
        "ARM-03": "02d1fe5c9c4be99bdf236b67bcea86a37ddd3ceb2212c4599f01f8ea3c3fb7e9",
        "ARM-04": "8e38ffd6aa8e1f052d653b9034d8b74493d149072b9a7ab0233cc26ba4bc95c5",
        "ARM-05": "27cb9a81ca3dada1a904d6cdac97b214df99e6ca104f62040e2e83cc3e342997",
    },
    "diagnostic_no_winner_receipt_sha256s": {
        "ARM-01": "afdb576eb25c8f74aa898c49cc4f8fc75b7152679300d4c4189f397c8017f258",
        "ARM-02": "3d05dcd3fabad9000a9391184a8e0dd0c294578a775bf61bd0b13315c4dbe2bb",
    },
    "safe_return_receipt_sha256": "659982aea768c6d4c057a75c6a50b04026d7c48875d604e06b1563a1b2b09484",
    "workers_reaped": True,
}
_BUDGET_KEYS = {
    "schema_version", "extension_id", "status", "owner_authorization", "a2_closeout_bindings",
    "a3_workload", "hard_stops", "activation_requirements", "pre_admission_safety",
    "budget_extension_sha256",
}
_AUTHORITY_KEYS = {
    "schema_version", "authority_id", "authority_state", "purpose", "a2_predecessor_bindings",
    "frozen_a2_bindings", "budget_extension_uri", "primary_arm_scope",
    "diagnostic_reporting_boundary", "post_closeout_execution_boundary",
    "pre_admission_forbidden_actions", "execution_permitted", "authority_sha256",
}
_MANIFEST_KEYS = {
    "schema_version", "bundle_id", "authority_id", "authority_state", "authority_sha256",
    "budget_extension_uri", "arms", "transfer_matrix", "complementarity_controls",
    "harnessopt_plan", "pending_runtime_inputs", "safety", "manifest_sha256",
}


class A3ThreePrimaryPreparationError(ValueError):
    """The three-primary A3 package cannot safely progress to admission."""


def _self_hash(value: Mapping[str, Any], field: str, *, role: str) -> None:
    supplied = value.get(field)
    if not _SHA256.fullmatch(str(supplied)):
        raise A3ThreePrimaryPreparationError(f"{role} self-hash is invalid")
    if supplied != canonical_sha256({key: item for key, item in value.items() if key != field}):
        raise A3ThreePrimaryPreparationError(f"{role} self-hash does not bind its contents")


def validate_three_primary_budget_extension(value: Mapping[str, Any]) -> dict[str, Any]:
    budget = deepcopy(dict(value))
    if set(budget) != _BUDGET_KEYS:
        raise A3ThreePrimaryPreparationError("three-primary budget fields are incomplete")
    if (
        budget["schema_version"] != "myis.armindex-a3-three-primary-budget-extension.v1"
        or budget["extension_id"] != "armindex-a3-three-primary-budget-extension-v1"
        or budget["status"] != "PENDING_FRESH_A3_ADMISSION"
    ):
        raise A3ThreePrimaryPreparationError("three-primary budget identity is invalid")
    if budget["owner_authorization"] != {
        "source_amendment_sha256": "4c48d6f30713ea391148694cab6e0fe15b5bd2f99866bb8778ace558272c0168",
        "a3_whole_workload_hard_stop_usd": 35,
        "campaign_hard_stop_usd": 180,
    }:
        raise A3ThreePrimaryPreparationError("three-primary budget Owner authority drift")
    bindings = budget["a2_closeout_bindings"]
    if (
        not isinstance(bindings, Mapping)
        or bindings.get("a2_closeout_receipt_sha256") != "e4bc663d7ee09282c334f25945ede247a50b81742a690c214e0f2aa9ffb81d1d"
        or bindings.get("a2_result_integrity_audit_sha256") != "7d31b80d4dab6897f3110ee629ddf8f9d12fd5f0522b0d8ccd175ba892986642"
        or bindings.get("a2_whole_workload_total_usd") != "54.52666666666665948"
        or bindings.get("a2_forward_hard_stop_usd") != "60"
        or bindings.get("safe_return_receipt_sha256") != "659982aea768c6d4c057a75c6a50b04026d7c48875d604e06b1563a1b2b09484"
        or bindings.get("workers_reaped") is not True
    ):
        raise A3ThreePrimaryPreparationError("A2 closeout binding drift")
    if budget["a3_workload"] != {
        "whole_workload_admission_required": True,
        "partial_arm_admission_allowed": False,
        "fresh_all_fee_quote_required": True,
        "fresh_provider_identity_required": True,
        "quote_max_age_seconds": 900,
        "target_ttl_hours": 48,
        "same_instance_reuse_allowed_only_after_a2_closeout": True,
        "additional_instance_creation_allowed": False,
        "planned_cross_arm_evaluation_cells_maximum": 6,
        "planned_harnessopt_batches_maximum": 3,
        "harnessopt_candidates_per_batch": 4,
    }:
        raise A3ThreePrimaryPreparationError("three-primary workload budget is invalid")
    if budget["hard_stops"] != {
        "a3_forward_usd": 35,
        "campaign_usd": 180,
        "a2_must_close_at_or_below_usd": 60,
        "remaining_campaign_after_a1_a2_a3_usd": "79.31170133333334052",
    }:
        raise A3ThreePrimaryPreparationError("three-primary hard-stop values are invalid")
    required = {
        "PASS_A2_EXECUTION_CLOSEOUT_V2", "PASS_A2_RESULT_INTEGRITY_V2", "A2_SAFE_RETURN_AND_WORKER_REAP",
        "three_primary_winner_receipts_bound", "two_diagnostic_no_winner_receipts_bound",
        "fresh_A3_all_fee_quote_at_or_below_hard_stop", "fresh_A3_provider_identity",
        "post_A2_campaign_budget_amendment_receipt", "three_primary_A3_bundle_validation_pass",
    }
    if not isinstance(budget["activation_requirements"], list) or set(budget["activation_requirements"]) != required:
        raise A3ThreePrimaryPreparationError("three-primary budget activation requirements are incomplete")
    if budget["pre_admission_safety"] != {
        "launch_allowed": False, "provider_contact_allowed": False, "remote_execution_allowed": False,
        "spend_allowed": False, "selection_allowed": False, "final_allowed": False,
    }:
        raise A3ThreePrimaryPreparationError("three-primary budget opens a forbidden action")
    _self_hash(budget, "budget_extension_sha256", role="three-primary budget")
    return budget


def validate_three_primary_authority(value: Mapping[str, Any]) -> dict[str, Any]:
    authority = deepcopy(dict(value))
    try:
        assert_aggregate_only(authority)
    except ValueError as error:
        raise A3ThreePrimaryPreparationError(str(error)) from error
    if set(authority) != _AUTHORITY_KEYS:
        raise A3ThreePrimaryPreparationError("three-primary authority fields are incomplete")
    if (
        authority["schema_version"] != "myis.armindex-a3-three-primary-preparation-authority.v1"
        or authority["authority_id"] != "A3_THREE_PRIMARY_TRANSFER_HARNESSOPT_POST_A2"
        or authority["authority_state"] != "PENDING_FRESH_A3_ADMISSION"
        or authority["execution_permitted"] is not False
        or authority["frozen_a2_bindings"] != _FROZEN_A2_BINDINGS
        or authority["budget_extension_uri"] != "control/budgets/armindex-budget-extension-a3-three-primary.v1.json"
        or authority["primary_arm_scope"] != list(_PRIMARY_ARMS)
    ):
        raise A3ThreePrimaryPreparationError("three-primary authority is invalid or not fail-closed")
    predecessor = authority["a2_predecessor_bindings"]
    if not isinstance(predecessor, Mapping) or predecessor != _A2_PREDECESSOR:
        raise A3ThreePrimaryPreparationError("three-primary predecessor winner bindings are incomplete")
    if authority["diagnostic_reporting_boundary"] != {
        "excluded_arm_ids": ["ARM-01", "ARM-02"],
        "a3_optimization_input": False,
        "permitted_use": "bounded_A2_negative_diagnostic_reporting_only",
    }:
        raise A3ThreePrimaryPreparationError("diagnostic arms are not excluded from A3 optimization")
    required_forbidden = {
        "candidate_mutation", "retrieval", "transfer_evaluation", "complementarity_evaluation",
        "harnessopt_evaluation", "provider_contact", "remote_execution", "spend", "selection", "final",
    }
    if not isinstance(authority["pre_admission_forbidden_actions"], list) or set(authority["pre_admission_forbidden_actions"]) != required_forbidden:
        raise A3ThreePrimaryPreparationError("three-primary forbidden-action boundary is incomplete")
    _self_hash(authority, "authority_sha256", role="three-primary authority")
    return authority


def validate_three_primary_manifest(value: Mapping[str, Any], *, authority: Mapping[str, Any]) -> dict[str, Any]:
    manifest = deepcopy(dict(value))
    try:
        assert_aggregate_only(manifest)
    except ValueError as error:
        raise A3ThreePrimaryPreparationError(str(error)) from error
    if set(manifest) != _MANIFEST_KEYS:
        raise A3ThreePrimaryPreparationError("three-primary manifest fields are incomplete")
    if (
        manifest["schema_version"] != "myis.armindex-a3-three-primary-preparation-manifest.v1"
        or manifest["bundle_id"] != "A3_THREE_PRIMARY_TRANSFER_HARNESSOPT_PENDING"
        or manifest["authority_id"] != authority["authority_id"]
        or manifest["authority_state"] != authority["authority_state"]
        or manifest["authority_sha256"] != authority["authority_sha256"]
        or manifest["budget_extension_uri"] != authority["budget_extension_uri"]
    ):
        raise A3ThreePrimaryPreparationError("three-primary manifest identity is invalid")
    arms = manifest["arms"]
    if not isinstance(arms, list) or [item.get("arm_id") for item in arms] != list(_PRIMARY_ARMS) or any(item.get("winner_program_sha256") is not None or item.get("winner_selection_receipt_sha256") is not None for item in arms):
        raise A3ThreePrimaryPreparationError("three-primary manifest arms are incomplete or materialized early")
    expected_pairs = set(product(_PRIMARY_ARMS, repeat=2))
    rows = manifest["transfer_matrix"]
    if not isinstance(rows, list) or len(rows) != len(expected_pairs):
        raise A3ThreePrimaryPreparationError("three-primary transfer matrix must contain nine cells")
    pairs: set[tuple[str, str]] = set()
    for row in rows:
        pair = (row.get("source_arm_id"), row.get("target_arm_id"))
        expected_action = "reuse_self_winner" if pair[0] == pair[1] else "validate_cross_arm_transfer"
        if pair not in expected_pairs or pair in pairs or row.get("post_closeout_action") != expected_action or row.get("transfer_classification") is not None or row.get("result_receipt_sha256") is not None:
            raise A3ThreePrimaryPreparationError("three-primary transfer matrix contains invalid or materialized cells")
        pairs.add(pair)
    expected_controls = {
        "same_depth_required": True,
        "control_ids": ["best_single", "all_primary_rrf60", "top_two_rrf60", "top_three_rrf60", "commercial_only_fixed_union"],
        "commercial_only_fixed_union_arm_ids": ["ARM-04", "ARM-05"],
        "aggregate_outputs": ["union_recall", "best_arm_recall", "unique_relevant_pairs", "overlap", "oracle_recall", "incremental_cost", "incremental_latency"],
    }
    if manifest["complementarity_controls"] != expected_controls:
        raise A3ThreePrimaryPreparationError("three-primary complementarity controls are invalid")
    if manifest["harnessopt_plan"] != {
        "maximum_batches": 3,
        "candidates_per_batch": 4,
        "roles": list(HARNESS_BATCH_ROLES),
        "adaptive_scope": "Train-250 only",
        "hdev100_role": "non_adaptive_diagnostic_only",
    }:
        raise A3ThreePrimaryPreparationError("three-primary HarnessOpt plan is invalid")
    if manifest["pending_runtime_inputs"] != [
        "a2_execution_closeout_receipt_v2", "a2_result_integrity_audit_v2",
        "three_primary_winner_selection_receipts", "two_diagnostic_no_winner_tie_records",
        "a1_incumbent_aggregate_receipt", "safe_return_and_workers_reaped",
        "fresh_a3_provider_admission", "post_a2_campaign_budget_amendment_receipt",
    ]:
        raise A3ThreePrimaryPreparationError("three-primary runtime inputs are incomplete")
    if manifest["safety"] != {
        "measured_execution_started": False, "protected_data_accessed": False,
        "provider_contacted": False, "remote_execution_started": False, "spend_permitted": False,
        "candidate_mutation_permitted": False, "selection_permitted": False, "final_permitted": False,
    }:
        raise A3ThreePrimaryPreparationError("three-primary manifest opens a forbidden action")
    _self_hash(manifest, "manifest_sha256", role="three-primary manifest")
    return manifest


def build_three_primary_pending_preflight(
    budget: Mapping[str, Any], authority: Mapping[str, Any], manifest: Mapping[str, Any]
) -> dict[str, Any]:
    checked_budget = validate_three_primary_budget_extension(budget)
    checked_authority = validate_three_primary_authority(authority)
    checked_manifest = validate_three_primary_manifest(manifest, authority=checked_authority)
    body = {
        "schema_version": "myis.armindex-a3-three-primary-pending-preflight.v1",
        "status": "PENDING_FRESH_A3_ADMISSION",
        "launch_permitted": False,
        "budget_extension_sha256": checked_budget["budget_extension_sha256"],
        "authority_sha256": checked_authority["authority_sha256"],
        "manifest_sha256": checked_manifest["manifest_sha256"],
        "primary_arm_count": 3,
        "diagnostic_arm_count": 2,
        "transfer_matrix_cell_count": 9,
        "planned_cross_arm_evaluation_count": 6,
        "maximum_harnessopt_batches": 3,
        "maximum_harnessopt_candidates": 12,
        "protected_payload_included": False,
        "provider_contacted": False,
        "remote_execution_started": False,
        "spend_permitted": False,
    }
    return {**body, "preflight_sha256": canonical_sha256(body)}


__all__ = [
    "A3ThreePrimaryPreparationError",
    "build_three_primary_pending_preflight",
    "validate_three_primary_authority",
    "validate_three_primary_budget_extension",
    "validate_three_primary_manifest",
]
