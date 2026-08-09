from __future__ import annotations

import json
from pathlib import Path

from myis_research.projections.read_model import build_read_model

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_repair_and_additive_compiler_integration_are_validated() -> None:
    model = build_read_model(ROOT)
    projection = model["armindex"]["a1_2_dense_overflow"]

    assert projection["validated"] is True
    assert projection["repair_frozen"] is True
    assert projection["status"] in {
        "PASS_PROTECTED_COMPILER_INTEGRATION_LOCAL_ONLY",
        "LOCAL_ADOPTION_INPUTS_VALIDATED_PENDING_LIVE_PROVIDER",
    }
    assert projection["compiler_integration_status"] == "PASS"
    assert projection["compiled_bindings_25_of_25"] == "PASS"
    assert projection["protected_handoff_status"] == "PASS"
    assert projection["transfer_receipt_status"] == "PASS"
    assert projection["requirements"]["compatible_cells_25_of_25"] is True
    assert projection["requirements"]["zero_silent_truncation"] is True
    assert projection["safety"]["retrieval_started"] is False
    assert (
        projection["publication_method_disclosure"]["publication_claim_authorized"]
        is False
    )


def test_dense_overflow_projection_exposes_only_bound_aggregate_artifacts() -> None:
    model = build_read_model(ROOT)
    projection = model["armindex"]["a1_2_dense_overflow"]
    for key in (
        "contract_file_sha256",
        "inventory_file_sha256",
        "composition_file_sha256",
        "figure_png_sha256",
        "figure_svg_sha256",
    ):
        assert isinstance(projection[key], str)
        assert len(projection[key]) == 64
    assert projection["scope"]["all_program_arm_cells_compatible"] == 25
    assert projection["scope"]["dense_program_arm_cells"] == 20

    report = (
        ROOT
        / "obsidian_report/05_Research_History/ArmIndex/A1_2_DENSE_OVERFLOW_REPAIR_COMPILER_BLOCKER.md"
    )
    assert report.is_file()
    text = report.read_text(encoding="utf-8")
    assert "repair frozen, compiler integration PASS" in text
    assert "No vector, encoder-parity" in text

    contract = json.loads(
        (ROOT / projection["contract_uri"]).read_text(encoding="ascii")
    )
    assert contract["owner_decision"]["allow_measured_retrieval"] is False
