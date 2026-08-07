"""Attempt-scoped synthetic A1.2 live preflight runtime for revision v9.

This module is deliberately separate from the immutable v1-v8 lineage. It
accepts only synthetic inputs, Owner-staged local model bytes, and a validated
v9 verification marker. It cannot authorize measured retrieval.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import re
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from ..kernel.canonical import canonical_sha256, file_sha256


REVISION_ID = "a1.2-live-preflight-execution-lifecycle-v9"
MARKER_SCHEMA = "myis.armindex-a1.2-live-preflight-verification-marker.v9"
IMAGE_DIGEST = "sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20"
ATTEMPT_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
IDENTITY_RE = re.compile(r"^[a-f0-9]{40,64}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
ROLE_RE = re.compile(r"^[a-z][a-z0-9_-]{1,79}$")
STATUSES = frozenset({"RUNNING", "FAILED", "COMPLETE"})
ARMS = ("ARM-02", "ARM-03", "ARM-04", "ARM-05")
L2_NORMALIZATION_ATOL = 1e-3
ARM_CONFIG_OVERRIDES: dict[str, dict[str, Any]] = {
    "ARM-04": {
        "attn_implementation": "sdpa",
        "unpad_inputs": False,
        "use_memory_efficient_attention": False,
    }
}
SAFE_EXPORT_PREFIXES = (
    "attempt.json",
    "state.json",
    "summary.json",
    "teardown.json",
    "preflight/adapters/",
    "runtime-receipts/",
    "failure-receipts/",
    "worker-artifacts/",
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


class LiveRuntimeV9Error(ValueError):
    """Raised when a v9 runtime invariant cannot be proven."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _atomic_write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("xb") as handle:
        handle.write(_json_text(value).encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _write_immutable(path: Path, value: Mapping[str, Any]) -> None:
    text = _json_text(value)
    if path.exists():
        if not path.is_file() or path.is_symlink() or path.read_text(encoding="utf-8") != text:
            raise LiveRuntimeV9Error(f"immutable artifact differs: {path}")
        return
    _atomic_write(path, value)


def _read(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise LiveRuntimeV9Error(f"required regular JSON file is missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise LiveRuntimeV9Error(f"JSON object required: {path}")
    return value


def _checked(path: Path, field: str, label: str) -> dict[str, Any]:
    value = _read(path)
    body = dict(value)
    if body.pop(field, None) != canonical_sha256(body):
        raise LiveRuntimeV9Error(f"{label} self-hash mismatch")
    return value


def write_verification_marker(
    path: Path,
    *,
    expected_commit: str,
    expected_tree: str,
    expected_manifest_digest: str,
    expected_bundle_sha256: str,
    runtime_identity_path: Path,
) -> dict[str, Any]:
    identity = _checked(runtime_identity_path, "receipt_sha256", "runtime identity")
    if not IDENTITY_RE.fullmatch(expected_commit) or not IDENTITY_RE.fullmatch(expected_tree):
        raise LiveRuntimeV9Error("verification marker Git identity is invalid")
    if not SHA256_RE.fullmatch(expected_bundle_sha256):
        raise LiveRuntimeV9Error("verification marker bundle SHA-256 is invalid")
    if expected_manifest_digest != IMAGE_DIGEST:
        raise LiveRuntimeV9Error("verification marker image digest drifted")
    if (
        identity.get("status") != "PASS"
        or identity.get("expected_manifest_digest") != expected_manifest_digest
        or identity.get("bundle_sha256") != expected_bundle_sha256
    ):
        raise LiveRuntimeV9Error("runtime identity is not bound to the marker request")
    unsigned = {
        "schema_version": MARKER_SCHEMA,
        "status": "PASS",
        "revision_id": REVISION_ID,
        "git_commit": expected_commit,
        "git_tree": expected_tree,
        "manifest_digest": expected_manifest_digest,
        "bundle_sha256": expected_bundle_sha256,
        "runtime_identity_sha256": file_sha256(runtime_identity_path),
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_retrieval": False,
        "generated_at": _utc_now(),
    }
    value = {**unsigned, "marker_sha256": canonical_sha256(unsigned)}
    if path.exists():
        prior = _checked(path, "marker_sha256", "verification marker")
        stable = ("git_commit", "git_tree", "manifest_digest", "bundle_sha256", "runtime_identity_sha256")
        if any(prior.get(key) != value.get(key) for key in stable):
            raise LiveRuntimeV9Error("existing verification marker binds different bytes")
        return prior
    _write_immutable(path, value)
    return value


def validate_verification_marker(
    path: Path,
    *,
    expected_commit: str | None = None,
    expected_tree: str | None = None,
    expected_manifest_digest: str | None = None,
    expected_bundle_sha256: str | None = None,
) -> dict[str, Any]:
    value = _checked(path, "marker_sha256", "verification marker")
    required = {
        "schema_version": MARKER_SCHEMA,
        "status": "PASS",
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_retrieval": False,
    }
    if any(value.get(key) != expected for key, expected in required.items()):
        raise LiveRuntimeV9Error("verification marker is not a launch-locked PASS")
    requested = {
        "git_commit": expected_commit,
        "git_tree": expected_tree,
        "manifest_digest": expected_manifest_digest,
        "bundle_sha256": expected_bundle_sha256,
    }
    if any(expected is not None and value.get(key) != expected for key, expected in requested.items()):
        raise LiveRuntimeV9Error("verification marker identity mismatch")
    return value


def _attempt_directory(output_root: Path, attempt_id: str) -> Path:
    if not ATTEMPT_RE.fullmatch(attempt_id):
        raise LiveRuntimeV9Error("attempt_id is invalid")
    root = output_root.resolve()
    directory = (root / "attempts" / attempt_id).resolve()
    if directory.parent != (root / "attempts").resolve():
        raise LiveRuntimeV9Error("attempt path escaped output root")
    return directory


def _attempt(directory: Path, attempt_id: str) -> dict[str, Any]:
    value = _checked(directory / "attempt.json", "attempt_sha256", "attempt record")
    if value.get("attempt_id") != attempt_id:
        raise LiveRuntimeV9Error("attempt identity mismatch")
    return value


def _state(directory: Path, attempt_id: str) -> dict[str, Any]:
    value = _checked(directory / "state.json", "state_sha256", "attempt state")
    if value.get("attempt_id") != attempt_id or value.get("status") not in STATUSES:
        raise LiveRuntimeV9Error("attempt state binding mismatch")
    return value


def initialize_attempt(output_root: Path, attempt_id: str, marker_path: Path) -> dict[str, Any]:
    directory = _attempt_directory(output_root, attempt_id)
    marker = validate_verification_marker(marker_path)
    if directory.exists():
        record = _attempt(directory, attempt_id)
        if record.get("verification_marker_sha256") != marker["marker_sha256"]:
            raise LiveRuntimeV9Error("retry requires the same attempt and marker")
        state = _state(directory, attempt_id)
        if state["status"] != "RUNNING":
            raise LiveRuntimeV9Error("a completed or failed attempt cannot restart")
        return {"attempt_id": attempt_id, "status": state["status"]}
    directory.mkdir(parents=True, exist_ok=False)
    attempt_unsigned = {
        "schema_version": "myis.armindex-a1.2-live-attempt.v9",
        "attempt_id": attempt_id,
        "verification_marker_sha256": marker["marker_sha256"],
        "identity": {key: marker[key] for key in ("git_commit", "git_tree", "manifest_digest", "bundle_sha256")},
        "synthetic_preflight_only": True,
        "measured_retrieval": False,
        "created_at": _utc_now(),
    }
    state_unsigned = {
        "schema_version": "myis.armindex-a1.2-live-attempt-state.v9",
        "attempt_id": attempt_id,
        "status": "RUNNING",
        "sequence": 1,
        "reason": "initialized",
        "updated_at": _utc_now(),
    }
    _write_immutable(directory / "attempt.json", {**attempt_unsigned, "attempt_sha256": canonical_sha256(attempt_unsigned)})
    _atomic_write(directory / "state.json", {**state_unsigned, "state_sha256": canonical_sha256(state_unsigned)})
    return {"attempt_id": attempt_id, "status": "RUNNING", "verification_marker_sha256": marker["marker_sha256"]}


def _set_state(directory: Path, attempt_id: str, status: str, reason: str) -> dict[str, Any]:
    if status not in STATUSES:
        raise LiveRuntimeV9Error("invalid lifecycle state")
    prior = _state(directory, attempt_id)
    unsigned = {
        "schema_version": "myis.armindex-a1.2-live-attempt-state.v9",
        "attempt_id": attempt_id,
        "status": status,
        "sequence": int(prior["sequence"]) + 1,
        "reason": reason,
        "updated_at": _utc_now(),
    }
    value = {**unsigned, "state_sha256": canonical_sha256(unsigned)}
    _atomic_write(directory / "state.json", value)
    return value


def _durable_hash(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise LiveRuntimeV9Error(f"durable artifact must be a regular file: {path}")
    with path.open("rb") as handle:
        while handle.read(1024 * 1024):
            pass
    return file_sha256(path)


def complete_step(output_root: Path, attempt_id: str, step_id: str, artifacts: Sequence[Path]) -> dict[str, Any]:
    if not ROLE_RE.fullmatch(step_id):
        raise LiveRuntimeV9Error("step_id is invalid")
    directory = _attempt_directory(output_root, attempt_id)
    _attempt(directory, attempt_id)
    if _state(directory, attempt_id)["status"] != "RUNNING":
        raise LiveRuntimeV9Error("only a RUNNING attempt may checkpoint")
    rows = []
    for artifact in sorted({path.resolve() for path in artifacts}):
        try:
            relative = artifact.relative_to(directory)
        except ValueError as error:
            raise LiveRuntimeV9Error("checkpoint artifact escaped the attempt") from error
        rows.append({"uri": relative.as_posix(), "sha256": _durable_hash(artifact)})
    if not rows:
        raise LiveRuntimeV9Error("checkpoint requires a durable artifact")
    target = directory / "steps" / f"{step_id}.json"
    unsigned = {
        "schema_version": "myis.armindex-a1.2-live-step-checkpoint.v9",
        "attempt_id": attempt_id,
        "step_id": step_id,
        "status": "COMPLETE",
        "artifacts": rows,
        "completed_at": _utc_now(),
    }
    value = {**unsigned, "checkpoint_sha256": canonical_sha256(unsigned)}
    if target.exists():
        prior = _checked(target, "checkpoint_sha256", "step checkpoint")
        if prior.get("status") != "COMPLETE" or prior.get("artifacts") != rows:
            raise LiveRuntimeV9Error("checkpoint already records different work")
        return prior
    _write_immutable(target, value)
    return value


def linux_proc_start_time(pid: int, proc_root: Path = Path("/proc")) -> str:
    if pid < 1:
        raise LiveRuntimeV9Error("pid must be positive")
    try:
        text = (proc_root / str(pid) / "stat").read_text(encoding="utf-8")
        fields = text[text.rfind(")") + 2 :].split()
        return fields[19]
    except (OSError, IndexError) as error:
        raise LiveRuntimeV9Error(f"Linux process start time is unavailable for pid {pid}") from error


def record_process(
    output_root: Path,
    attempt_id: str,
    pid: int,
    *,
    role: str,
    proc_root: Path = Path("/proc"),
) -> dict[str, Any]:
    if not ROLE_RE.fullmatch(role):
        raise LiveRuntimeV9Error("process role is invalid")
    directory = _attempt_directory(output_root, attempt_id)
    _attempt(directory, attempt_id)
    if _state(directory, attempt_id)["status"] != "RUNNING":
        raise LiveRuntimeV9Error("only a RUNNING attempt may register a process")
    unsigned = {
        "schema_version": "myis.armindex-a1.2-live-process.v9",
        "attempt_id": attempt_id,
        "pid": pid,
        "role": role,
        "linux_proc_start_time": linux_proc_start_time(pid, proc_root),
        "recorded_at": _utc_now(),
    }
    value = {**unsigned, "process_sha256": canonical_sha256(unsigned)}
    _write_immutable(directory / "processes" / f"{pid}.json", value)
    return value


def _verified_process(directory: Path, attempt_id: str, pid: int, proc_root: Path) -> dict[str, Any]:
    value = _checked(directory / "processes" / f"{pid}.json", "process_sha256", "process record")
    if value.get("attempt_id") != attempt_id or linux_proc_start_time(pid, proc_root) != value.get("linux_proc_start_time"):
        raise LiveRuntimeV9Error("process identity changed or pid was reused")
    return value


def heartbeat(output_root: Path, attempt_id: str, pid: int, proc_root: Path = Path("/proc")) -> dict[str, Any]:
    directory = _attempt_directory(output_root, attempt_id)
    process = _verified_process(directory, attempt_id, pid, proc_root)
    unsigned = {
        "schema_version": "myis.armindex-a1.2-live-heartbeat.v9",
        "attempt_id": attempt_id,
        "pid": pid,
        "role": process["role"],
        "linux_proc_start_time": process["linux_proc_start_time"],
        "status": "RUNNING",
        "generated_at": _utc_now(),
    }
    value = {**unsigned, "heartbeat_sha256": canonical_sha256(unsigned)}
    _atomic_write(directory / "heartbeats" / f"{pid}.json", value)
    return value


def record_process_exit(output_root: Path, attempt_id: str, pid: int, exit_code: int) -> dict[str, Any]:
    directory = _attempt_directory(output_root, attempt_id)
    process = _checked(directory / "processes" / f"{pid}.json", "process_sha256", "process record")
    unsigned = {
        "schema_version": "myis.armindex-a1.2-live-process-exit.v9",
        "attempt_id": attempt_id,
        "pid": pid,
        "role": process["role"],
        "linux_proc_start_time": process["linux_proc_start_time"],
        "exit_code": exit_code,
        "status": "PASS" if exit_code == 0 else "FAIL",
        "recorded_at": _utc_now(),
    }
    value = {**unsigned, "process_exit_sha256": canonical_sha256(unsigned)}
    _write_immutable(directory / "process-exits" / f"{pid}.json", value)
    return value


def attempt_status(
    output_root: Path,
    attempt_id: str,
    *,
    proc_root: Path = Path("/proc"),
    maximum_heartbeat_age_seconds: float = 90.0,
    require_pass: bool = False,
) -> dict[str, Any]:
    directory = _attempt_directory(output_root, attempt_id)
    state = _state(directory, attempt_id)
    active: list[dict[str, Any]] = []
    blockers: list[str] = []
    if state["status"] == "RUNNING":
        now = time.time()
        for record_path in sorted((directory / "processes").glob("*.json")):
            pid = int(record_path.stem)
            if (directory / "process-exits" / f"{pid}.json").is_file():
                continue
            try:
                process = _verified_process(directory, attempt_id, pid, proc_root)
                beat = _checked(directory / "heartbeats" / f"{pid}.json", "heartbeat_sha256", "heartbeat")
                age = now - datetime.fromisoformat(beat["generated_at"].replace("Z", "+00:00")).timestamp()
                if age < 0 or age > maximum_heartbeat_age_seconds:
                    blockers.append(f"stale_heartbeat:{pid}")
                active.append({"pid": pid, "role": process["role"], "heartbeat_age_seconds": round(age, 3)})
            except LiveRuntimeV9Error:
                blockers.append(f"process_identity_or_heartbeat:{pid}")
    effective = "FAILED" if blockers else state["status"]
    if require_pass and effective != "COMPLETE":
        raise LiveRuntimeV9Error("same-attempt preflight is not COMPLETE")
    return {
        "schema_version": "myis.armindex-a1.2-live-status.v9",
        "attempt_id": attempt_id,
        "status": effective,
        "active_processes": active,
        "blockers": blockers,
        "generated_at": _utc_now(),
    }


def teardown_attempt(
    output_root: Path,
    attempt_id: str,
    *,
    proc_root: Path = Path("/proc"),
    children_reaped: bool = False,
) -> dict[str, Any]:
    """Record teardown only after the launcher has terminated and reaped children."""

    if not children_reaped:
        raise LiveRuntimeV9Error("teardown receipt requires launcher-confirmed child reaping")
    directory = _attempt_directory(output_root, attempt_id)
    _attempt(directory, attempt_id)
    receipt_path = directory / "teardown.json"
    if receipt_path.exists():
        return _checked(receipt_path, "teardown_sha256", "teardown receipt")
    prior_state = _state(directory, attempt_id)["status"]
    reaped: list[int] = []
    for record_path in sorted((directory / "processes").glob("*.json")):
        pid = int(record_path.stem)
        exit_record = _checked(
            directory / "process-exits" / f"{pid}.json", "process_exit_sha256", "process exit"
        )
        if exit_record.get("attempt_id") != attempt_id or exit_record.get("pid") != pid:
            raise LiveRuntimeV9Error("process exit is not bound to its attempt")
        if (proc_root / str(pid)).exists():
            raise LiveRuntimeV9Error("teardown receipt cannot precede process reaping")
        reaped.append(pid)
    final_state = prior_state
    if prior_state == "RUNNING":
        final_state = _set_state(directory, attempt_id, "FAILED", "verified_process_cleanup_before_completion")["status"]
    unsigned = {
        "schema_version": "myis.armindex-a1.2-live-teardown.v9",
        "attempt_id": attempt_id,
        "status": final_state,
        "children_reaped": True,
        "reaped_pids": reaped,
        "provider_destruction_proven": False,
        "generated_at": _utc_now(),
    }
    value = {**unsigned, "teardown_sha256": canonical_sha256(unsigned)}
    _write_immutable(receipt_path, value)
    return value


def _attention_tokens(adapter: Any, text: str) -> int:
    features = adapter.tokenize([text])
    mask = features.get("attention_mask")
    if mask is None:
        raise LiveRuntimeV9Error("Qwen adapter tokenize omitted attention_mask")
    total = mask.sum()
    return int(total.item() if hasattr(total, "item") else total)


def _exact_qwen_text(adapter: Any, target_tokens: int, declared_max: int) -> str:
    prefix = (
        "Instruct: Retrieve patent families containing technical information relevant "
        "to prior-art search for the query patent family.\nQuery:"
    )
    adapter.max_seq_length = declared_max + 4096
    low, high = 0, max(64, target_tokens)
    while _attention_tokens(adapter, prefix + " synthetic" * high) < target_tokens:
        high *= 2
        if high > declared_max * 4:
            raise LiveRuntimeV9Error("cannot construct bounded Qwen synthetic input")
    while low <= high:
        middle = (low + high) // 2
        text = prefix + " synthetic" * middle
        observed = _attention_tokens(adapter, text)
        if observed == target_tokens:
            return text
        if observed < target_tokens:
            low = middle + 1
        else:
            high = middle - 1
    for repeats in range(max(0, high - 64), low + 65):
        text = prefix + " synthetic" * repeats
        if _attention_tokens(adapter, text) == target_tokens:
            return text
    raise LiveRuntimeV9Error(f"cannot construct exact {target_tokens}-token Qwen input")


def measure_qwen_max_length(
    adapter: Any,
    *,
    pooling_sha256: str,
    torch_module: Any,
    candidate_token_counts: Sequence[int] = (8192, 16384, 32768),
) -> dict[str, Any]:
    """Measure ARM-05 only through the frozen SentenceTransformer encode path."""

    import numpy as np

    if not SHA256_RE.fullmatch(pooling_sha256):
        raise LiveRuntimeV9Error("Qwen pooling hash is required")
    candidates = tuple(candidate_token_counts)
    if not candidates or tuple(sorted(set(candidates))) != candidates or candidates[0] < 8192 or candidates[-1] > 32768:
        raise LiveRuntimeV9Error("Qwen candidate token counts are invalid")
    passed = 0
    first_oom: int | None = None
    attempts: list[dict[str, Any]] = []
    largest_text = ""
    largest_output: Any = None
    cuda = torch_module.cuda
    oom_type = getattr(cuda, "OutOfMemoryError", getattr(torch_module, "OutOfMemoryError", ()))
    for count in candidates:
        text = _exact_qwen_text(adapter, count, 32768)
        adapter.max_seq_length = count
        actual = _attention_tokens(adapter, text)
        if actual != count:
            raise LiveRuntimeV9Error("Qwen adapter input was silently truncated")
        cuda.empty_cache()
        if hasattr(cuda, "reset_peak_memory_stats"):
            cuda.reset_peak_memory_stats()
        if hasattr(cuda, "synchronize"):
            cuda.synchronize()
        started = time.monotonic()
        try:
            output = adapter.encode(
                [text],
                batch_size=1,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            if hasattr(cuda, "synchronize"):
                cuda.synchronize()
            finite = bool(np.isfinite(output).all())
            dimension = int(output.shape[1]) if getattr(output, "ndim", 0) == 2 and output.shape[0] == 1 else 0
            normalized = dimension == 1024 and bool(
                np.allclose(np.linalg.norm(output, axis=1), [1.0], rtol=0.0, atol=1e-4)
            )
            if not finite or not normalized:
                raise LiveRuntimeV9Error("Qwen adapter output invariant failed")
            attempts.append(
                {
                    "requested_tokens": count,
                    "actual_tokens": actual,
                    "status": "PASS",
                    "peak_allocated_bytes": int(cuda.max_memory_allocated()),
                    "peak_reserved_bytes": int(cuda.max_memory_reserved()) if hasattr(cuda, "max_memory_reserved") else None,
                    "elapsed_seconds": round(time.monotonic() - started, 6),
                }
            )
            passed = count
            largest_text = text
            largest_output = output
        except Exception as error:
            if not oom_type or not isinstance(error, oom_type):
                raise
            first_oom = count
            attempts.append(
                {
                    "requested_tokens": count,
                    "actual_tokens": actual,
                    "status": "OOM",
                    "peak_allocated_bytes": int(cuda.max_memory_allocated()),
                    "peak_reserved_bytes": int(cuda.max_memory_reserved()) if hasattr(cuda, "max_memory_reserved") else None,
                    "elapsed_seconds": round(time.monotonic() - started, 6),
                }
            )
            gc.collect()
            cuda.empty_cache()
            break
    if passed < 8192 or largest_output is None:
        raise LiveRuntimeV9Error("Qwen did not complete the minimum adapter-level input")
    adapter.max_seq_length = passed
    repeated = adapter.encode(
        [largest_text],
        batch_size=1,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    repeat_agreement = bool(np.allclose(largest_output, repeated, rtol=0.0, atol=1e-6))
    if not repeat_agreement:
        raise LiveRuntimeV9Error("Qwen largest-pass repeat agreement failed")
    return {
        "schema_version": "myis.armindex-a1.2-qwen-adapter-measurement.v9",
        "adapter_path": "sentence_transformer_encode",
        "query_format_sha256": hashlib.sha256(
            b"Instruct: Retrieve patent families containing technical information relevant to prior-art search for the query patent family.\\nQuery:{query}"
        ).hexdigest(),
        "pooling_sha256": pooling_sha256,
        "pooling": "last_token_left_padding",
        "normalization": "l2",
        "declared_max_input_tokens": 32768,
        "measured_adapter_max_input_tokens": passed,
        "candidate_safe_max_input_tokens": passed,
        "first_oom_adapter_input_tokens": first_oom,
        "repeat_agreement_atol": 1e-6,
        "repeat_agreement": repeat_agreement,
        "output_dimension": 1024,
        "attempts": attempts,
        "claim_boundary": "single RTX 3090, FP16, batch size one, frozen v9 runtime and model only",
        "synthetic_text_only": True,
        "measured_retrieval": False,
    }


def run_adapter_check(
    *,
    output_root: Path,
    attempt_id: str,
    arm_id: str,
    model_root: Path,
) -> dict[str, Any]:
    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer

    from .a1_2_live_preflight import (
        EXPECTED_DIMENSIONS,
        MAX_INPUT_TOKENS,
        _gpu_rows,
        _pooling_config,
        _synthetic_texts,
    )

    if arm_id not in ARMS or os.environ.get("CUDA_VISIBLE_DEVICES") != str(ARMS.index(arm_id)):
        raise LiveRuntimeV9Error("adapter arm or CUDA mapping is invalid")
    if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("TRANSFORMERS_OFFLINE") != "1":
        raise LiveRuntimeV9Error("offline adapter runtime is not enforced")
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise LiveRuntimeV9Error("adapter worker must see exactly one CUDA device")
    directory = (model_root / arm_id).resolve()
    manifest = _read(directory / "runtime-file-manifest.v4.json")
    query, document = _synthetic_texts(arm_id)
    torch.manual_seed(20260807)
    torch.cuda.manual_seed_all(20260807)
    torch.cuda.reset_peak_memory_stats()
    model = SentenceTransformer(
        str(directory),
        device="cuda",
        trust_remote_code=arm_id == "ARM-04",
        local_files_only=True,
        model_kwargs={"torch_dtype": torch.float16},
        config_kwargs=ARM_CONFIG_OVERRIDES.get(arm_id),
    )
    model.max_seq_length = MAX_INPUT_TOKENS[arm_id]
    first = model.encode(
        [query, document], batch_size=2, convert_to_numpy=True,
        normalize_embeddings=True, show_progress_bar=False,
    )
    repeated = model.encode(
        [query, document], batch_size=2, convert_to_numpy=True,
        normalize_embeddings=True, show_progress_bar=False,
    )
    finite = bool(np.isfinite(first).all())
    dimension = int(first.shape[1]) if first.ndim == 2 else 0
    normalized = bool(
        np.allclose(
            np.linalg.norm(first, axis=1),
            np.ones(2),
            rtol=0.0,
            atol=L2_NORMALIZATION_ATOL,
        )
    )
    repeat = bool(np.allclose(first, repeated, rtol=0.0, atol=1e-6))
    if not finite or not normalized or not repeat or dimension != EXPECTED_DIMENSIONS[arm_id]:
        raise LiveRuntimeV9Error(f"{arm_id} frozen adapter parity failed")
    pooling = _pooling_config(directory)
    qwen = None
    if arm_id == "ARM-05":
        qwen = measure_qwen_max_length(model, pooling_sha256=pooling["sha256"], torch_module=torch)
    attempt = _attempt(_attempt_directory(output_root, attempt_id), attempt_id)
    physical = _gpu_rows()[int(os.environ["CUDA_VISIBLE_DEVICES"])]
    unsigned = {
        "schema_version": "myis.armindex-a1.2-live-adapter-parity.v9",
        "attempt_id": attempt_id,
        "verification_marker_sha256": attempt["verification_marker_sha256"],
        "arm_id": arm_id,
        "status": "PASS",
        "cuda_visible_devices": os.environ["CUDA_VISIBLE_DEVICES"],
        "physical_gpu_uuid": physical["uuid"],
        "physical_gpu_name": physical["name"],
        "model_manifest_sha256": manifest.get("manifest_sha256"),
        "pooling_config": pooling,
        "query_format_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
        "document_format_sha256": hashlib.sha256(document.encode("utf-8")).hexdigest(),
        "output_dimension": dimension,
        "finite_embeddings": finite,
        "l2_normalized": normalized,
        "l2_normalization_atol": L2_NORMALIZATION_ATOL,
        "repeat_agreement_atol": 1e-6,
        "repeat_agreement": repeat,
        "model_config_overrides": ARM_CONFIG_OVERRIDES.get(arm_id, {}),
        "torch_dtype": "float16",
        "peak_vram_bytes": int(torch.cuda.max_memory_allocated()),
        "qwen_adapter_maximum": qwen,
        "trust_remote_code": arm_id == "ARM-04",
        "local_files_only": True,
        "network_fallback": False,
        "synthetic_text_only": True,
        "measured_retrieval": False,
        "scientific_authority": False,
        "generated_at": _utc_now(),
    }
    value = {**unsigned, "receipt_sha256": canonical_sha256(unsigned)}
    target = _attempt_directory(output_root, attempt_id) / "preflight" / "adapters" / f"{arm_id}.json"
    _write_immutable(target, value)
    return value


def run_checkpoint_worker(
    *,
    output_root: Path,
    attempt_id: str,
    arm_id: str,
    fail_before_step: int | None = None,
) -> dict[str, Any]:
    if arm_id not in ARMS or os.environ.get("CUDA_VISIBLE_DEVICES") != str(ARMS.index(arm_id)):
        raise LiveRuntimeV9Error("checkpoint worker CUDA mapping is invalid")
    directory = _attempt_directory(output_root, attempt_id)
    failure = directory / "failure-receipts" / f"{arm_id}.injected.json"
    resumed = failure.is_file()
    for step in (1, 2):
        step_id = f"{arm_id.lower()}-step-{step}"
        if (directory / "steps" / f"{step_id}.json").is_file():
            continue
        if fail_before_step == step:
            unsigned = {
                "schema_version": "myis.armindex-a1.2-live-injected-failure.v9",
                "attempt_id": attempt_id,
                "arm_id": arm_id,
                "failed_before_step": step,
                "checkpoint_written_for_failed_step": False,
                "status": "EXPECTED_FAILURE",
            }
            _write_immutable(failure, {**unsigned, "receipt_sha256": canonical_sha256(unsigned)})
            raise LiveRuntimeV9Error("injected failure before durable step completion")
        artifact = directory / "worker-artifacts" / arm_id / f"step-{step}.json"
        payload = {"attempt_id": attempt_id, "arm_id": arm_id, "step": step, "synthetic_only": True}
        _write_immutable(artifact, payload)
        complete_step(output_root, attempt_id, step_id, [artifact])
    unsigned = {
        "schema_version": "myis.armindex-a1.2-live-worker-receipt.v9",
        "attempt_id": attempt_id,
        "arm_id": arm_id,
        "status": "PASS",
        "completed_steps": 2,
        "resumed_after_injected_failure": resumed,
        "cuda_visible_devices": os.environ["CUDA_VISIBLE_DEVICES"],
        "synthetic_only": True,
        "measured_retrieval": False,
    }
    value = {**unsigned, "receipt_sha256": canonical_sha256(unsigned)}
    _write_immutable(directory / "runtime-receipts" / f"{arm_id}.json", value)
    return value


def _attempt_evidence(directory: Path, attempt_id: str) -> dict[str, Any]:
    adapters: dict[str, str] = {}
    workers: dict[str, str] = {}
    blockers: list[str] = []
    for arm in ARMS:
        adapter_path = directory / "preflight" / "adapters" / f"{arm}.json"
        worker_path = directory / "runtime-receipts" / f"{arm}.json"
        try:
            adapter = _checked(adapter_path, "receipt_sha256", "adapter receipt")
            worker = _checked(worker_path, "receipt_sha256", "worker receipt")
            if (
                adapter.get("status") != "PASS"
                or adapter.get("attempt_id") != attempt_id
                or adapter.get("arm_id") != arm
                or worker.get("status") != "PASS"
                or worker.get("attempt_id") != attempt_id
                or worker.get("arm_id") != arm
            ):
                blockers.append(f"arm_status:{arm}")
            adapters[arm] = file_sha256(adapter_path)
            workers[arm] = file_sha256(worker_path)
        except LiveRuntimeV9Error:
            blockers.append(f"missing_or_invalid:{arm}")
    failure_path = directory / "failure-receipts" / "ARM-02.injected.json"
    try:
        failure = _checked(failure_path, "receipt_sha256", "injected failure receipt")
        if (
            failure.get("schema_version") != "myis.armindex-a1.2-live-injected-failure.v9"
            or failure.get("attempt_id") != attempt_id
            or failure.get("arm_id") != "ARM-02"
            or failure.get("failed_before_step") != 1
            or failure.get("checkpoint_written_for_failed_step") is not False
            or failure.get("status") != "EXPECTED_FAILURE"
        ):
            raise LiveRuntimeV9Error("injected failure receipt identity mismatch")
    except LiveRuntimeV9Error:
        blockers.append("checkpoint_injected_failure")
    try:
        checkpoint = _checked(
            directory / "steps" / "arm-02-step-1.json",
            "checkpoint_sha256",
            "resume checkpoint",
        )
        if (
            checkpoint.get("attempt_id") != attempt_id
            or checkpoint.get("step_id") != "arm-02-step-1"
            or checkpoint.get("status") != "COMPLETE"
        ):
            raise LiveRuntimeV9Error("resume checkpoint identity mismatch")
        arm02_worker = _checked(
            directory / "runtime-receipts" / "ARM-02.json",
            "receipt_sha256",
            "ARM-02 worker receipt",
        )
        if arm02_worker.get("resumed_after_injected_failure") is not True:
            raise LiveRuntimeV9Error("ARM-02 worker did not record injected-failure resume")
    except LiveRuntimeV9Error:
        blockers.append("checkpoint_resume")
    arm05_path = directory / "preflight" / "adapters" / "ARM-05.json"
    qwen_max = None
    if arm05_path.is_file():
        qwen = _read(arm05_path).get("qwen_adapter_maximum")
        if isinstance(qwen, Mapping):
            qwen_max = qwen.get("measured_adapter_max_input_tokens")
    if not isinstance(qwen_max, int) or isinstance(qwen_max, bool) or qwen_max < 8192:
        blockers.append("qwen_adapter_maximum")
    return {
        "blockers": sorted(blockers),
        "adapter_receipt_sha256s": adapters,
        "worker_receipt_sha256s": workers,
        "checkpoint_resume_passed": (
            "checkpoint_resume" not in blockers
            and "checkpoint_injected_failure" not in blockers
        ),
        "qwen_measured_adapter_max_input_tokens": qwen_max,
    }


def summarize_attempt(output_root: Path, attempt_id: str) -> dict[str, Any]:
    directory = _attempt_directory(output_root, attempt_id)
    attempt = _attempt(directory, attempt_id)
    evidence = _attempt_evidence(directory, attempt_id)
    blockers = evidence["blockers"]
    unsigned = {
        "schema_version": "myis.armindex-a1.2-live-preflight-summary.v9",
        "attempt_id": attempt_id,
        "verification_marker_sha256": attempt["verification_marker_sha256"],
        "status": "PASS" if not blockers else "BLOCKED_PREFLIGHT",
        **evidence,
        "synthetic_workers_only": True,
        "measured_retrieval": False,
        "launch_allowed": False,
        "adopted_for_execution": False,
        "generated_at": _utc_now(),
    }
    value = {**unsigned, "summary_sha256": canonical_sha256(unsigned)}
    _write_immutable(directory / "summary.json", value)
    if blockers:
        raise LiveRuntimeV9Error("live preflight summary is blocked: " + ", ".join(blockers))
    return value


def complete_attempt(output_root: Path, attempt_id: str, summary_path: Path) -> dict[str, Any]:
    directory = _attempt_directory(output_root, attempt_id)
    attempt = _attempt(directory, attempt_id)
    if _state(directory, attempt_id)["status"] != "RUNNING" or summary_path.resolve() != (directory / "summary.json").resolve():
        raise LiveRuntimeV9Error("completion requires the canonical RUNNING-attempt summary")
    summary = _checked(summary_path, "summary_sha256", "preflight summary")
    evidence = _attempt_evidence(directory, attempt_id)
    if (
        summary.get("status") != "PASS"
        or summary.get("attempt_id") != attempt_id
        or summary.get("verification_marker_sha256") != attempt["verification_marker_sha256"]
        or evidence["blockers"]
        or any(summary.get(key) != value for key, value in evidence.items())
        or summary.get("synthetic_workers_only") is not True
        or summary.get("measured_retrieval") is not False
        or summary.get("launch_allowed") is not False
        or summary.get("adopted_for_execution") is not False
    ):
        raise LiveRuntimeV9Error(
            "completion summary is not same-attempt evidence-bound PASS"
        )
    return _set_state(directory, attempt_id, "COMPLETE", "same_attempt_pass_summary_durable")


def _safe_attempt_files(directory: Path) -> list[Path]:
    files: list[Path] = []
    total = 0
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(directory).as_posix()
        if relative == "safe-export-members.v9.json":
            continue
        if FORBIDDEN_EXPORT_FRAGMENT.search(relative):
            raise LiveRuntimeV9Error(f"unsafe export path: {relative}")
        if not any(relative == prefix or relative.startswith(prefix) for prefix in SAFE_EXPORT_PREFIXES):
            raise LiveRuntimeV9Error(f"path is outside the v9 safe-export allowlist: {relative}")
        size = path.stat().st_size
        if size > 1024 * 1024:
            raise LiveRuntimeV9Error(f"safe-export file exceeds 1 MiB: {relative}")
        path.read_text(encoding="utf-8")
        total += size
        files.append(path)
    if total > 16 * 1024 * 1024:
        raise LiveRuntimeV9Error("safe-export text exceeds 16 MiB")
    return files


def build_safe_export(output_root: Path, attempt_id: str, archive_path: Path) -> dict[str, Any]:
    directory = _attempt_directory(output_root, attempt_id)
    attempt = _attempt(directory, attempt_id)
    if _state(directory, attempt_id)["status"] != "COMPLETE":
        raise LiveRuntimeV9Error("safe export requires COMPLETE attempt")
    summary = _checked(directory / "summary.json", "summary_sha256", "preflight summary")
    if summary.get("status") != "PASS" or summary.get("verification_marker_sha256") != attempt["verification_marker_sha256"]:
        raise LiveRuntimeV9Error("safe export requires same-attempt marker-bound PASS")
    teardown_path = directory / "teardown.json"
    if not teardown_path.is_file() or teardown_path.is_symlink():
        raise LiveRuntimeV9Error("safe export requires a same-attempt reaped teardown receipt")
    teardown = _checked(teardown_path, "teardown_sha256", "teardown receipt")
    if teardown.get("attempt_id") != attempt_id or teardown.get("children_reaped") is not True:
        raise LiveRuntimeV9Error("safe export requires a same-attempt reaped teardown receipt")
    archive = archive_path.resolve()
    export_root = (output_root.resolve() / "exports").resolve()
    if archive.parent != export_root or attempt_id not in archive.name:
        raise LiveRuntimeV9Error("safe export must use the attempt-bound export directory")
    receipt_path = archive.with_suffix(archive.suffix + ".receipt.json")
    if archive.is_file() and receipt_path.is_file():
        receipt = _checked(receipt_path, "receipt_sha256", "safe-export receipt")
        if receipt.get("attempt_id") == attempt_id and receipt.get("archive_sha256") == file_sha256(archive):
            validate_safe_export_archive(archive)
            return receipt
        raise LiveRuntimeV9Error("existing safe export differs from its receipt")
    files = _safe_attempt_files(directory)
    members = [
        {"uri": path.relative_to(directory).as_posix(), "sha256": _durable_hash(path), "size_bytes": path.stat().st_size}
        for path in files
    ]
    manifest_unsigned = {
        "schema_version": "myis.armindex-a1.2-live-safe-export-members.v9",
        "attempt_id": attempt_id,
        "verification_marker_sha256": attempt["verification_marker_sha256"],
        "members": members,
    }
    manifest = {**manifest_unsigned, "members_sha256": canonical_sha256(manifest_unsigned)}
    manifest_path = directory / "safe-export-members.v9.json"
    _write_immutable(manifest_path, manifest)
    export_root.mkdir(parents=True, exist_ok=True)
    temporary = export_root / f".{archive.name}.{os.getpid()}.tmp"
    with tarfile.open(temporary, "w:gz", format=tarfile.PAX_FORMAT) as tar:
        for path in [*files, manifest_path]:
            tar.add(path, arcname=path.relative_to(directory).as_posix(), recursive=False)
    os.replace(temporary, archive)
    validation = validate_safe_export_archive(archive)
    receipt_unsigned = {
        "schema_version": "myis.armindex-a1.2-live-safe-export-receipt.v9",
        "attempt_id": attempt_id,
        "status": "PASS",
        "verification_marker_sha256": attempt["verification_marker_sha256"],
        "members_manifest_sha256": manifest["members_sha256"],
        "archive_sha256": validation["archive_sha256"],
        "archive_bytes": archive.stat().st_size,
    }
    receipt = {**receipt_unsigned, "receipt_sha256": canonical_sha256(receipt_unsigned)}
    _write_immutable(receipt_path, receipt)
    return receipt


def validate_safe_export_archive(archive_path: Path) -> dict[str, Any]:
    if not archive_path.is_file() or archive_path.is_symlink():
        raise LiveRuntimeV9Error("safe-export archive is missing or unsafe")
    with tarfile.open(archive_path, "r:gz") as archive:
        tar_members = archive.getmembers()
        names = [member.name for member in tar_members]
        if len(names) != len(set(names)) or any(
            not member.isreg() or Path(member.name).is_absolute() or ".." in Path(member.name).parts
            for member in tar_members
        ):
            raise LiveRuntimeV9Error("safe-export archive has unsafe or duplicate members")
        try:
            stream = archive.extractfile("safe-export-members.v9.json")
            if stream is None:
                raise KeyError
            manifest = json.loads(stream.read().decode("utf-8"))
        except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise LiveRuntimeV9Error("safe-export member manifest is invalid") from error
        body = dict(manifest)
        if body.pop("members_sha256", None) != canonical_sha256(body):
            raise LiveRuntimeV9Error("safe-export member manifest self-hash mismatch")
        expected_names = [row["uri"] for row in manifest.get("members", [])]
        if sorted(names) != sorted([*expected_names, "safe-export-members.v9.json"]):
            raise LiveRuntimeV9Error("safe-export members differ from the manifest")
        for row in manifest["members"]:
            member_stream = archive.extractfile(row["uri"])
            if member_stream is None:
                raise LiveRuntimeV9Error("safe-export member cannot be read")
            digest = hashlib.sha256()
            size = 0
            while chunk := member_stream.read(1024 * 1024):
                digest.update(chunk)
                size += len(chunk)
            if digest.hexdigest() != row["sha256"] or size != row["size_bytes"]:
                raise LiveRuntimeV9Error(f"safe-export member mismatch: {row['uri']}")
    return {
        "status": "PASS",
        "archive_sha256": file_sha256(archive_path),
        "member_count": len(tar_members),
        "members_manifest_sha256": manifest["members_sha256"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myis-a1.2-live-preflight-runtime-v9")
    parser.add_argument(
        "command",
        choices=(
            "validate-verification-marker", "init", "status", "teardown", "safe-export",
            "validate-export", "complete", "heartbeat", "record-pid", "record-process-exit",
            "checkpoint", "adapter-check", "checkpoint-worker", "summarize",
        ),
    )
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--attempt-id")
    parser.add_argument("--marker", type=Path)
    parser.add_argument("--write-marker", type=Path)
    parser.add_argument("--runtime-identity", type=Path)
    parser.add_argument("--expected-commit")
    parser.add_argument("--expected-tree")
    parser.add_argument("--expected-manifest-digest")
    parser.add_argument("--expected-bundle-sha256")
    parser.add_argument("--pid", type=int)
    parser.add_argument("--role")
    parser.add_argument("--exit-code", type=int)
    parser.add_argument("--step-id")
    parser.add_argument("--artifact", type=Path, action="append")
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--model-root", type=Path)
    parser.add_argument("--arm", choices=ARMS)
    parser.add_argument("--fail-before-step", type=int)
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--children-reaped", action="store_true")
    return parser


def _required(value: Any, label: str) -> Any:
    if value is None:
        raise LiveRuntimeV9Error(f"{label} is required")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "validate-verification-marker":
        marker_path = args.write_marker or args.marker
        _required(marker_path, "marker path")
        if args.write_marker:
            result = write_verification_marker(
                marker_path,
                expected_commit=_required(args.expected_commit, "expected commit"),
                expected_tree=_required(args.expected_tree, "expected tree"),
                expected_manifest_digest=_required(args.expected_manifest_digest, "expected manifest digest"),
                expected_bundle_sha256=_required(args.expected_bundle_sha256, "expected bundle hash"),
                runtime_identity_path=_required(args.runtime_identity, "runtime identity"),
            )
        else:
            result = validate_verification_marker(
                marker_path,
                expected_commit=args.expected_commit,
                expected_tree=args.expected_tree,
                expected_manifest_digest=args.expected_manifest_digest,
                expected_bundle_sha256=args.expected_bundle_sha256,
            )
    elif args.command == "validate-export":
        result = validate_safe_export_archive(_required(args.archive, "archive"))
    else:
        output_root = _required(args.output_root, "output root")
        attempt_id = _required(args.attempt_id, "attempt id")
        if args.command != "init" and args.marker:
            marker = validate_verification_marker(args.marker)
            attempt = _attempt(_attempt_directory(output_root, attempt_id), attempt_id)
            if attempt.get("verification_marker_sha256") != marker.get("marker_sha256"):
                raise LiveRuntimeV9Error("attempt and verification marker differ")
        if args.command == "init":
            result = initialize_attempt(output_root, attempt_id, _required(args.marker, "marker"))
        elif args.command == "status":
            result = attempt_status(output_root, attempt_id, require_pass=args.require_pass)
        elif args.command == "teardown":
            result = teardown_attempt(output_root, attempt_id, children_reaped=args.children_reaped)
        elif args.command == "safe-export":
            result = build_safe_export(output_root, attempt_id, _required(args.archive, "archive"))
        elif args.command == "complete":
            result = complete_attempt(output_root, attempt_id, _required(args.summary, "summary"))
        elif args.command == "heartbeat":
            result = heartbeat(output_root, attempt_id, _required(args.pid, "pid"))
        elif args.command == "record-pid":
            result = record_process(
                output_root, attempt_id, _required(args.pid, "pid"), role=_required(args.role, "role")
            )
        elif args.command == "record-process-exit":
            result = record_process_exit(
                output_root, attempt_id, _required(args.pid, "pid"), _required(args.exit_code, "exit code")
            )
        elif args.command == "checkpoint":
            result = complete_step(
                output_root, attempt_id, _required(args.step_id, "step id"), _required(args.artifact, "artifact")
            )
        elif args.command == "adapter-check":
            result = run_adapter_check(
                output_root=output_root, attempt_id=attempt_id,
                arm_id=_required(args.arm, "arm"), model_root=_required(args.model_root, "model root"),
            )
        elif args.command == "checkpoint-worker":
            result = run_checkpoint_worker(
                output_root=output_root, attempt_id=attempt_id,
                arm_id=_required(args.arm, "arm"), fail_before_step=args.fail_before_step,
            )
        else:
            result = summarize_attempt(output_root, attempt_id)
    print(_json_text(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
