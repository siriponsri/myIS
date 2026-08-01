from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from myis_research.kernel.canonical import file_sha256
from myis_research.p2 import (
    Candidate,
    P2RunStateMachine,
    P2StateError,
    load_profile,
    validate_p2_artifact,
)


ROOT = Path(__file__).resolve().parents[1]
PRIOR_URI = "campaigns/scope-autoindex-v1/evidence/dapfam-p1-fulltext-c058a3aa7357c782.receipt.json"
DATASET_HASH = "3dbb55b0d9f98d2e27665ad87fb6711f1e43d9466fcf7a96eea917df753adaf6"
COMPILER_HASH = "c" * 64
CONFIG_HASH = "d" * 64
RETRIEVER_HASH = "e" * 64
EVALUATOR_HASH = "6dd3b1d203304c3e8ef9e1aa049b82ae99ce60c1cd3af78cf99f76874db6346d"
BASELINE_VALUE = 0.085847360337


def _machine() -> P2RunStateMachine:
    return P2RunStateMachine(request_id="p2-state-test", profile=load_profile(ROOT))


def _train_metric(candidate_id: str, value: float, *, arm: str = "R1") -> dict[str, object]:
    return {
        "schema_version": "myis.p2-train-metric.v1",
        "candidate_id": candidate_id,
        "arm": arm,
        "metric_name": "recall_at_100",
        "data_role": "train",
        "scope": "OUT",
        "evidence_role": "primary",
        "direction": "higher_is_better",
        "value": value,
        "n": 179,
        "denominator": "macro_mean_per_query_relevant_families",
        "dataset_lineage_sha256": DATASET_HASH,
        "config_sha256": CONFIG_HASH,
        "retriever_sha256": RETRIEVER_HASH,
        "evaluator_sha256": EVALUATOR_HASH,
    }


def _selection_metric(candidate_id: str, value: float) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "name": "recall_at_100",
        "value": value,
        "n": 16,
        "scope": "OUT",
        "split": "selection",
        "direction": "maximize",
        "denominator": "macro_mean_per_query_relevant_families",
        "evidence_role": "primary",
    }


def _register_base(machine: P2RunStateMachine) -> None:
    for index, arm in enumerate(("R0-W", "R0", "R1", "R1")):
        machine.register_candidate(Candidate(f"control-{index}", arm, "frozen_control", 0, "1" * 64))
    for index in range(8):
        machine.register_candidate(Candidate(f"patent-{index}", "R1", "preregistered_patent", 0, "2" * 64))


def _commit_baseline(machine: P2RunStateMachine) -> dict[str, object]:
    return machine.commit_baseline_expectation(
        baseline_candidate_id="control-0",
        baseline_arm="R0-W",
        prior_artifact_uri=PRIOR_URI,
        prior_artifact_sha256=file_sha256(ROOT / PRIOR_URI),
        metric_locator={"metrics_index": 8},
        expected_metric=_train_metric("control-0", BASELINE_VALUE, arm="R0-W"),
        tolerance=0.001,
    )


def _complete_iteration(machine: P2RunStateMachine, iteration: int, best_value: float) -> bool:
    for index in range(4):
        candidate_id = f"adaptive-{iteration}-{index}"
        machine.register_candidate(Candidate(candidate_id, "R1", "adaptive_autoindex", iteration, "3" * 64))
        machine.record_train(candidate_id, metric=_train_metric(candidate_id, best_value - index * 0.01))
    return machine.record_iteration(iteration)


def _finish_generation(machine: P2RunStateMachine, scores: tuple[float, ...] = (0.6, 0.7, 0.7, 0.7)) -> None:
    _register_base(machine)
    _commit_baseline(machine)
    for iteration, score in enumerate(scores, start=1):
        _complete_iteration(machine, iteration, score)
    machine.finish_generation()


def _record_baseline(machine: P2RunStateMachine, *, result_value: float = BASELINE_VALUE) -> dict[str, object]:
    return machine.record_baseline_reproduction(
        result=_train_metric("control-0", result_value, arm="R0-W"),
    )


def _train_base(
    machine: P2RunStateMachine,
    *,
    tie: bool = False,
    failure: bool = False,
    baseline: bool = True,
    baseline_value: float = BASELINE_VALUE,
) -> None:
    scores = [baseline_value, 0.8, 0.4, 0.3] if tie else [baseline_value, 0.9, 0.4, 0.3]
    scores.extend([0.8 if tie else 0.85, 0.75, 0.7, 0.65, 0.45, 0.35, 0.25, 0.15])
    for index, candidate_id in enumerate(
        candidate_id for candidate_id, row in machine.candidates.items() if row["iteration"] == 0
    ):
        if failure and index == 0:
            machine.record_train(candidate_id, metric=None, status="failed", failure_reason="fixture failure")
        else:
            arm = machine.candidates[candidate_id]["arm"]
            machine.record_train(candidate_id, metric=_train_metric(candidate_id, scores[index], arm=arm))
    if baseline:
        _record_baseline(machine, result_value=baseline_value)


def _ready_for_freeze(machine: P2RunStateMachine, *, tie: bool = False) -> tuple[str, ...]:
    _finish_generation(machine)
    _train_base(machine, tie=tie)
    machine.finish_train()
    return machine.build_shortlist()


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


def test_train_requires_commitment_and_commitment_precedes_outcomes() -> None:
    machine = _machine()
    _register_base(machine)
    machine.register_candidate(Candidate("adaptive-1-0", "R1", "adaptive_autoindex", 1, "3" * 64))
    with pytest.raises(P2StateError, match="baseline commitment"):
        machine.record_train("adaptive-1-0", metric=_train_metric("adaptive-1-0", 0.5))

    _commit_baseline(machine)
    machine.record_train("adaptive-1-0", metric=_train_metric("adaptive-1-0", 0.5))
    with pytest.raises(P2StateError, match="after train outcomes"):
        _commit_baseline(machine)


@pytest.mark.parametrize(
    ("change", "remove"),
    [
        (("metric_name", "precision_at_100"), None),
        (("data_role", "selection"), None),
        (("scope", "IN"), None),
        (("evidence_role", "secondary"), None),
        (("direction", "maximize"), None),
        (("denominator", "queries_with_positive_family_relevance"), None),
        (("n", 0), None),
        (None, "dataset_lineage_sha256"),
        (None, "config_sha256"),
        (None, "retriever_sha256"),
        (None, "evaluator_sha256"),
    ],
)
def test_train_metric_rejects_wrong_semantics_and_missing_lineage(
    change: tuple[str, object] | None,
    remove: str | None,
) -> None:
    machine = _machine()
    _register_base(machine)
    _commit_baseline(machine)
    machine.register_candidate(Candidate("adaptive-1-0", "R1", "adaptive_autoindex", 1, "3" * 64))
    metric = deepcopy(_train_metric("adaptive-1-0", 0.5))
    if change is not None:
        metric[change[0]] = change[1]
    if remove is not None:
        metric.pop(remove)
    with pytest.raises(P2StateError, match="JSON Schema"):
        machine.record_train("adaptive-1-0", metric=metric)


def test_train_metrics_require_one_shared_comparison_signature() -> None:
    machine = _machine()
    _register_base(machine)
    _commit_baseline(machine)
    for index in range(2):
        machine.register_candidate(Candidate(f"adaptive-1-{index}", "R1", "adaptive_autoindex", 1, "3" * 64))
    machine.record_train("adaptive-1-0", metric=_train_metric("adaptive-1-0", 0.5))
    inconsistent = _train_metric("adaptive-1-1", 0.6)
    inconsistent["n"] = 178
    with pytest.raises(P2StateError, match="share metric identity, n, denominator, and lineage"):
        machine.record_train("adaptive-1-1", metric=inconsistent)


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
    _train_base(failed, baseline=False, baseline_value=0.5)
    with pytest.raises(P2StateError, match="baseline reproduction failure"):
        _record_baseline(failed, result_value=0.5)
    assert failed.state == "blocked"


def test_baseline_reproduction_must_equal_the_ledger_metric() -> None:
    machine = _machine()
    _finish_generation(machine)
    _train_base(machine, baseline=False, baseline_value=BASELINE_VALUE + 0.0005)
    with pytest.raises(P2StateError, match="differs from the baseline candidate train metric"):
        _record_baseline(machine, result_value=BASELINE_VALUE)


def test_ties_are_rejected_and_never_enter_shortlist() -> None:
    machine = _machine()
    shortlist = _ready_for_freeze(machine, tie=True)
    assert "control-1" not in shortlist
    assert "patent-0" not in shortlist


def test_freeze_is_immutable_and_selection_is_one_shot() -> None:
    machine = _machine()
    assert _ready_for_freeze(machine) == ("control-1", "patent-0", "patent-1", "patent-3")
    receipt = _freeze(machine)
    assert receipt["budget_profile_sha256"] == load_profile(ROOT).sha256
    assert receipt["selection_exposure_count"] == 0
    with pytest.raises(P2StateError, match="candidate_generation"):
        machine.register_candidate(Candidate("late", "R1", "adaptive_autoindex", 5, "4" * 64))
    assert machine.open_selection() == ("control-1", "patent-0", "patent-1", "patent-3")
    with pytest.raises(P2StateError, match="frozen"):
        machine.open_selection()

    for index, candidate_id in enumerate(reversed(machine.shortlist_ids)):
        machine.record_selection(candidate_id, metric={key: value for key, value in _selection_metric(candidate_id, 0.5 + index * 0.01).items() if key != "candidate_id"})
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
    candidate_id = machine.shortlist_ids[0]
    metric = {key: value for key, value in _selection_metric(candidate_id, 0.5).items() if key != "candidate_id"}
    machine.record_selection(candidate_id, metric=metric)
    with pytest.raises(P2StateError, match="immutable and unique"):
        machine.record_selection(candidate_id, metric=metric)
    with pytest.raises(P2StateError, match="frozen shortlist"):
        machine.record_selection("unknown", metric=metric)
    with pytest.raises(P2StateError, match="(?i)additional properties"):
        machine.record_selection(machine.shortlist_ids[1], metric={**metric, "unexpected": 1})
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
    _commit_baseline(machine)
    with pytest.raises(P2StateError, match="consecutive"):
        machine.register_candidate(Candidate("adaptive-2-0", "R1", "adaptive_autoindex", 2, "3" * 64))

    for index in range(3):
        candidate_id = f"adaptive-1-{index}"
        machine.register_candidate(Candidate(candidate_id, "R1", "adaptive_autoindex", 1, "3" * 64))
        machine.record_train(candidate_id, metric=_train_metric(candidate_id, 0.5 + index * 0.01))
    with pytest.raises(P2StateError, match="exactly four"):
        machine.record_iteration(1)

    machine.register_candidate(Candidate("adaptive-1-3", "R1", "adaptive_autoindex", 1, "3" * 64))
    machine.record_train("adaptive-1-3", metric=_train_metric("adaptive-1-3", 0.9))
    assert machine.record_iteration(1) is False
    assert machine.iteration_records[1]["best_metric"]["value"] == 0.9
    with pytest.raises(P2StateError, match="immutable"):
        machine.register_candidate(Candidate("adaptive-1-late", "R1", "adaptive_autoindex", 1, "3" * 64))


def test_early_stop_requires_four_iterations_and_patience_evidence() -> None:
    machine = _machine()
    _register_base(machine)
    _commit_baseline(machine)
    assert _complete_iteration(machine, 1, 0.5) is False
    assert _complete_iteration(machine, 2, 0.6) is False
    assert _complete_iteration(machine, 3, 0.6) is False
    assert _complete_iteration(machine, 4, 0.6) is True

    improving = _machine()
    _register_base(improving)
    _commit_baseline(improving)
    for iteration, score in enumerate((0.5, 0.6, 0.7, 0.8), start=1):
        assert _complete_iteration(improving, iteration, score) is False
    with pytest.raises(P2StateError, match="stop early"):
        improving.finish_generation()
