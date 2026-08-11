from __future__ import annotations

import copy
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_provider_continuation_v16 import (
    RECEIPT_NAME,
    ProviderContinuationV16Error,
    build_provider_continuation_receipt,
    main,
    read_provider_continuation_receipt,
    validate_provider_continuation_receipt,
    write_provider_continuation_receipt,
)
from myis_research.kernel.canonical import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 8, 11, 10, 0, tzinfo=UTC)


def _observed(seconds: int = 60) -> str:
    return (NOW - timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def _payload() -> dict[str, object]:
    identity = "a" * 64
    return {
        "attempt_id": "a12-v16-20260811-r15",
        "instance_id": "47256937",
        "expected_instance_identity_sha256": identity,
        "provider_identity": {
            "observed_at_utc": _observed(),
            "authenticated": True,
            "provider_status": "RUNNING_VERIFIED",
            "instance_identity_sha256": identity,
            "provider_evidence_sha256": "b" * 64,
        },
        "ssh_endpoint": {
            "observed_at_utc": _observed(),
            "observation": "reachable",
            "instance_identity_sha256": identity,
            "ssh_evidence_sha256": "c" * 64,
        },
        "current_quote": {
            "observed_at_utc": _observed(),
            "quote_sha256": "d" * 64,
            "all_fee_hourly_rate_usd": "0.629444",
        },
        "accrued_a1_charge_usd": "12.345678",
        "watchdog": {
            "observed_at_utc": _observed(),
            "status": "PASS",
            "remaining_ttl_seconds": 7199,
            "watchdog_evidence_sha256": "e" * 64,
        },
        "safe_return_archive_sha256": "f" * 64,
        "evaluator_closeout_receipt_sha256": "0" * 64,
    }


def test_build_validate_and_immutable_external_write(tmp_path: Path) -> None:
    receipt = build_provider_continuation_receipt(ROOT, _payload(), now=NOW)
    assert receipt["provider_continuation_status"] == "REUSE_ELIGIBLE"
    assert receipt["next_phase"]["phase_id"] == "A2_PER_ARM_AUTOINDEX"
    target = tmp_path / "owner-receipts" / RECEIPT_NAME
    assert write_provider_continuation_receipt(ROOT, target, receipt, now=NOW) == receipt
    assert read_provider_continuation_receipt(ROOT, target, now=NOW) == receipt
    assert write_provider_continuation_receipt(ROOT, target, receipt, now=NOW) == receipt


def test_rejects_self_hash_tampering() -> None:
    receipt = build_provider_continuation_receipt(ROOT, _payload(), now=NOW)
    receipt["accrued_a1_charge_usd"] = "12.345679"
    with pytest.raises(ProviderContinuationV16Error, match="receipt_sha256 mismatch"):
        validate_provider_continuation_receipt(ROOT, receipt, now=NOW)


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda value: value["provider_identity"].update({"authenticated": False}), "authenticated running"),
        (lambda value: value["ssh_endpoint"].update({"observation": "connection_refused"}), "reachable"),
        (lambda value: value["ssh_endpoint"].update({"instance_identity_sha256": "1" * 64}), "must remain unchanged"),
        (lambda value: value["watchdog"].update({"status": "FAIL"}), "watchdog must pass"),
        (lambda value: value.update({"raw_provider_payload": {}}), "protected payload key"),
        (lambda value: value["current_quote"].update({"public_ip": "192.0.2.1"}), "incomplete or unsafe"),
    ],
)
def test_rejects_unsafe_or_drifted_continuation_evidence(mutate: object, message: str) -> None:
    payload = _payload()
    mutate(payload)  # type: ignore[operator]
    with pytest.raises(ProviderContinuationV16Error, match=message):
        build_provider_continuation_receipt(ROOT, payload, now=NOW)


def test_rejects_stale_evidence_and_safeguard_drift() -> None:
    stale = _payload()
    stale["watchdog"]["observed_at_utc"] = _observed(901)  # type: ignore[index]
    with pytest.raises(ProviderContinuationV16Error, match="not fresh"):
        build_provider_continuation_receipt(ROOT, stale, now=NOW)
    receipt = build_provider_continuation_receipt(ROOT, _payload(), now=NOW)
    changed = copy.deepcopy(receipt)
    changed["next_phase"]["new_isolated_remote_root_required"] = False
    changed["receipt_sha256"] = canonical_sha256(
        {key: value for key, value in changed.items() if key != "receipt_sha256"}
    )
    with pytest.raises(ProviderContinuationV16Error, match="schema validation"):
        validate_provider_continuation_receipt(ROOT, changed, now=NOW)


def test_rejects_immutable_conflict_and_repository_target(tmp_path: Path) -> None:
    receipt = build_provider_continuation_receipt(ROOT, _payload(), now=NOW)
    target = tmp_path / "owner-receipts" / RECEIPT_NAME
    write_provider_continuation_receipt(ROOT, target, receipt, now=NOW)
    target.write_text("{}\n", encoding="ascii")
    with pytest.raises(ProviderContinuationV16Error, match="immutable"):
        write_provider_continuation_receipt(ROOT, target, receipt, now=NOW)
    with pytest.raises(ProviderContinuationV16Error, match="outside the repository"):
        write_provider_continuation_receipt(ROOT, ROOT / RECEIPT_NAME, receipt, now=NOW)


def test_cli_builds_and_validates_owner_local_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    current = datetime.now(UTC)
    payload = _payload()
    observed = current.isoformat().replace("+00:00", "Z")
    for field in ("provider_identity", "ssh_endpoint", "current_quote", "watchdog"):
        payload[field]["observed_at_utc"] = observed  # type: ignore[index]
    input_path = tmp_path / "sanitized-continuation-input.json"
    input_path.write_text(json.dumps(payload), encoding="ascii")
    target = tmp_path / "owner-receipts" / RECEIPT_NAME
    monkeypatch.setattr(sys, "argv", [
        "a1_2_provider_continuation_v16", "build", "--repository-root", str(ROOT),
        "--input", str(input_path), "--receipt-path", str(target),
    ])
    assert main() == 0
    assert json.loads(capsys.readouterr().out)["status"] == "PASS"
    monkeypatch.setattr(sys, "argv", [
        "a1_2_provider_continuation_v16", "validate", "--repository-root", str(ROOT),
        "--receipt-path", str(target),
    ])
    assert main() == 0
    assert json.loads(capsys.readouterr().out)["provider_continuation_status"] == "REUSE_ELIGIBLE"
