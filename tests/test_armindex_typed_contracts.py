from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from myis_research.armindex.contracts import (
    CONTRACT_MODELS,
    AggregateMetric,
    AggregateReceipt,
    ArmAdapterLock,
    ArmCapabilities,
    ArmSpecification,
    AutoIndexBatch,
    AutoIndexCandidate,
    BrainProjectionEvent,
    CandidatePool,
    CompiledRepresentation,
    ComplementarityReport,
    CostReceipt,
    EvaluationRequest,
    FamilyDocument,
    FamilyRanking,
    FusionConfiguration,
    HarnessAction,
    HarnessConfiguration,
    IndexManifest,
    MLflowMirrorEvent,
    PhaseCloseoutEvent,
    ProductionProfile,
    QueryFamily,
    RepresentationProgram,
    RunManifest,
    SearchHit,
    SearchRequest,
    SearchableUnit,
    SourceSpan,
    TransferEvaluation,
    grouped_json_schemas,
    parse_contract,
    validate_grouped_schema,
)
from myis_research.kernel.canonical import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
H = "a" * 64


def _meta(schema_version: str, contract_id: str, *, commercial_status: str = "commercial_capable") -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "contract_id": contract_id,
        "evidence_class": "synthetic_fixture",
        "scientific_authority": False,
        "commercial_status": commercial_status,
        "protected_data_accessed": False,
    }


def _contracts() -> tuple[object, ...]:
    span = SourceSpan(
        **_meta("myis.armindex-source-span.v1", "span-1"),
        source_id="publication-1",
        field_name="title",
        start_offset=0,
        end_offset=5,
        source_sha256=H,
    )
    document = FamilyDocument(
        **_meta("myis.armindex-family-document.v1", "document-1"),
        family_id="family-1",
        publication_id="publication-1",
        fields={"title": "alpha"},
        source_spans=(span,),
        document_sha256=H,
    )
    query = QueryFamily(
        **_meta("myis.armindex-query-family.v1", "query-1"),
        query_id="fixture-query-1",
        family_id="fixture-query-family-1",
        text="alpha",
        data_role="synthetic_fixture",
        query_sha256=H,
    )
    unit = SearchableUnit(
        **_meta("myis.armindex-searchable-unit.v1", "unit-1"),
        unit_id="unit-1",
        family_id="family-1",
        publication_id="publication-1",
        representation_program_id="program-1",
        text="TITLE: alpha",
        source_spans=(span,),
        content_sha256=H,
    )
    program = RepresentationProgram(
        **_meta("myis.armindex-representation-program.v2", "program-contract-1"),
        program_id="program-1",
        source_fields=("title",),
        field_order=("title",),
        field_labels={"title": "TITLE"},
        unit_kind="document",
        normalization="unicode_nfkc_whitespace_lower",
        duplicate_policy="family_content_hash_first",
        family_aggregation="single_unit",
    )
    compiled = CompiledRepresentation(
        **_meta("myis.armindex-compiled-representation.v1", "compiled-1"),
        compiled_id="compiled-1",
        program_id="program-1",
        logical_program_sha256=program.contract_sha256,
        arm_id="ARM-01",
        units=(unit,),
        unit_count=1,
        estimated_storage_bytes=12,
        truncation_count=0,
        omitted_span_count=0,
        compiled_sha256=H,
    )
    capabilities = ArmCapabilities(
        method="lexical",
        maximum_input_length=100000,
        multilingual=True,
        cpu_supported=True,
        gpu_supported=False,
        batch_supported=True,
        index_type="in_memory_okapi_bm25_v1",
    )
    arm = ArmSpecification(
        **_meta("myis.armindex-arm-specification.v1", "arm-spec-1"),
        arm_id="ARM-01",
        model_id="lexical/bm25s",
        role="lexical_anchor_cpu_fallback",
        license_id="Apache-2.0",
        capabilities=capabilities,
        adapter_status="fixture_ready",
        measured_use_allowed=False,
    )
    lock = ArmAdapterLock(
        **_meta("myis.armindex-arm-adapter-lock.v1", "adapter-lock-1"),
        arm_id="ARM-01",
        model_id="fixture/myis-okapi-bm25",
        resolved_model_sha="b" * 40,
        tokenizer_sha256=H,
        adapter_sha256=H,
        input_format={"query": "plain_text"},
        pooling="not_applicable",
        normalization="unicode_nfkc_whitespace_lower",
        dimension=1,
        maximum_input_length=100000,
        precision="lexical",
        similarity="okapi_bm25",
        network_required=False,
    )
    index = IndexManifest(
        **_meta("myis.armindex-index-manifest.v1", "index-1"),
        index_id="index-1",
        arm_id="ARM-01",
        compiled_representation_sha256=compiled.contract_sha256,
        adapter_lock_sha256=lock.contract_sha256,
        index_type="in_memory_okapi_bm25_v1",
        unit_count=1,
        index_size_bytes=12,
        artifact_uri="temporary://armindex-fixture/index-1",
        index_sha256=H,
    )
    search_request = SearchRequest(
        **_meta("myis.armindex-search-request.v1", "search-request-1"),
        request_id="search-request-1",
        arm_id="ARM-01",
        index_manifest_sha256=index.contract_sha256,
        query=query,
        depth=100,
    )
    hit = SearchHit(
        **_meta("myis.armindex-search-hit.v1", "hit-1"),
        request_id="search-request-1",
        arm_id="ARM-01",
        unit_id="unit-1",
        family_id="family-1",
        publication_id="publication-1",
        rank=1,
        score=1.0,
    )
    ranking = FamilyRanking(
        **_meta("myis.armindex-family-ranking.v1", "ranking-contract-1"),
        ranking_id="ranking-1",
        request_id="search-request-1",
        arm_ids=("ARM-01",),
        entries=({"family_id": "family-1", "rank": 1, "score": 1.0, "supporting_unit_ids": ("unit-1",)},),
        depth=100,
        ranking_sha256=H,
    )
    pool = CandidatePool(
        **_meta("myis.armindex-candidate-pool.v1", "pool-contract-1"),
        pool_id="pool-1",
        request_id="search-request-1",
        arm_ids=("ARM-01",),
        depth_by_arm={"ARM-01": 100},
        hits=(hit,),
        pool_sha256=H,
    )
    fusion = FusionConfiguration(
        **_meta("myis.armindex-fusion-configuration.v1", "fusion-contract-1"),
        fusion_id="identity-1",
        method="identity",
        arm_ids=("ARM-01",),
        parameters={},
    )
    transfer = TransferEvaluation(
        **_meta("myis.armindex-transfer-evaluation.v1", "transfer-1"),
        transfer_id="transfer-1",
        source_program_id="program-1",
        source_arm_id="ARM-01",
        target_arm_id="ARM-02",
        transfer_state="adapter_constrained",
        compiled_representation_sha256=H,
        metric_sha256s=(),
    )
    complementarity = ComplementarityReport(
        **_meta("myis.armindex-complementarity-report.v1", "complementarity-1", commercial_status="mixed"),
        report_id="complementarity-1",
        arm_ids=("ARM-01", "ARM-02"),
        candidate_depth=100,
        pairwise_overlap={"ARM-01:ARM-02": 0.5},
        rank_overlap={"ARM-01:ARM-02": 0.4},
        unique_hit_counts={"ARM-01": 1, "ARM-02": 2},
        aggregate_metric_sha256s=(),
        gate_status="not_evaluated",
    )
    candidates = tuple(
        AutoIndexCandidate(
            **_meta("myis.armindex-autoindex-candidate.v1", f"candidate-contract-{index_value}"),
            candidate_id=f"candidate-{index_value}",
            arm_id="ARM-01",
            parent_candidate_id="incumbent-1",
            hypothesis_id=f"hypothesis-{index_value}",
            hypothesis=f"fixture hypothesis {index_value}",
            role=role,
            declared_axis="field_order",
            representation_program_sha256=format(index_value, "x") * 64,
            scientific_payload_sha256=format(index_value + 4, "x") * 64,
            axis_values={"field_order": index_value},
        )
        for index_value, role in enumerate(("exploit", "matched_ablation", "orthogonal", "diversity"), start=1)
    )
    batch = AutoIndexBatch(
        **_meta("myis.armindex-autoindex-batch.v1", "batch-contract-1"),
        batch_id="batch-1",
        arm_id="ARM-01",
        iteration=1,
        incumbent_candidate_id="incumbent-1",
        status="frozen_before_evaluation",
        candidates=candidates,
        budget_counters={"candidates": 4, "seconds": 0},
    )
    harness = HarnessConfiguration(
        **_meta("myis.armindex-harness-configuration.v2", "harness-contract-1"),
        harness_id="harness-1",
        arm_ids=("ARM-01",),
        invocation_order=("ARM-01",),
        execution="sequential",
        initial_depth_by_arm={"ARM-01": 100},
        maximum_depth_by_arm={"ARM-01": 100},
        fusion_configuration_sha256=fusion.contract_sha256,
        early_stop={"maximum_actions": 1},
        cache_policy="disabled",
        latency_profile="FAST",
        runtime_features=("query_length",),
    )
    action = HarnessAction(
        **_meta("myis.armindex-harness-action.v1", "action-contract-1"),
        action_id="action-1",
        harness_id="harness-1",
        request_id="search-request-1",
        sequence=1,
        arm_id="ARM-01",
        action="search",
        depth=100,
        reason="fixed synthetic plan",
    )
    profile = ProductionProfile(
        **_meta("myis.armindex-production-profile.v1", "profile-contract-fast"),
        profile_id="FAST",
        harness_configuration_sha256=harness.contract_sha256,
        arm_ids=("ARM-01",),
        mode="synchronous",
        maximum_candidate_depth=100,
        commercial_only=True,
        readiness="contract_only",
    )
    evaluation = EvaluationRequest(
        **_meta("myis.armindex-evaluation-request.v1", "evaluation-request-1"),
        request_id="evaluation-request-1",
        ranking_sha256s=(ranking.contract_sha256,),
        metric_names=("recall_at_100", "ndcg_at_100", "ndcg_at_10"),
        synthetic_relevance={"fixture-query-1": ("family-1",)},
        data_role="synthetic_fixture",
        evaluator_sha256=H,
    )
    metric = AggregateMetric(
        **_meta("myis.armindex-aggregate-metric.v1", "metric-contract-1"),
        metric_id="metric-recall-1",
        name="recall_at_100",
        value=1.0,
        sample_count=1,
        scope="SYNTHETIC",
        direction="maximize",
        denominator="macro_mean_per_query_relevant_families",
        evidence_role="fixture_only",
    )
    manifest = RunManifest(
        **_meta("myis.armindex-run-manifest.v1", "manifest-contract-1"),
        run_id="fixture-run-1",
        campaign_id="armindex-multiretriever-v2",
        phase_id="A0_MIGRATION_FOUNDATION",
        task_id="A0.10",
        stage="fixture",
        status="valid",
        git_commit="b" * 40,
        git_tree="c" * 40,
        input_hashes={"documents": document.contract_sha256},
        method_sha256=program.contract_sha256,
        resources_sha256=H,
        artifact_sha256s=(ranking.contract_sha256,),
        measured_execution=False,
        selection_accesses=0,
        final_accesses=0,
    )
    cost = CostReceipt(
        **_meta("myis.armindex-cost-receipt.v1", "cost-contract-1"),
        receipt_id="cost-1",
        run_id="fixture-run-1",
        arm_ids=("ARM-01",),
        sample_count=1,
        latency_p50_ms=1.0,
        latency_p95_ms=2.0,
        latency_p99_ms=3.0,
        throughput_qps=1.0,
        cost_per_query_usd=0.0,
        charged_usd=0.0,
        index_size_bytes=12,
        ram_bytes=12,
        vram_bytes=0,
        run_manifest_sha256=manifest.contract_sha256,
    )
    receipt = AggregateReceipt(
        **_meta("myis.armindex-aggregate-receipt.v1", "receipt-contract-1"),
        receipt_id="receipt-1",
        run_id="fixture-run-1",
        run_manifest_sha256=manifest.contract_sha256,
        status="passed",
        aggregate_metric_sha256s=(metric.contract_sha256,),
        aggregate_counts={"documents": 1, "queries": 1},
        cost_receipt_sha256=cost.contract_sha256,
        measured_execution=False,
        selection_accesses=0,
        final_accesses=0,
    )
    closeout = PhaseCloseoutEvent(
        **_meta("myis.armindex-phase-closeout-event.v1", "closeout-event-1"),
        event_id="closeout-1",
        phase_id="A0_MIGRATION_FOUNDATION",
        task_id="A0.10",
        aggregate_receipt_sha256=receipt.contract_sha256,
        status="completed",
        next_authorized_action="synthetic-only A0 preflight",
    )
    brain = BrainProjectionEvent(
        **_meta("myis.armindex-brain-projection-event.v1", "brain-event-1"),
        event_id="brain-1",
        source_receipt_uri="campaigns/armindex-multiretriever-v2/evidence/fixture-receipt.json",
        source_receipt_sha256=receipt.contract_sha256,
        memory_kind="evidence",
        status="pending",
    )
    mlflow = MLflowMirrorEvent(
        **_meta("myis.armindex-mlflow-mirror-event.v1", "mlflow-event-1"),
        event_id="mlflow-1",
        source_receipt_uri="campaigns/armindex-multiretriever-v2/evidence/fixture-receipt.json",
        source_receipt_sha256=receipt.contract_sha256,
        experiment_name="myis-armindex-multiretriever-v2",
        allowlisted_tags={"campaign_id": "armindex-multiretriever-v2", "data_role": "fixture"},
        status="pending",
    )
    return (
        document,
        query,
        unit,
        span,
        program,
        compiled,
        arm,
        lock,
        index,
        search_request,
        hit,
        ranking,
        pool,
        fusion,
        transfer,
        complementarity,
        *candidates[:1],
        batch,
        harness,
        action,
        profile,
        evaluation,
        metric,
        manifest,
        receipt,
        cost,
        closeout,
        brain,
        mlflow,
    )


def test_all_29_contracts_are_typed_addressed_and_schema_valid() -> None:
    contracts = _contracts()
    assert len(CONTRACT_MODELS) == len(contracts) == 29
    assert {type(contract) for contract in contracts} == set(CONTRACT_MODELS)
    for contract in contracts:
        payload = contract.model_dump(mode="json")
        unsigned = {key: value for key, value in payload.items() if key != "contract_sha256"}
        assert payload["contract_sha256"] == canonical_sha256(unsigned)
        assert payload["commercial_status"]
        assert payload["protected_data_accessed"] is False
        validate_grouped_schema(ROOT, payload)
        assert parse_contract(payload) == contract


def test_checked_in_grouped_schemas_match_typed_registry() -> None:
    generated = grouped_json_schemas()
    assert len(generated) == 8
    for filename, schema in generated.items():
        checked_in = json.loads((ROOT / "schemas" / "armindex" / filename).read_text(encoding="utf-8"))
        assert checked_in == schema


def test_contract_hash_tampering_and_protected_payloads_fail_closed() -> None:
    document = _contracts()[0]
    tampered = document.model_dump(mode="json")
    tampered["publication_id"] = "publication-tampered"
    with pytest.raises(ValidationError, match="contract_sha256"):
        FamilyDocument.model_validate(tampered)

    with pytest.raises(ValidationError, match="protected payload key"):
        MLflowMirrorEvent(
            **_meta("myis.armindex-mlflow-mirror-event.v1", "unsafe-event"),
            event_id="unsafe",
            source_receipt_uri="evidence/receipt.json",
            source_receipt_sha256=H,
            experiment_name="myis-system",
            allowlisted_tags={"credentials": "forbidden"},
            status="pending",
        )

    with pytest.raises(ValidationError, match="personal absolute path"):
        BrainProjectionEvent(
            **_meta("myis.armindex-brain-projection-event.v1", "unsafe-brain-event"),
            event_id="unsafe",
            source_receipt_uri=r"C:\Users\example\receipt.json",
            source_receipt_sha256=H,
            memory_kind="evidence",
            status="pending",
        )

    invalid_authority = document.model_dump(mode="json", exclude={"contract_sha256"})
    invalid_authority["scientific_authority"] = True
    with pytest.raises(ValidationError, match="cannot claim scientific authority"):
        FamilyDocument.model_validate(invalid_authority)


def test_autoindex_batch_and_harness_constraints_are_semantic() -> None:
    contracts = _contracts()
    batch = next(item for item in contracts if isinstance(item, AutoIndexBatch))
    duplicate = batch.model_dump(mode="json", exclude={"contract_sha256"})
    duplicate["candidates"][3]["scientific_payload_sha256"] = duplicate["candidates"][2]["scientific_payload_sha256"]
    duplicate["candidates"][3].pop("contract_sha256")
    with pytest.raises(ValidationError, match="scientific payloads must be unique"):
        AutoIndexBatch.model_validate(duplicate)

    harness = next(item for item in contracts if isinstance(item, HarnessConfiguration))
    invalid = harness.model_dump(mode="json", exclude={"contract_sha256"})
    invalid["arm_ids"] = ["ARM-01", "ARM-02"]
    with pytest.raises(ValidationError, match="permutation"):
        HarnessConfiguration.model_validate(invalid)

    with pytest.raises(ValidationError, match="FAST"):
        ProductionProfile(
            **_meta("myis.armindex-production-profile.v1", "invalid-fast"),
            profile_id="FAST",
            harness_configuration_sha256=H,
            arm_ids=("ARM-02",),
            mode="asynchronous",
            maximum_candidate_depth=100,
            commercial_only=True,
            readiness="contract_only",
        )
