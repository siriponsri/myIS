"""Deterministic synthetic CPU baselines R0 and R0-W."""

from __future__ import annotations

import re
import time
from collections import defaultdict
from typing import Any, Mapping, Sequence

from .canonical import canonical_sha256


TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(TOKEN_RE.findall(text.casefold()))


def _score(query_tokens: Sequence[str], doc_tokens: Sequence[str]) -> float:
    q = set(query_tokens)
    if not q:
        return 0.0
    counts = defaultdict(int)
    for token in doc_tokens:
        counts[token] += 1
    return sum(min(counts[token], 3) for token in q)


def _rank(query: str, docs: Sequence[Mapping[str, Any]], *, window_size: int | None) -> list[str]:
    rows: list[tuple[float, str]] = []
    query_tokens = _tokens(query)
    for doc in docs:
        doc_id = str(doc["doc_id"])
        text = str(doc["text"])
        if window_size is None:
            score = _score(query_tokens, _tokens(text))
        else:
            tokens = _tokens(text)
            windows = [tokens[start : start + window_size] for start in range(0, len(tokens), window_size)] or [()]
            score = max((_score(query_tokens, window) for window in windows), default=0.0)
        rows.append((score, doc_id))
    return [doc_id for _, doc_id in sorted(rows, key=lambda item: (-item[0], item[1]))]


def evaluate_baseline(
    *,
    documents: Sequence[Mapping[str, Any]],
    queries: Sequence[Mapping[str, Any]],
    qrels: Mapping[str, Sequence[str]],
    arm_id: str,
    top_k: int = 100,
    window_size: int = 32,
) -> dict[str, Any]:
    """Evaluate a fixture or owner-local bundle without emitting per-query data."""

    if arm_id not in {"R0", "R0-W"}:
        raise ValueError("evaluate_baseline only accepts R0 or R0-W")
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    if arm_id == "R0-W" and window_size <= 0:
        raise ValueError("window_size must be positive")
    started = time.perf_counter()
    window = None if arm_id == "R0" else window_size
    doc_rows = [dict(item) for item in documents]
    seen_docs: set[str] = set()
    for item in doc_rows:
        if set(item) != {"doc_id", "family_id", "text"}:
            raise ValueError("documents must contain exactly doc_id, family_id, text")
        if item["doc_id"] in seen_docs:
            raise ValueError("document IDs must be unique")
        seen_docs.add(str(item["doc_id"]))
    hits = 0
    total = 0
    for query in queries:
        if set(query) != {"query_id", "text", "split"}:
            raise ValueError("queries must contain exactly query_id, text, split")
        query_id = str(query["query_id"])
        relevant = set(str(value) for value in qrels.get(query_id, ()))
        if not relevant:
            raise ValueError(f"qrels missing relevant family for query {query_id}")
        ranked = _rank(str(query["text"]), doc_rows, window_size=window)
        family_rank: list[str] = []
        family_by_doc = {str(item["doc_id"]): str(item["family_id"]) for item in doc_rows}
        for doc_id in ranked:
            family = family_by_doc[doc_id]
            if family not in family_rank:
                family_rank.append(family)
        hits += int(bool(set(family_rank[:top_k]) & relevant))
        total += 1
    if not total:
        raise ValueError("at least one query is required")
    elapsed = time.perf_counter() - started
    return {
        "schema_version": "myis.metric-bundle.v1",
        "arm_id": arm_id,
        "evidence_class": "fixture",
        "metrics": {"recall_at_100/out": round(hits / total, 12)},
        "counts": {"queries": total, "documents": len(doc_rows)},
        "resources": {"cpu_seconds": round(elapsed, 9), "cost_usd": 0.0},
        "input_commitment": canonical_sha256({"documents": doc_rows, "queries": list(queries), "qrels": dict(qrels)}),
    }
