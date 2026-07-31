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
    "decision", "risk", "failed_attempt", "presentation", "glossary", "owner_note",
})
_ALLOWED_WORKFLOW_STATUSES = frozenset({
    "waiting_dependency", "ready", "in_progress", "verification_needed",
    "waiting_gate", "blocked", "complete",
})
_ALLOWED_EVIDENCE_MATURITY = frozenset({
    "non_scientific", "fixture", "dry_run", "measured_development",
    "measured_selection", "confirmatory", "publication", "historical_exposed",
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
    _validate_generated_contents(vault_contents)
    manifest = _generated_manifest(model, vault_contents)
    manifest_text = _json_text(manifest)

    archive = {
        **_mlflow_archive_index(model),
        "dashboard_snapshot_sha256": model_sha,
        "obsidian_manifest_sha256": manifest["manifest_sha256"],
    }
    archive_text = _json_text(archive)

    outputs = {
        root / relative: content for relative, content in vault_contents.items()
    }
    outputs[root / GENERATED_MANIFEST_RELATIVE_PATH] = manifest_text
    outputs[root / "mlflow/generated/archive-index.v2.json"] = archive_text
    if mlflow_run_id is not None:
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
            "status": "PASS",
        })
    external_outputs = {
        **_brain_report_contents(root, model),
        **_paper_report_contents(root, model),
        **_compatibility_report_contents(root, model),
    }
    _validate_external_projection_contents(external_outputs)
    outputs.update(external_outputs)
    return outputs


def _mlflow_archive_index(model: Mapping[str, Any]) -> dict[str, Any]:
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
    evaluator_path = root / "src/myis_research/report_cli.py"
    environment_path = root / "uv.lock"
    for path in (schema_path, campaign_path, envelope_path, evaluator_path, environment_path):
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"MLflow projection source is missing or unsafe: {path.relative_to(root)}")

    schema_registry = RegistrySnapshot(
        schema_version=SCHEMA_REGISTRY_SCHEMA,
        registry_kind="schema",
        items=({"id": "read-model.v2", "sha256": sha256(schema_path.read_bytes())},),
    )
    rule_registry = RegistrySnapshot(
        schema_version=RULE_REGISTRY_SCHEMA,
        registry_kind="rule",
        items=(
            {"id": "scope-autoindex-v1", "sha256": sha256(campaign_path.read_bytes())},
            {"id": "execution-envelope", "sha256": sha256(envelope_path.read_bytes())},
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


def _obsidian_vault_contents(root: Path, model: Mapping[str, Any]) -> dict[Path, str]:
    revision = str(model["read_model_revision"])
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
        _p1_home_body(model, next_lines),
    )

    for phase in model.get("phases", []):
        phase_id = str(phase["phase_id"])
        phase_folder = VAULT_RELATIVE_PATH / "01_Phases" / phase_id
        task_rows = "\n".join(
            f"| [[{task['task_id']}]] | {task['title']} | {_workflow_status(task['status'])} | {', '.join(task.get('evidence_ids', [])) or 'not measured'} |"
            for task in phase.get("tasks", [])
        ) or "| none | none | planned | none |"
        phase_body = _p1_phase_body(model, phase, revision) if phase_id == "P1_CPU_BASELINE" else (
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
        )
        outputs[phase_folder / f"{phase_id}_MASTER_REPORT.md"] = _note(
            {**common, "note_id": f"{phase_id}-MASTER", "note_type": "phase_report", "phase_id": phase_id, "task_id": None, "workflow_status": _workflow_status(phase["status"]), "evidence_maturity": "measured_selection" if phase_id == "P1_CPU_BASELINE" and _p1_measured(model) else "non_scientific" if phase["status"] in {"blocked", "planned", "blocked_until_p1", "locked_until_D2", "locked_until_D3"} else "measured_development", "claim_level": "descriptive" if phase_id == "P1_CPU_BASELINE" and _p1_measured(model) else "none", "source_run_ids": p1_run_ids if phase_id == "P1_CPU_BASELINE" else [], "source_manifest_sha256": p1_manifest_hashes if phase_id == "P1_CPU_BASELINE" else []},
            phase_body,
        )
        for task in phase.get("tasks", []):
            task_id = str(task["task_id"])
            body = _p1_task_body(model, phase_id, task) if phase_id == "P1_CPU_BASELINE" else (
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
            )
            outputs[phase_folder / "Tasks" / f"{task_id}.md"] = _note(
                {**common, "note_id": task_id, "note_type": "task_report", "phase_id": phase_id, "task_id": task_id, "workflow_status": _workflow_status(task["status"]), "evidence_maturity": "measured_selection" if phase_id == "P1_CPU_BASELINE" and _p1_measured(model) else "measured_development" if task.get("evidence_ids") else "non_scientific", "claim_level": "descriptive" if phase_id == "P1_CPU_BASELINE" and _p1_measured(model) else "none", "source_run_ids": p1_run_ids if phase_id == "P1_CPU_BASELINE" else [], "source_manifest_sha256": p1_manifest_hashes if phase_id == "P1_CPU_BASELINE" else []},
                body,
            )

    result = model.get("results", [{}])[0]
    outputs[VAULT_RELATIVE_PATH / "03_Results/Current/P1_CPU_BASELINE_RESULT.md"] = _note(
        {**common, "note_id": "P1-CPU-BASELINE-RESULT", "note_type": "result_report", "phase_id": "P1_CPU_BASELINE", "task_id": "P1.3", "workflow_status": "complete" if _p1_measured(model) else "blocked", "evidence_maturity": "measured_selection" if _p1_measured(model) else "historical_exposed", "claim_level": "descriptive" if _p1_measured(model) else "none", "result_id": result.get("result_id", "P1-CPU-BASELINE"), "current_scientific_authority": _p1_measured(model), "source_run_ids": p1_run_ids, "source_manifest_sha256": p1_manifest_hashes},
        _p1_result_body(model),
    )

    outputs[VAULT_RELATIVE_PATH / "02_Advisor_Updates/Drafts/CURRENT_ADVISOR_UPDATE.md"] = _note(
        {**common, "note_id": "CURRENT-ADVISOR-UPDATE", "note_type": "advisor_update", "phase_id": "P1_CPU_BASELINE", "task_id": "P1.3", "workflow_status": "verification_needed", "evidence_maturity": "measured_selection" if _p1_measured(model) else "non_scientific", "claim_level": "descriptive" if _p1_measured(model) else "none", "lifecycle": "draft", "snapshot_status": "draft", "supersedes": None, "source_run_ids": p1_run_ids, "source_manifest_sha256": p1_manifest_hashes},
        _p1_advisor_body(model),
    )

    _add_literature_outputs(root, model, common, outputs)
    _add_history_outputs(common, outputs)
    _add_system_outputs(model, common, outputs)
    return outputs


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

    phase_lines: list[str] = []
    for phase in phases:
        phase_lines.append(f"- **{phase['phase_id']}**: {phase['status']}")
        for task in phase.get("tasks", []):
            phase_lines.append(
                f"  - `{task['task_id']}` {task['title']}: **{task['status']}**"
            )
    status_body = (
        "# Program Status / สถานะโครงการ\n\n"
        f"State: **{state}**\n\n"
        + "\n".join(f"- **{phase['phase_id']}**: {phase['status']}" for phase in phases)
        + "\n\n## Resource boundary\n\n"
        f"- CPU-only: `{model['resources']['cpu_only']}`\n"
        f"- GPU used: `{model['resources']['gpu']}`\n"
        f"- Paid API used: `{model['resources']['paid_api']}`\n"
        f"- Actual cost USD: `{model['resources']['actual_cost_usd']}`\n\n"
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
        "## Next automatic action\n\n"
        "P2 is ready but not started. Keep work reversible and CPU-only until a separate P2 action begins; "
        "D2 and D3 remain unchanged.\n"
    )

    moc_body = (
        "# myIS Research MOC\n\n"
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
    lines = ["| Check | Status | Canonical source |", "|---|---|---|"]
    for check in readiness.get("checks", []):
        lines.append(f"| `{check['id']}` | **{check['status']}** | `{check['source']}` |")
    body = (
        "# Publication Readiness\n\n"
        f"Program state: **{model['project']['state']}**\n\n"
        f"Publication status: **{readiness.get('status', 'unknown')}**\n\n"
        + "\n".join(lines)
        + "\n\nP1 contains measured train/selection evidence only. D2 and D3 remain Owner-only, "
        "and this projection does not authorize final evaluation or release.\n"
    )
    source_lock = {
        "schema_version": "myis.publication-source-lock.v2",
        "research_repository": "../01_Research",
        "campaign_id": model["project"]["campaign_id"],
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
        "complete": "complete",
        "measured": "complete",
        "blocked": "blocked",
        "blocked_until_p1": "waiting_dependency",
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


def _validate_generated_contents(contents: Mapping[Path, str]) -> None:
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
        for target in _WIKILINK_RE.findall(content):
            target_name = Path(target.replace("\\", "/")).name
            if target_name not in known_links and not target.startswith("80_Owner_Notes/"):
                raise ValueError(f"unresolved wikilink {target}: {relative}")


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
    for phase in ("P0_FOUNDATION", "P1_CPU_BASELINE", "P2_SCOPE_DEVELOPMENT", "P3_FINAL", "P4_PUBLICATION"):
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
        "obsidian_manifest_sha256", "status",
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
