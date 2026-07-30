"""Validated aggregate/hash-only F1/G1 readiness projection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ..harness.dapfam_contracts import SAFE_PROJECTION_SCHEMA, validate_owner_value_batch


def owner_local_f1_g1_root(repository_root: Path) -> Path | None:
    repository_root = repository_root.resolve(strict=True)
    candidates = []
    for ancestor in (repository_root, *repository_root.parents):
        candidate = ancestor / "01_Stores" / "00_myIS" / "owner-local" / "f1-g1"
        if candidate.is_dir():
            candidates.append(candidate.resolve())
    unique = list(dict.fromkeys(candidates))
    if len(unique) > 1:
        raise ValueError("multiple Owner-local F1/G1 stores were discovered")
    return unique[0] if unique else None


def load_f1_g1_readiness(repository_root: Path, *, owner_root: Path | None = None) -> dict[str, Any]:
    root = owner_root.resolve(strict=True) if owner_root else owner_local_f1_g1_root(repository_root)
    if root is None:
        return _not_prepared()
    _assert_store_boundary(root, repository_root.resolve(strict=True))
    projection_path = _regular_child(root, "safe/projections/current.json")
    if projection_path is None:
        return _not_prepared()
    projection = _json_object(projection_path)
    if projection.get("schema_version") != SAFE_PROJECTION_SCHEMA:
        raise ValueError("Owner-local F1/G1 projection schema is invalid")
    proposal = _sha256_value(projection.get("proposal_sha256"), "proposal_sha256")
    batch_path = _regular_child(root, f"safe/batches/g1-owner-value-batch-{proposal}.json")
    if batch_path is None:
        raise ValueError("Owner-local F1/G1 safe batch is missing")
    batch = validate_owner_value_batch(_json_object(batch_path))
    batch_sha = hashlib.sha256(batch_path.read_bytes()).hexdigest()
    if batch_sha != projection.get("safe_batch_sha256"):
        raise ValueError("Owner-local F1/G1 safe batch hash drifted")
    if projection.get("gate_status") != "pending" or projection.get("authorization") != "NOT_AUTHORIZED":
        raise ValueError("Owner-local F1/G1 projection crossed the G1 boundary")
    if projection.get("scientific_run") is not False or projection.get("scientific_metric_count") != 0:
        raise ValueError("Owner-local F1/G1 projection contains scientific execution")
    public = {
        key: projection[key]
        for key in (
            "schema_version",
            "status",
            "readiness",
            "gate",
            "gate_status",
            "authorization",
            "scientific_run",
            "scientific_metric_count",
            "proposal_sha256",
            "supersedes_proposal_sha256",
            "safe_batch_sha256",
            "inventory_counts",
            "qrels_domain_distribution",
            "split",
            "source_commitments",
            "family_commitment_sha256",
            "evaluator",
            "field_protocol",
            "published_targets",
            "unresolved_owner_decisions",
            "mlflow",
            "notebook",
        )
    }
    serialized = json.dumps(public, ensure_ascii=True, sort_keys=True)
    if str(root) in serialized or "membership" in serialized and "membership_sha256" not in serialized:
        raise ValueError("Owner-local F1/G1 public projection is not redacted")
    public["prepared"] = True
    public["safe_batch_schema_version"] = batch.schema_version
    return public


def _not_prepared() -> dict[str, Any]:
    return {
        "schema_version": SAFE_PROJECTION_SCHEMA,
        "prepared": False,
        "status": "NOT_PREPARED",
        "readiness": "F1/G1 preparation only",
        "gate": "G1",
        "gate_status": "pending",
        "authorization": "NOT_AUTHORIZED",
        "scientific_run": False,
        "scientific_metric_count": 0,
    }


def _assert_store_boundary(root: Path, repository_root: Path) -> None:
    try:
        root.relative_to(repository_root)
    except ValueError:
        pass
    else:
        raise PermissionError("Owner-local F1/G1 store must remain outside Git")
    if root.is_symlink() or not root.is_dir():
        raise PermissionError("Owner-local F1/G1 root must be a regular directory")
    expected_tail = ("01_Stores", "00_myIS", "owner-local", "f1-g1")
    if tuple(root.parts[-4:]) != expected_tail:
        raise PermissionError("Owner-local F1/G1 root is outside the approved store namespace")


def _regular_child(root: Path, relative: str) -> Path | None:
    target = root.joinpath(*relative.split("/"))
    if not target.exists():
        return None
    if target.is_symlink() or not target.is_file():
        raise PermissionError("Owner-local F1/G1 projection source must be a regular file")
    resolved = target.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise PermissionError("Owner-local F1/G1 projection escaped its store") from error
    return resolved


def _json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Owner-local F1/G1 JSON payload must be an object")
    return payload


def _sha256_value(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"Owner-local {label} is not SHA-256")
    return value
