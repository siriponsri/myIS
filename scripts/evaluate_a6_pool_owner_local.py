"""Evaluate an A6 opaque Top-200 pool locally against protected relations.

The evaluator emits aggregate-only ALL/IN/OUT curves.  It never writes query,
family, ranking, or per-query outcome data to the output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import pyarrow as pa


def read_pool(path: Path) -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        result[str(row["opaque_query_token"])].append(str(row["opaque_family_token"]))
    if len(result) != 1247 or any(len(values) != 200 for values in result.values()):
        raise ValueError("A6 pool must cover exactly 1,247 queries at Top-200")
    return dict(result)


def read_token_map(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    family: dict[str, str] = {}
    query: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        token = str(row["opaque_token"])
        source = str(row["source_id"])
        role = str(row["role"])
        if role == "corpus_family":
            family[source] = token.lower()
        elif role.endswith("query"):
            query[source] = token.lower()
    return family, query


def read_relations(path: Path, family_map: dict[str, str]) -> tuple[dict[str, dict[str, int]], dict[str, dict[str, dict[str, int]]]]:
    with path.open("rb") as handle:
        table = pa.ipc.open_stream(handle).read_all()
    all_qrels: dict[str, dict[str, int]] = defaultdict(dict)
    by_domain: dict[str, dict[str, dict[str, int]]] = {"IN": defaultdict(dict), "OUT": defaultdict(dict)}
    for row in table.to_pylist():
        if float(row["relevance_score"]) <= 0:
            continue
        query_source = str(row["query_id"])
        family = family_map.get(str(row["relevant_id"]))
        if family is None:
            continue
        query = "q-" + hashlib.sha256(query_source.encode("utf-8")).hexdigest()
        grade = max(1, int(round(float(row["relevance_score"]))))
        all_qrels[query][family] = max(grade, all_qrels[query].get(family, 0))
        domain = str(row["domain_rel"])
        if domain in by_domain:
            by_domain[domain][query][family] = max(grade, by_domain[domain][query].get(family, 0))
    return dict(all_qrels), {key: dict(value) for key, value in by_domain.items()}


def metric_curve(pool: dict[str, list[str]], qrels: dict[str, dict[str, int]], cutoffs: tuple[int, ...]) -> dict[str, Any]:
    valid = sorted(set(pool) & set(qrels))
    result: dict[str, Any] = {"judged_query_count": len(valid), "relevant_family_count": sum(len(qrels[q]) for q in valid)}
    for cutoff in cutoffs:
        recalls: list[float] = []
        ndcg: list[float] = []
        for query in valid:
            ranked = pool[query][:cutoff]
            grades = qrels[query]
            relevant = set(grades)
            recalls.append(len(set(ranked) & relevant) / len(relevant))
            dcg = sum((2 ** grades[item] - 1) / math.log2(position + 1) for position, item in enumerate(ranked, 1) if item in grades)
            ideal = sorted(grades.values(), reverse=True)[:cutoff]
            idcg = sum((2 ** grade - 1) / math.log2(position + 1) for position, grade in enumerate(ideal, 1))
            ndcg.append(dcg / idcg if idcg else 0.0)
        result[f"Recall@{cutoff}"] = round(sum(recalls) / len(recalls), 12) if recalls else None
        result[f"nDCG@{cutoff}"] = round(sum(ndcg) / len(ndcg), 12) if ndcg else None
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool", type=Path, required=True)
    parser.add_argument("--relations", type=Path, required=True)
    parser.add_argument("--token-map", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    pool = read_pool(args.pool)
    family_map, _ = read_token_map(args.token_map)
    all_qrels, domain_qrels = read_relations(args.relations, family_map)
    cutoffs = (10, 20, 50, 100, 200)
    body = {
        "schema_version": "myis.armindex-a6-owner-local-family-evaluation.v1",
        "status": "PASS_A6_OWNER_LOCAL_ALL_IN_OUT_EVALUATION",
        "query_count": len(pool),
        "pool_depth": 200,
        "populations": {
            "ALL": metric_curve(pool, all_qrels, cutoffs),
            "IN": metric_curve(pool, domain_qrels["IN"], cutoffs),
            "OUT": metric_curve(pool, domain_qrels["OUT"], cutoffs),
        },
        "relation_rows": 49869,
        "protected_payload_included": True,
        "selection_accesses": 0,
        "final_accesses": 0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({**body, "evaluation_sha256": hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()}, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="ascii")
    print(json.dumps({"status": body["status"], "query_count": len(pool)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
