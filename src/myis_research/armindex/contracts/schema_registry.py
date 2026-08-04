"""Grouped JSON Schema registry for the typed ArmIndex contracts."""

from __future__ import annotations

import json
from functools import reduce
from operator import or_
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator
from pydantic import TypeAdapter

from .models import (
    AggregateMetric,
    AggregateReceipt,
    ArmAdapterLock,
    ArmIndexContract,
    ArmSpecification,
    AutoIndexBatch,
    AutoIndexCandidate,
    BrainProjectionEvent,
    CandidatePool,
    CompiledRepresentation,
    ComplementarityReport,
    CostReceipt,
    EvaluationRequest,
    FamilyDocument,
    FamilyRanking,
    FusionConfiguration,
    HarnessAction,
    HarnessConfiguration,
    IndexManifest,
    MLflowMirrorEvent,
    PhaseCloseoutEvent,
    ProductionProfile,
    QueryFamily,
    RepresentationProgram,
    RunManifest,
    SearchHit,
    SearchRequest,
    SearchableUnit,
    SourceSpan,
    TransferEvaluation,
)


CONTRACT_GROUPS: dict[str, tuple[type[ArmIndexContract], ...]] = {
    "domain-contracts.v1.json": (FamilyDocument, QueryFamily, SearchableUnit, SourceSpan),
    "representation-contracts.v1.json": (RepresentationProgram, CompiledRepresentation),
    "arm-contracts.v1.json": (ArmSpecification, ArmAdapterLock),
    "retrieval-contracts.v1.json": (IndexManifest, SearchRequest, SearchHit, FamilyRanking, CandidatePool),
    "optimization-contracts.v1.json": (
        FusionConfiguration,
        TransferEvaluation,
        ComplementarityReport,
        AutoIndexCandidate,
        AutoIndexBatch,
    ),
    "harness-production-contracts.v1.json": (HarnessConfiguration, HarnessAction, ProductionProfile),
    "evaluation-contracts.v1.json": (EvaluationRequest, AggregateMetric),
    "evidence-lifecycle-contracts.v1.json": (
        RunManifest,
        AggregateReceipt,
        CostReceipt,
        PhaseCloseoutEvent,
        BrainProjectionEvent,
        MLflowMirrorEvent,
    ),
}


def grouped_json_schemas() -> dict[str, dict[str, Any]]:
    """Return deterministic Draft 2020-12 schemas for all contract groups."""

    output: dict[str, dict[str, Any]] = {}
    for filename, models in CONTRACT_GROUPS.items():
        union_type = reduce(or_, models)
        schema = TypeAdapter(union_type).json_schema(union_format="any_of")
        stem = filename.removesuffix(".json")
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"urn:myis:armindex:{stem.replace('.', ':')}",
            "title": f"ArmIndex {stem.replace('-', ' ')}",
            **schema,
        }
        Draft202012Validator.check_schema(schema)
        output[filename] = schema
    return output


def write_grouped_json_schemas(repository_root: Path) -> tuple[Path, ...]:
    """Materialize the deterministic schema registry under schemas/armindex."""

    root = Path(repository_root).resolve() / "schemas" / "armindex"
    root.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for filename, schema in grouped_json_schemas().items():
        path = root / filename
        path.write_text(json.dumps(schema, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        paths.append(path)
    return tuple(paths)


def validate_grouped_schema(repository_root: Path, value: Mapping[str, Any]) -> None:
    """Validate one serialized typed contract against its checked-in group."""

    schema_version = str(value.get("schema_version", ""))
    for filename, models in CONTRACT_GROUPS.items():
        versions = {
            model.model_fields["schema_version"].annotation.__args__[0]
            for model in models
        }
        if schema_version not in versions:
            continue
        path = Path(repository_root).resolve() / "schemas" / "armindex" / filename
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(dict(value))
        return
    raise ValueError(f"unsupported ArmIndex contract schema: {schema_version!r}")


__all__ = ["CONTRACT_GROUPS", "grouped_json_schemas", "validate_grouped_schema", "write_grouped_json_schemas"]
