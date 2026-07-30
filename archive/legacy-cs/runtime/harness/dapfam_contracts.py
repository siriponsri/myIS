"""Typed, preparation-only DAPFAM commitments.

The payloads in this module are hash/count-only. Raw query membership belongs
in the Owner-local sealed store and must never be serialized through these
models.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..identity import PROGRAM_ID, PROTOCOL_VERSION, RESEARCH_VERSION


OWNER_VALUE_BATCH_SCHEMA = "myis.g1-owner-value-batch.v1"
SAFE_PROJECTION_SCHEMA = "myis.f1-g1-safe-projection.v1"
SHA256_PATTERN = r"^[0-9a-f]{64}$"
SPLIT_COUNTS = {"train": 250, "selection": 125, "joint_test": 872}
SPLIT_ALIASES = {
    "c_train": "train",
    "train": "train",
    "adaptation": "train",
    "c_selection": "selection",
    "selection": "selection",
    "joint_test": "joint_test",
    "confirmation": "joint_test",
}


def canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")


def sha256_payload(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceCommitment(StrictModel):
    role: Literal["corpus", "queries", "qrels", "out_strata", "validation"]
    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]+$")
    relative_path: str
    bytes: int = Field(gt=0)
    sha256: str = Field(pattern=SHA256_PATTERN)

    @field_validator("relative_path")
    @classmethod
    def safe_relative_path(cls, value: str) -> str:
        normalized = value.replace("\\", "/")
        if normalized.startswith("/") or ":" in normalized or ".." in normalized.split("/"):
            raise ValueError("source commitment path must be a safe relative hint")
        return normalized


class SplitCommitment(StrictModel):
    seed: Literal[42]
    algorithm: Literal["hamilton-sha256-v1"]
    counts: dict[str, int]
    membership_sha256: dict[str, str]
    out_positive_counts: dict[str, int]
    out_positive_total: int = Field(ge=0)
    aliases: dict[str, str]

    @model_validator(mode="after")
    def validate_split(self) -> "SplitCommitment":
        if self.counts != SPLIT_COUNTS:
            raise ValueError("split counts must be train=250, selection=125, joint_test=872")
        if set(self.membership_sha256) != set(SPLIT_COUNTS):
            raise ValueError("membership hashes must cover all safe split roles")
        if any(not _is_sha256(value) for value in self.membership_sha256.values()):
            raise ValueError("membership commitments must be SHA-256")
        if set(self.out_positive_counts) != set(SPLIT_COUNTS):
            raise ValueError("OUT-positive counts must cover all safe split roles")
        if sum(self.out_positive_counts.values()) != self.out_positive_total:
            raise ValueError("OUT-positive split counts must sum to the declared total")
        if self.aliases != SPLIT_ALIASES:
            raise ValueError("split aliases drifted from the locked contract")
        return self


class ValidationReceipt(StrictModel):
    status: Literal["PASS"]
    validated_at_utc: datetime
    checks: dict[str, bool]
    safe_batch_sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)

    @field_validator("checks")
    @classmethod
    def all_checks_pass(cls, value: dict[str, bool]) -> dict[str, bool]:
        if not value or not all(value.values()):
            raise ValueError("every preparation validation check must pass")
        return value


class GeneratorIdentity(StrictModel):
    program_id: Literal[PROGRAM_ID]
    protocol_version: Literal[PROTOCOL_VERSION]
    research_version: Literal[RESEARCH_VERSION]
    package_version: Literal["0.1.0"]
    git_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    python_version: str
    platform: str


class EvaluatorCommitment(StrictModel):
    evaluator_id: Literal["dapfam-family-retrieval-v1"]
    unit: Literal["patent_family"]
    relevance_rule: Literal["grade_gt_0"]
    primary_metric: Literal["recall_at_100"]
    claim_boundary: Literal["retrieval_relevance_not_legal_truth"]


class PublishedTargetsCommitment(StrictModel):
    encoder: Literal["Llama-Embed-Nemotron-8B"]
    encoder_revision: Literal["aa3b43a495a9b280d1bdb716da37c54bb495d630"]
    arms: tuple[Literal["B0", "B1", "B2"], ...]

    @model_validator(mode="after")
    def exact_arms(self) -> "PublishedTargetsCommitment":
        if self.arms != ("B0", "B1", "B2"):
            raise ValueError("published targets must bind B0/B1/B2 in protocol order")
        return self


class OwnerValueBatchV1(StrictModel):
    schema_version: Literal[OWNER_VALUE_BATCH_SCHEMA]
    document_kind: Literal["g1_owner_value_batch"]
    status: Literal["proposal"]
    executable: Literal[False]
    gate: Literal["G1"]
    gate_status: Literal["pending"]
    authorization: Literal["NOT_AUTHORIZED"]
    scientific_run: Literal[False]
    dataset_access: Literal["owner_local_read_only"]
    scientific_metric_count: Literal[0]
    track: Literal["C"]
    phase: Literal["F1"]
    task: Literal["F1.1"]
    proposal_sha256: str = Field(pattern=SHA256_PATTERN)
    generated_at_utc: datetime
    generator: GeneratorIdentity
    sources: list[SourceCommitment]
    inventory_counts: dict[str, int]
    qrels_domain_distribution: dict[str, int]
    family_commitment_sha256: str = Field(pattern=SHA256_PATTERN)
    evaluator: EvaluatorCommitment
    field_protocol: dict[str, Any]
    published_targets: PublishedTargetsCommitment
    split: SplitCommitment
    validation: ValidationReceipt
    unresolved_owner_decisions: list[str]
    owner_decision_sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)
    mlflow: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_batch(self) -> "OwnerValueBatchV1":
        roles = [item.role for item in self.sources]
        if sorted(roles) != sorted({"corpus", "queries", "qrels", "out_strata", "validation"}):
            raise ValueError("source commitments must contain each required role exactly once")
        expected = proposal_hash(self.model_dump(mode="json"))
        if self.proposal_sha256 != expected:
            raise ValueError("proposal_sha256 does not match canonical semantic content")
        forbidden = {"query_ids", "membership", "absolute_path", "per_query", "metrics", "results"}
        if forbidden & _all_keys(self.model_dump(mode="json")):
            raise ValueError("safe batch contains a protected or measured field")
        if self.inventory_counts != {"corpus": 45_336, "queries": 1_247, "qrels": 49_869}:
            raise ValueError("DAPFAM inventory counts drifted from the validated source")
        if set(self.qrels_domain_distribution) != {"IN", "OUT", "NC"}:
            raise ValueError("qrels domain distribution must cover IN, OUT, and NC")
        if sum(self.qrels_domain_distribution.values()) != 49_869:
            raise ValueError("qrels domain distribution must cover every qrels row")
        if set(self.field_protocol) != {"B0", "B1", "B2"}:
            raise ValueError("field protocol must bind exactly B0/B1/B2")
        return self


_PROPOSAL_EXCLUDED = {
    "proposal_sha256",
    "generated_at_utc",
    "validation",
    "owner_decision_sha256",
    "mlflow",
}


def proposal_semantics(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key not in _PROPOSAL_EXCLUDED}


def proposal_hash(payload: Mapping[str, Any]) -> str:
    return sha256_payload(proposal_semantics(payload))


def validate_owner_value_batch(payload: Mapping[str, Any]) -> OwnerValueBatchV1:
    return OwnerValueBatchV1.model_validate(payload)


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _all_keys(value: Any) -> set[str]:
    if isinstance(value, Mapping):
        keys = set(value)
        for child in value.values():
            keys.update(_all_keys(child))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys.update(_all_keys(child))
        return keys
    return set()
