"""Checkpointed P2 measured lifecycle driven by the durable journal."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Callable, Mapping

from ..kernel.canonical import canonical_sha256, file_sha256
from .contracts import (
    P2BudgetProfile,
    P2ContractError,
    build_request,
    validate_p2_artifact,
    validate_p2_package_bundle,
)
from .measured_adapter import baseline_expectation, validate_owner_inputs
from .measured_contracts import (
    can_admit_adaptive_batch,
    validate_measured_artifact,
)
from .measured_state import (
    MeasuredRunJournal,
    MeasuredStateError,
    compare_and_swap_selection_counter,
    process_creation_identity,
)
from .proposer import invoke_codex_proposer
from .runtime_environment import sanitized_runtime_environment
from .state import Candidate, P2RunStateMachine


CandidateExecutor = Callable[
    [Mapping[str, Any], Mapping[str, Any], str, dict[str, Any]],
    tuple[dict[str, Any], dict[str, Any]],
]
Proposer = Callable[..., tuple[dict[str, Any], dict[str, Any]]]


def run_measured_execution(
    *,
    request: Mapping[str, Any],
    request_path: Path,
    repository_root: Path,
    run_root: Path,
    cache_root: Path,
    owner_store: Path,
    journal: MeasuredRunJournal,
    state: Mapping[str, Any],
    heartbeat: Callable[[], None],
    stop_requested: Callable[[], bool],
    candidate_executor: CandidateExecutor | None = None,
    proposer: Proposer = invoke_codex_proposer,
    proposer_runner: Callable[..., Any] = subprocess.run,
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    owner_run_root = Path(run_root).resolve()
    request_payload = _request_payload(request)
    resolved = request["_resolved"]
    profile_payload = dict(resolved["profile"])
    current = deepcopy(dict(state))
    current = _transition(
        journal,
        current,
        stage="validating_owner_inputs",
        event_type="owner_inputs_validation_started",
        key="owner-inputs-validation-started",
    )
    validated_inputs = validate_owner_inputs(
        request=request_payload,
        repository_root=root,
        cache_root=cache_root,
    )
    current["dataset_lineage_sha256"] = validated_inputs[
        "dataset_lineage_sha256"
    ]
    current = _transition(
        journal,
        current,
        stage="owner_inputs_validated",
        event_type="owner_inputs_validated",
        key=f"owner-inputs-validated:{current['dataset_lineage_sha256']}",
    )
    definitions = _candidate_definitions(request, journal)
    machine = _replay_machine(request, journal, current, definitions)
    if not current.get("base_registered"):
        current["base_registered"] = True
        current["candidates"] = {
            candidate_id: {
                "candidate_id": candidate_id,
                "arm": definition["arm"],
                "class": definition["candidate_class"],
                "iteration": int(definition.get("iteration", 0)),
                "spec_sha256": definition["spec_sha256"],
                "status": "registered",
            }
            for candidate_id, definition in definitions.items()
            if int(definition.get("iteration", 0)) == 0
        }
        current = _transition(
            journal,
            current,
            stage="base_registered",
            event_type="base_candidates_registered",
            key=f"base-registered:{request_payload['base_candidate_set_sha256']}",
        )
    expectation = baseline_expectation(
        request=request_payload,
        repository_root=root,
    )
    if not current.get("baseline_commitment_sha256"):
        commitment = machine.commit_baseline_expectation(
            baseline_candidate_id="p2-control-r0-window-maxp",
            baseline_arm="R0-W",
            **expectation,
        )
        _ensure_artifact(journal, "baseline-commitment.json", commitment)
        current["baseline_commitment_sha256"] = commitment["commitment_sha256"]
        current = _transition(
            journal,
            current,
            stage="baseline_committed",
            event_type="baseline_commitment_written",
            key=f"baseline-commitment:{commitment['commitment_sha256']}",
        )
    machine = _replay_machine(request, journal, current, definitions)
    executor = candidate_executor or _subprocess_candidate_executor(
        request_path=request_path,
        repository_root=root,
        run_root=owner_run_root,
        cache_root=cache_root,
        journal=journal,
        heartbeat=heartbeat,
        timeout_seconds=int(profile_payload["runtime"]["per_candidate_timeout_seconds"]),
    )
    base_order = [
        "p2-control-r0-window-maxp",
        *[
            candidate_id
            for candidate_id, definition in definitions.items()
            if int(definition.get("iteration", 0)) == 0
            and candidate_id != "p2-control-r0-window-maxp"
        ],
    ]
    for candidate_id in base_order:
        if candidate_id in current.get("accepted_result_ids", []):
            continue
        current = _measure_with_retry(
            request=request_payload,
            candidate=definitions[candidate_id],
            data_role="train",
            state=current,
            profile=profile_payload,
            journal=journal,
            executor=executor,
            repository_root=root,
        )
        heartbeat()
        machine = _replay_machine(request, journal, current, definitions)
        if (
            candidate_id == "p2-control-r0-window-maxp"
            and not current.get("baseline_reproduction_sha256")
        ):
            baseline_result = _candidate_result(journal, candidate_id)["metric"]
            receipt = machine.record_baseline_reproduction(result=baseline_result)
            _ensure_artifact(
                journal, "baseline-reproduction-receipt.json", receipt
            )
            current["baseline_reproduction_sha256"] = receipt["receipt_sha256"]
            current = _transition(
                journal,
                current,
                stage="baseline_reproduced",
                event_type="baseline_reproduction_passed",
                key=f"baseline-reproduced:{receipt['receipt_sha256']}",
            )
        if stop_requested():
            return _stop_at_checkpoint(journal, current)
    max_iterations = int(profile_payload["limits"]["max_adaptive_iterations"])
    while len(current.get("completed_iterations", [])) < max_iterations:
        if stop_requested():
            return _stop_at_checkpoint(journal, current)
        machine = _replay_machine(request, journal, current, definitions)
        if machine.early_stop_eligible:
            current["stop_reason"] = "development_impact_gate"
            break
        if not can_admit_adaptive_batch(
            profile_payload,
            consumed_measurement_seconds=float(
                current.get("measurement_runtime_seconds", 0.0)
            ),
            candidate_count=len(current.get("accepted_result_ids", [])),
        ):
            current["stop_reason"] = "wall_clock_exhausted"
            break
        iteration = len(current.get("completed_iterations", [])) + 1
        batch_name = f"adaptive-batch-i{iteration:02d}.json"
        batch_path = journal.artifact_root / batch_name
        if batch_path.is_file():
            batch = _json_file(batch_path)
            validate_measured_artifact(batch, root)
        else:
            feedback = _build_feedback(
                request=request_payload,
                machine=machine,
                policy=resolved["adaptive_policy"],
                iteration=iteration,
                state=current,
                repository_root=root,
            )
            _ensure_artifact(
                journal, f"adaptive-feedback-i{iteration:02d}.json", feedback
            )
            batch, _ = proposer(
                feedback=feedback,
                request=request,
                proposer_contract=resolved["proposer_contract"],
                repository_root=root,
                run_root=owner_run_root,
                journal=journal,
                runner=proposer_runner,
            )
            _ensure_artifact(journal, batch_name, batch)
        if batch["batch_sha256"] not in current.get("adaptive_batches", []):
            current.setdefault("adaptive_batches", []).append(batch["batch_sha256"])
            for row in batch["candidates"]:
                definition = _adaptive_definition(row, iteration=iteration)
                definitions[definition["candidate_id"]] = definition
                current.setdefault("used_adaptive_axes", []).append(
                    str(definition["declared_axis"])
                )
                current.setdefault("candidates", {})[definition["candidate_id"]] = {
                    "candidate_id": definition["candidate_id"],
                    "arm": "R1",
                    "class": "adaptive_autoindex",
                    "iteration": iteration,
                    "spec_sha256": definition["spec_sha256"],
                    "status": "registered",
                }
                _ensure_artifact(
                    journal,
                    f"candidate-{definition['candidate_id']}-definition.json",
                    definition,
                )
            current = _transition(
                journal,
                current,
                stage="adaptive_batch_frozen",
                event_type="adaptive_batch_frozen",
                key=f"adaptive-batch:{batch['batch_sha256']}",
            )
        definitions = _candidate_definitions(request, journal)
        for row in batch["candidates"]:
            candidate_id = str(row["candidate_id"])
            if candidate_id in current.get("accepted_result_ids", []):
                continue
            current = _measure_with_retry(
                request=request_payload,
                candidate=definitions[candidate_id],
                data_role="train",
                state=current,
                profile=profile_payload,
                journal=journal,
                executor=executor,
                repository_root=root,
            )
            heartbeat()
            if stop_requested():
                return _stop_at_checkpoint(journal, current)
        machine = _replay_machine(request, journal, current, definitions)
        machine.record_iteration(iteration)
        current.setdefault("completed_iterations", []).append(iteration)
        current = _transition(
            journal,
            current,
            stage="adaptive_iteration_completed",
            event_type="adaptive_iteration_completed",
            key=f"adaptive-iteration:{iteration}",
        )
    machine = _replay_machine(request, journal, current, definitions)
    machine.finish_generation_with_reason(current.get("stop_reason"))
    current["generation_finished"] = True
    current = _transition(
        journal,
        current,
        stage="generation_finished",
        event_type="candidate_generation_finished",
        key=f"generation-finished:{current.get('stop_reason') or 'budget-complete'}",
    )
    machine = _replay_machine(request, journal, current, definitions)
    machine.finish_train()
    current["train_finished"] = True
    shortlist = machine.build_shortlist()
    current["shortlist_ids"] = list(shortlist)
    current = _transition(
        journal,
        current,
        stage="shortlist_ready",
        event_type="shortlist_derived",
        key=f"shortlist-derived:{canonical_sha256(list(shortlist))}",
    )
    freeze = machine.freeze_shortlist(
        compiler_sha256=request_payload["scope_hashes"]["compiler_sha256"],
        config_sha256=request_payload["scope_hashes"]["config_sha256"],
        retriever_sha256=request_payload["scope_hashes"]["retriever_sha256"],
        evaluator_sha256=request_payload["scope_hashes"]["evaluator_sha256"],
    )
    _ensure_artifact(journal, "shortlist-freeze-receipt.json", freeze)
    current["shortlist_freeze_sha256"] = freeze["receipt_sha256"]
    current = _transition(
        journal,
        current,
        stage="shortlist_frozen",
        event_type="shortlist_frozen",
        key=f"shortlist-frozen:{freeze['receipt_sha256']}",
    )
    if shortlist:
        counter = compare_and_swap_selection_counter(
            owner_store,
            request_id=request_payload["request_id"],
            freeze_sha256=freeze["receipt_sha256"],
        )
        current["selection_exposure_count"] = 1
        current["selection_counter_sha256"] = counter["counter_sha256"]
        current = _transition(
            journal,
            current,
            stage="selection_exposed",
            event_type="selection_exposure_committed",
            key=f"selection-exposure:{counter['counter_sha256']}",
        )
        machine = _replay_machine(request, journal, current, definitions)
        for candidate_id in shortlist:
            result_name = f"selection-{candidate_id}-result.json"
            if (journal.artifact_root / result_name).is_file():
                continue
            current = _measure_selection_with_retry(
                request=request_payload,
                candidate=definitions[candidate_id],
                state=current,
                profile=profile_payload,
                journal=journal,
                executor=executor,
                repository_root=root,
                result_name=result_name,
            )
            heartbeat()
    return _finalize_run(
        request=request,
        repository_root=root,
        journal=journal,
        state=current,
        definitions=definitions,
    )


def _measure_with_retry(
    *,
    request: Mapping[str, Any],
    candidate: Mapping[str, Any],
    data_role: str,
    state: dict[str, Any],
    profile: Mapping[str, Any],
    journal: MeasuredRunJournal,
    executor: CandidateExecutor,
    repository_root: Path,
) -> dict[str, Any]:
    candidate_id = str(candidate["candidate_id"])
    _ensure_artifact(
        journal, f"candidate-{candidate_id}-definition.json", candidate
    )
    attempts = state.setdefault("candidate_attempts", {}).get(candidate_id, 0)
    while attempts < 2:
        attempts += 1
        state["candidate_attempts"][candidate_id] = attempts
        try:
            result, state = executor(request, candidate, data_role, state)
        except (TimeoutError, OSError, subprocess.SubprocessError) as error:
            elapsed = float(getattr(error, "elapsed_seconds", 0.0))
            state["measurement_runtime_seconds"] = round(
                float(state.get("measurement_runtime_seconds", 0.0)) + elapsed,
                6,
            )
            quarantined = journal.quarantine_partial_indexes()
            if quarantined:
                state.setdefault("quarantined_partial_indexes", []).extend(quarantined)
            state["failure"] = {
                "category": "infrastructure",
                "candidate_id": candidate_id,
                "attempt": attempts,
                "detail_sha256": canonical_sha256({"error": str(error)}),
            }
            state = _transition(
                journal,
                state,
                stage="candidate_retry_pending" if attempts < 2 else "blocked_infrastructure",
                event_type="candidate_infrastructure_failure",
                key=f"candidate-infrastructure:{candidate_id}:{attempts}",
            )
            remaining = float(profile["runtime"]["measurement_budget_seconds"]) - float(
                state.get("measurement_runtime_seconds", 0.0)
            )
            if attempts >= 2 or remaining < float(
                profile["runtime"]["per_candidate_timeout_seconds"]
            ):
                raise MeasuredStateError(
                    f"candidate infrastructure retries exhausted: {candidate_id}"
                ) from error
            continue
        except P2ContractError as error:
            detail_sha256 = canonical_sha256({"error": str(error)})
            row = state.setdefault("candidates", {}).setdefault(candidate_id, {})
            row.update(
                {
                    "candidate_id": candidate_id,
                    "arm": candidate["arm"],
                    "class": candidate["candidate_class"],
                    "iteration": int(candidate.get("iteration", 0)),
                    "spec_sha256": candidate["spec_sha256"],
                    "status": "failed",
                    "failure_reason_sha256": detail_sha256,
                }
            )
            state["failure"] = {
                "category": "scientific_validation",
                "candidate_id": candidate_id,
                "attempt": attempts,
                "detail_sha256": detail_sha256,
            }
            _transition(
                journal,
                state,
                stage="blocked_scientific",
                event_type="candidate_scientific_failure",
                key=f"candidate-scientific:{candidate_id}:{attempts}:{detail_sha256}",
            )
            raise
        validated = validate_measured_artifact(result, repository_root)
        projected_index_builds = int(state.get("total_index_builds", 0)) + int(
            validated["index_build_count"]
        )
        if projected_index_builds > int(profile["limits"]["max_index_builds"]):
            state["failure"] = {
                "category": "budget",
                "candidate_id": candidate_id,
                "attempt": attempts,
                "limit": "max_index_builds",
            }
            _transition(
                journal,
                state,
                stage="blocked_budget",
                event_type="candidate_index_budget_exhausted",
                key=f"candidate-index-budget:{candidate_id}:{projected_index_builds}",
            )
            raise MeasuredStateError("candidate result exceeds the index build budget")
        _, artifact_hash = _ensure_artifact(
            journal, f"candidate-{candidate_id}-result.json", validated
        )
        row = state.setdefault("candidates", {}).setdefault(candidate_id, {})
        row.update(
            {
                "candidate_id": candidate_id,
                "arm": candidate["arm"],
                "class": candidate["candidate_class"],
                "iteration": int(candidate.get("iteration", 0)),
                "spec_sha256": candidate["spec_sha256"],
                "status": "train_complete",
                "result_sha256": artifact_hash,
            }
        )
        state.setdefault("accepted_result_ids", []).append(candidate_id)
        state["accepted_result_ids"] = list(dict.fromkeys(state["accepted_result_ids"]))
        state["total_index_builds"] = projected_index_builds
        state["measurement_runtime_seconds"] = round(
            float(state.get("measurement_runtime_seconds", 0.0))
            + float(result["runtime_seconds"]),
            6,
        )
        state["failure"] = None
        return _transition(
            journal,
            state,
            stage="candidate_train_completed",
            event_type="candidate_train_completed",
            key=f"candidate-result:{result['result_sha256']}",
        )
    raise MeasuredStateError(f"candidate did not complete: {candidate_id}")


def _measure_selection_with_retry(
    *,
    request: Mapping[str, Any],
    candidate: Mapping[str, Any],
    state: dict[str, Any],
    profile: Mapping[str, Any],
    journal: MeasuredRunJournal,
    executor: CandidateExecutor,
    repository_root: Path,
    result_name: str,
) -> dict[str, Any]:
    """Retry selection infrastructure failures without reopening selection."""

    candidate_id = str(candidate["candidate_id"])
    attempt_key = f"selection:{candidate_id}"
    attempts = int(state.setdefault("candidate_attempts", {}).get(attempt_key, 0))
    while attempts < 2:
        attempts += 1
        state["candidate_attempts"][attempt_key] = attempts
        try:
            result, state = executor(request, candidate, "selection", state)
        except (TimeoutError, OSError, subprocess.SubprocessError) as error:
            elapsed = float(getattr(error, "elapsed_seconds", 0.0))
            state["measurement_runtime_seconds"] = round(
                float(state.get("measurement_runtime_seconds", 0.0)) + elapsed,
                6,
            )
            quarantined = journal.quarantine_partial_indexes()
            if quarantined:
                state.setdefault("quarantined_partial_indexes", []).extend(quarantined)
            detail_sha256 = canonical_sha256({"error": str(error)})
            state["failure"] = {
                "category": "infrastructure",
                "candidate_id": candidate_id,
                "data_role": "selection",
                "attempt": attempts,
                "detail_sha256": detail_sha256,
            }
            state = _transition(
                journal,
                state,
                stage="selection_retry_pending" if attempts < 2 else "blocked_infrastructure",
                event_type="selection_infrastructure_failure",
                key=f"selection-infrastructure:{candidate_id}:{attempts}",
            )
            remaining = float(profile["runtime"]["measurement_budget_seconds"]) - float(
                state.get("measurement_runtime_seconds", 0.0)
            )
            if attempts >= 2 or remaining < float(profile["runtime"]["per_candidate_timeout_seconds"]):
                raise MeasuredStateError(
                    f"selection infrastructure retries exhausted: {candidate_id}"
                ) from error
            continue
        except P2ContractError as error:
            detail_sha256 = canonical_sha256({"error": str(error)})
            state["failure"] = {
                "category": "scientific_validation",
                "candidate_id": candidate_id,
                "data_role": "selection",
                "attempt": attempts,
                "detail_sha256": detail_sha256,
            }
            _transition(
                journal,
                state,
                stage="blocked_scientific",
                event_type="selection_scientific_failure",
                key=f"selection-scientific:{candidate_id}:{attempts}:{detail_sha256}",
            )
            raise
        validated = validate_measured_artifact(result, repository_root)
        _ensure_artifact(journal, result_name, validated)
        state["measurement_runtime_seconds"] = round(
            float(state.get("measurement_runtime_seconds", 0.0))
            + float(validated["runtime_seconds"]),
            6,
        )
        state["failure"] = None
        return _transition(
            journal,
            state,
            stage="selection_candidate_completed",
            event_type="selection_candidate_completed",
            key=f"selection-result:{validated['result_sha256']}",
        )
    raise MeasuredStateError(f"selection candidate did not complete: {candidate_id}")


def _subprocess_candidate_executor(
    *,
    request_path: Path,
    repository_root: Path,
    run_root: Path,
    cache_root: Path,
    journal: MeasuredRunJournal,
    heartbeat: Callable[[], None],
    timeout_seconds: int,
) -> CandidateExecutor:
    def execute(
        request: Mapping[str, Any],
        candidate: Mapping[str, Any],
        data_role: str,
        state: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        candidate_id = str(candidate["candidate_id"])
        definition_path = (
            journal.artifact_root / f"candidate-{candidate_id}-definition.json"
        )
        work_root = Path(run_root) / "work"
        work_root.mkdir(parents=True, exist_ok=True)
        output_path = work_root / f"{data_role}-{candidate_id}-result.json"
        if output_path.is_file():
            result = validate_measured_artifact(
                _json_file(output_path), repository_root
            )
            return result, state
        logs = Path(run_root) / "logs" / "candidates"
        logs.mkdir(parents=True, exist_ok=True)
        stdout_path = logs / f"{data_role}-{candidate_id}.stdout.log"
        stderr_path = logs / f"{data_role}-{candidate_id}.stderr.log"
        command = [
            sys.executable,
            "-m",
            "myis_research.p2_measured_cli",
            "candidate-worker",
            "--request",
            str(Path(request_path).resolve()),
            "--candidate-definition",
            str(definition_path),
            "--data-role",
            data_role,
            "--repository-root",
            str(Path(repository_root).resolve()),
            "--cache-root",
            str(Path(cache_root).resolve()),
            "--run-root",
            str(Path(run_root).resolve()),
            "--output",
            str(output_path),
        ]
        started = time.monotonic()
        with stdout_path.open("ab", buffering=0) as stdout_handle, stderr_path.open(
            "ab", buffering=0
        ) as stderr_handle:
            process = subprocess.Popen(
                command,
                cwd=repository_root,
                env=sanitized_runtime_environment(),
                stdin=subprocess.DEVNULL,
                stdout=stdout_handle,
                stderr=stderr_handle,
                close_fds=True,
            )
            identity = process_creation_identity(process.pid)
            if identity is None:
                process.terminate()
                process.wait(timeout=10)
                raise OSError("cannot bind candidate child process identity")
            state["active_child"] = {
                "pid": process.pid,
                "process_creation_identity": identity,
                "candidate_id": candidate_id,
                "data_role": data_role,
            }
            state = _transition(
                journal,
                state,
                stage="candidate_child_active",
                event_type="candidate_child_started",
                key=f"candidate-child:{candidate_id}:{data_role}:{identity}",
            )
            timeout = timeout_seconds
            try:
                return_code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired as error:
                process.terminate()
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)
                state["active_child"] = None
                _transition(
                    journal,
                    state,
                    stage="candidate_timeout",
                    event_type="candidate_child_timed_out",
                    key=f"candidate-timeout:{candidate_id}:{data_role}:{identity}",
                )
                timeout_error = TimeoutError(
                    f"candidate timed out after {timeout} seconds: {candidate_id}"
                )
                timeout_error.elapsed_seconds = time.monotonic() - started  # type: ignore[attr-defined]
                raise timeout_error from error
        state["active_child"] = None
        state = _transition(
            journal,
            state,
            stage="candidate_child_finished",
            event_type="candidate_child_finished",
            key=f"candidate-child-finished:{candidate_id}:{data_role}:{identity}",
        )
        heartbeat()
        if return_code != 0:
            if return_code == 3:
                raise P2ContractError(
                    f"candidate scientific validation failed: {candidate_id}"
                )
            error = subprocess.SubprocessError(
                f"candidate worker exited with code {return_code}: {candidate_id}"
            )
            error.elapsed_seconds = time.monotonic() - started  # type: ignore[attr-defined]
            raise error
        result = validate_measured_artifact(_json_file(output_path), repository_root)
        output_path.unlink(missing_ok=True)
        return result, state

    return execute


def _replay_machine(
    request: Mapping[str, Any],
    journal: MeasuredRunJournal,
    state: Mapping[str, Any],
    definitions: Mapping[str, Mapping[str, Any]],
) -> P2RunStateMachine:
    profile_payload = dict(request["_resolved"]["profile"])
    machine = P2RunStateMachine(
        request_id=str(request["request_id"]),
        profile=P2BudgetProfile(profile_payload, canonical_sha256(profile_payload)),
    )
    base_definitions = sorted(
        (
            item
            for item in definitions.values()
            if int(item.get("iteration", 0)) == 0
        ),
        key=lambda item: (
            0 if item["candidate_class"] == "frozen_control" else 1,
            str(item["candidate_id"]),
        ),
    )
    for definition in base_definitions:
        machine.register_candidate(
            Candidate(
                str(definition["candidate_id"]),
                str(definition["arm"]),
                str(definition["candidate_class"]),
                int(definition.get("iteration", 0)),
                str(definition["spec_sha256"]),
            )
        )
    commitment_path = journal.artifact_root / "baseline-commitment.json"
    if commitment_path.is_file():
        commitment = _json_file(commitment_path)
        machine.commit_baseline_expectation(
            baseline_candidate_id=commitment["baseline_candidate_id"],
            baseline_arm=commitment["baseline_arm"],
            prior_artifact_uri=commitment["prior_artifact_uri"],
            prior_artifact_sha256=commitment["prior_artifact_sha256"],
            metric_locator=commitment["metric_locator"],
            expected_metric=commitment["expected_metric"],
            tolerance=commitment["tolerance"],
        )
    accepted = {str(item) for item in state.get("accepted_result_ids", [])}
    for definition in base_definitions:
        candidate_id = str(definition["candidate_id"])
        if candidate_id not in accepted:
            continue
        result = _candidate_result(journal, candidate_id)
        machine.record_train(
            candidate_id,
            status="train_complete",
            metric=result["metric"],
            index_build_count=int(result["index_build_count"]),
        )
    baseline_path = journal.artifact_root / "baseline-reproduction-receipt.json"
    if baseline_path.is_file():
        baseline = _json_file(baseline_path)
        machine.record_baseline_reproduction(result=baseline["result"])
    completed_iterations = {
        int(item) for item in state.get("completed_iterations", [])
    }
    adaptive_iterations = sorted(
        {
            int(item.get("iteration", 0))
            for item in definitions.values()
            if int(item.get("iteration", 0)) > 0
        }
    )
    for iteration in adaptive_iterations:
        members = sorted(
            (
                item
                for item in definitions.values()
                if int(item.get("iteration", 0)) == iteration
            ),
            key=lambda item: str(item["candidate_id"]),
        )
        for definition in members:
            machine.register_candidate(
                Candidate(
                    str(definition["candidate_id"]),
                    str(definition["arm"]),
                    str(definition["candidate_class"]),
                    iteration,
                    str(definition["spec_sha256"]),
                )
            )
        for definition in members:
            candidate_id = str(definition["candidate_id"])
            if candidate_id not in accepted:
                continue
            result = _candidate_result(journal, candidate_id)
            machine.record_train(
                candidate_id,
                status="train_complete",
                metric=result["metric"],
                index_build_count=int(result["index_build_count"]),
            )
        if iteration in completed_iterations:
            machine.record_iteration(iteration)
    if state.get("generation_finished"):
        machine.finish_generation_with_reason(state.get("stop_reason"))
    if state.get("train_finished"):
        machine.finish_train()
        observed = machine.build_shortlist()
        if list(observed) != list(state.get("shortlist_ids", [])):
            raise MeasuredStateError("replayed shortlist differs from journal state")
    freeze_path = journal.artifact_root / "shortlist-freeze-receipt.json"
    if freeze_path.is_file():
        freeze = _json_file(freeze_path)
        rebuilt = machine.freeze_shortlist(
            compiler_sha256=freeze["compiler_sha256"],
            config_sha256=freeze["config_sha256"],
            retriever_sha256=freeze["retriever_sha256"],
            evaluator_sha256=freeze["evaluator_sha256"],
        )
        if rebuilt != freeze:
            raise MeasuredStateError("replayed shortlist freeze differs from artifact")
    if int(state.get("selection_exposure_count", 0)) == 1:
        machine.open_selection()
        for candidate_id in state.get("shortlist_ids", []):
            path = journal.artifact_root / f"selection-{candidate_id}-result.json"
            if not path.is_file():
                continue
            metric = deepcopy(_json_file(path)["metric"])
            metric.pop("candidate_id", None)
            machine.record_selection(
                str(candidate_id), metric=metric
            )
    return machine


def _finalize_run(
    *,
    request: Mapping[str, Any],
    repository_root: Path,
    journal: MeasuredRunJournal,
    state: dict[str, Any],
    definitions: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    machine = _replay_machine(request, journal, state, definitions)
    shortlist = tuple(state.get("shortlist_ids", []))
    if shortlist:
        if any(
            not (journal.artifact_root / f"selection-{candidate_id}-result.json").is_file()
            for candidate_id in shortlist
        ):
            raise MeasuredStateError("selection closeout is missing finalist results")
        machine.close()
        selection = machine.build_selection_receipt()
        _ensure_artifact(journal, "selection-receipt.json", selection)
        state["selection_receipt_sha256"] = selection["receipt_sha256"]
    else:
        machine.open_selection()
        selection = None
    ledger = validate_p2_artifact(
        machine.build_candidate_ledger(), repository_root=repository_root
    )
    commitment = validate_p2_artifact(
        _json_file(journal.artifact_root / "baseline-commitment.json"),
        repository_root=repository_root,
    )
    baseline = validate_p2_artifact(
        _json_file(journal.artifact_root / "baseline-reproduction-receipt.json"),
        repository_root=repository_root,
    )
    freeze = validate_p2_artifact(
        _json_file(journal.artifact_root / "shortlist-freeze-receipt.json"),
        repository_root=repository_root,
    )
    request_payload = _request_payload(request)
    canonical_request = build_request(
        request_id=request_payload["request_id"],
        git_commit=request_payload["execution_source_commit"],
        execution_envelope_sha256=request_payload["execution_envelope_sha256"],
        scope_hashes=request_payload["scope_hashes"],
        input_hashes=request_payload["input_hashes"],
        frozen_controls=[
            str(item["candidate_id"])
            for item in request["_resolved"]["base_candidate_set"]["frozen_controls"]
        ],
        repository_root=repository_root,
        budget_profile_uri=request_payload["budget_profile_uri"],
    )
    _ensure_artifact(journal, "canonical-request.json", canonical_request)
    _ensure_artifact(journal, "candidate-ledger.json", ledger)
    metrics = selection["metrics"] if selection is not None else []
    manifest = {
        "schema_version": "myis.p2-manifest.v1",
        "run_id": request_payload["request_id"],
        "request_id": request_payload["request_id"],
        "phase_id": "P2_SCOPE_DEVELOPMENT",
        "arm": "R1",
        "campaign_revision": request_payload["campaign_revision"],
        "budget_profile_id": request_payload["budget_profile_id"],
        "budget_profile_sha256": request_payload["budget_profile_sha256"],
        "status": "valid" if shortlist else "negative_development",
        "evidence_class": "train_selection_measured",
        "request_sha256": canonical_sha256(canonical_request),
        "candidate_ledger_sha256": ledger["ledger_sha256"],
        "baseline_commitment_sha256": commitment["commitment_sha256"],
        "baseline_reproduction_receipt_sha256": baseline["receipt_sha256"],
        "shortlist_freeze_receipt_sha256": freeze["receipt_sha256"],
        "selection_receipt_sha256": (
            selection["receipt_sha256"] if selection is not None else None
        ),
        "candidate_count": ledger["candidate_count"],
        "candidate_ids": list(shortlist),
        "selection_exposure_count": 1 if shortlist else 0,
        "metrics": metrics,
    }
    manifest["manifest_sha256"] = canonical_sha256(manifest)
    manifest = validate_p2_artifact(manifest, repository_root=repository_root)
    _ensure_artifact(journal, "manifest.json", manifest)
    package = {
        "schema_version": "myis.p2-package.v1",
        "package_id": f"{request_payload['request_id']}-package",
        "request_id": request_payload["request_id"],
        "campaign_revision": request_payload["campaign_revision"],
        "status": "validated_structural" if shortlist else "negative_development",
        "request_uri": "canonical-request.json",
        "request_sha256": canonical_sha256(canonical_request),
        "candidate_ledger_uri": "candidate-ledger.json",
        "candidate_ledger_sha256": ledger["ledger_sha256"],
        "baseline_commitment_uri": "baseline-commitment.json",
        "baseline_commitment_sha256": commitment["commitment_sha256"],
        "baseline_reproduction_uri": "baseline-reproduction-receipt.json",
        "baseline_reproduction_sha256": baseline["receipt_sha256"],
        "shortlist_freeze_uri": "shortlist-freeze-receipt.json",
        "shortlist_freeze_sha256": freeze["receipt_sha256"],
        "selection_uri": "selection-receipt.json" if selection is not None else None,
        "selection_sha256": selection["receipt_sha256"] if selection is not None else None,
        "manifest_uri": "manifest.json",
        "manifest_sha256": manifest["manifest_sha256"],
        "budget_profile_id": request_payload["budget_profile_id"],
        "budget_profile_sha256": request_payload["budget_profile_sha256"],
        "candidate_count": ledger["candidate_count"],
        "selection_exposure_count": 1 if shortlist else 0,
    }
    package["package_sha256"] = canonical_sha256(package)
    validate_p2_package_bundle(
        request=canonical_request,
        ledger=ledger,
        commitment=commitment,
        baseline=baseline,
        freeze=freeze,
        selection=selection,
        manifest=manifest,
        package=package,
        repository_root=repository_root,
        artifact_root=journal.artifact_root,
    )
    _ensure_artifact(journal, "package.json", package)
    state["stage"] = "measured_complete"
    state["failure"] = None
    state["package_sha256"] = package["package_sha256"]
    return journal.append_transition(
        state,
        event_type="measured_run_completed",
        idempotency_key=f"measured-complete:{package['package_sha256']}",
    )


def _candidate_definitions(
    request: Mapping[str, Any], journal: MeasuredRunJournal
) -> dict[str, dict[str, Any]]:
    base = request["_resolved"]["base_candidate_set"]
    definitions: dict[str, dict[str, Any]] = {}
    for row in [*base["frozen_controls"], *base["preregistered_candidates"]]:
        definition = {**deepcopy(row), "iteration": 0}
        definitions[str(definition["candidate_id"])] = definition
    for path in sorted(journal.artifact_root.glob("adaptive-batch-i*.json")):
        batch = _json_file(path)
        for row in batch["candidates"]:
            definition = _adaptive_definition(row, iteration=int(batch["iteration"]))
            definitions[str(definition["candidate_id"])] = definition
    return definitions


def _adaptive_definition(
    row: Mapping[str, Any], *, iteration: int
) -> dict[str, Any]:
    spec = deepcopy(dict(row["scope_spec"]))
    aggregation = str(spec.get("aggregation", {}).get("rule", "family_maxp"))
    return {
        **deepcopy(dict(row)),
        "candidate_class": "adaptive_autoindex",
        "arm": "R1",
        "iteration": iteration,
        "retrieval": {
            "scorer": "sqlite_fts5_bm25_v1",
            "query_operator": "OR",
            "top_k": 100,
            "family_aggregation": aggregation,
            "fts_tokenizer": "unicode61 remove_diacritics 2",
            "lexical_tokenizer": "python-re-unicode-word-casefold-v1",
        },
    }


def _build_feedback(
    *,
    request: Mapping[str, Any],
    machine: P2RunStateMachine,
    policy: Mapping[str, Any],
    iteration: int,
    state: Mapping[str, Any],
    repository_root: Path,
) -> dict[str, Any]:
    baseline = machine.baseline_commitment["expected_metric"]
    rows = []
    used_axes = {str(item) for item in state.get("used_adaptive_axes", [])}
    for candidate in sorted(machine.candidates.values(), key=lambda item: str(item["candidate_id"])):
        metric = candidate.get("train_metric")
        if metric is None:
            continue
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "arm": candidate["arm"],
                "candidate_class": candidate["class"],
                "iteration": candidate["iteration"],
                "value": metric["value"],
                "delta_from_baseline": round(
                    float(metric["value"]) - float(baseline["value"]), 12
                ),
            }
        )
    feedback = {
        "schema_version": "myis.p2-adaptive-feedback.v1",
        "feedback_id": f"{request['request_id']}-feedback-i{iteration:02d}",
        "request_id": request["request_id"],
        "campaign_revision": request["campaign_revision"],
        "iteration": iteration,
        "lineage_hashes": {
            **dict(request["scope_hashes"]),
            "dataset_lineage_sha256": state["dataset_lineage_sha256"],
        },
        "aggregate_candidates": rows,
        "failure_categories": [],
        "remaining_axes": [
            axis for axis in policy["allowed_axes"] if axis not in used_axes
        ],
        "budget_counters": {
            "candidate_count": len(state.get("accepted_result_ids", [])),
            "completed_iterations": len(state.get("completed_iterations", [])),
            "measurement_runtime_seconds": state.get(
                "measurement_runtime_seconds", 0.0
            ),
        },
        "selection_exposures": 0,
        "protected_data_accessed": False,
    }
    feedback["feedback_sha256"] = canonical_sha256(feedback)
    return validate_measured_artifact(feedback, repository_root)


def _stop_at_checkpoint(
    journal: MeasuredRunJournal, state: dict[str, Any]
) -> dict[str, Any]:
    state["stage"] = "stopped_after_checkpoint"
    state["stop_after_checkpoint_requested"] = True
    state["stop_reason"] = "owner_stop_after_checkpoint"
    return journal.append_transition(
        state,
        event_type="stop_after_checkpoint_acknowledged",
        idempotency_key=f"stop-after-checkpoint:{state['journal_sequence']}",
    )


def _transition(
    journal: MeasuredRunJournal,
    state: Mapping[str, Any],
    *,
    stage: str,
    event_type: str,
    key: str,
) -> dict[str, Any]:
    updated = deepcopy(dict(state))
    updated["stage"] = stage
    return journal.append_transition(
        updated, event_type=event_type, idempotency_key=key
    )


def _ensure_artifact(
    journal: MeasuredRunJournal,
    name: str,
    payload: Mapping[str, Any],
) -> tuple[Path, str]:
    path = journal.artifact_root / name
    if path.is_file():
        existing = _json_file(path)
        if existing != dict(payload):
            raise MeasuredStateError(
                f"immutable measured artifact differs on resume: {name}"
            )
        return path, file_sha256(path)
    return journal.write_artifact(name, payload)


def _candidate_result(
    journal: MeasuredRunJournal, candidate_id: str
) -> dict[str, Any]:
    return _json_file(journal.artifact_root / f"candidate-{candidate_id}-result.json")


def _request_payload(request: Mapping[str, Any]) -> dict[str, Any]:
    return {key: deepcopy(value) for key, value in request.items() if key != "_resolved"}


def _json_file(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MeasuredStateError(f"cannot read measured executor JSON: {path}") from error
    if not isinstance(value, dict):
        raise MeasuredStateError(f"measured executor JSON must be an object: {path}")
    return value
