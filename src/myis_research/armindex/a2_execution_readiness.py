"""Local, aggregate-safe A2 execution-readiness primitives.

This module deliberately does not contact a provider, execute retrieval, or
generate candidates.  It only binds the already frozen A2 candidate universe
to lifecycle, synthetic-fixture, receipt, return, and bundle mechanics that a
separate adopted runner may use later.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import subprocess
import tarfile
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from io import BytesIO
from pathlib import Path
from typing import Any, Callable

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a2_candidate_freeze import validate_candidate_freeze

_HASH = re.compile(r"^[a-f0-9]{64}$")
_COMMIT = re.compile(r"^[a-f0-9]{40}$")
_ATTEMPT = re.compile(r"^a2-[a-z0-9-]{7,63}$")
_REMOTE_ROOT = re.compile(r"^/opt/myis/a2-[a-z0-9][a-z0-9-]{7,63}$")
_SCHEMA_ROOT = Path("schemas/armindex")
_MANIFEST = Path(
    "campaigns/armindex-multiretriever-v2/manifests/"
    "a2-five-arm-candidate-manifest.v1.json"
)
_FORBIDDEN_MEMBER = re.compile(
    r"(?:qrels|membership|query[_-]?ids?|ranking|credential|secret|"
    r"provider[_-]?payload|model[_-]?weights?)",
    re.IGNORECASE,
)
_REQUIRED_QUOTE_COMPONENTS = frozenset(
    {
        "compute_usd",
        "storage_usd",
        "network_usd",
        "platform_or_other_fee_usd",
        "tax_or_surcharge_usd",
    }
)
_REQUIRED_PROVIDER_SOURCES = frozenset(
    {
        "runtime",
        "model_lockset",
        "data_handoff",
        "ssh_host_key",
        "management_authority",
    }
)
_REQUIRED_TTL_SECONDS = 40 * 60 * 60
_FRESH_INSTANCE_ID = re.compile(r"^[1-9][0-9]{3,19}$")
_DESTROYED_PROVIDER_INSTANCE_IDS = frozenset({"47411176"})
_BUNDLE_CLOSURE = (
    "campaigns/armindex-multiretriever-v2/evidence/a2-five-arm-candidate-freeze.receipt.v1.json",
    "campaigns/armindex-multiretriever-v2/manifests/a2-five-arm-candidate-manifest.v1.json",
    "control/armindex/a2/candidate-freeze.lock.v1.json",
    "schemas/armindex/a2-candidate-freeze-lock.v1.json",
    "schemas/armindex/a2-candidate-freeze-receipt.v1.json",
    "schemas/armindex/a2-candidate-manifest.v1.json",
    "schemas/armindex/a2-execution-adoption-receipt.v1.json",
    "schemas/armindex/a2-execution-bundle-receipt.v1.json",
    "schemas/armindex/a2-deployment-package-receipt.v1.json",
    "schemas/armindex/a2-execution-ledger-entry.v1.json",
    "schemas/armindex/a2-execution-ledger-entry.v2.json",
    "schemas/armindex/a2-execution-ledger-entry.v3.json",
    "schemas/armindex/a2-candidate-result-receipt.v1.json",
    "schemas/armindex/a2-execution-closeout-receipt.v1.json",
    "schemas/armindex/a2-remote-stage-receipt.v1.json",
    "schemas/armindex/a2-lifecycle-checkpoint.v1.json",
    "schemas/armindex/a2-live-remote-probe-receipt.v1.json",
    "schemas/armindex/a2-measured-execution-authority.v1.json",
    "schemas/armindex/a2-measurement-authority-commitment.v1.json",
    "schemas/armindex/a2-remote-measured-transport.v1.json",
    "schemas/armindex/a2-remote-measured-transport.v2.json",
    "schemas/armindex/a2-remote-retrieval-input.v1.json",
    "schemas/armindex/a2-owner-local-measured-input.v1.json",
    "schemas/armindex/representation-program.v1.json",
    "schemas/armindex/a2-provider-admission-receipt.v1.json",
    "schemas/armindex/a2-provider-observation.v1.json",
    "schemas/armindex/a2-provider-instance-binding.v1.json",
    "schemas/armindex/a2-provider-observation.v2.json",
    "schemas/armindex/a2-provider-admission-receipt.v2.json",
    "schemas/armindex/a2-live-remote-probe-receipt.v2.json",
    "schemas/armindex/a2-remote-stage-receipt.v2.json",
    "schemas/armindex/a2-execution-adoption-receipt.v2.json",
    "schemas/armindex/a2-reserve-activation-decision.v1.json",
    "schemas/armindex/a2-reserve-budget-admission.v1.json",
    "schemas/armindex/a2-reserve-continuation-authority.v1.json",
    "schemas/armindex/a2-safe-return-receipt.v1.json",
    "schemas/armindex/a2-train-evaluation-receipt.v1.json",
    "schemas/armindex/a2-winner-selection-receipt.v1.json",
    "control/armindex/a2/execution-readiness-contract.v1.json",
    "control/armindex/a2/execution-readiness-contract.v2.json",
    "control/armindex/a2/measured-command-argv.v1.json",
    "control/armindex/a2/measurement-authority-commitment.v1.json",
    "control/budgets/a2-execution-readiness-v1.json",
    "control/execution-envelope-a2-readiness-v1.yaml",
    "control/execution-envelope-a2-readiness-v2.yaml",
    "control/runbooks/A2_PER_ARM_AUTOINDEX_EXECUTION_V1.md",
    "src/myis_research/armindex/a2_candidate_freeze.py",
    "src/myis_research/armindex/a2_execution_readiness.py",
    "src/myis_research/armindex/a2_deployment_package.py",
    "src/myis_research/armindex/a2_measured_adapter.py",
    "src/myis_research/armindex/a2_owner_local_engine.py",
    "src/myis_research/armindex/a2_operational_executor.py",
    "src/myis_research/armindex/a2_remote_transport.py",
    "src/myis_research/armindex/a2_remote_candidate.py",
    "src/myis_research/armindex/a2_remote_retriever.py",
    "src/myis_research/armindex/a2_program_runtime.py",
    "src/myis_research/__init__.py",
    "src/myis_research/armindex/__init__.py",
    "src/myis_research/armindex/constants.py",
    "src/myis_research/armindex/contracts/__init__.py",
    "src/myis_research/armindex/contracts/_legacy.py",
    "src/myis_research/armindex/contracts/models.py",
    "src/myis_research/armindex/contracts/schema_registry.py",
    "src/myis_research/kernel/__init__.py",
    "src/myis_research/kernel/errors.py",
    "src/myis_research/kernel/failures.py",
    "src/myis_research/kernel/manifest.py",
    "src/myis_research/kernel/manifest_validation.py",
    "src/myis_research/kernel/models.py",
    "src/myis_research/armindex/a1_2_dense_overflow_adapter_v1.py",
    "src/myis_research/armindex/a1_2_measured_executor_v16.py",
    "src/myis_research/armindex/a1_2_owner_local_evaluator_v16.py",
    "src/myis_research/armindex/a1_2_safe_return_v16.py",
    "src/myis_research/armindex/a1_2_raw_materializer_bridge_v16.py",
    "src/myis_research/armindex/bm25s_adapter.py",
    "src/myis_research/armindex/scientific_common_programs_v11.py",
    "src/myis_research/armindex/autoindex.py",
    "src/myis_research/armindex/compiler.py",
    "src/myis_research/armindex/official_codex_bridge.py",
    "src/myis_research/kernel/canonical.py",
    "src/myis_research/kernel/p1.py",
    "src/myis_research/owner_local.py",
    "src/myis_research/protection.py",
)
_RETURN_MANIFEST = "A2_SAFE_RETURN_MANIFEST.json"


class A2ExecutionReadinessError(ValueError):
    """Raised when an A2 readiness operation fails closed."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A2ExecutionReadinessError(f"invalid JSON: {path}") from error
    if not isinstance(value, dict):
        raise A2ExecutionReadinessError(f"JSON object required: {path}")
    return value


def _validate(root: Path, name: str, value: Mapping[str, Any]) -> None:
    schema = _load_json(root / _SCHEMA_ROOT / name)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(value)),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if errors:
        raise A2ExecutionReadinessError(
            f"{name} validation failed: {errors[0].message}"
        )


def _require_hash(value: object, label: str) -> str:
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise A2ExecutionReadinessError(f"{label} must be a SHA-256")
    return value


def _self_hash(value: Mapping[str, Any], field: str) -> None:
    if value.get(field) != canonical_sha256(
        {key: item for key, item in value.items() if key != field}
    ):
        raise A2ExecutionReadinessError(f"{field} is invalid")


def _freeze_bindings(root: Path) -> dict[str, str]:
    replay = validate_candidate_freeze(root)
    return {
        "manifest_sha256": str(replay["manifest_sha256"]),
        "freeze_receipt_sha256": str(replay["receipt_sha256"]),
        "lock_sha256": str(replay["lock_sha256"]),
    }


def frozen_candidates(repository_root: Path) -> dict[str, dict[str, Any]]:
    """Return an immutable view of the existing 52-candidate manifest only."""

    root = repository_root.resolve()
    bindings = _freeze_bindings(root)
    manifest = _load_json(root / _MANIFEST)
    if manifest.get("manifest_sha256") != bindings["manifest_sha256"]:
        raise A2ExecutionReadinessError("manifest changed after freeze replay")
    rows = manifest.get("candidates")
    if not isinstance(rows, list) or len(rows) != 52:
        raise A2ExecutionReadinessError("frozen candidate manifest must have 52 candidates")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("candidate_id"), str):
            raise A2ExecutionReadinessError("frozen candidate is invalid")
        candidate_id = row["candidate_id"]
        if candidate_id in result:
            raise A2ExecutionReadinessError("frozen candidate identifiers are not unique")
        result[candidate_id] = dict(row)
    return result


def _candidate(root: Path, candidate_id: str) -> dict[str, Any]:
    candidate = frozen_candidates(root).get(candidate_id)
    if candidate is None:
        raise A2ExecutionReadinessError("candidate is absent from the frozen manifest")
    return candidate


def _receipt_id(attempt_id: str, suffix: str) -> str:
    if _ATTEMPT.fullmatch(attempt_id) is None:
        raise A2ExecutionReadinessError("attempt_id is invalid")
    stem = attempt_id.removeprefix("a2-")
    return f"a2-{stem}-{suffix}-v1"


def required_execution_bundle_paths() -> tuple[str, ...]:
    """Return the minimum immutable code/control closure for an A2 bundle."""

    return _BUNDLE_CLOSURE


def build_lifecycle_checkpoint(
    repository_root: Path,
    *,
    attempt_id: str,
    sequence: int,
    status: str,
    completed_candidate_count: int,
    failed_candidate_count: int,
    resume_allowed: bool,
    previous_checkpoint_sha256: str | None = None,
) -> dict[str, Any]:
    """Build one append-only checkpoint; it never records candidate outcomes."""

    root = repository_root.resolve()
    if _ATTEMPT.fullmatch(attempt_id) is None or sequence < 1:
        raise A2ExecutionReadinessError("attempt_id or sequence is invalid")
    if previous_checkpoint_sha256 is not None:
        _require_hash(previous_checkpoint_sha256, "previous checkpoint")
    if completed_candidate_count + failed_candidate_count > 52:
        raise A2ExecutionReadinessError("checkpoint candidate counts exceed frozen membership")
    if status in {"FAILED_CLOSED", "SAFE_RETURNED"} and resume_allowed:
        raise A2ExecutionReadinessError("terminal checkpoint cannot allow resume")
    body = {
        "schema_version": "myis.armindex-a2-lifecycle-checkpoint.v1",
        "checkpoint_id": f"{attempt_id}-checkpoint-{sequence:04d}",
        "attempt_id": attempt_id,
        "sequence": sequence,
        "previous_checkpoint_sha256": previous_checkpoint_sha256,
        "status": status,
        "completed_candidate_count": completed_candidate_count,
        "failed_candidate_count": failed_candidate_count,
        "resume_allowed": resume_allowed,
        "freeze_bindings": _freeze_bindings(root),
    }
    checkpoint = {**body, "checkpoint_sha256": canonical_sha256(body)}
    _validate(root, "a2-lifecycle-checkpoint.v1.json", checkpoint)
    return checkpoint


def append_lifecycle_checkpoint(ledger_path: Path, checkpoint: Mapping[str, Any]) -> None:
    """Append a checked checkpoint without rewriting historical ledger lines."""

    checkpoint = dict(checkpoint)
    _self_hash(checkpoint, "checkpoint_sha256")
    root = Path(__file__).resolve().parents[3]
    _validate(root, "a2-lifecycle-checkpoint.v1.json", checkpoint)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    if ledger_path.exists():
        try:
            prior = [
                json.loads(line)
                for line in ledger_path.read_text(encoding="utf-8").splitlines()
                if line
            ]
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise A2ExecutionReadinessError("checkpoint ledger is invalid") from error
        if prior:
            previous = prior[-1]
            _self_hash(previous, "checkpoint_sha256")
            _validate(root, "a2-lifecycle-checkpoint.v1.json", previous)
            if checkpoint["sequence"] != previous["sequence"] + 1:
                raise A2ExecutionReadinessError("checkpoint sequence is not append-only")
            if checkpoint["previous_checkpoint_sha256"] != previous["checkpoint_sha256"]:
                raise A2ExecutionReadinessError("checkpoint chain is broken")
    elif checkpoint["sequence"] != 1 or checkpoint["previous_checkpoint_sha256"] is not None:
        raise A2ExecutionReadinessError("first checkpoint must be sequence one")
    with ledger_path.open("a", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps(checkpoint, ensure_ascii=True, sort_keys=True) + "\n")


def resume_checkpoint(ledger_path: Path, *, attempt_id: str) -> dict[str, Any]:
    """Return the sole valid resume point, or fail closed."""

    if not ledger_path.is_file():
        raise A2ExecutionReadinessError("checkpoint ledger is absent")
    try:
        rows = [
            json.loads(line)
            for line in ledger_path.read_text(encoding="utf-8").splitlines()
            if line
        ]
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A2ExecutionReadinessError("checkpoint ledger is invalid") from error
    if not rows:
        raise A2ExecutionReadinessError("checkpoint ledger is empty")
    prior: str | None = None
    for index, row in enumerate(rows, start=1):
        if row.get("attempt_id") != attempt_id or row.get("sequence") != index:
            raise A2ExecutionReadinessError("checkpoint ledger identity drift")
        _self_hash(row, "checkpoint_sha256")
        _validate(
            Path(__file__).resolve().parents[3],
            "a2-lifecycle-checkpoint.v1.json",
            row,
        )
        if row.get("previous_checkpoint_sha256") != prior:
            raise A2ExecutionReadinessError("checkpoint ledger chain drift")
        prior = row["checkpoint_sha256"]
    last = rows[-1]
    if last.get("status") in {"FAILED_CLOSED", "SAFE_RETURNED"} or not last.get("resume_allowed"):
        raise A2ExecutionReadinessError("terminal checkpoint cannot resume")
    return last


def validate_execution_ledger(
    repository_root: Path, ledger_path: Path
) -> list[dict[str, Any]]:
    """Validate an A2 material-event ledger as one append-only hash chain."""

    try:
        rows = [
            json.loads(line)
            for line in ledger_path.read_text(encoding="utf-8").splitlines()
            if line
        ]
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A2ExecutionReadinessError("execution ledger is invalid") from error
    if not rows:
        raise A2ExecutionReadinessError("execution ledger is empty")
    root = repository_root.resolve()
    attempt_id = rows[0].get("attempt_id")
    prior: str | None = None
    for row in rows:
        if row.get("attempt_id") != attempt_id:
            raise A2ExecutionReadinessError("execution ledger attempt identity drift")
        _self_hash(row, "entry_sha256")
        schema_version = row.get("schema_version")
        schema_name = {
            "myis.armindex-a2-execution-ledger-entry.v1": (
                "a2-execution-ledger-entry.v1.json"
            ),
            "myis.armindex-a2-execution-ledger-entry.v2": (
                "a2-execution-ledger-entry.v2.json"
            ),
            "myis.armindex-a2-execution-ledger-entry.v3": (
                "a2-execution-ledger-entry.v3.json"
            ),
        }.get(schema_version)
        if schema_name is None:
            raise A2ExecutionReadinessError("execution ledger schema version is invalid")
        _validate(root, schema_name, row)
        _validate_freeze_bindings(root, row["freeze_bindings"])
        if row.get("previous_entry_sha256") != prior:
            raise A2ExecutionReadinessError("execution ledger chain drift")
        prior = row["entry_sha256"]
    return rows


def build_train_evaluation_receipt(
    repository_root: Path,
    *,
    attempt_id: str,
    candidate_id: str,
    aggregate_fixture: Mapping[str, Any],
    allow_synthetic_fixture: bool = False,
) -> dict[str, Any]:
    """Bind a synthetic aggregate-only fixture to one frozen candidate.

    Production callers cannot use this helper to submit measured outcomes:
    ``allow_synthetic_fixture`` is intentionally an explicit test-only gate.
    """

    if not allow_synthetic_fixture:
        raise A2ExecutionReadinessError("synthetic aggregate fixtures are test-only")
    root = repository_root.resolve()
    candidate = _candidate(root, candidate_id)
    fixture = dict(aggregate_fixture)
    if fixture.get("fixture_kind") != "synthetic_a2_aggregate_v1":
        raise A2ExecutionReadinessError("only the synthetic aggregate fixture is accepted")
    if fixture.get("rep_dev_measured") is not False or fixture.get("per_query_outcomes_included") is not False:
        raise A2ExecutionReadinessError("fixture crosses the protected/REP-DEV boundary")
    metrics = fixture.get("metrics")
    if not isinstance(metrics, Mapping) or not metrics:
        raise A2ExecutionReadinessError("synthetic fixture requires aggregate metrics")
    assert_aggregate_only(fixture)
    body = {
        "schema_version": "myis.armindex-a2-train-evaluation-receipt.v1",
        "receipt_id": _receipt_id(attempt_id, f"{candidate_id}-train-evaluation"),
        "attempt_id": attempt_id,
        "status": "PASS_A2_TRAIN_EVALUATION",
        "candidate_id": candidate_id,
        "arm_id": candidate["arm_id"],
        "aggregate_metrics_sha256": canonical_sha256(fixture),
        "aggregate_metric_count": len(metrics),
        "train_only": True,
        "rep_dev_measured": False,
        "per_query_outcomes_included": False,
        "freeze_bindings": _freeze_bindings(root),
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _validate(root, "a2-train-evaluation-receipt.v1.json", receipt)
    return receipt


def build_winner_receipt(
    repository_root: Path,
    *,
    attempt_id: str,
    arm_id: str,
    winner_candidate_id: str,
    train_evaluation_receipt_sha256: str,
    strict_tie_rejected: bool,
) -> dict[str, Any]:
    """Build a schema-bound per-arm winner receipt from frozen membership only."""

    root = repository_root.resolve()
    candidate = _candidate(root, winner_candidate_id)
    if candidate.get("arm_id") != arm_id:
        raise A2ExecutionReadinessError("winner does not belong to the requested arm")
    _require_hash(train_evaluation_receipt_sha256, "train evaluation receipt")
    if strict_tie_rejected is not True:
        raise A2ExecutionReadinessError("winner receipt requires strict tie rejection")
    diagnostic = bool(candidate["diagnostic_non_advancing"])
    eligible = bool(candidate["advancement_eligible"])
    if diagnostic == eligible or (arm_id in {"ARM-01", "ARM-02"}) != diagnostic:
        raise A2ExecutionReadinessError("diagnostic/advancement policy drift")
    body = {
        "schema_version": "myis.armindex-a2-winner-selection-receipt.v1",
        "receipt_id": _receipt_id(attempt_id, f"{arm_id.lower()}-winner"),
        "attempt_id": attempt_id,
        "status": "PASS_A2_WINNER_SELECTED",
        "arm_id": arm_id,
        "winner_candidate_id": winner_candidate_id,
        "diagnostic_non_advancing": diagnostic,
        "advancement_eligible": eligible,
        "train_evaluation_receipt_sha256": train_evaluation_receipt_sha256,
        "strict_tie_rejected": True,
        "freeze_bindings": _freeze_bindings(root),
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _validate(root, "a2-winner-selection-receipt.v1.json", receipt)
    return receipt


def build_safe_return_receipt(
    repository_root: Path,
    *,
    attempt_id: str,
    archive_path: Path,
    remote_root: str,
) -> dict[str, Any]:
    """Validate an aggregate-only return archive before binding it to A2."""

    root = repository_root.resolve()
    if _REMOTE_ROOT.fullmatch(remote_root) is None:
        raise A2ExecutionReadinessError("remote root is not an isolated A2 root")
    archive = archive_path.resolve()
    if not archive.is_file() or archive.is_symlink():
        raise A2ExecutionReadinessError("safe-return archive is missing or unsafe")
    try:
        with tarfile.open(archive, "r:gz") as bundle:
            members = bundle.getmembers()
            names = [member.name for member in members]
            if (
                len(names) != len(set(names))
                or _RETURN_MANIFEST not in names
                or any(
                    not member.isreg()
                    or Path(member.name).is_absolute()
                    or ".." in Path(member.name).parts
                    or _FORBIDDEN_MEMBER.search(member.name)
                    for member in members
                    if member.name != _RETURN_MANIFEST
                )
            ):
                raise A2ExecutionReadinessError("safe-return archive members are unsafe")
            stream = bundle.extractfile(_RETURN_MANIFEST)
            if stream is None:
                raise A2ExecutionReadinessError("safe-return archive manifest is missing")
            manifest = json.loads(stream.read().decode("ascii"))
            if not isinstance(manifest, Mapping):
                raise A2ExecutionReadinessError("safe-return archive manifest is invalid")
            manifest = dict(manifest)
            manifest_hash = manifest.get("archive_manifest_sha256")
            _require_hash(manifest_hash, "safe-return archive manifest")
            if manifest_hash != canonical_sha256(
                {key: value for key, value in manifest.items() if key != "archive_manifest_sha256"}
            ):
                raise A2ExecutionReadinessError("safe-return archive manifest hash drift")
            if manifest.get("attempt_id") != attempt_id or manifest.get("protected_payload_included") is not False:
                raise A2ExecutionReadinessError("safe-return archive identity or boundary drift")
            rows = manifest.get("members")
            if not isinstance(rows, list) or not rows:
                raise A2ExecutionReadinessError("safe-return archive has no aggregate members")
            expected = {_RETURN_MANIFEST}
            for row in rows:
                if not isinstance(row, Mapping) or set(row) != {"path", "sha256", "size_bytes"}:
                    raise A2ExecutionReadinessError("safe-return manifest member is invalid")
                path = row["path"]
                if not isinstance(path, str) or _FORBIDDEN_MEMBER.search(path):
                    raise A2ExecutionReadinessError("safe-return member crosses protected boundary")
                stream = bundle.extractfile(path)
                if stream is None or file_sha256_from_stream(stream) != row["sha256"]:
                    raise A2ExecutionReadinessError("safe-return member hash drift")
                if bundle.getmember(path).size != row["size_bytes"]:
                    raise A2ExecutionReadinessError("safe-return member size drift")
                expected.add(path)
            if set(names) != expected:
                raise A2ExecutionReadinessError("safe-return members differ from manifest")
    except (OSError, tarfile.TarError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise A2ExecutionReadinessError("safe-return archive cannot be validated") from error
    body = {
        "schema_version": "myis.armindex-a2-safe-return-receipt.v1",
        "receipt_id": _receipt_id(attempt_id, "safe-return"),
        "attempt_id": attempt_id,
        "status": "PASS_A2_SAFE_RETURN",
        "archive_sha256": file_sha256(archive),
        "archive_manifest_sha256": manifest_hash,
        "aggregate_artifact_count": len(rows),
        "protected_payload_included": False,
        "remote_root": remote_root,
        "freeze_bindings": _freeze_bindings(root),
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _validate(root, "a2-safe-return-receipt.v1.json", receipt)
    return receipt


def build_execution_bundle(
    repository_root: Path,
    *,
    attempt_id: str,
    output_path: Path,
) -> dict[str, Any]:
    """Create a deterministic local code/control bundle; no staging is performed."""

    root = repository_root.resolve()
    if output_path.resolve().is_relative_to(root):
        raise A2ExecutionReadinessError("bundle output must remain outside the repository")
    git_commit = _git(root, "rev-parse", "HEAD^{commit}")
    git_tree = _git(root, "rev-parse", "HEAD^{tree}")
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise A2ExecutionReadinessError("bundle needs a clean worktree")
    if _git(root, "rev-parse", "origin/main") != git_commit:
        raise A2ExecutionReadinessError("bundle needs main synchronized with origin/main")
    source_paths = _BUNDLE_CLOSURE
    paths: list[Path] = []
    for relative in sorted(source_paths):
        if _FORBIDDEN_MEMBER.search(relative):
            raise A2ExecutionReadinessError("bundle path crosses protected boundary")
        path = (root / relative).resolve()
        if not path.is_file() or path.is_symlink() or not path.is_relative_to(root):
            raise A2ExecutionReadinessError("bundle source is unsafe")
        paths.append(path)
    manifest_body = {
        "schema_version": "myis.armindex-a2-execution-bundle.v1",
        "attempt_id": attempt_id,
        "freeze_bindings": _freeze_bindings(root),
        "paths": sorted(source_paths),
        "files": [
            {"path": path.relative_to(root).as_posix(), "sha256": file_sha256(path), "size_bytes": path.stat().st_size}
            for path in paths
        ],
        "git_commit": git_commit,
        "git_tree": git_tree,
        "protected_payload_included": False,
    }
    manifest = {**manifest_body, "bundle_manifest_sha256": canonical_sha256(manifest_body)}
    output = output_path.resolve()
    if output.exists():
        raise A2ExecutionReadinessError("bundle output already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=output.parent, prefix=f".{output.name}.")
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with temporary.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as zipped, tarfile.open(fileobj=zipped, mode="w") as archive:
            for path in paths:
                data = path.read_bytes()
                info = tarfile.TarInfo(path.relative_to(root).as_posix())
                info.size, info.mtime, info.mode = len(data), 0, 0o644
                archive.addfile(info, BytesIO(data))
            encoded = (json.dumps(manifest, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
            info = tarfile.TarInfo("BUNDLE_MANIFEST.json")
            info.size, info.mtime, info.mode = len(encoded), 0, 0o644
            archive.addfile(info, BytesIO(encoded))
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    body = {
        "schema_version": "myis.armindex-a2-execution-bundle-receipt.v1",
        "receipt_id": _receipt_id(attempt_id, "bundle"),
        "attempt_id": attempt_id,
        "status": "PASS_CLEAN_HASH_BOUND_A2_BUNDLE",
        "clean_worktree": True,
        "pushed_to_origin_main": True,
        "git_commit": git_commit,
        "git_tree": git_tree,
        "freeze_bindings": manifest["freeze_bindings"],
        "bundle_sha256": file_sha256(output),
        "bundle_manifest_sha256": manifest["bundle_manifest_sha256"],
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _validate(root, "a2-execution-bundle-receipt.v1.json", receipt)
    return {"receipt": receipt, "manifest": manifest}


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode:
        raise A2ExecutionReadinessError("Git identity cannot be verified")
    return result.stdout.strip()


def validate_execution_bundle(repository_root: Path, *, bundle_path: Path, receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Verify archive members and the receipt without extracting to disk."""

    root = repository_root.resolve()
    checked = dict(receipt)
    _self_hash(checked, "receipt_sha256")
    _validate(root, "a2-execution-bundle-receipt.v1.json", checked)
    if file_sha256(bundle_path) != checked["bundle_sha256"]:
        raise A2ExecutionReadinessError("execution bundle hash drift")
    with tarfile.open(bundle_path, "r:gz") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)) or any(not member.isreg() or ".." in Path(member.name).parts for member in members):
            raise A2ExecutionReadinessError("execution bundle members are unsafe")
        stream = archive.extractfile("BUNDLE_MANIFEST.json")
        if stream is None:
            raise A2ExecutionReadinessError("execution bundle manifest is missing")
        manifest = json.loads(stream.read().decode("ascii"))
        if manifest.get("bundle_manifest_sha256") != checked["bundle_manifest_sha256"]:
            raise A2ExecutionReadinessError("execution bundle manifest binding drift")
        if manifest.get("bundle_manifest_sha256") != canonical_sha256(
            {
                key: value
                for key, value in manifest.items()
                if key != "bundle_manifest_sha256"
            }
        ):
            raise A2ExecutionReadinessError("execution bundle manifest self-hash drift")
        if (
            manifest.get("paths") != sorted(_BUNDLE_CLOSURE)
            or manifest.get("git_commit") != checked["git_commit"]
            or manifest.get("git_tree") != checked["git_tree"]
            or manifest.get("freeze_bindings") != checked["freeze_bindings"]
            or manifest.get("protected_payload_included") is not False
        ):
            raise A2ExecutionReadinessError("execution bundle closure or identity drift")
        rows = manifest.get("files")
        if not isinstance(rows, list) or not rows:
            raise A2ExecutionReadinessError("execution bundle file manifest is invalid")
        if [row.get("path") for row in rows if isinstance(row, Mapping)] != sorted(
            _BUNDLE_CLOSURE
        ):
            raise A2ExecutionReadinessError("execution bundle file closure drift")
        for row in rows:
            if not isinstance(row, Mapping) or _FORBIDDEN_MEMBER.search(
                str(row.get("path", ""))
            ):
                raise A2ExecutionReadinessError(
                    "execution bundle member crosses protected boundary"
                )
            stream = archive.extractfile(row["path"])
            if stream is None or file_sha256_from_stream(stream) != row["sha256"]:
                raise A2ExecutionReadinessError("execution bundle member hash drift")
    return {**checked, "validation_status": "PASS"}


def file_sha256_from_stream(stream: Any) -> str:
    import hashlib

    digest = hashlib.sha256()
    while chunk := stream.read(1024 * 1024):
        digest.update(chunk)
    return digest.hexdigest()


def _timestamp(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        raise A2ExecutionReadinessError(f"{label} timestamp is invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise A2ExecutionReadinessError(f"{label} timestamp is invalid") from error
    if parsed.tzinfo is None:
        raise A2ExecutionReadinessError(f"{label} timestamp must include UTC offset")
    return parsed.astimezone(timezone.utc)


def _money(value: object, label: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise A2ExecutionReadinessError(f"{label} is not a decimal amount") from error
    if not result.is_finite() or result < 0:
        raise A2ExecutionReadinessError(f"{label} is not a non-negative amount")
    return result


def _validate_freeze_bindings(root: Path, value: Mapping[str, Any]) -> None:
    if dict(value) != _freeze_bindings(root):
        raise A2ExecutionReadinessError("receipt freeze bindings drift")


def _source_hashes(paths: Mapping[str, Path]) -> dict[str, str]:
    if set(paths) != _REQUIRED_PROVIDER_SOURCES:
        raise A2ExecutionReadinessError("provider source artifact set is incomplete")
    result: dict[str, str] = {}
    for name in sorted(paths):
        path = Path(paths[name]).resolve()
        if not path.is_file() or path.is_symlink():
            raise A2ExecutionReadinessError(f"provider {name} source artifact is unsafe")
        result[name] = file_sha256(path)
    return result


def _provider_observation(
    root: Path,
    *,
    attempt_id: str,
    provider_observation_path: Path,
    source_artifact_paths: Mapping[str, Path],
) -> tuple[dict[str, Any], str, dict[str, str]]:
    path = provider_observation_path.resolve()
    if not path.is_file() or path.is_symlink():
        raise A2ExecutionReadinessError("provider observation artifact is unsafe")
    observation = _load_json(path)
    assert_aggregate_only(observation)
    _self_hash(observation, "observation_sha256")
    _validate(root, "a2-provider-observation.v1.json", observation)
    if observation["attempt_id"] != attempt_id:
        raise A2ExecutionReadinessError("provider observation attempt differs from admission")
    source_hashes = _source_hashes(source_artifact_paths)
    if observation["source_artifact_sha256"] != source_hashes:
        raise A2ExecutionReadinessError("provider source artifact bytes drift")
    bindings = observation.get("source_artifacts")
    if not isinstance(bindings, Mapping) or set(bindings) != _REQUIRED_PROVIDER_SOURCES:
        raise A2ExecutionReadinessError("provider source artifact provenance is incomplete")
    for name, field in (
        ("runtime", "runtime_sha256"),
        ("model_lockset", "model_lockset_sha256"),
        ("data_handoff", "data_handoff_sha256"),
        ("ssh_host_key", "ssh_host_key_sha256"),
        ("management_authority", "management_authority_sha256"),
    ):
        if observation[field] != source_hashes[name]:
            raise A2ExecutionReadinessError(f"provider {name} observation binding drift")
        binding = bindings[name]
        if (
            not isinstance(binding, Mapping)
            or binding.get("file_sha256") != source_hashes[name]
            or not isinstance(binding.get("uri"), str)
        ):
            raise A2ExecutionReadinessError(f"provider {name} source provenance drift")
    return observation, file_sha256(path), source_hashes


def build_provider_admission_receipt(
    repository_root: Path,
    *,
    attempt_id: str,
    provider_observation_path: Path,
    source_artifact_paths: Mapping[str, Path],
    now_utc: datetime,
    maximum_quote_age: timedelta = timedelta(minutes=15),
) -> dict[str, Any]:
    """Build a PASS receipt only from fresh, complete local admission evidence.

    ``provider_evidence`` is an already-sanitized observation.  This function
    performs no provider interaction and rejects estimates, partial fees, old
    quotes, the wrong instance, or an over-limit all-fee workload total.
    """

    root = repository_root.resolve()
    if now_utc.tzinfo is None:
        raise A2ExecutionReadinessError("now_utc must include an offset")
    evidence, observation_file_sha256, source_hashes = _provider_observation(
        root,
        attempt_id=attempt_id,
        provider_observation_path=provider_observation_path,
        source_artifact_paths=source_artifact_paths,
    )
    if evidence.get("provider_instance_id") != "47411176":
        raise A2ExecutionReadinessError("provider instance is not 47411176")
    if evidence.get("provider_status") != "RUNNING" or evidence.get(
        "provider_verification"
    ) != "VERIFIED":
        raise A2ExecutionReadinessError("provider instance is not running and verified")
    if evidence.get("gpu_count") != 4 or evidence.get("gpu_model") != "RTX3090":
        raise A2ExecutionReadinessError("provider GPU identity is not 4x RTX3090")
    if evidence.get("vram_mib_each") != 24576:
        raise A2ExecutionReadinessError("provider GPU VRAM identity is not 24576 MiB")
    mode = evidence.get("source_mode")
    if mode not in {"authenticated_vast_cli", "OwnerDashboardSsh"}:
        raise A2ExecutionReadinessError("provider evidence mode is unsupported")
    authenticated = evidence.get("provider_authenticated")
    if not isinstance(authenticated, bool) or (
        mode == "OwnerDashboardSsh" and authenticated
    ):
        raise A2ExecutionReadinessError("provider authentication evidence is inconsistent")
    if evidence.get("login_or_logout_performed") is not False:
        raise A2ExecutionReadinessError("provider login/logout is forbidden")
    observed_at = _timestamp(evidence.get("observed_at_utc"), "provider observation")
    observed = _timestamp(evidence.get("quote_observed_at_utc"), "quote")
    current = now_utc.astimezone(timezone.utc)
    if (
        observed_at > current
        or current - observed_at > maximum_quote_age
        or observed > current
        or current - observed > maximum_quote_age
    ):
        raise A2ExecutionReadinessError("provider quote is not fresh")
    ttl_deadline = _timestamp(evidence.get("ttl_deadline_utc"), "provider TTL deadline")
    remaining_ttl_seconds = int((ttl_deadline - current).total_seconds())
    if remaining_ttl_seconds < _REQUIRED_TTL_SECONDS:
        raise A2ExecutionReadinessError("NEEDS_OWNER_TTL_EXTENSION")
    expected_remaining = int((ttl_deadline - observed_at).total_seconds())
    if evidence.get("remaining_ttl_seconds") != expected_remaining:
        raise A2ExecutionReadinessError("provider observation remaining TTL drift")
    components = evidence.get("all_fee_components_usd")
    if not isinstance(components, Mapping) or set(components) != _REQUIRED_QUOTE_COMPONENTS:
        raise A2ExecutionReadinessError("all required quote fee components are required")
    total = sum((_money(components[name], name) for name in sorted(components)), Decimal())
    declared_total = _money(evidence.get("whole_workload_total_usd"), "whole workload total")
    if total != declared_total or total > Decimal("35"):
        raise A2ExecutionReadinessError("whole-workload all-fee quote exceeds the A2 hard stop")
    quote_body = {
        "provider_instance_id": evidence["provider_instance_id"],
        "quote_observed_at_utc": evidence["quote_observed_at_utc"],
        "ttl_deadline_utc": evidence["ttl_deadline_utc"],
        "all_fee_components_usd": dict(components),
        "whole_workload_total_usd": str(declared_total),
    }
    quote_sha256 = canonical_sha256(quote_body)
    budget_sha256 = canonical_sha256(
        {"quote_sha256": quote_sha256, "whole_workload_total_usd": str(total), "hard_stop_usd": "35"}
    )
    management_mode = evidence.get("management_mode")
    manual_ready = evidence.get("owner_manual_dashboard_destroy_ready")
    if mode == "authenticated_vast_cli":
        if authenticated is not True or management_mode != "AUTHENTICATED_CLI":
            raise A2ExecutionReadinessError("authenticated CLI management authority is missing")
    elif (
        management_mode != "OWNER_MANUAL_DASHBOARD_DESTROY_READY"
        or manual_ready is not True
    ):
        raise A2ExecutionReadinessError("Owner dashboard destruction readiness is missing")
    if evidence.get("provider_destroy_performed") is not False:
        raise A2ExecutionReadinessError("provider destruction is forbidden")
    body = {
        "schema_version": "myis.armindex-a2-provider-admission-receipt.v1",
        "receipt_id": _receipt_id(attempt_id, "provider-admission"),
        "attempt_id": attempt_id,
        "status": "PASS_A2_PROVIDER_ADMISSION",
        "observed_at_utc": evidence["observed_at_utc"],
        "quote_observed_at_utc": evidence["quote_observed_at_utc"],
        "provider_instance_id": "47411176",
        "provider_status": "RUNNING",
        "provider_verification": "VERIFIED",
        "evidence_mode": mode,
        "provider_authenticated": authenticated,
        "login_or_logout_performed": False,
        "gpu_count": 4,
        "gpu_model": "RTX3090",
        "vram_mib_each": 24576,
        "gpu_uuid_set_sha256": evidence["gpu_uuid_set_sha256"],
        "runtime_sha256": source_hashes["runtime"],
        "model_lockset_sha256": source_hashes["model_lockset"],
        "data_handoff_sha256": source_hashes["data_handoff"],
        "ssh_host_key_sha256": source_hashes["ssh_host_key"],
        "all_fee_components_usd": {
            name: str(_money(components[name], name)) for name in sorted(components)
        },
        "whole_workload_total_usd": str(declared_total),
        "quote_sha256": quote_sha256,
        "whole_workload_budget_sha256": budget_sha256,
        "management_mode": management_mode,
        "management_authority_sha256": source_hashes["management_authority"],
        "owner_manual_dashboard_destroy_ready": bool(manual_ready),
        "provider_destroy_performed": False,
        "provider_observation_sha256": evidence["observation_sha256"],
        "provider_observation_file_sha256": observation_file_sha256,
        "source_artifact_sha256": source_hashes,
        "ttl_deadline_utc": evidence["ttl_deadline_utc"],
        "remaining_ttl_seconds": remaining_ttl_seconds,
        "forward_hard_stop_usd": 35,
        "freeze_bindings": _freeze_bindings(root),
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _validate(root, "a2-provider-admission-receipt.v1.json", receipt)
    return receipt


def validate_provider_admission_receipt(
    repository_root: Path,
    receipt: Mapping[str, Any],
    *,
    provider_observation_path: Path | None = None,
    source_artifact_paths: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    """Validate admission and, when supplied, its current source artifact bytes."""

    root = repository_root.resolve()
    checked = dict(receipt)
    _self_hash(checked, "receipt_sha256")
    _validate(root, "a2-provider-admission-receipt.v1.json", checked)
    _validate_freeze_bindings(root, checked["freeze_bindings"])
    if (provider_observation_path is None) != (source_artifact_paths is None):
        raise A2ExecutionReadinessError("provider admission source paths are incomplete")
    if provider_observation_path is not None and source_artifact_paths is not None:
        try:
            observation, observation_file_hash, source_hashes = _provider_observation(
                root,
                attempt_id=str(checked["attempt_id"]),
                provider_observation_path=provider_observation_path,
                source_artifact_paths=source_artifact_paths,
            )
        except A2ExecutionReadinessError as error:
            raise A2ExecutionReadinessError(
                "provider admission source artifact bytes drift after receipt mutation"
            ) from error
        if (
            observation["observation_sha256"] != checked["provider_observation_sha256"]
            or observation_file_hash != checked["provider_observation_file_sha256"]
            or source_hashes != checked["source_artifact_sha256"]
        ):
            raise A2ExecutionReadinessError("provider admission source artifact mutation")
    return checked


def _provider_observation_v2(
    root: Path,
    *,
    attempt_id: str,
    provider_observation_path: Path,
    source_artifact_paths: Mapping[str, Path],
) -> tuple[dict[str, Any], str, dict[str, str]]:
    """Load a fresh-instance observation without accepting caller-supplied hashes."""

    path = provider_observation_path.resolve()
    if not path.is_file() or path.is_symlink():
        raise A2ExecutionReadinessError("provider observation artifact is unsafe")
    observation = _load_json(path)
    assert_aggregate_only(observation)
    _self_hash(observation, "observation_sha256")
    _validate(root, "a2-provider-observation.v2.json", observation)
    if observation["attempt_id"] != attempt_id:
        raise A2ExecutionReadinessError("provider observation attempt differs from admission")
    if (
        _FRESH_INSTANCE_ID.fullmatch(str(observation["provider_instance_id"])) is None
        or str(observation["provider_instance_id"]) in _DESTROYED_PROVIDER_INSTANCE_IDS
    ):
        raise A2ExecutionReadinessError("provider instance ID is unsafe")
    source_hashes = _source_hashes(source_artifact_paths)
    if observation["source_artifact_sha256"] != source_hashes:
        raise A2ExecutionReadinessError("provider source artifact bytes drift")
    bindings = observation.get("source_artifacts")
    if not isinstance(bindings, Mapping) or set(bindings) != _REQUIRED_PROVIDER_SOURCES:
        raise A2ExecutionReadinessError("provider source artifact provenance is incomplete")
    for name, field in (
        ("runtime", "runtime_sha256"),
        ("model_lockset", "model_lockset_sha256"),
        ("data_handoff", "data_handoff_sha256"),
        ("ssh_host_key", "ssh_host_key_sha256"),
        ("management_authority", "management_authority_sha256"),
    ):
        binding = bindings[name]
        if (
            observation[field] != source_hashes[name]
            or not isinstance(binding, Mapping)
            or binding.get("file_sha256") != source_hashes[name]
            or not isinstance(binding.get("uri"), str)
        ):
            raise A2ExecutionReadinessError(f"provider {name} observation binding drift")
    return observation, file_sha256(path), source_hashes


def build_provider_instance_binding(
    repository_root: Path,
    *,
    attempt_id: str,
    provider_observation_path: Path,
    source_artifact_paths: Mapping[str, Path],
) -> dict[str, Any]:
    """Bind one newly observed Vast instance to its immutable local evidence."""

    root = repository_root.resolve()
    observation, observation_file_sha256, source_hashes = _provider_observation_v2(
        root,
        attempt_id=attempt_id,
        provider_observation_path=provider_observation_path,
        source_artifact_paths=source_artifact_paths,
    )
    body = {
        "schema_version": "myis.armindex-a2-provider-instance-binding.v1",
        "binding_id": _receipt_id(attempt_id, "provider-instance-binding"),
        "attempt_id": attempt_id,
        "status": "PASS_A2_FRESH_INSTANCE_BINDING",
        "provider_label": "Vast",
        "provider_instance_id": observation["provider_instance_id"],
        "observed_at_utc": observation["observed_at_utc"],
        "provider_observation_sha256": observation["observation_sha256"],
        "provider_observation_file_sha256": observation_file_sha256,
        "source_artifact_sha256": source_hashes,
    }
    binding = {**body, "binding_sha256": canonical_sha256(body)}
    _validate(root, "a2-provider-instance-binding.v1.json", binding)
    return binding


def validate_provider_instance_binding(
    repository_root: Path,
    binding: Mapping[str, Any],
    *,
    provider_observation_path: Path | None = None,
    source_artifact_paths: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    """Validate a fresh binding and, when available, its immutable source bytes."""

    root = repository_root.resolve()
    checked = dict(binding)
    _self_hash(checked, "binding_sha256")
    _validate(root, "a2-provider-instance-binding.v1.json", checked)
    if str(checked["provider_instance_id"]) in _DESTROYED_PROVIDER_INSTANCE_IDS:
        raise A2ExecutionReadinessError(
            "provider instance binding targets a destroyed instance"
        )
    if (provider_observation_path is None) != (source_artifact_paths is None):
        raise A2ExecutionReadinessError("provider binding source paths are incomplete")
    if provider_observation_path is not None and source_artifact_paths is not None:
        observation, observation_file_sha256, source_hashes = _provider_observation_v2(
            root,
            attempt_id=str(checked["attempt_id"]),
            provider_observation_path=provider_observation_path,
            source_artifact_paths=source_artifact_paths,
        )
        if (
            observation["provider_instance_id"] != checked["provider_instance_id"]
            or observation["observation_sha256"] != checked["provider_observation_sha256"]
            or observation_file_sha256 != checked["provider_observation_file_sha256"]
            or source_hashes != checked["source_artifact_sha256"]
        ):
            raise A2ExecutionReadinessError("provider instance binding source artifact mutation")
    return checked


def build_provider_admission_receipt_v2(
    repository_root: Path,
    *,
    attempt_id: str,
    provider_observation_path: Path,
    source_artifact_paths: Mapping[str, Path],
    instance_binding: Mapping[str, Any],
    now_utc: datetime,
    maximum_quote_age: timedelta = timedelta(minutes=15),
) -> dict[str, Any]:
    """Admit only the runtime-supplied instance authenticated by a v2 binding."""

    root = repository_root.resolve()
    if now_utc.tzinfo is None:
        raise A2ExecutionReadinessError("now_utc must include an offset")
    evidence, observation_file_sha256, source_hashes = _provider_observation_v2(
        root,
        attempt_id=attempt_id,
        provider_observation_path=provider_observation_path,
        source_artifact_paths=source_artifact_paths,
    )
    binding = validate_provider_instance_binding(
        root,
        instance_binding,
        provider_observation_path=provider_observation_path,
        source_artifact_paths=source_artifact_paths,
    )
    if binding["attempt_id"] != attempt_id or binding["provider_instance_id"] != evidence["provider_instance_id"]:
        raise A2ExecutionReadinessError("fresh provider instance binding drift")
    if evidence.get("provider_status") != "RUNNING" or evidence.get("provider_verification") != "VERIFIED":
        raise A2ExecutionReadinessError("provider instance is not running and verified")
    if (evidence.get("gpu_count"), evidence.get("gpu_model"), evidence.get("vram_mib_each")) != (4, "RTX3090", 24576):
        raise A2ExecutionReadinessError("provider GPU identity is not 4x RTX3090 with 24576 MiB")
    mode = evidence.get("source_mode")
    authenticated = evidence.get("provider_authenticated")
    if mode not in {"authenticated_vast_cli", "OwnerDashboardSsh"} or not isinstance(authenticated, bool):
        raise A2ExecutionReadinessError("provider evidence mode is unsupported")
    if (mode == "OwnerDashboardSsh" and authenticated) or evidence.get("login_or_logout_performed") is not False:
        raise A2ExecutionReadinessError("provider authentication evidence is inconsistent")
    current = now_utc.astimezone(timezone.utc)
    observed_at = _timestamp(evidence.get("observed_at_utc"), "provider observation")
    quote_observed = _timestamp(evidence.get("quote_observed_at_utc"), "quote")
    if any(value > current or current - value > maximum_quote_age for value in (observed_at, quote_observed)):
        raise A2ExecutionReadinessError("provider quote is not fresh")
    ttl_deadline = _timestamp(evidence.get("ttl_deadline_utc"), "provider TTL deadline")
    remaining_ttl_seconds = int((ttl_deadline - current).total_seconds())
    if remaining_ttl_seconds < _REQUIRED_TTL_SECONDS:
        raise A2ExecutionReadinessError("NEEDS_OWNER_TTL_EXTENSION")
    if evidence.get("remaining_ttl_seconds") != int((ttl_deadline - observed_at).total_seconds()):
        raise A2ExecutionReadinessError("provider observation remaining TTL drift")
    components = evidence.get("all_fee_components_usd")
    if not isinstance(components, Mapping) or set(components) != _REQUIRED_QUOTE_COMPONENTS:
        raise A2ExecutionReadinessError("all required quote fee components are required")
    total = sum((_money(components[name], name) for name in sorted(components)), Decimal())
    declared_total = _money(evidence.get("whole_workload_total_usd"), "whole workload total")
    if total != declared_total or total > Decimal("35"):
        raise A2ExecutionReadinessError("whole-workload all-fee quote exceeds the A2 hard stop")
    management_mode = evidence.get("management_mode")
    manual_ready = evidence.get("owner_manual_dashboard_destroy_ready")
    if mode == "authenticated_vast_cli":
        management_ok = authenticated is True and management_mode == "AUTHENTICATED_CLI"
    else:
        management_ok = management_mode == "OWNER_MANUAL_DASHBOARD_DESTROY_READY" and manual_ready is True
    if not management_ok or evidence.get("provider_destroy_performed") is not False:
        raise A2ExecutionReadinessError("provider management authority is invalid")
    quote_sha256 = canonical_sha256({
        "provider_instance_id": evidence["provider_instance_id"], "quote_observed_at_utc": evidence["quote_observed_at_utc"],
        "ttl_deadline_utc": evidence["ttl_deadline_utc"], "all_fee_components_usd": dict(components),
        "whole_workload_total_usd": str(declared_total),
    })
    budget_sha256 = canonical_sha256({"quote_sha256": quote_sha256, "whole_workload_total_usd": str(total), "hard_stop_usd": "35"})
    body = {
        "schema_version": "myis.armindex-a2-provider-admission-receipt.v2",
        "receipt_id": _receipt_id(attempt_id, "provider-admission").removesuffix("-v1") + "-v2",
        "attempt_id": attempt_id, "status": "PASS_A2_PROVIDER_ADMISSION",
        "observed_at_utc": evidence["observed_at_utc"], "quote_observed_at_utc": evidence["quote_observed_at_utc"],
        "provider_instance_id": evidence["provider_instance_id"], "provider_instance_binding_sha256": binding["binding_sha256"],
        "provider_status": "RUNNING", "provider_verification": "VERIFIED", "evidence_mode": mode,
        "provider_authenticated": authenticated, "login_or_logout_performed": False,
        "gpu_count": 4, "gpu_model": "RTX3090", "vram_mib_each": 24576, "gpu_uuid_set_sha256": evidence["gpu_uuid_set_sha256"],
        "runtime_sha256": source_hashes["runtime"], "model_lockset_sha256": source_hashes["model_lockset"], "data_handoff_sha256": source_hashes["data_handoff"], "ssh_host_key_sha256": source_hashes["ssh_host_key"],
        "all_fee_components_usd": {name: str(_money(components[name], name)) for name in sorted(components)},
        "whole_workload_total_usd": str(declared_total), "quote_sha256": quote_sha256, "whole_workload_budget_sha256": budget_sha256,
        "management_mode": management_mode, "management_authority_sha256": source_hashes["management_authority"], "owner_manual_dashboard_destroy_ready": bool(manual_ready), "provider_destroy_performed": False,
        "provider_observation_sha256": evidence["observation_sha256"], "provider_observation_file_sha256": observation_file_sha256, "source_artifact_sha256": source_hashes,
        "ttl_deadline_utc": evidence["ttl_deadline_utc"], "remaining_ttl_seconds": remaining_ttl_seconds, "forward_hard_stop_usd": 35, "freeze_bindings": _freeze_bindings(root),
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _validate(root, "a2-provider-admission-receipt.v2.json", receipt)
    return receipt


def validate_provider_admission_receipt_v2(repository_root: Path, receipt: Mapping[str, Any]) -> dict[str, Any]:
    root = repository_root.resolve()
    checked = dict(receipt)
    _self_hash(checked, "receipt_sha256")
    _validate(root, "a2-provider-admission-receipt.v2.json", checked)
    if str(checked["provider_instance_id"]) in _DESTROYED_PROVIDER_INSTANCE_IDS:
        raise A2ExecutionReadinessError("provider admission targets a destroyed instance")
    _validate_freeze_bindings(root, checked["freeze_bindings"])
    return checked


def build_execution_adoption_receipt_v2(
    repository_root: Path,
    *,
    attempt_id: str,
    provider_admission_receipt: Mapping[str, Any],
    bundle_receipt: Mapping[str, Any],
    remote_root: str,
    staged_bundle_sha256: str,
    watchdog_sha256: str,
    watchdog_deadline_utc: str,
    lifecycle_genesis_checkpoint_sha256: str,
    live_probe_receipt_sha256: str,
    live_probe_file_sha256: str,
) -> dict[str, Any]:
    """Create an adoption receipt that cannot be reused across fresh instances."""

    root = repository_root.resolve()
    provider = validate_provider_admission_receipt_v2(root, provider_admission_receipt)
    bundle = dict(bundle_receipt)
    _self_hash(bundle, "receipt_sha256")
    _validate(root, "a2-execution-bundle-receipt.v1.json", bundle)
    _validate_freeze_bindings(root, bundle["freeze_bindings"])
    if bundle["attempt_id"] != attempt_id or provider["attempt_id"] != attempt_id:
        raise A2ExecutionReadinessError("adoption attempt identity differs from inputs")
    if _REMOTE_ROOT.fullmatch(remote_root) is None or not remote_root.endswith(attempt_id):
        raise A2ExecutionReadinessError("adoption requires its isolated A2 remote root")
    if staged_bundle_sha256 != bundle["bundle_sha256"]:
        raise A2ExecutionReadinessError("staged bundle hash differs from the local bundle")
    _require_hash(watchdog_sha256, "watchdog")
    if _timestamp(watchdog_deadline_utc, "watchdog deadline") >= _timestamp(provider["ttl_deadline_utc"], "provider TTL deadline"):
        raise A2ExecutionReadinessError("watchdog deadline must precede provider TTL deadline")
    _require_hash(lifecycle_genesis_checkpoint_sha256, "lifecycle genesis checkpoint")
    _require_hash(live_probe_receipt_sha256, "live remote probe receipt")
    _require_hash(live_probe_file_sha256, "live remote probe file")
    body = {
        "schema_version": "myis.armindex-a2-execution-adoption-receipt.v2",
        "receipt_id": _receipt_id(attempt_id, "execution-adoption").removesuffix("-v1") + "-v2",
        "attempt_id": attempt_id, "status": "PASS_A2_EXECUTION_ADOPTION",
        "provider_admission_receipt_sha256": provider["receipt_sha256"], "provider_instance_id": provider["provider_instance_id"], "provider_instance_binding_sha256": provider["provider_instance_binding_sha256"],
        "provider_observation_sha256": provider["provider_observation_sha256"], "provider_observation_file_sha256": provider["provider_observation_file_sha256"],
        "live_probe_receipt_sha256": live_probe_receipt_sha256, "live_probe_file_sha256": live_probe_file_sha256,
        "bundle_receipt_sha256": bundle["receipt_sha256"], "bundle_sha256": bundle["bundle_sha256"], "git_commit": bundle["git_commit"], "git_tree": bundle["git_tree"],
        "remote_root": remote_root, "remote_root_created_fresh": True, "staged_bundle_sha256": staged_bundle_sha256, "staged_bundle_verified": True,
        "ttl_deadline_utc": provider["ttl_deadline_utc"], "remaining_ttl_seconds_at_admission": provider["remaining_ttl_seconds"],
        "watchdog_installed": True, "watchdog_deadline_utc": watchdog_deadline_utc, "watchdog_sha256": watchdog_sha256,
        "lifecycle_genesis_checkpoint_sha256": lifecycle_genesis_checkpoint_sha256, "freeze_bindings": _freeze_bindings(root),
        "launch_allowed": True, "measured_retrieval_allowed": False,
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _validate(root, "a2-execution-adoption-receipt.v2.json", receipt)
    return receipt


def validate_execution_adoption_receipt_v2(
    repository_root: Path, receipt: Mapping[str, Any]
) -> dict[str, Any]:
    root = repository_root.resolve()
    checked = dict(receipt)
    _self_hash(checked, "receipt_sha256")
    _validate(root, "a2-execution-adoption-receipt.v2.json", checked)
    _validate_freeze_bindings(root, checked["freeze_bindings"])
    return checked


def build_execution_adoption_receipt(
    repository_root: Path,
    *,
    attempt_id: str,
    provider_admission_receipt: Mapping[str, Any],
    bundle_receipt: Mapping[str, Any],
    remote_root: str,
    staged_bundle_sha256: str,
    watchdog_sha256: str,
    watchdog_deadline_utc: str,
    lifecycle_genesis_checkpoint_sha256: str,
    live_probe_receipt_sha256: str,
    live_probe_file_sha256: str,
) -> dict[str, Any]:
    """Bind validated admission, bundle, isolated root, and watchdog for staging."""

    root = repository_root.resolve()
    provider = validate_provider_admission_receipt(root, provider_admission_receipt)
    bundle = dict(bundle_receipt)
    _self_hash(bundle, "receipt_sha256")
    _validate(root, "a2-execution-bundle-receipt.v1.json", bundle)
    _validate_freeze_bindings(root, bundle["freeze_bindings"])
    if bundle["attempt_id"] != attempt_id or provider["attempt_id"] != attempt_id:
        raise A2ExecutionReadinessError("adoption attempt identity differs from inputs")
    if _REMOTE_ROOT.fullmatch(remote_root) is None or not remote_root.endswith(attempt_id):
        raise A2ExecutionReadinessError("adoption requires its isolated A2 remote root")
    if staged_bundle_sha256 != bundle["bundle_sha256"]:
        raise A2ExecutionReadinessError("staged bundle hash differs from the local bundle")
    _require_hash(watchdog_sha256, "watchdog")
    deadline = _timestamp(watchdog_deadline_utc, "watchdog deadline")
    ttl_deadline = _timestamp(provider["ttl_deadline_utc"], "provider TTL deadline")
    if deadline >= ttl_deadline:
        raise A2ExecutionReadinessError("watchdog deadline must precede provider TTL deadline")
    _require_hash(lifecycle_genesis_checkpoint_sha256, "lifecycle genesis checkpoint")
    _require_hash(live_probe_receipt_sha256, "live remote probe receipt")
    _require_hash(live_probe_file_sha256, "live remote probe file")
    body = {
        "schema_version": "myis.armindex-a2-execution-adoption-receipt.v1",
        "receipt_id": _receipt_id(attempt_id, "execution-adoption"),
        "attempt_id": attempt_id,
        "status": "PASS_A2_EXECUTION_ADOPTION",
        "provider_admission_receipt_sha256": provider["receipt_sha256"],
        "provider_observation_sha256": provider["provider_observation_sha256"],
        "provider_observation_file_sha256": provider["provider_observation_file_sha256"],
        "live_probe_receipt_sha256": live_probe_receipt_sha256,
        "live_probe_file_sha256": live_probe_file_sha256,
        "bundle_receipt_sha256": bundle["receipt_sha256"],
        "bundle_sha256": bundle["bundle_sha256"],
        "git_commit": bundle["git_commit"],
        "git_tree": bundle["git_tree"],
        "remote_root": remote_root,
        "remote_root_created_fresh": True,
        "staged_bundle_sha256": staged_bundle_sha256,
        "staged_bundle_verified": True,
        "ttl_deadline_utc": provider["ttl_deadline_utc"],
        "remaining_ttl_seconds_at_admission": provider["remaining_ttl_seconds"],
        "watchdog_installed": True,
        "watchdog_deadline_utc": watchdog_deadline_utc,
        "watchdog_sha256": watchdog_sha256,
        "lifecycle_genesis_checkpoint_sha256": lifecycle_genesis_checkpoint_sha256,
        "freeze_bindings": _freeze_bindings(root),
        "launch_allowed": True,
        "measured_retrieval_allowed": False,
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _validate(root, "a2-execution-adoption-receipt.v1.json", receipt)
    return receipt


def validate_execution_adoption_receipt(
    repository_root: Path, receipt: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate an adoption receipt without contacting or launching anything."""

    if receipt.get("schema_version") == "myis.armindex-a2-execution-adoption-receipt.v2":
        return validate_execution_adoption_receipt_v2(repository_root, receipt)
    root = repository_root.resolve()
    checked = dict(receipt)
    _self_hash(checked, "receipt_sha256")
    _validate(root, "a2-execution-adoption-receipt.v1.json", checked)
    _validate_freeze_bindings(root, checked["freeze_bindings"])
    return checked


@dataclass(frozen=True)
class A2MeasuredRunner:
    """In-memory runner state machine; it never starts a process or a provider call."""

    attempt_id: str
    state: str = "LOCKED"
    executor: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None

    def stage(
        self, repository_root: Path, adoption_receipt: Mapping[str, Any]
    ) -> "A2MeasuredRunner":
        """Move to a staged state only after a syntactically valid PASS adoption."""

        if self.state != "LOCKED":
            raise A2ExecutionReadinessError("runner state is immutable after staging")
        adopted = validate_execution_adoption_receipt(
            repository_root, adoption_receipt
        )
        if adopted.get("attempt_id") != self.attempt_id:
            raise A2ExecutionReadinessError("runner attempt differs from adoption receipt")
        require_execution_adoption(adopted)
        return A2MeasuredRunner(
            attempt_id=self.attempt_id,
            state="STAGED_NOT_LAUNCHED",
            executor=self.executor,
        )

    def request_external_execution(self) -> dict[str, Any]:
        """Emit a side-effect-free launch plan for the separately authorized executor."""

        if self.state != "STAGED_NOT_LAUNCHED":
            raise A2ExecutionReadinessError("runner must be staged after adoption PASS")
        return {
            "attempt_id": self.attempt_id,
            "state": "EXTERNAL_EXECUTION_REQUESTED_NOT_LAUNCHED",
            "candidate_generation_performed": False,
            "process_started": False,
            "provider_contacted": False,
        }

    def call_injected_executor(self, launch_plan: Mapping[str, Any]) -> Mapping[str, Any]:
        """Call only an explicit injected executor after adoption-based staging.

        The readiness implementation has no executor of its own.  This keeps
        imports and ordinary method calls side-effect free while allowing a
        separately authorized integration to supply its controlled executor.
        """

        if self.state != "STAGED_NOT_LAUNCHED":
            raise A2ExecutionReadinessError("runner must be staged before executor use")
        if self.executor is None:
            raise A2ExecutionReadinessError("runner has no injected executor")
        plan = dict(launch_plan)
        if (
            set(plan) != {"attempt_id", "measured_retrieval_allowed"}
            or
            plan.get("attempt_id") != self.attempt_id
            or plan.get("measured_retrieval_allowed", False) is not False
        ):
            raise A2ExecutionReadinessError("injected executor plan crosses readiness lock")
        return self.executor(plan)


def build_remote_staging_plan(
    repository_root: Path,
    *,
    adoption_receipt: Mapping[str, Any],
    bundle_path: Path,
) -> dict[str, Any]:
    """Create a deterministic transfer plan without opening an SSH connection."""

    root = repository_root.resolve()
    adoption = validate_execution_adoption_receipt(root, adoption_receipt)
    bundle = bundle_path.resolve()
    if not bundle.is_file() or bundle.is_symlink():
        raise A2ExecutionReadinessError("staging bundle is missing or unsafe")
    if file_sha256(bundle) != adoption.get("bundle_sha256"):
        raise A2ExecutionReadinessError("staging bundle does not match adoption receipt")
    plan = {
        "schema_version": "myis.armindex-a2-remote-staging-plan.v1",
        "attempt_id": adoption["attempt_id"],
        "remote_root": adoption["remote_root"],
        "bundle_sha256": adoption["bundle_sha256"],
        "staging_operations": [
            "create_isolated_remote_root",
            "transfer_bundle",
            "verify_bundle_sha256",
            "extract_without_overwriting_a1_root",
        ],
        "ssh_called": False,
        "provider_contacted": False,
        "measured_retrieval_allowed": False,
    }
    return {**plan, "plan_sha256": canonical_sha256(plan)}


def build_watchdog_script(
    *, attempt_id: str, remote_root: str, deadline_utc: str
) -> dict[str, Any]:
    """Build a bounded watchdog that signals only same-identity registered children."""

    if _ATTEMPT.fullmatch(attempt_id) is None or _REMOTE_ROOT.fullmatch(remote_root) is None:
        raise A2ExecutionReadinessError("watchdog attempt or root is invalid")
    deadline = _timestamp(deadline_utc, "watchdog deadline")
    body = (
        "#!/usr/bin/env sh\n"
        "set -eu\n"
        f"attempt_id='{attempt_id}'\n"
        f"remote_root='{remote_root}'\n"
        f"deadline_utc='{deadline.isoformat().replace('+00:00', 'Z')}'\n"
        "test -d \"$remote_root\"\n"
        "test -n \"$attempt_id\"\n"
        "test -n \"$deadline_utc\"\n"
        "deadline_epoch=$(date -u -d \"$deadline_utc\" +%s)\n"
        "heartbeat=\"$remote_root/lifecycle/heartbeats/watchdog\"\n"
        "while test \"$(date -u +%s)\" -lt \"$deadline_epoch\"; do\n"
        "  date -u +%Y-%m-%dT%H:%M:%SZ >\"$heartbeat\"\n"
        "  sleep 2\n"
        "done\n"
        "registry=\"$remote_root/lifecycle/processes\"\n"
        "test -d \"$registry\" || exit 0\n"
        "for identity in \"$registry\"/*.identity; do\n"
        "  test -f \"$identity\" || continue\n"
        "  IFS=: read -r pid start_tick <\"$identity\"\n"
        "  case \"$pid:$start_tick\" in *[!0-9:]*) exit 70;; esac\n"
        "  test -r \"/proc/$pid/stat\" || continue\n"
        "  actual=$(sed 's/.*) //' \"/proc/$pid/stat\" | awk '{print $20}')\n"
        "  test \"$actual\" = \"$start_tick\" || continue\n"
        "  kill -TERM \"$pid\" 2>/dev/null || true\n"
        "done\n"
        "sleep 15\n"
        "for identity in \"$registry\"/*.identity; do\n"
        "  test -f \"$identity\" || continue\n"
        "  IFS=: read -r pid start_tick <\"$identity\"\n"
        "  test -r \"/proc/$pid/stat\" || continue\n"
        "  actual=$(sed 's/.*) //' \"/proc/$pid/stat\" | awk '{print $20}')\n"
        "  test \"$actual\" = \"$start_tick\" && kill -KILL \"$pid\" 2>/dev/null || true\n"
        "done\n"
    )
    return {
        "attempt_id": attempt_id,
        "remote_root": remote_root,
        "deadline_utc": deadline.isoformat().replace("+00:00", "Z"),
        "script": body,
        "watchdog_sha256": hashlib.sha256(body.encode("ascii")).hexdigest(),
        "ssh_called": False,
        "provider_contacted": False,
    }


def evaluate_aggregate_train_results(
    repository_root: Path,
    *,
    results_by_candidate: Mapping[str, Mapping[str, Any]],
    allow_synthetic_fixture: bool = False,
) -> dict[str, Any]:
    """Deterministically select one unique aggregate winner per frozen arm.

    The input must cover the frozen 52-candidate universe exactly.  Inputs are
    synthetic fixtures in this readiness surface, so no result can be mistaken
    for measured A2 evidence.
    """

    if not allow_synthetic_fixture:
        raise A2ExecutionReadinessError("aggregate evaluator accepts synthetic fixtures only")
    root = repository_root.resolve()
    candidates = frozen_candidates(root)
    if set(results_by_candidate) != set(candidates):
        raise A2ExecutionReadinessError("aggregate results must cover frozen membership exactly")
    winners: dict[str, dict[str, Any]] = {}
    for arm_id in ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05"):
        scored: list[tuple[Decimal, str]] = []
        for candidate_id, candidate in candidates.items():
            if candidate["arm_id"] != arm_id:
                continue
            result = dict(results_by_candidate[candidate_id])
            if set(result) != {
                "fixture_kind",
                "candidate_id",
                "arm_id",
                "primary_metric",
                "aggregate_metrics_sha256",
                "train_only",
                "rep_dev_measured",
                "per_query_outcomes_included",
            }:
                raise A2ExecutionReadinessError("aggregate train fixture fields are not allowlisted")
            if (
                result["fixture_kind"] != "synthetic_a2_train_result_v1"
                or result["candidate_id"] != candidate_id
                or result["arm_id"] != arm_id
                or result["train_only"] is not True
                or result["rep_dev_measured"] is not False
                or result["per_query_outcomes_included"] is not False
            ):
                raise A2ExecutionReadinessError("aggregate train fixture violates A2 boundaries")
            _require_hash(result["aggregate_metrics_sha256"], "aggregate metrics")
            assert_aggregate_only(result)
            try:
                score = Decimal(str(result["primary_metric"]))
            except (InvalidOperation, ValueError) as error:
                raise A2ExecutionReadinessError("aggregate primary metric is invalid") from error
            if not score.is_finite():
                raise A2ExecutionReadinessError("aggregate primary metric is invalid")
            scored.append((score, candidate_id))
        scored.sort(key=lambda item: (-item[0], item[1]))
        if len(scored) < 2 or scored[0][0] == scored[1][0]:
            raise A2ExecutionReadinessError("exact aggregate winner tie is rejected")
        winner_id = scored[0][1]
        winner = candidates[winner_id]
        winners[arm_id] = {
            "winner_candidate_id": winner_id,
            "primary_metric": str(scored[0][0]),
            "diagnostic_non_advancing": winner["diagnostic_non_advancing"],
            "advancement_eligible": winner["advancement_eligible"],
        }
    return {
        "status": "PASS_SYNTHETIC_A2_AGGREGATE_EVALUATION",
        "candidate_count": 52,
        "winners": winners,
        "freeze_bindings": _freeze_bindings(root),
        "measured_a2_performed": False,
    }


def require_execution_adoption(adoption_receipt: Mapping[str, Any]) -> None:
    """The runner's only authorization gate; anything else is locked."""

    if adoption_receipt.get("status") != "PASS_A2_EXECUTION_ADOPTION":
        raise A2ExecutionReadinessError("measured runner remains locked without adoption PASS")
    if adoption_receipt.get("launch_allowed") is not True:
        raise A2ExecutionReadinessError("adoption does not allow launcher setup")
    if adoption_receipt.get("measured_retrieval_allowed") is not False:
        raise A2ExecutionReadinessError("readiness runner never authorizes measured retrieval")


__all__ = [
    "A2ExecutionReadinessError",
    "A2MeasuredRunner",
    "append_lifecycle_checkpoint",
    "build_execution_bundle",
    "build_execution_adoption_receipt",
    "build_execution_adoption_receipt_v2",
    "build_lifecycle_checkpoint",
    "build_provider_admission_receipt",
    "build_provider_admission_receipt_v2",
    "build_provider_instance_binding",
    "build_remote_staging_plan",
    "build_safe_return_receipt",
    "build_train_evaluation_receipt",
    "build_winner_receipt",
    "build_watchdog_script",
    "evaluate_aggregate_train_results",
    "frozen_candidates",
    "require_execution_adoption",
    "required_execution_bundle_paths",
    "resume_checkpoint",
    "validate_execution_adoption_receipt",
    "validate_execution_adoption_receipt_v2",
    "validate_execution_bundle",
    "validate_execution_ledger",
    "validate_provider_admission_receipt",
    "validate_provider_admission_receipt_v2",
    "validate_provider_instance_binding",
]
