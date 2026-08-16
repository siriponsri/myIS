from __future__ import annotations

from pathlib import Path

import pytest

from myis_research.armindex.a2_publication_figures import (
    A2PublicationFigureError,
    render_a2_goal004_publication_figures,
    validate_a2_goal004_figure_evidence,
)
from myis_research.kernel.canonical import canonical_sha256

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _digest(value: str) -> str:
    return canonical_sha256({"fixture": value})


def _evidence(*, measured: bool = False) -> dict[str, object]:
    closeout = {
        "schema_version": "myis.armindex-a2-execution-closeout-receipt.v1",
        "receipt_id": "a2-goal004-20260816-005-execution-closeout-v1",
        "attempt_id": "a2-goal004-20260816-005",
        "status": "PASS_A2_EXECUTION_CLOSEOUT",
        "evidence_class": "measured_development_aggregate" if measured else "engineering_synthetic",
        "candidate_count": 52,
        "matched_candidate_count": 40,
        "conditional_reserve_candidate_count": 12,
        "arm_winner_receipt_sha256s": {arm: _digest(arm) for arm in ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")},
        "candidate_result_set_sha256": _digest("candidates"),
        "safe_return_receipt_sha256": _digest("safe-return"),
        "terminal_checkpoint_sha256": _digest("checkpoint"),
        "workers_reaped": True,
        "protected_scan_passed": True,
        "diagnostic_non_advancing_arms": ["ARM-01", "ARM-02"],
        "primary_advancement_arms": ["ARM-03", "ARM-05", "ARM-04"],
        "claim_evidence_pointers": ["recovery-coordinator-001/outputs/aggregate-coverage.v1.json"],
        "freeze_bindings": {"manifest_sha256": _digest("manifest"), "freeze_receipt_sha256": _digest("freeze"), "lock_sha256": _digest("lock")},
    }
    closeout["receipt_sha256"] = canonical_sha256(closeout)
    audit = {
        "schema_version": "myis.armindex-a2-result-audit-receipt.v1",
        "audit_id": "a2-goal004-20260816-005-result-audit-v1",
        "attempt_id": closeout["attempt_id"],
        "status": "PASS_A2_RESULT_AUDIT",
        "execution_closeout_receipt_sha256": closeout["receipt_sha256"],
        "candidate_result_set_sha256": closeout["candidate_result_set_sha256"],
        "safe_return_receipt_sha256": closeout["safe_return_receipt_sha256"],
        "candidate_count": 52,
        "aggregate_only": True,
        "protected_scan_passed": True,
        "claim_boundary": "Aggregate-only REP-DEV results; no protected or per-query material is plotted.",
    }
    audit["audit_sha256"] = canonical_sha256(audit)
    metrics = []
    for index, arm_id in enumerate(("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")):
        metrics.append({"arm_id": arm_id, "recall_at_100": 0.61 + index * 0.02, "ndcg_at_100": 0.42 + index * 0.01, "ndcg_at_10": 0.31 + index * 0.01, "latency_ms": 20.0 + index * 5, "charged_usd": 0.8 + index * 0.1, "index_size_mb": 32.0 + index, "ram_gb": 1.5 + index * 0.1, "vram_gb": None if index == 0 else 3.0 + index * 0.2})
    return {"execution_closeout": closeout, "result_audit": audit, "arm_metrics": metrics, "recovery_summary": {"checkpoint_count": 53, "recovered_candidate_count": 1, "failed_attempts_separated": True}, "reserve_decision": {"matched_status": "COMPLETE", "reserve_status": "DORMANT", "reserve_candidate_count": 12}}


def test_fixture_renderer_writes_all_five_figure_families(tmp_path: Path) -> None:
    result = render_a2_goal004_publication_figures(
        REPOSITORY_ROOT, _evidence(), output_directory=tmp_path, fixture_mode=True
    )
    manifest = result["manifest"]
    assert manifest["fixture_mode"] is True
    assert {row["figure_id"] for row in manifest["figures"]} == {"coverage-recovery", "outcomes", "quality-latency-cost-frontier", "matched-reserve-decision-path", "appendix-audit-map"}
    assert result["manifest_path"].is_file()
    for row in manifest["figures"]:
        assert set(row["artifacts"]) == {"png", "svg", "pdf"}
        for artifact in row["artifacts"].values():
            assert (REPOSITORY_ROOT / artifact["uri"]).exists() is False
            assert (tmp_path / Path(artifact["uri"]).name).stat().st_size == artifact["bytes"]


def test_renderer_rejects_precloseout_or_protected_evidence() -> None:
    precloseout = _evidence()
    precloseout["execution_closeout"]["status"] = "RUNNING"  # type: ignore[index]
    with pytest.raises(A2PublicationFigureError, match="validation failed"):
        validate_a2_goal004_figure_evidence(REPOSITORY_ROOT, precloseout, fixture_mode=True)
    protected = _evidence()
    protected["qrels"] = ["forbidden"]  # type: ignore[index]
    with pytest.raises(A2PublicationFigureError, match="protected boundary"):
        validate_a2_goal004_figure_evidence(REPOSITORY_ROOT, protected, fixture_mode=True)


def test_production_render_requires_measured_closeout_and_goal_directory(tmp_path: Path) -> None:
    with pytest.raises(A2PublicationFigureError, match="measured aggregate"):
        render_a2_goal004_publication_figures(REPOSITORY_ROOT, _evidence(), output_directory=tmp_path)
    measured = _evidence(measured=True)
    with pytest.raises(A2PublicationFigureError, match="Goal 004 output directory"):
        render_a2_goal004_publication_figures(REPOSITORY_ROOT, measured, output_directory=tmp_path)
