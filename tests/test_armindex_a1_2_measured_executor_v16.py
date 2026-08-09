from __future__ import annotations

import numpy as np
import pytest

from myis_research.armindex.a1_2_measured_executor_v16 import (
    DenseEmbeddingAdapter,
    LogicalInput,
    MeasuredExecutorV16Error,
    PhysicalInput,
    build_dense_index,
    encode_logical_inputs,
    execute_program_cell,
    execute_program_cell_batch,
    search_bm25,
    search_dense,
)


class FakeAdapter(DenseEmbeddingAdapter):
    def __init__(self, vectors: dict[str, tuple[float, ...]]) -> None:
        self.vectors = vectors

    def encode(self, inputs: list[str]) -> np.ndarray:
        return np.asarray([self.vectors[item] for item in inputs], dtype=np.float64)


class CountingAdapter(FakeAdapter):
    def __init__(self, vectors: dict[str, tuple[float, ...]]) -> None:
        super().__init__(vectors)
        self.calls: list[tuple[str, ...]] = []

    def encode(self, inputs: list[str]) -> np.ndarray:
        self.calls.append(tuple(inputs))
        return super().encode(inputs)


def unit(
    logical_id: str,
    family: str,
    *texts: tuple[str, int],
    view_id: str | None = None,
) -> LogicalInput:
    return LogicalInput(
        logical_id=logical_id,
        family_token=family,
        view_id=view_id,
        physical_inputs=tuple(PhysicalInput(text, count) for text, count in texts),
    )


def test_dense_overflow_recomposition_is_source_token_weighted_then_normalized() -> (
    None
):
    adapter = FakeAdapter({"first": (1.0, 0.0), "second": (0.0, 1.0)})
    values = encode_logical_inputs(
        arm_id="ARM-03",
        adapter=adapter,
        logical_inputs=(
            unit(
                "doc", "F-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", ("first", 3), ("second", 1)
            ),
        ),
    )
    assert np.allclose(values[0], np.asarray((3.0, 1.0)) / np.sqrt(10.0))


def test_dense_family_max_rank_has_lexical_ties_and_hides_units() -> None:
    adapter = FakeAdapter(
        {
            "f-b-1": (1.0, 0.0),
            "f-b-2": (0.0, 1.0),
            "f-a": (1.0, 0.0),
            "query": (1.0, 0.0),
        }
    )
    corpus = (
        unit("b-1", "F-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", ("f-b-1", 1)),
        unit("b-2", "F-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", ("f-b-2", 1)),
        unit("a", "F-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", ("f-a", 1)),
    )
    index = build_dense_index(arm_id="ARM-02", adapter=adapter, corpus=corpus)
    ranks = search_dense(
        index=index,
        adapter=adapter,
        query=unit("query", "Q-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", ("query", 1)),
        program_id="P03-PASSAGE",
    )
    assert [(row.family_token, row.rank) for row in ranks] == [
        ("F-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 1),
        ("F-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", 2),
    ]


def test_dense_executor_accepts_frozen_passage_view_ids() -> None:
    adapter = FakeAdapter({"passage": (1.0, 0.0), "query": (1.0, 0.0)})
    index = build_dense_index(
        arm_id="ARM-02",
        adapter=adapter,
        corpus=(
            unit(
                "passage-0001",
                "F-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                ("passage", 1),
                view_id="passage-0001",
            ),
        ),
    )
    ranks = search_dense(
        index=index,
        adapter=adapter,
        query=unit("query", "Q-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", ("query", 1)),
        program_id="P03-PASSAGE",
    )
    assert [(row.family_token, row.rank) for row in ranks] == [
        ("F-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 1)
    ]


def test_p04_uses_frozen_view_rrf_not_raw_score_fusion() -> None:
    family_a = "F-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    family_b = "F-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    adapter = FakeAdapter(
        {
            "at": (1.0, 0.0),
            "bt": (0.9938837346736188, 0.11043152607484655),
            "aa": (0.0, 1.0),
            "ba": (0.11043152607484655, 0.9938837346736188),
            "ac": (1.0, 0.0),
            "bc": (0.9938837346736188, 0.11043152607484655),
            "query": (1.0, 0.0),
        }
    )
    corpus = (
        unit("at", family_a, ("at", 1), view_id="title"),
        unit("bt", family_b, ("bt", 1), view_id="title"),
        unit("aa", family_a, ("aa", 1), view_id="abstract"),
        unit("ba", family_b, ("ba", 1), view_id="abstract"),
        unit("ac", family_a, ("ac", 1), view_id="claims"),
        unit("bc", family_b, ("bc", 1), view_id="claims"),
    )
    index = build_dense_index(arm_id="ARM-02", adapter=adapter, corpus=corpus)
    ranks = search_dense(
        index=index,
        adapter=adapter,
        query=unit("query", "Q-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", ("query", 1)),
        program_id="P04-SECTION-MULTIVIEW",
    )
    assert [(row.family_token, row.rank) for row in ranks] == [
        (family_a, 1),
        (family_b, 2),
    ]


def test_bm25_uses_same_family_max_and_p04_rrf() -> None:
    family_a = "F-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    family_b = "F-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    corpus = (
        unit("at", family_a, ("alpha", 1), view_id="title"),
        unit("bt", family_b, ("alpha", 1), view_id="title"),
        unit("aa", family_a, ("outside", 1), view_id="abstract"),
        unit("ba", family_b, ("alpha", 1), view_id="abstract"),
        unit("ac", family_a, ("alpha", 1), view_id="claims"),
        unit("bc", family_b, ("outside", 1), view_id="claims"),
    )
    ranks = search_bm25(
        corpus=corpus, query="alpha", program_id="P04-SECTION-MULTIVIEW"
    )
    assert [(row.family_token, row.rank) for row in ranks] == [
        (family_a, 1),
        (family_b, 2),
    ]


def test_dense_core_rejects_invalid_physical_plan_and_dimensions() -> None:
    adapter = FakeAdapter({"one": (1.0, 0.0), "query": (1.0, 0.0, 0.0)})
    with pytest.raises(MeasuredExecutorV16Error, match="physical input"):
        build_dense_index(
            arm_id="ARM-02",
            adapter=adapter,
            corpus=(unit("one", "F-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", ("one", 0)),),
        )
    index = build_dense_index(
        arm_id="ARM-02",
        adapter=FakeAdapter({"one": (1.0, 0.0)}),
        corpus=(unit("one", "F-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", ("one", 1)),),
    )
    with pytest.raises(MeasuredExecutorV16Error, match="dimensions"):
        search_dense(
            index=index,
            adapter=adapter,
            query=unit("query", "Q-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", ("query", 1)),
            program_id="P00-TAC-DOC",
        )


def test_callback_api_returns_only_top_100_family_ranks() -> None:
    corpus = tuple(
        unit(
            f"unit-{index}",
            f"F-{index:032x}",
            (("alpha" if index < 101 else "other"), 1),
        )
        for index in range(101)
    )
    ranks = execute_program_cell(
        arm_id="ARM-01", program_id="P02-FIRST-CLAIM", corpus=corpus, query="alpha"
    )
    assert len(ranks) == 100
    assert ranks[0].rank == 1
    assert all(set(row.__dict__) == {"family_token", "rank", "score"} for row in ranks)


def test_batch_dense_builds_corpus_once_and_queries_once_in_work_order() -> None:
    adapter = CountingAdapter(
        {"doc": (1.0, 0.0), "query-a": (1.0, 0.0), "query-b": (0.0, 1.0)}
    )
    corpus = (unit("doc", "F-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", ("doc", 1)),)
    queries = {
        "Q-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa01": unit(
            "query-a", "Q-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa01", ("query-a", 1)
        ),
        "Q-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa02": unit(
            "query-b", "Q-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa02", ("query-b", 1)
        ),
    }
    result = execute_program_cell_batch(
        arm_id="ARM-02",
        program_id="P00-TAC-DOC",
        corpus=corpus,
        queries=queries,
        adapter=adapter,
    )
    assert list(result) == list(queries)
    assert adapter.calls == [("doc",), ("query-a", "query-b")]
    replay = execute_program_cell_batch(
        arm_id="ARM-02",
        program_id="P00-TAC-DOC",
        corpus=corpus,
        queries=queries,
        adapter=adapter,
    )
    assert result == replay


def test_batch_bm25_builds_one_index_and_preserves_query_order() -> None:
    corpus = (
        unit("a", "F-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", ("alpha", 1)),
        unit("b", "F-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", ("beta", 1)),
    )
    result = execute_program_cell_batch(
        arm_id="ARM-01",
        program_id="P00-TAC-DOC",
        corpus=corpus,
        queries={
            "Q-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa01": "alpha",
            "Q-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa02": "beta",
        },
    )
    assert list(result) == [
        "Q-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa01",
        "Q-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa02",
    ]
    assert result["Q-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa01"][0].family_token.startswith("F-")
