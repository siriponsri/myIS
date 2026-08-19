"""Typed, versioned ArmIndex contracts for A0 scaffolding.

These models describe aggregate-safe public artifacts and synthetic fixture
data only. They do not authorize measured execution or protected-data access.
"""

from __future__ import annotations

import re
from typing import Any, ClassVar, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ...kernel.canonical import canonical_sha256


Sha256 = str
ArmId = Literal["ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05"]
CommercialStatus = Literal["commercial_capable", "research_non_commercial", "mixed", "not_applicable"]
EvidenceClass = Literal["synthetic_fixture", "engineering", "aggregate_evidence", "contract_only"]

_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
_COMMIT_RE = re.compile(r"^[a-f0-9]{40,64}$")
_PERSONAL_PATH_RE = re.compile(r"(?:[A-Za-z]:\\Users\\|/Users/|/home/)", re.IGNORECASE)
_FORBIDDEN_KEYS = frozenset(
    {
        "credentials",
        "dataset_membership",
        "final_query_ids",
        "membership",
        "memberships",
        "per_query_outcome",
        "per_query_outcomes",
        "qrel",
        "qrels",
        "raw_provider_payload",
        "raw_provider_payloads",
        "secret",
        "secrets",
        "selection_feedback",
    }
)
_ZERO_SHA256 = "0" * 64


def _safe_scan(value: Any, *, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for raw_key, item in value.items():
            key = str(raw_key)
            normalized = key.casefold().replace("-", "_").replace(" ", "_")
            if normalized in _FORBIDDEN_KEYS:
                raise ValueError(f"protected payload key is forbidden at {path}.{key}")
            _safe_scan(item, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _safe_scan(item, path=f"{path}[{index}]")
    elif isinstance(value, str) and _PERSONAL_PATH_RE.search(value):
        raise ValueError(f"personal absolute path is forbidden at {path}")


class ArmIndexContract(BaseModel):
    """Frozen contract envelope with a canonical self-hash."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{1,127}$")
    evidence_class: EvidenceClass
    scientific_authority: bool
    commercial_status: CommercialStatus
    protected_data_accessed: Literal[False]
    contract_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="before")
    @classmethod
    def _supply_hash_sentinel(cls, value: Any) -> Any:
        if isinstance(value, Mapping) and "contract_sha256" not in value:
            return {**value, "contract_sha256": _ZERO_SHA256}
        return value

    @model_validator(mode="after")
    def _validate_safety_and_hash(self) -> "ArmIndexContract":
        if self.evidence_class != "aggregate_evidence" and self.scientific_authority:
            raise ValueError("fixture, engineering, and contract-only objects cannot claim scientific authority")
        unsigned = self.model_dump(mode="json", exclude={"contract_sha256"})
        _safe_scan(unsigned)
        digest = canonical_sha256(unsigned)
        if self.contract_sha256 not in {_ZERO_SHA256, digest}:
            raise ValueError("contract_sha256 does not match canonical contract bytes")
        object.__setattr__(self, "contract_sha256", digest)
        return self


class SourceSpan(ArmIndexContract):
    schema_version: Literal["myis.armindex-source-span.v1"]
    source_id: str = Field(min_length=1)
    field_name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    start_offset: int = Field(ge=0)
    end_offset: int = Field(gt=0)
    source_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def _ordered_offsets(self) -> "SourceSpan":
        if self.end_offset <= self.start_offset:
            raise ValueError("source span end must be greater than start")
        return self


class FamilyDocument(ArmIndexContract):
    schema_version: Literal["myis.armindex-family-document.v1"]
    family_id: str = Field(min_length=1)
    publication_id: str = Field(min_length=1)
    fields: Mapping[str, str] = Field(min_length=1)
    source_spans: tuple[SourceSpan, ...] = Field(min_length=1)
    document_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")

    @field_validator("fields")
    @classmethod
    def _valid_document_fields(cls, value: Mapping[str, str]) -> dict[str, str]:
        normalized = dict(value)
        if any(not re.fullmatch(r"[a-z][a-z0-9_]*", key) or not text.strip() for key, text in normalized.items()):
            raise ValueError("document fields require stable names and non-empty text")
        return normalized


class QueryFamily(ArmIndexContract):
    schema_version: Literal["myis.armindex-query-family.v1"]
    query_id: str = Field(min_length=1)
    family_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    data_role: Literal["synthetic_fixture"]
    query_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")


class SearchableUnit(ArmIndexContract):
    schema_version: Literal["myis.armindex-searchable-unit.v1"]
    unit_id: str = Field(min_length=1)
    family_id: str = Field(min_length=1)
    publication_id: str = Field(min_length=1)
    representation_program_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    source_spans: tuple[SourceSpan, ...] = Field(min_length=1)
    content_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")


class RepresentationProgram(ArmIndexContract):
    schema_version: Literal["myis.armindex-representation-program.v2"]
    program_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]+$")
    source_fields: tuple[str, ...] = Field(min_length=1)
    field_order: tuple[str, ...] = Field(min_length=1)
    field_labels: Mapping[str, str]
    unit_kind: Literal["document", "section", "claim", "passage"]
    passage_size: int | None = Field(default=None, ge=1)
    passage_overlap: int = Field(default=0, ge=0)
    normalization: Literal["unicode_nfkc_whitespace", "unicode_nfkc_whitespace_lower"]
    duplicate_policy: Literal["family_content_hash_first", "preserve_all"]
    family_aggregation: Literal["maxp", "top_m", "single_unit"]
    family_top_m: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _program_semantics(self) -> "RepresentationProgram":
        if len(set(self.source_fields)) != len(self.source_fields) or set(self.source_fields) != set(self.field_order):
            raise ValueError("field_order must contain every unique source field exactly once")
        if set(self.field_labels) - set(self.source_fields):
            raise ValueError("field_labels may reference declared source fields only")
        if self.unit_kind == "passage" and self.passage_size is None:
            raise ValueError("passage unitization requires passage_size")
        if self.passage_size is not None and self.passage_overlap >= self.passage_size:
            raise ValueError("passage overlap must be smaller than passage size")
        if (self.family_aggregation == "top_m") != (self.family_top_m is not None):
            raise ValueError("family_top_m is required only for top_m aggregation")
        return self


class CompiledRepresentation(ArmIndexContract):
    schema_version: Literal["myis.armindex-compiled-representation.v1"]
    compiled_id: str = Field(min_length=1)
    program_id: str = Field(min_length=1)
    logical_program_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    arm_id: ArmId
    adapter_lock_sha256: Sha256 | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    units: tuple[SearchableUnit, ...]
    unit_count: int = Field(ge=0)
    estimated_storage_bytes: int = Field(ge=0)
    truncation_count: int = Field(ge=0)
    omitted_span_count: int = Field(ge=0)
    compiled_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def _compiled_counts(self) -> "CompiledRepresentation":
        if self.unit_count != len(self.units):
            raise ValueError("unit_count must match units")
        if any(unit.representation_program_id != self.program_id for unit in self.units):
            raise ValueError("compiled units must bind the representation program")
        return self


class ArmCapabilities(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    method: Literal["lexical", "dense", "sparse", "multivector"]
    maximum_input_length: int = Field(ge=1)
    embedding_dimension: int | None = Field(default=None, ge=1)
    multilingual: bool
    cpu_supported: bool
    gpu_supported: bool
    batch_supported: bool
    index_type: str = Field(min_length=1)


class ArmSpecification(ArmIndexContract):
    schema_version: Literal["myis.armindex-arm-specification.v1"]
    arm_id: ArmId
    model_id: str = Field(min_length=1)
    role: str = Field(min_length=1)
    license_id: str = Field(min_length=1)
    capabilities: ArmCapabilities
    adapter_status: Literal["fixture_ready", "metadata_declared", "revision_unresolved", "model_not_downloaded"]
    measured_use_allowed: Literal[False]


class ArmAdapterLock(ArmIndexContract):
    schema_version: Literal["myis.armindex-arm-adapter-lock.v1"]
    arm_id: ArmId
    model_id: str = Field(min_length=1)
    resolved_model_sha: str = Field(pattern=r"^[a-f0-9]{40,64}$")
    tokenizer_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    adapter_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    input_format: Mapping[str, str]
    pooling: str = Field(min_length=1)
    normalization: str = Field(min_length=1)
    dimension: int = Field(ge=1)
    maximum_input_length: int = Field(ge=1)
    precision: Literal["lexical", "fp32", "bf16", "fp16"]
    similarity: str = Field(min_length=1)
    network_required: Literal[False]


class IndexManifest(ArmIndexContract):
    schema_version: Literal["myis.armindex-index-manifest.v1"]
    index_id: str = Field(min_length=1)
    arm_id: ArmId
    compiled_representation_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    adapter_lock_sha256: Sha256 | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    index_type: str = Field(min_length=1)
    unit_count: int = Field(ge=0)
    index_size_bytes: int = Field(ge=0)
    artifact_uri: str = Field(min_length=1)
    index_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")


class SearchRequest(ArmIndexContract):
    schema_version: Literal["myis.armindex-search-request.v1"]
    request_id: str = Field(min_length=1)
    arm_id: ArmId
    index_manifest_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    query: QueryFamily
    depth: int = Field(ge=1, le=2000)


class SearchHit(ArmIndexContract):
    schema_version: Literal["myis.armindex-search-hit.v1"]
    request_id: str = Field(min_length=1)
    arm_id: ArmId
    unit_id: str = Field(min_length=1)
    family_id: str = Field(min_length=1)
    publication_id: str = Field(min_length=1)
    rank: int = Field(ge=1)
    score: float


class FamilyRankEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    family_id: str = Field(min_length=1)
    rank: int = Field(ge=1)
    score: float
    supporting_unit_ids: tuple[str, ...] = Field(min_length=1)


class FamilyRanking(ArmIndexContract):
    schema_version: Literal["myis.armindex-family-ranking.v1"]
    ranking_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    arm_ids: tuple[ArmId, ...] = Field(min_length=1)
    entries: tuple[FamilyRankEntry, ...]
    depth: int = Field(ge=1)
    ranking_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def _ranking_order(self) -> "FamilyRanking":
        if tuple(entry.rank for entry in self.entries) != tuple(range(1, len(self.entries) + 1)):
            raise ValueError("family ranking ranks must be contiguous")
        if len({entry.family_id for entry in self.entries}) != len(self.entries):
            raise ValueError("family ranking cannot repeat a family")
        return self


class CandidatePool(ArmIndexContract):
    schema_version: Literal["myis.armindex-candidate-pool.v1"]
    pool_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    arm_ids: tuple[ArmId, ...] = Field(min_length=1)
    depth_by_arm: Mapping[str, int] = Field(min_length=1)
    hits: tuple[SearchHit, ...]
    pool_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def _candidate_pool_bindings(self) -> "CandidatePool":
        if set(self.depth_by_arm) != set(self.arm_ids):
            raise ValueError("depth_by_arm must bind each candidate-pool arm")
        if any(hit.request_id != self.request_id or hit.arm_id not in self.arm_ids for hit in self.hits):
            raise ValueError("candidate-pool hits must bind the request and declared arms")
        return self


class FusionConfiguration(ArmIndexContract):
    schema_version: Literal["myis.armindex-fusion-configuration.v1"]
    fusion_id: str = Field(min_length=1)
    method: Literal["identity", "rrf", "weighted_rrf", "normalized_rank_sum", "lexicographic_union"]
    arm_ids: tuple[ArmId, ...] = Field(min_length=1)
    parameters: Mapping[str, float]


class TransferEvaluation(ArmIndexContract):
    schema_version: Literal["myis.armindex-transfer-evaluation.v1"]
    transfer_id: str = Field(min_length=1)
    source_program_id: str = Field(min_length=1)
    source_arm_id: ArmId
    target_arm_id: ArmId
    transfer_state: Literal["exact_logical_transfer", "adapter_constrained", "unsupported"]
    compiled_representation_sha256: Sha256 | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    unsupported_reason: str | None = None
    metric_sha256s: tuple[Sha256, ...]

    @model_validator(mode="after")
    def _transfer_result(self) -> "TransferEvaluation":
        unsupported = self.transfer_state == "unsupported"
        if unsupported != (self.unsupported_reason is not None):
            raise ValueError("unsupported transfer requires exactly one unsupported reason")
        if unsupported and self.compiled_representation_sha256 is not None:
            raise ValueError("unsupported transfer cannot bind a compiled representation")
        return self


class ComplementarityReport(ArmIndexContract):
    schema_version: Literal["myis.armindex-complementarity-report.v1"]
    report_id: str = Field(min_length=1)
    arm_ids: tuple[ArmId, ...] = Field(min_length=2)
    candidate_depth: int = Field(ge=1)
    pairwise_overlap: Mapping[str, float]
    rank_overlap: Mapping[str, float]
    unique_hit_counts: Mapping[str, int]
    aggregate_metric_sha256s: tuple[Sha256, ...]
    gate_status: Literal["eligible", "ineligible", "not_evaluated"]


class AutoIndexCandidate(ArmIndexContract):
    schema_version: Literal["myis.armindex-autoindex-candidate.v1"]
    candidate_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]+$")
    arm_id: ArmId
    parent_candidate_id: str | None = None
    hypothesis_id: str = Field(min_length=1)
    hypothesis: str = Field(min_length=1)
    role: Literal["exploit", "matched_ablation", "orthogonal", "diversity"]
    declared_axis: str = Field(min_length=1)
    representation_program_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    scientific_payload_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    axis_values: Mapping[str, Any] = Field(min_length=1)


class AutoIndexBatch(ArmIndexContract):
    schema_version: Literal["myis.armindex-autoindex-batch.v1"]
    batch_id: str = Field(min_length=1)
    arm_id: ArmId
    iteration: int = Field(ge=1)
    incumbent_candidate_id: str = Field(min_length=1)
    status: Literal["frozen_before_evaluation"]
    candidates: tuple[AutoIndexCandidate, ...] = Field(min_length=4, max_length=4)
    budget_counters: Mapping[str, int]

    @model_validator(mode="after")
    def _complete_unique_batch(self) -> "AutoIndexBatch":
        roles = tuple(candidate.role for candidate in self.candidates)
        if roles != ("exploit", "matched_ablation", "orthogonal", "diversity"):
            raise ValueError("AutoIndex batch roles and order are invalid")
        if any(candidate.arm_id != self.arm_id for candidate in self.candidates):
            raise ValueError("AutoIndex candidates must bind the batch arm")
        if len({candidate.candidate_id for candidate in self.candidates}) != 4:
            raise ValueError("AutoIndex candidate IDs must be unique")
        if len({candidate.scientific_payload_sha256 for candidate in self.candidates}) != 4:
            raise ValueError("AutoIndex scientific payloads must be unique")
        if any(value < 0 for value in self.budget_counters.values()):
            raise ValueError("AutoIndex budget counters must be non-negative")
        return self


class HarnessConfiguration(ArmIndexContract):
    schema_version: Literal["myis.armindex-harness-configuration.v2"]
    harness_id: str = Field(min_length=1)
    arm_ids: tuple[ArmId, ...] = Field(min_length=1, max_length=5)
    invocation_order: tuple[ArmId, ...] = Field(min_length=1, max_length=5)
    execution: Literal["parallel", "sequential"]
    initial_depth_by_arm: Mapping[str, int] = Field(min_length=1)
    maximum_depth_by_arm: Mapping[str, int] = Field(min_length=1)
    fusion_configuration_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    early_stop: Mapping[str, Any]
    cache_policy: Literal["disabled", "read_only", "bounded"]
    latency_profile: Literal["FAST", "BALANCED", "DEEP"]
    runtime_features: tuple[Literal["query_length", "token_count", "script", "language_hint", "system_load", "cache_state"], ...]

    @model_validator(mode="after")
    def _harness_bindings(self) -> "HarnessConfiguration":
        if len(set(self.arm_ids)) != len(self.arm_ids) or set(self.invocation_order) != set(self.arm_ids):
            raise ValueError("invocation_order must be a permutation of unique arm_ids")
        if set(self.initial_depth_by_arm) != set(self.arm_ids) or set(self.maximum_depth_by_arm) != set(self.arm_ids):
            raise ValueError("harness depth maps must bind every arm")
        for arm_id in self.arm_ids:
            initial = self.initial_depth_by_arm[arm_id]
            maximum = self.maximum_depth_by_arm[arm_id]
            if initial < 1 or maximum < initial or maximum > 2000:
                raise ValueError("harness depths must satisfy 1 <= initial <= maximum <= 2000")
        return self


class HarnessAction(ArmIndexContract):
    schema_version: Literal["myis.armindex-harness-action.v1"]
    action_id: str = Field(min_length=1)
    harness_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    sequence: int = Field(ge=1)
    arm_id: ArmId
    action: Literal["search", "escalate", "stop", "fallback", "abstain"]
    depth: int = Field(ge=0, le=2000)
    reason: str = Field(min_length=1)
    previous_action_sha256: Sha256 | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class ProductionProfile(ArmIndexContract):
    schema_version: Literal["myis.armindex-production-profile.v1"]
    profile_id: Literal["FAST", "BALANCED", "DEEP"]
    harness_configuration_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    arm_ids: tuple[ArmId, ...] = Field(min_length=1, max_length=5)
    mode: Literal["synchronous", "asynchronous"]
    maximum_candidate_depth: int = Field(ge=1, le=2000)
    commercial_only: bool
    readiness: Literal["contract_only"]

    @model_validator(mode="after")
    def _profile_constraints(self) -> "ProductionProfile":
        if self.profile_id == "FAST" and (self.mode != "synchronous" or "ARM-01" not in self.arm_ids or len(self.arm_ids) > 2):
            raise ValueError("FAST must be synchronous with ARM-01 and at most two arms")
        if self.profile_id == "BALANCED" and (self.mode != "synchronous" or not self.commercial_only):
            raise ValueError("BALANCED must remain synchronous and commercial-only until validated")
        return self


class EvaluationRequest(ArmIndexContract):
    schema_version: Literal["myis.armindex-evaluation-request.v1"]
    request_id: str = Field(min_length=1)
    ranking_sha256s: tuple[Sha256, ...] = Field(min_length=1)
    metric_names: tuple[Literal["recall_at_100", "ndcg_at_100", "ndcg_at_10"], ...] = Field(min_length=1)
    synthetic_relevance: Mapping[str, tuple[str, ...]] = Field(min_length=1)
    data_role: Literal["synthetic_fixture"]
    evaluator_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")


class AggregateMetric(ArmIndexContract):
    schema_version: Literal["myis.armindex-aggregate-metric.v1"]
    metric_id: str = Field(min_length=1)
    name: Literal["recall_at_100", "ndcg_at_100", "ndcg_at_10"]
    value: float = Field(ge=0, le=1)
    sample_count: int = Field(ge=1)
    scope: Literal["ALL", "IN", "OUT", "SYNTHETIC"]
    direction: Literal["maximize"]
    denominator: str = Field(min_length=1)
    evidence_role: Literal["primary", "secondary", "fixture_only"]


class RunManifest(ArmIndexContract):
    schema_version: Literal["myis.armindex-run-manifest.v1"]
    run_id: str = Field(min_length=1)
    campaign_id: Literal["armindex-multiretriever-v2"]
    phase_id: str = Field(pattern=r"^A[0-7]_[A-Z0-9_]+$")
    task_id: str = Field(pattern=r"^A[0-7]\.[0-9]+$")
    stage: Literal["fixture"]
    status: Literal["valid", "invalid", "blocked"]
    git_commit: str = Field(pattern=r"^[a-f0-9]{40,64}$")
    git_tree: str = Field(pattern=r"^[a-f0-9]{40,64}$")
    input_hashes: Mapping[str, Sha256] = Field(min_length=1)
    method_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    resources_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    artifact_sha256s: tuple[Sha256, ...]
    measured_execution: Literal[False]
    selection_accesses: Literal[0]
    final_accesses: Literal[0]


class AggregateReceipt(ArmIndexContract):
    schema_version: Literal["myis.armindex-aggregate-receipt.v1"]
    receipt_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    run_manifest_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    status: Literal["passed", "failed", "blocked"]
    aggregate_metric_sha256s: tuple[Sha256, ...]
    aggregate_counts: Mapping[str, int]
    cost_receipt_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    measured_execution: Literal[False]
    selection_accesses: Literal[0]
    final_accesses: Literal[0]

    @field_validator("aggregate_counts")
    @classmethod
    def _nonnegative_counts(cls, value: Mapping[str, int]) -> dict[str, int]:
        normalized = dict(value)
        if any(count < 0 for count in normalized.values()):
            raise ValueError("aggregate counts must be non-negative")
        return normalized


class CostReceipt(ArmIndexContract):
    schema_version: Literal["myis.armindex-cost-receipt.v1"]
    receipt_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    arm_ids: tuple[ArmId, ...] = Field(min_length=1)
    sample_count: int = Field(ge=1)
    latency_p50_ms: float = Field(ge=0)
    latency_p95_ms: float = Field(ge=0)
    latency_p99_ms: float = Field(ge=0)
    throughput_qps: float = Field(ge=0)
    cost_per_query_usd: float = Field(ge=0)
    charged_usd: float = Field(ge=0)
    index_size_bytes: int = Field(ge=0)
    ram_bytes: int = Field(ge=0)
    vram_bytes: int = Field(ge=0)
    run_manifest_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def _latency_order(self) -> "CostReceipt":
        if not self.latency_p50_ms <= self.latency_p95_ms <= self.latency_p99_ms:
            raise ValueError("latency percentiles must be monotonic")
        return self


class PhaseCloseoutEvent(ArmIndexContract):
    schema_version: Literal["myis.armindex-phase-closeout-event.v1"]
    event_id: str = Field(min_length=1)
    phase_id: str = Field(pattern=r"^A[0-7]_[A-Z0-9_]+$")
    task_id: str = Field(pattern=r"^A[0-7]\.[0-9]+$")
    aggregate_receipt_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    status: Literal["completed", "blocked"]
    next_authorized_action: str = Field(min_length=1)


class BrainProjectionEvent(ArmIndexContract):
    schema_version: Literal["myis.armindex-brain-projection-event.v1"]
    event_id: str = Field(min_length=1)
    source_receipt_uri: str = Field(min_length=1)
    source_receipt_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    memory_kind: Literal["decision", "evidence", "lesson", "failed_attempt", "active_context"]
    status: Literal["pending", "projected", "failed"]


class MLflowMirrorEvent(ArmIndexContract):
    schema_version: Literal["myis.armindex-mlflow-mirror-event.v1"]
    event_id: str = Field(min_length=1)
    source_receipt_uri: str = Field(min_length=1)
    source_receipt_sha256: Sha256 = Field(pattern=r"^[a-f0-9]{64}$")
    experiment_name: Literal["myis-armindex-multiretriever-v2", "myis-system"]
    allowlisted_tags: Mapping[str, str]
    status: Literal["pending", "mirrored", "failed"]


CONTRACT_MODELS: tuple[type[ArmIndexContract], ...] = (
    FamilyDocument,
    QueryFamily,
    SearchableUnit,
    SourceSpan,
    RepresentationProgram,
    CompiledRepresentation,
    ArmSpecification,
    ArmAdapterLock,
    IndexManifest,
    SearchRequest,
    SearchHit,
    FamilyRanking,
    CandidatePool,
    FusionConfiguration,
    TransferEvaluation,
    ComplementarityReport,
    AutoIndexCandidate,
    AutoIndexBatch,
    HarnessConfiguration,
    HarnessAction,
    ProductionProfile,
    EvaluationRequest,
    AggregateMetric,
    RunManifest,
    AggregateReceipt,
    CostReceipt,
    PhaseCloseoutEvent,
    BrainProjectionEvent,
    MLflowMirrorEvent,
)

CONTRACT_MODEL_BY_SCHEMA: dict[str, type[ArmIndexContract]] = {
    model.model_fields["schema_version"].annotation.__args__[0]: model for model in CONTRACT_MODELS
}


def parse_contract(value: Mapping[str, Any]) -> ArmIndexContract:
    """Parse one of the 29 active A0.10 contract types by schema version."""

    schema_version = str(value.get("schema_version", ""))
    model = CONTRACT_MODEL_BY_SCHEMA.get(schema_version)
    if model is None:
        raise ValueError(f"unsupported ArmIndex contract schema: {schema_version!r}")
    return model.model_validate(value)


__all__: ClassVar[tuple[str, ...]] = tuple(model.__name__ for model in CONTRACT_MODELS) + (
    "ArmCapabilities",
    "ArmIndexContract",
    "CONTRACT_MODELS",
    "CONTRACT_MODEL_BY_SCHEMA",
    "parse_contract",
)
