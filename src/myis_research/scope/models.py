"""Pydantic contracts for the active SCOPE DSL."""

from __future__ import annotations

from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ScopeValidationError(ValueError):
    pass


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ScopeField(StrictModel):
    field_id: str = Field(pattern=r"^[a-z][a-z0-9_.-]*$")
    source: str = Field(pattern=r"^[a-z][a-z0-9_.-]*$")
    role: Literal["identity", "text", "span", "metadata"]


class ScopeView(StrictModel):
    view_id: str = Field(pattern=r"^[a-z][a-z0-9_.-]*$")
    kind: Literal["document", "section", "claim", "passage", "generated"]
    source_fields: tuple[str, ...] = Field(min_length=1)
    family_field: str = Field(pattern=r"^[a-z][a-z0-9_.-]*$")
    publication_field: str = Field(pattern=r"^[a-z][a-z0-9_.-]*$")
    span_scheme: str = Field(min_length=1)
    compiler_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    normalization_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    searchable: bool = True
    aggregation: Literal["family_maxp", "family_first", "official", "none"] = "family_maxp"
    deterministic_order: Literal["source", "lexicographic", "explicit"] = "source"
    source_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    output_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @field_validator("source_fields")
    @classmethod
    def unique_source_fields(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("source_fields must be unique and ordered")
        return value


class ScopeConstraints(StrictModel):
    require_source_grounding: Literal[True]
    abstractive_summaries: Literal[False]
    query_specific_vocabulary: Literal[False]
    adapter_limits: Mapping[str, int] = Field(default_factory=dict)

    @field_validator("adapter_limits")
    @classmethod
    def valid_adapter_limits(cls, value: Mapping[str, int]) -> dict[str, int]:
        normalized = dict(value)
        if any(not isinstance(limit, int) or limit <= 0 for limit in normalized.values()):
            raise ValueError("adapter limits must be positive integers")
        return normalized


class ScopeSpec(StrictModel):
    schema_version: Literal["myis.scope-dsl.v1"]
    spec_id: str = Field(pattern=r"^spec-[a-z0-9][a-z0-9-]*-v[0-9]{2}$")
    parent_spec_id: str | None = None
    hypothesis_id: str = Field(pattern=r"^hyp-i[0-9]{2}-[0-9]{3}$")
    compiler_api_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    description: Mapping[str, str]
    fields: tuple[ScopeField, ...]
    claims: Mapping[str, str]
    graph: Mapping[str, Any]
    views: tuple[ScopeView, ...] = Field(min_length=1)
    aggregation: Mapping[str, Any]
    constraints: ScopeConstraints

    @field_validator("fields")
    @classmethod
    def unique_fields(cls, value: tuple[ScopeField, ...]) -> tuple[ScopeField, ...]:
        ids = [field.field_id for field in value]
        if len(ids) != len(set(ids)):
            raise ValueError("field_id values must be unique")
        return value

    @field_validator("views")
    @classmethod
    def unique_views(cls, value: tuple[ScopeView, ...]) -> tuple[ScopeView, ...]:
        ids = [view.view_id for view in value]
        if len(ids) != len(set(ids)):
            raise ValueError("view_id values must be unique")
        return value

    @model_validator(mode="after")
    def validate_references(self) -> "ScopeSpec":
        known = {field.field_id for field in self.fields}
        for view in self.views:
            missing = set(view.source_fields) - known
            if missing:
                raise ValueError(f"view {view.view_id!r} references unknown fields: {sorted(missing)}")
        return self


def parse_scope_spec(value: ScopeSpec | Mapping[str, Any]) -> ScopeSpec:
    try:
        return value if isinstance(value, ScopeSpec) else ScopeSpec.model_validate(value)
    except Exception as exc:  # pydantic emits several concrete error classes
        raise ScopeValidationError(str(exc)) from exc
