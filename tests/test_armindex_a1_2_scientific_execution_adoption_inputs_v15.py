from __future__ import annotations

import json
from pathlib import Path

import pytest

import myis_research.armindex.a1_2_scientific_execution_adoption_inputs_v15 as v15
from myis_research.armindex.a1_2_whole_workload_budget_model_v15 import (
    validate_contract as validate_budget_model,
)

ROOT = Path(__file__).resolve().parents[1]


def _clean_pushed_git(monkeypatch: pytest.MonkeyPatch) -> None:
    values = {
        ("status", "--porcelain=v1", "--untracked-files=all"): "",
        ("rev-parse", "HEAD^{commit}"): "a" * 40,
        ("rev-parse", "HEAD^{tree}"): "b" * 40,
        ("rev-parse", "origin/main"): "a" * 40,
        ("ls-files",): "\n".join(v15.BUNDLE_PATHS),
    }
    monkeypatch.setattr(v15, "_git", lambda _root, *args: values[args])


def test_v15_contract_keeps_every_live_provider_input_pending() -> None:
    contract = v15.validate_contract(ROOT)
    assert contract["pending_live_provider"] == v15.PENDING_LIVE_PROVIDER
    assert contract["authorization"]["provider_contact_allowed"] is False
    assert contract["authorization"]["measured_retrieval_allowed"] is False
    assert contract["counters"]["measured_runs"] == 0


def test_v15_budget_model_binds_physical_workload_and_hard_stops() -> None:
    model = validate_budget_model(ROOT)
    assert model["workload"]["physical_window_total"] == 2_581_603
    assert model["workload"]["raw_overflow_logical_inputs"] == 140_907
    assert model["frozen_hard_stops_usd"] == {
        "common_screen": 18,
        "a1_total": 23,
        "campaign": 100,
    }
    assert model["live_admission"]["admitted"] is False


def test_v15_preserves_v13_machine_ids_and_safe_publication_labels() -> None:
    publication = json.loads(
        (ROOT / "control/armindex/a1.2/publication-impact-contract.v13.json").read_text(
            encoding="utf-8"
        )
    )
    assert v15._publication_outcomes(publication) == {
        "primary": "OUT Recall@100",
        "secondary": ["OUT nDCG@100", "OUT nDCG@10"],
    }


def test_v15_bundle_is_deterministic_and_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _clean_pushed_git(monkeypatch)
    first = v15.build_bundle(
        ROOT,
        output=tmp_path / "first.tar.gz",
        receipt_output=tmp_path / "first.json",
    )
    second = v15.build_bundle(
        ROOT,
        output=tmp_path / "second.tar.gz",
        receipt_output=tmp_path / "second.json",
    )
    assert (tmp_path / "first.tar.gz").read_bytes() == (
        tmp_path / "second.tar.gz"
    ).read_bytes()
    assert first["bundle_sha256"] == second["bundle_sha256"]
    assert first["file_count"] == len(v15.BUNDLE_PATHS)


def test_v15_contract_rejects_live_authorization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    value = json.loads((ROOT / v15.CONTRACT_PATH).read_text(encoding="utf-8"))
    value["authorization"]["provider_contact_allowed"] = True
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    monkeypatch.setattr(v15, "CONTRACT_PATH", path)
    with pytest.raises(v15.AdoptionInputsV15Error):
        v15.validate_contract(ROOT)
