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
    outputs.update(_compatibility_report_contents(root, model))
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
    freeze = FreezeBundle(
        freeze_id=f"freeze-projection-{str(model['read_model_revision'])[:16]}",
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
        environment_lock_sha256=sha256(environment_path.read_bytes()),
    )
    archive_text = _json_text(archive_index)
    run = ArchiveRun(
        run_id=f"projection-sync-v3-{str(model['read_model_revision'])[:20]}",
        phase_id="P0_FOUNDATION",
        task_id="P0.3",
        run_kind="projection_sync",
        git_commit=str(model["source_commit"]),
        manifest_sha256=str(model["read_model_sha256"]),
        receipt_sha256=sha256(archive_text.encode("utf-8")),
        dataset_lineage_sha256=sha256(canonical_json(model.get("datasets", []))),
        config_sha256=sha256(campaign_path.read_bytes()),
        evaluator_sha256=evaluator_sha,
        environment_sha256=sha256(environment_path.read_bytes()),
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
    outputs: dict[Path, str] = {}
    outputs[VAULT_RELATIVE_PATH / "HOME.md"] = _note(
        {**common, "note_id": "HOME", "note_type": "home", "phase_id": project["current_phase"], "task_id": project["current_task"], "workflow_status": "blocked" if project["state"] == "P1_BLOCKED_WITH_EVIDENCE" else "in_progress", "evidence_maturity": "non_scientific", "claim_level": "none"},
        "# myIS Research Report\n\n"
        "Generated from validated evidence. Manual edits may be replaced. Add personal comments in the linked Owner Note.\n\n"
        "## Thesis\n\nCan a patent-native grounded representation compiler improve family-level DAPFAM retrieval while the retriever, evaluator, and budget remain fixed?\n\n"
        f"## Current Phase and Task\n\n- Phase: `{project['current_phase']}`\n- Task: `{project['current_task']}`\n- State: **{project['state']}**\n\n"
        f"## Next actions\n\n{next_lines}\n\n"
        "## Latest valid result\n\nNo validated measured result is available. The retained aggregate receipt is historical-invalid and cannot be promoted.\n\n"
        "## What we must not say\n\nP1 is not measured complete; final-872 cannot be claimed globally untouched.\n\n"
        "## Navigate\n\n- [[P0_FOUNDATION_MASTER_REPORT]]\n- [[P1_CPU_BASELINE_MASTER_REPORT]]\n- [[CURRENT_ADVISOR_UPDATE]]\n- [[LITERATURE_INDEX]]\n- [[RESEARCH_HISTORY_INDEX]]\n",
    )

    for phase in model.get("phases", []):
        phase_id = str(phase["phase_id"])
        phase_folder = VAULT_RELATIVE_PATH / "01_Phases" / phase_id
        task_rows = "\n".join(
            f"| [[{task['task_id']}]] | {task['title']} | {_workflow_status(task['status'])} | {', '.join(task.get('evidence_ids', [])) or 'not measured'} |"
            for task in phase.get("tasks", [])
        ) or "| none | none | planned | none |"
        phase_body = (
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
            {**common, "note_id": f"{phase_id}-MASTER", "note_type": "phase_report", "phase_id": phase_id, "task_id": None, "workflow_status": _workflow_status(phase["status"]), "evidence_maturity": "non_scientific" if phase["status"] in {"blocked", "planned", "blocked_until_p1", "locked_until_D2", "locked_until_D3"} else "measured_development", "claim_level": "none"},
            phase_body,
        )
        for task in phase.get("tasks", []):
            task_id = str(task["task_id"])
            body = (
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
                {**common, "note_id": task_id, "note_type": "task_report", "phase_id": phase_id, "task_id": task_id, "workflow_status": _workflow_status(task["status"]), "evidence_maturity": "measured_development" if task.get("evidence_ids") else "non_scientific", "claim_level": "none"},
                body,
            )

    result = model.get("results", [{}])[0]
    outputs[VAULT_RELATIVE_PATH / "03_Results/Current/P1_CPU_BASELINE_RESULT.md"] = _note(
        {**common, "note_id": "P1-CPU-BASELINE-RESULT", "note_type": "result_report", "phase_id": "P1_CPU_BASELINE", "task_id": "P1.3", "workflow_status": "blocked", "evidence_maturity": "historical_exposed", "claim_level": "none", "result_id": result.get("result_id", "P1-CPU-BASELINE"), "current_scientific_authority": False, "source_manifest_sha256": []},
        "# P1 CPU Baseline Result\n\nGenerated from validated evidence. Manual edits may be replaced.\n\n"
        "## Output\n\nAn aggregate receipt exists, but its explicit historical-invalid disposition prevents promotion.\n\n"
        f"## Result\n\nValidity: **{result.get('validity', 'blocked')}**. No validated measured value is available.\n\n"
        "## Interpretation\n\nNo measured claim is available while the hash-bound four-slot evidence matrix is missing.\n\n"
        "## What we can say\n\nThe integration and evidence-recovery work is active and historical evidence remains traceable.\n\n"
        "## What we must not say\n\nP1 is not measured complete and final-872 is not globally untouched.\n\n"
        "## Evidence and audit details\n\n[[P1.3]]\n",
    )

    outputs[VAULT_RELATIVE_PATH / "02_Advisor_Updates/Drafts/CURRENT_ADVISOR_UPDATE.md"] = _note(
        {**common, "note_id": "CURRENT-ADVISOR-UPDATE", "note_type": "advisor_update", "phase_id": "P1_CPU_BASELINE", "task_id": "P1.3", "workflow_status": "verification_needed", "evidence_maturity": "non_scientific", "claim_level": "none", "lifecycle": "draft", "snapshot_status": "draft", "supersedes": None},
        "# Advisor Update\n\nGenerated draft. Owner edits belong in a separate meeting note; this draft is rebuilt from the shared revision.\n\n"
        "## One-paragraph summary\n\nP1 is blocked with evidence recovery in progress; no measured or final-split conclusion is available.\n\n"
        "## Plain-language primer\n\nA measured claim requires a hash-bound manifest and validation evidence, not merely an aggregate receipt.\n\n"
        "## Current Phase/Task\n\n[[P1_CPU_BASELINE_MASTER_REPORT]] and [[P1.3]].\n\n"
        "## Evidence ledger\n\n- [[P1_CPU_BASELINE_RESULT]]\n\n"
        "## Main outputs\n\nThe read model records a safe historical-invalid disposition.\n\n"
        "## Measured result\n\nNo validated measured result.\n\n"
        "## Interpretation\n\nThe current evidence blocks promotion, which is a valid governance outcome.\n\n"
        "## Gate/decision\n\nD2 and D3 remain Owner-only.\n\n"
        "## What we can say\n\nThe control plane and safe aggregate receipt exist.\n\n"
        "## What we must not say\n\nNo measured-complete or final-split claim.\n\n"
        "## Risks and blockers\n\n[[RAID]]\n\n"
        "## Questions for advisor\n\nWhat evidence-recovery framing is most useful before a fresh Owner-local P1 run?\n\n"
        "## Recommended next action\n\nReview the recovery freeze, then authorize only the existing Owner-local P1 workflow when ready.\n\n"
        "## Advisor Q&A preparation\n\nWhy blocked? Canonical four-slot manifests and validation reports are absent.\n\n"
        "## Suggested visual story\n\n1. Research question\n2. Current evidence boundary\n3. Next reversible action\n\n"
        "## Literature used\n\n[[LITERATURE_INDEX]]\n",
    )

    _add_literature_outputs(root, model, common, outputs)
    _add_history_outputs(common, outputs)
    _add_system_outputs(common, outputs)
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


def _add_system_outputs(common: Mapping[str, Any], outputs: dict[Path, str]) -> None:
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
        {**common, "note_id": "RAID", "note_type": "risk", "phase_id": "P1_CPU_BASELINE", "task_id": "P1.3", "workflow_status": "blocked", "evidence_maturity": "non_scientific", "claim_level": "none", "raid_id": "RISK-P1-EVIDENCE-MATRIX", "raid_type": "risk", "raid_status": "open"},
        "# RAID\n\n- Risk: P1 evidence matrix is incomplete.\n- Decision: D2 and D3 remain Owner-only.\n",
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


def _compatibility_report_contents(root: Path, model: Mapping[str, Any]) -> dict[Path, str]:
    revision = str(model["read_model_revision"])
    state = str(model["project"]["state"])
    phases = "\n".join(f"- **{phase['phase_id']}**: {phase['status']}" for phase in model.get("phases", []))
    content = f"---\nread_model_revision: {revision}\nmanaged_by: myis-report\n---\n\n# Program Status\n\nState: **{state}**\n\n{phases}\n"
    brain = (root.parent / "02_Brain/reports/generated/program-status.md").resolve()
    paper = (root.parent / "03_Paper/publications/isai-nlp-2026/generated/publication-readiness.md").resolve()
    legacy = root / "projections/obsidian/generated/program-status.md"
    return {brain: content, paper: content, legacy: content}


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
            if properties.get("note_type") == "result_report" and properties.get("current_scientific_authority") is not False:
                raise ValueError(f"unpromoted result must be non-authoritative: {relative}")
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


def _check(root: Path, target: Path) -> dict[str, Any]:
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
    args = parser.parse_args(argv)
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
    result = _check(root, target)
    print(json.dumps(result, ensure_ascii=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
