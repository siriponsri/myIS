"""The only optimizer-editable part of HarnessOpt."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .models import canonical_hash


_ALLOWED_FUSION = {"rrf", "weighted_rrf", "max"}
_ALLOWED_STOPPING = {"budget", "no_gain", "fixed_depth"}


@dataclass(frozen=True)
class HarnessPolicy:
    """Schema-bounded policy; it cannot alter kernel or evaluator controls."""

    policy_id: str
    query_routes: tuple[str, ...] = ("lexical", "dense")
    context_fields: tuple[str, ...] = ("title", "abstract", "claims")
    fusion: str = "rrf"
    fusion_k: int = 60
    retrieval_depth: int = 100
    rerank_depth: int = 100
    evidence_depth: int = 20
    fallback_route: str = "lexical"
    stopping: str = "budget"
    weights: dict[str, float] = field(default_factory=lambda: {"lexical": 1.0, "dense": 1.0})

    def validate(self, module_allowlist: set[str] | None = None) -> None:
        if not self.policy_id.strip():
            raise ValueError("policy_id is required")
        if self.fusion not in _ALLOWED_FUSION:
            raise ValueError(f"fusion must be one of {sorted(_ALLOWED_FUSION)}")
        if self.stopping not in _ALLOWED_STOPPING:
            raise ValueError(f"stopping must be one of {sorted(_ALLOWED_STOPPING)}")
        for name, value in {
            "fusion_k": self.fusion_k,
            "retrieval_depth": self.retrieval_depth,
            "rerank_depth": self.rerank_depth,
            "evidence_depth": self.evidence_depth,
        }.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        routes = set(self.query_routes) | {self.fallback_route} | set(self.weights)
        if module_allowlist is not None and not routes <= module_allowlist:
            raise ValueError(f"policy requests modules outside allowlist: {sorted(routes - module_allowlist)}")
        if any(value < 0 for value in self.weights.values()):
            raise ValueError("fusion weights must be non-negative")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def sha256(self) -> str:
        return canonical_hash(self.as_dict())
