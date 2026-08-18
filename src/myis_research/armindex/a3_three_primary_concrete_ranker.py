"""Concrete Train-250-only ranker for three-primary A3 remote operations.

This is a retrieval-only component.  It receives opaque corpus/query assets,
never opens qrels or membership, and returns transient ranks to the remote A3
worker.  Aggregate evaluation is deliberately outside this module.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
import json
import math
import os
from pathlib import Path
import time
from typing import Any

from ..kernel.canonical import canonical_sha256, file_sha256
from .a1_2_measured_executor_v16 import SentenceTransformerDenseAdapter
from .a2_owner_local_engine import _corpus_rows, _queries, _rank_dense
from .a2_program_runtime import compile_program
from .fusion import fuse_rankings
from .a3_three_primary_execution import PRIMARY_ARMS, _validate_package_bindings
from .a3_three_primary_remote_retriever import validate_remote_cell_request


_SHA256 = set("0123456789abcdef")
_INVENTORY_KEYS = {"schema_version", "remote_asset_sha256s", "ranker_command", "inventory_sha256"}
_RUNTIME_KEYS = {
    "schema_version", "primary_arm_scope", "budget_extension_sha256", "authority_sha256",
    "manifest_sha256", "admission_sha256", "winner_bindings", "target_adapter_sha256s",
    "runtime_bindings_sha256",
}


class A3ThreePrimaryConcreteRankerError(ValueError):
    """Raised without exposing Owner-local ranker inputs or results."""


def run_a3_three_primary_ranker(
    request_path: Path,
    *,
    assets_root: Path,
    result_path: Path,
    adapter_factory: Callable[..., Any] = SentenceTransformerDenseAdapter.from_staged_directory,
    rank_dense: Callable[..., tuple[dict[str, tuple[Any, ...]], tuple[float, ...]]] = _rank_dense,
) -> dict[str, Any]:
    """Run one transfer or fixed-union operation from verified opaque assets."""

    request = validate_remote_cell_request(_load_json(request_path, role="remote request"))
    root = assets_root.resolve(strict=True)
    if root.is_symlink() or not root.is_dir():
        raise A3ThreePrimaryConcreteRankerError("A3 assets root is unsafe")
    inventory = _inventory(root, expected_assets=request["remote_asset_sha256s"])
    runtime = _runtime_bindings(root, expected_sha256=request["runtime_bindings_sha256"])
    if inventory.get("package_bindings") != runtime.get("package_bindings"):
        raise A3ThreePrimaryConcreteRankerError("runtime package commitments are not aligned")
    corpus_path, queries = _train_assets(root, inventory)
    depth = max(request["output_depth_by_arm"].values())
    started = time.perf_counter()
    if request["operation_kind"] == "transfer_cell":
        source, target = request["source_arm_id"], request["target_arm_id"]
        rankings, latencies = _rank_one(
            root, runtime, source_arm_id=source, target_arm_id=target, corpus_path=corpus_path,
            queries=queries, adapter_factory=adapter_factory, rank_dense=rank_dense,
        )
    else:
        all_rankings: dict[str, dict[str, tuple[Any, ...]]] = {}
        latencies = ()
        for arm_id in request["retrieval_arm_ids"]:
            ranks, current = _rank_one(
                root, runtime, source_arm_id=arm_id, target_arm_id=arm_id, corpus_path=corpus_path,
                queries=queries, adapter_factory=adapter_factory, rank_dense=rank_dense,
            )
            all_rankings[arm_id] = ranks
            latencies += tuple(current)
        rankings = _rrf_union(all_rankings, depth=depth)
    serialised = _serialise_rankings(rankings, depth=depth)
    body = {
        "rankings": serialised,
        "coverage": {"expected_units": len(queries), "completed_units": len(serialised)},
        "latency": {
            "wall_seconds": time.perf_counter() - started,
            "search_p95_seconds": _p95(latencies),
        },
    }
    _write_json(result_path, body)
    return body


def _rank_one(
    root: Path,
    runtime: Mapping[str, Any],
    *,
    source_arm_id: str,
    target_arm_id: str,
    corpus_path: Path,
    queries: Mapping[str, str],
    adapter_factory: Callable[..., Any],
    rank_dense: Callable[..., tuple[dict[str, tuple[Any, ...]], tuple[float, ...]]],
) -> tuple[dict[str, tuple[Any, ...]], tuple[float, ...]]:
    if source_arm_id not in PRIMARY_ARMS or target_arm_id not in PRIMARY_ARMS:
        raise A3ThreePrimaryConcreteRankerError("A3 arm is outside the primary scope")
    program_path = root / "programs" / f"{source_arm_id}.json"
    program = _load_json(program_path, role="winner program")
    _require_sha256(program.get("program_sha256"), "winner program")
    expected = runtime["winner_bindings"][source_arm_id]["winner_program_sha256"]
    if program["program_sha256"] != expected or canonical_sha256({key: value for key, value in program.items() if key != "program_sha256"}) != expected:
        raise A3ThreePrimaryConcreteRankerError("winner program does not bind the A2 selection")
    adapter = _adapter_binding(root, target_arm_id=target_arm_id)
    if adapter["target_adapter_sha256"] != runtime["target_adapter_sha256s"][target_arm_id]:
        raise A3ThreePrimaryConcreteRankerError("target adapter does not bind the A3 runtime")
    compiled = compile_program(_corpus_rows(corpus_path, program), program)
    try:
        return rank_dense(
            compiled.units,
            queries,
            arm_id=target_arm_id,
            model_directory=root / "models" / target_arm_id,
            device=os.environ.get("A3_REMOTE_DEVICE", "cuda:0"),
            method=compiled.family_aggregation,
            adapter_factory=adapter_factory,
        )
    except Exception as error:
        raise A3ThreePrimaryConcreteRankerError("target adapter retrieval failed") from error


def _rrf_union(
    ranks_by_arm: Mapping[str, Mapping[str, Sequence[Any]]], *, depth: int) -> dict[str, tuple[dict[str, Any], ...]]:
    tokens = set.intersection(*(set(ranks) for ranks in ranks_by_arm.values())) if ranks_by_arm else set()
    if not tokens or any(set(ranks) != tokens for ranks in ranks_by_arm.values()):
        raise A3ThreePrimaryConcreteRankerError("fixed-union query coverage is incomplete")
    result: dict[str, tuple[dict[str, Any], ...]] = {}
    for token in sorted(tokens):
        fused = fuse_rankings(
            {arm_id: [row.family_token for row in ranks[token]] for arm_id, ranks in ranks_by_arm.items()},
            method="rrf", rrf_k=60, limit=depth,
        )
        if len(fused) != depth:
            raise A3ThreePrimaryConcreteRankerError("fixed union cannot supply the frozen depth")
        result[token] = tuple(fused)
    return result


def _serialise_rankings(rankings: Mapping[str, Sequence[Any]], *, depth: int) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for token, rows in rankings.items():
        if len(rows) < depth:
            raise A3ThreePrimaryConcreteRankerError("ranker cannot supply the requested output depth")
        serialised = []
        for rank, row in enumerate(rows[:depth], start=1):
            family = getattr(row, "family_token", None) if not isinstance(row, Mapping) else row.get("family_id")
            score = getattr(row, "score", None) if not isinstance(row, Mapping) else row.get("score")
            if not isinstance(family, str) or not family or isinstance(score, bool) or not isinstance(score, (int, float, str)):
                raise A3ThreePrimaryConcreteRankerError("ranker emitted an invalid family rank")
            numeric = float(score)
            if not math.isfinite(numeric):
                raise A3ThreePrimaryConcreteRankerError("ranker emitted a non-finite score")
            serialised.append({"family_token": family, "rank": rank, "score": numeric})
        if len({row["family_token"] for row in serialised}) != depth:
            raise A3ThreePrimaryConcreteRankerError("ranker duplicated a family")
        result[str(token)] = serialised
    return result


def _train_assets(root: Path, inventory: Mapping[str, Any]) -> tuple[Path, dict[str, str]]:
    scope = _load_json(root / "train-scope.json", role="Train-250 scope")
    expected_scope = {
        "schema_version": "myis.armindex-a3-train-scope.v1",
        "scope": "Train-250",
        "split_id": "Train-250",
        "query_count": 250,
        "queries_sha256": inventory["remote_asset_sha256s"]["queries_sha256"],
    }
    package = inventory.get("package_bindings")
    if package is not None:
        expected_scope["split_commitment_sha256"] = package["split_commitment_sha256"]
    if scope != expected_scope:
        raise A3ThreePrimaryConcreteRankerError("A3 ranker requires exactly Train-250")
    corpus_path, queries_path = root / "corpus.jsonl", root / "queries.jsonl"
    if file_sha256(corpus_path) != inventory["remote_asset_sha256s"]["corpus_sha256"] or file_sha256(queries_path) != scope["queries_sha256"]:
        raise A3ThreePrimaryConcreteRankerError("Train-250 asset hash drift")
    if package is not None and (
        package["corpus_sha256"] != inventory["remote_asset_sha256s"]["corpus_sha256"]
        or package["query_bundle_sha256"] != inventory["remote_asset_sha256s"]["queries_sha256"]
    ):
        raise A3ThreePrimaryConcreteRankerError("A3 package commitments do not match staged assets")
    queries = _queries(queries_path)
    if len(queries) != 250:
        raise A3ThreePrimaryConcreteRankerError("Train-250 query coverage drift")
    return corpus_path, queries


def _inventory(root: Path, *, expected_assets: Mapping[str, Any]) -> dict[str, Any]:
    value = _load_json(root / "A3_RUNTIME_ASSETS.json", role="runtime asset inventory")
    allowed = _INVENTORY_KEYS | {"package_bindings"}
    if set(value) - allowed or value.get("schema_version") != "myis.armindex-a3-runtime-assets-inventory.v1" or value.get("remote_asset_sha256s") != expected_assets:
        raise A3ThreePrimaryConcreteRankerError("runtime assets are not bound to the remote request")
    _require_sha256(value.get("inventory_sha256"), "runtime inventory")
    if value["inventory_sha256"] != canonical_sha256({key: item for key, item in value.items() if key != "inventory_sha256"}):
        raise A3ThreePrimaryConcreteRankerError("runtime asset inventory hash drift")
    return value


def _runtime_bindings(root: Path, *, expected_sha256: str) -> dict[str, Any]:
    value = _load_json(root / "A3_RUNTIME_BINDINGS.json", role="runtime bindings")
    if set(value) not in (_RUNTIME_KEYS, _RUNTIME_KEYS | {"package_bindings"}) or value.get("primary_arm_scope") != list(PRIMARY_ARMS) or value.get("runtime_bindings_sha256") != expected_sha256:
        raise A3ThreePrimaryConcreteRankerError("runtime binding identity drift")
    if expected_sha256 != canonical_sha256({key: item for key, item in value.items() if key != "runtime_bindings_sha256"}):
        raise A3ThreePrimaryConcreteRankerError("runtime binding hash drift")
    for arm_id in PRIMARY_ARMS:
        _require_sha256(value["winner_bindings"][arm_id]["winner_program_sha256"], "winner program")
        _require_sha256(value["target_adapter_sha256s"][arm_id], "target adapter")
    if "package_bindings" in value:
        _validate_package_bindings(value["package_bindings"])
    return value


def _adapter_binding(root: Path, *, target_arm_id: str) -> dict[str, Any]:
    model = root / "models" / target_arm_id
    binding = _load_json(model / "A3_ADAPTER_BINDING.json", role="target adapter")
    if set(binding) != {"arm_id", "target_adapter_sha256", "model_tree_sha256"} or binding.get("arm_id") != target_arm_id:
        raise A3ThreePrimaryConcreteRankerError("target adapter binding is invalid")
    _require_sha256(binding["target_adapter_sha256"], "target adapter")
    _require_sha256(binding["model_tree_sha256"], "model tree")
    if _tree_sha256(model, exclude={"A3_ADAPTER_BINDING.json"}) != binding["model_tree_sha256"]:
        raise A3ThreePrimaryConcreteRankerError("target model asset hash drift")
    return binding


def _tree_sha256(root: Path, *, exclude: set[str] | None = None) -> str:
    if root.is_symlink() or not root.is_dir():
        raise A3ThreePrimaryConcreteRankerError("model asset directory is invalid")
    excluded = exclude or set()
    entries = []
    # Sort serialized POSIX paths, rather than platform-specific Path ordering.
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if relative in excluded:
            continue
        if path.is_symlink():
            raise A3ThreePrimaryConcreteRankerError("model asset tree contains an unsafe entry")
        if path.is_dir():
            continue
        if not path.is_file():
            raise A3ThreePrimaryConcreteRankerError("model asset tree contains an unsafe entry")
        entries.append({"path": relative, "sha256": file_sha256(path)})
    if not entries:
        raise A3ThreePrimaryConcreteRankerError("model asset tree is empty")
    return canonical_sha256(entries)


def _load_json(path: Path, *, role: str) -> dict[str, Any]:
    try:
        resolved = path.resolve(strict=True)
        if resolved.is_symlink() or not resolved.is_file():
            raise OSError
        value = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as error:
        raise A3ThreePrimaryConcreteRankerError(f"{role} is invalid") from error
    if not isinstance(value, dict):
        raise A3ThreePrimaryConcreteRankerError(f"{role} is invalid")
    return deepcopy(value)


def _p95(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def _require_sha256(value: Any, role: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(char not in _SHA256 for char in value):
        raise A3ThreePrimaryConcreteRankerError(f"{role} SHA-256 is invalid")


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise A3ThreePrimaryConcreteRankerError("ranker result destination already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a3-three-primary-concrete-ranker")
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--assets-root", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args()
    run_a3_three_primary_ranker(args.request, assets_root=args.assets_root, result_path=args.result)
    return 0


__all__ = ["A3ThreePrimaryConcreteRankerError", "run_a3_three_primary_ranker"]


if __name__ == "__main__":
    raise SystemExit(main())
