"""Bootstrap the governed local MLflow mirror without scientific data."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from myis_research.mlflow_mirror import MLflowMirror, MirrorSpec, MirrorStage, default_store


REPO_ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP_CONFIG = REPO_ROOT / "03_experiments" / "config" / "mlflow" / "bootstrap.yaml"


def _git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def main() -> int:
    store_root = default_store()
    source_hash = hashlib.sha256(BOOTSTRAP_CONFIG.read_bytes()).hexdigest()
    receipt = MLflowMirror(store_root).sync(
        MirrorSpec(
            stage=MirrorStage.BOOTSTRAP,
            run_name="is1-v0.1-store-connectivity",
            git_commit=_git_commit(),
            canonical_source_sha256=source_hash,
            tags={
                "scientific_run": "false",
                "dataset_access": "none",
            },
            parameters={
                "purpose": "tracking-store connectivity only",
                "artifact_count": 0,
                "scientific_metric_count": 0,
            },
            metrics={},
        )
    )
    report = {
        "schema_version": "myis.mlflow-bootstrap-report.v2",
        "status": "PASS" if receipt.status in {"synced", "already_synced"} else "DEFERRED",
        "stage": "bootstrap",
        "scientific_run": False,
        "dataset_access": "none",
        "artifact_count": 0,
        "scientific_metric_count": 0,
        "store_root": str(store_root),
        "experiment_name": receipt.experiment_name,
        "mlflow_run_id": receipt.mlflow_run_id,
        "mirror_key": receipt.mirror_key,
        "receipt_status": receipt.status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    report_path = store_root / "mlflow-bootstrap.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
