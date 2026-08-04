"""Deterministic representation compilation for the synthetic ArmIndex slice."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from ..kernel.canonical import canonical_sha256
from ..kernel.p1 import tokenize


_CLAIM_START = re.compile(r"(?m)(?=^\s*\d+[\.)]\s+)")
_SUPPORTED_ARMS = frozenset({"ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05"})
_SUPPORTED_AGGREGATIONS = frozenset({"maxp", "avg_top3", "single_unit", "top_m"})


class RepresentationCompileError(ValueError):
    """Raised when a logical program or synthetic document fails closed."""


@dataclass(frozen=True)
class SourceSpan:
    source_field: str
    start: int
    end: int
    source_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_field": self.source_field,
            "start": self.start,
            "end": self.end,
            "source_sha256": self.source_sha256,
        }


@dataclass(frozen=True)
class CompiledUnit:
    unit_id: str
    family_id: str
    publication_id: str
    unit_kind: str
    text: str
    content_sha256: str
    source_spans: tuple[SourceSpan, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "family_id": self.family_id,
            "publication_id": self.publication_id,
            "unit_kind": self.unit_kind,
            "text": self.text,
            "content_sha256": self.content_sha256,
            "source_spans": [span.as_dict() for span in self.source_spans],
        }


@dataclass(frozen=True)
class CompiledRepresentation:
    arm_id: str
    program_id: str
    logical_program_sha256: str
    compiled_representation_sha256: str
    source_sha256: str
    family_aggregation: str
    units: tuple[CompiledUnit, ...]
    estimated_storage_bytes: int
    estimated_token_count: int
    omitted_unit_count: int
    truncated_span_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "arm_id": self.arm_id,
            "program_id": self.program_id,
            "logical_program_sha256": self.logical_program_sha256,
            "compiled_representation_sha256": self.compiled_representation_sha256,
            "source_sha256": self.source_sha256,
            "family_aggregation": self.family_aggregation,
            "units": [unit.as_dict() for unit in self.units],
            "estimates": {
                "storage_bytes": self.estimated_storage_bytes,
                "token_count": self.estimated_token_count,
                "unit_count": len(self.units),
            },
            "omitted_unit_count": self.omitted_unit_count,
            "truncated_span_count": self.truncated_span_count,
        }


@dataclass(frozen=True)
class _Descriptor:
    kind: str
    text: str
    spans: tuple[SourceSpan, ...]


def compile_program(
    program: Mapping[str, Any],
    documents: Iterable[Mapping[str, Any]],
    *,
    max_units_per_publication: int = 4,
) -> CompiledRepresentation:
    """Compile a logical program into byte-stable, source-grounded units.

    This implementation is fixture-only. It does not resolve model adapters,
    access benchmark data, or mutate any measured campaign state.
    """

    normalized_program = _validate_program(program)
    if max_units_per_publication < 1:
        raise RepresentationCompileError("max_units_per_publication must be positive")
    rows = _validate_documents(normalized_program, documents)
    source_sha256 = canonical_sha256(rows)
    units: list[CompiledUnit] = []
    omitted = 0
    for row in rows:
        descriptors = _descriptors(normalized_program, row)
        selected, omitted_here = _bounded(descriptors, max_units_per_publication)
        omitted += omitted_here
        for descriptor in selected:
            semantic = {
                "arm_id": normalized_program["arm_id"],
                "program_sha256": normalized_program["program_sha256"],
                "family_id": row["family_id"],
                "publication_id": row["publication_id"],
                "unit_kind": descriptor.kind,
                "text": descriptor.text,
                "source_spans": [span.as_dict() for span in descriptor.spans],
            }
            content_sha256 = canonical_sha256(descriptor.text)
            units.append(
                CompiledUnit(
                    unit_id="unit-" + canonical_sha256(semantic)[:24],
                    family_id=row["family_id"],
                    publication_id=row["publication_id"],
                    unit_kind=descriptor.kind,
                    text=descriptor.text,
                    content_sha256=content_sha256,
                    source_spans=descriptor.spans,
                )
            )
    units = _deduplicate(normalized_program, units)
    units.sort(key=lambda unit: (unit.family_id, unit.publication_id, unit.unit_id))
    if normalized_program["family_aggregation"] == "single_unit":
        counts: dict[str, int] = {}
        for unit in units:
            counts[unit.family_id] = counts.get(unit.family_id, 0) + 1
        if any(count != 1 for count in counts.values()):
            raise RepresentationCompileError("single_unit aggregation requires exactly one unit per family")
    compiled_payload = {
        "compiler": "myis.armindex-synthetic-compiler.v1",
        "arm_id": normalized_program["arm_id"],
        "logical_program_sha256": normalized_program["program_sha256"],
        "source_sha256": source_sha256,
        "family_aggregation": normalized_program["family_aggregation"],
        "max_units_per_publication": max_units_per_publication,
        "units": [unit.as_dict() for unit in units],
        "omitted_unit_count": omitted,
        "truncated_span_count": 0,
    }
    return CompiledRepresentation(
        arm_id=normalized_program["arm_id"],
        program_id=normalized_program["program_id"],
        logical_program_sha256=normalized_program["program_sha256"],
        compiled_representation_sha256=canonical_sha256(compiled_payload),
        source_sha256=source_sha256,
        family_aggregation=normalized_program["family_aggregation"],
        units=tuple(units),
        estimated_storage_bytes=sum(len(unit.text.encode("utf-8")) for unit in units),
        estimated_token_count=sum(len(tokenize(unit.text)) for unit in units),
        omitted_unit_count=omitted,
        truncated_span_count=0,
    )


def _validate_program(program: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(program)
    required = {
        "schema_version",
        "program_id",
        "arm_id",
        "source_fields",
        "field_order",
        "field_labels",
        "unitization",
        "normalization",
        "duplicate_policy",
        "family_aggregation",
        "preserve_family_identity",
        "program_sha256",
    }
    if set(value) != required:
        raise RepresentationCompileError("representation program fields do not match the fixture contract")
    if value["arm_id"] not in _SUPPORTED_ARMS:
        raise RepresentationCompileError("unknown ArmIndex arm")
    fields = tuple(str(field) for field in value["source_fields"])
    order = tuple(str(field) for field in value["field_order"])
    if not fields or len(fields) != len(set(fields)) or set(fields) != set(order) or len(order) != len(set(order)):
        raise RepresentationCompileError("source_fields and field_order must contain the same unique fields")
    labels = value["field_labels"]
    if not isinstance(labels, Mapping) or set(labels) - set(fields):
        raise RepresentationCompileError("field_labels references an unknown source field")
    unitization = value["unitization"]
    if not isinstance(unitization, Mapping) or set(unitization) - {"kind", "logical_size", "overlap"}:
        raise RepresentationCompileError("unitization is invalid")
    kind = str(unitization.get("kind", ""))
    if kind not in {"family", "document", "field", "section", "claim", "passage"}:
        raise RepresentationCompileError("unsupported unitization kind")
    logical_size = unitization.get("logical_size")
    overlap = unitization.get("overlap", 0)
    if kind == "passage" and (not isinstance(logical_size, int) or logical_size < 1):
        raise RepresentationCompileError("passage unitization requires a positive logical_size")
    if not isinstance(overlap, int) or overlap < 0 or (isinstance(logical_size, int) and overlap >= logical_size):
        raise RepresentationCompileError("unitization overlap must be smaller than logical_size")
    if value["normalization"] not in {"unicode_nfkc_whitespace", "unicode_nfkc_whitespace_lower"}:
        raise RepresentationCompileError("unsupported normalization")
    if value["duplicate_policy"] not in {"content_hash_first", "preserve_all"}:
        raise RepresentationCompileError("unsupported duplicate policy")
    if value["family_aggregation"] not in _SUPPORTED_AGGREGATIONS:
        raise RepresentationCompileError("unsupported family aggregation")
    if value["preserve_family_identity"] is not True:
        raise RepresentationCompileError("family identity preservation is mandatory")
    unsigned = {key: item for key, item in value.items() if key != "program_sha256"}
    if canonical_sha256(unsigned) != value["program_sha256"]:
        raise RepresentationCompileError("representation program hash mismatch")
    return value


def _validate_documents(program: Mapping[str, Any], documents: Iterable[Mapping[str, Any]]) -> list[dict[str, str]]:
    expected = {"family_id", "publication_id", *program["source_fields"]}
    rows: list[dict[str, str]] = []
    publication_families: dict[str, str] = {}
    for raw in documents:
        if set(raw) != expected:
            raise RepresentationCompileError("synthetic document fields do not match the program")
        row = {str(key): str(item) for key, item in raw.items()}
        if any(not row[key].strip() for key in ("family_id", "publication_id")):
            raise RepresentationCompileError("family_id and publication_id are required")
        publication = row["publication_id"]
        family = row["family_id"]
        if publication in publication_families:
            raise RepresentationCompileError("publication_id must be unique")
        publication_families[publication] = family
        rows.append(row)
    if not rows:
        raise RepresentationCompileError("at least one synthetic document is required")
    return sorted(rows, key=lambda row: (row["family_id"], row["publication_id"], canonical_sha256(row)))


def _descriptors(program: Mapping[str, Any], row: Mapping[str, str]) -> list[_Descriptor]:
    kind = str(program["unitization"]["kind"])
    ordered_fields = tuple(str(field) for field in program["field_order"])
    if kind in {"family", "document"}:
        text = _compose(program, row, ordered_fields)
        return [_Descriptor("document", text, _full_spans(row, ordered_fields))] if text else []
    if kind in {"field", "section"}:
        return [
            _Descriptor("section", _compose(program, row, (field,)), _full_spans(row, (field,)))
            for field in ordered_fields
            if _normalize(row[field], str(program["normalization"]))
        ]
    if kind == "claim":
        output: list[_Descriptor] = []
        for field in ordered_fields:
            raw = row[field]
            for start, end, text in _claim_spans(raw):
                normalized = _normalize(text, str(program["normalization"]))
                if normalized:
                    label = str(program["field_labels"].get(field, field))
                    rendered = f"{label}: {normalized}" if label else normalized
                    output.append(
                        _Descriptor(
                            "claim",
                            rendered,
                            (SourceSpan(field, start, end, canonical_sha256(raw[start:end])),),
                        )
                    )
        return output
    size = int(program["unitization"]["logical_size"])
    overlap = int(program["unitization"].get("overlap", 0))
    stride = size - overlap
    field_tokens: list[tuple[str, str]] = []
    for field in ordered_fields:
        normalized = _normalize(row[field], str(program["normalization"]))
        label = str(program["field_labels"].get(field, field))
        if normalized and label:
            field_tokens.append((f"{label}:", field))
        field_tokens.extend((token, field) for token in tokenize(normalized))
    output = []
    for start in range(0, len(field_tokens), stride):
        window = field_tokens[start : start + size]
        if not window:
            continue
        touched = tuple(dict.fromkeys(field for _token, field in window))
        output.append(
            _Descriptor(
                "passage",
                " ".join(token for token, _field in window),
                _full_spans(row, touched),
            )
        )
    return output


def _compose(program: Mapping[str, Any], row: Mapping[str, str], fields: Sequence[str]) -> str:
    parts = []
    for field in fields:
        content = _normalize(row[field], str(program["normalization"]))
        if not content:
            continue
        label = str(program["field_labels"].get(field, field))
        parts.append(f"{label}: {content}" if label else content)
    return "\n".join(parts)


def _normalize(text: str, mode: str) -> str:
    value = " ".join(unicodedata.normalize("NFKC", text).split())
    return value.casefold() if mode.endswith("_lower") else value


def _full_spans(row: Mapping[str, str], fields: Sequence[str]) -> tuple[SourceSpan, ...]:
    return tuple(
        SourceSpan(field, 0, len(row[field]), canonical_sha256(row[field]))
        for field in fields
        if row[field]
    )


def _claim_spans(text: str) -> list[tuple[int, int, str]]:
    starts = [match.start() for match in _CLAIM_START.finditer(text)]
    if not starts:
        return [(0, len(text), text)] if text.strip() else []
    output = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(text)
        if text[start:end].strip():
            output.append((start, end, text[start:end]))
    return output


def _bounded(descriptors: Sequence[_Descriptor], maximum: int) -> tuple[list[_Descriptor], int]:
    if len(descriptors) <= maximum:
        return list(descriptors), 0
    first_count = (maximum + 1) // 2
    last_count = maximum - first_count
    selected = list(descriptors[:first_count])
    if last_count:
        selected.extend(descriptors[-last_count:])
    return selected, len(descriptors) - maximum


def _deduplicate(program: Mapping[str, Any], units: Sequence[CompiledUnit]) -> list[CompiledUnit]:
    if program["duplicate_policy"] == "preserve_all":
        return list(units)
    selected: dict[tuple[str, str], CompiledUnit] = {}
    for unit in sorted(units, key=lambda item: (item.family_id, item.publication_id, item.unit_id)):
        selected.setdefault((unit.family_id, unit.content_sha256), unit)
    return list(selected.values())
