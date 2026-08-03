from __future__ import annotations

import json
import multiprocessing
import os
from pathlib import Path
import stat
import time

import pytest

from myis_research.kernel.canonical import canonical_sha256, file_sha256
from myis_research.p2.measured_state import (
    ExclusiveWriterLease,
    MeasuredRunJournal,
    MeasuredStateError,
    _pid_is_alive,
    compare_and_swap_selection_counter,
    process_creation_identity,
    validate_resume_state,
)
from myis_research.p2 import contracts as p2_contracts


def _request() -> dict:
    return {
        "schema_version": "myis.p2-measured-request.v1",
        "request_id": "p2-measured-state-test",
        "campaign_revision": "scope-autoindex-v1-p2-r1-primary-v2",
        "budget_profile_id": "p2-r1-primary-v2",
        "budget_profile_sha256": "b" * 64,
        "execution_source_commit": "c" * 40,
        "execution_source_tree": "d" * 40,
    }


def _hold_lease(run_root: str, ready: multiprocessing.synchronize.Event) -> None:
    with ExclusiveWriterLease(
        Path(run_root),
        run_id="run-1",
        request_sha256="a" * 64,
    ):
        ready.set()
        time.sleep(30)


def _selection_writer(
    owner_store: str,
    request_id: str,
    freeze_sha256: str,
    ready: multiprocessing.synchronize.Event,
    start: multiprocessing.synchronize.Event,
    queue: multiprocessing.Queue,
) -> None:
    ready.set()
    start.wait(10)
    try:
        compare_and_swap_selection_counter(
            Path(owner_store),
            request_id=request_id,
            freeze_sha256=freeze_sha256,
        )
    except MeasuredStateError as error:
        queue.put(("error", str(error)))
    else:
        queue.put(("ok", request_id))


def test_measured_journal_is_hash_chained_rebuildable_and_immutable(tmp_path: Path) -> None:
    journal = MeasuredRunJournal(tmp_path / "run")
    state = journal.initialize(
        run_id="run-1",
        request=_request(),
        owner_paths={
            "cache_root": str(tmp_path / "cache"),
            "index_root": str(tmp_path / "index"),
        },
    )
    assert state["journal_sequence"] == 1
    state["stage"] = "base_train"
    saved = journal.append_transition(
        state,
        event_type="base_train_started",
        idempotency_key="base-train-started",
    )
    duplicate = journal.append_transition(
        state,
        event_type="base_train_started",
        idempotency_key="base-train-started",
    )
    assert duplicate["journal_sequence"] == saved["journal_sequence"]
    assert len(list((tmp_path / "run" / "journal").glob("*.json"))) == 2

    journal.state_path.unlink()
    rebuilt = journal.load()
    assert rebuilt["stage"] == "base_train"
    assert rebuilt["state_sha256"] == saved["state_sha256"]

    journal.state_path.write_text('{"corrupt":true}\n', encoding="utf-8")
    assert journal.load()["journal_head_sha256"] == saved["journal_head_sha256"]

    _, artifact_hash = journal.write_artifact(
        "baseline-commitment.json",
        {"status": "committed"},
    )
    assert len(artifact_hash) == 64
    with pytest.raises(Exception, match="overwrite"):
        journal.write_artifact("baseline-commitment.json", {"status": "changed"})
    verification = journal.verify()
    assert verification["status"] == "passed"
    assert verification["journal_event_count"] == 2

    event = tmp_path / "run" / "journal" / "00000000000000000002.json"
    payload = json.loads(event.read_text(encoding="utf-8"))
    payload["event_type"] = "tampered"
    os.chmod(event, stat.S_IRUSR | stat.S_IWUSR)
    event.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(MeasuredStateError, match="event hash"):
        journal.verify()


def test_process_liveness_probe_never_calls_os_kill(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("os.kill must not be used by the measured liveness probe")

    monkeypatch.setattr(os, "kill", forbidden)
    assert _pid_is_alive(os.getpid()) is True


def test_exclusive_writer_contends_across_processes_and_crash_releases(
    tmp_path: Path,
) -> None:
    context = multiprocessing.get_context("spawn")
    ready = context.Event()
    process = context.Process(target=_hold_lease, args=(str(tmp_path / "run"), ready))
    process.start()
    assert ready.wait(10)
    with pytest.raises(MeasuredStateError, match="active writer"):
        with ExclusiveWriterLease(
            tmp_path / "run",
            run_id="run-1",
            request_sha256="a" * 64,
        ):
            pass
    process.terminate()
    process.join(10)
    assert not process.is_alive()
    with ExclusiveWriterLease(
        tmp_path / "run",
        run_id="run-1",
        request_sha256="a" * 64,
    ) as lease:
        lease.heartbeat()
    assert (tmp_path / "run" / "exclusive-writer.lock").is_file()
    assert json.loads((tmp_path / "run" / "lease.json").read_text(encoding="utf-8"))[
        "status"
    ] == "closed_cleanly"


def test_stale_pid_reuse_metadata_is_observational_only(tmp_path: Path) -> None:
    run_root = tmp_path / "run"
    run_root.mkdir()
    stale = {
        "schema_version": "myis.p2-exclusive-writer-lease.v2",
        "run_id": "run-1",
        "request_sha256": "a" * 64,
        "host": "recorded-host",
        "pid": os.getpid(),
        "process_creation_identity": "win:reused:identity",
        "lease_acquired_utc": "2026-01-01T00:00:00Z",
        "lease_heartbeat_utc": "2026-01-01T00:00:00Z",
        "status": "active",
        "lock_authority": "os_advisory_handle",
    }
    stale["lease_sha256"] = canonical_sha256(stale)
    (run_root / "lease.json").write_text(json.dumps(stale), encoding="utf-8")
    with ExclusiveWriterLease(
        run_root,
        run_id="run-1",
        request_sha256="a" * 64,
    ):
        pass
    archived = list((run_root / "lease-history").glob("prior-metadata-*.json"))
    assert len(archived) == 1
    assert json.loads(archived[0].read_text(encoding="utf-8"))["process_creation_identity"] == "win:reused:identity"


def test_resume_quarantines_partial_indexes_and_never_reruns_accepted_results(
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "run"
    journal = MeasuredRunJournal(run_root)
    state = journal.initialize(
        run_id="run-1",
        request=_request(),
        owner_paths={"index_root": str(run_root / "indexes")},
    )
    accepted = {"candidate_id": "accepted", "status": "train_complete"}
    _, accepted_hash = journal.write_artifact(
        "candidate-accepted-result.json",
        accepted,
    )
    state["candidates"] = {
        "accepted": {
            "candidate_id": "accepted",
            "status": "train_complete",
            "result_sha256": accepted_hash,
        }
    }
    state["accepted_result_ids"] = ["accepted"]
    journal.append_transition(
        state,
        event_type="candidate_accepted",
        idempotency_key="candidate-accepted",
    )
    partial = run_root / "indexes" / "partial-candidate"
    partial.mkdir(parents=True)
    (partial / "index.sqlite.tmp").write_bytes(b"partial")
    resumed = validate_resume_state(journal, request=_request())
    assert resumed["accepted_result_ids"] == ["accepted"]
    assert len(resumed["quarantined_partial_indexes"]) == 1
    assert not partial.exists()
    assert file_sha256(journal.artifact_root / "candidate-accepted-result.json") == accepted_hash


def test_global_selection_counter_has_exactly_one_process_winner(tmp_path: Path) -> None:
    context = multiprocessing.get_context("spawn")
    ready_one = context.Event()
    ready_two = context.Event()
    start = context.Event()
    queue = context.Queue()
    processes = [
        context.Process(
            target=_selection_writer,
            args=(str(tmp_path), "request-1", "f" * 64, ready_one, start, queue),
        ),
        context.Process(
            target=_selection_writer,
            args=(str(tmp_path), "request-2", "e" * 64, ready_two, start, queue),
        ),
    ]
    for process in processes:
        process.start()
    assert ready_one.wait(10)
    assert ready_two.wait(10)
    start.set()
    results = [queue.get(timeout=10), queue.get(timeout=10)]
    for process in processes:
        process.join(10)
        assert process.exitcode == 0
    assert [result[0] for result in results].count("ok") == 1
    assert [result[0] for result in results].count("error") == 1
    counter = json.loads(
        (tmp_path / "p2" / "global-selection-counter.json").read_text(encoding="utf-8")
    )
    assert counter["selection_exposure_count"] == 1
    assert (tmp_path / "p2" / "global-selection-counter.lock").is_file()


def test_resume_blocks_live_child_and_releases_stale_child_metadata(
    tmp_path: Path,
) -> None:
    live_journal = MeasuredRunJournal(tmp_path / "live")
    live_state = live_journal.initialize(
        run_id="run-live",
        request=_request(),
        owner_paths={"run_root": str(tmp_path / "live")},
    )
    identity = process_creation_identity(os.getpid())
    assert identity is not None
    live_state["active_child"] = {
        "pid": os.getpid(),
        "process_creation_identity": identity,
        "candidate_id": "candidate-live",
        "data_role": "train",
    }
    live_journal.append_transition(
        live_state,
        event_type="candidate_child_started",
        idempotency_key="live-child",
    )
    with pytest.raises(MeasuredStateError, match="candidate child is active"):
        validate_resume_state(live_journal, request=_request())

    stale_journal = MeasuredRunJournal(tmp_path / "stale")
    stale_state = stale_journal.initialize(
        run_id="run-stale",
        request=_request(),
        owner_paths={"run_root": str(tmp_path / "stale")},
    )
    stale_state["active_child"] = {
        "pid": os.getpid(),
        "process_creation_identity": "stale-process-identity",
        "candidate_id": "candidate-stale",
        "data_role": "train",
    }
    stale_journal.append_transition(
        stale_state,
        event_type="candidate_child_started",
        idempotency_key="stale-child",
    )
    resumed = validate_resume_state(stale_journal, request=_request())
    assert resumed["active_child"] is None


def test_resume_reconciles_owned_selection_counter_after_crash(tmp_path: Path) -> None:
    run_root = tmp_path / "run"
    owner_store = tmp_path / "store"
    journal = MeasuredRunJournal(run_root)
    state = journal.initialize(
        run_id="run-1",
        request=_request(),
        owner_paths={"run_root": str(run_root)},
    )
    state["shortlist_freeze_sha256"] = "f" * 64
    journal.append_transition(
        state,
        event_type="shortlist_frozen",
        idempotency_key="shortlist-frozen",
    )
    compare_and_swap_selection_counter(
        owner_store,
        request_id=state["request_id"],
        freeze_sha256="f" * 64,
    )
    resumed = validate_resume_state(
        journal,
        request=_request(),
        owner_store=owner_store,
    )
    assert resumed["selection_exposure_count"] == 1
    assert resumed["selection_counter_sha256"]


def test_immutable_write_failure_leaves_no_partial_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "artifact.json"

    def fail_link(_source: object, _target: object) -> None:
        raise OSError("synthetic link failure")

    monkeypatch.setattr(p2_contracts.os, "link", fail_link)
    with pytest.raises(OSError, match="synthetic link failure"):
        p2_contracts.write_immutable_json(target, {"status": "complete"})
    assert not target.exists()
    assert not list(tmp_path.glob(".artifact.json.*.tmp"))
