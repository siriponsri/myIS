"""Receipt-validated, local-only A1.2 v13 instance disposition."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a1_2_watchdog_provider_destroy_dry_run_v12 import (
    POLICY_PATH as WATCHDOG_POLICY_PATH,
)
from .a1_2_watchdog_provider_destroy_dry_run_v12 import (
    _validate_result as validate_watchdog_result,
)

REVISION_ID = "a1.2-instance-disposition-v13"
POLICY_PATH = Path("control/armindex/a1.2/instance-disposition-policy.v13.json")
SCHEMA_PATH = Path("schemas/armindex/a1.2-instance-disposition-result.v13.json")
DESTROY_READINESS_SCHEMA_PATH = Path(
    "schemas/armindex/a1.2-provider-destroy-readiness.v13.json"
)
PROVIDER_TEMPLATE_PATH = Path(
    "control/armindex/a1.2/provider-admission-input-template.v12.json"
)
BUDGET_ADMISSION_PATH = Path(
    "control/armindex/a1.2/whole-workload-budget-admission.v12.json"
)
RESULT_SCHEMA = "myis.armindex-a1.2-instance-disposition-result.v13"
POLICY_SCHEMA = "myis.armindex-a1.2-instance-disposition-policy.v13"
NO_ACTIONS = [
    "provider_contact", "ssh", "provider_cli", "provider_destruction",
    "launch_allowed", "adopted_for_execution", "measured_retrieval",
    "optimization", "selection", "final", "paid_api_work", "model_weight_changes",
]
RECEIPT_KEYS = (
    "preflight_identity", "provider_identity_observation", "provider_quote_observation",
    "safe_return", "teardown_export", "local_collection", "protected_scan",
    "clean_worker_proof", "watchdog_destroy_dry_run", "provider_destroy_readiness",
    "next_goal_authorization",
)
EVIDENCE_KEYS = set(RECEIPT_KEYS) | {"evaluation_time_utc", "owner_requests_destroy"}
HASH = re.compile(r"^[a-f0-9]{64}$")
GIT = re.compile(r"^[a-f0-9]{40}$")


class InstanceDispositionV13Error(ValueError):
    """Raised when the local evaluator or emitted receipt is invalid."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InstanceDispositionV13Error(f"invalid JSON: {path.as_posix()}") from error
    if not isinstance(value, dict):
        raise InstanceDispositionV13Error(f"JSON object required: {path.as_posix()}")
    return value


def _hash(value: object) -> bool:
    return isinstance(value, str) and HASH.fullmatch(value) is not None


def _time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        return datetime.fromisoformat(value).astimezone(UTC)
    except ValueError:
        return None


def _self_hashed(receipt: Mapping[str, Any]) -> bool:
    return _hash(receipt.get("receipt_sha256")) and receipt.get("receipt_sha256") == canonical_sha256(
        {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    )


def _policy(root: Path) -> Mapping[str, Any]:
    policy = _load(root / POLICY_PATH)
    if (
        policy.get("schema_version") != POLICY_SCHEMA
        or policy.get("policy_id") != REVISION_ID
        or policy.get("status") != "PENDING_LIVE_PROVIDER"
        or policy.get("current_disposition") != "NO_LIVE_INSTANCE"
        or policy.get("launch_allowed") is not False
        or policy.get("does_not_authorize") != NO_ACTIONS
    ):
        raise InstanceDispositionV13Error("v13 policy identity or safety boundary mismatch")
    return policy


def current_status(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    _policy(root)
    return {
        "status": "PENDING_LIVE_PROVIDER",
        "current_disposition": "NO_LIVE_INSTANCE",
        "policy_id": REVISION_ID,
        "policy_file_sha256": file_sha256(root / POLICY_PATH),
        "launch_allowed": False,
        "adopted_for_execution": False,
    }


def _source(root: Path, value: object) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping) or set(value) not in ({"receipt"}, {"external_path"}):
        return None
    receipt: Mapping[str, Any] | None
    if "receipt" in value:
        receipt = value["receipt"] if isinstance(value["receipt"], Mapping) else None
    else:
        raw = value["external_path"]
        if not isinstance(raw, str) or not Path(raw).is_absolute():
            return None
        path = Path(raw).resolve()
        if path.is_relative_to(root) or not path.is_file():
            return None
        try:
            receipt = _load(path)
        except InstanceDispositionV13Error:
            return None
    try:
        if receipt is None:
            return None
        assert_aggregate_only(receipt)
    except ValueError:
        return None
    return receipt


def _generic(receipt: Mapping[str, Any] | None, kind: str) -> bool:
    expected_schema = (
        "myis.armindex-a1.2-provider-destroy-readiness-evidence.v13"
        if kind == "provider_destroy_readiness"
        else "myis.armindex-a1.2-instance-disposition-evidence.v13"
    )
    return bool(
        receipt
        and receipt.get("schema_version") == expected_schema
        and receipt.get("receipt_kind") == kind
        and receipt.get("status") == "PASS"
        and _hash(receipt.get("instance_identity_sha256"))
        and _self_hashed(receipt)
    )


def _valid_schema(root: Path, path: Path, receipt: Mapping[str, Any] | None) -> bool:
    if receipt is None:
        return False
    try:
        return not list(Draft202012Validator(_load(root / path)).iter_errors(receipt))
    except InstanceDispositionV13Error:
        return False


def _frozen_identity_sha256(identity: Mapping[str, Any] | None) -> str | None:
    if identity is None:
        return None
    fields = (
        "git_commit", "git_tree", "bundle_sha256", "model_lockset_sha256",
        "program_set_sha256", "image_reference", "image_manifest_digest",
        "gpu_uuid_set_sha256",
    )
    if any(field not in identity for field in fields):
        return None
    return canonical_sha256({field: identity[field] for field in fields})


def _semantic(receipt: Mapping[str, Any] | None, kind: str) -> bool:
    if not _generic(receipt, kind):
        return False
    assert receipt is not None
    checks: dict[str, bool] = {
        "preflight_identity": receipt.get("preflight_status") == "PASS",
        "provider_identity_observation": receipt.get("identity_observation_status") == "PASS",
        "provider_quote_observation": receipt.get("all_fee_quote_status") == "PASS",
        "safe_return": (
            receipt.get("safe_return_status") == "PASS"
            and receipt.get("local_validation_status") == "PASS"
            and receipt.get("collection_status") == "PASS"
            and receipt.get("teardown_status") == "PASS"
            and _hash(receipt.get("teardown_receipt_sha256"))
        ),
        "teardown_export": (
            receipt.get("teardown_status") == "PASS"
            and receipt.get("guest_process_cleanup_verified") is True
            and _hash(receipt.get("remote_cleanup_receipt_sha256"))
        ),
        "local_collection": (
            receipt.get("collection_status") == "PASS"
            and receipt.get("local_validation_status") == "PASS"
            and receipt.get("member_hash_validation_status") == "PASS"
            and isinstance(receipt.get("member_count"), int)
            and not isinstance(receipt.get("member_count"), bool)
            and int(receipt["member_count"]) >= 0
        ),
        "protected_scan": (
            receipt.get("protected_scan_status") == "PASS"
            and receipt.get("protected_boundary_clean") is True
        ),
        "clean_worker_proof": (
            receipt.get("clean_worker_proof_status") == "PASS"
            and receipt.get("worker_state") == "CLEAN"
            and receipt.get("gpu_process_count") == 0
            and receipt.get("child_process_count") == 0
        ),
        "next_goal_authorization": (
            receipt.get("owner_authorized") is True
            and receipt.get("owner_report_status") == "ACKNOWLEDGED"
            and isinstance(receipt.get("next_goal_id"), str)
            and bool(receipt.get("next_goal_id"))
            and _hash(receipt.get("owner_report_receipt_sha256"))
            and _hash(receipt.get("owner_decision_receipt_sha256"))
            and _hash(receipt.get("next_goal_authorization_sha256"))
        ),
    }
    return checks.get(kind, True)


def _fresh(receipt: Mapping[str, Any] | None, now: datetime | None, seconds: int) -> bool:
    observed = _time(receipt.get("observed_at_utc")) if receipt else None
    return bool(observed and now and 0 <= (now - observed).total_seconds() <= seconds)


def _same_identity(preflight: Mapping[str, Any] | None, current: Mapping[str, Any] | None) -> bool:
    fields = (
        "instance_identity_sha256", "gpu_uuid_set_sha256", "image_reference",
        "image_manifest_digest", "git_commit", "git_tree", "bundle_sha256",
        "model_lockset_sha256", "program_set_sha256",
    )
    if not _generic(preflight, "preflight_identity") or not _generic(current, "provider_identity_observation"):
        return False
    assert preflight is not None and current is not None
    return (
        all(preflight.get(field) == current.get(field) for field in fields)
        and all(_hash(preflight.get(field)) for field in ("instance_identity_sha256", "gpu_uuid_set_sha256", "bundle_sha256", "model_lockset_sha256", "program_set_sha256"))
        and isinstance(preflight.get("image_manifest_digest"), str)
        and str(preflight["image_manifest_digest"]).startswith("sha256:")
        and GIT.fullmatch(str(preflight.get("git_commit"))) is not None
        and GIT.fullmatch(str(preflight.get("git_tree"))) is not None
    )


def _same_attempt_export(receipts: Mapping[str, Mapping[str, Any] | None]) -> bool:
    keys = (
        "safe_return",
        "teardown_export",
        "local_collection",
        "protected_scan",
        "clean_worker_proof",
    )
    values = [receipts[key] for key in keys]
    if not all(_semantic(value, key) for key, value in zip(keys, values, strict=True)):
        return False
    assert all(value is not None for value in values)
    if not all(
        isinstance(value.get("attempt_id"), str)
        and bool(value["attempt_id"])
        and _hash(value.get("safe_export_archive_sha256"))
        and _hash(value.get("safe_export_members_sha256"))
        for value in values
    ):
        return False
    attempts = {str(value["attempt_id"]) for value in values}
    archives = {str(value["safe_export_archive_sha256"]) for value in values}
    manifests = {str(value["safe_export_members_sha256"]) for value in values}
    if len(attempts) != 1 or len(archives) != 1 or len(manifests) != 1:
        return False
    if not all(_hash(value["safe_export_archive_sha256"]) and _hash(value["safe_export_members_sha256"]) for value in values):
        return False
    collection = receipts["local_collection"]
    safe_return = receipts["safe_return"]
    assert collection is not None and safe_return is not None
    return (
        isinstance(next(iter(attempts)), str)
        and bool(next(iter(attempts)))
        and safe_return.get("local_collection_receipt_sha256")
        == collection.get("receipt_sha256")
        and _hash(safe_return.get("local_collection_receipt_sha256"))
    )


def _budget(receipt: Mapping[str, Any] | None, policy: Mapping[str, Any], now: datetime | None) -> bool:
    if not _generic(receipt, "provider_quote_observation") or not _fresh(receipt, now, int(policy["evaluation"]["fresh_quote_max_age_seconds"])):
        return False
    assert receipt is not None
    template = _load(Path(__file__).resolve().parents[3] / PROVIDER_TEMPLATE_PATH)
    budget_contract = _load(Path(__file__).resolve().parents[3] / BUDGET_ADMISSION_PATH)
    if (
        receipt.get("provider_admission_template_file_sha256")
        != file_sha256(Path(__file__).resolve().parents[3] / PROVIDER_TEMPLATE_PATH)
        or receipt.get("provider_admission_template_sha256")
        != template.get("template_sha256")
        or receipt.get("budget_admission_file_sha256")
        != file_sha256(Path(__file__).resolve().parents[3] / BUDGET_ADMISSION_PATH)
        or receipt.get("budget_admission_sha256")
        != budget_contract.get("admission_sha256")
    ):
        return False
    fields = (
        "compute_hourly_rate_usd", "billing_granularity_seconds",
        "minimum_billable_seconds", "storage_fee_usd", "network_fee_usd",
        "platform_or_other_fee_usd", "tax_or_surcharge_usd",
        "remaining_ttl_seconds", "required_next_goal_ttl_seconds",
        "ttl_safety_margin_seconds", "charged_common_screen_usd",
        "charged_a1_usd", "charged_campaign_usd", "projected_common_screen_usd",
        "projected_a1_usd", "projected_campaign_usd", "worst_case_total_charge_usd",
    )
    if not all(isinstance(receipt.get(field), (int, float)) and not isinstance(receipt.get(field), bool) and math.isfinite(float(receipt[field])) and float(receipt[field]) >= 0 for field in fields):
        return False
    if (
        float(receipt["remaining_ttl_seconds"])
        < float(receipt["required_next_goal_ttl_seconds"])
        + float(receipt["ttl_safety_margin_seconds"])
        or float(receipt["billing_granularity_seconds"]) <= 0
    ):
        return False
    billable = max(
        float(receipt["minimum_billable_seconds"]),
        math.ceil(
            float(receipt["required_next_goal_ttl_seconds"])
            / float(receipt["billing_granularity_seconds"])
        ) * float(receipt["billing_granularity_seconds"]),
    )
    increment = (
        billable / 3600 * float(receipt["compute_hourly_rate_usd"])
        + float(receipt["storage_fee_usd"])
        + float(receipt["network_fee_usd"])
        + float(receipt["platform_or_other_fee_usd"])
        + float(receipt["tax_or_surcharge_usd"])
    )
    if not math.isclose(float(receipt["worst_case_total_charge_usd"]), increment, rel_tol=0, abs_tol=1e-9):
        return False
    stops = policy["evaluation"]["hard_stops_usd"]
    channels = (("common_screen", "common_screen"), ("a1", "a1_total"), ("campaign", "campaign"))
    return all(math.isclose(float(receipt[f"projected_{name}_usd"]), float(receipt[f"charged_{name}_usd"]) + increment, rel_tol=0, abs_tol=1e-9) and float(receipt[f"projected_{name}_usd"]) <= float(stops[key]) for name, key in channels)


def _watchdog(root: Path, receipt: Mapping[str, Any] | None, instance_hash: object) -> bool:
    if receipt is None:
        return False
    try:
        validate_watchdog_result(root, receipt)
    except Exception:  # noqa: BLE001 - fail closed when the external receipt validator rejects input.
        return False
    return (
        receipt.get("policy_file_sha256") == file_sha256(root / WATCHDOG_POLICY_PATH)
        and receipt.get("target_instance_identity_sha256") == instance_hash
        and receipt.get("actual_provider_destroy_capability") == "PENDING_LIVE_PROVIDER"
        and receipt.get("provider_action_performed") is False
    )


def _destroy_readiness(
    root: Path,
    receipt: Mapping[str, Any] | None,
    instance_hash: object,
    current_identity_receipt_sha256: object,
    watchdog_receipt_sha256: object,
    now: datetime | None,
    policy: Mapping[str, Any],
) -> bool:
    return bool(
        _valid_schema(root, DESTROY_READINESS_SCHEMA_PATH, receipt)
        and _semantic(receipt, "provider_destroy_readiness")
        and _fresh(
            receipt,
            now,
            int(policy["evaluation"]["fresh_destroy_readiness_max_age_seconds"]),
        )
        and receipt is not None
        and receipt.get("instance_identity_sha256") == instance_hash
        and receipt.get("provider_destroy_readiness_status")
        == "TESTED_LIVE_PROVIDER"
        and receipt.get("actual_provider_destroy_capability")
        == "TESTED_LIVE_PROVIDER"
        and receipt.get("provider_action_performed") is False
        and _hash(receipt.get("destroy_command_template_sha256"))
        and receipt.get("provider_identity_observation_receipt_sha256")
        == current_identity_receipt_sha256
        and receipt.get("watchdog_destroy_dry_run_receipt_sha256")
        == watchdog_receipt_sha256
    )


def _reasons(root: Path, evidence: Mapping[str, Any], policy: Mapping[str, Any]) -> tuple[list[str], dict[str, str]]:
    now = _time(evidence.get("evaluation_time_utc"))
    receipts = {key: _source(root, evidence.get(key)) for key in RECEIPT_KEYS}
    hashes = {key: str(value["receipt_sha256"]) for key, value in receipts.items() if value and _self_hashed(value)}
    reasons = [f"missing_or_invalid_{key}" for key, value in receipts.items() if value is None]
    preflight, current = receipts["preflight_identity"], receipts["provider_identity_observation"]
    if not _fresh(current, now, int(policy["evaluation"]["fresh_identity_max_age_seconds"])):
        reasons.append("provider_identity_not_fresh")
    if not _same_identity(preflight, current):
        reasons.append("instance_or_frozen_identity_mismatch")
    if not _semantic(preflight, "preflight_identity"):
        reasons.append("preflight_identity_semantics_invalid")
    if not _semantic(current, "provider_identity_observation"):
        reasons.append("provider_identity_semantics_invalid")
    frozen_identity = _frozen_identity_sha256(preflight)
    if not _budget(receipts["provider_quote_observation"], policy, now):
        reasons.append("quote_not_fresh_or_budget_insufficient")
    if not _same_attempt_export(receipts):
        reasons.append("same_attempt_export_collection_binding_invalid")
    protected = receipts["protected_scan"]
    if not _semantic(protected, "protected_scan"):
        reasons.append("protected_boundary_not_clean")
    worker = receipts["clean_worker_proof"]
    if not _semantic(worker, "clean_worker_proof") or not _fresh(worker, now, int(policy["evaluation"]["fresh_identity_max_age_seconds"])):
        reasons.append("clean_worker_proof_missing_or_stale")
    if not _watchdog(root, receipts["watchdog_destroy_dry_run"], current.get("instance_identity_sha256") if current else None):
        reasons.append("watchdog_destroy_dry_run_unvalidated")
    if not _destroy_readiness(
        root,
        receipts["provider_destroy_readiness"],
        current.get("instance_identity_sha256") if current else None,
        current.get("receipt_sha256") if current else None,
        receipts["watchdog_destroy_dry_run"].get("receipt_sha256") if receipts["watchdog_destroy_dry_run"] else None,
        now,
        policy,
    ):
        reasons.append("provider_destroy_readiness_missing_or_not_tested")
    goal = receipts["next_goal_authorization"]
    if not _semantic(goal, "next_goal_authorization") or goal.get("compatible_next_goal") is not True or goal.get("fresh_provider_admission_required") is not False or goal.get("compatible_frozen_identity_sha256") != frozen_identity:
        reasons.append("next_goal_not_authorized_or_requires_fresh_provider")
    if evidence.get("owner_requests_destroy") is not False:
        reasons.append("owner_requested_destroy")
    return sorted(set(reasons)), hashes


def evaluate_payload(repository_root: Path, evidence: Mapping[str, Any], *, receipt_id: str) -> dict[str, Any]:
    root = repository_root.resolve()
    policy = _policy(root)
    if not isinstance(evidence, Mapping) or set(evidence) != EVIDENCE_KEYS:
        raise InstanceDispositionV13Error("v13 evidence keys are incomplete or unsafe")
    if not isinstance(receipt_id, str) or re.fullmatch(r"a1\.2-instance-disposition-[a-z0-9._-]+-v13", receipt_id) is None:
        raise InstanceDispositionV13Error("invalid v13 receipt identifier")
    reasons, hashes = _reasons(root, evidence, policy)
    destroy_readiness = _source(root, evidence.get("provider_destroy_readiness"))
    body: dict[str, Any] = {"schema_version": RESULT_SCHEMA, "receipt_id": receipt_id, "revision_id": REVISION_ID, "status": "PASS", "scientific_authority": False, "policy_id": REVISION_ID, "policy_file_sha256": file_sha256(root / POLICY_PATH), "evaluation_input_sha256": canonical_sha256(dict(evidence)), "disposition": "REUSE_ELIGIBLE" if not reasons else "DESTROY_REQUIRED", "failure_reasons": reasons, "actual_provider_destroy_capability": "PENDING_LIVE_PROVIDER", "destroy_readiness_evidence_status": "TESTED_LIVE_PROVIDER" if destroy_readiness and destroy_readiness.get("actual_provider_destroy_capability") == "TESTED_LIVE_PROVIDER" else "MISSING_OR_INVALID", "validated_receipt_sha256s": hashes, "next_owner_instruction": "Owner continue next goal on PLAN" if not reasons else "Owner destroy instance", "does_not_authorize": list(NO_ACTIONS), "launch_allowed": False}
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _validate_result(root, receipt)
    return receipt


def _validate_result(root: Path, receipt: Mapping[str, Any]) -> None:
    errors = sorted(Draft202012Validator(_load(root / SCHEMA_PATH)).iter_errors(receipt), key=lambda error: list(error.path))
    if errors or not _self_hashed(receipt) or ((receipt.get("disposition") == "REUSE_ELIGIBLE") != (receipt.get("failure_reasons") == [])):
        raise InstanceDispositionV13Error("v13 disposition result is invalid")
    assert_aggregate_only(receipt)


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-instance-disposition-v13")
    parser.add_argument("command", choices=("status", "evaluate"))
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--evidence", type=Path)
    parser.add_argument(
        "--receipt-id", default="a1.2-instance-disposition-local-v13"
    )
    args = parser.parse_args()
    if args.command == "status":
        result = current_status(args.repository_root)
    else:
        if args.evidence is None:
            parser.error("--evidence is required for evaluate")
        result = evaluate_payload(args.repository_root, _load(args.evidence), receipt_id=args.receipt_id)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
