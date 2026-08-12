from __future__ import annotations

import copy
import json
import subprocess
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
    handoff = {
        "status": "PASS",
        "source_contract_sha256": json.loads((ROOT / "control/owner-local/a1.2-evaluator-handoff-request.v11.json").read_text(encoding="utf-8"))["handoff_contract_sha256"],
        "split_role": "REP-DEV",
        "query_count": 150,
        "reserved_harness_dev_count": 100,
        "corpus_bundle_sha256": artifacts["corpus"]["binding_sha256"],
        "query_bundle_sha256": artifacts["queries"]["binding_sha256"],
        "qrels_commitment_sha256": artifacts["qrels"]["binding_sha256"],
        "split_commitment_sha256": artifacts["membership"]["binding_sha256"],
        "evaluator_sha256": artifacts["evaluator"]["binding_sha256"],
    }
    handoff_path = owner / locations["data_handoff"]
    handoff_path.write_text(json.dumps(handoff), encoding="ascii")
    artifacts["data_handoff"]["sha256"] = file_sha256(handoff_path)
    model_manifests: dict[str, str] = {}
    for arm_id in ("ARM-02", "ARM-03", "ARM-04", "ARM-05"):
        model_root = owner / "models" / arm_id
        model_root.mkdir(parents=True, exist_ok=True)
        model_file = model_root / "config.json"
        model_file.write_text(f"{arm_id}\n", encoding="ascii")
        model_manifest = owner / "models" / f"{arm_id}.manifest.json"
        model_manifest.write_text(json.dumps({"files": [{"path": "config.json", "sha256": file_sha256(model_file)}]}), encoding="ascii")
        model_manifests[arm_id] = model_manifest.relative_to(owner).as_posix()
    body: dict[str, object] = {
        "schema_version": "myis.armindex-a2-owner-local-measured-input.v1",
        "status": "READY",
        "attempt_id": ATTEMPT,
        "a1_v16_bindings": bindings,
        "arm_incumbents": adapter.canonical_a1_incumbents(ROOT),
        "owner_artifacts": artifacts,
        "engine": {
            "engine_id": "myis.armindex-a2-owner-local-retriever-evaluator.v1",
            "argv": argv,
            "code_sha256": code_sha256,
            "python_executable": "python",
            "model_directories": {arm_id: f"models/{arm_id}" for arm_id in ("ARM-02", "ARM-03", "ARM-04", "ARM-05")},
            "model_manifests": model_manifests,
            "device_by_arm": {"ARM-02": "cuda:0", "ARM-03": "cuda:1", "ARM-04": "cuda:2", "ARM-05": "cuda:3"},
            "all_fee_usd_per_hour": "0.6",
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
        "train_only": False,
        "rep_dev_measured": True,
        "protected_payload_included": False,
        "per_query_outcomes_included": False,
    }


def test_owner_local_input_rejects_fixture_path_and_hash_drift(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path, argv=["fixture-worker", "{program_path}"])
    _write_manifest(tmp_path, manifest)
    with pytest.raises(adapter.A2MeasuredAdapterError, match="fixture adapter"):
        adapter.validate_owner_local_input(ROOT, owner_root=tmp_path, manifest_relative_path="input.json")

    manifest = _manifest(tmp_path, argv=["python", "-m", "myis_research.armindex.a2_owner_local_engine", "{program_path}"])
    artifact = tmp_path / "runtime/lock.json"
    artifact.write_text("changed\n", encoding="ascii")
    _write_manifest(tmp_path, manifest)
    with pytest.raises(adapter.A2MeasuredAdapterError, match="runtime artifact hash drift"):
        adapter.validate_owner_local_input(ROOT, owner_root=tmp_path, manifest_relative_path="input.json")


def test_owner_local_input_rejects_symlink_and_a1_binding_drift(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path, argv=["python", "-m", "myis_research.armindex.a2_owner_local_engine", "{program_path}"])
    manifest["a1_v16_bindings"]["runtime_lock_sha256"] = "0" * 64
    body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    manifest["manifest_sha256"] = canonical_sha256(body)
    _write_manifest(tmp_path, manifest)
    with pytest.raises(adapter.A2MeasuredAdapterError, match="A1 v16 binding drift"):
        adapter.validate_owner_local_input(ROOT, owner_root=tmp_path, manifest_relative_path="input.json")

    manifest = _manifest(tmp_path, argv=["python", "-m", "myis_research.armindex.a2_owner_local_engine", "{program_path}"])
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


def test_owner_local_input_rejects_incumbent_and_rep_dev_handoff_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(adapter, "_runtime_python_identity", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(adapter, "_verify_model_manifest", lambda *_args, **_kwargs: None)
    argv = ["python", "-m", "myis_research.armindex.a2_owner_local_engine", "{program_path}"]
    manifest = _manifest(tmp_path, argv=argv)
    manifest["arm_incumbents"]["ARM-03"]["primary_metric"] = "0"
    body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    manifest["manifest_sha256"] = canonical_sha256(body)
    _write_manifest(tmp_path, manifest)
    with pytest.raises(adapter.A2MeasuredAdapterError, match="incumbent binding drift"):
        adapter.validate_owner_local_input(
            ROOT, owner_root=tmp_path, manifest_relative_path="input.json"
        )

    manifest = _manifest(tmp_path, argv=argv)
    handoff_path = tmp_path / manifest["owner_artifacts"]["data_handoff"]["path"]
    handoff = json.loads(handoff_path.read_text(encoding="ascii"))
    handoff["split_role"] = "TRAIN"
    handoff_path.write_text(json.dumps(handoff), encoding="ascii")
    manifest["owner_artifacts"]["data_handoff"]["sha256"] = file_sha256(handoff_path)
    body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    manifest["manifest_sha256"] = canonical_sha256(body)
    _write_manifest(tmp_path, manifest)
    with pytest.raises(adapter.A2MeasuredAdapterError, match="REP-DEV data handoff drift"):
        adapter.validate_owner_local_input(
            ROOT, owner_root=tmp_path, manifest_relative_path="input.json"
        )


def test_runtime_and_model_manifest_identity_drift_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        adapter.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [], 0, json.dumps({"python": "3.11.9", "pytorch": "drift", "cuda": "drift"}), ""
        ),
    )
    with pytest.raises(adapter.A2MeasuredAdapterError, match="interpreter identity drift"):
        adapter._runtime_python_identity(ROOT, Path("python"))

    model_root = tmp_path / "model"
    model_root.mkdir()
    (model_root / "config.json").write_text("safe\n", encoding="ascii")
    manifest_path = tmp_path / "model-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "arm_id": "ARM-03",
                "model_id": "drift",
                "resolved_revision": "drift",
                "model_lock_sha256": "0" * 64,
                "files": [{"path": "config.json", "sha256": file_sha256(model_root / "config.json")}],
            }
        ),
        encoding="ascii",
    )
    with pytest.raises(adapter.A2MeasuredAdapterError, match="model manifest binding drift"):
        adapter._verify_model_manifest(
            ROOT, arm_id="ARM-02", model_root=model_root, manifest_path=manifest_path
        )


def test_adapter_accepts_one_aggregate_result_and_rejects_protected_output(tmp_path: Path) -> None:
    candidate_id = next(iter(frozen_candidates(ROOT)))
    manifest = _manifest(tmp_path, argv=["python", "-m", "myis_research.armindex.a2_owner_local_engine", "{program_path}"])
    good = _result(candidate_id, manifest)
    _write_manifest(tmp_path, manifest)
    candidate = frozen_candidates(ROOT)[candidate_id]
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(adapter, "_runtime_python_identity", lambda *_args, **_kwargs: None)
        monkeypatch.setattr(adapter, "_verify_model_manifest", lambda *_args, **_kwargs: None)
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
        monkeypatch.setattr(adapter, "_runtime_python_identity", lambda *_args, **_kwargs: None)
        monkeypatch.setattr(adapter, "_verify_model_manifest", lambda *_args, **_kwargs: None)
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
    manifest = _manifest(tmp_path, argv=["python", "-m", "myis_research.armindex.a2_owner_local_engine", "{program_path}"])
    _write_manifest(tmp_path, manifest)
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(adapter, "_runtime_python_identity", lambda *_args, **_kwargs: None)
        monkeypatch.setattr(adapter, "_verify_model_manifest", lambda *_args, **_kwargs: None)
        monkeypatch.setenv("MYIS_A2_ARM_ID", "ARM-05")
        monkeypatch.setenv("MYIS_A2_PROGRAM_SHA256", "0" * 64)
        with pytest.raises(adapter.A2MeasuredAdapterError, match="environment identity drift"):
            adapter.run_candidate_adapter(
                ROOT, owner_root=tmp_path, manifest_relative_path="input.json", candidate_id=candidate_id
            )
