"""Deterministic, aggregate-safe AutoIndex orchestration primitives."""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, ROUND_HALF_EVEN
import re
from typing import Any, Mapping

from ..kernel.canonical import canonical_sha256
from ..protection import assert_aggregate_only


AUTOINDEX_BATCH_ROLES = (
    "exploit",
    "matched_ablation",
    "orthogonal",
    "diversity",
)
AUTOINDEX_AXES = frozenset(
    {
        "source_fields",
        "field_order",
        "field_labels",
        "unitization",
        "independent_claim_extraction",
        "passage_size",
        "overlap",
        "boundaries",
        "packing",
        "normalization",
        "duplicate_handling",
        "family_aggregation",
    }
)
_CANDIDATE_KEYS = frozenset(
    {
        "candidate_id",
        "role",
        "hypothesis",
        "declared_axis",
        "program_sha256",
        "compiled_sha256",
        "scientific_payload_sha256",
        "matched_ablation_id",
        "compile_sha256s",
        "verifier_status",
    }
)
_BATCH_KEYS = frozenset(
    {
        "schema_version",
        "batch_id",
        "arm_id",
        "iteration",
        "incumbent_program_sha256",
        "frozen_bindings_sha256",
        "status",
        "candidates",
        "batch_sha256",
    }
)
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_STABLE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]+$")
_METRIC_QUANTUM = Decimal("0.000000000001")


class AutoIndexError(ValueError):
    """Raised when an AutoIndex artifact or transition is invalid."""


def canonical_metric(value: int | float | Decimal | str) -> Decimal:
    """Normalize a primary metric before any strict comparison."""

    numeric = value if isinstance(value, Decimal) else Decimal(str(value))
    if not numeric.is_finite():
        raise AutoIndexError("primary metric must be finite")
    return numeric.quantize(_METRIC_QUANTUM, rounding=ROUND_HALF_EVEN)


def strict_primary_improvement(
    candidate: int | float | Decimal | str,
    incumbent: int | float | Decimal | str,
) -> bool:
    """Return true only for a strictly greater canonical primary score."""

    return canonical_metric(candidate) > canonical_metric(incumbent)


def validate_autoindex_batch(
    value: Mapping[str, Any],
    *,
    seen_payload_sha256s: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    """Validate one complete batch frozen before any candidate is evaluated."""

    batch = dict(value)
    if set(batch) != _BATCH_KEYS:
        raise AutoIndexError("AutoIndex batch fields do not match the v1 contract")
    if batch["schema_version"] != "myis.armindex-autoindex-batch.v1":
        raise AutoIndexError("unsupported AutoIndex batch schema")
    if batch["status"] != "frozen_before_evaluation":
        raise AutoIndexError("AutoIndex batch must be frozen before evaluation")
    if not _STABLE_ID.fullmatch(str(batch["batch_id"])):
        raise AutoIndexError("AutoIndex batch_id is not stable lowercase text")
    if not re.fullmatch(r"ARM-0[1-5]", str(batch["arm_id"])):
        raise AutoIndexError("AutoIndex batch arm_id is invalid")
    if isinstance(batch["iteration"], bool) or int(batch["iteration"]) not in {1, 2, 3}:
        raise AutoIndexError("AutoIndex iteration must be one, two, or three")
    for field in ("incumbent_program_sha256", "frozen_bindings_sha256"):
        _require_sha256(batch[field], field)

    candidates = batch["candidates"]
    if not isinstance(candidates, list) or len(candidates) != 4:
        raise AutoIndexError("AutoIndex batch requires exactly four candidates")
    if tuple(item.get("role") for item in candidates if isinstance(item, Mapping)) != AUTOINDEX_BATCH_ROLES:
        raise AutoIndexError("AutoIndex batch roles and order are not canonical")

    candidate_ids: list[str] = []
    payload_hashes: list[str] = []
    for candidate in candidates:
        if not isinstance(candidate, Mapping) or set(candidate) != _CANDIDATE_KEYS:
            raise AutoIndexError("AutoIndex candidate fields do not match the v1 contract")
        candidate_id = str(candidate["candidate_id"])
        if not _STABLE_ID.fullmatch(candidate_id):
            raise AutoIndexError("AutoIndex candidate_id is not stable lowercase text")
        if not str(candidate["hypothesis"]).strip():
            raise AutoIndexError("AutoIndex hypothesis must be falsifiable text")
        if candidate["declared_axis"] not in AUTOINDEX_AXES:
            raise AutoIndexError("AutoIndex candidate declares an unsupported axis")
        for field in ("program_sha256", "compiled_sha256", "scientific_payload_sha256"):
            _require_sha256(candidate[field], field)
        compile_hashes = candidate["compile_sha256s"]
        if (
            not isinstance(compile_hashes, list)
            or len(compile_hashes) != 2
            or compile_hashes[0] != compile_hashes[1]
            or compile_hashes[0] != candidate["compiled_sha256"]
        ):
            raise AutoIndexError("candidate must compile twice to the same declared hash")
        if candidate["verifier_status"] != "accepted":
            raise AutoIndexError("candidate requires independent verifier acceptance")
        candidate_ids.append(candidate_id)
        payload_hashes.append(str(candidate["scientific_payload_sha256"]))

    if len(candidate_ids) != len(set(candidate_ids)):
        raise AutoIndexError("AutoIndex candidate IDs must be unique")
    if len(payload_hashes) != len(set(payload_hashes)):
        raise AutoIndexError("scientific payloads must be unique within a batch")
    if set(payload_hashes) & set(seen_payload_sha256s):
        raise AutoIndexError("scientific payload was already evaluated")

    exploit, ablation = candidates[:2]
    if (
        exploit["matched_ablation_id"] != ablation["candidate_id"]
        or ablation["matched_ablation_id"] != exploit["candidate_id"]
    ):
        raise AutoIndexError("exploit and matched ablation must bind each other")
    if any(item["matched_ablation_id"] is not None for item in candidates[2:]):
        raise AutoIndexError("orthogonal and diversity candidates cannot claim a matched ablation")

    unsigned = {key: item for key, item in batch.items() if key != "batch_sha256"}
    if batch["batch_sha256"] != canonical_sha256(unsigned):
        raise AutoIndexError("AutoIndex batch self-hash is invalid")
    return batch


def validate_aggregate_feedback(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate that proposer feedback contains aggregate-safe material only."""

    feedback = dict(value)
    try:
        assert_aggregate_only(feedback)
    except ValueError as error:
        raise AutoIndexError(str(error)) from error
    if feedback.get("schema_version") != "myis.armindex-autoindex-feedback.v1":
        raise AutoIndexError("unsupported AutoIndex feedback schema")
    recorded = feedback.get("feedback_sha256")
    unsigned = {key: item for key, item in feedback.items() if key != "feedback_sha256"}
    if recorded != canonical_sha256(unsigned):
        raise AutoIndexError("AutoIndex feedback self-hash is invalid")
    if feedback.get("protected_data_accessed") is not False:
        raise AutoIndexError("AutoIndex feedback must declare no protected-data access")
    return feedback


@dataclass(frozen=True)
class AutoIndexState:
    arm_id: str
    incumbent_candidate_id: str
    incumbent_program_sha256: str
    incumbent_primary: Decimal
    frozen_bindings_sha256: str
    completed_batches: int = 0
    strict_improvements: int = 0
    no_improvement_streak: int = 0
    seen_payload_sha256s: frozenset[str] = frozenset()
    terminal_state: str | None = None

    def __post_init__(self) -> None:
        if not re.fullmatch(r"ARM-0[1-5]", self.arm_id):
            raise AutoIndexError("AutoIndex state arm_id is invalid")
        _require_sha256(self.incumbent_program_sha256, "incumbent_program_sha256")
        _require_sha256(self.frozen_bindings_sha256, "frozen_bindings_sha256")
        object.__setattr__(self, "incumbent_primary", canonical_metric(self.incumbent_primary))


@dataclass(frozen=True)
class AutoIndexDecision:
    state: AutoIndexState
    best_candidate_id: str
    strict_improvement: bool
    next_action: str


def advance_autoindex(
    state: AutoIndexState,
    batch: Mapping[str, Any],
    primary_by_candidate: Mapping[str, int | float | Decimal | str],
    *,
    remaining_budget: bool,
    grounded_axes_remaining: bool,
) -> AutoIndexDecision:
    """Record one complete batch and deterministically decide stop, freeze, or batch three."""

    if state.terminal_state is not None:
        raise AutoIndexError("terminal AutoIndex state is immutable")
    validated = validate_autoindex_batch(
        batch,
        seen_payload_sha256s=state.seen_payload_sha256s,
    )
    if validated["arm_id"] != state.arm_id:
        raise AutoIndexError("AutoIndex batch arm differs from state")
    if int(validated["iteration"]) != state.completed_batches + 1:
        raise AutoIndexError("AutoIndex batches must be completed consecutively")
    if validated["incumbent_program_sha256"] != state.incumbent_program_sha256:
        raise AutoIndexError("AutoIndex batch does not bind the current incumbent")
    if validated["frozen_bindings_sha256"] != state.frozen_bindings_sha256:
        raise AutoIndexError("AutoIndex frozen bindings changed")

    candidate_ids = [str(item["candidate_id"]) for item in validated["candidates"]]
    if set(primary_by_candidate) != set(candidate_ids):
        raise AutoIndexError("one primary metric is required for every batch candidate")
    canonical_scores = {
        candidate_id: canonical_metric(primary_by_candidate[candidate_id])
        for candidate_id in candidate_ids
    }
    best_candidate_id = min(
        candidate_ids,
        key=lambda candidate_id: (-canonical_scores[candidate_id], candidate_id),
    )
    best_score = canonical_scores[best_candidate_id]
    improved = strict_primary_improvement(best_score, state.incumbent_primary)
    best_candidate = next(
        item for item in validated["candidates"] if item["candidate_id"] == best_candidate_id
    )
    payload_hashes = frozenset(
        str(item["scientific_payload_sha256"]) for item in validated["candidates"]
    )
    updated = replace(
        state,
        incumbent_candidate_id=best_candidate_id if improved else state.incumbent_candidate_id,
        incumbent_program_sha256=(
            str(best_candidate["program_sha256"])
            if improved
            else state.incumbent_program_sha256
        ),
        incumbent_primary=best_score if improved else state.incumbent_primary,
        completed_batches=state.completed_batches + 1,
        strict_improvements=state.strict_improvements + int(improved),
        no_improvement_streak=0 if improved else state.no_improvement_streak + 1,
        seen_payload_sha256s=state.seen_payload_sha256s | payload_hashes,
    )

    if updated.completed_batches < 2:
        action = "run_required_batch"
    elif updated.no_improvement_streak >= 2:
        action = "stop_flat_representation_surface"
        updated = replace(
            updated,
            terminal_state="STOP_WITH_EVIDENCE_FLAT_REPRESENTATION_SURFACE",
        )
    elif updated.completed_batches == 2 and (
        updated.strict_improvements == 0
        or not remaining_budget
        or not grounded_axes_remaining
    ):
        action = "freeze_arm_program"
        updated = replace(updated, terminal_state="FREEZE_ARM_PROGRAM")
    elif updated.completed_batches == 2:
        action = "run_gated_third_batch"
    else:
        action = "freeze_arm_program"
        updated = replace(updated, terminal_state="FREEZE_ARM_PROGRAM")
    return AutoIndexDecision(updated, best_candidate_id, improved, action)


def build_autoindex_terminal_receipt(
    state: AutoIndexState,
    *,
    evidence_ids: tuple[str, ...],
) -> dict[str, Any]:
    """Build one aggregate-only hash-bound terminal receipt."""

    if state.terminal_state is None:
        raise AutoIndexError("AutoIndex terminal receipt requires terminal state")
    if not evidence_ids or len(evidence_ids) != len(set(evidence_ids)):
        raise AutoIndexError("terminal receipt requires unique evidence IDs")
    body: dict[str, Any] = {
        "schema_version": "myis.armindex-autoindex-terminal.v1",
        "arm_id": state.arm_id,
        "terminal_state": state.terminal_state,
        "winner_candidate_id": state.incumbent_candidate_id,
        "winner_program_sha256": state.incumbent_program_sha256,
        "primary_metric": str(state.incumbent_primary),
        "completed_batches": state.completed_batches,
        "strict_improvements": state.strict_improvements,
        "frozen_bindings_sha256": state.frozen_bindings_sha256,
        "evidence_ids": list(evidence_ids),
        "protected_data_accessed": False,
    }
    assert_aggregate_only(body)
    body["receipt_sha256"] = canonical_sha256(body)
    return body


def _require_sha256(value: Any, field: str) -> None:
    if not _SHA256.fullmatch(str(value)):
        raise AutoIndexError(f"{field} must be SHA-256")
