from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_instance_disposition_v12 import (
    CURRENT_DISPOSITION,
    CURRENT_STATUS,
    InstanceDispositionV12Error,
    POLICY_PATH,
    current_status,
    evaluate_payload,
)


ROOT = Path(__file__).resolve().parents[1]


def _hash(character: str) -> str:
    return character * 64


def _evidence() -> dict[str, object]:
    identity = {
        "instance_identity_sha256": _hash("1"),
        "gpu_uuid_set_sha256": _hash("2"),
        "image_reference": "pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime",
        "image_manifest_digest": "sha256:" + _hash("3"),
        "git_commit": "a" * 40,
        "git_tree": "b" * 40,
        "bundle_sha256": _hash("4"),
        "staged_artifacts_sha256": _hash("5"),
    }
    return {
        "safe_return": {
            "local_validation_status": "PASS", "collection_status": "PASS", "teardown_status": "PASS",
            "archive_sha256": _hash("6"), "members_sha256": _hash("7"),
            "teardown_receipt_sha256": _hash("8"), "collection_receipt_sha256": _hash("9"), "member_count": 72,
        },
        "preflight_identity": dict(identity),
        "current_identity": dict(identity),
        "budget": {
            "quote_age_seconds": 10, "all_fee_hourly_usd": 0.6, "planned_next_goal_seconds": 3600,
            "charged_common_screen_usd": 0, "charged_a1_usd": 0, "charged_campaign_usd": 0,
            "projected_common_screen_usd": 0.6, "projected_a1_usd": 0.6, "projected_campaign_usd": 0.6,
        },
        "remaining_ttl_seconds": 7200,
        "ttl_safety_margin_seconds": 300,
        "protected_boundary": {"status": "PASS", "scan_receipt_sha256": _hash("a")},
        "watchdog_destroy_dry_run": {
            "status": "PASS", "mode": "owner_local_dry_run", "provider_action_performed": False,
            "destroy_command_validated": True, "ttl_trigger_simulated": True,
            "guest_poweroff_is_provider_destruction": False,
            "target_instance_identity_sha256": _hash("1"), "receipt_sha256": _hash("b"),
        },
        "next_goal": {"owner_authorized": True, "goal_id": "a1.2-next-local-goal", "authorization_sha256": _hash("c"), "execution_adoption_authorized": False},
        "owner_requests_destroy": False,
    }


def test_v12_policy_reports_no_live_instance_without_external_action() -> None:
    status = current_status(ROOT)
    policy = json.loads((ROOT / POLICY_PATH).read_text(encoding="utf-8"))
    assert status["status"] == CURRENT_STATUS
    assert status["current_disposition"] == CURRENT_DISPOSITION
    assert policy["status"] == CURRENT_STATUS
    assert policy["current_disposition"] == CURRENT_DISPOSITION
    assert status["launch_allowed"] is False


def test_v12_reuse_requires_every_local_predicate() -> None:
    receipt = evaluate_payload(ROOT, _evidence(), receipt_id="a1.2-instance-disposition-pass-v12")
    assert receipt["disposition"] == "REUSE_ELIGIBLE"
    assert receipt["failure_reasons"] == []
    assert receipt["next_owner_instruction"] == "Owner continue next goal on PLAN"
    assert receipt["launch_allowed"] is False
    assert receipt["does_not_authorize"]


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda value: value["safe_return"].update({"collection_status": "FAIL"}), "safe_return_not_validated"),
        (lambda value: value["current_identity"].update({"bundle_sha256": _hash("d")}), "instance_identity_or_frozen_binding_changed"),
        (lambda value: value["budget"].update({"quote_age_seconds": 901}), "quote_stale_or_budget_headroom_insufficient"),
        (lambda value: value.update({"remaining_ttl_seconds": 300}), "remaining_ttl_insufficient"),
        (lambda value: value["protected_boundary"].update({"status": "FAIL"}), "protected_boundary_not_clean"),
        (lambda value: value["watchdog_destroy_dry_run"].update({"provider_action_performed": True}), "watchdog_or_destroy_dry_run_failed"),
        (lambda value: value["next_goal"].update({"owner_authorized": False}), "separate_next_goal_not_authorized"),
        (lambda value: value.update({"owner_requests_destroy": True}), "owner_requested_destroy"),
    ],
)
def test_v12_fails_closed_with_deterministic_reasons(mutate: object, reason: str) -> None:
    evidence = _evidence()
    mutate(evidence)  # type: ignore[operator]
    receipt = evaluate_payload(ROOT, evidence, receipt_id="a1.2-instance-disposition-fail-v12")
    assert receipt["disposition"] == "DESTROY_REQUIRED"
    assert receipt["next_owner_instruction"] == "Owner destroy instance"
    assert reason in receipt["failure_reasons"]
    assert receipt["failure_reasons"] == sorted(receipt["failure_reasons"])


def test_v12_rejects_unsafe_evidence_and_invalid_receipt_id() -> None:
    evidence = _evidence()
    evidence["unsafe"] = "C:\\Owner\\secret"
    with pytest.raises(InstanceDispositionV12Error):
        evaluate_payload(ROOT, evidence, receipt_id="a1.2-instance-disposition-safe-v12")
    with pytest.raises(InstanceDispositionV12Error, match="receipt identifier"):
        evaluate_payload(ROOT, _evidence(), receipt_id="wrong")
