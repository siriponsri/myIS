"""Non-executable DAPFAM reproduction command scaffold.

This module intentionally has no dataset, qrels, provider, MLflow, or harness
executor imports. A future executor requires separate Owner-approved work.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import subprocess

import yaml

from .drafts import DRAFT_RUNSPEC_SCHEMA, DraftValidationError, load_draft_document
from .dapfam_contracts import sha256_payload, validate_owner_value_batch
from .f1_baselines import FrozenF1RunSpecV1, validate_frozen_f1_runspec


WAITING_GATE_EXIT_CODE = 2
HANDOFF_READY_EXIT_CODE = 3


def reproduce_dapfam(
    *,
    repository_root: Path,
    manifest: Path | None,
    validate_draft: bool,
    owner_batch: Path | None = None,
    g1_decision: Path | None = None,
    frozen_runspec: Path | None = None,
) -> dict[str, object]:
    """Return a fail-closed F1/G1 preparation result without executing anything."""

    result: dict[str, object] = {
        "status": "WAITING_GATE",
        "gate": "G1",
        "gate_status": "pending",
        "reason": "G1_REPRODUCTION_APPROVAL_REQUIRED",
        "executor_available": False,
        "scientific_run": False,
        "dataset_access": "none",
        "network_access": "none",
        "provider_access": "none",
        "gpu_access": "none",
        "mlflow_access": "none",
        "artifact_count": 0,
        "scientific_metric_count": 0,
    }
    # A normal invocation refuses before opening a caller-supplied path. The
    # explicit dry-run/validation mode is limited to checked-in planning files.
    if validate_draft:
        if manifest is None:
            raise DraftValidationError("--manifest is required for draft validation")
        result["draft_validation"] = load_draft_document(
            manifest,
            template_root=repository_root / "campaigns" / "scope-autoindex-v1" / "specs",
            expected_schema=DRAFT_RUNSPEC_SCHEMA,
        )
        return result
    supplied = (owner_batch, g1_decision, frozen_runspec)
    if any(supplied) and not all(supplied):
        return {**result, "status": "BLOCKED", "reason": "G1_HANDOFF_INPUTS_INCOMPLETE"}
    if all(supplied):
        decision = _validate_g1_decision(repository_root, g1_decision)  # type: ignore[arg-type]
        runspec, runspec_sha = _validate_frozen_runspec(repository_root, frozen_runspec, decision)  # type: ignore[arg-type]
        batch_path = owner_batch.resolve(strict=True)  # type: ignore[union-attr]
        if batch_path.is_symlink() or not batch_path.is_file():
            raise DraftValidationError("Owner-value batch must be a regular file")
        batch = validate_owner_value_batch(json.loads(batch_path.read_text(encoding="utf-8")))
        batch_sha = hashlib.sha256(batch_path.read_bytes()).hexdigest()
        evidence_hashes = decision.get("evidence_manifest_hashes", [])
        if batch_sha not in evidence_hashes or runspec_sha not in evidence_hashes:
            raise DraftValidationError("G1 decision must bind the Owner-value batch and frozen RunSpec SHA-256")
        if runspec.owner_value_batch_sha256 != batch_sha:
            raise DraftValidationError("frozen RunSpec does not bind the Owner-value batch bytes")
        if batch.generator.git_commit != decision.get("git_commit") or batch.generator.git_commit != runspec.git_commit:
            raise DraftValidationError("Owner-value batch generator commit must match the G1 decision and frozen RunSpec")
        if runspec.proposal_sha256 != batch.proposal_sha256:
            raise DraftValidationError("frozen RunSpec proposal hash does not match the Owner-value batch")
        if runspec.split_membership_sha256 != batch.split.membership_sha256:
            raise DraftValidationError("frozen RunSpec split commitments do not match the Owner-value batch")
        expected_sources = {
            item.role: item.sha256 for item in batch.sources if item.role in {"corpus", "queries", "qrels"}
        }
        expected_sources.update(
            {
                "family": batch.family_commitment_sha256,
                "evaluator": sha256_payload(batch.evaluator.model_dump(mode="json")),
                "field_protocol": sha256_payload(batch.field_protocol),
            }
        )
        if runspec.source_sha256 != expected_sources:
            raise DraftValidationError("frozen RunSpec source commitments do not match the Owner-value batch")
        return {
            **result,
            "status": "HANDOFF_READY_EXECUTOR_UNAVAILABLE",
            "reason": "REPRODUCTION_EXECUTOR_NOT_IMPLEMENTED",
            "gate_status": "approved",
            "authorization": "F1.1_B0_B1_B2_ONLY",
            "executor_available": False,
            "proposal_sha256": batch.proposal_sha256,
            "owner_decision_id": decision["decision_id"],
            "frozen_runspec_sha256": runspec_sha,
        }
    return result


def _validate_g1_decision(repository_root: Path, path: Path) -> dict[str, object]:
    approvals = (repository_root / "control" / "decisions").resolve(strict=True)
    resolved = path.resolve(strict=True)
    if resolved.is_symlink() or not resolved.is_file():
        raise DraftValidationError("G1 decision must be a regular file")
    try:
        resolved.relative_to(approvals)
    except ValueError as error:
        raise DraftValidationError("G1 decision must be an immutable repository approval") from error
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    scope = payload.get("scope", {})
    if (
        payload.get("schema_version") != "myis.owner-gate-decision.v2"
        or payload.get("gate_id") != "G1"
        or payload.get("status") != "approved"
        or scope.get("action") != "authorize_reproduction"
        or "F1.1" not in scope.get("task_ids", [])
    ):
        raise DraftValidationError("G1 decision does not authorize F1.1 reproduction")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repository_root, check=True, capture_output=True, text=True
    ).stdout.strip()
    if payload.get("git_commit") != head:
        raise DraftValidationError("G1 decision is not bound to the current Git commit")
    if resolved.name != f"{payload.get('decision_id')}.json":
        raise DraftValidationError("G1 decision filename does not match its immutable ID")
    return payload


def _validate_frozen_runspec(
    repository_root: Path, path: Path, decision: dict[str, object]
) -> tuple[FrozenF1RunSpecV1, str]:
    resolved = path.resolve(strict=True)
    if resolved.is_symlink() or not resolved.is_file() or resolved.suffix.lower() not in {".yaml", ".yml"}:
        raise DraftValidationError("frozen RunSpec must be a regular YAML file")
    try:
        resolved.relative_to((repository_root / "campaigns").resolve(strict=True))
    except ValueError as error:
        raise DraftValidationError("frozen RunSpec must remain under campaigns") from error
    payload = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DraftValidationError("frozen RunSpec must be a mapping")
    try:
        runspec = validate_frozen_f1_runspec(payload)
    except ValueError as error:
        raise DraftValidationError("frozen RunSpec is not an exact G1 F1.1 B0/B1/B2 contract") from error
    if runspec.git_commit != decision.get("git_commit"):
        raise DraftValidationError("frozen RunSpec Git commit does not match the G1 decision")
    return runspec, hashlib.sha256(resolved.read_bytes()).hexdigest()
