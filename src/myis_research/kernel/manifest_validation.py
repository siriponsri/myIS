"""Fail-closed validation and ordered persistence for run-manifest v2."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import Any, Mapping

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from ..owner_local import OwnerLocalContractError, canonical_sha256 as owner_canonical_sha256
from ..owner_local import validate_receipt, validate_request
from ..protection import assert_aggregate_only, assert_hash_only_mapping
from .canonical import canonical_json, canonical_sha256


MANIFEST_SCHEMA = "myis.run-manifest.v2"
VALIDATION_REPORT_SCHEMA = "myis.run-manifest-validation.v1"
_MANIFEST_KEYS = frozenset({
    "schema_version", "run_id", "parent_run_id", "experiment_id", "campaign_id", "evidence_class",
    "status", "stage", "created_at_utc", "git", "request_sha256", "inputs", "method", "resources",
    "metrics", "artifacts", "commitments", "receipt_sha256", "manifest_sha256",
})
_COMMITMENT_KEYS = frozenset({
    "inputs_sha256", "method_sha256", "resources_sha256", "metrics_sha256", "artifacts_sha256",
})
_SHA256_LENGTH = 64
_SCHEMA_DIRECTORY = Path(__file__).resolve().parents[3] / "schemas"


class ManifestValidationError(ValueError):
    """Raised when a public manifest cannot be proven canonical and safe."""


def capture_git_state(repository_root: Path) -> dict[str, str]:
    """Capture HEAD and tracked-file state; untracked artifacts do not dirty code."""

    root = Path(repository_root).resolve()
    commit = _git_output(root, "rev-parse", "--verify", "HEAD").decode("ascii").strip()
    if not _is_git_commit(commit):
        raise ManifestValidationError("repository HEAD is not a full lowercase Git commit")
    tracked_diff = _git_output(root, "diff", "--binary", "HEAD", "--")
    return {
        "commit": commit,
        "tracked_worktree_state": "clean" if not tracked_diff else "dirty",
        "tracked_worktree_diff_sha256": hashlib.sha256(tracked_diff).hexdigest(),
    }


def validate_manifest(payload: Mapping[str, Any]) -> None:
    """Validate the active JSON-schema shape and its all-content commitments."""

    if not isinstance(payload, Mapping) or set(payload) != _MANIFEST_KEYS:
        raise ManifestValidationError("manifest fields do not match run-manifest.v2")
    _validate_json_schema(payload, "run-manifest.v2.json")
    if payload["schema_version"] != MANIFEST_SCHEMA:
        raise ManifestValidationError("unsupported manifest schema")
    if not isinstance(payload["run_id"], str) or not payload["run_id"]:
        raise ManifestValidationError("manifest run_id is invalid")
    if not isinstance(payload["experiment_id"], str) or not payload["experiment_id"]:
        raise ManifestValidationError("manifest experiment_id is invalid")
    if payload["campaign_id"] != "scope-autoindex-v1":
        raise ManifestValidationError("manifest campaign_id is invalid")
    if payload["stage"] not in {"fixture", "train", "selection", "final", "report"}:
        raise ManifestValidationError("manifest stage is invalid")
    if payload["status"] not in {"valid", "invalid", "blocked", "exploratory", "superseded", "aggregate_pending"}:
        raise ManifestValidationError("manifest status is invalid")
    if payload["evidence_class"] not in {"fixture", "train_selection_measured", "final", "report", "blocked"}:
        raise ManifestValidationError("manifest evidence_class is invalid")
    if payload["parent_run_id"] is not None and (not isinstance(payload["parent_run_id"], str) or not payload["parent_run_id"]):
        raise ManifestValidationError("manifest parent_run_id is invalid")
    _validate_timestamp(payload["created_at_utc"])
    _validate_git(payload["git"])
    _validate_hash(payload["request_sha256"], "request_sha256")
    _validate_hash(payload["receipt_sha256"], "receipt_sha256")
    _validate_inputs(payload["inputs"])
    _validate_content(payload["method"], "method")
    _validate_content(payload["resources"], "resources")
    _validate_content_list(payload["metrics"], "metrics")
    _validate_content_list(payload["artifacts"], "artifacts")
    _validate_commitments(payload)
    assert_aggregate_only(payload)
    recorded = payload["manifest_sha256"]
    _validate_hash(recorded, "manifest_sha256")
    unsigned = {key: value for key, value in payload.items() if key != "manifest_sha256"}
    if canonical_sha256(unsigned) != recorded:
        raise ManifestValidationError("manifest_sha256 does not match canonical manifest bytes")


def validate_manifest_binding(
    payload: Mapping[str, Any],
    owner_local_request: Mapping[str, Any],
    owner_local_receipt: Mapping[str, Any],
) -> None:
    """Prove that the public manifest references these exact Owner-local records."""

    validate_manifest(payload)
    try:
        request = validate_request(owner_local_request)
        receipt = validate_receipt(owner_local_receipt)
    except OwnerLocalContractError as error:
        raise ManifestValidationError("owner-local request or receipt is invalid") from error
    request_sha256 = owner_canonical_sha256(request)
    if payload["request_sha256"] != request_sha256 or receipt["request_sha256"] != request_sha256:
        raise ManifestValidationError("manifest and receipt must bind the supplied request")
    if payload["receipt_sha256"] != receipt["receipt_sha256"]:
        raise ManifestValidationError("manifest does not bind the supplied receipt")
    if payload["git"]["commit"] != request["git_commit"]:
        raise ManifestValidationError("manifest Git commit does not bind the supplied request")


def build_validation_report(
    payload: Mapping[str, Any],
    *,
    owner_local_request: Mapping[str, Any],
    owner_local_receipt: Mapping[str, Any],
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Return a hash-bound validation report for a canonical immutable manifest."""

    validate_manifest_binding(payload, owner_local_request, owner_local_receipt)
    body: dict[str, Any] = {
        "schema_version": VALIDATION_REPORT_SCHEMA,
        "created_at_utc": timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "valid",
        "manifest_sha256": payload["manifest_sha256"],
        "checks": {
            "json_schema": "pass",
            "git_state_commitment": "pass",
            "request_receipt_binding": "pass",
            "content_commitments": "pass",
            "manifest_commitment": "pass",
            "aggregate_only_boundary": "pass",
        },
    }
    body["validation_report_sha256"] = canonical_sha256(body)
    validate_validation_report(body)
    return body


def validate_validation_report(payload: Mapping[str, Any]) -> None:
    """Validate the report schema and its self-commitment before persistence."""

    _validate_json_schema(payload, "manifest-validation-report.v1.json")
    _validate_timestamp(payload["created_at_utc"])
    _validate_hash(payload["manifest_sha256"], "manifest_sha256")
    _validate_hash(payload["validation_report_sha256"], "validation_report_sha256")
    unsigned = {key: value for key, value in payload.items() if key != "validation_report_sha256"}
    if canonical_sha256(unsigned) != payload["validation_report_sha256"]:
        raise ManifestValidationError("validation_report_sha256 does not match canonical report bytes")


def write_validated_manifest(
    manifest_path: Path,
    validation_report_path: Path,
    payload: Mapping[str, Any],
    *,
    owner_local_request: Mapping[str, Any],
    owner_local_receipt: Mapping[str, Any],
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Persist the validation report before creating a never-overwritten manifest."""

    if payload.get("git", {}).get("tracked_worktree_state") != "clean":
        raise ManifestValidationError("tracked worktree must be clean before persisting an immutable manifest")
    report = build_validation_report(
        payload,
        owner_local_request=owner_local_request,
        owner_local_receipt=owner_local_receipt,
        timestamp=timestamp,
    )
    _write_new_json(Path(validation_report_path), report)
    _write_new_json(Path(manifest_path), dict(payload))
    return report


def _git_output(root: Path, *args: str) -> bytes:
    try:
        completed = run(["git", *args], cwd=root, check=True, capture_output=True)
    except (OSError, CalledProcessError) as error:
        raise ManifestValidationError(f"cannot capture Git state for {root}") from error
    return completed.stdout


def _validate_git(value: Any) -> None:
    if not isinstance(value, Mapping) or set(value) != {"commit", "tracked_worktree_state", "tracked_worktree_diff_sha256"}:
        raise ManifestValidationError("manifest git state shape is invalid")
    _validate_git_commit(value["commit"])
    if value["tracked_worktree_state"] not in {"clean", "dirty"}:
        raise ManifestValidationError("git.tracked_worktree_state must be clean or dirty")
    _validate_hash(value["tracked_worktree_diff_sha256"], "git.tracked_worktree_diff_sha256")


def _validate_inputs(value: Any) -> None:
    if not isinstance(value, Mapping) or not isinstance(value.get("hashes"), Mapping):
        raise ManifestValidationError("manifest inputs must include a named hash mapping")
    try:
        assert_hash_only_mapping({str(key): str(item) for key, item in value["hashes"].items()}, name="inputs.hashes")
    except ValueError as error:
        raise ManifestValidationError("manifest input hashes are invalid") from error


def _validate_content(value: Any, field_name: str) -> None:
    if not isinstance(value, Mapping):
        raise ManifestValidationError(f"manifest {field_name} must be an object")


def _validate_content_list(value: Any, field_name: str) -> None:
    if not isinstance(value, list) or not all(isinstance(item, Mapping) for item in value):
        raise ManifestValidationError(f"manifest {field_name} must be an array of objects")


def _validate_commitments(payload: Mapping[str, Any]) -> None:
    commitments = payload["commitments"]
    if not isinstance(commitments, Mapping) or set(commitments) != _COMMITMENT_KEYS:
        raise ManifestValidationError("manifest content commitment fields are invalid")
    expected = {
        "inputs_sha256": canonical_sha256(payload["inputs"]),
        "method_sha256": canonical_sha256(payload["method"]),
        "resources_sha256": canonical_sha256(payload["resources"]),
        "metrics_sha256": canonical_sha256(payload["metrics"]),
        "artifacts_sha256": canonical_sha256(payload["artifacts"]),
    }
    for key, value in expected.items():
        _validate_hash(commitments[key], f"commitments.{key}")
        if commitments[key] != value:
            raise ManifestValidationError(f"manifest {key} does not match canonical content")


def _validate_timestamp(value: Any) -> None:
    if not isinstance(value, str) or not value:
        raise ManifestValidationError("manifest created_at_utc is invalid")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ManifestValidationError("manifest created_at_utc is not ISO-8601") from error


def _validate_hash(value: Any, field_name: str) -> None:
    if not _is_sha256(value):
        raise ManifestValidationError(f"{field_name} must be a lowercase SHA-256")


def _validate_git_commit(value: Any) -> None:
    if not _is_git_commit(value):
        raise ManifestValidationError("git.commit must be a full lowercase Git commit")


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == _SHA256_LENGTH and all(char in "0123456789abcdef" for char in value)


def _is_git_commit(value: Any) -> bool:
    return isinstance(value, str) and len(value) in {40, 64} and all(char in "0123456789abcdef" for char in value)


def _validate_json_schema(payload: Mapping[str, Any], schema_name: str) -> None:
    schema_path = _SCHEMA_DIRECTORY / schema_name
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(dict(payload))
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        raise ManifestValidationError(f"JSON Schema validation failed for {schema_name}: {error}") from error


def _write_new_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (canonical_json(payload) + "\n").encode("utf-8")
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    except FileExistsError as error:
        raise ManifestValidationError(f"refusing to overwrite immutable artifact: {path}") from error
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        # This path was exclusively created by this call and cannot be trusted
        # as a complete immutable artifact after a write failure.
        path.unlink(missing_ok=True)
        raise
