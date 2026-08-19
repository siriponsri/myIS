"""Remote retrieval-only worker for fresh ArmIndex A4 profile requests.

It reads only opaque corpus/query assets and frozen local model trees.  Qrels,
membership, Selection, and Final are unavailable to this module.  Its ranking
payload is transient and must return only to an Owner-local evaluator.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import json
import math
import os
from pathlib import Path
import time
from typing import Any

try:
    import resource
except ImportError:  # pragma: no cover - Windows development host
    resource = None  # type: ignore[assignment]

from ..kernel.canonical import canonical_json, canonical_sha256, file_sha256
from .a1_2_measured_executor_v16 import SentenceTransformerDenseAdapter
from .a2_owner_local_engine import _corpus_rows, _queries, _rank_dense
from .a2_program_runtime import compile_program
from .bm25s_adapter import BM25sAdapter
from .fusion import fuse_rankings
from .scientific_common_programs_v11 import compile_common_program


_DENSE_ARMS = ("ARM-03", "ARM-04", "ARM-05")
_COMMERCIAL_ARMS = ("ARM-01", "ARM-02", "ARM-04", "ARM-05")
_REQUEST_KEYS = {
    "schema_version",
    "attempt_id",
    "request_id",
    "profile_id",
    "system_sha256",
    "profile_registry_sha256",
    "runtime_bindings_sha256",
    "hdev_scope_sha256",
    "arm_ids",
    "candidate_depth",
    "mode",
    "license_scope",
    "request_sha256",
}


class A4RemoteRankerError(ValueError):
    """Raised without revealing an input row, token, or ranking."""


def build_a4_profile_request(
    *,
    attempt_id: str,
    profile_registry: Mapping[str, Any],
    runtime_bindings: Mapping[str, Any],
    profile_id: str,
) -> dict[str, Any]:
    """Create an immutable request for one named commercial profile/reference."""

    registry = _profile_registry(profile_registry, attempt_id=attempt_id)
    runtime = _runtime_bindings(runtime_bindings, attempt_id=attempt_id)
    if runtime["profile_registry_sha256"] != registry["registry_sha256"]:
        raise A4RemoteRankerError("A4 runtime does not bind the profile registry")
    profiles = {item["profile_id"]: item for item in registry["profiles"]}
    if profile_id in profiles:
        profile = profiles[profile_id]
        arm_ids = profile["arm_ids"]
        mode = profile["mode"]
        depth = profile["candidate_depth"]
        system = profile["system_sha256"]
        scope = "commercial_capable"
    elif profile_id == "ARM-03_RESEARCH_REFERENCE":
        reference = registry["research_reference"]
        arm_ids = reference["arm_ids"]
        mode, depth, system, scope = "synchronous", 100, reference["system_sha256"], "research_only"
    else:
        raise A4RemoteRankerError("unknown A4 profile request")
    body = {
        "schema_version": "myis.armindex-a4-remote-profile-request.v1",
        "attempt_id": attempt_id,
        "request_id": f"{attempt_id}--{profile_id.lower()}",
        "profile_id": profile_id,
        "system_sha256": system,
        "profile_registry_sha256": registry["registry_sha256"],
        "runtime_bindings_sha256": runtime["runtime_bindings_sha256"],
        "hdev_scope_sha256": runtime["hdev_scope_sha256"],
        "arm_ids": arm_ids,
        "candidate_depth": depth,
        "mode": mode,
        "license_scope": scope,
    }
    return {**body, "request_sha256": canonical_sha256(body)}


def run_a4_profile_ranker(
    request_path: Path,
    *,
    assets_root: Path,
    result_path: Path,
) -> dict[str, Any]:
    """Run one frozen A4 profile over exactly 100 HDEV opaque work tokens."""

    request = _request(_load_json(request_path, "A4 profile request"))
    root = _directory(assets_root, "A4 assets")
    runtime = _runtime_bindings(_load_json(root.parent / "A4_RUNTIME_BINDINGS.json", "A4 runtime bindings"), attempt_id=request["attempt_id"])
    if runtime["runtime_bindings_sha256"] != request["runtime_bindings_sha256"]:
        raise A4RemoteRankerError("A4 request runtime binding drift")
    scope = _scope(_load_json(root / "hdev-scope.json", "A4 HDEV scope"))
    if scope["scope_sha256"] != request["hdev_scope_sha256"]:
        raise A4RemoteRankerError("A4 request HDEV scope drift")
    inventory = _inventory(_load_json(root / "A4_RUNTIME_ASSETS.json", "A4 inventory"), root)
    if inventory["inventory_sha256"] != runtime["asset_inventory_sha256"]:
        raise A4RemoteRankerError("A4 asset inventory binding drift")
    queries = _queries(root / "queries.jsonl")
    if len(queries) != 100:
        raise A4RemoteRankerError("A4 ranker requires exactly HDEV-100")
    started = time.perf_counter()
    rankings_by_arm: dict[str, dict[str, list[dict[str, Any]]]] = {}
    latencies: list[float] = []
    for arm_id in request["arm_ids"]:
        ranks, current = _rank_one(root, arm_id=arm_id, queries=queries)
        rankings_by_arm[arm_id] = ranks
        latencies.extend(current)
    rankings = _fuse(rankings_by_arm, depth=request["candidate_depth"])
    body = {
        "rankings": rankings,
        "coverage": {"expected_units": 100, "completed_units": len(rankings)},
        "latency": {
            "wall_seconds": time.perf_counter() - started,
            "search_p50_seconds": _percentile(latencies, 0.5),
            "search_p95_seconds": _percentile(latencies, 0.95),
            "search_p99_seconds": _percentile(latencies, 0.99),
        },
        "resource": _resource_metrics(root, started, request["arm_ids"]),
    }
    _write_new_json(result_path, body)
    return body


def _resource_metrics(root: Path, started: float, arm_ids: Sequence[str]) -> dict[str, Any]:
    """Return aggregate-safe runtime resources required by the Owner evaluator."""
    elapsed = max(0.0, time.perf_counter() - started)
    rate = float(os.environ.get("A4_HOURLY_RATE_USD", "0.6455555555555554"))
    if not math.isfinite(rate) or rate < 0:
        raise A4RemoteRankerError("A4 hourly rate is invalid")
    ram_gib = 0.0
    if resource is not None:
        ram_gib = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / (1024 ** 2)
    vram_gib = 0.0
    try:
        import torch

        vram_gib = max(float(torch.cuda.max_memory_allocated(i)) for i in range(torch.cuda.device_count())) / (1024 ** 3) if torch.cuda.is_available() else 0.0
    except (ImportError, RuntimeError, ValueError):
        vram_gib = 0.0
    index_size = sum(path.stat().st_size for path in root.rglob("*") if path.is_file())
    return {
        "gpu_ids": _gpu_ids(arm_ids),
        "mode": "measured",
        "cost_usd": rate * elapsed / 3600.0,
        "ram_gib": max(0.0, ram_gib),
        "vram_gib": max(0.0, vram_gib),
        "index_size_bytes": int(index_size),
    }


def _rank_one(root: Path, *, arm_id: str, queries: Mapping[str, str]) -> tuple[dict[str, list[dict[str, Any]]], list[float]]:
    if arm_id == "ARM-01":
        return _rank_common_bm25(root, queries)
    if arm_id not in _DENSE_ARMS:
        raise A4RemoteRankerError("A4 profile contains unsupported arm")
    program = _load_json(root / "programs" / f"{arm_id}.json", f"{arm_id} program")
    if program.get("arm_id") != arm_id or not isinstance(program.get("program_sha256"), str):
        raise A4RemoteRankerError("A4 winner program identity is invalid")
    corpus = _corpus_rows(root / "corpus.jsonl", program)
    compiled = compile_program(corpus, program)
    ranks, latencies = _rank_dense(
        compiled.units,
        queries,
        arm_id=arm_id,
        model_directory=root / "models" / arm_id,
        device=_device_for_arm(arm_id),
        method=compiled.family_aggregation,
        adapter_factory=SentenceTransformerDenseAdapter.from_staged_directory,
    )
    return _serialise(ranks), list(latencies)


def _rank_common_bm25(root: Path, queries: Mapping[str, str]) -> tuple[dict[str, list[dict[str, Any]]], list[float]]:
    rows = []
    for line in (root / "corpus.jsonl").read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        if not isinstance(item, dict):
            raise A4RemoteRankerError("A4 corpus record is invalid")
        rows.append(item)
    try:
        compiled = compile_common_program("P00-TAC-DOC", rows)
    except ValueError as error:
        raise A4RemoteRankerError("A4 static BM25 compilation failed") from error
    documents = [{"doc_id": unit.unit_id, "family_id": unit.family_token, "text": unit.text} for unit in compiled.units]
    adapter = BM25sAdapter()
    index = adapter.build_index(documents)
    result: dict[str, list[dict[str, Any]]] = {}
    latencies: list[float] = []
    for token, query in queries.items():
        started = time.perf_counter()
        rows = adapter.search(index, query)
        latencies.append(time.perf_counter() - started)
        seen: set[str] = set()
        ranking: list[dict[str, Any]] = []
        for _doc, family, score in rows:
            if family in seen:
                continue
            seen.add(family)
            ranking.append({"family_token": family, "rank": len(ranking) + 1, "score": float(score)})
            if len(ranking) == 100:
                break
        if len(ranking) != 100:
            raise A4RemoteRankerError("A4 static BM25 cannot return top 100")
        result[token] = ranking
    return result, latencies


def _fuse(rankings_by_arm: Mapping[str, Mapping[str, Sequence[Mapping[str, Any]]]], *, depth: int) -> dict[str, list[dict[str, Any]]]:
    # Profiles may build a deeper candidate pool, but every returned result is
    # normalized to the frozen OUT top-100 evaluator depth.
    if not isinstance(depth, int) or isinstance(depth, bool) or depth < 100:
        raise A4RemoteRankerError("A4 candidate depth must be at least 100")
    tokens = set.intersection(*(set(value) for value in rankings_by_arm.values())) if rankings_by_arm else set()
    if len(tokens) != 100 or any(set(value) != tokens for value in rankings_by_arm.values()):
        raise A4RemoteRankerError("A4 profile coverage is incomplete")
    result: dict[str, list[dict[str, Any]]] = {}
    for token in sorted(tokens):
        if len(rankings_by_arm) == 1:
            result[token] = list(next(iter(rankings_by_arm.values()))[token])
            continue
        fused = fuse_rankings(
            {arm: [row["family_token"] for row in rows[token]] for arm, rows in rankings_by_arm.items()},
            method="rrf",
            rrf_k=60,
            limit=100,
        )
        if len(fused) != 100:
            raise A4RemoteRankerError("A4 fused profile cannot return top 100")
        result[token] = [
            {"family_token": row.family_token, "rank": index, "score": float(row.score)}
            for index, row in enumerate(fused, start=1)
        ]
    return result


def _serialise(rankings: Mapping[str, Sequence[Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for token, rows in rankings.items():
        if len(rows) != 100:
            raise A4RemoteRankerError("A4 dense arm cannot return top 100")
        result[token] = [
            {"family_token": row.family_token, "rank": row.rank, "score": float(row.score)} for row in rows
        ]
    return result


def _profile_registry(value: Mapping[str, Any], *, attempt_id: str) -> dict[str, Any]:
    item = dict(value)
    if item.get("schema_version") != "myis.armindex-a4-profile-registry.v1" or item.get("attempt_id") != attempt_id:
        raise A4RemoteRankerError("A4 profile registry identity is invalid")
    _self_hash(item, "registry_sha256", "A4 profile registry")
    return item


def _runtime_bindings(value: Mapping[str, Any], *, attempt_id: str) -> dict[str, Any]:
    item = dict(value)
    if item.get("schema_version") != "myis.armindex-a4-runtime-bindings.v1" or item.get("attempt_id") != attempt_id:
        raise A4RemoteRankerError("A4 runtime binding identity is invalid")
    _self_hash(item, "runtime_bindings_sha256", "A4 runtime bindings")
    return item


def _scope(value: Mapping[str, Any]) -> dict[str, Any]:
    item = dict(value)
    if item.get("schema_version") != "myis.armindex-a4-harness-dev-scope.v1" or item.get("scope") != "HARNESS-DEV" or item.get("query_count") != 100:
        raise A4RemoteRankerError("A4 HDEV scope is invalid")
    _self_hash(item, "scope_sha256", "A4 HDEV scope")
    return item


def _inventory(value: Mapping[str, Any], root: Path) -> dict[str, Any]:
    item = dict(value)
    if item.get("schema_version") != "myis.armindex-a4-runtime-assets-inventory.v1":
        raise A4RemoteRankerError("A4 runtime asset inventory identity is invalid")
    _self_hash(item, "inventory_sha256", "A4 runtime inventory")
    expected = item.get("asset_sha256s")
    if not isinstance(expected, Mapping):
        raise A4RemoteRankerError("A4 runtime asset inventory is invalid")
    observed: dict[str, str] = {}
    for path in root.rglob("*"):
        if path.is_dir() or path.name == "A4_RUNTIME_ASSETS.json":
            continue
        if path.is_symlink() or not path.is_file():
            raise A4RemoteRankerError("A4 runtime asset is unsafe")
        observed[path.relative_to(root).as_posix()] = file_sha256(path)
    if dict(expected) != observed:
        raise A4RemoteRankerError("A4 runtime asset hash drift")
    return item


def _request(value: Mapping[str, Any]) -> dict[str, Any]:
    item = dict(value)
    if set(item) != _REQUEST_KEYS or item.get("schema_version") != "myis.armindex-a4-remote-profile-request.v1":
        raise A4RemoteRankerError("A4 profile request schema is invalid")
    if item.get("profile_id") not in {"FAST", "BALANCED", "DEEP", "ARM-03_RESEARCH_REFERENCE"}:
        raise A4RemoteRankerError("A4 profile request identity is invalid")
    if item.get("license_scope") == "commercial_capable" and any(arm not in _COMMERCIAL_ARMS for arm in item.get("arm_ids", [])):
        raise A4RemoteRankerError("A4 commercial profile contains research arm")
    if item.get("profile_id") == "ARM-03_RESEARCH_REFERENCE" and item.get("arm_ids") != ["ARM-03"]:
        raise A4RemoteRankerError("A4 research reference must use ARM-03 only")
    if item.get("candidate_depth") != 100 or item.get("mode") not in {"synchronous", "asynchronous"}:
        raise A4RemoteRankerError("A4 profile request configuration drift")
    _self_hash(item, "request_sha256", "A4 profile request")
    return item


def _device_for_arm(arm_id: str) -> str:
    return {"ARM-03": "cuda:0", "ARM-04": "cuda:1", "ARM-05": "cuda:2"}[arm_id]


def _gpu_ids(arms: Sequence[str]) -> list[int]:
    return sorted({_device_for_arm(arm).removeprefix("cuda:") for arm in arms if arm in _DENSE_ARMS})


def _percentile(values: Sequence[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q * len(ordered)) - 1)]


def _load_json(path: Path, role: str) -> dict[str, Any]:
    try:
        candidate = Path(path).resolve(strict=True)
        if candidate.is_symlink() or not candidate.is_file():
            raise OSError
        value = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise A4RemoteRankerError(f"{role} is invalid") from error
    if not isinstance(value, dict):
        raise A4RemoteRankerError(f"{role} is invalid")
    return value


def _directory(path: Path, role: str) -> Path:
    candidate = Path(path).resolve(strict=True)
    if candidate.is_symlink() or not candidate.is_dir():
        raise A4RemoteRankerError(f"{role} is invalid")
    return candidate


def _self_hash(value: Mapping[str, Any], field: str, role: str) -> None:
    digest = value.get(field)
    if not isinstance(digest, str) or len(digest) != 64 or digest != canonical_sha256({key: item for key, item in value.items() if key != field}):
        raise A4RemoteRankerError(f"{role} self-hash mismatch")


def _write_new_json(path: Path, value: Mapping[str, Any]) -> None:
    target = Path(path)
    if target.exists() or target.is_symlink():
        raise A4RemoteRankerError("A4 profile result destination exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(canonical_json(value) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a4-remote-ranker")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--assets-root", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    run_a4_profile_ranker(args.request, assets_root=args.assets_root, result_path=args.result)
    return 0


__all__ = ["A4RemoteRankerError", "build_a4_profile_request", "run_a4_profile_ranker"]


if __name__ == "__main__":
    raise SystemExit(main())
