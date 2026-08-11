from __future__ import annotations

import json
import shutil
from pathlib import Path

from myis_research.projections.read_model import (
    _a12_r13_failure_projection,
    build_read_model,
)
from myis_research.report_cli import (
    VAULT_RELATIVE_PATH,
    projection_report_contents,
)
from myis_research.report_records import build_report_records

ROOT = Path(__file__).resolve().parents[1]
R13_RELATIVE = Path("outputs/audits/armindex/a1.2-v16-r13-failure-audit-20260810.json")


def test_r13_failure_projection_is_valid_failed_closed_provenance(tmp_path: Path) -> None:
    target = tmp_path / R13_RELATIVE
    target.parent.mkdir(parents=True)
    shutil.copy2(ROOT / R13_RELATIVE, target)

    model = build_read_model(tmp_path)
    armindex = model["armindex"]
    projection = armindex["a1_2_r13_failure"]

    assert projection["validated"] is True
    assert projection["status"] == "FAILED_CLOSED"
    assert projection["scientific_authority"] is False
    assert projection["attempt"]["completed_logical_cells"] == 24
    assert projection["attempt"]["required_logical_cells"] == 25
    assert projection["attempt"]["partial_results_promotable"] is False
    assert projection["disposition"]["instance_reuse_allowed"] is False
    assert projection["next_authorized_action"].startswith("PREPARE_FRESH_A1")
    assert armindex["a1_2_current_attempt"]["validated"] is False
    assert "r13_failed_closed" not in armindex["status"]


def test_r13_failure_projection_rejects_tampered_audit(tmp_path: Path) -> None:
    target = tmp_path / R13_RELATIVE
    target.parent.mkdir(parents=True)
    audit = json.loads((ROOT / R13_RELATIVE).read_text(encoding="ascii"))
    audit["status"] = "PASS"
    target.write_text(json.dumps(audit, sort_keys=True), encoding="ascii")

    projection = _a12_r13_failure_projection(tmp_path)
    assert projection["validated"] is False
    assert projection["status"] == "invalid"


def test_r13_failure_is_linked_to_a1_and_a12_records_without_authority() -> None:
    model = build_read_model(ROOT)
    records = build_report_records(ROOT, model)
    for report_id in ("phase-a1_baselines_and_multi_arm_screening", "task-a1-2"):
        record = next(item for item in records if item["report_id"] == report_id)
        artifact = next(
            item
            for item in record["artifact_references"]
            if item["artifact_id"] == "a12-v16-r13-failed-closed-attempt-audit"
        )
        assert record["status"] == "completed"
        assert record["scientific_authority"] is True
        assert artifact["scientific_authority"] is False
        assert (
            artifact["content_sha256"]
            == model["armindex"]["a1_2_r13_failure"]["audit_file_sha256"]
        )


def test_generated_a12_note_states_incomplete_failure_and_retry_gate() -> None:
    model = build_read_model(ROOT)
    outputs = projection_report_contents(ROOT, model)
    path = (
        ROOT
        / VAULT_RELATIVE_PATH
        / "02_Tasks/ArmIndex/A1_BASELINES_AND_MULTI_ARM_SCREENING/A1.2.md"
    )
    note = outputs[path]
    assert "a1.2-v16-r13-failure-audit-20260810.json" in note
    assert "A1.2 v16 r13 failed-closed attempt audit" in note
