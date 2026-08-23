"""Merge disjoint shard rankings into an Owner-Store A6 frozen pool."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def read_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"invalid row in {path}")
            rows.append(value)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pool-200", type=Path, required=True)
    parser.add_argument("--query-count", type=int, default=1247)
    parser.add_argument("--depth", type=int, default=2000)
    args = parser.parse_args()
    by_query: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in args.input:
        for row in read_rows(path):
            by_query[str(row["opaque_query_token"])].append(row)
    if len(by_query) != args.query_count:
        raise ValueError(f"query coverage mismatch: {len(by_query)} != {args.query_count}")
    merged: list[dict[str, Any]] = []
    pool_200: list[dict[str, Any]] = []
    for query in sorted(by_query):
        candidates = sorted(by_query[query], key=lambda row: (-float(row["score"]), str(row["opaque_family_token"])))
        seen: set[str] = set()
        unique = [row for row in candidates if not (str(row["opaque_family_token"]) in seen or seen.add(str(row["opaque_family_token"])))][: args.depth]
        if len(unique) < args.depth:
            raise ValueError(f"deep ranking is too short for {query}")
        for rank, row in enumerate(unique, start=1):
            merged_row = {
                "opaque_query_token": query,
                "opaque_family_token": str(row["opaque_family_token"]),
                "rank": rank,
                "score": float(row["score"]),
                "pool_depth": args.depth,
                "evidence_pointer": f"armindex/a6/deep-rankings/{row.get('shard', 'unknown')}",
                "passage_count": int(row.get("passage_count", 0)),
                "field_provenance": str(row.get("field_provenance", "NOT_AVAILABLE_IN_A6_METADATA")),
            }
            merged.append(merged_row)
            if rank <= 200:
                pool_200.append({
                    "opaque_query_token": query,
                    "opaque_family_token": merged_row["opaque_family_token"],
                    "rank": rank,
                    "score": merged_row["score"],
                    "pool_depth": 200,
                    "evidence_pointer": merged_row["evidence_pointer"],
                })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.pool_200.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n" for row in merged), encoding="ascii")
    args.pool_200.write_text("".join(json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n" for row in pool_200), encoding="ascii")
    print(json.dumps({"status": "PASS_A6_POOL_MERGE", "query_count": len(by_query), "deep_rows": len(merged), "pool_200_rows": len(pool_200)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
