from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_scientific_execution_request_v11 import (
    BUDGET_PATH,
    HANDOFF_PATH,
    JOB_ROOT,
    LINEAGE,
    PROGRAM_SET_PATH,
    PROVIDER_PATH,
    RECEIPT_PATH,
    RESULT_CONTRACT_PATH,
    RESULT_SCHEMA_PATH,
    REQUEST_PATH,
    REQUEST_SCHEMA_PATH,
    STOP_PATH,
    TRANSFER_PATH,
    WORKLOAD_SET_PATH,
    _validate_ledger,
    _validate_safe,
    _validate_schema,
    materialize,
    validate,
)
from myis_research.kernel.canonical import canonical_sha256, file_sha256


ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> dict[str, object]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_v11_request_validates_and_keeps_every_execution_surface_locked() -> None:
    result = validate(ROOT)
    request = _read(REQUEST_PATH)
    receipt = _read(RECEIPT_PATH)

    assert result["status"] == "PASS"
    assert result["lineage_bindings"] == 11
    assert result["workload_manifests"] == 5
    assert request["status"] == "prepared_for_owner_review_not_adopted"
    assert request["adoption"]["adoption_receipt_present"] is False
    assert set(request["authorization"].values()) == {False}
    assert set(request["counters"].values()) == {0}
    assert receipt["launch_allowed"] is False
    assert receipt["adopted_for_execution"] is False
    assert receipt["measured_runs"] == 0
    assert receipt["selection_accesses"] == 0
    assert receipt["final_accesses"] == 0
    assert receipt["charged_usd"] == 0


def test_v11_materialization_is_idempotent() -> None:
    before = file_sha256(ROOT / RECEIPT_PATH)
    result = materialize(ROOT)
    assert result["status"] == "PASS"
    assert file_sha256(ROOT / RECEIPT_PATH) == before


def test_v11_binds_exact_unchanged_v1_through_v10_bytes() -> None:
    request = _read(REQUEST_PATH)
    observed = {
        item["revision"]: (item["uri"], item["file_sha256"], item["embedded_sha256"])
        for item in request["predecessor_lineage"]
    }
    expected = {
        revision: (uri, digest, embedded)
        for revision, uri, digest, embedded, _ in LINEAGE
    }
    assert observed == expected
    for _, uri, digest, _, _ in LINEAGE:
        assert file_sha256(ROOT / uri) == digest


def test_v11_budget_requires_whole_workload_and_fresh_quote() -> None:
    budget = _read(BUDGET_PATH)
    limits = budget["hard_stops"]
    window = budget["requested_window"]

    assert limits == {
        "common_screen_usd": 18,
        "a1_total_usd": 23,
        "campaign_usd": 100,
    }
    assert window["owner_ttl_hours"] * window["maximum_hourly_rate_at_full_ttl_usd"] == 18
    assert window["whole_workload_admission_required"] is True
    assert window["partial_arm_admission_allowed"] is False
    assert budget["admission"]["fresh_live_quote_required"] is True
    assert budget["admission"]["unknown_billable_component_allowed"] is False
    assert "worst_case_total_charge_usd" in budget["admission"][
        "sanitized_quote_receipt_required_fields"
    ]
    assert all(
        quote["admissible_for_fresh_launch"] is False
        for quote in budget["historical_quotes"]
    )
    assert budget["launch_allowed"] is False


def test_v11_protected_handoff_keeps_evaluation_and_identity_mapping_local() -> None:
    handoff = _read(HANDOFF_PATH)
    local = set(handoff["owner_local_only_surfaces"])
    remote_inputs = set(handoff["remote_input_allowlist"])

    assert {"qrels", "split_membership", "query_ids", "per_query_outcomes"} <= local
    assert "ephemeral_token_identity_map" in local
    assert "frozen_query_text_keyed_by_run_scoped_opaque_work_tokens" in remote_inputs
    assert "structured_independent_claim_markers_without_original_identifiers" in remote_inputs
    assert handoff["safe_aggregate_protocol"]["development_query_count"] == 150
    assert handoff["safe_aggregate_protocol"]["reserved_harness_dev_count"] == 100
    assert handoff["owner_local_evaluation"]["required"] is True
    assert handoff["owner_payload_opened_during_preparation"] is False
    assert handoff["remote_payload_staged_during_preparation"] is False


def test_v11_workloads_freeze_five_programs_and_one_dense_arm_per_gpu() -> None:
    manifest_set = _read(WORKLOAD_SET_PATH)
    assert manifest_set["arm_count"] == 5
    assert manifest_set["common_program_count"] == 5
    assert manifest_set["expected_program_arm_runs"] == 25
    assert manifest_set["expected_physical_program_view_paths"] == 35
    assert manifest_set["all_arms_required_for_completion"] is True

    for index, arm_id in enumerate(("ARM-02", "ARM-03", "ARM-04", "ARM-05")):
        job = _read(JOB_ROOT / f"{arm_id}.json")
        assert job["execution"]["cuda_visible_devices"] == str(index)
        assert job["execution"]["visible_gpu_count_required"] == 1
        assert len(job["program_set"]["programs"]) == 5
        assert job["protocol"]["query_count"] == 150
        assert job["protocol"]["harness_dev_reserved_count"] == 100
        assert job["protocol"]["top_k"] == 100
        assert job["measured_retrieval_allowed"] is False
        assert job["launch_allowed"] is False

    arm01 = _read(JOB_ROOT / "ARM-01.json")
    assert arm01["execution"]["location"] == "owner_local"
    assert arm01["execution"]["device"] == "cpu"
    assert arm01["execution"]["visible_gpu_count_required"] == 0

    qwen = _read(JOB_ROOT / "ARM-05.json")
    assert qwen["adapter_execution_envelope"]["precision"] == "fp16"
    assert qwen["adapter_execution_envelope"]["batch_size"] == 1
    assert qwen["adapter_execution_envelope"]["maximum_input_tokens"] == 32768
    assert qwen["adapter_execution_envelope"]["qwen_v9_scope_binding"]["scope"] == (
        "single_rtx3090_fp16_batch_one_32768_tokens"
    )


def test_v11_adds_scientific_transfer_without_reinterpreting_v5_or_v6() -> None:
    transfer = _read(TRANSFER_PATH)
    preserved = {
        item["uri"]: item["file_sha256"]
        for item in transfer["additive_to_preserved_contracts"]
    }

    assert preserved["control/armindex/a1.2/topology-contract.direct-base.v5.json"] == (
        "e36f28b6fceea0d1e25518d49b37afc808af76afeba0010767f068b7bb2f684e"
    )
    assert preserved["control/armindex/a1.2/safe-export-allowlist.v6.json"] == (
        "f8bc1e7ef07c6e10716e81df2b373bff4620d968572584266124c9137487f201"
    )
    assert transfer["remote_stage_manifest"]["reject_unlisted_artifacts"] is True
    assert transfer["opaque_token_contract"]["original_identifier_allowed"] is False
    assert transfer["safe_return_contract"]["unknown_duplicate_or_missing_opaque_token_allowed"] is False
    assert transfer["cleanup_receipt"]["provider_destruction_proven_must_equal"] is False
    assert transfer["launch_allowed"] is False


def test_v11_common_program_set_binds_executable_specs_and_compiler() -> None:
    program_set = _read(PROGRAM_SET_PATH)
    programs = {item["program_key"]: item for item in program_set["programs"]}

    assert set(programs) == {
        "P00-TAC-DOC",
        "P01-TA-DOC",
        "P02-CLAIM1",
        "P03-PASSAGE",
        "P04-SECTION-MULTIVIEW",
    }
    assert programs["P02-CLAIM1"]["unitization"]["fallback"] == "forbidden"
    assert programs["P03-PASSAGE"]["unitization"]["window_tokens"] == 384
    assert programs["P03-PASSAGE"]["execution_boundary"]["silent_truncation_allowed"] is False
    assert programs["P04-SECTION-MULTIVIEW"]["family_aggregation"] == {
        "kind": "view_rrf",
        "per_view_depth": 100,
        "rrf_k": 60,
        "tie_break": "opaque_family_token_lexical",
    }
    assert program_set["physical_program_view_paths"] == 35
    assert len(program_set["compiler_contract"]["source_files"]) == 2
    assert program_set["per_arm_compilation_manifest"]["required_program_arm_bindings"] == 25


def test_v11_result_contract_requires_all_25_aggregate_safe_receipts() -> None:
    contract = _read(RESULT_CONTRACT_PATH)
    schema = _read(RESULT_SCHEMA_PATH)

    assert contract["completion"]["required_program_arm_receipts"] == 25
    assert contract["completion"]["partial_completion_promotable"] is False
    assert contract["completion"]["twenty_four_of_twenty_five_status"] == (
        "FAILED_INCOMPLETE_COMMON_SCREEN"
    )
    assert "recall_at_100_out" in contract["required_aggregate_metrics"]["quality"]
    assert "unique_relevant_family_query_pairs" in contract["required_aggregate_metrics"]["quality"]
    assert schema["properties"]["completion"]["properties"]["rep_dev_query_count"] == {
        "const": 150
    }


def test_v11_provider_plan_requires_fresh_identity_and_never_reuses_v9_quote() -> None:
    provider = _read(PROVIDER_PATH)

    assert provider["destroyed_predecessor_instance_reusable"] is False
    assert provider["historical_v9_identity_or_quote_admissible"] is False
    assert provider["requested_topology"]["gpu_count"] == 4
    assert provider["requested_topology"]["gpu_model_exact"] == "NVIDIA GeForce RTX 3090"
    assert provider["runtime_identity"]["torch"] == "2.6.0+cu118"
    assert provider["runtime_identity"]["cuda"] == "11.8"
    assert provider["termination"]["ttl_seconds"] == 21600
    assert provider["provider_contacted"] is False
    assert provider["gpu_reserved"] is False


def test_v11_stop_conditions_cover_integrity_budget_runtime_and_safe_return() -> None:
    stops = _read(STOP_PATH)
    text = json.dumps(stops, sort_keys=True)

    for required in (
        "v1_v10_or_operational_binding_mismatch",
        "fresh_quote_missing_stale_or_over_any_hard_stop",
        "owner_local_handoff_receipt_missing_or_mismatched",
        "image_platform_python_torch_cuda_or_gpu_identity_mismatch",
        "heartbeat_stale_over_300_seconds",
        "safe_export_or_local_return_hash_validation_failure",
    ):
        assert required in text
    assert stops["scientific_fail_closed_rules"]["partial_arm_screen_can_complete"] is False
    assert stops["scientific_fail_closed_rules"]["selection_or_final_fallback_allowed"] is False


def test_v11_rejects_rehashed_semantic_authorization_tampering() -> None:
    request = _read(REQUEST_PATH)
    tampered = copy.deepcopy(request)
    tampered["authorization"]["launch_allowed"] = True
    tampered["request_sha256"] = canonical_sha256(
        {key: value for key, value in tampered.items() if key != "request_sha256"}
    )

    with pytest.raises(ValueError, match="schema failure"):
        _validate_schema(tampered, REQUEST_SCHEMA_PATH, ROOT)
    with pytest.raises(ValueError, match="secret-like"):
        unsafe = copy.deepcopy(request)
        unsafe["next_authorized_action"] = "Bearer abcdefghijklmnopqrstuvwxyz"
        _validate_safe(unsafe)


def test_v11_ledger_is_hash_chained_and_append_only() -> None:
    result = _validate_ledger(ROOT)
    assert result["entry_count"] >= 3
    assert len(result["head_sha256"]) == 64
