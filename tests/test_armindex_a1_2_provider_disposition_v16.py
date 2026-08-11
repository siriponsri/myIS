from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_provider_disposition_v16 import (
    RECEIPT_NAME,
    ProviderDispositionV16Error,
    build_provider_disposition_receipt,
    main,
    read_provider_disposition_receipt,
    validate_provider_disposition_receipt,
    write_provider_disposition_receipt,
)

ROOT = Path(__file__).resolve().parents[1]


def _payload() -> dict[str, object]:
    return {
        "attempt_id": "a12-v16-20260811-r15",
        "instance_id": "47256937",
        "observed_at_utc": "2026-08-11T09:10:11Z",
        "provider_authentication": {
            "authenticated": True,
            "destroy_outcome": "DESTROYED_CONFIRMED",
            "provider_absence_verified": True,
        },
        "ssh_endpoint": {"post_destroy_observation": "connection_refused"},
        "final_charge_usd": "12.345678",
        "final_quote_sha256": "a" * 64,
    }


def test_build_validate_and_immutable_external_write(tmp_path: Path) -> None:
    receipt = build_provider_disposition_receipt(ROOT, _payload())
    assert receipt["status"] == "PASS"
    assert receipt["scientific_authority"] is False
    target = tmp_path / "owner-receipts" / RECEIPT_NAME
    assert write_provider_disposition_receipt(ROOT, target, receipt)["receipt_sha256"] == receipt["receipt_sha256"]
    assert read_provider_disposition_receipt(ROOT, target) == receipt
    assert write_provider_disposition_receipt(ROOT, target, receipt) == receipt


def test_rejects_self_hash_tampering() -> None:
    receipt = build_provider_disposition_receipt(ROOT, _payload())
    receipt["instance_id"] = "47256938"
    with pytest.raises(ProviderDispositionV16Error, match="receipt_sha256 mismatch"):
        validate_provider_disposition_receipt(ROOT, receipt)


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda value: value["provider_authentication"].update({"authenticated": False}), "authenticated provider destruction"),
        (lambda value: value["provider_authentication"].update({"provider_absence_verified": False}), "authenticated provider destruction"),
        (lambda value: value["ssh_endpoint"].update({"post_destroy_observation": "reachable"}), "connection_refused"),
        (lambda value: value.update({"raw_provider_payload": {}}), "protected payload key"),
        (lambda value: value.update({"public_ip": "192.0.2.1"}), "incomplete or unsafe"),
    ],
)
def test_rejects_unsafe_or_incomplete_closeout_evidence(mutate: object, message: str) -> None:
    payload = _payload()
    mutate(payload)  # type: ignore[operator]
    with pytest.raises(ProviderDispositionV16Error, match=message):
        build_provider_disposition_receipt(ROOT, payload)


def test_rejects_immutable_conflict_and_repository_target(tmp_path: Path) -> None:
    receipt = build_provider_disposition_receipt(ROOT, _payload())
    target = tmp_path / "owner-receipts" / RECEIPT_NAME
    write_provider_disposition_receipt(ROOT, target, receipt)
    target.write_text("{}\n", encoding="ascii")
    with pytest.raises(ProviderDispositionV16Error, match="immutable"):
        write_provider_disposition_receipt(ROOT, target, receipt)
    with pytest.raises(ProviderDispositionV16Error, match="outside the repository"):
        write_provider_disposition_receipt(ROOT, ROOT / RECEIPT_NAME, receipt)


def test_cli_builds_and_validates_owner_local_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    input_path = tmp_path / "sanitized-disposition-input.json"
    input_path.write_text(json.dumps(_payload()), encoding="ascii")
    target = tmp_path / "owner-receipts" / RECEIPT_NAME
    monkeypatch.setattr(sys, "argv", [
        "a1_2_provider_disposition_v16", "build", "--repository-root", str(ROOT),
        "--input", str(input_path), "--receipt-path", str(target),
    ])
    assert main() == 0
    assert json.loads(capsys.readouterr().out)["status"] == "PASS"
    monkeypatch.setattr(sys, "argv", [
        "a1_2_provider_disposition_v16", "validate", "--repository-root", str(ROOT),
        "--receipt-path", str(target),
    ])
    assert main() == 0
    assert json.loads(capsys.readouterr().out)["ssh_endpoint"]["post_destroy_observation"] == "connection_refused"
