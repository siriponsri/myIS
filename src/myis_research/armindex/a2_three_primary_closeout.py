"""Additive closeout and audit for the Owner-approved three-primary A2 route."""

from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a2_execution_readiness import build_winner_receipt, frozen_candidates
from .a2_measured_adapter import canonical_a1_incumbents


_ATTEMPT = "a2-goal004-20260816-005"
_PRIMARY_ARMS = ("ARM-03", "ARM-05", "ARM-04")
_PRIMARY_ARM_KEYS = ("ARM-03", "ARM-04", "ARM-05")
_DIAGNOSTIC_ARMS = ("ARM-01", "ARM-02")
_FROZEN_BINDINGS = {
    "manifest_sha256": "f6276e3a15e760187152270418e00ce4cae4d8efe45b13edb02c4742e3b3049e",
    "freeze_receipt_sha256": "ea93db368c3e740f7914e07e2bdfc15052991f6f05976f6924acdce717392e10",
    "lock_sha256": "c01f683b909e6f4c6310c01855b3f79319a183b7950f91338d43baa8a2d57952",
}
_HASH_LENGTH = 64


class A2ThreePrimaryCloseoutError(ValueError):
    """The amended closeout cannot prove its aggregate-safe lineage."""


def _load(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise A2ThreePrimaryCloseoutError(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise A2ThreePrimaryCloseoutError(f"{role} must be an object")
    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise A2ThreePrimaryCloseoutError(f"{role} contains raw or protected content") from error
    return value


def _schema(root: Path, name: str, value: Mapping[str, Any], *, role: str) -> None:
    schema = _load(root / "schemas" / "armindex" / name, role=f"{role} schema")
    errors = sorted(Draft202012Validator(schema).iter_errors(dict(value)), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        at = ".".join(str(part) for part in error.path) or "<root>"
        raise A2ThreePrimaryCloseoutError(f"{role} does not satisfy its schema at {at}: {error.message}")


def _hash(value: object, *, role: str) -> str:
    if not isinstance(value, str) or len(value) != _HASH_LENGTH or any(char not in "0123456789abcdef" for char in value):
        raise A2ThreePrimaryCloseoutError(f"{role} hash is invalid")
    return value


def _self_hash(value: Mapping[str, Any], field: str, *, role: str) -> str:
    expected = _hash(value.get(field), role=role)
    actual = canonical_sha256({key: item for key, item in value.items() if key != field})
    if expected != actual:
        raise A2ThreePrimaryCloseoutError(f"{role} self-hash drift")
    return actual


def _decimal(value: object, *, role: str) -> Decimal:
    if not isinstance(value, str):
        raise A2ThreePrimaryCloseoutError(f"{role} is not a decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise A2ThreePrimaryCloseoutError(f"{role} is invalid") from error
    if not parsed.is_finite():
        raise A2ThreePrimaryCloseoutError(f"{role} is non-finite")
    return parsed


def _validate_amendment(repository_root: Path, amendment: Mapping[str, Any]) -> dict[str, Any]:
    root = repository_root.resolve()
    value = dict(amendment)
    _schema(root, "a2-goal004-three-primary-amendment.v1.json", value, role="amendment")
    _self_hash(value, "amendment_sha256", role="amendment")
    if value["frozen_a2_bindings"] != _FROZEN_BINDINGS:
        raise A2ThreePrimaryCloseoutError("amendment changes frozen A2 bindings")
    approval_hash = canonical_sha256({"owner_approval_text": value["owner_approval_text"]})
    if value["owner_approval_sha256"] != approval_hash:
        raise A2ThreePrimaryCloseoutError("amendment Owner approval hash drift")
    authority = _load(root / value["superseded_for_execution_only"]["a3_five_arm_authority_uri"], role="five-arm authority")
    manifest = _load(root / value["superseded_for_execution_only"]["a3_five_arm_manifest_uri"], role="five-arm manifest")
    if authority.get("authority_sha256") != value["superseded_for_execution_only"]["a3_five_arm_authority_sha256"]:
        raise A2ThreePrimaryCloseoutError("five-arm authority binding drift")
    if manifest.get("manifest_sha256") != value["superseded_for_execution_only"]["a3_five_arm_manifest_sha256"]:
        raise A2ThreePrimaryCloseoutError("five-arm manifest binding drift")
    return value


def _validate_candidate_receipt(
    root: Path,
    receipt: Mapping[str, Any],
    *,
    candidate_id: str,
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    value = dict(receipt)
    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise A2ThreePrimaryCloseoutError("candidate receipt contains protected content") from error
    _schema(root, "a2-candidate-result-receipt.v1.json", value, role="candidate receipt")
    _self_hash(value, "receipt_sha256", role="candidate receipt")
    if (
        value.get("attempt_id") != _ATTEMPT
        or value.get("candidate_id") != candidate_id
        or value.get("arm_id") != candidate.get("arm_id")
        or value.get("freeze_bindings") != _FROZEN_BINDINGS
    ):
        raise A2ThreePrimaryCloseoutError("candidate receipt identity or freeze binding drift")
    reserve = candidate.get("tier") == "conditional_reserve"
    if reserve and value.get("status") == "DORMANT_CONDITIONAL_RESERVE":
        if value.get("reserve_activation_passed") is not False:
            raise A2ThreePrimaryCloseoutError("dormant reserve activation drift")
    elif value.get("status") != "PASS_A2_CANDIDATE_RESULT":
        raise A2ThreePrimaryCloseoutError("active candidate lacks a PASS result")
    return value


def _diagnostic_no_winner_receipt(
    repository_root: Path,
    *,
    arm_id: str,
    top_score: Decimal,
    tied_receipts: list[Mapping[str, Any]],
) -> dict[str, Any]:
    root = repository_root.resolve()
    hashes = sorted(_self_hash(item, "receipt_sha256", role="tied candidate receipt") for item in tied_receipts)
    body = {
        "schema_version": "myis.armindex-a2-diagnostic-no-winner-receipt.v1",
        "receipt_id": f"{_ATTEMPT}-{arm_id.lower()}-diagnostic-no-winner-v1",
        "attempt_id": _ATTEMPT,
        "status": "PASS_A2_DIAGNOSTIC_NO_WINNER_TIE",
        "arm_id": arm_id,
        "primary_metric_name": "recall_at_100/out",
        "top_primary_metric_value": str(top_score),
        "top_tie_count": len(tied_receipts),
        "top_candidate_result_receipt_sha256s": hashes,
        "diagnostic_non_advancing": True,
        "advancement_eligible": False,
        "strict_tie_rejected": True,
        "freeze_bindings": _FROZEN_BINDINGS,
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _schema(root, "a2-diagnostic-no-winner-receipt.v1.json", receipt, role="diagnostic no-winner receipt")
    return receipt


def build_three_primary_coverage(
    repository_root: Path,
    *,
    receipts_by_candidate: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate all frozen receipts without weakening the original five-arm evaluator."""

    root = repository_root.resolve()
    candidates = frozen_candidates(root)
    if set(receipts_by_candidate) != set(candidates):
        raise A2ThreePrimaryCloseoutError("candidate receipts must cover all 52 frozen IDs")
    checked: dict[str, dict[str, Any]] = {}
    for candidate_id, candidate in candidates.items():
        checked[candidate_id] = _validate_candidate_receipt(
            root, receipts_by_candidate[candidate_id], candidate_id=candidate_id, candidate=candidate
        )
    measured = [receipt for receipt in checked.values() if receipt["status"] == "PASS_A2_CANDIDATE_RESULT"]
    dormant = [receipt for receipt in checked.values() if receipt["status"] == "DORMANT_CONDITIONAL_RESERVE"]
    if (len(measured), len(dormant)) != (44, 8):
        raise A2ThreePrimaryCloseoutError("candidate receipts do not prove exact 44 measured and 8 dormant accounting")
    for arm_id in _PRIMARY_ARMS:
        reserves = [
            checked[candidate_id]
            for candidate_id, candidate in candidates.items()
            if candidate["arm_id"] == arm_id and candidate["tier"] == "conditional_reserve"
        ]
        statuses = {receipt["status"] for receipt in reserves}
        decisions = {receipt["reserve_activation_evidence_sha256"] for receipt in reserves}
        if len(reserves) != 4 or len(statuses) != 1 or len(decisions) != 1:
            raise A2ThreePrimaryCloseoutError("primary-arm reserve quartet provenance drift")
    winners: dict[str, dict[str, Any]] = {}
    diagnostics: dict[str, dict[str, Any]] = {}
    proofs: dict[str, dict[str, Any]] = {}
    incumbents = canonical_a1_incumbents(root)
    for arm_id in (*_DIAGNOSTIC_ARMS, *_PRIMARY_ARMS):
        scored = [
            ( _decimal(receipt["primary_metric"]["value"], role="primary metric"), candidate_id, receipt)
            for candidate_id, receipt in checked.items()
            if candidates[candidate_id]["arm_id"] == arm_id and receipt["status"] == "PASS_A2_CANDIDATE_RESULT"
        ]
        if not scored:
            raise A2ThreePrimaryCloseoutError("arm has no measured candidate result")
        top_score = max(item[0] for item in scored)
        top = [(candidate_id, receipt) for score, candidate_id, receipt in scored if score == top_score]
        if arm_id in _DIAGNOSTIC_ARMS:
            if len(top) < 2:
                raise A2ThreePrimaryCloseoutError("diagnostic arm must retain an exact primary-score tie")
            diagnostics[arm_id] = _diagnostic_no_winner_receipt(
                root, arm_id=arm_id, top_score=top_score, tied_receipts=[receipt for _, receipt in top]
            )
            continue
        if len(top) != 1:
            raise A2ThreePrimaryCloseoutError("primary arm must have one unique top candidate")
        winner_id, winner_result = top[0]
        incumbent = incumbents[arm_id]
        incumbent_score = _decimal(incumbent["primary_metric"], role="frozen A1 incumbent metric")
        winners[arm_id] = build_winner_receipt(
            root,
            attempt_id=_ATTEMPT,
            arm_id=arm_id,
            winner_candidate_id=winner_id,
            train_evaluation_receipt_sha256=winner_result["receipt_sha256"],
            strict_tie_rejected=True,
        )
        proofs[arm_id] = {
            "winner_candidate_id": winner_id,
            "winner_primary_metric": str(top_score),
            "frozen_a1_incumbent_candidate_id": incumbent["candidate_id"],
            "frozen_a1_primary_metric": str(incumbent_score),
            "strict_primary_improvement": top_score > incumbent_score,
            "a1_comparison": (
                "STRICT_IMPROVEMENT" if top_score > incumbent_score else "NO_STRICT_IMPROVEMENT"
            ),
        }
    if set(winners) != set(_PRIMARY_ARM_KEYS) or set(diagnostics) != set(_DIAGNOSTIC_ARMS):
        raise A2ThreePrimaryCloseoutError("three-primary arm disposition is incomplete")
    body = {
        "schema_version": "myis.armindex-a2-three-primary-coverage-receipt.v1",
        "receipt_id": f"{_ATTEMPT}-three-primary-coverage-v1",
        "attempt_id": _ATTEMPT,
        "status": "PASS_A2_THREE_PRIMARY_EXACT_COVERAGE",
        "candidate_count": 52,
        "matched_candidate_count": 40,
        "conditional_reserve_candidate_count": 12,
        "measured_candidate_count": 44,
        "dormant_conditional_reserve_count": 8,
        "failed_candidate_count": 0,
        "candidate_result_set_sha256": canonical_sha256(sorted(item["receipt_sha256"] for item in checked.values())),
        "primary_winner_receipts": winners,
        "diagnostic_no_winner_receipts": diagnostics,
        "primary_improvement_proofs": proofs,
        "freeze_bindings": _FROZEN_BINDINGS,
    }
    coverage = {**body, "coverage_sha256": canonical_sha256(body)}
    _schema(root, "a2-three-primary-coverage-receipt.v1.json", coverage, role="three-primary coverage")
    _validate_coverage(root, coverage, expect_proofs=proofs)
    return coverage


def _validate_coverage(
    root: Path, coverage: Mapping[str, Any], *, expect_proofs: Mapping[str, Any] | None = None
) -> dict[str, dict[str, Any]]:
    value = dict(coverage)
    _schema(root, "a2-three-primary-coverage-receipt.v1.json", value, role="three-primary coverage")
    _self_hash(value, "coverage_sha256", role="three-primary coverage")
    if value["attempt_id"] != _ATTEMPT or value["freeze_bindings"] != _FROZEN_BINDINGS:
        raise A2ThreePrimaryCloseoutError("three-primary coverage attempt or freeze binding drift")
    winners = value["primary_winner_receipts"]
    diagnostics = value["diagnostic_no_winner_receipts"]
    for arm_id in _PRIMARY_ARM_KEYS:
        winner = dict(winners[arm_id])
        _schema(root, "a2-winner-selection-receipt.v1.json", winner, role="primary winner receipt")
        _self_hash(winner, "receipt_sha256", role="primary winner receipt")
        if (winner["arm_id"], winner["attempt_id"], winner["freeze_bindings"], winner["diagnostic_non_advancing"], winner["advancement_eligible"]) != (arm_id, _ATTEMPT, _FROZEN_BINDINGS, False, True):
            raise A2ThreePrimaryCloseoutError("primary winner receipt binding drift")
    for arm_id in _DIAGNOSTIC_ARMS:
        receipt = dict(diagnostics[arm_id])
        _schema(root, "a2-diagnostic-no-winner-receipt.v1.json", receipt, role="diagnostic no-winner receipt")
        _self_hash(receipt, "receipt_sha256", role="diagnostic no-winner receipt")
        if (receipt["arm_id"], receipt["attempt_id"], receipt["freeze_bindings"]) != (arm_id, _ATTEMPT, _FROZEN_BINDINGS):
            raise A2ThreePrimaryCloseoutError("diagnostic no-winner receipt binding drift")
    proofs = value["primary_improvement_proofs"]
    incumbents = canonical_a1_incumbents(root)
    for arm_id in _PRIMARY_ARM_KEYS:
        proof = proofs[arm_id]
        if (
            proof["winner_candidate_id"] != winners[arm_id]["winner_candidate_id"]
            or proof["frozen_a1_incumbent_candidate_id"] != incumbents[arm_id]["candidate_id"]
            or proof["frozen_a1_primary_metric"] != incumbents[arm_id]["primary_metric"]
        ):
            raise A2ThreePrimaryCloseoutError("primary strict-improvement proof drift")
        winner_score = _decimal(proof["winner_primary_metric"], role="winner primary metric")
        incumbent_score = _decimal(proof["frozen_a1_primary_metric"], role="frozen A1 incumbent metric")
        strict = winner_score > incumbent_score
        if proof["strict_primary_improvement"] is not strict or proof["a1_comparison"] != (
            "STRICT_IMPROVEMENT" if strict else "NO_STRICT_IMPROVEMENT"
        ):
            raise A2ThreePrimaryCloseoutError("primary A1 comparison classification drift")
    if expect_proofs is not None and dict(proofs) != dict(expect_proofs):
        raise A2ThreePrimaryCloseoutError("primary strict-improvement proof coverage is incomplete")
    return {arm_id: dict(winners[arm_id]) for arm_id in _PRIMARY_ARM_KEYS}


def build_three_primary_terminal_checkpoint(
    repository_root: Path,
    *,
    amendment: Mapping[str, Any],
    safe_return_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    root = repository_root.resolve()
    checked_amendment = _validate_amendment(root, amendment)
    safe_return = dict(safe_return_receipt)
    _schema(root, "a2-safe-return-receipt.v1.json", safe_return, role="safe-return receipt")
    safe_hash = _self_hash(safe_return, "receipt_sha256", role="safe-return receipt")
    if safe_return.get("attempt_id") != _ATTEMPT or safe_return.get("freeze_bindings") != _FROZEN_BINDINGS or safe_return.get("status") != "PASS_A2_SAFE_RETURN" or safe_return.get("protected_payload_included") is not False:
        raise A2ThreePrimaryCloseoutError("safe-return receipt is not compatible with amended terminal closeout")
    body = {
        "schema_version": "myis.armindex-a2-three-primary-terminal-checkpoint.v1",
        "checkpoint_id": f"{_ATTEMPT}-three-primary-terminal-v1",
        "attempt_id": _ATTEMPT,
        "status": "PASS_A2_THREE_PRIMARY_SAFE_RETURNED",
        "candidate_count": 52,
        "measured_candidate_count": 44,
        "dormant_conditional_reserve_count": 8,
        "failed_candidate_count": 0,
        "safe_return_receipt_sha256": safe_hash,
        "amendment_sha256": checked_amendment["amendment_sha256"],
        "workers_reaped": True,
        "resume_allowed": False,
        "freeze_bindings": _FROZEN_BINDINGS,
    }
    checkpoint = {**body, "checkpoint_sha256": canonical_sha256(body)}
    _schema(root, "a2-three-primary-terminal-checkpoint.v1.json", checkpoint, role="terminal checkpoint")
    return checkpoint


def _require_accounting(summary: Mapping[str, Any]) -> None:
    if summary != {
        "attempt_id": _ATTEMPT,
        "candidate_count": 52,
        "dormant_candidate_count": 8,
        "failure_marker_count": 0,
        "measured_candidate_count": 44,
        "protected_payload_included": False,
        "status": "PASS_A2_AGGREGATE_RETURN_ACCOUNTING",
    }:
        raise A2ThreePrimaryCloseoutError("aggregate accounting summary drift")


def _require_worker_reap(summary: Mapping[str, Any]) -> None:
    required = {
        "attempt_id": _ATTEMPT,
        "candidate_worker_count": 0,
        "protected_payload_included": False,
        "remote_root": f"/opt/myis/{_ATTEMPT}",
        "status": "PASS_A2_WORKERS_REAPED",
        "watchdog_count": 0,
    }
    if summary != required:
        raise A2ThreePrimaryCloseoutError("worker-reap summary drift")


def build_three_primary_closeout(
    repository_root: Path,
    *,
    amendment: Mapping[str, Any],
    coverage: Mapping[str, Any],
    safe_return_receipt: Mapping[str, Any],
    terminal_checkpoint: Mapping[str, Any],
    aggregate_accounting_summary: Mapping[str, Any],
    worker_reap_summary: Mapping[str, Any],
    dormant_repair_manifest_file_sha256: str,
    aggregate_accounting_summary_sha256: str,
    worker_reap_summary_sha256: str,
    budget_cap_summary: Mapping[str, Any],
    budget_cap_summary_sha256: str,
    claim_evidence_pointers: list[str],
) -> dict[str, Any]:
    root = repository_root.resolve()
    checked_amendment = _validate_amendment(root, amendment)
    winners = _validate_coverage(root, coverage)
    _require_accounting(dict(aggregate_accounting_summary))
    _require_worker_reap(dict(worker_reap_summary))
    safe_return = dict(safe_return_receipt)
    terminal = dict(terminal_checkpoint)
    _schema(root, "a2-safe-return-receipt.v1.json", safe_return, role="safe-return receipt")
    _schema(root, "a2-three-primary-terminal-checkpoint.v1.json", terminal, role="terminal checkpoint")
    safe_hash = _self_hash(safe_return, "receipt_sha256", role="safe-return receipt")
    terminal_hash = _self_hash(terminal, "checkpoint_sha256", role="terminal checkpoint")
    if terminal["safe_return_receipt_sha256"] != safe_hash or terminal["amendment_sha256"] != checked_amendment["amendment_sha256"]:
        raise A2ThreePrimaryCloseoutError("terminal checkpoint binding drift")
    budget = dict(budget_cap_summary)
    if (
        budget.get("attempt_id") != _ATTEMPT
        or budget.get("status") != "PASS_A2_BUDGET_WITHIN_CAP"
        or budget.get("protected_payload_included") is not False
        or budget.get("forward_hard_stop_usd") != "60"
        or _decimal(budget.get("whole_workload_total_usd"), role="A2 whole-workload total") > Decimal("60")
    ):
        raise A2ThreePrimaryCloseoutError("A2 budget cap summary does not prove the USD 60 hard stop")
    hashes = {
        "dormant repair manifest": _hash(dormant_repair_manifest_file_sha256, role="dormant repair manifest"),
        "aggregate accounting summary": _hash(aggregate_accounting_summary_sha256, role="aggregate accounting summary"),
        "worker-reap summary": _hash(worker_reap_summary_sha256, role="worker-reap summary"),
        "budget cap summary": _hash(budget_cap_summary_sha256, role="budget cap summary"),
    }
    if not claim_evidence_pointers or any(Path(pointer).is_absolute() or ".." in Path(pointer).parts for pointer in claim_evidence_pointers):
        raise A2ThreePrimaryCloseoutError("claim evidence pointers are unsafe")
    primary_hashes = {arm_id: winners[arm_id]["receipt_sha256"] for arm_id in _PRIMARY_ARM_KEYS}
    diagnostic_hashes = {
        arm_id: coverage["diagnostic_no_winner_receipts"][arm_id]["receipt_sha256"]
        for arm_id in _DIAGNOSTIC_ARMS
    }
    body = {
        "schema_version": "myis.armindex-a2-execution-closeout-receipt.v2",
        "receipt_id": f"{_ATTEMPT}-execution-closeout-v2",
        "attempt_id": _ATTEMPT,
        "status": "PASS_A2_EXECUTION_CLOSEOUT",
        "evidence_class": "measured_development_aggregate",
        "amendment_sha256": checked_amendment["amendment_sha256"],
        "candidate_count": 52,
        "matched_candidate_count": 40,
        "conditional_reserve_candidate_count": 12,
        "measured_candidate_count": 44,
        "dormant_conditional_reserve_count": 8,
        "failed_candidate_count": 0,
        "primary_winner_receipt_sha256s": primary_hashes,
        "diagnostic_no_winner_receipt_sha256s": diagnostic_hashes,
        "primary_improvement_proofs": coverage["primary_improvement_proofs"],
        "candidate_result_set_sha256": coverage["candidate_result_set_sha256"],
        "safe_return_receipt_sha256": safe_hash,
        "terminal_checkpoint_sha256": terminal_hash,
        "aggregate_accounting_summary_sha256": hashes["aggregate accounting summary"],
        "dormant_provenance_repair_manifest_file_sha256": hashes["dormant repair manifest"],
        "worker_reap_summary_sha256": hashes["worker-reap summary"],
        "budget_cap_summary_sha256": hashes["budget cap summary"],
        "whole_workload_total_usd": budget["whole_workload_total_usd"],
        "forward_hard_stop_usd": "60",
        "workers_reaped": True,
        "protected_scan_passed": True,
        "diagnostic_non_advancing_arms": ["ARM-01", "ARM-02"],
        "primary_advancement_arms": ["ARM-03", "ARM-05", "ARM-04"],
        "claim_evidence_pointers": claim_evidence_pointers,
        "freeze_bindings": _FROZEN_BINDINGS,
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _schema(root, "a2-execution-closeout-receipt.v2.json", receipt, role="three-primary closeout")
    return receipt


def _relative_uri(owner_root: Path, path: Path, *, role: str) -> str:
    try:
        resolved = path.resolve(strict=True)
        relative = resolved.relative_to(owner_root.resolve(strict=True))
    except (OSError, ValueError) as error:
        raise A2ThreePrimaryCloseoutError(f"{role} must stay in the Owner-local attempt root") from error
    if path.is_symlink() or not resolved.is_file():
        raise A2ThreePrimaryCloseoutError(f"{role} is unsafe")
    return relative.as_posix()


def _validate_dormant_repair(value: Mapping[str, Any]) -> None:
    if (
        value.get("attempt_id") != _ATTEMPT
        or value.get("status") != "PASS_A2_DORMANT_PROVENANCE_FIX_FORWARD"
        or value.get("active_receipt_count") != 44
        or value.get("dormant_receipt_count") != 8
        or value.get("protected_payload_included") is not False
        or not isinstance(value.get("dormant_receipt_repairs"), list)
        or len(value["dormant_receipt_repairs"]) != 8
        or value.get("repair_manifest_sha256")
        != canonical_sha256({key: item for key, item in value.items() if key != "repair_manifest_sha256"})
    ):
        raise A2ThreePrimaryCloseoutError("dormant provenance repair manifest drift")


def audit_three_primary_closeout(
    repository_root: Path,
    *,
    owner_attempt_root: Path,
    amendment_path: Path,
    closeout_path: Path,
    coverage_path: Path,
    safe_return_path: Path,
    terminal_checkpoint_path: Path,
    aggregate_accounting_summary_path: Path,
    worker_reap_summary_path: Path,
    budget_cap_summary_path: Path,
    dormant_repair_manifest_path: Path,
) -> dict[str, Any]:
    """Independently audit all receipt-bound facts required for A3 admission."""

    root = repository_root.resolve()
    owner_root = owner_attempt_root.resolve(strict=True)
    paths = {
        "closeout": closeout_path,
        "coverage": coverage_path,
        "safe_return": safe_return_path,
        "terminal_checkpoint": terminal_checkpoint_path,
        "aggregate_accounting": aggregate_accounting_summary_path,
        "worker_reap": worker_reap_summary_path,
        "budget_cap": budget_cap_summary_path,
        "dormant_repair": dormant_repair_manifest_path,
    }
    uris = {role: _relative_uri(owner_root, path, role=role) for role, path in paths.items()}
    amendment = _validate_amendment(root, _load(amendment_path, role="amendment"))
    closeout = _load(closeout_path, role="closeout receipt")
    coverage = _load(coverage_path, role="coverage receipt")
    safe_return = _load(safe_return_path, role="safe-return receipt")
    terminal = _load(terminal_checkpoint_path, role="terminal checkpoint")
    accounting = _load(aggregate_accounting_summary_path, role="aggregate accounting summary")
    workers = _load(worker_reap_summary_path, role="worker-reap summary")
    budget = _load(budget_cap_summary_path, role="budget cap summary")
    dormant_repair = _load(dormant_repair_manifest_path, role="dormant-repair manifest")
    _schema(root, "a2-execution-closeout-receipt.v2.json", closeout, role="closeout receipt")
    _schema(root, "a2-three-primary-terminal-checkpoint.v1.json", terminal, role="terminal checkpoint")
    closeout_hash = _self_hash(closeout, "receipt_sha256", role="closeout receipt")
    coverage_hash = _self_hash(coverage, "coverage_sha256", role="coverage receipt")
    safe_return_hash = _self_hash(safe_return, "receipt_sha256", role="safe-return receipt")
    checkpoint_hash = _self_hash(terminal, "checkpoint_sha256", role="terminal checkpoint")
    winners = _validate_coverage(root, coverage)
    _require_accounting(accounting)
    _require_worker_reap(workers)
    _validate_dormant_repair(dormant_repair)
    if (
        closeout["amendment_sha256"] != amendment["amendment_sha256"]
        or closeout["candidate_result_set_sha256"] != coverage["candidate_result_set_sha256"]
        or closeout["safe_return_receipt_sha256"] != safe_return_hash
        or closeout["terminal_checkpoint_sha256"] != checkpoint_hash
        or terminal["safe_return_receipt_sha256"] != safe_return_hash
        or terminal["amendment_sha256"] != amendment["amendment_sha256"]
        or closeout["primary_winner_receipt_sha256s"]
        != {arm_id: winners[arm_id]["receipt_sha256"] for arm_id in _PRIMARY_ARM_KEYS}
        or closeout["diagnostic_no_winner_receipt_sha256s"]
        != {arm_id: coverage["diagnostic_no_winner_receipts"][arm_id]["receipt_sha256"] for arm_id in _DIAGNOSTIC_ARMS}
        or closeout["primary_improvement_proofs"] != coverage["primary_improvement_proofs"]
    ):
        raise A2ThreePrimaryCloseoutError("closeout receipt binding drift")
    expected_file_hashes = {
        "aggregate_accounting_summary_sha256": file_sha256(aggregate_accounting_summary_path),
        "worker_reap_summary_sha256": file_sha256(worker_reap_summary_path),
        "budget_cap_summary_sha256": file_sha256(budget_cap_summary_path),
        "dormant_provenance_repair_manifest_file_sha256": file_sha256(dormant_repair_manifest_path),
    }
    if any(closeout[key] != value for key, value in expected_file_hashes.items()):
        raise A2ThreePrimaryCloseoutError("closeout external summary hash drift")
    if (
        budget.get("attempt_id") != _ATTEMPT
        or budget.get("status") != "PASS_A2_BUDGET_WITHIN_CAP"
        or budget.get("forward_hard_stop_usd") != "60"
        or budget.get("whole_workload_total_usd") != closeout["whole_workload_total_usd"]
        or _decimal(closeout["whole_workload_total_usd"], role="A2 whole-workload total") > Decimal("60")
    ):
        raise A2ThreePrimaryCloseoutError("A2 budget evidence drift")
    body = {
        "schema_version": "myis.armindex-a2-result-integrity-audit.v2",
        "audit_id": f"{_ATTEMPT}-result-integrity-audit-v2",
        "status": "PASS_A2_RESULT_INTEGRITY",
        "evidence_class": "measured_development_aggregate_result_audit",
        "scientific_authority": False,
        "claim_boundary": "Aggregate-only integrity audit for the Owner-approved three-primary amendment. It validates receipt lineage and supports no per-query, protected-membership, or publication performance claim by itself.",
        "amendment_sha256": amendment["amendment_sha256"],
        "closeout": {"uri": uris["closeout"], "file_sha256": file_sha256(closeout_path), "receipt_sha256": closeout_hash},
        "coverage": {"uri": uris["coverage"], "file_sha256": file_sha256(coverage_path), "receipt_sha256": coverage_hash},
        "safe_return": {"uri": uris["safe_return"], "file_sha256": file_sha256(safe_return_path), "receipt_sha256": safe_return_hash},
        "terminal_checkpoint": {"uri": uris["terminal_checkpoint"], "file_sha256": file_sha256(terminal_checkpoint_path), "receipt_sha256": checkpoint_hash},
        "protection": {"aggregate_only_scan_passed": True, "raw_or_protected_content_observed": False},
    }
    audit = {**body, "audit_sha256": canonical_sha256(body)}
    _schema(root, "a2-result-integrity-audit.v2.json", audit, role="result-integrity audit")
    return audit


__all__ = [
    "A2ThreePrimaryCloseoutError",
    "build_three_primary_closeout",
    "build_three_primary_coverage",
    "build_three_primary_terminal_checkpoint",
    "audit_three_primary_closeout",
]
