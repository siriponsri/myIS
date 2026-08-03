"""Deterministic SCOPE compiler."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping

from ..kernel.canonical import sha256_hex
from ..kernel.errors import FailureCategory, KernelContractError
from ..kernel.p1 import tokenize
from .adapters import DapfamAdapter, FinePatentsAdapter
from .models import ScopeSpec, parse_scope_spec


@dataclass(frozen=True)
class CompiledUnit:
    unit_id: str
    view_id: str
    family_id: str
    publication_id: str
    text: str
    source_fields: tuple[str, ...]
    source_span: str
    source_hash: str
    searchable: bool
    official_passage_ids: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "view_id": self.view_id,
            "family_id": self.family_id,
            "publication_id": self.publication_id,
            "text": self.text,
            "source_fields": list(self.source_fields),
            "source_span": self.source_span,
            "source_hash": self.source_hash,
            "searchable": self.searchable,
            "official_passage_ids": list(self.official_passage_ids),
        }


@dataclass(frozen=True)
class CompiledScope:
    spec_id: str
    compiler_api_version: str
    source_hash: str
    output_hash: str
    units: tuple[CompiledUnit, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "spec_id": self.spec_id,
            "compiler_api_version": self.compiler_api_version,
            "source_hash": self.source_hash,
            "output_hash": self.output_hash,
            "units": [unit.as_dict() for unit in self.units],
        }


def compile_scope(
    spec: ScopeSpec | Mapping[str, Any],
    records: Iterable[Mapping[str, Any]],
    *,
    adapter: str | DapfamAdapter | FinePatentsAdapter = "dapfam",
    official_passages: Iterable[Mapping[str, Any]] | None = None,
) -> CompiledScope:
    parsed = parse_scope_spec(spec)
    rows = tuple(dict(row) for row in records)
    source_hash = sha256_hex(sorted(rows, key=lambda row: tuple((str(key), str(value)) for key, value in sorted(row.items()))))
    resolved = _resolve_adapter(adapter)
    units: list[CompiledUnit] = []
    for row in rows:
        for view in parsed.views:
            family_id = _required(row, view.family_field, "family_id")
            publication_id = _required(row, view.publication_field, "publication_id")
            missing_fields = [field for field in view.source_fields if field not in row]
            if missing_fields:
                raise KernelContractError(
                    f"record is missing source fields for view {view.view_id!r}: {missing_fields}",
                    FailureCategory.PROVENANCE,
                )
            descriptors = _compile_view_descriptors(parsed, view.view_id, view.kind, view.source_fields, row)
            if view.searchable and not descriptors:
                raise KernelContractError(
                    f"searchable view {view.view_id!r} produced empty text", FailureCategory.PROVENANCE
                )
            mapped_official = tuple(str(item) for item in row.get("official_passage_ids", ()) or ())
            for descriptor in descriptors:
                source_fields = tuple(descriptor["source_fields"])
                source_span = f"{view.span_scheme}:{descriptor['source_span']}"
                source_fields_hash = sha256_hex({
                    "fields": {field: row.get(field) for field in source_fields},
                    "source_span": source_span,
                })
                semantic = {
                    "family_id": family_id,
                    "publication_id": publication_id,
                    "view_id": view.view_id,
                    "source_span": source_span,
                    "source_hash": source_fields_hash,
                    "text": descriptor["text"],
                }
                units.append(
                    CompiledUnit(
                        unit_id="unit-" + sha256_hex(semantic)[:24],
                        view_id=view.view_id,
                        family_id=family_id,
                        publication_id=publication_id,
                        text=str(descriptor["text"]),
                        source_fields=source_fields,
                        source_span=source_span,
                        source_hash=source_fields_hash,
                        searchable=view.searchable,
                        official_passage_ids=mapped_official,
                    )
                )
    units.sort(key=lambda unit: (unit.family_id, unit.publication_id, unit.view_id, unit.unit_id))
    if isinstance(resolved, DapfamAdapter):
        resolved.validate_units([unit.as_dict() for unit in units])
    elif isinstance(resolved, FinePatentsAdapter):
        if official_passages is None:
            raise KernelContractError("FiNE compilation requires official_passages", FailureCategory.PROVENANCE)
        resolved.validate_generated_units(official_passages, [unit.as_dict() for unit in units])
    output_hash = sha256_hex([unit.as_dict() for unit in units])
    return CompiledScope(parsed.spec_id, parsed.compiler_api_version, source_hash, output_hash, tuple(units))


def _compile_view_descriptors(
    spec: ScopeSpec,
    view_id: str,
    view_kind: str,
    source_fields: tuple[str, ...],
    row: Mapping[str, Any],
) -> list[dict[str, Any]]:
    policy_root = spec.graph.get("unitization", {})
    policy = policy_root.get(view_id, {}) if isinstance(policy_root, Mapping) else {}
    if not isinstance(policy, Mapping) or not policy:
        parts = [str(row[field]).strip() for field in source_fields if str(row.get(field, "")).strip()]
        return [{
            "text": "\n\n".join(parts),
            "source_fields": source_fields,
            "source_span": ",".join(source_fields),
        }] if parts else []

    mode = str(policy.get("mode", "joined_document"))
    max_units = int(policy.get("max_units", 4))
    if max_units < 1 or max_units > 4:
        raise KernelContractError("SCOPE unitization max_units must be between one and four", FailureCategory.CONSTRAINT)
    if mode == "joined_document":
        return _joined_descriptor(source_fields, row)
    if mode == "field_sections":
        descriptors = [
            {"text": str(row[field]).strip(), "source_fields": (field,), "source_span": field}
            for field in source_fields
            if str(row.get(field, "")).strip()
        ]
        return _bounded_descriptors(descriptors, max_units)
    if mode == "claim_elements":
        if view_kind != "claim":
            raise KernelContractError("claim_elements unitization requires a claim view", FailureCategory.SCHEMA)
        descriptors: list[dict[str, Any]] = []
        for field in source_fields:
            text = str(row.get(field, "")).strip()
            for index, (start, end, claim) in enumerate(_claim_spans(text)):
                descriptors.append({
                    "text": claim,
                    "source_fields": (field,),
                    "source_span": f"{field}:claim:{index:06d}:char:{start}-{end}",
                })
        return _bounded_descriptors(descriptors, max_units)
    if mode == "token_passages":
        if view_kind != "passage":
            raise KernelContractError("token_passages unitization requires a passage view", FailureCategory.SCHEMA)
        window = int(policy.get("window_tokens", 0))
        stride = int(policy.get("stride_tokens", window))
        if window <= 0 or stride <= 0:
            raise KernelContractError("passage window and stride must be positive", FailureCategory.CONSTRAINT)
        joined = "\n\n".join(
            str(row[field]).strip() for field in source_fields if str(row.get(field, "")).strip()
        )
        tokens = tokenize(joined)
        descriptors = [
            {
                "text": " ".join(tokens[start : start + window]),
                "source_fields": source_fields,
                "source_span": f"tokens:{start}-{min(start + window, len(tokens))}",
            }
            for start in range(0, len(tokens), stride)
            if tokens[start : start + window]
        ]
        return _bounded_descriptors(descriptors, max_units)
    if mode == "multiview":
        groups = policy.get("source_field_groups")
        if not isinstance(groups, list) or not groups:
            raise KernelContractError("multiview requires source_field_groups", FailureCategory.SCHEMA)
        allowed = set(source_fields)
        descriptors = []
        for index, group in enumerate(groups):
            if not isinstance(group, list) or not group or any(str(field) not in allowed for field in group):
                raise KernelContractError("multiview source_field_groups must reference declared fields", FailureCategory.SCHEMA)
            normalized = tuple(str(field) for field in group)
            parts = [str(row[field]).strip() for field in normalized if str(row.get(field, "")).strip()]
            if parts:
                descriptors.append({
                    "text": "\n\n".join(parts),
                    "source_fields": normalized,
                    "source_span": f"view:{index:02d}:" + ",".join(normalized),
                })
        return _bounded_descriptors(descriptors, max_units)
    raise KernelContractError(f"unsupported SCOPE unitization mode: {mode!r}", FailureCategory.SCHEMA)


def _joined_descriptor(source_fields: tuple[str, ...], row: Mapping[str, Any]) -> list[dict[str, Any]]:
    parts = [str(row[field]).strip() for field in source_fields if str(row.get(field, "")).strip()]
    if not parts:
        return []
    return [{"text": "\n\n".join(parts), "source_fields": source_fields, "source_span": ",".join(source_fields)}]


def _bounded_descriptors(descriptors: list[dict[str, Any]], max_units: int) -> list[dict[str, Any]]:
    if len(descriptors) <= max_units:
        return descriptors
    first_count = (max_units + 1) // 2
    last_count = max_units - first_count
    selected = descriptors[:first_count]
    if last_count:
        selected.extend(descriptors[-last_count:])
    return selected


def _claim_spans(text: str) -> list[tuple[int, int, str]]:
    if not text:
        return []
    starts = [match.start() for match in re.finditer(r"(?m)(?=^\s*\d+[\.)]\s+)", text)]
    if not starts:
        paragraphs = list(re.finditer(r"[^\n]+(?:\n(?!\s*\d+[\.)]\s+)[^\n]+)*", text))
        return [(match.start(), match.end(), match.group(0).strip()) for match in paragraphs if match.group(0).strip()]
    spans: list[tuple[int, int, str]] = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(text)
        claim = text[start:end].strip()
        if claim:
            spans.append((start, end, claim))
    return spans


def _resolve_adapter(adapter: str | DapfamAdapter | FinePatentsAdapter) -> DapfamAdapter | FinePatentsAdapter:
    if isinstance(adapter, (DapfamAdapter, FinePatentsAdapter)):
        return adapter
    if adapter.casefold() == "dapfam":
        return DapfamAdapter()
    if adapter.casefold() in {"fine", "fine_patents", "fine-patents"}:
        return FinePatentsAdapter()
    raise KernelContractError(f"unsupported SCOPE adapter: {adapter!r}", FailureCategory.SCHEMA)


def _required(row: Mapping[str, Any], key: str, label: str) -> str:
    value = row.get(key)
    if value is None or not str(value).strip():
        raise KernelContractError(f"record is missing {label} field {key!r}", FailureCategory.IDENTITY)
    return str(value).strip()
