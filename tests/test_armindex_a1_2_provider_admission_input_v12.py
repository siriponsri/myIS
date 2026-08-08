from __future__ import annotations

import copy
from datetime import datetime, timezone
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_provider_admission_input_v12 import (
    ProviderAdmissionInputV12Error,
    TEMPLATE_PATH,
    validate_candidate,
)
from myis_research.kernel.canonical import file_sha256


ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 8, 8, 0, 10, 0, tzinfo=timezone.utc)
TEMPLATE_SHA256 = "16342d91674f2b6496c1c0633ec9e3b9583ce7d63fa3d744d14c21d323cfe615"


def _candidate() -> dict[str, object]:
    return {
        "schema_version": "myis.armindex-a1.2-provider-admission-input.v12",
        "status": "PENDING_LIVE_PROVIDER",
        "template_file_sha256": file_sha256(ROOT / TEMPLATE_PATH),
        "template_sha256": TEMPLATE_SHA256,
        "observed_at_utc": "2026-08-08T00:00:00Z",
        "provider_identity": {
            "provider_label": "Vast", "instance_identity_sha256": "1" * 64,
            "observed_at_utc": "2026-08-08T00:00:00Z", "gpu_uuid_set_sha256": "2" * 64,
            "gpu_count": 4, "gpu_model": "NVIDIA GeForce RTX 3090", "vram_mib_each": 24576,
            "cpu_count": 16, "ram_bytes": 68719476736, "free_disk_bytes": 268435456000,
        },
        "runtime_identity": {
            "image_reference": "pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime",
            "image_manifest_digest": "sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20",
            "platform": "linux/amd64", "python": "3.11", "torch": "2.6.0+cu118", "cuda": "11.8",
        },
        "quote": {
            "quote_observed_at_utc": "2026-08-08T00:00:00Z", "compute_hourly_rate_usd": 0.6,
            "billing_granularity_seconds": 60, "minimum_billable_seconds": 60,
            "storage_fee_usd": 0.1, "network_fee_usd": 0.1, "platform_or_other_fee_usd": 0.1,
            "tax_or_surcharge_usd": 0.0, "owner_ttl_hours": 6, "worst_case_total_charge_usd": 3.9,
            "quote_receipt_sha256": "3" * 64,
        },
    }


def test_exact_fresh_sanitized_input_remains_pending_and_locked() -> None:
    result = validate_candidate(ROOT, _candidate(), now=NOW)
    assert result["status"] == "PENDING_LIVE_PROVIDER"
    assert result["provider_contact_allowed"] is False
    assert result["launch_allowed"] is False
    assert result["adopted_for_execution"] is False


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value["provider_identity"].update({"gpu_count": 3}),
        lambda value: value["provider_identity"].update({"gpu_model": "NVIDIA A100"}),
        lambda value: value["provider_identity"].update({"vram_mib_each": 16000}),
        lambda value: value["runtime_identity"].update({"image_reference": "other:image"}),
        lambda value: value["runtime_identity"].update({"platform": "linux/arm64"}),
        lambda value: value["runtime_identity"].update({"torch": "2.5.0+cu118"}),
        lambda value: value["runtime_identity"].update({"cuda": "12.1"}),
        lambda value: value["quote"].pop("tax_or_surcharge_usd"),
        lambda value: value["quote"].update({"unknown_fee_usd": 0}),
        lambda value: value["quote"].update({"network_fee_usd": -0.01}),
        lambda value: value["quote"].update({"quote_observed_at_utc": "2026-08-07T23:54:59Z"}),
        lambda value: value["provider_identity"].update({"instance_id": "raw-id-forbidden"}),
        lambda value: value.update({"credentials": "Bearer abcdefghijklmnopqrstuvwxyz"}),
    ],
)
def test_invalid_or_unsafe_provider_inputs_fail_closed(mutate: object) -> None:
    value = _candidate()
    mutate(value)  # type: ignore[operator]
    with pytest.raises(ProviderAdmissionInputV12Error):
        validate_candidate(ROOT, value, now=NOW)


def test_future_identity_and_misaligned_billing_fail_closed() -> None:
    future = _candidate()
    future["observed_at_utc"] = "2026-08-08T00:10:01Z"
    future["provider_identity"]["observed_at_utc"] = "2026-08-08T00:10:01Z"
    with pytest.raises(ProviderAdmissionInputV12Error, match="future"):
        validate_candidate(ROOT, future, now=NOW)
    billing = _candidate()
    billing["quote"]["minimum_billable_seconds"] = 61
    with pytest.raises(ProviderAdmissionInputV12Error, match="align"):
        validate_candidate(ROOT, billing, now=NOW)


def test_input_hash_is_deterministic() -> None:
    first = validate_candidate(ROOT, _candidate(), now=NOW)
    second = validate_candidate(ROOT, copy.deepcopy(_candidate()), now=NOW)
    assert first == second
