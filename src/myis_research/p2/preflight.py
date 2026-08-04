"""Read-only P2 Owner-local preflight and safe receipt construction."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import subprocess
import uuid
from typing import Any, Mapping

import yaml

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_path_not_protected
from .contracts import (
    ENVELOPE_RELATIVE_PATH,
    P2_ARTIFACT_SCHEMAS,
    P2ContractError,
    P2_PREFLIGHT_CHECK_IDS,
    P2_PREFLIGHT_V2_CHECK_IDS,
    load_p2_request,
    validate_p2_artifact,
    validate_p2_preflight_receipt,
    write_immutable_json,
)
from .measured_contracts import git_identity, load_measured_request


P2_PREFLIGHT_RECEIPT_PATH = Path(
    "campaigns/scope-autoindex-v1/preflight/p2-preflight-receipt.json"
)
DEFAULT_REQUIRED_FREE_SPACE_BYTES = 1
STORE_ENVIRONMENT = ("MYIS_STORE", "MYIS_MLFLOW_STORE")
P2_COUNTER_ARTIFACT_DIRS = ("requests", "manifests", "evidence", "packages", "reports")
P2_LIFECYCLE_SCHEMAS = frozenset(P2_ARTIFACT_SCHEMAS) - {
    "myis.p2-request.v1",
    "myis.p2-measured-request.v1",
    "myis.p2-preflight-receipt.v1",
    "myis.p2-preflight-receipt.v2",
    "myis.p2-candidate-freeze-proposal.v1",
}
OWNER_APPROVAL_REQUIRED = [
    "Owner confirms both protected store identities and permits read-only metadata preflight.",
    "Owner approves the four frozen controls and eight preregistered candidate definitions.",
    "Owner resolves any ambiguous SCOPE view, field, normalization, or aggregation definition before adoption.",
    "Owner approves the concrete compiler, config, retriever, and evaluator SHA-256 bindings before a measured request.",
    "Owner explicitly requests measured P2; this preflight does not create a request, baseline commitment, or selection exposure.",
]


def run_p2_preflight(
    request_path: Path,
    repository_root: Path,
    *,
    output: Path | None = None,
    require_stores: bool = True,
    required_free_space_bytes: int | None = None,
    allow_historical_request: bool = False,
) -> dict[str, Any]:
    """Run the repository-boundary checks without opening protected payloads."""

    root = Path(repository_root).resolve(strict=True)
    raw_request = _json_file(Path(request_path))
    schema_version = str(raw_request.get("schema_version", ""))
    if schema_version == "myis.p2-measured-request.v1":
        return _run_measured_p2_preflight(
            request_path=Path(request_path),
            repository_root=root,
            output=output,
            require_stores=require_stores,
            required_free_space_bytes=required_free_space_bytes,
        )
    if not allow_historical_request:
        raise P2ContractError(
            "active P2 preflight requires myis.p2-measured-request.v1; historical v1 fallback is forbidden"
        )
    request, profile = load_p2_request(Path(request_path), root, require_store=False)
    envelope_path = root / ENVELOPE_RELATIVE_PATH
    campaign_path = root / "control/campaigns/scope-autoindex-v1.yaml"
    envelope_sha256 = file_sha256(envelope_path) if envelope_path.is_file() else "0" * 64
    campaign_sha256 = file_sha256(campaign_path) if campaign_path.is_file() else "0" * 64
    required_space = _required_free_space(required_free_space_bytes)
    checks: list[dict[str, str]] = []

    source_exists = _git_commit_exists(root, str(request["git_commit"]))
    checks.append(_check("execution_source_commit", source_exists, "commit_exists" if source_exists else "commit_missing"))

    profile_ok = (
        request["budget_profile_id"] == profile.profile_id
        and request["budget_profile_sha256"] == profile.sha256
        and request["campaign_revision"] == profile.payload["campaign_revision"]
    )
    checks.append(_check("canonical_profile_binding", profile_ok, "profile_matches" if profile_ok else "profile_mismatch"))

    envelope_ok = envelope_path.is_file() and request["execution_envelope_sha256"] == envelope_sha256
    checks.append(_check("canonical_envelope_binding", envelope_ok, "envelope_matches" if envelope_ok else "envelope_mismatch"))

    campaign_ok = _campaign_binding_ok(root, profile.payload, campaign_path)
    checks.append(_check("canonical_campaign_binding", campaign_ok, "campaign_matches" if campaign_ok else "campaign_mismatch"))

    gate_snapshot, gate_ok = _gate_snapshot(root, profile.payload)
    checks.append(_check("gate_state", gate_ok, "owner_gates_closed" if gate_ok else "gate_state_not_safe"))
    counter_snapshot, counter_ok = _counter_snapshot(root, profile.payload)
    checks.append(_check("counter_state", counter_ok, "real_counters_zero" if counter_ok else "real_counters_nonzero"))

    worktrees = _git_worktree_roots(root)
    stores, overlap_ok, aggregate_free = _store_snapshot(
        root,
        worktrees,
        check_stores=require_stores,
    )
    for name in STORE_ENVIRONMENT:
        checks.append(_check(
            f"store_{name.casefold()}",
            stores[name]["status"] == "passed",
            stores[name]["status"],
        ))
    checks.append(_check("store_path_overlap", overlap_ok, "paths_disjoint" if overlap_ok else "paths_overlap"))
    free_ok = aggregate_free >= required_space
    checks.append(_check("aggregate_free_space", free_ok, "sufficient" if free_ok else "insufficient"))
    if [item["check_id"] for item in checks] != list(P2_PREFLIGHT_CHECK_IDS):
        raise P2ContractError("P2 preflight implementation emitted an unexpected check set")

    all_passed = (
        all(item["status"] == "passed" for item in checks)
        and source_exists
        and gate_ok
        and counter_ok
        and overlap_ok
        and free_ok
    )
    status = "passed_pending_owner" if all_passed else "failed"
    receipt = build_preflight_receipt(
        request=request,
        profile=profile.payload,
        request_sha256=canonical_sha256(request),
        campaign_sha256=campaign_sha256,
        envelope_sha256=envelope_sha256,
        status=status,
        checks=checks,
        stores=stores,
        worktree_count=len(worktrees),
        outside_all_worktrees=all(
            bool(item.get("outside_all_worktrees")) for item in stores.values()
        ),
        overlap_checked=True,
        counters=counter_snapshot,
        gates=gate_snapshot,
        required_free_space_bytes=required_space,
        aggregate_free_space_bytes=aggregate_free,
        failure_codes=[item["check_id"] for item in checks if item["status"] == "failed"],
        repository_root=root,
    )
    if output is not None:
        write_preflight_receipt(root, output, receipt)
    return receipt


def _run_measured_p2_preflight(
    *,
    request_path: Path,
    repository_root: Path,
    output: Path | None,
    require_stores: bool,
    required_free_space_bytes: int | None,
) -> dict[str, Any]:
    """Run the active v2 checks against one measured-request contract."""

    root = Path(repository_root).resolve(strict=True)
    measured = load_measured_request(
        request_path,
        root,
        require_current_git=False,
    )
    resolved = measured["_resolved"]
    request = {key: value for key, value in measured.items() if key != "_resolved"}
    profile = resolved["profile"]
    envelope = resolved["envelope"]
    campaign = resolved["campaign_revision"]
    active = resolved["active_sources"]
    compatibility = resolved["evaluator_compatibility"]
    required_space = _required_free_space(required_free_space_bytes)
    checks: list[dict[str, str]] = []

    identity = git_identity(root)
    commit_exists = _git_commit_exists(root, request["execution_source_commit"])
    commit_matches = commit_exists and identity["commit"] == request["execution_source_commit"]
    checks.append(_check(
        "execution_source_commit",
        commit_matches,
        "commit_matches" if commit_matches else "commit_missing_or_not_checked_out",
    ))
    committed_tree = _tree_for_commit(root, request["execution_source_commit"])
    tree_matches = (
        committed_tree == request["execution_source_tree"]
        and identity["tree"] == request["execution_source_tree"]
    )
    checks.append(_check(
        "execution_source_tree",
        tree_matches,
        "tree_matches" if tree_matches else "tree_mismatch",
    ))
    worktree_clean = identity["worktree_clean"] and request["worktree_clean"] is True
    checks.append(_check(
        "worktree_clean",
        worktree_clean,
        "worktree_clean" if worktree_clean else "worktree_dirty",
    ))

    profile_ok = (
        request["budget_profile_uri"] == active["profile"]
        and request["budget_profile_id"] == profile["profile_id"]
        and request["budget_profile_sha256"] == canonical_sha256(profile)
        and request["campaign_revision"] == profile["campaign_revision"]
    )
    checks.append(_check(
        "canonical_profile_binding",
        profile_ok,
        "profile_matches" if profile_ok else "profile_mismatch",
    ))
    envelope_sha256 = canonical_sha256(envelope)
    envelope_ok = (
        request["execution_envelope_uri"] == active["execution_envelope"]
        and request["execution_envelope_id"] == envelope["envelope_id"]
        and request["execution_envelope_sha256"] == envelope_sha256
        and envelope.get("scope", {}).get("campaign_revision")
        == profile["campaign_revision"]
    )
    checks.append(_check(
        "canonical_envelope_binding",
        envelope_ok,
        "envelope_matches" if envelope_ok else "envelope_mismatch",
    ))
    campaign_path = root / active["campaign_revision"]
    campaign_sha256 = file_sha256(campaign_path)
    campaign_ok = (
        campaign.get("campaign_id") == request["campaign_id"]
        and campaign.get("campaign_revision") == request["campaign_revision"]
        and campaign.get("budget_profile_ref") == active["profile"]
        and campaign.get("execution_envelope_ref") == active["execution_envelope"]
        and campaign.get("status") == "ready_planned_not_measured"
    )
    checks.append(_check(
        "canonical_campaign_binding",
        campaign_ok,
        "campaign_matches" if campaign_ok else "campaign_mismatch",
    ))
    from .measured_adapter import current_scope_hashes

    expected_scope_hashes = current_scope_hashes(
        root,
        revision=(request["execution_source_commit"] if commit_exists else "HEAD"),
    )
    scope_ok = all(
        request["scope_hashes"].get(key) == value
        for key, value in expected_scope_hashes.items()
    )
    checks.append(_check(
        "canonical_scope_hashes",
        scope_ok,
        "scope_hashes_match" if scope_ok else "scope_hash_mismatch",
    ))
    compatibility_ok = (
        request["scope_hashes"].get("evaluator_compatibility_sha256")
        == compatibility["compatibility_sha256"]
        and request["scope_hashes"].get("evaluator_sha256")
        == compatibility["current"]["evaluator_sha256"]
        and compatibility["current"]["evaluator_sha256"]
        != compatibility["baseline"]["evaluator_sha256"]
    )
    checks.append(_check(
        "evaluator_compatibility",
        compatibility_ok,
        "compatibility_proved" if compatibility_ok else "compatibility_invalid",
    ))

    gate_snapshot, gate_ok = _gate_snapshot(root, profile)
    checks.append(_check(
        "gate_state",
        gate_ok,
        "owner_gates_closed" if gate_ok else "gate_state_not_safe",
    ))
    counter_snapshot, counter_ok = _counter_snapshot(root, profile)
    checks.append(_check(
        "counter_state",
        counter_ok,
        "real_counters_zero" if counter_ok else "real_counters_nonzero",
    ))

    pre_store_ok = all(item["status"] == "passed" for item in checks)
    worktrees = _git_worktree_roots(root)
    stores, overlap_ok, aggregate_free = _store_snapshot(
        root,
        worktrees,
        check_stores=require_stores and pre_store_ok,
    )
    outside_all_worktrees = all(
        bool(item.get("outside_all_worktrees")) for item in stores.values()
    )
    for name in STORE_ENVIRONMENT:
        checks.append(_check(
            f"store_{name.casefold()}",
            stores[name]["status"] == "passed",
            stores[name]["status"],
        ))
    paths_safe = overlap_ok and outside_all_worktrees
    checks.append(_check(
        "store_path_overlap",
        paths_safe,
        "paths_disjoint_outside_worktrees" if paths_safe else "paths_overlap_or_enter_worktree",
    ))
    free_ok = aggregate_free >= required_space
    checks.append(_check(
        "aggregate_free_space",
        free_ok,
        "sufficient" if free_ok else "insufficient",
    ))
    if [item["check_id"] for item in checks] != list(P2_PREFLIGHT_V2_CHECK_IDS):
        raise P2ContractError("P2 measured preflight emitted an unexpected check set")
    status = (
        "passed_pending_owner"
        if all(item["status"] == "passed" for item in checks)
        else "failed"
    )
    receipt = build_preflight_receipt_v2(
        request=request,
        profile=profile,
        envelope=envelope,
        active_sources=active,
        request_sha256=canonical_sha256(request),
        campaign_sha256=campaign_sha256,
        envelope_sha256=envelope_sha256,
        compatibility_sha256=compatibility["compatibility_sha256"],
        commit_exists=commit_exists,
        tree_matches=committed_tree == request["execution_source_tree"],
        status=status,
        checks=checks,
        stores=stores,
        worktree_count=len(worktrees),
        outside_all_worktrees=outside_all_worktrees,
        stores_disjoint=overlap_ok,
        overlap_checked=True,
        counters=counter_snapshot,
        gates=gate_snapshot,
        required_free_space_bytes=required_space,
        aggregate_free_space_bytes=aggregate_free,
        failure_codes=[item["check_id"] for item in checks if item["status"] == "failed"],
        repository_root=root,
    )
    if output is not None:
        write_preflight_receipt(root, output, receipt)
    return receipt


def preflight_what_if(
    request_path: Path,
    repository_root: Path,
    *,
    allow_historical_request: bool = False,
) -> dict[str, Any]:
    """Describe a preflight without touching either Owner-local store."""

    root = Path(repository_root).resolve(strict=True)
    raw_request = _json_file(Path(request_path))
    if raw_request.get("schema_version") != "myis.p2-measured-request.v1":
        if allow_historical_request:
            return _historical_preflight_what_if(request_path, root)
        raise P2ContractError(
            "active P2 preflight requires myis.p2-measured-request.v1; historical v1 fallback is forbidden"
        )
    measured = load_measured_request(
        Path(request_path), root, require_current_git=False
    )
    resolved = measured["_resolved"]
    profile_payload = resolved["profile"]
    return {
        "schema_version": "myis.p2-preflight-what-if.v1",
        "status": "not_started",
        "preflight_status": "not_started",
        "request_id": measured["request_id"],
        "phase_id": measured["phase_id"],
        "arm": measured["arm"],
        "budget_profile_id": profile_payload["profile_id"],
        "budget_profile_sha256": measured["budget_profile_sha256"],
        "stores_checked": False,
        "protected_data_accessed": False,
        "measured_execution": False,
        "counters": {
            "measured_runs": 0,
            "candidate_count": 0,
            "shortlist_count": 0,
            "selection_accesses": 0,
        },
        "next_authorized_action": "Owner-local P2 measured preflight",
    }


def _historical_preflight_what_if(request_path: Path, repository_root: Path) -> dict[str, Any]:
    """Retain the v1 preview implementation for explicit historical callers."""

    root = Path(repository_root).resolve(strict=True)
    request, profile = load_p2_request(Path(request_path), root, require_store=False)
    return {
        "schema_version": "myis.p2-preflight-what-if.v1",
        "status": "not_started",
        "preflight_status": "not_started",
        "request_id": request["request_id"],
        "phase_id": request["phase_id"],
        "arm": request["arm"],
        "budget_profile_id": profile.profile_id,
        "budget_profile_sha256": profile.sha256,
        "stores_checked": False,
        "protected_data_accessed": False,
        "measured_execution": False,
        "counters": {
            "measured_runs": 0,
            "candidate_count": 0,
            "shortlist_count": 0,
            "selection_accesses": 0,
        },
        "next_authorized_action": "Owner-local P2 measured preflight",
    }


def build_preflight_receipt(
    *,
    request: Mapping[str, Any],
    profile: Mapping[str, Any],
    request_sha256: str,
    campaign_sha256: str,
    envelope_sha256: str,
    status: str,
    checks: list[Mapping[str, Any]],
    stores: Mapping[str, Mapping[str, Any]],
    worktree_count: int,
    outside_all_worktrees: bool,
    overlap_checked: bool,
    counters: Mapping[str, Any],
    gates: Mapping[str, Any],
    required_free_space_bytes: int,
    aggregate_free_space_bytes: int,
    failure_codes: list[str],
    repository_root: Path | None = None,
) -> dict[str, Any]:
    """Build and validate an immutable receipt payload."""

    if status not in {"not_started", "passed_pending_owner", "failed"}:
        raise P2ContractError("unsupported P2 preflight status")
    body: dict[str, Any] = {
        "schema_version": "myis.p2-preflight-receipt.v1",
        "receipt_id": f"p2-preflight-{request['request_id']}",
        "request_id": str(request["request_id"]),
        "phase_id": "P2_SCOPE_DEVELOPMENT",
        "arm": "R1",
        "campaign_id": "scope-autoindex-v1",
        "campaign_revision": str(profile["campaign_revision"]),
        "budget_profile_id": str(profile["profile_id"]),
        "budget_profile_sha256": canonical_sha256(dict(profile)),
        "execution_envelope_sha256": envelope_sha256,
        "campaign_sha256": campaign_sha256,
        "request_sha256": request_sha256,
        "git_commit": str(request["git_commit"]),
        "git_commit_exists": any(
            item.get("check_id") == "execution_source_commit" and item.get("status") == "passed"
            for item in checks
        ),
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": status,
        "checks": [
            {"check_id": str(item["check_id"]), "status": str(item["status"]), "detail": str(item["detail"])}
            for item in checks
        ],
        "stores": {name: dict(stores.get(name, _not_run_store())) for name in STORE_ENVIRONMENT},
        "safe_path_boundary": {
            "all_worktrees_count": max(1, int(worktree_count)),
            "outside_all_worktrees": bool(outside_all_worktrees),
            "path_overlap_checked": bool(overlap_checked),
            "unsafe_links_rejected": True,
        },
        "counters": {
            "measured_runs": int(counters.get("measured_runs", 0)),
            "candidate_count": int(counters.get("candidate_count", 0)),
            "shortlist_count": int(counters.get("shortlist_count", 0)),
            "selection_accesses": int(counters.get("selection_accesses", 0)),
            "baseline_commitment_present": bool(counters.get("baseline_commitment_present", False)),
            "freeze_started": bool(counters.get("freeze_started", False)),
        },
        "gates": {
            "D1_START_CAMPAIGN": str(gates.get("D1_START_CAMPAIGN", "unknown")),
            "D2_OPEN_FINAL": str(gates.get("D2_OPEN_FINAL", "unknown")),
            "D3_SUBMIT_RELEASE": str(gates.get("D3_SUBMIT_RELEASE", "unknown")),
            "final_split_open": bool(gates.get("final_split_open", False)),
        },
        "required_free_space_bytes": max(0, int(required_free_space_bytes)),
        "aggregate_free_space_bytes": max(0, int(aggregate_free_space_bytes)),
        "measured_execution": False,
        "protected_data_accessed": False,
        "final_split_open": False,
        "absolute_owner_local_paths_emitted": False,
        "failure_codes": sorted(str(item) for item in failure_codes),
        "owner_approval_required": list(OWNER_APPROVAL_REQUIRED),
    }
    body["receipt_sha256"] = canonical_sha256(body)
    return validate_p2_preflight_receipt(
        body,
        repository_root=Path(repository_root).resolve() if repository_root is not None else _repository_root_from_profile(profile),
    )


def build_preflight_receipt_v2(
    *,
    request: Mapping[str, Any],
    profile: Mapping[str, Any],
    envelope: Mapping[str, Any],
    active_sources: Mapping[str, str],
    request_sha256: str,
    campaign_sha256: str,
    envelope_sha256: str,
    compatibility_sha256: str,
    commit_exists: bool,
    tree_matches: bool,
    status: str,
    checks: list[Mapping[str, Any]],
    stores: Mapping[str, Mapping[str, Any]],
    worktree_count: int,
    outside_all_worktrees: bool,
    stores_disjoint: bool,
    overlap_checked: bool,
    counters: Mapping[str, Any],
    gates: Mapping[str, Any],
    required_free_space_bytes: int,
    aggregate_free_space_bytes: int,
    failure_codes: list[str],
    repository_root: Path,
) -> dict[str, Any]:
    """Build the active measured-request preflight receipt."""

    if status not in {"not_started", "passed_pending_owner", "failed"}:
        raise P2ContractError("unsupported P2 preflight v2 status")
    check_map = {str(item["check_id"]): str(item["status"]) for item in checks}
    body: dict[str, Any] = {
        "schema_version": "myis.p2-preflight-receipt.v2",
        "receipt_id": f"p2-preflight-{request['request_id']}",
        "request_id": str(request["request_id"]),
        "request_schema_version": str(request["schema_version"]),
        "request_sha256": request_sha256,
        "phase_id": "P2_SCOPE_DEVELOPMENT",
        "arm": "R1",
        "campaign_id": str(request["campaign_id"]),
        "campaign_revision": str(profile["campaign_revision"]),
        "campaign_revision_uri": str(active_sources["campaign_revision"]),
        "campaign_sha256": campaign_sha256,
        "budget_profile_id": str(profile["profile_id"]),
        "budget_profile_uri": str(active_sources["profile"]),
        "budget_profile_sha256": canonical_sha256(dict(profile)),
        "execution_envelope_id": str(envelope["envelope_id"]),
        "execution_envelope_uri": str(active_sources["execution_envelope"]),
        "execution_envelope_sha256": envelope_sha256,
        "evaluator_compatibility_uri": str(active_sources["evaluator_compatibility"]),
        "evaluator_compatibility_sha256": compatibility_sha256,
        "scope_hashes": dict(sorted(request["scope_hashes"].items())),
        "git_commit": str(request["execution_source_commit"]),
        "git_tree": str(request["execution_source_tree"]),
        "git_commit_exists": bool(commit_exists),
        "git_tree_matches": bool(tree_matches),
        "worktree_clean": check_map.get("worktree_clean") == "passed",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": status,
        "checks": [
            {
                "check_id": str(item["check_id"]),
                "status": str(item["status"]),
                "detail": str(item["detail"]),
            }
            for item in checks
        ],
        "stores": {
            name: dict(stores.get(name, _not_run_store()))
            for name in STORE_ENVIRONMENT
        },
        "safe_path_boundary": {
            "all_worktrees_count": max(1, int(worktree_count)),
            "outside_all_worktrees": bool(outside_all_worktrees),
            "stores_disjoint": bool(stores_disjoint),
            "path_overlap_checked": bool(overlap_checked),
            "unsafe_links_rejected": True,
        },
        "counters": {
            "measured_runs": int(counters.get("measured_runs", 0)),
            "candidate_count": int(counters.get("candidate_count", 0)),
            "shortlist_count": int(counters.get("shortlist_count", 0)),
            "selection_accesses": int(counters.get("selection_accesses", 0)),
            "baseline_commitment_present": bool(counters.get("baseline_commitment_present", False)),
            "freeze_started": bool(counters.get("freeze_started", False)),
        },
        "gates": {
            "D1_START_CAMPAIGN": str(gates.get("D1_START_CAMPAIGN", "unknown")),
            "D2_OPEN_FINAL": str(gates.get("D2_OPEN_FINAL", "unknown")),
            "D3_SUBMIT_RELEASE": str(gates.get("D3_SUBMIT_RELEASE", "unknown")),
            "final_split_open": bool(gates.get("final_split_open", False)),
        },
        "required_free_space_bytes": max(0, int(required_free_space_bytes)),
        "aggregate_free_space_bytes": max(0, int(aggregate_free_space_bytes)),
        "measured_execution": False,
        "protected_data_accessed": False,
        "final_split_open": False,
        "absolute_owner_local_paths_emitted": False,
        "failure_codes": sorted(str(item) for item in failure_codes),
        "owner_approval_required": list(OWNER_APPROVAL_REQUIRED),
    }
    body["receipt_sha256"] = canonical_sha256(body)
    return validate_p2_preflight_receipt(body, repository_root=repository_root)


def write_preflight_receipt(repository_root: Path, output: Path, receipt: Mapping[str, Any]) -> str:
    """Persist one immutable repository-safe preflight receipt."""

    root = Path(repository_root).resolve(strict=True)
    raw_target = Path(output) if Path(output).is_absolute() else root / Path(output)
    lexical_target = Path(os.path.abspath(raw_target))
    try:
        relative_target = lexical_target.relative_to(root)
    except ValueError as error:
        raise P2ContractError("preflight receipt output must remain in the repository") from error
    try:
        assert_path_not_protected(relative_target.as_posix())
    except PermissionError as error:
        raise P2ContractError(str(error)) from error
    if lexical_target.is_symlink() or any(
        _is_link_or_junction(parent) for parent in _ancestors(lexical_target, root)
    ):
        raise P2ContractError("preflight receipt output cannot traverse a symlink or junction")
    target = lexical_target.resolve(strict=False)
    try:
        target.relative_to(root)
    except ValueError as error:
        raise P2ContractError("preflight receipt output must remain in the repository") from error
    validate_p2_preflight_receipt(receipt, repository_root=root)
    return write_immutable_json(target, receipt)


def _campaign_binding_ok(root: Path, profile: Mapping[str, Any], path: Path) -> bool:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError):
        return False
    if not isinstance(payload, Mapping):
        return False
    campaign = payload.get("campaign") if isinstance(payload.get("campaign"), Mapping) else {}
    execution = payload.get("p2_execution") if isinstance(payload.get("p2_execution"), Mapping) else {}
    protocol = payload.get("protocol") if isinstance(payload.get("protocol"), Mapping) else {}
    return (
        campaign.get("id") == profile.get("campaign_id")
        and campaign.get("p2_campaign_revision") == profile.get("campaign_revision")
        and campaign.get("p2_budget_profile_ref") == "control/budgets/p2-r1-primary-v1.yaml"
        and execution.get("profile_id") == profile.get("profile_id")
        and execution.get("profile_ref") == "control/budgets/p2-r1-primary-v1.yaml"
        and protocol.get("p2_final_split_open") is False
        and campaign.get("active_owner_decisions") == ["D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"]
    )


def _gate_snapshot(root: Path, profile: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
    d1_path = root / "control/decisions/D1_START_CAMPAIGN.yaml"
    try:
        d1 = yaml.safe_load(d1_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError):
        d1 = {}
    if not isinstance(d1, Mapping):
        d1 = {}
    scope = d1.get("scope") if isinstance(d1.get("scope"), Mapping) else {}
    statuses = {"D2_OPEN_FINAL": "waiting_owner", "D3_SUBMIT_RELEASE": "waiting_owner"}
    ledger_path = root / "control/decisions/ledger.jsonl"
    try:
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = _json_object(line)
            decision_id = str(row.get("decision_id", ""))
            if decision_id in statuses and str(row.get("status", "")) == "approved":
                statuses[decision_id] = "approved"
    except (OSError, UnicodeError, ValueError):
        statuses = {key: "unknown" for key in statuses}
    snapshot = {
        "D1_START_CAMPAIGN": str(d1.get("status", "unknown")),
        "D2_OPEN_FINAL": statuses["D2_OPEN_FINAL"],
        "D3_SUBMIT_RELEASE": statuses["D3_SUBMIT_RELEASE"],
        "final_split_open": bool(scope.get("final_split_open", True)),
    }
    safe = (
        snapshot["D1_START_CAMPAIGN"] == "active"
        and snapshot["D2_OPEN_FINAL"] == "waiting_owner"
        and snapshot["D3_SUBMIT_RELEASE"] == "waiting_owner"
        and snapshot["final_split_open"] is False
        and scope.get("execution_mode") == "cpu_local_reversible"
        and scope.get("gpu") is False
        and scope.get("paid_api") is False
    )
    return snapshot, safe


def _counter_snapshot(root: Path, profile: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
    campaign_path = root / "control/campaigns/scope-autoindex-v1.yaml"
    try:
        campaign = yaml.safe_load(campaign_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError):
        campaign = {}
    task_counters: dict[str, Any] = {}
    if isinstance(campaign, Mapping):
        phases = campaign.get("phases") if isinstance(campaign.get("phases"), list) else []
        for phase in phases:
            if not isinstance(phase, Mapping) or phase.get("id") != "P2_SCOPE_DEVELOPMENT":
                continue
            tasks = phase.get("tasks") if isinstance(phase.get("tasks"), list) else []
            for task in tasks:
                if isinstance(task, Mapping) and task.get("id") == "P2.1":
                    task_counters = dict(task)
    measured_runs = int(task_counters.get("measured_runs", 0) or 0)
    selection_accesses = int(task_counters.get("selection_accesses", 0) or 0)
    read_model_path = root / "projections/read-model/read-model.v2.json"
    p2: Mapping[str, Any] = {}
    if read_model_path.is_file() and not read_model_path.is_symlink():
        try:
            read_model = _json_file(read_model_path)
            p2 = read_model.get("p2_readiness", {}) if isinstance(read_model.get("p2_readiness"), Mapping) else {}
        except (OSError, UnicodeError, ValueError):
            p2 = {}
    measured_runs = max(measured_runs, int(p2.get("measured_runs", 0) or 0))
    selection_accesses = max(selection_accesses, int(p2.get("selection_accesses", 0) or 0))
    artifact_counters, artifacts_safe = _artifact_counter_snapshot(root)
    counters = {
        "measured_runs": max(measured_runs, artifact_counters["measured_runs"]),
        "candidate_count": max(int(p2.get("candidate_count", 0) or 0), artifact_counters["candidate_count"]),
        "shortlist_count": max(int(p2.get("shortlist_count", 0) or 0), artifact_counters["shortlist_count"]),
        "selection_accesses": max(selection_accesses, artifact_counters["selection_accesses"]),
        "baseline_commitment_present": (
            bool(p2.get("source", {}).get("baseline_commitment_sha256"))
            if isinstance(p2.get("source"), Mapping)
            else False
        ) or artifact_counters["baseline_commitment_present"],
        "freeze_started": (
            bool((p2.get("freeze_barrier") or {}).get("status") not in {None, "not_started"})
            if isinstance(p2.get("freeze_barrier"), Mapping)
            else False
        ) or artifact_counters["freeze_started"],
    }
    safe = counters == {
        "measured_runs": 0,
        "candidate_count": 0,
        "shortlist_count": 0,
        "selection_accesses": 0,
        "baseline_commitment_present": False,
        "freeze_started": False,
    } and artifacts_safe
    return counters, safe


def _artifact_counter_snapshot(root: Path) -> tuple[dict[str, Any], bool]:
    counters: dict[str, Any] = {
        "measured_runs": 0,
        "candidate_count": 0,
        "shortlist_count": 0,
        "selection_accesses": 0,
        "baseline_commitment_present": False,
        "freeze_started": False,
    }
    safe = True
    measured_run_ids: set[str] = set()
    campaign_root = root / "campaigns/scope-autoindex-v1"
    for directory_name in P2_COUNTER_ARTIFACT_DIRS:
        directory = campaign_root / directory_name
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.json")):
            p2_named = any(token in path.stem.casefold() for token in ("p2-", "p2_", ".p2"))
            if path.is_symlink() or not path.is_file():
                safe = safe and not p2_named
                continue
            try:
                payload = _json_file(path)
            except (OSError, UnicodeError, ValueError):
                safe = safe and not p2_named
                continue
            schema_version = str(payload.get("schema_version", ""))
            if not schema_version.startswith("myis.p2-"):
                continue
            try:
                artifact = validate_p2_artifact(payload, repository_root=root)
            except (P2ContractError, TypeError, ValueError):
                safe = False
                continue
            if schema_version not in P2_LIFECYCLE_SCHEMAS:
                continue
            safe = False
            if schema_version == "myis.p2-candidate-ledger.v1":
                counters["candidate_count"] = max(
                    counters["candidate_count"], int(artifact.get("candidate_count", 0) or 0)
                )
            elif schema_version in {
                "myis.p2-baseline-commitment.v1",
                "myis.p2-baseline-reproduction-receipt.v1",
            }:
                counters["baseline_commitment_present"] = True
            elif schema_version == "myis.p2-shortlist-freeze-receipt.v1":
                counters["freeze_started"] = True
                counters["shortlist_count"] = max(
                    counters["shortlist_count"], len(artifact.get("candidate_ids", []))
                )
            elif schema_version == "myis.p2-selection-receipt.v1":
                counters["selection_accesses"] = max(
                    counters["selection_accesses"],
                    int(artifact.get("selection_exposure_count", 0) or 0),
                )
            elif (
                schema_version == "myis.p2-manifest.v1"
                and artifact.get("evidence_class") == "train_selection_measured"
                and artifact.get("status") in {"valid", "negative_development"}
            ):
                measured_run_ids.add(str(artifact.get("run_id", path.stem)))
    counters["measured_runs"] = len(measured_run_ids)
    return counters, safe


def _store_snapshot(
    root: Path,
    worktrees: list[Path],
    *,
    check_stores: bool,
) -> tuple[dict[str, dict[str, Any]], bool, int]:
    raw_paths: dict[str, Path | None] = {}
    stores: dict[str, dict[str, Any]] = {}
    for name in STORE_ENVIRONMENT:
        raw = os.environ.get(name)
        raw_paths[name] = Path(raw).expanduser() if raw else None
        if not check_stores:
            stores[name] = _not_run_store(raw_paths[name])
            continue
        stores[name] = _inspect_store(name, raw_paths[name], worktrees)
    paths = [path for path in raw_paths.values() if path is not None]
    overlap_ok = len(paths) == 2 and not _paths_overlap(paths[0], paths[1])
    free_space_by_filesystem: dict[str, int] = {}
    for name, path in raw_paths.items():
        store = stores[name]
        if path is None or store.get("status") != "passed":
            continue
        identity = _filesystem_identity(path)
        free_space = int(store.get("free_space_bytes", 0))
        if identity in free_space_by_filesystem:
            free_space_by_filesystem[identity] = min(
                free_space_by_filesystem[identity], free_space
            )
        else:
            free_space_by_filesystem[identity] = free_space
    aggregate = sum(free_space_by_filesystem.values())
    return stores, overlap_ok, aggregate


def _inspect_store(name: str, value: Path | None, worktrees: list[Path]) -> dict[str, Any]:
    if value is None:
        return _not_run_store(None, status="not_configured")
    commitment = canonical_sha256({"store": name, "path": os.path.normcase(str(value.resolve(strict=False)))})
    if not value.is_absolute():
        return {
            "configured": True,
            "exists": bool(value.exists()),
            "is_directory": False,
            "outside_all_worktrees": False,
            "unsafe_link_or_junction": False,
            "writable_sentinel_created": False,
            "writable_sentinel_cleaned": False,
            "free_space_bytes": 0,
            "path_commitment_sha256": commitment,
            "status": "failed",
        }
    unsafe = _path_has_unsafe_link(value)
    exists = value.exists() or value.is_symlink()
    is_directory = exists and value.is_dir() and not unsafe
    resolved = value.resolve(strict=False)
    outside = bool(worktrees) and all(not _paths_overlap(root, resolved) for root in worktrees)
    sentinel_created = False
    sentinel_cleaned = False
    free_space = 0
    if is_directory and outside:
        sentinel = value / f".myis-p2-preflight-{uuid.uuid4().hex}.sentinel"
        try:
            descriptor = os.open(sentinel, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                os.write(descriptor, b"p2-preflight")
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            sentinel_created = True
        except OSError:
            sentinel_created = False
        finally:
            if sentinel_created:
                try:
                    sentinel.unlink()
                    sentinel_cleaned = True
                except OSError:
                    sentinel_cleaned = False
        try:
            free_space = max(0, int(shutil.disk_usage(value).free))
        except OSError:
            free_space = 0
    passed = bool(
        exists
        and is_directory
        and outside
        and not unsafe
        and sentinel_created
        and sentinel_cleaned
    )
    return {
        "configured": True,
        "exists": bool(exists),
        "is_directory": bool(is_directory),
        "outside_all_worktrees": bool(outside),
        "unsafe_link_or_junction": bool(unsafe),
        "writable_sentinel_created": bool(sentinel_created),
        "writable_sentinel_cleaned": bool(sentinel_cleaned),
        "free_space_bytes": free_space,
        "path_commitment_sha256": commitment,
        "status": "passed" if passed else "failed",
    }


def _not_run_store(value: Path | None = None, *, status: str = "not_run") -> dict[str, Any]:
    raw = os.path.normcase(str(value.resolve(strict=False))) if value is not None else "unconfigured"
    return {
        "configured": value is not None,
        "exists": False,
        "is_directory": False,
        "outside_all_worktrees": False,
        "unsafe_link_or_junction": False,
        "writable_sentinel_created": False,
        "writable_sentinel_cleaned": False,
        "free_space_bytes": 0,
        "path_commitment_sha256": canonical_sha256({"store": raw}),
        "status": status,
    }


def _git_worktree_roots(root: Path) -> list[Path]:
    try:
        completed = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.SubprocessError):
        return [root]
    roots: list[Path] = []
    for line in completed.stdout.splitlines():
        if line.startswith("worktree "):
            candidate = Path(line[9:].strip()).resolve(strict=False)
            if candidate not in roots:
                roots.append(candidate)
    if root not in roots:
        roots.append(root)
    return roots


def _git_commit_exists(root: Path, commit: str) -> bool:
    try:
        completed = subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            cwd=root,
            check=False,
            capture_output=True,
        )
    except OSError:
        return False
    return completed.returncode == 0


def _tree_for_commit(root: Path, commit: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "show", "-s", "--format=%T", commit],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    value = completed.stdout.strip()
    return value if len(value) == 40 and all(char in "0123456789abcdef" for char in value) else None


def _required_free_space(value: int | None) -> int:
    if value is not None:
        if isinstance(value, bool) or value < 0:
            raise P2ContractError("required free space must be a non-negative integer")
        return int(value)
    raw = os.environ.get("MYIS_P2_PREFLIGHT_REQUIRED_FREE_SPACE_BYTES")
    if raw is None:
        return DEFAULT_REQUIRED_FREE_SPACE_BYTES
    try:
        parsed = int(raw)
    except ValueError as error:
        raise P2ContractError("required free space environment value is invalid") from error
    if parsed < 0:
        raise P2ContractError("required free space must be non-negative")
    return parsed


def _check(check_id: str, passed: bool, detail: str) -> dict[str, str]:
    return {"check_id": check_id, "status": "passed" if passed else "failed", "detail": detail}


def _path_has_unsafe_link(path: Path) -> bool:
    for current in _ancestors(path, None):
        if _is_link_or_junction(current):
            return True
    return False


def _ancestors(path: Path, stop: Path | None) -> list[Path]:
    target = Path(path)
    boundary = Path(stop) if stop is not None else None
    values: list[Path] = []
    current = target
    while True:
        values.append(current)
        if boundary is not None and current == boundary:
            break
        if current.parent == current:
            break
        current = current.parent
    return values


def _is_link_or_junction(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        info = path.lstat()
    except OSError:
        return False
    attributes = int(getattr(info, "st_file_attributes", 0))
    return bool(attributes & 0x400)


def _path_contains(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _paths_overlap(first: Path, second: Path) -> bool:
    left = first.resolve(strict=False)
    right = second.resolve(strict=False)
    return _path_contains(left, right) or _path_contains(right, left)


def _filesystem_identity(path: Path) -> str:
    try:
        resolved = path.resolve(strict=True)
        device = int(resolved.stat().st_dev)
        anchor = os.path.normcase(resolved.anchor)
    except OSError:
        return "unknown-filesystem"
    return f"{device}:{anchor}"


def _json_file(path: Path) -> dict[str, Any]:
    import json

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    return value


def _json_object(line: str) -> dict[str, Any]:
    import json

    value = json.loads(line)
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    return value


def _repository_root_from_profile(profile: Mapping[str, Any]) -> Path:
    """Resolve the active repository for direct receipt-builder callers."""

    del profile
    return Path(__file__).resolve().parents[3]
