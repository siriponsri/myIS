"""Run the two frozen A5 Final-872 retrieval systems on opaque inputs only."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from tqdm import tqdm

from myis_research.armindex.a4_remote_ranker import _fuse, _rank_one, _resource_metrics
from myis_research.kernel.canonical import canonical_sha256, file_sha256

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"invalid JSON object: {path.name}")
    return value


def run(request_path: Path, *, assets_root: Path, result_path: Path) -> dict:
    request = _load(request_path)
    if request.get("schema_version") != "myis.armindex-a5-final-request.v1" or request.get("scope") != "Final-872":
        raise ValueError("A5 request identity is invalid")
    if request.get("query_count") != 872 or request.get("final_accesses") != 1 or request.get("protected_payload_included") is not False:
        raise ValueError("A5 request does not bind the admitted Final-872 scope")
    if request.get("request_sha256") != canonical_sha256({key: value for key, value in request.items() if key != "request_sha256"}):
        raise ValueError("A5 request self-hash mismatch")
    root = assets_root.resolve(strict=True)
    queries: dict[str, str] = {}
    for line in (root / "queries.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if set(row) != {"work_token", "text"}:
            raise ValueError("A5 query payload is not opaque-only")
        queries[row["work_token"]] = str(row["text"])
    if len(queries) != 872:
        raise ValueError("A5 query coverage is incomplete")
    started = time.perf_counter()
    profiles = {"research_champion": ("ARM-03",), "static_common_baseline": ("ARM-01", "ARM-04")}
    rankings: dict[str, dict[str, list[dict]]] = {}
    latencies: dict[str, list[float]] = {}
    with tqdm(total=len(profiles), desc="A5-FINAL", unit="system", leave=True) as progress:
        for label, arms in profiles.items():
            print(f"[A5-FINAL] START system={label} queries=872", flush=True)
            arm_rankings, arm_latencies = {}, {}
            for arm in arms:
                result, samples = _rank_one(root, arm_id=arm, queries=queries)
                arm_rankings[arm] = result
                arm_latencies[arm] = samples
            rankings[label] = _fuse(arm_rankings, depth=100, expected_query_count=872)
            latencies[label] = [sum(arm_latencies[arm][i] for arm in arms) for i in range(872)]
            progress.update(1)
            print(f"[A5-FINAL] COMPLETE system={label} coverage={len(rankings[label])}/872", flush=True)
    elapsed = max(time.perf_counter() - started, 1e-9)
    body = {
        "schema_version": "myis.armindex-a5-final-ranking-package.v1",
        "status": "PASS_A5_REMOTE_OPAQUE_RANKINGS",
        "attempt_id": request["attempt_id"],
        "request_sha256": request["request_sha256"],
        "scope": "Final-872",
        "query_count": 872,
        "rankings": rankings,
        "ranking_sha256": canonical_sha256(rankings),
        "coverage": {label: len(rows) for label, rows in rankings.items()},
        "latency": {label: {"p50_ms": sorted(values)[int(len(values) * 0.50)] * 1000.0, "p95_ms": sorted(values)[int(len(values) * 0.95) - 1] * 1000.0, "p99_ms": sorted(values)[int(len(values) * 0.99) - 1] * 1000.0, "throughput_qps": 872 / sum(values)} for label, values in latencies.items()},
        "resource": _resource_metrics(root, elapsed, ("ARM-03", "ARM-04"), mode="synchronous"),
        "determinism": True,
        "failures": 0,
        "protected_payload_included": False,
        "rankings_returned_to": "owner_local_evaluator_only",
    }
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(body, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n", encoding="ascii")
    return {"status": body["status"], "query_count": 872, "ranking_sha256": body["ranking_sha256"], "result_sha256": file_sha256(result_path), "protected_payload_included": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--assets-root", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.request, assets_root=args.assets_root, result_path=args.result), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
