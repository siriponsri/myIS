"""Aggregate-only deterministic integrity and leakage preflight.

This module runs inside the owner-local boundary.  Its public receipt contains
only counts, commitments, algorithm configuration, and recovery actions; the
owner-local caller may retain detailed offending rows separately.
"""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from .canonical import canonical_sha256


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

# These fixed limits make the approximate candidate stage bounded.  Hitting a
# limit is an integrity failure, rather than silently omitting a candidate.
_LSH_BANDS = 4
_LSH_BITS_PER_BAND = 16
_LSH_MAX_BUCKET_SIZE = 512
_LSH_MAX_CANDIDATE_PAIRS = 250_000
_LSH_MAX_UNIQUE_TOKENS_PER_DOCUMENT = 8_192
# Keep the public identifier stable for existing receipts.  The explicit
# bounds and scan-completeness fields below distinguish this fail-closed form.
_LSH_VERSION = "simhash-lsh-capped-v2"


def run_integrity_preflight(
    *,
    documents: Sequence[Mapping[str, Any]],
    queries: Sequence[Mapping[str, Any]],
    targets: Mapping[str, Sequence[str]],
    splits: Mapping[str, Sequence[str]],
    near_duplicate_threshold: float = 0.8,
    input_commitment: str | None = None,
) -> dict[str, Any]:
    """Build an aggregate-only, deterministic preflight receipt.

    ``queries`` must carry a ``family_id`` (or ``query_family_id``) whenever
    there are queries.  A query family that is also a corpus family is a
    leakage signal.  Callers with an ID mapping must resolve it before calling
    this function; unknown mappings are intentionally blocked rather than
    inferred from query text or qrels.
    """
    if not 0.0 < near_duplicate_threshold <= 1.0:
        raise ValueError("near_duplicate_threshold must be in (0, 1]")
    if input_commitment is not None and not _SHA256_RE.fullmatch(input_commitment):
        raise ValueError("input_commitment must be a lowercase SHA-256 digest")

    document_rows = [dict(row) for row in documents]
    query_rows = [dict(row) for row in queries]
    target_rows = {str(query_id): tuple(str(value) for value in values) for query_id, values in targets.items()}
    split_rows = {str(split): tuple(str(value) for value in values) for split, values in splits.items()}
    commitments = _commitments(document_rows, query_rows, target_rows, split_rows)
    query_index = _index_rows(query_rows, "query_id")
    document_families = {str(row.get("family_id", "")) for row in document_rows if str(row.get("family_id", ""))}

    checks = {
        "required_fields": _check_required_fields(document_rows, query_rows),
        "document_identity": _check_unique(_values(document_rows, "doc_id")),
        "query_identity": _check_unique(_values(query_rows, "query_id")),
        "split_membership": _check_split_membership(query_rows, query_index, split_rows),
        "cross_split_query_identity": _check_cross_split_identity(split_rows),
        "cross_split_family_identity": _check_cross_split_families(query_index, split_rows),
        "target_identity": _check_targets(query_rows, target_rows, document_families),
        "family_mapping": _check_family_mapping(document_rows, query_rows, target_rows, document_families),
        "family_overlap": _check_family_overlap(query_rows, document_families),
        "exact_text_duplicate": _check_exact_documents(document_rows),
        "near_duplicate": _check_near_duplicates(document_rows, near_duplicate_threshold),
    }
    algorithm = {
        "normalization": "casefold-token-v1",
        "near_duplicate": _LSH_VERSION,
        "implementation": "fail-closed-bounded-v3",
        "similarity": "token-jaccard-v1",
        "threshold": near_duplicate_threshold,
        "bands": _LSH_BANDS,
        "bits_per_band": _LSH_BITS_PER_BAND,
        "max_bucket_size": _LSH_MAX_BUCKET_SIZE,
        "max_candidate_pairs": _LSH_MAX_CANDIDATE_PAIRS,
        "max_unique_tokens_per_document": _LSH_MAX_UNIQUE_TOKENS_PER_DOCUMENT,
    }
    body: dict[str, Any] = {
        "schema_version": "myis.integrity-receipt.v2",
        "status": "pass" if all(item["status"] == "pass" for item in checks.values()) else "blocked",
        "checks": checks,
        "algorithm": algorithm,
        "algorithm_sha256": canonical_sha256(algorithm),
        "counts": {
            "documents": len(document_rows),
            "queries": len(query_rows),
            "corpus_families": len(document_families),
            "target_links": sum(len(values) for values in target_rows.values()),
            "split_assignments": sum(len(values) for values in split_rows.values()),
        },
        "commitments": commitments,
        "input_commitment": input_commitment or canonical_sha256(commitments),
    }
    body["receipt_sha256"] = canonical_sha256(body)
    return body


def require_integrity_pass(receipt: Mapping[str, Any]) -> None:
    """Raise before a measured run when an aggregate receipt is blocked."""
    if receipt.get("status") != "pass":
        raise ValueError("integrity preflight is blocked")


def _commitments(
    documents: Sequence[Mapping[str, Any]],
    queries: Sequence[Mapping[str, Any]],
    targets: Mapping[str, Sequence[str]],
    splits: Mapping[str, Sequence[str]],
) -> dict[str, str]:
    return {
        "documents_sha256": canonical_sha256(list(documents)),
        "queries_sha256": canonical_sha256(list(queries)),
        "targets_sha256": canonical_sha256(dict(targets)),
        "splits_sha256": canonical_sha256(dict(splits)),
        "family_mapping_sha256": canonical_sha256({
            "document_families": sorted({str(row.get("family_id", "")) for row in documents}),
            "query_families": sorted(_query_family(row) for row in queries),
        }),
    }


def _values(rows: Sequence[Mapping[str, Any]], field: str) -> list[str]:
    return [str(row.get(field, "")).strip() for row in rows]


def _index_rows(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, Mapping[str, Any]]:
    # Duplicate identifiers are independently blocked; keeping the first row
    # here only avoids amplifying a malformed input into a noisy receipt.
    indexed: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        value = str(row.get(field, "")).strip()
        if value and value not in indexed:
            indexed[value] = row
    return indexed


def _check_required_fields(documents: Sequence[Mapping[str, Any]], queries: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    missing_documents = sum(
        1
        for row in documents
        if any(not str(row.get(field, "")).strip() for field in ("doc_id", "family_id", "text"))
    )
    missing_queries = sum(
        1
        for row in queries
        if any(not str(row.get(field, "")).strip() for field in ("query_id", "text"))
    )
    missing_query_families = sum(not _query_family(row) for row in queries)
    count = missing_documents + missing_queries + missing_query_families
    return _result(
        count == 0,
        count,
        category="required_field_coverage",
        recovery_action="resolve missing identity or text fields before evaluation",
        documents_missing=missing_documents,
        queries_missing=missing_queries,
        query_families_missing=missing_query_families,
    )


def _check_unique(values: Sequence[str]) -> dict[str, Any]:
    invalid = sum(not value for value in values)
    duplicates = len(values) - len(set(values))
    return _result(
        invalid == 0 and duplicates == 0,
        max(0, duplicates) + invalid,
        category="identifier_uniqueness",
        recovery_action="deduplicate and resolve blank identifiers",
        invalid=invalid,
        duplicates=max(0, duplicates),
    )


def _check_split_membership(
    queries: Sequence[Mapping[str, Any]],
    query_index: Mapping[str, Mapping[str, Any]],
    splits: Mapping[str, Sequence[str]],
) -> dict[str, Any]:
    referenced = [query_id for values in splits.values() for query_id in values]
    unknown = sum(query_id not in query_index for query_id in referenced)
    unassigned = sum(query_id not in set(referenced) for query_id in query_index)
    declared_mismatch = 0
    for split, query_ids in splits.items():
        for query_id in query_ids:
            row = query_index.get(query_id)
            declared = str(row.get("split", "")).strip() if row is not None else ""
            if declared and declared != split:
                declared_mismatch += 1
    count = unknown + unassigned + declared_mismatch
    return _result(
        count == 0,
        count,
        category="split_membership",
        recovery_action="reconcile query IDs and declared split assignments",
        unknown_query_ids=unknown,
        unassigned_queries=unassigned,
        declared_split_mismatches=declared_mismatch,
    )


def _check_cross_split_identity(splits: Mapping[str, Sequence[str]]) -> dict[str, Any]:
    assignments: dict[str, set[str]] = defaultdict(set)
    for split, query_ids in splits.items():
        for query_id in query_ids:
            if query_id:
                assignments[query_id].add(split)
    overlaps = sum(1 for values in assignments.values() if len(values) > 1)
    blanks = sum(not query_id for values in splits.values() for query_id in values)
    return _result(
        overlaps == 0 and blanks == 0,
        overlaps + blanks,
        category="cross_split_query_identity",
        recovery_action="assign every query ID to exactly one split",
        cross_split_duplicates=overlaps,
        blank_query_ids=blanks,
    )


def _check_cross_split_families(
    query_index: Mapping[str, Mapping[str, Any]], splits: Mapping[str, Sequence[str]]
) -> dict[str, Any]:
    assignments: dict[str, set[str]] = defaultdict(set)
    for split, query_ids in splits.items():
        for query_id in query_ids:
            row = query_index.get(query_id)
            if row is not None and _query_family(row):
                assignments[_query_family(row)].add(split)
    overlaps = sum(1 for values in assignments.values() if len(values) > 1)
    return _result(
        overlaps == 0,
        overlaps,
        category="cross_split_family_identity",
        recovery_action="keep each query family in one split",
        cross_split_family_duplicates=overlaps,
    )


def _check_targets(
    queries: Sequence[Mapping[str, Any]], targets: Mapping[str, Sequence[str]], document_families: set[str]
) -> dict[str, Any]:
    query_ids = {str(row.get("query_id", "")).strip() for row in queries if str(row.get("query_id", "")).strip()}
    unknown_queries = sum(query_id not in query_ids for query_id in targets)
    missing_query_targets = sum(query_id not in targets or not targets[query_id] for query_id in query_ids)
    duplicate_targets = sum(len(values) - len(set(values)) for values in targets.values())
    blank_targets = sum(not family for values in targets.values() for family in values)
    unmapped_families = sum(family not in document_families for values in targets.values() for family in values if family)
    count = unknown_queries + missing_query_targets + duplicate_targets + blank_targets + unmapped_families
    return _result(
        count == 0,
        count,
        category="target_family_mapping",
        recovery_action="reconcile qrels against query and corpus family mappings",
        unknown_query_ids=unknown_queries,
        missing_query_targets=missing_query_targets,
        duplicate_target_ids=duplicate_targets,
        blank_target_ids=blank_targets,
        unmapped_target_families=unmapped_families,
    )


def _check_family_mapping(
    documents: Sequence[Mapping[str, Any]],
    queries: Sequence[Mapping[str, Any]],
    targets: Mapping[str, Sequence[str]],
    document_families: set[str],
) -> dict[str, Any]:
    missing_document_families = sum(not str(row.get("family_id", "")).strip() for row in documents)
    missing_query_families = sum(not _query_family(row) for row in queries)
    publication_map: dict[str, str] = {}
    publication_conflicts = 0
    for row in documents:
        publication_id = str(row.get("publication_id", "")).strip()
        family_id = str(row.get("family_id", "")).strip()
        if publication_id and family_id:
            existing = publication_map.setdefault(publication_id, family_id)
            if existing != family_id:
                publication_conflicts += 1
    unresolved_targets = sum(
        family not in document_families for values in targets.values() for family in values if family
    )
    count = missing_document_families + missing_query_families + publication_conflicts + unresolved_targets
    return _result(
        count == 0,
        count,
        category="family_mapping",
        recovery_action="supply a complete, one-to-one publication-to-family mapping and query families",
        document_families_missing=missing_document_families,
        query_families_missing=missing_query_families,
        publication_family_conflicts=publication_conflicts,
        unresolved_target_families=unresolved_targets,
    )


def _check_family_overlap(queries: Sequence[Mapping[str, Any]], document_families: set[str]) -> dict[str, Any]:
    overlaps = sum(1 for row in queries if _query_family(row) in document_families)
    return _result(
        overlaps == 0,
        overlaps,
        category="query_corpus_family_overlap",
        recovery_action="remove the overlapping query family from the corpus or revise the protocol mapping",
    )


def _check_exact_documents(documents: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    digests = {
        hashlib.sha256("\0".join(_normalize(str(row.get("text", "")))).encode("utf-8")).digest()
        for row in documents
    }
    duplicates = len(documents) - len(digests)
    return _result(
        duplicates == 0,
        max(0, duplicates),
        category="normalized_exact_text_duplicate",
        recovery_action="deduplicate normalized corpus text before indexing",
    )


def _check_near_duplicates(documents: Sequence[Mapping[str, Any]], threshold: float) -> dict[str, Any]:
    """Check deterministic SimHash LSH candidates with fixed resource bounds.

    LSH is an approximate candidate generator, so exact Jaccard is calculated
    for every generated pair.  A token, bucket, or candidate-pair cap blocks
    the preflight; it never turns an incomplete candidate scan into a pass.
    """
    if not documents:
        return _near_duplicate_result(True, 0, candidate_pairs=0, overflow_buckets=0)

    bands: dict[tuple[int, int], list[int]] = defaultdict(list)
    token_sets: list[frozenset[str]] = []
    oversized_documents = 0
    for index, row in enumerate(documents):
        tokens = frozenset(_normalize(str(row.get("text", ""))))
        token_sets.append(tokens)
        if len(tokens) > _LSH_MAX_UNIQUE_TOKENS_PER_DOCUMENT:
            oversized_documents += 1
            continue
        signature = _simhash(tokens)
        for band in range(_LSH_BANDS):
            mask = (1 << _LSH_BITS_PER_BAND) - 1
            bands[(band, (signature >> (band * _LSH_BITS_PER_BAND)) & mask)].append(index)
    if oversized_documents:
        return _near_duplicate_result(
            False,
            0,
            candidate_pairs=0,
            overflow_buckets=0,
            oversized_documents=oversized_documents,
            resource_limit="max_unique_tokens_per_document",
        )

    overflow_buckets = sum(1 for values in bands.values() if len(values) > _LSH_MAX_BUCKET_SIZE)
    if overflow_buckets:
        return _near_duplicate_result(
            False,
            0,
            candidate_pairs=0,
            overflow_buckets=overflow_buckets,
            resource_limit="max_bucket_size",
        )

    candidate_pairs: set[tuple[int, int]] = set()
    for values in bands.values():
        for left_offset, left in enumerate(values):
            for right in values[left_offset + 1 :]:
                candidate_pairs.add((left, right))
                if len(candidate_pairs) > _LSH_MAX_CANDIDATE_PAIRS:
                    return _near_duplicate_result(
                        False,
                        0,
                        candidate_pairs=len(candidate_pairs),
                        overflow_buckets=0,
                        resource_limit="max_candidate_pairs",
                    )

    near = 0
    for left, right in sorted(candidate_pairs):
        left_tokens, right_tokens = token_sets[left], token_sets[right]
        union = left_tokens | right_tokens
        similarity = len(left_tokens & right_tokens) / len(union) if union else 1.0
        if similarity >= threshold:
            near += 1
    return _near_duplicate_result(True, near, candidate_pairs=len(candidate_pairs), overflow_buckets=0)


def _near_duplicate_result(
    complete: bool,
    count: int,
    *,
    candidate_pairs: int,
    overflow_buckets: int,
    oversized_documents: int = 0,
    resource_limit: str | None = None,
) -> dict[str, Any]:
    return {
        "status": "pass" if complete and count == 0 else "blocked",
        "count": count,
        "candidate_pairs": candidate_pairs,
        "overflow_buckets": overflow_buckets,
        "oversized_documents": oversized_documents,
        "candidate_scan_complete": complete,
        "resource_limit": resource_limit,
        "algorithm": _LSH_VERSION,
        "complexity": "bounded_linear_plus_candidate_cap",
        "category": "near_duplicate" if complete else "near_duplicate_scan_incomplete",
        "recovery_action": "resolve duplicate candidates" if complete else "partition or deduplicate corpus before retrying bounded LSH",
    }


def _query_family(row: Mapping[str, Any]) -> str:
    return str(row.get("family_id", row.get("query_family_id", ""))).strip()


def _normalize(text: str) -> tuple[str, ...]:
    return tuple(_TOKEN_RE.findall(text.casefold()))


def _simhash(tokens: Iterable[str]) -> int:
    weights = [0] * 64
    ordered_tokens = sorted(tokens)
    for token in ordered_tokens:
        value = int.from_bytes(hashlib.sha256(token.encode("utf-8")).digest()[:8], "big")
        for bit in range(64):
            weights[bit] += 1 if value & (1 << bit) else -1
    # Even-sized token sets can tie a bit.  A fixed digest-derived tiebreaker
    # avoids the systematic all-one bias of ``weight >= 0`` and keeps LSH
    # bucket occupancy practical at the 45,336-family protocol scale.
    tie_breaker = int.from_bytes(
        hashlib.sha256("\0".join(ordered_tokens).encode("utf-8")).digest()[:8], "big"
    )
    signature = 0
    for bit, weight in enumerate(weights):
        if weight > 0 or (weight == 0 and tie_breaker & (1 << bit)):
            signature |= 1 << bit
    return signature


def _result(passed: bool, count: int, *, category: str, recovery_action: str, **details: int) -> dict[str, Any]:
    return {
        "status": "pass" if passed else "blocked",
        "count": count,
        "category": category,
        "recovery_action": recovery_action,
        **details,
    }
