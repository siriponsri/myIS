"""Fail-closed local whole-workload budget admission for A1.2 v12.

The evaluator receives only a sanitized quote, prior aggregate spend, and
whole-workload declaration from the Owner.  It does not contact a provider or
change any execution authorization.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only


REVISION_ID = "a1.2-whole-workload-budget-admission-v12"
ADMISSION_PATH = Path("control/armindex/a1.2/whole-workload-budget-admission.v12.json")
RESULT_SCHEMA_PATH = Path("schemas/armindex/a1.2-whole-workload-budget-admission-result.v12.json")
V11_BUDGET_PATH = Path("control/budgets/a1.2-common-screen-scientific-request-v11.json")
RESULT_SCHEMA = "myis.armindex-a1.2-whole-workload-budget-admission-result.v12"
EXPECTED_ARMS = ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")
EXPECTED_INPUT_KEYS = {"quote", "prior_spend_usd", "workload", "evaluated_at_utc"}
EXPECTED_QUOTE_KEYS = {
    "quote_observed_at_utc", "compute_hourly_rate_usd", "billing_granularity_seconds",
    "minimum_billable_seconds", "storage_fee_usd", "network_fee_usd",
    "platform_or_other_fee_usd", "tax_or_surcharge_usd",
}
EXPECTED_SPEND_KEYS = {"common_screen", "a1_total", "campaign"}
EXPECTED_WORKLOAD_KEYS = {"arm_ids", "expected_program_arm_runs", "partial_arm_admission"}
CLAIM_BOUNDARY = (
    "Local-only whole-workload budget arithmetic over an Owner-supplied sanitized quote; "
    "no provider contact, reservation, launch, adoption, measured retrieval, or scientific execution."
)


class WholeWorkloadBudgetAdmissionV12Error(ValueError):
    """Raised for malformed, unsafe, or non-frozen budget-admission inputs."""


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WholeWorkloadBudgetAdmissionV12Error(f"invalid JSON: {path.as_posix()}") from error
    if not isinstance(value, dict):
        raise WholeWorkloadBudgetAdmissionV12Error(f"JSON object required: {path.as_posix()}")
    return value


def _expect_mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise WholeWorkloadBudgetAdmissionV12Error(f"{label} must be an object")
    return value


def _decimal_nonnegative(value: object, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise WholeWorkloadBudgetAdmissionV12Error(f"{label} must be a known non-negative number")
    try:
        decimal = Decimal(str(value))
    except Exception as error:
        raise WholeWorkloadBudgetAdmissionV12Error(f"{label} must be a known non-negative number") from error
    if not decimal.is_finite() or decimal < 0:
        raise WholeWorkloadBudgetAdmissionV12Error(f"{label} must be a known non-negative number")
    return decimal


def _positive_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise WholeWorkloadBudgetAdmissionV12Error(f"{label} must be a positive integer")
    return value


def _utc_timestamp(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        raise WholeWorkloadBudgetAdmissionV12Error(f"{label} must be an RFC3339 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise WholeWorkloadBudgetAdmissionV12Error(f"{label} must be an RFC3339 UTC timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise WholeWorkloadBudgetAdmissionV12Error(f"{label} must be UTC")
    return parsed.astimezone(timezone.utc)


def _validate_admission_contract(root: Path) -> dict[str, Any]:
    contract = _load_object(root / ADMISSION_PATH)
    expected = {
        "schema_version": "myis.armindex-a1.2-whole-workload-budget-admission.v12",
        "status": "PENDING_LIVE_PROVIDER",
        "admitted": False,
        "launch_allowed": False,
        "whole_workload_required": True,
        "historical_quote_usable": False,
        "currency": "USD",
        "required_formula": "ceil(ttl_seconds/billing_granularity_seconds)*billing_granularity_seconds/3600*compute_hourly_rate_usd+storage_fee_usd+network_fee_usd+platform_or_other_fee_usd+tax_or_surcharge_usd",
    }
    if any(contract.get(key) != value for key, value in expected.items()):
        raise WholeWorkloadBudgetAdmissionV12Error("v12 admission contract drift")
    if contract.get("admission_sha256") != canonical_sha256(
        {key: value for key, value in contract.items() if key != "admission_sha256"}
    ):
        raise WholeWorkloadBudgetAdmissionV12Error("v12 admission contract self-hash mismatch")
    if contract.get("hard_stops_usd") != {"a1_total": 23, "campaign": 100, "common_screen": 18}:
        raise WholeWorkloadBudgetAdmissionV12Error("v12 hard-stop contract drift")
    if contract.get("window") != {"owner_ttl_hours": 6, "partial_arm_admission_allowed": False, "quote_max_age_seconds": 900}:
        raise WholeWorkloadBudgetAdmissionV12Error("v12 workload window drift")
    v11 = _expect_mapping(contract.get("v11_budget"), "v11_budget")
    if v11.get("uri") != V11_BUDGET_PATH.as_posix() or v11.get("file_sha256") != file_sha256(root / V11_BUDGET_PATH):
        raise WholeWorkloadBudgetAdmissionV12Error("v11 budget binding mismatch")
    return contract


def current_status(repository_root: Path) -> dict[str, Any]:
    """Validate the frozen local contract without a quote or provider action."""
    root = repository_root.resolve()
    contract = _validate_admission_contract(root)
    return {
        "status": contract["status"],
        "revision_id": REVISION_ID,
        "admission_file_sha256": file_sha256(root / ADMISSION_PATH),
        "launch_allowed": False,
        "adopted_for_execution": False,
        "provider_contact_allowed": False,
        "measured_runs": 0,
        "charged_usd": 0,
    }


def _validate_input_shape(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any], datetime]:
    if set(payload) != EXPECTED_INPUT_KEYS:
        raise WholeWorkloadBudgetAdmissionV12Error("budget input keys are incomplete or unsafe")
    assert_aggregate_only(payload)
    quote = _expect_mapping(payload["quote"], "quote")
    spend = _expect_mapping(payload["prior_spend_usd"], "prior_spend_usd")
    workload = _expect_mapping(payload["workload"], "workload")
    if set(quote) != EXPECTED_QUOTE_KEYS:
        raise WholeWorkloadBudgetAdmissionV12Error("quote must include every all-fee field and no unknown field")
    if set(spend) != EXPECTED_SPEND_KEYS:
        raise WholeWorkloadBudgetAdmissionV12Error("prior spend must include common_screen, a1_total, and campaign only")
    if set(workload) != EXPECTED_WORKLOAD_KEYS:
        raise WholeWorkloadBudgetAdmissionV12Error("workload declaration keys are incomplete or unsafe")
    evaluated_at = _utc_timestamp(payload["evaluated_at_utc"], "evaluated_at_utc")
    return quote, spend, workload, evaluated_at


def _quote_charge(quote: Mapping[str, Any], ttl_seconds: int) -> tuple[Decimal, int, Decimal]:
    observed_at = _utc_timestamp(quote["quote_observed_at_utc"], "quote_observed_at_utc")
    granularity = _positive_integer(quote["billing_granularity_seconds"], "billing_granularity_seconds")
    minimum = _positive_integer(quote["minimum_billable_seconds"], "minimum_billable_seconds")
    if minimum % granularity != 0:
        raise WholeWorkloadBudgetAdmissionV12Error("minimum_billable_seconds must align to billing granularity")
    rate = _decimal_nonnegative(quote["compute_hourly_rate_usd"], "compute_hourly_rate_usd")
    fees = sum(
        (_decimal_nonnegative(quote[field], field) for field in (
            "storage_fee_usd", "network_fee_usd", "platform_or_other_fee_usd", "tax_or_surcharge_usd"
        )),
        Decimal("0"),
    )
    billable_seconds = int((Decimal(ttl_seconds) / Decimal(granularity)).to_integral_value(rounding=ROUND_CEILING)) * granularity
    # The frozen formula is intentionally exact; minimum billing is an input validation property,
    # not an unlisted extra term, and the six-hour TTL is already at least the minimum.
    if billable_seconds < minimum:
        raise WholeWorkloadBudgetAdmissionV12Error("frozen TTL is below the quote minimum billable duration")
    charge = Decimal(billable_seconds) / Decimal(3600) * rate + fees
    return charge, billable_seconds, Decimal(observed_at.timestamp())


def _workload_reasons(workload: Mapping[str, Any]) -> list[str]:
    arms = workload.get("arm_ids")
    if not isinstance(arms, list) or tuple(arms) != EXPECTED_ARMS:
        return ["partial_or_noncanonical_arm_set"]
    if workload.get("partial_arm_admission") is not False:
        return ["partial_workload_admission_forbidden"]
    if workload.get("expected_program_arm_runs") != 25:
        return ["whole_workload_result_count_mismatch"]
    return []


def evaluate_payload(repository_root: Path, payload: Mapping[str, Any], *, receipt_id: str) -> dict[str, Any]:
    """Evaluate an Owner-supplied all-fee quote; all execution authorization stays false."""
    root = repository_root.resolve()
    contract = _validate_admission_contract(root)
    if not isinstance(payload, Mapping):
        raise WholeWorkloadBudgetAdmissionV12Error("budget admission input must be an object")
    if not isinstance(receipt_id, str) or not receipt_id.startswith("a1.2-whole-workload-budget-admission-") or not receipt_id.endswith("-v12"):
        raise WholeWorkloadBudgetAdmissionV12Error("invalid v12 receipt identifier")
    quote, spend, workload, evaluated_at = _validate_input_shape(payload)
    ttl_seconds = int(contract["window"]["owner_ttl_hours"]) * 3600
    charge, billable_seconds, observed_timestamp = _quote_charge(quote, ttl_seconds)
    quote_age = Decimal(evaluated_at.timestamp()) - observed_timestamp
    if quote_age < 0:
        raise WholeWorkloadBudgetAdmissionV12Error("quote_observed_at_utc is after evaluated_at_utc")
    prior = {key: _decimal_nonnegative(spend[key], f"prior_spend_usd.{key}") for key in EXPECTED_SPEND_KEYS}
    projected = {key: prior[key] + charge for key in EXPECTED_SPEND_KEYS}
    hard_stops = {"common_screen": Decimal("18"), "a1_total": Decimal("23"), "campaign": Decimal("100")}
    reasons = _workload_reasons(workload)
    if quote_age > Decimal(contract["window"]["quote_max_age_seconds"]):
        reasons.append("stale_quote")
    for key in ("common_screen", "a1_total", "campaign"):
        if projected[key] > hard_stops[key]:
            reasons.append(f"{key}_hard_stop_exceeded")
    reasons = sorted(set(reasons))
    admitted = not reasons
    body: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "receipt_id": receipt_id,
        "revision_id": REVISION_ID,
        "status": "PASS_BUDGET_ADMISSION_LOCKED" if admitted else "BLOCKED_BUDGET",
        "claim_boundary": CLAIM_BOUNDARY,
        "admitted": admitted,
        "admission_file_sha256": file_sha256(root / ADMISSION_PATH),
        "input_sha256": canonical_sha256(dict(payload)),
        "quote_age_seconds": float(quote_age),
        "billable_seconds": billable_seconds,
        "worst_case_ttl_charge_usd": float(charge),
        "projected_spend_usd": {key: float(projected[key]) for key in ("common_screen", "a1_total", "campaign")},
        "hard_stops_usd": {key: int(hard_stops[key]) for key in ("common_screen", "a1_total", "campaign")},
        "failure_reasons": reasons,
        "provider_contact_allowed": False,
        "launch_allowed": False,
        "adopted_for_execution": False,
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _validate_result(root, receipt)
    return receipt


def _validate_result(root: Path, receipt: Mapping[str, Any]) -> None:
    schema = _load_object(root / RESULT_SCHEMA_PATH)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda error: list(error.path))
    if errors:
        raise WholeWorkloadBudgetAdmissionV12Error(f"budget-admission result schema failure: {errors[0].message}")
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    if receipt.get("receipt_sha256") != canonical_sha256(body):
        raise WholeWorkloadBudgetAdmissionV12Error("budget-admission result self-hash mismatch")
    reasons = receipt.get("failure_reasons")
    if not isinstance(reasons, list) or reasons != sorted(set(reasons)):
        raise WholeWorkloadBudgetAdmissionV12Error("failure reasons must be sorted and unique")
    if bool(receipt.get("admitted")) != (receipt.get("status") == "PASS_BUDGET_ADMISSION_LOCKED" and reasons == []):
        raise WholeWorkloadBudgetAdmissionV12Error("admission status does not match failure reasons")
    assert_aggregate_only(receipt)


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-whole-workload-budget-admission-v12")
    parser.add_argument("command", choices=("status", "evaluate"))
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--input", type=Path)
    parser.add_argument("--receipt-id", default="a1.2-whole-workload-budget-admission-local-v12")
    args = parser.parse_args()
    if args.command == "status":
        result = current_status(args.repository_root)
    else:
        if args.input is None:
            parser.error("--input is required for evaluate")
        result = evaluate_payload(args.repository_root, _load_object(args.input), receipt_id=args.receipt_id)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
