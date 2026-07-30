"""Validate and mirror the governed document catalog into local MLflow."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from myis_research.dashboard.progress import parse_plan
from myis_research.dashboard.projections import load_governance_document_catalog
from myis_research.mlflow_mirror import (
    MLflowMirror,
    MirrorArtifact,
    MirrorKind,
    MirrorSpec,
    MirrorStage,
    ProjectionLineage,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
KIND_MAP = {
    "docs": MirrorKind.DOC,
    "rules": MirrorKind.RULE,
    "tools": MirrorKind.TOOL,
}


def _git_state() -> tuple[str, bool]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    dirty = bool(
        subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=normal"],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    return commit, dirty


def build_sync_plan() -> dict[str, object]:
    plan = parse_plan(REPOSITORY_ROOT / "PLAN.md")
    catalog = load_governance_document_catalog(REPOSITORY_ROOT, plan)
    commit, dirty = _git_state()
    documents = []
    for item in catalog["documents"]:
        documents.append(
            {
                "document_id": item["document_id"],
                "title_en": item["title_en"],
                "title_th": item["title_th"],
                "sha256": item["sha256"],
                "kind": item["kind"],
                "phase_ids": item["phase_ids"],
                "task_ids": item["task_ids"],
                "gate_ids": item["gate_ids"],
                "linear_issue_ids": item["linear_issue_ids"],
                "dashboard_content_id": item["dashboard_content_id"],
            }
        )
    return {
        "schema_version": "myis.mlflow-governance-sync-plan.v1",
        "status": "validated",
        "write_requested": False,
        "git_commit": commit,
        "git_dirty": dirty,
        "plan_sha256": plan.sha256,
        "catalog_sha256": catalog["source_sha256"],
        "experiment_name": "myis-research-catalog",
        "document_count": len(documents),
        "documents": documents,
    }


def sync_documents(store_root: Path | None = None) -> dict[str, object]:
    plan = parse_plan(REPOSITORY_ROOT / "PLAN.md")
    catalog = load_governance_document_catalog(REPOSITORY_ROOT, plan)
    commit, dirty = _git_state()
    if dirty:
        raise RuntimeError("repository must be clean before mirroring governance documents")
    mirror = MLflowMirror(store_root)
    receipts = []
    for item in catalog["documents"]:
        artifact = MirrorArtifact.from_path(
            item["resolved_path"],
            kind=KIND_MAP[item["kind"]],
            canonical_root=REPOSITORY_ROOT,
            artifact_name=item["document_id"],
        )
        lineage = ProjectionLineage(
            plan_sha256=plan.sha256,
            phase_ids=tuple(item["phase_ids"]),
            task_ids=tuple(item["task_ids"]),
            gate_ids=tuple(item["gate_ids"]),
            linear_issue_ids=tuple(item["linear_issue_ids"]),
            dashboard_content_id=item["dashboard_content_id"],
        )
        receipt = mirror.sync(
            MirrorSpec(
                stage=MirrorStage.CATALOG,
                run_name=f"governance-{item['document_id']}",
                git_commit=commit,
                canonical_source_sha256=item["sha256"],
                tags={
                    "projection_kind": "governance-document",
                    "document_id": item["document_id"],
                    "document_title_en": item["title_en"],
                    "document_title_th": item["title_th"],
                    "document_summary_en": item["summary_en"],
                    "document_summary_th": item["summary_th"],
                },
                parameters={"artifact_count": 1, "scientific_metric_count": 0},
                projection=lineage,
            ),
            (artifact,),
        )
        receipts.append(
            {
                "document_id": item["document_id"],
                "status": receipt.status,
                "mirror_key": receipt.mirror_key,
                "mlflow_run_id": receipt.mlflow_run_id,
                "artifact_sha256": item["sha256"],
            }
        )
    complete = all(item["status"] in {"synced", "already_synced"} for item in receipts)
    return {
        "schema_version": "myis.mlflow-governance-sync-report.v1",
        "status": "complete" if complete else "sync_deferred",
        "write_requested": True,
        "scientific_run": False,
        "scientific_metric_count": 0,
        "git_commit": commit,
        "plan_sha256": plan.sha256,
        "catalog_sha256": catalog["source_sha256"],
        "experiment_name": "myis-research-catalog",
        "document_count": len(receipts),
        "receipts": receipts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="validate and print the sync plan without writing MLflow")
    parser.add_argument("--store", type=Path, help="approved persistent MLflow store outside Git")
    arguments = parser.parse_args()
    report = build_sync_plan() if arguments.dry_run else sync_documents(arguments.store)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] in {"validated", "complete"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
