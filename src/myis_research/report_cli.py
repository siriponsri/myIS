"""Build and verify the integrated Dashboard, MLflow, and Obsidian projections."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import stat
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from .armindex.constants import A0_8_NEXT_AUTHORIZED_ACTION
from .mlflow_archive import (
    ACTIVE_CAMPAIGN,
    ArchiveRun,
    FreezeBundle,
    MLflowEvidenceArchive,
    RegistrySnapshot,
    RULE_REGISTRY_SCHEMA,
    SCHEMA_REGISTRY_SCHEMA,
)
from .mlflow_mirror import default_store as default_mlflow_store
from .progress import DEFAULT_HEARTBEAT_SECONDS
from .projections.read_model import build_read_model, canonical_json, sha256, write_read_model
from .report_records import build_report_records, report_json_outputs


READ_MODEL_RELATIVE_PATH = Path("projections/read-model/read-model.v2.json")
VAULT_RELATIVE_PATH = Path("obsidian_report")
GENERATED_MANIFEST_RELATIVE_PATH = VAULT_RELATIVE_PATH / "00_System/Generated/generated-manifest.json"
SYNC_RECEIPT_RELATIVE_PATH = Path("projections/sync-receipt.v2.json")
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
_NOTE_ID_RE = re.compile(r"^note_id:\s*([^\r\n]+)$", re.MULTILINE)
_FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
_PROPERTY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_]*):\s*(.*)$")
_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
_UNSAFE_HTML_RE = re.compile(r"<(?:script|iframe|object|embed|style)\b", re.IGNORECASE)
_ABSOLUTE_PERSONAL_PATH_RE = re.compile(r"[A-Za-z]:[\\/]Users[\\/]", re.IGNORECASE)
_PROTECTED_FIELD_RE = re.compile(
    r"(?:query_ids?|split_membership|per_query(?:_outcomes?)?|raw_provider_payload|"
    r"credentials?|api_keys?)\s*[:=]",
    re.IGNORECASE,
)
_REMOTE_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(https?://", re.IGNORECASE)
_SNAPSHOT_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,63}$")
_ALLOWED_NOTE_TYPES = frozenset({
    "home", "project_map", "phase_report", "task_report", "result_report",
    "advisor_update", "literature_proxy", "literature_synthesis", "history_report",
    "run_report", "decision", "risk", "failed_attempt", "presentation", "glossary", "owner_note",
})
_ALLOWED_WORKFLOW_STATUSES = frozenset({
    "waiting_dependency", "ready", "in_progress", "verification_needed",
    "waiting_gate", "blocked", "complete",
})
_ALLOWED_EVIDENCE_MATURITY = frozenset({
    "non_scientific", "fixture", "dry_run", "measured_development",
    "measured_selection", "confirmatory", "publication", "historical_exposed",
    "planned", "engineering", "train_selection_measured", "static_contract_review",
})
_ALLOWED_CLAIM_LEVELS = frozenset({
    "none", "descriptive", "exploratory", "confirmatory", "publication_ready",
})
_REQUIRED_NOTE_PROPERTIES = frozenset({
    "schema_version", "note_id", "note_type", "workflow_status", "evidence_maturity",
    "claim_level", "safe_to_present", "managed_by", "edit_policy",
    "read_model_revision", "read_model_sha256", "source_commit",
    "projection_schema_version", "source_run_ids", "source_manifest_sha256",
    "related_literature_ids", "related_decision_ids",
    "evidence_class", "scientific_authority", "claim_boundary",
    "generated_from_revision", "last_material_update", "next_authorized_action",
})


def validate_read_model(model: Mapping[str, Any]) -> None:
    if not isinstance(model, Mapping):
        raise ValueError("read model must be a JSON object")
    schema_path = Path(__file__).resolve().parents[2] / "schemas" / "read-model.v2.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(dict(model))
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        raise ValueError(f"read model schema validation failed: {error}") from error
    if model.get("read_model_revision") != model.get("projection_revision"):
        raise ValueError("read model revision aliases do not match")
    recorded = model.get("read_model_sha256")
    if not isinstance(recorded, str) or not _SHA256_RE.fullmatch(recorded):
        raise ValueError("read_model_sha256 must be SHA-256")
    unsigned = {key: value for key, value in model.items() if key != "read_model_sha256"}
    if sha256(canonical_json(unsigned)) != recorded:
        raise ValueError("read_model_sha256 does not match canonical read model")
    gate_ids = {str(item.get("gate_id")) for item in model.get("gates", []) if isinstance(item, Mapping)}
    if gate_ids != {"D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"}:
        raise ValueError("read model must expose exactly D2 and D3 decisions")


def projection_report_contents(
    root: Path,
    model: Mapping[str, Any],
    *,
    mlflow_run_id: str | None = None,
) -> dict[Path, str]:
    """Render every generated projection without mutating the filesystem."""

    root = root.resolve()
    validate_read_model(model)
    revision = str(model["read_model_revision"])
    model_sha = str(model["read_model_sha256"])
    source_commit = str(model["source_commit"])
    vault_contents = _obsidian_vault_contents(root, model)
    _validate_generated_contents(vault_contents, model)
    manifest = _generated_manifest(model, vault_contents)
    manifest_text = _json_text(manifest)

    archive = {
        **_mlflow_archive_index(model),
        "dashboard_snapshot_sha256": model_sha,
        "obsidian_manifest_sha256": manifest["manifest_sha256"],
    }
    archive_text = _json_text(archive)

    external_outputs = {
        **_brain_report_contents(root, model),
        **_paper_report_contents(root, model),
        **_compatibility_report_contents(root, model),
    }
    _validate_external_projection_contents(external_outputs)
    outputs = {
        root / relative: content for relative, content in vault_contents.items()
    }
    outputs[root / GENERATED_MANIFEST_RELATIVE_PATH] = manifest_text
    outputs[root / "mlflow/generated/archive-index.v2.json"] = archive_text
    if mlflow_run_id is not None:
        lifecycle = _a010_projection_lifecycle(
            root,
            model,
            archive_text=archive_text,
            obsidian_manifest_sha256=str(manifest["manifest_sha256"]),
            external_outputs=external_outputs,
        )
        outputs[root / SYNC_RECEIPT_RELATIVE_PATH] = _json_text({
            "schema_version": "myis.projection-sync-receipt.v2",
            "projection_schema_version": model["projection_schema_version"],
            "read_model_revision": revision,
            "read_model_sha256": model_sha,
            "source_commit": source_commit,
            "mlflow_run_id": mlflow_run_id,
            "mlflow_archive_sha256": sha256(archive_text.encode("utf-8")),
            "dashboard_snapshot_sha256": model_sha,
            "obsidian_manifest_sha256": manifest["manifest_sha256"],
            **lifecycle,
            "status": "PASS",
        })
    outputs.update(external_outputs)
    outputs.update(report_json_outputs(root, model))
    return outputs


def _mlflow_archive_index(model: Mapping[str, Any]) -> dict[str, Any]:
    p2 = model.get("p2_readiness", {}) if isinstance(model.get("p2_readiness"), Mapping) else {}
    freeze = p2.get("freeze_barrier", {}) if isinstance(p2.get("freeze_barrier"), Mapping) else {}
    review = p2.get("official_review", {}) if isinstance(p2.get("official_review"), Mapping) else {}
    fixture = p2.get("fixture_pilot", {}) if isinstance(p2.get("fixture_pilot"), Mapping) else {}
    review_source = review.get("source", {}) if isinstance(review.get("source"), Mapping) else {}
    observatory = model.get("observatory", {}) if isinstance(model.get("observatory"), Mapping) else {}
    armindex = model.get("armindex", {}) if isinstance(model.get("armindex"), Mapping) else {}
    harvest = armindex.get("legacy_code_harvest", {}) if isinstance(armindex.get("legacy_code_harvest"), Mapping) else {}
    feasibility = armindex.get("compute_storage_feasibility", {}) if isinstance(armindex.get("compute_storage_feasibility"), Mapping) else {}
    closeout = armindex.get("phase_closeout", {}) if isinstance(armindex.get("phase_closeout"), Mapping) else {}
    adapter = armindex.get("adapter_fixture_validation", {}) if isinstance(armindex.get("adapter_fixture_validation"), Mapping) else {}
    return {
        "schema_version": "myis.mlflow-archive-index.v2",
        "projection_schema_version": model["projection_schema_version"],
        "read_model_revision": model["read_model_revision"],
        "read_model_sha256": model["read_model_sha256"],
        "source_commit": model["source_commit"],
        "campaign_experiment": "myis-scope-autoindex-v1",
        "system_experiment": "myis-system",
        "run_ids": [item.get("run_id") for item in model.get("runs", [])],
        "evidence_ids": [item.get("evidence_id") for item in model.get("evidence", [])],
        "status": "blocked" if model["project"]["state"] == "P1_BLOCKED_WITH_EVIDENCE" else "current",
        "armindex_legacy_code_harvest": {
            "status": harvest.get("status", "not_started"),
            "evidence_class": harvest.get("evidence_class", "engineering"),
            "scientific_authority": harvest.get("scientific_authority", False),
            "source_receipt_uri": harvest.get("receipt_uri"),
            "source_receipt_sha256": harvest.get("receipt_sha256"),
            "source_verification_receipt_uri": harvest.get("source_verification_receipt_uri"),
            "source_verification_receipt_sha256": harvest.get("source_verification_receipt_sha256"),
            "measured_runs": harvest.get("measured_runs", 0),
            "selection_accesses": harvest.get("selection_accesses", 0),
            "final_accesses": harvest.get("final_accesses", 0),
        },
        "armindex_compute_storage_feasibility": {
            "status": feasibility.get("status", "not_started"),
            "fixture_status": feasibility.get("fixture_status", "not_started"),
            "evidence_class": feasibility.get("evidence_class", "engineering_fixture"),
            "scientific_authority": feasibility.get("scientific_authority", False),
            "source_receipt_uri": feasibility.get("task_receipt_uri"),
            "source_receipt_sha256": feasibility.get("task_receipt_sha256"),
            "fixture_manifest_sha256": feasibility.get("fixture_manifest_sha256"),
            "fixture_receipt_sha256": feasibility.get("fixture_receipt_sha256"),
            "profile_count": len(feasibility.get("profiles", [])),
            "measured_runs": feasibility.get("measured_runs", 0),
            "selection_accesses": feasibility.get("selection_accesses", 0),
            "final_accesses": feasibility.get("final_accesses", 0),
        },
        "armindex_a0_phase_closeout": {
            "status": closeout.get("status", "not_started"),
            "evidence_class": closeout.get("evidence_class", "engineering_validation"),
            "scientific_authority": closeout.get("scientific_authority", False),
            "source_receipt_uri": closeout.get("receipt_uri"),
            "source_receipt_sha256": closeout.get("receipt_sha256"),
            "validation_audit_sha256": closeout.get("validation_audit_sha256"),
            "completed_task_count": closeout.get("completed_task_count", 0),
            "validation_check_count": closeout.get("validation_check_count", 0),
            "measured_runs": closeout.get("measured_runs", 0),
            "selection_accesses": closeout.get("selection_accesses", 0),
            "final_accesses": closeout.get("final_accesses", 0),
        },
        "armindex_a1_adapter_fixture": {
            "status": adapter.get("status", "not_started"),
            "fixture_status": adapter.get("fixture_status", "not_started"),
            "evidence_class": adapter.get("evidence_class", "engineering_fixture"),
            "scientific_authority": adapter.get("scientific_authority", False),
            "source_receipt_uri": adapter.get("task_receipt_uri"),
            "source_receipt_sha256": adapter.get("task_receipt_sha256"),
            "fixture_manifest_sha256": adapter.get("fixture_manifest_sha256"),
            "fixture_receipt_sha256": adapter.get("fixture_receipt_sha256"),
            "gpu_proposal_status": adapter.get("gpu_proposal_status", "not_available"),
            "gpu_proposal_sha256": adapter.get("gpu_proposal_sha256"),
            "registered_arms": adapter.get("registered_arms", 0),
            "runnable_cpu_arms": adapter.get("runnable_cpu_arms", 0),
            "dense_arms_blocked": adapter.get("dense_arms_blocked", 0),
            "measured_runs": adapter.get("measured_runs", 0),
            "selection_accesses": adapter.get("selection_accesses", 0),
            "final_accesses": adapter.get("final_accesses", 0),
        },
        "observatory": {
            "status": observatory.get("status", "not_available"),
            "evidence_class": observatory.get("evidence_class", "fixture"),
            "scientific_authority": observatory.get("scientific_authority", False),
            "registry_sha256": observatory.get("registry_sha256"),
            "receipt_sha256": observatory.get("receipt_sha256"),
            "mlflow_run_id": observatory.get("mlflow_run_id"),
            "validated_artifact_count": observatory.get("validated_artifact_count", 0),
            "validated_metric_count": observatory.get("validated_metric_count", 0),
            "failed_child_count": observatory.get("failed_child_count", 0),
            "recovered_child_count": observatory.get("recovered_child_count", 0),
            "artifact_lineage_status": observatory.get("artifact_lineage_status", "unknown"),
            "retention_class_counts": observatory.get("retention_class_counts", {}),
            "prompt_binding_count": observatory.get("prompt_binding_count", 0),
            "config_binding_count": observatory.get("config_binding_count", 0),
            "environment_binding_count": observatory.get("environment_binding_count", 0),
        },
        "p2_readiness": {
            "status": p2.get("status", "unknown"),
            "budget_profile_id": p2.get("budget_profile_id"),
            "budget_profile_sha256": p2.get("budget_profile_sha256"),
            "measured_runs": p2.get("measured_runs", 0),
            "selection_accesses": p2.get("selection_accesses", 0),
            "candidate_count": p2.get("candidate_count", 0),
            "freeze_status": freeze.get("status", "not_started"),
            "fixture_pilot": {
                "executed": fixture.get("executed", False),
                "status": fixture.get("status", "not_executed"),
                "evidence_class": fixture.get("evidence_class", "fixture"),
                "scientific_authority": fixture.get("scientific_authority", False),
                "protected_data_accessed": fixture.get("protected_data_accessed", False),
                "measured_execution_performed": fixture.get("measured_execution_performed", False),
                "synthetic_candidates": fixture.get("synthetic_candidates", 0),
                "synthetic_iterations": fixture.get("synthetic_iterations", 0),
                "synthetic_shortlist": fixture.get("synthetic_shortlist", 0),
                "fixture_selection_exposures": fixture.get("fixture_selection_exposures", 0),
                "receipt_sha256": fixture.get("receipt_sha256"),
                "execution_manifest_sha256": fixture.get("execution_manifest_sha256"),
                "fixture_package_sha256": fixture.get("fixture_package_sha256"),
                "deterministic_rerun": fixture.get("deterministic_rerun", "not_run"),
                "negative_checks_passed": fixture.get("negative_checks_passed", False),
            },
            "official_review": {
                "status": review.get("status", "not_recorded"),
                "evidence_class": review.get("evidence_class", "static_contract_review"),
                "final_round": review.get("final_round"),
                "final_verdict": review.get("final_verdict"),
                "reviewed_commit": review.get("reviewed_commit"),
                "index_sha256": review_source.get("index_sha256"),
                "protected_data_accessed": review.get("protected_data_accessed", False),
                "measured_execution_performed": review.get("measured_execution_performed", False),
            },
        },
    }


def _a010_projection_lifecycle(
    root: Path,
    model: Mapping[str, Any],
    *,
    archive_text: str,
    obsidian_manifest_sha256: str,
    external_outputs: Mapping[Path, str],
) -> dict[str, Any]:
    """Bind every projection sink to the latest validated ArmIndex task receipt."""

    armindex = model.get("armindex", {}) if isinstance(model.get("armindex"), Mapping) else {}
    harvest = armindex.get("legacy_code_harvest", {}) if isinstance(armindex.get("legacy_code_harvest"), Mapping) else {}
    feasibility = armindex.get("compute_storage_feasibility", {}) if isinstance(armindex.get("compute_storage_feasibility"), Mapping) else {}
    closeout = armindex.get("phase_closeout", {}) if isinstance(armindex.get("phase_closeout"), Mapping) else {}
    adapter = armindex.get("adapter_fixture_validation", {}) if isinstance(armindex.get("adapter_fixture_validation"), Mapping) else {}
    if adapter.get("validated") is True and adapter.get("status") == "complete":
        source_uri = adapter.get("task_receipt_uri")
        source_sha256 = adapter.get("task_receipt_sha256")
        source_validated = True
        source_phase_id = "A1_BASELINES_AND_MULTI_ARM_SCREENING"
    elif closeout.get("validated") is True and closeout.get("status") == "complete":
        source_uri = closeout.get("receipt_uri")
        source_sha256 = closeout.get("receipt_sha256")
        source_validated = True
        source_phase_id = "A0_MIGRATION_FOUNDATION"
    elif feasibility.get("validated") is True and feasibility.get("status") == "complete":
        source_uri = feasibility.get("task_receipt_uri")
        source_sha256 = feasibility.get("task_receipt_sha256")
        source_validated = True
        source_phase_id = "A0_MIGRATION_FOUNDATION"
    else:
        source_uri = harvest.get("receipt_uri")
        source_sha256 = harvest.get("receipt_sha256")
        source_validated = harvest.get("validated") is True
        source_phase_id = "A0_MIGRATION_FOUNDATION"
    if (
        source_validated is not True
        or not isinstance(source_uri, str)
        or not isinstance(source_sha256, str)
        or not _SHA256_RE.fullmatch(source_sha256)
    ):
        raise ValueError("ArmIndex projection lifecycle requires a validated source receipt")
    brain_path = (
        root.parent / f"02_Brain/reports/generated/armindex/phase-{source_phase_id}.md"
    ).resolve()
    paper_path = (root.parent / "03_Paper/publications/isai-nlp-2026/generated/publication-readiness.md").resolve()
    if brain_path not in external_outputs or paper_path not in external_outputs:
        raise ValueError("ArmIndex external projection lifecycle is incomplete")
    read_model_sha256 = str(model["read_model_sha256"])
    return {
        "source_receipt_uri": source_uri,
        "source_receipt_sha256": source_sha256,
        "projection_events": {
            "mlflow_safe_mirror": {
                "status": "mirrored",
                "artifact_uri": "mlflow/generated/archive-index.v2.json",
                "artifact_sha256": sha256(archive_text.encode("utf-8")),
            },
            "read_model_rebuild": {
                "status": "projected",
                "artifact_uri": "projections/read-model/read-model.v2.json",
                "artifact_sha256": read_model_sha256,
            },
            "brain_projection": {
                "status": "projected",
                "artifact_uri": f"../02_Brain/reports/generated/armindex/phase-{source_phase_id}.md",
                "artifact_sha256": sha256(external_outputs[brain_path].encode("utf-8")),
            },
            "obsidian_report": {
                "status": "projected",
                "artifact_uri": "obsidian_report/00_System/Generated/generated-manifest.json",
                "artifact_sha256": obsidian_manifest_sha256,
            },
            "dashboard_projection": {
                "status": "projected",
                "artifact_uri": "projections/read-model/read-model.v2.json",
                "artifact_sha256": read_model_sha256,
            },
            "paper_readiness": {
                "status": "projected",
                "artifact_uri": "../03_Paper/publications/isai-nlp-2026/generated/publication-readiness.md",
                "artifact_sha256": sha256(external_outputs[paper_path].encode("utf-8")),
            },
        },
    }


def _projection_identity_fingerprint(**bindings: str) -> str:
    required = {
        "archive_sha256",
        "config_sha256",
        "dataset_lineage_sha256",
        "environment_sha256",
        "evaluator_sha256",
        "metric_registry_sha256",
        "read_model_revision",
        "read_model_sha256",
        "rule_registry_sha256",
        "schema_registry_sha256",
    }
    if set(bindings) != required or any(not value for value in bindings.values()):
        raise ValueError("projection identity bindings are incomplete")
    return sha256(canonical_json(dict(sorted(bindings.items()))))


def _sync_mlflow_projection(
    root: Path,
    model: Mapping[str, Any],
    *,
    store_root: Path | None = None,
) -> str:
    """Archive the exact in-memory projection revision before other writers run."""

    vault_contents = _obsidian_vault_contents(root, model)
    _validate_generated_contents(vault_contents)
    manifest = _generated_manifest(model, vault_contents)
    archive_index = {
        **_mlflow_archive_index(model),
        "dashboard_snapshot_sha256": model["read_model_sha256"],
        "obsidian_manifest_sha256": manifest["manifest_sha256"],
    }
    schema_path = root / "schemas/read-model.v2.json"
    campaign_path = root / "control/campaigns/scope-autoindex-v1.yaml"
    envelope_path = root / "control/execution-envelope.yaml"
    p2_source = model.get("p2_readiness", {}).get("source", {})
    p2_envelope_path = root / str(p2_source.get("execution_envelope", ""))
    p2_profile_path = root / str(p2_source.get("profile", ""))
    evaluator_path = root / "src/myis_research/report_cli.py"
    environment_path = root / "uv.lock"
    for path in (schema_path, campaign_path, envelope_path, p2_envelope_path, p2_profile_path, evaluator_path, environment_path):
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"MLflow projection source is missing or unsafe: {path.relative_to(root)}")

    schema_registry = RegistrySnapshot(
        schema_version=SCHEMA_REGISTRY_SCHEMA,
        registry_kind="schema",
        items=tuple(
            [{"id": "read-model.v2", "sha256": sha256(schema_path.read_bytes())}]
            + [
                {"id": path.stem, "sha256": sha256(path.read_bytes())}
                for path in sorted((root / "schemas").glob("p2-*.json"))
                if path.is_file() and not path.is_symlink()
            ]
        ),
    )
    rule_registry = RegistrySnapshot(
        schema_version=RULE_REGISTRY_SCHEMA,
        registry_kind="rule",
        items=(
            {"id": "scope-autoindex-v1", "sha256": sha256(campaign_path.read_bytes())},
            {"id": "execution-envelope", "sha256": sha256(envelope_path.read_bytes())},
            {"id": "execution-envelope-p2", "sha256": sha256(p2_envelope_path.read_bytes())},
            {"id": "p2-budget-profile", "sha256": sha256(p2_profile_path.read_bytes())},
        ),
    )
    no_metric_registry: dict[str, Any] = {
        "schema_version": "myis.metric-registry.v2",
        "definitions": [],
    }
    no_metric_registry["registry_sha256"] = sha256(canonical_json(no_metric_registry))
    evaluator_sha = sha256(evaluator_path.read_bytes())
    archive_text = _json_text(archive_index)
    config_sha = sha256(campaign_path.read_bytes())
    environment_sha = sha256(environment_path.read_bytes())
    dataset_lineage_sha = sha256(canonical_json(model.get("datasets", [])))
    projection_fingerprint = _projection_identity_fingerprint(
        archive_sha256=sha256(archive_text.encode("utf-8")),
        config_sha256=config_sha,
        dataset_lineage_sha256=dataset_lineage_sha,
        environment_sha256=environment_sha,
        evaluator_sha256=evaluator_sha,
        metric_registry_sha256=str(no_metric_registry["registry_sha256"]),
        read_model_revision=str(model["read_model_revision"]),
        read_model_sha256=str(model["read_model_sha256"]),
        rule_registry_sha256=str(rule_registry.as_dict()["registry_sha256"]),
        schema_registry_sha256=str(schema_registry.as_dict()["registry_sha256"]),
    )
    freeze = FreezeBundle(
        freeze_id=f"freeze-projection-v4-{projection_fingerprint[:20]}",
        campaign_id=ACTIVE_CAMPAIGN,
        phase_id="P0_FOUNDATION",
        scope="projection_sync",
        status="frozen_development",
        source_commit=str(model["source_commit"]),
        rules_sha256=str(rule_registry.as_dict()["registry_sha256"]),
        metric_registry_sha256=str(no_metric_registry["registry_sha256"]),
        schema_registry_sha256=str(schema_registry.as_dict()["registry_sha256"]),
        evaluator_sha256=evaluator_sha,
        protocol_sha256=sha256(campaign_path.read_bytes()),
        environment_lock_sha256=environment_sha,
    )
    run = ArchiveRun(
        run_id=f"projection-sync-v4-{projection_fingerprint[:20]}",
        phase_id="P0_FOUNDATION",
        task_id="P0.3",
        run_kind="projection_sync",
        git_commit=str(model["source_commit"]),
        manifest_sha256=str(model["read_model_sha256"]),
        receipt_sha256=sha256(archive_text.encode("utf-8")),
        dataset_lineage_sha256=dataset_lineage_sha,
        config_sha256=config_sha,
        evaluator_sha256=evaluator_sha,
        environment_sha256=environment_sha,
        read_model_revision=str(model["read_model_revision"]),
        read_model_sha256=str(model["read_model_sha256"]),
        evidence_maturity="non_scientific",
        run_validity="valid",
        freeze=freeze,
        metrics={},
        safe_to_present=True,
    )
    archive = MLflowEvidenceArchive(default_mlflow_store(store_root))
    receipt = archive.sync(
        run,
        archive_index=archive_index,
        schema_registry=schema_registry,
        rule_registry=rule_registry,
    )
    if receipt.status not in {"synced", "already_synced"} or not receipt.mlflow_run_id:
        raise RuntimeError(f"MLflow projection archive failed: {receipt.status}")
    return receipt.mlflow_run_id


def _p1_measured(model: Mapping[str, Any]) -> bool:
    return model.get("project", {}).get("state") == "P1_CPU_MEASURED_COMPLETE"


def _p2_readiness(model: Mapping[str, Any]) -> Mapping[str, Any]:
    value = model.get("p2_readiness", {})
    return value if isinstance(value, Mapping) else {}


def _p2_official_review(model: Mapping[str, Any]) -> Mapping[str, Any]:
    value = _p2_readiness(model).get("official_review", {})
    return value if isinstance(value, Mapping) else {}


def _p2_fixture(model: Mapping[str, Any]) -> Mapping[str, Any]:
    value = _p2_readiness(model).get("fixture_pilot", {})
    return value if isinstance(value, Mapping) else {}


def _p2_measured(model: Mapping[str, Any]) -> bool:
    return bool(_p2_readiness(model).get("measured"))


def _p2_readiness_table(model: Mapping[str, Any]) -> str:
    p2 = _p2_readiness(model)
    budget = p2.get("candidate_budget", {}) if isinstance(p2.get("candidate_budget"), Mapping) else {}
    runtime = p2.get("runtime", {}) if isinstance(p2.get("runtime"), Mapping) else {}
    freeze = p2.get("freeze_barrier", {}) if isinstance(p2.get("freeze_barrier"), Mapping) else {}
    resources = p2.get("resources", {}) if isinstance(p2.get("resources"), Mapping) else {}
    review = _p2_official_review(model)
    fixture = _p2_fixture(model)
    proposal = p2.get("candidate_proposal", {}) if isinstance(p2.get("candidate_proposal"), Mapping) else {}
    review_value = (
        f"Round {review.get('final_round')} {review.get('final_verdict')} / {review.get('status')}"
        if review.get("final_round") is not None
        else review.get("status", "not_recorded")
    )
    rows = [
        ("Status", p2.get("status", "unknown")),
        ("Owner-local preflight", p2.get("preflight_status", "not_started")),
        (
            "Candidate proposal",
            f"{proposal.get('status', 'not_created')} / {proposal.get('adoption', 'not_adopted')}; "
            f"{proposal.get('frozen_controls', 0)} controls + {proposal.get('preregistered_candidates', 0)} candidates; "
            f"registered {proposal.get('registered_candidates', 0)}, hash-locked {proposal.get('hash_locked_candidates', 0)}",
        ),
        ("Official static review", review_value),
        (
            "Fixture pilot",
            f"{fixture.get('status', 'not_executed')} / {fixture.get('evidence_class', 'fixture')} / "
            f"scientific authority {fixture.get('scientific_authority', False)}",
        ),
        (
            "Synthetic lifecycle",
            f"{fixture.get('synthetic_candidates', 0)} candidates; "
            f"{fixture.get('synthetic_iterations', 0)} iterations; "
            f"shortlist {fixture.get('synthetic_shortlist', 0)}; "
            f"fixture selection {fixture.get('fixture_selection_exposures', 0)}",
        ),
        ("Profile", f"{p2.get('budget_profile_id', '-')} / {p2.get('budget_profile_sha256', '-') }"),
        ("Real candidates", f"{p2.get('candidate_count', 0)} / {budget.get('max_candidates_total', '-')}"),
        ("Real shortlist", f"{p2.get('shortlist_count', 0)} / {budget.get('max_selection_finalists', '-')}"),
        ("Runtime", f"{runtime.get('max_wall_clock_seconds', '-')} wall seconds; {runtime.get('per_candidate_timeout_seconds', '-')} per candidate"),
        ("Real freeze / selection", f"{freeze.get('status', 'not_started')}; {p2.get('selection_accesses', 0)}/{budget.get('selection_exposure_limit', 1)}"),
        ("Protected access", fixture.get("protected_data_accessed", False)),
        ("Scientific claim", fixture.get("claim_boundary", "no_measured_claim")),
        ("Resources", f"GPU {resources.get('gpu_budget_usd', 0)} USD; paid API {resources.get('paid_api_budget_usd', 0)} USD; model download {resources.get('network_model_download', False)}"),
        ("Next step", "Owner review of preflight and candidate-freeze proposal" if p2.get("preflight_status") == "passed_pending_owner" else "Owner-local measured preflight" if fixture.get("status") == "passed" else "Repository-only fixture pilot"),
    ]
    return "\n".join(["| Check | Value |", "|---|---|"] + [f"| {label} | {value} |" for label, value in rows])


def _p2_phase_body(model: Mapping[str, Any], phase: Mapping[str, Any], revision: str) -> str:
    p2 = _p2_readiness(model)
    review = _p2_official_review(model)
    fixture = _p2_fixture(model)
    proposal = p2.get("candidate_proposal", {}) if isinstance(p2.get("candidate_proposal"), Mapping) else {}
    return (
        "# P2_SCOPE_DEVELOPMENT\n\n"
        "P2 คือช่วงพัฒนา R1 SCOPE/AutoIndex แบบ reversible และ CPU-only. ตอนนี้เป็น readiness/planned เท่านั้น ยังไม่มี measured P2 run.\n\n"
        "## Status for Owner\n\n"
        f"**{p2.get('status', 'unknown')}**. P1 remains `P1_CPU_MEASURED_COMPLETE`; P3 and P4 remain locked.\n\n"
        f"Owner-local preflight state is **{p2.get('preflight_status', 'not_started')}**; it does not change measured counters (runs `{p2.get('measured_runs', 0)}`, candidates `{p2.get('candidate_count', 0)}`, selection accesses `{p2.get('selection_accesses', 0)}`).\n\n"
        f"The repository-safe candidate proposal is **{proposal.get('status', 'not_created')} / {proposal.get('adoption', 'not_adopted')}** with `{proposal.get('frozen_controls', 0)}` controls and `{proposal.get('preregistered_candidates', 0)}` preregistered candidates; registered count is `{proposal.get('registered_candidates', 0)}` and hash-locked count is `{proposal.get('hash_locked_candidates', 0)}`.\n\n"
        "## Official static review\n\n"
        f"Round `{review.get('final_round', '-')}` verdict is **{review.get('final_verdict', 'not_recorded')}** with status `{review.get('status', 'not_recorded')}`. This static review remains engineering provenance only. See [[P2_OFFICIAL_REVIEW_AUDIT]].\n\n"
        "## Repository-only fixture pilot\n\n"
        f"Fixture status is **{fixture.get('status', 'not_executed')}** with evidence class `{fixture.get('evidence_class', 'fixture')}` and scientific authority `{fixture.get('scientific_authority', False)}`. Synthetic lifecycle counts are kept separate from real campaign counters. See [[P2_FIXTURE_PILOT]].\n\n"
        "## Budget and runtime\n\n"
        f"{_p2_readiness_table(model)}\n\n"
        "## Why these methods\n\n"
        "`R0` uses one full TAC document per patent family and BM25 to isolate the representation question with a transparent lexical comparator; the DAPFAM protocol and patent-retrieval context are references U011 and U006 in [[LITERATURE_INDEX]]. `R0-W` keeps BM25 and family-level evaluation fixed but splits text into non-overlapping 512-token windows and uses family MaxP, testing whether passage granularity changes exposure (U154). `R1` is the planned patent-native SCOPE/AutoIndex representation-program search, evaluated with the same retriever/evaluator so any gain can be attributed to representation rather than a new dense model (U154 on the DAPFAM protocol U011). No dense model, LLM, paid API, or provider is part of this P2 arm.\n\n"
        "## Internal freeze barrier\n\n"
        "Baseline reproduction, candidate generation, and train evaluation must pass before the immutable shortlist receipt. Selection may open once, only for that frozen shortlist. Ties reject; any baseline, train, or freeze validation failure stops before selection.\n\n"
        "## Outputs and evidence\n\n"
        "The canonical profile, P2 execution envelope, request schema, candidate ledger, freeze receipt, selection receipt, manifest, and package schemas are the source surfaces. No fixture or dashboard preview is scientific evidence.\n\n"
        "## What is measured\n\n"
        "Not measured. Current P2 measured runs = `0`; selection accesses = `0`; GPU, paid API, network model download, and provider fallback = disabled.\n\n"
        f"## Read-model binding\n\nRevision: `{revision}`\n\n"
        "## Next action\n\nThe static contract and repository-only fixture are complete. The next authorized action is Owner-local measured preflight; measured P2 and real selection remain closed until that separate action begins.\n\n"
        "Links: [[P2.1]] · [[P2_SCOPE_DEVELOPMENT_RESULT]] · [[P2_OFFICIAL_REVIEW_AUDIT]] · [[P1_CPU_BASELINE_RESULT]]\n"
    )


def _p2_task_body(model: Mapping[str, Any], task: Mapping[str, Any]) -> str:
    p2 = _p2_readiness(model)
    review = _p2_official_review(model)
    fixture = _p2_fixture(model)
    proposal = p2.get("candidate_proposal", {}) if isinstance(p2.get("candidate_proposal"), Mapping) else {}
    return (
        f"# {task.get('task_id')}: {task.get('title')}\n\n"
        "## Objective\n\n"
        "Prepare a deterministic R1 representation search while keeping the retriever and evaluator fixed.\n\n"
        f"## Status\n\n**{p2.get('status', task.get('status', 'planned'))}**; this is not a measured result.\n\n"
        f"Owner-local preflight state: **{p2.get('preflight_status', 'not_started')}**.\n\n"
        f"Candidate proposal: **{proposal.get('status', 'not_created')} / {proposal.get('adoption', 'not_adopted')}**; `{proposal.get('frozen_controls', 0)}` controls + `{proposal.get('preregistered_candidates', 0)}` candidates, with no registered or hash-locked measured candidate.\n\n"
        "## Required contract\n\n"
        "Every measured request binds `budget_profile_id` and `budget_profile_sha256`. Baseline reproduction must pass before the one-run hard barrier freezes candidate IDs, SCOPE/spec, compiler, config, retriever, evaluator, and budget hashes before selection.\n\n"
        "## Current output\n\n"
        f"{_p2_readiness_table(model)}\n\n"
        "## Official review evidence\n\n"
        f"The bounded static review ended at Round `{review.get('final_round', '-')}` with verdict **{review.get('final_verdict', 'not_recorded')}**. The later repository-only fixture status is `{fixture.get('status', 'not_executed')}` and remains separate from the static review. See [[P2_OFFICIAL_REVIEW_AUDIT]] and [[P2_FIXTURE_PILOT]].\n\n"
        "## Method rationale and papers\n\n"
        "- `R0` is the simple full-family BM25 comparator: it answers how far a clear lexical baseline can go (U006, U011; see [[LITERATURE_INDEX]]).\n"
        "- `R0-W` changes only the text unit: 512-token windows plus family MaxP, so the comparison isolates passage granularity (U154; see [[LITERATURE_INDEX]]).\n"
        "- `R1` searches patent-native representation programs in the AutoIndex style while keeping retrieval/evaluation fixed; this is a planned development arm, not a measured claim yet (U154, U011; see [[LITERATURE_INDEX]]).\n\n"
        "## Protected boundary\n\n"
        "No protected qrels, query identifiers, split membership, per-query outcomes, credentials, raw provider payloads, GPU, paid API, or network model download.\n\n"
        "## Next action\n\nOwner-local measured preflight is the next authorized action. Do not open measured execution or real selection automatically.\n\n"
        "Links: [[P2_SCOPE_DEVELOPMENT_MASTER_REPORT]] · [[P2_SCOPE_DEVELOPMENT_RESULT]] · [[P2_OFFICIAL_REVIEW_AUDIT]] · [[LITERATURE_INDEX]]\n"
    )


def _p2_result_body(model: Mapping[str, Any]) -> str:
    p2 = _p2_readiness(model)
    review = _p2_official_review(model)
    fixture = _p2_fixture(model)
    source = p2.get("source", {}) if isinstance(p2.get("source"), Mapping) else {}
    return (
        "# P2 SCOPE Development Result\n\n"
        "## Result\n\n"
        "P2 is ready/planned but not measured. This note deliberately contains no scientific metric.\n\n"
        f"Owner-local preflight state is **{p2.get('preflight_status', 'not_started')}** and remains separate from measured execution.\n\n"
        f"{_p2_readiness_table(model)}\n\n"
        "## Fixture evidence\n\n"
        f"The repository-only synthetic fixture is `{fixture.get('status', 'not_executed')}`. It exercised `{fixture.get('synthetic_candidates', 0)}` synthetic candidates across `{fixture.get('synthetic_iterations', 0)}` adaptive iterations, froze `{fixture.get('synthetic_shortlist', 0)}` synthetic finalists, and used `{fixture.get('fixture_selection_exposures', 0)}` fixture-only selection exposure. This is engineering evidence, not retrieval-quality evidence.\n\n"
        "## Method rationale and references\n\n"
        "The baseline family BM25 arm (`R0`) establishes a transparent comparator (U006, U011; see [[LITERATURE_INDEX]]). The 512-token window/MaxP arm (`R0-W`) tests passage granularity without changing the evaluator (U154). The planned R1 arm follows AutoIndex-style representation-program search and keeps the same retrieval/evaluation boundary so the scientific contrast is representation, not provider or model substitution (U154, U011).\n\n"
        "## Interpretation boundary\n\n"
        "Readiness proves that the execution contract is explicit; it does not prove that R1 improves retrieval. A budget stop or no-improvement stop is a valid negative development outcome.\n\n"
        "## Official review boundary\n\n"
        f"Round `{review.get('final_round', '-')}` is **{review.get('final_verdict', 'not_recorded')}** for static contract safety. Evidence class is `{review.get('evidence_class', 'static_contract_review')}` and the claim boundary is `{review.get('claim_boundary', 'engineering_provenance_only')}`. See [[P2_OFFICIAL_REVIEW_AUDIT]].\n\n"
        "## Freeze rule\n\n"
        "Baseline reproduction, train evaluation, and freeze validation must pass before selection. Selection is unavailable until a validated immutable shortlist-freeze receipt exists, and it may be exposed only once. Final-872 remains closed.\n\n"
        "## Canonical sources\n\n"
        f"[[P2_SCOPE_DEVELOPMENT_MASTER_REPORT]] · `{source.get('profile', '-')}` · `{source.get('execution_envelope', '-')}`\n\n"
        f"Claim boundary: `{p2.get('claim_boundary', 'no_measured_claim')}`\n"
    )


def _p2_fixture_body(model: Mapping[str, Any]) -> str:
    fixture = _p2_fixture(model)
    return (
        "# P2 Fixture Pilot / รายงาน fixture สังเคราะห์\n\n"
        "## สถานะตอนนี้\n\n"
        f"Phase `P2_SCOPE_DEVELOPMENT`, Task `P2.1`: fixture status **{fixture.get('status', 'not_executed')}**. หลักฐานชั้นนี้คือ `{fixture.get('evidence_class', 'fixture')}` และไม่มีอำนาจรองรับข้ออ้างทางวิทยาศาสตร์ (`scientific_authority = {fixture.get('scientific_authority', False)}`).\n\n"
        "## สิ่งที่ทำแล้ว\n\n"
        f"ทดสอบ lifecycle แบบสังเคราะห์ครบ `{fixture.get('synthetic_candidates', 0)}` candidates, `{fixture.get('synthetic_iterations', 0)}` adaptive iterations, shortlist `{fixture.get('synthetic_shortlist', 0)}` รายการ และ fixture-only selection exposure `{fixture.get('fixture_selection_exposures', 0)}` ครั้ง. Deterministic rerun = `{fixture.get('deterministic_rerun', 'not_run')}`; negative checks = `{fixture.get('negative_checks_passed', False)}`.\n\n"
        "## สิ่งที่ไม่ได้ใช้\n\n"
        f"Protected data accessed = `{fixture.get('protected_data_accessed', False)}` และ measured execution performed = `{fixture.get('measured_execution_performed', False)}`. ไม่ได้เปิด protected store, real selection, final-872, D2 หรือ D3.\n\n"
        "## หลักฐานและ hash\n\n"
        f"- Fixture receipt: `{fixture.get('receipt_uri')}` / `{fixture.get('receipt_sha256')}`\n"
        f"- Execution manifest: `{fixture.get('execution_manifest_uri')}` / `{fixture.get('execution_manifest_sha256')}`\n"
        f"- Fixture package SHA-256: `{fixture.get('fixture_package_sha256')}`\n\n"
        "## ความหมายของผล\n\n"
        "ผลนี้ยืนยันเชิงวิศวกรรมว่า accepted P2 lifecycle ทำงานสอดคล้องกันบน synthetic inputs เท่านั้น ไม่ได้วัด retrieval quality, ไม่ได้สร้าง measured candidate และไม่อนุญาต measured P2 หรือ selection.\n\n"
        "## สิ่งที่ Owner ต้องทำ\n\n"
        "ขั้นถัดไปที่ได้รับอนุญาตคือ `Owner-local measured preflight` และต้องเริ่มเป็นงานแยกต่างหาก.\n\n"
        "## ขอบเขตที่ยังไม่แตะ\n\n"
        "Real candidates `0 / 32`, real shortlist `0 / 4`, real selection `0 / 1`; final evaluation และ scientific claims ยังปิดอยู่.\n\n"
        "Links: [[P2_SCOPE_DEVELOPMENT_MASTER_REPORT]] · [[P2.1]] · [[P2_SCOPE_DEVELOPMENT_RESULT]] · [[P2_OFFICIAL_REVIEW_AUDIT]]\n"
    )


def _p2_official_review_body(model: Mapping[str, Any]) -> str:
    review = _p2_official_review(model)
    source = review.get("source", {}) if isinstance(review.get("source"), Mapping) else {}
    round_lines = ["| รอบ | Verdict | Commit ที่ตรวจ | Result SHA-256 |", "|---:|---|---|---|"]
    for item in review.get("rounds", []):
        if not isinstance(item, Mapping):
            continue
        round_lines.append(
            f"| {item.get('round')} | `{item.get('verdict')}` | `{item.get('reviewed_commit')}` | `{item.get('result_sha256')}` |"
        )
    return (
        "# P2 Official Review Audit\n\n"
        "## สถานะตอนนี้\n\n"
        f"Official static review จบที่ Round `{review.get('final_round', '-')}` ด้วย verdict **{review.get('final_verdict', 'not_recorded')}**. สถานะ projection คือ `{review.get('status', 'not_recorded')}` และหลักฐานเป็น engineering provenance เท่านั้น ไม่ใช่ผลการทดลองทางวิทยาศาสตร์\n\n"
        "## สิ่งที่ทำแล้ว\n\n"
        + "\n".join(round_lines)
        + "\n\n"
        f"Audit index: `{source.get('index_uri', '-')}` (`{source.get('index_sha256', '-')}`)\n\n"
        f"Checksum manifest: `{source.get('checksums_uri', '-')}` (`{source.get('checksums_sha256', '-')}`)\n\n"
        "ทุก round เป็น read-only static inspection; provider/model provenance ถูกเก็บแบบ sanitized และไม่มี credential หรือ raw runtime payload ใน projection นี้\n\n"
        "## ความหมายของ accept\n\n"
        "ผล accept ยืนยันว่า contract guards ที่อนุญาตให้อ่านผ่านการตรวจแบบ static รองรับ repository-only fixture pilot ได้ ไม่ได้ยืนยันว่า R1 ทำให้ Recall@100 ดีขึ้น และไม่ได้สร้าง measured P2 result\n\n"
        "## สิ่งที่ Owner ต้องทำ\n\n"
        "ไม่มี Owner decision ใหม่สำหรับการบันทึก audit นี้ ส่วน `D2_OPEN_FINAL` และ `D3_SUBMIT_RELEASE` ยังรอ Owner ตามเดิม\n\n"
        "## สิ่งที่จะขอจาก Owner\n\n"
        "ไม่มีคำขอเปิด protected data, GPU, paid API หรือ provider fallback ขั้นถัดไปที่ย้อนกลับได้คือ repository-only fixture pilot แยกต่างหาก\n\n"
        "## ทรัพยากร Phase ถัดไป\n\n"
        "CPU-only, ค่า API 0 USD, GPU 0 USD, ไม่มี network model download และยังไม่เปิด selection\n\n"
        "## ขอบเขตที่ยังไม่แตะ\n\n"
        f"fixture pilot executed = `{review.get('fixture_pilot_executed', False)}`; protected data accessed = `{review.get('protected_data_accessed', False)}`; measured execution performed = `{review.get('measured_execution_performed', False)}`. Final-872, qrels, membership, query identifiers และ per-query outcomes ยังอยู่นอก projection\n\n"
        "Links: [[P2_SCOPE_DEVELOPMENT_MASTER_REPORT]] · [[P2.1]] · [[P2_SCOPE_DEVELOPMENT_RESULT]] · [[HOME]]\n"
    )


def _p1_run_ids(model: Mapping[str, Any]) -> list[str]:
    return sorted(str(row["run_id"]) for row in model.get("runs", []) if row.get("campaign_id") == "scope-autoindex-v1")


def _p1_manifest_hashes(model: Mapping[str, Any]) -> list[str]:
    return sorted(
        str(row["manifest_sha256"])
        for row in model.get("runs", [])
        if row.get("campaign_id") == "scope-autoindex-v1" and row.get("manifest_sha256")
    )


def _p1_metric_table(model: Mapping[str, Any], arm: str | None = None) -> str:
    split_order = {"train": 0, "selection": 1}
    scope_order = {"ALL": 0, "IN": 1, "OUT": 2}
    rows = [
        row for row in model.get("metrics", [])
        if isinstance(row, Mapping) and (arm is None or row.get("arm") == arm)
    ]
    rows.sort(key=lambda row: (
        str(row.get("arm", "")),
        split_order.get(str(row.get("split", "")), 9),
        scope_order.get(str(row.get("scope", "")), 9),
    ))
    if not rows:
        return "ยังไม่มี measured metric ที่ผ่าน package และ rigor review"
    lines = [
        "| Arm | Split | Scope | Metric | Value | n | Retrieved relevant | Relevant total |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        value = row.get("value")
        rendered = f"{float(value):.6f}" if isinstance(value, (int, float)) and not isinstance(value, bool) else "n/a"
        lines.append(
            f"| {row.get('arm')} | {row.get('split')} | {row.get('scope')} | "
            f"{row.get('name')} | {rendered} | {row.get('n')} | "
            f"{row.get('retrieved_relevant')} | {row.get('relevant_total')} |"
        )
    return "\n".join(lines) + "\n"


def _p1_comparison(model: Mapping[str, Any]) -> str:
    values = {
        str(row.get("arm")): float(row["value"])
        for row in model.get("metrics", [])
        if isinstance(row, Mapping)
        and row.get("split") == "selection"
        and row.get("scope") == "OUT"
        and isinstance(row.get("value"), (int, float))
        and not isinstance(row.get("value"), bool)
    }
    if set(values) != {"R0", "R0-W"}:
        return "ยังเปรียบเทียบ selection/OUT ไม่ได้ เพราะ evidence matrix ยังไม่สมบูรณ์"
    delta = values["R0-W"] - values["R0"]
    relation = "สูงกว่า" if delta > 0 else "ต่ำกว่า" if delta < 0 else "เท่ากัน"
    return (
        f"บน selection/OUT ค่า R0-W {relation} R0 โดย observed delta = `{delta:+.6f}`. "
        "นี่เป็น descriptive development evidence เท่านั้น ไม่ใช่ผลยืนยันเชิงสถิติและไม่ใช่ final-split claim"
    )


def _p1_dataset_table(model: Mapping[str, Any]) -> str:
    rows = [row for row in model.get("datasets", []) if isinstance(row, Mapping)]
    if not rows:
        return "ยังไม่มี dataset projection ที่ผ่าน validation"
    lines = ["| Dataset view | Representation | Safe aggregate counts |", "|---|---|---|"]
    for row in rows:
        counts = row.get("counts", {})
        count_text = ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) if isinstance(counts, Mapping) else "n/a"
        lines.append(f"| {row.get('dataset_id')} | {row.get('representation')} | {count_text or 'n/a'} |")
    return "\n".join(lines)


def _p1_evidence_table(model: Mapping[str, Any]) -> str:
    rows = [row for row in model.get("runs", []) if row.get("campaign_id") == "scope-autoindex-v1"]
    if not rows:
        return "ยังไม่มี canonical four-slot run matrix"
    lines = ["| Arm | Split | Run ID | Manifest SHA-256 |", "|---|---|---|---|"]
    for row in sorted(rows, key=lambda item: (str(item.get("arm")), str(item.get("stage")))):
        lines.append(f"| {row.get('arm')} | {row.get('stage')} | `{row.get('run_id')}` | `{row.get('manifest_sha256')}` |")
    evidence = {
        str(row.get("evidence_id")): row
        for row in model.get("evidence", [])
        if isinstance(row, Mapping)
    }
    for evidence_id in ("p1-four-slot-package", "p1-rigor-review", "mlflow-p1-registration"):
        row = evidence.get(evidence_id)
        if row:
            lines.append(f"\n- `{evidence_id}`: `{row.get('sha256')}` at `{row.get('uri')}`")
    return "\n".join(lines)


def _p1_execution_summary(model: Mapping[str, Any]) -> str:
    resources = model.get("resources", {})
    latency = resources.get("latency_seconds") if isinstance(resources, Mapping) else None
    if isinstance(latency, (int, float)) and not isinstance(latency, bool):
        elapsed = f"`{float(latency):.3f}` seconds (`{float(latency) / 3600:.2f}` hours)"
    else:
        elapsed = "not available"
    return (
        f"- Accepted measured run elapsed: {elapsed}.\n"
        "- The accepted source run predates the progress contract and records aggregate completion plus total latency only.\n"
        f"- The current runner shows a TTY progress bar and emits privacy-safe JSON heartbeats every "
        f"`{int(DEFAULT_HEARTBEAT_SECONDS)}` seconds for non-TTY execution.\n"
        "- Heartbeats contain only stage, processed/total, elapsed time, and bounded ETA; no item identifiers or outcomes are emitted."
    )


def _p1_home_body(model: Mapping[str, Any], next_lines: str) -> str:
    if not _p1_measured(model):
        latest = "No validated measured result is available. The retained aggregate receipt is historical-invalid and cannot be promoted."
        boundary = "P1 is not measured complete; final-872 cannot be claimed globally untouched."
    else:
        latest = (
            "P1 CPU baseline ผ่าน four-slot manifest, validation reports, package binding และ artifact-only rigor review "
            "สำหรับ train/selection แล้ว ดูรายละเอียดที่ [[P1_CPU_BASELINE_RESULT]]."
        )
        boundary = (
            "ผลนี้รองรับเฉพาะ development train/selection. ชุด final 872 ยังปิด และ historical exposure "
            "ทำให้ห้ามอ้างว่า final split ไม่เคยถูกแตะทั่วทั้งโครงการ"
        )
    return (
        "# myIS Research Report\n\n"
        "รายงานนี้สร้างจาก validated shared read model; การแก้มืออาจถูกแทนที่ ให้บันทึกความเห็นส่วนตัวใน Owner Note\n\n"
        "## Thesis\n\nCan a patent-native grounded representation compiler improve family-level DAPFAM retrieval while the retriever, evaluator, and budget remain fixed?\n\n"
        f"## สถานะตอนนี้\n\n- Phase: `{model['project']['current_phase']}`\n- Task: `{model['project']['current_task']}`\n- State: **{model['project']['state']}**\n\n"
        f"## สิ่งที่ทำแล้ว\n\n{latest}\n\n"
        f"## สิ่งที่ Owner ต้องทำ\n\n{next_lines}\n\n"
        f"## ขอบเขตที่ยังไม่แตะ\n\n{boundary}\n\n"
        "## Navigate\n\n- [[P0_FOUNDATION_MASTER_REPORT]]\n- [[P1_CPU_BASELINE_MASTER_REPORT]]\n- [[P1_CPU_BASELINE_RESULT]]\n- [[CURRENT_ADVISOR_UPDATE]]\n- [[LITERATURE_INDEX]]\n- [[RESEARCH_HISTORY_INDEX]]\n"
    )


def _p1_phase_body(model: Mapping[str, Any], phase: Mapping[str, Any], revision: str) -> str:
    measured = _p1_measured(model)
    status = "complete (measured train/selection)" if measured else "blocked with evidence"
    task_rows = "\n".join(
        f"| [[{task['task_id']}]] | {task['title']} | {_workflow_status(task['status'])} | {', '.join(task.get('evidence_ids', [])) or 'not measured'} |"
        for task in phase.get("tasks", [])
    )
    return (
        "# Phase 1: P1_CPU_BASELINE\n\n"
        "รายงาน Phase นี้แยกผล baseline แบบเอกสารเต็มและแบบ window ก่อนเริ่ม SCOPE development\n\n"
        f"## สถานะตอนนี้\n\n**{status}**. ใช้ standing authorization `D1_START_CAMPAIGN`; ไม่ได้ร้องขอหรือเปลี่ยน `D2_OPEN_FINAL` และ `D3_SUBMIT_RELEASE`\n\n"
        "## ขอบเขตและ protocol\n\n"
        "- Dataset: pinned DAPFAM revision; evaluation unit เป็น patent family\n"
        "- Query/corpus view: full TAC = title + abstract + claims; ไม่ใช้ description\n"
        "- R0: หนึ่งเอกสาร TAC ต่อ family\n"
        "- R0-W: window TAC แบบไม่ซ้อน 512 tokens และรวมผลด้วย family MaxP\n"
        "- Retriever: deterministic SQLite FTS5 BM25, OR query, top 100 unique families\n"
        "- Split ที่วัด: train 250 และ selection 125; final 872 ยังปิด\n"
        "- Compute: CPU-only, zero paid API, zero GPU, zero network model download\n\n"
        f"## Dataset projections\n\n{_p1_dataset_table(model)}\n\n"
        "## Task board\n\n| Task | Work | Status | Evidence |\n|---|---|---|---|\n"
        f"{task_rows}\n\n"
        f"## Execution progress / observability\n\n{_p1_execution_summary(model)}\n\n"
        f"## Measured results\n\n{_p1_metric_table(model)}\n\n"
        f"## Interpretation\n\n{_p1_comparison(model)}\n\n"
        "## Checks และ evidence chain\n\n"
        f"{_p1_evidence_table(model)}\n\n"
        "## สิ่งที่พูดได้\n\nผล Recall@100 ที่แสดงเป็น aggregate development evidence สำหรับ train/selection ภายใต้ protocol ที่ระบุ\n\n"
        "## สิ่งที่ยังพูดไม่ได้\n\nห้ามสรุป final performance, statistical superiority, legal novelty, infringement, validity หรือ freedom to operate จากผลนี้\n\n"
        "## สิ่งที่ Owner ต้องทำ\n\nไม่ต้องตัดสินใจ Gate เพื่อปิด P1. การเริ่ม P2 เป็น next automatic CPU-only action; D2/D3 ยังเป็น Owner-only\n\n"
        "## ขอบเขตที่ยังไม่แตะ\n\nFinal split content, protected labels, per-query outcomes, credentials, paid API, GPU และ provider payload ยังคงอยู่นอก projection\n\n"
        f"## Evidence revision\n\nRead-model revision: `{revision}`\n"
    )


def _p1_task_body(model: Mapping[str, Any], phase_id: str, task: Mapping[str, Any]) -> str:
    task_id = str(task["task_id"])
    measured = _p1_measured(model)
    arm = "R0" if task_id == "P1.1" else "R0-W" if task_id == "P1.2" else None
    if task_id == "P1.1":
        objective = "สร้าง flat BM25 baseline จาก full TAC หนึ่งเอกสารต่อ patent family และวัด train/selection"
        method = "one full TAC document per family; family-first ranking; top 100"
    elif task_id == "P1.2":
        objective = "สร้าง deterministic window baseline เพื่อทดสอบผลของการแบ่ง TAC โดยคง retriever และ evaluator เดิม"
        method = "non-overlapping 512-token TAC windows; exact family MaxP; top 100 unique families"
    else:
        objective = "ผูก measured run กับ request, aggregate receipt, four manifests, validation reports, package, rigor review และ MLflow mirror"
        method = "immutable aggregate-only evidence chain; protected run artifacts remain Owner-local"
    result = _p1_metric_table(model, arm=arm) if arm else _p1_metric_table(model)
    evidence = _p1_evidence_table(model) if measured else "evidence chain ยังไม่ครบ จึง fail closed"
    return (
        f"# {task_id}: {task['title']}\n\n"
        f"## Objective / hypothesis\n\n{objective}\n\n"
        f"## สถานะตอนนี้\n\n**{_workflow_status(task['status'])}**\n\n"
        "## Definition of Ready\n\nPinned source contract, clean execution commit, protected split commitment และ CPU execution envelope ต้องผ่าน\n\n"
        "## Definition of Done\n\nMeasured aggregate ต้อง reproducible สองรอบต่อ slot และผูกกับ canonical evidence chain โดยไม่มี blocker\n\n"
        f"## Inputs and method\n\n{method}\n\n"
        f"## Execution progress / observability\n\n{_p1_execution_summary(model)}\n\n"
        "## สิ่งที่ทำแล้ว\n\nImplementation ตรวจ source SHA-256, split cardinality, deterministic ranking, family deduplication และ aggregate-only output\n\n"
        f"## Result\n\n{result}\n\n"
        f"## Interpretation\n\n{_p1_comparison(model) if measured else 'ยังไม่มี measured interpretation ที่ promote ได้'}\n\n"
        "## Checks / blockers / failures\n\n"
        f"{'ไม่มี blocking finding ใน promoted package; historical receipt เดิมยังคงเป็น historical-invalid' if measured else 'four-slot package หรือ rigor review ยังไม่ผ่าน'}\n\n"
        f"## Evidence and MLflow links\n\n{evidence}\n\n"
        "## What this does not prove\n\nไม่พิสูจน์ final performance, statistical superiority หรือข้อสรุปทางกฎหมาย\n\n"
        f"## Dependencies\n\n[[{phase_id}_MASTER_REPORT]] และ [[P1_CPU_BASELINE_RESULT]]\n\n"
        "## Next action\n\nเมื่อ P1 complete ให้เปิดงาน P2 แบบ CPU-only โดยไม่แตะ D2\n\n"
        "## Owner notes\n\n[[80_Owner_Notes/README]]\n"
    )


def _p1_result_body(model: Mapping[str, Any]) -> str:
    result = model.get("results", [{}])[0]
    if not _p1_measured(model):
        return (
            "# P1 CPU Baseline Result\n\n## Output\n\nAggregate receipt เดิมถูกจัดเป็น historical-invalid และยัง promote ไม่ได้\n\n"
            f"## Result\n\nValidity: **{result.get('validity', 'blocked')}**. No validated measured value is available.\n\n"
            "## Interpretation\n\nNo measured claim is available while the hash-bound four-slot evidence matrix is missing.\n\n"
            "## What we must not say\n\nP1 is not measured complete and final-872 is not globally untouched.\n\n## Evidence\n\n[[P1.3]]\n"
        )
    return (
        "# P1 CPU Baseline Result\n\n"
        "## Output\n\nValidated aggregate results from four slots: R0/R0-W crossed with train/selection\n\n"
        f"## Result status\n\nValidity: **{result.get('validity')}**; maturity: **{result.get('evidence_maturity')}**; claim boundary: **{result.get('claim_boundary')}**\n\n"
        f"## Metric table\n\n{_p1_metric_table(model)}\n\n"
        f"## Comparison\n\n{_p1_comparison(model)}\n\n"
        f"## Resource result\n\nCPU-only: `{model['resources']['cpu_only']}`; GPU: `{model['resources']['gpu']}`; paid API: `{model['resources']['paid_api']}`; actual cost USD: `{model['resources']['actual_cost_usd']}`\n\n"
        f"## Execution progress / observability\n\n{_p1_execution_summary(model)}\n\n"
        f"## Rigor\n\nGrade: `{result.get('rigor_grade')}`; mean score: `{result.get('rigor_mean_score')}`; review SHA-256: `{result.get('rigor_review_sha256')}`\n\n"
        f"## Evidence and audit details\n\n{_p1_evidence_table(model)}\n\n"
        "## Interpretation boundary\n\nผลนี้ใช้วาง baseline สำหรับ P2 เท่านั้น Final 872 ยังปิด และไม่มี confirmatory/statistical claim\n\n"
        "## Links\n\n[[P1_CPU_BASELINE_MASTER_REPORT]] · [[P1.1]] · [[P1.2]] · [[P1.3]]\n"
    )


def _p1_advisor_body(model: Mapping[str, Any]) -> str:
    measured = _p1_measured(model)
    summary = (
        "P1 CPU baseline เสร็จด้วย measured train/selection evidence ครบ R0 และ R0-W; package ผ่าน structural validation และ artifact-only rigor review"
        if measured else
        "P1 ยัง blocked เพราะ four-slot package และ validation evidence ยังไม่ครบ"
    )
    measured_result = _p1_comparison(model) if measured else "ยังไม่มี validated measured result"
    return (
        "# Advisor Update\n\nGenerated draft; Owner edits belong in a separate immutable meeting note\n\n"
        f"## One-paragraph summary\n\n{summary}.\n\n"
        "## Plain-language primer\n\nR0 อ่าน TAC เต็มหนึ่งฉบับต่อ family; R0-W แบ่ง TAC เป็นช่วง 512 tokens แล้วเลือกคะแนนดีที่สุดของ family\n\n"
        "## Current Phase/Task\n\n[[P1_CPU_BASELINE_MASTER_REPORT]] และ [[P1.3]]\n\n"
        f"## Measured result\n\n{measured_result}\n\n"
        f"## Evidence ledger\n\n{_p1_evidence_table(model)}\n\n"
        "## Gate/decision\n\nD1 ครอบคลุม P1; D2 และ D3 ยังไม่ถูกเปิดหรือเปลี่ยนแปลง\n\n"
        "## What we can say\n\nรายงาน aggregate Recall@100 สำหรับ train/selection ภายใต้ fixed CPU protocol ได้\n\n"
        "## What we must not say\n\nยังอ้าง final performance, statistical superiority หรือ legal conclusion ไม่ได้\n\n"
        "## Recommended next action\n\nเริ่ม P2 SCOPE development แบบ CPU-only และ reversible; ขอ Owner เฉพาะเมื่อถึง D2 หรือจำเป็นต้องขยาย compute\n\n"
        "## Literature used\n\n[[LITERATURE_INDEX]]\n"
    )


def _structured_report_body(record: Mapping[str, Any], model: Mapping[str, Any]) -> str:
    """Render the canonical fifteen-section Phase/Task report contract."""

    def bullets(values: Any, fallback: str = "- None recorded.") -> str:
        if not isinstance(values, list) or not values:
            return fallback
        lines = []
        for value in values:
            if isinstance(value, Mapping):
                if value.get("failure_id"):
                    recovery = value.get("recovery_id", "no recovery recorded")
                    lines.append(
                        f"- `{value['failure_id']}` -> `{recovery}`; status "
                        f"`{value.get('status', 'unknown')}`; counters changed "
                        f"`{value.get('counters_changed', False)}`; failure "
                        f"`{value.get('failure_uri', 'not recorded')}` / `{value.get('failure_sha256')}`; "
                        f"recovery `{value.get('recovery_uri', 'not recorded')}` / `{value.get('recovery_sha256')}`"
                    )
                    continue
                claim = value.get("claim") or value.get("artifact_id") or value.get("failure_id") or value.get("uri") or value
                evidence = value.get("evidence")
                suffix = f" (evidence: {', '.join(map(str, evidence))})" if isinstance(evidence, list) and evidence else ""
                lines.append(f"- {claim}{suffix}")
            else:
                lines.append(f"- {value}")
        return "\n".join(lines)

    def binding_lines(value: Any) -> str:
        if not isinstance(value, Mapping):
            return "- None recorded."
        lines = []
        for key, item in value.items():
            if isinstance(item, Mapping):
                lines.append(f"- `{key}`: `{item.get('uri', 'inline')}`; SHA-256 `{item.get('sha256')}`")
            else:
                lines.append(f"- `{key}`: {item}")
        return "\n".join(lines) or "- None recorded."

    artifacts = record.get("artifact_references", [])
    artifact_rows = [
        "| Artifact | Type | Evidence | Safe URI | SHA-256 | Validation |",
        "|---|---|---|---|---|---|",
    ]
    for item in artifacts if isinstance(artifacts, list) else []:
        if not isinstance(item, Mapping):
            continue
        artifact_rows.append(
            f"| {item.get('title', item.get('artifact_id'))} | `{item.get('artifact_type')}` | `{item.get('evidence_class')}` | `{item.get('safe_uri')}` | `{item.get('content_sha256')}` | `{item.get('validation_status')}` |"
        )
    if len(artifact_rows) == 2:
        artifact_rows.append("| None | - | - | - | - | - |")

    metrics = record.get("metric_references", [])
    metric_rows = ["| Metric | Split | Scope | Value | n | Denominator | Evidence |", "|---|---|---|---:|---:|---|---|"]
    for metric in metrics if isinstance(metrics, list) else []:
        if not isinstance(metric, Mapping):
            continue
        metric_rows.append(
            f"| `{metric.get('name')}`@{metric.get('cutoff', 100)} | `{metric.get('split')}` | `{metric.get('scope')}` | `{metric.get('value')}` | `{metric.get('n')}` | `{metric.get('denominator')}` | `{record.get('evidence_class')}` |"
        )
    if len(metric_rows) == 2:
        metric_rows.append("| No measured metric is available | - | - | - | - | - | planned/fixture |")

    governance = record.get("governance_status", {})
    governance_lines = binding_lines(governance)
    result = record.get("result", {}) if isinstance(record.get("result"), Mapping) else {}
    phase_id = str(record.get("phase_id"))
    progress_note = (
        "\n### Execution progress / observability\n\n"
        "Aggregate progress is reported without item identifiers or outcomes. "
        "A future non-TTY measured runner must emit only stage, processed/total, elapsed time, and capped ETA."
        if phase_id == "P1_CPU_BASELINE" else ""
    )
    p2_note = ""
    if phase_id == "P2_SCOPE_DEVELOPMENT":
        p2 = model.get("p2_readiness", {}) if isinstance(model.get("p2_readiness"), Mapping) else {}
        fixture = p2.get("fixture_pilot", {}) if isinstance(p2.get("fixture_pilot"), Mapping) else {}
        review = p2.get("official_review", {}) if isinstance(p2.get("official_review"), Mapping) else {}
        p2_note = (
            f"\nStatic review: Round `{review.get('final_round', '-')}` verdict **{review.get('final_verdict', 'not_recorded')}**. "
            f"Repository-only fixture status **{fixture.get('status', 'not_executed')}**; synthetic lifecycle counts are "
            f"`{fixture.get('synthetic_candidates', 0)}` candidates, `{fixture.get('synthetic_iterations', 0)}` iterations, "
            f"`{fixture.get('synthetic_shortlist', 0)}` finalists, and `{fixture.get('fixture_selection_exposures', 0)}` fixture selection exposure(s)."
        )
    a1_note = ""
    if phase_id == "A1_BASELINES_AND_MULTI_ARM_SCREENING":
        armindex = model.get("armindex", {}) if isinstance(model.get("armindex"), Mapping) else {}
        adapter = armindex.get("adapter_fixture_validation", {}) if isinstance(armindex.get("adapter_fixture_validation"), Mapping) else {}
        gpu = adapter.get("gpu_spec", {}) if isinstance(adapter.get("gpu_spec"), Mapping) else {}
        timing = adapter.get("time_estimate", {}) if isinstance(adapter.get("time_estimate"), Mapping) else {}
        budget = adapter.get("budget_estimate", {}) if isinstance(adapter.get("budget_estimate"), Mapping) else {}
        owner_needs = adapter.get("owner_needs", []) if isinstance(adapter.get("owner_needs"), list) else []
        gpu_classes = ", ".join(str(item) for item in gpu.get("preferred_gpu_classes", []))
        owner_lines = "\n".join(f"- {item}" for item in owner_needs) or "- No Owner input is required for the completed CPU fixture."
        a1_note = (
            "\n\n### A1.2 resource planning boundary\n\n"
            f"The proposal remains `{adapter.get('gpu_proposal_status', 'not_available')}`. "
            f"It specifies `{gpu.get('gpu_count', 0)}` GPU with at least `{gpu.get('minimum_vram_gib', 0)}` GiB VRAM; "
            f"preferred classes are {gpu_classes or 'not recorded'}. A100/H100 required: `{gpu.get('a100_or_h100_required', False)}`. "
            f"The planning range is `{timing.get('gpu_reservation_hours_min', 0)}-{timing.get('gpu_reservation_hours_max', 0)}` GPU hours and "
            f"`{timing.get('end_to_end_elapsed_hours_min', 0)}-{timing.get('end_to_end_elapsed_hours_max', 0)}` elapsed hours. "
            f"Raw compute is estimated at USD `{budget.get('raw_gpu_compute_estimate_min', 0)}-{budget.get('raw_gpu_compute_estimate_max', 0)}`; "
            f"hard stops are USD `{budget.get('model_parity_and_pilot_hard_stop', 0)}` for parity/pilot, "
            f"USD `{budget.get('common_screen_hard_stop', 0)}` for the common screen, "
            f"USD `{budget.get('a1_total_hard_stop', 0)}` for A1, and USD `{budget.get('campaign_hard_stop', 0)}` for the campaign.\n\n"
            "Owner prerequisites:\n\n"
            f"{owner_lines}"
        )
    failures = record.get("failure_recovery_references", [])
    artifact_markdown = "\n".join(artifact_rows)
    metric_markdown = "\n".join(metric_rows)
    return (
        f"# {record.get('phase_id')}{(' / ' + str(record.get('task_id'))) if record.get('task_id') else ''}\n\n"
        "Generated from the validated report record. Manual edits may be replaced; use the separate Owner Notes area for personal annotations.\n\n"
        "## Objective\n\n"
        f"{record.get('objective')}\n\n"
        "## Starting State\n\n"
        f"{binding_lines(record.get('starting_state'))}\n\n"
        "## Inputs and Frozen Bindings\n\n"
        f"{binding_lines(record.get('input_bindings'))}\n\n"
        "## Work Performed\n\n"
        f"{record.get('work_summary')}{progress_note}{p2_note}{a1_note}\n\n"
        "## Artifacts Produced\n\n"
        "These references explain what each artifact is for; the bytes remain governed by canonical paths.\n\n"
        f"{artifact_markdown}\n\n"
        "## Metrics\n\n"
        f"{metric_markdown}\n\n"
        "Fixture values are synthetic engineering diagnostics and are never reported as measured performance.\n\n"
        "## Result\n\n"
        f"**Output:** {result.get('output', 'No output recorded.')}\n\n"
        f"**Result:** {result.get('result', 'No result recorded.')}\n\n"
        f"**Decision:** {result.get('decision', 'No decision recorded.')}\n\n"
        "## Interpretation\n\n"
        f"{record.get('interpretation')}\n\n"
        "## Supported Claims\n\n"
        f"{bullets(record.get('supported_claims'))}\n\n"
        "## Unsupported Claims\n\n"
        f"{bullets(record.get('unsupported_claims'))}\n\n"
        "## Failures and Recovery\n\n"
        f"{bullets(failures, '- No material failure is recorded for this Phase or Task.')}\n\n"
        "## Governance and Safety\n\n"
        f"{governance_lines}\n\n"
        "## Decision\n\n"
        f"Status: **{record.get('decision', {}).get('status', record.get('status'))}**. {record.get('decision', {}).get('reason', '')}\n\n"
        "## Next Action\n\n"
        f"{record.get('next_authorized_action')}\n\n"
        "Measured P2, real selection, and final evaluation must not start automatically from this report.\n\n"
        "## Evidence Links\n\n"
        f"{bullets(record.get('evidence_links'))}\n"
    )


def _obsidian_vault_contents(root: Path, model: Mapping[str, Any]) -> dict[Path, str]:
    revision = str(model["read_model_revision"])
    report_records = {str(item["report_id"]): item for item in build_report_records(root, model)}
    common = {
        "schema_version": "myis.obsidian-note.v2",
        "read_model_revision": revision,
        "read_model_sha256": model["read_model_sha256"],
        "source_commit": model["source_commit"],
        "projection_schema_version": model["projection_schema_version"],
        "source_run_ids": [],
        "source_manifest_sha256": [],
        "related_literature_ids": [],
        "related_decision_ids": ["D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"],
        "evidence_class": "engineering",
        "scientific_authority": False,
        "claim_boundary": "engineering_provenance_only",
        "generated_from_revision": revision,
        "last_material_update": model["generated_at"],
        "next_authorized_action": A0_8_NEXT_AUTHORIZED_ACTION,
        "managed_by": "myis-report",
        "edit_policy": "generated_do_not_edit",
        "safe_to_present": True,
        "created_at": model["generated_at"],
        "updated_at": model["generated_at"],
    }
    project = model["project"]
    inbox = model.get("owner_inbox", [])
    next_lines = "\n".join(f"- {item.get('label')}" for item in inbox) or "- ไม่มีรายการ"
    p1_run_ids = _p1_run_ids(model)
    p1_manifest_hashes = _p1_manifest_hashes(model)
    outputs: dict[Path, str] = {}
    outputs[VAULT_RELATIVE_PATH / "HOME.md"] = _note(
        {**common, "note_id": "HOME", "note_type": "home", "phase_id": project["current_phase"], "task_id": project["current_task"], "workflow_status": "blocked" if project["state"] == "P1_BLOCKED_WITH_EVIDENCE" else "complete", "evidence_maturity": "measured_selection" if _p1_measured(model) else "non_scientific", "claim_level": "descriptive" if _p1_measured(model) else "none", "source_run_ids": p1_run_ids, "source_manifest_sha256": p1_manifest_hashes},
        _p1_home_body(model, next_lines) + "\n\n## P2 Readiness\n\n" + _p2_readiness_table(model) + "\n\nP2 remains planned and not measured; selection access is zero.\n",
    )

    armindex = model.get("armindex", {}) if isinstance(model.get("armindex"), Mapping) else {}
    armindex_phases = [row for row in armindex.get("phases", []) if isinstance(row, Mapping)]
    arm_rows = "\n".join(
        f"| `{row.get('arm_id')}` | `{row.get('model_id')}` | {row.get('adapter_status')} | {row.get('representation_status')} | {row.get('commercial_status')} |"
        for row in armindex.get("arms", [])
        if isinstance(row, Mapping)
    )
    armindex_home = (
        "# ArmIndex Home\n\n"
        "ArmIndex is the active campaign. Historical SCOPE and P1 evidence remains readable but is not current ArmIndex evidence.\n\n"
        f"## Campaign and phase status\n\n- Campaign: `{armindex.get('campaign_id')}`\n- Phase: `{armindex.get('current_phase')}`\n- Status: `{armindex.get('status')}`\n\n"
        "## Retrieval arms\n\n| Arm | Model | Adapter | Representation | Commercial status |\n|---|---|---|---|---|\n"
        + arm_rows
        + "\n\n## Optimization status\n\n"
        f"- Transfer: `{armindex.get('transfer', {}).get('status', 'not_started')}`\n"
        f"- Complementarity: `{armindex.get('complementarity', {}).get('status', 'not_started')}`\n"
        f"- HarnessOpt: `{armindex.get('harnessopt', {}).get('status', 'not_started')}`\n"
        f"- Research champion: `{armindex.get('champions', {}).get('research')}`\n"
        f"- Commercial champion: `{armindex.get('champions', {}).get('commercial')}`\n\n"
        "## Integrity and gates\n\n"
        f"- Measured runs: `{armindex.get('counters', {}).get('measured_runs', 0)}`\n"
        f"- Selection exposures: `{armindex.get('counters', {}).get('selection_accesses', 0)}`\n"
        f"- Final exposures: `{armindex.get('counters', {}).get('final_accesses', 0)}`\n"
        "- D2 and D3 remain Owner-only.\n- Final remains closed.\n\n"
        f"## Next command\n\n`{armindex.get('next_command', '')}`\n\n"
        "## Historical evidence\n\n[[SCOPE_HISTORY_INDEX]] · [[P1_CPU_BASELINE_MASTER_REPORT]] · [[P2_SCOPE_DEVELOPMENT_MASTER_REPORT]]\n"
    )
    outputs[VAULT_RELATIVE_PATH / "00_Home/ARM_INDEX_HOME.md"] = _note(
        {**common, "note_id": "ARM-INDEX-HOME", "note_type": "home", "phase_id": armindex.get("current_phase"), "task_id": "A0.3", "workflow_status": "verification_needed", "evidence_maturity": "non_scientific", "claim_level": "none"},
        armindex_home,
    )
    outputs[VAULT_RELATIVE_PATH / "00_Home/MOC.md"] = _note(
        {**common, "note_id": "ARM-INDEX-MOC", "note_type": "home", "phase_id": armindex.get("current_phase"), "task_id": "A0.3", "workflow_status": "verification_needed", "evidence_maturity": "non_scientific", "claim_level": "none"},
        "# ArmIndex MOC\n\n- [[ARM_INDEX_HOME]]\n" + "\n".join(f"- [[{phase.get('phase_id')}_REPORT]]" for phase in armindex_phases) + "\n- [[ARMINDEX_MIGRATION_RESULT]]\n- [[SCOPE_HISTORY_INDEX]]\n- [[Decisions]]\n- [[Failed_Attempts]]\n",
    )
    for phase in armindex_phases:
        phase_id = str(phase["phase_id"])
        phase_folder = VAULT_RELATIVE_PATH / "01_Phases" / "ArmIndex" / phase_id
        phase_record = report_records.get(f"phase-{phase_id.lower()}")
        task_table = "\n".join(
            f"| [[{task.get('task_id')}]] | {task.get('title')} | {task.get('status')} |"
            for task in phase.get("tasks", [])
            if isinstance(task, Mapping)
        ) or "| none | none | planned |"
        fallback_body = (
            f"# {phase_id}\n\n"
            f"## Objective\n\n{phase.get('purpose')}\n\n"
            "## Starting State\n\nArmIndex measured counters are zero and historical SCOPE evidence is read-only.\n\n"
            "## Inputs and Frozen Bindings\n\n`control/campaigns/armindex-multiretriever-v2.yaml`, versioned ArmIndex schemas, and the shared read-model revision.\n\n"
            "## Work Performed\n\nThe generated projection records the canonical phase/task state; it performs no measurement.\n\n"
            "## Artifacts Produced\n\nGenerated phase and task reports with canonical source pointers.\n\n"
            "## Metrics\n\nNo ArmIndex scientific metric is available. Measured run count is `0`.\n\n"
            f"## Result\n\nStatus: **{phase.get('status')}**.\n\n"
            "## Interpretation\n\nThis is engineering migration state, not scientific evidence.\n\n"
            "## Supported Claims\n\nThe phase registry and migration boundary are implemented and inspectable.\n\n"
            "## Unsupported Claims\n\nNo retrieval gain, champion, production readiness, Selection, or Final claim.\n\n"
            "## Failures and Recovery\n\nNo active failure is projected; failures remain append-only when present.\n\n"
            "## Governance and Safety\n\nProtected data remains Owner-local; D2 and D3 are the only Owner gates.\n\n"
            "## Decision\n\nContinue automatically only within the canonical phase and budget contract.\n\n"
            f"## Next Action\n\n{armindex.get('next_command')}\n\n"
            "## Evidence Links\n\n[[ARM_INDEX_HOME]] · [[ARMINDEX_MIGRATION_RESULT]] · [[SCOPE_HISTORY_INDEX]]\n\n"
            "## Tasks\n\n| Task | Work | Status |\n|---|---|---|\n" + task_table + "\n"
        )
        body = (
            _structured_report_body(phase_record, model)
            if phase_record is not None
            else fallback_body
        )
        phase_evidence_class = (
            str(phase_record.get("evidence_class")) if phase_record else "engineering"
        )
        phase_maturity = (
            "fixture"
            if phase_evidence_class == "engineering_fixture"
            else "planned"
            if phase_evidence_class == "planning_estimate"
            else "non_scientific"
        )
        outputs[phase_folder / f"{phase_id}_REPORT.md"] = _note(
            {**common, "note_id": f"{phase_id}-MASTER", "note_type": "phase_report", "phase_id": phase_id, "task_id": None, "workflow_status": _workflow_status(str(phase_record.get("status"))) if phase_record else _workflow_status(str(phase.get('status'))), "evidence_class": phase_evidence_class, "evidence_maturity": phase_maturity, "scientific_authority": bool(phase_record.get("scientific_authority")) if phase_record else False, "claim_boundary": str(phase_record.get("claim_boundary")) if phase_record else "engineering_provenance_only", "claim_level": "none", "next_authorized_action": phase_record.get("next_authorized_action", common["next_authorized_action"]) if phase_record else common["next_authorized_action"]},
            body,
        )
        for task in phase.get("tasks", []):
            if not isinstance(task, Mapping):
                continue
            task_id = str(task["task_id"])
            task_record = report_records.get(f"task-{task_id.lower().replace('.', '-')}")
            task_body = (
                _structured_report_body(task_record, model)
                if task_record is not None
                else fallback_body.replace(f"# {phase_id}", f"# {task_id}: {task.get('title')}", 1).replace(f"Status: **{phase.get('status')}**", f"Status: **{task.get('status')}**", 1)
            )
            task_evidence_class = (
                str(task_record.get("evidence_class")) if task_record else "engineering"
            )
            task_maturity = (
                "fixture"
                if task_evidence_class == "engineering_fixture"
                else "planned"
                if task_evidence_class == "planning_estimate"
                else "non_scientific"
            )
            outputs[VAULT_RELATIVE_PATH / "02_Tasks" / "ArmIndex" / phase_id / f"{task_id}.md"] = _note(
                {**common, "note_id": task_id, "note_type": "task_report", "phase_id": phase_id, "task_id": task_id, "workflow_status": _workflow_status(str(task_record.get("status"))) if task_record else _workflow_status(str(task.get('status'))), "evidence_class": task_evidence_class, "evidence_maturity": task_maturity, "scientific_authority": bool(task_record.get("scientific_authority")) if task_record else False, "claim_boundary": str(task_record.get("claim_boundary")) if task_record else "engineering_provenance_only", "claim_level": "none", "next_authorized_action": task_record.get("next_authorized_action", common["next_authorized_action"]) if task_record else common["next_authorized_action"]},
                task_body,
            )
    outputs[VAULT_RELATIVE_PATH / "03_Results/Current/ARMINDEX_MIGRATION_RESULT.md"] = _note(
        {**common, "note_id": "ARMINDEX-MIGRATION-RESULT", "note_type": "result_report", "phase_id": "A0_MIGRATION_FOUNDATION", "task_id": "A0.3", "workflow_status": "verification_needed", "evidence_maturity": "non_scientific", "claim_level": "none", "result_id": "ARMINDEX-MIGRATION", "current_scientific_authority": False},
        "# ArmIndex Migration Result\n\nThe infrastructure migration is represented in the shared read model. ArmIndex measured runs, Selection exposures, and Final exposures remain zero. No champion or benchmark result exists.\n\n[[ARM_INDEX_HOME]]\n",
    )
    outputs[VAULT_RELATIVE_PATH / "05_Research_History/SCOPE/SCOPE_HISTORY_INDEX.md"] = _note(
        {**common, "note_id": "SCOPE-HISTORY-INDEX", "note_type": "history_report", "phase_id": "P2_SCOPE_DEVELOPMENT", "task_id": "P2.1", "workflow_status": "complete", "evidence_maturity": "historical_exposed", "claim_level": "descriptive"},
        "# Historical SCOPE Campaign\n\n`scope-autoindex-v1` is historical and read-only. Its P1 measured evidence and P2 engineering evidence retain their original paths, hashes, counters, and claim boundaries.\n\n[[P1_CPU_BASELINE_MASTER_REPORT]] · [[P2_SCOPE_DEVELOPMENT_MASTER_REPORT]] · [[P2_FIXTURE_PILOT]]\n",
    )

    for phase in model.get("phases", []):
        phase_id = str(phase["phase_id"])
        phase_folder = VAULT_RELATIVE_PATH / "01_Phases" / phase_id
        task_rows = "\n".join(
            f"| [[{task['task_id']}]] | {task['title']} | {_workflow_status(task['status'])} | {', '.join(task.get('evidence_ids', [])) or 'not measured'} |"
            for task in phase.get("tasks", [])
        ) or "| none | none | planned | none |"
        phase_record = report_records.get(f"phase-{phase_id.lower()}")
        phase_body = _structured_report_body(phase_record, model) if phase_record else (_p1_phase_body(model, phase, revision) if phase_id == "P1_CPU_BASELINE" else _p2_phase_body(model, phase, revision) if phase_id == "P2_SCOPE_DEVELOPMENT" else (
            f"# {phase_id}\n\nGenerated from validated evidence. Manual edits may be replaced. Add personal comments in the linked Owner Note.\n\n"
            "## Summary for Owner\n\nThis report is a narrative projection of the shared read model, not a source of scientific truth.\n\n"
            f"## Current status and gate\n\n**{_workflow_status(phase['status'])}**. D2 and D3 remain Owner-only.\n\n"
            "## Task board\n\n| Task | Work | Status | Evidence |\n|---|---|---|---|\n"
            f"{task_rows}\n\n## Output\n\nGenerated task records are available; no run output is promoted from historical-invalid evidence.\n\n"
            "## Measured results\n\n[[P1_CPU_BASELINE_RESULT]]\n\n"
            "## Interpretation\n\nNo scientific interpretation is promoted without validated evidence.\n\n"
            "## What we can say\n\nThe control plane records the evidence boundary and blocks promotion safely.\n\n"
            "## What we must not say yet\n\nNo P1 measured-complete, selection, or final-split claim.\n\n"
            "## Literature basis\n\n[[LITERATURE_INDEX]]\n\n"
            "## Decisions and RAID\n\n[[RAID]]\n\n"
            f"## Evidence and audit details\n\nRead-model revision: `{revision}`\n"
        ))
        outputs[phase_folder / f"{phase_id}_MASTER_REPORT.md"] = _note(
            {**common, "note_id": f"{phase_id}-MASTER", "note_type": "phase_report", "phase_id": phase_id, "task_id": None, "workflow_status": _workflow_status(phase["status"]), "evidence_maturity": "measured_selection" if phase_id == "P1_CPU_BASELINE" and _p1_measured(model) else "non_scientific" if phase_id == "P2_SCOPE_DEVELOPMENT" and not _p2_measured(model) else "non_scientific" if phase["status"] in {"blocked", "planned", "blocked_until_p1", "locked_until_D2", "locked_until_D3"} else "measured_development", "claim_level": "descriptive" if phase_id == "P1_CPU_BASELINE" and _p1_measured(model) else "none", "source_run_ids": p1_run_ids if phase_id == "P1_CPU_BASELINE" else [], "source_manifest_sha256": p1_manifest_hashes if phase_id == "P1_CPU_BASELINE" else [], "related_literature_ids": ["U006", "U011", "U154"] if phase_id == "P2_SCOPE_DEVELOPMENT" else common["related_literature_ids"]},
            phase_body,
        )
        for task in phase.get("tasks", []):
            task_id = str(task["task_id"])
            task_record = report_records.get(f"task-{task_id.lower().replace('.', '-')}")
            body = _structured_report_body(task_record, model) if task_record else (_p1_task_body(model, phase_id, task) if phase_id == "P1_CPU_BASELINE" else _p2_task_body(model, task) if phase_id == "P2_SCOPE_DEVELOPMENT" else (
                f"# {task_id}: {task['title']}\n\nGenerated from validated evidence. Manual edits may be replaced. Add personal comments in the linked Owner Note.\n\n"
                "## Objective / hypothesis\n\nDeliver the registry-defined task without crossing the protected-data boundary.\n\n"
                f"## Status\n\n**{_workflow_status(task['status'])}**\n\n"
                "## Definition of Ready\n\nCanonical control records and safe projection inputs are available.\n\n"
                "## Definition of Done\n\nRequires acceptance evidence in the canonical manifest/receipt chain; changing this note cannot complete the task.\n\n"
                "## Inputs and protocol boundary\n\nCPU-only, no protected payloads, qrels, membership, or per-query outcomes.\n\n"
                "## Work performed\n\nThe shared read model records current status.\n\n"
                "## Output\n\nOutput pointers come from the shared read model.\n\n"
                "## Result\n\nNo validated measured result is rendered.\n\n"
                "## Interpretation\n\nBlocked or pending review; no scientific inference follows.\n\n"
                "## What this does not prove\n\nIt does not prove a P1 metric, selection result, or final evaluation claim.\n\n"
                "## Checks / blockers / failures\n\nThe evidence matrix remains incomplete where the phase is blocked.\n\n"
                "## Evidence and MLflow links\n\nNo promoted MLflow run is linked.\n\n"
                "## Related literature\n\n[[LITERATURE_INDEX]]\n\n"
                f"## Dependencies\n\n[[{phase_id}_MASTER_REPORT]]\n\n"
                "## Next action\n\nFollow the Owner-inbox item in [[HOME]].\n\n"
                f"## Owner notes\n\n[[80_Owner_Notes/README]]\n"
            ))
            outputs[phase_folder / "Tasks" / f"{task_id}.md"] = _note(
                {**common, "note_id": task_id, "note_type": "task_report", "phase_id": phase_id, "task_id": task_id, "workflow_status": _workflow_status(task["status"]), "evidence_maturity": "measured_selection" if phase_id == "P1_CPU_BASELINE" and _p1_measured(model) else "non_scientific" if phase_id == "P2_SCOPE_DEVELOPMENT" and not _p2_measured(model) else "measured_development" if task.get("evidence_ids") else "non_scientific", "claim_level": "descriptive" if phase_id == "P1_CPU_BASELINE" and _p1_measured(model) else "none", "source_run_ids": p1_run_ids if phase_id == "P1_CPU_BASELINE" else [], "source_manifest_sha256": p1_manifest_hashes if phase_id == "P1_CPU_BASELINE" else [], "related_literature_ids": ["U006", "U011", "U154"] if phase_id == "P2_SCOPE_DEVELOPMENT" else common["related_literature_ids"]},
                body,
            )

    result = model.get("results", [{}])[0]
    outputs[VAULT_RELATIVE_PATH / "03_Results/Current/P1_CPU_BASELINE_RESULT.md"] = _note(
        {**common, "note_id": "P1-CPU-BASELINE-RESULT", "note_type": "result_report", "phase_id": "P1_CPU_BASELINE", "task_id": "P1.3", "workflow_status": "complete" if _p1_measured(model) else "blocked", "evidence_maturity": "measured_selection" if _p1_measured(model) else "historical_exposed", "claim_level": "descriptive" if _p1_measured(model) else "none", "result_id": result.get("result_id", "P1-CPU-BASELINE"), "current_scientific_authority": _p1_measured(model), "source_run_ids": p1_run_ids, "source_manifest_sha256": p1_manifest_hashes},
        _p1_result_body(model),
    )
    p2_result = next((item for item in model.get("results", []) if item.get("result_id") == "P2-SCOPE-DEVELOPMENT"), {})
    outputs[VAULT_RELATIVE_PATH / "03_Results/Current/P2_SCOPE_DEVELOPMENT_RESULT.md"] = _note(
        {**common, "note_id": "P2-SCOPE-DEVELOPMENT-RESULT", "note_type": "result_report", "phase_id": "P2_SCOPE_DEVELOPMENT", "task_id": "P2.1", "workflow_status": "complete" if _p2_measured(model) else "ready", "evidence_maturity": "measured_selection" if _p2_measured(model) else "non_scientific", "claim_level": "descriptive" if _p2_measured(model) else "none", "result_id": p2_result.get("result_id", "P2-SCOPE-DEVELOPMENT"), "current_scientific_authority": False, "source_run_ids": [], "source_manifest_sha256": [], "related_literature_ids": ["U006", "U011", "U154"]},
        _p2_result_body(model),
    )
    fixture = _p2_fixture(model)
    fixture_manifest_hashes = (
        [str(fixture["execution_manifest_sha256"])]
        if fixture.get("execution_manifest_sha256")
        else []
    )
    outputs[VAULT_RELATIVE_PATH / "05_Research_History/P2_FIXTURE_PILOT.md"] = _note(
        {**common, "note_id": "P2-FIXTURE-PILOT", "note_type": "history_report", "phase_id": "P2_SCOPE_DEVELOPMENT", "task_id": "P2.1", "workflow_status": "complete" if fixture.get("status") == "passed" else "verification_needed", "evidence_maturity": "fixture", "claim_level": "none", "current_scientific_authority": False, "source_run_ids": ["p2-fixture-pilot-v1"] if fixture.get("executed") else [], "source_manifest_sha256": fixture_manifest_hashes, "related_literature_ids": ["U006", "U011", "U154"]},
        _p2_fixture_body(model),
    )
    review = _p2_official_review(model)
    outputs[VAULT_RELATIVE_PATH / "05_Research_History/P2_OFFICIAL_REVIEW_AUDIT.md"] = _note(
        {**common, "note_id": "P2-OFFICIAL-REVIEW-AUDIT", "note_type": "history_report", "phase_id": "P2_SCOPE_DEVELOPMENT", "task_id": "P2.1", "workflow_status": "complete" if review.get("status") == "accepted_static_contract_review" else "verification_needed", "evidence_maturity": "non_scientific", "claim_level": "none", "current_scientific_authority": False, "source_run_ids": [], "source_manifest_sha256": [], "related_literature_ids": ["U006", "U011", "U154"]},
        _p2_official_review_body(model),
    )

    # Preserve each bounded review round as its own generated history note.
    for round_item in review.get("rounds", []) if isinstance(review.get("rounds"), list) else []:
        if not isinstance(round_item, Mapping):
            continue
        round_number = str(round_item.get("round", ""))
        if not round_number.isdigit():
            continue
        result_sha = str(round_item.get("result_sha256", ""))
        round_verdict = str(round_item.get("verdict", "not_recorded"))
        round_body = (
            f"# P2 Official Review Round {round_number}\n\n"
            "## Scope\n\n"
            "This note records one read-only static contract-review round. It is engineering provenance and does not authorize measured execution.\n\n"
            f"## Verdict\n\nRound `{round_number}` verdict: **{round_verdict}**. Reviewed commit: `{round_item.get('reviewed_commit', '-')}`. Result SHA-256: `{result_sha}`.\n\n"
            "## Boundary\n\nProtected data, final split, real candidates, selection, and measured P2 remained untouched. A later accepted round supersedes only the review disposition, not the historical record of this round.\n\n"
            "## Links\n\n[[P2_OFFICIAL_REVIEW_AUDIT]] · [[P2.1]] · [[HOME]]\n"
        )
        outputs[VAULT_RELATIVE_PATH / f"05_Research_History/P2_OFFICIAL_REVIEW_ROUND_{round_number}.md"] = _note(
            {**common, "note_id": f"P2-OFFICIAL-REVIEW-ROUND-{round_number}", "note_type": "history_report", "phase_id": "P2_SCOPE_DEVELOPMENT", "task_id": "P2.1", "workflow_status": "complete", "evidence_maturity": "static_contract_review", "claim_level": "none", "source_run_ids": [], "source_manifest_sha256": [result_sha] if result_sha else [], "related_literature_ids": ["U006", "U011", "U154"], "review_round": int(round_number), "verdict": round_verdict},
            round_body,
        )

    outputs[VAULT_RELATIVE_PATH / "03_Results/Current/P2_MEASURED_PENDING.md"] = _note(
        {**common, "note_id": "P2-MEASURED-PENDING", "note_type": "result_report", "phase_id": "P2_SCOPE_DEVELOPMENT", "task_id": "P2.1", "workflow_status": "ready", "evidence_maturity": "planned", "claim_level": "none", "result_id": "P2-MEASURED-PENDING", "current_scientific_authority": False, "source_run_ids": [], "source_manifest_sha256": [], "related_literature_ids": ["U006", "U011", "U154"]},
        "# P2 Measured Result Template\n\n"
        "This validated template is pending Owner-local execution. It contains no fixture metrics and no measured result.\n\n"
        "- status = `not_started`\n"
        "- evidence_class = `planned`\n"
        "- scientific_authority = `false`\n"
        "- measured results = `unavailable`\n"
        "- baseline commitment = `unavailable`\n"
        "- candidate results = `unavailable`\n"
        "- shortlist = `unavailable`\n"
        "- selection result = `unavailable`\n"
        "- final claim = `unavailable`\n"
        "- next action = `Owner-local P2 measured preflight`\n\n"
        "Do not populate this template from the repository-only fixture.\n\n"
        "[[P2_SCOPE_DEVELOPMENT_MASTER_REPORT]] · [[P2.1]] · [[HOME]]\n",
    )

    observatory = model.get("observatory", {}) if isinstance(model.get("observatory"), Mapping) else {}
    observatory_hashes = [str(value) for value in (observatory.get("registry_sha256"), observatory.get("receipt_sha256")) if value]
    outputs[VAULT_RELATIVE_PATH / "03_Results/Current/OBSERVATORY_FIXTURE_RUN.md"] = _note(
        {**common, "note_id": "OBSERVATORY-FIXTURE-RUN", "note_type": "result_report", "phase_id": "P2_SCOPE_DEVELOPMENT", "task_id": "P2.1", "workflow_status": "complete" if observatory.get("status") == "ready" else "verification_needed", "evidence_maturity": "fixture", "claim_level": "none", "result_id": "obs-result-fixture", "current_scientific_authority": False, "source_run_ids": ["obs-run-parent"], "source_manifest_sha256": observatory_hashes},
        _observatory_run_body(observatory),
    )
    outputs[VAULT_RELATIVE_PATH / "05_Research_History/OBSERVATORY_FAILURE_RECOVERY.md"] = _note(
        {**common, "note_id": "OBSERVATORY-FAILURE-RECOVERY", "note_type": "failed_attempt", "phase_id": "P2_SCOPE_DEVELOPMENT", "task_id": "P2.1", "workflow_status": "complete" if observatory.get("status") == "ready" else "verification_needed", "evidence_maturity": "fixture", "claim_level": "none", "current_scientific_authority": False, "source_run_ids": ["obs-run-candidate-02"], "source_manifest_sha256": observatory_hashes},
        _observatory_failure_body(observatory),
    )

    for run in model.get("runs", []) if isinstance(model.get("runs"), list) else []:
        if not isinstance(run, Mapping):
            continue
        run_id = str(run.get("run_id", ""))
        if not run_id:
            continue
        run_metrics = [item for item in model.get("metrics", []) if isinstance(item, Mapping) and item.get("run_id") == run_id]
        metric_lines = "\n".join(
            f"- `{item.get('name')}` / split `{item.get('split')}` / scope `{item.get('scope')}`: `{item.get('value')}` (n=`{item.get('n')}`)"
            for item in run_metrics
        ) or "- No aggregate metric is recorded for this run."
        run_body = (
            f"# Run Report: {run_id}\n\n"
            "## Purpose\n\nThis report describes one validated aggregate run slot and its immutable manifest binding.\n\n"
            f"## Status\n\nArm `{run.get('arm', '-')}`; stage `{run.get('stage', '-')}`; status `{run.get('status', '-')}`.\n\n"
            f"## Output\n\nManifest SHA-256: `{run.get('manifest_sha256')}`. The safe projection retains aggregate values only.\n\n"
            "## Aggregate metrics\n\n" + metric_lines + "\n\n"
            "## Interpretation boundary\n\nThis run supports only the declared train/selection aggregate description. It does not expose per-query outcomes or establish final-split generalization.\n\n"
            "## Links\n\n[[P1_CPU_BASELINE_MASTER_REPORT]] · [[P1.3]] · [[P1_CPU_BASELINE_RESULT]]\n"
        )
        outputs[VAULT_RELATIVE_PATH / "03_Runs" / f"{run_id}.md"] = _note(
            {**common, "note_id": f"RUN-{run_id}", "note_type": "run_report", "phase_id": "P1_CPU_BASELINE", "task_id": "P1.3", "workflow_status": "complete", "evidence_maturity": "measured_selection", "claim_level": "descriptive", "current_scientific_authority": True, "source_run_ids": [run_id], "source_manifest_sha256": [str(run.get("manifest_sha256"))] if run.get("manifest_sha256") else [], "related_literature_ids": [], "related_decision_ids": ["D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"]},
            run_body,
        )

    outputs[VAULT_RELATIVE_PATH / "02_Advisor_Updates/Drafts/CURRENT_ADVISOR_UPDATE.md"] = _note(
        {**common, "note_id": "CURRENT-ADVISOR-UPDATE", "note_type": "advisor_update", "phase_id": "P1_CPU_BASELINE", "task_id": "P1.3", "workflow_status": "verification_needed", "evidence_maturity": "measured_selection" if _p1_measured(model) else "non_scientific", "claim_level": "descriptive" if _p1_measured(model) else "none", "lifecycle": "draft", "snapshot_status": "draft", "supersedes": None, "source_run_ids": p1_run_ids, "source_manifest_sha256": p1_manifest_hashes},
        _p1_advisor_body(model),
    )

    _add_literature_outputs(root, model, common, outputs)
    _add_history_outputs(common, outputs)
    _add_system_outputs(model, common, outputs)
    return outputs


def _observatory_run_body(observatory: Mapping[str, Any]) -> str:
    counters = observatory.get("real_counters", {})
    return (
        "# Evidence Observatory Fixture Run\n\n"
        "## Purpose\n\n"
        "This note records the repository-only capture exercise. It is engineering evidence and cannot be promoted to a scientific result.\n\n"
        "## What happened\n\n"
        f"The registry is **{observatory.get('status', 'unavailable')}** with integrity **{observatory.get('integrity_status', 'unknown')}**. "
        f"It contains `{observatory.get('record_counts', {}).get('runs', 0)}` runs, `{observatory.get('record_counts', {}).get('artifacts', 0)}` artifacts, and `{observatory.get('validated_metric_count', 0)}` validated synthetic metric.\n\n"
        f"Artifact lineage validation is **{observatory.get('artifact_lineage_status', 'unknown')}** with retention classes `{observatory.get('retention_class_counts', {})}`. "
        f"Prompt/config/environment bindings: `{observatory.get('prompt_binding_count', 0)}` / `{observatory.get('config_binding_count', 0)}` / `{observatory.get('environment_binding_count', 0)}`.\n\n"
        "## Boundary\n\n"
        f"Evidence class: `{observatory.get('evidence_class', 'fixture')}`; scientific authority: `{observatory.get('scientific_authority', False)}`; claim boundary: `{observatory.get('claim_boundary', 'no_measured_claim')}`.\n\n"
        f"Real P2 counters remain measured runs `{counters.get('measured_runs', 0)}`, candidates `{counters.get('candidate_count', 0)}`, shortlist `{counters.get('shortlist_count', 0)}`, selection `{counters.get('selection_accesses', 0)}`.\n\n"
        "## Next action\n\n"
        f"{observatory.get('next_action', 'Owner-local P2 measured preflight')}\n"
    )


def _observatory_failure_body(observatory: Mapping[str, Any]) -> str:
    failures = observatory.get("failure_records", []) if isinstance(observatory.get("failure_records"), list) else []
    recoveries = observatory.get("recovery_records", []) if isinstance(observatory.get("recovery_records"), list) else []
    detail_lines = []
    for failure in failures:
        detail_lines.append(
            f"- Failure `{failure.get('record_id')}` at `{failure.get('stage')}` / class `{failure.get('failure_class')}`; checkpoint `{failure.get('last_valid_checkpoint')}`; counters before/after `{failure.get('counters_before')}` -> `{failure.get('counters_after')}`; protected data accessed `{failure.get('protected_data_accessed')}`."
        )
    for recovery in recoveries:
        detail_lines.append(
            f"- Recovery `{recovery.get('record_id')}` for `{recovery.get('failure_id')}`: `{recovery.get('action')}`; validation `{recovery.get('validation_after_recovery')}`; metric promotion `{recovery.get('metric_promotion')}`; residual risk `{recovery.get('residual_risk')}`."
        )
    return (
        "# Observatory Failure and Recovery\n\n"
        "The synthetic fixture intentionally retained one failed child and its recovery record. The failure did not change real counters or promote an incomplete metric.\n\n"
        f"- Failed child records: `{observatory.get('failed_child_count', 0)}`\n"
        f"- Recovery records: `{observatory.get('recovered_child_count', 0)}`\n"
        f"- Negative checks passed: `{observatory.get('negative_checks_passed', False)}`\n\n"
        "## Captured lineage\n\n"
        + ("\n".join(detail_lines) if detail_lines else "- No material failure/recovery record is available.")
        + "\n\n"
        "## Lesson\n\n"
        "A failed branch remains useful evidence when the checkpoint, retry action, and claim boundary are recorded together. This is a capture-readiness lesson, not evidence about retrieval quality.\n"
    )


def _add_literature_outputs(root: Path, model: Mapping[str, Any], common: Mapping[str, Any], outputs: dict[Path, str]) -> None:
    catalog = root / "evidence/literature/catalog/corpus_manifest.csv"
    rows: list[dict[str, str]] = []
    if catalog.is_file():
        with catalog.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    links = []
    for row in rows:
        paper_id = row.get("u_id", "")
        if not re.fullmatch(r"U\d{3}", paper_id):
            continue
        title = row.get("verified_title") or paper_id
        theme = _literature_theme(paper_id)
        task_id = "P1.3" if paper_id == "U011" else "P2.1" if paper_id == "U154" else "P0.3"
        digest = next(iter(sorted((root / "evidence/literature/digests").glob(f"{paper_id}_*.md"))), None)
        digest_uri = digest.relative_to(root).as_posix() if digest else "not-available"
        digest_sha256 = sha256(digest.read_bytes()) if digest else None
        domain = urlparse(row.get("source_url", "")).netloc or "local"
        body = (
            f"# {title}\n\n## Why it matters to myIS\n\nLiterature proxy for {theme}.\n\n"
            "## Key takeaway\n\nA safe proxy records metadata and a digest commitment; the full digest remains in Brain.\n\n"
            f"## Supports / challenges\n\nSupports the evidence map for [[{task_id}]].\n\n"
            f"## Used in\n\n[[{task_id}]] and [[P1_CPU_BASELINE_RESULT]].\n\n"
            f"## Citation status\n\nTier {row.get('tier') or 'unassigned'}; source domain `{domain}`.\n\n"
            f"## Canonical digest\n\nSafe pointer: `{digest_uri}`\n"
        )
        outputs[VAULT_RELATIVE_PATH / "04_Literature_Map/Papers" / f"{paper_id}.md"] = _note(
            {**common, "note_id": f"LIT-{paper_id}", "note_type": "literature_proxy", "phase_id": "P1_CPU_BASELINE" if task_id == "P1.3" else "P0_FOUNDATION", "task_id": task_id, "workflow_status": "complete", "evidence_maturity": "historical_exposed", "claim_level": "descriptive", "paper_id": paper_id, "literature_status": "digested" if digest else "waiting_dependency", "themes": [theme], "supports": [task_id], "challenges": [], "canonical_digest_path": digest_uri, "canonical_digest_sha256": digest_sha256, "canonical_commit": common["source_commit"], "source_pdf_in_vault": False},
            body,
        )
        links.append(f"- [[{paper_id}]] - {title}")
    outputs[VAULT_RELATIVE_PATH / "04_Literature_Map/LITERATURE_INDEX.md"] = _note(
        {**common, "note_id": "LITERATURE-INDEX", "note_type": "literature_synthesis", "phase_id": "P0_FOUNDATION", "task_id": "P0.3", "workflow_status": "in_progress", "evidence_maturity": "historical_exposed", "claim_level": "descriptive", "paper_count": len(links)},
        "# Literature Map\n\n" + "\n".join(links) + "\n",
    )


def _add_history_outputs(common: Mapping[str, Any], outputs: dict[Path, str]) -> None:
    links = []
    for paper in ("A", "B", "C", "D"):
        note_id = f"HISTORY-PAPER-{paper}"
        exposure = "historical_exposed" if paper in {"A", "B", "D"} else "historical_unverified"
        outputs[VAULT_RELATIVE_PATH / "05_Research_History" / f"Paper_{paper}.md"] = _note(
            {**common, "note_id": note_id, "note_type": "history_report", "phase_id": None, "task_id": None, "workflow_status": "complete", "evidence_maturity": "historical_exposed", "claim_level": "none", "exposure_status": exposure, "current_scientific_authority": False},
            f"# Paper {paper}\n\nStatus: **{exposure}**\n\nThis note is historical evidence and cannot override current P0-P4 run facts.\n",
        )
        links.append(f"- [[Paper_{paper}]] - {exposure}")
    outputs[VAULT_RELATIVE_PATH / "05_Research_History/RESEARCH_HISTORY_INDEX.md"] = _note(
        {**common, "note_id": "RESEARCH-HISTORY-INDEX", "note_type": "history_report", "phase_id": None, "task_id": None, "workflow_status": "complete", "evidence_maturity": "historical_exposed", "claim_level": "none", "current_scientific_authority": False},
        "# Research History\n\n" + "\n".join(links) + "\n",
    )


def _add_system_outputs(model: Mapping[str, Any], common: Mapping[str, Any], outputs: dict[Path, str]) -> None:
    outputs[VAULT_RELATIVE_PATH / "README.md"] = (
        "# myIS Research Report Vault\n\n"
        "This is a rebuildable narrative and knowledge projection. Canonical run facts remain in Git-tracked manifests and receipts. "
        "Open `HOME.md` first; write personal notes only under `80_Owner_Notes/`.\n\n"
        "Migration: legacy generated projection notes remain under `projections/obsidian/`; current P0-P4 reports are rebuilt here. "
        "Historical Paper A-D notes cannot establish current scientific claims.\n"
    )
    note_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "myis.obsidian-note.v2",
        "type": "object",
        "required": sorted(_REQUIRED_NOTE_PROPERTIES),
        "properties": {
            "schema_version": {"const": "myis.obsidian-note.v2"},
            "note_id": {"type": "string", "minLength": 1},
            "note_type": {"enum": sorted(_ALLOWED_NOTE_TYPES)},
            "workflow_status": {"enum": sorted(_ALLOWED_WORKFLOW_STATUSES)},
            "evidence_maturity": {"enum": sorted(_ALLOWED_EVIDENCE_MATURITY)},
            "claim_level": {"enum": sorted(_ALLOWED_CLAIM_LEVELS)},
            "claim_boundary": {"type": "string", "minLength": 1},
            "evidence_class": {"type": "string", "minLength": 1},
            "scientific_authority": {"type": "boolean"},
            "generated_from_revision": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
            "last_material_update": {"type": "string", "format": "date-time"},
            "next_authorized_action": {"type": "string", "minLength": 1},
            "safe_to_present": {"type": "boolean"},
            "managed_by": {"const": "myis-report"},
            "edit_policy": {"const": "generated_do_not_edit"},
        },
    }
    outputs[VAULT_RELATIVE_PATH / "00_System/schemas/obsidian-note.v2.json"] = _json_text(note_schema)
    outputs[VAULT_RELATIVE_PATH / "06_Decisions_Risks/RAID.md"] = _note(
        {**common, "note_id": "RAID", "note_type": "risk", "phase_id": "P1_CPU_BASELINE", "task_id": "P1.3", "workflow_status": "complete" if _p1_measured(model) else "blocked", "evidence_maturity": "measured_selection" if _p1_measured(model) else "non_scientific", "claim_level": "none", "raid_id": "RISK-P1-EVIDENCE-MATRIX", "raid_type": "risk", "raid_status": "closed" if _p1_measured(model) else "open"},
        "# RAID\n\n"
        + ("- Closed: P1 evidence matrix, package binding, and rigor review are complete.\n" if _p1_measured(model) else "- Risk: P1 evidence matrix is incomplete.\n")
        + "- Decision: D2 and D3 remain Owner-only.\n",
    )
    outputs[VAULT_RELATIVE_PATH / "06_Decisions_Risks/Decisions.md"] = _note(
        {**common, "note_id": "DECISIONS", "note_type": "decision", "phase_id": "P3_FINAL", "task_id": "P3.1", "workflow_status": "waiting_gate", "evidence_maturity": "non_scientific", "claim_level": "none", "decision_ids": ["D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"], "authority": "owner"},
        "# Owner Decisions\n\n- `D2_OPEN_FINAL`: waiting for Owner.\n- `D3_SUBMIT_RELEASE`: waiting for Owner.\n\nThis vault can display but cannot approve either decision.\n",
    )
    decision_sources = {
        "D1_START_CAMPAIGN": ("control/decisions/D1_START_CAMPAIGN.yaml", "active", "standing campaign authorization; it does not open D2, D3, final split, or selection"),
        "D2_OPEN_FINAL": ("control/decisions/ledger.jsonl", "waiting_owner", "Owner-only decision required before P3 final evaluation"),
        "D3_SUBMIT_RELEASE": ("control/decisions/ledger.jsonl", "waiting_owner", "Owner-only decision required before P4 publication and release"),
    }
    for decision_id, (source_uri, status, explanation) in decision_sources.items():
        outputs[VAULT_RELATIVE_PATH / "06_Decisions_Risks" / f"{decision_id}.md"] = _note(
            {**common, "note_id": f"DECISION-{decision_id}", "note_type": "decision", "phase_id": "P0_FOUNDATION" if decision_id == "D1_START_CAMPAIGN" else "P3_FINAL" if decision_id == "D2_OPEN_FINAL" else "P4_PUBLICATION", "task_id": "P0.3" if decision_id == "D1_START_CAMPAIGN" else "P3.1" if decision_id == "D2_OPEN_FINAL" else "P4.1", "workflow_status": "complete" if decision_id == "D1_START_CAMPAIGN" else "waiting_gate", "evidence_maturity": "engineering", "claim_level": "none", "decision_id": decision_id, "decision_status": status, "authority": "owner", "source_uri": source_uri},
            f"# Decision {decision_id}\n\n**Status:** `{status}`\n\n{explanation}.\n\nCanonical source: `{source_uri}`. Generated notes cannot approve or mutate Owner decisions.\n\n[[Decisions]] · [[HOME]]\n",
        )
    outputs[VAULT_RELATIVE_PATH / "06_Decisions_Risks/Failed_Attempts.md"] = _note(
        {**common, "note_id": "FAILED-ATTEMPTS", "note_type": "failed_attempt", "phase_id": "P1_CPU_BASELINE", "task_id": "P1.3", "workflow_status": "complete", "evidence_maturity": "historical_exposed", "claim_level": "none", "retry_allowed": True},
        "# Historical Invalid Attempt\n\n## What was tried\n\nA legacy aggregate P1 receipt was retained.\n\n## Failure category\n\nIt lacks the hash-bound four-slot manifest and validation-report matrix required for promotion.\n\n## Lesson\n\nHistorical aggregate evidence remains traceable but cannot override canonical run facts.\n\n## Retry\n\nA fresh Owner-local CPU P1 run may proceed only through the existing approved envelope.\n",
    )
    bases = {
        "phases.base": ("phase_id", ["P0-P4 Overview", "Current Phase", "Blocked Phases"]),
        "tasks.base": ("workflow_status", ["Simple Board", "PM Detail", "By Phase", "Blocked", "Verification Needed", "Owner Actions"]),
        "results.base": ("evidence_maturity", ["Current Valid", "Selection", "Confirmation", "Negative or Null", "Historical Exposed", "Publication Ready"]),
        "literature.base": ("literature_status", ["By Theme", "By Status", "Cited", "Supports", "Challenges", "Missing Synthesis"]),
        "advisor-updates.base": ("snapshot_status", ["Latest", "Drafts", "Presented Snapshots", "Corrections"]),
        "decisions-risks.base": ("workflow_status", ["Pending Decisions", "Active Risks", "Blocked Dependencies", "Closed Items"]),
    }
    for name, (group, views) in bases.items():
        outputs[VAULT_RELATIVE_PATH / "10_Bases" / name] = (
            "filters:\n  and:\n    - 'managed_by == \"myis-report\"'\n"
            f"groupBy:\n  property: {group}\nviews:\n" + "".join(f"  - type: table\n    name: {view}\n" for view in views)
        )
    outputs[VAULT_RELATIVE_PATH / "70_Templates/OWNER_NOTE_TEMPLATE.md"] = _note(
        {**common, "note_id": "OWNER-NOTE-TEMPLATE", "note_type": "owner_note", "phase_id": None, "task_id": None, "workflow_status": "ready", "evidence_maturity": "non_scientific", "claim_level": "none", "safe_to_present": False},
        "# Owner Note\n\nCopy this template into `80_Owner_Notes/` before writing. Files in that folder are Owner-authored and preserved by sync.\n",
    )
    outputs[VAULT_RELATIVE_PATH / "00_System/Generated/README.md"] = (
        "# Generated files\n\nFiles listed in `generated-manifest.json` are managed by `myis-report`.\n"
    )
    report_links = ["# Generated Report Index", "", "All report notes are generated from one validated read-model revision.", "", "## Phase and Task reports", ""]
    for phase in model.get("phases", []) if isinstance(model.get("phases"), list) else []:
        phase_id = str(phase.get("phase_id"))
        report_links.append(f"- [[{phase_id}_MASTER_REPORT]]")
        for task in phase.get("tasks", []) if isinstance(phase.get("tasks"), list) else []:
            report_links.append(f"  - [[{task.get('task_id')}]]")
    report_links.extend(["", "## Run, decision, and pending reports", "", "- [[P2_MEASURED_PENDING]]"])
    for target, relative in (
        ("P2_OFFICIAL_REVIEW_AUDIT", "05_Research_History/P2_OFFICIAL_REVIEW_AUDIT.md"),
        ("P2_OFFICIAL_REVIEW_ROUND_1", "05_Research_History/P2_OFFICIAL_REVIEW_ROUND_1.md"),
        ("P2_OFFICIAL_REVIEW_ROUND_2", "05_Research_History/P2_OFFICIAL_REVIEW_ROUND_2.md"),
        ("P2_OFFICIAL_REVIEW_ROUND_3", "05_Research_History/P2_OFFICIAL_REVIEW_ROUND_3.md"),
        ("P2_FIXTURE_PILOT", "05_Research_History/P2_FIXTURE_PILOT.md"),
        ("OBSERVATORY_FIXTURE_RUN", "03_Results/Current/OBSERVATORY_FIXTURE_RUN.md"),
        ("OBSERVATORY_FAILURE_RECOVERY", "05_Research_History/OBSERVATORY_FAILURE_RECOVERY.md"),
        ("D1_START_CAMPAIGN", "06_Decisions_Risks/D1_START_CAMPAIGN.md"),
        ("D2_OPEN_FINAL", "06_Decisions_Risks/D2_OPEN_FINAL.md"),
        ("D3_SUBMIT_RELEASE", "06_Decisions_Risks/D3_SUBMIT_RELEASE.md"),
    ):
        if VAULT_RELATIVE_PATH / relative in outputs:
            report_links.append(f"- [[{target}]]")
    report_links.extend(["", "Source: [[HOME]]", ""])
    outputs[VAULT_RELATIVE_PATH / "00_System/Generated/REPORT_INDEX.md"] = _note(
        {**common, "note_id": "REPORT-INDEX", "note_type": "project_map", "phase_id": model.get("project", {}).get("current_phase"), "task_id": model.get("project", {}).get("current_task"), "workflow_status": "complete", "evidence_maturity": "engineering", "claim_level": "none", "report_index": "projections/reports/index.json"},
        "\n".join(report_links),
    )


def _projection_frontmatter(model: Mapping[str, Any], **properties: Any) -> str:
    values = {
        "schema_version": "myis.generated-projection.v2",
        "managed_by": "myis-report",
        "read_model_path": "../../../01_Research/projections/read-model/read-model.v2.json",
        "read_model_revision": model["read_model_revision"],
        "read_model_sha256": model["read_model_sha256"],
        "source_commit": model["source_commit"],
        **properties,
    }
    lines = ["---"]
    for key, value in values.items():
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.extend(["---", ""])
    return "\n".join(lines)


def _brain_report_contents(root: Path, model: Mapping[str, Any]) -> dict[Path, str]:
    directory = (root.parent / "02_Brain/reports/generated").resolve()
    revision = str(model["read_model_revision"])
    state = str(model["project"]["state"])
    phases = [row for row in model.get("phases", []) if isinstance(row, Mapping)]
    tasks = [row for row in model.get("tasks", []) if isinstance(row, Mapping)]
    p2 = _p2_readiness(model)
    p2_review = _p2_official_review(model)
    p2_fixture = _p2_fixture(model)
    p2_proposal = p2.get("candidate_proposal", {}) if isinstance(p2.get("candidate_proposal"), Mapping) else {}
    armindex = model.get("armindex", {}) if isinstance(model.get("armindex"), Mapping) else {}
    armindex_phases = [row for row in armindex.get("phases", []) if isinstance(row, Mapping)]

    phase_lines: list[str] = []
    for phase in phases:
        phase_lines.append(f"- **{phase['phase_id']}**: {phase['status']}")
        for task in phase.get("tasks", []):
            phase_lines.append(
                f"  - `{task['task_id']}` {task['title']}: **{task['status']}**"
            )
    status_body = (
        "# Program Status / สถานะโครงการ\n\n"
        f"Active campaign: **{armindex.get('campaign_id', 'armindex-multiretriever-v2')}**\n\n"
        f"Active phase: **{armindex.get('current_phase', 'A0_MIGRATION_FOUNDATION')}**\n\n"
        f"Historical SCOPE state: **{state}**\n\n"
        + "\n".join(f"- **{phase['phase_id']}**: {phase['status']}" for phase in phases)
        + "\n\n## Resource boundary\n\n"
        f"- CPU-only: `{model['resources']['cpu_only']}`\n"
        f"- GPU used: `{model['resources']['gpu']}`\n"
        f"- Paid API used: `{model['resources']['paid_api']}`\n"
        f"- Actual cost USD: `{model['resources']['actual_cost_usd']}`\n\n"
        f"P2 official static review: Round `{p2_review.get('final_round', '-')}` / `{p2_review.get('final_verdict', 'not_recorded')}`; evidence class `{p2_review.get('evidence_class', 'static_contract_review')}`.\n\n"
        f"P2 repository-only fixture: `{p2_fixture.get('status', 'not_executed')}`; evidence class `{p2_fixture.get('evidence_class', 'fixture')}`; scientific authority `{p2_fixture.get('scientific_authority', False)}`.\n\n"
        f"P2 Owner-local preflight: `{p2.get('preflight_status', 'not_started')}`; measured runs `{p2.get('measured_runs', 0)}`, real candidates `{p2.get('candidate_count', 0)}`, shortlist `{p2.get('shortlist_count', 0)}`, selection accesses `{p2.get('selection_accesses', 0)}`.\n\n"
        f"P2 candidate proposal: `{p2_proposal.get('status', 'not_created')}` / `{p2_proposal.get('adoption', 'not_adopted')}`; controls `{p2_proposal.get('frozen_controls', 0)}`, preregistered candidates `{p2_proposal.get('preregistered_candidates', 0)}`, registered `{p2_proposal.get('registered_candidates', 0)}`, hash-locked `{p2_proposal.get('hash_locked_candidates', 0)}`.\n\n"
        "D2 and D3 remain Owner-only. Final 872 is still closed.\n"
    )
    phase_task_body = (
        "# Phase / Task Status\n\n"
        + "\n".join(phase_lines)
        + f"\n\nProgress: `{model['progress']['done']}/{model['progress']['total']}` tasks complete.\n"
    )

    dataset_lines = [
        "| Dataset | Role | Representation | Classification | Safe counts | SHA-256 |",
        "|---|---|---|---|---|---|",
    ]
    for dataset in model.get("datasets", []):
        counts = dataset.get("counts", {})
        count_text = ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
        dataset_lines.append(
            f"| `{dataset['dataset_id']}` | {dataset['role']} | {dataset['representation']} | "
            f"{dataset['classification']} | {count_text} | `{dataset['sha256']}` |"
        )
    datasets_body = (
        "# Dataset Registry / ชุดข้อมูล\n\n"
        "All rows are aggregate/hash-only projections. Owner-local bytes stay outside Brain.\n\n"
        + "\n".join(dataset_lines)
        + "\n"
    )

    experiment_rows = [
        row for row in model.get("experiments", []) if isinstance(row, Mapping)
    ]
    experiment = experiment_rows[0] if experiment_rows else {}
    run_lines = [
        "| Arm | Split | Run ID | Status | Manifest SHA-256 |",
        "|---|---|---|---|---|",
    ]
    for run in sorted(model.get("runs", []), key=lambda row: (str(row.get("arm")), str(row.get("stage")))):
        run_lines.append(
            f"| {run['arm']} | {run['stage']} | `{run['run_id']}` | {run['status']} | "
            f"`{run['manifest_sha256']}` |"
        )
    experiments_body = (
        "# Experiments / การทดลอง\n\n"
        f"Campaign: `{experiment.get('campaign_id')}`; experiment: "
        f"`{experiment.get('experiment_id')}`; validated runs: `{experiment.get('run_count', 0)}`.\n\n"
        + "\n".join(run_lines)
        + "\n\nMLflow is an additive aggregate-only mirror; canonical manifests and receipts remain authoritative.\n"
    )

    readiness = model.get("publication_readiness", {})
    readiness_lines = ["| Check | Status | Canonical source |", "|---|---|---|"]
    for check in readiness.get("checks", []):
        readiness_lines.append(f"| `{check['id']}` | **{check['status']}** | `{check['source']}` |")
    readiness_body = (
        "# Publication Readiness\n\n"
        f"Status: **{readiness.get('status', 'unknown')}**\n\n"
        + "\n".join(readiness_lines)
        + "\n\nP1 selection evidence does not open D2, establish a final result, or authorize publication.\n"
    )

    result_rows = [row for row in model.get("results", []) if isinstance(row, Mapping)]
    result = result_rows[0] if result_rows else {}
    weekly_body = (
        "# Weekly Summary / สรุปสัปดาห์\n\n"
        "## Completed\n\n"
        f"- P1 CPU baseline is `{state}` with four validated R0/R0-W train/selection slots.\n"
        f"- Package: `{result.get('package_sha256')}`; rigor: `{result.get('rigor_grade')}`.\n"
        f"- MLflow parent + children: `{1 + len(model.get('mlflow_registration', {}).get('children', []))}` runs.\n\n"
        f"- P2 static review closed at Round `{p2_review.get('final_round', '-')}` with verdict `{p2_review.get('final_verdict', 'not_recorded')}`.\n"
        f"- Repository-only P2 fixture is `{p2_fixture.get('status', 'not_executed')}` with `{p2_fixture.get('synthetic_candidates', 0)}` synthetic candidates and no measured execution.\n\n"
        f"- Owner-local P2 preflight is `{p2.get('preflight_status', 'not_started')}`; the candidate proposal is `{p2_proposal.get('adoption', 'not_adopted')}` with no registered or hash-locked measured candidates.\n\n"
        "## Next automatic action\n\n"
        "P2 remains ready but not measured. The next authorized action is Owner-local measured preflight; "
        "D2 and D3 remain unchanged.\n"
    )

    moc_body = (
        "# ArmIndex Research MOC\n\n"
        "- [[program-status]]\n- [[phase-task-status]]\n- [[datasets]]\n"
        "- [[experiments]]\n- [[publication-readiness]]\n- [[weekly-summary]]\n\n"
        "## Phase reports / รายงานราย Phase\n\n"
        + "\n".join(f"- [[phase-{phase['phase_id']}]]" for phase in phases)
        + "\n\n## Backlinks\n\n- [[../../memory/MOC]]\n- [[../../reference/Literature/Literature Index]]\n\n"
        f"Source revision: `{revision}`\n"
    )

    common = _projection_frontmatter(model)
    outputs = {
        directory / "MOC.md": common + moc_body,
        directory / "program-status.md": common + status_body,
        directory / "phase-task-status.md": common + phase_task_body,
        directory / "datasets.md": common + datasets_body,
        directory / "experiments.md": common + experiments_body,
        directory / "publication-readiness.md": common + readiness_body,
        directory / "weekly-summary.md": common + weekly_body,
    }
    for phase in armindex_phases:
        phase_id = str(phase["phase_id"])
        task_lines = "\n".join(
            f"- `{task.get('task_id')}` **{task.get('status')}**: {task.get('title')}"
            for task in phase.get("tasks", [])
            if isinstance(task, Mapping)
        ) or "- No task rows"
        harvest_note = ""
        if phase_id == "A0_MIGRATION_FOUNDATION":
            harvest = armindex.get("legacy_code_harvest", {})
            if isinstance(harvest, Mapping):
                harvest_note = (
                    "\n## A0.10 Legacy Code Harvest\n\n"
                    f"Status: `{harvest.get('status', 'not_started')}`; validated: `{harvest.get('validated', False)}`; "
                    f"reviewed/adopted/rejected: `{harvest.get('components_reviewed', 0)}`/"
                    f"`{harvest.get('components_adopted', 0)}`/`{harvest.get('components_rejected', 0)}`.\n\n"
                    f"Ledger: `{harvest.get('ledger_uri')}` / `{harvest.get('ledger_sha256')}`.\n\n"
                    f"Receipt: `{harvest.get('receipt_uri')}` / `{harvest.get('receipt_sha256')}`.\n"
                )
        outputs[directory / "armindex" / f"phase-{phase_id}.md"] = _projection_frontmatter(model, phase_id=phase_id) + (
            f"# {phase_id}\n\nStatus: **{phase.get('status')}**\n\n{phase.get('purpose')}\n\n## Tasks\n\n{task_lines}\n\n"
            f"Measured ArmIndex runs: `{armindex.get('counters', {}).get('measured_runs', 0)}`. Selection: `{armindex.get('counters', {}).get('selection_accesses', 0)}`. Final: `{armindex.get('counters', {}).get('final_accesses', 0)}`.\n\n"
            f"Next: {armindex.get('next_command', '')}\n"
            + harvest_note
        )
    for phase in phases:
        phase_id = str(phase["phase_id"])
        task_rows = [task for task in tasks if task.get("phase_id") == phase_id]
        task_lines = []
        for task in task_rows:
            evidence_ids = ", ".join(f"`{item}`" for item in task.get("evidence_ids", [])) or "none"
            task_lines.append(
                f"- `{task['task_id']}` **{task['status']}**: {task['title']}; evidence: {evidence_ids}"
            )
        gate_text = (
            "`D2_OPEN_FINAL` is required only before P3 final evaluation."
            if phase_id == "P3_FINAL"
            else "`D3_SUBMIT_RELEASE` is required only before P4 publication."
            if phase_id == "P4_PUBLICATION"
            else "No additional Owner micro-gate is created by this phase report."
        )
        body = (
            f"# {phase_id} / รายงาน Phase\n\n"
            f"สถานะปัจจุบัน: **{phase['status']}**\n\n"
            "## Tasks\n\n"
            + "\n".join(task_lines)
            + f"\n\n## Gate / Owner action\n\n- {gate_text}\n"
        )
        if phase_id == "P1_CPU_BASELINE":
            registration = model.get("mlflow_registration", {})
            body += (
                "\n## Execution and progress\n\n"
                f"{_p1_execution_summary(model)}\n\n"
                f"## Dataset aggregates\n\n{_p1_dataset_table(model)}\n\n"
                f"## Measured train/selection results\n\n{_p1_metric_table(model)}\n\n"
                f"## Interpretation\n\n{_p1_comparison(model)}\n\n"
                f"## Evidence package\n\n{_p1_evidence_table(model)}\n\n"
                f"- Package SHA-256: `{result.get('package_sha256')}`\n"
                f"- Package file SHA-256: `{result.get('package_file_sha256')}`\n"
                f"- Rigor: `{result.get('rigor_grade')}` (mean `{result.get('rigor_mean_score')}`)\n"
                f"- MLflow parent status: `{registration.get('parent', {}).get('status')}`; "
                f"children: `{len(registration.get('children', []))}`\n\n"
                "## Evidence boundary\n\n"
                "These are descriptive train/selection results. Final 872 remains closed, globally untouched "
                "remains not claimable, and no statistical superiority or publication claim is made.\n"
            )
        else:
            body += (
                "\n## Evidence and next step\n\n"
                f"- Read-model revision: `{revision}`\n"
                "- Follow the canonical phase order and keep D2/D3 Owner-only.\n"
            )
            if phase_id == "P2_SCOPE_DEVELOPMENT":
                body += (
                    f"- Official static review: Round `{p2_review.get('final_round', '-')}` "
                    f"verdict `{p2_review.get('final_verdict', 'not_recorded')}`; "
                    f"repository fixture `{p2_fixture.get('status', 'not_executed')}`.\n"
                    f"- Fixture receipt: `{p2_fixture.get('receipt_uri')}` / `{p2_fixture.get('receipt_sha256')}`.\n"
                    "- Real candidates, real shortlist, and real selection remain zero.\n"
                    "- Source: `orchestration/audits/p2-readiness/index.json`.\n"
                )
        outputs[directory / f"phase-{phase_id}.md"] = (
            _projection_frontmatter(model, phase_id=phase_id) + body
        )
    return outputs


def _paper_report_contents(root: Path, model: Mapping[str, Any]) -> dict[Path, str]:
    path = (root.parent / "03_Paper/publications/isai-nlp-2026/generated/publication-readiness.md").resolve()
    source_lock_path = (
        root.parent
        / "03_Paper/publications/isai-nlp-2026/provenance/publication-source-lock.json"
    ).resolve()
    readiness = model.get("publication_readiness", {})
    fixture = _p2_fixture(model)
    harvest = model.get("armindex", {}).get("legacy_code_harvest", {})
    if not isinstance(harvest, Mapping):
        harvest = {}
    lines = ["| Check | Status | Canonical source |", "|---|---|---|"]
    for check in readiness.get("checks", []):
        lines.append(f"| `{check['id']}` | **{check['status']}** | `{check['source']}` |")
    body = (
        "# Publication Readiness\n\n"
        f"Active campaign: **{model.get('armindex', {}).get('campaign_id', 'armindex-multiretriever-v2')}**\n\n"
        f"Active state: **{model.get('armindex', {}).get('status', 'migration')}**\n\n"
        f"Historical P1 state: **{model['project']['state']}**\n\n"
        f"Publication status: **{readiness.get('status', 'unknown')}**\n\n"
        + "\n".join(lines)
        + "\n\nArmIndex is in infrastructure migration with zero measured runs, Selection exposures, and Final exposures. P1 contains historical measured train/selection evidence only. The historical P2 lifecycle passed a "
        f"repository-only synthetic fixture (`{fixture.get('status', 'not_executed')}`), but measured P2 has not started and no P2 scientific claim is available. "
        "AI-assisted static review and synthetic fixture provenance are archived. D2 and D3 remain Owner-only, and this projection does not authorize final evaluation or release.\n\n"
        "## A0.10 engineering provenance\n\n"
        f"Source receipt: `{harvest.get('receipt_uri')}` / `{harvest.get('receipt_sha256')}`. "
        "This receipt is engineering evidence only and supports no retrieval-quality or publication claim.\n"
    )
    source_lock = {
        "schema_version": "myis.publication-source-lock.v2",
        "research_repository": "../01_Research",
        "campaign_id": model.get("armindex", {}).get("campaign_id", "armindex-multiretriever-v2"),
        "historical_campaign_id": model["project"]["campaign_id"],
        "read_model_path": "../01_Research/projections/read-model/read-model.v2.json",
        "read_model_revision": model["read_model_revision"],
        "read_model_sha256": model["read_model_sha256"],
        "status": "bound_train_selection_only",
        "claim_boundary": "train_selection_only",
        "claim_policy": "all_numeric_claims_resolve_to_hash_bound_research_evidence",
        "owner_decisions": ["D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"],
    }
    return {
        path: _projection_frontmatter(
            model,
            read_model_path="../../../../01_Research/projections/read-model/read-model.v2.json",
        ) + body,
        source_lock_path: _json_text(source_lock),
    }


def _compatibility_report_contents(root: Path, model: Mapping[str, Any]) -> dict[Path, str]:
    revision = str(model["read_model_revision"])
    state = str(model["project"]["state"])
    phases = "\n".join(f"- **{phase['phase_id']}**: {phase['status']}" for phase in model.get("phases", []))
    content = f"---\nread_model_revision: {revision}\nmanaged_by: myis-report\n---\n\n# Program Status\n\nState: **{state}**\n\n{phases}\n"
    legacy = root / "projections/obsidian/generated/program-status.md"
    return {legacy: content}


def _validate_external_projection_contents(contents: Mapping[Path, str]) -> None:
    for path, content in contents.items():
        if path.suffix.lower() not in {".json", ".md"}:
            raise ValueError(f"external projection has unsupported format: {path}")
        if path.suffix.lower() == ".json":
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as error:
                raise ValueError(f"external JSON projection is invalid: {path}") from error
            if not isinstance(parsed, Mapping):
                raise ValueError(f"external JSON projection is not an object: {path}")
        if _UNSAFE_HTML_RE.search(content) or _ABSOLUTE_PERSONAL_PATH_RE.search(content):
            raise ValueError(f"unsafe external projection content: {path}")
        if _PROTECTED_FIELD_RE.search(content) or _REMOTE_IMAGE_RE.search(content):
            raise ValueError(f"protected or remote external projection content: {path}")


def _generated_manifest(model: Mapping[str, Any], contents: Mapping[Path, str]) -> dict[str, Any]:
    files = []
    for relative, content in sorted(contents.items(), key=lambda item: item[0].as_posix()):
        if not relative.is_relative_to(VAULT_RELATIVE_PATH):
            continue
        match = _NOTE_ID_RE.search(content)
        note_id = match.group(1).strip().strip('"') if match else f"FILE-{sha256(relative.as_posix().encode())[:12]}"
        files.append({
            "note_id": note_id,
            "relative_path": relative.relative_to(VAULT_RELATIVE_PATH).as_posix(),
            "sha256": sha256(content.encode("utf-8")),
            "managed_by": "myis-report",
        })
    manifest: dict[str, Any] = {
        "schema_version": "myis.obsidian-generated-manifest.v2",
        "vault_id": "myis-obsidian-report",
        "read_model_revision": model["read_model_revision"],
        "read_model_sha256": model["read_model_sha256"],
        "source_commit": model["source_commit"],
        "projection_schema_version": model["projection_schema_version"],
        "files": files,
    }
    manifest["manifest_sha256"] = sha256(canonical_json(manifest))
    return manifest


def _note(properties: Mapping[str, Any], body: str) -> str:
    lines = ["---"]
    for key, value in properties.items():
        if value is None:
            rendered = "null"
        elif isinstance(value, bool):
            rendered = "true" if value else "false"
        elif isinstance(value, (int, float)):
            rendered = str(value)
        elif isinstance(value, (list, dict)):
            rendered = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        else:
            rendered = json.dumps(str(value), ensure_ascii=False)
        lines.append(f"{key}: {rendered}")
    lines.extend(["---", "", body.rstrip(), ""])
    return "\n".join(lines)


def _literature_theme(paper_id: str) -> str:
    number = int(paper_id[1:])
    if number <= 57:
        return "patent-retrieval"
    if number <= 82:
        return "optimization"
    if number <= 100:
        return "retrieval-evaluation"
    if number <= 130:
        return "multilingual-systems"
    return "governance-and-method"


def _workflow_status(value: Any) -> str:
    """Map read-model display states to the single Obsidian workflow vocabulary."""

    mapping = {
        "planned": "ready",
        "ready": "ready",
        "active": "in_progress",
        "a1_1_complete_a1_2_contract_locked": "in_progress",
        "complete": "complete",
        "completed": "complete",
        "measured": "complete",
        "blocked": "blocked",
        "blocked_until_p1": "waiting_dependency",
        "locked_pending_execution_contract": "waiting_dependency",
        "locked_until_D2": "waiting_gate",
        "locked_until_D3": "waiting_gate",
        "locked_owner_D2": "waiting_gate",
        "locked_owner_D3": "waiting_gate",
    }
    return mapping.get(str(value), "verification_needed")


def _frontmatter_properties(content: str, relative: Path) -> dict[str, Any]:
    match = _FRONTMATTER_RE.match(content)
    if match is None:
        raise ValueError(f"note has no YAML frontmatter: {relative}")
    properties: dict[str, Any] = {}
    for line in match.group(1).splitlines():
        item = _PROPERTY_RE.match(line)
        if item is None:
            raise ValueError(f"invalid frontmatter property: {relative}")
        key, raw = item.groups()
        try:
            properties[key] = json.loads(raw)
        except json.JSONDecodeError:
            properties[key] = raw.strip()
    return properties


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def _validate_generated_contents(contents: Mapping[Path, str], model: Mapping[str, Any] | None = None) -> None:
    seen_note_ids: set[str] = set()
    known_links = {relative.stem for relative in contents if relative.suffix.lower() == ".md"}
    known_links.add("README")
    for relative, content in contents.items():
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"generated path escapes repository: {relative}")
        if _UNSAFE_HTML_RE.search(content) or _ABSOLUTE_PERSONAL_PATH_RE.search(content):
            raise ValueError(f"unsafe generated content: {relative}")
        if _PROTECTED_FIELD_RE.search(content) or _REMOTE_IMAGE_RE.search(content):
            raise ValueError(f"protected or remote generated content: {relative}")
        match = _NOTE_ID_RE.search(content)
        if match:
            properties = _frontmatter_properties(content, relative)
            missing = _REQUIRED_NOTE_PROPERTIES - properties.keys()
            if missing:
                raise ValueError(f"note is missing common properties {sorted(missing)}: {relative}")
            note_id = str(properties["note_id"])
            if note_id in seen_note_ids:
                raise ValueError(f"duplicate note_id: {note_id}")
            seen_note_ids.add(note_id)
            if properties.get("schema_version") != "myis.obsidian-note.v2":
                raise ValueError(f"unsupported note schema: {relative}")
            if properties.get("note_type") not in _ALLOWED_NOTE_TYPES:
                raise ValueError(f"unsupported note_type: {relative}")
            if properties.get("workflow_status") not in _ALLOWED_WORKFLOW_STATUSES:
                raise ValueError(f"unsupported workflow_status: {relative}")
            if properties.get("evidence_maturity") not in _ALLOWED_EVIDENCE_MATURITY:
                raise ValueError(f"unsupported evidence_maturity: {relative}")
            if properties.get("claim_level") not in _ALLOWED_CLAIM_LEVELS:
                raise ValueError(f"unsupported claim_level: {relative}")
            if properties.get("managed_by") != "myis-report" or properties.get("edit_policy") != "generated_do_not_edit":
                raise ValueError(f"generated ownership contract failed: {relative}")
            if not isinstance(properties.get("safe_to_present"), bool):
                raise ValueError(f"safe_to_present must be boolean: {relative}")
            if properties.get("note_type") == "result_report":
                authority = properties.get("current_scientific_authority")
                if not isinstance(authority, bool):
                    raise ValueError(f"result authority must be boolean: {relative}")
                if authority and (
                    properties.get("workflow_status") != "complete"
                    or properties.get("evidence_maturity") != "measured_selection"
                    or properties.get("claim_level") != "descriptive"
                    or not properties.get("source_run_ids")
                    or not properties.get("source_manifest_sha256")
                ):
                    raise ValueError(f"promoted result is missing measured authority bindings: {relative}")
            if properties.get("generated_from_revision") != properties.get("read_model_revision"):
                raise ValueError(f"generated report revision binding mismatch: {relative}")
            if not str(properties.get("last_material_update", "")).strip():
                raise ValueError(f"generated report lifecycle timestamp is missing: {relative}")
            if not str(properties.get("next_authorized_action", "")).strip():
                raise ValueError(f"generated report next action is missing: {relative}")
        for target in _WIKILINK_RE.findall(content):
            target_name = Path(target.replace("\\", "/")).name
            if target_name not in known_links and not target.startswith("80_Owner_Notes/"):
                raise ValueError(f"unresolved wikilink {target}: {relative}")
    if model is not None:
        p2 = model.get("p2_readiness", {}) if isinstance(model.get("p2_readiness"), Mapping) else {}
        fixture = p2.get("fixture_pilot", {}) if isinstance(p2.get("fixture_pilot"), Mapping) else {}
        review = p2.get("official_review", {}) if isinstance(p2.get("official_review"), Mapping) else {}
        if fixture.get("status") == "passed":
            for content in contents.values():
                lowered = content.lower()
                if "fixture remains not executed" in lowered or "which remains not executed" in lowered:
                    raise ValueError("stale fixture narrative contradicts validated fixture status")
        if review.get("final_verdict") == "accept":
            for content in contents.values():
                lowered = content.lower()
                if "official review" in lowered and "pending" in lowered:
                    raise ValueError("stale official review narrative contradicts accepted review")
        if int(p2.get("measured_runs", 0) or 0) == 0:
            for content in contents.values():
                if re.search(r"measured\s+p2[^\n]*(started|running|complete)", content, re.IGNORECASE):
                    raise ValueError("measured P2 narrative contradicts zero measured runs")


def _owner_file_hashes(vault_root: Path) -> dict[str, str]:
    roots = [vault_root / "80_Owner_Notes"]
    roots.extend(sorted((vault_root / "01_Phases").glob("*/Owner_Notes")))
    return {
        path.relative_to(vault_root).as_posix(): sha256(path.read_bytes())
        for owner_root in roots
        if owner_root.is_dir()
        for path in sorted(owner_root.rglob("*"))
        if path.is_file()
    }


def _ensure_owner_boundary(vault_root: Path) -> None:
    owner_root = vault_root / "80_Owner_Notes"
    owner_root.mkdir(parents=True, exist_ok=True)
    readme = owner_root / "README.md"
    if not readme.exists():
        readme.write_text("# Owner Notes\n\nFiles in this directory are never generated or overwritten by `myis-report`.\n", encoding="utf-8")
    for phase in (
        "P0_FOUNDATION", "P1_CPU_BASELINE", "P2_SCOPE_DEVELOPMENT", "P3_FINAL", "P4_PUBLICATION",
        "A0_MIGRATION_FOUNDATION", "A1_BASELINES_AND_MULTI_ARM_SCREENING", "A2_PER_ARM_AUTOINDEX",
        "A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT", "A4_PRODUCTION_TRANSFER_AND_SELECTION",
        "A5_FINAL_CONFIRMATION", "A6_PUBLICATION_AND_RELEASE",
    ):
        (vault_root / "01_Phases" / phase / "Owner_Notes").mkdir(parents=True, exist_ok=True)


def write_projection_reports(
    root: Path,
    model: Mapping[str, Any],
    *,
    mlflow_run_id: str | None = None,
) -> list[Path]:
    """Validate all bytes first, then replace generated targets with rollback."""

    root = root.resolve()
    vault_root = root / VAULT_RELATIVE_PATH
    _ensure_owner_boundary(vault_root)
    owner_before = _owner_file_hashes(vault_root)
    contents = projection_report_contents(root, model, mlflow_run_id=mlflow_run_id)
    previous: dict[Path, bytes | None] = {}
    written: list[Path] = []
    try:
        for target, content in contents.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            previous[target] = target.read_bytes() if target.is_file() else None
            temporary = target.with_suffix(target.suffix + ".tmp")
            temporary.write_text(content, encoding="utf-8", newline="\n")
            temporary.replace(target)
            written.append(target)
    except BaseException:
        for target in reversed(written):
            prior = previous[target]
            if prior is None:
                target.unlink(missing_ok=True)
            else:
                target.write_bytes(prior)
        raise
    if _owner_file_hashes(vault_root) != owner_before:
        raise RuntimeError("Owner-authored files changed during report sync")
    return written


def validate_advisor_update(root: Path) -> dict[str, Any]:
    """Validate the generated draft against the current shared revision before freeze."""

    root = root.resolve()
    model = build_read_model(root)
    validate_read_model(model)
    contents = _obsidian_vault_contents(root, model)
    _validate_generated_contents(contents)
    return {
        "status": "PASS",
        "read_model_revision": model["read_model_revision"],
        "read_model_sha256": model["read_model_sha256"],
        "source_commit": model["source_commit"],
    }


def _write_immutable_snapshot(target: Path, content: str) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    except FileExistsError as error:
        raise ValueError("advisor snapshot already exists and is immutable") from error
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    try:
        target.chmod(stat.S_IREAD)
    except OSError:
        pass
    return target


def present_advisor_update(root: Path, snapshot_id: str) -> Path:
    if not _SNAPSHOT_ID_RE.fullmatch(snapshot_id):
        raise ValueError("snapshot_id must be stable uppercase text")
    root = root.resolve()
    validate_advisor_update(root)
    model = build_read_model(root)
    draft = _obsidian_vault_contents(root, model)[VAULT_RELATIVE_PATH / "02_Advisor_Updates/Drafts/CURRENT_ADVISOR_UPDATE.md"]
    frozen = (
        draft.replace('note_id: "CURRENT-ADVISOR-UPDATE"', f'note_id: "{snapshot_id}"', 1)
        .replace('workflow_status: "verification_needed"', 'workflow_status: "complete"', 1)
        .replace('lifecycle: "draft"', 'lifecycle: "presented"', 1)
        .replace('snapshot_status: "draft"', 'snapshot_status: "presented"', 1)
        .replace("# Advisor Update", f"# Advisor Update {snapshot_id}\n\nThis immutable snapshot was validated before presentation.", 1)
    )
    target = root / VAULT_RELATIVE_PATH / "02_Advisor_Updates/Presented" / f"{snapshot_id}.md"
    return _write_immutable_snapshot(target, frozen)


def correct_advisor_update(root: Path, snapshot_id: str, corrects_snapshot_id: str) -> Path:
    if not _SNAPSHOT_ID_RE.fullmatch(snapshot_id) or not _SNAPSHOT_ID_RE.fullmatch(corrects_snapshot_id):
        raise ValueError("snapshot IDs must be stable uppercase text")
    root = root.resolve()
    original = root / VAULT_RELATIVE_PATH / "02_Advisor_Updates/Presented" / f"{corrects_snapshot_id}.md"
    if not original.is_file():
        raise ValueError("correction target snapshot does not exist")
    original_properties = _frontmatter_properties(original.read_text(encoding="utf-8"), original.relative_to(root))
    if original_properties.get("snapshot_status") not in {"presented", "corrected"}:
        raise ValueError("only a presented snapshot can be corrected")
    validate_advisor_update(root)
    model = build_read_model(root)
    draft = _obsidian_vault_contents(root, model)[VAULT_RELATIVE_PATH / "02_Advisor_Updates/Drafts/CURRENT_ADVISOR_UPDATE.md"]
    correction = (
        draft.replace('note_id: "CURRENT-ADVISOR-UPDATE"', f'note_id: "{snapshot_id}"', 1)
        .replace('workflow_status: "verification_needed"', 'workflow_status: "complete"', 1)
        .replace('lifecycle: "draft"', 'lifecycle: "correction"', 1)
        .replace('snapshot_status: "draft"', 'snapshot_status: "correction"', 1)
        .replace('supersedes: null', f'corrects_snapshot_id: "{corrects_snapshot_id}"', 1)
        .replace("# Advisor Update", f"# Advisor Update Correction {snapshot_id}\n\nCorrects immutable snapshot [[{corrects_snapshot_id}]] without modifying it.", 1)
    )
    target = root / VAULT_RELATIVE_PATH / "02_Advisor_Updates/Presented" / f"{snapshot_id}.md"
    return _write_immutable_snapshot(target, correction)


def _check(root: Path, target: Path, *, read_model_only: bool = False) -> dict[str, Any]:
    if not target.is_file():
        return {"status": "FAIL", "reason": "read_model_missing", "read_model": str(target)}
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
        validate_read_model(payload)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        return {"status": "FAIL", "reason": str(error), "read_model": str(target)}
    expected = build_read_model(root)
    read_model_drift = payload != expected
    report_drift = []
    sync_receipt_error = None
    if not read_model_only:
        for path, content in projection_report_contents(root, expected).items():
            try:
                matches = path.is_file() and path.read_bytes() == content.encode("utf-8")
            except (OSError, UnicodeError):
                matches = False
            if not matches:
                report_drift.append(str(path))
        sync_receipt_error = _validate_sync_receipt(root, expected)
        if sync_receipt_error:
            report_drift.append(str(root / SYNC_RECEIPT_RELATIVE_PATH))
    drift = read_model_drift or bool(report_drift)
    return {
        "status": "FAIL" if drift else "PASS",
        "drift": drift,
        "read_model_drift": read_model_drift,
        "report_drift": report_drift,
        "read_model": str(target),
        "read_model_revision": expected["read_model_revision"],
        "read_model_sha256": expected["read_model_sha256"],
        "sync_receipt_error": sync_receipt_error,
    }


def _validate_sync_receipt(root: Path, model: Mapping[str, Any]) -> str | None:
    path = root / SYNC_RECEIPT_RELATIVE_PATH
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
        archive_text = (root / "mlflow/generated/archive-index.v2.json").read_text(encoding="utf-8")
        manifest = json.loads((root / GENERATED_MANIFEST_RELATIVE_PATH).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "cross-projection receipt or bound projection is missing/invalid"
    required = {
        "schema_version", "projection_schema_version", "read_model_revision",
        "read_model_sha256", "source_commit", "mlflow_run_id",
        "mlflow_archive_sha256", "dashboard_snapshot_sha256",
        "obsidian_manifest_sha256", "source_receipt_uri", "source_receipt_sha256",
        "projection_events", "status",
    }
    if set(receipt) != required or receipt.get("schema_version") != "myis.projection-sync-receipt.v2" or receipt.get("status") != "PASS":
        return "cross-projection receipt contract is invalid"
    expected = {
        "projection_schema_version": model["projection_schema_version"],
        "read_model_revision": model["read_model_revision"],
        "read_model_sha256": model["read_model_sha256"],
        "source_commit": model["source_commit"],
        "dashboard_snapshot_sha256": model["read_model_sha256"],
        "obsidian_manifest_sha256": manifest.get("manifest_sha256"),
        "mlflow_archive_sha256": sha256(archive_text.encode("utf-8")),
    }
    external_outputs = {
        **_brain_report_contents(root, model),
        **_paper_report_contents(root, model),
        **_compatibility_report_contents(root, model),
    }
    expected.update(_a010_projection_lifecycle(
        root,
        model,
        archive_text=archive_text,
        obsidian_manifest_sha256=str(manifest.get("manifest_sha256")),
        external_outputs=external_outputs,
    ))
    if any(receipt.get(key) != value for key, value in expected.items()):
        return "cross-projection receipt does not match the shared revision"
    if not isinstance(receipt.get("mlflow_run_id"), str) or not re.fullmatch(r"[A-Za-z0-9]{16,64}", receipt["mlflow_run_id"]):
        return "cross-projection receipt has no valid MLflow run ID"
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-report")
    parser.add_argument("command", choices=["build", "check", "sync", "advisor-validate", "advisor-present", "advisor-correct"])
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--snapshot-id")
    parser.add_argument("--mlflow-store", type=Path)
    parser.add_argument("--corrects-snapshot-id")
    parser.add_argument("--read-model-only", action="store_true")
    args = parser.parse_args(argv)
    if args.read_model_only and args.command != "check":
        parser.error("--read-model-only is valid only with check")
    root = args.repository_root.resolve()
    target = args.output.resolve() if args.output else root / READ_MODEL_RELATIVE_PATH
    if args.command == "build":
        path = write_read_model(root, target)
        print(json.dumps({"status": "PASS", "read_model": str(path)}, ensure_ascii=True))
        return 0
    if args.command == "advisor-validate":
        print(json.dumps(validate_advisor_update(root), ensure_ascii=True))
        return 0
    if args.command == "advisor-present":
        if not args.snapshot_id:
            parser.error("advisor-present requires --snapshot-id")
        path = present_advisor_update(root, args.snapshot_id)
        print(json.dumps({"status": "PASS", "snapshot": str(path)}, ensure_ascii=True))
        return 0
    if args.command == "advisor-correct":
        if not args.snapshot_id or not args.corrects_snapshot_id:
            parser.error("advisor-correct requires --snapshot-id and --corrects-snapshot-id")
        path = correct_advisor_update(root, args.snapshot_id, args.corrects_snapshot_id)
        print(json.dumps({"status": "PASS", "snapshot": str(path)}, ensure_ascii=True))
        return 0
    if args.command == "sync":
        model = build_read_model(root)
        validate_read_model(model)
        mlflow_run_id = _sync_mlflow_projection(root, model, store_root=args.mlflow_store)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(_json_text(model), encoding="utf-8", newline="\n")
        temporary.replace(target)
        outputs = write_projection_reports(root, model, mlflow_run_id=mlflow_run_id)
        print(json.dumps({"status": "PASS", "read_model": str(target), "report_count": len(outputs), "read_model_revision": model["read_model_revision"], "mlflow_run_id": mlflow_run_id}, ensure_ascii=True))
        return 0
    result = _check(root, target, read_model_only=args.read_model_only)
    print(json.dumps(result, ensure_ascii=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
