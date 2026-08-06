"""A1.2 additive v5 direct-base Vast preflight controls.

The provider starts the pinned official PyTorch image.  This revision removes
all custom-image build/save/upload/load and nested-container steps from the
active path while retaining the v1-v3 contracts as immutable history.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from .a1_2_runtime_minimal import POLICY_PATH, REVISION_ID as V4_REVISION_ID, load_runtime_policy
from .a1_2_vast import validate_v1_preserved
from .a1_2_vast_postcommit import validate_postcommit_revision


REVISION_ID = "a1.2-runtime-minimal-direct-base-v5"
IMAGE_REFERENCE = "pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime"
RESOLVED_MANIFEST_DIGEST = "sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20"
RUNTIME_LOCK_PATH = Path("control/armindex/a1.2/runtime-lock.direct-base.v5.json")
IMAGE_CONTRACT_PATH = Path("control/armindex/a1.2/image-digest-contract.direct-base.v5.json")
TOPOLOGY_PATH = Path("control/armindex/a1.2/topology-contract.direct-base.v5.json")
CONTRACT_PATH = Path("control/armindex/a1.2/execution-contract.direct-base.v5.json")
SCHEMA_PATH = Path("schemas/armindex/a1.2-runtime-minimal-direct-base.v5.json")
RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-runtime-minimal-direct-base-migration.receipt.v5.json"
)
COORDINATOR_PATH = Path("scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinator.ps1")
BOOTSTRAP_PATH = Path("scripts/a1_2_vast/remote-bootstrap-direct-base.sh")
LAUNCHER_PATH = Path("scripts/a1_2_vast/remote-launch-4gpu-direct-base.sh")
OWNER_RUNBOOK_PATH = Path("docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V5.md")
V3_RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-vast-4x3090-postcommit-migration.receipt.v3.json"
)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
OCI_RE = re.compile(r"^sha256:[a-f0-9]{64}$")


class DirectBaseError(ValueError):
    """Raised when the direct-base active path is not safe to launch."""


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _load_json(root: Path, path: Path) -> dict[str, Any]:
    value = json.loads((root / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DirectBaseError(f"JSON object required: {path.as_posix()}")
    return value


def _binding(root: Path, path: Path) -> dict[str, str]:
    return {"uri": path.as_posix(), "sha256": file_sha256(root / path)}


def _self_hash(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    body = dict(value)
    body[field] = canonical_sha256(body)
    return body


def materialize_direct_base_revision(repository_root: Path) -> dict[str, Any]:
    """Materialize additive v5 contracts and the aggregate-safe migration receipt."""

    root = repository_root.resolve()
    validate_v1_preserved(root)
    validate_postcommit_revision(root, require_clean=False)
    policy = load_runtime_policy(root)
    if policy.get("revision_id") != V4_REVISION_ID:
        raise DirectBaseError("v4 runtime-minimal policy lineage is missing")
    v3 = _load_json(root, V3_RECEIPT_PATH)
    if v3.get("receipt_sha256") != "75379b2f33b85549036135cf6c7cc1b06c479b6fe5a1643c08a88501fefdc8ca":
        raise DirectBaseError("v3 receipt lineage mismatch")

    runtime_lock = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-runtime-lock.direct-base.v5",
            "runtime_lock_id": REVISION_ID,
            "status": "official_pytorch_base_direct_vast_launch",
            "platform": "linux/amd64",
            "image_reference": IMAGE_REFERENCE,
            "resolved_manifest_digest": RESOLVED_MANIFEST_DIGEST,
            "python": "3.11",
            "pytorch": "2.6.0+cu118",
            "cuda": "11.8",
            "torch_cuda_required": True,
            "dependencies": {"accelerate": "1.6.0", "pyyaml": "6.0.2", "safetensors": "0.5.3", "sentence-transformers": "4.1.0", "transformers": "4.51.3"},
            "offline_install": {"wheelhouse_sha256s_required": True, "pip_index_access_allowed": False, "hf_hub_offline": True, "transformers_offline": True, "runtime_model_download_allowed": False, "local_files_only": True},
            "custom_image_build": False,
            "docker_in_docker": False,
            "jupyter": False,
        },
        "runtime_lock_sha256",
    )
    (root / RUNTIME_LOCK_PATH).write_text(_json_text(runtime_lock), encoding="utf-8", newline="")

    image_contract = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-image-digest-contract.direct-base.v5",
            "image_contract_id": REVISION_ID,
            "status": "manifest_digest_verified_direct_base_no_local_custom_image",
            "image_reference": IMAGE_REFERENCE,
            "resolved_manifest_digest": RESOLVED_MANIFEST_DIGEST,
            "manifest_media_type": "application/vnd.docker.distribution.manifest.v2+json",
            "platform": "linux/amd64",
            "verification": {"source": "docker_buildx_imagetools_inspect_registry_manifest", "tag_is_not_identity": True, "layer_digest_is_not_identity": True, "runtime_pull_allowed": False, "best_observable_remote_identity_required": True},
            "active_path": {"launch_official_image_directly": True, "custom_image_build": False, "docker_save": False, "image_upload": False, "docker_load": False, "nested_container": False, "jupyter": False},
            "launch_allowed": False,
            "adopted_for_execution": False,
        },
        "image_contract_sha256",
    )
    (root / IMAGE_CONTRACT_PATH).write_text(_json_text(image_contract), encoding="utf-8", newline="")

    topology = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-topology-contract.direct-base.v5",
            "topology_id": REVISION_ID,
            "status": "prepared_not_adopted",
            "platform": "linux/amd64",
            "provider": "vast",
            "transport": "ssh",
            "worker": {"instances": 1, "disposable": True, "gpu_count": 4, "gpu_model_exact": "NVIDIA GeForce RTX 3090", "vram_gib_each_min": 24, "minimum_vcpu": 16, "minimum_ram_gib": 64, "minimum_free_disk_gib": 250},
            "arm_placement": {"ARM-01": {"location": "local", "device": "cpu"}, "ARM-02": {"location": "remote", "cuda_visible_devices": "0"}, "ARM-03": {"location": "remote", "cuda_visible_devices": "1"}, "ARM-04": {"location": "remote", "cuda_visible_devices": "2"}, "ARM-05": {"location": "remote", "cuda_visible_devices": "3"}},
            "remote_upload_allowlist": ["frozen_code_bundle", "linux_x86_64_wheelhouse_with_SHA256SUMS", "runtime_minimal_model_directories_with_SHA256SUMS", "safe_job_manifests"],
            "local_only_surfaces": ["evaluation_truth", "split_membership", "qrels", "query_ids", "protected_evaluator", "credentials", "private_keys", "mlflow", "brain", "obsidian", "dashboard", "git", "provider_access_material"],
            "remote_forbidden_surfaces": ["qrels", "split_membership", "query_ids", "credentials", "private_keys", "protected_evaluator_payloads", "unsafe_paths", "pypi", "huggingface", "github"],
            "launch_allowed": False,
            "adopted_for_execution": False,
        },
        "topology_contract_sha256",
    )
    (root / TOPOLOGY_PATH).write_text(_json_text(topology), encoding="utf-8", newline="")

    source_paths = [POLICY_PATH, RUNTIME_LOCK_PATH, IMAGE_CONTRACT_PATH, TOPOLOGY_PATH, COORDINATOR_PATH, BOOTSTRAP_PATH, LAUNCHER_PATH, OWNER_RUNBOOK_PATH, Path("src/myis_research/armindex/a1_2_runtime_minimal_direct_base.py")]
    contract = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-execution-contract.direct-base.v5",
            "contract_id": REVISION_ID,
            "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
            "task_id": "A1.2",
            "status": "direct_base_preflight_prepared_live_vast_pending",
            "evidence_class": "engineering_preflight_revision",
            "scientific_authority": False,
            "migration_from": {"v3_receipt_uri": V3_RECEIPT_PATH.as_posix(), "v3_receipt_sha256": v3["receipt_sha256"], "disposition": "preserved_immutable_additive_direct_base"},
            "runtime_minimal_policy_uri": POLICY_PATH.as_posix(),
            "runtime_minimal_policy_sha256": file_sha256(root / POLICY_PATH),
            "bindings": [_binding(root, path) for path in source_paths],
            "image_reference": IMAGE_REFERENCE,
            "resolved_manifest_digest": RESOLVED_MANIFEST_DIGEST,
            "platform": "linux/amd64",
            "active_path": {"direct_base_launch": True, "custom_image_build": False, "docker_save": False, "image_upload": False, "docker_load": False, "nested_container": False, "runtime_model_download": False, "network_fallback": False},
            "launch_allowed": False,
            "adopted_for_execution": False,
            "upload_artifacts": ["frozen_code_bundle", "linux_x86_64_wheelhouse/SHA256SUMS", "models/ARM-02..ARM-05/SHA256SUMS", "safe_job_manifests"],
            "live_checks_pending": ["exact_git_commit_tree", "frozen_bundle_hash", "image_reference_and_best_observable_identity", "linux_amd64", "python_3_11", "torch_2.6.0_cu118", "cuda_11.8", "cuda_available", "four_distinct_rtx3090_uuids", "gpu_model_and_vram", "cpu_ram_disk", "dependency_versions", "model_sha256sums", "snowflake_remote_code_hashes", "remote_forbidden_surface_absent", "dense_adapter_parity", "qwen_measured_max_length", "gpu_memory_feasibility", "heartbeat_checkpoint_resume", "live_quote_instance_identity", "provider_destroy_ttl"],
            "budget": {"planning_rate_usd_per_four_gpu_instance_hour": 0.6, "estimated_instance_hours": "2-4", "estimated_raw_worker_usd": "1.20-2.40", "common_screen_hard_stop_usd": 18, "a1_hard_stop_usd": 23, "campaign_hard_stop_usd": 100, "live_quote_required": True, "over_hard_stop_status": "BLOCKED_BUDGET"},
            "authorization": {"launch_allowed": False, "adopted_for_execution": False, "measured_retrieval_allowed": False, "synthetic_preflight_workers_only": True, "selection_accesses": 0, "final_accesses": 0},
            "real_counters": {"measured_runs": 0, "candidate_count": 0, "selection_accesses": 0, "final_accesses": 0},
            "resource_counters": {"charged_usd": 0, "gpu_reservations": 0, "gpu_scientific_runs": 0, "model_downloads": 0, "paid_api_calls": 0, "provider_switches": 0},
            "claim_boundary": "local_direct_base_preflight_preparation_only_no_live_vast_or_scientific_authority",
            "next_authorized_action": "Owner stages local runtime-minimal artifacts, then later opens one quoted Vast worker and runs the v5 SSH preflight without measured retrieval.",
        },
        "contract_sha256",
    )
    (root / CONTRACT_PATH).write_text(_json_text(contract), encoding="utf-8", newline="")
    receipt = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-runtime-minimal-direct-base.v5",
            "receipt_id": "a1.2-runtime-minimal-direct-base-migration-v5",
            "revision_id": REVISION_ID,
            "status": "direct_base_preflight_prepared_local_owner_stage_pending",
            "evidence_class": "engineering_preflight_revision",
            "scientific_authority": False,
            "claim_boundary": "direct_official_base_image_path_only_no_vast_contact_no_measured_execution",
            "contract_sha256": file_sha256(root / CONTRACT_PATH),
            "policy_sha256": file_sha256(root / POLICY_PATH),
            "v3_receipt_sha256": v3["receipt_sha256"],
            "image_reference": IMAGE_REFERENCE,
            "resolved_manifest_digest": RESOLVED_MANIFEST_DIGEST,
            "platform": "linux/amd64",
            "local_preparation_status": "runtime_minimal_policy_ready_model_stage_resumable_pending",
            "model_snapshots": "runtime_minimal_frozen",
            "cpu_model_load": "intentionally_skipped_due_host_memory",
            "dense_gpu_parity": "pending_live_vast_preflight",
            "qwen_measured_max_length": "pending_live_vast_preflight",
            "gpu_memory_feasibility": "pending_live_vast_preflight",
            "custom_local_docker_build": False,
            "launch_allowed": False,
            "adopted_for_execution": False,
            "real_counters": {"measured_runs": 0, "candidate_count": 0, "selection_accesses": 0, "final_accesses": 0},
            "resource_counters": {"charged_usd": 0, "gpu_reservations": 0, "gpu_scientific_runs": 0, "model_downloads": 0, "paid_api_calls": 0, "provider_switches": 0},
            "live_checks_pending": contract["live_checks_pending"],
            "removed_active_steps": ["custom_image_build", "docker_save", "image_upload", "docker_load", "nested_container_execution", "runtime_model_download"],
            "upload_artifacts": contract["upload_artifacts"],
            "next_authorized_action": contract["next_authorized_action"],
            "bindings": contract["bindings"],
        },
        "receipt_sha256",
    )
    (root / RECEIPT_PATH).write_text(_json_text(receipt), encoding="utf-8", newline="")
    return {"status": receipt["status"], "revision_id": REVISION_ID, "contract_sha256": contract["contract_sha256"], "receipt_sha256": receipt["receipt_sha256"], "image_reference": IMAGE_REFERENCE, "resolved_manifest_digest": RESOLVED_MANIFEST_DIGEST, "launch_allowed": False, "adopted_for_execution": False}


def validate_direct_base_revision(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    validate_v1_preserved(root)
    validate_postcommit_revision(root, require_clean=False)
    policy = load_runtime_policy(root)
    contract = _load_json(root, CONTRACT_PATH)
    receipt = _load_json(root, RECEIPT_PATH)
    schema = _load_json(root, SCHEMA_PATH)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        raise DirectBaseError(f"v5 receipt schema failure: {errors[0].message}")
    for payload, field in ((contract, "contract_sha256"), (receipt, "receipt_sha256")):
        digest = payload.get(field)
        body = dict(payload)
        body.pop(field, None)
        if digest != canonical_sha256(body):
            raise DirectBaseError(f"v5 {field} mismatch")
    for binding in contract["bindings"]:
        if file_sha256(root / binding["uri"]) != binding["sha256"]:
            raise DirectBaseError(f"v5 binding mismatch: {binding['uri']}")
    for payload in (contract, receipt):
        if payload.get("launch_allowed") is not False or payload.get("adopted_for_execution") is not False:
            raise DirectBaseError("v5 direct-base revision cannot authorize execution")
        if any(float(value) != 0 for value in payload.get("resource_counters", {}).values()) or any(int(value) != 0 for value in payload.get("real_counters", {}).values()):
            raise DirectBaseError("v5 counters must remain zero")
    if receipt.get("contract_sha256") != file_sha256(root / CONTRACT_PATH) or receipt.get("policy_sha256") != file_sha256(root / POLICY_PATH):
        raise DirectBaseError("v5 receipt lineage binding mismatch")
    if contract.get("resolved_manifest_digest") != RESOLVED_MANIFEST_DIGEST or contract.get("platform") != "linux/amd64":
        raise DirectBaseError("v5 OCI platform or manifest digest mismatch")
    if policy.get("revision_id") != V4_REVISION_ID:
        raise DirectBaseError("v4 runtime-minimal policy is not preserved")
    return {"status": "direct_base_prepared_launch_locked", "revision_id": REVISION_ID, "image_reference": IMAGE_REFERENCE, "resolved_manifest_digest": RESOLVED_MANIFEST_DIGEST, "platform": "linux/amd64", "launch_allowed": False, "adopted_for_execution": False, "measured_runs": 0, "selection_accesses": 0, "final_accesses": 0, "charged_usd": 0}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myis-a1.2-runtime-minimal-direct-base")
    parser.add_argument("command", choices=("materialize", "validate"))
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    payload = materialize_direct_base_revision(args.repository_root) if args.command == "materialize" else validate_direct_base_revision(args.repository_root)
    print(_json_text(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
