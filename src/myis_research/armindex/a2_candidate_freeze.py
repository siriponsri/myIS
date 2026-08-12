"""Generate, verify, and freeze the pre-measurement A2 candidate universe."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_json, canonical_sha256, file_sha256
from ..kernel.p1 import tokenize
from .compiler import RepresentationCompileError, compile_program
from .official_codex_bridge import (
    BridgeConfig,
    OfficialCodexBridgeError,
    invoke_operation,
    load_bridge_config,
)

MANIFEST_SCHEMA_VERSION = "myis.armindex-a2-candidate-manifest.v1"
FREEZE_RECEIPT_SCHEMA_VERSION = "myis.armindex-a2-candidate-freeze-receipt.v1"
FREEZE_LOCK_SCHEMA_VERSION = "myis.armindex-a2-candidate-freeze-lock.v1"
CONTRACT_SCHEMA_VERSION = "myis.armindex-a2-execution-contract.v1"
BUDGET_SCHEMA_VERSION = "myis.armindex-a2-budget-profile.v1"
ENVELOPE_SCHEMA_VERSION = "myis.execution-envelope-a2.v1"
CAMPAIGN_ID = "armindex-multiretriever-v2"
PHASE_ID = "A2_PER_ARM_AUTOINDEX"
TASK_ID = "OFFICIAL_CODEX_BRIDGE_AND_CANDIDATE_FREEZE"
REVISION_ID = "a2-five-arm-premeasurement-freeze-v1"
SEED = 20260812
ARMS = ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")
PRIMARY_ADVANCEMENT_ARMS = ("ARM-03", "ARM-05", "ARM-04")
DIAGNOSTIC_NON_ADVANCING_ARMS = ("ARM-01", "ARM-02")
ROLES = ("exploit", "matched_ablation", "orthogonal", "diversity")
ALLOWED_SOURCE_FIELDS = ("title", "abstract", "claims_text")
ALLOWED_AXES = (
    "field_selection",
    "field_order",
    "field_labeling",
    "unitization",
    "normalization",
    "duplicate_policy",
    "family_aggregation",
)
AXIS_TO_AUTOINDEX = {
    "field_selection": "source_fields",
    "field_order": "field_order",
    "field_labeling": "field_labels",
    "unitization": "unitization",
    "normalization": "normalization",
    "duplicate_policy": "duplicate_handling",
    "family_aggregation": "family_aggregation",
}
ARM_CONTEXTS: Mapping[str, Mapping[str, Any]] = {
    "ARM-01": {
        "model_id": "lexical/bm25s",
        "method": "bm25",
        "effective_max_input_tokens": 4096,
    },
    "ARM-02": {
        "model_id": "BAAI/bge-m3",
        "method": "dense_embedding",
        "effective_max_input_tokens": 8192,
    },
    "ARM-03": {
        "model_id": "datalyes/patembed-large",
        "method": "patent_dense_embedding",
        "effective_max_input_tokens": 512,
    },
    "ARM-04": {
        "model_id": "Snowflake/snowflake-arctic-embed-m-v2.0",
        "method": "dense_embedding",
        "effective_max_input_tokens": 8192,
    },
    "ARM-05": {
        "model_id": "Qwen/Qwen3-Embedding-0.6B",
        "method": "instruction_dense_embedding",
        "effective_max_input_tokens": 32768,
    },
}
REVIEW_CRITERIA = (
    "falsifiability",
    "role_fit",
    "duplication",
    "protected_boundary",
    "arm_compatibility",
    "determinism",
    "publication_interpretability",
)
RESERVE_ACTIVATION_PREDICATE = (
    "after_two_complete_matched_batches AND strict_primary_improvement "
    "AND grounded_axis_remaining AND fresh_budget_admission_pass"
)
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_CANDIDATE_ID = re.compile(
    r"^a2-arm-(0[1-5])-(matched|reserve)-b([1-3])-"
    r"(exploit|matched-ablation|orthogonal|diversity)$"
)


class A2CandidateFreezeError(RuntimeError):
    """Raised when the candidate universe cannot be frozen safely."""


@dataclass(frozen=True)
class BatchSpec:
    batch_id: str
    arm_id: str
    tier: str
    batch_index: int
    candidate_slots: tuple[dict[str, str], ...]
    diagnostic_non_advancing: bool
    advancement_eligible: bool


InvokeOperation = Callable[[BridgeConfig, str, Mapping[str, Any]], dict[str, Any]]


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _generation_attempt_id() -> str:
    return datetime.now(UTC).strftime("a2freeze-%Y%m%dt%H%M%Sz").casefold()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise A2CandidateFreezeError(f"invalid JSON file: {path}") from exc
    if not isinstance(value, dict):
        raise A2CandidateFreezeError(f"JSON root must be an object: {path}")
    return value


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise A2CandidateFreezeError(f"invalid YAML file: {path}") from exc
    if not isinstance(value, dict):
        raise A2CandidateFreezeError(f"YAML root must be an object: {path}")
    return value


def _validate_schema(value: Mapping[str, Any], schema_path: Path) -> None:
    schema = _load_json(schema_path)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(value)),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if errors:
        first = errors[0]
        location = ".".join(str(item) for item in first.absolute_path) or "$"
        raise A2CandidateFreezeError(
            f"schema validation failed at {location}: {first.message}"
        )


def candidate_id(arm_id: str, tier: str, batch_index: int, role: str) -> str:
    role_id = role.replace("_", "-")
    arm_number = arm_id.removeprefix("ARM-")
    tier_id = "matched" if tier == "matched" else "reserve"
    value = f"a2-arm-{arm_number}-{tier_id}-b{batch_index}-{role_id}"
    if not _CANDIDATE_ID.fullmatch(value):
        raise A2CandidateFreezeError("candidate ID convention is invalid")
    return value


def build_batch_specs() -> tuple[BatchSpec, ...]:
    specs: list[BatchSpec] = []
    for arm_id in ARMS:
        for batch_index in (1, 2):
            tier = "matched"
            specs.append(
                _batch_spec(arm_id, tier=tier, batch_index=batch_index)
            )
    for arm_id in PRIMARY_ADVANCEMENT_ARMS:
        specs.append(
            _batch_spec(arm_id, tier="conditional_reserve", batch_index=3)
        )
    return tuple(specs)


def _batch_spec(arm_id: str, *, tier: str, batch_index: int) -> BatchSpec:
    tier_id = "matched" if tier == "matched" else "reserve"
    batch_id = f"a2-{arm_id.casefold()}-{tier_id}-b{batch_index}"
    slots = tuple(
        {"candidate_id": candidate_id(arm_id, tier, batch_index, role), "role": role}
        for role in ROLES
    )
    diagnostic = arm_id in DIAGNOSTIC_NON_ADVANCING_ARMS
    return BatchSpec(
        batch_id=batch_id,
        arm_id=arm_id,
        tier=tier,
        batch_index=batch_index,
        candidate_slots=slots,
        diagnostic_non_advancing=diagnostic,
        advancement_eligible=not diagnostic,
    )


def design_summary() -> dict[str, Any]:
    specs = build_batch_specs()
    matched = [slot for spec in specs if spec.tier == "matched" for slot in spec.candidate_slots]
    reserve = [
        slot
        for spec in specs
        if spec.tier == "conditional_reserve"
        for slot in spec.candidate_slots
    ]
    return {
        "arms": list(ARMS),
        "primary_advancement_arms": list(PRIMARY_ADVANCEMENT_ARMS),
        "diagnostic_non_advancing_arms": list(DIAGNOSTIC_NON_ADVANCING_ARMS),
        "roles": list(ROLES),
        "matched_batches_per_arm": 2,
        "matched_candidates_per_arm": 8,
        "conditional_reserve_candidates_per_primary_arm": 4,
        "matched_candidate_count": len(matched),
        "conditional_reserve_candidate_count": len(reserve),
        "candidate_count": len(matched) + len(reserve),
        "batch_count": len(specs),
        "reserve_activation_predicate": RESERVE_ACTIVATION_PREDICATE,
        "stable_id_pattern": _CANDIDATE_ID.pattern,
    }


def validate_design() -> dict[str, Any]:
    summary = design_summary()
    if summary["matched_candidate_count"] != 40:
        raise A2CandidateFreezeError("matched candidate count must be 40")
    if summary["conditional_reserve_candidate_count"] != 12:
        raise A2CandidateFreezeError("conditional reserve count must be 12")
    if summary["candidate_count"] != 52 or summary["batch_count"] != 13:
        raise A2CandidateFreezeError("candidate universe must be 52 across 13 batches")
    specs = build_batch_specs()
    ids = [slot["candidate_id"] for spec in specs for slot in spec.candidate_slots]
    if len(ids) != len(set(ids)):
        raise A2CandidateFreezeError("candidate IDs must be unique")
    for spec in specs:
        if tuple(slot["role"] for slot in spec.candidate_slots) != ROLES:
            raise A2CandidateFreezeError("batch roles are not canonical")
        if spec.arm_id in DIAGNOSTIC_NON_ADVANCING_ARMS:
            if spec.batch_index == 3 or spec.advancement_eligible:
                raise A2CandidateFreezeError("diagnostic arms cannot advance or receive reserve")
        elif not spec.advancement_eligible:
            raise A2CandidateFreezeError("primary arms must remain advancement eligible")
    return summary


def _validate_control_set(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    envelope_path = root / "control/execution-envelope-a2-v1.yaml"
    budget_path = root / "control/budgets/a2-per-arm-autoindex-v1.json"
    contract_path = root / "control/armindex/a2/execution-contract.v1.json"
    envelope = _load_yaml(envelope_path)
    budget = _load_json(budget_path)
    contract = _load_json(contract_path)
    if envelope.get("schema_version") != ENVELOPE_SCHEMA_VERSION:
        raise A2CandidateFreezeError("A2 envelope schema version mismatch")
    if budget.get("schema_version") != BUDGET_SCHEMA_VERSION:
        raise A2CandidateFreezeError("A2 budget schema version mismatch")
    if contract.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        raise A2CandidateFreezeError("A2 execution contract schema version mismatch")
    if canonical_sha256({k: v for k, v in budget.items() if k != "budget_profile_sha256"}) != budget.get(
        "budget_profile_sha256"
    ):
        raise A2CandidateFreezeError("A2 budget self-hash mismatch")
    if canonical_sha256({k: v for k, v in contract.items() if k != "contract_sha256"}) != contract.get(
        "contract_sha256"
    ):
        raise A2CandidateFreezeError("A2 execution contract self-hash mismatch")
    design = validate_design()
    if contract.get("candidate_design") != design:
        raise A2CandidateFreezeError("A2 contract candidate design mismatch")
    if budget.get("candidate_design") != {
        "matched_candidate_count": 40,
        "conditional_reserve_candidate_count": 12,
        "candidate_count": 52,
    }:
        raise A2CandidateFreezeError("A2 budget does not cover 40+12 candidates")
    if contract.get("measured_execution_allowed") is not False:
        raise A2CandidateFreezeError("preparation contract must not authorize measurement")
    return {
        "envelope": envelope,
        "envelope_path": envelope_path,
        "budget": budget,
        "budget_path": budget_path,
        "contract": contract,
        "contract_path": contract_path,
    }


def _frozen_bindings(repository_root: Path, controls: Mapping[str, Any]) -> dict[str, str]:
    root = repository_root.resolve()
    summary_path = root / (
        "campaigns/armindex-multiretriever-v2/evidence/a1.2-result-summaries/"
        "a12-v16-20260811-r15.summary.v16.json"
    )
    terminal_path = root / (
        "campaigns/armindex-multiretriever-v2/evidence/a1.2-terminal-attempts/"
        "a12-v16-20260811-r15.receipt.v16.json"
    )
    summary = _load_json(summary_path)
    terminal = _load_json(terminal_path)
    if summary.get("promoted_arm_ids") != list(PRIMARY_ADVANCEMENT_ARMS):
        raise A2CandidateFreezeError("A1 promotion binding changed")
    if terminal.get("status") != "PASS" or terminal.get("coverage") != {
        "completed_logical_cells": 25,
        "partial_results_promotable": False,
        "required_logical_cells": 25,
    }:
        raise A2CandidateFreezeError("A1 terminal 25/25 binding changed")
    return {
        "campaign_sha256": file_sha256(
            root / "control/campaigns/armindex-multiretriever-v2.yaml"
        ),
        "a1_terminal_receipt_sha256": str(terminal["receipt_sha256"]),
        "promotion_receipt_sha256": str(terminal["promotion_receipt_sha256"]),
        "representation_schema_sha256": file_sha256(
            root / "schemas/armindex/representation-program.v1.json"
        ),
        "evaluator_sha256": str(terminal["evaluator_receipt_sha256"]),
        "primary_metric": "recall_at_100/out",
        "a1_summary_sha256": str(summary["summary_sha256"]),
        "a1_summary_file_sha256": file_sha256(summary_path),
        "a1_terminal_file_sha256": file_sha256(terminal_path),
        "execution_envelope_sha256": file_sha256(controls["envelope_path"]),
        "budget_profile_sha256": str(controls["budget"]["budget_profile_sha256"]),
        "execution_contract_sha256": str(controls["contract"]["contract_sha256"]),
    }


def _arm_context(spec: BatchSpec) -> dict[str, Any]:
    return {
        **dict(ARM_CONTEXTS[spec.arm_id]),
        "diagnostic_non_advancing": spec.diagnostic_non_advancing,
        "advancement_eligible": spec.advancement_eligible,
    }


def _propose_request(
    spec: BatchSpec,
    bindings: Mapping[str, str],
    *,
    generation_attempt_id: str,
    revision_round: int,
    reviewer_required_changes: Sequence[str],
) -> dict[str, Any]:
    return {
        "schema_version": "myis.armindex-representation-propose-request.v1",
        "request_id": f"{generation_attempt_id}-propose-{spec.arm_id.casefold()}-{spec.tier}-b{spec.batch_index}-r{revision_round}",
        "arm_id": spec.arm_id,
        "tier": spec.tier,
        "batch_id": spec.batch_id,
        "batch_index": spec.batch_index,
        "revision_round": revision_round,
        "reviewer_required_changes": list(reviewer_required_changes),
        "candidate_slots": [dict(slot) for slot in spec.candidate_slots],
        "allowed_source_fields": list(ALLOWED_SOURCE_FIELDS),
        "allowed_axes": list(ALLOWED_AXES),
        "arm_context": _arm_context(spec),
        "frozen_bindings": {
            key: bindings[key]
            for key in (
                "campaign_sha256",
                "a1_terminal_receipt_sha256",
                "promotion_receipt_sha256",
                "representation_schema_sha256",
                "evaluator_sha256",
                "primary_metric",
            )
        },
        "protected_data_accessed": False,
        "measured_execution_performed": False,
    }


def _review_request(
    spec: BatchSpec,
    candidates: Sequence[Mapping[str, Any]],
    bindings: Mapping[str, str],
    *,
    generation_attempt_id: str,
    review_round: int,
) -> dict[str, Any]:
    return {
        "schema_version": "myis.armindex-representation-review-request.v1",
        "request_id": f"{generation_attempt_id}-review-{spec.arm_id.casefold()}-{spec.tier}-b{spec.batch_index}-r{review_round}",
        "arm_id": spec.arm_id,
        "tier": spec.tier,
        "batch_id": spec.batch_id,
        "review_round": review_round,
        "arm_context": _arm_context(spec),
        "candidates": [dict(candidate) for candidate in candidates],
        "review_criteria": list(REVIEW_CRITERIA),
        "frozen_bindings": {
            key: bindings[key]
            for key in (
                "campaign_sha256",
                "a1_terminal_receipt_sha256",
                "promotion_receipt_sha256",
                "representation_schema_sha256",
                "evaluator_sha256",
                "primary_metric",
            )
        },
        "protected_data_accessed": False,
        "measured_execution_performed": False,
    }


def _validate_proposal_response(
    spec: BatchSpec, response: Mapping[str, Any]
) -> list[dict[str, Any]]:
    result = response.get("result")
    if not isinstance(result, dict):
        raise A2CandidateFreezeError("proposer response is missing result")
    if (
        result.get("request_id") != response.get("request_id")
        or result.get("arm_id") != spec.arm_id
        or result.get("tier") != spec.tier
        or result.get("batch_id") != spec.batch_id
    ):
        raise A2CandidateFreezeError("proposer response identity mismatch")
    candidates = result.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 4:
        raise A2CandidateFreezeError("proposer must return four candidates")
    expected = [dict(slot) for slot in spec.candidate_slots]
    observed = [
        {"candidate_id": item.get("candidate_id"), "role": item.get("role")}
        for item in candidates
        if isinstance(item, dict)
    ]
    if observed != expected:
        raise A2CandidateFreezeError("proposer changed candidate slots or role order")
    normalized: list[dict[str, Any]] = []
    for item in candidates:
        if not isinstance(item, dict):
            raise A2CandidateFreezeError("candidate proposal must be an object")
        _normalize_program(spec, item)
        normalized.append(dict(item))
    return normalized


def _review_acceptance(
    spec: BatchSpec,
    response: Mapping[str, Any],
) -> tuple[bool, list[str], dict[str, dict[str, Any]]]:
    result = response.get("result")
    if not isinstance(result, dict):
        raise A2CandidateFreezeError("reviewer response is missing result")
    if (
        result.get("request_id") != response.get("request_id")
        or result.get("arm_id") != spec.arm_id
        or result.get("tier") != spec.tier
        or result.get("batch_id") != spec.batch_id
    ):
        raise A2CandidateFreezeError("reviewer response identity mismatch")
    reviews = result.get("reviews")
    if not isinstance(reviews, list) or len(reviews) != 4:
        raise A2CandidateFreezeError("reviewer must return four reviews")
    expected_ids = [slot["candidate_id"] for slot in spec.candidate_slots]
    if [item.get("candidate_id") for item in reviews if isinstance(item, dict)] != expected_ids:
        raise A2CandidateFreezeError("reviewer changed candidate order or IDs")
    required_checks = (
        "falsifiable",
        "role_fit",
        "duplicate_free",
        "protected_boundary_safe",
        "arm_compatible",
        "deterministic",
        "publication_interpretable",
    )
    feedback: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}
    accepted = True
    for review in reviews:
        if not isinstance(review, dict):
            raise A2CandidateFreezeError("candidate review must be an object")
        candidate = str(review["candidate_id"])
        by_id[candidate] = dict(review)
        item_accepted = review.get("verdict") == "accept" and all(
            review.get(check) is True for check in required_checks
        )
        accepted = accepted and item_accepted
        if not item_accepted:
            changes = review.get("required_changes")
            if isinstance(changes, list) and changes:
                feedback.extend(f"{candidate}: {change!s}" for change in changes)
            else:
                feedback.append(f"{candidate}: {review.get('rationale', 'revise')!s}")
    return accepted, feedback, by_id


def _normalize_program(spec: BatchSpec, candidate: Mapping[str, Any]) -> dict[str, Any]:
    proposal = candidate.get("program")
    if not isinstance(proposal, dict):
        raise A2CandidateFreezeError("candidate program proposal is missing")
    fields = [str(item) for item in proposal.get("source_fields", [])]
    order = [str(item) for item in proposal.get("field_order", [])]
    if (
        not fields
        or len(fields) != len(set(fields))
        or set(fields) != set(order)
        or len(order) != len(set(order))
        or not set(fields) <= set(ALLOWED_SOURCE_FIELDS)
    ):
        raise A2CandidateFreezeError("program source_fields/field_order is invalid")
    label_source = proposal.get("field_labels")
    if not isinstance(label_source, dict) or set(label_source) != set(ALLOWED_SOURCE_FIELDS):
        raise A2CandidateFreezeError("program field_labels must cover the public field vocabulary")
    labels = {field: str(label_source[field]) for field in fields}
    unitization = proposal.get("unitization")
    if not isinstance(unitization, dict):
        raise A2CandidateFreezeError("program unitization is invalid")
    kind = str(unitization.get("kind"))
    logical_size = unitization.get("logical_size")
    overlap = unitization.get("overlap")
    if kind == "passage":
        if (
            isinstance(logical_size, bool)
            or not isinstance(logical_size, int)
            or logical_size < 32
            or logical_size > int(ARM_CONTEXTS[spec.arm_id]["effective_max_input_tokens"])
            or isinstance(overlap, bool)
            or not isinstance(overlap, int)
            or overlap < 0
            or overlap >= logical_size
        ):
            raise A2CandidateFreezeError("passage size/overlap exceeds the arm contract")
    elif kind in {"family", "field", "section"}:
        if logical_size is not None or overlap != 0:
            raise A2CandidateFreezeError("non-passage unitization requires null size and zero overlap")
    else:
        raise A2CandidateFreezeError("program unitization is outside canonical compiler intersection")
    aggregation = str(proposal.get("family_aggregation"))
    if aggregation == "single_unit" and kind != "family":
        raise A2CandidateFreezeError("single_unit aggregation requires family unitization")
    unsigned: dict[str, Any] = {
        "schema_version": "myis.armindex-representation-program.v1",
        "program_id": str(candidate["candidate_id"]),
        "arm_id": spec.arm_id,
        "source_fields": fields,
        "field_order": order,
        "field_labels": labels,
        "unitization": {
            "kind": kind,
            "logical_size": logical_size,
            "overlap": overlap,
        },
        "normalization": str(proposal.get("normalization")),
        "duplicate_policy": str(proposal.get("duplicate_policy")),
        "family_aggregation": aggregation,
        "preserve_family_identity": True,
    }
    program = {**unsigned, "program_sha256": canonical_sha256(unsigned)}
    return program


def _synthetic_documents(program: Mapping[str, Any]) -> list[dict[str, str]]:
    source = {
        "title": "Adaptive retrieval representation for structured technical records",
        "abstract": "A deterministic system reorganizes public document fields while preserving family identity.",
        "claims_text": "1. A method comprising deterministic field selection. 2. The method preserves source provenance.",
    }
    second = {
        "title": "Auditable indexing for multilingual patent families",
        "abstract": "An indexing pipeline compiles bounded units without silent truncation or model changes.",
        "claims_text": "1. A system validates stable identifiers. 2. The system emits hash-bound aggregate receipts.",
    }
    fields = tuple(str(item) for item in program["source_fields"])
    return [
        {
            "family_id": "SYN-FAMILY-001",
            "publication_id": "SYN-PUB-001",
            **{field: source[field] for field in fields},
        },
        {
            "family_id": "SYN-FAMILY-002",
            "publication_id": "SYN-PUB-002",
            **{field: second[field] for field in fields},
        },
    ]


def _compile_and_verify(
    repository_root: Path,
    spec: BatchSpec,
    candidate: Mapping[str, Any],
    review: Mapping[str, Any],
    proposer_response: Mapping[str, Any],
    reviewer_response: Mapping[str, Any],
    proposer_request: Mapping[str, Any],
    reviewer_request: Mapping[str, Any],
) -> dict[str, Any]:
    program = _normalize_program(spec, candidate)
    _validate_schema(
        program,
        repository_root / "schemas/armindex/representation-program.v1.json",
    )
    documents = _synthetic_documents(program)
    try:
        first = compile_program(program, documents)
        second = compile_program(program, documents)
    except RepresentationCompileError as exc:
        raise A2CandidateFreezeError(
            f"candidate {candidate['candidate_id']} failed deterministic compile"
        ) from exc
    if first.compiled_representation_sha256 != second.compiled_representation_sha256:
        raise A2CandidateFreezeError("candidate compile-twice hash mismatch")
    if first.truncated_span_count != 0 or second.truncated_span_count != 0:
        raise A2CandidateFreezeError("candidate compiler reported silent truncation")
    effective_limit = int(ARM_CONTEXTS[spec.arm_id]["effective_max_input_tokens"])
    if any(len(tokenize(unit.text)) > effective_limit for unit in first.units):
        raise A2CandidateFreezeError("compiled unit exceeds effective arm token limit")
    scientific_payload = {
        "arm_id": spec.arm_id,
        "tier": spec.tier,
        "role": candidate["role"],
        "hypothesis": candidate["hypothesis"],
        "declared_axis": candidate["declared_axis"],
        "program": {
            key: value
            for key, value in program.items()
            if key not in {"program_id", "program_sha256"}
        },
    }
    role = str(candidate["role"])
    paired = None
    if role == "exploit":
        paired = spec.candidate_slots[1]["candidate_id"]
    elif role == "matched_ablation":
        paired = spec.candidate_slots[0]["candidate_id"]
    lifecycle = "active_matched" if spec.tier == "matched" else "dormant_conditional"
    return {
        "candidate_id": str(candidate["candidate_id"]),
        "arm_id": spec.arm_id,
        "tier": spec.tier,
        "batch_id": spec.batch_id,
        "batch_index": spec.batch_index,
        "role": role,
        "lifecycle": lifecycle,
        "advancement_eligible": spec.advancement_eligible,
        "diagnostic_non_advancing": spec.diagnostic_non_advancing,
        "hypothesis": str(candidate["hypothesis"]),
        "declared_axis": AXIS_TO_AUTOINDEX[str(candidate["declared_axis"])],
        "program": program,
        "program_sha256": program["program_sha256"],
        "compiled_sha256": first.compiled_representation_sha256,
        "compile_sha256s": [
            first.compiled_representation_sha256,
            second.compiled_representation_sha256,
        ],
        "scientific_payload_sha256": canonical_sha256(scientific_payload),
        "matched_ablation_id": paired,
        "proposer_request_sha256": canonical_sha256(dict(proposer_request)),
        "proposer_event_sha256": str(proposer_response["event_sha256"]),
        "reviewer_request_sha256": canonical_sha256(dict(reviewer_request)),
        "reviewer_event_sha256": str(reviewer_response["event_sha256"]),
        "review_verdict": str(review["verdict"]),
        "verifier_status": "accepted",
        "synthetic_source_sha256": first.source_sha256,
        "omitted_unit_count": first.omitted_unit_count,
        "truncated_span_count": first.truncated_span_count,
    }


def _official_identity(response: Mapping[str, Any]) -> dict[str, str]:
    identity = response.get("identity")
    if not isinstance(identity, dict):
        raise A2CandidateFreezeError("Official response identity is missing")
    required = {
        "sdk_version": "0.144.4",
        "cli_version": "0.144.4",
        "model": "gpt-5.6-sol",
        "model_provider": "openai",
        "reasoning_effort": "high",
    }
    if any(identity.get(key) != value for key, value in required.items()):
        raise A2CandidateFreezeError("Official response identity changed")
    if not str(identity.get("runtime_user_agent", "")).strip():
        raise A2CandidateFreezeError("Official runtime user agent is missing")
    return {str(key): str(value) for key, value in identity.items()}


def _generate_batch(
    repository_root: Path,
    bridge_config: BridgeConfig,
    spec: BatchSpec,
    bindings: Mapping[str, str],
    generation_attempt_id: str,
    invoke: InvokeOperation,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    feedback: list[str] = []
    last_error: Exception | None = None
    for revision_round in range(3):
        proposer_request = _propose_request(
            spec,
            bindings,
            generation_attempt_id=generation_attempt_id,
            revision_round=revision_round,
            reviewer_required_changes=feedback,
        )
        try:
            proposer_response = invoke(
                bridge_config, "representation_propose", proposer_request
            )
            proposer_identity = _official_identity(proposer_response)
            candidates = _validate_proposal_response(spec, proposer_response)
        except (A2CandidateFreezeError, OfficialCodexBridgeError) as exc:
            last_error = exc
            feedback = [f"schema/compiler compatibility repair: {type(exc).__name__}"]
            continue
        reviewer_request = _review_request(
            spec,
            candidates,
            bindings,
            generation_attempt_id=generation_attempt_id,
            review_round=revision_round,
        )
        try:
            reviewer_response = invoke(
                bridge_config, "representation_review", reviewer_request
            )
            reviewer_identity = _official_identity(reviewer_response)
            accepted, feedback, reviews = _review_acceptance(spec, reviewer_response)
        except (A2CandidateFreezeError, OfficialCodexBridgeError) as exc:
            last_error = exc
            feedback = [f"review integration repair: {type(exc).__name__}"]
            continue
        if not accepted:
            last_error = A2CandidateFreezeError("Official reviewer requested revision")
            continue
        try:
            records = [
                _compile_and_verify(
                    repository_root,
                    spec,
                    candidate,
                    reviews[str(candidate["candidate_id"])],
                    proposer_response,
                    reviewer_response,
                    proposer_request,
                    reviewer_request,
                )
                for candidate in candidates
            ]
        except A2CandidateFreezeError as exc:
            last_error = exc
            feedback = [f"deterministic compiler/verifier repair: {type(exc).__name__}"]
            continue
        batch = {
            "batch_id": spec.batch_id,
            "arm_id": spec.arm_id,
            "tier": spec.tier,
            "batch_index": spec.batch_index,
            "candidate_ids": [record["candidate_id"] for record in records],
            "proposer_request_sha256": canonical_sha256(proposer_request),
            "proposer_event_sha256": proposer_response["event_sha256"],
            "reviewer_request_sha256": canonical_sha256(reviewer_request),
            "reviewer_event_sha256": reviewer_response["event_sha256"],
            "revision_round": revision_round,
            "status": "accepted_frozen_before_measurement",
        }
        batch["batch_sha256"] = canonical_sha256(batch)
        return records, {
            **batch,
            "proposer_identity_sha256": canonical_sha256(proposer_identity),
            "reviewer_identity_sha256": canonical_sha256(reviewer_identity),
        }
    raise A2CandidateFreezeError(
        f"batch {spec.batch_id} exhausted bounded propose/review rounds"
    ) from last_error


def _git_identity(repository_root: Path) -> tuple[str, str]:
    values = []
    for args in (("rev-parse", "HEAD"), ("rev-parse", "HEAD^{tree}")):
        completed = subprocess.run(
            ["git", *args],
            cwd=repository_root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=15,
        )
        value = completed.stdout.strip()
        if completed.returncode != 0 or not re.fullmatch(r"[a-f0-9]{40,64}", value):
            raise A2CandidateFreezeError("source Git identity is unavailable")
        values.append(value)
    return values[0], values[1]


def _write_once(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="ascii", newline="") as handle:
            handle.write(canonical_json(dict(value)) + "\n")
    except FileExistsError as exc:
        raise A2CandidateFreezeError(f"write-once artifact already exists: {path}") from exc


def _canonical_file_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256((canonical_json(dict(value)) + "\n").encode("ascii")).hexdigest()


def append_preparation_ledger_event(
    repository_root: Path,
    *,
    generation_attempt_id: str,
    event_type: str,
    status: str,
    summary: str,
    evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    ledger_path = repository_root / "control/armindex/a2/preparation-ledger.v1.jsonl"
    lines = [
        line
        for line in ledger_path.read_text(encoding="ascii").splitlines()
        if line.strip()
    ]
    if not lines:
        raise A2CandidateFreezeError("preparation ledger is empty")
    try:
        previous = json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        raise A2CandidateFreezeError("preparation ledger tail is invalid") from exc
    sequence = int(previous["sequence"]) + 1
    body: dict[str, Any] = {
        "schema_version": "myis.armindex-a2-preparation-ledger-entry.v1",
        "ledger_id": "a2-official-codex-candidate-freeze-preparation-v1",
        "event_id": f"A2PREP-EV{sequence:04d}",
        "sequence": sequence,
        "previous_entry_sha256": str(previous["entry_sha256"]),
        "event_type": event_type,
        "generation_attempt_id": generation_attempt_id,
        "status": status,
        "summary": summary,
        "evidence_class": "engineering_preparation",
        "scientific_authority": False,
        "safety": {
            "final_opened": False,
            "gpu_used": False,
            "measured_a2_execution": False,
            "paid_api_used": False,
            "protected_data_accessed": False,
            "provider_admission_performed": False,
            "provider_execution_adoption_performed": False,
            "rep_dev_accessed_for_measurement": False,
            "selection_opened": False,
        },
        "timestamp_utc": _utc_now(),
    }
    if evidence:
        body["evidence"] = dict(evidence)
    body["entry_sha256"] = canonical_sha256(body)
    with ledger_path.open("a", encoding="ascii", newline="") as handle:
        handle.write(canonical_json(body) + "\n")
    return body


def generate_and_freeze(
    repository_root: Path,
    *,
    bridge_config: BridgeConfig | None = None,
    invoke: InvokeOperation = invoke_operation,
    manifest_path: Path | None = None,
    receipt_path: Path | None = None,
    lock_path: Path | None = None,
) -> dict[str, Any]:
    root = repository_root.resolve()
    validate_design()
    controls = _validate_control_set(root)
    config = bridge_config or load_bridge_config(root)
    generation_attempt_id = _generation_attempt_id()
    manifest_target = manifest_path or root / (
        "campaigns/armindex-multiretriever-v2/manifests/"
        "a2-five-arm-candidate-manifest.v1.json"
    )
    receipt_target = receipt_path or root / (
        "campaigns/armindex-multiretriever-v2/evidence/"
        "a2-five-arm-candidate-freeze.receipt.v1.json"
    )
    lock_target = lock_path or config.freeze_lock
    if any(path.exists() for path in (manifest_target, receipt_target, lock_target)):
        raise A2CandidateFreezeError("candidate freeze artifacts are write-once")
    bindings = _frozen_bindings(root, controls)
    source_commit, source_tree = _git_identity(root)
    append_preparation_ledger_event(
        root,
        generation_attempt_id=generation_attempt_id,
        event_type="candidate_generation_start",
        status="active",
        summary="Started Official proposer/reviewer generation for the frozen 52-candidate universe.",
        evidence={
            "source_commit": source_commit,
            "source_tree": source_tree,
            "candidate_count": 52,
            "matched_candidate_count": 40,
            "conditional_reserve_candidate_count": 12,
        },
    )
    candidates: list[dict[str, Any]] = []
    batches: list[dict[str, Any]] = []
    try:
        for spec in build_batch_specs():
            records, batch = _generate_batch(
                root,
                config,
                spec,
                bindings,
                generation_attempt_id,
                invoke,
            )
            candidates.extend(records)
            batches.append(batch)
            append_preparation_ledger_event(
                root,
                generation_attempt_id=generation_attempt_id,
                event_type="candidate_batch_accepted",
                status="passed",
                summary=f"Accepted and compile-twice verified batch {spec.batch_id} before measurement.",
                evidence={
                    "batch_id": spec.batch_id,
                    "batch_sha256": batch["batch_sha256"],
                    "candidate_count": 4,
                    "proposer_event_sha256": batch["proposer_event_sha256"],
                    "reviewer_event_sha256": batch["reviewer_event_sha256"],
                },
            )
    except Exception as exc:
        append_preparation_ledger_event(
            root,
            generation_attempt_id=generation_attempt_id,
            event_type="candidate_generation_failure",
            status="repair_required",
            summary="Candidate generation stopped for bounded engineering repair before freeze.",
            evidence={"failure_type": type(exc).__name__},
        )
        raise
    candidates.sort(key=lambda item: str(item["candidate_id"]))
    batches.sort(key=lambda item: str(item["batch_id"]))
    payload_hashes = [str(item["scientific_payload_sha256"]) for item in candidates]
    if len(candidates) != 52 or len(payload_hashes) != len(set(payload_hashes)):
        raise A2CandidateFreezeError("candidate universe is incomplete or duplicated")
    design = validate_design()
    manifest: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "manifest_id": "a2-five-arm-candidate-manifest-v1",
        "campaign_id": CAMPAIGN_ID,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "revision_id": REVISION_ID,
        "generation_attempt_id": generation_attempt_id,
        "status": "frozen_before_measurement",
        "seed": SEED,
        "design": design,
        "bindings": {
            **bindings,
            "bridge_config_sha256": _load_json(config.config_path)["config_sha256"],
            "compiler_sha256": file_sha256(root / "src/myis_research/armindex/compiler.py"),
            "verifier_sha256": file_sha256(Path(__file__)),
            "manifest_schema_sha256": file_sha256(
                root / "schemas/armindex/a2-candidate-manifest.v1.json"
            ),
            "freeze_receipt_schema_sha256": file_sha256(
                root / "schemas/armindex/a2-candidate-freeze-receipt.v1.json"
            ),
            "freeze_lock_schema_sha256": file_sha256(
                root / "schemas/armindex/a2-candidate-freeze-lock.v1.json"
            ),
            "source_commit": source_commit,
            "source_tree": source_tree,
        },
        "candidate_count": 52,
        "matched_candidate_count": 40,
        "conditional_reserve_candidate_count": 12,
        "candidate_ids_sha256": canonical_sha256(
            [item["candidate_id"] for item in candidates]
        ),
        "scientific_payload_set_sha256": canonical_sha256(sorted(payload_hashes)),
        "batches": batches,
        "candidates": candidates,
        "official_call_binding_count": len(batches) * 2,
        "protected_data_accessed": False,
        "rep_dev_accessed_for_measurement": False,
        "measured_execution_performed": False,
        "gpu_work_performed": False,
        "provider_admission_performed": False,
        "provider_execution_adoption_performed": False,
    }
    manifest["manifest_sha256"] = canonical_sha256(manifest)
    _validate_schema(
        manifest, root / "schemas/armindex/a2-candidate-manifest.v1.json"
    )
    lock: dict[str, Any] = {
        "schema_version": FREEZE_LOCK_SCHEMA_VERSION,
        "lock_id": "a2-five-arm-candidate-freeze-lock-v1",
        "campaign_id": CAMPAIGN_ID,
        "revision_id": REVISION_ID,
        "manifest_sha256": manifest["manifest_sha256"],
        "candidate_count": 52,
        "locked_operations": ["representation_propose", "representation_review"],
        "mutation_policy": "new_campaign_revision_required_no_reinterpretation",
        "created_at": _utc_now(),
        "measured_execution_performed": False,
    }
    lock["lock_sha256"] = canonical_sha256(lock)
    receipt: dict[str, Any] = {
        "schema_version": FREEZE_RECEIPT_SCHEMA_VERSION,
        "receipt_id": "a2-five-arm-candidate-freeze-v1",
        "campaign_id": CAMPAIGN_ID,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "revision_id": REVISION_ID,
        "generation_attempt_id": generation_attempt_id,
        "status": "PASS_FIVE_ARM_CANDIDATE_FREEZE",
        "manifest_sha256": manifest["manifest_sha256"],
        "manifest_file_sha256": _canonical_file_sha256(manifest),
        "lock_sha256": lock["lock_sha256"],
        "candidate_count": 52,
        "matched_candidate_count": 40,
        "conditional_reserve_candidate_count": 12,
        "accepted_candidate_count": 52,
        "compile_twice_candidate_count": 52,
        "diagnostic_non_advancing_arms": list(DIAGNOSTIC_NON_ADVANCING_ARMS),
        "primary_advancement_arms": list(PRIMARY_ADVANCEMENT_ARMS),
        "official_model": "gpt-5.6-sol",
        "official_reasoning_effort": "high",
        "official_sdk_version": "0.144.4",
        "official_cli_version": "0.144.4",
        "official_provider": "openai",
        "source_commit": source_commit,
        "source_tree": source_tree,
        "protected_data_accessed": False,
        "rep_dev_accessed_for_measurement": False,
        "measured_a2_started": False,
        "gpu_work_performed": False,
        "provider_admission_performed": False,
        "provider_execution_adoption_performed": False,
        "selection_accesses": 0,
        "final_accesses": 0,
        "harness_dev_accesses": 0,
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    _validate_schema(
        receipt,
        root / "schemas/armindex/a2-candidate-freeze-receipt.v1.json",
    )
    _validate_schema(
        lock,
        root / "schemas/armindex/a2-candidate-freeze-lock.v1.json",
    )
    _write_once(manifest_target, manifest)
    _write_once(receipt_target, receipt)
    _write_once(lock_target, lock)
    replay = validate_candidate_freeze(
        root,
        manifest_path=manifest_target,
        receipt_path=receipt_target,
        lock_path=lock_target,
    )
    append_preparation_ledger_event(
        root,
        generation_attempt_id=generation_attempt_id,
        event_type="candidate_freeze_closeout",
        status="complete_auditor_review_required",
        summary="Frozen the complete five-arm candidate universe and stopped before measured A2.",
        evidence={
            "manifest_sha256": manifest["manifest_sha256"],
            "receipt_sha256": receipt["receipt_sha256"],
            "lock_sha256": lock["lock_sha256"],
            "candidate_count": 52,
        },
    )
    return {
        "status": replay["status"],
        "manifest_sha256": manifest["manifest_sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "lock_sha256": lock["lock_sha256"],
        "candidate_count": 52,
        "matched_candidate_count": 40,
        "conditional_reserve_candidate_count": 12,
        "measured_a2_started": False,
    }


def validate_candidate_freeze(
    repository_root: Path,
    *,
    manifest_path: Path | None = None,
    receipt_path: Path | None = None,
    lock_path: Path | None = None,
) -> dict[str, Any]:
    root = repository_root.resolve()
    manifest_target = manifest_path or root / (
        "campaigns/armindex-multiretriever-v2/manifests/"
        "a2-five-arm-candidate-manifest.v1.json"
    )
    receipt_target = receipt_path or root / (
        "campaigns/armindex-multiretriever-v2/evidence/"
        "a2-five-arm-candidate-freeze.receipt.v1.json"
    )
    lock_target = lock_path or root / "control/armindex/a2/candidate-freeze.lock.v1.json"
    manifest = _load_json(manifest_target)
    receipt = _load_json(receipt_target)
    lock = _load_json(lock_target)
    _validate_schema(
        manifest, root / "schemas/armindex/a2-candidate-manifest.v1.json"
    )
    _validate_schema(
        receipt,
        root / "schemas/armindex/a2-candidate-freeze-receipt.v1.json",
    )
    _validate_schema(
        lock,
        root / "schemas/armindex/a2-candidate-freeze-lock.v1.json",
    )
    if canonical_sha256({k: v for k, v in manifest.items() if k != "manifest_sha256"}) != manifest.get(
        "manifest_sha256"
    ):
        raise A2CandidateFreezeError("candidate manifest self-hash mismatch")
    if canonical_sha256({k: v for k, v in receipt.items() if k != "receipt_sha256"}) != receipt.get(
        "receipt_sha256"
    ):
        raise A2CandidateFreezeError("candidate freeze receipt self-hash mismatch")
    if canonical_sha256({k: v for k, v in lock.items() if k != "lock_sha256"}) != lock.get(
        "lock_sha256"
    ):
        raise A2CandidateFreezeError("candidate freeze lock self-hash mismatch")
    if receipt.get("manifest_sha256") != manifest.get("manifest_sha256"):
        raise A2CandidateFreezeError("freeze receipt manifest binding mismatch")
    if receipt.get("lock_sha256") != lock.get("lock_sha256"):
        raise A2CandidateFreezeError("freeze receipt lock binding mismatch")
    if receipt.get("manifest_file_sha256") != file_sha256(manifest_target):
        raise A2CandidateFreezeError("freeze receipt manifest file binding mismatch")
    if receipt.get("generation_attempt_id") != manifest.get("generation_attempt_id"):
        raise A2CandidateFreezeError("freeze generation attempt binding mismatch")
    if receipt.get("primary_advancement_arms") != list(PRIMARY_ADVANCEMENT_ARMS):
        raise A2CandidateFreezeError("freeze primary-arm order changed")
    if receipt.get("diagnostic_non_advancing_arms") != list(DIAGNOSTIC_NON_ADVANCING_ARMS):
        raise A2CandidateFreezeError("freeze diagnostic-arm order changed")
    candidates = manifest.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 52:
        raise A2CandidateFreezeError("manifest candidate count mismatch")
    matched = [item for item in candidates if item.get("tier") == "matched"]
    reserve = [item for item in candidates if item.get("tier") == "conditional_reserve"]
    if len(matched) != 40 or len(reserve) != 12:
        raise A2CandidateFreezeError("manifest 40+12 count mismatch")
    by_arm = {arm_id: [item for item in matched if item.get("arm_id") == arm_id] for arm_id in ARMS}
    if any(len(items) != 8 for items in by_arm.values()):
        raise A2CandidateFreezeError("matched tier is not 8 candidates per arm")
    if {item.get("arm_id") for item in reserve} != set(PRIMARY_ADVANCEMENT_ARMS):
        raise A2CandidateFreezeError("reserve candidates are not limited to primary arms")
    for arm_id in PRIMARY_ADVANCEMENT_ARMS:
        if len([item for item in reserve if item.get("arm_id") == arm_id]) != 4:
            raise A2CandidateFreezeError("reserve tier is not 4 candidates per primary arm")
    for item in candidates:
        if item.get("arm_id") in DIAGNOSTIC_NON_ADVANCING_ARMS and (
            item.get("advancement_eligible") is not False
            or item.get("diagnostic_non_advancing") is not True
        ):
            raise A2CandidateFreezeError(
                "diagnostic candidate gained advancement authority"
            )
        if item.get("tier") == "conditional_reserve" and item.get("lifecycle") != "dormant_conditional":
            raise A2CandidateFreezeError("reserve candidate is not dormant")
        compile_hashes = item.get("compile_sha256s")
        if (
            not isinstance(compile_hashes, list)
            or len(compile_hashes) != 2
            or compile_hashes[0] != compile_hashes[1]
            or compile_hashes[0] != item.get("compiled_sha256")
        ):
            raise A2CandidateFreezeError("candidate compile-twice binding mismatch")
        program = item.get("program")
        if not isinstance(program, dict):
            raise A2CandidateFreezeError("candidate program missing during replay")
        replay = compile_program(program, _synthetic_documents(program))
        if replay.compiled_representation_sha256 != item.get("compiled_sha256"):
            raise A2CandidateFreezeError("candidate deterministic replay changed")
    ids = [str(item["candidate_id"]) for item in candidates]
    payloads = [str(item["scientific_payload_sha256"]) for item in candidates]
    if len(ids) != len(set(ids)) or len(payloads) != len(set(payloads)):
        raise A2CandidateFreezeError("candidate IDs or payload hashes are duplicated")
    if manifest.get("candidate_ids_sha256") != canonical_sha256(ids):
        raise A2CandidateFreezeError("candidate ID set hash mismatch")
    if manifest.get("scientific_payload_set_sha256") != canonical_sha256(sorted(payloads)):
        raise A2CandidateFreezeError("scientific payload set hash mismatch")
    for key in (
        "protected_data_accessed",
        "rep_dev_accessed_for_measurement",
        "measured_execution_performed",
        "gpu_work_performed",
        "provider_admission_performed",
        "provider_execution_adoption_performed",
    ):
        if manifest.get(key) is not False:
            raise A2CandidateFreezeError(f"manifest safety flag changed: {key}")
    if receipt.get("measured_a2_started") is not False:
        raise A2CandidateFreezeError("freeze receipt claims measured A2 started")
    return {
        "status": "PASS_A2_CANDIDATE_FREEZE_REPLAY",
        "candidate_count": 52,
        "matched_candidate_count": 40,
        "conditional_reserve_candidate_count": 12,
        "manifest_sha256": manifest["manifest_sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "lock_sha256": lock["lock_sha256"],
        "measured_a2_started": False,
    }


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("design", "generate-freeze", "validate-freeze"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--repository-root", type=Path, default=Path.cwd())
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.command == "design":
        result = {"status": "PASS_A2_FIVE_ARM_DESIGN", **validate_design()}
    elif args.command == "generate-freeze":
        result = generate_and_freeze(args.repository_root)
    else:
        result = validate_candidate_freeze(args.repository_root)
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
