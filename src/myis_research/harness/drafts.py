"""Draft-only F1 planning contracts that cannot be used as measured manifests."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml


DRAFT_RUNSPEC_SCHEMA = "myis.draft-runspec.v1"
DRAFT_MEASURED_MANIFEST_SCHEMA = "myis.draft-measured-manifest.v1"
PENDING_OWNER_DECISION = "PENDING_OWNER_DECISION"
NOT_YET_FROZEN = "NOT_YET_FROZEN"
NOT_AUTHORIZED = "NOT_AUTHORIZED"

_REQUIRED_COMMITMENTS = {
    "corpus",
    "query",
    "qrels",
    "family",
    "evaluator",
    "field_protocol",
    "published_targets",
    "compute_budget",
    "exact_split_membership_hash",
    "exact_out_positive_counts",
    "reproduction_authorization",
    "owner_value_batch",
    "source_commitment_hashes",
    "split_aliases",
    "proposal_sha256",
    "validation_receipt",
}
_FORBIDDEN_KEYS = {
    "approval_id",
    "decision_id",
    "artifact_hashes",
    "artifacts",
    "metrics",
    "results",
    "scientific_metrics",
    "run_id",
}
_DOCUMENT_KIND_BY_SCHEMA = {
    DRAFT_RUNSPEC_SCHEMA: "f1_dapfam_runspec_draft",
    DRAFT_MEASURED_MANIFEST_SCHEMA: "f1_dapfam_measured_manifest_draft",
}


class DraftValidationError(ValueError):
    """Raised when a planning document could be mistaken for an executable run."""


def validate_draft_document(payload: Any, *, expected_schema: str | None = None) -> dict[str, object]:
    """Validate a deliberately non-executable F1 planning document.

    These documents are not ``RunSpec`` or ``myis.run-manifest.v3`` payloads.
    They record only the gated preparation state and contain no measurements.
    """

    if not isinstance(payload, Mapping):
        raise DraftValidationError("draft document must be a mapping")
    schema = payload.get("schema_version")
    if schema not in {DRAFT_RUNSPEC_SCHEMA, DRAFT_MEASURED_MANIFEST_SCHEMA}:
        raise DraftValidationError("unsupported draft document schema")
    if expected_schema is not None and schema != expected_schema:
        raise DraftValidationError("draft document schema does not match the requested command")
    if payload.get("document_kind") != _DOCUMENT_KIND_BY_SCHEMA[schema]:
        raise DraftValidationError("draft document kind is not valid for its schema")
    if (payload.get("track"), payload.get("phase"), payload.get("task")) != ("C", "F1", "F1.1"):
        raise DraftValidationError("draft document is not scoped to Track C F1.1")
    if payload.get("status") != "draft":
        raise DraftValidationError("draft document status must be draft")
    if payload.get("executable") is not False:
        raise DraftValidationError("draft document executable must be false")
    if payload.get("gate") != "G1" or payload.get("gate_status") != "pending":
        raise DraftValidationError("draft document must remain G1 pending")
    if payload.get("authorization") != NOT_AUTHORIZED:
        raise DraftValidationError("draft document must remain NOT_AUTHORIZED")
    if payload.get("frozen_run_spec") != NOT_YET_FROZEN:
        raise DraftValidationError("draft document must remain NOT_YET_FROZEN")
    if payload.get("scientific_run") is not False or payload.get("dataset_access") != "none":
        raise DraftValidationError("draft document must declare no scientific run or dataset access")
    if payload.get("artifact_count") != 0 or payload.get("scientific_metric_count") != 0:
        raise DraftValidationError("draft document cannot declare artifacts or scientific metrics")

    commitments = payload.get("owner_commitments")
    if not isinstance(commitments, Mapping) or set(commitments) != _REQUIRED_COMMITMENTS:
        raise DraftValidationError("draft document must list the complete G1 Owner commitment set")
    if any(value != PENDING_OWNER_DECISION for value in commitments.values()):
        raise DraftValidationError("draft document commitments must remain PENDING_OWNER_DECISION")

    present_forbidden = sorted(_FORBIDDEN_KEYS & set(payload))
    if present_forbidden:
        raise DraftValidationError(f"draft document contains measured-run fields: {present_forbidden}")
    return {
        "status": "PASS",
        "schema_version": schema,
        "document_kind": payload.get("document_kind"),
        "executable": False,
        "gate": "G1",
    }


def load_draft_document(path: Path, *, template_root: Path, expected_schema: str | None = None) -> dict[str, object]:
    """Load only a regular YAML planning file under the repository template root."""

    root = template_root.resolve(strict=True)
    candidate = path if path.is_absolute() else (Path.cwd() / path)
    if candidate.is_symlink():
        raise DraftValidationError("draft document symlinks are not allowed")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (FileNotFoundError, ValueError) as error:
        raise DraftValidationError("draft document must be a regular file under campaigns/scope-autoindex-v1/specs") from error
    if resolved.suffix.lower() not in {".yaml", ".yml"}:
        raise DraftValidationError("draft document must use YAML")
    try:
        payload = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise DraftValidationError(f"invalid draft YAML: {error}") from error
    validation = validate_draft_document(payload, expected_schema=expected_schema)
    return {**validation, "path": resolved.relative_to(root.parent.parent).as_posix()}
