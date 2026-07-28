"""Independent validator for canonical run bundles."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .manifest import MANIFEST_V2, MANIFEST_V3
from .models import is_sha256
from ..identity import DISPLAY_NAME, PROGRAM_ID, PROTOCOL_FAMILY_ID, RESEARCH_VERSION


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


def validate_manifest_payload(manifest: dict[str, Any]) -> dict[str, Any]:
    schema = manifest.get("schema_version")
    if schema not in {MANIFEST_V2, MANIFEST_V3}:
        raise ValidationError("unsupported manifest schema")
    for section in ("identity", "lifecycle", "method", "inputs", "evaluator", "budget", "metrics", "artifacts"):
        if section not in manifest:
            raise ValidationError(f"manifest missing section: {section}")
    if not is_sha256(manifest["inputs"].get("dataset_manifest_hash")):
        raise ValidationError("dataset_manifest_hash must be SHA-256")
    if not is_sha256(manifest["inputs"].get("split_query_ids_hash")):
        raise ValidationError("split_query_ids_hash must be SHA-256")
    if not is_sha256(manifest["evaluator"].get("hash")):
        raise ValidationError("evaluator hash must be SHA-256")

    if schema == MANIFEST_V3:
        research = manifest.get("identity", {}).get("research")
        expected_research = {
            "program_id": PROGRAM_ID,
            "display_name": DISPLAY_NAME,
            "research_version": RESEARCH_VERSION,
            "protocol_family_id": PROTOCOL_FAMILY_ID,
        }
        if not isinstance(research, dict) or any(research.get(key) != value for key, value in expected_research.items()):
            raise ValidationError("manifest is not bound to IS1 Research V0.1")
        if not str(research.get("revision_id", "")).strip():
            raise ValidationError("manifest research revision_id is required")
        environment = manifest.get("environment")
        phase = str(manifest["identity"].get("phase", ""))
        measured = not phase.startswith(("offline", "bootstrap", "fixture"))
        if measured and environment is None:
            raise ValidationError("measured manifests require a locked runtime environment")
        if environment is not None:
            required_environment = ("python_version", "uv_version", "os", "architecture", "accelerator")
            missing_environment = [name for name in required_environment if not str(environment.get(name, "")).strip()]
            if missing_environment:
                raise ValidationError(f"environment missing fields: {missing_environment}")
            if not str(environment.get("python_version", "")).startswith("3.11."):
                raise ValidationError("measured environment requires an exact Python 3.11 patch version")
            if not is_sha256(environment.get("uv_lock_sha256")):
                raise ValidationError("environment uv_lock_sha256 must be SHA-256")
        provider = manifest["method"].get("provider")
        if measured and provider is None:
            raise ValidationError("measured manifests require requested/resolved provider identity")
        if provider is not None:
            required_provider = ("requested_model", "resolved_model", "provider", "effort", "endpoint_class")
            missing_provider = [name for name in required_provider if not str(provider.get(name, "")).strip()]
            if missing_provider:
                raise ValidationError(f"provider identity missing fields: {missing_provider}")
            if provider.get("requested_model") != provider.get("resolved_model"):
                raise ValidationError("requested/resolved model identity mismatch")
            if measured and (provider.get("fallback_allowed") or provider.get("fallback_used")):
                raise ValidationError("provider fallback invalidates a measured manifest")
        isolation = manifest.get("isolation")
        if measured and isolation is None:
            raise ValidationError("measured manifests require offline execution isolation")
        if isolation is not None:
            if isolation.get("network_mode") != "offline" or isolation.get("confirmation_access"):
                raise ValidationError("measured execution isolation must be offline and confirmation-blind")
            if isolation.get("dependency_replay_command") != "uv sync --locked":
                raise ValidationError("dependency replay must use uv sync --locked")
            scopes = isolation.get("data_scopes", [])
            if not scopes or set(scopes) - {"adaptation", "selection"} or len(scopes) != len(set(scopes)):
                raise ValidationError("execution isolation data scopes are invalid")
            if not is_sha256(isolation.get("network_guard_sha256")) or not is_sha256(
                isolation.get("cached_inputs_sha256")
            ):
                raise ValidationError("execution isolation commitments must be SHA-256")
        replication = manifest.get("replication")
        if replication is not None:
            if not str(replication.get("repeat_id", "")).strip() or int(replication.get("order_index", -1)) < 0:
                raise ValidationError("replication requires repeat_id and non-negative order_index")
        surfaces = manifest.get("surfaces")
        if surfaces is not None:
            overlap = set(surfaces.get("editable", [])) & set(surfaces.get("protected", []))
            if overlap:
                raise ValidationError(f"editable/protected surface overlap: {sorted(overlap)}")
        statistics = manifest.get("statistics")
        if statistics is not None:
            if statistics.get("bootstrap_resamples") != 10_000 or statistics.get("confidence_level") != 0.95:
                raise ValidationError("statistics contract must use 10,000 paired-bootstrap resamples at 95%")
            role = statistics.get("comparison_role")
            expected_correction = "none" if role == "primary" else "holm" if role == "additional" else None
            if expected_correction is None or statistics.get("correction") != expected_correction:
                raise ValidationError("statistics comparison family/correction contract is invalid")
        pool = manifest.get("candidate_pool")
        if pool is not None:
            if (
                not pool.get("frozen")
                or not is_sha256(pool.get("candidate_pool_sha256"))
                or not is_sha256(pool.get("policy_sha256"))
                or int(pool.get("final_k", 0)) <= 0
                or int(pool.get("query_count", 0)) <= 0
            ):
                raise ValidationError("candidate pool reference must be frozen and hash-bound")
        declared = manifest.get("declared_artifact_hashes", {})
        if any(not is_sha256(value) for value in declared.values()):
            raise ValidationError("declared artifact hashes must be SHA-256")
    return {"schema_version": schema, "read_only_legacy": schema == MANIFEST_V2}


def validate_run_bundle(run_dir: Path, *, expected_split_hash: str | None = None) -> dict[str, Any]:
    missing = [name for name in REQUIRED_RUN_FILES if not (run_dir / name).is_file()]
    if missing:
        raise ValidationError(f"missing run artifacts: {', '.join(missing)}")

    manifest = _json(run_dir / "manifest.json")
    manifest_validation = validate_manifest_payload(manifest)
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
        **manifest_validation,
    }
