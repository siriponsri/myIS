from __future__ import annotations

import json
from pathlib import Path

from myis_research.armindex.a1_2_instance_disposition_v13 import (
    current_status,
    evaluate_payload,
)
from myis_research.armindex.a1_2_watchdog_provider_destroy_dry_run_v12 import (
    evaluate_payload as watchdog_receipt,
)
from myis_research.kernel.canonical import canonical_sha256, file_sha256

ROOT = Path(__file__).resolve().parents[1]
NOW = "2026-08-08T12:00:00Z"


def _hash(char: str) -> str:
    return char * 64


def _receipt(kind: str, **extra: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": "myis.armindex-a1.2-instance-disposition-evidence.v13",
        "receipt_kind": kind,
        "status": "PASS",
        "instance_identity_sha256": _hash("a"),
        "observed_at_utc": NOW,
        **extra,
    }
    value["receipt_sha256"] = canonical_sha256(value)
    return value


def _source(receipt: dict[str, object]) -> dict[str, object]:
    return {"receipt": receipt}


def _control(path: str) -> dict[str, object]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _evidence() -> dict[str, object]:
    identity = {
        "gpu_uuid_set_sha256": _hash("b"),
        "image_reference": "pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime",
        "image_manifest_digest": "sha256:" + _hash("c"),
        "git_commit": "d" * 40,
        "git_tree": "e" * 40,
        "bundle_sha256": _hash("f"),
        "model_lockset_sha256": _hash("1"),
        "program_set_sha256": _hash("2"),
    }
    watchdog = watchdog_receipt(
        ROOT,
        {
            "target_instance_identity_sha256": _hash("a"),
            "ttl_seconds": 21600,
            "heartbeat_stale_seconds": 300,
            "simulated_elapsed_seconds": 21600,
            "simulated_heartbeat_age_seconds": 0,
            "expected_trigger": "ttl_expired",
            "command_template_tokens": [
                "<provider_cli>",
                "destroy",
                "instance",
                "<provider_instance_identity_sha256>",
            ],
        },
        receipt_id="a1.2-watchdog-provider-destroy-dry-run-v13-test-v12",
    )
    run = {
        "attempt_id": "a12-v13-same-attempt",
        "safe_export_archive_sha256": _hash("3"),
        "safe_export_members_sha256": _hash("4"),
    }
    collection = _receipt(
        "local_collection",
        **run,
        collection_status="PASS",
        local_validation_status="PASS",
        member_hash_validation_status="PASS",
        member_count=72,
    )
    template_path = "control/armindex/a1.2/provider-admission-input-template.v12.json"
    budget_path = "control/armindex/a1.2/whole-workload-budget-admission.v12.json"
    template = _control(template_path)
    budget = _control(budget_path)
    preflight = _receipt(
        "preflight_identity", **identity, preflight_status="PASS"
    )
    current = _receipt(
        "provider_identity_observation",
        **identity,
        identity_observation_status="PASS",
    )
    safe_return = _receipt(
        "safe_return",
        **run,
        safe_return_status="PASS",
        local_validation_status="PASS",
        collection_status="PASS",
        teardown_status="PASS",
        teardown_receipt_sha256=_hash("6"),
        local_collection_receipt_sha256=collection["receipt_sha256"],
    )
    teardown = _receipt(
        "teardown_export",
        **run,
        teardown_status="PASS",
        guest_process_cleanup_verified=True,
        remote_cleanup_receipt_sha256=_hash("7"),
    )
    protected_scan = _receipt(
        "protected_scan",
        **run,
        protected_scan_status="PASS",
        protected_boundary_clean=True,
    )
    clean_worker = _receipt(
        "clean_worker_proof",
        **run,
        clean_worker_proof_status="PASS",
        worker_state="CLEAN",
        gpu_process_count=0,
        child_process_count=0,
    )
    destroy_readiness = _receipt(
        "provider_destroy_readiness",
        schema_version="myis.armindex-a1.2-provider-destroy-readiness-evidence.v13",
        provider_destroy_readiness_status="TESTED_LIVE_PROVIDER",
        actual_provider_destroy_capability="TESTED_LIVE_PROVIDER",
        provider_action_performed=False,
        destroy_command_template_sha256=_hash("5"),
        provider_identity_observation_receipt_sha256=current["receipt_sha256"],
        watchdog_destroy_dry_run_receipt_sha256=watchdog["receipt_sha256"],
    )
    next_goal = _receipt(
        "next_goal_authorization",
        owner_authorized=True,
        owner_report_status="ACKNOWLEDGED",
        owner_report_receipt_sha256=_hash("8"),
        owner_decision_receipt_sha256=_hash("9"),
        next_goal_authorization_sha256=_hash("0"),
        next_goal_id="A2.1",
        compatible_next_goal=True,
        fresh_provider_admission_required=False,
        compatible_frozen_identity_sha256=canonical_sha256(identity),
    )
    return {
        "preflight_identity": _source(preflight),
        "provider_identity_observation": _source(current),
        "provider_quote_observation": _source(
            _receipt(
                "provider_quote_observation",
                all_fee_quote_status="PASS",
                compute_hourly_rate_usd=0.6,
                billing_granularity_seconds=60,
                minimum_billable_seconds=60,
                storage_fee_usd=0,
                network_fee_usd=0,
                platform_or_other_fee_usd=0,
                tax_or_surcharge_usd=0,
                remaining_ttl_seconds=7200,
                required_next_goal_ttl_seconds=3600,
                ttl_safety_margin_seconds=300,
                charged_common_screen_usd=0,
                charged_a1_usd=0,
                charged_campaign_usd=0,
                projected_common_screen_usd=0.6,
                projected_a1_usd=0.6,
                projected_campaign_usd=0.6,
                worst_case_total_charge_usd=0.6,
                provider_admission_template_file_sha256=file_sha256(ROOT / template_path),
                provider_admission_template_sha256=template["template_sha256"],
                budget_admission_file_sha256=file_sha256(ROOT / budget_path),
                budget_admission_sha256=budget["admission_sha256"],
            )
        ),
        "safe_return": _source(safe_return),
        "teardown_export": _source(teardown),
        "local_collection": _source(collection),
        "protected_scan": _source(protected_scan),
        "clean_worker_proof": _source(clean_worker),
        "watchdog_destroy_dry_run": _source(watchdog),
        "provider_destroy_readiness": _source(destroy_readiness),
        "next_goal_authorization": _source(next_goal),
        "evaluation_time_utc": NOW,
        "owner_requests_destroy": False,
    }


def test_v13_is_pending_without_a_live_instance() -> None:
    result = current_status(ROOT)
    assert result["status"] == "PENDING_LIVE_PROVIDER"
    assert result["current_disposition"] == "NO_LIVE_INSTANCE"


def test_v13_reuse_requires_receipt_validated_evidence() -> None:
    result = evaluate_payload(
        ROOT, _evidence(), receipt_id="a1.2-instance-disposition-pass-v13"
    )
    assert result["disposition"] == "REUSE_ELIGIBLE"
    assert len(result["validated_receipt_sha256s"]) == 11
    assert result["destroy_readiness_evidence_status"] == "TESTED_LIVE_PROVIDER"


def test_v13_forces_destroy_for_tampered_watchdog_and_fresh_admission() -> None:
    evidence = _evidence()
    evidence["watchdog_destroy_dry_run"] = {
        "receipt": {"status": "PASS", "receipt_sha256": _hash("9")}
    }
    result = evaluate_payload(
        ROOT, evidence, receipt_id="a1.2-instance-disposition-watchdog-v13"
    )
    assert result["disposition"] == "DESTROY_REQUIRED"
    assert "watchdog_destroy_dry_run_unvalidated" in result["failure_reasons"]

    evidence = _evidence()
    goal = evidence["next_goal_authorization"]["receipt"]
    goal["fresh_provider_admission_required"] = True
    goal["receipt_sha256"] = canonical_sha256(
        {key: value for key, value in goal.items() if key != "receipt_sha256"}
    )
    result = evaluate_payload(
        ROOT, evidence, receipt_id="a1.2-instance-disposition-admission-v13"
    )
    assert result["disposition"] == "DESTROY_REQUIRED"
    assert "next_goal_not_authorized_or_requires_fresh_provider" in result["failure_reasons"]


def test_v13_forces_destroy_when_a_required_receipt_is_missing() -> None:
    evidence = _evidence()
    evidence["safe_return"] = {}
    result = evaluate_payload(
        ROOT, evidence, receipt_id="a1.2-instance-disposition-missing-v13"
    )
    assert result["disposition"] == "DESTROY_REQUIRED"
    assert "missing_or_invalid_safe_return" in result["failure_reasons"]


def test_v13_forces_destroy_for_export_or_destroy_readiness_tampering() -> None:
    evidence = _evidence()
    export = evidence["teardown_export"]["receipt"]
    export["safe_export_archive_sha256"] = _hash("6")
    export["receipt_sha256"] = canonical_sha256(
        {key: value for key, value in export.items() if key != "receipt_sha256"}
    )
    result = evaluate_payload(
        ROOT, evidence, receipt_id="a1.2-instance-disposition-export-v13"
    )
    assert result["disposition"] == "DESTROY_REQUIRED"
    assert "same_attempt_export_collection_binding_invalid" in result["failure_reasons"]

    evidence = _evidence()
    readiness = evidence["provider_destroy_readiness"]["receipt"]
    readiness["actual_provider_destroy_capability"] = "PENDING_LIVE_PROVIDER"
    readiness["receipt_sha256"] = canonical_sha256(
        {key: value for key, value in readiness.items() if key != "receipt_sha256"}
    )
    result = evaluate_payload(
        ROOT, evidence, receipt_id="a1.2-instance-disposition-readiness-v13"
    )
    assert result["disposition"] == "DESTROY_REQUIRED"
    assert "provider_destroy_readiness_missing_or_not_tested" in result["failure_reasons"]


def test_v13_reads_only_safe_external_receipt_paths(tmp_path: Path) -> None:
    evidence = _evidence()
    path = tmp_path / "safe-return.json"
    path.write_text(
        json.dumps(evidence["safe_return"]["receipt"]), encoding="utf-8"
    )
    evidence["safe_return"] = {"external_path": str(path.resolve())}
    result = evaluate_payload(
        ROOT, evidence, receipt_id="a1.2-instance-disposition-external-v13"
    )
    assert result["disposition"] == "REUSE_ELIGIBLE"
