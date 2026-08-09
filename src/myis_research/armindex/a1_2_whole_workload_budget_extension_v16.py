"""Evaluate the additive Owner-approved A1.2 budget and TTL extension."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import ROUND_CEILING, Decimal
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only

POLICY_PATH = Path(
    "control/armindex/a1.2/whole-workload-budget-extension.v16.json"
)
POLICY_SCHEMA_PATH = Path(
    "schemas/armindex/a1.2-whole-workload-budget-extension.v16.json"
)
RESULT_SCHEMA_PATH = Path(
    "schemas/armindex/a1.2-whole-workload-budget-extension-result.v16.json"
)
REVISION_ID = "a1.2-whole-workload-budget-extension-v16"
RESULT_SCHEMA = "myis.armindex-a1.2-whole-workload-budget-extension-result.v16"
EXPECTED_ARMS = ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")
EXPECTED_INPUT_KEYS = {"quote", "prior_spend_usd", "workload", "evaluated_at_utc"}
EXPECTED_QUOTE_KEYS = {
    "quote_observed_at_utc",
    "compute_hourly_rate_usd",
    "billing_granularity_seconds",
    "minimum_billable_seconds",
    "storage_fee_usd",
    "network_fee_usd",
    "platform_or_other_fee_usd",
    "tax_or_surcharge_usd",
}
EXPECTED_SPEND_KEYS = {"common_screen", "a1_total", "campaign"}
EXPECTED_WORKLOAD_KEYS = {
    "arm_ids",
    "expected_program_arm_runs",
    "partial_arm_admission",
}
CLAIM_BOUNDARY = (
    "Aggregate-only local evaluation of an Owner-supplied fresh all-fee quote "
    "against the approved A1.2 v16 limits; no provider contact, reservation, "
    "launch, adoption, measured retrieval, or scientific result."
)


class WholeWorkloadBudgetExtensionV16Error(ValueError):
    """Raised for malformed, unsafe, or drifted v16 budget inputs."""


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise WholeWorkloadBudgetExtensionV16Error(
            f"invalid JSON: {path.as_posix()}"
        ) from error
    if not isinstance(value, dict):
        raise WholeWorkloadBudgetExtensionV16Error(
            f"JSON object required: {path.as_posix()}"
        )
    return value


def _utc_timestamp(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        raise WholeWorkloadBudgetExtensionV16Error(
            f"{label} must be an RFC3339 UTC timestamp"
        )
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise WholeWorkloadBudgetExtensionV16Error(
            f"{label} must be an RFC3339 UTC timestamp"
        ) from error
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise WholeWorkloadBudgetExtensionV16Error(
            f"{label} must be UTC"
        )
    return parsed.astimezone(UTC)


def _decimal_nonnegative(value: object, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise WholeWorkloadBudgetExtensionV16Error(
            f"{label} must be a known non-negative number"
        )
    try:
        decimal = Decimal(str(value))
    except Exception as error:
        raise WholeWorkloadBudgetExtensionV16Error(
            f"{label} must be a known non-negative number"
        ) from error
    if not decimal.is_finite() or decimal < 0:
        raise WholeWorkloadBudgetExtensionV16Error(
            f"{label} must be a known non-negative number"
        )
    return decimal


def _positive_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise WholeWorkloadBudgetExtensionV16Error(
            f"{label} must be a positive integer"
        )
    return value


def _validate_policy(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    policy = _load_object(root / POLICY_PATH)
    schema = _load_object(root / POLICY_SCHEMA_PATH)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(policy),
        key=lambda error: list(error.path),
    )
    if errors:
        raise WholeWorkloadBudgetExtensionV16Error(
            f"v16 policy schema failure at {list(errors[0].path)}"
        )
    body = {key: value for key, value in policy.items() if key != "policy_sha256"}
    if policy.get("policy_sha256") != canonical_sha256(body):
        raise WholeWorkloadBudgetExtensionV16Error("v16 policy self-hash mismatch")
    if file_sha256(root / POLICY_PATH) is None:
        raise WholeWorkloadBudgetExtensionV16Error("v16 policy cannot be hashed")
    assert_aggregate_only(policy)
    if policy["authorization"] != {
        "provider_contact_allowed": False,
        "admitted": False,
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_retrieval_allowed": False,
    }:
        raise WholeWorkloadBudgetExtensionV16Error(
            "v16 authorization must remain locked"
        )
    if any(value != 0 for value in policy["preparation_counters"].values()):
        raise WholeWorkloadBudgetExtensionV16Error(
            "v16 preparation counters must remain zero"
        )
    return policy


def validate_contract(repository_root: Path) -> dict[str, Any]:
    """Validate the additive policy while leaving all execution gates closed."""

    return _validate_policy(repository_root)


def current_status(repository_root: Path) -> dict[str, Any]:
    policy = _validate_policy(repository_root)
    return {
        "status": policy["status"],
        "revision_id": REVISION_ID,
        "policy_sha256": policy["policy_sha256"],
        "hard_stops_usd": policy["approved_limits"]["hard_stops_usd"],
        "owner_ttl_hours": policy["approved_limits"]["owner_ttl_hours"],
        "ttl_basis": policy["approved_limits"]["ttl_basis"],
        "provider_contact_allowed": False,
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
        "charged_usd": 0,
    }


def _validate_input_shape(
    payload: Mapping[str, Any],
) -> tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any], datetime]:
    if set(payload) != EXPECTED_INPUT_KEYS:
        raise WholeWorkloadBudgetExtensionV16Error(
            "budget input keys are incomplete or unsafe"
        )
    assert_aggregate_only(payload)
    quote = payload["quote"]
    spend = payload["prior_spend_usd"]
    workload = payload["workload"]
    if not isinstance(quote, Mapping):
        raise WholeWorkloadBudgetExtensionV16Error("quote must be an object")
    if not isinstance(spend, Mapping):
        raise WholeWorkloadBudgetExtensionV16Error(
            "prior_spend_usd must be an object"
        )
    if not isinstance(workload, Mapping):
        raise WholeWorkloadBudgetExtensionV16Error("workload must be an object")
    if set(quote) != EXPECTED_QUOTE_KEYS:
        raise WholeWorkloadBudgetExtensionV16Error(
            "quote must include every all-fee field and no unknown field"
        )
    if set(spend) != EXPECTED_SPEND_KEYS:
        raise WholeWorkloadBudgetExtensionV16Error(
            "prior spend must include common_screen, a1_total, and campaign only"
        )
    if set(workload) != EXPECTED_WORKLOAD_KEYS:
        raise WholeWorkloadBudgetExtensionV16Error(
            "workload declaration keys are incomplete or unsafe"
        )
    evaluated_at = _utc_timestamp(
        payload["evaluated_at_utc"], "evaluated_at_utc"
    )
    return quote, spend, workload, evaluated_at


def _quote_charge(
    quote: Mapping[str, Any], ttl_seconds: int
) -> tuple[Decimal, int, Decimal]:
    observed_at = _utc_timestamp(
        quote["quote_observed_at_utc"], "quote_observed_at_utc"
    )
    granularity = _positive_integer(
        quote["billing_granularity_seconds"], "billing_granularity_seconds"
    )
    minimum = _positive_integer(
        quote["minimum_billable_seconds"], "minimum_billable_seconds"
    )
    if minimum % granularity != 0:
        raise WholeWorkloadBudgetExtensionV16Error(
            "minimum_billable_seconds must align to billing granularity"
        )
    rate = _decimal_nonnegative(
        quote["compute_hourly_rate_usd"], "compute_hourly_rate_usd"
    )
    fees = sum(
        (
            _decimal_nonnegative(quote[field], field)
            for field in (
                "storage_fee_usd",
                "network_fee_usd",
                "platform_or_other_fee_usd",
                "tax_or_surcharge_usd",
            )
        ),
        Decimal(0),
    )
    billable_seconds = (
        int(
            (
                Decimal(ttl_seconds) / Decimal(granularity)
            ).to_integral_value(rounding=ROUND_CEILING)
        )
        * granularity
    )
    if billable_seconds < minimum:
        raise WholeWorkloadBudgetExtensionV16Error(
            "approved TTL is below the quote minimum billable duration"
        )
    charge = Decimal(billable_seconds) / Decimal(3600) * rate + fees
    return charge, billable_seconds, Decimal(observed_at.timestamp())


def _workload_reasons(workload: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if workload.get("arm_ids") != list(EXPECTED_ARMS):
        reasons.append("partial_or_noncanonical_arm_set")
    if workload.get("partial_arm_admission") is not False:
        reasons.append("partial_workload_admission_forbidden")
    if workload.get("expected_program_arm_runs") != 25:
        reasons.append("whole_workload_result_count_mismatch")
    return reasons


def evaluate_payload(
    repository_root: Path,
    payload: Mapping[str, Any],
    *,
    receipt_id: str,
) -> dict[str, Any]:
    """Evaluate a sanitized fresh all-fee quote without authorizing execution."""

    root = repository_root.resolve()
    policy = _validate_policy(root)
    if not isinstance(payload, Mapping):
        raise WholeWorkloadBudgetExtensionV16Error(
            "budget admission input must be an object"
        )
    if (
        not isinstance(receipt_id, str)
        or not receipt_id.startswith("a1.2-whole-workload-budget-extension-")
        or not receipt_id.endswith("-v16")
    ):
        raise WholeWorkloadBudgetExtensionV16Error(
            "invalid v16 receipt identifier"
        )
    quote, spend, workload, evaluated_at = _validate_input_shape(payload)
    ttl_hours = int(policy["approved_limits"]["owner_ttl_hours"])
    ttl_seconds = ttl_hours * 3600
    charge, billable_seconds, observed_timestamp = _quote_charge(
        quote, ttl_seconds
    )
    quote_age = Decimal(evaluated_at.timestamp()) - observed_timestamp
    if quote_age < 0:
        raise WholeWorkloadBudgetExtensionV16Error(
            "quote_observed_at_utc is after evaluated_at_utc"
        )
    prior = {
        key: _decimal_nonnegative(spend[key], f"prior_spend_usd.{key}")
        for key in EXPECTED_SPEND_KEYS
    }
    projected = {key: prior[key] + charge for key in EXPECTED_SPEND_KEYS}
    hard_stops = {
        key: Decimal(str(value))
        for key, value in policy["approved_limits"]["hard_stops_usd"].items()
    }
    reasons = _workload_reasons(workload)
    if quote_age > Decimal(
        policy["approved_limits"]["quote_max_age_seconds"]
    ):
        reasons.append("stale_quote")
    reasons.extend(
        f"{key}_hard_stop_exceeded"
        for key in ("common_screen", "a1_total", "campaign")
        if projected[key] > hard_stops[key]
    )
    reasons = sorted(set(reasons))
    admitted = not reasons
    body: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "receipt_id": receipt_id,
        "revision_id": REVISION_ID,
        "status": "PASS_BUDGET_ADMISSION_LOCKED" if admitted else "BLOCKED_BUDGET",
        "claim_boundary": CLAIM_BOUNDARY,
        "admitted": admitted,
        "policy_sha256": policy["policy_sha256"],
        "input_sha256": canonical_sha256(dict(payload)),
        "quote_age_seconds": float(quote_age),
        "ttl_hours": ttl_hours,
        "billable_seconds": billable_seconds,
        "worst_case_ttl_charge_usd": float(charge),
        "projected_spend_usd": {
            key: float(projected[key])
            for key in ("common_screen", "a1_total", "campaign")
        },
        "hard_stops_usd": {
            key: int(hard_stops[key])
            for key in ("common_screen", "a1_total", "campaign")
        },
        "failure_reasons": reasons,
        "preparation_counters": {
            "charged_usd": 0,
            "gpu_scientific_runs": 0,
            "measured_runs": 0,
            "model_downloads": 0,
            "paid_api_calls": 0,
        },
        "provider_contact_allowed": False,
        "launch_allowed": False,
        "adopted_for_execution": False,
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _validate_result(root, receipt)
    return receipt


def _validate_result(root: Path, receipt: Mapping[str, Any]) -> None:
    schema = _load_object(root / RESULT_SCHEMA_PATH)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(receipt),
        key=lambda error: list(error.path),
    )
    if errors:
        raise WholeWorkloadBudgetExtensionV16Error(
            f"v16 result schema failure: {errors[0].message}"
        )
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    if receipt.get("receipt_sha256") != canonical_sha256(body):
        raise WholeWorkloadBudgetExtensionV16Error(
            "v16 result self-hash mismatch"
        )
    reasons = receipt.get("failure_reasons")
    if not isinstance(reasons, list) or reasons != sorted(set(reasons)):
        raise WholeWorkloadBudgetExtensionV16Error(
            "failure reasons must be sorted and unique"
        )
    if bool(receipt.get("admitted")) != (
        receipt.get("status") == "PASS_BUDGET_ADMISSION_LOCKED" and reasons == []
    ):
        raise WholeWorkloadBudgetExtensionV16Error(
            "admission status does not match failure reasons"
        )
    assert_aggregate_only(receipt)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="myis-a1.2-whole-workload-budget-extension-v16"
    )
    parser.add_argument("command", choices=("status", "evaluate"))
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--input", type=Path)
    parser.add_argument(
        "--receipt-id",
        default="a1.2-whole-workload-budget-extension-local-v16",
    )
    args = parser.parse_args()
    if args.command == "status":
        result = current_status(args.repository_root)
    else:
        if args.input is None:
            parser.error("--input is required for evaluate")
        result = evaluate_payload(
            args.repository_root,
            _load_object(args.input),
            receipt_id=args.receipt_id,
        )
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
