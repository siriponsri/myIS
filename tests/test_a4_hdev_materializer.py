"""Focused protected-local tests for A4 HDEV handoff materialization."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pyarrow as pa
import pyarrow.ipc as ipc
import pytest

from myis_research.armindex.a4_hdev_materializer import (
    A4HdevMaterializerError,
    materialize_a4_hdev_handoff,
    validate_a4_hdev_handoff,
)
from myis_research.kernel.canonical import canonical_json, canonical_sha256, file_sha256


def _write_json(path: Path, value: object) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(canonical_json(row) + "\n" for row in rows), encoding="utf-8")


def _self_hashed(value: dict[str, object], field: str) -> dict[str, object]:
    return {**value, field: canonical_sha256(value)}


def _fixture(tmp_path: Path) -> dict[str, Path]:
    store = tmp_path / "04_Owner_Stores"
    source = store / "source"
    package = store / "a3-train250"
    source.mkdir(parents=True)
    (package / "inputs").mkdir(parents=True)
    source_queries = source / "queries.arrow"
    source_queries.write_bytes(b"synthetic-source-query-arrow")
    hdev = [f"source-hdev-{index:03d}" for index in range(100)]
    rep = [f"source-rep-{index:03d}" for index in range(150)]
    relations = package / "inputs" / "evaluator-relations.arrow"
    table = pa.table(
        {
            "query_id": pa.array(hdev + rep, type=pa.large_string()),
            "relevant_id": pa.array([f"rel-{index:03d}" for index in range(250)], type=pa.large_string()),
            "relevance_score": pa.array([1.0] * 250),
            "domain_rel": pa.array(["IN"] * 250),
        }
    )
    with relations.open("wb") as handle:
        with ipc.new_stream(handle, table.schema) as writer:
            writer.write_table(table)
    membership_body: dict[str, object] = {
        "schema_version": "myis.armindex-a1.2-rep-harness-protected-membership.v1",
        "algorithm_id": "synthetic-split-v1",
        "algorithm_source_sha256": "a" * 64,
        "decision_id": "synthetic-decision",
        "decision_sha256": "b" * 64,
        "grouping_constraints": [],
        "harness_dev": hdev,
        "harness_dev_membership_sha256": canonical_sha256(sorted(hdev)),
        "parent_split_file_sha256": "c" * 64,
        "parent_split_sha256": "d" * 64,
        "parent_train_membership_sha256": "e" * 64,
        "rep_dev": rep,
        "rep_dev_membership_sha256": canonical_sha256(sorted(rep)),
        "seed": 42,
        "source_hashes": {
            "queries_arrow_sha256": file_sha256(source_queries),
            "relations_arrow_sha256": file_sha256(relations),
        },
        "strata": [{"stratum_key": "IN|0001", "role_set": "IN", "relevance_count": 1, "harness_dev": hdev, "rep_dev": rep}],
    }
    membership = _self_hashed(membership_body, "protected_membership_sha256")
    membership_path = source / "membership.json"
    _write_json(membership_path, membership)
    split_body: dict[str, object] = {
        "schema_version": "myis.armindex-a1.2-rep-harness-split-receipt.v1",
        "status": "PASS",
        "algorithm_id": membership["algorithm_id"],
        "algorithm_source_sha256": membership["algorithm_source_sha256"],
        "decision_id": membership["decision_id"],
        "decision_sha256": membership["decision_sha256"],
        "parent_split_sha256": membership["parent_split_sha256"],
        "parent_train_membership_sha256": membership["parent_train_membership_sha256"],
        "protected_membership_sha256": membership["protected_membership_sha256"],
        "harness_dev_membership_sha256": membership["harness_dev_membership_sha256"],
        "rep_dev_membership_sha256": membership["rep_dev_membership_sha256"],
        "seed": membership["seed"],
        "counts": {"harness_dev": 100, "parent_train": 250, "rep_dev": 150},
        "source_hashes": membership["source_hashes"],
        "strata": [{"stratum_key": "IN|0001", "role_set": "IN", "harness_dev_count": 100, "rep_dev_count": 150, "parent_count": 250}],
    }
    split_receipt = _self_hashed(split_body, "receipt_sha256")
    split_receipt_path = source / "split-receipt.json"
    _write_json(split_receipt_path, split_receipt)
    source_ids = hdev + rep
    tokens = [f"Q-{hashlib.sha256(f'742b38916b194950515ffcb911c9f6b9f44f458b962c376db6a187c8b971a2e6:Q:{source_id}'.encode()).hexdigest()[:32]}" for source_id in source_ids]
    query_rows = [{"work_token": token, "text": f"synthetic query {index}"} for index, token in enumerate(tokens)]
    membership_rows = [{"work_token": token, "eligible_out": index % 2 == 0} for index, token in enumerate(tokens)]
    qrels_rows = [{"work_token": token, "relevance": {"F-synthetic": 1.0}} for token in tokens]
    queries = package / "inputs" / "queries.jsonl"
    package_membership = package / "inputs" / "membership.jsonl"
    qrels = package / "inputs" / "qrels.jsonl"
    _write_jsonl(queries, query_rows)
    _write_jsonl(package_membership, membership_rows)
    _write_jsonl(qrels, qrels_rows)
    scope = {
        "schema_version": "myis.armindex-a3-train-scope.v1",
        "scope": "Train-250",
        "query_count": 250,
        "queries_sha256": file_sha256(queries),
        "split_commitment_sha256": "f" * 64,
    }
    scope_path = package / "train-scope.json"
    _write_json(scope_path, scope)
    package_body = {
        "schema_version": "myis.armindex-a3-train250-owner-package-receipt.v1",
        "status": "PASS_A3_TRAIN250_OWNER_PACKAGE",
        "queries_sha256": file_sha256(queries),
        "membership_sha256": file_sha256(package_membership),
        "qrels_sha256": file_sha256(qrels),
        "relations_arrow_sha256": file_sha256(relations),
        "scope_sha256": scope["split_commitment_sha256"],
        "query_count": 250,
        "harness_dev_count": 100,
        "rep_dev_count": 150,
        "parent_split_sha256": membership["parent_split_sha256"],
        "split_receipt_sha256": split_receipt["receipt_sha256"],
        "source_arrow_hashes": {
            "queries_000_sha256": file_sha256(source_queries),
            "relations_000_sha256": file_sha256(relations),
        },
        "protected_payload_included": False,
    }
    package_receipt = _self_hashed(package_body, "receipt_sha256")
    package_receipt_path = package / "A3_TRAIN250_OWNER_PACKAGE_RECEIPT.json"
    _write_json(package_receipt_path, package_receipt)
    map_path = source / "query-id-map.jsonl"
    _write_jsonl(map_path, [{"work_token": token, "query_id": identifier} for token, identifier in zip(tokens, source_ids, strict=True)])
    return {
        "store": store,
        "membership": membership_path,
        "split_receipt": split_receipt_path,
        "scope": scope_path,
        "package_receipt": package_receipt_path,
        "queries": queries,
        "package_membership": package_membership,
        "qrels": qrels,
        "source_queries": source_queries,
        "relations": relations,
        "map": map_path,
    }


def _materialize(paths: dict[str, Path], *, output_name: str, include_map: bool = False) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "membership_path": paths["membership"],
        "split_receipt_path": paths["split_receipt"],
        "train_scope_path": paths["scope"],
        "train_package_receipt_path": paths["package_receipt"],
        "train_queries_path": paths["queries"],
        "train_membership_path": paths["package_membership"],
        "train_qrels_path": paths["qrels"],
        "source_queries_path": paths["source_queries"],
        "evaluator_relations_path": paths["relations"],
        "output_root": paths["store"] / output_name,
        "owner_store_root": paths["store"],
        "attempt_id": "a4-test-001",
    }
    if include_map:
        kwargs["train_query_id_map_path"] = paths["map"]
    return materialize_a4_hdev_handoff(**kwargs)  # type: ignore[arg-type]


def test_materializes_hash_bound_aggregate_safe_hdev_handoff(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    receipt = _materialize(paths, output_name="a4-handoff", include_map=True)
    assert receipt["hdev_query_count"] == 100
    assert receipt["linkage"]["query_id_map_complete"] is True  # type: ignore[index]
    root = paths["store"] / "a4-handoff"
    assert validate_a4_hdev_handoff(root, expected_attempt_id="a4-test-001")["receipt_sha256"] == receipt["receipt_sha256"]
    serialized = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.json"))
    assert "source-hdev-000" not in serialized
    assert "synthetic query 0" not in serialized
    assert len((root / "protected" / "hdev-queries.jsonl").read_text(encoding="utf-8").splitlines()) == 100


def test_accepts_lineage_without_intersecting_source_and_opaque_tokens(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    receipt = _materialize(paths, output_name="a4-lineage-only")
    assert receipt["linkage"]["hdev_subset_of_train250"] is True  # type: ignore[index]
    assert receipt["linkage"]["query_id_map_complete"] is False  # type: ignore[index]


def test_fails_closed_when_qrels_break_train250_linkage(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    rows = [json.loads(line) for line in paths["qrels"].read_text(encoding="utf-8").splitlines()]
    rows[0]["work_token"] = "Q-not-in-query-package"
    _write_jsonl(paths["qrels"], rows)
    with pytest.raises(A4HdevMaterializerError, match="qrels/membership/query linkage"):
        _materialize(paths, output_name="a4-bad-qrels")
    assert not (paths["store"] / "a4-bad-qrels").exists()


def test_fails_closed_when_source_relation_hash_drifts(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    paths["relations"].write_bytes(paths["relations"].read_bytes() + b"drift")
    with pytest.raises(A4HdevMaterializerError, match="hash drifted"):
        _materialize(paths, output_name="a4-drift")
    assert not (paths["store"] / "a4-drift").exists()
