from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

import myis_research.armindex.a1_2_owner_local_measured_runner_v16 as measured_runner
from myis_research.armindex.a1_2_measured_executor_v16 import (
    FamilyRank,
    MeasuredExecutorV16Error,
)
from myis_research.armindex.a1_2_owner_local_measured_runner_v16 import (
    OwnerLocalMeasuredRunnerV16Error,
    _physical_inputs,
    merge_measured_arm_outputs,
    run_owner_local_measured_screen,
    validate_manifest,
)
from myis_research.kernel.canonical import canonical_sha256, file_sha256

ARMS = ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")
PROGRAMS = ("P00-TAC-DOC", "P01-TA-DOC", "P02-CLAIM1", "P03-PASSAGE", "P04-SECTION-MULTIVIEW")


def _write_json(path: Path, value: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return file_sha256(path)


def _manifest(tmp_path: Path) -> Path:
    root = tmp_path / "protected-store"
    root.mkdir()
    corpus = root / "compiled" / "corpus.jsonl"
    corpus.parent.mkdir(parents=True)
    corpus.write_text(
        "".join(
            json.dumps(
                {"logical_id": f"unit-{i}", "family_token": f"F-{i:032x}", "view_id": ("title", "abstract", "claims")[i % 3], "text": "alpha", "source_token_count": 1},
                separators=(",", ":"),
            )
            + "\n"
            for i in range(100)
        ),
        encoding="utf-8",
    )
    queries = root / "compiled" / "queries.jsonl"
    queries.write_text(
        "".join(
            json.dumps({"work_token": f"Q-{i:032x}", "text": "alpha"}, separators=(",", ":")) + "\n"
            for i in range(150)
        ),
        encoding="utf-8",
    )
    work = root / "inputs" / "work.jsonl"
    work.parent.mkdir(parents=True)
    work.write_bytes(queries.read_bytes())
    cells = []
    for arm in ARMS:
        for program in PROGRAMS:
            binding = root / "bindings" / f"{arm}--{program.replace('-', '_')}.json"
            binding_hash = _write_json(binding, {"binding_id": f"{arm}--{program}", "aggregate_safe": True})
            executable = "P02-FIRST-CLAIM" if program == "P02-CLAIM1" else program
            cells.append(
                {
                    "cell_id": f"{arm}--{program}",
                    "arm_id": arm,
                    "program_id": program,
                    "executable_program_id": executable,
                    "binding_path": binding.relative_to(root).as_posix(),
                    "binding_sha256": binding_hash,
                    "corpus_path": corpus.relative_to(root).as_posix(),
                    "corpus_sha256": file_sha256(corpus),
                    "query_path": queries.relative_to(root).as_posix(),
                    "query_sha256": file_sha256(queries),
                }
            )
    body = {
        "schema_version": "myis.armindex-a1.2-owner-local-measured-input-manifest.v16",
        "revision_id": "synthetic-v16",
        "status": "READY",
        "attempt_id": "a12-v16-synthetic",
        "gates": {name: "PASS" for name in ("provider_admission", "execution_adoption", "watchdog_ttl", "protected_boundary", "frozen_bindings")},
        "work_tokens": {"path": work.relative_to(root).as_posix(), "sha256": file_sha256(work), "count": 150},
        "cells": cells,
    }
    manifest = root / "manifest.json"
    _write_json(manifest, {**body, "manifest_sha256": canonical_sha256(body)})
    return manifest


def test_compiled_physical_inputs_allow_exact_token_ids_only_when_valid() -> None:
    values = _physical_inputs(
        {"physical_inputs": [{"text": "opaque", "source_token_count": 2, "token_ids": [1, 2]}]},
        role="compiled corpus",
    )
    assert values[0].token_ids == (1, 2)
    with pytest.raises(OwnerLocalMeasuredRunnerV16Error, match="token-ID"):
        _physical_inputs(
            {"physical_inputs": [{"text": "opaque", "source_token_count": 2, "token_ids": [True]}]},
            role="compiled corpus",
        )


def test_owner_local_bridge_runs_25_cells_and_preserves_p02_bridge(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    calls: list[str] = []

    def synthetic_executor(*, arm_id: str, program_id: str, queries: dict[str, object], **_: object) -> dict[str, tuple[FamilyRank, ...]]:
        calls.append(f"{arm_id}:{program_id}")
        ranks = tuple(FamilyRank(f"F-{i:032x}", i + 1, float(100 - i)) for i in range(100))
        return {token: ranks for token in queries}

    result = run_owner_local_measured_screen(
        manifest,
        output_root=tmp_path / "owner-receipts",
        adapters={arm: object() for arm in ("ARM-02", "ARM-03", "ARM-04", "ARM-05")},
        batch_executor=synthetic_executor,
        measured_mode=False,
    )
    assert result["status"] == "PASS" and result["cells"] == 25 and result["work_tokens"] == 150
    assert "ARM-01:P02-FIRST-CLAIM" in calls
    assert len(calls) == 25
    receipt = tmp_path / "owner-receipts" / "a12-v16-synthetic" / "receipts" / "screen.json"
    assert receipt.is_file()
    value = json.loads(receipt.read_text(encoding="ascii"))
    assert value["aggregate_safe"] is True and value["top_k"] == 100
    assert "family_token" not in value and "per_query" not in value
    ranking = tmp_path / "owner-receipts" / "a12-v16-synthetic" / "rankings" / "ARM-01--P02-CLAIM1.jsonl"
    rows = [json.loads(line) for line in ranking.read_text(encoding="ascii").splitlines()]
    assert len(rows) == 150 and all(set(row) == {"work_token", "family_tokens"} and len(row["family_tokens"]) == 100 for row in rows)
    cell_receipt = json.loads((tmp_path / "owner-receipts" / "a12-v16-synthetic" / "receipts" / "ARM-01--P02-CLAIM1.json").read_text(encoding="ascii"))
    assert cell_receipt["ranking_path"] == "rankings/ARM-01--P02-CLAIM1.jsonl"
    assert cell_receipt["ranking_file_sha256"] == file_sha256(ranking)
    assert "output_root" not in result and result["output_relative"] == "a12-v16-synthetic/receipts"


def test_owner_local_bridge_rejects_gate_drift_and_writes_nothing(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    value = json.loads(manifest.read_text(encoding="ascii"))
    value["gates"]["execution_adoption"] = "FAIL"
    body = {key: item for key, item in value.items() if key != "manifest_sha256"}
    manifest.write_text(json.dumps({**body, "manifest_sha256": canonical_sha256(body)}, sort_keys=True) + "\n", encoding="ascii")
    with pytest.raises(OwnerLocalMeasuredRunnerV16Error, match="gates"):
        run_owner_local_measured_screen(manifest, output_root=tmp_path / "owner-receipts", batch_executor=lambda **_: {}, measured_mode=False)
    assert not (tmp_path / "owner-receipts").exists()


def test_owner_local_bridge_rejects_partial_executor_result(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)

    def short_executor(*, queries: dict[str, object], **_: object) -> dict[str, tuple[FamilyRank, ...]]:
        short = (FamilyRank("F-" + "0" * 32, 1, 1.0),)
        return {token: short for token in queries}

    with pytest.raises(OwnerLocalMeasuredRunnerV16Error, match="exactly 100"):
        run_owner_local_measured_screen(manifest, output_root=tmp_path / "owner-receipts", batch_executor=short_executor, measured_mode=False)
    assert not (tmp_path / "owner-receipts").exists()


def test_owner_local_bridge_resumes_from_durable_cell_receipts(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    output = tmp_path / "owner-receipts"
    calls = 0

    def interrupted_executor(*, queries: dict[str, object], **_: object) -> dict[str, tuple[FamilyRank, ...]]:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise RuntimeError("synthetic interruption")
        ranks = tuple(FamilyRank(f"F-{index:032x}", index + 1, float(100 - index)) for index in range(100))
        return {token: ranks for token in queries}

    with pytest.raises(RuntimeError, match="synthetic interruption"):
        run_owner_local_measured_screen(
            manifest,
            output_root=output,
            batch_executor=interrupted_executor,
            arm_ids=("ARM-01",),
            measured_mode=False,
        )
    partial = output / "a12-v16-synthetic" / "receipts"
    assert len(list(partial.glob("ARM-01--*.json"))) == 2

    def complete_executor(*, queries: dict[str, object], **_: object) -> dict[str, tuple[FamilyRank, ...]]:
        nonlocal calls
        calls += 1
        ranks = tuple(FamilyRank(f"F-{index:032x}", index + 1, float(100 - index)) for index in range(100))
        return {token: ranks for token in queries}

    result = run_owner_local_measured_screen(
        manifest,
        output_root=output,
        batch_executor=complete_executor,
        arm_ids=("ARM-01",),
        measured_mode=False,
    )
    assert result["status"] == "PASS" and result["cells"] == 5
    assert calls == 6


def test_default_executor_emits_schema_valid_bound_metrics_sidecars(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    output = tmp_path / "owner-receipts"
    result = run_owner_local_measured_screen(
        manifest,
        output_root=output,
        arm_ids=("ARM-01",),
    )
    assert result["status"] == "PASS" and result["cells"] == 5
    attempt = output / "a12-v16-synthetic"
    summary = json.loads((attempt / "receipts" / "screen.json").read_text(encoding="ascii"))
    sidecars = [
        json.loads(path.read_text(encoding="ascii"))
        for path in sorted((attempt / "metrics").glob("ARM-01--*.json"))
    ]
    commits = [
        json.loads(path.read_text(encoding="ascii"))
        for path in sorted((attempt / "commits").glob("ARM-01--*.json"))
    ]
    schema = json.loads(
        Path("schemas/armindex/a1.2-cell-performance-metrics.v16.json").read_text(encoding="ascii")
    )
    assert len(sidecars) == 5
    assert len(commits) == 5
    assert not any(Draft202012Validator(schema).iter_errors(sidecars[0]))
    commit_schema = json.loads(
        Path("schemas/armindex/a1.2-owner-local-cell-commit.v16.json").read_text(encoding="ascii")
    )
    assert not any(Draft202012Validator(commit_schema).iter_errors(commits[0]))
    assert summary["cell_metrics_sha256"] == canonical_sha256(
        [sidecar["metrics_sha256"] for sidecar in sidecars]
    )
    assert summary["cell_commits_sha256"] == canonical_sha256(
        [commit["commit_sha256"] for commit in commits]
    )

    def keys(value: object) -> set[str]:
        if isinstance(value, dict):
            return set(value) | set().union(*(keys(item) for item in value.values()))
        if isinstance(value, list):
            return set().union(*(keys(item) for item in value))
        return set()

    assert all(
        sidecar["reliability"]["replay_count"] == 2
        and sidecar["reliability"]["replay_ranking_sha256"] == sidecar["ranking_set_sha256"]
        and keys(sidecar).isdisjoint({"work_token", "family_tokens", "family_token", "query_id"})
        for sidecar in sidecars
    )


def test_default_executor_failure_writes_safe_immutable_sidecar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = _manifest(tmp_path)
    output = tmp_path / "owner-receipts"

    def failed_executor(**_: object) -> object:
        raise MeasuredExecutorV16Error("synthetic")

    monkeypatch.setattr(measured_runner, "execute_program_cell_batch_instrumented", failed_executor)
    with pytest.raises(MeasuredExecutorV16Error, match="synthetic"):
        run_owner_local_measured_screen(manifest, output_root=output, arm_ids=("ARM-01",))
    failure = json.loads(
        (output / "a12-v16-synthetic" / "metrics" / "ARM-01--P00-TAC-DOC.failure.json").read_text(encoding="ascii")
    )
    schema = json.loads(
        Path("schemas/armindex/a1.2-cell-performance-failure-metrics.v16.json").read_text(encoding="ascii")
    )
    assert not any(Draft202012Validator(schema).iter_errors(failure))
    assert failure["reliability"] == {"retry_count": 0, "oom_count": 0, "failure_category": "runtime"}
    assert "error" not in json.dumps(failure).lower()
    with pytest.raises(OwnerLocalMeasuredRunnerV16Error, match="fresh attempt"):
        run_owner_local_measured_screen(manifest, output_root=output, arm_ids=("ARM-01",))


@pytest.mark.parametrize("crash_after", ("ranking", "receipt", "metrics", "commit"))
def test_measured_cell_commit_recovers_each_write_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, crash_after: str
) -> None:
    manifest = _manifest(tmp_path)
    output = tmp_path / "owner-receipts"
    raised = False

    def crash_once(name: str) -> None:
        nonlocal raised
        if name == crash_after and not raised:
            raised = True
            raise RuntimeError(f"crash-after-{name}")

    monkeypatch.setattr(measured_runner, "_after_cell_artifact", crash_once)
    with pytest.raises(RuntimeError, match=f"crash-after-{crash_after}"):
        run_owner_local_measured_screen(manifest, output_root=output, arm_ids=("ARM-01",))
    result = run_owner_local_measured_screen(manifest, output_root=output, arm_ids=("ARM-01",))
    assert result["status"] == "PASS" and result["cells"] == 5
    attempt = output / "a12-v16-synthetic"
    commits = sorted((attempt / "commits").glob("ARM-01--*.json"))
    metrics = [json.loads(path.read_text(encoding="ascii")) for path in sorted((attempt / "metrics").glob("ARM-01--*.json"))]
    assert len(commits) == len(metrics) == 5
    if crash_after == "commit":
        assert not (attempt / "failed-partial" / "ARM-01--P00-TAC-DOC").exists()
        assert metrics[0]["reliability"]["retry_count"] == 0
    else:
        recovery = attempt / "failed-partial" / "ARM-01--P00-TAC-DOC" / "retry-1" / "recovery.json"
        assert recovery.is_file()
        assert metrics[0]["reliability"]["retry_count"] == 1


def test_measured_mode_rejects_injected_batch_executor(tmp_path: Path) -> None:
    with pytest.raises(OwnerLocalMeasuredRunnerV16Error, match="frozen production executor"):
        run_owner_local_measured_screen(
            _manifest(tmp_path),
            output_root=tmp_path / "owner-receipts",
            batch_executor=lambda **_: {},
        )


def test_manifest_rejects_shuffled_cells(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    value = json.loads(manifest.read_text(encoding="ascii"))
    value["cells"][0], value["cells"][1] = value["cells"][1], value["cells"][0]
    body = {key: item for key, item in value.items() if key != "manifest_sha256"}
    manifest.write_text(
        json.dumps({**body, "manifest_sha256": canonical_sha256(body)}, sort_keys=True) + "\n",
        encoding="ascii",
    )
    with pytest.raises(OwnerLocalMeasuredRunnerV16Error, match="order"):
        validate_manifest(manifest)


def test_validate_manifest_is_aggregate_safe(tmp_path: Path) -> None:
    value = validate_manifest(_manifest(tmp_path))
    assert value == {"status": "PASS", "attempt_id": "a12-v16-synthetic", "cells": 25, "work_token_count": 150, "top_k": 100, "manifest_sha256": value["manifest_sha256"]}


def test_per_arm_execution_merges_to_exact_25_cells(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    input_root.mkdir()
    manifest = _manifest(input_root)

    def synthetic_executor(*, queries: dict[str, object], **_: object) -> dict[str, tuple[FamilyRank, ...]]:
        ranks = tuple(FamilyRank(f"F-{index:032x}", index + 1, float(100 - index)) for index in range(100))
        return {token: ranks for token in queries}

    partials: dict[str, Path] = {}
    for arm in ARMS:
        output = tmp_path / "partials" / arm
        run_owner_local_measured_screen(
            manifest,
            output_root=output,
            adapters={} if arm == "ARM-01" else {arm: object()},
            batch_executor=synthetic_executor,
            arm_ids=(arm,),
            measured_mode=False,
        )
        partials[arm] = output
    result = merge_measured_arm_outputs(
        manifest,
        arm_output_roots=partials,
        output_root=tmp_path / "merged",
    )
    assert result["status"] == "PASS" and result["cells"] == 25
    receipts = tmp_path / "merged" / "a12-v16-synthetic" / "receipts"
    assert len(list(receipts.glob("ARM-*.json"))) == 25

    tampered = partials["ARM-02"] / "a12-v16-synthetic" / "receipts" / "ARM-02--P00-TAC-DOC.json"
    value = json.loads(tampered.read_text(encoding="ascii"))
    value["binding_sha256"] = "f" * 64
    body = {key: item for key, item in value.items() if key != "receipt_sha256"}
    tampered.write_text(json.dumps({**body, "receipt_sha256": canonical_sha256(body)}, sort_keys=True) + "\n", encoding="ascii")
    with pytest.raises(OwnerLocalMeasuredRunnerV16Error, match="arm cell receipt"):
        merge_measured_arm_outputs(
            manifest,
            arm_output_roots=partials,
            output_root=tmp_path / "merged-tampered",
        )
