"""Read-model projection for the aggregate-safe Observatory fixture."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .core import ObservatoryError, validate_registry
from .graph import build_evidence_graph, validate_evidence_graph


PROJECTION_SCHEMA = "myis.observatory-projection.v1"
FIXTURE_RELATIVE = Path("outputs/observatory/fixture-v1")


def load_observatory_registry(root: Path) -> dict[str, Any]:
    path = root / FIXTURE_RELATIVE / "registry.json"
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
        validate_registry(registry)
        graph = build_evidence_graph(registry)
        validate_evidence_graph(graph, registry)
        return registry
    except (OSError, UnicodeError, json.JSONDecodeError, ObservatoryError, TypeError, ValueError) as error:
        raise ObservatoryError("validated Observatory registry is unavailable") from error


def load_observatory_projection(root: Path) -> dict[str, Any]:
    """Load only validated, repository-safe Observatory metadata."""

    base = root / FIXTURE_RELATIVE
    registry_path = base / "registry.json"
    receipt_path = base / "receipt.json"
    if not registry_path.is_file() or not receipt_path.is_file():
        return _missing_projection()
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        validate_registry(registry)
        graph = build_evidence_graph(registry)
        validate_evidence_graph(graph, registry)
        if receipt.get("registry_sha256") != registry.get("registry_sha256"):
            raise ObservatoryError("Observatory receipt is not bound to registry")
        if receipt.get("evidence_class") != "fixture" or receipt.get("scientific_authority") is not False:
            raise ObservatoryError("fixture authority boundary is invalid")
        if receipt.get("protected_data_accessed") is not False or receipt.get("measured_execution") is not False:
            raise ObservatoryError("fixture crossed the protected or measured boundary")
    except (OSError, UnicodeError, json.JSONDecodeError, ObservatoryError, TypeError, ValueError):
        return {**_missing_projection(), "status": "invalid", "integrity_status": "fail"}

    records = registry.get("records", {})
    artifacts = records.get("artifacts", [])
    metrics = records.get("metrics", [])
    runs = records.get("runs", [])
    failures = records.get("failures", [])
    recoveries = records.get("recoveries", [])
    lifecycle = Counter(str(item.get("status", "unknown")) for item in runs)
    artifact_types = Counter(str(item.get("artifact_type", "unknown")) for item in artifacts)
    negative_checks = receipt.get("negative_checks", {})
    retention_classes = Counter(str(item.get("retention_class", "unspecified")) for item in artifacts)
    lineage_complete = all(
        all(key in item for key in ("producing_run_id", "producing_phase_id", "producing_task_id", "parent_artifact_hashes", "child_artifact_hashes"))
        for item in artifacts
    )
    return {
        "schema_version": PROJECTION_SCHEMA,
        "status": "ready",
        "integrity_status": "pass",
        "fixture_id": receipt.get("fixture_id"),
        "evidence_class": "fixture",
        "scientific_authority": False,
        "claim_boundary": "engineering_provenance_only",
        "registry_sha256": registry.get("registry_sha256"),
        "receipt_sha256": receipt.get("receipt_sha256"),
        "package_sha256": receipt.get("package_sha256"),
        "mlflow_run_id": receipt.get("mlflow_run_id"),
        "mlflow_record_sha256": receipt.get("mlflow_record_sha256"),
        "real_counters": dict(receipt.get("real_counters", {})),
        "protected_data_accessed": False,
        "measured_execution": False,
        "record_counts": {key: len(value) for key, value in sorted(records.items()) if isinstance(value, list)},
        "run_status_counts": dict(sorted(lifecycle.items())),
        "artifact_type_counts": dict(sorted(artifact_types.items())),
        "retention_class_counts": dict(sorted(retention_classes.items())),
        "artifact_lineage_status": "pass" if lineage_complete else "fail",
        "prompt_binding_count": len(records.get("prompts", [])),
        "config_binding_count": len(records.get("configs", [])),
        "environment_binding_count": len(records.get("environments", [])),
        "failure_records": [
            {
                key: item.get(key)
                for key in ("record_id", "run_id", "stage", "failure_class", "last_valid_checkpoint", "counters_before", "counters_after", "protected_data_accessed", "recovery_id", "recovery_action", "validation_after_recovery", "residual_risk", "decision")
            }
            for item in failures if isinstance(item, dict)
        ],
        "recovery_records": [
            {
                key: item.get(key)
                for key in ("record_id", "run_id", "failure_id", "action", "validation_after_recovery", "counters_before", "counters_after", "residual_risk", "metric_promotion")
            }
            for item in recoveries if isinstance(item, dict)
        ],
        "validated_artifact_count": sum(item.get("validation_status") == "validated" for item in artifacts),
        "validated_metric_count": sum(1 for item in metrics if item.get("record_id")),
        "failed_child_count": len(failures),
        "recovered_child_count": len(recoveries),
        "graph_node_count": len(graph.nodes),
        "graph_edge_count": len(graph.edges),
        "negative_checks_passed": bool(negative_checks) and all(value == "PASS" for value in negative_checks.values()),
        "negative_check_count": len(negative_checks),
        "next_action": receipt.get("next_action", "Owner-local P2 measured preflight"),
        "narrative": "Synthetic Observatory evidence is ready; measured P2 remains closed.",
    }


def _missing_projection() -> dict[str, Any]:
    return {
        "schema_version": PROJECTION_SCHEMA,
        "status": "not_available",
        "integrity_status": "unknown",
        "fixture_id": None,
        "evidence_class": "fixture",
        "scientific_authority": False,
        "claim_boundary": "no_measured_claim",
        "registry_sha256": None,
        "receipt_sha256": None,
        "package_sha256": None,
        "mlflow_run_id": None,
        "mlflow_record_sha256": None,
        "real_counters": {"measured_runs": 0, "candidate_count": 0, "shortlist_count": 0, "selection_accesses": 0},
        "protected_data_accessed": False,
        "measured_execution": False,
        "record_counts": {},
        "run_status_counts": {},
        "artifact_type_counts": {},
        "validated_artifact_count": 0,
        "validated_metric_count": 0,
        "failed_child_count": 0,
        "recovered_child_count": 0,
        "retention_class_counts": {},
        "artifact_lineage_status": "unknown",
        "prompt_binding_count": 0,
        "config_binding_count": 0,
        "environment_binding_count": 0,
        "failure_records": [],
        "recovery_records": [],
        "graph_node_count": 0,
        "graph_edge_count": 0,
        "negative_checks_passed": False,
        "negative_check_count": 0,
        "next_action": "Build the repository-only Observatory fixture",
        "narrative": "No validated Observatory fixture is available.",
    }
