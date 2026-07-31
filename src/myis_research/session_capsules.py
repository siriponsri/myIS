"""Fail-closed validation and discovery for append-only session capsules."""

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


SESSION_SCHEMA_V1 = "myis.research-session.v1"
SESSION_SCHEMA_V2 = "myis.research-session.v2"
# Kept for callers that imported the original public constant.
SESSION_SCHEMA = SESSION_SCHEMA_V1
SESSION_ROOT = Path("projections/sessions")
EVENT_TYPES = frozenset({"decision", "experiment", "dead_end", "pivot", "claim", "heuristic", "action", "observation"})
PROVENANCE_VALUES = frozenset({"owner", "agent-observed", "agent-proposed", "owner-revised"})
RUN_ARTIFACT_KEYS = frozenset({
    "prompt", "flow", "progress", "result", "metrics", "runtime", "per_query_metrics",
    "validation_report", "manifest", "mlflow_receipts",
})
V2_ROOT_KEYS = frozenset({
    "schema_version", "session_id", "run_id", "goal_id", "started_at_utc", "ended_at_utc",
    "scope", "provenance", "owner_approvals", "repository", "events", "run_artifacts",
    "open_threads", "integrity", "execution_snapshot", "owner_brief_th", "owner_actions",
    "gate_request", "next_resources", "closeout", "corrections",
})
V2_EVENT_KEYS = frozenset({"event_id", "sequence", "type", "provenance", "summary", "evidence_refs", "quantitative_claims"})
SNAPSHOT_KEYS = frozenset({"phase_id", "task_id", "gate_id", "gate_status"})
OWNER_ACTION_KEYS = frozenset({"action_id", "priority", "action_th", "reason_th", "blocking_gate"})
GATE_REQUEST_KEYS = frozenset({"gate_id", "state", "summary_th", "blocking_reason_th", "evidence_refs"})
NEXT_RESOURCES_KEYS = frozenset({"status", "items"})
NEXT_RESOURCE_KEYS = frozenset({"resource_id", "description_th", "purpose_th"})
CLOSEOUT_KEYS = frozenset({"checks", "changed_files", "untouched_protected_surfaces"})
CHECK_KEYS = frozenset({"check_id", "status", "summary"})
CORRECTION_KEYS = frozenset({"target_session_id", "observed_validation_error", "correction_th"})
QUANTITATIVE_CLAIM_KEYS = frozenset({"claim_id", "statement", "value", "unit", "evidence_ref"})
_SESSION_ID_RE = re.compile(r"^[0-9]{8}T[0-9]{6}Z-[A-Za-z0-9._-]+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GATE_RE = re.compile(r"^D[123]_[A-Z_]+$")
_TASK_RE = re.compile(r"^([A-Z][A-Z0-9]*)\.(\d+)$")
_PLAN_TASK_RE = re.compile(r"^### Task ([A-Z0-9]+\.\d+) - .+$")
_PLAN_GATE_RE = re.compile(r"^- \*\*Owner Decision:\*\* .*?\b(D[123]_[A-Z_]+)\b")
_THAI_RE = re.compile(r"[\u0e00-\u0e7f]")
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
    schema_version: str = SESSION_SCHEMA_V1

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
    """Validate one existing capsule against only its recorded historical revision."""

    root = repository_root.resolve(strict=True)
    capsule, payload = _load_capsule(path, root)
    _assert_no_protected_or_secret_content(payload)
    schema_version = payload.get("schema_version")
    if schema_version not in {SESSION_SCHEMA_V1, SESSION_SCHEMA_V2}:
        raise SessionCapsuleValidationError("schema_version is unsupported")
    if schema_version == SESSION_SCHEMA_V2:
        _exact_keys(payload, V2_ROOT_KEYS, "v2 capsule")

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
    strict = schema_version == SESSION_SCHEMA_V2
    _validate_owner_approvals(payload.get("owner_approvals"), strict=strict)
    revision = _validate_repository(payload.get("repository"), strict=strict)
    if schema_version == SESSION_SCHEMA_V1:
        reference_count = _validate_events_v1(payload.get("events"), root, revision)
    else:
        reference_count = _validate_events_v2(payload.get("events"), root, revision)
    _validate_run_artifacts(payload.get("run_artifacts"))
    open_threads = _validate_open_threads(payload.get("open_threads"), strict=strict)
    _validate_integrity(payload.get("integrity"))
    if schema_version == SESSION_SCHEMA_V2:
        reference_count += _validate_v2_closeout(payload, root, revision)
    return SessionCapsuleValidation(
        session_id, revision, len(payload["events"]), reference_count, len(open_threads), schema_version
    )


def validate_all_session_capsules(repository_root: Path) -> dict[str, object]:
    """Classify every capsule and allow valid v2 records to cover invalid v1 history."""

    root = repository_root.resolve(strict=True)
    session_root = root / SESSION_ROOT
    if session_root.is_symlink() or not session_root.is_dir():
        raise SessionCapsuleValidationError("session capsule root must be a regular directory")
    records: list[dict[str, object]] = []
    corrections: dict[str, set[str]] = {}
    for path in sorted(session_root.glob("*.json")):
        try:
            payload = _read_payload(path)
            report = validate_session_capsule(path, root)
            record: dict[str, object] = {
                "path": path.relative_to(root).as_posix(), "session_id": report.session_id,
                "capsule_schema_version": report.schema_version, "classification": "PASS", "reason": None,
            }
            if report.schema_version == SESSION_SCHEMA_V2:
                for correction in payload["corrections"]:
                    corrections.setdefault(correction["target_session_id"], set()).add(
                        correction["observed_validation_error"]
                    )
        except SessionCapsuleValidationError as error:
            session_id, schema = _unsafe_metadata(path)
            record = {
                "path": path.relative_to(root).as_posix(), "session_id": session_id,
                "capsule_schema_version": schema, "classification": "INVALID", "reason": str(error),
            }
        records.append(record)

    unresolved = 0
    for record in records:
        reasons = corrections.get(record["session_id"], set())
        if record["classification"] == "PASS" and reasons:
            record["classification"] = "SUPERSEDED"
            record["reason"] = "; ".join(sorted(reasons))
            continue
        if record["classification"] != "INVALID":
            continue
        if record["reason"] in reasons:
            record["classification"] = "CORRECTED_INVALID"
        else:
            unresolved += 1
    return {
        "schema_version": "myis.session-capsule-audit.v1",
        "status": "PASS" if unresolved == 0 else "FAIL",
        "records": records,
        "unresolved_invalid_count": unresolved,
    }


def latest_valid_session(
    repository_root: Path, *, phase_id: str | None = None, task_id: str | None = None, gate_id: str | None = None,
) -> dict[str, object] | None:
    """Return the latest individually valid capsule, optionally scoped to a v2 task snapshot."""

    root = repository_root.resolve(strict=True)
    candidates: list[tuple[datetime, str, dict[str, object]]] = []
    superseded: set[str] = set()
    for path in sorted((root / SESSION_ROOT).glob("*.json")):
        try:
            payload = _read_payload(path)
            report = validate_session_capsule(path, root)
        except SessionCapsuleValidationError:
            continue
        if report.schema_version == SESSION_SCHEMA_V2:
            superseded.update(
                str(item["target_session_id"])
                for item in payload["corrections"]
            )
        snapshot = payload.get("execution_snapshot")
        if any(value is not None for value in (phase_id, task_id, gate_id)):
            if report.schema_version != SESSION_SCHEMA_V2 or not isinstance(snapshot, dict):
                continue
            if phase_id is not None and snapshot["phase_id"] != phase_id:
                continue
            if task_id is not None and snapshot["task_id"] != task_id:
                continue
            if gate_id is not None and snapshot["gate_id"] != gate_id:
                continue
        candidates.append((_timestamp(payload, "ended_at_utc"), report.session_id, {
            "path": path.relative_to(root).as_posix(), "session_id": report.session_id,
            "capsule_schema_version": report.schema_version, "ended_at_utc": payload["ended_at_utc"],
            "execution_snapshot": snapshot,
            "owner_brief_th": payload.get("owner_brief_th"),
            "owner_actions": payload.get("owner_actions"),
            "gate_request": payload.get("gate_request"),
            "next_resources": payload.get("next_resources"),
            "closeout": payload.get("closeout"),
        }))
    candidates = [item for item in candidates if item[1] not in superseded]
    return max(candidates, default=(None, "", None), key=lambda item: (item[0] is not None, item[0], item[1]))[2]


def _load_capsule(path: Path, root: Path) -> tuple[Path, dict[str, Any]]:
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
    return capsule, _read_payload(capsule)


def _read_payload(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SessionCapsuleValidationError("session capsule is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise SessionCapsuleValidationError("session capsule root must be an object")
    return payload


def _unsafe_metadata(path: Path) -> tuple[str | None, str | None]:
    try:
        payload = _read_payload(path)
    except SessionCapsuleValidationError:
        return None, None
    return payload.get("session_id") if isinstance(payload.get("session_id"), str) else None, payload.get("schema_version") if isinstance(payload.get("schema_version"), str) else None


def _assert_no_protected_or_secret_content(payload: Mapping[str, Any]) -> None:
    try:
        assert_aggregate_only(payload)
    except ValueError as exc:
        raise SessionCapsuleValidationError(str(exc)) from exc
    if _SECRET_RE.search(json.dumps(payload, ensure_ascii=True, sort_keys=True)):
        raise SessionCapsuleValidationError("session capsule contains a credential or secret")


def _required(payload: Mapping[str, Any], key: str, expected: object) -> None:
    if payload.get(key) != expected:
        raise SessionCapsuleValidationError(f"{key} must be {expected!r}")


def _exact_keys(value: Mapping[str, Any], expected: frozenset[str], label: str) -> None:
    if set(value) != expected:
        raise SessionCapsuleValidationError(f"{label} keys are invalid")


def _required_string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SessionCapsuleValidationError(f"{key} must be a non-empty string")
    return value


def _thai_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or not _THAI_RE.search(value):
        raise SessionCapsuleValidationError(f"{label} must be non-empty Thai text")
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
    return None if payload.get(key) is None else _timestamp(payload, key)


def _provenance(value: str, label: str) -> None:
    if value not in PROVENANCE_VALUES:
        raise SessionCapsuleValidationError(f"{label} is invalid")


def _validate_owner_approvals(value: Any, *, strict: bool = False) -> None:
    if not isinstance(value, list):
        raise SessionCapsuleValidationError("owner_approvals must be a list")
    for approval in value:
        if not isinstance(approval, dict):
            raise SessionCapsuleValidationError("owner approval must be an object")
        if strict:
            _exact_keys(approval, frozenset({"gate", "source", "scope"}), "owner approval")
        if not _GATE_RE.fullmatch(_required_string(approval, "gate")):
            raise SessionCapsuleValidationError("owner approval gate is invalid")
        _required_string(approval, "source")
        _required_string(approval, "scope")


def _validate_repository(value: Any, *, strict: bool = False) -> str:
    if not isinstance(value, dict) or value.get("path") != ".":
        raise SessionCapsuleValidationError("repository.path must be '.'")
    if strict:
        _exact_keys(value, frozenset({"path", "revision", "dirty_paths"}), "repository")
    revision = _required_string(value, "revision")
    try:
        validate_full_git_commit(revision, field_name="repository.revision")
    except IdentityValidationError as exc:
        raise SessionCapsuleValidationError(str(exc)) from exc
    dirty = value.get("dirty_paths")
    if not isinstance(dirty, list) or any(not isinstance(path, str) for path in dirty):
        raise SessionCapsuleValidationError("repository.dirty_paths must be a list of strings")
    return revision


def _validate_events_v1(value: Any, root: Path, revision: str) -> int:
    return _validate_events(value, root, revision, strict=False)


def _validate_events_v2(value: Any, root: Path, revision: str) -> int:
    return _validate_events(value, root, revision, strict=True)


def _validate_events(value: Any, root: Path, revision: str, *, strict: bool) -> int:
    if not isinstance(value, list):
        raise SessionCapsuleValidationError("events must be a list")
    reference_count = 0
    for expected_sequence, event in enumerate(value, start=1):
        if not isinstance(event, dict):
            raise SessionCapsuleValidationError("event must be an object")
        if strict:
            _exact_keys(event, V2_EVENT_KEYS, "v2 event")
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
            _validate_reference(reference, root, revision, strict=strict)
            reference_count += 1
        if strict:
            _validate_quantitative_claims(event["quantitative_claims"], refs)
    return reference_count


def _validate_reference(value: Any, root: Path, revision: str, *, strict: bool = False) -> None:
    if not isinstance(value, dict):
        raise SessionCapsuleValidationError("evidence reference must be an object")
    if strict:
        _exact_keys(value, frozenset({"path", "sha256", "locator"}), "evidence reference")
    relative = _repository_relative_path(_required_string(value, "path"))
    expected_hash = _required_string(value, "sha256")
    if not _SHA256_RE.fullmatch(expected_hash):
        raise SessionCapsuleValidationError("evidence reference sha256 must be lowercase SHA-256")
    _required_string(value, "locator")
    completed = subprocess.run(["git", "show", f"{revision}:{relative}"], cwd=root, capture_output=True, check=False)
    if completed.returncode != 0:
        raise SessionCapsuleValidationError(f"evidence reference is absent at recorded revision: {relative}")
    if hashlib.sha256(completed.stdout).hexdigest() != expected_hash:
        raise SessionCapsuleValidationError(f"evidence reference hash mismatch: {relative}")


def _repository_relative_path(value: str) -> str:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or ":" in path.parts[0] or any(part in {"", ".", ".."} for part in path.parts):
        raise SessionCapsuleValidationError("evidence reference path must be repository-relative")
    return path.as_posix()


def _validate_quantitative_claims(value: Any, event_refs: list[Any]) -> None:
    if not isinstance(value, list):
        raise SessionCapsuleValidationError("quantitative_claims must be a list")
    available = {json.dumps(reference, ensure_ascii=True, sort_keys=True) for reference in event_refs}
    seen: set[str] = set()
    for claim in value:
        if not isinstance(claim, dict):
            raise SessionCapsuleValidationError("quantitative claim must be an object")
        _exact_keys(claim, QUANTITATIVE_CLAIM_KEYS, "quantitative claim")
        claim_id = _required_string(claim, "claim_id")
        if claim_id in seen:
            raise SessionCapsuleValidationError("quantitative claim IDs must be unique")
        seen.add(claim_id)
        _required_string(claim, "statement")
        if isinstance(claim["value"], bool) or not isinstance(claim["value"], (int, float)):
            raise SessionCapsuleValidationError("quantitative claim value must be numeric")
        _required_string(claim, "unit")
        reference = claim["evidence_ref"]
        if json.dumps(reference, ensure_ascii=True, sort_keys=True) not in available:
            raise SessionCapsuleValidationError("quantitative claim must bind an event evidence reference")


def _validate_v2_closeout(payload: Mapping[str, Any], root: Path, revision: str) -> int:
    snapshot = payload["execution_snapshot"]
    if not isinstance(snapshot, dict):
        raise SessionCapsuleValidationError("execution_snapshot must be an object")
    _exact_keys(snapshot, SNAPSHOT_KEYS, "execution_snapshot")
    phase_id = _required_string(snapshot, "phase_id")
    task_id = _required_string(snapshot, "task_id")
    gate_id = _required_string(snapshot, "gate_id")
    if snapshot["gate_status"] not in {"pending", "approved", "rejected", "deferred", "blocked"}:
        raise SessionCapsuleValidationError("execution_snapshot gate_status is invalid")
    _validate_plan_binding(root, phase_id, task_id, gate_id)
    _thai_string(payload["owner_brief_th"], "owner_brief_th")
    _validate_owner_actions(payload["owner_actions"])
    reference_count = _validate_gate_request(payload["gate_request"], root, revision, gate_id)
    _validate_next_resources(payload["next_resources"])
    _validate_closeout(payload["closeout"])
    _validate_corrections(payload["corrections"])
    return reference_count


def _validate_plan_binding(root: Path, phase_id: str, task_id: str, gate_id: str) -> None:
    phase_aliases = {f"P{index}": name for index, name in enumerate((
        "P0_FOUNDATION", "P1_CPU_BASELINE", "P2_SCOPE_DEVELOPMENT", "P3_FINAL", "P4_PUBLICATION"
    ))}
    task_prefix = task_id.split(".", 1)[0] if _TASK_RE.fullmatch(task_id) else ""
    if not _TASK_RE.fullmatch(task_id) or phase_id != phase_aliases.get(task_prefix, task_prefix) or not _GATE_RE.fullmatch(gate_id):
        raise SessionCapsuleValidationError("execution_snapshot phase, task, or gate is invalid")
    if (phase_id, task_id, gate_id) == ("V0", "V0.1", "D1_START_CAMPAIGN"):
        return
    current_task: str | None = None
    bindings: dict[str, tuple[str, str]] = {}
    for line in (root / "PLAN.md").read_text(encoding="utf-8").splitlines():
        task_match = _PLAN_TASK_RE.match(line)
        if task_match:
            current_task = task_match.group(1)
            continue
        gate_match = _PLAN_GATE_RE.match(line)
        if current_task and gate_match:
            bindings[current_task] = (phase_aliases.get(current_task.split(".", 1)[0], current_task.split(".", 1)[0]), gate_match.group(1))
            current_task = None
    expected_binding = bindings.get(task_id)
    # P0/P1 implementation tasks run under the single standing D1
    # authorization; they do not create a recurring Owner micro-gate.
    if expected_binding is None and task_id in {"P0.3", "P1.3"}:
        expected_binding = (phase_id, "D1_START_CAMPAIGN")
    if expected_binding != (phase_id, gate_id):
        raise SessionCapsuleValidationError("execution_snapshot does not match PLAN.md")


def _validate_owner_actions(value: Any) -> None:
    if not isinstance(value, list) or not value:
        raise SessionCapsuleValidationError("owner_actions must be a non-empty list")
    seen: set[str] = set()
    for action in value:
        if not isinstance(action, dict):
            raise SessionCapsuleValidationError("owner action must be an object")
        _exact_keys(action, OWNER_ACTION_KEYS, "owner action")
        action_id = _required_string(action, "action_id")
        if action_id in seen:
            raise SessionCapsuleValidationError("owner action IDs must be unique")
        seen.add(action_id)
        if action["priority"] not in {"required", "optional"}:
            raise SessionCapsuleValidationError("owner action priority is invalid")
        _thai_string(action["action_th"], "owner action action_th")
        _thai_string(action["reason_th"], "owner action reason_th")
        gate = action["blocking_gate"]
        if gate is not None and (not isinstance(gate, str) or not _GATE_RE.fullmatch(gate)):
            raise SessionCapsuleValidationError("owner action blocking_gate is invalid")


def _validate_gate_request(value: Any, root: Path, revision: str, snapshot_gate: str) -> int:
    if not isinstance(value, dict):
        raise SessionCapsuleValidationError("gate_request must be an object")
    _exact_keys(value, GATE_REQUEST_KEYS, "gate_request")
    if value["gate_id"] != snapshot_gate or not _GATE_RE.fullmatch(str(value["gate_id"])):
        raise SessionCapsuleValidationError("gate_request gate_id must match execution_snapshot")
    state = value["state"]
    if state not in {"draft", "blocked", "ready_for_decision"}:
        raise SessionCapsuleValidationError("gate_request state is invalid")
    _thai_string(value["summary_th"], "gate_request summary_th")
    blocking_reason = value["blocking_reason_th"]
    if state == "blocked":
        _thai_string(blocking_reason, "gate_request blocking_reason_th")
    elif blocking_reason is not None:
        raise SessionCapsuleValidationError("non-blocked gate_request must not include blocking_reason_th")
    refs = value["evidence_refs"]
    if not isinstance(refs, list):
        raise SessionCapsuleValidationError("gate_request evidence_refs must be a list")
    if state == "ready_for_decision" and not refs:
        raise SessionCapsuleValidationError("ready_for_decision requires evidence_refs")
    for reference in refs:
        _validate_reference(reference, root, revision, strict=True)
    return len(refs)


def _validate_next_resources(value: Any) -> None:
    if not isinstance(value, dict):
        raise SessionCapsuleValidationError("next_resources must be an object")
    _exact_keys(value, NEXT_RESOURCES_KEYS, "next_resources")
    status = value["status"]
    items = value["items"]
    if status not in {"required", "none"} or not isinstance(items, list):
        raise SessionCapsuleValidationError("next_resources status or items is invalid")
    if (status == "required" and not items) or (status == "none" and items):
        raise SessionCapsuleValidationError("next_resources status must agree with items")
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise SessionCapsuleValidationError("next resource must be an object")
        _exact_keys(item, NEXT_RESOURCE_KEYS, "next resource")
        resource_id = _required_string(item, "resource_id")
        if resource_id in seen:
            raise SessionCapsuleValidationError("next resource IDs must be unique")
        seen.add(resource_id)
        _thai_string(item["description_th"], "next resource description_th")
        _thai_string(item["purpose_th"], "next resource purpose_th")


def _validate_closeout(value: Any) -> None:
    if not isinstance(value, dict):
        raise SessionCapsuleValidationError("closeout must be an object")
    _exact_keys(value, CLOSEOUT_KEYS, "closeout")
    checks = value["checks"]
    if not isinstance(checks, list) or not checks:
        raise SessionCapsuleValidationError("closeout checks must be a non-empty list")
    seen_checks: set[str] = set()
    for check in checks:
        if not isinstance(check, dict):
            raise SessionCapsuleValidationError("closeout check must be an object")
        _exact_keys(check, CHECK_KEYS, "closeout check")
        check_id = _required_string(check, "check_id")
        if check_id in seen_checks:
            raise SessionCapsuleValidationError("closeout check IDs must be unique")
        seen_checks.add(check_id)
        if check["status"] not in {"PASS", "FAIL", "BLOCKED", "SKIPPED"}:
            raise SessionCapsuleValidationError("closeout check status is invalid")
        _required_string(check, "summary")
    changed_files = value["changed_files"]
    if not isinstance(changed_files, list) or any(not isinstance(path, str) for path in changed_files):
        raise SessionCapsuleValidationError("closeout changed_files must be a list of strings")
    if len({_repository_relative_path(path) for path in changed_files}) != len(changed_files):
        raise SessionCapsuleValidationError("closeout changed_files must be unique repository-relative paths")
    surfaces = value["untouched_protected_surfaces"]
    if not isinstance(surfaces, list) or not surfaces or any(not isinstance(item, str) or not item.strip() for item in surfaces):
        raise SessionCapsuleValidationError("closeout must list untouched protected surfaces")


def _validate_corrections(value: Any) -> None:
    if not isinstance(value, list):
        raise SessionCapsuleValidationError("corrections must be a list")
    seen: set[str] = set()
    for correction in value:
        if not isinstance(correction, dict):
            raise SessionCapsuleValidationError("correction must be an object")
        _exact_keys(correction, CORRECTION_KEYS, "correction")
        session_id = _required_string(correction, "target_session_id")
        if not _SESSION_ID_RE.fullmatch(session_id) or session_id in seen:
            raise SessionCapsuleValidationError("correction target_session_id is invalid or duplicated")
        seen.add(session_id)
        _required_string(correction, "observed_validation_error")
        _thai_string(correction["correction_th"], "correction correction_th")


def _validate_run_artifacts(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != RUN_ARTIFACT_KEYS:
        raise SessionCapsuleValidationError("run_artifacts must contain the exact session-artifact keys")
    for key, item in value.items():
        if key == "mlflow_receipts":
            if not isinstance(item, list) or any(not isinstance(entry, str) for entry in item):
                raise SessionCapsuleValidationError("run_artifacts.mlflow_receipts must be a list of strings")
        elif item is not None and not isinstance(item, str):
            raise SessionCapsuleValidationError(f"run_artifacts.{key} must be a string or null")


def _validate_open_threads(value: Any, *, strict: bool = False) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise SessionCapsuleValidationError("open_threads must be a list")
    for thread in value:
        if not isinstance(thread, dict):
            raise SessionCapsuleValidationError("open thread must be an object")
        if strict:
            _exact_keys(thread, frozenset({"thread_id", "provenance", "summary", "blocking_gate"}), "open thread")
        _required_string(thread, "thread_id")
        _provenance(_required_string(thread, "provenance"), "open thread provenance")
        _required_string(thread, "summary")
        gate = thread.get("blocking_gate")
        if gate is not None and (not isinstance(gate, str) or not _GATE_RE.fullmatch(gate)):
            raise SessionCapsuleValidationError("open thread blocking_gate is invalid")
    return value


def _validate_integrity(value: Any) -> None:
    expected = {"all_refs_exist": True, "all_hashes_match": True, "contains_protected_payload": False, "contains_secrets": False}
    if value != expected:
        raise SessionCapsuleValidationError("integrity must report complete references and no protected content or secrets")
