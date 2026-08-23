"""Focused checks for the post-confirmatory A6 phase registry amendment."""

from __future__ import annotations

import json
from pathlib import Path

from myis_research.armindex import ACTIVE_PHASE_IDS
from myis_research.mlflow_mirror import ARMINDEX_EXPERIMENT, MirrorStage
from myis_research.projections.read_model import _empty_armindex_projection


ROOT = Path(__file__).resolve().parents[1]
A6 = "A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY"
A7 = "A7_SEVEN_LAYER_RETRIEVAL_DIAGNOSIS"
A8 = "A8_JOURNAL_SYNTHESIS_AND_PUBLICATION"


def test_active_registry_routes_frozen_pool_to_diagnosis_and_journal() -> None:
    assert ACTIVE_PHASE_IDS[-4:] == ("A5_FINAL_CONFIRMATION", A6, A7, A8)
    assert len(ACTIVE_PHASE_IDS) == 9


def test_mlflow_and_fail_closed_projection_accept_the_nine_phase_registry() -> None:
    assert MirrorStage(A6).experiment_name == ARMINDEX_EXPERIMENT
    assert MirrorStage(A7).experiment_name == ARMINDEX_EXPERIMENT
    assert MirrorStage(A8).experiment_name == ARMINDEX_EXPERIMENT
    assert [phase["phase_id"] for phase in _empty_armindex_projection()["phases"]] == list(ACTIVE_PHASE_IDS)


def test_phase_report_schema_accepts_materialization_diagnosis_and_journal_phase() -> None:
    schema = json.loads((ROOT / "schemas" / "phase-task-report.v1.json").read_text(encoding="utf-8"))
    phase_ids = schema["properties"]["phase_id"]["enum"]
    assert phase_ids[-4:] == ["A5_FINAL_CONFIRMATION", A6, A7, A8]
    assert "A6_PUBLICATION_AND_RELEASE" not in phase_ids
