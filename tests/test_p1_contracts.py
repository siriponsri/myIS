from __future__ import annotations

from pathlib import Path

from myis_research.kernel.integrity import run_integrity_preflight
from myis_research.kernel.manifest import build_manifest, manifest_round_trip
from myis_research.kernel.manifest_validation import capture_git_state
from myis_research.kernel.p1 import BM25Index, evaluate_baseline
from myis_research.owner_local import build_receipt
from myis_research.scope import parse_scope_spec


def test_bm25_is_not_token_overlap() -> None:
    index = BM25Index([
        {"doc_id": "d1", "family_id": "f1", "text": "rare common"},
        {"doc_id": "d2", "family_id": "f2", "text": "common common common"},
    ])
    ranked = index.rank("rare common")
    assert ranked[0][0] == "d1"
    assert ranked[0][2] > 0.0


def test_recall_denominator_and_all_in_out_are_explicit() -> None:
    documents = [
        {"doc_id": "d1", "family_id": "f1", "text": "alpha"},
        {"doc_id": "d2", "family_id": "f2", "text": "beta"},
        {"doc_id": "d3", "family_id": "f3", "text": "gamma"},
    ]
    queries = [
        {"query_id": "q1", "text": "alpha", "split": "train"},
        {"query_id": "q2", "text": "beta", "split": "train"},
        {"query_id": "q3", "text": "ignored", "split": "train"},
    ]
    result = evaluate_baseline(
        documents=documents,
        queries=queries,
        qrels={"q1": ["f1", "f3"], "q2": ["f2"]},
        qrel_domains={"q1": {"f1": "IN", "f3": "OUT"}, "q2": {"f2": "OUT"}},
        arm_id="R0",
        split_name="train",
    )
    rows = {row["scope"]: row for row in result["metrics"]}
    assert rows["ALL"]["n"] == 2
    assert rows["IN"]["n"] == 1
    assert rows["OUT"]["n"] == 2
    assert rows["ALL"]["value"] == 0.75
    assert rows["ALL"]["retrieved_relevant"] == 2
    assert rows["ALL"]["relevant_total"] == 3
    assert rows["ALL"]["denominator"] == "macro_mean_per_query_relevant_families"


def test_manifest_builder_round_trips_one_canonical_shape() -> None:
    git = capture_git_state(Path(__file__).resolve().parents[1])
    request = {
        "schema_version": "myis.owner-local-request.v2",
        "request_id": "p1-manifest-contract",
        "decision_id": "P1_CPU_EXECUTION_ENVELOPE",
        "phase_id": "P1_CPU_BASELINE",
        "stage": "train_selection",
        "scope": {"campaign_sha256": "a" * 64},
        "git_commit": git["commit"],
        "input_hashes": {"documents_sha256": "b" * 64},
    }
    receipt = build_receipt(
        request,
        aggregate_counts={"queries": 2, "train_queries": 2, "selection_queries": 2},
        aggregate_hashes={f"{arm.lower()}_{split}_metrics": "c" * 64 for arm in ("R0", "R0-W") for split in ("train", "selection")},
        metrics=[
            {"arm": arm, "name": "recall_at_100", "value": 1.0, "n": 1, "retrieved_relevant": 1, "relevant_total": 1, "scope": scope, "split": split, "direction": "maximize", "denominator": "macro_mean_per_query_relevant_families", "evidence_role": "primary" if scope == "OUT" else "secondary"}
            for arm in ("R0", "R0-W") for split in ("train", "selection") for scope in ("ALL", "IN", "OUT")
        ],
        cost_usd=0.0,
        latency_seconds=0.0,
        lineage_hashes={key: "b" * 64 for key in ("dataset_sha256", "corpus_sha256", "query_sha256", "qrels_sha256", "split_sha256", "index_sha256", "evaluator_sha256")},
    )
    payload = build_manifest(
        run_id="run-p1", parent_run_id=None, experiment_id="exp-p1", campaign_id="scope-autoindex-v1",
        stage="train", status="valid", source={"dataset": "dapfam"}, data={"split": "train"},
        method={"arm": "R0"}, resources={"cost_usd": 0.0}, metrics=[], artifacts=[],
        evidence_class="train_selection_measured", repository_root=Path(__file__).resolve().parents[1],
        owner_local_request=request, owner_local_receipt=receipt,
    )
    assert manifest_round_trip(payload)["schema_version"] == "myis.run-manifest.v2"


def test_integrity_uses_scalable_near_duplicate_algorithm() -> None:
    documents = [{"doc_id": f"d{i}", "family_id": f"f{i}", "text": f"unique-token-{i}"} for i in range(5000)]
    receipt = run_integrity_preflight(documents=documents, queries=[], targets={}, splits={})
    assert receipt["checks"]["near_duplicate"]["algorithm"] == "simhash-lsh-capped-v2"
    assert receipt["checks"]["near_duplicate"]["complexity"] == "bounded_linear_plus_candidate_cap"


def test_scope_runtime_accepts_only_active_v1_schema() -> None:
    payload = {
        "schema_version": "myis.scope-dsl.v1", "spec_id": "spec-fixture-v01", "parent_spec_id": None,
        "hypothesis_id": "hyp-i01-001", "compiler_api_version": "1.0.0", "description": {"en": "fixture"},
        "fields": [{"field_id": "family_id", "source": "family_id", "role": "identity"}, {"field_id": "publication_id", "source": "publication_id", "role": "identity"}, {"field_id": "title", "source": "title", "role": "text"}],
        "claims": {}, "graph": {}, "views": [{"view_id": "tac", "kind": "document", "source_fields": ["title"], "family_field": "family_id", "publication_field": "publication_id", "span_scheme": "field-v1", "compiler_version": "1.0.0", "normalization_version": "1.0.0"}],
        "aggregation": {}, "constraints": {"require_source_grounding": True, "abstractive_summaries": False, "query_specific_vocabulary": False},
    }
    assert parse_scope_spec(payload).schema_version == "myis.scope-dsl.v1"
    payload["schema_version"] = "myis.scope-dsl.v2"
    try:
        parse_scope_spec(payload)
    except Exception:
        pass
    else:
        raise AssertionError("v2 SCOPE must not remain active")
