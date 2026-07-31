"""Create the zero-data MLflow registry used by the local projections.

Bootstrap is a connectivity receipt only. It creates the active campaign and
system experiments while preserving pre-v2 experiments as legacy_read_only.
It never reads protected research inputs or records scientific metrics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

from myis_research.mlflow_mirror import (
    DISPLAY_NAME,
    EXPERIMENTS,
    MLflowMirror,
    MirrorReceipt,
    MirrorSpec,
    MirrorStage,
    PROGRAM_ID,
    PROTOCOL_VERSION,
    RESEARCH_VERSION,
    SYSTEM_EXPERIMENT,
    default_store,
)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git_commit(root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _write_once(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        with path.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        if path.read_bytes() != data:
            raise RuntimeError(f"immutable bootstrap report drifted: {path}")


def _write_bootstrap_report(store: Path, report: dict[str, object]) -> Path:
    primary = store / "mlflow-bootstrap.json"
    data = (json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if not primary.exists():
        _write_once(primary, report)
        return primary
    if primary.read_bytes() == data:
        return primary
    versioned = store / "mlflow-bootstrap-v2.json"
    _write_once(versioned, report)
    return versioned


def bootstrap(store_root: Path | None = None, *, repository_root: Path | None = None) -> dict[str, object]:
    root = (repository_root or _repository_root()).resolve(strict=True)
    store = default_store(store_root)
    git_commit = _git_commit(root)
    source = root / "control" / "campaigns" / "scope-autoindex-v1.yaml"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    receipt = MLflowMirror(store).sync(
        MirrorSpec(
            stage=MirrorStage.P0_FOUNDATION,
            experiment_name=SYSTEM_EXPERIMENT,
            run_name=f"myis-system-bootstrap-{git_commit[:12]}",
            git_commit=git_commit,
            canonical_source_sha256=source_hash,
            phase=MirrorStage.P0_FOUNDATION.value,
            data_role="bootstrap",
            campaign_id="scope-autoindex-v1",
            decision_id="D1_START_CAMPAIGN",
            tags={"scientific_run": "false", "dataset_access": "none"},
            parameters={
                "purpose": "tracking-store connectivity only",
                "experiment_count": len(EXPERIMENTS),
                "artifact_count": 0,
                "scientific_metric_count": 0,
            },
            metrics={},
        )
    )
    if receipt.status not in {"synced", "already_synced"}:
        return {"schema_version": "myis.mlflow-bootstrap-report.v2", "status": "BLOCKED", "receipt_status": receipt.status, "error_type": receipt.error_type}
    report = {
        "schema_version": "myis.mlflow-bootstrap-report.v2",
        "status": "PASS",
        "stage": "bootstrap",
        "program_id": PROGRAM_ID,
        "display_name": DISPLAY_NAME,
        "protocol_version": PROTOCOL_VERSION,
        "research_version": RESEARCH_VERSION,
        "git_commit": git_commit,
        "scientific_run": False,
        "dataset_access": "none",
        "artifact_count": 0,
        "scientific_metric_count": 0,
        "experiment_names": list(EXPERIMENTS),
        "store_root": str(store.resolve()),
        "experiment_name": receipt.experiment_name,
        "mlflow_run_id": receipt.mlflow_run_id,
        "mirror_key": receipt.mirror_key,
        "receipt_status": receipt.status,
        "recorded_at_utc": receipt.recorded_at_utc,
    }
    report_path = _write_bootstrap_report(store, report)
    metadata = {
        "schema_version": "myis.mlflow-store.v2",
        "artifact_root": "artifacts",
        "repository_program_id": PROGRAM_ID,
        "created_by": "bootstrap_mlflow.py",
    }
    metadata_path = store / "store.json"
    if metadata_path.exists():
        existing = json.loads(metadata_path.read_text(encoding="utf-8"))
        if existing.get("schema_version") != "myis.mlflow-store.v2" or existing.get("artifact_root") != "artifacts":
            raise RuntimeError("existing MLflow store metadata is invalid")
    else:
        _write_once(metadata_path, metadata)
    return {**report, "report_path": str(report_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap the zero-data local MLflow mirror")
    parser.add_argument("--store-root", type=Path)
    parser.add_argument("--repository-root", type=Path, default=_repository_root())
    args = parser.parse_args(argv)
    report = bootstrap(args.store_root, repository_root=args.repository_root)
    print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
    return 0 if report.get("status") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
