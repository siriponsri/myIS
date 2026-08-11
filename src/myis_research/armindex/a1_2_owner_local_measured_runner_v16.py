"""Owner-local bridge for one hash-bound A1.2 v16 common-screen attempt.

The bridge is deliberately narrow: it reads only paths committed by an
Owner-local materializer manifest, invokes the v16 ``execute_program_cell``
callback, and writes aggregate-safe cell receipts.  It never evaluates qrels,
maps opaque identities, or emits ranking rows.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import tempfile
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from ..kernel.canonical import canonical_sha256, file_sha256
from .a1_2_measured_executor_v16 import (
    DenseEmbeddingAdapter,
    FamilyRank,
    LogicalInput,
    MeasuredExecutorV16Error,
    PhysicalInput,
    execute_program_cell_batch,
    execute_program_cell_batch_instrumented,
)
from .a1_2_raw_materializer_bridge_v16 import (
    RawMaterializerBridgeV16Error,
    materialize_raw_corpus,
    materialize_raw_query,
)

ARM_IDS = ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")
ORIGINAL_PROGRAM_IDS = (
    "P00-TAC-DOC",
    "P01-TA-DOC",
    "P02-CLAIM1",
    "P03-PASSAGE",
    "P04-SECTION-MULTIVIEW",
)
EXECUTABLE_PROGRAM_IDS = {
    **{program: program for program in ORIGINAL_PROGRAM_IDS if program != "P02-CLAIM1"},
    "P02-CLAIM1": "P02-FIRST-CLAIM",
}
CELL_IDS = tuple(f"{arm}--{program}" for arm in ARM_IDS for program in ORIGINAL_PROGRAM_IDS)
TOKEN_RE = re.compile(r"^[FQ]-[a-f0-9]{32}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
ATTEMPT_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
MANIFEST_SCHEMA = "myis.armindex-a1.2-owner-local-measured-input-manifest.v16"
RECEIPT_SCHEMA = "myis.armindex-a1.2-owner-local-cell-receipt.v16"
SUMMARY_SCHEMA = "myis.armindex-a1.2-owner-local-screen-receipt.v16"
METRICS_SCHEMA = "myis.armindex-a1.2-cell-performance-metrics.v16"
FAILURE_METRICS_SCHEMA = "myis.armindex-a1.2-cell-performance-failure-metrics.v16"
CELL_COMMIT_SCHEMA = "myis.armindex-a1.2-owner-local-cell-commit.v16"
GATE_NAMES = (
    "provider_admission",
    "execution_adoption",
    "watchdog_ttl",
    "protected_boundary",
    "frozen_bindings",
)


class OwnerLocalMeasuredRunnerV16Error(ValueError):
    """Raised for any manifest, callback, or completion mismatch."""


def _json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _load_json(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} must be a JSON object")
    return value


def _hash(value: Any, *, role: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} hash is invalid")
    return value


def _safe_file(root: Path, relative: Any, *, role: str) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} path is invalid")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} path must be relative")
    candidate = root / path
    try:
        resolved = candidate.resolve(strict=True)
        metadata = candidate.lstat()
    except OSError as error:
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} is missing") from error
    if candidate.is_symlink() or not resolved.is_relative_to(root) or metadata.st_mode & 0o170000 != 0o100000:
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} is unsafe")
    return resolved


def _atomic(path: Path, value: Mapping[str, Any]) -> None:
    text = _json(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_text(encoding="ascii") != text:
            raise OwnerLocalMeasuredRunnerV16Error("immutable receipt already differs")
        return
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_text(encoding="ascii") != value:
            raise OwnerLocalMeasuredRunnerV16Error("immutable text artifact already differs")
        return
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _read_jsonl(path: Path, *, role: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            for line in handle:
                if not line.strip():
                    raise OwnerLocalMeasuredRunnerV16Error(f"{role} contains an empty row")
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise OwnerLocalMeasuredRunnerV16Error(f"{role} contains a non-object row")
                rows.append(value)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        if isinstance(error, OwnerLocalMeasuredRunnerV16Error):
            raise
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} is invalid JSONL") from error
    if not rows:
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} is empty")
    return rows


def _physical_inputs(row: Mapping[str, Any], *, role: str) -> tuple[PhysicalInput, ...]:
    values = row.get("physical_inputs")
    if values is None:
        text, count = row.get("text"), row.get("source_token_count", 1)
        values = [{"text": text, "source_token_count": count}]
    if not isinstance(values, list) or not values:
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} physical plan is missing")
    parsed: list[PhysicalInput] = []
    for value in values:
        if not isinstance(value, Mapping) or set(value) not in (
            {"text", "source_token_count"},
            {"text", "source_token_count", "token_ids"},
        ):
            raise OwnerLocalMeasuredRunnerV16Error(f"{role} physical plan is invalid")
        text, count = value["text"], value["source_token_count"]
        if not isinstance(text, str) or not text or isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise OwnerLocalMeasuredRunnerV16Error(f"{role} physical input is invalid")
        token_ids = value.get("token_ids")
        if token_ids is not None and (
            not isinstance(token_ids, list)
            or not token_ids
            or any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in token_ids)
        ):
            raise OwnerLocalMeasuredRunnerV16Error(f"{role} physical token-ID plan is invalid")
        parsed.append(PhysicalInput(text, count, tuple(token_ids) if token_ids is not None else None))
    return tuple(parsed)


def _logical(row: Mapping[str, Any], *, role: str, query: bool = False) -> LogicalInput:
    token_key = "work_token" if query else "family_token"
    token = row.get(token_key)
    if not isinstance(token, str) or TOKEN_RE.fullmatch(token) is None or (query and not token.startswith("Q-")) or (not query and not token.startswith("F-")):
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} opaque token is invalid")
    logical_id = row.get("logical_id", row.get("unit_id", token))
    if not isinstance(logical_id, str) or not logical_id:
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} logical identity is invalid")
    view = row.get("view_id")
    if view is not None and view not in {"title", "abstract", "claims"}:
        raise OwnerLocalMeasuredRunnerV16Error(f"{role} view is invalid")
    return LogicalInput(logical_id, token, view, _physical_inputs(row, role=role))


def _ranking_rows(rows: Sequence[Any]) -> tuple[str, tuple[str, ...]]:
    safe: list[dict[str, Any]] = []
    for item in rows:
        if isinstance(item, FamilyRank):
            family, rank, score = item.family_token, item.rank, item.score
        elif isinstance(item, Mapping) and set(item) == {"family_token", "rank", "score"}:
            family, rank, score = item["family_token"], item["rank"], item["score"]
        else:
            raise OwnerLocalMeasuredRunnerV16Error("executor returned an invalid rank row")
        if not isinstance(family, str) or not family.startswith("F-") or TOKEN_RE.fullmatch(family) is None:
            raise OwnerLocalMeasuredRunnerV16Error("executor returned a non-opaque family token")
        if not isinstance(rank, int) or rank < 1 or rank > 100 or not isinstance(score, (int, float)):
            raise OwnerLocalMeasuredRunnerV16Error("executor returned an invalid rank")
        safe.append({"family_token": family, "rank": rank, "score": float(score)})
    if len(safe) != 100 or [item["rank"] for item in safe] != list(range(1, 101)) or len({item["family_token"] for item in safe}) != 100:
        raise OwnerLocalMeasuredRunnerV16Error("executor must return exactly 100 unique ranked families")
    return canonical_sha256(safe), tuple(item["family_token"] for item in safe)


def _ranking_hash(rows: Sequence[Any]) -> str:
    return _ranking_rows(rows)[0]


def _percentile(samples: Sequence[float], fraction: float) -> float:
    ordered = sorted(float(value) for value in samples)
    if not ordered:
        raise OwnerLocalMeasuredRunnerV16Error("search latency samples are missing")
    index = (len(ordered) - 1) * fraction
    lower, upper = int(index), min(int(index) + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def _host_rss_bytes() -> int:
    """Read only the current process RSS; no environment is exposed."""

    status = Path("/proc/self/status")
    if status.is_file():
        for line in status.read_text(encoding="ascii", errors="ignore").splitlines():
            if line.startswith("VmRSS:"):
                fields = line.split()
                if len(fields) >= 2 and fields[1].isdigit():
                    return int(fields[1]) * 1024
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class _ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = _ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        if ctypes.windll.psapi.GetProcessMemoryInfo(
            ctypes.windll.kernel32.GetCurrentProcess(),
            ctypes.byref(counters),
            counters.cb,
        ):
            return int(counters.PeakWorkingSetSize)
    return 0


def _vram_bytes() -> int:
    try:
        import torch

        if torch.cuda.is_available():
            return int(torch.cuda.memory_allocated())
    except ImportError:
        pass
    return 0


class _PeakResources:
    """Small per-cell sampler for aggregate host/GPU resource peaks."""

    def __init__(self) -> None:
        self.host_peak_bytes = _host_rss_bytes()
        self.vram_peak_bytes = _vram_bytes()
        self._stopped = threading.Event()
        self._thread = threading.Thread(target=self._sample, daemon=True)

    def start(self) -> None:
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.reset_peak_memory_stats()
        except ImportError:
            pass
        self._thread.start()

    def _sample(self) -> None:
        while not self._stopped.wait(0.05):
            self.host_peak_bytes = max(self.host_peak_bytes, _host_rss_bytes())
            self.vram_peak_bytes = max(self.vram_peak_bytes, _vram_bytes())

    def stop(self) -> tuple[int, int]:
        self._stopped.set()
        self._thread.join(timeout=1)
        self.host_peak_bytes = max(self.host_peak_bytes, _host_rss_bytes())
        self.vram_peak_bytes = max(self.vram_peak_bytes, _vram_bytes())
        try:
            import torch

            if torch.cuda.is_available():
                self.vram_peak_bytes = max(self.vram_peak_bytes, int(torch.cuda.max_memory_allocated()))
        except ImportError:
            pass
        return self.host_peak_bytes, self.vram_peak_bytes


def _metrics_sidecar(
    *,
    manifest: Mapping[str, Any],
    cell: Mapping[str, Any],
    receipt: Mapping[str, Any],
    compile_latency_ms: float,
    index_latency_ms: float,
    query_encode_latency_ms: float,
    search_latency_ms: Sequence[float],
    wall_seconds: float,
    peak_host_ram_bytes: int,
    peak_vram_bytes: int,
    index_size_bytes: int,
    replay_count: int,
    replay_ranking_sha256: str,
    retry_count: int,
) -> dict[str, Any]:
    total_query_seconds = (query_encode_latency_ms + sum(search_latency_ms)) / 1_000
    if len(search_latency_ms) != 150 or total_query_seconds <= 0:
        raise OwnerLocalMeasuredRunnerV16Error("search measurement coverage is invalid")
    if replay_count < 2 or replay_ranking_sha256 != receipt["ranking_set_sha256"]:
        raise OwnerLocalMeasuredRunnerV16Error("same-index/vector ranking replay failed")
    latency = {
        "p50": _percentile(search_latency_ms, 0.50),
        "p95": _percentile(search_latency_ms, 0.95),
        "p99": _percentile(search_latency_ms, 0.99),
    }
    attempt_binding_sha256 = canonical_sha256(
        {
            "attempt_id": manifest["attempt_id"],
            "cell_id": cell["cell_id"],
            "binding_sha256": cell["binding_sha256"],
            "manifest_sha256": manifest["manifest_sha256"],
        }
    )
    body = {
        "schema_version": METRICS_SCHEMA,
        "receipt_id": f"{manifest['attempt_id']}--{cell['cell_id']}--metrics",
        "attempt_id": manifest["attempt_id"],
        "cell_id": cell["cell_id"],
        "status": "PASS",
        "aggregate_safe": True,
        "manifest_sha256": manifest["manifest_sha256"],
        "attempt_binding_sha256": attempt_binding_sha256,
        "binding_sha256": cell["binding_sha256"],
        "cell_receipt_sha256": receipt["receipt_sha256"],
        "ranking_file_sha256": receipt["ranking_file_sha256"],
        "ranking_set_sha256": receipt["ranking_set_sha256"],
        "performance": {
            "compile_latency_ms": compile_latency_ms,
            "index_latency_ms": index_latency_ms,
            "query_encode_latency_ms": query_encode_latency_ms,
            "search_latency_ms": latency,
            "throughput_qps": 150 / total_query_seconds,
            "wall_seconds": wall_seconds,
        },
        "resources": {
            "peak_host_ram_bytes": peak_host_ram_bytes,
            "peak_vram_bytes": peak_vram_bytes,
            "index_size_bytes": index_size_bytes,
        },
        "resource_sampling": {
            "host_rss": "current_process_50ms",
            "vram": "pytorch_allocator_50ms_and_peak",
        },
        "reliability": {
            "replay_count": replay_count,
            "replay_ranking_sha256": replay_ranking_sha256,
            "ranking_replay_match": True,
            "retry_count": retry_count,
            "oom_count": 0,
            "failure_category": "none",
        },
    }
    return {**body, "metrics_sha256": canonical_sha256(body)}


def _cell_commit(
    *,
    manifest: Mapping[str, Any],
    cell: Mapping[str, Any],
    receipt: Mapping[str, Any],
    metrics: Mapping[str, Any],
) -> dict[str, Any]:
    body = {
        "schema_version": CELL_COMMIT_SCHEMA,
        "receipt_id": f"{manifest['attempt_id']}--{cell['cell_id']}--commit",
        "attempt_id": manifest["attempt_id"],
        "cell_id": cell["cell_id"],
        "status": "PASS",
        "aggregate_safe": True,
        "manifest_sha256": manifest["manifest_sha256"],
        "binding_sha256": cell["binding_sha256"],
        "cell_receipt_sha256": receipt["receipt_sha256"],
        "ranking_file_sha256": receipt["ranking_file_sha256"],
        "ranking_set_sha256": receipt["ranking_set_sha256"],
        "metrics_sha256": metrics["metrics_sha256"],
    }
    return {**body, "commit_sha256": canonical_sha256(body)}


def _validate_cell_commit(
    value: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any],
    cell: Mapping[str, Any],
    receipt: Mapping[str, Any],
    metrics: Mapping[str, Any],
) -> None:
    body = {key: item for key, item in value.items() if key != "commit_sha256"}
    if (
        value.get("schema_version") != CELL_COMMIT_SCHEMA
        or value.get("receipt_id") != f"{manifest['attempt_id']}--{cell['cell_id']}--commit"
        or value.get("attempt_id") != manifest["attempt_id"]
        or value.get("cell_id") != cell["cell_id"]
        or value.get("status") != "PASS"
        or value.get("aggregate_safe") is not True
        or value.get("manifest_sha256") != manifest["manifest_sha256"]
        or value.get("binding_sha256") != cell["binding_sha256"]
        or value.get("cell_receipt_sha256") != receipt["receipt_sha256"]
        or value.get("ranking_file_sha256") != receipt["ranking_file_sha256"]
        or value.get("ranking_set_sha256") != receipt["ranking_set_sha256"]
        or value.get("metrics_sha256") != metrics["metrics_sha256"]
        or value.get("commit_sha256") != canonical_sha256(body)
    ):
        raise OwnerLocalMeasuredRunnerV16Error("cell commit marker is invalid")


def _after_cell_artifact(_name: str) -> None:
    """Test hook for process-loss boundaries; production implementation is a no-op."""


def _archive_partial_cell(
    *,
    attempt_root: Path,
    cell_id: str,
    artifacts: Mapping[str, Path],
) -> int:
    """Move uncommitted aggregate-safe artifacts aside before one deterministic retry."""

    partial_root = attempt_root / "failed-partial" / cell_id
    if partial_root.exists() and (partial_root.is_symlink() or not partial_root.is_dir()):
        raise OwnerLocalMeasuredRunnerV16Error("partial recovery root is unsafe")
    completed_retries: list[int] = []
    if partial_root.exists():
        for entry in partial_root.iterdir():
            if entry.is_symlink() or not entry.is_dir() or not entry.name.startswith("retry-"):
                raise OwnerLocalMeasuredRunnerV16Error("partial recovery history is unsafe")
            suffix = entry.name.removeprefix("retry-")
            if not suffix.isdigit() or int(suffix) < 1:
                raise OwnerLocalMeasuredRunnerV16Error("partial recovery retry is invalid")
            completed_retries.append(int(suffix))
    retry_count = max(completed_retries, default=0) + 1
    archive = partial_root / f"retry-{retry_count}"
    archive.mkdir(parents=True, exist_ok=False)
    moved: list[dict[str, str]] = []
    for role, source in artifacts.items():
        if not source.exists():
            continue
        if source.is_symlink() or not source.is_file() or not source.resolve().is_relative_to(attempt_root):
            raise OwnerLocalMeasuredRunnerV16Error("partial cell artifact is unsafe")
        target = archive / source.name
        os.replace(source, target)
        moved.append({"role": role, "filename": target.name, "sha256": file_sha256(target)})
    body = {
        "schema_version": "myis.armindex-a1.2-owner-local-partial-cell-recovery.v16",
        "attempt_id": attempt_root.name,
        "cell_id": cell_id,
        "status": "UNCOMMITTED_PARTIAL_PRESERVED",
        "retry_count": retry_count,
        "artifacts": moved,
    }
    _atomic(archive / "recovery.json", {**body, "recovery_sha256": canonical_sha256(body)})
    return retry_count


def _failure_category(error: BaseException) -> str:
    if isinstance(error, MemoryError) or "outofmemory" in type(error).__name__.lower():
        return "oom"
    if isinstance(error, RawMaterializerBridgeV16Error):
        return "input"
    if isinstance(error, MeasuredExecutorV16Error):
        return "runtime"
    return "unknown"


def _failure_metrics_sidecar(
    *,
    manifest: Mapping[str, Any],
    cell: Mapping[str, Any],
    compile_latency_ms: float,
    wall_seconds: float,
    peak_host_ram_bytes: int,
    peak_vram_bytes: int,
    error: BaseException,
    retry_count: int,
) -> dict[str, Any]:
    """Write only category/count/resource facts for a failed executable cell."""

    category = _failure_category(error)
    body = {
        "schema_version": FAILURE_METRICS_SCHEMA,
        "receipt_id": f"{manifest['attempt_id']}--{cell['cell_id']}--metrics-failure",
        "attempt_id": manifest["attempt_id"],
        "cell_id": cell["cell_id"],
        "status": "FAILED",
        "aggregate_safe": True,
        "manifest_sha256": manifest["manifest_sha256"],
        "attempt_binding_sha256": canonical_sha256(
            {
                "attempt_id": manifest["attempt_id"],
                "cell_id": cell["cell_id"],
                "binding_sha256": cell["binding_sha256"],
                "manifest_sha256": manifest["manifest_sha256"],
            }
        ),
        "binding_sha256": cell["binding_sha256"],
        "performance": {
            "compile_latency_ms": compile_latency_ms,
            "wall_seconds": wall_seconds,
        },
        "resources": {
            "peak_host_ram_bytes": peak_host_ram_bytes,
            "peak_vram_bytes": peak_vram_bytes,
        },
        "reliability": {
            "retry_count": retry_count,
            "oom_count": int(category == "oom"),
            "failure_category": category,
        },
    }
    return {**body, "metrics_sha256": canonical_sha256(body)}


def _validate_metrics_sidecar(
    value: Mapping[str, Any], *, receipt: Mapping[str, Any], cell: Mapping[str, Any], manifest_sha256: str
) -> None:
    body = {key: item for key, item in value.items() if key != "metrics_sha256"}
    if (
        value.get("schema_version") != METRICS_SCHEMA
        or value.get("status") != "PASS"
        or value.get("aggregate_safe") is not True
        or value.get("receipt_id") != f"{receipt['attempt_id']}--{cell['cell_id']}--metrics"
        or value.get("attempt_id") != receipt["attempt_id"]
        or value.get("manifest_sha256") != manifest_sha256
        or value.get("cell_id") != cell["cell_id"]
        or value.get("binding_sha256") != cell["binding_sha256"]
        or value.get("cell_receipt_sha256") != receipt["receipt_sha256"]
        or value.get("ranking_file_sha256") != receipt["ranking_file_sha256"]
        or value.get("ranking_set_sha256") != receipt["ranking_set_sha256"]
        or value.get("metrics_sha256") != canonical_sha256(body)
    ):
        raise OwnerLocalMeasuredRunnerV16Error("cell metrics sidecar is invalid")
    performance, resources, reliability = value.get("performance"), value.get("resources"), value.get("reliability")
    resource_sampling = value.get("resource_sampling")
    expected_attempt_binding = canonical_sha256(
        {
            "attempt_id": receipt["attempt_id"],
            "cell_id": cell["cell_id"],
            "binding_sha256": cell["binding_sha256"],
            "manifest_sha256": manifest_sha256,
        }
    )
    if value.get("attempt_binding_sha256") != expected_attempt_binding:
        raise OwnerLocalMeasuredRunnerV16Error("cell metrics attempt binding is invalid")
    if (
        not isinstance(performance, Mapping)
        or set(performance) != {"compile_latency_ms", "index_latency_ms", "query_encode_latency_ms", "search_latency_ms", "throughput_qps", "wall_seconds"}
        or not isinstance(resources, Mapping)
        or set(resources) != {"peak_host_ram_bytes", "peak_vram_bytes", "index_size_bytes"}
        or resource_sampling != {
            "host_rss": "current_process_50ms",
            "vram": "pytorch_allocator_50ms_and_peak",
        }
        or not isinstance(reliability, Mapping)
        or reliability.get("replay_count", 0) < 2
        or reliability.get("ranking_replay_match") is not True
        or reliability.get("failure_category") != "none"
    ):
        raise OwnerLocalMeasuredRunnerV16Error("cell metrics sidecar fields are invalid")
    if (
        not isinstance(performance["search_latency_ms"], Mapping)
        or set(performance["search_latency_ms"]) != {"p50", "p95", "p99"}
        or any(not isinstance(resources[key], int) or isinstance(resources[key], bool) or resources[key] < 0 for key in resources)
        or set(reliability) != {"replay_count", "replay_ranking_sha256", "ranking_replay_match", "retry_count", "oom_count", "failure_category"}
        or not isinstance(reliability["replay_count"], int)
        or not isinstance(reliability["retry_count"], int)
        or not isinstance(reliability["oom_count"], int)
        or reliability["retry_count"] < 0
        or reliability["oom_count"] != 0
        or reliability["replay_ranking_sha256"] != receipt["ranking_set_sha256"]
        or SHA256_RE.fullmatch(str(value.get("attempt_binding_sha256"))) is None
    ):
        raise OwnerLocalMeasuredRunnerV16Error("cell metrics sidecar values are invalid")
    numeric = [
        performance["compile_latency_ms"],
        performance["index_latency_ms"],
        performance["query_encode_latency_ms"],
        performance["throughput_qps"],
        performance["wall_seconds"],
        *performance["search_latency_ms"].values(),
    ]
    if (
        any(not isinstance(item, (int, float)) or not math.isfinite(item) or item < 0 for item in numeric)
        or not (
            performance["search_latency_ms"]["p50"]
            <= performance["search_latency_ms"]["p95"]
            <= performance["search_latency_ms"]["p99"]
        )
    ):
        raise OwnerLocalMeasuredRunnerV16Error("cell metrics sidecar numeric values are invalid")


def _validate_failure_metrics_sidecar(
    value: Mapping[str, Any], *, manifest: Mapping[str, Any], cell: Mapping[str, Any]
) -> None:
    body = {key: item for key, item in value.items() if key != "metrics_sha256"}
    performance, resources, reliability = (
        value.get("performance"),
        value.get("resources"),
        value.get("reliability"),
    )
    expected_binding = canonical_sha256(
        {
            "attempt_id": manifest["attempt_id"],
            "cell_id": cell["cell_id"],
            "binding_sha256": cell["binding_sha256"],
            "manifest_sha256": manifest["manifest_sha256"],
        }
    )
    if (
        value.get("schema_version") != FAILURE_METRICS_SCHEMA
        or value.get("receipt_id") != f"{manifest['attempt_id']}--{cell['cell_id']}--metrics-failure"
        or value.get("attempt_id") != manifest["attempt_id"]
        or value.get("cell_id") != cell["cell_id"]
        or value.get("status") != "FAILED"
        or value.get("aggregate_safe") is not True
        or value.get("manifest_sha256") != manifest["manifest_sha256"]
        or value.get("attempt_binding_sha256") != expected_binding
        or value.get("binding_sha256") != cell["binding_sha256"]
        or value.get("metrics_sha256") != canonical_sha256(body)
        or not isinstance(performance, Mapping)
        or set(performance) != {"compile_latency_ms", "wall_seconds"}
        or not isinstance(resources, Mapping)
        or set(resources) != {"peak_host_ram_bytes", "peak_vram_bytes"}
        or not isinstance(reliability, Mapping)
        or set(reliability) != {"retry_count", "oom_count", "failure_category"}
        or not isinstance(reliability.get("retry_count"), int)
        or reliability["retry_count"] < 0
        or reliability.get("failure_category") not in {"oom", "input", "runtime", "unknown"}
        or reliability.get("oom_count") != int(reliability.get("failure_category") == "oom")
    ):
        raise OwnerLocalMeasuredRunnerV16Error("cell failure metrics sidecar is invalid")
    numeric = [*performance.values(), *resources.values()]
    if any(not isinstance(item, (int, float)) or isinstance(item, bool) or not math.isfinite(item) or item < 0 for item in numeric):
        raise OwnerLocalMeasuredRunnerV16Error("cell failure metrics values are invalid")


def _validate_manifest(path: Path) -> tuple[Path, dict[str, Any]]:
    manifest_path = path.resolve(strict=True)
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise OwnerLocalMeasuredRunnerV16Error("input manifest is unsafe")
    root = manifest_path.parent.resolve()
    manifest = _load_json(manifest_path, role="input manifest")
    observed = manifest.get("manifest_sha256")
    if observed != canonical_sha256({key: value for key, value in manifest.items() if key != "manifest_sha256"}):
        raise OwnerLocalMeasuredRunnerV16Error("input manifest self-hash mismatch")
    if manifest.get("schema_version") != MANIFEST_SCHEMA or manifest.get("status") != "READY":
        raise OwnerLocalMeasuredRunnerV16Error("input manifest is not READY v16")
    attempt_id = manifest.get("attempt_id")
    if not isinstance(attempt_id, str) or ATTEMPT_RE.fullmatch(attempt_id) is None:
        raise OwnerLocalMeasuredRunnerV16Error("attempt identity is invalid")
    gates = manifest.get("gates")
    if not isinstance(gates, Mapping) or any(gates.get(name) != "PASS" for name in GATE_NAMES):
        raise OwnerLocalMeasuredRunnerV16Error("provider/adoption gates are not PASS")
    cells = manifest.get("cells")
    if not isinstance(cells, list) or len(cells) != 25:
        raise OwnerLocalMeasuredRunnerV16Error("manifest must bind exactly 25 cells")
    observed_cells: set[str] = set()
    for cell in cells:
        if not isinstance(cell, Mapping):
            raise OwnerLocalMeasuredRunnerV16Error("cell binding is invalid")
        required = {"cell_id", "arm_id", "program_id", "executable_program_id", "binding_path", "binding_sha256", "corpus_path", "corpus_sha256", "query_path", "query_sha256"}
        if set(cell) != required:
            raise OwnerLocalMeasuredRunnerV16Error("cell binding fields are invalid")
        cell_id = cell["cell_id"]
        if cell_id not in CELL_IDS or cell_id != f"{cell['arm_id']}--{cell['program_id']}" or cell_id in observed_cells or cell["arm_id"] not in ARM_IDS or cell["program_id"] not in ORIGINAL_PROGRAM_IDS:
            raise OwnerLocalMeasuredRunnerV16Error("cell topology is invalid")
        if cell["executable_program_id"] != EXECUTABLE_PROGRAM_IDS[cell["program_id"]]:
            raise OwnerLocalMeasuredRunnerV16Error("program ID bridge is invalid")
        for key in ("binding_sha256", "corpus_sha256", "query_sha256"):
            _hash(cell[key], role=key)
        for key in ("binding_path", "corpus_path", "query_path"):
            target = _safe_file(root, cell[key], role=key)
            if file_sha256(target) != cell[key.replace("_path", "_sha256")]:
                raise OwnerLocalMeasuredRunnerV16Error(f"{key} hash mismatch")
        observed_cells.add(cell_id)
    if observed_cells != set(CELL_IDS):
        raise OwnerLocalMeasuredRunnerV16Error("manifest cell set is incomplete")
    if tuple(cell["cell_id"] for cell in cells) != CELL_IDS:
        raise OwnerLocalMeasuredRunnerV16Error("manifest cell order is not canonical")
    work = manifest.get("work_tokens")
    if not isinstance(work, Mapping) or set(work) != {"path", "sha256", "count"} or work["count"] != 150:
        raise OwnerLocalMeasuredRunnerV16Error("manifest work-token commitment is invalid")
    _hash(work["sha256"], role="work-token")
    work_path = _safe_file(root, work["path"], role="work-token")
    if file_sha256(work_path) != work["sha256"]:
        raise OwnerLocalMeasuredRunnerV16Error("work-token hash mismatch")
    return root, manifest


def validate_manifest(manifest_path: Path) -> dict[str, Any]:
    """Validate and return only aggregate-safe manifest facts."""

    _root, manifest = _validate_manifest(manifest_path)
    return {"status": "PASS", "attempt_id": manifest["attempt_id"], "cells": 25, "work_token_count": 150, "top_k": 100, "manifest_sha256": manifest["manifest_sha256"]}


def run_owner_local_measured_screen(
    manifest_path: Path,
    *,
    output_root: Path,
    adapters: Mapping[str, DenseEmbeddingAdapter] | None = None,
    batch_executor: Callable[..., Mapping[str, Sequence[Any]]] = execute_program_cell_batch,
    arm_ids: Sequence[str] = ARM_IDS,
    measured_mode: bool = True,
) -> dict[str, Any]:
    """Run the selected complete arm set and emit aggregate-safe receipts.

    Measured mode is explicit and only admits the frozen production executor.
    Test callbacks must declare ``measured_mode=False`` and cannot produce a
    scientific-performance sidecar.
    """

    root, manifest = _validate_manifest(manifest_path)
    selected_arms = tuple(arm_ids)
    if (
        not selected_arms
        or len(selected_arms) != len(set(selected_arms))
        or any(arm not in ARM_IDS for arm in selected_arms)
    ):
        raise OwnerLocalMeasuredRunnerV16Error("selected arm set is invalid")
    if not isinstance(measured_mode, bool):
        raise OwnerLocalMeasuredRunnerV16Error("measured mode is invalid")
    if measured_mode and batch_executor is not execute_program_cell_batch:
        raise OwnerLocalMeasuredRunnerV16Error("measured mode requires the frozen production executor")
    output = output_root.resolve()
    if output.is_relative_to(Path.cwd().resolve()):
        raise OwnerLocalMeasuredRunnerV16Error("receipt output must remain outside the repository")
    work_path = _safe_file(root, manifest["work_tokens"]["path"], role="work-token")
    work_rows = _read_jsonl(work_path, role="work-token input")
    if len(work_rows) != 150:
        raise OwnerLocalMeasuredRunnerV16Error("work-token input must contain exactly 150 rows")
    work_tokens: list[str] = []
    query_tokens: set[str] = set()
    for row in work_rows:
        token = row.get("work_token")
        if not isinstance(token, str) or not token.startswith("Q-") or TOKEN_RE.fullmatch(token) is None or token in query_tokens:
            raise OwnerLocalMeasuredRunnerV16Error("work-token input domain is invalid")
        work_tokens.append(token)
        query_tokens.add(token)
    if len(work_tokens) != 150:
        raise OwnerLocalMeasuredRunnerV16Error("work-token set is incomplete")
    token_set_hash = canonical_sha256({"work_tokens": sorted(work_tokens)})
    cell_receipts: list[dict[str, Any]] = []
    cell_metrics_sha256s: list[str] = []
    cell_commit_sha256s: list[str] = []
    attempt_root = output / manifest["attempt_id"]
    if attempt_root.exists() and (attempt_root.is_symlink() or not attempt_root.is_dir()):
        raise OwnerLocalMeasuredRunnerV16Error("receipt attempt root is unsafe")
    receipts_root = attempt_root / "receipts"
    rankings_root = attempt_root / "rankings"
    metrics_root = attempt_root / "metrics"
    commits_root = attempt_root / "commits"
    production_instrumentation = measured_mode
    for cell in manifest["cells"]:
        if cell["arm_id"] not in selected_arms:
            continue
        existing_receipt_path = receipts_root / f"{cell['cell_id']}.json"
        existing_ranking_path = rankings_root / f"{cell['cell_id']}.jsonl"
        existing_metrics_path = metrics_root / f"{cell['cell_id']}.json"
        existing_failure_metrics_path = metrics_root / f"{cell['cell_id']}.failure.json"
        existing_commit_path = commits_root / f"{cell['cell_id']}.json"
        cell_retry_count = 0
        if existing_failure_metrics_path.exists():
            if existing_failure_metrics_path.is_symlink() or not existing_failure_metrics_path.is_file():
                raise OwnerLocalMeasuredRunnerV16Error("existing cell failure metrics sidecar is unsafe")
            _validate_failure_metrics_sidecar(
                _load_json(existing_failure_metrics_path, role="existing cell failure metrics sidecar"),
                manifest=manifest,
                cell=cell,
            )
            raise OwnerLocalMeasuredRunnerV16Error("existing failed cell requires a fresh attempt")
        current_artifacts = {
            "ranking": existing_ranking_path,
            "receipt": existing_receipt_path,
            "metrics": existing_metrics_path,
            "commit": existing_commit_path,
        }
        if production_instrumentation and any(path.exists() for path in current_artifacts.values()) and not all(path.exists() for path in current_artifacts.values()):
            cell_retry_count = _archive_partial_cell(
                attempt_root=attempt_root,
                cell_id=cell["cell_id"],
                artifacts=current_artifacts,
            )
        if (
            existing_receipt_path.exists()
            or existing_ranking_path.exists()
            or existing_metrics_path.exists()
            or existing_commit_path.exists()
        ):
            if (
                not existing_receipt_path.is_file()
                or not existing_ranking_path.is_file()
                or (production_instrumentation and not existing_metrics_path.is_file())
                or (production_instrumentation and not existing_commit_path.is_file())
            ):
                raise OwnerLocalMeasuredRunnerV16Error("partial cell artifacts are inconsistent")
            existing = _load_json(existing_receipt_path, role="existing cell receipt")
            existing_body = {key: value for key, value in existing.items() if key != "receipt_sha256"}
            if (
                existing.get("schema_version") != RECEIPT_SCHEMA
                or existing.get("attempt_id") != manifest["attempt_id"]
                or existing.get("cell_id") != cell["cell_id"]
                or existing.get("arm_id") != cell["arm_id"]
                or existing.get("program_id") != cell["program_id"]
                or existing.get("executable_program_id") != cell["executable_program_id"]
                or existing.get("binding_sha256") != cell["binding_sha256"]
                or existing.get("status") != "PASS"
                or existing.get("aggregate_safe") is not True
                or existing.get("work_token_count") != 150
                or existing.get("returned_row_count") != 150
                or existing.get("top_k") != 100
                or existing.get("ranking_path") != f"rankings/{cell['cell_id']}.jsonl"
                or existing.get("receipt_sha256") != canonical_sha256(existing_body)
                or file_sha256(existing_ranking_path) != existing.get("ranking_file_sha256")
            ):
                raise OwnerLocalMeasuredRunnerV16Error("existing cell artifact is incompatible with manifest")
            ranking_rows = _read_jsonl(existing_ranking_path, role="existing ranking")
            observed_tokens: set[str] = set()
            for row in ranking_rows:
                if set(row) != {"work_token", "family_tokens"}:
                    raise OwnerLocalMeasuredRunnerV16Error("existing ranking row is invalid")
                token, families = row["work_token"], row["family_tokens"]
                if token not in query_tokens or token in observed_tokens or not isinstance(families, list) or len(families) != 100 or len(set(families)) != 100 or any(not isinstance(value, str) or TOKEN_RE.fullmatch(value) is None or not value.startswith("F-") for value in families):
                    raise OwnerLocalMeasuredRunnerV16Error("existing ranking coverage is invalid")
                observed_tokens.add(token)
            if observed_tokens != query_tokens:
                raise OwnerLocalMeasuredRunnerV16Error("existing ranking query coverage is incomplete")
            if production_instrumentation:
                if existing_metrics_path.is_symlink() or not existing_metrics_path.is_file():
                    raise OwnerLocalMeasuredRunnerV16Error("existing cell metrics sidecar is unsafe")
                existing_metrics = _load_json(existing_metrics_path, role="existing cell metrics sidecar")
                _validate_metrics_sidecar(
                    existing_metrics,
                    receipt=existing,
                    cell=cell,
                    manifest_sha256=manifest["manifest_sha256"],
                )
                existing_commit = _load_json(existing_commit_path, role="existing cell commit marker")
                _validate_cell_commit(
                    existing_commit,
                    manifest=manifest,
                    cell=cell,
                    receipt=existing,
                    metrics=existing_metrics,
                )
                cell_metrics_sha256s.append(existing_metrics["metrics_sha256"])
                cell_commit_sha256s.append(existing_commit["commit_sha256"])
            cell_receipts.append(existing)
            continue
        cell_started = time.perf_counter_ns()
        # 50ms current-process RSS plus PyTorch allocator sampling covers compile,
        # materialization, indexing, encoding, and search for this cell.
        resources = _PeakResources()
        resources.start()
        corpus_rows = _read_jsonl(_safe_file(root, cell["corpus_path"], role="compiled corpus"), role="compiled corpus")
        adapter = None if cell["arm_id"] == "ARM-01" else (adapters or {}).get(cell["arm_id"])
        raw_corpus = bool(corpus_rows and {"claims", "claims_text", "publication_token"}.issubset(corpus_rows[0]))
        try:
            if raw_corpus:
                corpus = materialize_raw_corpus(
                    corpus_rows,
                    arm_id=cell["arm_id"],
                    program_id=cell["executable_program_id"],
                    adapter=adapter,
                )
            else:
                corpus = tuple(_logical(row, role="compiled corpus") for row in corpus_rows)
        except RawMaterializerBridgeV16Error as error:
            resources.stop()
            raise OwnerLocalMeasuredRunnerV16Error("raw corpus materialization failed") from error
        query_path = _safe_file(root, cell["query_path"], role="compiled query")
        query_rows = _read_jsonl(query_path, role="compiled query")
        if len(query_rows) != 150 or {row.get("work_token") for row in query_rows} != query_tokens:
            resources.stop()
            raise OwnerLocalMeasuredRunnerV16Error("compiled query coverage is not exactly 150 opaque work tokens")
        query_by_token = {str(row["work_token"]): row for row in query_rows}
        batch_queries: dict[str, str | LogicalInput] = {}
        for token in work_tokens:
            row = query_by_token[token]
            try:
                if "physical_inputs" in row:
                    batch_queries[token] = _logical(row, role="compiled query", query=True)
                elif cell["arm_id"] == "ARM-01" or not raw_corpus:
                    text = row.get("text")
                    if not isinstance(text, str) or not text:
                        raise RawMaterializerBridgeV16Error("raw query text is invalid")
                    batch_queries[token] = text
                else:
                    batch_queries[token] = materialize_raw_query(
                        row, arm_id=cell["arm_id"], adapter=adapter
                    )
            except RawMaterializerBridgeV16Error as error:
                resources.stop()
                raise OwnerLocalMeasuredRunnerV16Error("raw query materialization failed") from error
        if cell["arm_id"] != "ARM-01" and adapter is None:
            resources.stop()
            raise OwnerLocalMeasuredRunnerV16Error("dense adapter is missing")
        compile_latency_ms = (time.perf_counter_ns() - cell_started) / 1_000_000
        rank_hashes: list[str] = []
        ranking_lines: list[str] = []
        try:
            if production_instrumentation:
                execution = execute_program_cell_batch_instrumented(
                    arm_id=cell["arm_id"],
                    program_id=cell["executable_program_id"],
                    corpus=corpus,
                    queries=batch_queries,
                    adapter=adapter,
                )
                rankings = execution.rankings
            else:
                rankings = batch_executor(arm_id=cell["arm_id"], program_id=cell["executable_program_id"], corpus=corpus, queries=batch_queries, adapter=adapter)
                execution = None
        except BaseException as error:
            peak_host_ram_bytes, peak_vram_bytes = resources.stop()
            if production_instrumentation:
                failure_sidecar = _failure_metrics_sidecar(
                    manifest=manifest,
                    cell=cell,
                    compile_latency_ms=compile_latency_ms,
                    wall_seconds=(time.perf_counter_ns() - cell_started) / 1_000_000_000,
                    peak_host_ram_bytes=peak_host_ram_bytes,
                    peak_vram_bytes=peak_vram_bytes,
                    error=error,
                    retry_count=cell_retry_count,
                )
                _validate_failure_metrics_sidecar(failure_sidecar, manifest=manifest, cell=cell)
                _atomic(existing_failure_metrics_path, failure_sidecar)
            raise
        else:
            peak_host_ram_bytes, peak_vram_bytes = resources.stop()
        if not isinstance(rankings, Mapping) or tuple(rankings) != tuple(work_tokens):
            raise OwnerLocalMeasuredRunnerV16Error("batch executor returned incomplete work-token results")
        for token in work_tokens:
            ranks = rankings[token]
            ranking_hash, family_tokens = _ranking_rows(ranks)
            rank_hashes.append(ranking_hash)
            ranking_lines.append(_json({"work_token": token, "family_tokens": list(family_tokens)}))
        ranking_text = "".join(ranking_lines)
        ranking_sha256 = hashlib.sha256(ranking_text.encode("ascii")).hexdigest()
        ranking_relative = f"rankings/{cell['cell_id']}.jsonl"
        attempt_root.mkdir(parents=True, exist_ok=True)
        _atomic_text(attempt_root / ranking_relative, ranking_text)
        _after_cell_artifact("ranking")
        body = {
            "schema_version": RECEIPT_SCHEMA,
            "receipt_id": f"{manifest['attempt_id']}--{cell['cell_id']}",
            "attempt_id": manifest["attempt_id"],
            "cell_id": cell["cell_id"],
            "arm_id": cell["arm_id"],
            "program_id": cell["program_id"],
            "executable_program_id": cell["executable_program_id"],
            "status": "PASS",
            "aggregate_safe": True,
            "work_token_count": 150,
            "returned_row_count": 150,
            "top_k": 100,
            "work_token_set_sha256": token_set_hash,
            "ranking_set_sha256": canonical_sha256(rank_hashes),
            "ranking_path": ranking_relative,
            "ranking_file_sha256": ranking_sha256,
            "binding_sha256": cell["binding_sha256"],
        }
        body["receipt_sha256"] = canonical_sha256(body)
        _atomic(receipts_root / f"{cell['cell_id']}.json", body)
        _after_cell_artifact("receipt")
        if production_instrumentation and execution is not None:
            sidecar = _metrics_sidecar(
                manifest=manifest,
                cell=cell,
                receipt=body,
                compile_latency_ms=compile_latency_ms,
                index_latency_ms=execution.index_latency_ms,
                query_encode_latency_ms=execution.query_encode_latency_ms,
                search_latency_ms=execution.search_latency_ms,
                wall_seconds=(time.perf_counter_ns() - cell_started) / 1_000_000_000,
                peak_host_ram_bytes=peak_host_ram_bytes,
                peak_vram_bytes=peak_vram_bytes,
                index_size_bytes=execution.index_size_bytes,
                replay_count=execution.replay_count,
                replay_ranking_sha256=execution.replay_ranking_sha256,
                retry_count=cell_retry_count,
            )
            _validate_metrics_sidecar(
                sidecar,
                receipt=body,
                cell=cell,
                manifest_sha256=manifest["manifest_sha256"],
            )
            _atomic(metrics_root / f"{cell['cell_id']}.json", sidecar)
            _after_cell_artifact("metrics")
            commit = _cell_commit(manifest=manifest, cell=cell, receipt=body, metrics=sidecar)
            _validate_cell_commit(
                commit,
                manifest=manifest,
                cell=cell,
                receipt=body,
                metrics=sidecar,
            )
            _atomic(commits_root / f"{cell['cell_id']}.json", commit)
            _after_cell_artifact("commit")
            cell_metrics_sha256s.append(sidecar["metrics_sha256"])
            cell_commit_sha256s.append(commit["commit_sha256"])
        cell_receipts.append(body)
    summary_body = {
        "schema_version": SUMMARY_SCHEMA,
        "receipt_id": f"{manifest['attempt_id']}--screen",
        "attempt_id": manifest["attempt_id"],
        "status": "PASS",
        "aggregate_safe": True,
        "cell_count": len(cell_receipts),
        "work_token_count": 150,
        "top_k": 100,
        "manifest_sha256": manifest["manifest_sha256"],
        "cell_receipts_sha256": canonical_sha256([item["receipt_sha256"] for item in cell_receipts]),
    }
    if production_instrumentation:
        if len(cell_metrics_sha256s) != len(cell_receipts):
            raise OwnerLocalMeasuredRunnerV16Error("screen metrics coverage is incomplete")
        if len(cell_commit_sha256s) != len(cell_receipts):
            raise OwnerLocalMeasuredRunnerV16Error("screen cell commit coverage is incomplete")
        summary_body["cell_metrics_sha256"] = canonical_sha256(cell_metrics_sha256s)
        summary_body["cell_commits_sha256"] = canonical_sha256(cell_commit_sha256s)
    summary = {**summary_body, "receipt_sha256": canonical_sha256(summary_body)}
    output.mkdir(parents=True, exist_ok=True)
    _atomic(receipts_root / "screen.json", summary)
    return {"status": "PASS", "attempt_id": manifest["attempt_id"], "cells": len(cell_receipts), "work_tokens": 150, "top_k": 100, "receipt_sha256": summary["receipt_sha256"], "output_relative": f"{manifest['attempt_id']}/receipts"}


def merge_measured_arm_outputs(
    manifest_path: Path,
    *,
    arm_output_roots: Mapping[str, Path],
    output_root: Path,
) -> dict[str, Any]:
    """Validate five complete arm outputs and merge the unchanged payloads."""

    _root, manifest = _validate_manifest(manifest_path)
    if set(arm_output_roots) != set(ARM_IDS):
        raise OwnerLocalMeasuredRunnerV16Error("merge requires all five arms")
    output = output_root.resolve()
    if output.is_relative_to(Path.cwd().resolve()):
        raise OwnerLocalMeasuredRunnerV16Error("merged output must remain outside the repository")
    attempt_id = manifest["attempt_id"]
    work_path = _safe_file(_root, manifest["work_tokens"]["path"], role="work-token")
    work_rows = _read_jsonl(work_path, role="work-token input")
    work_tokens = tuple(str(row.get("work_token")) for row in work_rows)
    if len(work_tokens) != 150 or len(set(work_tokens)) != 150 or any(TOKEN_RE.fullmatch(token) is None or not token.startswith("Q-") for token in work_tokens):
        raise OwnerLocalMeasuredRunnerV16Error("merge work-token set is invalid")
    expected_work = set(work_tokens)
    expected_work_hash = canonical_sha256({"work_tokens": sorted(expected_work)})
    manifest_cells = {cell["cell_id"]: cell for cell in manifest["cells"]}
    receipts: list[dict[str, Any]] = []
    metrics: list[dict[str, Any]] = []
    commits: list[dict[str, Any]] = []
    sources: list[tuple[Path, str]] = []
    metrics_bound: bool | None = None
    for arm in ARM_IDS:
        arm_root = Path(arm_output_roots[arm]).resolve(strict=True)
        if arm_root.is_symlink() or not arm_root.is_dir() or arm_root.is_relative_to(Path.cwd().resolve()):
            raise OwnerLocalMeasuredRunnerV16Error("arm output root is unsafe")
        attempt = arm_root / attempt_id
        summary = _load_json(attempt / "receipts" / "screen.json", role="arm screen receipt")
        summary_body = {key: value for key, value in summary.items() if key != "receipt_sha256"}
        if (
            summary.get("schema_version") != SUMMARY_SCHEMA
            or summary.get("status") != "PASS"
            or summary.get("aggregate_safe") is not True
            or summary.get("cell_count") != 5
            or summary.get("work_token_count") != 150
            or summary.get("top_k") != 100
            or summary.get("manifest_sha256") != manifest["manifest_sha256"]
            or summary.get("receipt_sha256") != canonical_sha256(summary_body)
        ):
            raise OwnerLocalMeasuredRunnerV16Error("arm screen receipt is invalid")
        arm_has_metrics = "cell_metrics_sha256" in summary
        if arm_has_metrics and (
            SHA256_RE.fullmatch(str(summary["cell_metrics_sha256"])) is None
            or SHA256_RE.fullmatch(str(summary.get("cell_commits_sha256"))) is None
        ):
            raise OwnerLocalMeasuredRunnerV16Error("arm screen metrics binding is invalid")
        if not arm_has_metrics and "cell_commits_sha256" in summary:
            raise OwnerLocalMeasuredRunnerV16Error("arm screen cell commit binding is invalid")
        if metrics_bound is None:
            metrics_bound = arm_has_metrics
        elif metrics_bound != arm_has_metrics:
            raise OwnerLocalMeasuredRunnerV16Error("arm screen metrics coverage is inconsistent")
        arm_metric_hashes: list[str] = []
        arm_commit_hashes: list[str] = []
        for cell in (value for value in CELL_IDS if value.startswith(f"{arm}--")):
            receipt_path = attempt / "receipts" / f"{cell}.json"
            receipt = _load_json(receipt_path, role="arm cell receipt")
            binding = manifest_cells[cell]
            receipt_body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
            ranking_relative = f"rankings/{cell}.jsonl"
            ranking_path = attempt / ranking_relative
            if (
                receipt.get("schema_version") != RECEIPT_SCHEMA
                or receipt.get("attempt_id") != attempt_id
                or receipt.get("cell_id") != cell
                or receipt.get("arm_id") != arm
                or receipt.get("program_id") != binding["program_id"]
                or receipt.get("executable_program_id") != binding["executable_program_id"]
                or receipt.get("binding_sha256") != binding["binding_sha256"]
                or receipt.get("status") != "PASS"
                or receipt.get("aggregate_safe") is not True
                or receipt.get("work_token_count") != 150
                or receipt.get("returned_row_count") != 150
                or receipt.get("top_k") != 100
                or receipt.get("work_token_set_sha256") != expected_work_hash
                or receipt.get("ranking_path") != ranking_relative
                or receipt.get("receipt_sha256") != canonical_sha256(receipt_body)
                or not ranking_path.is_file()
                or ranking_path.is_symlink()
                or file_sha256(ranking_path) != receipt.get("ranking_file_sha256")
            ):
                raise OwnerLocalMeasuredRunnerV16Error("arm cell receipt is invalid")
            ranking_rows = _read_jsonl(ranking_path, role="arm ranking")
            observed_work: set[str] = set()
            for row in ranking_rows:
                if set(row) != {"work_token", "family_tokens"}:
                    raise OwnerLocalMeasuredRunnerV16Error("arm ranking row is invalid")
                token, families = row["work_token"], row["family_tokens"]
                if (
                    token not in expected_work
                    or token in observed_work
                    or not isinstance(families, list)
                    or len(families) != 100
                    or len(set(families)) != 100
                    or any(not isinstance(value, str) or TOKEN_RE.fullmatch(value) is None or not value.startswith("F-") for value in families)
                ):
                    raise OwnerLocalMeasuredRunnerV16Error("arm ranking coverage is invalid")
                observed_work.add(token)
            if observed_work != expected_work:
                raise OwnerLocalMeasuredRunnerV16Error("arm ranking work-token set is incomplete")
            receipts.append(receipt)
            sources.extend(((ranking_path, ranking_relative), (receipt_path, f"receipts/{cell}.json")))
            if arm_has_metrics:
                metrics_path = attempt / "metrics" / f"{cell}.json"
                if metrics_path.is_symlink() or not metrics_path.is_file():
                    raise OwnerLocalMeasuredRunnerV16Error("arm cell metrics sidecar is unsafe")
                metric = _load_json(metrics_path, role="arm cell metrics sidecar")
                _validate_metrics_sidecar(
                    metric,
                    receipt=receipt,
                    cell=binding,
                    manifest_sha256=manifest["manifest_sha256"],
                )
                arm_metric_hashes.append(metric["metrics_sha256"])
                metrics.append(metric)
                sources.append((metrics_path, f"metrics/{cell}.json"))
                commit_path = attempt / "commits" / f"{cell}.json"
                if commit_path.is_symlink() or not commit_path.is_file():
                    raise OwnerLocalMeasuredRunnerV16Error("arm cell commit marker is unsafe")
                commit = _load_json(commit_path, role="arm cell commit marker")
                _validate_cell_commit(
                    commit,
                    manifest=manifest,
                    cell=binding,
                    receipt=receipt,
                    metrics=metric,
                )
                arm_commit_hashes.append(commit["commit_sha256"])
                commits.append(commit)
                sources.append((commit_path, f"commits/{cell}.json"))
        if arm_has_metrics and summary["cell_metrics_sha256"] != canonical_sha256(arm_metric_hashes):
            raise OwnerLocalMeasuredRunnerV16Error("arm screen metrics binding mismatch")
        if arm_has_metrics and summary["cell_commits_sha256"] != canonical_sha256(arm_commit_hashes):
            raise OwnerLocalMeasuredRunnerV16Error("arm screen cell commit binding mismatch")
    ordered_receipts = sorted(receipts, key=lambda value: CELL_IDS.index(value["cell_id"]))
    if len(ordered_receipts) != 25:
        raise OwnerLocalMeasuredRunnerV16Error("merged cell set is not 25/25")
    summary_body = {
        "schema_version": SUMMARY_SCHEMA,
        "receipt_id": f"{attempt_id}--screen",
        "attempt_id": attempt_id,
        "status": "PASS",
        "aggregate_safe": True,
        "cell_count": 25,
        "work_token_count": 150,
        "top_k": 100,
        "manifest_sha256": manifest["manifest_sha256"],
        "cell_receipts_sha256": canonical_sha256([item["receipt_sha256"] for item in ordered_receipts]),
    }
    if metrics_bound:
        ordered_metrics = sorted(metrics, key=lambda value: CELL_IDS.index(value["cell_id"]))
        if len(ordered_metrics) != 25:
            raise OwnerLocalMeasuredRunnerV16Error("merged metrics set is not 25/25")
        ordered_commits = sorted(commits, key=lambda value: CELL_IDS.index(value["cell_id"]))
        if len(ordered_commits) != 25:
            raise OwnerLocalMeasuredRunnerV16Error("merged cell commit set is not 25/25")
        summary_body["cell_metrics_sha256"] = canonical_sha256(
            [item["metrics_sha256"] for item in ordered_metrics]
        )
        summary_body["cell_commits_sha256"] = canonical_sha256(
            [item["commit_sha256"] for item in ordered_commits]
        )
    summary = {**summary_body, "receipt_sha256": canonical_sha256(summary_body)}
    attempt_root = output / attempt_id
    if attempt_root.exists():
        raise OwnerLocalMeasuredRunnerV16Error("merged output already exists")
    output.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{attempt_id}.", dir=output))
    try:
        for source, relative in sources:
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        _atomic(staging / "receipts" / "screen.json", summary)
        os.replace(staging, attempt_root)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {"status": "PASS", "attempt_id": attempt_id, "cells": 25, "work_tokens": 150, "top_k": 100, "receipt_sha256": summary["receipt_sha256"]}


__all__ = ["OwnerLocalMeasuredRunnerV16Error", "merge_measured_arm_outputs", "run_owner_local_measured_screen", "validate_manifest"]
