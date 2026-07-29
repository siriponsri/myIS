"""Exact Track S usage aggregation and prospective budget checks."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable


@dataclass(frozen=True)
class UsageRecord:
    arm: str | None
    seed: int | None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    retries: int = 0
    rollouts: int = 0
    usd: Decimal = Decimal("0")
    shared: bool = False

    def validate(self) -> None:
        if self.shared and (self.arm is not None or self.seed is not None):
            raise ValueError("shared usage cannot be assigned to an arm or seed")
        if not self.shared and not self.arm:
            raise ValueError("non-shared usage requires an arm")
        for name, value in {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "latency_ms": self.latency_ms,
            "retries": self.retries,
            "rollouts": self.rollouts,
        }.items():
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.usd < 0:
            raise ValueError("usd must be non-negative")


@dataclass(frozen=True)
class UsageTotals:
    input_tokens: int
    output_tokens: int
    latency_ms: int
    retries: int
    rollouts: int
    usd: Decimal


@dataclass(frozen=True)
class UsageSummary:
    total: UsageTotals
    shared: UsageTotals
    by_arm: dict[str, UsageTotals]
    by_seed: dict[tuple[str, int], UsageTotals]


@dataclass(frozen=True)
class BudgetCaps:
    rollouts_per_seed: int = 160
    rollouts_per_arm: int = 480
    usd_per_arm: Decimal = Decimal("20")
    shared_usd: Decimal = Decimal("30")
    target_usd: Decimal = Decimal("90")
    hard_stop_usd: Decimal = Decimal("100")


@dataclass(frozen=True)
class BudgetCheck:
    allowed: bool
    breaches: tuple[str, ...]
    warnings: tuple[str, ...]
    prospective: UsageSummary


def aggregate_usage(records: Iterable[UsageRecord]) -> UsageSummary:
    materialized = tuple(records)
    for record in materialized:
        record.validate()
    total = _sum_records(materialized)
    shared = _sum_records(record for record in materialized if record.shared)
    arms = sorted({record.arm for record in materialized if record.arm is not None})
    seeds = sorted(
        {(record.arm, record.seed) for record in materialized if record.arm is not None and record.seed is not None}
    )
    return UsageSummary(
        total=total,
        shared=shared,
        by_arm={
            str(arm): _sum_records(record for record in materialized if record.arm == arm)
            for arm in arms
        },
        by_seed={
            (str(arm), int(seed)): _sum_records(
                record for record in materialized
                if record.arm == arm and record.seed == seed
            )
            for arm, seed in seeds
        },
    )


def check_prospective_caps(
    existing: Iterable[UsageRecord], proposed: Iterable[UsageRecord],
    *, caps: BudgetCaps = BudgetCaps(),
) -> BudgetCheck:
    summary = aggregate_usage((*tuple(existing), *tuple(proposed)))
    breaches: list[str] = []
    warnings: list[str] = []
    for (arm, seed), totals in sorted(summary.by_seed.items()):
        if totals.rollouts > caps.rollouts_per_seed:
            breaches.append(
                f"{arm}/seed={seed} rollouts {totals.rollouts} exceed {caps.rollouts_per_seed}"
            )
    for arm, totals in sorted(summary.by_arm.items()):
        if totals.rollouts > caps.rollouts_per_arm:
            breaches.append(f"{arm} rollouts {totals.rollouts} exceed {caps.rollouts_per_arm}")
        if totals.usd > caps.usd_per_arm:
            breaches.append(f"{arm} USD {totals.usd} exceeds {caps.usd_per_arm}")
    if summary.shared.usd > caps.shared_usd:
        breaches.append(f"shared USD {summary.shared.usd} exceeds {caps.shared_usd}")
    if summary.total.usd > caps.hard_stop_usd:
        breaches.append(f"total USD {summary.total.usd} exceeds hard stop {caps.hard_stop_usd}")
    elif summary.total.usd > caps.target_usd:
        warnings.append(f"total USD {summary.total.usd} exceeds target {caps.target_usd}")
    return BudgetCheck(not breaches, tuple(breaches), tuple(warnings), summary)


def _sum_records(records: Iterable[UsageRecord]) -> UsageTotals:
    materialized = tuple(records)
    return UsageTotals(
        input_tokens=sum(record.input_tokens for record in materialized),
        output_tokens=sum(record.output_tokens for record in materialized),
        latency_ms=sum(record.latency_ms for record in materialized),
        retries=sum(record.retries for record in materialized),
        rollouts=sum(record.rollouts for record in materialized),
        usd=sum((record.usd for record in materialized), Decimal("0")),
    )
