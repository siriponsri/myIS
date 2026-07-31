"""Inspect a real MLflow SQLite archive, receipts, lineage and safe artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from myis_research.mlflow_mirror import LEGACY_EXPERIMENTS, V2_EXPERIMENTS


_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_PROTECTED_PATH_OR_KEY = re.compile(
    r"(?:^|[._/\\-])(qrels?|query[_-]?ids?|confirmation|heldout|membership|"
    r"per[_-]?query|rankings?|credentials?|secrets?|provider[_-]?payload)(?:[._/\\-]|$)",
    re.IGNORECASE,
)
_PROTECTED_TEXT = re.compile(
    r"\b(?:qrels?|query[ _-]?ids?|split[ _-]?membership|per[ _-]?query|"
    r"final[ _-]?rankings?|credentials?|secrets?|provider[ _-]?payload)\b",
    re.IGNORECASE,
)
_SECRET = re.compile(r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\bsk-[A-Za-z0-9_-]{12,}|\bBearer\s+[A-Za-z0-9._~+/-]{12,})", re.IGNORECASE)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def doctor(repository_root: Path, store_root: Path | None = None) -> dict[str, object]:
    root = repository_root.resolve()
    checks: dict[str, bool] = {
        "campaign_control": (root / "control/campaigns/scope-autoindex-v1.yaml").is_file(),
        "legacy_mapping": _legacy_mapping_valid(root),
        "archive_independent": not any(
            "archive/" in path.as_posix().replace("\\", "/")
            for path in (root / "scripts").rglob("*.py")
            if "archive" in path.read_text(encoding="utf-8", errors="ignore")
        ),
    }
    metadata: dict[str, object] = {
        "legacy_experiments": list(LEGACY_EXPERIMENTS),
        "v2_experiments": list(V2_EXPERIMENTS),
    }
    if store_root is None:
        checks["store_configured"] = False
        return _result(checks, metadata, reason="pass --store-root or set MYIS_MLFLOW_STORE")
    store = store_root.resolve()
    database = store / "database/mlflow.db"
    checks["store_external"] = root not in store.parents and store != root
    checks["store_configured"] = True
    checks["database_exists"] = database.is_file() and not database.is_symlink()
    if not checks["database_exists"]:
        return _result(checks, metadata, reason="SQLite database is missing", database=str(database))
    before = _hash(database)
    checks["sqlite_header"] = database.read_bytes()[:16] == b"SQLite format 3\x00"
    tables: list[str] = []
    experiments: list[str] = []
    try:
        with sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True) as connection:
            tables = [row[0] for row in connection.execute("select name from sqlite_master where type='table'")]
            if "experiments" in tables:
                experiments = [row[0] for row in connection.execute("select name from experiments where lifecycle_stage='active'")]
            archive_ok, archive_counts, archive_failures = _validate_archives(store, connection)
    except (sqlite3.Error, OSError, ValueError) as error:
        checks["sqlite_read_only"] = False
        return _result(checks, metadata, reason=str(error), database=str(database))
    checks["sqlite_read_only"] = _hash(database) == before
    checks["required_tables"] = all(name in tables for name in ("experiments", "runs", "tags", "params", "metrics"))
    governed = set(experiments) - {"Default"}
    checks["legacy_experiments_preserved"] = set(LEGACY_EXPERIMENTS).issubset(governed)
    checks["v2_experiments_present"] = set(V2_EXPERIMENTS).issubset(governed)
    checks["artifact_root"] = (store / "artifacts").is_dir() and not (store / "artifacts").is_symlink()
    checks["archive_lineage"] = archive_ok
    checks["store_metadata"] = _store_metadata_valid(store)
    checks["backup_ready"] = (store / "database").is_dir() and (store / "receipts").is_dir() and checks["store_metadata"]
    metadata.update({"database": str(database), "tables": tables, "experiments": experiments, "archive_counts": archive_counts, "archive_failures": archive_failures})
    return _result(checks, metadata)


def _validate_archives(store: Path, connection: sqlite3.Connection) -> tuple[bool, dict[str, int], list[str]]:
    failures: list[str] = []
    receipt_root = store / "receipts/archive"
    receipts = sorted(receipt_root.glob("*.json")) if receipt_root.is_dir() else []
    run_count = 0
    artifact_count = 0
    for path in receipts:
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
            if receipt.get("schema_version") != "myis.mlflow-archive-receipt.v2" or path.stem != receipt.get("archive_key"):
                raise ValueError("archive receipt identity mismatch")
            for key in ("archive_key", "archive_record_sha256", "mirror_receipt_sha256", "read_model_sha256", "read_model_revision"):
                if not _SHA256.fullmatch(str(receipt.get(key, ""))):
                    raise ValueError(f"invalid {key}")
            run_id = str(receipt.get("mlflow_run_id", ""))
            run_row = connection.execute("select artifact_uri from runs where run_uuid=? and lifecycle_stage='active'", (run_id,)).fetchone()
            if run_row is None:
                raise ValueError("MLflow run is missing")
            tags = dict(connection.execute("select key, value from tags where run_uuid=?", (run_id,)).fetchall())
            if tags.get("read_model_revision") != receipt["read_model_revision"] or tags.get("read_model_sha256") != receipt["read_model_sha256"]:
                raise ValueError("run/read-model tag mismatch")
            mirror_key = tags.get("mirror_key", "")
            mirror_path = store / "receipts/mlflow" / f"mlflow-mirror-{mirror_key}.json"
            mirror = json.loads(mirror_path.read_text(encoding="utf-8"))
            mirror_sha = hashlib.sha256(json.dumps(mirror, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()
            if mirror_sha != receipt["mirror_receipt_sha256"] or mirror.get("mlflow_run_id") != run_id:
                raise ValueError("mirror receipt hash or run mismatch")
            staging = store / "staging" / receipt["archive_key"]
            run_record = json.loads((staging / "about/run.json").read_text(encoding="utf-8"))
            if run_record.get("archive_record_sha256") != receipt["archive_record_sha256"]:
                raise ValueError("archive record hash mismatch")
            if run_record.get("freeze_sha256") != tags.get("freeze_sha256"):
                raise ValueError("freeze lineage mismatch")
            artifact_root = _artifact_uri_path(str(run_row[0])) / "mirror"
            staged_files = [item for item in staging.rglob("*") if item.is_file()]
            stored_files = [item for item in artifact_root.rglob("*") if item.is_file()]
            staged_by_suffix = {item.relative_to(staging).as_posix(): _hash(item) for item in staged_files}
            stored_by_suffix = {}
            for item in stored_files:
                relative = item.relative_to(artifact_root).as_posix()
                parts = relative.split("/", 1)
                if len(parts) != 2:
                    raise ValueError("stored artifact path is malformed")
                stored_by_suffix[parts[1]] = _hash(item)
                text = item.read_text(encoding="utf-8", errors="strict")
                if (
                    _PROTECTED_PATH_OR_KEY.search(relative)
                    or _PROTECTED_TEXT.search(text)
                    or _SECRET.search(text)
                    or _contains_protected_key(text)
                ):
                    raise ValueError("protected or secret content found in exposed artifact")
            if staged_by_suffix != stored_by_suffix:
                raise ValueError("stored artifact hashes do not match staging")
            run_count += 1
            artifact_count += len(stored_files)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            failures.append(f"{path.name}: {error}")
    return not failures, {"archive_receipts": len(receipts), "archive_runs": run_count, "archive_artifacts": artifact_count}, failures


def _contains_protected_key(text: str) -> bool:
    """Catch protected structured keys even when JSON punctuation hides word boundaries."""

    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return False
    return _structured_key_is_protected(value)


def _structured_key_is_protected(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower()
            commitment = normalized.endswith(("_hash", "_sha256"))
            lifecycle_flag = normalized in {"confirmation", "is_confirmation"} and isinstance(item, bool)
            if _PROTECTED_PATH_OR_KEY.search(normalized) and not (commitment or lifecycle_flag):
                return True
            if _structured_key_is_protected(item):
                return True
    elif isinstance(value, list):
        return any(_structured_key_is_protected(item) for item in value)
    return False


def _artifact_uri_path(value: str) -> Path:
    from urllib.parse import unquote, urlparse

    parsed = urlparse(value)
    if parsed.scheme != "file":
        raise ValueError("artifact URI is not local file storage")
    raw = unquote(parsed.path)
    if parsed.netloc:
        raw = f"//{parsed.netloc}{raw}"
    if re.match(r"^/[A-Za-z]:/", raw):
        raw = raw[1:]
    return Path(raw).resolve(strict=True)


def _store_metadata_valid(store: Path) -> bool:
    try:
        value = json.loads((store / "store.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return value.get("schema_version") == "myis.mlflow-store.v2" and value.get("artifact_root") == "artifacts"


def _legacy_mapping_valid(root: Path) -> bool:
    path = root / "mlflow/legacy-experiment-map.v2.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    names = {str(item.get("name")) for item in value.get("experiments", []) if isinstance(item, dict)}
    statuses = {str(item.get("status")) for item in value.get("experiments", []) if isinstance(item, dict)}
    return (
        value.get("schema_version") == "myis.mlflow-legacy-experiment-map.v2"
        and value.get("policy") == "legacy_read_only"
        and set(LEGACY_EXPERIMENTS) == names
        and statuses == {"legacy_read_only"}
        and set(V2_EXPERIMENTS) == set(value.get("active_experiments", []))
    )


def _result(checks: dict[str, bool], metadata: dict[str, object], *, reason: str | None = None, **extra: object) -> dict[str, object]:
    passed = bool(checks) and all(checks.values())
    result: dict[str, object] = {"schema_version": "myis.mlflow-doctor.v2", "status": "PASS" if passed else "BLOCKED", "checks": checks, **metadata, **extra}
    if reason:
        result["reason"] = reason
    return result


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
