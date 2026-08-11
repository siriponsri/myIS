from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex import a1_2_engineering_execution_bundle_v16 as v16
from myis_research.kernel.canonical import file_sha256

ROOT = Path(__file__).resolve().parents[1]


def _contract() -> dict[str, object]:
    return json.loads((ROOT / v16.CONTRACT_PATH).read_text(encoding="utf-8"))


def test_closed_v16_contract_preserves_frozen_surface_and_cannot_authorize() -> None:
    contract = _contract()
    assert contract["contract_sha256"] == v16._self_hash(contract, "contract_sha256")
    v16._validate_frozen_files(ROOT, contract["frozen_file_sha256"])
    assert contract["status"] == "READY_FOR_CLEAN_BUNDLE"
    assert contract["authorization"]["measured_retrieval_allowed"] is False
    assert contract["runtime_policy"]["runtime_downloads_forbidden"] is True


def test_closed_v16_contract_has_complete_historical_bundle_closure() -> None:
    contract = _contract()
    assert contract["support_sources"]["raw_materializer_bridge"]["sha256"]
    assert contract["support_sources"]["remote_arm_worker"]["sha256"]
    assert contract["support_sources"]["distributed_launcher"]["sha256"]
    assert contract["support_sources"]["evaluation_manifest_builder"]["sha256"]
    assert contract["support_sources"]["evaluator_closeout"]["sha256"]
    assert "control/armindex/a1.2/promotion-policy.v16.json" in contract["frozen_file_sha256"]


def test_v16_bundle_base_closure_binds_safe_return_and_watchdog() -> None:
    assert (
        "src/myis_research/armindex/a1_2_safe_return_v16.py"
        in v16._BASE_PATHS
    )
    assert "scripts/a1_2_vast/Invoke-A12GovernedWatchdogV16.ps1" in v16._BASE_PATHS
    assert "schemas/armindex/a1.2-cell-performance-metrics.v16.json" in v16._BASE_PATHS
    assert "schemas/armindex/a1.2-owner-local-cell-commit.v16.json" in v16._BASE_PATHS


def test_v16_watchdog_checkout_bytes_are_forced_to_lf() -> None:
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
    assert (
        "scripts/a1_2_vast/Invoke-A12GovernedWatchdogV16.ps1 text eol=lf"
        in attributes
    )


def test_v16_bundle_rebuild_fails_after_terminal_closeout_source_repair() -> None:
    contract = _contract()
    mismatches = []
    for group in ("executor_sources", "support_sources"):
        for role, binding in contract[group].items():
            if file_sha256(ROOT / binding["path"]) != binding["sha256"]:
                mismatches.append((group, role))
    assert mismatches == [("support_sources", "evaluator_closeout")]
    with pytest.raises(v16.EngineeringExecutionV16Error, match="source hash drift"):
        v16.bundle_paths(ROOT)


def test_v16_contract_rejects_frozen_hash_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    value = json.loads((ROOT / v16.CONTRACT_PATH).read_text(encoding="utf-8"))
    value["frozen_file_sha256"]["control/armindex/a1.2/common-program-set.v11.json"] = "0" * 64
    value["contract_sha256"] = v16._self_hash(value, "contract_sha256")
    changed = tmp_path / "changed.json"
    changed.write_text(json.dumps(value), encoding="utf-8")
    monkeypatch.setattr(v16, "CONTRACT_PATH", changed)
    with pytest.raises(v16.EngineeringExecutionV16Error, match="hash drift"):
        v16.validate_contract(ROOT)
