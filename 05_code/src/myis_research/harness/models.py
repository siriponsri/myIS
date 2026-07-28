"""Public data contracts and immutable lifecycle states."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class GoalState(StrEnum):
    DRAFT = "DRAFT"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class RunState(StrEnum):
    CREATED = "CREATED"
    PREFLIGHTED = "PREFLIGHTED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    INVALIDATED = "INVALIDATED"


GOAL_TRANSITIONS = {
    GoalState.DRAFT: {GoalState.REVIEWED, GoalState.CANCELLED},
    GoalState.REVIEWED: {GoalState.APPROVED, GoalState.CANCELLED},
    GoalState.APPROVED: {GoalState.ACTIVE, GoalState.CANCELLED},
    GoalState.ACTIVE: {GoalState.CLOSED, GoalState.CANCELLED},
    GoalState.CLOSED: set(),
    GoalState.CANCELLED: set(),
}

RUN_TRANSITIONS = {
    RunState.CREATED: {RunState.PREFLIGHTED, RunState.CANCELLED, RunState.INVALIDATED},
    RunState.PREFLIGHTED: {RunState.RUNNING, RunState.CANCELLED, RunState.INVALIDATED},
    RunState.RUNNING: {
        RunState.SUCCEEDED,
        RunState.FAILED,
        RunState.CANCELLED,
        RunState.INVALIDATED,
    },
    RunState.SUCCEEDED: set(),
    RunState.FAILED: set(),
    RunState.CANCELLED: set(),
    RunState.INVALIDATED: set(),
}


@dataclass(frozen=True)
class ApprovalRecord:
    approval_id: str
    source: str
    approved_at_utc: str
    scope_hash: str
    budget_tier: str = "R0_OFFLINE"
    held_out_allowed: bool = False


@dataclass(frozen=True)
class GoalSpec:
    goal_id: str
    objective: str
    track: str
    state: GoalState = GoalState.APPROVED
    success_metrics: tuple[str, ...] = ()
    stop_conditions: tuple[str, ...] = ()


@dataclass(frozen=True)
class RunSpec:
    run_id: str
    goal: GoalSpec
    approval: ApprovalRecord
    arm: str
    phase: str
    dataset_id: str
    dataset_manifest_hash: str
    split: str
    split_query_ids_hash: str
    evaluator_id: str
    evaluator_hash: str
    kernel_version: str
    policy_hash: str
    config_hash: str
    prompt_hash: str
    skill_set_hash: str
    seed: int
    budget: dict[str, float | int]
    repository: str = "siriponsri/myIS"
    git_commit: str = "unknown"
    git_dirty: bool = False
    model_id: str = "offline-fixture"
    module_pool_hash: str = "offline-fixture"
    parent_run_id: str | None = None
    trial_id: str | None = None

    def scope_hash(self) -> str:
        return canonical_hash(
            {
                "goal_id": self.goal.goal_id,
                "phase": self.phase,
                "dataset_id": self.dataset_id,
                "split": self.split,
                "split_query_ids_hash": self.split_query_ids_hash,
                "budget": self.budget,
            }
        )


@dataclass(frozen=True)
class RunEvent:
    schema_version: str
    event_id: str
    timestamp_utc: str
    monotonic_ns: int
    sequence: int
    level: str
    event: str
    run_id: str
    goal_id: str
    phase: str
    component: str
    status: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ArtifactRecord:
    path: str
    role: str
    sha256: str
    size_bytes: int
    mime_type: str
    classification: str = "internal"

    @classmethod
    def from_path(cls, root: Path, path: Path, *, role: str, mime_type: str) -> "ArtifactRecord":
        return cls(
            path=path.relative_to(root).as_posix(),
            role=role,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            size_bytes=path.stat().st_size,
            mime_type=mime_type,
        )


@dataclass(frozen=True)
class RunResult:
    run_id: str
    state: RunState
    run_dir: Path
    metrics: dict[str, float]
    manifest_sha256: str | None = None
    stop_reason: str | None = None


def dataclass_dict(value: Any) -> dict[str, Any]:
    result = asdict(value)
    for key, item in tuple(result.items()):
        if isinstance(item, StrEnum):
            result[key] = item.value
    return result
