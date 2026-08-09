"""Additive A1.2 v16 attempt-scoped execution lifecycle.

This module is deliberately scientific-policy neutral.  It cannot choose a
program, alter a model, evaluate quality, or contact a provider.  It supplies
the durable execution boundary used by the separately hash-bound measured
executor: admission gates, a restricted child environment, process identity,
checkpoints, fail-closed completeness, and aggregate-safe return packaging.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import re
import subprocess
import tarfile
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..kernel.canonical import canonical_sha256, file_sha256

REVISION_ID = "a1.2-execution-lifecycle-v16"
ARMS = ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")
PROGRAMS = ("P00-TAC-DOC", "P01-TA-DOC", "P02-CLAIM1", "P03-PASSAGE", "P04-SECTION-MULTIVIEW")
EXECUTOR_PROGRAM_IDS = {"P02-CLAIM1": "P02-FIRST-CLAIM"}
REQUIRED_GATES = frozenset({"provider_admission", "execution_adoption", "watchdog_ttl", "protected_boundary", "frozen_bindings"})
ATTEMPT_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
CELL_RE = re.compile(r"^ARM-0[1-5]--P0[0-4]-(?:TAC-DOC|TA-DOC|CLAIM1|PASSAGE|SECTION-MULTIVIEW)$")
FORBIDDEN_PATH = re.compile(r"(?:qrels|membership|query[_-]?ids?|credential|secret|token|embedding|raw[_-]?input|environment|provider[_-]?payload|id_rsa|id_ed25519|protected)", re.IGNORECASE)
FORBIDDEN_KEY = re.compile(r"(?:qrels|membership|query[_-]?ids?|credential|secret|token|embedding|raw[_-]?input|environment|provider[_-]?payload|protected)", re.IGNORECASE)
SAFE_AGGREGATE_KEYS = frozenset({"work_token_count"})
FORCED_ENV = {
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "PIP_NO_INDEX": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "TOKENIZERS_PARALLELISM": "false",
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "TZ": "UTC",
}
ALLOWED_ENV_NAMES = frozenset({
    "CUDA_VISIBLE_DEVICES", "HF_HUB_OFFLINE", "LANG", "LC_ALL", "PATH",
    "PIP_NO_INDEX", "PYTHONDONTWRITEBYTECODE", "PYTHONHASHSEED", "TZ",
    "TRANSFORMERS_OFFLINE", "TOKENIZERS_PARALLELISM",
})


class ExecutionLifecycleV16Error(RuntimeError):
    """Raised when the governed lifecycle cannot establish a safe transition."""


def required_cells() -> tuple[str, ...]:
    return tuple(f"{arm}--{program}" for arm in ARMS for program in PROGRAMS)


def validate_executor_interface() -> dict[str, str]:
    """Bind to the v16 executor's deliberately narrow in-memory callback API.

    The executor is never asked to own state, export bytes, evaluate results,
    or decide a gate.  The caller must record ``source_sha256`` in the attempt
    identity before it may invoke this callback against Owner-local inputs.
    """

    from . import a1_2_measured_executor_v16 as executor

    callback = getattr(executor, "execute_program_cell", None)
    if callback is None or not callable(callback):
        raise ExecutionLifecycleV16Error("v16 executor callback is unavailable")
    parameters = tuple(inspect.signature(callback).parameters)
    if parameters != ("arm_id", "program_id", "corpus", "query", "adapter"):
        raise ExecutionLifecycleV16Error("v16 executor callback signature drifted")
    source = Path(executor.__file__ or "")
    if not source.is_file():
        raise ExecutionLifecycleV16Error("v16 executor source binding is unavailable")
    return {"callback": "execute_program_cell", "source_sha256": file_sha256(source)}


def executor_program_id(program_id: str) -> str:
    """Translate only the additive executable label; lifecycle IDs stay v11."""

    if program_id not in PROGRAMS:
        raise ExecutionLifecycleV16Error("program is outside the frozen v11 common set")
    return EXECUTOR_PROGRAM_IDS.get(program_id, program_id)


def invoke_executor_cell(executor: Any, *, arm_id: str, program_id: str, corpus: Any, query: Any, adapter: Any = None) -> Any:
    """Call the separately hash-bound executor with the explicit v11 bridge."""

    validate_executor_interface()
    if arm_id not in ARMS:
        raise ExecutionLifecycleV16Error("arm is outside the frozen v11 common set")
    return executor(arm_id=arm_id, program_id=executor_program_id(program_id), corpus=corpus, query=query, adapter=adapter)


def run_program_cells(
    output_root: Path,
    attempt_id: str,
    executor: Any,
    cell_inputs: Mapping[str, Mapping[str, Any]],
    receipt_writer: Any,
) -> dict[str, tuple[str, ...]]:
    """Resume and execute pending cells through an explicit executor callback.

    ``receipt_writer`` is the only serialization hook.  It must write one
    aggregate-safe, self-hashed JSON receipt under ``attempt/results``; this
    function never evaluates ranks or copies protected input into a receipt.
    """

    plan = resume_plan(output_root, attempt_id)
    attempt = _attempt(_attempt_dir(output_root, attempt_id), attempt_id)
    if attempt.get("execution_mode") != "production":
        raise ExecutionLifecycleV16Error("executor callbacks are unavailable in synthetic mode")
    pending = plan["pending"]
    if set(cell_inputs) != set(pending):
        raise ExecutionLifecycleV16Error("cell input set must exactly equal the pending frozen cells")
    for cell_id in pending:
        arm_id, program_id = cell_id.split("--", 1)
        values = dict(cell_inputs[cell_id])
        if set(values) - {"corpus", "query", "adapter"} or "corpus" not in values or "query" not in values:
            raise ExecutionLifecycleV16Error("cell input must provide only corpus, query, and optional adapter")
        result = invoke_executor_cell(executor, arm_id=arm_id, program_id=program_id, **values)
        receipt_path = receipt_writer(cell_id, result)
        if not isinstance(receipt_path, Path):
            raise ExecutionLifecycleV16Error("receipt_writer must return a Path")
        record_cell_checkpoint(output_root, attempt_id, cell_id, receipt_path)
    return resume_plan(output_root, attempt_id)


def _utc() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _atomic(path: Path, value: Mapping[str, Any], *, immutable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = _text(value)
    if path.exists():
        if immutable and path.read_text(encoding="utf-8") != text:
            raise ExecutionLifecycleV16Error(f"immutable lifecycle record differs: {path.name}")
        if immutable:
            return
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("x", encoding="utf-8", newline="") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _load_checked(path: Path, field: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ExecutionLifecycleV16Error(f"invalid lifecycle record: {path}") from error
    if not isinstance(value, dict):
        raise ExecutionLifecycleV16Error(f"lifecycle record must be an object: {path}")
    body = dict(value)
    if body.pop(field, None) != canonical_sha256(body):
        raise ExecutionLifecycleV16Error(f"lifecycle self-hash mismatch: {path.name}")
    return value


def _attempt_dir(output_root: Path, attempt_id: str) -> Path:
    if not ATTEMPT_RE.fullmatch(attempt_id):
        raise ExecutionLifecycleV16Error("attempt_id is invalid")
    root = output_root.resolve()
    directory = (root / "attempts" / attempt_id).resolve()
    try:
        directory.relative_to(root)
    except ValueError as error:
        raise ExecutionLifecycleV16Error("attempt path escapes output root") from error
    return directory


def _attempt(directory: Path, attempt_id: str) -> dict[str, Any]:
    value = _load_checked(directory / "attempt.json", "attempt_sha256")
    if value.get("attempt_id") != attempt_id:
        raise ExecutionLifecycleV16Error("attempt identity mismatch")
    return value


def _state(directory: Path, attempt_id: str) -> dict[str, Any]:
    value = _load_checked(directory / "state.json", "state_sha256")
    if value.get("attempt_id") != attempt_id or value.get("status") not in {"RUNNING", "FAILED", "COMPLETE"}:
        raise ExecutionLifecycleV16Error("attempt state mismatch")
    return value


def explicit_environment(values: Mapping[str, str] | None = None, *, cuda_visible_devices: str | None = None) -> dict[str, str]:
    """Return a child environment from an explicit small allowlist only."""

    supplied = values or {}
    unknown = set(supplied) - ALLOWED_ENV_NAMES
    if unknown:
        raise ExecutionLifecycleV16Error("environment contains a forbidden name")
    if any(name in FORCED_ENV and value != FORCED_ENV[name] for name, value in supplied.items()):
        raise ExecutionLifecycleV16Error("environment attempts to override a forced policy value")
    result = dict(FORCED_ENV)
    if "PATH" in supplied:
        result["PATH"] = supplied["PATH"]
    elif os.environ.get("PATH"):
        result["PATH"] = os.environ["PATH"]
    for name, value in supplied.items():
        if name != "PATH":
            result[name] = value
    if cuda_visible_devices is not None:
        if not re.fullmatch(r"[0-3]", cuda_visible_devices):
            raise ExecutionLifecycleV16Error("CUDA slot must be one pinned GPU index")
        result["CUDA_VISIBLE_DEVICES"] = cuda_visible_devices
    return result


def initialize_attempt(
    output_root: Path, attempt_id: str, *, gates: Mapping[str, str], execution_identity: Mapping[str, str], executor_sha256: str,
    execution_mode: str = "production",
) -> dict[str, Any]:
    """Create/reopen only an identical, fully admitted A1.2 attempt."""

    missing = REQUIRED_GATES - set(gates)
    if execution_mode not in {"production", "synthetic"}:
        raise ExecutionLifecycleV16Error("execution_mode must be production or synthetic")
    if execution_mode == "production" and (missing or any(gates.get(name) != "PASS" for name in REQUIRED_GATES)):
        raise ExecutionLifecycleV16Error("provider admission and execution adoption gates must all PASS")
    if execution_mode == "synthetic" and (
        missing
        or gates.get("execution_adoption") == "PASS"
        or gates.get("frozen_bindings") != "PASS"
        or gates.get("protected_boundary") != "PASS"
    ):
        raise ExecutionLifecycleV16Error("synthetic mode cannot run under adopted execution gates")
    if not re.fullmatch(r"[a-f0-9]{64}", executor_sha256):
        raise ExecutionLifecycleV16Error("executor_sha256 is required")
    if not execution_identity or any(not re.fullmatch(r"[a-f0-9]{64}", value) for value in execution_identity.values()):
        raise ExecutionLifecycleV16Error("execution identity must contain only SHA-256 bindings")
    directory = _attempt_dir(output_root, attempt_id)
    unsigned = {
        "schema_version": "myis.armindex-a1.2-execution-attempt.v16", "attempt_id": attempt_id,
        "revision_id": REVISION_ID, "gates": dict(sorted(gates.items())), "execution_mode": execution_mode,
        "execution_identity": dict(sorted(execution_identity.items())), "executor_sha256": executor_sha256,
        "required_cells": list(required_cells()), "created_at": _utc(),
    }
    if directory.exists():
        previous = _attempt(directory, attempt_id)
        comparable = {key: value for key, value in previous.items() if key not in {"created_at", "attempt_sha256"}}
        expected = {key: value for key, value in unsigned.items() if key != "created_at"}
        if comparable != expected:
            raise ExecutionLifecycleV16Error("resume requires the exact same attempt identity and bindings")
        return previous
    directory.mkdir(parents=True, exist_ok=False)
    _atomic(directory / "attempt.json", {**unsigned, "attempt_sha256": canonical_sha256(unsigned)}, immutable=True)
    state = {"schema_version": "myis.armindex-a1.2-execution-state.v16", "attempt_id": attempt_id, "status": "RUNNING", "sequence": 1, "reason": "admission_passed", "updated_at": _utc()}
    _atomic(directory / "state.json", {**state, "state_sha256": canonical_sha256(state)}, immutable=True)
    return _attempt(directory, attempt_id)


def _transition(directory: Path, attempt_id: str, status: str, reason: str) -> dict[str, Any]:
    previous = _state(directory, attempt_id)
    if previous["status"] == "COMPLETE":
        raise ExecutionLifecycleV16Error("completed attempt is immutable")
    unsigned = {"schema_version": "myis.armindex-a1.2-execution-state.v16", "attempt_id": attempt_id, "status": status, "sequence": int(previous["sequence"]) + 1, "reason": reason, "updated_at": _utc()}
    value = {**unsigned, "state_sha256": canonical_sha256(unsigned)}
    _atomic(directory / "state.json", value)
    return value


def _durable_hash(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise ExecutionLifecycleV16Error("artifact must be a regular file")
    with path.open("rb+") as handle:
        while handle.read(1024 * 1024):
            pass
        handle.flush()
        os.fsync(handle.fileno())
    return file_sha256(path)


def _assert_aggregate_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            name = str(key)
            if (
                FORBIDDEN_KEY.search(name)
                and not name.endswith("_sha256")
                and name not in SAFE_AGGREGATE_KEYS
            ):
                raise ExecutionLifecycleV16Error("aggregate receipt contains a protected field")
            _assert_aggregate_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _assert_aggregate_keys(child)


def record_cell_checkpoint(output_root: Path, attempt_id: str, cell_id: str, aggregate_receipt: Path) -> dict[str, Any]:
    """Commit one aggregate-safe program-arm result after its bytes are durable."""

    if cell_id not in required_cells() or not CELL_RE.fullmatch(cell_id):
        raise ExecutionLifecycleV16Error("cell is not one of the frozen 25 program-arm cells")
    directory = _attempt_dir(output_root, attempt_id)
    _attempt(directory, attempt_id)
    if _state(directory, attempt_id)["status"] != "RUNNING":
        raise ExecutionLifecycleV16Error("checkpoint requires a RUNNING attempt")
    receipt = aggregate_receipt.resolve()
    try:
        relative = receipt.relative_to((directory / "results").resolve())
    except ValueError as error:
        raise ExecutionLifecycleV16Error("result receipt must remain under attempt/results") from error
    if FORBIDDEN_PATH.search(relative.as_posix()):
        raise ExecutionLifecycleV16Error("result receipt path is not aggregate-safe")
    payload = _load_checked(receipt, "receipt_sha256")
    _assert_aggregate_keys(payload)
    if payload.get("attempt_id") != attempt_id or payload.get("cell_id") != cell_id or payload.get("aggregate_safe") is not True:
        raise ExecutionLifecycleV16Error("result receipt is not same-attempt aggregate-safe evidence")
    digest = _durable_hash(receipt)
    unsigned = {"schema_version": "myis.armindex-a1.2-cell-checkpoint.v16", "attempt_id": attempt_id, "cell_id": cell_id, "status": "COMPLETE", "result_uri": (Path("results") / relative).as_posix(), "result_sha256": digest, "completed_at": _utc()}
    value = {**unsigned, "checkpoint_sha256": canonical_sha256(unsigned)}
    _atomic(directory / "checkpoints" / f"{cell_id}.json", value, immutable=True)
    return value


def completed_cells(output_root: Path, attempt_id: str) -> tuple[str, ...]:
    directory = _attempt_dir(output_root, attempt_id)
    _attempt(directory, attempt_id)
    result: list[str] = []
    for path in sorted((directory / "checkpoints").glob("*.json")):
        value = _load_checked(path, "checkpoint_sha256")
        if value.get("attempt_id") != attempt_id or value.get("cell_id") not in required_cells() or value.get("status") != "COMPLETE":
            raise ExecutionLifecycleV16Error("invalid checkpoint binding")
        receipt = directory / value["result_uri"]
        if _durable_hash(receipt) != value.get("result_sha256"):
            raise ExecutionLifecycleV16Error("checkpointed result bytes drifted")
        result.append(value["cell_id"])
    if len(result) != len(set(result)):
        raise ExecutionLifecycleV16Error("duplicate checkpoint cell")
    return tuple(result)


def _proc_start(pid: int, proc_root: Path = Path("/proc")) -> str:
    try:
        text = (proc_root / str(pid) / "stat").read_text(encoding="utf-8")
        return text[text.rfind(")") + 2 :].split()[19]
    except (OSError, IndexError) as error:
        raise ExecutionLifecycleV16Error("Linux process start identity unavailable") from error


def record_process(output_root: Path, attempt_id: str, worker_id: str, pid: int, *, proc_root: Path = Path("/proc")) -> dict[str, Any]:
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{1,79}", worker_id):
        raise ExecutionLifecycleV16Error("worker_id is invalid")
    directory = _attempt_dir(output_root, attempt_id)
    _attempt(directory, attempt_id)
    if _state(directory, attempt_id)["status"] != "RUNNING":
        raise ExecutionLifecycleV16Error("process registration requires a RUNNING attempt")
    unsigned = {"schema_version": "myis.armindex-a1.2-process.v16", "attempt_id": attempt_id, "worker_id": worker_id, "pid": pid, "linux_proc_start_time": _proc_start(pid, proc_root), "recorded_at": _utc()}
    value = {**unsigned, "process_sha256": canonical_sha256(unsigned)}
    _atomic(directory / "processes" / f"{worker_id}.json", value, immutable=True)
    return value


def heartbeat(output_root: Path, attempt_id: str, worker_id: str, *, proc_root: Path = Path("/proc")) -> dict[str, Any]:
    directory = _attempt_dir(output_root, attempt_id)
    process = _load_checked(directory / "processes" / f"{worker_id}.json", "process_sha256")
    if process.get("attempt_id") != attempt_id or _proc_start(int(process["pid"]), proc_root) != process.get("linux_proc_start_time"):
        raise ExecutionLifecycleV16Error("process identity changed or PID was reused")
    unsigned = {"schema_version": "myis.armindex-a1.2-heartbeat.v16", "attempt_id": attempt_id, "worker_id": worker_id, "pid": process["pid"], "linux_proc_start_time": process["linux_proc_start_time"], "generated_at": _utc()}
    value = {**unsigned, "heartbeat_sha256": canonical_sha256(unsigned)}
    _atomic(directory / "heartbeats" / f"{worker_id}.json", value)
    return value


def assert_heartbeats_fresh(output_root: Path, attempt_id: str, *, maximum_age_seconds: float = 300.0) -> tuple[str, ...]:
    """Verify every currently registered child has a same-identity fresh beat."""

    if maximum_age_seconds <= 0:
        raise ExecutionLifecycleV16Error("heartbeat maximum age must be positive")
    directory = _attempt_dir(output_root, attempt_id)
    _attempt(directory, attempt_id)
    workers: list[str] = []
    now = time.time()
    for process_path in sorted((directory / "processes").glob("*.json")):
        process = _load_checked(process_path, "process_sha256")
        worker_id = str(process.get("worker_id", ""))
        beat = _load_checked(directory / "heartbeats" / f"{worker_id}.json", "heartbeat_sha256")
        if beat.get("attempt_id") != attempt_id or beat.get("pid") != process.get("pid") or beat.get("linux_proc_start_time") != process.get("linux_proc_start_time"):
            raise ExecutionLifecycleV16Error("heartbeat identity does not bind its registered child")
        try:
            age = now - datetime.fromisoformat(str(beat["generated_at"])).timestamp()
        except (KeyError, ValueError) as error:
            raise ExecutionLifecycleV16Error("heartbeat timestamp is invalid") from error
        if age < 0 or age > maximum_age_seconds:
            raise ExecutionLifecycleV16Error("heartbeat is stale")
        workers.append(worker_id)
    return tuple(workers)


def resume_plan(output_root: Path, attempt_id: str) -> dict[str, tuple[str, ...]]:
    """Return only uncheckpointed frozen cells; never restarts different work."""

    directory = _attempt_dir(output_root, attempt_id)
    attempt = _attempt(directory, attempt_id)
    if _state(directory, attempt_id)["status"] != "RUNNING":
        raise ExecutionLifecycleV16Error("only a RUNNING attempt may resume")
    complete = completed_cells(output_root, attempt_id)
    return {"completed": complete, "pending": tuple(cell for cell in attempt["required_cells"] if cell not in set(complete))}


def cancel_and_reap(processes: Mapping[str, subprocess.Popen[Any]], *, timeout_seconds: float = 15.0) -> dict[str, Any]:
    """Stop sibling children immediately; never signals a PID not owned by us."""

    for process in processes.values():
        if process.poll() is None:
            process.terminate()
    deadline = time.monotonic() + timeout_seconds
    for process in processes.values():
        remaining = max(0.0, deadline - time.monotonic())
        try:
            process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            process.kill()
    return {worker_id: process.wait() for worker_id, process in processes.items()}


def supervise_commands(
    output_root: Path, attempt_id: str, commands: Mapping[str, Sequence[str]], *, base_environment: Mapping[str, str] | None = None,
    gpu_slot_by_worker: Mapping[str, str] | None = None, heartbeat_interval_seconds: float = 15.0,
) -> dict[str, int]:
    """Run bounded sibling commands, cancelling and reaping every sibling on failure."""

    directory = _attempt_dir(output_root, attempt_id)
    if _state(directory, attempt_id)["status"] != "RUNNING" or not commands:
        raise ExecutionLifecycleV16Error("supervision requires a RUNNING attempt and workers")
    children: dict[str, subprocess.Popen[Any]] = {}
    try:
        for worker_id, command in commands.items():
            if not command:
                raise ExecutionLifecycleV16Error("worker command is empty")
            environment = explicit_environment(base_environment, cuda_visible_devices=(gpu_slot_by_worker or {}).get(worker_id))
            logs = directory / "logs"
            logs.mkdir(parents=True, exist_ok=True)
            stdout = (logs / f"{worker_id}.stdout").open("xb")
            stderr = (logs / f"{worker_id}.stderr").open("xb")
            try:
                process = subprocess.Popen(list(command), stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, env=environment, close_fds=True)
            finally:
                stdout.close()
                stderr.close()
            children[worker_id] = process
            record_process(output_root, attempt_id, worker_id, process.pid)
            heartbeat(output_root, attempt_id, worker_id)
        last_beat = 0.0
        while True:
            failed = {worker_id: process.returncode for worker_id, process in children.items() if process.poll() not in (None, 0)}
            if failed:
                exits = cancel_and_reap(children)
                _transition(directory, attempt_id, "FAILED", "sibling_failure_cancelled_and_reaped")
                raise ExecutionLifecycleV16Error(f"worker failed and siblings reaped: {failed}; exits={exits}")
            if all(process.poll() == 0 for process in children.values()):
                return {worker_id: int(process.returncode or 0) for worker_id, process in children.items()}
            if time.monotonic() - last_beat >= heartbeat_interval_seconds:
                for worker_id, process in children.items():
                    if process.poll() is None:
                        heartbeat(output_root, attempt_id, worker_id)
                last_beat = time.monotonic()
            time.sleep(0.05)
    except BaseException:
        if children:
            cancel_and_reap(children)
        if _state(directory, attempt_id)["status"] == "RUNNING":
            _transition(directory, attempt_id, "FAILED", "supervision_exception_cancelled_and_reaped")
        raise


def teardown_attempt(output_root: Path, attempt_id: str, *, children_reaped: bool) -> dict[str, Any]:
    directory = _attempt_dir(output_root, attempt_id)
    _attempt(directory, attempt_id)
    if not children_reaped:
        raise ExecutionLifecycleV16Error("teardown requires verified child reaping")
    for path in (directory / "processes").glob("*.json"):
        record = _load_checked(path, "process_sha256")
        if (Path("/proc") / str(record["pid"])).exists():
            raise ExecutionLifecycleV16Error("recorded child remains live")
    unsigned = {"schema_version": "myis.armindex-a1.2-teardown.v16", "attempt_id": attempt_id, "children_reaped": True, "provider_destroy_invoked": False, "completed_at": _utc()}
    value = {**unsigned, "teardown_sha256": canonical_sha256(unsigned)}
    _atomic(directory / "teardown.json", value, immutable=True)
    return value


def complete_attempt(output_root: Path, attempt_id: str) -> dict[str, Any]:
    directory = _attempt_dir(output_root, attempt_id)
    attempt = _attempt(directory, attempt_id)
    complete = completed_cells(output_root, attempt_id)
    missing = sorted(set(attempt["required_cells"]) - set(complete))
    if missing or len(complete) != 25:
        _transition(directory, attempt_id, "FAILED", "incomplete_common_screen")
        raise ExecutionLifecycleV16Error(f"25/25 required; missing={len(missing)}")
    return _transition(directory, attempt_id, "COMPLETE", "25_of_25_aggregate_safe_checkpoints")


def _safe_files(directory: Path) -> list[Path]:
    # Checkpoints and logs are local execution controls, not return payloads.
    permitted = ("attempt.json", "state.json", "results/", "processes/", "heartbeats/", "teardown.json")
    files = []
    for path in directory.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(directory).as_posix()
        if relative.startswith(("checkpoints/", "logs/")) or relative == "safe-export-members.v16.json":
            continue
        if FORBIDDEN_PATH.search(relative) or not any(relative == value or relative.startswith(value) for value in permitted):
            raise ExecutionLifecycleV16Error("safe export encountered an unsafe path")
        if path.stat().st_size > 16 * 1024 * 1024:
            raise ExecutionLifecycleV16Error("safe export member exceeds size limit")
        files.append(path)
    return sorted(files)


def build_safe_export(output_root: Path, attempt_id: str, archive_path: Path) -> dict[str, Any]:
    directory = _attempt_dir(output_root, attempt_id)
    attempt = _attempt(directory, attempt_id)
    if attempt.get("execution_mode") != "synthetic":
        raise ExecutionLifecycleV16Error("generic export is synthetic-only; production requires strict safe return")
    if _state(directory, attempt_id)["status"] != "COMPLETE":
        raise ExecutionLifecycleV16Error("safe export requires complete 25/25 attempt")
    teardown = _load_checked(directory / "teardown.json", "teardown_sha256")
    if teardown.get("attempt_id") != attempt_id or teardown.get("children_reaped") is not True:
        raise ExecutionLifecycleV16Error("safe export requires same-attempt teardown")
    archive = archive_path.resolve()
    export_root = (output_root.resolve() / "exports").resolve()
    if archive.parent != export_root or attempt_id not in archive.name:
        raise ExecutionLifecycleV16Error("archive must be in the attempt-bound export root")
    receipt_path = archive.with_suffix(archive.suffix + ".receipt.json")
    if archive.is_file() and receipt_path.is_file():
        prior = _load_checked(receipt_path, "receipt_sha256")
        if prior.get("attempt_id") != attempt_id or prior.get("archive_sha256") != file_sha256(archive):
            raise ExecutionLifecycleV16Error("existing safe export does not match this attempt")
        return prior
    files = _safe_files(directory)
    members = [{"uri": path.relative_to(directory).as_posix(), "sha256": _durable_hash(path), "size_bytes": path.stat().st_size} for path in files]
    unsigned = {"schema_version": "myis.armindex-a1.2-safe-export-members.v16", "attempt_id": attempt_id, "attempt_sha256": attempt["attempt_sha256"], "members": members}
    manifest = {**unsigned, "members_sha256": canonical_sha256(unsigned)}
    manifest_path = directory / "safe-export-members.v16.json"
    _atomic(manifest_path, manifest, immutable=True)
    export_root.mkdir(parents=True, exist_ok=True)
    temporary = export_root / f".{archive.name}.{os.getpid()}.tmp"
    with tarfile.open(temporary, "w:gz", format=tarfile.PAX_FORMAT) as bundle:
        for path in [*files, manifest_path]:
            bundle.add(path, arcname=path.relative_to(directory).as_posix(), recursive=False)
    os.replace(temporary, archive)
    validate_safe_export_archive(archive)
    receipt_unsigned = {"schema_version": "myis.armindex-a1.2-safe-export-receipt.v16", "attempt_id": attempt_id, "status": "PASS", "attempt_sha256": attempt["attempt_sha256"], "members_sha256": manifest["members_sha256"], "archive_sha256": file_sha256(archive), "archive_bytes": archive.stat().st_size}
    receipt = {**receipt_unsigned, "receipt_sha256": canonical_sha256(receipt_unsigned)}
    _atomic(receipt_path, receipt, immutable=True)
    return receipt


def validate_production_safe_return(output_root: Path, attempt_id: str, archive_path: Path) -> dict[str, Any]:
    """Accept a production return only when the exact v16 archive validates."""

    from .a1_2_safe_return_v16 import SafeReturnV16Error, validate_safe_return_archive

    directory = _attempt_dir(output_root, attempt_id)
    attempt = _attempt(directory, attempt_id)
    if attempt.get("execution_mode") != "production" or _state(directory, attempt_id)["status"] != "COMPLETE":
        raise ExecutionLifecycleV16Error("strict safe return requires a complete production attempt")
    teardown = _load_checked(directory / "teardown.json", "teardown_sha256")
    if teardown.get("attempt_id") != attempt_id or teardown.get("children_reaped") is not True:
        raise ExecutionLifecycleV16Error("strict safe return requires same-attempt teardown")
    try:
        result = validate_safe_return_archive(archive_path)
    except SafeReturnV16Error as error:
        raise ExecutionLifecycleV16Error("strict safe return validation failed") from error
    if result.get("attempt_id") != attempt_id or result.get("cells") != 25 or result.get("rows") != 150 or result.get("top_k") != 100:
        raise ExecutionLifecycleV16Error("safe return does not bind this complete 25/25 attempt")
    unsigned = {
        "schema_version": "myis.armindex-a1.2-production-safe-return-receipt.v16",
        "attempt_id": attempt_id, "status": "PASS", "archive_sha256": result["archive_sha256"],
        "archive_bytes": result["archive_bytes"], "member_cells": result["cells"],
        "work_rows": result["rows"], "top_k": result["top_k"],
    }
    receipt = {**unsigned, "receipt_sha256": canonical_sha256(unsigned)}
    _atomic(directory / "production-safe-return.receipt.v16.json", receipt, immutable=True)
    return receipt


def validate_safe_export_archive(archive_path: Path) -> dict[str, Any]:
    """Validate regular members and every member hash in the embedded manifest."""

    if not archive_path.is_file() or archive_path.is_symlink():
        raise ExecutionLifecycleV16Error("safe export archive is missing")
    with tarfile.open(archive_path, "r:gz") as bundle:
        members = bundle.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)) or any(not member.isreg() or Path(member.name).is_absolute() or ".." in Path(member.name).parts for member in members):
            raise ExecutionLifecycleV16Error("safe export contains unsafe or duplicate members")
        stream = bundle.extractfile("safe-export-members.v16.json")
        if stream is None:
            raise ExecutionLifecycleV16Error("safe export member manifest is missing")
        try:
            manifest = json.loads(stream.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ExecutionLifecycleV16Error("safe export member manifest is invalid") from error
        body = dict(manifest)
        if body.pop("members_sha256", None) != canonical_sha256(body):
            raise ExecutionLifecycleV16Error("safe export member manifest hash mismatch")
        rows = manifest.get("members")
        if not isinstance(rows, list) or sorted(names) != sorted([row["uri"] for row in rows] + ["safe-export-members.v16.json"]):
            raise ExecutionLifecycleV16Error("safe export members differ from manifest")
        for row in rows:
            if FORBIDDEN_PATH.search(str(row["uri"])):
                raise ExecutionLifecycleV16Error("safe export includes a forbidden member")
            stream = bundle.extractfile(str(row["uri"]))
            if stream is None:
                raise ExecutionLifecycleV16Error("safe export member is unreadable")
            digest = hashlib.sha256()
            size = 0
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
                size += len(chunk)
            if digest.hexdigest() != row.get("sha256") or size != row.get("size_bytes"):
                raise ExecutionLifecycleV16Error(f"safe export member hash mismatch: {row['uri']}")
    return {"status": "PASS", "archive_sha256": file_sha256(archive_path), "member_count": len(members), "members_sha256": manifest["members_sha256"]}
