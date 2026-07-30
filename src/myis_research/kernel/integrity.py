"""Aggregate-only deterministic integrity and leakage preflight."""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from .canonical import canonical_sha256

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def run_integrity_preflight(*, documents: Sequence[Mapping[str, Any]], queries: Sequence[Mapping[str, Any]], targets: Mapping[str, Sequence[str]], splits: Mapping[str, Sequence[str]], near_duplicate_threshold: float = 0.8) -> dict[str, Any]:
    """Return counts and commitments only; detailed offending IDs stay local."""
    if not 0.0 < near_duplicate_threshold <= 1.0:
        raise ValueError("near_duplicate_threshold must be in (0, 1]")
    checks = {
        "document_identity": _check_unique([str(row.get("doc_id", "")) for row in documents]),
        "query_identity": _check_unique([str(row.get("query_id", "")) for row in queries]),
        "cross_split_query_identity": _check_unique([str(item) for values in splits.values() for item in values]),
        "target_identity": _check_targets(targets),
        "exact_text_duplicate": _check_exact_documents(documents),
        "family_overlap": _check_family_overlap(queries, targets),
        "near_duplicate": _check_near_duplicates(documents, near_duplicate_threshold),
    }
    body: dict[str, Any] = {
        "schema_version": "myis.integrity-receipt.v1",
        "status": "pass" if all(item["status"] == "pass" for item in checks.values()) else "blocked",
        "checks": checks,
        "algorithm": {"normalization": "casefold-token-v1", "near_duplicate": "token-jaccard-v1", "threshold": near_duplicate_threshold},
        "input_commitment": canonical_sha256({"documents": list(documents), "queries": list(queries), "targets": dict(targets), "splits": dict(splits)}),
    }
    body["receipt_sha256"] = canonical_sha256(body)
    return body


def require_integrity_pass(receipt: Mapping[str, Any]) -> None:
    if receipt.get("status") != "pass":
        raise ValueError("integrity preflight is blocked")


def _check_unique(values: Sequence[str]) -> dict[str, Any]:
    invalid = sum(not value for value in values)
    duplicates = len(values) - len(set(values))
    return {"status": "pass" if invalid == 0 and duplicates == 0 else "blocked", "count": max(0, duplicates) + invalid}


def _check_targets(targets: Mapping[str, Sequence[str]]) -> dict[str, Any]:
    missing = sum(not values for values in targets.values())
    return {"status": "pass" if missing == 0 else "blocked", "count": missing}


def _normalize(text: str) -> tuple[str, ...]:
    return tuple(_TOKEN_RE.findall(text.casefold()))


def _check_exact_documents(documents: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    values = [_normalize(str(row.get("text", ""))) for row in documents]
    duplicates = len(values) - len(set(values))
    return {"status": "pass" if duplicates == 0 else "blocked", "count": max(0, duplicates)}


def _check_family_overlap(queries: Sequence[Mapping[str, Any]], targets: Mapping[str, Sequence[str]]) -> dict[str, Any]:
    overlaps = sum(1 for query in queries if query.get("family_id") is not None and str(query.get("family_id")) in {str(item) for item in targets.get(str(query.get("query_id")), ())})
    return {"status": "pass" if overlaps == 0 else "blocked", "count": overlaps}


def _check_near_duplicates(documents: Sequence[Mapping[str, Any]], threshold: float) -> dict[str, Any]:
    token_sets = [set(_normalize(str(row.get("text", "")))) for row in documents]
    candidates = 0
    for index, left in enumerate(token_sets):
        for right in token_sets[index + 1 :]:
            union = left | right
            similarity = len(left & right) / len(union) if union else 1.0
            if similarity >= threshold:
                candidates += 1
    return {"status": "pass" if candidates == 0 else "blocked", "count": candidates}
