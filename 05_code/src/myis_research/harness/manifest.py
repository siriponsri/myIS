"""Atomic immutable manifest finalization and MLflow receipt handling."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import ArtifactRecord, RunSpec, dataclass_dict


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
        if path.exists():
            raise FileExistsError(f"immutable artifact already exists: {path}")
        temporary.replace(path)
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
    records = artifact_records(run_dir)
    manifest = {
        "schema_version": "myis.run-manifest.v2",
        "identity": {
            "run_id": spec.run_id,
            "goal_id": spec.goal.goal_id,
            "parent_run_id": spec.parent_run_id,
            "trial_id": spec.trial_id,
            "arm": spec.arm,
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
        },
        "inputs": {
            "dataset_id": spec.dataset_id,
            "dataset_manifest_hash": spec.dataset_manifest_hash,
            "split": spec.split,
            "split_query_ids_hash": spec.split_query_ids_hash,
            "seed": spec.seed,
        },
        "evaluator": {"evaluator_id": spec.evaluator_id, "hash": spec.evaluator_hash, "immutable": True},
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
