"""Focused tests for the fail-closed Selection-125 input materializer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex.a4_selection_materializer import (
    A4SelectionMaterializerError,
    materialize_selection_inputs,
    validate_selection_input_materialization,
)
from myis_research.kernel.canonical import canonical_json, canonical_sha256, file_sha256


def _write_json(path: Path, value: object) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(canonical_json(row) + "\n" for row in rows), encoding="utf-8")


def _fixture(tmp_path: Path, *, complete: bool = True) -> tuple[Path, Path, Path, Path]:
    store = tmp_path / "04_Owner_Stores"
    source = store / "source"
    source.mkdir(parents=True)
    train = [f"train-{i:03d}" for i in range(250)]
    selection = [f"selection-{i:03d}" for i in range(125)]
    final = [f"final-{i:03d}" for i in range(872)]
    split = {"schema_version": "myis.protected-split.v1", "algorithm": "sha256-seed-colon-id-lexical-v1", "seed": 42, "train": train, "selection": selection, "final": final}
    split["split_sha256"] = "f" * 64
    split_path = source / "split.json"
    _write_json(split_path, split)
    ids = train + selection + final
    if not complete:
        ids = ids[:-1]
    query_path = source / "queries.jsonl"
    _write_jsonl(query_path, [{"query_id": query_id, "text": f"query {query_id}"} for query_id in ids])
    relations = source / "relations.arrow"
    relations.write_bytes(b"synthetic evaluator relation source")
    return store, split_path, query_path, relations


def test_materializes_exact_selection_scope(tmp_path: Path) -> None:
    store, split, queries, relations = _fixture(tmp_path)
    output = store / "a4" / "attempt-001"
    receipt = materialize_selection_inputs(
        protected_split_path=split,
        source_queries_path=queries,
        evaluator_relations_path=relations,
        output_root=output,
        owner_store_root=store,
        attempt_id="a4-selection-test-001",
        expected_parent_split_sha256="f" * 64,
        expected_source_queries_sha256=file_sha256(queries),
        expected_evaluator_relations_sha256=file_sha256(relations),
    )
    assert receipt["status"] == "PASS_A4_SELECTION_INPUT_MATERIALIZED"
    assert receipt["selection_query_count"] == 125
    assert receipt["selection_accesses"] == receipt["final_accesses"] == 0
    validated = validate_selection_input_materialization(output, expected_attempt_id="a4-selection-test-001")
    assert validated["receipt_sha256"] == receipt["receipt_sha256"]
    rows = [json.loads(line) for line in (output / "protected" / "selection-125-queries.jsonl").read_text().splitlines()]
    assert len(rows) == 125
    assert all(set(row) == {"work_token", "text"} for row in rows)


def test_rejects_incomplete_canonical_payload(tmp_path: Path) -> None:
    store, split, queries, relations = _fixture(tmp_path, complete=False)
    with pytest.raises(A4SelectionMaterializerError, match="canonical query payload"):
        materialize_selection_inputs(
            protected_split_path=split,
            source_queries_path=queries,
            evaluator_relations_path=relations,
            output_root=store / "a4" / "attempt-001",
            owner_store_root=store,
            attempt_id="a4-selection-test-002",
            expected_parent_split_sha256="f" * 64,
            expected_source_queries_sha256=file_sha256(queries),
            expected_evaluator_relations_sha256=file_sha256(relations),
        )


def test_rejects_existing_attempt_root(tmp_path: Path) -> None:
    store, split, queries, relations = _fixture(tmp_path)
    output = store / "a4" / "attempt-001"
    output.mkdir(parents=True)
    with pytest.raises(A4SelectionMaterializerError, match="already exists"):
        materialize_selection_inputs(
            protected_split_path=split,
            source_queries_path=queries,
            evaluator_relations_path=relations,
            output_root=output,
            owner_store_root=store,
            attempt_id="a4-selection-test-003",
            expected_parent_split_sha256="f" * 64,
            expected_source_queries_sha256=file_sha256(queries),
            expected_evaluator_relations_sha256=file_sha256(relations),
        )
