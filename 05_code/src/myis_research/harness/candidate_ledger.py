"""Deterministic family-level candidate fusion and pool commitments."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Iterable

from .models import CandidatePoolReference, is_sha256


_SCORE_QUANTUM = Decimal("0.000000000000001")


@dataclass(frozen=True)
class GroundingSpan:
    source_field: str
    start: int
    end: int
    source_sha256: str

    def validate(self) -> None:
        if self.source_field not in {"title", "abstract", "claims"}:
            raise ValueError("grounding source_field must be title, abstract, or claims")
        if self.start < 0 or self.end <= self.start:
            raise ValueError("grounding offsets must define a non-empty source span")
        if not is_sha256(self.source_sha256):
            raise ValueError("grounding source_sha256 must be SHA-256")


@dataclass(frozen=True)
class GroundedQueryView:
    query_id: str
    view_id: str
    text: str
    grounding: tuple[GroundingSpan, ...]
    quarantined: bool = False

    def validate(self) -> None:
        if not self.query_id.strip() or not self.view_id.strip() or not self.text.strip():
            raise ValueError("query_id, view_id, and text are required")
        for span in self.grounding:
            span.validate()
        if not self.grounding and not self.quarantined:
            raise ValueError("ungrounded query views must be quarantined")
        if self.grounding and self.quarantined:
            raise ValueError("grounded query views cannot be marked quarantined")


@dataclass(frozen=True)
class RouteHit:
    query_id: str
    route_id: str
    view_id: str
    family_id: str
    publication_id: str
    rank: int
    score: float
    passage_id: str | None = None
    source_sha256: str | None = None

    def validate(self) -> None:
        for name, value in {
            "query_id": self.query_id,
            "route_id": self.route_id,
            "view_id": self.view_id,
            "family_id": self.family_id,
            "publication_id": self.publication_id,
        }.items():
            if not value.strip():
                raise ValueError(f"{name} is required")
        if self.rank <= 0:
            raise ValueError("route rank must be positive")
        if self.source_sha256 is not None and not is_sha256(self.source_sha256):
            raise ValueError("source_sha256 must be SHA-256")


@dataclass(frozen=True)
class RouteProvenance:
    route_id: str
    view_id: str
    publication_id: str
    passage_id: str | None
    rank: int
    score: float
    contribution: float


@dataclass(frozen=True)
class FamilyCandidate:
    query_id: str
    family_id: str
    publication_id: str
    final_rank: int
    fused_score: float
    best_component_rank: int
    provenance: tuple[RouteProvenance, ...]


def _quantized(value: Decimal) -> Decimal:
    return value.quantize(_SCORE_QUANTUM, rounding=ROUND_HALF_EVEN)


def _deduplicate_route_hits(hits: Iterable[RouteHit]) -> list[RouteHit]:
    best: dict[tuple[str, str, str, str], RouteHit] = {}
    for hit in hits:
        hit.validate()
        key = (hit.query_id, hit.family_id, hit.route_id, hit.view_id)
        incumbent = best.get(key)
        order = (hit.rank, hit.publication_id, hit.passage_id or "")
        if incumbent is None or order < (incumbent.rank, incumbent.publication_id, incumbent.passage_id or ""):
            best[key] = hit
    return sorted(
        best.values(),
        key=lambda hit: (hit.query_id, hit.family_id, hit.route_id, hit.view_id, hit.rank, hit.publication_id),
    )


def build_family_ledger(
    hits: Iterable[RouteHit],
    *,
    fusion_method: str = "rrf",
    fusion_k: int = 60,
    weights: dict[str, float] | None = None,
    final_k: int = 100,
) -> tuple[FamilyCandidate, ...]:
    """Fuse route hits, deduplicate by family, and assign stable final ranks."""

    if fusion_method not in {"rrf", "weighted_rrf", "max"}:
        raise ValueError("unsupported fusion method")
    if fusion_k <= 0 or final_k <= 0:
        raise ValueError("fusion_k and final_k must be positive")
    route_weights = weights or {}
    if any(value < 0 for value in route_weights.values()):
        raise ValueError("route weights must be non-negative")

    grouped: dict[tuple[str, str], list[RouteHit]] = {}
    for hit in _deduplicate_route_hits(hits):
        grouped.setdefault((hit.query_id, hit.family_id), []).append(hit)

    pending: dict[str, list[tuple[str, str, Decimal, int, tuple[RouteProvenance, ...]]]] = {}
    for (query_id, family_id), family_hits in sorted(grouped.items()):
        provenance = []
        contributions = []
        for hit in family_hits:
            weight = Decimal(str(route_weights.get(hit.route_id, 1.0)))
            if fusion_method == "max":
                contribution = weight * Decimal(str(hit.score))
            else:
                contribution = weight / Decimal(fusion_k + hit.rank)
            contribution = _quantized(contribution)
            contributions.append(contribution)
            provenance.append(
                RouteProvenance(
                    route_id=hit.route_id,
                    view_id=hit.view_id,
                    publication_id=hit.publication_id,
                    passage_id=hit.passage_id,
                    rank=hit.rank,
                    score=hit.score,
                    contribution=float(contribution),
                )
            )
        fused = max(contributions) if fusion_method == "max" else sum(contributions, Decimal(0))
        fused = _quantized(fused)
        best_hit = min(family_hits, key=lambda hit: (hit.rank, hit.publication_id, hit.passage_id or ""))
        ordered_provenance = tuple(
            sorted(provenance, key=lambda item: (item.rank, item.route_id, item.view_id, item.publication_id))
        )
        pending.setdefault(query_id, []).append(
            (family_id, best_hit.publication_id, fused, best_hit.rank, ordered_provenance)
        )

    output = []
    for query_id in sorted(pending):
        rows = sorted(pending[query_id], key=lambda row: (-row[2], row[3], row[0]))[:final_k]
        for final_rank, (family_id, publication_id, fused, best_rank, provenance) in enumerate(rows, start=1):
            output.append(
                FamilyCandidate(
                    query_id=query_id,
                    family_id=family_id,
                    publication_id=publication_id,
                    final_rank=final_rank,
                    fused_score=float(fused),
                    best_component_rank=best_rank,
                    provenance=provenance,
                )
            )
    return tuple(output)


def candidate_ledger_bytes(rows: Iterable[FamilyCandidate]) -> bytes:
    ordered = sorted(rows, key=lambda row: (row.query_id, row.final_rank, row.family_id))
    lines = [json.dumps(asdict(row), ensure_ascii=False, separators=(",", ":"), sort_keys=True) for row in ordered]
    return (("\n".join(lines) + "\n") if lines else "").encode("utf-8")


def freeze_candidate_pool(
    rows: Iterable[FamilyCandidate], *, policy_sha256: str, final_k: int
) -> CandidatePoolReference:
    if not is_sha256(policy_sha256):
        raise ValueError("policy_sha256 must be SHA-256")
    materialized = tuple(rows)
    query_count = len({row.query_id for row in materialized})
    if query_count == 0:
        raise ValueError("candidate pool cannot be empty")
    reference = CandidatePoolReference(
        candidate_pool_sha256=hashlib.sha256(candidate_ledger_bytes(materialized)).hexdigest(),
        policy_sha256=policy_sha256,
        final_k=final_k,
        query_count=query_count,
        frozen=True,
    )
    reference.validate()
    return reference
