"""Local-only Official Codex SDK bridge for governed A2 preparation."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import re
import subprocess
import sys
import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_json, canonical_sha256, file_sha256

BRIDGE_SCHEMA_VERSION = "myis.armindex-official-codex-bridge.v1"
REQUEST_ENVELOPE_VERSION = "myis.armindex-official-codex-request.v1"
RESPONSE_ENVELOPE_VERSION = "myis.armindex-official-codex-response.v1"
EVENT_SCHEMA_VERSION = "myis.armindex-official-codex-event.v1"
CREDIT_SNAPSHOT_SCHEMA_VERSION = "myis.armindex-official-codex-credit-snapshot.v1"
SDK_PACKAGE = "openai-codex"
SDK_VERSION = "0.144.4"
MODEL = "gpt-5.6-sol"
REASONING_EFFORT = "high"
LOOPBACK_HOST = "127.0.0.1"
OPERATION_NAMES = (
    "representation_propose",
    "representation_review",
    "engineering_refactor_review",
)
LOCKED_AFTER_FREEZE = frozenset(
    {"representation_propose", "representation_review"}
)
_REQUEST_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{7,127}$")
_EVENT_LOCK = threading.Lock()
_SAFE_ENVIRONMENT_KEYS = (
    "APPDATA",
    "COMSPEC",
    "HOMEDRIVE",
    "HOMEPATH",
    "LOCALAPPDATA",
    "NUMBER_OF_PROCESSORS",
    "OS",
    "PATH",
    "PATHEXT",
    "PROCESSOR_ARCHITECTURE",
    "PROGRAMDATA",
    "SYSTEMDRIVE",
    "SYSTEMROOT",
    "TEMP",
    "TMP",
    "USERDOMAIN",
    "USERNAME",
    "USERPROFILE",
    "WINDIR",
)


class OfficialCodexBridgeError(RuntimeError):
    """Raised when the bridge fails closed."""


@dataclass(frozen=True)
class OperationSpec:
    name: str
    request_schema: Path
    response_schema: Path
    prompt_template: Path


@dataclass(frozen=True)
class BridgeIdentity:
    sdk_version: str
    runtime_user_agent: str
    cli_version: str
    model: str
    model_provider: str
    reasoning_effort: str

    def as_dict(self) -> dict[str, str]:
        return {
            "sdk_version": self.sdk_version,
            "runtime_user_agent": self.runtime_user_agent,
            "cli_version": self.cli_version,
            "model": self.model,
            "model_provider": self.model_provider,
            "reasoning_effort": self.reasoning_effort,
        }


@dataclass(frozen=True)
class BridgeConfig:
    repository_root: Path
    config_path: Path
    official_home: Path
    maxplus_home: Path
    event_root: Path
    freeze_lock: Path
    operations: Mapping[str, OperationSpec]
    event_store_pointer: str
    worker_timeout_seconds: int
    max_retries: int


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OfficialCodexBridgeError(f"invalid JSON file: {path}") from exc
    if not isinstance(value, dict):
        raise OfficialCodexBridgeError(f"JSON root must be an object: {path}")
    return value


def _validate_schema(instance: Mapping[str, Any], schema_path: Path) -> None:
    schema = _load_json(schema_path)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(instance)),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if errors:
        first = errors[0]
        location = ".".join(str(item) for item in first.absolute_path) or "$"
        raise OfficialCodexBridgeError(
            f"schema validation failed at {location}: {first.message}"
        )


def _resolved_child(parent: Path, relative: str) -> Path:
    candidate = (parent / relative).resolve()
    try:
        candidate.relative_to(parent.resolve())
    except ValueError as exc:
        raise OfficialCodexBridgeError(
            f"configured path escapes repository: {relative}"
        ) from exc
    return candidate


def load_bridge_config(
    repository_root: Path,
    *,
    config_path: Path | None = None,
    official_home: Path | None = None,
    maxplus_home: Path | None = None,
    event_root: Path | None = None,
) -> BridgeConfig:
    root = repository_root.resolve()
    path = (
        config_path.resolve()
        if config_path is not None
        else root / "control/armindex/a2/official-codex-bridge.v1.json"
    )
    value = _load_json(path)
    if value.get("schema_version") != BRIDGE_SCHEMA_VERSION:
        raise OfficialCodexBridgeError("bridge config schema_version mismatch")
    if value.get("host") != LOOPBACK_HOST:
        raise OfficialCodexBridgeError("Official Codex bridge must bind 127.0.0.1")
    if value.get("model") != MODEL or value.get("reasoning_effort") != REASONING_EFFORT:
        raise OfficialCodexBridgeError("bridge model or reasoning effort is not frozen")
    if value.get("sdk_package") != SDK_PACKAGE or value.get("sdk_version") != SDK_VERSION:
        raise OfficialCodexBridgeError("bridge SDK package/version is not frozen")
    declared_hash = value.get("config_sha256")
    unsigned = {key: item for key, item in value.items() if key != "config_sha256"}
    if declared_hash != canonical_sha256(unsigned):
        raise OfficialCodexBridgeError("bridge config self-hash mismatch")

    operations_value = value.get("operations")
    if not isinstance(operations_value, dict) or set(operations_value) != set(OPERATION_NAMES):
        raise OfficialCodexBridgeError("bridge operation registry is not the exact allowlist")
    operations: dict[str, OperationSpec] = {}
    for name in OPERATION_NAMES:
        item = operations_value.get(name)
        if not isinstance(item, dict):
            raise OfficialCodexBridgeError(f"missing operation config: {name}")
        request_schema = _resolved_child(root, str(item.get("request_schema", "")))
        response_schema = _resolved_child(root, str(item.get("response_schema", "")))
        prompt_template = _resolved_child(root, str(item.get("prompt_template", "")))
        expected_hashes = {
            "request_schema_sha256": file_sha256(request_schema),
            "response_schema_sha256": file_sha256(response_schema),
            "prompt_template_sha256": file_sha256(prompt_template),
        }
        for field, actual in expected_hashes.items():
            if item.get(field) != actual:
                raise OfficialCodexBridgeError(
                    f"operation {name} binding mismatch for {field}"
                )
        operations[name] = OperationSpec(
            name=name,
            request_schema=request_schema,
            response_schema=response_schema,
            prompt_template=prompt_template,
        )

    user_profile = Path(os.environ.get("USERPROFILE", str(Path.home()))).resolve()
    resolved_official = (official_home or user_profile / ".codex-official").resolve()
    resolved_maxplus = (maxplus_home or user_profile / ".codex").resolve()
    resolved_event_root = (
        event_root
        or user_profile
        / ".myis-research"
        / "official-codex-events"
        / str(value["event_store_id"])
    ).resolve()
    freeze_lock = _resolved_child(root, str(value["freeze_lock_path"]))
    config = BridgeConfig(
        repository_root=root,
        config_path=path,
        official_home=resolved_official,
        maxplus_home=resolved_maxplus,
        event_root=resolved_event_root,
        freeze_lock=freeze_lock,
        operations=operations,
        event_store_pointer=str(value["event_store_pointer"]),
        worker_timeout_seconds=int(value["worker_timeout_seconds"]),
        max_retries=int(value["max_retries"]),
    )
    validate_bridge_preflight(config)
    return config


def validate_bridge_preflight(config: BridgeConfig) -> dict[str, Any]:
    if config.official_home == config.maxplus_home:
        raise OfficialCodexBridgeError("Official and MaxPlus profiles must be distinct")
    for label, profile in (
        ("official", config.official_home),
        ("maxplus", config.maxplus_home),
    ):
        if not profile.is_dir() or not (profile / "config.toml").is_file():
            raise OfficialCodexBridgeError(f"{label} Codex profile is unavailable")
    try:
        config.event_root.relative_to(config.repository_root)
    except ValueError:
        pass
    else:
        raise OfficialCodexBridgeError("Owner-local event root must be outside Git")
    installed_sdk = importlib.metadata.version(SDK_PACKAGE)
    if installed_sdk != SDK_VERSION:
        raise OfficialCodexBridgeError(
            f"installed {SDK_PACKAGE} version {installed_sdk} != {SDK_VERSION}"
        )
    if config.worker_timeout_seconds < 1 or config.max_retries not in range(4):
        raise OfficialCodexBridgeError("bridge retry or timeout policy is invalid")
    return {
        "status": "PASS_OFFICIAL_CODEX_BRIDGE_PREFLIGHT",
        "host": LOOPBACK_HOST,
        "sdk_package": SDK_PACKAGE,
        "sdk_version": installed_sdk,
        "model": MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "operation_count": len(config.operations),
        "official_profile_present": True,
        "maxplus_profile_present": True,
        "profiles_distinct": True,
        "event_store_pointer": config.event_store_pointer,
        "protected_data_accessed": False,
        "measured_execution_performed": False,
        "parent_environment_mutated": False,
    }


def _render_prompt(spec: OperationSpec, payload: Mapping[str, Any]) -> str:
    template = spec.prompt_template.read_text(encoding="utf-8")
    marker = "{{OPERATION_PAYLOAD_JSON}}"
    if template.count(marker) != 1:
        raise OfficialCodexBridgeError(
            f"operation {spec.name} prompt requires exactly one payload marker"
        )
    return template.replace(marker, canonical_json(dict(payload)))


def build_child_environment(official_home: Path) -> dict[str, str]:
    environment = {
        key: os.environ[key]
        for key in _SAFE_ENVIRONMENT_KEYS
        if os.environ.get(key)
    }
    environment.update(
        {
            "CODEX_HOME": str(official_home),
            "HOME": str(Path(os.environ.get("USERPROFILE", str(Path.home())))),
            "NO_COLOR": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
        }
    )
    forbidden = {
        "MYIS_STORE",
        "MYIS_MLFLOW_STORE",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "AZURE_OPENAI_API_KEY",
    }
    if forbidden.intersection(environment):
        raise OfficialCodexBridgeError("forbidden credential/store environment escaped")
    return environment


def _write_exclusive(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise OfficialCodexBridgeError(f"append-only artifact already exists: {path.name}") from exc


def _append_event(path: Path, event: Mapping[str, Any]) -> None:
    line = (canonical_json(dict(event)) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    with _EVENT_LOCK, path.open("ab") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def _git_commit(repository_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )
    value = completed.stdout.strip()
    return value if completed.returncode == 0 and re.fullmatch(r"[a-f0-9]{40,64}", value) else "0" * 40


def _worker_command() -> list[str]:
    return [
        sys.executable,
        "-m",
        "myis_research.armindex.official_codex_bridge",
        "worker",
    ]


def _credit_worker_command() -> list[str]:
    return [
        sys.executable,
        "-m",
        "myis_research.armindex.official_codex_bridge",
        "credit-worker",
    ]


def _run_worker(
    config: BridgeConfig,
    worker_input: Mapping[str, Any],
) -> tuple[dict[str, Any], bytes, bytes, int]:
    environment = build_child_environment(config.official_home)
    completed = subprocess.run(
        _worker_command(),
        input=canonical_json(dict(worker_input)),
        cwd=config.repository_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=config.worker_timeout_seconds,
    )
    stdout = completed.stdout.encode("utf-8")
    stderr = completed.stderr.encode("utf-8")
    if completed.returncode != 0:
        error_type = completed.stderr.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]{0,127}", error_type):
            error_type = "UnknownWorkerError"
        raise OfficialCodexBridgeError(
            "Official Codex SDK worker failed with exit "
            f"{completed.returncode}: {error_type}"
        )
    try:
        response = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise OfficialCodexBridgeError("Official Codex SDK worker returned invalid JSON") from exc
    if not isinstance(response, dict):
        raise OfficialCodexBridgeError("Official Codex SDK worker response must be an object")
    return response, stdout, stderr, completed.returncode


def capture_official_credit_snapshot(
    config: BridgeConfig,
    checkpoint_id: str,
) -> dict[str, Any]:
    if not _REQUEST_ID.fullmatch(checkpoint_id):
        raise OfficialCodexBridgeError("credit checkpoint_id is not stable")
    completed = subprocess.run(
        _credit_worker_command(),
        input=canonical_json(
            {
                "schema_version": "myis.armindex-official-codex-credit-request.v1",
                "checkpoint_id": checkpoint_id,
                "model_name": MODEL,
                "sdk_version": SDK_VERSION,
            }
        ),
        cwd=config.repository_root,
        env=build_child_environment(config.official_home),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    if completed.returncode != 0:
        error_type = completed.stderr.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]{0,127}", error_type):
            error_type = "UnknownCreditWorkerError"
        normalized = error_type.casefold()
        if any(token in normalized for token in ("auth", "unauthorized", "forbidden")):
            failure_code = "OFFICIAL_CREDIT_AUTHENTICATION_FAILED"
        elif any(
            token in normalized
            for token in ("connection", "network", "timeout", "transport")
        ):
            failure_code = "OFFICIAL_CREDIT_TRANSPORT_FAILED"
        else:
            failure_code = "OFFICIAL_CREDIT_UNAVAILABLE"
        raise OfficialCodexBridgeError(
            f"{failure_code}: worker exit {completed.returncode}"
        )
    try:
        snapshot = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise OfficialCodexBridgeError(
            "OFFICIAL_CREDIT_MALFORMED_RESPONSE"
        ) from exc
    if not isinstance(snapshot, dict):
        raise OfficialCodexBridgeError("Official Codex credit snapshot must be an object")
    required = {
        "schema_version",
        "checkpoint_id",
        "observed_at_utc",
        "model_name",
        "sdk_version",
        "plan_type",
        "primary",
        "rate_limit_reached_type",
        "credits",
        "reset_credit_available_count",
        "limit_reached",
        "protected_data_accessed",
        "measured_execution_performed",
    }
    if set(snapshot) != required:
        raise OfficialCodexBridgeError("Official Codex credit snapshot shape changed")
    if (
        snapshot["schema_version"] != CREDIT_SNAPSHOT_SCHEMA_VERSION
        or snapshot["checkpoint_id"] != checkpoint_id
        or snapshot["model_name"] != MODEL
        or snapshot["sdk_version"] != SDK_VERSION
        or snapshot["protected_data_accessed"] is not False
        or snapshot["measured_execution_performed"] is not False
    ):
        raise OfficialCodexBridgeError("Official Codex credit snapshot identity changed")
    primary = snapshot.get("primary")
    if not isinstance(primary, dict) or set(primary) != {
        "used_percent",
        "remaining_percent",
        "window_duration_mins",
        "resets_at",
        "resets_at_utc",
    }:
        raise OfficialCodexBridgeError("Official Codex primary limit window is unavailable")
    if (
        snapshot.get("limit_reached") is not False
        or snapshot.get("rate_limit_reached_type") is not None
        or not isinstance(primary.get("remaining_percent"), int)
        or primary["remaining_percent"] <= 0
        or not isinstance(primary.get("resets_at"), int)
        or not str(primary.get("resets_at_utc", "")).endswith("Z")
    ):
        raise OfficialCodexBridgeError("Official Codex credit or rate limit is exhausted")
    snapshot["snapshot_sha256"] = canonical_sha256(snapshot)
    target = config.event_root / "credit-snapshots" / f"{checkpoint_id}.json"
    _write_exclusive(
        target,
        (canonical_json(snapshot) + "\n").encode("ascii"),
    )
    return {
        **snapshot,
        "snapshot_pointer": (
            f"{config.event_store_pointer.removesuffix('/events.jsonl')}"
            f"/credit-snapshots/{checkpoint_id}.json"
        ),
    }


def invoke_operation(
    config: BridgeConfig,
    operation: str,
    payload: Mapping[str, Any],
    *,
    retry_offset: int = 0,
) -> dict[str, Any]:
    if operation not in config.operations:
        raise OfficialCodexBridgeError("operation is not allowlisted")
    if operation in LOCKED_AFTER_FREEZE and config.freeze_lock.exists():
        raise OfficialCodexBridgeError(
            f"operation {operation} is locked after candidate freeze"
        )
    request_id = str(payload.get("request_id", ""))
    if not _REQUEST_ID.fullmatch(request_id):
        raise OfficialCodexBridgeError("request_id is not a stable identifier")
    spec = config.operations[operation]
    _validate_schema(payload, spec.request_schema)
    prompt = _render_prompt(spec, payload)
    response_schema = _load_json(spec.response_schema)
    request_envelope = {
        "schema_version": REQUEST_ENVELOPE_VERSION,
        "request_id": request_id,
        "operation": operation,
        "payload": dict(payload),
    }
    raw_request = (canonical_json(request_envelope) + "\n").encode("utf-8")
    prompt_bytes = prompt.encode("utf-8")
    last_error: Exception | None = None
    for retry_count in range(retry_offset, retry_offset + config.max_retries + 1):
        attempt_name = f"{request_id}.retry-{retry_count:02d}"
        attempt_root = config.event_root / operation / attempt_name
        started_at = _utc_now()
        _write_exclusive(attempt_root / "request.json", raw_request)
        _write_exclusive(attempt_root / "prompt.txt", prompt_bytes)
        worker_input = {
            "schema_version": "myis.armindex-official-codex-worker-request.v1",
            "request_id": request_id,
            "operation": operation,
            "prompt": prompt,
            "output_schema": response_schema,
            "model": MODEL,
            "reasoning_effort": REASONING_EFFORT,
            "sdk_version": SDK_VERSION,
            "work_directory": str(config.event_root / "workspace"),
        }
        stdout = b""
        stderr = b""
        try:
            worker_response, stdout, stderr, exit_code = _run_worker(config, worker_input)
            result = worker_response.get("result")
            identity_value = worker_response.get("identity")
            if not isinstance(result, dict) or not isinstance(identity_value, dict):
                raise OfficialCodexBridgeError("worker response is missing result/identity")
            _validate_schema(result, spec.response_schema)
            identity = BridgeIdentity(**identity_value)
            if (
                identity.sdk_version != SDK_VERSION
                or identity.model != MODEL
                or identity.reasoning_effort != REASONING_EFFORT
                or identity.model_provider != "openai"
            ):
                raise OfficialCodexBridgeError("Official model/provider/effort identity mismatch")
            completed_at = _utc_now()
            raw_response = (canonical_json(worker_response) + "\n").encode("utf-8")
            _write_exclusive(attempt_root / "response.json", raw_response)
            _write_exclusive(attempt_root / "stdout.log", stdout)
            _write_exclusive(attempt_root / "stderr.log", stderr)
            event: dict[str, Any] = {
                "schema_version": EVENT_SCHEMA_VERSION,
                "request_id": request_id,
                "operation": operation,
                "prompt_sha256": canonical_sha256(prompt),
                "template_sha256": file_sha256(spec.prompt_template),
                "input_sha256": canonical_sha256(dict(payload)),
                "response_sha256": canonical_sha256(result),
                "request_schema_sha256": file_sha256(spec.request_schema),
                "response_schema_sha256": file_sha256(spec.response_schema),
                "sdk_version": identity.sdk_version,
                "runtime_user_agent": identity.runtime_user_agent,
                "cli_version": identity.cli_version,
                "model": identity.model,
                "model_provider": identity.model_provider,
                "reasoning_effort": identity.reasoning_effort,
                "started_at": started_at,
                "completed_at": completed_at,
                "usage": worker_response.get("usage"),
                "retry_count": retry_count,
                "exit_code": exit_code,
                "verdict": "accepted",
                "git_commit": _git_commit(config.repository_root),
                "event_store_pointer": config.event_store_pointer,
                "protected_data_accessed": False,
                "measured_execution_performed": False,
            }
            event["event_sha256"] = canonical_sha256(event)
            _append_event(config.event_root / "events.jsonl", event)
            return {
                "schema_version": RESPONSE_ENVELOPE_VERSION,
                "request_id": request_id,
                "operation": operation,
                "status": "accepted",
                "result": result,
                "identity": identity.as_dict(),
                "usage": worker_response.get("usage"),
                "event_sha256": event["event_sha256"],
                "retry_count": retry_count,
                "protected_data_accessed": False,
                "measured_execution_performed": False,
            }
        except (OfficialCodexBridgeError, subprocess.SubprocessError) as exc:
            last_error = exc
            if stdout:
                _write_exclusive(attempt_root / "stdout.log", stdout)
            if stderr:
                _write_exclusive(attempt_root / "stderr.log", stderr)
            failure = {
                "schema_version": EVENT_SCHEMA_VERSION,
                "request_id": request_id,
                "operation": operation,
                "prompt_sha256": canonical_sha256(prompt),
                "template_sha256": file_sha256(spec.prompt_template),
                "input_sha256": canonical_sha256(dict(payload)),
                "response_sha256": None,
                "request_schema_sha256": file_sha256(spec.request_schema),
                "response_schema_sha256": file_sha256(spec.response_schema),
                "sdk_version": SDK_VERSION,
                "runtime_user_agent": None,
                "cli_version": None,
                "model": MODEL,
                "model_provider": "openai",
                "reasoning_effort": REASONING_EFFORT,
                "started_at": started_at,
                "completed_at": _utc_now(),
                "usage": None,
                "retry_count": retry_count,
                "exit_code": 70,
                "verdict": "retry" if retry_count < retry_offset + config.max_retries else "failed",
                "git_commit": _git_commit(config.repository_root),
                "event_store_pointer": config.event_store_pointer,
                "protected_data_accessed": False,
                "measured_execution_performed": False,
            }
            failure["event_sha256"] = canonical_sha256(failure)
            _append_event(config.event_root / "events.jsonl", failure)
    raise OfficialCodexBridgeError(
        f"Official Codex operation exhausted retries: {type(last_error).__name__}"
    ) from last_error


def _sdk_worker(worker_input: Mapping[str, Any]) -> dict[str, Any]:
    if worker_input.get("sdk_version") != SDK_VERSION:
        raise OfficialCodexBridgeError("worker SDK version mismatch")
    if worker_input.get("model") != MODEL or worker_input.get("reasoning_effort") != REASONING_EFFORT:
        raise OfficialCodexBridgeError("worker model/effort mismatch")
    if os.environ.get("CODEX_HOME") is None:
        raise OfficialCodexBridgeError("worker CODEX_HOME is missing")
    forbidden_present = [
        key
        for key in (
            "MYIS_STORE",
            "MYIS_MLFLOW_STORE",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "GOOGLE_API_KEY",
            "AZURE_OPENAI_API_KEY",
        )
        if key in os.environ
    ]
    if forbidden_present:
        raise OfficialCodexBridgeError("worker inherited a forbidden environment variable")
    work_directory = Path(str(worker_input["work_directory"])).resolve()
    work_directory.mkdir(parents=True, exist_ok=True)
    prompt = str(worker_input["prompt"])
    output_schema = worker_input["output_schema"]
    if not isinstance(output_schema, dict):
        raise OfficialCodexBridgeError("worker output schema must be an object")

    from openai_codex import ApprovalMode, Codex, CodexConfig, Sandbox, Thread
    from openai_codex._approval_mode import _approval_mode_settings
    from openai_codex._sandbox import _sandbox_mode
    from openai_codex.generated.v2_all import ReasoningEffort, ThreadStartParams

    approval_policy, approvals_reviewer = _approval_mode_settings(ApprovalMode.deny_all)
    with Codex(
        CodexConfig(
            cwd=str(work_directory),
            env={"CODEX_HOME": os.environ["CODEX_HOME"]},
            client_name="myis_official_codex_bridge",
            client_title="myIS Official Codex Bridge",
            client_version=SDK_VERSION,
        )
    ) as codex:
        params = ThreadStartParams(
            approval_policy=approval_policy,
            approvals_reviewer=approvals_reviewer,
            base_instructions=(
                "Return only the requested structured JSON. Do not inspect the filesystem, "
                "run commands, use tools, reveal hidden reasoning, or infer protected data."
            ),
            config={"model_reasoning_effort": REASONING_EFFORT},
            cwd=str(work_directory),
            ephemeral=True,
            model=MODEL,
            sandbox=_sandbox_mode(Sandbox.read_only),
        )
        started = codex._client.thread_start(params)
        observed_effort = (
            started.reasoning_effort.value
            if started.reasoning_effort is not None
            else None
        )
        if (
            started.model != MODEL
            or started.model_provider != "openai"
            or observed_effort != REASONING_EFFORT
        ):
            raise OfficialCodexBridgeError("thread start did not observe frozen identity")
        thread = Thread(codex._client, started.thread.id)
        result = thread.run(
            prompt,
            approval_mode=ApprovalMode.deny_all,
            cwd=str(work_directory),
            effort=ReasoningEffort.high,
            model=MODEL,
            output_schema=output_schema,
            sandbox=Sandbox.read_only,
        )
        if getattr(result.status, "value", str(result.status)) != "completed":
            raise OfficialCodexBridgeError("Official Codex turn did not complete")
        if not result.final_response:
            raise OfficialCodexBridgeError("Official Codex returned no final response")
        try:
            response = json.loads(result.final_response)
        except json.JSONDecodeError as exc:
            raise OfficialCodexBridgeError("Official Codex final response is not JSON") from exc
        if not isinstance(response, dict):
            raise OfficialCodexBridgeError("Official Codex response root must be an object")
        _validate_schema(response, _temporary_schema_path(output_schema, work_directory))
        usage = (
            result.usage.model_dump(mode="json", by_alias=True)
            if result.usage is not None
            else None
        )
        identity = BridgeIdentity(
            sdk_version=importlib.metadata.version(SDK_PACKAGE),
            runtime_user_agent=str(codex._init.userAgent or "unknown"),
            cli_version=str(started.thread.cli_version),
            model=str(started.model),
            model_provider=str(started.model_provider),
            reasoning_effort=str(observed_effort),
        )
    return {
        "schema_version": "myis.armindex-official-codex-worker-response.v1",
        "request_id": str(worker_input["request_id"]),
        "operation": str(worker_input["operation"]),
        "result": response,
        "identity": identity.as_dict(),
        "usage": usage,
        "environment_key_count": len(os.environ),
        "environment_allowlist_sha256": canonical_sha256(sorted(os.environ)),
        "protected_data_accessed": False,
        "measured_execution_performed": False,
    }


def _credit_worker(worker_input: Mapping[str, Any]) -> dict[str, Any]:
    if (
        worker_input.get("sdk_version") != SDK_VERSION
        or worker_input.get("model_name") != MODEL
    ):
        raise OfficialCodexBridgeError("credit worker model or SDK identity changed")
    checkpoint_id = str(worker_input.get("checkpoint_id", ""))
    if not _REQUEST_ID.fullmatch(checkpoint_id):
        raise OfficialCodexBridgeError("credit worker checkpoint_id is invalid")
    if os.environ.get("CODEX_HOME") is None:
        raise OfficialCodexBridgeError("credit worker CODEX_HOME is missing")
    if any(
        key in os.environ
        for key in (
            "MYIS_STORE",
            "MYIS_MLFLOW_STORE",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "GOOGLE_API_KEY",
            "AZURE_OPENAI_API_KEY",
        )
    ):
        raise OfficialCodexBridgeError(
            "credit worker inherited a forbidden environment variable"
        )

    from openai_codex import Codex, CodexConfig
    from openai_codex.generated.v2_all import GetAccountRateLimitsResponse

    with Codex(
        CodexConfig(
            cwd=str(Path.cwd()),
            env={"CODEX_HOME": os.environ["CODEX_HOME"]},
            client_name="myis_official_codex_bridge",
            client_title="myIS Official Codex Credit Check",
            client_version=SDK_VERSION,
        )
    ) as codex:
        response = codex._client.request(
            "account/rateLimits/read",
            None,
            response_model=GetAccountRateLimitsResponse,
        )
    value = response.model_dump(mode="json", by_alias=True)
    rate_limits = value.get("rateLimits")
    if not isinstance(rate_limits, dict):
        raise OfficialCodexBridgeError("credit worker rate limits are missing")
    primary = rate_limits.get("primary")
    if not isinstance(primary, dict):
        raise OfficialCodexBridgeError("credit worker primary window is missing")
    used_percent = primary.get("usedPercent")
    resets_at = primary.get("resetsAt")
    if not isinstance(used_percent, int) or not isinstance(resets_at, int):
        raise OfficialCodexBridgeError("credit worker primary window is incomplete")
    credits = rate_limits.get("credits")
    credit_summary = credits if isinstance(credits, dict) else {}
    reset_credits = value.get("rateLimitResetCredits")
    reset_summary = reset_credits if isinstance(reset_credits, dict) else {}
    reached_type = rate_limits.get("rateLimitReachedType")
    return {
        "schema_version": CREDIT_SNAPSHOT_SCHEMA_VERSION,
        "checkpoint_id": checkpoint_id,
        "observed_at_utc": _utc_now(),
        "model_name": MODEL,
        "sdk_version": importlib.metadata.version(SDK_PACKAGE),
        "plan_type": rate_limits.get("planType"),
        "primary": {
            "used_percent": used_percent,
            "remaining_percent": 100 - used_percent,
            "window_duration_mins": primary.get("windowDurationMins"),
            "resets_at": resets_at,
            "resets_at_utc": datetime.fromtimestamp(resets_at, UTC)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
        },
        "rate_limit_reached_type": reached_type,
        "credits": {
            "has_credits": bool(credit_summary.get("hasCredits", False)),
            "unlimited": bool(credit_summary.get("unlimited", False)),
        },
        "reset_credit_available_count": int(
            reset_summary.get("availableCount", 0)
        ),
        "limit_reached": reached_type is not None or used_percent >= 100,
        "protected_data_accessed": False,
        "measured_execution_performed": False,
    }


def _temporary_schema_path(schema: Mapping[str, Any], work_directory: Path) -> Path:
    path = work_directory / f"schema-{canonical_sha256(dict(schema))}.json"
    if not path.exists():
        path.write_text(canonical_json(dict(schema)) + "\n", encoding="utf-8", newline="\n")
    return path


class _BridgeHandler(BaseHTTPRequestHandler):
    server: OfficialCodexHTTPServer

    def do_GET(self) -> None:
        if self.path != "/healthz":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self._send_json(
            HTTPStatus.OK,
            {
                "status": "ready",
                "host": LOOPBACK_HOST,
                "operations": list(OPERATION_NAMES),
                "measured_execution_performed": False,
            },
        )

    def do_POST(self) -> None:
        prefix = "/v1/operations/"
        operation = self.path.removeprefix(prefix) if self.path.startswith(prefix) else ""
        if operation not in OPERATION_NAMES or self.path != prefix + operation:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 2 or length > 1024 * 1024:
                raise OfficialCodexBridgeError("request body size is invalid")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise OfficialCodexBridgeError("request payload must be an object")
            response = invoke_operation(self.server.bridge_config, operation, payload)
        except (OfficialCodexBridgeError, json.JSONDecodeError) as exc:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"status": "rejected", "error": type(exc).__name__},
            )
            return
        self._send_json(HTTPStatus.OK, response)

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _send_json(self, status: HTTPStatus, value: Mapping[str, Any]) -> None:
        body = (canonical_json(dict(value)) + "\n").encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class OfficialCodexHTTPServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], config: BridgeConfig) -> None:
        if address[0] != LOOPBACK_HOST:
            raise OfficialCodexBridgeError("bridge server address must be loopback")
        self.bridge_config = config
        super().__init__(address, _BridgeHandler)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("what-if", "serve"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--repository-root", type=Path, default=Path.cwd())
        sub.add_argument("--config", type=Path)
        sub.add_argument("--official-home", type=Path)
        sub.add_argument("--maxplus-home", type=Path)
        sub.add_argument("--event-root", type=Path)
        if command == "serve":
            sub.add_argument("--port", type=int, default=8765)
    subparsers.add_parser("worker")
    subparsers.add_parser("credit-worker")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.command == "worker":
        try:
            raw = json.loads(sys.stdin.read())
            if not isinstance(raw, dict):
                raise OfficialCodexBridgeError("worker input must be an object")
            sys.stdout.write(canonical_json(_sdk_worker(raw)) + "\n")
            return 0
        except Exception as exc:  # noqa: BLE001 - worker boundary must fail closed
            sys.stderr.write(type(exc).__name__ + "\n")
            return 70
    if args.command == "credit-worker":
        try:
            raw = json.loads(sys.stdin.read())
            if not isinstance(raw, dict):
                raise OfficialCodexBridgeError("credit worker input must be an object")
            sys.stdout.write(canonical_json(_credit_worker(raw)) + "\n")
            return 0
        except Exception as exc:  # noqa: BLE001 - worker boundary must fail closed
            sys.stderr.write(type(exc).__name__ + "\n")
            return 70
    config = load_bridge_config(
        args.repository_root,
        config_path=args.config,
        official_home=args.official_home,
        maxplus_home=args.maxplus_home,
        event_root=args.event_root,
    )
    if args.command == "what-if":
        sys.stdout.write(canonical_json(validate_bridge_preflight(config)) + "\n")
        return 0
    server = OfficialCodexHTTPServer((LOOPBACK_HOST, args.port), config)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 130
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
