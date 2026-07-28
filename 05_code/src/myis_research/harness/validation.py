"""Independent validator for canonical run bundles."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REQUIRED_RUN_FILES = (
    "prompt.json",
    "flow.json",
    "progress.jsonl",
    "result.json",
    "metrics.json",
    "runtime.jsonl",
    "per_query_metrics.jsonl",
    "validation_report.json",
    "manifest.json",
)


class ValidationError(RuntimeError):
    pass


def _json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"invalid UTF-8 JSON: {path.name}: {error}") from error


def _validate_jsonl(path: Path, *, require_sequence: bool = False) -> list[dict[str, Any]]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValidationError(f"invalid JSONL {path.name}:{number}: {error}") from error
        rows.append(row)
    if require_sequence:
        sequence = [row.get("sequence") for row in rows]
        if sequence != list(range(1, len(sequence) + 1)):
            raise ValidationError(f"non-monotonic event sequence in {path.name}")
    return rows


def validate_run_bundle(run_dir: Path, *, expected_split_hash: str | None = None) -> dict[str, Any]:
    missing = [name for name in REQUIRED_RUN_FILES if not (run_dir / name).is_file()]
    if missing:
        raise ValidationError(f"missing run artifacts: {', '.join(missing)}")

    manifest = _json(run_dir / "manifest.json")
    if manifest.get("schema_version") != "myis.run-manifest.v2":
        raise ValidationError("unsupported manifest schema")
    if expected_split_hash and manifest["inputs"]["split_query_ids_hash"] != expected_split_hash:
        raise ValidationError("split query-ID hash mismatch")

    listed = {item["path"]: item for item in manifest.get("artifacts", [])}
    for relative, item in listed.items():
        path = run_dir / relative
        if not path.is_file():
            raise ValidationError(f"manifest artifact is missing: {relative}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != item["sha256"] or path.stat().st_size != item["size_bytes"]:
            raise ValidationError(f"artifact integrity failure: {relative}")

    runtime = _validate_jsonl(run_dir / "runtime.jsonl", require_sequence=True)
    progress = _validate_jsonl(run_dir / "progress.jsonl")
    _validate_jsonl(run_dir / "per_query_metrics.jsonl")
    runtime_ids = {row["event_id"] for row in runtime}
    if any(row.get("event_id") not in runtime_ids for row in progress):
        raise ValidationError("progress event is not a projection of runtime events")

    return {
        "status": "PASS",
        "run_id": manifest["identity"]["run_id"],
        "artifact_count": len(listed),
        "runtime_event_count": len(runtime),
        "progress_event_count": len(progress),
        "manifest_sha256": hashlib.sha256((run_dir / "manifest.json").read_bytes()).hexdigest(),
    }
