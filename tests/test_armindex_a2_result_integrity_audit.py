from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from myis_research.armindex import a2_result_integrity_audit as audit_module
from myis_research.kernel.canonical import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]
ATTEMPT = "a2-rigor-audit-001"
ARMS = ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")


def _hash(char: str) -> str:
    return char * 64


def _signed(value: dict[str, Any], field: str) -> dict[str, Any]:
    return {**value, field: canonical_sha256(value)}


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="ascii")


def _fixture_root(tmp_path: Path) -> tuple[Path, dict[str, Path]]:
    root = tmp_path / "repository"
    schema_directory = root / "schemas/armindex"
    schema_directory.mkdir(parents=True)
    for name in (
        "a2-execution-closeout-receipt.v1.json",
        "a2-safe-return-receipt.v1.json",
        "a2-lifecycle-checkpoint.v1.json",
        "a2-winner-selection-receipt.v1.json",
        "a2-result-integrity-audit.v1.json",
    ):
        shutil.copy2(ROOT / "schemas/armindex" / name, schema_directory / name)

    freeze = {
        "manifest_sha256": _hash("a"),
        "freeze_receipt_sha256": _hash("b"),
        "lock_sha256": _hash("c"),
    }
    winner_receipts: dict[str, dict[str, Any]] = {}
    for index, arm_id in enumerate(ARMS, start=1):
        winner_receipts[arm_id] = _signed(
            {
                "schema_version": "myis.armindex-a2-winner-selection-receipt.v1",
                "receipt_id": f"{ATTEMPT}-winner-v1",
                "attempt_id": ATTEMPT,
                "status": "PASS_A2_WINNER_SELECTED",
                "arm_id": arm_id,
                "winner_candidate_id": f"a2-arm-{index:02d}-matched-b1-exploit",
                "diagnostic_non_advancing": arm_id in {"ARM-01", "ARM-02"},
                "advancement_eligible": arm_id not in {"ARM-01", "ARM-02"},
                "train_evaluation_receipt_sha256": _hash(format(index, "x")),
                "strict_tie_rejected": True,
                "freeze_bindings": freeze,
            },
            "receipt_sha256",
        )
    winner_hashes = {arm_id: winner_receipts[arm_id]["receipt_sha256"] for arm_id in ARMS}
    coverage = {
        "status": "PASS_A2_EXACT_COVERAGE",
        "attempt_id": ATTEMPT,
        "candidate_count": 52,
        "matched_candidate_count": 40,
        "conditional_reserve_candidate_count": 12,
        "candidate_result_set_sha256": _hash("d"),
        "winner_receipts": winner_receipts,
        "freeze_bindings": freeze,
    }
    safe_return = _signed(
        {
            "schema_version": "myis.armindex-a2-safe-return-receipt.v1",
            "receipt_id": f"{ATTEMPT}-safe-return-v1",
            "attempt_id": ATTEMPT,
            "status": "PASS_A2_SAFE_RETURN",
            "archive_sha256": _hash("e"),
            "archive_manifest_sha256": _hash("f"),
            "aggregate_artifact_count": 9,
            "protected_payload_included": False,
            "remote_root": f"/opt/myis/{ATTEMPT}",
            "freeze_bindings": freeze,
        },
        "receipt_sha256",
    )
    checkpoint = _signed(
        {
            "schema_version": "myis.armindex-a2-lifecycle-checkpoint.v1",
            "checkpoint_id": f"{ATTEMPT}-checkpoint-0052",
            "attempt_id": ATTEMPT,
            "sequence": 52,
            "previous_checkpoint_sha256": _hash("0"),
            "status": "SAFE_RETURNED",
            "completed_candidate_count": 52,
            "failed_candidate_count": 0,
            "resume_allowed": False,
            "freeze_bindings": freeze,
        },
        "checkpoint_sha256",
    )
    closeout = _signed(
        {
            "schema_version": "myis.armindex-a2-execution-closeout-receipt.v1",
            "receipt_id": f"{ATTEMPT}-execution-closeout-v1",
            "attempt_id": ATTEMPT,
            "status": "PASS_A2_EXECUTION_CLOSEOUT",
            "evidence_class": "measured_development_aggregate",
            "candidate_count": 52,
            "matched_candidate_count": 40,
            "conditional_reserve_candidate_count": 12,
            "arm_winner_receipt_sha256s": winner_hashes,
            "candidate_result_set_sha256": coverage["candidate_result_set_sha256"],
            "safe_return_receipt_sha256": safe_return["receipt_sha256"],
            "terminal_checkpoint_sha256": checkpoint["checkpoint_sha256"],
            "workers_reaped": True,
            "protected_scan_passed": True,
            "diagnostic_non_advancing_arms": ["ARM-01", "ARM-02"],
            "primary_advancement_arms": ["ARM-03", "ARM-05", "ARM-04"],
            "claim_evidence_pointers": ["outputs/a2/coverage.json"],
            "freeze_bindings": freeze,
        },
        "receipt_sha256",
    )
    paths = {
        "closeout": root / "outputs/a2/closeout.json",
        "coverage": root / "outputs/a2/coverage.json",
        "safe_return": root / "outputs/a2/safe-return.json",
        "terminal_checkpoint": root / "outputs/a2/checkpoint.json",
    }
    _write(paths["closeout"], closeout)
    _write(paths["coverage"], coverage)
    _write(paths["safe_return"], safe_return)
    _write(paths["terminal_checkpoint"], checkpoint)
    return root, paths


def _audit(root: Path, paths: dict[str, Path]) -> dict[str, Any]:
    return audit_module.audit_completed_closeout(
        root,
        closeout_path=paths["closeout"],
        coverage_path=paths["coverage"],
        safe_return_path=paths["safe_return"],
        terminal_checkpoint_path=paths["terminal_checkpoint"],
    )


def test_audit_completed_closeout_writes_aggregate_only_artifact(tmp_path: Path) -> None:
    root, paths = _fixture_root(tmp_path)
    result = _audit(root, paths)
    assert result["status"] == "PASS_A2_RESULT_INTEGRITY"
    assert result["closeout"]["candidate_count"] == 52
    assert result["coverage"]["matched_candidate_count"] == 40
    assert set(result["closeout"]["arm_winner_receipt_sha256s"]) == set(ARMS)
    assert result["audit_sha256"] == canonical_sha256(
        {key: value for key, value in result.items() if key != "audit_sha256"}
    )

    output = root / "outputs/audits/rigor/a2-rigor-audit-001-result-integrity-audit-v1.json"
    written = audit_module.write_audit(
        root,
        output_path=output,
        closeout_path=paths["closeout"],
        coverage_path=paths["coverage"],
        safe_return_path=paths["safe_return"],
        terminal_checkpoint_path=paths["terminal_checkpoint"],
    )
    assert json.loads(output.read_text(encoding="ascii")) == written


@pytest.mark.parametrize(
    ("target", "mutate"),
    [
        ("closeout", lambda value: value.update({"receipt_sha256": _hash("0")})),
        ("coverage", lambda value: value.update({"matched_candidate_count": 39})),
        ("safe_return", lambda value: value.update({"protected_payload_included": True})),
        ("terminal_checkpoint", lambda value: value.update({"attempt_id": "a2-other-audit-001"})),
        ("coverage", lambda value: value.update({"query_id": "must-not-enter-audit"})),
        ("coverage", lambda value: value.update({"raw_rankings": "must-not-enter-audit"})),
    ],
)
def test_audit_rejects_hash_coverage_protection_and_lineage_drift(
    tmp_path: Path, target: str, mutate: Any
) -> None:
    root, paths = _fixture_root(tmp_path)
    value = json.loads(paths[target].read_text(encoding="ascii"))
    mutate(value)
    _write(paths[target], value)
    with pytest.raises(audit_module.A2ResultIntegrityAuditError):
        _audit(root, paths)


def test_audit_rejects_closeout_winner_hash_drift_and_unsafe_output(tmp_path: Path) -> None:
    root, paths = _fixture_root(tmp_path)
    closeout = json.loads(paths["closeout"].read_text(encoding="ascii"))
    closeout["arm_winner_receipt_sha256s"]["ARM-05"] = _hash("9")
    closeout = _signed({key: value for key, value in closeout.items() if key != "receipt_sha256"}, "receipt_sha256")
    _write(paths["closeout"], closeout)
    with pytest.raises(audit_module.A2ResultIntegrityAuditError, match="winner receipt bindings"):
        _audit(root, paths)

    root, paths = _fixture_root(tmp_path / "second")
    with pytest.raises(audit_module.A2ResultIntegrityAuditError, match="outputs/audits/rigor"):
        audit_module.write_audit(
            root,
            output_path=root / "outputs/a2/actual-result.json",
            closeout_path=paths["closeout"],
            coverage_path=paths["coverage"],
            safe_return_path=paths["safe_return"],
            terminal_checkpoint_path=paths["terminal_checkpoint"],
        )
