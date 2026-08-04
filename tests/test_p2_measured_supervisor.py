from __future__ import annotations

import json
from pathlib import Path
import time

import pytest

from tests._p2_v2_fixture import prepare_v2_repository
from myis_research.p2.measured_state import MeasuredStateError
from myis_research.p2.measured_supervisor import (
    request_stop_after_checkpoint,
    run_worker,
    start_detached_worker,
    status,
    verify_run,
)


ROOT = Path(__file__).resolve().parents[1]


def _prepare_repository(tmp_path: Path) -> tuple[Path, Path]:
    repository = tmp_path / "repository"
    generated_path, _ = prepare_v2_repository(
        repository,
        request_id="p2-detached-supervisor-test",
    )
    request_path = tmp_path / "request.json"
    request_path.write_bytes(generated_path.read_bytes())
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
