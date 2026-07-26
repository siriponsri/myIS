"""Fail-closed guards shared by future research runners."""

from __future__ import annotations

from dataclasses import dataclass


class AuthorizationError(RuntimeError):
    """Raised when an execution has not passed an explicit Owner gate."""


@dataclass(frozen=True)
class ExecutionAuthorization:
    owner_approval_source: str | None
    track: str
    stage: str
    held_out: bool = False
    held_out_approved: bool = False

    def validate(self) -> None:
        if self.track not in {"C", "R", "S"}:
            raise AuthorizationError(f"Unknown track: {self.track!r}")
        if not self.owner_approval_source:
            raise AuthorizationError("Explicit Owner approval source is required")
        if self.held_out and not self.held_out_approved:
            raise AuthorizationError("Held-out access requires a separate Owner gate")


def assert_research_execution_enabled(enabled: bool) -> None:
    """Prevent accidental execution while the repository is restructure-only."""
    if not enabled:
        raise AuthorizationError(
            "Research execution is disabled during restructuring; ask the Owner"
        )

