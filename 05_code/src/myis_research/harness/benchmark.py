"""DAPFAM split, Track C recovery, and frozen-pool diagnostic contracts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Iterable, Mapping, Sequence

from .metrics import canonical_metric, strictly_greater
from .models import canonical_hash, is_sha256
from .statistics import PairedStatistics, paired_statistics


LEGACY_ARMS = ("dapfam", "human", "skillopt", "harnessopt")
SHARED_SPLIT_SEED = 42
SHARED_SPLIT_COUNTS = {"train": 250, "selection": 125, "joint_test": 872}


@dataclass(frozen=True)
class SplitAssignment:
    adaptation: tuple[str, ...]
    selection: tuple[str, ...]
    confirmation: tuple[str, ...]

    @property
    def hashes(self) -> dict[str, str]:
        return {
            name: hashlib.sha256("\n".join(getattr(self, name)).encode("utf-8")).hexdigest()
            for name in ("adaptation", "selection", "confirmation")
        }


def deterministic_stratified_split(
    rows: Iterable[tuple[str, str]],
    *,
    seed: int,
    ratios: tuple[float, float, float],
) -> SplitAssignment:
    """Assign query IDs with a stable hash order within each declared stratum."""

    if len(ratios) != 3 or any(value <= 0 for value in ratios) or abs(sum(ratios) - 1.0) > 1e-12:
        raise ValueError("split ratios must be three positive values summing to one")
    strata: dict[str, set[str]] = {}
    seen_queries: set[str] = set()
    for query_id, stratum in rows:
        if not query_id or not stratum:
            raise ValueError("query_id and stratum are required")
        if query_id in seen_queries:
            raise ValueError(f"duplicate query_id in split input: {query_id}")
        seen_queries.add(query_id)
        strata.setdefault(stratum, set()).add(query_id)
    output = {"adaptation": [], "selection": [], "confirmation": []}
    for stratum in sorted(strata):
        ids = sorted(
            strata[stratum],
            key=lambda query_id: (
                hashlib.sha256(f"{seed}\0{stratum}\0{query_id}".encode("utf-8")).digest(),
                query_id,
            ),
        )
        n = len(ids)
        adaptation_end = round(n * ratios[0])
        selection_end = adaptation_end + round(n * ratios[1])
        output["adaptation"].extend(ids[:adaptation_end])
        output["selection"].extend(ids[adaptation_end:selection_end])
        output["confirmation"].extend(ids[selection_end:])
    return SplitAssignment(
        *(tuple(sorted(output[name])) for name in ("adaptation", "selection", "confirmation"))
    )


@dataclass(frozen=True)
class SplitFreezeCommitment:
    seed: int
    ratios: tuple[float, float, float]
    membership_hashes: Mapping[str, str]
    qrels_snapshot_sha256: str
    query_counts: Mapping[str, int]
    out_positive_counts: Mapping[str, int]
    out_positive_available: Mapping[str, bool]
    prospective_sensitivity_report_sha256: str
    owner_decision_id: str

    def validate(self) -> None:
        names = {"adaptation", "selection", "confirmation"}
        if len(self.ratios) != 3 or any(value <= 0 for value in self.ratios):
            raise ValueError("split freeze requires three positive ratios")
        if abs(sum(self.ratios) - 1.0) > 1e-12:
            raise ValueError("split freeze ratios must sum to one")
        if set(self.membership_hashes) != names or any(
            not is_sha256(value) for value in self.membership_hashes.values()
        ):
            raise ValueError("split membership commitments must contain three SHA-256 hashes")
        if not is_sha256(self.qrels_snapshot_sha256):
            raise ValueError("qrels snapshot commitment must be SHA-256")
        if not is_sha256(self.prospective_sensitivity_report_sha256):
            raise ValueError("prospective sensitivity report commitment must be SHA-256")
        if set(self.query_counts) != names or set(self.out_positive_counts) != names:
            raise ValueError("split and OUT-positive counts must cover all three splits")
        if set(self.out_positive_available) != names:
            raise ValueError("OUT-positive availability must cover all three splits")
        for name in sorted(names):
            total = int(self.query_counts[name])
            positives = int(self.out_positive_counts[name])
            if total <= 0 or positives < 0 or positives > total:
                raise ValueError(f"invalid query/OUT-positive counts for {name}")
            if bool(self.out_positive_available[name]) != (positives > 0):
                raise ValueError(f"OUT-positive availability disagrees with count for {name}")
        if not self.owner_decision_id.strip():
            raise ValueError("split freeze requires an Owner Gate decision")

    @property
    def sha256(self) -> str:
        self.validate()
        return canonical_hash(
            {
                "seed": self.seed,
                "ratios": self.ratios,
                "membership_hashes": dict(sorted(self.membership_hashes.items())),
                "qrels_snapshot_sha256": self.qrels_snapshot_sha256,
                "query_counts": dict(sorted(self.query_counts.items())),
                "out_positive_counts": dict(sorted(self.out_positive_counts.items())),
                "out_positive_available": dict(sorted(self.out_positive_available.items())),
                "prospective_sensitivity_report_sha256": self.prospective_sensitivity_report_sha256,
                "owner_decision_id": self.owner_decision_id,
            }
        )


@dataclass(frozen=True)
class SharedSplitCommitment:
    """Hash-only shared membership with independently bound C and S firewalls."""

    seed: int
    membership_hashes: Mapping[str, str]
    qrels_snapshot_sha256: str
    c_firewall_sha256: str
    s_firewall_sha256: str
    owner_decision_id: str
    query_counts: Mapping[str, int] = field(default_factory=lambda: dict(SHARED_SPLIT_COUNTS))

    def validate(self) -> None:
        expected_roles = set(SHARED_SPLIT_COUNTS)
        counts = self.query_counts
        if self.seed != SHARED_SPLIT_SEED:
            raise ValueError("shared split seed must be 42")
        if dict(counts) != SHARED_SPLIT_COUNTS:
            raise ValueError("shared split counts must be train=250, selection=125, joint_test=872")
        if set(self.membership_hashes) != expected_roles or any(
            not is_sha256(value) for value in self.membership_hashes.values()
        ):
            raise ValueError("shared split membership commitments require three SHA-256 hashes")
        for name, value in {
            "qrels_snapshot_sha256": self.qrels_snapshot_sha256,
            "c_firewall_sha256": self.c_firewall_sha256,
            "s_firewall_sha256": self.s_firewall_sha256,
        }.items():
            if not is_sha256(value):
                raise ValueError(f"{name} must be SHA-256")
        if self.c_firewall_sha256 == self.s_firewall_sha256:
            raise ValueError("Track C and Track S require independent firewall commitments")
        if not self.owner_decision_id.strip():
            raise ValueError("shared split commitment requires an Owner Gate decision")

    @property
    def sha256(self) -> str:
        self.validate()
        return canonical_hash(
            {
                "seed": self.seed,
                "membership_hashes": dict(sorted(self.membership_hashes.items())),
                "query_counts": dict(sorted(self.query_counts.items())),
                "qrels_snapshot_sha256": self.qrels_snapshot_sha256,
                "c_firewall_sha256": self.c_firewall_sha256,
                "s_firewall_sha256": self.s_firewall_sha256,
                "owner_decision_id": self.owner_decision_id,
            }
        )


class SelectionStatus(StrEnum):
    ACCEPTED = "accepted"
    REJECTED_TIE = "rejected_tie"
    REJECTED_NOT_BETTER = "rejected_not_better"


@dataclass(frozen=True)
class SelectionDecision:
    candidate_id: str
    incumbent_id: str
    primary_metric: str
    candidate_score: float
    incumbent_score: float
    status: SelectionStatus

    @property
    def accepted(self) -> bool:
        return self.status == SelectionStatus.ACCEPTED

    @classmethod
    def decide(
        cls,
        *,
        candidate_id: str,
        incumbent_id: str,
        primary_metric: str,
        candidate_score: float,
        incumbent_score: float,
    ) -> "SelectionDecision":
        if not candidate_id or not incumbent_id or not primary_metric:
            raise ValueError("candidate, incumbent, and primary metric are required")
        candidate = canonical_metric(candidate_score)
        incumbent = canonical_metric(incumbent_score)
        if strictly_greater(candidate, incumbent):
            status = SelectionStatus.ACCEPTED
        elif candidate == incumbent:
            status = SelectionStatus.REJECTED_TIE
        else:
            status = SelectionStatus.REJECTED_NOT_BETTER
        return cls(
            candidate_id,
            incumbent_id,
            primary_metric,
            float(candidate),
            float(incumbent),
            status,
        )


class ConfirmationClassification(StrEnum):
    STATISTICALLY_SUPPORTED_SUPERIORITY = "statistically_supported_superiority"
    HIGHER_MEASURED_SCORE_UNCERTAIN_SUPERIORITY = "higher_measured_score_uncertain_superiority"
    NO_OBSERVED_IMPROVEMENT = "no_observed_improvement"


def classify_confirmation(delta: float, ci_lower: float) -> ConfirmationClassification:
    canonical_delta = canonical_metric(delta)
    if canonical_delta <= 0:
        return ConfirmationClassification.NO_OBSERVED_IMPROVEMENT
    if canonical_metric(ci_lower) > 0:
        return ConfirmationClassification.STATISTICALLY_SUPPORTED_SUPERIORITY
    return ConfirmationClassification.HIGHER_MEASURED_SCORE_UNCERTAIN_SUPERIORITY


@dataclass(frozen=True)
class CandidateExposureComparison:
    baseline_id: str
    candidate_id: str
    statistics: PairedStatistics
    classification: ConfirmationClassification
    primary_metric: str = "out_recall_at_100"
    gate_id: str = "C"

    @classmethod
    def compare(
        cls,
        *,
        baseline_id: str,
        candidate_id: str,
        baseline_scores: Sequence[float],
        candidate_scores: Sequence[float],
        bootstrap_seed: int | str | bytes,
        resamples: int = 10_000,
    ) -> "CandidateExposureComparison":
        stats = paired_statistics(baseline_scores, candidate_scores, seed=bootstrap_seed, resamples=resamples)
        return cls(baseline_id, candidate_id, stats, classify_confirmation(stats.paired_delta, stats.ci95.lower))


@dataclass(frozen=True)
class TrackCRankingDiagnostic:
    """Post-freeze Track C ranking headroom; never an independent gate claim."""

    candidate_pool_sha256: str
    no_rerank_id: str
    reranker_id: str
    no_rerank_ndcg_at_100: float
    reranked_ndcg_at_100: float
    oracle_ndcg_at_100: float
    reachable_ndcg_at_100: float
    promotions: int
    demotions: int
    failure_layer: str

    def validate(self) -> None:
        if not is_sha256(self.candidate_pool_sha256):
            raise ValueError("Track C diagnostic requires an identical frozen candidate-pool hash")
        if not self.no_rerank_id.strip() or not self.reranker_id.strip():
            raise ValueError("Track C diagnostic requires no-rerank and reranker identities")
        scores = (
            self.no_rerank_ndcg_at_100,
            self.reranked_ndcg_at_100,
            self.oracle_ndcg_at_100,
            self.reachable_ndcg_at_100,
        )
        if any(not 0.0 <= score <= 1.0 for score in scores):
            raise ValueError("Track C diagnostic nDCG values must be in [0, 1]")
        if self.reachable_ndcg_at_100 > self.oracle_ndcg_at_100:
            raise ValueError("reachable nDCG cannot exceed oracle nDCG")
        if self.promotions < 0 or self.demotions < 0 or not self.failure_layer.strip():
            raise ValueError("Track C diagnostic promotion/demotion counts and failure layer are required")


@dataclass(frozen=True)
class FrozenPoolRankingComparison:
    baseline_id: str
    candidate_id: str
    candidate_pool_sha256: str
    statistics: PairedStatistics
    classification: ConfirmationClassification
    primary_metric: str = "out_ndcg_at_100"
    track_id: str = "C"
    diagnostic_id: str = "C_DIAGNOSTIC"

    @classmethod
    def compare(
        cls,
        *,
        baseline_id: str,
        candidate_id: str,
        baseline_pool_sha256: str,
        candidate_pool_sha256: str,
        baseline_scores: Sequence[float],
        candidate_scores: Sequence[float],
        bootstrap_seed: int | str | bytes,
        resamples: int = 10_000,
    ) -> "FrozenPoolRankingComparison":
        if baseline_pool_sha256 != candidate_pool_sha256:
            raise ValueError("Track C diagnostics require an identical frozen candidate pool")
        if len(candidate_pool_sha256) != 64:
            raise ValueError("candidate pool commitment must be SHA-256")
        try:
            int(candidate_pool_sha256, 16)
        except ValueError as error:
            raise ValueError("candidate pool commitment must be SHA-256") from error
        stats = paired_statistics(baseline_scores, candidate_scores, seed=bootstrap_seed, resamples=resamples)
        return cls(
            baseline_id,
            candidate_id,
            candidate_pool_sha256,
            stats,
            classify_confirmation(stats.paired_delta, stats.ci95.lower),
        )


def validate_comparable_arms(manifests: dict[str, dict]) -> None:
    """Read-only compatibility check for historical four-arm manifests."""

    missing = set(LEGACY_ARMS) - set(manifests)
    if missing:
        raise ValueError(f"missing benchmark arms: {sorted(missing)}")
    fields = (
        ("inputs", "split_query_ids_hash"),
        ("evaluator", "hash"),
        ("method", "model_id"),
        ("method", "module_pool_hash"),
    )
    for section, field in fields:
        values = {arm: manifests[arm][section][field] for arm in LEGACY_ARMS}
        if len(set(values.values())) != 1:
            raise ValueError(f"arms are not comparable: {section}.{field} differs: {values}")
    budgets = {arm: json.dumps(manifests[arm]["budget"]["limits"], sort_keys=True) for arm in LEGACY_ARMS}
    if len(set(budgets.values())) != 1:
        raise ValueError(f"arms are not comparable: budgets differ: {budgets}")
