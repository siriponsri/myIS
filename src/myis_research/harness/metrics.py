"""Deterministic family-level retrieval metrics and score comparison."""

from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Iterable, Mapping, Sequence


METRIC_QUANTUM = Decimal("0.000000000001")


def canonical_metric(value: float | Decimal) -> Decimal:
    numeric = value if isinstance(value, Decimal) else Decimal(str(value))
    if not numeric.is_finite():
        raise ValueError("metric values must be finite")
    return numeric.quantize(METRIC_QUANTUM, rounding=ROUND_HALF_EVEN)


def strictly_greater(candidate: float | Decimal, incumbent: float | Decimal) -> bool:
    """Compare preregistered primary scores at canonical precision."""

    return canonical_metric(candidate) > canonical_metric(incumbent)


def recall_at_k(retrieved: Sequence[str], relevant: Iterable[str], *, k: int = 100) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    relevant_set = set(relevant)
    if not relevant_set:
        raise ValueError("recall is undefined for a query without relevant families")
    retrieved_unique = tuple(dict.fromkeys(retrieved[:k]))
    return float(canonical_metric(len(relevant_set & set(retrieved_unique)) / len(relevant_set)))


def dcg_at_k(retrieved: Sequence[str], relevance: Mapping[str, float], *, k: int = 100) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    total = 0.0
    for rank, family_id in enumerate(dict.fromkeys(retrieved[:k]), start=1):
        gain = float(relevance.get(family_id, 0.0))
        if gain < 0:
            raise ValueError("relevance grades must be non-negative")
        total += (2.0**gain - 1.0) / math.log2(rank + 1)
    return total


def ndcg_at_k(retrieved: Sequence[str], relevance: Mapping[str, float], *, k: int = 100) -> float:
    if not relevance:
        raise ValueError("nDCG is undefined for a query without relevance judgments")
    ideal = sorted(relevance, key=lambda family_id: (-float(relevance[family_id]), family_id))
    denominator = dcg_at_k(ideal, relevance, k=k)
    if denominator == 0:
        raise ValueError("nDCG is undefined when ideal DCG is zero")
    return float(canonical_metric(dcg_at_k(retrieved, relevance, k=k) / denominator))


def macro_mean(values: Iterable[float | Decimal]) -> float:
    materialized = [canonical_metric(value) for value in values]
    if not materialized:
        raise ValueError("macro mean requires at least one query")
    return float(canonical_metric(sum(materialized, Decimal(0)) / Decimal(len(materialized))))
