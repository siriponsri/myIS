"""Durable journal, advisory locks, and resume checks for measured P2."""

from __future__ import annotations

from contextlib import AbstractContextManager
from copy import deepcopy
from datetime import datetime, timezone
import ctypes
import json
import os
from pathlib import Path
import socket
import tempfile
import time
from typing import Any, Mapping

from ..kernel.canonical import canonical_json, canonical_sha256, file_sha256
from .contracts import P2ContractError, write_immutable_json


STATE_SCHEMA = "myis.p2-measured-state.v2"
EVENT_SCHEMA = "myis.p2-measured-event.v1"
LEASE_SCHEMA = "myis.p2-exclusive-writer-lease.v2"
SELECTION_COUNTER_SCHEMA = "myis.p2-global-selection-counter.v1"


class MeasuredStateError(P2ContractError):
    """Raised when durable measured state cannot advance safely."""


class AdvisoryFileLock(AbstractContextManager["AdvisoryFileLock"]):
    """Cross-platform nonblocking advisory lock held by an open file handle."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path).resolve()
        self.handle: Any | None = None

    def __enter__(self) -> "AdvisoryFileLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b", buffering=0)
        try:
            if self.path.stat().st_size == 0:
                handle.write(b"\0")
                handle.flush()
                os.fsync(handle.fileno())
            handle.seek(0)
            _lock_handle(handle)
        except BaseException:
            handle.close()
            raise
        self.handle = handle
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        handle = self.handle
        self.handle = None
        if handle is None:
            return
        try:
            _unlock_handle(handle)
        finally:
            handle.close()


class ExclusiveWriterLease(AbstractContextManager["ExclusiveWriterLease"]):
    """Single-writer lease whose authority is the held OS advisory lock."""

    def __init__(
        self,
        run_root: Path,
        *,
        run_id: str,
        request_sha256: str,
        recover_stale: bool = False,
        verifier_receipt: Path | None = None,
    ) -> None:
        self.run_root = Path(run_root).resolve()
        self.lock_path = self.run_root / "exclusive-writer.lock"
        self.path = self.run_root / "lease.json"
        self.run_id = run_id
        self.request_sha256 = request_sha256
        self.recover_stale = recover_stale
        self.verifier_receipt = Path(verifier_receipt).resolve() if verifier_receipt else None
        self.acquired = False
        self.payload: dict[str, Any] | None = None
        self._lock: AdvisoryFileLock | None = None

    def __enter__(self) -> "ExclusiveWriterLease":
        self.run_root.mkdir(parents=True, exist_ok=True)
        lock = AdvisoryFileLock(self.lock_path)
        try:
            lock.__enter__()
        except (OSError, BlockingIOError) as error:
            raise MeasuredStateError("measured run already has an active writer") from error
        self._lock = lock
        try:
            self._archive_prior_metadata()
            identity = process_creation_identity(os.getpid())
            if identity is None:
                raise MeasuredStateError("cannot establish measured worker process creation identity")
            now = _utc_now()
            payload = {
                "schema_version": LEASE_SCHEMA,
                "run_id": self.run_id,
                "request_sha256": self.request_sha256,
                "host": socket.gethostname(),
                "pid": os.getpid(),
                "process_creation_identity": identity,
                "lease_acquired_utc": now,
                "lease_heartbeat_utc": now,
                "status": "active",
                "lock_authority": "os_advisory_handle",
            }
            payload["lease_sha256"] = canonical_sha256(payload)
            atomic_write_json(self.path, payload)
            self.payload = payload
            self.acquired = True
            return self
        except BaseException:
            lock.__exit__(None, None, None)
            self._lock = None
            raise

    def heartbeat(self) -> None:
        if not self.acquired or self.payload is None or self._lock is None:
            raise MeasuredStateError("cannot heartbeat an inactive measured lease")
        identity = process_creation_identity(os.getpid())
        if identity != self.payload["process_creation_identity"]:
            raise MeasuredStateError("measured worker process identity changed")
        payload = {**self.payload, "lease_heartbeat_utc": _utc_now()}
        payload.pop("lease_sha256", None)
        payload["lease_sha256"] = canonical_sha256(payload)
        atomic_write_json(self.path, payload)
        self.payload = payload

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if not self.acquired:
            return
        try:
            if self.payload is None:
                raise MeasuredStateError("measured lease payload disappeared")
            payload = {
                **self.payload,
                "lease_heartbeat_utc": _utc_now(),
                "status": "closed_cleanly" if exc is None else "closed_after_failure",
                "closed_at_utc": _utc_now(),
            }
            payload.pop("lease_sha256", None)
            payload["lease_sha256"] = canonical_sha256(payload)
            atomic_write_json(self.path, payload)
            archive = self.run_root / "lease-history" / f"lease-{time.time_ns()}.json"
            write_immutable_json(archive, payload)
            self.payload = payload
        finally:
            self.acquired = False
            lock = self._lock
            self._lock = None
            if lock is not None:
                lock.__exit__(exc_type, exc, traceback)

    def _archive_prior_metadata(self) -> None:
        if not self.path.exists():
            return
        try:
            existing = _json_file(self.path)
        except MeasuredStateError:
            target = self.run_root / "lease-history" / f"malformed-metadata-{time.time_ns()}.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(self.path, target)
            return
        archive = self.run_root / "lease-history" / f"prior-metadata-{time.time_ns()}.json"
        write_immutable_json(archive, existing)


class MeasuredRunJournal:
    """Hash-chained event authority with a rebuildable state snapshot."""

    def __init__(self, run_root: Path) -> None:
        self.run_root = Path(run_root).resolve()
        self.state_path = self.run_root / "state.json"
        self.event_root = self.run_root / "journal"
        self.artifact_root = self.run_root / "artifacts"
        self.protected_root = self.run_root / "protected"

    def initialize(
        self,
        *,
        run_id: str,
        request: Mapping[str, Any],
        owner_paths: Mapping[str, str],
    ) -> dict[str, Any]:
        if self.event_root.exists() and any(self.event_root.glob("*.json")):
            raise MeasuredStateError("measured run journal already exists; use resume")
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        self.protected_root.mkdir(parents=True, exist_ok=True)
        request_payload = dict(request)
        request_payload.pop("_resolved", None)
        request_sha256 = canonical_sha256(request_payload)
        write_immutable_json(self.artifact_root / "request.json", request_payload)
        owner_binding = {
            "schema_version": "myis.p2-owner-path-binding.v1",
            "run_id": run_id,
            "request_sha256": request_sha256,
            "paths": dict(owner_paths),
            "created_at_utc": _utc_now(),
        }
        owner_binding["binding_sha256"] = canonical_sha256(owner_binding)
        write_immutable_json(self.run_root / "owner-paths.json", owner_binding)
        state = {
            "schema_version": STATE_SCHEMA,
            "run_id": run_id,
            "request_id": request_payload["request_id"],
            "request_sha256": request_sha256,
            "campaign_revision": request_payload["campaign_revision"],
            "budget_profile_id": request_payload["budget_profile_id"],
            "budget_profile_sha256": request_payload["budget_profile_sha256"],
            "execution_source_commit": request_payload["execution_source_commit"],
            "execution_source_tree": request_payload["execution_source_tree"],
            "stage": "initialized",
            "started_at_utc": _utc_now(),
            "base_registered": False,
            "baseline_commitment_sha256": None,
            "baseline_reproduction_sha256": None,
            "candidates": {},
            "adaptive_batches": [],
            "completed_iterations": [],
            "shortlist_freeze_sha256": None,
            "shortlist_ids": [],
            "selection_exposure_count": 0,
            "selection_receipt_sha256": None,
            "total_index_builds": 0,
            "total_runtime_seconds": 0.0,
            "accepted_result_ids": [],
            "quarantined_partial_indexes": [],
            "candidate_attempts": {},
            "used_adaptive_axes": [],
            "measurement_runtime_seconds": 0.0,
            "active_child": None,
            "generation_finished": False,
            "train_finished": False,
            "stop_after_checkpoint_requested": False,
            "failure": None,
        }
        return self.save(
            state,
            event_type="run_initialized",
            idempotency_key=f"run-initialized:{request_sha256}",
        )

    def load(self, *, repair_snapshot: bool = True) -> dict[str, Any]:
        state, events = self._rebuild()
        snapshot = self._snapshot_payload(state)
        current = _try_json_file(self.state_path)
        if repair_snapshot and current != snapshot:
            atomic_write_json(self.state_path, snapshot)
        if not events:
            raise MeasuredStateError("measured event journal is empty")
        return snapshot

    def save(
        self,
        state: Mapping[str, Any],
        *,
        event_type: str = "state_transition",
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        payload = self._event_state_payload(state)
        if idempotency_key is None:
            idempotency_key = f"state:{canonical_sha256(payload)}"
        event = self._append_event(
            event_type=event_type,
            idempotency_key=idempotency_key,
            payload={"state": payload},
        )
        rebuilt = self._state_from_event(event)
        snapshot = self._snapshot_payload(rebuilt)
        atomic_write_json(self.state_path, snapshot)
        return snapshot

    def append_transition(
        self,
        state: Mapping[str, Any],
        *,
        event_type: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        return self.save(state, event_type=event_type, idempotency_key=idempotency_key)

    def write_artifact(self, name: str, payload: Mapping[str, Any]) -> tuple[Path, str]:
        if not name or Path(name).name != name or not name.endswith(".json"):
            raise MeasuredStateError("measured artifact name must be one safe JSON filename")
        path = self.artifact_root / name
        write_immutable_json(path, payload)
        return path, file_sha256(path)

    def verify(self) -> dict[str, Any]:
        state, events = self._rebuild()
        artifacts: dict[str, str] = {}
        for path in sorted(self.artifact_root.glob("*.json")):
            if path.is_symlink() or not path.is_file():
                raise MeasuredStateError("measured artifact root contains an unsafe entry")
            artifacts[path.name] = file_sha256(path)
        snapshot = self._snapshot_payload(state)
        return {
            "schema_version": "myis.p2-owner-run-verification.v2",
            "run_id": snapshot["run_id"],
            "request_sha256": snapshot["request_sha256"],
            "stage": snapshot["stage"],
            "state_sha256": snapshot["state_sha256"],
            "journal_event_count": len(events),
            "journal_head_sha256": snapshot["journal_head_sha256"],
            "artifact_hashes": artifacts,
            "selection_exposure_count": snapshot["selection_exposure_count"],
            "status": "passed",
        }

    def quarantine_partial_indexes(self) -> list[str]:
        index_root = self.run_root / "indexes"
        if not index_root.is_dir():
            return []
        quarantined: list[str] = []
        quarantine_root = self.run_root / "quarantine" / "indexes"
        for path in sorted(index_root.iterdir(), key=lambda item: item.name):
            if path.is_symlink() or not path.is_dir():
                raise MeasuredStateError("measured index root contains an unsafe entry")
            if (path / "COMPLETE.json").is_file():
                continue
            quarantine_root.mkdir(parents=True, exist_ok=True)
            target = quarantine_root / f"{path.name}-{time.time_ns()}"
            os.replace(path, target)
            quarantined.append(target.relative_to(self.run_root).as_posix())
        return quarantined

    def _append_event(
        self,
        *,
        event_type: str,
        idempotency_key: str,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not event_type or not idempotency_key:
            raise MeasuredStateError("journal events require type and idempotency key")
        events = self._load_events()
        for existing in events:
            if existing["idempotency_key"] != idempotency_key:
                continue
            comparable = {
                "event_type": event_type,
                "idempotency_key": idempotency_key,
                "payload": dict(payload),
            }
            observed = {
                "event_type": existing["event_type"],
                "idempotency_key": existing["idempotency_key"],
                "payload": existing["payload"],
            }
            if _idempotency_comparable(comparable) != _idempotency_comparable(observed):
                raise MeasuredStateError("journal idempotency key was reused for a different transition")
            return existing
        sequence = len(events) + 1
        previous = events[-1]["event_sha256"] if events else None
        event = {
            "schema_version": EVENT_SCHEMA,
            "event_id": f"EV{sequence:08d}",
            "sequence": sequence,
            "previous_event_sha256": previous,
            "event_type": event_type,
            "idempotency_key": idempotency_key,
            "payload": dict(payload),
            "recorded_at_utc": _utc_now(),
        }
        event["event_sha256"] = canonical_sha256(event)
        path = self.event_root / f"{sequence:020d}.json"
        write_immutable_json(path, event)
        return event

    def _load_events(self) -> list[dict[str, Any]]:
        if not self.event_root.exists():
            return []
        paths = sorted(self.event_root.glob("*.json"), key=lambda item: item.name)
        events: list[dict[str, Any]] = []
        previous: str | None = None
        idempotency_keys: set[str] = set()
        for expected, path in enumerate(paths, start=1):
            if path.is_symlink() or not path.is_file():
                raise MeasuredStateError("measured journal contains an unsafe entry")
            event = _json_file(path)
            recorded_hash = str(event.get("event_sha256", ""))
            unsigned = {key: value for key, value in event.items() if key != "event_sha256"}
            if event.get("schema_version") != EVENT_SCHEMA:
                raise MeasuredStateError("measured journal event schema is invalid")
            if event.get("sequence") != expected or path.name != f"{expected:020d}.json":
                raise MeasuredStateError("measured journal sequence is not contiguous")
            if event.get("previous_event_sha256") != previous:
                raise MeasuredStateError("measured journal previous hash is invalid")
            if recorded_hash != canonical_sha256(unsigned):
                raise MeasuredStateError("measured journal event hash is invalid")
            key = str(event.get("idempotency_key", ""))
            if not key or key in idempotency_keys:
                raise MeasuredStateError("measured journal idempotency keys must be unique")
            idempotency_keys.add(key)
            events.append(event)
            previous = recorded_hash
        return events

    def _rebuild(self) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        events = self._load_events()
        if not events:
            raise MeasuredStateError("measured event journal is missing")
        state: dict[str, Any] | None = None
        for event in events:
            candidate = event.get("payload", {}).get("state")
            if not isinstance(candidate, dict):
                raise MeasuredStateError("measured journal transition is missing state")
            state = deepcopy(candidate)
            state["journal_sequence"] = event["sequence"]
            state["journal_head_sha256"] = event["event_sha256"]
        if state is None or state.get("schema_version") != STATE_SCHEMA:
            raise MeasuredStateError("measured journal did not rebuild a valid state")
        return state, events

    def _state_from_event(self, event: Mapping[str, Any]) -> dict[str, Any]:
        state = deepcopy(dict(event["payload"]["state"]))
        state["journal_sequence"] = event["sequence"]
        state["journal_head_sha256"] = event["event_sha256"]
        return state

    @staticmethod
    def _event_state_payload(state: Mapping[str, Any]) -> dict[str, Any]:
        payload = deepcopy(dict(state))
        for key in ("state_sha256", "journal_sequence", "journal_head_sha256"):
            payload.pop(key, None)
        payload["schema_version"] = STATE_SCHEMA
        payload["updated_at_utc"] = _utc_now()
        return payload

    @staticmethod
    def _snapshot_payload(state: Mapping[str, Any]) -> dict[str, Any]:
        payload = deepcopy(dict(state))
        payload.pop("state_sha256", None)
        payload["state_sha256"] = canonical_sha256(payload)
        return payload


def compare_and_swap_selection_counter(
    owner_store: Path,
    *,
    request_id: str,
    freeze_sha256: str,
) -> dict[str, Any]:
    root = Path(owner_store).resolve()
    counter_path = root / "p2" / "global-selection-counter.json"
    lock_path = root / "p2" / "global-selection-counter.lock"
    counter_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        lock = AdvisoryFileLock(lock_path)
        lock.__enter__()
    except (OSError, BlockingIOError) as error:
        raise MeasuredStateError("global selection counter is locked by another writer") from error
    try:
        if counter_path.exists():
            current = _json_file(counter_path)
            if current.get("schema_version") != SELECTION_COUNTER_SCHEMA:
                raise MeasuredStateError("global selection counter is malformed")
            count = int(current.get("selection_exposure_count", -1))
        else:
            count = 0
        if count != 0:
            raise MeasuredStateError("global selection exposure was already consumed")
        updated = {
            "schema_version": SELECTION_COUNTER_SCHEMA,
            "selection_exposure_count": 1,
            "request_id": request_id,
            "shortlist_freeze_sha256": freeze_sha256,
            "advanced_at_utc": _utc_now(),
        }
        updated["counter_sha256"] = canonical_sha256(updated)
        atomic_write_json(counter_path, updated)
        return updated
    finally:
        lock.__exit__(None, None, None)


def validate_resume_state(
    journal: MeasuredRunJournal,
    *,
    request: Mapping[str, Any],
    owner_store: Path | None = None,
) -> dict[str, Any]:
    state = journal.load()
    terminal_stage = str(state.get("stage", ""))
    if terminal_stage in {
        "blocked_scientific",
        "blocked_infrastructure",
        "blocked_budget",
    }:
        raise MeasuredStateError(
            f"measured run is terminal after {terminal_stage}; resume is forbidden"
        )
    request_payload = dict(request)
    request_payload.pop("_resolved", None)
    request_sha256 = canonical_sha256(request_payload)
    if state["request_sha256"] != request_sha256:
        raise MeasuredStateError("resume request hash differs from the journal")
    for field in (
        "campaign_revision",
        "budget_profile_id",
        "budget_profile_sha256",
        "execution_source_commit",
        "execution_source_tree",
    ):
        if state.get(field) != request_payload.get(field):
            raise MeasuredStateError(f"resume request field is stale: {field}")
    accepted = list(state.get("accepted_result_ids", []))
    if len(accepted) != len(set(accepted)):
        raise MeasuredStateError("accepted result IDs are not unique")
    candidates = state.get("candidates", {})
    if not isinstance(candidates, dict):
        raise MeasuredStateError("resume candidate snapshot is malformed")
    for candidate_id in accepted:
        row = candidates.get(candidate_id)
        if not isinstance(row, dict) or row.get("status") not in {"train_complete", "frozen", "selected"}:
            raise MeasuredStateError("accepted result is missing from the candidate snapshot")
        artifact = journal.artifact_root / f"candidate-{candidate_id}-result.json"
        expected_hash = row.get("result_sha256")
        if not artifact.is_file() or not expected_hash or file_sha256(artifact) != expected_hash:
            raise MeasuredStateError("accepted candidate result artifact is missing or stale")
    active_child = state.get("active_child")
    if isinstance(active_child, Mapping):
        pid = int(active_child.get("pid", -1))
        recorded_identity = str(active_child.get("process_creation_identity", ""))
        current_identity = process_creation_identity(pid)
        if current_identity is not None and current_identity == recorded_identity:
            raise MeasuredStateError("resume blocked while the recorded candidate child is active")
        updated = deepcopy(state)
        updated["active_child"] = None
        state = journal.append_transition(
            updated,
            event_type="orphan_candidate_child_released",
            idempotency_key=f"orphan-child-released:{pid}:{recorded_identity}",
        )
    quarantined = journal.quarantine_partial_indexes()
    if quarantined:
        updated = deepcopy(state)
        updated["quarantined_partial_indexes"] = [
            *list(updated.get("quarantined_partial_indexes", [])),
            *quarantined,
        ]
        state = journal.append_transition(
            updated,
            event_type="partial_indexes_quarantined",
            idempotency_key=f"quarantine:{canonical_sha256(quarantined)}",
        )
    if owner_store is not None:
        counter_path = Path(owner_store).resolve() / "p2" / "global-selection-counter.json"
        counter = _json_file(counter_path) if counter_path.is_file() else None
        exposure = int(state.get("selection_exposure_count", 0))
        if exposure == 0 and counter is not None:
            if (
                counter.get("request_id") != state["request_id"]
                or counter.get("shortlist_freeze_sha256")
                != state.get("shortlist_freeze_sha256")
            ):
                raise MeasuredStateError("global selection counter advanced beyond the run journal")
            recorded_counter_hash = str(counter.get("counter_sha256", ""))
            unsigned_counter = {
                key: value for key, value in counter.items() if key != "counter_sha256"
            }
            if recorded_counter_hash != canonical_sha256(unsigned_counter):
                raise MeasuredStateError("global selection counter hash is invalid")
            updated = deepcopy(state)
            updated["selection_exposure_count"] = 1
            updated["selection_counter_sha256"] = recorded_counter_hash
            state = journal.append_transition(
                updated,
                event_type="selection_counter_reconciled",
                idempotency_key=f"selection-counter-reconciled:{recorded_counter_hash}",
            )
        if exposure == 1:
            if counter is None or counter.get("request_id") != state["request_id"]:
                raise MeasuredStateError("run selection exposure is not bound by the global counter")
            if counter.get("shortlist_freeze_sha256") != state.get("shortlist_freeze_sha256"):
                raise MeasuredStateError("global selection counter freeze hash differs from the run")
    return state


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = (canonical_json(dict(payload)) + "\n").encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=target.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        _replace_with_retry(temporary, target)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def process_creation_identity(pid: int) -> str | None:
    if pid <= 0:
        return None
    if os.name == "nt":
        return _windows_process_creation_identity(pid)
    proc_stat = Path("/proc") / str(pid) / "stat"
    try:
        fields = proc_stat.read_text(encoding="ascii").split()
        start_ticks = fields[21]
        boot_id = (Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip())
        return f"posix:{pid}:{boot_id}:{start_ticks}"
    except (OSError, IndexError):
        return None


def _pid_is_alive(pid: int) -> bool:
    """Compatibility probe that never sends a signal on Windows."""

    return process_creation_identity(pid) is not None


def _windows_process_creation_identity(pid: int) -> str | None:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    process_query_limited_information = 0x1000
    still_active = 259
    kernel32.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    kernel32.GetExitCodeProcess.restype = ctypes.c_int
    kernel32.GetProcessTimes.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    kernel32.GetProcessTimes.restype = ctypes.c_int
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
    if not handle:
        return None
    try:
        exit_code = ctypes.c_ulong()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return None
        if exit_code.value != still_active:
            return None
        creation = ctypes.c_ulonglong()
        exit_time = ctypes.c_ulonglong()
        kernel = ctypes.c_ulonglong()
        user = ctypes.c_ulonglong()
        if not kernel32.GetProcessTimes(
            handle,
            ctypes.byref(creation),
            ctypes.byref(exit_time),
            ctypes.byref(kernel),
            ctypes.byref(user),
        ):
            return None
        return f"win:{pid}:{creation.value}"
    finally:
        kernel32.CloseHandle(handle)


def _lock_handle(handle: Any) -> None:
    if os.name == "nt":
        import msvcrt

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        return
    import fcntl

    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock_handle(handle: Any) -> None:
    if os.name == "nt":
        import msvcrt

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _try_json_file(path: Path) -> dict[str, Any] | None:
    if not Path(path).is_file() or Path(path).is_symlink():
        return None
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict):
        return None
    recorded = str(value.get("state_sha256", ""))
    unsigned = {key: item for key, item in value.items() if key != "state_sha256"}
    if recorded != canonical_sha256(unsigned):
        return None
    return value


def _replace_with_retry(source: Path, target: Path) -> None:
    attempts = 50 if os.name == "nt" else 1
    for attempt in range(attempts):
        try:
            os.replace(source, target)
            return
        except PermissionError:
            if attempt + 1 >= attempts:
                raise
            time.sleep(0.01)


def _idempotency_comparable(value: Mapping[str, Any]) -> dict[str, Any]:
    payload = deepcopy(dict(value))
    state = payload.get("payload", {}).get("state")
    if isinstance(state, dict):
        state.pop("updated_at_utc", None)
    return payload


def _json_file(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MeasuredStateError(f"cannot read measured JSON state: {path}") from error
    if not isinstance(value, dict):
        raise MeasuredStateError(f"measured JSON state must be an object: {path}")
    return value


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
