from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex import a2_owner_local_engine as engine
from myis_research.armindex.a1_2_measured_executor_v16 import FamilyRank
from myis_research.armindex.a2_execution_readiness import frozen_candidates
from myis_research.kernel.canonical import canonical_sha256, file_sha256

ROOT = Path(__file__).resolve().parents[1]
ATTEMPT = "a2-engine-test01"


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _artifact(owner: Path, relative: str, value: str, binding: str) -> dict[str, str]:
    path = owner / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
    return {"path": relative, "sha256": file_sha256(path), "binding_sha256": binding}


def _manifest(owner: Path) -> dict[str, object]:
    bindings = {
        "runtime_lock_sha256": "1" * 64,
        "model_lockset_sha256": "2" * 64,
        "data_handoff_sha256": "3" * 64,
        "evaluator_receipt_sha256": "4" * 64,
    }
    program = next(value["program"] for value in frozen_candidates(ROOT).values() if value["arm_id"] == "ARM-01")
    _write_jsonl(owner / "protected/corpus.jsonl", [{"family_token": "F-" + "a" * 32, "publication_token": "P-1", "title": "TITLE", "abstract": "ABSTRACT", "claims_text": "CLAIMS"}])
    _write_jsonl(owner / "protected/queries.jsonl", [{"work_token": "Q-" + "b" * 32, "text": "query"}])
    family_tokens = [f"F-{index:032x}" for index in range(100)]
    _write_jsonl(owner / "protected/qrels.json", [{"work_token": "Q-" + "b" * 32, "relevance": {family_tokens[0]: 1}}])
    _write_jsonl(owner / "protected/membership.json", [{"work_token": "Q-" + "b" * 32, "eligible_out": True}])
    artifacts = {
        "runtime": _artifact(owner, "runtime/lock.json", "runtime", bindings["runtime_lock_sha256"]),
        "model_lockset": _artifact(owner, "models/lock.json", "models", bindings["model_lockset_sha256"]),
        "data_handoff": _artifact(owner, "handoff/aggregate.json", "handoff", bindings["data_handoff_sha256"]),
        "evaluator": _artifact(owner, "aggregate/evaluator.json", "evaluator", bindings["evaluator_receipt_sha256"]),
        "corpus": {"path": "protected/corpus.jsonl", "sha256": file_sha256(owner / "protected/corpus.jsonl"), "binding_sha256": "5" * 64},
        "queries": {"path": "protected/queries.jsonl", "sha256": file_sha256(owner / "protected/queries.jsonl"), "binding_sha256": "6" * 64},
        "qrels": {"path": "protected/qrels.json", "sha256": file_sha256(owner / "protected/qrels.json"), "binding_sha256": "7" * 64},
        "membership": {"path": "protected/membership.json", "sha256": file_sha256(owner / "protected/membership.json"), "binding_sha256": "8" * 64},
    }
    body: dict[str, object] = {
        "schema_version": "myis.armindex-a2-owner-local-measured-input.v1",
        "status": "READY",
        "attempt_id": ATTEMPT,
        "a1_v16_bindings": bindings,
        "arm_incumbents": {arm: {"candidate_id": f"a1-{arm}", "program_sha256": value * 64, "primary_metric": "0.1"} for arm, value in (("ARM-03", "3"), ("ARM-05", "5"), ("ARM-04", "4"))},
        "owner_artifacts": artifacts,
        "engine": {
            "engine_id": "myis.armindex-a2-owner-local-retriever-evaluator.v1",
            "argv": ["python", "-m", "myis_research.armindex.a2_owner_local_engine", "{program_path}"],
            "code_sha256": file_sha256(Path(engine.__file__)),
            "all_fee_usd_per_hour": "0.6",
            "model_directories": {arm: f"models/{arm}" for arm in ("ARM-02", "ARM-03", "ARM-04", "ARM-05")},
            "device_by_arm": {"ARM-02": "cuda:0", "ARM-03": "cuda:1", "ARM-04": "cuda:2", "ARM-05": "cuda:3"},
            "output_root": "output",
        },
    }
    return {**body, "manifest_sha256": canonical_sha256(body)}, program


def test_engine_compiles_frozen_program_and_exports_only_aggregate_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest, program = _manifest(tmp_path)
    program_path = tmp_path / "frozen-program.json"
    program_path.write_text(json.dumps(program), encoding="ascii")
    observed: dict[str, object] = {}

    def fake_validate(*_args: object, **_kwargs: object) -> dict[str, object]:
        return manifest

    def fake_rank(units: object, queries: object, method: str) -> tuple[dict[str, tuple[FamilyRank, ...]], tuple[float, ...]]:
        observed["texts"] = [unit.physical_inputs[0].text for unit in units]
        observed["method"] = method
        return ({"Q-" + "b" * 32: tuple(FamilyRank(f"F-{index:032x}", index + 1, float(100 - index)) for index in range(100))}, (0.25,))

    monkeypatch.setattr(engine, "validate_owner_local_input", fake_validate)
    monkeypatch.setattr(engine, "_rank_arm01", fake_rank)
    result = engine.run_owner_local_engine(ROOT, owner_root=tmp_path, manifest_relative_path="input.json", program_path=program_path, candidate_id=program["program_id"], arm_id="ARM-01", program_sha256=program["program_sha256"])

    assert observed["method"] == program["family_aggregation"]
    assert observed["texts"]
    assert result["primary_metric"]["name"] == "recall_at_100/out"
    assert result["coverage"] == {"expected_units": 1, "completed_units": 1}
    assert result["latency"]["search_p95_seconds"] == "0.25"
    assert result["train_only"] is False
    assert result["rep_dev_measured"] is True
    assert not ({"query_ids", "qrels", "membership", "per_query_outcomes"} & set(result))


def test_corpus_rows_maps_frozen_compact_fields_to_canonical_materialized_fields(tmp_path: Path) -> None:
    _input_manifest, program = _manifest(tmp_path)
    corpus = tmp_path / "canonical-corpus.jsonl"
    _write_jsonl(
        corpus,
        [
            {
                "family_token": "F-" + "a" * 32,
                "publication_token": "P-1",
                "title_en": "TITLE",
                "abstract_en": "ABSTRACT",
                "claims_text": "CLAIMS",
            }
        ],
    )

    rows = engine._corpus_rows(corpus, program)

    assert rows == [
        {
            "family_token": "F-" + "a" * 32,
            "publication_token": "P-1",
            "title": "TITLE",
            "abstract": "ABSTRACT",
            "claims_text": "CLAIMS",
        }
    ]


def test_engine_rejects_program_hash_drift_before_opening_owner_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest, program = _manifest(tmp_path)
    program["program_sha256"] = "0" * 64
    program_path = tmp_path / "frozen-program.json"
    program_path.write_text(json.dumps(program), encoding="ascii")
    monkeypatch.setattr(engine, "validate_owner_local_input", lambda *_args, **_kwargs: manifest)

    with pytest.raises(engine.A2OwnerLocalEngineError, match="program identity drift"):
        engine.run_owner_local_engine(ROOT, owner_root=tmp_path, manifest_relative_path="input.json", program_path=program_path, candidate_id=program["program_id"], arm_id="ARM-01", program_sha256="0" * 64)


def test_engine_rejects_nonfrozen_program_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest, program = _manifest(tmp_path)
    altered = dict(program)
    altered["field_labels"] = {**program["field_labels"], "title": "drift: "}
    body = {key: value for key, value in altered.items() if key != "program_sha256"}
    altered["program_sha256"] = canonical_sha256(body)
    program_path = tmp_path / "frozen-program.json"
    program_path.write_text(json.dumps(altered), encoding="ascii")
    monkeypatch.setattr(engine, "validate_owner_local_input", lambda *_args, **_kwargs: manifest)

    with pytest.raises(engine.A2OwnerLocalEngineError, match="program bytes drift"):
        engine.run_owner_local_engine(ROOT, owner_root=tmp_path, manifest_relative_path="input.json", program_path=program_path, candidate_id=program["program_id"], arm_id="ARM-01", program_sha256=altered["program_sha256"])


def test_remote_result_rejects_v2_before_opening_owner_local_evaluator(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    manifest = tmp_path / "input.json"
    manifest.write_text("{}", encoding="ascii")
    monkeypatch.setattr(
        engine,
        "validate_owner_local_input",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not open")),
    )
    with pytest.raises(RuntimeError, match="requires successor authority v3"):
        engine.evaluate_remote_retrieval_result(
            ROOT,
            owner_root=tmp_path,
            manifest_relative_path="input.json",
            retrieval_result={},
            candidate_id="a2-arm-03-matched-b1-exploit",
            measurement_authority={
                "schema_version": "myis.armindex-a2-measured-execution-authority.v2"
            },
        )
