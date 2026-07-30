"""Deterministic CPU BM25 baselines for the active P1 protocol.

The implementation is deliberately small and dependency-free.  It is a real
Okapi BM25 scorer (not token-overlap) and exposes one evaluator for flat
document ranking (R0) and passage/window ranking with family MaxP (R0-W).
"""

from __future__ import annotations

import hashlib
import math
import re
import time
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from .canonical import canonical_sha256


TOKEN_RE = re.compile(r"(?u)\b\w+\b")


def tokenize(text: str) -> tuple[str, ...]:
    return tuple(TOKEN_RE.findall(str(text).casefold()))


class BM25Index:
    """In-memory Okapi BM25 index used by fixtures and small owner-local tests."""

    def __init__(self, documents: Sequence[Mapping[str, Any]], *, k1: float = 1.2, b: float = 0.75) -> None:
        if k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("BM25 k1 must be positive and b must be in [0, 1]")
        self.documents = [dict(row) for row in documents]
        self.k1 = float(k1)
        self.b = float(b)
        self._tokens: list[tuple[str, ...]] = []
        self._postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
        self._df: dict[str, int] = {}
        total_length = 0
        for index, row in enumerate(self.documents):
            if set(row) != {"doc_id", "family_id", "text"}:
                raise ValueError("documents must contain exactly doc_id, family_id, text")
            tokens = tokenize(str(row["text"]))
            self._tokens.append(tokens)
            total_length += len(tokens)
            frequencies: dict[str, int] = defaultdict(int)
            for token in tokens:
                frequencies[token] += 1
            for token, frequency in frequencies.items():
                self._postings[token].append((index, frequency))
        self._df = {token: len(rows) for token, rows in self._postings.items()}
        self._avgdl = total_length / len(self.documents) if self.documents else 0.0
        ids = [str(row["doc_id"]) for row in self.documents]
        if len(ids) != len(set(ids)):
            raise ValueError("document IDs must be unique")

    def rank(self, query: str, *, limit: int | None = None) -> list[tuple[str, str, float]]:
        query_terms = set(tokenize(query))
        if not query_terms or not self.documents:
            return []
        scores: dict[int, float] = defaultdict(float)
        n_docs = len(self.documents)
        for term in query_terms:
            postings = self._postings.get(term, ())
            if not postings:
                continue
            idf = math.log(1.0 + (n_docs - len(postings) + 0.5) / (len(postings) + 0.5))
            for doc_index, frequency in postings:
                dl = len(self._tokens[doc_index])
                denominator = frequency + self.k1 * (1.0 - self.b + self.b * dl / self._avgdl) if self._avgdl else frequency + self.k1
                scores[doc_index] += idf * (frequency * (self.k1 + 1.0)) / denominator
        rows = [
            (str(self.documents[index]["doc_id"]), str(self.documents[index]["family_id"]), score)
            for index, score in scores.items()
        ]
        rows.sort(key=lambda item: (-item[2], item[0]))
        return rows if limit is None else rows[:limit]


def evaluate_baseline(
    *,
    documents: Sequence[Mapping[str, Any]],
    queries: Sequence[Mapping[str, Any]],
    qrels: Mapping[str, Sequence[str]],
    arm_id: str,
    top_k: int = 100,
    window_size: int = 512,
    query_groups: Mapping[str, Sequence[str]] | None = None,
    qrel_domains: Mapping[str, Mapping[str, str]] | None = None,
    split_name: str = "unknown",
    ranker: Callable[[str], Sequence[tuple[str, str, float]]] | None = None,
    lineage_hint: Mapping[str, str] | None = None,
    protected_sink: Callable[[dict[str, Any]], None] | None = None,
    documents_are_windowed: bool = False,
) -> dict[str, Any]:
    """Evaluate aggregate family-level Recall@100 for one split.

    Recall is the macro mean of per-query relevant-family recall.  `qrel_domains`
    maps each relevant family to its IN/OUT label so every scope uses its own
    relevant-family denominator. `query_groups` remains fixture compatibility
    for callers that do not have family-level domain labels.
    """

    if arm_id not in {"R0", "R0-W"}:
        raise ValueError("evaluate_baseline only accepts R0 or R0-W")
    if top_k <= 0 or (arm_id == "R0-W" and window_size <= 0):
        raise ValueError("top_k and window_size must be positive")
    started = time.perf_counter()
    rows = [dict(item) for item in documents]
    indexed_rows = (
        rows
        if arm_id != "R0-W" or documents_are_windowed
        else _window_rows(rows, window_size)
    )
    if ranker is None:
        index = BM25Index(indexed_rows)
        ranker = lambda text: index.rank(text)
    scopes = ("ALL", "IN", "OUT")
    recall_sums: dict[str, float] = {scope: 0.0 for scope in scopes}
    retrieved_relevant: dict[str, int] = {scope: 0 for scope in scopes}
    relevant_totals: dict[str, int] = {scope: 0 for scope in scopes}
    denominators: dict[str, int] = {scope: 0 for scope in scopes}
    query_commitments: list[str] = []
    ranking_commitments: list[str] = []
    for query in queries:
        if set(query) != {"query_id", "text", "split"}:
            raise ValueError("queries must contain exactly query_id, text, split")
        query_id = str(query["query_id"])
        all_relevant = {str(value) for value in qrels.get(query_id, ())}
        if not all_relevant:
            continue
        query_commitments.append(canonical_sha256({"query": str(query["text"]), "split": split_name}))
        ranked = list(ranker(str(query["text"])))
        family_rank: list[str] = []
        best_score: dict[str, float] = {}
        for _, family_id, score in ranked:
            if family_id not in best_score or score > best_score[family_id]:
                best_score[family_id] = float(score)
        family_rank = [family for family, _ in sorted(best_score.items(), key=lambda item: (-item[1], item[0]))]
        ranked_top_k = family_rank[:top_k]
        ranking_commitments.append(canonical_sha256({"query": canonical_sha256(str(query["text"])), "families": ranked_top_k}))
        scoped_relevance: dict[str, set[str]] = {"ALL": all_relevant}
        if qrel_domains is not None:
            domain_map = {str(family): str(label).upper() for family, label in qrel_domains.get(query_id, {}).items()}
            scoped_relevance["IN"] = {family for family in all_relevant if domain_map.get(family) == "IN"}
            scoped_relevance["OUT"] = {family for family in all_relevant if domain_map.get(family) == "OUT"}
        else:
            groups = {str(value).upper() for value in (query_groups or {}).get(query_id, ())}
            scoped_relevance["IN"] = all_relevant if "IN" in groups else set()
            scoped_relevance["OUT"] = all_relevant if "OUT" in groups else set()
        protected_row: dict[str, Any] = {"query_id": query_id, "ranked_family_ids": ranked_top_k, "recall_at_100": {}}
        for scope in scopes:
            relevant = scoped_relevance[scope]
            if not relevant:
                protected_row["recall_at_100"][scope] = None
                continue
            retrieved = len(set(ranked_top_k) & relevant)
            query_recall = retrieved / len(relevant)
            denominators[scope] += 1
            retrieved_relevant[scope] += retrieved
            relevant_totals[scope] += len(relevant)
            recall_sums[scope] += query_recall
            protected_row["recall_at_100"][scope] = query_recall
        if protected_sink is not None:
            protected_sink(protected_row)
    metrics = [
        {
            "name": "recall_at_100",
            "value": round(recall_sums[scope] / denominators[scope], 12) if denominators[scope] else None,
            "n": denominators[scope],
            "retrieved_relevant": retrieved_relevant[scope],
            "relevant_total": relevant_totals[scope],
            "scope": scope,
            "split": split_name,
            "direction": "maximize",
            "denominator": "macro_mean_per_query_relevant_families",
            "evidence_role": "primary" if scope == "OUT" else "secondary",
        }
        for scope in scopes
    ]
    elapsed = time.perf_counter() - started
    # Owner-local legacy qrels are sets; normalize them before hashing so the
    # metric bundle remains deterministic without exposing query-level rows.
    qrels_commitment = canonical_sha256({
        str(query_id): sorted(str(value) for value in values)
        for query_id, values in qrels.items()
    })
    if lineage_hint:
        corpus_commitment = str(lineage_hint.get("corpus_sha256") or canonical_sha256(rows))
        query_commitment_hash = str(lineage_hint.get("query_sha256") or canonical_sha256(list(queries)))
        qrels_commitment = str(lineage_hint.get("qrels_sha256") or qrels_commitment)
        input_commitment = str(lineage_hint.get("dataset_sha256") or canonical_sha256({"corpus_sha256": corpus_commitment, "query_sha256": query_commitment_hash, "qrels_sha256": qrels_commitment}))
    else:
        corpus_commitment = canonical_sha256(rows)
        query_commitment_hash = canonical_sha256(list(queries))
        input_commitment = canonical_sha256({"documents": rows, "queries": list(queries), "qrels_commitment": qrels_commitment})
    body = {
        "schema_version": "myis.metric-bundle.v1",
        "run_id": f"{arm_id.lower()}-{split_name}",
        "arm_id": arm_id,
        "evidence_class": "fixture" if split_name == "fixture" else "train_selection_measured",
        "split": split_name,
        "metrics": metrics,
        "counts": {"queries_input": len(queries), "documents": len(rows), "indexed_units": len(indexed_rows), "queries_with_positive_relevance": denominators["ALL"]},
        "cost": {"currency": "USD", "value": 0.0},
        "latency_seconds": round(elapsed, 9),
        "lineage": {"dataset_sha256": input_commitment, "corpus_sha256": corpus_commitment, "query_sha256": query_commitment_hash, "qrels_sha256": qrels_commitment, "split_sha256": str(lineage_hint.get("split_sha256")) if lineage_hint and lineage_hint.get("split_sha256") else canonical_sha256(split_name), "index_sha256": str(lineage_hint.get("index_sha256")) if lineage_hint and lineage_hint.get("index_sha256") else canonical_sha256({"scorer": "okapi_bm25_v1", "arm": arm_id}), "evaluator_sha256": str(lineage_hint.get("evaluator_sha256")) if lineage_hint and lineage_hint.get("evaluator_sha256") else canonical_sha256("myis-p1-evaluator-v2")},
        "input_commitment": input_commitment,
        "query_commitment": hashlib.sha256("".join(sorted(query_commitments)).encode("ascii")).hexdigest(),
        "ranking_commitment": hashlib.sha256("".join(sorted(ranking_commitments)).encode("ascii")).hexdigest(),
        "retrieval": {"scorer": "okapi_bm25_v1", "query_operator": "OR", "family_aggregation": "maxP" if arm_id == "R0-W" else "family_first", "window_size": window_size if arm_id == "R0-W" else None, "documents_are_windowed": documents_are_windowed if arm_id == "R0-W" else False, "top_k": top_k},
    }
    body["metrics_hash"] = canonical_sha256(body["metrics"])
    return body


def _window_rows(rows: Sequence[Mapping[str, Any]], window_size: int) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        tokens = tokenize(str(row["text"]))
        windows = [tokens[start : start + window_size] for start in range(0, len(tokens), window_size)] or [()]
        for index, window in enumerate(windows):
            output.append({
                "doc_id": f"{row['doc_id']}#w{index:06d}",
                "family_id": str(row["family_id"]),
                "text": " ".join(window),
            })
    return output
