"""Inspect a real MLflow SQLite mirror without treating declarations as proof."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from myis_research.mlflow_mirror import EXPERIMENTS


def doctor(repository_root: Path, store_root: Path | None = None) -> dict[str, object]:
    root = repository_root.resolve()
    checks: dict[str, object] = {
        "campaign_control": (root / "control/campaigns/scope-autoindex-v1.yaml").is_file(),
        "active_experiments": list(EXPERIMENTS),
        "archive_independent": not any("archive/" in path.as_posix().replace("\\", "/") for path in (root / "scripts").rglob("*.py") if "archive" in path.read_text(encoding="utf-8", errors="ignore")),
    }
    if store_root is None:
        checks["store_configured"] = False
        return {"schema_version": "myis.mlflow-doctor.v2", "status": "BLOCKED", "checks": checks, "reason": "pass --store-root or set MYIS_MLFLOW_STORE"}
    store = store_root.resolve()
    db = store / "database" / "mlflow.db"
    checks["store_external"] = root not in store.parents and store != root
    checks["database_exists"] = db.is_file()
    if not db.is_file():
        return {"schema_version": "myis.mlflow-doctor.v2", "status": "BLOCKED", "checks": checks, "reason": "SQLite database is missing", "database": str(db)}
    header = db.read_bytes()[:16]
    checks["sqlite_header"] = header == b"SQLite format 3\x00"
    tables: list[str] = []
    experiments: list[str] = []
    try:
        with sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True) as connection:
            tables = [row[0] for row in connection.execute("select name from sqlite_master where type='table'")]
            if "experiments" in tables:
                experiments = [row[0] for row in connection.execute("select name from experiments where lifecycle_stage='active'")]
    except sqlite3.Error as error:
        checks["sqlite_read_only"] = False
        return {"schema_version": "myis.mlflow-doctor.v2", "status": "BLOCKED", "checks": checks, "reason": str(error), "database": str(db)}
    checks["sqlite_read_only"] = True
    checks["required_tables"] = all(name in tables for name in ("experiments", "runs", "tags", "params", "metrics"))
    # MLflow creates a built-in Default experiment; it is outside the governed
    # namespace and must not make an otherwise valid store fail closed.
    governed = set(experiments) - {"Default"}
    checks["experiment_lineage"] = governed == set(EXPERIMENTS)
    checks["artifact_root"] = (store / "artifacts").is_dir()
    checks["store_configured"] = True
    passed = all(value is True for key, value in checks.items() if key not in {"active_experiments"})
    return {"schema_version": "myis.mlflow-doctor.v2", "status": "PASS" if passed else "BLOCKED", "checks": checks, "database": str(db), "tables": tables, "experiments": experiments}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--store-root", type=Path)
    args = parser.parse_args(argv)
    result = doctor(args.repository_root, args.store_root)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
