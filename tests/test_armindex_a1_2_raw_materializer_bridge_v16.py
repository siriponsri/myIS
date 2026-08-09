from __future__ import annotations

from collections.abc import Sequence

from myis_research.armindex.a1_2_raw_materializer_bridge_v16 import (
    materialize_raw_corpus,
    materialize_raw_query,
)


class WordTokenizer:
    def __init__(self) -> None:
        self._ids: dict[str, int] = {}
        self._words: dict[int, str] = {}

    def _encode(self, text: str) -> list[int]:
        values = []
        for word in text.split():
            if word not in self._ids:
                value = len(self._ids) + 10
                self._ids[word] = value
                self._words[value] = word
            values.append(self._ids[word])
        return values

    def __call__(self, texts: Sequence[str], *, add_special_tokens: bool, **_: object) -> dict[str, list[list[int]]]:
        values = [self._encode(text) for text in texts]
        if add_special_tokens:
            values = [[1, *row, 2] for row in values]
        return {"input_ids": values}

    def decode(self, values: Sequence[int], **_: object) -> str:
        return " ".join(self._words[value] for value in values if value not in {1, 2})


class Adapter:
    def __init__(self) -> None:
        self.tokenizer = WordTokenizer()


def _row(*, family: str = "F-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", claims_text: str = "1. first claim. 2. second claim.", title: str = "Title", abstract: str = "Abstract") -> dict[str, object]:
    return {
        "family_token": family,
        "publication_token": "P-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "publication_ordinal": 0,
        "title_en": title,
        "abstract_en": abstract,
        "claims_text": claims_text,
        "claims": [],
    }


def test_raw_rows_compile_common_programs_and_p02_boundary() -> None:
    rows = [_row()]
    lexical = materialize_raw_corpus(rows, arm_id="ARM-01", program_id="P00-TAC-DOC")
    assert len(lexical) == 1 and len(lexical[0].physical_inputs) == 1
    assert "TITLE: Title" in lexical[0].physical_inputs[0].text

    first_claim = materialize_raw_corpus(rows, arm_id="ARM-01", program_id="P02-FIRST-CLAIM")
    assert len(first_claim) == 1
    assert first_claim[0].physical_inputs[0].text == "first claim. 2. second claim"

    views = materialize_raw_corpus(rows, arm_id="ARM-01", program_id="P04-SECTION-MULTIVIEW")
    assert {unit.view_id for unit in views} == {"title", "abstract", "claims"}


def test_p02_preserves_one_logical_unit_per_publication_row() -> None:
    rows = [
        _row(),
        {
            **_row(),
            "publication_token": "P-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "publication_ordinal": 1,
            "claims_text": "1. second publication claim.",
        },
    ]
    units = materialize_raw_corpus(rows, arm_id="ARM-01", program_id="P02-FIRST-CLAIM")
    assert len(units) == 2
    assert len({unit.logical_id for unit in units}) == 2
    assert {unit.family_token for unit in units} == {
        "F-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }


def test_dense_fit_uses_frozen_template_and_source_weight() -> None:
    adapter = Adapter()
    units = materialize_raw_corpus([_row()], arm_id="ARM-03", program_id="P00-TAC-DOC", adapter=adapter)
    assert len(units) == 1 and len(units[0].physical_inputs) == 1
    assert units[0].physical_inputs[0].source_token_count > 0
    assert units[0].physical_inputs[0].text.startswith("encode document for different retrieval:")

    query = materialize_raw_query({"work_token": "Q-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "text": "query words"}, arm_id="ARM-03", adapter=adapter)
    assert query.physical_inputs[0].text.startswith("encode query for different document retrieval:")


def test_dense_fit_accepts_empty_template_prefix() -> None:
    adapter = Adapter()
    units = materialize_raw_corpus(
        [_row()], arm_id="ARM-02", program_id="P00-TAC-DOC", adapter=adapter
    )
    assert len(units) == 1 and len(units[0].physical_inputs) == 1
    assert units[0].physical_inputs[0].source_token_count > 0
    query = materialize_raw_query(
        {"work_token": "Q-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "text": "query words"},
        arm_id="ARM-02",
        adapter=adapter,
    )
    assert query.physical_inputs[0].token_ids


def test_dense_overflow_has_zero_overlap_and_no_truncation() -> None:
    adapter = Adapter()
    long_text = " ".join(f"token{i}" for i in range(700))
    units = materialize_raw_corpus([_row(abstract=long_text)], arm_id="ARM-03", program_id="P01-TA-DOC", adapter=adapter)
    physical = units[0].physical_inputs
    assert len(physical) >= 2
    assert sum(item.source_token_count for item in physical) == 703
    assert all(len(adapter.tokenizer(item.text, add_special_tokens=True)["input_ids"][0]) <= 512 for item in physical)


def test_dense_decode_text_does_not_replace_exact_planned_ids() -> None:
    class DriftAdapter(Adapter):
        def __init__(self) -> None:
            super().__init__()
            self.tokenizer.decode = lambda *_args, **_kwargs: "drifted"

    units = materialize_raw_corpus(
        [_row(abstract=" ".join(f"token{i}" for i in range(700)))],
        arm_id="ARM-03",
        program_id="P01-TA-DOC",
        adapter=DriftAdapter(),
    )
    assert len(units) == 1
    assert all(item.token_ids for item in units[0].physical_inputs)


def test_dense_materialization_never_requires_window_decode() -> None:
    class DecodeForbiddenAdapter(Adapter):
        def __init__(self) -> None:
            super().__init__()
            self.tokenizer.decode = lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("decode called"))

    units = materialize_raw_corpus(
        [_row(abstract=" ".join(f"token{i}" for i in range(700)))],
        arm_id="ARM-03",
        program_id="P01-TA-DOC",
        adapter=DecodeForbiddenAdapter(),
    )
    assert len(units[0].physical_inputs) > 1
    assert all(item.token_ids for item in units[0].physical_inputs)
