from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path

import pytest

from myis_research.armindex import a1_2_owner_local_evaluator_v16 as evaluator
from myis_research.armindex.a1_2_owner_local_evaluation_manifest_builder_v16 import (
    OwnerLocalEvaluationManifestBuilderV16Error,
    build_evaluation_manifest,
)
from myis_research.armindex.a1_2_owner_local_measured_runner_v16 import (
    ARM_IDS,
    ORIGINAL_PROGRAM_IDS,
)
from myis_research.kernel.canonical import canonical_sha256, file_sha256

ROOT = Path(__file__).resolve().parents[1]
ATTEMPT = "a12-v16-evaluation-builder-test"
CELLS = tuple(f"{arm}--{program}" for arm in ARM_IDS for program in ORIGINAL_PROGRAM_IDS)


def _tokens(prefix: str, count: int) -> list[str]:
    return [f"{prefix}-{index:032x}" for index in range(count)]


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n", encoding="ascii")


def _ranking_bytes() -> bytes:
    work, families = _tokens("Q", 150), _tokens("F", 100)
    return ("\n".join(json.dumps({"work_token": token, "family_tokens": families}, sort_keys=True, separators=(",", ":")) for token in work) + "\n").encode("ascii")


def _archive(path: Path) -> tuple[Path, str]:
    work, _ = _tokens("Q", 150), _tokens("F", 100)
    payloads: dict[str, bytes] = {}
    members: list[dict[str, object]] = []
    for cell in CELLS:
        arm, program = cell.split("--", 1)
        ranking_name = f"rankings/{arm}--{program.replace('-', '_')}.jsonl"
        ranking = _ranking_bytes()
        payloads[ranking_name] = ranking
        ranking_sha = hashlib.sha256(ranking).hexdigest()
        members.append({"kind": "ranking", "arm_id": arm, "program_id": program, "relative_path": ranking_name, "sha256": ranking_sha, "size_bytes": len(ranking)})
        receipt_name = f"receipts/{arm}--{program.replace('-', '_')}.json"
        body = {"schema_version": "myis.armindex-a1.2-safe-return-resource-receipt.v16", "attempt_id": ATTEMPT, "arm_id": arm, "program_id": program, "status": "PASS", "checkpoint_sha256": "a" * 64, "ranking_sha256": ranking_sha}
        receipt = (json.dumps({**body, "receipt_sha256": canonical_sha256(body)}, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
        payloads[receipt_name] = receipt
        members.append({"kind": "receipt", "arm_id": arm, "program_id": program, "relative_path": receipt_name, "sha256": hashlib.sha256(receipt).hexdigest(), "size_bytes": len(receipt)})
    body = {"schema_version": "myis.armindex-a1.2-safe-return-manifest.v16", "attempt_id": ATTEMPT, "status": "PASS", "transfer_manifest_sha256": "b" * 64, "split_commitment_sha256": "c" * 64, "ephemeral_token_map_sha256": "d" * 64, "work_token_set_sha256": canonical_sha256({"work_tokens": work}), "members": members}
    manifest_sha256 = canonical_sha256(body)
    payloads["safe-return-manifest.v16.json"] = (json.dumps({**body, "manifest_sha256": manifest_sha256}, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    with tarfile.open(path, "w:gz") as archive:
        for name, data in payloads.items():
            info = tarfile.TarInfo(name); info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return path, manifest_sha256


def _controls() -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    return tuple(json.loads((ROOT / path).read_text(encoding="utf-8")) for path in (
        "control/armindex/a1.2/scientific-execution-adoption-request.v11.json",
        "control/armindex/a1.2/common-program-set.v11.json",
        "control/armindex/a1.2/workload-manifest-set.scientific-request.v11.json",
        "control/armindex/a1.2/runtime-lock.direct-base.v5.json",
    ))  # type: ignore[return-value]


def _prepare(tmp_path: Path) -> dict[str, Path]:
    protected = tmp_path / "protected"; protected.mkdir()
    owner = tmp_path / "owner"; owner.mkdir()
    combined = tmp_path / "combined"; attempt_root = combined / ATTEMPT
    archive, safe_return_manifest_sha256 = _archive(tmp_path / "safe-return.tar.gz")
    work, families = _tokens("Q", 150), _tokens("F", 100)
    qrels = protected / "qrels.jsonl"
    membership = protected / "membership.jsonl"
    qrels.write_text("\n".join(json.dumps({"work_token": token, "relevance": {families[0]: 2}}) for token in work) + "\n", encoding="utf-8")
    membership.write_text("\n".join(json.dumps({"work_token": token, "eligible_out": True}) for token in work) + "\n", encoding="utf-8")
    cells = []
    for index, cell in enumerate(CELLS):
        arm, program = cell.split("--", 1)
        binding = f"{index:x}".rjust(64, "0")
        cells.append({"cell_id": cell, "arm_id": arm, "program_id": program, "binding_sha256": binding})
        ranking_sha = hashlib.sha256(_ranking_bytes()).hexdigest()
        receipt_body = {"attempt_id": ATTEMPT, "cell_id": cell, "binding_sha256": binding, "ranking_file_sha256": ranking_sha, "ranking_set_sha256": "f" * 64}
        receipt = {**receipt_body, "receipt_sha256": canonical_sha256(receipt_body)}
        _write_json(attempt_root / "receipts" / f"{cell}.json", receipt)
        metrics_body = {
            "schema_version": "myis.armindex-a1.2-cell-performance-metrics.v16", "receipt_id": f"{ATTEMPT}--{cell}--metrics", "attempt_id": ATTEMPT, "cell_id": cell, "status": "PASS", "aggregate_safe": True,
            "manifest_sha256": "pending", "attempt_binding_sha256": "pending", "binding_sha256": binding, "cell_receipt_sha256": receipt["receipt_sha256"], "ranking_file_sha256": ranking_sha, "ranking_set_sha256": "f" * 64,
            "performance": {"compile_latency_ms": 1.0, "index_latency_ms": 2.0, "query_encode_latency_ms": 3.0, "search_latency_ms": {"p50": 1.0, "p95": 2.0, "p99": 3.0}, "throughput_qps": 4.0, "wall_seconds": 5.0},
            "resources": {"peak_host_ram_bytes": 1, "peak_vram_bytes": 2, "index_size_bytes": 3}, "resource_sampling": {"host_rss": "current_process_50ms", "vram": "pytorch_allocator_50ms_and_peak"},
            "reliability": {"replay_count": 2, "replay_ranking_sha256": "f" * 64, "ranking_replay_match": True, "retry_count": 0, "oom_count": 0, "failure_category": "none"},
        }
        cells[-1]["_metrics"] = metrics_body
    manifest_body = {"schema_version": "myis.armindex-a1.2-owner-local-measured-input-manifest.v16", "status": "READY", "attempt_id": ATTEMPT, "gates": {name: "PASS" for name in ("provider_admission", "execution_adoption", "watchdog_ttl", "protected_boundary", "frozen_bindings")}, "cells": [{key: value for key, value in cell.items() if not key.startswith("_")} for cell in cells], "work_tokens": {"path": "work.jsonl", "sha256": "e" * 64, "count": 150}}
    manifest = {**manifest_body, "manifest_sha256": canonical_sha256(manifest_body)}
    input_manifest = owner / "input.json"; _write_json(input_manifest, manifest)
    for cell in cells:
        metrics = cell.pop("_metrics")
        metrics["manifest_sha256"] = manifest["manifest_sha256"]
        metrics["attempt_binding_sha256"] = canonical_sha256({"attempt_id": ATTEMPT, "cell_id": cell["cell_id"], "binding_sha256": cell["binding_sha256"], "manifest_sha256": manifest["manifest_sha256"]})
        _write_json(attempt_root / "metrics" / f"{cell['cell_id']}.json", {**metrics, "metrics_sha256": canonical_sha256(metrics)})
    request, common, workload, runtime = _controls()
    adoption_inputs = json.loads((ROOT / "control/armindex/a1.2/scientific-execution-adoption-inputs.v15.json").read_text(encoding="utf-8"))
    lockset = json.loads((ROOT / "control/armindex/a1.2/model-lockset.v1.json").read_text(encoding="utf-8"))
    compiler = json.loads((ROOT / "control/armindex/a1.2/protected-compiler-integration.v15.json").read_text(encoding="utf-8"))
    execution = json.loads((ROOT / "control/armindex/a1.2/engineering-execution-contract.v16.json").read_text(encoding="utf-8"))
    promotion_control = json.loads((ROOT / "control/armindex/a1.2/promotion-policy.v16.json").read_text(encoding="utf-8"))
    bundle_body = {"schema_version": "myis.armindex-a1.2-engineering-execution-bundle-receipt.v16", "revision_id": "a1.2-engineering-execution-v16", "status": "ENGINEERING_BUNDLE_BUILT_NOT_ADOPTED", "clean_worktree": True, "pushed_to_origin_main": True, "git_commit": "4" * 40, "git_tree": "5" * 40, "frozen_bundle_sha256": "1" * 64, "bundle_manifest_sha256": "2" * 64, "bundle_path_set_sha256": "3" * 64}
    bundle = {**bundle_body, "receipt_sha256": canonical_sha256(bundle_body)}
    bundle_path = owner / "bundle.json"; _write_json(bundle_path, bundle)
    spend = {"common_screen": 1.0, "a1_total": 1.0, "campaign": 1.0}
    provider_body = {"schema_version": "myis.armindex-a1.2-live-provider-admission-receipt.v16", "receipt_kind": "provider_admission", "receipt_id": f"{ATTEMPT}-provider-admission-v16", "revision_id": "a1.2-live-admission-v16", "attempt_id": ATTEMPT, "status": "PASS_PROVIDER_ADMISSION", "claim_boundary": "Aggregate-safe provider admission for the frozen A1.2 test workload only. It contains no raw provider payload, credential, protected query data, retrieval output, launch, or destruction action.", "provider_identity_receipt_sha256": "1" * 64, "ssh_runtime_receipt_sha256": "2" * 64, "management_dry_run_receipt_sha256": "3" * 64, "budget_admission_receipt_sha256": "4" * 64, "budget_revision_id": "a1.2-whole-workload-budget-extension-v17", "watchdog_receipt_sha256": "5" * 64, "budget_status": "PASS_BUDGET_ADMISSION_LOCKED", "budget_admitted": True, "prior_attempt_count": 1, "prior_attempt_spend_usd": spend, "current_worst_case_ttl_charge_usd": 1.0, "projected_spend_usd": spend, "hard_stops_usd": spend, "owner_ttl_hours": 40, "provider_destroy_capability": "READY_NOT_EXECUTED", "provider_admission_receipt_pass": True}
    provider_admission = {**provider_body, "receipt_sha256": canonical_sha256(provider_body)}
    provider_admission_path = owner / "provider-admission.json"; _write_json(provider_admission_path, provider_admission)
    bindings = {name: "a" * 64 for name in (
        "provider_identity", "all_fee_quote", "whole_workload_budget", "provider_management_authority", "watchdog_ttl", "ssh_identity", "runtime_identity", "scientific_request", "adoption_inputs", "transfer", "workload", "common_programs", "model_lockset", "protected_compiler", "image", "git_commit_tree_bundle", "evaluator", "split", "qrels_commitment", "token_map", "safe_return", "compiled_bindings_25_of_25", "physical_coverage_35", "promotion_policy",
    )}
    quote_binding = canonical_sha256({"provider_admission_receipt_sha256": provider_admission["receipt_sha256"], "currency": "USD", "all_fee_usd_per_hour": 0.6})
    bindings.update({"scientific_request": request["request_sha256"], "adoption_inputs": adoption_inputs["contract_sha256"], "common_programs": common["program_set_sha256"], "workload": workload["manifest_set_sha256"], "model_lockset": lockset["lockset_sha256"], "protected_compiler": compiler["contract_sha256"], "image": runtime["resolved_manifest_digest"].split(":", 1)[1], "git_commit_tree_bundle": canonical_sha256({key: bundle[key] for key in ("git_commit", "git_tree", "frozen_bundle_sha256", "bundle_manifest_sha256", "bundle_path_set_sha256")}), "evaluator": execution["support_sources"]["evaluator_promotion"]["sha256"], "transfer": "b" * 64, "split": "c" * 64, "qrels_commitment": file_sha256(qrels), "token_map": "d" * 64, "safe_return": safe_return_manifest_sha256, "all_fee_quote": quote_binding, "promotion_policy": promotion_control["policy_sha256"]})
    adoption_body = {"schema_version": "myis.armindex-a1.2-live-execution-adoption-receipt.v16", "receipt_kind": "execution_adoption", "receipt_id": f"{ATTEMPT}-execution-adoption-v16", "revision_id": "a1.2-live-admission-v16", "attempt_id": ATTEMPT, "status": "PASS_EXECUTION_ADOPTION", "claim_boundary": "Aggregate-safe execution adoption for one immutable frozen A1.2 test attempt only. It retains no credentials, provider payloads, protected inputs, rankings, or per-query outcomes.", "provider_admission_receipt_sha256": provider_admission["receipt_sha256"], "ssh_runtime_receipt_sha256": "2" * 64, "management_dry_run_receipt_sha256": "3" * 64, "watchdog_receipt_sha256": "4" * 64, "adoption_bindings": bindings, "adoption_binding_set_sha256": canonical_sha256(bindings), "provider_admission_receipt_pass": True, "execution_adoption_receipt_pass": True, "launch_allowed": True, "adopted_for_execution": True, "measured_retrieval_allowed": True, "selection_allowed": False, "final_allowed": False, "paid_api_allowed": False}
    adoption = {**adoption_body, "receipt_sha256": canonical_sha256(adoption_body)}
    adoption_path = owner / "adoption.json"; _write_json(adoption_path, adoption)
    quote_body = {"schema_version": "myis.armindex-a1.2-admitted-all-fee-quote-receipt.v16", "receipt_kind": "admitted_all_fee_quote", "receipt_id": f"{ATTEMPT}-all-fee-quote-v16", "attempt_id": ATTEMPT, "status": "PASS_ADMITTED_ALL_FEE_QUOTE", "claim_boundary": "Aggregate-safe admitted all-fee rate for the immutable test attempt. This contains no credentials, raw provider payload, protected input, ranking, per-query outcome, provider action, or scientific result.", "provider_admission_receipt_sha256": adoption["provider_admission_receipt_sha256"], "currency": "USD", "all_fee_usd_per_hour": 0.6, "quote_sha256": bindings["all_fee_quote"]}
    quote = {**quote_body, "receipt_sha256": canonical_sha256(quote_body)}
    quote_path = owner / "quote.json"; _write_json(quote_path, quote)
    policy_body = {"schema_version": "myis.armindex-a1.2-promotion-policy.v16", "status": "READY", "rule": "lexicographic_recall_ndcg_latency_cost_simplicity", "max_arms": 3, "quality_aggregation": {"method": "macro_mean", "metrics": ["recall_at_100_out", "ndcg_at_100_out"], "programs_per_arm": 5}, "latency_aggregation": {"method": "macro_mean", "metric": "search_latency_ms.p95"}, "cost_allocation": {"rule": "dense_arm_all_fee_hourly_x_measured_wall_seconds_div_4_div_750", "quote_source": "admitted_all_fee_quote_receipt", "dense_gpu_count": 4, "queries_per_arm": 750, "arm_01_provider_cost_per_query_usd": 0}, "simplicity_by_arm": {"ARM-01": 0, "ARM-02": 1, "ARM-03": 1, "ARM-04": 1, "ARM-05": 1}, "exact_ties": "reject"}
    policy = {**policy_body, "policy_sha256": canonical_sha256(policy_body)}
    policy_path = owner / "policy.json"; _write_json(policy_path, policy)
    return {"archive": archive, "combined": combined, "protected": protected, "input": input_manifest, "adoption": adoption_path, "bundle": bundle_path, "provider": provider_admission_path, "quote": quote_path, "policy": policy_path}


def _build(paths: dict[str, Path]) -> dict[str, object]:
    return build_evaluation_manifest(
        safe_return_archive=paths["archive"], combined_output_root=paths["combined"],
        protected_root=paths["protected"], input_manifest_path=paths["input"],
        adoption_receipt_path=paths["adoption"], bundle_receipt_path=paths["bundle"],
        provider_admission_receipt_path=paths["provider"],
        admitted_quote_receipt_path=paths["quote"],
        promotion_policy_path=paths["policy"], repository_root=ROOT,
    )

def _resign(value: dict[str, object], field: str = "receipt_sha256") -> dict[str, object]:
    body = {key: item for key, item in value.items() if key != field}
    return {**body, field: canonical_sha256(body)}


def test_builder_writes_evaluator_compatible_aggregate_manifest(tmp_path: Path) -> None:
    paths = _prepare(tmp_path)
    result = _build(paths)
    target = paths["protected"] / "evaluation-input.v16.json"
    assert result["status"] == "PASS" and result["cells"] == 25 and target.is_file()
    manifest = json.loads(target.read_text(encoding="ascii"))
    assert evaluator._validate_manifest(target, file_sha256(paths["archive"]))[1]["manifest_sha256"] == result["manifest_sha256"]
    assert manifest["promotion"]["arms"][0]["cost_per_query_usd"] == 0
    assert manifest["promotion"]["allocation"]["cost_per_query_usd_by_arm"]["ARM-02"] == pytest.approx(0.6 * 25 / 3600 / 4 / 750)
    assert manifest["promotion"]["policy_sha256"] == result["policy_sha256"]
    assert manifest["promotion"]["allocation_sha256"] == manifest["promotion"]["allocation"]["allocation_sha256"]
    assert "Q-" not in target.read_text(encoding="ascii") and "F-" not in target.read_text(encoding="ascii")


def test_builder_rejects_policy_without_valid_self_hash(tmp_path: Path) -> None:
    paths = _prepare(tmp_path)
    policy = json.loads(paths["policy"].read_text(encoding="ascii"))
    policy["policy_sha256"] = "0" * 64
    _write_json(paths["policy"], policy)
    with pytest.raises(OwnerLocalEvaluationManifestBuilderV16Error, match="self-hash"):
        _build(paths)


def test_builder_rejects_resigned_adoption_control_drift(tmp_path: Path) -> None:
    paths = _prepare(tmp_path)
    adoption = json.loads(paths["adoption"].read_text(encoding="ascii"))
    adoption["adoption_bindings"]["model_lockset"] = "0" * 64
    adoption["adoption_binding_set_sha256"] = canonical_sha256(adoption["adoption_bindings"])
    _write_json(paths["adoption"], _resign(adoption))
    with pytest.raises(OwnerLocalEvaluationManifestBuilderV16Error, match="frozen control"):
        _build(paths)


def test_builder_rejects_resigned_bundle_drift(tmp_path: Path) -> None:
    paths = _prepare(tmp_path)
    bundle = json.loads(paths["bundle"].read_text(encoding="ascii"))
    bundle["git_tree"] = "0" * 40
    _write_json(paths["bundle"], _resign(bundle))
    with pytest.raises(OwnerLocalEvaluationManifestBuilderV16Error, match="frozen bundle"):
        _build(paths)


def test_builder_rejects_resigned_ranking_receipt_drift(tmp_path: Path) -> None:
    paths = _prepare(tmp_path)
    receipt_path = paths["combined"] / ATTEMPT / "receipts" / f"{CELLS[0]}.json"
    receipt = json.loads(receipt_path.read_text(encoding="ascii"))
    receipt["ranking_file_sha256"] = "0" * 64
    _write_json(receipt_path, _resign(receipt))
    with pytest.raises(OwnerLocalEvaluationManifestBuilderV16Error, match="safe-return archive"):
        _build(paths)


def test_builder_rejects_qrels_drift(tmp_path: Path) -> None:
    paths = _prepare(tmp_path)
    qrels = paths["protected"] / "qrels.jsonl"
    qrels.write_text(qrels.read_text(encoding="utf-8") + "{}\n", encoding="utf-8")
    with pytest.raises(OwnerLocalEvaluationManifestBuilderV16Error, match="protected qrels"):
        _build(paths)


def test_builder_rejects_resigned_quote_rate_drift(tmp_path: Path) -> None:
    paths = _prepare(tmp_path)
    quote = json.loads(paths["quote"].read_text(encoding="ascii"))
    quote["all_fee_usd_per_hour"] = 0.7
    _write_json(paths["quote"], _resign(quote))
    with pytest.raises(OwnerLocalEvaluationManifestBuilderV16Error, match="quote hash"):
        _build(paths)
