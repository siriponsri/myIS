from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.session_capsules import (
    SessionCapsuleValidationError,
    _validate_plan_binding,
    latest_valid_session,
    validate_all_session_capsules,
)


ROOT = Path(__file__).resolve().parents[1]


def test_valid_historical_session_can_be_superseded(monkeypatch, tmp_path: Path) -> None:
    session_root = tmp_path / "projections/sessions"
    session_root.mkdir(parents=True)
    old_id = "20260730T180521Z-old"
    new_id = "20260730T210000Z-new"
    old_path = session_root / f"{old_id}.json"
    new_path = session_root / f"{new_id}.json"
    old_path.write_text(json.dumps({"session_id": old_id}), encoding="utf-8")
    new_path.write_text(json.dumps({
        "session_id": new_id,
        "corrections": [{
            "target_session_id": old_id,
            "observed_validation_error": "historical completion claim is superseded",
        }],
    }), encoding="utf-8")

    class Report:
        schema_version = "myis.research-session.v2"

        def __init__(self, session_id: str) -> None:
            self.session_id = session_id

    monkeypatch.setattr(
        "myis_research.session_capsules.validate_session_capsule",
        lambda path, root: Report(path.stem),
    )
    monkeypatch.setattr(
        "myis_research.session_capsules._timestamp",
        lambda payload, key: old_path.stat().st_mtime if payload["session_id"] == old_id else new_path.stat().st_mtime + 1,
    )
    monkeypatch.setattr(
        "myis_research.session_capsules._read_payload",
        lambda path: {
            "session_id": path.stem,
            "schema_version": "myis.research-session.v2",
            "ended_at_utc": "2026-07-30T21:00:00Z",
            "execution_snapshot": None,
            "owner_brief_th": "สถานะ",
            "owner_actions": [],
            "gate_request": {},
            "next_resources": {},
            "closeout": {},
            "corrections": ([{
                "target_session_id": old_id,
                "observed_validation_error": "historical completion claim is superseded",
            }] if path.stem == new_id else []),
        },
    )

    audit = validate_all_session_capsules(tmp_path)
    by_id = {record["session_id"]: record for record in audit["records"]}
    assert by_id[old_id]["classification"] == "SUPERSEDED"
    assert by_id[new_id]["classification"] == "PASS"
    assert latest_valid_session(tmp_path)["session_id"] == new_id


def test_p1_legacy_completion_capsule_is_superseded_by_recovery_freeze() -> None:
    audit = validate_all_session_capsules(ROOT)
    records = {record["session_id"]: record for record in audit["records"]}
    assert records["20260730T180521Z-p1-legacy-certification-v1"]["classification"] == "SUPERSEDED"
    latest = latest_valid_session(ROOT, phase_id="P1_CPU_BASELINE", task_id="P1.3", gate_id="D1_START_CAMPAIGN")
    assert latest is not None
    assert latest["session_id"] != "20260730T180521Z-p1-legacy-certification-v1"


def test_armindex_task_map_uses_canonical_phase_and_standing_d1() -> None:
    _validate_plan_binding(
        ROOT,
        "A1_BASELINES_AND_MULTI_ARM_SCREENING",
        "A1.2",
        "D1_START_CAMPAIGN",
    )

    with pytest.raises(SessionCapsuleValidationError, match="phase, task, or gate"):
        _validate_plan_binding(ROOT, "A1", "A1.2", "D1_START_CAMPAIGN")
