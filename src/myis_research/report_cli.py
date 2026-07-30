"""Build and verify the integrated Dashboard, MLflow, and Obsidian projections."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from .projections.read_model import build_read_model, canonical_json, sha256, write_read_model


READ_MODEL_RELATIVE_PATH = Path("projections/read-model/read-model.v2.json")
VAULT_RELATIVE_PATH = Path("obsidian_report")
GENERATED_MANIFEST_RELATIVE_PATH = VAULT_RELATIVE_PATH / "00_System/Generated/generated-manifest.json"
SYNC_RECEIPT_RELATIVE_PATH = Path("projections/sync-receipt.v2.json")
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
_NOTE_ID_RE = re.compile(r"^note_id:\s*([^\r\n]+)$", re.MULTILINE)
_UNSAFE_HTML_RE = re.compile(r"<(?:script|iframe|object|embed|style)\b", re.IGNORECASE)
_ABSOLUTE_PERSONAL_PATH_RE = re.compile(r"[A-Za-z]:[\\/]Users[\\/]", re.IGNORECASE)
_PROTECTED_FIELD_RE = re.compile(
    r"(?:query_ids?|split_membership|per_query(?:_outcomes?)?|raw_provider_payload|"
    r"credentials?|api_keys?)\s*[:=]",
    re.IGNORECASE,
)
_REMOTE_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(https?://", re.IGNORECASE)
_SNAPSHOT_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,63}$")


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


def projection_report_contents(root: Path, model: Mapping[str, Any]) -> dict[Path, str]:
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
        "schema_version": "myis.mlflow-archive-index.v2",
        "projection_schema_version": model["projection_schema_version"],
        "read_model_revision": revision,
        "read_model_sha256": model_sha,
        "source_commit": source_commit,
        "campaign_experiment": "myis-scope-autoindex-v1",
        "system_experiment": "myis-system",
        "run_ids": [item.get("run_id") for item in model.get("runs", [])],
        "evidence_ids": [item.get("evidence_id") for item in model.get("evidence", [])],
        "status": "blocked" if model["project"]["state"] == "P1_BLOCKED_WITH_EVIDENCE" else "current",
    }
    archive_text = _json_text(archive)
    sync_receipt = {
        "schema_version": "myis.projection-sync-receipt.v2",
        "projection_schema_version": model["projection_schema_version"],
        "read_model_revision": revision,
        "read_model_sha256": model_sha,
        "source_commit": source_commit,
        "mlflow_run_id": None,
        "mlflow_archive_sha256": sha256(archive_text.encode("utf-8")),
        "dashboard_snapshot_sha256": model_sha,
        "obsidian_manifest_sha256": manifest["manifest_sha256"],
        "status": "PASS",
    }

    outputs = {
        root / relative: content for relative, content in vault_contents.items()
    }
    outputs[root / GENERATED_MANIFEST_RELATIVE_PATH] = manifest_text
    outputs[root / "mlflow/generated/archive-index.v2.json"] = archive_text
    outputs[root / SYNC_RECEIPT_RELATIVE_PATH] = _json_text(sync_receipt)
    outputs.update(_compatibility_report_contents(root, model))
    return outputs


def _obsidian_vault_contents(root: Path, model: Mapping[str, Any]) -> dict[Path, str]:
    revision = str(model["read_model_revision"])
    common = {
        "read_model_revision": revision,
        "read_model_sha256": model["read_model_sha256"],
        "source_commit": model["source_commit"],
        "projection_schema_version": model["projection_schema_version"],
        "managed_by": "myis-report",
    }
    project = model["project"]
    inbox = model.get("owner_inbox", [])
    next_lines = "\n".join(f"- {item.get('label')}" for item in inbox) or "- ไม่มีรายการ"
    outputs: dict[Path, str] = {}
    outputs[VAULT_RELATIVE_PATH / "HOME.md"] = _note(
        {**common, "note_id": "HOME", "note_type": "home", "status": "blocked" if project["state"] == "P1_BLOCKED_WITH_EVIDENCE" else "current", "evidence_maturity": "not_run", "claim_level": "none"},
        "# myIS Research Report\n\n"
        f"## Current\n\n- Phase: `{project['current_phase']}`\n- Task: `{project['current_task']}`\n- State: **{project['state']}**\n\n"
        f"## Next actions\n\n{next_lines}\n\n"
        "## Navigate\n\n- [[P0_FOUNDATION_MASTER_REPORT]]\n- [[P1_CPU_BASELINE_MASTER_REPORT]]\n- [[CURRENT_ADVISOR_UPDATE]]\n- [[LITERATURE_INDEX]]\n- [[RESEARCH_HISTORY_INDEX]]\n",
    )

    for phase in model.get("phases", []):
        phase_id = str(phase["phase_id"])
        phase_folder = VAULT_RELATIVE_PATH / "01_Phases" / phase_id
        task_rows = "\n".join(
            f"| [[{task['task_id']}]] | {task['title']} | {task['status']} | {', '.join(task.get('evidence_ids', [])) or 'none'} |"
            for task in phase.get("tasks", [])
        ) or "| none | none | planned | none |"
        phase_body = (
            f"# {phase_id}\n\n## Status\n\n**{phase['status']}**\n\n"
            "## Tasks\n\n| Task | Work | Status | Evidence |\n|---|---|---|---|\n"
            f"{task_rows}\n\n## Output\n\nGenerated task records only.\n\n"
            "## Result\n\n[[P1_CPU_BASELINE_RESULT]]\n\n"
            "## Interpretation\n\nNo scientific interpretation is promoted without validated evidence.\n\n"
            f"## Revision\n\n`{revision}`\n"
        )
        outputs[phase_folder / f"{phase_id}_MASTER_REPORT.md"] = _note(
            {**common, "note_id": f"{phase_id}-MASTER", "note_type": "phase_master", "phase_id": phase_id, "status": phase["status"], "evidence_maturity": "not_run" if phase["status"] in {"blocked", "planned"} else "validated", "claim_level": "none"},
            phase_body,
        )
        for task in phase.get("tasks", []):
            task_id = str(task["task_id"])
            body = (
                f"# {task_id}: {task['title']}\n\n"
                f"## Status\n\n**{task['status']}**\n\n"
                "## Output\n\nOutput pointers come from the shared read model.\n\n"
                "## Result\n\nNo result is rendered unless acceptance evidence is valid.\n\n"
                "## Interpretation\n\nBlocked or pending review.\n\n"
                f"## Phase\n\n[[{phase_id}_MASTER_REPORT]]\n"
            )
            outputs[phase_folder / "Tasks" / f"{task_id}.md"] = _note(
                {**common, "note_id": task_id, "note_type": "task", "phase_id": phase_id, "task_id": task_id, "status": task["status"], "evidence_maturity": "validated" if task.get("evidence_ids") else "not_run", "claim_level": "none"},
                body,
            )

    result = model.get("results", [{}])[0]
    outputs[VAULT_RELATIVE_PATH / "03_Results/Current/P1_CPU_BASELINE_RESULT.md"] = _note(
        {**common, "note_id": "P1-CPU-BASELINE-RESULT", "note_type": "result", "phase_id": "P1_CPU_BASELINE", "task_id": "P1.3", "status": result.get("validity", "blocked"), "evidence_maturity": result.get("evidence_maturity", "not_run"), "claim_level": "none" if result.get("validity") != "valid" else "aggregate"},
        "# P1 CPU Baseline Result\n\n## Output\n\nAggregate receipt is present but unpromoted.\n\n"
        f"## Result\n\nValidity: **{result.get('validity', 'blocked')}**\n\n"
        "## Interpretation\n\nNo measured claim is available while the four-slot evidence matrix is missing.\n\n"
        "## What we can say\n\nThe integration and evidence-recovery work is active.\n\n"
        "## What we must not say\n\nP1 is not measured complete and final-872 is not globally untouched.\n",
    )

    outputs[VAULT_RELATIVE_PATH / "02_Advisor_Updates/Drafts/CURRENT_ADVISOR_UPDATE.md"] = _note(
        {**common, "note_id": "CURRENT-ADVISOR-UPDATE", "note_type": "advisor_update", "status": "draft", "evidence_maturity": "not_run", "claim_level": "none", "lifecycle": "draft", "supersedes": None},
        "# Advisor Update\n\n## Current state\n\nP1 is blocked with evidence recovery in progress.\n\n"
        "## What we can say\n\nThe control plane and safe aggregate receipt exist.\n\n"
        "## What we must not say\n\nNo measured-complete or final-split claim.\n\n"
        "## Evidence ledger\n\n- [[P1_CPU_BASELINE_RESULT]]\n\n"
        "## Q&A\n\n- Why blocked? Canonical four-slot manifests and validation reports are absent.\n\n"
        "## Presentation flow\n\n1. Research question\n2. Current evidence boundary\n3. Next reversible action\n",
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
        domain = urlparse(row.get("source_url", "")).netloc or "local"
        body = (
            f"# {title}\n\n## Why it matters to myIS\n\nLiterature proxy for {theme}.\n\n"
            f"## Key takeaway\n\nSee the canonical digest `{digest_uri}`.\n\n"
            f"## Supports / challenges\n\nSupports the evidence map for [[{task_id}]].\n\n"
            f"## Used in\n\n[[{task_id}]] and [[P1_CPU_BASELINE_RESULT]].\n\n"
            f"## Citation status\n\nTier {row.get('tier') or 'unassigned'}; source domain `{domain}`.\n\n"
            f"## Canonical digest\n\n`{digest_uri}`\n"
        )
        outputs[VAULT_RELATIVE_PATH / "04_Literature_Map/Papers" / f"{paper_id}.md"] = _note(
            {**common, "note_id": f"LIT-{paper_id}", "note_type": "literature", "status": "current", "evidence_maturity": "historical", "claim_level": "supporting", "paper_id": paper_id, "source_sha256": row.get("sha256", ""), "theme": theme, "task_id": task_id},
            body,
        )
        links.append(f"- [[{paper_id}]] - {title}")
    outputs[VAULT_RELATIVE_PATH / "04_Literature_Map/LITERATURE_INDEX.md"] = _note(
        {**common, "note_id": "LITERATURE-INDEX", "note_type": "literature_map", "status": "current", "evidence_maturity": "historical", "claim_level": "supporting", "paper_count": len(links)},
        "# Literature Map\n\n" + "\n".join(links) + "\n",
    )


def _add_history_outputs(common: Mapping[str, Any], outputs: dict[Path, str]) -> None:
    links = []
    for paper in ("A", "B", "C", "D"):
        note_id = f"HISTORY-PAPER-{paper}"
        exposure = "historical_exposed" if paper in {"A", "B", "D"} else "historical_unverified"
        outputs[VAULT_RELATIVE_PATH / "05_Research_History" / f"Paper_{paper}.md"] = _note(
            {**common, "note_id": note_id, "note_type": "research_history", "status": "historical", "evidence_maturity": "historical", "claim_level": "none", "exposure_status": exposure},
            f"# Paper {paper}\n\nStatus: **{exposure}**\n\nThis note is historical evidence and cannot override current P0-P4 run facts.\n",
        )
        links.append(f"- [[Paper_{paper}]] - {exposure}")
    outputs[VAULT_RELATIVE_PATH / "05_Research_History/RESEARCH_HISTORY_INDEX.md"] = _note(
        {**common, "note_id": "RESEARCH-HISTORY-INDEX", "note_type": "research_history", "status": "historical", "evidence_maturity": "historical", "claim_level": "none"},
        "# Research History\n\n" + "\n".join(links) + "\n",
    )


def _add_system_outputs(common: Mapping[str, Any], outputs: dict[Path, str]) -> None:
    outputs[VAULT_RELATIVE_PATH / "06_Decisions_Risks/RAID.md"] = _note(
        {**common, "note_id": "RAID", "note_type": "raid", "status": "current", "evidence_maturity": "not_run", "claim_level": "none"},
        "# RAID\n\n- Risk: P1 evidence matrix is incomplete.\n- Decision: D2 and D3 remain Owner-only.\n",
    )
    bases = {
        "phases.base": "phase_id",
        "tasks.base": "task_id",
        "results.base": "result_id",
        "literature.base": "paper_id",
        "advisor-updates.base": "lifecycle",
        "decisions-risks.base": "note_type",
    }
    for name, group in bases.items():
        outputs[VAULT_RELATIVE_PATH / "10_Bases" / name] = (
            "filters:\n  and:\n    - 'managed_by == \"myis-report\"'\n"
            f"groupBy:\n  property: {group}\nviews:\n  - type: table\n    name: Current\n"
        )
    outputs[VAULT_RELATIVE_PATH / "70_Templates/OWNER_NOTE_TEMPLATE.md"] = (
        "---\nmanaged_by: owner\nnote_type: owner_note\n---\n\n# Owner Note\n"
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


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def _validate_generated_contents(contents: Mapping[Path, str]) -> None:
    seen_note_ids: set[str] = set()
    for relative, content in contents.items():
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"generated path escapes repository: {relative}")
        if _UNSAFE_HTML_RE.search(content) or _ABSOLUTE_PERSONAL_PATH_RE.search(content):
            raise ValueError(f"unsafe generated content: {relative}")
        if _PROTECTED_FIELD_RE.search(content) or _REMOTE_IMAGE_RE.search(content):
            raise ValueError(f"protected or remote generated content: {relative}")
        match = _NOTE_ID_RE.search(content)
        if match:
            note_id = match.group(1).strip().strip('"')
            if note_id in seen_note_ids:
                raise ValueError(f"duplicate note_id: {note_id}")
            seen_note_ids.add(note_id)


def _owner_file_hashes(vault_root: Path) -> dict[str, str]:
    owner_root = vault_root / "80_Owner_Notes"
    if not owner_root.is_dir():
        return {}
    return {
        path.relative_to(owner_root).as_posix(): sha256(path.read_bytes())
        for path in sorted(owner_root.rglob("*"))
        if path.is_file()
    }


def _ensure_owner_boundary(vault_root: Path) -> None:
    owner_root = vault_root / "80_Owner_Notes"
    owner_root.mkdir(parents=True, exist_ok=True)
    readme = owner_root / "README.md"
    if not readme.exists():
        readme.write_text("# Owner Notes\n\nFiles in this directory are never generated or overwritten by `myis-report`.\n", encoding="utf-8")


def write_projection_reports(root: Path, model: Mapping[str, Any]) -> list[Path]:
    """Validate all bytes first, then replace generated targets with rollback."""

    root = root.resolve()
    vault_root = root / VAULT_RELATIVE_PATH
    _ensure_owner_boundary(vault_root)
    owner_before = _owner_file_hashes(vault_root)
    contents = projection_report_contents(root, model)
    previous: dict[Path, bytes | None] = {}
    written: list[Path] = []
    try:
        for target, content in contents.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            previous[target] = target.read_bytes() if target.is_file() else None
            temporary = target.with_suffix(target.suffix + ".tmp")
            temporary.write_text(content, encoding="utf-8")
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


def present_advisor_update(root: Path, snapshot_id: str) -> Path:
    if not _SNAPSHOT_ID_RE.fullmatch(snapshot_id):
        raise ValueError("snapshot_id must be stable uppercase text")
    root = root.resolve()
    model = build_read_model(root)
    validate_read_model(model)
    draft = _obsidian_vault_contents(root, model)[VAULT_RELATIVE_PATH / "02_Advisor_Updates/Drafts/CURRENT_ADVISOR_UPDATE.md"]
    frozen = draft.replace('"draft"', '"presented"', 2).replace('note_id: "CURRENT-ADVISOR-UPDATE"', f'note_id: "{snapshot_id}"', 1)
    target = root / VAULT_RELATIVE_PATH / "02_Advisor_Updates/Presented" / f"{snapshot_id}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(frozen)
    return target


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
            matches = path.is_file() and path.read_text(encoding="utf-8") == content
        except (OSError, UnicodeError):
            matches = False
        if not matches:
            report_drift.append(str(path))
    drift = read_model_drift or bool(report_drift)
    return {
        "status": "FAIL" if drift else "PASS",
        "drift": drift,
        "read_model_drift": read_model_drift,
        "report_drift": report_drift,
        "read_model": str(target),
        "read_model_revision": expected["read_model_revision"],
        "read_model_sha256": expected["read_model_sha256"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-report")
    parser.add_argument("command", choices=["build", "check", "sync", "advisor-present"])
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--snapshot-id")
    args = parser.parse_args(argv)
    root = args.repository_root.resolve()
    target = args.output.resolve() if args.output else root / READ_MODEL_RELATIVE_PATH
    if args.command == "build":
        path = write_read_model(root, target)
        print(json.dumps({"status": "PASS", "read_model": str(path)}, ensure_ascii=True))
        return 0
    if args.command == "advisor-present":
        if not args.snapshot_id:
            parser.error("advisor-present requires --snapshot-id")
        path = present_advisor_update(root, args.snapshot_id)
        print(json.dumps({"status": "PASS", "snapshot": str(path)}, ensure_ascii=True))
        return 0
    if args.command == "sync":
        model = build_read_model(root)
        validate_read_model(model)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(_json_text(model), encoding="utf-8")
        temporary.replace(target)
        outputs = write_projection_reports(root, model)
        print(json.dumps({"status": "PASS", "read_model": str(target), "report_count": len(outputs), "read_model_revision": model["read_model_revision"]}, ensure_ascii=True))
        return 0
    result = _check(root, target)
    print(json.dumps(result, ensure_ascii=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
