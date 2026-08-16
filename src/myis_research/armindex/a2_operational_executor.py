"""Operational A2 orchestration with measured execution locked by default."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import tempfile
import time
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable

import yaml
from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a2_deployment_package import (
    A2DeploymentAssets,
    A2DeploymentPackageError,
    build_deployment_package,
    validate_deployment_package,
)
from .a2_execution_readiness import (
    A2ExecutionReadinessError,
    append_lifecycle_checkpoint,
    build_execution_adoption_receipt,
    build_execution_adoption_receipt_v2,
    build_execution_adoption_receipt_v3,
    build_execution_bundle,
    build_lifecycle_checkpoint,
    build_provider_admission_receipt,
    build_provider_admission_receipt_v2,
    build_provider_admission_receipt_v3,
    build_provider_instance_binding,
    build_safe_return_receipt,
    build_winner_receipt,
    build_watchdog_script,
    frozen_candidates,
    required_execution_bundle_paths,
    resume_checkpoint,
    validate_execution_adoption_receipt,
    validate_execution_adoption_receipt_v2,
    validate_execution_adoption_receipt_v3,
    validate_execution_bundle,
    validate_provider_admission_receipt,
    validate_provider_admission_receipt_v2,
    validate_provider_admission_receipt_v3,
)
from .autoindex import (
    AutoIndexState,
    advance_autoindex,
    strict_primary_improvement,
)
from .a2_measured_adapter import canonical_a1_incumbents, validate_owner_local_input
from .a2_remote_transport import (
    A2RemoteTransportError,
    RemoteExecutor,
    RemoteTransportConfig,
    build_remote_validation_command,
    build_transport_request,
    validate_remote_transport_result,
    validate_transport_adoption_binding,
)

_HASH = re.compile(r"^[a-f0-9]{64}$")
_ATTEMPT = re.compile(r"^a2-[a-z0-9-]{7,63}$")
_REMOTE_ROOT = re.compile(r"^/opt/myis/a2-[a-z0-9][a-z0-9-]{7,63}$")
_MAX_REMOTE_CLOCK_SKEW_SECONDS = 60
_HOST = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_OWNER_KEYS = {
    "VAST_HOST",
    "VAST_PORT",
    "VAST_USER",
    "SSH_KEY_PATH",
    "LOCAL_KNOWN_HOSTS_FILE",
}
_INITIAL_ADMISSION_TTL_SECONDS = 40 * 60 * 60
_RESERVE_TTL_RESERVE_SECONDS = 6 * 60 * 60
_AUTHORITY_PROVENANCE_POLICY = (
    "bundle_ancestor_with_unchanged_execution_closure_v1"
)
_AUTHORITY_V2 = "myis.armindex-a2-measured-execution-authority.v2"
_AUTHORITY_V3 = "myis.armindex-a2-measured-execution-authority.v3"
_AUTHORITY_V4 = "myis.armindex-a2-measured-execution-authority.v4"
_HYBRID_ARM_ROUTES = {
    "ARM-01": "remote_cpu_retrieval_return_to_owner_local_only",
    "ARM-02": "remote_retrieval_return_to_owner_local_only",
    "ARM-03": "remote_retrieval_return_to_owner_local_only",
    "ARM-04": "remote_retrieval_return_to_owner_local_only",
    "ARM-05": "remote_retrieval_return_to_owner_local_only",
}
_RESULT_FIELDS = {
    "schema_version",
    "attempt_id",
    "candidate_id",
    "arm_id",
    "program_sha256",
    "executor_output_sha256",
    "evaluator_input_sha256",
    "evaluator_sha256",
    "code_sha256",
    "model_sha256",
    "data_sha256",
    "primary_metric",
    "secondary_metrics",
    "latency",
    "cost",
    "coverage",
    "resume_count",
    "failure_count",
    "reserve_activation_passed",
    "reserve_activation_evidence_sha256",
    "train_only",
    "rep_dev_measured",
    "protected_payload_included",
    "per_query_outcomes_included",
}


class A2OperationalExecutorError(RuntimeError):
    """Raised when operational A2 work cannot proceed without crossing a lock."""


def _load_json(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A2OperationalExecutorError(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise A2OperationalExecutorError(f"{role} must be a JSON object")
    return value


def _validate(root: Path, schema_name: str, value: Mapping[str, Any]) -> None:
    schema = _load_json(root / "schemas/armindex" / schema_name, role=schema_name)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(value)),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if errors:
        raise A2OperationalExecutorError(
            f"{schema_name} validation failed: {errors[0].message}"
        )


def _freeze_bindings(root: Path) -> dict[str, str]:
    candidates = frozen_candidates(root)
    manifest = _load_json(
        root
        / "campaigns/armindex-multiretriever-v2/manifests/"
        "a2-five-arm-candidate-manifest.v1.json",
        role="candidate manifest",
    )
    receipt = _load_json(
        root
        / "campaigns/armindex-multiretriever-v2/evidence/"
        "a2-five-arm-candidate-freeze.receipt.v1.json",
        role="candidate freeze receipt",
    )
    lock = _load_json(
        root / "control/armindex/a2/candidate-freeze.lock.v1.json",
        role="candidate freeze lock",
    )
    if len(candidates) != 52:
        raise A2OperationalExecutorError("candidate freeze is incomplete")
    return {
        "manifest_sha256": str(manifest["manifest_sha256"]),
        "freeze_receipt_sha256": str(receipt["receipt_sha256"]),
        "lock_sha256": str(lock["lock_sha256"]),
    }


def _candidate_authority_bindings(root: Path) -> dict[str, str]:
    """Commit the exact frozen candidate membership, order, and program bytes."""

    candidates = frozen_candidates(root)
    ordered = list(candidates)
    if len(ordered) != 52:
        raise A2OperationalExecutorError("candidate freeze is incomplete")
    return {
        "candidate_ids_sha256": canonical_sha256(sorted(ordered)),
        "candidate_order_sha256": canonical_sha256(ordered),
        "candidate_program_hashes_sha256": canonical_sha256(
            [
                {"candidate_id": candidate_id, "program_sha256": candidates[candidate_id]["program_sha256"]}
                for candidate_id in ordered
            ]
        ),
    }


def _hash(value: object, *, role: str) -> str:
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise A2OperationalExecutorError(f"{role} must be a SHA-256")
    return value


def _decimal(value: object, *, role: str) -> str:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise A2OperationalExecutorError(f"{role} is invalid") from error
    if not number.is_finite() or number < 0:
        raise A2OperationalExecutorError(f"{role} is invalid")
    return format(number, "f")


def _write_json(path: Path, value: Mapping[str, Any]) -> Path:
    encoded = (
        json.dumps(dict(value), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + "\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_text(encoding="ascii") != encoded:
            raise A2OperationalExecutorError("immutable artifact already differs")
        return path
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
    return path


def _replace_json(path: Path, value: Mapping[str, Any]) -> Path:
    """Atomically replace mutable operational state such as a heartbeat."""

    encoded = (
        json.dumps(dict(value), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + "\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.is_symlink():
        raise A2OperationalExecutorError("mutable operational state is a symlink")
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
    return path


def load_owner_connection(path: Path) -> dict[str, Any]:
    """Load only connection fields; returned values must never be printed or committed."""

    values: dict[str, str] = {}
    try:
        lines = path.resolve(strict=True).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise A2OperationalExecutorError("owner connection file is unavailable") from error
    for line in lines:
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split(":", 1)
        if key in _OWNER_KEYS:
            values[key] = value.strip().strip('"')
    if set(values) != _OWNER_KEYS:
        raise A2OperationalExecutorError("owner connection fields are incomplete")
    if _HOST.fullmatch(values["VAST_HOST"]) is None:
        raise A2OperationalExecutorError("owner SSH host is invalid")
    try:
        port = int(values["VAST_PORT"])
    except ValueError as error:
        raise A2OperationalExecutorError("owner SSH port is invalid") from error
    if not 1 <= port <= 65535 or values["VAST_USER"] != "root":
        raise A2OperationalExecutorError("owner SSH identity is invalid")
    key = Path(values["SSH_KEY_PATH"])
    known_hosts = Path(values["LOCAL_KNOWN_HOSTS_FILE"])
    if (
        not key.is_file()
        or key.is_symlink()
        or not known_hosts.is_file()
        or known_hosts.is_symlink()
    ):
        raise A2OperationalExecutorError("owner SSH files are missing or unsafe")
    return {
        "host": values["VAST_HOST"],
        "port": port,
        "user": values["VAST_USER"],
        "key_path": key.resolve(),
        "known_hosts_path": known_hosts.resolve(),
    }


def _ssh_arguments(connection: Mapping[str, Any]) -> list[str]:
    return [
        "-i",
        str(connection["key_path"]),
        "-p",
        str(connection["port"]),
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        f"UserKnownHostsFile={connection['known_hosts_path']}",
        f"{connection['user']}@{connection['host']}",
    ]


def _scp_arguments(connection: Mapping[str, Any]) -> list[str]:
    return [
        "-i",
        str(connection["key_path"]),
        "-P",
        str(connection["port"]),
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        f"UserKnownHostsFile={connection['known_hosts_path']}",
    ]


def _native(
    executable: str,
    arguments: Sequence[str],
    *,
    role: str,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str:
    result = runner(
        [executable, *arguments],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise A2OperationalExecutorError(f"{role} failed closed")
    return result.stdout.strip()


def _git(repository_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository_root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise A2OperationalExecutorError("measurement authority Git provenance is invalid")
    return result.stdout.strip()


def _validate_measurement_authority_provenance(
    repository_root: Path, authority: Mapping[str, Any]
) -> None:
    authority_uri = str(authority["authority_uri"])
    authority_path = repository_root / authority_uri
    if authority_path.is_symlink() or not authority_path.is_file():
        raise A2OperationalExecutorError("measurement authority is not canonical and tracked")
    if _load_json(authority_path, role="measurement authority") != dict(authority):
        raise A2OperationalExecutorError("measurement authority bytes differ from canonical control")
    if _git(repository_root, "rev-parse", "--abbrev-ref", "HEAD") != "main":
        raise A2OperationalExecutorError("measurement authority requires main")
    head = _git(repository_root, "rev-parse", "HEAD^{commit}")
    if _git(repository_root, "rev-parse", "origin/main^{commit}") != head:
        raise A2OperationalExecutorError("measurement authority requires pushed origin/main")
    if _git(repository_root, "status", "--porcelain=v1"):
        raise A2OperationalExecutorError("measurement authority requires a clean worktree")
    _git(repository_root, "ls-files", "--error-unmatch", "--", authority_uri)
    if _git(repository_root, "hash-object", "--", authority_uri) != _git(
        repository_root, "rev-parse", f"HEAD:{authority_uri}"
    ):
        raise A2OperationalExecutorError("measurement authority is not bound to HEAD")
    _validate_bundle_authority_lineage(repository_root, authority, head=head)


def _validate_bundle_authority_lineage(
    repository_root: Path,
    authority: Mapping[str, Any],
    *,
    head: str,
) -> None:
    """Allow post-bundle authority commits without allowing executor drift."""

    bundle_commit = str(authority["execution_bundle_git_commit"])
    bundle_tree = str(authority["execution_bundle_git_tree"])
    if authority.get("provenance_policy") != _AUTHORITY_PROVENANCE_POLICY:
        raise A2OperationalExecutorError("measurement authority provenance policy drift")
    if _git(repository_root, "rev-parse", f"{bundle_commit}^{{commit}}") != bundle_commit:
        raise A2OperationalExecutorError("measurement authority bundle commit is unavailable")
    if _git(repository_root, "rev-parse", f"{bundle_commit}^{{tree}}") != bundle_tree:
        raise A2OperationalExecutorError("measurement authority bundle tree drift")
    if _git(repository_root, "merge-base", bundle_commit, head) != bundle_commit:
        raise A2OperationalExecutorError(
            "measurement authority bundle commit is not an ancestor of HEAD"
        )
    changed = _git(
        repository_root,
        "diff",
        "--name-only",
        bundle_commit,
        head,
        "--",
        *required_execution_bundle_paths(),
    )
    if changed:
        raise A2OperationalExecutorError(
            "measurement authority execution bundle closure drift"
        )


def _validate_measurement_goal(authority: Mapping[str, Any], goal_path: Path) -> None:
    try:
        text = goal_path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            raise ValueError("missing front matter")
        goal = yaml.safe_load(text.split("---\n", 2)[1])
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
        raise A2OperationalExecutorError("measurement authority goal is invalid") from error
    if (
        not isinstance(goal, Mapping)
        or goal.get("scientific_authority") is not True
        or goal.get("measured_a2_authorized") is not True
        or goal.get("measurement_authority_uri") != authority["authority_uri"]
        or goal.get("status") != "READY_FOR_MEASURED_EXECUTION"
    ):
        raise A2OperationalExecutorError("measurement authority goal does not authorize execution")


def validate_owner_local_evaluation_authority(
    repository_root: Path,
    *,
    authority: Mapping[str, Any],
    owner_manifest_path: Path,
    candidate_id: str | None = None,
    execution_route: str | None = None,
) -> dict[str, Any]:
    """Allow the protected evaluator only after a successor local authorization.

    This runs before the Owner-local evaluator opens qrels, membership, or the
    query token map.  It intentionally accepts no v2 compatibility path.
    """

    root = repository_root.resolve()
    checked = dict(authority)
    schema_version = checked.get("schema_version")
    if schema_version not in {_AUTHORITY_V3, _AUTHORITY_V4}:
        raise A2OperationalExecutorError(
            "Owner-local aggregate evaluation requires successor authority v3 or v4"
        )
    _validate(
        root,
        "a2-measured-execution-authority.v4.json"
        if schema_version == _AUTHORITY_V4
        else "a2-measured-execution-authority.v3.json",
        checked,
    )
    if (
        checked["candidate_generation_allowed"] is not False
        or checked["candidate_mutation_allowed"] is not False
        or checked["candidate_evaluation_allowed"] is not True
        or checked["rep_dev_measurement_allowed"] is not True
        or checked["evaluation_location"] != "owner_local_only"
        or checked["evaluation_transition"]
        != "remote_retrieval_return_to_owner_local_only"
        or checked["evaluation_output_class"] != "aggregate_safe_only"
        or checked["a3_allowed"] is not False
        or checked["selection_allowed"] is not False
        or checked["final_allowed"] is not False
        or checked["candidate_bindings"] != _candidate_authority_bindings(root)
        or checked["freeze_bindings"] != _freeze_bindings(root)
        or checked["authority_sha256"]
        != canonical_sha256(
            {key: value for key, value in checked.items() if key != "authority_sha256"}
        )
    ):
        raise A2OperationalExecutorError("Owner-local aggregate evaluation authority drift")
    if schema_version == _AUTHORITY_V4:
        if (
            checked["authority_id"] != "a2-measured-execution-authority-v4"
            or checked["arm_execution_routes"] != _HYBRID_ARM_ROUTES
            or checked["official_codex_mode"] != "pre_freeze_lineage_only"
            or checked["max_concurrent_arms"] != 5
            or checked["max_active_candidates_per_arm"] != 1
            or checked["receipt_commit_order"] != "frozen_candidate_order"
            or candidate_id is None
            or execution_route is None
        ):
            raise A2OperationalExecutorError("hybrid Owner-local evaluation authority drift")
        candidate = frozen_candidates(root).get(candidate_id)
        if (
            candidate is None
            or checked["arm_execution_routes"].get(candidate["arm_id"])
            != execution_route
        ):
            raise A2OperationalExecutorError("hybrid Owner-local route is invalid")
    path = owner_manifest_path.resolve(strict=True)
    if path.is_symlink() or not path.is_file():
        raise A2OperationalExecutorError("Owner-local evaluation manifest is unsafe")
    if (
        file_sha256(path)
        != checked["owner_local_evaluation_bindings"]["owner_manifest_file_sha256"]
    ):
        raise A2OperationalExecutorError("Owner-local evaluation manifest binding drift")
    return checked


def validate_owner_local_evaluation_manifest_binding(
    authority: Mapping[str, Any], manifest: Mapping[str, Any]
) -> None:
    """Check manifest commitments before protected evaluation inputs are opened."""

    bindings = authority["owner_local_evaluation_bindings"]
    artifacts = manifest.get("owner_artifacts")
    if not isinstance(artifacts, Mapping) or manifest.get("manifest_sha256") != bindings[
        "owner_manifest_sha256"
    ]:
        raise A2OperationalExecutorError("Owner-local evaluation manifest commitment drift")
    expected = {
        "evaluator_sha256": artifacts.get("evaluator", {}).get("binding_sha256"),
        "qrels_commitment_sha256": artifacts.get("qrels", {}).get("binding_sha256"),
        "membership_commitment_sha256": artifacts.get("membership", {}).get("binding_sha256"),
        "token_map_commitment_sha256": artifacts.get("queries", {}).get("binding_sha256"),
        "runtime_sha256": artifacts.get("runtime", {}).get("binding_sha256"),
        "model_lockset_sha256": artifacts.get("model_lockset", {}).get("binding_sha256"),
        "data_handoff_sha256": artifacts.get("data_handoff", {}).get("binding_sha256"),
    }
    if any(bindings[key] != value for key, value in expected.items()):
        raise A2OperationalExecutorError("Owner-local evaluation artifact commitment drift")


def validate_measurement_authority(
    repository_root: Path,
    authority: Mapping[str, Any],
    *,
    attempt_id: str,
    execution_adoption_receipt_sha256: str,
    execution_bundle_git_commit: str,
    execution_bundle_git_tree: str,
) -> dict[str, Any]:
    """Validate the separate AP-adopted authority required after staging."""

    root = repository_root.resolve()
    checked = dict(authority)
    schema_version = checked.get("schema_version")
    if schema_version not in {_AUTHORITY_V2, _AUTHORITY_V3, _AUTHORITY_V4}:
        raise A2OperationalExecutorError(
            "measured execution authority provenance v1 is superseded"
        )
    _validate(
        root,
        (
            "a2-measured-execution-authority.v4.json"
            if schema_version == _AUTHORITY_V4
            else "a2-measured-execution-authority.v3.json"
        )
        if schema_version != _AUTHORITY_V2
        else "a2-measured-execution-authority.v2.json",
        checked,
    )
    common_invalid = (
        checked["status"] != "PASS_A2_MEASURED_EXECUTION_AUTHORIZED"
        or checked["attempt_id"] != attempt_id
        or checked["execution_adoption_receipt_sha256"]
        != execution_adoption_receipt_sha256
        or checked["execution_bundle_git_commit"] != execution_bundle_git_commit
        or checked["execution_bundle_git_tree"] != execution_bundle_git_tree
        or checked["provenance_policy"] != _AUTHORITY_PROVENANCE_POLICY
        or checked["measured_a2_authorized"] is not True
        or checked["candidate_generation_allowed"] is not False
        or checked["candidate_mutation_allowed"] is not False
        or checked["a3_allowed"] is not False
        or checked["selection_allowed"] is not False
        or checked["final_allowed"] is not False
        or checked["freeze_bindings"] != _freeze_bindings(root)
        or checked["authority_sha256"]
        != canonical_sha256(
            {key: value for key, value in checked.items() if key != "authority_sha256"}
        )
    )
    if schema_version == _AUTHORITY_V2:
        version_invalid = (
            checked["authority_id"] != "a2-measured-execution-authority-v2"
            or checked["rep_dev_measurement_allowed"] is not False
        )
    elif schema_version == _AUTHORITY_V3:
        version_invalid = (
            checked["authority_id"] != "a2-measured-execution-authority-v3"
            or checked["candidate_evaluation_allowed"] is not True
            or checked["rep_dev_measurement_allowed"] is not True
            or checked["evaluation_location"] != "owner_local_only"
            or checked["evaluation_transition"]
            != "remote_retrieval_return_to_owner_local_only"
            or checked["evaluation_output_class"] != "aggregate_safe_only"
            or checked["candidate_bindings"] != _candidate_authority_bindings(root)
        )
    else:
        version_invalid = (
            checked["authority_id"] != "a2-measured-execution-authority-v4"
            or checked["candidate_evaluation_allowed"] is not True
            or checked["rep_dev_measurement_allowed"] is not True
            or checked["evaluation_location"] != "owner_local_only"
            or checked["evaluation_transition"]
            != "remote_retrieval_return_to_owner_local_only"
            or checked["evaluation_output_class"] != "aggregate_safe_only"
            or checked["candidate_bindings"] != _candidate_authority_bindings(root)
            or checked["arm_execution_routes"] != _HYBRID_ARM_ROUTES
            or checked["official_codex_mode"] != "pre_freeze_lineage_only"
            or checked["max_concurrent_arms"] != 5
            or checked["max_active_candidates_per_arm"] != 1
            or checked["receipt_commit_order"] != "frozen_candidate_order"
        )
    if (
        common_invalid
        or version_invalid
    ):
        raise A2OperationalExecutorError("measured execution authority is not adopted")
    _validate_measurement_authority_provenance(root, checked)
    goal_path = root / checked["source_goal_uri"]
    if (
        not goal_path.is_file()
        or goal_path.is_symlink()
        or file_sha256(goal_path) != checked["source_goal_sha256"]
    ):
        raise A2OperationalExecutorError("measured execution authority goal binding drift")
    _validate_measurement_goal(checked, goal_path)
    # The AP authority starts the measured attempt only.  It must not decide a
    # conditional batch before the two frozen matched batches have outcomes.
    if checked["active_reserve_candidate_ids"] or checked[
        "reserve_activation_evidence_sha256"
    ] is not None:
        raise A2OperationalExecutorError(
            "initial measurement authority cannot pre-activate conditional reserves"
        )
    return checked


@contextmanager
def _attempt_lock(path: Path) -> Any:
    """Hold one OS-released lock; no PID liveness probe is used on Windows."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise A2OperationalExecutorError("another executor owns the attempt lock") from error
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _executor_environment(candidate: Mapping[str, Any]) -> dict[str, str]:
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
        "PYTHONDONTWRITEBYTECODE": "1",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "PIP_NO_INDEX": "1",
        "MYIS_A2_CANDIDATE_ID": str(candidate["candidate_id"]),
        "MYIS_A2_ARM_ID": str(candidate["arm_id"]),
        "MYIS_A2_PROGRAM_SHA256": str(candidate["program_sha256"]),
    }
    if os.name == "nt":
        for name in ("SystemRoot", "TEMP", "TMP"):
            if os.environ.get(name):
                environment[name] = os.environ[name]
    return environment


def _run_executor_process(
    command: Sequence[str],
    *,
    environment: Mapping[str, str],
    heartbeat_path: Path,
    process_path: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    if not command or timeout_seconds <= 0:
        raise A2OperationalExecutorError("external executor command or timeout is invalid")
    process = subprocess.Popen(
        list(command),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=dict(environment),
        close_fds=True,
    )
    launched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    _write_json(
        process_path,
        {
            "pid": process.pid,
            "launched_at_utc": launched_at,
            "command_sha256": canonical_sha256(list(command)),
            "owned_popen_handle": True,
        },
    )
    deadline = time.monotonic() + timeout_seconds
    try:
        while process.poll() is None:
            _replace_json(
                heartbeat_path,
                {
                    "pid": process.pid,
                    "launched_at_utc": launched_at,
                    "observed_at_utc": datetime.now(timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z"),
                    "owned_popen_handle": True,
                },
            )
            if time.monotonic() >= deadline:
                process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                raise A2OperationalExecutorError("external executor timed out and was reaped")
            time.sleep(0.05)
        stdout, _stderr = process.communicate()
    except BaseException:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        raise
    if process.returncode != 0:
        raise A2OperationalExecutorError("external executor failed and was reaped")
    try:
        value = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise A2OperationalExecutorError("external executor output is invalid JSON") from error
    if not isinstance(value, dict):
        raise A2OperationalExecutorError("external executor output must be an object")
    return value


def execute_external_candidate_set(
    repository_root: Path,
    *,
    attempt_id: str,
    adoption_receipt: Mapping[str, Any],
    measurement_authority: Mapping[str, Any],
    command_template: Sequence[str],
    output_directory: Path,
    checkpoint_ledger: Path,
    owner_local_root: Path | None = None,
    owner_input_manifest: str | None = None,
    python_executable: str | None = None,
    reserve_budget_admission: Mapping[str, Any] | None = None,
    arm_incumbents: Mapping[str, Mapping[str, Any]] | None = None,
    now_utc: datetime | None = None,
    timeout_seconds: int = 21600,
    executor: Callable[..., Mapping[str, Any]] = _run_executor_process,
) -> dict[str, Any]:
    """Run the frozen external executor with resumable aggregate-only receipts."""

    root = repository_root.resolve()
    adoption = validate_execution_adoption_receipt(root, adoption_receipt)
    authority = validate_measurement_authority(
        root,
        measurement_authority,
        attempt_id=attempt_id,
        execution_adoption_receipt_sha256=adoption["receipt_sha256"],
        execution_bundle_git_commit=adoption["git_commit"],
        execution_bundle_git_tree=adoption["git_tree"],
    )
    if adoption["attempt_id"] != attempt_id:
        raise A2OperationalExecutorError("executor attempt differs from adoption")
    if authority["schema_version"] == _AUTHORITY_V4 and not isinstance(executor, RemoteExecutor):
        raise A2OperationalExecutorError(
            "hybrid v4 execution requires the bound RemoteExecutor"
        )
    if isinstance(executor, RemoteExecutor):
        validate_remote_execution_binding(
            root,
            config=executor.config,
            attempt_id=attempt_id,
            adoption_receipt=adoption,
            measurement_authority=authority,
        )
        if authority["schema_version"] not in {_AUTHORITY_V3, _AUTHORITY_V4}:
            raise A2OperationalExecutorError(
                "v2 authority cannot reach Owner-local candidate evaluation"
            )
        if executor.owner_root is None or executor.manifest_relative_path is None:
            raise A2OperationalExecutorError(
                "successor authority requires a complete Owner-local evaluation binding"
            )
        executor.measurement_authority = authority
    elif authority["schema_version"] == _AUTHORITY_V3 and owner_local_root is not None:
        raise A2OperationalExecutorError(
            "successor authority requires remote retrieval before Owner-local evaluation"
        )
    output = output_directory.resolve()
    if output.is_relative_to(root):
        raise A2OperationalExecutorError("external executor working output must remain Owner-local")
    if not command_template or any(not isinstance(item, str) or not item for item in command_template):
        raise A2OperationalExecutorError("external executor argv template is invalid")
    allowed_template_fields = {
        "{candidate_id}",
        "{arm_id}",
        "{program_sha256}",
        "{owner_local_root}",
        "{owner_local_input_manifest}",
        "{python_executable}",
        "{repository_root}",
    }
    if any("{" in item and item not in allowed_template_fields for item in command_template):
        raise A2OperationalExecutorError("external executor argv contains an unknown placeholder")
    if ("{owner_local_root}" in command_template or "{owner_local_input_manifest}" in command_template) and (
        owner_local_root is None or owner_input_manifest is None
    ):
        raise A2OperationalExecutorError("production adapter requires Owner-local input binding")
    if "{python_executable}" in command_template and not python_executable:
        raise A2OperationalExecutorError("production adapter requires a validated runtime interpreter")
    candidates = frozen_candidates(root)
    receipts_directory = output / "receipts"
    processes_directory = output / "processes"
    heartbeats_directory = output / "heartbeats"
    receipts_directory.mkdir(parents=True, exist_ok=True)
    completed: dict[str, dict[str, Any]] = {}
    for path in sorted(receipts_directory.glob("*.json")):
        receipt = _load_json(path, role="candidate result receipt")
        candidate_id = receipt.get("candidate_id")
        if candidate_id not in candidates:
            raise A2OperationalExecutorError("resume receipt is outside frozen membership")
        _validate(root, "a2-candidate-result-receipt.v1.json", receipt)
        if receipt.get("receipt_sha256") != canonical_sha256(
            {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        ):
            raise A2OperationalExecutorError("resume receipt hash drift")
        if (
            receipt.get("attempt_id") != attempt_id
            or receipt.get("evidence_class") != "measured_development_aggregate"
            or receipt.get("scientific_authority") is not True
            or receipt.get("code_sha256") != adoption["bundle_sha256"]
            or receipt.get("evaluator_sha256") != authority["authority_sha256"]
            or receipt.get("freeze_bindings") != _freeze_bindings(root)
        ):
            raise A2OperationalExecutorError(
                "resume receipt differs from attempt, adoption, or authority"
            )
        completed[str(candidate_id)] = receipt
    ledger = checkpoint_ledger.resolve()
    sequence = 0
    previous: str | None = None
    if ledger.exists():
        resumed = resume_checkpoint(ledger, attempt_id=attempt_id)
        sequence = int(resumed["sequence"])
        previous = str(resumed["checkpoint_sha256"])
        if int(resumed["completed_candidate_count"]) != len(completed):
            raise A2OperationalExecutorError("resume checkpoint differs from durable receipts")
    else:
        genesis = build_lifecycle_checkpoint(
            root,
            attempt_id=attempt_id,
            sequence=1,
            status="RUNNING",
            completed_candidate_count=len(completed),
            failed_candidate_count=0,
            resume_allowed=True,
        )
        append_lifecycle_checkpoint(ledger, genesis)
        sequence = 1
        previous = genesis["checkpoint_sha256"]
    matched_ids = _matched_candidate_ids(candidates)
    reserve_ids = tuple(
        candidate_id for candidate_id in candidates if candidate_id not in matched_ids
    )
    if any(candidate_id in completed for candidate_id in reserve_ids) and not (
        output / "reserve-activation-decision.v1.json"
    ).is_file():
        raise A2OperationalExecutorError("reserve receipt exists before activation decision")

    def execute_candidate(candidate_id: str, *, sequence_hint: int) -> dict[str, Any]:
        candidate = candidates[candidate_id]
        command = [
            item.format(
                candidate_id=candidate_id,
                arm_id=candidate["arm_id"],
                program_sha256=candidate["program_sha256"],
                owner_local_root=(
                    str(owner_local_root.resolve()) if owner_local_root is not None else ""
                ),
                owner_local_input_manifest=owner_input_manifest or "",
                python_executable=python_executable or "",
                repository_root=str(root),
            )
            for item in command_template
        ]
        kwargs = {
            "environment": _executor_environment(candidate),
            "heartbeat_path": heartbeats_directory / f"{candidate_id}.attempt-{sequence_hint:04d}.json",
            "process_path": processes_directory / f"{candidate_id}.attempt-{sequence_hint:04d}.json",
            "timeout_seconds": timeout_seconds,
        }
        return dict(executor(command, **kwargs))

    def record(
        candidate_id: str,
        *,
        active_reserve: bool = False,
        decision_sha256: str | None = None,
        executed_row: Mapping[str, Any] | None = None,
    ) -> None:
        nonlocal sequence, previous
        candidate = candidates[candidate_id]
        if candidate["tier"] == "conditional_reserve" and not active_reserve:
            row: dict[str, Any] = {
                "schema_version": "myis.armindex-a2-external-candidate-result.v1",
                "attempt_id": attempt_id,
                "candidate_id": candidate_id,
                "arm_id": candidate["arm_id"],
                "program_sha256": candidate["program_sha256"],
                "executor_output_sha256": canonical_sha256([candidate_id, "dormant"]),
                "evaluator_input_sha256": canonical_sha256([candidate_id, "dormant-input"]),
                "evaluator_sha256": authority["authority_sha256"],
                "code_sha256": adoption["bundle_sha256"],
                "model_sha256": "0" * 64,
                "data_sha256": "0" * 64,
                "primary_metric": None,
                "secondary_metrics": None,
                "latency": None,
                "cost": None,
                "coverage": {"expected_units": 1, "completed_units": 0},
                "resume_count": 0,
                "failure_count": 0,
                "reserve_activation_passed": False,
                "reserve_activation_evidence_sha256": decision_sha256,
                "train_only": False,
                "rep_dev_measured": True,
                "protected_payload_included": False,
                "per_query_outcomes_included": False,
            }
        else:
            try:
                row = (
                    dict(executed_row)
                    if executed_row is not None
                    else execute_candidate(candidate_id, sequence_hint=sequence + 1)
                )
            except BaseException:
                paused = build_lifecycle_checkpoint(
                    root, attempt_id=attempt_id, sequence=sequence + 1, status="PAUSED",
                    completed_candidate_count=len(completed), failed_candidate_count=1,
                    resume_allowed=True, previous_checkpoint_sha256=previous,
                )
                append_lifecycle_checkpoint(ledger, paused)
                raise
            if active_reserve:
                row["reserve_activation_passed"] = True
                row["reserve_activation_evidence_sha256"] = decision_sha256
        receipt = build_candidate_result_receipt(
            root, result=row, evidence_class="measured_development_aggregate",
            measurement_authority=authority, execution_adoption_receipt=adoption,
        )
        _write_json(receipts_directory / f"{candidate_id}.json", receipt)
        completed[candidate_id] = receipt
        sequence += 1
        checkpoint = build_lifecycle_checkpoint(
            root, attempt_id=attempt_id, sequence=sequence, status="RUNNING",
            completed_candidate_count=len(completed), failed_candidate_count=0,
            resume_allowed=True, previous_checkpoint_sha256=previous,
        )
        append_lifecycle_checkpoint(ledger, checkpoint)
        previous = checkpoint["checkpoint_sha256"]

    def run_stage(candidate_ids: Sequence[str], *, active_reserves: set[str] | None = None, decision_sha256: str | None = None) -> None:
        """Run up to one frozen candidate per arm, committing in manifest order."""

        pending_ids = [candidate_id for candidate_id in candidate_ids if candidate_id not in completed]
        if authority["schema_version"] != _AUTHORITY_V4:
            for candidate_id in pending_ids:
                record(
                    candidate_id,
                    active_reserve=active_reserves is not None and candidate_id in active_reserves,
                    decision_sha256=decision_sha256,
                )
            return
        queues: dict[str, list[str]] = {arm_id: [] for arm_id in _HYBRID_ARM_ROUTES}
        for candidate_id in pending_ids:
            if (
                candidates[candidate_id]["tier"] != "conditional_reserve"
                or active_reserves is None
                or candidate_id in active_reserves
            ):
                queues[str(candidates[candidate_id]["arm_id"])].append(candidate_id)
        positions = {arm_id: 0 for arm_id in queues}
        results: dict[str, dict[str, Any]] = {}
        active: dict[Future[dict[str, Any]], str] = {}

        def submit_next(pool: ThreadPoolExecutor, arm_id: str) -> None:
            position = positions[arm_id]
            if position >= len(queues[arm_id]):
                return
            candidate_id = queues[arm_id][position]
            positions[arm_id] = position + 1
            active[pool.submit(execute_candidate, candidate_id, sequence_hint=sequence + 1)] = candidate_id

        def commit_ready() -> None:
            while pending_ids:
                candidate_id = pending_ids[0]
                dormant = (
                    candidates[candidate_id]["tier"] == "conditional_reserve"
                    and active_reserves is not None
                    and candidate_id not in active_reserves
                )
                if dormant:
                    pending_ids.pop(0)
                    record(
                        candidate_id,
                        active_reserve=False,
                        decision_sha256=decision_sha256,
                    )
                elif candidate_id in results:
                    pending_ids.pop(0)
                    record(
                        candidate_id,
                        active_reserve=active_reserves is not None and candidate_id in active_reserves,
                        decision_sha256=decision_sha256,
                        executed_row=results.pop(candidate_id),
                    )
                else:
                    return

        try:
            with ThreadPoolExecutor(max_workers=5, thread_name_prefix="a2-hybrid") as pool:
                for arm_id in _HYBRID_ARM_ROUTES:
                    submit_next(pool, arm_id)
                commit_ready()
                while active:
                    done, _ = wait(tuple(active), return_when=FIRST_COMPLETED)
                    for future in done:
                        candidate_id = active.pop(future)
                        results[candidate_id] = future.result()
                        submit_next(pool, str(candidates[candidate_id]["arm_id"]))
                    commit_ready()
        except BaseException:
            siblings = tuple(active.values())
            for future in active:
                future.cancel()
            try:
                assert isinstance(executor, RemoteExecutor)
                if siblings:
                    executor.cancel_and_reap(candidate_ids=siblings)
                _done, not_done = wait(tuple(active)) if active else (set(), set())
                if not_done:
                    raise A2OperationalExecutorError(
                        "hybrid sibling teardown did not reap every submitted worker"
                    )
                for future in _done:
                    try:
                        future.result()
                    except BaseException:
                        pass
            except (A2RemoteTransportError, A2OperationalExecutorError) as teardown_error:
                raise A2OperationalExecutorError(
                    "hybrid sibling teardown failed closed"
                ) from teardown_error
            paused = build_lifecycle_checkpoint(
                root,
                attempt_id=attempt_id,
                sequence=sequence + 1,
                status="PAUSED",
                completed_candidate_count=len(completed),
                failed_candidate_count=1,
                resume_allowed=True,
                previous_checkpoint_sha256=previous,
            )
            append_lifecycle_checkpoint(ledger, paused)
            raise
        if pending_ids or results:
            raise A2OperationalExecutorError("hybrid scheduler did not commit frozen candidate order")

    decision_path = output / "reserve-activation-decision.v1.json"
    continuation_path = output / "reserve-continuation-authority.v1.json"
    with _attempt_lock(output / "attempt.lock"):
        # Stage one never runs or marks a reserve until every frozen matched cell is durable.
        run_stage(matched_ids)
        if reserve_budget_admission is None:
            return {
                "status": "MATCHED_COMPLETE_RESERVE_ADMISSION_REQUIRED",
                "attempt_id": attempt_id,
                "matched_candidate_count": 40,
                "matched_candidate_result_set_sha256": _matched_result_set_sha256(completed),
                "checkpoint_sha256": previous,
                "execution_adoption_receipt_sha256": adoption["receipt_sha256"],
                "measurement_authority_sha256": authority["authority_sha256"],
                "workers_reaped": True,
            }
        if decision_path.exists():
            decision = _load_json(decision_path, role="reserve activation decision")
            _validate(root, "a2-reserve-activation-decision.v1.json", decision)
            if (
                decision.get("receipt_sha256")
                != canonical_sha256(
                    {key: value for key, value in decision.items() if key != "receipt_sha256"}
                )
                or decision.get("matched_candidate_result_set_sha256")
                != _matched_result_set_sha256(completed)
                or decision.get("execution_adoption_receipt_sha256") != adoption["receipt_sha256"]
                or decision.get("initial_measurement_authority_sha256") != authority["authority_sha256"]
            ):
                raise A2OperationalExecutorError("reserve activation decision identity drift")
            expected_decision = build_reserve_activation_decision(
                root,
                attempt_id=attempt_id,
                receipts_by_candidate=completed,
                adoption_receipt_sha256=adoption["receipt_sha256"],
                authority_sha256=authority["authority_sha256"],
                provider_admission_receipt_sha256=reserve_budget_admission[
                    "provider_admission_receipt_sha256"
                ],
                arm_incumbents=arm_incumbents,
                reserve_budget_admission=reserve_budget_admission,
                now_utc=now_utc,
            )
            if decision != expected_decision:
                raise A2OperationalExecutorError("reserve continuation decision drift")
        else:
            decision = build_reserve_activation_decision(
                root,
                attempt_id=attempt_id,
                receipts_by_candidate=completed,
                adoption_receipt_sha256=adoption["receipt_sha256"],
                authority_sha256=authority["authority_sha256"],
                provider_admission_receipt_sha256=reserve_budget_admission[
                    "provider_admission_receipt_sha256"
                ],
                arm_incumbents=arm_incumbents,
                reserve_budget_admission=reserve_budget_admission,
                now_utc=now_utc,
            )
            _write_json(decision_path, decision)
        continuation = build_reserve_continuation(
            root,
            attempt_id=attempt_id,
            adoption_receipt_sha256=adoption["receipt_sha256"],
            authority_sha256=authority["authority_sha256"],
            decision=decision,
        )
        _write_json(continuation_path, continuation)
        active_reserves = set(continuation["active_reserve_candidate_ids"])
        decision_hash = continuation["reserve_activation_decision_receipt_sha256"]
        for candidate_id in reserve_ids:
            existing = completed.get(candidate_id)
            if existing is None:
                continue
            if existing.get("reserve_activation_evidence_sha256") != decision_hash:
                raise A2OperationalExecutorError("reserve receipt continuation binding drift")
            expected_active = candidate_id in active_reserves
            if existing.get("reserve_activation_passed") is not expected_active:
                raise A2OperationalExecutorError("reserve receipt activation decision drift")
        run_stage(
            reserve_ids,
            active_reserves=active_reserves,
            decision_sha256=decision_hash,
        )
    coverage = evaluate_candidate_receipts(root, receipts_by_candidate=completed)
    return {
        **coverage,
        "attempt_id": attempt_id,
        "checkpoint_sha256": previous,
        "execution_adoption_receipt_sha256": adoption["receipt_sha256"],
        "measurement_authority_sha256": authority["authority_sha256"],
        "reserve_activation_decision_receipt_sha256": decision["receipt_sha256"],
        "reserve_continuation_authority_sha256": continuation["continuation_sha256"],
        "workers_reaped": True,
    }


def build_candidate_result_receipt(
    repository_root: Path,
    *,
    result: Mapping[str, Any],
    evidence_class: str,
    measurement_authority: Mapping[str, Any] | None = None,
    execution_adoption_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate one aggregate external-executor output against frozen membership."""

    root = repository_root.resolve()
    row = dict(result)
    if set(row) != _RESULT_FIELDS:
        raise A2OperationalExecutorError("candidate result fields are not allowlisted")
    if row.get("schema_version") != "myis.armindex-a2-external-candidate-result.v1":
        raise A2OperationalExecutorError("candidate result schema is invalid")
    assert_aggregate_only(row)
    attempt_id = row.get("attempt_id")
    candidate_id = row.get("candidate_id")
    if not isinstance(attempt_id, str) or _ATTEMPT.fullmatch(attempt_id) is None:
        raise A2OperationalExecutorError("candidate result attempt is invalid")
    candidates = frozen_candidates(root)
    candidate = candidates.get(str(candidate_id))
    if candidate is None or row.get("arm_id") != candidate["arm_id"]:
        raise A2OperationalExecutorError("candidate result is outside frozen membership")
    if row.get("program_sha256") != candidate["program_sha256"]:
        raise A2OperationalExecutorError("candidate program hash drift")
    for field in (
        "executor_output_sha256",
        "evaluator_input_sha256",
        "evaluator_sha256",
        "code_sha256",
        "model_sha256",
        "data_sha256",
    ):
        _hash(row.get(field), role=field)
    measured = evidence_class == "measured_development_aggregate"
    if (
        row.get("train_only") is not (not measured)
        or row.get("rep_dev_measured") is not measured
    ):
        raise A2OperationalExecutorError("candidate result data-role declaration drift")
    if (
        row.get("protected_payload_included") is not False
        or row.get("per_query_outcomes_included") is not False
    ):
        raise A2OperationalExecutorError("candidate result crosses the protected boundary")
    if evidence_class not in {"engineering_synthetic", "measured_development_aggregate"}:
        raise A2OperationalExecutorError("candidate result evidence class is invalid")
    if evidence_class == "measured_development_aggregate":
        try:
            adoption = validate_execution_adoption_receipt(
                root, dict(execution_adoption_receipt or {})
            )
            validate_measurement_authority(
                root,
                dict(measurement_authority or {}),
                attempt_id=str(attempt_id),
                execution_adoption_receipt_sha256=adoption["receipt_sha256"],
                execution_bundle_git_commit=adoption["git_commit"],
                execution_bundle_git_tree=adoption["git_tree"],
            )
        except (A2ExecutionReadinessError, A2OperationalExecutorError):
            raise A2OperationalExecutorError("measured candidate result lacks adopted authority")
    elif measurement_authority is not None or execution_adoption_receipt is not None:
        raise A2OperationalExecutorError("synthetic result cannot consume measured authority")
    reserve = candidate["tier"] == "conditional_reserve"
    active = row.get("reserve_activation_passed") is True
    activation_evidence = row.get("reserve_activation_evidence_sha256")
    if reserve:
        _hash(activation_evidence, role="reserve activation evidence")
    elif active or activation_evidence is not None:
        raise A2OperationalExecutorError("matched candidate has reserve activation state")
    if reserve and not active:
        if any(row.get(field) is not None for field in ("primary_metric", "secondary_metrics", "latency", "cost")):
            raise A2OperationalExecutorError("dormant reserve contains an outcome")
        if row.get("coverage") != {"expected_units": 1, "completed_units": 0}:
            raise A2OperationalExecutorError("dormant reserve coverage is invalid")
        status = "DORMANT_CONDITIONAL_RESERVE"
        primary = secondary = latency = cost = None
    else:
        primary_value = row.get("primary_metric")
        secondary_value = row.get("secondary_metrics")
        latency_value = row.get("latency")
        cost_value = row.get("cost")
        coverage = row.get("coverage")
        if (
            not isinstance(primary_value, Mapping)
            or primary_value.get("name") != "recall_at_100/out"
            or not isinstance(secondary_value, Mapping)
            or set(secondary_value) != {"ndcg_at_100/out", "ndcg_at_10/out"}
            or not isinstance(latency_value, Mapping)
            or set(latency_value) != {"wall_seconds", "search_p95_seconds"}
            or not isinstance(cost_value, Mapping)
            or set(cost_value) != {"charged_usd", "currency"}
            or cost_value.get("currency") != "USD"
            or not isinstance(coverage, Mapping)
            or coverage.get("expected_units") != coverage.get("completed_units")
        ):
            raise A2OperationalExecutorError("candidate aggregate outcome is incomplete")
        primary = {
            "name": "recall_at_100/out",
            "value": _decimal(primary_value.get("value"), role="primary metric"),
        }
        secondary = {
            key: _decimal(secondary_value[key], role=key)
            for key in ("ndcg_at_100/out", "ndcg_at_10/out")
        }
        latency = {
            key: _decimal(latency_value[key], role=key)
            for key in ("wall_seconds", "search_p95_seconds")
        }
        cost = {
            "charged_usd": _decimal(cost_value["charged_usd"], role="charged_usd"),
            "currency": "USD",
        }
        status = "PASS_A2_CANDIDATE_RESULT"
    for count in ("resume_count", "failure_count"):
        if isinstance(row.get(count), bool) or not isinstance(row.get(count), int) or row[count] < 0:
            raise A2OperationalExecutorError(f"{count} is invalid")
    body = {
        "schema_version": "myis.armindex-a2-candidate-result-receipt.v1",
        "receipt_id": f"{attempt_id}-{candidate_id}-candidate-result-v1",
        "attempt_id": attempt_id,
        "status": status,
        "evidence_class": evidence_class,
        "scientific_authority": evidence_class == "measured_development_aggregate",
        "candidate_id": candidate_id,
        "arm_id": candidate["arm_id"],
        "tier": candidate["tier"],
        "program_sha256": candidate["program_sha256"],
        "executor_output_sha256": row["executor_output_sha256"],
        "evaluator_input_sha256": row["evaluator_input_sha256"],
        "evaluator_sha256": row["evaluator_sha256"],
        "code_sha256": row["code_sha256"],
        "model_sha256": row["model_sha256"],
        "data_sha256": row["data_sha256"],
        "primary_metric": primary,
        "secondary_metrics": secondary,
        "latency": latency,
        "cost": cost,
        "coverage": dict(row["coverage"]),
        "resume_count": row["resume_count"],
        "failure_count": row["failure_count"],
        "reserve_activation_passed": active,
        "reserve_activation_evidence_sha256": activation_evidence,
        "train_only": not measured,
        "rep_dev_measured": measured,
        "protected_payload_included": False,
        "per_query_outcomes_included": False,
        "freeze_bindings": _freeze_bindings(root),
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _validate(root, "a2-candidate-result-receipt.v1.json", receipt)
    return receipt


def evaluate_candidate_receipts(
    repository_root: Path,
    *,
    receipts_by_candidate: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Require exact 52-candidate accounting and unique matched-arm winners."""

    root = repository_root.resolve()
    candidates = frozen_candidates(root)
    if set(receipts_by_candidate) != set(candidates):
        raise A2OperationalExecutorError("candidate receipts must cover all 52 frozen IDs")
    winners: dict[str, dict[str, Any]] = {}
    winner_receipts: dict[str, dict[str, Any]] = {}
    receipt_hashes: list[str] = []
    for candidate_id, candidate in candidates.items():
        receipt = dict(receipts_by_candidate[candidate_id])
        _validate(root, "a2-candidate-result-receipt.v1.json", receipt)
        unsigned = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        if receipt.get("receipt_sha256") != canonical_sha256(unsigned):
            raise A2OperationalExecutorError("candidate result receipt hash drift")
        if receipt.get("candidate_id") != candidate_id or receipt.get("arm_id") != candidate["arm_id"]:
            raise A2OperationalExecutorError("candidate result receipt identity drift")
        if receipt.get("freeze_bindings") != _freeze_bindings(root):
            raise A2OperationalExecutorError("candidate result freeze binding drift")
        if (receipt.get("evidence_class") == "measured_development_aggregate") != (
            receipt.get("scientific_authority") is True
        ):
            raise A2OperationalExecutorError("candidate result authority class drift")
        reserve = candidate["tier"] == "conditional_reserve"
        if reserve and receipt["status"] == "DORMANT_CONDITIONAL_RESERVE":
            if receipt["reserve_activation_passed"] is not False:
                raise A2OperationalExecutorError("dormant reserve activation drift")
        elif receipt["status"] != "PASS_A2_CANDIDATE_RESULT":
            raise A2OperationalExecutorError("active candidate lacks a PASS result")
        receipt_hashes.append(receipt["receipt_sha256"])
    for arm_id in ("ARM-03", "ARM-05", "ARM-04"):
        reserve_receipts = [
            receipts_by_candidate[candidate_id]
            for candidate_id, candidate in candidates.items()
            if candidate["arm_id"] == arm_id
            and candidate["tier"] == "conditional_reserve"
        ]
        statuses = {receipt["status"] for receipt in reserve_receipts}
        decision_hashes = {
            receipt["reserve_activation_evidence_sha256"]
            for receipt in reserve_receipts
        }
        if (
            len(reserve_receipts) != 4
            or len(statuses) != 1
            or len(decision_hashes) != 1
            or statuses
            not in ({"PASS_A2_CANDIDATE_RESULT"}, {"DORMANT_CONDITIONAL_RESERVE"})
        ):
            raise A2OperationalExecutorError(
                "conditional reserve must be one decision-bound complete arm quartet"
            )
    for arm_id in ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05"):
        scored: list[tuple[Decimal, str]] = []
        for candidate_id, candidate in candidates.items():
            receipt = receipts_by_candidate[candidate_id]
            if candidate["arm_id"] != arm_id or receipt["status"] != "PASS_A2_CANDIDATE_RESULT":
                continue
            scored.append((Decimal(receipt["primary_metric"]["value"]), candidate_id))
        scored.sort(key=lambda item: (-item[0], item[1]))
        if len(scored) < 2 or scored[0][0] == scored[1][0]:
            raise A2OperationalExecutorError("exact winner tie or insufficient arm coverage")
        winner_id = scored[0][1]
        candidate = candidates[winner_id]
        if arm_id in {"ARM-01", "ARM-02"} and candidate["advancement_eligible"] is not False:
            raise A2OperationalExecutorError("diagnostic arm gained advancement authority")
        winners[arm_id] = {
            "winner_candidate_id": winner_id,
            "primary_metric": str(scored[0][0]),
            "diagnostic_non_advancing": candidate["diagnostic_non_advancing"],
            "advancement_eligible": candidate["advancement_eligible"],
            "candidate_result_receipt_sha256": receipts_by_candidate[winner_id]["receipt_sha256"],
        }
        winner_receipts[arm_id] = build_winner_receipt(
            root,
            attempt_id=str(receipts_by_candidate[winner_id]["attempt_id"]),
            arm_id=arm_id,
            winner_candidate_id=winner_id,
            train_evaluation_receipt_sha256=str(
                receipts_by_candidate[winner_id]["receipt_sha256"]
            ),
            strict_tie_rejected=True,
        )
    return {
        "status": "PASS_A2_EXACT_COVERAGE",
        "candidate_count": 52,
        "matched_candidate_count": 40,
        "conditional_reserve_candidate_count": 12,
        "candidate_result_set_sha256": canonical_sha256(sorted(receipt_hashes)),
        "winners": winners,
        "winner_receipts": winner_receipts,
        "freeze_bindings": _freeze_bindings(root),
    }


def build_remote_stage_plan(
    repository_root: Path,
    *,
    attempt_id: str,
    remote_root: str,
    bundle_receipt: Mapping[str, Any],
    bundle_path: Path,
    watchdog: Mapping[str, Any],
) -> dict[str, Any]:
    """Return exact SSH/SCP operations without embedding owner connection values."""

    root = repository_root.resolve()
    bundle = bundle_path.resolve(strict=True)
    checked_bundle = validate_execution_bundle(
        root, bundle_path=bundle, receipt=bundle_receipt
    )
    if bundle.is_symlink() or checked_bundle["attempt_id"] != attempt_id:
        raise A2OperationalExecutorError("remote stage bundle hash drift")
    if watchdog.get("attempt_id") != attempt_id:
        raise A2OperationalExecutorError("remote stage watchdog hash drift")
    if _REMOTE_ROOT.fullmatch(remote_root) is None or not remote_root.endswith(attempt_id):
        raise A2OperationalExecutorError("remote stage root is invalid")
    commands = [
        "verify_zero_a2_workers",
        "verify_remote_root_absent",
        "create_isolated_remote_root",
        "upload_bundle_and_watchdog",
        "verify_bundle_and_watchdog_hashes",
        "extract_bundle_without_a1_mutation",
        "start_watchdog_and_record_pid_start_identity",
        "verify_watchdog_heartbeat",
        "write_staged_not_launched_checkpoint",
    ]
    body = {
        "schema_version": "myis.armindex-a2-operational-stage-plan.v1",
        "attempt_id": attempt_id,
        "remote_root": remote_root,
        "bundle_sha256": checked_bundle["bundle_sha256"],
        "watchdog_sha256": watchdog["watchdog_sha256"],
        "operations": commands,
        "a1_root_mutation_allowed": False,
        "provider_destroy_allowed": False,
        "measured_a2_allowed": False,
        "connection_values_included": False,
    }
    return {**body, "plan_sha256": canonical_sha256(body)}


def validate_live_remote_probe(
    repository_root: Path,
    *,
    attempt_id: str,
    probe: Mapping[str, Any],
    provider_admission_receipt: Mapping[str, Any],
    bundle_sha256: str,
    remote_root: str,
    known_hosts_path: Path,
    now_utc: datetime,
) -> dict[str, Any]:
    """Validate a fresh, aggregate-safe SSH probe before remote mutation."""

    root = repository_root.resolve()
    checked = dict(probe)
    expected_receipt_id = f"{attempt_id}-live-remote-probe-v1"
    if checked.get("receipt_sha256") != canonical_sha256(
        {key: value for key, value in checked.items() if key != "receipt_sha256"}
    ):
        raise A2OperationalExecutorError("live remote probe self-hash is invalid")
    _validate(root, "a2-live-remote-probe-receipt.v1.json", checked)
    provider = validate_provider_admission_receipt(root, provider_admission_receipt)
    if checked.get("receipt_id") != expected_receipt_id or checked.get("attempt_id") != attempt_id:
        raise A2OperationalExecutorError("live remote probe attempt identity drift")
    if checked.get("provider_instance_id") != provider.get("provider_instance_id"):
        raise A2OperationalExecutorError("live remote probe provider identity drift")
    host_key_hash = file_sha256(known_hosts_path.resolve(strict=True))
    if checked.get("ssh_host_key_sha256") != host_key_hash or host_key_hash != provider.get(
        "ssh_host_key_sha256"
    ):
        raise A2OperationalExecutorError("live remote probe SSH host-key drift")
    for field, label in (
        ("runtime_sha256", "runtime"),
        ("gpu_uuid_set_sha256", "GPU UUID set"),
        ("model_lockset_sha256", "model lockset"),
        ("data_handoff_sha256", "data handoff"),
    ):
        if checked.get(field) != provider.get(field):
            raise A2OperationalExecutorError(f"live remote probe {label} drift")
    if checked.get("bundle_sha256") != bundle_sha256:
        raise A2OperationalExecutorError("live remote probe bundle drift")
    if checked.get("remote_root") != remote_root or checked.get("remote_root_absent") is not True:
        raise A2OperationalExecutorError("live remote probe remote root collision")
    if checked.get("gpu_compute_process_count") != 0:
        raise A2OperationalExecutorError("live remote probe found GPU compute process")
    if checked.get("a2_process_count") != 0:
        raise A2OperationalExecutorError("live remote probe found A2 process")
    if checked.get("ttl_deadline_utc") != provider.get("ttl_deadline_utc"):
        raise A2OperationalExecutorError("live remote probe TTL deadline drift")
    observed = datetime.fromisoformat(str(checked["observed_at_utc"]).replace("Z", "+00:00"))
    deadline = datetime.fromisoformat(str(checked["ttl_deadline_utc"]).replace("Z", "+00:00"))
    current = now_utc.astimezone(timezone.utc)
    if (
        observed.tzinfo is None
        or observed > current + timedelta(minutes=1)
        or (current - observed).total_seconds() > 900
    ):
        raise A2OperationalExecutorError("live remote probe is stale")
    remaining = int((deadline.astimezone(timezone.utc) - current).total_seconds())
    try:
        validate_initial_admission_ttl(remaining)
    except A2OperationalExecutorError as error:
        raise A2OperationalExecutorError("NEEDS_OWNER_TTL_EXTENSION") from error
    if checked.get("remaining_ttl_seconds") != remaining:
        raise A2OperationalExecutorError("NEEDS_OWNER_TTL_EXTENSION")
    return checked


def validate_live_remote_probe_v2(
    repository_root: Path,
    *,
    attempt_id: str,
    probe: Mapping[str, Any],
    provider_admission_receipt: Mapping[str, Any],
    bundle_sha256: str,
    remote_root: str,
    known_hosts_path: Path,
    now_utc: datetime,
) -> dict[str, Any]:
    """Validate a v2 probe against a fresh instance binding and bounded remote clock."""

    root = repository_root.resolve()
    checked = dict(probe)
    if checked.get("receipt_sha256") != canonical_sha256({key: value for key, value in checked.items() if key != "receipt_sha256"}):
        raise A2OperationalExecutorError("live remote probe self-hash is invalid")
    _validate(root, "a2-live-remote-probe-receipt.v2.json", checked)
    provider = (
        validate_provider_admission_receipt_v3(root, provider_admission_receipt)
        if provider_admission_receipt.get("schema_version")
        == "myis.armindex-a2-provider-admission-receipt.v3"
        else validate_provider_admission_receipt_v2(root, provider_admission_receipt)
    )
    if checked.get("receipt_id") != f"{attempt_id}-live-remote-probe-v2" or checked.get("attempt_id") != attempt_id:
        raise A2OperationalExecutorError("live remote probe attempt identity drift")
    for field, label in (
        ("provider_instance_id", "provider identity"),
        ("provider_instance_binding_sha256", "provider instance binding"),
        ("runtime_sha256", "runtime"),
        ("gpu_uuid_set_sha256", "GPU UUID set"),
        ("model_lockset_sha256", "model lockset"),
        ("data_handoff_sha256", "data handoff"),
    ):
        if checked.get(field) != provider.get(field):
            raise A2OperationalExecutorError(f"live remote probe {label} drift")
    host_key_hash = file_sha256(known_hosts_path.resolve(strict=True))
    if checked.get("ssh_host_key_sha256") != host_key_hash or host_key_hash != provider.get("ssh_host_key_sha256"):
        raise A2OperationalExecutorError("live remote probe SSH host-key drift")
    if checked.get("bundle_sha256") != bundle_sha256:
        raise A2OperationalExecutorError("live remote probe bundle drift")
    if checked.get("remote_root") != remote_root or checked.get("remote_root_absent") is not True:
        raise A2OperationalExecutorError("live remote probe remote root collision")
    if checked.get("gpu_compute_process_count") != 0:
        raise A2OperationalExecutorError("live remote probe found GPU compute process")
    if checked.get("a2_process_count") != 0:
        raise A2OperationalExecutorError("live remote probe found A2 process")
    if checked.get("ttl_deadline_utc") != provider.get("ttl_deadline_utc"):
        raise A2OperationalExecutorError("live remote probe TTL deadline drift")
    observed = datetime.fromisoformat(str(checked["observed_at_utc"]).replace("Z", "+00:00"))
    deadline = datetime.fromisoformat(str(checked["ttl_deadline_utc"]).replace("Z", "+00:00"))
    current = now_utc.astimezone(timezone.utc)
    if observed.tzinfo is None or observed > current + timedelta(seconds=_MAX_REMOTE_CLOCK_SKEW_SECONDS) or (current - observed).total_seconds() > 900:
        raise A2OperationalExecutorError("live remote probe is stale or exceeds clock skew")
    remote_remaining = int((deadline.astimezone(timezone.utc) - observed.astimezone(timezone.utc)).total_seconds())
    local_remaining = int((deadline.astimezone(timezone.utc) - current).total_seconds())
    if checked.get("remaining_ttl_seconds") != remote_remaining:
        raise A2OperationalExecutorError("live remote probe remaining TTL drift")
    try:
        validate_initial_admission_ttl(local_remaining)
    except A2OperationalExecutorError as error:
        raise A2OperationalExecutorError("NEEDS_OWNER_TTL_EXTENSION") from error
    return checked


def _run_live_remote_probe(
    *,
    ssh: Sequence[str],
    remote_root: str,
    provider: Mapping[str, Any],
    bundle_sha256: str,
    remote_identity_paths: Mapping[str, str],
    runner: Callable[..., subprocess.CompletedProcess[str]],
) -> dict[str, Any]:
    """Run a pinned-SSH probe and parse one aggregate-safe JSON object."""

    if set(remote_identity_paths) != {"provider_instance_id", "runtime", "model_lockset", "data_handoff"}:
        raise A2OperationalExecutorError("remote identity path set is incomplete")
    for value in remote_identity_paths.values():
        if re.fullmatch(r"/opt/myis/[A-Za-z0-9._/\\-]+", value) is None or ".." in value.split("/"):
            raise A2OperationalExecutorError("remote identity path is unsafe")
    expected = {
        "attempt_id": provider["attempt_id"],
        "provider_instance_id": provider["provider_instance_id"],
        "ttl_deadline_utc": provider["ttl_deadline_utc"],
        "remote_root": remote_root,
        "bundle_sha256": bundle_sha256,
        "ssh_host_key_sha256": provider["ssh_host_key_sha256"],
        "runtime_sha256": provider["runtime_sha256"],
        "gpu_uuid_set_sha256": provider["gpu_uuid_set_sha256"],
        "model_lockset_sha256": provider["model_lockset_sha256"],
        "data_handoff_sha256": provider["data_handoff_sha256"],
        "provider_instance_binding_sha256": provider.get("provider_instance_binding_sha256"),
        "remote_identity_paths": dict(remote_identity_paths),
    }
    encoded = shlex.quote(json.dumps(expected, sort_keys=True, separators=(",", ":")))
    command = (
        "set -eu; EXPECTED=" + encoded + "; export EXPECTED; "
        "python - <<'PY'\n"
        "import datetime, hashlib, json, os, pathlib, subprocess\n"
        "e=json.loads(os.environ['EXPECTED'])\n"
        "def out(argv): return subprocess.run(argv,check=True,capture_output=True,text=True).stdout\n"
        "g=[x.strip().split(',') for x in out(['nvidia-smi','--query-gpu=uuid,name,memory.total','--format=csv,noheader,nounits']).splitlines() if x.strip()]\n"
        "p=out(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits']).splitlines()\n"
        "a=subprocess.run(['pgrep','-af','[m]yis_research.armindex.a2_'],capture_output=True,text=True).stdout.splitlines()\n"
        "now=datetime.datetime.now(datetime.timezone.utc); deadline=datetime.datetime.fromisoformat(e['ttl_deadline_utc'].replace('Z','+00:00'))\n"
        "paths={k:pathlib.Path(v) for k,v in e['remote_identity_paths'].items()}; [x.resolve(strict=True) for x in paths.values()]\n"
        "digest=lambda x: hashlib.sha256(x.read_bytes()).hexdigest()\n"
        "body={'schema_version':'myis.armindex-a2-live-remote-probe-receipt.v2' if e.get('provider_instance_binding_sha256') else 'myis.armindex-a2-live-remote-probe-receipt.v1','receipt_id':e['attempt_id']+('-live-remote-probe-v2' if e.get('provider_instance_binding_sha256') else '-live-remote-probe-v1'),'attempt_id':e['attempt_id'],'status':'PASS_A2_LIVE_REMOTE_PROBE','observed_at_utc':now.isoformat().replace('+00:00','Z'),'provider_instance_id':paths['provider_instance_id'].read_text().strip(),'ssh_host_key_sha256':e['ssh_host_key_sha256'],'runtime_sha256':digest(paths['runtime']),'gpu_uuid_set_sha256':hashlib.sha256(json.dumps(sorted(x[0] for x in g),separators=(',',':')).encode()).hexdigest(),'gpu_count':len(g),'gpu_model':'RTX3090' if all(x[1].strip()=='NVIDIA GeForce RTX 3090' for x in g) else 'DRIFT','vram_mib_each':min(int(x[2]) for x in g) if g else 0,'gpu_compute_process_count':len([x for x in p if x.strip() and x.strip()!='No running processes found']),'a2_process_count':len(a),'model_lockset_sha256':digest(paths['model_lockset']),'data_handoff_sha256':digest(paths['data_handoff']),'bundle_sha256':e['bundle_sha256'],'remote_root':e['remote_root'],'remote_root_absent':not pathlib.Path(e['remote_root']).exists(),'ttl_deadline_utc':e['ttl_deadline_utc'],'remaining_ttl_seconds':int((deadline-now).total_seconds())}; \n"
        "if e.get('provider_instance_binding_sha256'): body['provider_instance_binding_sha256']=e['provider_instance_binding_sha256']\n"
        "body['receipt_sha256']=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':')).encode()).hexdigest(); print(json.dumps(body,sort_keys=True,separators=(',',':')))\n"
        "PY"
    )
    output = _native("ssh", [*ssh, command], role="live remote probe", runner=runner)
    try:
        value = json.loads(output)
    except json.JSONDecodeError as error:
        raise A2OperationalExecutorError("live remote probe returned invalid JSON") from error
    if not isinstance(value, dict):
        raise A2OperationalExecutorError("live remote probe returned invalid JSON")
    assert_aggregate_only(value)
    return value


def _candidate_manifest(root: Path) -> dict[str, Any]:
    return _load_json(
        root
        / "campaigns/armindex-multiretriever-v2/manifests/"
        "a2-five-arm-candidate-manifest.v1.json",
        role="candidate manifest",
    )


def _matched_candidate_ids(
    candidates: Mapping[str, Mapping[str, Any]],
) -> tuple[str, ...]:
    return tuple(
        candidate_id
        for candidate_id, candidate in candidates.items()
        if candidate["tier"] == "matched"
    )


def _matched_result_set_sha256(receipts: Mapping[str, Mapping[str, Any]]) -> str:
    matched = {
        candidate_id: receipt["receipt_sha256"]
        for candidate_id, receipt in receipts.items()
        if receipt.get("tier") == "matched"
    }
    if len(matched) != 40:
        raise A2OperationalExecutorError("reserve decision requires all 40 matched receipts")
    return canonical_sha256(dict(sorted(matched.items())))


def _primary_value(receipt: Mapping[str, Any]) -> str:
    metric = receipt.get("primary_metric")
    if not isinstance(metric, Mapping) or metric.get("name") != "recall_at_100/out":
        raise A2OperationalExecutorError("matched receipt lacks the frozen primary metric")
    return _decimal(metric.get("value"), role="matched primary metric")


def _batch_best(
    candidate_ids: Sequence[str], receipts: Mapping[str, Mapping[str, Any]]
) -> tuple[str, str]:
    scored = [(_decimal(_primary_value(receipts[candidate_id]), role="primary"), candidate_id) for candidate_id in candidate_ids]
    winner = min(scored, key=lambda item: (-Decimal(item[0]), item[1]))
    return winner[1], winner[0]


def reserve_checkpoint_ttl_seconds(
    repository_root: Path, *, successor_v3: bool = False
) -> int:
    """Derive the post-matched checkpoint floor from the frozen runtime model.

    Initial provider admission remains a separate 40-hour requirement.  At the
    matched barrier only the unfinished conditional-reserve critical path plus
    the frozen six-hour reserve is required.
    """

    profile_path = repository_root.resolve() / (
        "control/budgets/a2-execution-readiness-v2.json"
        if successor_v3
        else "control/budgets/a2-execution-readiness-v1.json"
    )
    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        projection = profile["runtime_projection"]
        worst = Decimal(str(projection["worst_case_dense_parallel_critical_path_seconds"]))
        matched = Decimal(str(projection["matched_dense_parallel_critical_path_seconds"]))
        reserve = Decimal(str(projection.get("owner_ttl_reserve_seconds", _RESERVE_TTL_RESERVE_SECONDS)))
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, InvalidOperation) as error:
        raise A2OperationalExecutorError("frozen runtime projection is unavailable") from error
    unfinished = worst - matched
    if unfinished < 0 or reserve < 0:
        raise A2OperationalExecutorError("frozen runtime projection is inconsistent")
    # Decimal ceiling avoids under-admitting a fractional projected second.
    return int((unfinished + reserve).to_integral_value(rounding="ROUND_CEILING"))


def validate_initial_admission_ttl(remaining_ttl_seconds: int) -> None:
    """Keep the fresh provider admission floor explicit and unchanged."""

    if remaining_ttl_seconds < _INITIAL_ADMISSION_TTL_SECONDS:
        raise A2OperationalExecutorError("initial provider admission requires 40 hours remaining")


def _load_remote_transport_config(
    path: Path,
    *,
    repository_root: Path,
    attempt_id: str,
    owner_root: Path | None = None,
    owner_manifest: Path | None = None,
) -> tuple[RemoteTransportConfig, dict[str, Any]]:
    try:
        raw = json.loads(path.resolve(strict=True).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A2OperationalExecutorError("remote transport config is missing or invalid") from error
    if not isinstance(raw, Mapping):
        raise A2OperationalExecutorError("remote transport config must be an object")
    try:
        config = RemoteTransportConfig(
            provider_instance_id=str(raw["provider_instance_id"]),
            host=str(raw["host"]),
            port=int(raw["port"]),
            user=str(raw.get("user", "root")),
            key_path=Path(str(raw["key_path"])).resolve(strict=True),
            known_hosts_path=Path(str(raw["known_hosts_path"])).resolve(strict=True),
            remote_root=str(raw["remote_root"]),
            remote_repository_root=str(raw["remote_repository_root"]),
            remote_owner_root=str(raw["remote_owner_root"]),
            remote_input_manifest=str(raw["remote_input_manifest"]),
            remote_bundle_path=str(raw["remote_bundle_path"]),
            remote_bundle_receipt_path=str(raw["remote_bundle_receipt_path"]),
            remote_python_executable=str(raw["remote_python_executable"]),
            bundle_sha256=str(raw["bundle_sha256"]),
            bundle_receipt_sha256=str(raw["bundle_receipt_sha256"]),
            bundle_receipt_file_sha256=str(raw["bundle_receipt_file_sha256"]),
            git_commit=str(raw["git_commit"]),
            git_tree=str(raw["git_tree"]),
            measurement_authority_commitment_uri=str(
                raw["measurement_authority_commitment_uri"]
            ),
            measurement_authority_commitment_file_sha256=str(
                raw["measurement_authority_commitment_file_sha256"]
            ),
            owner_manifest_sha256=str(raw["owner_manifest_sha256"]),
            remote_input_manifest_sha256=str(raw["remote_input_manifest_sha256"]),
            local_repository_root=str(repository_root.resolve()),
            local_owner_root=str(owner_root.resolve()) if owner_root is not None else None,
            local_python_executable=str(raw.get("local_python_executable", "")) or None,
            local_input_manifest=(
                owner_manifest.resolve().relative_to(owner_root.resolve()).as_posix()
                if owner_manifest is not None and owner_root is not None
                else None
            ),
        )
    except (KeyError, TypeError, ValueError, A2RemoteTransportError) as error:
        raise A2OperationalExecutorError("remote transport config binding is invalid") from error
    request = raw.get("request")
    if not isinstance(request, Mapping):
        raise A2OperationalExecutorError("remote transport request is missing")
    try:
        from .a2_remote_transport import validate_transport_request

        validate_transport_request(request, config, attempt_id=attempt_id)
    except A2RemoteTransportError as error:
        raise A2OperationalExecutorError("remote transport request is not hash-bound") from error
    if owner_manifest is not None and file_sha256(owner_manifest.resolve(strict=True)) != config.owner_manifest_sha256:
        raise A2OperationalExecutorError("Owner-local manifest hash differs from remote transport binding")
    return config, dict(raw)


def validate_remote_execution_binding(
    repository_root: Path,
    *,
    config: RemoteTransportConfig,
    attempt_id: str,
    adoption_receipt: Mapping[str, Any],
    measurement_authority: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind transport, adoption, pushed bundle, and AP authority before launch."""

    root = repository_root.resolve()
    adoption = validate_execution_adoption_receipt(root, adoption_receipt)
    authority = validate_measurement_authority(
        root,
        measurement_authority,
        attempt_id=attempt_id,
        execution_adoption_receipt_sha256=adoption["receipt_sha256"],
        execution_bundle_git_commit=adoption["git_commit"],
        execution_bundle_git_tree=adoption["git_tree"],
    )
    schema_version = authority["schema_version"]
    successor = schema_version in {_AUTHORITY_V3, _AUTHORITY_V4}
    expected_commitment_uri = {
        _AUTHORITY_V2: "control/armindex/a2/measurement-authority-commitment.v1.json",
        _AUTHORITY_V3: "control/armindex/a2/measurement-authority-commitment.v2.json",
        _AUTHORITY_V4: "control/armindex/a2/measurement-authority-commitment.v3.json",
    }[schema_version]
    if config.measurement_authority_commitment_uri != expected_commitment_uri:
        raise A2OperationalExecutorError("measurement authority commitment version drift")
    if successor and config.provider_instance_id != authority["provider_instance_id"]:
        raise A2OperationalExecutorError("remote provider differs from successor authority")
    commitment_path = (root / config.measurement_authority_commitment_uri).resolve()
    if (
        not commitment_path.is_relative_to(root)
        or commitment_path.is_symlink()
        or not commitment_path.is_file()
    ):
        raise A2OperationalExecutorError("measurement authority commitment is unsafe")
    commitment = _load_json(commitment_path, role="measurement authority commitment")
    _validate(
        root,
        {
            _AUTHORITY_V2: "a2-measurement-authority-commitment.v1.json",
            _AUTHORITY_V3: "a2-measurement-authority-commitment.v2.json",
            _AUTHORITY_V4: "a2-measurement-authority-commitment.v3.json",
        }[schema_version],
        commitment,
    )
    if (
        commitment["commitment_sha256"]
        != canonical_sha256(
            {
                key: value
                for key, value in commitment.items()
                if key != "commitment_sha256"
            }
        )
        or file_sha256(commitment_path)
        != config.measurement_authority_commitment_file_sha256
        or commitment["status"]
        != "MEASURED_EXECUTION_AUTHORITY_ABSENT_PENDING_AP"
        or commitment["scientific_authority"] is not False
        or commitment["measured_a2_authorized"] is not False
    ):
        raise A2OperationalExecutorError("measurement authority commitment drift")
    expected_successor_contract = {
        _AUTHORITY_V3: {
            "authority_schema_uri": "schemas/armindex/a2-measured-execution-authority.v3.json",
            "transport_schema_version": "myis.armindex-a2-remote-measured-transport.v3",
            "authority_contract_version": "owner_local_aggregate_evaluation_v1",
        },
        _AUTHORITY_V4: {
            "authority_schema_uri": "schemas/armindex/a2-measured-execution-authority.v4.json",
            "transport_schema_version": "myis.armindex-a2-remote-measured-transport.v4",
            "authority_contract_version": "hybrid_remote_cpu_gpu_owner_local_aggregate_evaluation_v1",
        },
    }
    if successor and any(
        commitment[key] != value
        for key, value in expected_successor_contract[schema_version].items()
    ):
        raise A2OperationalExecutorError("successor authority commitment drift")
    _git(root, "ls-files", "--error-unmatch", "--", config.measurement_authority_commitment_uri)
    if _git(root, "hash-object", "--", config.measurement_authority_commitment_uri) != _git(
        root, "rev-parse", f"HEAD:{config.measurement_authority_commitment_uri}"
    ):
        raise A2OperationalExecutorError("measurement authority commitment is not bound to HEAD")
    expected = {
        "attempt_id": attempt_id,
        "bundle_sha256": adoption["bundle_sha256"],
        "bundle_receipt_sha256": adoption["bundle_receipt_sha256"],
        "git_commit": adoption["git_commit"],
        "git_tree": adoption["git_tree"],
        "remote_root": adoption["remote_root"],
    }
    actual = {
        "attempt_id": attempt_id,
        "bundle_sha256": config.bundle_sha256,
        "bundle_receipt_sha256": config.bundle_receipt_sha256,
        "git_commit": config.git_commit,
        "git_tree": config.git_tree,
        "remote_root": config.remote_root,
    }
    try:
        validate_transport_adoption_binding(
            config, attempt_id=attempt_id, adoption_receipt=adoption
        )
    except A2RemoteTransportError as error:
        raise A2OperationalExecutorError(
            "remote transport differs from adoption or measurement authority"
        ) from error
    if actual != expected or authority["execution_adoption_receipt_sha256"] != adoption[
        "receipt_sha256"
    ]:
        raise A2OperationalExecutorError(
            "remote transport differs from adoption or measurement authority"
        )
    if successor:
        bindings = authority["owner_local_evaluation_bindings"]
        request = build_transport_request(config, attempt_id=attempt_id)
        if (
            bindings["owner_manifest_file_sha256"] != config.owner_manifest_sha256
            or bindings["transport_request_sha256"] != request["request_sha256"]
        ):
            raise A2OperationalExecutorError(
                "successor Owner-local evaluation transport binding drift"
            )
    return {
        **expected,
        "execution_adoption_receipt_sha256": adoption["receipt_sha256"],
        "measurement_authority_sha256": authority["authority_sha256"],
        "measurement_authority_commitment_file_sha256": (
            config.measurement_authority_commitment_file_sha256
        ),
        "status": "PASS_A2_REMOTE_EXECUTION_BINDING",
    }


def build_reserve_budget_admission(
    repository_root: Path,
    *,
    attempt_id: str,
    adoption_receipt: Mapping[str, Any],
    measurement_authority: Mapping[str, Any],
    provider_observation_path: Path,
    source_artifact_paths: Mapping[str, Path],
    instance_binding: Mapping[str, Any] | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Create the fresh reserve-checkpoint admission without provider contact."""

    root = repository_root.resolve()
    adoption_schema = adoption_receipt.get("schema_version")
    adoption_v2 = adoption_schema == "myis.armindex-a2-execution-adoption-receipt.v2"
    adoption_v3 = adoption_schema == "myis.armindex-a2-execution-adoption-receipt.v3"
    if adoption_v2 or adoption_v3:
        from .a2_execution_readiness import validate_provider_instance_binding

        adoption = (
            validate_execution_adoption_receipt_v3(root, adoption_receipt)
            if adoption_v3
            else validate_execution_adoption_receipt_v2(root, adoption_receipt)
        )
        if instance_binding is None:
            raise A2OperationalExecutorError("bound reserve admission requires fresh provider instance binding")
        binding = validate_provider_instance_binding(
            root, instance_binding, provider_observation_path=provider_observation_path,
            source_artifact_paths=source_artifact_paths,
        )
        if binding["binding_sha256"] != adoption.get("provider_instance_binding_sha256"):
            raise A2OperationalExecutorError("reserve instance binding differs from adoption")
    else:
        if instance_binding is not None:
            raise A2OperationalExecutorError("v1 reserve admission cannot accept a bound instance")
        adoption = validate_execution_adoption_receipt(root, adoption_receipt)
    authority = validate_measurement_authority(
        root,
        measurement_authority,
        attempt_id=attempt_id,
        execution_adoption_receipt_sha256=adoption["receipt_sha256"],
        execution_bundle_git_commit=adoption["git_commit"],
        execution_bundle_git_tree=adoption["git_tree"],
    )
    if adoption_v3:
        fresh_provider = build_provider_admission_receipt_v3(
            root, attempt_id=attempt_id, provider_observation_path=provider_observation_path,
            source_artifact_paths=source_artifact_paths, instance_binding=instance_binding,
            now_utc=now_utc or datetime.now(timezone.utc),
        )
    elif adoption_v2:
        fresh_provider = build_provider_admission_receipt_v2(
            root, attempt_id=attempt_id, provider_observation_path=provider_observation_path,
            source_artifact_paths=source_artifact_paths, instance_binding=instance_binding,
            now_utc=now_utc or datetime.now(timezone.utc),
        )
    else:
        fresh_provider = build_provider_admission_receipt(
            root, attempt_id=attempt_id, provider_observation_path=provider_observation_path,
            source_artifact_paths=source_artifact_paths, now_utc=now_utc or datetime.now(timezone.utc),
        )
    reserve_version = "v2" if adoption_v3 else "v1"
    # v1 reserves retain their historical USD 50 serialization even for the
    # original USD 35 provider-admission lineage.  Only the v3 successor
    # adoption selects the new USD 60 reserve receipt.
    hard_stop = "60" if adoption_v3 else "50"
    body = {
        "schema_version": f"myis.armindex-a2-reserve-budget-admission.{reserve_version}",
        "receipt_id": f"{attempt_id}-reserve-budget-admission-{reserve_version}",
        "attempt_id": attempt_id,
        "execution_adoption_receipt_sha256": adoption["receipt_sha256"],
        "initial_measurement_authority_sha256": authority["authority_sha256"],
        "provider_admission_receipt_sha256": fresh_provider["receipt_sha256"],
        "provider_observation_sha256": fresh_provider["provider_observation_sha256"],
        "provider_observation_file_sha256": fresh_provider["provider_observation_file_sha256"],
        "source_artifact_sha256": fresh_provider["source_artifact_sha256"],
        "observed_at_utc": fresh_provider["observed_at_utc"],
        "ttl_deadline_utc": fresh_provider["ttl_deadline_utc"],
        "whole_workload_total_usd": fresh_provider["whole_workload_total_usd"],
        "forward_hard_stop_usd": hard_stop,
        "freeze_bindings": _freeze_bindings(root),
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    return validate_reserve_budget_admission(
        root,
        receipt,
        attempt_id=attempt_id,
        adoption_receipt_sha256=adoption["receipt_sha256"],
        authority_sha256=authority["authority_sha256"],
        provider_admission_receipt_sha256=fresh_provider["receipt_sha256"],
        now_utc=now_utc,
    )


def validate_reserve_budget_admission(
    repository_root: Path,
    receipt: Mapping[str, Any],
    *,
    attempt_id: str,
    adoption_receipt_sha256: str,
    authority_sha256: str,
    provider_admission_receipt_sha256: str,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    root = repository_root.resolve()
    checked = dict(receipt)
    schema_version = checked.get("schema_version")
    if schema_version not in {
        "myis.armindex-a2-reserve-budget-admission.v1",
        "myis.armindex-a2-reserve-budget-admission.v2",
    }:
        raise A2OperationalExecutorError("reserve budget admission schema is unsupported")
    successor_v3 = schema_version == "myis.armindex-a2-reserve-budget-admission.v2"
    _validate(root, f"a2-reserve-budget-admission.v{'2' if successor_v3 else '1'}.json", checked)
    now = now_utc or datetime.now(timezone.utc)
    try:
        observed = datetime.fromisoformat(checked["observed_at_utc"].replace("Z", "+00:00"))
        deadline = datetime.fromisoformat(checked["ttl_deadline_utc"].replace("Z", "+00:00"))
    except (TypeError, ValueError) as error:
        raise A2OperationalExecutorError("reserve budget admission timestamps are invalid") from error
    if (
        checked["attempt_id"] != attempt_id
        or checked["execution_adoption_receipt_sha256"] != adoption_receipt_sha256
        or checked["initial_measurement_authority_sha256"] != authority_sha256
        or checked["provider_admission_receipt_sha256"] != provider_admission_receipt_sha256
        or not isinstance(checked.get("source_artifact_sha256"), Mapping)
        or checked["freeze_bindings"] != _freeze_bindings(root)
        or checked["receipt_sha256"]
        != canonical_sha256({key: value for key, value in checked.items() if key != "receipt_sha256"})
        or Decimal(checked["whole_workload_total_usd"])
        > Decimal("60" if successor_v3 else "50")
        or checked["forward_hard_stop_usd"] != ("60" if successor_v3 else "50")
        or now - observed > timedelta(minutes=15)
        or observed > now + timedelta(minutes=1)
        or (deadline - now).total_seconds()
        < reserve_checkpoint_ttl_seconds(root, successor_v3=successor_v3)
    ):
        raise A2OperationalExecutorError("reserve budget admission is stale or identity-drifted")
    return checked


def build_reserve_activation_decision(
    repository_root: Path,
    *,
    attempt_id: str,
    receipts_by_candidate: Mapping[str, Mapping[str, Any]],
    adoption_receipt_sha256: str,
    authority_sha256: str,
    provider_admission_receipt_sha256: str,
    arm_incumbents: Mapping[str, Mapping[str, Any]] | None = None,
    reserve_budget_admission: Mapping[str, Any],
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    root = repository_root.resolve()
    budget = validate_reserve_budget_admission(
        root,
        reserve_budget_admission,
        attempt_id=attempt_id,
        adoption_receipt_sha256=adoption_receipt_sha256,
        authority_sha256=authority_sha256,
        provider_admission_receipt_sha256=provider_admission_receipt_sha256,
        now_utc=now_utc,
    )
    manifest = _candidate_manifest(root)
    canonical_incumbents = canonical_a1_incumbents(root)
    if arm_incumbents is not None and dict(arm_incumbents) != canonical_incumbents:
        raise A2OperationalExecutorError("Owner-local A1 incumbent binding drift")
    candidates = frozen_candidates(root)
    matched_set = _matched_result_set_sha256(receipts_by_candidate)
    decisions: list[dict[str, Any]] = []
    active: list[str] = []
    frozen_bindings_sha256 = canonical_sha256(_freeze_bindings(root))
    batches = {row["batch_id"]: row for row in manifest["batches"]}
    for arm_id in ("ARM-03", "ARM-05", "ARM-04"):
        incumbent = canonical_incumbents.get(arm_id)
        if not isinstance(incumbent, Mapping):
            raise A2OperationalExecutorError("Owner-local A1 incumbent binding is missing")
        state = AutoIndexState(
            arm_id=arm_id,
            incumbent_candidate_id=str(incumbent["candidate_id"]),
            incumbent_program_sha256=_hash(incumbent["program_sha256"], role="incumbent program"),
            incumbent_primary=Decimal(str(incumbent["primary_metric"])),
            frozen_bindings_sha256=frozen_bindings_sha256,
        )
        batch_results: list[tuple[str, str]] = []
        arm_receipt_hashes: list[str] = []
        reserve_id = f"a2-{arm_id.lower()}-reserve-b3"
        reserve_ids = list(batches[reserve_id]["candidate_ids"])
        reserve_rows = [candidates[candidate_id] for candidate_id in reserve_ids]
        grounded = (
            len(reserve_rows) == 4
            and all(row["tier"] == "conditional_reserve" for row in reserve_rows)
            and all(row["batch_index"] == 3 for row in reserve_rows)
            and all(row["advancement_eligible"] is True for row in reserve_rows)
            and all(row["verifier_status"] == "accepted" for row in reserve_rows)
            and all(
                isinstance(row["declared_axis"], str) and bool(row["declared_axis"].strip())
                for row in reserve_rows
            )
            and len({row["scientific_payload_sha256"] for row in reserve_rows}) == 4
            and len({row["program_sha256"] for row in reserve_rows}) == 4
        )
        last_decision = None
        for batch_index in (1, 2):
            batch_id = f"a2-{arm_id.lower()}-matched-b{batch_index}"
            frozen_batch = batches[batch_id]
            candidate_ids = list(frozen_batch["candidate_ids"])
            arm_receipt_hashes.extend(receipts_by_candidate[item]["receipt_sha256"] for item in candidate_ids)
            derived_candidates = [
                {
                    key: candidates[candidate_id][key]
                    for key in (
                        "candidate_id", "role", "hypothesis", "declared_axis", "program_sha256",
                        "compiled_sha256", "scientific_payload_sha256", "matched_ablation_id",
                        "compile_sha256s", "verifier_status",
                    )
                }
                for candidate_id in candidate_ids
            ]
            batch_body = {
                "schema_version": "myis.armindex-autoindex-execution-batch.v1",
                "batch_id": batch_id,
                "arm_id": arm_id,
                "iteration": batch_index,
                "incumbent_program_sha256": state.incumbent_program_sha256,
                "frozen_bindings_sha256": frozen_bindings_sha256,
                "status": "frozen_before_evaluation",
                "candidates": derived_candidates,
            }
            batch = {**batch_body, "batch_sha256": canonical_sha256(batch_body)}
            scores = {candidate_id: _primary_value(receipts_by_candidate[candidate_id]) for candidate_id in candidate_ids}
            last_decision = advance_autoindex(
                state,
                batch,
                scores,
                remaining_budget=True,
                grounded_axes_remaining=grounded,
            )
            state = last_decision.state
            batch_results.append(_batch_best(candidate_ids, receipts_by_candidate))
        assert last_decision is not None
        # ``advance_autoindex`` owns the frozen two-batch transition.  Bind the
        # predicate to its retained incumbent rather than requiring the second
        # batch alone to beat the first: a batch-one improvement followed by a
        # flat batch-two remains a valid, grounded third-batch continuation.
        improvement = strict_primary_improvement(
            state.incumbent_primary, Decimal(str(incumbent["primary_metric"]))
        )
        activation = improvement and grounded and last_decision.next_action == "run_gated_third_batch"
        if activation:
            active.extend(reserve_ids)
        decisions.append(
            {
                "arm_id": arm_id,
                "matched_batch_receipt_sha256s": arm_receipt_hashes,
                "batch_one_best_candidate_id": batch_results[0][0],
                "batch_one_best_primary_metric": batch_results[0][1],
                "batch_two_best_candidate_id": batch_results[1][0],
                "batch_two_best_primary_metric": batch_results[1][1],
                "strict_primary_improvement": improvement,
                "grounded_axes_remaining": grounded,
                "fresh_budget_admission_pass": True,
                "activation_passed": activation,
                "reserve_candidate_ids": reserve_ids,
            }
        )
    body = {
        "schema_version": "myis.armindex-a2-reserve-activation-decision.v1",
        "receipt_id": f"{attempt_id}-reserve-activation-decision-v1",
        "attempt_id": attempt_id,
        "status": "PASS_A2_RESERVE_ACTIVATION_DECISION",
        "execution_adoption_receipt_sha256": adoption_receipt_sha256,
        "initial_measurement_authority_sha256": authority_sha256,
        "matched_candidate_result_set_sha256": matched_set,
        "matched_candidate_count": 40,
        "reserve_budget_admission_receipt_sha256": budget["receipt_sha256"],
        "decisions": decisions,
        "active_reserve_candidate_ids": active,
        "freeze_bindings": _freeze_bindings(root),
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _validate(root, "a2-reserve-activation-decision.v1.json", receipt)
    return receipt


def build_reserve_continuation(
    repository_root: Path,
    *,
    attempt_id: str,
    adoption_receipt_sha256: str,
    authority_sha256: str,
    decision: Mapping[str, Any],
) -> dict[str, Any]:
    root = repository_root.resolve()
    checked = dict(decision)
    _validate(root, "a2-reserve-activation-decision.v1.json", checked)
    if (
        checked.get("receipt_sha256")
        != canonical_sha256(
            {key: value for key, value in checked.items() if key != "receipt_sha256"}
        )
        or checked.get("attempt_id") != attempt_id
        or checked.get("execution_adoption_receipt_sha256")
        != adoption_receipt_sha256
        or checked.get("initial_measurement_authority_sha256") != authority_sha256
        or checked.get("freeze_bindings") != _freeze_bindings(root)
    ):
        raise A2OperationalExecutorError("reserve continuation decision binding drift")
    body = {
        "schema_version": "myis.armindex-a2-reserve-continuation-authority.v1",
        "continuation_id": f"{attempt_id}-reserve-continuation-v1",
        "attempt_id": attempt_id,
        "initial_measurement_authority_sha256": authority_sha256,
        "execution_adoption_receipt_sha256": adoption_receipt_sha256,
        "matched_candidate_result_set_sha256": checked["matched_candidate_result_set_sha256"],
        "reserve_activation_decision_receipt_sha256": checked["receipt_sha256"],
        "active_reserve_candidate_ids": list(checked["active_reserve_candidate_ids"]),
        "freeze_bindings": _freeze_bindings(root),
    }
    continuation = {**body, "continuation_sha256": canonical_sha256(body)}
    _validate(root, "a2-reserve-continuation-authority.v1.json", continuation)
    return continuation


def perform_remote_stage(
    repository_root: Path,
    *,
    attempt_id: str,
    provider_admission_receipt: Mapping[str, Any],
    bundle_receipt: Mapping[str, Any],
    bundle_path: Path,
    remote_root: str,
    watchdog_deadline_utc: str,
    owner_connection_path: Path,
    provider_observation_path: Path,
    source_artifact_paths: Mapping[str, Path],
    remote_identity_paths: Mapping[str, str],
    instance_binding: Mapping[str, Any] | None = None,
    now_utc: datetime | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    """Create and verify an isolated A2 root, then stop before any worker launch."""

    root = repository_root.resolve()
    provider_schema = provider_admission_receipt.get("schema_version")
    bound_instance = provider_schema in {
        "myis.armindex-a2-provider-admission-receipt.v2",
        "myis.armindex-a2-provider-admission-receipt.v3",
    }
    successor_v3 = provider_schema == "myis.armindex-a2-provider-admission-receipt.v3"
    if bound_instance:
        from .a2_execution_readiness import validate_provider_instance_binding

        if instance_binding is None:
            raise A2OperationalExecutorError("bound remote stage requires fresh provider instance binding")
        binding = validate_provider_instance_binding(
            root, instance_binding, provider_observation_path=provider_observation_path,
            source_artifact_paths=source_artifact_paths,
        )
        provider = (
            validate_provider_admission_receipt_v3(root, provider_admission_receipt)
            if successor_v3
            else validate_provider_admission_receipt_v2(root, provider_admission_receipt)
        )
        if binding["binding_sha256"] != provider.get("provider_instance_binding_sha256"):
            raise A2OperationalExecutorError("remote stage provider instance binding drift")
    else:
        if instance_binding is not None:
            raise A2OperationalExecutorError("v1 remote stage cannot accept a bound instance")
        provider = validate_provider_admission_receipt(
            root, provider_admission_receipt, provider_observation_path=provider_observation_path,
            source_artifact_paths=source_artifact_paths,
        )
    checked_bundle = validate_execution_bundle(
        root, bundle_path=bundle_path, receipt=bundle_receipt
    )
    if provider["attempt_id"] != attempt_id or checked_bundle["attempt_id"] != attempt_id:
        raise A2OperationalExecutorError("remote stage attempt identity drift")
    checkpoint = build_lifecycle_checkpoint(
        root,
        attempt_id=attempt_id,
        sequence=1,
        status="STAGED",
        completed_candidate_count=0,
        failed_candidate_count=0,
        resume_allowed=True,
    )
    watchdog = build_watchdog_script(
        attempt_id=attempt_id,
        remote_root=remote_root,
        deadline_utc=watchdog_deadline_utc,
    )
    plan = build_remote_stage_plan(
        root,
        attempt_id=attempt_id,
        remote_root=remote_root,
        bundle_receipt=bundle_receipt,
        bundle_path=bundle_path,
        watchdog=watchdog,
    )
    connection = load_owner_connection(owner_connection_path)
    ssh = _ssh_arguments(connection)
    scp = _scp_arguments(connection)
    target = ssh[-1]
    bundle_hash = checked_bundle["bundle_sha256"]
    watchdog_hash = watchdog["watchdog_sha256"]
    watchdog_file = bundle_path.parent / f"{attempt_id}.watchdog.sh"
    live_probe = _run_live_remote_probe(
        ssh=ssh,
        remote_root=remote_root,
        provider=provider,
        bundle_sha256=bundle_hash,
        remote_identity_paths=remote_identity_paths,
        runner=runner,
    )
    current = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    probe_file = bundle_path.parent / f"{attempt_id}.live-remote-probe.receipt.v{'2' if bound_instance else '1'}.json"
    _write_json(probe_file, live_probe)
    live_probe_file_hash = file_sha256(probe_file)
    live_probe = (validate_live_remote_probe_v2 if bound_instance else validate_live_remote_probe)(
        root, attempt_id=attempt_id, probe=live_probe, provider_admission_receipt=provider,
        bundle_sha256=bundle_hash, remote_root=remote_root,
        known_hosts_path=Path(connection["known_hosts_path"]), now_utc=current,
    )
    watchdog_file.write_text(str(watchdog["script"]), encoding="ascii", newline="\n")
    try:
        prepare = (
            "set -eu; "
            "test -z \"$(pgrep -f '[m]yis_research.armindex.a2_' || true)\"; "
            f"test ! -e {shlex.quote(remote_root)}; "
            f"mkdir -p {shlex.quote(remote_root)}/incoming {shlex.quote(remote_root)}/current "
            f"{shlex.quote(remote_root)}/lifecycle/processes {shlex.quote(remote_root)}/lifecycle/heartbeats"
        )
        _native("ssh", [*ssh, prepare], role="remote root preparation", runner=runner)
        _native(
            "scp",
            [*scp, str(bundle_path.resolve()), f"{target}:{remote_root}/incoming/bundle.tar.gz"],
            role="bundle upload",
            runner=runner,
        )
        _native(
            "scp",
            [*scp, str(watchdog_file.resolve()), f"{target}:{remote_root}/incoming/watchdog.sh"],
            role="watchdog upload",
            runner=runner,
        )
        verify = (
            "set -eu; "
            f"test \"$(sha256sum {remote_root}/incoming/bundle.tar.gz | awk '{{print $1}}')\" = {bundle_hash}; "
            f"test \"$(sha256sum {remote_root}/incoming/watchdog.sh | awk '{{print $1}}')\" = {watchdog_hash}; "
            f"tar --no-same-owner --no-same-permissions -xzf {remote_root}/incoming/bundle.tar.gz -C {remote_root}/current; "
            f"chmod 700 {remote_root}/incoming/watchdog.sh; "
            f"nohup {remote_root}/incoming/watchdog.sh </dev/null >{remote_root}/lifecycle/watchdog.stdout "
            f"2>{remote_root}/lifecycle/watchdog.stderr & pid=$!; "
            "start=$(sed 's/.*) //' /proc/$pid/stat | awk '{print $20}'); "
            f"printf '%s:%s\\n' \"$pid\" \"$start\" >{remote_root}/lifecycle/watchdog.identity; "
            f"i=0; while test ! -s {remote_root}/lifecycle/heartbeats/watchdog; do "
            "test \"$i\" -lt 20; test -r /proc/$pid/stat; i=$((i+1)); sleep 1; done; "
            "actual=$(sed 's/.*) //' /proc/$pid/stat | awk '{print $20}'); "
            "test \"$actual\" = \"$start\"; "
            f"heartbeat=$(cat {remote_root}/lifecycle/heartbeats/watchdog); "
            "age=$(( $(date -u +%s) - $(date -u -d \"$heartbeat\" +%s) )); "
            "test \"$age\" -ge 0; test \"$age\" -le 5; "
            "printf '%s:%s' \"$pid\" \"$start\""
        )
        identity = _native("ssh", [*ssh, verify], role="remote stage verification", runner=runner)
        match = re.fullmatch(r"([1-9][0-9]{0,9}):([0-9]+)", identity.strip())
        if match is None:
            raise A2OperationalExecutorError("watchdog process identity is invalid")
    finally:
        watchdog_file.unlink(missing_ok=True)
    body = {
        "schema_version": f"myis.armindex-a2-remote-stage-receipt.v{'2' if bound_instance else '1'}",
        "receipt_id": f"{attempt_id}-remote-stage-v{'2' if bound_instance else '1'}",
        "attempt_id": attempt_id,
        "status": "PASS_A2_REMOTE_STAGE_NOT_LAUNCHED",
        "provider_observation_sha256": provider["provider_observation_sha256"],
        "live_probe_receipt_sha256": live_probe["receipt_sha256"],
        "live_probe_file_sha256": live_probe_file_hash,
        "ttl_deadline_utc": provider["ttl_deadline_utc"],
        "watchdog_deadline_utc": watchdog_deadline_utc,
        "remote_root": remote_root,
        "remote_root_created_fresh": True,
        "bundle_sha256": bundle_hash,
        "staged_bundle_sha256": bundle_hash,
        "watchdog_sha256": watchdog_hash,
        "watchdog_pid": int(match.group(1)),
        "watchdog_linux_proc_start_time": match.group(2),
        "watchdog_heartbeat_observed": True,
        "gpu_compute_process_count": live_probe["gpu_compute_process_count"],
        "a2_process_count": live_probe["a2_process_count"],
        "zero_gpu_compute_processes": live_probe["gpu_compute_process_count"] == 0,
        "zero_workers_before_stage": live_probe["a2_process_count"] == 0,
        "a1_root_mutated": False,
        "provider_destroy_performed": False,
        "measured_a2_started": False,
        "freeze_bindings": _freeze_bindings(root),
    }
    if bound_instance:
        body.update({
            "provider_admission_receipt_sha256": provider["receipt_sha256"],
            "provider_instance_id": provider["provider_instance_id"],
            "provider_instance_binding_sha256": provider["provider_instance_binding_sha256"],
            "bundle_receipt_sha256": bundle_receipt["receipt_sha256"],
        })
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _validate(root, f"a2-remote-stage-receipt.v{'2' if bound_instance else '1'}.json", receipt)
    adoption_builder = (
        build_execution_adoption_receipt_v3
        if successor_v3
        else build_execution_adoption_receipt_v2
        if bound_instance
        else build_execution_adoption_receipt
    )
    adoption = adoption_builder(
        root, attempt_id=attempt_id, provider_admission_receipt=provider, bundle_receipt=bundle_receipt,
        remote_root=remote_root, staged_bundle_sha256=bundle_hash, watchdog_sha256=watchdog_hash,
        watchdog_deadline_utc=watchdog_deadline_utc, lifecycle_genesis_checkpoint_sha256=checkpoint["checkpoint_sha256"],
        live_probe_receipt_sha256=live_probe["receipt_sha256"], live_probe_file_sha256=live_probe_file_hash,
    )
    return {
        "plan": plan,
        "stage_receipt": receipt,
        "genesis_checkpoint": checkpoint,
        "execution_adoption_receipt": adoption,
        "state": "EXTERNAL_EXECUTION_REQUESTED_NOT_LAUNCHED",
        "measured_a2_started": False,
    }


def run_synthetic_dry_run(repository_root: Path, *, attempt_id: str) -> dict[str, Any]:
    """Exercise exact coverage, tie handling, reserve dormancy, and resume locally."""

    root = repository_root.resolve()
    if _ATTEMPT.fullmatch(attempt_id) is None:
        raise A2OperationalExecutorError("dry-run attempt ID is invalid")
    candidates = frozen_candidates(root)
    receipts: dict[str, dict[str, Any]] = {}
    synthetic_reserve_decision_sha256 = canonical_sha256(
        {
            "attempt_id": attempt_id,
            "evidence_class": "engineering_synthetic",
            "active_reserve_candidate_ids": [],
            "conditional_reserve_candidate_ids": [
                candidate_id
                for candidate_id, candidate in candidates.items()
                if candidate["tier"] == "conditional_reserve"
            ],
        }
    )
    for index, (candidate_id, candidate) in enumerate(candidates.items(), start=1):
        dormant = candidate["tier"] == "conditional_reserve"
        row = {
            "schema_version": "myis.armindex-a2-external-candidate-result.v1",
            "attempt_id": attempt_id,
            "candidate_id": candidate_id,
            "arm_id": candidate["arm_id"],
            "program_sha256": candidate["program_sha256"],
            "executor_output_sha256": canonical_sha256([candidate_id, "executor"]),
            "evaluator_input_sha256": canonical_sha256([candidate_id, "evaluator-input"]),
            "evaluator_sha256": "a" * 64,
            "code_sha256": "b" * 64,
            "model_sha256": "c" * 64,
            "data_sha256": "d" * 64,
            "primary_metric": None if dormant else {"name": "recall_at_100/out", "value": str(index)},
            "secondary_metrics": None if dormant else {"ndcg_at_100/out": str(index), "ndcg_at_10/out": str(index)},
            "latency": None if dormant else {"wall_seconds": "1", "search_p95_seconds": "0.1"},
            "cost": None if dormant else {"charged_usd": "0", "currency": "USD"},
            "coverage": {"expected_units": 1, "completed_units": 0 if dormant else 1},
            "resume_count": 0,
            "failure_count": 0,
            "reserve_activation_passed": False,
            "reserve_activation_evidence_sha256": (
                synthetic_reserve_decision_sha256 if dormant else None
            ),
            "train_only": True,
            "rep_dev_measured": False,
            "protected_payload_included": False,
            "per_query_outcomes_included": False,
        }
        receipts[candidate_id] = build_candidate_result_receipt(
            root, result=row, evidence_class="engineering_synthetic"
        )
    coverage = evaluate_candidate_receipts(root, receipts_by_candidate=receipts)
    with tempfile.TemporaryDirectory(prefix="myis-a2-dry-run-") as temporary:
        ledger = Path(temporary) / "lifecycle.jsonl"
        first = build_lifecycle_checkpoint(
            root,
            attempt_id=attempt_id,
            sequence=1,
            status="STAGED",
            completed_candidate_count=0,
            failed_candidate_count=0,
            resume_allowed=True,
        )
        append_lifecycle_checkpoint(ledger, first)
        second = build_lifecycle_checkpoint(
            root,
            attempt_id=attempt_id,
            sequence=2,
            status="PAUSED",
            completed_candidate_count=17,
            failed_candidate_count=0,
            resume_allowed=True,
            previous_checkpoint_sha256=first["checkpoint_sha256"],
        )
        append_lifecycle_checkpoint(ledger, second)
        resumed = resume_checkpoint(ledger, attempt_id=attempt_id)
    watchdog = build_watchdog_script(
        attempt_id=attempt_id,
        remote_root=f"/opt/myis/{attempt_id}",
        deadline_utc="2099-01-01T00:00:00Z",
    )
    return {
        "status": "PASS_A2_SYNTHETIC_OPERATIONAL_DRY_RUN",
        "attempt_id": attempt_id,
        "candidate_count": coverage["candidate_count"],
        "matched_candidate_count": coverage["matched_candidate_count"],
        "conditional_reserve_candidate_count": coverage["conditional_reserve_candidate_count"],
        "winner_count": len(coverage["winners"]),
        "resume_checkpoint_sha256": resumed["checkpoint_sha256"],
        "watchdog_sha256": watchdog["watchdog_sha256"],
        "measured_a2_started": False,
        "provider_contacted": False,
        "protected_payload_included": False,
        "result_set_sha256": coverage["candidate_result_set_sha256"],
    }


def build_execution_closeout_receipt(
    repository_root: Path,
    *,
    attempt_id: str,
    coverage: Mapping[str, Any],
    winner_receipt_sha256s: Mapping[str, str],
    safe_return_receipt: Mapping[str, Any],
    terminal_checkpoint_sha256: str,
    claim_evidence_pointers: Sequence[str],
    evidence_class: str,
) -> dict[str, Any]:
    """Bind exact coverage, safe return, teardown, and journal evidence pointers."""

    root = repository_root.resolve()
    if coverage.get("status") != "PASS_A2_EXACT_COVERAGE" or coverage.get("candidate_count") != 52:
        raise A2OperationalExecutorError("execution closeout requires exact 52 coverage")
    if set(winner_receipt_sha256s) != {"ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05"}:
        raise A2OperationalExecutorError("execution closeout requires five winner receipts")
    for arm_id, value in winner_receipt_sha256s.items():
        _hash(value, role=f"{arm_id} winner receipt")
    if safe_return_receipt.get("status") != "PASS_A2_SAFE_RETURN":
        raise A2OperationalExecutorError("execution closeout requires safe return PASS")
    _hash(safe_return_receipt.get("receipt_sha256"), role="safe return receipt")
    _hash(terminal_checkpoint_sha256, role="terminal checkpoint")
    if not claim_evidence_pointers or any(
        not isinstance(pointer, str)
        or Path(pointer).is_absolute()
        or ".." in Path(pointer).parts
        for pointer in claim_evidence_pointers
    ):
        raise A2OperationalExecutorError("claim evidence pointers are unsafe")
    body = {
        "schema_version": "myis.armindex-a2-execution-closeout-receipt.v1",
        "receipt_id": f"{attempt_id}-execution-closeout-v1",
        "attempt_id": attempt_id,
        "status": "PASS_A2_EXECUTION_CLOSEOUT",
        "evidence_class": evidence_class,
        "candidate_count": 52,
        "matched_candidate_count": 40,
        "conditional_reserve_candidate_count": 12,
        "arm_winner_receipt_sha256s": dict(winner_receipt_sha256s),
        "candidate_result_set_sha256": coverage["candidate_result_set_sha256"],
        "safe_return_receipt_sha256": safe_return_receipt["receipt_sha256"],
        "terminal_checkpoint_sha256": terminal_checkpoint_sha256,
        "workers_reaped": True,
        "protected_scan_passed": True,
        "diagnostic_non_advancing_arms": ["ARM-01", "ARM-02"],
        "primary_advancement_arms": ["ARM-03", "ARM-05", "ARM-04"],
        "claim_evidence_pointers": list(claim_evidence_pointers),
        "freeze_bindings": _freeze_bindings(root),
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _validate(root, "a2-execution-closeout-receipt.v1.json", receipt)
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myis-a2-executor")
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--attempt-id", default="a2-operational-dryrun")
    parser.add_argument("--dry-run", action="store_true")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("preflight")
    bundle = commands.add_parser("bundle")
    bundle.add_argument("--output", type=Path, required=True)
    bundle.add_argument("--receipt-output", type=Path)
    deployment = commands.add_parser("deployment-package")
    deployment.add_argument("--output", type=Path, required=True)
    deployment.add_argument("--receipt-output", type=Path)
    deployment_validate = commands.add_parser("deployment-validate")
    deployment_validate.add_argument("--package", type=Path, required=True)
    deployment_validate.add_argument("--receipt", type=Path, required=True)
    for deployment_command, paths_required in (
        (deployment, True),
        (deployment_validate, False),
    ):
        for arm_id in ("02", "03", "04", "05"):
            deployment_command.add_argument(
                f"--arm-{arm_id}-model-root", type=Path, required=paths_required
            )
        deployment_command.add_argument(
            "--wheelhouse-root", type=Path, required=paths_required
        )
        deployment_command.add_argument(
            "--a1-baseline-root", type=Path, required=paths_required
        )
        deployment_command.add_argument(
            "--a1-journal-root", type=Path, required=paths_required
        )
        deployment_command.add_argument(
            "--a1-closeout-root", type=Path, required=paths_required
        )
        deployment_command.add_argument(
            "--runtime-identity", type=Path, required=paths_required
        )
        deployment_command.add_argument(
            "--frozen-a1-bundle", type=Path, required=paths_required
        )
        deployment_command.add_argument(
            "--frozen-a1-bundle-receipt", type=Path, required=paths_required
        )
        deployment_command.add_argument(
            "--a2-bundle", type=Path, required=paths_required
        )
        deployment_command.add_argument(
            "--a2-bundle-receipt", type=Path, required=paths_required
        )
    admission = commands.add_parser("admit")
    admission.add_argument("--provider-observation", type=Path, required=True)
    admission.add_argument("--runtime-source", type=Path, required=True)
    admission.add_argument("--model-lockset-source", type=Path, required=True)
    admission.add_argument("--data-handoff-source", type=Path, required=True)
    admission.add_argument("--ssh-host-key-source", type=Path, required=True)
    admission.add_argument("--management-authority-source", type=Path, required=True)
    admission.add_argument("--provider-instance-binding", type=Path)
    admission.add_argument("--execution-readiness-contract", type=Path)
    admission.add_argument("--output", type=Path)
    bind_instance = commands.add_parser("bind-instance")
    bind_instance.add_argument("--provider-observation", type=Path, required=True)
    bind_instance.add_argument("--runtime-source", type=Path, required=True)
    bind_instance.add_argument("--model-lockset-source", type=Path, required=True)
    bind_instance.add_argument("--data-handoff-source", type=Path, required=True)
    bind_instance.add_argument("--ssh-host-key-source", type=Path, required=True)
    bind_instance.add_argument("--management-authority-source", type=Path, required=True)
    bind_instance.add_argument("--output", type=Path, required=True)
    reserve_admission = commands.add_parser("reserve-admit")
    reserve_admission.add_argument("--execution-adoption-receipt", type=Path, required=True)
    reserve_admission.add_argument("--measurement-authority", type=Path, required=True)
    reserve_admission.add_argument("--provider-observation", type=Path, required=True)
    reserve_admission.add_argument("--runtime-source", type=Path, required=True)
    reserve_admission.add_argument("--model-lockset-source", type=Path, required=True)
    reserve_admission.add_argument("--data-handoff-source", type=Path, required=True)
    reserve_admission.add_argument("--ssh-host-key-source", type=Path, required=True)
    reserve_admission.add_argument("--management-authority-source", type=Path, required=True)
    reserve_admission.add_argument("--provider-instance-binding", type=Path)
    reserve_admission.add_argument("--output", type=Path, required=True)
    stage = commands.add_parser("stage")
    stage.add_argument("--provider-admission-receipt", type=Path, required=True)
    stage.add_argument("--bundle-receipt", type=Path, required=True)
    stage.add_argument("--bundle", type=Path, required=True)
    stage.add_argument("--remote-root", required=True)
    stage.add_argument("--watchdog-deadline-utc", required=True)
    stage.add_argument("--owner-connection", type=Path, required=True)
    stage.add_argument("--provider-observation", type=Path, required=True)
    stage.add_argument("--runtime-source", type=Path, required=True)
    stage.add_argument("--model-lockset-source", type=Path, required=True)
    stage.add_argument("--data-handoff-source", type=Path, required=True)
    stage.add_argument("--ssh-host-key-source", type=Path, required=True)
    stage.add_argument("--management-authority-source", type=Path, required=True)
    stage.add_argument("--provider-instance-binding", type=Path)
    stage.add_argument("--remote-instance-id-path")
    stage.add_argument("--remote-runtime-path")
    stage.add_argument("--remote-model-lockset-path")
    stage.add_argument("--remote-data-handoff-path")
    stage.add_argument("--output-directory", type=Path)
    execute = commands.add_parser("execute")
    execute.add_argument("--execution-adoption-receipt", type=Path, required=True)
    execute.add_argument("--measurement-authority", type=Path, required=True)
    execute.add_argument("--command-argv-json", type=Path, required=True)
    execute.add_argument("--owner-root", type=Path, required=True)
    execute.add_argument("--owner-input-manifest", type=Path, required=True)
    execute.add_argument("--reserve-budget-admission", type=Path)
    execute.add_argument("--output-directory", type=Path, required=True)
    execute.add_argument("--checkpoint-ledger", type=Path, required=True)
    execute.add_argument("--remote-transport", type=Path)
    execute.add_argument("--timeout-seconds", type=int, default=21600)
    transport_check = commands.add_parser("transport-check")
    transport_check.add_argument("--remote-transport", type=Path, required=True)
    resume = commands.add_parser("resume")
    resume.add_argument("--ledger", type=Path, required=True)
    safe_return = commands.add_parser("safe-return")
    safe_return.add_argument("--archive", type=Path, required=True)
    safe_return.add_argument("--remote-root", required=True)
    safe_return.add_argument("--output", type=Path)
    closeout = commands.add_parser("closeout")
    closeout.add_argument("--coverage", type=Path, required=True)
    closeout.add_argument("--winner-receipts", type=Path, required=True)
    closeout.add_argument("--safe-return-receipt", type=Path, required=True)
    closeout.add_argument("--terminal-checkpoint-sha256", required=True)
    closeout.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = args.repository_root.resolve()
    command = args.command
    try:
        if args.dry_run or command is None:
            result = run_synthetic_dry_run(root, attempt_id=args.attempt_id)
        elif command == "preflight":
            from .a2_entry_preflight_v16 import evaluate_a2_entry_preflight

            result = evaluate_a2_entry_preflight(root)
        elif command == "bundle":
            result = build_execution_bundle(root, attempt_id=args.attempt_id, output_path=args.output)
            if args.receipt_output is not None:
                _write_json(args.receipt_output, result["receipt"])
        elif command in {"deployment-package", "deployment-validate"}:
            asset_values = (
                args.arm_02_model_root,
                args.arm_03_model_root,
                args.arm_04_model_root,
                args.arm_05_model_root,
                args.wheelhouse_root,
                args.a1_baseline_root,
                args.a1_journal_root,
                args.a1_closeout_root,
                args.runtime_identity,
                args.frozen_a1_bundle,
                args.frozen_a1_bundle_receipt,
                args.a2_bundle,
                args.a2_bundle_receipt,
            )
            if any(value is not None for value in asset_values) and not all(
                value is not None for value in asset_values
            ):
                raise A2OperationalExecutorError(
                    "deployment source re-probe requires every asset path"
                )
            assets = (
                A2DeploymentAssets(
                    model_roots={
                        "ARM-02": args.arm_02_model_root,
                        "ARM-03": args.arm_03_model_root,
                        "ARM-04": args.arm_04_model_root,
                        "ARM-05": args.arm_05_model_root,
                    },
                    wheelhouse_root=args.wheelhouse_root,
                    a1_baseline_root=args.a1_baseline_root,
                    a1_journal_root=args.a1_journal_root,
                    a1_closeout_root=args.a1_closeout_root,
                    runtime_identity_path=args.runtime_identity,
                    frozen_a1_bundle_path=args.frozen_a1_bundle,
                    frozen_a1_bundle_receipt_path=args.frozen_a1_bundle_receipt,
                    a2_bundle_path=args.a2_bundle,
                    a2_bundle_receipt_path=args.a2_bundle_receipt,
                )
                if all(value is not None for value in asset_values)
                else None
            )
            if command == "deployment-package":
                if assets is None:
                    raise A2OperationalExecutorError(
                        "deployment package build requires every asset path"
                    )
                result = build_deployment_package(
                    root,
                    attempt_id=args.attempt_id,
                    output_path=args.output,
                    assets=assets,
                )
                if args.receipt_output is not None:
                    _write_json(args.receipt_output, result["receipt"])
            else:
                result = validate_deployment_package(
                    root,
                    package_path=args.package,
                    receipt=_load_json(args.receipt, role="deployment package receipt"),
                    assets=assets,
                )
        elif command == "admit":
            source_paths = {
                    "runtime": args.runtime_source,
                    "model_lockset": args.model_lockset_source,
                    "data_handoff": args.data_handoff_source,
                    "ssh_host_key": args.ssh_host_key_source,
                    "management_authority": args.management_authority_source,
                }
            successor_v3 = False
            if args.execution_readiness_contract is not None:
                contract = _load_json(
                    args.execution_readiness_contract,
                    role="execution readiness contract",
                )
                successor_v3 = (
                    contract.get("schema_version")
                    == "myis.armindex-a2-execution-readiness-contract.v3"
                )
                if not successor_v3 and contract.get("schema_version") != (
                    "myis.armindex-a2-execution-readiness-contract.v2"
                ):
                    raise A2OperationalExecutorError(
                        "execution readiness contract is unsupported"
                    )
            if args.provider_instance_binding is not None and successor_v3:
                result = build_provider_admission_receipt_v3(
                    root, attempt_id=args.attempt_id, provider_observation_path=args.provider_observation,
                    source_artifact_paths=source_paths,
                    instance_binding=_load_json(args.provider_instance_binding, role="provider instance binding"),
                    now_utc=datetime.now(timezone.utc),
                )
            elif args.provider_instance_binding is not None:
                result = build_provider_admission_receipt_v2(
                    root, attempt_id=args.attempt_id, provider_observation_path=args.provider_observation,
                    source_artifact_paths=source_paths,
                    instance_binding=_load_json(args.provider_instance_binding, role="provider instance binding"),
                    now_utc=datetime.now(timezone.utc),
                )
            else:
                result = build_provider_admission_receipt(
                    root, attempt_id=args.attempt_id, provider_observation_path=args.provider_observation,
                    source_artifact_paths=source_paths, now_utc=datetime.now(timezone.utc),
                )
            if args.output is not None:
                _write_json(args.output, result)
        elif command == "bind-instance":
            result = build_provider_instance_binding(
                root, attempt_id=args.attempt_id, provider_observation_path=args.provider_observation,
                source_artifact_paths={
                    "runtime": args.runtime_source, "model_lockset": args.model_lockset_source,
                    "data_handoff": args.data_handoff_source, "ssh_host_key": args.ssh_host_key_source,
                    "management_authority": args.management_authority_source,
                },
            )
            _write_json(args.output, result)
        elif command == "transport-check":
            config, _ = _load_remote_transport_config(
                args.remote_transport,
                repository_root=root,
                attempt_id=args.attempt_id,
            )
            completed = subprocess.run(
                [*config.ssh_argv(), build_remote_validation_command(config, attempt_id=args.attempt_id)],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )
            if completed.returncode != 0:
                raise A2OperationalExecutorError("remote transport validation failed closed")
            try:
                result = validate_remote_transport_result(
                    json.loads(completed.stdout.strip().splitlines()[-1]),
                    config,
                    attempt_id=args.attempt_id,
                )
            except (IndexError, json.JSONDecodeError, A2RemoteTransportError) as error:
                raise A2OperationalExecutorError("remote transport validation returned invalid evidence") from error
        elif command == "execute":
            argv_value = json.loads(args.command_argv_json.read_text(encoding="utf-8"))
            if not isinstance(argv_value, list):
                raise A2OperationalExecutorError("external executor argv JSON must be a list")
            try:
                expected_argv = json.loads(
                    (root / "control/armindex/a2/measured-command-argv.v1.json").read_text(
                        encoding="utf-8"
                    )
                )
            except (OSError, UnicodeError, json.JSONDecodeError) as error:
                raise A2OperationalExecutorError(
                    "tracked measured command argv is invalid"
                ) from error
            if not isinstance(expected_argv, list):
                raise A2OperationalExecutorError("tracked measured command argv is invalid")
            if argv_value != expected_argv:
                raise A2OperationalExecutorError("external executor argv must match tracked measured adapter")
            owner_root = args.owner_root.resolve(strict=True)
            if owner_root.is_relative_to(root) or owner_root.is_symlink() or not owner_root.is_dir():
                raise A2OperationalExecutorError("Owner-local root is unsafe")
            owner_manifest = args.owner_input_manifest.resolve(strict=True)
            if owner_manifest.is_symlink() or not owner_manifest.is_file():
                raise A2OperationalExecutorError("Owner-local input manifest is unsafe")
            try:
                manifest_relative = owner_manifest.relative_to(owner_root).as_posix()
            except ValueError as error:
                raise A2OperationalExecutorError(
                    "Owner-local input manifest must be within Owner-local root"
                ) from error
            validated_owner_manifest = validate_owner_local_input(
                root,
                owner_root=owner_root,
                manifest_relative_path=manifest_relative,
                validate_runtime_identity=False,
            )
            if args.remote_transport is None:
                raise A2OperationalExecutorError(
                    "production measured adapter requires hash-bound remote transport"
                )
            config, _ = _load_remote_transport_config(
                args.remote_transport,
                repository_root=root,
                attempt_id=args.attempt_id,
                owner_root=owner_root,
                owner_manifest=owner_manifest,
            )
            result = execute_external_candidate_set(
                root,
                attempt_id=args.attempt_id,
                adoption_receipt=_load_json(
                    args.execution_adoption_receipt,
                    role="execution adoption receipt",
                ),
                measurement_authority=_load_json(
                    args.measurement_authority,
                    role="measurement authority",
                ),
                command_template=argv_value,
                output_directory=args.output_directory,
                checkpoint_ledger=args.checkpoint_ledger,
                owner_local_root=owner_root,
                owner_input_manifest=manifest_relative,
                python_executable=str(validated_owner_manifest["engine"]["python_executable"]),
                reserve_budget_admission=(
                    _load_json(args.reserve_budget_admission, role="reserve budget admission")
                    if args.reserve_budget_admission is not None
                    else None
                ),
                arm_incumbents=validated_owner_manifest.get("arm_incumbents"),
                timeout_seconds=args.timeout_seconds,
                executor=RemoteExecutor(
                    config=config,
                    attempt_id=args.attempt_id,
                    owner_root=owner_root,
                    manifest_relative_path=manifest_relative,
                ),
            )
        elif command == "reserve-admit":
            result = build_reserve_budget_admission(
                root,
                attempt_id=args.attempt_id,
                adoption_receipt=_load_json(
                    args.execution_adoption_receipt, role="execution adoption receipt"
                ),
                measurement_authority=_load_json(
                    args.measurement_authority, role="measurement authority"
                ),
                provider_observation_path=args.provider_observation,
                source_artifact_paths={
                    "runtime": args.runtime_source,
                    "model_lockset": args.model_lockset_source,
                    "data_handoff": args.data_handoff_source,
                    "ssh_host_key": args.ssh_host_key_source,
                    "management_authority": args.management_authority_source,
                },
                instance_binding=(
                    _load_json(args.provider_instance_binding, role="provider instance binding")
                    if args.provider_instance_binding is not None else None
                ),
                now_utc=datetime.now(timezone.utc),
            )
            _write_json(args.output, result)
        elif command == "stage":
            stage_source_values = {
                "runtime": args.runtime_source,
                "model_lockset": args.model_lockset_source,
                "data_handoff": args.data_handoff_source,
                "ssh_host_key": args.ssh_host_key_source,
                "management_authority": args.management_authority_source,
            }
            source_paths = (
                {key: value for key, value in stage_source_values.items() if value is not None}
                if any(value is not None for value in stage_source_values.values())
                else None
            )
            remote_path_values = {
                "provider_instance_id": args.remote_instance_id_path,
                "runtime": args.remote_runtime_path,
                "model_lockset": args.remote_model_lockset_path,
                "data_handoff": args.remote_data_handoff_path,
            }
            remote_paths = (
                {key: value for key, value in remote_path_values.items() if value is not None}
                if any(value is not None for value in remote_path_values.values())
                else None
            )
            if source_paths is None or set(source_paths) != {
                "runtime",
                "model_lockset",
                "data_handoff",
                "ssh_host_key",
                "management_authority",
            }:
                raise A2OperationalExecutorError(
                    "remote stage requires every provider source artifact"
                )
            if remote_paths is None or set(remote_paths) != {
                "provider_instance_id",
                "runtime",
                "model_lockset",
                "data_handoff",
            }:
                raise A2OperationalExecutorError(
                    "remote stage requires every remote identity path"
                )
            result = perform_remote_stage(
                root,
                attempt_id=args.attempt_id,
                provider_admission_receipt=_load_json(
                    args.provider_admission_receipt, role="provider admission receipt"
                ),
                bundle_receipt=_load_json(args.bundle_receipt, role="bundle receipt"),
                bundle_path=args.bundle,
                remote_root=args.remote_root,
                watchdog_deadline_utc=args.watchdog_deadline_utc,
                owner_connection_path=args.owner_connection,
                provider_observation_path=args.provider_observation,
                source_artifact_paths=source_paths,
                remote_identity_paths=remote_paths,
                instance_binding=(
                    _load_json(args.provider_instance_binding, role="provider instance binding")
                    if args.provider_instance_binding is not None else None
                ),
            )
            if args.output_directory is not None:
                output = args.output_directory.resolve()
                stage_version = result["stage_receipt"]["schema_version"].rsplit(".", 1)[-1]
                adoption_version = result["execution_adoption_receipt"][
                    "schema_version"
                ].rsplit(".", 1)[-1]
                _write_json(
                    output / f"remote-stage.receipt.{stage_version}.json",
                    result["stage_receipt"],
                )
                _write_json(output / "lifecycle-genesis.checkpoint.v1.json", result["genesis_checkpoint"])
                _write_json(
                    output / f"execution-adoption.receipt.{adoption_version}.json",
                    result["execution_adoption_receipt"],
                )
        elif command == "resume":
            result = resume_checkpoint(args.ledger, attempt_id=args.attempt_id)
        elif command == "safe-return":
            result = build_safe_return_receipt(
                root,
                attempt_id=args.attempt_id,
                archive_path=args.archive,
                remote_root=args.remote_root,
            )
            if args.output is not None:
                _write_json(args.output, result)
        elif command == "closeout":
            result = build_execution_closeout_receipt(
                root,
                attempt_id=args.attempt_id,
                coverage=_load_json(args.coverage, role="coverage receipt"),
                winner_receipt_sha256s=_load_json(args.winner_receipts, role="winner receipt hashes"),
                safe_return_receipt=_load_json(args.safe_return_receipt, role="safe return receipt"),
                terminal_checkpoint_sha256=args.terminal_checkpoint_sha256,
                claim_evidence_pointers=[args.coverage.as_posix(), args.safe_return_receipt.as_posix()],
                evidence_class="measured_development_aggregate",
            )
            if args.output is not None:
                _write_json(args.output, result)
        else:
            raise A2OperationalExecutorError("unsupported A2 executor command")
    except (
        A2DeploymentPackageError,
        A2OperationalExecutorError,
        A2ExecutionReadinessError,
        ValueError,
    ) as error:
        print(json.dumps({"status": "FAILED_CLOSED", "error": str(error)}, ensure_ascii=True, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
