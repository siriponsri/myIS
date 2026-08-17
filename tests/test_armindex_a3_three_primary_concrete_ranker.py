from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from myis_research.armindex.a3_three_primary_asset_bundle import (
    build_a3_three_primary_asset_bundle,
)
from myis_research.armindex.a3_three_primary_concrete_ranker import (
    run_a3_three_primary_ranker,
)
from myis_research.armindex.a3_three_primary_remote_retriever import (
    build_remote_cell_request,
)
from myis_research.kernel.canonical import canonical_json, canonical_sha256, file_sha256


PRIMARY_ARMS = ("ARM-03", "ARM-04", "ARM-05")


def _self_hash(value: dict[str, object], field: str) -> dict[str, object]:
    value[field] = canonical_sha256({key: item for key, item in value.items() if key != field})
    return value


def _runtime() -> dict[str, object]:
    return _self_hash(
        {
            "schema_version": "myis.armindex-a3-three-primary-runtime-bindings.v1",
            "primary_arm_scope": list(PRIMARY_ARMS),
            "budget_extension_sha256": "1" * 64,
            "authority_sha256": "2" * 64,
            "manifest_sha256": "3" * 64,
            "admission_sha256": "4" * 64,
            "winner_bindings": {
                arm_id: {
                    "winner_program_sha256": str(index + 5) * 64,
                    "winner_selection_receipt_sha256": str(index + 8) * 64,
                }
                for index, arm_id in enumerate(PRIMARY_ARMS)
            },
            "target_adapter_sha256s": {arm_id: str(index + 1) * 64 for index, arm_id in enumerate(PRIMARY_ARMS)},
            "runtime_bindings_sha256": "",
        },
        "runtime_bindings_sha256",
    )


def _contract(runtime: dict[str, object]) -> dict[str, object]:
    matrix = [
        {
            "source_arm_id": source,
            "target_arm_id": target,
            "post_admission_action": "reuse_self_winner" if source == target else "validate_cross_arm_transfer",
            "winner_program_sha256": runtime["winner_bindings"][source]["winner_program_sha256"],
            "target_adapter_sha256": runtime["target_adapter_sha256s"][target],
            "result_scope": "aggregate_only",
        }
        for source in PRIMARY_ARMS
        for target in PRIMARY_ARMS
    ]
    return _self_hash(
        {
            "schema_version": "myis.armindex-a3-three-primary-execution-contract.v1",
            "status": "READY_FOR_POST_ADMISSION_EXECUTION",
            "runtime_bindings_sha256": runtime["runtime_bindings_sha256"],
            "transfer_matrix": matrix,
            "fixed_union_sha256": "d" * 64,
            "harness_batch_sha256s": ["e" * 64],
            "execution_order": ["transfer_matrix", "fixed_union_controls", "complete_harnessopt_batches"],
            "selection_permitted": False,
            "final_permitted": False,
            "provider_contact_performed": False,
            "remote_execution_performed": False,
            "execution_contract_sha256": "",
        },
        "execution_contract_sha256",
    )


def _program(arm_id: str, expected_sha: str) -> dict[str, object]:
    body: dict[str, object] = {
        "program_id": f"winner-{arm_id}",
        "arm_id": arm_id,
        "source_fields": ["title"],
        "field_order": ["title"],
        "field_labels": {"title": f"{arm_id}: "},
        "normalization": "unicode_nfkc_whitespace",
        "duplicate_policy": "preserve_all",
        "unitization": {"kind": "family"},
        "family_aggregation": "maxp",
    }
    assert canonical_sha256(body) != expected_sha
    # Fixture hashes are derived from actual program bytes, then bound into runtime.
    return {**body, "program_sha256": canonical_sha256(body)}


def _write_sources(tmp_path: Path) -> tuple[dict[str, object], dict[str, Path], dict[str, Path], Path, Path, dict[str, object]]:
    programs: dict[str, Path] = {}
    models: dict[str, Path] = {}
    runtime = _runtime()
    program_values = {arm_id: _program(arm_id, "") for arm_id in PRIMARY_ARMS}
    for arm_id, program in program_values.items():
        runtime["winner_bindings"][arm_id]["winner_program_sha256"] = program["program_sha256"]
    runtime["runtime_bindings_sha256"] = canonical_sha256(
        {key: item for key, item in runtime.items() if key != "runtime_bindings_sha256"}
    )
    for arm_id, program in program_values.items():
        path = tmp_path / f"{arm_id}.program.json"
        path.write_text(canonical_json(program), encoding="utf-8")
        programs[arm_id] = path
        model = tmp_path / "models" / arm_id
        model.mkdir(parents=True)
        (model / "weights.bin").write_bytes(arm_id.encode("ascii"))
        models[arm_id] = model
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(
        "\n".join(
            canonical_json({"family_token": f"F-{index:032x}", "publication_token": f"P-{index}", "title_en": f"title {index}"})
            for index in range(1, 4)
        ),
        encoding="utf-8",
    )
    queries = tmp_path / "queries.jsonl"
    queries.write_text(
        "\n".join(
            canonical_json({"work_token": f"Q-{index:032x}", "text": f"query {index}"})
            for index in range(1, 251)
        ),
        encoding="utf-8",
    )
    scope = {
        "schema_version": "myis.armindex-a3-train-scope.v1",
        "scope": "Train-250",
        "split_id": "Train-250",
        "query_count": 250,
        "queries_sha256": file_sha256(queries),
    }
    return runtime, programs, models, corpus, queries, scope


def test_builder_and_ranker_bind_train250_winner_programs_and_target_adapters(tmp_path: Path) -> None:
    runtime, programs, models, corpus, queries, scope = _write_sources(tmp_path)
    stage_root = tmp_path / "owner-store" / "a3" / "stage-source-001"
    receipt = build_a3_three_primary_asset_bundle(
        stage_root,
        runtime_bindings=runtime,
        corpus_path=corpus,
        queries_path=queries,
        train_scope=scope,
        winner_program_paths=programs,
        target_model_directories=models,
    )
    assert receipt["scope"] == "Train-250"
    assert receipt["query_count"] == 250
    assert receipt["provider_contacted"] is False
    assets = stage_root / "assets"
    inventory = json.loads((assets / "A3_RUNTIME_ASSETS.json").read_text(encoding="utf-8"))
    contract = _contract(runtime)
    request = build_remote_cell_request(
        contract,
        operation_id="a3-cross-03-04",
        operation_kind="transfer_cell",
        source_arm_id="ARM-03",
        target_arm_id="ARM-04",
        fixed_union_control_id=None,
        retrieval_arm_ids=["ARM-04"],
        output_depth_by_arm={"ARM-04": 3},
        remote_asset_sha256s=inventory["remote_asset_sha256s"],
    )
    request_path = tmp_path / "request.json"
    request_path.write_text(canonical_json(request), encoding="utf-8")
    observed: list[str] = []

    def rank_dense(units, query_map, **kwargs):
        observed.append(units[0].physical_inputs[0].text)
        rows = tuple(SimpleNamespace(family_token=f"F-{index:032x}", rank=index, score=1.0 / index) for index in range(1, 4))
        return {token: rows for token in query_map}, tuple(0.01 for _ in query_map)

    result = run_a3_three_primary_ranker(
        request_path,
        assets_root=assets,
        result_path=tmp_path / "transient-result.json",
        rank_dense=rank_dense,
    )
    assert result["coverage"] == {"expected_units": 250, "completed_units": 250}
    assert len(result["rankings"]["Q-00000000000000000000000000000001"]) == 3
    assert observed and observed[0].startswith("ARM-03:")


def test_fixed_union_uses_equal_depth_rrf_and_never_opens_an_evaluator(tmp_path: Path) -> None:
    runtime, programs, models, corpus, queries, scope = _write_sources(tmp_path)
    root = tmp_path / "owner-store" / "a3" / "stage-source-002"
    build_a3_three_primary_asset_bundle(
        root, runtime_bindings=runtime, corpus_path=corpus, queries_path=queries,
        train_scope=scope, winner_program_paths=programs, target_model_directories=models,
    )
    assets = root / "assets"
    inventory = json.loads((assets / "A3_RUNTIME_ASSETS.json").read_text(encoding="utf-8"))
    request = build_remote_cell_request(
        _contract(runtime), operation_id="a3-commercial-union", operation_kind="fixed_union",
        source_arm_id=None, target_arm_id=None, fixed_union_control_id="commercial_only_fixed_union",
        retrieval_arm_ids=["ARM-04", "ARM-05"], output_depth_by_arm={"ARM-04": 3, "ARM-05": 3},
        remote_asset_sha256s=inventory["remote_asset_sha256s"],
    )
    request_path = tmp_path / "union-request.json"
    request_path.write_text(canonical_json(request), encoding="utf-8")

    def rank_dense(_units, query_map, *, arm_id, **_kwargs):
        ordering = (1, 2, 3) if arm_id == "ARM-04" else (2, 1, 3)
        rows = tuple(SimpleNamespace(family_token=f"F-{index:032x}", rank=rank, score=1.0 / rank) for rank, index in enumerate(ordering, start=1))
        return {token: rows for token in query_map}, tuple(0.02 for _ in query_map)

    result = run_a3_three_primary_ranker(request_path, assets_root=assets, result_path=tmp_path / "union.json", rank_dense=rank_dense)
    assert result["coverage"]["completed_units"] == 250
    assert all(len(rows) == 3 for rows in result["rankings"].values())
