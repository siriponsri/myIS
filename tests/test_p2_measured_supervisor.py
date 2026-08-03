from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import time

import pytest

from myis_research.kernel.canonical import file_sha256
from myis_research.p2.base_candidates import (
    build_adaptive_policy,
    build_base_candidate_set,
    build_proposer_contract,
)
from myis_research.p2.measured_contracts import build_measured_request
from myis_research.p2.measured_state import MeasuredStateError
from myis_research.p2.measured_supervisor import (
    request_stop_after_checkpoint,
    run_worker,
    start_detached_worker,
    status,
    verify_run,
)
from myis_research.p2.proposer import PROPOSER_INSTRUCTIONS_SHA256


ROOT = Path(__file__).resolve().parents[1]


def _git(repository: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _prepare_repository(tmp_path: Path) -> tuple[Path, Path]:
    repository = tmp_path / "repository"
    (repository / "schemas").mkdir(parents=True)
    (repository / "control" / "budgets").mkdir(parents=True)
    (repository / "control" / "p2").mkdir(parents=True)
    for schema in (ROOT / "schemas").glob("p2-*.v1.json"):
        shutil.copy2(schema, repository / "schemas" / schema.name)
    shutil.copy2(
        ROOT / "control" / "budgets" / "p2-r1-primary-v2.yaml",
        repository / "control" / "budgets" / "p2-r1-primary-v2.yaml",
    )
    shutil.copy2(
        ROOT / "control" / "execution-envelope-p2-v2.yaml",
        repository / "control" / "execution-envelope-p2-v2.yaml",
    )
    artifacts = {
        "p2-base-candidate-set-r1-v2.json": build_base_candidate_set(
            ROOT,
            committed_hashes=False,
        ),
        "p2-adaptive-policy-r1-v2.json": build_adaptive_policy(),
        "p2-proposer-contract-r1-v2.json": build_proposer_contract(),
    }
    for name, payload in artifacts.items():
        (repository / "control" / "p2" / name).write_text(
            json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    _git(repository, "init")
    _git(repository, "config", "user.email", "p2-supervisor-test@example.invalid")
    _git(repository, "config", "user.name", "P2 Supervisor Test")
    _git(repository, "add", ".")
    _git(repository, "commit", "-m", "synthetic supervisor fixture")
    request = build_measured_request(
        repository_root=repository,
        request_id="p2-detached-supervisor-test",
        budget_profile_uri="control/budgets/p2-r1-primary-v2.yaml",
        execution_envelope_uri="control/execution-envelope-p2-v2.yaml",
        base_candidate_set_uri="control/p2/p2-base-candidate-set-r1-v2.json",
        adaptive_policy_uri="control/p2/p2-adaptive-policy-r1-v2.json",
        proposer_contract_uri="control/p2/p2-proposer-contract-r1-v2.json",
        proposer_identity={
            "provider": "synthetic",
            "model": "synthetic",
            "revision": "synthetic",
            "effort": "none",
            "tool_version": "synthetic",
            "instructions_sha256": PROPOSER_INSTRUCTIONS_SHA256,
            "output_schema_sha256": file_sha256(
                repository / "schemas" / "p2-scope-candidate-batch.v1.json"
            ),
            "seed": 42,
            "fallback": False,
        },
        input_hashes={
            "synthetic_input_sha256": "a" * 64,
            "dataset_lineage_sha256": "d" * 64,
        },
        scope_hashes={
            "compiler_sha256": artifacts[
                "p2-base-candidate-set-r1-v2.json"
            ]["compiler_sha256"],
            "config_sha256": "b" * 64,
            "retriever_sha256": "c" * 64,
            "evaluator_sha256": "e" * 64,
        },
        global_counters={
            "measured_runs": 0,
            "candidate_count": 0,
            "shortlist_count": 0,
            "selection_accesses": 0,
        },
    )
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(request, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return repository, request_path


def test_detached_worker_survives_launcher_return_and_completes_synthetic_soak(
    tmp_path: Path,
) -> None:
    repository, request_path = _prepare_repository(tmp_path)
    run_root = tmp_path / "owner-run"
    startup = start_detached_worker(
        request_path=request_path,
        run_root=run_root,
        repository_root=repository,
        mode="start",
        synthetic_checkpoints=8,
        checkpoint_delay_seconds=0.05,
        startup_timeout_seconds=20,
    )
    assert startup["status"] == "started"
    deadline = time.monotonic() + 20
    current = {}
    while time.monotonic() < deadline:
        current = status(run_root)
        if current["stage"] == "synthetic_complete":
            break
        time.sleep(0.05)
    assert current["stage"] == "synthetic_complete"
    verification = verify_run(
        run_root=run_root,
        request_path=request_path,
        repository_root=repository,
    )
    assert verification["status"] == "passed"
    assert verification["journal_event_count"] == 11
    assert (run_root / "logs" / "worker.stdout.log").is_file()
    assert (run_root / "logs" / "worker.stderr.log").is_file()


def test_supervisor_rejects_run_root_inside_repository(tmp_path: Path) -> None:
    repository, request_path = _prepare_repository(tmp_path)
    with pytest.raises(MeasuredStateError, match="outside the Git worktree"):
        start_detached_worker(
            request_path=request_path,
            run_root=repository / "owner-run",
            repository_root=repository,
            mode="start",
            synthetic_checkpoints=1,
        )


def test_measured_start_and_worker_require_explicit_owner_paths(
    tmp_path: Path,
) -> None:
    repository, request_path = _prepare_repository(tmp_path)
    with pytest.raises(MeasuredStateError, match="--owner-store and --cache-root"):
        start_detached_worker(
            request_path=request_path,
            run_root=tmp_path / "owner-run-start",
            repository_root=repository,
            mode="start",
        )
    with pytest.raises(MeasuredStateError, match="owner store and cache roots"):
        run_worker(
            request_path=request_path,
            run_root=tmp_path / "owner-run-worker",
            repository_root=repository,
            mode="start",
        )


def test_stop_after_checkpoint_is_acknowledged_and_resume_continues(
    tmp_path: Path,
) -> None:
    repository, request_path = _prepare_repository(tmp_path)
    run_root = tmp_path / "owner-run"

    def checkpoint_hook(checkpoint: int) -> None:
        if checkpoint == 2:
            request_stop_after_checkpoint(run_root)

    stopped = run_worker(
        request_path=request_path,
        run_root=run_root,
        repository_root=repository,
        mode="start",
        synthetic_checkpoints=6,
        checkpoint_hook=checkpoint_hook,
    )
    assert stopped["stage"] == "stopped_after_checkpoint"
    stop_request = json.loads(
        (run_root / "control" / "stop-after-checkpoint.json").read_text(
            encoding="utf-8"
        )
    )
    assert stop_request["status"] == "acknowledged"

    resumed = run_worker(
        request_path=request_path,
        run_root=run_root,
        repository_root=repository,
        mode="resume",
        synthetic_checkpoints=6,
    )
    assert resumed["stage"] == "synthetic_complete"
    assert resumed["synthetic_checkpoint"] == 6
    assert verify_run(run_root=run_root)["status"] == "passed"
