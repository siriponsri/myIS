"""Evaluate the complete A3 three-primary batch inside an Owner Store.

Returned ranking packages are protected Owner-local inputs.  This command
validates their remote-return lineage and the frozen Train-250 commitments
before opening the local qrels/membership files.  It writes only aggregate
results and a safe-return receipt, all under the supplied Owner Store root.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any

from myis_research.armindex.a1_2_owner_local_evaluator_v16 import _quality
from myis_research.armindex.a3_three_primary_owner_evaluator import (
    A3ThreePrimaryOwnerEvaluatorError,
    build_aggregate_safe_return_receipt,
    evaluate_remote_ranking_owner_local,
)
from myis_research.armindex.a3_three_primary_remote_launcher import (
    validate_a3_remote_stage_manifest,
    validate_a3_remote_stage_receipt,
    validate_a3_transient_ranking_return_receipt,
)
from myis_research.armindex.a3_three_primary_remote_retriever import (
    validate_remote_cell_request,
    validate_remote_ranking_package,
)
from myis_research.kernel.canonical import canonical_sha256, file_sha256
from myis_research.protection import assert_aggregate_only


_PRIMARY_ARMS = ("ARM-03", "ARM-04", "ARM-05")
_FIXED_OPERATIONS = (
    "fixed-all-primary-rrf60",
    "fixed-best-single",
    "fixed-commercial-only-fixed-union",
    "fixed-top-three-rrf60",
    "fixed-top-two-rrf60",
)
_EXPECTED_OPERATIONS = frozenset(
    (*_FIXED_OPERATIONS, *(f"transfer-arm-{source[-2:]}-to-arm-{target[-2:]}" for source in _PRIMARY_ARMS for target in _PRIMARY_ARMS))
)
_SHA256 = frozenset("0123456789abcdef")


class A3OwnerBatchEvaluatorError(ValueError):
    """Raised without revealing protected ranking or relevance material."""


def evaluate_a3_owner_batch(
    *,
    owner_store_root: Path,
    stage_receipt_path: Path,
    stage_manifest_path: Path,
    runtime_bindings_path: Path,
    train_package_root: Path,
    requests_dir: Path,
    rankings_dir: Path,
    return_receipts_dir: Path,
    aggregate_output_dir: Path,
    safe_return_receipt_path: Path,
) -> dict[str, Any]:
    """Run the complete 14-operation A3 aggregate evaluation fail-closed."""

    owner_root = _owner_directory(owner_store_root, role="Owner Store root")
    paths = {
        "stage receipt": stage_receipt_path,
        "stage manifest": stage_manifest_path,
        "runtime bindings": runtime_bindings_path,
        "requests": requests_dir,
        "rankings": rankings_dir,
        "return receipts": return_receipts_dir,
        "aggregate output": aggregate_output_dir,
        "safe-return receipt": safe_return_receipt_path,
    }
    for role, path in paths.items():
        _inside_owner_store(owner_root, path, role=role)
    package_root = _owner_directory(train_package_root, owner_root=owner_root, role="Train-250 package root")
    stage = validate_a3_remote_stage_receipt(_load_json(stage_receipt_path, role="stage receipt"))
    manifest = validate_a3_remote_stage_manifest(_load_json(stage_manifest_path, role="stage manifest"))
    if stage["stage_manifest_sha256"] != manifest["stage_manifest_sha256"]:
        raise A3OwnerBatchEvaluatorError("stage receipt does not bind its stage manifest")
    bindings = _runtime_bindings(_load_json(runtime_bindings_path, role="runtime bindings"))
    if bindings["runtime_bindings_sha256"] != manifest["runtime_bindings_sha256"]:
        raise A3OwnerBatchEvaluatorError("runtime bindings do not match the stage receipt")
    _train_package(package_root, bindings=bindings, stage=stage)
    request_paths = _json_files(requests_dir, role="request directory")
    if set(request_paths) != _EXPECTED_OPERATIONS:
        raise A3OwnerBatchEvaluatorError("A3 batch does not contain the exact 14 operations")
    ranking_paths = _json_files(rankings_dir, role="ranking directory")
    return_paths = _json_files(return_receipts_dir, role="ranking return directory")
    if set(ranking_paths) != _EXPECTED_OPERATIONS or set(return_paths) != _EXPECTED_OPERATIONS:
        raise A3OwnerBatchEvaluatorError("A3 returned inputs do not contain the exact 14 operations")
    if aggregate_output_dir.exists() or aggregate_output_dir.is_symlink():
        raise A3OwnerBatchEvaluatorError("aggregate output directory must be new")
    if safe_return_receipt_path.exists() or safe_return_receipt_path.is_symlink():
        raise A3OwnerBatchEvaluatorError("safe-return receipt destination already exists")

    # This is the sole protected-data transition: all remote and hash bindings
    # above must be valid before qrels/membership are opened.
    qrels, eligible = _evaluation_inputs(
        package_root / "inputs" / "qrels.jsonl",
        package_root / "inputs" / "membership.jsonl",
        expected_qrels_sha256=bindings["package_bindings"]["qrels_commitment_sha256"],
        expected_membership_sha256=bindings["package_bindings"]["membership_commitment_sha256"],
    )
    results: list[dict[str, Any]] = []
    aggregate_output_dir.mkdir(parents=True, exist_ok=False)
    try:
        for operation_id in sorted(_EXPECTED_OPERATIONS):
            request = validate_remote_cell_request(_load_json(request_paths[operation_id], role="remote request"))
            _validate_request(request, operation_id=operation_id, stage=manifest)
            ranking_path = ranking_paths[operation_id]
            returned = validate_a3_transient_ranking_return_receipt(
                _load_json(return_paths[operation_id], role="ranking return receipt")
            )
            ranking = validate_remote_ranking_package(_load_json(ranking_path, role="returned ranking package"))
            _validate_return_lineage(returned, ranking_path=ranking_path, ranking=ranking, request=request, stage=stage)
            result = evaluate_remote_ranking_owner_local(
                request,
                ranking,
                evaluator_binding_sha256=bindings["package_bindings"]["evaluator_sha256"],
                evaluator_input_sha256=canonical_sha256(
                    {
                        "qrels_sha256": bindings["package_bindings"]["qrels_commitment_sha256"],
                        "membership_sha256": bindings["package_bindings"]["membership_commitment_sha256"],
                        "ranking_sha256": ranking["ranking_sha256"],
                    }
                ),
                metric_evaluator=lambda ranks: _metrics(ranks, qrels=qrels, eligible=eligible),
            )
            _write_new(aggregate_output_dir / f"{operation_id}.aggregate-result.json", result)
            results.append(result)
        safe_return = build_aggregate_safe_return_receipt(
            results, runtime_bindings_sha256=bindings["runtime_bindings_sha256"]
        )
        _write_new(safe_return_receipt_path, safe_return)
    except BaseException:
        # Do not leave a partial batch that could be confused with measured A3.
        for path in aggregate_output_dir.glob("*.aggregate-result.json"):
            path.unlink(missing_ok=True)
        aggregate_output_dir.rmdir()
        raise
    return {
        "schema_version": "myis.armindex-a3-three-primary-owner-batch-evaluation.v1",
        "status": "PASS_A3_OWNER_LOCAL_COMPLETE_BATCH_EVALUATION",
        "attempt_id": stage["attempt_id"],
        "operation_count": len(results),
        "aggregate_output_count": len(results),
        "safe_return_receipt_sha256": safe_return["receipt_sha256"],
        "rankings_embedded": False,
        "protected_payload_included": False,
    }


def _runtime_bindings(value: Mapping[str, Any]) -> dict[str, Any]:
    bindings = dict(value)
    required = {
        "schema_version", "primary_arm_scope", "budget_extension_sha256", "authority_sha256",
        "manifest_sha256", "admission_sha256", "winner_bindings", "target_adapter_sha256s",
        "package_bindings", "runtime_bindings_sha256",
    }
    if set(bindings) != required or bindings.get("schema_version") != "myis.armindex-a3-three-primary-runtime-bindings.v1":
        raise A3OwnerBatchEvaluatorError("runtime bindings are incomplete")
    if bindings["primary_arm_scope"] != list(_PRIMARY_ARMS):
        raise A3OwnerBatchEvaluatorError("runtime bindings changed the A3 primary-arm scope")
    _require_hash(bindings["runtime_bindings_sha256"], role="runtime bindings")
    if bindings["runtime_bindings_sha256"] != canonical_sha256({key: item for key, item in bindings.items() if key != "runtime_bindings_sha256"}):
        raise A3OwnerBatchEvaluatorError("runtime binding self-hash drift")
    package = bindings["package_bindings"]
    expected_package = {
        "corpus_sha256", "query_bundle_sha256", "split_commitment_sha256", "evaluator_sha256",
        "qrels_commitment_sha256", "membership_commitment_sha256", "runtime_lock_sha256", "data_handoff_sha256",
    }
    if not isinstance(package, Mapping) or set(package) != expected_package:
        raise A3OwnerBatchEvaluatorError("runtime package bindings are incomplete")
    for role, digest in package.items():
        _require_hash(digest, role=role)
    return bindings


def _train_package(root: Path, *, bindings: Mapping[str, Any], stage: Mapping[str, Any]) -> dict[str, Any]:
    receipt = _load_json(root / "A3_TRAIN250_OWNER_PACKAGE_RECEIPT.json", role="Train-250 package receipt")
    if receipt.get("receipt_sha256") != canonical_sha256({key: item for key, item in receipt.items() if key != "receipt_sha256"}):
        raise A3OwnerBatchEvaluatorError("Train-250 package receipt self-hash drift")
    package = _load_json(root / "package-bindings.json", role="Train-250 package bindings")
    if package.get("package_bindings_sha256") != canonical_sha256({key: item for key, item in package.items() if key != "package_bindings_sha256"}):
        raise A3OwnerBatchEvaluatorError("Train-250 package bindings self-hash drift")
    scope = _load_json(root / "train-scope.json", role="Train-250 scope")
    expected_scope = {
        "schema_version": "myis.armindex-a3-train-scope.v1", "scope": "Train-250",
        "split_id": "Train-250", "query_count": 250,
        "queries_sha256": bindings["package_bindings"]["query_bundle_sha256"],
        "split_commitment_sha256": bindings["package_bindings"]["split_commitment_sha256"],
    }
    if scope != expected_scope or receipt.get("status") != "PASS_A3_TRAIN250_OWNER_PACKAGE" or receipt.get("query_count") != 250:
        raise A3OwnerBatchEvaluatorError("Train-250 package scope drift")
    expected_hashes = {
        "corpus_sha256": bindings["package_bindings"]["corpus_sha256"],
        "queries_sha256": bindings["package_bindings"]["query_bundle_sha256"],
        "qrels_sha256": bindings["package_bindings"]["qrels_commitment_sha256"],
        "membership_sha256": bindings["package_bindings"]["membership_commitment_sha256"],
    }
    for key, digest in expected_hashes.items():
        if package.get("input_hashes", {}).get(key) != digest or receipt.get(key) != digest:
            raise A3OwnerBatchEvaluatorError("Train-250 package binding drift")
    if stage["remote_asset_sha256s"]["corpus_sha256"] != expected_hashes["corpus_sha256"] or stage["remote_asset_sha256s"]["queries_sha256"] != expected_hashes["queries_sha256"]:
        raise A3OwnerBatchEvaluatorError("Train-250 package does not match staged assets")
    return package


def _evaluation_inputs(qrels_path: Path, membership_path: Path, *, expected_qrels_sha256: str, expected_membership_sha256: str) -> tuple[dict[str, dict[str, int]], set[str]]:
    if file_sha256(_regular_file(qrels_path, role="qrels")) != expected_qrels_sha256 or file_sha256(_regular_file(membership_path, role="membership")) != expected_membership_sha256:
        raise A3OwnerBatchEvaluatorError("local evaluator input hash drift")
    qrels: dict[str, dict[str, int]] = {}
    for row in _jsonl(qrels_path, role="qrels"):
        if set(row) != {"work_token", "relevance"} or not isinstance(row["work_token"], str) or not isinstance(row["relevance"], Mapping):
            raise A3OwnerBatchEvaluatorError("qrels schema is invalid")
        relevance = row["relevance"]
        if not relevance or any(not isinstance(family, str) or not isinstance(score, int) or isinstance(score, bool) or score <= 0 for family, score in relevance.items()):
            raise A3OwnerBatchEvaluatorError("qrels relevance is invalid")
        if row["work_token"] in qrels:
            raise A3OwnerBatchEvaluatorError("qrels has duplicate work tokens")
        qrels[row["work_token"]] = dict(relevance)
    memberships: dict[str, bool] = {}
    for row in _jsonl(membership_path, role="membership"):
        if set(row) != {"work_token", "eligible_out"} or not isinstance(row["work_token"], str) or not isinstance(row["eligible_out"], bool) or row["work_token"] in memberships:
            raise A3OwnerBatchEvaluatorError("membership schema is invalid")
        memberships[row["work_token"]] = row["eligible_out"]
    if len(qrels) != 250 or set(qrels) != set(memberships):
        raise A3OwnerBatchEvaluatorError("Train-250 evaluator coverage is incomplete")
    eligible = {token for token, is_eligible in memberships.items() if is_eligible}
    if not eligible:
        raise A3OwnerBatchEvaluatorError("Train-250 has no eligible OUT queries")
    return qrels, eligible


def _metrics(rankings: Mapping[str, Any], *, qrels: Mapping[str, Mapping[str, int]], eligible: set[str]) -> dict[str, str]:
    if set(rankings) != set(qrels):
        raise A3OwnerBatchEvaluatorError("ranking query coverage differs from Train-250")
    evaluated: dict[str, list[str]] = {}
    for token in sorted(eligible):
        rows = rankings.get(token)
        if not isinstance(rows, Sequence) or len(rows) != 100:
            raise A3OwnerBatchEvaluatorError("top-100 ranking coverage is incomplete")
        families = [row.get("family_token") if isinstance(row, Mapping) else None for row in rows]
        if any(not isinstance(family, str) for family in families) or len(set(families)) != 100:
            raise A3OwnerBatchEvaluatorError("top-100 ranking is invalid")
        evaluated[token] = list(families)
    value = _quality(evaluated, qrels, eligible)
    return {
        "recall_at_100/out": _decimal(value["recall_at_100_out"]),
        "ndcg_at_100/out": _decimal(value["ndcg_at_100_out"]),
        "ndcg_at_10/out": _decimal(value["ndcg_at_10_out"]),
    }


def _validate_request(request: Mapping[str, Any], *, operation_id: str, stage: Mapping[str, Any]) -> None:
    if request["operation_id"] != operation_id or request["runtime_bindings_sha256"] != stage["runtime_bindings_sha256"] or request["execution_contract_sha256"] != stage["execution_contract_sha256"] or request["remote_asset_sha256s"] != stage["remote_asset_sha256s"]:
        raise A3OwnerBatchEvaluatorError("remote request does not bind the staged A3 runtime")


def _validate_return_lineage(returned: Mapping[str, Any], *, ranking_path: Path, ranking: Mapping[str, Any], request: Mapping[str, Any], stage: Mapping[str, Any]) -> None:
    expected = {
        "attempt_id": stage["attempt_id"], "operation_id": request["operation_id"],
        "request_sha256": request["request_sha256"], "stage_receipt_sha256": stage["receipt_sha256"],
        "ranking_sha256": ranking["ranking_sha256"], "ranking_package_receipt_sha256": ranking["receipt_sha256"],
        "ranking_package_file_sha256": file_sha256(ranking_path),
    }
    if any(returned[key] != value for key, value in expected.items()):
        raise A3OwnerBatchEvaluatorError("returned ranking lineage drift")


def _json_files(directory: Path, *, role: str) -> dict[str, Path]:
    root = _owner_directory(directory, role=role)
    result: dict[str, Path] = {}
    for path in root.glob("*.json"):
        if path.is_symlink() or not path.is_file() or path.stem in result:
            raise A3OwnerBatchEvaluatorError(f"{role} contains an unsafe file")
        result[path.stem] = path
    return result


def _required_child(directory: Path, operation_id: str, *, role: str) -> Path:
    return _regular_file(directory / f"{operation_id}.json", role=role)


def _owner_directory(path: Path, *, owner_root: Path | None = None, role: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise A3OwnerBatchEvaluatorError(f"{role} is unavailable") from error
    if path.is_symlink() or not resolved.is_dir():
        raise A3OwnerBatchEvaluatorError(f"{role} is unsafe")
    if owner_root is not None and not resolved.is_relative_to(owner_root):
        raise A3OwnerBatchEvaluatorError(f"{role} escapes the Owner Store")
    return resolved


def _inside_owner_store(owner_root: Path, path: Path, *, role: str) -> None:
    try:
        resolved = path.resolve(strict=False)
    except OSError as error:
        raise A3OwnerBatchEvaluatorError(f"{role} is unavailable") from error
    if not resolved.is_relative_to(owner_root):
        raise A3OwnerBatchEvaluatorError(f"{role} must remain inside the Owner Store")


def _regular_file(path: Path, *, role: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise A3OwnerBatchEvaluatorError(f"{role} is unavailable") from error
    if path.is_symlink() or not resolved.is_file():
        raise A3OwnerBatchEvaluatorError(f"{role} is unsafe")
    return resolved


def _load_json(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(_regular_file(path, role=role).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A3OwnerBatchEvaluatorError(f"{role} is not valid JSON") from error
    if not isinstance(value, dict):
        raise A3OwnerBatchEvaluatorError(f"{role} must be a JSON object")
    return value


def _jsonl(path: Path, *, role: str) -> list[dict[str, Any]]:
    try:
        rows = [json.loads(line) for line in _regular_file(path, role=role).read_text(encoding="utf-8").splitlines()]
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A3OwnerBatchEvaluatorError(f"{role} is invalid") from error
    if not rows or any(not isinstance(row, dict) for row in rows):
        raise A3OwnerBatchEvaluatorError(f"{role} is invalid")
    return rows


def _require_hash(value: Any, *, role: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(character not in _SHA256 for character in value):
        raise A3OwnerBatchEvaluatorError(f"{role} SHA-256 is invalid")


def _decimal(value: Any) -> str:
    number = float(value)
    if not math.isfinite(number) or not 0 <= number <= 1:
        raise A3OwnerBatchEvaluatorError("aggregate metric is invalid")
    return format(number, ".12g")


def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    assert_aggregate_only(value)
    if path.exists() or path.is_symlink():
        raise A3OwnerBatchEvaluatorError("aggregate receipt destination already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(dict(value), ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="ascii", dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        handle.write(serialized)
        temporary = Path(handle.name)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-a3-three-primary-owner-batch-evaluator")
    parser.add_argument("--owner-store-root", required=True, type=Path)
    parser.add_argument("--stage-receipt", required=True, type=Path, dest="stage_receipt_path")
    parser.add_argument("--stage-manifest", required=True, type=Path, dest="stage_manifest_path")
    parser.add_argument("--runtime-bindings", required=True, type=Path, dest="runtime_bindings_path")
    parser.add_argument("--train-package-root", required=True, type=Path)
    parser.add_argument("--requests-dir", required=True, type=Path)
    parser.add_argument("--rankings-dir", required=True, type=Path)
    parser.add_argument("--return-receipts-dir", required=True, type=Path)
    parser.add_argument("--aggregate-output-dir", required=True, type=Path)
    parser.add_argument("--safe-return-receipt", required=True, type=Path, dest="safe_return_receipt_path")
    args = parser.parse_args(argv)
    try:
        result = evaluate_a3_owner_batch(**vars(args))
    except (A3OwnerBatchEvaluatorError, A3ThreePrimaryOwnerEvaluatorError, ValueError):
        print('{"status":"FAILED_CLOSED"}')
        return 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
