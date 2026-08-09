from __future__ import annotations

from pathlib import Path

from myis_research.projections.read_model import build_read_model
from myis_research.report_cli import VAULT_RELATIVE_PATH, _obsidian_vault_contents
from myis_research.report_records import build_report_records

ROOT = Path(__file__).resolve().parents[1]


def test_exact_token_id_probe_projection_is_aggregate_safe_and_pre_measurement() -> None:
    model = build_read_model(ROOT)
    projection = model["armindex"]["a1_2_exact_token_id_adapter_probe"]

    assert projection["validated"] is True
    assert projection["status"] == "PASS_PRE_MEASUREMENT"
    assert projection["scientific_authority"] is False
    assert projection["audit_sha256"] == (
        "03b2bce9ab001e2ce4a0fff218ac4dead89f9107cb64173fe56291a780bebb8c"
    )
    assert projection["synthetic_probe"]["ARM-03"]["status"] == "PASS"
    assert projection["synthetic_probe"]["ARM-03"]["exact_token_id_windows"] == 5
    assert projection["authorization"]["measured_retrieval_allowed"] is False
    assert projection["counters"] == {
        "measured_runs": 0,
        "selection_accesses": 0,
        "final_accesses": 0,
    }


def test_exact_token_id_probe_is_bound_into_a12_task_and_history_reports() -> None:
    model = build_read_model(ROOT)
    records = build_report_records(ROOT, model)
    task = next(record for record in records if record["report_id"] == "task-a1-2")
    artifacts = task["artifact_references"]
    probe_artifact = next(
        item
        for item in artifacts
        if item["artifact_id"] == "a12-v16-exact-token-id-adapter-probe"
    )
    assert probe_artifact["safe_uri"].endswith(
        "a1.2-v16-exact-token-id-adapter-probe-20260809.json"
    )
    assert len(probe_artifact["content_sha256"]) == 64

    contents = _obsidian_vault_contents(ROOT, model)
    note = contents[
        VAULT_RELATIVE_PATH
        / "05_Research_History/ArmIndex/A1_2_EXACT_TOKEN_ID_ADAPTER_PROBE.md"
    ]
    assert "PASS_PRE_MEASUREMENT" in note
    assert "exact-token-ID" in note
    assert "No measured A1 result" in note
    assert "a1.2-v16-exact-token-id-adapter-probe-20260809.json" in note
