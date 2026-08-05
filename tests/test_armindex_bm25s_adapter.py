from __future__ import annotations

import math

import pytest

from myis_research.armindex.bm25s_adapter import BM25sAdapter, tokenize
from myis_research.kernel.p1 import BM25Index


DOCUMENTS = [
    {"doc_id": "DOC-003", "family_id": "FAM-C", "text": "gamma valve actuator"},
    {"doc_id": "DOC-001", "family_id": "FAM-A", "text": "alpha alpha turbine blade"},
    {"doc_id": "DOC-002", "family_id": "FAM-B", "text": "alpha turbine coating"},
    {"doc_id": "DOC-004", "family_id": "FAM-D", "text": "unrelated optics"},
]


@pytest.mark.parametrize("query", ["alpha", "turbine", "alpha turbine", "valve"])
def test_bm25s_rank_order_matches_repository_okapi_reference(query: str) -> None:
    measured = BM25sAdapter()
    measured_rows = measured.search(measured.build_index(DOCUMENTS), query)
    reference_rows = BM25Index(DOCUMENTS, k1=1.2, b=0.75).rank(query)

    assert [row[0] for row in measured_rows] == [row[0] for row in reference_rows]
    ratios = [reference[2] / observed[2] for observed, reference in zip(measured_rows, reference_rows, strict=True)]
    assert all(math.isclose(ratio, 2.2, rel_tol=1e-12) for ratio in ratios)


def test_bm25s_filters_zero_scores_and_breaks_exact_ties_lexically() -> None:
    adapter = BM25sAdapter()
    index = adapter.build_index(
        [
            {"doc_id": "DOC-B", "family_id": "FAM-B", "text": "same token"},
            {"doc_id": "DOC-A", "family_id": "FAM-A", "text": "same token"},
            {"doc_id": "DOC-C", "family_id": "FAM-C", "text": "different"},
        ]
    )

    assert [row[0] for row in adapter.search(index, "same")] == ["DOC-A", "DOC-B"]
    assert adapter.search(index, "missing") == []


def test_bm25s_tokenizer_is_nfkc_casefold_and_language_neutral() -> None:
    assert tokenize("Ａlpha STRASSE ไทย_123") == ("alpha", "strasse", "ไทย_123")


def test_bm25s_adapter_rejects_invalid_documents_and_limits() -> None:
    adapter = BM25sAdapter()
    with pytest.raises(ValueError, match="exactly"):
        adapter.build_index([{"doc_id": "DOC", "text": "alpha"}])
    with pytest.raises(ValueError, match="unique"):
        adapter.build_index(
            [
                {"doc_id": "DOC", "family_id": "F1", "text": "alpha"},
                {"doc_id": "DOC", "family_id": "F2", "text": "beta"},
            ]
        )
    index = adapter.build_index(DOCUMENTS)
    with pytest.raises(ValueError, match="limit"):
        adapter.search(index, "alpha", limit=0)
