"""Build the canonical read model and safe cross-repository reports."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from .projections.read_model import write_read_model, build_read_model, canonical_json, sha256


REQUIRED_READ_MODEL_KEYS = {
    "schema_version", "projection_revision", "generated_at", "campaigns",
    "phases", "tasks", "gates", "experiments", "runs", "metrics", "cost",
    "decisions", "evidence", "publication_readiness",
}


def validate_read_model(model: dict) -> None:
    """Fail closed when a projection writer emits an incomplete read model."""
    missing = REQUIRED_READ_MODEL_KEYS.difference(model)
    if missing:
        raise ValueError(f"read model is missing required keys: {sorted(missing)}")
    if model.get("schema_version") != "myis.read-model.v1":
        raise ValueError("read model schema_version is invalid")
    revision = model.get("projection_revision")
    if not isinstance(revision, str) or not re.fullmatch(r"[a-f0-9]{64}", revision):
        raise ValueError("read model projection_revision must be SHA-256")
    if not isinstance(model.get("phases"), list) or not isinstance(model.get("tasks"), list):
        raise ValueError("read model phases/tasks must be arrays")
    gate_ids = {str(item.get("gate_id")) for item in model.get("gates", []) if isinstance(item, dict)}
    if gate_ids != {"D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"}:
        raise ValueError("read model must expose exactly D2 and D3 decisions")


def write_projection_reports(root: Path, model: dict) -> list[Path]:
    """Atomically regenerate Brain and Paper text projections from one model."""
    outputs: list[Path] = []
    # Bind reports to the stable read-model revision, excluding generation time.
    source_sha = str(model.get("projection_revision") or sha256(canonical_json({key: value for key, value in model.items() if key != "generated_at"})))
    campaign = model.get("campaigns", [{}])[0]
    readiness = model.get("publication_readiness", {})
    validate_read_model(model)
    brain_root = (root.parent / "02_Brain" / "reports" / "generated").resolve()
    brain_root.mkdir(parents=True, exist_ok=True)
    def docs_for(source_path: str, *, memory_link: str, literature_link: str) -> dict[str, str]:
        return {
        "program-status.md": f"---\nsource: {source_path}\nsource_sha256: {source_sha}\n---\n\n# Program Status\n\n- Campaign: `{campaign.get('campaign_id', 'unknown')}`\n- Phase status: **{campaign.get('status', 'unknown')}**\n- Runs: {len(model.get('runs', []))}\n- Evidence pointers: {len(model.get('evidence', []))}\n",
        "experiments.md": f"---\nsource_sha256: {source_sha}\n---\n\n# Experiments\n\n| Experiment | Runs |\n|---|---:|\n" + "".join(f"| `{item.get('experiment_id')}` | {item.get('run_count', 0)} |\n" for item in model.get('experiments', [])),
        "publication-readiness.md": f"---\nsource_sha256: {source_sha}\n---\n\n# Publication Readiness\n\nStatus: **{readiness.get('status', 'blocked')}**\n\n" + "".join(f"- {check.get('id')}: **{check.get('status')}**\n" for check in readiness.get('checks', [])),
        "weekly-summary.md": f"---\nsource_sha256: {source_sha}\n---\n\n# Weekly Summary\n\nGenerated from the canonical read model. No manual metric entry is allowed here.\n",
        "phase-task-status.md": "---\nsource_sha256: " + source_sha + "\n---\n\n# Phase / Task Status\n\n" + "\n".join(
            f"- **{phase.get('phase_id')}**: {phase.get('status')}\n" + "\n".join(f"  - `{task.get('task_id')}` {task.get('title')}: **{task.get('status')}**" for task in phase.get('tasks', []))
            for phase in model.get('phases', [])
        ),
        "MOC.md": f"---\nsource: {source_path}\nsource_sha256: {source_sha}\n---\n\n# myIS Research MOC\n\n- [[program-status]]\n- [[phase-task-status]]\n- [[experiments]]\n- [[publication-readiness]]\n- [[weekly-summary]]\n\n## Backlinks\n\n- [[{memory_link}]]\n- [[{literature_link}]]\n\nSource revision: `{source_sha}`\n",
        }
    brain_docs = docs_for(
        "../../../01_Research/projections/read-model/read-model.v1.json",
        memory_link="../../memory/MOC",
        literature_link="../../reference/Literature/Literature Index",
    )
    for name, content in brain_docs.items():
        target = brain_root / name
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(target)
        outputs.append(target)
    obsidian_root = root / "projections" / "obsidian" / "generated"
    obsidian_root.mkdir(parents=True, exist_ok=True)
    obsidian_docs = docs_for(
        "../../read-model/read-model.v1.json",
        memory_link="../../../02_Brain/memory/MOC",
        literature_link="../../../02_Brain/reference/Literature/Literature Index",
    )
    for name, content in obsidian_docs.items():
        target = obsidian_root / name
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(target)
        outputs.append(target)
    paper_root = (root.parent / "03_Paper" / "publications" / "isai-nlp-2026" / "generated").resolve()
    paper_root.mkdir(parents=True, exist_ok=True)
    paper_readiness = paper_root / "publication-readiness.md"
    tmp = paper_readiness.with_suffix(".md.tmp")
    tmp.write_text(obsidian_docs["publication-readiness.md"], encoding="utf-8")
    tmp.replace(paper_readiness)
    outputs.append(paper_readiness)
    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-report")
    parser.add_argument("command", choices=["build", "check", "sync"])
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    root = args.repository_root.resolve()
    target = args.output.resolve() if args.output else root / "projections" / "read-model" / "read-model.v1.json"
    if args.command == "build":
        path = write_read_model(root, target)
        print(json.dumps({"status": "PASS", "read_model": str(path)}, ensure_ascii=True))
        return 0
    if args.command == "sync":
        model = build_read_model(root)
        validate_read_model(model)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(model, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        model_path = target
        outputs = write_projection_reports(root, model)
        print(json.dumps({"status": "PASS", "read_model": str(model_path), "reports": [str(item) for item in outputs]}, ensure_ascii=True))
        return 0
    if not target.is_file():
        print(json.dumps({"status": "FAIL", "reason": "read_model_missing", "path": str(target)}, ensure_ascii=True))
        return 1
    payload = json.loads(target.read_text(encoding="utf-8"))
    required = REQUIRED_READ_MODEL_KEYS
    missing = sorted(required - set(payload))
    expected = build_read_model(root)
    try:
        validate_read_model(payload)
    except ValueError as error:
        print(json.dumps({"status": "FAIL", "reason": str(error), "read_model": str(target)}, ensure_ascii=True))
        return 1
    stable = lambda value: {key: item for key, item in value.items() if key != "generated_at"}
    drift = stable(payload) != stable(expected)
    result = {"status": "PASS" if not missing and not drift else "FAIL", "missing": missing, "drift": drift, "read_model": str(target), "projection_revision": expected.get("projection_revision")}
    print(json.dumps(result, ensure_ascii=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

