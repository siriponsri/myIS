"""Deterministic P2 candidate lifecycle with a hard internal freeze barrier."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import re
from typing import Any, Mapping

from ..kernel.canonical import canonical_sha256


class P2StateError(RuntimeError):
    """Raised when a P2 lifecycle transition violates the freeze contract."""


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    candidate_class: str
    iteration: int
    spec_sha256: str


class P2RunStateMachine:
    """One scientific P2 run; selection can be exposed at most once."""

    def __init__(self, *, request_id: str, profile: Mapping[str, Any]) -> None:
        self.request_id = request_id
        self.profile = dict(profile)
        self.state = "candidate_generation"
        self.candidates: dict[str, dict[str, Any]] = {}
        self.shortlist_ids: tuple[str, ...] = ()
        self.freeze_receipt: dict[str, Any] | None = None
        self.selection_exposure_count = 0
        self.selection_metrics: list[dict[str, Any]] = []
        self.completed_iterations: list[int] = []
        self.best_iteration_score: float | None = None
        self.no_improvement_streak = 0
        self.total_index_builds = 0
        self.baseline_reproduction_status = "pending"

    def register_candidate(self, candidate: Candidate) -> None:
        self._require_state("candidate_generation")
        if candidate.candidate_id in self.candidates:
            raise P2StateError("candidate IDs are immutable and must be unique")
        limits = self.profile["limits"]
        allocation = self.profile["candidate_allocation"]
        if len(self.candidates) >= limits["max_candidates_total"]:
            raise P2StateError("candidate budget exhausted")
        if candidate.candidate_class not in {"frozen_control", "preregistered_patent", "adaptive_autoindex"}:
            raise P2StateError("unsupported candidate class")
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]+", candidate.candidate_id):
            raise P2StateError("candidate_id must be stable lowercase text")
        if not re.fullmatch(r"[a-f0-9]{64}", candidate.spec_sha256):
            raise P2StateError("candidate spec hash must be SHA-256")
        if candidate.iteration < 0 or candidate.iteration > limits["max_adaptive_iterations"]:
            raise P2StateError("candidate iteration exceeds the profile")
        same_class = [item for item in self.candidates.values() if item["class"] == candidate.candidate_class]
        if candidate.candidate_class == "frozen_control":
            if candidate.iteration != 0:
                raise P2StateError("frozen controls must use iteration zero")
            if len(same_class) >= allocation["frozen_controls"]:
                raise P2StateError("frozen control allocation exhausted")
        elif candidate.candidate_class == "preregistered_patent":
            if candidate.iteration != 0:
                raise P2StateError("preregistered patent candidates must use iteration zero")
            if len(same_class) >= allocation["preregistered_patent_candidates"]:
                raise P2StateError("preregistered patent allocation exhausted")
        else:
            if candidate.iteration < 1:
                raise P2StateError("adaptive candidates must use iterations one through five")
            adaptive = [item for item in self.candidates.values() if item["class"] == candidate.candidate_class]
            if len(adaptive) >= limits["max_adaptive_candidates"]:
                raise P2StateError("adaptive candidate budget exhausted")
            per_iteration = sum(item["iteration"] == candidate.iteration for item in adaptive)
            if per_iteration >= limits["candidates_per_iteration"]:
                raise P2StateError("candidates_per_iteration exceeded")
        self.candidates[candidate.candidate_id] = {
            "candidate_id": candidate.candidate_id,
            "class": candidate.candidate_class,
            "iteration": candidate.iteration,
            "spec_sha256": candidate.spec_sha256,
            "status": "generated",
        }

    def finish_generation(self) -> None:
        self._require_state("candidate_generation")
        if not self.candidates:
            raise P2StateError("cannot evaluate an empty candidate ledger")
        allocation = self.profile["candidate_allocation"]
        counts = {
            candidate_class: sum(item["class"] == candidate_class for item in self.candidates.values())
            for candidate_class in ("frozen_control", "preregistered_patent", "adaptive_autoindex")
        }
        if counts["frozen_control"] != allocation["frozen_controls"]:
            raise P2StateError("generation requires all frozen controls")
        if counts["preregistered_patent"] != allocation["preregistered_patent_candidates"]:
            raise P2StateError("generation requires all preregistered patent candidates")
        self.state = "train_evaluation"

    def record_train(
        self,
        candidate_id: str,
        *,
        score: float | None,
        status: str = "train_complete",
        failure_reason: str | None = None,
        index_build_count: int = 1,
    ) -> None:
        self._require_state("train_evaluation")
        if candidate_id not in self.candidates:
            raise P2StateError("candidate is not in the frozen generation ledger")
        if status not in {"train_complete", "failed"}:
            raise P2StateError("train status must be complete or failed")
        if index_build_count < 0 or index_build_count > self.profile["limits"]["max_index_builds"]:
            raise P2StateError("index build count exceeds profile")
        if score is not None and not 0 <= score <= 1:
            raise P2StateError("train score must be between zero and one")
        row = self.candidates[candidate_id]
        if row["status"] != "generated":
            raise P2StateError("train outcome is immutable once recorded")
        self.total_index_builds += index_build_count
        if self.total_index_builds > self.profile["limits"]["max_index_builds"]:
            raise P2StateError("total index build budget exhausted")
        row.update({"status": status, "train_score": score, "index_build_count": index_build_count})
        if failure_reason is not None:
            row["failure_reason"] = failure_reason

    def finish_train(self) -> None:
        self._require_state("train_evaluation")
        if any(item["status"] == "generated" for item in self.candidates.values()):
            raise P2StateError("all generated candidates must receive a train outcome")
        if any(item["status"] == "failed" for item in self.candidates.values()):
            self.state = "blocked"
            raise P2StateError("train failure blocks shortlist and selection")
        if self.baseline_reproduction_status != "passed":
            self.state = "blocked"
            raise P2StateError("baseline reproduction must pass before shortlist and selection")
        self.state = "shortlist"

    def record_baseline_reproduction(self, *, passed: bool) -> None:
        """Close the mandatory baseline reproduction check before shortlist."""

        self._require_state("train_evaluation")
        if self.baseline_reproduction_status != "pending":
            raise P2StateError("baseline reproduction status is immutable")
        if not passed:
            self.baseline_reproduction_status = "failed"
            self.state = "blocked"
            raise P2StateError("baseline reproduction failure blocks shortlist and selection")
        self.baseline_reproduction_status = "passed"

    def record_iteration(self, iteration: int, *, best_score: float) -> bool:
        """Record one completed adaptive iteration and return early-stop eligibility."""

        # Adaptive search is complete before train evaluation begins. Keeping
        # this transition state-bound prevents late search bookkeeping from
        # mutating a run after the freeze barrier or one-shot selection.
        self._require_state("candidate_generation")
        if iteration < 1 or iteration > self.profile["limits"]["max_adaptive_iterations"]:
            raise P2StateError("iteration exceeds the profile")
        if iteration in self.completed_iterations:
            raise P2StateError("iteration completion is immutable")
        if not 0 <= best_score <= 1:
            raise P2StateError("iteration score must be between zero and one")
        self.completed_iterations.append(iteration)
        self.completed_iterations.sort()
        if self.best_iteration_score is None or best_score > self.best_iteration_score:
            self.best_iteration_score = best_score
            self.no_improvement_streak = 0
        else:
            self.no_improvement_streak += 1
        stopping = self.profile["stopping"]
        return (
            len(self.completed_iterations) >= stopping["min_iterations_before_early_stop"]
            and self.no_improvement_streak >= stopping["no_improvement_patience"]
        )

    def build_shortlist(self, *, incumbent_score: float) -> tuple[str, ...]:
        self._require_state("shortlist")
        if not 0 <= incumbent_score <= 1:
            raise P2StateError("incumbent score must be between zero and one")
        eligible = [
            item for item in self.candidates.values()
            if item["status"] == "train_complete" and item.get("train_score") is not None and item["train_score"] > incumbent_score
        ]
        grouped: dict[float, list[dict[str, Any]]] = defaultdict(list)
        for item in eligible:
            grouped[float(item["train_score"])].append(item)
        shortlisted: list[str] = []
        for score in sorted(grouped, reverse=True):
            group = grouped[score]
            if len(group) != 1:
                for item in group:
                    item["status"] = "rejected"
                    item["selection_eligible"] = False
                continue
            if len(shortlisted) >= self.profile["limits"]["max_selection_finalists"]:
                group[0]["status"] = "rejected"
                group[0]["selection_eligible"] = False
                continue
            group[0]["status"] = "frozen"
            group[0]["selection_eligible"] = True
            shortlisted.append(group[0]["candidate_id"])
        for item in self.candidates.values():
            item.setdefault("selection_eligible", item["candidate_id"] in shortlisted)
        self.shortlist_ids = tuple(shortlisted)
        self.state = "shortlist_ready"
        return self.shortlist_ids

    def freeze_shortlist(
        self,
        *,
        budget_profile_sha256: str,
        compiler_sha256: str,
        config_sha256: str,
        retriever_sha256: str,
        evaluator_sha256: str,
    ) -> dict[str, Any]:
        self._require_state("shortlist_ready")
        if self.freeze_receipt is not None:
            raise P2StateError("shortlist freeze is immutable and can occur once")
        if not re.fullmatch(r"[a-f0-9]{64}", budget_profile_sha256):
            raise P2StateError("budget profile hash must be SHA-256")
        if self.profile["limits"]["selection_exposure_limit"] != 1:
            raise P2StateError("P2 requires a one-shot selection exposure limit")
        for label, value in {
            "budget profile": budget_profile_sha256,
            "compiler": compiler_sha256,
            "config": config_sha256,
            "retriever": retriever_sha256,
            "evaluator": evaluator_sha256,
        }.items():
            if not re.fullmatch(r"[a-f0-9]{64}", value):
                raise P2StateError(f"{label} hash must be SHA-256")
        body: dict[str, Any] = {
            "schema_version": "myis.p2-shortlist-freeze-receipt.v1",
            "request_id": self.request_id,
            "phase_id": "P2_SCOPE_DEVELOPMENT",
            "campaign_revision": self.profile["campaign_revision"],
            "budget_profile_id": self.profile["profile_id"],
            "budget_profile_sha256": budget_profile_sha256,
            "candidate_ids": list(self.shortlist_ids),
            "candidate_spec_hashes": {candidate_id: self.candidates[candidate_id]["spec_sha256"] for candidate_id in self.shortlist_ids},
            "compiler_sha256": compiler_sha256,
            "config_sha256": config_sha256,
            "retriever_sha256": retriever_sha256,
            "evaluator_sha256": evaluator_sha256,
            "selection_rule": "strictly_greater_reject_ties",
            "selection_exposure_count": 0,
            "status": "validated_immutable",
        }
        body["receipt_sha256"] = canonical_sha256(body)
        self.freeze_receipt = body
        self.state = "frozen"
        return dict(body)

    def open_selection(self) -> tuple[str, ...]:
        self._require_state("frozen")
        if self.selection_exposure_count >= self.profile["limits"]["selection_exposure_limit"]:
            raise P2StateError("selection exposure limit already consumed")
        if not self.shortlist_ids:
            self.state = "closed"
            return ()
        self.selection_exposure_count = 1
        self.state = "selection_exposed"
        return self.shortlist_ids

    def record_selection(self, candidate_id: str, *, metric: Mapping[str, Any]) -> None:
        self._require_state("selection_exposed")
        if candidate_id not in self.shortlist_ids:
            raise P2StateError("selection may evaluate only frozen shortlist IDs")
        self.selection_metrics.append({"candidate_id": candidate_id, **dict(metric)})

    def close(self) -> None:
        if self.state not in {"selection_exposed", "closed"}:
            raise P2StateError("run cannot close before freeze and optional selection")
        self.state = "closed"

    def build_selection_receipt(self) -> dict[str, Any]:
        if self.state not in {"selection_exposed", "closed"}:
            raise P2StateError("selection receipt requires one-shot exposure")
        if self.freeze_receipt is None:
            raise P2StateError("selection receipt requires an immutable freeze receipt")
        body: dict[str, Any] = {
            "schema_version": "myis.p2-selection-receipt.v1",
            "request_id": self.request_id,
            "candidate_ids": list(self.shortlist_ids),
            "shortlist_freeze_receipt_sha256": self.freeze_receipt["receipt_sha256"],
            "selection_exposure_count": self.selection_exposure_count,
            "status": "accepted" if self.selection_exposure_count == 1 else "blocked",
            "metrics": list(self.selection_metrics),
        }
        body["receipt_sha256"] = canonical_sha256(body)
        return body

    def summary(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "state": self.state,
            "candidate_count": len(self.candidates),
            "shortlist_ids": list(self.shortlist_ids),
            "selection_exposure_count": self.selection_exposure_count,
            "selection_metric_count": len(self.selection_metrics),
            "completed_iterations": list(self.completed_iterations),
            "best_iteration_score": self.best_iteration_score,
            "no_improvement_streak": self.no_improvement_streak,
            "total_index_builds": self.total_index_builds,
            "baseline_reproduction_status": self.baseline_reproduction_status,
        }

    def _require_state(self, expected: str) -> None:
        if self.state != expected:
            raise P2StateError(f"operation requires state {expected!r}, current state is {self.state!r}")
