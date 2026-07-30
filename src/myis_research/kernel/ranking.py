"""Deterministic ranking primitives shared by fixture and protected runners."""

from __future__ import annotations

from collections.abc import Iterable, Mapping


def rank_scores(scores: Mapping[str, float], *, limit: int) -> list[str]:
    if limit < 1:
        raise ValueError("limit must be positive")
    # Stable lexical tie break makes rankings byte-identical across platforms.
    return [key for key, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def family_maxp(ranked_publications: Iterable[tuple[str, str, float]], *, limit: int) -> list[str]:
    best: dict[str, tuple[float, str]] = {}
    for publication_id, family_id, score in ranked_publications:
        current = best.get(family_id)
        candidate = (float(score), str(publication_id))
        if current is None or candidate[0] > current[0] or (candidate[0] == current[0] and candidate[1] < current[1]):
            best[family_id] = candidate
    return [family for family, _ in sorted(best.items(), key=lambda item: (-item[1][0], item[0]))[:limit]]
