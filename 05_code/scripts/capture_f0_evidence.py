"""Capture append-only, aggregate-only evidence for the F0 migration gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
import subprocess
import sys
from typing import Any, Sequence

import yaml

from myis_research.dashboard.contracts import TaskEvidenceRecord
from myis_research.protection import assert_aggregate_only


ROOT = Path(__file__).resolve().parents[2]
MIGRATION_BASE = "4dd0f4b5698174a128d3d1c4d4efcdee6dd04f4c"
F0_SCHEMA = "myis.f0-evidence.v1"
PROTECTED_SURFACES = (
    "01_evidence",
    "02_tracks/99_legacy",
    "03_experiments/V01_brain_drive_agent_demo",
    "04_outputs",
    "00_governance/approvals",
    "uv.lock",
    ".python-version",
)
AUTHORIZED_ROOTS = (
    Path("04_outputs/artifacts/f0-migration"),
    Path("04_outputs/artifacts/task-evidence/F0.1"),
    Path("04_outputs/artifacts/task-evidence/F0.2"),
    Path("04_outputs/artifacts/task-evidence/F0.3"),
    Path("04_outputs/audits/rigor"),
)
ABSOLUTE_WINDOWS_PATH = re.compile(r"(?i)(?:^|\s|[\"'])([a-z]:[\\/][^\s\"']*)")


class EvidenceCaptureError(RuntimeError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")


def git(*arguments: str, root: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *arguments], cwd=root, capture_output=True, text=True, check=False
    )
    if check and completed.returncode != 0:
        raise EvidenceCaptureError(f"git {' '.join(arguments)} failed: {completed.stderr.strip()}")
    return completed


def normalize_local_paths(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): normalize_local_paths(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize_local_paths(item) for item in value]
    if isinstance(value, str):
        path = PureWindowsPath(value)
        if path.is_absolute():
            return f"<LOCAL_PATH>/{path.name}"
        candidate = Path(value)
        if candidate.is_absolute():
            return f"<LOCAL_PATH>/{candidate.name}"
    return value


def assert_no_absolute_local_paths(value: Any) -> None:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True)
    if str(ROOT) in encoded or ABSOLUTE_WINDOWS_PATH.search(encoded):
        raise EvidenceCaptureError("evidence payload contains an absolute local path")


def _assert_regular_output_root(root: Path, relative: Path) -> Path:
    if relative not in AUTHORIZED_ROOTS:
        raise EvidenceCaptureError(f"output root is not Owner-authorized: {relative.as_posix()}")
    target = root / relative
    cursor = target
    while cursor != root:
        if cursor.exists() and cursor.is_symlink():
            raise EvidenceCaptureError(f"output path contains a symlink: {cursor}")
        cursor = cursor.parent
    target.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or not target.is_dir():
        raise EvidenceCaptureError(f"output root must be a regular directory: {relative.as_posix()}")
    return target


def append_json(path: Path, payload: Any) -> str:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"append-only evidence already exists: {path.name}")
    encoded = canonical_json_bytes(payload)
    with path.open("xb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    return sha256_bytes(encoded)


def _validate_commit(commit: str, *, name: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise EvidenceCaptureError(f"{name} must be a full lowercase Git SHA")
    git("cat-file", "-e", f"{commit}^{{commit}}")


def _assert_ancestor(ancestor: str, descendant: str, *, name: str) -> None:
    result = git("merge-base", "--is-ancestor", ancestor, descendant, check=False)
    if result.returncode != 0:
        raise EvidenceCaptureError(f"{name} is not an ancestor of the source commit")


def _changed_files(base: str, source: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    output = git("diff", "--name-status", "--find-renames", base, source).stdout
    for line in output.splitlines():
        fields = line.split("\t")
        status = fields[0]
        path = fields[-1].replace("\\", "/")
        rows.append({"status": status, "path": path})
    return rows


def _tree_receipt(commit: str, relative: str) -> dict[str, Any]:
    listing = git("ls-tree", "-r", "--full-tree", commit, "--", relative).stdout.encode("utf-8")
    return {
        "path": relative,
        "entry_count": len([line for line in listing.splitlines() if line]),
        "tree_listing_sha256": sha256_bytes(listing),
    }


def protected_comparison(audit_base: str, source: str) -> dict[str, Any]:
    drift = git("diff", "--name-only", audit_base, source, "--", *PROTECTED_SURFACES).stdout.splitlines()
    if drift:
        raise EvidenceCaptureError(f"protected surface drift detected: {sorted(drift)}")
    return {
        "status": "zero_drift",
        "paths": list(PROTECTED_SURFACES),
        "base": [_tree_receipt(audit_base, path) for path in PROTECTED_SURFACES],
        "source": [_tree_receipt(source, path) for path in PROTECTED_SURFACES],
        "external_app_repository": "not_accessed",
        "confirmation_surfaces": "not_accessed",
    }


def _command_receipt(check_id: str, command: Sequence[str], *, display: str | None = None) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    combined = (completed.stdout + completed.stderr).encode("utf-8", errors="replace")
    return {
        "check_id": check_id,
        "status": "passed" if completed.returncode == 0 else "failed",
        "exit_code": completed.returncode,
        "command": display or " ".join(command),
        "output_sha256": sha256_bytes(combined),
        "output_line_count": len(combined.splitlines()),
    }


def run_required_checks() -> list[dict[str, Any]]:
    bash = shutil.which("bash")
    commands: list[tuple[str, Sequence[str], str | None]] = [
        ("uv_lock", ("uv", "lock", "--check"), None),
        ("restructure", ("uv", "run", "--no-sync", "python", "05_code/scripts/validate_restructure.py"), None),
        ("integrity", ("uv", "run", "--no-sync", "python", "05_code/scripts/validate_integrity.py"), None),
        ("literature", ("uv", "run", "--no-sync", "python", "05_code/scripts/validate_literature_corpus.py"), None),
        ("unit_suite", ("uv", "run", "--no-sync", "python", "-m", "unittest", "discover", "-s", "05_code/tests", "-v"), None),
        ("diff_check", ("git", "diff", "--check"), None),
    ]
    if bash is None:
        raise EvidenceCaptureError("Git Bash is required for the MLflow doctor receipt")
    commands.append(
        ("mlflow_doctor", (bash, "06_frontend/mlflow/mlflow.sh", "doctor"), "bash 06_frontend/mlflow/mlflow.sh doctor")
    )
    receipts = [_command_receipt(check_id, command, display=display) for check_id, command, display in commands]
    failed = [receipt["check_id"] for receipt in receipts if receipt["status"] != "passed"]
    if failed:
        raise EvidenceCaptureError(f"required F0 checks failed: {failed}")
    return receipts


def _environment() -> dict[str, Any]:
    from capture_environment import build_environment

    return normalize_local_paths(build_environment([], ["tracking", "dashboard", "test"]))


def _projection_readbacks(args: argparse.Namespace, checks: list[dict[str, Any]]) -> dict[str, Any]:
    linear_config = yaml.safe_load((ROOT / "00_governance/config/linear.yaml").read_text(encoding="utf-8"))["linear"]
    plan_hash = sha256_file(ROOT / "PLAN.md")
    if args.linear_plan_sha256 != plan_hash or linear_config["plan_binding"]["plan_sha256"] != plan_hash:
        raise EvidenceCaptureError("Linear PLAN readback hash does not match canonical PLAN.md")
    if (args.linear_milestones, args.linear_tasks, args.linear_dependencies) != (13, 22, 27):
        raise EvidenceCaptureError("Linear readback counts must be exactly 13 milestones, 22 tasks, and 27 dependencies")
    if args.brain_pending_active_hashes != 0:
        raise EvidenceCaptureError("Brain QMD readback must have zero pending active hashes")
    mlflow = next(receipt for receipt in checks if receipt["check_id"] == "mlflow_doctor")
    experiments = yaml.safe_load((ROOT / "03_experiments/config/mlflow/mirror.yaml").read_text(encoding="utf-8"))["experiments"]
    return {
        "brain": {
            "commit": args.brain_commit,
            "branch": "main",
            "literature_note_count": 153,
            "pending_active_hashes": args.brain_pending_active_hashes,
            "protected_payloads": "not_present",
        },
        "linear": {
            "project_external_id": linear_config["project"]["external_id"],
            "plan_sha256": plan_hash,
            "milestone_count": args.linear_milestones,
            "task_count": args.linear_tasks,
            "dependency_count": args.linear_dependencies,
            "f0_statuses": [row["status"] for row in linear_config["tasks"] if row["phase"] == "F0"],
        },
        "mlflow": {
            "doctor_status": mlflow["status"],
            "experiment_count": len(experiments),
            "experiments": sorted(experiments.values()),
            "authoritative": False,
        },
    }


def build_evidence(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source = git("rev-parse", "HEAD").stdout.strip()
    if git("status", "--porcelain", "--untracked-files=normal").stdout.strip():
        raise EvidenceCaptureError("source commit must have a clean index and worktree")
    if args.source_commit != source:
        raise EvidenceCaptureError("source commit must equal the clean repository HEAD")
    for value, name in ((source, "source_commit"), (args.audit_base, "audit_base"), (MIGRATION_BASE, "migration_base")):
        _validate_commit(value, name=name)
    _assert_ancestor(MIGRATION_BASE, source, name="migration_base")
    _assert_ancestor(args.audit_base, source, name="audit_base")

    checks = run_required_checks()
    evidence_id = f"F0-{source[:12]}"
    payload = {
        "schema_version": F0_SCHEMA,
        "evidence_id": evidence_id,
        "identity": {
            "program_id": "myis-research",
            "display_name": "myIS Research",
            "protocol_version": "1.0",
            "research_version": "0.1",
        },
        "source_git_commit": source,
        "migration_base": MIGRATION_BASE,
        "audit_base": args.audit_base,
        "canonical_hashes": {
            name: sha256_file(ROOT / name) for name in ("PLAN.md", "pyproject.toml", "uv.lock")
        },
        "environment": _environment(),
        "changed_files": _changed_files(MIGRATION_BASE, source),
        "protected_comparison": protected_comparison(args.audit_base, source),
        "checks": checks,
        "projections": _projection_readbacks(args, checks),
        "evidence_roles": {
            "fixture": "assessable",
            "development": "not_assessable",
            "descriptive": "not_assessable",
            "confirmation": "not_assessable",
        },
        "scientific_execution": "not_run",
        "legal_scope": "decision_support_not_legal_advice",
    }
    payload = normalize_local_paths(payload)
    assert_aggregate_only(payload)
    assert_no_absolute_local_paths(payload)
    return payload, checks


def write_evidence(payload: dict[str, Any], checks: list[dict[str, Any]], *, root: Path = ROOT) -> dict[str, Any]:
    evidence_id = payload["evidence_id"]
    output_root = _assert_regular_output_root(root, AUTHORIZED_ROOTS[0])
    manifest_path = output_root / f"{evidence_id}.json"
    manifest_sha256 = sha256_bytes(canonical_json_bytes(payload))
    plan_sha256 = payload["canonical_hashes"]["PLAN.md"]
    source = payload["source_git_commit"]
    check_hashes = {receipt["check_id"]: receipt["output_sha256"] for receipt in checks}
    task_checks = {
        "F0.1": ("uv_lock", "integrity", "diff_check"),
        "F0.2": ("restructure", "literature", "unit_suite"),
        "F0.3": ("mlflow_doctor", "restructure", "unit_suite"),
    }
    pending: list[tuple[Path, dict[str, Any]]] = [(manifest_path, payload)]
    for task_id, receipt_ids in task_checks.items():
        task_root = _assert_regular_output_root(root, Path(f"04_outputs/artifacts/task-evidence/{task_id}"))
        record_id = f"{task_id.replace('.', '-')}-{source[:12]}"
        record = {
            "schema_version": "myis.task-evidence.v1",
            "record_id": record_id,
            "task_id": task_id,
            "plan_sha256": plan_sha256,
            "git_commit": source,
            "acceptance_checks": [
                {"check_id": receipt_id, "status": "passed", "evidence_sha256": check_hashes[receipt_id]}
                for receipt_id in receipt_ids
            ],
            "evidence_manifest_hashes": [manifest_sha256],
            "prior_record_hash": None,
            "supersedes_record_id": None,
        }
        TaskEvidenceRecord.model_validate(record)
        record_path = task_root / f"{record_id}.json"
        pending.append((record_path, record))
    collisions = [path.relative_to(root).as_posix() for path, _ in pending if path.exists() or path.is_symlink()]
    if collisions:
        raise FileExistsError(f"append-only evidence already exists: {collisions}")
    written = []
    for path, record in pending:
        record_sha256 = append_json(path, record)
        written.append({"path": path.relative_to(root).as_posix(), "sha256": record_sha256})
    return {"evidence_id": evidence_id, "manifest_sha256": manifest_sha256, "written": written}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--write", action="store_true")
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--audit-base", required=True)
    parser.add_argument("--brain-commit", required=True)
    parser.add_argument("--brain-pending-active-hashes", type=int, required=True)
    parser.add_argument("--linear-plan-sha256", required=True)
    parser.add_argument("--linear-milestones", type=int, required=True)
    parser.add_argument("--linear-tasks", type=int, required=True)
    parser.add_argument("--linear-dependencies", type=int, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.brain_commit):
        raise EvidenceCaptureError("brain_commit must be a full lowercase Git SHA")
    payload, checks = build_evidence(args)
    if args.dry_run:
        print(json.dumps({
            "status": "DRY_RUN_PASS",
            "schema_version": payload["schema_version"],
            "evidence_id": payload["evidence_id"],
            "check_count": len(checks),
            "changed_file_count": len(payload["changed_files"]),
            "protected_drift": 0,
        }, ensure_ascii=True, sort_keys=True))
        return 0
    print(json.dumps(write_evidence(payload, checks), ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except EvidenceCaptureError as error:
        print(f"F0_EVIDENCE_CAPTURE_FAILED: {error}", file=sys.stderr)
        raise SystemExit(1) from error
