from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from test_armindex_a1_2_evaluator_closeout_v16 import _evaluation

from myis_research.armindex import a1_2_measured_result_summary_v16 as summary_module
from myis_research.armindex.a1_2_evaluator_closeout_v16 import (
    RECEIPT_NAME,
    write_evaluator_closeout_receipt,
)
from myis_research.armindex.a1_2_measured_result_summary_v16 import (
    MeasuredResultSummaryV16Error,
    validate_measured_result_summary_file,
    write_measured_result_summary,
)
from myis_research.kernel.canonical import canonical_json, canonical_sha256
from myis_research.report_records import _artifacts, _metrics

ROOT = Path(__file__).resolve().parents[1]


def _repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    schema_root = repository / "schemas" / "armindex"
    schema_root.mkdir(parents=True)
    for name in (
        "a1.2-aggregate-result-receipt.v11.json",
        "a1.2-evaluator-closeout-receipt.v16.json",
        "a1.2-measured-result-summary.v16.json",
    ):
        shutil.copy2(ROOT / "schemas" / "armindex" / name, schema_root / name)
    return repository


def test_writes_one_repository_safe_summary_for_all_five_arms(tmp_path: Path) -> None:
    evaluation = _evaluation(tmp_path)
    write_evaluator_closeout_receipt(ROOT, evaluation)
    repository = _repository(tmp_path)

    path, summary = write_measured_result_summary(repository, evaluation)

    assert path.is_file()
    assert summary["coverage"]["completed_logical_cells"] == 25
    assert [item["arm_id"] for item in summary["arm_results"]] == [
        "ARM-01",
        "ARM-02",
        "ARM-03",
        "ARM-04",
        "ARM-05",
    ]
    assert all(item["out_recall_at_100_mean"] == 1.0 for item in summary["arm_results"])
    assert summary["promoted_arm_ids"] == ["ARM-01", "ARM-02", "ARM-03"]
    assert "Q-" not in json.dumps(summary) and "F-" not in json.dumps(summary)
    validated = validate_measured_result_summary_file(
        repository, "a12-v16-evaluator-test"
    )
    assert validated["summary_sha256"] == summary["summary_sha256"]

    model = {
        "armindex": {
            "a1_2_current_attempt": {
                "validated": True,
                "status": "PASS",
                "measured_result_summary": validated,
            }
        }
    }
    metrics = _metrics(model, "A1_BASELINES_AND_MULTI_ARM_SCREENING", "A1.2")
    assert len(metrics) == 30
    assert {item["split"] for item in metrics} == {"REP-DEV"}
    artifacts = _artifacts(
        repository, model, "A1_BASELINES_AND_MULTI_ARM_SCREENING", "A1.2"
    )
    assert any(item["artifact_id"] == "a12-measured-result-summary-v16" for item in artifacts)


def test_rejects_tampered_aggregate_receipt(tmp_path: Path) -> None:
    evaluation = _evaluation(tmp_path)
    write_evaluator_closeout_receipt(ROOT, evaluation)
    repository = _repository(tmp_path)
    receipt_path = evaluation / "receipts" / "ARM-01--P00-TAC-DOC.json"
    receipt = json.loads(receipt_path.read_text(encoding="ascii"))
    receipt["quality"]["recall_at_100_out"] = 0.5
    receipt_path.write_text(json.dumps(receipt), encoding="ascii")

    with pytest.raises(MeasuredResultSummaryV16Error, match="receipt_sha256 mismatch"):
        write_measured_result_summary(repository, evaluation)


def test_rejects_closeout_from_a_different_evaluation_lineage(tmp_path: Path) -> None:
    evaluation = _evaluation(tmp_path)
    write_evaluator_closeout_receipt(ROOT, evaluation)
    closeout_path = evaluation / RECEIPT_NAME
    repository = _repository(tmp_path)
    closeout = json.loads(closeout_path.read_text(encoding="ascii"))
    closeout["cell_receipt_set_sha256"] = "0" * 64
    closeout["receipt_sha256"] = canonical_sha256(
        {key: value for key, value in closeout.items() if key != "receipt_sha256"}
    )
    closeout_path.write_text(canonical_json(closeout) + "\n", encoding="ascii")

    with pytest.raises(
        MeasuredResultSummaryV16Error,
        match="does not bind the current evaluation inputs",
    ):
        write_measured_result_summary(repository, evaluation)


def test_summary_id_must_bind_attempt_id(tmp_path: Path) -> None:
    evaluation = _evaluation(tmp_path)
    write_evaluator_closeout_receipt(ROOT, evaluation)
    repository = _repository(tmp_path)
    path, _summary = write_measured_result_summary(repository, evaluation)
    value = json.loads(path.read_text(encoding="ascii"))
    value["summary_id"] = "a12-v16-other-measured-result-summary-v16"
    value["summary_sha256"] = canonical_sha256(
        {key: item for key, item in value.items() if key != "summary_sha256"}
    )
    path.write_text(canonical_json(value) + "\n", encoding="ascii")

    with pytest.raises(MeasuredResultSummaryV16Error, match="summary_id"):
        validate_measured_result_summary_file(repository, evaluation.name)


def test_rejects_receipt_change_during_summary_construction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evaluation = _evaluation(tmp_path)
    write_evaluator_closeout_receipt(ROOT, evaluation)
    repository = _repository(tmp_path)
    original = summary_module.validate_evaluator_closeout_inputs

    def validate_then_mutate(root: Path, attempt_root: Path) -> dict[str, object]:
        values = original(root, attempt_root)
        path = attempt_root / "receipts" / "ARM-01--P00-TAC-DOC.json"
        receipt = json.loads(path.read_text(encoding="ascii"))
        receipt["quality"]["recall_at_100_out"] = 0.5
        receipt["receipt_sha256"] = canonical_sha256(
            {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        )
        path.write_text(canonical_json(receipt) + "\n", encoding="ascii")
        return values

    monkeypatch.setattr(
        summary_module,
        "validate_evaluator_closeout_inputs",
        validate_then_mutate,
    )

    with pytest.raises(MeasuredResultSummaryV16Error, match="changed during"):
        write_measured_result_summary(repository, evaluation)
