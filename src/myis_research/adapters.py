"""Explicitly gated interfaces for external research engines."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from threading import Lock
from typing import Any, Callable

from .governance import AuthorizationError
from .harness.models import is_sha256
from .protection import assert_aggregate_only


@dataclass(frozen=True)
class Trial:
    hypothesis: str
    patch: str
    command: str
    metric_name: str
    metric_value: float
    decision: str
    artifact_paths: tuple[str, ...] = ()


class AutoresearchAdapter:
    """Represent the Karpathy loop without vendoring or executing upstream code."""

    upstream_commit = "228791fb499afffb54b46200aca536f79142f117"

    def to_ledger_entry(self, trial: Trial) -> dict[str, object]:
        return {"hypothesis": trial.hypothesis, "patch": trial.patch, "command": trial.command,
                "metrics": {trial.metric_name: trial.metric_value}, "decision": trial.decision,
                "artifacts": list(trial.artifact_paths), "upstream_commit": self.upstream_commit}


class HyperResearchAdapter:
    """Fail closed unless the Claude-only Owner gate is explicitly present."""

    def __init__(self, *, owner_approval: str | None, provider: str):
        self.owner_approval = owner_approval
        self.provider = provider

    def validate(self) -> None:
        if self.provider.lower() != "claude":
            raise AuthorizationError("HyperResearch execution is Claude-only")
        if not self.owner_approval:
            raise AuthorizationError("HyperResearch requires explicit Owner approval")


class AdapterOperation(StrEnum):
    READ = "read"
    WRITE = "write"


@dataclass(frozen=True)
class AdapterRequest:
    adapter_id: str
    operation: AdapterOperation
    resource_id: str
    purpose: str
    request_sha256: str
    timeout_seconds: int = 30
    max_retries: int = 1
    owner_decision_id: str | None = None

    def validate(self) -> None:
        if not self.adapter_id.strip() or not self.resource_id.strip() or not self.purpose.strip():
            raise ValueError("adapter, resource, and purpose are required")
        if not is_sha256(self.request_sha256):
            raise ValueError("adapter request must be hash-bound")
        if not 1 <= self.timeout_seconds <= 60 or not 0 <= self.max_retries <= 3:
            raise ValueError("adapter timeout/retry budget is outside the allowlist")
        if self.operation == AdapterOperation.WRITE and not (self.owner_decision_id or "").strip():
            raise PermissionError("adapter writes require an Owner Gate decision")


@dataclass(frozen=True)
class AdapterProvenance:
    source_id: str
    source_sha256: str
    response_sha256: str
    tool_id: str
    tool_version: str
    retrieved_at_utc: str

    def validate(self) -> None:
        if not all(
            value.strip()
            for value in (self.source_id, self.tool_id, self.tool_version, self.retrieved_at_utc)
        ):
            raise ValueError("adapter provenance identity is incomplete")
        if not is_sha256(self.source_sha256) or not is_sha256(self.response_sha256):
            raise ValueError("adapter provenance must bind source and response hashes")


@dataclass(frozen=True)
class AdapterResponse:
    metadata: dict[str, Any]
    classification: str
    provenance: AdapterProvenance

    def validate(self) -> None:
        if self.classification not in {"public", "internal", "aggregate"}:
            raise PermissionError("protected adapter responses cannot enter the agent workspace")
        assert_aggregate_only(self.metadata)
        self.provenance.validate()


class TypedAdapterBoundary:
    """Read-only by default; approved writes are serialized and provenance-bound."""

    def __init__(
        self,
        handler: Callable[[AdapterRequest], AdapterResponse],
        *,
        writes_enabled: bool = False,
    ) -> None:
        self.handler = handler
        self.writes_enabled = writes_enabled
        self._writer = Lock()

    def execute(self, request: AdapterRequest) -> AdapterResponse:
        request.validate()
        if request.operation == AdapterOperation.WRITE:
            if not self.writes_enabled:
                raise PermissionError("adapter is read-only")
            with self._writer:
                response = self.handler(request)
        else:
            response = self.handler(request)
        response.validate()
        return response
