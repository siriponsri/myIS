"""Command-line entry point for offline ArmIndex engineering fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import yaml

from .adapter_fixture import run_adapter_fixture
from .arms import ArmRegistry
from .contracts import grouped_json_schemas, load_campaign
from .feasibility import run_compute_storage_feasibility_fixture
from .fixture import run_synthetic_fixture
from .resource_proposal import load_and_validate_gpu_proposal


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myis-armindex")
    commands = parser.add_subparsers(dest="command", required=True)
    status = commands.add_parser("status", help="show aggregate-safe ArmIndex migration status")
    status.add_argument("--repository-root", type=Path, default=Path.cwd())
    validate = commands.add_parser("validate", help="validate campaign, schemas, and arm registry")
    validate.add_argument("--repository-root", type=Path, default=Path.cwd())
    fixture = commands.add_parser("fixture", help="run the disposable synthetic ARM-01 slice")
    fixture.add_argument("--repository-root", type=Path, default=Path.cwd())
    fixture.add_argument("--output", type=Path)
    adapter_fixture = commands.add_parser(
        "adapter-fixture",
        help="run the synthetic-only A1.1 five-arm adapter and ARM-01 CPU fixture",
    )
    adapter_fixture.add_argument("--repository-root", type=Path, default=Path.cwd())
    adapter_fixture.add_argument("--output", type=Path)
    adapter_fixture.add_argument("--repetitions", type=int, default=11)
    feasibility = commands.add_parser(
        "feasibility-fixture",
        help="run the synthetic-only A0.8 CPU compute and storage fixture",
    )
    feasibility.add_argument("--repository-root", type=Path, default=Path.cwd())
    feasibility.add_argument("--output", type=Path)
    feasibility.add_argument("--repetitions", type=int, default=11)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = args.repository_root.resolve()
    campaign = load_campaign(root)

    if args.command == "status":
        current_phase = next(
            (phase for phase in campaign["phases"] if phase.get("status") != "complete"),
            campaign["phases"][-1],
        )
        current_task = next(
            (
                task
                for task in current_phase.get("tasks", [])
                if task.get("status") not in {"complete", "locked_owner_D2", "locked_owner_D3"}
            ),
            current_phase.get("tasks", [{}])[-1],
        )
        payload = {
            "schema_version": "myis.armindex-cli-status.v1",
            "campaign_id": campaign["campaign"]["id"],
            "campaign_status": campaign["campaign"]["status"],
            "current_phase": current_phase["id"],
            "current_task": current_task.get("id"),
            "evidence_class": campaign["campaign"]["evidence_class"],
            "scientific_authority": False,
            "measured_runs": campaign["campaign"]["migration_measured_runs"],
            "selection_accesses": campaign["campaign"]["selection_accesses"],
            "final_accesses": campaign["campaign"]["final_accesses"],
            "model_download_allowed": campaign["protocol"]["model_download_allowed"],
        }
    elif args.command == "validate":
        schemas = grouped_json_schemas()
        for filename, expected in schemas.items():
            path = root / "schemas" / "armindex" / filename
            actual = json.loads(path.read_text(encoding="utf-8"))
            if actual != expected:
                raise ValueError(f"generated ArmIndex schema drift: {filename}")
        capabilities = ArmRegistry().capabilities()
        proposal = load_and_validate_gpu_proposal(root)
        payload = {
            "schema_version": "myis.armindex-cli-validation.v1",
            "status": "PASS",
            "campaign_id": campaign["campaign"]["id"],
            "contract_schema_groups": len(schemas),
            "registered_arms": len(capabilities),
            "runnable_fixture_arms": sum(
                item.fixture_status.startswith("runnable_fixture") for item in capabilities
            ),
            "unresolved_dense_arms": sum(
                item.fixture_status == "declared_unresolved_model_not_downloaded"
                for item in capabilities
            ),
            "a1_2_gpu_proposal_status": proposal["status"],
            "scientific_authority": False,
            "measured_execution": False,
        }
    elif args.command == "fixture":
        artifacts = run_synthetic_fixture(args.output)
        payload = artifacts.summary()
    elif args.command == "adapter-fixture":
        artifacts = run_adapter_fixture(args.output, repetitions=args.repetitions)
        payload = artifacts.summary()
    else:
        artifacts = run_compute_storage_feasibility_fixture(
            args.output,
            repetitions=args.repetitions,
        )
        payload = artifacts.summary()

    print(yaml.safe_dump(payload, allow_unicode=False, sort_keys=True), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
