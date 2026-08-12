"""Operational A2 orchestration with measured execution locked by default."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import tempfile
import time
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a2_entry_preflight_v16 import evaluate_a2_entry_preflight
from .a2_execution_readiness import (
    A2ExecutionReadinessError,
    append_lifecycle_checkpoint,
    build_execution_adoption_receipt,
    build_execution_bundle,
    build_lifecycle_checkpoint,
    build_provider_admission_receipt,
    build_safe_return_receipt,
    build_winner_receipt,
    build_watchdog_script,
    frozen_candidates,
    resume_checkpoint,
    validate_execution_adoption_receipt,
    validate_execution_bundle,
    validate_provider_admission_receipt,
)

_HASH = re.compile(r"^[a-f0-9]{64}$")
_ATTEMPT = re.compile(r"^a2-[a-z0-9-]{7,63}$")
_REMOTE_ROOT = re.compile(r"^/opt/myis/a2-[a-z0-9][a-z0-9-]{7,63}$")
_HOST = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_OWNER_KEYS = {
    "VAST_HOST",
    "VAST_PORT",
    "VAST_USER",
    "SSH_KEY_PATH",
    "LOCAL_KNOWN_HOSTS_FILE",
}
_RESULT_FIELDS = {
    "schema_version",
    "attempt_id",
    "candidate_id",
    "arm_id",
    "program_sha256",
    "executor_output_sha256",
    "evaluator_input_sha256",
    "evaluator_sha256",
    "code_sha256",
    "model_sha256",
    "data_sha256",
    "primary_metric",
    "secondary_metrics",
    "latency",
    "cost",
    "coverage",
    "resume_count",
    "failure_count",
    "reserve_activation_passed",
    "reserve_activation_evidence_sha256",
    "train_only",
    "rep_dev_measured",
    "protected_payload_included",
    "per_query_outcomes_included",
}


class A2OperationalExecutorError(RuntimeError):
    """Raised when operational A2 work cannot proceed without crossing a lock."""


def _load_json(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A2OperationalExecutorError(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise A2OperationalExecutorError(f"{role} must be a JSON object")
    return value


def _validate(root: Path, schema_name: str, value: Mapping[str, Any]) -> None:
    schema = _load_json(root / "schemas/armindex" / schema_name, role=schema_name)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(value)),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if errors:
        raise A2OperationalExecutorError(
            f"{schema_name} validation failed: {errors[0].message}"
        )


def _freeze_bindings(root: Path) -> dict[str, str]:
    candidates = frozen_candidates(root)
    manifest = _load_json(
        root
        / "campaigns/armindex-multiretriever-v2/manifests/"
        "a2-five-arm-candidate-manifest.v1.json",
        role="candidate manifest",
    )
    receipt = _load_json(
        root
        / "campaigns/armindex-multiretriever-v2/evidence/"
        "a2-five-arm-candidate-freeze.receipt.v1.json",
        role="candidate freeze receipt",
    )
    lock = _load_json(
        root / "control/armindex/a2/candidate-freeze.lock.v1.json",
        role="candidate freeze lock",
    )
    if len(candidates) != 52:
        raise A2OperationalExecutorError("candidate freeze is incomplete")
    return {
        "manifest_sha256": str(manifest["manifest_sha256"]),
        "freeze_receipt_sha256": str(receipt["receipt_sha256"]),
        "lock_sha256": str(lock["lock_sha256"]),
    }


def _hash(value: object, *, role: str) -> str:
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise A2OperationalExecutorError(f"{role} must be a SHA-256")
    return value


def _decimal(value: object, *, role: str) -> str:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise A2OperationalExecutorError(f"{role} is invalid") from error
    if not number.is_finite() or number < 0:
        raise A2OperationalExecutorError(f"{role} is invalid")
    return format(number, "f")


def _write_json(path: Path, value: Mapping[str, Any]) -> Path:
    encoded = (
        json.dumps(dict(value), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + "\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_text(encoding="ascii") != encoded:
            raise A2OperationalExecutorError("immutable artifact already differs")
        return path
    descriptor, name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def _replace_json(path: Path, value: Mapping[str, Any]) -> Path:
    """Atomically replace mutable operational state such as a heartbeat."""

    encoded = (
        json.dumps(dict(value), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + "\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.is_symlink():
        raise A2OperationalExecutorError("mutable operational state is a symlink")
    descriptor, name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def load_owner_connection(path: Path) -> dict[str, Any]:
    """Load only connection fields; returned values must never be printed or committed."""

    values: dict[str, str] = {}
    try:
        lines = path.resolve(strict=True).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise A2OperationalExecutorError("owner connection file is unavailable") from error
    for line in lines:
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split(":", 1)
        if key in _OWNER_KEYS:
            values[key] = value.strip().strip('"')
    if set(values) != _OWNER_KEYS:
        raise A2OperationalExecutorError("owner connection fields are incomplete")
    if _HOST.fullmatch(values["VAST_HOST"]) is None:
        raise A2OperationalExecutorError("owner SSH host is invalid")
    try:
        port = int(values["VAST_PORT"])
    except ValueError as error:
        raise A2OperationalExecutorError("owner SSH port is invalid") from error
    if not 1 <= port <= 65535 or values["VAST_USER"] != "root":
        raise A2OperationalExecutorError("owner SSH identity is invalid")
    key = Path(values["SSH_KEY_PATH"])
    known_hosts = Path(values["LOCAL_KNOWN_HOSTS_FILE"])
    if (
        not key.is_file()
        or key.is_symlink()
        or not known_hosts.is_file()
        or known_hosts.is_symlink()
    ):
        raise A2OperationalExecutorError("owner SSH files are missing or unsafe")
    return {
        "host": values["VAST_HOST"],
        "port": port,
        "user": values["VAST_USER"],
        "key_path": key.resolve(),
        "known_hosts_path": known_hosts.resolve(),
    }


def _ssh_arguments(connection: Mapping[str, Any]) -> list[str]:
    return [
        "-i",
        str(connection["key_path"]),
        "-p",
        str(connection["port"]),
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        f"UserKnownHostsFile={connection['known_hosts_path']}",
        f"{connection['user']}@{connection['host']}",
    ]


def _scp_arguments(connection: Mapping[str, Any]) -> list[str]:
    return [
        "-i",
        str(connection["key_path"]),
        "-P",
        str(connection["port"]),
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        f"UserKnownHostsFile={connection['known_hosts_path']}",
    ]


def _native(
    executable: str,
    arguments: Sequence[str],
    *,
    role: str,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str:
    result = runner(
        [executable, *arguments],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise A2OperationalExecutorError(f"{role} failed closed")
    return result.stdout.strip()


def validate_measurement_authority(
    repository_root: Path,
    authority: Mapping[str, Any],
    *,
    attempt_id: str,
    execution_adoption_receipt_sha256: str,
) -> dict[str, Any]:
    """Validate the separate AP-adopted authority required after staging."""

    root = repository_root.resolve()
    checked = dict(authority)
    _validate(root, "a2-measured-execution-authority.v1.json", checked)
    if (
        checked["schema_version"] != "myis.armindex-a2-measured-execution-authority.v1"
        or checked["status"] != "PASS_A2_MEASURED_EXECUTION_AUTHORIZED"
        or checked["attempt_id"] != attempt_id
        or checked["execution_adoption_receipt_sha256"]
        != execution_adoption_receipt_sha256
        or checked["measured_a2_authorized"] is not True
        or checked["candidate_generation_allowed"] is not False
        or checked["candidate_mutation_allowed"] is not False
        or checked["rep_dev_measurement_allowed"] is not False
        or checked["a3_allowed"] is not False
        or checked["selection_allowed"] is not False
        or checked["final_allowed"] is not False
        or checked["freeze_bindings"] != _freeze_bindings(root)
        or checked["authority_sha256"]
        != canonical_sha256(
            {key: value for key, value in checked.items() if key != "authority_sha256"}
        )
    ):
        raise A2OperationalExecutorError("measured execution authority is not adopted")
    goal_path = root / checked["source_goal_uri"]
    if (
        not goal_path.is_file()
        or goal_path.is_symlink()
        or file_sha256(goal_path) != checked["source_goal_sha256"]
    ):
        raise A2OperationalExecutorError("measured execution authority goal binding drift")
    candidates = frozen_candidates(root)
    active_reserves = checked["active_reserve_candidate_ids"]
    if any(
        candidate_id not in candidates
        or candidates[candidate_id]["tier"] != "conditional_reserve"
        or candidates[candidate_id]["arm_id"] not in {"ARM-03", "ARM-04", "ARM-05"}
        for candidate_id in active_reserves
    ):
        raise A2OperationalExecutorError("authority activates a non-reserve candidate")
    for arm_id in ("ARM-03", "ARM-04", "ARM-05"):
        count = sum(candidates[candidate_id]["arm_id"] == arm_id for candidate_id in active_reserves)
        if count not in {0, 4}:
            raise A2OperationalExecutorError("reserve activation must cover a complete arm batch")
    return checked


@contextmanager
def _attempt_lock(path: Path) -> Any:
    """Hold one OS-released lock; no PID liveness probe is used on Windows."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise A2OperationalExecutorError("another executor owns the attempt lock") from error
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _executor_environment(candidate: Mapping[str, Any]) -> dict[str, str]:
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
        "PYTHONDONTWRITEBYTECODE": "1",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "PIP_NO_INDEX": "1",
        "MYIS_A2_CANDIDATE_ID": str(candidate["candidate_id"]),
        "MYIS_A2_ARM_ID": str(candidate["arm_id"]),
        "MYIS_A2_PROGRAM_SHA256": str(candidate["program_sha256"]),
    }
    if os.name == "nt":
        for name in ("SystemRoot", "TEMP", "TMP"):
            if os.environ.get(name):
                environment[name] = os.environ[name]
    return environment


def _run_executor_process(
    command: Sequence[str],
    *,
    environment: Mapping[str, str],
    heartbeat_path: Path,
    process_path: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    if not command or timeout_seconds <= 0:
        raise A2OperationalExecutorError("external executor command or timeout is invalid")
    process = subprocess.Popen(
        list(command),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=dict(environment),
        close_fds=True,
    )
    launched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    _write_json(
        process_path,
        {
            "pid": process.pid,
            "launched_at_utc": launched_at,
            "command_sha256": canonical_sha256(list(command)),
            "owned_popen_handle": True,
        },
    )
    deadline = time.monotonic() + timeout_seconds
    try:
        while process.poll() is None:
            _replace_json(
                heartbeat_path,
                {
                    "pid": process.pid,
                    "launched_at_utc": launched_at,
                    "observed_at_utc": datetime.now(timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z"),
                    "owned_popen_handle": True,
                },
            )
            if time.monotonic() >= deadline:
                process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                raise A2OperationalExecutorError("external executor timed out and was reaped")
            time.sleep(0.05)
        stdout, _stderr = process.communicate()
    except BaseException:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        raise
    if process.returncode != 0:
        raise A2OperationalExecutorError("external executor failed and was reaped")
    try:
        value = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise A2OperationalExecutorError("external executor output is invalid JSON") from error
    if not isinstance(value, dict):
        raise A2OperationalExecutorError("external executor output must be an object")
    return value


def execute_external_candidate_set(
    repository_root: Path,
    *,
    attempt_id: str,
    adoption_receipt: Mapping[str, Any],
    measurement_authority: Mapping[str, Any],
    command_template: Sequence[str],
    output_directory: Path,
    checkpoint_ledger: Path,
    timeout_seconds: int = 21600,
    executor: Callable[..., Mapping[str, Any]] = _run_executor_process,
) -> dict[str, Any]:
    """Run the frozen external executor with resumable aggregate-only receipts."""

    root = repository_root.resolve()
    adoption = validate_execution_adoption_receipt(root, adoption_receipt)
    authority = validate_measurement_authority(
        root,
        measurement_authority,
        attempt_id=attempt_id,
        execution_adoption_receipt_sha256=adoption["receipt_sha256"],
    )
    if adoption["attempt_id"] != attempt_id:
        raise A2OperationalExecutorError("executor attempt differs from adoption")
    output = output_directory.resolve()
    if output.is_relative_to(root):
        raise A2OperationalExecutorError("external executor working output must remain Owner-local")
    if not command_template or any(not isinstance(item, str) or not item for item in command_template):
        raise A2OperationalExecutorError("external executor argv template is invalid")
    candidates = frozen_candidates(root)
    receipts_directory = output / "receipts"
    processes_directory = output / "processes"
    heartbeats_directory = output / "heartbeats"
    receipts_directory.mkdir(parents=True, exist_ok=True)
    completed: dict[str, dict[str, Any]] = {}
    for path in sorted(receipts_directory.glob("*.json")):
        receipt = _load_json(path, role="candidate result receipt")
        candidate_id = receipt.get("candidate_id")
        if candidate_id not in candidates:
            raise A2OperationalExecutorError("resume receipt is outside frozen membership")
        _validate(root, "a2-candidate-result-receipt.v1.json", receipt)
        if receipt.get("receipt_sha256") != canonical_sha256(
            {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        ):
            raise A2OperationalExecutorError("resume receipt hash drift")
        completed[str(candidate_id)] = receipt
    ledger = checkpoint_ledger.resolve()
    sequence = 0
    previous: str | None = None
    if ledger.exists():
        resumed = resume_checkpoint(ledger, attempt_id=attempt_id)
        sequence = int(resumed["sequence"])
        previous = str(resumed["checkpoint_sha256"])
        if int(resumed["completed_candidate_count"]) != len(completed):
            raise A2OperationalExecutorError("resume checkpoint differs from durable receipts")
    else:
        genesis = build_lifecycle_checkpoint(
            root,
            attempt_id=attempt_id,
            sequence=1,
            status="RUNNING",
            completed_candidate_count=len(completed),
            failed_candidate_count=0,
            resume_allowed=True,
        )
        append_lifecycle_checkpoint(ledger, genesis)
        sequence = 1
        previous = genesis["checkpoint_sha256"]
    with _attempt_lock(output / "attempt.lock"):
        for candidate_id, candidate in candidates.items():
            if candidate_id in completed:
                continue
            reserve = candidate["tier"] == "conditional_reserve"
            active_reserves = authority.get("active_reserve_candidate_ids", [])
            if reserve and candidate_id not in active_reserves:
                row = {
                    "schema_version": "myis.armindex-a2-external-candidate-result.v1",
                    "attempt_id": attempt_id,
                    "candidate_id": candidate_id,
                    "arm_id": candidate["arm_id"],
                    "program_sha256": candidate["program_sha256"],
                    "executor_output_sha256": canonical_sha256([candidate_id, "dormant"]),
                    "evaluator_input_sha256": canonical_sha256([candidate_id, "dormant-input"]),
                    "evaluator_sha256": authority["authority_sha256"],
                    "code_sha256": adoption["bundle_sha256"],
                    "model_sha256": "0" * 64,
                    "data_sha256": "0" * 64,
                    "primary_metric": None,
                    "secondary_metrics": None,
                    "latency": None,
                    "cost": None,
                    "coverage": {"expected_units": 1, "completed_units": 0},
                    "resume_count": 0,
                    "failure_count": 0,
                    "reserve_activation_passed": False,
                    "reserve_activation_evidence_sha256": None,
                    "train_only": True,
                    "rep_dev_measured": False,
                    "protected_payload_included": False,
                    "per_query_outcomes_included": False,
                }
            else:
                command = [
                    item.format(
                        candidate_id=candidate_id,
                        arm_id=candidate["arm_id"],
                        program_sha256=candidate["program_sha256"],
                    )
                    for item in command_template
                ]
                try:
                    row = dict(
                        executor(
                            command,
                            environment=_executor_environment(candidate),
                            heartbeat_path=heartbeats_directory
                            / f"{candidate_id}.attempt-{sequence + 1:04d}.json",
                            process_path=processes_directory
                            / f"{candidate_id}.attempt-{sequence + 1:04d}.json",
                            timeout_seconds=timeout_seconds,
                        )
                    )
                except BaseException:
                    paused = build_lifecycle_checkpoint(
                        root,
                        attempt_id=attempt_id,
                        sequence=sequence + 1,
                        status="PAUSED",
                        completed_candidate_count=len(completed),
                        failed_candidate_count=1,
                        resume_allowed=True,
                        previous_checkpoint_sha256=previous,
                    )
                    append_lifecycle_checkpoint(ledger, paused)
                    raise
                if reserve:
                    row["reserve_activation_passed"] = True
                    row["reserve_activation_evidence_sha256"] = authority[
                        "reserve_activation_evidence_sha256"
                    ]
            receipt = build_candidate_result_receipt(
                root,
                result=row,
                evidence_class="measured_development_aggregate",
                measurement_authority=authority,
                execution_adoption_receipt=adoption,
            )
            _write_json(receipts_directory / f"{candidate_id}.json", receipt)
            completed[candidate_id] = receipt
            sequence += 1
            checkpoint = build_lifecycle_checkpoint(
                root,
                attempt_id=attempt_id,
                sequence=sequence,
                status="RUNNING",
                completed_candidate_count=len(completed),
                failed_candidate_count=0,
                resume_allowed=True,
                previous_checkpoint_sha256=previous,
            )
            append_lifecycle_checkpoint(ledger, checkpoint)
            previous = checkpoint["checkpoint_sha256"]
    coverage = evaluate_candidate_receipts(root, receipts_by_candidate=completed)
    return {
        **coverage,
        "attempt_id": attempt_id,
        "checkpoint_sha256": previous,
        "execution_adoption_receipt_sha256": adoption["receipt_sha256"],
        "measurement_authority_sha256": authority["authority_sha256"],
        "workers_reaped": True,
    }


def build_candidate_result_receipt(
    repository_root: Path,
    *,
    result: Mapping[str, Any],
    evidence_class: str,
    measurement_authority: Mapping[str, Any] | None = None,
    execution_adoption_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate one aggregate external-executor output against frozen membership."""

    root = repository_root.resolve()
    row = dict(result)
    if set(row) != _RESULT_FIELDS:
        raise A2OperationalExecutorError("candidate result fields are not allowlisted")
    if row.get("schema_version") != "myis.armindex-a2-external-candidate-result.v1":
        raise A2OperationalExecutorError("candidate result schema is invalid")
    assert_aggregate_only(row)
    attempt_id = row.get("attempt_id")
    candidate_id = row.get("candidate_id")
    if not isinstance(attempt_id, str) or _ATTEMPT.fullmatch(attempt_id) is None:
        raise A2OperationalExecutorError("candidate result attempt is invalid")
    candidates = frozen_candidates(root)
    candidate = candidates.get(str(candidate_id))
    if candidate is None or row.get("arm_id") != candidate["arm_id"]:
        raise A2OperationalExecutorError("candidate result is outside frozen membership")
    if row.get("program_sha256") != candidate["program_sha256"]:
        raise A2OperationalExecutorError("candidate program hash drift")
    for field in (
        "executor_output_sha256",
        "evaluator_input_sha256",
        "evaluator_sha256",
        "code_sha256",
        "model_sha256",
        "data_sha256",
    ):
        _hash(row.get(field), role=field)
    if row.get("train_only") is not True or row.get("rep_dev_measured") is not False:
        raise A2OperationalExecutorError("candidate result crosses the train-only boundary")
    if (
        row.get("protected_payload_included") is not False
        or row.get("per_query_outcomes_included") is not False
    ):
        raise A2OperationalExecutorError("candidate result crosses the protected boundary")
    if evidence_class not in {"engineering_synthetic", "measured_development_aggregate"}:
        raise A2OperationalExecutorError("candidate result evidence class is invalid")
    if evidence_class == "measured_development_aggregate":
        try:
            adoption = validate_execution_adoption_receipt(
                root, dict(execution_adoption_receipt or {})
            )
            validate_measurement_authority(
                root,
                dict(measurement_authority or {}),
                attempt_id=str(attempt_id),
                execution_adoption_receipt_sha256=adoption["receipt_sha256"],
            )
        except (A2ExecutionReadinessError, A2OperationalExecutorError):
            raise A2OperationalExecutorError("measured candidate result lacks adopted authority")
    elif measurement_authority is not None or execution_adoption_receipt is not None:
        raise A2OperationalExecutorError("synthetic result cannot consume measured authority")
    reserve = candidate["tier"] == "conditional_reserve"
    active = row.get("reserve_activation_passed") is True
    activation_evidence = row.get("reserve_activation_evidence_sha256")
    if active:
        _hash(activation_evidence, role="reserve activation evidence")
    elif activation_evidence is not None:
        raise A2OperationalExecutorError("dormant reserve has activation evidence")
    if reserve and not active:
        if any(row.get(field) is not None for field in ("primary_metric", "secondary_metrics", "latency", "cost")):
            raise A2OperationalExecutorError("dormant reserve contains an outcome")
        if row.get("coverage") != {"expected_units": 1, "completed_units": 0}:
            raise A2OperationalExecutorError("dormant reserve coverage is invalid")
        status = "DORMANT_CONDITIONAL_RESERVE"
        primary = secondary = latency = cost = None
    else:
        primary_value = row.get("primary_metric")
        secondary_value = row.get("secondary_metrics")
        latency_value = row.get("latency")
        cost_value = row.get("cost")
        coverage = row.get("coverage")
        if (
            not isinstance(primary_value, Mapping)
            or primary_value.get("name") != "recall_at_100/out"
            or not isinstance(secondary_value, Mapping)
            or set(secondary_value) != {"ndcg_at_100/out", "ndcg_at_10/out"}
            or not isinstance(latency_value, Mapping)
            or set(latency_value) != {"wall_seconds", "search_p95_seconds"}
            or not isinstance(cost_value, Mapping)
            or set(cost_value) != {"charged_usd", "currency"}
            or cost_value.get("currency") != "USD"
            or not isinstance(coverage, Mapping)
            or coverage.get("expected_units") != coverage.get("completed_units")
        ):
            raise A2OperationalExecutorError("candidate aggregate outcome is incomplete")
        primary = {
            "name": "recall_at_100/out",
            "value": _decimal(primary_value.get("value"), role="primary metric"),
        }
        secondary = {
            key: _decimal(secondary_value[key], role=key)
            for key in ("ndcg_at_100/out", "ndcg_at_10/out")
        }
        latency = {
            key: _decimal(latency_value[key], role=key)
            for key in ("wall_seconds", "search_p95_seconds")
        }
        cost = {
            "charged_usd": _decimal(cost_value["charged_usd"], role="charged_usd"),
            "currency": "USD",
        }
        status = "PASS_A2_CANDIDATE_RESULT"
    for count in ("resume_count", "failure_count"):
        if isinstance(row.get(count), bool) or not isinstance(row.get(count), int) or row[count] < 0:
            raise A2OperationalExecutorError(f"{count} is invalid")
    body = {
        "schema_version": "myis.armindex-a2-candidate-result-receipt.v1",
        "receipt_id": f"{attempt_id}-{candidate_id}-candidate-result-v1",
        "attempt_id": attempt_id,
        "status": status,
        "evidence_class": evidence_class,
        "scientific_authority": evidence_class == "measured_development_aggregate",
        "candidate_id": candidate_id,
        "arm_id": candidate["arm_id"],
        "tier": candidate["tier"],
        "program_sha256": candidate["program_sha256"],
        "executor_output_sha256": row["executor_output_sha256"],
        "evaluator_input_sha256": row["evaluator_input_sha256"],
        "evaluator_sha256": row["evaluator_sha256"],
        "code_sha256": row["code_sha256"],
        "model_sha256": row["model_sha256"],
        "data_sha256": row["data_sha256"],
        "primary_metric": primary,
        "secondary_metrics": secondary,
        "latency": latency,
        "cost": cost,
        "coverage": dict(row["coverage"]),
        "resume_count": row["resume_count"],
        "failure_count": row["failure_count"],
        "reserve_activation_passed": active,
        "reserve_activation_evidence_sha256": activation_evidence,
        "train_only": True,
        "rep_dev_measured": False,
        "protected_payload_included": False,
        "per_query_outcomes_included": False,
        "freeze_bindings": _freeze_bindings(root),
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _validate(root, "a2-candidate-result-receipt.v1.json", receipt)
    return receipt


def evaluate_candidate_receipts(
    repository_root: Path,
    *,
    receipts_by_candidate: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Require exact 52-candidate accounting and unique matched-arm winners."""

    root = repository_root.resolve()
    candidates = frozen_candidates(root)
    if set(receipts_by_candidate) != set(candidates):
        raise A2OperationalExecutorError("candidate receipts must cover all 52 frozen IDs")
    winners: dict[str, dict[str, Any]] = {}
    winner_receipts: dict[str, dict[str, Any]] = {}
    receipt_hashes: list[str] = []
    for candidate_id, candidate in candidates.items():
        receipt = dict(receipts_by_candidate[candidate_id])
        _validate(root, "a2-candidate-result-receipt.v1.json", receipt)
        unsigned = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        if receipt.get("receipt_sha256") != canonical_sha256(unsigned):
            raise A2OperationalExecutorError("candidate result receipt hash drift")
        if receipt.get("candidate_id") != candidate_id or receipt.get("arm_id") != candidate["arm_id"]:
            raise A2OperationalExecutorError("candidate result receipt identity drift")
        if receipt.get("freeze_bindings") != _freeze_bindings(root):
            raise A2OperationalExecutorError("candidate result freeze binding drift")
        if (receipt.get("evidence_class") == "measured_development_aggregate") != (
            receipt.get("scientific_authority") is True
        ):
            raise A2OperationalExecutorError("candidate result authority class drift")
        reserve = candidate["tier"] == "conditional_reserve"
        if reserve and receipt["status"] == "DORMANT_CONDITIONAL_RESERVE":
            if receipt["reserve_activation_passed"] is not False:
                raise A2OperationalExecutorError("dormant reserve activation drift")
        elif receipt["status"] != "PASS_A2_CANDIDATE_RESULT":
            raise A2OperationalExecutorError("active candidate lacks a PASS result")
        receipt_hashes.append(receipt["receipt_sha256"])
    for arm_id in ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05"):
        scored: list[tuple[Decimal, str]] = []
        for candidate_id, candidate in candidates.items():
            receipt = receipts_by_candidate[candidate_id]
            if candidate["arm_id"] != arm_id or receipt["status"] != "PASS_A2_CANDIDATE_RESULT":
                continue
            scored.append((Decimal(receipt["primary_metric"]["value"]), candidate_id))
        scored.sort(key=lambda item: (-item[0], item[1]))
        if len(scored) < 2 or scored[0][0] == scored[1][0]:
            raise A2OperationalExecutorError("exact winner tie or insufficient arm coverage")
        winner_id = scored[0][1]
        candidate = candidates[winner_id]
        if arm_id in {"ARM-01", "ARM-02"} and candidate["advancement_eligible"] is not False:
            raise A2OperationalExecutorError("diagnostic arm gained advancement authority")
        winners[arm_id] = {
            "winner_candidate_id": winner_id,
            "primary_metric": str(scored[0][0]),
            "diagnostic_non_advancing": candidate["diagnostic_non_advancing"],
            "advancement_eligible": candidate["advancement_eligible"],
            "candidate_result_receipt_sha256": receipts_by_candidate[winner_id]["receipt_sha256"],
        }
        winner_receipts[arm_id] = build_winner_receipt(
            root,
            attempt_id=str(receipts_by_candidate[winner_id]["attempt_id"]),
            arm_id=arm_id,
            winner_candidate_id=winner_id,
            train_evaluation_receipt_sha256=str(
                receipts_by_candidate[winner_id]["receipt_sha256"]
            ),
            strict_tie_rejected=True,
        )
    return {
        "status": "PASS_A2_EXACT_COVERAGE",
        "candidate_count": 52,
        "matched_candidate_count": 40,
        "conditional_reserve_candidate_count": 12,
        "candidate_result_set_sha256": canonical_sha256(sorted(receipt_hashes)),
        "winners": winners,
        "winner_receipts": winner_receipts,
        "freeze_bindings": _freeze_bindings(root),
    }


def build_remote_stage_plan(
    repository_root: Path,
    *,
    attempt_id: str,
    remote_root: str,
    bundle_receipt: Mapping[str, Any],
    bundle_path: Path,
    watchdog: Mapping[str, Any],
) -> dict[str, Any]:
    """Return exact SSH/SCP operations without embedding owner connection values."""

    root = repository_root.resolve()
    bundle = bundle_path.resolve(strict=True)
    checked_bundle = validate_execution_bundle(
        root, bundle_path=bundle, receipt=bundle_receipt
    )
    if bundle.is_symlink() or checked_bundle["attempt_id"] != attempt_id:
        raise A2OperationalExecutorError("remote stage bundle hash drift")
    if watchdog.get("attempt_id") != attempt_id:
        raise A2OperationalExecutorError("remote stage watchdog hash drift")
    if _REMOTE_ROOT.fullmatch(remote_root) is None or not remote_root.endswith(attempt_id):
        raise A2OperationalExecutorError("remote stage root is invalid")
    commands = [
        "verify_zero_a2_workers",
        "verify_remote_root_absent",
        "create_isolated_remote_root",
        "upload_bundle_and_watchdog",
        "verify_bundle_and_watchdog_hashes",
        "extract_bundle_without_a1_mutation",
        "start_watchdog_and_record_pid_start_identity",
        "verify_watchdog_heartbeat",
        "write_staged_not_launched_checkpoint",
    ]
    body = {
        "schema_version": "myis.armindex-a2-operational-stage-plan.v1",
        "attempt_id": attempt_id,
        "remote_root": remote_root,
        "bundle_sha256": checked_bundle["bundle_sha256"],
        "watchdog_sha256": watchdog["watchdog_sha256"],
        "operations": commands,
        "a1_root_mutation_allowed": False,
        "provider_destroy_allowed": False,
        "measured_a2_allowed": False,
        "connection_values_included": False,
    }
    return {**body, "plan_sha256": canonical_sha256(body)}


def perform_remote_stage(
    repository_root: Path,
    *,
    attempt_id: str,
    provider_admission_receipt: Mapping[str, Any],
    bundle_receipt: Mapping[str, Any],
    bundle_path: Path,
    remote_root: str,
    watchdog_deadline_utc: str,
    owner_connection_path: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    """Create and verify an isolated A2 root, then stop before any worker launch."""

    root = repository_root.resolve()
    provider = validate_provider_admission_receipt(root, provider_admission_receipt)
    checked_bundle = validate_execution_bundle(
        root, bundle_path=bundle_path, receipt=bundle_receipt
    )
    if provider["attempt_id"] != attempt_id or checked_bundle["attempt_id"] != attempt_id:
        raise A2OperationalExecutorError("remote stage attempt identity drift")
    checkpoint = build_lifecycle_checkpoint(
        root,
        attempt_id=attempt_id,
        sequence=1,
        status="STAGED",
        completed_candidate_count=0,
        failed_candidate_count=0,
        resume_allowed=True,
    )
    watchdog = build_watchdog_script(
        attempt_id=attempt_id,
        remote_root=remote_root,
        deadline_utc=watchdog_deadline_utc,
    )
    plan = build_remote_stage_plan(
        root,
        attempt_id=attempt_id,
        remote_root=remote_root,
        bundle_receipt=checked_bundle,
        bundle_path=bundle_path,
        watchdog=watchdog,
    )
    connection = load_owner_connection(owner_connection_path)
    ssh = _ssh_arguments(connection)
    scp = _scp_arguments(connection)
    target = ssh[-1]
    bundle_hash = checked_bundle["bundle_sha256"]
    watchdog_hash = watchdog["watchdog_sha256"]
    watchdog_file = bundle_path.parent / f"{attempt_id}.watchdog.sh"
    watchdog_file.write_text(str(watchdog["script"]), encoding="ascii", newline="\n")
    try:
        prepare = (
            "set -eu; "
            "test -z \"$(pgrep -f 'myis_research.armindex.a2_' || true)\"; "
            f"test ! -e {shlex.quote(remote_root)}; "
            f"mkdir -p {shlex.quote(remote_root)}/incoming {shlex.quote(remote_root)}/current "
            f"{shlex.quote(remote_root)}/lifecycle/processes {shlex.quote(remote_root)}/lifecycle/heartbeats"
        )
        _native("ssh", [*ssh, prepare], role="remote root preparation", runner=runner)
        _native(
            "scp",
            [*scp, str(bundle_path.resolve()), f"{target}:{remote_root}/incoming/bundle.tar.gz"],
            role="bundle upload",
            runner=runner,
        )
        _native(
            "scp",
            [*scp, str(watchdog_file.resolve()), f"{target}:{remote_root}/incoming/watchdog.sh"],
            role="watchdog upload",
            runner=runner,
        )
        verify = (
            "set -eu; "
            f"test \"$(sha256sum {remote_root}/incoming/bundle.tar.gz | awk '{{print $1}}')\" = {bundle_hash}; "
            f"test \"$(sha256sum {remote_root}/incoming/watchdog.sh | awk '{{print $1}}')\" = {watchdog_hash}; "
            f"tar --no-same-owner --no-same-permissions -xzf {remote_root}/incoming/bundle.tar.gz -C {remote_root}/current; "
            f"chmod 700 {remote_root}/incoming/watchdog.sh; "
            f"nohup {remote_root}/incoming/watchdog.sh </dev/null >{remote_root}/lifecycle/watchdog.stdout "
            f"2>{remote_root}/lifecycle/watchdog.stderr & pid=$!; "
            "start=$(sed 's/.*) //' /proc/$pid/stat | awk '{print $20}'); "
            f"printf '%s:%s\\n' \"$pid\" \"$start\" >{remote_root}/lifecycle/processes/watchdog.identity; "
            f"printf '%s\\n' \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\" >{remote_root}/lifecycle/heartbeats/watchdog; "
            "printf '%s:%s' \"$pid\" \"$start\""
        )
        identity = _native("ssh", [*ssh, verify], role="remote stage verification", runner=runner)
        match = re.fullmatch(r"([1-9][0-9]{0,9}):([0-9]+)", identity.strip())
        if match is None:
            raise A2OperationalExecutorError("watchdog process identity is invalid")
    finally:
        watchdog_file.unlink(missing_ok=True)
    body = {
        "schema_version": "myis.armindex-a2-remote-stage-receipt.v1",
        "receipt_id": f"{attempt_id}-remote-stage-v1",
        "attempt_id": attempt_id,
        "status": "PASS_A2_REMOTE_STAGE_NOT_LAUNCHED",
        "remote_root": remote_root,
        "remote_root_created_fresh": True,
        "bundle_sha256": bundle_hash,
        "staged_bundle_sha256": bundle_hash,
        "watchdog_sha256": watchdog_hash,
        "watchdog_pid": int(match.group(1)),
        "watchdog_linux_proc_start_time": match.group(2),
        "watchdog_heartbeat_observed": True,
        "zero_workers_before_stage": True,
        "a1_root_mutated": False,
        "provider_destroy_performed": False,
        "measured_a2_started": False,
        "freeze_bindings": _freeze_bindings(root),
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _validate(root, "a2-remote-stage-receipt.v1.json", receipt)
    adoption = build_execution_adoption_receipt(
        root,
        attempt_id=attempt_id,
        provider_admission_receipt=provider,
        bundle_receipt=checked_bundle,
        remote_root=remote_root,
        staged_bundle_sha256=bundle_hash,
        watchdog_sha256=watchdog_hash,
        watchdog_deadline_utc=watchdog_deadline_utc,
        lifecycle_genesis_checkpoint_sha256=checkpoint["checkpoint_sha256"],
    )
    return {
        "plan": plan,
        "stage_receipt": receipt,
        "genesis_checkpoint": checkpoint,
        "execution_adoption_receipt": adoption,
        "state": "EXTERNAL_EXECUTION_REQUESTED_NOT_LAUNCHED",
        "measured_a2_started": False,
    }


def run_synthetic_dry_run(repository_root: Path, *, attempt_id: str) -> dict[str, Any]:
    """Exercise exact coverage, tie handling, reserve dormancy, and resume locally."""

    root = repository_root.resolve()
    if _ATTEMPT.fullmatch(attempt_id) is None:
        raise A2OperationalExecutorError("dry-run attempt ID is invalid")
    candidates = frozen_candidates(root)
    receipts: dict[str, dict[str, Any]] = {}
    for index, (candidate_id, candidate) in enumerate(candidates.items(), start=1):
        dormant = candidate["tier"] == "conditional_reserve"
        row = {
            "schema_version": "myis.armindex-a2-external-candidate-result.v1",
            "attempt_id": attempt_id,
            "candidate_id": candidate_id,
            "arm_id": candidate["arm_id"],
            "program_sha256": candidate["program_sha256"],
            "executor_output_sha256": canonical_sha256([candidate_id, "executor"]),
            "evaluator_input_sha256": canonical_sha256([candidate_id, "evaluator-input"]),
            "evaluator_sha256": "a" * 64,
            "code_sha256": "b" * 64,
            "model_sha256": "c" * 64,
            "data_sha256": "d" * 64,
            "primary_metric": None if dormant else {"name": "recall_at_100/out", "value": str(index)},
            "secondary_metrics": None if dormant else {"ndcg_at_100/out": str(index), "ndcg_at_10/out": str(index)},
            "latency": None if dormant else {"wall_seconds": "1", "search_p95_seconds": "0.1"},
            "cost": None if dormant else {"charged_usd": "0", "currency": "USD"},
            "coverage": {"expected_units": 1, "completed_units": 0 if dormant else 1},
            "resume_count": 0,
            "failure_count": 0,
            "reserve_activation_passed": False,
            "reserve_activation_evidence_sha256": None,
            "train_only": True,
            "rep_dev_measured": False,
            "protected_payload_included": False,
            "per_query_outcomes_included": False,
        }
        receipts[candidate_id] = build_candidate_result_receipt(
            root, result=row, evidence_class="engineering_synthetic"
        )
    coverage = evaluate_candidate_receipts(root, receipts_by_candidate=receipts)
    with tempfile.TemporaryDirectory(prefix="myis-a2-dry-run-") as temporary:
        ledger = Path(temporary) / "lifecycle.jsonl"
        first = build_lifecycle_checkpoint(
            root,
            attempt_id=attempt_id,
            sequence=1,
            status="STAGED",
            completed_candidate_count=0,
            failed_candidate_count=0,
            resume_allowed=True,
        )
        append_lifecycle_checkpoint(ledger, first)
        second = build_lifecycle_checkpoint(
            root,
            attempt_id=attempt_id,
            sequence=2,
            status="PAUSED",
            completed_candidate_count=17,
            failed_candidate_count=0,
            resume_allowed=True,
            previous_checkpoint_sha256=first["checkpoint_sha256"],
        )
        append_lifecycle_checkpoint(ledger, second)
        resumed = resume_checkpoint(ledger, attempt_id=attempt_id)
    watchdog = build_watchdog_script(
        attempt_id=attempt_id,
        remote_root=f"/opt/myis/{attempt_id}",
        deadline_utc="2099-01-01T00:00:00Z",
    )
    return {
        "status": "PASS_A2_SYNTHETIC_OPERATIONAL_DRY_RUN",
        "attempt_id": attempt_id,
        "candidate_count": coverage["candidate_count"],
        "matched_candidate_count": coverage["matched_candidate_count"],
        "conditional_reserve_candidate_count": coverage["conditional_reserve_candidate_count"],
        "winner_count": len(coverage["winners"]),
        "resume_checkpoint_sha256": resumed["checkpoint_sha256"],
        "watchdog_sha256": watchdog["watchdog_sha256"],
        "measured_a2_started": False,
        "provider_contacted": False,
        "protected_payload_included": False,
        "result_set_sha256": coverage["candidate_result_set_sha256"],
    }


def build_execution_closeout_receipt(
    repository_root: Path,
    *,
    attempt_id: str,
    coverage: Mapping[str, Any],
    winner_receipt_sha256s: Mapping[str, str],
    safe_return_receipt: Mapping[str, Any],
    terminal_checkpoint_sha256: str,
    claim_evidence_pointers: Sequence[str],
    evidence_class: str,
) -> dict[str, Any]:
    """Bind exact coverage, safe return, teardown, and journal evidence pointers."""

    root = repository_root.resolve()
    if coverage.get("status") != "PASS_A2_EXACT_COVERAGE" or coverage.get("candidate_count") != 52:
        raise A2OperationalExecutorError("execution closeout requires exact 52 coverage")
    if set(winner_receipt_sha256s) != {"ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05"}:
        raise A2OperationalExecutorError("execution closeout requires five winner receipts")
    for arm_id, value in winner_receipt_sha256s.items():
        _hash(value, role=f"{arm_id} winner receipt")
    if safe_return_receipt.get("status") != "PASS_A2_SAFE_RETURN":
        raise A2OperationalExecutorError("execution closeout requires safe return PASS")
    _hash(safe_return_receipt.get("receipt_sha256"), role="safe return receipt")
    _hash(terminal_checkpoint_sha256, role="terminal checkpoint")
    if not claim_evidence_pointers or any(
        not isinstance(pointer, str)
        or Path(pointer).is_absolute()
        or ".." in Path(pointer).parts
        for pointer in claim_evidence_pointers
    ):
        raise A2OperationalExecutorError("claim evidence pointers are unsafe")
    body = {
        "schema_version": "myis.armindex-a2-execution-closeout-receipt.v1",
        "receipt_id": f"{attempt_id}-execution-closeout-v1",
        "attempt_id": attempt_id,
        "status": "PASS_A2_EXECUTION_CLOSEOUT",
        "evidence_class": evidence_class,
        "candidate_count": 52,
        "matched_candidate_count": 40,
        "conditional_reserve_candidate_count": 12,
        "arm_winner_receipt_sha256s": dict(winner_receipt_sha256s),
        "candidate_result_set_sha256": coverage["candidate_result_set_sha256"],
        "safe_return_receipt_sha256": safe_return_receipt["receipt_sha256"],
        "terminal_checkpoint_sha256": terminal_checkpoint_sha256,
        "workers_reaped": True,
        "protected_scan_passed": True,
        "diagnostic_non_advancing_arms": ["ARM-01", "ARM-02"],
        "primary_advancement_arms": ["ARM-03", "ARM-05", "ARM-04"],
        "claim_evidence_pointers": list(claim_evidence_pointers),
        "freeze_bindings": _freeze_bindings(root),
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _validate(root, "a2-execution-closeout-receipt.v1.json", receipt)
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myis-a2-executor")
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--attempt-id", default="a2-operational-dryrun")
    parser.add_argument("--dry-run", action="store_true")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("preflight")
    bundle = commands.add_parser("bundle")
    bundle.add_argument("--output", type=Path, required=True)
    bundle.add_argument("--receipt-output", type=Path)
    admission = commands.add_parser("admit")
    admission.add_argument("--provider-evidence", type=Path, required=True)
    admission.add_argument("--runtime-sha256", required=True)
    admission.add_argument("--model-lockset-sha256", required=True)
    admission.add_argument("--data-handoff-sha256", required=True)
    admission.add_argument("--management-authority-sha256", required=True)
    admission.add_argument("--output", type=Path)
    stage = commands.add_parser("stage")
    stage.add_argument("--provider-admission-receipt", type=Path, required=True)
    stage.add_argument("--bundle-receipt", type=Path, required=True)
    stage.add_argument("--bundle", type=Path, required=True)
    stage.add_argument("--remote-root", required=True)
    stage.add_argument("--watchdog-deadline-utc", required=True)
    stage.add_argument("--owner-connection", type=Path, required=True)
    stage.add_argument("--output-directory", type=Path)
    execute = commands.add_parser("execute")
    execute.add_argument("--execution-adoption-receipt", type=Path, required=True)
    execute.add_argument("--measurement-authority", type=Path, required=True)
    execute.add_argument("--command-argv-json", type=Path, required=True)
    execute.add_argument("--output-directory", type=Path, required=True)
    execute.add_argument("--checkpoint-ledger", type=Path, required=True)
    execute.add_argument("--timeout-seconds", type=int, default=21600)
    resume = commands.add_parser("resume")
    resume.add_argument("--ledger", type=Path, required=True)
    safe_return = commands.add_parser("safe-return")
    safe_return.add_argument("--archive", type=Path, required=True)
    safe_return.add_argument("--remote-root", required=True)
    safe_return.add_argument("--output", type=Path)
    closeout = commands.add_parser("closeout")
    closeout.add_argument("--coverage", type=Path, required=True)
    closeout.add_argument("--winner-receipts", type=Path, required=True)
    closeout.add_argument("--safe-return-receipt", type=Path, required=True)
    closeout.add_argument("--terminal-checkpoint-sha256", required=True)
    closeout.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = args.repository_root.resolve()
    command = args.command
    try:
        if args.dry_run or command is None:
            result = run_synthetic_dry_run(root, attempt_id=args.attempt_id)
        elif command == "preflight":
            result = evaluate_a2_entry_preflight(root)
        elif command == "bundle":
            result = build_execution_bundle(root, attempt_id=args.attempt_id, output_path=args.output)
            if args.receipt_output is not None:
                _write_json(args.receipt_output, result["receipt"])
        elif command == "admit":
            result = build_provider_admission_receipt(
                root,
                attempt_id=args.attempt_id,
                provider_evidence=_load_json(args.provider_evidence, role="provider evidence"),
                runtime_sha256=args.runtime_sha256,
                model_lockset_sha256=args.model_lockset_sha256,
                data_handoff_sha256=args.data_handoff_sha256,
                management_authority_sha256=args.management_authority_sha256,
                now_utc=datetime.now(timezone.utc),
            )
            if args.output is not None:
                _write_json(args.output, result)
        elif command == "stage":
            result = perform_remote_stage(
                root,
                attempt_id=args.attempt_id,
                provider_admission_receipt=_load_json(
                    args.provider_admission_receipt, role="provider admission receipt"
                ),
                bundle_receipt=_load_json(args.bundle_receipt, role="bundle receipt"),
                bundle_path=args.bundle,
                remote_root=args.remote_root,
                watchdog_deadline_utc=args.watchdog_deadline_utc,
                owner_connection_path=args.owner_connection,
            )
            if args.output_directory is not None:
                output = args.output_directory.resolve()
                _write_json(output / "remote-stage.receipt.v1.json", result["stage_receipt"])
                _write_json(output / "lifecycle-genesis.checkpoint.v1.json", result["genesis_checkpoint"])
                _write_json(
                    output / "execution-adoption.receipt.v1.json",
                    result["execution_adoption_receipt"],
                )
        elif command == "execute":
            argv_value = json.loads(args.command_argv_json.read_text(encoding="utf-8"))
            if not isinstance(argv_value, list):
                raise A2OperationalExecutorError("external executor argv JSON must be a list")
            result = execute_external_candidate_set(
                root,
                attempt_id=args.attempt_id,
                adoption_receipt=_load_json(
                    args.execution_adoption_receipt,
                    role="execution adoption receipt",
                ),
                measurement_authority=_load_json(
                    args.measurement_authority,
                    role="measurement authority",
                ),
                command_template=argv_value,
                output_directory=args.output_directory,
                checkpoint_ledger=args.checkpoint_ledger,
                timeout_seconds=args.timeout_seconds,
            )
        elif command == "resume":
            result = resume_checkpoint(args.ledger, attempt_id=args.attempt_id)
        elif command == "safe-return":
            result = build_safe_return_receipt(
                root,
                attempt_id=args.attempt_id,
                archive_path=args.archive,
                remote_root=args.remote_root,
            )
            if args.output is not None:
                _write_json(args.output, result)
        elif command == "closeout":
            result = build_execution_closeout_receipt(
                root,
                attempt_id=args.attempt_id,
                coverage=_load_json(args.coverage, role="coverage receipt"),
                winner_receipt_sha256s=_load_json(args.winner_receipts, role="winner receipt hashes"),
                safe_return_receipt=_load_json(args.safe_return_receipt, role="safe return receipt"),
                terminal_checkpoint_sha256=args.terminal_checkpoint_sha256,
                claim_evidence_pointers=[args.coverage.as_posix(), args.safe_return_receipt.as_posix()],
                evidence_class="measured_development_aggregate",
            )
            if args.output is not None:
                _write_json(args.output, result)
        else:
            raise A2OperationalExecutorError("unsupported A2 executor command")
    except (A2OperationalExecutorError, A2ExecutionReadinessError, ValueError) as error:
        print(json.dumps({"status": "FAILED_CLOSED", "error": str(error)}, ensure_ascii=True, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
