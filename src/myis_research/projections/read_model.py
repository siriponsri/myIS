"""Build the single aggregate read model consumed by Dashboard, Brain, and Paper."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


READ_MODEL_SCHEMA = "myis.read-model.v1"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def build_read_model(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    campaign_id = "scope-autoindex-v1"
    campaign_config = _load_yaml_like(root / "control" / "campaigns" / f"{campaign_id}.yaml")
    manifests = _load_manifests(root / "campaigns" / campaign_id / "manifests")
    decisions = _load_jsonl(root / "control" / "decisions" / "ledger.jsonl")
    metrics: list[dict[str, Any]] = []
    runs: list[dict[str, Any]] = []
    experiments: dict[str, dict[str, Any]] = {}
    evidence: list[dict[str, Any]] = []
    total_actual = 0.0
    total_estimated = 0.0
    for manifest in manifests:
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
            "experiment_id": experiment_id,
            "campaign_id": campaign_id,
            "stage": manifest.get("stage", "unknown"),
            "status": manifest.get("status", "unknown"),
            "arm": manifest.get("method", {}).get("arm_id") if isinstance(manifest.get("method"), dict) else None,
            "source": manifest.get("source", {}),
            "owner_local_receipt_sha256": manifest.get("owner_local_receipt_sha256"),
        })
        for artifact in manifest.get("artifacts", []) if isinstance(manifest.get("artifacts"), list) else []:
            if isinstance(artifact, dict) and artifact.get("sha256"):
                evidence.append({"evidence_id": artifact.get("artifact_id", artifact.get("name", "artifact")), "sha256": artifact["sha256"], "run_id": run_id, "uri": artifact.get("uri")})
    readiness = _publication_readiness(root, manifests, decisions)
    configured_phases = campaign_config.get("phases", []) if isinstance(campaign_config.get("phases"), list) else []
    phases = []
    tasks = []
    for phase in configured_phases:
        if not isinstance(phase, dict):
            continue
        phase_id = str(phase.get("id", ""))
        phase_row = {"phase_id": phase_id, "status": str(phase.get("status", "planned")), "tasks": []}
        for task in phase.get("tasks", []) if isinstance(phase.get("tasks"), list) else []:
            if not isinstance(task, dict):
                continue
            task_row = {"task_id": str(task.get("id", "")), "phase_id": phase_id, "title": str(task.get("title", "")), "status": str(task.get("status", "planned")), "evidence_ids": []}
            phase_row["tasks"].append(task_row)
            tasks.append(task_row)
        phases.append(phase_row)
    body: dict[str, Any] = {
        "schema_version": READ_MODEL_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "campaigns": [{
            "campaign_id": campaign_id,
            "status": campaign_config.get("campaign", {}).get("status", "preparation"),
            "title": campaign_config.get("campaign", {}).get("title", campaign_id),
            "primary_metric": campaign_config.get("protocol", {}).get("primary_metric", "recall_at_100/out"),
            "standing_authorization": "D1_START_CAMPAIGN",
            "active_owner_decisions": ["D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"],
        }],
        "phases": phases,
        "tasks": tasks,
        "gates": [
            {"gate_id": "D2_OPEN_FINAL", "status": "approved" if any(item.get("decision_id") == "D2_OPEN_FINAL" and item.get("status") == "approved" for item in decisions) else "waiting_owner"},
            {"gate_id": "D3_SUBMIT_RELEASE", "status": "approved" if any(item.get("decision_id") == "D3_SUBMIT_RELEASE" and item.get("status") == "approved" for item in decisions) else "waiting_owner"},
        ],
        "experiments": sorted(experiments.values(), key=lambda item: item["experiment_id"]),
        "runs": sorted(runs, key=lambda item: item["run_id"]),
        "metrics": metrics,
        "cost": {"currency": "USD", "actual": total_actual if manifests else None, "estimated": total_estimated if manifests else 0.0, "budget": 100.0},
        "decisions": decisions,
        "evidence": evidence,
        "publication_readiness": readiness,
    }
    revision_body = {key: value for key, value in body.items() if key != "generated_at"}
    body["projection_revision"] = sha256(canonical_json(revision_body))
    return body


def write_read_model(repository_root: Path, output: Path | None = None) -> Path:
    root = repository_root.resolve()
    target = output or root / "projections" / "read-model" / "read-model.v1.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(build_read_model(root), ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def _load_manifests(directory: Path) -> list[dict[str, Any]]:
    if not directory.is_dir():
        return []
    values: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            values.append(value)
    return values


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


def _load_yaml_like(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError:
        return {}
    if not path.is_file():
        return {}
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _publication_readiness(root: Path, manifests: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> dict[str, Any]:
    checks = [
        {"id": "canonical_run_manifest", "status": "pass" if manifests else "blocked", "source": "campaigns/scope-autoindex-v1/manifests"},
        {"id": "owner_local_aggregate", "status": "pass" if any(item.get("owner_local_receipt_sha256") for item in manifests) else "blocked", "source": "control/owner-local"},
        {"id": "d2_open_final", "status": "pass" if any(item.get("decision_id") == "D2_OPEN_FINAL" and item.get("status") == "approved" for item in decisions) else "blocked", "source": "control/decisions/ledger.jsonl"},
        {"id": "live_venue_check", "status": "unknown", "source": "Owner/live venue verification"},
        {"id": "prior_publication_status", "status": "unknown", "source": "Owner publication declaration"},
        {"id": "paper_build_hash_closure", "status": "blocked", "source": "03_Paper/publications/isai-nlp-2026"},
    ]
    status = "ready" if all(item["status"] == "pass" for item in checks) else "blocked"
    return {"schema_version": "myis.publication-readiness.v1", "status": status, "checks": checks}
