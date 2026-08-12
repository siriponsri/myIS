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


def _fake_credit_check(
    _config: bridge.BridgeConfig,
    checkpoint_id: str,
) -> dict[str, Any]:
    snapshot = {
        "schema_version": bridge.CREDIT_SNAPSHOT_SCHEMA_VERSION,
        "checkpoint_id": checkpoint_id,
        "observed_at_utc": "2026-08-12T00:00:00Z",
        "model_name": bridge.MODEL,
        "sdk_version": bridge.SDK_VERSION,
        "plan_type": "plus",
        "primary": {
            "used_percent": 10,
            "remaining_percent": 90,
            "window_duration_mins": 10080,
            "resets_at": 1787013939,
            "resets_at_utc": "2026-08-18T00:45:39Z",
        },
        "rate_limit_reached_type": None,
        "credits": {"has_credits": False, "unlimited": False},
        "reset_credit_available_count": 1,
        "limit_reached": False,
        "protected_data_accessed": False,
        "measured_execution_performed": False,
    }
    snapshot["snapshot_sha256"] = canonical_sha256(snapshot)
    snapshot["snapshot_pointer"] = (
        "owner-local://official-codex/test/credit-snapshots/"
        f"{checkpoint_id}.json"
    )
    return snapshot


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
        credit_check=_fake_credit_check,
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
    assert manifest["official_credit_check_count"] == 14
    assert manifest["pre_generation_official_credit_snapshot"]["model_name"] == (
        "gpt-5.6-sol"
    )
    assert manifest["final_official_credit_snapshot"]["model_name"] == "gpt-5.6-sol"
    assert manifest["final_official_credit_snapshot"]["plan_type"] == "plus"
    assert manifest["final_official_credit_snapshot"]["remaining_percent"] == 90
    assert manifest["final_official_credit_snapshot"]["checkpoint_id"] == (
        f"{manifest['generation_attempt_id']}-review-arm-04-"
        "conditional_reserve-b3-r0-credit"
    )
    assert ledger_events[0]["event_type"] == "candidate_generation_start"
    assert ledger_events[-1]["event_type"] == "candidate_freeze_closeout"

    with pytest.raises(bridge.OfficialCodexBridgeError, match="locked after candidate freeze"):
        bridge.invoke_operation(
            config,
            "representation_propose",
            {"request_id": "a2-locked-after-freeze"},
        )


def test_pre_generation_credit_failure_stops_before_generation_or_persistence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ledger_events: list[dict[str, Any]] = []
    invoke_calls: list[str] = []
    monkeypatch.setattr(
        freeze,
        "append_preparation_ledger_event",
        lambda *_args, **kwargs: ledger_events.append(dict(kwargs)),
    )
    config = bridge.load_bridge_config(
        ROOT,
        event_root=tmp_path / "owner-events",
    )
    manifest_path = tmp_path / "candidate-manifest.json"
    receipt_path = tmp_path / "freeze-receipt.json"
    lock_path = tmp_path / "freeze-lock.json"
    config = replace(config, freeze_lock=lock_path)

    def forbidden_invoke(
        _config: bridge.BridgeConfig,
        operation: str,
        _request: Mapping[str, Any],
    ) -> dict[str, Any]:
        invoke_calls.append(operation)
        raise AssertionError("proposer/reviewer must not start")

    def unavailable_credit(
        _config: bridge.BridgeConfig,
        _checkpoint_id: str,
    ) -> dict[str, Any]:
        raise bridge.OfficialCodexBridgeError("OFFICIAL_CREDIT_UNAVAILABLE")

    with pytest.raises(
        freeze.A2CandidateFreezeError,
        match="before candidate generation",
    ):
        freeze.generate_and_freeze(
            ROOT,
            bridge_config=config,
            invoke=forbidden_invoke,
            credit_check=unavailable_credit,
            manifest_path=manifest_path,
            receipt_path=receipt_path,
            lock_path=lock_path,
        )

    assert ledger_events == []
    assert invoke_calls == []
    assert not manifest_path.exists()
    assert not receipt_path.exists()
    assert not lock_path.exists()


def test_design_has_no_reserve_for_diagnostic_arms() -> None:
    specs = freeze.build_batch_specs()

    assert freeze.validate_design()["candidate_count"] == 52
    assert not any(
        spec.tier == "conditional_reserve"
        for spec in specs
        if spec.arm_id in freeze.DIAGNOSTIC_NON_ADVANCING_ARMS
    )


def test_batch_revision_budget_is_bounded_and_schema_aligned() -> None:
    propose_schema = json.loads(
        (
            ROOT
            / "schemas/armindex/official-codex/representation-propose.request.v1.json"
        ).read_text(encoding="utf-8")
    )
    review_schema = json.loads(
        (
            ROOT
            / "schemas/armindex/official-codex/representation-review.request.v1.json"
        ).read_text(encoding="utf-8")
    )
    manifest_schema = json.loads(
        (ROOT / "schemas/armindex/a2-candidate-manifest.v1.json").read_text(
            encoding="utf-8"
        )
    )

    maximum_round = freeze.MAX_BATCH_REVISION_ROUNDS - 1
    assert propose_schema["properties"]["revision_round"]["maximum"] == maximum_round
    assert review_schema["properties"]["review_round"]["maximum"] == maximum_round
    assert (
        manifest_schema["$defs"]["batch"]["properties"]["revision_round"][
            "maximum"
        ]
        == maximum_round
    )
    assert (
        propose_schema["properties"]["reviewer_required_changes"]["items"][
            "maxLength"
        ]
        >= 400
    )


def test_previously_accepted_candidate_must_be_preserved() -> None:
    spec = freeze.build_batch_specs()[0]
    previous = [
        {
            "candidate_id": slot["candidate_id"],
            "role": slot["role"],
            "hypothesis": f"Stable falsifiable hypothesis for {slot['candidate_id']}.",
            "declared_axis": "field_selection",
            "program": _program(),
            "expected_effect": "A bounded within-arm effect can be measured later.",
            "failure_risk": "The candidate may not improve the frozen metric.",
        }
        for slot in spec.candidate_slots
    ]
    current = json.loads(json.dumps(previous))
    accepted_id = str(previous[0]["candidate_id"])

    freeze._validate_accepted_candidate_preservation(
        previous, current, {accepted_id}
    )
    current[0]["hypothesis"] = "Changed after independent acceptance."
    with pytest.raises(freeze.A2CandidateFreezeError, match="previously accepted"):
        freeze._validate_accepted_candidate_preservation(
            previous, current, {accepted_id}
        )


def test_partial_acceptance_revises_only_rejected_candidate(tmp_path: Path) -> None:
    spec = freeze.build_batch_specs()[0]
    config = bridge.load_bridge_config(
        ROOT,
        event_root=tmp_path / "owner-events",
    )
    bindings = {
        "campaign_sha256": "a" * 64,
        "a1_terminal_receipt_sha256": "b" * 64,
        "promotion_receipt_sha256": "c" * 64,
        "representation_schema_sha256": "d" * 64,
        "evaluator_sha256": "e" * 64,
        "primary_metric": "recall_at_100/out",
    }
    proposed_rounds: list[list[dict[str, Any]]] = []

    def candidate(slot: Mapping[str, Any], revision_round: int) -> dict[str, Any]:
        item = {
            "candidate_id": slot["candidate_id"],
            "role": slot["role"],
            "hypothesis": (
                f"Candidate {slot['candidate_id']} changes one declared axis "
                "and remains falsifiable against the frozen baseline."
            ),
            "declared_axis": "field_selection",
            "program": _program(),
            "expected_effect": "Improve bounded retrieval coverage without evaluator changes.",
            "failure_risk": "The representation may add noise and fail comparison.",
        }
        if revision_round == 1 and slot == spec.candidate_slots[-1]:
            item["hypothesis"] = (
                f"Revised candidate {slot['candidate_id']} changes one declared axis "
                "and isolates the reviewer-requested failure mode."
            )
        return item

    def invoke(
        _config: bridge.BridgeConfig,
        operation: str,
        request: Mapping[str, Any],
    ) -> dict[str, Any]:
        request_id = str(request["request_id"])
        revision_round = int(request.get("revision_round", request.get("review_round", 0)))
        if operation == "representation_propose":
            candidates = [candidate(slot, revision_round) for slot in spec.candidate_slots]
            if revision_round == 1:
                assert request["accepted_candidate_ids"] == [
                    slot["candidate_id"] for slot in spec.candidate_slots[:3]
                ]
                assert request["previous_candidates"] == proposed_rounds[0]
                assert candidates[:3] == proposed_rounds[0][:3]
                assert candidates[3] != proposed_rounds[0][3]
            proposed_rounds.append(candidates)
            result = {
                "schema_version": "myis.armindex-representation-propose-response.v1",
                "request_id": request_id,
                "arm_id": spec.arm_id,
                "tier": spec.tier,
                "batch_id": spec.batch_id,
                "candidates": candidates,
                "protected_data_accessed": False,
                "measured_execution_performed": False,
            }
        elif operation == "representation_review":
            assert request["previously_accepted_candidate_ids"] == (
                []
                if revision_round == 0
                else [slot["candidate_id"] for slot in spec.candidate_slots[:3]]
            )
            reviews = []
            for index, item in enumerate(request["candidates"]):
                revise = revision_round == 0 and index == 3
                reviews.append(
                    {
                        "candidate_id": item["candidate_id"],
                        "verdict": "revise" if revise else "accept",
                        "falsifiable": not revise,
                        "role_fit": True,
                        "duplicate_free": True,
                        "protected_boundary_safe": True,
                        "arm_compatible": True,
                        "deterministic": True,
                        "publication_interpretable": True,
                        "rationale": "The candidate is bounded and independently testable.",
                        "required_changes": (
                            ["Isolate the requested failure mode."] if revise else []
                        ),
                    }
                )
            result = {
                "schema_version": "myis.armindex-representation-review-response.v1",
                "request_id": request_id,
                "arm_id": spec.arm_id,
                "tier": spec.tier,
                "batch_id": spec.batch_id,
                "reviews": reviews,
                "protected_data_accessed": False,
                "measured_execution_performed": False,
            }
        else:
            raise AssertionError(f"unexpected operation: {operation}")
        return {
            "request_id": request_id,
            "operation": operation,
            "result": result,
            "identity": _identity(),
            "event_sha256": canonical_sha256(
                {"operation": operation, "request_id": request_id, "result": result}
            ),
            "status": "accepted",
            "retry_count": 0,
            "protected_data_accessed": False,
            "measured_execution_performed": False,
        }

    records, batch = freeze._generate_batch(
        ROOT,
        config,
        spec,
        bindings,
        "a2-preservation-test",
        invoke,
        _fake_credit_check,
    )

    assert len(records) == 4
    assert batch["revision_round"] == 1
    assert batch["credit_check_count"] == 2
    assert batch["final_credit_snapshot"]["model_name"] == "gpt-5.6-sol"
