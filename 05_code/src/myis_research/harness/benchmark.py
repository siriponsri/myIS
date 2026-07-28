"""DAPFAM cohort rules and four-arm comparison validation."""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from typing import Iterable


ARMS = ("dapfam", "human", "skillopt", "harnessopt")
PRIMARY_METRICS = ("out_ndcg_at_100", "out_recall_at_100")


@dataclass(frozen=True)
class SplitAssignment:
    train: tuple[str, ...]
    selection: tuple[str, ...]
    confirmation: tuple[str, ...]

    @property
    def hashes(self) -> dict[str, str]:
        return {
            name: hashlib.sha256("\n".join(getattr(self, name)).encode("utf-8")).hexdigest()
            for name in ("train", "selection", "confirmation")
        }


def deterministic_stratified_split(rows: Iterable[tuple[str, str]], *, seed: int) -> SplitAssignment:
    """Split query IDs 60/20/20 within each declared stratum."""
    strata: dict[str, list[str]] = {}
    for query_id, stratum in rows:
        strata.setdefault(stratum, []).append(query_id)
    output = {"train": [], "selection": [], "confirmation": []}
    for stratum in sorted(strata):
        ids = sorted(set(strata[stratum]))
        rng = random.Random(f"{seed}:{stratum}")
        rng.shuffle(ids)
        n = len(ids)
        train_end = round(n * 0.60)
        selection_end = train_end + round(n * 0.20)
        output["train"].extend(ids[:train_end])
        output["selection"].extend(ids[train_end:selection_end])
        output["confirmation"].extend(ids[selection_end:])
    return SplitAssignment(*(tuple(sorted(output[name])) for name in ("train", "selection", "confirmation")))


def validate_comparable_arms(manifests: dict[str, dict]) -> None:
    missing = set(ARMS) - set(manifests)
    if missing:
        raise ValueError(f"missing benchmark arms: {sorted(missing)}")
    fields = (
        ("inputs", "split_query_ids_hash"),
        ("evaluator", "hash"),
        ("method", "model_id"),
        ("method", "module_pool_hash"),
    )
    for section, field in fields:
        values = {arm: manifests[arm][section][field] for arm in ARMS}
        if len(set(values.values())) != 1:
            raise ValueError(f"arms are not comparable: {section}.{field} differs: {values}")
    budgets = {arm: json.dumps(manifests[arm]["budget"]["limits"], sort_keys=True) for arm in ARMS}
    if len(set(budgets.values())) != 1:
        raise ValueError(f"arms are not comparable: budgets differ: {budgets}")


def harnessopt_wins(metrics: dict[str, dict[str, float]]) -> bool:
    """Require HarnessOpt to beat both DAPFAM and SkillOpt on both primary endpoints."""
    return all(
        metrics["harnessopt"][metric] > metrics[competitor][metric]
        for metric in PRIMARY_METRICS
        for competitor in ("dapfam", "skillopt")
    )
