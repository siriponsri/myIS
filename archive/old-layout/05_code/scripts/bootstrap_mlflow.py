"""Bootstrap the governed local MLflow mirror without scientific data."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

from myis_research.mlflow_mirror import (
    DISPLAY_NAME,
    PROGRAM_ID,
    PROTOCOL_VERSION,
    RESEARCH_VERSION,
    MLflowMirror,
    MirrorReceipt,
    MirrorSpec,
    MirrorStage,
    default_store,
)


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


def _bootstrap_report_path(store_root: Path, git_commit: str, mirror_key: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{40}", git_commit):
        raise ValueError("bootstrap report requires a full lowercase Git commit")
    if not re.fullmatch(r"[0-9a-f]{64}", mirror_key):
        raise ValueError("bootstrap report requires a SHA-256 mirror key")
    return store_root / "bootstrap-reports" / f"mlflow-bootstrap-{git_commit}-{mirror_key}.json"


def _bootstrap_report(store_root: Path, git_commit: str, receipt: MirrorReceipt) -> dict[str, object]:
    if receipt.experiment_name != "myis-research-bootstrap":
        raise RuntimeError("bootstrap receipt has an unexpected MLflow experiment")
    if receipt.status not in {"synced", "already_synced"}:
        raise RuntimeError("bootstrap receipt did not complete")
    if receipt.artifact_hashes:
        raise RuntimeError("bootstrap receipt must not contain artifacts")
    return {
        "schema_version": "myis.mlflow-bootstrap-report.v3",
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
        "store_root": str(store_root.resolve()),
        "experiment_name": receipt.experiment_name,
        "mlflow_run_id": receipt.mlflow_run_id,
        "mirror_key": receipt.mirror_key,
        "receipt_status": receipt.status,
        "recorded_at_utc": receipt.recorded_at_utc,
    }


def _write_report_once(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        with path.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        if path.read_bytes() != payload:
            raise RuntimeError("conflicting immutable MLflow bootstrap report already exists")


def bootstrap(store_root: Path | None = None) -> dict[str, object]:
    resolved_store = default_store(store_root)
    git_commit = _git_commit()
    source_hash = hashlib.sha256(BOOTSTRAP_CONFIG.read_bytes()).hexdigest()
    receipt = MLflowMirror(resolved_store).sync(
        MirrorSpec(
            stage=MirrorStage.BOOTSTRAP,
            run_name="myis-research-v0.1-store-connectivity",
            git_commit=git_commit,
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
    if receipt.status not in {"synced", "already_synced"}:
        return {
            "schema_version": "myis.mlflow-bootstrap-report.v3",
            "status": "DEFERRED",
            "stage": "bootstrap",
            "scientific_run": False,
            "dataset_access": "none",
            "artifact_count": 0,
            "scientific_metric_count": 0,
            "store_root": str(resolved_store),
            "receipt_status": receipt.status,
            "mirror_key": receipt.mirror_key,
        }
    report = _bootstrap_report(resolved_store, git_commit, receipt)
    _write_report_once(_bootstrap_report_path(resolved_store, git_commit, receipt.mirror_key), report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap the zero-data local MLflow mirror")
    parser.add_argument("--store-root", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = bootstrap(args.store_root)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
