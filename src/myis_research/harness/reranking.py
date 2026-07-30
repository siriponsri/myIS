"""Strict dependency-free parsing primitives for listwise reranking."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Sequence


_CLOSED_THINK_RE = re.compile(r"(?is)<think>.*?</think>")


@dataclass(frozen=True)
class PermutationParse:
    permutation: tuple[str, ...]
    valid: bool
    reason: str


def strip_closed_thinking_blocks(text: str) -> str:
    return _CLOSED_THINK_RE.sub("", text).strip()


def parse_permutation(text: str, candidate_ids: Sequence[str]) -> PermutationParse:
    expected = tuple(str(item) for item in candidate_ids)
    if len(set(expected)) != len(expected):
        return PermutationParse(expected, False, "candidate ids are not unique")
    stripped = strip_closed_thinking_blocks(text)
    if re.search(r"(?i)</?think>", stripped):
        return PermutationParse(expected, False, "unclosed thinking block")
    parsed: object | None = None
    if stripped.startswith("["):
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = None
    if isinstance(parsed, list):
        ids = tuple(str(item).strip() for item in parsed)
    else:
        found: list[tuple[int, str]] = []
        for candidate_id in sorted(expected, key=len, reverse=True):
            found.extend(
                (match.start(), candidate_id)
                for match in re.finditer(re.escape(candidate_id), stripped)
            )
        ids = tuple(candidate_id for _position, candidate_id in sorted(found))
    if len(ids) != len(expected):
        return PermutationParse(
            expected, False, f"expected {len(expected)} ids, parsed {len(ids)}"
        )
    if len(set(ids)) != len(ids):
        return PermutationParse(expected, False, "duplicate ids")
    if set(ids) != set(expected):
        missing = sorted(set(expected) - set(ids))
        extra = sorted(set(ids) - set(expected))
        return PermutationParse(expected, False, f"missing={missing}; extra={extra}")
    reason = "valid identity permutation" if ids == expected else "valid permutation"
    return PermutationParse(ids, True, reason)


def sliding_window_starts(n_items: int, *, window: int, stride: int) -> tuple[int, ...]:
    if n_items < 0:
        raise ValueError("n_items must be non-negative")
    if window < 1 or stride < 1:
        raise ValueError("window and stride must be positive")
    if n_items <= window:
        return (0,)
    starts = list(range(0, n_items - window + 1, stride))
    last = n_items - window
    if starts[-1] != last:
        starts.append(last)
    return tuple(starts)
