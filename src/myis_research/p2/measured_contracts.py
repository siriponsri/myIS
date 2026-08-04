"""Profile-resolved contracts for Owner-local P2 measured execution."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Mapping

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from ..scope import compile_scope, parse_scope_spec
from .contracts import (
    P2ContractError,
    validate_p2_aggregate_metric,
    validate_p2_train_metric,
)
from .active_binding import active_p2_source_uris


BASE_CONTROL_IDS = (
    "p2-control-r0-flat-bm25",
    "p2-control-r0-window-maxp",
    "p2-control-r1-document-grounded",
    "p2-control-r1-passage-maxp",
)
BASE_CANDIDATE_IDS = (
    "p2-r1-tac-document",
    "p2-r1-title-abstract",
    "p2-r1-claim-view",
    "p2-r1-section-view",
    "p2-r1-claim-element-view",
    "p2-r1-passage-256-maxp",
    "p2-r1-passage-512-maxp",
    "p2-r1-multiview-maxp",
)
BATCH_ROLES = ("exploit", "matched_ablation", "orthogonal", "diversity")
SELF_HASH_FIELDS = {
    "myis.p2-base-candidate-set.v1": "candidate_set_sha256",
    "myis.p2-adaptive-policy.v1": "policy_sha256",
    "myis.p2-proposer-contract.v1": "contract_sha256",
    "myis.p2-adaptive-feedback.v1": "feedback_sha256",
    "myis.p2-scope-candidate-batch.v1": "batch_sha256",
    "myis.p2-proposer-invocation.v1": "invocation_sha256",
    "myis.p2-budget-extension-brief.v1": "brief_sha256",
    "myis.p2-candidate-result.v1": "result_sha256",
}
SCHEMA_FILES = {
    "myis.p2-base-candidate-set.v1": "p2-base-candidate-set.v1.json",
    "myis.p2-adaptive-policy.v1": "p2-adaptive-policy.v1.json",
    "myis.p2-proposer-contract.v1": "p2-proposer-contract.v1.json",
    "myis.p2-measured-request.v1": "p2-measured-request.v1.json",
    "myis.p2-adaptive-feedback.v1": "p2-adaptive-feedback.v1.json",
    "myis.p2-scope-candidate-batch.v1": "p2-scope-candidate-batch.v1.json",
    "myis.p2-proposer-invocation.v1": "p2-proposer-invocation.v1.json",
    "myis.p2-budget-extension-brief.v1": "p2-budget-extension-brief.v1.json",
    "myis.p2-candidate-result.v1": "p2-candidate-result.v1.json",
}
IDENTITY_ONLY_SPEC_FIELDS = frozenset({
    "spec_id",
    "parent_spec_id",
    "hypothesis_id",
    "description",
    "created_at",
    "artifact_uri",
})
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
COMMIT_RE = re.compile(r"^[a-f0-9]{40}$")
VALID_STOP_REASONS = frozenset({
    "wall_clock_exhausted",
    "development_impact_gate",
    "no_grounded_hypotheses",
    "owner_stop_after_checkpoint",
})


def validate_measured_artifact(payload: Mapping[str, Any], repository_root: Path) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise P2ContractError("measured P2 artifact must be a JSON object")
    value = dict(payload)
    schema_version = str(value.get("schema_version", ""))
    schema_file = SCHEMA_FILES.get(schema_version)
    if schema_file is None:
        raise P2ContractError(f"unsupported measured P2 schema: {schema_version!r}")
    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise P2ContractError(str(error)) from error
    schema = _json_file(Path(repository_root) / "schemas" / schema_file)
    try:
        Draft202012Validator(schema).validate(value)
    except ValidationError as error:
        path = "/".join(str(item) for item in error.absolute_path)
        raise P2ContractError(f"{schema_version} JSON Schema validation failed at {path or '$'}: {error.message}") from error
    hash_field = SELF_HASH_FIELDS.get(schema_version)
    if hash_field is not None:
        unsigned = {key: item for key, item in value.items() if key != hash_field}
        if value.get(hash_field) != canonical_sha256(unsigned):
            raise P2ContractError(f"{schema_version} self-hash is invalid")
    if schema_version == "myis.p2-base-candidate-set.v1":
        _validate_base_candidate_set_semantics(value)
    elif schema_version == "myis.p2-adaptive-policy.v1":
        _validate_policy_semantics(value)
    elif schema_version == "myis.p2-scope-candidate-batch.v1":
        _validate_batch_semantics(value)
    elif schema_version == "myis.p2-candidate-result.v1":
        metric = value["metric"]
        if value["data_role"] == "train":
            if metric.get("schema_version") != "myis.p2-train-metric.v1":
                raise P2ContractError("train candidate result requires a P2 train metric")
            if metric.get("candidate_id") != value["candidate_id"]:
                raise P2ContractError("train candidate result metric ID mismatch")
            validate_p2_train_metric(metric)
        elif metric.get("split") != "selection" or metric.get("candidate_id") != value["candidate_id"]:
            raise P2ContractError("selection candidate result metric identity mismatch")
        else:
            validate_p2_aggregate_metric(metric, selection=True)
    return value


def load_measured_request(
    request_path: Path,
    repository_root: Path,
    *,
    require_current_git: bool = True,
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    return validate_measured_request_payload(
        _json_file(Path(request_path)),
        root,
        require_current_git=require_current_git,
    )


def validate_measured_request_payload(
    payload: Mapping[str, Any],
    repository_root: Path,
    *,
    require_current_git: bool = True,
) -> dict[str, Any]:
    """Validate one measured request and resolve every active v2 binding."""

    root = Path(repository_root).resolve()
    request = validate_measured_artifact(payload, root)
    if request["schema_version"] != "myis.p2-measured-request.v1":
        raise P2ContractError("measured runner requires myis.p2-measured-request.v1")
    active = active_p2_source_uris(root)
    if request["budget_profile_uri"] != active["profile"]:
        raise P2ContractError("measured request does not bind the active P2 budget profile")
    if request["execution_envelope_uri"] != active["execution_envelope"]:
        raise P2ContractError("measured request does not bind the active P2 execution envelope")
    profile, profile_hash = load_profile_uri(root, request["budget_profile_uri"])
    envelope, envelope_hash = load_envelope_uri(root, request["execution_envelope_uri"])
    base_set = load_referenced_measured_artifact(root, request["base_candidate_set_uri"])
    policy = load_referenced_measured_artifact(root, request["adaptive_policy_uri"])
    proposer = load_referenced_measured_artifact(root, request["proposer_contract_uri"])
    bindings = (
        (request["budget_profile_id"], profile["profile_id"], "budget profile ID"),
        (request["budget_profile_sha256"], profile_hash, "budget profile hash"),
        (request["execution_envelope_id"], envelope["envelope_id"], "execution envelope ID"),
        (request["execution_envelope_sha256"], envelope_hash, "execution envelope hash"),
        (request["base_candidate_set_id"], base_set["candidate_set_id"], "base candidate set ID"),
        (request["base_candidate_set_sha256"], base_set["candidate_set_sha256"], "base candidate set hash"),
        (request["adaptive_policy_id"], policy["policy_id"], "adaptive policy ID"),
        (request["adaptive_policy_sha256"], policy["policy_sha256"], "adaptive policy hash"),
        (request["proposer_contract_id"], proposer["contract_id"], "proposer contract ID"),
        (request["proposer_contract_sha256"], proposer["contract_sha256"], "proposer contract hash"),
    )
    for recorded, observed, label in bindings:
        if recorded != observed:
            raise P2ContractError(f"measured request {label} mismatch")
    revision = str(profile["campaign_revision"])
    if any(str(item.get("campaign_revision", revision)) != revision for item in (request, envelope, base_set, policy)):
        raise P2ContractError("profile-resolved artifacts disagree on campaign revision")
    campaign = _yaml_file(resolve_safe_uri(root, active["campaign_revision"]))
    if (
        campaign.get("campaign_id") != request["campaign_id"]
        or campaign.get("campaign_revision") != revision
        or campaign.get("budget_profile_ref") != active["profile"]
        or campaign.get("execution_envelope_ref") != active["execution_envelope"]
        or campaign.get("status") != "ready_planned_not_measured"
    ):
        raise P2ContractError("active P2 campaign revision binding is invalid")
    _validate_profile_resources(profile)
    _validate_profile_allocation(profile)
    _validate_envelope(envelope, profile, request["budget_profile_uri"])
    required_scope_hashes = {
        "compiler_sha256",
        "config_sha256",
        "retriever_sha256",
        "evaluator_sha256",
        "evaluator_compatibility_sha256",
    }
    if not required_scope_hashes.issubset(request["scope_hashes"]):
        raise P2ContractError("measured request is missing required scope hashes")
    if request["scope_hashes"]["compiler_sha256"] != base_set["compiler_sha256"]:
        raise P2ContractError("measured request compiler hash differs from the base set")
    if "dataset_lineage_sha256" not in request["input_hashes"]:
        raise P2ContractError("measured request is missing dataset lineage")
    execution_commit = str(request["execution_source_commit"])
    execution_tree = _git(root, "show", "-s", "--format=%T", execution_commit)
    if execution_tree != request["execution_source_tree"]:
        raise P2ContractError("measured request execution-source tree does not match its commit")
    from .evaluator_compatibility import load_evaluator_compatibility

    compatibility = load_evaluator_compatibility(
        root,
        execution_revision=execution_commit,
        expected_sha256=request["scope_hashes"]["evaluator_compatibility_sha256"],
    )
    if request["scope_hashes"]["evaluator_sha256"] != compatibility["current"]["evaluator_sha256"]:
        raise P2ContractError("measured request evaluator hash differs from the compatibility proof")
    from .measured_adapter import current_scope_hashes

    expected_scope_hashes = current_scope_hashes(root, revision=execution_commit)
    for field, expected in expected_scope_hashes.items():
        if request["scope_hashes"].get(field) != expected:
            raise P2ContractError(f"measured request scope hash is stale: {field}")
    if require_current_git:
        identity = git_identity(root)
        if request["execution_source_commit"] != identity["commit"]:
            raise P2ContractError("measured request execution-source commit is stale")
        if request["execution_source_tree"] != identity["tree"]:
            raise P2ContractError("measured request execution-source tree is stale")
        if not identity["worktree_clean"]:
            raise P2ContractError("measured execution requires a clean worktree")
    return {
        **request,
        "_resolved": {
            "profile": profile,
            "envelope": envelope,
            "base_candidate_set": base_set,
            "adaptive_policy": policy,
            "proposer_contract": proposer,
            "campaign_revision": campaign,
            "active_sources": active,
            "evaluator_compatibility": compatibility,
        },
    }


def build_measured_request(
    *,
    repository_root: Path,
    request_id: str,
    budget_profile_uri: str,
    execution_envelope_uri: str,
    base_candidate_set_uri: str,
    adaptive_policy_uri: str,
    proposer_contract_uri: str,
    proposer_identity: Mapping[str, Any],
    input_hashes: Mapping[str, str],
    scope_hashes: Mapping[str, str],
    global_counters: Mapping[str, int],
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    identity = git_identity(root)
    if not identity["worktree_clean"]:
        raise P2ContractError("cannot create a measured request from a dirty worktree")
    profile, profile_hash = load_profile_uri(root, budget_profile_uri)
    envelope, envelope_hash = load_envelope_uri(root, execution_envelope_uri)
    base_set = load_referenced_measured_artifact(root, base_candidate_set_uri)
    policy = load_referenced_measured_artifact(root, adaptive_policy_uri)
    proposer = load_referenced_measured_artifact(root, proposer_contract_uri)
    request = {
        "schema_version": "myis.p2-measured-request.v1",
        "request_id": request_id,
        "phase_id": "P2_SCOPE_DEVELOPMENT",
        "arm": "R1",
        "stage": "train_selection",
        "campaign_id": "scope-autoindex-v1",
        "campaign_revision": profile["campaign_revision"],
        "budget_profile_id": profile["profile_id"],
        "budget_profile_uri": budget_profile_uri,
        "budget_profile_sha256": profile_hash,
        "execution_envelope_id": envelope["envelope_id"],
        "execution_envelope_uri": execution_envelope_uri,
        "execution_envelope_sha256": envelope_hash,
        "base_candidate_set_id": base_set["candidate_set_id"],
        "base_candidate_set_uri": base_candidate_set_uri,
        "base_candidate_set_sha256": base_set["candidate_set_sha256"],
        "adaptive_policy_id": policy["policy_id"],
        "adaptive_policy_uri": adaptive_policy_uri,
        "adaptive_policy_sha256": policy["policy_sha256"],
        "proposer_contract_id": proposer["contract_id"],
        "proposer_contract_uri": proposer_contract_uri,
        "proposer_contract_sha256": proposer["contract_sha256"],
        "proposer_identity": dict(proposer_identity),
        "execution_source_commit": identity["commit"],
        "execution_source_tree": identity["tree"],
        "worktree_clean": True,
        "input_hashes": dict(sorted(input_hashes.items())),
        "scope_hashes": dict(sorted(scope_hashes.items())),
        "global_counters": dict(global_counters),
        "protected_boundary": {
            "output_mode": "aggregate_hash_count_only",
            "train_selection_only": True,
            "final_split_open": False,
            "d2_open_final": False,
            "d3_submit_release": False,
            "gpu": False,
            "paid_api": False,
            "network_model_download": False,
            "provider_fallback": False,
        },
    }
    validated = validate_measured_request_payload(
        request,
        root,
        require_current_git=True,
    )
    return {key: value for key, value in validated.items() if key != "_resolved"}


def load_profile_uri(repository_root: Path, uri: str) -> tuple[dict[str, Any], str]:
    path = resolve_safe_uri(repository_root, uri)
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise P2ContractError(f"cannot load measured budget profile: {uri}") from error
    if not isinstance(payload, dict):
        raise P2ContractError("measured budget profile must be a mapping")
    schema = _json_file(Path(repository_root) / "schemas" / "p2-budget-profile.v1.json")
    try:
        Draft202012Validator(schema).validate(payload)
    except ValidationError as error:
        raise P2ContractError(f"measured budget profile failed schema validation: {error.message}") from error
    _validate_profile_resources(payload)
    _validate_profile_allocation(payload)
    return dict(payload), canonical_sha256(payload)


def load_envelope_uri(repository_root: Path, uri: str) -> tuple[dict[str, Any], str]:
    path = resolve_safe_uri(repository_root, uri)
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise P2ContractError(f"cannot load measured execution envelope: {uri}") from error
    if not isinstance(payload, dict):
        raise P2ContractError("measured execution envelope must be a mapping")
    return dict(payload), file_sha256(path)


def can_admit_adaptive_batch(
    profile: Mapping[str, Any],
    *,
    consumed_measurement_seconds: float,
    candidate_count: int,
) -> bool:
    """Admit only a complete four-candidate batch inside time and count budgets."""

    _validate_profile_resources(profile)
    _validate_profile_allocation(profile)
    if consumed_measurement_seconds < 0 or candidate_count < 0:
        raise P2ContractError("batch admission counters cannot be negative")
    limits = profile["limits"]
    runtime = profile["runtime"]
    batch_size = int(limits["candidates_per_iteration"])
    if candidate_count + batch_size > int(limits["max_candidates_total"]):
        return False
    measurement_budget = float(
        runtime.get("measurement_budget_seconds", runtime["max_wall_clock_seconds"])
    )
    required = batch_size * float(runtime["per_candidate_timeout_seconds"])
    return measurement_budget - float(consumed_measurement_seconds) >= required


def validate_stop_reason(profile: Mapping[str, Any], reason: str) -> str:
    configured = set(profile.get("stopping", {}).get("valid_reasons", VALID_STOP_REASONS))
    if reason not in VALID_STOP_REASONS or reason not in configured:
        raise P2ContractError(f"invalid measured P2 stopping reason: {reason}")
    return reason


def load_referenced_measured_artifact(repository_root: Path, uri: str) -> dict[str, Any]:
    path = resolve_safe_uri(repository_root, uri)
    return validate_measured_artifact(_json_file(path), repository_root)


def scientific_payload(scope_spec: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: deepcopy(value)
        for key, value in scope_spec.items()
        if key not in IDENTITY_ONLY_SPEC_FIELDS
    }


def scientific_payload_sha256(scope_spec: Mapping[str, Any]) -> str:
    return canonical_sha256(scientific_payload(scope_spec))


def assert_single_axis_pair(
    candidate: Mapping[str, Any],
    ablation: Mapping[str, Any],
    declared_axis: str,
) -> None:
    candidate_axes = dict(candidate.get("axis_values", {}))
    ablation_axes = dict(ablation.get("axis_values", {}))
    if set(candidate_axes) != set(ablation_axes):
        raise P2ContractError("matched ablation axis sets differ")
    changed = [key for key in candidate_axes if candidate_axes[key] != ablation_axes[key]]
    if changed != [declared_axis]:
        raise P2ContractError("matched ablation must differ on exactly the declared scientific axis")
    if scientific_payload_sha256(candidate["scope_spec"]) == scientific_payload_sha256(ablation["scope_spec"]):
        raise P2ContractError("matched ablation scientific payload did not change")


def git_identity(repository_root: Path) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    commit = _git(root, "rev-parse", "HEAD")
    tree = _git(root, "rev-parse", "HEAD^{tree}")
    status = _git(root, "status", "--porcelain", allow_empty=True)
    if not COMMIT_RE.fullmatch(commit) or not COMMIT_RE.fullmatch(tree):
        raise P2ContractError("cannot resolve full Git execution identity")
    return {"commit": commit, "tree": tree, "worktree_clean": not status}


def committed_blob_sha256(repository_root: Path, uri: str, revision: str = "HEAD") -> str:
    relative = resolve_safe_uri(repository_root, uri).relative_to(Path(repository_root).resolve()).as_posix()
    try:
        completed = subprocess.run(
            ["git", "show", f"{revision}:{relative}"],
            cwd=repository_root,
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise P2ContractError(f"cannot read committed bytes for {relative}") from error
    return hashlib.sha256(completed.stdout).hexdigest()


def resolve_safe_uri(repository_root: Path, uri: str) -> Path:
    value = str(uri)
    pure_posix = PurePosixPath(value)
    pure_windows = PureWindowsPath(value)
    if (
        not value
        or pure_posix.is_absolute()
        or pure_windows.is_absolute()
        or pure_windows.drive
        or ".." in pure_posix.parts
        or "\\" in value
    ):
        raise P2ContractError(f"unsafe repository-relative URI: {value!r}")
    root = Path(repository_root).resolve()
    path = (root / Path(*pure_posix.parts)).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise P2ContractError(f"repository-relative URI escaped the repository: {value!r}") from error
    if path.is_symlink() or not path.is_file():
        raise P2ContractError(f"referenced measured artifact must be a regular file: {value}")
    return path


def _validate_base_candidate_set_semantics(payload: Mapping[str, Any]) -> None:
    controls = list(payload["frozen_controls"])
    candidates = list(payload["preregistered_candidates"])
    if tuple(item["candidate_id"] for item in controls) != BASE_CONTROL_IDS:
        raise P2ContractError("base candidate set frozen control IDs/order are not canonical")
    if tuple(item["candidate_id"] for item in candidates) != BASE_CANDIDATE_IDS:
        raise P2ContractError("base candidate set preregistered IDs/order are not canonical")
    if [item["arm"] for item in controls] != ["R0", "R0-W", "R1", "R1"]:
        raise P2ContractError("base candidate set frozen control arms are invalid")
    if any(item["arm"] != "R1" for item in candidates):
        raise P2ContractError("all preregistered candidates must use R1")
    rows = [*controls, *candidates]
    identifiers = [str(item["candidate_id"]) for item in rows]
    if len(identifiers) != len(set(identifiers)):
        raise P2ContractError("base candidate IDs must be unique")
    fixture_records = (
        {"family_id": "family-b", "publication_id": "family-b", "title_en": "B title", "abstract_en": "B abstract evidence", "claims_text": "1. first claim\n2. second claim\n3. third claim\n4. fourth claim\n5. fifth claim"},
        {"family_id": "family-a", "publication_id": "family-a", "title_en": "A title", "abstract_en": "A abstract evidence", "claims_text": "1. alpha claim\n2. beta claim\n3. gamma claim\n4. delta claim\n5. epsilon claim"},
    )
    for item in rows:
        spec = item["scope_spec"]
        parse_scope_spec(spec)
        if item["spec_sha256"] != canonical_sha256(spec):
            raise P2ContractError(f"candidate {item['candidate_id']} spec hash mismatch")
        if item["scientific_payload_sha256"] != scientific_payload_sha256(spec):
            raise P2ContractError(f"candidate {item['candidate_id']} scientific payload hash mismatch")
        first = compile_scope(spec, fixture_records)
        second = compile_scope(spec, reversed(fixture_records))
        if first.as_dict() != second.as_dict():
            raise P2ContractError(f"candidate {item['candidate_id']} compiler output is order-dependent")
        per_family: dict[str, int] = {}
        for unit in first.units:
            per_family[unit.family_id] = per_family.get(unit.family_id, 0) + int(unit.searchable)
        if any(count > 4 for count in per_family.values()):
            raise P2ContractError(f"candidate {item['candidate_id']} exceeds the four-unit limit")


def _validate_policy_semantics(payload: Mapping[str, Any]) -> None:
    if tuple(payload["batch_roles"]) != BATCH_ROLES:
        raise P2ContractError("adaptive policy batch roles/order are not canonical")
    if set(payload["allowed_axes"]) & set(payload["forbidden_axes"]):
        raise P2ContractError("adaptive policy allowed and forbidden axes overlap")
    if payload["candidates_per_iteration"] != 4:
        raise P2ContractError("adaptive policy requires four candidates per iteration")


def _validate_batch_semantics(payload: Mapping[str, Any]) -> None:
    candidates = list(payload["candidates"])
    if tuple(item["role"] for item in candidates) != BATCH_ROLES:
        raise P2ContractError("adaptive batch roles/order are invalid")
    iteration = int(payload["iteration"])
    expected_prefix = f"p2-r1-r{_revision_number(payload['campaign_revision']):02d}-i{iteration:02d}-c"
    expected_ids = tuple(f"{expected_prefix}{index:02d}" for index in range(1, 5))
    if tuple(item["candidate_id"] for item in candidates) != expected_ids:
        raise P2ContractError("adaptive candidate IDs are not stable consecutive batch IDs")
    for item in candidates:
        parse_scope_spec(item["scope_spec"])
        if item["spec_sha256"] != canonical_sha256(item["scope_spec"]):
            raise P2ContractError("adaptive candidate spec hash mismatch")
        if item["scientific_payload_sha256"] != scientific_payload_sha256(item["scope_spec"]):
            raise P2ContractError("adaptive candidate scientific payload hash mismatch")
    exploit = candidates[0]
    ablation = candidates[1]
    if exploit["matched_ablation_id"] != ablation["candidate_id"]:
        raise P2ContractError("exploit candidate must bind the batch matched ablation")
    if ablation["matched_ablation_id"] != exploit["candidate_id"]:
        raise P2ContractError("matched ablation must bind the exploit candidate")
    assert_single_axis_pair(exploit, ablation, str(exploit["declared_axis"]))


def _validate_profile_resources(profile: Mapping[str, Any]) -> None:
    resources = profile.get("resources", {})
    if resources.get("paid_api_budget_usd") != 0 or resources.get("gpu_budget_usd") != 0:
        raise P2ContractError("P2 measured profile must remain zero-cost CPU-only")
    if resources.get("network_model_download") is not False or resources.get("provider_fallback") is not False:
        raise P2ContractError("P2 measured profile forbids downloads and provider fallback")


def _validate_profile_allocation(profile: Mapping[str, Any]) -> None:
    allocation = profile.get("candidate_allocation", {})
    limits = profile.get("limits", {})
    if allocation.get("frozen_controls") != 4 or allocation.get("preregistered_patent_candidates") != 8:
        raise P2ContractError("every measured revision requires four controls and eight preregistered candidates")
    adaptive = int(allocation.get("adaptive_candidates", -1))
    if adaptive < 0 or adaptive % 4:
        raise P2ContractError("adaptive allocation must be a nonnegative multiple of four")
    if limits.get("candidates_per_iteration") != 4:
        raise P2ContractError("measured profile candidates_per_iteration must equal four")
    if limits.get("max_candidates_total") != 12 + adaptive:
        raise P2ContractError("measured profile candidate total does not match its allocation")
    if limits.get("max_adaptive_candidates") != adaptive:
        raise P2ContractError("measured profile adaptive limit does not match its allocation")
    if limits.get("max_adaptive_iterations") != adaptive // 4:
        raise P2ContractError("measured profile iteration limit does not match its allocation")
    if limits.get("max_index_builds") < limits.get("max_candidates_total"):
        raise P2ContractError("measured profile index-build limit is too small")
    if limits.get("selection_exposure_limit") != 1:
        raise P2ContractError("measured profile selection exposure limit must equal one")
    runtime = profile.get("runtime", {})
    wall = int(runtime.get("max_wall_clock_seconds", -1))
    timeout = int(runtime.get("per_candidate_timeout_seconds", -1))
    measurement = int(runtime.get("measurement_budget_seconds", wall))
    reserve = int(runtime.get("overhead_reserve_seconds", wall - measurement))
    if wall <= 0 or timeout <= 0 or measurement <= 0 or reserve < 0:
        raise P2ContractError("measured profile runtime limits must be explicit positive values")
    if "measurement_budget_seconds" in runtime:
        if measurement + reserve != wall:
            raise P2ContractError("measurement budget plus overhead reserve must equal wall clock")
        if measurement < int(limits["max_candidates_total"]) * timeout:
            raise P2ContractError("measurement budget cannot cover every admitted candidate timeout")
    stopping = profile.get("stopping", {})
    if profile.get("profile_id") == "p2-r1-primary-v2":
        if runtime.get("prevent_system_sleep") is not True:
            raise P2ContractError("v2 measured profile must prevent system sleep")
        if stopping.get("whole_batch_admission") is not True:
            raise P2ContractError("v2 measured profile requires whole-batch admission")


def _validate_envelope(envelope: Mapping[str, Any], profile: Mapping[str, Any], profile_uri: str) -> None:
    scope = envelope.get("scope", {})
    resources = envelope.get("resources", {})
    if scope.get("phase_id") != "P2_SCOPE_DEVELOPMENT" or scope.get("arm") != "R1":
        raise P2ContractError("measured envelope phase/arm mismatch")
    if scope.get("campaign_revision") != profile.get("campaign_revision"):
        raise P2ContractError("measured envelope campaign revision mismatch")
    if scope.get("budget_profile_ref") != profile_uri:
        raise P2ContractError("measured envelope budget profile reference mismatch")
    if scope.get("train_selection_only") is not True or scope.get("final_split_open") is not False:
        raise P2ContractError("measured envelope must remain train/selection only")
    if scope.get("selection_access_requires_shortlist_freeze") is not True:
        raise P2ContractError("measured envelope must require shortlist freeze")
    if any(resources.get(key) is not False for key in ("gpu", "paid_api", "network_model_download", "provider_fallback")):
        raise P2ContractError("measured envelope resource boundary mismatch")


def _revision_number(campaign_revision: str) -> int:
    match = re.search(r"-v(\d+)$", str(campaign_revision))
    return int(match.group(1)) if match else 1


def _json_file(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise P2ContractError(f"cannot load JSON artifact: {path}") from error
    if not isinstance(value, dict):
        raise P2ContractError(f"JSON artifact must be an object: {path}")
    return value


def _yaml_file(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise P2ContractError(f"cannot load YAML artifact: {path}") from error
    if not isinstance(value, dict):
        raise P2ContractError(f"YAML artifact must be a mapping: {path}")
    return value


def _git(root: Path, *args: str, allow_empty: bool = False) -> str:
    try:
        completed = subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as error:
        raise P2ContractError(f"Git command failed: {' '.join(args)}") from error
    value = completed.stdout.strip()
    if not value and not allow_empty:
        raise P2ContractError(f"Git command returned no value: {' '.join(args)}")
    return value
