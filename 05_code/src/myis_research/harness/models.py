"""Public data contracts and immutable lifecycle states."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from ..identity import (
    DISPLAY_NAME,
    PROGRAM_ID,
    PROTOCOL_FAMILY_ID,
    PROTOCOL_VERSION,
    RESEARCH_VERSION,
)


SHA256_HEX_LENGTH = 64
PACKAGE_VERSION = "0.1.0"
TRACK_C_ARMS = frozenset({"B0", "B1", "B2", "C0", "C1", "CF", "C_DIAGNOSTIC", "Q", "PC", "CT"})
TRACK_S_ARMS = frozenset({"A0", "A1", "A2", "A2L", "A3", "SF", "Q", "PS", "CT"})


def is_sha256(value: str | None) -> bool:
    if value is None or len(value) != SHA256_HEX_LENGTH:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


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


class EndpointClass(StrEnum):
    OFFICIAL = "official"
    THIRD_PARTY = "third_party"
    LOCAL = "local"


class SeedControl(StrEnum):
    FIXED = "fixed"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"


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
class RuntimeEnvironment:
    """Exact replay environment recorded for every measured run."""

    python_version: str
    uv_version: str
    os: str
    architecture: str
    uv_lock_sha256: str
    accelerator: str = "cpu"
    cuda_stack: str | None = None
    selected_groups: tuple[str, ...] = ()
    selected_extras: tuple[str, ...] = ()

    def validate(self) -> None:
        for name, value in {
            "python_version": self.python_version,
            "uv_version": self.uv_version,
            "os": self.os,
            "architecture": self.architecture,
            "accelerator": self.accelerator,
        }.items():
            if not value.strip():
                raise ValueError(f"{name} is required")
        if not self.python_version.startswith("3.11."):
            raise ValueError("measured runs require an exact Python 3.11 patch version")
        if not is_sha256(self.uv_lock_sha256):
            raise ValueError("uv_lock_sha256 must be SHA-256")
        if len(set(self.selected_groups)) != len(self.selected_groups):
            raise ValueError("selected_groups must be unique")
        if len(set(self.selected_extras)) != len(self.selected_extras):
            raise ValueError("selected_extras must be unique")


@dataclass(frozen=True)
class ProviderExecution:
    """Requested and resolved inference identity with explicit fallback state."""

    requested_model: str
    resolved_model: str
    provider: str
    effort: str
    endpoint_class: EndpointClass = EndpointClass.OFFICIAL
    fallback_allowed: bool = False
    fallback_used: bool = False
    routing_used: bool = False
    parameters_dropped: bool = False
    request_id: str | None = None
    temperature: float | None = None
    seed: int | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_seconds: float = 0.0
    cost_usd: float = 0.0

    def validate(self, *, measured: bool = True) -> None:
        for name, value in {
            "requested_model": self.requested_model,
            "resolved_model": self.resolved_model,
            "provider": self.provider,
            "effort": self.effort,
        }.items():
            if not value.strip():
                raise ValueError(f"{name} is required")
        if self.requested_model != self.resolved_model:
            raise ValueError("requested and resolved model identities differ")
        if measured and (self.fallback_allowed or self.fallback_used):
            raise ValueError("provider/model fallback is forbidden in measured runs")
        if measured and self.routing_used:
            raise ValueError("provider routing is forbidden in measured runs")
        if measured and self.parameters_dropped:
            raise ValueError("provider parameter dropping is forbidden in measured runs")
        if min(self.input_tokens, self.output_tokens) < 0:
            raise ValueError("token usage must be non-negative")
        if self.latency_seconds < 0 or self.cost_usd < 0:
            raise ValueError("latency and cost must be non-negative")


@dataclass(frozen=True)
class ReplicationContract:
    repeat_id: str = "r0"
    stochastic: bool = False
    seed_control: SeedControl = SeedControl.NOT_APPLICABLE
    matched_group_id: str | None = None
    order_index: int = 0

    def validate(self) -> None:
        if not self.repeat_id.strip():
            raise ValueError("repeat_id is required")
        if self.order_index < 0:
            raise ValueError("order_index must be non-negative")
        if self.stochastic and self.seed_control == SeedControl.NOT_APPLICABLE:
            raise ValueError("stochastic runs must declare fixed or unavailable seed control")


@dataclass(frozen=True)
class StatisticsContract:
    primary_metric: str
    bootstrap_resamples: int = 10_000
    confidence_level: float = 0.95
    effect_size: str = "rank_biserial"
    comparison_family_id: str = "primary"
    comparison_role: str = "primary"
    correction: str = "none"

    def validate(self) -> None:
        if not self.primary_metric.strip():
            raise ValueError("primary_metric is required")
        if self.bootstrap_resamples != 10_000:
            raise ValueError("confirmation uses exactly 10,000 paired-bootstrap resamples")
        if self.confidence_level != 0.95:
            raise ValueError("confirmation confidence level must be 0.95")
        if self.effect_size != "rank_biserial":
            raise ValueError("effect_size must be rank_biserial")
        if self.comparison_role not in {"primary", "additional"}:
            raise ValueError("comparison_role must be primary or additional")
        expected = "none" if self.comparison_role == "primary" else "holm"
        if self.correction != expected:
            raise ValueError(f"{self.comparison_role} comparisons require correction={expected}")


@dataclass(frozen=True)
class ProtectedSurfaceContract:
    editable: tuple[str, ...] = ()
    protected: tuple[str, ...] = ()

    def validate(self) -> None:
        editable = set(self.editable)
        protected = set(self.protected)
        overlap = editable & protected
        if overlap:
            raise ValueError(f"editable and protected surfaces overlap: {sorted(overlap)}")
        if len(editable) != len(self.editable) or len(protected) != len(self.protected):
            raise ValueError("surface paths must be unique")


@dataclass(frozen=True)
class ExecutionIsolationContract:
    network_mode: str
    network_guard_sha256: str
    cached_inputs_sha256: str
    data_scopes: tuple[str, ...] = ("adaptation", "selection")
    dependency_replay_command: str = "uv sync --locked"
    confirmation_access: bool = False

    def validate(self) -> None:
        if self.network_mode != "offline":
            raise ValueError("measured optimization requires offline network mode")
        if not is_sha256(self.network_guard_sha256) or not is_sha256(self.cached_inputs_sha256):
            raise ValueError("network guard and cached inputs require SHA-256 commitments")
        if not self.data_scopes or set(self.data_scopes) - {"adaptation", "selection"}:
            raise ValueError("agent data scopes are limited to adaptation and selection")
        if len(set(self.data_scopes)) != len(self.data_scopes):
            raise ValueError("agent data scopes must be unique")
        if self.dependency_replay_command != "uv sync --locked":
            raise ValueError("dependency replay must use uv sync --locked")
        if self.confirmation_access:
            raise ValueError("confirmation access is forbidden in the agent workspace")


@dataclass(frozen=True)
class CandidatePoolReference:
    candidate_pool_sha256: str
    policy_sha256: str
    final_k: int
    query_count: int
    frozen: bool = True

    def validate(self) -> None:
        if not is_sha256(self.candidate_pool_sha256):
            raise ValueError("candidate_pool_sha256 must be SHA-256")
        if not is_sha256(self.policy_sha256):
            raise ValueError("policy_sha256 must be SHA-256")
        if self.final_k <= 0 or self.query_count <= 0:
            raise ValueError("candidate pool dimensions must be positive")


@dataclass(frozen=True)
class ResearchVersionSpec:
    program_id: str = PROGRAM_ID
    display_name: str = DISPLAY_NAME
    protocol_version: str = PROTOCOL_VERSION
    track_id: str = "C"
    track_version: str = RESEARCH_VERSION
    package_version: str = PACKAGE_VERSION
    research_version: str = RESEARCH_VERSION
    protocol_family_id: str = PROTOCOL_FAMILY_ID
    revision_id: str = "uncommitted"
    owner_decision_id: str | None = None

    def validate(self) -> None:
        if (
            self.program_id != PROGRAM_ID
            or self.display_name != DISPLAY_NAME
            or self.protocol_version != PROTOCOL_VERSION
            or self.track_id not in {"C", "S"}
            or self.track_version != RESEARCH_VERSION
            or self.package_version != PACKAGE_VERSION
            or self.research_version != RESEARCH_VERSION
            or self.protocol_family_id != PROTOCOL_FAMILY_ID
        ):
            raise ValueError("run is not bound to the canonical myIS Research protocol 1.0 identity")
        if not self.revision_id.strip():
            raise ValueError("revision_id is required")


@dataclass(frozen=True)
class TrackCManifest:
    """Typed active Track C arm binding; it has no independent R-track mode."""

    arm: str

    def validate(self) -> None:
        if self.arm not in TRACK_C_ARMS:
            raise ValueError(f"unsupported Track C arm: {self.arm}")


@dataclass(frozen=True)
class TrackSManifest:
    """Typed active Track S arm binding for required matched-budget arms."""

    arm: str

    def validate(self) -> None:
        if self.arm not in TRACK_S_ARMS:
            raise ValueError(f"unsupported Track S arm: {self.arm}")


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
    research: ResearchVersionSpec = field(default_factory=ResearchVersionSpec)
    environment: RuntimeEnvironment | None = None
    provider: ProviderExecution | None = None
    replication: ReplicationContract | None = None
    statistics: StatisticsContract | None = None
    surfaces: ProtectedSurfaceContract | None = None
    isolation: ExecutionIsolationContract | None = None
    candidate_pool: CandidatePoolReference | None = None
    artifact_hashes: dict[str, str] = field(default_factory=dict)
    shared_split_commitment_sha256: str | None = None
    track_firewall_sha256: str | None = None

    def validate_active_contract(self) -> None:
        """Reject legacy identity and independent-R emissions before execution."""

        self.research.validate()
        if self.research.track_id == "C":
            TrackCManifest(self.arm).validate()
        else:
            TrackSManifest(self.arm).validate()
        if self.phase.upper().startswith("R"):
            raise ValueError("independent ranking/evidence phases are legacy read-only and cannot be emitted")
        measured = not self.phase.startswith(("offline", "bootstrap", "fixture"))
        if measured and not is_sha256(self.shared_split_commitment_sha256):
            raise ValueError("measured runs require a shared split commitment SHA-256")
        if measured and not is_sha256(self.track_firewall_sha256):
            raise ValueError("measured runs require a track-specific firewall SHA-256")

    def scope_hash(self) -> str:
        return canonical_hash(
            {
                "goal_id": self.goal.goal_id,
                "phase": self.phase,
                "dataset_id": self.dataset_id,
                "split": self.split,
                "split_query_ids_hash": self.split_query_ids_hash,
                "shared_split_commitment_sha256": self.shared_split_commitment_sha256,
                "track_firewall_sha256": self.track_firewall_sha256,
                "budget": self.budget,
                "research": dataclass_dict(self.research),
                "model_id": self.model_id,
                "module_pool_hash": self.module_pool_hash,
                "candidate_pool": dataclass_dict(self.candidate_pool) if self.candidate_pool else None,
                "surfaces": dataclass_dict(self.surfaces) if self.surfaces else None,
                "isolation": dataclass_dict(self.isolation) if self.isolation else None,
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
