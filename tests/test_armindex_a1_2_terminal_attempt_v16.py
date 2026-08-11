from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_terminal_attempt_v16 import (
    CURRENT_POINTER_PATH,
    TerminalAttemptV16Error,
    build_current_attempt_pointer,
    build_terminal_attempt_receipt,
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
    ):
        shutil.copy2(ROOT / "schemas" / "armindex" / name, schema_dir / name)
    return tmp_path


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

    result = validate_current_attempt_pointer(root)
    assert result["receipt"]["status"] == "PASS"
    assert result["receipt"]["coverage"]["completed_logical_cells"] == 25
    assert result["pointer"]["attempt_id"] == pointer["attempt_id"]

    model = build_read_model(root)
    assert model["armindex"]["a1_2_current_attempt"]["validated"] is True
    assert model["armindex"]["status"] == "a1_2_terminal_pass_25_of_25_closeout_recorded"


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
