"""Evaluate one completed opaque A5 Final-872 package inside Owner Store only."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Any, Mapping

from myis_research.armindex.a1_2_owner_local_evaluator_v16 import _quality
from myis_research.kernel.canonical import canonical_sha256, file_sha256
from myis_research.protection import assert_aggregate_only


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="ascii"))
    if not isinstance(value, dict):
        raise ValueError(f"invalid object: {path}")
    return value


def _validate_ranking_package(request: Mapping[str, Any], package: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate the opaque remote package before opening Owner-local qrels."""

    if package.get("schema_version") != "myis.armindex-a5-final-ranking-package.v1" or package.get("status") != "PASS_A5_REMOTE_OPAQUE_RANKINGS":
        raise ValueError("A5 ranking package is not complete")
    if (
        package.get("attempt_id") != request["attempt_id"]
        or package.get("request_sha256") != request["request_sha256"]
        or package.get("scope") != "Final-872"
        or package.get("query_count") != 872
        or package.get("failures") != 0
        or package.get("determinism") is not True
        or package.get("protected_payload_included") is not False
        or package.get("rankings_returned_to") != "owner_local_evaluator_only"
    ):
        raise ValueError("A5 ranking package binding is invalid")
    rankings = package.get("rankings")
    if not isinstance(rankings, Mapping) or set(rankings) != {"research_champion", "static_common_baseline"}:
        raise ValueError("A5 finalist ranking set is invalid")
    if package.get("coverage") != {"research_champion": 872, "static_common_baseline": 872}:
        raise ValueError("A5 ranking package coverage is invalid")
    if package.get("ranking_sha256") != canonical_sha256(rankings):
        raise ValueError("A5 ranking package commitment drift")
    return rankings


def _qrels(path: Path) -> tuple[dict[str, dict[str, int]], set[str]]:
    qrels: dict[str, dict[str, int]] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        row = json.loads(line)
        if set(row) != {"work_token", "relevance"} or row["work_token"] in qrels:
            raise ValueError("invalid protected qrels contract")
        qrels[row["work_token"]] = {str(k): int(v) for k, v in row["relevance"].items()}
    membership = path.parent / "membership.jsonl"
    eligible = set()
    for line in membership.read_text(encoding="ascii").splitlines():
        row = json.loads(line)
        if set(row) != {"work_token", "eligible_out"}:
            raise ValueError("invalid protected membership contract")
        if row["eligible_out"]:
            eligible.add(row["work_token"])
    if set(qrels) != eligible or len(eligible) != 872:
        raise ValueError("Final-872 protected evaluator coverage is incomplete")
    return qrels, eligible


def _vectors(rows: Mapping[str, list[dict[str, Any]]], qrels: Mapping[str, Mapping[str, int]], eligible: set[str]) -> tuple[list[float], list[float], list[float]]:
    recall, ndcg100, ndcg10 = [], [], []
    for token in sorted(eligible):
        ranking = [str(item["family_token"]) for item in rows[token]]
        value = _quality({token: ranking}, qrels, {token})
        recall.append(float(value["recall_at_100_out"]))
        ndcg100.append(float(value["ndcg_at_100_out"]))
        ndcg10.append(float(value["ndcg_at_10_out"]))
    return recall, ndcg100, ndcg10


def _bootstrap_delta(left: list[float], right: list[float], *, seed: int = 42, draws: int = 10_000) -> tuple[float, float, float]:
    if len(left) != len(right) or not left:
        raise ValueError("paired vectors are incomplete")
    delta = [a - b for a, b in zip(left, right, strict=True)]
    rng = random.Random(seed)
    samples = [sum(delta[rng.randrange(len(delta))] for _ in delta) / len(delta) for _ in range(draws)]
    samples.sort()
    return sum(delta) / len(delta), samples[250], samples[9749]


def evaluate(*, ranking_path: Path, request_path: Path, owner_root: Path, output_path: Path) -> dict[str, Any]:
    request = _load(request_path)
    if request.get("schema_version") != "myis.armindex-a5-final-request.v1" or request.get("scope") != "Final-872" or request.get("query_count") != 872:
        raise ValueError("A5 request binding is invalid")
    if request.get("request_sha256") != canonical_sha256({k: v for k, v in request.items() if k != "request_sha256"}):
        raise ValueError("A5 request hash mismatch")
    package = _load(ranking_path)
    rankings = _validate_ranking_package(request, package)
    qrels, eligible = _qrels(owner_root / "protected" / "qrels.jsonl")
    metrics: dict[str, dict[str, Any]] = {}
    vectors: dict[str, tuple[list[float], list[float], list[float]]] = {}
    for label, value in rankings.items():
        if not isinstance(value, Mapping) or set(value) != eligible:
            raise ValueError("A5 ranking coverage is incomplete")
        normalized: dict[str, list[dict[str, Any]]] = {}
        for token, rows in value.items():
            if not isinstance(rows, list) or len(rows) != 100 or [row.get("rank") for row in rows] != list(range(1, 101)):
                raise ValueError("A5 top-100 ranking topology is invalid")
            families = [row.get("family_token") for row in rows]
            if len(set(families)) != 100 or any(not isinstance(f, str) or not f.startswith("F-") for f in families):
                raise ValueError("A5 ranking family identity is invalid")
            normalized[token] = rows
        vectors[label] = _vectors(normalized, qrels, eligible)
        quality = _quality({token: [row["family_token"] for row in rows] for token, rows in normalized.items()}, qrels, eligible)
        latency = package.get("latency", {}).get(label, {})
        metrics[label] = {"quality": quality, "latency": latency, "resource": package.get("resource", {}), "coverage": 872, "failures": 0, "determinism": True}
    research, baseline = vectors["research_champion"], vectors["static_common_baseline"]
    recall_delta, recall_lo, recall_hi = _bootstrap_delta(research[0], baseline[0])
    ndcg_delta, ndcg_lo, ndcg_hi = _bootstrap_delta(research[1], baseline[1])
    wins = sum(a > b for a, b in zip(research[0], baseline[0], strict=True))
    losses = sum(a < b for a, b in zip(research[0], baseline[0], strict=True))
    body = {
        "schema_version": "myis.armindex-a5-final-owner-evaluation.v1",
        "status": "PASS_A5_FINAL_CONFIRMATION",
        "scope": "Final-872",
        "request_sha256": request["request_sha256"],
        "ranking_package_sha256": file_sha256(ranking_path),
        "query_count": 872,
        "judged_query_count": len(eligible),
        "systems": metrics,
        "paired_effects": {
            "research_minus_static_recall_at_100": {"delta": recall_delta, "ci95": [recall_lo, recall_hi]},
            "research_minus_static_ndcg_at_100": {"delta": ndcg_delta, "ci95": [ndcg_lo, ndcg_hi]},
            "recall_wins_ties_losses": {"wins": wins, "ties": 872 - wins - losses, "losses": losses},
            "bootstrap_resamples": 10_000,
        },
        "winner": "research_champion" if (recall_delta, ndcg_delta) > (0.0, 0.0) else "static_common_baseline" if (recall_delta, ndcg_delta) < (0.0, 0.0) else "TIE",
        "selection_accesses": 1,
        "final_accesses": 1,
        "protected_payload_included": False,
        "claim_boundary": "Final-872 confirmatory aggregate only; no per-query outcomes, rankings, qrels, membership, IDs, or protected payload are projected.",
    }
    assert_aggregate_only(body)
    body["result_sha256"] = canonical_sha256(body)
    if output_path.exists() or output_path.is_symlink():
        raise FileExistsError(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(body, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="ascii")
    return body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ranking", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--owner-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(ranking_path=args.ranking.resolve(strict=True), request_path=args.request.resolve(strict=True), owner_root=args.owner_root.resolve(strict=True), output_path=args.output.resolve())
    print(json.dumps({"status": result["status"], "result_sha256": result["result_sha256"], "winner": result["winner"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
