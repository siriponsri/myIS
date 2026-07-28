"""Atomic immutable manifest finalization and MLflow receipt handling."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import ArtifactRecord, RunSpec, dataclass_dict, is_sha256


MANIFEST_V2 = "myis.run-manifest.v2"
MANIFEST_V3 = "myis.run-manifest.v3"


MIME_BY_SUFFIX = {
    ".json": "application/json",
    ".jsonl": "application/x-ndjson",
    ".csv": "text/csv",
    ".md": "text/markdown",
}


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def atomic_write_once(path: Path, value: Any) -> str:
    if path.exists():
        raise FileExistsError(f"immutable artifact already exists: {path}")
    payload = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            raise FileExistsError(f"immutable artifact already exists: {path}") from None
        except OSError as error:
            raise RuntimeError("no-overwrite link is required for immutable artifacts") from error
    finally:
        if temporary.exists():
            temporary.unlink()
    return hashlib.sha256(payload).hexdigest()


def artifact_records(run_dir: Path) -> list[ArtifactRecord]:
    records = []
    for path in sorted(run_dir.iterdir(), key=lambda item: item.name):
        if not path.is_file() or path.name == "manifest.json":
            continue
        records.append(
            ArtifactRecord.from_path(
                run_dir,
                path,
                role=path.stem.replace("_", "-"),
                mime_type=MIME_BY_SUFFIX.get(path.suffix.lower(), "application/octet-stream"),
            )
        )
    return records


def finalize_manifest(
    run_dir: Path,
    spec: RunSpec,
    *,
    status: str,
    started_at_utc: str,
    finished_at_utc: str,
    metrics: dict[str, float],
    budget_actual: dict[str, float | int],
    stop_reason: str | None,
) -> str:
    measured = not spec.phase.startswith(("offline", "bootstrap", "fixture"))
    spec.research.validate()
    if measured and spec.environment is None:
        raise ValueError("measured manifests require a locked runtime environment")
    if measured and spec.provider is None:
        raise ValueError("measured manifests require requested/resolved provider identity")
    if measured and spec.isolation is None:
        raise ValueError("measured manifests require an offline execution-isolation contract")
    if spec.environment is not None:
        spec.environment.validate()
    if spec.provider is not None:
        spec.provider.validate(measured=measured)
    if spec.replication is not None:
        spec.replication.validate()
    if spec.statistics is not None:
        spec.statistics.validate()
    if spec.surfaces is not None:
        spec.surfaces.validate()
    if spec.isolation is not None:
        spec.isolation.validate()
    if spec.candidate_pool is not None:
        spec.candidate_pool.validate()
    invalid_declared = sorted(name for name, value in spec.artifact_hashes.items() if not is_sha256(value))
    if invalid_declared:
        raise ValueError(f"declared artifacts require SHA-256 hashes: {invalid_declared}")
    records = artifact_records(run_dir)
    manifest = {
        "schema_version": MANIFEST_V3,
        "identity": {
            "research": dataclass_dict(spec.research),
            "run_id": spec.run_id,
            "goal_id": spec.goal.goal_id,
            "parent_run_id": spec.parent_run_id,
            "trial_id": spec.trial_id,
            "arm": spec.arm,
            "phase": spec.phase,
        },
        "lifecycle": {
            "started_at_utc": started_at_utc,
            "finished_at_utc": finished_at_utc,
            "status": status,
            "stop_reason": stop_reason,
        },
        "approval": dataclass_dict(spec.approval),
        "code": {
            "repository": spec.repository,
            "git_commit": spec.git_commit,
            "dirty": spec.git_dirty,
        },
        "method": {
            "kernel_version": spec.kernel_version,
            "policy_hash": spec.policy_hash,
            "config_hash": spec.config_hash,
            "prompt_hash": spec.prompt_hash,
            "skill_set_hash": spec.skill_set_hash,
            "model_id": spec.model_id,
            "module_pool_hash": spec.module_pool_hash,
            "provider": dataclass_dict(spec.provider) if spec.provider else None,
        },
        "inputs": {
            "dataset_id": spec.dataset_id,
            "dataset_manifest_hash": spec.dataset_manifest_hash,
            "split": spec.split,
            "split_query_ids_hash": spec.split_query_ids_hash,
            "seed": spec.seed,
        },
        "evaluator": {"evaluator_id": spec.evaluator_id, "hash": spec.evaluator_hash, "immutable": True},
        "environment": dataclass_dict(spec.environment) if spec.environment else None,
        "replication": dataclass_dict(spec.replication) if spec.replication else None,
        "statistics": dataclass_dict(spec.statistics) if spec.statistics else None,
        "surfaces": dataclass_dict(spec.surfaces) if spec.surfaces else None,
        "isolation": dataclass_dict(spec.isolation) if spec.isolation else None,
        "candidate_pool": dataclass_dict(spec.candidate_pool) if spec.candidate_pool else None,
        "declared_artifact_hashes": dict(sorted(spec.artifact_hashes.items())),
        "budget": {"limits": spec.budget, "actual": budget_actual},
        "metrics": {"summary_exact": metrics, "definition_version": "myis.retrieval-metrics.v1"},
        "artifacts": [dataclass_dict(record) for record in records],
        "validation": {
            "schema": "PASS",
            "hashes": "PASS_AT_FINALIZE",
            "split_leakage": "PASS_BY_PREFLIGHT",
            "determinism": "FIXED_SEED_DECLARED",
        },
        "retention": {"class": "research-run", "automatic_delete": False},
        "redaction_policy_version": "myis.redaction.v1",
    }
    return atomic_write_once(run_dir / "manifest.json", manifest)


def write_mlflow_receipt(run_dir: Path, payload: dict[str, Any]) -> Path:
    receipts = run_dir / "receipts"
    receipts.mkdir(exist_ok=True)
    receipt_id = payload.get("receipt_id") or "initial"
    path = receipts / f"mlflow-{receipt_id}.json"
    body = {
        "schema_version": "myis.mlflow-receipt.v1",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    atomic_write_once(path, body)
    return path
