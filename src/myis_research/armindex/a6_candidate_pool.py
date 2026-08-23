"""Owner-local construction and evaluation of the frozen A6 candidate pool.

This module is deliberately separate from :mod:`a6_full_materialization`.
The remote materializer produces the frozen ARM-03 passage index; this module
uses only opaque Owner-Store inputs to create the Top-200 family pool and to
evaluate that already-frozen pool locally.  It never opens Selection or Final,
and it never produces an aggregate-safe projection containing rankings.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only


EXPECTED_QUERY_COUNT = 1_247
FROZEN_POOL_DEPTH = 200
_SHA256_LENGTH = 64
_QUERY_PREFIX = "q-"
_FAMILY_PREFIX = "f-"
_FORBIDDEN_INPUT_KEYS = frozenset({
    "query_id", "family_id", "publication_id", "qrels", "qrel",
    "membership", "split", "per_query_outcome", "per_query_outcomes",
    "ranking", "rankings", "domain_rel", "in_out", "in_out_label",
})
_UNEVALUABLE_REASONS = frozenset({"EMPTY_QUERY_TEXT", "ENCODING_FAILURE", "NO_CANDIDATES"})


class A6CandidatePoolError(ValueError):
    """Raised when a candidate pool would violate the frozen A6 unit."""


@dataclass(frozen=True)
class Passage:
    opaque_family_token: str
    vector: tuple[float, ...]
    evidence_pointer: str


def _require_sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != _SHA256_LENGTH:
        raise A6CandidatePoolError(f"{field} must be SHA-256")
    try:
        int(value, 16)
    except ValueError as error:
        raise A6CandidatePoolError(f"{field} must be SHA-256") from error
    return value


def _require_token(value: Any, *, prefix: str, field: str) -> str:
    if not isinstance(value, str) or not value.startswith(prefix) or len(value) <= len(prefix):
        raise A6CandidatePoolError(f"{field} must be an opaque {prefix} token")
    suffix = value[len(prefix):]
    if any(character not in "0123456789abcdef" for character in suffix):
        raise A6CandidatePoolError(f"{field} must use a lowercase hexadecimal opaque token")
    if any(char.isspace() for char in value):
        raise A6CandidatePoolError(f"{field} must not contain whitespace")
    return value


def _require_owner_pointer(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or value.startswith(("/", "\\")) or "\\" in value:
        raise A6CandidatePoolError(f"{field} must be Owner-Store relative")
    if any(part in {"", ".", ".."} for part in value.split("/")):
        raise A6CandidatePoolError(f"{field} has an unsafe path")
    return value


def _assert_no_protected_keys(value: Mapping[str, Any], *, role: str) -> None:
    normalized = {str(key).casefold().replace("-", "_") for key in value}
    forbidden = normalized & _FORBIDDEN_INPUT_KEYS
    if forbidden:
        raise A6CandidatePoolError(f"{role} contains protected field(s): {sorted(forbidden)}")


def _unit_vector(values: Sequence[Any], *, role: str) -> tuple[float, ...]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)) or not values:
        raise A6CandidatePoolError(f"{role} vector is empty")
    try:
        vector = tuple(float(value) for value in values)
    except (TypeError, ValueError) as error:
        raise A6CandidatePoolError(f"{role} vector is non-numeric") from error
    if not all(math.isfinite(value) for value in vector):
        raise A6CandidatePoolError(f"{role} vector is non-finite")
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        raise A6CandidatePoolError(f"{role} vector has zero norm")
    return tuple(value / norm for value in vector)


def validate_query_rows(rows: Iterable[Mapping[str, Any]], *, expected_count: int = EXPECTED_QUERY_COUNT) -> list[dict[str, Any]]:
    """Validate the full opaque query commitment without exposing raw IDs."""

    if expected_count <= 0:
        raise A6CandidatePoolError("query count commitment is invalid")
    normalized: list[dict[str, Any]] = []
    seen_tokens: set[str] = set()
    seen_indices: set[int] = set()
    for raw in rows:
        if not isinstance(raw, Mapping):
            raise A6CandidatePoolError("query row must be an object")
        _assert_no_protected_keys(raw, role="query row")
        if set(raw) != {"opaque_query_token", "query_text", "query_index"}:
            raise A6CandidatePoolError("query row schema is invalid")
        token = _require_token(raw["opaque_query_token"], prefix=_QUERY_PREFIX, field="opaque_query_token")
        text = raw["query_text"]
        index = raw["query_index"]
        if not isinstance(text, str) or not text.strip() or not isinstance(index, int) or index < 0 or index >= expected_count:
            raise A6CandidatePoolError("query row contents are invalid")
        if token in seen_tokens or index in seen_indices:
            raise A6CandidatePoolError("query commitment has duplicate opaque token or index")
        seen_tokens.add(token)
        seen_indices.add(index)
        normalized.append({"opaque_query_token": token, "query_text": text, "query_index": index})
    if len(normalized) != expected_count or seen_indices != set(range(expected_count)):
        raise A6CandidatePoolError("query commitment must contain the exact complete query count")
    return sorted(normalized, key=lambda row: row["query_index"])


def validate_passages(rows: Iterable[Mapping[str, Any]]) -> list[Passage]:
    """Validate opaque passage embeddings prepared from the frozen A6 index."""

    result: list[Passage] = []
    dimensions: int | None = None
    for raw in rows:
        if not isinstance(raw, Mapping):
            raise A6CandidatePoolError("passage row must be an object")
        _assert_no_protected_keys(raw, role="passage row")
        if set(raw) != {"opaque_family_token", "vector", "evidence_pointer"}:
            raise A6CandidatePoolError("passage row schema is invalid")
        vector = _unit_vector(raw["vector"], role="passage")
        if dimensions is None:
            dimensions = len(vector)
        if len(vector) != dimensions:
            raise A6CandidatePoolError("passage vectors have inconsistent dimension")
        result.append(Passage(
            opaque_family_token=_require_token(raw["opaque_family_token"], prefix=_FAMILY_PREFIX, field="opaque_family_token"),
            vector=vector,
            evidence_pointer=_require_owner_pointer(raw["evidence_pointer"], "evidence_pointer"),
        ))
    if not result:
        raise A6CandidatePoolError("candidate corpus has no passages")
    return result


def rank_families(
    query_vector: Sequence[Any], passages: Iterable[Passage], *, pool_depth: int = FROZEN_POOL_DEPTH,
) -> list[dict[str, Any]]:
    """Use normalized dot product and MaxP, with a lexical opaque-token tie break."""

    if pool_depth != FROZEN_POOL_DEPTH:
        raise A6CandidatePoolError("A6 candidate depth must remain exactly 200")
    query = _unit_vector(query_vector, role="query")
    best: dict[str, tuple[float, str]] = {}
    for passage in passages:
        if len(query) != len(passage.vector):
            raise A6CandidatePoolError("query and passage vector dimensions differ")
        score = sum(left * right for left, right in zip(query, passage.vector, strict=True))
        current = best.get(passage.opaque_family_token)
        candidate = (score, passage.evidence_pointer)
        if current is None or score > current[0] or (score == current[0] and passage.evidence_pointer < current[1]):
            best[passage.opaque_family_token] = candidate
    if len(best) < pool_depth:
        raise A6CandidatePoolError("frozen corpus has fewer than 200 candidate families")
    ordered = sorted(best.items(), key=lambda item: (-item[1][0], item[0]))[:pool_depth]
    return [
        {
            "opaque_family_token": family,
            "rank": rank,
            "score": score,
            "pool_depth": pool_depth,
            "evidence_pointer": pointer,
        }
        for rank, (family, (score, pointer)) in enumerate(ordered, start=1)
    ]


def build_candidate_pool(
    query_vectors: Mapping[str, Sequence[Any] | None], passages: Iterable[Passage], *, pool_depth: int = FROZEN_POOL_DEPTH,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Build a complete pool, retaining an explicit Owner-local reason for unevaluable queries."""

    corpus = list(passages)
    rows: list[dict[str, Any]] = []
    unevaluable: list[dict[str, str]] = []
    for token in sorted(query_vectors):
        _require_token(token, prefix=_QUERY_PREFIX, field="opaque_query_token")
        vector = query_vectors[token]
        if vector is None:
            unevaluable.append({"opaque_query_token": token, "reason": "ENCODING_FAILURE"})
            continue
        for candidate in rank_families(vector, corpus, pool_depth=pool_depth):
            rows.append({"opaque_query_token": token, **candidate})
    return rows, unevaluable


def validate_candidate_pool(
    query_tokens: Iterable[str], rows: Iterable[Mapping[str, Any]], unevaluable: Iterable[Mapping[str, Any]],
    *, pool_depth: int = FROZEN_POOL_DEPTH,
) -> dict[str, Any]:
    """Enforce immutable Top-200 shape before a pool can become A6 authority."""

    if pool_depth != FROZEN_POOL_DEPTH:
        raise A6CandidatePoolError("candidate pool depth differs from the frozen value")
    expected = set(query_tokens)
    if len(expected) != EXPECTED_QUERY_COUNT or any(_require_token(value, prefix=_QUERY_PREFIX, field="opaque_query_token") != value for value in expected):
        raise A6CandidatePoolError("candidate pool query coverage is not the committed 1,247-query set")
    by_query: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for raw in rows:
        if not isinstance(raw, Mapping):
            raise A6CandidatePoolError("candidate row must be an object")
        _assert_no_protected_keys(raw, role="candidate row")
        required = {"opaque_query_token", "opaque_family_token", "rank", "score", "pool_depth", "evidence_pointer"}
        if set(raw) != required:
            raise A6CandidatePoolError("candidate row schema is invalid")
        query = _require_token(raw["opaque_query_token"], prefix=_QUERY_PREFIX, field="opaque_query_token")
        family = _require_token(raw["opaque_family_token"], prefix=_FAMILY_PREFIX, field="opaque_family_token")
        rank, depth, score = raw["rank"], raw["pool_depth"], raw["score"]
        if query not in expected or not isinstance(rank, int) or not isinstance(depth, int) or depth != pool_depth or not isinstance(score, (int, float)) or not math.isfinite(float(score)):
            raise A6CandidatePoolError("candidate row values are invalid")
        by_query[query].append({
            "opaque_query_token": query, "opaque_family_token": family, "rank": rank,
            "score": float(score), "pool_depth": depth,
            "evidence_pointer": _require_owner_pointer(raw["evidence_pointer"], "evidence_pointer"),
        })
    unevaluable_by_query: dict[str, str] = {}
    for raw in unevaluable:
        if not isinstance(raw, Mapping) or set(raw) != {"opaque_query_token", "reason"}:
            raise A6CandidatePoolError("unevaluable record schema is invalid")
        _assert_no_protected_keys(raw, role="unevaluable record")
        token = _require_token(raw["opaque_query_token"], prefix=_QUERY_PREFIX, field="opaque_query_token")
        reason = raw["reason"]
        if token not in expected or token in unevaluable_by_query or reason not in _UNEVALUABLE_REASONS:
            raise A6CandidatePoolError("unevaluable record is invalid")
        unevaluable_by_query[token] = reason
    if set(by_query) & set(unevaluable_by_query) or set(by_query) | set(unevaluable_by_query) != expected:
        raise A6CandidatePoolError("every committed query must have exactly one pool state")
    for query, candidates in by_query.items():
        ordered = sorted(candidates, key=lambda row: row["rank"])
        if len(ordered) != pool_depth or [row["rank"] for row in ordered] != list(range(1, pool_depth + 1)):
            raise A6CandidatePoolError(f"rank continuity failed for {query}")
        families = [row["opaque_family_token"] for row in ordered]
        if len(families) != len(set(families)):
            raise A6CandidatePoolError(f"duplicate family found for {query}")
        expected_order = sorted(ordered, key=lambda row: (-row["score"], row["opaque_family_token"]))
        if [row["opaque_family_token"] for row in ordered] != [row["opaque_family_token"] for row in expected_order]:
            raise A6CandidatePoolError(f"deterministic tie ordering failed for {query}")
    return {
        "query_count": EXPECTED_QUERY_COUNT,
        "coverage_count": len(by_query) + len(unevaluable_by_query),
        "evaluable_query_count": len(by_query),
        "unevaluable_query_count": len(unevaluable_by_query),
        "pool_depth": pool_depth,
        "candidate_row_count": sum(len(value) for value in by_query.values()),
        "duplicate_family_count": 0,
        "rank_continuity": True,
    }


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="") as handle:
            json.dump(value, handle, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_pool_checkpoint(
    path: Path, *, config_sha256: str, query_source_sha256: str, corpus_source_sha256: str,
    completed_query_tokens: Iterable[str],
) -> dict[str, Any]:
    """Persist only compatibility bindings and opaque completed work units."""

    observed = list(completed_query_tokens)
    tokens = sorted(set(observed))
    if len(tokens) != len(observed):
        raise A6CandidatePoolError("checkpoint has duplicate completed query tokens")
    for token in tokens:
        _require_token(token, prefix=_QUERY_PREFIX, field="opaque_query_token")
    body = {
        "schema_version": "myis.armindex-a6-pool-checkpoint.v1",
        "config_sha256": _require_sha256(config_sha256, "config_sha256"),
        "query_source_sha256": _require_sha256(query_source_sha256, "query_source_sha256"),
        "corpus_source_sha256": _require_sha256(corpus_source_sha256, "corpus_source_sha256"),
        "completed_query_tokens": tokens,
    }
    result = {**body, "checkpoint_sha256": canonical_sha256(body)}
    _atomic_json(path, result)
    return result


def load_pool_checkpoint(
    path: Path, *, config_sha256: str, query_source_sha256: str, corpus_source_sha256: str,
) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A6CandidatePoolError("candidate-pool checkpoint is invalid") from error
    if not isinstance(value, dict) or set(value) != {
        "schema_version", "config_sha256", "query_source_sha256", "corpus_source_sha256",
        "completed_query_tokens", "checkpoint_sha256",
    }:
        raise A6CandidatePoolError("candidate-pool checkpoint schema is invalid")
    body = {key: item for key, item in value.items() if key != "checkpoint_sha256"}
    if value["schema_version"] != "myis.armindex-a6-pool-checkpoint.v1" or value["checkpoint_sha256"] != canonical_sha256(body):
        raise A6CandidatePoolError("candidate-pool checkpoint hash drifted")
    if any(value[field] != expected for field, expected in {
        "config_sha256": config_sha256, "query_source_sha256": query_source_sha256, "corpus_source_sha256": corpus_source_sha256,
    }.items()):
        raise A6CandidatePoolError("candidate-pool checkpoint is incompatible with this frozen attempt")
    tokens = value["completed_query_tokens"]
    if not isinstance(tokens, list) or len(tokens) != len(set(tokens)):
        raise A6CandidatePoolError("candidate-pool checkpoint units are invalid")
    for token in tokens:
        _require_token(token, prefix=_QUERY_PREFIX, field="opaque_query_token")
    return value


def build_frozen_pool_authority(
    *, pool_path: Path, pool_summary: Mapping[str, Any], manifest_sha256: str, winner_configuration_sha256: str,
    query_source_sha256: str, corpus_source_sha256: str, evaluation_receipt_sha256: str,
) -> dict[str, Any]:
    """Create the hash-bound Owner-Store authority consumed by A7."""

    required_summary = {
        "query_count", "coverage_count", "evaluable_query_count", "unevaluable_query_count", "pool_depth",
        "candidate_row_count", "duplicate_family_count", "rank_continuity",
    }
    if set(pool_summary) != required_summary or pool_summary["query_count"] != EXPECTED_QUERY_COUNT or pool_summary["coverage_count"] != EXPECTED_QUERY_COUNT or pool_summary["pool_depth"] != FROZEN_POOL_DEPTH or pool_summary["duplicate_family_count"] != 0 or pool_summary["rank_continuity"] is not True:
        raise A6CandidatePoolError("candidate-pool summary cannot become frozen authority")
    if not pool_path.is_file() or pool_path.is_symlink():
        raise A6CandidatePoolError("candidate-pool bytes are unavailable")
    body = {
        "schema_version": "myis.armindex-a6-frozen-pool-authority.v1",
        "status": "PASS_A6_FROZEN_POOL_AUTHORITY",
        "pool_sha256": file_sha256(pool_path),
        "manifest_sha256": _require_sha256(manifest_sha256, "manifest_sha256"),
        "query_count": EXPECTED_QUERY_COUNT,
        "pool_depth": FROZEN_POOL_DEPTH,
        "coverage_count": EXPECTED_QUERY_COUNT,
        "evaluation_receipt_sha256": _require_sha256(evaluation_receipt_sha256, "evaluation_receipt_sha256"),
        "winner_configuration_sha256": _require_sha256(winner_configuration_sha256, "winner_configuration_sha256"),
        "query_source_sha256": _require_sha256(query_source_sha256, "query_source_sha256"),
        "corpus_source_sha256": _require_sha256(corpus_source_sha256, "corpus_source_sha256"),
        "pool_owner_store_pointer": _require_owner_pointer(pool_path.name, "pool_owner_store_pointer"),
        "protected_payload_included": True,
        "selection_accesses": 0,
        "final_accesses": 0,
    }
    return {**body, "a6_pool_authority_sha256": canonical_sha256(body)}


def build_aggregate_safe_pool_projection(authority: Mapping[str, Any], pool_summary: Mapping[str, Any]) -> dict[str, Any]:
    """Return the only pool summary eligible for Git/Paper projections."""

    required = {
        "schema_version", "status", "pool_sha256", "manifest_sha256", "query_count", "pool_depth", "coverage_count",
        "evaluation_receipt_sha256", "winner_configuration_sha256", "query_source_sha256", "corpus_source_sha256",
        "pool_owner_store_pointer", "protected_payload_included", "selection_accesses", "final_accesses", "a6_pool_authority_sha256",
    }
    if set(authority) != required or authority.get("protected_payload_included") is not True:
        raise A6CandidatePoolError("invalid Owner-Store pool authority")
    body = {
        "schema_version": "myis.armindex-a6-frozen-pool-projection.v1",
        "a6_pool_authority_sha256": authority["a6_pool_authority_sha256"],
        "pool_sha256": authority["pool_sha256"],
        "manifest_sha256": authority["manifest_sha256"],
        "query_count": pool_summary["query_count"],
        "coverage_count": pool_summary["coverage_count"],
        "evaluable_query_count": pool_summary["evaluable_query_count"],
        "unevaluable_query_count": pool_summary["unevaluable_query_count"],
        "pool_depth": pool_summary["pool_depth"],
        "candidate_row_count": pool_summary["candidate_row_count"],
        "duplicate_family_count": pool_summary["duplicate_family_count"],
        "rank_continuity": pool_summary["rank_continuity"],
        "selection_accesses": 0,
        "final_accesses": 0,
        "protected_payload_included": False,
    }
    try:
        assert_aggregate_only(body)
    except ValueError as error:
        raise A6CandidatePoolError("aggregate-safe pool projection leaks protected data") from error
    return {**body, "projection_sha256": canonical_sha256(body)}


def evaluate_frozen_pool_owner_local(
    rows: Iterable[Mapping[str, Any]], *, qrels_by_query: Mapping[str, Mapping[str, int]],
    domain_by_query: Mapping[str, str], cutoff: int = 100,
) -> dict[str, Any]:
    """Compute ALL/IN/OUT metrics locally without emitting any per-query outcome."""

    if cutoff <= 0 or cutoff > FROZEN_POOL_DEPTH:
        raise A6CandidatePoolError("evaluation cutoff is outside the frozen pool")
    rankings: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for row in rows:
        if not isinstance(row, Mapping):
            raise A6CandidatePoolError("candidate row must be an object")
        token = _require_token(row.get("opaque_query_token"), prefix=_QUERY_PREFIX, field="opaque_query_token")
        family = _require_token(row.get("opaque_family_token"), prefix=_FAMILY_PREFIX, field="opaque_family_token")
        rank = row.get("rank")
        if not isinstance(rank, int) or rank < 1 or rank > FROZEN_POOL_DEPTH:
            raise A6CandidatePoolError("candidate rank is invalid")
        rankings[token].append((rank, family))
    for values in rankings.values():
        values.sort()
    for query, qrels in qrels_by_query.items():
        _require_token(query, prefix=_QUERY_PREFIX, field="opaque_query_token")
        if query not in domain_by_query or domain_by_query[query] not in {"IN", "OUT"}:
            raise A6CandidatePoolError("owner-local evaluation domains are invalid")
        if not isinstance(qrels, Mapping) or not qrels:
            raise A6CandidatePoolError("owner-local qrels are invalid")
        for family, grade in qrels.items():
            _require_token(family, prefix=_FAMILY_PREFIX, field="opaque_family_token")
            if not isinstance(grade, int) or grade <= 0:
                raise A6CandidatePoolError("owner-local qrel grade is invalid")
    if set(qrels_by_query) != set(domain_by_query) or not qrels_by_query:
        raise A6CandidatePoolError("owner-local evaluation population is incomplete")

    def summarize(tokens: list[str]) -> dict[str, Any]:
        if not tokens:
            # An empty split population is not a measured zero. Keep the
            # population explicit while avoiding fabricated aggregate metrics.
            return {
                "judged_query_count": 0,
                f"Recall@{cutoff}": None,
                f"nDCG@{cutoff}": None,
                "nDCG@10": None,
            }
        recalls: list[float] = []
        ndcg100: list[float] = []
        ndcg10: list[float] = []
        for token in tokens:
            qrels = qrels_by_query[token]
            ranked = [family for _, family in rankings.get(token, [])]
            relevant = set(qrels)
            def ndcg(at: int) -> float:
                dcg = sum((2 ** qrels[family] - 1) / math.log2(position + 1) for position, family in enumerate(ranked[:at], start=1) if family in qrels)
                ideal = sorted(qrels.values(), reverse=True)[:at]
                idcg = sum((2 ** grade - 1) / math.log2(position + 1) for position, grade in enumerate(ideal, start=1))
                return dcg / idcg if idcg else 0.0
            recalls.append(len(set(ranked[:cutoff]) & relevant) / len(relevant))
            ndcg100.append(ndcg(cutoff))
            ndcg10.append(ndcg(min(10, cutoff)))
        return {
            "judged_query_count": len(tokens),
            f"Recall@{cutoff}": round(sum(recalls) / len(recalls), 12),
            f"nDCG@{cutoff}": round(sum(ndcg100) / len(ndcg100), 12),
            "nDCG@10": round(sum(ndcg10) / len(ndcg10), 12),
        }

    all_tokens = sorted(qrels_by_query)
    result = {
        "schema_version": "myis.armindex-a6-owner-local-pool-evaluation.v1",
        "cutoff": cutoff,
        "ALL": summarize(all_tokens),
        "IN": summarize([token for token in all_tokens if domain_by_query[token] == "IN"]),
        "OUT": summarize([token for token in all_tokens if domain_by_query[token] == "OUT"]),
        "protected_payload_included": False,
    }
    try:
        assert_aggregate_only(result)
    except ValueError as error:
        raise A6CandidatePoolError("aggregate evaluation leaks protected data") from error
    return {**result, "evaluation_receipt_sha256": canonical_sha256(result)}


def evaluate_frozen_pool_owner_local_curve(
    rows: Iterable[Mapping[str, Any]], *, qrels_by_query: Mapping[str, Mapping[str, int]],
    domain_by_query: Mapping[str, str], cutoffs: Sequence[int] = (10, 20, 50, 100, 200),
) -> dict[str, Any]:
    """Evaluate every preregistered A6 cutoff while retaining aggregates only."""

    normalized_cutoffs = tuple(dict.fromkeys(int(cutoff) for cutoff in cutoffs))
    if normalized_cutoffs != (10, 20, 50, 100, 200):
        raise A6CandidatePoolError("A6 evaluation cutoffs must be exactly 10,20,50,100,200")
    results = {
        f"cutoff_{cutoff}": evaluate_frozen_pool_owner_local(
            rows, qrels_by_query=qrels_by_query, domain_by_query=domain_by_query, cutoff=cutoff,
        )
        for cutoff in normalized_cutoffs
    }
    body = {
        "schema_version": "myis.armindex-a6-owner-local-pool-evaluation-curve.v1",
        "cutoffs": list(normalized_cutoffs),
        "metrics": results,
        "nDCG_cutoffs": [10, 100],
        "populations": ["ALL", "IN", "OUT"],
        "protected_payload_included": False,
    }
    try:
        assert_aggregate_only(body)
    except ValueError as error:
        raise A6CandidatePoolError("aggregate evaluation curve leaks protected data") from error
    return {**body, "evaluation_receipt_sha256": canonical_sha256(body)}


def evaluate_frozen_pool_owner_local_relation_curve(
    rows: Iterable[Mapping[str, Any]], *,
    relations_by_query: Mapping[str, Iterable[Mapping[str, Any]]],
    cutoffs: Sequence[int] = (10, 20, 50, 100, 200),
) -> dict[str, Any]:
    """Evaluate family-level DAPFAM relations with relation-scoped IN/OUT views.

    A query may have relevant families in both domains.  This adapter therefore
    derives each population from ``domain_rel`` on the individual relation,
    rather than assigning one domain label to the query.
    """
    normalized_cutoffs = tuple(dict.fromkeys(int(cutoff) for cutoff in cutoffs))
    if normalized_cutoffs != (10, 20, 50, 100, 200):
        raise A6CandidatePoolError("A6 evaluation cutoffs must be exactly 10,20,50,100,200")
    normalized: dict[str, dict[str, dict[str, int]]] = {}
    for query, raw_relations in relations_by_query.items():
        query_token = _require_token(query, prefix=_QUERY_PREFIX, field="opaque_query_token")
        views = {"ALL": {}, "IN": {}, "OUT": {}}
        for relation in raw_relations:
            if not isinstance(relation, Mapping) or set(relation) != {"opaque_family_token", "relevance_grade", "domain_rel"}:
                raise A6CandidatePoolError("owner-local relation schema is invalid")
            family = _require_token(relation["opaque_family_token"], prefix=_FAMILY_PREFIX, field="opaque_family_token")
            grade = relation["relevance_grade"]
            domain = relation["domain_rel"]
            if not isinstance(grade, int) or grade <= 0 or domain not in {"IN", "OUT"}:
                raise A6CandidatePoolError("owner-local relation values are invalid")
            views["ALL"][family] = max(grade, views["ALL"].get(family, 0))
            views[domain][family] = max(grade, views[domain].get(family, 0))
        if not views["ALL"]:
            raise A6CandidatePoolError("every committed query must have positive relations")
        normalized[query_token] = views

    rankings: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        if not isinstance(row, Mapping):
            raise A6CandidatePoolError("candidate row must be an object")
        query = _require_token(row.get("opaque_query_token"), prefix=_QUERY_PREFIX, field="opaque_query_token")
        family = _require_token(row.get("opaque_family_token"), prefix=_FAMILY_PREFIX, field="opaque_family_token")
        rank = row.get("rank")
        if not isinstance(rank, int) or not 1 <= rank <= FROZEN_POOL_DEPTH:
            raise A6CandidatePoolError("candidate rank is invalid")
        rankings[query].append((rank, family))
    rankings = {query: [family for _, family in sorted(values)] for query, values in rankings.items()}
    if set(rankings) != set(normalized):
        raise A6CandidatePoolError("pool and relation query coverage differ")

    def summarize(view: str, cutoff: int) -> dict[str, Any]:
        recalls: list[float] = []
        ndcg: list[float] = []
        ndcg10: list[float] = []
        for query in sorted(normalized):
            qrels = normalized[query][view]
            if not qrels:
                continue
            ranked = rankings[query]
            relevant = set(qrels)
            top = ranked[:cutoff]
            recalls.append(len(set(top) & relevant) / len(relevant))
            def score(at: int) -> float:
                dcg = sum((2 ** qrels[f] - 1) / math.log2(pos + 1) for pos, f in enumerate(ranked[:at], 1) if f in qrels)
                ideal = sorted(qrels.values(), reverse=True)[:at]
                idcg = sum((2 ** grade - 1) / math.log2(pos + 1) for pos, grade in enumerate(ideal, 1))
                return dcg / idcg if idcg else 0.0
            ndcg.append(score(cutoff))
            ndcg10.append(score(10))
        count = len(recalls)
        return {
            "judged_query_count": count,
            f"Recall@{cutoff}": round(sum(recalls) / count, 12) if count else None,
            f"nDCG@{cutoff}": round(sum(ndcg) / count, 12) if count else None,
            "nDCG@10": round(sum(ndcg10) / count, 12) if count else None,
        }

    metrics = {
        f"cutoff_{cutoff}": {view: summarize(view, cutoff) for view in ("ALL", "IN", "OUT")}
        for cutoff in normalized_cutoffs
    }
    body = {
        "schema_version": "myis.armindex-a6-owner-local-relation-evaluation-curve.v1",
        "cutoffs": list(normalized_cutoffs), "metrics": metrics,
        "nDCG_cutoffs": [10, 100], "populations": ["ALL", "IN", "OUT"],
        "domain_assignment": "family_relation_domain_rel", "query_count": len(normalized),
        "mixed_domain_query_count": sum(bool(v["IN"]) and bool(v["OUT"]) for v in normalized.values()),
        "protected_payload_included": False,
    }
    try:
        assert_aggregate_only(body)
    except ValueError as error:
        raise A6CandidatePoolError("aggregate relation evaluation leaks protected data") from error
    return {**body, "evaluation_receipt_sha256": canonical_sha256(body)}


__all__ = [
    "A6CandidatePoolError", "EXPECTED_QUERY_COUNT", "FROZEN_POOL_DEPTH", "Passage",
    "build_aggregate_safe_pool_projection", "build_candidate_pool", "build_frozen_pool_authority",
    "evaluate_frozen_pool_owner_local", "evaluate_frozen_pool_owner_local_curve", "evaluate_frozen_pool_owner_local_relation_curve", "load_pool_checkpoint", "rank_families", "validate_candidate_pool",
    "validate_passages", "validate_query_rows", "write_pool_checkpoint",
]
