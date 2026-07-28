"""Strict browser and dashboard projection contracts."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DecisionBudget(StrictModel):
    max_cost_usd: float | None = Field(default=None, ge=0)
    max_tokens: int | None = Field(default=None, ge=0)
    max_wall_clock_minutes: int | None = Field(default=None, ge=1)
    max_trials: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def require_a_limit(self) -> "DecisionBudget":
        if all(value is None for value in self.model_dump().values()):
            raise ValueError("a budget must contain at least one limit")
        return self


DecisionAction = Literal[
    "approve_implementation",
    "approve_documentation_migration",
    "approve_cleanup",
    "authorize_reproduction",
    "authorize_track_c_development",
    "freeze_track_c",
    "authorize_track_r_development",
    "authorize_harnessopt",
    "authorize_confirmation",
    "authorize_transfer",
    "authorize_publication",
    "anchor_pdf_receipt_chain",
]


class DecisionScope(StrictModel):
    action: DecisionAction
    phase_ids: tuple[str, ...] = ()
    task_ids: tuple[str, ...] = ()
    targets: tuple[str, ...] = ()
    budget: DecisionBudget | None = None

    @field_validator("phase_ids", "task_ids", "targets")
    @classmethod
    def sorted_unique_values(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if tuple(sorted(set(values))) != values:
            raise ValueError("scope values must be sorted and unique")
        return values

    @field_validator("targets")
    @classmethod
    def validate_targets(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        for value in values:
            if not value or len(value) > 240 or "\x00" in value:
                raise ValueError("scope target is invalid")
            normalized = value.replace("\\", "/")
            if normalized.startswith("/") or ":" in normalized.split("/")[0]:
                raise ValueError("scope targets must be repository-relative")
            if any(part in {"", ".", ".."} for part in normalized.split("/")):
                raise ValueError("scope targets cannot traverse directories")
        return values

    @model_validator(mode="after")
    def require_named_scope(self) -> "DecisionScope":
        if not (self.phase_ids or self.task_ids or self.targets):
            raise ValueError("Owner decisions require a named phase, task, or target scope")
        if self.action == "approve_cleanup" and not self.targets:
            raise ValueError("cleanup approval requires exact repository-relative targets")
        return self


class OwnerGateDecisionRecord(StrictModel):
    schema_version: Literal["myis.owner-gate-decision.v2"]
    decision_id: str = Field(min_length=2, max_length=160, pattern=r"^[A-Za-z0-9_-]+$")
    gate_id: Literal["G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"]
    status: Literal["approved", "rejected", "deferred"]
    rationale: str = Field(min_length=3, max_length=4000)
    timestamp: str = Field(min_length=20, max_length=64)
    actor: str
    display_label: str | None = Field(default=None, max_length=120)
    evidence_manifest_hashes: tuple[str, ...] = ()
    git_commit: str = Field(min_length=40, max_length=64, pattern=r"^[0-9a-f]+$")
    scope: DecisionScope
    scope_hash: str
    prior_record_hash: str | None = None
    supersedes_decision_id: str | None = Field(
        default=None, min_length=2, max_length=160, pattern=r"^[A-Za-z0-9_-]+$"
    )

    @field_validator("actor", "scope_hash")
    @classmethod
    def validate_required_sha256(cls, value: str) -> str:
        _sha256(value)
        return value

    @field_validator("prior_record_hash")
    @classmethod
    def validate_optional_sha256(cls, value: str | None) -> str | None:
        if value is not None:
            _sha256(value)
        return value

    @field_validator("evidence_manifest_hashes")
    @classmethod
    def validate_evidence_hashes(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if tuple(sorted(set(values))) != values:
            raise ValueError("evidence hashes must be sorted and unique")
        for value in values:
            _sha256(value)
        return values

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("timestamp must be ISO-8601") from error
        if parsed.tzinfo is None:
            raise ValueError("timestamp must include a timezone")
        return value

    @model_validator(mode="after")
    def validate_scope_hash(self) -> "OwnerGateDecisionRecord":
        scope = self.scope.model_dump(mode="json", exclude_none=True)
        encoded = json.dumps(scope, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode(
            "utf-8"
        )
        expected = hashlib.sha256(encoded).hexdigest()
        if self.scope_hash != expected:
            raise ValueError("scope_hash does not match the canonical typed scope")
        return self


class DecisionPreviewRequest(StrictModel):
    gate_id: Literal["G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"]
    status: Literal["approved", "rejected", "deferred"]
    rationale: str = Field(min_length=3, max_length=4000)
    evidence_manifest_hashes: tuple[str, ...] = ()
    scope: DecisionScope
    supersedes_decision_id: str | None = Field(
        default=None, min_length=2, max_length=160, pattern=r"^[A-Za-z0-9_-]+$"
    )
    display_label: str | None = Field(default=None, max_length=120)

    @field_validator("evidence_manifest_hashes")
    @classmethod
    def validate_hashes(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(sorted(set(values)))
        if len(normalized) != len(values):
            raise ValueError("evidence hashes must be sorted and unique")
        for value in values:
            _sha256(value)
        return values

class DecisionConfirmRequest(StrictModel):
    preview_token: str = Field(min_length=32, max_length=256)
    confirm: Literal[True]


class PdfAccessRequest(StrictModel):
    artifact_id: str = Field(min_length=2, max_length=128, pattern=r"^[A-Za-z0-9._-]+$")
    purpose: str = Field(min_length=3, max_length=500)


class TaskEvidenceCheck(StrictModel):
    check_id: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9._-]+$")
    status: Literal["passed", "failed"]
    evidence_sha256: str

    @field_validator("evidence_sha256")
    @classmethod
    def validate_evidence_sha256(cls, value: str) -> str:
        _sha256(value)
        return value


class TaskEvidenceRecord(StrictModel):
    schema_version: Literal["myis.task-evidence.v1"]
    record_id: str = Field(min_length=2, max_length=160, pattern=r"^[A-Za-z0-9_-]+$")
    task_id: str = Field(min_length=2, max_length=16, pattern=r"^[A-Z][A-Z0-9]*\.[0-9]+$")
    plan_sha256: str
    git_commit: str = Field(min_length=40, max_length=64, pattern=r"^[0-9a-f]+$")
    acceptance_checks: tuple[TaskEvidenceCheck, ...]
    evidence_manifest_hashes: tuple[str, ...] = ()
    prior_record_hash: str | None = None
    supersedes_record_id: str | None = Field(
        default=None, min_length=2, max_length=160, pattern=r"^[A-Za-z0-9._-]+$"
    )

    @field_validator("plan_sha256")
    @classmethod
    def validate_plan_sha256(cls, value: str) -> str:
        _sha256(value)
        return value

    @field_validator("prior_record_hash")
    @classmethod
    def validate_prior_hash(cls, value: str | None) -> str | None:
        if value is not None:
            _sha256(value)
        return value

    @field_validator("evidence_manifest_hashes")
    @classmethod
    def validate_manifest_hashes(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if tuple(sorted(set(values))) != values:
            raise ValueError("evidence hashes must be sorted and unique")
        for value in values:
            _sha256(value)
        return values

    @model_validator(mode="after")
    def validate_checks(self) -> "TaskEvidenceRecord":
        identifiers = tuple(item.check_id for item in self.acceptance_checks)
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("acceptance check IDs must be unique")
        return self


def _sha256(value: str) -> None:
    if len(value) != 64:
        raise ValueError("value must be SHA-256")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError("value must be SHA-256") from error
