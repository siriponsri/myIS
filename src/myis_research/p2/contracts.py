"""Hash-bound P2 budget/request contracts.

This module is deliberately separate from the P1 owner-local contract.  P1
requests remain immutable evidence; P2 requests carry the new profile and
freeze-barrier commitments explicitly.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from ..kernel.canonical import canonical_json, canonical_sha256, file_sha256
from ..protection import assert_aggregate_only


PROFILE_RELATIVE_PATH = Path("control/budgets/p2-r1-primary-v1.yaml")
ENVELOPE_RELATIVE_PATH = Path("control/execution-envelope-p2.yaml")
PROFILE_SCHEMA = "p2-budget-profile.v1.json"
REQUEST_SCHEMA = "p2-request.v1.json"
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
GIT_RE = re.compile(r"^(?:[a-f0-9]{40}|[a-f0-9]{64})$")
P2_ARTIFACT_SCHEMAS = {
    "myis.p2-request.v1": "p2-request.v1.json",
    "myis.p2-candidate-ledger.v1": "p2-candidate-ledger.v1.json",
    "myis.p2-shortlist-freeze-receipt.v1": "p2-shortlist-freeze-receipt.v1.json",
    "myis.p2-selection-receipt.v1": "p2-selection-receipt.v1.json",
    "myis.p2-manifest.v1": "p2-manifest.v1.json",
    "myis.p2-package.v1": "p2-package.v1.json",
}
P2_HASH_FIELDS = {
    "myis.p2-candidate-ledger.v1": "ledger_sha256",
    "myis.p2-shortlist-freeze-receipt.v1": "receipt_sha256",
    "myis.p2-selection-receipt.v1": "receipt_sha256",
    "myis.p2-manifest.v1": "manifest_sha256",
    "myis.p2-package.v1": "package_sha256",
}


class P2ContractError(ValueError):
    """Raised when a P2 contract is missing, stale, or unsafe."""


@dataclass(frozen=True)
class P2BudgetProfile:
    payload: dict[str, Any]
    sha256: str

    @property
    def profile_id(self) -> str:
        return str(self.payload["profile_id"])


def load_profile(repository_root: Path) -> P2BudgetProfile:
    root = Path(repository_root).resolve()
    path = root / PROFILE_RELATIVE_PATH
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise P2ContractError(f"cannot load P2 budget profile: {path}") from error
    if not isinstance(payload, dict):
        raise P2ContractError("P2 budget profile must be a mapping")
    _validate_schema(payload, PROFILE_SCHEMA)
    _validate_profile_invariants(payload)
    return P2BudgetProfile(dict(payload), canonical_sha256(payload))


def load_p2_request(
    request_path: Path,
    repository_root: Path,
    *,
    require_store: bool = False,
) -> tuple[dict[str, Any], P2BudgetProfile]:
    root = Path(repository_root).resolve()
    path = Path(request_path).resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise P2ContractError(f"cannot load P2 request: {path}") from error
    if not isinstance(payload, dict):
        raise P2ContractError("P2 request must be a JSON object")
    _validate_schema(payload, REQUEST_SCHEMA)
    try:
        assert_aggregate_only(payload)
    except ValueError as error:
        raise P2ContractError(str(error)) from error
    _reject_hidden_defaults(payload)
    profile = load_profile(root)
    if payload["budget_profile_id"] != profile.profile_id:
        raise P2ContractError("request budget_profile_id does not match the canonical profile")
    if payload["budget_profile_sha256"] != profile.sha256:
        raise P2ContractError("request budget_profile_sha256 does not match the canonical profile")
    envelope = root / ENVELOPE_RELATIVE_PATH
    if not envelope.is_file() or file_sha256(envelope) != payload["execution_envelope_sha256"]:
        raise P2ContractError("request execution envelope hash is stale or missing")
    if not GIT_RE.fullmatch(str(payload["git_commit"])):
        raise P2ContractError("request git_commit must be a full lowercase Git commit")
    if len(payload["frozen_controls"]) != 4 or len(set(payload["frozen_controls"])) != 4:
        raise P2ContractError("exactly four unique frozen controls must be preregistered")
    if require_store:
        _validate_store_environment(root)
    return dict(payload), profile


def build_request(
    *,
    request_id: str,
    git_commit: str,
    execution_envelope_sha256: str,
    scope_hashes: Mapping[str, str],
    input_hashes: Mapping[str, str],
    frozen_controls: list[str],
    repository_root: Path,
) -> dict[str, Any]:
    """Build a complete request; callers still need to persist it immutably."""

    profile = load_profile(repository_root)
    body: dict[str, Any] = {
        "schema_version": "myis.p2-request.v1",
        "request_id": request_id,
        "phase_id": "P2_SCOPE_DEVELOPMENT",
        "arm": "R1",
        "stage": "train_selection",
        "campaign_id": "scope-autoindex-v1",
        "campaign_revision": profile.payload["campaign_revision"],
        "budget_profile_id": profile.profile_id,
        "budget_profile_sha256": profile.sha256,
        "execution_envelope_sha256": execution_envelope_sha256,
        "git_commit": git_commit,
        "scope_hashes": dict(scope_hashes),
        "input_hashes": dict(input_hashes),
        "frozen_controls": list(frozen_controls),
    }
    _validate_schema(body, REQUEST_SCHEMA)
    return body


def write_immutable_json(path: Path, payload: Mapping[str, Any]) -> str:
    """Write one canonical JSON object without allowing overwrite."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = (canonical_json(dict(payload)) + "\n").encode("utf-8")
    try:
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    except FileExistsError as error:
        raise P2ContractError(f"refusing to overwrite immutable P2 artifact: {target}") from error
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return canonical_sha256(dict(payload))


def validate_p2_artifact(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one non-secret P2 artifact and its canonical self-hash.

    Request artifacts intentionally have no self-hash; their hash is bound by
    the package or manifest that references them. All other P2 receipts,
    ledgers, manifests, and packages are immutable canonical JSON objects.
    """

    if not isinstance(payload, Mapping):
        raise P2ContractError("P2 artifact must be a JSON object")
    schema_version = str(payload.get("schema_version", ""))
    schema_name = P2_ARTIFACT_SCHEMAS.get(schema_version)
    if schema_name is None:
        raise P2ContractError("unsupported P2 artifact schema")
    _validate_schema(payload, schema_name)
    hash_field = P2_HASH_FIELDS.get(schema_version)
    if hash_field:
        recorded = str(payload.get(hash_field, ""))
        unsigned = {key: value for key, value in payload.items() if key != hash_field}
        if recorded != canonical_sha256(unsigned):
            raise P2ContractError(f"{schema_version} self-hash is invalid")
    if payload.get("budget_profile_id") not in {None, "p2-r1-primary-v1"}:
        raise P2ContractError("P2 artifact uses an unknown budget profile")
    return dict(payload)


def _validate_profile_invariants(payload: Mapping[str, Any]) -> None:
    limits = payload["limits"]
    allocation = payload["candidate_allocation"]
    if allocation["frozen_controls"] + allocation["preregistered_patent_candidates"] + allocation["adaptive_candidates"] != limits["max_candidates_total"]:
        raise P2ContractError("candidate allocation must equal max_candidates_total")
    if limits["max_adaptive_candidates"] != allocation["adaptive_candidates"]:
        raise P2ContractError("adaptive candidate ceiling mismatch")
    if limits["max_adaptive_iterations"] * limits["candidates_per_iteration"] != limits["max_adaptive_candidates"]:
        raise P2ContractError("adaptive iteration budget does not equal adaptive candidate ceiling")
    if "max_cpu_seconds" in json.dumps(payload, ensure_ascii=True):
        raise P2ContractError("max_cpu_seconds is not an allowed P2 field")


def _reject_hidden_defaults(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) == "max_cpu_seconds":
                raise P2ContractError(f"hidden or ambiguous runtime field at {path}.{key}")
            _reject_hidden_defaults(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_hidden_defaults(item, f"{path}[{index}]")


def _validate_store_environment(repository_root: Path) -> None:
    for name in ("MYIS_STORE", "MYIS_MLFLOW_STORE"):
        raw = os.environ.get(name)
        if not raw:
            raise P2ContractError(f"{name} is required before a measured P2 run")
        candidate = Path(raw).expanduser().resolve()
        try:
            candidate.relative_to(repository_root)
        except ValueError:
            continue
        raise P2ContractError(f"{name} must be outside the Git worktree")


def _validate_schema(payload: Mapping[str, Any], schema_name: str) -> None:
    schema_path = Path(__file__).resolve().parents[3] / "schemas" / schema_name
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(dict(payload))
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        raise P2ContractError(f"JSON Schema validation failed for {schema_name}: {error}") from error
