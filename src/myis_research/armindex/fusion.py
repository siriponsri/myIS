"""Deterministic family-ranking fusion without evaluator or qrels access."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN
from typing import Mapping, Sequence


_SCORE_QUANTUM = Decimal("0.000000000000001")
FUSION_METHODS = frozenset({"rrf", "weighted_rrf", "normalized_rank_sum"})


class FusionError(ValueError):
    """Raised when family rankings cannot be fused deterministically."""


def fuse_rankings(
    rankings: Mapping[str, Sequence[str]],
    *,
    method: str = "rrf",
    weights: Mapping[str, int | float | Decimal] | None = None,
    rrf_k: int = 60,
    limit: int = 100,
) -> tuple[dict[str, object], ...]:
    """Fuse arm rankings with stable family deduplication and lexical ties."""

    if method not in FUSION_METHODS:
        raise FusionError("unsupported ArmIndex fusion method")
    if isinstance(rrf_k, bool) or rrf_k <= 0 or isinstance(limit, bool) or limit <= 0:
        raise FusionError("rrf_k and limit must be positive integers")
    if not rankings:
        raise FusionError("at least one arm ranking is required")
    arm_ids = tuple(sorted(str(arm_id) for arm_id in rankings))
    route_weights = {
        arm_id: _weight((weights or {}).get(arm_id, 1)) for arm_id in arm_ids
    }
    unknown_weights = set(weights or {}) - set(arm_ids)
    if unknown_weights:
        raise FusionError(f"fusion weights reference unknown arms: {sorted(unknown_weights)}")

    totals: dict[str, Decimal] = {}
    best_rank: dict[str, int] = {}
    contributors: dict[str, list[str]] = {}
    for arm_id in arm_ids:
        ranking = _deduplicate(rankings[arm_id])
        depth = len(ranking)
        for rank, family_id in enumerate(ranking, start=1):
            if method in {"rrf", "weighted_rrf"}:
                contribution = route_weights[arm_id] / Decimal(rrf_k + rank)
            else:
                contribution = route_weights[arm_id] * Decimal(depth - rank + 1) / Decimal(depth)
            contribution = contribution.quantize(_SCORE_QUANTUM, rounding=ROUND_HALF_EVEN)
            totals[family_id] = totals.get(family_id, Decimal(0)) + contribution
            best_rank[family_id] = min(best_rank.get(family_id, rank), rank)
            contributors.setdefault(family_id, []).append(arm_id)

    ordered = sorted(
        totals,
        key=lambda family_id: (-totals[family_id], best_rank[family_id], family_id),
    )[:limit]
    return tuple(
        {
            "family_id": family_id,
            "rank": rank,
            "score": str(totals[family_id].quantize(_SCORE_QUANTUM)),
            "best_component_rank": best_rank[family_id],
            "contributing_arm_ids": sorted(set(contributors[family_id])),
        }
        for rank, family_id in enumerate(ordered, start=1)
    )


def _deduplicate(ranking: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    output: list[str] = []
    for raw_family_id in ranking:
        family_id = str(raw_family_id)
        if not family_id:
            raise FusionError("family IDs cannot be empty")
        if family_id not in seen:
            output.append(family_id)
            seen.add(family_id)
    return tuple(output)


def _weight(value: int | float | Decimal) -> Decimal:
    weight = value if isinstance(value, Decimal) else Decimal(str(value))
    if not weight.is_finite() or weight < 0:
        raise FusionError("fusion weights must be finite and non-negative")
    return weight
