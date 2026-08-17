from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from myis_research.armindex.a3_three_primary_admission import (
    A3ThreePrimaryAdmissionError,
    build_three_primary_live_admission,
)


ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 8, 17, 15, 0, tzinfo=timezone.utc)


def _load(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _receipts(**kwargs: object) -> dict[str, dict[str, object]]:
    values: dict[str, object] = {
        "budget": _load("control/budgets/armindex-budget-extension-a3-three-primary.v1.json"),
        "authority": _load("control/armindex/a3/a3-three-primary-preparation-authority.v1.json"),
        "manifest": _load("control/armindex/a3/a3-three-primary-preparation-manifest.v1.json"),
        "provider_identity": {
            "provider": "vast",
            "instance_id": 47790578,
            "machine_id": 134131,
            "status": "running",
            "gpu_count": 4,
            "gpu_model": "RTX_3090",
            "ssh_runtime_sha256": "a" * 64,
        },
        "observed_at_utc": NOW - timedelta(seconds=30),
        "all_fee_usd_per_hour": "0.6456",
        "a1_actual_usd": "11.161632",
        "now_utc": NOW,
    }
    values.update(kwargs)
    return build_three_primary_live_admission(**values)  # type: ignore[arg-type]


def test_builds_fresh_hash_bound_admission_under_both_caps() -> None:
    receipts = _receipts()
    assert receipts["admission"]["status"] == "PASS_A3_FRESH_ADMISSION"
    assert receipts["admission"]["quote_age_seconds"] == 30
    assert receipts["all_fee_quote"]["a3_projected_total_usd"] == "30.9888"
    assert receipts["campaign_budget_amendment"]["campaign_projected_total_usd"] == "96.67709866666665948"


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"all_fee_usd_per_hour": "0.73"}, "A3 projected spend"),
        ({"target_ttl_seconds": 172799}, "target TTL"),
        ({"observed_at_utc": NOW - timedelta(seconds=901)}, "stale"),
    ],
)
def test_rejects_stale_or_over_cap_live_admission(change: dict[str, object], message: str) -> None:
    with pytest.raises(A3ThreePrimaryAdmissionError, match=message):
        _receipts(**change)
