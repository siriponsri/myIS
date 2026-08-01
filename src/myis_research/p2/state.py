"""Deterministic P2 candidate lifecycle with a hard internal freeze barrier."""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
import re
from typing import Any, Mapping

from ..kernel.canonical import canonical_sha256
from .contracts import (
    P2BudgetProfile,
    P2ContractError,
    validate_p2_aggregate_metric,
)


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

    def __init__(self, *, request_id: str, profile: P2BudgetProfile) -> None:
        if not isinstance(profile, P2BudgetProfile):
            raise P2StateError("state machine requires a canonical loaded P2BudgetProfile")
        if profile.sha256 != canonical_sha256(profile.payload):
            raise P2StateError("loaded P2 profile hash does not match its canonical payload")
        self.request_id = request_id
        self.profile = deepcopy(profile.payload)
        self.profile_sha256 = profile.sha256
        self.state = "candidate_generation"
        self.candidates: dict[str, dict[str, Any]] = {}
        self.shortlist_ids: tuple[str, ...] = ()
        self.baseline_reproduction_receipt: dict[str, Any] | None = None
        self.freeze_receipt: dict[str, Any] | None = None
        self.selection_exposure_count = 0
        self.selection_metrics: list[dict[str, Any]] = []
        self.completed_iterations: list[int] = []
        self.iteration_records: dict[int, dict[str, Any]] = {}
        self.best_iteration_score: float | None = None
        self.no_improvement_streak = 0
        self.early_stop_eligible = False
        self.total_index_builds = 0

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
            if self._adaptive_candidates():
                raise P2StateError("frozen controls cannot be added after adaptive search starts")
            if len(same_class) >= allocation["frozen_controls"]:
                raise P2StateError("frozen control allocation exhausted")
        elif candidate.candidate_class == "preregistered_patent":
            if candidate.iteration != 0:
                raise P2StateError("preregistered patent candidates must use iteration zero")
            if self._adaptive_candidates():
                raise P2StateError("preregistered candidates cannot be added after adaptive search starts")
            if len(same_class) >= allocation["preregistered_patent_candidates"]:
                raise P2StateError("preregistered patent allocation exhausted")
        else:
            if candidate.iteration < 1:
                raise P2StateError("adaptive candidates must use iterations one through five")
            if len(same_class) >= limits["max_adaptive_candidates"]:
                raise P2StateError("adaptive candidate budget exhausted")
            if not self._base_allocation_complete():
                raise P2StateError("all frozen and preregistered candidates must precede adaptive search")
            if candidate.iteration in self.completed_iterations:
                raise P2StateError("completed iteration membership is immutable")
            active_iterations = sorted({item["iteration"] for item in self._adaptive_candidates() if item["iteration"] not in self.completed_iterations})
            expected_iteration = len(self.completed_iterations) + 1
            if active_iterations:
                if candidate.iteration != active_iterations[-1]:
                    raise P2StateError("complete the current adaptive iteration before opening the next")
            elif candidate.iteration != expected_iteration:
                raise P2StateError("adaptive iterations must be consecutive")
            per_iteration = sum(item["iteration"] == candidate.iteration for item in same_class)
            if per_iteration >= limits["candidates_per_iteration"]:
                raise P2StateError("candidates_per_iteration exceeded")

        self.candidates[candidate.candidate_id] = {
            "candidate_id": candidate.candidate_id,
            "class": candidate.candidate_class,
            "iteration": candidate.iteration,
            "spec_sha256": candidate.spec_sha256,
            "status": "generated",
        }

    def record_train(
        self,
        candidate_id: str,
        *,
        score: float | None,
        status: str = "train_complete",
        failure_reason: str | None = None,
        index_build_count: int = 1,
    ) -> None:
        if self.state not in {"candidate_generation", "train_evaluation"}:
            raise P2StateError("train outcomes require candidate generation or train evaluation")
        if candidate_id not in self.candidates:
            raise P2StateError("candidate is not in the immutable generation ledger")
        row = self.candidates[candidate_id]
        if self.state == "candidate_generation":
            if row["class"] != "adaptive_autoindex":
                raise P2StateError("only active adaptive candidates can train during generation")
            if row["iteration"] in self.completed_iterations:
                raise P2StateError("completed iteration outcomes are immutable")
        if status not in {"train_complete", "failed"}:
            raise P2StateError("train status must be complete or failed")
        if index_build_count < 0 or index_build_count > self.profile["limits"]["max_index_builds"]:
            raise P2StateError("index build count exceeds profile")
        if score is not None and (isinstance(score, bool) or not 0 <= score <= 1):
            raise P2StateError("train score must be between zero and one")
        if status == "train_complete" and score is None:
            raise P2StateError("completed train outcome requires an aggregate score")
        if status == "failed" and score is not None:
            raise P2StateError("failed train outcome cannot carry a score")
        if row["status"] != "generated":
            raise P2StateError("train outcome is immutable once recorded")
        self.total_index_builds += index_build_count
        if self.total_index_builds > self.profile["limits"]["max_index_builds"]:
            raise P2StateError("total index build budget exhausted")
        row.update({"status": status, "train_score": score, "index_build_count": index_build_count})
        if failure_reason is not None:
            row["failure_reason"] = failure_reason

    def record_iteration(self, iteration: int) -> bool:
        """Complete one adaptive iteration using only its recorded train outcomes."""

        self._require_state("candidate_generation")
        expected_iteration = len(self.completed_iterations) + 1
        if iteration != expected_iteration:
            raise P2StateError("adaptive iterations must be completed consecutively")
        members = sorted(
            (item for item in self._adaptive_candidates() if item["iteration"] == iteration),
            key=lambda item: str(item["candidate_id"]),
        )
        expected_count = self.profile["limits"]["candidates_per_iteration"]
        if len(members) != expected_count:
            raise P2StateError("completed adaptive iteration requires exactly four candidates")
        if any(item["status"] != "train_complete" or item.get("train_score") is None for item in members):
            raise P2StateError("iteration score requires completed recorded train outcomes")
        best_score = max(float(item["train_score"]) for item in members)
        record = {
            "iteration": iteration,
            "candidate_ids": [str(item["candidate_id"]) for item in members],
            "best_score": best_score,
            "status": "completed",
        }
        self.completed_iterations.append(iteration)
        self.iteration_records[iteration] = record
        if self.best_iteration_score is None or best_score > self.best_iteration_score:
            self.best_iteration_score = best_score
            self.no_improvement_streak = 0
        else:
            self.no_improvement_streak += 1
        stopping = self.profile["stopping"]
        self.early_stop_eligible = (
            len(self.completed_iterations) >= stopping["min_iterations_before_early_stop"]
            and self.no_improvement_streak >= stopping["no_improvement_patience"]
        )
        return self.early_stop_eligible

    def finish_generation(self) -> None:
        self._require_state("candidate_generation")
        if not self._base_allocation_complete():
            raise P2StateError("generation requires all frozen controls and preregistered candidates")
        adaptive_ids = {str(item["candidate_id"]) for item in self._adaptive_candidates()}
        completed_ids = {
            str(candidate_id)
            for record in self.iteration_records.values()
            for candidate_id in record["candidate_ids"]
        }
        if adaptive_ids != completed_ids:
            raise P2StateError("every adaptive candidate must belong to one completed iteration")
        maximum_iterations = self.profile["limits"]["max_adaptive_iterations"]
        if len(self.completed_iterations) < maximum_iterations and not self.early_stop_eligible:
            raise P2StateError("generation can stop early only after valid completed iterations")
        if any(item["status"] == "failed" for item in self._adaptive_candidates()):
            self.state = "blocked"
            raise P2StateError("adaptive train failure blocks shortlist and selection")
        self.state = "train_evaluation"

    def record_baseline_reproduction(
        self,
        *,
        baseline_id: str,
        expected_metric: Mapping[str, Any],
        tolerance: float,
        dataset_lineage_sha256: str,
        config_sha256: str,
        retriever_sha256: str,
        evaluator_sha256: str,
        result: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Record one immutable hash-bound baseline reproduction receipt."""

        self._require_state("train_evaluation")
        if self.baseline_reproduction_receipt is not None:
            raise P2StateError("baseline reproduction receipt is immutable")
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]+", baseline_id):
            raise P2StateError("baseline identity must be stable lowercase text")
        baseline_candidate = self.candidates.get(baseline_id)
        if baseline_candidate is None or baseline_candidate["class"] != "frozen_control":
            raise P2StateError("baseline identity must name a registered frozen control")
        if baseline_candidate["status"] != "train_complete":
            raise P2StateError("baseline reproduction requires its completed train outcome")
        if isinstance(tolerance, bool) or not 0 <= tolerance <= 1:
            raise P2StateError("baseline tolerance must be between zero and one")
        for label, value in {
            "dataset lineage": dataset_lineage_sha256,
            "config": config_sha256,
            "retriever": retriever_sha256,
            "evaluator": evaluator_sha256,
        }.items():
            if not re.fullmatch(r"[a-f0-9]{64}", value):
                raise P2StateError(f"baseline {label} hash must be SHA-256")
        try:
            expected = validate_p2_aggregate_metric(expected_metric)
            observed = validate_p2_aggregate_metric(result)
        except P2ContractError as error:
            raise P2StateError(str(error)) from error
        if expected["candidate_id"] != baseline_id or observed["candidate_id"] != baseline_id:
            raise P2StateError("baseline metric identity must match baseline_id")
        identity_fields = ("candidate_id", "name", "n", "scope", "split", "direction", "denominator", "evidence_role")
        if any(expected[key] != observed[key] for key in identity_fields):
            raise P2StateError("baseline result identity differs from the expected metric")
        status = "passed" if abs(float(observed["value"]) - float(expected["value"])) <= tolerance else "failed"
        body: dict[str, Any] = {
            "schema_version": "myis.p2-baseline-reproduction-receipt.v1",
            "request_id": self.request_id,
            "phase_id": "P2_SCOPE_DEVELOPMENT",
            "campaign_revision": self.profile["campaign_revision"],
            "budget_profile_id": self.profile["profile_id"],
            "budget_profile_sha256": self.profile_sha256,
            "baseline_id": baseline_id,
            "expected_metric": expected,
            "tolerance": tolerance,
            "dataset_lineage_sha256": dataset_lineage_sha256,
            "config_sha256": config_sha256,
            "retriever_sha256": retriever_sha256,
            "evaluator_sha256": evaluator_sha256,
            "result": observed,
            "status": status,
        }
        body["receipt_sha256"] = canonical_sha256(body)
        self.baseline_reproduction_receipt = body
        if status != "passed":
            self.state = "blocked"
            raise P2StateError("baseline reproduction failure blocks shortlist and selection")
        return deepcopy(body)

    def finish_train(self) -> None:
        self._require_state("train_evaluation")
        if any(item["status"] == "generated" for item in self.candidates.values()):
            raise P2StateError("all generated candidates must receive a train outcome")
        if any(item["status"] == "failed" for item in self.candidates.values()):
            self.state = "blocked"
            raise P2StateError("train failure blocks shortlist and selection")
        if self.baseline_reproduction_receipt is None or self.baseline_reproduction_receipt["status"] != "passed":
            self.state = "blocked"
            raise P2StateError("baseline reproduction receipt must pass before shortlist and selection")
        self.state = "shortlist"

    def build_shortlist(self, *, incumbent_score: float) -> tuple[str, ...]:
        self._require_state("shortlist")
        if isinstance(incumbent_score, bool) or not 0 <= incumbent_score <= 1:
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
        compiler_sha256: str,
        config_sha256: str,
        retriever_sha256: str,
        evaluator_sha256: str,
    ) -> dict[str, Any]:
        self._require_state("shortlist_ready")
        if self.freeze_receipt is not None:
            raise P2StateError("shortlist freeze is immutable and can occur once")
        if self.baseline_reproduction_receipt is None or self.baseline_reproduction_receipt["status"] != "passed":
            raise P2StateError("shortlist freeze requires a passed baseline receipt")
        if self.profile["limits"]["selection_exposure_limit"] != 1:
            raise P2StateError("P2 requires a one-shot selection exposure limit")
        for label, value in {
            "compiler": compiler_sha256,
            "config": config_sha256,
            "retriever": retriever_sha256,
            "evaluator": evaluator_sha256,
        }.items():
            if not re.fullmatch(r"[a-f0-9]{64}", value):
                raise P2StateError(f"{label} hash must be SHA-256")
        baseline = self.baseline_reproduction_receipt
        for field, value in {
            "config_sha256": config_sha256,
            "retriever_sha256": retriever_sha256,
            "evaluator_sha256": evaluator_sha256,
        }.items():
            if value != baseline[field]:
                raise P2StateError(f"{field} must match the immutable baseline lineage")
        body: dict[str, Any] = {
            "schema_version": "myis.p2-shortlist-freeze-receipt.v1",
            "request_id": self.request_id,
            "phase_id": "P2_SCOPE_DEVELOPMENT",
            "campaign_revision": self.profile["campaign_revision"],
            "budget_profile_id": self.profile["profile_id"],
            "budget_profile_sha256": self.profile_sha256,
            "baseline_reproduction_receipt_sha256": self.baseline_reproduction_receipt["receipt_sha256"],
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
        return deepcopy(body)

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
        if any(item["candidate_id"] == candidate_id for item in self.selection_metrics):
            raise P2StateError("selection outcome is immutable and unique per finalist")
        if "candidate_id" in metric:
            raise P2StateError("candidate_id is supplied by the frozen selection membership")
        row = {"candidate_id": candidate_id, **dict(metric)}
        try:
            validated = validate_p2_aggregate_metric(row, selection=True)
        except P2ContractError as error:
            raise P2StateError(str(error)) from error
        self.selection_metrics.append(validated)

    def close(self) -> None:
        if self.state == "selection_exposed":
            recorded_ids = [str(item["candidate_id"]) for item in self.selection_metrics]
            if set(recorded_ids) != set(self.shortlist_ids) or len(recorded_ids) != len(set(recorded_ids)):
                raise P2StateError("selection cannot close until every finalist has exactly one aggregate result")
            self.state = "closed"
            return
        if self.state != "closed":
            raise P2StateError("run cannot close before freeze and optional selection")

    def build_selection_receipt(self) -> dict[str, Any]:
        self._require_state("closed")
        if self.freeze_receipt is None:
            raise P2StateError("selection receipt requires an immutable freeze receipt")
        if self.selection_exposure_count != 1 or not self.shortlist_ids:
            raise P2StateError("accepted selection receipt requires one nonempty exposure")
        recorded_ids = [str(item["candidate_id"]) for item in self.selection_metrics]
        if set(recorded_ids) != set(self.shortlist_ids) or len(recorded_ids) != len(set(recorded_ids)):
            raise P2StateError("selection receipt requires exactly one aggregate result per finalist")
        metric_by_id = {str(item["candidate_id"]): item for item in self.selection_metrics}
        body: dict[str, Any] = {
            "schema_version": "myis.p2-selection-receipt.v1",
            "request_id": self.request_id,
            "campaign_revision": self.profile["campaign_revision"],
            "budget_profile_id": self.profile["profile_id"],
            "budget_profile_sha256": self.profile_sha256,
            "candidate_ids": list(self.shortlist_ids),
            "shortlist_freeze_receipt_sha256": self.freeze_receipt["receipt_sha256"],
            "selection_exposure_count": self.selection_exposure_count,
            "status": "accepted",
            "metrics": [deepcopy(metric_by_id[candidate_id]) for candidate_id in self.shortlist_ids],
        }
        body["receipt_sha256"] = canonical_sha256(body)
        return body

    def build_candidate_ledger(self) -> dict[str, Any]:
        if self.state in {"candidate_generation", "train_evaluation", "blocked"}:
            raise P2StateError("complete candidate ledger requires successful train and baseline gates")
        body: dict[str, Any] = {
            "schema_version": "myis.p2-candidate-ledger.v1",
            "request_id": self.request_id,
            "campaign_revision": self.profile["campaign_revision"],
            "budget_profile_id": self.profile["profile_id"],
            "budget_profile_sha256": self.profile_sha256,
            "candidate_count": len(self.candidates),
            "candidates": [deepcopy(self.candidates[candidate_id]) for candidate_id in sorted(self.candidates)],
            "iterations": [deepcopy(self.iteration_records[index]) for index in sorted(self.iteration_records)],
        }
        body["ledger_sha256"] = canonical_sha256(body)
        return body

    def summary(self) -> dict[str, Any]:
        baseline_status = (
            self.baseline_reproduction_receipt["status"]
            if self.baseline_reproduction_receipt is not None
            else "pending"
        )
        return {
            "request_id": self.request_id,
            "state": self.state,
            "candidate_count": len(self.candidates),
            "shortlist_ids": list(self.shortlist_ids),
            "selection_exposure_count": self.selection_exposure_count,
            "selection_metric_count": len(self.selection_metrics),
            "completed_iterations": list(self.completed_iterations),
            "iteration_records": [deepcopy(self.iteration_records[index]) for index in sorted(self.iteration_records)],
            "best_iteration_score": self.best_iteration_score,
            "no_improvement_streak": self.no_improvement_streak,
            "early_stop_eligible": self.early_stop_eligible,
            "total_index_builds": self.total_index_builds,
            "baseline_reproduction_status": baseline_status,
            "baseline_reproduction_receipt_sha256": (
                self.baseline_reproduction_receipt["receipt_sha256"]
                if self.baseline_reproduction_receipt is not None
                else None
            ),
        }

    def _adaptive_candidates(self) -> list[dict[str, Any]]:
        return [item for item in self.candidates.values() if item["class"] == "adaptive_autoindex"]

    def _base_allocation_complete(self) -> bool:
        allocation = self.profile["candidate_allocation"]
        return (
            sum(item["class"] == "frozen_control" for item in self.candidates.values()) == allocation["frozen_controls"]
            and sum(item["class"] == "preregistered_patent" for item in self.candidates.values()) == allocation["preregistered_patent_candidates"]
        )

    def _require_state(self, expected: str) -> None:
        if self.state != expected:
            raise P2StateError(f"operation requires state {expected!r}, current state is {self.state!r}")
