from __future__ import annotations

from pathlib import Path

import pytest

from myis_research.armindex.a1_2_watchdog_provider_destroy_dry_run_v12 import (
    WatchdogDestroyDryRunV12Error,
    current_status,
    evaluate_payload,
    write_result,
)


ROOT = Path(__file__).resolve().parents[1]


def _evidence() -> dict[str, object]:
    return {
        "target_instance_identity_sha256": "a" * 64,
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
    }


def test_v12_watchdog_status_remains_pending_live_provider() -> None:
    status = current_status(ROOT)
    assert status["status"] == "PENDING_LIVE_PROVIDER"
    assert status["actual_provider_destroy_capability"] == "PENDING_LIVE_PROVIDER"
    assert status["provider_action_performed"] is False


def test_v12_watchdog_validates_template_and_ttl_without_provider_action() -> None:
    receipt = evaluate_payload(
        ROOT, _evidence(), receipt_id="a1.2-watchdog-provider-destroy-dry-run-pass-v12"
    )
    assert receipt["status"] == "PASS"
    assert receipt["mode"] == "owner_local_dry_run"
    assert receipt["destroy_command_validated"] is True
    assert receipt["ttl_trigger_simulated"] is True
    assert receipt["simulated_trigger"] == "ttl_expired"
    assert receipt["provider_action_performed"] is False
    assert receipt["actual_provider_destroy_capability"] == "PENDING_LIVE_PROVIDER"
    assert receipt["actual_destroy_receipt_required"] is True


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("simulated_elapsed_seconds", 21599, "TTL has not expired"),
        ("expected_trigger", "heartbeat_stale", "requires a TTL-expired"),
        (
            "command_template_tokens",
            ["vastai", "destroy", "instance", "123"],
            "sanitized frozen",
        ),
        ("target_instance_identity_sha256", "123", "identity hash"),
    ],
)
def test_v12_watchdog_rejects_non_dry_run_or_unsanitized_inputs(
    field: str, value: object, message: str
) -> None:
    evidence = _evidence()
    evidence[field] = value
    with pytest.raises(WatchdogDestroyDryRunV12Error, match=message):
        evaluate_payload(
            ROOT, evidence, receipt_id="a1.2-watchdog-provider-destroy-dry-run-fail-v12"
        )


def test_v12_watchdog_rejects_unsafe_provider_material() -> None:
    evidence = _evidence()
    evidence["provider_instance_id"] = "12345678"
    with pytest.raises(WatchdogDestroyDryRunV12Error, match="incomplete or unsafe"):
        evaluate_payload(
            ROOT, evidence, receipt_id="a1.2-watchdog-provider-destroy-dry-run-safe-v12"
        )


def test_v12_watchdog_writes_only_immutable_external_receipt(tmp_path: Path) -> None:
    output = tmp_path / "watchdog.json"
    first = write_result(
        ROOT,
        _evidence(),
        receipt_id="a1.2-watchdog-provider-destroy-dry-run-written-v12",
        output=output,
    )
    second = write_result(
        ROOT,
        _evidence(),
        receipt_id="a1.2-watchdog-provider-destroy-dry-run-written-v12",
        output=output,
    )

    assert first == second
    assert output.is_file()
    with pytest.raises(WatchdogDestroyDryRunV12Error, match="outside the repository"):
        write_result(
            ROOT,
            _evidence(),
            receipt_id="a1.2-watchdog-provider-destroy-dry-run-repository-v12",
            output=ROOT / "watchdog.json",
        )
