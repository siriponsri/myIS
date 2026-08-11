"""Build aggregate-safe, immutable A1.2 v16 live-admission receipts.

This module is deliberately outside the frozen execution bundle.  It performs
no provider, network, SSH, launch, or destruction action.  Its only input is a
strictly allowlisted sanitized JSON observation prepared by the Owner-local
orchestration layer.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_json, canonical_sha256
from ..protection import assert_aggregate_only

REVISION_ID = "a1.2-live-admission-v16"
FRESHNESS_SECONDS = 900
_HASH = re.compile(r"^[a-f0-9]{64}$")
_ATTEMPT = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
_SCHEMA_ROOT = Path("schemas/armindex")
_PROMOTION_POLICY_PATH = Path("control/armindex/a1.2/promotion-policy.v16.json")
_PROMOTION_POLICY_SCHEMA = _SCHEMA_ROOT / "a1.2-promotion-policy.v16.json"
_RECEIPT_FILES = {
    "provider_identity": "provider-identity.receipt.v16.json",
    "ssh_runtime": "ssh-runtime.receipt.v16.json",
    "management_dry_run": "management-dry-run.receipt.v16.json",
    "provider_admission": "provider-admission.receipt.v16.json",
    "execution_adoption": "execution-adoption.receipt.v16.json",
}
_SCHEMAS = {
    kind: _SCHEMA_ROOT / f"a1.2-live-{kind.replace('_', '-')}-receipt.v16.json"
    for kind in _RECEIPT_FILES
}
_BUDGET_SCHEMAS = {
    "myis.armindex-a1.2-whole-workload-budget-extension-result.v16": _SCHEMA_ROOT / "a1.2-whole-workload-budget-extension-result.v16.json",
    "myis.armindex-a1.2-whole-workload-budget-extension-result.v17": _SCHEMA_ROOT / "a1.2-whole-workload-budget-extension-result.v17.json",
}
_BUDGET_REVISIONS = {
    "myis.armindex-a1.2-whole-workload-budget-extension-result.v16": "a1.2-whole-workload-budget-extension-v16",
    "myis.armindex-a1.2-whole-workload-budget-extension-result.v17": "a1.2-whole-workload-budget-extension-v17",
}
_REQUIRED_BINDINGS = (
    "provider_identity",
    "all_fee_quote",
    "whole_workload_budget",
    "provider_management_authority",
    "watchdog_ttl",
    "ssh_identity",
    "runtime_identity",
    "scientific_request",
    "adoption_inputs",
    "transfer",
    "workload",
    "common_programs",
    "model_lockset",
    "protected_compiler",
    "image",
    "git_commit_tree_bundle",
    "evaluator",
    "split",
    "qrels_commitment",
    "token_map",
    "safe_return",
    "compiled_bindings_25_of_25",
    "physical_coverage_35",
    "promotion_policy",
)


class LiveAdmissionV16Error(ValueError):
    """Raised when sanitized live-admission evidence is incomplete or unsafe."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise LiveAdmissionV16Error(f"invalid JSON: {path.as_posix()}") from error
    if not isinstance(value, dict):
        raise LiveAdmissionV16Error(f"JSON object required: {path.as_posix()}")
    return value


def _hash(value: object, label: str) -> str:
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise LiveAdmissionV16Error(f"{label} must be a SHA-256 value")
    return value


def _utc(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        raise LiveAdmissionV16Error(f"{label} must be a UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise LiveAdmissionV16Error(f"{label} must be a UTC timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise LiveAdmissionV16Error(f"{label} must be UTC")
    return parsed.astimezone(UTC)


def _exact(value: object, keys: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise LiveAdmissionV16Error(f"{label} fields are incomplete or unsafe")
    return value


def _schema(root: Path, path: Path, value: Mapping[str, Any]) -> None:
    errors = sorted(
        Draft202012Validator(_load(root / path)).iter_errors(dict(value)),
        key=lambda error: list(error.path),
    )
    if errors:
        raise LiveAdmissionV16Error(f"receipt schema failure: {errors[0].message}")


def _self_hashed(value: Mapping[str, Any]) -> None:
    body = dict(value)
    actual = body.pop("receipt_sha256", None)
    if actual != canonical_sha256(body):
        raise LiveAdmissionV16Error("receipt self-hash mismatch")


def _validate_promotion_policy_binding(root: Path, bindings: Mapping[str, Any]) -> None:
    policy = _load(root / _PROMOTION_POLICY_PATH)
    _schema(root, _PROMOTION_POLICY_SCHEMA, policy)
    body = {key: item for key, item in policy.items() if key != "policy_sha256"}
    if policy.get("policy_sha256") != canonical_sha256(body):
        raise LiveAdmissionV16Error("promotion policy self-hash mismatch")
    if bindings["promotion_policy"] != policy["policy_sha256"]:
        raise LiveAdmissionV16Error("promotion policy differs from execution adoption")


def _spend(value: object, label: str) -> Mapping[str, float]:
    spend = _exact(value, {"common_screen", "a1_total", "campaign"}, label)
    parsed: dict[str, float] = {}
    for key, amount in spend.items():
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount < 0:
            raise LiveAdmissionV16Error(f"{label}.{key} must be a non-negative number")
        parsed[key] = float(amount)
    return parsed


def _validate_budget(root: Path, value: object, *, requires_v17: bool) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise LiveAdmissionV16Error("budget_admission must be an object")
    schema_version = value.get("schema_version")
    if not isinstance(schema_version, str):
        raise LiveAdmissionV16Error("budget receipt schema version is invalid")
    schema_path = _BUDGET_SCHEMAS.get(schema_version)
    if schema_path is None or value.get("revision_id") != _BUDGET_REVISIONS[schema_version]:
        raise LiveAdmissionV16Error("budget receipt is not a recognized v16/v17 result")
    if requires_v17 and schema_version != "myis.armindex-a1.2-whole-workload-budget-extension-result.v17":
        raise LiveAdmissionV16Error("fresh r14 admission requires the v17 budget receipt")
    _schema(root, schema_path, value)
    _self_hashed(value)
    if value.get("status") != "PASS_BUDGET_ADMISSION_LOCKED" or value.get("admitted") is not True:
        raise LiveAdmissionV16Error("whole-workload budget admission did not pass")
    if value.get("ttl_hours") != 40 or value.get("failure_reasons") != []:
        raise LiveAdmissionV16Error("budget receipt TTL or failure status drifted")
    projected = _spend(value.get("projected_spend_usd"), "budget_admission.projected_spend_usd")
    hard_stops = _spend(value.get("hard_stops_usd"), "budget_admission.hard_stops_usd")
    if any(projected[key] > hard_stops[key] for key in projected):
        raise LiveAdmissionV16Error("budget receipt projected spend exceeds its hard stop")
    if schema_version.endswith("v17"):
        prior = _spend(value.get("prior_attempt_spend_usd"), "budget_admission.prior_attempt_spend_usd")
        if value.get("prior_attempt_count") != 1:
            raise LiveAdmissionV16Error("v17 budget receipt must bind one prior destroyed attempt")
        charge = value.get("worst_case_ttl_charge_usd")
        if isinstance(charge, bool) or not isinstance(charge, (int, float)) or charge < 0:
            raise LiveAdmissionV16Error("v17 budget receipt charge is invalid")
        if any(abs(projected[key] - (prior[key] + float(charge))) > 1e-8 for key in projected):
            raise LiveAdmissionV16Error("v17 projected spend is not prior plus current charge")
    else:
        prior = {"common_screen": 0.0, "a1_total": 0.0, "campaign": 0.0}
    return value


def _validate_input(root: Path, value: Mapping[str, Any], *, now: datetime | None) -> dict[str, Any]:
    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise LiveAdmissionV16Error(str(error)) from error
    top = _exact(
        value,
        {"attempt_id", "provider_identity", "ssh_runtime", "management_dry_run", "budget_admission", "watchdog", "adoption_bindings"},
        "live admission input",
    )
    attempt_id = top["attempt_id"]
    if not isinstance(attempt_id, str) or _ATTEMPT.fullmatch(attempt_id) is None:
        raise LiveAdmissionV16Error("attempt_id is invalid")

    provider = _exact(top["provider_identity"], {
        "observed_at_utc", "observation_mode", "provider_label", "provider_authenticated",
        "provider_identity_sha256", "provider_evidence_sha256", "instance_identity_sha256",
        "host_identity_sha256", "machine_identity_sha256", "gpu_uuid_set_sha256", "provider_status",
        "gpu_count", "gpu_model", "vram_mib_each", "platform", "all_fee_quote_sha256",
        "whole_workload_budget_input_sha256",
    }, "provider_identity")
    if provider["observation_mode"] not in {"AUTHENTICATED_CLI", "OWNER_DASHBOARD_SSH"}:
        raise LiveAdmissionV16Error("provider observation mode is invalid")
    if provider["provider_status"] != "RUNNING_VERIFIED" or provider["provider_label"] != "Vast":
        raise LiveAdmissionV16Error("provider identity is not running/verified Vast")
    if provider["provider_authenticated"] is not (provider["observation_mode"] == "AUTHENTICATED_CLI"):
        raise LiveAdmissionV16Error("provider authentication does not match observation mode")
    if (provider["gpu_count"], provider["gpu_model"], provider["vram_mib_each"], provider["platform"]) != (4, "NVIDIA GeForce RTX 3090", 24576, "linux/amd64"):
        raise LiveAdmissionV16Error("provider GPU or platform identity drifted")
    for key in ("provider_identity_sha256", "provider_evidence_sha256", "instance_identity_sha256", "host_identity_sha256", "machine_identity_sha256", "gpu_uuid_set_sha256", "all_fee_quote_sha256", "whole_workload_budget_input_sha256"):
        _hash(provider[key], f"provider_identity.{key}")

    ssh = _exact(top["ssh_runtime"], {
        "observed_at_utc", "instance_identity_sha256", "host_identity_sha256", "ssh_host_key_sha256",
        "gpu_uuid_set_sha256", "platform", "python", "torch", "cuda", "gpu_count", "gpu_model",
        "vram_mib_each", "image_reference", "image_manifest_digest", "runtime_evidence_sha256",
    }, "ssh_runtime")
    if (ssh["platform"], ssh["python"], ssh["torch"], ssh["cuda"], ssh["gpu_count"], ssh["gpu_model"], ssh["vram_mib_each"]) != ("linux/amd64", "3.11", "2.6.0+cu118", "11.8", 4, "NVIDIA GeForce RTX 3090", 24576):
        raise LiveAdmissionV16Error("SSH runtime identity drifted")
    if ssh["image_reference"] != "pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime" or ssh["image_manifest_digest"] != "sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20":
        raise LiveAdmissionV16Error("SSH runtime image identity drifted")
    for key in ("instance_identity_sha256", "host_identity_sha256", "ssh_host_key_sha256", "gpu_uuid_set_sha256", "runtime_evidence_sha256"):
        _hash(ssh[key], f"ssh_runtime.{key}")
    for key in ("instance_identity_sha256", "host_identity_sha256", "gpu_uuid_set_sha256"):
        if ssh[key] != provider[key]:
            raise LiveAdmissionV16Error("provider and SSH identity do not match")

    management = _exact(top["management_dry_run"], {
        "observed_at_utc", "instance_identity_sha256", "provider_identity_sha256", "status",
        "provider_destroy_capability", "provider_action_performed", "destroy_command_template_sha256",
        "management_evidence_sha256",
    }, "management_dry_run")
    expected_management = "READY_NOT_EXECUTED" if provider["provider_authenticated"] else "OWNER_MANUAL_DASHBOARD_DESTROY_READY"
    if management["status"] != expected_management or management["provider_destroy_capability"] != expected_management or management["provider_action_performed"] is not False:
        raise LiveAdmissionV16Error("management dry-run authority is invalid")
    for key in ("instance_identity_sha256", "provider_identity_sha256", "destroy_command_template_sha256", "management_evidence_sha256"):
        _hash(management[key], f"management_dry_run.{key}")
    if management["instance_identity_sha256"] != provider["instance_identity_sha256"] or management["provider_identity_sha256"] != provider["provider_identity_sha256"]:
        raise LiveAdmissionV16Error("management identity does not match provider")

    watchdog = _exact(top["watchdog"], {"observed_at_utc", "status", "instance_identity_sha256", "owner_ttl_hours", "ttl_deadline_utc", "watchdog_receipt_sha256"}, "watchdog")
    if watchdog["status"] != "PASS" or watchdog["owner_ttl_hours"] != 40:
        raise LiveAdmissionV16Error("watchdog or TTL is not ready")
    watchdog_observed = _utc(watchdog["observed_at_utc"], "watchdog.observed_at_utc")
    deadline = _utc(watchdog["ttl_deadline_utc"], "watchdog.ttl_deadline_utc")
    if deadline <= watchdog_observed or deadline - watchdog_observed > timedelta(hours=40):
        raise LiveAdmissionV16Error("watchdog TTL deadline is unsafe")
    for key in ("instance_identity_sha256", "watchdog_receipt_sha256"):
        _hash(watchdog[key], f"watchdog.{key}")
    if watchdog["instance_identity_sha256"] != provider["instance_identity_sha256"]:
        raise LiveAdmissionV16Error("watchdog identity does not match provider")

    bindings = _exact(top["adoption_bindings"], set(_REQUIRED_BINDINGS), "adoption_bindings")
    for key in _REQUIRED_BINDINGS:
        _hash(bindings[key], f"adoption_bindings.{key}")
    _validate_promotion_policy_binding(root, bindings)
    budget = _validate_budget(root, top["budget_admission"], requires_v17=attempt_id.endswith("-r14"))
    if budget["input_sha256"] != provider["whole_workload_budget_input_sha256"]:
        raise LiveAdmissionV16Error("provider budget binding does not match budget receipt")
    prior_spend = (
        _spend(budget["prior_attempt_spend_usd"], "budget_admission.prior_attempt_spend_usd")
        if budget["schema_version"].endswith("v17")
        else {"common_screen": 0.0, "a1_total": 0.0, "campaign": 0.0}
    )
    live_binding_values = {
        "provider_identity": provider["provider_identity_sha256"],
        "all_fee_quote": provider["all_fee_quote_sha256"],
        "whole_workload_budget": budget["receipt_sha256"],
        "provider_management_authority": management["management_evidence_sha256"],
        "watchdog_ttl": watchdog["watchdog_receipt_sha256"],
        "ssh_identity": ssh["ssh_host_key_sha256"],
        "runtime_identity": ssh["runtime_evidence_sha256"],
    }
    if any(bindings[key] != expected for key, expected in live_binding_values.items()):
        raise LiveAdmissionV16Error("live adoption binding does not match observed evidence")

    timestamps = [
        _utc(provider["observed_at_utc"], "provider_identity.observed_at_utc"),
        _utc(ssh["observed_at_utc"], "ssh_runtime.observed_at_utc"),
        _utc(management["observed_at_utc"], "management_dry_run.observed_at_utc"),
        _utc(watchdog["observed_at_utc"], "watchdog.observed_at_utc"),
    ]
    if (max(timestamps) - min(timestamps)).total_seconds() > FRESHNESS_SECONDS:
        raise LiveAdmissionV16Error("live observations are not from one fresh admission window")
    evaluated_at = now or datetime.now(UTC)
    if evaluated_at.tzinfo is None:
        raise LiveAdmissionV16Error("now must be timezone-aware")
    if any((evaluated_at.astimezone(UTC) - observed).total_seconds() < 0 or (evaluated_at.astimezone(UTC) - observed).total_seconds() > FRESHNESS_SECONDS for observed in timestamps):
        raise LiveAdmissionV16Error("live observation is stale or from the future")
    return {"attempt_id": attempt_id, "provider": dict(provider), "ssh": dict(ssh), "management": dict(management), "watchdog": dict(watchdog), "budget": dict(budget), "bindings": dict(bindings), "budget_prior_spend_usd": prior_spend}


def _receipt(kind: str, body: Mapping[str, Any]) -> dict[str, Any]:
    return {**body, "receipt_sha256": canonical_sha256(dict(body))}


def build_receipts(repository_root: Path, payload: Mapping[str, Any], *, now: datetime | None = None) -> dict[str, dict[str, Any]]:
    """Build five linked receipts from a sanitized, current Owner-local input."""

    verified = _validate_input(repository_root.resolve(), payload, now=now)
    attempt_id = verified["attempt_id"]
    provider = verified["provider"]
    ssh = verified["ssh"]
    management = verified["management"]
    watchdog = verified["watchdog"]
    budget = verified["budget"]
    prior_spend = verified["budget_prior_spend_usd"]
    source_hashes = {
        "provider_identity_input_sha256": canonical_sha256(provider),
        "ssh_runtime_input_sha256": canonical_sha256(ssh),
        "management_dry_run_input_sha256": canonical_sha256(management),
    }
    provider_receipt = _receipt("provider_identity", {
        "schema_version": "myis.armindex-a1.2-live-provider-identity-receipt.v16", "receipt_kind": "provider_identity", "receipt_id": f"{attempt_id}-provider-identity-v16", "revision_id": REVISION_ID,
        "attempt_id": attempt_id, "status": "PASS_PROVIDER_IDENTITY", "claim_boundary": "Aggregate-safe live provider identity observation only; no provider payload, credential, launch, retrieval, or destruction action is retained or performed.", "identity": provider, **source_hashes,
    })
    ssh_receipt = _receipt("ssh_runtime", {
        "schema_version": "myis.armindex-a1.2-live-ssh-runtime-receipt.v16", "receipt_kind": "ssh_runtime", "receipt_id": f"{attempt_id}-ssh-runtime-v16", "revision_id": REVISION_ID,
        "attempt_id": attempt_id, "status": "PASS_SSH_RUNTIME", "claim_boundary": "Aggregate-safe SSH and runtime identity observation only; no endpoint, host name, credential, protected input, launch, retrieval, or provider action is retained or performed.", "runtime": ssh, "provider_identity_receipt_sha256": provider_receipt["receipt_sha256"], "ssh_runtime_input_sha256": source_hashes["ssh_runtime_input_sha256"],
    })
    management_receipt = _receipt("management_dry_run", {
        "schema_version": "myis.armindex-a1.2-live-management-dry-run-receipt.v16", "receipt_kind": "management_dry_run", "receipt_id": f"{attempt_id}-management-dry-run-v16", "revision_id": REVISION_ID,
        "attempt_id": attempt_id, "status": "PASS_MANAGEMENT_DRY_RUN", "claim_boundary": "Aggregate-safe non-destructive management-readiness evidence only; no destroy, launch, reservation, credential, raw provider payload, or scientific action is performed.", "management": management, "provider_identity_receipt_sha256": provider_receipt["receipt_sha256"], "management_dry_run_input_sha256": source_hashes["management_dry_run_input_sha256"],
    })
    provider_admission = _receipt("provider_admission", {
        "schema_version": "myis.armindex-a1.2-live-provider-admission-receipt.v16", "receipt_kind": "provider_admission", "receipt_id": f"{attempt_id}-provider-admission-v16", "revision_id": REVISION_ID,
        "attempt_id": attempt_id, "status": "PASS_PROVIDER_ADMISSION", "claim_boundary": "Aggregate-safe provider admission for the frozen A1.2 workload only. It contains no raw provider payload, credential, protected query data, retrieval output, launch, or destruction action.", "provider_identity_receipt_sha256": provider_receipt["receipt_sha256"], "ssh_runtime_receipt_sha256": ssh_receipt["receipt_sha256"], "management_dry_run_receipt_sha256": management_receipt["receipt_sha256"], "budget_admission_receipt_sha256": budget["receipt_sha256"], "budget_revision_id": budget["revision_id"], "watchdog_receipt_sha256": watchdog["watchdog_receipt_sha256"], "budget_status": budget["status"], "budget_admitted": True, "prior_attempt_count": budget.get("prior_attempt_count", 0), "prior_attempt_spend_usd": prior_spend, "current_worst_case_ttl_charge_usd": budget["worst_case_ttl_charge_usd"], "projected_spend_usd": budget["projected_spend_usd"], "hard_stops_usd": budget["hard_stops_usd"], "owner_ttl_hours": 40, "provider_destroy_capability": management["provider_destroy_capability"], "provider_admission_receipt_pass": True,
    })
    adoption = _receipt("execution_adoption", {
        "schema_version": "myis.armindex-a1.2-live-execution-adoption-receipt.v16", "receipt_kind": "execution_adoption", "receipt_id": f"{attempt_id}-execution-adoption-v16", "revision_id": REVISION_ID,
        "attempt_id": attempt_id, "status": "PASS_EXECUTION_ADOPTION", "claim_boundary": "Aggregate-safe execution adoption for one immutable frozen A1.2 attempt only. It does not change scientific semantics or retain credentials, provider payloads, protected inputs, rankings, or per-query outcomes.", "provider_admission_receipt_sha256": provider_admission["receipt_sha256"], "ssh_runtime_receipt_sha256": ssh_receipt["receipt_sha256"], "management_dry_run_receipt_sha256": management_receipt["receipt_sha256"], "watchdog_receipt_sha256": watchdog["watchdog_receipt_sha256"], "adoption_bindings": verified["bindings"], "adoption_binding_set_sha256": canonical_sha256(verified["bindings"]), "provider_admission_receipt_pass": True, "execution_adoption_receipt_pass": True, "launch_allowed": True, "adopted_for_execution": True, "measured_retrieval_allowed": True, "selection_allowed": False, "final_allowed": False, "paid_api_allowed": False,
    })
    receipts = {"provider_identity": provider_receipt, "ssh_runtime": ssh_receipt, "management_dry_run": management_receipt, "provider_admission": provider_admission, "execution_adoption": adoption}
    validate_receipt_set(repository_root, receipts)
    return receipts


def validate_receipt_set(repository_root: Path, receipts: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Validate receipt schemas, canonical self-hashes, and cross-receipt links."""

    root = repository_root.resolve()
    if set(receipts) != set(_RECEIPT_FILES):
        raise LiveAdmissionV16Error("receipt set is incomplete or contains unknown receipts")
    for kind, receipt in receipts.items():
        if not isinstance(receipt, Mapping):
            raise LiveAdmissionV16Error(f"{kind} receipt must be an object")
        try:
            assert_aggregate_only(receipt)
        except ValueError as error:
            raise LiveAdmissionV16Error(str(error)) from error
        _schema(root, _SCHEMAS[kind], receipt)
        _self_hashed(receipt)
    attempt_ids = {receipt["attempt_id"] for receipt in receipts.values()}
    if len(attempt_ids) != 1:
        raise LiveAdmissionV16Error("receipts span multiple attempts")
    provider = receipts["provider_identity"]
    ssh = receipts["ssh_runtime"]
    management = receipts["management_dry_run"]
    admission = receipts["provider_admission"]
    adoption = receipts["execution_adoption"]
    if ssh["provider_identity_receipt_sha256"] != provider["receipt_sha256"] or management["provider_identity_receipt_sha256"] != provider["receipt_sha256"]:
        raise LiveAdmissionV16Error("provider identity receipt linkage failed")
    if any(admission[field] != receipts[key]["receipt_sha256"] for field, key in (("provider_identity_receipt_sha256", "provider_identity"), ("ssh_runtime_receipt_sha256", "ssh_runtime"), ("management_dry_run_receipt_sha256", "management_dry_run"))):
        raise LiveAdmissionV16Error("provider admission receipt linkage failed")
    if any(adoption[field] != receipts[key]["receipt_sha256"] for field, key in (("provider_admission_receipt_sha256", "provider_admission"), ("ssh_runtime_receipt_sha256", "ssh_runtime"), ("management_dry_run_receipt_sha256", "management_dry_run"))):
        raise LiveAdmissionV16Error("execution adoption receipt linkage failed")
    if adoption["adoption_binding_set_sha256"] != canonical_sha256(adoption["adoption_bindings"]):
        raise LiveAdmissionV16Error("execution adoption binding set hash mismatch")
    return {"status": "PASS", "attempt_id": next(iter(attempt_ids)), "receipt_sha256": {kind: receipt["receipt_sha256"] for kind, receipt in sorted(receipts.items())}, "provider_admission": admission["status"], "execution_adoption": adoption["status"]}


def _write_immutable(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = canonical_json(dict(value)) + "\n"
    if path.exists():
        if path.is_symlink() or path.read_text(encoding="utf-8") != text:
            raise LiveAdmissionV16Error(f"immutable receipt differs: {path.name}")
        return
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_receipts(repository_root: Path, output_dir: Path, receipts: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Write only an immutable external receipt set, never into the repository."""

    root = repository_root.resolve()
    target = output_dir.resolve()
    if target == root or target.is_relative_to(root):
        raise LiveAdmissionV16Error("live receipts must remain outside the repository")
    result = validate_receipt_set(root, receipts)
    for kind, filename in _RECEIPT_FILES.items():
        _write_immutable(target / filename, receipts[kind])
    return result


def read_receipts(repository_root: Path, receipt_dir: Path) -> dict[str, dict[str, Any]]:
    root, directory = repository_root.resolve(), receipt_dir.resolve()
    if directory == root or directory.is_relative_to(root):
        raise LiveAdmissionV16Error("live receipts must be read from an external receipt directory")
    receipts = {kind: _load(directory / filename) for kind, filename in _RECEIPT_FILES.items()}
    validate_receipt_set(root, receipts)
    return receipts


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-live-admission-v16")
    parser.add_argument("command", choices=("build", "validate"))
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--input", type=Path)
    parser.add_argument("--receipt-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build":
        if args.input is None:
            parser.error("build requires --input")
        receipts = build_receipts(args.repository_root, _load(args.input))
        result = write_receipts(args.repository_root, args.receipt_dir, receipts)
    else:
        result = validate_receipt_set(args.repository_root, read_receipts(args.repository_root, args.receipt_dir))
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
