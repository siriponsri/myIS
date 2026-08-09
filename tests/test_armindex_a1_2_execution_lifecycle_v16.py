from __future__ import annotations

import hashlib
import io
import json
import sys
import tarfile
from pathlib import Path

import pytest

import myis_research.armindex.a1_2_execution_lifecycle_v16 as lifecycle
from myis_research.armindex.a1_2_execution_lifecycle_v16 import (
    ExecutionLifecycleV16Error,
    build_safe_export,
    complete_attempt,
    completed_cells,
    explicit_environment,
    initialize_attempt,
    invoke_executor_cell,
    record_cell_checkpoint,
    resume_plan,
    supervise_commands,
    teardown_attempt,
    validate_executor_interface,
    validate_production_safe_return,
    validate_safe_export_archive,
)
from myis_research.armindex.a1_2_safe_return_v16 import ARM_IDS, PROGRAM_IDS
from myis_research.kernel.canonical import canonical_sha256

GATES = {
    "provider_admission": "NOT_REQUIRED_SYNTHETIC",
    "execution_adoption": "SYNTHETIC_ONLY",
    "watchdog_ttl": "SYNTHETIC_ONLY",
    "protected_boundary": "PASS",
    "frozen_bindings": "PASS",
}
IDENTITY = {"bundle": "a" * 64, "request": "b" * 64, "transfer": "c" * 64}
PRODUCTION_GATES = {name: "PASS" for name in GATES}


def _attempt(tmp_path: Path) -> tuple[Path, str]:
    output, attempt_id = tmp_path / "output", "a12-v16-synthetic"
    initialize_attempt(output, attempt_id, gates=GATES, execution_identity=IDENTITY, executor_sha256="d" * 64, execution_mode="synthetic")
    return output, attempt_id


def _result(output: Path, attempt_id: str, cell: str) -> Path:
    target = output / "attempts" / attempt_id / "results" / f"{cell}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    body = {"schema_version": "synthetic", "attempt_id": attempt_id, "cell_id": cell, "aggregate_safe": True, "metric_count": 0}
    target.write_text(json.dumps({**body, "receipt_sha256": canonical_sha256(body)}, sort_keys=True) + "\n", encoding="utf-8")
    return target


def _runner_result(output: Path, attempt_id: str, cell: str, *, include_raw_token: bool = False) -> Path:
    target = output / "attempts" / attempt_id / "results" / f"{cell}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    body: dict[str, object] = {
        "schema_version": "myis.armindex-a1.2-owner-local-cell-receipt.v16",
        "attempt_id": attempt_id,
        "cell_id": cell,
        "aggregate_safe": True,
        "work_token_count": 150,
        "work_token_set_sha256": "e" * 64,
    }
    if include_raw_token:
        body["work_token"] = "Q-" + "0" * 32
    target.write_text(json.dumps({**body, "receipt_sha256": canonical_sha256(body)}, sort_keys=True) + "\n", encoding="utf-8")
    return target


def _strict_safe_return_archive(tmp_path: Path, attempt_id: str) -> Path:
    work = [f"Q-{index:032x}" for index in range(150)]
    families = [f"F-{index:032x}" for index in range(100)]
    payloads: dict[str, bytes] = {}
    members: list[dict[str, object]] = []
    for arm in ARM_IDS:
        for program in PROGRAM_IDS:
            stem = f"{arm}--{program.replace('-', '_')}"
            ranking_name = f"rankings/{stem}.jsonl"
            ranking = "".join(
                json.dumps({"work_token": token, "family_tokens": families}, sort_keys=True, separators=(",", ":")) + "\n"
                for token in work
            ).encode("ascii")
            ranking_sha = hashlib.sha256(ranking).hexdigest()
            payloads[ranking_name] = ranking
            receipt_body = {
                "schema_version": "myis.armindex-a1.2-safe-return-resource-receipt.v16",
                "attempt_id": attempt_id, "arm_id": arm, "program_id": program, "status": "PASS",
                "checkpoint_sha256": "a" * 64, "ranking_sha256": ranking_sha,
            }
            receipt = {**receipt_body, "receipt_sha256": canonical_sha256(receipt_body)}
            receipt_name = f"receipts/{stem}.json"
            payloads[receipt_name] = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode("ascii")
            for kind, name in (("ranking", ranking_name), ("receipt", receipt_name)):
                data = payloads[name]
                members.append({"kind": kind, "arm_id": arm, "program_id": program, "relative_path": name, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)})
    manifest_body = {
        "schema_version": "myis.armindex-a1.2-safe-return-manifest.v16", "attempt_id": attempt_id,
        "status": "PASS", "transfer_manifest_sha256": "b" * 64, "split_commitment_sha256": "c" * 64,
        "ephemeral_token_map_sha256": "d" * 64, "work_token_set_sha256": canonical_sha256({"work_tokens": work}),
        "members": members,
    }
    payloads["safe-return-manifest.v16.json"] = json.dumps({**manifest_body, "manifest_sha256": canonical_sha256(manifest_body)}, sort_keys=True, separators=(",", ":")).encode("ascii")
    archive = tmp_path / "strict-safe-return.tar.gz"
    with tarfile.open(archive, "w:gz") as bundle:
        for name, data in sorted(payloads.items()):
            info = tarfile.TarInfo(name)
            info.size = len(data)
            bundle.addfile(info, io.BytesIO(data))
    return archive


def test_v16_requires_all_admission_gates_and_drops_environment() -> None:
    with pytest.raises(ExecutionLifecycleV16Error, match="gates"):
        initialize_attempt(Path("/tmp"), "bad", gates={}, execution_identity=IDENTITY, executor_sha256="d" * 64)
    environment = explicit_environment({"PATH": "/usr/bin", "LANG": "C.UTF-8"}, cuda_visible_devices="2")
    assert set(environment) <= {"CUDA_VISIBLE_DEVICES", "HF_HUB_OFFLINE", "LANG", "LC_ALL", "PATH", "PIP_NO_INDEX", "PYTHONDONTWRITEBYTECODE", "PYTHONHASHSEED", "TZ", "TRANSFORMERS_OFFLINE", "TOKENIZERS_PARALLELISM"}
    assert environment["HF_HUB_OFFLINE"] == "1" and environment["CUDA_VISIBLE_DEVICES"] == "2"
    with pytest.raises(ExecutionLifecycleV16Error, match="forced policy"):
        explicit_environment({"HF_HUB_OFFLINE": "0"})
    assert validate_executor_interface()["callback"] == "execute_program_cell"
    seen: list[str] = []

    def fake_executor(**kwargs: object) -> tuple[object, ...]:
        seen.append(str(kwargs["program_id"]))
        return ()

    invoke_executor_cell(fake_executor, arm_id="ARM-01", program_id="P02-CLAIM1", corpus=(), query="q")
    assert seen == ["P02-FIRST-CLAIM"]


def test_v16_checkpoint_resume_is_identity_bound_and_requires_all_25(tmp_path: Path) -> None:
    output, attempt_id = _attempt(tmp_path)
    record_cell_checkpoint(output, attempt_id, "ARM-01--P00-TAC-DOC", _result(output, attempt_id, "ARM-01--P00-TAC-DOC"))
    assert completed_cells(output, attempt_id) == ("ARM-01--P00-TAC-DOC",)
    attempt = initialize_attempt(output, attempt_id, gates=GATES, execution_identity=IDENTITY, executor_sha256="d" * 64, execution_mode="synthetic")
    assert resume_plan(output, attempt_id)["pending"] == tuple(cell for cell in attempt["required_cells"] if cell != "ARM-01--P00-TAC-DOC")
    with pytest.raises(ExecutionLifecycleV16Error, match="25/25"):
        complete_attempt(output, attempt_id)
    with pytest.raises(ExecutionLifecycleV16Error, match="exact same"):
        initialize_attempt(output, attempt_id, gates=GATES, execution_identity={"bundle": "e" * 64}, executor_sha256="d" * 64, execution_mode="synthetic")


def test_v16_checkpoint_accepts_aggregate_token_counts_but_rejects_raw_tokens(tmp_path: Path) -> None:
    output, attempt_id = _attempt(tmp_path)
    cell = "ARM-01--P00-TAC-DOC"
    record_cell_checkpoint(output, attempt_id, cell, _runner_result(output, attempt_id, cell))
    assert completed_cells(output, attempt_id) == (cell,)

    raw_output, raw_attempt_id = _attempt(tmp_path / "raw")
    with pytest.raises(ExecutionLifecycleV16Error, match="protected field"):
        record_cell_checkpoint(
            raw_output,
            raw_attempt_id,
            cell,
            _runner_result(raw_output, raw_attempt_id, cell, include_raw_token=True),
        )


def test_v16_sibling_failure_is_reaped_and_safe_export_is_same_attempt_25_of_25(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output, attempt_id = _attempt(tmp_path)
    # The shipped worker is Linux-only; retain a synthetic process identity on Windows.
    monkeypatch.setattr(lifecycle, "_proc_start", lambda pid, proc_root=Path("/proc"): str(pid))
    commands = {
        "good-worker": [sys.executable, "-c", "import time; time.sleep(10)"],
        "bad-worker": [sys.executable, "-c", "raise SystemExit(7)"],
    }
    with pytest.raises(ExecutionLifecycleV16Error, match="siblings reaped"):
        supervise_commands(output, attempt_id, commands, base_environment={"PATH": str(Path(sys.executable).parent)}, heartbeat_interval_seconds=0.01)

    output, attempt_id = _attempt(tmp_path / "pass")
    for arm in range(1, 6):
        for program in ("P00-TAC-DOC", "P01-TA-DOC", "P02-CLAIM1", "P03-PASSAGE", "P04-SECTION-MULTIVIEW"):
            cell = f"ARM-0{arm}--{program}"
            record_cell_checkpoint(output, attempt_id, cell, _result(output, attempt_id, cell))
    complete_attempt(output, attempt_id)
    teardown_attempt(output, attempt_id, children_reaped=True)
    receipt = build_safe_export(output, attempt_id, output / "exports" / f"{attempt_id}.tar.gz")
    assert receipt["status"] == "PASS" and receipt["attempt_id"] == attempt_id
    assert build_safe_export(output, attempt_id, output / "exports" / f"{attempt_id}.tar.gz") == receipt
    assert validate_safe_export_archive(output / "exports" / f"{attempt_id}.tar.gz")["status"] == "PASS"


def test_v16_production_rejects_generic_payload_and_accepts_exact_safe_return(tmp_path: Path) -> None:
    output, attempt_id = tmp_path / "production-output", "a12-v16-production"
    initialize_attempt(output, attempt_id, gates=PRODUCTION_GATES, execution_identity=IDENTITY, executor_sha256="d" * 64)
    for arm in range(1, 6):
        for program in ("P00-TAC-DOC", "P01-TA-DOC", "P02-CLAIM1", "P03-PASSAGE", "P04-SECTION-MULTIVIEW"):
            cell = f"ARM-0{arm}--{program}"
            record_cell_checkpoint(output, attempt_id, cell, _result(output, attempt_id, cell))
    complete_attempt(output, attempt_id)
    teardown_attempt(output, attempt_id, children_reaped=True)
    with pytest.raises(ExecutionLifecycleV16Error, match="synthetic-only"):
        build_safe_export(output, attempt_id, output / "exports" / f"{attempt_id}.tar.gz")
    receipt = validate_production_safe_return(output, attempt_id, _strict_safe_return_archive(tmp_path, attempt_id))
    assert receipt["status"] == "PASS" and receipt["member_cells"] == 25 and receipt["work_rows"] == 150
