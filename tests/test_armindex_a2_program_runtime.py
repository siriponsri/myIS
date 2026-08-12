from __future__ import annotations

from myis_research.armindex.a1_2_measured_executor_v16 import LogicalInput, PhysicalInput
from myis_research.armindex.a2_program_runtime import aggregate_family_scores, compile_program


def _program(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "program_id": "a2-test-program",
        "source_fields": ["title", "abstract"],
        "field_order": ["abstract", "title"],
        "field_labels": {"abstract": "A: ", "title": "T: "},
        "unitization": {"kind": "passage", "logical_size": 3, "overlap": 1},
        "normalization": "unicode_nfkc_whitespace_lower",
        "duplicate_policy": "content_hash_first",
        "family_aggregation": "avg_top3",
    }
    value.update(changes)
    return value


def test_compile_program_preserves_literal_labels_order_and_final_partial() -> None:
    rows = [
        {"family_token": "F-" + "1" * 32, "publication_token": "P-1", "title": "  HELLO ", "abstract": "Ａ  B C D"},
    ]
    compiled = compile_program(rows, _program())
    assert [item.physical_inputs[0].text for item in compiled.units] == [
        "A: a b",
        "b c d",
        "d T: hello",
    ]


def test_compile_program_duplicate_modes_and_family_unitization() -> None:
    rows = [
        {"family_token": "F-" + "1" * 32, "publication_token": "P-1", "title": "same", "abstract": "text"},
        {"family_token": "F-" + "2" * 32, "publication_token": "P-2", "title": "same", "abstract": "text"},
    ]
    deduped = compile_program(rows, _program(unitization={"kind": "family", "logical_size": None, "overlap": 0}, family_aggregation="single_unit"))
    preserved = compile_program(rows, _program(unitization={"kind": "family", "logical_size": None, "overlap": 0}, family_aggregation="single_unit", duplicate_policy="preserve_all"))
    # Equal text in different families must not collapse family identity.
    assert len(deduped.units) == 2
    assert len(preserved.units) == 2


def test_family_aggregation_avg_top3_and_lexical_tie() -> None:
    units = tuple(
        LogicalInput(f"u{i}", family, None, (PhysicalInput("x", 1),))
        for i, family in enumerate(("F-b", "F-b", "F-b", "F-b", "F-a"))
    )
    ranks = aggregate_family_scores(units, (4.0, 3.0, 2.0, 1.0, 3.0), method="avg_top3")
    assert [item.family_token for item in ranks] == ["F-a", "F-b"]
    assert ranks[1].score == 3.0
