"""Governed local research harness.

The kernel owns lifecycle, approvals, budgets, split isolation, event logging,
artifact hashing, and validation. Optimizers may only replace ``HarnessPolicy``.
"""

from .models import (
    ApprovalRecord,
    ArtifactRecord,
    GoalSpec,
    GoalState,
    RunEvent,
    RunResult,
    RunSpec,
    RunState,
)
from .policy import HarnessPolicy
from .runner import HarnessAdapter, LocalHarness
from .validation import ValidationError, validate_run_bundle

__all__ = [
    "ApprovalRecord",
    "ArtifactRecord",
    "GoalSpec",
    "GoalState",
    "HarnessAdapter",
    "HarnessPolicy",
    "LocalHarness",
    "RunEvent",
    "RunResult",
    "RunSpec",
    "RunState",
    "ValidationError",
    "validate_run_bundle",
]
