"""Validate additive V13 hardening for the A1.2 publication-impact contract.

V13 preserves V12 byte-for-byte and freezes the full analysis declaration so a
rehash cannot relax exposure, interaction, complementarity, or safety rules.
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a1_2_publication_impact_v12 import validate as validate_v12

REVISION_ID = "a1.2-publication-impact-preregistration-v13"
CONTRACT_PATH = Path("control/armindex/a1.2/publication-impact-contract.v13.json")
SCHEMA_PATH = Path("schemas/armindex/a1.2-publication-impact-contract.v13.json")
V12_CONTRACT_PATH = Path("control/armindex/a1.2/publication-impact-contract.v12.json")
V12_FILE_SHA256 = "124a48157c9114e61d30d01e0ea9597f4af97b98ace4a51d7f021cd9993d4a59"
V12_SELF_SHA256 = "abfe059cc84f77fc6c76caded95e7ebc43c84e7ec62da5e6d820c6fc19d03897"
U011_PATH = Path("evidence/literature/digests/U011_dapfam_digest.md")
U011_FILE_SHA256 = "103dc96cb7a9c7ddd9e017666cc9252f830a520b174692dea313d3db249cfdf6"
DOCUMENTATION_PATH = Path("docs/research/A1_2_PUBLICATION_IMPACT_PREREGISTRATION_V13.md")
DOCUMENTATION_FILE_SHA256 = "4698e8a4d90dd72904f066cd0073121685edfc842b47d73fbb53155333efb35c"

_SECRET = re.compile(
    r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\bsk-[A-Za-z0-9_-]{12,}|"
    r"\bBearer\s+[A-Za-z0-9._~+/-]{12,})",
    re.IGNORECASE,
)

EXPECTED_STUDY_IDENTITY: dict[str, Any] = {
    "a1_2_study_type": "candidate_exposure_and_representation_screening",
    "evidence_stage": "development_diagnostic_evidence_only",
    "representation_program_effects": "pre_registered_program_by_arm_contrasts",
    "retriever_family_effects": "pre_registered_family_grouped_arm_contrasts",
    "retriever_by_representation_interaction": "pre_registered_cross_arm_transfer_interaction",
    "publication_claim_before_final_allowed": False,
}

EXPECTED_ANALYSIS: dict[str, Any] = {
    "outcomes": {
        "primary": "out_recall_at_100",
        "secondary": ["out_ndcg_at_100", "out_ndcg_at_10"],
        "evaluation_unit": "patent_family",
        "aggregation": "macro_over_eligible_out_queries",
        "cutoff": 100,
        "family_mapping_and_evaluator_bindings_required": True,
        "missing_or_unjudged_policy": "predeclared_owner_local_evaluator_receipt_required",
        "stable_tie_policy_required": True,
    },
    "development_confirmation_boundary": {
        "rep_dev_role": "exploratory_common_screen_and_representation_development",
        "harness_dev_role": "exploratory_transfer_complementarity_and_harness_development",
        "selection_125_role": "one_time_finalist_selection_not_confirmation",
        "final_872_role": "sole_confirmatory_evaluation",
        "finalists_must_freeze_before_final": True,
        "post_selection_or_final_mutation_allowed": False,
    },
    "statistics": {
        "paired_unit": "eligible_out_query",
        "bootstrap_resamples": 10000,
        "bootstrap_seed_source": "frozen_confirmation_analysis_receipt",
        "confidence_interval": "two_sided_95_percent_paired_bootstrap",
        "required_aggregate_outputs": [
            "point_estimate", "paired_delta", "ci_lower", "ci_upper",
            "win_tie_loss", "rank_biserial_effect", "comparison_family_id",
        ],
        "superiority_rule": "paired_bootstrap_95ci_lower_gt_zero",
        "positive_ci_crossing_zero_interpretation": "higher_measured_score_uncertain_superiority",
        "multiple_comparison_rule": "holm_only_for_preregistered_additional_confirmatory_comparisons",
        "unplanned_analysis_label": "exploratory",
    },
    "candidate_selection": {
        "development_decision_ledger_required": True,
        "candidate_universe_and_budget_frozen_before_measurement": True,
        "promotion_rule_must_be_lexicographic_and_replayable": True,
        "max_cell_promotion_allowed": False,
        "arm_or_program_failure_policy_predeclared": True,
        "research_and_commercial_champion_tracks_distinct": True,
    },
    "candidate_exposure": {
        "same_total_candidate_depth_required": True,
        "per_arm_depth_union_dedup_and_fusion_bound": True,
        "pool_hash_required": True,
        "deployed_result": "out_recall_at_100_after_frozen_family_aggregation",
        "oracle_metrics_role": "frozen_pool_diagnostic_not_deployed_result",
        "latency_and_cost_include_all_arms": True,
        "post_hoc_cutoff_or_depth_change_allowed": False,
    },
    "interaction": {
        "matrix": "program_by_arm_within_arm_and_cross_arm_deltas",
        "required_outputs": [
            "within_arm_delta", "transfer_delta", "rank_order",
            "rank_reversal_indicator", "paired_effect_and_ci", "truncation_and_cost_context",
        ],
        "claim_scope": "five_frozen_arms_five_programs_dapfam_and_frozen_budget_only",
        "universal_causal_claim_allowed": False,
    },
    "complementarity": {
        "eligible_out_query_denominator_required": True,
        "unique_relevant_family_query_pair_numerator_required": True,
        "pairwise_relevant_pair_overlap_definition_required": True,
        "equal_depth_union_against_best_single_required": True,
        "incremental_latency_and_cost_required": True,
        "non_best_arm_retention_requires_preregistered_gate": True,
    },
    "operational": {
        "cold_and_warm_protocol_bound": True,
        "repetition_count_order_and_discard_policy_bound": True,
        "hardware_runtime_identity_bound": True,
        "resource_sampling_cadence_bound": True,
        "failure_timeout_and_oom_denominator_bound": True,
        "ranking_replay_is_not_latency_variance_evidence": True,
    },
    "safe_reporting": {
        "protected_analysis_location": "owner_local_only",
        "repository_safe_receipt_contains": [
            "aggregate_estimates", "confidence_intervals", "effect_sizes",
            "comparison_family_metadata", "hashes", "counts", "claim_boundary",
        ],
        "repository_safe_receipt_forbids": [
            "opaque_rankings", "query_identifiers", "family_identifiers",
            "per_query_values", "raw_evaluator_payload",
        ],
        "publication_claim_requires_final_confirmatory_receipt": True,
    },
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _check_self_hash(value: Mapping[str, Any]) -> None:
    expected = canonical_sha256(
        {key: item for key, item in value.items() if key != "contract_sha256"}
    )
    if value.get("contract_sha256") != expected:
        raise ValueError("contract_sha256 mismatch")


def _validate_schema(value: Mapping[str, Any], root: Path) -> None:
    schema = _load(root / SCHEMA_PATH)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda item: list(item.path))
    if errors:
        raise ValueError(f"schema failure at {list(errors[0].path)}: {errors[0].message}")


def _validate_safe(value: Mapping[str, Any]) -> None:
    assert_aggregate_only(value)
    text = json.dumps(value, ensure_ascii=True, sort_keys=True)
    if _SECRET.search(text):
        raise ValueError("secret-like material found in v13 publication contract")
    if re.search(r"(?:[A-Za-z]:\\\\|/Users/|/home/|\\\\\\\\[^\\\\]+\\\\)", text):
        raise ValueError("absolute personal path found in v13 publication contract")


def _validate_bindings(value: Mapping[str, Any], root: Path) -> None:
    validate_v12(root)
    if file_sha256(root / V12_CONTRACT_PATH) != V12_FILE_SHA256:
        raise ValueError("preserved v12 contract file hash mismatch")
    v12 = _load(root / V12_CONTRACT_PATH)
    if v12.get("contract_sha256") != V12_SELF_SHA256:
        raise ValueError("preserved v12 contract self hash mismatch")
    if file_sha256(root / U011_PATH) != U011_FILE_SHA256:
        raise ValueError("preserved U011 digest file hash mismatch")
    if file_sha256(root / DOCUMENTATION_PATH) != DOCUMENTATION_FILE_SHA256:
        raise ValueError("v13 preregistration Markdown file hash mismatch")

    expected_v12 = {
        "uri": V12_CONTRACT_PATH.as_posix(),
        "file_sha256": V12_FILE_SHA256,
        "self_sha256": V12_SELF_SHA256,
        "v12_contract_must_remain_unchanged": True,
    }
    if value["v12_binding"] != expected_v12:
        raise ValueError("v13 v12 binding differs from immutable v12 identity")
    expected_reconciliation = {
        "source": {"uri": U011_PATH.as_posix(), "file_sha256": U011_FILE_SHA256},
        "historical_metric_convention": "dapfam_source_study_ndcg_at_100_primary_recall_at_100_secondary",
        "current_a1_2_metric_convention": "candidate_exposure_out_recall_at_100_primary_ndcg_secondary",
        "scope": "historical_external_study_not_current_armindex_candidate_exposure_claim",
        "resolution": "additive_scope_specific_metric_supersession_without_source_rewrite",
        "historical_file_must_remain_unchanged": True,
    }
    if value["historical_metric_reconciliation"] != expected_reconciliation:
        raise ValueError("historical metric reconciliation is incomplete or altered")
    expected_documentation = {
        "uri": DOCUMENTATION_PATH.as_posix(),
        "file_sha256": DOCUMENTATION_FILE_SHA256,
        "purpose": "human_readable_projection_of_this_contract",
    }
    if value["documentation_binding"] != expected_documentation:
        raise ValueError("v13 preregistration Markdown binding differs from frozen documentation")


def _validate_semantics(value: Mapping[str, Any]) -> None:
    if value["study_identity"] != EXPECTED_STUDY_IDENTITY:
        raise ValueError("A1.2 publication study identity differs from the frozen V13 declaration")
    if value["analysis"] != EXPECTED_ANALYSIS:
        raise ValueError("publication analysis differs from the frozen V13 preregistration")
    if value["authorization"] != {
        "adopted_for_execution": False,
        "launch_allowed": False,
        "measured_retrieval_allowed": False,
        "provider_contact_allowed": False,
        "selection_open": False,
        "final_open": False,
    }:
        raise ValueError("v13 must not change execution authorization")
    if value["counters"] != {
        "measured_runs": 0,
        "selection_accesses": 0,
        "final_accesses": 0,
        "charged_usd": 0,
    }:
        raise ValueError("v13 must retain zero resource and exposure counters")


def validate(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    value = _load(root / CONTRACT_PATH)
    _validate_schema(value, root)
    _check_self_hash(value)
    _validate_safe(value)
    _validate_bindings(value, root)
    _validate_semantics(value)
    return {
        "status": "PASS",
        "revision_id": REVISION_ID,
        "contract_file_sha256": file_sha256(root / CONTRACT_PATH),
        "contract_sha256": value["contract_sha256"],
        "v12_file_sha256": V12_FILE_SHA256,
        "historical_digest_file_sha256": U011_FILE_SHA256,
        "documentation_file_sha256": DOCUMENTATION_FILE_SHA256,
        "primary_outcome": EXPECTED_ANALYSIS["outcomes"]["primary"],
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
        "charged_usd": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-publication-impact-v13")
    parser.add_argument("validate", nargs="?", default="validate", choices=("validate",))
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    args = parser.parse_args()
    print(json.dumps(validate(args.repository_root), ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
