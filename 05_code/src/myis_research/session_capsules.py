"""Fail-closed validation for append-only myIS research-session capsules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any, Mapping

from .identity import IdentityValidationError, validate_full_git_commit
from .protection import assert_aggregate_only


SESSION_SCHEMA = "myis.research-session.v1"
SESSION_ROOT = Path("04_outputs/audits/research-sessions")
EVENT_TYPES = frozenset({"decision", "experiment", "dead_end", "pivot", "claim", "heuristic", "action", "observation"})
PROVENANCE_VALUES = frozenset({"owner", "agent-observed", "agent-proposed", "owner-revised"})
RUN_ARTIFACT_KEYS = frozenset({
    "prompt", "flow", "progress", "result", "metrics", "runtime", "per_query_metrics",
    "validation_report", "manifest", "mlflow_receipts",
})
_SESSION_ID_RE = re.compile(r"^[0-9]{8}T[0-9]{6}Z-[A-Za-z0-9._-]+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GATE_RE = re.compile(r"^G[0-8]$")
_SECRET_RE = re.compile(
    r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\bsk-[A-Za-z0-9_-]{12,}|"
    r"\bBearer\s+[A-Za-z0-9._~+/-]{12,}|(?:api[_-]?key|password|secret)\s*[:=]\s*[^\s]{8,})",
    re.IGNORECASE,
)


class SessionCapsuleValidationError(ValueError):
    """Raised when a capsule is malformed, mutable, or untraceable."""


@dataclass(frozen=True, slots=True)
class SessionCapsuleValidation:
    session_id: str
    repository_revision: str
    event_count: int
    reference_count: int
    open_thread_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "myis.session-capsule-validation.v1",
            "status": "PASS",
            "session_id": self.session_id,
            "repository_revision": self.repository_revision,
            "event_count": self.event_count,
            "reference_count": self.reference_count,
            "open_thread_count": self.open_thread_count,
        }


def assert_append_only_session_target(path: Path, repository_root: Path) -> Path:
    """Return a safe new capsule target without creating or overwriting it."""

    root = repository_root.resolve(strict=True)
    target = path.resolve(strict=False)
    expected_root = root / SESSION_ROOT
    try:
        target.relative_to(expected_root)
    except ValueError as exc:
        raise SessionCapsuleValidationError("session capsule target is outside its append-only root") from exc
    if target.parent != expected_root or target.suffix != ".json":
        raise SessionCapsuleValidationError("session capsule target must be a direct JSON file in the append-only root")
    if target.exists() or target.is_symlink():
        raise SessionCapsuleValidationError("append-only session capsule target already exists")
    if expected_root.exists() and (expected_root.is_symlink() or not expected_root.is_dir()):
        raise SessionCapsuleValidationError("session capsule root must be a regular directory")
    if target.name != target.stem + ".json" or not _SESSION_ID_RE.fullmatch(target.stem):
        raise SessionCapsuleValidationError("session capsule filename must use a UTC collision-resistant session ID")
    return target


def validate_session_capsule(path: Path, repository_root: Path) -> SessionCapsuleValidation:
    """Validate an existing capsule against the historical Git revision it records."""

    root = repository_root.resolve(strict=True)
    if path.is_symlink():
        raise SessionCapsuleValidationError("session capsule must not be a symlink")
    capsule = path.resolve(strict=True)
    expected_root = root / SESSION_ROOT
    try:
        capsule.relative_to(expected_root)
    except ValueError as exc:
        raise SessionCapsuleValidationError("session capsule is outside its authorized root") from exc
    if expected_root.is_symlink() or not expected_root.is_dir():
        raise SessionCapsuleValidationError("session capsule root must be a regular directory")
    if capsule.parent != expected_root or not capsule.is_file() or capsule.suffix != ".json":
        raise SessionCapsuleValidationError("session capsule must be a regular JSON file")
    try:
        payload = json.loads(capsule.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SessionCapsuleValidationError("session capsule is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise SessionCapsuleValidationError("session capsule root must be an object")

    _assert_no_protected_or_secret_content(payload)
    _required(payload, "schema_version", SESSION_SCHEMA)
    session_id = _required_string(payload, "session_id")
    if capsule.stem != session_id or not _SESSION_ID_RE.fullmatch(session_id):
        raise SessionCapsuleValidationError("session_id and append-only filename must match")
    _nullable_string(payload, "run_id")
    _nullable_string(payload, "goal_id")
    started = _nullable_timestamp(payload, "started_at_utc")
    ended = _timestamp(payload, "ended_at_utc")
    if started is not None and ended < started:
        raise SessionCapsuleValidationError("ended_at_utc precedes started_at_utc")
    _required_string(payload, "scope")
    _provenance(_required_string(payload, "provenance"), "capsule provenance")
    _validate_owner_approvals(payload.get("owner_approvals"))
    revision = _validate_repository(payload.get("repository"))
    reference_count = _validate_events(payload.get("events"), root, revision)
    _validate_run_artifacts(payload.get("run_artifacts"))
    open_threads = _validate_open_threads(payload.get("open_threads"))
    _validate_integrity(payload.get("integrity"))
    return SessionCapsuleValidation(session_id, revision, len(payload["events"]), reference_count, len(open_threads))


def _assert_no_protected_or_secret_content(payload: Mapping[str, Any]) -> None:
    try:
        assert_aggregate_only(payload)
    except ValueError as exc:
        raise SessionCapsuleValidationError(str(exc)) from exc
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True)
    if _SECRET_RE.search(encoded):
        raise SessionCapsuleValidationError("session capsule contains a credential or secret")


def _required(payload: Mapping[str, Any], key: str, expected: object) -> None:
    if payload.get(key) != expected:
        raise SessionCapsuleValidationError(f"{key} must be {expected!r}")


def _required_string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SessionCapsuleValidationError(f"{key} must be a non-empty string")
    return value


def _nullable_string(payload: Mapping[str, Any], key: str) -> None:
    value = payload.get(key)
    if value is not None and (not isinstance(value, str) or not value.strip()):
        raise SessionCapsuleValidationError(f"{key} must be a non-empty string or null")


def _timestamp(payload: Mapping[str, Any], key: str) -> datetime:
    value = _required_string(payload, key)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SessionCapsuleValidationError(f"{key} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise SessionCapsuleValidationError(f"{key} must include a timezone")
    return parsed


def _nullable_timestamp(payload: Mapping[str, Any], key: str) -> datetime | None:
    if payload.get(key) is None:
        return None
    return _timestamp(payload, key)


def _provenance(value: str, label: str) -> None:
    if value not in PROVENANCE_VALUES:
        raise SessionCapsuleValidationError(f"{label} is invalid")


def _validate_owner_approvals(value: Any) -> None:
    if not isinstance(value, list):
        raise SessionCapsuleValidationError("owner_approvals must be a list")
    for approval in value:
        if not isinstance(approval, dict):
            raise SessionCapsuleValidationError("owner approval must be an object")
        gate = _required_string(approval, "gate")
        if not _GATE_RE.fullmatch(gate):
            raise SessionCapsuleValidationError("owner approval gate is invalid")
        _required_string(approval, "source")
        _required_string(approval, "scope")


def _validate_repository(value: Any) -> str:
    if not isinstance(value, dict) or value.get("path") != ".":
        raise SessionCapsuleValidationError("repository.path must be '.'")
    revision = _required_string(value, "revision")
    try:
        validate_full_git_commit(revision, field_name="repository.revision")
    except IdentityValidationError as exc:
        raise SessionCapsuleValidationError(str(exc)) from exc
    dirty = value.get("dirty_paths")
    if not isinstance(dirty, list) or any(not isinstance(path, str) for path in dirty):
        raise SessionCapsuleValidationError("repository.dirty_paths must be a list of strings")
    return revision


def _validate_events(value: Any, root: Path, revision: str) -> int:
    if not isinstance(value, list):
        raise SessionCapsuleValidationError("events must be a list")
    reference_count = 0
    for expected_sequence, event in enumerate(value, start=1):
        if not isinstance(event, dict):
            raise SessionCapsuleValidationError("event must be an object")
        event_id = _required_string(event, "event_id")
        if not re.fullmatch(r"EV[0-9]{4,}", event_id):
            raise SessionCapsuleValidationError("event_id must be an EV-prefixed identifier")
        if event.get("sequence") != expected_sequence:
            raise SessionCapsuleValidationError("event sequence must be contiguous and ordered")
        if event.get("type") not in EVENT_TYPES:
            raise SessionCapsuleValidationError("event type is invalid")
        _provenance(_required_string(event, "provenance"), "event provenance")
        _required_string(event, "summary")
        refs = event.get("evidence_refs")
        if not isinstance(refs, list):
            raise SessionCapsuleValidationError("event evidence_refs must be a list")
        for reference in refs:
            _validate_reference(reference, root, revision)
            reference_count += 1
    return reference_count


def _validate_reference(value: Any, root: Path, revision: str) -> None:
    if not isinstance(value, dict):
        raise SessionCapsuleValidationError("evidence reference must be an object")
    relative = _repository_relative_path(_required_string(value, "path"))
    expected_hash = _required_string(value, "sha256")
    if not _SHA256_RE.fullmatch(expected_hash):
        raise SessionCapsuleValidationError("evidence reference sha256 must be lowercase SHA-256")
    _required_string(value, "locator")
    completed = subprocess.run(
        ["git", "show", f"{revision}:{relative}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SessionCapsuleValidationError(f"evidence reference is absent at recorded revision: {relative}")
    actual_hash = hashlib.sha256(completed.stdout).hexdigest()
    if actual_hash != expected_hash:
        raise SessionCapsuleValidationError(f"evidence reference hash mismatch: {relative}")


def _repository_relative_path(value: str) -> str:
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ":" in path.parts[0] or any(part in {"", ".", ".."} for part in path.parts):
        raise SessionCapsuleValidationError("evidence reference path must be repository-relative")
    return path.as_posix()


def _validate_run_artifacts(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != RUN_ARTIFACT_KEYS:
        raise SessionCapsuleValidationError("run_artifacts must contain the exact session-artifact keys")
    for key, item in value.items():
        if key == "mlflow_receipts":
            if not isinstance(item, list) or any(not isinstance(entry, str) for entry in item):
                raise SessionCapsuleValidationError("run_artifacts.mlflow_receipts must be a list of strings")
        elif item is not None and not isinstance(item, str):
            raise SessionCapsuleValidationError(f"run_artifacts.{key} must be a string or null")


def _validate_open_threads(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise SessionCapsuleValidationError("open_threads must be a list")
    for thread in value:
        if not isinstance(thread, dict):
            raise SessionCapsuleValidationError("open thread must be an object")
        _required_string(thread, "thread_id")
        _provenance(_required_string(thread, "provenance"), "open thread provenance")
        _required_string(thread, "summary")
        gate = thread.get("blocking_gate")
        if gate is not None and (not isinstance(gate, str) or not _GATE_RE.fullmatch(gate)):
            raise SessionCapsuleValidationError("open thread blocking_gate is invalid")
    return value


def _validate_integrity(value: Any) -> None:
    if not isinstance(value, dict):
        raise SessionCapsuleValidationError("integrity must be an object")
    expected = {
        "all_refs_exist": True,
        "all_hashes_match": True,
        "contains_protected_payload": False,
        "contains_secrets": False,
    }
    if value != expected:
        raise SessionCapsuleValidationError("integrity must report complete references and no protected content or secrets")
