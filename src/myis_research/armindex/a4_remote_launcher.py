"""Transport and process lifecycle for an isolated A4 remote attempt.

This module owns operational mechanics only.  It does not evaluate rankings,
open qrels, inspect membership, or create Selection/Final access.  Every
remote operation is bound to a fresh attempt/root and returns aggregate-safe
hash receipts.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shlex
import subprocess
from typing import Any

from ..kernel.canonical import canonical_json, canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a4_remote_worker import validate_a4_completion_receipt, validate_a4_ranking_package, validate_a4_worker_request


class A4RemoteLauncherError(ValueError):
    """Raised when A4 remote transport or process identity is unsafe."""


_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_ATTEMPT = re.compile(r"^a4-goal001-[0-9]{8}T[0-9]{6}Z-[a-z0-9]{4,24}$")
_ROOT = re.compile(r"^/opt/myis/a4-goal001-[0-9]{8}T[0-9]{6}Z-[a-z0-9]{4,24}$")
_OPERATION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,80}$")
_PID = re.compile(r"^[1-9][0-9]{0,11}$")


def build_a4_stage_manifest(
    *,
    attempt_id: str,
    remote_root: str,
    runtime_bindings_sha256: str,
    profile_registry_sha256: str,
    code_bundle_sha256: str,
    runtime_assets_archive_sha256: str,
    runtime_assets_inventory_sha256: str,
    remote_asset_sha256s: Mapping[str, Any],
) -> dict[str, Any]:
    _attempt_root(attempt_id, remote_root)
    for name, value in (("runtime_bindings_sha256", runtime_bindings_sha256), ("profile_registry_sha256", profile_registry_sha256), ("code_bundle_sha256", code_bundle_sha256), ("runtime_assets_archive_sha256", runtime_assets_archive_sha256), ("runtime_assets_inventory_sha256", runtime_assets_inventory_sha256)):
        _require_sha256(value, name)
    assets = dict(remote_asset_sha256s)
    try:
        assert_aggregate_only(assets)
    except ValueError as error:
        raise A4RemoteLauncherError("A4 stage assets contain protected payload") from error
    if not assets or any(not isinstance(value, str) or not _SHA256.fullmatch(value) for value in assets.values()):
        raise A4RemoteLauncherError("A4 stage assets must be named SHA-256 values")
    body = {
        "schema_version": "myis.armindex-a4-remote-stage-manifest.v1",
        "status": "READY_A4_ISOLATED_REMOTE_STAGE",
        "attempt_id": attempt_id,
        "remote_root": remote_root,
        "runtime_bindings_sha256": runtime_bindings_sha256,
        "profile_registry_sha256": profile_registry_sha256,
        "code_bundle_sha256": code_bundle_sha256,
        "runtime_assets_archive_sha256": runtime_assets_archive_sha256,
        "runtime_assets_inventory_sha256": runtime_assets_inventory_sha256,
        "remote_asset_sha256s": assets,
        "selection_permitted": False,
        "final_permitted": False,
        "protected_payload_included": False,
    }
    return {**body, "stage_manifest_sha256": canonical_sha256(body)}


def validate_a4_stage_manifest(value: Mapping[str, Any]) -> dict[str, Any]:
    item = dict(value)
    _aggregate(item, "A4 stage manifest")
    required = {
        "schema_version", "status", "attempt_id", "remote_root", "runtime_bindings_sha256",
        "profile_registry_sha256", "code_bundle_sha256", "runtime_assets_archive_sha256",
        "runtime_assets_inventory_sha256", "remote_asset_sha256s", "selection_permitted",
        "final_permitted", "protected_payload_included", "stage_manifest_sha256",
    }
    if set(item) != required or item["schema_version"] != "myis.armindex-a4-remote-stage-manifest.v1" or item["status"] != "READY_A4_ISOLATED_REMOTE_STAGE":
        raise A4RemoteLauncherError("A4 stage manifest schema is invalid")
    if item["selection_permitted"] is not False or item["final_permitted"] is not False or item["protected_payload_included"] is not False:
        raise A4RemoteLauncherError("A4 stage manifest opens a protected gate")
    _attempt_root(item["attempt_id"], item["remote_root"])
    for field in ("runtime_bindings_sha256", "profile_registry_sha256", "code_bundle_sha256", "runtime_assets_archive_sha256", "runtime_assets_inventory_sha256"):
        _require_sha256(item[field], field)
    if not isinstance(item["remote_asset_sha256s"], Mapping) or not item["remote_asset_sha256s"]:
        raise A4RemoteLauncherError("A4 stage asset commitments are invalid")
    for value in item["remote_asset_sha256s"].values():
        _require_sha256(value, "remote asset")
    _self_hash(item, "stage_manifest_sha256", "A4 stage manifest")
    return item


def stage_a4_remote_runtime(
    stage_manifest: Mapping[str, Any],
    *,
    code_bundle: Path,
    runtime_assets_archive: Path,
    runtime_assets_inventory: Path,
    ssh_host: str,
    ssh_port: int,
    ssh_key_path: Path,
    known_hosts_path: Path,
    run: Callable[[Sequence[str]], str] | None = None,
) -> dict[str, Any]:
    """Create a new remote root and stage opaque code/assets only."""

    manifest = validate_a4_stage_manifest(stage_manifest)
    files = {
        "code_bundle": (Path(code_bundle), manifest["code_bundle_sha256"], "code.tar.gz"),
        "runtime_assets_archive": (Path(runtime_assets_archive), manifest["runtime_assets_archive_sha256"], "assets.tar.gz"),
        "runtime_assets_inventory": (Path(runtime_assets_inventory), manifest["runtime_assets_inventory_sha256"], "A4_RUNTIME_ASSETS.json"),
    }
    for role, (path, expected, _name) in files.items():
        _verify_file(path, expected, role)
    ssh, scp, target = _connection(ssh_host, ssh_port, ssh_key_path, known_hosts_path)
    execute = run or _run
    root = manifest["remote_root"]
    execute([*ssh, f"set -eu; test ! -e {shlex.quote(root)}; mkdir -p {shlex.quote(root)}/incoming {shlex.quote(root)}/current {shlex.quote(root)}/assets {shlex.quote(root)}/requests {shlex.quote(root)}/receipts {shlex.quote(root)}/output {shlex.quote(root)}/checkpoints"])
    for _role, (path, _expected, name) in files.items():
        execute([*scp, str(path.resolve()), f"{target}:{root}/incoming/{name}"])
    execute([*ssh, f"set -eu; test \"$(sha256sum {shlex.quote(root)}/incoming/code.tar.gz | awk '{{print $1}}')\" = {shlex.quote(manifest['code_bundle_sha256'])}; test \"$(sha256sum {shlex.quote(root)}/incoming/assets.tar.gz | awk '{{print $1}}')\" = {shlex.quote(manifest['runtime_assets_archive_sha256'])}; test \"$(sha256sum {shlex.quote(root)}/incoming/A4_RUNTIME_ASSETS.json | awk '{{print $1}}')\" = {shlex.quote(manifest['runtime_assets_inventory_sha256'])}; tar -xzf {shlex.quote(root)}/incoming/code.tar.gz -C {shlex.quote(root)}/current; tar -xzf {shlex.quote(root)}/incoming/assets.tar.gz -C {shlex.quote(root)}/assets; cp {shlex.quote(root)}/incoming/A4_RUNTIME_ASSETS.json {shlex.quote(root)}/assets/A4_RUNTIME_ASSETS.json; sha256sum {shlex.quote(root)}/incoming/* > {shlex.quote(root)}/receipts/staged.sha256"])
    body = {
        "schema_version": "myis.armindex-a4-remote-stage-receipt.v1",
        "status": "PASS_A4_REMOTE_RUNTIME_STAGED",
        "attempt_id": manifest["attempt_id"],
        "remote_root": root,
        "stage_manifest_sha256": manifest["stage_manifest_sha256"],
        "code_bundle_sha256": manifest["code_bundle_sha256"],
        "runtime_assets_archive_sha256": manifest["runtime_assets_archive_sha256"],
        "runtime_assets_inventory_sha256": manifest["runtime_assets_inventory_sha256"],
        "protected_payload_included": False,
        "selection_accesses": 0,
        "final_accesses": 0,
    }
    return {**body, "receipt_sha256": canonical_sha256(body)}


def build_a4_launch_integrity_receipt(*, attempt_id: str, stage_receipt_sha256: str, request_sha256: str, code_bundle_sha256: str, runtime_bindings_sha256: str) -> dict[str, Any]:
    _attempt(attempt_id)
    for field, value in (("stage_receipt_sha256", stage_receipt_sha256), ("request_sha256", request_sha256), ("code_bundle_sha256", code_bundle_sha256), ("runtime_bindings_sha256", runtime_bindings_sha256)):
        _require_sha256(value, field)
    body = {"schema_version": "myis.armindex-a4-launch-integrity-receipt.v1", "status": "PASS_A4_LAUNCH_INTEGRITY", "attempt_id": attempt_id, "stage_receipt_sha256": stage_receipt_sha256, "request_sha256": request_sha256, "code_bundle_sha256": code_bundle_sha256, "runtime_bindings_sha256": runtime_bindings_sha256, "qrels_opened": False, "membership_opened": False, "selection_accesses": 0, "final_accesses": 0, "protected_payload_included": False}
    return {**body, "receipt_sha256": canonical_sha256(body)}


def launch_a4_remote_operation(
    stage_receipt: Mapping[str, Any],
    launch_integrity: Mapping[str, Any],
    *,
    request_path: Path,
    ssh_host: str,
    ssh_port: int,
    ssh_key_path: Path,
    known_hosts_path: Path,
    run: Callable[[Sequence[str]], str] | None = None,
) -> dict[str, Any]:
    """Upload one request and start exactly one receipt-bound worker."""

    stage = dict(stage_receipt)
    integrity = dict(launch_integrity)
    if stage.get("status") != "PASS_A4_REMOTE_RUNTIME_STAGED" or integrity.get("status") != "PASS_A4_LAUNCH_INTEGRITY":
        raise A4RemoteLauncherError("A4 launch gates are not passed")
    _self_hash(stage, "receipt_sha256", "A4 stage receipt")
    _self_hash(integrity, "receipt_sha256", "A4 launch integrity receipt")
    if stage["attempt_id"] != integrity["attempt_id"] or stage["receipt_sha256"] != integrity["stage_receipt_sha256"]:
        raise A4RemoteLauncherError("A4 launch receipts are not bound")
    request = validate_a4_worker_request(_load_json(request_path, "A4 request"))
    if request["attempt_id"] != stage["attempt_id"] or request["request_sha256"] != integrity["request_sha256"]:
        raise A4RemoteLauncherError("A4 request is not bound to launch integrity")
    operation_id = f"{request['request_id']}-run"
    if not _OPERATION.fullmatch(operation_id):
        raise A4RemoteLauncherError("A4 operation identity is invalid")
    root = stage["remote_root"]
    ssh, scp, target = _connection(ssh_host, ssh_port, ssh_key_path, known_hosts_path)
    execute = run or _run
    execute([*scp, str(Path(request_path).resolve()), f"{target}:{root}/requests/{operation_id}.json"])
    command = f"cd {shlex.quote(root)}; export PYTHONPATH={shlex.quote(f'{root}/current')}:$PYTHONPATH; nohup {shlex.quote('python3')} -m myis_research.armindex.a4_remote_worker --request {shlex.quote(f'{root}/requests/{operation_id}.json')} --assets-root {shlex.quote(f'{root}/assets')} --output-root {shlex.quote(f'{root}/output/{operation_id}')} > {shlex.quote(f'{root}/output/{operation_id}.log')} 2>&1 & echo $!"
    pid_text = execute([*ssh, command]).strip().splitlines()[-1]
    if not _PID.fullmatch(pid_text):
        raise A4RemoteLauncherError("A4 remote worker PID was not returned")
    body = {"schema_version": "myis.armindex-a4-remote-launch-receipt.v1", "status": "PASS_A4_REMOTE_WORKER_LAUNCHED", "attempt_id": stage["attempt_id"], "operation_id": operation_id, "remote_root": root, "request_sha256": request["request_sha256"], "request_file_sha256": file_sha256(Path(request_path)), "stage_receipt_sha256": stage["receipt_sha256"], "remote_pid": pid_text, "protected_payload_included": False, "selection_accesses": 0, "final_accesses": 0}
    return {**body, "receipt_sha256": canonical_sha256(body)}


def build_a4_heartbeat(*, attempt_id: str, operation_id: str, remote_pid: str, completed_units: int, expected_units: int = 100, recorded_at_utc: datetime | None = None) -> dict[str, Any]:
    _attempt(attempt_id)
    if not _OPERATION.fullmatch(operation_id) or not _PID.fullmatch(remote_pid) or not isinstance(completed_units, int) or not 0 <= completed_units <= expected_units or expected_units != 100:
        raise A4RemoteLauncherError("A4 heartbeat identity or coverage is invalid")
    body = {"schema_version": "myis.armindex-a4-heartbeat.v1", "status": "A4_WORKER_HEARTBEAT", "attempt_id": attempt_id, "operation_id": operation_id, "remote_pid": remote_pid, "completed_units": completed_units, "expected_units": expected_units, "recorded_at_utc": (recorded_at_utc or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat().replace("+00:00", "Z"), "protected_payload_included": False}
    return {**body, "heartbeat_sha256": canonical_sha256(body)}


def build_a4_checkpoint(*, attempt_id: str, operation_id: str, completed_units: int, request_sha256: str, ranking_sha256: str | None = None) -> dict[str, Any]:
    _attempt(attempt_id)
    if not _OPERATION.fullmatch(operation_id) or not isinstance(completed_units, int) or not 0 <= completed_units <= 100:
        raise A4RemoteLauncherError("A4 checkpoint coverage is invalid")
    _require_sha256(request_sha256, "request_sha256")
    if ranking_sha256 is not None:
        _require_sha256(ranking_sha256, "ranking_sha256")
    body = {"schema_version": "myis.armindex-a4-checkpoint.v1", "status": "A4_CHECKPOINT", "attempt_id": attempt_id, "operation_id": operation_id, "completed_units": completed_units, "expected_units": 100, "request_sha256": request_sha256, "ranking_sha256": ranking_sha256, "protected_payload_included": False}
    return {**body, "checkpoint_sha256": canonical_sha256(body)}


def validate_a4_resume_checkpoint(
    checkpoint: Mapping[str, Any], *, attempt_id: str, operation_id: str, request_sha256: str
) -> dict[str, Any]:
    """Allow resume only from the same request and same operation lineage."""

    item = dict(checkpoint)
    _aggregate(item, "A4 checkpoint")
    required = {"schema_version", "status", "attempt_id", "operation_id", "completed_units", "expected_units", "request_sha256", "ranking_sha256", "protected_payload_included", "checkpoint_sha256"}
    if set(item) != required or item.get("schema_version") != "myis.armindex-a4-checkpoint.v1" or item.get("status") != "A4_CHECKPOINT":
        raise A4RemoteLauncherError("A4 checkpoint schema is invalid")
    if item.get("attempt_id") != attempt_id or item.get("operation_id") != operation_id or item.get("request_sha256") != request_sha256:
        raise A4RemoteLauncherError("A4 checkpoint is incompatible with resume")
    if item.get("protected_payload_included") is not False or not isinstance(item.get("completed_units"), int) or not 0 <= item["completed_units"] <= 100:
        raise A4RemoteLauncherError("A4 checkpoint coverage is invalid")
    _self_hash(item, "checkpoint_sha256", "A4 checkpoint")
    return item


def verify_a4_process_identity(*, launch_receipt: Mapping[str, Any], ps_output: str) -> dict[str, Any]:
    """Verify PID, root, and operation markers before accepting a worker as live."""

    launch = dict(launch_receipt)
    if launch.get("status") != "PASS_A4_REMOTE_WORKER_LAUNCHED":
        raise A4RemoteLauncherError("A4 launch receipt is invalid")
    _self_hash(launch, "receipt_sha256", "A4 launch receipt")
    pid = str(launch.get("remote_pid"))
    if not _PID.fullmatch(pid) or not isinstance(ps_output, str) or pid not in ps_output or launch["operation_id"] not in ps_output or launch["remote_root"] not in ps_output:
        raise A4RemoteLauncherError("A4 process identity does not match launch receipt")
    body = {"schema_version": "myis.armindex-a4-process-identity-receipt.v1", "status": "PASS_A4_REMOTE_PROCESS_IDENTITY", "attempt_id": launch["attempt_id"], "operation_id": launch["operation_id"], "remote_pid": pid, "launch_receipt_sha256": launch["receipt_sha256"], "protected_payload_included": False}
    return {**body, "receipt_sha256": canonical_sha256(body)}


def reap_a4_remote_process(launch_receipt: Mapping[str, Any], *, ssh_host: str, ssh_port: int, ssh_key_path: Path, known_hosts_path: Path, run: Callable[[Sequence[str]], str] | None = None) -> dict[str, Any]:
    launch = dict(launch_receipt)
    if launch.get("status") != "PASS_A4_REMOTE_WORKER_LAUNCHED":
        raise A4RemoteLauncherError("A4 launch receipt is invalid")
    _self_hash(launch, "receipt_sha256", "A4 launch receipt")
    root = launch.get("remote_root")
    if not isinstance(root, str) or not _ROOT.fullmatch(root):
        raise A4RemoteLauncherError("A4 process root is invalid")
    _PID.fullmatch(str(launch.get("remote_pid"))) or (_ for _ in ()).throw(A4RemoteLauncherError("A4 process PID is invalid"))
    ssh, _scp, _target = _connection(ssh_host, ssh_port, ssh_key_path, known_hosts_path)
    execute = run or _run
    pid = shlex.quote(str(launch["remote_pid"]))
    operation = shlex.quote(str(launch["operation_id"]))
    remote_root = shlex.quote(root)
    execute([*ssh, f"set +e; cmdline=$(tr '\\0' ' ' < /proc/{pid}/cmdline 2>/dev/null || true); case \"$cmdline\" in *{operation}*{remote_root}*) kill -TERM {pid} 2>/dev/null; sleep 1; kill -0 {pid} 2>/dev/null && kill -KILL {pid} 2>/dev/null;; *) exit 0;; esac"])
    body = {"schema_version": "myis.armindex-a4-reap-receipt.v1", "status": "PASS_A4_REMOTE_WORKER_REAPED", "attempt_id": launch["attempt_id"], "operation_id": launch["operation_id"], "remote_pid": launch["remote_pid"], "launch_receipt_sha256": launch["receipt_sha256"], "protected_payload_included": False}
    return {**body, "receipt_sha256": canonical_sha256(body)}


def safe_return_a4_result(*, launch_receipt: Mapping[str, Any], completion_path: Path, owner_output_path: Path) -> dict[str, Any]:
    """Copy a completion receipt/package only to a fresh Owner-local path."""
    launch = dict(launch_receipt)
    if launch.get("status") != "PASS_A4_REMOTE_WORKER_LAUNCHED":
        raise A4RemoteLauncherError("A4 launch receipt is invalid")
    source = Path(completion_path).resolve(strict=True)
    destination = Path(owner_output_path).resolve()
    if destination.exists() or destination.is_symlink():
        raise A4RemoteLauncherError("A4 safe-return destination already exists")
    completion = validate_a4_completion_receipt(_load_json(source, "A4 completion receipt"))
    if completion["attempt_id"] != launch["attempt_id"]:
        raise A4RemoteLauncherError("A4 completion is not bound to launch")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(canonical_json(completion) + "\n", encoding="utf-8")
    body = {"schema_version": "myis.armindex-a4-safe-return-receipt.v1", "status": "PASS_A4_SAFE_RETURN", "attempt_id": launch["attempt_id"], "operation_id": launch["operation_id"], "launch_receipt_sha256": launch["receipt_sha256"], "completion_receipt_sha256": completion["receipt_sha256"], "owner_local_only": True, "evaluation_pending": True, "protected_payload_included": False}
    return {**body, "receipt_sha256": canonical_sha256(body)}


def safe_return_a4_remote_result(
    *,
    launch_receipt: Mapping[str, Any],
    remote_completion_path: str,
    owner_output_path: Path,
    ssh_host: str,
    ssh_port: int,
    ssh_key_path: Path,
    known_hosts_path: Path,
    run: Callable[[Sequence[str]], str] | None = None,
) -> dict[str, Any]:
    """Fetch one aggregate-safe completion file and validate it locally."""

    launch = dict(launch_receipt)
    if launch.get("status") != "PASS_A4_REMOTE_WORKER_LAUNCHED" or not isinstance(remote_completion_path, str) or "qrel" in remote_completion_path.casefold() or "membership" in remote_completion_path.casefold():
        raise A4RemoteLauncherError("A4 remote result path is unsafe")
    root = launch.get("remote_root")
    if not isinstance(root, str) or not remote_completion_path.startswith(root + "/output/") or not remote_completion_path.endswith("/completion-receipt.json"):
        raise A4RemoteLauncherError("A4 remote result path is outside the attempt root")
    _ssh, scp, target = _connection(ssh_host, ssh_port, ssh_key_path, known_hosts_path)
    execute = run or _run
    temporary = Path(owner_output_path).resolve().with_suffix(".incoming.json")
    if temporary.exists() or temporary.is_symlink():
        raise A4RemoteLauncherError("A4 temporary safe-return destination exists")
    execute([*scp, f"{target}:{remote_completion_path}", str(temporary)])
    try:
        return safe_return_a4_result(launch_receipt=launch, completion_path=temporary, owner_output_path=owner_output_path)
    finally:
        temporary.unlink(missing_ok=True)


def safe_return_a4_remote_package(
    *,
    launch_receipt: Mapping[str, Any],
    remote_package_path: str,
    remote_completion_path: str,
    owner_output_root: Path,
    ssh_host: str,
    ssh_port: int,
    ssh_key_path: Path,
    known_hosts_path: Path,
    run: Callable[[Sequence[str]], str] | None = None,
) -> dict[str, Any]:
    """Return the ranking package and completion receipt into Owner Store."""

    launch = dict(launch_receipt)
    root = launch.get("remote_root")
    if launch.get("status") != "PASS_A4_REMOTE_WORKER_LAUNCHED" or not isinstance(root, str):
        raise A4RemoteLauncherError("A4 launch receipt is invalid")
    for path, suffix in ((remote_package_path, "/ranking-package.json"), (remote_completion_path, "/completion-receipt.json")):
        if not isinstance(path, str) or not path.startswith(root + "/output/") or not path.endswith(suffix) or any(part in path.casefold() for part in ("qrel", "membership", "credential", "secret")):
            raise A4RemoteLauncherError("A4 remote package path is unsafe")
    output = Path(owner_output_root).resolve()
    if output.exists() or output.is_symlink():
        raise A4RemoteLauncherError("A4 Owner Store output root already exists")
    output.mkdir(parents=True, exist_ok=False)
    _ssh, scp, target = _connection(ssh_host, ssh_port, ssh_key_path, known_hosts_path)
    execute = run or _run
    package_file = output / "ranking-package.json"
    completion_file = output / "completion-receipt.json"
    execute([*scp, f"{target}:{remote_package_path}", str(package_file)])
    execute([*scp, f"{target}:{remote_completion_path}", str(completion_file)])
    package = validate_a4_ranking_package(_load_json(package_file, "A4 ranking package"))
    completion = validate_a4_completion_receipt(_load_json(completion_file, "A4 completion receipt"))
    if package["attempt_id"] != launch["attempt_id"] or completion["attempt_id"] != launch["attempt_id"] or completion["ranking_sha256"] != package["ranking_sha256"]:
        raise A4RemoteLauncherError("A4 returned package is not bound to launch")
    body = {"schema_version": "myis.armindex-a4-safe-return-package-receipt.v1", "status": "PASS_A4_SAFE_RETURN_PACKAGE", "attempt_id": launch["attempt_id"], "operation_id": launch["operation_id"], "launch_receipt_sha256": launch["receipt_sha256"], "ranking_sha256": package["ranking_sha256"], "completion_receipt_sha256": completion["receipt_sha256"], "owner_local_only": True, "evaluation_pending": True, "protected_payload_included": False}
    return {**body, "receipt_sha256": canonical_sha256(body)}


def _connection(host: str, port: int, key: Path, known_hosts: Path) -> tuple[list[str], list[str], str]:
    if not isinstance(host, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]{0,252}", host) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise A4RemoteLauncherError("A4 SSH endpoint is invalid")
    prefix = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", f"UserKnownHostsFile={Path(known_hosts).resolve()}", "-i", str(Path(key).resolve()), "-p", str(port)]
    return prefix + [f"root@{host}"], ["scp", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", f"UserKnownHostsFile={Path(known_hosts).resolve()}", "-i", str(Path(key).resolve()), "-P", str(port)], f"root@{host}"


def _verify_file(path: Path, expected: str, role: str) -> None:
    candidate = path.resolve(strict=True)
    if candidate.is_symlink() or not candidate.is_file() or file_sha256(candidate) != expected:
        raise A4RemoteLauncherError(f"{role} hash mismatch")


def _load_json(path: Path, role: str) -> dict[str, Any]:
    candidate = Path(path).resolve(strict=True)
    try:
        value = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise A4RemoteLauncherError(f"{role} is invalid") from error
    if not isinstance(value, dict):
        raise A4RemoteLauncherError(f"{role} is invalid")
    return value


def _aggregate(value: Mapping[str, Any], role: str) -> None:
    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise A4RemoteLauncherError(f"{role} contains protected payload") from error


def _attempt(value: Any) -> None:
    if not isinstance(value, str) or not _ATTEMPT.fullmatch(value):
        raise A4RemoteLauncherError("A4 attempt identity is invalid")


def _attempt_root(attempt_id: str, root: str) -> None:
    _attempt(attempt_id)
    if not isinstance(root, str) or not _ROOT.fullmatch(root) or not root.endswith(attempt_id):
        raise A4RemoteLauncherError("A4 remote root is not bound to attempt")


def _require_sha256(value: Any, field: str) -> None:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise A4RemoteLauncherError(f"{field} must be SHA-256")


def _self_hash(value: Mapping[str, Any], field: str, role: str) -> None:
    _require_sha256(value.get(field), field)
    if value[field] != canonical_sha256({key: item for key, item in value.items() if key != field}):
        raise A4RemoteLauncherError(f"{role} self-hash mismatch")


def _run(arguments: Sequence[str]) -> str:
    return subprocess.run(list(arguments), check=True, capture_output=True, text=True).stdout


__all__ = ["A4RemoteLauncherError", "build_a4_checkpoint", "build_a4_heartbeat", "build_a4_launch_integrity_receipt", "build_a4_stage_manifest", "launch_a4_remote_operation", "reap_a4_remote_process", "safe_return_a4_remote_package", "safe_return_a4_remote_result", "safe_return_a4_result", "stage_a4_remote_runtime", "validate_a4_stage_manifest", "validate_a4_resume_checkpoint", "verify_a4_process_identity"]
