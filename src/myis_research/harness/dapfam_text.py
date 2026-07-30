"""Dependency-light DAPFAM text views for fixtures and governed adapters."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any


_CLAIM_BOUNDARY_RE = re.compile(
    r"(?im)(?=^\s*(?:claim\s+)?\d+\s*[\.)\]:-]\s+)"
)
_CLAIM_NUMBER_RE = re.compile(r"(?is)^\s*(?:claim\s+)?\d+\s*[\.)\]:-]\s*")
_DEPENDENCY_RE = re.compile(
    r"(?i)\b(?:according to|as claimed in|of|under|defined in)\s+"
    r"(?:any one of\s+)?claims?\s+\d+|\bclaims?\s+\d+\s*(?:-|to|or|and)"
)


def compose_title_abstract(row: Mapping[str, Any]) -> str:
    return _join_fields(row, ("title", "abstract"))


def compose_tac(row: Mapping[str, Any]) -> str:
    parts = [compose_title_abstract(row)]
    parts.extend(parse_claims(row.get("claims")))
    return "\n\n".join(part for part in parts if part)


def parse_claims(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return ()
        chunks = [chunk.strip() for chunk in _CLAIM_BOUNDARY_RE.split(text) if chunk.strip()]
        if len(chunks) == 1:
            return (text,)
        return tuple(_CLAIM_NUMBER_RE.sub("", chunk).strip() for chunk in chunks)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    text = str(value).strip()
    return (text,) if text else ()


def independent_claims(value: Any) -> tuple[str, ...]:
    claims = parse_claims(value)
    independent = tuple(claim for claim in claims if not _DEPENDENCY_RE.search(claim))
    return independent or claims[:1]


def compose_independent_claim_view(row: Mapping[str, Any]) -> str:
    return "\n\n".join(independent_claims(row.get("claims")))


def whitespace_windows(
    text: str, window_tokens: int, *, stride_tokens: int | None = None,
) -> tuple[str, ...]:
    if window_tokens <= 0:
        raise ValueError("window_tokens must be positive")
    stride = window_tokens if stride_tokens is None else stride_tokens
    if stride <= 0 or stride > window_tokens:
        raise ValueError("stride_tokens must be in [1, window_tokens]")
    tokens = text.split()
    if not tokens:
        return ()
    if stride_tokens is None:
        return tuple(
            " ".join(tokens[start : start + window_tokens])
            for start in range(0, len(tokens), window_tokens)
        )
    starts = list(range(0, max(1, len(tokens) - window_tokens + 1), stride))
    last = max(0, len(tokens) - window_tokens)
    if starts[-1] != last:
        starts.append(last)
    return tuple(" ".join(tokens[start : start + window_tokens]) for start in starts)


def _join_fields(row: Mapping[str, Any], fields: tuple[str, ...]) -> str:
    parts = []
    for field in fields:
        value = row.get(field)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
    return "\n\n".join(parts)
