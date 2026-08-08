"""A1.2 v12 local-only watchdog/provider-destroy dry-run validator.

The module deliberately has no subprocess, network, SSH, or provider SDK
dependency.  A PASS validates a template and a simulated TTL event, never a
provider account, command availability, or destruction capability.
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


REVISION_ID = "a1.2-watchdog-provider-destroy-dry-run-v12"
POLICY_PATH = Path(
    "control/armindex/a1.2/watchdog-provider-destroy-dry-run-contract.v12.json"
)
SCHEMA_PATH = Path(
    "schemas/armindex/a1.2-watchdog-provider-destroy-dry-run-result.v12.json"
)
RESULT_SCHEMA = "myis.armindex-a1.2-watchdog-provider-destroy-dry-run-result.v12"
POLICY_SCHEMA = "myis.armindex-a1.2-watchdog-provider-destroy-dry-run-contract.v12"
NO_ACTIONS = [
    "provider_contact",
    "provider_cli",
    "provider_destroy",
    "ssh",
    "launch_allowed",
    "adopted_for_execution",
    "measured_retrieval",
    "optimization",
    "selection",
    "final",
    "paid_api_work",
    "model_weight_changes",
]
_HASH = re.compile(r"^[a-f0-9]{64}$")
_ABSOLUTE_PATH = re.compile(r"(?:[A-Za-z]:\\|/Users/|/home/|\\\\[^\\]+\\)")
_FORBIDDEN = re.compile(
    r'"(?:provider_instance_id|instance_id|credential|credentials|private_key|qrels|query_ids|membership)"\s*:',
    re.IGNORECASE,
)
_INPUT_KEYS = {
    "target_instance_identity_sha256",
    "ttl_seconds",
    "heartbeat_stale_seconds",
    "simulated_elapsed_seconds",
    "simulated_heartbeat_age_seconds",
    "expected_trigger",
    "command_template_tokens",
}


class WatchdogDestroyDryRunV12Error(ValueError):
    """Raised when a local dry-run input or result is invalid."""


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WatchdogDestroyDryRunV12Error(
            f"invalid JSON: {path.as_posix()}"
        ) from error
    if not isinstance(value, dict):
        raise WatchdogDestroyDryRunV12Error(f"JSON object required: {path.as_posix()}")
    return value


def _nonnegative(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) >= 0
    )


def _validate_policy(policy: Mapping[str, Any]) -> None:
    if (
        policy.get("schema_version") != POLICY_SCHEMA
        or policy.get("policy_id") != REVISION_ID
    ):
        raise WatchdogDestroyDryRunV12Error("v12 watchdog policy identity mismatch")
    if policy.get("status") != "PENDING_LIVE_PROVIDER":
        raise WatchdogDestroyDryRunV12Error(
            "v12 watchdog policy must remain pending live provider"
        )
    if policy.get("actual_provider_destroy_capability") != "PENDING_LIVE_PROVIDER":
        raise WatchdogDestroyDryRunV12Error(
            "v12 watchdog policy cannot claim provider capability"
        )
    if (
        policy.get("does_not_authorize") != NO_ACTIONS
        or policy.get("launch_allowed") is not False
    ):
        raise WatchdogDestroyDryRunV12Error(
            "v12 watchdog policy authorization boundary mismatch"
        )


def current_status(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    policy = _load_object(root / POLICY_PATH)
    _validate_policy(policy)
    return {
        "status": "PENDING_LIVE_PROVIDER",
        "actual_provider_destroy_capability": "PENDING_LIVE_PROVIDER",
        "policy_id": REVISION_ID,
        "policy_file_sha256": file_sha256(root / POLICY_PATH),
        "provider_action_performed": False,
    }


def _validate_input(evidence: Mapping[str, Any], policy: Mapping[str, Any]) -> None:
    if set(evidence) != _INPUT_KEYS:
        raise WatchdogDestroyDryRunV12Error(
            "watchdog dry-run input keys are incomplete or unsafe"
        )
    assert_aggregate_only(evidence)
    serialized = json.dumps(evidence, ensure_ascii=True, sort_keys=True)
    if _ABSOLUTE_PATH.search(serialized) or _FORBIDDEN.search(serialized):
        raise WatchdogDestroyDryRunV12Error(
            "watchdog dry-run input contains forbidden material"
        )
    if not isinstance(
        evidence.get("target_instance_identity_sha256"), str
    ) or not _HASH.fullmatch(str(evidence["target_instance_identity_sha256"])):
        raise WatchdogDestroyDryRunV12Error(
            "sanitized target identity hash is required"
        )
    if not all(
        _nonnegative(evidence.get(field))
        for field in (
            "ttl_seconds",
            "heartbeat_stale_seconds",
            "simulated_elapsed_seconds",
            "simulated_heartbeat_age_seconds",
        )
    ):
        raise WatchdogDestroyDryRunV12Error(
            "watchdog timing values must be finite and nonnegative"
        )
    if (
        not 60 <= float(evidence["ttl_seconds"]) <= 86400
        or not 30 <= float(evidence["heartbeat_stale_seconds"]) <= 3600
    ):
        raise WatchdogDestroyDryRunV12Error(
            "watchdog timing values are outside the contract bounds"
        )
    if evidence.get("command_template_tokens") != policy.get(
        "allowed_command_template_tokens"
    ):
        raise WatchdogDestroyDryRunV12Error(
            "destroy command template is not the sanitized frozen template"
        )
    if evidence.get("expected_trigger") != "ttl_expired":
        raise WatchdogDestroyDryRunV12Error("v12 requires a TTL-expired simulation")
    if float(evidence["simulated_elapsed_seconds"]) < float(evidence["ttl_seconds"]):
        raise WatchdogDestroyDryRunV12Error("simulated TTL has not expired")


def evaluate_payload(
    repository_root: Path, evidence: Mapping[str, Any], *, receipt_id: str
) -> dict[str, Any]:
    """Validate one simulated TTL trigger without invoking any external process."""
    root = repository_root.resolve()
    policy = _load_object(root / POLICY_PATH)
    _validate_policy(policy)
    if not isinstance(evidence, Mapping):
        raise WatchdogDestroyDryRunV12Error(
            "watchdog dry-run evidence must be an object"
        )
    _validate_input(evidence, policy)
    if not isinstance(receipt_id, str) or not re.fullmatch(
        r"a1\.2-watchdog-provider-destroy-dry-run-[a-z0-9._-]+-v12", receipt_id
    ):
        raise WatchdogDestroyDryRunV12Error(
            "invalid v12 watchdog dry-run receipt identifier"
        )
    command_tokens = list(evidence["command_template_tokens"])
    body: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "receipt_id": receipt_id,
        "revision_id": REVISION_ID,
        "status": "PASS",
        "claim_boundary": str(policy["claim_boundary"]),
        "policy_id": REVISION_ID,
        "policy_file_sha256": file_sha256(root / POLICY_PATH),
        "mode": "owner_local_dry_run",
        "target_instance_identity_sha256": evidence["target_instance_identity_sha256"],
        "command_template_sha256": canonical_sha256(command_tokens),
        "destroy_command_validated": True,
        "ttl_trigger_simulated": True,
        "simulated_trigger": "ttl_expired",
        "provider_action_performed": False,
        "actual_provider_destroy_capability": "PENDING_LIVE_PROVIDER",
        "guest_poweroff_is_provider_destruction": False,
        "actual_destroy_receipt_required": True,
        "does_not_authorize": list(NO_ACTIONS),
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _validate_result(root, receipt)
    return receipt


def write_result(
    repository_root: Path,
    evidence: Mapping[str, Any],
    *,
    receipt_id: str,
    output: Path,
) -> dict[str, Any]:
    """Write one immutable dry-run receipt outside the repository."""

    root = repository_root.resolve()
    destination = output.resolve()
    if destination.is_relative_to(root):
        raise WatchdogDestroyDryRunV12Error(
            "watchdog dry-run receipt must remain outside the repository"
        )
    receipt = evaluate_payload(root, evidence, receipt_id=receipt_id)
    serialized = (
        json.dumps(receipt, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + "\n"
    )
    if destination.exists() and destination.read_text(encoding="utf-8") != serialized:
        raise WatchdogDestroyDryRunV12Error(
            "immutable watchdog dry-run receipt already exists with different bytes"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        destination.write_text(serialized, encoding="utf-8", newline="")
    return receipt


def _validate_result(root: Path, receipt: Mapping[str, Any]) -> None:
    schema = _load_object(root / SCHEMA_PATH)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(receipt),
        key=lambda error: list(error.path),
    )
    if errors:
        raise WatchdogDestroyDryRunV12Error(
            f"v12 watchdog result schema failure: {errors[0].message}"
        )
    if receipt.get("receipt_sha256") != canonical_sha256(
        {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    ):
        raise WatchdogDestroyDryRunV12Error("v12 watchdog result self-hash mismatch")
    assert_aggregate_only(receipt)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="myis-a1.2-watchdog-provider-destroy-dry-run-v12"
    )
    parser.add_argument("command", choices=("status", "evaluate"))
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--evidence", type=Path)
    parser.add_argument(
        "--receipt-id", default="a1.2-watchdog-provider-destroy-dry-run-local-v12"
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = current_status(args.repository_root)
    if args.command == "evaluate":
        if args.evidence is None:
            parser.error("--evidence is required for evaluate")
        evidence = _load_object(args.evidence)
        if args.output is None:
            result = evaluate_payload(
                args.repository_root, evidence, receipt_id=args.receipt_id
            )
        else:
            result = write_result(
                args.repository_root,
                evidence,
                receipt_id=args.receipt_id,
                output=args.output,
            )
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
