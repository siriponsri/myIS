"""Typed, non-executable contracts for the Track S matched-arm protocol."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping

from .models import is_sha256


FULL_SKILLOPT_TAG_OBJECT = "51d0a4d96e88558c84dee637f98e24e3fb2d1547"
FULL_SKILLOPT_COMMIT = "e4ea6a6771e797ef820cdd8bfea64c57e0481065"
FULL_SKILLOPT_TREE = "5a603e937a20f1078059f94039a50028c022487a"
FULL_SKILLOPT_PARENT = "5487e2c426db8b75a0e8e2714641542325d55f9e"
LITE_SKILLOPT_COMMIT = "4cb4eeef1f95375a9179737ab94cf5e64b9647c6"
LITE_SKILLOPT_TREE = "6e2cf3d17f251312412f4393cd60254dfd046a4a"
LITE_SKILLOPT_PARENTS = (
    "32708a1349105b59183afb1b417385aa4e8812e0",
    "636791a4b5f949c10b4540512fd67f149a98eecc",
)
TRACK_S_SEEDS = (11, 23, 47)
MAX_TYPED_OVERLAY_VALUES = 12

_ROUTE_QUOTA_FIELDS = frozenset(
    {
        "tac_bm25_quota",
        "tac_dense_quota",
        "claim_bm25_quota",
        "claim_dense_quota",
        "mechanism_bm25_quota",
        "mechanism_dense_quota",
    }
)
_OVERLAY_VALUE_FIELDS = _ROUTE_QUOTA_FIELDS | {"fusion_profile", "rrf_k", "pool_depth", "rerank_depth"}
_FUSION_PROFILES = frozenset({"inherit_c1", "rrf", "weighted_rrf", "max", "minmax_weighted"})
_C1_INVARIANT_FIELDS = frozenset(
    {
        "query_views",
        "prompt",
        "encoder",
        "reranker_instructions",
        "corpus",
        "evaluator",
        "split",
        "qrels",
        "family_map",
        "provider",
        "budget",
        "executable_code",
        "dynamic_policy",
    }
)


@dataclass(frozen=True)
class EngineProvenance:
    """Bind each arm to an exact optimizer engine without importing it."""

    arm: str
    engine_name: str
    source_reference: str
    executable_commit: str
    tree: str
    parents: tuple[str, ...]
    release_tag_object: str | None = None

    def validate(self) -> None:
        if self.arm not in {"A2", "A2L", "A3"}:
            raise ValueError("engine provenance is only defined for A2, A2L, and A3")
        if self.arm in {"A2", "A3"}:
            expected = (
                "skillopt-full",
                FULL_SKILLOPT_TAG_OBJECT,
                FULL_SKILLOPT_COMMIT,
                FULL_SKILLOPT_TREE,
                (FULL_SKILLOPT_PARENT,),
                FULL_SKILLOPT_TAG_OBJECT,
            )
        else:
            expected = (
                "skillopt-lite",
                LITE_SKILLOPT_COMMIT,
                LITE_SKILLOPT_COMMIT,
                LITE_SKILLOPT_TREE,
                LITE_SKILLOPT_PARENTS,
                None,
            )
        observed = (
            self.engine_name,
            self.source_reference,
            self.executable_commit,
            self.tree,
            self.parents,
            self.release_tag_object,
        )
        if observed != expected:
            raise ValueError("Track S engine provenance does not match the locked upstream identity")

    @property
    def execution_identity(self) -> tuple[str, str, str, tuple[str, ...], str | None]:
        return (self.engine_name, self.executable_commit, self.tree, self.parents, self.release_tag_object)


@dataclass(frozen=True)
class C1TypedOverlay:
    """A bounded data overlay over the frozen C1 harness, never executable policy."""

    c1_harness_sha256: str
    c1_policy_sha256: str
    values: Mapping[str, bool | int | float | str]

    def validate(self) -> None:
        if not is_sha256(self.c1_harness_sha256) or not is_sha256(self.c1_policy_sha256):
            raise ValueError("C1 overlay must bind frozen harness and policy SHA-256 values")
        if not self.values or len(self.values) > MAX_TYPED_OVERLAY_VALUES:
            raise ValueError(f"typed overlay must contain 1-{MAX_TYPED_OVERLAY_VALUES} values")
        unknown = set(self.values) - _OVERLAY_VALUE_FIELDS
        protected = set(self.values) & _C1_INVARIANT_FIELDS
        if unknown or protected:
            raise ValueError("typed overlay attempted an unknown or protected C1 field")
        groups = {_overlay_group(field) for field in self.values}
        if len(groups) > 2:
            raise ValueError("one A3 candidate may change no more than two typed field groups")
        for field, value in self.values.items():
            if field in _ROUTE_QUOTA_FIELDS:
                if type(value) is not int or not 0 <= value <= 400:
                    raise ValueError(f"typed route quota for {field} must be an integer from 0 through 400")
            elif field == "fusion_profile":
                if value not in _FUSION_PROFILES:
                    raise ValueError("typed fusion profile is not allowlisted")
            elif type(value) is not int or not 1 <= value <= 400:
                raise ValueError(f"typed overlay value for {field} must be an integer from 1 through 400")
        quotas = [value for field, value in self.values.items() if field in _ROUTE_QUOTA_FIELDS]
        if quotas and sum(quotas) > 400:
            raise ValueError("typed route quotas exceed the frozen raw candidate budget of 400")
        if "pool_depth" in self.values and "rerank_depth" in self.values:
            if int(self.values["rerank_depth"]) > int(self.values["pool_depth"]):
                raise ValueError("typed rerank depth cannot exceed pool depth")


@dataclass(frozen=True)
class TrackSTreatment:
    """Declare the exact editable treatment before an arm can be evaluated."""

    provenance: EngineProvenance
    skill_text_sha256: str
    overlay: C1TypedOverlay | None = None

    def validate(self) -> None:
        self.provenance.validate()
        if not is_sha256(self.skill_text_sha256):
            raise ValueError("Track S treatment must bind a skill text SHA-256")
        if self.provenance.arm == "A3":
            if self.overlay is None:
                raise ValueError("A3 requires a typed C1 overlay in addition to the full SkillOpt core")
            self.overlay.validate()
        elif self.overlay is not None:
            raise ValueError("only A3 may use a typed C1 overlay")


@dataclass(frozen=True)
class SelectionScores:
    out: float
    all: float
    in_domain: float

    def validate(self) -> None:
        if not all(isfinite(value) for value in (self.out, self.all, self.in_domain)):
            raise ValueError("Track S selection scores must be finite")


@dataclass(frozen=True)
class CandidateAcceptance:
    accepted: bool
    delta_out: float
    delta_all: float
    delta_in: float
    reason: str


@dataclass(frozen=True)
class SMarginRule:
    """Prospective signed OUT improvement with ALL/IN noninferiority floors."""

    margin_all: float
    margin_in: float
    baseline_audit_sha256: str
    owner_decision_sha256: str

    def validate(self) -> None:
        if self.margin_all < 0 or self.margin_in < 0:
            raise ValueError("S-MARGIN values must be non-negative")
        if not is_sha256(self.baseline_audit_sha256) or not is_sha256(self.owner_decision_sha256):
            raise ValueError("S-MARGIN must bind the baseline-only audit and Owner decision")

    def evaluate(self, incumbent: SelectionScores, candidate: SelectionScores) -> CandidateAcceptance:
        self.validate()
        incumbent.validate()
        candidate.validate()
        delta_out = candidate.out - incumbent.out
        delta_all = candidate.all - incumbent.all
        delta_in = candidate.in_domain - incumbent.in_domain
        # Treat tiny binary floating-point drift at a signed margin boundary as equal.
        epsilon = 1e-12
        accepted = (
            delta_out > epsilon
            and delta_all + epsilon >= -self.margin_all
            and delta_in + epsilon >= -self.margin_in
        )
        if delta_out <= 0:
            reason = "OUT_NOT_STRICTLY_GREATER"
        elif delta_all + epsilon < -self.margin_all:
            reason = "ALL_NONINFERIORITY_FAILED"
        elif delta_in + epsilon < -self.margin_in:
            reason = "IN_NONINFERIORITY_FAILED"
        else:
            reason = "STRICT_OUT_AND_NONINFERIORITY_PASS"
        return CandidateAcceptance(accepted, delta_out, delta_all, delta_in, reason)


@dataclass(frozen=True)
class SeedFinalist:
    seed: int
    artifact_sha256: str
    selection_score: float

    def validate(self) -> None:
        if self.seed not in TRACK_S_SEEDS:
            raise ValueError("Track S finalist seed is not preregistered")
        if not is_sha256(self.artifact_sha256):
            raise ValueError("Track S finalist must bind an artifact SHA-256")
        if not isfinite(self.selection_score):
            raise ValueError("Track S finalist score must be finite")


def select_arm_finalist(finalists: tuple[SeedFinalist, ...]) -> SeedFinalist:
    """Select the highest preregistered score; fixed seed priority resolves exact ties."""

    if len(finalists) != len(TRACK_S_SEEDS):
        raise ValueError("Track S selection requires exactly one finalist for each preregistered seed")
    for finalist in finalists:
        finalist.validate()
    if {finalist.seed for finalist in finalists} != set(TRACK_S_SEEDS):
        raise ValueError("Track S selection requires seeds 11, 23, and 47 exactly once")
    priority = {seed: index for index, seed in enumerate(TRACK_S_SEEDS)}
    return min(finalists, key=lambda finalist: (-finalist.selection_score, priority[finalist.seed]))


@dataclass(frozen=True)
class MatchedCampaign:
    """Aggregate realized resources required before a primary-arm comparison."""

    arm: str
    seed_rollouts: Mapping[int, int]
    stop_reason: str | None

    def validate(self) -> None:
        if self.arm not in {"A2", "A2L", "A3"}:
            raise ValueError("matched campaign must be A2, A2L, or A3")
        if set(self.seed_rollouts) != set(TRACK_S_SEEDS):
            raise ValueError("matched campaign must report all preregistered seeds")
        if any(not isinstance(value, int) or value < 0 or value > 160 for value in self.seed_rollouts.values()):
            raise ValueError("matched campaign rollouts must be integers from 0 through 160")


def assert_matched_realized_campaigns(*campaigns: MatchedCampaign) -> None:
    """Reject primary comparison when resource exhaustion favored one arm."""

    if len(campaigns) != 3 or {campaign.arm for campaign in campaigns} != {"A2", "A2L", "A3"}:
        raise ValueError("matched Track S validation requires A2, A2L, and A3 exactly once")
    for campaign in campaigns:
        campaign.validate()
    reference = campaigns[0]
    for campaign in campaigns[1:]:
        if campaign.seed_rollouts != reference.seed_rollouts or campaign.stop_reason != reference.stop_reason:
            raise ValueError("Track S realized rollout or stop schedules are not matched")


@dataclass(frozen=True)
class MechanismMetrics:
    """Descriptive treatment traces; never performance or confirmation metrics."""

    skill_text_edits: int
    overlay_value_count: int
    enabled_route_count: int
    pool_depth: int
    rerank_depth: int
    valid_rollout_count: int = 0
    rollout_to_best: int = 0
    accepted_update_count: int = 0
    invalid_patch_count: int = 0
    incumbent_replacement_count: int = 0
    final_skill_token_length: int = 0
    changed_typed_field_count: int = 0
    executable_expansion_rejection_count: int = 0

    def validate(self) -> None:
        values = {
            "skill_text_edits": self.skill_text_edits,
            "overlay_value_count": self.overlay_value_count,
            "enabled_route_count": self.enabled_route_count,
            "pool_depth": self.pool_depth,
            "rerank_depth": self.rerank_depth,
            "valid_rollout_count": self.valid_rollout_count,
            "rollout_to_best": self.rollout_to_best,
            "accepted_update_count": self.accepted_update_count,
            "invalid_patch_count": self.invalid_patch_count,
            "incumbent_replacement_count": self.incumbent_replacement_count,
            "final_skill_token_length": self.final_skill_token_length,
            "changed_typed_field_count": self.changed_typed_field_count,
            "executable_expansion_rejection_count": self.executable_expansion_rejection_count,
        }
        if any(value < 0 for value in values.values()):
            raise ValueError("descriptive mechanism metrics must be non-negative")
        if self.overlay_value_count > MAX_TYPED_OVERLAY_VALUES:
            raise ValueError("descriptive overlay count exceeds the typed overlay cap")


def _overlay_group(field: str) -> str:
    if field in _ROUTE_QUOTA_FIELDS:
        return "routes"
    if field in {"fusion_profile", "rrf_k"}:
        return "fusion"
    return "depths"
