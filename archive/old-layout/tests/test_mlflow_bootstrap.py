import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from myis_research.mlflow_mirror import MirrorReceipt


REPO_ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP_PATH = REPO_ROOT / "05_code" / "scripts" / "bootstrap_mlflow.py"
VALIDATOR_PATH = REPO_ROOT / "05_code" / "scripts" / "validate_mlflow_bootstrap.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bootstrap = load_module("myis_bootstrap_mlflow", BOOTSTRAP_PATH)
validator = load_module("myis_validate_mlflow_bootstrap", VALIDATOR_PATH)

COMMIT = "a" * 40
MIRROR_KEY = "b" * 64
RUN_ID = "run-bootstrap"
SOURCE_SHA = "c" * 64


def receipt() -> MirrorReceipt:
    return MirrorReceipt(
        receipt_id=MIRROR_KEY,
        mirror_key=MIRROR_KEY,
        status="synced",
        experiment_name="myis-research-bootstrap",
        recorded_at_utc="2026-07-29T00:00:00+00:00",
        canonical_source_sha256=SOURCE_SHA,
        git_commit=COMMIT,
        artifact_hashes={},
        mlflow_run_id=RUN_ID,
    )


def make_store(root: Path) -> tuple[Path, dict[str, object]]:
    store = root / "store"
    (store / "artifacts").mkdir(parents=True)
    database = store / "database" / "mlflow.db"
    database.parent.mkdir()
    connection = sqlite3.connect(database)
    try:
        connection.execute("CREATE TABLE experiments (experiment_id INTEGER, name TEXT)")
        connection.execute("CREATE TABLE runs (run_uuid TEXT, experiment_id INTEGER)")
        connection.execute("CREATE TABLE tags (run_uuid TEXT, key TEXT, value TEXT)")
        connection.execute("CREATE TABLE params (run_uuid TEXT, key TEXT, value TEXT)")
        connection.execute("CREATE TABLE metrics (run_uuid TEXT, key TEXT)")
        connection.execute("INSERT INTO experiments VALUES (?, ?)", (1, "myis-research-bootstrap"))
        connection.execute("INSERT INTO runs VALUES (?, ?)", (RUN_ID, 1))
        tags = {
            "program_id": "myis-research",
            "display_name": "myIS Research",
            "protocol_version": "1.0",
            "research_version": "0.1",
            "stage": "bootstrap",
            "mirror_key": MIRROR_KEY,
            "git_commit": COMMIT,
            "scientific_run": "false",
            "dataset_access": "none",
        }
        connection.executemany("INSERT INTO tags VALUES (?, ?, ?)", [(RUN_ID, key, value) for key, value in tags.items()])
        connection.executemany(
            "INSERT INTO params VALUES (?, ?, ?)",
            [(RUN_ID, "artifact_count", "0"), (RUN_ID, "scientific_metric_count", "0")],
        )
        connection.commit()
    finally:
        connection.close()
    report = bootstrap._bootstrap_report(store, COMMIT, receipt())
    report_path = bootstrap._bootstrap_report_path(store, COMMIT, MIRROR_KEY)
    bootstrap._write_report_once(report_path, report)
    receipt_path = store / "receipts" / "mlflow" / f"mlflow-mirror-{MIRROR_KEY}.json"
    receipt_path.parent.mkdir(parents=True)
    receipt_path.write_text(json.dumps(receipt().as_dict(), sort_keys=True), encoding="utf-8")
    return store, report


class MLflowBootstrapTests(unittest.TestCase):
    def test_append_only_report_preserves_legacy_root_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = root / "store"
            store.mkdir()
            legacy = store / "mlflow-bootstrap.json"
            legacy.write_text('{"legacy": true}\n', encoding="utf-8")
            report = bootstrap._bootstrap_report(store, COMMIT, receipt())
            report_path = bootstrap._bootstrap_report_path(store, COMMIT, MIRROR_KEY)
            bootstrap._write_report_once(report_path, report)
            bootstrap._write_report_once(report_path, report)
            self.assertEqual(legacy.read_text(encoding="utf-8"), '{"legacy": true}\n')
            conflict = {**report, "dataset_access": "all"}
            with self.assertRaisesRegex(RuntimeError, "conflicting immutable"):
                bootstrap._write_report_once(report_path, conflict)

    def test_readonly_validator_accepts_complete_zero_only_bootstrap(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repository = root / "repo"
            repository.mkdir()
            store, _ = make_store(root)
            original = validator._git_head
            validator._git_head = lambda _repository: COMMIT
            try:
                report = validator.validate(store, repository)
            finally:
                validator._git_head = original
            self.assertEqual(report["status"], "PASS")
            self.assertFalse(report["scientific_run"])
            self.assertEqual(report["artifact_count"], 0)
            self.assertEqual(report["scientific_metric_count"], 0)

    def test_readonly_validator_rejects_metrics_without_changing_database(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repository = root / "repo"
            repository.mkdir()
            store, _ = make_store(root)
            database = store / "database" / "mlflow.db"
            connection = sqlite3.connect(database)
            try:
                connection.execute("INSERT INTO metrics VALUES (?, ?)", (RUN_ID, "forbidden"))
                connection.commit()
            finally:
                connection.close()
            before = database.read_bytes()
            original = validator._git_head
            validator._git_head = lambda _repository: COMMIT
            try:
                with self.assertRaisesRegex(validator.BootstrapValidationError, "contains metrics"):
                    validator.validate(store, repository)
            finally:
                validator._git_head = original
            self.assertEqual(database.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
