"""Owner-local aggregate evaluator and deterministic arm-promotion bridge.

This module is deliberately not a remote component.  It reads qrels and REP-DEV
membership only from an Owner-local, hash-bound input manifest after the v16
safe-return archive has passed structural validation.  Its only outputs are
aggregate-safe v11 result receipts and an aggregate promotion decision.
"""

from __future__ import annotations

import json
import math
import os
import re
import tarfile
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a1_2_safe_return_v16 import ARM_IDS, PROGRAM_IDS, validate_safe_return_archive

CELL_IDS = tuple(f"{arm}--{program}" for arm in ARM_IDS for program in PROGRAM_IDS)
HASH_RE = re.compile(r"^[a-f0-9]{64}$")
TOKEN_RE = re.compile(r"^[FQ]-[a-f0-9]{32}$")
MANIFEST_SCHEMA = "myis.armindex-a1.2-owner-local-evaluation-input.v16"
PROMOTION_RULE = "lexicographic_recall_ndcg_latency_cost_simplicity"


class OwnerLocalEvaluatorV16Error(ValueError):
    """Raised before a protected value can influence an aggregate receipt."""


def _load(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise OwnerLocalEvaluatorV16Error(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise OwnerLocalEvaluatorV16Error(f"{role} must be an object")
    return value


def _safe(root: Path, relative: Any, *, role: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise OwnerLocalEvaluatorV16Error(f"{role} path is invalid")
    candidate = root / relative
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise OwnerLocalEvaluatorV16Error(f"{role} is unavailable") from error
    if candidate.is_symlink() or not resolved.is_file() or not resolved.is_relative_to(root):
        raise OwnerLocalEvaluatorV16Error(f"{role} path is unsafe")
    return resolved


def _hash(value: Any, *, role: str) -> str:
    if not isinstance(value, str) or HASH_RE.fullmatch(value) is None:
        raise OwnerLocalEvaluatorV16Error(f"{role} must be a lowercase SHA-256")
    return value


def _number(value: Any, *, role: str, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or not float(value) >= minimum:
        raise OwnerLocalEvaluatorV16Error(f"{role} is invalid")
    return float(value)


def _jsonl(path: Path, *, role: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line:
                raise OwnerLocalEvaluatorV16Error(f"{role} contains an empty row")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise OwnerLocalEvaluatorV16Error(f"{role} contains a non-object row")
            rows.append(value)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise OwnerLocalEvaluatorV16Error(f"{role} is invalid JSONL") from error
    if len(rows) != 150:
        raise OwnerLocalEvaluatorV16Error(f"{role} must contain exactly 150 rows")
    return rows


def _load_protected_inputs(root: Path, manifest: Mapping[str, Any]) -> tuple[dict[str, dict[str, int]], set[str]]:
    qrels_spec, membership_spec = manifest.get("qrels"), manifest.get("membership")
    for spec, role in ((qrels_spec, "qrels"), (membership_spec, "membership")):
        if not isinstance(spec, Mapping) or set(spec) != {"path", "sha256", "count"} or spec.get("count") != 150:
            raise OwnerLocalEvaluatorV16Error(f"{role} commitment is invalid")
        _hash(spec.get("sha256"), role=role)
    qrels_path = _safe(root, qrels_spec["path"], role="qrels")
    membership_path = _safe(root, membership_spec["path"], role="membership")
    if file_sha256(qrels_path) != qrels_spec["sha256"] or file_sha256(membership_path) != membership_spec["sha256"]:
        raise OwnerLocalEvaluatorV16Error("protected input hash mismatch")
    qrels: dict[str, dict[str, int]] = {}
    for row in _jsonl(qrels_path, role="qrels"):
        if set(row) != {"work_token", "relevance"} or not isinstance(row["work_token"], str) or TOKEN_RE.fullmatch(row["work_token"]) is None or not row["work_token"].startswith("Q-"):
            raise OwnerLocalEvaluatorV16Error("qrels token domain is invalid")
        relevance = row["relevance"]
        if not isinstance(relevance, dict) or not relevance:
            raise OwnerLocalEvaluatorV16Error("qrels relevance is invalid")
        parsed: dict[str, int] = {}
        for family, grade in relevance.items():
            if not isinstance(family, str) or TOKEN_RE.fullmatch(family) is None or not family.startswith("F-") or isinstance(grade, bool) or not isinstance(grade, int) or grade < 1:
                raise OwnerLocalEvaluatorV16Error("qrels relevance entry is invalid")
            parsed[family] = grade
        if row["work_token"] in qrels:
            raise OwnerLocalEvaluatorV16Error("qrels work token is duplicated")
        qrels[row["work_token"]] = parsed
    eligible: set[str] = set()
    seen: set[str] = set()
    for row in _jsonl(membership_path, role="membership"):
        if set(row) != {"work_token", "eligible_out"} or not isinstance(row["work_token"], str) or TOKEN_RE.fullmatch(row["work_token"]) is None or not row["work_token"].startswith("Q-") or not isinstance(row["eligible_out"], bool) or row["work_token"] in seen:
            raise OwnerLocalEvaluatorV16Error("membership row is invalid")
        seen.add(row["work_token"])
        if row["eligible_out"]:
            eligible.add(row["work_token"])
    if set(qrels) != seen or not eligible:
        raise OwnerLocalEvaluatorV16Error("qrels and REP-DEV membership do not agree")
    return qrels, eligible


def _validate_manifest(path: Path, archive_sha256: str) -> tuple[Path, dict[str, Any]]:
    manifest_path = path.resolve(strict=True)
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise OwnerLocalEvaluatorV16Error("evaluation manifest is unsafe")
    root = manifest_path.parent.resolve()
    value = _load(manifest_path, role="evaluation manifest")
    body = {key: item for key, item in value.items() if key != "manifest_sha256"}
    if value.get("manifest_sha256") != canonical_sha256(body):
        raise OwnerLocalEvaluatorV16Error("evaluation manifest self-hash mismatch")
    required = {"schema_version", "status", "safe_return_archive_sha256", "qrels", "membership", "lineage_by_cell", "cell_metrics", "promotion", "manifest_sha256"}
    if set(value) != required or value.get("schema_version") != MANIFEST_SCHEMA or value.get("status") != "READY":
        raise OwnerLocalEvaluatorV16Error("evaluation manifest is not READY v16")
    if value.get("safe_return_archive_sha256") != archive_sha256:
        raise OwnerLocalEvaluatorV16Error("safe-return archive hash is not bound")
    qrels_spec = value["qrels"]
    _load_protected_inputs(root, value)
    if not isinstance(value["lineage_by_cell"], Mapping) or set(value["lineage_by_cell"]) != set(CELL_IDS):
        raise OwnerLocalEvaluatorV16Error("lineage does not bind all 25 cells")
    lineage_keys = {"request_sha256", "adoption_receipt_sha256", "transfer_manifest_sha256", "workload_manifest_sha256", "program_spec_sha256", "model_lock_file_sha256", "compiler_source_manifest_sha256", "runtime_lock_sha256", "image_manifest_digest", "git_commit", "git_tree", "frozen_bundle_sha256", "evaluator_sha256", "split_commitment_sha256", "qrels_commitment_sha256", "ephemeral_token_map_sha256", "safe_return_archive_sha256"}
    for cell, lineage in value["lineage_by_cell"].items():
        if not isinstance(lineage, Mapping) or set(lineage) != lineage_keys or lineage.get("safe_return_archive_sha256") != archive_sha256:
            raise OwnerLocalEvaluatorV16Error(f"lineage is invalid for {cell}")
        for key, item in lineage.items():
            if key == "image_manifest_digest":
                if not isinstance(item, str) or not re.fullmatch(r"sha256:[a-f0-9]{64}", item):
                    raise OwnerLocalEvaluatorV16Error("image lineage is invalid")
            elif key in {"git_commit", "git_tree"}:
                if not isinstance(item, str) or not re.fullmatch(r"[a-f0-9]{40}", item):
                    raise OwnerLocalEvaluatorV16Error("Git lineage is invalid")
            else:
                _hash(item, role=key)
        if lineage["evaluator_sha256"] != file_sha256(Path(__file__)):
            raise OwnerLocalEvaluatorV16Error("evaluator lineage does not bind this bridge")
        if lineage["qrels_commitment_sha256"] != qrels_spec["sha256"]:
            raise OwnerLocalEvaluatorV16Error("qrels lineage does not bind the protected qrels input")
    if not isinstance(value["cell_metrics"], Mapping) or set(value["cell_metrics"]) != set(CELL_IDS):
        raise OwnerLocalEvaluatorV16Error("metrics do not bind all 25 cells")
    return root, value


def _rankings(archive: Path) -> dict[str, dict[str, list[str]]]:
    result: dict[str, dict[str, list[str]]] = {}
    with tarfile.open(archive, "r:gz") as bundle:
        for arm in ARM_IDS:
            for program in PROGRAM_IDS:
                cell = f"{arm}--{program}"
                name = f"rankings/{arm}--{program.replace('-', '_')}.jsonl"
                stream = bundle.extractfile(name)
                if stream is None:
                    raise OwnerLocalEvaluatorV16Error("validated safe-return member disappeared")
                rows: dict[str, list[str]] = {}
                for line in stream.read().decode("ascii").splitlines():
                    row = json.loads(line)
                    rows[row["work_token"]] = row["family_tokens"]
                if len(rows) != 150 or any(len(value) != 100 for value in rows.values()):
                    raise OwnerLocalEvaluatorV16Error("safe-return ranking topology drifted")
                result[cell] = rows
    return result


def _dcg(ranking: list[str], relevance: Mapping[str, int], cutoff: int) -> float:
    return sum(((2 ** relevance.get(family, 0) - 1) / __import__("math").log2(rank + 1)) for rank, family in enumerate(ranking[:cutoff], start=1))


def _quality(rows: Mapping[str, list[str]], qrels: Mapping[str, Mapping[str, int]], eligible: set[str]) -> dict[str, Any]:
    recalls: list[float] = []
    ndcg100: list[float] = []
    ndcg10: list[float] = []
    pairs = 0
    for work in sorted(eligible):
        relevant = qrels[work]
        pairs += len(relevant)
        ranking = rows[work]
        recalls.append(len(set(ranking) & set(relevant)) / len(relevant))
        ideal = sorted(relevant.values(), reverse=True)
        for cutoff, target in ((100, ndcg100), (10, ndcg10)):
            denominator = sum(((2 ** grade - 1) / __import__("math").log2(rank + 1)) for rank, grade in enumerate(ideal[:cutoff], start=1))
            target.append(0.0 if denominator == 0 else _dcg(ranking, relevant, cutoff) / denominator)
    return {"recall_at_100_out": sum(recalls) / len(recalls), "ndcg_at_100_out": sum(ndcg100) / len(ndcg100), "ndcg_at_10_out": sum(ndcg10) / len(ndcg10), "unique_relevant_family_query_pairs": pairs, "judged_query_count": len(eligible), "tie_rate": 0.0, "failure_rate": 0.0}


def _receipt(cell: str, value: Mapping[str, Any], quality: Mapping[str, Any], archive_bytes: int) -> dict[str, Any]:
    arm, program = cell.split("--", 1)
    metrics = value["cell_metrics"][cell]
    if not isinstance(metrics, Mapping) or set(metrics) != {"performance", "resources", "reliability"}:
        raise OwnerLocalEvaluatorV16Error("cell metrics are incomplete")
    resources = dict(metrics["resources"])
    if resources.get("safe_return_bytes") != archive_bytes:
        raise OwnerLocalEvaluatorV16Error("safe-return bytes are not bound to the archive")
    body = {"schema_version": "myis.armindex-a1.2-aggregate-result-receipt.v11", "receipt_id": f"{value['safe_return_archive_sha256'][:16]}--{cell}", "status": "PASS", "evidence_class": "measured_development_aggregate", "scientific_authority": True, "claim_boundary": "Aggregate-only Owner-local REP-DEV evaluation after validated v16 safe return; no rankings, identifiers, qrels, membership, or per-query outcomes are projected.", "arm_id": arm, "program_id": program, "lineage": dict(value["lineage_by_cell"][cell]), "completion": {"rep_dev_query_count": 150, "returned_query_count": 150, "top_k": 100, "valid_result_lists": 150, "unique_results_per_work_token": 100, "program_arm_complete": True}, "quality": dict(quality), "performance": dict(metrics["performance"]), "resources": resources, "reliability": dict(metrics["reliability"]), "safety": {"protected_payload_projected": False, "per_query_outcome_projected": False, "selection_accessed": False, "final_accessed": False, "model_weight_changed": False}}
    schema = _load(Path(__file__).resolve().parents[3] / "schemas/armindex/a1.2-aggregate-result-receipt.v11.json", role="aggregate receipt schema")
    body["receipt_sha256"] = canonical_sha256(body)
    errors = sorted(Draft202012Validator(schema).iter_errors(body), key=lambda item: list(item.path))
    if errors:
        raise OwnerLocalEvaluatorV16Error(f"v11 aggregate receipt schema failure at {list(errors[0].path)}")
    assert_aggregate_only(body)
    return body


def _promotion(value: Mapping[str, Any], receipts: list[Mapping[str, Any]]) -> dict[str, Any]:
    promotion = value["promotion"]
    required = {"rule", "max_arms", "policy_sha256", "quote_receipt_sha256", "quote_sha256", "allocation", "allocation_sha256", "arms"}
    if not isinstance(promotion, Mapping) or set(promotion) != required or promotion.get("rule") != PROMOTION_RULE or promotion.get("max_arms") != 3 or not isinstance(promotion["arms"], list) or len(promotion["arms"]) != 5:
        raise OwnerLocalEvaluatorV16Error("frozen promotion rule is invalid")
    for key in ("policy_sha256", "quote_receipt_sha256", "quote_sha256", "allocation_sha256"):
        _hash(promotion.get(key), role=f"promotion {key}")
    allocation = promotion["allocation"]
    allocation_required = {"rule", "policy_sha256", "quote_receipt_sha256", "quote_sha256", "all_fee_usd_per_hour", "dense_gpu_count", "queries_per_arm", "wall_seconds_by_arm", "cost_per_query_usd_by_arm", "allocation_sha256"}
    if not isinstance(allocation, Mapping) or set(allocation) != allocation_required or allocation.get("rule") != "dense_arm_all_fee_hourly_x_measured_wall_seconds_div_4_div_750" or allocation.get("dense_gpu_count") != 4 or allocation.get("queries_per_arm") != 750:
        raise OwnerLocalEvaluatorV16Error("promotion allocation policy is invalid")
    if any(allocation.get(key) != promotion[key] for key in ("policy_sha256", "quote_receipt_sha256", "quote_sha256", "allocation_sha256")):
        raise OwnerLocalEvaluatorV16Error("promotion allocation provenance is not bound")
    allocation_body = {key: item for key, item in allocation.items() if key != "allocation_sha256"}
    if allocation["allocation_sha256"] != canonical_sha256(allocation_body):
        raise OwnerLocalEvaluatorV16Error("promotion allocation self-hash mismatch")
    hourly_rate = _number(allocation.get("all_fee_usd_per_hour"), role="promotion all-fee hourly quote")
    wall_seconds = allocation.get("wall_seconds_by_arm")
    costs = allocation.get("cost_per_query_usd_by_arm")
    if not isinstance(wall_seconds, Mapping) or not isinstance(costs, Mapping) or set(wall_seconds) != set(ARM_IDS) or set(costs) != set(ARM_IDS):
        raise OwnerLocalEvaluatorV16Error("promotion allocation arms are incomplete")
    scores: list[tuple[tuple[float, float, float, float, float], str]] = []
    seen: set[str] = set()
    by_arm: dict[str, list[Mapping[str, Any]]] = {arm: [] for arm in ARM_IDS}
    for receipt in receipts:
        by_arm[receipt["arm_id"]].append(receipt)
    for row in promotion["arms"]:
        if not isinstance(row, Mapping) or set(row) != {"arm_id", "recall_at_100_out", "ndcg_at_100_out", "latency_p95_ms", "cost_per_query_usd", "simplicity"} or row.get("arm_id") not in ARM_IDS or row["arm_id"] in seen:
            raise OwnerLocalEvaluatorV16Error("promotion arm row is invalid")
        seen.add(row["arm_id"])
        score = (_number(row["recall_at_100_out"], role="promotion recall"), _number(row["ndcg_at_100_out"], role="promotion ndcg"), _number(row["latency_p95_ms"], role="promotion latency"), _number(row["cost_per_query_usd"], role="promotion cost"), _number(row["simplicity"], role="promotion simplicity"))
        arm_receipts = by_arm[row["arm_id"]]
        expected_recall = sum(item["quality"]["recall_at_100_out"] for item in arm_receipts) / len(arm_receipts)
        expected_ndcg = sum(item["quality"]["ndcg_at_100_out"] for item in arm_receipts) / len(arm_receipts)
        expected_latency = sum(item["performance"]["search_latency_ms"]["p95"] for item in arm_receipts) / len(arm_receipts)
        expected_wall_seconds = sum(item["performance"]["wall_seconds"] for item in arm_receipts)
        expected_cost = 0.0 if row["arm_id"] == "ARM-01" else hourly_rate * expected_wall_seconds / 3600.0 / 4.0 / 750.0
        expected_simplicity = 0.0 if row["arm_id"] == "ARM-01" else 1.0
        if abs(score[0] - expected_recall) > 1e-12 or abs(score[1] - expected_ndcg) > 1e-12 or abs(score[2] - expected_latency) > 1e-12 or abs(score[3] - expected_cost) > 1e-12 or abs(score[4] - expected_simplicity) > 1e-12 or abs(_number(wall_seconds[row["arm_id"]], role="promotion wall seconds") - expected_wall_seconds) > 1e-12 or abs(_number(costs[row["arm_id"]], role="promotion cost allocation") - expected_cost) > 1e-12:
            raise OwnerLocalEvaluatorV16Error("promotion quality scores do not derive from evaluated receipts")
        scores.append((score, row["arm_id"]))
    if seen != set(ARM_IDS) or len({score for score, _arm in scores}) != 5:
        raise OwnerLocalEvaluatorV16Error("frozen promotion rule rejects exact ties")
    ordered = sorted(scores, key=lambda item: (-item[0][0], -item[0][1], item[0][2], item[0][3], item[0][4]))
    return {"schema_version": "myis.armindex-a1.2-arm-promotion.v16", "status": "PASS", "rule": PROMOTION_RULE, "policy_sha256": promotion["policy_sha256"], "quote_receipt_sha256": promotion["quote_receipt_sha256"], "quote_sha256": promotion["quote_sha256"], "allocation_sha256": promotion["allocation_sha256"], "max_promoted_arms": 3, "promoted_arm_ids": [arm for _score, arm in ordered[:3]], "candidate_arm_count": 5, "tie_rejected": True}


def _write(path: Path, value: Mapping[str, Any]) -> None:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="ascii") != payload:
            raise OwnerLocalEvaluatorV16Error("immutable output already differs")
        return
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def evaluate_safe_return(archive_path: Path, evaluation_manifest_path: Path, *, output_root: Path, repository_root: Path) -> dict[str, Any]:
    """Evaluate one complete safe return and emit aggregate-only immutable receipts."""

    archive = archive_path.resolve(strict=True)
    archive_facts = validate_safe_return_archive(archive)
    root, manifest = _validate_manifest(evaluation_manifest_path, archive_facts["archive_sha256"])
    output = output_root.resolve()
    repository = repository_root.resolve()
    if output.is_relative_to(repository) or output.is_relative_to(root):
        raise OwnerLocalEvaluatorV16Error("aggregate output must use a separate Owner-local directory")
    qrels, eligible = _load_protected_inputs(root, manifest)
    rankings = _rankings(archive)
    if file_sha256(archive) != archive_facts["archive_sha256"]:
        raise OwnerLocalEvaluatorV16Error("safe-return archive changed during evaluation")
    receipts = [_receipt(cell, manifest, _quality(rankings[cell], qrels, eligible), archive_facts["archive_bytes"]) for cell in CELL_IDS]
    decision = _promotion(manifest, receipts)
    decision_body = {**decision, "receipt_sha256": canonical_sha256(decision)}
    assert_aggregate_only(decision_body)
    attempt = archive_facts["attempt_id"]
    target = output / attempt
    if target.exists():
        raise OwnerLocalEvaluatorV16Error("evaluation output already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{attempt}.", dir=output.parent))
    try:
        for receipt in receipts:
            _write(staging / "receipts" / f"{receipt['arm_id']}--{receipt['program_id']}.json", receipt)
        _write(staging / "promotion.json", decision_body)
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staging, target)
    except BaseException:
        import shutil
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {"status": "PASS", "attempt_id": attempt, "receipt_count": 25, "promoted_arm_count": 3, "promotion_receipt_sha256": decision_body["receipt_sha256"]}


__all__ = ["OwnerLocalEvaluatorV16Error", "evaluate_safe_return"]
