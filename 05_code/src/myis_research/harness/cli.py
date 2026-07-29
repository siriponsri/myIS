"""Low-dev command line for local harness checks and offline demos."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

import yaml

import structlog

from ..brain_drive import run_brain_drive_demo
from .drafts import DraftValidationError
from .reproduction import HANDOFF_READY_EXIT_CODE, WAITING_GATE_EXIT_CODE, reproduce_dapfam
from .runner import KERNEL_VERSION
from .validation import validate_run_bundle


def _doctor(research_root: Path, mlflow_root: Path) -> dict[str, object]:
    checks = {
        "research_root": research_root.is_dir(),
        "source_package": (research_root / "05_code" / "src" / "myis_research").is_dir(),
        "mlflow_root": mlflow_root.is_dir(),
        "mlflow_database": (mlflow_root / "database" / "mlflow.db").is_file(),
        "mlflow_artifacts": (mlflow_root / "artifacts").is_dir(),
        "structlog_version": structlog.__version__ == "26.1.0",
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "kernel_version": KERNEL_VERSION, "checks": checks}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myis-harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="check local Research and MLflow prerequisites")
    doctor.add_argument("--research-root", type=Path, default=Path.cwd())
    doctor.add_argument("--mlflow-root", type=Path, required=True)

    demo = subparsers.add_parser("demo", help="run the approved offline Brain-drive fixture")
    demo.add_argument("--workdir", type=Path, required=True)
    demo.add_argument("--mlflow-root", type=Path, required=True)

    validate = subparsers.add_parser("validate", help="validate an immutable run bundle")
    validate.add_argument("run_dir", type=Path)
    validate.add_argument("--split-hash")

    reproduce = subparsers.add_parser("reproduce", help="non-executable reproduction preparation")
    reproduce_targets = reproduce.add_subparsers(dest="reproduction_target", required=True)
    dapfam = reproduce_targets.add_parser("dapfam", help="validate a draft and refuse until G1")
    dapfam.add_argument("--manifest", type=Path, help="draft RunSpec YAML under 03_experiments/templates")
    dapfam.add_argument(
        "--dry-run",
        "--validate-draft",
        dest="validate_draft",
        action="store_true",
        help="validate a non-executable draft only; never starts reproduction",
    )
    dapfam.add_argument("--owner-batch", type=Path, help="validated external G1 Owner-value batch")
    dapfam.add_argument("--g1-decision", type=Path, help="immutable approved G1 decision record")
    dapfam.add_argument("--frozen-runspec", type=Path, help="G1-bound frozen F1 RunSpec")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        result = _doctor(args.research_root.resolve(), args.mlflow_root.resolve())
    elif args.command == "demo":
        output = run_brain_drive_demo(args.workdir.resolve(), mlflow_root=args.mlflow_root.resolve())
        result = {"status": "PASS", "run_dir": output["run_dir"], "report": output["report"]}
    elif args.command == "validate":
        result = validate_run_bundle(args.run_dir.resolve(), expected_split_hash=args.split_hash)
    else:
        try:
            result = reproduce_dapfam(
                repository_root=Path.cwd().resolve(),
                manifest=args.manifest,
                validate_draft=args.validate_draft,
                owner_batch=args.owner_batch,
                g1_decision=args.g1_decision,
                frozen_runspec=args.frozen_runspec,
            )
        except DraftValidationError as error:
            if args.validate_draft:
                result = {
                    "status": "WAITING_GATE",
                    "gate": "G1",
                    "gate_status": "pending",
                    "reason": "DRAFT_VALIDATION_FAILED",
                    "message": str(error),
                    "executor_available": False,
                    "scientific_run": False,
                    "dataset_access": "none",
                    "artifact_count": 0,
                    "scientific_metric_count": 0,
                }
            else:
                result = _blocked_handoff_result()
        except (OSError, ValueError, yaml.YAMLError, subprocess.SubprocessError):
            result = _blocked_handoff_result()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.command == "reproduce":
        return HANDOFF_READY_EXIT_CODE if result["status"] == "HANDOFF_READY_EXECUTOR_UNAVAILABLE" else WAITING_GATE_EXIT_CODE
    return 0 if result["status"] == "PASS" else 1


def _blocked_handoff_result() -> dict[str, object]:
    """Return a payload-safe refusal for malformed G1 handoff inputs."""

    return {
        "status": "BLOCKED",
        "gate": "G1",
        "gate_status": "pending",
        "reason": "G1_HANDOFF_VALIDATION_FAILED",
        "executor_available": False,
        "scientific_run": False,
        "dataset_access": "none",
        "artifact_count": 0,
        "scientific_metric_count": 0,
    }


if __name__ == "__main__":
    raise SystemExit(main())
