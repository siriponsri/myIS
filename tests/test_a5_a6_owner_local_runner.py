"""Focused tests for the owner-local A5/A6 execution adapter."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import run_a5_a6_owner_local as runner  # noqa: E402


def _manifest(tmp_path: Path, phase: str, command: list[str]) -> tuple[Path, Path, Path, Path]:
    owner = tmp_path / "owner-store"
    owner.mkdir()
    payload = owner / "opaque-payload"
    payload.mkdir()
    attempt = owner / f"{phase.lower()}-attempt"
    body = {
        "schema_version": runner.SCHEMA,
        "phase": phase,
        "attempt_id": f"{phase.lower()}-goal001-20260822T120000Z-test",
        "status": "READY",
        "execution_permitted": True,
        "expected_units": runner.PHASES[phase]["expected_units"],
        "winner_count": runner.PHASES[phase]["winner_count"],
        "payload_scope": "owner_local_only",
        "remote_upload_allowed": False,
        "protected_payload_included": False,
        "selection_accesses": 0,
        "final_accesses": 0,
        "executor_sha256": runner._sha(command),
    }
    manifest = {**body, "manifest_sha256": runner._sha(body)}
    path = owner / f"{phase.lower()}-manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return owner, payload, attempt, path


def _executor(total: int, result: dict[str, object]) -> list[str]:
    code = (
        "import json; from pathlib import Path; "
        f"print('ARMIndex_PROGRESS completed={total} total={total}', flush=True); "
        f"Path('result.json').write_text(json.dumps({result!r}), encoding='utf-8')"
    )
    return [sys.executable, "-c", code]


def test_a5_runs_with_durable_checkpoint_and_aggregate_receipt(tmp_path: Path) -> None:
    total = runner.PHASES["A5"]["expected_units"]
    command = _executor(total, {"status": "PASS", "metrics": {"recall_at_100": 0.4}})
    owner, payload, attempt, manifest = _manifest(tmp_path, "A5", command)
    receipt = runner.run_phase(
        phase="A5",
        manifest_path=manifest,
        owner_store_root=owner,
        attempt_root=attempt,
        payload_root=payload,
        executor=command,
    )
    assert receipt["status"] == "PASS"
    assert receipt["completed_units"] == total
    assert receipt["final_accesses"] == 1
    checkpoint = json.loads((attempt / "checkpoint.json").read_text(encoding="utf-8"))
    assert checkpoint["completed_units"] == total
    assert checkpoint["manifest_sha256"] == receipt["manifest_sha256"]


def test_missing_payload_fails_before_executor(tmp_path: Path) -> None:
    total = runner.PHASES["A5"]["expected_units"]
    command = _executor(total, {"status": "PASS"})
    owner, payload, attempt, manifest = _manifest(tmp_path, "A5", command)
    payload.rmdir()
    with pytest.raises(runner.RunnerError, match="payload"):
        runner.run_phase(
            phase="A5",
            manifest_path=manifest,
            owner_store_root=owner,
            attempt_root=attempt,
            payload_root=payload,
            executor=command,
        )
    assert not attempt.exists()


def test_a6_requires_one_frozen_a5_winner(tmp_path: Path) -> None:
    total = runner.PHASES["A6"]["expected_units"]
    command = _executor(total, {"status": "PASS", "coverage": {"rows": total}})
    owner, payload, attempt, manifest = _manifest(tmp_path, "A6", command)
    predecessor = owner / "a5-receipt.json"
    value = {"status": "PASS_A5_FINAL_CONFIRMATION", "winner_count": 1, "final_accesses": 1}
    predecessor.write_text(json.dumps(value), encoding="utf-8")
    receipt = runner.run_phase(
        phase="A6",
        manifest_path=manifest,
        owner_store_root=owner,
        attempt_root=attempt,
        payload_root=payload,
        executor=command,
        predecessor_receipt=predecessor,
    )
    assert receipt["status"] == "PASS"
    assert receipt["predecessor_receipt_sha256"] == runner._sha(value)


def test_protected_result_is_rejected(tmp_path: Path) -> None:
    total = runner.PHASES["A5"]["expected_units"]
    command = _executor(total, {"status": "PASS", "per_query": [{"id": "opaque"}]})
    owner, payload, attempt, manifest = _manifest(tmp_path, "A5", command)
    with pytest.raises(runner.RunnerError, match="protected field"):
        runner.run_phase(
            phase="A5",
            manifest_path=manifest,
            owner_store_root=owner,
            attempt_root=attempt,
            payload_root=payload,
            executor=command,
        )
