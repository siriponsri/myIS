"""Deterministic SCOPE compiler."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from ..kernel.canonical import sha256_hex
from ..kernel.errors import FailureCategory, KernelContractError
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
            parts = [str(row[field]).strip() for field in view.source_fields if str(row.get(field, "")).strip()]
            text = "\n\n".join(parts)
            if view.searchable and not text:
                raise KernelContractError(
                    f"searchable view {view.view_id!r} produced empty text", FailureCategory.PROVENANCE
                )
            source_span = f"{view.span_scheme}:" + ",".join(view.source_fields)
            source_fields_hash = sha256_hex({field: row.get(field) for field in view.source_fields})
            mapped_official = tuple(str(item) for item in row.get("official_passage_ids", ()) or ())
            semantic = {
                "family_id": family_id,
                "publication_id": publication_id,
                "view_id": view.view_id,
                "source_span": source_span,
                "source_hash": source_fields_hash,
                "text": text,
            }
            units.append(
                CompiledUnit(
                    unit_id="unit-" + sha256_hex(semantic)[:24],
                    view_id=view.view_id,
                    family_id=family_id,
                    publication_id=publication_id,
                    text=text,
                    source_fields=view.source_fields,
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
