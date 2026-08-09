from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from myis_research.armindex import a1_2_owner_local_protected_compiler_v12 as compiler
from myis_research.armindex.a1_2_compiled_bindings_v12 import validate_binding_set
from myis_research.kernel.canonical import canonical_sha256, file_sha256

ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=True, sort_keys=True), encoding="utf-8")


def _artifact(root: Path, relative: str) -> dict[str, str]:
    return {"relative_path": relative, "sha256": file_sha256(root / relative)}


def _self_hash(value: dict[str, object], field: str) -> dict[str, object]:
    value[field] = canonical_sha256({key: item for key, item in value.items() if key != field})
    return value


def _make_store(tmp_path: Path) -> tuple[Path, Path, dict[str, object]]:
    store, model_root = tmp_path / "protected-store", tmp_path / "staged-models"
    store.mkdir()
    model_root.mkdir()
    for name in ("inputs", "indexes", "receipts"):
        (store / name).mkdir()
    corpus = {"family_token": "F-" + "a" * 32, "publication_token": "P-" + "a" * 31 + "1", "publication_ordinal": 1, "title_en": "Synthetic title", "abstract_en": "Synthetic abstract", "claims_text": "Synthetic independent claim", "claims": [{"claim_ordinal": 1, "is_independent": True, "text": "Synthetic claim"}]}
    (store / "inputs/corpus.jsonl").write_text(json.dumps(corpus) + "\n", encoding="utf-8")
    tokens = [f"Q-{index:032x}" for index in range(150)]
    (store / "inputs/queries.jsonl").write_text("".join(json.dumps({"work_token": token, "text": "synthetic query"}) + "\n" for token in tokens), encoding="utf-8")
    _write_json(store / "inputs/split.json", {"schema_version": "myis.armindex-a1.2-protected-split.v1", "rep_dev_work_tokens": tokens, "harness_dev_reserved_count": 100, "train_pool_count": 250})
    for name in ("evaluator.bin", "ephemeral-map.bin"):
        (store / f"inputs/{name}").write_bytes(b"synthetic-test-only")
    contract = json.loads((ROOT / "control/owner-local/a1.2-compiled-program-bindings-contract.v12.json").read_text())
    handoff_request = json.loads((ROOT / "control/owner-local/a1.2-evaluator-handoff-request.v11.json").read_text())
    handoff = _self_hash({"handoff_receipt_id": "synthetic-handoff-v12", "source_contract_sha256": handoff_request["source_contract"]["file_sha256"], "corpus_bundle_sha256": file_sha256(store / "inputs/corpus.jsonl"), "query_bundle_sha256": file_sha256(store / "inputs/queries.jsonl"), "split_commitment_sha256": file_sha256(store / "inputs/split.json"), "evaluator_sha256": file_sha256(store / "inputs/evaluator.bin"), "ephemeral_token_map_sha256": file_sha256(store / "inputs/ephemeral-map.bin"), "corpus_count": 1, "query_count": 150, "reserved_harness_dev_count": 100, "train_pool_count": 250, "return_root_free_bytes": 1_000_000, "receipt_sha256": ""}, "receipt_sha256")
    _write_json(store / "inputs/handoff.json", handoff)
    transfer_contract = json.loads((ROOT / "control/armindex/a1.2/scientific-transfer-contract.v11.json").read_text())
    workload_set = json.loads((ROOT / "control/armindex/a1.2/workload-manifest-set.scientific-request.v11.json").read_text())
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    v11_request = json.loads((ROOT / "control/armindex/a1.2/scientific-execution-adoption-request.v11.json").read_text())
    v11_receipt = json.loads((ROOT / "campaigns/armindex-multiretriever-v2/evidence/a1.2-scientific-execution-adoption-request.receipt.v11.json").read_text())
    v12_contract = json.loads((ROOT / "control/armindex/a1.2/scientific-execution-adoption-inputs.v12.json").read_text())
    publication_v13 = json.loads((ROOT / "control/armindex/a1.2/publication-impact-contract.v13.json").read_text())
    disposition = json.loads((ROOT / "control/armindex/a1.2/instance-disposition-policy.v13.json").read_text())
    anchor_body = {"schema_version": "myis.armindex-a1.2-scientific-execution-pre-adoption-anchor.v12-r3", "anchor_id": "a1.2-pre-adoption-anchor-synthetic-v12-r3", "revision_id": "a1.2-scientific-execution-adoption-inputs-v12-r3", "status": "PRE_ADOPTION_INPUT_ANCHOR", "claim_boundary": "Synthetic non-authorizing anchor for local compiler tests only; it binds immutable source and bundle identities but never authorizes provider contact, adoption, launch, retrieval, or scientific measurement.", "v11_request": {"uri": "control/armindex/a1.2/scientific-execution-adoption-request.v11.json", "file_sha256": file_sha256(ROOT / "control/armindex/a1.2/scientific-execution-adoption-request.v11.json"), "self_sha256": v11_request["request_sha256"]}, "v11_receipt": {"uri": "campaigns/armindex-multiretriever-v2/evidence/a1.2-scientific-execution-adoption-request.receipt.v11.json", "file_sha256": file_sha256(ROOT / "campaigns/armindex-multiretriever-v2/evidence/a1.2-scientific-execution-adoption-request.receipt.v11.json"), "self_sha256": v11_receipt["receipt_sha256"]}, "v12_contract": {"uri": "control/armindex/a1.2/scientific-execution-adoption-inputs.v12.json", "file_sha256": file_sha256(ROOT / "control/armindex/a1.2/scientific-execution-adoption-inputs.v12.json"), "self_sha256": v12_contract["contract_sha256"]}, "publication_v13": {"uri": "control/armindex/a1.2/publication-impact-contract.v13.json", "file_sha256": file_sha256(ROOT / "control/armindex/a1.2/publication-impact-contract.v13.json"), "self_sha256": publication_v13["contract_sha256"]}, "instance_disposition_v13": {"uri": "control/armindex/a1.2/instance-disposition-policy.v13.json", "file_sha256": file_sha256(ROOT / "control/armindex/a1.2/instance-disposition-policy.v13.json"), "policy_id": disposition["policy_id"]}, "execution_bundle": {"git_commit": commit, "git_tree": tree, "frozen_bundle_sha256": "a" * 64, "bundle_manifest_sha256": "b" * 64, "receipt_sha256": "c" * 64}, "authorization": {"provider_contact_allowed": False, "launch_allowed": False, "adopted_for_execution": False, "measured_retrieval_allowed": False}, "counters": {"measured_runs": 0, "selection_accesses": 0, "final_accesses": 0, "charged_usd": 0}}
    anchor = _self_hash(anchor_body, "anchor_sha256")
    _write_json(store / "inputs/anchor.json", anchor)
    transfer = _self_hash({"transfer_id": "synthetic-transfer-v12", "request_sha256": contract["v11_request"]["request_sha256"], "adoption_receipt_sha256": anchor["anchor_sha256"], "dataset_revision": handoff_request["source_contract"]["dataset_revision"], "split_commitment_sha256": file_sha256(store / "inputs/split.json"), "evaluator_sha256": file_sha256(store / "inputs/evaluator.bin"), "corpus_bundle_sha256": file_sha256(store / "inputs/corpus.jsonl"), "corpus_bundle_bytes": (store / "inputs/corpus.jsonl").stat().st_size, "corpus_family_count": 1, "query_bundle_sha256": file_sha256(store / "inputs/queries.jsonl"), "query_bundle_bytes": (store / "inputs/queries.jsonl").stat().st_size, "rep_dev_query_count": 150, "harness_dev_reserved_count": 100, "opaque_token_scheme_sha256": canonical_sha256(transfer_contract["opaque_token_contract"]), "ephemeral_token_map_sha256": file_sha256(store / "inputs/ephemeral-map.bin"), "workload_manifest_set_sha256": workload_set["manifest_set_sha256"], "expected_result_rows_per_program": 150, "manifest_sha256": ""}, "manifest_sha256")
    _write_json(store / "inputs/transfer.json", transfer)
    models = []
    for lock in contract["model_locks"]:
        arm = lock["arm_id"]
        if arm == "ARM-01":
            models.append({"arm_id": arm, "model_relative_path": None, "tokenizer_json_relative_path": None, "runtime_manifest_relative_path": None})
            continue
        directory = model_root / arm
        directory.mkdir()
        (directory / "tokenizer.json").write_text("synthetic tokenizer", encoding="utf-8")
        _write_json(directory / "runtime-file-manifest.v4.json", {"arm_id": arm, "source_lock_file_sha256": lock["file_sha256"], "files": [{"sha256": lock["tokenizer_sha256"]}]})
        models.append({"arm_id": arm, "model_relative_path": arm, "tokenizer_json_relative_path": "tokenizer.json", "runtime_manifest_relative_path": "runtime-file-manifest.v4.json"})
    value: dict[str, object] = {"schema_version": "myis.armindex-a1.2-owner-local-protected-compilation-input.v12", "input_id": "a1.2-v12-synthetic-test", "claim_boundary": "Synthetic test-only protected-store fixture. It exercises a local compiler interface and is not measured evidence, a provider request, or a scientific result.", "corpus": _artifact(store, "inputs/corpus.jsonl"), "queries": _artifact(store, "inputs/queries.jsonl"), "split": _artifact(store, "inputs/split.json"), "evaluator": _artifact(store, "inputs/evaluator.bin"), "ephemeral_token_map": _artifact(store, "inputs/ephemeral-map.bin"), "handoff_receipt": _artifact(store, "inputs/handoff.json"), "protected_transfer_manifest": _artifact(store, "inputs/transfer.json"), "pre_adoption_anchor": _artifact(store, "inputs/anchor.json"), "models": models, "protected_index_manifest_directory": "indexes"}
    _write_json(store / "inputs/contract.json", value)
    return store, model_root, value


def _fake_tokenizer_setup(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    original_hash = compiler.file_sha256
    locks = json.loads((ROOT / "control/owner-local/a1.2-compiled-program-bindings-contract.v12.json").read_text())["model_locks"]
    expected = {item["arm_id"]: item["tokenizer_sha256"] for item in locks}
    monkeypatch.setattr(compiler, "file_sha256", lambda path: expected[Path(path).parent.name] if Path(path).name == "tokenizer.json" else original_hash(Path(path)))
    calls: list[str] = []

    class Tokenizer:
        def __call__(self, text: str, **_kwargs: object) -> dict[str, list[int]]:
            return {"input_ids": list(range(max(1, len(text.split()))))}

    def load(_directory: Path, *, arm_id: str) -> Tokenizer:
        calls.append(arm_id)
        return Tokenizer()

    monkeypatch.setattr(compiler, "_load_dense_tokenizer", load)
    return calls


def test_produce_streams_spools_and_caches_one_tokenizer_per_dense_arm(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store, model_root, _value = _make_store(tmp_path)
    calls = _fake_tokenizer_setup(monkeypatch)
    monkeypatch.setenv("MYIS_STORE", str(store))
    result = compiler.produce(ROOT, input_relative_path="inputs/contract.json", binding_output_relative_path="receipts/bindings.json", receipt_output_relative_path="receipts/compiler.json", model_root=model_root)
    bindings = json.loads((store / "receipts/bindings.json").read_text())
    assert result["binding_count"] == 25
    assert calls == ["ARM-02", "ARM-03", "ARM-04", "ARM-05"]
    assert validate_binding_set(ROOT, bindings)["actual_bindings"] == 25
    assert len(list((store / "indexes").glob("ARM-*.json"))) == 25
    by_id = {item["binding_id"]: item for item in bindings["bindings"]}
    assert by_id["ARM-02--P00-TAC-DOC"]["compiled_representation_sha256"] != by_id["ARM-03--P00-TAC-DOC"]["compiled_representation_sha256"]


def test_jsonl_iterator_does_not_use_read_text(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "rows.jsonl"
    path.write_text('{"one":1}\n{"two":2}\n', encoding="utf-8")
    monkeypatch.setattr(Path, "read_text", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("read_text")))
    iterator = compiler._iter_jsonl(path, role="test rows")
    assert next(iterator) == {"one": 1}
    assert next(iterator) == {"two": 2}


def test_receipt_tamper_is_rejected_after_artifact_hash_is_updated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store, model_root, value = _make_store(tmp_path)
    _fake_tokenizer_setup(monkeypatch)
    monkeypatch.setenv("MYIS_STORE", str(store))
    receipt = json.loads((store / "inputs/handoff.json").read_text())
    receipt["query_count"] = 149
    _write_json(store / "inputs/handoff.json", receipt)
    value["handoff_receipt"] = _artifact(store, "inputs/handoff.json")
    _write_json(store / "inputs/contract.json", value)
    with pytest.raises(compiler.ProtectedCompilationV12Error, match="source binding or self-hash mismatch"):
        compiler.preflight(ROOT, input_relative_path="inputs/contract.json", model_root=model_root)


def test_model_root_must_be_external_to_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store, _model_root, _value = _make_store(tmp_path)
    _fake_tokenizer_setup(monkeypatch)
    monkeypatch.setenv("MYIS_STORE", str(store))
    with pytest.raises(compiler.ProtectedCompilationV12Error, match="model root must be a non-symlink directory outside"):
        compiler.preflight(ROOT, input_relative_path="inputs/contract.json", model_root=ROOT)


def test_resume_after_render_interruption_reuses_complete_logical_spools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store, model_root, _value = _make_store(tmp_path)
    _fake_tokenizer_setup(monkeypatch)
    monkeypatch.setenv("MYIS_STORE", str(store))
    original_compile = compiler.compile_common_program
    compile_calls = 0

    def counted(*args: object, **kwargs: object) -> object:
        nonlocal compile_calls
        compile_calls += 1
        return original_compile(*args, **kwargs)

    monkeypatch.setattr(compiler, "compile_common_program", counted)
    original_render = compiler._representation_hash
    failed = False

    def fail_once(**kwargs: object) -> tuple[str, int, int]:
        nonlocal failed
        if not failed:
            failed = True
            raise RuntimeError("synthetic interruption")
        return original_render(**kwargs)

    monkeypatch.setattr(compiler, "_representation_hash", fail_once)
    with pytest.raises(RuntimeError, match="synthetic interruption"):
        compiler.produce(ROOT, input_relative_path="inputs/contract.json", binding_output_relative_path="receipts/bindings.json", receipt_output_relative_path="receipts/compiler.json", model_root=model_root)
    assert compile_calls == 5
    monkeypatch.setattr(compiler, "_representation_hash", original_render)
    compiler.produce(ROOT, input_relative_path="inputs/contract.json", binding_output_relative_path="receipts/bindings.json", receipt_output_relative_path="receipts/compiler.json", model_root=model_root)
    assert compile_calls == 5


def test_resume_after_spool_interruption_restarts_the_whole_logical_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store, model_root, _value = _make_store(tmp_path)
    _fake_tokenizer_setup(monkeypatch)
    monkeypatch.setenv("MYIS_STORE", str(store))
    original_compile = compiler.compile_common_program
    calls = 0

    def fail_during_first_pass(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise RuntimeError("synthetic spool interruption")
        return original_compile(*args, **kwargs)

    monkeypatch.setattr(compiler, "compile_common_program", fail_during_first_pass)
    with pytest.raises(RuntimeError, match="synthetic spool interruption"):
        compiler.produce(ROOT, input_relative_path="inputs/contract.json", binding_output_relative_path="receipts/bindings.json", receipt_output_relative_path="receipts/compiler.json", model_root=model_root)
    compiler.produce(ROOT, input_relative_path="inputs/contract.json", binding_output_relative_path="receipts/bindings.json", receipt_output_relative_path="receipts/compiler.json", model_root=model_root)
    assert calls == 8


def test_completed_spool_tamper_fails_closed_on_resume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store, model_root, _value = _make_store(tmp_path)
    _fake_tokenizer_setup(monkeypatch)
    monkeypatch.setenv("MYIS_STORE", str(store))
    original_render = compiler._representation_hash
    monkeypatch.setattr(
        compiler,
        "_representation_hash",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("stop after spooling")),
    )
    with pytest.raises(RuntimeError, match="stop after spooling"):
        compiler.produce(ROOT, input_relative_path="inputs/contract.json", binding_output_relative_path="receipts/bindings.json", receipt_output_relative_path="receipts/compiler.json", model_root=model_root)
    transaction = next((store / "indexes").glob(".a1_2_v12_transaction_*"))
    with (transaction / "P00-TAC-DOC.units.jsonl").open("a", encoding="utf-8") as handle:
        handle.write("{}\n")
    monkeypatch.setattr(compiler, "_representation_hash", original_render)
    with pytest.raises(compiler.ProtectedCompilationV12Error, match="spool integrity mismatch"):
        compiler.produce(ROOT, input_relative_path="inputs/contract.json", binding_output_relative_path="receipts/bindings.json", receipt_output_relative_path="receipts/compiler.json", model_root=model_root)


def test_existing_receipts_restore_a_missing_index_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store, model_root, _value = _make_store(tmp_path)
    calls = _fake_tokenizer_setup(monkeypatch)
    monkeypatch.setenv("MYIS_STORE", str(store))
    compiler.produce(ROOT, input_relative_path="inputs/contract.json", binding_output_relative_path="receipts/bindings.json", receipt_output_relative_path="receipts/compiler.json", model_root=model_root)
    missing = store / "indexes/ARM-04--P03-PASSAGE.json"
    missing.unlink()
    compiler.produce(ROOT, input_relative_path="inputs/contract.json", binding_output_relative_path="receipts/bindings.json", receipt_output_relative_path="receipts/compiler.json", model_root=model_root)
    assert missing.is_file()
    assert calls == ["ARM-02", "ARM-03", "ARM-04", "ARM-05"]


def test_handoff_must_bind_dapfam_source_contract_not_handoff_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store, model_root, value = _make_store(tmp_path)
    _fake_tokenizer_setup(monkeypatch)
    monkeypatch.setenv("MYIS_STORE", str(store))
    handoff = json.loads((store / "inputs/handoff.json").read_text())
    request = json.loads((ROOT / "control/owner-local/a1.2-evaluator-handoff-request.v11.json").read_text())
    handoff["source_contract_sha256"] = request["handoff_contract_sha256"]
    _self_hash(handoff, "receipt_sha256")
    _write_json(store / "inputs/handoff.json", handoff)
    value["handoff_receipt"] = _artifact(store, "inputs/handoff.json")
    _write_json(store / "inputs/contract.json", value)
    with pytest.raises(compiler.ProtectedCompilationV12Error, match="source binding"):
        compiler.preflight(ROOT, input_relative_path="inputs/contract.json", model_root=model_root)


def test_transfer_manifest_must_bind_exact_dataset_revision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store, model_root, value = _make_store(tmp_path)
    _fake_tokenizer_setup(monkeypatch)
    monkeypatch.setenv("MYIS_STORE", str(store))
    transfer = json.loads((store / "inputs/transfer.json").read_text())
    transfer["dataset_revision"] = "f" * 40
    _self_hash(transfer, "manifest_sha256")
    _write_json(store / "inputs/transfer.json", transfer)
    value["protected_transfer_manifest"] = _artifact(store, "inputs/transfer.json")
    _write_json(store / "inputs/contract.json", value)
    with pytest.raises(compiler.ProtectedCompilationV12Error, match="protected transfer manifest counts"):
        compiler.preflight(ROOT, input_relative_path="inputs/contract.json", model_root=model_root)


def test_p02_missing_independent_claim_is_eligible_not_coverage_gap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store, model_root, value = _make_store(tmp_path)
    _fake_tokenizer_setup(monkeypatch)
    monkeypatch.setenv("MYIS_STORE", str(store))
    corpus = json.loads((store / "inputs/corpus.jsonl").read_text())
    corpus["claims"] = []
    second = {"family_token": "F-" + "b" * 32, "publication_token": "P-" + "b" * 32, "publication_ordinal": 1, "title_en": "Synthetic title two", "abstract_en": "Synthetic abstract two", "claims_text": "Synthetic independent claim two", "claims": [{"claim_ordinal": 1, "is_independent": True, "text": "Synthetic claim two"}]}
    (store / "inputs/corpus.jsonl").write_text(json.dumps(corpus) + "\n" + json.dumps(second) + "\n", encoding="utf-8")
    value["corpus"] = _artifact(store, "inputs/corpus.jsonl")
    # Rebuild strict source receipts against the revised protected corpus.
    for name, field in (("handoff.json", "receipt_sha256"), ("transfer.json", "manifest_sha256")):
        receipt = json.loads((store / "inputs" / name).read_text())
        receipt["corpus_bundle_sha256"] = value["corpus"]["sha256"]
        if name == "handoff.json":
            receipt["corpus_count"] = 2
        else:
            receipt["corpus_family_count"] = 2
            receipt["corpus_bundle_bytes"] = (store / "inputs/corpus.jsonl").stat().st_size
        _self_hash(receipt, field)
        _write_json(store / "inputs" / name, receipt)
    value["handoff_receipt"] = _artifact(store, "inputs/handoff.json")
    value["protected_transfer_manifest"] = _artifact(store, "inputs/transfer.json")
    _write_json(store / "inputs/contract.json", value)
    compiler.produce(ROOT, input_relative_path="inputs/contract.json", binding_output_relative_path="receipts/bindings.json", receipt_output_relative_path="receipts/compiler.json", model_root=model_root)
    bindings = json.loads((store / "receipts/bindings.json").read_text())
    assert all(item["coverage_gap_count"] == 0 for item in bindings["bindings"] if item["program_id"] == "P02-CLAIM1")
