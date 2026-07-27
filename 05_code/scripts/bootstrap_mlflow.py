"""Create a local bootstrap-only MLflow store without scientific data."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import mlflow


REPO_ROOT = Path(__file__).resolve().parents[2]


def resolve_store_root() -> Path:
    """Resolve the persistent MLflow store outside the Git repository."""
    configured = os.environ.get("MYIS_MLFLOW_STORE")
    if configured:
        return Path(configured).expanduser().resolve()

    for ancestor in (REPO_ROOT, *REPO_ROOT.parents):
        numbered = ancestor / "01_Stores" / "00_myIS" / "mlflow"
        legacy = ancestor / "Stores" / "myIS" / "mlflow"
        if numbered.parent.is_dir():
            return numbered
        if legacy.parent.is_dir():
            return legacy
    raise RuntimeError(
        "Cannot locate the workspace MLflow store; set MYIS_MLFLOW_STORE"
    )


def main() -> int:
    store_root = resolve_store_root()
    database_dir = store_root / "database"
    artifacts = store_root / "artifacts"
    database = database_dir / "mlflow.db"
    database_dir.mkdir(parents=True, exist_ok=True)
    artifacts.mkdir(parents=True, exist_ok=True)
    tracking_uri = f"sqlite:///{database.as_posix()}"
    mlflow.set_tracking_uri(tracking_uri)

    experiment = mlflow.get_experiment_by_name("myis-bootstrap")
    if experiment is None:
        experiment_id = mlflow.create_experiment(
            "myis-bootstrap", artifact_location=artifacts.resolve().as_uri()
        )
    else:
        experiment_id = experiment.experiment_id

    with mlflow.start_run(
        experiment_id=experiment_id,
        run_name="restructure-smoke",
        tags={
            "project": "myIS Research",
            "stage": "bootstrap",
            "scientific_run": "false",
            "dataset_access": "none",
            "owner_approval_source": "owner restructure implementation 2026-07-26",
        },
    ) as run:
        mlflow.log_param("mlflow_version", mlflow.__version__)
        mlflow.log_param("purpose", "tracking-store connectivity only")
        run_id = run.info.run_id

    report = {
        "status": "PASS",
        "stage": "bootstrap",
        "scientific_run": False,
        "dataset_access": "none",
        "tracking_uri": tracking_uri,
        "experiment_id": experiment_id,
        "run_id": run_id,
        "mlflow_version": mlflow.__version__,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    report_path = store_root / "mlflow-bootstrap.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
