"""Aggregate-safe same-depth complementarity interfaces."""

from __future__ import annotations

from itertools import combinations
from typing import Any, Mapping, Sequence

from ..kernel.canonical import canonical_sha256
from ..protection import assert_aggregate_only


class ComplementarityError(ValueError):
    """Raised when arm rankings or aggregate gates are not comparable."""


def same_depth_union(
    rankings: Mapping[str, Sequence[str]], *, depth: int
) -> tuple[str, ...]:
    """Return a deterministic family union after enforcing equal candidate depth."""

    materialized = _at_equal_depth(rankings, depth)
    return tuple(sorted({family_id for ranking in materialized.values() for family_id in ranking}))


def pairwise_overlap(
    rankings: Mapping[str, Sequence[str]], *, depth: int
) -> tuple[dict[str, Any], ...]:
    """Compute count and Jaccard overlap without relevance labels."""

    materialized = _at_equal_depth(rankings, depth)
    rows = []
    for left, right in combinations(sorted(materialized), 2):
        left_set, right_set = set(materialized[left]), set(materialized[right])
        intersection = len(left_set & right_set)
        union = len(left_set | right_set)
        rows.append(
            {
                "left_arm_id": left,
                "right_arm_id": right,
                "candidate_depth": depth,
                "intersection_count": intersection,
                "union_count": union,
                "jaccard": intersection / union if union else 1.0,
                "rank_overlap_at_depth": intersection / depth,
            }
        )
    return tuple(rows)


def evaluate_complementarity_gate(value: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate the preregistered gate from aggregate evaluator outputs only."""

    report = dict(value)
    try:
        assert_aggregate_only(report)
    except ValueError as error:
        raise ComplementarityError(str(error)) from error
    required = {
        "schema_version",
        "best_arm_recall_at_100",
        "union_recall_at_100",
        "union_recall_at_1000",
        "best_arm_recall_at_1000",
        "maximum_unique_query_fraction",
        "fixed_union_frontier_acceptable",
    }
    if set(report) != required or report["schema_version"] != "myis.armindex-complementarity-gate-input.v1":
        raise ComplementarityError("complementarity gate fields do not match the v1 contract")
    numbers = {
        key: _bounded_fraction(report[key])
        for key in required
        if key not in {"schema_version", "fixed_union_frontier_acceptable"}
    }
    promoted = (
        numbers["union_recall_at_1000"] - numbers["best_arm_recall_at_1000"] >= 0.015
        or numbers["maximum_unique_query_fraction"] >= 0.05
        or (
            numbers["union_recall_at_100"] > numbers["best_arm_recall_at_100"]
            and report["fixed_union_frontier_acceptable"] is True
        )
    )
    output = {
        "schema_version": "myis.armindex-complementarity-gate.v1",
        "status": "promote_multi_arm_harness" if promoted else "freeze_best_single_arm",
        "aggregate_inputs": numbers,
        "fixed_union_frontier_acceptable": report["fixed_union_frontier_acceptable"] is True,
        "protected_data_accessed": False,
    }
    output["report_sha256"] = canonical_sha256(output)
    return output


def _at_equal_depth(
    rankings: Mapping[str, Sequence[str]], depth: int
) -> dict[str, tuple[str, ...]]:
    if isinstance(depth, bool) or depth <= 0 or not rankings:
        raise ComplementarityError("candidate depth and rankings are required")
    output: dict[str, tuple[str, ...]] = {}
    for arm_id in sorted(rankings):
        if not str(arm_id).startswith("ARM-"):
            raise ComplementarityError("ranking arm ID is invalid")
        deduplicated = tuple(dict.fromkeys(str(value) for value in rankings[arm_id]))
        if len(deduplicated) < depth:
            raise ComplementarityError("every arm must provide the same requested candidate depth")
        output[str(arm_id)] = deduplicated[:depth]
    return output


def _bounded_fraction(value: Any) -> float:
    if isinstance(value, bool):
        raise ComplementarityError("complementarity metrics must be numeric")
    numeric = float(value)
    if not 0 <= numeric <= 1:
        raise ComplementarityError("complementarity metrics must be in [0, 1]")
    return numeric
