from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from myis_research.armindex import a1_2_owner_local_protected_compiler_v15 as compiler
from myis_research.armindex import (
    a1_2_protected_compiler_integration_audit_v15 as audit,
)
from myis_research.kernel.canonical import canonical_sha256, file_sha256

ROOT = Path(__file__).resolve().parents[1]


def _read(relative: Path | str) -> dict[str, object]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_current_v15_integration_contract_is_strictly_valid() -> None:
    value = compiler._validate_integration(ROOT)
    implementation = value["implementation"]
    assert value["contract_sha256"] == canonical_sha256(
        {key: item for key, item in value.items() if key != "contract_sha256"}
    )
    assert implementation["source_sha256"] == file_sha256(
        ROOT / str(implementation["source_uri"])
    )
    assert implementation["materializer_source_sha256"] == file_sha256(
        ROOT / str(implementation["materializer_source_uri"])
    )


def test_v15_preserves_historical_lineage_and_v13_outcomes() -> None:
    integration = compiler._validate_integration(ROOT)
    request, program_set, publication = compiler._validate_lineage(ROOT, integration)
    assert request["request_sha256"] == integration["preserved_lineage"]["v11_request_sha256"]
    assert program_set["program_set_sha256"] == integration["preserved_lineage"]["v11_program_set_sha256"]
    outcomes = publication["analysis"]["outcomes"]
    assert outcomes["primary"] == "out_recall_at_100"
    assert outcomes["secondary"] == ["out_ndcg_at_100", "out_ndcg_at_10"]


def test_v15_binds_the_exact_25_cell_topology() -> None:
    schema = _read(compiler.BINDING_SCHEMA_PATH)
    expected = schema["properties"]["expected_bindings"]["const"]
    assert expected == [
        {"arm_id": arm_id, "program_slot": program_slot}
        for arm_id in ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")
        for program_slot in ("P00", "P01", "P02", "P03", "P04")
    ]


def test_v15_templates_match_the_frozen_composition_audit() -> None:
    composition = _read("outputs/audits/armindex/a1.2-dense-overflow-composition-20260808.json")
    for arm_id in ("ARM-02", "ARM-03", "ARM-04", "ARM-05"):
        lock = _read(f"control/armindex/a1.2/model-locks/{arm_id}.v1.json")
        templates = {
            "corpus": compiler._template_from_lock(lock, side="corpus"),
            "rep_dev_queries": compiler._template_from_lock(lock, side="rep_dev_queries"),
        }
        assert canonical_sha256(templates) == composition["bindings"]["dense_arms"][arm_id][
            "template_sha256"
        ]


def test_weighted_recomposition_applies_token_weighting_and_l2() -> None:
    result = compiler.aggregate_physical_window_vectors(
        "ARM-03",
        vectors=((1.0, 0.0), (0.0, 1.0)),
        source_token_counts=(3, 1),
    )
    assert result == pytest.approx((3 / math.sqrt(10), 1 / math.sqrt(10)))
    assert math.sqrt(sum(value * value for value in result)) == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("arm_id", "vectors", "counts", "message"),
    [
        ("ARM-01", ((1.0,),), (1,), "dense arm"),
        ("ARM-02", (), (), "incomplete"),
        ("ARM-02", ((1.0,), (1.0, 2.0)), (1, 1), "dimensions"),
        ("ARM-02", ((1.0,),), (0,), "weights"),
        ("ARM-02", ((float("nan"),),), (1,), "non-finite"),
        ("ARM-02", ((0.0, 0.0),), (1,), "L2-normalized"),
    ],
)
def test_weighted_recomposition_rejects_invalid_inputs(
    arm_id: str,
    vectors: tuple[tuple[float, ...], ...],
    counts: tuple[int, ...],
    message: str,
) -> None:
    with pytest.raises(compiler.ProtectedCompilationV15Error, match=message):
        compiler.aggregate_physical_window_vectors(arm_id, vectors, counts)


def test_p02_successor_has_no_independence_semantics() -> None:
    integration = compiler._validate_integration(ROOT)
    assert integration["p02_successor"] == {
        "topology_slot": "P02",
        "original_program_id": "P02-CLAIM1",
        "executable_program_id": "P02-FIRST-CLAIM",
        "contract_uri": "control/armindex/a1.2/p02-first-claim-repair.v1.json",
        "independence_or_dependency_status": "not_inferred_not_asserted_not_published",
        "fallback": False,
    }


def test_v14_compatibility_evidence_is_a_complete_zero_drop_pass() -> None:
    integration = compiler._validate_integration(ROOT)
    v14 = compiler._validate_v14(ROOT, integration)
    inventory, composition = compiler._validate_audits(ROOT, integration, v14)
    assert inventory["scope"]["program_arm_cell_count"] == 25
    assert composition["scope"]["all_program_arm_cells_compatible"] == 25
    requirements = composition["requirements"]
    assert requirements["compatible_cells_25_of_25"] is True
    assert requirements["every_physical_window_within_limit"] is True
    assert requirements["rep_dev_query_coverage_fraction"] == 1.0
    assert requirements["required_corpus_logical_unit_coverage_fraction"] == 1.0
    assert requirements["zero_fallback"] is True
    assert requirements["zero_omitted_source_tokens"] is True
    assert requirements["zero_silent_truncation"] is True


def test_current_aggregate_only_v15_audit_is_valid() -> None:
    value = _read("outputs/audits/armindex/a1.2-protected-compiler-integration-20260809-v15.json")
    result = audit.validate_audit(ROOT, value)
    assert result["compiled_bindings"] == 25
    assert result["zero_silent_truncation"] is True
    assert result["protected_boundary"] == "PASS"


def test_rehashed_v15_audit_cannot_change_the_integration_binding() -> None:
    value = _read("outputs/audits/armindex/a1.2-protected-compiler-integration-20260809-v15.json")
    value["integration"]["contract_sha256"] = "0" * 64
    value["audit_sha256"] = canonical_sha256(
        {key: item for key, item in value.items() if key != "audit_sha256"}
    )
    with pytest.raises(audit.ProtectedCompilerAuditV15Error, match="integration binding"):
        audit.validate_audit(ROOT, value)
