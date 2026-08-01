from __future__ import annotations

import pytest
from pathlib import Path

from myis_research.p2.state import Candidate, P2RunStateMachine, P2StateError
from myis_research.p2.contracts import load_profile


def _machine() -> P2RunStateMachine:
    return P2RunStateMachine(request_id="p2-state-test", profile=load_profile(Path(__file__).resolve().parents[1]).payload)


def _generate(machine: P2RunStateMachine) -> None:
    for index in range(4):
        machine.register_candidate(Candidate(f"control-{index}", "frozen_control", 0, "a" * 64))
    for index in range(8):
        machine.register_candidate(Candidate(f"patent-{index}", "preregistered_patent", 0, "b" * 64))
    machine.register_candidate(Candidate("adaptive-1-0", "adaptive_autoindex", 1, "c" * 64))
    machine.finish_generation()


def _train(machine: P2RunStateMachine, *, tie: bool = False, failure: bool = False) -> None:
    for index, candidate_id in enumerate(machine.candidates):
        if failure and index == 0:
            machine.record_train(candidate_id, score=None, status="failed", failure_reason="fixture failure")
        else:
            score = 0.8 if index == 0 else 0.8 if tie and index == 1 else 0.7 if index == 1 else 0.1
            machine.record_train(candidate_id, score=score)
    machine.record_baseline_reproduction(passed=True)


def test_train_failure_stops_before_shortlist() -> None:
    machine = _machine()
    _generate(machine)
    _train(machine, failure=True)
    with pytest.raises(P2StateError, match="train failure"):
        machine.finish_train()
    assert machine.state == "blocked"


def test_baseline_reproduction_failure_stops_before_shortlist() -> None:
    machine = _machine()
    _generate(machine)
    for candidate_id in machine.candidates:
        machine.record_train(candidate_id, score=0.1)
    with pytest.raises(P2StateError, match="baseline reproduction failure"):
        machine.record_baseline_reproduction(passed=False)
    assert machine.state == "blocked"


def test_ties_are_rejected_and_never_enter_shortlist() -> None:
    machine = _machine()
    _generate(machine)
    _train(machine, tie=True)
    machine.finish_train()
    assert machine.build_shortlist(incumbent_score=0.5) == ()


def test_freeze_is_immutable_and_selection_is_one_shot() -> None:
    machine = _machine()
    _generate(machine)
    _train(machine)
    machine.finish_train()
    assert machine.build_shortlist(incumbent_score=0.5) == ("control-0", "control-1")
    receipt = machine.freeze_shortlist(
        budget_profile_sha256="d" * 64,
        compiler_sha256="e" * 64,
        config_sha256="f" * 64,
        retriever_sha256="1" * 64,
        evaluator_sha256="2" * 64,
    )
    assert receipt["selection_exposure_count"] == 0
    with pytest.raises(P2StateError, match="candidate"):
        machine.register_candidate(Candidate("late", "adaptive_autoindex", 2, "3" * 64))
    with pytest.raises(P2StateError, match="candidate_generation"):
        machine.record_iteration(1, best_score=0.9)
    assert machine.open_selection() == ("control-0", "control-1")
    with pytest.raises(P2StateError, match="frozen|exposure"):
        machine.open_selection()
    machine.record_selection("control-0", metric={"name": "recall_at_100", "value": 0.5})
    selection = machine.build_selection_receipt()
    assert selection["selection_exposure_count"] == 1


def test_freeze_rejects_malformed_component_hashes() -> None:
    machine = _machine()
    _generate(machine)
    _train(machine)
    machine.finish_train()
    machine.build_shortlist(incumbent_score=0.5)
    with pytest.raises(P2StateError, match="compiler hash"):
        machine.freeze_shortlist(
            budget_profile_sha256="d" * 64,
            compiler_sha256="not-a-hash",
            config_sha256="f" * 64,
            retriever_sha256="1" * 64,
            evaluator_sha256="2" * 64,
        )


def test_early_stop_requires_four_iterations_and_two_no_improvements() -> None:
    machine = _machine()
    assert machine.record_iteration(1, best_score=0.5) is False
    assert machine.record_iteration(2, best_score=0.6) is False
    assert machine.record_iteration(3, best_score=0.6) is False
    assert machine.record_iteration(4, best_score=0.6) is True
