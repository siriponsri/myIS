"""Build the single aggregate read model consumed by Dashboard, Brain, and Paper."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from ..dapfam_p1 import DapfamP1Error, load_package
from ..kernel.canonical import canonical_sha256
from ..kernel.manifest import manifest_round_trip
from ..kernel.manifest_validation import ManifestValidationError, validate_validation_report
from ..owner_local import OwnerLocalContractError, validate_receipt
from ..p2 import (
    P2ContractError,
    P2FixtureError,
    validate_fixture_execution_manifest,
    validate_fixture_receipt,
    validate_p2_artifact,
    validate_p2_candidate_freeze_proposal,
    validate_p2_package_bundle,
    validate_p2_preflight_receipt,
)
from ..protection import assert_aggregate_only
from ..observatory.projection import load_observatory_projection
from ..armindex import ArmIndexContractError, build_armindex_projection
from ..armindex.constants import A0_8_NEXT_AUTHORIZED_ACTION


READ_MODEL_SCHEMA = "myis.read-model.v2"
PROJECTION_SCHEMA_VERSION = "myis.integrated-projection.v2"
P1_ARMS = frozenset({"R0", "R0-W"})
P1_SPLITS = frozenset({"train", "selection"})
P1_SCOPES = frozenset({"ALL", "IN", "OUT"})
P1_ACCEPTED_METRIC_FIELDS = frozenset({
    "arm", "name", "value", "n", "retrieved_relevant", "relevant_total",
    "scope", "split", "direction", "denominator", "evidence_role",
})
LEGACY_DISPOSITION_RELATIVE_PATH = Path(
    "campaigns/scope-autoindex-v1/evidence/legacy-p1-receipt.v2.disposition.json"
)
LEGACY_DISPOSITION_KEYS = frozenset({
    "schema_version", "disposition_id", "evidence_id", "source_uri",
    "source_file_sha256", "receipt_sha256", "status", "evidence_class",
    "promotable", "superseded_by", "reason_codes", "invalidation_evidence",
    "related_records", "record_sha256",
})
PROJECTION_SOURCE_PATHS = (
    "control/program.yaml",
    "control/campaigns/scope-autoindex-v1.yaml",
    "control/execution-envelope.yaml",
    "control/execution-envelope-p2.yaml",
    "control/budgets/p2-r1-primary-v1.yaml",
    "control/execution-envelope-p2-v2.yaml",
    "control/budgets/p2-r1-primary-v2.yaml",
    "control/campaigns/scope-autoindex-p2-r1-primary-v2.yaml",
    "control/runbooks/P2_MEASURED_AUTORESEARCH_V2.md",
    "archive/p2-runtime-resilience-v1-interrupted",
    "orchestration/autoresearch/p2-runtime-resilience-v2",
    "control/source-of-truth.yaml",
    "control/decisions",
    "campaigns/scope-autoindex-v1/evidence",
    "campaigns/scope-autoindex-v1/requests",
    "campaigns/scope-autoindex-v1/manifests",
    "campaigns/scope-autoindex-v1/validation-reports",
    "campaigns/scope-autoindex-v1/packages",
    "campaigns/scope-autoindex-v1/proposals",
    "campaigns/scope-autoindex-v1/preflight",
    "orchestration/audits/p2-readiness",
    "outputs/fixtures/p2",
    "outputs/observatory/fixture-v1",
    "control/assets/dapfam-p1-source.v1.json",
    "outputs/audits/rigor",
    "evidence/legacy-dapfam-inventory.v1.json",
    "schemas/read-model.v2.json",
    "schemas/p2-budget-profile.v1.json",
    "schemas/p2-request.v1.json",
    "schemas/p2-aggregate-metric.v1.json",
    "schemas/p2-train-metric.v1.json",
    "schemas/p2-candidate-ledger.v1.json",
    "schemas/p2-baseline-commitment.v1.json",
    "schemas/p2-baseline-reproduction-receipt.v1.json",
    "schemas/p2-shortlist-freeze-receipt.v1.json",
    "schemas/p2-selection-receipt.v1.json",
    "schemas/p2-manifest.v1.json",
    "schemas/p2-package.v1.json",
    "schemas/p2-preflight-receipt.v1.json",
    "schemas/p2-candidate-freeze-proposal.v1.json",
    "schemas/observatory-registry.v1.json",
    "schemas/observatory-run.v1.json",
    "schemas/observatory-artifact.v1.json",
    "schemas/observatory-prompt.v1.json",
    "schemas/observatory-metric.v1.json",
    "schemas/observatory-receipt.v1.json",
    "schemas/observatory-config.v1.json",
    "schemas/observatory-environment.v1.json",
    "schemas/observatory-failure.v1.json",
    "schemas/observatory-recovery.v1.json",
    "schemas/observatory-decision.v1.json",
    "schemas/phase-task-report.v1.json",
    "docs/observatory/REPORTING_POLICY.md",
    "docs/observatory/MEASURED_PREFLIGHT_INTEGRATION.md",
    "src/myis_research/p2",
    "src/myis_research/observatory",
    "src/myis_research/p2_cli.py",
    "src/myis_research/p2/preflight.py",
    "src/myis_research/projections/read_model.py",
    "src/myis_research/report_cli.py",
    "src/myis_research/report_records.py",
    "control/campaigns/armindex-multiretriever-v2.yaml",
    "control/budgets/armindex-migration-v2.yaml",
    "control/plans/ARMINDEX_AUTOINDEX_HARNESSOPT_CONTRACT.md",
    "schemas/armindex",
    "src/myis_research/armindex",
    "docs/research/ARMINDEX_RESEARCH_PLAN_V02.md",
    "control/armindex",
    "campaigns/armindex-multiretriever-v2/evidence",
)

P2_ARTIFACT_DIRS = ("requests", "manifests", "evidence", "packages", "reports")
P2_OFFICIAL_REVIEW_ROOT = Path("orchestration/audits/p2-readiness")
P2_FIXTURE_RECEIPT_PATH = Path("outputs/fixtures/p2/p2-fixture-pilot-v1.receipt.json")
P2_FIXTURE_MANIFEST_PATH = Path(
    "outputs/fixtures/p2/p2-fixture-pilot-v1.execution-manifest.json"
)
P2_PREFLIGHT_RECEIPT_PATH = Path(
    "campaigns/scope-autoindex-v1/preflight/p2-preflight-receipt.json"
)
P2_CANDIDATE_PROPOSAL_PATH = Path(
    "campaigns/scope-autoindex-v1/proposals/p2-candidate-freeze-proposal.v1.json"
)
P2_METRIC_FIELDS = frozenset({
    "candidate_id", "arm", "name", "value", "n", "retrieved_relevant", "relevant_total",
    "scope", "split", "direction", "denominator", "evidence_role",
})
A010_LEGACY_CODE_HARVEST_LEDGER_PATH = Path(
    "control/armindex/a0.10-legacy-code-harvest-ledger.v1.json"
)
A010_LEGACY_CODE_HARVEST_RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a0.10-legacy-code-harvest.receipt.v1.json"
)
A010_REPOSITORY_HYGIENE_AUDIT_PATH = Path(
    "outputs/audits/repository/repository-hygiene-a0.10-20260804.json"
)
A010_OUTPUT_ROOT_RELOCATION_RECEIPT_PATH = Path(
    "outputs/audits/dashboard/output-root-relocation-20260804.json"
)
A010_SOURCE_VERIFICATION_RECEIPT_PATH = Path(
    "outputs/audits/repository/thaipha-lex-source-verification-a0.10-20260804.json"
)


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def build_read_model(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    campaign_id = "scope-autoindex-v1"
    try:
        armindex = build_armindex_projection(root)
    except ArmIndexContractError:
        armindex = _empty_armindex_projection()
    armindex = {
        **armindex,
        "legacy_code_harvest": _a010_legacy_code_harvest_projection(root),
    }
    campaign_config = _load_yaml_like(root / "control" / "campaigns" / f"{campaign_id}.yaml")
    legacy_disposition = _load_legacy_disposition(root)
    manifests = _load_manifests(root / "campaigns" / campaign_id / "manifests")
    invalidated_receipt_hashes = (
        {str(legacy_disposition["receipt_sha256"])} if legacy_disposition else set()
    )
    receipts = _load_receipts(
        root / "campaigns" / campaign_id / "evidence",
        invalidated_receipt_hashes=invalidated_receipt_hashes,
    )
    validation_reports = _load_validation_reports(root / "campaigns" / campaign_id / "validation-reports")
    p1_pairs = validated_p1_matrix(manifests, receipts, validation_reports)
    p2_readiness = _p2_readiness_projection(root, campaign_config)
    observatory = load_observatory_projection(root)
    package_review: dict[str, Any] = {}
    if (root / "control/assets/dapfam-p1-source.v1.json").is_file() and p1_pairs:
        package_review = _validated_p1_package_review(root, p1_pairs)
        if not package_review:
            p1_pairs = []
    paired_manifest_hashes = {str(pair["manifest"]["manifest_sha256"]) for pair in p1_pairs}
    paired_receipts = [pair["receipt"] for pair in p1_pairs]
    mlflow_registration = _load_optional_json(root / "evidence" / "mlflow-p1-registration.v2.json")
    decisions = _load_jsonl(root / "control" / "decisions" / "ledger.jsonl")
    metrics: list[dict[str, Any]] = []
    runs: list[dict[str, Any]] = []
    experiments: dict[str, dict[str, Any]] = {}
    evidence: list[dict[str, Any]] = []
    total_actual = 0.0
    total_estimated = 0.0
    for manifest in manifests:
        if _is_p1_manifest(manifest) and str(manifest.get("manifest_sha256", "")) not in paired_manifest_hashes:
            continue
        run_id = str(manifest.get("run_id", "unknown"))
        experiment_id = str(manifest.get("experiment_id", f"exp-{run_id}"))
        experiments.setdefault(experiment_id, {"experiment_id": experiment_id, "campaign_id": campaign_id, "run_count": 0})["run_count"] += 1
        run_metrics = manifest.get("metrics", [])
        if isinstance(run_metrics, dict):
            run_metrics = [{"name": key, "value": value} for key, value in run_metrics.items()]
        for item in run_metrics if isinstance(run_metrics, list) else []:
            if isinstance(item, dict):
                metrics.append({"run_id": run_id, **item})
        resources = manifest.get("resources", {}) if isinstance(manifest.get("resources"), dict) else {}
        actual = resources.get("cost_actual")
        estimate = resources.get("cost_estimated")
        if isinstance(actual, (int, float)) and not isinstance(actual, bool):
            total_actual += float(actual)
        if isinstance(estimate, (int, float)) and not isinstance(estimate, bool):
            total_estimated += float(estimate)
        runs.append({
            "run_id": run_id,
            "manifest_sha256": manifest.get("manifest_sha256"),
            "experiment_id": experiment_id,
            "campaign_id": campaign_id,
            "stage": manifest.get("stage", "unknown"),
            "status": manifest.get("status", "unknown"),
            "arm": (manifest["method"].get("arm_id") or manifest["method"].get("arm")) if isinstance(manifest.get("method"), dict) else None,
            "source": manifest.get("inputs", {}).get("source", {}) if isinstance(manifest.get("inputs"), dict) else {},
            "owner_local_receipt_sha256": manifest.get("receipt_sha256"),
        })
        for artifact in manifest.get("artifacts", []) if isinstance(manifest.get("artifacts"), list) else []:
            if isinstance(artifact, dict) and artifact.get("sha256"):
                evidence.append({"evidence_id": artifact.get("artifact_id", artifact.get("name", "artifact")), "sha256": artifact["sha256"], "run_id": run_id, "uri": artifact.get("uri")})
    datasets = _dataset_projection(root, paired_receipts)
    if package_review:
        evidence.extend([
            {
                "evidence_id": "p1-four-slot-package",
                "sha256": package_review["package_file_sha256"],
                "run_id": package_review["package_id"],
                "uri": package_review["package_uri"],
            },
            {
                "evidence_id": "p1-rigor-review",
                "sha256": package_review["review_sha256"],
                "run_id": package_review["review_id"],
                "uri": package_review["review_uri"],
            },
        ])
    if _registration_matches_p1_pair(mlflow_registration, p1_pairs, package_review):
        evidence.append({"evidence_id": "mlflow-p1-registration", "sha256": _file_sha256(root / "evidence" / "mlflow-p1-registration.v2.json"), "run_id": str(mlflow_registration.get("parent", {}).get("source_run_id", "p1-parent")), "uri": "evidence/mlflow-p1-registration.v2.json"})
    else:
        mlflow_registration = {}
    readiness = _publication_readiness(root, p1_pairs, decisions, legacy_disposition)
    configured_phases = campaign_config.get("phases", []) if isinstance(campaign_config.get("phases"), list) else []
    phases = []
    tasks = []
    for phase in configured_phases:
        if not isinstance(phase, dict):
            continue
        phase_id = str(phase.get("id", ""))
        phase_status = str(phase.get("status", "planned"))
        phase_preflight_status: str | None = None
        if phase_id == "P1_CPU_BASELINE":
            phase_status = "measured" if p1_pairs else "blocked"
        elif phase_id == "P2_SCOPE_DEVELOPMENT":
            phase_status = "ready" if p2_readiness["status"] == "ready_planned_not_measured" else p2_readiness["status"]
            phase_preflight_status = str(p2_readiness.get("preflight_status", "not_started"))
        phase_row = {"phase_id": phase_id, "status": phase_status, "tasks": []}
        if phase_preflight_status is not None:
            phase_row["preflight_status"] = phase_preflight_status
        for task in phase.get("tasks", []) if isinstance(phase.get("tasks"), list) else []:
            if not isinstance(task, dict):
                continue
            task_row = {"task_id": str(task.get("id", "")), "phase_id": phase_id, "title": str(task.get("title", "")), "status": str(task.get("status", "planned")), "evidence_ids": []}
            if phase_id == "P1_CPU_BASELINE":
                task_row["status"] = "measured" if p1_pairs else "blocked"
                if p1_pairs:
                    task_row["evidence_ids"] = sorted({
                        str(pair["receipt"]["request_id"])
                        for pair in p1_pairs
                    })
            elif phase_id == "P2_SCOPE_DEVELOPMENT":
                task_row["status"] = "ready" if p2_readiness["status"] == "ready_planned_not_measured" else p2_readiness["status"]
                task_row["preflight_status"] = str(p2_readiness.get("preflight_status", "not_started"))
                task_row["evidence_ids"] = [str(item["uri"]) for item in p2_readiness.get("artifacts", [])]
                official_review = p2_readiness.get("official_review", {})
                if official_review.get("status") == "accepted_static_contract_review":
                    task_row["evidence_ids"].append(str(official_review["source"]["index_uri"]))
            phase_row["tasks"].append(task_row)
            tasks.append(task_row)
        phases.append(phase_row)
    source_commit, generated_at = _source_commit_metadata(root)
    p1_state = "P1_CPU_MEASURED_COMPLETE" if p1_pairs else "P1_BLOCKED_WITH_EVIDENCE"
    next_actions = ([
        {"action_id": "review-recovery-freeze", "label": "รอ Owner ตรวจ recovery freeze และหลักฐาน invalidation", "kind": "owner_command"},
        {"action_id": "fresh-owner-local-p1-rerun", "label": "รัน P1 ใหม่แบบ Owner-local เมื่อ Owner สั่งหลัง review", "kind": "owner_command"},
        {"action_id": "hold-before-p2", "label": "ห้ามเริ่ม P2 จนกว่า P1 rerun จะมี receipt, manifests และ validation reports ครบ", "kind": "constraint"},
    ] if not p1_pairs else [
        {"action_id": "review-p1", "label": "ตรวจ P1 evidence package ก่อนพิจารณาคำสั่ง P2 แยกต่างหาก", "kind": "owner_command"},
    ])
    fixture_status = str(
        p2_readiness.get("fixture_pilot", {}).get("status", "not_executed")
        if isinstance(p2_readiness.get("fixture_pilot"), dict)
        else "not_executed"
    )
    if p1_pairs and p2_readiness.get("official_review", {}).get("status") == "accepted_static_contract_review":
        if fixture_status == "passed":
            next_actions = [
                {
                    "action_id": "owner-local-p2-measured-preflight",
                    "label": "Owner-local P2 measured preflight",
                    "kind": "owner_command",
                },
                {
                    "action_id": "hold-before-measured-p2",
                    "label": "Do not start measured P2 or selection exposure automatically; preflight requires the Owner-local protected store",
                    "kind": "constraint",
                },
            ]
        else:
            next_actions = [
                {
                    "action_id": "p2-fixture-pilot",
                    "label": "Run the repository-only P2 fixture pilot before Owner-local measured preflight",
                    "kind": "automatic_next",
                },
                {
                    "action_id": "hold-before-measured-p2",
                    "label": "Do not start measured P2 or selection exposure from the static review verdict",
                    "kind": "constraint",
                },
            ]
    result_state = "valid" if p1_pairs else "blocked"
    p1_latency = paired_receipts[0].get("latency_seconds") if paired_receipts else None
    p2_metric_rows = [
        {"run_id": str(p2_readiness.get("budget_profile_id", "p2-r1-primary")), "phase_id": "P2_SCOPE_DEVELOPMENT", **item}
        for item in p2_readiness.get("metrics", [])
    ]
    body: dict[str, Any] = {
        "schema_version": READ_MODEL_SCHEMA,
        "projection_schema_version": PROJECTION_SCHEMA_VERSION,
        "source_commit": source_commit,
        "generated_at": generated_at,
        "project": {
            "program_id": "myis-research",
            "display_name": "myIS Research",
            "campaign_id": campaign_id,
            "active_campaign_id": armindex["campaign_id"],
            "active_direction": "ArmIndex",
            "active_phase": armindex["current_phase"],
            "current_phase": "P2_SCOPE_DEVELOPMENT" if p1_pairs else "P1_CPU_BASELINE",
            "current_task": "P2.1" if p1_pairs else "P1.3",
            "state": p1_state,
        },
        "projection_health": {
            "status": "blocked" if not p1_pairs else "current",
            "reason": "p1_evidence_matrix_missing" if not p1_pairs else None,
            "shared_revision_required": True,
        },
        "owner_inbox": next_actions[:3],
        "progress": {
            "done": sum(1 for task in tasks if task["status"] in {"complete", "measured"}),
            "in_process": sum(1 for task in tasks if task["status"] in {"in_progress", "executable"}),
            "planned_or_blocked": sum(1 for task in tasks if task["status"] not in {"complete", "measured", "in_progress", "executable"}),
            "total": len(tasks),
        },
        "campaigns": [{
            "campaign_id": campaign_id,
            "authority_status": "historical_read_only",
            "status": campaign_config.get("campaign", {}).get("status", "preparation"),
            "title": campaign_config.get("campaign", {}).get("title", campaign_id),
            "primary_metric": campaign_config.get("protocol", {}).get("primary_metric", "recall_at_100/out"),
            "standing_authorization": "D1_START_CAMPAIGN",
            "active_owner_decisions": ["D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"],
            "current_state": p1_state,
            "p2_status": p2_readiness["status"],
            "p2_preflight_status": p2_readiness.get("preflight_status", "not_started"),
        }, {
            "campaign_id": armindex["campaign_id"],
            "status": armindex["status"],
            "title": "ArmIndex - Retriever-Conditioned Representation Search and Harness Optimization",
            "primary_metric": "recall_at_100/out",
            "standing_authorization": "D1_START_CAMPAIGN",
            "active_owner_decisions": ["D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"],
            "current_state": "A0_MIGRATION_FOUNDATION",
            "authority_status": "active",
        }],
        "armindex": armindex,
        "p2_readiness": p2_readiness,
        "observatory": observatory,
        "phases": phases,
        "tasks": tasks,
        "gates": [
            {"gate_id": "D2_OPEN_FINAL", "status": "approved" if any(item.get("decision_id") == "D2_OPEN_FINAL" and item.get("status") == "approved" for item in decisions) else "waiting_owner"},
            {"gate_id": "D3_SUBMIT_RELEASE", "status": "approved" if any(item.get("decision_id") == "D3_SUBMIT_RELEASE" and item.get("status") == "approved" for item in decisions) else "waiting_owner"},
        ],
        "experiments": sorted(experiments.values(), key=lambda item: item["experiment_id"]),
        "runs": sorted(runs, key=lambda item: item["run_id"]),
        "metrics": metrics + p2_metric_rows,
        "cost": {"currency": "USD", "actual": total_actual if manifests else None, "estimated": total_estimated if manifests else 0.0, "budget": 100.0},
        "decisions": decisions,
        "evidence": evidence,
        "datasets": datasets,
        "historical_exposure": (
            paired_receipts[0].get("historical_exposure", {})
            if paired_receipts
            else ({"active_final_872_global_untouched": "not_claimable"} if legacy_disposition else {})
        ),
        "mlflow_registration": {key: mlflow_registration.get(key) for key in ("schema_version", "package_sha256", "source_receipt_sha256", "dataset_lineage_sha256", "parent", "children") if key in mlflow_registration},
        "publication_readiness": readiness,
        "milestones": [
            {"milestone_id": phase["phase_id"], "status": phase["status"], "depends_on": ([phases[index - 1]["phase_id"]] if index else [])}
            for index, phase in enumerate(phases)
        ],
        "outputs": ([{
            "output_id": "P1-LEGACY-RECEIPT",
            "phase_id": "P1_CPU_BASELINE",
            "task_id": "P1.3",
            "status": legacy_disposition["status"],
            "evidence_class": legacy_disposition["evidence_class"],
            "source_uri": legacy_disposition["source_uri"],
            "source_sha256": legacy_disposition["source_file_sha256"],
            "disposition_uri": LEGACY_DISPOSITION_RELATIVE_PATH.as_posix(),
            "promotable": False,
            "superseded_by": legacy_disposition["superseded_by"],
        }] if legacy_disposition else []),
        "results": [{
            "result_id": "P1-CPU-BASELINE",
            "phase_id": "P1_CPU_BASELINE",
            "task_id": "P1.3",
            "validity": result_state,
            "evidence_maturity": "selection" if p1_pairs else "not_run",
            "metric_ids": [str(item.get("name", "")) for item in metrics] if p1_pairs else [],
            "claim_boundary": "train_selection_only" if p1_pairs else "no_measured_claim",
            "limitations": ["active_final_872_global_untouched_not_claimable"],
            "package_sha256": package_review.get("package_sha256"),
            "package_file_sha256": package_review.get("package_file_sha256"),
            "rigor_review_sha256": package_review.get("review_sha256"),
            "rigor_grade": package_review.get("grade"),
            "rigor_mean_score": package_review.get("mean_score"),
        }, {
            "result_id": "P2-SCOPE-DEVELOPMENT",
            "phase_id": "P2_SCOPE_DEVELOPMENT",
            "task_id": "P2.1",
            "validity": "valid" if p2_readiness["measured"] else "not_measured",
            "evidence_maturity": "measured_selection" if p2_readiness["measured"] else "non_scientific",
            "metric_ids": [str(item.get("name", "")) for item in p2_readiness.get("metrics", [])],
            "claim_boundary": p2_readiness["claim_boundary"],
            "limitations": ["selection_accesses_remain_zero_until_validated_freeze"],
            "budget_profile_id": p2_readiness.get("budget_profile_id"),
            "budget_profile_sha256": p2_readiness.get("budget_profile_sha256"),
            "selection_exposure_count": p2_readiness.get("selection_accesses", 0),
            "preflight_status": p2_readiness.get("preflight_status", "not_started"),
        }],
        "interpretations": ([{
            "interpretation_id": "P1-CPU-BASELINE-INTERPRETATION",
            "result_id": "P1-CPU-BASELINE",
            "status": "pending_review" if p1_pairs else "blocked",
            "statement": "ยังสรุปผลเชิงวิทยาศาสตร์ไม่ได้จนกว่า evidence matrix จะผ่าน",
        }, {
            "interpretation_id": "P2-SCOPE-DEVELOPMENT-INTERPRETATION",
            "result_id": "P2-SCOPE-DEVELOPMENT",
            "status": (
                "pending_measurement"
                if p2_readiness.get("preflight_status") == "not_started"
                else "pending_owner"
                if p2_readiness.get("preflight_status") == "passed_pending_owner"
                else "blocked"
            ),
            "statement": "P2 is contract-ready but has no measured result; fixture readiness does not authorize selection or final evaluation.",
        }]),
        "raid": ([{
            "raid_id": "RISK-P1-EVIDENCE-MATRIX",
            "kind": "risk",
            "status": "open",
            "summary": "P1 receipt ยังไม่มี hash-matched validation reports และ four-slot manifests",
        }] if not p1_pairs else []),
        "resources": {
            "cpu_only": True,
            "gpu": False,
            "paid_api": False,
            "budget_usd": 100.0,
            "actual_cost_usd": total_actual if manifests else 0.0,
            "latency_seconds": (
                float(p1_latency)
                if isinstance(p1_latency, (int, float)) and not isinstance(p1_latency, bool)
                else None
            ),
            "p2_measured_runs": p2_readiness["measured_runs"],
            "p2_selection_accesses": p2_readiness["selection_accesses"],
            "p2_max_wall_clock_seconds": p2_readiness["runtime"].get("max_wall_clock_seconds"),
            "p2_per_candidate_timeout_seconds": p2_readiness["runtime"].get("per_candidate_timeout_seconds"),
        },
        "presentation": {
            "audiences": ["owner", "advisor", "peer"],
            "safe_result_ids": ["P1-CPU-BASELINE", "P2-SCOPE-DEVELOPMENT"],
            "claim_boundary": "no_measured_claim" if not p1_pairs else "train_selection_only",
            "screens": _presentation_screens(
                p1_state=p1_state,
                phases=phases,
                tasks=tasks,
                next_actions=next_actions,
                has_valid_result=bool(p1_pairs),
                has_legacy_output=bool(legacy_disposition),
            ),
        },
        "reports": {
            "vault_id": "myis-obsidian-report",
            "vault_path": "obsidian_report",
            "generated_manifest": "obsidian_report/00_System/Generated/generated-manifest.json",
        },
        "literature": {"registry": "evidence/literature/catalog/corpus_manifest.csv", "proxy_mode": True},
        "advisor_updates": {"draft_path": "obsidian_report/02_Advisor_Updates/Drafts/CURRENT_ADVISOR_UPDATE.md", "presented_immutable": True},
        "tools": {
            "mlflow": {"mode": "read_only_on_demand", "port": 5000},
            "obsidian": {"vault_id": "myis-obsidian-report", "open_via_dashboard": True},
        },
        "archive_contract": {
            "schema_version": "myis.mlflow-archive-contract.v2",
            "active_experiments": ["myis-armindex-multiretriever-v2", "myis-system"],
            "scientific_experiment": "myis-armindex-multiretriever-v2",
            "system_experiment": "myis-system",
            "legacy_policy": "legacy_read_only",
            "historical_experiments": ["myis-scope-autoindex-v1"],
            "writer": "serialized_append_only",
            "viewer": "sqlite_read_only",
            "freeze_required_for_measured_runs": True,
        },
    }
    revision_body = {key: value for key, value in body.items() if key != "generated_at"}
    body["read_model_revision"] = sha256(canonical_json(revision_body))
    body["projection_revision"] = body["read_model_revision"]
    body["read_model_sha256"] = sha256(canonical_json(body))
    return body


def _empty_armindex_projection() -> dict[str, Any]:
    """Return a fail-closed fragment for unit fixtures without ArmIndex control files."""

    phase_ids = (
        "A0_MIGRATION_FOUNDATION",
        "A1_BASELINES_AND_MULTI_ARM_SCREENING",
        "A2_PER_ARM_AUTOINDEX",
        "A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT",
        "A4_PRODUCTION_TRANSFER_AND_SELECTION",
        "A5_FINAL_CONFIRMATION",
        "A6_PUBLICATION_AND_RELEASE",
    )
    return {
        "schema_version": "myis.armindex-read-model.v1",
        "campaign_id": "armindex-multiretriever-v2",
        "status": "control_missing_fail_closed",
        "current_phase": "A0_MIGRATION_FOUNDATION",
        "phases": [{"phase_id": phase_id, "purpose": "control unavailable", "status": "blocked", "tasks": []} for phase_id in phase_ids],
        "arms": [{"arm_id": f"ARM-{index:02d}", "model_id": "unresolved", "role": "unresolved", "license": "unresolved", "commercial_status": "unresolved", "adapter_status": "blocked", "representation_status": "not_started"} for index in range(1, 6)],
        "representation_programs": [],
        "transfer": {"status": "not_started", "matrix_entries": 0},
        "complementarity": {"status": "not_started", "evaluated_arm_sets": 0},
        "harnessopt": {"status": "not_started", "candidate_count": 0, "forbidden_mutations": []},
        "production_profiles": [{"profile_id": profile, "status": "contract_only"} for profile in ("FAST", "BALANCED", "DEEP")],
        "champions": {"research": None, "commercial": None},
        "counters": {"measured_runs": 0, "candidate_count": 0, "selection_accesses": 0, "final_accesses": 0},
        "gates": [{"gate_id": gate, "status": "waiting_owner"} for gate in ("D2_OPEN_FINAL", "D3_SUBMIT_RELEASE")],
        "budget": {"currency": "USD", "actual": 0.0, "hard_stop": 100.0, "migration_profile": "armindex-migration-v2"},
        "historical_campaigns": [{"campaign_id": "scope-autoindex-v1", "status": "historical_read_only", "p1_measured_evidence": "preserved_by_pointer", "p2_measured_runs": 0}],
        "next_command": "Resolve missing ArmIndex control files before any execution.",
    }


def _a010_legacy_code_harvest_projection(root: Path) -> dict[str, Any]:
    """Load only a validated, aggregate-safe A0.10 ledger/receipt pair."""

    missing = {
        "status": "not_started",
        "validated": False,
        "evidence_class": "engineering",
        "scientific_authority": False,
        "claim_boundary": "engineering_provenance_only",
        "ledger_uri": A010_LEGACY_CODE_HARVEST_LEDGER_PATH.as_posix(),
        "ledger_sha256": None,
        "receipt_uri": A010_LEGACY_CODE_HARVEST_RECEIPT_PATH.as_posix(),
        "receipt_sha256": None,
        "fixture_status": "not_started",
        "fixture_receipt_uri": None,
        "fixture_receipt_sha256": None,
        "repository_hygiene_audit_uri": A010_REPOSITORY_HYGIENE_AUDIT_PATH.as_posix(),
        "repository_hygiene_audit_sha256": None,
        "output_root_relocation_receipt_uri": A010_OUTPUT_ROOT_RELOCATION_RECEIPT_PATH.as_posix(),
        "output_root_relocation_receipt_sha256": None,
        "source_verification_receipt_uri": A010_SOURCE_VERIFICATION_RECEIPT_PATH.as_posix(),
        "source_verification_receipt_sha256": None,
        "components_reviewed": 0,
        "components_adopted": 0,
        "components_rejected": 0,
        "measured_runs": 0,
        "selection_accesses": 0,
        "final_accesses": 0,
    }
    ledger_path = root / A010_LEGACY_CODE_HARVEST_LEDGER_PATH
    receipt_path = root / A010_LEGACY_CODE_HARVEST_RECEIPT_PATH
    if not ledger_path.exists() and not receipt_path.exists():
        return missing
    if (
        not ledger_path.is_file()
        or ledger_path.is_symlink()
        or not receipt_path.is_file()
        or receipt_path.is_symlink()
    ):
        return {**missing, "status": "invalid"}
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if not isinstance(ledger, Mapping) or not isinstance(receipt, Mapping):
            raise ValueError("A0.10 ledger and receipt must be objects")
        assert_aggregate_only(ledger)
        assert_aggregate_only(receipt)
        ledger_hash = _file_sha256(ledger_path)
        if str(ledger.get("ledger_sha256", "")) != canonical_sha256(
            {key: value for key, value in ledger.items() if key != "ledger_sha256"}
        ):
            raise ValueError("A0.10 ledger self-hash is invalid")
        if str(receipt.get("receipt_sha256", "")) != canonical_sha256(
            {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        ):
            raise ValueError("A0.10 receipt self-hash is invalid")
        if (
            receipt.get("schema_version") != "myis.armindex-legacy-code-harvest-receipt.v1"
            or ledger.get("schema_version") != "myis.armindex-legacy-code-harvest-ledger.v1"
            or receipt.get("campaign_id") != "armindex-multiretriever-v2"
            or receipt.get("phase_id") != "A0_MIGRATION_FOUNDATION"
            or receipt.get("task_id") != "A0.10"
            or receipt.get("ledger_uri") != A010_LEGACY_CODE_HARVEST_LEDGER_PATH.as_posix()
            or receipt.get("ledger_sha256") != ledger_hash
        ):
            raise ValueError("A0.10 receipt bindings are invalid")
        if receipt.get("scientific_authority") is not False or receipt.get("protected_data_accessed") is not False:
            raise ValueError("A0.10 receipt crosses a protected or scientific boundary")
        if receipt.get("measured_execution_performed") is not False:
            raise ValueError("A0.10 receipt cannot report measured execution")
        if receipt.get("next_authorized_action") != A0_8_NEXT_AUTHORIZED_ACTION:
            raise ValueError("A0.10 next authorized action is not canonical")
        counters = receipt.get("counters")
        if not isinstance(counters, Mapping) or any(
            counters.get(key) != 0
            for key in ("measured_runs", "selection_accesses", "final_accesses")
        ):
            raise ValueError("A0.10 receipt counters must remain zero")
        components = receipt.get("components")
        if not isinstance(components, Mapping):
            raise ValueError("A0.10 receipt component aggregates are missing")
        component_counts = {
            key: int(components.get(key, 0))
            for key in ("reviewed", "adopted", "rejected")
        }
        if any(value < 0 for value in component_counts.values()):
            raise ValueError("A0.10 component aggregate cannot be negative")
        fixture_uri = receipt.get("fixture_receipt_uri")
        fixture_sha = receipt.get("fixture_receipt_sha256")
        if (fixture_uri is None) != (fixture_sha is None):
            raise ValueError("A0.10 fixture receipt binding is incomplete")
        if fixture_uri is not None:
            if not isinstance(fixture_uri, str) or not isinstance(fixture_sha, str):
                raise ValueError("A0.10 fixture receipt binding is invalid")
            fixture_path = (root / fixture_uri).resolve()
            fixture_path.relative_to(root.resolve())
            if fixture_path.is_symlink() or not fixture_path.is_file() or _file_sha256(fixture_path) != fixture_sha:
                raise ValueError("A0.10 fixture receipt commitment is invalid")
        status = str(receipt.get("status", "invalid"))
        if status not in {"not_started", "in_progress", "complete", "blocked"}:
            raise ValueError("A0.10 receipt status is invalid")
        fixture_status = str(receipt.get("fixture_status", "not_started"))
        if fixture_status not in {"not_started", "passed", "failed"}:
            raise ValueError("A0.10 fixture status is invalid")
        if fixture_status == "passed" and fixture_uri is None:
            raise ValueError("passed A0.10 fixture requires a committed receipt")
        supporting_artifacts = (
            (
                "repository_hygiene_audit_uri",
                "repository_hygiene_audit_sha256",
                A010_REPOSITORY_HYGIENE_AUDIT_PATH,
                "myis.repository-hygiene-audit.v1",
                "audit_sha256",
            ),
            (
                "output_root_relocation_receipt_uri",
                "output_root_relocation_receipt_sha256",
                A010_OUTPUT_ROOT_RELOCATION_RECEIPT_PATH,
                "myis.output-root-relocation.v1",
                "receipt_sha256",
            ),
            (
                "source_verification_receipt_uri",
                "source_verification_receipt_sha256",
                A010_SOURCE_VERIFICATION_RECEIPT_PATH,
                "myis.source-verification-receipt.v1",
                "receipt_sha256",
            ),
        )
        loaded_supporting: dict[Path, Mapping[str, Any]] = {}
        for uri_key, sha_key, expected_path, schema_version, self_hash_key in supporting_artifacts:
            uri = receipt.get(uri_key)
            digest = receipt.get(sha_key)
            if uri != expected_path.as_posix() or not isinstance(digest, str):
                raise ValueError(f"A0.10 supporting artifact binding is invalid: {uri_key}")
            artifact_path = (root / expected_path).resolve()
            artifact_path.relative_to(root.resolve())
            if artifact_path.is_symlink() or not artifact_path.is_file() or _file_sha256(artifact_path) != digest:
                raise ValueError(f"A0.10 supporting artifact commitment is invalid: {uri_key}")
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            if (
                not isinstance(artifact, Mapping)
                or artifact.get("schema_version") != schema_version
                or artifact.get("status") != "PASS"
                or artifact.get("scientific_authority") is not False
                or artifact.get(self_hash_key) != canonical_sha256(
                    {key: value for key, value in artifact.items() if key != self_hash_key}
                )
            ):
                raise ValueError(f"A0.10 supporting artifact content is invalid: {uri_key}")
            assert_aggregate_only(artifact)
            loaded_supporting[expected_path] = artifact

        source_verification = loaded_supporting[A010_SOURCE_VERIFICATION_RECEIPT_PATH]
        repositories = ledger.get("source_repositories")
        components = ledger.get("components")
        if not isinstance(repositories, list) or not isinstance(components, list):
            raise ValueError("A0.10 ledger source provenance is incomplete")
        thaipha_repository = next(
            (item for item in repositories if isinstance(item, Mapping) and item.get("repository") == "ThaiPha-Lex"),
            None,
        )
        thaipha_components = {
            str(item.get("component_id")): item
            for item in components
            if isinstance(item, Mapping) and item.get("source_repository") == "ThaiPha-Lex"
        }
        verified_components = source_verification.get("components")
        if (
            not isinstance(thaipha_repository, Mapping)
            or source_verification.get("source_commit") != thaipha_repository.get("commit")
            or source_verification.get("source_tree") != thaipha_repository.get("tree")
            or source_verification.get("source_remote") != thaipha_repository.get("remote")
            or source_verification.get("verified_from_git_object_database") is not True
            or not isinstance(verified_components, list)
            or source_verification.get("verified_component_count") != len(thaipha_components)
        ):
            raise ValueError("A0.10 source verification receipt identity is invalid")
        verified_by_id = {
            str(item.get("component_id")): item
            for item in verified_components
            if isinstance(item, Mapping)
        }
        if set(verified_by_id) != set(thaipha_components):
            raise ValueError("A0.10 source verification coverage is incomplete")
        for component_id, source in thaipha_components.items():
            verified = verified_by_id[component_id]
            if (
                verified.get("source_path") != source.get("source_path")
                or verified.get("source_sha256") != source.get("source_sha256")
                or verified.get("disposition") != source.get("disposition")
                or not re.fullmatch(r"[a-f0-9]{40}", str(verified.get("git_blob", "")))
            ):
                raise ValueError("A0.10 source verification component binding is invalid")
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        return {**missing, "status": "invalid"}
    return {
        **missing,
        "status": status,
        "validated": True,
        "ledger_sha256": ledger_hash,
        "receipt_sha256": str(receipt["receipt_sha256"]),
        "fixture_status": fixture_status,
        "fixture_receipt_uri": fixture_uri,
        "fixture_receipt_sha256": fixture_sha,
        "repository_hygiene_audit_sha256": str(receipt["repository_hygiene_audit_sha256"]),
        "output_root_relocation_receipt_sha256": str(receipt["output_root_relocation_receipt_sha256"]),
        "source_verification_receipt_sha256": str(receipt["source_verification_receipt_sha256"]),
        "components_reviewed": component_counts["reviewed"],
        "components_adopted": component_counts["adopted"],
        "components_rejected": component_counts["rejected"],
        "measured_runs": int(counters["measured_runs"]),
        "selection_accesses": int(counters["selection_accesses"]),
        "final_accesses": int(counters["final_accesses"]),
    }


def _presentation_screens(
    *,
    p1_state: str,
    phases: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    next_actions: list[dict[str, str]],
    has_valid_result: bool,
    has_legacy_output: bool,
) -> list[dict[str, Any]]:
    """Build the reviewed, presentation-safe ten-screen story from canonical state."""

    audiences = ["owner", "advisor", "peer"]
    complete_tasks = sum(task.get("status") in {"complete", "measured"} for task in tasks)
    phase_summary = ", ".join(
        f"{str(phase.get('phase_id', '')).split('_', 1)[0]}: {phase.get('status', 'planned')}"
        for phase in phases
    )
    next_label = str(next_actions[0]["label"]) if next_actions else "ไม่มีคำสั่งจาก Owner ที่ค้างอยู่"
    latest_result = (
        "มีผล P1 ที่ผ่าน evidence matrix สำหรับ train/selection; final ยังปิดตาม protocol"
        if has_valid_result
        else "ยังไม่มีผล P1 ที่ผ่าน validation; สถานะที่รายงานได้คือ blocked with evidence"
    )
    delivered = (
        f"Task ที่เสร็จพร้อมหลักฐาน {complete_tasks}/{len(tasks)}; เก็บ legacy receipt ไว้เป็น historical-invalid output"
        if has_legacy_output
        else f"Task ที่เสร็จพร้อมหลักฐาน {complete_tasks}/{len(tasks)}; ยังไม่มี measured output ที่ promote ได้"
    )
    rows = [
        (
            "thesis",
            "myIS Research: SCOPE / AutoIndex",
            "คำถามหลักคือ representation ที่ยึดหลักฐานจะช่วย family-level patent retrieval ได้หรือไม่ เมื่อ retriever, evaluator และ budget คงที่",
        ),
        (
            "difficulty",
            "เหตุใดการค้น prior art จึงยาก",
            "สิทธิบัตรยาว ใช้ถ้อยคำหลากหลาย และหลักฐานอาจอยู่คนละส่วนของเอกสาร การประเมินจึงต้องแยก retrieval evidence ออกจากข้อสรุปทางกฎหมาย",
        ),
        (
            "boundary",
            "ขอบเขตข้อมูลและการประเมิน",
            "งานปัจจุบันเป็น CPU-only และ aggregate-only; ข้อมูล protected และ final confirmation ยังอยู่ใน Owner-local boundary",
        ),
        (
            "history",
            "เส้นทาง A → B → D → SCOPE",
            "บทเรียนจากงานเดิมชี้ให้ตรวจ candidate exposure และ headroom ก่อนเพิ่มความซับซ้อน ผลเดิมถูกเก็บเป็น historical/exposed และไม่ปะปนกับผลปัจจุบัน",
        ),
        (
            "architecture",
            "ระบบหลักฐานหนึ่งชุด หลายมุมมอง",
            "Control files และ immutable receipts สร้าง shared read model หนึ่งครั้ง แล้ว fan out ไป Dashboard, MLflow และ Obsidian ด้วย revision เดียวกัน",
        ),
        (
            "plan",
            "แผน P0–P4",
            phase_summary,
        ),
        (
            "delivered",
            "สิ่งที่ส่งมอบแล้ว",
            delivered,
        ),
        (
            "result",
            "ผลที่ตรวจสอบแล้วล่าสุด",
            latest_result,
        ),
        (
            "interpretation",
            "การแปลผลและข้อจำกัด",
            "หลักฐานปัจจุบันรองรับเฉพาะสถานะ recovery ของ P1 ยังไม่รองรับ measured claim, P2, final confirmation หรือ publication claim",
        ),
        (
            "next",
            "สถานะและการตัดสินใจถัดไป",
            f"{p1_state}. ขั้นถัดไป: {next_label}. D2 และ D3 ยังคงเป็น Owner-only decisions",
        ),
    ]
    return [
        {
            "screen_id": f"shared-{index:02d}-{screen_id}",
            "audience": audiences,
            "order": index,
            "title_th": title,
            "message_th": message,
            "visual_artifact_id": None,
            "evidence_ids": [],
            "safe_to_present": True,
        }
        for index, (screen_id, title, message) in enumerate(rows, start=1)
    ]


def write_read_model(repository_root: Path, output: Path | None = None) -> Path:
    root = repository_root.resolve()
    target = output or root / "projections" / "read-model" / "read-model.v2.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(build_read_model(root), ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def _p2_official_review_projection(root: Path) -> dict[str, Any]:
    """Validate and summarize the repository-safe three-round P2 static review."""

    audit_root = root / P2_OFFICIAL_REVIEW_ROOT
    missing = {
        "status": "not_recorded",
        "evidence_class": "static_contract_review",
        "claim_boundary": "engineering_provenance_only",
        "round_count": 0,
        "final_round": None,
        "final_verdict": None,
        "reviewed_commit": None,
        "fixture_pilot_contract_status": "not_reviewed",
        "fixture_pilot_executed": False,
        "protected_data_accessed": False,
        "measured_execution_performed": False,
        "rounds": [],
        "source": None,
    }
    if not audit_root.is_dir():
        return missing

    try:
        resolved_root = audit_root.resolve()

        def resolve_file(value: str) -> Path:
            relative = Path(value)
            if not value.strip() or relative.is_absolute() or ".." in relative.parts:
                raise ValueError("audit reference must be repository-relative")
            unresolved = audit_root / relative
            target = unresolved.resolve()
            target.relative_to(resolved_root)
            if unresolved.is_symlink() or not target.is_file():
                raise ValueError("audit reference must resolve to a regular file")
            return target

        checksums_path = resolve_file("SHA256SUMS.txt")
        checksums: dict[str, str] = {}
        json_payloads: dict[str, dict[str, Any]] = {}
        for raw_line in checksums_path.read_text(encoding="utf-8").splitlines():
            digest, separator, relative = raw_line.partition("  ")
            if separator != "  " or len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
                raise ValueError("invalid audit checksum line")
            path = resolve_file(relative)
            if _file_sha256(path) != digest or relative in checksums:
                raise ValueError("audit checksum mismatch")
            checksums[relative] = digest
            if path.suffix == ".json":
                payload = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("audit JSON must be an object")
                assert_aggregate_only(payload)
                json_payloads[relative] = payload

        index = json_payloads.get("index.json")
        if not index or index.get("schema_version") != "myis.official-review-index.v1":
            raise ValueError("official review index is missing or invalid")
        if index.get("phase") != "P2_SCOPE_DEVELOPMENT" or index.get("status_at_close") != "ready_planned_not_measured":
            raise ValueError("official review boundary is invalid")
        runtime = index.get("review_runtime")
        expected_runtime = {
            "provider": "openai",
            "model": "gpt-5.6-sol",
            "codex_cli_version": "0.146.0",
            "sandbox": "read-only",
            "protected_data_accessed": False,
            "measured_execution_performed": False,
        }
        if not isinstance(runtime, dict) or any(runtime.get(field) != value for field, value in expected_runtime.items()):
            raise ValueError("official review runtime provenance is invalid")
        raw_rounds = index.get("rounds")
        if not isinstance(raw_rounds, list) or [item.get("round") for item in raw_rounds if isinstance(item, dict)] != [1, 2, 3]:
            raise ValueError("official review rounds must be exactly 1, 2, and 3")

        rounds: list[dict[str, Any]] = []
        for item in raw_rounds:
            if not isinstance(item, dict):
                raise ValueError("official review round must be an object")
            round_number = int(item["round"])
            metadata_relative = str(item["metadata"])
            result_relative = str(item["result"])
            prompt_relative = str(item["prompt"])
            if any(relative not in checksums for relative in (metadata_relative, result_relative, prompt_relative)):
                raise ValueError("official review reference is absent from checksum manifest")
            metadata = json_payloads.get(metadata_relative)
            result = json_payloads.get(result_relative)
            if not metadata or not result:
                raise ValueError("official review metadata or result is missing")
            if metadata.get("schema_version") != "myis.official-review-metadata.v1" or result.get("schema_version") != "1.0":
                raise ValueError("official review schema mismatch")
            for field in ("round", "task_id", "verdict"):
                if metadata.get(field) != item.get(field) or result.get(field) != item.get(field):
                    raise ValueError("official review round identity mismatch")
            if metadata.get("reviewed_commit") != item.get("reviewed_commit"):
                raise ValueError("official review commit mismatch")
            reviewed_commit = str(item["reviewed_commit"])
            if len(reviewed_commit) != 40 or any(character not in "0123456789abcdef" for character in reviewed_commit):
                raise ValueError("official review commit must be a Git SHA-1")
            if metadata.get("prompt_sha256") != checksums[prompt_relative] or metadata.get("result_sha256") != checksums[result_relative]:
                raise ValueError("official review metadata hash mismatch")
            if metadata.get("protected_data_accessed") is not False or result.get("protected_data_accessed") is not False:
                raise ValueError("official review crossed the protected-data boundary")
            if metadata.get("measured_execution_performed") is not False or result.get("measured_execution_performed") is not False:
                raise ValueError("official review performed measured execution")
            rounds.append({
                "round": round_number,
                "task_id": str(item["task_id"]),
                "verdict": str(item["verdict"]),
                "reviewed_commit": reviewed_commit,
                "invoked_at_utc": str(metadata.get("invoked_at_utc", "")),
                "provider": str(metadata.get("provider", "")),
                "model": str(metadata.get("model", "")),
                "codex_cli_version": str(metadata.get("codex_cli_version", "")),
                "sandbox": str(metadata.get("sandbox", "")),
                "approval": str(metadata.get("approval", "")),
                "source_provenance": str(metadata.get("source_provenance", "")),
                "result_uri": f"{P2_OFFICIAL_REVIEW_ROOT.as_posix()}/{result_relative}",
                "result_sha256": checksums[result_relative],
            })

        boundary = index.get("final_boundary")
        if not isinstance(boundary, dict):
            raise ValueError("official review final boundary is missing")
        expected_boundary = {
            "fixture_pilot_executed": False,
            "measured_runs": 0,
            "candidate_count": 0,
            "selection_accesses": 0,
            "protected_data_accessed": False,
            "measured_execution_performed": False,
        }
        if any(boundary.get(field) != value for field, value in expected_boundary.items()):
            raise ValueError("official review final boundary changed")
        final_round = rounds[-1]
        final_result = json_payloads[str(raw_rounds[-1]["result"])]
        if final_round["verdict"] == "accept" and (
            final_result.get("required_changes") != [] or final_result.get("major_risks") != []
        ):
            raise ValueError("accepted official review still contains blocking findings")

        return {
            "status": "accepted_static_contract_review" if final_round["verdict"] == "accept" else "revision_required",
            "audit_id": str(index.get("audit_id", "")),
            "evidence_class": "static_contract_review",
            "claim_boundary": "engineering_provenance_only",
            "round_count": len(rounds),
            "final_round": final_round["round"],
            "final_verdict": final_round["verdict"],
            "reviewed_commit": final_round["reviewed_commit"],
            "fixture_pilot_contract_status": (
                "static_review_accepted_not_executed"
                if final_round["verdict"] == "accept"
                else "static_review_requires_revision"
            ),
            "fixture_pilot_executed": False,
            "protected_data_accessed": False,
            "measured_execution_performed": False,
            "rounds": rounds,
            "source": {
                "index_uri": f"{P2_OFFICIAL_REVIEW_ROOT.as_posix()}/index.json",
                "index_sha256": checksums["index.json"],
                "checksums_uri": f"{P2_OFFICIAL_REVIEW_ROOT.as_posix()}/SHA256SUMS.txt",
                "checksums_sha256": _file_sha256(checksums_path),
            },
        }
    except (KeyError, OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        return {
            **missing,
            "status": "invalid_audit_bundle",
            "fixture_pilot_contract_status": "blocked_invalid_audit",
        }


def _p2_readiness_projection(root: Path, campaign_config: dict[str, Any]) -> dict[str, Any]:
    """Read only validated P2 control/artifact metadata.

    A missing P2 package is a normal readiness state.  Invalid or incomplete
    P2 JSON is never promoted into the shared read model; only a schema-valid,
    self-hash-valid artifact contributes a pointer, count, or freeze state.
    """

    official_review = _p2_official_review_projection(root)
    fixture_pilot = _p2_fixture_projection(root)
    preflight = _p2_preflight_projection(root)
    candidate_proposal = _p2_candidate_proposal_projection(root)
    active_sources = _active_p2_sources(root)
    profile_path = root / active_sources["profile"]
    profile: dict[str, Any] = {}
    profile_sha256: str | None = None
    try:
        loaded = _load_yaml_like(profile_path)
        if isinstance(loaded, dict) and loaded.get("schema_version") == "myis.p2-budget-profile.v1":
            profile = loaded
            profile_sha256 = canonical_sha256(profile)
    except (OSError, ValueError, TypeError):
        profile = {}

    configured = campaign_config.get("p2_execution", {})
    if not isinstance(configured, dict):
        configured = {}
    limits = profile.get("limits") if isinstance(profile.get("limits"), dict) else configured.get("candidate_allocation", {})
    runtime = profile.get("runtime") if isinstance(profile.get("runtime"), dict) else configured.get("runtime", {})
    allocation = profile.get("candidate_allocation") if isinstance(profile.get("candidate_allocation"), dict) else configured.get("candidate_allocation", {})
    stopping = profile.get("stopping") if isinstance(profile.get("stopping"), dict) else configured.get("stopping", {})
    resources = profile.get("resources") if isinstance(profile.get("resources"), dict) else {}

    campaign_root = root / "campaigns/scope-autoindex-v1"
    valid: list[tuple[Path, dict[str, Any]]] = []
    invalid_count = 1 if candidate_proposal["status"] == "invalid" else 0
    seen: set[Path] = set()
    for directory_name in P2_ARTIFACT_DIRS:
        directory = campaign_root / directory_name
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.json")):
            if path in seen or not any(token in path.stem.lower() for token in ("p2-", "p2_", ".p2")):
                continue
            seen.add(path)
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                payload = json.loads(path.read_text(encoding="utf-8"))
                validated = validate_p2_artifact(payload, repository_root=root)
            except (OSError, UnicodeError, json.JSONDecodeError, P2ContractError, TypeError, ValueError):
                invalid_count += 1
                continue
            artifact_revision = validated.get("campaign_revision")
            if artifact_revision not in {None, profile.get("campaign_revision")}:
                continue
            if profile_sha256 and validated.get("budget_profile_sha256") not in {None, profile_sha256}:
                invalid_count += 1
                continue
            valid.append((path, validated))

    by_schema: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    for path, payload in valid:
        by_schema.setdefault(str(payload.get("schema_version")), []).append((path, payload))

    def latest(schema_version: str) -> tuple[Path, dict[str, Any]] | None:
        values = by_schema.get(schema_version, [])
        return values[-1] if values else None

    package = latest("myis.p2-package.v1")
    valid_by_uri = {path.relative_to(root).as_posix(): payload for path, payload in valid}
    bundle: dict[str, dict[str, Any]] | None = None
    if package is not None:
        package_payload = package[1]

        def referenced(field: str) -> dict[str, Any] | None:
            value = package_payload.get(field)
            if value is None:
                return None
            if not isinstance(value, str) or value not in valid_by_uri:
                raise P2ContractError(f"package {field} does not reference a validated P2 artifact")
            return valid_by_uri[value]

        try:
            request_payload = referenced("request_uri")
            ledger_payload = referenced("candidate_ledger_uri")
            commitment_payload = referenced("baseline_commitment_uri")
            baseline_payload = referenced("baseline_reproduction_uri")
            freeze_payload = referenced("shortlist_freeze_uri")
            manifest_payload = referenced("manifest_uri")
            if any(item is None for item in (request_payload, ledger_payload, commitment_payload, baseline_payload, freeze_payload, manifest_payload)):
                raise P2ContractError("complete P2 package is missing a required artifact reference")
            bundle = validate_p2_package_bundle(
                request=request_payload,
                ledger=ledger_payload,
                commitment=commitment_payload,
                baseline=baseline_payload,
                freeze=freeze_payload,
                selection=referenced("selection_uri"),
                manifest=manifest_payload,
                package=package_payload,
                repository_root=root,
            )
        except (P2ContractError, TypeError, ValueError):
            invalid_count += 1
            bundle = None

    ledger = bundle.get("ledger") if bundle else None
    commitment = bundle.get("commitment") if bundle else None
    baseline = bundle.get("baseline") if bundle else None
    freeze = bundle.get("freeze") if bundle else None
    selection = bundle.get("selection") if bundle else None
    manifest = bundle.get("manifest") if bundle else None
    measured_manifest = (
        manifest is not None
        and manifest.get("evidence_class") == "train_selection_measured"
        and manifest.get("status") in {"valid", "negative_development"}
    )
    freeze_valid = (
        bool(measured_manifest)
        and freeze is not None
        and freeze.get("status") == "validated_immutable"
        and freeze.get("selection_exposure_count") == 0
    )
    selection_count = (
        1
        if measured_manifest
        and selection is not None
        and selection.get("selection_exposure_count") == 1
        else 0
    )
    if invalid_count or fixture_pilot["status"] == "invalid":
        status = "blocked_invalid_artifact"
    elif measured_manifest:
        status = "measured"
    else:
        status = "ready_planned_not_measured"

    pointers: list[dict[str, Any]] = []
    if candidate_proposal["validated"]:
        pointers.append({
            "schema_version": "myis.p2-candidate-freeze-proposal.v1",
            "uri": candidate_proposal["proposal_uri"],
            "sha256": candidate_proposal["proposal_sha256"],
        })
    for path, payload in valid:
        self_hash_field = {
            "myis.p2-candidate-ledger.v1": "ledger_sha256",
            "myis.p2-baseline-commitment.v1": "commitment_sha256",
            "myis.p2-baseline-reproduction-receipt.v1": "receipt_sha256",
            "myis.p2-shortlist-freeze-receipt.v1": "receipt_sha256",
            "myis.p2-selection-receipt.v1": "receipt_sha256",
            "myis.p2-manifest.v1": "manifest_sha256",
            "myis.p2-package.v1": "package_sha256",
        }.get(str(payload.get("schema_version")))
        pointers.append({
            "schema_version": payload.get("schema_version"),
            "uri": path.relative_to(root).as_posix(),
            "sha256": str(payload.get(self_hash_field)) if self_hash_field else _file_sha256(path),
        })

    p2_metrics: list[dict[str, Any]] = []
    if measured_manifest:
        raw_metrics = manifest.get("metrics", [])
        if isinstance(raw_metrics, list):
            for item in raw_metrics:
                if isinstance(item, dict) and set(item).issubset(P2_METRIC_FIELDS) and {"name", "value"} <= set(item):
                    p2_metrics.append(dict(item))

    review_source = official_review.get("source") if isinstance(official_review.get("source"), dict) else {}

    return {
        "status": status,
        "preflight_status": preflight["status"],
        "preflight": preflight,
        "candidate_proposal": candidate_proposal,
        "phase_id": "P2_SCOPE_DEVELOPMENT",
        "arm": "R1",
        "campaign_revision": profile.get("campaign_revision") or configured.get("campaign_revision"),
        "budget_profile_id": profile.get("profile_id") or configured.get("profile_id"),
        "budget_profile_sha256": profile_sha256,
        "measured": bool(measured_manifest),
        "measured_runs": 1 if measured_manifest else 0,
        "selection_accesses": selection_count,
        "candidate_count": int(ledger.get("candidate_count", 0)) if measured_manifest and ledger else 0,
        "shortlist_count": len(freeze.get("candidate_ids", [])) if measured_manifest and freeze else 0,
        "candidate_budget": {
            "max_candidates_total": limits.get("max_candidates_total"),
            "max_adaptive_candidates": limits.get("max_adaptive_candidates"),
            "max_adaptive_iterations": limits.get("max_adaptive_iterations"),
            "candidates_per_iteration": limits.get("candidates_per_iteration"),
            "max_index_builds": limits.get("max_index_builds"),
            "max_selection_finalists": limits.get("max_selection_finalists"),
            "selection_exposure_limit": limits.get("selection_exposure_limit"),
            "frozen_controls": allocation.get("frozen_controls"),
            "preregistered_patent_candidates": allocation.get("preregistered_patent_candidates"),
        },
        "runtime": {
            "max_wall_clock_seconds": runtime.get("max_wall_clock_seconds"),
            "measurement_budget_seconds": runtime.get("measurement_budget_seconds"),
            "overhead_reserve_seconds": runtime.get("overhead_reserve_seconds"),
            "per_candidate_timeout_seconds": runtime.get("per_candidate_timeout_seconds"),
            "prevent_system_sleep": runtime.get("prevent_system_sleep", False),
        },
        "stopping": {
            "min_iterations_before_early_stop": stopping.get("min_iterations_before_early_stop"),
            "no_improvement_patience": stopping.get("no_improvement_patience"),
            "selection_rule": stopping.get("selection_rule", "strictly_greater_reject_ties"),
            "whole_batch_admission": stopping.get("whole_batch_admission", False),
            "valid_reasons": stopping.get("valid_reasons", []),
        },
        "resources": {
            "paid_api_budget_usd": resources.get("paid_api_budget_usd", 0),
            "gpu_budget_usd": resources.get("gpu_budget_usd", 0),
            "network_model_download": resources.get("network_model_download", False),
            "provider_fallback": resources.get("provider_fallback", False),
            "proposer_mode": resources.get("proposer_mode", "disabled"),
        },
        "freeze_barrier": {
            "required": True,
            "status": "validated_immutable" if freeze_valid else "not_started" if freeze is None else "blocked",
            "candidate_ids_frozen": bool(freeze_valid),
            "selection_exposure_limit": limits.get("selection_exposure_limit", 1),
            "selection_exposure_count": selection_count,
            "mutation_after_selection": "forbidden",
        },
        "metrics": p2_metrics,
        "artifacts": pointers,
        "invalid_artifact_count": invalid_count,
        "claim_boundary": "no_measured_claim" if not measured_manifest else "train_selection_development_only",
        "source": {
            "profile": active_sources["profile"],
            "execution_envelope": active_sources["execution_envelope"],
            "campaign_revision": active_sources.get("campaign_revision"),
            "baseline_commitment_sha256": commitment.get("commitment_sha256") if commitment else None,
            "baseline_reproduction_receipt_sha256": baseline.get("receipt_sha256") if baseline else None,
            "official_review_index_sha256": review_source.get("index_sha256"),
            "fixture_receipt_sha256": fixture_pilot.get("receipt_sha256"),
            "fixture_manifest_sha256": fixture_pilot.get("execution_manifest_sha256"),
            "fixture_package_sha256": fixture_pilot.get("fixture_package_sha256"),
        },
        "official_review": official_review,
        "fixture_pilot": fixture_pilot,
    }


def _active_p2_sources(root: Path) -> dict[str, str]:
    legacy = {
        "profile": "control/budgets/p2-r1-primary-v1.yaml",
        "execution_envelope": "control/execution-envelope-p2.yaml",
    }
    source_path = root / "control/source-of-truth.yaml"
    if not source_path.is_file() or source_path.is_symlink():
        return legacy
    source = _load_yaml_like(source_path)
    records = source.get("records", []) if isinstance(source, dict) else []
    by_id = {
        str(item.get("id")): item
        for item in records
        if isinstance(item, dict) and item.get("id")
    }
    profile = by_id.get("p2_budget_profile", {}).get("authority")
    execution = by_id.get("execution_boundary", {}).get("phase_mapping", {}).get(
        "P2_SCOPE_DEVELOPMENT"
    )
    revision = by_id.get("p2_campaign_revision", {}).get("authority")
    if (
        "p2_budget_profile" not in by_id
        and "p2_campaign_revision" not in by_id
        and execution is None
    ):
        return legacy
    values = {
        "profile": profile,
        "execution_envelope": execution,
        "campaign_revision": revision,
    }
    for label, uri in values.items():
        if uri is None and label == "campaign_revision":
            continue
        if not isinstance(uri, str) or not uri or Path(uri).is_absolute() or ".." in Path(uri).parts:
            raise ValueError(f"active P2 {label} source is not repository-relative")
        path = root / uri
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"active P2 {label} source is missing or unsafe")
    return {key: str(value) for key, value in values.items() if value is not None}


def _p2_candidate_proposal_projection(root: Path) -> dict[str, Any]:
    """Project an Owner-review draft without promoting it into the measured ledger."""

    missing = {
        "status": "not_created",
        "adoption": "not_adopted",
        "proposal_uri": P2_CANDIDATE_PROPOSAL_PATH.as_posix(),
        "proposal_sha256": None,
        "validated": False,
        "frozen_controls": 0,
        "preregistered_candidates": 0,
        "registered_candidates": 0,
        "hash_locked_candidates": 0,
        "scientific_authority": False,
    }
    path = root / P2_CANDIDATE_PROPOSAL_PATH
    if not path.exists():
        return missing
    if path.is_symlink() or not path.is_file():
        return {**missing, "status": "invalid"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        active = _active_p2_sources(root)
        active_profile = _load_yaml_like(root / active["profile"])
        historical = payload.get("campaign_revision") != active_profile.get("campaign_revision")
        if historical:
            recorded_hash = str(payload.get("proposal_sha256", ""))
            unsigned = {key: value for key, value in payload.items() if key != "proposal_sha256"}
            assert_aggregate_only(payload)
            if recorded_hash != canonical_sha256(unsigned):
                raise P2ContractError("historical candidate proposal self-hash is invalid")
            proposal = payload
        else:
            proposal = validate_p2_candidate_freeze_proposal(payload, repository_root=root)
    except (OSError, UnicodeError, json.JSONDecodeError, P2ContractError, TypeError, ValueError):
        return {**missing, "status": "invalid"}
    controls = proposal.get("frozen_controls", [])
    candidates = proposal.get("preregistered_candidates", [])
    rows = [item for item in [*controls, *candidates] if isinstance(item, Mapping)]
    return {
        "status": str(proposal.get("status", "invalid")),
        "adoption": str(proposal.get("adoption", "not_adopted")),
        "proposal_uri": P2_CANDIDATE_PROPOSAL_PATH.as_posix(),
        "proposal_sha256": str(proposal.get("proposal_sha256")),
        "validated": True,
        "historical_superseded": historical,
        "frozen_controls": len(controls),
        "preregistered_candidates": len(candidates),
        "registered_candidates": sum(1 for item in rows if item.get("registered") is True),
        "hash_locked_candidates": sum(1 for item in rows if item.get("hash_locked") is True),
        "scientific_authority": False,
    }


def _p2_preflight_projection(root: Path) -> dict[str, Any]:
    """Project only the validated preflight state; never infer readiness from a preview."""

    missing = {
        "status": "not_started",
        "receipt_uri": P2_PREFLIGHT_RECEIPT_PATH.as_posix(),
        "receipt_sha256": None,
        "validated": False,
        "checks_passed": 0,
        "checks_failed": 0,
        "failure_codes": [],
        "measured_runs": 0,
        "candidate_count": 0,
        "shortlist_count": 0,
        "selection_accesses": 0,
        "safe_to_measure": False,
        "owner_approval_required": [
            "Owner confirms both protected store identities and permits read-only metadata preflight.",
            "Owner approves the four frozen controls and eight preregistered candidate definitions.",
            "Owner resolves any ambiguous SCOPE view, field, normalization, or aggregation definition before adoption.",
            "Owner approves the concrete compiler, config, retriever, and evaluator SHA-256 bindings before a measured request.",
            "Owner explicitly requests measured P2; this preflight does not create a request, baseline commitment, or selection exposure.",
        ],
    }
    path = root / P2_PREFLIGHT_RECEIPT_PATH
    if not path.exists():
        return missing
    if path.is_symlink() or not path.is_file():
        return {**missing, "status": "failed"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        receipt = validate_p2_preflight_receipt(payload, repository_root=root)
    except (OSError, UnicodeError, json.JSONDecodeError, P2ContractError, TypeError, ValueError):
        return {**missing, "status": "failed"}
    checks = receipt.get("checks", [])
    counters = receipt.get("counters", {})
    status = str(receipt.get("status", "failed"))
    if status not in {"not_started", "passed_pending_owner", "failed"}:
        status = "failed"
    safe_to_measure = status == "passed_pending_owner" and all(
        item.get("status") == "passed" for item in checks if isinstance(item, Mapping)
    )
    return {
        "status": status,
        "receipt_uri": P2_PREFLIGHT_RECEIPT_PATH.as_posix(),
        "receipt_sha256": str(receipt.get("receipt_sha256")),
        "validated": True,
        "checks_passed": sum(1 for item in checks if isinstance(item, Mapping) and item.get("status") == "passed"),
        "checks_failed": sum(1 for item in checks if isinstance(item, Mapping) and item.get("status") == "failed"),
        "failure_codes": [str(item) for item in receipt.get("failure_codes", [])],
        "measured_runs": int(counters.get("measured_runs", 0)),
        "candidate_count": int(counters.get("candidate_count", 0)),
        "shortlist_count": int(counters.get("shortlist_count", 0)),
        "selection_accesses": int(counters.get("selection_accesses", 0)),
        "safe_to_measure": safe_to_measure,
        "owner_approval_required": [str(item) for item in receipt.get("owner_approval_required", [])],
    }


def _p2_fixture_projection(root: Path) -> dict[str, Any]:
    """Project only validated aggregate fixture provenance, never synthetic ledgers."""

    missing = {
        "executed": False,
        "status": "not_executed",
        "evidence_class": "fixture",
        "scientific_authority": False,
        "claim_boundary": "no_measured_claim",
        "protected_data_accessed": False,
        "measured_execution_performed": False,
        "synthetic_candidates": 0,
        "synthetic_iterations": 0,
        "synthetic_shortlist": 0,
        "fixture_selection_exposures": 0,
        "receipt_uri": None,
        "receipt_sha256": None,
        "execution_manifest_uri": None,
        "execution_manifest_sha256": None,
        "fixture_package_sha256": None,
        "deterministic_rerun": "not_run",
        "canonical_hashes_match": False,
        "negative_checks_passed": False,
        "negative_check_count": 0,
    }
    receipt_path = root / P2_FIXTURE_RECEIPT_PATH
    manifest_path = root / P2_FIXTURE_MANIFEST_PATH
    if not receipt_path.exists() and not manifest_path.exists():
        return missing
    if not receipt_path.is_file() or receipt_path.is_symlink() or not manifest_path.is_file() or manifest_path.is_symlink():
        return {**missing, "status": "invalid"}
    try:
        receipt_payload = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt = validate_fixture_receipt(receipt_payload, repository_root=root)
        manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest = validate_fixture_execution_manifest(manifest_payload, receipt=receipt)
        assert_aggregate_only(receipt)
        assert_aggregate_only(manifest)
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        P2FixtureError,
        TypeError,
        ValueError,
    ):
        return {**missing, "status": "invalid"}
    return {
        "executed": True,
        "status": "passed",
        "evidence_class": "fixture",
        "scientific_authority": False,
        "claim_boundary": "no_measured_claim",
        "protected_data_accessed": False,
        "measured_execution_performed": False,
        "synthetic_candidates": int(receipt["synthetic_candidates"]),
        "synthetic_iterations": int(receipt["synthetic_adaptive_iterations"]),
        "synthetic_shortlist": int(receipt["synthetic_shortlist_count"]),
        "fixture_selection_exposures": int(receipt["fixture_selection_exposures"]),
        "receipt_uri": P2_FIXTURE_RECEIPT_PATH.as_posix(),
        "receipt_sha256": str(receipt["receipt_sha256"]),
        "execution_manifest_uri": P2_FIXTURE_MANIFEST_PATH.as_posix(),
        "execution_manifest_sha256": str(manifest["manifest_sha256"]),
        "fixture_package_sha256": str(receipt["fixture_package_sha256"]),
        "deterministic_rerun": str(receipt["deterministic_rerun"]),
        "canonical_hashes_match": bool(receipt["canonical_hashes_match"]),
        "negative_checks_passed": bool(receipt["negative_checks_passed"]),
        "negative_check_count": int(receipt["negative_check_count"]),
    }


def _load_manifests(directory: Path) -> list[dict[str, Any]]:
    if not directory.is_dir():
        return []
    values: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(value, dict):
            continue
        try:
            values.append(manifest_round_trip(value))
        except ValueError:
            continue
    return values


def _load_receipts(
    directory: Path,
    *,
    invalidated_receipt_hashes: set[str] | None = None,
) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    invalidated = invalidated_receipt_hashes or set()
    if not directory.is_dir():
        return values
    for path in sorted(directory.glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(value, dict):
            continue
        try:
            receipt = validate_receipt(value)
        except (OwnerLocalContractError, ValueError):
            continue
        if str(receipt.get("receipt_sha256", "")) in invalidated:
            continue
        values.append(receipt)
    return values


def _load_legacy_disposition(root: Path) -> dict[str, Any]:
    path = root / LEGACY_DISPOSITION_RELATIVE_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict) or set(payload) != LEGACY_DISPOSITION_KEYS:
        return {}
    if (
        payload.get("schema_version") != "myis.evidence-disposition.v1"
        or payload.get("status") != "historical_invalid_superseded"
        or payload.get("evidence_class") != "historical_invalid"
        or payload.get("promotable") is not False
    ):
        return {}
    unsigned = {key: value for key, value in payload.items() if key != "record_sha256"}
    if sha256(canonical_json(unsigned)) != payload.get("record_sha256"):
        return {}
    source_uri = payload.get("source_uri")
    if not isinstance(source_uri, str):
        return {}
    try:
        source = (root / source_uri).resolve(strict=True)
        source.relative_to(root)
    except (OSError, ValueError):
        return {}
    if (
        source.is_symlink()
        or not source.is_file()
        or not _legacy_file_commitment_matches(source, str(payload.get("source_file_sha256", "")))
    ):
        return {}
    invalidation = payload.get("invalidation_evidence")
    if not isinstance(invalidation, dict) or set(invalidation) != {"uri", "sha256"}:
        return {}
    try:
        audit = (root / str(invalidation["uri"])).resolve(strict=True)
        audit.relative_to(root)
    except (OSError, ValueError):
        return {}
    if (
        audit.is_symlink()
        or not audit.is_file()
        or not _legacy_file_commitment_matches(audit, str(invalidation.get("sha256", "")))
    ):
        return {}
    if not isinstance(payload.get("reason_codes"), list) or not payload["reason_codes"]:
        return {}
    return payload


def _load_validation_reports(directory: Path) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    if not directory.is_dir():
        return values
    for path in sorted(directory.glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            validate_validation_report(value)
        except (OSError, json.JSONDecodeError, ManifestValidationError, TypeError, ValueError):
            continue
        values.append(value)
    return values


def validated_p1_matrix(
    manifests: list[dict[str, Any]],
    receipts: list[dict[str, Any]],
    validation_reports: list[dict[str, Any]] | None = None,
) -> list[dict[str, dict[str, Any]]]:
    """Return P1 facts only when the full arm/split/scope matrix is committed."""

    reports = validation_reports or []
    valid_manifest_hashes = {
        str(report.get("manifest_sha256", ""))
        for report in reports
        if report.get("status") == "valid"
    }
    pairs = [
        pair for pair in validated_p1_pairs(manifests, receipts)
        if str(pair["manifest"].get("manifest_sha256", "")) in valid_manifest_hashes
    ]
    ordered = sorted(pairs, key=lambda item: str(item["manifest"]["run_id"]))
    return ordered if _has_complete_p1_matrix(ordered) else []


def validated_p1_pairs(manifests: list[dict[str, Any]], receipts: list[dict[str, Any]]) -> list[dict[str, dict[str, Any]]]:
    """Return individually validated P1 manifest/receipt pairs for additive mirrors."""

    valid_manifests: list[dict[str, Any]] = []
    for manifest in manifests:
        try:
            valid_manifests.append(manifest_round_trip(manifest))
        except (TypeError, ValueError):
            continue
    valid_receipts: list[dict[str, Any]] = []
    for receipt in receipts:
        try:
            valid_receipts.append(validate_receipt(receipt))
        except (OwnerLocalContractError, TypeError, ValueError):
            continue
    receipts_by_sha = {str(receipt.get("receipt_sha256", "")): receipt for receipt in valid_receipts}
    invalidated_receipts = {
        str(manifest.get("receipt_sha256", ""))
        for manifest in valid_manifests
        if _is_p1_manifest(manifest) and manifest.get("status") != "valid"
    }
    pairs: list[dict[str, dict[str, Any]]] = []
    for manifest in valid_manifests:
        if not _is_p1_manifest(manifest) or manifest.get("status") != "valid":
            continue
        receipt_sha = str(manifest.get("receipt_sha256", ""))
        receipt = receipts_by_sha.get(receipt_sha)
        if receipt_sha in invalidated_receipts or not _is_accepted_p1_receipt(receipt):
            continue
        if not _manifest_metrics_match_receipt(manifest, receipt):
            continue
        pairs.append({"manifest": manifest, "receipt": receipt})
    return sorted(pairs, key=lambda item: str(item["manifest"]["run_id"]))


def _is_p1_manifest(manifest: dict[str, Any]) -> bool:
    return (
        manifest.get("campaign_id") == "scope-autoindex-v1"
        and manifest.get("evidence_class") == "train_selection_measured"
        and manifest.get("stage") in {"train", "selection"}
    )


def _is_accepted_p1_receipt(receipt: dict[str, Any] | None) -> bool:
    return bool(receipt) and (
        receipt.get("status") == "accepted"
        and not receipt.get("blockers")
        and receipt.get("decision_id") == "P1_CPU_EXECUTION_ENVELOPE"
        and receipt.get("phase_id") == "P1_CPU_BASELINE"
        and receipt.get("stage") == "train_selection"
    )


def _manifest_metrics_match_receipt(manifest: dict[str, Any], receipt: dict[str, Any]) -> bool:
    metrics = manifest.get("metrics")
    receipt_metrics = receipt.get("metrics")
    if not isinstance(metrics, list) or not metrics or not isinstance(receipt_metrics, list):
        return False
    arm = _manifest_arm(manifest)
    split = manifest.get("stage")
    if arm not in P1_ARMS or split not in P1_SPLITS:
        return False
    if len(metrics) != len(P1_SCOPES):
        return False
    manifest_rows = _metric_rows(metrics, arm, split)
    receipt_rows = _metric_rows(receipt_metrics, arm, split)
    if manifest_rows is None or receipt_rows is None:
        return False
    return {canonical_json(row) for row in manifest_rows} == {canonical_json(row) for row in receipt_rows}


def _has_complete_p1_matrix(pairs: list[dict[str, dict[str, Any]]]) -> bool:
    """Require R0/R0-W x train/selection with exactly ALL/IN/OUT each."""

    slots: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}
    for pair in pairs:
        manifest = pair["manifest"]
        slot = (_manifest_arm(manifest), str(manifest.get("stage", "")))
        if slot[0] not in P1_ARMS or slot[1] not in P1_SPLITS or slot in slots:
            return False
        slots[slot] = pair
    expected_slots = {(arm, split) for arm in P1_ARMS for split in P1_SPLITS}
    if set(slots) != expected_slots:
        return False
    receipt_hashes = {str(pair["receipt"].get("receipt_sha256", "")) for pair in slots.values()}
    return len(receipt_hashes) == 1


def _manifest_arm(manifest: dict[str, Any]) -> str:
    method = manifest.get("method", {})
    if not isinstance(method, dict):
        return ""
    return str(method.get("arm_id") or method.get("arm") or "")


def _metric_rows(metrics: list[Any], arm: str, split: str) -> list[dict[str, Any]] | None:
    rows = [
        row for row in metrics
        if isinstance(row, dict) and row.get("arm") == arm and row.get("split") == split
    ]
    if len(rows) != len(P1_SCOPES) or {str(row.get("scope", "")) for row in rows} != P1_SCOPES:
        return None
    if any(set(row) != P1_ACCEPTED_METRIC_FIELDS for row in rows):
        return None
    return rows


def _registration_matches_p1_pair(
    registration: dict[str, Any],
    pairs: list[dict[str, dict[str, Any]]],
    package_review: dict[str, Any],
) -> bool:
    if registration.get("schema_version") == "myis.p1-mlflow-registration.v2":
        children = registration.get("children")
        if not isinstance(children, list) or len(children) != 4:
            return False
        expected = {
            (pair["manifest"]["run_id"], pair["manifest"]["manifest_sha256"])
            for pair in pairs
        }
        observed = {
            (child.get("source_run_id"), child.get("source_manifest_sha256"))
            for child in children if isinstance(child, dict)
        }
        receipt_hashes = {pair["receipt"]["receipt_sha256"] for pair in pairs}
        return (
            observed == expected
            and receipt_hashes == {registration.get("source_receipt_sha256")}
            and bool(package_review)
            and registration.get("package_sha256") == package_review.get("package_sha256")
        )
    return False


def _validated_p1_package_review(root: Path, pairs: list[dict[str, dict[str, Any]]]) -> dict[str, Any]:
    """Require one hash-bound four-slot package and a clean artifact-only rigor review."""

    manifest_hashes = {pair["manifest"]["manifest_sha256"] for pair in pairs}
    receipt_hashes = {pair["receipt"]["receipt_sha256"] for pair in pairs}
    if len(manifest_hashes) != 4 or len(receipt_hashes) != 1:
        return {}
    package_directory = root / "campaigns/scope-autoindex-v1/packages"
    review_directory = root / "outputs/audits/rigor"
    for package_path in sorted(package_directory.glob("*.package.json")) if package_directory.is_dir() else ():
        try:
            package = load_package(package_path, root)
        except (DapfamP1Error, OSError, json.JSONDecodeError, ValueError):
            continue
        slots = package.get("slots")
        if (
            package.get("receipt_sha256") not in receipt_hashes
            or not isinstance(slots, list)
            or {slot.get("manifest_sha256") for slot in slots if isinstance(slot, dict)} != manifest_hashes
        ):
            continue
        relative_package = package_path.relative_to(root).as_posix()
        package_file_hash = _file_sha256(package_path)
        for review_path in sorted(review_directory.rglob("*.json")) if review_directory.is_dir() else ():
            try:
                review = json.loads(review_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(review, dict) or review.get("schema_version") != "myis.rigor-review.v1":
                continue
            governance = review.get("governance")
            findings = review.get("findings")
            if (
                review.get("review_status") == "complete"
                and review.get("artifact_path") == relative_package
                and review.get("artifact_sha256") == package_file_hash
                and isinstance(governance, dict)
                and governance.get("approval_valid") is True
                and governance.get("split_isolation_valid") is True
                and governance.get("gate_order_valid") is True
                and governance.get("budget_valid") is True
                and governance.get("manifest_integrity_valid") is True
                and governance.get("blocking_findings") == []
                and isinstance(findings, list)
                and not any(isinstance(item, dict) and item.get("severity") == "critical" for item in findings)
            ):
                overall = review.get("overall") if isinstance(review.get("overall"), dict) else {}
                return {
                    "package_id": package["package_id"],
                    "package_uri": relative_package,
                    "package_sha256": package["package_sha256"],
                    "package_file_sha256": package_file_hash,
                    "review_id": str(review.get("review_id", review_path.stem)),
                    "review_uri": review_path.relative_to(root).as_posix(),
                    "review_sha256": _file_sha256(review_path),
                    "grade": overall.get("grade"),
                    "mean_score": overall.get("mean_score"),
                }
    return {}


def _dataset_projection(root: Path, receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if receipts:
        contract_path = root / "control/assets/dapfam-p1-source.v1.json"
        try:
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            contract = {}
        if isinstance(contract, dict) and contract.get("schema_version") == "myis.dapfam-p1-source.v1":
            receipt = receipts[0]
            counts = receipt.get("aggregate_counts", {})
            lineage = receipt.get("lineage_hashes", {})
            return [
                {
                    "dataset_id": "DAPFAM-FAMILY-CORPUS",
                    "role": "family-corpus",
                    "representation": "one full TAC document per family",
                    "classification": "measured-source",
                    "counts": {"families": counts.get("families"), "documents": counts.get("r0_documents")},
                    "sha256": lineage.get("corpus_sha256"),
                    "protection": "owner-local-only",
                },
                {
                    "dataset_id": "DAPFAM-QUERY-SET",
                    "role": "query-set",
                    "representation": "TAC train/selection queries",
                    "classification": "measured-source",
                    "counts": {"queries": counts.get("queries"), "train": counts.get("train_queries"), "selection": counts.get("selection_queries"), "final_closed": counts.get("final_queries")},
                    "sha256": lineage.get("query_sha256"),
                    "protection": "owner-local-only",
                },
                {
                    "dataset_id": "DAPFAM-RELEVANCE-LABELS",
                    "role": "relevance-labels",
                    "representation": "positive family relations with released IN/OUT labels",
                    "classification": "measured-source",
                    "counts": {"positive": counts.get("positive_relations"), "in": counts.get("positive_in_relations"), "out": counts.get("positive_out_relations")},
                    "sha256": lineage.get("qrels_sha256"),
                    "protection": "owner-local-only",
                },
                {
                    "dataset_id": "DAPFAM-R0-CANDIDATES",
                    "role": "r0-candidate",
                    "representation": "full TAC family document",
                    "classification": "measured-derived",
                    "counts": {"documents": counts.get("r0_documents")},
                    "sha256": receipt.get("aggregate_hashes", {}).get("r0_index"),
                    "protection": "external-derived-store",
                },
                {
                    "dataset_id": "DAPFAM-R0W-CANDIDATES",
                    "role": "r0-w-candidate",
                    "representation": "non-overlapping 512-token full TAC windows with family MaxP",
                    "classification": "measured-derived",
                    "counts": {"windows": counts.get("r0w_windows")},
                    "sha256": receipt.get("aggregate_hashes", {}).get("r0-w_index"),
                    "protection": "external-derived-store",
                },
            ]
    inventory_path = root / "evidence" / "legacy-dapfam-inventory.v1.json"
    if not inventory_path.is_file():
        return []
    try:
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    assets = inventory.get("assets", []) if isinstance(inventory, dict) else []
    by_path = {str(item.get("path")): item for item in assets if isinstance(item, dict)}
    receipt = receipts[0] if receipts else {}
    counts = receipt.get("aggregate_counts", {}) if isinstance(receipt, dict) else {}
    hashes = receipt.get("aggregate_hashes", {}) if isinstance(receipt, dict) else {}
    def asset(asset_id: str, path: str, role: str, representation: str, classification: str) -> dict[str, Any]:
        row = by_path.get(path, {})
        return {
            "dataset_id": asset_id,
            "role": role,
            "representation": representation,
            "classification": classification,
            "bytes": row.get("bytes"),
            "sha256": row.get("sha256"),
            "protection": "owner-local-only" if ("qrel" in path or "quer" in path) else "metadata-safe",
        }
    rows = [
        asset("DAPFAM-FAMILY-CORPUS", "processed/dapfam/patents.jsonl", "family-corpus", "patent family records", "reusable-after-certification"),
        asset("DAPFAM-QUERY-SET", "processed/dapfam/queries.jsonl", "query-set", "TAC query records", "reusable-after-certification"),
        asset("DAPFAM-RELEVANCE-LABELS", "processed/dapfam/qrels.tsv", "relevance-labels", "family relevance labels", "reusable-after-certification"),
        asset("DAPFAM-R0-CANDIDATES", "processed/dapfam/chunks_doc.jsonl", "r0-candidate", "one document per family candidate", "reusable-after-certification"),
        asset("DAPFAM-R0W-CANDIDATES", "processed/retrieval/dapfam_citation_controlled_tac512/corpus_tac_passages.jsonl", "r0-w-candidate", "TAC512 passages with family MaxP", "reusable-after-certification"),
        asset("DAPFAM-R1-REFERENCE", "processed/dapfam/chunks_section.jsonl", "r1-reference", "section units", "historical-reference"),
        asset("DAPFAM-INCOMPATIBLE", "processed/dapfam/chunks_element.jsonl", "incompatible", "element units", "incompatible"),
    ]
    rows[0]["counts"] = {"patents": counts.get("patents"), "families": counts.get("patents")}
    rows[1]["counts"] = {"queries": counts.get("queries")}
    rows[2]["sha256"] = next((str(value) for key, value in hashes.items() if "qrels" in str(key) and str(key).endswith("sha256")), None)
    rows[3]["counts"] = {"documents": counts.get("r0_documents")}
    rows[4]["counts"] = {"passages": counts.get("r0w_passages")}
    rows[5]["constraint"] = "reference only; not active R1 main"
    rows[6]["constraint"] = "exceeds four-unit DAPFAM limit; never active R1 main"
    return rows


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    values: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if isinstance(value, dict):
            values.append(value)
    return values


def _load_optional_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _file_sha256(path: Path) -> str:
    if not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _legacy_file_commitment_matches(path: Path, expected: str) -> bool:
    """Keep the historical Windows receipt bound across Git LF checkouts."""

    if not path.is_file() or path.is_symlink():
        return False
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() == expected:
        return True
    crlf = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return hashlib.sha256(crlf).hexdigest() == expected


def _load_yaml_like(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError:
        return {}
    if not path.is_file():
        return {}
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _source_commit_metadata(root: Path) -> tuple[str, str]:
    try:
        completed = subprocess.run(
            ["git", "log", "-1", "--format=%H%n%cI", "--", *PROJECTION_SOURCE_PATHS],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        commit, timestamp = completed.stdout.strip().splitlines()[:2]
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return commit, parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except (OSError, subprocess.SubprocessError, ValueError):
        return "0" * 40, "1970-01-01T00:00:00Z"


def _publication_readiness(
    root: Path,
    p1_pairs: list[dict[str, dict[str, Any]]],
    decisions: list[dict[str, Any]],
    legacy_disposition: dict[str, Any],
) -> dict[str, Any]:
    checks = [
        {"id": "canonical_run_manifest", "status": "pass" if p1_pairs else "blocked", "source": "campaigns/scope-autoindex-v1/manifests"},
        {"id": "owner_local_aggregate", "status": "pass" if p1_pairs else "blocked", "source": "campaigns/scope-autoindex-v1/evidence"},
        {"id": "d2_open_final", "status": "pass" if any(item.get("decision_id") == "D2_OPEN_FINAL" and item.get("status") == "approved" for item in decisions) else "blocked", "source": "control/decisions/ledger.jsonl"},
        {"id": "live_venue_check", "status": "unknown", "source": "Owner/live venue verification"},
        {"id": "prior_publication_status", "status": "unknown", "source": "Owner publication declaration"},
        {"id": "paper_build_hash_closure", "status": "blocked", "source": "03_Paper/publications/isai-nlp-2026"},
        {"id": "historical_final_872_exposure", "status": "blocked" if legacy_disposition or any(pair["receipt"].get("historical_exposure", {}).get("active_final_872_global_untouched") == "not_claimable" for pair in p1_pairs) else "unknown", "source": "owner-local historical exposure audit"},
    ]
    status = "ready" if all(item["status"] == "pass" for item in checks) else "blocked"
    return {"schema_version": "myis.publication-readiness.v1", "status": status, "checks": checks}
