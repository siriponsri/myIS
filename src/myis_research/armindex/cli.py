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
        # Prefer the validated aggregate-safe read model once a measured
        # closeout exists. The campaign file remains useful as the fallback
        # for historical/scaffold checkouts that predate the projection.
        read_model_path = root / "projections/read-model/read-model.v2.json"
        if read_model_path.is_file():
            read_model = json.loads(read_model_path.read_text(encoding="utf-8"))
            project = read_model.get("project", {})
            armindex = read_model.get("armindex", {})
            closeout = armindex.get("a2_goal004_closeout", {})
            current_phase = {"id": project.get("current_phase", current_phase["id"]), "tasks": []}
            current_task = {"id": project.get("current_task", current_task.get("id"))}
            campaign_status = armindex.get("status", campaign["campaign"]["status"])
            evidence_class = closeout.get("evidence_class", campaign["campaign"]["evidence_class"])
            current_phase_id = str(project.get("current_phase", ""))
            if current_phase_id.startswith("A6_"):
                scientific_authority = False
            elif current_phase_id == "A7_SEVEN_LAYER_RETRIEVAL_DIAGNOSIS":
                audit_path = root / "control/armindex/a7/a7-result-integrity-audit-20260823.json"
                try:
                    audit = json.loads(audit_path.read_text(encoding="utf-8"))
                except (OSError, UnicodeError, json.JSONDecodeError):
                    audit = {}
                scientific_authority = audit.get("status") == "PASS_A7_RESULT_INTEGRITY"
            else:
                scientific_authority = bool(closeout.get("scientific_authority", False))
            counters = armindex.get("counters", {})
            measured_runs = counters.get("measured_runs", campaign["campaign"]["migration_measured_runs"])
            selection_accesses = counters.get("selection_accesses", campaign["campaign"]["selection_accesses"])
            final_accesses = counters.get("final_accesses", campaign["campaign"]["final_accesses"])
        else:
            campaign_status = campaign["campaign"]["status"]
            evidence_class = campaign["campaign"]["evidence_class"]
            scientific_authority = False
            measured_runs = campaign["campaign"]["migration_measured_runs"]
            selection_accesses = campaign["campaign"]["selection_accesses"]
            final_accesses = campaign["campaign"]["final_accesses"]
        payload = {
            "schema_version": "myis.armindex-cli-status.v1",
            "campaign_id": campaign["campaign"]["id"],
            "campaign_status": campaign_status,
            "current_phase": current_phase["id"],
            "current_task": current_task.get("id"),
            "evidence_class": evidence_class,
            "scientific_authority": scientific_authority,
            "measured_runs": measured_runs,
            "selection_accesses": selection_accesses,
            "final_accesses": final_accesses,
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
