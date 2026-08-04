from __future__ import annotations

import ast
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from myis_research.armindex.autoindex import (
    AutoIndexError,
    AutoIndexState,
    advance_autoindex,
    build_autoindex_terminal_receipt,
    strict_primary_improvement,
    validate_aggregate_feedback,
    validate_autoindex_batch,
)
from myis_research.armindex.complementarity import (
    ComplementarityError,
    evaluate_complementarity_gate,
    pairwise_overlap,
    same_depth_union,
)
from myis_research.armindex.fusion import fuse_rankings
from myis_research.armindex.harnessopt import (
    HarnessOptError,
    detect_forbidden_mutations,
    validate_harness_batch,
    validate_harness_configuration,
)
from myis_research.armindex.runtime import (
    RuntimeContractError,
    build_execution_plan,
    validate_execution_plan,
    validate_runtime_signals,
)
from myis_research.armindex.transfer import (
    TransferStatus,
    build_transfer_matrix,
    classify_transfer,
)
from myis_research.kernel.canonical import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]


def _digest(label: str) -> str:
    return canonical_sha256({"label": label})


def _autoindex_batch(state: AutoIndexState, iteration: int) -> dict[str, object]:
    roles = ("exploit", "matched_ablation", "orthogonal", "diversity")
    ids = [f"a2-arm01-i{iteration:02d}-c{index:02d}" for index in range(1, 5)]
    candidates = []
    for index, (candidate_id, role) in enumerate(zip(ids, roles, strict=True)):
        compiled = _digest(f"compiled-{iteration}-{index}")
        candidates.append(
            {
                "candidate_id": candidate_id,
                "role": role,
                "hypothesis": f"fixture hypothesis {iteration}-{index}",
                "declared_axis": "source_fields" if index < 2 else "unitization",
                "program_sha256": _digest(f"program-{iteration}-{index}"),
                "compiled_sha256": compiled,
                "scientific_payload_sha256": _digest(f"payload-{iteration}-{index}"),
                "matched_ablation_id": ids[1] if index == 0 else ids[0] if index == 1 else None,
                "compile_sha256s": [compiled, compiled],
                "verifier_status": "accepted",
            }
        )
    batch: dict[str, object] = {
        "schema_version": "myis.armindex-autoindex-batch.v1",
        "batch_id": f"a2-arm01-i{iteration:02d}",
        "arm_id": state.arm_id,
        "iteration": iteration,
        "incumbent_program_sha256": state.incumbent_program_sha256,
        "frozen_bindings_sha256": state.frozen_bindings_sha256,
        "status": "frozen_before_evaluation",
        "candidates": candidates,
    }
    batch["batch_sha256"] = canonical_sha256(batch)
    return batch


def _scores(batch: dict[str, object], values: tuple[str, str, str, str]) -> dict[str, str]:
    candidates = batch["candidates"]
    assert isinstance(candidates, list)
    return {
        str(candidate["candidate_id"]): value
        for candidate, value in zip(candidates, values, strict=True)
    }


def test_autoindex_exact_four_strict_stop_and_immutable_terminal() -> None:
    state = AutoIndexState(
        arm_id="ARM-01",
        incumbent_candidate_id="static-incumbent",
        incumbent_program_sha256=_digest("incumbent"),
        incumbent_primary=Decimal("0.200000000000"),
        frozen_bindings_sha256=_digest("bindings"),
    )
    assert not strict_primary_improvement("0.2000000000004", "0.200000000000")

    first = _autoindex_batch(state, 1)
    validate_autoindex_batch(first)
    decision = advance_autoindex(
        state,
        first,
        _scores(first, ("0.20", "0.19", "0.18", "0.17")),
        remaining_budget=True,
        grounded_axes_remaining=True,
    )
    assert decision.next_action == "run_required_batch"
    second = _autoindex_batch(decision.state, 2)
    decision = advance_autoindex(
        decision.state,
        second,
        _scores(second, ("0.20", "0.19", "0.18", "0.17")),
        remaining_budget=True,
        grounded_axes_remaining=True,
    )
    assert decision.state.terminal_state == "STOP_WITH_EVIDENCE_FLAT_REPRESENTATION_SURFACE"
    receipt = build_autoindex_terminal_receipt(decision.state, evidence_ids=("fixture-b01", "fixture-b02"))
    assert receipt["protected_data_accessed"] is False
    with pytest.raises(AutoIndexError, match="terminal AutoIndex state is immutable"):
        advance_autoindex(
            decision.state,
            second,
            _scores(second, ("0.21", "0.19", "0.18", "0.17")),
            remaining_budget=True,
            grounded_axes_remaining=True,
        )


def test_autoindex_strict_improvement_admits_one_third_batch_and_rejects_protected_feedback() -> None:
    state = AutoIndexState(
        arm_id="ARM-01",
        incumbent_candidate_id="static-incumbent",
        incumbent_program_sha256=_digest("incumbent-2"),
        incumbent_primary=Decimal("0.20"),
        frozen_bindings_sha256=_digest("bindings-2"),
    )
    first = _autoindex_batch(state, 1)
    first_decision = advance_autoindex(
        state,
        first,
        _scores(first, ("0.21", "0.20", "0.19", "0.18")),
        remaining_budget=True,
        grounded_axes_remaining=True,
    )
    second = _autoindex_batch(first_decision.state, 2)
    second_decision = advance_autoindex(
        first_decision.state,
        second,
        _scores(second, ("0.21", "0.20", "0.19", "0.18")),
        remaining_budget=True,
        grounded_axes_remaining=True,
    )
    assert second_decision.next_action == "run_gated_third_batch"
    third = _autoindex_batch(second_decision.state, 3)
    final = advance_autoindex(
        second_decision.state,
        third,
        _scores(third, ("0.22", "0.21", "0.20", "0.19")),
        remaining_budget=True,
        grounded_axes_remaining=True,
    )
    assert final.state.terminal_state == "FREEZE_ARM_PROGRAM"

    feedback = {
        "schema_version": "myis.armindex-autoindex-feedback.v1",
        "arm_id": "ARM-01",
        "aggregate_metrics": [],
        "protected_data_accessed": False,
    }
    feedback["feedback_sha256"] = canonical_sha256(feedback)
    validate_aggregate_feedback(feedback)
    leaked = {**feedback, "qrels": {"fixture-query": ["family-a"]}}
    leaked["feedback_sha256"] = canonical_sha256(
        {key: value for key, value in leaked.items() if key != "feedback_sha256"}
    )
    with pytest.raises(AutoIndexError, match="protected payload key"):
        validate_aggregate_feedback(leaked)


def test_fusion_and_same_depth_complementarity_are_order_independent() -> None:
    rankings = {
        "ARM-02": ["family-b", "family-c", "family-d"],
        "ARM-01": ["family-a", "family-b", "family-c"],
    }
    first = fuse_rankings(rankings, method="rrf", limit=4)
    second = fuse_rankings(dict(reversed(list(rankings.items()))), method="rrf", limit=4)
    assert first == second
    assert first[0]["family_id"] == "family-b"
    assert same_depth_union(rankings, depth=3) == (
        "family-a",
        "family-b",
        "family-c",
        "family-d",
    )
    overlap = pairwise_overlap(rankings, depth=3)
    assert overlap[0]["intersection_count"] == 2
    with pytest.raises(ComplementarityError, match="same requested candidate depth"):
        same_depth_union({"ARM-01": ["a"], "ARM-02": ["b", "c"]}, depth=2)

    gate = evaluate_complementarity_gate(
        {
            "schema_version": "myis.armindex-complementarity-gate-input.v1",
            "best_arm_recall_at_100": 0.20,
            "union_recall_at_100": 0.20,
            "union_recall_at_1000": 0.40,
            "best_arm_recall_at_1000": 0.38,
            "maximum_unique_query_fraction": 0.01,
            "fixed_union_frontier_acceptable": False,
        }
    )
    assert gate["status"] == "promote_multi_arm_harness"


def test_transfer_matrix_classification_and_compilation_are_deterministic() -> None:
    assert classify_transfer(
        required_fields=("title",),
        target_fields=("title", "abstract"),
        logical_unitization="section",
        supported_unitizations=("document",),
        safe_constraint_available=True,
    ) is TransferStatus.ADAPTER_CONSTRAINED_COMPILATION
    programs = [
        {"program_id": "program-b", "program_sha256": _digest("program-b")},
        {"program_id": "program-a", "program_sha256": _digest("program-a")},
    ]
    adapters = [{"arm_id": "ARM-02"}, {"arm_id": "ARM-01"}]

    def compile_fixture(program: dict[str, object], adapter: dict[str, object]) -> dict[str, object]:
        constrained = adapter["arm_id"] == "ARM-02"
        return {
            "target_arm_id": adapter["arm_id"],
            "status": (
                "adapter_constrained_compilation" if constrained else "exact_logical_transfer"
            ),
            "logical_program_sha256": program["program_sha256"],
            "compiled_sha256": _digest(f"{program['program_id']}-{adapter['arm_id']}"),
            "constraints_applied": ["bounded_input"] if constrained else [],
            "reason": "adapter input cap" if constrained else "logical program supported",
        }

    first = build_transfer_matrix(programs, adapters, compiler=compile_fixture)
    second = build_transfer_matrix(reversed(programs), reversed(adapters), compiler=compile_fixture)
    assert first == second
    assert [row["source_program_id"] for row in first["rows"]] == [
        "program-a",
        "program-a",
        "program-b",
        "program-b",
    ]


def _harness_config(*, harness_id: str = "harness-fixture", bindings: str | None = None) -> dict[str, object]:
    config: dict[str, object] = {
        "schema_version": "myis.armindex-harness.v2",
        "harness_id": harness_id,
        "profile": "FAST",
        "frozen_bindings_sha256": bindings or _digest("harness-bindings"),
        "arm_ids": ["ARM-01", "ARM-02"],
        "invocation_order": ["ARM-01", "ARM-02"],
        "execution_mode": "sequential",
        "initial_depth_by_arm": {"ARM-01": 100, "ARM-02": 50},
        "maximum_depth_by_arm": {"ARM-01": 100, "ARM-02": 100},
        "fusion": {
            "method": "rrf",
            "rrf_k": 60,
            "weights": {"ARM-01": 1.0, "ARM-02": 1.0},
        },
        "routing": [
            {
                "feature": "query_length",
                "operator": "gte",
                "threshold": 10,
                "activate_arm_id": "ARM-02",
            }
        ],
        "early_stop": {"max_escalations": 1, "score_margin": 0.1, "rank_stability": 0.9},
        "cache_policy": "frozen_read_only",
        "latency_profile": "fast",
        "runtime_features": ["cache_state", "query_length"],
    }
    config["config_sha256"] = canonical_sha256(config)
    return config


def test_harness_forbidden_mutation_exact_batch_and_label_free_runtime() -> None:
    config = _harness_config()
    validate_harness_configuration(config)
    changed = deepcopy(config)
    changed["frozen_bindings_sha256"] = _digest("mutated-binding")
    assert detect_forbidden_mutations(config, changed) == ("frozen_bindings_sha256",)
    injected = {**config, "qrels": {}}
    with pytest.raises(HarnessOptError):
        validate_harness_configuration(injected)

    roles = (
        "quality_exploit",
        "cost_latency_ablation",
        "routing_hypothesis",
        "diversity_profile",
    )
    ids = [f"harness-i01-c{index:02d}" for index in range(1, 5)]
    candidates = []
    for index, (candidate_id, role) in enumerate(zip(ids, roles, strict=True)):
        candidates.append(
            {
                "candidate_id": candidate_id,
                "role": role,
                "hypothesis": f"harness fixture hypothesis {index}",
                "matched_ablation_id": ids[1] if index == 0 else ids[0] if index == 1 else None,
                "scientific_payload_sha256": _digest(f"harness-payload-{index}"),
                "configuration": _harness_config(
                    harness_id=f"harness-fixture-{index}",
                    bindings=str(config["frozen_bindings_sha256"]),
                ),
                "verifier_status": "accepted",
            }
        )
    batch: dict[str, object] = {
        "schema_version": "myis.armindex-harness-batch.v1",
        "batch_id": "harness-i01",
        "iteration": 1,
        "frozen_bindings_sha256": config["frozen_bindings_sha256"],
        "status": "frozen_before_evaluation",
        "candidates": candidates,
    }
    batch["batch_sha256"] = canonical_sha256(batch)
    validate_harness_batch(batch)
    invalid = deepcopy(batch)
    invalid["candidates"] = candidates[:3]
    invalid["batch_sha256"] = canonical_sha256(
        {key: value for key, value in invalid.items() if key != "batch_sha256"}
    )
    with pytest.raises(HarnessOptError, match="exactly four"):
        validate_harness_batch(invalid)

    signals = {"query_length": 20, "cache_state": "miss"}
    first = build_execution_plan(config, signals)
    second = build_execution_plan(config, dict(reversed(list(signals.items()))))
    assert first == second
    assert [item["arm_id"] for item in first["actions"]] == ["ARM-01", "ARM-02"]
    validate_execution_plan(first)
    with pytest.raises(RuntimeContractError, match="IN/OUT labels"):
        validate_runtime_signals({"language_hint": "OUT"}, enabled_features=["language_hint"])
    with pytest.raises(RuntimeContractError, match="IN/OUT labels"):
        validate_runtime_signals({"language_hint": "en-OUT"}, enabled_features=["language_hint"])
    with pytest.raises(RuntimeContractError, match="exactly"):
        build_execution_plan(config, {**signals, "split_label": "OUT"})


def test_phase_scaffold_has_no_historical_runtime_or_dynamic_code_imports() -> None:
    module_names = (
        "autoindex.py",
        "fusion.py",
        "transfer.py",
        "complementarity.py",
        "harnessopt.py",
        "runtime.py",
    )
    forbidden_imports = (
        "myis_research.p2",
        "myis_research.scope",
        "myis_research.archive",
    )
    forbidden_calls = {"eval", "exec", "compile", "__import__"}
    for name in module_names:
        path = ROOT / "src" / "myis_research" / "armindex" / name
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported = []
        called = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                called.append(node.func.id)
        assert not any(
            dependency.startswith(forbidden)
            for dependency in imported
            for forbidden in forbidden_imports
        ), path
        assert not (set(called) & forbidden_calls), path
