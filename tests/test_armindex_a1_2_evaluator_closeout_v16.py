from __future__ import annotations

import json
from pathlib import Path

import pytest
from test_armindex_a1_2_owner_local_evaluator_v16 import _archive, _manifest

from myis_research.armindex.a1_2_evaluator_closeout_v16 import (
    EvaluatorCloseoutV16Error,
    validate_evaluator_closeout_inputs,
    validate_evaluator_closeout_receipt,
    write_evaluator_closeout_receipt,
)
from myis_research.armindex.a1_2_owner_local_evaluator_v16 import (
    evaluate_safe_return,
)
from myis_research.kernel.canonical import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]


def _evaluation(tmp_path: Path) -> Path:
    owner = tmp_path / "owner"
    owner.mkdir()
    archive = _archive(tmp_path / "return.tar.gz")
    manifest = _manifest(owner, archive)
    output = tmp_path / "evaluation"
    evaluate_safe_return(archive, manifest, output_root=output, repository_root=ROOT)
    return output / "a12-v16-evaluator-test"


def _write_rehashed(path: Path, receipt: dict[str, object]) -> None:
    receipt["receipt_sha256"] = canonical_sha256(
        {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    )
    path.write_text(
        json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="ascii",
    )


def test_closeout_binds_exactly_25_aggregate_receipts_and_promotion(tmp_path: Path) -> None:
    attempt_root = _evaluation(tmp_path)

    receipt = write_evaluator_closeout_receipt(ROOT, attempt_root)
    assert receipt["status"] == "PASS"
    assert receipt["cell_receipt_count"] == 25
    assert receipt["promoted_arm_ids"] == ["ARM-01", "ARM-02", "ARM-03"]
    promotion = json.loads((attempt_root / "promotion.json").read_text(encoding="ascii"))
    assert receipt["promotion_policy_sha256"] == promotion["policy_sha256"]
    assert receipt["admitted_quote_receipt_sha256"] == promotion["quote_receipt_sha256"]
    assert receipt["admitted_quote_sha256"] == promotion["quote_sha256"]
    assert receipt["cost_allocation_sha256"] == promotion["allocation_sha256"]
    assert validate_evaluator_closeout_inputs(ROOT, attempt_root)["promotion_receipt_sha256"] == receipt["promotion_receipt_sha256"]
    assert validate_evaluator_closeout_receipt(ROOT, receipt)["receipt_sha256"] == receipt["receipt_sha256"]
    assert write_evaluator_closeout_receipt(ROOT, attempt_root)["receipt_sha256"] == receipt["receipt_sha256"]


def test_closeout_accepts_frozen_lineage_that_varies_by_arm_and_program(tmp_path: Path) -> None:
    attempt_root = _evaluation(tmp_path)
    for path in (attempt_root / "receipts").glob("*.json"):
        receipt = json.loads(path.read_text(encoding="ascii"))
        arm = receipt["arm_id"]
        program = receipt["program_id"]
        receipt["lineage"]["model_lock_file_sha256"] = canonical_sha256(
            {"arm_id": arm, "role": "model_lock"}
        )
        receipt["lineage"]["workload_manifest_sha256"] = canonical_sha256(
            {"arm_id": arm, "role": "workload"}
        )
        receipt["lineage"]["program_spec_sha256"] = canonical_sha256(
            {"program_id": program, "role": "program"}
        )
        _write_rehashed(path, receipt)

    values = validate_evaluator_closeout_inputs(ROOT, attempt_root)
    assert values["cell_receipt_count"] == 25


def test_closeout_rejects_inconsistent_cell_specific_lineage(tmp_path: Path) -> None:
    attempt_root = _evaluation(tmp_path)
    path = attempt_root / "receipts" / "ARM-01--P01-TA-DOC.json"
    receipt = json.loads(path.read_text(encoding="ascii"))
    receipt["lineage"]["model_lock_file_sha256"] = canonical_sha256(
        {"arm_id": "ARM-01", "role": "different_model_lock"}
    )
    _write_rehashed(path, receipt)

    with pytest.raises(
        EvaluatorCloseoutV16Error,
        match="inconsistent cell-specific lineage",
    ):
        validate_evaluator_closeout_inputs(ROOT, attempt_root)


def test_closeout_rejects_inconsistent_shared_lineage(tmp_path: Path) -> None:
    attempt_root = _evaluation(tmp_path)
    path = attempt_root / "receipts" / "ARM-01--P01-TA-DOC.json"
    receipt = json.loads(path.read_text(encoding="ascii"))
    receipt["lineage"]["request_sha256"] = canonical_sha256(
        {"request": "different"}
    )
    _write_rehashed(path, receipt)

    with pytest.raises(EvaluatorCloseoutV16Error, match="do not share frozen lineage"):
        validate_evaluator_closeout_inputs(ROOT, attempt_root)


def test_closeout_rejects_tampered_cell_receipt(tmp_path: Path) -> None:
    attempt_root = _evaluation(tmp_path)
    path = attempt_root / "receipts" / "ARM-01--P00-TAC-DOC.json"
    receipt = json.loads(path.read_text(encoding="ascii"))
    receipt["quality"]["recall_at_100_out"] = 0.5
    path.write_text(json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n", encoding="ascii")

    with pytest.raises(EvaluatorCloseoutV16Error, match="receipt_sha256 mismatch"):
        validate_evaluator_closeout_inputs(ROOT, attempt_root)


def test_closeout_rejects_protected_field_even_when_rehashed(tmp_path: Path) -> None:
    attempt_root = _evaluation(tmp_path)
    path = attempt_root / "promotion.json"
    promotion = json.loads(path.read_text(encoding="ascii"))
    promotion["qrels"] = []
    promotion["receipt_sha256"] = canonical_sha256(
        {key: value for key, value in promotion.items() if key != "receipt_sha256"}
    )
    path.write_text(json.dumps(promotion, sort_keys=True, separators=(",", ":")) + "\n", encoding="ascii")

    with pytest.raises(EvaluatorCloseoutV16Error, match="protected payload key"):
        validate_evaluator_closeout_inputs(ROOT, attempt_root)
