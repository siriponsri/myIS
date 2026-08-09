from __future__ import annotations

from pathlib import Path

import pytest

from myis_research.armindex.a1_2_dense_overflow_inventory_v1 import (
    DenseOverflowInventoryError,
    _cell,
    _Counts,
    _lengths,
    _logical_units,
    _template,
)
from myis_research.armindex.scientific_common_programs_v11 import compile_common_program


def _row() -> dict[str, str]:
    return {
        "title_en": "Synthetic title",
        "abstract_en": "Synthetic abstract",
        "claims_text": "1. First claim; 2. Second claim",
    }


def test_logical_inventory_preserves_slots_and_additive_p02_semantics() -> None:
    units = _logical_units(_row(), source_id="safe-synthetic-source")
    assert set(units) == {
        "P00-TAC-DOC",
        "P01-TA-DOC",
        "P02-CLAIM1",
        "P03-PASSAGE",
        "P04-SECTION-MULTIVIEW",
    }
    assert units["P02-CLAIM1"] == ("First claim",)
    assert len(units["P04-SECTION-MULTIVIEW"]) == 3


def test_unchanged_slot_text_matches_frozen_v11_compiler() -> None:
    row = _row()
    units = _logical_units(row, source_id="safe-synthetic-source")
    record = {
        "family_token": "F-" + "a" * 32,
        "publication_token": "P-" + "b" * 32,
        "publication_ordinal": 0,
        **row,
        "claims": [],
    }
    for program_id in (
        "P00-TAC-DOC",
        "P01-TA-DOC",
        "P03-PASSAGE",
        "P04-SECTION-MULTIVIEW",
    ):
        compiled = compile_common_program(program_id, (record,))
        assert units[program_id] == tuple(unit.text for unit in compiled.units)


def test_templates_bind_exact_frozen_query_and_document_formats() -> None:
    assert _template("ARM-03", side="corpus").startswith("encode document")
    assert _template("ARM-03", side="rep_dev_queries").startswith("encode query")
    assert _template("ARM-04", side="rep_dev_queries") == "query: {text}"
    assert "Query:{text}" in _template("ARM-05", side="rep_dev_queries")
    assert _template("ARM-02", side="corpus") == "{text}"


def test_batch_lengths_and_incidence_are_exact() -> None:
    class Tokenizer:
        def __call__(self, values: list[str], **_kwargs: object) -> dict[str, list[list[int]]]:
            return {"input_ids": [list(range(len(value.split()) + 2)) for value in values]}

    assert _lengths(Tokenizer(), ["one two", "three"]) == [4, 3]
    corpus = _Counts(logical_units=4, overflow_units=1, maximum_rendered_tokens=12)
    queries = _Counts(logical_units=2, overflow_units=1, maximum_rendered_tokens=9)
    cell = _cell(corpus, queries)
    assert cell["corpus"]["overflow_incidence"] == 0.25
    assert cell["combined"]["overflow_incidence"] == pytest.approx(1 / 3)
    assert cell["raw_compatibility"] == "OVERFLOW_REQUIRES_AUTHORIZED_COMPOSITION"


def test_empty_or_invalid_tokenizer_output_fails_closed() -> None:
    class EmptyTokenizer:
        def __call__(self, _values: list[str], **_kwargs: object) -> dict[str, list[list[int]]]:
            return {"input_ids": []}

    assert _lengths(EmptyTokenizer(), ["one"]) == []
    with pytest.raises(DenseOverflowInventoryError, match="no logical units"):
        _Counts().as_dict()


def test_inventory_module_remains_repository_relative() -> None:
    assert Path("src/myis_research/armindex/a1_2_dense_overflow_inventory_v1.py").is_absolute() is False
