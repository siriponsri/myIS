from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.kernel.canonical import file_sha256
from myis_research.p2.contracts import (
    P2ContractError,
    build_request,
    load_p2_request,
    load_profile,
    validate_p2_artifact,
    write_immutable_json,
)


ROOT = Path(__file__).resolve().parents[1]


def _request() -> dict[str, object]:
    return build_request(
        request_id="p2-fixture-request",
        git_commit="a" * 40,
        execution_envelope_sha256=file_sha256(ROOT / "control/execution-envelope-p2.yaml"),
        scope_hashes={"scope": "b" * 64},
        input_hashes={"inputs": "c" * 64},
        frozen_controls=["r0", "r0-w", "matched-control-a", "matched-control-b"],
        repository_root=ROOT,
    )


def test_profile_is_hash_bound_and_has_no_ambiguous_cpu_limit() -> None:
    profile = load_profile(ROOT)
    assert profile.profile_id == "p2-r1-primary-v1"
    assert profile.payload["limits"]["max_candidates_total"] == 32
    assert profile.payload["runtime"]["max_wall_clock_seconds"] == 259200
    assert profile.payload["runtime"]["per_candidate_timeout_seconds"] == 10800
    assert "max_cpu_seconds" not in json.dumps(profile.payload)


def test_request_requires_current_profile_and_envelope_hash(tmp_path: Path) -> None:
    request = _request()
    request_path = tmp_path / "p2-request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    loaded, profile = load_p2_request(request_path, ROOT)
    assert loaded["budget_profile_sha256"] == profile.sha256

    stale = dict(request)
    stale["budget_profile_sha256"] = "d" * 64
    request_path.write_text(json.dumps(stale), encoding="utf-8")
    with pytest.raises(P2ContractError, match="budget_profile_sha256"):
        load_p2_request(request_path, ROOT)


def test_immutable_json_refuses_overwrite(tmp_path: Path) -> None:
    path = tmp_path / "receipt.json"
    payload = {"status": "fixture"}
    write_immutable_json(path, payload)
    with pytest.raises(P2ContractError, match="overwrite"):
        write_immutable_json(path, payload)


def test_p2_receipt_self_hash_is_verified() -> None:
    payload = {
        "schema_version": "myis.p2-selection-receipt.v1",
        "request_id": "p2-fixture-request",
        "candidate_ids": [],
        "shortlist_freeze_receipt_sha256": "a" * 64,
        "selection_exposure_count": 1,
        "status": "accepted",
        "metrics": [],
    }
    from myis_research.kernel.canonical import canonical_sha256

    payload["receipt_sha256"] = canonical_sha256(payload)
    assert validate_p2_artifact(payload)["status"] == "accepted"
    payload["status"] = "blocked"
    with pytest.raises(P2ContractError, match="self-hash"):
        validate_p2_artifact(payload)
