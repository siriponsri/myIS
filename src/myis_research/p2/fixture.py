"""Repository-only deterministic P2 fixture pilot.

The pilot exercises the accepted P2 request, state-machine, manifest, and
package contracts in disposable workspaces. Only sanitized fixture provenance
is allowed to leave those workspaces.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import shutil
import subprocess
import tempfile
from typing import Any, Callable, Mapping

from ..kernel.canonical import canonical_sha256, file_sha256
from ..kernel.manifest_validation import ManifestValidationError, validate_manifest
from ..owner_local import OwnerLocalContractError, validate_receipt
from ..protection import assert_aggregate_only, assert_path_not_protected
from .contracts import (
    P2ContractError,
    build_request,
    load_profile,
    validate_p2_package_bundle,
    validate_p2_train_metric,
    write_immutable_json,
)
from .state import Candidate, P2RunStateMachine, P2StateError


FIXTURE_ID = "p2-fixture-pilot-v1"
FIXTURE_RUN_ID = f"{FIXTURE_ID}-run"
FIXTURE_PACKAGE_ID = f"{FIXTURE_ID}-package"
FIXTURE_OUTPUT_ROOT = Path("outputs/fixtures/p2")
DEFAULT_RECEIPT_PATH = FIXTURE_OUTPUT_ROOT / f"{FIXTURE_ID}.receipt.json"
DEFAULT_EXECUTION_MANIFEST_PATH = (
    FIXTURE_OUTPUT_ROOT / f"{FIXTURE_ID}.execution-manifest.json"
)
PRIOR_BASELINE_URI = Path(
    "campaigns/scope-autoindex-v1/evidence/"
    "dapfam-p1-fulltext-c058a3aa7357c782.receipt.json"
)
FIXTURE_TIMESTAMP = "2026-08-01T00:00:00Z"
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_GIT_COMMIT = re.compile(r"^[a-f0-9]{40,64}$")
_EXTRA_PROTECTED_KEYS = frozenset(
    {
        "raw_ranking",
        "raw_rankings",
        "ranking_payload",
        "ranking_payloads",
        "corpus_text",
        "query_text",
        "per_query_metrics",
        "token",
        "tokens",
        "cookie",
        "cookies",
        "session_id",
        "session_ids",
    }
)
_SECRET_VALUE = re.compile(
    r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\bsk-[A-Za-z0-9_-]{12,}|"
    r"\bBearer\s+[A-Za-z0-9._~+/-]{12,})",
    re.IGNORECASE,
)


class P2FixtureError(ValueError):
    """Raised before fixture provenance is persisted."""


@dataclass(frozen=True)
class FixtureRun:
    artifacts: dict[str, dict[str, Any]]
    hashes: dict[str, str]
    train_signature_sha256: str
    selection_signature_sha256: str


def fixture_what_if(repository_root: Path, output: Path | None = None) -> dict[str, Any]:
    """Describe fixture actions without executing the lifecycle."""

    root = Path(repository_root).resolve()
    profile = load_profile(root)
    target = Path(output) if output is not None else root / DEFAULT_RECEIPT_PATH
    return {
        "schema_version": "myis.p2-fixture-what-if.v1",
        "fixture_id": FIXTURE_ID,
        "command": "fixture-pilot",
        "what_if": True,
        "status": "fixture_only_planned",
        "phase_id": "P2_SCOPE_DEVELOPMENT",
        "task_id": "P2.1",
        "arm": "R1",
        "profile_id": profile.profile_id,
        "profile_sha256": profile.sha256,
        "output": _safe_display_path(root, target),
        "isolated_workspaces": 2,
        "synthetic_candidates": 32,
        "synthetic_iterations": 5,
        "synthetic_shortlist": 4,
        "fixture_selection_exposures": 1,
        "measured_runs": 0,
        "candidate_count": 0,
        "selection_accesses": 0,
        "protected_data_accessed": False,
        "measured_execution": False,
        "measured_execution_performed": False,
        "real_selection_opened": False,
    }


def run_fixture_pilot(
    repository_root: Path,
    output: Path,
    *,
    require_clean_git: bool = True,
    enforce_repository_output: bool = True,
) -> dict[str, Any]:
    """Run two independent fixture lifecycles and persist sanitized provenance."""

    root = Path(repository_root).resolve(strict=True)
    target = Path(output)
    if enforce_repository_output:
        target = _validate_output_path(root, target)
    else:
        target = target.resolve()
    if require_clean_git and _tracked_diff(root):
        raise P2FixtureError("tracked worktree must be clean before fixture execution")
    git_commit = _git_commit(root)
    profile = load_profile(root)
    envelope_sha256 = file_sha256(root / "control/execution-envelope-p2.yaml")
    real_before = _real_counter_snapshot(root)
    _require_real_boundary(real_before)

    runs: list[FixtureRun] = []
    for label in ("run-a", "run-b"):
        with tempfile.TemporaryDirectory(prefix=f"{FIXTURE_ID}-{label}-") as temporary:
            workspace = Path(temporary) / "repository"
            runs.append(_execute_once(root, workspace, git_commit))

    if runs[0].hashes != runs[1].hashes:
        raise P2FixtureError("deterministic fixture rerun canonical hashes differ")
    if runs[0].train_signature_sha256 != runs[1].train_signature_sha256:
        raise P2FixtureError("deterministic fixture train signatures differ")
    if runs[0].selection_signature_sha256 != runs[1].selection_signature_sha256:
        raise P2FixtureError("deterministic fixture selection signatures differ")

    negative_checks = run_negative_checks(root, git_commit=git_commit)
    if not negative_checks["passed"]:
        raise P2FixtureError("one or more fail-closed fixture probes did not reject")

    first = runs[0]
    receipt = _build_fixture_receipt(
        git_commit=git_commit,
        profile_id=profile.profile_id,
        profile_sha256=profile.sha256,
        envelope_sha256=envelope_sha256,
        hashes=first.hashes,
        negative_checks=negative_checks,
    )
    receipt = validate_fixture_receipt(receipt, repository_root=root)
    execution_manifest = _build_execution_manifest(
        git_commit=git_commit,
        receipt=receipt,
        hashes=first.hashes,
        profile_sha256=profile.sha256,
        envelope_sha256=envelope_sha256,
    )
    validate_fixture_execution_manifest(execution_manifest, receipt=receipt)

    execution_manifest_path = target.with_name(
        target.name.replace(".receipt.json", ".execution-manifest.json")
    )
    if execution_manifest_path == target:
        raise P2FixtureError("fixture receipt output must end with .receipt.json")
    _write_stable_json(target, receipt)
    _write_stable_json(execution_manifest_path, execution_manifest)

    real_after = _real_counter_snapshot(root)
    _require_real_boundary(real_after)
    if real_after != real_before:
        raise P2FixtureError("real P2 counters changed during fixture execution")

    return {
        "status": "PASS",
        "fixture_id": FIXTURE_ID,
        "fixture_status": "passed",
        "evidence_class": "fixture",
        "scientific_authority": False,
        "measured_execution": False,
        "protected_data_accessed": False,
        "receipt_path": _safe_display_path(root, target),
        "receipt_sha256": receipt["receipt_sha256"],
        "execution_manifest_path": _safe_display_path(root, execution_manifest_path),
        "execution_manifest_sha256": execution_manifest["manifest_sha256"],
        "fixture_package_sha256": receipt["fixture_package_sha256"],
        "deterministic_rerun": "passed",
        "canonical_hashes_match": True,
        "negative_checks_passed": True,
        "negative_check_count": negative_checks["count"],
        "synthetic_candidates": 32,
        "synthetic_iterations": 5,
        "synthetic_shortlist": 4,
        "fixture_selection_exposures": 1,
        "measured_runs": 0,
        "candidate_count": 0,
        "selection_accesses": 0,
    }


def validate_fixture_receipt(
    payload: Mapping[str, Any],
    *,
    repository_root: Path,
) -> dict[str, Any]:
    """Validate the sanitized fixture-only receipt defined by the goal contract."""

    if not isinstance(payload, Mapping):
        raise P2FixtureError("fixture receipt must be a JSON object")
    assert_fixture_safe(payload)
    required = {
        "schema_version",
        "fixture_id",
        "phase_id",
        "task_id",
        "arm",
        "fixture",
        "fixture_pilot_executed",
        "fixture_status",
        "evidence_class",
        "scientific_authority",
        "measured_execution",
        "measured_execution_performed",
        "protected_data_accessed",
        "claim_level",
        "claim_boundary",
        "safe_to_present",
        "git_commit",
        "synthetic_candidates",
        "synthetic_frozen_controls",
        "synthetic_preregistered_candidates",
        "synthetic_adaptive_candidates",
        "synthetic_adaptive_iterations",
        "synthetic_train_outcomes",
        "synthetic_shortlist_count",
        "fixture_selection_exposures",
        "synthetic_selection_outcomes",
        "measured_runs",
        "candidate_count",
        "selection_accesses",
        "profile_id",
        "profile_sha256",
        "execution_envelope_sha256",
        "request_sha256",
        "candidate_ledger_sha256",
        "baseline_commitment_sha256",
        "baseline_reproduction_receipt_sha256",
        "shortlist_freeze_receipt_sha256",
        "selection_receipt_sha256",
        "fixture_manifest_sha256",
        "fixture_package_sha256",
        "train_signature_sha256",
        "selection_signature_sha256",
        "deterministic_rerun",
        "canonical_hashes_match",
        "negative_checks_passed",
        "negative_check_count",
        "negative_check_catalog_sha256",
        "fixture_workspace_persisted",
        "real_selection_opened",
        "final_split_accessed",
        "gpu_used",
        "paid_api_used",
        "network_model_download_used",
        "provider_fallback_used",
        "receipt_sha256",
    }
    if set(payload) != required:
        missing = sorted(required - set(payload))
        extra = sorted(set(payload) - required)
        raise P2FixtureError(f"fixture receipt fields differ: missing={missing}, extra={extra}")
    expected_values = {
        "schema_version": "myis.p2-fixture-receipt.v1",
        "fixture_id": FIXTURE_ID,
        "phase_id": "P2_SCOPE_DEVELOPMENT",
        "task_id": "P2.1",
        "arm": "R1",
        "fixture": True,
        "fixture_pilot_executed": True,
        "fixture_status": "passed",
        "evidence_class": "fixture",
        "scientific_authority": False,
        "measured_execution": False,
        "measured_execution_performed": False,
        "protected_data_accessed": False,
        "claim_level": "none",
        "claim_boundary": "no_measured_claim",
        "safe_to_present": True,
        "synthetic_candidates": 32,
        "synthetic_frozen_controls": 4,
        "synthetic_preregistered_candidates": 8,
        "synthetic_adaptive_candidates": 20,
        "synthetic_adaptive_iterations": 5,
        "synthetic_train_outcomes": 32,
        "synthetic_shortlist_count": 4,
        "fixture_selection_exposures": 1,
        "synthetic_selection_outcomes": 4,
        "measured_runs": 0,
        "candidate_count": 0,
        "selection_accesses": 0,
        "profile_id": "p2-r1-primary-v1",
        "deterministic_rerun": "passed",
        "canonical_hashes_match": True,
        "negative_checks_passed": True,
        "fixture_workspace_persisted": False,
        "real_selection_opened": False,
        "final_split_accessed": False,
        "gpu_used": False,
        "paid_api_used": False,
        "network_model_download_used": False,
        "provider_fallback_used": False,
    }
    for field, expected in expected_values.items():
        if payload[field] != expected:
            raise P2FixtureError(f"fixture receipt {field} is invalid")
    for field in (
        "profile_sha256",
        "execution_envelope_sha256",
        "request_sha256",
        "candidate_ledger_sha256",
        "baseline_commitment_sha256",
        "baseline_reproduction_receipt_sha256",
        "shortlist_freeze_receipt_sha256",
        "selection_receipt_sha256",
        "fixture_manifest_sha256",
        "fixture_package_sha256",
        "train_signature_sha256",
        "selection_signature_sha256",
        "negative_check_catalog_sha256",
        "receipt_sha256",
    ):
        if not _SHA256.fullmatch(str(payload[field])):
            raise P2FixtureError(f"fixture receipt {field} must be SHA-256")
    if not _GIT_COMMIT.fullmatch(str(payload["git_commit"])):
        raise P2FixtureError("fixture receipt git_commit is invalid")
    if payload["negative_check_count"] != len(NEGATIVE_CHECK_IDS):
        raise P2FixtureError("fixture receipt negative check count is invalid")
    profile = load_profile(repository_root)
    if payload["profile_sha256"] != profile.sha256:
        raise P2FixtureError("fixture receipt profile hash is stale")
    envelope_path = Path(repository_root).resolve() / "control/execution-envelope-p2.yaml"
    if payload["execution_envelope_sha256"] != file_sha256(envelope_path):
        raise P2FixtureError("fixture receipt execution envelope hash is stale")
    unsigned = {key: value for key, value in payload.items() if key != "receipt_sha256"}
    if payload["receipt_sha256"] != canonical_sha256(unsigned):
        raise P2FixtureError("fixture receipt self-hash is invalid")
    return dict(payload)


def validate_fixture_execution_manifest(
    payload: Mapping[str, Any],
    *,
    receipt: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate execution metadata separately from the canonical P2 request."""

    try:
        validate_manifest(payload)
    except ManifestValidationError as error:
        raise P2FixtureError(str(error)) from error
    if payload["stage"] != "fixture" or payload["evidence_class"] != "fixture":
        raise P2FixtureError("execution manifest is not fixture-classified")
    if payload["receipt_sha256"] != receipt["receipt_sha256"]:
        raise P2FixtureError("execution manifest does not bind the fixture receipt")
    method = payload["method"]
    expected = {
        "fixture": True,
        "evidence_class": "fixture",
        "scientific_authority": False,
        "measured_execution": False,
        "protected_data_accessed": False,
        "claim_boundary": "no_measured_claim",
    }
    if not isinstance(method, Mapping) or any(method.get(key) != value for key, value in expected.items()):
        raise P2FixtureError("execution manifest fixture metadata is invalid")
    if payload["metrics"] != []:
        raise P2FixtureError("execution manifest cannot contain scientific metrics")
    assert_fixture_safe(payload)
    return dict(payload)


def assert_fixture_safe(value: Any, *, path: str = "$") -> None:
    """Apply the shared aggregate validator plus fixture-specific hard stops."""

    try:
        assert_aggregate_only(value, path=path)
    except ValueError as error:
        raise P2FixtureError(str(error)) from error
    _assert_fixture_extra_boundary(value, path=path)


def _assert_fixture_extra_boundary(value: Any, *, path: str) -> None:
    if isinstance(value, Mapping):
        for raw_key, item in value.items():
            key = str(raw_key)
            normalized = key.casefold().replace("-", "_").replace(" ", "_")
            if normalized in _EXTRA_PROTECTED_KEYS:
                raise P2FixtureError(f"fixture protected payload key is forbidden at {path}.{key}")
            _assert_fixture_extra_boundary(item, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _assert_fixture_extra_boundary(item, path=f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.casefold().replace("_", "-")
        if "final-872" in lowered:
            raise P2FixtureError(f"fixture final split reference is forbidden at {path}")
        if _SECRET_VALUE.search(value):
            raise P2FixtureError(f"fixture credential-like value is forbidden at {path}")
        is_absolute = (
            Path(value).is_absolute()
            or PurePosixPath(value).is_absolute()
            or PureWindowsPath(value).is_absolute()
        )
        if is_absolute and any(
            token in lowered
            for token in ("qrels", "membership", "query", "selection", "final", "credential", "secret")
        ):
            raise P2FixtureError(f"fixture owner-local protected path is forbidden at {path}")


def _execute_once(source_root: Path, workspace: Path, git_commit: str) -> FixtureRun:
    _prepare_workspace(source_root, workspace)
    profile = load_profile(workspace)
    envelope_sha256 = file_sha256(workspace / "control/execution-envelope-p2.yaml")
    prior_path = workspace / PRIOR_BASELINE_URI
    prior = _load_prior_receipt(prior_path)
    prior_metric = prior["metrics"][8]

    compiler_sha256 = canonical_sha256({"fixture": FIXTURE_ID, "component": "compiler"})
    config_sha256 = canonical_sha256({"fixture": FIXTURE_ID, "component": "config"})
    retriever_sha256 = canonical_sha256({"fixture": FIXTURE_ID, "component": "retriever"})
    evaluator_sha256 = str(prior["lineage_hashes"]["evaluator_sha256"])
    dataset_sha256 = str(prior["lineage_hashes"]["dataset_sha256"])
    scope_hashes = {
        "compiler": compiler_sha256,
        "config": config_sha256,
        "retriever": retriever_sha256,
        "evaluator": evaluator_sha256,
    }
    frozen_controls = [f"fixture-control-{index:02d}" for index in range(4)]
    request = build_request(
        request_id=FIXTURE_ID,
        git_commit=git_commit,
        execution_envelope_sha256=envelope_sha256,
        scope_hashes=scope_hashes,
        input_hashes={"dataset_lineage": dataset_sha256},
        frozen_controls=frozen_controls,
        repository_root=workspace,
    )
    machine = P2RunStateMachine(request_id=request["request_id"], profile=profile)

    control_arms = ("R0-W", "R0", "R1", "R1")
    for candidate_id, arm in zip(frozen_controls, control_arms, strict=True):
        machine.register_candidate(
            Candidate(candidate_id, arm, "frozen_control", 0, _candidate_spec_sha256(candidate_id))
        )
    preregistered = [f"fixture-preregistered-{index:02d}" for index in range(8)]
    for candidate_id in preregistered:
        machine.register_candidate(
            Candidate(candidate_id, "R1", "preregistered_patent", 0, _candidate_spec_sha256(candidate_id))
        )

    baseline_value = float(prior_metric["value"])
    expected_metric = _train_metric(
        frozen_controls[0],
        baseline_value,
        arm="R0-W",
        n=int(prior_metric["n"]),
        dataset_sha256=dataset_sha256,
        config_sha256=config_sha256,
        retriever_sha256=retriever_sha256,
        evaluator_sha256=evaluator_sha256,
    )
    commitment = machine.commit_baseline_expectation(
        baseline_candidate_id=frozen_controls[0],
        baseline_arm="R0-W",
        prior_artifact_uri=PRIOR_BASELINE_URI.as_posix(),
        prior_artifact_sha256=file_sha256(prior_path),
        metric_locator={"metrics_index": 8},
        expected_metric=expected_metric,
        tolerance=0.0,
    )

    adaptive_values = [round(0.60 + index * 0.01, 2) for index in range(20)]
    adaptive_index = 0
    for iteration in range(1, 6):
        for member in range(4):
            candidate_id = f"fixture-adaptive-{iteration:02d}-{member:02d}"
            machine.register_candidate(
                Candidate(candidate_id, "R1", "adaptive_autoindex", iteration, _candidate_spec_sha256(candidate_id))
            )
            machine.record_train(
                candidate_id,
                metric=_train_metric(
                    candidate_id,
                    adaptive_values[adaptive_index],
                    arm="R1",
                    n=int(prior_metric["n"]),
                    dataset_sha256=dataset_sha256,
                    config_sha256=config_sha256,
                    retriever_sha256=retriever_sha256,
                    evaluator_sha256=evaluator_sha256,
                ),
            )
            adaptive_index += 1
        machine.record_iteration(iteration)
    machine.finish_generation()

    base_candidates = frozen_controls + preregistered
    base_values = [baseline_value, 0.20, 0.30, 0.40] + [round(0.50 + index * 0.01, 2) for index in range(8)]
    for candidate_id, value in zip(base_candidates, base_values, strict=True):
        arm = str(machine.candidates[candidate_id]["arm"])
        machine.record_train(
            candidate_id,
            metric=_train_metric(
                candidate_id,
                value,
                arm=arm,
                n=int(prior_metric["n"]),
                dataset_sha256=dataset_sha256,
                config_sha256=config_sha256,
                retriever_sha256=retriever_sha256,
                evaluator_sha256=evaluator_sha256,
            ),
        )
    baseline = machine.record_baseline_reproduction(result=expected_metric)
    machine.finish_train()
    shortlist = machine.build_shortlist()
    if len(shortlist) != 4:
        raise P2FixtureError("canonical fixture shortlist must contain exactly four candidates")
    freeze = machine.freeze_shortlist(
        compiler_sha256=compiler_sha256,
        config_sha256=config_sha256,
        retriever_sha256=retriever_sha256,
        evaluator_sha256=evaluator_sha256,
    )
    exposed = machine.open_selection()
    if exposed != shortlist:
        raise P2FixtureError("fixture selection exposure differs from the frozen shortlist")
    for index, candidate_id in enumerate(shortlist):
        machine.record_selection(
            candidate_id,
            metric={
                "name": "recall_at_100",
                "value": round(0.70 + index * 0.01, 2),
                "n": 16,
                "scope": "OUT",
                "split": "selection",
                "direction": "maximize",
                "denominator": "macro_mean_per_query_relevant_families",
                "evidence_role": "primary",
            },
        )
    machine.close()
    selection = machine.build_selection_receipt()
    ledger = machine.build_candidate_ledger()

    request_sha256 = canonical_sha256(request)
    manifest = _self_hash(
        {
            "schema_version": "myis.p2-manifest.v1",
            "run_id": FIXTURE_RUN_ID,
            "request_id": request["request_id"],
            "phase_id": "P2_SCOPE_DEVELOPMENT",
            "arm": "R1",
            "campaign_revision": profile.payload["campaign_revision"],
            "budget_profile_id": profile.profile_id,
            "budget_profile_sha256": profile.sha256,
            "status": "valid",
            "evidence_class": "fixture",
            "request_sha256": request_sha256,
            "candidate_ledger_sha256": ledger["ledger_sha256"],
            "baseline_commitment_sha256": commitment["commitment_sha256"],
            "baseline_reproduction_receipt_sha256": baseline["receipt_sha256"],
            "shortlist_freeze_receipt_sha256": freeze["receipt_sha256"],
            "selection_receipt_sha256": selection["receipt_sha256"],
            "candidate_count": ledger["candidate_count"],
            "candidate_ids": selection["candidate_ids"],
            "selection_exposure_count": 1,
            "metrics": selection["metrics"],
        },
        "manifest_sha256",
    )
    artifact_root = Path("fixture-workspace") / FIXTURE_ID / "artifacts"
    uris = {
        "request": artifact_root / "request.json",
        "ledger": artifact_root / "candidate-ledger.json",
        "commitment": artifact_root / "baseline-commitment.json",
        "baseline": artifact_root / "baseline-reproduction.json",
        "freeze": artifact_root / "shortlist-freeze.json",
        "selection": artifact_root / "selection-receipt.json",
        "manifest": artifact_root / "manifest.json",
    }
    package = _self_hash(
        {
            "schema_version": "myis.p2-package.v1",
            "package_id": FIXTURE_PACKAGE_ID,
            "request_id": request["request_id"],
            "campaign_revision": profile.payload["campaign_revision"],
            "status": "validated_structural",
            "request_uri": uris["request"].as_posix(),
            "request_sha256": request_sha256,
            "candidate_ledger_uri": uris["ledger"].as_posix(),
            "candidate_ledger_sha256": ledger["ledger_sha256"],
            "baseline_commitment_uri": uris["commitment"].as_posix(),
            "baseline_commitment_sha256": commitment["commitment_sha256"],
            "baseline_reproduction_uri": uris["baseline"].as_posix(),
            "baseline_reproduction_sha256": baseline["receipt_sha256"],
            "shortlist_freeze_uri": uris["freeze"].as_posix(),
            "shortlist_freeze_sha256": freeze["receipt_sha256"],
            "selection_uri": uris["selection"].as_posix(),
            "selection_sha256": selection["receipt_sha256"],
            "manifest_uri": uris["manifest"].as_posix(),
            "manifest_sha256": manifest["manifest_sha256"],
            "budget_profile_id": profile.profile_id,
            "budget_profile_sha256": profile.sha256,
            "candidate_count": ledger["candidate_count"],
            "selection_exposure_count": 1,
        },
        "package_sha256",
    )
    artifacts = {
        "request": request,
        "ledger": ledger,
        "commitment": commitment,
        "baseline": baseline,
        "freeze": freeze,
        "selection": selection,
        "manifest": manifest,
        "package": package,
    }
    for name, relative in uris.items():
        write_immutable_json(workspace / relative, artifacts[name])
    write_immutable_json(workspace / artifact_root / "package.json", package)
    validate_p2_package_bundle(
        request=request,
        ledger=ledger,
        commitment=commitment,
        baseline=baseline,
        freeze=freeze,
        selection=selection,
        manifest=manifest,
        package=package,
        repository_root=workspace,
    )
    hashes = {
        "request_sha256": request_sha256,
        "candidate_ledger_sha256": ledger["ledger_sha256"],
        "baseline_commitment_sha256": commitment["commitment_sha256"],
        "baseline_reproduction_receipt_sha256": baseline["receipt_sha256"],
        "shortlist_freeze_receipt_sha256": freeze["receipt_sha256"],
        "selection_receipt_sha256": selection["receipt_sha256"],
        "fixture_manifest_sha256": manifest["manifest_sha256"],
        "fixture_package_sha256": package["package_sha256"],
    }
    train_signature = canonical_sha256(
        [candidate["train_metric"] for candidate in ledger["candidates"]]
    )
    selection_signature = canonical_sha256(selection["metrics"])
    return FixtureRun(
        artifacts=deepcopy(artifacts),
        hashes=hashes,
        train_signature_sha256=train_signature,
        selection_signature_sha256=selection_signature,
    )


def _build_fixture_receipt(
    *,
    git_commit: str,
    profile_id: str,
    profile_sha256: str,
    envelope_sha256: str,
    hashes: Mapping[str, str],
    negative_checks: Mapping[str, Any],
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": "myis.p2-fixture-receipt.v1",
        "fixture_id": FIXTURE_ID,
        "phase_id": "P2_SCOPE_DEVELOPMENT",
        "task_id": "P2.1",
        "arm": "R1",
        "fixture": True,
        "fixture_pilot_executed": True,
        "fixture_status": "passed",
        "evidence_class": "fixture",
        "scientific_authority": False,
        "measured_execution": False,
        "measured_execution_performed": False,
        "protected_data_accessed": False,
        "claim_level": "none",
        "claim_boundary": "no_measured_claim",
        "safe_to_present": True,
        "git_commit": git_commit,
        "synthetic_candidates": 32,
        "synthetic_frozen_controls": 4,
        "synthetic_preregistered_candidates": 8,
        "synthetic_adaptive_candidates": 20,
        "synthetic_adaptive_iterations": 5,
        "synthetic_train_outcomes": 32,
        "synthetic_shortlist_count": 4,
        "fixture_selection_exposures": 1,
        "synthetic_selection_outcomes": 4,
        "measured_runs": 0,
        "candidate_count": 0,
        "selection_accesses": 0,
        "profile_id": profile_id,
        "profile_sha256": profile_sha256,
        "execution_envelope_sha256": envelope_sha256,
        **dict(hashes),
        "train_signature_sha256": str(negative_checks["train_signature_sha256"]),
        "selection_signature_sha256": str(negative_checks["selection_signature_sha256"]),
        "deterministic_rerun": "passed",
        "canonical_hashes_match": True,
        "negative_checks_passed": True,
        "negative_check_count": int(negative_checks["count"]),
        "negative_check_catalog_sha256": str(negative_checks["catalog_sha256"]),
        "fixture_workspace_persisted": False,
        "real_selection_opened": False,
        "final_split_accessed": False,
        "gpu_used": False,
        "paid_api_used": False,
        "network_model_download_used": False,
        "provider_fallback_used": False,
    }
    body["receipt_sha256"] = canonical_sha256(body)
    return body


def _build_execution_manifest(
    *,
    git_commit: str,
    receipt: Mapping[str, Any],
    hashes: Mapping[str, str],
    profile_sha256: str,
    envelope_sha256: str,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": "myis.run-manifest.v2",
        "run_id": FIXTURE_RUN_ID,
        "parent_run_id": None,
        "experiment_id": "myis-system",
        "campaign_id": "scope-autoindex-v1",
        "evidence_class": "fixture",
        "status": "valid",
        "stage": "fixture",
        "created_at_utc": FIXTURE_TIMESTAMP,
        "git": {
            "commit": git_commit,
            "tracked_worktree_state": "clean",
            "tracked_worktree_diff_sha256": hashlib.sha256(b"").hexdigest(),
        },
        "request_sha256": hashes["request_sha256"],
        "inputs": {
            "hashes": {
                "dataset_lineage_sha256": receipt["train_signature_sha256"],
                "execution_envelope_sha256": envelope_sha256,
                "profile_sha256": profile_sha256,
                "request_sha256": hashes["request_sha256"],
            },
        },
        "method": {
            "fixture": True,
            "evidence_class": "fixture",
            "scientific_authority": False,
            "measured_execution": False,
            "protected_data_accessed": False,
            "claim_boundary": "no_measured_claim",
            "deterministic_rerun": "passed",
        },
        "resources": {
            "cpu_only": True,
            "gpu_used": False,
            "paid_api_used": False,
            "network_model_download_used": False,
            "provider_fallback_used": False,
        },
        "metrics": [],
        "artifacts": [
            {
                "artifact_id": f"{FIXTURE_ID}-receipt",
                "classification": "fixture",
                "sha256": receipt["receipt_sha256"],
            },
            {
                "artifact_id": FIXTURE_PACKAGE_ID,
                "classification": "fixture",
                "sha256": hashes["fixture_package_sha256"],
            },
        ],
        "commitments": {},
        "receipt_sha256": receipt["receipt_sha256"],
    }
    body["commitments"] = {
        "inputs_sha256": canonical_sha256(body["inputs"]),
        "method_sha256": canonical_sha256(body["method"]),
        "resources_sha256": canonical_sha256(body["resources"]),
        "metrics_sha256": canonical_sha256(body["metrics"]),
        "artifacts_sha256": canonical_sha256(body["artifacts"]),
    }
    body["manifest_sha256"] = canonical_sha256(body)
    return body


NEGATIVE_CHECK_IDS = (
    "metric-wrong-name",
    "metric-wrong-role",
    "metric-wrong-scope",
    "metric-wrong-evidence-role",
    "metric-wrong-direction",
    "metric-inconsistent-n",
    "metric-inconsistent-denominator",
    "metric-inconsistent-dataset-lineage",
    "metric-inconsistent-config",
    "metric-inconsistent-retriever",
    "metric-inconsistent-evaluator",
    "metric-missing-field",
    "metric-boolean-value",
    "candidate-duplicate-id",
    "candidate-invalid-id",
    "candidate-wrong-arm",
    "candidate-wrong-class",
    "candidate-invalid-iteration",
    "candidate-adaptive-before-base",
    "candidate-total-overflow",
    "candidate-adaptive-overflow",
    "candidate-iteration-overflow",
    "candidate-iteration-missing-member",
    "candidate-after-iteration-close",
    "candidate-outcome-unknown",
    "candidate-spec-hash-mismatch",
    "baseline-commitment-after-train",
    "baseline-missing-candidate",
    "baseline-duplicate-candidate",
    "baseline-wrong-arm",
    "baseline-prior-sha-mismatch",
    "baseline-invalid-locator",
    "baseline-expected-mismatch",
    "baseline-invalid-tolerance",
    "baseline-duplicate-commitment",
    "baseline-reproduction-before-train-complete",
    "baseline-reproduction-ledger-mismatch",
    "baseline-duplicate-reproduction",
    "iteration-non-consecutive",
    "iteration-incomplete",
    "iteration-best-not-derived",
    "iteration-membership-altered",
    "iteration-early-stop-too-soon",
    "iteration-stop-without-patience",
    "iteration-failure-before-shortlist",
    "shortlist-too-large",
    "shortlist-incomplete-train",
    "shortlist-unknown-candidate",
    "shortlist-duplicate-candidate",
    "shortlist-tie-rejected",
    "shortlist-altered-after-freeze",
    "shortlist-altered-freeze-receipt",
    "shortlist-freeze-hash-mismatch",
    "shortlist-selection-before-freeze",
    "selection-incomplete",
    "selection-duplicate",
    "selection-non-finalist",
    "selection-protected-field",
    "selection-query-id",
    "selection-per-query",
    "selection-second-exposure",
    "selection-real-counter-increment",
    "selection-post-close-mutation",
    "package-wrong-request-hash",
    "package-wrong-ledger-hash",
    "package-wrong-commitment-hash",
    "package-wrong-baseline-hash",
    "package-wrong-freeze-hash",
    "package-wrong-selection-hash",
    "package-wrong-manifest-hash",
    "package-wrong-self-hash",
    "package-candidate-count-mismatch",
    "package-candidate-id-mismatch",
    "package-profile-mismatch",
    "package-campaign-mismatch",
    "package-unauthorized-path",
    "package-protected-uri",
    "package-missing-artifact",
    "protected-query-id",
    "protected-query-ids",
    "protected-qrels",
    "protected-membership",
    "protected-per-query",
    "protected-per-query-metrics",
    "protected-raw-rankings",
    "protected-provider-payload",
    "protected-corpus-text",
    "protected-query-text",
    "protected-final-872",
    "protected-credentials",
    "protected-tokens",
    "protected-cookies",
    "protected-session-id",
    "protected-absolute-owner-path",
)


def run_negative_checks(repository_root: Path, *, git_commit: str) -> dict[str, Any]:
    """Run deterministic fail-closed probes covering every Section 16 case."""

    root = Path(repository_root).resolve(strict=True)
    profile = load_profile(root)
    if profile.payload["limits"]["max_candidates_total"] != 32:
        raise P2FixtureError("negative-check profile boundary drifted")
    passed: set[str] = set()

    def rejects(check_id: str, action: Callable[[], Any]) -> None:
        try:
            action()
        except (P2ContractError, P2FixtureError, P2StateError, ManifestValidationError, ValueError, PermissionError):
            passed.add(check_id)
            return
        raise P2FixtureError(f"negative check did not reject: {check_id}")

    context = _probe_context(root)
    base_metric = _probe_metric(context, "probe-control-00", context["baseline_value"], arm="R0-W")
    metric_mutations: dict[str, Callable[[dict[str, Any]], None]] = {
        "metric-wrong-name": lambda row: row.__setitem__("metric_name", "precision_at_100"),
        "metric-wrong-role": lambda row: row.__setitem__("data_role", "selection"),
        "metric-wrong-scope": lambda row: row.__setitem__("scope", "IN"),
        "metric-wrong-evidence-role": lambda row: row.__setitem__("evidence_role", "secondary"),
        "metric-wrong-direction": lambda row: row.__setitem__("direction", "maximize"),
        "metric-inconsistent-denominator": lambda row: row.__setitem__("denominator", "other"),
        "metric-missing-field": lambda row: row.pop("evaluator_sha256"),
        "metric-boolean-value": lambda row: row.__setitem__("value", True),
    }
    for check_id, mutate in metric_mutations.items():
        def action(mutate: Callable[[dict[str, Any]], None] = mutate) -> None:
            metric = deepcopy(base_metric)
            mutate(metric)
            validate_p2_train_metric(metric)
        rejects(check_id, action)

    for check_id, field, value in (
        ("metric-inconsistent-n", "n", int(context["n"]) + 1),
        ("metric-inconsistent-dataset-lineage", "dataset_lineage_sha256", "1" * 64),
        ("metric-inconsistent-config", "config_sha256", "2" * 64),
        ("metric-inconsistent-retriever", "retriever_sha256", "3" * 64),
        ("metric-inconsistent-evaluator", "evaluator_sha256", "4" * 64),
    ):
        def action(field: str = field, value: Any = value) -> None:
            machine = _probe_machine(root, context)
            _register_probe_base(machine)
            _commit_probe_baseline(machine, context)
            for index in range(2):
                candidate_id = f"probe-adaptive-01-{index:02d}"
                machine.register_candidate(
                    Candidate(candidate_id, "R1", "adaptive_autoindex", 1, _candidate_spec_sha256(candidate_id))
                )
            machine.record_train(
                "probe-adaptive-01-00",
                metric=_probe_metric(context, "probe-adaptive-01-00", 0.60),
            )
            changed = _probe_metric(context, "probe-adaptive-01-01", 0.61)
            changed[field] = value
            machine.record_train("probe-adaptive-01-01", metric=changed)
        rejects(check_id, action)

    rejects("candidate-duplicate-id", lambda: _probe_duplicate_candidate(root, context))
    rejects(
        "candidate-invalid-id",
        lambda: _probe_machine(root, context).register_candidate(
            Candidate("INVALID ID", "R0", "frozen_control", 0, "1" * 64)
        ),
    )
    rejects("candidate-wrong-arm", lambda: _probe_wrong_candidate_arm(root, context))
    rejects(
        "candidate-wrong-class",
        lambda: _probe_machine(root, context).register_candidate(
            Candidate("probe-invalid-class", "R1", "unknown", 0, "1" * 64)
        ),
    )
    rejects(
        "candidate-invalid-iteration",
        lambda: _probe_machine(root, context).register_candidate(
            Candidate("probe-invalid-iteration", "R1", "adaptive_autoindex", 6, "1" * 64)
        ),
    )
    rejects("candidate-adaptive-before-base", lambda: _probe_adaptive_before_base(root, context))
    rejects("candidate-total-overflow", lambda: _probe_candidate_overflow(root, context))
    rejects("candidate-adaptive-overflow", lambda: _probe_candidate_overflow(root, context))
    rejects("candidate-iteration-overflow", lambda: _probe_iteration_overflow(root, context))
    rejects("candidate-iteration-missing-member", lambda: _probe_incomplete_iteration(root, context))
    rejects("candidate-after-iteration-close", lambda: _probe_after_iteration_close(root, context))
    rejects("candidate-outcome-unknown", lambda: _probe_unknown_outcome(root, context))

    with tempfile.TemporaryDirectory(prefix=f"{FIXTURE_ID}-negative-anchor-") as temporary:
        anchor_root = Path(temporary) / "repository"
        anchor = _execute_once(root, anchor_root, git_commit)
        rejects(
            "candidate-spec-hash-mismatch",
            lambda: _probe_bundle_mutation(root, anchor, "candidate-spec-hash-mismatch"),
        )

        rejects("baseline-prior-sha-mismatch", lambda: _probe_bundle_mutation(root, anchor, "baseline-prior-sha-mismatch"))
        rejects("baseline-invalid-locator", lambda: _probe_bundle_mutation(root, anchor, "baseline-invalid-locator"))
        rejects("baseline-expected-mismatch", lambda: _probe_bundle_mutation(root, anchor, "baseline-expected-mismatch"))
        rejects("baseline-duplicate-candidate", lambda: _probe_bundle_mutation(root, anchor, "baseline-duplicate-candidate"))
        rejects("iteration-best-not-derived", lambda: _probe_bundle_mutation(root, anchor, "iteration-best-not-derived"))
        rejects("iteration-membership-altered", lambda: _probe_bundle_mutation(root, anchor, "iteration-membership-altered"))
        rejects("shortlist-too-large", lambda: _probe_bundle_mutation(root, anchor, "shortlist-too-large"))
        rejects("shortlist-unknown-candidate", lambda: _probe_bundle_mutation(root, anchor, "shortlist-unknown-candidate"))
        rejects("shortlist-duplicate-candidate", lambda: _probe_bundle_mutation(root, anchor, "shortlist-duplicate-candidate"))
        rejects("shortlist-altered-freeze-receipt", lambda: _probe_bundle_mutation(root, anchor, "shortlist-altered-freeze-receipt"))
        rejects("shortlist-freeze-hash-mismatch", lambda: _probe_bundle_mutation(root, anchor, "shortlist-freeze-hash-mismatch"))
        for check_id in (
            "package-wrong-request-hash",
            "package-wrong-ledger-hash",
            "package-wrong-commitment-hash",
            "package-wrong-baseline-hash",
            "package-wrong-freeze-hash",
            "package-wrong-selection-hash",
            "package-wrong-manifest-hash",
            "package-wrong-self-hash",
            "package-candidate-count-mismatch",
            "package-candidate-id-mismatch",
            "package-profile-mismatch",
            "package-campaign-mismatch",
            "package-unauthorized-path",
            "package-protected-uri",
            "package-missing-artifact",
        ):
            rejects(check_id, lambda check_id=check_id: _probe_bundle_mutation(root, anchor, check_id))

        train_signature_sha256 = anchor.train_signature_sha256
        selection_signature_sha256 = anchor.selection_signature_sha256

    rejects("baseline-commitment-after-train", lambda: _probe_commitment_after_train(root, context))
    rejects("baseline-missing-candidate", lambda: _probe_missing_baseline(root, context))
    rejects("baseline-wrong-arm", lambda: _probe_wrong_baseline_arm(root, context))
    rejects("baseline-invalid-tolerance", lambda: _probe_invalid_tolerance(root, context))
    rejects("baseline-duplicate-commitment", lambda: _probe_duplicate_commitment(root, context))
    rejects(
        "baseline-reproduction-before-train-complete",
        lambda: _probe_reproduction_before_baseline_train(root, context),
    )
    rejects(
        "baseline-reproduction-ledger-mismatch",
        lambda: _probe_reproduction_ledger_mismatch(root, context),
    )
    rejects("baseline-duplicate-reproduction", lambda: _probe_duplicate_reproduction(root, context))

    rejects("iteration-non-consecutive", lambda: _probe_nonconsecutive_iteration(root, context))
    rejects("iteration-incomplete", lambda: _probe_incomplete_iteration(root, context))
    rejects("iteration-early-stop-too-soon", lambda: _probe_early_stop_too_soon(root, context))
    rejects("iteration-stop-without-patience", lambda: _probe_stop_without_patience(root, context))
    rejects("iteration-failure-before-shortlist", lambda: _probe_adaptive_failure(root, context))

    rejects("shortlist-incomplete-train", lambda: _probe_shortlist_incomplete_train(root, context))
    _probe_tie_rejection(root, context)
    passed.add("shortlist-tie-rejected")
    rejects("shortlist-altered-after-freeze", lambda: _probe_post_freeze_mutation(root, context))
    rejects("shortlist-selection-before-freeze", lambda: _probe_selection_before_freeze(root, context))

    rejects("selection-incomplete", lambda: _probe_selection_incomplete(root, context))
    rejects("selection-duplicate", lambda: _probe_selection_duplicate(root, context))
    rejects("selection-non-finalist", lambda: _probe_selection_nonfinalist(root, context))
    rejects("selection-protected-field", lambda: _probe_selection_payload(root, context, {"credentials": {}}))
    rejects("selection-query-id", lambda: _probe_selection_payload(root, context, {"query_id": "x"}))
    rejects("selection-per-query", lambda: _probe_selection_payload(root, context, {"per_query": []}))
    rejects("selection-second-exposure", lambda: _probe_second_selection_exposure(root, context))
    rejects("selection-post-close-mutation", lambda: _probe_post_close_mutation(root, context))
    invalid_receipt = _build_fixture_receipt(
        git_commit=git_commit,
        profile_id=profile.profile_id,
        profile_sha256=profile.sha256,
        envelope_sha256=file_sha256(root / "control/execution-envelope-p2.yaml"),
        hashes={
            "request_sha256": "1" * 64,
            "candidate_ledger_sha256": "2" * 64,
            "baseline_commitment_sha256": "3" * 64,
            "baseline_reproduction_receipt_sha256": "4" * 64,
            "shortlist_freeze_receipt_sha256": "5" * 64,
            "selection_receipt_sha256": "6" * 64,
            "fixture_manifest_sha256": "7" * 64,
            "fixture_package_sha256": "8" * 64,
        },
        negative_checks={
            "count": len(NEGATIVE_CHECK_IDS),
            "catalog_sha256": canonical_sha256(list(NEGATIVE_CHECK_IDS)),
            "train_signature_sha256": "9" * 64,
            "selection_signature_sha256": "a" * 64,
        },
    )
    invalid_receipt["selection_accesses"] = 1
    invalid_receipt["receipt_sha256"] = canonical_sha256(
        {key: value for key, value in invalid_receipt.items() if key != "receipt_sha256"}
    )
    rejects(
        "selection-real-counter-increment",
        lambda: validate_fixture_receipt(invalid_receipt, repository_root=root),
    )

    probes = {
        "protected-query-id": {"query_id": "fixture"},
        "protected-query-ids": {"query_ids": []},
        "protected-qrels": {"qrels": []},
        "protected-membership": {"membership": []},
        "protected-per-query": {"per_query": []},
        "protected-per-query-metrics": {"per_query_metrics": []},
        "protected-raw-rankings": {"raw_rankings": []},
        "protected-provider-payload": {"raw_provider_payload": {}},
        "protected-corpus-text": {"corpus_text": "fixture"},
        "protected-query-text": {"query_text": "fixture"},
        "protected-final-872": {"pointer": "final-872"},
        "protected-credentials": {"credentials": {}},
        "protected-tokens": {"tokens": []},
        "protected-cookies": {"cookies": []},
        "protected-session-id": {"session_id": "fixture"},
        "protected-absolute-owner-path": {"pointer": "C:/owner/protected/query/data.json"},
    }
    for check_id, value in probes.items():
        rejects(check_id, lambda value=value: assert_fixture_safe(value))

    expected = set(NEGATIVE_CHECK_IDS)
    if passed != expected:
        missing = sorted(expected - passed)
        extra = sorted(passed - expected)
        raise P2FixtureError(f"negative check coverage mismatch: missing={missing}, extra={extra}")
    return {
        "passed": True,
        "count": len(passed),
        "catalog_sha256": canonical_sha256(list(NEGATIVE_CHECK_IDS)),
        "train_signature_sha256": train_signature_sha256,
        "selection_signature_sha256": selection_signature_sha256,
    }


def _probe_context(root: Path) -> dict[str, Any]:
    prior_path = root / PRIOR_BASELINE_URI
    prior = _load_prior_receipt(prior_path)
    metric = prior["metrics"][8]
    return {
        "prior_sha256": file_sha256(prior_path),
        "baseline_value": float(metric["value"]),
        "n": int(metric["n"]),
        "dataset_sha256": str(prior["lineage_hashes"]["dataset_sha256"]),
        "compiler_sha256": canonical_sha256({"fixture": FIXTURE_ID, "probe": "compiler"}),
        "config_sha256": canonical_sha256({"fixture": FIXTURE_ID, "probe": "config"}),
        "retriever_sha256": canonical_sha256({"fixture": FIXTURE_ID, "probe": "retriever"}),
        "evaluator_sha256": str(prior["lineage_hashes"]["evaluator_sha256"]),
    }


def _probe_machine(root: Path, context: Mapping[str, Any]) -> P2RunStateMachine:
    del context
    return P2RunStateMachine(request_id="p2-fixture-negative-probe", profile=load_profile(root))


def _probe_metric(
    context: Mapping[str, Any],
    candidate_id: str,
    value: float,
    *,
    arm: str = "R1",
) -> dict[str, Any]:
    return _train_metric(
        candidate_id,
        value,
        arm=arm,
        n=int(context["n"]),
        dataset_sha256=str(context["dataset_sha256"]),
        config_sha256=str(context["config_sha256"]),
        retriever_sha256=str(context["retriever_sha256"]),
        evaluator_sha256=str(context["evaluator_sha256"]),
    )


def _register_probe_base(machine: P2RunStateMachine) -> None:
    for index, arm in enumerate(("R0-W", "R0", "R1", "R1")):
        candidate_id = f"probe-control-{index:02d}"
        machine.register_candidate(
            Candidate(candidate_id, arm, "frozen_control", 0, _candidate_spec_sha256(candidate_id))
        )
    for index in range(8):
        candidate_id = f"probe-preregistered-{index:02d}"
        machine.register_candidate(
            Candidate(candidate_id, "R1", "preregistered_patent", 0, _candidate_spec_sha256(candidate_id))
        )


def _commit_probe_baseline(
    machine: P2RunStateMachine,
    context: Mapping[str, Any],
    *,
    candidate_id: str = "probe-control-00",
    arm: str = "R0-W",
    tolerance: float = 0.0,
) -> dict[str, Any]:
    return machine.commit_baseline_expectation(
        baseline_candidate_id=candidate_id,
        baseline_arm=arm,
        prior_artifact_uri=PRIOR_BASELINE_URI.as_posix(),
        prior_artifact_sha256=str(context["prior_sha256"]),
        metric_locator={"metrics_index": 8},
        expected_metric=_probe_metric(
            context,
            candidate_id,
            float(context["baseline_value"]),
            arm=arm,
        ),
        tolerance=tolerance,
    )


def _complete_probe_iteration(
    machine: P2RunStateMachine,
    context: Mapping[str, Any],
    iteration: int,
    best_value: float,
) -> None:
    for member in range(4):
        candidate_id = f"probe-adaptive-{iteration:02d}-{member:02d}"
        machine.register_candidate(
            Candidate(candidate_id, "R1", "adaptive_autoindex", iteration, _candidate_spec_sha256(candidate_id))
        )
        machine.record_train(
            candidate_id,
            metric=_probe_metric(context, candidate_id, best_value - member * 0.01),
        )
    machine.record_iteration(iteration)


def _finish_probe_generation(
    machine: P2RunStateMachine,
    context: Mapping[str, Any],
    *,
    scores: tuple[float, ...] = (0.60, 0.70, 0.70, 0.70),
) -> None:
    for iteration, score in enumerate(scores, start=1):
        _complete_probe_iteration(machine, context, iteration, score)
    machine.finish_generation()


def _train_probe_base(
    machine: P2RunStateMachine,
    context: Mapping[str, Any],
    *,
    baseline_value: float | None = None,
    tie: bool = False,
) -> None:
    actual_baseline = float(context["baseline_value"]) if baseline_value is None else baseline_value
    values = [actual_baseline, 0.85 if tie else 0.90, 0.40, 0.30]
    values += [0.85 if tie else 0.80, 0.75, 0.65, 0.55, 0.45, 0.35, 0.25, 0.15]
    base_ids = [f"probe-control-{index:02d}" for index in range(4)] + [
        f"probe-preregistered-{index:02d}" for index in range(8)
    ]
    for candidate_id, value in zip(base_ids, values, strict=True):
        arm = str(machine.candidates[candidate_id]["arm"])
        machine.record_train(candidate_id, metric=_probe_metric(context, candidate_id, value, arm=arm))


def _ready_probe_machine(
    root: Path,
    context: Mapping[str, Any],
    *,
    tie: bool = False,
) -> P2RunStateMachine:
    machine = _probe_machine(root, context)
    _register_probe_base(machine)
    _commit_probe_baseline(machine, context)
    _finish_probe_generation(machine, context)
    _train_probe_base(machine, context, tie=tie)
    machine.record_baseline_reproduction(
        result=_probe_metric(
            context,
            "probe-control-00",
            float(context["baseline_value"]),
            arm="R0-W",
        )
    )
    machine.finish_train()
    machine.build_shortlist()
    machine.freeze_shortlist(
        compiler_sha256=str(context["compiler_sha256"]),
        config_sha256=str(context["config_sha256"]),
        retriever_sha256=str(context["retriever_sha256"]),
        evaluator_sha256=str(context["evaluator_sha256"]),
    )
    return machine


def _probe_duplicate_candidate(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    candidate = Candidate("probe-control-00", "R0-W", "frozen_control", 0, "1" * 64)
    machine.register_candidate(candidate)
    machine.register_candidate(candidate)


def _probe_wrong_candidate_arm(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    machine.register_candidate(
        Candidate("probe-preregistered-wrong-arm", "R0", "preregistered_patent", 0, "1" * 64)
    )


def _probe_adaptive_before_base(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    machine.register_candidate(
        Candidate("probe-adaptive-01-00", "R1", "adaptive_autoindex", 1, "1" * 64)
    )


def _probe_candidate_overflow(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    _register_probe_base(machine)
    _commit_probe_baseline(machine, context)
    for iteration, score in enumerate((0.60, 0.61, 0.62, 0.63, 0.64), start=1):
        _complete_probe_iteration(machine, context, iteration, score)
    machine.register_candidate(
        Candidate("probe-adaptive-overflow", "R1", "adaptive_autoindex", 5, "1" * 64)
    )


def _probe_iteration_overflow(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    _register_probe_base(machine)
    _commit_probe_baseline(machine, context)
    for member in range(5):
        candidate_id = f"probe-adaptive-01-{member:02d}"
        machine.register_candidate(
            Candidate(candidate_id, "R1", "adaptive_autoindex", 1, _candidate_spec_sha256(candidate_id))
        )


def _probe_incomplete_iteration(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    _register_probe_base(machine)
    _commit_probe_baseline(machine, context)
    for member in range(3):
        candidate_id = f"probe-adaptive-01-{member:02d}"
        machine.register_candidate(
            Candidate(candidate_id, "R1", "adaptive_autoindex", 1, _candidate_spec_sha256(candidate_id))
        )
        machine.record_train(candidate_id, metric=_probe_metric(context, candidate_id, 0.60 + member * 0.01))
    machine.record_iteration(1)


def _probe_after_iteration_close(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    _register_probe_base(machine)
    _commit_probe_baseline(machine, context)
    _complete_probe_iteration(machine, context, 1, 0.60)
    machine.register_candidate(
        Candidate("probe-adaptive-01-late", "R1", "adaptive_autoindex", 1, "1" * 64)
    )


def _probe_unknown_outcome(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    _register_probe_base(machine)
    _commit_probe_baseline(machine, context)
    machine.record_train("probe-unknown", metric=_probe_metric(context, "probe-unknown", 0.50))


def _probe_commitment_after_train(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    _register_probe_base(machine)
    _commit_probe_baseline(machine, context)
    candidate_id = "probe-adaptive-01-00"
    machine.register_candidate(
        Candidate(candidate_id, "R1", "adaptive_autoindex", 1, _candidate_spec_sha256(candidate_id))
    )
    machine.record_train(candidate_id, metric=_probe_metric(context, candidate_id, 0.60))
    _commit_probe_baseline(machine, context)


def _probe_missing_baseline(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    _register_probe_base(machine)
    _commit_probe_baseline(machine, context, candidate_id="probe-missing")


def _probe_wrong_baseline_arm(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    _register_probe_base(machine)
    _commit_probe_baseline(machine, context, arm="R0")


def _probe_invalid_tolerance(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    _register_probe_base(machine)
    _commit_probe_baseline(machine, context, tolerance=-0.1)


def _probe_duplicate_commitment(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    _register_probe_base(machine)
    _commit_probe_baseline(machine, context)
    _commit_probe_baseline(machine, context)


def _probe_reproduction_before_baseline_train(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    _register_probe_base(machine)
    _commit_probe_baseline(machine, context)
    _finish_probe_generation(machine, context)
    machine.record_baseline_reproduction(
        result=_probe_metric(context, "probe-control-00", float(context["baseline_value"]), arm="R0-W")
    )


def _probe_reproduction_ledger_mismatch(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    _register_probe_base(machine)
    _commit_probe_baseline(machine, context)
    _finish_probe_generation(machine, context)
    _train_probe_base(machine, context, baseline_value=float(context["baseline_value"]) + 0.0001)
    machine.record_baseline_reproduction(
        result=_probe_metric(context, "probe-control-00", float(context["baseline_value"]), arm="R0-W")
    )


def _probe_duplicate_reproduction(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    _register_probe_base(machine)
    _commit_probe_baseline(machine, context)
    _finish_probe_generation(machine, context)
    _train_probe_base(machine, context)
    result = _probe_metric(context, "probe-control-00", float(context["baseline_value"]), arm="R0-W")
    machine.record_baseline_reproduction(result=result)
    machine.record_baseline_reproduction(result=result)


def _probe_nonconsecutive_iteration(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    _register_probe_base(machine)
    _commit_probe_baseline(machine, context)
    machine.register_candidate(
        Candidate("probe-adaptive-02-00", "R1", "adaptive_autoindex", 2, "1" * 64)
    )


def _probe_early_stop_too_soon(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    _register_probe_base(machine)
    _commit_probe_baseline(machine, context)
    for iteration, score in enumerate((0.60, 0.70, 0.70), start=1):
        _complete_probe_iteration(machine, context, iteration, score)
    machine.finish_generation()


def _probe_stop_without_patience(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    _register_probe_base(machine)
    _commit_probe_baseline(machine, context)
    for iteration, score in enumerate((0.60, 0.70, 0.80, 0.90), start=1):
        _complete_probe_iteration(machine, context, iteration, score)
    machine.finish_generation()


def _probe_adaptive_failure(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    _register_probe_base(machine)
    _commit_probe_baseline(machine, context)
    for iteration, score in enumerate((0.60, 0.70, 0.70), start=1):
        _complete_probe_iteration(machine, context, iteration, score)
    for member in range(4):
        candidate_id = f"probe-adaptive-04-{member:02d}"
        machine.register_candidate(
            Candidate(candidate_id, "R1", "adaptive_autoindex", 4, _candidate_spec_sha256(candidate_id))
        )
        if member == 0:
            machine.record_train(candidate_id, metric=None, status="failed", failure_reason="fixture probe")
        else:
            machine.record_train(candidate_id, metric=_probe_metric(context, candidate_id, 0.70 - member * 0.01))
    machine.finish_generation()


def _probe_shortlist_incomplete_train(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    _register_probe_base(machine)
    _commit_probe_baseline(machine, context)
    _finish_probe_generation(machine, context)
    machine.finish_train()


def _probe_tie_rejection(root: Path, context: Mapping[str, Any]) -> None:
    machine = _ready_probe_machine(root, context, tie=True)
    if "probe-control-01" in machine.shortlist_ids or "probe-preregistered-00" in machine.shortlist_ids:
        raise P2FixtureError("strict tie rejection did not remove tied candidates")


def _probe_post_freeze_mutation(root: Path, context: Mapping[str, Any]) -> None:
    machine = _ready_probe_machine(root, context)
    machine.register_candidate(Candidate("probe-late", "R1", "adaptive_autoindex", 5, "1" * 64))


def _probe_selection_before_freeze(root: Path, context: Mapping[str, Any]) -> None:
    machine = _probe_machine(root, context)
    _register_probe_base(machine)
    _commit_probe_baseline(machine, context)
    _finish_probe_generation(machine, context)
    _train_probe_base(machine, context)
    machine.record_baseline_reproduction(
        result=_probe_metric(context, "probe-control-00", float(context["baseline_value"]), arm="R0-W")
    )
    machine.finish_train()
    machine.build_shortlist()
    machine.open_selection()


def _selection_probe_machine(root: Path, context: Mapping[str, Any]) -> P2RunStateMachine:
    machine = _ready_probe_machine(root, context)
    machine.open_selection()
    return machine


def _selection_metric_payload(value: float = 0.70) -> dict[str, Any]:
    return {
        "name": "recall_at_100",
        "value": value,
        "n": 16,
        "scope": "OUT",
        "split": "selection",
        "direction": "maximize",
        "denominator": "macro_mean_per_query_relevant_families",
        "evidence_role": "primary",
    }


def _probe_selection_incomplete(root: Path, context: Mapping[str, Any]) -> None:
    machine = _selection_probe_machine(root, context)
    machine.record_selection(machine.shortlist_ids[0], metric=_selection_metric_payload())
    machine.close()


def _probe_selection_duplicate(root: Path, context: Mapping[str, Any]) -> None:
    machine = _selection_probe_machine(root, context)
    candidate_id = machine.shortlist_ids[0]
    machine.record_selection(candidate_id, metric=_selection_metric_payload())
    machine.record_selection(candidate_id, metric=_selection_metric_payload())


def _probe_selection_nonfinalist(root: Path, context: Mapping[str, Any]) -> None:
    machine = _selection_probe_machine(root, context)
    machine.record_selection("probe-control-00", metric=_selection_metric_payload())


def _probe_selection_payload(
    root: Path,
    context: Mapping[str, Any],
    extra: Mapping[str, Any],
) -> None:
    machine = _selection_probe_machine(root, context)
    machine.record_selection(
        machine.shortlist_ids[0],
        metric={**_selection_metric_payload(), **dict(extra)},
    )


def _probe_second_selection_exposure(root: Path, context: Mapping[str, Any]) -> None:
    machine = _selection_probe_machine(root, context)
    machine.open_selection()


def _probe_post_close_mutation(root: Path, context: Mapping[str, Any]) -> None:
    machine = _selection_probe_machine(root, context)
    for index, candidate_id in enumerate(machine.shortlist_ids):
        machine.record_selection(candidate_id, metric=_selection_metric_payload(0.70 + index * 0.01))
    machine.close()
    machine.record_selection(machine.shortlist_ids[0], metric=_selection_metric_payload())


def _probe_bundle_mutation(source_root: Path, anchor: FixtureRun, check_id: str) -> None:
    bundle = deepcopy(anchor.artifacts)
    package = bundle["package"]

    if check_id.startswith("package-"):
        field_map = {
            "package-wrong-request-hash": "request_sha256",
            "package-wrong-ledger-hash": "candidate_ledger_sha256",
            "package-wrong-commitment-hash": "baseline_commitment_sha256",
            "package-wrong-baseline-hash": "baseline_reproduction_sha256",
            "package-wrong-freeze-hash": "shortlist_freeze_sha256",
            "package-wrong-selection-hash": "selection_sha256",
            "package-wrong-manifest-hash": "manifest_sha256",
        }
        if check_id in field_map:
            package[field_map[check_id]] = "0" * 64
            _rehash(package, "package_sha256")
        elif check_id == "package-wrong-self-hash":
            package["candidate_count"] = 31
        elif check_id == "package-candidate-count-mismatch":
            package["candidate_count"] = 31
            _rehash(package, "package_sha256")
        elif check_id == "package-candidate-id-mismatch":
            manifest = bundle["manifest"]
            manifest["candidate_ids"] = list(reversed(manifest["candidate_ids"]))
            _rehash(manifest, "manifest_sha256")
            package["manifest_sha256"] = manifest["manifest_sha256"]
            _rehash(package, "package_sha256")
        elif check_id == "package-profile-mismatch":
            package["budget_profile_sha256"] = "0" * 64
            _rehash(package, "package_sha256")
        elif check_id == "package-campaign-mismatch":
            package["campaign_revision"] = "scope-autoindex-v1-p2-other"
            _rehash(package, "package_sha256")
        elif check_id == "package-unauthorized-path":
            package["request_uri"] = "../request.json"
            _rehash(package, "package_sha256")
        elif check_id == "package-protected-uri":
            package["request_uri"] = "qrels/request.json"
            _rehash(package, "package_sha256")
        elif check_id != "package-missing-artifact":
            raise P2FixtureError(f"unknown package negative check: {check_id}")
    elif check_id in {
        "baseline-prior-sha-mismatch",
        "baseline-invalid-locator",
        "baseline-expected-mismatch",
    }:
        commitment = bundle["commitment"]
        if check_id == "baseline-prior-sha-mismatch":
            commitment["prior_artifact_sha256"] = "0" * 64
        elif check_id == "baseline-invalid-locator":
            commitment["metric_locator"] = {"metrics_index": 999}
        else:
            commitment["expected_metric"]["value"] = float(commitment["expected_metric"]["value"]) + 0.0001
        _rehash(commitment, "commitment_sha256")
        _rebind_bundle(bundle)
    elif check_id == "baseline-duplicate-candidate":
        ledger = bundle["ledger"]
        ledger["candidates"][1]["candidate_id"] = ledger["candidates"][0]["candidate_id"]
        ledger["candidates"][1]["train_metric"]["candidate_id"] = ledger["candidates"][0]["candidate_id"]
        _rehash(ledger, "ledger_sha256")
        _rebind_bundle(bundle, ledger_only=True)
    elif check_id == "candidate-spec-hash-mismatch":
        freeze = bundle["freeze"]
        candidate_id = freeze["candidate_ids"][0]
        freeze["candidate_spec_hashes"][candidate_id] = "f" * 64
        _rehash(freeze, "receipt_sha256")
        _rebind_bundle(bundle, freeze_only=True)
    elif check_id in {"iteration-best-not-derived", "iteration-membership-altered"}:
        ledger = bundle["ledger"]
        if check_id == "iteration-best-not-derived":
            ledger["iterations"][0]["best_metric"]["value"] = 0.01
        else:
            ledger["iterations"][0]["candidate_ids"][0] = "fixture-control-00"
        _rehash(ledger, "ledger_sha256")
        _rebind_bundle(bundle, ledger_only=True)
    elif check_id == "shortlist-too-large":
        freeze = bundle["freeze"]
        freeze["candidate_ids"].append("fixture-extra-finalist")
        freeze["candidate_spec_hashes"]["fixture-extra-finalist"] = "1" * 64
        _rehash(freeze, "receipt_sha256")
    elif check_id == "shortlist-duplicate-candidate":
        freeze = bundle["freeze"]
        freeze["candidate_ids"][1] = freeze["candidate_ids"][0]
        _rehash(freeze, "receipt_sha256")
    elif check_id == "shortlist-altered-freeze-receipt":
        bundle["freeze"]["status"] = "changed"
        _rehash(bundle["freeze"], "receipt_sha256")
    elif check_id == "shortlist-freeze-hash-mismatch":
        bundle["freeze"]["candidate_ids"] = list(reversed(bundle["freeze"]["candidate_ids"]))
    elif check_id == "shortlist-unknown-candidate":
        freeze = bundle["freeze"]
        old = freeze["candidate_ids"][0]
        freeze["candidate_ids"][0] = "fixture-unknown-finalist"
        freeze["candidate_spec_hashes"]["fixture-unknown-finalist"] = freeze["candidate_spec_hashes"].pop(old)
        _rehash(freeze, "receipt_sha256")
        selection = bundle["selection"]
        selection["candidate_ids"][0] = "fixture-unknown-finalist"
        selection["metrics"][0]["candidate_id"] = "fixture-unknown-finalist"
        selection["shortlist_freeze_receipt_sha256"] = freeze["receipt_sha256"]
        _rehash(selection, "receipt_sha256")
        manifest = bundle["manifest"]
        manifest["candidate_ids"] = list(selection["candidate_ids"])
        manifest["metrics"] = deepcopy(selection["metrics"])
        manifest["shortlist_freeze_receipt_sha256"] = freeze["receipt_sha256"]
        manifest["selection_receipt_sha256"] = selection["receipt_sha256"]
        _rehash(manifest, "manifest_sha256")
        package["shortlist_freeze_sha256"] = freeze["receipt_sha256"]
        package["selection_sha256"] = selection["receipt_sha256"]
        package["manifest_sha256"] = manifest["manifest_sha256"]
        _rehash(package, "package_sha256")
    else:
        raise P2FixtureError(f"unknown bundle negative check: {check_id}")

    with tempfile.TemporaryDirectory(prefix=f"{FIXTURE_ID}-{check_id}-") as temporary:
        case_root = Path(temporary) / "repository"
        _prepare_workspace(source_root, case_root)
        _write_probe_bundle(case_root, bundle)
        if check_id == "package-missing-artifact":
            (case_root / package["request_uri"]).unlink()
        _validate_probe_bundle(case_root, bundle)


def _rebind_bundle(
    bundle: dict[str, dict[str, Any]],
    *,
    ledger_only: bool = False,
    freeze_only: bool = False,
) -> None:
    ledger = bundle["ledger"]
    commitment = bundle["commitment"]
    baseline = bundle["baseline"]
    freeze = bundle["freeze"]
    selection = bundle["selection"]
    manifest = bundle["manifest"]
    package = bundle["package"]
    if not ledger_only and not freeze_only:
        ledger["baseline_commitment_sha256"] = commitment["commitment_sha256"]
        _rehash(ledger, "ledger_sha256")
        baseline["baseline_commitment_sha256"] = commitment["commitment_sha256"]
        baseline["expected_metric"] = deepcopy(commitment["expected_metric"])
        baseline["tolerance"] = commitment["tolerance"]
        _rehash(baseline, "receipt_sha256")
        freeze["baseline_commitment_sha256"] = commitment["commitment_sha256"]
        freeze["baseline_reproduction_receipt_sha256"] = baseline["receipt_sha256"]
        _rehash(freeze, "receipt_sha256")
    if ledger_only:
        pass
    selection["shortlist_freeze_receipt_sha256"] = freeze["receipt_sha256"]
    _rehash(selection, "receipt_sha256")
    manifest["candidate_ledger_sha256"] = ledger["ledger_sha256"]
    manifest["baseline_commitment_sha256"] = commitment["commitment_sha256"]
    manifest["baseline_reproduction_receipt_sha256"] = baseline["receipt_sha256"]
    manifest["shortlist_freeze_receipt_sha256"] = freeze["receipt_sha256"]
    manifest["selection_receipt_sha256"] = selection["receipt_sha256"]
    _rehash(manifest, "manifest_sha256")
    package["candidate_ledger_sha256"] = ledger["ledger_sha256"]
    package["baseline_commitment_sha256"] = commitment["commitment_sha256"]
    package["baseline_reproduction_sha256"] = baseline["receipt_sha256"]
    package["shortlist_freeze_sha256"] = freeze["receipt_sha256"]
    package["selection_sha256"] = selection["receipt_sha256"]
    package["manifest_sha256"] = manifest["manifest_sha256"]
    _rehash(package, "package_sha256")


def _write_probe_bundle(root: Path, bundle: Mapping[str, Mapping[str, Any]]) -> None:
    package = bundle["package"]
    uri_fields = {
        "request": "request_uri",
        "ledger": "candidate_ledger_uri",
        "commitment": "baseline_commitment_uri",
        "baseline": "baseline_reproduction_uri",
        "freeze": "shortlist_freeze_uri",
        "selection": "selection_uri",
        "manifest": "manifest_uri",
    }
    for name, field in uri_fields.items():
        value = package[field]
        if value is None:
            continue
        path = root / str(value)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(bundle[name]), ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def _validate_probe_bundle(root: Path, bundle: Mapping[str, Mapping[str, Any]]) -> None:
    validate_p2_package_bundle(
        request=bundle["request"],
        ledger=bundle["ledger"],
        commitment=bundle["commitment"],
        baseline=bundle["baseline"],
        freeze=bundle["freeze"],
        selection=bundle["selection"],
        manifest=bundle["manifest"],
        package=bundle["package"],
        repository_root=root,
    )


def _rehash(payload: dict[str, Any], field: str) -> None:
    payload.pop(field, None)
    payload[field] = canonical_sha256(payload)


def _prepare_workspace(source_root: Path, workspace: Path) -> None:
    for relative in (
        Path("control/budgets/p2-r1-primary-v1.yaml"),
        Path("control/execution-envelope-p2.yaml"),
        PRIOR_BASELINE_URI,
    ):
        source = source_root / relative
        target = workspace / relative
        if source.is_symlink() or not source.is_file():
            raise P2FixtureError(f"required repository-safe fixture input is missing: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def _load_prior_receipt(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        receipt = validate_receipt(payload)
    except (OSError, json.JSONDecodeError, OwnerLocalContractError, PermissionError, ValueError) as error:
        raise P2FixtureError("repository-safe prior P1 receipt is invalid") from error
    metrics = receipt.get("metrics")
    if not isinstance(metrics, list) or len(metrics) <= 8 or not isinstance(metrics[8], Mapping):
        raise P2FixtureError("repository-safe prior P1 metric locator is unavailable")
    assert_fixture_safe(receipt)
    return receipt


def _train_metric(
    candidate_id: str,
    value: float,
    *,
    arm: str,
    n: int,
    dataset_sha256: str,
    config_sha256: str,
    retriever_sha256: str,
    evaluator_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_version": "myis.p2-train-metric.v1",
        "candidate_id": candidate_id,
        "arm": arm,
        "metric_name": "recall_at_100",
        "data_role": "train",
        "scope": "OUT",
        "evidence_role": "primary",
        "direction": "higher_is_better",
        "value": value,
        "n": n,
        "denominator": "macro_mean_per_query_relevant_families",
        "dataset_lineage_sha256": dataset_sha256,
        "config_sha256": config_sha256,
        "retriever_sha256": retriever_sha256,
        "evaluator_sha256": evaluator_sha256,
    }


def _candidate_spec_sha256(candidate_id: str) -> str:
    return canonical_sha256({"fixture_id": FIXTURE_ID, "candidate_id": candidate_id})


def _self_hash(payload: dict[str, Any], field: str) -> dict[str, Any]:
    payload[field] = canonical_sha256(payload)
    return payload


def _real_counter_snapshot(root: Path) -> dict[str, Any]:
    campaign = _load_yaml(root / "control/campaigns/scope-autoindex-v1.yaml")
    execution = campaign.get("p2_execution", {}) if isinstance(campaign, Mapping) else {}
    read_model_path = root / "projections/read-model/read-model.v2.json"
    read_model: dict[str, Any] = {}
    if read_model_path.is_file():
        try:
            loaded = json.loads(read_model_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                read_model = loaded
        except (OSError, json.JSONDecodeError):
            pass
    p2 = read_model.get("p2_readiness", {}) if isinstance(read_model.get("p2_readiness"), Mapping) else {}
    source = p2.get("source", {}) if isinstance(p2.get("source"), Mapping) else {}
    freeze = p2.get("freeze_barrier", {}) if isinstance(p2.get("freeze_barrier"), Mapping) else {}
    return {
        "measured_runs": int(execution.get("measured_runs", p2.get("measured_runs", 0))),
        "candidate_count": int(p2.get("candidate_count", 0)),
        "selection_accesses": int(execution.get("selection_accesses", p2.get("selection_accesses", 0))),
        "shortlist_count": int(p2.get("shortlist_count", 0)),
        "baseline_commitment_sha256": source.get("baseline_commitment_sha256"),
        "baseline_reproduction_receipt_sha256": source.get("baseline_reproduction_receipt_sha256"),
        "freeze_status": freeze.get("status", "not_started"),
    }


def _require_real_boundary(snapshot: Mapping[str, Any]) -> None:
    expected = {
        "measured_runs": 0,
        "candidate_count": 0,
        "selection_accesses": 0,
        "shortlist_count": 0,
        "baseline_commitment_sha256": None,
        "baseline_reproduction_receipt_sha256": None,
        "freeze_status": "not_started",
    }
    if dict(snapshot) != expected:
        raise P2FixtureError("real P2 state is not at the required zero-counter boundary")


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml

        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (ImportError, OSError, ValueError) as error:
        raise P2FixtureError(f"cannot read canonical fixture control: {path}") from error
    if not isinstance(value, dict):
        raise P2FixtureError(f"canonical fixture control must be a mapping: {path}")
    return value


def _git_commit(root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise P2FixtureError("cannot resolve repository Git commit") from error
    value = completed.stdout.strip()
    if not _GIT_COMMIT.fullmatch(value):
        raise P2FixtureError("repository Git commit is invalid")
    return value


def _tracked_diff(root: Path) -> bytes:
    try:
        return subprocess.run(
            ["git", "diff", "--binary", "HEAD", "--"],
            cwd=root,
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, subprocess.SubprocessError) as error:
        raise P2FixtureError("cannot inspect tracked worktree state") from error


def _validate_output_path(root: Path, output: Path) -> Path:
    target = output if output.is_absolute() else root / output
    target = target.resolve()
    allowed_root = (root / FIXTURE_OUTPUT_ROOT).resolve()
    try:
        target.relative_to(allowed_root)
    except ValueError as error:
        raise P2FixtureError("fixture output must remain under outputs/fixtures/p2") from error
    if target.suffix.lower() != ".json" or not target.name.endswith(".receipt.json"):
        raise P2FixtureError("fixture output must be a .receipt.json file")
    relative = target.relative_to(root).as_posix()
    try:
        assert_path_not_protected(relative)
    except PermissionError as error:
        raise P2FixtureError(str(error)) from error
    current = target.parent
    while current != root.parent and current != root:
        if current.exists() and current.is_symlink():
            raise P2FixtureError("fixture output path cannot traverse a symlink")
        current = current.parent
    if target.exists() and target.is_symlink():
        raise P2FixtureError("fixture output cannot be a symlink")
    return target


def _write_stable_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(dict(payload), ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    except FileExistsError:
        if path.read_bytes() != encoded:
            raise P2FixtureError(f"refusing to overwrite drifted fixture provenance: {path}")
        return
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _safe_display_path(root: Path, value: Path) -> str:
    target = value if value.is_absolute() else root / value
    try:
        return target.resolve().relative_to(root).as_posix()
    except ValueError:
        return "external-fixture-output"


def utc_now() -> str:
    """Return a runtime-only timestamp for non-canonical logs."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
