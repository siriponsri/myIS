from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from myis_research.armindex import a2_entry_preflight_v16 as preflight_module
from myis_research.armindex.a1_2_terminal_attempt_v16 import (
    build_current_attempt_pointer,
    build_terminal_attempt_receipt,
    write_current_attempt_pointer,
    write_terminal_attempt_receipt,
)
from myis_research.armindex.a2_entry_preflight_v16 import (
    A2EntryPreflightV16Error,
    evaluate_a2_entry_preflight,
    main,
)

ROOT = Path(__file__).resolve().parents[1]


def _root(tmp_path: Path) -> Path:
    schema_directory = tmp_path / "schemas" / "armindex"
    schema_directory.mkdir(parents=True)
    for name in (
        "a1.2-terminal-attempt-receipt.v16.json",
        "a1.2-current-attempt-pointer.v16.json",
    ):
        shutil.copy2(ROOT / "schemas" / "armindex" / name, schema_directory / name)
    return tmp_path


def _write_current(root: Path, *, disposition: str = "REUSE_ELIGIBLE", status: str = "PASS") -> None:
    kwargs: dict[str, str] = {
        "provider_disposition_receipt_sha256": "d" * 64,
        "final_charge_usd": "12.345678",
        "claim_boundary": "Aggregate-safe terminal binding only; protected inputs and per-query outcomes remain Owner-local.",
    }
    if status == "PASS":
        kwargs.update(
            safe_return_sha256="a" * 64,
            evaluator_receipt_sha256="b" * 64,
            promotion_receipt_sha256="c" * 64,
        )
    else:
        kwargs["failure_evidence_sha256"] = "e" * 64
    receipt = build_terminal_attempt_receipt(
        repository_root=root,
        attempt_id="a12-v16-20260811-r15",
        status=status,
        completed_logical_cells=25 if status == "PASS" else 24,
        provider_disposition_status=disposition,
        **kwargs,
    )
    receipt_path = write_terminal_attempt_receipt(root, receipt)
    pointer = build_current_attempt_pointer(
        receipt,
        target_sha256=hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
    )
    write_current_attempt_pointer(root, pointer)


def _post_freeze_projection() -> dict[str, object]:
    return {
        "validated": True,
        "status": "complete_audit_passed_measured_a2_closed",
        "independent_audit_status": "PASS",
        "candidate_count": 52,
        "matched_candidate_count": 40,
        "conditional_reserve_candidate_count": 12,
        "manifest_sha256": "a" * 64,
        "manifest_file_sha256": "b" * 64,
        "freeze_receipt_sha256": "c" * 64,
        "freeze_receipt_file_sha256": "d" * 64,
        "lock_sha256": "e" * 64,
        "lock_file_sha256": "f" * 64,
        "independent_audit_receipt_sha256": "1" * 64,
        "independent_audit_receipt_file_sha256": "2" * 64,
        "measured_a2_started": False,
        "rep_dev_accessed_for_measurement": False,
        "gpu_work_performed": False,
        "provider_admission_performed": False,
        "provider_execution_adoption_performed": False,
        "protected_data_accessed": False,
        "harness_dev_accesses": 0,
        "selection_accesses": 0,
        "final_accesses": 0,
    }


def _mock_closeout_projection(
    monkeypatch: pytest.MonkeyPatch,
    *,
    disposition: str = "REUSE_ELIGIBLE",
    post_freeze: dict[str, object] | None = None,
) -> None:
    def build_model(_: Path) -> dict[str, object]:
        return {
            "read_model_revision": "f" * 64,
            "armindex": {
                "a1_2_current_attempt": {
                    "validated": True,
                    "attempt_id": "a12-v16-20260811-r15",
                    "status": "PASS",
                    "provider_disposition_status": disposition,
                    "receipt_file_sha256": preflight_module.validate_current_attempt_pointer(
                        _
                    )["receipt_file_sha256"],
                    "measured_result_summary": {
                        "status": "PASS",
                        "attempt_id": "a12-v16-20260811-r15",
                        "summary_sha256": "7" * 64,
                        "summary_file_sha256": "8" * 64,
                        "promoted_arm_ids": ["ARM-01", "ARM-02", "ARM-03"],
                    },
                },
                "counters": {
                    "measured_runs": 1,
                    "selection_accesses": 0,
                    "final_accesses": 0,
                },
                "phases": [
                    {
                        "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
                        "status": "complete",
                    },
                    {
                        "phase_id": "A2_PER_ARM_AUTOINDEX",
                        "status": "blocked" if post_freeze is not None else "planned",
                    },
                ],
                "a2_candidate_freeze": post_freeze,
            },
        }

    monkeypatch.setattr(preflight_module, "build_read_model", build_model)
    monkeypatch.setattr(
        preflight_module,
        "build_report_records",
        lambda _root, _model: [
            {
                "report_id": "task-a1-2",
                "status": "completed",
                "scientific_authority": True,
                "claim_boundary": "Aggregate-safe A1.2 measured closeout.",
                "report_sha256": "9" * 64,
            }
        ],
    )


@pytest.mark.parametrize(
    ("disposition", "reuse"), [("REUSE_ELIGIBLE", True), ("DESTROYED", False)])
def test_preflight_requires_pass_25_of_25_and_reports_provider_preparation(
    tmp_path: Path,
    disposition: str,
    reuse: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _root(tmp_path)
    _write_current(root, disposition=disposition)
    _mock_closeout_projection(monkeypatch, disposition=disposition)

    result = evaluate_a2_entry_preflight(root)

    assert result["status"] == "PASS_A2_ENTRY_PREFLIGHT"
    assert result["provider_disposition_status"] == disposition
    assert result["a1_provider_disposition_status"] == disposition
    assert result["a1_reuse_lineage_eligible"] is reuse
    assert result["a2_provider_disposition_status"] == "FRESH_INSTANCE_REQUIRED"
    assert result["reuse_existing_instance_permitted"] is False
    assert result["fresh_a2_provider_admission_required"] is True
    assert result["fresh_a2_execution_adoption_required"] is True
    assert result["new_isolated_remote_root_required"] is True
    assert result["a2_execution_authorized"] is False
    assert result["candidate_evaluation_authorized"] is False
    assert result["a2_phase_status"] == "planned"
    assert result["candidate_freeze"] is None
    assert result["read_model_revision"] == "f" * 64
    assert result["a1_report_sha256"] == "9" * 64
    assert result["measured_result_summary_sha256"] == "7" * 64
    assert result["promoted_arm_ids"] == ["ARM-01", "ARM-02", "ARM-03"]
    assert result["access_counters"] == {
        "harness_dev_accesses": 0,
        "selection_accesses": 0,
        "final_accesses": 0,
    }


def test_preflight_rejects_failed_a1_terminal(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _write_current(root, status="FAILED_CLOSED")

    with pytest.raises(A2EntryPreflightV16Error, match="PASS A1 terminal"):
        evaluate_a2_entry_preflight(root)


def test_preflight_rejects_destroy_required_disposition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _root(tmp_path)
    _write_current(root)
    current = preflight_module.validate_current_attempt_pointer(root)
    current["receipt"]["provider_disposition_status"] = "DESTROY_REQUIRED"
    monkeypatch.setattr(
        preflight_module,
        "validate_current_attempt_pointer",
        lambda _root: current,
    )

    with pytest.raises(A2EntryPreflightV16Error, match="reusable or destroyed"):
        evaluate_a2_entry_preflight(root)


def test_preflight_rejects_a2_still_locked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _root(tmp_path)
    _write_current(root)
    _mock_closeout_projection(monkeypatch)
    original = preflight_module.build_read_model

    def locked_model(repository_root: Path) -> dict[str, object]:
        model = original(repository_root)
        phases = model["armindex"]["phases"]  # type: ignore[index]
        phases[1]["status"] = "locked_until_A1"  # type: ignore[index]
        return model

    monkeypatch.setattr(preflight_module, "build_read_model", locked_model)

    with pytest.raises(A2EntryPreflightV16Error, match="no longer locked"):
        evaluate_a2_entry_preflight(root)


def test_preflight_accepts_only_audited_post_freeze_blocked_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _root(tmp_path)
    _write_current(root)
    _mock_closeout_projection(monkeypatch, post_freeze=_post_freeze_projection())

    result = evaluate_a2_entry_preflight(root)

    assert result["status"] == "PASS_A2_ENTRY_PREFLIGHT"
    assert result["a2_phase_status"] == "blocked"
    assert result["a2_execution_authorized"] is False
    assert result["candidate_evaluation_authorized"] is False
    assert result["candidate_freeze"] == {
        "status": "complete_audit_passed_measured_a2_closed",
        "independent_audit_status": "PASS",
        "candidate_count": 52,
        "matched_candidate_count": 40,
        "conditional_reserve_candidate_count": 12,
        "diagnostic_non_advancing_arms": ["ARM-01", "ARM-02"],
        "manifest_sha256": "a" * 64,
        "manifest_file_sha256": "b" * 64,
        "freeze_receipt_sha256": "c" * 64,
        "freeze_receipt_file_sha256": "d" * 64,
        "lock_sha256": "e" * 64,
        "lock_file_sha256": "f" * 64,
        "independent_audit_receipt_sha256": "1" * 64,
        "independent_audit_receipt_file_sha256": "2" * 64,
    }


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("independent_audit_status", "REVISE", "PASS candidate-freeze audit"),
        ("candidate_count", 51, "exactly 40\\+12"),
        ("manifest_sha256", "not-a-hash", "immutable candidate-freeze hashes"),
        ("provider_admission_performed", True, "safety flags"),
        ("selection_accesses", 1, "access counters"),
    ],
)
def test_preflight_rejects_invalid_post_freeze_blocked_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    key: str,
    value: object,
    message: str,
) -> None:
    root = _root(tmp_path)
    _write_current(root)
    post_freeze = _post_freeze_projection()
    post_freeze[key] = value
    _mock_closeout_projection(monkeypatch, post_freeze=post_freeze)

    with pytest.raises(A2EntryPreflightV16Error, match=message):
        evaluate_a2_entry_preflight(root)


def test_preflight_cli_is_read_only(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _root(tmp_path)
    _write_current(root)
    _mock_closeout_projection(monkeypatch)
    before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))

    assert main(["--repository-root", str(root)]) == 0

    result = json.loads(capsys.readouterr().out)
    after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
    assert result["status"] == "PASS_A2_ENTRY_PREFLIGHT"
    assert after == before
