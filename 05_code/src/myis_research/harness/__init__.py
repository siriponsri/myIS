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
)
from .benchmark import (
    CandidateExposureComparison,
    ConfirmationClassification,
    FrozenPoolRankingComparison,
    SelectionDecision,
    SplitFreezeCommitment,
)
from .policy import CandidateBudget, FusionContract, HarnessPolicy, QueryViewPolicy, RoutePolicy
from .runner import HarnessAdapter, LocalHarness
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
    "RoutePolicy",
    "RunEvent",
    "RunResult",
    "RunSpec",
    "RunState",
    "RuntimeEnvironment",
    "SelectionDecision",
    "StatisticsContract",
    "SplitFreezeCommitment",
    "ValidationError",
    "validate_run_bundle",
]
