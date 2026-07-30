from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping

from ..kernel.canonical import canonical_sha256, stable_id
from ..kernel.failures import FailureCategory, KernelFailure


@dataclass(frozen=True)
class ScopeSpec:
    schema_version: str
    spec_id: str
    parent_spec_id: str | None
    hypothesis_id: str
    compiler_api_version: str
    views: tuple[dict[str, object], ...]
    aggregation: dict[str, object]
    constraints: dict[str, object]


def parse_scope(payload: Mapping[str, object]) -> ScopeSpec:
    required = {"schema_version", "spec_id", "parent_spec_id", "hypothesis_id", "compiler_api_version", "views", "aggregation", "constraints"}
    if set(payload) != required:
        raise KernelFailure(FailureCategory.COMPILER, f"scope fields must be exactly {sorted(required)}")
    if payload["schema_version"] != "myis.scope-dsl.v1" or not isinstance(payload["views"], list) or not payload["views"]:
        raise KernelFailure(FailureCategory.COMPILER, "invalid SCOPE schema or empty views")
    constraints = payload["constraints"]
    if not isinstance(constraints, Mapping) or constraints.get("require_source_grounding") is not True or constraints.get("abstractive_summaries") is not False:
        raise KernelFailure(FailureCategory.COMPILER, "SCOPE requires grounded non-abstractive units")
    views: list[dict[str, object]] = []
    for view in payload["views"]:
        if not isinstance(view, Mapping):
            raise KernelFailure(FailureCategory.COMPILER, "view must be an object")
        expected = {"view_id", "kind", "source", "identity", "searchability", "aggregation"}
        if set(view) != expected:
            raise KernelFailure(FailureCategory.COMPILER, f"view fields must be exactly {sorted(expected)}")
        if not isinstance(view["source"], Mapping) or not view["source"].get("field"):
            raise KernelFailure(FailureCategory.COMPILER, "view source.field is required")
        if not isinstance(view["identity"], Mapping) or not view["identity"].get("family_field") or not view["identity"].get("publication_field"):
            raise KernelFailure(FailureCategory.COMPILER, "view identity must bind family and publication")
        views.append(dict(view))
    return ScopeSpec(str(payload["schema_version"]), str(payload["spec_id"]), payload["parent_spec_id"] if payload["parent_spec_id"] is None else str(payload["parent_spec_id"]), str(payload["hypothesis_id"]), str(payload["compiler_api_version"]), tuple(views), dict(payload["aggregation"]), dict(constraints))


def compile_scope(spec: ScopeSpec, record: Mapping[str, object]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for view in spec.views:
        source = view["source"]
        identity = view["identity"]
        field = str(source["field"])
        value = record.get(field)
        if value is None:
            continue
        values = value if isinstance(value, list) else [value]
        for index, raw in enumerate(values):
            text = str(raw).strip()
            if not text:
                continue
            unit = {
                "unit_id": stable_id("unit", {"spec": spec.spec_id, "view": view["view_id"], "record": record.get(str(identity["publication_field"])), "index": index, "text": text}),
                "view_id": view["view_id"], "kind": view["kind"],
                "family_id": str(record.get(str(identity["family_field"]), "")),
                "publication_id": str(record.get(str(identity["publication_field"]), "")),
                "source_field": field, "source_index": index, "text": text,
                "source_sha256": canonical_sha256({"field": field, "value": raw}),
                "compiler_api_version": spec.compiler_api_version,
                "searchable": bool(view["searchability"].get("enabled", True)),
                "aggregation": dict(view["aggregation"]),
            }
            output.append(unit)
    return sorted(output, key=lambda item: (str(item["family_id"]), str(item["publication_id"]), str(item["view_id"]), int(item["source_index"])))
