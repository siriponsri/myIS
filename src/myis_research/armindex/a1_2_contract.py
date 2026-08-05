"""Build and validate the offline A1.2 execution-contract scaffold."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from ..kernel.canonical import canonical_sha256
from ..protection import assert_aggregate_only
from .bm25s_adapter import adapter_lock_material


SCAFFOLD_STATUS = "a1_2_contract_scaffold_complete_launch_locked"
PREPARED_AT_UTC = "2026-08-05T14:30:18Z"
CONTROL_ROOT = Path("control/armindex/a1.2")
RUNBOOK_PATH = Path("control/runbooks/A1_2_COMMON_MULTI_ARM_SCREENING.md")
LEDGER_PATH = CONTROL_ROOT / "execution-scaffold-ledger.v1.jsonl"
RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-contract-scaffold.receipt.v1.json"
)
ARM01_PARITY_RECEIPT_PATH = Path(
    "outputs/fixtures/armindex/a1.2/bm25s-rank-parity-v1/receipt.json"
)

MODEL_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "arm_id": "ARM-02",
        "model_id": "BAAI/bge-m3",
        "source_uri": "https://huggingface.co/BAAI/bge-m3",
        "resolved_revision": "5617a9f61b028005a4858fdac845db406aefb181",
        "license": "MIT",
        "commercial_status": "commercial_capable",
        "dimension": 1024,
        "max_input_tokens": 8192,
        "pooling": "official_dense_implementation_pending_owner_local_parity",
        "normalization": "official_dense_implementation_pending_owner_local_parity",
        "query_format": "no_instruction",
        "critical_artifacts": [
            {"path": "pytorch_model.bin", "sha256": "b5e0ce3470abf5ef3831aa1bd5553b486803e83251590ab7ff35a117cf6aad38"},
            {"path": "tokenizer.json", "sha256": "21106b6d7dab2952c1d496fb21d5dc9db75c28ed361a05f5020bbba27810dd08"},
        ],
        "remote_code": [],
    },
    {
        "arm_id": "ARM-03",
        "model_id": "datalyes/patembed-large",
        "source_uri": "https://huggingface.co/datalyes/patembed-large",
        "resolved_revision": "2d5c0f92a3e5dc3d5415c08e612c57543c0e03ad",
        "license": "CC-BY-NC-SA-4.0",
        "commercial_status": "research_non_commercial",
        "dimension": 1024,
        "max_input_tokens": 512,
        "pooling": "mean_non_padding_tokens",
        "normalization": "l2",
        "query_format": "encode query for different document retrieval: {query}",
        "document_format": "encode document for different retrieval: {document}",
        "critical_artifacts": [
            {"path": "model.safetensors", "sha256": "234ea36a876fe5d5c416c1cbaad6f7221e17861fadd6481f0b96588fdc1ca482"},
        ],
        "metadata_git_oids": [
            {"path": "tokenizer.json", "git_oid": "5dff0fb953b220cf9900a811df9ae7798d802fdc"},
        ],
        "remote_code": [],
    },
    {
        "arm_id": "ARM-04",
        "model_id": "Snowflake/snowflake-arctic-embed-m-v2.0",
        "source_uri": "https://huggingface.co/Snowflake/snowflake-arctic-embed-m-v2.0",
        "resolved_revision": "95c2741480856aa9666782eb4afe11959938017f",
        "license": "Apache-2.0",
        "commercial_status": "commercial_capable",
        "dimension": 768,
        "max_input_tokens": 8192,
        "pooling": "first_token_cls",
        "normalization": "l2",
        "query_format": "query: {query}",
        "document_format": "{document}",
        "critical_artifacts": [
            {"path": "model.safetensors", "sha256": "3d80d4727ac8759fb8624b690697c053a3d1992120111dc4a71178e608c26604"},
            {"path": "tokenizer.json", "sha256": "f1cc44ad7faaeec47241864835473fd5403f2da94673f3f764a77ebcb0a803ec"},
        ],
        "remote_code": [
            {"path": "configuration_hf_alibaba_nlp_gte.py", "git_oid": "d816ed663a58404f966fe322cd113ac39a957686"},
            {"path": "modeling_hf_alibaba_nlp_gte.py", "git_oid": "63c0975e09b5631b564170d2ecb7985c5d8dd189"},
        ],
    },
    {
        "arm_id": "ARM-05",
        "model_id": "Qwen/Qwen3-Embedding-0.6B",
        "source_uri": "https://huggingface.co/Qwen/Qwen3-Embedding-0.6B",
        "resolved_revision": "97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3",
        "license": "Apache-2.0",
        "commercial_status": "commercial_capable",
        "dimension": 1024,
        "declared_max_input_tokens": 32768,
        "measured_max_input_tokens": "pending_owner_local_preflight_freeze",
        "pooling": "last_token_left_padding",
        "normalization": "l2",
        "query_format": "Instruct: Retrieve patent families containing technical information relevant to prior-art search for the query patent family.\nQuery:{query}",
        "document_format": "{document}",
        "critical_artifacts": [
            {"path": "model.safetensors", "sha256": "0437e45c94563b09e13cb7a64478fc406947a93cb34a7e05870fc8dcd48e23fd"},
            {"path": "tokenizer.json", "sha256": "def76fb086971c7867b829c23a26261e38d9d74e02139253b38aeb9df8b4b50a"},
        ],
        "remote_code": [],
    },
)


@dataclass(frozen=True)
class ScaffoldValidation:
    status: str
    file_count: int
    model_lock_count: int
    launch_ready: bool
    measured_execution: bool

    def summary(self) -> dict[str, Any]:
        return {
            "schema_version": "myis.armindex-a1.2-scaffold-validation.v1",
            "status": self.status,
            "file_count": self.file_count,
            "model_lock_count": self.model_lock_count,
            "launch_ready": self.launch_ready,
            "measured_execution": self.measured_execution,
            "protected_data_accessed": False,
            "gpu_used": False,
            "charged_usd": 0,
        }


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _yaml_text(value: Mapping[str, Any]) -> str:
    return yaml.safe_dump(dict(value), allow_unicode=False, sort_keys=False, width=120)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _self_hash(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    result = dict(value)
    result[field] = canonical_sha256(result)
    return result


def _binding(root: Path, relative: str) -> dict[str, str]:
    path = root / relative
    if not path.is_file():
        raise FileNotFoundError(f"required A1.2 scaffold source is missing: {relative}")
    return {"uri": relative, "sha256": _file_sha256(path)}


def _raw_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_a1_2_scaffold_files(repository_root: Path) -> dict[Path, str]:
    root = repository_root.resolve()
    source_bindings = [
        _binding(root, "outputs/fixtures/armindex/a1.1/adapter-cpu-v1/receipt.json"),
        _binding(root, "campaigns/armindex-multiretriever-v2/evidence/a1.1-adapter-fixture-validation.receipt.v1.json"),
        _binding(root, "campaigns/armindex-multiretriever-v2/proposals/a1.2-gpu-execution-plan.v1.json"),
        _binding(root, "docs/research/ARMINDEX_RESEARCH_PLAN_V02.md"),
        _binding(root, "docs/research/MODEL_SELECTION_V02.md"),
        _binding(root, "src/myis_research/armindex/bm25s_adapter.py"),
        _binding(root, "control/runbooks/A1_2_COMMON_MULTI_ARM_SCREENING.md"),
        _binding(root, "docs/research/A1_2_MODEL_SOURCE_LOCKS.md"),
        _binding(root, "src/myis_research/armindex/a1_2_contract.py"),
        _binding(root, "tests/test_armindex_bm25s_adapter.py"),
        _binding(root, "pyproject.toml"),
        _binding(root, "uv.lock"),
    ]
    inputs = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-scaffold-inputs.v1",
            "scaffold_id": "a1.2-common-multi-arm-screen-v1",
            "campaign_id": "armindex-multiretriever-v2",
            "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
            "task_id": "A1.2",
            "prepared_at_utc": PREPARED_AT_UTC,
            "status": SCAFFOLD_STATUS,
            "source_bindings": source_bindings,
            "model_sources": list(MODEL_SOURCES),
            "report_contract": {
                "language": "en",
                "required_sections": 15,
                "one_report_per_registered_phase": True,
                "one_report_per_registered_task": True,
                "archive_policy": "retain_history_archive_only_superseded_unreferenced_checksum_validated_generated_reports",
                "owner_notes_mutable_by_sync": False,
            },
            "safety": {
                "scaffold_cpu_only": True,
                "protected_data_accessed": False,
                "model_payload_downloaded": False,
                "measured_execution": False,
                "gpu_reserved": False,
                "paid_api_used": False,
                "provider_switched": False,
                "selection_opened": False,
                "final_opened": False,
            },
        },
        "inputs_sha256",
    )
    files: dict[Path, str] = {
        CONTROL_ROOT / "scaffold-inputs.v1.yaml": _yaml_text(inputs),
    }

    envelope = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-execution-envelope.v1",
            "envelope_id": "a1.2-common-screen-v1",
            "status": "scaffold_validated_execution_not_authorized",
            "standing_decision": "D1_START_CAMPAIGN",
            "scope": {
                "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
                "task_id": "A1.2",
                "arms": ["ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05"],
                "rep_dev_only": True,
                "selection_open": False,
                "final_open": False,
            },
            "scaffold_resources": {"cpu_only": True, "gpu": False, "paid_api": False, "network_model_download": False, "hard_stop_usd": 0},
            "planned_execution_resources": {
                "gpu_count": 1,
                "minimum_vram_gib": 24,
                "gpu_classes": ["RTX_4090_24GB", "RTX_3090_24GB", "L4_24GB", "A10_24GB"],
                "a100_or_h100_required": False,
                "minimum_vcpu": 8,
                "minimum_ram_gib": 32,
                "recommended_ram_gib": 64,
                "minimum_local_ssd_gib": 200,
                "offline_measured_runtime": True,
                "sequential_dense_model_residency": True,
                "arm01_gpu_budget_usd": 0,
            },
            "authorization": {
                "adopted": False,
                "launch_allowed": False,
                "requires_owner_artifact_manifest": True,
                "requires_owner_live_quote_and_capacity": True,
                "requires_external_termination_dry_run": True,
            },
            "protected_boundary": {
                "repository_output": "aggregate_hash_count_pointer_only",
                "protected_root": "owner_local_only",
                "agent_payload_access": False,
            },
            "inputs_sha256": inputs["inputs_sha256"],
        },
        "envelope_sha256",
    )
    files[Path("control/execution-envelope-a1.2-v1.yaml")] = _yaml_text(envelope)

    budget = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-budget-profile.v1",
            "profile_id": "a1.2-common-screen-v1",
            "status": "scaffold_validated_not_adopted",
            "currency": "USD",
            "limits": {
                "arm01_gpu_usd": 0,
                "pilot_hard_stop_usd": 5,
                "common_screen_hard_stop_usd": 18,
                "a1_total_hard_stop_usd": 23,
                "campaign_hard_stop_usd": 100,
                "gpu_hours_min": 8,
                "gpu_hours_max": 16,
                "end_to_end_hours_min": 10,
                "end_to_end_hours_max": 20,
                "raw_gpu_estimate_min_usd": 2.4,
                "raw_gpu_estimate_max_usd": 12.8,
            },
            "enforcement": {
                "missing_profile_rejected": True,
                "live_quote_required": True,
                "estimate_before_launch_required": True,
                "no_default_inference": True,
                "overrun_action": "stop_flush_request_external_termination",
                "budget_change_after_measurement": "new_campaign_revision_required",
            },
            "actuals": {"charged_usd": 0, "gpu_hours": 0, "measured_runs": 0},
            "inputs_sha256": inputs["inputs_sha256"],
        },
        "budget_profile_sha256",
    )
    budget_path = Path("control/budgets/a1.2-common-screen-v1.json")
    files[budget_path] = _json_text(budget)

    arm01 = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-model-source-lock.v1",
            "arm_id": "ARM-01",
            "model_id": "lexical/bm25s",
            "status": "offline_adapter_frozen_cpu_parity_validated",
            "resolved_revision": "d271d4e1ad7ffdacb224f41bc54aba55159438ecf06439ffe929f088efa96858",
            "package_artifact": {"filename": "bm25s-0.3.10-py3-none-any.whl", "sha256": "d271d4e1ad7ffdacb224f41bc54aba55159438ecf06439ffe929f088efa96858", "size_bytes": 74687},
            "adapter": adapter_lock_material(),
            "owner_artifact_manifest_required": False,
            "network_required": False,
            "gpu_required": False,
            "launch_ready": True,
        },
        "lock_sha256",
    )
    locks = [arm01]
    for source in MODEL_SOURCES:
        locks.append(
            _self_hash(
                {
                    "schema_version": "myis.armindex-a1.2-model-source-lock.v1",
                    **source,
                    "status": "metadata_frozen_owner_artifacts_pending",
                    "owner_artifact_manifest": {
                        "required": True,
                        "required_filename": "SHA256SUMS",
                        "local_config_tokenizer_adapter_hashes_pending": True,
                        "must_bind_all_runtime_files": True,
                    },
                    "network_required": False,
                    "gpu_required": True,
                    "launch_ready": False,
                },
                "lock_sha256",
            )
        )
    lock_entries: list[dict[str, str]] = []
    for lock in locks:
        relative = CONTROL_ROOT / "model-locks" / f"{lock['arm_id']}.v1.json"
        text = _json_text(lock)
        files[relative] = text
        lock_entries.append({"arm_id": str(lock["arm_id"]), "uri": relative.as_posix(), "sha256": _raw_sha(text), "lock_sha256": str(lock["lock_sha256"]), "status": str(lock["status"])})
    lockset = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-model-lockset.v1",
            "lockset_id": "a1.2-five-arm-lockset-v1",
            "status": "metadata_frozen_owner_artifacts_pending",
            "locks": lock_entries,
            "aggregate_counts": {"arms": 5, "offline_adapter_ready": 1, "owner_artifact_manifests_pending": 4, "launch_ready_dense_arms": 0},
            "measured_execution_allowed": False,
        },
        "lockset_sha256",
    )
    lockset_path = CONTROL_ROOT / "model-lockset.v1.json"
    files[lockset_path] = _json_text(lockset)

    shutdown = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-shutdown-plan.v1",
            "plan_id": "a1.2-owner-managed-termination-v1",
            "status": "scaffold_complete_external_termination_dry_run_pending",
            "in_instance_guard": {
                "triggers": ["budget_limit", "wall_clock_limit", "artifact_integrity_failure", "worker_failure", "owner_ttl"],
                "actions": ["stop_new_work", "flush_aggregate_safe_artifacts", "write_terminal_receipt", "emit_shutdown_request", "power_off_instance"],
            },
            "owner_local_watcher": {
                "required": True,
                "credentials_owner_local": True,
                "actions": ["observe_heartbeat_and_ttl", "invoke_provider_instance_termination", "verify_provider_instance_destroyed", "record_sanitized_termination_receipt"],
                "dry_run_validated": False,
            },
            "billing_boundary": "guest_poweroff_does_not_prove_provider_billing_stopped",
            "launch_allowed": False,
        },
        "shutdown_plan_sha256",
    )
    shutdown_path = CONTROL_ROOT / "shutdown-plan.v1.json"
    files[shutdown_path] = _json_text(shutdown)

    checklist = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-launch-checklist.v1",
            "checklist_id": "a1.2-owner-local-launch-v1",
            "status": "launch_locked",
            "passed": [
                "a1.1_engineering_receipt_valid",
                "arm01_bm25s_cpu_rank_parity_valid",
                "five_source_revisions_frozen",
                "budget_limits_hash_bound",
                "report_and_archive_contract_frozen",
            ],
            "pending_owner": [
                "protected_root_mounted_read_only_for_runner",
                "dense_model_SHA256SUMS_manifests_validated",
                "snowflake_remote_code_byte_sha256_validated",
                "dense_adapter_parity_tests_passed",
                "qwen_measured_max_length_frozen",
                "live_quote_capacity_and_provider_instance_id_bound",
                "external_termination_and_ttl_dry_run_passed",
                "artifact_return_path_and_free_space_validated",
                "owner_adopts_execution_contract_without_budget_change",
            ],
            "forbidden_until_all_pass": ["gpu_reservation", "protected_payload_open", "measured_retrieval", "model_download_during_runtime", "selection", "final"],
            "launch_ready": False,
            "bindings": {
                "inputs_sha256": inputs["inputs_sha256"],
                "budget_profile_sha256": budget["budget_profile_sha256"],
                "envelope_sha256": envelope["envelope_sha256"],
                "lockset_sha256": lockset["lockset_sha256"],
                "shutdown_plan_sha256": shutdown["shutdown_plan_sha256"],
            },
        },
        "checklist_sha256",
    )
    checklist_path = CONTROL_ROOT / "launch-checklist.v1.json"
    files[checklist_path] = _json_text(checklist)

    archive_audit = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-report-archive-audit.v1",
            "audit_id": "a1.2-generated-report-archive-audit-v1",
            "status": "PASS",
            "report_language": "en",
            "required_sections": 15,
            "registered_reports": {"phase": 12, "task": 27, "total": 39},
            "archive_candidates": 0,
            "retained_active_or_referenced": 39,
            "archive_root": "obsidian_report/90_Archives/Generated",
            "archive_admission": [
                "managed_generated_report",
                "explicitly_superseded",
                "unreferenced_by_current_registry_manifest_and_artifact_graph",
                "checksum_validated",
                "protected_and_unsafe_path_scans_pass",
                "supersession_pointer_retained",
            ],
            "disposition": "retain_all_current_and_graph_referenced_reports",
            "historical_lineage": "scope_p1_p2_reports_remain_referenced_and_are_not_archive_candidates",
            "owner_notes_moved": False,
            "reports_deleted": False,
        },
        "audit_sha256",
    )
    archive_audit_path = CONTROL_ROOT / "report-archive-audit.v1.json"
    files[archive_audit_path] = _json_text(archive_audit)

    contract = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-execution-contract.v1",
            "contract_id": "a1.2-common-multi-arm-screen-v1",
            "campaign_id": "armindex-multiretriever-v2",
            "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
            "task_id": "A1.2",
            "status": SCAFFOLD_STATUS,
            "adopted_for_execution": False,
            "launch_allowed": False,
            "scientific_authority": False,
            "evidence_class": "engineering_contract_scaffold",
            "claim_boundary": "offline_scaffold_and_arm01_synthetic_cpu_rank_parity_only_no_measured_retrieval_claim",
            "bindings": {
                "inputs": {"uri": (CONTROL_ROOT / "scaffold-inputs.v1.yaml").as_posix(), "sha256": _raw_sha(files[CONTROL_ROOT / "scaffold-inputs.v1.yaml"])},
                "envelope": {"uri": "control/execution-envelope-a1.2-v1.yaml", "sha256": _raw_sha(files[Path("control/execution-envelope-a1.2-v1.yaml")])},
                "budget": {"uri": budget_path.as_posix(), "sha256": _raw_sha(files[budget_path])},
                "lockset": {"uri": lockset_path.as_posix(), "sha256": _raw_sha(files[lockset_path])},
                "checklist": {"uri": checklist_path.as_posix(), "sha256": _raw_sha(files[checklist_path])},
                "shutdown": {"uri": shutdown_path.as_posix(), "sha256": _raw_sha(files[shutdown_path])},
                "report_archive_audit": {"uri": archive_audit_path.as_posix(), "sha256": _raw_sha(files[archive_audit_path])},
            },
            "execution_order": ["ARM-01_local_cpu", "ARM-02_gpu", "ARM-03_gpu", "ARM-04_gpu", "ARM-05_gpu"],
            "resource_plan": {"arm01": "local_cpu_only_zero_gpu_usd", "dense_arms": "one_owner_managed_24_gib_gpu_sequential", "estimated_gpu_hours": "8-16", "estimated_end_to_end_hours": "10-20", "raw_gpu_estimate_usd": "2.40-12.80"},
            "real_counters": {"measured_runs": 0, "candidate_count": 0, "selection_accesses": 0, "final_accesses": 0},
            "resource_counters": {"charged_usd": 0, "gpu_scientific_runs": 0, "paid_api_calls": 0, "model_downloads": 0, "provider_switches": 0},
            "next_authorized_action": "Owner-local artifact-manifest and termination dry-run preflight on CPU; do not reserve GPU until every launch checklist item passes and the contract is explicitly adopted",
        },
        "contract_sha256",
    )
    contract_path = CONTROL_ROOT / "execution-contract.v1.json"
    files[contract_path] = _json_text(contract)

    parity_receipt = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-arm01-rank-parity-receipt.v1",
            "receipt_id": "a1.2-arm01-bm25s-rank-parity-v1",
            "campaign_id": "armindex-multiretriever-v2",
            "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
            "task_id": "A1.2",
            "status": "PASS",
            "evidence_class": "engineering_fixture",
            "scientific_authority": False,
            "claim_boundary": "synthetic_cpu_rank_order_parity_only",
            "backend_id": adapter_lock_material()["backend_id"],
            "reference_backend_id": "kernel_okapi_bm25_fixture_v1",
            "synthetic_case_count": 4,
            "focused_test_count": 7,
            "rank_order_parity": True,
            "score_relation": "repository_okapi_score_equals_bm25s_lucene_score_times_k1_plus_one",
            "k1_plus_one": 2.2,
            "deterministic_rank_commitment": canonical_sha256(
                [
                    ["DOC-001", "DOC-002"],
                    ["DOC-002", "DOC-001"],
                    ["DOC-001", "DOC-002"],
                    ["DOC-003"],
                ]
            ),
            "safety": {
                "synthetic_inputs_only": True,
                "cpu_only": True,
                "protected_data_accessed": False,
                "measured_execution": False,
                "gpu_used": False,
                "network_used": False,
                "paid_api_used": False,
            },
            "real_counters": {"measured_runs": 0, "candidate_count": 0, "selection_accesses": 0, "final_accesses": 0},
            "resource_counters": {"charged_usd": 0, "gpu_scientific_runs": 0, "model_downloads": 0},
        },
        "receipt_sha256",
    )
    files[ARM01_PARITY_RECEIPT_PATH] = _json_text(parity_receipt)

    receipt = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-contract-scaffold-receipt.v1",
            "receipt_id": "a1.2-contract-scaffold-v1",
            "campaign_id": "armindex-multiretriever-v2",
            "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
            "task_id": "A1.2",
            "status": "scaffold_complete_launch_locked",
            "evidence_class": "engineering_contract_scaffold",
            "scientific_authority": False,
            "protected_data_accessed": False,
            "measured_execution_performed": False,
            "artifact_bindings": [
                {"uri": path.as_posix(), "sha256": _raw_sha(text)}
                for path, text in sorted(files.items(), key=lambda item: item[0].as_posix())
            ],
            "contract_self_sha256": contract["contract_sha256"],
            "arm01_parity_receipt_uri": ARM01_PARITY_RECEIPT_PATH.as_posix(),
            "arm01_parity_receipt_sha256": _raw_sha(files[ARM01_PARITY_RECEIPT_PATH]),
            "lockset_self_sha256": lockset["lockset_sha256"],
            "report_contract": inputs["report_contract"],
            "archive_disposition": {
                "candidate_count": 0,
                "status": "retain_all_current_and_graph_referenced_reports",
                "audit_uri": archive_audit_path.as_posix(),
                "audit_sha256": _raw_sha(files[archive_audit_path]),
            },
            "real_counters": contract["real_counters"],
            "resource_counters": contract["resource_counters"],
            "owner_requirements_pending": len(checklist["pending_owner"]),
            "next_authorized_action": contract["next_authorized_action"],
        },
        "receipt_sha256",
    )
    files[RECEIPT_PATH] = _json_text(receipt)

    ledger_entries: list[dict[str, Any]] = []
    previous = "0" * 64
    for sequence, (event_type, status, summary) in enumerate(
        (
            ("start", "active", "Started the offline A1.2 contract scaffold with no GPU reservation or protected payload access."),
            ("arm01_parity", "passed", "Validated the frozen bm25s 0.3.10 ARM-01 rank order against the repository Okapi reference on synthetic CPU inputs."),
            ("scaffold_closeout", "complete_launch_locked", "Hash-bound the A1.2 source locks, budget, execution envelope, launch checklist, shutdown plan, and engineering receipt; dense execution remains Owner-locked."),
        ),
        start=1,
    ):
        entry = {
            "schema_version": "myis.armindex-execution-ledger-entry.v1",
            "ledger_id": "a1.2-contract-scaffold-v1",
            "sequence": sequence,
            "event_id": f"A12-EV{sequence:04d}",
            "event_type": event_type,
            "timestamp_utc": PREPARED_AT_UTC,
            "status": status,
            "evidence_class": "engineering_contract_scaffold",
            "scientific_authority": False,
            "previous_entry_sha256": previous,
            "safety": {"protected_data_accessed": False, "measured_execution": False, "gpu_used": False, "paid_api_used": False, "selection_opened": False, "final_opened": False},
            "summary": summary,
        }
        if sequence == 3:
            entry["receipt_uri"] = RECEIPT_PATH.as_posix()
            entry["receipt_sha256"] = _raw_sha(files[RECEIPT_PATH])
        if sequence == 2:
            entry["artifact_uri"] = ARM01_PARITY_RECEIPT_PATH.as_posix()
            entry["artifact_sha256"] = _raw_sha(files[ARM01_PARITY_RECEIPT_PATH])
        entry["entry_sha256"] = canonical_sha256(entry)
        previous = str(entry["entry_sha256"])
        ledger_entries.append(entry)
    files[LEDGER_PATH] = "".join(_json_text(entry) for entry in ledger_entries)
    return files


def materialize_a1_2_scaffold(repository_root: Path) -> ScaffoldValidation:
    root = repository_root.resolve()
    files = build_a1_2_scaffold_files(root)
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = text.encode("utf-8")
        if path.is_file() and path.read_bytes() != encoded:
            raise FileExistsError(f"A1.2 scaffold artifact drift requires an explicit revision: {relative.as_posix()}")
        if not path.exists():
            path.write_bytes(encoded)
    return validate_a1_2_scaffold(root)


def validate_a1_2_scaffold(repository_root: Path) -> ScaffoldValidation:
    root = repository_root.resolve()
    expected = build_a1_2_scaffold_files(root)
    for relative, text in expected.items():
        path = root / relative
        if not path.is_file() or path.read_bytes() != text.encode("utf-8"):
            raise ValueError(f"A1.2 scaffold artifact is missing or drifted: {relative.as_posix()}")
        if relative.suffix in {".json", ".jsonl"}:
            payloads = [json.loads(line) for line in text.splitlines() if line]
        else:
            loaded = yaml.safe_load(text)
            payloads = [loaded]
        for payload in payloads:
            if not isinstance(payload, Mapping):
                raise ValueError(f"A1.2 scaffold artifact is not an object: {relative.as_posix()}")
            assert_aggregate_only(payload)
    contract = json.loads(expected[CONTROL_ROOT / "execution-contract.v1.json"])
    checklist = json.loads(expected[CONTROL_ROOT / "launch-checklist.v1.json"])
    if contract["launch_allowed"] is not False or checklist["launch_ready"] is not False:
        raise ValueError("A1.2 scaffold cannot authorize launch")
    if any(value != 0 for value in contract["real_counters"].values()):
        raise ValueError("A1.2 scaffold real counters must remain zero")
    if any(value != 0 for value in contract["resource_counters"].values()):
        raise ValueError("A1.2 scaffold resource counters must remain zero")
    return ScaffoldValidation(
        status=SCAFFOLD_STATUS,
        file_count=len(expected),
        model_lock_count=5,
        launch_ready=False,
        measured_execution=False,
    )
