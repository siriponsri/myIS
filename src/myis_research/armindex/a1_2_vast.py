"""Offline A1.2 local-orchestrated Vast 4xRTX3090 preflight scaffold.

This module creates additive v2 controls and exercises only synthetic workers.
It contains no measured-retrieval entry point and never contacts Vast itself.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
from io import BytesIO
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml
from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256


SCHEMA_VERSION = "myis.armindex-a1.2-vast-4x3090-preflight.v2"
REVISION_ID = "a1.2-local-vast-4x3090-v2"
PREPARED_AT_UTC = "2026-08-05T22:57:54Z"
CONTROL_ROOT = Path("control/armindex/a1.2")
RUNBOOK_PATH = Path("control/runbooks/A1_2_VAST_4X3090_PREFLIGHT_V2.md")
LEDGER_PATH = CONTROL_ROOT / "vast-4x3090-preflight-ledger.v2.jsonl"
RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-vast-4x3090-migration.receipt.v2.json"
)
SYNTHETIC_RECEIPT_PATH = Path(
    "outputs/fixtures/armindex/a1.2/vast-4x3090-preflight-v2/receipt.json"
)
DENSE_ARMS = ("ARM-02", "ARM-03", "ARM-04", "ARM-05")
GPU_SLOT_BY_ARM = {arm: slot for slot, arm in enumerate(DENSE_ARMS)}
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
OCI_DIGEST_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
GPU_UUID_RE = re.compile(r"^GPU-[A-Za-z0-9-]{8,}$")

V1_BINDINGS = {
    "control/execution-envelope-a1.2-v1.yaml": "0117e36c7737baba58a1f5de2b3ec42355f3350ec1b856b110e61b3dd4e32cbf",
    "control/budgets/a1.2-common-screen-v1.json": "07ae7de5c7e704c2f905f3da1294c70db1e5f786a2b00ad6d17c97626b86f44c",
    "control/armindex/a1.2/execution-contract.v1.json": "2c927841a06ee355a405f9053976a8e5543f7f43794dca0231ea04d3b286e335",
    "control/armindex/a1.2/launch-checklist.v1.json": "6dff0daf0d4190a1a5018ce28ee20d67af60e82220717adea1ec480867894175",
    "control/armindex/a1.2/shutdown-plan.v1.json": "9bd32b7c22c82be6ccc1f2b0f5f7f9798213d57d1087230468474cc0cbe86482",
    "control/armindex/a1.2/model-lockset.v1.json": "0e31912ba0e036580fd394db9bab2260c0eaffafef6baea89b2f7567460f5e43",
    "control/armindex/a1.2/scaffold-inputs.v1.yaml": "6383c3c790cabe8ad633d8e8312121d97a60ae465c6c7058f39bd2dbb3a060cc",
    "control/armindex/a1.2/execution-scaffold-ledger.v1.jsonl": "c0c2ab001460905e52a8d22606da3a2d44f7c8388612b1592d0b4fa05105273f",
    "campaigns/armindex-multiretriever-v2/evidence/a1.2-contract-scaffold.receipt.v1.json": "834ed83440b7d2c0809588f661739208ddb62d72d6d4cd582f192bd9f2cbff7d",
}

SAFE_EXPORT_PATTERNS = (
    "heartbeats/ARM-0[2-5].json",
    "checkpoints/ARM-0[2-5].json",
    "runtime-receipts/ARM-0[2-5].json",
    "failure-receipts/ARM-0[2-5].json",
    "preflight/remote-hardware.json",
    "preflight/launcher-process.json",
    "safe-export-manifest.json",
)

FORBIDDEN_REMOTE_NAMES = {
    "auth.json",
    "id_rsa",
    "id_ed25519",
    "qrels",
    "membership",
    "query_ids",
    "provider_payload",
}


class A12VastError(ValueError):
    """Raised when an additive v2 contract or synthetic preflight fails."""


@dataclass(frozen=True)
class V2Validation:
    status: str
    file_count: int
    job_count: int
    launch_allowed: bool = False
    adopted_for_execution: bool = False

    def summary(self) -> dict[str, Any]:
        return {
            "schema_version": "myis.armindex-a1.2-vast-v2-validation.v1",
            "revision_id": REVISION_ID,
            "status": self.status,
            "file_count": self.file_count,
            "job_count": self.job_count,
            "launch_allowed": self.launch_allowed,
            "adopted_for_execution": self.adopted_for_execution,
            "gpu_reserved": False,
            "measured_execution": False,
            "charged_usd": 0,
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _yaml_text(value: Mapping[str, Any]) -> str:
    return yaml.safe_dump(dict(value), allow_unicode=False, sort_keys=False, width=120)


def _self_hash(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    result = dict(value)
    result[field] = canonical_sha256(result)
    return result


def _raw_binding(root: Path, relative: str | Path) -> dict[str, str]:
    path = root / relative
    if not path.is_file():
        raise FileNotFoundError(f"required v2 source is missing: {Path(relative).as_posix()}")
    return {"uri": Path(relative).as_posix(), "sha256": file_sha256(path)}


def _git_value(root: Path, expression: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", expression],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _git_lines(root: Path, *arguments: str) -> list[str]:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.splitlines()


def build_frozen_bundle(repository_root: Path, output_path: Path, image_digest: str) -> dict[str, Any]:
    root = repository_root.resolve()
    target = output_path.resolve()
    if target == root or root in target.parents:
        raise A12VastError("frozen bundle output must be outside the repository")
    if not OCI_DIGEST_RE.fullmatch(image_digest):
        raise A12VastError("a resolved OCI image digest is required")
    if _git_lines(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise A12VastError("the repository must be clean before building a frozen bundle")
    commit = _git_value(root, "HEAD^{commit}")
    tree = _git_value(root, "HEAD^{tree}")
    prefixes = (
        "src/myis_research/",
        "control/armindex/a1.2/",
        "control/budgets/a1.2-common-screen-vast-4x3090-v2.json",
        "control/execution-envelope-a1.2-v2.yaml",
        "scripts/a1_2_vast/",
        "containers/a1_2_vast_4x3090/",
        "pyproject.toml",
    )
    tracked = _git_lines(root, "ls-files")
    selected = sorted(path for path in tracked if any(path == prefix or path.startswith(prefix) for prefix in prefixes))
    if not selected:
        raise A12VastError("frozen bundle allowlist selected no tracked files")
    entries = []
    for relative in selected:
        lowered = Path(relative).name.lower()
        if any(fragment in lowered for fragment in FORBIDDEN_REMOTE_NAMES):
            raise A12VastError(f"bundle allowlist selected an unsafe name: {relative}")
        path = root / relative
        entries.append({"path": relative, "sha256": file_sha256(path), "size_bytes": path.stat().st_size})
    manifest = {
        "schema_version": "myis.armindex-a1.2-frozen-bundle.v2",
        "revision_id": REVISION_ID,
        "git_commit": commit,
        "git_tree": tree,
        "image_digest": image_digest,
        "files": entries,
        "file_count": len(entries),
        "protected_surface_included": False,
        "generated_at": _utc_now(),
    }
    manifest["manifest_sha256"] = canonical_sha256(manifest)
    metadata = {
        "GIT_COMMIT": commit + "\n",
        "GIT_TREE": tree + "\n",
        "IMAGE_DIGEST": image_digest + "\n",
        "BUNDLE_MANIFEST.json": _json_text(manifest),
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(f"frozen bundle output already exists: {target}")
    with target.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive:
                for relative in selected:
                    path = root / relative
                    info = tarfile.TarInfo(relative)
                    info.size = path.stat().st_size
                    info.mtime = 0
                    info.mode = 0o755 if path.suffix == ".sh" else 0o644
                    with path.open("rb") as handle:
                        archive.addfile(info, handle)
                for name, text in metadata.items():
                    data = text.encode("utf-8")
                    info = tarfile.TarInfo(name)
                    info.size = len(data)
                    info.mtime = 0
                    info.mode = 0o644
                    archive.addfile(info, BytesIO(data))
    return {
        "status": "PASS",
        "bundle_path": str(target),
        "bundle_sha256": file_sha256(target),
        "bundle_bytes": target.stat().st_size,
        "git_commit": commit,
        "git_tree": tree,
        "image_digest": image_digest,
        "file_count": len(entries),
        "manifest_sha256": manifest["manifest_sha256"],
    }


def validate_v1_preserved(root: Path) -> list[dict[str, str]]:
    bindings: list[dict[str, str]] = []
    for relative, expected in sorted(V1_BINDINGS.items()):
        actual = file_sha256(root / relative)
        if actual != expected:
            raise A12VastError(f"preserved A1.2 v1 artifact drifted: {relative}")
        bindings.append({"uri": relative, "sha256": actual})
    return bindings


def quote_admission(
    *,
    hourly_instance_usd: float,
    estimated_instance_hours: float,
    common_screen_remaining_usd: float = 18.0,
    a1_remaining_usd: float = 23.0,
    campaign_remaining_usd: float = 100.0,
) -> dict[str, Any]:
    values = (
        hourly_instance_usd,
        estimated_instance_hours,
        common_screen_remaining_usd,
        a1_remaining_usd,
        campaign_remaining_usd,
    )
    if any(not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0 for value in values):
        raise A12VastError("quote inputs must be finite non-negative numbers")
    estimated_cost = round(hourly_instance_usd * estimated_instance_hours, 6)
    ceilings = {
        "common_screen_remaining_usd": common_screen_remaining_usd,
        "a1_remaining_usd": a1_remaining_usd,
        "campaign_remaining_usd": campaign_remaining_usd,
    }
    fits = all(estimated_cost <= value for value in ceilings.values())
    return {
        "status": "PASS" if fits else "BLOCKED_BUDGET",
        "hourly_instance_usd": hourly_instance_usd,
        "estimated_instance_hours": estimated_instance_hours,
        "estimated_cost_usd": estimated_cost,
        "ceilings": ceilings,
        "fits_all_ceilings": fits,
    }


def build_v2_files(repository_root: Path) -> dict[Path, str]:
    root = repository_root.resolve()
    v1_bindings = validate_v1_preserved(root)
    source_bindings = [
        _raw_binding(root, RUNBOOK_PATH),
        _raw_binding(root, "containers/a1_2_vast_4x3090/Dockerfile"),
        _raw_binding(root, "containers/a1_2_vast_4x3090/runtime/requirements.v2.txt"),
        _raw_binding(root, "scripts/a1_2_vast/Invoke-A12VastCoordinator.ps1"),
        _raw_binding(root, "scripts/a1_2_vast/Invoke-A12VastWatchdog.ps1"),
        _raw_binding(root, "scripts/a1_2_vast/remote-bootstrap.sh"),
        _raw_binding(root, "scripts/a1_2_vast/remote-launch-4gpu.sh"),
        _raw_binding(root, "src/myis_research/armindex/a1_2_vast.py"),
    ]
    base_commit = _git_value(root, "HEAD^{commit}")
    base_tree = _git_value(root, "HEAD^{tree}")
    inputs = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-vast-preflight-inputs.v2",
            "revision_id": REVISION_ID,
            "prepared_at_utc": PREPARED_AT_UTC,
            "prepared_against_git_commit": base_commit,
            "prepared_against_git_tree": base_tree,
            "v1_preserved_bindings": v1_bindings,
            "source_bindings": source_bindings,
            "authorization": {
                "offline_local_synthetic_only": True,
                "launch_allowed": False,
                "adopted_for_execution": False,
                "paid_worker_contact_allowed": False,
                "model_download_allowed": False,
                "measured_retrieval_allowed": False,
            },
        },
        "inputs_sha256",
    )
    files: dict[Path, str] = {CONTROL_ROOT / "vast-4x3090-inputs.v2.yaml": _yaml_text(inputs)}

    budget = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-budget-profile.v2",
            "profile_id": "a1.2-common-screen-vast-4x3090-v2",
            "status": "planning_quote_recorded_live_quote_required",
            "currency": "USD",
            "planning_quote": {
                "source": "owner_supplied",
                "scope": "complete_four_rtx3090_instance",
                "hourly_instance_usd": 0.6,
                "estimated_instance_hours_min": 2,
                "estimated_instance_hours_max": 4,
                "raw_worker_estimate_min_usd": 1.2,
                "raw_worker_estimate_max_usd": 2.4,
                "scientific_authority": False,
                "authorizes_launch": False,
            },
            "hard_stops": {
                "common_screen_usd": 18,
                "a1_total_usd": 23,
                "campaign_usd": 100,
            },
            "derived_planning_limit": {
                "common_screen_instance_hours_at_planning_rate": 30,
                "live_quote_and_remaining_budget_override_estimate": True,
            },
            "enforcement": {
                "live_quote_required": True,
                "provider_instance_identity_required": True,
                "missing_or_expired_quote_status": "BLOCKED_BUDGET",
                "over_ceiling_status": "BLOCKED_BUDGET",
                "no_default_inference": True,
            },
            "actuals": {"charged_usd": 0, "gpu_hours": 0, "instance_hours": 0, "measured_runs": 0},
            "inputs_sha256": inputs["inputs_sha256"],
        },
        "budget_profile_sha256",
    )
    budget_path = Path("control/budgets/a1.2-common-screen-vast-4x3090-v2.json")
    files[budget_path] = _json_text(budget)

    runtime = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-runtime-lock.v2",
            "runtime_lock_id": "a1.2-vast-4x3090-runtime-v2",
            "status": "offline_definition_frozen_image_build_pending",
            "python": "3.11",
            "cuda": "11.8",
            "pytorch": "2.6.0+cu118",
            "pytorch_cuda_required": True,
            "base_image": {
                "repository": "pytorch/pytorch",
                "tag": "2.6.0-cuda11.8-cudnn9-runtime",
                "digest": None,
                "digest_required_before_live_preflight": True,
            },
            "built_image": {
                "digest": None,
                "digest_required_before_upload": True,
                "tags_are_not_identity": True,
            },
            "python_packages": {
                "accelerate": "1.6.0",
                "pyyaml": "6.0.2",
                "safetensors": "0.5.3",
                "sentence-transformers": "4.1.0",
                "transformers": "4.51.3",
            },
            "offline_install": {
                "wheelhouse_sha256s_required": True,
                "index_access_allowed": False,
                "runtime_model_download_allowed": False,
                "hf_hub_offline": True,
                "transformers_offline": True,
            },
            "dockerfile": _raw_binding(root, "containers/a1_2_vast_4x3090/Dockerfile"),
        },
        "runtime_lock_sha256",
    )
    runtime_path = CONTROL_ROOT / "runtime-lock.v2.json"
    files[runtime_path] = _json_text(runtime)

    image_contract = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-image-digest-contract.v2",
            "image_contract_id": "a1.2-vast-runtime-image-v2",
            "status": "offline_definition_complete_owner_build_digest_pending",
            "dockerfile": _raw_binding(root, "containers/a1_2_vast_4x3090/Dockerfile"),
            "runtime_lock_sha256": runtime["runtime_lock_sha256"],
            "base_image": {
                "mutable_tag_is_identity": False,
                "resolved_digest_required_at_build": True,
            },
            "built_image": {
                "local_tag_is_identity": False,
                "docker_image_id_required": True,
                "expected_pattern": "sha256:<64-lowercase-hex>",
                "bundle_must_bind_image_id": True,
                "remote_verify_and_start_must_recheck_image_id": True,
                "resolved_image_id": None,
            },
            "launch_allowed": False,
            "adopted_for_execution": False,
        },
        "image_contract_sha256",
    )
    image_contract_path = CONTROL_ROOT / "image-digest-contract.v2.json"
    files[image_contract_path] = _json_text(image_contract)

    topology = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-topology-contract.v2",
            "topology_id": "local-codex-vast-4xrtx3090-v2",
            "status": "prepared_not_adopted",
            "canonical_writer": "local_codex_vscode_only",
            "worker": {
                "provider": "vast",
                "instances": 1,
                "disposable": True,
                "transport": "ssh",
                "gpu_count": 4,
                "gpu_model_exact": "NVIDIA GeForce RTX 3090",
                "vram_gib_each_min": 24,
                "minimum_vcpu": 16,
                "minimum_ram_gib": 64,
                "minimum_free_disk_gib": 250,
            },
            "arm_placement": {
                "ARM-01": {"location": "local", "device": "cpu"},
                **{arm: {"location": "remote", "cuda_visible_devices": str(slot), "visible_gpu_count": 1} for arm, slot in GPU_SLOT_BY_ARM.items()},
            },
            "local_only_surfaces": [
                "evaluation_truth",
                "split_membership",
                "protected_evaluator",
                "mlflow_canonical_write",
                "brain",
                "obsidian",
                "dashboard",
                "git",
                "provider_access_material",
                "openai_access_material",
            ],
            "remote_allowlist": [
                "frozen_code_or_image",
                "frozen_model_artifacts",
                "aggregate_safe_retrieval_inputs",
                "immutable_job_manifests",
                "declared_safe_output_paths",
            ],
            "launch_allowed": False,
            "adopted_for_execution": False,
        },
        "topology_contract_sha256",
    )
    topology_path = CONTROL_ROOT / "topology-contract.v2.json"
    files[topology_path] = _json_text(topology)

    safe_export = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-safe-export-allowlist.v2",
            "allowlist_id": "a1.2-vast-safe-export-v2",
            "allowed_patterns": list(SAFE_EXPORT_PATTERNS),
            "text_only": True,
            "maximum_file_bytes": 1048576,
            "maximum_total_bytes": 16777216,
            "forbidden_name_fragments": sorted(FORBIDDEN_REMOTE_NAMES),
            "raw_provider_payload_allowed": False,
            "model_bytes_allowed": False,
            "evaluation_payload_allowed": False,
        },
        "allowlist_sha256",
    )
    allowlist_path = CONTROL_ROOT / "safe-export-allowlist.v2.json"
    files[allowlist_path] = _json_text(safe_export)

    shutdown = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-shutdown-plan.v2",
            "plan_id": "a1.2-owner-local-vast-termination-v2",
            "status": "watchdog_implemented_live_destroy_dry_run_pending",
            "guest_guard": {
                "can_stop_workers": True,
                "can_flush_safe_outputs": True,
                "can_request_poweroff": True,
                "proves_provider_destruction": False,
            },
            "owner_local_watchdog": {
                "script": _raw_binding(root, "scripts/a1_2_vast/Invoke-A12VastWatchdog.ps1"),
                "provider_destroy_required": True,
                "provider_destroy_verification_required": True,
                "ttl_seconds_default": 21600,
                "heartbeat_stale_seconds_default": 300,
                "dry_run_required_before_start": True,
            },
            "launch_allowed": False,
        },
        "shutdown_plan_sha256",
    )
    shutdown_path = CONTROL_ROOT / "shutdown-plan.v2.json"
    files[shutdown_path] = _json_text(shutdown)

    jobs: list[dict[str, Any]] = []
    for arm, slot in GPU_SLOT_BY_ARM.items():
        job = _self_hash(
            {
                "schema_version": "myis.armindex.a1.2-remote-job.v2",
                "job_id": f"a1.2-v2-{arm.lower()}-synthetic-preflight",
                "revision_id": REVISION_ID,
                "arm_id": arm,
                "mode": "synthetic_preflight_only",
                "cuda_visible_devices": str(slot),
                "visible_gpu_count_required": 1,
                "output_prefix": f"arms/{arm}",
                "heartbeat_seconds": 1,
                "checkpoint_every_steps": 1,
                "steps": 3,
                "resume_allowed": True,
                "network_model_download_allowed": False,
                "measured_retrieval_allowed": False,
                "safe_export_allowlist_sha256": safe_export["allowlist_sha256"],
            },
            "job_sha256",
        )
        path = CONTROL_ROOT / "jobs/v2" / f"{arm}.json"
        files[path] = _json_text(job)
        jobs.append({"arm_id": arm, "uri": path.as_posix(), "job_sha256": job["job_sha256"]})

    envelope = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-execution-envelope.v2",
            "envelope_id": REVISION_ID,
            "status": "offline_preflight_revision_prepared_launch_locked",
            "standing_decision": "D1_START_CAMPAIGN",
            "scope": {
                "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
                "task_id": "A1.2",
                "offline_local_synthetic_preparation_only": True,
                "selection_open": False,
                "final_open": False,
            },
            "planned_topology": {
                "local_arm": "ARM-01_cpu",
                "remote_dense_arms": list(DENSE_ARMS),
                "parallelism": 4,
                "one_arm_per_gpu": True,
                "gpu_model": "RTX_3090_24GB",
            },
            "authorization": {
                "launch_allowed": False,
                "adopted_for_execution": False,
                "paid_worker_contact_allowed": False,
                "scientific_execution_allowed": False,
            },
            "bindings": {
                "inputs_sha256": inputs["inputs_sha256"],
                "budget_profile_sha256": budget["budget_profile_sha256"],
                "runtime_lock_sha256": runtime["runtime_lock_sha256"],
                "image_contract_sha256": image_contract["image_contract_sha256"],
                "topology_contract_sha256": topology["topology_contract_sha256"],
                "shutdown_plan_sha256": shutdown["shutdown_plan_sha256"],
                "allowlist_sha256": safe_export["allowlist_sha256"],
            },
        },
        "envelope_sha256",
    )
    envelope_path = Path("control/execution-envelope-a1.2-v2.yaml")
    files[envelope_path] = _yaml_text(envelope)

    required_live_checks = [
        "clean_git_commit_and_tree_match_frozen_bundle",
        "built_oci_image_digest_matches_owner_binding",
        "four_distinct_rtx3090_gpu_uuids",
        "cuda_pytorch_compatibility",
        "cpu_ram_disk_minimums",
        "complete_model_tokenizer_sha256sums",
        "snowflake_remote_code_byte_hashes",
        "dense_adapter_parity",
        "qwen_measured_max_length_frozen",
        "protected_root_read_only_and_local",
        "remote_forbidden_surface_absence",
        "artifact_return_path_free_space",
        "provider_identity_and_live_quote",
        "heartbeat_checkpoint_resume",
        "provider_destroy_ttl_dry_run",
        "owner_adopts_unchanged_revision",
    ]
    checklist = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-launch-checklist.v2",
            "checklist_id": "a1.2-owner-local-vast-4x3090-v2",
            "status": "offline_preparation_only_live_owner_preflight_pending",
            "prepared_checks": [
                "v1_artifacts_hash_preserved",
                "topology_contract_frozen",
                "fixed_cuda_mapping_frozen",
                "coordinator_and_watchdog_implemented",
                "safe_export_allowlist_frozen",
                "budget_hard_stops_preserved",
            ],
            "pending_live_owner": required_live_checks,
            "jobs": jobs,
            "launch_ready": False,
            "launch_allowed": False,
            "adopted_for_execution": False,
            "bindings": {
                "budget_profile_sha256": budget["budget_profile_sha256"],
                "runtime_lock_sha256": runtime["runtime_lock_sha256"],
                "image_contract_sha256": image_contract["image_contract_sha256"],
                "topology_contract_sha256": topology["topology_contract_sha256"],
                "shutdown_plan_sha256": shutdown["shutdown_plan_sha256"],
                "allowlist_sha256": safe_export["allowlist_sha256"],
                "envelope_sha256": envelope["envelope_sha256"],
            },
        },
        "checklist_sha256",
    )
    checklist_path = CONTROL_ROOT / "launch-checklist.v2.json"
    files[checklist_path] = _json_text(checklist)

    contract_bindings = {
        "budget": {"uri": budget_path.as_posix(), "sha256": hashlib.sha256(files[budget_path].encode()).hexdigest()},
        "runtime": {"uri": runtime_path.as_posix(), "sha256": hashlib.sha256(files[runtime_path].encode()).hexdigest()},
        "image": {"uri": image_contract_path.as_posix(), "sha256": hashlib.sha256(files[image_contract_path].encode()).hexdigest()},
        "topology": {"uri": topology_path.as_posix(), "sha256": hashlib.sha256(files[topology_path].encode()).hexdigest()},
        "allowlist": {"uri": allowlist_path.as_posix(), "sha256": hashlib.sha256(files[allowlist_path].encode()).hexdigest()},
        "shutdown": {"uri": shutdown_path.as_posix(), "sha256": hashlib.sha256(files[shutdown_path].encode()).hexdigest()},
        "envelope": {"uri": envelope_path.as_posix(), "sha256": hashlib.sha256(files[envelope_path].encode()).hexdigest()},
        "checklist": {"uri": checklist_path.as_posix(), "sha256": hashlib.sha256(files[checklist_path].encode()).hexdigest()},
        "runbook": _raw_binding(root, RUNBOOK_PATH),
    }
    contract = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-execution-contract.v2",
            "contract_id": REVISION_ID,
            "campaign_id": "armindex-multiretriever-v2",
            "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
            "task_id": "A1.2",
            "status": "preflight_prepared_live_owner_evidence_pending",
            "evidence_class": "engineering_preflight_scaffold",
            "scientific_authority": False,
            "migration_from": {
                "contract_id": "a1.2-common-multi-arm-screen-v1",
                "adopted": False,
                "disposition": "preserved_historical_not_overwritten_not_adopted",
            },
            "bindings": contract_bindings,
            "jobs": jobs,
            "launch_allowed": False,
            "adopted_for_execution": False,
            "real_counters": {"measured_runs": 0, "candidate_count": 0, "selection_accesses": 0, "final_accesses": 0},
            "resource_counters": {"charged_usd": 0, "gpu_reservations": 0, "gpu_scientific_runs": 0, "model_downloads": 0, "paid_api_calls": 0},
            "claim_boundary": "offline_synthetic_four_worker_orchestration_only_no_gpu_or_retrieval_quality_authority",
            "next_authorized_action": "Owner opens one matching Vast instance and runs the exact local SSH preflight commands; stop before scientific launch or adoption.",
        },
        "contract_sha256",
    )
    files[CONTROL_ROOT / "execution-contract.v2.json"] = _json_text(contract)
    return files


def materialize_v2(repository_root: Path) -> V2Validation:
    root = repository_root.resolve()
    files = build_v2_files(root)
    for relative, text in files.items():
        target = root / relative
        if target.exists() and target.read_text(encoding="utf-8") != text:
            if (root / RECEIPT_PATH).exists():
                raise FileExistsError(f"immutable v2 artifact drift requires a new revision: {relative.as_posix()}")
            target.write_text(text, encoding="utf-8", newline="")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text(text, encoding="utf-8", newline="")
    return validate_v2(root)


def validate_v2(repository_root: Path) -> V2Validation:
    root = repository_root.resolve()
    validate_v1_preserved(root)
    expected = build_v2_files(root)
    for relative, text in expected.items():
        path = root / relative
        if not path.is_file() or path.read_text(encoding="utf-8") != text:
            raise A12VastError(f"A1.2 v2 artifact is missing or drifted: {relative.as_posix()}")
    contract = json.loads((root / CONTROL_ROOT / "execution-contract.v2.json").read_text(encoding="utf-8"))
    checklist = json.loads((root / CONTROL_ROOT / "launch-checklist.v2.json").read_text(encoding="utf-8"))
    if contract["launch_allowed"] or contract["adopted_for_execution"]:
        raise A12VastError("v2 preparation cannot authorize execution")
    if checklist["launch_ready"] or checklist["launch_allowed"]:
        raise A12VastError("v2 preparation checklist cannot be launch-ready")
    if any(contract["real_counters"].values()) or any(contract["resource_counters"].values()):
        raise A12VastError("v2 preparation counters must remain zero")
    if (root / RECEIPT_PATH).is_file():
        validate_preparation_receipt(root)
    return V2Validation("prepared_launch_locked", len(expected), len(DENSE_ARMS))


def validate_complete_sha256s(directory: Path) -> dict[str, Any]:
    root = directory.resolve()
    manifest = root / "SHA256SUMS"
    if not manifest.is_file():
        raise A12VastError("SHA256SUMS is missing")
    entries: dict[str, str] = {}
    for line_number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        match = re.fullmatch(r"([a-f0-9]{64})  ([^\r\n]+)", line)
        if not match:
            raise A12VastError(f"malformed SHA256SUMS line {line_number}")
        digest, relative = match.groups()
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or relative in entries:
            raise A12VastError(f"unsafe or duplicate SHA256SUMS path: {relative}")
        entries[relative] = digest
    actual_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS"
    }
    if set(entries) != actual_files:
        missing = sorted(actual_files - set(entries))
        extra = sorted(set(entries) - actual_files)
        raise A12VastError(f"SHA256SUMS coverage mismatch: missing={missing}, extra={extra}")
    for relative, expected in entries.items():
        if file_sha256(root / relative) != expected:
            raise A12VastError(f"SHA256SUMS byte mismatch: {relative}")
    return {
        "status": "PASS",
        "file_count": len(entries),
        "manifest_sha256": file_sha256(manifest),
        "entries_sha256": canonical_sha256(entries),
    }


def _load_job(path: Path) -> dict[str, Any]:
    job = json.loads(path.read_text(encoding="utf-8"))
    body = dict(job)
    digest = body.pop("job_sha256", None)
    if digest != canonical_sha256(body):
        raise A12VastError("job self-hash mismatch")
    arm = job.get("arm_id")
    if arm not in GPU_SLOT_BY_ARM or job.get("mode") != "synthetic_preflight_only":
        raise A12VastError("only frozen synthetic A1.2 jobs are accepted")
    if job.get("cuda_visible_devices") != str(GPU_SLOT_BY_ARM[arm]):
        raise A12VastError("job CUDA mapping drifted")
    if job.get("measured_retrieval_allowed") is not False:
        raise A12VastError("measured retrieval is forbidden in the preflight worker")
    return job


def remote_worker(job_path: Path, output_root: Path, *, fail_after_step: int | None = None) -> dict[str, Any]:
    job = _load_job(job_path)
    arm = job["arm_id"]
    expected_device = job["cuda_visible_devices"]
    observed_device = os.environ.get("CUDA_VISIBLE_DEVICES")
    if observed_device != expected_device:
        raise A12VastError(f"{arm} expected CUDA_VISIBLE_DEVICES={expected_device}")
    root = output_root.resolve()
    dirs = {name: root / name for name in ("heartbeats", "checkpoints", "runtime-receipts", "failure-receipts")}
    for directory in dirs.values():
        directory.mkdir(parents=True, exist_ok=True)
    checkpoint_path = dirs["checkpoints"] / f"{arm}.json"
    start_step = 0
    resumed = False
    if checkpoint_path.is_file() and job.get("resume_allowed"):
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if checkpoint.get("job_sha256") != job["job_sha256"]:
            raise A12VastError("checkpoint job binding mismatch")
        start_step = int(checkpoint.get("completed_steps", 0))
        resumed = start_step > 0
    try:
        for step in range(start_step + 1, int(job["steps"]) + 1):
            now = _utc_now()
            heartbeat = {
                "schema_version": "myis.armindex-a1.2-heartbeat.v2",
                "arm_id": arm,
                "job_sha256": job["job_sha256"],
                "generated_at": now,
                "completed_steps": step - 1,
            }
            (dirs["heartbeats"] / f"{arm}.json").write_text(_json_text(heartbeat), encoding="utf-8", newline="")
            checkpoint = {
                "schema_version": "myis.armindex-a1.2-checkpoint.v2",
                "arm_id": arm,
                "job_sha256": job["job_sha256"],
                "completed_steps": step,
                "generated_at": now,
            }
            checkpoint_path.write_text(_json_text(checkpoint), encoding="utf-8", newline="")
            if fail_after_step == step:
                raise RuntimeError("injected synthetic worker failure")
            time.sleep(0.01)
        receipt = {
            "schema_version": "myis.armindex-a1.2-runtime-receipt.v2",
            "arm_id": arm,
            "job_sha256": job["job_sha256"],
            "status": "synthetic_preflight_passed",
            "cuda_visible_devices": observed_device,
            "visible_gpu_count_required": 1,
            "completed_steps": int(job["steps"]),
            "resumed_from_checkpoint": resumed,
            "process_identity": _process_identity(),
            "measured_execution": False,
            "scientific_authority": False,
            "generated_at": _utc_now(),
        }
        receipt["receipt_sha256"] = canonical_sha256(receipt)
        (dirs["runtime-receipts"] / f"{arm}.json").write_text(_json_text(receipt), encoding="utf-8", newline="")
        return receipt
    except Exception as exc:
        failure = {
            "schema_version": "myis.armindex-a1.2-failure-receipt.v2",
            "arm_id": arm,
            "job_sha256": job["job_sha256"],
            "status": "synthetic_worker_failed",
            "error_type": type(exc).__name__,
            "retry_from_checkpoint_allowed": True,
            "measured_execution": False,
            "generated_at": _utc_now(),
        }
        failure["receipt_sha256"] = canonical_sha256(failure)
        (dirs["failure-receipts"] / f"{arm}.json").write_text(_json_text(failure), encoding="utf-8", newline="")
        raise


def _worker_subprocess(job_path: Path, output_root: Path, slot: int) -> subprocess.Popen[str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if key.upper() not in {"MYIS_STORE", "MYIS_MLFLOW_STORE", "OPENAI_API_KEY", "VAST_API_KEY"}
    }
    env["CUDA_VISIBLE_DEVICES"] = str(slot)
    return subprocess.Popen(
        [sys.executable, "-m", "myis_research.armindex.a1_2_vast", "remote-worker", "--job", str(job_path), "--output-root", str(output_root)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )


def run_synthetic_four_worker(repository_root: Path, output_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    validate_v2(root)
    output = output_root.resolve()
    if output == root or root in output.parents:
        raise A12VastError("synthetic worker output must be outside the repository")
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    processes = [
        _worker_subprocess(root / CONTROL_ROOT / "jobs/v2" / f"{arm}.json", output, slot)
        for arm, slot in GPU_SLOT_BY_ARM.items()
    ]
    failures: list[dict[str, Any]] = []
    for arm, process in zip(DENSE_ARMS, processes, strict=True):
        stdout, stderr = process.communicate(timeout=30)
        if process.returncode != 0:
            failures.append({"arm_id": arm, "exit_code": process.returncode, "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest()})
        elif stdout.strip():
            json.loads(stdout)
    receipts = []
    for arm in DENSE_ARMS:
        path = output / "runtime-receipts" / f"{arm}.json"
        if path.is_file():
            receipts.append(json.loads(path.read_text(encoding="utf-8")))
    payload = {
        "schema_version": "myis.armindex-a1.2-four-worker-synthetic.v2",
        "status": "PASS" if not failures and len(receipts) == 4 else "FAIL",
        "revision_id": REVISION_ID,
        "worker_count": len(receipts),
        "parallel_launch_count": 4,
        "device_mapping": {arm: str(slot) for arm, slot in GPU_SLOT_BY_ARM.items()},
        "isolated_receipts": sorted(item["arm_id"] for item in receipts),
        "failure_count": len(failures),
        "failures": failures,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "cpu_synthetic_only": True,
        "gpu_used": False,
        "charged_usd": 0,
        "measured_execution": False,
        "scientific_authority": False,
        "generated_at": _utc_now(),
    }
    payload["receipt_sha256"] = canonical_sha256(payload)
    return payload


def validate_safe_export(output_root: Path, allowlist_path: Path) -> dict[str, Any]:
    root = output_root.resolve()
    allowlist = json.loads(allowlist_path.read_text(encoding="utf-8"))
    allowed = [re.compile("^" + pattern.replace(".", r"\.").replace("[", "[").replace("]", "]") + "$") for pattern in allowlist["allowed_patterns"]]
    files = [path for path in root.rglob("*") if path.is_file()]
    total = 0
    exported: list[dict[str, Any]] = []
    for path in files:
        relative = path.relative_to(root).as_posix()
        lower = relative.lower()
        if any(fragment in lower for fragment in allowlist["forbidden_name_fragments"]):
            raise A12VastError(f"unsafe export name: {relative}")
        if not any(regex.fullmatch(relative) for regex in allowed):
            raise A12VastError(f"path is outside the safe-export allowlist: {relative}")
        size = path.stat().st_size
        if size > int(allowlist["maximum_file_bytes"]):
            raise A12VastError(f"safe-export file is too large: {relative}")
        path.read_text(encoding="utf-8")
        total += size
        exported.append({"path": relative, "sha256": file_sha256(path), "size_bytes": size})
    if total > int(allowlist["maximum_total_bytes"]):
        raise A12VastError("safe-export total size exceeds the limit")
    return {"status": "PASS", "file_count": len(exported), "total_bytes": total, "files_sha256": canonical_sha256(exported)}


def validate_live_preflight(metadata: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    commit = metadata.get("git_commit")
    tree = metadata.get("git_tree")
    if not isinstance(commit, str) or not re.fullmatch(r"[a-f0-9]{40,64}", commit):
        blockers.append("git_commit")
    if not isinstance(tree, str) or not re.fullmatch(r"[a-f0-9]{40,64}", tree):
        blockers.append("git_tree")
    if not OCI_DIGEST_RE.fullmatch(str(metadata.get("image_digest", ""))):
        blockers.append("image_digest")
    gpus = metadata.get("gpus")
    if not isinstance(gpus, list) or len(gpus) != 4:
        blockers.append("gpu_count")
    else:
        uuids = [item.get("uuid") for item in gpus if isinstance(item, Mapping)]
        models = [item.get("model") for item in gpus if isinstance(item, Mapping)]
        if len(set(uuids)) != 4 or any(not GPU_UUID_RE.fullmatch(str(value)) for value in uuids):
            blockers.append("gpu_uuids")
        if models != ["NVIDIA GeForce RTX 3090"] * 4:
            blockers.append("gpu_models")
    if metadata.get("cuda_available") is not True or metadata.get("pytorch_cuda_compatible") is not True:
        blockers.append("cuda_pytorch")
    if int(metadata.get("cpu_count", 0)) < 16 or float(metadata.get("ram_gib", 0)) < 64 or float(metadata.get("free_disk_gib", 0)) < 250:
        blockers.append("cpu_ram_disk")
    evidence_fields = {
        "model_manifests_complete": "model_manifests_sha256",
        "snowflake_remote_code_hashes_match": "snowflake_remote_code_sha256",
        "dense_adapter_parity": "dense_adapter_parity_sha256",
        "qwen_max_length_frozen": "qwen_max_length_sha256",
    }
    for field, digest_field in evidence_fields.items():
        if metadata.get(field) is not True or not SHA256_RE.fullmatch(str(metadata.get(digest_field, ""))):
            blockers.append(field)
    qwen_maximum = metadata.get("qwen_measured_max_length")
    if not isinstance(qwen_maximum, int) or isinstance(qwen_maximum, bool) or qwen_maximum <= 0 or qwen_maximum > 32768:
        blockers.append("qwen_measured_max_length")
    if (
        metadata.get("protected_root_read_only") is not True
        or metadata.get("protected_root_remote") is not False
        or not SHA256_RE.fullmatch(str(metadata.get("protected_root_probe_sha256", "")))
    ):
        blockers.append("protected_root_boundary")
    if metadata.get("remote_forbidden_surface_absent") is not True:
        blockers.append("remote_forbidden_surface")
    if (
        metadata.get("return_path_writable") is not True
        or float(metadata.get("return_path_free_gib", 0)) < 50
        or not SHA256_RE.fullmatch(str(metadata.get("return_path_probe_sha256", "")))
    ):
        blockers.append("artifact_return_path")
    provider_instance_id = metadata.get("provider_instance_id")
    if (
        not isinstance(provider_instance_id, str)
        or not re.fullmatch(r"[0-9]+", provider_instance_id)
        or metadata.get("quote_live") is not True
        or not SHA256_RE.fullmatch(str(metadata.get("provider_quote_sha256", "")))
    ):
        blockers.append("provider_identity_live_quote")
    quote = quote_admission(
        hourly_instance_usd=float(metadata.get("hourly_instance_usd", -1)),
        estimated_instance_hours=float(metadata.get("estimated_instance_hours", -1)),
        common_screen_remaining_usd=float(metadata.get("common_screen_remaining_usd", 18)),
        a1_remaining_usd=float(metadata.get("a1_remaining_usd", 23)),
        campaign_remaining_usd=float(metadata.get("campaign_remaining_usd", 100)),
    )
    if quote["status"] == "BLOCKED_BUDGET":
        return {"status": "BLOCKED_BUDGET", "blockers": sorted(set(blockers + ["budget"])), "quote": quote, "launch_allowed": False, "adopted_for_execution": False}
    for field in ("heartbeat_fresh", "checkpoint_resume_passed", "provider_destroy_dry_run_passed", "ttl_dry_run_passed"):
        if metadata.get(field) is not True:
            blockers.append(field)
    if not SHA256_RE.fullmatch(str(metadata.get("heartbeat_resume_sha256", ""))):
        blockers.append("heartbeat_resume_receipt")
    if (
        metadata.get("watchdog_provider_instance_id") != provider_instance_id
        or not SHA256_RE.fullmatch(str(metadata.get("watchdog_dry_run_sha256", "")))
    ):
        blockers.append("watchdog_dry_run_receipt")
    return {
        "status": "PASSED_PENDING_OWNER_ADOPTION" if not blockers else "BLOCKED_PREFLIGHT",
        "blockers": sorted(set(blockers)),
        "quote": quote,
        "launch_allowed": False,
        "adopted_for_execution": False,
    }


def _process_identity() -> dict[str, Any]:
    identity: dict[str, Any] = {
        "pid": os.getpid(),
        "started_at_utc": _utc_now(),
    }
    proc_stat = Path(f"/proc/{os.getpid()}/stat")
    boot_id = Path("/proc/sys/kernel/random/boot_id")
    if proc_stat.is_file():
        fields = proc_stat.read_text(encoding="utf-8").split()
        if len(fields) > 21:
            identity["linux_start_ticks"] = fields[21]
    if boot_id.is_file():
        identity["linux_boot_id"] = boot_id.read_text(encoding="utf-8").strip()
    identity["identity_sha256"] = canonical_sha256(identity)
    return identity


def container_self_check(runtime_lock_path: Path) -> dict[str, Any]:
    lock = json.loads(runtime_lock_path.read_text(encoding="utf-8"))
    if lock.get("schema_version") != "myis.armindex-a1.2-runtime-lock.v2":
        raise A12VastError("runtime lock schema mismatch")
    if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("TRANSFORMERS_OFFLINE") != "1":
        raise A12VastError("offline runtime environment is not enforced")
    versions: dict[str, str] = {}
    from importlib.metadata import version

    for package, expected in lock["python_packages"].items():
        actual = version(package)
        if actual != expected:
            raise A12VastError(f"runtime package drift: {package}")
        versions[package] = actual
    return {
        "status": "PASS",
        "runtime_lock_sha256": file_sha256(runtime_lock_path),
        "packages_sha256": canonical_sha256(versions),
        "network_model_download_allowed": False,
    }


def _memory_gib() -> float:
    if Path("/proc/meminfo").is_file():
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                return round(int(line.split()[1]) / 1024**2, 3)
    return 0.0


def remote_preflight(
    *,
    bundle_root: Path,
    output_root: Path,
    model_root: Path,
    expected_git_commit: str,
    expected_git_tree: str,
    expected_image_digest: str,
) -> dict[str, Any]:
    if not re.fullmatch(r"[a-f0-9]{40,64}", expected_git_commit):
        raise A12VastError("expected Git commit is invalid")
    if not re.fullmatch(r"[a-f0-9]{40,64}", expected_git_tree):
        raise A12VastError("expected Git tree is invalid")
    if not OCI_DIGEST_RE.fullmatch(expected_image_digest):
        raise A12VastError("expected OCI image digest is invalid")
    bundle = bundle_root.resolve()
    expected_files = {
        "GIT_COMMIT": expected_git_commit,
        "GIT_TREE": expected_git_tree,
        "IMAGE_DIGEST": expected_image_digest,
    }
    for name, expected in expected_files.items():
        path = bundle / name
        if not path.is_file() or path.read_text(encoding="utf-8").strip() != expected:
            raise A12VastError(f"remote bundle binding mismatch: {name}")
    forbidden_hits = []
    for path in bundle.rglob("*"):
        if path.is_file() and any(fragment in path.name.lower() for fragment in FORBIDDEN_REMOTE_NAMES):
            forbidden_hits.append(path.relative_to(bundle).as_posix())
    if forbidden_hits:
        raise A12VastError("remote bundle contains a forbidden surface")
    manifests = {}
    for arm in DENSE_ARMS:
        manifests[arm] = validate_complete_sha256s(model_root / arm)
    facts = remote_hardware_facts()
    facts.update(
        {
            "git_commit": expected_git_commit,
            "git_tree": expected_git_tree,
            "image_digest": expected_image_digest,
            "ram_gib": _memory_gib(),
            "free_disk_gib": round(shutil.disk_usage(output_root).free / 1024**3, 3),
            "model_manifests": manifests,
            "remote_forbidden_surface_absent": True,
        }
    )
    target = output_root / "preflight" / "remote-hardware.json"
    _write_json(target, facts)
    return facts


def remote_status(output_root: Path) -> dict[str, Any]:
    heartbeats = []
    for arm in DENSE_ARMS:
        path = output_root / "heartbeats" / f"{arm}.json"
        if path.is_file():
            value = json.loads(path.read_text(encoding="utf-8"))
            heartbeats.append({"arm_id": arm, "generated_at": value.get("generated_at"), "completed_steps": value.get("completed_steps")})
    return {
        "schema_version": "myis.armindex-a1.2-remote-status.v2",
        "status": "complete" if len(heartbeats) == 4 else "incomplete",
        "heartbeat_count": len(heartbeats),
        "heartbeats": heartbeats,
        "generated_at": _utc_now(),
    }


def guest_stop(output_root: Path) -> dict[str, Any]:
    value = {
        "schema_version": "myis.armindex-a1.2-guest-stop-request.v2",
        "status": "guest_stop_requested",
        "provider_destruction_proven": False,
        "generated_at": _utc_now(),
    }
    _write_json(output_root / "shutdown-request.json", value)
    return value


def launch_remote_detached(bundle_root: Path, output_root: Path, image_reference: str, image_digest: str) -> dict[str, Any]:
    bundle = bundle_root.resolve()
    output = output_root.resolve()
    launcher = bundle / "scripts/a1_2_vast/remote-launch-4gpu.sh"
    if not launcher.is_file():
        raise A12VastError("remote four-GPU launcher is missing")
    if not re.fullmatch(r"[A-Za-z0-9._/-]+:[A-Za-z0-9._-]+", image_reference):
        raise A12VastError("remote launcher image reference is invalid")
    if not OCI_DIGEST_RE.fullmatch(image_digest):
        raise A12VastError("remote launcher requires an image digest")
    logs = output / "local-remote-logs"
    logs.mkdir(parents=True, exist_ok=True)
    allowed_environment = {
        key: os.environ[key]
        for key in ("PATH", "HOME", "LANG", "LC_ALL", "LD_LIBRARY_PATH", "NVIDIA_VISIBLE_DEVICES", "NVIDIA_DRIVER_CAPABILITIES")
        if key in os.environ
    }
    allowed_environment.update(
        {
            "MYIS_REMOTE_MODE": "a1_2_preflight_only",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "PYTHONPATH": str(bundle / "src"),
        }
    )
    stdout_path = logs / "launcher.stdout.log"
    stderr_path = logs / "launcher.stderr.log"
    with stdout_path.open("ab") as stdout, stderr_path.open("ab") as stderr:
        process = subprocess.Popen(
            ["bash", str(launcher), str(bundle), str(output), image_reference, image_digest],
            cwd=bundle,
            env=allowed_environment,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )
    receipt = {
        "schema_version": "myis.armindex-a1.2-launcher-process.v2",
        "status": "started",
        "process_identity": {"pid": process.pid, "created_at": _utc_now()},
        "environment_allowlist": sorted(allowed_environment),
        "image_digest": image_digest,
        "inherited_environment_dumped": False,
        "measured_execution": False,
        "generated_at": _utc_now(),
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    _write_json(output / "preflight/launcher-process.json", receipt)
    return receipt


def build_safe_export(output_root: Path, allowlist_path: Path, archive_path: Path) -> dict[str, Any]:
    initial = validate_safe_export(output_root, allowlist_path)
    manifest = {
        "schema_version": "myis.armindex-a1.2-safe-export-manifest.v2",
        "status": "PASS",
        "source_file_count": initial["file_count"],
        "source_total_bytes": initial["total_bytes"],
        "source_files_sha256": initial["files_sha256"],
        "generated_at": _utc_now(),
    }
    manifest["manifest_sha256"] = canonical_sha256(manifest)
    _write_json(output_root / "safe-export-manifest.json", manifest)
    validation = validate_safe_export(output_root, allowlist_path)
    files = [path for path in output_root.rglob("*") if path.is_file() and path.resolve() != archive_path.resolve()]
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "w:gz") as archive:
        for path in sorted(files):
            archive.add(path, arcname=path.relative_to(output_root).as_posix(), recursive=False)
    return {
        "status": "PASS",
        "archive_sha256": file_sha256(archive_path),
        "archive_bytes": archive_path.stat().st_size,
        **validation,
    }


def remote_hardware_facts() -> dict[str, Any]:
    completed = subprocess.run(
        ["nvidia-smi", "--query-gpu=uuid,name,memory.total", "--format=csv,noheader,nounits"],
        check=True,
        capture_output=True,
        text=True,
    )
    gpus = []
    for line in completed.stdout.splitlines():
        uuid, name, memory = [part.strip() for part in line.split(",", 2)]
        gpus.append({"uuid": uuid, "model": name, "memory_mib": int(memory)})
    import torch

    return {
        "schema_version": "myis.armindex-a1.2-remote-hardware.v2",
        "gpus": gpus,
        "cuda_available": torch.cuda.is_available(),
        "pytorch_cuda_version": torch.version.cuda,
        "pytorch_version": torch.__version__,
        "cpu_count": os.cpu_count(),
        "generated_at": _utc_now(),
    }


def write_preparation_receipt(repository_root: Path, synthetic_receipt: Mapping[str, Any]) -> dict[str, Any]:
    root = repository_root.resolve()
    validation = validate_v2(root)
    if synthetic_receipt.get("status") != "PASS" or synthetic_receipt.get("worker_count") != 4:
        raise A12VastError("four-worker synthetic receipt is not complete")
    generated_paths = sorted(build_v2_files(root))
    bindings = [_raw_binding(root, path) for path in generated_paths]
    bindings.extend(
        _raw_binding(root, path)
        for path in (
            RUNBOOK_PATH,
            "src/myis_research/armindex/a1_2_vast.py",
            "scripts/a1_2_vast/Invoke-A12VastCoordinator.ps1",
            "scripts/a1_2_vast/Invoke-A12VastWatchdog.ps1",
            "scripts/a1_2_vast/remote-bootstrap.sh",
            "scripts/a1_2_vast/remote-launch-4gpu.sh",
            "containers/a1_2_vast_4x3090/Dockerfile",
            "containers/a1_2_vast_4x3090/runtime/requirements.v2.txt",
            "schemas/armindex/a1.2-vast-4x3090-preflight.v2.json",
            "tests/test_armindex_a1_2_vast.py",
            "docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK.md",
        )
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "receipt_id": "a1.2-vast-4x3090-migration-and-preparation-v2",
        "revision_id": REVISION_ID,
        "status": "offline_preparation_complete_live_owner_preflight_pending",
        "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
        "task_id": "A1.2",
        "evidence_class": "engineering_preflight_scaffold",
        "scientific_authority": False,
        "generated_at": _utc_now(),
        "validation": validation.summary(),
        "synthetic_four_worker": {
            "uri": SYNTHETIC_RECEIPT_PATH.as_posix(),
            "file_sha256": file_sha256(root / SYNTHETIC_RECEIPT_PATH),
            "receipt_sha256": synthetic_receipt["receipt_sha256"],
            "worker_count": synthetic_receipt["worker_count"],
            "parallel_launch_count": synthetic_receipt["parallel_launch_count"],
        },
        "bindings": bindings,
        "v1_preserved_bindings": validate_v1_preserved(root),
        "budget": {
            "planning_rate_usd_per_four_gpu_instance_hour": 0.6,
            "estimated_instance_hours": "2-4",
            "estimated_raw_worker_usd": "1.20-2.40",
            "common_screen_hard_stop_usd": 18,
            "a1_hard_stop_usd": 23,
            "campaign_hard_stop_usd": 100,
            "charged_usd": 0,
        },
        "launch_allowed": False,
        "adopted_for_execution": False,
        "real_counters": {"measured_runs": 0, "candidate_count": 0, "selection_accesses": 0, "final_accesses": 0},
        "resource_counters": {"charged_usd": 0, "gpu_reservations": 0, "gpu_scientific_runs": 0, "model_downloads": 0, "paid_api_calls": 0},
        "claim_boundary": "offline_synthetic_preparation_only_live_vast_and_scientific_execution_unstarted",
        "next_authorized_action": "Owner opens one four-RTX3090 Vast instance and runs the documented local SSH preflight without starting measured retrieval.",
    }
    payload["receipt_sha256"] = canonical_sha256(payload)
    return payload


def _ledger_entry(value: Mapping[str, Any]) -> dict[str, Any]:
    entry = dict(value)
    entry["entry_sha256"] = canonical_sha256(entry)
    return entry


def _validate_ledger(path: Path) -> list[dict[str, Any]]:
    entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    previous = "0" * 64
    for index, entry in enumerate(entries, 1):
        body = dict(entry)
        digest = body.pop("entry_sha256", None)
        if digest != canonical_sha256(body):
            raise A12VastError(f"v2 ledger entry {index} self-hash mismatch")
        if entry.get("sequence") != index or entry.get("previous_entry_sha256") != previous:
            raise A12VastError(f"v2 ledger entry {index} chain mismatch")
        previous = str(digest)
    return entries


def _closeout_ledger(root: Path, synthetic: Mapping[str, Any], receipt: Mapping[str, Any]) -> None:
    path = root / LEDGER_PATH
    existing = _validate_ledger(path)
    if len(existing) not in {1, 3}:
        raise A12VastError("v2 ledger has an unexpected preparation state")
    event2 = _ledger_entry(
        {
            "schema_version": "myis.armindex-a1.2-vast-preflight-ledger-entry.v2",
            "ledger_id": "a1.2-local-vast-4x3090-preflight-v2",
            "event_id": "A12V2-EV0002",
            "sequence": 2,
            "event_type": "synthetic_four_worker",
            "status": "passed",
            "timestamp_utc": synthetic["generated_at"],
            "previous_entry_sha256": existing[0]["entry_sha256"],
            "evidence_class": "engineering_preflight_scaffold",
            "scientific_authority": False,
            "artifact_uri": SYNTHETIC_RECEIPT_PATH.as_posix(),
            "artifact_sha256": file_sha256(root / SYNTHETIC_RECEIPT_PATH),
            "summary": "Four isolated CPU subprocesses passed the fixed ARM-02 through ARM-05 device mapping with heartbeat, checkpoint, and runtime receipts.",
            "safety": {
                "gpu_reserved": False,
                "measured_execution": False,
                "protected_data_accessed": False,
                "paid_api_calls": 0,
                "charged_usd": 0,
                "selection_opened": False,
                "final_opened": False,
            },
        }
    )
    event3 = _ledger_entry(
        {
            "schema_version": "myis.armindex-a1.2-vast-preflight-ledger-entry.v2",
            "ledger_id": "a1.2-local-vast-4x3090-preflight-v2",
            "event_id": "A12V2-EV0003",
            "sequence": 3,
            "event_type": "offline_preparation_closeout",
            "status": "complete_live_owner_preflight_pending",
            "timestamp_utc": receipt["generated_at"],
            "previous_entry_sha256": event2["entry_sha256"],
            "evidence_class": "engineering_preflight_scaffold",
            "scientific_authority": False,
            "receipt_uri": RECEIPT_PATH.as_posix(),
            "receipt_sha256": file_sha256(root / RECEIPT_PATH),
            "summary": "Closed the additive offline v2 preparation while keeping launch, adoption, measured retrieval, Selection, and Final locked.",
            "safety": {
                "gpu_reserved": False,
                "measured_execution": False,
                "protected_data_accessed": False,
                "paid_api_calls": 0,
                "charged_usd": 0,
                "selection_opened": False,
                "final_opened": False,
            },
        }
    )
    expected = [existing[0], event2, event3]
    if len(existing) == 3:
        if existing != expected:
            raise A12VastError("immutable v2 ledger differs from expected closeout")
        return
    path.write_text("".join(_json_text(entry) for entry in expected), encoding="utf-8", newline="")


def finalize_preparation(repository_root: Path, synthetic_receipt_path: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    synthetic = json.loads(synthetic_receipt_path.read_text(encoding="utf-8"))
    body = dict(synthetic)
    digest = body.pop("receipt_sha256", None)
    if digest != canonical_sha256(body) or synthetic.get("status") != "PASS":
        raise A12VastError("synthetic four-worker receipt is invalid")
    _write_json(root / SYNTHETIC_RECEIPT_PATH, synthetic)
    receipt = write_preparation_receipt(root, synthetic)
    _write_json(root / RECEIPT_PATH, receipt)
    _closeout_ledger(root, synthetic, receipt)
    validate_preparation_receipt(root)
    return receipt


def validate_preparation_receipt(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    path = root / RECEIPT_PATH
    receipt = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads((root / "schemas/armindex/a1.2-vast-4x3090-preflight.v2.json").read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        raise A12VastError(f"v2 preparation receipt schema failure: {errors[0].message}")
    body = dict(receipt)
    digest = body.pop("receipt_sha256", None)
    if digest != canonical_sha256(body):
        raise A12VastError("v2 preparation receipt self-hash mismatch")
    for binding in receipt["bindings"] + receipt["v1_preserved_bindings"]:
        if file_sha256(root / binding["uri"]) != binding["sha256"]:
            raise A12VastError(f"v2 preparation receipt binding mismatch: {binding['uri']}")
    if receipt["launch_allowed"] or receipt["adopted_for_execution"]:
        raise A12VastError("v2 preparation receipt cannot authorize execution")
    if any(receipt["real_counters"].values()) or any(receipt["resource_counters"].values()):
        raise A12VastError("v2 preparation receipt counters must remain zero")
    ledger = _validate_ledger(root / LEDGER_PATH)
    if len(ledger) not in {1, 3}:
        raise A12VastError("v2 preparation ledger state is invalid")
    return receipt


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = _json_text(value)
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise FileExistsError(f"immutable receipt differs: {path}")
    if not path.exists():
        path.write_text(text, encoding="utf-8", newline="")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myis-a1.2-vast")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("materialize", "validate"):
        child = sub.add_parser(command)
        child.add_argument("--repository-root", type=Path, default=Path.cwd())
    worker = sub.add_parser("remote-worker")
    worker.add_argument("--job", type=Path, required=True)
    worker.add_argument("--output-root", type=Path, required=True)
    worker.add_argument("--fail-after-step", type=int)
    synthetic = sub.add_parser("synthetic-four-worker")
    synthetic.add_argument("--repository-root", type=Path, default=Path.cwd())
    synthetic.add_argument("--output-root", type=Path, required=True)
    synthetic.add_argument("--receipt", type=Path)
    live = sub.add_parser("validate-live-preflight")
    live.add_argument("--metadata", type=Path, required=True)
    facts = sub.add_parser("remote-hardware")
    facts.add_argument("--output", type=Path)
    container = sub.add_parser("container-self-check")
    container.add_argument("--runtime-lock", type=Path, required=True)
    preflight = sub.add_parser("remote-preflight")
    preflight.add_argument("--bundle-root", type=Path, required=True)
    preflight.add_argument("--output-root", type=Path, required=True)
    preflight.add_argument("--model-root", type=Path, required=True)
    preflight.add_argument("--expected-git-commit", required=True)
    preflight.add_argument("--expected-git-tree", required=True)
    preflight.add_argument("--expected-image-digest", required=True)
    status = sub.add_parser("remote-status")
    status.add_argument("--output-root", type=Path, required=True)
    stop = sub.add_parser("guest-stop")
    stop.add_argument("--output-root", type=Path, required=True)
    export = sub.add_parser("safe-export")
    export.add_argument("--output-root", type=Path, required=True)
    export.add_argument("--allowlist", type=Path, required=True)
    export.add_argument("--archive", type=Path, required=True)
    detached = sub.add_parser("launch-detached")
    detached.add_argument("--bundle-root", type=Path, required=True)
    detached.add_argument("--output-root", type=Path, required=True)
    detached.add_argument("--image-reference", required=True)
    detached.add_argument("--image-digest", required=True)
    bundle = sub.add_parser("build-frozen-bundle")
    bundle.add_argument("--repository-root", type=Path, default=Path.cwd())
    bundle.add_argument("--output", type=Path, required=True)
    bundle.add_argument("--image-digest", required=True)
    finalize = sub.add_parser("finalize-preparation")
    finalize.add_argument("--repository-root", type=Path, default=Path.cwd())
    finalize.add_argument("--synthetic-receipt", type=Path, required=True)
    sha = sub.add_parser("validate-sha256s")
    sha.add_argument("--directory", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "materialize":
        print(_json_text(materialize_v2(args.repository_root).summary()), end="")
        return 0
    if args.command == "validate":
        print(_json_text(validate_v2(args.repository_root).summary()), end="")
        return 0
    if args.command == "remote-worker":
        receipt = remote_worker(args.job, args.output_root, fail_after_step=args.fail_after_step)
        print(_json_text(receipt), end="")
        return 0
    if args.command == "synthetic-four-worker":
        receipt = run_synthetic_four_worker(args.repository_root, args.output_root)
        if args.receipt:
            _write_json(args.receipt, receipt)
        print(_json_text(receipt), end="")
        return 0 if receipt["status"] == "PASS" else 1
    if args.command == "validate-live-preflight":
        metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
        result = validate_live_preflight(metadata)
        print(_json_text(result), end="")
        return 0 if result["status"] == "PASSED_PENDING_OWNER_ADOPTION" else 3
    if args.command == "remote-hardware":
        facts = remote_hardware_facts()
        if args.output:
            _write_json(args.output, facts)
        print(_json_text(facts), end="")
        return 0
    if args.command == "container-self-check":
        print(_json_text(container_self_check(args.runtime_lock)), end="")
        return 0
    if args.command == "remote-preflight":
        result = remote_preflight(
            bundle_root=args.bundle_root,
            output_root=args.output_root,
            model_root=args.model_root,
            expected_git_commit=args.expected_git_commit,
            expected_git_tree=args.expected_git_tree,
            expected_image_digest=args.expected_image_digest,
        )
        print(_json_text(result), end="")
        return 0
    if args.command == "remote-status":
        print(_json_text(remote_status(args.output_root)), end="")
        return 0
    if args.command == "guest-stop":
        print(_json_text(guest_stop(args.output_root)), end="")
        return 0
    if args.command == "safe-export":
        print(_json_text(build_safe_export(args.output_root, args.allowlist, args.archive)), end="")
        return 0
    if args.command == "launch-detached":
        print(_json_text(launch_remote_detached(args.bundle_root, args.output_root, args.image_reference, args.image_digest)), end="")
        return 0
    if args.command == "build-frozen-bundle":
        print(_json_text(build_frozen_bundle(args.repository_root, args.output, args.image_digest)), end="")
        return 0
    if args.command == "finalize-preparation":
        print(_json_text(finalize_preparation(args.repository_root, args.synthetic_receipt)), end="")
        return 0
    if args.command == "validate-sha256s":
        print(_json_text(validate_complete_sha256s(args.directory)), end="")
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
