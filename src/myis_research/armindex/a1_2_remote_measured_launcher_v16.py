"""Topology-correct local launch and distributed finalization for A1.2 v16."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path
from typing import Any

from ..kernel.canonical import file_sha256
from .a1_2_execution_lifecycle_v16 import (
    complete_attempt,
    initialize_attempt,
    record_cell_checkpoint,
    teardown_attempt,
    validate_production_safe_return,
)
from .a1_2_owner_local_measured_runner_v16 import (
    ARM_IDS,
    CELL_IDS,
    merge_measured_arm_outputs,
    run_owner_local_measured_screen,
)
from .a1_2_safe_return_builder_v16 import build_safe_return_archive


class RemoteMeasuredLauncherV16Error(RuntimeError):
    """Raised when local execution or distributed finalization is unsafe."""


REMOTE_ARM_SLOTS = {"ARM-02": "0", "ARM-03": "1", "ARM-04": "2", "ARM-05": "3"}
_SHA256 = r"^[a-f0-9]{64}$"
_REMOTE_ROOT = re.compile(r"^/opt/myis/[A-Za-z0-9._/-]+$")
_ABSOLUTE_PATH = re.compile(r"^/[A-Za-z0-9._/-]+$")
_HOST = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_ATTEMPT = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
_PID = re.compile(r"^[1-9][0-9]{0,9}$")


def _load(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RemoteMeasuredLauncherV16Error(f"{role} is invalid") from error
    if not isinstance(value, dict):
        raise RemoteMeasuredLauncherV16Error(f"{role} must be an object")
    return value


def _validate_adoption(path: Path) -> dict[str, Any]:
    adoption = _load(path.resolve(strict=True), role="execution-adoption receipt")
    if (
        adoption.get("status")
        not in {"PASS", "PASS_EXECUTION_ADOPTION", "PASS_EXECUTION_ADOPTION_LOCKED"}
        or adoption.get("measured_retrieval_allowed") is not True
    ):
        raise RemoteMeasuredLauncherV16Error("execution adoption receipt is not PASS")
    return adoption


def _require_offline_runtime() -> None:
    if any(
        os.environ.get(name) != "1"
        for name in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "PIP_NO_INDEX")
    ):
        raise RemoteMeasuredLauncherV16Error("offline runtime policy is not enforced")


def _native(executable: str, arguments: list[str], *, role: str) -> str:
    result = subprocess.run(
        [executable, *arguments],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RemoteMeasuredLauncherV16Error(f"{role} failed with exit code {result.returncode}")
    return result.stdout.strip()


def _ssh_args(*, host: str, port: int, key_path: Path, known_hosts: Path) -> list[str]:
    if _HOST.fullmatch(host) is None:
        raise RemoteMeasuredLauncherV16Error("SSH host is invalid")
    if (
        not 1 <= port <= 65535
        or not key_path.is_file()
        or key_path.is_symlink()
        or not known_hosts.is_file()
        or known_hosts.is_symlink()
    ):
        raise RemoteMeasuredLauncherV16Error("SSH connection inputs are invalid")
    return [
        "-i", str(key_path.resolve()),
        "-p", str(port),
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=yes",
        "-o", f"UserKnownHostsFile={known_hosts.resolve()}",
        "root@" + host,
    ]


def _scp_args(*, host: str, port: int, key_path: Path, known_hosts: Path) -> list[str]:
    """Build SCP options separately because SCP uses -P for the port."""

    if _HOST.fullmatch(host) is None:
        raise RemoteMeasuredLauncherV16Error("SCP host is invalid")
    if (
        not 1 <= port <= 65535
        or not key_path.is_file()
        or key_path.is_symlink()
        or not known_hosts.is_file()
        or known_hosts.is_symlink()
    ):
        raise RemoteMeasuredLauncherV16Error("SCP connection inputs are invalid")
    return [
        "-i", str(key_path.resolve()),
        "-P", str(port),
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=yes",
        "-o", f"UserKnownHostsFile={known_hosts.resolve()}",
    ]


def _manifest_transfer_archive(manifest_path: Path, adoption_receipt_path: Path) -> tuple[Path, str]:
    """Create a temporary allowlisted archive of opaque compiled inputs only."""

    manifest_root = manifest_path.resolve(strict=True).parent
    manifest = _load(manifest_path.resolve(strict=True), role="measured input manifest")
    adoption = _validate_adoption(adoption_receipt_path)
    cells = manifest.get("cells")
    work = manifest.get("work_tokens")
    if not isinstance(cells, list) or len(cells) != 25 or not isinstance(work, dict):
        raise RemoteMeasuredLauncherV16Error("manifest does not bind 25 cells")
    source_paths = [manifest_path.resolve(strict=True), adoption_receipt_path.resolve(strict=True)]
    for cell in cells:
        for field in ("binding_path", "corpus_path", "query_path"):
            value = cell.get(field)
            if not isinstance(value, str) or Path(value).is_absolute() or ".." in Path(value).parts:
                raise RemoteMeasuredLauncherV16Error("manifest transfer path is unsafe")
            source_paths.append((manifest_root / value).resolve(strict=True))
    work_value = work.get("path")
    if not isinstance(work_value, str) or Path(work_value).is_absolute() or ".." in Path(work_value).parts:
        raise RemoteMeasuredLauncherV16Error("work-token transfer path is unsafe")
    source_paths.append((manifest_root / work_value).resolve(strict=True))
    temporary = Path(tempfile.mkdtemp(prefix="a1.2-v16-inputs-"))
    try:
        stage = temporary / "inputs"
        stage.mkdir()
        for source in dict.fromkeys(source_paths):
            if source.is_symlink() or not source.is_file():
                raise RemoteMeasuredLauncherV16Error("input transfer contains an unsafe file")
            if source == adoption_receipt_path.resolve():
                target = stage / "adoption.json"
                target.write_text(
                    json.dumps(
                        {
                            "status": adoption["status"],
                            "measured_retrieval_allowed": True,
                        },
                        ensure_ascii=True,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    + "\n",
                    encoding="ascii",
                )
                continue
            elif source == manifest_path.resolve():
                target = stage / "manifest.json"
            else:
                relative = source.relative_to(manifest_root)
                target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        archive = temporary / "inputs.tar.gz"
        with tarfile.open(archive, "w:gz") as handle:
            for source in sorted(stage.rglob("*")):
                if source.is_file() and not source.is_symlink():
                    handle.add(source, arcname=source.relative_to(stage).as_posix(), recursive=False)
        return archive, file_sha256(archive)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def stage_and_launch_remote_arms(
    *,
    bundle_path: Path,
    manifest_path: Path,
    adoption_receipt_path: Path,
    remote_root: str,
    remote_model_root: str,
    attempt_id: str,
    ssh_host: str,
    ssh_port: int,
    ssh_key_path: Path,
    known_hosts_path: Path,
    venv_python: str = "/opt/myis/a1.2-v16-stage-20260809/venv/bin/python",
) -> dict[str, Any]:
    """Stage frozen code/opaque inputs and launch one v16 worker per GPU."""

    _require_offline_runtime()
    if _REMOTE_ROOT.fullmatch(remote_root) is None or ".." in Path(remote_root).parts:
        raise RemoteMeasuredLauncherV16Error("remote root is unsafe")
    if _REMOTE_ROOT.fullmatch(remote_model_root) is None or ".." in Path(remote_model_root).parts:
        raise RemoteMeasuredLauncherV16Error("remote model root is unsafe")
    if _ATTEMPT.fullmatch(attempt_id) is None:
        raise RemoteMeasuredLauncherV16Error("attempt identity is invalid")
    if _ABSOLUTE_PATH.fullmatch(venv_python) is None or ".." in Path(venv_python).parts:
        raise RemoteMeasuredLauncherV16Error("remote Python path is unsafe")
    bundle = bundle_path.resolve(strict=True)
    if bundle.is_symlink() or file_sha256(bundle) is None:
        raise RemoteMeasuredLauncherV16Error("frozen bundle is unsafe")
    manifest = _load(manifest_path.resolve(strict=True), role="measured input manifest")
    if manifest.get("attempt_id") != attempt_id:
        raise RemoteMeasuredLauncherV16Error("attempt identity differs from manifest")
    inputs_archive, inputs_sha256 = _manifest_transfer_archive(manifest_path, adoption_receipt_path)
    ssh = _ssh_args(host=ssh_host, port=ssh_port, key_path=ssh_key_path, known_hosts=known_hosts_path)
    scp = _scp_args(host=ssh_host, port=ssh_port, key_path=ssh_key_path, known_hosts=known_hosts_path)
    target = ssh[-1]
    pids: dict[str, str] = {}
    try:
        _native("ssh", ssh + [f"set -eu; test ! -e {remote_root}; mkdir -p {remote_root}/incoming {remote_root}/current {remote_root}/inputs {remote_root}/output"], role="remote root preparation")
        _native("scp", [*scp, str(bundle), f"{target}:{remote_root}/incoming/bundle.tar.gz"], role="bundle upload")
        _native("scp", [*scp, str(inputs_archive), f"{target}:{remote_root}/incoming/inputs.tar.gz"], role="input upload")
        bundle_sha = file_sha256(bundle)
        command = (
            f"set -eu; test \"$(sha256sum {remote_root}/incoming/bundle.tar.gz | awk '{{print $1}}')\" = {bundle_sha}; "
            f"test \"$(sha256sum {remote_root}/incoming/inputs.tar.gz | awk '{{print $1}}')\" = {inputs_sha256}; "
            f"tar --no-same-owner --no-same-permissions -xzf {remote_root}/incoming/bundle.tar.gz -C {remote_root}/current; "
            f"tar --no-same-owner --no-same-permissions -xzf {remote_root}/incoming/inputs.tar.gz -C {remote_root}/inputs; "
            f"test -f {remote_root}/current/BUNDLE_MANIFEST.json; test -f {remote_root}/inputs/manifest.json; test -f {remote_root}/inputs/adoption.json; "
            f"for arm in ARM-02 ARM-03 ARM-04 ARM-05; do test -f {remote_model_root}/$arm/SHA256SUMS; (cd {remote_model_root}/$arm && sha256sum -c SHA256SUMS >/dev/null); done"
        )
        _native("ssh", ssh + [command], role="remote bundle/input verification")
        for arm, slot in REMOTE_ARM_SLOTS.items():
            output_root = f"{remote_root}/output/{arm}"
            command = (
                f"set -eu; mkdir -p {output_root}; "
                f"nohup sh -c 'set -u; export PYTHONPATH={remote_root}/current/src "
                f"CUDA_VISIBLE_DEVICES={slot} HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PIP_NO_INDEX=1 "
                f"PYTHONDONTWRITEBYTECODE=1; "
                f"if {venv_python} -m myis_research.armindex.a1_2_remote_arm_worker_v16 "
                f"--manifest {remote_root}/inputs/manifest.json --output-root {output_root} --model-root {remote_model_root} "
                f"--arm-id {arm} --gpu-slot {slot} --adoption-receipt {remote_root}/inputs/adoption.json "
                f">{output_root}/worker.stdout 2>{output_root}/worker.stderr; then "
                f"printf PASS >{output_root}/worker.success; "
                f"else code=$?; printf FAIL:$code >{output_root}/worker.failure; exit $code; fi' "
                f"</dev/null >/dev/null 2>&1 & echo $!"
            )
            output = _native("ssh", ssh + [command], role=f"{arm} remote launch")
            lines = output.splitlines()
            pid = lines[-1].strip() if lines else ""
            if _PID.fullmatch(pid) is None:
                raise RemoteMeasuredLauncherV16Error(f"{arm} remote launch returned an invalid PID")
            pids[arm] = pid
        return {
            "status": "PASS",
            "attempt_id": attempt_id,
            "remote_root": remote_root,
            "remote_model_root": remote_model_root,
            "inputs_archive_sha256": inputs_sha256,
            "bundle_sha256": bundle_sha,
            "remote_pids": pids,
            "arms": list(REMOTE_ARM_SLOTS),
            "measured_retrieval": True,
        }
    except BaseException:
        if pids:
            valid_pids = [pid for pid in pids.values() if _PID.fullmatch(pid)]
            cleanup = "for pid in " + " ".join(valid_pids) + "; do kill \"$pid\" 2>/dev/null || true; pkill -TERM -P \"$pid\" 2>/dev/null || true; done"
            try:
                _native("ssh", ssh + [cleanup], role="remote sibling cleanup")
            except RemoteMeasuredLauncherV16Error:
                pass
        raise
    finally:
        shutil.rmtree(inputs_archive.parent, ignore_errors=True)


def wait_remote_arms(
    *,
    remote_root: str,
    attempt_id: str,
    ssh_host: str,
    ssh_port: int,
    ssh_key_path: Path,
    known_hosts_path: Path,
    timeout_seconds: int = 21600,
    poll_seconds: int = 30,
) -> dict[str, Any]:
    """Wait for all four remote screen receipts without exposing rows/logs."""

    if timeout_seconds <= 0 or poll_seconds <= 0:
        raise RemoteMeasuredLauncherV16Error("remote wait bounds are invalid")
    if (
        _REMOTE_ROOT.fullmatch(remote_root) is None
        or ".." in Path(remote_root).parts
        or _ATTEMPT.fullmatch(attempt_id) is None
    ):
        raise RemoteMeasuredLauncherV16Error("remote wait identity is unsafe")
    ssh = _ssh_args(host=ssh_host, port=ssh_port, key_path=ssh_key_path, known_hosts=known_hosts_path)
    failure_checks = " ".join(f"{remote_root}/output/{arm}/worker.failure" for arm in REMOTE_ARM_SLOTS)
    checks = " ".join(f"{remote_root}/output/{arm}/{attempt_id}/receipts/screen.json" for arm in REMOTE_ARM_SLOTS)
    probe = (
        f"for p in {failure_checks}; do if test -f $p; then echo FAIL:$p; exit 0; fi; done; "
        f"if for p in {checks}; do test -f $p || exit 7; done; then echo PASS; else echo WAIT; fi"
    )
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            state = _native("ssh", ssh + [probe], role="remote status probe")
        except RemoteMeasuredLauncherV16Error:
            state = ""
        state = state.strip()
        if state.startswith("FAIL:"):
            raise RemoteMeasuredLauncherV16Error("remote arm worker failed before producing a screen receipt")
        if state == "PASS":
            return {"status": "PASS", "attempt_id": attempt_id, "arms": list(REMOTE_ARM_SLOTS), "cells": 20, "measured_retrieval": True}
        time.sleep(poll_seconds)
    raise RemoteMeasuredLauncherV16Error("remote arm wait timed out")


def collect_remote_arm_outputs(
    *,
    remote_root: str,
    attempt_id: str,
    local_output_root: Path,
    ssh_host: str,
    ssh_port: int,
    ssh_key_path: Path,
    known_hosts_path: Path,
) -> dict[str, Any]:
    """Copy only one completed attempt directory per remote arm to Owner-local storage."""

    if (
        _REMOTE_ROOT.fullmatch(remote_root) is None
        or ".." in Path(remote_root).parts
        or _ATTEMPT.fullmatch(attempt_id) is None
    ):
        raise RemoteMeasuredLauncherV16Error("remote collection identity is unsafe")
    destination_root = local_output_root.resolve()
    if destination_root.is_relative_to(Path.cwd().resolve()):
        raise RemoteMeasuredLauncherV16Error("remote collection must remain outside the repository")
    ssh = _ssh_args(host=ssh_host, port=ssh_port, key_path=ssh_key_path, known_hosts=known_hosts_path)
    scp = _scp_args(host=ssh_host, port=ssh_port, key_path=ssh_key_path, known_hosts=known_hosts_path)
    target = ssh[-1]
    destination_root.mkdir(parents=True, exist_ok=True)
    for arm in REMOTE_ARM_SLOTS:
        arm_root = destination_root / arm
        attempt_root = arm_root / attempt_id
        if attempt_root.exists() or attempt_root.is_symlink():
            raise RemoteMeasuredLauncherV16Error("remote collection destination already exists")
        arm_root.mkdir(parents=True, exist_ok=True)
        remote_attempt = f"{target}:{remote_root}/output/{arm}/{attempt_id}"
        _native("scp", [*scp, "-r", remote_attempt, str(arm_root)], role=f"{arm} output collection")
        screen = attempt_root / "receipts" / "screen.json"
        if attempt_root.is_symlink() or not attempt_root.is_dir() or screen.is_symlink() or not screen.is_file():
            raise RemoteMeasuredLauncherV16Error("remote collection did not produce an expected arm screen")
    return {
        "status": "PASS",
        "attempt_id": attempt_id,
        "arms": list(REMOTE_ARM_SLOTS),
        "cells": 20,
        "measured_retrieval": True,
    }


def run_local_cpu_arm(
    *,
    manifest_path: Path,
    output_root: Path,
    adoption_receipt_path: Path,
) -> dict[str, Any]:
    """Run only the frozen ARM-01 BM25 cells on the Owner-local CPU."""

    _validate_adoption(adoption_receipt_path)
    _require_offline_runtime()
    result = run_owner_local_measured_screen(
        manifest_path,
        output_root=output_root,
        arm_ids=("ARM-01",),
    )
    if result.get("status") != "PASS" or result.get("cells") != 5:
        raise RemoteMeasuredLauncherV16Error("ARM-01 did not complete five cells")
    return {
        "status": "PASS",
        "attempt_id": result["attempt_id"],
        "arm_id": "ARM-01",
        "device": "cpu",
        "location": "owner_local",
        "cells": 5,
        "work_tokens": 150,
        "top_k": 100,
        "receipt_sha256": result["receipt_sha256"],
        "measured_retrieval": True,
    }


def finalize_distributed_production(
    *,
    manifest_path: Path,
    lifecycle_root: Path,
    combined_runner_root: Path,
    archive_path: Path,
    arm_output_roots: dict[str, Path],
    attempt_id: str,
    executor_sha256: str,
    execution_identity: dict[str, str],
    transfer_manifest_sha256: str,
    split_commitment_sha256: str,
    ephemeral_token_map_sha256: str,
    adoption_receipt_path: Path,
) -> dict[str, Any]:
    """Merge five complete arms, checkpoint 25 cells, and build safe return."""

    _validate_adoption(adoption_receipt_path)
    _require_offline_runtime()
    if set(arm_output_roots) != set(ARM_IDS):
        raise RemoteMeasuredLauncherV16Error("all five arm outputs are required")
    manifest = _load(manifest_path.resolve(strict=True), role="measured input manifest")
    if manifest.get("attempt_id") != attempt_id:
        raise RemoteMeasuredLauncherV16Error("attempt identity differs from manifest")
    gates = manifest.get("gates")
    if not isinstance(gates, dict) or any(
        gates.get(name) != "PASS"
        for name in (
            "provider_admission",
            "execution_adoption",
            "watchdog_ttl",
            "protected_boundary",
            "frozen_bindings",
        )
    ):
        raise RemoteMeasuredLauncherV16Error("measured input manifest gates are not PASS")
    initialize_attempt(
        lifecycle_root.resolve(),
        attempt_id,
        gates=gates,
        execution_identity=execution_identity,
        executor_sha256=executor_sha256,
        execution_mode="production",
    )
    screen = merge_measured_arm_outputs(
        manifest_path,
        arm_output_roots=arm_output_roots,
        output_root=combined_runner_root,
    )
    runner_attempt = combined_runner_root.resolve() / attempt_id
    lifecycle_attempt = lifecycle_root.resolve() / "attempts" / attempt_id
    results_root = lifecycle_attempt / "results"
    checkpoint_hashes: dict[str, str] = {}
    for cell in CELL_IDS:
        source = runner_attempt / "receipts" / f"{cell}.json"
        target = results_root / f"{cell}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        checkpoint = record_cell_checkpoint(lifecycle_root, attempt_id, cell, target)
        checkpoint_hashes[cell] = checkpoint["checkpoint_sha256"]
    complete_attempt(lifecycle_root, attempt_id)
    teardown_attempt(lifecycle_root, attempt_id, children_reaped=True)
    safe = build_safe_return_archive(
        runner_output_root=combined_runner_root,
        attempt_id=attempt_id,
        archive_path=archive_path,
        transfer_manifest_sha256=transfer_manifest_sha256,
        split_commitment_sha256=split_commitment_sha256,
        ephemeral_token_map_sha256=ephemeral_token_map_sha256,
        checkpoint_sha256_by_cell=checkpoint_hashes,
    )
    safe_return_receipt = validate_production_safe_return(
        lifecycle_root,
        attempt_id,
        archive_path,
    )
    return {
        "status": "PASS",
        "attempt_id": attempt_id,
        "cells": screen["cells"],
        "safe_return_archive_sha256": safe["archive_sha256"],
        "safe_return_archive_bytes": safe["archive_bytes"],
        "safe_return_receipt_sha256": safe_return_receipt["receipt_sha256"],
        "lifecycle_root_sha256": file_sha256(lifecycle_attempt / "attempt.json"),
        "measured_retrieval": True,
    }


def _identity(values: list[str], parser: argparse.ArgumentParser) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in values:
        if "=" not in item:
            parser.error("--execution-identity must be KEY=SHA256")
        key, value = item.split("=", 1)
        result[key] = value
    return result


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-measured-launcher-v16")
    subparsers = parser.add_subparsers(dest="command", required=True)
    local = subparsers.add_parser("local-arm01")
    local.add_argument("--manifest", type=Path, required=True)
    local.add_argument("--output-root", type=Path, required=True)
    local.add_argument("--adoption-receipt", type=Path, required=True)
    final = subparsers.add_parser("finalize")
    final.add_argument("--manifest", type=Path, required=True)
    final.add_argument("--lifecycle-root", type=Path, required=True)
    final.add_argument("--combined-runner-root", type=Path, required=True)
    final.add_argument("--archive", type=Path, required=True)
    final.add_argument("--arm-output", action="append", default=[])
    final.add_argument("--attempt-id", required=True)
    final.add_argument("--executor-sha256", required=True)
    final.add_argument("--execution-identity", action="append", default=[])
    final.add_argument("--transfer-manifest-sha256", required=True)
    final.add_argument("--split-commitment-sha256", required=True)
    final.add_argument("--ephemeral-token-map-sha256", required=True)
    final.add_argument("--adoption-receipt", type=Path, required=True)
    remote = subparsers.add_parser("remote-launch")
    remote.add_argument("--bundle", type=Path, required=True)
    remote.add_argument("--manifest", type=Path, required=True)
    remote.add_argument("--adoption-receipt", type=Path, required=True)
    remote.add_argument("--remote-root", required=True)
    remote.add_argument("--remote-model-root", required=True)
    remote.add_argument("--attempt-id", required=True)
    remote.add_argument("--ssh-host", required=True)
    remote.add_argument("--ssh-port", type=int, required=True)
    remote.add_argument("--ssh-key", type=Path, required=True)
    remote.add_argument("--known-hosts", type=Path, required=True)
    remote.add_argument("--venv-python", default="/opt/myis/a1.2-v16-stage-20260809/venv/bin/python")
    wait = subparsers.add_parser("remote-wait")
    wait.add_argument("--remote-root", required=True)
    wait.add_argument("--attempt-id", required=True)
    wait.add_argument("--ssh-host", required=True)
    wait.add_argument("--ssh-port", type=int, required=True)
    wait.add_argument("--ssh-key", type=Path, required=True)
    wait.add_argument("--known-hosts", type=Path, required=True)
    wait.add_argument("--timeout-seconds", type=int, default=21600)
    wait.add_argument("--poll-seconds", type=int, default=30)
    collect = subparsers.add_parser("remote-collect")
    collect.add_argument("--remote-root", required=True)
    collect.add_argument("--attempt-id", required=True)
    collect.add_argument("--local-output-root", type=Path, required=True)
    collect.add_argument("--ssh-host", required=True)
    collect.add_argument("--ssh-port", type=int, required=True)
    collect.add_argument("--ssh-key", type=Path, required=True)
    collect.add_argument("--known-hosts", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "local-arm01":
        result = run_local_cpu_arm(
            manifest_path=args.manifest,
            output_root=args.output_root,
            adoption_receipt_path=args.adoption_receipt,
        )
    elif args.command == "finalize":
        arm_outputs: dict[str, Path] = {}
        for item in args.arm_output:
            if "=" not in item:
                parser.error("--arm-output must be ARM-ID=PATH")
            arm, raw_path = item.split("=", 1)
            arm_outputs[arm] = Path(raw_path)
        result = finalize_distributed_production(
            manifest_path=args.manifest,
            lifecycle_root=args.lifecycle_root,
            combined_runner_root=args.combined_runner_root,
            archive_path=args.archive,
            arm_output_roots=arm_outputs,
            attempt_id=args.attempt_id,
            executor_sha256=args.executor_sha256,
            execution_identity=_identity(args.execution_identity, parser),
            transfer_manifest_sha256=args.transfer_manifest_sha256,
            split_commitment_sha256=args.split_commitment_sha256,
            ephemeral_token_map_sha256=args.ephemeral_token_map_sha256,
            adoption_receipt_path=args.adoption_receipt,
        )
    elif args.command == "remote-launch":
        result = stage_and_launch_remote_arms(
            bundle_path=args.bundle,
            manifest_path=args.manifest,
            adoption_receipt_path=args.adoption_receipt,
            remote_root=args.remote_root,
            remote_model_root=args.remote_model_root,
            attempt_id=args.attempt_id,
            ssh_host=args.ssh_host,
            ssh_port=args.ssh_port,
            ssh_key_path=args.ssh_key,
            known_hosts_path=args.known_hosts,
            venv_python=args.venv_python,
        )
    elif args.command == "remote-wait":
        result = wait_remote_arms(
            remote_root=args.remote_root,
            attempt_id=args.attempt_id,
            ssh_host=args.ssh_host,
            ssh_port=args.ssh_port,
            ssh_key_path=args.ssh_key,
            known_hosts_path=args.known_hosts,
            timeout_seconds=args.timeout_seconds,
            poll_seconds=args.poll_seconds,
        )
    else:
        result = collect_remote_arm_outputs(
            remote_root=args.remote_root,
            attempt_id=args.attempt_id,
            local_output_root=args.local_output_root,
            ssh_host=args.ssh_host,
            ssh_port=args.ssh_port,
            ssh_key_path=args.ssh_key,
            known_hosts_path=args.known_hosts,
        )
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
