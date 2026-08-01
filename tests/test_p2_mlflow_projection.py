from __future__ import annotations

from pathlib import Path

from myis_research.projections.read_model import build_read_model
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
    assert "candidate_ids" not in p2
    assert "query_ids" not in str(index).lower()
