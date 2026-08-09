from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from myis_research.armindex import a1_2_claim_parser_audit_v1 as audit
from myis_research.projections.read_model import (
    _a12_rep_harness_claim_audit_projection,
    build_read_model,
)
from myis_research.report_cli import projection_report_contents

ROOT = Path(__file__).resolve().parents[1]


def test_literal_constant_reads_parser_versions() -> None:
    source = 'SCHEMA_VERSION = "claim-structure-v1"\nPARSER_VERSION = "parser-v1"\n'
    assert audit._literal_constant(source, "SCHEMA_VERSION") == "claim-structure-v1"
    assert audit._literal_constant(source, "PARSER_VERSION") == "parser-v1"


def test_scan_emits_counts_and_hash_only(monkeypatch) -> None:
    monkeypatch.setattr(
        audit,
        "iter_arrow_rows",
        lambda _paths, _fields: iter([{"claims_text": "first|second"}, {"claims_text": None}]),
    )
    result = audit._scan(
        (Path("fixture.arrow"),),
        split_claims=lambda value: [] if value is None else value.split("|"),
        detect_dependency=lambda **values: SimpleNamespace(is_independent="second" not in values["claim_text_en"]),
        source_role="fixture",
    )
    assert result["row_count"] == 2
    assert result["candidate_record_count"] == 2
    assert result["inferred_independent_count"] == 1
    assert result["inferred_dependent_count"] == 1
    assert result["independence_ground_truth_count"] == 0
    assert len(result["output_manifest_sha256"]) == 64


def test_read_model_and_generated_note_include_validated_audit() -> None:
    projection = _a12_rep_harness_claim_audit_projection(ROOT)
    assert projection["validated"] is True
    assert projection["status"] == "SPLIT_PASS_P02_BLOCKED"
    model = build_read_model(ROOT)
    outputs = projection_report_contents(ROOT, model)
    note = ROOT / "obsidian_report/05_Research_History/ArmIndex/A1_2_REP_HARNESS_SPLIT_AUDIT.md"
    assert note in outputs
    assert "## Objective" in outputs[note]
    assert "## Evidence Links" in outputs[note]
    assert "ADDITIVE_PRE_MEASUREMENT_P02_FIRST_CLAIM_REPAIR" in outputs[note]
