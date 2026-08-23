from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex.a6_candidate_pool import (
    A6CandidatePoolError,
    EXPECTED_QUERY_COUNT,
    FROZEN_POOL_DEPTH,
    Passage,
    build_aggregate_safe_pool_projection,
    build_frozen_pool_authority,
    evaluate_frozen_pool_owner_local,
    evaluate_frozen_pool_owner_local_curve,
    load_pool_checkpoint,
    rank_families,
    validate_candidate_pool,
    validate_query_rows,
    write_pool_checkpoint,
)


def _queries() -> list[dict[str, object]]:
    return [
        {"opaque_query_token": f"q-{index:016x}", "query_text": f"patent query {index}", "query_index": index}
        for index in range(EXPECTED_QUERY_COUNT)
    ]


def _pool_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for query in _queries():
        query_token = str(query["opaque_query_token"])
        for rank in range(1, FROZEN_POOL_DEPTH + 1):
            rows.append({
                "opaque_query_token": query_token,
                "opaque_family_token": f"f-{rank:016x}",
                "rank": rank,
                "score": float(FROZEN_POOL_DEPTH - rank),
                "pool_depth": FROZEN_POOL_DEPTH,
                "evidence_pointer": f"evidence/{query_token}/{rank}.json",
            })
    return rows


def test_query_commitment_requires_exactly_1247_complete_indices() -> None:
    rows = _queries()
    assert len(validate_query_rows(rows)) == EXPECTED_QUERY_COUNT
    with pytest.raises(A6CandidatePoolError, match="exact complete query count"):
        validate_query_rows(rows[:-1])
    changed = [dict(row) for row in rows]
    changed[-1]["query_index"] = 0
    with pytest.raises(A6CandidatePoolError, match="duplicate"):
        validate_query_rows(changed)


def test_pool_validation_enforces_k_rank_continuity_and_family_deduplication() -> None:
    tokens = [str(row["opaque_query_token"]) for row in _queries()]
    rows = _pool_rows()
    summary = validate_candidate_pool(tokens, rows, [])
    assert summary["candidate_row_count"] == EXPECTED_QUERY_COUNT * FROZEN_POOL_DEPTH
    bad_depth = [dict(row) for row in rows]
    bad_depth[0]["pool_depth"] = 100
    with pytest.raises(A6CandidatePoolError, match="values are invalid"):
        validate_candidate_pool(tokens, bad_depth, [])
    bad_rank = [dict(row) for row in rows]
    bad_rank[1]["rank"] = 1
    with pytest.raises(A6CandidatePoolError, match="rank continuity"):
        validate_candidate_pool(tokens, bad_rank, [])
    duplicate = [dict(row) for row in rows]
    duplicate[1]["opaque_family_token"] = duplicate[0]["opaque_family_token"]
    with pytest.raises(A6CandidatePoolError, match="duplicate family"):
        validate_candidate_pool(tokens, duplicate, [])


def test_deterministic_tie_break_is_opaque_family_lexical() -> None:
    passages = [
        Passage("f-f", (1.0, 0.0), "evidence/f"),
        Passage("f-a", (1.0, 0.0), "evidence/a"),
    ] + [Passage(f"f-{index:04d}", (0.0, 1.0), f"evidence/{index}") for index in range(198)]
    ranked = rank_families((1.0, 0.0), passages)
    assert ranked[0]["opaque_family_token"] == "f-a"
    assert ranked[1]["opaque_family_token"] == "f-f"


def test_protected_fields_are_rejected() -> None:
    rows = _queries()
    rows[0]["qrels"] = {"f-1": 1}
    with pytest.raises(A6CandidatePoolError, match="protected"):
        validate_query_rows(rows)
    rows = _queries()
    rows[0]["domain_rel"] = "OUT"
    with pytest.raises(A6CandidatePoolError, match="protected"):
        validate_query_rows(rows)


def test_checkpoint_resume_requires_identical_hash_bound_inputs(tmp_path: Path) -> None:
    path = tmp_path / "checkpoint.json"
    config = "a" * 64
    query = "b" * 64
    corpus = "c" * 64
    receipt = write_pool_checkpoint(path, config_sha256=config, query_source_sha256=query, corpus_source_sha256=corpus, completed_query_tokens=["q-0000000000000000"])
    assert receipt["checkpoint_sha256"]
    assert load_pool_checkpoint(path, config_sha256=config, query_source_sha256=query, corpus_source_sha256=corpus)["completed_query_tokens"] == ["q-0000000000000000"]
    with pytest.raises(A6CandidatePoolError, match="incompatible"):
        load_pool_checkpoint(path, config_sha256="d" * 64, query_source_sha256=query, corpus_source_sha256=corpus)


def test_frozen_pool_authority_cannot_expand_and_projection_is_aggregate_safe(tmp_path: Path) -> None:
    pool = tmp_path / "pool.jsonl"
    pool.write_text("{}\n", encoding="ascii")
    summary = {
        "query_count": EXPECTED_QUERY_COUNT, "coverage_count": EXPECTED_QUERY_COUNT,
        "evaluable_query_count": EXPECTED_QUERY_COUNT, "unevaluable_query_count": 0,
        "pool_depth": FROZEN_POOL_DEPTH, "candidate_row_count": EXPECTED_QUERY_COUNT * FROZEN_POOL_DEPTH,
        "duplicate_family_count": 0, "rank_continuity": True,
    }
    authority = build_frozen_pool_authority(
        pool_path=pool, pool_summary=summary, manifest_sha256="a" * 64,
        winner_configuration_sha256="b" * 64, query_source_sha256="c" * 64,
        corpus_source_sha256="d" * 64, evaluation_receipt_sha256="e" * 64,
    )
    assert authority["pool_depth"] == FROZEN_POOL_DEPTH
    projection = build_aggregate_safe_pool_projection(authority, summary)
    encoded = json.dumps(projection)
    assert "opaque_query_token" not in encoded and "evidence_pointer" not in encoded
    expanded = dict(summary)
    expanded["pool_depth"] = 201
    with pytest.raises(A6CandidatePoolError, match="cannot become frozen authority"):
        build_frozen_pool_authority(
            pool_path=pool, pool_summary=expanded, manifest_sha256="a" * 64,
            winner_configuration_sha256="b" * 64, query_source_sha256="c" * 64,
            corpus_source_sha256="d" * 64, evaluation_receipt_sha256="e" * 64,
        )


def test_owner_local_evaluation_reports_all_in_out_without_per_query_payloads() -> None:
    rows = [
        {"opaque_query_token": "q-a", "opaque_family_token": "f-1", "rank": 1, "score": 1.0, "pool_depth": 200, "evidence_pointer": "x/1"},
        {"opaque_query_token": "q-a", "opaque_family_token": "f-2", "rank": 2, "score": 0.5, "pool_depth": 200, "evidence_pointer": "x/2"},
        {"opaque_query_token": "q-b", "opaque_family_token": "f-2", "rank": 1, "score": 1.0, "pool_depth": 200, "evidence_pointer": "y/1"},
    ]
    receipt = evaluate_frozen_pool_owner_local(
        rows,
        qrels_by_query={"q-a": {"f-1": 1}, "q-b": {"f-1": 1}},
        domain_by_query={"q-a": "IN", "q-b": "OUT"},
    )
    assert receipt["ALL"]["Recall@100"] == 0.5
    assert receipt["IN"]["Recall@100"] == 1.0
    assert receipt["OUT"]["Recall@100"] == 0.0
    assert "q-a" not in json.dumps(receipt)


def test_owner_local_curve_contains_all_required_recall_cutoffs_and_ndcg_cutoffs() -> None:
    rows = [
        {"opaque_query_token": "q-a", "opaque_family_token": "f-1", "rank": 1, "score": 1.0, "pool_depth": 200, "evidence_pointer": "x/1"},
        {"opaque_query_token": "q-a", "opaque_family_token": "f-2", "rank": 101, "score": 0.5, "pool_depth": 200, "evidence_pointer": "x/2"},
    ]
    receipt = evaluate_frozen_pool_owner_local_curve(
        rows,
        qrels_by_query={"q-a": {"f-1": 1, "f-2": 1}},
        domain_by_query={"q-a": "OUT"},
    )
    assert receipt["cutoffs"] == [10, 20, 50, 100, 200]
    assert receipt["nDCG_cutoffs"] == [10, 100]
    assert set(receipt["metrics"]) == {"cutoff_10", "cutoff_20", "cutoff_50", "cutoff_100", "cutoff_200"}
