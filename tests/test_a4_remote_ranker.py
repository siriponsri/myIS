from __future__ import annotations

from threading import Barrier
from types import SimpleNamespace

import pytest

from myis_research.armindex import a4_remote_ranker
from myis_research.armindex.a4_remote_ranker import A4RemoteRankerError, _fuse, _profile_latencies, _rank_arms


def _rows(offset: int = 0) -> list[dict[str, object]]:
    return [
        {"family_token": f"family-{(index + offset) % 100:03d}", "rank": index + 1, "score": 1.0 / (index + 1)}
        for index in range(100)
    ]


def test_deeper_profile_pool_still_returns_frozen_top_100() -> None:
    tokens = {f"work-{index:03d}" for index in range(100)}
    result = _fuse(
        {"ARM-01": {token: _rows() for token in tokens}},
        depth=200,
    )
    assert len(result) == 100
    assert all(len(rows) == 100 for rows in result.values())


def test_fused_profile_serializes_fusion_mapping_rows() -> None:
    tokens = {f"work-{index:03d}" for index in range(100)}
    result = _fuse(
        {
            "ARM-04": {token: _rows() for token in tokens},
            "ARM-05": {token: _rows(offset=17) for token in tokens},
        },
        depth=100,
    )
    rows = result["work-000"]
    assert len(rows) == 100
    assert all(set(row) == {"family_token", "rank", "score"} for row in rows)
    assert [row["rank"] for row in rows] == list(range(1, 101))
    assert all(isinstance(row["score"], float) for row in rows)


def test_ranker_rejects_depth_below_evaluator_depth() -> None:
    with pytest.raises(A4RemoteRankerError, match="at least 100"):
        _fuse({"ARM-01": {"work-000": _rows()}}, depth=99)


def test_asynchronous_profile_runs_components_concurrently(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    barrier = Barrier(2)

    def fake_rank(_root, *, arm_id, queries):
        barrier.wait(timeout=1)
        return ({token: _rows() for token in queries}, [0.1] * len(queries))

    monkeypatch.setattr(a4_remote_ranker, "_rank_one", fake_rank)
    rankings, latencies = _rank_arms(
        tmp_path,
        arm_ids=["ARM-04", "ARM-05"],
        queries={f"work-{index:03d}": "opaque" for index in range(100)},
        mode="asynchronous",
    )
    assert set(rankings) == {"ARM-04", "ARM-05"}
    assert set(latencies) == {"ARM-04", "ARM-05"}


def test_profile_latency_respects_service_mode() -> None:
    components = {"ARM-04": [0.1, 0.4], "ARM-05": [0.3, 0.2]}
    assert _profile_latencies(components, arm_ids=["ARM-04", "ARM-05"], mode="synchronous") == pytest.approx([0.4, 0.6])
    assert _profile_latencies(components, arm_ids=["ARM-04", "ARM-05"], mode="asynchronous") == pytest.approx([0.3, 0.4])


def test_dense_ranking_uses_conservative_batch_one_after_oom_recovery(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """The A4 24 GiB recovery must never silently restore the old batch of 32."""

    captured: dict[str, int] = {}
    monkeypatch.setattr(a4_remote_ranker, "_load_json", lambda *_args: {"arm_id": "ARM-05", "program_sha256": "0" * 64})
    monkeypatch.setattr(a4_remote_ranker, "_corpus_rows", lambda *_args: [])
    monkeypatch.setattr(
        a4_remote_ranker,
        "compile_program",
        lambda *_args: SimpleNamespace(units=[], family_aggregation="max"),
    )

    def fake_rank_dense(*_args, **kwargs):
        captured["batch_size"] = kwargs["batch_size"]
        return {}, []

    monkeypatch.setattr(a4_remote_ranker, "_rank_dense", fake_rank_dense)
    monkeypatch.setattr(a4_remote_ranker, "_serialise", lambda _ranks: {})

    a4_remote_ranker._rank_one(tmp_path, arm_id="ARM-05", queries={})

    assert captured["batch_size"] == 1
