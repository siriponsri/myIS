"""Independently verify the repository-level ArmIndex migration invariants."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import yaml


STARTING_COMMIT = "abb8e1981c652fc14c3a9b779b99372e1a401b2a"
HISTORICAL_PATHS = (
    "control/campaigns/scope-autoindex-v1.yaml",
    "campaigns/scope-autoindex-v1",
    "schemas/scope-dsl.v1.json",
    "src/myis_research/scope",
)


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=root, check=False, capture_output=True, text=True
    )


def verify(root: Path) -> dict[str, object]:
    root = root.resolve(strict=True)
    campaign = yaml.safe_load(
        (root / "control/campaigns/armindex-multiretriever-v2.yaml").read_text(encoding="utf-8")
    )
    layout = yaml.safe_load((root / "control/layout.v2.yaml").read_text(encoding="utf-8"))
    source_of_truth = yaml.safe_load(
        (root / "control/source-of-truth.yaml").read_text(encoding="utf-8")
    )
    migration = json.loads(
        (root / "archive/migration-records/armindex-20260804/migration-manifest.v1.json").read_text(
            encoding="utf-8"
        )
    )
    state = json.loads(
        (root / "campaigns/armindex-multiretriever/migration-state.v1.json").read_text(
            encoding="utf-8"
        )
    )
    readme = (root / "README.md").read_text(encoding="utf-8")
    plan = (root / "PLAN.md").read_text(encoding="utf-8")

    records = {item["id"]: item for item in source_of_truth["records"]}
    armindex = campaign["campaign"]
    checks = {
        "in_place_repository_history": (
            _git(root, "merge-base", "--is-ancestor", STARTING_COMMIT, "HEAD").returncode == 0
            and migration["new_repository_created"] is False
            and migration["history_rewritten"] is False
        ),
        "root_authority_is_armindex": (
            "# ArmIndex" in readme
            and "# ArmIndex Research Plan" in plan
            and records["active_armindex_program"]["active_campaign"]
            == "campaigns/armindex-multiretriever-v2"
        ),
        "scope_is_historical_only": (
            layout["historical_campaign_roots"] == ["campaigns/scope-autoindex-v1"]
            and records["protocol"]["status"] == "historical_read_only"
        ),
        "p1_scope_evidence_unchanged": (
            _git(root, "diff", "--quiet", STARTING_COMMIT, "--", *HISTORICAL_PATHS).returncode == 0
        ),
        "armindex_measured_counters_zero": (
            armindex["migration_measured_runs"] == 0
            and armindex["selection_accesses"] == 0
            and armindex["final_accesses"] == 0
            and state["measured_runs"] == 0
            and state["candidate_count"] == 0
        ),
        "selection_and_final_closed": (
            campaign["protocol"]["final_split_open"] is False
            and campaign["protocol"]["measured_execution_allowed"] is False
            and state["final_split"] == "closed"
            and state["d2_open_final"] == "waiting_owner"
            and state["d3_submit_release"] == "waiting_owner"
        ),
        "patembed_not_commercial_default": (
            next(item for item in campaign["arms"] if item["id"] == "ARM-03")["commercial_status"]
            == "research_non_commercial"
        ),
        "readme_has_no_unmeasured_benchmark_claim": (
            "No ArmIndex benchmark result exists yet." in readme
            and "does not claim a win" in readme
            and "These are target domains, not claims" in readme
        ),
        "license_decision_remains_owner_follow_up": (
            "Repository license decision pending." in readme
            and migration.get("license_decision", "owner_follow_up_required")
            == "owner_follow_up_required"
        ),
    }
    return {
        "schema_version": "myis.armindex-independent-verifier.v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "check_count": len(checks),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    result = verify(args.repository_root)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
