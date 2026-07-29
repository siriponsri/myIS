"""Governed local research harness.

The kernel owns lifecycle, approvals, budgets, split isolation, event logging,
artifact hashing, and validation. Optimizers may only replace ``HarnessPolicy``.
"""

from .models import (
    ApprovalRecord,
    ArtifactRecord,
    CandidatePoolReference,
    EndpointClass,
    ExecutionIsolationContract,
    GoalSpec,
    GoalState,
    ProtectedSurfaceContract,
    ProviderExecution,
    ReplicationContract,
    RunEvent,
    RunResult,
    RunSpec,
    RunState,
    RuntimeEnvironment,
    StatisticsContract,
    TrackCManifest,
    TrackSManifest,
)
from .benchmark import (
    CandidateExposureComparison,
    ConfirmationClassification,
    FrozenPoolRankingComparison,
    SharedSplitCommitment,
    SelectionDecision,
    SplitFreezeCommitment,
    TrackCRankingDiagnostic,
)
from .policy import CandidateBudget, FusionContract, HarnessPolicy, QueryViewPolicy, RoutePolicy
from .runner import HarnessAdapter, LocalHarness
from .f1_baselines import (
    BaselineReplay,
    FrozenF1RunSpecV1,
    ResourcePreflight,
    replay_fixture_baselines,
    validate_frozen_f1_runspec,
)
from .validation import ValidationError, validate_run_bundle

__all__ = [
    "ApprovalRecord",
    "ArtifactRecord",
    "CandidateBudget",
    "CandidateExposureComparison",
    "CandidatePoolReference",
    "ConfirmationClassification",
    "EndpointClass",
    "ExecutionIsolationContract",
    "FrozenPoolRankingComparison",
    "FrozenF1RunSpecV1",
    "FusionContract",
    "GoalSpec",
    "GoalState",
    "HarnessAdapter",
    "HarnessPolicy",
    "LocalHarness",
    "ProtectedSurfaceContract",
    "ProviderExecution",
    "QueryViewPolicy",
    "ReplicationContract",
    "ResourcePreflight",
    "RoutePolicy",
    "RunEvent",
    "RunResult",
    "RunSpec",
    "RunState",
    "RuntimeEnvironment",
    "SelectionDecision",
    "StatisticsContract",
    "SharedSplitCommitment",
    "SplitFreezeCommitment",
    "TrackCManifest",
    "TrackCRankingDiagnostic",
    "TrackSManifest",
    "BaselineReplay",
    "ValidationError",
    "validate_run_bundle",
    "replay_fixture_baselines",
    "validate_frozen_f1_runspec",
]
