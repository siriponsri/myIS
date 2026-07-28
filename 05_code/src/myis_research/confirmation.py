"""Hash-only confirmation requests and aggregate-only response validation.

This module deliberately contains no evaluator and no protected-data loader.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .harness.benchmark import ConfirmationClassification, classify_confirmation
from .harness.manifest import atomic_write_once
from .harness.metrics import canonical_metric
from .harness.models import canonical_hash, is_sha256
from .identity import PROGRAM_ID, PROTOCOL_FAMILY_ID, RESEARCH_VERSION
from .protection import assert_aggregate_only, assert_hash_only_mapping


REQUEST_SCHEMA = "myis.confirmation-request.v1"
AGGREGATE_SCHEMA = "myis.confirmation-aggregate.v1"


@dataclass(frozen=True)
class ConfirmationRequest:
    request_id: str
    created_at_utc: str
    git_commit: str
    submission_hashes: dict[str, str]
    config_hashes: dict[str, str]
    protocol_hashes: dict[str, str]
    program_id: str = PROGRAM_ID
    research_version: str = RESEARCH_VERSION
    protocol_family_id: str = PROTOCOL_FAMILY_ID
    schema_version: str = REQUEST_SCHEMA

    def validate(self) -> None:
        if self.schema_version != REQUEST_SCHEMA:
            raise ValueError("unsupported confirmation request schema")
        if (
            self.program_id != PROGRAM_ID
            or self.research_version != RESEARCH_VERSION
            or self.protocol_family_id != PROTOCOL_FAMILY_ID
        ):
            raise ValueError("confirmation request is not bound to IS1 Research V0.1")
        if not self.request_id.strip() or not self.created_at_utc.strip():
            raise ValueError("request_id and created_at_utc are required")
        if len(self.git_commit) not in {40, 64}:
            raise ValueError("git_commit must be a full 40- or 64-hex commit identity")
        try:
            int(self.git_commit, 16)
        except ValueError as error:
            raise ValueError("git_commit must be a full 40- or 64-hex commit identity") from error
        assert_hash_only_mapping(self.submission_hashes, name="submission_hashes")
        assert_hash_only_mapping(self.config_hashes, name="config_hashes")
        assert_hash_only_mapping(self.protocol_hashes, name="protocol_hashes")
        assert_aggregate_only(self.as_dict())

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def sha256(self) -> str:
        self.validate()
        return canonical_hash(self.as_dict())


def write_confirmation_request(path: Path, request: ConfirmationRequest) -> str:
    request.validate()
    return atomic_write_once(path, request.as_dict())


def load_confirmation_request(payload: Mapping[str, Any]) -> ConfirmationRequest:
    expected = set(ConfirmationRequest.__dataclass_fields__)
    if set(payload) != expected:
        raise ValueError("confirmation request fields do not match the schema")
    request = ConfirmationRequest(
        request_id=payload["request_id"],
        created_at_utc=payload["created_at_utc"],
        git_commit=payload["git_commit"],
        submission_hashes=dict(payload["submission_hashes"]),
        config_hashes=dict(payload["config_hashes"]),
        protocol_hashes=dict(payload["protocol_hashes"]),
        program_id=payload["program_id"],
        research_version=payload["research_version"],
        protocol_family_id=payload["protocol_family_id"],
        schema_version=payload["schema_version"],
    )
    request.validate()
    return request


@dataclass(frozen=True)
class ComparisonFamilyMetadata:
    family_id: str
    role: str
    correction: str
    family_size: int

    def validate(self) -> None:
        if not self.family_id.strip() or self.role not in {"primary", "additional"}:
            raise ValueError("comparison family requires an ID and primary/additional role")
        expected = "none" if self.role == "primary" else "holm"
        if self.correction != expected:
            raise ValueError(f"{self.role} comparison family requires correction={expected}")
        if self.family_size <= 0:
            raise ValueError("comparison family_size must be positive")


@dataclass(frozen=True)
class AggregateComparison:
    gate_id: str
    primary_metric: str
    baseline_id: str
    candidate_id: str
    n: int
    baseline_point_estimate: float
    candidate_point_estimate: float
    paired_delta: float
    ci95_lower: float
    ci95_upper: float
    effect_size_name: str
    effect_size_value: float
    wins: int
    losses: int
    ties: int
    classification: ConfirmationClassification
    comparison_family: ComparisonFamilyMetadata

    def validate(self) -> None:
        expected_metric = {"C": "out_recall_at_100", "R": "out_ndcg_at_100"}.get(self.gate_id)
        if self.gate_id not in {"C", "R", "S"}:
            raise ValueError("gate_id must be C, R, or S")
        if expected_metric and self.primary_metric != expected_metric:
            raise ValueError(f"Gate {self.gate_id} primary metric must be {expected_metric}")
        if not self.baseline_id.strip() or not self.candidate_id.strip() or not self.primary_metric.strip():
            raise ValueError("comparison identities and primary metric are required")
        if self.n <= 0 or min(self.wins, self.losses, self.ties) < 0:
            raise ValueError("aggregate comparison counts must be valid")
        if self.wins + self.losses + self.ties != self.n:
            raise ValueError("wins + losses + ties must equal n")
        numeric = (
            self.baseline_point_estimate,
            self.candidate_point_estimate,
            self.paired_delta,
            self.ci95_lower,
            self.ci95_upper,
            self.effect_size_value,
        )
        if any(not math.isfinite(value) for value in numeric):
            raise ValueError("confirmation aggregate values must be finite")
        expected_delta = canonical_metric(self.candidate_point_estimate) - canonical_metric(
            self.baseline_point_estimate
        )
        if canonical_metric(self.paired_delta) != canonical_metric(expected_delta):
            raise ValueError("paired_delta disagrees with point estimates")
        if canonical_metric(self.ci95_lower) > canonical_metric(self.ci95_upper):
            raise ValueError("CI lower cannot exceed CI upper")
        if self.effect_size_name != "rank_biserial":
            raise ValueError("effect size must be rank_biserial")
        expected_classification = classify_confirmation(self.paired_delta, self.ci95_lower)
        if self.classification != expected_classification:
            raise ValueError("confirmation classification disagrees with delta/CI")
        self.comparison_family.validate()

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AggregateComparison":
        expected = {
            "gate_id", "primary_metric", "baseline_id", "candidate_id", "n",
            "baseline_point_estimate", "candidate_point_estimate", "paired_delta",
            "ci95_lower", "ci95_upper", "effect_size_name", "effect_size_value",
            "wins", "losses", "ties", "classification", "comparison_family",
        }
        if set(value) != expected:
            raise ValueError("aggregate comparison fields do not match the schema")
        family_fields = {"family_id", "role", "correction", "family_size"}
        if set(value["comparison_family"]) != family_fields:
            raise ValueError("comparison-family fields do not match the schema")
        family = ComparisonFamilyMetadata(**value["comparison_family"])
        return cls(
            gate_id=value["gate_id"],
            primary_metric=value["primary_metric"],
            baseline_id=value["baseline_id"],
            candidate_id=value["candidate_id"],
            n=int(value["n"]),
            baseline_point_estimate=float(value["baseline_point_estimate"]),
            candidate_point_estimate=float(value["candidate_point_estimate"]),
            paired_delta=float(value["paired_delta"]),
            ci95_lower=float(value["ci95_lower"]),
            ci95_upper=float(value["ci95_upper"]),
            effect_size_name=value["effect_size_name"],
            effect_size_value=float(value["effect_size_value"]),
            wins=int(value["wins"]),
            losses=int(value["losses"]),
            ties=int(value["ties"]),
            classification=ConfirmationClassification(value["classification"]),
            comparison_family=family,
        )


@dataclass(frozen=True)
class ConfirmationAggregatePackage:
    package_id: str
    created_at_utc: str
    request_sha256: str
    input_hashes: dict[str, str]
    output_hashes: dict[str, str]
    comparisons: tuple[AggregateComparison, ...]
    schema_version: str = AGGREGATE_SCHEMA

    def validate(self, *, expected_request_sha256: str | None = None) -> None:
        if self.schema_version != AGGREGATE_SCHEMA:
            raise ValueError("unsupported confirmation aggregate schema")
        if not self.package_id.strip() or not self.created_at_utc.strip():
            raise ValueError("package_id and created_at_utc are required")
        if not is_sha256(self.request_sha256):
            raise ValueError("request_sha256 must be SHA-256")
        if expected_request_sha256 and self.request_sha256 != expected_request_sha256:
            raise ValueError("confirmation package request hash mismatch")
        assert_hash_only_mapping(self.input_hashes, name="input_hashes")
        assert_hash_only_mapping(self.output_hashes, name="output_hashes")
        if not self.comparisons:
            raise ValueError("confirmation aggregate requires at least one comparison")
        for comparison in self.comparisons:
            comparison.validate()
        assert_aggregate_only(self.as_dict())

    def as_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(asdict(self), ensure_ascii=False))

    @property
    def sha256(self) -> str:
        self.validate()
        return canonical_hash(self.as_dict())


def validate_confirmation_aggregate(
    payload: Mapping[str, Any], *, expected_request_sha256: str | None = None
) -> ConfirmationAggregatePackage:
    assert_aggregate_only(payload)
    expected = {
        "package_id", "created_at_utc", "request_sha256", "input_hashes",
        "output_hashes", "comparisons", "schema_version",
    }
    if set(payload) != expected:
        raise ValueError("confirmation aggregate fields do not match the schema")
    package = ConfirmationAggregatePackage(
        package_id=payload["package_id"],
        created_at_utc=payload["created_at_utc"],
        request_sha256=payload["request_sha256"],
        input_hashes=dict(payload["input_hashes"]),
        output_hashes=dict(payload["output_hashes"]),
        comparisons=tuple(AggregateComparison.from_dict(value) for value in payload["comparisons"]),
        schema_version=payload.get("schema_version", AGGREGATE_SCHEMA),
    )
    package.validate(expected_request_sha256=expected_request_sha256)
    return package
