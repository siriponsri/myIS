"""Mirror the A1.2 CPU preflight receipt and safe result into MLflow.

Only the canonical aggregate receipt and a scanner-safe projection are mirrored.
This script never opens Owner-local inputs and never sends model or protected
payloads to MLflow.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from myis_research.kernel.canonical import canonical_sha256
from myis_research.mlflow_mirror import (
    ARMINDEX_EXPERIMENT,
    MLflowMirror,
    MirrorArtifact,
    MirrorKind,
    MirrorSpec,
    MirrorStage,
)


SCHEMA_VERSION = "myis.armindex-a1.2-preflight-mlflow-registration.v1"
RECEIPT_PATH = Path("outputs/audits/armindex/a1.2-owner-local-preflight-20260806.json")
SAFE_PROJECTION_PATH = Path("outputs/audits/armindex/a1.2-owner-local-preflight-mlflow-safe.json")
REGISTRATION_PATH = Path("outputs/audits/armindex/a1.2-owner-local-preflight-mlflow-registration.json")


def _git_commit(root: Path) -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


def _write_once(path: Path, payload: dict[str, Any]) -> None:
    encoded = (json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_bytes() != encoded:
            raise ValueError(f"immutable registration drifted: {path}")
        return
    with path.open("xb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())


def _safe_projection(receipt: dict[str, Any]) -> dict[str, Any]:
    owner = receipt.get("owner_input", {}) if isinstance(receipt.get("owner_input"), dict) else {}
    safe = {
        "schema_version": "myis.armindex-a1.2-preflight-mlflow-safe.v1",
        "receipt_id": receipt["receipt_id"],
        "source_receipt_sha256": receipt["receipt_sha256"],
        "phase_id": receipt["phase_id"],
        "task_id": receipt["task_id"],
        "status": receipt["status"],
        "evidence_class": receipt["evidence_class"],
        "scientific_authority": False,
        "cpu_only": True,
        "launch_ready": False,
        "measured_execution": False,
        "protected_data_opened": False,
        "sensitive_material_opened": False,
        "gpu_reserved": False,
        "charged_usd": 0,
        "real_counters": dict(receipt["real_counters"]),
        "resource_counters": dict(receipt["resource_counters"]),
        "blocker_count": len(receipt.get("blockers", [])),
        "owner_root_supplied": bool(owner.get("owner_root_supplied", False)),
        "canonical_bindings": dict(receipt["canonical_bindings"]),
        "claim_boundary": receipt["claim_boundary"],
        "safe_pointers": [RECEIPT_PATH.as_posix()],
    }
    safe["projection_sha256"] = canonical_sha256(safe)
    return safe


def register(repository_root: Path, store_root: Path) -> dict[str, Any]:
    root = repository_root.resolve(strict=True)
    store = store_root.resolve()
    if store == root or root in store.parents:
        raise ValueError("MLflow store must be outside the repository")
    receipt_path = root / RECEIPT_PATH
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    safe = _safe_projection(receipt)
    safe_path = root / SAFE_PROJECTION_PATH
    _write_once(safe_path, safe)
    # The canonical receipt remains the source of truth but contains explicit
    # boundary booleans whose field names are intentionally rejected by the
    # MLflow content scanner.  Mirror only the scanner-safe projection and bind
    # the canonical receipt by hash.
    artifacts = (MirrorArtifact.from_path(safe_path, kind=MirrorKind.RESULT, canonical_root=root),)
    mirror = MLflowMirror(store)
    mirrored = mirror.sync(
        MirrorSpec(
            stage=MirrorStage.A1_BASELINES_AND_MULTI_ARM_SCREENING,
            experiment_name=ARMINDEX_EXPERIMENT,
            run_name="a1.2-owner-local-preflight-20260806",
            run_id="a1.2-owner-local-preflight-20260806",
            git_commit=_git_commit(root),
            canonical_source_sha256=receipt["receipt_sha256"],
            campaign_id="armindex-multiretriever-v2",
            phase="A1_BASELINES_AND_MULTI_ARM_SCREENING",
            data_role="engineering_preflight",
            tags={
                "run_type": "owner_local_preflight",
                "evidence_class": "engineering_preflight",
                "scientific_authority": "false",
                "measured_execution": "false",
                "protected_data_opened": "false",
                "gpu_reserved": "false",
                "preflight_status": receipt["status"],
            },
            parameters={
                "blocker_count": len(receipt.get("blockers", [])),
                "measured_runs": 0,
                "candidate_count": 0,
                "selection_accesses": 0,
                "final_accesses": 0,
                "charged_usd": 0,
            },
            metrics={},
        ),
        artifacts,
    )
    if mirrored.status not in {"synced", "already_synced"} or not mirrored.mlflow_run_id:
        raise RuntimeError(f"MLflow registration failed: {mirrored.status}")
    registration = {
        "schema_version": SCHEMA_VERSION,
        "status": "registered",
        "evidence_class": "engineering_preflight",
        "scientific_authority": False,
        "source_receipt_uri": RECEIPT_PATH.as_posix(),
        "source_receipt_sha256": receipt["receipt_sha256"],
        "safe_projection_uri": SAFE_PROJECTION_PATH.as_posix(),
        "safe_projection_sha256": safe["projection_sha256"],
        "experiment": ARMINDEX_EXPERIMENT,
        "mlflow_run_id": mirrored.mlflow_run_id,
        "mirror_key": mirrored.mirror_key,
        "protected_artifacts_mirrored": False,
        "credential_material_mirrored": False,
    }
    registration["registration_sha256"] = canonical_sha256(registration)
    _write_once(root / REGISTRATION_PATH, registration)
    return registration


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--store-root", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(register(args.repository_root, args.store_root), ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
