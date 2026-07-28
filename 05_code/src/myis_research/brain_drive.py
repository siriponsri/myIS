"""Deterministic Brain-drive orchestration adapters for offline validation."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import replace
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .harness import ApprovalRecord, GoalSpec, HarnessPolicy, LocalHarness, RunSpec
from .harness.models import GoalState, canonical_hash
from .harness.runner import KERNEL_VERSION
from .mlflow_mirror import MLflowMirror, MirrorArtifact, MirrorKind, MirrorSpec, MirrorStage
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
    """Run Brain -> Harness -> structlog -> MLflow -> manifest offline."""
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
    policy = HarnessPolicy(policy_id="offline-brain-drive-v1")
    goal = GoalSpec(
        goal_id="V01-brain-drive-demo",
        objective="Demonstrate a governed Brain-drive research run using offline fixtures.",
        track="F0",
        state=GoalState.APPROVED,
        success_metrics=("source_count", "retrieval_hit_count", "provenance_completeness"),
    )
    approval = ApprovalRecord(
        approval_id="owner-offline-demo-20260727",
        source="Owner approved local offline harness implementation",
        approved_at_utc=datetime.now(timezone.utc).isoformat(),
        scope_hash="pending",
    )
    spec = RunSpec(
        run_id=f"v01-{uuid.uuid4().hex}",
        goal=goal,
        approval=approval,
        arm="C0",
        phase="offline-demo",
        dataset_id="V01-offline-pdf-web-history-fixtures",
        dataset_manifest_hash=manifest_hash,
        split="development",
        split_query_ids_hash=hashlib.sha256(b"offline-query-001").hexdigest(),
        evaluator_id="fixture-provenance-evaluator-v1",
        evaluator_hash=hashlib.sha256(b"fixture-provenance-evaluator-v1").hexdigest(),
        kernel_version=KERNEL_VERSION,
        policy_hash=policy.sha256,
        config_hash=canonical_hash({"seed": 7, "network": False}),
        prompt_hash=hashlib.sha256(b"Synthesize a bounded ranking hypothesis from curated Brain sources.").hexdigest(),
        skill_set_hash=hashlib.sha256(b"brain-drive-v1").hexdigest(),
        seed=7,
        budget={"max_seconds": 30, "max_api_cost_usd": 0, "max_gpu_seconds": 0},
    )
    spec = replace(spec, approval=replace(approval, scope_hash=spec.scope_hash()))
    # The harness writes the canonical bundle. MLflow receives only an explicit,
    # validated projection after finalization, never the whole run directory.
    harness = LocalHarness(workdir / "runs", mlflow_root=None)

    def execute_fixture(_: RunSpec, __: HarnessPolicy, logger: object) -> dict[str, object]:
        for record in records:
            logger.emit("source.registered", status="RUNNING", milestone=True, source_id=record.source_id, source_kind=record.kind)
        logger.emit("retrieval.completed", status="RUNNING", milestone=True, hit_count=len(hits))
        return {
            "result": report,
            "metrics": {
                "source_count": len(records),
                "retrieval_hit_count": len(hits),
                "provenance_completeness": len(records) / 3,
            },
            "per_query": [{"query_id": "offline-query-001", "hit_count": len(hits), "provenance_complete": 1.0}],
        }

    run_result = harness.execute(
        spec,
        policy,
        executor=execute_fixture,
        prompt_record={
            "template_id": "brain-drive-synthesis",
            "version": "01_Prompt+02_Prompt",
            "sha256": spec.prompt_hash,
            "rendered": "Synthesize a bounded ranking hypothesis from curated Brain sources.",
            "rules": ["raw inbox immutable", "provenance required"],
        },
        flow_record={
            "engine": "brain-drive-harness",
            "steps": [
                "register offline PDF, web, and history fixtures",
                "retrieve through the QMD-compatible Brain adapter",
                "execute under the immutable harness kernel",
                "write structlog runtime/progress projections",
                "mirror to local MLflow and finalize a canonical manifest",
            ],
        },
    )
    run_dir = run_result.run_dir
    mirrored = tuple(
        MirrorArtifact.from_path(path, kind=kind, canonical_root=run_dir)
        for path, kind in (
            (run_dir / "manifest.json", MirrorKind.RESULT),
            (run_dir / "validation_report.json", MirrorKind.RESULT),
            (run_dir / "result.json", MirrorKind.RESULT),
            (run_dir / "metrics.json", MirrorKind.METRIC),
        )
    )
    mirror_receipt = MLflowMirror(mlflow_root).sync(
        MirrorSpec(
            stage=MirrorStage.TRACK_C,
            run_name=spec.run_id,
            git_commit=spec.git_commit,
            canonical_source_sha256=run_result.manifest_sha256 or ("0" * 64),
            track="C",
            arm=spec.arm,
            phase=spec.phase,
            data_role="offline_fixture",
            tags={
                "goal_id": spec.goal.goal_id,
                "phase": spec.phase,
                "scientific_run": "false",
                "dataset_access": "offline-fixtures-only",
            },
            parameters={
                "dataset_id": spec.dataset_id,
                "split": spec.split,
                "seed": spec.seed,
                "model_id": spec.model_id,
                "evaluator_id": spec.evaluator_id,
            },
            metrics={name: float(value) for name, value in run_result.metrics.items()},
        ),
        mirrored,
        receipt_dir=run_dir / "receipts",
    )
    return {
        "report": report,
        "records": records,
        "run_dir": str(run_dir),
        "mlflow_receipt": mirror_receipt.as_dict(),
    }
