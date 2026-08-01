from __future__ import annotations

from pathlib import Path

import pytest

from myis_research.p2 import (
    Candidate,
    P2RunStateMachine,
    P2StateError,
    load_profile,
    validate_p2_artifact,
)


ROOT = Path(__file__).resolve().parents[1]
DATASET_HASH = "a" * 64
COMPILER_HASH = "c" * 64
CONFIG_HASH = "d" * 64
RETRIEVER_HASH = "e" * 64
EVALUATOR_HASH = "f" * 64


def _machine() -> P2RunStateMachine:
    return P2RunStateMachine(request_id="p2-state-test", profile=load_profile(ROOT))


def _metric(candidate_id: str, value: float, *, split: str = "train") -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "name": "recall_at_100",
        "value": value,
        "n": 16,
        "scope": "OUT",
        "split": split,
        "direction": "maximize",
        "denominator": "macro_mean_per_query_relevant_families",
        "evidence_role": "primary",
    }


def _register_base(machine: P2RunStateMachine) -> None:
    for index in range(4):
        machine.register_candidate(Candidate(f"control-{index}", "frozen_control", 0, "1" * 64))
    for index in range(8):
        machine.register_candidate(Candidate(f"patent-{index}", "preregistered_patent", 0, "2" * 64))


def _complete_iteration(machine: P2RunStateMachine, iteration: int, best_score: float) -> bool:
    for index in range(4):
        candidate_id = f"adaptive-{iteration}-{index}"
        machine.register_candidate(Candidate(candidate_id, "adaptive_autoindex", iteration, "3" * 64))
        machine.record_train(candidate_id, score=best_score - index * 0.01)
    return machine.record_iteration(iteration)


def _finish_generation(machine: P2RunStateMachine, scores: tuple[float, ...] = (0.6, 0.7, 0.7, 0.7)) -> None:
    _register_base(machine)
    for iteration, score in enumerate(scores, start=1):
        _complete_iteration(machine, iteration, score)
    machine.finish_generation()


def _record_baseline(machine: P2RunStateMachine, *, result_value: float = 0.95) -> dict[str, object]:
    return machine.record_baseline_reproduction(
        baseline_id="control-0",
        expected_metric=_metric("control-0", 0.95),
        tolerance=0.001,
        dataset_lineage_sha256=DATASET_HASH,
        config_sha256=CONFIG_HASH,
        retriever_sha256=RETRIEVER_HASH,
        evaluator_sha256=EVALUATOR_HASH,
        result=_metric("control-0", result_value),
    )


def _train_base(
    machine: P2RunStateMachine,
    *,
    tie: bool = False,
    failure: bool = False,
    baseline: bool = True,
) -> None:
    scores = [0.8, 0.8, 0.4, 0.3] if tie else [0.95, 0.9, 0.4, 0.3]
    scores.extend([0.85, 0.8, 0.75, 0.65, 0.45, 0.35, 0.25, 0.15])
    for index, candidate_id in enumerate(
        candidate_id for candidate_id, row in machine.candidates.items() if row["iteration"] == 0
    ):
        if failure and index == 0:
            machine.record_train(candidate_id, score=None, status="failed", failure_reason="fixture failure")
        else:
            machine.record_train(candidate_id, score=scores[index])
    if baseline:
        _record_baseline(machine)


def _ready_for_freeze(machine: P2RunStateMachine, *, tie: bool = False) -> tuple[str, ...]:
    _finish_generation(machine)
    _train_base(machine, tie=tie)
    machine.finish_train()
    return machine.build_shortlist(incumbent_score=0.5 if not tie else 0.75)


def _freeze(machine: P2RunStateMachine) -> dict[str, object]:
    return machine.freeze_shortlist(
        compiler_sha256=COMPILER_HASH,
        config_sha256=CONFIG_HASH,
        retriever_sha256=RETRIEVER_HASH,
        evaluator_sha256=EVALUATOR_HASH,
    )


def test_train_failure_stops_before_shortlist() -> None:
    machine = _machine()
    _finish_generation(machine)
    _train_base(machine, failure=True, baseline=False)
    with pytest.raises(P2StateError, match="train failure"):
        machine.finish_train()
    assert machine.state == "blocked"


def test_baseline_reproduction_is_hash_bound_immutable_and_fail_closed() -> None:
    machine = _machine()
    _finish_generation(machine)
    _train_base(machine, baseline=False)
    receipt = _record_baseline(machine)
    assert validate_p2_artifact(receipt, repository_root=ROOT)["status"] == "passed"
    with pytest.raises(P2StateError, match="immutable"):
        _record_baseline(machine)

    failed = _machine()
    _finish_generation(failed)
    _train_base(failed, baseline=False)
    with pytest.raises(P2StateError, match="baseline reproduction failure"):
        _record_baseline(failed, result_value=0.8)
    assert failed.state == "blocked"


def test_ties_are_rejected_and_never_enter_shortlist() -> None:
    machine = _machine()
    shortlist = _ready_for_freeze(machine, tie=True)
    assert "control-0" not in shortlist
    assert "control-1" not in shortlist


def test_freeze_is_immutable_and_selection_is_one_shot() -> None:
    machine = _machine()
    assert _ready_for_freeze(machine) == ("control-0", "control-1", "patent-0", "patent-1")
    receipt = _freeze(machine)
    assert receipt["budget_profile_sha256"] == load_profile(ROOT).sha256
    assert receipt["selection_exposure_count"] == 0
    with pytest.raises(P2StateError, match="candidate_generation"):
        machine.register_candidate(Candidate("late", "adaptive_autoindex", 5, "4" * 64))
    assert machine.open_selection() == ("control-0", "control-1", "patent-0", "patent-1")
    with pytest.raises(P2StateError, match="frozen"):
        machine.open_selection()

    for index, candidate_id in enumerate(reversed(machine.shortlist_ids)):
        machine.record_selection(candidate_id, metric={key: value for key, value in _metric(candidate_id, 0.5 + index * 0.01, split="selection").items() if key != "candidate_id"})
    machine.close()
    selection = machine.build_selection_receipt()
    assert [item["candidate_id"] for item in selection["metrics"]] == list(machine.shortlist_ids)
    assert validate_p2_artifact(selection, repository_root=ROOT)["selection_exposure_count"] == 1
    with pytest.raises(P2StateError, match="selection_exposed"):
        machine.record_selection("control-0", metric={})


def test_selection_rejects_duplicate_unknown_partial_and_unknown_metric_fields() -> None:
    machine = _machine()
    _ready_for_freeze(machine)
    _freeze(machine)
    machine.open_selection()
    metric = {key: value for key, value in _metric("control-0", 0.5, split="selection").items() if key != "candidate_id"}
    machine.record_selection("control-0", metric=metric)
    with pytest.raises(P2StateError, match="immutable and unique"):
        machine.record_selection("control-0", metric=metric)
    with pytest.raises(P2StateError, match="frozen shortlist"):
        machine.record_selection("unknown", metric=metric)
    with pytest.raises(P2StateError, match="(?i)additional properties"):
        machine.record_selection("control-1", metric={**metric, "unexpected": 1})
    with pytest.raises(P2StateError, match="every finalist"):
        machine.close()
    with pytest.raises(P2StateError, match="closed"):
        machine.build_selection_receipt()


def test_freeze_rejects_malformed_or_mismatched_component_hashes() -> None:
    machine = _machine()
    _ready_for_freeze(machine)
    with pytest.raises(P2StateError, match="compiler hash"):
        machine.freeze_shortlist(
            compiler_sha256="not-a-hash",
            config_sha256=CONFIG_HASH,
            retriever_sha256=RETRIEVER_HASH,
            evaluator_sha256=EVALUATOR_HASH,
        )
    with pytest.raises(P2StateError, match="config_sha256"):
        machine.freeze_shortlist(
            compiler_sha256=COMPILER_HASH,
            config_sha256="0" * 64,
            retriever_sha256=RETRIEVER_HASH,
            evaluator_sha256=EVALUATOR_HASH,
        )


def test_adaptive_iterations_are_consecutive_complete_immutable_and_derived() -> None:
    machine = _machine()
    _register_base(machine)
    with pytest.raises(P2StateError, match="consecutive"):
        machine.register_candidate(Candidate("adaptive-2-0", "adaptive_autoindex", 2, "3" * 64))

    for index in range(3):
        candidate_id = f"adaptive-1-{index}"
        machine.register_candidate(Candidate(candidate_id, "adaptive_autoindex", 1, "3" * 64))
        machine.record_train(candidate_id, score=0.5 + index * 0.01)
    with pytest.raises(P2StateError, match="exactly four"):
        machine.record_iteration(1)

    machine.register_candidate(Candidate("adaptive-1-3", "adaptive_autoindex", 1, "3" * 64))
    machine.record_train("adaptive-1-3", score=0.9)
    assert machine.record_iteration(1) is False
    assert machine.iteration_records[1]["best_score"] == 0.9
    with pytest.raises(P2StateError, match="immutable"):
        machine.register_candidate(Candidate("adaptive-1-late", "adaptive_autoindex", 1, "3" * 64))


def test_early_stop_requires_four_iterations_and_patience_evidence() -> None:
    machine = _machine()
    _register_base(machine)
    assert _complete_iteration(machine, 1, 0.5) is False
    assert _complete_iteration(machine, 2, 0.6) is False
    assert _complete_iteration(machine, 3, 0.6) is False
    assert _complete_iteration(machine, 4, 0.6) is True

    improving = _machine()
    _register_base(improving)
    for iteration, score in enumerate((0.5, 0.6, 0.7, 0.8), start=1):
        assert _complete_iteration(improving, iteration, score) is False
    with pytest.raises(P2StateError, match="stop early"):
        improving.finish_generation()
