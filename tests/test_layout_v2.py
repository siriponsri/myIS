from pathlib import Path

import yaml

from myis_research.layout import validate


def test_active_layout_has_no_legacy_roots():
    result = validate(Path(__file__).resolve().parents[1])
    assert result["status"] == "PASS", result


def test_program_contract_exposes_only_three_owner_decisions():
    payload = yaml.safe_load((Path(__file__).resolve().parents[1] / "control/program.yaml").read_text(encoding="utf-8"))
    assert payload["owner_decisions"] == {
        "standing_authorization": "D1_START_CAMPAIGN",
        "final_access": "D2_OPEN_FINAL",
        "external_release": "D3_SUBMIT_RELEASE",
        "micro_gates": False,
    }


def test_cpu_contract_fetches_history_required_by_projection_lineage():
    root = Path(__file__).resolve().parents[1]
    workflow = yaml.safe_load((root / ".github/workflows/cpu-contract.yml").read_text(encoding="utf-8"))
    checkout = next(
        step
        for step in workflow["jobs"]["contract"]["steps"]
        if step.get("uses") == "actions/checkout@v4"
    )
    assert checkout["with"]["fetch-depth"] == 0
