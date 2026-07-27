"""Explicitly gated interfaces for external research engines."""

from __future__ import annotations

from dataclasses import dataclass

from .governance import AuthorizationError


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
