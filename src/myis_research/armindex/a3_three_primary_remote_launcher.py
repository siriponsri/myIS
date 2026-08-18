"""Isolated, aggregate-safe remote staging for the amended three-primary A3 run.

This module moves opaque runtime assets only after a separately validated A3
admission.  It never reads rankings, qrels, membership, query identifiers, or
worker logs.  The returned receipts are intentionally limited to stable IDs,
paths, counts, and SHA-256 commitments so they can be retained outside the
Owner Store.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import json
from pathlib import Path
import re
import shlex
import subprocess
from typing import Any, Callable

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a3_three_primary_execution import PRIMARY_ARMS
from .a3_three_primary_remote_retriever import (
    validate_remote_cell_request,
    validate_remote_ranking_package,
)


_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_ATTEMPT = re.compile(r"^a3-goal003-[0-9]{8}-[0-9]{3}$")
_REMOTE_ROOT = re.compile(r"^/opt/myis/a3-[a-z0-9][a-z0-9._-]{5,95}$")
_HOST = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]{0,252}$")
_PORT = re.compile(r"^[1-9][0-9]{0,4}$")
_PID = re.compile(r"^[1-9][0-9]{0,11}$")
_OPERATION_ID = re.compile(r"^[a-z0-9][a-z0-9._-]+$")
_REMOTE_DEVICE = re.compile(r"^cuda:[0-9]+$")
_A2_REUSE_ASSETS_ROOT = "/opt/myis/a2-goal004-20260816-005-incoming/assets"
_STAGE_KEYS = {
    "schema_version",
    "status",
    "attempt_id",
    "remote_root",
    "runtime_bindings_sha256",
    "execution_contract_sha256",
    "harness_batch_sha256s",
    "code_bundle_sha256",
    "runtime_assets_archive_sha256",
    "runtime_assets_inventory_sha256",
    "remote_asset_sha256s",
    "selection_permitted",
    "final_permitted",
    "stage_manifest_sha256",
}
_STAGE_RECEIPT_KEYS = {
    "schema_version",
    "status",
    "attempt_id",
    "remote_root",
    "stage_manifest_sha256",
    "code_bundle_sha256",
    "runtime_assets_archive_sha256",
    "runtime_assets_inventory_sha256",
    "remote_asset_sha256s",
    "staged_file_count",
    "rankings_returned",
    "protected_payload_included",
    "receipt_sha256",
}
_LAUNCH_RECEIPT_KEYS = {
    "schema_version",
    "status",
    "attempt_id",
    "operation_id",
    "request_sha256",
    "request_manifest_file_sha256",
    "stage_receipt_sha256",
    "remote_pid",
    "rankings_returned",
    "protected_payload_included",
    "receipt_sha256",
}
_RETURN_RECEIPT_KEYS = {
    "schema_version",
    "status",
    "attempt_id",
    "operation_id",
    "request_sha256",
    "stage_receipt_sha256",
    "launch_receipt_sha256",
    "ranking_sha256",
    "ranking_package_receipt_sha256",
    "ranking_package_file_sha256",
    "owner_local_only",
    "evaluation_pending",
    "rankings_embedded",
    "protected_payload_included",
    "receipt_sha256",
}


class A3ThreePrimaryRemoteLauncherError(ValueError):
    """Raised when an A3 remote lifecycle action is unsafe or incomplete."""


def build_a3_remote_stage_manifest(
    execution_contract: Mapping[str, Any],
    *,
    attempt_id: str,
    remote_root: str,
    code_bundle_sha256: str,
    runtime_assets_archive_sha256: str,
    runtime_assets_inventory_sha256: str,
    remote_asset_sha256s: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind an isolated remote root to the A3 Extended runtime before staging."""

    contract = _validate_extended_execution_contract(execution_contract)
    _validate_attempt_and_root(attempt_id, remote_root)
    for name, value in (
        ("code_bundle_sha256", code_bundle_sha256),
        ("runtime_assets_archive_sha256", runtime_assets_archive_sha256),
        ("runtime_assets_inventory_sha256", runtime_assets_inventory_sha256),
    ):
        _require_sha256(value, name)
    assets = _validate_remote_assets(remote_asset_sha256s)
    body = {
        "schema_version": "myis.armindex-a3-three-primary-remote-stage-manifest.v1",
        "status": "READY_A3_ISOLATED_REMOTE_STAGE",
        "attempt_id": attempt_id,
        "remote_root": remote_root,
        "runtime_bindings_sha256": contract["runtime_bindings_sha256"],
        "execution_contract_sha256": contract["execution_contract_sha256"],
        "harness_batch_sha256s": list(contract["harness_batch_sha256s"]),
        "code_bundle_sha256": code_bundle_sha256,
        "runtime_assets_archive_sha256": runtime_assets_archive_sha256,
        "runtime_assets_inventory_sha256": runtime_assets_inventory_sha256,
        "remote_asset_sha256s": assets,
        "selection_permitted": False,
        "final_permitted": False,
    }
    return {**body, "stage_manifest_sha256": canonical_sha256(body)}


def validate_a3_remote_stage_manifest(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a portable, aggregate-safe staging manifest."""

    manifest = _aggregate_copy(value, role="A3 remote stage manifest")
    if set(manifest) != _STAGE_KEYS:
        raise A3ThreePrimaryRemoteLauncherError("A3 stage manifest fields are incomplete")
    if (
        manifest["schema_version"]
        != "myis.armindex-a3-three-primary-remote-stage-manifest.v1"
        or manifest["status"] != "READY_A3_ISOLATED_REMOTE_STAGE"
        or manifest["selection_permitted"] is not False
        or manifest["final_permitted"] is not False
    ):
        raise A3ThreePrimaryRemoteLauncherError("A3 stage manifest identity is invalid")
    _validate_attempt_and_root(manifest["attempt_id"], manifest["remote_root"])
    for name in (
        "runtime_bindings_sha256",
        "execution_contract_sha256",
        "code_bundle_sha256",
        "runtime_assets_archive_sha256",
        "runtime_assets_inventory_sha256",
    ):
        _require_sha256(manifest[name], name)
    batches = manifest["harness_batch_sha256s"]
    if not isinstance(batches, list) or not 1 <= len(batches) <= 3:
        raise A3ThreePrimaryRemoteLauncherError(
            "A3 Extended stage requires one to three complete HarnessOpt batches"
        )
    for digest in batches:
        _require_sha256(digest, "harness_batch_sha256s")
    if len(set(batches)) != len(batches):
        raise A3ThreePrimaryRemoteLauncherError("A3 HarnessOpt batch commitments are duplicated")
    _validate_remote_assets(manifest["remote_asset_sha256s"])
    _self_hash(manifest, "stage_manifest_sha256", role="A3 remote stage manifest")
    return manifest


def stage_a3_remote_runtime(
    stage_manifest: Mapping[str, Any],
    *,
    code_bundle: Path,
    runtime_assets_archive: Path,
    runtime_assets_inventory: Path,
    ssh_host: str,
    ssh_port: int,
    ssh_key_path: Path,
    known_hosts_path: Path,
    remote_reuse_assets_root: str | None = None,
    run: Callable[[Sequence[str]], str] | None = None,
) -> dict[str, Any]:
    """Create a never-reused A3 remote root and verify opaque staged assets.

    The three local input files are expected to live in the Owner Store. Their
    paths and bytes do not enter receipts; only verified SHA-256 commitments do.
    """

    manifest = validate_a3_remote_stage_manifest(stage_manifest)
    files = {
        "code_bundle": (code_bundle, manifest["code_bundle_sha256"]),
        "runtime_assets_archive": (
            runtime_assets_archive,
            manifest["runtime_assets_archive_sha256"],
        ),
        "runtime_assets_inventory": (
            runtime_assets_inventory,
            manifest["runtime_assets_inventory_sha256"],
        ),
    }
    for role, (path, expected) in files.items():
        _verify_local_file(path, expected, role=role)
    ssh, scp, target = _connection_args(
        ssh_host=ssh_host,
        ssh_port=ssh_port,
        ssh_key_path=ssh_key_path,
        known_hosts_path=known_hosts_path,
    )
    execute = run or _run_no_output
    root = manifest["remote_root"]
    reuse_assets_root = _validate_reuse_assets_root(remote_reuse_assets_root)
    try:
        execute(
            [
                *ssh,
                (
                    f"set -eu; test ! -e {shlex.quote(root)}; "
                    f"mkdir -p {shlex.quote(root)}/incoming {shlex.quote(root)}/current "
                    f"{shlex.quote(root)}/assets {shlex.quote(root)}/requests "
                    f"{shlex.quote(root)}/receipts {shlex.quote(root)}/output"
                ),
            ]
        )
        for role, (path, _digest) in files.items():
            remote_name = {
                "code_bundle": "code.tar.gz",
                "runtime_assets_archive": "assets.tar.gz",
                "runtime_assets_inventory": "A3_RUNTIME_ASSETS.json",
            }[role]
            execute([*scp, str(path.resolve()), f"{target}:{root}/incoming/{remote_name}"])
        reuse = ""
        if reuse_assets_root is not None:
            corpus_sha = manifest["remote_asset_sha256s"]["corpus_sha256"]
            query_sha = manifest["remote_asset_sha256s"]["queries_sha256"]
            model_shas = manifest["remote_asset_sha256s"]["model_sha256s"]
            # The model commitment is the canonical POSIX tree hash, not the
            # hash of runtime-file-manifest.v4.json.  Compute that same
            # aggregate on the instance after reusing its verified bytes.
            tree_hash_script = (
                "import hashlib,json,os,sys;"
                "root=sys.argv[1]; expected=sys.argv[2];"
                "paths=[os.path.join(base,name) for base,dirs,files in os.walk(root) for name in files];"
                "if any(os.path.islink(path) for path in paths): raise SystemExit('symlink in model tree');"
                "entries=[{'path':os.path.relpath(path,root).replace(os.sep,'/'),'sha256':hashlib.sha256(open(path,'rb').read()).hexdigest()} for path in paths if os.path.relpath(path,root).replace(os.sep,'/') != 'A3_ADAPTER_BINDING.json'];"
                "entries.sort(key=lambda item:item['path']);"
                "actual=hashlib.sha256(json.dumps(entries,ensure_ascii=True,sort_keys=True,separators=(',',':')).encode()).hexdigest();"
                "raise SystemExit(0 if actual == expected else 'model tree hash mismatch')"
            )
            reuse = (
                f"mkdir -p {shlex.quote(root)}/assets/models; "
                f"cp --reflink=auto --preserve=mode,timestamps {shlex.quote(reuse_assets_root)}/owner-input/inputs/corpus.jsonl {shlex.quote(root)}/assets/corpus.jsonl; "
                f"if test -f {shlex.quote(root)}/assets/queries.jsonl && test \"$(sha256sum {shlex.quote(root)}/assets/queries.jsonl | awk '{{print $1}}')\" = {query_sha}; then :; "
                f"else cp --reflink=auto --preserve=mode,timestamps {shlex.quote(reuse_assets_root)}/owner-input/inputs/queries.jsonl {shlex.quote(root)}/assets/queries.jsonl; fi; "
                f"cp -a --reflink=auto {shlex.quote(reuse_assets_root)}/models/ARM-03/. {shlex.quote(root)}/assets/models/ARM-03/; "
                f"cp -a --reflink=auto {shlex.quote(reuse_assets_root)}/models/ARM-04/. {shlex.quote(root)}/assets/models/ARM-04/; "
                f"cp -a --reflink=auto {shlex.quote(reuse_assets_root)}/models/ARM-05/. {shlex.quote(root)}/assets/models/ARM-05/; "
                f"for arm in ARM-03 ARM-04 ARM-05; do cd {shlex.quote(root)}/assets/models/$arm; "
                "find . -type f ! -name 'A3_ADAPTER_BINDING.json' ! -name 'SHA256SUMS' "
                "! -name 'runtime-file-manifest.v4.json' -printf '%P\\n' | sort | "
                "while IFS= read -r file; do sha256sum \"$file\"; done > SHA256SUMS; done; "
                f"test \"$(sha256sum {shlex.quote(root)}/assets/corpus.jsonl | awk '{{print $1}}')\" = {corpus_sha}; "
                f"test \"$(sha256sum {shlex.quote(root)}/assets/queries.jsonl | awk '{{print $1}}')\" = {query_sha}; "
                f"python3 -c {shlex.quote(tree_hash_script)} {shlex.quote(root)}/assets/models/ARM-03 {model_shas['ARM-03']}; "
                f"python3 -c {shlex.quote(tree_hash_script)} {shlex.quote(root)}/assets/models/ARM-04 {model_shas['ARM-04']}; "
                f"python3 -c {shlex.quote(tree_hash_script)} {shlex.quote(root)}/assets/models/ARM-05 {model_shas['ARM-05']}; "
            )
        verify = (
            "set -eu; "
            f"test \"$(sha256sum {shlex.quote(root)}/incoming/code.tar.gz | awk '{{print $1}}')\" = {manifest['code_bundle_sha256']}; "
            f"test \"$(sha256sum {shlex.quote(root)}/incoming/assets.tar.gz | awk '{{print $1}}')\" = {manifest['runtime_assets_archive_sha256']}; "
            f"test \"$(sha256sum {shlex.quote(root)}/incoming/A3_RUNTIME_ASSETS.json | awk '{{print $1}}')\" = {manifest['runtime_assets_inventory_sha256']}; "
            f"tar --no-same-owner --no-same-permissions -xzf {shlex.quote(root)}/incoming/code.tar.gz -C {shlex.quote(root)}/current; "
            f"tar --no-same-owner --no-same-permissions -xzf {shlex.quote(root)}/incoming/assets.tar.gz -C {shlex.quote(root)}/assets; "
            f"{reuse}"
            f"sed -i 's/\\r$//' {shlex.quote(root)}/assets/bin/a3-three-primary-ranker; "
            f"chmod 755 {shlex.quote(root)}/assets/bin/a3-three-primary-ranker; "
            f"test -f {shlex.quote(root)}/current/src/myis_research/armindex/a3_three_primary_remote_retriever.py; "
            f"test -f {shlex.quote(root)}/current/src/myis_research/armindex/a3_three_primary_remote_worker.py; "
            f"cp {shlex.quote(root)}/incoming/A3_RUNTIME_ASSETS.json {shlex.quote(root)}/assets/A3_RUNTIME_ASSETS.json; "
            f"test -f {shlex.quote(root)}/assets/A3_RUNTIME_ASSETS.json"
        )
        execute([*ssh, verify])
    except (OSError, subprocess.SubprocessError, A3ThreePrimaryRemoteLauncherError) as error:
        raise A3ThreePrimaryRemoteLauncherError("A3 isolated remote stage failed") from error
    body = {
        "schema_version": "myis.armindex-a3-three-primary-stage-receipt.v1",
        "status": "PASS_A3_ISOLATED_REMOTE_STAGE",
        "attempt_id": manifest["attempt_id"],
        "remote_root": root,
        "stage_manifest_sha256": manifest["stage_manifest_sha256"],
        "code_bundle_sha256": manifest["code_bundle_sha256"],
        "runtime_assets_archive_sha256": manifest["runtime_assets_archive_sha256"],
        "runtime_assets_inventory_sha256": manifest["runtime_assets_inventory_sha256"],
        "remote_asset_sha256s": manifest["remote_asset_sha256s"],
        "staged_file_count": 3,
        "rankings_returned": False,
        "protected_payload_included": False,
    }
    return {**body, "receipt_sha256": canonical_sha256(body)}


def validate_a3_remote_stage_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the aggregate-only receipt produced by remote staging."""

    receipt = _aggregate_copy(value, role="A3 remote stage receipt")
    if set(receipt) != _STAGE_RECEIPT_KEYS:
        raise A3ThreePrimaryRemoteLauncherError("A3 stage receipt fields are incomplete")
    if (
        receipt["schema_version"] != "myis.armindex-a3-three-primary-stage-receipt.v1"
        or receipt["status"] != "PASS_A3_ISOLATED_REMOTE_STAGE"
        or receipt["rankings_returned"] is not False
        or receipt["protected_payload_included"] is not False
        or receipt["staged_file_count"] != 3
    ):
        raise A3ThreePrimaryRemoteLauncherError("A3 stage receipt identity is invalid")
    _validate_attempt_and_root(receipt["attempt_id"], receipt["remote_root"])
    for field in (
        "stage_manifest_sha256",
        "code_bundle_sha256",
        "runtime_assets_archive_sha256",
        "runtime_assets_inventory_sha256",
    ):
        _require_sha256(receipt[field], field)
    _validate_remote_assets(receipt["remote_asset_sha256s"])
    _self_hash(receipt, "receipt_sha256", role="A3 remote stage receipt")
    return receipt


def launch_a3_remote_operation(
    stage_receipt: Mapping[str, Any],
    request: Mapping[str, Any],
    *,
    request_manifest: Path,
    ssh_host: str,
    ssh_port: int,
    ssh_key_path: Path,
    known_hosts_path: Path,
    remote_python: str,
    remote_device: str | None = None,
    run: Callable[[Sequence[str]], str] | None = None,
) -> dict[str, Any]:
    """Launch one isolated remote operation without reading output or logs.

    The actual ranker must be packaged with the committed code bundle and emit
    only the transient Owner-local ranking package expected by the evaluator.
    This routine starts no work until a request manifest has passed the remote
    request contract and its local SHA-256 matches that request.
    """

    stage = validate_a3_remote_stage_receipt(stage_receipt)
    checked_request = validate_remote_cell_request(request)
    request_manifest_file_sha256 = _verify_request_manifest(
        request_manifest, checked_request
    )
    if not isinstance(remote_python, str) or not remote_python.startswith("/") or ".." in Path(remote_python).parts:
        raise A3ThreePrimaryRemoteLauncherError("remote Python path is unsafe")
    if remote_device is not None and not _REMOTE_DEVICE.fullmatch(remote_device):
        raise A3ThreePrimaryRemoteLauncherError("remote device is unsafe")
    ssh, scp, target = _connection_args(
        ssh_host=ssh_host,
        ssh_port=ssh_port,
        ssh_key_path=ssh_key_path,
        known_hosts_path=known_hosts_path,
    )
    execute = run or _run_no_output
    root = stage["remote_root"]
    operation = checked_request["operation_id"]
    try:
        execute([*scp, str(request_manifest.resolve()), f"{target}:{root}/requests/{operation}.json"])
        command = (
            "set -eu; "
            f"test -f {shlex.quote(root)}/assets/A3_RUNTIME_ASSETS.json; "
            f"test \"$(sha256sum {shlex.quote(root)}/requests/{operation}.json | awk '{{print $1}}')\" = {request_manifest_file_sha256}; "
            f"mkdir -p {shlex.quote(root)}/output; "
            f"nohup sh -c 'set -eu; export PYTHONPATH={shlex.quote(root)}/current/src A3_REMOTE_PYTHON={shlex.quote(remote_python)}"
            + (f" A3_REMOTE_DEVICE={shlex.quote(remote_device)}" if remote_device is not None else "")
            + "; "
            f"{shlex.quote(remote_python)} -m myis_research.armindex.a3_three_primary_remote_worker "
            f"--request {shlex.quote(root)}/requests/{operation}.json --assets-root {shlex.quote(root)}/assets "
            f"--output-root {shlex.quote(root)}/output/{operation}' </dev/null "
            f">{shlex.quote(root)}/output/{operation}.stdout 2>{shlex.quote(root)}/output/{operation}.stderr & echo $!"
        )
        output = execute([*ssh, command]).strip().splitlines()
    except (OSError, subprocess.SubprocessError, A3ThreePrimaryRemoteLauncherError) as error:
        raise A3ThreePrimaryRemoteLauncherError("A3 remote operation launch failed") from error
    pid = output[-1].strip() if output else ""
    if _PID.fullmatch(pid) is None:
        raise A3ThreePrimaryRemoteLauncherError("A3 remote operation did not return a process identity")
    body = {
        "schema_version": "myis.armindex-a3-three-primary-launch-receipt.v1",
        "status": "PASS_A3_REMOTE_OPERATION_LAUNCHED",
        "attempt_id": stage["attempt_id"],
        "operation_id": operation,
        "request_sha256": checked_request["request_sha256"],
        "request_manifest_file_sha256": request_manifest_file_sha256,
        "stage_receipt_sha256": stage["receipt_sha256"],
        "remote_pid": pid,
        "rankings_returned": False,
        "protected_payload_included": False,
    }
    return {**body, "receipt_sha256": canonical_sha256(body)}


def validate_a3_remote_launch_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a launch receipt before monitoring an A3 remote worker."""

    receipt = _aggregate_copy(value, role="A3 launch receipt")
    if set(receipt) != _LAUNCH_RECEIPT_KEYS:
        raise A3ThreePrimaryRemoteLauncherError("A3 launch receipt fields are incomplete")
    if (
        receipt["schema_version"] != "myis.armindex-a3-three-primary-launch-receipt.v1"
        or receipt["status"] != "PASS_A3_REMOTE_OPERATION_LAUNCHED"
        or receipt["rankings_returned"] is not False
        or receipt["protected_payload_included"] is not False
        or not _ATTEMPT.fullmatch(str(receipt["attempt_id"]))
        or not _OPERATION_ID.fullmatch(str(receipt["operation_id"]))
        or not _PID.fullmatch(str(receipt["remote_pid"]))
    ):
        raise A3ThreePrimaryRemoteLauncherError("A3 launch receipt identity is invalid")
    for field in ("request_sha256", "request_manifest_file_sha256", "stage_receipt_sha256"):
        _require_sha256(receipt[field], field)
    _self_hash(receipt, "receipt_sha256", role="A3 launch receipt")
    return receipt


def collect_a3_remote_ranking_package(
    stage_receipt: Mapping[str, Any],
    launch_receipt: Mapping[str, Any],
    request: Mapping[str, Any],
    *,
    owner_local_output: Path,
    ssh_host: str,
    ssh_port: int,
    ssh_key_path: Path,
    known_hosts_path: Path,
    run: Callable[[Sequence[str]], str] | None = None,
) -> dict[str, Any]:
    """Return exactly one transient ranking package to an Owner-local path.

    ``owner_local_output`` is deliberately caller-owned and must be outside the
    repository.  This helper emits only a hash-bound return receipt; the raw
    package is passed directly to ``evaluate_remote_ranking_owner_local``.
    """

    stage = validate_a3_remote_stage_receipt(stage_receipt)
    launch = validate_a3_remote_launch_receipt(launch_receipt)
    checked_request = validate_remote_cell_request(request)
    if (
        launch["attempt_id"] != stage["attempt_id"]
        or launch["stage_receipt_sha256"] != stage["receipt_sha256"]
        or launch["operation_id"] != checked_request["operation_id"]
        or launch["request_sha256"] != checked_request["request_sha256"]
    ):
        raise A3ThreePrimaryRemoteLauncherError("ranking return lineage is not bound")
    destination = owner_local_output.resolve()
    repository = Path.cwd().resolve()
    if destination.is_relative_to(repository):
        raise A3ThreePrimaryRemoteLauncherError("ranking return must remain outside the repository")
    if destination.exists() or destination.is_symlink():
        raise A3ThreePrimaryRemoteLauncherError("ranking return destination already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    ssh, scp, target = _connection_args(
        ssh_host=ssh_host,
        ssh_port=ssh_port,
        ssh_key_path=ssh_key_path,
        known_hosts_path=known_hosts_path,
    )
    execute = run or _run_no_output
    root, operation = stage["remote_root"], checked_request["operation_id"]
    try:
        execute(
            [
                *ssh,
                f"set -eu; test -f {shlex.quote(root)}/output/{operation}/ranking-package.json; "
                f"test ! -f {shlex.quote(root)}/output/{operation}/worker.failure",
            ]
        )
        execute(
            [
                *scp,
                f"{target}:{root}/output/{operation}/ranking-package.json",
                str(destination),
            ]
        )
    except (OSError, subprocess.SubprocessError, A3ThreePrimaryRemoteLauncherError) as error:
        destination.unlink(missing_ok=True)
        raise A3ThreePrimaryRemoteLauncherError("A3 ranking package return failed") from error
    try:
        package = _load_json_file(destination, role="returned ranking package")
        ranking = validate_remote_ranking_package(package)
    except (OSError, ValueError, A3ThreePrimaryRemoteLauncherError) as error:
        destination.unlink(missing_ok=True)
        raise A3ThreePrimaryRemoteLauncherError("returned A3 ranking package is invalid") from error
    if ranking["request_sha256"] != checked_request["request_sha256"]:
        destination.unlink(missing_ok=True)
        raise A3ThreePrimaryRemoteLauncherError("returned A3 ranking package is not bound to its request")
    body = {
        "schema_version": "myis.armindex-a3-three-primary-transient-ranking-return-receipt.v1",
        "status": "PASS_A3_TRANSIENT_OWNER_LOCAL_RANKING_RETURN",
        "attempt_id": stage["attempt_id"],
        "operation_id": operation,
        "request_sha256": checked_request["request_sha256"],
        "stage_receipt_sha256": stage["receipt_sha256"],
        "launch_receipt_sha256": launch["receipt_sha256"],
        "ranking_sha256": ranking["ranking_sha256"],
        "ranking_package_receipt_sha256": ranking["receipt_sha256"],
        "ranking_package_file_sha256": file_sha256(destination),
        "owner_local_only": True,
        "evaluation_pending": True,
        "rankings_embedded": False,
        "protected_payload_included": False,
    }
    return {**body, "receipt_sha256": canonical_sha256(body)}


def validate_a3_transient_ranking_return_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a receipt that proves a ranking stayed outside the repository."""

    receipt = _aggregate_copy(value, role="A3 transient ranking return receipt")
    if set(receipt) != _RETURN_RECEIPT_KEYS:
        raise A3ThreePrimaryRemoteLauncherError("A3 ranking return receipt fields are incomplete")
    if (
        receipt["schema_version"]
        != "myis.armindex-a3-three-primary-transient-ranking-return-receipt.v1"
        or receipt["status"] != "PASS_A3_TRANSIENT_OWNER_LOCAL_RANKING_RETURN"
        or receipt["owner_local_only"] is not True
        or receipt["evaluation_pending"] is not True
        or receipt["rankings_embedded"] is not False
        or receipt["protected_payload_included"] is not False
        or not _ATTEMPT.fullmatch(str(receipt["attempt_id"]))
        or not _OPERATION_ID.fullmatch(str(receipt["operation_id"]))
    ):
        raise A3ThreePrimaryRemoteLauncherError("A3 ranking return receipt identity is invalid")
    for field in (
        "request_sha256",
        "stage_receipt_sha256",
        "launch_receipt_sha256",
        "ranking_sha256",
        "ranking_package_receipt_sha256",
        "ranking_package_file_sha256",
    ):
        _require_sha256(receipt[field], field)
    _self_hash(receipt, "receipt_sha256", role="A3 transient ranking return receipt")
    return receipt


def _validate_extended_execution_contract(value: Mapping[str, Any]) -> dict[str, Any]:
    contract = _aggregate_copy(value, role="A3 Extended execution contract")
    required = {
        "schema_version", "status", "runtime_bindings_sha256", "transfer_matrix",
        "fixed_union_sha256", "harness_batch_sha256s", "execution_order",
        "selection_permitted", "final_permitted", "provider_contact_performed",
        "remote_execution_performed", "execution_contract_sha256",
    }
    if set(contract) != required or (
        contract["schema_version"] != "myis.armindex-a3-three-primary-execution-contract.v1"
        or contract["status"] != "READY_FOR_POST_ADMISSION_EXECUTION"
        or contract["selection_permitted"] is not False
        or contract["final_permitted"] is not False
    ):
        raise A3ThreePrimaryRemoteLauncherError("A3 execution contract is not launch-safe")
    for field in ("runtime_bindings_sha256", "fixed_union_sha256"):
        _require_sha256(contract[field], field)
    batches = contract["harness_batch_sha256s"]
    if not isinstance(batches, list) or not 1 <= len(batches) <= 3:
        raise A3ThreePrimaryRemoteLauncherError(
            "A3 Extended requires one to three complete HarnessOpt batches"
        )
    for digest in batches:
        _require_sha256(digest, "harness_batch_sha256s")
    pairs = {
        (row.get("source_arm_id"), row.get("target_arm_id"))
        for row in contract["transfer_matrix"]
        if isinstance(row, Mapping)
    } if isinstance(contract["transfer_matrix"], list) else set()
    expected = {(source, target) for source in PRIMARY_ARMS for target in PRIMARY_ARMS}
    if len(contract["transfer_matrix"]) != 9 or pairs != expected:
        raise A3ThreePrimaryRemoteLauncherError("A3 stage requires the exact 3x3 transfer matrix")
    _self_hash(contract, "execution_contract_sha256", role="A3 Extended execution contract")
    return contract


def _validate_remote_assets(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {"corpus_sha256", "queries_sha256", "model_sha256s"}:
        raise A3ThreePrimaryRemoteLauncherError("remote assets must bind corpus, queries, and models")
    for field in ("corpus_sha256", "queries_sha256"):
        _require_sha256(value[field], field)
    models = value["model_sha256s"]
    if not isinstance(models, Mapping) or set(models) != set(PRIMARY_ARMS):
        raise A3ThreePrimaryRemoteLauncherError("remote model assets must cover the primary arms")
    result = {"corpus_sha256": str(value["corpus_sha256"]), "queries_sha256": str(value["queries_sha256"]), "model_sha256s": {}}
    for arm_id, digest in models.items():
        _require_sha256(digest, f"model_sha256s.{arm_id}")
        result["model_sha256s"][str(arm_id)] = str(digest)
    return result


def _verify_local_file(path: Path, expected_sha256: str, *, role: str) -> None:
    _require_sha256(expected_sha256, f"{role}_sha256")
    resolved = path.resolve(strict=True)
    if resolved.is_symlink() or not resolved.is_file() or file_sha256(resolved) != expected_sha256:
        raise A3ThreePrimaryRemoteLauncherError(f"{role} does not match its frozen SHA-256")


def _verify_request_manifest(path: Path, request: Mapping[str, Any]) -> str:
    resolved = path.resolve(strict=True)
    if resolved.is_symlink() or not resolved.is_file():
        raise A3ThreePrimaryRemoteLauncherError("request manifest is not a regular file")
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as error:
        raise A3ThreePrimaryRemoteLauncherError("request manifest is not valid JSON") from error
    if not isinstance(payload, Mapping) or dict(payload) != dict(request):
        raise A3ThreePrimaryRemoteLauncherError("request manifest does not match its request")
    return file_sha256(resolved)


def _load_json_file(path: Path, *, role: str) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if resolved.is_symlink() or not resolved.is_file():
        raise A3ThreePrimaryRemoteLauncherError(f"{role} is not a regular file")
    try:
        value = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as error:
        raise A3ThreePrimaryRemoteLauncherError(f"{role} is not valid JSON") from error
    if not isinstance(value, dict):
        raise A3ThreePrimaryRemoteLauncherError(f"{role} must be an object")
    return value


def _connection_args(*, ssh_host: str, ssh_port: int, ssh_key_path: Path, known_hosts_path: Path) -> tuple[list[str], list[str], str]:
    if not _HOST.fullmatch(ssh_host) or isinstance(ssh_port, bool) or not 1 <= ssh_port <= 65535:
        raise A3ThreePrimaryRemoteLauncherError("SSH endpoint is unsafe")
    key, known = ssh_key_path.resolve(strict=True), known_hosts_path.resolve(strict=True)
    if key.is_symlink() or known.is_symlink() or not key.is_file() or not known.is_file():
        raise A3ThreePrimaryRemoteLauncherError("SSH material is unavailable")
    port = str(ssh_port)
    target = f"root@{ssh_host}"
    common = ["-o", "BatchMode=yes", "-o", f"UserKnownHostsFile={known}", "-o", "StrictHostKeyChecking=yes", "-i", str(key)]
    return (["ssh", *common, "-p", port, target], ["scp", *common, "-P", port], target)


def _run_no_output(arguments: Sequence[str]) -> str:
    completed = subprocess.run(list(arguments), check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return completed.stdout


def _validate_attempt_and_root(attempt_id: Any, remote_root: Any) -> None:
    if not _ATTEMPT.fullmatch(str(attempt_id)):
        raise A3ThreePrimaryRemoteLauncherError("A3 attempt identity is invalid")
    if not _REMOTE_ROOT.fullmatch(str(remote_root)) or "/a2-" in str(remote_root) or ".." in Path(str(remote_root)).parts:
        raise A3ThreePrimaryRemoteLauncherError("A3 remote root must be a new isolated A3 root")


def _validate_reuse_assets_root(value: str | None) -> str | None:
    if value is None:
        return None
    if value != _A2_REUSE_ASSETS_ROOT:
        raise A3ThreePrimaryRemoteLauncherError("A3 asset reuse source is not the bound A2 input root")
    return value


def _aggregate_copy(value: Mapping[str, Any], *, role: str) -> dict[str, Any]:
    result = deepcopy(dict(value))
    try:
        assert_aggregate_only(result)
    except ValueError as error:
        raise A3ThreePrimaryRemoteLauncherError(f"{role}: {error}") from error
    return result


def _require_sha256(value: Any, field: str) -> None:
    if not _SHA256.fullmatch(str(value)):
        raise A3ThreePrimaryRemoteLauncherError(f"{field} must be a SHA-256 digest")


def _self_hash(value: Mapping[str, Any], field: str, *, role: str) -> None:
    _require_sha256(value.get(field), field)
    if value[field] != canonical_sha256({key: item for key, item in value.items() if key != field}):
        raise A3ThreePrimaryRemoteLauncherError(f"{role} self-hash does not bind its contents")


__all__ = [
    "A3ThreePrimaryRemoteLauncherError",
    "build_a3_remote_stage_manifest",
    "collect_a3_remote_ranking_package",
    "launch_a3_remote_operation",
    "stage_a3_remote_runtime",
    "validate_a3_remote_launch_receipt",
    "validate_a3_remote_stage_manifest",
    "validate_a3_remote_stage_receipt",
    "validate_a3_transient_ranking_return_receipt",
]
