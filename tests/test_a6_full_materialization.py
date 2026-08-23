from __future__ import annotations

import json
import importlib.util
import os
from pathlib import Path
from queue import Queue

import pytest

import myis_research.armindex.a6_full_materialization as a6
from myis_research.armindex.a6_full_materialization import (
    A6ExecutionError,
    ExecutionConfig,
    build_canary_receipt,
    build_failure_receipt,
    build_owner_store_index_manifest,
    enforce_offline_environment,
    merge_latency_histograms,
    model_tree_sha256,
    build_safe_return_manifest,
    passage_texts,
    prepare_fresh_attempt,
    prepare_full_attempt_after_canary,
    shard_for_family,
    truncate_checkpoint_tails,
    validate_fresh_attempt_root,
    validate_full_attempt_resume,
    validate_source_and_shard,
)


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("run_a6_full_dapfam", ROOT / "scripts" / "run_a6_full_dapfam.py")
assert SPEC and SPEC.loader
LAUNCHER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LAUNCHER)


def _record(*, publication: str = "P-1", family: str = "F-1", claims: str = "claim " * 500) -> dict[str, object]:
    return {
        "family_token": family,
        "publication_token": publication,
        "title_en": " A  title ",
        "abstract_en": "abstract",
        "claims_text": claims,
        "claims": [claims],
        "publication_ordinal": 0,
    }


def _config(tmp_path: Path, source: Path, count: int, *, families: int = 1) -> ExecutionConfig:
    model = tmp_path / "model"
    model.mkdir(exist_ok=True)
    return ExecutionConfig(
        "a6-goal001-20260822T010203Z-x", source, "a" * 64, count, families, "c" * 64,
        model, "d" * 64, "e" * 64,
        {"numpy": "test", "torch": "test", "sentence-transformers": "test", "transformers": "test"},
        tmp_path / "program.json", "h" * 64, (0, 1), 1, 1, 0.342, "f" * 64,
        {"representation_program_sha256": "g" * 64}, "b" * 64,
    )


def test_frozen_schema_representation_is_passage_normalized_and_deterministic() -> None:
    passages = passage_texts(_record())
    assert passages[0].startswith("encode document for different retrieval: A title abstract claim")
    assert len(passages) == 2
    assert shard_for_family("F-1") == shard_for_family("F-1")


@pytest.mark.parametrize(
    "record",
    [
        {"family_id": "F", "title": "x", "claims_text": "x"},
        {**_record(), "qrels": "forbidden"},
        {**_record(), "title_en": 3},
    ],
)
def test_representation_rejects_noncanonical_or_evaluation_schema(record: dict[str, object]) -> None:
    with pytest.raises(A6ExecutionError, match="schema|non-text"):
        passage_texts(record)


def test_source_sharding_rejects_wrong_full_coverage_but_supports_two_gpu_canary(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    first = _record(publication="P-1", family="F-1")
    second = _record(publication="P-2", family="F-2")
    while shard_for_family(str(first["family_token"])) == shard_for_family(str(second["family_token"])):
        second["family_token"] = f"{second['family_token']}-x"
    source.write_text("\n".join((json.dumps(first), json.dumps(second))) + "\n", encoding="utf-8")
    config = _config(tmp_path, source, 45_336)
    with pytest.raises(A6ExecutionError, match="coverage"):
        validate_source_and_shard(config)
    shards = validate_source_and_shard(config, canary_documents=1)
    assert {key: len(value) for key, value in shards.items()} == {0: 1, 1: 1}


def test_source_requires_unique_opaque_publication_tokens(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    source.write_text("\n".join((json.dumps(_record()), json.dumps(_record()))) + "\n", encoding="utf-8")
    config = _config(tmp_path, source, 45_336)
    with pytest.raises(A6ExecutionError, match="identities"):
        validate_source_and_shard(config, canary_documents=2)


def _write_owner_source_lineage(owner: Path, source: Path, *, rows: int = 1) -> dict[str, object]:
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"{\"row\":1}\n")
    manifest = {
        "schema_version": "myis.armindex-owner-data-source-manifest.v1",
        "source_contract_sha256": "c" * 64,
        "full_corpus_row_count": rows,
        "protected_payload_included": False,
        "parent_split_sha256": "p" * 64,
        "partition_counts": {"final": 872},
        "artifacts": [{
            "artifact_role": "a6_full_corpus_owner_pointer",
            "owner_relative_pointer": source.relative_to(owner).as_posix(),
            "bytes": source.stat().st_size,
            "sha256": a6.file_sha256(source),
        }],
    }
    manifest_hash = a6.canonical_sha256(manifest)
    manifest_path = owner / "data-bundle" / "canonical-a2-a6-20260820" / "source-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    opaque = {
        "schema_version": "myis.armindex-a5-final-872-opaque-input-receipt.v1",
        "status": "SEALED_PRE_D2_OPAQUE_POINTER_READY",
        "source_manifest_sha256": manifest_hash,
        "final_split_commitment_sha256": "p" * 64,
        "expected_final_query_count": 872,
        "payload_materialized": False,
        "protected_payload_included": False,
    }
    opaque_path = owner / "armindex" / "a5" / "final-872-input" / "receipt.json"
    opaque_path.parent.mkdir(parents=True, exist_ok=True)
    opaque_path.write_text(json.dumps(opaque), encoding="utf-8")
    a5_manifest_body = {
        "schema_version": "myis.armindex-a5-final-opaque-materialization.v1",
        "status": "PASS_A5_OPAQUE_INPUTS_MATERIALIZED", "scope": "Final-872",
        "corpus_count": rows, "hashes": {"corpus": a6.file_sha256(source)},
        "protected_payload_included": False,
    }
    a5_manifest_hash = a6.canonical_sha256(a5_manifest_body)
    a5_manifest_path = owner / "armindex" / "a5" / "materialized" / "A5_OPAQUE_MATERIALIZATION_MANIFEST.json"
    a5_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    a5_manifest_path.write_text(json.dumps({**a5_manifest_body, "sha256": a5_manifest_hash}), encoding="utf-8")
    return {"manifest": manifest, "manifest_hash": manifest_hash, "manifest_path": manifest_path,
            "opaque_path": opaque_path, "a5_manifest_hash": a5_manifest_hash}


def test_owner_source_lineage_rejects_manifest_pointer_and_opaque_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    owner = tmp_path / "owner"
    source = owner / "protected" / "inputs" / "corpus.jsonl"
    lineage = _write_owner_source_lineage(owner, source)
    monkeypatch.setattr(a6, "CANONICAL_SOURCE_MANIFEST_SHA256", "c" * 64)
    monkeypatch.setattr(a6, "OWNER_SOURCE_MANIFEST_SHA256", lineage["manifest_hash"])
    monkeypatch.setattr(a6, "A5_SOURCE_SNAPSHOT_MANIFEST_SHA256", lineage["a5_manifest_hash"])
    a6._validate_owner_source_provenance(owner, source, expected_rows=1)

    source.write_bytes(b"{\"row\":2}\n")
    with pytest.raises(A6ExecutionError, match="source bytes"):
        a6._validate_owner_source_provenance(owner, source, expected_rows=1)

    source.write_bytes(b"{\"row\":1}\n")
    manifest = dict(lineage["manifest"])
    manifest["full_corpus_row_count"] = 2
    lineage["manifest_path"].write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(A6ExecutionError, match="manifest hash"):
        a6._validate_owner_source_provenance(owner, source, expected_rows=1)

    lineage["manifest_path"].write_text(json.dumps(lineage["manifest"]), encoding="utf-8")
    opaque = json.loads(lineage["opaque_path"].read_text(encoding="utf-8"))
    opaque["expected_final_query_count"] = 871
    lineage["opaque_path"].write_text(json.dumps(opaque), encoding="utf-8")
    with pytest.raises(A6ExecutionError, match="opaque source receipt"):
        a6._validate_owner_source_provenance(owner, source, expected_rows=1)


def test_owner_source_lineage_accepts_only_hash_bound_semantic_bridge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = tmp_path / "owner"
    source = owner / "protected" / "inputs" / "corpus.jsonl"
    lineage = _write_owner_source_lineage(owner, source)
    a5_path = owner / "armindex" / "a5" / "materialized" / "A5_OPAQUE_MATERIALIZATION_MANIFEST.json"
    a5_body = json.loads(a5_path.read_text(encoding="utf-8"))
    a5_body["hashes"]["corpus"] = "f" * 64
    a5_manifest_body = {key: value for key, value in a5_body.items() if key != "sha256"}
    a5_body["sha256"] = a6.canonical_sha256(a5_manifest_body)
    a5_path.write_text(json.dumps(a5_body), encoding="utf-8")
    bridge_body = {
        "schema_version": "myis.armindex-a6-source-equivalence-bridge.v1",
        "status": "PASS_A6_SOURCE_SEMANTIC_EQUIVALENCE_BRIDGE",
        "canonical_source_sha256": a6.file_sha256(source),
        "a5_materialized_source_sha256": "f" * 64,
        "canonical_row_count": 1,
        "a5_row_count": 1,
        "frozen_field_set": ["title_en", "abstract_en", "claims_text", "claims", "publication_ordinal"],
        "canonical_content_multiset_sha256": "e" * 64,
        "a5_content_multiset_sha256": "e" * 64,
        "token_namespace_equivalent": False,
        "protected_payload_included": False,
    }
    bridge_path = owner / "armindex" / "a6" / "a6-source-equivalence-bridge-20260823.json"
    bridge_path.parent.mkdir(parents=True, exist_ok=True)
    bridge_path.write_text(json.dumps({
        **bridge_body, "bridge_sha256": a6.canonical_sha256(bridge_body),
    }), encoding="utf-8")
    monkeypatch.setattr(a6, "EXPECTED_DOCUMENT_COUNT", 1)
    monkeypatch.setattr(a6, "CANONICAL_SOURCE_MANIFEST_SHA256", "c" * 64)
    monkeypatch.setattr(a6, "OWNER_SOURCE_MANIFEST_SHA256", lineage["manifest_hash"])
    monkeypatch.setattr(a6, "A5_SOURCE_SNAPSHOT_MANIFEST_SHA256", a5_body["sha256"])

    a6._validate_owner_source_provenance(owner, source, expected_rows=1)

    invalid = json.loads(bridge_path.read_text(encoding="utf-8"))
    invalid["canonical_content_multiset_sha256"] = "d" * 64
    invalid_body = {key: value for key, value in invalid.items() if key != "bridge_sha256"}
    invalid["bridge_sha256"] = a6.canonical_sha256(invalid_body)
    bridge_path.write_text(json.dumps(invalid), encoding="utf-8")
    with pytest.raises(A6ExecutionError, match="equivalence bridge"):
        a6._validate_owner_source_provenance(owner, source, expected_rows=1)


def test_fresh_attempt_root_is_one_shot_and_owner_local(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    config = _config(tmp_path, source, 45_336)
    root = tmp_path / "owner"
    root.mkdir()
    attempt = root / "a6" / config.attempt_id
    receipt = prepare_fresh_attempt(config, owner_store_root=root, attempt_root=attempt)
    assert receipt["attempt_root_pointer"] == f"a6/{config.attempt_id}"
    with pytest.raises(A6ExecutionError, match="already exists"):
        prepare_fresh_attempt(config, owner_store_root=root, attempt_root=attempt)


def test_resume_truncates_vector_and_metadata_tails_to_one_checkpoint_prefix(tmp_path: Path) -> None:
    vector = tmp_path / "vectors.f32"
    vector.write_bytes(b"1234567890tail")
    metadata = tmp_path / "metadata.jsonl"
    metadata.write_bytes(b"{\"x\":1}\ntail")
    truncate_checkpoint_tails(vector_path=vector, metadata_path=metadata, checkpoint={"vector_bytes": 10, "metadata_bytes": 8})
    assert vector.read_bytes() == b"1234567890"
    assert metadata.read_bytes() == b'{"x":1}\n'


def _checkpoint(config: ExecutionConfig, shard: int) -> dict[str, object]:
    body: dict[str, object] = {
        "schema_version": "myis.armindex-a6-shard-checkpoint.v1", "attempt_id": config.attempt_id,
        "config_sha256": config.config_sha256, "source_sha256": config.source_sha256, "shard": shard,
        "completed_records": 1, "completed_chunks": 1, "vector_bytes": 4, "metadata_bytes": 2,
        "protected_payload_included": False,
    }
    from myis_research.kernel.canonical import canonical_sha256

    return {**body, "checkpoint_sha256": canonical_sha256(body)}


def test_full_resume_requires_same_fresh_root_and_both_compatible_checkpoints(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    config = _config(tmp_path, source, 45_336)
    root = tmp_path / "owner"
    root.mkdir()
    attempt = root / "a6" / config.attempt_id
    prepare_fresh_attempt(config, owner_store_root=root, attempt_root=attempt)
    for shard in (0, 1):
        shard_root = attempt / "owner-local" / f"shard-{shard}"
        shard_root.mkdir(parents=True)
        (shard_root / "flat-l2-normalized.index.f32").write_bytes(b"1234tail")
        (shard_root / "metadata.jsonl").write_bytes(b"{}tail")
        (shard_root / "checkpoint.json").write_text(json.dumps(_checkpoint(config, shard)), encoding="utf-8")
    assert validate_full_attempt_resume(config, owner_store_root=root, attempt_root=attempt)["attempt_id"] == config.attempt_id

    (attempt / "canary").mkdir()
    with pytest.raises(A6ExecutionError, match="canary"):
        validate_full_attempt_resume(config, owner_store_root=root, attempt_root=attempt)

    (attempt / "A6_CANARY_LINEAGE.json").write_text(json.dumps({
        "schema_version": "myis.armindex-a6-canary-lineage.v1",
        "status": "PASS_A6_CANARY_ISOLATED_NON_RESUMABLE", "stage": "canary",
        "attempt_id": config.attempt_id, "config_sha256": config.config_sha256,
        "source_sha256": config.source_sha256, "canary_root_pointer": f"a6/{config.attempt_id}/canary",
        "full_promotion_forbidden": True, "protected_payload_included": False,
        "lineage_sha256": "placeholder",
    }), encoding="utf-8")
    with pytest.raises(A6ExecutionError, match="canary"):
        validate_full_attempt_resume(config, owner_store_root=root, attempt_root=attempt)
    canary_path = attempt / "A6_CANARY_LINEAGE.json"
    canary = json.loads(canary_path.read_text(encoding="utf-8"))
    canary["lineage_sha256"] = a6.canonical_sha256({key: value for key, value in canary.items() if key != "lineage_sha256"})
    canary_path.write_text(json.dumps(canary), encoding="utf-8")
    prepare_full_attempt_after_canary(config, owner_store_root=root, attempt_root=attempt)
    assert validate_full_attempt_resume(config, owner_store_root=root, attempt_root=attempt)["attempt_id"] == config.attempt_id


def test_staged_fresh_root_validates_before_first_launch(tmp_path: Path) -> None:
    owner = tmp_path / "owner"
    attempt = owner / "armindex" / "a6" / "attempt"
    attempt.mkdir(parents=True)
    source = tmp_path / "source.jsonl"
    source.write_text("{}\n", encoding="utf-8")
    config = _config(tmp_path, source, 1)
    body = {
        "schema_version": "myis.armindex-a6-fresh-attempt-root-receipt.v1",
        "status": "PASS_A6_FRESH_ATTEMPT_ROOT", "attempt_id": config.attempt_id,
        "attempt_root_pointer": attempt.relative_to(owner).as_posix(),
        "config_sha256": config.config_sha256, "source_sha256": config.source_sha256,
        "protected_payload_included": False,
    }
    (attempt / "A6_FRESH_ATTEMPT_ROOT.json").write_text(
        json.dumps({**body, "fresh_attempt_root_receipt_sha256": a6.canonical_sha256(body)}, sort_keys=True), encoding="utf-8"
    )
    assert validate_fresh_attempt_root(config, owner_store_root=owner, attempt_root=attempt)["attempt_id"] == config.attempt_id


def test_failure_receipt_is_aggregate_safe_and_bounded(tmp_path: Path) -> None:
    config = _config(tmp_path, tmp_path / "source.jsonl", 45_336)
    receipt = build_failure_receipt(config, stage="full", worker_exit_codes=[1, None], completed_messages=0)
    assert receipt["status"] == "STOP_A6_WITH_OPERATIONAL_EVIDENCE"
    assert receipt["failure_taxonomy"] == {"worker_missing_queue_message": 2, "worker_nonzero_exit": 1, "worker_not_terminated": 1}
    assert "publication_token" not in json.dumps(receipt)


def test_staged_model_tree_hash_changes_when_staged_bytes_change(tmp_path: Path) -> None:
    model = tmp_path / "model"
    model.mkdir()
    weights = model / "model.safetensors"
    weights.write_bytes(b"first")
    first = model_tree_sha256(model)
    weights.write_bytes(b"second")
    assert model_tree_sha256(model) != first


def test_sha256sums_rejects_staged_model_byte_tampering(tmp_path: Path) -> None:
    model = tmp_path / "model"
    model.mkdir()
    weights = model / "model.safetensors"
    weights.write_bytes(b"frozen")
    expected = a6.file_sha256(weights)
    sums = model / "SHA256SUMS"
    sums.write_text(f"{expected}  model.safetensors\n", encoding="utf-8")
    a6._validate_sha256sums(model, sums, required_model_hash=expected)
    weights.write_bytes(b"tampered")
    with pytest.raises(A6ExecutionError, match="byte mismatch"):
        a6._validate_sha256sums(model, sums, required_model_hash=expected)


def test_canonical_model_lock_rejects_critical_artifact_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    a6._validate_canonical_model_lock(adapter_sha256="08bbed4b3f07ce6a52ce60992e178339e69f1672cffe0a04d2f77ffc01cc4f19")
    monkeypatch.setattr(a6, "MODEL_SAFETENSORS_SHA256", "0" * 64)
    with pytest.raises(A6ExecutionError, match="model\.safetensors"):
        a6._validate_canonical_model_lock(
            adapter_sha256="08bbed4b3f07ce6a52ce60992e178339e69f1672cffe0a04d2f77ffc01cc4f19"
        )


def test_runtime_package_lock_rejects_version_drift() -> None:
    packages = {"numpy": "test", "torch": "2.6.0+cu118", "sentence-transformers": "4.1.0", "transformers": "4.51.3"}
    a6._validate_runtime_package_lock(packages)
    packages["transformers"] = "4.50.0"
    with pytest.raises(A6ExecutionError, match="transformers"):
        a6._validate_runtime_package_lock(packages)


class _Worker:
    def __init__(self, exitcode: int | None) -> None:
        self.exitcode = exitcode
        self.terminated = False

    def is_alive(self) -> bool:
        return self.exitcode is None

    def terminate(self) -> None:
        self.terminated = True
        self.exitcode = -15

    def join(self, *, timeout: float) -> None:
        del timeout


def test_launcher_queue_polling_detects_dead_child_without_hanging() -> None:
    workers = [_Worker(1), _Worker(None)]
    messages, passed = LAUNCHER._collect_worker_messages(workers, Queue(), poll_seconds=0.001)
    assert messages == [] and passed is False and workers[1].terminated is True


def test_safe_return_is_aggregate_only_uses_actual_family_ram_and_derived_cost(tmp_path: Path) -> None:
    config = _config(tmp_path, tmp_path / "source.jsonl", 45_336, families=2)
    rows = [
        {"shard": 0, "document_count": 22_000, "family_count": 1, "chunk_count": 30_000, "index_sha256": "a" * 64, "index_size_bytes": 4, "latency_p50_ms": 1, "latency_p95_ms": 2, "latency_p99_ms": 3, "latency_histogram": {"1.0": 2}, "latency_count": 2, "ram_bytes_peak": 5, "vram_bytes_peak": 6, "failure_taxonomy": {}},
        {"shard": 1, "document_count": 23_336, "family_count": 1, "chunk_count": 31_000, "index_sha256": "b" * 64, "index_size_bytes": 6, "latency_p50_ms": 2, "latency_p95_ms": 3, "latency_p99_ms": 4, "latency_histogram": {"2.0": 2}, "latency_count": 2, "ram_bytes_peak": 7, "vram_bytes_peak": 8, "failure_taxonomy": {}},
    ]
    result = build_safe_return_manifest(config, rows, elapsed_seconds=3600, recovery_count=0, safe_export_root=tmp_path / "safe")
    assert result["coverage_rate"] == 1.0
    assert result["family_count"] == 2 and result["ram_bytes_peak"] == 7
    assert result["cost_usd"] == 0.342
    assert "publication_token" not in (tmp_path / "safe" / "A6_SAFE_RETURN_MANIFEST.json").read_text(encoding="utf-8")
    assert "family_token" not in (tmp_path / "safe" / "A6_SAFE_RETURN_MANIFEST.json").read_text(encoding="utf-8")
    rows[1]["document_count"] -= 1
    with pytest.raises(A6ExecutionError, match="coverage"):
        build_safe_return_manifest(config, rows, elapsed_seconds=10, recovery_count=0, safe_export_root=tmp_path / "safe-2")


def test_canary_receipt_is_aggregate_safe_and_cost_is_admission_derived(tmp_path: Path) -> None:
    config = _config(tmp_path, tmp_path / "source.jsonl", 45_336, families=2)
    rows = [
        {"shard": 0, "document_count": 2, "family_count": 1, "chunk_count": 3, "index_sha256": "a" * 64, "index_size_bytes": 4, "latency_p50_ms": 1, "latency_p95_ms": 2, "latency_p99_ms": 3, "latency_histogram": {"1.0": 2}, "latency_count": 2, "ram_bytes_peak": 5, "vram_bytes_peak": 6},
        {"shard": 1, "document_count": 2, "family_count": 1, "chunk_count": 3, "index_sha256": "b" * 64, "index_size_bytes": 4, "latency_p50_ms": 1, "latency_p95_ms": 2, "latency_p99_ms": 3, "latency_histogram": {"1.0": 2}, "latency_count": 2, "ram_bytes_peak": 7, "vram_bytes_peak": 8},
    ]
    receipt = build_canary_receipt(config, rows, elapsed_seconds=3600)
    assert receipt["cost_usd"] == 0.342
    assert receipt["canary_receipt_sha256"]
    assert "publication_token" not in json.dumps(receipt)


def test_latency_histogram_merges_for_global_quantiles() -> None:
    histogram, count, quantiles = merge_latency_histograms([
        {"latency_histogram": {"1.0": 3, "5.0": 1}, "latency_count": 4},
        {"latency_histogram": {"2.0": 4}, "latency_count": 4},
    ])
    assert histogram == {"1.0": 3, "2.0": 4, "5.0": 1}
    assert count == 8 and quantiles == (2.0, 5.0, 5.0)


def test_offline_environment_is_forced(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "PIP_NO_INDEX"):
        monkeypatch.delenv(key, raising=False)
    enforce_offline_environment()
    assert {key: os.environ[key] for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "PIP_NO_INDEX")} == {
        "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PIP_NO_INDEX": "1",
    }


def test_owner_store_index_manifest_is_self_describing_without_ids(tmp_path: Path) -> None:
    config = _config(tmp_path, tmp_path / "source.jsonl", 45_336)
    shard = tmp_path / "shard"
    shard.mkdir()
    index = shard / "flat-l2-normalized.index.f32"
    index.write_bytes(b"index")
    metadata = shard / "metadata.jsonl"
    metadata.write_bytes(b"private")
    manifest = build_owner_store_index_manifest(
        config, shard=0, shard_root=shard, vector_path=index, metadata_path=metadata, records=1,
        family_count=1, chunks=2, latency_histogram={"1.0": 1}, latency_count=1, latency_sum_ms=1.0,
    )
    assert manifest["manifest_sha256"] and "publication_token" not in json.dumps(manifest)
    assert manifest["vector_count"] == 2
    assert manifest["vector_dimension"] == 1024
    assert manifest["vector_normalization"] == "l2_unit"
    assert manifest["metadata_mapping_scope"] == "owner_store_only_document_to_chunk_locator"
