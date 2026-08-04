"""Aggregate-only synthetic family-level evaluator for ArmIndex fixtures."""

from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any, Mapping, Sequence

from ..kernel.canonical import canonical_sha256
from ..protection import assert_aggregate_only


_QUANTUM = Decimal("0.000000000001")


class SyntheticEvaluationError(ValueError):
    """Raised when synthetic fixture judgments are incomplete or malformed."""


def evaluate_family_rankings(
    rankings: Mapping[str, Sequence[str]],
    judgments: Mapping[str, Mapping[str, int]],
) -> dict[str, Any]:
    """Return Recall@100 and nDCG aggregates without per-case payloads."""

    if not rankings or set(rankings) != set(judgments):
        raise SyntheticEvaluationError("rankings and synthetic judgments must cover the same non-empty cases")
    recalls: list[Decimal] = []
    ndcg_100: list[Decimal] = []
    ndcg_10: list[Decimal] = []
    for case_id in sorted(rankings):
        relevance = judgments[case_id]
        if not relevance or any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in relevance.values()):
            raise SyntheticEvaluationError("every synthetic case requires finite non-negative integer judgments")
        if not any(value > 0 for value in relevance.values()):
            raise SyntheticEvaluationError("every synthetic case requires at least one relevant family")
        ranked = _unique(rankings[case_id])
        relevant = {family_id for family_id, grade in relevance.items() if grade > 0}
        recalls.append(_canonical(len(relevant & set(ranked[:100])) / len(relevant)))
        ndcg_100.append(_canonical(_ndcg(ranked, relevance, 100)))
        ndcg_10.append(_canonical(_ndcg(ranked, relevance, 10)))
    count = len(recalls)
    metrics = [
        _metric("recall_at_100", 100, recalls, count, "macro_mean_relevant_families"),
        _metric("ndcg_at_100", 100, ndcg_100, count, "macro_mean_graded_family_relevance"),
        _metric("ndcg_at_10", 10, ndcg_10, count, "macro_mean_graded_family_relevance"),
    ]
    payload = {
        "schema_version": "myis.armindex-synthetic-metric-bundle.v1",
        "evidence_class": "fixture",
        "scientific_authority": False,
        "case_count": count,
        "metrics": metrics,
        "ranking_commitment": canonical_sha256(
            {case_id: _unique(rankings[case_id]) for case_id in sorted(rankings)}
        ),
        "judgment_commitment": canonical_sha256(
            {
                case_id: dict(sorted(judgments[case_id].items()))
                for case_id in sorted(judgments)
            }
        ),
    }
    payload["metrics_sha256"] = canonical_sha256(metrics)
    assert_aggregate_only(payload)
    return payload


def _canonical(value: float | Decimal) -> Decimal:
    numeric = value if isinstance(value, Decimal) else Decimal(str(value))
    if not numeric.is_finite():
        raise SyntheticEvaluationError("metric value must be finite")
    return numeric.quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)


def _unique(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values))


def _dcg(ranked: Sequence[str], relevance: Mapping[str, int], cutoff: int) -> float:
    total = 0.0
    for rank, family_id in enumerate(_unique(ranked)[:cutoff], start=1):
        grade = relevance.get(family_id, 0)
        total += (2.0**grade - 1.0) / math.log2(rank + 1)
    return total


def _ndcg(ranked: Sequence[str], relevance: Mapping[str, int], cutoff: int) -> float:
    ideal = [
        family_id
        for family_id, _grade in sorted(
            relevance.items(), key=lambda item: (-item[1], item[0])
        )
    ]
    denominator = _dcg(ideal, relevance, cutoff)
    if denominator <= 0:
        raise SyntheticEvaluationError("nDCG is undefined when ideal DCG is zero")
    return _dcg(ranked, relevance, cutoff) / denominator


def _metric(
    name: str,
    cutoff: int,
    values: Sequence[Decimal],
    count: int,
    denominator: str,
) -> dict[str, Any]:
    mean = _canonical(sum(values, Decimal(0)) / Decimal(count))
    return {
        "name": name,
        "cutoff": cutoff,
        "value": float(mean),
        "n": count,
        "scope": "SYNTHETIC",
        "direction": "maximize",
        "denominator": denominator,
        "evidence_role": "engineering_diagnostic",
    }
