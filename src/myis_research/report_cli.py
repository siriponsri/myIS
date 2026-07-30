"""Build the canonical read model and safe cross-repository reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .projections.read_model import write_read_model, build_read_model, canonical_json, sha256


def write_projection_reports(root: Path, model: dict) -> list[Path]:
    """Atomically regenerate Brain and Paper text projections from one model."""
    outputs: list[Path] = []
    # Bind reports to the stable read-model revision, excluding generation time.
    source_sha = str(model.get("projection_revision") or sha256(canonical_json({key: value for key, value in model.items() if key != "generated_at"})))
    campaign = model.get("campaigns", [{}])[0]
    readiness = model.get("publication_readiness", {})
    brain_root = (root.parent / "02_Brain" / "reports" / "generated").resolve()
    brain_root.mkdir(parents=True, exist_ok=True)
    docs = {
        "program-status.md": f"---\nsource: ../../01_Research/projections/read-model/read-model.v1.json\nsource_sha256: {source_sha}\n---\n\n# Program Status\n\n- Campaign: `{campaign.get('campaign_id', 'unknown')}`\n- Phase status: **{campaign.get('status', 'unknown')}**\n- Runs: {len(model.get('runs', []))}\n- Evidence pointers: {len(model.get('evidence', []))}\n",
        "experiments.md": f"---\nsource_sha256: {source_sha}\n---\n\n# Experiments\n\n| Experiment | Runs |\n|---|---:|\n" + "".join(f"| `{item.get('experiment_id')}` | {item.get('run_count', 0)} |\n" for item in model.get('experiments', [])),
        "publication-readiness.md": f"---\nsource_sha256: {source_sha}\n---\n\n# Publication Readiness\n\nStatus: **{readiness.get('status', 'blocked')}**\n\n" + "".join(f"- {check.get('id')}: **{check.get('status')}**\n" for check in readiness.get('checks', [])),
        "weekly-summary.md": f"---\nsource_sha256: {source_sha}\n---\n\n# Weekly Summary\n\nGenerated from the canonical read model. No manual metric entry is allowed here.\n",
    }
    for name, content in docs.items():
        target = brain_root / name
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(target)
        outputs.append(target)
    obsidian_root = root / "projections" / "obsidian" / "generated"
    obsidian_root.mkdir(parents=True, exist_ok=True)
    for name, content in docs.items():
        target = obsidian_root / name
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(target)
        outputs.append(target)
    paper_root = (root.parent / "03_Paper" / "publications" / "isai-nlp-2026" / "generated").resolve()
    paper_root.mkdir(parents=True, exist_ok=True)
    paper_readiness = paper_root / "publication-readiness.md"
    tmp = paper_readiness.with_suffix(".md.tmp")
    tmp.write_text(docs["publication-readiness.md"], encoding="utf-8")
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
        model_path = write_read_model(root, target)
        outputs = write_projection_reports(root, build_read_model(root))
        print(json.dumps({"status": "PASS", "read_model": str(model_path), "reports": [str(item) for item in outputs]}, ensure_ascii=True))
        return 0
    if not target.is_file():
        print(json.dumps({"status": "FAIL", "reason": "read_model_missing", "path": str(target)}, ensure_ascii=True))
        return 1
    payload = json.loads(target.read_text(encoding="utf-8"))
    required = {"schema_version", "projection_revision", "campaigns", "experiments", "runs", "metrics", "cost", "decisions", "evidence", "publication_readiness"}
    missing = sorted(required - set(payload))
    result = {"status": "PASS" if not missing else "FAIL", "missing": missing, "read_model": str(target)}
    print(json.dumps(result, ensure_ascii=True))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())

