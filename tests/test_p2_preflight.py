from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess

import pytest

from myis_research.kernel.canonical import canonical_sha256, file_sha256
from myis_research.p2 import (
    P2ContractError,
    run_p2_preflight,
    validate_p2_candidate_freeze_proposal,
    validate_p2_preflight_receipt,
)
from myis_research.p2.contracts import build_request
from myis_research.projections.read_model import _p2_readiness_projection


ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_PATH = ROOT / "campaigns/scope-autoindex-v1/proposals/p2-candidate-freeze-proposal.v1.json"


def _self_hash(payload: dict[str, object], field: str) -> dict[str, object]:
    payload.pop(field, None)
    payload[field] = canonical_sha256(payload)
    return payload


def _request_path(tmp_path: Path) -> Path:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    request = build_request(
        request_id="p2-preflight-test",
        git_commit=commit,
        execution_envelope_sha256=file_sha256(ROOT / "control/execution-envelope-p2.yaml"),
        scope_hashes={
            "compiler": "1" * 64,
            "config": "2" * 64,
            "retriever": "3" * 64,
            "evaluator": "4" * 64,
        },
        input_hashes={"dataset": "5" * 64},
        frozen_controls=[f"control-{index}" for index in range(4)],
        repository_root=ROOT,
    )
    path = tmp_path / "request.json"
    path.write_text(json.dumps(request, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _passed_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    first = tmp_path / "myis-store"
    second = tmp_path / "myis-mlflow-store"
    first.mkdir()
    second.mkdir()
    monkeypatch.setenv("MYIS_STORE", str(first.resolve()))
    monkeypatch.setenv("MYIS_MLFLOW_STORE", str(second.resolve()))
    return run_p2_preflight(
        _request_path(tmp_path),
        ROOT,
        required_free_space_bytes=0,
    )


def test_candidate_freeze_proposal_is_valid_but_not_adopted() -> None:
    proposal = json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))

    validated = validate_p2_candidate_freeze_proposal(proposal, repository_root=ROOT)

    assert validated["status"] == "draft_owner_review"
    assert validated["adoption"] == "not_adopted"
    assert len(validated["frozen_controls"]) == 4
    assert len(validated["preregistered_candidates"]) == 8
    assert all(item["registered"] is False for item in validated["frozen_controls"])
    assert all(item["hash_locked"] is False for item in validated["preregistered_candidates"])

    projection = _p2_readiness_projection(ROOT, {})
    assert projection["candidate_proposal"]["status"] == "draft_owner_review"
    assert projection["candidate_proposal"]["adoption"] == "not_adopted"
    assert projection["candidate_count"] == 0
    assert projection["shortlist_count"] == 0
    assert projection["selection_accesses"] == 0


def test_candidate_freeze_proposal_rejects_stale_source_binding() -> None:
    proposal = json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))
    proposal["source_bindings"][0]["sha256"] = "0" * 64
    _self_hash(proposal, "proposal_sha256")

    with pytest.raises(P2ContractError, match="source binding is stale"):
        validate_p2_candidate_freeze_proposal(proposal, repository_root=ROOT)


def test_candidate_freeze_proposal_rejects_unsafe_source_locator() -> None:
    proposal = json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))
    proposal["source_bindings"][0]["uri"] = "../PLAN.md"
    _self_hash(proposal, "proposal_sha256")

    with pytest.raises(P2ContractError, match="safe repository-relative URI"):
        validate_p2_candidate_freeze_proposal(proposal, repository_root=ROOT)


def test_preflight_passes_without_emitting_owner_local_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _passed_receipt(tmp_path, monkeypatch)

    assert receipt["status"] == "passed_pending_owner"
    assert receipt["measured_execution"] is False
    assert receipt["protected_data_accessed"] is False
    assert receipt["counters"] == {
        "measured_runs": 0,
        "candidate_count": 0,
        "shortlist_count": 0,
        "selection_accesses": 0,
        "baseline_commitment_present": False,
        "freeze_started": False,
    }
    encoded = json.dumps(receipt, ensure_ascii=True, sort_keys=True)
    assert str((tmp_path / "myis-store").resolve()) not in encoded
    assert str((tmp_path / "myis-mlflow-store").resolve()) not in encoded


def test_preflight_fails_closed_when_store_paths_overlap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = tmp_path / "shared-store"
    store.mkdir()
    monkeypatch.setenv("MYIS_STORE", str(store.resolve()))
    monkeypatch.setenv("MYIS_MLFLOW_STORE", str(store.resolve()))

    receipt = run_p2_preflight(
        _request_path(tmp_path),
        ROOT,
        required_free_space_bytes=0,
    )

    assert receipt["status"] == "failed"
    assert "store_path_overlap" in receipt["failure_codes"]
    assert receipt["measured_execution"] is False
    assert receipt["counters"]["selection_accesses"] == 0


def test_preflight_receipt_rejects_stale_campaign_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _passed_receipt(tmp_path, monkeypatch)
    receipt["campaign_sha256"] = "0" * 64
    _self_hash(receipt, "receipt_sha256")

    with pytest.raises(P2ContractError, match="campaign binding is stale"):
        validate_p2_preflight_receipt(receipt, repository_root=ROOT)


def test_preflight_receipt_rejects_missing_required_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _passed_receipt(tmp_path, monkeypatch)
    receipt["checks"].pop()
    _self_hash(receipt, "receipt_sha256")

    with pytest.raises(P2ContractError, match="exact required check set"):
        validate_p2_preflight_receipt(receipt, repository_root=ROOT)


def test_preflight_receipt_rejects_stale_execution_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = deepcopy(_passed_receipt(tmp_path, monkeypatch))
    receipt["git_commit"] = "f" * 40
    _self_hash(receipt, "receipt_sha256")

    with pytest.raises(P2ContractError, match="execution source commit is stale"):
        validate_p2_preflight_receipt(receipt, repository_root=ROOT)
