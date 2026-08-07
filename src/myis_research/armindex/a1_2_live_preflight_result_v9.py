"""Canonical additive receipt for the completed A1.2 v9 synthetic preflight.

The execution-lifecycle receipt remains immutable historical preparation
evidence.  This module materializes a separate aggregate-only result receipt
from the Owner-local safe-export facts after the live synthetic run has
completed.  It never opens a provider connection and never changes scientific
authorization or counters.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a1_2_live_preflight_execution_v9 import (
    CONTRACT_PATH as V9_CONTRACT_PATH,
    RECEIPT_PATH as V9_RECEIPT_PATH,
    validate_revision as validate_v9,
)


REVISION_ID = "a1.2-live-synthetic-preflight-result-v9"
RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-live-synthetic-preflight-result.receipt.v9.json"
)
SCHEMA_PATH = Path("schemas/armindex/a1.2-live-synthetic-preflight-result.v9.json")
ATTEMPT_ID = "a12-v9-20260807-06"
IMAGE_REFERENCE = "pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime"
IMAGE_MANIFEST_DIGEST = "sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20"
GIT_COMMIT = "1cdff09343121b26cda968263d6a83cb403fba28"
GIT_TREE = "701b6c2bc1596334637d7c096ac50c4914936ebc"
BUNDLE_SHA256 = "e8c980f312f07b04ba6b5972f2098d95ee64ec92b7316f620a8a9c09538f439c"
VERIFICATION_MARKER_SHA256 = "a5ca248198724a9a10fee85d4e080b106f6f0efac981bb958f4ecb33878b5a10"
SUMMARY_SHA256 = "b82c364dba14a9385e848259f6d878cf2e4d7ff0b7ebbb77ee6b74b3acff0236"
SAFE_EXPORT_ARCHIVE_SHA256 = "92d24af6b24cf99e176ad23a5f3eec22478b8485f3a8770269640dcb423047a6"
SAFE_EXPORT_MEMBERS_SHA256 = "0fcf3b00a5ae3cdbfcaa18c95fc7be6ed6566ad7e14f6af7e8cafd7627dbb3b7"
TEARDOWN_SHA256 = "94b5d32414f5bd9e41e56c453263fff9b31fadc2338b2aae438c8b98c4ded0ae"
GPU_UUID_SET_SHA256 = "7b670e2c35f9ce93731ab13b3d82f4810d16df7d9e0d7885e7f47f958718027a"

_ARM_FACTS: tuple[dict[str, Any], ...] = (
    {
        "arm_id": "ARM-02",
        "cuda_visible_devices": "0",
        "status": "PASS",
        "adapter_receipt_sha256": "4de9210e97228620a202df5b733a3b6bccaa0fbde46d3643e1a61e3b90be893d",
        "worker_receipt_sha256": "a223c443b9dd37ad89d0afe0a0ef54ff7a84c3dfc42e2253fc6fdf7a8f234552",
        "model_manifest_sha256": "421aca4aa39d42e24ecec6f615b1e21a6c08f9ea85f8c91c6fa7de77be9f14fa",
        "output_dimension": 1024,
        "peak_vram_bytes": 1145933824,
    },
    {
        "arm_id": "ARM-03",
        "cuda_visible_devices": "1",
        "status": "PASS",
        "adapter_receipt_sha256": "67f5c374f82a475866a08d2be5f458b61a88ae745fc39046e0832965998a4e4b",
        "worker_receipt_sha256": "6f7d089bdc6f42ea7a6b90a713722ddf49ad484410a294147899557a88d28b01",
        "model_manifest_sha256": "0070947e7621ea3247e02e2bb5aa27caa72ebe9fb36cd1256139715b99f1343e",
        "output_dimension": 1024,
        "peak_vram_bytes": 699831808,
    },
    {
        "arm_id": "ARM-04",
        "cuda_visible_devices": "2",
        "status": "PASS",
        "adapter_receipt_sha256": "b91cfd112da14af4888207af8f42065e35f39b064fb91eef70890c1df8bc9b00",
        "worker_receipt_sha256": "571669dbddc6f49a397e2df66116e5724fd49340b99417bdce76750203e45d71",
        "model_manifest_sha256": "d2f14a2fd821e40fd5fbe714973b2f9450ff28b886e34d3de604b21317fd95bb",
        "output_dimension": 768,
        "peak_vram_bytes": 629110272,
    },
    {
        "arm_id": "ARM-05",
        "cuda_visible_devices": "3",
        "status": "PASS",
        "adapter_receipt_sha256": "3cbfc95f260b6dac910abce1bd41ca13ae61f9face23baa7d6d6ef01cf33c44e",
        "worker_receipt_sha256": "ebdb3fcb64207f4e711f6297a55ec9cf5ee756d9935246b53a5cf7fbdf81a482",
        "model_manifest_sha256": "0faade000cb4967cce1f16b8f7e1ed9e8368daea0d023f6ac24462a78d5fabef",
        "output_dimension": 1024,
        "peak_vram_bytes": 5982380544,
    },
)


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _git_identity(root: Path) -> tuple[str, str]:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    tree = subprocess.check_output(["git", "show", "-s", "--format=%T", "HEAD"], cwd=root, text=True).strip()
    return commit, tree


def _receipt_body(
    root: Path, *, require_attempt_git_identity: bool = True
) -> dict[str, Any]:
    validate_v9(root)
    if require_attempt_git_identity:
        commit, tree = _git_identity(root)
        if (commit, tree) != (GIT_COMMIT, GIT_TREE):
            raise ValueError("live result must be materialized at the verified attempt commit/tree")
    body: dict[str, Any] = {
        "schema_version": "myis.armindex-a1.2-live-synthetic-preflight-result.v9",
        "receipt_id": REVISION_ID,
        "revision_id": REVISION_ID,
        "status": "PASS",
        "evidence_class": "live_engineering_synthetic_preflight",
        "scientific_authority": False,
        "claim_boundary": (
            "Engineering-only synthetic adapter and lifecycle evidence on one Vast "
            "4xRTX3090 instance; no retrieval-quality, publication, or general workload claim."
        ),
        "attempt_id": ATTEMPT_ID,
        "identity": {
            "git_commit": GIT_COMMIT,
            "git_tree": GIT_TREE,
            "bundle_sha256": BUNDLE_SHA256,
            "image_reference": IMAGE_REFERENCE,
            "resolved_manifest_digest": IMAGE_MANIFEST_DIGEST,
            "verification_marker_sha256": VERIFICATION_MARKER_SHA256,
        },
        "provider": {
            "provider_label": "Vast",
            "instance_id": "47023328",
            "quote_usd_per_hour": 0.656,
            "hard_stop_fit": True,
            "gpu_count": 4,
            "gpu_model": "NVIDIA GeForce RTX 3090",
            "vram_mib_each": 24576,
            "gpu_uuid_set_sha256": GPU_UUID_SET_SHA256,
            "cpu_count": 64,
            "ram_bytes": 117996920832,
            "disk_total_bytes": 268435456000,
            "image_identity_observation": "runtime_anchors_only_expected_manifest_bound_locally",
        },
        "arms": [dict(item) for item in _ARM_FACTS],
        "qwen": {
            "arm_id": "ARM-05",
            "adapter_path": "sentence_transformer_encode",
            "declared_max_input_tokens": 32768,
            "measured_adapter_max_input_tokens": 32768,
            "candidate_safe_max_input_tokens": 32768,
            "candidate_tokens_passed": [8192, 16384, 32768],
            "peak_allocated_vram_bytes": 5982380544,
            "first_oom_adapter_input_tokens": None,
            "measurement_scope": "single RTX 3090, FP16, batch size one, frozen v9 runtime/model",
        },
        "lifecycle": {
            "checkpoint_resume": "PASS",
            "injected_failure": "EXPECTED_FAILURE",
            "guest_process_teardown": "PASS",
            "teardown_receipt_sha256": TEARDOWN_SHA256,
            "safe_export_archive_sha256": SAFE_EXPORT_ARCHIVE_SHA256,
            "safe_export_members_sha256": SAFE_EXPORT_MEMBERS_SHA256,
            "safe_export_member_count": 72,
            "provider_destruction_proven": False,
        },
        "source_bindings": [
            {"uri": "owner-store/a1.2-vast-20260806/return/a12-v9-20260807-06/summary.json", "sha256": SUMMARY_SHA256},
            {"uri": "owner-store/a1.2-vast-20260806/return/a12-v9-20260807-06/safe-export-members.v9.json", "sha256": SAFE_EXPORT_MEMBERS_SHA256},
            {"uri": "owner-store/a1.2-vast-20260806/return/a12-v9-20260807-06/teardown.json", "sha256": TEARDOWN_SHA256},
            {"uri": "owner-store/a1.2-vast-20260806/return/a12-v9-20260807-06/safe-export.tar.gz", "sha256": SAFE_EXPORT_ARCHIVE_SHA256},
        ],
        "pending_live_checks": [
            "provider destruction or policy-valid continuation disposition",
            "Owner-local TTL watchdog and provider absence proof",
        ],
        "owner_disposition": "pending_owner_policy_decision",
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
        "selection_accesses": 0,
        "final_accesses": 0,
        "charged_usd": 0,
        "next_authorized_action": (
            "Owner may destroy and verify provider absence, or explicitly authorize "
            "continue_next_goal_on_PLAN only while the continuation policy requirements remain true."
        ),
    }
    body["v9_contract_sha256"] = file_sha256(root / V9_CONTRACT_PATH)
    body["v9_preparation_receipt_sha256"] = file_sha256(root / V9_RECEIPT_PATH)
    return body


def _validate_receipt_payload(
    receipt: Mapping[str, Any], schema: Mapping[str, Any]
) -> None:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(receipt),
        key=lambda item: list(item.path),
    )
    if errors:
        raise ValueError(f"live result schema failure: {errors[0].message}")
    if receipt.get("receipt_sha256") != canonical_sha256(
        {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    ):
        raise ValueError("live result self-hash mismatch")
    assert_aggregate_only(receipt)


def _validate_expected_receipt(root: Path, receipt: Mapping[str, Any]) -> None:
    expected = _receipt_body(root, require_attempt_git_identity=False)
    observed = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    if observed != expected:
        raise ValueError("live result payload differs from the frozen attempt facts")


def materialize_result(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    body = _receipt_body(root)
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    schema = json.loads((root / SCHEMA_PATH).read_text(encoding="utf-8"))
    _validate_receipt_payload(receipt, schema)
    target = root / RECEIPT_PATH
    if target.exists() and target.read_text(encoding="utf-8") != _json_text(receipt):
        raise ValueError(f"immutable live result differs: {RECEIPT_PATH.as_posix()}")
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_json_text(receipt), encoding="utf-8", newline="")
    return validate_result(root)


def validate_result(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    validate_v9(root)
    receipt = json.loads((root / RECEIPT_PATH).read_text(encoding="utf-8"))
    schema = json.loads((root / SCHEMA_PATH).read_text(encoding="utf-8"))
    _validate_receipt_payload(receipt, schema)
    _validate_expected_receipt(root, receipt)
    if receipt.get("v9_contract_sha256") != file_sha256(root / V9_CONTRACT_PATH):
        raise ValueError("live result v9 contract binding mismatch")
    if receipt.get("v9_preparation_receipt_sha256") != file_sha256(root / V9_RECEIPT_PATH):
        raise ValueError("live result v9 preparation receipt binding mismatch")
    return {
        "status": receipt["status"],
        "revision_id": receipt["revision_id"],
        "receipt_sha256": file_sha256(root / RECEIPT_PATH),
        "receipt_self_sha256": receipt["receipt_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-live-preflight-result-v9")
    parser.add_argument("command", choices=("materialize", "validate"))
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    args = parser.parse_args()
    result = materialize_result(args.repository_root) if args.command == "materialize" else validate_result(args.repository_root)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
