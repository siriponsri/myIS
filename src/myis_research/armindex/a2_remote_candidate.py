"""Durable Linux supervisor for one hash-bound remote A2 candidate.

The supervisor is deliberately separate from retrieval.  It keeps enough
aggregate operational state to recover after an SSH interruption without
launching a second worker or trusting a stale PID.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from ..kernel.canonical import canonical_sha256, file_sha256


class A2RemoteCandidateError(RuntimeError):
    """Raised when durable remote candidate state cannot be proved safe."""


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise A2RemoteCandidateError("remote lifecycle path is a symlink")
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


def _read_json(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A2RemoteCandidateError(f"{role} is invalid") from error
    if not isinstance(value, dict):
        raise A2RemoteCandidateError(f"{role} must be an object")
    return value


def _proc_start_tick(pid: int) -> int | None:
    """Return Linux /proc start time, which protects against PID reuse."""

    try:
        fields = (
            Path(f"/proc/{pid}/stat")
            .read_text(encoding="ascii")
            .rsplit(") ", 1)[1]
            .split()
        )
        if fields[0] == "Z":
            return None
        return int(fields[19])
    except (OSError, UnicodeError, IndexError, ValueError):
        return None


def _same_process(identity: Mapping[str, Any]) -> bool:
    pid = identity.get("pid")
    start_tick = identity.get("start_tick")
    return (
        isinstance(pid, int)
        and pid > 1
        and isinstance(start_tick, int)
        and _proc_start_tick(pid) == start_tick
    )


def _terminate_and_reap(identity: Mapping[str, Any], *, grace_seconds: float) -> bool:
    if not _same_process(identity):
        return True
    pid = int(identity["pid"])
    os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        if not _same_process(identity):
            return True
        time.sleep(0.05)
    if _same_process(identity):
        os.kill(pid, signal.SIGKILL)
    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        if not _same_process(identity):
            return True
        time.sleep(0.05)
    return not _same_process(identity)


def _heartbeat_fresh(
    path: Path, *, identity: Mapping[str, Any], stale_seconds: float
) -> bool:
    try:
        value = _read_json(path, role="remote heartbeat")
        observed_ns = int(value["observed_monotonic_ns"])
    except (A2RemoteCandidateError, KeyError, TypeError, ValueError):
        return False
    return (
        value.get("attempt_id") == identity.get("attempt_id")
        and value.get("candidate_id") == identity.get("candidate_id")
        and value.get("pid") == identity.get("pid")
        and value.get("start_tick") == identity.get("start_tick")
        and 0 <= time.monotonic_ns() - observed_ns
        <= int(stale_seconds * 1_000_000_000)
    )


@contextmanager
def _candidate_lock(path: Path) -> Iterator[None]:
    """Serialize recovery; the OS releases this lock if a supervisor dies."""

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
            raise A2RemoteCandidateError(
                "another supervisor owns the remote candidate lock"
            ) from error
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


def _validate_result(path: Path, *, attempt_id: str, candidate_id: str) -> dict[str, Any]:
    result = _read_json(path, role="durable remote result")
    unsigned = {key: value for key, value in result.items() if key != "receipt_sha256"}
    if (
        result.get("attempt_id") != attempt_id
        or result.get("candidate_id") != candidate_id
        or result.get("receipt_sha256") != canonical_sha256(unsigned)
    ):
        raise A2RemoteCandidateError("durable remote result identity drift")
    return result


def _validate_launch_bindings(
    *,
    attempt_id: str,
    repository_root: Path,
    input_manifest_path: Path,
    input_manifest_sha256: str,
    owner_manifest_sha256: str,
    bundle_path: Path,
    bundle_receipt_path: Path,
    bundle_sha256: str,
    bundle_receipt_sha256: str,
    git_commit: str,
    git_tree: str,
    authority_commitment_uri: str,
    authority_commitment_file_sha256: str,
) -> None:
    if file_sha256(input_manifest_path.resolve(strict=True)) != input_manifest_sha256:
        raise A2RemoteCandidateError("remote retrieval input hash drift")
    remote_input = _read_json(input_manifest_path, role="remote retrieval input")
    unsigned_remote_input = {
        key: value for key, value in remote_input.items() if key != "manifest_sha256"
    }
    if (
        remote_input.get("attempt_id") != attempt_id
        or remote_input.get("owner_manifest_sha256") != owner_manifest_sha256
        or remote_input.get("manifest_sha256")
        != canonical_sha256(unsigned_remote_input)
        or remote_input.get("retriever_code_sha256")
        != file_sha256(repository_root / "src/myis_research/armindex/a2_remote_retriever.py")
    ):
        raise A2RemoteCandidateError("remote retrieval input provenance drift")
    if file_sha256(bundle_path.resolve(strict=True)) != bundle_sha256:
        raise A2RemoteCandidateError("remote bundle hash drift")
    if file_sha256(bundle_receipt_path.resolve(strict=True)) != bundle_receipt_sha256:
        raise A2RemoteCandidateError("remote bundle receipt hash drift")
    receipt = _read_json(bundle_receipt_path, role="remote bundle receipt")
    if (
        receipt.get("bundle_sha256") != bundle_sha256
        or receipt.get("git_commit") != git_commit
        or receipt.get("git_tree") != git_tree
    ):
        raise A2RemoteCandidateError("remote bundle receipt provenance drift")
    manifest = _read_json(repository_root / "BUNDLE_MANIFEST.json", role="bundle manifest")
    if (
        manifest.get("git_commit") != git_commit
        or manifest.get("git_tree") != git_tree
        or manifest.get("bundle_manifest_sha256")
        != canonical_sha256(
            {key: value for key, value in manifest.items() if key != "bundle_manifest_sha256"}
        )
    ):
        raise A2RemoteCandidateError("remote bundle manifest provenance drift")
    commitment = (repository_root / authority_commitment_uri).resolve(strict=True)
    if not commitment.is_relative_to(repository_root) or commitment.is_symlink():
        raise A2RemoteCandidateError("remote authority commitment path is unsafe")
    if file_sha256(commitment) != authority_commitment_file_sha256:
        raise A2RemoteCandidateError("remote authority commitment hash drift")
    value = _read_json(commitment, role="authority commitment")
    if (
        value.get("status") != "MEASURED_EXECUTION_AUTHORITY_ABSENT_PENDING_AP"
        or value.get("scientific_authority") is not False
        or value.get("measured_a2_authorized") is not False
    ):
        raise A2RemoteCandidateError("remote authority commitment is not launch-locked")


def supervise_candidate(
    *,
    attempt_id: str,
    candidate_id: str,
    lifecycle_root: Path,
    worker_argv: Sequence[str],
    timeout_seconds: float,
    heartbeat_interval_seconds: float = 2.0,
    stale_heartbeat_seconds: float = 30.0,
    terminate_grace_seconds: float = 15.0,
) -> dict[str, Any]:
    """Launch, recover, cancel, and reap exactly one remote candidate worker."""

    candidate_root = (lifecycle_root / "candidates" / candidate_id).resolve()
    if not candidate_root.is_relative_to(lifecycle_root.resolve()):
        raise A2RemoteCandidateError("remote candidate lifecycle root is unsafe")
    with _candidate_lock(candidate_root / "supervisor.lock"):
        return _supervise_candidate_locked(
            attempt_id=attempt_id,
            candidate_id=candidate_id,
            lifecycle_root=lifecycle_root,
            worker_argv=worker_argv,
            timeout_seconds=timeout_seconds,
            heartbeat_interval_seconds=heartbeat_interval_seconds,
            stale_heartbeat_seconds=stale_heartbeat_seconds,
            terminate_grace_seconds=terminate_grace_seconds,
        )


def _supervise_candidate_locked(
    *,
    attempt_id: str,
    candidate_id: str,
    lifecycle_root: Path,
    worker_argv: Sequence[str],
    timeout_seconds: float,
    heartbeat_interval_seconds: float = 2.0,
    stale_heartbeat_seconds: float = 30.0,
    terminate_grace_seconds: float = 15.0,
) -> dict[str, Any]:
    if not worker_argv or timeout_seconds <= 0:
        raise A2RemoteCandidateError("remote worker command or timeout is invalid")
    candidate_root = (lifecycle_root / "candidates" / candidate_id).resolve()
    if not candidate_root.is_relative_to(lifecycle_root.resolve()):
        raise A2RemoteCandidateError("remote candidate lifecycle root is unsafe")
    candidate_root.mkdir(parents=True, exist_ok=True)
    identity_path = candidate_root / "process.identity.json"
    heartbeat_path = candidate_root / "heartbeat.json"
    cancel_path = candidate_root / "cancel.request.json"
    result_path = candidate_root / "result.json"
    stdout_path = candidate_root / "worker.stdout"
    stderr_path = candidate_root / "worker.stderr"
    recovery_path = candidate_root / "recovery.json"
    if result_path.is_file():
        return _validate_result(result_path, attempt_id=attempt_id, candidate_id=candidate_id)

    recovery_count = 0
    if recovery_path.is_file():
        recovery_count = int(_read_json(recovery_path, role="recovery state").get("recovery_count", 0))
    identity = (
        _read_json(identity_path, role="remote process identity")
        if identity_path.is_file()
        else None
    )
    command_sha256 = canonical_sha256(list(worker_argv))
    if identity is not None and (
        identity.get("attempt_id") != attempt_id
        or identity.get("candidate_id") != candidate_id
        or identity.get("command_sha256") != command_sha256
    ):
        raise A2RemoteCandidateError("remote process identity binding drift")
    if identity is not None and _same_process(identity):
        if cancel_path.is_file() or not _heartbeat_fresh(
            heartbeat_path,
            identity=identity,
            stale_seconds=stale_heartbeat_seconds,
        ):
            if not _terminate_and_reap(identity, grace_seconds=terminate_grace_seconds):
                raise A2RemoteCandidateError("stale remote worker could not be reaped")
            recovery_count += 1
            _atomic_json(
                recovery_path,
                {
                    "attempt_id": attempt_id,
                    "candidate_id": candidate_id,
                    "recovery_count": recovery_count,
                    "prior_worker_reaped": True,
                },
            )
            identity = None
        else:
            # A reconnect attaches to the still-fresh identity and never duplicates it.
            pass
    elif identity is not None:
        recovered = _recover_stdout_result(
            stdout_path, attempt_id=attempt_id, candidate_id=candidate_id
        )
        if recovered is not None:
            _atomic_json(result_path, recovered)
            _persist_terminal_state(
                identity_path=identity_path,
                heartbeat_path=heartbeat_path,
                identity=identity,
                result=recovered,
                recovery_count=recovery_count + 1,
            )
            _atomic_json(
                recovery_path,
                {
                    "attempt_id": attempt_id,
                    "candidate_id": candidate_id,
                    "recovery_count": recovery_count + 1,
                    "prior_worker_reaped": True,
                    "result_recovered_without_relaunch": True,
                },
            )
            return recovered
        recovery_count += 1
        _atomic_json(
            recovery_path,
            {
                "attempt_id": attempt_id,
                "candidate_id": candidate_id,
                "recovery_count": recovery_count,
                "prior_worker_reaped": True,
            },
        )
        identity = None

    if cancel_path.is_file():
        raise A2RemoteCandidateError("remote candidate cancellation is durable")

    owned_process: subprocess.Popen[str] | None = None
    if identity is None:
        stdout_handle = stdout_path.open("w", encoding="utf-8")
        stderr_handle = stderr_path.open("w", encoding="utf-8")
        try:
            owned_process = subprocess.Popen(
                list(worker_argv),
                stdin=subprocess.DEVNULL,
                stdout=stdout_handle,
                stderr=stderr_handle,
                text=True,
                encoding="utf-8",
                errors="replace",
                close_fds=True,
                start_new_session=True,
            )
        finally:
            stdout_handle.close()
            stderr_handle.close()
        start_tick = _proc_start_tick(owned_process.pid)
        if start_tick is None:
            owned_process.terminate()
            owned_process.wait(timeout=terminate_grace_seconds)
            raise A2RemoteCandidateError("remote worker process identity is unavailable")
        identity = {
            "attempt_id": attempt_id,
            "candidate_id": candidate_id,
            "pid": owned_process.pid,
            "start_tick": start_tick,
            "command_sha256": command_sha256,
            "recovery_count": recovery_count,
            "status": "RUNNING",
        }
        _atomic_json(identity_path, identity)

    deadline = time.monotonic() + timeout_seconds
    while _same_process(identity):
        if cancel_path.is_file():
            if not _terminate_and_reap(identity, grace_seconds=terminate_grace_seconds):
                raise A2RemoteCandidateError("cancelled remote worker could not be reaped")
            raise A2RemoteCandidateError("remote candidate was cancelled and reaped")
        if time.monotonic() >= deadline:
            if not _terminate_and_reap(identity, grace_seconds=terminate_grace_seconds):
                raise A2RemoteCandidateError("timed-out remote worker could not be reaped")
            raise A2RemoteCandidateError("remote candidate timed out and was reaped")
        _atomic_json(
            heartbeat_path,
            {
                "attempt_id": attempt_id,
                "candidate_id": candidate_id,
                "pid": identity["pid"],
                "start_tick": identity["start_tick"],
                "observed_monotonic_ns": time.monotonic_ns(),
                "status": "RUNNING",
            },
        )
        time.sleep(heartbeat_interval_seconds)

    if owned_process is not None:
        owned_process.wait(timeout=terminate_grace_seconds)
    if result_path.is_file():
        result = _validate_result(result_path, attempt_id=attempt_id, candidate_id=candidate_id)
    else:
        try:
            result = json.loads(stdout_path.read_text(encoding="utf-8").strip())
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise A2RemoteCandidateError("reaped remote worker returned no durable result") from error
        if not isinstance(result, dict):
            raise A2RemoteCandidateError("remote worker result must be an object")
        _validate_result_payload(result, attempt_id=attempt_id, candidate_id=candidate_id)
        _atomic_json(result_path, result)
    _persist_terminal_state(
        identity_path=identity_path,
        heartbeat_path=heartbeat_path,
        identity=identity,
        result=result,
        recovery_count=recovery_count,
    )
    return result


def _recover_stdout_result(
    path: Path, *, attempt_id: str, candidate_id: str
) -> dict[str, Any] | None:
    """Harvest a completed worker result before any recovery relaunch."""

    try:
        encoded = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return None
    if not encoded:
        return None
    try:
        result = json.loads(encoded)
    except json.JSONDecodeError:
        return None
    if not isinstance(result, dict):
        raise A2RemoteCandidateError("remote worker result must be an object")
    _validate_result_payload(result, attempt_id=attempt_id, candidate_id=candidate_id)
    return result


def _persist_terminal_state(
    *,
    identity_path: Path,
    heartbeat_path: Path,
    identity: Mapping[str, Any],
    result: Mapping[str, Any],
    recovery_count: int,
) -> None:
    terminal_identity = {
        **identity,
        "status": "REAPED_WITH_DURABLE_RESULT",
        "recovery_count": recovery_count,
        "process_alive": False,
        "result_sha256": result["receipt_sha256"],
    }
    _atomic_json(identity_path, terminal_identity)
    _atomic_json(
        heartbeat_path,
        {
            "attempt_id": identity["attempt_id"],
            "candidate_id": identity["candidate_id"],
            "pid": identity["pid"],
            "start_tick": identity["start_tick"],
            "observed_monotonic_ns": time.monotonic_ns(),
            "status": "REAPED_WITH_DURABLE_RESULT",
        },
    )


def _validate_result_payload(
    result: Mapping[str, Any], *, attempt_id: str, candidate_id: str
) -> None:
    unsigned = {key: value for key, value in result.items() if key != "receipt_sha256"}
    if (
        result.get("attempt_id") != attempt_id
        or result.get("candidate_id") != candidate_id
        or result.get("receipt_sha256") != canonical_sha256(unsigned)
    ):
        raise A2RemoteCandidateError("remote worker result identity drift")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-a2-remote-candidate")
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--input-manifest", type=Path, required=True)
    parser.add_argument("--remote-root", type=Path, required=True)
    parser.add_argument("--bundle-path", type=Path, required=True)
    parser.add_argument("--bundle-receipt-path", type=Path, required=True)
    parser.add_argument("--bundle-sha256", required=True)
    parser.add_argument("--bundle-receipt-sha256", required=True)
    parser.add_argument("--git-commit", required=True)
    parser.add_argument("--git-tree", required=True)
    parser.add_argument("--authority-commitment-uri", required=True)
    parser.add_argument("--authority-commitment-file-sha256", required=True)
    parser.add_argument("--remote-input-manifest-sha256", required=True)
    parser.add_argument("--owner-manifest-sha256", required=True)
    parser.add_argument("--timeout-seconds", type=int, required=True)
    args = parser.parse_args(argv)
    attempt_id = os.environ.get("MYIS_A2_ATTEMPT_ID", "")
    candidate_id = os.environ.get("MYIS_A2_CANDIDATE_ID", "")
    try:
        root = args.repository_root.resolve(strict=True)
        remote_root = args.remote_root.resolve(strict=True)
        if not root.is_relative_to(remote_root):
            raise A2RemoteCandidateError("remote repository is outside attempt root")
        _validate_launch_bindings(
            attempt_id=attempt_id,
            repository_root=root,
            input_manifest_path=args.input_manifest,
            input_manifest_sha256=args.remote_input_manifest_sha256,
            owner_manifest_sha256=args.owner_manifest_sha256,
            bundle_path=args.bundle_path,
            bundle_receipt_path=args.bundle_receipt_path,
            bundle_sha256=args.bundle_sha256,
            bundle_receipt_sha256=args.bundle_receipt_sha256,
            git_commit=args.git_commit,
            git_tree=args.git_tree,
            authority_commitment_uri=args.authority_commitment_uri,
            authority_commitment_file_sha256=args.authority_commitment_file_sha256,
        )
        worker = [
            sys.executable,
            "-m",
            "myis_research.armindex.a2_remote_retriever",
            "--repository-root",
            str(root),
            "--input-manifest",
            str(args.input_manifest),
        ]
        result = supervise_candidate(
            attempt_id=attempt_id,
            candidate_id=candidate_id,
            lifecycle_root=remote_root / "lifecycle",
            worker_argv=worker,
            timeout_seconds=args.timeout_seconds,
        )
    except (A2RemoteCandidateError, OSError, ValueError):
        print('{"status":"FAILED_CLOSED"}')
        return 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["A2RemoteCandidateError", "supervise_candidate"]
