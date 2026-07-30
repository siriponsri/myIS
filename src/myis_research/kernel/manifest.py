"""Canonical immutable run-manifest builder for the active v2 contract."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from ..owner_local import OwnerLocalContractError, canonical_sha256 as owner_canonical_sha256
from ..owner_local import validate_receipt, validate_request
from .canonical import canonical_sha256
from .manifest_validation import capture_git_state, validate_manifest


MANIFEST_SCHEMA = "myis.run-manifest.v2"
VALID_STAGES = {"fixture", "train", "selection", "final", "report"}
VALID_STATUSES = {"valid", "invalid", "blocked", "exploratory", "superseded", "aggregate_pending"}
_EVIDENCE_CLASSES = {"fixture", "train_selection_measured", "final", "report", "blocked"}
_SHA256_LENGTH = 64


def build_manifest(
    *,
    run_id: str,
    experiment_id: str,
    campaign_id: str,
    stage: str,
    status: str,
    source: Mapping[str, Any],
    data: Mapping[str, Any],
    method: Mapping[str, Any],
    resources: Mapping[str, Any],
    metrics: list[Mapping[str, Any]],
    artifacts: list[Mapping[str, Any]],
    evidence_class: str,
    repository_root: Path,
    owner_local_request: Mapping[str, Any],
    owner_local_receipt: Mapping[str, Any],
    parent_run_id: str | None = None,
    inputs: Mapping[str, Any] | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Build a P1 manifest bound to the real repository and Owner-local receipt.

    The caller supplies aggregate-safe public metadata only. The immutable
    manifest always derives the request/receipt and Git commitments itself.
    """

    if not isinstance(run_id, str) or not run_id:
        raise ValueError("run_id is required")
    if not isinstance(experiment_id, str) or not experiment_id:
        raise ValueError("experiment_id is required")
    if campaign_id != "scope-autoindex-v1":
        raise ValueError("manifest campaign_id is invalid")
    if stage not in VALID_STAGES or status not in VALID_STATUSES:
        raise ValueError("manifest stage/status is invalid")
    if evidence_class not in _EVIDENCE_CLASSES:
        raise ValueError("manifest evidence_class is invalid")
    if parent_run_id is not None and (not isinstance(parent_run_id, str) or not parent_run_id):
        raise ValueError("parent_run_id must be a non-empty string or null")

    try:
        request = validate_request(owner_local_request)
        receipt = validate_receipt(owner_local_receipt)
    except OwnerLocalContractError as error:
        raise ValueError("owner-local request or receipt is invalid") from error

    request_sha256 = owner_canonical_sha256(request)
    if receipt["request_sha256"] != request_sha256:
        raise ValueError("receipt is not bound to the supplied owner-local request")
    if receipt["request_id"] != request["request_id"]:
        raise ValueError("receipt request identity does not match supplied request")

    git = capture_git_state(repository_root)
    if request["git_commit"] != git["commit"]:
        raise ValueError("owner-local request commit does not match repository HEAD")
    _validate_stage_binding(stage, request, receipt)

    manifest_inputs = _build_inputs(source, data, request["input_hashes"], inputs)
    body: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA,
        "run_id": run_id,
        "parent_run_id": parent_run_id,
        "experiment_id": experiment_id,
        "campaign_id": campaign_id,
        "evidence_class": evidence_class,
        "status": status,
        "stage": stage,
        "created_at_utc": timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "git": git,
        "request_sha256": request_sha256,
        "inputs": manifest_inputs,
        "method": dict(method),
        "resources": dict(resources),
        "metrics": [dict(item) for item in metrics],
        "artifacts": [dict(item) for item in artifacts],
        "commitments": {},
        "receipt_sha256": receipt["receipt_sha256"],
    }
    body["commitments"] = _content_commitments(body)
    body["manifest_sha256"] = canonical_sha256(body)
    validate_manifest(body)
    return body


def manifest_round_trip(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the v2 schema contract and all canonical commitments."""

    validate_manifest(payload)
    return dict(payload)


def _build_inputs(
    source: Mapping[str, Any],
    data: Mapping[str, Any],
    declared_hashes: Mapping[str, str],
    supplied_inputs: Mapping[str, Any] | None,
) -> dict[str, Any]:
    value = dict(supplied_inputs or {"source": dict(source), "data": dict(data)})
    if "hashes" in value and value["hashes"] != dict(declared_hashes):
        raise ValueError("manifest input hashes must exactly match the owner-local request")
    value["hashes"] = dict(sorted(declared_hashes.items()))
    return value


def _content_commitments(payload: Mapping[str, Any]) -> dict[str, str]:
    return {
        "inputs_sha256": canonical_sha256(payload["inputs"]),
        "method_sha256": canonical_sha256(payload["method"]),
        "resources_sha256": canonical_sha256(payload["resources"]),
        "metrics_sha256": canonical_sha256(payload["metrics"]),
        "artifacts_sha256": canonical_sha256(payload["artifacts"]),
    }


def _validate_stage_binding(stage: str, request: Mapping[str, Any], receipt: Mapping[str, Any]) -> None:
    request_stage = request["stage"]
    if stage in {"train", "selection"}:
        expected = "train_selection"
    else:
        expected = stage
    if request_stage != expected or receipt["stage"] != expected:
        raise ValueError("manifest stage is not bound to the owner-local request/receipt stage")
    if receipt["phase_id"] != request["phase_id"] or receipt["decision_id"] != request["decision_id"]:
        raise ValueError("receipt identity does not match the owner-local request")
