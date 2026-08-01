from __future__ import annotations

from pathlib import Path
import shutil

from myis_research.projections.read_model import _p2_official_review_projection, build_read_model
from myis_research.report_cli import _mlflow_archive_index


ROOT = Path(__file__).resolve().parents[1]


def test_mlflow_archive_index_contains_only_p2_readiness_aggregates() -> None:
    model = build_read_model(ROOT)
    index = _mlflow_archive_index(model)
    p2 = index["p2_readiness"]
    assert p2["budget_profile_id"] == "p2-r1-primary-v1"
    assert len(p2["budget_profile_sha256"]) == 64
    assert p2["measured_runs"] == 0
    assert p2["selection_accesses"] == 0
    assert p2["freeze_status"] == "not_started"
    review = p2["official_review"]
    assert review["status"] == "accepted_static_contract_review"
    assert review["evidence_class"] == "static_contract_review"
    assert review["final_round"] == 3
    assert review["final_verdict"] == "accept"
    assert len(review["index_sha256"]) == 64
    assert review["protected_data_accessed"] is False
    assert review["measured_execution_performed"] is False
    assert "candidate_ids" not in p2
    assert "query_ids" not in str(index).lower()


def test_official_review_projection_fails_closed_on_hash_drift(tmp_path: Path) -> None:
    target = tmp_path / "orchestration/audits/p2-readiness"
    shutil.copytree(ROOT / "orchestration/audits/p2-readiness", target)
    result = target / "round-03/result.json"
    result.write_text(result.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    review = _p2_official_review_projection(tmp_path)

    assert review["status"] == "invalid_audit_bundle"
    assert review["fixture_pilot_contract_status"] == "blocked_invalid_audit"
    assert review["final_verdict"] is None
