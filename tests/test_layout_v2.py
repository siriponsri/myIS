from pathlib import Path

import yaml

from myis_research.layout import validate


def test_active_layout_has_no_legacy_roots():
    result = validate(Path(__file__).resolve().parents[1])
    assert result["status"] == "PASS", result


def test_program_contract_exposes_only_three_owner_decisions():
    payload = yaml.safe_load((Path(__file__).resolve().parents[1] / "control/program.yaml").read_text(encoding="utf-8"))
    assert payload["owner_decisions"] == {
        "standing_campaign_authorization": "D1_START_CAMPAIGN",
        "final_access": "D2_OPEN_FINAL",
        "external_release": "D3_SUBMIT_RELEASE",
        "micro_gates": False,
    }
