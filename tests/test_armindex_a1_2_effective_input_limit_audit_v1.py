from __future__ import annotations

from myis_research.armindex.a1_2_effective_input_limit_audit_v1 import (
    _find_first_overlength,
)


class _Tokenizer:
    def __call__(self, text: str, **_kwargs: object) -> dict[str, list[int]]:
        return {"input_ids": list(range(len(text.split())))}


def _row(claim_words: int) -> dict[str, str]:
    return {
        "title_en": "title",
        "abstract_en": "abstract",
        "claims_text": " ".join(["claim"] * claim_words),
    }


def test_bounded_audit_returns_first_overlength_witness_without_payload() -> None:
    witness = _find_first_overlength(
        [_row(2), _row(30), _row(50)],
        tokenizer=_Tokenizer(),
        effective_input_limit=20,
        max_rows=3,
    )
    assert witness is not None
    assert witness["rows_examined"] == 2
    assert witness["observed_tokens"] > 20
    assert "claim" not in repr(witness)


def test_bounded_audit_returns_none_when_no_witness_exists() -> None:
    assert (
        _find_first_overlength(
            [_row(2), _row(3)],
            tokenizer=_Tokenizer(),
            effective_input_limit=100,
            max_rows=2,
        )
        is None
    )
