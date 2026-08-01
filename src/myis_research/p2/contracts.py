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
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable

from ..kernel.canonical import canonical_json, canonical_sha256, file_sha256
from ..protection import assert_aggregate_only, assert_path_not_protected


PROFILE_RELATIVE_PATH = Path("control/budgets/p2-r1-primary-v1.yaml")
ENVELOPE_RELATIVE_PATH = Path("control/execution-envelope-p2.yaml")
PROFILE_SCHEMA = "p2-budget-profile.v1.json"
REQUEST_SCHEMA = "p2-request.v1.json"
AGGREGATE_METRIC_SCHEMA = "p2-aggregate-metric.v1.json"
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
GIT_RE = re.compile(r"^(?:[a-f0-9]{40}|[a-f0-9]{64})$")
P2_ARTIFACT_SCHEMAS = {
    "myis.p2-request.v1": "p2-request.v1.json",
    "myis.p2-candidate-ledger.v1": "p2-candidate-ledger.v1.json",
    "myis.p2-baseline-reproduction-receipt.v1": "p2-baseline-reproduction-receipt.v1.json",
    "myis.p2-shortlist-freeze-receipt.v1": "p2-shortlist-freeze-receipt.v1.json",
    "myis.p2-selection-receipt.v1": "p2-selection-receipt.v1.json",
    "myis.p2-manifest.v1": "p2-manifest.v1.json",
    "myis.p2-package.v1": "p2-package.v1.json",
}
P2_HASH_FIELDS = {
    "myis.p2-candidate-ledger.v1": "ledger_sha256",
    "myis.p2-baseline-reproduction-receipt.v1": "receipt_sha256",
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
    payload = validate_p2_artifact(payload, repository_root=root)
    _reject_hidden_defaults(payload)
    profile = load_profile(root)
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
    return validate_p2_artifact(body, repository_root=repository_root)


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
    profile = load_profile(root)
    if payload.get("budget_profile_id") != profile.profile_id:
        raise P2ContractError("P2 artifact budget_profile_id does not match the canonical profile")
    if payload.get("budget_profile_sha256") != profile.sha256:
        raise P2ContractError("P2 artifact budget_profile_sha256 does not match the canonical profile")
    campaign_revision = payload.get("campaign_revision")
    if campaign_revision is not None and campaign_revision != profile.payload["campaign_revision"]:
        raise P2ContractError("P2 artifact campaign_revision does not match the canonical profile")
    if schema_version == "myis.p2-request.v1":
        envelope_path = root / ENVELOPE_RELATIVE_PATH
        if not envelope_path.is_file() or file_sha256(envelope_path) != payload["execution_envelope_sha256"]:
            raise P2ContractError("request execution envelope hash is stale or missing")
        if payload["campaign_id"] != profile.payload["campaign_id"]:
            raise P2ContractError("request campaign_id does not match the canonical profile")
    elif schema_version == "myis.p2-candidate-ledger.v1":
        if payload["candidate_count"] != len(payload["candidates"]):
            raise P2ContractError("candidate_count does not match the candidates array")
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


def validate_p2_package_bundle(
    *,
    request: Mapping[str, Any],
    ledger: Mapping[str, Any],
    baseline: Mapping[str, Any],
    freeze: Mapping[str, Any],
    selection: Mapping[str, Any] | None,
    manifest: Mapping[str, Any],
    package: Mapping[str, Any],
    repository_root: Path,
) -> dict[str, dict[str, Any]]:
    """Validate one complete fixture or measured P2 artifact graph semantically."""

    root = Path(repository_root).resolve()
    artifacts = {
        "request": validate_p2_artifact(request, repository_root=root),
        "ledger": validate_p2_artifact(ledger, repository_root=root),
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
    baseline_row = artifacts["baseline"]
    freeze_row = artifacts["freeze"]
    selection_row = artifacts.get("selection")
    manifest_row = artifacts["manifest"]
    package_row = artifacts["package"]
    profile = load_profile(root)
    envelope, envelope_sha256 = _load_envelope(root)

    _require_semantic(request_row["execution_envelope_sha256"] == envelope_sha256, "request envelope hash mismatch")
    scope = envelope.get("scope", {})
    _require_semantic(scope.get("phase_id") == "P2_SCOPE_DEVELOPMENT", "envelope phase mismatch")
    _require_semantic(scope.get("arm") == "R1", "envelope arm mismatch")
    _require_semantic(scope.get("campaign_id") == profile.payload["campaign_id"], "envelope campaign mismatch")
    _require_semantic(scope.get("campaign_revision") == profile.payload["campaign_revision"], "envelope campaign revision mismatch")
    _require_semantic(scope.get("budget_profile_ref") == PROFILE_RELATIVE_PATH.as_posix(), "envelope budget profile reference mismatch")
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
        all(item.get("status") in {"train_complete", "rejected", "frozen"} and item.get("train_score") is not None for item in candidates),
        "complete ledger contains an incomplete train outcome",
    )
    _require_semantic(
        sum(int(item.get("index_build_count", 0)) for item in candidates) <= profile.payload["limits"]["max_index_builds"],
        "ledger index build budget exceeded",
    )
    frozen_control_ids = {str(item["candidate_id"]) for item in candidates if item["class"] == "frozen_control"}
    _require_semantic(frozen_control_ids == set(request_row["frozen_controls"]), "request frozen controls do not match the ledger")

    iterations = list(ledger_row["iterations"])
    iteration_numbers = [int(item["iteration"]) for item in iterations]
    _require_semantic(iteration_numbers == list(range(1, len(iterations) + 1)), "adaptive iterations must be consecutive")
    _require_semantic(len(iterations) in {4, 5}, "complete ledger must contain four or five adaptive iterations")
    seen_adaptive: set[str] = set()
    iteration_scores: list[float] = []
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
        derived_score = max(float(item["train_score"]) for item in outcomes)
        _require_semantic(float(record["best_score"]) == derived_score, "adaptive iteration score is not derived from train outcomes")
        iteration_scores.append(derived_score)
    _require_semantic(seen_adaptive == {str(item["candidate_id"]) for item in candidates if item["class"] == "adaptive_autoindex"}, "adaptive candidates are missing from iteration records")
    if len(iterations) < profile.payload["limits"]["max_adaptive_iterations"]:
        _require_semantic(_early_stop_eligible(iteration_scores, profile.payload["stopping"]), "adaptive search stopped without valid early-stop evidence")

    expected_metric = baseline_row["expected_metric"]
    result_metric = baseline_row["result"]
    baseline_candidate = candidate_by_id.get(str(baseline_row["baseline_id"]))
    _require_semantic(
        baseline_candidate is not None and baseline_candidate["class"] == "frozen_control",
        "baseline identity is not a frozen control in the ledger",
    )
    metric_identity_fields = ("candidate_id", "name", "n", "scope", "split", "direction", "denominator", "evidence_role")
    _require_semantic(all(expected_metric[key] == result_metric[key] for key in metric_identity_fields), "baseline result identity differs from its expectation")
    reproduced = abs(float(result_metric["value"]) - float(expected_metric["value"])) <= float(baseline_row["tolerance"])
    _require_semantic((baseline_row["status"] == "passed") == reproduced, "baseline status does not match expected metric and tolerance")
    _require_semantic(baseline_row["status"] == "passed", "complete package requires a passed baseline reproduction")
    _require_semantic(baseline_row["dataset_lineage_sha256"] in request_row["input_hashes"].values(), "baseline dataset lineage is not bound by the request")

    freeze_ids = [str(item) for item in freeze_row["candidate_ids"]]
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
    _require_semantic(freeze_row["baseline_reproduction_receipt_sha256"] == baseline_row["receipt_sha256"], "freeze baseline receipt reference mismatch")
    for lineage_field in ("config_sha256", "retriever_sha256", "evaluator_sha256"):
        _require_semantic(freeze_row[lineage_field] == baseline_row[lineage_field], f"freeze {lineage_field} differs from baseline lineage")
    request_scope_hashes = set(request_row["scope_hashes"].values())
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
        referenced = _load_referenced_artifact(root, str(value), field)
        _require_semantic(referenced == artifacts[artifact_name], f"package {field} does not resolve to the supplied artifact")
    if not freeze_ids:
        _require_semantic(package_row["status"] == "negative_development", "empty shortlist package must be negative development")
    return artifacts


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_envelope(repository_root: Path) -> tuple[dict[str, Any], str]:
    path = repository_root / ENVELOPE_RELATIVE_PATH
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise P2ContractError(f"cannot load P2 execution envelope: {path}") from error
    if not isinstance(payload, dict):
        raise P2ContractError("P2 execution envelope must be a mapping")
    return dict(payload), file_sha256(path)


def _require_semantic(condition: bool, message: str) -> None:
    if not condition:
        raise P2ContractError(message)


def _early_stop_eligible(scores: list[float], stopping: Mapping[str, Any]) -> bool:
    best: float | None = None
    no_improvement_streak = 0
    for score in scores:
        if best is None or score > best:
            best = score
            no_improvement_streak = 0
        else:
            no_improvement_streak += 1
    return (
        len(scores) >= int(stopping["min_iterations_before_early_stop"])
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
    relative = _validate_safe_relative_uri(value, field)
    unresolved = repository_root / relative
    path = unresolved.resolve()
    try:
        path.relative_to(repository_root)
    except ValueError as error:
        raise P2ContractError(f"package {field} resolves outside the repository") from error
    if unresolved.is_symlink() or not path.is_file():
        raise P2ContractError(f"package {field} does not reference a regular artifact file")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise P2ContractError(f"package {field} cannot be loaded") from error
    if not isinstance(payload, dict):
        raise P2ContractError(f"package {field} must reference a JSON object")
    return payload


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
