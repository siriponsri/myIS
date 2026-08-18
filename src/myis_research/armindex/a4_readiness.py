"""Contract-only readiness checks for ArmIndex A4.

This module deliberately stops before production measurement or Selection.  It
accepts aggregate-safe manifests and hashes only; protected membership, qrels,
per-query outcomes, and model payloads are not valid inputs.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
from typing import Any

from ..kernel.canonical import canonical_sha256
from ..p2.measured_state import AdvisoryFileLock, atomic_write_json


SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
PRIMARY_ARMS = ("ARM-03", "ARM-04", "ARM-05")
COMMERCIAL_ARMS = ("ARM-01", "ARM-02", "ARM-04", "ARM-05")
REQUIRED_PROFILES = ("FAST", "BALANCED", "DEEP")
SELECTION_PREFLIGHT_CHECKS = (
    "a3_closeout_verified",
    "commercial_license_verified",
    "pareto_frontier_verified",
    "profiles_complete",
    "legal_transfer_isolated",
    "protected_boundary_verified",
)
_PROTECTED_KEYS = frozenset(
    {
        "qrel",
        "qrels",
        "membership",
        "memberships",
        "per_query_outcome",
        "per_query_outcomes",
        "raw_query_id",
        "raw_query_ids",
        "selection_feedback",
        "final_feedback",
        "credentials",
        "secret",
        "raw_provider_payload",
    }
)


class A4ReadinessError(ValueError):
    """Raised when a contract-only A4 invariant is not satisfied."""


def validate_a3_bindings(
    manifest: Mapping[str, Any],
    authority: Mapping[str, Any] | None = None,
    *,
    expected_binding_hashes: Mapping[str, str] | None = None,
    require_closeout: bool = False,
) -> dict[str, Any]:
    """Validate the A3-to-A4 handoff without opening protected data.

    The current preparation manifest is intentionally accepted as pending.  A
    future closeout caller sets ``require_closeout=True`` and must provide
    winner hashes and an explicit A3 closeout receipt.
    """

    _safe_scan(manifest)
    if authority is not None:
        _safe_scan(authority)
    if manifest.get("schema_version") != "myis.armindex-a3-three-primary-preparation-manifest.v1":
        raise A4ReadinessError("unsupported A3 preparation manifest schema")
    if manifest.get("bundle_id") != "A3_THREE_PRIMARY_TRANSFER_HARNESSOPT_PENDING":
        raise A4ReadinessError("A3 bundle identity is not the three-primary bundle")
    raw_arms = manifest.get("arms")
    if not isinstance(raw_arms, list) or any(not isinstance(item, Mapping) for item in raw_arms):
        raise A4ReadinessError("A3 arm declarations are malformed")
    arms = tuple(item.get("arm_id") for item in raw_arms)
    if arms != PRIMARY_ARMS:
        raise A4ReadinessError("A3 primary arm scope must be ARM-03, ARM-04, ARM-05")
    matrix = manifest.get("transfer_matrix")
    if not isinstance(matrix, list) or len(matrix) != 9 or any(not isinstance(item, Mapping) for item in matrix):
        raise A4ReadinessError("A3 transfer matrix must contain all nine primary cells")
    pairs = {(item.get("source_arm_id"), item.get("target_arm_id")) for item in matrix}
    if pairs != {(source, target) for source in PRIMARY_ARMS for target in PRIMARY_ARMS}:
        raise A4ReadinessError("A3 transfer matrix is incomplete or contains an invalid arm")
    complementarity = manifest.get("complementarity_controls", {})
    if complementarity.get("same_depth_required") is not True:
        raise A4ReadinessError("A3 complementarity must use same-depth controls")
    controls = tuple(complementarity.get("control_ids", ()))
    required_controls = {"best_single", "all_primary_rrf60", "top_two_rrf60", "top_three_rrf60", "commercial_only_fixed_union"}
    if not required_controls.issubset(controls):
        raise A4ReadinessError("A3 complementarity controls are incomplete")
    if tuple(complementarity.get("commercial_only_fixed_union_arm_ids", ())) != ("ARM-04", "ARM-05"):
        raise A4ReadinessError("commercial fixed union must be ARM-04 plus ARM-05")
    if authority is not None:
        if authority.get("schema_version") != "myis.armindex-a3-three-primary-preparation-authority.v1":
            raise A4ReadinessError("unsupported A3 authority schema")
        if tuple(authority.get("primary_arm_scope", ())) != PRIMARY_ARMS:
            raise A4ReadinessError("A3 authority primary scope differs from the manifest")
    if expected_binding_hashes:
        for name, expected in expected_binding_hashes.items():
            _require_sha256(expected, name)
            observed = _lookup_binding(manifest, authority, name)
            if observed != expected:
                raise A4ReadinessError(f"A3 binding mismatch for {name}")
    if require_closeout:
        state = str((authority or {}).get("authority_state", ""))
        if state not in {"A3_CLOSED", "READY_FOR_A4", "PASS_A3_CLOSEOUT"}:
            raise A4ReadinessError("A3 closeout state is not terminal")
        if not (authority or {}).get("a3_closeout_receipt_sha256"):
            raise A4ReadinessError("A3 closeout receipt is required before A4")
        for item in raw_arms:
            _require_sha256(item.get("winner_program_sha256"), f"{item['arm_id']}.winner_program_sha256")
    return {
        "status": "ready_for_a4_contract_checks" if require_closeout else "pending_a3_closeout",
        "primary_arm_scope": list(PRIMARY_ARMS),
        "commercial_fixed_union": ["ARM-04", "ARM-05"],
        "selection_permitted": False,
        "final_permitted": False,
    }


def validate_commercial_eligibility(
    license_matrix: Sequence[Mapping[str, Any]],
    candidate_arm_ids: Iterable[str],
    *,
    commercial_only: bool = False,
) -> dict[str, Any]:
    """Validate explicit model/license snapshots for a profile or candidate."""

    _safe_scan(license_matrix)
    if not isinstance(license_matrix, Sequence) or any(not isinstance(row, Mapping) for row in license_matrix):
        raise A4ReadinessError("license matrix rows are malformed")
    rows = {str(row.get("arm_id")): row for row in license_matrix}
    if len(rows) != len(license_matrix):
        raise A4ReadinessError("license matrix contains duplicate arm IDs")
    selected = tuple(candidate_arm_ids)
    if not selected or len(set(selected)) != len(selected):
        raise A4ReadinessError("candidate arm IDs must be non-empty and unique")
    if any(not re.fullmatch(r"ARM-0[1-5]", arm_id) for arm_id in selected):
        raise A4ReadinessError("candidate arm IDs are not active ArmIndex arms")
    unknown = set(selected) - set(rows)
    if unknown:
        raise A4ReadinessError(f"license matrix is missing arms: {sorted(unknown)}")
    eligible: list[str] = []
    excluded: list[str] = []
    for arm_id in selected:
        row = rows[arm_id]
        if not row.get("license") and not row.get("license_id"):
            raise A4ReadinessError(f"license is missing for {arm_id}")
        status = row.get("commercial_status")
        if status not in {"commercial_capable", "research_non_commercial", "mixed", "not_applicable"}:
            raise A4ReadinessError(f"unknown commercial status for {arm_id}")
        if status == "commercial_capable":
            eligible.append(arm_id)
        else:
            excluded.append(arm_id)
    if commercial_only and excluded:
        raise A4ReadinessError(f"commercial profile includes non-commercial arms: {excluded}")
    return {
        "selected_arm_ids": list(selected),
        "commercial_eligible_arm_ids": eligible,
        "excluded_arm_ids": excluded,
        "commercial_only": commercial_only,
    }


def non_dominated_frontier(
    points: Iterable[Mapping[str, Any]],
    *,
    id_key: str = "profile_id",
    maximize: Sequence[str] = ("recall_at_100", "throughput_qps"),
    minimize: Sequence[str] = ("latency_p95_ms", "cost_per_query_usd", "index_size_bytes"),
) -> tuple[str, ...]:
    """Return deterministic IDs on the quality/latency/cost Pareto frontier."""

    try:
        rows = [dict(point) for point in points]
    except (TypeError, ValueError) as error:
        raise A4ReadinessError("Pareto points must be mappings") from error
    ids = [str(row.get(id_key, "")) for row in rows]
    if not rows or any(not item for item in ids) or len(ids) != len(set(ids)):
        raise A4ReadinessError("Pareto points require unique non-empty IDs")
    dimensions = tuple(dict.fromkeys((*maximize, *minimize)))
    for row in rows:
        for dimension in dimensions:
            value = row.get(dimension)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise A4ReadinessError(f"Pareto metric {dimension} must be finite numeric")

    def dominates(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
        no_worse = all(left[key] >= right[key] for key in maximize) and all(
            left[key] <= right[key] for key in minimize
        )
        strict = any(left[key] > right[key] for key in maximize) or any(
            left[key] < right[key] for key in minimize
        )
        return no_worse and strict

    frontier = [row[id_key] for row in rows if not any(dominates(other, row) for other in rows if other is not row)]
    return tuple(sorted(str(item) for item in frontier))


def validate_production_profile_manifest(
    manifest: Mapping[str, Any],
    license_matrix: Sequence[Mapping[str, Any]],
    *,
    a3_binding_sha256: str,
) -> dict[str, Any]:
    """Require complete, contract-only FAST/BALANCED/DEEP profile entries."""

    _safe_scan(manifest)
    _require_sha256(a3_binding_sha256, "a3_binding_sha256")
    if manifest.get("schema_version") != "myis.armindex-a4-production-profile-manifest.v1":
        raise A4ReadinessError("unsupported A4 production profile manifest schema")
    if manifest.get("status") != "contract_only" or manifest.get("measured_execution") is not False:
        raise A4ReadinessError("A4 profile manifest must remain contract-only")
    if manifest.get("selection_accesses") != 0 or manifest.get("final_accesses") != 0:
        raise A4ReadinessError("A4 profile manifest cannot contain Selection or Final access")
    profiles = manifest.get("profiles")
    if not isinstance(profiles, list) or any(not isinstance(row, Mapping) for row in profiles):
        raise A4ReadinessError("A4 profile rows are malformed")
    if {row.get("profile_id") for row in profiles} != set(REQUIRED_PROFILES):
        raise A4ReadinessError("A4 profile manifest must contain FAST, BALANCED, and DEEP exactly once")
    if len(profiles) != len(REQUIRED_PROFILES):
        raise A4ReadinessError("A4 profile IDs must be unique")
    checked: list[str] = []
    for row in profiles:
        required = {
            "profile_id", "harness_configuration_sha256", "arm_ids", "mode",
            "maximum_candidate_depth", "commercial_only", "readiness",
            "a3_binding_sha256", "non_dominated",
        }
        if set(row) != required:
            raise A4ReadinessError(f"profile {row.get('profile_id')} is incomplete")
        if row["a3_binding_sha256"] != a3_binding_sha256 or row["readiness"] != "contract_only":
            raise A4ReadinessError("profile binding or readiness marker is invalid")
        _require_sha256(row["harness_configuration_sha256"], "harness_configuration_sha256")
        arms = tuple(row["arm_ids"])
        if not arms or len(set(arms)) != len(arms) or any(arm not in COMMERCIAL_ARMS + ("ARM-03",) for arm in arms):
            raise A4ReadinessError("profile arm IDs are invalid")
        if (
            isinstance(row["maximum_candidate_depth"], bool)
            or not isinstance(row["maximum_candidate_depth"], int)
            or row["maximum_candidate_depth"] < 1
            or row["maximum_candidate_depth"] > 2000
        ):
            raise A4ReadinessError("profile depth is outside the bounded contract")
        if not isinstance(row["commercial_only"], bool):
            raise A4ReadinessError("profile commercial_only marker must be boolean")
        validate_commercial_eligibility(license_matrix, arms, commercial_only=bool(row["commercial_only"]))
        if row["profile_id"] == "FAST" and (row["mode"] != "synchronous" or "ARM-01" not in arms or len(arms) > 2):
            raise A4ReadinessError("FAST must be synchronous, include BM25, and use at most two arms")
        if row["profile_id"] == "BALANCED" and (row["mode"] != "synchronous" or not row["commercial_only"]):
            raise A4ReadinessError("BALANCED must be synchronous and commercial-only")
        if row["profile_id"] == "DEEP" and row["mode"] not in {"synchronous", "asynchronous"}:
            raise A4ReadinessError("DEEP mode is invalid")
        if not isinstance(row["non_dominated"], bool):
            raise A4ReadinessError("profile non_dominated marker must be boolean")
        checked.append(str(row["profile_id"]))
    return {"status": "validated_contract_only", "profiles": sorted(checked), "selection_permitted": False}


def validate_legal_transfer_isolation(transfer: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a legal-transfer diagnostic is isolated from the patent campaign."""

    _safe_scan(transfer)
    required = {
        "transfer_id", "source_arm_id", "target_domain", "source_program_sha256",
        "target_adapter_sha256", "mapping_sha256", "transfer_state",
        "feedback_into_patent_campaign", "protected_data_accessed",
        "selection_accesses", "final_accesses",
    }
    if set(transfer) != required:
        raise A4ReadinessError("legal-transfer record is incomplete")
    if transfer["target_domain"] != "legal_structured_retrieval":
        raise A4ReadinessError("legal transfer must use the isolated legal structured-retrieval domain")
    for field in ("source_program_sha256", "target_adapter_sha256", "mapping_sha256"):
        _require_sha256(transfer[field], field)
    if transfer["source_arm_id"] not in (*PRIMARY_ARMS, "ARM-01", "ARM-02"):
        raise A4ReadinessError("legal transfer source arm is not an active ArmIndex arm")
    if transfer["transfer_state"] not in {"TRANSFER_SUPPORTED", "TRANSFER_MIXED", "STOP_WITH_EVIDENCE_NO_TRANSFER", "BLOCKED_INCOMPATIBLE_SCHEMA"}:
        raise A4ReadinessError("legal transfer state is invalid")
    if transfer["feedback_into_patent_campaign"] is not False or transfer["protected_data_accessed"] is not False:
        raise A4ReadinessError("legal transfer cannot feed back or access protected payloads")
    if transfer["selection_accesses"] != 0 or transfer["final_accesses"] != 0:
        raise A4ReadinessError("legal transfer cannot open Selection or Final")
    return {"status": "isolated", "transfer_id": transfer["transfer_id"], "patent_feedback": False}


def consume_selection_preflight_counter(
    counter_path: Path,
    *,
    request_id: str,
    frozen_bindings_sha256: str,
    checks: Mapping[str, bool],
) -> dict[str, Any]:
    """Atomically consume the one-shot Selection preflight counter.

    The counter is not Selection access. It only records that all aggregate-safe
    readiness checks passed before a future Owner-authorized Selection call.
    Any missing/false check or malformed prior state fails closed.
    """

    if not request_id or not isinstance(request_id, str):
        raise A4ReadinessError("Selection preflight request_id is required")
    _require_sha256(frozen_bindings_sha256, "frozen_bindings_sha256")
    if (
        not isinstance(checks, Mapping)
        or set(checks) != set(SELECTION_PREFLIGHT_CHECKS)
        or any(value is not True for value in checks.values())
    ):
        raise A4ReadinessError("all exact Selection preflight checks must pass")
    path = Path(counter_path)
    if path.is_symlink():
        raise A4ReadinessError("Selection preflight counter cannot be a symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = AdvisoryFileLock(path.with_name(path.name + ".lock"))
    try:
        lock.__enter__()
    except (OSError, BlockingIOError) as error:
        raise A4ReadinessError("Selection preflight counter is locked") from error
    try:
        if path.exists():
            current = _read_json(path)
            if current.get("schema_version") != "myis.armindex-a4-selection-preflight-counter.v1":
                raise A4ReadinessError("Selection preflight counter is malformed")
            if current.get("preflight_count") != 0:
                raise A4ReadinessError("Selection preflight counter was already consumed")
        payload: dict[str, Any] = {
            "schema_version": "myis.armindex-a4-selection-preflight-counter.v1",
            "preflight_count": 1,
            "request_id": request_id,
            "frozen_bindings_sha256": frozen_bindings_sha256,
            "checks": {key: True for key in SELECTION_PREFLIGHT_CHECKS},
            "selection_accesses": 0,
            "final_accesses": 0,
            "recorded_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        payload["counter_sha256"] = canonical_sha256(payload)
        atomic_write_json(path, payload)
        return payload
    finally:
        lock.__exit__(None, None, None)


def _lookup_binding(manifest: Mapping[str, Any], authority: Mapping[str, Any] | None, name: str) -> str | None:
    for source in (manifest, authority or {}):
        value = source.get(name)
        if isinstance(value, str):
            return value
        nested = source.get("bindings")
        if isinstance(nested, Mapping) and isinstance(nested.get(name), str):
            return str(nested[name])
    return None


def _require_sha256(value: Any, field: str) -> None:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise A4ReadinessError(f"{field} must be a lowercase SHA-256 hash")


def _safe_scan(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).casefold().replace("-", "_").replace(" ", "_")
            if normalized in _PROTECTED_KEYS:
                raise A4ReadinessError(f"protected field is forbidden at {path}.{key}")
            _safe_scan(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _safe_scan(item, f"{path}[{index}]")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise A4ReadinessError("Selection preflight counter is unreadable") from error
    if not isinstance(value, dict):
        raise A4ReadinessError("Selection preflight counter must be a JSON object")
    return value


__all__ = [
    "A4ReadinessError",
    "COMMERCIAL_ARMS",
    "PRIMARY_ARMS",
    "REQUIRED_PROFILES",
    "SELECTION_PREFLIGHT_CHECKS",
    "consume_selection_preflight_counter",
    "non_dominated_frontier",
    "validate_a3_bindings",
    "validate_commercial_eligibility",
    "validate_legal_transfer_isolation",
    "validate_production_profile_manifest",
]
