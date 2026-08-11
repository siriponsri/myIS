from __future__ import annotations

import copy
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_live_admission_v16 import (
    LiveAdmissionV16Error,
    build_receipts,
    main,
    read_receipts,
    validate_receipt_set,
    write_receipts,
)
from myis_research.armindex.a1_2_whole_workload_budget_extension_v16 import (
    evaluate_payload,
)
from myis_research.armindex.a1_2_whole_workload_budget_extension_v17 import (
    evaluate_payload as evaluate_v17_payload,
)
from myis_research.kernel.canonical import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 8, 11, 8, 10, tzinfo=UTC)


def _hash(value: str) -> str:
    return value * 64


def _budget(*, version: int = 17) -> dict[str, object]:
    if version == 17:
        return evaluate_v17_payload(
            ROOT,
            {
                "quote": {
                    "quote_observed_at_utc": "2026-08-11T08:00:00Z",
                    "compute_hourly_rate_usd": 0.56,
                    "billing_granularity_seconds": 60,
                    "minimum_billable_seconds": 60,
                    "storage_fee_usd": 0.06944444444444443,
                    "network_fee_usd": 0.0,
                    "platform_or_other_fee_usd": 0.0,
                    "tax_or_surcharge_usd": 0.0,
                },
                "prior_attempt_spend_usd": {
                    "attempt_count": 1,
                    "accounting_basis": "ALL_FEE_DESTROYED_ATTEMPT_TOTAL",
                    "common_screen": 22.469444444444443,
                    "a1_total": 22.469444444444443,
                    "campaign": 22.469444444444443,
                },
                "workload": {"arm_ids": ["ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05"], "expected_program_arm_runs": 25, "partial_arm_admission": False},
                "evaluated_at_utc": "2026-08-11T08:10:00Z",
            },
            receipt_id="a1.2-whole-workload-budget-extension-live-admission-v17",
        )
    payload = {
        "quote": {
            "quote_observed_at_utc": "2026-08-11T08:00:00Z",
            "compute_hourly_rate_usd": 0.5333333333,
            "billing_granularity_seconds": 60,
            "minimum_billable_seconds": 60,
            "storage_fee_usd": 0.0694444444,
            "network_fee_usd": 0.1,
            "platform_or_other_fee_usd": 0.0,
            "tax_or_surcharge_usd": 0.0,
        },
        "prior_spend_usd": {"common_screen": 0.0, "a1_total": 0.0, "campaign": 0.0},
        "workload": {"arm_ids": ["ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05"], "expected_program_arm_runs": 25, "partial_arm_admission": False},
        "evaluated_at_utc": "2026-08-11T08:10:00Z",
    }
    return evaluate_payload(ROOT, payload, receipt_id="a1.2-whole-workload-budget-extension-live-admission-v16")


def _payload() -> dict[str, object]:
    budget = _budget()
    promotion_policy = json.loads((ROOT / "control/armindex/a1.2/promotion-policy.v16.json").read_text(encoding="utf-8"))["policy_sha256"]
    instance, host, provider, gpu = (_hash("a"), _hash("b"), _hash("c"), _hash("d"))
    payload = {
        "attempt_id": "a12-v17-20260811-r14",
        "provider_identity": {
            "observed_at_utc": "2026-08-11T08:00:00Z", "observation_mode": "AUTHENTICATED_CLI", "provider_label": "Vast", "provider_authenticated": True,
            "provider_identity_sha256": provider, "provider_evidence_sha256": _hash("e"), "instance_identity_sha256": instance,
            "host_identity_sha256": host, "machine_identity_sha256": _hash("f"), "gpu_uuid_set_sha256": gpu, "provider_status": "RUNNING_VERIFIED",
            "gpu_count": 4, "gpu_model": "NVIDIA GeForce RTX 3090", "vram_mib_each": 24576, "platform": "linux/amd64",
            "all_fee_quote_sha256": _hash("1"), "whole_workload_budget_input_sha256": budget["input_sha256"],
        },
        "ssh_runtime": {
            "observed_at_utc": "2026-08-11T08:01:00Z", "instance_identity_sha256": instance, "host_identity_sha256": host, "ssh_host_key_sha256": _hash("2"), "gpu_uuid_set_sha256": gpu,
            "platform": "linux/amd64", "python": "3.11", "torch": "2.6.0+cu118", "cuda": "11.8", "gpu_count": 4, "gpu_model": "NVIDIA GeForce RTX 3090", "vram_mib_each": 24576,
            "image_reference": "pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime", "image_manifest_digest": "sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20", "runtime_evidence_sha256": _hash("3"),
        },
        "management_dry_run": {
            "observed_at_utc": "2026-08-11T08:02:00Z", "instance_identity_sha256": instance, "provider_identity_sha256": provider,
            "status": "READY_NOT_EXECUTED", "provider_destroy_capability": "READY_NOT_EXECUTED", "provider_action_performed": False, "destroy_command_template_sha256": _hash("4"), "management_evidence_sha256": _hash("5"),
        },
        "budget_admission": budget,
        "watchdog": {"observed_at_utc": "2026-08-11T08:03:00Z", "status": "PASS", "instance_identity_sha256": instance, "owner_ttl_hours": 40, "ttl_deadline_utc": "2026-08-13T00:00:00Z", "watchdog_receipt_sha256": _hash("6")},
        "adoption_bindings": {key: _hash(f"{index % 10}") for index, key in enumerate((
            "provider_identity", "all_fee_quote", "whole_workload_budget", "provider_management_authority", "watchdog_ttl", "ssh_identity", "runtime_identity", "scientific_request", "adoption_inputs", "transfer", "workload", "common_programs", "model_lockset", "protected_compiler", "image", "git_commit_tree_bundle", "evaluator", "split", "qrels_commitment", "token_map", "safe_return", "compiled_bindings_25_of_25", "physical_coverage_35", "promotion_policy",
        ))},
    }
    payload["adoption_bindings"].update({
        "provider_identity": provider,
        "all_fee_quote": _hash("1"),
        "whole_workload_budget": budget["receipt_sha256"],
        "provider_management_authority": _hash("5"),
        "watchdog_ttl": _hash("6"),
        "ssh_identity": _hash("2"),
        "runtime_identity": _hash("3"),
        "promotion_policy": promotion_policy,
    })
    return payload


def _with_budget(payload: dict[str, object], budget: dict[str, object]) -> None:
    payload["budget_admission"] = budget
    payload["provider_identity"]["whole_workload_budget_input_sha256"] = budget["input_sha256"]  # type: ignore[index]
    payload["adoption_bindings"]["whole_workload_budget"] = budget["receipt_sha256"]  # type: ignore[index]


def test_builds_self_hashed_linked_pass_receipts() -> None:
    receipts = build_receipts(ROOT, _payload(), now=NOW)
    result = validate_receipt_set(ROOT, receipts)
    assert result["status"] == "PASS"
    assert result["provider_admission"] == "PASS_PROVIDER_ADMISSION"
    assert result["execution_adoption"] == "PASS_EXECUTION_ADOPTION"
    assert receipts["execution_adoption"]["measured_retrieval_allowed"] is True
    assert receipts["execution_adoption"]["selection_allowed"] is False
    assert receipts["provider_admission"]["budget_admission_receipt_sha256"] == _payload()["budget_admission"]["receipt_sha256"]
    assert receipts["provider_admission"]["budget_revision_id"] == "a1.2-whole-workload-budget-extension-v17"
    assert receipts["provider_admission"]["prior_attempt_count"] == 1
    assert receipts["provider_admission"]["projected_spend_usd"]["a1_total"] == pytest.approx(44.93888888888889)


def test_r14_rejects_v16_budget_but_historical_attempt_remains_readable() -> None:
    r14 = _payload()
    _with_budget(r14, _budget(version=16))
    with pytest.raises(LiveAdmissionV16Error, match="r14"):
        build_receipts(ROOT, r14, now=NOW)
    historical = _payload()
    historical["attempt_id"] = "a12-v16-20260809-historical"
    _with_budget(historical, _budget(version=16))
    receipts = build_receipts(ROOT, historical, now=NOW)
    assert receipts["provider_admission"]["budget_revision_id"] == "a1.2-whole-workload-budget-extension-v16"
    assert receipts["provider_admission"]["prior_attempt_count"] == 0


def test_promotion_policy_binding_must_match_frozen_control() -> None:
    payload = _payload()
    payload["adoption_bindings"]["promotion_policy"] = _hash("0")  # type: ignore[index]
    with pytest.raises(LiveAdmissionV16Error, match="promotion policy"):
        build_receipts(ROOT, payload, now=NOW)


def test_immutable_external_write_and_read(tmp_path: Path) -> None:
    receipts = build_receipts(ROOT, _payload(), now=NOW)
    receipt_dir = tmp_path / "owner-local-receipts"
    assert write_receipts(ROOT, receipt_dir, receipts)["status"] == "PASS"
    assert read_receipts(ROOT, receipt_dir) == receipts
    assert write_receipts(ROOT, receipt_dir, receipts)["status"] == "PASS"
    path = receipt_dir / "provider-identity.receipt.v16.json"
    altered = json.loads(path.read_text(encoding="utf-8"))
    altered["status"] = "BAD"
    path.write_text(json.dumps(altered), encoding="utf-8")
    with pytest.raises(LiveAdmissionV16Error):
        read_receipts(ROOT, receipt_dir)


def test_module_cli_builds_and_validates_external_receipts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    input_path = tmp_path / "sanitized-live-input.json"
    payload = _payload()
    observed = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    for key in ("provider_identity", "ssh_runtime", "management_dry_run", "watchdog"):
        payload[key]["observed_at_utc"] = observed  # type: ignore[index]
    payload["watchdog"]["ttl_deadline_utc"] = (
        datetime.now(UTC) + timedelta(hours=39)
    ).isoformat().replace("+00:00", "Z")  # type: ignore[index]
    input_path.write_text(json.dumps(payload), encoding="utf-8")
    receipt_dir = tmp_path / "receipts"
    monkeypatch.setattr(sys, "argv", [
        "a1_2_live_admission_v16", "build", "--repository-root", str(ROOT),
        "--input", str(input_path), "--receipt-dir", str(receipt_dir),
    ])
    assert main() == 0
    assert json.loads(capsys.readouterr().out)["status"] == "PASS"
    monkeypatch.setattr(sys, "argv", [
        "a1_2_live_admission_v16", "validate", "--repository-root", str(ROOT),
        "--receipt-dir", str(receipt_dir),
    ])
    assert main() == 0
    assert json.loads(capsys.readouterr().out)["execution_adoption"] == "PASS_EXECUTION_ADOPTION"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value["provider_identity"].update({"instance_id": "47411176"}),
        lambda value: value["provider_identity"].update({"provider_authenticated": False}),
        lambda value: value["ssh_runtime"].update({"gpu_count": 3}),
        lambda value: value["management_dry_run"].update({"provider_action_performed": True}),
        lambda value: value["watchdog"].update({"status": "FAIL"}),
        lambda value: value["adoption_bindings"].pop("safe_return"),
        lambda value: value.update({"credentials": "Bearer abcdefghijklmnopqrstuvwxyz"}),
    ],
)
def test_unsafe_or_drifted_input_fails_closed(mutate: object) -> None:
    payload = _payload()
    mutate(payload)  # type: ignore[operator]
    with pytest.raises(LiveAdmissionV16Error):
        build_receipts(ROOT, payload, now=NOW)


def test_stale_observation_and_broken_cross_link_fail_closed() -> None:
    stale = _payload()
    stale["watchdog"]["observed_at_utc"] = "2026-08-11T07:30:00Z"  # type: ignore[index]
    stale["watchdog"]["ttl_deadline_utc"] = "2026-08-12T23:30:00Z"  # type: ignore[index]
    with pytest.raises(LiveAdmissionV16Error, match="fresh"):
        build_receipts(ROOT, stale, now=NOW)
    receipts = build_receipts(ROOT, _payload(), now=NOW)
    broken = copy.deepcopy(receipts)
    broken["execution_adoption"]["provider_admission_receipt_sha256"] = _hash("9")
    body = {key: value for key, value in broken["execution_adoption"].items() if key != "receipt_sha256"}
    broken["execution_adoption"]["receipt_sha256"] = canonical_sha256(body)
    with pytest.raises(LiveAdmissionV16Error, match="linkage"):
        validate_receipt_set(ROOT, broken)
