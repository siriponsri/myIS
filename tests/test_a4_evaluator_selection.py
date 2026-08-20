from __future__ import annotations

import pytest

from myis_research.armindex.a4_a5_handoff import (
    A4A5HandoffError,
    build_a5_pointer_bundle,
    build_pending_a5_handoff_template,
    validate_a5_pointer_bundle,
    validate_pending_a5_handoff_template,
)
from myis_research.armindex.a4_evaluator import (
    A4OwnerEvaluatorError,
    build_a4_coverage_receipt,
    build_legal_transfer_receipt,
    evaluate_a4_profile_owner_local,
)
from myis_research.armindex.a4_execution import freeze_selection_registry
from myis_research.armindex.a4_selection import (
    A4SelectionError,
    build_selection_frontier,
    consume_selection_once,
)


H = "a" * 64
GIT = "1" * 40


def _profile(name: str) -> dict:
    return {"profile_id": name, "attempt_id": "a4-goal001-20260819T010203Z"}


def _package(name: str) -> dict:
    body = {
        "schema_version": "myis.armindex-a4-remote-ranking-package.v1",
        "status": "PASS_A4_REMOTE_RANKING_PACKAGE",
        "request_sha256": H,
        "ranking_sha256": "b" * 64,
        "coverage": {"expected_units": 100, "completed_units": 100},
        "rankings": {f"opaque-{i}": ["f"] for i in range(100)},
        "latency": {"p50_ms": 1, "p95_ms": 2, "p99_ms": 3, "throughput_qps": 50},
        "resource": {"cost_usd": 1, "ram_gib": 2, "vram_gib": 3, "index_size_bytes": 4},
    }
    return body


def test_owner_local_profile_and_complete_coverage() -> None:
    result = evaluate_a4_profile_owner_local(
        _profile("FAST"),
        _package("FAST"),
        evaluator_binding_sha256=H,
        hdev_commitment_sha256=H,
        metric_evaluator=lambda _rankings: {"recall_at_100": 0.5, "ndcg_at_100": 0.4, "ndcg_at_10": 0.3},
    )
    assert result["protected_payload_included"] is False
    results = [result]
    for index, name in enumerate(("BALANCED", "DEEP"), start=1):
        package = _package(name)
        package["request_sha256"] = f"{index + 1:x}" * 64
        package["ranking_sha256"] = f"{index + 2:x}" * 64
        results.append(
            evaluate_a4_profile_owner_local(
                _profile(name), package, evaluator_binding_sha256=H, hdev_commitment_sha256=H,
                metric_evaluator=lambda _rankings: {"recall_at_100": 0.5, "ndcg_at_100": 0.4, "ndcg_at_10": 0.3},
            )
        )
    coverage = build_a4_coverage_receipt(results, attempt_id=_profile("FAST")["attempt_id"], hdev_commitment_sha256=H)
    assert coverage["commercial_profile_count"] == 3
    with pytest.raises(A4OwnerEvaluatorError):
        evaluate_a4_profile_owner_local(_profile("FAST"), {**_package("FAST"), "qrels": []}, evaluator_binding_sha256=H, hdev_commitment_sha256=H, metric_evaluator=lambda _: {})


def test_legal_transfer_isolated_and_selection_one_shot() -> None:
    legal = build_legal_transfer_receipt(attempt_id="a4-goal001-20260819T010203Z", mini_status="PASS", mini_metrics={"accuracy": 0.8}, isolation_sha256=H, a5_reserve_intact=True)
    assert legal["selection_accesses"] == 0
    registry = freeze_selection_registry(
        [
            {"role": "static_common_baseline", "system_sha256": H, "license_scope": "commercial_capable", "source_receipt_sha256": H},
            {"role": "research_champion", "system_sha256": "b" * 64, "license_scope": "research_only", "source_receipt_sha256": H},
        ],
        profile_registry_sha256=H,
    )
    comparison = {"comparison_id": "c1", "left_system_sha256": H, "right_system_sha256": "b" * 64, "decision": "TIE", "paired_effect": {"delta": 0}, "win_tie_loss": {"wins": 0, "ties": 1, "losses": 0}}
    receipt = consume_selection_once(registry, [comparison])
    assert receipt["selection_accesses"] == 1
    with pytest.raises(A4SelectionError):
        consume_selection_once(registry, [comparison], selection_accesses=1)


def test_frontier_and_a5_pointer_bundle() -> None:
    frontier = build_selection_frontier([
        {"system_sha256": H, "profile_id": "FAST", "metrics": {"recall_at_100": 0.5}, "latency": {"p95_ms": 10}, "resource": {"cost_usd": 1}},
        {"system_sha256": "b" * 64, "profile_id": "DEEP", "metrics": {"recall_at_100": 0.6}, "latency": {"p95_ms": 12}, "resource": {"cost_usd": 1}},
    ])
    assert frontier["nondominated_system_sha256s"] == ["a" * 64, "b" * 64]
    bundle = build_a5_pointer_bundle(
        attempt_id="a4-goal001-20260819T010203Z", a4_coverage_sha256=H, selection_receipt_sha256=H,
        result_audit_sha256=H, safe_return_sha256=H, final_split_commitment_sha256=H,
        final_input_pointer="a5/final-input", evaluator_handoff_sha256=H,
        evaluator_handoff_pointer="a5/evaluator-handoff", safe_export_manifest_sha256=H,
        git_commit=GIT, git_tree=GIT, git_ref="origin/main", clean_worktree=True,
        pushed_to_origin=True, a5_reserved_usd="8",
        finalists=[
            {"role": "static_common_baseline", "system_sha256": H, "program_sha256": H, "prompt_sha256": H, "representation_sha256": H, "model_sha256": H, "license_sha256": H, "runtime_sha256": H, "license_scope": "commercial_capable"},
            {"role": "research_champion", "system_sha256": "b" * 64, "program_sha256": "c" * 64, "prompt_sha256": H, "representation_sha256": H, "model_sha256": H, "license_sha256": H, "runtime_sha256": H, "license_scope": "research_only"},
        ],
    )
    assert validate_a5_pointer_bundle(bundle)["bundle_sha256"] == bundle["bundle_sha256"]
    with pytest.raises(A4A5HandoffError):
        build_a5_pointer_bundle(
            attempt_id="a4-goal001-20260819T010203Z", a4_coverage_sha256=H, selection_receipt_sha256=H,
            result_audit_sha256=H, safe_return_sha256=H, final_split_commitment_sha256=H,
            final_input_pointer="/private/final", evaluator_handoff_sha256=H,
            evaluator_handoff_pointer="a5/evaluator-handoff", safe_export_manifest_sha256=H,
            git_commit=GIT, git_tree=GIT, git_ref="origin/main", clean_worktree=True,
            pushed_to_origin=True, a5_reserved_usd="8", finalists=[],
        )


def test_pending_a5_template_is_fail_closed() -> None:
    template = build_pending_a5_handoff_template()
    assert validate_pending_a5_handoff_template(template)["status"] == "PENDING_A4_SELECTION"
    assert template["selection_accesses"] == template["final_accesses"] == 0
    with pytest.raises(A4A5HandoffError):
        build_pending_a5_handoff_template(expected_final_query_count=871)
    tampered = {**template, "final_input_pointer": "a5/final"}
    with pytest.raises(A4A5HandoffError):
        validate_pending_a5_handoff_template(tampered)


def test_a5_finalizer_rejects_invalid_pointer_reserve_license_and_plan() -> None:
    kwargs = dict(
        attempt_id="a4-goal001-20260819T010203Z", a4_coverage_sha256=H, selection_receipt_sha256=H,
        result_audit_sha256=H, safe_return_sha256=H, final_split_commitment_sha256=H,
        evaluator_handoff_sha256=H, evaluator_handoff_pointer="a5/evaluator-handoff",
        safe_export_manifest_sha256=H, git_commit=GIT, git_tree=GIT,
        git_ref="origin/main", clean_worktree=True, pushed_to_origin=True,
        finalists=[
            {"role": "static_common_baseline", "system_sha256": H, "program_sha256": H, "prompt_sha256": H, "representation_sha256": H, "model_sha256": H, "license_sha256": H, "runtime_sha256": H, "license_scope": "commercial_capable"},
            {"role": "research_champion", "system_sha256": "b" * 64, "program_sha256": "c" * 64, "prompt_sha256": H, "representation_sha256": H, "model_sha256": H, "license_sha256": H, "runtime_sha256": H, "license_scope": "research_only"},
        ],
    )
    for bad in ("../private/final", "0", "-1"):
        with pytest.raises(A4A5HandoffError):
            build_a5_pointer_bundle(**kwargs, final_input_pointer="a5/final", a5_reserved_usd=bad)
    with pytest.raises(A4A5HandoffError):
        build_a5_pointer_bundle(**kwargs, final_input_pointer="../private/final", a5_reserved_usd="8")
    with pytest.raises(A4A5HandoffError):
        build_a5_pointer_bundle(
            **kwargs, final_input_pointer="a5/final", a5_reserved_usd="8",
            statistical_plan={"paired_bootstrap_resamples": 10_000},
        )
    bad_finalists = [
        kwargs["finalists"][0],
        {**kwargs["finalists"][1], "license_scope": "commercial_capable"},
    ]
    with pytest.raises(A4A5HandoffError):
        build_a5_pointer_bundle(**{**kwargs, "finalists": bad_finalists}, final_input_pointer="a5/final", a5_reserved_usd="8")


def test_a5_pointer_bundle_rejects_unpushed_or_incomplete_binding() -> None:
    finalists = [
        {"role": "static_common_baseline", "system_sha256": H, "program_sha256": H, "prompt_sha256": H, "representation_sha256": H, "model_sha256": H, "license_sha256": H, "runtime_sha256": H, "license_scope": "commercial_capable"},
        {"role": "research_champion", "system_sha256": "b" * 64, "program_sha256": "c" * 64, "prompt_sha256": H, "representation_sha256": H, "model_sha256": H, "license_sha256": H, "runtime_sha256": H, "license_scope": "research_only"},
    ]
    kwargs = dict(
        attempt_id="a4-goal001-20260819T010203Z", a4_coverage_sha256=H, selection_receipt_sha256=H,
        result_audit_sha256=H, safe_return_sha256=H, final_split_commitment_sha256=H,
        final_input_pointer="a5/final", evaluator_handoff_sha256=H,
        evaluator_handoff_pointer="a5/evaluator-handoff", safe_export_manifest_sha256=H,
        git_commit=GIT, git_tree=GIT, git_ref="origin/main", clean_worktree=True,
        pushed_to_origin=True, a5_reserved_usd="8", finalists=finalists,
    )
    with pytest.raises(A4A5HandoffError):
        build_a5_pointer_bundle(**{**kwargs, "clean_worktree": False})
    with pytest.raises(A4A5HandoffError):
        build_a5_pointer_bundle(**{**kwargs, "finalists": [{**finalists[0], "runtime_sha256": None}, finalists[1]]})
