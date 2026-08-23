from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pyarrow as pa
import pytest

from myis_research.armindex.a7_diagnosis import A7DiagnosisError, diagnose, write_public_outputs


def _write_inputs(root: Path) -> tuple[Path, Path, Path, Path]:
    query_token = "q-" + hashlib.sha256(b"query-1").hexdigest()
    pool = root / "pool.jsonl"
    pool.write_text("\n".join(json.dumps({"opaque_query_token": query_token, "opaque_family_token": "f-" + ("b" * 64 if rank == 1 else f"{rank:064x}"), "rank": rank, "pool_depth": 200, "score": 1.0}) for rank in range(1, 201)) + "\n", encoding="ascii")
    token_map = root / "token-map.jsonl"
    token_map.write_text(json.dumps({"role": "corpus_family", "source_id": "family-1", "opaque_token": "f-" + "b" * 64}) + "\n", encoding="ascii")
    relations = root / "relations.arrow"
    table = pa.table({"query_id": ["query-1"], "relevant_id": ["family-1"], "relevance_score": [1.0], "domain_rel": ["IN"]})
    with relations.open("wb") as handle:
        with pa.ipc.new_stream(handle, table.schema) as writer:
            writer.write_table(table)
    evaluation = root / "evaluation.json"
    evaluation.write_text(json.dumps({"populations": {"ALL": {"Recall@100": 1.0, "nDCG@100": 1.0, "judged_query_count": 1}, "IN": {"Recall@100": 1.0, "nDCG@100": 1.0, "judged_query_count": 1}, "OUT": {"Recall@100": None, "nDCG@100": None, "judged_query_count": 0}}}), encoding="ascii")
    return pool, relations, token_map, evaluation


def test_a7_receipt_is_aggregate_only_and_records_unavailable_layers(tmp_path: Path) -> None:
    pool, relations, token_map, evaluation = _write_inputs(tmp_path)
    receipt, rows = diagnose(pool_path=pool, relations_path=relations, token_map_path=token_map, evaluation_path=evaluation)
    encoded = json.dumps(receipt)
    assert receipt["A7-L1_score_identity"]["status"] == "PASS"
    assert receipt["A7-L2_family_relevance_integrity"]["relations"]["family_collision_count"] == 0
    assert receipt["A7-L2_family_relevance_integrity"]["relations"]["denominator_discrepancy_count"] == 0
    assert receipt["A7-L2_family_relevance_integrity"]["relations"]["leakage_count"] == 0
    assert receipt["A7-L2_family_relevance_integrity"]["self_match_sensitivity"]["removed_raw_self_relation_count"] == 0
    parity = receipt["A7-L3_protocol_parity"]
    assert parity["status"] == "NOT_VERIFIED"
    assert len(parity["matrix"]) == 11
    assert {row["ArmIndex_vs_PatenTEB"] for row in parity["matrix"]} == {"UNKNOWN"}
    assert receipt["A7-L3R_fixed_reference_reproduction"]["status"] == "NOT_RUN_NO_FRESH_GPU"
    assert receipt["A7-L4_representation_attribution"]["unavailable_aggregate_record"]["status"] == "NOT_AVAILABLE"
    assert receipt["A7-L5_query_rescue"]["status"] == "NOT_AVAILABLE"
    assert receipt["A7-L5_query_rescue"]["unavailable_aggregate_record"]["comparator_system_count"] == 0
    assert receipt["A7-L6_candidate_exposure_error_anatomy"]["populations"]["ALL"]["relevant_family_exposed_at_100"] == 1
    assert receipt["A7-L6_candidate_exposure_error_anatomy"]["populations"]["ALL"]["aggregate_query_classes"] == {
        "fully_exposed_at_100": 1,
        "partially_exposed_at_100": 0,
        "deep_only_101_to_200": 0,
        "unretrieved_at_200": 0,
    }
    oracle = receipt["A7-L7_oracle_retrieval_boundary"]["populations"]["ALL"]
    assert oracle["bounded_top_200_oracle_nDCG@10"] == 1.0
    assert oracle["bounded_top_200_oracle_nDCG@100"] == 1.0
    assert receipt["A7-L7_oracle_retrieval_boundary"]["not_a_reranker_or_system_result"] is True
    assert "opaque_query_token" not in encoded and "q-" not in encoded
    assert any(row["metric"] == "curves.100.Recall" for row in rows)
    assert any(row["metric"] == "bounded_top_200_oracle_nDCG@10" for row in rows)


def test_a7_public_writer_rejects_owner_store_and_leaking_csv(tmp_path: Path) -> None:
    with pytest.raises(A7DiagnosisError, match="Owner Store"):
        write_public_outputs(receipt={"status": "PASS", "receipt_sha256": "x"}, csv_rows=[], output_root=Path("04_Owner_Stores") / "unsafe")
    with pytest.raises(A7DiagnosisError, match="leak"):
        write_public_outputs(receipt={"status": "PASS", "receipt_sha256": "x"}, csv_rows=[{"layer": "A7", "population": "ALL", "metric": "safe", "value": "q-secret"}], output_root=tmp_path / "safe")
