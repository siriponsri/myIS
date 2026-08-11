from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from jsonschema import Draft202012Validator

from myis_research.armindex.autoindex import (
    AutoIndexState,
    advance_autoindex,
    build_autoindex_terminal_receipt,
    validate_autoindex_batch,
)
from myis_research.armindex.contracts.models import AutoIndexBatch, AutoIndexCandidate
from myis_research.kernel.canonical import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]
TYPED_BATCH_SCHEMA = "myis.armindex-autoindex-batch.v1"
EXECUTION_BATCH_SCHEMA = "myis.armindex-autoindex-execution-batch.v1"
EXECUTION_TERMINAL_SCHEMA = "myis.armindex-autoindex-execution-terminal.v1"


def _digest(label: str) -> str:
    return canonical_sha256({"label": label})


def _load_schema(name: str) -> dict[str, object]:
    return json.loads((ROOT / "schemas" / "armindex" / name).read_text(encoding="utf-8"))


def _state() -> AutoIndexState:
    return AutoIndexState(
        arm_id="ARM-01",
        incumbent_candidate_id="static-incumbent",
        incumbent_program_sha256=_digest("incumbent"),
        incumbent_primary=Decimal("0.200000000000"),
        frozen_bindings_sha256=_digest("bindings"),
    )


def _execution_batch(state: AutoIndexState, iteration: int) -> dict[str, object]:
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
        "schema_version": EXECUTION_BATCH_SCHEMA,
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


def _scores(batch: dict[str, object]) -> dict[str, str]:
    candidates = batch["candidates"]
    assert isinstance(candidates, list)
    return {
        str(candidate["candidate_id"]): score
        for candidate, score in zip(candidates, ("0.20", "0.19", "0.18", "0.17"), strict=True)
    }


def _typed_batch() -> AutoIndexBatch:
    roles = ("exploit", "matched_ablation", "orthogonal", "diversity")
    candidates = tuple(
        AutoIndexCandidate(
            schema_version="myis.armindex-autoindex-candidate.v1",
            contract_id=f"candidate-contract-{index}",
            evidence_class="synthetic_fixture",
            scientific_authority=False,
            commercial_status="commercial_capable",
            protected_data_accessed=False,
            candidate_id=f"candidate-{index}",
            arm_id="ARM-01",
            parent_candidate_id="incumbent-1",
            hypothesis_id=f"hypothesis-{index}",
            hypothesis=f"fixture hypothesis {index}",
            role=role,
            declared_axis="field_order",
            representation_program_sha256=_digest(f"typed-program-{index}"),
            scientific_payload_sha256=_digest(f"typed-payload-{index}"),
            axis_values={"field_order": index},
        )
        for index, role in enumerate(roles, start=1)
    )
    return AutoIndexBatch(
        schema_version=TYPED_BATCH_SCHEMA,
        contract_id="typed-batch-contract",
        evidence_class="synthetic_fixture",
        scientific_authority=False,
        commercial_status="commercial_capable",
        protected_data_accessed=False,
        batch_id="typed-batch-1",
        arm_id="ARM-01",
        iteration=1,
        incumbent_candidate_id="incumbent-1",
        status="frozen_before_evaluation",
        candidates=candidates,
        budget_counters={"candidates": 4},
    )


def test_autoindex_execution_artifacts_validate_against_distinct_schemas() -> None:
    batch_schema = _load_schema("autoindex-execution-batch.v1.json")
    terminal_schema = _load_schema("autoindex-execution-terminal.v1.json")
    Draft202012Validator.check_schema(batch_schema)
    Draft202012Validator.check_schema(terminal_schema)

    state = _state()
    first = _execution_batch(state, 1)
    assert validate_autoindex_batch(first) == first
    assert not list(Draft202012Validator(batch_schema).iter_errors(first))

    first_decision = advance_autoindex(
        state,
        first,
        _scores(first),
        remaining_budget=True,
        grounded_axes_remaining=True,
    )
    second = _execution_batch(first_decision.state, 2)
    final_decision = advance_autoindex(
        first_decision.state,
        second,
        _scores(second),
        remaining_budget=True,
        grounded_axes_remaining=True,
    )
    receipt = build_autoindex_terminal_receipt(
        final_decision.state,
        evidence_ids=("fixture-b01", "fixture-b02"),
    )
    assert receipt["schema_version"] == EXECUTION_TERMINAL_SCHEMA
    assert not list(Draft202012Validator(terminal_schema).iter_errors(receipt))


def test_typed_autoindex_batch_keeps_its_existing_schema_identity() -> None:
    typed_schema = _load_schema("optimization-contracts.v1.json")
    execution_schema = _load_schema("autoindex-execution-batch.v1.json")
    typed = _typed_batch().model_dump(mode="json")
    execution = _execution_batch(_state(), 1)

    assert typed["schema_version"] == TYPED_BATCH_SCHEMA
    assert not list(Draft202012Validator(typed_schema).iter_errors(typed))
    assert execution["schema_version"] == EXECUTION_BATCH_SCHEMA
    assert execution["schema_version"] != typed["schema_version"]
    assert list(Draft202012Validator(typed_schema).iter_errors(execution))
    assert list(Draft202012Validator(execution_schema).iter_errors(typed))
