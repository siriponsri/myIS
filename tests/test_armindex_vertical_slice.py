from __future__ import annotations

import copy
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pytest

from myis_research.armindex.arms import ARM_IDS, ArmRegistry, ArmUnavailableError
from myis_research.armindex.compiler import RepresentationCompileError, compile_program
from myis_research.armindex.evaluation import SyntheticEvaluationError, evaluate_family_rankings
from myis_research.armindex.fixture import run_synthetic_fixture, validate_fixture_artifacts
from myis_research.kernel.canonical import canonical_sha256
from myis_research.protection import assert_aggregate_only


ROOT = Path(__file__).resolve().parents[1]


def _program(
    *,
    source_fields: tuple[str, ...] = ("title", "abstract"),
    unitization: dict[str, object] | None = None,
    duplicate_policy: str = "preserve_all",
    family_aggregation: str = "maxp",
) -> dict[str, object]:
    unsigned: dict[str, object] = {
        "schema_version": "myis.armindex-representation-program.v1",
        "program_id": "synthetic-test-program",
        "arm_id": "ARM-01",
        "source_fields": list(source_fields),
        "field_order": list(source_fields),
        "field_labels": {field: field.upper() for field in source_fields},
        "unitization": unitization or {"kind": "document", "overlap": 0},
        "normalization": "unicode_nfkc_whitespace_lower",
        "duplicate_policy": duplicate_policy,
        "family_aggregation": family_aggregation,
        "preserve_family_identity": True,
    }
    return {**unsigned, "program_sha256": canonical_sha256(unsigned)}


def _documents() -> list[dict[str, str]]:
    return [
        {
            "family_id": "FAMILY-A",
            "publication_id": "PUB-A1",
            "title": "Cooling controller",
            "abstract": "Battery thermal channels",
        },
        {
            "family_id": "FAMILY-A",
            "publication_id": "PUB-A2",
            "title": "Heat plate",
            "abstract": "Rareword battery cooling",
        },
        {
            "family_id": "FAMILY-B",
            "publication_id": "PUB-B1",
            "title": "Optical sensor",
            "abstract": "Camera alignment fiducial",
        },
    ]


def test_compiler_is_input_order_deterministic_and_preserves_lineage() -> None:
    program = _program()
    forward = compile_program(program, _documents())
    reverse = compile_program(program, reversed(_documents()))

    assert forward.as_dict() == reverse.as_dict()
    assert forward.logical_program_sha256 == program["program_sha256"]
    assert forward.compiled_representation_sha256 != forward.logical_program_sha256
    assert {unit.publication_id for unit in forward.units} == {"PUB-A1", "PUB-A2", "PUB-B1"}
    assert all(unit.source_spans for unit in forward.units)
    assert {span.source_field for unit in forward.units for span in unit.source_spans} == {
        "title",
        "abstract",
    }


def test_compiler_rejects_contract_drift_and_hash_mismatch() -> None:
    program = _program()
    unknown_document = {**_documents()[0], "unexpected": "value"}
    with pytest.raises(RepresentationCompileError, match="document fields"):
        compile_program(program, [unknown_document])

    unknown_program = {**program, "unexpected": "value"}
    with pytest.raises(RepresentationCompileError, match="program fields"):
        compile_program(unknown_program, _documents())

    bad_hash = {**program, "program_sha256": "0" * 64}
    with pytest.raises(RepresentationCompileError, match="hash mismatch"):
        compile_program(bad_hash, _documents())


def test_content_deduplication_never_collapses_distinct_families() -> None:
    program = _program(
        source_fields=("title",),
        duplicate_policy="content_hash_first",
    )
    documents = [
        {"family_id": "FAMILY-A", "publication_id": "PUB-A", "title": "same text"},
        {"family_id": "FAMILY-B", "publication_id": "PUB-B", "title": "same text"},
    ]

    compiled = compile_program(program, documents)

    assert len(compiled.units) == 2
    assert {unit.family_id for unit in compiled.units} == {"FAMILY-A", "FAMILY-B"}
    assert len({unit.content_sha256 for unit in compiled.units}) == 1


def test_bounded_passages_keep_first_and_last_units_and_count_omissions() -> None:
    program = _program(
        source_fields=("body",),
        unitization={"kind": "passage", "logical_size": 2, "overlap": 0},
    )
    document = {
        "family_id": "FAMILY-A",
        "publication_id": "PUB-A",
        "body": "one two three four five six seven eight",
    }

    compiled = compile_program(program, [document], max_units_per_publication=2)

    assert len(compiled.units) == 2
    assert compiled.omitted_unit_count == 3
    assert any("one" in unit.text for unit in compiled.units)
    assert any("eight" in unit.text for unit in compiled.units)


def test_registry_is_fixed_and_dense_arms_fail_closed() -> None:
    registry = ArmRegistry()

    assert ARM_IDS == ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")
    assert tuple(item.arm_id for item in registry.capabilities()) == ARM_IDS
    for arm_id in ARM_IDS[1:]:
        adapter = registry.get(arm_id)
        with pytest.raises(ArmUnavailableError, match="forbidden"):
            adapter.build_index(None)  # type: ignore[arg-type]
        with pytest.raises(ArmUnavailableError, match="blocked"):
            adapter.search(None, case_id="synthetic", text="text", top_k=1)


def test_arm01_aggregates_all_units_at_family_level() -> None:
    compiled = compile_program(_program(), _documents())
    adapter = ArmRegistry().get("ARM-01")

    ranking = adapter.search(
        adapter.build_index(compiled),
        case_id="synthetic-case",
        text="rareword",
        top_k=3,
    )

    assert [hit.family_id for hit in ranking.hits] == ["FAMILY-A", "FAMILY-B"]
    assert ranking.hits[0].publication_id == "PUB-A2"
    assert ranking.hits[0].component_count == 2
    assert ranking.hits[1].score == 0.0


def test_evaluator_returns_only_hand_checked_aggregate_metrics() -> None:
    rankings = {"case-a": ["F2", "F1"], "case-b": ["F3"]}
    judgments = {"case-a": {"F1": 3, "F2": 1}, "case-b": {"F3": 2}}

    result = evaluate_family_rankings(rankings, judgments)
    metrics = {metric["name"]: metric for metric in result["metrics"]}
    case_a_ndcg = (1.0 + 7.0 / math.log2(3)) / (7.0 + 1.0 / math.log2(3))

    assert metrics["recall_at_100"]["value"] == 1.0
    assert metrics["ndcg_at_10"]["value"] == pytest.approx((case_a_ndcg + 1.0) / 2)
    assert metrics["ndcg_at_100"]["value"] == metrics["ndcg_at_10"]["value"]
    assert result["case_count"] == 2
    assert_aggregate_only(result)


@pytest.mark.parametrize(
    ("rankings", "judgments"),
    [
        ({"case-a": ["F1"]}, {"case-b": {"F1": 1}}),
        ({"case-a": ["F1"]}, {"case-a": {"F1": -1}}),
        ({"case-a": ["F1"]}, {"case-a": {"F1": 0}}),
    ],
)
def test_evaluator_rejects_malformed_synthetic_judgments(
    rankings: dict[str, list[str]], judgments: dict[str, dict[str, int]]
) -> None:
    with pytest.raises(SyntheticEvaluationError):
        evaluate_family_rankings(rankings, judgments)


def test_full_fixture_is_byte_deterministic_and_disposable_by_default() -> None:
    first = run_synthetic_fixture()
    second = run_synthetic_fixture()

    assert first.manifest == second.manifest
    assert first.receipt == second.receipt
    assert first.output_persisted is False
    assert second.output_persisted is False
    assert all(value == 0 for value in first.receipt["real_counters"].values())
    assert_aggregate_only(first.receipt)


def test_full_fixture_is_deterministic_across_python_hash_seeds() -> None:
    command = [
        sys.executable,
        "-c",
        (
            "import json; "
            "from myis_research.armindex.fixture import run_synthetic_fixture; "
            "result = run_synthetic_fixture(); "
            "print(json.dumps([result.manifest['manifest_sha256'], result.receipt['receipt_sha256']]))"
        ),
    ]
    base_environment = {
        key: os.environ[key]
        for key in ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PYTHONPATH")
        if key in os.environ
    }
    outputs = []
    for seed in ("1", "8675309"):
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env={**base_environment, "PYTHONHASHSEED": seed},
            check=True,
            capture_output=True,
            text=True,
        )
        outputs.append(json.loads(completed.stdout))

    assert outputs[0] == outputs[1]


def test_explicit_fixture_output_is_write_once_and_validated(tmp_path) -> None:
    output = tmp_path / "fixture-output"

    result = run_synthetic_fixture(output)

    assert result.output_persisted is True
    manifest = json.loads((output / "manifest.json").read_text(encoding="ascii"))
    receipt = json.loads((output / "receipt.json").read_text(encoding="ascii"))
    validate_fixture_artifacts(manifest, receipt)
    assert manifest == result.manifest
    assert receipt == result.receipt
    with pytest.raises(FileExistsError, match="must be empty"):
        run_synthetic_fixture(output)


def test_fixture_validation_rejects_manifest_and_receipt_mutation() -> None:
    result = run_synthetic_fixture()
    manifest = copy.deepcopy(result.manifest)
    receipt = copy.deepcopy(result.receipt)
    manifest["counts"]["compiled_units"] += 1
    with pytest.raises(ValueError, match="manifest_sha256"):
        validate_fixture_artifacts(manifest, receipt)

    receipt = copy.deepcopy(result.receipt)
    receipt["real_counters"]["measured_runs"] = 1
    with pytest.raises(ValueError, match="receipt_sha256"):
        validate_fixture_artifacts(result.manifest, receipt)
