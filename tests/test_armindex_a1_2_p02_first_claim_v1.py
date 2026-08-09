from __future__ import annotations

from pathlib import Path

import pytest

from myis_research.armindex.a1_2_p02_first_claim_v1 import (
    P02FirstClaimError,
    _scan_rows,
    first_claim_segment,
    segment_claims_text,
)
from myis_research.projections.read_model import build_read_model

ROOT = Path(__file__).resolve().parents[1]


def test_numbered_claims_select_first_source_segment_without_dependency_semantics() -> None:
    segments = segment_claims_text("1. A device comprising X.\n2. The device of claim 1 further comprising Y.")
    assert [item.claim_ordinal for item in segments] == [1, 2]
    assert [item.source_number for item in segments] == [1, 2]
    assert first_claim_segment("1. A device.\n2. The device of claim 1.").text == "A device"
    assert all(not hasattr(item, "is_independent") for item in segments)


def test_unmarked_nonempty_source_is_one_declared_primary_segment_not_fallback() -> None:
    segments = segment_claims_text("A single unnumbered source claim")
    assert len(segments) == 1
    assert segments[0].boundary_mode == "single_unmarked_segment"
    assert segments[0].source_number is None
    assert segments[0].text == "A single unnumbered source claim"


@pytest.mark.parametrize("value", [None, "", "  \n\t ", 42, ["claim"]])
def test_missing_or_non_text_claim_source_fails_closed(value: object) -> None:
    assert segment_claims_text(value) == ()
    with pytest.raises(P02FirstClaimError, match="no successfully parsed"):
        first_claim_segment(value)


def test_non_increasing_boundary_markers_are_not_promoted() -> None:
    segments = segment_claims_text("1. First.\n1. Duplicate marker text.\n2. Second.")
    assert [item.source_number for item in segments] == [1, 2]
    assert segments[0].text.startswith("First")


def test_scan_requires_exact_selected_membership_and_records_no_identifiers() -> None:
    selected = {"q1", "q2"}
    result = _scan_rows(
        [
            {"query_id": "q1", "claims_text": "1. First"},
            {"query_id": "q2", "claims_text": "Second"},
            {"query_id": "q3", "claims_text": "Third"},
        ],
        source_role="rep_dev_queries",
        id_field="query_id",
        selected_ids=selected,
    )
    assert result["required_row_count"] == 2
    assert result["available_count"] == 2
    assert result["coverage_fraction"] == 1.0
    assert "q1" not in repr(result)


def test_scan_rejects_missing_selected_member() -> None:
    with pytest.raises(P02FirstClaimError, match="membership is incomplete"):
        _scan_rows(
            [{"query_id": "q1", "claims_text": "First"}],
            source_role="rep_dev_queries",
            id_field="query_id",
            selected_ids={"q1", "q2"},
        )


def test_read_model_projects_p02_pass_and_input_limit_blocker() -> None:
    projection = build_read_model(ROOT)["armindex"]["a1_2_p02_limit_audit"]
    assert projection["validated"] is True
    assert projection["status"] == "BLOCKED_CONTRACT_DEFECT"
    assert projection["p02"]["coverage"]["rep_dev_queries"]["available_count"] == 150
    assert projection["p02"]["coverage"]["corpus"]["available_count"] == 45336
    assert projection["input_limit"]["defect"]["binding_id"] == "ARM-03--P00-TAC-DOC"
    assert projection["input_limit"]["defect"]["truncation_performed"] is False
