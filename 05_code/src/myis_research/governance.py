"""Fail-closed guards shared by future research runners."""

from __future__ import annotations

from dataclasses import dataclass


OWNER_GATE_ACTIONS = {
    "G4": frozenset({"authorize_track_s"}),
    "G5": frozenset({"freeze_track_s"}),
    "G6": frozenset({"authorize_joint_confirmation"}),
    "G7": frozenset({"authorize_transfer"}),
    "G8": frozenset({"authorize_publication"}),
}


class AuthorizationError(RuntimeError):
    """Raised when an execution has not passed an explicit Owner gate."""


@dataclass(frozen=True)
class ExecutionAuthorization:
    owner_approval_source: str | None
    track: str
    stage: str
    held_out: bool = False
    held_out_approved: bool = False
    gate_id: str | None = None
    action: str | None = None

    def validate(self) -> None:
        if self.track not in {"C", "S"}:
            raise AuthorizationError(f"Unknown track: {self.track!r}")
        if not self.owner_approval_source:
            raise AuthorizationError("Explicit Owner approval source is required")
        if self.held_out and not self.held_out_approved:
            raise AuthorizationError("Held-out access requires a separate Owner gate")
        if (self.gate_id is None) != (self.action is None):
            raise AuthorizationError("gate_id and action must be supplied together")
        if self.gate_id is not None and self.action not in OWNER_GATE_ACTIONS.get(self.gate_id, frozenset()):
            raise AuthorizationError(f"Action {self.action!r} is not valid for Owner Gate {self.gate_id!r}")


def assert_research_execution_enabled(enabled: bool) -> None:
    """Prevent accidental execution while the repository is restructure-only."""
    if not enabled:
        raise AuthorizationError(
            "Research execution is disabled during restructuring; ask the Owner"
        )
