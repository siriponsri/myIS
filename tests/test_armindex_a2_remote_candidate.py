from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from myis_research.armindex import a2_remote_candidate as remote
from myis_research.kernel.canonical import canonical_sha256


ATTEMPT = "a2-remote-test01"
CANDIDATE = "a2-arm-03-matched-b1-exploit"


def _result() -> dict[str, object]:
    body: dict[str, object] = {
        "schema_version": "synthetic.remote-result.v1",
        "attempt_id": ATTEMPT,
        "candidate_id": CANDIDATE,
        "status": "PASS_SYNTHETIC_REMOTE_RESULT",
    }
    return {**body, "receipt_sha256": canonical_sha256(body)}


def test_durable_result_prevents_duplicate_worker_launch(tmp_path: Path) -> None:
    result_path = tmp_path / "lifecycle" / "candidates" / CANDIDATE / "result.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(json.dumps(_result()), encoding="ascii")

    result = remote.supervise_candidate(
        attempt_id=ATTEMPT,
        candidate_id=CANDIDATE,
        lifecycle_root=tmp_path / "lifecycle",
        worker_argv=["this-command-must-not-run"],
        timeout_seconds=1,
    )

    assert result["status"] == "PASS_SYNTHETIC_REMOTE_RESULT"


def test_supervisor_lock_fails_closed_before_duplicate_launch(tmp_path: Path) -> None:
    candidate_root = tmp_path / "lifecycle" / "candidates" / CANDIDATE
    with remote._candidate_lock(candidate_root / "supervisor.lock"):
        with pytest.raises(remote.A2RemoteCandidateError, match="supervisor owns"):
            remote.supervise_candidate(
                attempt_id=ATTEMPT,
                candidate_id=CANDIDATE,
                lifecycle_root=tmp_path / "lifecycle",
                worker_argv=[sys.executable, "-c", "raise SystemExit(99)"],
                timeout_seconds=1,
            )


def test_dead_worker_stdout_is_made_durable_without_relaunch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    candidate_root = tmp_path / "lifecycle" / "candidates" / CANDIDATE
    candidate_root.mkdir(parents=True)
    worker = ["this-command-must-not-run"]
    (candidate_root / "process.identity.json").write_text(
        json.dumps(
            {
                "attempt_id": ATTEMPT,
                "candidate_id": CANDIDATE,
                "pid": 321,
                "start_tick": 654,
                "command_sha256": canonical_sha256(worker),
                "status": "RUNNING",
            }
        ),
        encoding="ascii",
    )
    (candidate_root / "worker.stdout").write_text(
        json.dumps(_result()), encoding="utf-8"
    )
    monkeypatch.setattr(remote, "_same_process", lambda _identity: False)

    result = remote.supervise_candidate(
        attempt_id=ATTEMPT,
        candidate_id=CANDIDATE,
        lifecycle_root=tmp_path / "lifecycle",
        worker_argv=worker,
        timeout_seconds=1,
    )

    assert result == _result()
    assert json.loads((candidate_root / "result.json").read_text()) == _result()
    recovery = json.loads((candidate_root / "recovery.json").read_text())
    assert recovery["result_recovered_without_relaunch"] is True


def test_process_identity_cannot_cross_attempts(tmp_path: Path) -> None:
    candidate_root = tmp_path / "lifecycle" / "candidates" / CANDIDATE
    candidate_root.mkdir(parents=True)
    worker = [sys.executable, "-c", "raise SystemExit(99)"]
    (candidate_root / "process.identity.json").write_text(
        json.dumps(
            {
                "attempt_id": "a2-other-attempt01",
                "candidate_id": CANDIDATE,
                "pid": 321,
                "start_tick": 654,
                "command_sha256": canonical_sha256(worker),
            }
        ),
        encoding="ascii",
    )

    with pytest.raises(remote.A2RemoteCandidateError, match="identity binding drift"):
        remote.supervise_candidate(
            attempt_id=ATTEMPT,
            candidate_id=CANDIDATE,
            lifecycle_root=tmp_path / "lifecycle",
            worker_argv=worker,
            timeout_seconds=1,
        )


def test_stale_identity_is_reaped_before_synthetic_recovery(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    candidate_root = tmp_path / "lifecycle" / "candidates" / CANDIDATE
    candidate_root.mkdir(parents=True)
    (candidate_root / "process.identity.json").write_text(
        json.dumps(
            {
                "attempt_id": ATTEMPT,
                "candidate_id": CANDIDATE,
                "pid": 321,
                "start_tick": 654,
                "command_sha256": canonical_sha256(
                    [sys.executable, "-c", json.dumps("")]
                ),
                "status": "RUNNING",
            }
        ),
        encoding="ascii",
    )
    states = iter((True, False))
    monkeypatch.setattr(remote, "_same_process", lambda _identity: next(states))
    reaped: list[bool] = []
    monkeypatch.setattr(
        remote,
        "_terminate_and_reap",
        lambda _identity, grace_seconds: reaped.append(grace_seconds > 0) or True,
    )
    monkeypatch.setattr(remote, "_proc_start_tick", lambda _pid: 999)
    encoded = json.dumps(_result(), sort_keys=True, separators=(",", ":"))
    worker = [sys.executable, "-c", f"print({encoded!r})"]
    identity = json.loads(
        (candidate_root / "process.identity.json").read_text(encoding="ascii")
    )
    identity["command_sha256"] = canonical_sha256(worker)
    (candidate_root / "process.identity.json").write_text(
        json.dumps(identity), encoding="ascii"
    )

    result = remote.supervise_candidate(
        attempt_id=ATTEMPT,
        candidate_id=CANDIDATE,
        lifecycle_root=tmp_path / "lifecycle",
        worker_argv=worker,
        timeout_seconds=2,
        heartbeat_interval_seconds=0.01,
        stale_heartbeat_seconds=0.01,
        terminate_grace_seconds=0.1,
    )

    assert result["status"] == "PASS_SYNTHETIC_REMOTE_RESULT"
    assert reaped == [True]
    recovery = json.loads((candidate_root / "recovery.json").read_text(encoding="ascii"))
    assert recovery == {
        "attempt_id": ATTEMPT,
        "candidate_id": CANDIDATE,
        "prior_worker_reaped": True,
        "recovery_count": 1,
    }
    identity = json.loads(
        (candidate_root / "process.identity.json").read_text(encoding="ascii")
    )
    assert identity["status"] == "REAPED_WITH_DURABLE_RESULT"
    assert identity["process_alive"] is False


def test_durable_cancellation_reaps_existing_identity_without_restart(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    candidate_root = tmp_path / "lifecycle" / "candidates" / CANDIDATE
    candidate_root.mkdir(parents=True)
    (candidate_root / "process.identity.json").write_text(
        json.dumps(
            {
                "attempt_id": ATTEMPT,
                "candidate_id": CANDIDATE,
                "pid": 321,
                "start_tick": 654,
                "command_sha256": canonical_sha256(
                    [sys.executable, "-c", "raise SystemExit(99)"]
                ),
            }
        ),
        encoding="ascii",
    )
    (candidate_root / "cancel.request.json").write_text("{}", encoding="ascii")
    monkeypatch.setattr(remote, "_same_process", lambda _identity: True)
    reaped: list[bool] = []
    monkeypatch.setattr(
        remote,
        "_terminate_and_reap",
        lambda _identity, grace_seconds: reaped.append(grace_seconds > 0) or True,
    )

    with pytest.raises(remote.A2RemoteCandidateError, match="cancellation is durable"):
        remote.supervise_candidate(
            attempt_id=ATTEMPT,
            candidate_id=CANDIDATE,
            lifecycle_root=tmp_path / "lifecycle",
            worker_argv=[sys.executable, "-c", "raise SystemExit(99)"],
            timeout_seconds=1,
        )

    assert reaped == [True]


def test_interrupted_transport_marks_local_process_state(
    tmp_path: Path,
) -> None:
    # The SSH adapter test owns command construction. This test locks the
    # failure evidence contract without requiring an SSH endpoint.
    from myis_research.armindex.a2_remote_transport import RemoteExecutor
    from test_armindex_a2_remote_transport import _config

    def interrupted(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired("ssh", 1)

    executor = RemoteExecutor(config=_config(tmp_path), attempt_id=ATTEMPT, runner=interrupted)
    process_path = tmp_path / "process.json"
    with pytest.raises(subprocess.TimeoutExpired):
        executor(
            ["ignored"],
            environment={
                "MYIS_A2_CANDIDATE_ID": CANDIDATE,
                "MYIS_A2_ARM_ID": "ARM-03",
                "MYIS_A2_PROGRAM_SHA256": "a" * 64,
            },
            heartbeat_path=tmp_path / "heartbeat.json",
            process_path=process_path,
            timeout_seconds=1,
        )
    state = json.loads(process_path.read_text(encoding="ascii"))
    assert state["status"] == "REMOTE_TRANSPORT_INTERRUPTED"
