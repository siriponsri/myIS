"""Local-only A1.2 v12 same-instance disposition evaluator.

This additive revision evaluates already-collected, aggregate-safe evidence.  It
never opens SSH, invokes a provider CLI, destroys an instance, or changes any
scientific authorization.  The current policy intentionally has no live target.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only


REVISION_ID = "a1.2-instance-disposition-v12"
POLICY_PATH = Path("control/armindex/a1.2/instance-disposition-policy.v12.json")
SCHEMA_PATH = Path("schemas/armindex/a1.2-instance-disposition-result.v12.json")
RESULT_SCHEMA = "myis.armindex-a1.2-instance-disposition-result.v12"
POLICY_SCHEMA = "myis.armindex-a1.2-instance-disposition-policy.v12"
CURRENT_DISPOSITION = "NO_LIVE_INSTANCE"
CURRENT_STATUS = "PENDING_LIVE_PROVIDER"
NO_ACTIONS = [
    "provider_contact", "ssh", "provider_cli", "provider_destruction",
    "launch_allowed", "adopted_for_execution", "measured_retrieval",
    "optimization", "selection", "final", "paid_api_work", "model_weight_changes",
]
_HASH = "^[a-f0-9]{64}$"
_FORBIDDEN_EVIDENCE_KEY = re.compile(
    r'"(?:provider_instance_id|instance_id|credential|credentials|private_key|qrels|query_ids|membership)"\s*:',
    re.IGNORECASE,
)
_ABSOLUTE_PATH = re.compile(r"(?:[A-Za-z]:\\|/Users/|/home/|\\\\[^\\]+\\)")
_EVIDENCE_KEYS = {
    "safe_return", "preflight_identity", "current_identity", "budget",
    "remaining_ttl_seconds", "ttl_safety_margin_seconds", "protected_boundary",
    "watchdog_destroy_dry_run", "next_goal", "owner_requests_destroy",
}


class InstanceDispositionV12Error(ValueError):
    """Raised when local disposition evidence is malformed or unsafe."""


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InstanceDispositionV12Error(f"invalid JSON: {path.as_posix()}") from error
    if not isinstance(value, dict):
        raise InstanceDispositionV12Error(f"JSON object required: {path.as_posix()}")
    return value


def _is_hash(value: object) -> bool:
    import re

    return isinstance(value, str) and re.fullmatch(_HASH, value) is not None


def _is_oci_digest(value: object) -> bool:
    return isinstance(value, str) and value.startswith("sha256:") and _is_hash(value[7:])


def _finite_nonnegative(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) and float(value) >= 0


def _validate_policy(policy: Mapping[str, Any]) -> None:
    if policy.get("schema_version") != POLICY_SCHEMA:
        raise InstanceDispositionV12Error("v12 policy schema mismatch")
    if policy.get("policy_id") != REVISION_ID:
        raise InstanceDispositionV12Error("v12 policy identifier mismatch")
    if policy.get("status") != CURRENT_STATUS or policy.get("current_disposition") != CURRENT_DISPOSITION:
        raise InstanceDispositionV12Error("v12 policy must remain pending with no live instance")
    if policy.get("launch_allowed") is not False or policy.get("does_not_authorize") != NO_ACTIONS:
        raise InstanceDispositionV12Error("v12 policy authorization boundary mismatch")
    if policy.get("future_dispositions") != ["REUSE_ELIGIBLE", "DESTROY_REQUIRED"]:
        raise InstanceDispositionV12Error("v12 policy disposition vocabulary mismatch")
    counters = policy.get("measured_counters")
    if not isinstance(counters, Mapping) or any(value != 0 for value in counters.values()):
        raise InstanceDispositionV12Error("v12 policy counters must remain zero")


def current_status(repository_root: Path) -> dict[str, Any]:
    """Return the immutable current state without performing any external action."""
    root = repository_root.resolve()
    policy = _load_object(root / POLICY_PATH)
    _validate_policy(policy)
    return {
        "status": CURRENT_STATUS,
        "current_disposition": CURRENT_DISPOSITION,
        "policy_id": REVISION_ID,
        "policy_file_sha256": file_sha256(root / POLICY_PATH),
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
        "charged_usd": 0,
    }


def _expect_mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise InstanceDispositionV12Error(f"{label} object required")
    return value


def _add_if(condition: bool, reason: str, reasons: list[str]) -> None:
    if not condition:
        reasons.append(reason)


def _same_hashes(preflight: Mapping[str, Any], current: Mapping[str, Any]) -> bool:
    fields = (
        "instance_identity_sha256", "gpu_uuid_set_sha256", "image_reference",
        "image_manifest_digest", "git_commit", "git_tree", "bundle_sha256",
        "staged_artifacts_sha256",
    )
    return all(preflight.get(field) == current.get(field) for field in fields) and all(
        _is_hash(preflight.get(field)) for field in (
            "instance_identity_sha256", "gpu_uuid_set_sha256", "bundle_sha256", "staged_artifacts_sha256"
        )
    ) and _is_oci_digest(preflight.get("image_manifest_digest"))


def _budget_passes(budget: Mapping[str, Any], policy: Mapping[str, Any]) -> bool:
    values = (
        "quote_age_seconds", "all_fee_hourly_usd", "planned_next_goal_seconds",
        "charged_common_screen_usd", "charged_a1_usd", "charged_campaign_usd",
        "projected_common_screen_usd", "projected_a1_usd", "projected_campaign_usd",
    )
    if not all(_finite_nonnegative(budget.get(field)) for field in values):
        return False
    expected_increment = float(budget["all_fee_hourly_usd"]) * float(budget["planned_next_goal_seconds"]) / 3600
    expected = {
        "common_screen": float(budget["charged_common_screen_usd"]) + expected_increment,
        "a1_total": float(budget["charged_a1_usd"]) + expected_increment,
        "campaign": float(budget["charged_campaign_usd"]) + expected_increment,
    }
    reported = {
        "common_screen": float(budget["projected_common_screen_usd"]),
        "a1_total": float(budget["projected_a1_usd"]),
        "campaign": float(budget["projected_campaign_usd"]),
    }
    stops = _expect_mapping(_expect_mapping(policy.get("evaluation"), "evaluation").get("hard_stops_usd"), "hard stops")
    return (
        float(budget["quote_age_seconds"]) <= float(_expect_mapping(policy["evaluation"], "evaluation")["fresh_quote_max_age_seconds"])
        and all(math.isclose(reported[key], expected[key], rel_tol=0, abs_tol=1e-9) for key in expected)
        and all(reported[key] <= float(stops[key]) for key in expected)
    )


def _input_reasons(evidence: Mapping[str, Any], policy: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    safe_return = _expect_mapping(evidence.get("safe_return"), "safe_return")
    preflight = _expect_mapping(evidence.get("preflight_identity"), "preflight_identity")
    current = _expect_mapping(evidence.get("current_identity"), "current_identity")
    budget = _expect_mapping(evidence.get("budget"), "budget")
    watchdog = _expect_mapping(evidence.get("watchdog_destroy_dry_run"), "watchdog_destroy_dry_run")
    protected = _expect_mapping(evidence.get("protected_boundary"), "protected_boundary")
    next_goal = _expect_mapping(evidence.get("next_goal"), "next_goal")

    _add_if(
        safe_return.get("local_validation_status") == "PASS"
        and safe_return.get("collection_status") == "PASS"
        and safe_return.get("teardown_status") == "PASS"
        and all(_is_hash(safe_return.get(key)) for key in ("archive_sha256", "members_sha256", "teardown_receipt_sha256", "collection_receipt_sha256"))
        and isinstance(safe_return.get("member_count"), int) and safe_return["member_count"] >= 0,
        "safe_return_not_validated", reasons,
    )
    _add_if(_same_hashes(preflight, current), "instance_identity_or_frozen_binding_changed", reasons)
    _add_if(_budget_passes(budget, policy), "quote_stale_or_budget_headroom_insufficient", reasons)
    _add_if(
        _finite_nonnegative(evidence.get("remaining_ttl_seconds"))
        and _finite_nonnegative(evidence.get("ttl_safety_margin_seconds"))
        and float(evidence["remaining_ttl_seconds"]) >= float(budget.get("planned_next_goal_seconds", -1)) + float(evidence["ttl_safety_margin_seconds"]),
        "remaining_ttl_insufficient", reasons,
    )
    _add_if(
        protected.get("status") == "PASS" and _is_hash(protected.get("scan_receipt_sha256")),
        "protected_boundary_not_clean", reasons,
    )
    _add_if(
        watchdog.get("status") == "PASS"
        and watchdog.get("mode") == "owner_local_dry_run"
        and watchdog.get("provider_action_performed") is False
        and watchdog.get("destroy_command_validated") is True
        and watchdog.get("ttl_trigger_simulated") is True
        and watchdog.get("guest_poweroff_is_provider_destruction") is False
        and watchdog.get("target_instance_identity_sha256") == current.get("instance_identity_sha256")
        and _is_hash(watchdog.get("receipt_sha256")),
        "watchdog_or_destroy_dry_run_failed", reasons,
    )
    _add_if(
        next_goal.get("owner_authorized") is True
        and isinstance(next_goal.get("goal_id"), str) and bool(next_goal["goal_id"])
        and _is_hash(next_goal.get("authorization_sha256"))
        and next_goal.get("execution_adoption_authorized") is False,
        "separate_next_goal_not_authorized", reasons,
    )
    _add_if(evidence.get("owner_requests_destroy") is False, "owner_requested_destroy", reasons)
    return sorted(set(reasons))


def _validate_safe_evidence(evidence: Mapping[str, Any]) -> None:
    if set(evidence) != _EVIDENCE_KEYS:
        raise InstanceDispositionV12Error("v12 evidence keys are incomplete or unsafe")
    assert_aggregate_only(evidence)
    serialized = json.dumps(evidence, ensure_ascii=True, sort_keys=True)
    if _FORBIDDEN_EVIDENCE_KEY.search(serialized):
        raise InstanceDispositionV12Error("v12 evidence contains a forbidden raw identifier or protected key")
    if _ABSOLUTE_PATH.search(serialized):
        raise InstanceDispositionV12Error("v12 evidence contains an absolute path")


def evaluate_payload(repository_root: Path, evidence: Mapping[str, Any], *, receipt_id: str) -> dict[str, Any]:
    """Fail closed on incomplete local evidence and return an aggregate-safe result."""
    root = repository_root.resolve()
    policy = _load_object(root / POLICY_PATH)
    _validate_policy(policy)
    if not isinstance(evidence, Mapping):
        raise InstanceDispositionV12Error("disposition evidence must be an object")
    _validate_safe_evidence(evidence)
    if not isinstance(receipt_id, str) or not receipt_id.startswith("a1.2-instance-disposition-"):
        raise InstanceDispositionV12Error("invalid v12 receipt identifier")
    if not receipt_id.endswith("-v12"):
        raise InstanceDispositionV12Error("v12 receipt identifier must end in -v12")
    reasons = _input_reasons(evidence, policy)
    disposition = "REUSE_ELIGIBLE" if not reasons else "DESTROY_REQUIRED"
    body: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "receipt_id": receipt_id,
        "revision_id": REVISION_ID,
        "status": "PASS",
        "scientific_authority": False,
        "claim_boundary": "Local-only instance-disposition evaluation; no provider contact, SSH, destruction, launch, adoption, or scientific execution.",
        "policy_id": REVISION_ID,
        "policy_file_sha256": file_sha256(root / POLICY_PATH),
        "evaluation_input_sha256": canonical_sha256(dict(evidence)),
        "disposition": disposition,
        "failure_reasons": reasons,
        "next_owner_instruction": "Owner continue next goal on PLAN" if disposition == "REUSE_ELIGIBLE" else "Owner destroy instance",
        "does_not_authorize": list(NO_ACTIONS),
        "launch_allowed": False,
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _validate_result(root, receipt)
    return receipt


def _validate_result(root: Path, receipt: Mapping[str, Any]) -> None:
    schema = _load_object(root / SCHEMA_PATH)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        raise InstanceDispositionV12Error(f"v12 result schema failure: {errors[0].message}")
    if receipt.get("receipt_sha256") != canonical_sha256({key: value for key, value in receipt.items() if key != "receipt_sha256"}):
        raise InstanceDispositionV12Error("v12 result self-hash mismatch")
    reasons = receipt.get("failure_reasons")
    if not isinstance(reasons, list) or reasons != sorted(set(reasons)):
        raise InstanceDispositionV12Error("v12 failure reasons must be sorted and unique")
    if (receipt.get("disposition") == "REUSE_ELIGIBLE") != (reasons == []):
        raise InstanceDispositionV12Error("v12 disposition does not match predicate outcome")
    assert_aggregate_only(receipt)


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-instance-disposition-v12")
    parser.add_argument("command", choices=("status", "evaluate"))
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--receipt-id", default="a1.2-instance-disposition-local-v12")
    args = parser.parse_args()
    if args.command == "status":
        result = current_status(args.repository_root)
    else:
        if args.evidence is None:
            parser.error("--evidence is required for evaluate")
        result = evaluate_payload(args.repository_root, _load_object(args.evidence), receipt_id=args.receipt_id)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
