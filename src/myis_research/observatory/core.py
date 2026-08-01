"""Deterministic, aggregate-only evidence registry and capture lifecycle.

The module deliberately uses plain dictionaries at the boundary. This keeps
future runners independent of a UI framework while making every record easy to
serialize, validate, and hash.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from ..protection import assert_aggregate_only


REGISTRY_SCHEMA = "myis.observatory-registry.v1"
RECEIPT_SCHEMA = "myis.observatory-receipt.v1"
EVENT_SCHEMA = "myis.observatory-event.v1"
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
_ID_RE = re.compile(r"^[a-z][a-z0-9._-]{2,127}$")
_SAFE_URI_RE = re.compile(r"^(?:git|owner-local|external-store|brain|mlflow)://[A-Za-z0-9._/-]+$")
_ABSOLUTE_RE = re.compile(r"(?:^[A-Za-z]:[\\/]|^/|^\\\\)")
_FORBIDDEN_WORD_RE = re.compile(
    r"(?:query[_ -]?ids?|split[_ -]?membership|per[_ -]?query|raw[_ -]?provider|credentials?|api[_ -]?keys?)",
    re.IGNORECASE,
)
EVIDENCE_CLASSES = frozenset({"fixture", "dry_run", "measured_development", "measured_selection", "confirmatory", "publication"})
CLAIM_BOUNDARIES = frozenset({"engineering_provenance_only", "no_measured_claim", "aggregate_only", "train_selection_only", "confirmatory_only", "publication_only"})
RUN_STATUSES = frozenset({"planned", "running", "succeeded", "failed", "interrupted", "cancelled"})


class ObservatoryError(ValueError):
    """Raised when an observatory record would violate its boundary."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else canonical_json(value)).hexdigest()


def _record_hash(record: Mapping[str, Any], field_name: str = "record_sha256") -> str:
    return canonical_sha256({key: value for key, value in record.items() if key != field_name})


def _require_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise ObservatoryError(f"{label} must be a stable lower-case ID")
    return value


def _require_hash(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ObservatoryError(f"{label} must be a lowercase SHA-256")
    return value


def _safe_scan(value: Any, *, path: str = "$") -> None:
    try:
        assert_aggregate_only(value, path=path)
    except ValueError as error:
        raise ObservatoryError(str(error)) from error
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if _FORBIDDEN_WORD_RE.search(key_text) and not key_text.lower().endswith(("_sha256", "_hash")):
                raise ObservatoryError(f"protected field is forbidden at {path}.{key_text}")
            _safe_scan(item, path=f"{path}.{key_text}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _safe_scan(item, path=f"{path}[{index}]")
    elif isinstance(value, str) and _ABSOLUTE_RE.match(value):
        raise ObservatoryError(f"absolute path is forbidden at {path}")


def _base(schema_version: str, record_id: str, *, evidence_class: str, scientific_authority: bool, claim_boundary: str, summary: str, **fields: Any) -> dict[str, Any]:
    _require_id(record_id, "record_id")
    if evidence_class not in EVIDENCE_CLASSES:
        raise ObservatoryError("evidence_class is invalid")
    if claim_boundary not in CLAIM_BOUNDARIES:
        raise ObservatoryError("claim_boundary is invalid")
    if not isinstance(scientific_authority, bool) or not isinstance(summary, str) or not summary.strip():
        raise ObservatoryError("scientific_authority and summary are required")
    record = {
        "schema_version": schema_version,
        "record_id": record_id,
        "evidence_class": evidence_class,
        "scientific_authority": scientific_authority,
        "claim_boundary": claim_boundary,
        "summary": summary.strip(),
        **fields,
    }
    _safe_scan(record)
    record["record_sha256"] = _record_hash(record)
    return record


def build_standard_record(record_type: str, record_id: str, *, evidence_class: str = "fixture", scientific_authority: bool = False, claim_boundary: str = "engineering_provenance_only", summary: str, **fields: Any) -> dict[str, Any]:
    return _base(f"myis.observatory-{record_type}.v1", record_id, evidence_class=evidence_class, scientific_authority=scientific_authority, claim_boundary=claim_boundary, summary=summary, **fields)


def build_run_record(run_id: str, *, request_id: str, phase_id: str, task_id: str, status: str = "planned", execution_class: str = "fixture", evidence_class: str = "fixture", scientific_authority: bool = False, claim_boundary: str = "engineering_provenance_only", git_commit: str = "0" * 40, request_sha256: str = "0" * 64, profile_sha256: str = "0" * 64, envelope_sha256: str = "0" * 64, environment_sha256: str = "0" * 64, config_sha256: str = "0" * 64, prompt_ids: Iterable[str] = (), candidate_ids: Iterable[str] = (), artifact_ids: Iterable[str] = (), counters_before: Mapping[str, int] | None = None, counters_after: Mapping[str, int] | None = None, started_at: str = "1970-01-01T00:00:00Z", ended_at: str | None = None, exit_code: int | None = None, summary: str = "Observatory run", **fields: Any) -> dict[str, Any]:
    if status not in RUN_STATUSES:
        raise ObservatoryError("run status is invalid")
    for label, value in (("request_sha256", request_sha256), ("profile_sha256", profile_sha256), ("envelope_sha256", envelope_sha256), ("environment_sha256", environment_sha256), ("config_sha256", config_sha256)):
        _require_hash(value, label)
    return _base("myis.observatory-run.v1", run_id, evidence_class=evidence_class, scientific_authority=scientific_authority, claim_boundary=claim_boundary, summary=summary, request_id=_require_id(request_id, "request_id"), phase_id=phase_id, task_id=task_id, status=status, execution_class=execution_class, git_commit=git_commit, request_sha256=request_sha256, profile_sha256=profile_sha256, envelope_sha256=envelope_sha256, environment_sha256=environment_sha256, config_sha256=config_sha256, prompt_ids=sorted(set(prompt_ids)), candidate_ids=sorted(set(candidate_ids)), artifact_ids=sorted(set(artifact_ids)), counters_before=dict(counters_before or {}), counters_after=dict(counters_after or {}), started_at=started_at, ended_at=ended_at, exit_code=exit_code, **fields)


def build_artifact_record(artifact_id: str, *, title: str, artifact_type: str, producing_run_id: str, safe_uri: str, size_bytes: int, content_sha256: str, evidence_class: str = "fixture", scientific_authority: bool = False, claim_boundary: str = "engineering_provenance_only", validation_status: str = "validated", parent_artifact_ids: Iterable[str] = (), summary: str, **fields: Any) -> dict[str, Any]:
    _require_id(producing_run_id, "producing_run_id")
    if not _SAFE_URI_RE.fullmatch(safe_uri) or ".." in safe_uri:
        raise ObservatoryError("safe_uri is not an allowlisted relative pointer")
    if not isinstance(size_bytes, int) or size_bytes < 0:
        raise ObservatoryError("size_bytes must be a non-negative integer")
    _require_hash(content_sha256, "content_sha256")
    return _base("myis.observatory-artifact.v1", artifact_id, evidence_class=evidence_class, scientific_authority=scientific_authority, claim_boundary=claim_boundary, summary=summary, title=title, artifact_type=artifact_type, producing_run_id=producing_run_id, safe_uri=safe_uri, size_bytes=size_bytes, content_sha256=content_sha256, validation_status=validation_status, parent_artifact_ids=sorted(set(parent_artifact_ids)), **fields)


def build_prompt_record(prompt_id: str, *, version: str, family: str, role: str, content_sha256: str, frozen: bool, source_uri: str, candidate_ids: Iterable[str] = (), parent_prompt_id: str | None = None, evidence_class: str = "fixture", scientific_authority: bool = False, summary: str, **fields: Any) -> dict[str, Any]:
    _require_hash(content_sha256, "content_sha256")
    if not _SAFE_URI_RE.fullmatch(source_uri) or ".." in source_uri:
        raise ObservatoryError("prompt source_uri is unsafe")
    return _base("myis.observatory-prompt.v1", prompt_id, evidence_class=evidence_class, scientific_authority=scientific_authority, claim_boundary="engineering_provenance_only", summary=summary, version=version, family=family, role=role, content_sha256=content_sha256, frozen=bool(frozen), source_uri=source_uri, candidate_ids=sorted(set(candidate_ids)), parent_prompt_id=parent_prompt_id, **fields)


def build_metric_record(metric_id: str, *, name: str, cutoff: int, direction: str, data_role: str, scope: str, evidence_role: str, value: float, n: int, denominator: str, run_id: str, candidate_id: str | None = None, result_id: str | None = None, evidence_class: str = "fixture", scientific_authority: bool = False, claim_boundary: str = "engineering_provenance_only", uncertainty: Mapping[str, Any] | None = None, summary: str, **fields: Any) -> dict[str, Any]:
    if not isinstance(cutoff, int) or cutoff <= 0 or not isinstance(n, int) or n < 0 or not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ObservatoryError("metric numeric identity is invalid")
    if direction not in {"maximize", "minimize"} or not name or not data_role or not scope or not evidence_role:
        raise ObservatoryError("metric identity is incomplete")
    return _base("myis.observatory-metric.v1", metric_id, evidence_class=evidence_class, scientific_authority=scientific_authority, claim_boundary=claim_boundary, summary=summary, name=name, cutoff=cutoff, direction=direction, data_role=data_role, scope=scope, evidence_role=evidence_role, value=float(value), n=n, denominator=denominator, run_id=_require_id(run_id, "run_id"), candidate_id=candidate_id, result_id=result_id, uncertainty=dict(uncertainty or {}), **fields)


def build_result_record(result_id: str, *, run_id: str, output_artifact_ids: Iterable[str], metric_ids: Iterable[str], validity: str, evidence_maturity: str, supports: str, does_not_support: str, evidence_class: str = "fixture", scientific_authority: bool = False, claim_boundary: str = "engineering_provenance_only", summary: str, **fields: Any) -> dict[str, Any]:
    return _base("myis.observatory-result.v1", result_id, evidence_class=evidence_class, scientific_authority=scientific_authority, claim_boundary=claim_boundary, summary=summary, run_id=_require_id(run_id, "run_id"), output_artifact_ids=sorted(set(output_artifact_ids)), metric_ids=sorted(set(metric_ids)), validity=validity, evidence_maturity=evidence_maturity, supports=supports, does_not_support=does_not_support, **fields)


def build_decision_record(decision_id: str, *, result_id: str, status: str, next_action: str, evidence_class: str = "fixture", scientific_authority: bool = False, claim_boundary: str = "engineering_provenance_only", summary: str, **fields: Any) -> dict[str, Any]:
    return _base("myis.observatory-decision.v1", decision_id, evidence_class=evidence_class, scientific_authority=scientific_authority, claim_boundary=claim_boundary, summary=summary, result_id=_require_id(result_id, "result_id"), status=status, next_action=next_action, **fields)


def build_failure_record(failure_id: str, *, run_id: str, stage: str, reason: str, checkpoint: str, retryable: bool, partial_artifact_ids: Iterable[str], recovery_id: str | None, counters_changed: bool, evidence_class: str = "fixture", scientific_authority: bool = False, claim_boundary: str = "engineering_provenance_only", summary: str, **fields: Any) -> dict[str, Any]:
    return _base("myis.observatory-failure.v1", failure_id, evidence_class=evidence_class, scientific_authority=scientific_authority, claim_boundary=claim_boundary, summary=summary, run_id=_require_id(run_id, "run_id"), stage=stage, reason=reason, checkpoint=checkpoint, retryable=bool(retryable), partial_artifact_ids=sorted(set(partial_artifact_ids)), recovery_id=recovery_id, counters_changed=bool(counters_changed), **fields)


@dataclass
class EvidenceRegistry:
    """Append-only registry with deterministic serialization."""

    registry_id: str = "observatory-fixture-v1"
    created_at: str = "2026-01-01T00:00:00Z"
    records: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: {})
    events: list[dict[str, Any]] = field(default_factory=list)

    def add(self, kind: str, record: Mapping[str, Any]) -> dict[str, Any]:
        item = dict(record)
        validate_record(item)
        existing = [entry.get("record_id") for entry in self.records.get(kind, [])]
        if item["record_id"] in existing:
            raise ObservatoryError(f"duplicate record ID: {item['record_id']}")
        self.records.setdefault(kind, []).append(item)
        self.records[kind].sort(key=lambda value: str(value["record_id"]))
        return item

    def event(self, event_id: str, *, event_type: str, run_id: str, stage: str, status: str, timestamp: str = "2026-01-01T00:00:00Z", details: Mapping[str, Any] | None = None) -> dict[str, Any]:
        _require_id(event_id, "event_id")
        event = {"schema_version": EVENT_SCHEMA, "event_id": event_id, "event_type": event_type, "run_id": run_id, "stage": stage, "status": status, "timestamp": timestamp, "details": dict(details or {})}
        _safe_scan(event)
        event["event_sha256"] = _record_hash(event, "event_sha256")
        if event_id in {str(item.get("event_id")) for item in self.events}:
            raise ObservatoryError(f"duplicate event ID: {event_id}")
        self.events.append(event)
        self.events.sort(key=lambda value: str(value["event_id"]))
        return event

    def as_dict(self) -> dict[str, Any]:
        body = {"schema_version": REGISTRY_SCHEMA, "registry_id": self.registry_id, "created_at": self.created_at, "records": {key: list(self.records[key]) for key in sorted(self.records)}, "events": list(self.events)}
        body["registry_sha256"] = _record_hash(body, "registry_sha256")
        return body

    def validate(self) -> None:
        validate_registry(self.as_dict())

    def write(self, path: Path) -> Path:
        self.validate()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.as_dict(), ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path


def validate_record(record: Mapping[str, Any]) -> None:
    if not isinstance(record, Mapping) or not isinstance(record.get("schema_version"), str) or not isinstance(record.get("record_id"), str):
        raise ObservatoryError("record identity is incomplete")
    _require_id(str(record["record_id"]), "record_id")
    _require_hash(record.get("record_sha256"), "record_sha256")
    if _record_hash(record) != record["record_sha256"]:
        raise ObservatoryError(f"record hash mismatch: {record['record_id']}")
    if record.get("evidence_class") not in EVIDENCE_CLASSES:
        raise ObservatoryError("record evidence_class is invalid")
    if not isinstance(record.get("scientific_authority"), bool):
        raise ObservatoryError("record scientific_authority must be boolean")
    if record.get("claim_boundary") not in CLAIM_BOUNDARIES:
        raise ObservatoryError("record claim_boundary is invalid")
    _safe_scan(record)


def validate_registry(registry: Mapping[str, Any]) -> None:
    if not isinstance(registry, Mapping) or registry.get("schema_version") != REGISTRY_SCHEMA:
        raise ObservatoryError("registry schema_version is invalid")
    _require_id(registry.get("registry_id"), "registry_id")
    records = registry.get("records")
    if not isinstance(records, Mapping):
        raise ObservatoryError("registry records must be an object")
    ids: set[str] = set()
    for kind, items in records.items():
        if not isinstance(kind, str) or not isinstance(items, list):
            raise ObservatoryError("registry record families are invalid")
        for item in items:
            validate_record(item)
            item_id = str(item["record_id"])
            if item_id in ids:
                raise ObservatoryError(f"duplicate registry ID: {item_id}")
            ids.add(item_id)
    for event in registry.get("events", []):
        if not isinstance(event, Mapping) or _record_hash(event, "event_sha256") != event.get("event_sha256"):
            raise ObservatoryError("event hash mismatch")
        _safe_scan(event)
    recorded = registry.get("registry_sha256")
    _require_hash(recorded, "registry_sha256")
    if _record_hash(registry, "registry_sha256") != recorded:
        raise ObservatoryError("registry hash mismatch")
    _safe_scan(registry)


@dataclass
class CaptureSession:
    """Small reusable lifecycle wrapper for future runners."""

    registry: EvidenceRegistry
    run_id: str
    request_id: str
    phase_id: str
    task_id: str
    run: dict[str, Any] | None = None

    def start(self, **kwargs: Any) -> dict[str, Any]:
        if self.run is not None:
            raise ObservatoryError("capture session already started")
        self.run = self.registry.add(
            "runs",
            build_run_record(self.run_id, request_id=self.request_id, phase_id=self.phase_id, task_id=self.task_id, status="planned", **kwargs),
        )
        self.registry.event(f"{self.run_id}-planned", event_type="run_planned", run_id=self.run_id, stage="pre_run", status="planned")
        return self.run

    def transition(self, stage: str, status: str = "running", **details: Any) -> None:
        if self.run is None:
            raise ObservatoryError("capture session has not started")
        self.registry.event(f"{self.run_id}-{stage}-{status}", event_type="stage_transition", run_id=self.run_id, stage=stage, status=status, details=details)
        self.run["status"] = status
        self.run["record_sha256"] = _record_hash(self.run)

    def register_artifact(self, artifact: Mapping[str, Any]) -> None:
        if self.run is None:
            raise ObservatoryError("capture session has not started")
        self.registry.add("artifacts", artifact)
        self.run.setdefault("artifact_ids", []).append(artifact["record_id"])
        self.run["artifact_ids"] = sorted(set(self.run["artifact_ids"]))
        self.run["record_sha256"] = _record_hash(self.run)

    def finish(self, *, ended_at: str = "2026-01-01T00:00:10Z", exit_code: int = 0) -> dict[str, Any]:
        if self.run is None:
            raise ObservatoryError("capture session has not started")
        self.run["status"] = "succeeded"
        self.run["ended_at"] = ended_at
        self.run["exit_code"] = exit_code
        self.run["record_sha256"] = _record_hash(self.run)
        self.registry.event(f"{self.run_id}-finished", event_type="run_finished", run_id=self.run_id, stage="post_run", status="succeeded")
        self.registry.validate()
        return self.run

    def fail(self, failure: Mapping[str, Any], *, ended_at: str = "2026-01-01T00:00:10Z") -> dict[str, Any]:
        if self.run is None:
            raise ObservatoryError("capture session has not started")
        self.registry.add("failures", failure)
        self.run["status"] = "failed"
        self.run["ended_at"] = ended_at
        self.run["exit_code"] = 1
        self.run["record_sha256"] = _record_hash(self.run)
        self.registry.event(f"{self.run_id}-failed", event_type="run_failed", run_id=self.run_id, stage=str(failure.get("stage", "unknown")), status="failed")
        return self.run
