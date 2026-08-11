from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path

import pytest

from myis_research.armindex import a1_2_owner_local_evaluator_v16 as evaluator
from myis_research.armindex.a1_2_owner_local_evaluator_v16 import (
    OwnerLocalEvaluatorV16Error,
    evaluate_safe_return,
)
from myis_research.armindex.a1_2_safe_return_v16 import ARM_IDS, PROGRAM_IDS
from myis_research.kernel.canonical import canonical_sha256, file_sha256


def _tokens(prefix: str, count: int) -> list[str]:
    return [f"{prefix}-{index:032x}" for index in range(count)]


def _write(path: Path, value: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return file_sha256(path)


def _archive(path: Path) -> Path:
    work, families, attempt = _tokens("Q", 150), _tokens("F", 100), "a12-v16-evaluator-test"
    payloads: dict[str, bytes] = {}
    specs: list[dict[str, object]] = []
    for arm in ARM_IDS:
        for program in PROGRAM_IDS:
            ranking = f"rankings/{arm}--{program.replace('-', '_')}.jsonl"
            data = ("\n".join(json.dumps({"work_token": token, "family_tokens": families}, sort_keys=True, separators=(",", ":")) for token in work) + "\n").encode("ascii")
            payloads[ranking] = data
            specs.append({"kind": "ranking", "arm_id": arm, "program_id": program, "relative_path": ranking, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)})
            receipt = f"receipts/{arm}--{program.replace('-', '_')}.json"
            body = {"schema_version": "myis.armindex-a1.2-safe-return-resource-receipt.v16", "attempt_id": attempt, "arm_id": arm, "program_id": program, "status": "PASS", "checkpoint_sha256": "a" * 64, "ranking_sha256": specs[-1]["sha256"]}
            data = (json.dumps({**body, "receipt_sha256": canonical_sha256(body)}, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
            payloads[receipt] = data
            specs.append({"kind": "receipt", "arm_id": arm, "program_id": program, "relative_path": receipt, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)})
    body = {"schema_version": "myis.armindex-a1.2-safe-return-manifest.v16", "attempt_id": attempt, "status": "PASS", "transfer_manifest_sha256": "b" * 64, "split_commitment_sha256": "c" * 64, "ephemeral_token_map_sha256": "d" * 64, "work_token_set_sha256": canonical_sha256({"work_tokens": work}), "members": specs}
    payloads["safe-return-manifest.v16.json"] = (json.dumps({**body, "manifest_sha256": canonical_sha256(body)}, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    with tarfile.open(path, "w:gz") as tar:
        for name, data in payloads.items():
            info = tarfile.TarInfo(name); info.size = len(data); tar.addfile(info, io.BytesIO(data))
    return path


def _manifest(root: Path, archive: Path, *, tie: bool = False) -> Path:
    work, families = _tokens("Q", 150), _tokens("F", 100)
    qrels = root / "qrels.jsonl"; membership = root / "membership.jsonl"
    qrels.write_text("\n".join(json.dumps({"work_token": token, "relevance": {families[0]: 2}}) for token in work) + "\n", encoding="utf-8")
    membership.write_text("\n".join(json.dumps({"work_token": token, "eligible_out": True}) for token in work) + "\n", encoding="utf-8")
    lineage = {"request_sha256": "1" * 64, "adoption_receipt_sha256": "2" * 64, "transfer_manifest_sha256": "3" * 64, "workload_manifest_sha256": "4" * 64, "program_spec_sha256": "5" * 64, "model_lock_file_sha256": "6" * 64, "compiler_source_manifest_sha256": "7" * 64, "runtime_lock_sha256": "8" * 64, "image_manifest_digest": "sha256:" + "9" * 64, "git_commit": "a" * 40, "git_tree": "b" * 40, "frozen_bundle_sha256": "c" * 64, "evaluator_sha256": file_sha256(Path(evaluator.__file__)), "split_commitment_sha256": "e" * 64, "qrels_commitment_sha256": file_sha256(qrels), "ephemeral_token_map_sha256": "0" * 64, "safe_return_archive_sha256": file_sha256(archive)}
    cells = [f"{arm}--{program}" for arm in ARM_IDS for program in PROGRAM_IDS]
    resources = {"peak_host_ram_bytes": 1, "peak_vram_bytes": 0, "index_size_bytes": 1, "safe_return_bytes": archive.stat().st_size}
    reliability = {"ranking_replay_count": 2, "ranking_replay_hash_match": True, "retry_count": 0, "oom_recovery_count": 0, "failure_categories": []}
    hourly_rate = 0.6
    performance_by_arm = {arm: {"compile_latency_ms": 1.0, "index_latency_ms": 2.0, "search_latency_ms": {"p50": 1.0, "p95": 1.0 if tie else float(index + 1), "p99": 3.0}, "throughput_qps": 1.0, "wall_seconds": 4.0} for index, arm in enumerate(ARM_IDS)}
    wall_seconds_by_arm = {arm: 20.0 for arm in ARM_IDS}
    cost_by_arm = {arm: 0.0 if arm == "ARM-01" else hourly_rate * wall_seconds_by_arm[arm] / 3600 / 4 / 750 for arm in ARM_IDS}
    allocation_body = {"rule": "dense_arm_all_fee_hourly_x_measured_wall_seconds_div_4_div_750", "policy_sha256": "1" * 64, "quote_receipt_sha256": "2" * 64, "quote_sha256": "3" * 64, "all_fee_usd_per_hour": hourly_rate, "dense_gpu_count": 4, "queries_per_arm": 750, "wall_seconds_by_arm": wall_seconds_by_arm, "cost_per_query_usd_by_arm": cost_by_arm}
    allocation = {**allocation_body, "allocation_sha256": canonical_sha256(allocation_body)}
    promotions = []
    for index, arm in enumerate(ARM_IDS):
        score = 1.0
        performance = performance_by_arm[arm]
        promotions.append({"arm_id": arm, "recall_at_100_out": score, "ndcg_at_100_out": score, "latency_p95_ms": performance["search_latency_ms"]["p95"], "cost_per_query_usd": cost_by_arm[arm], "simplicity": 0 if arm == "ARM-01" else 1})
    body = {"schema_version": "myis.armindex-a1.2-owner-local-evaluation-input.v16", "status": "READY", "safe_return_archive_sha256": file_sha256(archive), "qrels": {"path": qrels.name, "sha256": file_sha256(qrels), "count": 150}, "membership": {"path": membership.name, "sha256": file_sha256(membership), "count": 150}, "lineage_by_cell": {cell: lineage for cell in cells}, "cell_metrics": {cell: {"performance": performance_by_arm[cell.split("--", 1)[0]], "resources": resources, "reliability": reliability} for cell in cells}, "promotion": {"rule": "lexicographic_recall_ndcg_latency_cost_simplicity", "max_arms": 3, "policy_sha256": "1" * 64, "quote_receipt_sha256": "2" * 64, "quote_sha256": "3" * 64, "allocation": allocation, "allocation_sha256": allocation["allocation_sha256"], "arms": promotions}}
    manifest = root / "evaluation.json"
    _write(manifest, {**body, "manifest_sha256": canonical_sha256(body)})
    return manifest


def test_owner_local_evaluator_emits_25_v11_aggregate_receipts_and_three_arms(tmp_path: Path) -> None:
    owner = tmp_path / "owner"; owner.mkdir(); archive = _archive(tmp_path / "return.tar.gz"); manifest = _manifest(owner, archive)
    result = evaluate_safe_return(archive, manifest, output_root=tmp_path / "receipts", repository_root=Path.cwd())
    assert result["status"] == "PASS" and result["receipt_count"] == 25 and result["promoted_arm_count"] == 3
    receipt = json.loads((tmp_path / "receipts" / "a12-v16-evaluator-test" / "receipts" / "ARM-01--P00-TAC-DOC.json").read_text(encoding="ascii"))
    assert receipt["quality"]["recall_at_100_out"] == 1.0
    assert "Q-" not in json.dumps(receipt) and "F-" not in json.dumps(receipt)
    promotion = json.loads((tmp_path / "receipts" / "a12-v16-evaluator-test" / "promotion.json").read_text(encoding="ascii"))
    assert promotion["promoted_arm_ids"] == ["ARM-01", "ARM-02", "ARM-03"]


def test_owner_local_evaluator_rejects_promotion_ties_before_writing(tmp_path: Path) -> None:
    owner = tmp_path / "owner"; owner.mkdir(); archive = _archive(tmp_path / "return.tar.gz"); manifest = _manifest(owner, archive, tie=True)
    with pytest.raises(OwnerLocalEvaluatorV16Error, match="rejects exact ties"):
        evaluate_safe_return(archive, manifest, output_root=tmp_path / "receipts", repository_root=Path.cwd())
    assert not (tmp_path / "receipts").exists()


def test_owner_local_evaluator_rejects_resigned_cost_allocation_drift(tmp_path: Path) -> None:
    owner = tmp_path / "owner"; owner.mkdir(); archive = _archive(tmp_path / "return.tar.gz"); manifest = _manifest(owner, archive)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    allocation = value["promotion"]["allocation"]
    allocation["cost_per_query_usd_by_arm"]["ARM-02"] = 0.0
    allocation_body = {key: item for key, item in allocation.items() if key != "allocation_sha256"}
    allocation["allocation_sha256"] = canonical_sha256(allocation_body)
    value["promotion"]["allocation_sha256"] = allocation["allocation_sha256"]
    body = {key: item for key, item in value.items() if key != "manifest_sha256"}
    _write(manifest, {**body, "manifest_sha256": canonical_sha256(body)})
    with pytest.raises(OwnerLocalEvaluatorV16Error, match="derive from evaluated receipts"):
        evaluate_safe_return(archive, manifest, output_root=tmp_path / "receipts", repository_root=Path.cwd())
