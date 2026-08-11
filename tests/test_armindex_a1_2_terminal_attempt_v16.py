from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_measured_result_summary_v16 import summary_path
from myis_research.armindex.a1_2_terminal_attempt_v16 import (
    CURRENT_POINTER_PATH,
    TerminalAttemptV16Error,
    build_current_attempt_pointer,
    build_terminal_attempt_receipt,
    main,
    validate_current_attempt_pointer,
    validate_terminal_attempt_receipt,
    write_current_attempt_pointer,
    write_terminal_attempt_receipt,
)
from myis_research.kernel.canonical import canonical_json, canonical_sha256
from myis_research.projections.read_model import build_read_model

ROOT = Path(__file__).resolve().parents[1]


def _root(tmp_path: Path) -> Path:
    schema_dir = tmp_path / "schemas" / "armindex"
    schema_dir.mkdir(parents=True)
    for name in (
        "a1.2-terminal-attempt-receipt.v16.json",
        "a1.2-current-attempt-pointer.v16.json",
        "a1.2-measured-result-summary.v16.json",
    ):
        shutil.copy2(ROOT / "schemas" / "armindex" / name, schema_dir / name)
    return tmp_path


def _write_measured_summary(root: Path, attempt_id: str) -> None:
    arm_results = [
        {
            "arm_id": f"ARM-{index:02d}",
            "program_count": 5,
            "out_recall_at_100_mean": 0.5,
            "out_ndcg_at_100_mean": 0.4,
            "out_ndcg_at_10_mean": 0.3,
            "search_latency_p95_ms_mean": 10.0,
            "wall_seconds_sum": 20.0,
            "failure_rate_mean": 0.0,
        }
        for index in range(1, 6)
    ]
    body = {
        "schema_version": "myis.armindex-a1.2-measured-result-summary.v16",
        "summary_id": f"{attempt_id}-measured-result-summary-v16",
        "attempt_id": attempt_id,
        "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
        "task_id": "A1.2",
        "status": "PASS",
        "evidence_class": "measured_development_aggregate",
        "scientific_authority": True,
        "claim_boundary": "Aggregate-only measured summary; protected inputs and per-query outcomes remain Owner-local.",
        "metric_contract": {
            "primary": "OUT Recall@100",
            "secondary": ["OUT nDCG@100", "OUT nDCG@10"],
        },
        "coverage": {
            "arm_count": 5,
            "programs_per_arm": 5,
            "completed_logical_cells": 25,
            "required_logical_cells": 25,
        },
        "arm_results": arm_results,
        "promoted_arm_ids": ["ARM-01", "ARM-02", "ARM-03"],
        "lineage": {
            "safe_return_archive_sha256": "a" * 64,
            "cell_receipt_set_sha256": "f" * 64,
            "promotion_receipt_sha256": "c" * 64,
            "evaluator_closeout_receipt_sha256": "b" * 64,
        },
        "access_counters": {
            "harness_dev_accesses": 0,
            "selection_accesses": 0,
            "final_accesses": 0,
        },
    }
    value = {**body, "summary_sha256": canonical_sha256(body)}
    path = root / summary_path(attempt_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="ascii")


def _receipt(
    root: Path, *, status: str, completed: int, provider_disposition_status: str = "DESTROYED"
) -> dict[str, object]:
    kwargs: dict[str, str] = {}
    if status == "PASS":
        kwargs.update(
            safe_return_sha256="a" * 64,
            evaluator_receipt_sha256="b" * 64,
            promotion_receipt_sha256="c" * 64,
        )
    else:
        kwargs["failure_evidence_sha256"] = "e" * 64
    return build_terminal_attempt_receipt(
        repository_root=root,
        attempt_id="a12-v16-20260811-r14",
        status=status,
        completed_logical_cells=completed,
        provider_disposition_receipt_sha256="d" * 64,
        provider_disposition_status=provider_disposition_status,
        final_charge_usd="12.345678",
        claim_boundary="Aggregate-safe terminal binding only; protected inputs and per-query outcomes remain Owner-local.",
        **kwargs,
    )


def _write_current(root: Path, receipt: dict[str, object]) -> dict[str, object]:
    receipt_path = write_terminal_attempt_receipt(root, receipt)
    pointer = build_current_attempt_pointer(
        receipt,
        target_sha256=hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
    )
    write_current_attempt_pointer(root, pointer)
    return pointer


def test_terminal_pass_requires_and_projects_complete_25_of_25(tmp_path: Path) -> None:
    root = _root(tmp_path)
    receipt = _receipt(root, status="PASS", completed=25)
    pointer = _write_current(root, receipt)
    _write_measured_summary(root, str(receipt["attempt_id"]))

    result = validate_current_attempt_pointer(root)
    assert result["receipt"]["status"] == "PASS"
    assert result["receipt"]["coverage"]["completed_logical_cells"] == 25
    assert result["pointer"]["attempt_id"] == pointer["attempt_id"]

    model = build_read_model(root)
    assert model["armindex"]["a1_2_current_attempt"]["validated"] is True
    assert model["armindex"]["status"] == "a1_2_terminal_pass_25_of_25_closeout_recorded"
    assert model["armindex"]["counters"]["measured_runs"] == 1
    assert model["armindex"]["a1_2_current_attempt"]["measured_result_summary"][
        "promoted_arm_ids"
    ] == ["ARM-01", "ARM-02", "ARM-03"]


def test_terminal_failed_closed_is_valid_without_25_of_25(tmp_path: Path) -> None:
    root = _root(tmp_path)
    receipt = _receipt(
        root,
        status="FAILED_CLOSED",
        completed=24,
        provider_disposition_status="REUSE_ELIGIBLE",
    )
    _write_current(root, receipt)

    result = validate_current_attempt_pointer(root)
    assert result["receipt"]["status"] == "FAILED_CLOSED"
    assert result["receipt"]["scientific_authority"] is False
    assert result["receipt"]["coverage"]["completed_logical_cells"] == 24
    assert "safe_return_sha256" not in result["receipt"]
    assert result["receipt"]["failure_evidence_sha256"] == "e" * 64
    assert result["receipt"]["provider_disposition_status"] == "REUSE_ELIGIBLE"

    model = build_read_model(root)
    assert model["armindex"]["a1_2_current_attempt"]["validated"] is True
    assert model["armindex"]["a1_2_current_attempt"]["status"] == "FAILED_CLOSED"
    assert model["armindex"]["status"] == "a1_2_terminal_failed_closed_retry_required"
    assert model["armindex"]["next_command"] == (
        "PREPARE_FRESH_A1_SAME_INSTANCE_ADMISSION_AND_RETRY_25_OF_25_BEFORE_A2"
    )


def test_terminal_pass_rejects_incomplete_provider_disposition(tmp_path: Path) -> None:
    root = _root(tmp_path)
    with pytest.raises(TerminalAttemptV16Error):
        _receipt(
            root,
            status="PASS",
            completed=25,
            provider_disposition_status="DESTROY_REQUIRED",
        )


def test_terminal_pass_rejects_incomplete_coverage(tmp_path: Path) -> None:
    root = _root(tmp_path)
    receipt = _receipt(root, status="PASS", completed=25)
    receipt["coverage"]["completed_logical_cells"] = 24
    receipt["receipt_sha256"] = canonical_sha256(
        {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    )
    with pytest.raises(TerminalAttemptV16Error, match="schema validation failed"):
        validate_terminal_attempt_receipt(root, receipt)


def test_terminal_failed_closed_rejects_dummy_success_hashes(tmp_path: Path) -> None:
    root = _root(tmp_path)
    receipt = _receipt(root, status="FAILED_CLOSED", completed=0)
    receipt["safe_return_sha256"] = "a" * 64
    receipt["receipt_sha256"] = canonical_sha256(
        {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    )

    with pytest.raises(TerminalAttemptV16Error, match="schema validation failed"):
        validate_terminal_attempt_receipt(root, receipt)


def test_current_pointer_rejects_tampered_terminal_receipt(tmp_path: Path) -> None:
    root = _root(tmp_path)
    receipt = _receipt(root, status="FAILED_CLOSED", completed=24)
    _write_current(root, receipt)
    receipt_path = root / "campaigns/armindex-multiretriever-v2/evidence/a1.2-terminal-attempts/a12-v16-20260811-r14.receipt.v16.json"
    receipt_path.write_text(receipt_path.read_text(encoding="ascii").replace("FAILED_CLOSED", "PASS"), encoding="ascii")

    with pytest.raises(TerminalAttemptV16Error, match="file hash mismatch"):
        validate_current_attempt_pointer(root)


def test_current_pointer_rejects_target_hash_mismatch(tmp_path: Path) -> None:
    root = _root(tmp_path)
    receipt = _receipt(root, status="FAILED_CLOSED", completed=24)
    receipt_path = write_terminal_attempt_receipt(root, receipt)
    pointer = build_current_attempt_pointer(receipt, target_sha256="0" * 64)
    pointer_path = root / CURRENT_POINTER_PATH
    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    pointer_path.write_text(canonical_json(pointer) + "\n", encoding="ascii")

    assert receipt_path.is_file()
    with pytest.raises(TerminalAttemptV16Error, match="file hash mismatch"):
        validate_current_attempt_pointer(root)
    model = build_read_model(root)
    assert model["armindex"]["a1_2_current_attempt"]["status"] == "INVALID"
    assert model["armindex"]["status"] == "a1_2_current_terminal_pointer_invalid_fail_closed"


def test_terminal_receipt_rejects_protected_fields_even_with_a_valid_self_hash(tmp_path: Path) -> None:
    root = _root(tmp_path)
    receipt = _receipt(root, status="FAILED_CLOSED", completed=24)
    receipt["qrels"] = []
    receipt["receipt_sha256"] = canonical_sha256(
        {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    )

    with pytest.raises(TerminalAttemptV16Error, match="protected payload key"):
        validate_terminal_attempt_receipt(root, receipt)


def test_r13_remains_historical_when_no_current_pointer_exists(tmp_path: Path) -> None:
    root = _root(tmp_path)
    relative = Path("outputs/audits/armindex/a1.2-v16-r13-failure-audit-20260810.json")
    target = root / relative
    target.parent.mkdir(parents=True)
    shutil.copy2(ROOT / relative, target)

    model = build_read_model(root)
    assert model["armindex"]["a1_2_r13_failure"]["validated"] is True
    assert model["armindex"]["a1_2_current_attempt"]["validated"] is False
    assert "r13_failed_closed" not in model["armindex"]["status"]


def test_terminal_cli_writes_pass_receipt_and_current_pointer(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _root(tmp_path)
    common = [
        "--repository-root", str(root),
        "--attempt-id", "a12-v16-20260811-r15",
        "--status", "PASS",
        "--completed-logical-cells", "25",
        "--provider-disposition-receipt-sha256", "d" * 64,
        "--provider-disposition-status", "DESTROYED",
        "--final-charge-usd", "12.345678",
        "--claim-boundary", "Aggregate-safe terminal binding only; protected inputs and per-query outcomes remain Owner-local.",
        "--safe-return-sha256", "a" * 64,
        "--evaluator-receipt-sha256", "b" * 64,
        "--promotion-receipt-sha256", "c" * 64,
    ]

    assert main(["write", *common]) == 0
    receipt_result = json.loads(capsys.readouterr().out)
    assert receipt_result["status"] == "PASS"
    assert receipt_result["receipt_uri"].endswith("a12-v16-20260811-r15.receipt.v16.json")

    assert main([
        "write-pointer", "--repository-root", str(root),
        "--attempt-id", "a12-v16-20260811-r15",
    ]) == 0
    pointer_result = json.loads(capsys.readouterr().out)
    assert pointer_result["status"] == "PASS"
    assert pointer_result["pointer_uri"] == CURRENT_POINTER_PATH.as_posix()
    assert validate_current_attempt_pointer(root)["receipt"]["status"] == "PASS"


def test_terminal_cli_rejects_incomplete_pass_receipt(tmp_path: Path) -> None:
    root = _root(tmp_path)
    with pytest.raises(SystemExit, match="2"):
        main([
            "write", "--repository-root", str(root),
            "--attempt-id", "a12-v16-20260811-r15",
            "--status", "PASS",
            "--completed-logical-cells", "24",
            "--provider-disposition-receipt-sha256", "d" * 64,
            "--provider-disposition-status", "DESTROYED",
            "--final-charge-usd", "12.345678",
            "--claim-boundary", "Aggregate-safe terminal binding only; protected inputs and per-query outcomes remain Owner-local.",
            "--safe-return-sha256", "a" * 64,
            "--evaluator-receipt-sha256", "b" * 64,
            "--promotion-receipt-sha256", "c" * 64,
        ])
