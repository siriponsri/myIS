"""Build a hash-bound Owner-local v16 evaluation input manifest.

This bridge is deliberately outside the frozen executor bundle.  It reads
protected qrels and membership only to calculate aggregate quality, writes the
evaluation manifest only inside the protected store, and never emits rankings
or protected identifiers.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import tarfile
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from . import a1_2_owner_local_evaluator_v16 as evaluator
from . import a1_2_owner_local_measured_runner_v16 as runner
from .a1_2_safe_return_v16 import ARM_IDS, PROGRAM_IDS, validate_safe_return_archive

CELL_IDS = tuple(f"{arm}--{program}" for arm in ARM_IDS for program in PROGRAM_IDS)
MANIFEST_SCHEMA = "myis.armindex-a1.2-owner-local-evaluation-input.v16"
POLICY_SCHEMA = "myis.armindex-a1.2-promotion-policy.v16"
POLICY_SCHEMA_PATH = Path("schemas/armindex/a1.2-promotion-policy.v16.json")
ADOPTION_SCHEMA_PATH = Path("schemas/armindex/a1.2-live-execution-adoption-receipt.v16.json")
BUNDLE_SCHEMA_PATH = Path("schemas/armindex/a1.2-engineering-execution-bundle-receipt.v16.json")
EXECUTION_CONTRACT_SCHEMA_PATH = Path("schemas/armindex/a1.2-engineering-execution-contract.v16.json")
QUOTE_SCHEMA_PATH = Path("schemas/armindex/a1.2-admitted-all-fee-quote-receipt.v16.json")
PROVIDER_ADMISSION_SCHEMA_PATH = Path("schemas/armindex/a1.2-live-provider-admission-receipt.v16.json")
_ADOPTION_BINDINGS = frozenset({
    "provider_identity", "all_fee_quote", "whole_workload_budget",
    "provider_management_authority", "watchdog_ttl", "ssh_identity",
    "runtime_identity", "scientific_request", "adoption_inputs", "transfer",
    "workload", "common_programs", "model_lockset", "protected_compiler",
    "image", "git_commit_tree_bundle", "evaluator", "split",
    "qrels_commitment", "token_map", "safe_return",
    "compiled_bindings_25_of_25", "physical_coverage_35", "promotion_policy",
})


class OwnerLocalEvaluationManifestBuilderV16Error(ValueError):
    """Raised when a protected evaluation input cannot be bound safely."""


def _load(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise OwnerLocalEvaluationManifestBuilderV16Error(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise OwnerLocalEvaluationManifestBuilderV16Error(f"{role} must be an object")
    return value


def _sha(value: object, *, role: str) -> str:
    if not isinstance(value, str) or evaluator.HASH_RE.fullmatch(value) is None:
        raise OwnerLocalEvaluationManifestBuilderV16Error(f"{role} must be a lowercase SHA-256")
    return value


def _regular(path: Path, *, role: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise OwnerLocalEvaluationManifestBuilderV16Error(f"{role} is unavailable") from error
    if path.is_symlink() or not resolved.is_file():
        raise OwnerLocalEvaluationManifestBuilderV16Error(f"{role} is unsafe")
    return resolved


def _inside(root: Path, relative: str, *, role: str) -> Path:
    candidate = Path(relative)
    if not relative or candidate.is_absolute() or ".." in candidate.parts:
        raise OwnerLocalEvaluationManifestBuilderV16Error(f"{role} path is unsafe")
    resolved = _regular(root / candidate, role=role)
    if not resolved.is_relative_to(root):
        raise OwnerLocalEvaluationManifestBuilderV16Error(f"{role} path is unsafe")
    return resolved


def _self_hash(value: Mapping[str, Any], field: str, *, role: str) -> None:
    if value.get(field) != canonical_sha256({key: item for key, item in value.items() if key != field}):
        raise OwnerLocalEvaluationManifestBuilderV16Error(f"{role} self-hash mismatch")


def _schema(repository_root: Path, relative: Path, value: Mapping[str, Any], *, role: str) -> None:
    schema = _load(_regular(repository_root / relative, role=f"{role} schema"), role=f"{role} schema")
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda item: list(item.path))
    if errors:
        raise OwnerLocalEvaluationManifestBuilderV16Error(f"{role} schema failure at {list(errors[0].path)}")


def _input_manifest(path: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    manifest = _load(_regular(path, role="measured input manifest"), role="measured input manifest")
    required = {"schema_version", "status", "attempt_id", "gates", "cells", "work_tokens", "manifest_sha256"}
    if set(manifest) != required or manifest.get("schema_version") != runner.MANIFEST_SCHEMA or manifest.get("status") != "READY":
        raise OwnerLocalEvaluationManifestBuilderV16Error("measured input manifest is not READY v16")
    _self_hash(manifest, "manifest_sha256", role="measured input manifest")
    if not isinstance(manifest["attempt_id"], str) or runner.ATTEMPT_RE.fullmatch(manifest["attempt_id"]) is None:
        raise OwnerLocalEvaluationManifestBuilderV16Error("measured input attempt is invalid")
    gates = manifest["gates"]
    if not isinstance(gates, Mapping) or any(gates.get(name) != "PASS" for name in runner.GATE_NAMES):
        raise OwnerLocalEvaluationManifestBuilderV16Error("measured input gates are not PASS")
    cells = manifest["cells"]
    if not isinstance(cells, list) or len(cells) != 25:
        raise OwnerLocalEvaluationManifestBuilderV16Error("measured input cells are incomplete")
    by_cell = {item.get("cell_id"): item for item in cells if isinstance(item, dict)}
    if set(by_cell) != set(CELL_IDS):
        raise OwnerLocalEvaluationManifestBuilderV16Error("measured input cell topology is invalid")
    for cell, binding in by_cell.items():
        if binding.get("arm_id") != cell.split("--", 1)[0] or binding.get("program_id") != cell.split("--", 1)[1]:
            raise OwnerLocalEvaluationManifestBuilderV16Error("measured input cell lineage is invalid")
        _sha(binding.get("binding_sha256"), role=f"binding {cell}")
    work = manifest["work_tokens"]
    if not isinstance(work, Mapping) or set(work) != {"path", "sha256", "count"} or work.get("count") != 150:
        raise OwnerLocalEvaluationManifestBuilderV16Error("measured input work-token commitment is invalid")
    _sha(work.get("sha256"), role="work-token")
    return manifest, by_cell


def _adoption(repository_root: Path, path: Path, *, attempt_id: str) -> dict[str, Any]:
    receipt = _load(_regular(path, role="execution adoption receipt"), role="execution adoption receipt")
    _schema(repository_root, ADOPTION_SCHEMA_PATH, receipt, role="execution adoption receipt")
    _self_hash(receipt, "receipt_sha256", role="execution adoption receipt")
    if receipt.get("attempt_id") != attempt_id or receipt.get("status") != "PASS_EXECUTION_ADOPTION" or receipt.get("measured_retrieval_allowed") is not True:
        raise OwnerLocalEvaluationManifestBuilderV16Error("execution adoption receipt is not admitted for this attempt")
    bindings = receipt.get("adoption_bindings")
    if not isinstance(bindings, Mapping) or set(bindings) != _ADOPTION_BINDINGS:
        raise OwnerLocalEvaluationManifestBuilderV16Error("execution adoption bindings are incomplete")
    for key in _ADOPTION_BINDINGS:
        _sha(bindings[key], role=f"adoption binding {key}")
    if receipt.get("adoption_binding_set_sha256") != canonical_sha256(dict(bindings)):
        raise OwnerLocalEvaluationManifestBuilderV16Error("execution adoption binding-set hash mismatch")
    return receipt


def _bundle(repository_root: Path, path: Path) -> dict[str, Any]:
    receipt = _load(_regular(path, role="frozen bundle receipt"), role="frozen bundle receipt")
    _schema(repository_root, BUNDLE_SCHEMA_PATH, receipt, role="frozen bundle receipt")
    _self_hash(receipt, "receipt_sha256", role="frozen bundle receipt")
    for key in ("frozen_bundle_sha256", "bundle_manifest_sha256", "bundle_path_set_sha256"):
        _sha(receipt.get(key), role=f"bundle {key}")
    for key in ("git_commit", "git_tree"):
        value = receipt.get(key)
        if not isinstance(value, str) or len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
            raise OwnerLocalEvaluationManifestBuilderV16Error(f"bundle {key} is invalid")
    return receipt


def _controls(root: Path, adoption: Mapping[str, Any]) -> tuple[dict[str, str], dict[str, str], dict[str, str], str, str]:
    request = _load(_regular(root / "control/armindex/a1.2/scientific-execution-adoption-request.v11.json", role="scientific request"), role="scientific request")
    common = _load(_regular(root / "control/armindex/a1.2/common-program-set.v11.json", role="common program set"), role="common program set")
    workload = _load(_regular(root / "control/armindex/a1.2/workload-manifest-set.scientific-request.v11.json", role="workload set"), role="workload set")
    runtime = _load(_regular(root / "control/armindex/a1.2/runtime-lock.direct-base.v5.json", role="runtime lock"), role="runtime lock")
    adoption_inputs = _load(_regular(root / "control/armindex/a1.2/scientific-execution-adoption-inputs.v15.json", role="adoption inputs"), role="adoption inputs")
    lockset = _load(_regular(root / "control/armindex/a1.2/model-lockset.v1.json", role="model lockset"), role="model lockset")
    compiler_integration = _load(_regular(root / "control/armindex/a1.2/protected-compiler-integration.v15.json", role="protected compiler integration"), role="protected compiler integration")
    execution_contract = _load(_regular(root / "control/armindex/a1.2/engineering-execution-contract.v16.json", role="engineering execution contract"), role="engineering execution contract")
    _schema(root, EXECUTION_CONTRACT_SCHEMA_PATH, execution_contract, role="engineering execution contract")
    _self_hash(execution_contract, "contract_sha256", role="engineering execution contract")
    bindings = adoption["adoption_bindings"]
    if request.get("request_sha256") != bindings["scientific_request"] or common.get("program_set_sha256") != bindings["common_programs"] or workload.get("manifest_set_sha256") != bindings["workload"]:
        raise OwnerLocalEvaluationManifestBuilderV16Error("frozen control binding differs from execution adoption")
    if runtime.get("resolved_manifest_digest") != "sha256:" + bindings["image"]:
        raise OwnerLocalEvaluationManifestBuilderV16Error("runtime image differs from execution adoption")
    programs = common.get("programs")
    workloads = workload.get("manifests")
    if not isinstance(programs, list) or not isinstance(workloads, list):
        raise OwnerLocalEvaluationManifestBuilderV16Error("frozen control topology is invalid")
    program_hashes = {item.get("program_key"): item.get("program_spec_sha256") for item in programs if isinstance(item, Mapping)}
    workload_hashes = {item.get("arm_id"): item.get("manifest_sha256") for item in workloads if isinstance(item, Mapping)}
    if set(program_hashes) != set(PROGRAM_IDS) or set(workload_hashes) != set(ARM_IDS):
        raise OwnerLocalEvaluationManifestBuilderV16Error("frozen control topology is incomplete")
    for value in (*program_hashes.values(), *workload_hashes.values()):
        _sha(value, role="frozen control")
    compiler = common.get("compiler_contract")
    if not isinstance(compiler, Mapping):
        raise OwnerLocalEvaluationManifestBuilderV16Error("compiler source manifest is invalid")
    compiler_source = _sha(compiler.get("source_manifest_sha256"), role="compiler source manifest")
    runtime_lock = _sha(runtime.get("runtime_lock_sha256"), role="runtime lock")
    model_hashes = {arm: file_sha256(_regular(root / f"control/armindex/a1.2/model-locks/{arm}.v1.json", role=f"model lock {arm}")) for arm in ARM_IDS}
    evaluator_source = execution_contract["support_sources"]["evaluator_promotion"]
    if evaluator_source.get("path") != "src/myis_research/armindex/a1_2_owner_local_evaluator_v16.py":
        raise OwnerLocalEvaluationManifestBuilderV16Error("engineering contract evaluator source drifted")
    evaluator_sha = _sha(evaluator_source.get("sha256"), role="engineering contract evaluator")
    if file_sha256(_regular(root / evaluator_source["path"], role="frozen evaluator source")) != evaluator_sha:
        raise OwnerLocalEvaluationManifestBuilderV16Error("frozen evaluator source differs from engineering contract")
    expected_bindings = {
        "adoption_inputs": _sha(adoption_inputs.get("contract_sha256"), role="adoption inputs"),
        "model_lockset": _sha(lockset.get("lockset_sha256"), role="model lockset"),
        "protected_compiler": _sha(compiler_integration.get("contract_sha256"), role="protected compiler integration"),
        "evaluator": evaluator_sha,
    }
    if any(adoption["adoption_bindings"][key] != value for key, value in expected_bindings.items()):
        raise OwnerLocalEvaluationManifestBuilderV16Error("frozen control differs from execution adoption")
    return program_hashes, workload_hashes, model_hashes, compiler_source, runtime_lock


def _safe_return_bindings(archive: Path, *, adoption: Mapping[str, Any]) -> dict[str, Any]:
    facts = validate_safe_return_archive(archive)
    with tarfile.open(archive, "r:gz") as bundle:
        member = bundle.extractfile("safe-return-manifest.v16.json")
        if member is None:
            raise OwnerLocalEvaluationManifestBuilderV16Error("safe-return manifest disappeared")
        manifest = json.loads(member.read().decode("ascii"))
    if not isinstance(manifest, dict):
        raise OwnerLocalEvaluationManifestBuilderV16Error("safe-return manifest is invalid")
    bindings = adoption["adoption_bindings"]
    for archive_key, binding_key in (("transfer_manifest_sha256", "transfer"), ("split_commitment_sha256", "split"), ("ephemeral_token_map_sha256", "token_map")):
        if manifest.get(archive_key) != bindings[binding_key]:
            raise OwnerLocalEvaluationManifestBuilderV16Error("safe-return lineage differs from execution adoption")
    if manifest.get("manifest_sha256") != bindings["safe_return"]:
        raise OwnerLocalEvaluationManifestBuilderV16Error("safe-return manifest differs from execution adoption")
    ranking_sha256_by_cell = {
        f"{member.get('arm_id')}--{member.get('program_id')}": member.get("sha256")
        for member in manifest.get("members", [])
        if isinstance(member, Mapping) and member.get("kind") == "ranking"
    }
    if set(ranking_sha256_by_cell) != set(CELL_IDS):
        raise OwnerLocalEvaluationManifestBuilderV16Error("safe-return ranking topology is incomplete")
    for cell, ranking_sha256 in ranking_sha256_by_cell.items():
        _sha(ranking_sha256, role=f"safe-return ranking {cell}")
    facts["ranking_sha256_by_cell"] = ranking_sha256_by_cell
    return facts


def _policy(repository_root: Path, path: Path, *, adoption: Mapping[str, Any]) -> dict[str, Any]:
    value = _load(_regular(path, role="promotion policy"), role="promotion policy")
    _schema(repository_root, POLICY_SCHEMA_PATH, value, role="promotion policy")
    _self_hash(value, "policy_sha256", role="promotion policy")
    if value["policy_sha256"] != adoption["adoption_bindings"]["promotion_policy"]:
        raise OwnerLocalEvaluationManifestBuilderV16Error("promotion policy differs from execution adoption")
    return value


def _provider_admission(repository_root: Path, path: Path, *, adoption: Mapping[str, Any], attempt_id: str) -> dict[str, Any]:
    receipt = _load(_regular(path, role="provider admission receipt"), role="provider admission receipt")
    _schema(repository_root, PROVIDER_ADMISSION_SCHEMA_PATH, receipt, role="provider admission receipt")
    _self_hash(receipt, "receipt_sha256", role="provider admission receipt")
    if receipt["attempt_id"] != attempt_id or receipt["receipt_sha256"] != adoption["provider_admission_receipt_sha256"]:
        raise OwnerLocalEvaluationManifestBuilderV16Error("provider admission differs from execution adoption")
    return receipt


def _quote(repository_root: Path, path: Path, *, admission: Mapping[str, Any], adoption: Mapping[str, Any], attempt_id: str) -> dict[str, Any]:
    receipt = _load(_regular(path, role="admitted all-fee quote receipt"), role="admitted all-fee quote receipt")
    _schema(repository_root, QUOTE_SCHEMA_PATH, receipt, role="admitted all-fee quote receipt")
    _self_hash(receipt, "receipt_sha256", role="admitted all-fee quote receipt")
    if receipt["attempt_id"] != attempt_id or receipt["provider_admission_receipt_sha256"] != admission["receipt_sha256"]:
        raise OwnerLocalEvaluationManifestBuilderV16Error("admitted all-fee quote differs from execution adoption")
    quote_body = {
        key: receipt[key]
        for key in ("provider_admission_receipt_sha256", "currency", "all_fee_usd_per_hour")
    }
    if receipt["quote_sha256"] != canonical_sha256(quote_body):
        raise OwnerLocalEvaluationManifestBuilderV16Error("admitted all-fee quote hash mismatch")
    if receipt["quote_sha256"] != adoption["adoption_bindings"]["all_fee_quote"]:
        raise OwnerLocalEvaluationManifestBuilderV16Error("admitted all-fee quote binding differs from execution adoption")
    rate = receipt["all_fee_usd_per_hour"]
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(float(rate)) or rate < 0:
        raise OwnerLocalEvaluationManifestBuilderV16Error("admitted all-fee hourly quote is invalid")
    return receipt


def _metrics(
    combined_root: Path,
    *,
    manifest: Mapping[str, Any],
    cells: Mapping[str, Mapping[str, Any]],
    archive_bytes: int,
    archive_ranking_sha256_by_cell: Mapping[str, str],
    repository_root: Path,
) -> dict[str, dict[str, Any]]:
    attempt = combined_root.resolve(strict=True) / manifest["attempt_id"]
    if attempt.is_symlink() or not attempt.is_dir():
        raise OwnerLocalEvaluationManifestBuilderV16Error("combined output attempt is unavailable")
    result: dict[str, dict[str, Any]] = {}
    for cell in CELL_IDS:
        receipt = _load(_regular(attempt / "receipts" / f"{cell}.json", role=f"cell receipt {cell}"), role=f"cell receipt {cell}")
        if receipt.get("ranking_file_sha256") != archive_ranking_sha256_by_cell[cell]:
            raise OwnerLocalEvaluationManifestBuilderV16Error(f"cell receipt ranking differs from safe-return archive for {cell}")
        metric = _load(_regular(attempt / "metrics" / f"{cell}.json", role=f"cell metrics {cell}"), role=f"cell metrics {cell}")
        _schema(repository_root, Path("schemas/armindex/a1.2-cell-performance-metrics.v16.json"), metric, role="cell metrics")
        try:
            runner._validate_metrics_sidecar(metric, receipt=receipt, cell=cells[cell], manifest_sha256=manifest["manifest_sha256"])
        except runner.OwnerLocalMeasuredRunnerV16Error as error:
            raise OwnerLocalEvaluationManifestBuilderV16Error(f"cell metrics lineage is invalid for {cell}") from error
        performance = metric["performance"]
        resources = metric["resources"]
        reliability = metric["reliability"]
        result[cell] = {
            "performance": {key: performance[key] for key in ("compile_latency_ms", "index_latency_ms", "search_latency_ms", "throughput_qps", "wall_seconds")},
            "resources": {**resources, "safe_return_bytes": archive_bytes},
            "reliability": {
                "ranking_replay_count": reliability["replay_count"],
                "ranking_replay_hash_match": reliability["ranking_replay_match"],
                "retry_count": reliability["retry_count"],
                "oom_recovery_count": reliability["oom_count"],
                "failure_categories": [] if reliability["failure_category"] == "none" else [reliability["failure_category"]],
            },
        }
    return result


def _allocation(policy: Mapping[str, Any], quote: Mapping[str, Any], metrics: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    cost_policy = policy["cost_allocation"]
    wall_seconds_by_arm = {
        arm: sum(float(metrics[f"{arm}--{program}"]["performance"]["wall_seconds"]) for program in PROGRAM_IDS)
        for arm in ARM_IDS
    }
    rate = float(quote["all_fee_usd_per_hour"])
    cost_per_query_usd_by_arm = {
        arm: 0.0 if arm == "ARM-01" else rate * wall_seconds_by_arm[arm] / 3600.0 / cost_policy["dense_gpu_count"] / cost_policy["queries_per_arm"]
        for arm in ARM_IDS
    }
    body = {
        "rule": cost_policy["rule"],
        "policy_sha256": policy["policy_sha256"],
        "quote_receipt_sha256": quote["receipt_sha256"],
        "quote_sha256": quote["quote_sha256"],
        "all_fee_usd_per_hour": rate,
        "dense_gpu_count": cost_policy["dense_gpu_count"],
        "queries_per_arm": cost_policy["queries_per_arm"],
        "wall_seconds_by_arm": wall_seconds_by_arm,
        "cost_per_query_usd_by_arm": cost_per_query_usd_by_arm,
    }
    return {**body, "allocation_sha256": canonical_sha256(body)}


def _write_immutable(path: Path, value: Mapping[str, Any]) -> None:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    if path.exists():
        if path.is_symlink() or path.read_text(encoding="ascii") != payload:
            raise OwnerLocalEvaluationManifestBuilderV16Error("evaluation manifest already differs")
        return
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def build_evaluation_manifest(
    *,
    safe_return_archive: Path,
    combined_output_root: Path,
    protected_root: Path,
    input_manifest_path: Path,
    adoption_receipt_path: Path,
    bundle_receipt_path: Path,
    provider_admission_receipt_path: Path,
    admitted_quote_receipt_path: Path,
    promotion_policy_path: Path,
    repository_root: Path,
    output_name: str = "evaluation-input.v16.json",
) -> dict[str, Any]:
    """Build one immutable aggregate-safe evaluator input manifest."""

    repository = repository_root.resolve(strict=True)
    protected = protected_root.resolve(strict=True)
    if protected_root.is_symlink() or not protected.is_dir():
        raise OwnerLocalEvaluationManifestBuilderV16Error("protected root is unsafe")
    output = protected / output_name
    if Path(output_name).is_absolute() or ".." in Path(output_name).parts or output.parent != protected:
        raise OwnerLocalEvaluationManifestBuilderV16Error("evaluation manifest output must be directly inside protected root")
    manifest, cells = _input_manifest(input_manifest_path)
    adoption = _adoption(repository, adoption_receipt_path, attempt_id=manifest["attempt_id"])
    bundle = _bundle(repository, bundle_receipt_path)
    bundle_binding = canonical_sha256({
        key: bundle[key]
        for key in ("git_commit", "git_tree", "frozen_bundle_sha256", "bundle_manifest_sha256", "bundle_path_set_sha256")
    })
    if adoption["adoption_bindings"]["git_commit_tree_bundle"] != bundle_binding:
        raise OwnerLocalEvaluationManifestBuilderV16Error("frozen bundle differs from execution adoption")
    provider_admission = _provider_admission(repository, provider_admission_receipt_path, adoption=adoption, attempt_id=manifest["attempt_id"])
    archive = _regular(safe_return_archive, role="safe-return archive")
    safe = _safe_return_bindings(archive, adoption=adoption)
    if safe["attempt_id"] != manifest["attempt_id"]:
        raise OwnerLocalEvaluationManifestBuilderV16Error("safe-return attempt differs from measured input")
    policy = _policy(repository, promotion_policy_path, adoption=adoption)
    quote = _quote(repository, admitted_quote_receipt_path, admission=provider_admission, adoption=adoption, attempt_id=manifest["attempt_id"])
    program_hashes, workload_hashes, model_hashes, compiler_source, runtime_lock = _controls(repository, adoption)
    qrels = _inside(protected, "qrels.jsonl", role="qrels")
    membership = _inside(protected, "membership.jsonl", role="membership")
    qrels_spec = {"path": qrels.name, "sha256": file_sha256(qrels), "count": 150}
    membership_spec = {"path": membership.name, "sha256": file_sha256(membership), "count": 150}
    if adoption["adoption_bindings"]["qrels_commitment"] != qrels_spec["sha256"]:
        raise OwnerLocalEvaluationManifestBuilderV16Error("protected qrels differs from execution adoption")
    qrels_data, eligible = evaluator._load_protected_inputs(protected, {"qrels": qrels_spec, "membership": membership_spec})
    rankings = evaluator._rankings(archive)
    metrics = _metrics(combined_output_root, manifest=manifest, cells=cells, archive_bytes=safe["archive_bytes"], archive_ranking_sha256_by_cell=safe["ranking_sha256_by_cell"], repository_root=repository)
    allocation = _allocation(policy, quote, metrics)
    evaluator_sha = file_sha256(Path(evaluator.__file__ or ""))
    lineage: dict[str, dict[str, str]] = {}
    cell_metrics: dict[str, dict[str, Any]] = {}
    receipt_rows: list[dict[str, Any]] = []
    for cell in CELL_IDS:
        arm, program = cell.split("--", 1)
        value = {
            "request_sha256": adoption["adoption_bindings"]["scientific_request"],
            "adoption_receipt_sha256": file_sha256(_regular(adoption_receipt_path, role="execution adoption receipt")),
            "transfer_manifest_sha256": adoption["adoption_bindings"]["transfer"],
            "workload_manifest_sha256": workload_hashes[arm],
            "program_spec_sha256": program_hashes[program],
            "model_lock_file_sha256": model_hashes[arm],
            "compiler_source_manifest_sha256": compiler_source,
            "runtime_lock_sha256": runtime_lock,
            "image_manifest_digest": "sha256:" + adoption["adoption_bindings"]["image"],
            "git_commit": bundle["git_commit"],
            "git_tree": bundle["git_tree"],
            "frozen_bundle_sha256": bundle["frozen_bundle_sha256"],
            "evaluator_sha256": evaluator_sha,
            "split_commitment_sha256": adoption["adoption_bindings"]["split"],
            "qrels_commitment_sha256": qrels_spec["sha256"],
            "ephemeral_token_map_sha256": adoption["adoption_bindings"]["token_map"],
            "safe_return_archive_sha256": safe["archive_sha256"],
        }
        lineage[cell] = value
        cell_metrics[cell] = metrics[cell]
        receipt_rows.append({"arm_id": arm, "quality": evaluator._quality(rankings[cell], qrels_data, eligible), **metrics[cell]})
    promotion_rows = []
    for arm in ARM_IDS:
        arm_rows = [row for row in receipt_rows if row["arm_id"] == arm]
        promotion_rows.append({
            "arm_id": arm,
            "recall_at_100_out": sum(row["quality"]["recall_at_100_out"] for row in arm_rows) / len(arm_rows),
            "ndcg_at_100_out": sum(row["quality"]["ndcg_at_100_out"] for row in arm_rows) / len(arm_rows),
            "latency_p95_ms": sum(row["performance"]["search_latency_ms"]["p95"] for row in arm_rows) / len(arm_rows),
            "cost_per_query_usd": allocation["cost_per_query_usd_by_arm"][arm],
            "simplicity": policy["simplicity_by_arm"][arm],
        })
    body = {
        "schema_version": MANIFEST_SCHEMA,
        "status": "READY",
        "safe_return_archive_sha256": safe["archive_sha256"],
        "qrels": qrels_spec,
        "membership": membership_spec,
        "lineage_by_cell": lineage,
        "cell_metrics": cell_metrics,
        "promotion": {
            "rule": policy["rule"], "max_arms": policy["max_arms"], "policy_sha256": policy["policy_sha256"],
            "quote_receipt_sha256": quote["receipt_sha256"], "quote_sha256": quote["quote_sha256"],
            "allocation": allocation, "allocation_sha256": allocation["allocation_sha256"], "arms": promotion_rows,
        },
    }
    value = {**body, "manifest_sha256": canonical_sha256(body)}
    _write_immutable(output, value)
    return {"status": "PASS", "attempt_id": manifest["attempt_id"], "cells": 25, "manifest_sha256": value["manifest_sha256"], "policy_sha256": policy["policy_sha256"]}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-owner-evaluation-manifest-builder-v16")
    parser.add_argument("--safe-return-archive", required=True, type=Path)
    parser.add_argument("--combined-output-root", required=True, type=Path)
    parser.add_argument("--protected-root", required=True, type=Path)
    parser.add_argument("--input-manifest", required=True, type=Path)
    parser.add_argument("--adoption-receipt", required=True, type=Path)
    parser.add_argument("--bundle-receipt", required=True, type=Path)
    parser.add_argument("--provider-admission-receipt", required=True, type=Path)
    parser.add_argument("--admitted-quote-receipt", required=True, type=Path)
    parser.add_argument("--promotion-policy", required=True, type=Path)
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--output-name", default="evaluation-input.v16.json")
    args = parser.parse_args(argv)
    try:
        result = build_evaluation_manifest(
            safe_return_archive=args.safe_return_archive,
            combined_output_root=args.combined_output_root,
            protected_root=args.protected_root,
            input_manifest_path=args.input_manifest,
            adoption_receipt_path=args.adoption_receipt,
            bundle_receipt_path=args.bundle_receipt,
            provider_admission_receipt_path=args.provider_admission_receipt,
            admitted_quote_receipt_path=args.admitted_quote_receipt,
            promotion_policy_path=args.promotion_policy,
            repository_root=args.repository_root,
            output_name=args.output_name,
        )
    except OwnerLocalEvaluationManifestBuilderV16Error as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


__all__ = ["OwnerLocalEvaluationManifestBuilderV16Error", "build_evaluation_manifest", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
