from __future__ import annotations

import pytest

from myis_research.armindex.a4_remote_ranker import A4RemoteRankerError, _fuse


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


def test_ranker_rejects_depth_below_evaluator_depth() -> None:
    with pytest.raises(A4RemoteRankerError, match="at least 100"):
        _fuse({"ARM-01": {"work-000": _rows()}}, depth=99)
