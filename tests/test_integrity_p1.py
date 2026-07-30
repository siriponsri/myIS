from __future__ import annotations

import json

import pytest

from myis_research.kernel.integrity import require_integrity_pass, run_integrity_preflight


def _documents() -> list[dict[str, str]]:
    return [
        {"doc_id": "doc-a", "family_id": "target-a", "publication_id": "pub-a", "text": "catalyst control system"},
        {"doc_id": "doc-b", "family_id": "target-b", "publication_id": "pub-b", "text": "thermal valve assembly"},
    ]


def _queries() -> list[dict[str, str]]:
    return [
        {"query_id": "query-a", "family_id": "query-family-a", "text": "catalyst control", "split": "train"},
        {"query_id": "query-b", "family_id": "query-family-b", "text": "thermal valve", "split": "selection"},
    ]


def _clean_receipt() -> dict[str, object]:
    return run_integrity_preflight(
        documents=_documents(),
        queries=_queries(),
        targets={"query-a": ["target-a"], "query-b": ["target-b"]},
        splits={"train": ["query-a"], "selection": ["query-b"]},
    )


def test_clean_receipt_is_aggregate_only_and_binds_component_commitments() -> None:
    receipt = _clean_receipt()
    assert receipt["status"] == "pass"
    assert set(receipt["commitments"]) == {
        "documents_sha256", "queries_sha256", "targets_sha256", "splits_sha256", "family_mapping_sha256",
    }
    assert receipt["counts"] == {
        "documents": 2, "queries": 2, "corpus_families": 2, "target_links": 2, "split_assignments": 2,
    }
    assert receipt["algorithm"]["near_duplicate"] == "simhash-lsh-capped-v2"
    assert receipt["algorithm"]["implementation"] == "fail-closed-bounded-v3"
    assert "query-a" not in json.dumps(receipt)
    assert "catalyst control" not in json.dumps(receipt)
    assert receipt == _clean_receipt()
    require_integrity_pass(receipt)


def test_exact_duplicate_is_blocked_without_disclosing_rows() -> None:
    documents = _documents()
    documents.append({"doc_id": "doc-c", "family_id": "target-c", "publication_id": "pub-c", "text": "catalyst control system"})
    receipt = run_integrity_preflight(
        documents=documents,
        queries=_queries(),
        targets={"query-a": ["target-a"], "query-b": ["target-b"]},
        splits={"train": ["query-a"], "selection": ["query-b"]},
    )
    assert receipt["status"] == "blocked"
    assert receipt["checks"]["exact_text_duplicate"]["count"] == 1
    with pytest.raises(ValueError, match="blocked"):
        require_integrity_pass(receipt)


def test_query_corpus_family_overlap_and_cross_split_family_overlap_block() -> None:
    queries = _queries()
    queries[0]["family_id"] = "target-a"
    queries[1]["family_id"] = "target-a"
    receipt = run_integrity_preflight(
        documents=_documents(),
        queries=queries,
        targets={"query-a": ["target-a"], "query-b": ["target-b"]},
        splits={"train": ["query-a"], "selection": ["query-b"]},
    )
    assert receipt["checks"]["family_overlap"]["status"] == "blocked"
    assert receipt["checks"]["cross_split_family_identity"]["status"] == "blocked"


def test_cross_split_query_and_unmapped_target_are_fail_closed() -> None:
    receipt = run_integrity_preflight(
        documents=_documents(),
        queries=_queries(),
        targets={"query-a": ["target-a"], "query-b": ["not-in-corpus"]},
        splits={"train": ["query-a"], "selection": ["query-a", "query-b"]},
    )
    assert receipt["checks"]["cross_split_query_identity"]["status"] == "blocked"
    assert receipt["checks"]["target_identity"]["unmapped_target_families"] == 1
    assert receipt["checks"]["family_mapping"]["unresolved_target_families"] == 1


def test_missing_query_family_is_blocked_rather_than_inferred() -> None:
    queries = _queries()
    del queries[0]["family_id"]
    receipt = run_integrity_preflight(
        documents=_documents(),
        queries=queries,
        targets={"query-a": ["target-a"], "query-b": ["target-b"]},
        splits={"train": ["query-a"], "selection": ["query-b"]},
    )
    assert receipt["checks"]["required_fields"]["query_families_missing"] == 1
    assert receipt["checks"]["family_mapping"]["status"] == "blocked"


def test_near_duplicate_candidate_is_checked_with_exact_jaccard() -> None:
    common = " ".join(f"token{i}" for i in range(96))
    documents = [
        {"doc_id": "doc-a", "family_id": "target-a", "text": common},
        {"doc_id": "doc-b", "family_id": "target-b", "text": f"{common} additional"},
    ]
    receipt = run_integrity_preflight(documents=documents, queries=[], targets={}, splits={})
    near = receipt["checks"]["near_duplicate"]
    assert near["candidate_scan_complete"] is True
    assert near["candidate_pairs"] >= 1
    assert near["count"] == 1
    assert near["status"] == "blocked"


def test_lsh_bucket_overflow_is_blocked_instead_of_silently_skipped() -> None:
    documents = [
        {"doc_id": f"doc-{index}", "family_id": f"target-{index}", "text": "same normalized payload"}
        for index in range(513)
    ]
    receipt = run_integrity_preflight(documents=documents, queries=[], targets={}, splits={})
    near = receipt["checks"]["near_duplicate"]
    assert near["status"] == "blocked"
    assert near["candidate_scan_complete"] is False
    assert near["resource_limit"] == "max_bucket_size"
    assert near["overflow_buckets"] >= 1


def test_45336_synthetic_families_use_bounded_candidate_scan() -> None:
    documents = [
        {
            "doc_id": f"doc-{index}",
            "family_id": f"family-{index}",
            "text": f"a{index * 2654435761} b{index * 2246822519} c{index * 3266489917} d{index * 668265263}",
        }
        for index in range(45_336)
    ]
    receipt = run_integrity_preflight(documents=documents, queries=[], targets={}, splits={})
    near = receipt["checks"]["near_duplicate"]
    assert receipt["status"] == "pass"
    assert near["candidate_scan_complete"] is True
    assert near["candidate_pairs"] <= receipt["algorithm"]["max_candidate_pairs"]
    assert near["complexity"] == "bounded_linear_plus_candidate_cap"
