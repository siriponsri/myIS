"""Read-only validation for an append-only myIS MLflow bootstrap record."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from myis_research.mlflow_mirror import (
    DISPLAY_NAME,
    PROGRAM_ID,
    PROTOCOL_VERSION,
    RECEIPT_SCHEMA,
    RESEARCH_VERSION,
    _assert_store_outside_git,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPORT_SCHEMA = "myis.mlflow-bootstrap-report.v3"


class BootstrapValidationError(RuntimeError):
    """Raised when a bootstrap record cannot prove its governed boundary."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_head(repository_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _read_object(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise BootstrapValidationError(f"expected a regular file: {path.name}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BootstrapValidationError(f"invalid JSON: {path.name}") from error
    if not isinstance(value, dict):
        raise BootstrapValidationError(f"expected a JSON object: {path.name}")
    return value


def _report_path(store_root: Path, git_commit: str, mirror_key: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{40}", git_commit):
        raise BootstrapValidationError("Git commit must be a full lowercase SHA-1")
    if not re.fullmatch(r"[0-9a-f]{64}", mirror_key):
        raise BootstrapValidationError("mirror key must be SHA-256")
    return store_root / "bootstrap-reports" / f"mlflow-bootstrap-{git_commit}-{mirror_key}.json"


def _validate_report(report: dict[str, Any], store_root: Path, expected_commit: str) -> None:
    expected = {
        "schema_version": REPORT_SCHEMA,
        "status": "PASS",
        "stage": "bootstrap",
        "program_id": PROGRAM_ID,
        "display_name": DISPLAY_NAME,
        "protocol_version": PROTOCOL_VERSION,
        "research_version": RESEARCH_VERSION,
        "git_commit": expected_commit,
        "scientific_run": False,
        "dataset_access": "none",
        "artifact_count": 0,
        "scientific_metric_count": 0,
        "store_root": str(store_root),
        "experiment_name": "myis-research-bootstrap",
    }
    mismatches = [key for key, value in expected.items() if report.get(key) != value]
    if mismatches:
        raise BootstrapValidationError(f"bootstrap report mismatch: {', '.join(mismatches)}")
    if not isinstance(report.get("mlflow_run_id"), str) or not report["mlflow_run_id"]:
        raise BootstrapValidationError("bootstrap report has no MLflow run ID")
    if not isinstance(report.get("recorded_at_utc"), str) or not report["recorded_at_utc"]:
        raise BootstrapValidationError("bootstrap report has no recorded timestamp")


def _validate_receipt(receipt: dict[str, Any], report: dict[str, Any]) -> None:
    expected = {
        "schema_version": RECEIPT_SCHEMA,
        "receipt_id": report["mirror_key"],
        "mirror_key": report["mirror_key"],
        "experiment_name": "myis-research-bootstrap",
        "mlflow_run_id": report["mlflow_run_id"],
    }
    mismatches = [key for key, value in expected.items() if receipt.get(key) != value]
    if mismatches:
        raise BootstrapValidationError(f"bootstrap receipt mismatch: {', '.join(mismatches)}")
    if receipt.get("status") not in {"synced", "already_synced"}:
        raise BootstrapValidationError("bootstrap receipt is not complete")
    if receipt.get("artifact_hashes") != {}:
        raise BootstrapValidationError("bootstrap receipt contains artifacts")


def _validate_run_metadata(database: Path, report: dict[str, Any]) -> None:
    uri = f"file:{database.resolve().as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        row = connection.execute(
            "SELECT e.name FROM runs r JOIN experiments e ON e.experiment_id = r.experiment_id "
            "WHERE r.run_uuid = ?",
            (report["mlflow_run_id"],),
        ).fetchone()
        if row != ("myis-research-bootstrap",):
            raise BootstrapValidationError("bootstrap MLflow run is absent or has the wrong experiment")
        tags = dict(connection.execute("SELECT key, value FROM tags WHERE run_uuid = ?", (report["mlflow_run_id"],)))
        parameters = dict(
            connection.execute("SELECT key, value FROM params WHERE run_uuid = ?", (report["mlflow_run_id"],))
        )
        metrics = connection.execute("SELECT COUNT(*) FROM metrics WHERE run_uuid = ?", (report["mlflow_run_id"],)).fetchone()
    except sqlite3.Error as error:
        raise BootstrapValidationError("MLflow database cannot provide bootstrap metadata") from error
    finally:
        connection.close()
    expected_tags = {
        "program_id": PROGRAM_ID,
        "display_name": DISPLAY_NAME,
        "protocol_version": PROTOCOL_VERSION,
        "research_version": RESEARCH_VERSION,
        "stage": "bootstrap",
        "mirror_key": report["mirror_key"],
        "git_commit": report["git_commit"],
        "scientific_run": "false",
        "dataset_access": "none",
    }
    mismatches = [key for key, value in expected_tags.items() if tags.get(key) != value]
    if mismatches:
        raise BootstrapValidationError(f"bootstrap MLflow tag mismatch: {', '.join(mismatches)}")
    if parameters.get("artifact_count") != "0" or parameters.get("scientific_metric_count") != "0":
        raise BootstrapValidationError("bootstrap MLflow parameters are not zero-only")
    if metrics != (0,):
        raise BootstrapValidationError("bootstrap MLflow run contains metrics")


def validate(store_root: Path, repository_root: Path = REPOSITORY_ROOT) -> dict[str, object]:
    root = _assert_store_outside_git(store_root.resolve(strict=True))
    if not root.is_dir() or root.is_symlink():
        raise BootstrapValidationError("MLflow store must be a regular directory")
    database = root / "database" / "mlflow.db"
    artifacts = root / "artifacts"
    if not database.is_file() or database.read_bytes()[:16] != b"SQLite format 3\x00":
        raise BootstrapValidationError("MLflow database is missing or invalid")
    if not artifacts.is_dir() or artifacts.is_symlink():
        raise BootstrapValidationError("MLflow artifacts directory is missing or unsafe")
    git_commit = _git_head(repository_root.resolve(strict=True))
    candidates = sorted((root / "bootstrap-reports").glob(f"mlflow-bootstrap-{git_commit}-*.json"))
    if len(candidates) != 1:
        raise BootstrapValidationError("expected exactly one append-only bootstrap report for current HEAD")
    before = _sha256(database)
    report = _read_object(candidates[0])
    _validate_report(report, root, git_commit)
    expected_path = _report_path(root, git_commit, str(report.get("mirror_key", "")))
    if candidates[0] != expected_path:
        raise BootstrapValidationError("bootstrap report filename does not bind its Git commit and mirror key")
    receipt = _read_object(root / "receipts" / "mlflow" / f"mlflow-mirror-{report['mirror_key']}.json")
    _validate_receipt(receipt, report)
    _validate_run_metadata(database, report)
    after = _sha256(database)
    if before != after:
        raise BootstrapValidationError("read-only bootstrap validation changed the MLflow database")
    return {
        "status": "PASS",
        "store_root": str(root),
        "git_commit": git_commit,
        "report_path": str(candidates[0]),
        "mlflow_run_id": report["mlflow_run_id"],
        "mirror_key": report["mirror_key"],
        "scientific_run": False,
        "dataset_access": "none",
        "artifact_count": 0,
        "scientific_metric_count": 0,
        "database_sha256": before,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True, help="approved external MLflow store")
    parser.add_argument("--repository-root", type=Path, default=REPOSITORY_ROOT)
    arguments = parser.parse_args()
    try:
        print(json.dumps(validate(arguments.store, arguments.repository_root), ensure_ascii=True, indent=2, sort_keys=True))
    except BootstrapValidationError as error:
        print(f"FAIL: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
