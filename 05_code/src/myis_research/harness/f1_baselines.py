"""G1-bound F1 baseline contracts and source-free replay helpers.

This module is safe to import before G1. It contains no dataset readers,
network clients, model loaders, evaluators, or artifact writers.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterable, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .candidate_ledger import (
    FamilyCandidate,
    RouteHit,
    build_family_ledger,
    candidate_ledger_bytes,
)


FROZEN_F1_RUNSPEC_SCHEMA = "myis.frozen-f1-runspec.v1"
LOCKED_ENCODER = "Llama-Embed-Nemotron-8B"
LOCKED_ENCODER_REVISION = "aa3b43a495a9b280d1bdb716da37c54bb495d630"
SHA256_PATTERN = r"^[0-9a-f]{64}$"
_SOURCE_ROLES = frozenset({"corpus", "queries", "qrels", "family", "evaluator", "field_protocol"})
_SPLIT_ROLES = frozenset({"train", "selection", "joint_test"})
_ENVIRONMENT_ROLES = frozenset({"uv_lock", "python", "code"})


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class B0Protocol(_StrictModel):
    view: Literal["TAC"]
    dense_top_k: Literal[400]
    final_family_k: Literal[100]


class B1Protocol(_StrictModel):
    view: Literal["TAC"]
    dense_top_k: Literal[400]
    bm25_top_k: Literal[400]
    fusion: Literal["minmax_weighted"]
    dense_weight: Literal[0.7]
    bm25_weight: Literal[0.3]
    final_family_k: Literal[100]


class B2Protocol(_StrictModel):
    views: tuple[Literal["TAC", "Abstract", "Claim1"], ...]
    fusion: Literal["rrf"]
    rrf_k: Literal[60]
    final_family_k: Literal[100]

    @model_validator(mode="after")
    def exact_views(self) -> "B2Protocol":
        if self.views != ("TAC", "Abstract", "Claim1"):
            raise ValueError("B2 views must be TAC, Abstract, Claim1 in protocol order")
        return self


class BaselineProtocol(_StrictModel):
    B0: B0Protocol
    B1: B1Protocol
    B2: B2Protocol


class ModelArtifactCommitment(_StrictModel):
    model_id: Literal[LOCKED_ENCODER]
    revision: Literal[LOCKED_ENCODER_REVISION]
    artifact_sha256: str = Field(pattern=SHA256_PATTERN)
    manifest_sha256: str = Field(pattern=SHA256_PATTERN)


class ExecutionBudget(_StrictModel):
    compute_class: Literal["local_cpu", "owned_gpu", "approved_cloud_gpu"]
    max_threads: int = Field(ge=1, le=256)
    max_wall_seconds: int = Field(gt=0)
    max_temp_bytes: int = Field(gt=0)
    max_cost_usd: float = Field(ge=0)


class AccessPolicy(_StrictModel):
    provider: str = Field(min_length=1, max_length=128)
    endpoint_class: Literal["local", "official", "third_party"]
    network_access: Literal["none", "owner_approved_model_download"]
    data_egress: Literal[False]
    fallback: Literal["forbidden"]
    parameter_dropping: Literal[False]


class RuntimeIdentity(_StrictModel):
    python_version: str = Field(pattern=r"^3\.11\.\d+$")
    uv_version: str = Field(min_length=1, max_length=64)
    os: str = Field(min_length=1, max_length=128)
    architecture: str = Field(min_length=1, max_length=64)
    accelerator: str = Field(min_length=1, max_length=64)
    cuda_stack: str | None = Field(default=None, max_length=128)
    selected_groups: tuple[str, ...]
    selected_extras: tuple[str, ...]


class FrozenF1RunSpecV1(_StrictModel):
    """Exact pre-decision RunSpec that a later immutable G1 record must bind."""

    schema_version: Literal[FROZEN_F1_RUNSPEC_SCHEMA]
    status: Literal["frozen"]
    executable: Literal[True]
    gate: Literal["G1"]
    authorization: Literal["F1.1_B0_B1_B2_ONLY"]
    track: Literal["C"]
    phase: Literal["F1"]
    task: Literal["F1.1"]
    arms: tuple[Literal["B0", "B1", "B2"], ...]
    git_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    owner_value_batch_sha256: str = Field(pattern=SHA256_PATTERN)
    proposal_sha256: str = Field(pattern=SHA256_PATTERN)
    source_sha256: dict[str, str]
    split_membership_sha256: dict[str, str]
    environment_sha256: dict[str, str]
    model: ModelArtifactCommitment
    protocol: BaselineProtocol
    budget: ExecutionBudget
    runtime: RuntimeIdentity
    access: AccessPolicy

    @field_validator("arms")
    @classmethod
    def exact_arms(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if value != ("B0", "B1", "B2"):
            raise ValueError("F1 RunSpec must bind B0, B1, B2 in protocol order")
        return value

    @model_validator(mode="after")
    def exact_hash_closure(self) -> "FrozenF1RunSpecV1":
        _validate_hash_map(self.source_sha256, _SOURCE_ROLES, "source")
        _validate_hash_map(self.split_membership_sha256, _SPLIT_ROLES, "split membership")
        _validate_hash_map(self.environment_sha256, _ENVIRONMENT_ROLES, "environment")
        return self


@dataclass(frozen=True, slots=True)
class BaselineReplay:
    arm: str
    candidates: tuple[FamilyCandidate, ...]
    ledger_sha256: str


@dataclass(frozen=True, slots=True)
class ResourcePreflight:
    status: Literal["PASS", "RESOURCE_BLOCKED"]
    reason: str
    manifest_sha256: str | None
    network_access: Literal["none"] = "none"
    model_loaded: Literal[False] = False


def validate_frozen_f1_runspec(payload: Mapping[str, object]) -> FrozenF1RunSpecV1:
    return FrozenF1RunSpecV1.model_validate(payload)


def replay_fixture_baselines(fixtures: Mapping[str, Iterable[RouteHit]]) -> dict[str, BaselineReplay]:
    """Replay B0/B1/B2 from synthetic hits without data, qrels, or metrics."""

    if set(fixtures) != {"B0", "B1", "B2"}:
        raise ValueError("fixture replay requires exactly B0, B1, and B2")
    materialized = {arm: tuple(hits) for arm, hits in fixtures.items()}
    _validate_fixture_hits("B0", materialized["B0"], {"dense"}, {"tac"}, 400)
    _validate_fixture_hits("B1", materialized["B1"], {"dense", "bm25"}, {"tac"}, 400)
    _validate_fixture_hits(
        "B2", materialized["B2"], {"tac", "abstract", "claim1"}, {"tac", "abstract", "claim1"}, 400
    )
    rows = {
        "B0": build_family_ledger(materialized["B0"], fusion_method="max", final_k=100),
        "B1": build_family_ledger(
            materialized["B1"],
            fusion_method="minmax_weighted",
            weights={"dense": 0.7, "bm25": 0.3},
            score_directions={"dense": "higher", "bm25": "lower"},
            final_k=100,
        ),
        "B2": build_family_ledger(materialized["B2"], fusion_method="rrf", fusion_k=60, final_k=100),
    }
    return {
        arm: BaselineReplay(arm, candidates, hashlib.sha256(candidate_ledger_bytes(candidates)).hexdigest())
        for arm, candidates in rows.items()
    }


def preflight_model_manifest(path: Path | None, commitment: ModelArtifactCommitment) -> ResourcePreflight:
    """Validate only the local model manifest; never load or download model bytes."""

    if path is None or not path.exists():
        return ResourcePreflight("RESOURCE_BLOCKED", "LOCKED_MODEL_MANIFEST_MISSING", None)
    if path.is_symlink() or not path.is_file():
        return ResourcePreflight("RESOURCE_BLOCKED", "LOCKED_MODEL_MANIFEST_NOT_REGULAR", None)
    manifest_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    if manifest_sha256 != commitment.manifest_sha256:
        return ResourcePreflight("RESOURCE_BLOCKED", "LOCKED_MODEL_MANIFEST_HASH_MISMATCH", manifest_sha256)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return ResourcePreflight("RESOURCE_BLOCKED", "LOCKED_MODEL_MANIFEST_INVALID", manifest_sha256)
    expected = {
        "schema_version": "myis.model-artifact.v1",
        "model_id": commitment.model_id,
        "revision": commitment.revision,
        "artifact_sha256": commitment.artifact_sha256,
    }
    if payload != expected:
        return ResourcePreflight("RESOURCE_BLOCKED", "LOCKED_MODEL_IDENTITY_MISMATCH", manifest_sha256)
    return ResourcePreflight("PASS", "LOCKED_MODEL_MANIFEST_VALID", manifest_sha256)


def _validate_hash_map(value: Mapping[str, str], expected: frozenset[str], label: str) -> None:
    if set(value) != expected or any(not _is_sha256(item) for item in value.values()):
        raise ValueError(f"{label} hashes must cover exactly {sorted(expected)}")


def _validate_fixture_hits(
    arm: str,
    hits: tuple[RouteHit, ...],
    routes: set[str],
    views: set[str],
    max_rank: int,
) -> None:
    if not hits:
        raise ValueError(f"{arm} fixture hits cannot be empty")
    for hit in hits:
        hit.validate()
        if hit.route_id.casefold() not in routes or hit.view_id.casefold() not in views:
            raise ValueError(f"{arm} fixture route/view drift")
        if hit.rank > max_rank:
            raise ValueError(f"{arm} fixture rank exceeds raw top-{max_rank}")
    observed_routes = {hit.route_id.casefold() for hit in hits}
    observed_views = {hit.view_id.casefold() for hit in hits}
    if observed_routes != routes or observed_views != views:
        raise ValueError(f"{arm} fixture must cover every protocol route and view")


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)
