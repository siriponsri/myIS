"""CPU-only validation for the Owner-local A1.2 launch preflight.

The runner accepts only aggregate-safe metadata from an Owner-managed staging
directory.  It never copies model bytes into the repository, never reads
credentials, and never contacts a provider.  Missing Owner evidence is a
normal, fail-closed result rather than an inferred pass.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from ..kernel.canonical import canonical_sha256, file_sha256


SCHEMA_VERSION = "myis.armindex-a1.2-owner-local-preflight.v1"
CONTROL_ROOT = Path("control/armindex/a1.2")
DENSE_ARMS = ("ARM-02", "ARM-03", "ARM-04", "ARM-05")
SHA_RE = re.compile(r"^[a-f0-9]{64}$")
SHA_LINE_RE = re.compile(r"^([a-f0-9]{64})  (.+)$")
FORBIDDEN_MARKERS = (
    "credential",
    "password",
    "secret",
    "token_value",
    "api_key",
    "private_key",
    "qrel",
    "ranking",
    "per_query",
    "protected_payload",
)


class A12PreflightError(ValueError):
    """Raised for malformed or unsafe Owner-local metadata."""


@dataclass(frozen=True)
class PreflightResult:
    status: str
    receipt: dict[str, Any]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except (OSError, json.JSONDecodeError) as exc:
        raise A12PreflightError(f"invalid JSON metadata: {path.name}") from exc
    if not isinstance(value, dict):
        raise A12PreflightError(f"metadata must be an object: {path.name}")
    return value


def _safe_metadata(value: Any, path: str = "root") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).lower()
            if any(marker in key_text for marker in FORBIDDEN_MARKERS):
                raise A12PreflightError(f"forbidden metadata key: {path}.{key}")
            _safe_metadata(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _safe_metadata(child, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in FORBIDDEN_MARKERS):
            raise A12PreflightError(f"forbidden metadata value at {path}")
        if "\\" in value or value.startswith("/"):
            raise A12PreflightError(f"absolute path is forbidden at {path}")


def _load_control(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    lockset = _read_json(root / CONTROL_ROOT / "model-lockset.v1.json")
    checklist = _read_json(root / CONTROL_ROOT / "launch-checklist.v1.json")
    shutdown = _read_json(root / CONTROL_ROOT / "shutdown-plan.v1.json")
    contract = _read_json(root / CONTROL_ROOT / "execution-contract.v1.json")
    if contract.get("launch_allowed") is not False or contract.get("scientific_authority") is not False:
        raise A12PreflightError("A1.2 contract is not launch-locked")
    if checklist.get("launch_ready") is not False:
        raise A12PreflightError("A1.2 checklist is unexpectedly launch-ready")
    return lockset, checklist, shutdown, contract


def _canonical_binding(value: Mapping[str, Any], field: str) -> str:
    body = dict(value)
    body.pop(field, None)
    return canonical_sha256(body)


def _validate_bindings(root: Path, lockset: Mapping[str, Any], checklist: Mapping[str, Any], shutdown: Mapping[str, Any], contract: Mapping[str, Any]) -> dict[str, str]:
    paths = {
        "budget_profile_sha256": root / "control/budgets/a1.2-common-screen-v1.json",
        "envelope_sha256": root / "control/execution-envelope-a1.2-v1.yaml",
        "inputs_sha256": root / CONTROL_ROOT / "scaffold-inputs.v1.yaml",
        "lockset_sha256": root / CONTROL_ROOT / "model-lockset.v1.json",
        "shutdown_plan_sha256": root / CONTROL_ROOT / "shutdown-plan.v1.json",
    }
    actual = {
        "budget_profile_sha256": _read_json(paths["budget_profile_sha256"]).get("budget_profile_sha256"),
        "envelope_sha256": _yaml_binding(paths["envelope_sha256"], "envelope_sha256"),
        "inputs_sha256": _yaml_binding(paths["inputs_sha256"], "inputs_sha256"),
        "lockset_sha256": lockset.get("lockset_sha256"),
        "shutdown_plan_sha256": shutdown.get("shutdown_plan_sha256"),
    }
    expected = checklist.get("bindings", {})
    for key, value in actual.items():
        if not isinstance(value, str) or not SHA_RE.fullmatch(value) or expected.get(key) != value:
            raise A12PreflightError(f"canonical binding mismatch: {key}")
    return actual


def _yaml_binding(path: Path, field: str) -> str | None:
    import yaml

    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise A12PreflightError(f"invalid YAML control: {path.name}")
    return value.get(field)


def _manifest(path: Path, required: Mapping[str, str]) -> dict[str, Any]:
    if not path.is_file():
        return {"status": "missing", "path": path.name, "file_count": 0, "sha256": None, "missing": sorted(required)}
    entries: dict[str, str] = {}
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise A12PreflightError(f"cannot read manifest: {path.name}") from exc
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        match = SHA_LINE_RE.fullmatch(line)
        if not match:
            errors.append(f"line_{line_number}_malformed")
            continue
        digest, relative = match.groups()
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            errors.append(f"line_{line_number}_unsafe_path")
            continue
        if relative in entries:
            errors.append(f"duplicate:{relative}")
            continue
        entries[relative] = digest
        target = path.parent / relative_path
        if not target.is_file():
            errors.append(f"missing_file:{relative}")
            continue
        if file_sha256(target) != digest:
            errors.append(f"hash_mismatch:{relative}")
        if required.get(relative) is not None and required[relative] != digest:
            errors.append(f"commitment_mismatch:{relative}")
    missing = sorted(set(required) - set(entries))
    errors.extend(f"missing_required:{item}" for item in missing)
    runtime_files = {
        item.relative_to(path.parent).as_posix()
        for item in path.parent.rglob("*")
        if item.is_file() and item.resolve() != path.resolve()
    }
    unlisted = sorted(runtime_files - set(entries))
    errors.extend(f"unlisted_runtime_file:{item}" for item in unlisted)
    extra = sorted(set(entries) - runtime_files)
    errors.extend(f"manifest_entry_without_file:{item}" for item in extra)
    status = "passed" if not errors and bool(entries) else "failed"
    return {
        "status": status,
        "path": path.name,
        "file_count": len(entries),
        "manifest_sha256": file_sha256(path),
        "required_file_count": len(required),
        "missing_required": missing,
        "unlisted_runtime_files": unlisted,
        "extra_manifest_entries": extra,
        "error_count": len(errors),
        "errors": errors[:32],
        "entries_sha256": canonical_sha256(entries),
    }


def _owner_inputs(root: Path, owner_root: Path | None, locks: Mapping[str, Any]) -> dict[str, Any]:
    if owner_root is None:
        return {
            "owner_root_supplied": False,
            "protected_root_accessed": False,
            "manifests": {arm: {"status": "pending_owner_input", "file_count": 0} for arm in DENSE_ARMS},
            "snowflake_remote_code": {"status": "pending_owner_input"},
            "qwen_measured_max_length": {"status": "pending_owner_input"},
            "adapter_parity": {"status": "pending_owner_input"},
            "storage": {"status": "pending_owner_input"},
            "protected_root": {"status": "pending_owner_input"},
            "provider_preflight": {"status": "pending_owner_input", "access_material_present": False},
            "termination_dry_run": {"status": "pending_owner_input", "access_material_present": False},
        }
    owner_root = owner_root.resolve()
    if owner_root == root.resolve() or root.resolve() in owner_root.parents:
        raise A12PreflightError("Owner input root must be outside the repository")
    manifests: dict[str, Any] = {}
    for arm in DENSE_ARMS:
        arm_lock = next(item for item in locks["locks"] if item["arm_id"] == arm)
        lock_path = root / arm_lock["uri"]
        lock = _read_json(lock_path)
        required = {item["path"]: item["sha256"] for item in lock["critical_artifacts"]}
        manifests[arm] = _manifest(owner_root / arm / "SHA256SUMS", required)
    result: dict[str, Any] = {
        "owner_root_supplied": True,
        "protected_root_accessed": False,
        "manifests": manifests,
    }
    key_names = {
        "snowflake-remote-code.json": "snowflake_remote_code",
        "qwen-measured-max-length.json": "qwen_measured_max_length",
        "adapter-parity.json": "adapter_parity",
        "storage.json": "storage",
        "protected-root.json": "protected_root",
        "provider-preflight.json": "provider_preflight",
        "termination-dry-run.json": "termination_dry_run",
    }
    for name, key in key_names.items():
        path = owner_root / name
        if not path.is_file():
            result[key] = {"status": "missing"}
            continue
        value = _read_json(path)
        _safe_metadata(value)
        value["metadata_sha256"] = canonical_sha256(value)
        value["status"] = "present"
        result[key] = value
    return result


def _check_owner_evidence(data: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    for arm in DENSE_ARMS:
        if data["manifests"].get(arm, {}).get("status") != "passed":
            blockers.append(f"{arm.lower()}_sha256s_manifest")
    remote = data.get("snowflake_remote_code", {})
    remote_files = remote.get("files")
    expected_remote_paths = {
        "configuration_hf_alibaba_nlp_gte.py",
        "modeling_hf_alibaba_nlp_gte.py",
    }
    remote_hashes_valid = (
        isinstance(remote_files, list)
        and {item.get("path") for item in remote_files if isinstance(item, Mapping)} == expected_remote_paths
        and all(SHA_RE.fullmatch(str(item.get("sha256", ""))) for item in remote_files if isinstance(item, Mapping))
    )
    if (
        remote.get("status") != "present"
        or not remote.get("byte_hashes_frozen")
        or remote.get("source_revision") != "95c2741480856aa9666782eb4afe11959938017f"
        or not remote_hashes_valid
    ):
        blockers.append("snowflake_remote_code_byte_hashes")
    qwen = data.get("qwen_measured_max_length", {})
    maximum = qwen.get("measured_max_input_tokens")
    if (
        qwen.get("status") != "present"
        or qwen.get("source_revision") != "97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3"
        or not isinstance(maximum, int)
        or isinstance(maximum, bool)
        or maximum <= 0
        or maximum > 32768
    ):
        blockers.append("qwen_measured_max_input_tokens")
    parity = data.get("adapter_parity", {})
    if parity.get("status") != "present" or parity.get("all_dense_arms_passed") is not True:
        blockers.append("dense_adapter_parity")
    storage = data.get("storage", {})
    if storage.get("status") != "present" or storage.get("return_path_writable") is not True or storage.get("free_bytes", 0) < 200 * 1024**3:
        blockers.append("artifact_return_storage")
    protected_root = data.get("protected_root", {})
    if (
        protected_root.get("status") != "present"
        or protected_root.get("mounted_read_only") is not True
        or protected_root.get("runner_write_access") is not False
        or protected_root.get("remote_present") is not False
    ):
        blockers.append("protected_root_read_only_local")
    quote = data.get("provider_preflight", {})
    instance_id = quote.get("provider_instance_id")
    rate = quote.get("hourly_instance_usd")
    hours = quote.get("estimated_instance_hours")
    quote_fields_valid = (
        quote.get("provider") == "vast"
        and isinstance(instance_id, str)
        and bool(re.fullmatch(r"[0-9]+", instance_id))
        and quote.get("quote_live") is True
        and quote.get("gpu_count") == 4
        and quote.get("gpu_model") == "NVIDIA GeForce RTX 3090"
        and isinstance(rate, (int, float))
        and not isinstance(rate, bool)
        and rate > 0
        and isinstance(hours, (int, float))
        and not isinstance(hours, bool)
        and hours > 0
        and rate * hours <= 18
    )
    if quote.get("status") != "present" or not quote_fields_valid:
        blockers.append("live_quote_and_provider_instance")
    termination = data.get("termination_dry_run", {})
    required_termination = (
        "guest_guard_armed",
        "destroy_command_validated",
        "ttl_trigger_simulated",
        "guest_poweroff_not_provider_destruction",
    )
    if (
        termination.get("status") != "present"
        or termination.get("provider") != "vast"
        or termination.get("provider_instance_id") != instance_id
        or termination.get("dry_run") is not True
        or termination.get("provider_destroy_invoked") is not False
        or any(termination.get(key) is not True for key in required_termination)
    ):
        blockers.append("external_termination_and_ttl")
    return blockers


def run_a1_2_preflight(repository_root: Path, owner_input_root: Path | None = None) -> PreflightResult:
    root = repository_root.resolve()
    if owner_input_root is not None:
        owner_resolved = owner_input_root.resolve()
        if owner_resolved == root or root in owner_resolved.parents:
            raise A12PreflightError("Owner input root must be outside the repository")
    lockset, checklist, shutdown, contract = _load_control(root)
    bindings = _validate_bindings(root, lockset, checklist, shutdown, contract)
    owner = _owner_inputs(root, owner_input_root, lockset)
    blockers = _check_owner_evidence(owner)
    now = _utc_now()
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "receipt_id": f"a1.2-owner-local-preflight-{now.replace(':', '').replace('-', '')}",
        "status": "blocked_owner_input" if blockers else "passed_pending_owner_adoption",
        "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
        "task_id": "A1.2",
        "evidence_class": "engineering_preflight",
        "scientific_authority": False,
        "generated_at": now,
        "cpu_only": True,
        "owner_input": owner,
        "canonical_bindings": bindings,
        "blockers": blockers,
        "launch_ready": False,
        "execution_contract_adopted": False,
        "gpu_reserved": False,
        "measured_execution": False,
        "protected_data_accessed": False,
        "credentials_accessed": False,
        "real_counters": {"measured_runs": 0, "candidate_count": 0, "selection_accesses": 0, "final_accesses": 0},
        "resource_counters": {"gpu_reservations": 0, "gpu_scientific_runs": 0, "model_downloads": 0, "paid_api_calls": 0, "charged_usd": 0},
        "claim_boundary": "owner_local_metadata_preflight_only_no_measured_retrieval_authority",
        "next_authorized_action": "Owner supplies sanitized manifests, live provider quote/identity, storage, parity, Qwen length, and termination receipt; rerun CPU preflight before contract adoption.",
    }
    payload["receipt_sha256"] = canonical_sha256(payload)
    return PreflightResult(payload["status"], payload)


def write_preflight_receipt(repository_root: Path, result: PreflightResult, output: Path | None = None) -> Path:
    root = repository_root.resolve()
    target = output or root / "outputs/audits/armindex/a1.2-owner-local-preflight-latest.json"
    target = target if target.is_absolute() else root / target
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result.receipt, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="")
    return target
