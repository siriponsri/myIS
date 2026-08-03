"""Hash-bound P2 budget/request contracts.

This module is deliberately separate from the P1 owner-local contract.  P1
requests remain immutable evidence; P2 requests carry the new profile and
freeze-barrier commitments explicitly.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Mapping
from urllib.parse import urlsplit

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable

from ..kernel.canonical import canonical_json, canonical_sha256, file_sha256
from ..owner_local import OwnerLocalContractError, validate_receipt
from ..protection import assert_aggregate_only, assert_path_not_protected


PROFILE_RELATIVE_PATH = Path("control/budgets/p2-r1-primary-v1.yaml")
ENVELOPE_RELATIVE_PATH = Path("control/execution-envelope-p2.yaml")
HISTORICAL_PROPOSAL_RELATIVE_PATH = Path(
    "campaigns/scope-autoindex-v1/proposals/p2-candidate-freeze-proposal.v1.json"
)
HISTORICAL_PROPOSAL_SESSION_RELATIVE_PATH = Path(
    "projections/sessions/20260802T093026Z-p2-preflight-freeze-proposal-v1.json"
)
PROFILE_SCHEMA = "p2-budget-profile.v1.json"
REQUEST_SCHEMA = "p2-request.v1.json"
AGGREGATE_METRIC_SCHEMA = "p2-aggregate-metric.v1.json"
TRAIN_METRIC_SCHEMA = "p2-train-metric.v1.json"
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
GIT_RE = re.compile(r"^(?:[a-f0-9]{40}|[a-f0-9]{64})$")
P2_ARTIFACT_SCHEMAS = {
    "myis.p2-request.v1": "p2-request.v1.json",
    "myis.p2-preflight-receipt.v1": "p2-preflight-receipt.v1.json",
    "myis.p2-candidate-freeze-proposal.v1": "p2-candidate-freeze-proposal.v1.json",
    "myis.p2-candidate-ledger.v1": "p2-candidate-ledger.v1.json",
    "myis.p2-baseline-commitment.v1": "p2-baseline-commitment.v1.json",
    "myis.p2-baseline-reproduction-receipt.v1": "p2-baseline-reproduction-receipt.v1.json",
    "myis.p2-shortlist-freeze-receipt.v1": "p2-shortlist-freeze-receipt.v1.json",
    "myis.p2-selection-receipt.v1": "p2-selection-receipt.v1.json",
    "myis.p2-manifest.v1": "p2-manifest.v1.json",
    "myis.p2-package.v1": "p2-package.v1.json",
}
P2_HASH_FIELDS = {
    "myis.p2-preflight-receipt.v1": "receipt_sha256",
    "myis.p2-candidate-freeze-proposal.v1": "proposal_sha256",
    "myis.p2-candidate-ledger.v1": "ledger_sha256",
    "myis.p2-baseline-commitment.v1": "commitment_sha256",
    "myis.p2-baseline-reproduction-receipt.v1": "receipt_sha256",
    "myis.p2-shortlist-freeze-receipt.v1": "receipt_sha256",
    "myis.p2-selection-receipt.v1": "receipt_sha256",
    "myis.p2-manifest.v1": "manifest_sha256",
    "myis.p2-package.v1": "package_sha256",
}
P2_PREFLIGHT_CHECK_IDS = (
    "execution_source_commit",
    "canonical_profile_binding",
    "canonical_envelope_binding",
    "canonical_campaign_binding",
    "gate_state",
    "counter_state",
    "store_myis_store",
    "store_myis_mlflow_store",
    "store_path_overlap",
    "aggregate_free_space",
)
TRAIN_METRIC_COMPARISON_FIELDS = (
    "schema_version",
    "metric_name",
    "data_role",
    "scope",
    "evidence_role",
    "direction",
    "n",
    "denominator",
    "dataset_lineage_sha256",
    "config_sha256",
    "retriever_sha256",
    "evaluator_sha256",
)
TRAIN_METRIC_IDENTITY_FIELDS = (
    "candidate_id",
    "arm",
    *TRAIN_METRIC_COMPARISON_FIELDS,
)


class P2ContractError(ValueError):
    """Raised when a P2 contract is missing, stale, or unsafe."""


@dataclass(frozen=True)
class P2BudgetProfile:
    payload: dict[str, Any]
    sha256: str

    @property
    def profile_id(self) -> str:
        return str(self.payload["profile_id"])


def load_profile(
    repository_root: Path,
    profile_relative_path: Path = PROFILE_RELATIVE_PATH,
) -> P2BudgetProfile:
    root = Path(repository_root).resolve()
    path = root / profile_relative_path
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise P2ContractError(f"cannot load P2 budget profile: {path}") from error
    if not isinstance(payload, dict):
        raise P2ContractError("P2 budget profile must be a mapping")
    _validate_schema(payload, PROFILE_SCHEMA)
    _validate_profile_invariants(payload)
    return P2BudgetProfile(dict(payload), canonical_sha256(payload))


def load_profile_by_id(repository_root: Path, profile_id: str) -> P2BudgetProfile:
    if not re.fullmatch(r"p2-r1-primary-v[0-9]+", str(profile_id)):
        raise P2ContractError("P2 budget profile ID is invalid")
    relative = Path("control/budgets") / f"{profile_id}.yaml"
    profile = load_profile(repository_root, relative)
    if profile.profile_id != profile_id:
        raise P2ContractError("P2 budget profile file and profile ID differ")
    return profile


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
    payload = validate_p2_artifact(payload, repository_root=root)
    _reject_hidden_defaults(payload)
    profile = load_profile_by_id(root, str(payload["budget_profile_id"]))
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
    budget_profile_uri: str = PROFILE_RELATIVE_PATH.as_posix(),
) -> dict[str, Any]:
    """Build a complete request; callers still need to persist it immutably."""

    profile = load_profile(repository_root, Path(budget_profile_uri))
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
    return validate_p2_artifact(body, repository_root=repository_root)


def write_immutable_json(path: Path, payload: Mapping[str, Any]) -> str:
    """Write one canonical JSON object without allowing overwrite."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = (canonical_json(dict(payload)) + "\n").encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError as error:
            raise P2ContractError(
                f"refusing to overwrite immutable P2 artifact: {target}"
            ) from error
    except BaseException:
        raise
    finally:
        temporary.unlink(missing_ok=True)
    return canonical_sha256(dict(payload))


def validate_p2_artifact(
    payload: Mapping[str, Any],
    *,
    repository_root: Path | None = None,
) -> dict[str, Any]:
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
    try:
        assert_aggregate_only(payload)
    except ValueError as error:
        raise P2ContractError(str(error)) from error
    _validate_schema(payload, schema_name)
    hash_field = P2_HASH_FIELDS.get(schema_version)
    if hash_field:
        recorded = str(payload.get(hash_field, ""))
        unsigned = {key: value for key, value in payload.items() if key != hash_field}
        if recorded != canonical_sha256(unsigned):
            raise P2ContractError(f"{schema_version} self-hash is invalid")
    root = Path(repository_root).resolve() if repository_root is not None else _repository_root()
    profile_id = payload.get("budget_profile_id")
    profile = (
        load_profile_by_id(root, str(profile_id))
        if profile_id is not None
        else load_profile(root)
    )
    if payload.get("budget_profile_id") != profile.profile_id:
        raise P2ContractError("P2 artifact budget_profile_id does not match the canonical profile")
    if payload.get("budget_profile_sha256") != profile.sha256:
        raise P2ContractError("P2 artifact budget_profile_sha256 does not match the canonical profile")
    campaign_revision = payload.get("campaign_revision")
    if campaign_revision is not None and campaign_revision != profile.payload["campaign_revision"]:
        raise P2ContractError("P2 artifact campaign_revision does not match the canonical profile")
    if schema_version == "myis.p2-request.v1":
        _, envelope_sha256 = _load_envelope_for_profile(root, profile)
        if envelope_sha256 != payload["execution_envelope_sha256"]:
            raise P2ContractError("request execution envelope hash is stale or missing")
        if payload["campaign_id"] != profile.payload["campaign_id"]:
            raise P2ContractError("request campaign_id does not match the canonical profile")
    elif schema_version == "myis.p2-preflight-receipt.v1":
        _validate_preflight_receipt_semantics(payload, root)
    elif schema_version == "myis.p2-candidate-freeze-proposal.v1":
        _validate_candidate_freeze_proposal_semantics(payload, root)
    elif schema_version == "myis.p2-candidate-ledger.v1":
        if payload["candidate_count"] != len(payload["candidates"]):
            raise P2ContractError("candidate_count does not match the candidates array")
    elif schema_version == "myis.p2-baseline-commitment.v1":
        _validate_safe_relative_uri(str(payload["prior_artifact_uri"]), "prior_artifact_uri")
        validate_p2_train_metric(payload["expected_metric"])
    elif schema_version == "myis.p2-baseline-reproduction-receipt.v1":
        validate_p2_train_metric(payload["expected_metric"])
        validate_p2_train_metric(payload["result"])
    elif schema_version == "myis.p2-shortlist-freeze-receipt.v1":
        if set(payload["candidate_ids"]) != set(payload["candidate_spec_hashes"]):
            raise P2ContractError("freeze candidate IDs and spec hashes do not correspond exactly")
    elif schema_version == "myis.p2-selection-receipt.v1":
        metric_ids = [str(item["candidate_id"]) for item in payload["metrics"]]
        if metric_ids != list(payload["candidate_ids"]) or len(metric_ids) != len(set(metric_ids)):
            raise P2ContractError("selection metrics must contain exactly one ordered result per finalist")
        for metric in payload["metrics"]:
            validate_p2_aggregate_metric(metric, selection=True)
    return dict(payload)


def validate_p2_preflight_receipt(
    payload: Mapping[str, Any],
    *,
    repository_root: Path | None = None,
) -> dict[str, Any]:
    """Validate the immutable, aggregate-only P2 preflight receipt."""

    return validate_p2_artifact(payload, repository_root=repository_root)


def validate_p2_candidate_freeze_proposal(
    payload: Mapping[str, Any],
    *,
    repository_root: Path | None = None,
) -> dict[str, Any]:
    """Validate a repository-safe proposal without registering candidates."""

    return validate_p2_artifact(payload, repository_root=repository_root)


def _validate_preflight_receipt_semantics(
    payload: Mapping[str, Any],
    repository_root: Path,
) -> None:
    """Apply the state and binding rules that JSON Schema cannot express."""

    _reject_absolute_paths(payload)
    profile = load_profile(repository_root)
    campaign_path = repository_root / "control/campaigns/scope-autoindex-v1.yaml"
    _, envelope_sha256 = _load_envelope_for_profile(repository_root, profile)
    if payload["budget_profile_id"] != profile.profile_id or payload["budget_profile_sha256"] != profile.sha256:
        raise P2ContractError("preflight profile binding is stale")
    if payload["campaign_revision"] != profile.payload["campaign_revision"]:
        raise P2ContractError("preflight campaign revision is stale")
    commit_exists = _git_commit_exists(repository_root, str(payload["git_commit"]))
    if payload["git_commit_exists"] and not commit_exists:
        raise P2ContractError("preflight execution source commit is stale or missing")
    if not campaign_path.is_file() or file_sha256(campaign_path) != payload["campaign_sha256"]:
        raise P2ContractError("preflight campaign binding is stale")
    if envelope_sha256 != payload["execution_envelope_sha256"]:
        raise P2ContractError("preflight execution envelope binding is stale")

    checks = list(payload["checks"])
    check_ids = [str(item["check_id"]) for item in checks]
    check_statuses = [str(item["status"]) for item in checks]
    failed_checks = [item for item in checks if item["status"] == "failed"]
    failed_check_ids = sorted(str(item["check_id"]) for item in failed_checks)
    if check_ids != list(P2_PREFLIGHT_CHECK_IDS):
        raise P2ContractError("preflight receipt does not contain the exact required check set")
    if list(payload["failure_codes"]) != failed_check_ids:
        raise P2ContractError("preflight failure codes do not match the failed checks")
    stores = payload["stores"]
    counters = payload["counters"]
    gates = payload["gates"]
    zero_counters = counters == {
        "measured_runs": 0,
        "candidate_count": 0,
        "shortlist_count": 0,
        "selection_accesses": 0,
        "baseline_commitment_present": False,
        "freeze_started": False,
    }
    stores_passed = all(
        isinstance(value, Mapping)
        and value.get("status") == "passed"
        and value.get("configured") is True
        and value.get("exists") is True
        and value.get("is_directory") is True
        and value.get("outside_all_worktrees") is True
        and value.get("unsafe_link_or_junction") is False
        and value.get("writable_sentinel_created") is True
        and value.get("writable_sentinel_cleaned") is True
        for value in stores.values()
    )
    gates_safe = (
        gates["D1_START_CAMPAIGN"] == "active"
        and gates["D2_OPEN_FINAL"] == "waiting_owner"
        and gates["D3_SUBMIT_RELEASE"] == "waiting_owner"
        and gates["final_split_open"] is False
    )
    campaign_binding_ok = _current_campaign_binding(repository_root, profile.payload)
    store_free_space_total = sum(int(value.get("free_space_bytes", 0)) for value in stores.values())
    if payload["aggregate_free_space_bytes"] > store_free_space_total:
        raise P2ContractError("preflight aggregate free-space value exceeds the store evidence")
    boundary = payload["safe_path_boundary"]
    outside_all_worktrees = all(
        isinstance(value, Mapping) and value.get("outside_all_worktrees") is True
        for value in stores.values()
    )
    if boundary["outside_all_worktrees"] is not outside_all_worktrees:
        raise P2ContractError("preflight worktree boundary summary is inconsistent")
    if payload["status"] != "not_started":
        expected_check_statuses = {
            "execution_source_commit": payload["git_commit_exists"],
            "canonical_profile_binding": True,
            "canonical_envelope_binding": True,
            "canonical_campaign_binding": campaign_binding_ok,
            "store_myis_store": stores["MYIS_STORE"].get("status") == "passed",
            "store_myis_mlflow_store": stores["MYIS_MLFLOW_STORE"].get("status") == "passed",
            "aggregate_free_space": payload["aggregate_free_space_bytes"] >= payload["required_free_space_bytes"],
        }
        for item in checks:
            expected = expected_check_statuses.get(str(item["check_id"]))
            if expected is not None and (item["status"] == "passed") is not expected:
                raise P2ContractError(f"preflight check state is inconsistent: {item['check_id']}")
        counter_check = next(item for item in checks if item["check_id"] == "counter_state")
        if counter_check["status"] == "passed" and not zero_counters:
            raise P2ContractError("preflight check state is inconsistent: counter_state")
        gate_check = next(item for item in checks if item["check_id"] == "gate_state")
        if gate_check["status"] == "passed" and not gates_safe:
            raise P2ContractError("preflight check state is inconsistent: gate_state")
    if payload["status"] == "passed_pending_owner" and payload["aggregate_free_space_bytes"] < payload["required_free_space_bytes"]:
        raise P2ContractError("preflight aggregate free-space binding is insufficient")
    if payload["status"] == "passed_pending_owner":
        if check_statuses != ["passed"] * len(checks) or failed_checks:
            raise P2ContractError("passed preflight contains a failed or unrun check")
        if (
            not payload["git_commit_exists"]
            or not zero_counters
            or not stores_passed
            or not gates_safe
            or not payload["safe_path_boundary"]["outside_all_worktrees"]
        ):
            raise P2ContractError("passed preflight does not prove the required zero-counter boundary")
        if payload["failure_codes"]:
            raise P2ContractError("passed preflight cannot contain failure codes")
        current_gates, current_gates_safe, current_counters, current_counters_safe = _current_preflight_state(
            repository_root
        )
        if current_gates != dict(gates) or not current_gates_safe:
            raise P2ContractError("passed preflight gate state is stale")
        if current_counters != dict(counters) or not current_counters_safe:
            raise P2ContractError("passed preflight counter state is stale")
    elif payload["status"] == "failed":
        if not failed_checks and not payload["failure_codes"]:
            raise P2ContractError("failed preflight must retain a failure code")
    elif payload["status"] == "not_started":
        if payload["failure_codes"] or not zero_counters:
            raise P2ContractError("not-started preflight must retain zero counters and no failure")
    if payload["measured_execution"] or payload["protected_data_accessed"] or payload["final_split_open"]:
        raise P2ContractError("preflight receipt crosses the measured or protected boundary")
    if boundary["all_worktrees_count"] < 1 or not boundary["path_overlap_checked"] or not boundary["unsafe_links_rejected"]:
        raise P2ContractError("preflight did not complete the worktree path safety checks")


def _current_preflight_state(
    repository_root: Path,
) -> tuple[dict[str, Any], bool, dict[str, Any], bool]:
    from .preflight import _counter_snapshot, _gate_snapshot

    profile = load_profile(repository_root)
    gates, gates_safe = _gate_snapshot(repository_root, profile.payload)
    counters, counters_safe = _counter_snapshot(repository_root, profile.payload)
    return gates, gates_safe, counters, counters_safe


def _current_campaign_binding(
    repository_root: Path,
    profile: Mapping[str, Any],
) -> bool:
    from .preflight import _campaign_binding_ok

    return _campaign_binding_ok(
        repository_root,
        profile,
        repository_root / "control/campaigns/scope-autoindex-v1.yaml",
    )


def _validate_candidate_freeze_proposal_semantics(
    payload: Mapping[str, Any],
    repository_root: Path,
) -> None:
    _reject_absolute_paths(payload)
    profile = load_profile(repository_root)
    if payload["budget_profile_id"] != profile.profile_id or payload["budget_profile_sha256"] != profile.sha256:
        raise P2ContractError("candidate proposal profile binding is stale")
    if payload["campaign_revision"] != profile.payload["campaign_revision"]:
        raise P2ContractError("candidate proposal campaign revision is stale")
    controls = list(payload["frozen_controls"])
    candidates = list(payload["preregistered_candidates"])
    rows = controls + candidates
    identifiers = [str(item["candidate_id"]) for item in rows]
    if len(controls) != 4 or len(candidates) != 8 or len(set(identifiers)) != 12:
        raise P2ContractError("candidate proposal must contain exactly four controls and eight candidates")
    if any(item["candidate_class"] != "frozen_control" for item in controls):
        raise P2ContractError("frozen control proposal class is invalid")
    if any(item["candidate_class"] != "preregistered_patent" for item in candidates):
        raise P2ContractError("preregistered proposal class is invalid")
    for item in rows:
        if item["registered"] is not False or item["hash_locked"] is not False:
            raise P2ContractError("candidate proposal cannot register or hash-lock a candidate")
        for lineage_name in ("spec", "config", "retriever", "evaluator"):
            lineage = item[lineage_name]
            if lineage["required"] is not True or not lineage["source_locations"]:
                raise P2ContractError(f"candidate proposal {lineage_name} lineage is incomplete")
    historical_tracked_proposal = _is_bound_historical_candidate_proposal(
        payload, repository_root
    )
    for source in payload["source_bindings"]:
        uri = str(source["uri"])
        path = _resolve_proposal_locator(repository_root, uri, "proposal source uri")
        if file_sha256(path) != source["sha256"] and not historical_tracked_proposal:
            raise P2ContractError("candidate proposal source binding is stale")
    for lineage_name, lineage in payload["lineage_requirements"].items():
        for locator in lineage["source_locations"]:
            _resolve_proposal_locator(
                repository_root,
                str(locator),
                f"proposal {lineage_name} source location",
            )
    for item in rows:
        for lineage_name in ("spec", "config", "retriever", "evaluator"):
            for locator in item[lineage_name]["source_locations"]:
                _resolve_proposal_locator(
                    repository_root,
                    str(locator),
                    f"proposal candidate {lineage_name} source location",
                )


def _is_bound_historical_candidate_proposal(
    payload: Mapping[str, Any], repository_root: Path
) -> bool:
    root = Path(repository_root).resolve()
    try:
        source_of_truth = yaml.safe_load(
            (root / "control/source-of-truth.yaml").read_text(encoding="utf-8")
        )
    except (OSError, yaml.YAMLError):
        return False
    if not isinstance(source_of_truth, Mapping):
        return False
    records = source_of_truth.get("records")
    if not isinstance(records, list):
        return False
    active_revision: str | None = None
    for record in records:
        if not isinstance(record, Mapping) or record.get("id") != "p2_campaign_revision":
            continue
        authority = record.get("authority")
        if not isinstance(authority, str):
            return False
        try:
            revision = yaml.safe_load((root / authority).read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            return False
        if isinstance(revision, Mapping):
            active_revision = str(revision.get("campaign_revision", ""))
        break
    if not active_revision or active_revision == payload.get("campaign_revision"):
        return False

    proposal_path = root / HISTORICAL_PROPOSAL_RELATIVE_PATH
    session_path = root / HISTORICAL_PROPOSAL_SESSION_RELATIVE_PATH
    try:
        tracked_payload = json.loads(proposal_path.read_text(encoding="utf-8"))
        session = json.loads(session_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if tracked_payload != dict(payload):
        return False
    tracked_sha256 = sha256(
        proposal_path.read_text(encoding="utf-8").encode("utf-8")
    ).hexdigest()
    for event in session.get("events", []):
        if not isinstance(event, Mapping):
            continue
        for reference in event.get("evidence_refs", []):
            if not isinstance(reference, Mapping):
                continue
            if (
                reference.get("path") == HISTORICAL_PROPOSAL_RELATIVE_PATH.as_posix()
                and reference.get("sha256") == tracked_sha256
            ):
                return True
    return False


def _reject_absolute_paths(value: Any, *, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_absolute_paths(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_absolute_paths(item, path=f"{path}[{index}]")
    elif isinstance(value, str):
        if Path(value).is_absolute() or PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute():
            raise P2ContractError(f"absolute path is forbidden in repository-safe P2 artifact at {path}")


def _resolve_proposal_locator(repository_root: Path, value: str, field: str) -> Path:
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or parsed.query or not parsed.path:
        raise P2ContractError(f"{field} must be a repository-relative file locator")
    relative = _validate_safe_relative_uri(parsed.path, field)
    unresolved = repository_root / relative
    resolved = unresolved.resolve()
    try:
        resolved.relative_to(repository_root)
    except ValueError as error:
        raise P2ContractError(f"{field} resolves outside the repository") from error
    if unresolved.is_symlink() or not resolved.is_file():
        raise P2ContractError(f"{field} does not reference a regular repository file")
    return resolved


def _git_commit_exists(repository_root: Path, commit: str) -> bool:
    try:
        completed = subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            cwd=repository_root,
            check=False,
            capture_output=True,
        )
    except OSError:
        return False
    return completed.returncode == 0


def validate_p2_aggregate_metric(
    payload: Mapping[str, Any],
    *,
    selection: bool = False,
) -> dict[str, Any]:
    """Validate the one allowlisted aggregate metric row used by P2 artifacts."""

    if not isinstance(payload, Mapping):
        raise P2ContractError("P2 aggregate metric must be a JSON object")
    try:
        assert_aggregate_only(payload)
    except ValueError as error:
        raise P2ContractError(str(error)) from error
    _validate_schema(payload, AGGREGATE_METRIC_SCHEMA)
    if selection and (
        payload["split"] != "selection"
        or payload["scope"] != "OUT"
        or payload["evidence_role"] != "primary"
    ):
        raise P2ContractError("selection result must be the aggregate selection/OUT primary metric")
    return dict(payload)


def validate_p2_train_metric(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the canonical train/OUT primary decision metric."""

    if not isinstance(payload, Mapping):
        raise P2ContractError("P2 train metric must be a JSON object")
    try:
        assert_aggregate_only(payload)
    except ValueError as error:
        raise P2ContractError(str(error)) from error
    _validate_schema(payload, TRAIN_METRIC_SCHEMA)
    return dict(payload)


def validate_p2_package_bundle(
    *,
    request: Mapping[str, Any],
    ledger: Mapping[str, Any],
    commitment: Mapping[str, Any],
    baseline: Mapping[str, Any],
    freeze: Mapping[str, Any],
    selection: Mapping[str, Any] | None,
    manifest: Mapping[str, Any],
    package: Mapping[str, Any],
    repository_root: Path,
    artifact_root: Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Validate one complete fixture or measured P2 artifact graph semantically."""

    root = Path(repository_root).resolve()
    package_artifact_root = (
        Path(artifact_root).resolve() if artifact_root is not None else root
    )
    artifacts = {
        "request": validate_p2_artifact(request, repository_root=root),
        "ledger": validate_p2_artifact(ledger, repository_root=root),
        "commitment": validate_p2_artifact(commitment, repository_root=root),
        "baseline": validate_p2_artifact(baseline, repository_root=root),
        "freeze": validate_p2_artifact(freeze, repository_root=root),
        "manifest": validate_p2_artifact(manifest, repository_root=root),
        "package": validate_p2_artifact(package, repository_root=root),
    }
    if selection is not None:
        artifacts["selection"] = validate_p2_artifact(selection, repository_root=root)
    expected_versions = {
        "request": "myis.p2-request.v1",
        "ledger": "myis.p2-candidate-ledger.v1",
        "commitment": "myis.p2-baseline-commitment.v1",
        "baseline": "myis.p2-baseline-reproduction-receipt.v1",
        "freeze": "myis.p2-shortlist-freeze-receipt.v1",
        "selection": "myis.p2-selection-receipt.v1",
        "manifest": "myis.p2-manifest.v1",
        "package": "myis.p2-package.v1",
    }
    for name, row in artifacts.items():
        _require_semantic(row["schema_version"] == expected_versions[name], f"{name} artifact schema mismatch")
    request_row = artifacts["request"]
    ledger_row = artifacts["ledger"]
    commitment_row = artifacts["commitment"]
    baseline_row = artifacts["baseline"]
    freeze_row = artifacts["freeze"]
    selection_row = artifacts.get("selection")
    manifest_row = artifacts["manifest"]
    package_row = artifacts["package"]
    profile = load_profile_by_id(root, str(request_row["budget_profile_id"]))
    envelope, envelope_sha256 = _load_envelope_for_profile(root, profile)

    _require_semantic(request_row["execution_envelope_sha256"] == envelope_sha256, "request envelope hash mismatch")
    scope = envelope.get("scope", {})
    _require_semantic(scope.get("phase_id") == "P2_SCOPE_DEVELOPMENT", "envelope phase mismatch")
    _require_semantic(scope.get("arm") == "R1", "envelope arm mismatch")
    _require_semantic(scope.get("campaign_id") == profile.payload["campaign_id"], "envelope campaign mismatch")
    _require_semantic(scope.get("campaign_revision") == profile.payload["campaign_revision"], "envelope campaign revision mismatch")
    expected_profile_ref = (
        Path("control/budgets") / f"{profile.profile_id}.yaml"
    ).as_posix()
    _require_semantic(scope.get("budget_profile_ref") == expected_profile_ref, "envelope budget profile reference mismatch")
    _require_semantic(scope.get("train_selection_only") is True, "envelope must remain train/selection only")
    _require_semantic(scope.get("final_split_open") is False, "envelope final split must remain closed")
    _require_semantic(scope.get("selection_access_requires_shortlist_freeze") is True, "envelope freeze barrier mismatch")
    resources = envelope.get("resources", {})
    _require_semantic(resources.get("gpu") is False and resources.get("paid_api") is False, "envelope resource boundary mismatch")
    _require_semantic(resources.get("network_model_download") is False and resources.get("provider_fallback") is False, "envelope provider boundary mismatch")

    request_id = request_row["request_id"]
    campaign_revision = profile.payload["campaign_revision"]
    for name, row in artifacts.items():
        if name != "package":
            _require_semantic(row.get("request_id") == request_id, f"{name} request_id mismatch")
        if "campaign_revision" in row:
            _require_semantic(row["campaign_revision"] == campaign_revision, f"{name} campaign revision mismatch")

    candidates = list(ledger_row["candidates"])
    baseline_matches = [
        item
        for item in candidates
        if str(item["candidate_id"]) == str(commitment_row["baseline_candidate_id"])
    ]
    _require_semantic(len(baseline_matches) == 1, "baseline candidate must occur exactly once in the ledger")
    candidate_by_id = {str(item["candidate_id"]): item for item in candidates}
    _require_semantic(len(candidate_by_id) == len(candidates), "ledger candidate IDs must be unique")
    _require_semantic(ledger_row["candidate_count"] == len(candidates), "ledger candidate_count mismatch")
    counts = {
        candidate_class: sum(item["class"] == candidate_class for item in candidates)
        for candidate_class in ("frozen_control", "preregistered_patent", "adaptive_autoindex")
    }
    allocation = profile.payload["candidate_allocation"]
    _require_semantic(counts["frozen_control"] == allocation["frozen_controls"], "ledger frozen control count mismatch")
    _require_semantic(counts["preregistered_patent"] == allocation["preregistered_patent_candidates"], "ledger preregistered count mismatch")
    _require_semantic(
        all(
            (item["class"] == "adaptive_autoindex" and int(item["iteration"]) >= 1)
            or (item["class"] != "adaptive_autoindex" and int(item["iteration"]) == 0)
            for item in candidates
        ),
        "ledger candidate class and iteration mismatch",
    )
    _require_semantic(
        all(item["class"] == "frozen_control" or item["arm"] == "R1" for item in candidates),
        "preregistered and adaptive candidates must use arm R1",
    )
    _require_semantic(
        all(
            item.get("status") in {"train_complete", "rejected", "frozen"}
            and isinstance(item.get("train_metric"), Mapping)
            for item in candidates
        ),
        "complete ledger contains an incomplete train outcome",
    )
    train_metrics = [validate_p2_train_metric(item["train_metric"]) for item in candidates]
    for candidate, metric in zip(candidates, train_metrics, strict=True):
        _require_semantic(metric["candidate_id"] == candidate["candidate_id"], "train metric candidate ID differs from the ledger")
        _require_semantic(metric["arm"] == candidate["arm"], "train metric arm differs from the ledger")
    comparison_signatures = {
        tuple(metric[field] for field in TRAIN_METRIC_COMPARISON_FIELDS)
        for metric in train_metrics
    }
    _require_semantic(
        len(comparison_signatures) == 1,
        "all comparable train metrics must share metric identity, n, denominator, and lineage",
    )
    _require_semantic(
        sum(int(item.get("index_build_count", 0)) for item in candidates) <= profile.payload["limits"]["max_index_builds"],
        "ledger index build budget exceeded",
    )
    frozen_control_ids = {str(item["candidate_id"]) for item in candidates if item["class"] == "frozen_control"}
    _require_semantic(frozen_control_ids == set(request_row["frozen_controls"]), "request frozen controls do not match the ledger")
    _require_semantic(
        ledger_row["baseline_commitment_sha256"] == commitment_row["commitment_sha256"],
        "ledger baseline commitment reference mismatch",
    )

    iterations = list(ledger_row["iterations"])
    iteration_numbers = [int(item["iteration"]) for item in iterations]
    _require_semantic(iteration_numbers == list(range(1, len(iterations) + 1)), "adaptive iterations must be consecutive")
    _require_semantic(
        0 <= len(iterations) <= profile.payload["limits"]["max_adaptive_iterations"],
        "complete ledger adaptive iteration count exceeds the profile",
    )
    seen_adaptive: set[str] = set()
    iteration_metrics: list[dict[str, Any]] = []
    for record in iterations:
        member_ids = [str(item) for item in record["candidate_ids"]]
        expected_members = {
            str(item["candidate_id"])
            for item in candidates
            if item["class"] == "adaptive_autoindex" and item["iteration"] == record["iteration"]
        }
        _require_semantic(len(member_ids) == profile.payload["limits"]["candidates_per_iteration"], "adaptive iteration must contain exactly four candidates")
        _require_semantic(set(member_ids) == expected_members, "adaptive iteration membership does not match the ledger")
        _require_semantic(not (seen_adaptive & set(member_ids)), "adaptive iteration membership overlaps")
        seen_adaptive.update(member_ids)
        outcomes = [candidate_by_id[candidate_id] for candidate_id in member_ids]
        _require_semantic(all(item.get("status") in {"train_complete", "rejected", "frozen"} for item in outcomes), "adaptive iteration has incomplete train outcomes")
        derived_metric = max(
            (item["train_metric"] for item in sorted(outcomes, key=lambda item: str(item["candidate_id"]))),
            key=lambda metric: float(metric["value"]),
        )
        _require_semantic(record["best_metric"] == derived_metric, "adaptive iteration metric is not derived from train outcomes")
        iteration_metrics.append(dict(derived_metric))
    _require_semantic(seen_adaptive == {str(item["candidate_id"]) for item in candidates if item["class"] == "adaptive_autoindex"}, "adaptive candidates are missing from iteration records")
    if len(iterations) < profile.payload["limits"]["max_adaptive_iterations"]:
        stop_reason = ledger_row.get("stop_reason")
        valid_reasons = set(profile.payload.get("stopping", {}).get("valid_reasons", []))
        _require_semantic(
            _early_stop_eligible(iteration_metrics, profile.payload["stopping"])
            or stop_reason in valid_reasons,
            "adaptive search stopped without valid early-stop evidence or stopping reason",
        )

    commitment_candidate = baseline_matches[0]
    _require_semantic(commitment_candidate["class"] == "frozen_control", "baseline identity is not a frozen control in the ledger")
    _require_semantic(commitment_candidate["arm"] == commitment_row["baseline_arm"], "baseline commitment arm differs from the ledger")
    expected_metric = commitment_row["expected_metric"]
    _require_semantic(expected_metric["candidate_id"] == commitment_row["baseline_candidate_id"], "baseline commitment metric candidate mismatch")
    _require_semantic(expected_metric["arm"] == commitment_row["baseline_arm"], "baseline commitment metric arm mismatch")
    _require_semantic(expected_metric["dataset_lineage_sha256"] in request_row["input_hashes"].values(), "baseline dataset lineage is not bound by the request")
    request_scope_hashes = set(request_row["scope_hashes"].values())
    for lineage_field in ("config_sha256", "retriever_sha256", "evaluator_sha256"):
        _require_semantic(expected_metric[lineage_field] in request_scope_hashes, f"baseline {lineage_field} is not bound by the request")
    _validate_prior_baseline_artifact(root, commitment_row)

    _require_semantic(baseline_row["baseline_commitment_sha256"] == commitment_row["commitment_sha256"], "baseline reproduction commitment reference mismatch")
    _require_semantic(baseline_row["baseline_id"] == commitment_row["baseline_candidate_id"], "baseline reproduction candidate differs from commitment")
    _require_semantic(baseline_row["expected_metric"] == expected_metric, "baseline reproduction expectation differs from commitment")
    _require_semantic(float(baseline_row["tolerance"]) == float(commitment_row["tolerance"]), "baseline reproduction tolerance differs from commitment")
    result_metric = baseline_row["result"]
    _require_semantic(
        all(expected_metric[key] == result_metric[key] for key in TRAIN_METRIC_IDENTITY_FIELDS),
        "baseline result identity differs from its expectation",
    )
    _require_semantic(
        result_metric == commitment_candidate["train_metric"],
        "baseline reproduction result differs from the baseline candidate train metric",
    )
    reproduced = abs(float(result_metric["value"]) - float(expected_metric["value"])) <= float(baseline_row["tolerance"])
    _require_semantic((baseline_row["status"] == "passed") == reproduced, "baseline status does not match expected metric and tolerance")
    _require_semantic(baseline_row["status"] == "passed", "complete package requires a passed baseline reproduction")

    freeze_ids = [str(item) for item in freeze_row["candidate_ids"]]
    incumbent_value = float(commitment_candidate["train_metric"]["value"])
    shortlist_groups: dict[float, list[str]] = {}
    for candidate in candidates:
        value = float(candidate["train_metric"]["value"])
        if value > incumbent_value:
            shortlist_groups.setdefault(value, []).append(str(candidate["candidate_id"]))
    expected_freeze_ids: list[str] = []
    for value in sorted(shortlist_groups, reverse=True):
        group = shortlist_groups[value]
        if len(group) != 1:
            continue
        if len(expected_freeze_ids) >= profile.payload["limits"]["max_selection_finalists"]:
            break
        expected_freeze_ids.append(group[0])
    _require_semantic(
        freeze_ids == expected_freeze_ids,
        "freeze shortlist is not derived from canonical train metrics and the committed baseline",
    )
    _require_semantic(set(freeze_ids).issubset(candidate_by_id), "freeze contains candidates outside the ledger")
    _require_semantic(set(freeze_row["candidate_spec_hashes"]) == set(freeze_ids), "freeze spec map membership mismatch")
    ledger_frozen_ids = {
        str(item["candidate_id"])
        for item in candidates
        if item.get("status") == "frozen" or item.get("selection_eligible") is True
    }
    _require_semantic(ledger_frozen_ids == set(freeze_ids), "ledger frozen membership differs from the freeze receipt")
    for candidate_id in freeze_ids:
        candidate = candidate_by_id[candidate_id]
        _require_semantic(freeze_row["candidate_spec_hashes"][candidate_id] == candidate["spec_sha256"], "freeze spec hash differs from the ledger")
        _require_semantic(candidate.get("status") == "frozen" and candidate.get("selection_eligible") is True, "freeze candidate is not marked eligible in the ledger")
    _require_semantic(freeze_row["baseline_commitment_sha256"] == commitment_row["commitment_sha256"], "freeze baseline commitment reference mismatch")
    _require_semantic(freeze_row["baseline_reproduction_receipt_sha256"] == baseline_row["receipt_sha256"], "freeze baseline receipt reference mismatch")
    for lineage_field in ("config_sha256", "retriever_sha256", "evaluator_sha256"):
        _require_semantic(freeze_row[lineage_field] == expected_metric[lineage_field], f"freeze {lineage_field} differs from baseline lineage")
    for lineage_field in ("compiler_sha256", "config_sha256", "retriever_sha256", "evaluator_sha256"):
        _require_semantic(freeze_row[lineage_field] in request_scope_hashes, f"freeze {lineage_field} is not bound by the request")

    if freeze_ids:
        _require_semantic(selection_row is not None, "nonempty frozen shortlist requires a selection receipt")
        _require_semantic(selection_row["candidate_ids"] == freeze_ids, "selection membership differs from the frozen shortlist")
        _require_semantic(selection_row["shortlist_freeze_receipt_sha256"] == freeze_row["receipt_sha256"], "selection freeze reference mismatch")
        _require_semantic(selection_row["selection_exposure_count"] == 1 and selection_row["status"] == "accepted", "complete package requires one accepted selection exposure")
        selection_metrics = selection_row["metrics"]
        selection_metric_ids = [str(item["candidate_id"]) for item in selection_metrics]
        _require_semantic(selection_metric_ids == freeze_ids and len(selection_metric_ids) == len(set(selection_metric_ids)), "selection requires exactly one ordered aggregate result per finalist")
        selection_receipt_sha256: str | None = selection_row["receipt_sha256"]
        selection_exposure_count = 1
    else:
        _require_semantic(selection_row is None, "empty frozen shortlist cannot have a selection receipt")
        selection_metrics = []
        selection_receipt_sha256 = None
        selection_exposure_count = 0

    request_sha256 = canonical_sha256(request_row)
    expected_manifest_refs = {
        "request_sha256": request_sha256,
        "candidate_ledger_sha256": ledger_row["ledger_sha256"],
        "baseline_commitment_sha256": commitment_row["commitment_sha256"],
        "baseline_reproduction_receipt_sha256": baseline_row["receipt_sha256"],
        "shortlist_freeze_receipt_sha256": freeze_row["receipt_sha256"],
        "selection_receipt_sha256": selection_receipt_sha256,
    }
    _require_semantic(manifest_row["request_id"] == request_id, "manifest request ID mismatch")
    _require_semantic(manifest_row["candidate_count"] == ledger_row["candidate_count"], "manifest candidate count mismatch")
    _require_semantic(manifest_row["candidate_ids"] == freeze_ids, "manifest finalist membership mismatch")
    _require_semantic(manifest_row["selection_exposure_count"] == selection_exposure_count, "manifest exposure count mismatch")
    _require_semantic(manifest_row["metrics"] == selection_metrics, "manifest metrics differ from the selection receipt")
    for field, expected in expected_manifest_refs.items():
        _require_semantic(manifest_row[field] == expected, f"manifest {field} mismatch")

    expected_manifest_status = {"validated_structural": "valid", "negative_development": "negative_development"}.get(package_row["status"])
    _require_semantic(expected_manifest_status is not None and manifest_row["status"] == expected_manifest_status, "package and manifest statuses are incoherent")
    _require_semantic(manifest_row["evidence_class"] in {"fixture", "train_selection_measured"}, "complete manifest evidence class is invalid")
    expected_package_refs = {
        "request_sha256": request_sha256,
        "candidate_ledger_sha256": ledger_row["ledger_sha256"],
        "baseline_commitment_sha256": commitment_row["commitment_sha256"],
        "baseline_reproduction_sha256": baseline_row["receipt_sha256"],
        "shortlist_freeze_sha256": freeze_row["receipt_sha256"],
        "selection_sha256": selection_receipt_sha256,
        "manifest_sha256": manifest_row["manifest_sha256"],
    }
    _require_semantic(package_row["request_id"] == request_id, "package request ID mismatch")
    _require_semantic(package_row["campaign_revision"] == campaign_revision, "package campaign revision mismatch")
    _require_semantic(package_row["candidate_count"] == ledger_row["candidate_count"], "package candidate count mismatch")
    _require_semantic(package_row["selection_exposure_count"] == selection_exposure_count, "package exposure count mismatch")
    for field, expected in expected_package_refs.items():
        _require_semantic(package_row[field] == expected, f"package {field} mismatch")
    uri_fields = {
        "request": "request_uri",
        "ledger": "candidate_ledger_uri",
        "commitment": "baseline_commitment_uri",
        "baseline": "baseline_reproduction_uri",
        "freeze": "shortlist_freeze_uri",
        "selection": "selection_uri",
        "manifest": "manifest_uri",
    }
    for artifact_name, field in uri_fields.items():
        value = package_row[field]
        if value is None:
            _require_semantic(artifact_name == "selection" and selection_row is None, f"package {field} cannot be null")
            continue
        referenced = _load_referenced_artifact(
            package_artifact_root, str(value), field
        )
        _require_semantic(referenced == artifacts[artifact_name], f"package {field} does not resolve to the supplied artifact")
    if not freeze_ids:
        _require_semantic(package_row["status"] == "negative_development", "empty shortlist package must be negative development")
    return artifacts


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_envelope_for_profile(
    repository_root: Path,
    profile: P2BudgetProfile,
) -> tuple[dict[str, Any], str]:
    root = Path(repository_root).resolve()
    expected_profile_ref = (
        Path("control/budgets") / f"{profile.profile_id}.yaml"
    ).as_posix()
    matches: list[tuple[dict[str, Any], str]] = []
    for path in sorted((root / "control").glob("execution-envelope-p2*.yaml")):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            continue
        if not isinstance(payload, dict):
            continue
        scope = payload.get("scope")
        if not isinstance(scope, Mapping):
            continue
        if (
            scope.get("budget_profile_ref") == expected_profile_ref
            and scope.get("campaign_revision")
            == profile.payload["campaign_revision"]
        ):
            matches.append((dict(payload), file_sha256(path)))
    if len(matches) != 1:
        raise P2ContractError(
            f"expected exactly one P2 execution envelope for {profile.profile_id}"
        )
    return matches[0]


def _require_semantic(condition: bool, message: str) -> None:
    if not condition:
        raise P2ContractError(message)


def _early_stop_eligible(metrics: list[Mapping[str, Any]], stopping: Mapping[str, Any]) -> bool:
    best: float | None = None
    no_improvement_streak = 0
    for metric in metrics:
        score = float(metric["value"])
        if best is None or score > best:
            best = score
            no_improvement_streak = 0
        else:
            no_improvement_streak += 1
    return (
        len(metrics) >= int(stopping["min_iterations_before_early_stop"])
        and no_improvement_streak >= int(stopping["no_improvement_patience"])
    )


def _validate_safe_relative_uri(value: str, field: str) -> Path:
    candidate = Path(value)
    if not value.strip() or candidate.is_absolute() or ".." in candidate.parts:
        raise P2ContractError(f"package {field} must be a safe repository-relative URI")
    try:
        assert_path_not_protected(value)
    except PermissionError as error:
        raise P2ContractError(str(error)) from error
    return candidate


def _load_referenced_artifact(repository_root: Path, value: str, field: str) -> dict[str, Any]:
    path = _resolve_referenced_artifact_path(repository_root, value, field)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise P2ContractError(f"package {field} cannot be loaded") from error
    if not isinstance(payload, dict):
        raise P2ContractError(f"package {field} must reference a JSON object")
    return payload


def _resolve_referenced_artifact_path(repository_root: Path, value: str, field: str) -> Path:
    relative = _validate_safe_relative_uri(value, field)
    unresolved = repository_root / relative
    path = unresolved.resolve()
    try:
        path.relative_to(repository_root)
    except ValueError as error:
        raise P2ContractError(f"package {field} resolves outside the repository") from error
    if unresolved.is_symlink() or not path.is_file():
        raise P2ContractError(f"package {field} does not reference a regular artifact file")
    return path


def _validate_prior_baseline_artifact(
    repository_root: Path,
    commitment: Mapping[str, Any],
) -> None:
    path = _resolve_referenced_artifact_path(
        repository_root,
        str(commitment["prior_artifact_uri"]),
        "prior_artifact_uri",
    )
    _require_semantic(
        file_sha256(path) == commitment["prior_artifact_sha256"],
        "baseline commitment prior artifact SHA-256 is stale",
    )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise P2ContractError("baseline commitment prior artifact cannot be loaded") from error
    if not isinstance(payload, dict):
        raise P2ContractError("baseline commitment prior artifact must be a JSON object")
    try:
        receipt = validate_receipt(payload)
    except (OwnerLocalContractError, PermissionError, ValueError) as error:
        raise P2ContractError("baseline commitment prior artifact is not a valid safe owner-local receipt") from error
    _require_semantic(
        receipt["decision_id"] == "P1_CPU_EXECUTION_ENVELOPE" and receipt["status"] == "accepted",
        "baseline commitment prior artifact is not accepted P1 evidence",
    )
    index = int(commitment["metric_locator"]["metrics_index"])
    metrics = receipt.get("metrics")
    _require_semantic(
        isinstance(metrics, list) and index < len(metrics) and isinstance(metrics[index], Mapping),
        "baseline commitment metric locator is invalid",
    )
    prior_metric = metrics[index]
    expected = commitment["expected_metric"]
    prior_direction = "higher_is_better" if prior_metric.get("direction") == "maximize" else prior_metric.get("direction")
    expected_bindings = {
        "arm": prior_metric.get("arm"),
        "metric_name": prior_metric.get("name"),
        "data_role": prior_metric.get("split"),
        "scope": prior_metric.get("scope"),
        "evidence_role": prior_metric.get("evidence_role"),
        "direction": prior_direction,
        "value": prior_metric.get("value"),
        "n": prior_metric.get("n"),
        "denominator": prior_metric.get("denominator"),
        "dataset_lineage_sha256": receipt.get("lineage_hashes", {}).get("dataset_sha256"),
        "evaluator_sha256": receipt.get("lineage_hashes", {}).get("evaluator_sha256"),
    }
    _require_semantic(
        commitment["baseline_arm"] == prior_metric.get("arm"),
        "baseline commitment arm differs from prior P1 evidence",
    )
    _require_semantic(
        all(expected[field] == value for field, value in expected_bindings.items()),
        "baseline commitment expected metric differs from prior P1 evidence",
    )


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


@lru_cache(maxsize=1)
def _schema_registry() -> tuple[dict[str, dict[str, Any]], Registry]:
    schema_root = _repository_root() / "schemas"
    schemas: dict[str, dict[str, Any]] = {}
    registry = Registry()
    try:
        for path in sorted(schema_root.glob("*.json")):
            schema = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(schema, dict):
                continue
            schemas[path.name] = schema
            schema_id = schema.get("$id")
            if isinstance(schema_id, str) and schema_id:
                registry = registry.with_resource(schema_id, Resource.from_contents(schema))
    except (OSError, json.JSONDecodeError) as error:
        raise P2ContractError(f"cannot load schema registry from {schema_root}") from error
    return schemas, registry


def _validate_schema(payload: Mapping[str, Any], schema_name: str) -> None:
    try:
        schemas, registry = _schema_registry()
        schema = schemas[schema_name]
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema, registry=registry).validate(dict(payload))
    except (KeyError, SchemaError, ValidationError, Unresolvable) as error:
        raise P2ContractError(f"JSON Schema validation failed for {schema_name}: {error}") from error
