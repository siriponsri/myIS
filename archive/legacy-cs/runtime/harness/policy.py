"""The only optimizer-editable part of HarnessOpt."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

from .models import canonical_hash


_ALLOWED_FUSION = {"rrf", "weighted_rrf", "max", "minmax_weighted"}
_ALLOWED_STOPPING = {"budget", "no_gain", "fixed_depth"}
_ALLOWED_ROUTE_KINDS = {"lexical", "dense", "citation", "metadata"}
_ALLOWED_SOURCE_FIELDS = {"title", "abstract", "claims"}
B1_MINMAX_WEIGHTS = {"dense": 0.7, "bm25": 0.3}
B1_SCORE_DIRECTIONS = {"dense": "higher", "bm25": "lower"}


class GroundingMode(StrEnum):
    REQUIRED = "required"
    QUARANTINE_UNGROUNDED = "quarantine_ungrounded"


@dataclass(frozen=True)
class QueryViewPolicy:
    view_id: str
    source_fields: tuple[str, ...]
    grounding: GroundingMode = GroundingMode.REQUIRED

    def validate(self) -> None:
        if not self.view_id.strip():
            raise ValueError("view_id is required")
        fields = set(self.source_fields)
        if not fields:
            raise ValueError("query views require at least one source field")
        if not fields <= _ALLOWED_SOURCE_FIELDS:
            raise ValueError(f"unsupported query-view source fields: {sorted(fields - _ALLOWED_SOURCE_FIELDS)}")
        if len(fields) != len(self.source_fields):
            raise ValueError("query-view source fields must be unique")


@dataclass(frozen=True)
class RoutePolicy:
    route_id: str
    kind: str
    view_ids: tuple[str, ...]
    depth: int
    quota: int
    enabled: bool = True

    def validate(self) -> None:
        if not self.route_id.strip():
            raise ValueError("route_id is required")
        if self.kind not in _ALLOWED_ROUTE_KINDS:
            raise ValueError(f"route kind must be one of {sorted(_ALLOWED_ROUTE_KINDS)}")
        if not self.view_ids:
            raise ValueError("routes require at least one query view")
        if self.depth <= 0 or self.quota <= 0:
            raise ValueError("route depth and quota must be positive")
        if self.quota > self.depth:
            raise ValueError("route quota cannot exceed route depth")


@dataclass(frozen=True)
class CandidateBudget:
    final_k: int = 100
    max_total_retrieved: int = 1_000

    def validate(self) -> None:
        if self.final_k <= 0 or self.max_total_retrieved <= 0:
            raise ValueError("candidate budgets must be positive")
        if self.max_total_retrieved < self.final_k:
            raise ValueError("max_total_retrieved cannot be smaller than final_k")


@dataclass(frozen=True)
class FusionContract:
    method: str = "rrf"
    k: int = 60
    weights: dict[str, float] = field(default_factory=dict)
    score_directions: dict[str, str] = field(default_factory=dict)

    def validate(self, route_ids: set[str]) -> None:
        if self.method not in _ALLOWED_FUSION:
            raise ValueError(f"fusion method must be one of {sorted(_ALLOWED_FUSION)}")
        if self.k <= 0:
            raise ValueError("fusion k must be positive")
        if not set(self.weights) <= route_ids:
            raise ValueError(f"fusion weights reference unknown routes: {sorted(set(self.weights) - route_ids)}")
        if any(value < 0 for value in self.weights.values()):
            raise ValueError("fusion weights must be non-negative")
        if not set(self.score_directions) <= route_ids:
            raise ValueError(
                f"score directions reference unknown routes: {sorted(set(self.score_directions) - route_ids)}"
            )
        invalid = {
            route_id: direction
            for route_id, direction in self.score_directions.items()
            if direction not in {"higher", "lower"}
        }
        if invalid:
            raise ValueError(f"score directions must be higher or lower: {invalid}")
        if self.method == "minmax_weighted":
            missing = set(self.weights) - set(self.score_directions)
            if missing:
                raise ValueError(f"minmax fusion requires score directions for: {sorted(missing)}")


def b1_fusion_contract() -> FusionContract:
    """Return the locked B1 dense/BM25 min-max fusion contract."""

    return FusionContract(
        method="minmax_weighted",
        weights=dict(B1_MINMAX_WEIGHTS),
        score_directions=dict(B1_SCORE_DIRECTIONS),
    )


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
    query_views: tuple[QueryViewPolicy, ...] = ()
    routes: tuple[RoutePolicy, ...] = ()
    candidate_budget: CandidateBudget | None = None
    fusion_contract: FusionContract | None = None
    family_deduplication: bool = True
    provenance_required: bool = True
    frozen_candidate_pool_sha256: str | None = None

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
        if self.frozen_candidate_pool_sha256 is not None:
            if len(self.frozen_candidate_pool_sha256) != 64:
                raise ValueError("frozen_candidate_pool_sha256 must be SHA-256")
            try:
                int(self.frozen_candidate_pool_sha256, 16)
            except ValueError as error:
                raise ValueError("frozen_candidate_pool_sha256 must be SHA-256") from error

        view_ids = [view.view_id for view in self.query_views]
        if len(set(view_ids)) != len(view_ids):
            raise ValueError("query view IDs must be unique")
        for view in self.query_views:
            view.validate()

        route_ids = [route.route_id for route in self.routes]
        if len(set(route_ids)) != len(route_ids):
            raise ValueError("route IDs must be unique")
        known_views = set(view_ids)
        for route in self.routes:
            route.validate()
            missing_views = set(route.view_ids) - known_views
            if missing_views:
                raise ValueError(f"route {route.route_id} references unknown views: {sorted(missing_views)}")
        if module_allowlist is not None and self.routes:
            requested_modules = {route.kind for route in self.routes if route.enabled}
            if not requested_modules <= module_allowlist:
                raise ValueError(
                    f"typed routes request modules outside allowlist: {sorted(requested_modules - module_allowlist)}"
                )

        if self.candidate_budget is not None:
            self.candidate_budget.validate()
            enabled = [route for route in self.routes if route.enabled]
            total_quota = sum(route.quota for route in enabled)
            if enabled and total_quota > self.candidate_budget.max_total_retrieved:
                raise ValueError("route quotas exceed max_total_retrieved")
        if self.fusion_contract is not None:
            self.fusion_contract.validate(set(route_ids))
        elif self.fusion == "minmax_weighted":
            raise ValueError("minmax_weighted requires a typed fusion_contract")
        if not self.family_deduplication:
            raise ValueError("family-level evaluation requires family deduplication")
        if not self.provenance_required:
            raise ValueError("candidate fusion provenance is required")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def sha256(self) -> str:
        return canonical_hash(self.as_dict())
