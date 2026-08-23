"""Construct or locally evaluate an Owner-Store-only frozen A6 Top-200 pool.

The command intentionally has no provider, qrels, or Selection/Final input.
Pool construction reads only opaque query/corpus representations.  Evaluation,
when requested, runs locally against a separately Owner-Store-bound qrels view
and writes aggregate metrics only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from myis_research.armindex.a6_candidate_pool import (
    A6CandidatePoolError,
    build_candidate_pool,
    evaluate_frozen_pool_owner_local_curve,
    validate_candidate_pool,
    validate_passages,
    validate_query_rows,
)
from myis_research.kernel.canonical import canonical_sha256


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file() or path.is_symlink():
        raise A6CandidatePoolError(f"unsafe or missing input: {path.name}")
    values: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise A6CandidatePoolError(f"invalid JSONL at line {number}") from error
        if not isinstance(value, dict):
            raise A6CandidatePoolError(f"JSONL row {number} is not an object")
        values.append(value)
    return values


def _write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    if path.exists() or path.is_symlink():
        raise A6CandidatePoolError("refusing to overwrite frozen candidate-pool bytes")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n" for value in values), encoding="ascii")


def _write_immutable_json(path: Path, value: dict[str, Any]) -> None:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    if path.exists() or path.is_symlink():
        raise A6CandidatePoolError("refusing to overwrite frozen output")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="ascii")


def construct(args: argparse.Namespace) -> dict[str, Any]:
    queries = validate_query_rows(_read_jsonl(args.queries))
    passages = validate_passages(_read_jsonl(args.passages))
    vectors = json.loads(args.query_vectors.read_text(encoding="utf-8"))
    if not isinstance(vectors, dict):
        raise A6CandidatePoolError("query vectors must be an object")
    query_tokens = [row["opaque_query_token"] for row in queries]
    if set(vectors) != set(query_tokens):
        raise A6CandidatePoolError("query-vector commitment does not match the full query source")
    rows, unevaluable = build_candidate_pool(vectors, passages)
    summary = validate_candidate_pool(query_tokens, rows, unevaluable)
    _write_jsonl(args.pool_output, rows)
    _write_jsonl(args.unevaluable_output, unevaluable)
    return {
        "schema_version": "myis.armindex-a6-pool-construction-receipt.v1",
        **summary,
        "query_source_sha256": canonical_sha256(queries),
        "pool_sha256": canonical_sha256(rows),
        "unevaluable_sha256": canonical_sha256(unevaluable),
        "protected_payload_included": True,
    }


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    pool = _read_jsonl(args.pool)
    qrels = json.loads(args.qrels.read_text(encoding="utf-8"))
    domains = json.loads(args.domains.read_text(encoding="utf-8"))
    if not isinstance(qrels, dict) or not isinstance(domains, dict):
        raise A6CandidatePoolError("Owner-local qrels and domains must be objects")
    return evaluate_frozen_pool_owner_local_curve(pool, qrels_by_query=qrels, domain_by_query=domains)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    construct_parser = sub.add_parser("construct")
    construct_parser.add_argument("--queries", type=Path, required=True)
    construct_parser.add_argument("--passages", type=Path, required=True)
    construct_parser.add_argument("--query-vectors", type=Path, required=True)
    construct_parser.add_argument("--pool-output", type=Path, required=True)
    construct_parser.add_argument("--unevaluable-output", type=Path, required=True)
    construct_parser.add_argument("--receipt-output", type=Path, required=True)
    evaluate_parser = sub.add_parser("evaluate")
    evaluate_parser.add_argument("--pool", type=Path, required=True)
    evaluate_parser.add_argument("--qrels", type=Path, required=True)
    evaluate_parser.add_argument("--domains", type=Path, required=True)
    evaluate_parser.add_argument("--receipt-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = construct(args) if args.command == "construct" else evaluate(args)
        _write_immutable_json(args.receipt_output, receipt)
        print(json.dumps({"status": "PASS", "receipt_sha256": receipt.get("evaluation_receipt_sha256", receipt.get("pool_sha256"))}, sort_keys=True))
        return 0
    except A6CandidatePoolError as error:
        print(f"[ARMIndex][A6][BLOCKED] {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
