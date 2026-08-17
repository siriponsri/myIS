from __future__ import annotations

from pathlib import Path

import yaml

from myis_research.armindex.cli import main


ROOT = Path(__file__).resolve().parents[1]


def test_status_is_aggregate_safe(capsys) -> None:
    assert main(["status", "--repository-root", str(ROOT)]) == 0
    payload = yaml.safe_load(capsys.readouterr().out)
    assert payload["current_phase"] == "A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT"
    assert payload["current_task"] == "A3.1"
    assert payload["scientific_authority"] is True
    assert payload["measured_runs"] == 1
    assert payload["selection_accesses"] == 0
    assert payload["final_accesses"] == 0


def test_validate_covers_contracts_and_five_arm_registry(capsys) -> None:
    assert main(["validate", "--repository-root", str(ROOT)]) == 0
    payload = yaml.safe_load(capsys.readouterr().out)
    assert payload == {
        "campaign_id": "armindex-multiretriever-v2",
        "contract_schema_groups": 8,
        "a1_2_gpu_proposal_status": "proposal_not_adopted_execution_locked",
        "measured_execution": False,
        "registered_arms": 5,
        "runnable_fixture_arms": 1,
        "schema_version": "myis.armindex-cli-validation.v1",
        "scientific_authority": False,
        "status": "PASS",
        "unresolved_dense_arms": 4,
    }


def test_fixture_defaults_to_disposable_output(capsys) -> None:
    assert main(["fixture", "--repository-root", str(ROOT)]) == 0
    payload = yaml.safe_load(capsys.readouterr().out)
    assert payload["status"] == "PASS"
    assert payload["output_persisted"] is False
    assert payload["protected_data_accessed"] is False
    assert payload["measured_execution"] is False
    assert set(payload["real_counters"].values()) == {0}


def test_feasibility_fixture_defaults_to_disposable_cpu_output(capsys) -> None:
    assert main(
        [
            "feasibility-fixture",
            "--repository-root",
            str(ROOT),
            "--repetitions",
            "3",
        ]
    ) == 0
    payload = yaml.safe_load(capsys.readouterr().out)
    assert payload["status"] == "PASS"
    assert payload["output_persisted"] is False
    assert payload["protected_data_accessed"] is False
    assert payload["measured_execution"] is False
    assert payload["cpu_only"] is True
    assert payload["largest_synthetic_document_count"] == 128
    assert payload["largest_peak_python_allocation_bytes"] > 0
    assert set(payload["real_counters"].values()) == {0}


def test_adapter_fixture_runs_arm01_on_cpu_and_keeps_a12_closed(capsys) -> None:
    assert main(
        [
            "adapter-fixture",
            "--repository-root",
            str(ROOT),
            "--repetitions",
            "3",
        ]
    ) == 0
    payload = yaml.safe_load(capsys.readouterr().out)
    assert payload["status"] == "PASS"
    assert payload["task_id"] == "A1.1"
    assert payload["arm01_cpu_path"] == "PASS"
    assert payload["registered_arms"] == 5
    assert payload["dense_arms_blocked"] == 4
    assert payload["output_persisted"] is False
    assert set(payload["real_counters"].values()) == {0}
