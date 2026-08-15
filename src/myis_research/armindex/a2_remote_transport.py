"""Hash-bound SSH transport for the A2 production executor.

The transport owns the host boundary: a CUDA-bound command is either sent to
the already-admitted Vast worker with a pinned host key, or it fails closed.
The local orchestrator keeps checkpoints and aggregate receipts; the remote
side returns one aggregate JSON object per candidate.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ..kernel.canonical import canonical_sha256

_HASH = re.compile(r"^[a-f0-9]{64}$")
_COMMIT = re.compile(r"^[a-f0-9]{40}$")
_REMOTE_ROOT = re.compile(r"^/opt/myis/a2-[a-z0-9][a-z0-9-]{7,63}$")
_HOST = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


class A2RemoteTransportError(ValueError):
    """Raised when the remote measured transport cannot prove its binding."""


def _ssh_path(path: Path) -> str:
    """Use a Windows short path so OpenSSH preserves spaces in user profiles."""

    if sys.platform != "win32":
        return str(path)
    try:
        import ctypes

        get_short = ctypes.windll.kernel32.GetShortPathNameW
        get_short.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
        get_short.restype = ctypes.c_uint32
        buffer = ctypes.create_unicode_buffer(1024)
        length = get_short(str(path), buffer, len(buffer))
        return buffer.value if length else str(path)
    except (AttributeError, OSError):
        return str(path)


def _hash(value: object, role: str) -> str:
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise A2RemoteTransportError(f"{role} hash is invalid")
    return value


@dataclass(frozen=True)
class RemoteTransportConfig:
    """All values needed to address the already-admitted remote worker."""

    provider_instance_id: str
    host: str
    port: int
    user: str
    key_path: Path
    known_hosts_path: Path
    remote_root: str
    remote_repository_root: str
    remote_owner_root: str
    remote_input_manifest: str
    remote_bundle_path: str
    remote_bundle_receipt_path: str
    remote_python_executable: str
    bundle_sha256: str
    bundle_receipt_sha256: str
    bundle_receipt_file_sha256: str
    git_commit: str
    git_tree: str
    measurement_authority_commitment_uri: str
    measurement_authority_commitment_file_sha256: str
    owner_manifest_sha256: str
    remote_input_manifest_sha256: str
    local_repository_root: str | None = None
    local_owner_root: str | None = None
    local_python_executable: str | None = None
    local_input_manifest: str | None = None

    def __post_init__(self) -> None:
        if self.provider_instance_id != "47700074":
            raise A2RemoteTransportError("remote transport is bound to Vast instance 47700074")
        if _HOST.fullmatch(self.host) is None or not self.user or not (1 <= self.port <= 65535):
            raise A2RemoteTransportError("remote SSH endpoint is invalid")
        if not self.key_path.is_file() or self.key_path.is_symlink():
            raise A2RemoteTransportError("remote SSH key path is unavailable")
        if self.known_hosts_path.is_symlink() or not self.known_hosts_path.is_file():
            raise A2RemoteTransportError("remote known-hosts path is unavailable")
        if _REMOTE_ROOT.fullmatch(self.remote_root) is None:
            raise A2RemoteTransportError("remote root is not an isolated A2 root")
        for value, role in (
            (self.bundle_sha256, "bundle"),
            (self.bundle_receipt_sha256, "bundle receipt"),
            (self.bundle_receipt_file_sha256, "bundle receipt file"),
            (
                self.measurement_authority_commitment_file_sha256,
                "measurement authority commitment file",
            ),
            (self.owner_manifest_sha256, "Owner-local input manifest"),
            (self.remote_input_manifest_sha256, "remote retrieval input manifest"),
        ):
            _hash(value, role)
        if _COMMIT.fullmatch(self.git_commit) is None or _COMMIT.fullmatch(self.git_tree) is None:
            raise A2RemoteTransportError("remote Git provenance is invalid")
        if not self.remote_repository_root.startswith(self.remote_root + "/"):
            raise A2RemoteTransportError("remote repository root must be under remote root")
        if not self.remote_owner_root.startswith(self.remote_root + "/"):
            raise A2RemoteTransportError("remote Owner root must be under remote root")
        if not self.remote_input_manifest.startswith(self.remote_owner_root + "/"):
            raise A2RemoteTransportError("remote input manifest must be under remote Owner root")
        for value, role in (
            (self.remote_bundle_path, "bundle"),
            (self.remote_bundle_receipt_path, "bundle receipt"),
            (self.remote_python_executable, "Python executable"),
        ):
            if not value.startswith(self.remote_root + "/"):
                raise A2RemoteTransportError(f"remote {role} path must be under remote root")
        if self.measurement_authority_commitment_uri != (
            "control/armindex/a2/measurement-authority-commitment.v1.json"
        ):
            raise A2RemoteTransportError("remote authority commitment URI is not canonical")

    def ssh_argv(self) -> list[str]:
        return [
            "ssh",
            "-i",
            _ssh_path(self.key_path),
            "-p",
            str(self.port),
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            f"UserKnownHostsFile={_ssh_path(self.known_hosts_path)}",
            f"{self.user}@{self.host}",
        ]


def build_transport_request(config: RemoteTransportConfig, *, attempt_id: str) -> dict[str, Any]:
    """Build a deterministic request that can be copied into a remote launcher."""

    if not re.fullmatch(r"^a2-[a-z0-9-]{7,63}$", attempt_id):
        raise A2RemoteTransportError("transport attempt ID is invalid")
    body = {
        "schema_version": "myis.armindex-a2-remote-measured-transport.v2",
        "request_id": f"{attempt_id}-remote-measured-transport-v2",
        "attempt_id": attempt_id,
        "provider_instance_id": config.provider_instance_id,
        "remote_root": config.remote_root,
        "remote_repository_root": config.remote_repository_root,
        "remote_owner_root": config.remote_owner_root,
        "remote_input_manifest": config.remote_input_manifest,
        "remote_bundle_path": config.remote_bundle_path,
        "remote_bundle_receipt_path": config.remote_bundle_receipt_path,
        "remote_python_executable": config.remote_python_executable,
        "bundle_sha256": config.bundle_sha256,
        "bundle_receipt_sha256": config.bundle_receipt_sha256,
        "bundle_receipt_file_sha256": config.bundle_receipt_file_sha256,
        "git_commit": config.git_commit,
        "git_tree": config.git_tree,
        "measurement_authority_commitment_uri": (
            config.measurement_authority_commitment_uri
        ),
        "measurement_authority_commitment_file_sha256": (
            config.measurement_authority_commitment_file_sha256
        ),
        "owner_manifest_sha256": config.owner_manifest_sha256,
        "remote_input_manifest_sha256": config.remote_input_manifest_sha256,
        "launch_mode": "remote_only_hash_bound",
        "protected_payload_returned": False,
        "candidate_evaluation_started": False,
        "rep_dev_measurement_started": False,
    }
    return {**body, "request_sha256": canonical_sha256(body)}


def validate_transport_request(request: Mapping[str, Any], config: RemoteTransportConfig, *, attempt_id: str) -> dict[str, Any]:
    checked = dict(request)
    expected = build_transport_request(config, attempt_id=attempt_id)
    if checked != expected:
        raise A2RemoteTransportError("remote transport request hash or binding drift")
    return checked


def validate_transport_adoption_binding(
    config: RemoteTransportConfig,
    *,
    attempt_id: str,
    adoption_receipt: Mapping[str, Any],
) -> None:
    """Fail before launch unless transport and adoption name one immutable bundle."""

    expected = {
        "attempt_id": attempt_id,
        "bundle_sha256": config.bundle_sha256,
        "bundle_receipt_sha256": config.bundle_receipt_sha256,
        "git_commit": config.git_commit,
        "git_tree": config.git_tree,
        "remote_root": config.remote_root,
    }
    actual = {key: adoption_receipt.get(key) for key in expected}
    if actual != expected or not config.remote_root.endswith(attempt_id):
        raise A2RemoteTransportError("remote transport differs from execution adoption")


def build_remote_validation_command(config: RemoteTransportConfig, *, attempt_id: str) -> str:
    """Return a side-effect-free remote proof command.

    The command checks bundle manifest provenance and process isolation only. It
    never imports the measured adapter and never opens an input manifest.
    """

    request = build_transport_request(config, attempt_id=attempt_id)
    encoded = json.dumps(request, sort_keys=True, separators=(",", ":"))
    return (
        "python - <<'PY'\n"
        "import hashlib, json, pathlib, subprocess\n"
        f"root=pathlib.Path({config.remote_repository_root!r})\n"
        f"bundle=pathlib.Path({config.remote_bundle_path!r})\n"
        f"bundle_receipt=pathlib.Path({config.remote_bundle_receipt_path!r})\n"
        f"input_manifest=pathlib.Path({config.remote_input_manifest!r})\n"
        f"request=json.loads({encoded!r})\n"
        "assert bundle.is_file()\n"
        "assert hashlib.sha256(bundle.read_bytes()).hexdigest()==request['bundle_sha256']\n"
        "assert bundle_receipt.is_file()\n"
        "assert hashlib.sha256(bundle_receipt.read_bytes()).hexdigest()==request['bundle_receipt_file_sha256']\n"
        "bundle_receipt_value=json.loads(bundle_receipt.read_text())\n"
        "assert bundle_receipt_value['receipt_sha256']==request['bundle_receipt_sha256']\n"
        "assert bundle_receipt_value['bundle_sha256']==request['bundle_sha256']\n"
        "assert bundle_receipt_value['git_commit']==request['git_commit']\n"
        "assert bundle_receipt_value['git_tree']==request['git_tree']\n"
        "assert input_manifest.is_file()\n"
        "assert hashlib.sha256(input_manifest.read_bytes()).hexdigest()==request['remote_input_manifest_sha256']\n"
        "remote_input=json.loads(input_manifest.read_text())\n"
        "assert remote_input.get('schema_version')=='myis.armindex-a2-remote-retrieval-input.v1'\n"
        "assert remote_input.get('attempt_id')==request['attempt_id']\n"
        "assert remote_input.get('owner_manifest_sha256')==request['owner_manifest_sha256']\n"
        "assert 'qrels' not in remote_input and 'membership' not in remote_input and 'evaluator' not in remote_input\n"
        "assert hashlib.sha256(json.dumps({k:v for k,v in remote_input.items() if k!='manifest_sha256'},sort_keys=True,separators=(',',':')).encode()).hexdigest()==remote_input['manifest_sha256']\n"
        "assert remote_input.get('retriever_code_sha256')==hashlib.sha256((root/'src/myis_research/armindex/a2_remote_retriever.py').read_bytes()).hexdigest()\n"
        "for name in ('corpus','queries'):\n"
        "    item=remote_input[name]; path=pathlib.Path(item['path']); assert path.is_file(); assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']\n"
        "manifest=json.loads((root/'BUNDLE_MANIFEST.json').read_text())\n"
        "assert manifest['git_commit']==request['git_commit']\n"
        "assert manifest['git_tree']==request['git_tree']\n"
        "body={key:value for key,value in manifest.items() if key!='bundle_manifest_sha256'}\n"
        "assert hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':')).encode()).hexdigest() == manifest['bundle_manifest_sha256']\n"
        "commitment=root/request['measurement_authority_commitment_uri']\n"
        "assert commitment.is_file()\n"
        "assert hashlib.sha256(commitment.read_bytes()).hexdigest()==request['measurement_authority_commitment_file_sha256']\n"
        "commitment_value=json.loads(commitment.read_text())\n"
        "assert commitment_value['status']=='MEASURED_EXECUTION_AUTHORITY_ABSENT_PENDING_AP'\n"
        "assert commitment_value['scientific_authority'] is False and commitment_value['measured_a2_authorized'] is False\n"
        "gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],capture_output=True,text=True).stdout\n"
        "a2=[]\n"
        "for cmdline in pathlib.Path('/proc').glob('[0-9]*/cmdline'):\n"
        "    try: argv=[x.decode(errors='replace') for x in cmdline.read_bytes().split(b'\\0') if x]\n"
        "    except OSError: continue\n"
        "    if '-m' in argv:\n"
        "        i=argv.index('-m'); module=argv[i+1] if i+1<len(argv) else ''\n"
        "        if module.startswith('myis_research.armindex.a2_'): a2.append(argv)\n"
        "out={'schema_version':'myis.armindex-a2-remote-transport-check.v1','status':'PASS_A2_REMOTE_TRANSPORT_CHECK','attempt_id':request['attempt_id'],'provider_instance_id':request['provider_instance_id'],'bundle_sha256':request['bundle_sha256'],'git_commit':manifest['git_commit'],'git_tree':manifest['git_tree'],'gpu_compute_process_count':len([x for x in gpu.splitlines() if x.strip()]),'a2_process_count':len(a2),'candidate_evaluation_started':False,'rep_dev_measurement_started':False,'protected_payload_returned':False}\n"
        "out['receipt_sha256']=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(',',':')).encode()).hexdigest()\n"
        "print(json.dumps(out,sort_keys=True,separators=(',',':')))\n"
        "PY"
    )


def validate_remote_transport_result(result: Mapping[str, Any], config: RemoteTransportConfig, *, attempt_id: str) -> dict[str, Any]:
    checked = dict(result)
    if checked.get("status") != "PASS_A2_REMOTE_TRANSPORT_CHECK" or checked.get("attempt_id") != attempt_id:
        raise A2RemoteTransportError("remote transport check did not pass")
    for key, expected in (("provider_instance_id", config.provider_instance_id), ("bundle_sha256", config.bundle_sha256), ("git_commit", config.git_commit), ("git_tree", config.git_tree)):
        if checked.get(key) != expected:
            raise A2RemoteTransportError(f"remote transport {key} drift")
    if any(checked.get(key) for key in ("candidate_evaluation_started", "rep_dev_measurement_started", "protected_payload_returned")):
        raise A2RemoteTransportError("remote transport check crossed a measured boundary")
    if checked.get("gpu_compute_process_count") != 0 or checked.get("a2_process_count") != 0:
        raise A2RemoteTransportError("remote transport check observed a live scientific worker")
    unsigned = {key: value for key, value in checked.items() if key != "receipt_sha256"}
    if checked.get("receipt_sha256") != canonical_sha256(unsigned):
        raise A2RemoteTransportError("remote transport result self-hash drift")
    return checked


@dataclass
class RemoteExecutor:
    """Callable adapter matching the local executor protocol."""

    config: RemoteTransportConfig
    attempt_id: str
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run
    owner_root: Path | None = None
    manifest_relative_path: str | None = None

    def __call__(self, command: Sequence[str], *, environment: Mapping[str, str], heartbeat_path: Path, process_path: Path, timeout_seconds: int) -> Mapping[str, Any]:
        del command
        remote_environment = {
            "PYTHONPATH": f"{self.config.remote_repository_root}/src",
            "MYIS_A2_ATTEMPT_ID": self.attempt_id,
            **{
                key: value
                for key, value in environment.items()
                if key
                in {
                    "PYTHONDONTWRITEBYTECODE",
                    "HF_HUB_OFFLINE",
                    "TRANSFORMERS_OFFLINE",
                    "PIP_NO_INDEX",
                    "MYIS_A2_CANDIDATE_ID",
                    "MYIS_A2_ARM_ID",
                    "MYIS_A2_PROGRAM_SHA256",
                }
            },
        }
        remote_command = shlex.join(
            [
                "env",
                *(f"{key}={value}" for key, value in remote_environment.items()),
                self.config.remote_python_executable,
                "-m",
                "myis_research.armindex.a2_remote_candidate",
                "--repository-root",
                self.config.remote_repository_root,
                "--input-manifest",
                self.config.remote_input_manifest,
                "--remote-root",
                self.config.remote_root,
                "--bundle-path",
                self.config.remote_bundle_path,
                "--bundle-receipt-path",
                self.config.remote_bundle_receipt_path,
                "--bundle-sha256",
                self.config.bundle_sha256,
                "--bundle-receipt-sha256",
                self.config.bundle_receipt_sha256,
                "--bundle-receipt-file-sha256",
                self.config.bundle_receipt_file_sha256,
                "--git-commit",
                self.config.git_commit,
                "--git-tree",
                self.config.git_tree,
                "--authority-commitment-uri",
                self.config.measurement_authority_commitment_uri,
                "--authority-commitment-file-sha256",
                self.config.measurement_authority_commitment_file_sha256,
                "--remote-input-manifest-sha256",
                self.config.remote_input_manifest_sha256,
                "--owner-manifest-sha256",
                self.config.owner_manifest_sha256,
                "--timeout-seconds",
                str(timeout_seconds),
            ]
        )
        local_state = {
            "attempt_id": self.attempt_id,
            "candidate_id": environment.get("MYIS_A2_CANDIDATE_ID", ""),
            "remote_lifecycle_root": f"{self.config.remote_root}/lifecycle",
            "request_sha256": build_transport_request(
                self.config, attempt_id=self.attempt_id
            )["request_sha256"],
            "status": "REMOTE_SUPERVISOR_REQUESTED",
        }
        _atomic_json(process_path, local_state)
        _atomic_json(
            heartbeat_path,
            {
                **local_state,
                "observed_at_utc": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
            },
        )
        try:
            result = self.runner(
                [*self.config.ssh_argv(), remote_command],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds + 60,
            )
        except BaseException:
            _atomic_json(process_path, {**local_state, "status": "REMOTE_TRANSPORT_INTERRUPTED"})
            raise
        if result.returncode != 0:
            _atomic_json(process_path, {**local_state, "status": "REMOTE_FAILED_CLOSED"})
            raise A2RemoteTransportError("remote measured executor failed closed")
        try:
            value = json.loads(result.stdout.strip())
        except json.JSONDecodeError as error:
            raise A2RemoteTransportError("remote measured executor returned invalid JSON") from error
        if not isinstance(value, Mapping):
            raise A2RemoteTransportError("remote measured executor output must be an object")
        _atomic_json(process_path, {**local_state, "status": "REMOTE_REAPED_WITH_DURABLE_RESULT"})
        _atomic_json(
            heartbeat_path,
            {
                **local_state,
                "status": "REMOTE_REAPED_WITH_DURABLE_RESULT",
                "observed_at_utc": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
            },
        )
        if self.owner_root is not None or self.manifest_relative_path is not None:
            if self.owner_root is None or self.manifest_relative_path is None:
                raise A2RemoteTransportError("Owner-local evaluation binding is incomplete")
            candidate_id = environment.get("MYIS_A2_CANDIDATE_ID", "")
            try:
                from .a2_owner_local_engine import evaluate_remote_retrieval_result

                return evaluate_remote_retrieval_result(
                    Path(self.config.local_repository_root or "."),
                    owner_root=self.owner_root,
                    manifest_relative_path=self.manifest_relative_path,
                    retrieval_result=value,
                    candidate_id=candidate_id,
                )
            except (OSError, ValueError) as error:
                raise A2RemoteTransportError("Owner-local evaluation failed closed") from error
        return dict(value)


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise A2RemoteTransportError("local remote-lifecycle evidence is a symlink")
    encoded = json.dumps(
        dict(value), ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ) + "\n"
    descriptor, name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


__all__ = [
    "A2RemoteTransportError",
    "RemoteExecutor",
    "RemoteTransportConfig",
    "build_remote_validation_command",
    "build_transport_request",
    "validate_remote_transport_result",
    "validate_transport_adoption_binding",
    "validate_transport_request",
]
