from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from myis_research.armindex.constants import (
    A0_8_NEXT_AUTHORIZED_ACTION,
    A0_9_NEXT_AUTHORIZED_ACTION,
    A1_1_NEXT_AUTHORIZED_ACTION,
    A1_2_NEXT_AUTHORIZED_ACTION,
    A1_LONG_RUN_NEXT_AUTHORIZED_ACTION,
)
from myis_research.kernel.canonical import canonical_sha256
from myis_research.kernel.manifest import build_manifest
from myis_research.kernel.manifest_validation import (
    build_validation_report,
    capture_git_state,
)
from myis_research.owner_local import build_receipt
from myis_research.projections import read_model as read_model_module
from myis_research.projections.read_model import (
    A010_LEGACY_CODE_HARVEST_LEDGER_PATH,
    A010_LEGACY_CODE_HARVEST_RECEIPT_PATH,
    A010_OUTPUT_ROOT_RELOCATION_RECEIPT_PATH,
    A010_REPOSITORY_HYGIENE_AUDIT_PATH,
    A010_SOURCE_VERIFICATION_RECEIPT_PATH,
    _a010_legacy_code_harvest_projection,
    _a08_compute_storage_feasibility_projection,
    _a09_phase_closeout_projection,
    _a11_adapter_fixture_projection,
    _a12_contract_scaffold_projection,
    _legacy_file_commitment_matches,
    build_read_model,
    write_read_model,
)
from myis_research.report_cli import validate_read_model

ROOT = Path(__file__).resolve().parents[1]


def test_empty_campaign_read_model_is_safe(tmp_path: Path) -> None:
    (tmp_path / "control" / "campaigns").mkdir(parents=True)
    (tmp_path / "control" / "decisions").mkdir(parents=True)
    (tmp_path / "control" / "campaigns" / "scope-autoindex-v1.yaml").write_text("campaign:\n  status: preparation\n", encoding="utf-8")
    (tmp_path / "control" / "decisions" / "ledger.jsonl").write_text("", encoding="utf-8")
    model = build_read_model(tmp_path)
    assert model["schema_version"] == "myis.read-model.v2"
    assert model["publication_readiness"]["status"] == "blocked"
    output = write_read_model(tmp_path)
    assert json.loads(output.read_text(encoding="utf-8"))["projection_revision"] == model["projection_revision"]


def test_a1_terminal_pass_unlocks_a2_planning(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        read_model_module,
        "_a12_current_attempt_projection",
        lambda _root: {
            "validated": True,
            "status": "PASS",
            "next_authorized_action": "A1_CLOSEOUT_COMPLETE_STOP_BEFORE_A2",
        },
    )

    model = build_read_model(ROOT)
    phases = {
        phase["phase_id"]: phase for phase in model["armindex"]["phases"]
    }

    assert phases["A1_BASELINES_AND_MULTI_ARM_SCREENING"]["status"] == "complete"
    assert phases["A2_PER_ARM_AUTOINDEX"]["status"] == "planned"
    assert model["armindex"]["next_command"] == "A1_CLOSEOUT_COMPLETE_STOP_BEFORE_A2"
    retention = model["armindex"]["a1_2_remote_retention"]
    assert retention["validated"] is True
    assert retention["status"] == "PASS"
    assert retention["packages"]["a1_baseline"]["remote_total_file_count"] == 29
    assert retention["packages"]["a1_journal_eda"]["remote_total_file_count"] == 8
    assert retention["packages"]["a1_closeout"]["remote_total_file_count"] == 12


def test_read_model_revision_ignores_postcommit_validation_git_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_validator = read_model_module.validate_a1_2_vast_postcommit
    identities = iter((("a" * 40, "b" * 40), ("c" * 40, "d" * 40)))

    def validator_with_changed_git_identity(
        repository_root: Path,
        *,
        require_clean: bool = True,
    ) -> dict[str, object]:
        result = original_validator(repository_root, require_clean=False)
        commit, tree = next(identities)
        return {**result, "git_commit": commit, "git_tree": tree}

    monkeypatch.setattr(
        read_model_module,
        "validate_a1_2_vast_postcommit",
        validator_with_changed_git_identity,
    )
    first = build_read_model(ROOT)
    second = build_read_model(ROOT)

    assert first["read_model_revision"] == second["read_model_revision"]
    assert first["read_model_sha256"] == second["read_model_sha256"]
    for model in (first, second):
        vast_v3 = model["armindex"]["a1_2_contract_scaffold"]["vast_preflight_v3"]
        assert "validation_git_commit" not in vast_v3
        assert "validation_git_tree" not in vast_v3


def test_read_model_validation_rejects_unknown_field_and_non_object(tmp_path: Path) -> None:
    (tmp_path / "control" / "campaigns").mkdir(parents=True)
    (tmp_path / "control" / "decisions").mkdir(parents=True)
    (tmp_path / "control" / "campaigns" / "scope-autoindex-v1.yaml").write_text("campaign: {}\n", encoding="utf-8")
    (tmp_path / "control" / "decisions" / "ledger.jsonl").write_text("", encoding="utf-8")
    model = build_read_model(tmp_path)
    with pytest.raises(ValueError, match="schema validation failed"):
        validate_read_model({**model, "source_path": "protected"})
    with pytest.raises(ValueError, match="JSON object"):
        validate_read_model([])  # type: ignore[arg-type]


def _write_a010_harvest_pair(tmp_path: Path) -> tuple[Path, Path]:
    ledger_path = tmp_path / A010_LEGACY_CODE_HARVEST_LEDGER_PATH
    receipt_path = tmp_path / A010_LEGACY_CODE_HARVEST_RECEIPT_PATH
    ledger_path.parent.mkdir(parents=True)
    receipt_path.parent.mkdir(parents=True)
    ledger = {
        "schema_version": "myis.armindex-legacy-code-harvest-ledger.v1",
        "ledger_id": "a0.10-fixture",
        "source_repositories": [{
            "repository": "ThaiPha-Lex",
            "remote": "https://github.com/siriponsri/thaipha-lex.git",
            "commit": "a" * 40,
            "tree": "b" * 40,
        }],
        "components": [],
    }
    ledger["ledger_sha256"] = canonical_sha256(ledger)
    ledger_path.write_text(json.dumps(ledger, sort_keys=True), encoding="utf-8")
    ledger_sha256 = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
    supporting = (
        (
            A010_REPOSITORY_HYGIENE_AUDIT_PATH,
            "myis.repository-hygiene-audit.v1",
            "audit_sha256",
        ),
        (
            A010_OUTPUT_ROOT_RELOCATION_RECEIPT_PATH,
            "myis.output-root-relocation.v1",
            "receipt_sha256",
        ),
        (
            A010_SOURCE_VERIFICATION_RECEIPT_PATH,
            "myis.source-verification-receipt.v1",
            "receipt_sha256",
        ),
    )
    supporting_hashes: dict[Path, str] = {}
    for relative, schema_version, self_hash_key in supporting:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": schema_version,
            "status": "PASS",
            "scientific_authority": False,
        }
        if relative == A010_SOURCE_VERIFICATION_RECEIPT_PATH:
            payload.update({
                "source_remote": "https://github.com/siriponsri/thaipha-lex.git",
                "source_commit": "a" * 40,
                "source_tree": "b" * 40,
                "verified_from_git_object_database": True,
                "verified_component_count": 0,
                "components": [],
            })
        payload[self_hash_key] = canonical_sha256(payload)
        path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        supporting_hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    receipt = {
        "schema_version": "myis.armindex-legacy-code-harvest-receipt.v1",
        "receipt_id": "a0.10-fixture",
        "campaign_id": "armindex-multiretriever-v2",
        "phase_id": "A0_MIGRATION_FOUNDATION",
        "task_id": "A0.10",
        "status": "in_progress",
        "ledger_uri": A010_LEGACY_CODE_HARVEST_LEDGER_PATH.as_posix(),
        "ledger_sha256": ledger_sha256,
        "scientific_authority": False,
        "protected_data_accessed": False,
        "measured_execution_performed": False,
        "counters": {"measured_runs": 0, "selection_accesses": 0, "final_accesses": 0},
        "components": {"reviewed": 2, "adopted": 1, "rejected": 1},
        "fixture_status": "not_started",
        "fixture_receipt_uri": None,
        "fixture_receipt_sha256": None,
        "repository_hygiene_audit_uri": A010_REPOSITORY_HYGIENE_AUDIT_PATH.as_posix(),
        "repository_hygiene_audit_sha256": supporting_hashes[A010_REPOSITORY_HYGIENE_AUDIT_PATH],
        "output_root_relocation_receipt_uri": A010_OUTPUT_ROOT_RELOCATION_RECEIPT_PATH.as_posix(),
        "output_root_relocation_receipt_sha256": supporting_hashes[A010_OUTPUT_ROOT_RELOCATION_RECEIPT_PATH],
        "source_verification_receipt_uri": A010_SOURCE_VERIFICATION_RECEIPT_PATH.as_posix(),
        "source_verification_receipt_sha256": supporting_hashes[A010_SOURCE_VERIFICATION_RECEIPT_PATH],
        "next_authorized_action": A0_8_NEXT_AUTHORIZED_ACTION,
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    receipt_path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
    return ledger_path, receipt_path


def test_a010_harvest_projection_is_receipt_first_and_fails_closed(tmp_path: Path) -> None:
    assert _a010_legacy_code_harvest_projection(tmp_path)["status"] == "not_started"
    _, receipt_path = _write_a010_harvest_pair(tmp_path)
    projection = _a010_legacy_code_harvest_projection(tmp_path)
    assert projection["validated"] is True
    assert projection["components_reviewed"] == 2
    assert projection["components_adopted"] == 1
    assert projection["repository_hygiene_audit_sha256"] is not None
    assert projection["output_root_relocation_receipt_sha256"] is not None
    assert projection["source_verification_receipt_sha256"] is not None
    assert projection["measured_runs"] == 0

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["counters"]["measured_runs"] = 1
    receipt_path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
    assert _a010_legacy_code_harvest_projection(tmp_path)["status"] == "invalid"


def test_a08_feasibility_projection_is_receipt_bound_and_zero_counter() -> None:
    projection = _a08_compute_storage_feasibility_projection(ROOT)

    assert projection["status"] == "complete"
    assert projection["validated"] is True
    assert projection["fixture_status"] == "passed"
    assert len(projection["profiles"]) == 3
    assert len(projection["observations"]) == 3
    assert projection["measured_runs"] == 0
    assert projection["selection_accesses"] == 0
    assert projection["final_accesses"] == 0
    assert projection["next_authorized_action"] == A0_9_NEXT_AUTHORIZED_ACTION


def test_a09_phase_closeout_projection_closes_every_a0_task_and_stays_zero() -> None:
    projection = _a09_phase_closeout_projection(ROOT)

    assert projection["status"] == "complete"
    assert projection["validated"] is True
    assert projection["completed_task_count"] == 10
    assert projection["validation_check_count"] == 15
    assert projection["measured_runs"] == 0
    assert projection["candidate_count"] == 0
    assert projection["selection_accesses"] == 0
    assert projection["final_accesses"] == 0
    assert projection["next_authorized_action"] == A1_1_NEXT_AUTHORIZED_ACTION

    model = build_read_model(ROOT)
    assert model["armindex"]["current_phase"] == "A1_BASELINES_AND_MULTI_ARM_SCREENING"
    current_attempt = model["armindex"]["a1_2_current_attempt"]
    if current_attempt["validated"] is True:
        assert model["armindex"]["next_command"] == current_attempt[
            "next_authorized_action"
        ]
    elif (
        model["armindex"]["local_adoption_input_status"]
        == "LOCAL_ADOPTION_INPUTS_VALIDATED_PENDING_LIVE_PROVIDER"
    ):
        assert model["armindex"]["next_command"] == A1_LONG_RUN_NEXT_AUTHORIZED_ACTION
    else:
        assert model["armindex"]["next_command"] == model["armindex"][
            "a1_2_dense_overflow"
        ]["next_authorized_action"]
    assert model["armindex"]["local_adoption_input_status"] in {
        "PASS_PROTECTED_COMPILER_INTEGRATION_LOCAL_ONLY",
        "LOCAL_ADOPTION_INPUTS_VALIDATED_PENDING_LIVE_PROVIDER",
        "REQUIRES_FRESH_A1_ADMISSION_AND_COMPLETE_RETRY",
        "A1_COMPLETE_25_OF_25",
    }


def test_a11_adapter_fixture_projection_closes_cpu_scaffold_and_keeps_gpu_locked() -> None:
    projection = _a11_adapter_fixture_projection(ROOT)

    assert projection["status"] == "complete"
    assert projection["validated"] is True
    assert projection["fixture_status"] == "passed"
    assert projection["registered_arms"] == 5
    assert projection["runnable_cpu_arms"] == 1
    assert projection["dense_arms_blocked"] == 4
    assert projection["gpu_proposal_status"] == "proposal_not_adopted_execution_locked"
    assert projection["gpu_spec"]["minimum_vram_gib"] == 24
    assert projection["time_estimate"]["end_to_end_elapsed_hours_max"] == 20
    assert projection["budget_estimate"]["a1_total_hard_stop"] == 23
    assert projection["report_contract"]["language"] == "en"
    assert projection["report_contract"]["required_registered_phase_reports"] == 12
    assert projection["report_contract"]["required_registered_task_reports"] == 27
    assert projection["measured_runs"] == 0
    assert projection["selection_accesses"] == 0
    assert projection["final_accesses"] == 0
    assert set(projection["resource_counters"].values()) == {0}
    assert projection["next_authorized_action"] == A1_2_NEXT_AUTHORIZED_ACTION


def test_a12_contract_scaffold_projection_is_complete_and_launch_locked() -> None:
    projection = _a12_contract_scaffold_projection(ROOT)

    assert projection["status"] == (
        "a1_2_scientific_execution_adoption_request_prepared_owner_review_launch_locked"
    )
    assert projection["validated"] is True
    assert projection["v1_status"] == "a1_2_contract_scaffold_complete_launch_locked"
    assert projection["evidence_class"] == (
        "scientific_execution_adoption_request_preparation"
    )
    assert projection["scientific_authority"] is False
    assert projection["model_lock_count"] == 5
    assert projection["offline_adapter_ready"] == 1
    assert projection["dense_artifact_manifests_pending"] == 4
    assert projection["owner_requirements_pending"] == len(
        projection["scientific_execution_request_v11"][
            "pending_adoption_requirements"
        ]
    )
    assert projection["launch_ready"] is False
    assert projection["measured_execution"] is False
    assert projection["budget_limits"]["arm01_gpu_usd"] == 0
    assert projection["budget_limits"]["a1_total_hard_stop_usd"] == 23
    assert projection["archive_disposition"]["candidate_count"] == 0
    assert projection["closeout_validation_check_count"] == 17
    assert projection["closeout_validation_recovery_count"] == 7
    assert len(projection["closeout_validation_recoveries"]) == 7
    assert projection["closeout_validation_audit_sha256"]
    assert set(projection["real_counters"].values()) == {0}
    assert set(projection["resource_counters"].values()) == {0}
    assert projection["next_authorized_action"] == projection[
        "scientific_execution_request_v11"
    ]["next_authorized_action"]
    vast = projection["vast_preflight_v2"]
    assert vast["validated"] is True
    assert vast["gpu_count"] == 4
    assert vast["gpu_model"] == "NVIDIA GeForce RTX 3090"
    assert vast["synthetic_worker_count"] == 4
    assert vast["planning_rate_usd"] == 0.6
    assert vast["estimated_instance_hours_min"] == 2
    assert vast["estimated_instance_hours_max"] == 4
    assert vast["estimated_raw_worker_usd_min"] == 1.2
    assert vast["estimated_raw_worker_usd_max"] == 2.4
    assert vast["launch_allowed"] is False
    assert vast["adopted_for_execution"] is False
    assert len(vast["jobs"]) == 4
    assert vast["closeout_validation_check_count"] == 18
    assert vast["closeout_validation_recovery_count"] == 2
    assert vast["closeout_validation_audit_sha256"]
    assert set(vast["real_counters"].values()) == {0}
    assert set(vast["resource_counters"].values()) == {0}
    vast_v3 = projection["vast_preflight_v3"]
    assert vast_v3["validated"] is True
    assert vast_v3["status"] == (
        "postcommit_validator_prepared_live_owner_preflight_pending"
    )
    assert vast_v3["v2_receipt_sha256"] == vast["receipt_self_sha256"]
    assert len(vast_v3["receipt_self_sha256"]) == 64
    assert vast_v3["planning_rate_usd"] == 0.6
    assert vast_v3["estimated_instance_hours"] == "2-4"
    assert vast_v3["estimated_raw_worker_usd"] == "1.20-2.40"
    assert vast_v3["common_screen_hard_stop_usd"] == 18
    assert vast_v3["a1_hard_stop_usd"] == 23
    assert vast_v3["campaign_hard_stop_usd"] == 100
    assert vast_v3["launch_allowed"] is False
    assert vast_v3["adopted_for_execution"] is False
    assert set(vast_v3["real_counters"].values()) == {0}
    assert set(vast_v3["resource_counters"].values()) == {0}
    vast_v5 = projection["vast_preflight_v5"]
    assert vast_v5["validated"] is True
    assert vast_v5["image_reference"] == "pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime"
    assert vast_v5["resolved_manifest_digest"] == "sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20"
    assert vast_v5["platform"] == "linux/amd64"
    assert vast_v5["custom_local_docker_build"] is False
    assert vast_v5["launch_allowed"] is False
    assert vast_v5["adopted_for_execution"] is False
    assert set(vast_v5["real_counters"].values()) == {0}
    assert set(vast_v5["resource_counters"].values()) == {0}
    vast_v6 = projection["vast_preflight_v6"]
    assert vast_v6["validated"] is True
    assert vast_v6["status"] == "live_correction_prepared_preflight_pending"
    assert vast_v6["image_reference"] == "pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime"
    assert vast_v6["resolved_manifest_digest"] == "sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20"
    assert vast_v6["live_quote_usd_per_hour"] == 0.656
    assert vast_v6["launch_allowed"] is False
    assert vast_v6["adopted_for_execution"] is False
    assert vast_v6["synthetic_preflight_only"] is True
    assert vast_v6["continuation_policy"]["validated"] is True
    assert vast_v6["continuation_policy"]["continuation_authorized_now"] is False
    assert vast_v6["continuation_policy"]["default_post_preflight_instruction"] == (
        "destroy_and_verify_provider_instance_absent"
    )
    assert vast_v6["continuation_policy"]["allowed_post_preflight_instruction"] == (
        "continue_next_goal_on_PLAN"
    )
    assert set(vast_v6["real_counters"].values()) == {0}
    assert set(vast_v6["resource_counters"].values()) == {0}
    vast_v7 = projection["vast_preflight_v7"]
    assert vast_v7["validated"] is True
    assert vast_v7["status"] == "same_instance_repair_prepared_preflight_pending"
    assert vast_v7["image_reference"] == "pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime"
    assert vast_v7["resolved_manifest_digest"] == "sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20"
    assert vast_v7["launch_allowed"] is False
    assert vast_v7["adopted_for_execution"] is False
    assert vast_v7["synthetic_preflight_only"] is True
    assert vast_v7["active_correction"]["fresh_remote_root_required"] is True
    assert vast_v7["active_correction"]["pythondontwritebytecode"] is True
    assert [item["failure_id"] for item in vast_v7["preserved_live_failures"]] == [
        "v6-initial-wheelhouse-missing-pydantic",
        "v6-supplement-repair-mutated-pycache-tree",
    ]
    assert vast_v7["continuation_policy"]["validated"] is True
    assert vast_v7["continuation_policy"]["continuation_authorized_now"] is False
    assert set(vast_v7["real_counters"].values()) == {0}
    assert set(vast_v7["resource_counters"].values()) == {0}
    vast_v8 = projection["vast_preflight_v8"]
    assert vast_v8["validated"] is True
    assert vast_v8["status"] == "validation_complete_bundle_repair_prepared_preflight_pending"
    assert vast_v8["image_reference"] == "pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime"
    assert vast_v8["resolved_manifest_digest"] == "sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20"
    assert vast_v8["launch_allowed"] is False
    assert vast_v8["adopted_for_execution"] is False
    assert vast_v8["synthetic_preflight_only"] is True
    assert [item["failure_id"] for item in vast_v8["preserved_live_failures"]] == [
        "v6-initial-wheelhouse-missing-pydantic",
        "v6-supplement-repair-mutated-pycache-tree",
        "v7-frozen-bundle-missing-validation-lineage",
    ]
    assert vast_v8["active_correction"]["validation_lineage_complete"] is True
    assert vast_v8["active_correction"]["fresh_remote_root"] == "/opt/myis/a1.2-v8"
    assert set(vast_v8["real_counters"].values()) == {0}
    assert set(vast_v8["resource_counters"].values()) == {0}
    vast_v9 = projection["vast_preflight_v9"]
    assert vast_v9["validated"] is True
    assert vast_v9["status"] == "execution_lifecycle_repair_prepared_preflight_pending"
    assert vast_v9["launch_allowed"] is False
    assert vast_v9["adopted_for_execution"] is False
    assert vast_v9["synthetic_preflight_only"] is True
    assert vast_v9["active_correction"]["fresh_remote_root"] == "/opt/myis/a1.2-v9"
    assert vast_v9["active_correction"]["source_remote_root"] == "/opt/myis/a1.2-v7"
    assert vast_v9["active_correction"]["implementation_validation_complete"] is True
    assert vast_v9["active_correction"]["live_preflight_execution_pending"] is True
    assert vast_v9["live_result_status"] == "PASS"
    assert vast_v9["live_result"]["attempt_id"] == "a12-v9-20260807-06"
    assert len(vast_v9["live_result"]["arms"]) == 4
    assert {item["status"] for item in vast_v9["live_result"]["arms"]} == {"PASS"}
    assert vast_v9["live_result"]["qwen"]["measured_adapter_max_input_tokens"] == 32768
    assert vast_v9["live_result"]["lifecycle"]["checkpoint_resume"] == "PASS"
    assert vast_v9["live_result"]["lifecycle"]["guest_process_teardown"] == "PASS"
    assert vast_v9["live_result"]["lifecycle"]["provider_destruction_proven"] is False
    assert set(vast_v9["real_counters"].values()) == {0}
    assert set(vast_v9["resource_counters"].values()) == {0}
    closeout_v10 = projection["provider_closeout_v10"]
    assert closeout_v10["validated"] is True
    assert closeout_v10["status"] == "PASS"
    assert closeout_v10["predecessor"]["receipt_self_sha256"] == (
        vast_v9["live_result_self_sha256"]
    )
    assert closeout_v10["provider_closeout"]["owner_disposition"] == (
        "destroyed_and_provider_absence_verified"
    )
    assert closeout_v10["provider_closeout"]["provider_destruction_proven"] is True
    assert closeout_v10["provider_closeout"]["provider_instance_absent_verified"] is True
    assert closeout_v10["provider_closeout"]["provider_api_query_performed"] is False
    assert closeout_v10["pending_provider_checks"] == []
    assert closeout_v10["launch_allowed"] is False
    assert closeout_v10["adopted_for_execution"] is False
    assert closeout_v10["measured_runs"] == 0
    assert closeout_v10["selection_accesses"] == 0
    assert closeout_v10["final_accesses"] == 0
    assert closeout_v10["charged_usd"] == 0
    request_v11 = projection["scientific_execution_request_v11"]
    assert request_v11["validated"] is True
    assert request_v11["status"] == "PASS"
    assert request_v11["workload_manifests"] == 5
    assert request_v11["expected_program_arm_runs"] == 25
    assert request_v11["expected_physical_program_view_paths"] == 35
    assert request_v11["rep_dev_query_count"] == 150
    assert request_v11["harness_dev_reserved_count"] == 100
    assert request_v11["launch_allowed"] is False
    assert request_v11["adopted_for_execution"] is False
    assert set(request_v11["authorization"].values()) == {False}
    assert set(request_v11["counters"].values()) == {0}
    assert len(request_v11["jobs"]) == 5


def _p1_request(repository_root: Path, request_id: str = "p1-projection-test") -> dict[str, object]:
    return {
        "schema_version": "myis.owner-local-request.v2",
        "request_id": request_id,
        "decision_id": "P1_CPU_EXECUTION_ENVELOPE",
        "phase_id": "P1_CPU_BASELINE",
        "stage": "train_selection",
        "scope": {"campaign": "a" * 64, "source_contract_sha256": "b" * 64},
        "git_commit": capture_git_state(repository_root)["commit"],
        "input_hashes": {"dataset": "c" * 64},
    }


def _p1_receipt(
    repository_root: Path,
    *,
    request_id: str = "p1-projection-test",
    value: float = 0.5,
) -> tuple[dict[str, object], dict[str, object]]:
    request = _p1_request(repository_root, request_id)
    metrics = [
        {
            "arm": arm,
            "name": "recall_at_100",
            "value": value,
            "n": 2,
            "retrieved_relevant": 1,
            "relevant_total": 2,
            "scope": scope,
            "split": split,
            "direction": "maximize",
            "denominator": "macro_mean_per_query_relevant_families",
            "evidence_role": "primary" if scope == "OUT" else "secondary",
        }
        for arm in ("R0", "R0-W")
        for split in ("train", "selection")
        for scope in ("ALL", "IN", "OUT")
    ]
    return request, build_receipt(
        request,
        aggregate_counts={"documents": 2, "train_queries": 2, "selection_queries": 2},
        aggregate_hashes={f"{arm.lower()}_{split}_metrics": "d" * 64 for arm in ("R0", "R0-W") for split in ("train", "selection")},
        metrics=metrics,
        cost_usd=0.0,
        latency_seconds=0.1,
        lineage_hashes={key: "e" * 64 for key in ("dataset_sha256", "corpus_sha256", "query_sha256", "qrels_sha256", "split_sha256", "index_sha256", "evaluator_sha256")},
    )


def _write_p1_campaign(tmp_path: Path, receipt: dict[str, object]) -> Path:
    evidence_dir = tmp_path / "campaigns" / "scope-autoindex-v1" / "evidence"
    evidence_dir.mkdir(parents=True)
    receipt_path = evidence_dir / "p1-receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    (tmp_path / "control" / "campaigns").mkdir(parents=True)
    (tmp_path / "control" / "decisions").mkdir(parents=True)
    (tmp_path / "control" / "campaigns" / "scope-autoindex-v1.yaml").write_text(
        "phases:\n  - id: P1_CPU_BASELINE\n    status: measured\n    tasks:\n      - id: P1.1\n        title: fixture\n        status: measured\n",
        encoding="utf-8",
    )
    (tmp_path / "control" / "decisions" / "ledger.jsonl").write_text("", encoding="utf-8")
    return receipt_path


def _write_p1_manifest(
    tmp_path: Path,
    repository_root: Path,
    request: dict[str, object],
    receipt: dict[str, object],
    *,
    arm: str,
    split: str,
    status: str = "valid",
    metrics: list[dict[str, object]] | None = None,
    run_suffix: str = "",
    write_validation: bool = True,
) -> Path:
    manifest_dir = tmp_path / "campaigns" / "scope-autoindex-v1" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(
        run_id=f"p1-{arm.lower()}-{split}-{status}{run_suffix}",
        parent_run_id="p1-projection-parent",
        experiment_id="myis-research-track-c",
        campaign_id="scope-autoindex-v1",
        stage=split,
        status=status,
        source={"dataset": "dapfam"},
        data={"split": split},
        method={"arm_id": arm, "top_k": 100},
        resources={"cost_usd": 0.0},
        metrics=metrics or [row for row in receipt["metrics"] if row["arm"] == arm and row["split"] == split],
        artifacts=[],
        evidence_class="train_selection_measured",
        repository_root=repository_root,
        owner_local_request=request,
        owner_local_receipt=receipt,
    )
    path = manifest_dir / f"{arm.lower()}-{split}-{status}{run_suffix}.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    if write_validation:
        _write_validation_report(tmp_path, path, request, receipt)
    return path


def _write_validation_report(
    tmp_path: Path,
    manifest_path: Path,
    request: dict[str, object],
    receipt: dict[str, object],
) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = build_validation_report(
        manifest,
        owner_local_request=request,
        owner_local_receipt=receipt,
    )
    report_dir = tmp_path / "campaigns" / "scope-autoindex-v1" / "validation-reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / manifest_path.name).write_text(json.dumps(report), encoding="utf-8")


def _write_p1_matrix(tmp_path: Path, repository_root: Path, request: dict[str, object], receipt: dict[str, object]) -> None:
    for arm in ("R0", "R0-W"):
        for split in ("train", "selection"):
            _write_p1_manifest(tmp_path, repository_root, request, receipt, arm=arm, split=split)


def _write_p1_package(
    tmp_path: Path,
    request: dict[str, object],
    receipt: dict[str, object],
) -> Path:
    request_dir = tmp_path / "campaigns/scope-autoindex-v1/requests"
    package_dir = tmp_path / "campaigns/scope-autoindex-v1/packages"
    request_dir.mkdir(parents=True, exist_ok=True)
    package_dir.mkdir(parents=True, exist_ok=True)
    request_path = request_dir / "p1-request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    receipt_path = tmp_path / "campaigns/scope-autoindex-v1/evidence/p1-receipt.json"
    slots = []
    for arm in ("R0", "R0-W"):
        for split in ("train", "selection"):
            stem = f"{arm.lower()}-{split}-valid"
            manifest_path = tmp_path / f"campaigns/scope-autoindex-v1/manifests/{stem}.json"
            report_path = tmp_path / f"campaigns/scope-autoindex-v1/validation-reports/{stem}.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            report = json.loads(report_path.read_text(encoding="utf-8"))
            slots.append({
                "arm": arm,
                "split": split,
                "run_id": manifest["run_id"],
                "manifest_uri": manifest_path.relative_to(tmp_path).as_posix(),
                "manifest_sha256": manifest["manifest_sha256"],
                "validation_report_uri": report_path.relative_to(tmp_path).as_posix(),
                "validation_report_sha256": report["validation_report_sha256"],
            })
    package = {
        "schema_version": "myis.p1-package.v1",
        "package_id": request["request_id"],
        "status": "validated_structural",
        "source_commit": request["git_commit"],
        "request_uri": request_path.relative_to(tmp_path).as_posix(),
        "request_sha256": canonical_sha256(request),
        "receipt_uri": receipt_path.relative_to(tmp_path).as_posix(),
        "receipt_sha256": receipt["receipt_sha256"],
        "source_contract_sha256": request["scope"]["source_contract_sha256"],
        "slots": slots,
    }
    package["package_sha256"] = canonical_sha256(package)
    package_path = package_dir / f"{request['request_id']}.package.json"
    package_path.write_text(json.dumps(package), encoding="utf-8")
    return package_path


def _write_p1_rigor_review(tmp_path: Path, package_path: Path) -> Path:
    package_id = package_path.name.removesuffix(".package.json")
    review_dir = tmp_path / "outputs/audits/rigor" / package_id
    review_dir.mkdir(parents=True, exist_ok=True)
    review = {
        "schema_version": "myis.rigor-review.v1",
        "review_status": "complete",
        "artifact_path": package_path.relative_to(tmp_path).as_posix(),
        "artifact_sha256": hashlib.sha256(package_path.read_bytes()).hexdigest(),
        "governance": {
            "approval_valid": True,
            "split_isolation_valid": True,
            "gate_order_valid": True,
            "budget_valid": True,
            "manifest_integrity_valid": True,
            "blocking_findings": [],
        },
        "findings": [],
    }
    path = review_dir / "rigor_review.json"
    path.write_text(json.dumps(review), encoding="utf-8")
    return path


def test_accepted_receipt_without_manifest_cannot_complete_p1(tmp_path: Path) -> None:
    _, receipt = _p1_receipt(Path(__file__).resolve().parents[1])
    _write_p1_campaign(tmp_path, receipt)
    model = build_read_model(tmp_path)
    assert model["campaigns"][0]["current_state"] == "P1_BLOCKED_WITH_EVIDENCE"
    assert model["phases"][0]["status"] == "blocked"
    assert model["metrics"] == []
    assert model["runs"] == []


def test_p1_requires_a_valid_non_invalidated_manifest_receipt_pair(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    request, receipt = _p1_receipt(repository_root)
    _write_p1_campaign(tmp_path, receipt)
    _write_p1_matrix(tmp_path, repository_root, request, receipt)
    model = build_read_model(tmp_path)
    assert model["campaigns"][0]["current_state"] == "P1_CPU_MEASURED_COMPLETE"
    assert len(model["metrics"]) == 12

    _write_p1_manifest(tmp_path, repository_root, request, receipt, arm="R0", split="train", status="superseded")
    invalidated = build_read_model(tmp_path)
    assert invalidated["campaigns"][0]["current_state"] == "P1_BLOCKED_WITH_EVIDENCE"
    assert invalidated["metrics"] == []


def test_p1_requires_validation_reports_for_all_four_slots(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    request, receipt = _p1_receipt(repository_root)
    _write_p1_campaign(tmp_path, receipt)
    paths = [
        _write_p1_manifest(
            tmp_path,
            repository_root,
            request,
            receipt,
            arm=arm,
            split=split,
            write_validation=False,
        )
        for arm in ("R0", "R0-W")
        for split in ("train", "selection")
    ]
    blocked = build_read_model(tmp_path)
    assert blocked["project"]["state"] == "P1_BLOCKED_WITH_EVIDENCE"
    assert blocked["runs"] == []
    assert blocked["metrics"] == []
    assert blocked["evidence"] == []

    for path in paths:
        _write_validation_report(tmp_path, path, request, receipt)
    promoted = build_read_model(tmp_path)
    assert promoted["project"]["state"] == "P1_CPU_MEASURED_COMPLETE"
    assert len(promoted["runs"]) == 4
    assert promoted["phases"][0]["tasks"][0]["evidence_ids"] == [request["request_id"]]
    assert len(promoted["metrics"]) == 12


def test_full_text_p1_requires_hash_bound_package_and_rigor_review(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    request, receipt = _p1_receipt(repository_root)
    _write_p1_campaign(tmp_path, receipt)
    _write_p1_matrix(tmp_path, repository_root, request, receipt)
    source_contract = tmp_path / "control/assets/dapfam-p1-source.v1.json"
    source_contract.parent.mkdir(parents=True)
    source_contract.write_text("{}", encoding="utf-8")

    assert build_read_model(tmp_path)["project"]["state"] == "P1_BLOCKED_WITH_EVIDENCE"
    package_path = _write_p1_package(tmp_path, request, receipt)
    assert build_read_model(tmp_path)["project"]["state"] == "P1_BLOCKED_WITH_EVIDENCE"
    _write_p1_rigor_review(tmp_path, package_path)
    promoted = build_read_model(tmp_path)
    assert promoted["project"]["state"] == "P1_CPU_MEASURED_COMPLETE"
    assert len(promoted["runs"]) == 4


def test_checked_in_legacy_receipt_is_hash_locked_and_never_promoted() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    receipt_path = repository_root / "campaigns/scope-autoindex-v1/evidence/legacy-p1-receipt.v2.json"
    disposition = json.loads(
        receipt_path.with_name(f"{receipt_path.stem}.disposition.json").read_text(encoding="utf-8")
    )
    assert disposition["source_file_sha256"] == "f83ae6b052334190eee08dda5ca1dde70930464d02f97f47d4ea18dc922d9766"
    model = build_read_model(repository_root)
    assert model["project"]["state"] == "P1_CPU_MEASURED_COMPLETE"
    assert len(model["runs"]) == 4
    assert len(model["metrics"]) == 12
    assert all(
        run["owner_local_receipt_sha256"] != disposition["receipt_sha256"]
        for run in model["runs"]
    )
    assert all(
        item.get("uri") != disposition["source_uri"]
        for item in model["evidence"]
    )
    assert len(model["mlflow_registration"]["children"]) == 4
    assert model["outputs"] == [{
        "output_id": "P1-LEGACY-RECEIPT",
        "phase_id": "P1_CPU_BASELINE",
        "task_id": "P1.3",
        "status": "historical_invalid_superseded",
        "evidence_class": "historical_invalid",
        "source_uri": "campaigns/scope-autoindex-v1/evidence/legacy-p1-receipt.v2.json",
        "source_sha256": "f83ae6b052334190eee08dda5ca1dde70930464d02f97f47d4ea18dc922d9766",
        "disposition_uri": "campaigns/scope-autoindex-v1/evidence/legacy-p1-receipt.v2.disposition.json",
        "promotable": False,
        "superseded_by": "fresh-owner-local-p1-rerun-pending",
    }]


def test_checked_in_p1_raw_hash_bindings_are_checkout_stable() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    source_path = repository_root / "control/assets/dapfam-p1-source.v1.json"
    package_path = repository_root / (
        "campaigns/scope-autoindex-v1/packages/"
        "dapfam-p1-fulltext-c058a3aa7357c782.package.json"
    )
    review_path = repository_root / (
        "outputs/audits/rigor/dapfam-p1-fulltext-c058a3aa7357c782/rigor_review.json"
    )
    registration_path = repository_root / "evidence/mlflow-p1-registration.v2.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    review = json.loads(review_path.read_text(encoding="utf-8"))
    read_model = build_read_model(repository_root)

    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == package["source_contract_sha256"]
    assert hashlib.sha256(package_path.read_bytes()).hexdigest() == review["artifact_sha256"]
    registration_evidence = next(
        item for item in read_model["evidence"] if item["evidence_id"] == "mlflow-p1-registration"
    )
    assert hashlib.sha256(registration_path.read_bytes()).hexdigest() == registration_evidence["sha256"]

    attributes = {
        line.strip()
        for line in (repository_root / ".gitattributes").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert {
        "control/assets/dapfam-p1-source.v1.json -text",
        "campaigns/scope-autoindex-v1/packages/*.json -text",
        "outputs/audits/rigor/**/*.json -text",
        "evidence/mlflow-p1-registration.v2.json -text",
    } <= attributes


def test_legacy_commitment_accepts_only_lf_crlf_checkout_variance(tmp_path: Path) -> None:
    path = tmp_path / "legacy.json"
    path.write_bytes(b'{"status":"historical-invalid"}\n')
    expected = hashlib.sha256(b'{"status":"historical-invalid"}\r\n').hexdigest()
    assert _legacy_file_commitment_matches(path, expected)
    assert not _legacy_file_commitment_matches(path, "0" * 64)


def test_manifest_metrics_must_match_the_paired_receipt(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    request, receipt = _p1_receipt(repository_root)
    _write_p1_campaign(tmp_path, receipt)
    _write_p1_matrix(tmp_path, repository_root, request, receipt)
    mismatched = [
        {**row, "value": 0.75}
        for row in receipt["metrics"]
        if row["arm"] == "R0" and row["split"] == "train"
    ]
    _write_p1_manifest(tmp_path, repository_root, request, receipt, arm="R0", split="train", metrics=mismatched)
    model = build_read_model(tmp_path)
    assert model["campaigns"][0]["current_state"] == "P1_BLOCKED_WITH_EVIDENCE"
    assert model["metrics"] == []


@pytest.mark.parametrize("invalid_metrics", [
    lambda receipt: [row for row in receipt["metrics"] if row["arm"] == "R0" and row["split"] == "train" and row["scope"] != "OUT"],
    lambda receipt: [row for row in receipt["metrics"] if row["arm"] == "R0" and row["split"] == "train"] + [receipt["metrics"][3]],
])
def test_p1_manifest_must_contain_exactly_its_three_scope_rows(tmp_path: Path, invalid_metrics) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    request, receipt = _p1_receipt(repository_root)
    _write_p1_campaign(tmp_path, receipt)
    _write_p1_matrix(tmp_path, repository_root, request, receipt)
    _write_p1_manifest(
        tmp_path,
        repository_root,
        request,
        receipt,
        arm="R0",
        split="train",
        metrics=invalid_metrics(receipt),
    )
    model = build_read_model(tmp_path)
    assert model["campaigns"][0]["current_state"] == "P1_BLOCKED_WITH_EVIDENCE"
    assert model["metrics"] == []


def test_p1_requires_all_four_arm_split_manifests(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    request, receipt = _p1_receipt(repository_root)
    _write_p1_campaign(tmp_path, receipt)
    _write_p1_manifest(tmp_path, repository_root, request, receipt, arm="R0", split="train")
    _write_p1_manifest(tmp_path, repository_root, request, receipt, arm="R0", split="selection")
    _write_p1_manifest(tmp_path, repository_root, request, receipt, arm="R0-W", split="train")
    model = build_read_model(tmp_path)
    assert model["campaigns"][0]["current_state"] == "P1_BLOCKED_WITH_EVIDENCE"


def test_p1_requires_one_receipt_and_one_manifest_per_slot(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    request, receipt = _p1_receipt(repository_root)
    alternative_request, alternative_receipt = _p1_receipt(
        repository_root,
        request_id="p1-projection-test-alt",
        value=0.6,
    )
    _write_p1_campaign(tmp_path, receipt)
    evidence_dir = tmp_path / "campaigns" / "scope-autoindex-v1" / "evidence"
    (evidence_dir / "p1-alternative-receipt.json").write_text(json.dumps(alternative_receipt), encoding="utf-8")
    _write_p1_matrix(tmp_path, repository_root, request, receipt)
    _write_p1_manifest(
        tmp_path,
        repository_root,
        alternative_request,
        alternative_receipt,
        arm="R0",
        split="train",
    )
    assert build_read_model(tmp_path)["campaigns"][0]["current_state"] == "P1_BLOCKED_WITH_EVIDENCE"

    _write_p1_manifest(
        tmp_path,
        repository_root,
        request,
        receipt,
        arm="R0",
        split="train",
        run_suffix="-duplicate",
    )
    assert build_read_model(tmp_path)["campaigns"][0]["current_state"] == "P1_BLOCKED_WITH_EVIDENCE"


def test_dataset_projection_exposes_logical_ids_without_source_paths(tmp_path: Path) -> None:
    (tmp_path / "control" / "campaigns").mkdir(parents=True)
    (tmp_path / "control" / "decisions").mkdir(parents=True)
    (tmp_path / "control" / "campaigns" / "scope-autoindex-v1.yaml").write_text("campaign: {}\n", encoding="utf-8")
    (tmp_path / "control" / "decisions" / "ledger.jsonl").write_text("", encoding="utf-8")
    inventory = {"assets": [{"path": "processed/dapfam/patents.jsonl", "bytes": 1, "sha256": "a" * 64}]}
    inventory_path = tmp_path / "evidence" / "legacy-dapfam-inventory.v1.json"
    inventory_path.parent.mkdir()
    inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
    datasets = build_read_model(tmp_path)["datasets"]
    assert datasets
    assert all("source_path" not in dataset for dataset in datasets)


def _registration_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "register_p1_mlflow.py"
    spec = importlib.util.spec_from_file_location("register_p1_mlflow_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mlflow_registration_requires_a_complete_validated_package(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    request, receipt = _p1_receipt(repository_root)
    _write_p1_campaign(tmp_path, receipt)
    _write_p1_matrix(tmp_path, repository_root, request, receipt)
    package_path = _write_p1_package(tmp_path, request, receipt)
    register_p1_mlflow = _registration_module()

    package, manifests, accepted_receipt = register_p1_mlflow.load_validated_p1_matrix(package_path, tmp_path)
    assert package["receipt_sha256"] == accepted_receipt["receipt_sha256"]
    assert len(manifests) == 4

    legacy_only = tmp_path / "legacy-only.json"
    legacy_only.write_text("{}", encoding="utf-8")
    with pytest.raises((ValueError, FileNotFoundError)):
        register_p1_mlflow.load_validated_p1_matrix(legacy_only, tmp_path)
