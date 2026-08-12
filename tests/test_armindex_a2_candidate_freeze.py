from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from myis_research.armindex import a2_candidate_freeze as freeze
from myis_research.armindex import official_codex_bridge as bridge
from myis_research.kernel.canonical import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]


def _identity() -> dict[str, str]:
    return {
        "sdk_version": "0.144.4",
        "runtime_user_agent": "codex_cli_rs/0.144.4",
        "cli_version": "0.144.4",
        "model": "gpt-5.6-sol",
        "model_provider": "openai",
        "reasoning_effort": "high",
    }


def _program() -> dict[str, Any]:
    return {
        "source_fields": ["title", "abstract", "claims_text"],
        "field_order": ["title", "abstract", "claims_text"],
        "field_labels": {
            "title": "Title",
            "abstract": "Abstract",
            "claims_text": "Claims",
        },
        "unitization": {"kind": "family", "logical_size": None, "overlap": 0},
        "normalization": "unicode_nfkc_whitespace",
        "duplicate_policy": "content_hash_first",
        "family_aggregation": "single_unit",
    }


def _fake_invoke(
    _config: bridge.BridgeConfig,
    operation: str,
    request: Mapping[str, Any],
) -> dict[str, Any]:
    request_id = str(request["request_id"])
    if operation == "representation_propose":
        result = {
            "schema_version": "myis.armindex-representation-propose-response.v1",
            "request_id": request_id,
            "arm_id": request["arm_id"],
            "tier": request["tier"],
            "batch_id": request["batch_id"],
            "candidates": [
                {
                    "candidate_id": slot["candidate_id"],
                    "role": slot["role"],
                    "hypothesis": (
                        f"Candidate {slot['candidate_id']} changes its declared representation axis "
                        "and is falsifiable against the frozen within-arm baseline."
                    ),
                    "declared_axis": "field_selection",
                    "program": _program(),
                    "expected_effect": "Improve retrieval coverage without changing the evaluator.",
                    "failure_risk": "The representation may add noise and fail within-arm comparison.",
                }
                for slot in request["candidate_slots"]
            ],
            "protected_data_accessed": False,
            "measured_execution_performed": False,
        }
    elif operation == "representation_review":
        result = {
            "schema_version": "myis.armindex-representation-review-response.v1",
            "request_id": request_id,
            "arm_id": request["arm_id"],
            "tier": request["tier"],
            "batch_id": request["batch_id"],
            "reviews": [
                {
                    "candidate_id": candidate["candidate_id"],
                    "verdict": "accept",
                    "falsifiable": True,
                    "role_fit": True,
                    "duplicate_free": True,
                    "protected_boundary_safe": True,
                    "arm_compatible": True,
                    "deterministic": True,
                    "publication_interpretable": True,
                    "rationale": "The candidate is bounded, deterministic, and independently testable.",
                    "required_changes": [],
                }
                for candidate in request["candidates"]
            ],
            "protected_data_accessed": False,
            "measured_execution_performed": False,
        }
    else:
        raise AssertionError(f"unexpected operation: {operation}")
    event_sha256 = canonical_sha256(
        {"operation": operation, "request_id": request_id, "result": result}
    )
    return {
        "request_id": request_id,
        "operation": operation,
        "result": result,
        "identity": _identity(),
        "event_sha256": event_sha256,
        "status": "accepted",
        "retry_count": 0,
        "protected_data_accessed": False,
        "measured_execution_performed": False,
    }


def test_generate_freeze_and_replay_exact_40_plus_12(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ledger_events: list[dict[str, Any]] = []

    def fake_ledger(*_args: Any, **kwargs: Any) -> dict[str, Any]:
        ledger_events.append(dict(kwargs))
        return dict(kwargs)

    monkeypatch.setattr(freeze, "append_preparation_ledger_event", fake_ledger)
    config = bridge.load_bridge_config(
        ROOT,
        event_root=tmp_path / "owner-events",
    )
    manifest_path = tmp_path / "candidate-manifest.json"
    receipt_path = tmp_path / "freeze-receipt.json"
    lock_path = tmp_path / "freeze-lock.json"
    config = replace(config, freeze_lock=lock_path)

    result = freeze.generate_and_freeze(
        ROOT,
        bridge_config=config,
        invoke=_fake_invoke,
        manifest_path=manifest_path,
        receipt_path=receipt_path,
        lock_path=lock_path,
    )
    replay = freeze.validate_candidate_freeze(
        ROOT,
        manifest_path=manifest_path,
        receipt_path=receipt_path,
        lock_path=lock_path,
    )
    manifest = json.loads(manifest_path.read_text(encoding="ascii"))
    candidates = manifest["candidates"]

    assert result["status"] == "PASS_A2_CANDIDATE_FREEZE_REPLAY"
    assert replay["candidate_count"] == 52
    assert len([item for item in candidates if item["tier"] == "matched"]) == 40
    assert len(
        [item for item in candidates if item["lifecycle"] == "dormant_conditional"]
    ) == 12
    assert all(
        item["advancement_eligible"] is False
        for item in candidates
        if item["arm_id"] in freeze.DIAGNOSTIC_NON_ADVANCING_ARMS
    )
    assert all(
        item["compile_sha256s"][0] == item["compile_sha256s"][1]
        for item in candidates
    )
    assert len({item["candidate_id"] for item in candidates}) == 52
    assert len({item["scientific_payload_sha256"] for item in candidates}) == 52
    assert manifest["measured_execution_performed"] is False
    assert ledger_events[0]["event_type"] == "candidate_generation_start"
    assert ledger_events[-1]["event_type"] == "candidate_freeze_closeout"

    with pytest.raises(bridge.OfficialCodexBridgeError, match="locked after candidate freeze"):
        bridge.invoke_operation(
            config,
            "representation_propose",
            {"request_id": "a2-locked-after-freeze"},
        )


def test_design_has_no_reserve_for_diagnostic_arms() -> None:
    specs = freeze.build_batch_specs()

    assert freeze.validate_design()["candidate_count"] == 52
    assert not any(
        spec.tier == "conditional_reserve"
        for spec in specs
        if spec.arm_id in freeze.DIAGNOSTIC_NON_ADVANCING_ARMS
    )
