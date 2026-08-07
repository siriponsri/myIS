"""Prepare the additive A1.2 scientific execution/adoption request v11.

This module freezes a request for later Owner review. Materialization is local
and deterministic; it cannot authorize provider contact or measured work.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .scientific_common_programs_v11 import compiler_manifest, program_set_manifest


REVISION_ID = "a1.2-scientific-execution-adoption-request-v11"
BASE_COMMIT = "b6dc377e810f9b9c251e5ed032ddbfb1282614e7"
BASE_TREE = "73e6f527971177d4b6612cae7ab0b942dd0d9b86"
REQUEST_PATH = Path("control/armindex/a1.2/scientific-execution-adoption-request.v11.json")
RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-scientific-execution-adoption-request.receipt.v11.json"
)
REQUEST_SCHEMA_PATH = Path(
    "schemas/armindex/a1.2-scientific-execution-adoption-request.v11.json"
)
RECEIPT_SCHEMA_PATH = Path(
    "schemas/armindex/a1.2-scientific-execution-adoption-request-receipt.v11.json"
)
BUDGET_PATH = Path("control/budgets/a1.2-common-screen-scientific-request-v11.json")
HANDOFF_PATH = Path("control/owner-local/a1.2-evaluator-handoff-request.v11.json")
STOP_PATH = Path("control/armindex/a1.2/stop-conditions.scientific-request.v11.json")
PROVIDER_PATH = Path("control/armindex/a1.2/provider-admission-plan.v11.json")
WORKLOAD_SET_PATH = Path(
    "control/armindex/a1.2/workload-manifest-set.scientific-request.v11.json"
)
TRANSFER_PATH = Path("control/armindex/a1.2/scientific-transfer-contract.v11.json")
PROGRAM_SET_PATH = Path("control/armindex/a1.2/common-program-set.v11.json")
RESULT_CONTRACT_PATH = Path("control/armindex/a1.2/aggregate-result-contract.v11.json")
RESULT_SCHEMA_PATH = Path("schemas/armindex/a1.2-aggregate-result-receipt.v11.json")
SCIENTIFIC_COMPILER_PATH = Path(
    "src/myis_research/armindex/scientific_common_programs_v11.py"
)
JOB_ROOT = Path("control/armindex/a1.2/jobs/scientific-request-v11")
RUNBOOK_PATH = Path("docs/operations/A1_2_SCIENTIFIC_EXECUTION_ADOPTION_REQUEST_V11.md")
LEDGER_PATH = Path(
    "control/armindex/a1.2/scientific-execution-adoption-request-ledger.v11.jsonl"
)

IMAGE_REFERENCE = "pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime"
IMAGE_DIGEST = "sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20"
PROGRAM_IDS = (
    "P00-TAC-DOC",
    "P01-TA-DOC",
    "P02-CLAIM1",
    "P03-PASSAGE",
    "P04-SECTION-MULTIVIEW",
)

LINEAGE = (
    (
        "v1",
        "campaigns/armindex-multiretriever-v2/evidence/a1.2-contract-scaffold.receipt.v1.json",
        "834ed83440b7d2c0809588f661739208ddb62d72d6d4cd582f192bd9f2cbff7d",
        "a0d48f009efa786972739af8861406cfdafcb676b58788486a64fb78dcf45ffa",
        "engineering_scaffold_only",
    ),
    (
        "v2",
        "campaigns/armindex-multiretriever-v2/evidence/a1.2-vast-4x3090-migration.receipt.v2.json",
        "efc6550fc9cb321a3cbaca75c5aea1b95e52d007b59b21f80888ab872e462efb",
        "869b6feac387c069f3f53ec49cc3ebf42159cf750d3e23acb0d57ead622ca600",
        "offline_four_worker_preparation_only",
    ),
    (
        "v3",
        "campaigns/armindex-multiretriever-v2/evidence/a1.2-vast-4x3090-postcommit-migration.receipt.v3.json",
        "f031a08a23d58b96e67461353d83b8f11243a5cf8ab4a2b571b8e1940876a8d0",
        "75379b2f33b85549036135cf6c7cc1b06c479b6fe5a1643c08a88501fefdc8ca",
        "postcommit_validator_correction_only",
    ),
    (
        "v4",
        "control/armindex/a1.2/runtime-minimal-model-policy.v4.json",
        "b8a00083c5776a87e8f6b6b2a9ed45882dbd72282e3df7f968c0729dd04b57bd",
        None,
        "runtime_minimal_executed_bytes_policy_only",
    ),
    (
        "v5",
        "campaigns/armindex-multiretriever-v2/evidence/a1.2-runtime-minimal-direct-base-migration.receipt.v5.json",
        "b8b71e4fab7faa0ace7fdb8857f9ec41bc344781eb416c5d7ceaa947b352859a",
        "5f3a4e19c1cd09fbd235d7e2bdb20259b2f810e8520fa806ae26f90b94ebcef1",
        "direct_base_local_stage_only",
    ),
    (
        "v6",
        "campaigns/armindex-multiretriever-v2/evidence/a1.2-live-preflight-correction.receipt.v6.json",
        "3918f0c6e9699a3c66de3f70d2c1efc1daead8e86f03647f4236ddb37cdab9a9",
        "c31ed46ff25a3d8fbd4768329e5a9ba61e50109011d24e41e6139687da227c5f",
        "live_container_correction_and_preserved_failures",
    ),
    (
        "v7",
        "campaigns/armindex-multiretriever-v2/evidence/a1.2-live-preflight-repair.receipt.v7.json",
        "8790fca3ff8a5d4a0cdfa19d41c0534df00b3ae6d2597455b89b290ba4f39edd",
        "bbfedc2c32b8245350d1566fed2c0b62c559e3bd703fecee8604f6fe6e0e48a4",
        "same_instance_engineering_repair_only",
    ),
    (
        "v8",
        "campaigns/armindex-multiretriever-v2/evidence/a1.2-live-preflight-packaging-repair.receipt.v8.json",
        "aaa15d54d73d78fd6237f71d99f9068579b2bc4451a6af15417024e345e076a6",
        "7cc3adb3f454b9ab7911270cfef9cb17863f39292d644b18396bf285af98b6b5",
        "validation_lineage_packaging_repair_only",
    ),
    (
        "v9-preparation",
        "campaigns/armindex-multiretriever-v2/evidence/a1.2-live-preflight-execution-lifecycle.receipt.v9.json",
        "0435823ca9e0e94695059c5aaba6c1f3406cc2873e6c2041ff132cc8f640fcbf",
        "c4d3d5af35cbb0e79abe42821e30d18b1c9c72e902b9d318b7ac064bb025fd9d",
        "synthetic_execution_lifecycle_preparation_only",
    ),
    (
        "v9-result",
        "campaigns/armindex-multiretriever-v2/evidence/a1.2-live-synthetic-preflight-result.receipt.v9.json",
        "52d1d892c4ce034e3d4b0887a5bddbb362d9747c3b343e766ad2a4302c3f13d6",
        "f8969e55225b4fa567c94079b6bffc834e1951268f626bdad7754104294df510",
        "synthetic_adapter_and_lifecycle_evidence_only",
    ),
    (
        "v10",
        "campaigns/armindex-multiretriever-v2/evidence/a1.2-provider-closeout-result.receipt.v10.json",
        "e3ec242228a9472a838518dca31ce9b5a5505d9d3b8c5ae567fb5815a9583216",
        "22f4e027668ecdd6ba5c9f162eee781269b0868bdec513df3ff0fab79b8507ef",
        "owner_attested_provider_closeout_only",
    ),
)

OPERATIONAL_BINDINGS = (
    (
        "model_lockset",
        "control/armindex/a1.2/model-lockset.v1.json",
        "0e31912ba0e036580fd394db9bab2260c0eaffafef6baea89b2f7567460f5e43",
        "99add84f2da3989f679cce5d0eebdcbb284e1cda2d91d0116a8063bc495aeea7",
        "lockset_sha256",
    ),
    (
        "runtime_lock",
        "control/armindex/a1.2/runtime-lock.direct-base.v5.json",
        "914159988fe902ca138847a1d8db3c9e0ea9c378bf1b39398cc1784f4346742e",
        "a390368be63f3c9f96d1a92a13d2d5874baa04ab8d89e397be111820c36757c7",
        "runtime_lock_sha256",
    ),
    (
        "image_contract",
        "control/armindex/a1.2/image-digest-contract.direct-base.v5.json",
        "5c691dc92f9f41fc02fbe388545fb3da34b08d9fdb1a9893012d11768d72829b",
        "86da09b73168275ec7ab8e5f369a539d14e38315e0e67908ca8213fcf1e69950",
        "image_contract_sha256",
    ),
    (
        "topology_contract",
        "control/armindex/a1.2/topology-contract.direct-base.v5.json",
        "e36f28b6fceea0d1e25518d49b37afc808af76afeba0010767f068b7bb2f684e",
        "e648cd608ae830d81a25457904eaa0d391327411a9f8d1628cd9c91f5c607c40",
        "topology_contract_sha256",
    ),
    (
        "safe_export_allowlist",
        "control/armindex/a1.2/safe-export-allowlist.v6.json",
        "f8bc1e7ef07c6e10716e81df2b373bff4620d968572584266124c9137487f201",
        "827945804364eba34d0c3127510fb099a3b8b6085f9454b1c1394ae35436ec30",
        "allowlist_sha256",
    ),
    (
        "continuation_policy",
        "control/armindex/a1.2/owner-instance-continuation-policy.v1.json",
        "28402c57d22400b343cdc94ef88aa285ce94eedf3cb44680c9679c6be9654acd",
        None,
        None,
    ),
    (
        "dapfam_source_contract",
        "control/assets/dapfam-p1-source.v1.json",
        "f829e1827aff84dfb332742f74c1f717da655a1ef962e1aca0260d8d2a450d6c",
        None,
        None,
    ),
)

MODEL_LOCKS = {
    "ARM-01": (
        "control/armindex/a1.2/model-locks/ARM-01.v1.json",
        "1fcaac97ae2bed15add7aca2f71d3d6eac953406347f12d0fe9348382fdf3292",
    ),
    "ARM-02": (
        "control/armindex/a1.2/model-locks/ARM-02.v1.json",
        "c9b60991149aa94506321b2cd719b49477c1c77ab30b78dd29d9c29faf52c607",
    ),
    "ARM-03": (
        "control/armindex/a1.2/model-locks/ARM-03.v1.json",
        "44ee3ec647938556f35852a279ab6a7c8808f35fb721becdc26e69ff9c16a830",
    ),
    "ARM-04": (
        "control/armindex/a1.2/model-locks/ARM-04.v1.json",
        "3ff3107bc6d866aa778548a208a9a8c1446fc5b373f58bde32be7332777b808f",
    ),
    "ARM-05": (
        "control/armindex/a1.2/model-locks/ARM-05.v1.json",
        "e31d412985289a7a0aafe1529860998bdafe834d6b235fe7cc81e4d1630b782a",
    ),
}

_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_SECRET = re.compile(
    r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\bsk-[A-Za-z0-9_-]{12,}|"
    r"\bBearer\s+[A-Za-z0-9._~+/-]{12,})",
    re.IGNORECASE,
)


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _finalize(body: dict[str, Any], field: str) -> dict[str, Any]:
    return {**body, field: canonical_sha256(body)}


def _check_self_hash(value: Mapping[str, Any], field: str) -> None:
    observed = value.get(field)
    expected = canonical_sha256({key: item for key, item in value.items() if key != field})
    if observed != expected:
        raise ValueError(f"{field} mismatch")


def _lineage_body() -> list[dict[str, Any]]:
    return [
        {
            "revision": revision,
            "uri": uri,
            "file_sha256": digest,
            "embedded_sha256": embedded,
            "claim_boundary": claim_boundary,
        }
        for revision, uri, digest, embedded, claim_boundary in LINEAGE
    ]


def _operational_body() -> list[dict[str, Any]]:
    return [
        {
            "binding_id": binding_id,
            "uri": uri,
            "file_sha256": digest,
            "embedded_sha256": embedded,
        }
        for binding_id, uri, digest, embedded, _ in OPERATIONAL_BINDINGS
    ]


def _budget() -> dict[str, Any]:
    body = {
        "schema_version": "myis.armindex-a1.2-scientific-budget-request.v11",
        "profile_id": "a1.2-common-screen-scientific-request-v11",
        "status": "prepared_not_adopted_live_quote_required",
        "currency": "USD",
        "hard_stops": {
            "common_screen_usd": 18,
            "a1_total_usd": 23,
            "campaign_usd": 100,
        },
        "requested_window": {
            "estimated_instance_hours_min": 2,
            "estimated_instance_hours_max": 4,
            "owner_ttl_hours": 6,
            "maximum_projected_common_screen_charge_usd": 18,
            "maximum_hourly_rate_at_full_ttl_usd": 3.0,
            "whole_workload_admission_required": True,
            "partial_arm_admission_allowed": False,
        },
        "historical_quotes": [
            {
                "hourly_instance_usd": 0.6,
                "source": "owner_planning_rate",
                "admissible_for_fresh_launch": False,
            },
            {
                "hourly_instance_usd": 0.656,
                "source": "destroyed_v9_instance",
                "admissible_for_fresh_launch": False,
            },
        ],
        "admission": {
            "fresh_live_quote_required": True,
            "quote_max_age_seconds": 900,
            "fresh_instance_identity_required": True,
            "authoritative_remaining_budget_required": True,
            "projected_ttl_charge_must_fit_all_hard_stops": True,
            "sanitized_quote_receipt_required_fields": [
                "compute_hourly_rate_usd",
                "billing_granularity_seconds",
                "minimum_billable_seconds",
                "storage_fee_usd",
                "network_fee_usd",
                "platform_or_other_fee_usd",
                "tax_or_surcharge_usd",
                "owner_ttl_hours",
                "worst_case_total_charge_usd",
                "quote_observed_at_utc",
                "quote_receipt_sha256",
            ],
            "worst_case_total_formula": (
                "ceil(ttl_seconds/billing_granularity_seconds)*"
                "billing_granularity_seconds/3600*compute_hourly_rate_usd+"
                "storage_fee_usd+network_fee_usd+platform_or_other_fee_usd+"
                "tax_or_surcharge_usd"
            ),
            "unknown_billable_component_allowed": False,
            "missing_or_stale_quote_status": "BLOCKED_BUDGET",
            "insufficient_remaining_budget_status": "BLOCKED_BUDGET",
            "no_default_inference": True,
        },
        "recovery_budget_policy": {
            "automatic_replacement_instance_allowed": False,
            "batch_size_only_oom_recovery_allowed": True,
            "weight_or_precision_change_allowed": False,
            "new_hypothesis_from_reserve_allowed": False,
        },
        "preparation_counters": {
            "measured_runs": 0,
            "gpu_scientific_runs": 0,
            "charged_usd": 0,
            "paid_api_calls": 0,
        },
        "launch_allowed": False,
        "adopted_for_execution": False,
    }
    return _finalize(body, "budget_profile_sha256")


def _handoff() -> dict[str, Any]:
    body = {
        "schema_version": "myis.armindex-a1.2-protected-evaluator-handoff-request.v11",
        "handoff_id": "a1.2-protected-evaluator-handoff-request-v11",
        "status": "protocol_frozen_owner_local_receipt_pending",
        "source_contract": {
            "uri": "control/assets/dapfam-p1-source.v1.json",
            "file_sha256": "f829e1827aff84dfb332742f74c1f717da655a1ef962e1aca0260d8d2a450d6c",
            "dataset_revision": "a59a74ce31384165065af1823a83c6f94ccafd48",
        },
        "safe_aggregate_protocol": {
            "evaluation_unit": "patent_family",
            "development_split_role": "REP-DEV",
            "development_query_count": 150,
            "train_pool_count": 250,
            "reserved_harness_dev_count": 100,
            "exact_membership_owner_local": True,
            "count_deviation_requires_pre_measurement_protocol_revision": True,
            "seed": 42,
            "primary_metric": "recall_at_100/out",
            "secondary_metrics": ["ndcg_at_100/out", "ndcg_at_10/out"],
            "top_k": 100,
            "tie_policy": "stable_lexical_family_id",
        },
        "owner_local_only_surfaces": [
            "qrels",
            "split_membership",
            "query_ids",
            "protected_evaluator_payload",
            "per_query_outcomes",
            "ephemeral_token_identity_map",
            "credentials",
            "provider_access_material",
            "canonical_mlflow_write",
        ],
        "remote_input_allowlist": [
            "frozen_corpus_text_keyed_by_run_scoped_opaque_family_tokens",
            "frozen_query_text_keyed_by_run_scoped_opaque_work_tokens",
            "structured_independent_claim_markers_without_original_identifiers",
            "frozen_program_adapter_and_result_contract_metadata",
            "safe_output_paths",
        ],
        "remote_output_allowlist": [
            "top100_opaque_family_tokens_by_opaque_work_token",
            "aggregate_resource_receipts",
            "heartbeats",
            "durable_checkpoints",
            "failure_receipts",
        ],
        "owner_local_evaluation": {
            "required": True,
            "validate_safe_return_before_mapping": True,
            "map_opaque_tokens_only_inside_protected_root": True,
            "evaluate_only_after_all_five_workloads_are_complete": True,
            "repository_projection": "validated_aggregate_hash_count_pointer_only",
        },
        "required_owner_local_receipt_fields": [
            "handoff_receipt_id",
            "source_contract_sha256",
            "corpus_bundle_sha256",
            "query_bundle_sha256",
            "split_commitment_sha256",
            "evaluator_sha256",
            "ephemeral_token_map_sha256",
            "corpus_count",
            "query_count",
            "reserved_harness_dev_count",
            "train_pool_count",
            "return_root_free_bytes",
            "receipt_sha256",
        ],
        "scientific_transfer_contract_uri": TRANSFER_PATH.as_posix(),
        "owner_payload_opened_during_preparation": False,
        "remote_payload_staged_during_preparation": False,
        "launch_allowed": False,
        "adopted_for_execution": False,
    }
    return _finalize(body, "handoff_contract_sha256")


def _transfer() -> dict[str, Any]:
    body = {
        "schema_version": "myis.armindex-a1.2-scientific-transfer-contract.v11",
        "transfer_contract_id": "a1.2-scientific-transfer-v11",
        "status": "frozen_request_not_authorized",
        "additive_to_preserved_contracts": [
            {
                "uri": "control/armindex/a1.2/topology-contract.direct-base.v5.json",
                "file_sha256": "e36f28b6fceea0d1e25518d49b37afc808af76afeba0010767f068b7bb2f684e",
                "role": "historical_local_stage_upload_allowlist_unchanged",
            },
            {
                "uri": "control/armindex/a1.2/safe-export-allowlist.v6.json",
                "file_sha256": "f8bc1e7ef07c6e10716e81df2b373bff4620d968572584266124c9137487f201",
                "role": "synthetic_preflight_export_allowlist_unchanged",
            },
        ],
        "owner_local_protected_transfer_manifest": {
            "tracked_in_git": False,
            "required_fields": [
                "transfer_id",
                "request_sha256",
                "adoption_receipt_sha256",
                "dataset_revision",
                "split_commitment_sha256",
                "evaluator_sha256",
                "corpus_bundle_sha256",
                "corpus_bundle_bytes",
                "corpus_family_count",
                "query_bundle_sha256",
                "query_bundle_bytes",
                "rep_dev_query_count",
                "harness_dev_reserved_count",
                "opaque_token_scheme_sha256",
                "ephemeral_token_map_sha256",
                "workload_manifest_set_sha256",
                "expected_result_rows_per_program",
                "manifest_sha256",
            ],
        },
        "remote_upload_allowlist_addition": [
            "protected_corpus_text_bundle_with_run_scoped_opaque_tokens",
            "protected_rep_dev_query_text_bundle_with_run_scoped_opaque_tokens",
            "common_program_set_and_scientific_compiler_source_manifest",
            "aggregate_result_receipt_schema",
            "remote_stage_manifest",
        ],
        "opaque_token_contract": {
            "family_token_pattern": "^F-[a-f0-9]{32}$",
            "publication_token_pattern": "^P-[a-f0-9]{32}$",
            "work_token_pattern": "^Q-[a-f0-9]{32}$",
            "run_scoped": True,
            "cross_run_reuse_allowed": False,
            "token_identity_map_owner_local_only": True,
            "original_identifier_allowed": False,
        },
        "remote_stage_manifest": {
            "required_per_artifact_fields": [
                "role",
                "sha256",
                "size_bytes",
                "relative_path",
                "adoption_id",
                "attempt_id",
            ],
            "reject_unlisted_artifacts": True,
            "reject_symlinks_hardlinks_special_files_or_traversal": True,
            "immutable_after_validation": True,
            "network_fallback_allowed": False,
        },
        "remote_forbidden_surfaces": [
            "qrels",
            "split_membership",
            "original_query_ids",
            "original_family_or_publication_ids",
            "ephemeral_token_identity_map",
            "protected_evaluator_payload",
            "credentials_or_private_keys",
            "canonical_mlflow_git_brain_obsidian_dashboard_or_paper_write",
        ],
        "safe_return_contract": {
            "allowed_members": [
                "top100_unique_opaque_family_tokens_by_opaque_work_token_per_arm_program",
                "hash_bound_lifecycle_resource_and_failure_receipts",
                "archive_member_manifest",
                "archive_receipt",
            ],
            "forbidden_members": [
                "logs",
                "model_weights",
                "embeddings",
                "caches",
                "tensor_checkpoints",
                "raw_inputs",
                "environment_dumps",
                "provider_payloads",
            ],
            "expected_unique_results_per_work_token": 100,
            "unknown_duplicate_or_missing_opaque_token_allowed": False,
            "regular_bounded_unique_members_only": True,
            "symlink_hardlink_or_traversal_allowed": False,
            "local_validation_before_identity_mapping": True,
        },
        "cleanup_receipt": {
            "required_after_validated_local_return": True,
            "required_fields": [
                "attempt_id",
                "remote_root_label",
                "input_archive_sha256",
                "return_archive_sha256",
                "worker_reap_receipt_sha256",
                "deleted_entry_count",
                "deletion_scope_sha256",
                "remote_root_absent_observed",
                "timestamp_utc",
                "provider_destruction_proven",
                "receipt_sha256",
            ],
            "provider_destruction_proven_must_equal": False,
            "filesystem_cleanup_is_secure_deletion_proof": False,
            "default_provider_disposition": "destroy_unless_policy_valid_next_goal_authorized",
        },
        "protected_payload_opened_during_preparation": False,
        "remote_payload_staged_during_preparation": False,
        "launch_allowed": False,
        "adopted_for_execution": False,
    }
    return _finalize(body, "transfer_contract_sha256")


def _program_specs() -> list[dict[str, Any]]:
    return [dict(item) for item in program_set_manifest()["programs"]]


def _program_set(root: Path) -> dict[str, Any]:
    executable_programs = program_set_manifest()
    executable_compiler = compiler_manifest()
    if executable_compiler["source_file_sha256"] != file_sha256(
        root / SCIENTIFIC_COMPILER_PATH
    ):
        raise ValueError("scientific compiler source manifest mismatch")
    compiler_sources = [
        {
            "uri": SCIENTIFIC_COMPILER_PATH.as_posix(),
            "file_sha256": executable_compiler["source_file_sha256"],
        },
        {
            "uri": "src/myis_research/kernel/canonical.py",
            "file_sha256": file_sha256(root / "src/myis_research/kernel/canonical.py"),
        },
    ]
    body = {
        "schema_version": "myis.armindex-a1.2-common-program-set.v11",
        "program_set_id": "a1.2-common-five-programs-v11",
        "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
        "task_id": "A1.2",
        "status": "frozen_request_not_authorized",
        "research_plan": {
            "uri": "docs/research/ARMINDEX_RESEARCH_PLAN_V02.md",
            "file_sha256": file_sha256(root / "docs/research/ARMINDEX_RESEARCH_PLAN_V02.md"),
            "data_role": "REP-DEV",
            "rep_dev_query_count": 150,
            "harness_dev_reserved_count": 100,
        },
        "source_field_contract": {
            "family_identity": "run_scoped_opaque_family_token",
            "publication_identity": "run_scoped_opaque_publication_token",
            "family_member_ordinal_required": True,
            "title_field": "title_en",
            "abstract_field": "abstract_en",
            "claims_field": "claims_text",
            "structured_claim_fields": ["claim_ordinal", "is_independent", "claim_text"],
            "structured_claim_extractor_sha256_status": "pending_owner_adoption_receipt",
            "exact_membership_owner_local": True,
        },
        "compiler_contract": {
            "api_version": executable_compiler["compiler_api_version"],
            "source_files": compiler_sources,
            "source_manifest_sha256": canonical_sha256(compiler_sources),
            "compiler_manifest_sha256": executable_compiler["compiler_manifest_sha256"],
            "executable_program_set_sha256": executable_programs["program_set_sha256"],
            "reversed_input_byte_stability_required": True,
            "source_span_lineage_required": True,
            "coverage_accounting_required": True,
            "silent_truncation_allowed": False,
        },
        "programs": _program_specs(),
        "per_arm_compilation_manifest": {
            "status": "pending_owner_adoption_receipt",
            "required_fields": [
                "arm_id",
                "logical_program_sha256",
                "compiler_source_manifest_sha256",
                "model_lock_file_sha256",
                "adapter_contract_sha256",
                "tokenizer_sha256",
                "effective_input_limit",
                "rendered_input_max_tokens",
                "compiled_representation_sha256",
                "unit_count",
                "coverage_gap_count",
                "omitted_unit_count",
                "truncation_count",
                "index_manifest_sha256",
            ],
            "required_program_arm_bindings": 25,
            "truncation_or_overlength_must_equal": 0,
        },
        "logical_program_count": 5,
        "logical_program_arm_runs": 25,
        "physical_program_view_paths": 35,
        "launch_allowed": False,
        "adopted_for_execution": False,
    }
    return _finalize(body, "program_set_sha256")


def _result_contract(root: Path) -> dict[str, Any]:
    body = {
        "schema_version": "myis.armindex-a1.2-aggregate-result-contract.v11",
        "result_contract_id": "a1.2-common-screen-aggregate-result-v11",
        "status": "frozen_request_not_authorized",
        "receipt_schema": {
            "uri": RESULT_SCHEMA_PATH.as_posix(),
            "file_sha256": file_sha256(root / RESULT_SCHEMA_PATH),
        },
        "completion": {
            "required_program_arm_receipts": 25,
            "required_arm_count": 5,
            "required_program_count": 5,
            "partial_completion_promotable": False,
            "twenty_four_of_twenty_five_status": "FAILED_INCOMPLETE_COMMON_SCREEN",
        },
        "required_aggregate_metrics": {
            "quality": [
                "recall_at_100_out",
                "ndcg_at_100_out",
                "ndcg_at_10_out",
                "unique_relevant_family_query_pairs",
                "judged_query_count",
                "tie_rate",
                "failure_rate",
            ],
            "performance": [
                "compile_latency_ms",
                "index_latency_ms",
                "search_latency_ms_p50_p95_p99",
                "throughput_qps",
                "wall_seconds",
            ],
            "resources": [
                "peak_host_ram_bytes",
                "peak_vram_bytes",
                "index_size_bytes",
                "safe_return_bytes",
            ],
            "reliability": [
                "ranking_replay_count",
                "ranking_replay_hash_match",
                "retry_count",
                "oom_recovery_count",
                "failure_categories",
            ],
        },
        "lineage_required": [
            "request_sha256",
            "adoption_receipt_sha256",
            "transfer_manifest_sha256",
            "workload_manifest_sha256",
            "program_spec_sha256",
            "model_lock_file_sha256",
            "compiler_source_manifest_sha256",
            "runtime_lock_sha256",
            "image_manifest_digest",
            "git_commit",
            "git_tree",
            "frozen_bundle_sha256",
            "evaluator_sha256",
            "split_commitment_sha256",
            "qrels_commitment_sha256",
            "ephemeral_token_map_sha256",
            "safe_return_archive_sha256",
        ],
        "projection_policy": {
            "canonical_write_location": "owner_local_protected_evaluator_then_repository_safe_aggregate_receipt",
            "allowed": ["aggregate_metrics", "hashes", "counts", "safe_pointers", "claim_boundary"],
            "forbidden": [
                "opaque_or_original_rankings",
                "per_query_scores",
                "query_or_family_identifiers",
                "raw_return_manifest",
                "qrels_or_membership",
            ],
            "canonical_receipt_before_projection": True,
            "mlflow_canonical_write_owner_local": True,
        },
        "launch_allowed": False,
        "adopted_for_execution": False,
    }
    return _finalize(body, "result_contract_sha256")


def _stop_conditions() -> dict[str, Any]:
    body = {
        "schema_version": "myis.armindex-a1.2-scientific-stop-conditions.v11",
        "stop_policy_id": "a1.2-scientific-stop-conditions-v11",
        "status": "frozen_request_not_active",
        "pre_contact_hard_stops": [
            "owner_adoption_receipt_absent_or_request_hash_changed",
            "source_commit_tree_not_clean_pushed_and_frozen",
            "v1_v10_or_operational_binding_mismatch",
            "owner_local_handoff_receipt_missing_or_mismatched",
            "required_transfer_artifact_missing_or_hash_mismatch",
            "scientific_transfer_program_or_result_contract_mismatch",
            "rep_dev_count_or_harness_dev_reservation_mismatch",
            "fresh_quote_missing_stale_or_over_any_hard_stop",
            "fresh_provider_identity_or_destroy_path_unavailable",
        ],
        "pre_launch_hard_stops": [
            "image_platform_python_torch_cuda_or_gpu_identity_mismatch",
            "cpu_ram_disk_or_return_capacity_below_contract",
            "model_tokenizer_snowflake_code_or_wheelhouse_hash_mismatch",
            "program_compilation_manifest_missing_truncated_or_overlength",
            "remote_forbidden_surface_or_unsafe_path_detected",
            "owner_ttl_watchdog_or_provider_destroy_dry_run_failed",
        ],
        "runtime_hard_stops": [
            "heartbeat_stale_over_300_seconds",
            "worker_exit_or_sibling_cancellation_failure",
            "oom_after_one_batch_size_only_recovery",
            "non_finite_embedding_or_frozen_dimension_mismatch",
            "input_output_count_or_opaque_token_domain_mismatch",
            "checkpoint_or_resume_integrity_failure",
            "free_disk_below_20_gib",
            "ttl_or_projected_budget_exhaustion",
            "protected_or_credential_surface_detected",
            "safe_export_or_local_return_hash_validation_failure",
            "fewer_than_25_valid_program_arm_results",
            "result_receipt_schema_or_lineage_mismatch",
        ],
        "scientific_fail_closed_rules": {
            "partial_arm_screen_can_complete": False,
            "baseline_mismatch_blocks_evaluation": True,
            "ties_change_no_frozen_decision": True,
            "failed_arm_can_be_silently_removed": False,
            "model_weight_format_precision_or_adapter_change_allowed": False,
            "selection_or_final_fallback_allowed": False,
        },
        "stop_actions": [
            "cancel_and_reap_all_remote_workers",
            "flush_only_allowlisted_receipts_and_checkpoints",
            "collect_and_validate_safe_return_locally",
            "record_failure_without_reinterpreting_completed_arms",
            "emit_remote_cleanup_receipt_only_after_validated_local_return",
            "destroy_provider_unless_policy_valid_next_goal_is_authorized",
        ],
        "launch_allowed": False,
        "adopted_for_execution": False,
    }
    return _finalize(body, "stop_policy_sha256")


def _provider_plan() -> dict[str, Any]:
    body = {
        "schema_version": "myis.armindex-a1.2-provider-admission-plan.v11",
        "plan_id": "a1.2-fresh-vast-4x3090-admission-v11",
        "status": "fresh_admission_required_provider_not_contacted",
        "provider_label": "Vast",
        "destroyed_predecessor_instance_reusable": False,
        "historical_v9_identity_or_quote_admissible": False,
        "requested_topology": {
            "instances": 1,
            "gpu_count": 4,
            "gpu_model_exact": "NVIDIA GeForce RTX 3090",
            "minimum_vram_gib_each": 24,
            "minimum_vcpu": 16,
            "minimum_ram_gib": 64,
            "minimum_free_disk_gib": 250,
            "platform": "linux/amd64",
            "transport": "ssh",
            "jupyter": False,
            "docker_in_docker": False,
        },
        "runtime_identity": {
            "image_reference": IMAGE_REFERENCE,
            "resolved_manifest_digest": IMAGE_DIGEST,
            "python": "3.11",
            "torch": "2.6.0+cu118",
            "cuda": "11.8",
            "runtime_model_download_allowed": False,
            "package_index_access_allowed": False,
        },
        "fresh_admission_checks": [
            "new_provider_instance_id_and_sanitized_quote_receipt",
            "quote_age_at_most_900_seconds_and_full_ttl_cost_fit",
            "clean_pushed_execution_commit_tree_and_bundle_hash",
            "best_observable_image_identity_and_exact_runtime",
            "four_distinct_rtx3090_gpu_uuids",
            "cpu_ram_disk_and_return_capacity",
            "all_frozen_model_code_wheelhouse_and_job_hashes",
            "scientific_transfer_program_result_and_compiler_hashes",
            "rep_dev_150_and_reserved_harness_dev_100_commitments",
            "protected_and_credential_absence_scan",
            "heartbeat_checkpoint_resume_and_safe_export_dry_run",
            "owner_local_ttl_watchdog_and_provider_destroy_dry_run",
        ],
        "owner_local_only": [
            "ssh_keys",
            "provider_credentials",
            "provider_configuration",
            "protected_handoff_receipt",
            "evaluator",
            "mlflow_canonical_write",
            "git_and_projection_writes",
        ],
        "termination": {
            "ttl_seconds": 21600,
            "heartbeat_stale_seconds": 300,
            "guest_poweroff_proves_provider_destruction": False,
            "provider_destroy_or_policy_valid_continuation_required": True,
            "continuation_policy_uri": (
                "control/armindex/a1.2/owner-instance-continuation-policy.v1.json"
            ),
            "continuation_policy_file_sha256": (
                "28402c57d22400b343cdc94ef88aa285ce94eedf3cb44680c9679c6be9654acd"
            ),
        },
        "provider_contacted": False,
        "gpu_reserved": False,
        "launch_allowed": False,
        "adopted_for_execution": False,
    }
    return _finalize(body, "provider_plan_sha256")


def _job(
    arm_id: str,
    program_set: Mapping[str, Any],
    result_contract: Mapping[str, Any],
) -> dict[str, Any]:
    remote = arm_id != "ARM-01"
    gpu_index = int(arm_id[-1]) - 2 if remote else None
    lock_uri, lock_sha256 = MODEL_LOCKS[arm_id]
    body = {
        "schema_version": "myis.armindex-a1.2-scientific-workload.v11",
        "manifest_id": f"a1.2-v11-{arm_id.lower()}-common-screen-request",
        "revision_id": REVISION_ID,
        "status": "frozen_request_not_authorized",
        "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
        "task_id": "A1.2",
        "arm_id": arm_id,
        "execution": {
            "location": "remote" if remote else "owner_local",
            "device": "cuda" if remote else "cpu",
            "cuda_visible_devices": str(gpu_index) if remote else None,
            "visible_gpu_count_required": 1 if remote else 0,
            "parallel_dense_group": "ARM-02..ARM-05" if remote else None,
        },
        "model_lock": {"uri": lock_uri, "file_sha256": lock_sha256},
        "program_set": {
            "uri": PROGRAM_SET_PATH.as_posix(),
            "program_set_sha256": program_set["program_set_sha256"],
            "programs": [
                {
                    "program_id": item["program_key"],
                    "logical_program_sha256": item["program_spec_sha256"],
                    "physical_view_paths": item["physical_view_multiplier"],
                }
                for item in program_set["programs"]
            ],
        },
        "protocol": {
            "split_role": "REP-DEV",
            "query_count": 150,
            "harness_dev_reserved_count": 100,
            "seed": 42,
            "evaluation_unit": "patent_family",
            "top_k": 100,
            "similarity_and_adapter_behavior": "frozen_by_model_lock",
            "expected_program_runs": 5,
        },
        "input_contract": {
            "handoff_uri": HANDOFF_PATH.as_posix(),
            "scientific_transfer_uri": TRANSFER_PATH.as_posix(),
            "actual_payload_hashes_status": "pending_owner_adoption_receipt",
            "protected_transfer_manifest_sha256": "pending_owner_adoption_receipt",
            "opaque_tokens_only": True,
            "network_fallback_allowed": False,
        },
        "output_contract": {
            "evaluation_location": "owner_local_protected_root",
            "remote_result": "top100_opaque_family_tokens_by_opaque_work_token",
            "result_contract_uri": RESULT_CONTRACT_PATH.as_posix(),
            "result_contract_sha256": result_contract["result_contract_sha256"],
            "aggregate_receipt_schema_uri": RESULT_SCHEMA_PATH.as_posix(),
            "aggregate_receipt_schema_sha256": result_contract["receipt_schema"]["file_sha256"],
            "required_aggregate_receipts_per_arm": 5,
            "required_metrics": [
                "quality_and_unique_contribution",
                "latency_and_throughput",
                "ram_vram_and_index_storage",
                "determinism_retries_and_failures",
            ],
            "per_query_projection_allowed": False,
            "aggregate_projection_requires_local_validation": True,
        },
        "adapter_execution_envelope": {
            "model_lock_controls_format_pooling_normalization_and_dimension": True,
            "rendered_input_length_validation_required": True,
            "silent_truncation_allowed": False,
            "precision": "fp16" if arm_id == "ARM-05" else "frozen_by_adoption_receipt",
            "batch_size": 1 if arm_id == "ARM-05" else "frozen_by_adoption_receipt",
            "maximum_input_tokens": 32768 if arm_id == "ARM-05" else "frozen_by_model_lock",
            "qwen_v9_scope_binding": (
                {
                    "uri": (
                        "campaigns/armindex-multiretriever-v2/evidence/"
                        "a1.2-live-synthetic-preflight-result.receipt.v9.json"
                    ),
                    "file_sha256": (
                        "52d1d892c4ce034e3d4b0887a5bddbb362d9747c3b343e766ad2a4302c3f13d6"
                    ),
                    "scope": "single_rtx3090_fp16_batch_one_32768_tokens",
                }
                if arm_id == "ARM-05"
                else None
            ),
        },
        "lifecycle": {
            "heartbeat_seconds": 60,
            "checkpoint_after_each_program": True,
            "resume_requires_same_manifest_and_input_hashes": True,
            "worker_timeout_seconds": 18000,
            "safe_return_required": True,
        },
        "recovery": {
            "batch_size_only_oom_recovery_attempts": (
                1 if remote and arm_id != "ARM-05" else 0
            ),
            "weight_format_precision_adapter_or_program_change_allowed": False,
            "partial_completion_promotable": False,
        },
        "measured_retrieval_allowed": False,
        "launch_allowed": False,
        "adopted_for_execution": False,
    }
    return _finalize(body, "manifest_sha256")


def _workload_set(jobs: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    body = {
        "schema_version": "myis.armindex-a1.2-scientific-workload-set.v11",
        "manifest_set_id": "a1.2-common-five-arm-screen-request-v11",
        "status": "frozen_request_not_authorized",
        "common_program_count": 5,
        "arm_count": 5,
        "expected_program_arm_runs": 25,
        "expected_physical_program_view_paths": 35,
        "arm01_local_cpu": True,
        "dense_arms_parallel": True,
        "one_dense_arm_per_gpu": True,
        "all_arms_required_for_completion": True,
        "manifests": [
            {
                "arm_id": arm_id,
                "uri": (JOB_ROOT / f"{arm_id}.json").as_posix(),
                "manifest_sha256": value["manifest_sha256"],
            }
            for arm_id, value in sorted(jobs.items())
        ],
        "protected_handoff_uri": HANDOFF_PATH.as_posix(),
        "scientific_transfer_uri": TRANSFER_PATH.as_posix(),
        "common_program_set_uri": PROGRAM_SET_PATH.as_posix(),
        "aggregate_result_contract_uri": RESULT_CONTRACT_PATH.as_posix(),
        "actual_input_hashes_status": "pending_owner_adoption_receipt",
        "launch_allowed": False,
        "adopted_for_execution": False,
    }
    return _finalize(body, "manifest_set_sha256")


def _request(
    root: Path,
    components: Mapping[str, Mapping[str, Any]],
    jobs: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    workload_set = components["workload_set"]
    body = {
        "schema_version": "myis.armindex-a1.2-scientific-execution-adoption-request.v11",
        "request_id": REVISION_ID,
        "revision_id": REVISION_ID,
        "status": "prepared_for_owner_review_not_adopted",
        "evidence_class": "scientific_execution_adoption_request_preparation",
        "scientific_authority": False,
        "claim_boundary": (
            "Local CPU-only preparation of a future A1.2 measured common-screen request; "
            "no provider contact, adoption, measured retrieval, optimization, Selection, "
            "Final, paid API work, model change, retrieval-quality result, or publication claim."
        ),
        "campaign_id": "armindex-multiretriever-v2",
        "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
        "task_id": "A1.2",
        "standing_authorization": "D1_START_CAMPAIGN",
        "preparation_base_identity": {
            "git_commit": BASE_COMMIT,
            "git_tree": BASE_TREE,
            "role": "pre_v11_clean_pushed_base_not_execution_identity",
        },
        "predecessor_lineage": _lineage_body(),
        "operational_bindings": _operational_body(),
        "component_bindings": {
            "budget": {
                "uri": BUDGET_PATH.as_posix(),
                "file_sha256": file_sha256(root / BUDGET_PATH),
                "self_sha256": components["budget"]["budget_profile_sha256"],
            },
            "protected_evaluator_handoff": {
                "uri": HANDOFF_PATH.as_posix(),
                "file_sha256": file_sha256(root / HANDOFF_PATH),
                "self_sha256": components["handoff"]["handoff_contract_sha256"],
            },
            "stop_conditions": {
                "uri": STOP_PATH.as_posix(),
                "file_sha256": file_sha256(root / STOP_PATH),
                "self_sha256": components["stops"]["stop_policy_sha256"],
            },
            "provider_admission": {
                "uri": PROVIDER_PATH.as_posix(),
                "file_sha256": file_sha256(root / PROVIDER_PATH),
                "self_sha256": components["provider"]["provider_plan_sha256"],
            },
            "scientific_transfer": {
                "uri": TRANSFER_PATH.as_posix(),
                "file_sha256": file_sha256(root / TRANSFER_PATH),
                "self_sha256": components["transfer"]["transfer_contract_sha256"],
            },
            "common_program_set": {
                "uri": PROGRAM_SET_PATH.as_posix(),
                "file_sha256": file_sha256(root / PROGRAM_SET_PATH),
                "self_sha256": components["program_set"]["program_set_sha256"],
            },
            "aggregate_result_contract": {
                "uri": RESULT_CONTRACT_PATH.as_posix(),
                "file_sha256": file_sha256(root / RESULT_CONTRACT_PATH),
                "self_sha256": components["result_contract"]["result_contract_sha256"],
            },
            "workload_set": {
                "uri": WORKLOAD_SET_PATH.as_posix(),
                "file_sha256": file_sha256(root / WORKLOAD_SET_PATH),
                "self_sha256": workload_set["manifest_set_sha256"],
                "arm_count": len(jobs),
            },
        },
        "future_execution_identity": {
            "clean_pushed_commit_tree": "pending_separate_adoption_receipt",
            "frozen_bundle_sha256": "pending_separate_adoption_receipt",
            "owner_local_handoff_receipt_sha256": "pending_separate_adoption_receipt",
            "owner_local_protected_transfer_manifest_sha256": (
                "pending_separate_adoption_receipt"
            ),
            "compiled_program_manifest_set_sha256": "pending_separate_adoption_receipt",
            "fresh_provider_admission_receipt_sha256": "pending_separate_adoption_receipt",
            "request_hash_must_remain_unchanged": True,
        },
        "adoption": {
            "new_micro_gate_created": False,
            "separate_owner_authorized_goal_required": True,
            "adoption_receipt_present": False,
            "unchanged_request_review_required": True,
        },
        "authorization": {
            "provider_contact_allowed": False,
            "gpu_reservation_allowed": False,
            "launch_allowed": False,
            "adopted_for_execution": False,
            "measured_retrieval_allowed": False,
            "optimization_allowed": False,
            "selection_open": False,
            "final_open": False,
            "paid_api_allowed": False,
            "model_weight_changes_allowed": False,
        },
        "counters": {
            "measured_runs": 0,
            "candidate_count": 0,
            "selection_accesses": 0,
            "final_accesses": 0,
            "gpu_scientific_runs": 0,
            "charged_usd": 0,
            "paid_api_calls": 0,
            "model_weight_changes": 0,
        },
        "next_authorized_action": (
            "Owner reviews the unchanged v11 request locally. A separate goal may "
            "prepare an adoption receipt only after a clean pushed execution commit/tree, "
            "Owner-local protected handoff and transfer receipts, 25 validated compiled-program "
            "bindings, fresh provider identity and all-fee quote, whole-workload budget "
            "admission, and watchdog/destroy checks are available; "
            "do not open a provider during this preparation goal."
        ),
    }
    return _finalize(body, "request_sha256")


def _receipt(root: Path, request: Mapping[str, Any]) -> dict[str, Any]:
    bindings = []
    for path in (
        BUDGET_PATH,
        HANDOFF_PATH,
        TRANSFER_PATH,
        PROGRAM_SET_PATH,
        RESULT_CONTRACT_PATH,
        RESULT_SCHEMA_PATH,
        SCIENTIFIC_COMPILER_PATH,
        STOP_PATH,
        PROVIDER_PATH,
        WORKLOAD_SET_PATH,
        REQUEST_PATH,
        REQUEST_SCHEMA_PATH,
        RECEIPT_SCHEMA_PATH,
        RUNBOOK_PATH,
    ):
        bindings.append({"uri": path.as_posix(), "file_sha256": file_sha256(root / path)})
    body = {
        "schema_version": (
            "myis.armindex-a1.2-scientific-execution-adoption-request-receipt.v11"
        ),
        "receipt_id": REVISION_ID,
        "revision_id": REVISION_ID,
        "status": "PASS",
        "evidence_class": "scientific_execution_adoption_request_preparation",
        "scientific_authority": False,
        "claim_boundary": request["claim_boundary"],
        "request": {
            "uri": REQUEST_PATH.as_posix(),
            "file_sha256": file_sha256(root / REQUEST_PATH),
            "request_sha256": request["request_sha256"],
        },
        "bindings": bindings,
        "ledger": {
            "uri": LEDGER_PATH.as_posix(),
            "start_entry_sha256": (
                "52589c23c0e4d1cb1737d5d7935215746b8fc17a19b3aaade6d12dca9d3f08f0"
            ),
            "append_only": True,
        },
        "validation_summary": {
            "lineage_bindings": len(LINEAGE),
            "operational_bindings": len(OPERATIONAL_BINDINGS),
            "workload_manifests": 5,
            "common_programs": 5,
            "expected_program_arm_runs": 25,
            "expected_physical_program_view_paths": 35,
            "rep_dev_query_count": 150,
            "harness_dev_reserved_count": 100,
            "required_aggregate_result_receipts": 25,
            "provider_contacted": False,
            "protected_payload_opened": False,
        },
        "pending_adoption_requirements": [
            "unchanged_v11_request_hash",
            "clean_pushed_execution_commit_tree_and_bundle_hash",
            "owner_local_protected_handoff_receipt",
            "owner_local_protected_transfer_manifest",
            "twenty_five_valid_compiled_program_bindings",
            "fresh_provider_identity_and_live_quote",
            "whole_workload_budget_admission",
            "owner_local_watchdog_and_provider_destroy_dry_run",
            "separate_owner_authorized_adoption_goal",
        ],
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
        "selection_accesses": 0,
        "final_accesses": 0,
        "charged_usd": 0,
        "next_authorized_action": request["next_authorized_action"],
    }
    return _finalize(body, "receipt_sha256")


def _validate_schema(value: Mapping[str, Any], schema_path: Path, root: Path) -> None:
    schema = json.loads((root / schema_path).read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: list(e.path))
    if errors:
        raise ValueError(f"schema failure at {list(errors[0].path)}: {errors[0].message}")


def _validate_safe(value: Mapping[str, Any]) -> None:
    assert_aggregate_only(value)
    text = json.dumps(value, ensure_ascii=True, sort_keys=True)
    if _SECRET.search(text):
        raise ValueError("secret-like material found in v11 request")
    if re.search(r"(?:[A-Za-z]:\\|/Users/|/home/|\\\\[^\\]+\\)", text):
        raise ValueError("absolute personal path found in v11 request")


def _verify_predecessors(root: Path) -> None:
    for revision, uri, digest, embedded, _ in LINEAGE:
        path = root / uri
        if not path.is_file() or file_sha256(path) != digest:
            raise ValueError(f"{revision} lineage file hash mismatch")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if embedded is not None and payload.get("receipt_sha256") != embedded:
            raise ValueError(f"{revision} embedded receipt hash mismatch")
    for binding_id, uri, digest, embedded, embedded_field in OPERATIONAL_BINDINGS:
        path = root / uri
        if not path.is_file() or file_sha256(path) != digest:
            raise ValueError(f"{binding_id} operational file hash mismatch")
        if embedded is not None:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get(embedded_field) != embedded:
                raise ValueError(f"{binding_id} embedded hash mismatch")
    for arm_id, (uri, digest) in MODEL_LOCKS.items():
        if file_sha256(root / uri) != digest:
            raise ValueError(f"{arm_id} model lock file hash mismatch")


def _validate_ledger(root: Path) -> dict[str, Any]:
    path = root / LEDGER_PATH
    entries = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not entries:
        raise ValueError("v11 preparation ledger is empty")
    previous: str | None = None
    for index, entry in enumerate(entries):
        if entry.get("previous_entry_sha256") != previous:
            raise ValueError(f"v11 preparation ledger chain mismatch at entry {index}")
        observed = entry.get("entry_sha256")
        expected = canonical_sha256(
            {key: value for key, value in entry.items() if key != "entry_sha256"}
        )
        if observed != expected:
            raise ValueError(f"v11 preparation ledger self-hash mismatch at entry {index}")
        previous = str(observed)
    return {"entry_count": len(entries), "head_sha256": previous}


def _write_immutable(path: Path, value: Mapping[str, Any]) -> None:
    text = _json_text(value)
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise ValueError(f"immutable v11 artifact differs: {path.as_posix()}")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="")


def materialize(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    _verify_predecessors(root)
    _validate_ledger(root)
    components = {
        "budget": _budget(),
        "handoff": _handoff(),
        "transfer": _transfer(),
        "program_set": _program_set(root),
        "result_contract": _result_contract(root),
        "stops": _stop_conditions(),
        "provider": _provider_plan(),
    }
    for key, path in (
        ("budget", BUDGET_PATH),
        ("handoff", HANDOFF_PATH),
        ("transfer", TRANSFER_PATH),
        ("program_set", PROGRAM_SET_PATH),
        ("result_contract", RESULT_CONTRACT_PATH),
        ("stops", STOP_PATH),
        ("provider", PROVIDER_PATH),
    ):
        _write_immutable(root / path, components[key])
    jobs = {
        arm_id: _job(arm_id, components["program_set"], components["result_contract"])
        for arm_id in sorted(MODEL_LOCKS)
    }
    for arm_id, job in jobs.items():
        _write_immutable(root / JOB_ROOT / f"{arm_id}.json", job)
    components["workload_set"] = _workload_set(jobs)
    _write_immutable(root / WORKLOAD_SET_PATH, components["workload_set"])
    request = _request(root, components, jobs)
    _validate_schema(request, REQUEST_SCHEMA_PATH, root)
    _check_self_hash(request, "request_sha256")
    _validate_safe(request)
    _write_immutable(root / REQUEST_PATH, request)
    receipt = _receipt(root, request)
    _validate_schema(receipt, RECEIPT_SCHEMA_PATH, root)
    _check_self_hash(receipt, "receipt_sha256")
    _validate_safe(receipt)
    _write_immutable(root / RECEIPT_PATH, receipt)
    return validate(repository_root)


def validate(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    _verify_predecessors(root)
    ledger = _validate_ledger(root)
    components = {
        "budget": _budget(),
        "handoff": _handoff(),
        "transfer": _transfer(),
        "program_set": _program_set(root),
        "result_contract": _result_contract(root),
        "stops": _stop_conditions(),
        "provider": _provider_plan(),
    }
    jobs = {
        arm_id: _job(arm_id, components["program_set"], components["result_contract"])
        for arm_id in sorted(MODEL_LOCKS)
    }
    components["workload_set"] = _workload_set(jobs)
    expected = {
        BUDGET_PATH: components["budget"],
        HANDOFF_PATH: components["handoff"],
        TRANSFER_PATH: components["transfer"],
        PROGRAM_SET_PATH: components["program_set"],
        RESULT_CONTRACT_PATH: components["result_contract"],
        STOP_PATH: components["stops"],
        PROVIDER_PATH: components["provider"],
        WORKLOAD_SET_PATH: components["workload_set"],
        **{JOB_ROOT / f"{arm_id}.json": job for arm_id, job in jobs.items()},
    }
    for path, value in expected.items():
        observed = json.loads((root / path).read_text(encoding="utf-8"))
        if observed != value:
            raise ValueError(f"v11 component differs from frozen request: {path.as_posix()}")
        _validate_safe(observed)
    request = json.loads((root / REQUEST_PATH).read_text(encoding="utf-8"))
    expected_request = _request(root, components, jobs)
    if request != expected_request:
        raise ValueError("v11 request differs from frozen preparation facts")
    _validate_schema(request, REQUEST_SCHEMA_PATH, root)
    _check_self_hash(request, "request_sha256")
    _validate_safe(request)
    receipt = json.loads((root / RECEIPT_PATH).read_text(encoding="utf-8"))
    expected_receipt = _receipt(root, request)
    if receipt != expected_receipt:
        raise ValueError("v11 receipt differs from frozen preparation facts")
    _validate_schema(receipt, RECEIPT_SCHEMA_PATH, root)
    _check_self_hash(receipt, "receipt_sha256")
    _validate_safe(receipt)
    return {
        "status": receipt["status"],
        "revision_id": REVISION_ID,
        "request_file_sha256": file_sha256(root / REQUEST_PATH),
        "request_self_sha256": request["request_sha256"],
        "receipt_file_sha256": file_sha256(root / RECEIPT_PATH),
        "receipt_self_sha256": receipt["receipt_sha256"],
        "lineage_bindings": len(LINEAGE),
        "workload_manifests": len(jobs),
        "ledger_entries": ledger["entry_count"],
        "ledger_head_sha256": ledger["head_sha256"],
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
        "charged_usd": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-scientific-request-v11")
    parser.add_argument("command", choices=("materialize", "validate"))
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    args = parser.parse_args()
    result = materialize(args.repository_root) if args.command == "materialize" else validate(args.repository_root)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
