from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from myis_research.armindex import a2_measured_adapter as adapter
from myis_research.armindex.a2_execution_readiness import frozen_candidates
from myis_research.kernel.canonical import canonical_sha256, file_sha256

ROOT = Path(__file__).resolve().parents[1]
ATTEMPT = "a2-adapter-test01"


def _manifest(owner: Path, *, argv: list[str], code_sha256: str = "d" * 64) -> dict[str, object]:
    bindings = adapter._a1_v16_bindings(ROOT)
    locations = {
        "runtime": "runtime/lock.json",
        "model_lockset": "models/lock.json",
        "data_handoff": "handoff/aggregate.json",
        "evaluator": "aggregate/evaluator.json",
        "corpus": "protected/corpus.jsonl",
        "queries": "protected/queries.jsonl",
        "qrels": "protected/qrels.json",
        "membership": "protected/membership.json",
    }
    artifacts: dict[str, dict[str, str]] = {}
    binding_names = {
        "runtime": "runtime_lock_sha256",
        "model_lockset": "model_lockset_sha256",
        "data_handoff": "data_handoff_sha256",
        "evaluator": "evaluator_receipt_sha256",
    }
    for name, relative in locations.items():
        path = owner / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"safe {name}\n", encoding="ascii")
        artifacts[name] = {
            "path": relative,
            "sha256": file_sha256(path),
            "binding_sha256": bindings[binding_names[name]] if name in binding_names else file_sha256(path),
        }
    for arm_id in ("ARM-02", "ARM-03", "ARM-04", "ARM-05"):
        (owner / "models" / arm_id).mkdir(parents=True, exist_ok=True)
    body: dict[str, object] = {
        "schema_version": "myis.armindex-a2-owner-local-measured-input.v1",
        "status": "READY",
        "attempt_id": ATTEMPT,
        "a1_v16_bindings": bindings,
        "arm_incumbents": {
            "ARM-03": {
                "candidate_id": "a1-arm-03-incumbent",
                "program_sha256": "3" * 64,
                "primary_metric": "0.4134",
            },
            "ARM-05": {
                "candidate_id": "a1-arm-05-incumbent",
                "program_sha256": "5" * 64,
                "primary_metric": "0.36373333333333335",
            },
            "ARM-04": {
                "candidate_id": "a1-arm-04-incumbent",
                "program_sha256": "4" * 64,
                "primary_metric": "0.3406666666666666",
            },
        },
        "owner_artifacts": artifacts,
        "engine": {
            "engine_id": "myis.armindex-a2-owner-local-retriever-evaluator.v1",
            "argv": argv,
            "code_sha256": code_sha256,
            "model_directories": {arm_id: f"models/{arm_id}" for arm_id in ("ARM-02", "ARM-03", "ARM-04", "ARM-05")},
            "output_root": "output",
        },
    }
    return {**body, "manifest_sha256": canonical_sha256(body)}


def _write_manifest(owner: Path, value: dict[str, object]) -> None:
    (owner / "input.json").write_text(json.dumps(value), encoding="ascii")


def _result(candidate_id: str, manifest: dict[str, object]) -> dict[str, object]:
    candidate = frozen_candidates(ROOT)[candidate_id]
    artifacts = manifest["owner_artifacts"]
    assert isinstance(artifacts, dict)
    return {
        "schema_version": "myis.armindex-a2-external-candidate-result.v1",
        "attempt_id": ATTEMPT,
        "candidate_id": candidate_id,
        "arm_id": candidate["arm_id"],
        "program_sha256": candidate["program_sha256"],
        "executor_output_sha256": "1" * 64,
        "evaluator_input_sha256": "2" * 64,
        "evaluator_sha256": artifacts["evaluator"]["binding_sha256"],
        "code_sha256": manifest["engine"]["code_sha256"],
        "model_sha256": artifacts["model_lockset"]["binding_sha256"],
        "data_sha256": artifacts["data_handoff"]["binding_sha256"],
        "primary_metric": {"name": "recall_at_100/out", "value": "1"},
        "secondary_metrics": {"ndcg_at_100/out": "1", "ndcg_at_10/out": "1"},
        "latency": {"wall_seconds": "1", "search_p95_seconds": "1"},
        "cost": {"charged_usd": "0", "currency": "USD"},
        "coverage": {"expected_units": 1, "completed_units": 1},
        "resume_count": 0,
        "failure_count": 0,
        "reserve_activation_passed": False,
        "reserve_activation_evidence_sha256": None,
        "train_only": True,
        "rep_dev_measured": False,
        "protected_payload_included": False,
        "per_query_outcomes_included": False,
    }


def test_owner_local_input_rejects_fixture_path_and_hash_drift(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path, argv=["fixture-worker", "{program_path}"])
    _write_manifest(tmp_path, manifest)
    with pytest.raises(adapter.A2MeasuredAdapterError, match="fixture adapter"):
        adapter.validate_owner_local_input(ROOT, owner_root=tmp_path, manifest_relative_path="input.json")

    manifest = _manifest(tmp_path, argv=[sys.executable, "-m", "myis_research.armindex.a2_owner_local_engine", "{program_path}"])
    artifact = tmp_path / "runtime/lock.json"
    artifact.write_text("changed\n", encoding="ascii")
    _write_manifest(tmp_path, manifest)
    with pytest.raises(adapter.A2MeasuredAdapterError, match="runtime artifact hash drift"):
        adapter.validate_owner_local_input(ROOT, owner_root=tmp_path, manifest_relative_path="input.json")


def test_owner_local_input_rejects_symlink_and_a1_binding_drift(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path, argv=[sys.executable, "-m", "myis_research.armindex.a2_owner_local_engine", "{program_path}"])
    manifest["a1_v16_bindings"]["runtime_lock_sha256"] = "0" * 64
    body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    manifest["manifest_sha256"] = canonical_sha256(body)
    _write_manifest(tmp_path, manifest)
    with pytest.raises(adapter.A2MeasuredAdapterError, match="A1 v16 binding drift"):
        adapter.validate_owner_local_input(ROOT, owner_root=tmp_path, manifest_relative_path="input.json")

    manifest = _manifest(tmp_path, argv=[sys.executable, "-m", "myis_research.armindex.a2_owner_local_engine", "{program_path}"])
    linked = tmp_path / "runtime/lock.json"
    linked.unlink()
    linked.symlink_to(tmp_path / "models/lock.json")
    body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    manifest["manifest_sha256"] = canonical_sha256(body)
    _write_manifest(tmp_path, manifest)
    with pytest.raises(adapter.A2MeasuredAdapterError, match="runtime artifact path is unsafe"):
        adapter.validate_owner_local_input(ROOT, owner_root=tmp_path, manifest_relative_path="input.json")


def test_frozen_program_rejects_program_hash_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    candidate_id = next(iter(frozen_candidates(ROOT)))
    drifted = copy.deepcopy(frozen_candidates(ROOT))
    drifted[candidate_id]["program"]["program_sha256"] = "0" * 64
    monkeypatch.setattr(adapter, "frozen_candidates", lambda _root: drifted)
    with pytest.raises(adapter.A2MeasuredAdapterError, match="program hash drift"):
        adapter.frozen_program_for_candidate(ROOT, candidate_id)


def test_adapter_accepts_one_aggregate_result_and_rejects_protected_output(tmp_path: Path) -> None:
    candidate_id = next(iter(frozen_candidates(ROOT)))
    manifest = _manifest(tmp_path, argv=[sys.executable, "-m", "myis_research.armindex.a2_owner_local_engine", "{program_path}"])
    good = _result(candidate_id, manifest)
    _write_manifest(tmp_path, manifest)
    candidate = frozen_candidates(ROOT)[candidate_id]
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setenv("MYIS_A2_ARM_ID", candidate["arm_id"])
        monkeypatch.setenv("MYIS_A2_PROGRAM_SHA256", candidate["program_sha256"])
        monkeypatch.setattr(
            adapter.subprocess,
            "run",
            lambda *_args, **_kwargs: subprocess.CompletedProcess([], 0, json.dumps(good) + "\n", ""),
        )
        assert adapter.run_candidate_adapter(
            ROOT, owner_root=tmp_path, manifest_relative_path="input.json", candidate_id=candidate_id
        )["candidate_id"] == candidate_id

    protected = dict(good)
    protected["query_ids"] = ["protected"]
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setenv("MYIS_A2_ARM_ID", candidate["arm_id"])
        monkeypatch.setenv("MYIS_A2_PROGRAM_SHA256", candidate["program_sha256"])
        monkeypatch.setattr(
            adapter.subprocess,
            "run",
            lambda *_args, **_kwargs: subprocess.CompletedProcess([], 0, json.dumps(protected) + "\n", ""),
        )
        with pytest.raises(adapter.A2MeasuredAdapterError, match="not allowlisted"):
            adapter.run_candidate_adapter(
                ROOT, owner_root=tmp_path, manifest_relative_path="input.json", candidate_id=candidate_id
            )


def test_adapter_rejects_environment_identity_drift(tmp_path: Path) -> None:
    candidate_id = next(iter(frozen_candidates(ROOT)))
    manifest = _manifest(tmp_path, argv=[sys.executable, "-m", "myis_research.armindex.a2_owner_local_engine", "{program_path}"])
    _write_manifest(tmp_path, manifest)
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setenv("MYIS_A2_ARM_ID", "ARM-05")
        monkeypatch.setenv("MYIS_A2_PROGRAM_SHA256", "0" * 64)
        with pytest.raises(adapter.A2MeasuredAdapterError, match="environment identity drift"):
            adapter.run_candidate_adapter(
                ROOT, owner_root=tmp_path, manifest_relative_path="input.json", candidate_id=candidate_id
            )
