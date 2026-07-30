"""Paired benchmark statistics with deterministic bootstrap and Holm scope."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Iterable, Sequence

from .metrics import canonical_metric, macro_mean


DEFAULT_BOOTSTRAP_RESAMPLES = 10_000


@dataclass(frozen=True)
class ConfidenceInterval:
    lower: float
    upper: float
    level: float = 0.95
    method: str = "paired_percentile_bootstrap"
    resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES


@dataclass(frozen=True)
class WinLossTie:
    wins: int
    losses: int
    ties: int

    @property
    def n(self) -> int:
        return self.wins + self.losses + self.ties


@dataclass(frozen=True)
class PairedStatistics:
    n: int
    baseline_point_estimate: float
    candidate_point_estimate: float
    paired_delta: float
    ci95: ConfidenceInterval
    rank_biserial_effect: float
    counts: WinLossTie


def deterministic_seed(material: str | bytes) -> int:
    payload = material.encode("utf-8") if isinstance(material, str) else material
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _paired_deltas(baseline: Sequence[float], candidate: Sequence[float]) -> list[float]:
    if len(baseline) != len(candidate) or not baseline:
        raise ValueError("paired statistics require equal non-empty sequences")
    return [float(canonical_metric(cand) - canonical_metric(base)) for base, cand in zip(baseline, candidate)]


def win_loss_tie(baseline: Sequence[float], candidate: Sequence[float]) -> WinLossTie:
    wins = losses = ties = 0
    for delta in _paired_deltas(baseline, candidate):
        canonical = canonical_metric(delta)
        if canonical > 0:
            wins += 1
        elif canonical < 0:
            losses += 1
        else:
            ties += 1
    return WinLossTie(wins, losses, ties)


def rank_biserial_effect(deltas: Sequence[float]) -> float:
    nonzero = [(abs(delta), 1 if delta > 0 else -1) for delta in deltas if canonical_metric(delta) != 0]
    if not nonzero:
        return 0.0
    ordered = sorted(nonzero, key=lambda item: item[0])
    signed_rank_sum = 0.0
    total_rank_sum = 0.0
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and canonical_metric(ordered[end][0]) == canonical_metric(ordered[index][0]):
            end += 1
        average_rank = ((index + 1) + end) / 2.0
        for _, sign in ordered[index:end]:
            signed_rank_sum += sign * average_rank
            total_rank_sum += average_rank
        index = end
    return float(canonical_metric(signed_rank_sum / total_rank_sum))


def _percentile(sorted_values: Sequence[float], probability: float) -> float:
    if not 0 <= probability <= 1 or not sorted_values:
        raise ValueError("invalid percentile input")
    position = probability * (len(sorted_values) - 1)
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    fraction = position - lower_index
    value = sorted_values[lower_index] + fraction * (sorted_values[upper_index] - sorted_values[lower_index])
    return float(canonical_metric(value))


def paired_bootstrap_ci(
    baseline: Sequence[float],
    candidate: Sequence[float],
    *,
    resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    confidence_level: float = 0.95,
    seed: int | str | bytes = 0,
) -> ConfidenceInterval:
    if resamples <= 0:
        raise ValueError("bootstrap resamples must be positive")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between zero and one")
    deltas = _paired_deltas(baseline, candidate)
    rng_seed = deterministic_seed(seed) if isinstance(seed, (str, bytes)) else seed
    rng = random.Random(rng_seed)
    n = len(deltas)
    bootstrap = []
    for _ in range(resamples):
        total = 0.0
        for _ in range(n):
            total += deltas[rng.randrange(n)]
        bootstrap.append(total / n)
    bootstrap.sort()
    alpha = (1.0 - confidence_level) / 2.0
    return ConfidenceInterval(
        lower=_percentile(bootstrap, alpha),
        upper=_percentile(bootstrap, 1.0 - alpha),
        level=confidence_level,
        resamples=resamples,
    )


def paired_statistics(
    baseline: Sequence[float],
    candidate: Sequence[float],
    *,
    seed: int | str | bytes,
    resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
) -> PairedStatistics:
    deltas = _paired_deltas(baseline, candidate)
    counts = win_loss_tie(baseline, candidate)
    baseline_point = macro_mean(baseline)
    candidate_point = macro_mean(candidate)
    return PairedStatistics(
        n=len(deltas),
        baseline_point_estimate=baseline_point,
        candidate_point_estimate=candidate_point,
        paired_delta=float(canonical_metric(candidate_point) - canonical_metric(baseline_point)),
        ci95=paired_bootstrap_ci(baseline, candidate, resamples=resamples, seed=seed),
        rank_biserial_effect=rank_biserial_effect(deltas),
        counts=counts,
    )


def holm_adjust(p_values: Iterable[float]) -> tuple[float, ...]:
    """Return Holm-adjusted p-values in the caller's original order."""

    values = list(p_values)
    if any(value < 0 or value > 1 for value in values):
        raise ValueError("p-values must be in [0, 1]")
    ordered = sorted(enumerate(values), key=lambda item: (item[1], item[0]))
    adjusted = [0.0] * len(values)
    running = 0.0
    total = len(values)
    for rank, (original_index, value) in enumerate(ordered):
        running = max(running, min(1.0, (total - rank) * value))
        adjusted[original_index] = float(canonical_metric(running))
    return tuple(adjusted)
