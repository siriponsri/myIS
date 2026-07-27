"""Deterministic Brain-drive orchestration adapters for offline validation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .mlflow_contract import AgentRun, AgentRunSpec
from .sources import SourceCatalog, SourceRecord, register_source


@dataclass(frozen=True)
class BrainHit:
    source_id: str
    title: str
    score: float
    pointer: str


class FixtureBrain:
    """Tiny lexical retriever that stands in for Obsidian Mind/QMD in tests."""

    def __init__(self, records: list[SourceRecord]):
        self.records = records

    def retrieve(self, query: str, limit: int = 5) -> list[BrainHit]:
        terms = {term.lower() for term in query.split() if term.strip()}
        hits = []
        for record in self.records:
            haystack = f"{record.title} {record.kind} {' '.join(record.metadata.values())}".lower()
            score = sum(term in haystack for term in terms) / max(len(terms), 1)
            if score:
                hits.append(BrainHit(record.source_id, record.title, score, record.locator))
        return sorted(hits, key=lambda hit: (-hit.score, hit.source_id))[:limit]


def run_brain_drive_demo(workdir: Path, *, mlflow_root: Path) -> dict[str, object]:
    """Run the complete source -> retrieve -> synthesize -> ledger flow."""
    fixture_dir = workdir / "fixtures"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    pdf = fixture_dir / "paper.pdf"
    history = fixture_dir / "history.md"
    pdf.write_bytes(b"deterministic patent retrieval paper fixture\n")
    history.write_text("baseline ranking experiment and lessons learned\n", encoding="utf-8")
    catalog = SourceCatalog(workdir / "source_catalog.jsonl")
    records = [
        register_source(pdf, kind="pdf", title="Patent retrieval paper", metadata={"topic": "retrieval ranking"}),
        register_source("https://example.test/brain-note", kind="web", title="Web retrieval note", metadata={"topic": "retrieval"}),
        register_source(history, kind="history", title="Legacy project history", metadata={"topic": "ranking lessons"}),
    ]
    for record in records:
        catalog.append(record)
    brain = FixtureBrain(records)
    query = "retrieval ranking"
    hits = brain.retrieve(query)
    report = {
        "query": query,
        "hits": [hit.__dict__ for hit in hits],
        "synthesis": "The deterministic evidence packet supports ranking-aware retrieval as the next bounded hypothesis.",
        "pointers": [hit.pointer for hit in hits],
    }
    report["report_sha256"] = hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest()
    manifest_hash = hashlib.sha256((workdir / "source_catalog.jsonl").read_bytes()).hexdigest()
    run = AgentRun.start(mlflow_root, AgentRunSpec(
        component="research", agent_id="notebook-demo", experiment="V01_brain_drive_agent_demo",
        prompt_version="01_Prompt+02_Prompt", skill_version="brain-drive-v1",
        source_manifest_hash=manifest_hash,
    ))
    run.log_prompt("Synthesize a bounded ranking hypothesis from curated Brain sources.", rules=["raw inbox immutable", "provenance required"])
    run.log_flow(["register sources", "retrieve from Obsidian Mind adapter", "synthesize report", "write KM pointers"])
    for record in records:
        run.progress("source_registered", source_id=record.source_id, kind=record.kind)
    run.progress("retrieval_complete", hit_count=len(hits))
    run.log_result(report)
    run.log_metric("source_count", len(records))
    run.log_metric("retrieval_hit_count", len(hits))
    run.log_metric("provenance_completeness", len(records) / 3)
    run_dir = run.close()
    return {"report": report, "records": records, "run_dir": str(run_dir)}
