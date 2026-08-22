"""Regression tests for the opaque A5 corpus staging contract."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from materialize_a5_final_owner_local import _corpus_record  # noqa: E402
from myis_research.armindex.scientific_common_programs_v11 import compile_common_program  # noqa: E402


def test_corpus_record_has_distinct_family_and_publication_tokens() -> None:
    record = _corpus_record(
        family_token="F-" + "a" * 32,
        publication_token="P-" + "b" * 32,
        publication_ordinal=0,
        row={"title_en": "title", "abstract_en": "abstract", "claims_text": "claims"},
    )
    assert set(record) == {
        "family_token",
        "publication_token",
        "publication_ordinal",
        "title_en",
        "abstract_en",
        "claims_text",
        "claims",
    }
    assert record["family_token"].startswith("F-")
    assert record["publication_token"].startswith("P-")
    assert record["family_token"] != record["publication_token"]
    assert record["publication_ordinal"] == 0


@pytest.mark.parametrize("ordinal", [-1, True, "0"])
def test_corpus_record_rejects_invalid_publication_ordinal(ordinal: object) -> None:
    with pytest.raises(ValueError, match="identity/order contract"):
        _corpus_record(
            family_token="F-" + "a" * 32,
            publication_token="P-" + "b" * 32,
            publication_ordinal=ordinal,  # type: ignore[arg-type]
            row={},
        )


def test_corpus_record_rejects_wrong_token_prefix() -> None:
    with pytest.raises(ValueError, match="identity/order contract"):
        _corpus_record(
            family_token="F-" + "a" * 32,
            publication_token="F-" + "b" * 32,
            publication_ordinal=0,
            row={},
        )


def test_corpus_record_is_accepted_by_frozen_common_program() -> None:
    record = _corpus_record(
        family_token="F-" + "a" * 32,
        publication_token="P-" + "b" * 32,
        publication_ordinal=0,
        row={"title_en": "title", "abstract_en": "abstract", "claims_text": "claims"},
    )
    compiled = compile_common_program("P00-TAC-DOC", [record])
    assert compiled.family_count == 1
    assert compiled.covered_family_count == 1
