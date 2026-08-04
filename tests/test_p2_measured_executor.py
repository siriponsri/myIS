from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from myis_research.kernel.canonical import canonical_sha256, file_sha256
from myis_research.p2.base_candidates import (
    build_base_candidate_set,
)
from tests._p2_v2_fixture import PRIOR_URI, prepare_v2_repository
from myis_research.p2.measured_contracts import (
    load_measured_request,
    scientific_payload_sha256,
    validate_measured_artifact,
)
from myis_research.p2.measured_executor import run_measured_execution
from myis_research.p2.measured_executor import (
    _measure_selection_with_retry,
    _measure_with_retry,
)
from myis_research.p2.measured_contracts import load_profile_uri
from myis_research.p2.contracts import P2ContractError
from myis_research.p2.measured_state import (
    MeasuredRunJournal,
    MeasuredStateError,
    validate_resume_state,
)


ROOT = Path(__file__).resolve().parents[1]


def _prepare_repository(tmp_path: Path) -> tuple[Path, Path, dict]:
    repository = tmp_path / "repository"
    request_path, prior = prepare_v2_repository(
        repository,
        request_id="p2-measured-executor-test",
    )
    request = json.loads(request_path.read_text(encoding="utf-8"))
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(request, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return repository, request_path, prior


def _adaptive_batch(feedback: dict, request: dict, repository_root: Path) -> dict:
    iteration = int(feedback["iteration"])
    base = request["_resolved"]["base_candidate_set"]
    sources = (
        base["preregistered_candidates"][0],
        base["preregistered_candidates"][1],
        base["preregistered_candidates"][4],
        base["preregistered_candidates"][7],
    )
    roles = ("exploit", "matched_ablation", "orthogonal", "diversity")
    axes = ("source_fields", "source_fields", "unitization", "view_composition")
    candidate_ids = [
        f"p2-r1-r02-i{iteration:02d}-c{index:02d}" for index in range(1, 5)
    ]
    candidates = []
    for index, (source, role, axis) in enumerate(
        zip(sources, roles, axes, strict=True), start=1
    ):
        spec = deepcopy(source["scope_spec"])
        spec["spec_id"] = f"spec-r02-i{iteration:02d}-c{index:02d}-v01"
        spec["hypothesis_id"] = f"hyp-i{iteration:02d}-{index:03d}"
        candidates.append(
            {
                "candidate_id": candidate_ids[index - 1],
                "parent_candidate_id": source["candidate_id"],
                "hypothesis_id": spec["hypothesis_id"],
                "hypothesis": source["hypothesis"],
                "role": role,
                "declared_axis": axis,
                "matched_ablation_id": (
                    candidate_ids[1]
                    if index == 1
                    else candidate_ids[0] if index == 2 else None
                ),
                "scope_spec": spec,
                "spec_sha256": canonical_sha256(spec),
                "scientific_payload_sha256": scientific_payload_sha256(spec),
                "axis_values": deepcopy(source["axis_values"]),
            }
        )
    batch = {
        "schema_version": "myis.p2-scope-candidate-batch.v1",
        "batch_id": f"p2-r1-r02-i{iteration:02d}",
        "request_id": request["request_id"],
        "campaign_revision": request["campaign_revision"],
        "iteration": iteration,
        "feedback_sha256": feedback["feedback_sha256"],
        "proposer_invocation_sha256": "f" * 64,
        "status": "frozen_before_measurement",
        "candidates": candidates,
    }
    batch["batch_sha256"] = canonical_sha256(batch)
    return validate_measured_artifact(batch, repository_root)


def test_checkpoint_engine_completes_32_candidate_lifecycle(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repository, request_path, prior = _prepare_repository(tmp_path)
    request = load_measured_request(request_path, repository)
    request_payload = {key: value for key, value in request.items() if key != "_resolved"}
    prior_metric = prior["metrics"][8]

    def fake_validate_owner_inputs(**_kwargs):
        return {
            "dataset_lineage_sha256": prior["lineage_hashes"]["dataset_sha256"],
            "scope_hashes": request_payload["scope_hashes"],
        }

    def fake_baseline_expectation(**_kwargs):
        return {
            "prior_artifact_uri": PRIOR_URI.as_posix(),
            "prior_artifact_sha256": file_sha256(repository / PRIOR_URI),
            "metric_locator": {"metrics_index": 8},
            "expected_metric": {
                "schema_version": "myis.p2-train-metric.v1",
                "candidate_id": "p2-control-r0-window-maxp",
                "arm": "R0-W",
                "metric_name": prior_metric["name"],
                "data_role": prior_metric["split"],
                "scope": prior_metric["scope"],
                "evidence_role": prior_metric["evidence_role"],
                "direction": "higher_is_better",
                "value": prior_metric["value"],
                "n": prior_metric["n"],
                "denominator": prior_metric["denominator"],
                "dataset_lineage_sha256": prior["lineage_hashes"]["dataset_sha256"],
                "config_sha256": request_payload["scope_hashes"]["config_sha256"],
                "retriever_sha256": request_payload["scope_hashes"]["retriever_sha256"],
                "evaluator_sha256": request_payload["scope_hashes"]["evaluator_sha256"],
            },
            "tolerance": 0.0,
        }

    monkeypatch.setattr(
        "myis_research.p2.measured_executor.validate_owner_inputs",
        fake_validate_owner_inputs,
    )
    monkeypatch.setattr(
        "myis_research.p2.measured_executor.baseline_expectation",
        fake_baseline_expectation,
    )
    train_values: dict[str, float] = {}

    def fake_candidate_executor(request_row, candidate, data_role, state):
        candidate_id = candidate["candidate_id"]
        if data_role == "train":
            if candidate_id == "p2-control-r0-window-maxp":
                value = float(prior_metric["value"])
            else:
                value = round(float(prior_metric["value"]) + 0.001 * (len(train_values) + 1), 12)
            train_values[candidate_id] = value
            metric = {
                "schema_version": "myis.p2-train-metric.v1",
                "candidate_id": candidate_id,
                "arm": candidate["arm"],
                "metric_name": "recall_at_100",
                "data_role": "train",
                "scope": "OUT",
                "evidence_role": "primary",
                "direction": "higher_is_better",
                "value": value,
                "n": prior_metric["n"],
                "denominator": prior_metric["denominator"],
                "dataset_lineage_sha256": prior["lineage_hashes"]["dataset_sha256"],
                "config_sha256": request_row["scope_hashes"]["config_sha256"],
                "retriever_sha256": request_row["scope_hashes"]["retriever_sha256"],
                "evaluator_sha256": request_row["scope_hashes"]["evaluator_sha256"],
            }
        else:
            metric = {
                "candidate_id": candidate_id,
                "name": "recall_at_100",
                "value": train_values[candidate_id],
                "n": 10,
                "scope": "OUT",
                "split": "selection",
                "direction": "maximize",
                "denominator": "macro_mean_per_query_relevant_families",
                "evidence_role": "primary",
            }
        result = {
            "schema_version": "myis.p2-candidate-result.v1",
            "request_id": request_row["request_id"],
            "candidate_id": candidate_id,
            "arm": candidate["arm"],
            "candidate_class": candidate["candidate_class"],
            "iteration": int(candidate.get("iteration", 0)),
            "data_role": data_role,
            "spec_sha256": candidate["spec_sha256"],
            "index_sha256": canonical_sha256({"index": candidate_id}),
            "index_lineage_sha256": canonical_sha256({"lineage": candidate_id}),
            "index_build_count": 1 if data_role == "train" else 0,
            "deterministic_replay": True,
            "runtime_seconds": 1.0,
            "metric": metric,
        }
        result["result_sha256"] = canonical_sha256(result)
        return validate_measured_artifact(result, repository), state

    feedback_axes: list[list[str]] = []

    def fake_proposer(**kwargs):
        feedback_axes.append(list(kwargs["feedback"]["remaining_axes"]))
        return (
            _adaptive_batch(
                kwargs["feedback"], kwargs["request"], kwargs["repository_root"]
            ),
            {},
        )

    run_root = tmp_path / "owner-run"
    owner_store = tmp_path / "owner-store"
    owner_store.mkdir()
    journal = MeasuredRunJournal(run_root)
    state = journal.initialize(
        run_id=request_payload["request_id"],
        request=request,
        owner_paths={"run_root": str(run_root)},
    )
    completed = run_measured_execution(
        request=request,
        request_path=request_path,
        repository_root=repository,
        run_root=run_root,
        cache_root=tmp_path / "unused-cache",
        owner_store=owner_store,
        journal=journal,
        state=state,
        heartbeat=lambda: None,
        stop_requested=lambda: False,
        candidate_executor=fake_candidate_executor,
        proposer=fake_proposer,
    )
    assert completed["stage"] == "measured_complete"
    assert len(completed["accepted_result_ids"]) == 32
    assert len(completed["shortlist_ids"]) == 4
    assert completed["selection_exposure_count"] == 1
    assert len(feedback_axes) == 5
    assert "source_fields" in feedback_axes[0]
    for remaining in feedback_axes[1:]:
        assert "source_fields" not in remaining
        assert "unitization" not in remaining
        assert "view_composition" not in remaining
    assert (run_root / "artifacts" / "package.json").is_file()
    assert journal.verify()["status"] == "passed"


def test_candidate_timeout_quarantines_partial_index_and_retries_once(
    tmp_path: Path,
) -> None:
    journal = MeasuredRunJournal(tmp_path / "run")
    request = {
        "request_id": "p2-retry-test",
        "campaign_revision": "scope-autoindex-v1-p2-r1-primary-v2",
        "budget_profile_id": "p2-r1-primary-v2",
        "budget_profile_sha256": "b" * 64,
        "execution_source_commit": "c" * 40,
        "execution_source_tree": "d" * 40,
    }
    state = journal.initialize(
        run_id="p2-retry-test",
        request=request,
        owner_paths={"run_root": str(tmp_path / "run")},
    )
    candidate = build_base_candidate_set(ROOT, committed_hashes=False)[
        "preregistered_candidates"
    ][0]
    state["candidates"] = {
        candidate["candidate_id"]: {
            "candidate_id": candidate["candidate_id"],
            "status": "registered",
        }
    }
    partial = journal.run_root / "indexes" / candidate["candidate_id"]
    partial.mkdir(parents=True)
    (partial / "index.sqlite.tmp").write_bytes(b"partial")
    attempts = 0

    def executor(request_row, candidate_row, data_role, current_state):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            error = TimeoutError("synthetic timeout")
            error.elapsed_seconds = 2.0  # type: ignore[attr-defined]
            raise error
        metric = {
            "schema_version": "myis.p2-train-metric.v1",
            "candidate_id": candidate_row["candidate_id"],
            "arm": candidate_row["arm"],
            "metric_name": "recall_at_100",
            "data_role": "train",
            "scope": "OUT",
            "evidence_role": "primary",
            "direction": "higher_is_better",
            "value": 0.1,
            "n": 1,
            "denominator": "macro_mean_per_query_relevant_families",
            "dataset_lineage_sha256": "a" * 64,
            "config_sha256": "b" * 64,
            "retriever_sha256": "c" * 64,
            "evaluator_sha256": "d" * 64,
        }
        result = {
            "schema_version": "myis.p2-candidate-result.v1",
            "request_id": request_row["request_id"],
            "candidate_id": candidate_row["candidate_id"],
            "arm": candidate_row["arm"],
            "candidate_class": candidate_row["candidate_class"],
            "iteration": 0,
            "data_role": data_role,
            "spec_sha256": candidate_row["spec_sha256"],
            "index_sha256": "e" * 64,
            "index_lineage_sha256": "f" * 64,
            "index_build_count": 1,
            "deterministic_replay": True,
            "runtime_seconds": 1.0,
            "metric": metric,
        }
        result["result_sha256"] = canonical_sha256(result)
        return result, current_state

    profile, _ = load_profile_uri(ROOT, "control/budgets/p2-r1-primary-v2.yaml")
    completed = _measure_with_retry(
        request={"request_id": request["request_id"]},
        candidate=candidate,
        data_role="train",
        state=state,
        profile=profile,
        journal=journal,
        executor=executor,
        repository_root=ROOT,
    )
    assert attempts == 2
    assert completed["candidate_attempts"][candidate["candidate_id"]] == 2
    assert candidate["candidate_id"] in completed["accepted_result_ids"]
    assert len(completed["quarantined_partial_indexes"]) == 1
    assert not partial.exists()


def test_scientific_candidate_failure_is_recorded_once_and_cannot_resume(
    tmp_path: Path,
) -> None:
    journal = MeasuredRunJournal(tmp_path / "run")
    request = {
        "request_id": "p2-scientific-failure-test",
        "campaign_revision": "scope-autoindex-v1-p2-r1-primary-v2",
        "budget_profile_id": "p2-r1-primary-v2",
        "budget_profile_sha256": "b" * 64,
        "execution_source_commit": "c" * 40,
        "execution_source_tree": "d" * 40,
    }
    state = journal.initialize(
        run_id=request["request_id"],
        request=request,
        owner_paths={"run_root": str(tmp_path / "run")},
    )
    candidate = build_base_candidate_set(ROOT, committed_hashes=False)[
        "preregistered_candidates"
    ][0]
    attempts = 0

    def executor(_request, _candidate, _data_role, _state):
        nonlocal attempts
        attempts += 1
        raise P2ContractError("synthetic scientific validation failure")

    profile, _ = load_profile_uri(ROOT, "control/budgets/p2-r1-primary-v2.yaml")
    with pytest.raises(P2ContractError, match="scientific validation failure"):
        _measure_with_retry(
            request={"request_id": request["request_id"]},
            candidate=candidate,
            data_role="train",
            state=state,
            profile=profile,
            journal=journal,
            executor=executor,
            repository_root=ROOT,
        )

    blocked = journal.load()
    assert attempts == 1
    assert blocked["stage"] == "blocked_scientific"
    assert blocked["failure"]["category"] == "scientific_validation"
    assert blocked["candidates"][candidate["candidate_id"]]["status"] == "failed"
    assert not (
        journal.artifact_root / f"candidate-{candidate['candidate_id']}-result.json"
    ).exists()
    with pytest.raises(MeasuredStateError, match="resume is forbidden"):
        validate_resume_state(journal, request=request)


def test_selection_infrastructure_failure_retries_once_and_succeeds(
    tmp_path: Path,
) -> None:
    journal = MeasuredRunJournal(tmp_path / "run")
    request = {
        "request_id": "p2-selection-retry-test",
        "campaign_revision": "scope-autoindex-v1-p2-r1-primary-v2",
        "budget_profile_id": "p2-r1-primary-v2",
        "budget_profile_sha256": "b" * 64,
        "execution_source_commit": "c" * 40,
        "execution_source_tree": "d" * 40,
    }
    state = journal.initialize(
        run_id=request["request_id"],
        request=request,
        owner_paths={"run_root": str(tmp_path / "run")},
    )
    candidate = build_base_candidate_set(ROOT, committed_hashes=False)[
        "preregistered_candidates"
    ][0]
    attempts = 0

    def executor(request_row, candidate_row, data_role, current_state):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            error = OSError("synthetic selection infrastructure failure")
            error.elapsed_seconds = 2.0  # type: ignore[attr-defined]
            raise error
        result = {
            "schema_version": "myis.p2-candidate-result.v1",
            "request_id": request_row["request_id"],
            "candidate_id": candidate_row["candidate_id"],
            "arm": candidate_row["arm"],
            "candidate_class": candidate_row["candidate_class"],
            "iteration": 0,
            "data_role": data_role,
            "spec_sha256": candidate_row["spec_sha256"],
            "index_sha256": "e" * 64,
            "index_lineage_sha256": "f" * 64,
            "index_build_count": 0,
            "deterministic_replay": True,
            "runtime_seconds": 1.0,
            "metric": {
                "candidate_id": candidate_row["candidate_id"],
                "name": "recall_at_100",
                "value": 0.1,
                "n": 1,
                "scope": "OUT",
                "split": "selection",
                "direction": "maximize",
                "denominator": "macro_mean_per_query_relevant_families",
                "evidence_role": "primary",
            },
        }
        result["result_sha256"] = canonical_sha256(result)
        return result, current_state

    profile, _ = load_profile_uri(ROOT, "control/budgets/p2-r1-primary-v2.yaml")
    completed = _measure_selection_with_retry(
        request={"request_id": request["request_id"]},
        candidate=candidate,
        state=state,
        profile=profile,
        journal=journal,
        executor=executor,
        repository_root=ROOT,
        result_name="selection-result.json",
    )
    assert attempts == 2
    assert completed["stage"] == "selection_candidate_completed"
    assert completed["candidate_attempts"][f"selection:{candidate['candidate_id']}"] == 2
    assert completed["failure"] is None
    assert (journal.artifact_root / "selection-result.json").is_file()


def test_selection_scientific_failure_is_terminal(tmp_path: Path) -> None:
    journal = MeasuredRunJournal(tmp_path / "run")
    request = {
        "request_id": "p2-selection-scientific-test",
        "campaign_revision": "scope-autoindex-v1-p2-r1-primary-v2",
        "budget_profile_id": "p2-r1-primary-v2",
        "budget_profile_sha256": "b" * 64,
        "execution_source_commit": "c" * 40,
        "execution_source_tree": "d" * 40,
    }
    state = journal.initialize(
        run_id=request["request_id"],
        request=request,
        owner_paths={"run_root": str(tmp_path / "run")},
    )
    candidate = build_base_candidate_set(ROOT, committed_hashes=False)[
        "preregistered_candidates"
    ][0]
    attempts = 0

    def executor(_request, _candidate, _data_role, _state):
        nonlocal attempts
        attempts += 1
        raise P2ContractError("synthetic selection scientific failure")

    profile, _ = load_profile_uri(ROOT, "control/budgets/p2-r1-primary-v2.yaml")
    with pytest.raises(P2ContractError, match="selection scientific failure"):
        _measure_selection_with_retry(
            request={"request_id": request["request_id"]},
            candidate=candidate,
            state=state,
            profile=profile,
            journal=journal,
            executor=executor,
            repository_root=ROOT,
            result_name="selection-result.json",
        )
    blocked = journal.load()
    assert attempts == 1
    assert blocked["stage"] == "blocked_scientific"
    assert blocked["failure"]["data_role"] == "selection"
    assert blocked["failure"]["category"] == "scientific_validation"


def test_candidate_result_cannot_exceed_index_build_budget(tmp_path: Path) -> None:
    journal = MeasuredRunJournal(tmp_path / "run")
    request = {
        "request_id": "p2-index-budget-test",
        "campaign_revision": "scope-autoindex-v1-p2-r1-primary-v2",
        "budget_profile_id": "p2-r1-primary-v2",
        "budget_profile_sha256": "b" * 64,
        "execution_source_commit": "c" * 40,
        "execution_source_tree": "d" * 40,
    }
    state = journal.initialize(
        run_id=request["request_id"],
        request=request,
        owner_paths={"run_root": str(tmp_path / "run")},
    )
    candidate = build_base_candidate_set(ROOT, committed_hashes=False)[
        "preregistered_candidates"
    ][0]
    profile, _ = load_profile_uri(ROOT, "control/budgets/p2-r1-primary-v2.yaml")
    state["total_index_builds"] = profile["limits"]["max_index_builds"]

    def executor(request_row, candidate_row, data_role, current_state):
        metric = {
            "schema_version": "myis.p2-train-metric.v1",
            "candidate_id": candidate_row["candidate_id"],
            "arm": candidate_row["arm"],
            "metric_name": "recall_at_100",
            "data_role": "train",
            "scope": "OUT",
            "evidence_role": "primary",
            "direction": "higher_is_better",
            "value": 0.1,
            "n": 1,
            "denominator": "macro_mean_per_query_relevant_families",
            "dataset_lineage_sha256": "a" * 64,
            "config_sha256": "b" * 64,
            "retriever_sha256": "c" * 64,
            "evaluator_sha256": "d" * 64,
        }
        result = {
            "schema_version": "myis.p2-candidate-result.v1",
            "request_id": request_row["request_id"],
            "candidate_id": candidate_row["candidate_id"],
            "arm": candidate_row["arm"],
            "candidate_class": candidate_row["candidate_class"],
            "iteration": 0,
            "data_role": data_role,
            "spec_sha256": candidate_row["spec_sha256"],
            "index_sha256": "e" * 64,
            "index_lineage_sha256": "f" * 64,
            "index_build_count": 1,
            "deterministic_replay": True,
            "runtime_seconds": 1.0,
            "metric": metric,
        }
        result["result_sha256"] = canonical_sha256(result)
        return result, current_state

    with pytest.raises(MeasuredStateError, match="index build budget"):
        _measure_with_retry(
            request={"request_id": request["request_id"]},
            candidate=candidate,
            data_role="train",
            state=state,
            profile=profile,
            journal=journal,
            executor=executor,
            repository_root=ROOT,
        )

    blocked = journal.load()
    assert blocked["stage"] == "blocked_budget"
    assert blocked["total_index_builds"] == profile["limits"]["max_index_builds"]
    assert blocked["accepted_result_ids"] == []
    assert not (
        journal.artifact_root / f"candidate-{candidate['candidate_id']}-result.json"
    ).exists()
