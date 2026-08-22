"""Materialize opaque Final-872 inputs inside the Owner Store.

This bridge is deliberately Owner-local.  It reads the pinned DAPFAM cache,
the protected split, and the protected relations, then writes only opaque
tokenized corpus/query inputs for remote retrieval plus protected evaluator
inputs that remain in the Owner Store.  It never prints IDs, qrels, or
per-query outcomes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

from myis_research.dapfam_p1 import compose_tac, iter_arrow_rows, resolve_cache
from myis_research.kernel.canonical import canonical_sha256, file_sha256


def _opaque(prefix: str, scope: str, value: str) -> str:
    return f"{prefix}-{hashlib.sha256(f'{scope}:{prefix}:{value}'.encode()).hexdigest()[:32]}"


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = {**value}
    body["sha256"] = canonical_sha256(body)
    path.write_text(json.dumps(body, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n", encoding="ascii")


def _read_split(path: Path) -> tuple[list[str], str]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("final"), list) or len(value["final"]) != 872:
        raise ValueError("protected split does not contain exactly 872 final queries")
    if len(set(value["final"])) != 872 or not isinstance(value.get("split_sha256"), str):
        raise ValueError("protected final split is invalid")
    return [str(item) for item in value["final"]], value["split_sha256"]


def materialize(*, repository_root: Path, cache_root: Path, split_path: Path, output: Path) -> dict[str, Any]:
    layout = resolve_cache(cache_root.resolve(strict=True), repository_root.resolve())
    final_ids, split_hash = _read_split(split_path.resolve(strict=True))
    final_set = set(final_ids)
    scope = canonical_sha256({"phase": "A5_FINAL_CONFIRMATION", "split": split_hash, "dataset": layout.contract["dataset"]["revision"]})
    output.mkdir(parents=True, exist_ok=True)
    inputs = output / "inputs"
    inputs.mkdir(exist_ok=True)
    family_tokens: set[str] = set()
    corpus_count = 0
    with (inputs / "corpus.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for row in iter_arrow_rows(tuple(layout.files["corpus"]), ("relevant_id", "title_en", "abstract_en", "claims_text")):
            source = str(row.get("relevant_id") or "")
            if not source or source in family_tokens:
                raise ValueError("corpus identity is invalid")
            token = _opaque("F", scope, source)
            family_tokens.add(source)
            handle.write(json.dumps({"family_token": token, "publication_token": token, "publication_ordinal": 0, "title_en": row.get("title_en"), "abstract_en": row.get("abstract_en"), "claims_text": row.get("claims_text"), "claims": []}, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n")
            corpus_count += 1
    observed: set[str] = set()
    with (inputs / "queries.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for row in iter_arrow_rows(tuple(layout.files["queries"]), ("query_id", "title_en", "abstract_en", "claims_text")):
            source = str(row.get("query_id") or "")
            if source not in final_set:
                continue
            if source in observed:
                raise ValueError("final query identity is duplicated")
            observed.add(source)
            token = _opaque("Q", scope, source)
            handle.write(json.dumps({"work_token": token, "text": compose_tac(row)}, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n")
    if observed != final_set or corpus_count != int(layout.contract["configs"]["corpus"]["rows"]):
        raise ValueError("Final-872 or corpus coverage is incomplete")

    # Protected evaluator inputs remain Owner-local; only their commitments
    # are included in the aggregate-safe manifest.
    qrels: dict[str, dict[str, int]] = defaultdict(dict)
    for row in iter_arrow_rows(tuple(layout.files["relations"]), ("query_id", "relevant_id", "relevance_score")):
        query = str(row.get("query_id") or "")
        family = str(row.get("relevant_id") or "")
        score = float(row.get("relevance_score") or 0.0)
        if query in final_set and score > 0:
            qrels[_opaque("Q", scope, query)][_opaque("F", scope, family)] = max(1, int(round(score)))
    membership_path = output / "protected" / "membership.jsonl"
    qrels_path = output / "protected" / "qrels.jsonl"
    membership_path.parent.mkdir(exist_ok=True)
    membership_path.write_text("".join(json.dumps({"work_token": _opaque("Q", scope, query), "eligible_out": True}, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n" for query in sorted(final_set)), encoding="ascii")
    qrels_path.write_text("".join(json.dumps({"work_token": query, "relevance": relevance}, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n" for query, relevance in sorted(qrels.items())), encoding="ascii")
    manifest = {
        "schema_version": "myis.armindex-a5-final-opaque-materialization.v1",
        "status": "PASS_A5_OPAQUE_INPUTS_MATERIALIZED",
        "scope": "Final-872",
        "query_count": len(observed),
        "corpus_count": corpus_count,
        "split_sha256": split_hash,
        "dataset_revision": layout.contract["dataset"]["revision"],
        "opaque_scope_sha256": scope,
        "remote_inputs": {"corpus": str((inputs / "corpus.jsonl").relative_to(output)), "queries": str((inputs / "queries.jsonl").relative_to(output))},
        "protected_evaluator_inputs": {"membership": str(membership_path.relative_to(output)), "qrels": str(qrels_path.relative_to(output))},
        "hashes": {name: file_sha256(path) for name, path in (("corpus", inputs / "corpus.jsonl"), ("queries", inputs / "queries.jsonl"), ("membership", membership_path), ("qrels", qrels_path))},
        "protected_payload_included": False,
        "remote_export_allowlist": ["opaque_corpus_text", "opaque_query_text", "aggregate_resource_receipts", "opaque_rankings_to_owner_evaluator_only"],
    }
    _write_json(output / "A5_OPAQUE_MATERIALIZATION_MANIFEST.json", manifest)
    return {"status": manifest["status"], "query_count": len(observed), "corpus_count": corpus_count, "manifest_sha256": file_sha256(output / "A5_OPAQUE_MATERIALIZATION_MANIFEST.json"), "protected_payload_included": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(materialize(repository_root=args.repository_root, cache_root=args.cache_root, split_path=args.split, output=args.output), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
