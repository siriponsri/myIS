from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from myis_research.armindex import a2_candidate_freeze as freeze
from myis_research.kernel.canonical import canonical_sha256, file_sha256

ROOT = Path(__file__).resolve().parents[1]
FREEZE = {
    "manifest_sha256": "f6276e3a15e760187152270418e00ce4cae4d8efe45b13edb02c4742e3b3049e",
    "freeze_receipt_sha256": "ea93db368c3e740f7914e07e2bdfc15052991f6f05976f6924acdce717392e10",
    "lock_sha256": "c01f683b909e6f4c6310c01855b3f79319a183b7950f91338d43baa8a2d57952",
}


def _json(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _valid(schema_name: str, payload: dict[str, object]) -> None:
    schema = _json(f"schemas/armindex/{schema_name}")
    assert not list(Draft202012Validator(schema).iter_errors(payload))


def test_a2_controls_bind_immutable_freeze_and_measurement_stays_locked() -> None:
    contract = _json("control/armindex/a2/execution-readiness-contract.v1.json")
    budget = _json("control/budgets/a2-execution-readiness-v1.json")

    assert contract["freeze_bindings"] == {
        **FREEZE,
        "manifest_uri": "campaigns/armindex-multiretriever-v2/manifests/a2-five-arm-candidate-manifest.v1.json",
        "manifest_file_sha256": "a49967760488971470169b97dd4a7638e045a72b6d20b119645eb0f9261f3133",
        "freeze_receipt_uri": "campaigns/armindex-multiretriever-v2/evidence/a2-five-arm-candidate-freeze.receipt.v1.json",
        "lock_uri": "control/armindex/a2/candidate-freeze.lock.v1.json",
    }
    assert {
        key: contract["candidate_design"][key]
        for key in (
            "arms", "primary_advancement_arms", "diagnostic_non_advancing_arms",
            "matched_candidate_count", "conditional_reserve_candidate_count", "candidate_count",
        )
    } == {
        "arms": list(freeze.ARMS),
        "primary_advancement_arms": list(freeze.PRIMARY_ADVANCEMENT_ARMS),
        "diagnostic_non_advancing_arms": list(freeze.DIAGNOSTIC_NON_ADVANCING_ARMS),
        "matched_candidate_count": 40,
        "conditional_reserve_candidate_count": 12,
        "candidate_count": 52,
    }
    assert contract["measured_execution_allowed"] is False
    assert contract["candidate_evaluation_allowed"] is False
    assert contract["execution_policy"]["forward_hard_stop_usd"] == 35
    assert contract["execution_policy"]["owner_ttl_hours"] == 40
    assert contract["contract_sha256"] == canonical_sha256(
        {key: value for key, value in contract.items() if key != "contract_sha256"}
    )
    assert budget["admission"]["forward_hard_stop_usd"] == 45
    assert budget["runtime_projection"]["owner_ttl_hours"] == 40
    assert budget["budget_profile_sha256"] == canonical_sha256(
        {key: value for key, value in budget.items() if key != "budget_profile_sha256"}
    )
    frozen_contract = _json("control/armindex/a2/execution-contract.v1.json")
    assert frozen_contract["revision_id"] == "a2-five-arm-premeasurement-freeze-v1"
    assert frozen_contract["measured_execution_allowed"] is False


def test_frozen_candidate_artifacts_are_unchanged_and_replay() -> None:
    assert file_sha256(ROOT / "campaigns/armindex-multiretriever-v2/manifests/a2-five-arm-candidate-manifest.v1.json") == "a49967760488971470169b97dd4a7638e045a72b6d20b119645eb0f9261f3133"
    result = freeze.validate_candidate_freeze(ROOT)
    assert result["status"] == "PASS_A2_CANDIDATE_FREEZE_REPLAY"
    assert {
        "manifest_sha256": result["manifest_sha256"],
        "freeze_receipt_sha256": result["receipt_sha256"],
        "lock_sha256": result["lock_sha256"],
    } == FREEZE


def test_a2_receipt_schemas_accept_only_aggregate_safe_staged_examples() -> None:
    attempt_id = "a2-20260812-readiness"
    digest = "a" * 64
    bundle = {"schema_version": "myis.armindex-a2-execution-bundle-receipt.v1", "receipt_id": "a2-20260812-readiness-bundle-v1", "attempt_id": attempt_id, "status": "PASS_CLEAN_HASH_BOUND_A2_BUNDLE", "clean_worktree": True, "pushed_to_origin_main": True, "git_commit": "b" * 40, "git_tree": "c" * 40, "freeze_bindings": FREEZE, "bundle_sha256": digest, "bundle_manifest_sha256": digest, "receipt_sha256": digest}
    admission = {"schema_version": "myis.armindex-a2-provider-admission-receipt.v1", "receipt_id": "a2-20260812-readiness-provider-admission-v1", "attempt_id": attempt_id, "status": "PASS_A2_PROVIDER_ADMISSION", "observed_at_utc": "2026-08-12T08:00:00Z", "quote_observed_at_utc": "2026-08-12T08:00:00Z", "provider_instance_id": "47411176", "provider_status": "RUNNING", "provider_verification": "VERIFIED", "evidence_mode": "OwnerDashboardSsh", "provider_authenticated": False, "login_or_logout_performed": False, "gpu_count": 4, "gpu_model": "RTX3090", "vram_mib_each": 24576, "gpu_uuid_set_sha256": digest, "runtime_sha256": digest, "model_lockset_sha256": digest, "data_handoff_sha256": digest, "ssh_host_key_sha256": digest, "all_fee_components_usd": {"compute_usd": "24.11", "storage_usd": "0", "network_usd": "0", "platform_or_other_fee_usd": "0", "tax_or_surcharge_usd": "0"}, "whole_workload_total_usd": "24.11", "quote_sha256": digest, "whole_workload_budget_sha256": digest, "management_mode": "OWNER_MANUAL_DASHBOARD_DESTROY_READY", "management_authority_sha256": digest, "owner_manual_dashboard_destroy_ready": True, "provider_destroy_performed": False, "provider_observation_sha256": digest, "provider_observation_file_sha256": digest, "source_artifact_sha256": {"runtime": digest, "model_lockset": digest, "data_handoff": digest, "ssh_host_key": digest, "management_authority": digest}, "ttl_deadline_utc": "2026-08-14T08:00:00Z", "remaining_ttl_seconds": 172800, "forward_hard_stop_usd": 35, "freeze_bindings": FREEZE, "receipt_sha256": digest}
    adoption = {"schema_version": "myis.armindex-a2-execution-adoption-receipt.v1", "receipt_id": "a2-20260812-readiness-execution-adoption-v1", "attempt_id": attempt_id, "status": "PASS_A2_EXECUTION_ADOPTION", "provider_admission_receipt_sha256": digest, "provider_observation_sha256": digest, "provider_observation_file_sha256": digest, "live_probe_receipt_sha256": digest, "live_probe_file_sha256": digest, "bundle_receipt_sha256": digest, "bundle_sha256": digest, "git_commit": "b" * 40, "git_tree": "c" * 40, "remote_root": "/opt/myis/a2-20260812-readiness", "remote_root_created_fresh": True, "staged_bundle_sha256": digest, "staged_bundle_verified": True, "ttl_deadline_utc": "2026-08-14T08:00:00Z", "remaining_ttl_seconds_at_admission": 172800, "watchdog_installed": True, "watchdog_deadline_utc": "2026-08-13T23:59:00Z", "watchdog_sha256": digest, "lifecycle_genesis_checkpoint_sha256": digest, "freeze_bindings": FREEZE, "launch_allowed": True, "measured_retrieval_allowed": False, "receipt_sha256": digest}
    checkpoint = {"schema_version": "myis.armindex-a2-lifecycle-checkpoint.v1", "checkpoint_id": "a2-20260812-readiness-checkpoint-0001", "attempt_id": attempt_id, "sequence": 1, "previous_checkpoint_sha256": None, "status": "STAGED", "completed_candidate_count": 0, "failed_candidate_count": 0, "resume_allowed": True, "freeze_bindings": FREEZE, "checkpoint_sha256": digest}
    safe_return = {"schema_version": "myis.armindex-a2-safe-return-receipt.v1", "receipt_id": "a2-20260812-readiness-safe-return-v1", "attempt_id": attempt_id, "status": "PASS_A2_SAFE_RETURN", "archive_sha256": digest, "archive_manifest_sha256": digest, "aggregate_artifact_count": 1, "protected_payload_included": False, "remote_root": "/opt/myis/a2-20260812-readiness", "freeze_bindings": FREEZE, "receipt_sha256": digest}
    train = {"schema_version": "myis.armindex-a2-train-evaluation-receipt.v1", "receipt_id": "a2-20260812-readiness-train-evaluation-v1", "attempt_id": attempt_id, "status": "PASS_A2_TRAIN_EVALUATION", "candidate_id": "a2-arm-03-matched-b1-exploit", "arm_id": "ARM-03", "aggregate_metrics_sha256": digest, "aggregate_metric_count": 1, "train_only": True, "rep_dev_measured": False, "per_query_outcomes_included": False, "freeze_bindings": FREEZE, "receipt_sha256": digest}
    winner = {"schema_version": "myis.armindex-a2-winner-selection-receipt.v1", "receipt_id": "a2-20260812-readiness-winner-v1", "attempt_id": attempt_id, "status": "PASS_A2_WINNER_SELECTED", "arm_id": "ARM-01", "winner_candidate_id": "a2-arm-01-matched-b1-exploit", "diagnostic_non_advancing": True, "advancement_eligible": False, "train_evaluation_receipt_sha256": digest, "strict_tie_rejected": True, "freeze_bindings": FREEZE, "receipt_sha256": digest}
    for schema, receipt in (("a2-execution-bundle-receipt.v1.json", bundle), ("a2-provider-admission-receipt.v1.json", admission), ("a2-execution-adoption-receipt.v1.json", adoption), ("a2-lifecycle-checkpoint.v1.json", checkpoint), ("a2-safe-return-receipt.v1.json", safe_return), ("a2-train-evaluation-receipt.v1.json", train), ("a2-winner-selection-receipt.v1.json", winner)):
        _valid(schema, receipt)


def test_dashboard_ssh_fallback_cannot_claim_authenticated_provider() -> None:
    payload = {"schema_version": "myis.armindex-a2-provider-admission-receipt.v1", "receipt_id": "a2-20260812-readiness-provider-admission-v1", "attempt_id": "a2-20260812-readiness", "status": "PASS_A2_PROVIDER_ADMISSION", "observed_at_utc": "2026-08-12T08:00:00Z", "quote_observed_at_utc": "2026-08-12T08:00:00Z", "provider_instance_id": "47411176", "provider_status": "RUNNING", "provider_verification": "VERIFIED", "evidence_mode": "OwnerDashboardSsh", "provider_authenticated": False, "login_or_logout_performed": False, "gpu_count": 4, "gpu_model": "RTX3090", "vram_mib_each": 24576, "runtime_sha256": "a" * 64, "model_lockset_sha256": "a" * 64, "data_handoff_sha256": "a" * 64, "ssh_host_key_sha256": "a" * 64, "all_fee_components_usd": {"compute_usd": "24.11", "storage_usd": "0", "network_usd": "0", "platform_or_other_fee_usd": "0", "tax_or_surcharge_usd": "0"}, "whole_workload_total_usd": "24.11", "quote_sha256": "a" * 64, "whole_workload_budget_sha256": "a" * 64, "management_mode": "OWNER_MANUAL_DASHBOARD_DESTROY_READY", "management_authority_sha256": "a" * 64, "owner_manual_dashboard_destroy_ready": True, "provider_destroy_performed": False, "ttl_hours": 40, "forward_hard_stop_usd": 35, "freeze_bindings": FREEZE, "receipt_sha256": "a" * 64}
    payload["provider_authenticated"] = True
    schema = _json("schemas/armindex/a2-provider-admission-receipt.v1.json")
    assert list(Draft202012Validator(schema).iter_errors(payload))
