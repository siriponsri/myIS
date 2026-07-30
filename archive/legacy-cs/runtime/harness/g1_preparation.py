"""Deterministic F1/G1 preparation algorithms with no execution adapter."""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Mapping

from .dapfam_contracts import SPLIT_ALIASES, SPLIT_COUNTS, SplitCommitment


@dataclass(frozen=True)
class PreparedSplit:
    membership: dict[str, tuple[str, ...]]
    commitment: SplitCommitment


def membership_sha256(role: str, query_ids: Iterable[str]) -> str:
    ordered = tuple(sorted(query_ids))
    payload = f"myis-shared-split-v1\0{role}\0" + "\n".join(ordered)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def hamilton_allocation(stratum_sizes: Mapping[str, int], target: int) -> dict[str, int]:
    """Allocate an exact target proportionally using stable Hamilton remainders."""

    if target < 0 or any(size < 0 for size in stratum_sizes.values()):
        raise ValueError("Hamilton allocation sizes must be non-negative")
    population = sum(stratum_sizes.values())
    if target > population or (population == 0 and target):
        raise ValueError("Hamilton target exceeds the available population")
    if population == 0:
        return {name: 0 for name in sorted(stratum_sizes)}
    quotas = {name: target * size / population for name, size in stratum_sizes.items()}
    result = {name: math.floor(quotas[name]) for name in stratum_sizes}
    remaining = target - sum(result.values())
    order = sorted(stratum_sizes, key=lambda name: (-(quotas[name] - result[name]), name))
    for name in order[:remaining]:
        result[name] += 1
    return dict(sorted(result.items()))


def prepare_shared_split(
    strata_by_query: Mapping[str, str],
    *,
    out_positive_query_ids: Iterable[str],
    seed: int = 42,
) -> PreparedSplit:
    if seed != 42:
        raise ValueError("the shared split seed is locked to 42")
    if len(strata_by_query) != 1247:
        raise ValueError("DAPFAM preparation requires exactly 1,247 unique queries")
    if any(not query_id or not stratum for query_id, stratum in strata_by_query.items()):
        raise ValueError("query IDs and deterministic strata are required")

    grouped: dict[str, list[str]] = defaultdict(list)
    for query_id, stratum in strata_by_query.items():
        grouped[stratum].append(query_id)
    for stratum, query_ids in grouped.items():
        query_ids.sort(key=lambda query_id: (_tie_break(seed, stratum, query_id), query_id))

    train_alloc = hamilton_allocation({name: len(ids) for name, ids in grouped.items()}, SPLIT_COUNTS["train"])
    train: list[str] = []
    remaining: dict[str, list[str]] = {}
    for name in sorted(grouped):
        cut = train_alloc[name]
        train.extend(grouped[name][:cut])
        remaining[name] = grouped[name][cut:]
    selection_alloc = hamilton_allocation(
        {name: len(ids) for name, ids in remaining.items()}, SPLIT_COUNTS["selection"]
    )
    selection: list[str] = []
    joint_test: list[str] = []
    for name in sorted(remaining):
        cut = selection_alloc[name]
        selection.extend(remaining[name][:cut])
        joint_test.extend(remaining[name][cut:])

    membership = {
        "train": tuple(sorted(train)),
        "selection": tuple(sorted(selection)),
        "joint_test": tuple(sorted(joint_test)),
    }
    flattened = [query_id for ids in membership.values() for query_id in ids]
    if len(flattened) != len(set(flattened)) or set(flattened) != set(strata_by_query):
        raise RuntimeError("split assignment is not a disjoint complete partition")
    if {role: len(ids) for role, ids in membership.items()} != SPLIT_COUNTS:
        raise RuntimeError("split assignment did not meet the locked exact counts")

    out_positive = set(out_positive_query_ids)
    if not out_positive.issubset(strata_by_query):
        raise ValueError("OUT-positive IDs must be present in the query inventory")
    out_counts = {role: sum(query_id in out_positive for query_id in ids) for role, ids in membership.items()}
    commitment = SplitCommitment(
        seed=42,
        algorithm="hamilton-sha256-v1",
        counts=dict(SPLIT_COUNTS),
        membership_sha256={role: membership_sha256(role, ids) for role, ids in membership.items()},
        out_positive_counts=out_counts,
        out_positive_total=len(out_positive),
        aliases=dict(SPLIT_ALIASES),
    )
    return PreparedSplit(membership=membership, commitment=commitment)


def _tie_break(seed: int, stratum: str, query_id: str) -> bytes:
    return hashlib.sha256(f"{seed}\0{stratum}\0{query_id}".encode("utf-8")).digest()
