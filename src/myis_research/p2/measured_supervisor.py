"""Detached supervisor and checkpoint control for measured P2."""

from __future__ import annotations

from contextlib import AbstractContextManager
from copy import deepcopy
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Callable, Mapping

from ..kernel.canonical import canonical_sha256
from .contracts import write_immutable_json
from .measured_contracts import load_measured_request
from .measured_executor import run_measured_execution
from .measured_state import (
    ExclusiveWriterLease,
    MeasuredRunJournal,
    MeasuredStateError,
    atomic_write_json,
    process_creation_identity,
    validate_resume_state,
)
from .runtime_environment import sanitized_runtime_environment


STARTUP_TIMEOUT_SECONDS = 30.0
STOP_REQUEST_SCHEMA = "myis.p2-stop-after-checkpoint-request.v1"


class WindowsPreventSleep(AbstractContextManager["WindowsPreventSleep"]):
    """Keep the Windows system awake while the measured worker owns the lease."""

    def __init__(self) -> None:
        self.active = False

    def __enter__(self) -> "WindowsPreventSleep":
        if os.name != "nt":
            self.active = True
            return self
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.SetThreadExecutionState.argtypes = [ctypes.c_ulong]
        kernel32.SetThreadExecutionState.restype = ctypes.c_ulong
        es_continuous = 0x80000000
        es_system_required = 0x00000001
        es_awaymode_required = 0x00000040
        result = kernel32.SetThreadExecutionState(
            es_continuous | es_system_required | es_awaymode_required
        )
        if result == 0:
            raise MeasuredStateError("Windows prevent-sleep request failed")
        self.active = True
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if not self.active or os.name != "nt":
            self.active = False
            return
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.SetThreadExecutionState(0x80000000)
        self.active = False


def start_detached_worker(
    *,
    request_path: Path,
    run_root: Path,
    repository_root: Path,
    mode: str,
    owner_store: Path | None = None,
    cache_root: Path | None = None,
    synthetic_checkpoints: int = 0,
    checkpoint_delay_seconds: float = 0.05,
    startup_timeout_seconds: float = STARTUP_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    owner_run_root = Path(run_root).resolve()
    _require_owner_local_run_root(owner_run_root, root)
    if not synthetic_checkpoints and (owner_store is None or cache_root is None):
        raise MeasuredStateError(
            "measured start/resume requires explicit --owner-store and --cache-root"
        )
    request = load_measured_request(request_path, root, require_current_git=True)
    request_payload = dict(request)
    request_payload.pop("_resolved", None)
    request_sha256 = canonical_sha256(request_payload)
    owner_run_root.mkdir(parents=True, exist_ok=True)
    log_root = owner_run_root / "logs"
    log_root.mkdir(parents=True, exist_ok=True)
    stdout_path = log_root / "worker.stdout.log"
    stderr_path = log_root / "worker.stderr.log"
    startup_path = owner_run_root / "startup.json"
    startup_path.unlink(missing_ok=True)
    command = [
        sys.executable,
        "-m",
        "myis_research.p2_measured_cli",
        "worker",
        "--request",
        str(Path(request_path).resolve()),
        "--run-root",
        str(owner_run_root),
        "--repository-root",
        str(root),
        "--mode",
        mode,
        "--synthetic-checkpoints",
        str(synthetic_checkpoints),
        "--checkpoint-delay-seconds",
        str(checkpoint_delay_seconds),
    ]
    if owner_store is not None:
        command.extend(["--owner-store", str(Path(owner_store).resolve())])
    if cache_root is not None:
        command.extend(["--cache-root", str(Path(cache_root).resolve())])
    creation_flags = 0
    start_new_session = False
    if os.name == "nt":
        creation_flags = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
    else:
        start_new_session = True
    child_environment = sanitized_runtime_environment()
    # The worker may be launched against a repository fixture that does not
    # contain an installed package. Bootstrap only this package's source root;
    # do not inherit arbitrary parent PYTHONPATH entries.
    package_source_root = Path(__file__).resolve().parents[2]
    child_environment["PYTHONPATH"] = str(package_source_root)
    with stdout_path.open("ab", buffering=0) as stdout_handle, stderr_path.open(
        "ab", buffering=0
    ) as stderr_handle:
        process = subprocess.Popen(
            command,
            cwd=root,
            env=child_environment,
            stdin=subprocess.DEVNULL,
            stdout=stdout_handle,
            stderr=stderr_handle,
            close_fds=True,
            creationflags=creation_flags,
            start_new_session=start_new_session,
        )
    deadline = time.monotonic() + startup_timeout_seconds
    while time.monotonic() < deadline:
        if startup_path.is_file():
            startup = _json_file(startup_path)
            if (
                startup.get("request_sha256") == request_sha256
                and startup.get("status") == "started"
                and isinstance(startup.get("worker_pid"), int)
                and startup.get("process_creation_identity")
            ):
                return startup
        return_code = process.poll()
        if return_code is not None:
            raise MeasuredStateError(
                f"detached measured worker exited before startup receipt: {return_code}"
            )
        time.sleep(0.05)
    raise MeasuredStateError("detached measured worker did not write a startup receipt")


def run_worker(
    *,
    request_path: Path,
    run_root: Path,
    repository_root: Path,
    mode: str,
    owner_store: Path | None = None,
    cache_root: Path | None = None,
    synthetic_checkpoints: int = 0,
    checkpoint_delay_seconds: float = 0.05,
    checkpoint_hook: Callable[[int], None] | None = None,
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    owner_run_root = Path(run_root).resolve()
    _require_owner_local_run_root(owner_run_root, root)
    if not synthetic_checkpoints and (owner_store is None or cache_root is None):
        raise MeasuredStateError(
            "measured worker requires explicit owner store and cache roots"
        )
    request = load_measured_request(request_path, root, require_current_git=True)
    request_payload = dict(request)
    request_payload.pop("_resolved", None)
    request_sha256 = canonical_sha256(request_payload)
    journal = MeasuredRunJournal(owner_run_root)
    with ExclusiveWriterLease(
        owner_run_root,
        run_id=request_payload["request_id"],
        request_sha256=request_sha256,
    ) as lease, WindowsPreventSleep():
        if mode == "start":
            state = journal.initialize(
                run_id=request_payload["request_id"],
                request=request,
                owner_paths={
                    "run_root": str(owner_run_root),
                    "request_path": str(Path(request_path).resolve()),
                    **(
                        {"owner_store": str(Path(owner_store).resolve())}
                        if owner_store is not None
                        else {}
                    ),
                },
            )
        elif mode == "resume":
            state = validate_resume_state(
                journal,
                request=request,
                owner_store=owner_store,
            )
            if state.get("stage") == "stopped_after_checkpoint":
                state = deepcopy(state)
                state["stop_after_checkpoint_requested"] = False
                state["stop_reason"] = None
                state = journal.append_transition(
                    state,
                    event_type="resumed_after_owner_checkpoint_stop",
                    idempotency_key=f"resume-after-stop:{state['journal_head_sha256']}",
                )
        else:
            raise MeasuredStateError(f"unsupported measured worker mode: {mode}")
        startup = {
            "schema_version": "myis.p2-worker-startup.v1",
            "request_id": request_payload["request_id"],
            "request_sha256": request_sha256,
            "worker_pid": os.getpid(),
            "process_creation_identity": process_creation_identity(os.getpid()),
            "mode": mode,
            "status": "started",
            "started_at_utc": _utc_now(),
        }
        startup["startup_sha256"] = canonical_sha256(startup)
        receipt_path = owner_run_root / "startup-receipts" / f"startup-{time.time_ns()}.json"
        write_immutable_json(receipt_path, startup)
        atomic_write_json(owner_run_root / "startup.json", startup)
        state = deepcopy(state)
        state["stage"] = "supervisor_ready"
        state = journal.append_transition(
            state,
            event_type="supervisor_started",
            idempotency_key=f"supervisor-started:{startup['startup_sha256']}",
        )
        completed_synthetic = int(state.get("synthetic_checkpoint", 0))
        for checkpoint in range(
            completed_synthetic + 1, synthetic_checkpoints + 1
        ):
            if checkpoint_hook is not None:
                checkpoint_hook(checkpoint)
            time.sleep(max(0.0, checkpoint_delay_seconds))
            lease.heartbeat()
            state = deepcopy(state)
            state["stage"] = "synthetic_checkpoint"
            state["synthetic_checkpoint"] = checkpoint
            state = journal.append_transition(
                state,
                event_type="synthetic_checkpoint",
                idempotency_key=f"synthetic-checkpoint:{checkpoint}",
            )
            if _stop_requested(owner_run_root):
                state = _acknowledge_stop(journal, state)
                return state
        if synthetic_checkpoints:
            state = deepcopy(state)
            state["stage"] = "synthetic_complete"
            return journal.append_transition(
                state,
                event_type="synthetic_run_completed",
                idempotency_key="synthetic-run-completed",
            )
        if owner_store is None or cache_root is None:
            raise MeasuredStateError(
                "measured execution requires explicit --owner-store and --cache-root"
            )
        completed = run_measured_execution(
            request=request,
            request_path=Path(request_path).resolve(),
            repository_root=root,
            run_root=owner_run_root,
            cache_root=Path(cache_root).resolve(),
            owner_store=Path(owner_store).resolve(),
            journal=journal,
            state=state,
            heartbeat=lease.heartbeat,
            stop_requested=lambda: _stop_requested(owner_run_root),
        )
        if completed.get("stage") == "stopped_after_checkpoint":
            _mark_stop_request_acknowledged(owner_run_root)
        return completed


def status(run_root: Path) -> dict[str, Any]:
    owner_run_root = Path(run_root).resolve()
    journal = MeasuredRunJournal(owner_run_root)
    state = journal.load(repair_snapshot=False)
    lease = _json_file(owner_run_root / "lease.json") if (owner_run_root / "lease.json").is_file() else None
    return {
        "schema_version": "myis.p2-measured-status.v1",
        "run_id": state["run_id"],
        "stage": state["stage"],
        "journal_sequence": state["journal_sequence"],
        "journal_head_sha256": state["journal_head_sha256"],
        "candidate_count": len(state.get("candidates", {})),
        "shortlist_count": len(state.get("shortlist_ids", [])),
        "selection_exposure_count": state.get("selection_exposure_count", 0),
        "lease_status": lease.get("status") if lease else "absent",
        "lease_heartbeat_utc": lease.get("lease_heartbeat_utc") if lease else None,
        "scientific_authority": False,
    }


def request_stop_after_checkpoint(run_root: Path, *, reason: str = "owner_request") -> dict[str, Any]:
    owner_run_root = Path(run_root).resolve()
    request = {
        "schema_version": STOP_REQUEST_SCHEMA,
        "reason": reason,
        "requested_at_utc": _utc_now(),
        "status": "pending_checkpoint",
    }
    request["request_sha256"] = canonical_sha256(request)
    atomic_write_json(owner_run_root / "control" / "stop-after-checkpoint.json", request)
    return request


def verify_run(
    *,
    run_root: Path,
    request_path: Path | None = None,
    repository_root: Path | None = None,
    owner_store: Path | None = None,
) -> dict[str, Any]:
    journal = MeasuredRunJournal(Path(run_root).resolve())
    verification = journal.verify()
    if request_path is not None and repository_root is not None:
        request = load_measured_request(
            request_path,
            Path(repository_root).resolve(),
            require_current_git=True,
        )
        validate_resume_state(journal, request=request, owner_store=owner_store)
    return verification


def _acknowledge_stop(
    journal: MeasuredRunJournal,
    state: Mapping[str, Any],
) -> dict[str, Any]:
    updated = deepcopy(dict(state))
    updated["stage"] = "stopped_after_checkpoint"
    updated["stop_after_checkpoint_requested"] = True
    updated["stop_reason"] = "owner_stop_after_checkpoint"
    result = journal.append_transition(
        updated,
        event_type="stop_after_checkpoint_acknowledged",
        idempotency_key="stop-after-checkpoint-acknowledged",
    )
    _mark_stop_request_acknowledged(journal.run_root)
    return result


def _stop_requested(run_root: Path) -> bool:
    path = Path(run_root) / "control" / "stop-after-checkpoint.json"
    if not path.is_file() or path.is_symlink():
        return False
    request = _json_file(path)
    recorded = str(request.get("request_sha256", ""))
    unsigned = {key: value for key, value in request.items() if key != "request_sha256"}
    if request.get("schema_version") != STOP_REQUEST_SCHEMA:
        raise MeasuredStateError("stop-after-checkpoint request schema is invalid")
    if recorded != canonical_sha256(unsigned):
        raise MeasuredStateError("stop-after-checkpoint request hash is invalid")
    return request.get("status") == "pending_checkpoint"


def _mark_stop_request_acknowledged(run_root: Path) -> None:
    path = Path(run_root) / "control" / "stop-after-checkpoint.json"
    if not path.is_file() or path.is_symlink():
        return
    request = _json_file(path)
    request["status"] = "acknowledged"
    request["acknowledged_at_utc"] = _utc_now()
    request.pop("request_sha256", None)
    request["request_sha256"] = canonical_sha256(request)
    atomic_write_json(path, request)


def _require_owner_local_run_root(run_root: Path, repository_root: Path) -> None:
    try:
        run_root.relative_to(repository_root)
    except ValueError:
        return
    raise MeasuredStateError("measured run root must remain outside the Git worktree")


def _json_file(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MeasuredStateError(f"cannot read measured supervisor JSON: {path}") from error
    if not isinstance(value, dict):
        raise MeasuredStateError(f"measured supervisor JSON must be an object: {path}")
    return value


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
