"""Additive A1.2 v9 synthetic execution-lifecycle repair contract.

This module records only the binding and authorization boundary for the next
synthetic-only lifecycle repair.  It never opens a provider connection or
starts a worker.  Materialization fails closed until the separately owned v9
execution files are present.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from .a1_2_live_preflight_packaging_v8 import (
    CONTRACT_PATH as V8_CONTRACT_PATH,
    RECEIPT_PATH as V8_RECEIPT_PATH,
    validate_revision as validate_v8,
)


REVISION_ID = "a1.2-live-preflight-execution-lifecycle-v9"
CONTRACT_PATH = Path(
    "control/armindex/a1.2/execution-contract.live-preflight-execution-lifecycle.v9.json"
)
RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-live-preflight-execution-lifecycle.receipt.v9.json"
)
SCHEMA_PATH = Path("schemas/armindex/a1.2-live-preflight-execution-lifecycle.v9.json")
CONTINUATION_POLICY_PATH = Path(
    "control/armindex/a1.2/owner-instance-continuation-policy.v1.json"
)
EXECUTION_MODULE_PATH = Path(
    "src/myis_research/armindex/a1_2_live_preflight_execution_v9.py"
)
RUNTIME_MODULE_PATH = Path(
    "src/myis_research/armindex/a1_2_live_preflight_runtime_v9.py"
)
LAUNCHER_PATH = Path("scripts/a1_2_vast/remote-live-preflight-v9.sh")
COORDINATOR_PATH = Path("scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinatorV9.ps1")
BOOTSTRAP_PATH = Path("scripts/a1_2_vast/remote-bootstrap-direct-base-v9.sh")
RUNBOOK_PATH = Path("docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V9.md")

DEPENDENT_PATHS = (
    RUNTIME_MODULE_PATH,
    LAUNCHER_PATH,
    COORDINATOR_PATH,
    BOOTSTRAP_PATH,
    RUNBOOK_PATH,
)
BINDING_PATHS = (
    V8_CONTRACT_PATH,
    V8_RECEIPT_PATH,
    CONTINUATION_POLICY_PATH,
    EXECUTION_MODULE_PATH,
    RUNTIME_MODULE_PATH,
    LAUNCHER_PATH,
    COORDINATOR_PATH,
    BOOTSTRAP_PATH,
    RUNBOOK_PATH,
    SCHEMA_PATH,
)


class ExecutionLifecycleV9Error(ValueError):
    """Raised when v9 cannot prove its additive lifecycle boundary."""


ATTEMPT_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
STEP_RE = re.compile(r"^[a-z][a-z0-9_-]{1,79}$")
LIFECYCLE_STATUSES = frozenset({"RUNNING", "FAILED", "COMPLETE"})
MARKER_SCHEMA = "myis.armindex-a1.2-live-preflight-verification-marker.v9"
IMAGE_DIGEST = "sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20"
SAFE_EXPORT_PREFIXES = (
    "attempt.json",
    "state.json",
    "summary.json",
    "preflight/adapters/",
    "runtime-receipts/",
    "failure-receipts/",
    "steps/",
    "heartbeats/",
    "processes/",
    "process-exits/",
    "logs/",
)
FORBIDDEN_EXPORT_FRAGMENT = re.compile(
    r"qrels|membership|query[_-]?ids|id_rsa|id_ed25519|credential|provider_payload|protected[_-]?evaluator",
    re.IGNORECASE,
)


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _load(root: Path, path: Path) -> dict[str, Any]:
    value = json.loads((root / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ExecutionLifecycleV9Error(f"JSON object required: {path.as_posix()}")
    return value


def _self_hash(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    body = dict(value)
    body[field] = canonical_sha256(body)
    return body


def _require_dependencies(root: Path) -> None:
    missing = [path.as_posix() for path in DEPENDENT_PATHS if not (root / path).is_file()]
    if missing:
        raise ExecutionLifecycleV9Error(
            "v9 lifecycle implementation is not ready; missing hash-bound dependency: "
            + ", ".join(missing)
        )


def _bindings(root: Path) -> list[dict[str, str]]:
    return [{"uri": path.as_posix(), "sha256": file_sha256(root / path)} for path in BINDING_PATHS]


def _validate_continuation_policy(policy: Mapping[str, Any]) -> None:
    if policy.get("schema_version") != "myis.armindex-a1.2-owner-instance-continuation-policy.v1":
        raise ExecutionLifecycleV9Error("v9 continuation policy schema mismatch")
    if policy.get("launch_allowed") is not False:
        raise ExecutionLifecycleV9Error("v9 continuation policy cannot permit launch")
    counters = policy.get("measured_counters")
    if not isinstance(counters, Mapping) or any(value != 0 for value in counters.values()):
        raise ExecutionLifecycleV9Error("v9 continuation policy counters must remain zero")


def _write_new(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise ExecutionLifecycleV9Error(f"immutable v9 artifact differs: {path.as_posix()}")
    if not path.exists():
        path.write_text(text, encoding="utf-8", newline="")


def materialize_revision(repository_root: Path) -> dict[str, Any]:
    """Materialize v9 only after the bound lifecycle implementation exists."""

    root = repository_root.resolve()
    validate_v8(root)
    _require_dependencies(root)
    policy = _load(root, CONTINUATION_POLICY_PATH)
    _validate_continuation_policy(policy)
    v8_receipt = _load(root, V8_RECEIPT_PATH)
    bindings = _bindings(root)
    contract = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-execution-contract.live-preflight-execution-lifecycle.v9",
            "contract_id": REVISION_ID,
            "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
            "task_id": "A1.2",
            "status": "execution_lifecycle_repair_prepared_preflight_pending",
            "evidence_class": "live_engineering_preflight_execution_lifecycle_repair",
            "scientific_authority": False,
            "claim_boundary": "synthetic execution-lifecycle repair only; no measured retrieval or scientific result",
            "migration_from": {
                "uri": V8_RECEIPT_PATH.as_posix(),
                "sha256": v8_receipt["receipt_sha256"],
                "disposition": "preserved_immutable_additive_v8_lifecycle_repair",
            },
            "continuation_policy": {
                "uri": CONTINUATION_POLICY_PATH.as_posix(),
                "sha256": file_sha256(root / CONTINUATION_POLICY_PATH),
                "default_post_preflight_instruction": policy["default_post_preflight_instruction"],
            },
            "active_correction": {
                "fresh_remote_root": "/opt/myis/a1.2-v9",
                "source_remote_root": "/opt/myis/a1.2-v7",
                "same_instance_reuse": True,
                "synthetic_preflight_only": True,
                "required_lifecycle_controls": [
                    "coordinated_failure_cancellation_and_reaping",
                    "checkpoint_records_completed_work_only",
                    "retry_safe_run_root_and_receipts",
                    "idempotent_safe_export_with_local_hash_validation",
                    "status_reports_liveness_exit_and_gpu_processes",
                    "owner_local_ttl_and_provider_destruction_proof_pending",
                ],
                "implementation_validation_complete": True,
                "live_preflight_execution_pending": True,
            },
            "launch_allowed": False,
            "adopted_for_execution": False,
            "measured_retrieval_allowed": False,
            "synthetic_preflight_only": True,
            "real_counters": {
                "measured_runs": 0,
                "candidate_count": 0,
                "selection_accesses": 0,
                "final_accesses": 0,
            },
            "resource_counters": {
                "charged_usd": 0,
                "gpu_scientific_runs": 0,
                "model_downloads": 0,
                "paid_api_calls": 0,
            },
            "bindings": bindings,
            "next_authorized_action": "Run only the v9 synthetic execution-lifecycle preflight after all bound implementation checks pass; launch adoption and measured retrieval remain closed.",
        },
        "contract_sha256",
    )
    _write_new(root / CONTRACT_PATH, _json_text(contract))
    receipt = _self_hash(
        {
            "schema_version": "myis.armindex-a1.2-live-preflight-execution-lifecycle.v9",
            "receipt_id": REVISION_ID,
            "revision_id": REVISION_ID,
            "status": contract["status"],
            "evidence_class": contract["evidence_class"],
            "scientific_authority": False,
            "claim_boundary": contract["claim_boundary"],
            "contract_sha256": file_sha256(root / CONTRACT_PATH),
            "v8_receipt_sha256": v8_receipt["receipt_sha256"],
            "continuation_policy_sha256": file_sha256(root / CONTINUATION_POLICY_PATH),
            "new_remote_root": contract["active_correction"]["fresh_remote_root"],
            "implementation_validation_complete": True,
            "live_preflight_execution_pending": True,
            "launch_allowed": False,
            "adopted_for_execution": False,
            "measured_runs": 0,
            "selection_accesses": 0,
            "final_accesses": 0,
            "charged_usd": 0,
            "bindings": bindings,
        },
        "receipt_sha256",
    )
    _write_new(root / RECEIPT_PATH, _json_text(receipt))
    return validate_revision(root)


def validate_revision(repository_root: Path) -> dict[str, Any]:
    """Validate v8 lineage, v9 bindings, and the launch-locked counters."""

    root = repository_root.resolve()
    validate_v8(root)
    _require_dependencies(root)
    contract = _load(root, CONTRACT_PATH)
    receipt = _load(root, RECEIPT_PATH)
    schema = _load(root, SCHEMA_PATH)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        raise ExecutionLifecycleV9Error(f"v9 receipt schema failure: {errors[0].message}")
    for payload, field in ((contract, "contract_sha256"), (receipt, "receipt_sha256")):
        body = dict(payload)
        if body.pop(field, None) != canonical_sha256(body):
            raise ExecutionLifecycleV9Error(f"v9 {field} mismatch")
    for binding in contract.get("bindings", []):
        if file_sha256(root / str(binding["uri"])) != binding["sha256"]:
            raise ExecutionLifecycleV9Error(f"v9 binding mismatch: {binding['uri']}")
    policy = _load(root, CONTINUATION_POLICY_PATH)
    _validate_continuation_policy(policy)
    v8_receipt = _load(root, V8_RECEIPT_PATH)
    if (
        receipt.get("contract_sha256") != file_sha256(root / CONTRACT_PATH)
        or receipt.get("v8_receipt_sha256") != v8_receipt.get("receipt_sha256")
        or receipt.get("continuation_policy_sha256") != file_sha256(root / CONTINUATION_POLICY_PATH)
    ):
        raise ExecutionLifecycleV9Error("v9 receipt lineage binding mismatch")
    for payload in (contract, receipt):
        if payload.get("launch_allowed") is not False or payload.get("adopted_for_execution") is not False:
            raise ExecutionLifecycleV9Error("v9 cannot authorize launch or adoption")
    counters = contract.get("real_counters", {})
    resources = contract.get("resource_counters", {})
    if any(value != 0 for value in counters.values()) or any(value != 0 for value in resources.values()):
        raise ExecutionLifecycleV9Error("v9 contract counters must remain zero")
    if any(receipt.get(key) != 0 for key in ("measured_runs", "selection_accesses", "final_accesses", "charged_usd")):
        raise ExecutionLifecycleV9Error("v9 receipt counters must remain zero")
    return {
        "status": receipt["status"],
        "revision_id": REVISION_ID,
        "contract_sha256": contract["contract_sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
        "charged_usd": 0,
    }


def _atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("xb") as handle:
        handle.write(_json_text(value).encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _attempt_directory(output_root: Path, attempt_id: str) -> Path:
    if not ATTEMPT_RE.fullmatch(attempt_id):
        raise ExecutionLifecycleV9Error("attempt_id is invalid")
    root = output_root.resolve()
    directory = (root / "attempts" / attempt_id).resolve()
    try:
        directory.relative_to(root)
    except ValueError as error:
        raise ExecutionLifecycleV9Error("attempt path escapes output root") from error
    return directory


def _read_lifecycle(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ExecutionLifecycleV9Error(f"invalid lifecycle JSON: {path}") from error
    if not isinstance(value, dict):
        raise ExecutionLifecycleV9Error(f"lifecycle JSON object required: {path}")
    return value


def _checked(path: Path, field: str, label: str) -> dict[str, Any]:
    value = _read_lifecycle(path)
    body = dict(value)
    if body.pop(field, None) != canonical_sha256(body):
        raise ExecutionLifecycleV9Error(f"{label} self-hash mismatch")
    return value


def _attempt_record(directory: Path, attempt_id: str) -> dict[str, Any]:
    value = _checked(directory / "attempt.json", "attempt_sha256", "attempt record")
    if value.get("attempt_id") != attempt_id:
        raise ExecutionLifecycleV9Error("attempt identity mismatch")
    return value


def _attempt_state(directory: Path, attempt_id: str) -> dict[str, Any]:
    value = _checked(directory / "state.json", "state_sha256", "attempt state")
    if value.get("attempt_id") != attempt_id or value.get("status") not in LIFECYCLE_STATUSES:
        raise ExecutionLifecycleV9Error("attempt state binding mismatch")
    return value


def _verification_marker(path: Path) -> dict[str, Any]:
    value = _checked(path, "marker_sha256", "v8 verification marker")
    required = {
        "schema_version": MARKER_SCHEMA,
        "status": "PASS",
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_retrieval": False,
    }
    if any(value.get(key) != expected for key, expected in required.items()):
        raise ExecutionLifecycleV9Error("v8 verification marker is not a launch-locked PASS")
    return value


def initialize_attempt(output_root: Path, attempt_id: str, v8_marker_path: Path) -> dict[str, Any]:
    """Create a new immutable attempt or reuse only the exact same marker binding."""

    directory = _attempt_directory(output_root, attempt_id)
    marker = _verification_marker(v8_marker_path)
    marker_sha256 = marker["marker_sha256"]
    if directory.exists():
        existing = _attempt_record(directory, attempt_id)
        if existing.get("v8_marker_sha256") != marker_sha256:
            raise ExecutionLifecycleV9Error("retry requires the same attempt identity and v8 marker")
        return {"attempt_id": attempt_id, "status": _attempt_state(directory, attempt_id)["status"]}
    directory.mkdir(parents=True, exist_ok=False)
    attempt_unsigned = {
        "schema_version": "myis.armindex-a1.2-live-attempt.v9",
        "attempt_id": attempt_id,
        "v8_marker_sha256": marker_sha256,
        "v8_identity": {key: marker[key] for key in ("git_commit", "git_tree", "manifest_digest", "bundle_sha256")},
        "synthetic_preflight_only": True,
        "measured_retrieval": False,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    state_unsigned = {
        "schema_version": "myis.armindex-a1.2-live-attempt-state.v9",
        "attempt_id": attempt_id,
        "status": "RUNNING",
        "sequence": 1,
        "reason": "initialized",
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    _atomic_write(directory / "attempt.json", {**attempt_unsigned, "attempt_sha256": canonical_sha256(attempt_unsigned)})
    _atomic_write(directory / "state.json", {**state_unsigned, "state_sha256": canonical_sha256(state_unsigned)})
    return {"attempt_id": attempt_id, "status": "RUNNING", "v8_marker_sha256": marker_sha256}


def _durable_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise ExecutionLifecycleV9Error(f"durable artifact must be a regular file: {path}")
    with path.open("rb+") as handle:
        while handle.read(1024 * 1024):
            pass
        os.fsync(handle.fileno())
    return file_sha256(path)


def complete_step(output_root: Path, attempt_id: str, step_id: str, artifacts: Sequence[Path]) -> dict[str, Any]:
    """Write a COMPLETE checkpoint only after the declared work is durable."""

    if not STEP_RE.fullmatch(step_id):
        raise ExecutionLifecycleV9Error("step_id is invalid")
    directory = _attempt_directory(output_root, attempt_id)
    _attempt_record(directory, attempt_id)
    if _attempt_state(directory, attempt_id)["status"] != "RUNNING":
        raise ExecutionLifecycleV9Error("only a RUNNING attempt may checkpoint work")
    rows = []
    for artifact in sorted({path.resolve() for path in artifacts}):
        try:
            relative = artifact.relative_to(directory)
        except ValueError as error:
            raise ExecutionLifecycleV9Error("checkpoint artifact is outside the attempt") from error
        rows.append({"uri": relative.as_posix(), "sha256": _durable_file(artifact)})
    if not rows:
        raise ExecutionLifecycleV9Error("checkpoint requires durable artifacts")
    target = directory / "steps" / f"{step_id}.json"
    unsigned = {
        "schema_version": "myis.armindex-a1.2-live-step-checkpoint.v9",
        "attempt_id": attempt_id,
        "step_id": step_id,
        "status": "COMPLETE",
        "artifacts": rows,
        "completed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    value = {**unsigned, "checkpoint_sha256": canonical_sha256(unsigned)}
    if target.exists():
        prior = _read_lifecycle(target)
        comparable = {key: item for key, item in prior.items() if key not in {"completed_at", "checkpoint_sha256"}}
        expected = {key: item for key, item in value.items() if key not in {"completed_at", "checkpoint_sha256"}}
        if comparable != expected:
            raise ExecutionLifecycleV9Error("checkpoint already records different work")
        return prior
    _atomic_write(target, value)
    return value


def linux_proc_start_time(pid: int, proc_root: Path = Path("/proc")) -> str:
    if pid < 1:
        raise ExecutionLifecycleV9Error("pid must be positive")
    try:
        text = (proc_root / str(pid) / "stat").read_text(encoding="utf-8")
        fields = text[text.rfind(")") + 2 :].split()
        return fields[19]
    except (OSError, IndexError) as error:
        raise ExecutionLifecycleV9Error(f"Linux /proc start-time unavailable for pid {pid}") from error


def record_process(output_root: Path, attempt_id: str, pid: int, proc_root: Path = Path("/proc")) -> dict[str, Any]:
    directory = _attempt_directory(output_root, attempt_id)
    _attempt_record(directory, attempt_id)
    if _attempt_state(directory, attempt_id)["status"] != "RUNNING":
        raise ExecutionLifecycleV9Error("only a RUNNING attempt may register a process")
    unsigned = {
        "schema_version": "myis.armindex-a1.2-live-process.v9",
        "attempt_id": attempt_id,
        "pid": pid,
        "linux_proc_start_time": linux_proc_start_time(pid, proc_root),
        "recorded_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    value = {**unsigned, "process_sha256": canonical_sha256(unsigned)}
    _atomic_write(directory / "processes" / f"{pid}.json", value)
    return value


def _verified_process(directory: Path, attempt_id: str, pid: int, proc_root: Path) -> dict[str, Any]:
    value = _checked(directory / "processes" / f"{pid}.json", "process_sha256", "process record")
    if value.get("attempt_id") != attempt_id or linux_proc_start_time(pid, proc_root) != value.get("linux_proc_start_time"):
        raise ExecutionLifecycleV9Error("process identity changed or pid was reused")
    return value


def heartbeat(output_root: Path, attempt_id: str, pid: int, proc_root: Path = Path("/proc")) -> dict[str, Any]:
    directory = _attempt_directory(output_root, attempt_id)
    process = _verified_process(directory, attempt_id, pid, proc_root)
    unsigned = {
        "schema_version": "myis.armindex-a1.2-live-heartbeat.v9",
        "attempt_id": attempt_id,
        "pid": pid,
        "linux_proc_start_time": process["linux_proc_start_time"],
        "status": "RUNNING",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    value = {**unsigned, "heartbeat_sha256": canonical_sha256(unsigned)}
    _atomic_write(directory / "heartbeats" / f"{pid}.json", value)
    return value


def attempt_status(output_root: Path, attempt_id: str, *, proc_root: Path = Path("/proc"), maximum_heartbeat_age_seconds: float = 90.0) -> dict[str, Any]:
    directory = _attempt_directory(output_root, attempt_id)
    state = _attempt_state(directory, attempt_id)
    pids = []
    if state["status"] == "RUNNING":
        records = sorted((directory / "processes").glob("*.json"))
        if not records:
            raise ExecutionLifecycleV9Error("RUNNING attempt has no registered process")
        now = time.time()
        for record_path in records:
            pid = int(record_path.stem)
            _verified_process(directory, attempt_id, pid, proc_root)
            beat = _checked(directory / "heartbeats" / f"{pid}.json", "heartbeat_sha256", "heartbeat")
            if beat.get("attempt_id") != attempt_id:
                raise ExecutionLifecycleV9Error("heartbeat attempt binding mismatch")
            age = now - datetime.fromisoformat(beat["generated_at"].replace("Z", "+00:00")).timestamp()
            if age > maximum_heartbeat_age_seconds:
                raise ExecutionLifecycleV9Error("heartbeat is stale")
            pids.append(pid)
    return {"attempt_id": attempt_id, "status": state["status"], "verified_pids": pids}


def _set_state(directory: Path, attempt_id: str, status: str, reason: str) -> dict[str, Any]:
    prior = _attempt_state(directory, attempt_id)
    unsigned = {
        "schema_version": "myis.armindex-a1.2-live-attempt-state.v9",
        "attempt_id": attempt_id,
        "status": status,
        "sequence": int(prior["sequence"]) + 1,
        "reason": reason,
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    value = {**unsigned, "state_sha256": canonical_sha256(unsigned)}
    _atomic_write(directory / "state.json", value)
    return value


def complete_attempt(output_root: Path, attempt_id: str, summary_path: Path) -> dict[str, Any]:
    directory = _attempt_directory(output_root, attempt_id)
    record = _attempt_record(directory, attempt_id)
    if _attempt_state(directory, attempt_id)["status"] != "RUNNING" or summary_path.resolve() != (directory / "summary.json").resolve():
        raise ExecutionLifecycleV9Error("completion requires the canonical same-attempt RUNNING summary")
    summary = _read_lifecycle(summary_path)
    if summary.get("status") != "PASS" or summary.get("attempt_id") != attempt_id or summary.get("v8_marker_sha256") != record["v8_marker_sha256"]:
        raise ExecutionLifecycleV9Error("completion summary is not same-attempt marker-bound PASS")
    _durable_file(summary_path)
    return _set_state(directory, attempt_id, "COMPLETE", "same_attempt_pass_summary_durable")


def teardown_attempt(output_root: Path, attempt_id: str, *, proc_root: Path = Path("/proc"), timeout_seconds: float = 10.0) -> dict[str, Any]:
    directory = _attempt_directory(output_root, attempt_id)
    _attempt_record(directory, attempt_id)
    terminated = []
    for record_path in sorted((directory / "processes").glob("*.json")):
        pid = int(record_path.stem)
        _verified_process(directory, attempt_id, pid, proc_root)
        os.kill(pid, signal.SIGTERM)
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline and (proc_root / str(pid)).exists():
            time.sleep(0.05)
        if (proc_root / str(pid)).exists():
            _verified_process(directory, attempt_id, pid, proc_root)
            os.kill(pid, signal.SIGKILL)
        terminated.append(pid)
    _set_state(directory, attempt_id, "FAILED", "verified_processes_terminated")
    return {"attempt_id": attempt_id, "status": "FAILED", "terminated_pids": terminated}


def build_safe_export(output_root: Path, attempt_id: str, archive_path: Path) -> dict[str, Any]:
    """Create a retry-safe archive only after same-attempt PASS completion."""

    directory = _attempt_directory(output_root, attempt_id)
    record = _attempt_record(directory, attempt_id)
    if _attempt_state(directory, attempt_id)["status"] != "COMPLETE":
        raise ExecutionLifecycleV9Error("safe export requires COMPLETE attempt")
    summary = _read_lifecycle(directory / "summary.json")
    if summary.get("status") != "PASS" or summary.get("attempt_id") != attempt_id or summary.get("v8_marker_sha256") != record["v8_marker_sha256"]:
        raise ExecutionLifecycleV9Error("safe export requires same-attempt marker-bound PASS summary")
    archive = archive_path.resolve()
    try:
        archive.relative_to(directory)
    except ValueError as error:
        raise ExecutionLifecycleV9Error("safe export archive must remain under the attempt") from error
    receipt_path = archive.with_suffix(archive.suffix + ".receipt.json")
    if archive.is_file() and receipt_path.is_file():
        receipt = _checked(receipt_path, "receipt_sha256", "safe export receipt")
        if receipt.get("attempt_id") == attempt_id and receipt.get("archive_sha256") == file_sha256(archive):
            return receipt
        raise ExecutionLifecycleV9Error("existing archive does not match its attempt")
    files = sorted(path for path in directory.rglob("*") if path.is_file() and path not in {archive, receipt_path})
    members = [{"uri": path.relative_to(directory).as_posix(), "sha256": _durable_file(path)} for path in files]
    manifest_unsigned = {"schema_version": "myis.armindex-a1.2-live-safe-export-members.v9", "attempt_id": attempt_id, "v8_marker_sha256": record["v8_marker_sha256"], "members": members}
    manifest = {**manifest_unsigned, "members_sha256": canonical_sha256(manifest_unsigned)}
    manifest_path = directory / "safe-export-members.v9.json"
    _atomic_write(manifest_path, manifest)
    temporary = archive.with_name(f".{archive.name}.{os.getpid()}.tmp")
    archive.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(temporary, "w:gz") as tar:
        for path in sorted([*files, manifest_path]):
            tar.add(path, arcname=path.relative_to(directory).as_posix(), recursive=False)
    os.replace(temporary, archive)
    receipt_unsigned = {"schema_version": "myis.armindex-a1.2-live-safe-export-receipt.v9", "attempt_id": attempt_id, "status": "PASS", "v8_marker_sha256": record["v8_marker_sha256"], "members_manifest_sha256": manifest["members_sha256"], "archive_sha256": file_sha256(archive), "archive_bytes": archive.stat().st_size}
    receipt = {**receipt_unsigned, "receipt_sha256": canonical_sha256(receipt_unsigned)}
    _atomic_write(receipt_path, receipt)
    return receipt


def measure_qwen_max_length(adapter: Any, *, pooling_sha256: str, torch_module: Any, candidate_token_counts: Sequence[int] = (8192, 16384, 32768)) -> dict[str, Any]:
    """Use only frozen SentenceTransformer ``encode`` with locked query formatting."""

    if not re.fullmatch(r"[a-f0-9]{64}", pooling_sha256):
        raise ExecutionLifecycleV9Error("Qwen pooling hash is required")
    query = "Instruct: Retrieve patent families containing technical information relevant to prior-art search for the query patent family.\nQuery:synthetic cooling power converter thermal housing"
    passed, oom_ceiling, attempts = 0, None, []
    for count in candidate_token_counts:
        torch_module.cuda.empty_cache()
        adapter.max_seq_length = count
        try:
            output = adapter.encode([query], batch_size=1, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
            if getattr(output, "ndim", 0) != 2 or output.shape[0] != 1:
                raise ExecutionLifecycleV9Error("Qwen SentenceTransformer encode shape is invalid")
            passed = count
            attempts.append({"token_count": count, "status": "PASS"})
        except Exception as error:
            if "out of memory" not in str(error).casefold():
                raise
            oom_ceiling = count
            attempts.append({"token_count": count, "status": "OOM"})
            torch_module.cuda.empty_cache()
            break
    if not passed:
        raise ExecutionLifecycleV9Error("Qwen did not complete the minimum synthetic encode")
    return {"schema_version": "myis.armindex-a1.2-qwen-adapter-measurement.v9", "adapter_path": "SentenceTransformer.encode", "formatting_sha256": canonical_sha256({"query": query, "normalization": "l2", "adapter": "SentenceTransformer.encode"}), "pooling_sha256": pooling_sha256, "normalization": "l2", "max_completed_token_count": passed, "oom_ceiling_token_count": oom_ceiling, "peak_vram_bytes": int(torch_module.cuda.max_memory_allocated()), "attempts": attempts, "synthetic_text_only": True, "measured_retrieval": False}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myis-a1.2-live-preflight-execution-v9")
    parser.add_argument("command", choices=("materialize", "validate"))
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "materialize":
        result = materialize_revision(args.repository_root)
    else:
        result = validate_revision(args.repository_root)
    print(_json_text(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
