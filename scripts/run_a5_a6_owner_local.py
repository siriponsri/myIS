"""Run a hash-bound A5/A6 executor against an Owner-local payload.

This is intentionally a small execution adapter rather than a scientific
evaluator.  The protected bundle is never copied or serialized by this
adapter.  A caller supplies a mounted Owner Store path through
``--payload-root`` and an executor command which consumes that path through
the ``ARMindex_PAYLOAD_ROOT`` environment variable.  Only aggregate-safe
progress and a final receipt are written by this script.

The executor must emit optional progress lines of the form::

    ARMIndex_PROGRESS completed=123 total=872

The command is run without a shell.  This makes the adapter suitable for a
fresh remote root where the Owner Store is mounted locally, while refusing a
missing payload or an unbound predecessor receipt before any work starts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from typing import Any, Iterable, Mapping

try:
    import resource
except ImportError:  # pragma: no cover - Windows runner
    resource = None  # type: ignore[assignment]


SCHEMA = "myis.armindex-a5-a6-owner-local-runner.v1"
RECEIPT_SCHEMA = "myis.armindex-a5-a6-owner-local-receipt.v1"
PHASES = {
    "A5": {"expected_units": 872, "winner_count": 2, "predecessor": None},
    "A6": {"expected_units": 45336, "winner_count": 1, "predecessor": "PASS_A5_FINAL_CONFIRMATION"},
}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
ATTEMPT = re.compile(r"^a[56]-goal001-[0-9]{8}T[0-9]{6}Z-[a-z0-9][a-z0-9._-]{2,31}$")
PROGRESS = re.compile(r"ARMIndex_PROGRESS\s+completed=(\d+)\s+total=(\d+)")
FORBIDDEN_KEYS = re.compile(
    r"(?:qrel|query[_-]?ids?|per[_-]?query|membership|credentials?|model[_-]?payload|provider[_-]?payload|raw[_-]?ids?|rankings$)",
    re.IGNORECASE,
)


class RunnerError(ValueError):
    """Raised when a run would cross the protected or evidence boundary."""


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    if path.exists():
        if path.is_symlink() or path.read_text(encoding="utf-8") != text:
            raise RunnerError(f"immutable artifact differs: {path}")
        return
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _replace_json(path: Path, value: Mapping[str, Any]) -> None:
    """Atomically advance a mutable checkpoint; receipts remain immutable."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise RunnerError(f"checkpoint is a symlink: {path}")
    text = json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _safe_dir(path: Path, *, root: Path, role: str) -> Path:
    if path.is_symlink():
        raise RunnerError(f"{role} must not be a symlink")
    try:
        candidate = path.resolve(strict=True)
    except OSError as error:
        raise RunnerError(f"{role} is missing") from error
    if not candidate.is_dir() or not _within(candidate, root):
        raise RunnerError(f"{role} must be a real directory inside Owner Store")
    return candidate


def _assert_aggregate(value: Any, *, location: str = "result") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if FORBIDDEN_KEYS.search(str(key)):
                raise RunnerError(f"protected field in aggregate result: {location}.{key}")
            _assert_aggregate(item, location=f"{location}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_aggregate(item, location=f"{location}[{index}]")


def _load_object(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RunnerError(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise RunnerError(f"{role} must be a JSON object")
    return value


def validate_manifest(value: Mapping[str, Any], *, phase: str) -> dict[str, Any]:
    item = dict(value)
    spec = PHASES.get(phase)
    if spec is None:
        raise RunnerError(f"unsupported phase: {phase}")
    required = {
        "schema_version", "phase", "attempt_id", "status", "execution_permitted",
        "expected_units", "winner_count", "payload_scope", "remote_upload_allowed",
        "protected_payload_included", "selection_accesses", "final_accesses",
        "executor_sha256", "manifest_sha256",
    }
    if set(item) != required:
        raise RunnerError("manifest fields are incomplete or unexpected")
    if item["schema_version"] != SCHEMA or item["phase"] != phase or item["status"] != "READY":
        raise RunnerError("manifest schema/status is invalid")
    if not isinstance(item["attempt_id"], str) or ATTEMPT.fullmatch(item["attempt_id"]) is None:
        raise RunnerError("attempt identity is invalid")
    if item["execution_permitted"] is not True or item["expected_units"] != spec["expected_units"]:
        raise RunnerError("execution is not admitted for this phase")
    if item["winner_count"] != spec["winner_count"] or item["payload_scope"] != "owner_local_only":
        raise RunnerError("frozen winner/payload scope is invalid")
    if item["remote_upload_allowed"] is not False or item["protected_payload_included"] is not False:
        raise RunnerError("manifest permits protected payload transport")
    if item["selection_accesses"] != 0 or item["final_accesses"] != 0:
        raise RunnerError("manifest has stale access counters")
    if not isinstance(item["executor_sha256"], str) or SHA256.fullmatch(item["executor_sha256"]) is None:
        raise RunnerError("executor hash is invalid")
    body = {key: value for key, value in item.items() if key != "manifest_sha256"}
    if item["manifest_sha256"] != _sha(body):
        raise RunnerError("manifest hash mismatch")
    return item


def _validate_predecessor(path: Path, manifest: Mapping[str, Any], phase: str) -> str | None:
    if phase != "A6":
        return None
    predecessor = _load_object(path, role="A5 predecessor receipt")
    _assert_aggregate(predecessor, location="predecessor")
    if predecessor.get("terminal_state", predecessor.get("status")) != "PASS_A5_FINAL_CONFIRMATION":
        raise RunnerError("A6 requires PASS_A5_FINAL_CONFIRMATION predecessor")
    if predecessor.get("winner_count") != 1 or predecessor.get("final_accesses") != 1:
        raise RunnerError("A6 predecessor is not exactly one frozen winner")
    digest = _sha(predecessor)
    return digest


def _checkpoint_body(manifest: Mapping[str, Any], completed: int, total: int, *, status: str) -> dict[str, Any]:
    body = {
        "schema_version": f"{SCHEMA}.checkpoint",
        "status": status,
        "phase": manifest["phase"],
        "attempt_id": manifest["attempt_id"],
        "completed_units": completed,
        "expected_units": total,
        "manifest_sha256": manifest["manifest_sha256"],
        "protected_payload_included": False,
    }
    return {**body, "checkpoint_sha256": _sha(body)}


def _resource_snapshot() -> dict[str, int]:
    if resource is None:
        return {"child_max_rss_kb": 0}
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {"child_max_rss_kb": int(getattr(usage, "ru_maxrss", 0))}


def run_phase(
    *,
    phase: str,
    manifest_path: Path,
    owner_store_root: Path,
    attempt_root: Path,
    payload_root: Path,
    executor: list[str],
    predecessor_receipt: Path | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    manifest = validate_manifest(_load_object(manifest_path, role="execution manifest"), phase=phase)
    root = _safe_dir(owner_store_root, root=owner_store_root.parent, role="Owner Store root")
    attempt = attempt_root.resolve()
    if attempt.exists() and (attempt.is_symlink() or not attempt.is_dir()):
        raise RunnerError("attempt root is unsafe")
    if not _within(attempt, root) or _within(attempt, Path.cwd().resolve()):
        raise RunnerError("attempt root must be outside the repository and inside Owner Store")
    payload = _safe_dir(payload_root, root=root, role="Owner-local payload root")
    predecessor_sha = None
    if phase == "A6":
        if predecessor_receipt is None:
            raise RunnerError("A6 requires an A5 predecessor receipt")
        predecessor_sha = _validate_predecessor(predecessor_receipt, manifest, phase)
    if not executor or any(not isinstance(part, str) or not part for part in executor):
        raise RunnerError("executor command is empty")
    executor_sha = _sha(executor)
    if executor_sha != manifest["executor_sha256"]:
        raise RunnerError("executor command hash does not match manifest")
    attempt.mkdir(parents=True, exist_ok=True)
    checkpoint_path = attempt / "checkpoint.json"
    receipt_path = attempt / "receipt.json"
    log_path = attempt / "executor.log"
    if receipt_path.exists():
        receipt = _load_object(receipt_path, role="existing receipt")
        if receipt.get("status") == "PASS":
            return receipt
        if not resume:
            raise RunnerError("attempt has an existing non-PASS receipt; use --resume")
    completed = 0
    if checkpoint_path.exists():
        checkpoint = _load_object(checkpoint_path, role="checkpoint")
        if checkpoint.get("manifest_sha256") != manifest["manifest_sha256"] or checkpoint.get("attempt_id") != manifest["attempt_id"]:
            raise RunnerError("checkpoint is not bound to this manifest/attempt")
        completed = int(checkpoint.get("completed_units", 0))
        if completed < 0 or completed > manifest["expected_units"]:
            raise RunnerError("checkpoint coverage is invalid")
    started = time.monotonic()
    env = os.environ.copy()
    env.update({
        "ARMIndex_PHASE": phase,
        "ARMIndex_ATTEMPT_ID": manifest["attempt_id"],
        "ARMIndex_PAYLOAD_ROOT": str(payload),
        "ARMIndex_EXPECTED_UNITS": str(manifest["expected_units"]),
        "ARMIndex_RESUME_COMPLETED": str(completed),
    })
    print(f"[ARMIndex][{phase}][START] attempt={manifest['attempt_id']} expected={manifest['expected_units']}", flush=True)
    _replace_json(checkpoint_path, _checkpoint_body(manifest, completed, manifest["expected_units"], status="RUNNING"))
    result_code = 1
    last_completed = completed
    with log_path.open("a", encoding="utf-8", buffering=1) as log:
        process = subprocess.Popen(executor, cwd=attempt, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        assert process.stdout is not None
        for line in process.stdout:
            log.write(line)
            sys.stdout.write(line)
            sys.stdout.flush()
            match = PROGRESS.search(line)
            if match:
                observed, observed_total = int(match.group(1)), int(match.group(2))
                if observed_total != manifest["expected_units"] or observed < last_completed or observed > observed_total:
                    process.terminate()
                    raise RunnerError("executor emitted invalid progress coverage")
                last_completed = observed
                print(f"[ARMIndex][{phase}][PROGRESS] {observed}/{observed_total}", flush=True)
                _replace_json(checkpoint_path, _checkpoint_body(manifest, observed, observed_total, status="RUNNING"))
        result_code = process.wait()
    elapsed = time.monotonic() - started
    result_path = attempt / "result.json"
    result_sha = None
    result_status = "MISSING"
    if result_path.is_file() and not result_path.is_symlink():
        result = _load_object(result_path, role="executor result")
        _assert_aggregate(result)
        result_sha = _sha(result)
        result_status = str(result.get("status", "UNKNOWN"))
    status = "PASS" if result_code == 0 and last_completed == manifest["expected_units"] and result_sha is not None else "FAILED"
    body = {
        "schema_version": RECEIPT_SCHEMA,
        "status": status,
        "phase": phase,
        "attempt_id": manifest["attempt_id"],
        "manifest_sha256": manifest["manifest_sha256"],
        "executor_sha256": executor_sha,
        "completed_units": last_completed,
        "expected_units": manifest["expected_units"],
        "executor_exit_code": result_code,
        "executor_result_status": result_status,
        "terminal_state": (
            "PASS_A5_FINAL_CONFIRMATION" if phase == "A5" and status == "PASS"
            else "PASS_A6_FULL_DAPFAM_MATERIALIZATION" if phase == "A6" and status == "PASS"
            else status
        ),
        "winner_count": manifest["winner_count"],
        "result_sha256": result_sha,
        "elapsed_seconds": round(elapsed, 6),
        "resources": _resource_snapshot(),
        "predecessor_receipt_sha256": predecessor_sha,
        "selection_accesses": 0,
        "final_accesses": 1 if phase == "A5" and status == "PASS" else 0,
        "protected_payload_included": False,
        "owner_local_only": True,
    }
    receipt = {**body, "receipt_sha256": _sha(body)}
    _atomic_json(receipt_path, receipt)
    _replace_json(checkpoint_path, _checkpoint_body(manifest, last_completed, manifest["expected_units"], status=status))
    print(f"[ARMIndex][{phase}][{status}] completed={last_completed}/{manifest['expected_units']}", flush=True)
    return receipt


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=tuple(PHASES), required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--owner-store-root", type=Path, required=True)
    parser.add_argument("--attempt-root", type=Path, required=True)
    parser.add_argument("--payload-root", type=Path, required=True)
    parser.add_argument("--predecessor-receipt", type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("executor", nargs=argparse.REMAINDER, help="executor command after --")
    args = parser.parse_args(list(argv) if argv is not None else None)
    executor = list(args.executor)
    if executor and executor[0] == "--":
        executor = executor[1:]
    try:
        receipt = run_phase(
            phase=args.phase,
            manifest_path=args.manifest,
            owner_store_root=args.owner_store_root,
            attempt_root=args.attempt_root,
            payload_root=args.payload_root,
            executor=executor,
            predecessor_receipt=args.predecessor_receipt,
            resume=args.resume,
        )
    except RunnerError as error:
        print(f"[ARMIndex][{args.phase}][BLOCKED] {error}", file=sys.stderr)
        return 2
    print(json.dumps({"status": receipt["status"], "receipt_sha256": receipt["receipt_sha256"]}, sort_keys=True))
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["RunnerError", "PHASES", "SCHEMA", "run_phase", "validate_manifest"]
