"""Production compilation and family aggregation for frozen A2 programs."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .a1_2_measured_executor_v16 import FamilyRank, LogicalInput, PhysicalInput


class A2ProgramRuntimeError(ValueError):
    """Raised when a frozen A2 representation program cannot be executed."""


@dataclass(frozen=True)
class CompiledProgram:
    program_id: str
    family_aggregation: str
    units: tuple[LogicalInput, ...]


def _normalize(value: object, mode: str) -> str:
    text = unicodedata.normalize("NFKC", value if isinstance(value, str) else "")
    text = re.sub(r"\s+", " ", text).strip()
    if mode == "unicode_nfkc_whitespace_lower":
        text = text.lower()
    if mode not in {"unicode_nfkc_whitespace", "unicode_nfkc_whitespace_lower"}:
        raise A2ProgramRuntimeError("unsupported frozen normalization")
    return text


def _render(row: Mapping[str, Any], program: Mapping[str, Any]) -> str:
    fields = program["field_order"]
    if set(fields) != set(program["source_fields"]):
        raise A2ProgramRuntimeError("frozen source field order is inconsistent")
    parts: list[str] = []
    for field in fields:
        value = _normalize(row.get(field), program["normalization"])
        if value:
            parts.append(f"{program['field_labels'].get(field, '')}{value}")
    rendered = " ".join(parts).strip()
    if not rendered:
        raise A2ProgramRuntimeError("frozen program rendered an empty source row")
    return rendered


def _windows(tokens: Sequence[str], size: int, overlap: int) -> tuple[str, ...]:
    if size < 1 or overlap < 0 or overlap >= size or not tokens:
        raise A2ProgramRuntimeError("frozen passage window is invalid")
    stride = size - overlap
    windows: list[str] = []
    start = 0
    while start < len(tokens):
        windows.append(" ".join(tokens[start : start + size]))
        if start + size >= len(tokens):
            break
        start += stride
    return tuple(windows)


def compile_program(
    rows: Sequence[Mapping[str, Any]], program: Mapping[str, Any]
) -> CompiledProgram:
    """Compile every source row without caps, truncation, or fixture shortcuts."""

    seen_content: set[str] = set()
    per_family: dict[str, list[tuple[str, str]]] = {}
    for ordinal, row in enumerate(rows):
        family = row.get("family_token")
        publication = row.get("publication_token")
        if not isinstance(family, str) or not family.startswith("F-"):
            raise A2ProgramRuntimeError("source row family token is invalid")
        if not isinstance(publication, str) or not publication:
            raise A2ProgramRuntimeError("source row publication token is invalid")
        rendered = _render(row, program)
        content_hash = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        if program["duplicate_policy"] == "content_hash_first":
            if content_hash in seen_content:
                continue
            seen_content.add(content_hash)
        elif program["duplicate_policy"] != "preserve_all":
            raise A2ProgramRuntimeError("unsupported frozen duplicate policy")
        per_family.setdefault(family, []).append((f"{publication}:{ordinal:08d}", rendered))
    units: list[LogicalInput] = []
    kind = program["unitization"]["kind"]
    for family in sorted(per_family):
        records = per_family[family]
        if kind == "family":
            text = " ".join(value for _identity, value in records)
            units.append(LogicalInput(f"{family}:family", family, None, (PhysicalInput(text, 1),)))
        elif kind == "passage":
            size = program["unitization"]["logical_size"]
            overlap = program["unitization"]["overlap"]
            for identity, text in records:
                for index, passage in enumerate(_windows(text.split(), size, overlap)):
                    units.append(
                        LogicalInput(
                            f"{family}:{identity}:p{index:08d}",
                            family,
                            f"passage-{index}",
                            (PhysicalInput(passage, len(passage.split())),),
                        )
                    )
        else:
            raise A2ProgramRuntimeError("unsupported frozen unitization")
    if not units:
        raise A2ProgramRuntimeError("frozen program produced no units")
    return CompiledProgram(str(program["program_id"]), str(program["family_aggregation"]), tuple(units))


def aggregate_family_scores(
    units: Sequence[LogicalInput], scores: Sequence[float], *, method: str, limit: int = 100
) -> tuple[FamilyRank, ...]:
    """Aggregate unit scores with the frozen lexical family-token tie break."""

    if len(units) != len(scores) or limit != 100:
        raise A2ProgramRuntimeError("family aggregation input is invalid")
    grouped: dict[str, list[float]] = {}
    for unit, score in zip(units, scores, strict=True):
        grouped.setdefault(unit.family_token, []).append(float(score))
    aggregated: list[tuple[str, float]] = []
    for family, values in grouped.items():
        ordered = sorted(values, reverse=True)
        if method == "maxp":
            score = ordered[0]
        elif method == "avg_top3":
            score = sum(ordered[:3]) / min(3, len(ordered))
        elif method == "single_unit":
            if len(ordered) != 1:
                raise A2ProgramRuntimeError("single_unit requires one unit per family")
            score = ordered[0]
        else:
            raise A2ProgramRuntimeError("unsupported frozen family aggregation")
        aggregated.append((family, score))
    aggregated.sort(key=lambda item: (-item[1], item[0]))
    return tuple(
        FamilyRank(family, rank, score)
        for rank, (family, score) in enumerate(aggregated[:limit], start=1)
    )


__all__ = ["A2ProgramRuntimeError", "CompiledProgram", "aggregate_family_scores", "compile_program"]
