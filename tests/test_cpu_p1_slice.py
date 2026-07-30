from __future__ import annotations

import json

import pytest

from myis_research.kernel.integrity import run_integrity_preflight
from myis_research.kernel.p1 import evaluate_baseline
from myis_research.scope import DapfamAdapter, compile_scope, parse_scope_spec


def _docs() -> list[dict[str, str]]:
    return [
        {"doc_id": "d1", "family_id": "f1", "text": "grounded source compiler"},
        {"doc_id": "d2", "family_id": "f2", "text": "different mechanism"},
    ]


def _queries() -> list[dict[str, str]]:
    return [{"query_id": "q1", "text": "grounded compiler", "split": "train"}]


def test_r0_and_r0w_are_deterministic() -> None:
    kwargs = {"documents": _docs(), "queries": _queries(), "qrels": {"q1": ["f1"]}, "top_k": 100}
    first = evaluate_baseline(arm_id="R0", **kwargs)
    second = evaluate_baseline(arm_id="R0", **kwargs)
    assert first["metrics"] == second["metrics"]
    assert first["input_commitment"] == second["input_commitment"]
    first_w = evaluate_baseline(arm_id="R0-W", **kwargs)
    second_w = evaluate_baseline(arm_id="R0-W", **kwargs)
    assert first_w["metrics"] == second_w["metrics"]
    assert first_w["input_commitment"] == second_w["input_commitment"]


def test_integrity_receipt_is_aggregate_only_and_detects_leaks() -> None:
    receipt = run_integrity_preflight(
        documents=[*_docs(), {"doc_id": "d3", "family_id": "f3", "text": "grounded source compiler"}],
        queries=_queries(),
        targets={"q1": ["f1"]},
        splits={"train": ["q1"], "selection": ["q1"]},
    )
    assert receipt["status"] == "blocked"
    assert receipt["checks"]["exact_text_duplicate"]["status"] == "blocked"
    assert receipt["checks"]["cross_split_query_identity"]["status"] == "blocked"
    assert "q1" not in json.dumps(receipt)


def _scope_spec() -> dict[str, object]:
    return {
        "schema_version": "myis.scope-dsl.v1",
        "spec_id": "spec-scope-fixture-v01",
        "parent_spec_id": None,
        "hypothesis_id": "hyp-i01-001",
        "compiler_api_version": "1.0.0",
        "description": {"en": "fixture"},
        "fields": [
            {"field_id": "family", "source": "family_id", "role": "identity"},
            {"field_id": "publication", "source": "publication_id", "role": "identity"},
            {"field_id": "abstract", "source": "abstract", "role": "text"},
        ],
        "claims": {},
        "graph": {},
        "views": [{
            "view_id": "abstract", "kind": "document", "source_fields": ["abstract"],
            "family_field": "family", "publication_field": "publication", "span_scheme": "field-v1",
            "compiler_version": "1.0.0", "normalization_version": "1.0.0", "searchable": True,
            "aggregation": "family_maxp", "deterministic_order": "source",
        }],
        "aggregation": {},
        "constraints": {"require_source_grounding": True, "abstractive_summaries": False, "query_specific_vocabulary": False},
    }


def test_scope_compiler_is_deterministic_and_enforces_dapfam_limit() -> None:
    spec = parse_scope_spec(_scope_spec())
    records = [{"family": "f1", "publication": "p1", "abstract": "grounded source"}]
    first = compile_scope(spec, records, adapter=DapfamAdapter())
    second = compile_scope(spec, records, adapter=DapfamAdapter())
    assert first.output_hash == second.output_hash
    with pytest.raises(Exception):
        compile_scope(spec, records * 5, adapter=DapfamAdapter())
