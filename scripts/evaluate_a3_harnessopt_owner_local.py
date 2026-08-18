"""Evaluate the frozen A3 HarnessOpt surface without reopening protected data.

The three frozen HarnessOpt batches are compiled into deterministic, label-free
action plans.  When every candidate has the same effective action signature,
the already evaluated fixed all-primary result is an exact aggregate-safe
reference and the adaptive surface can stop with evidence of a flat boundary.
This command never reads qrels, membership, rankings, or per-query outcomes.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any

from myis_research.armindex.a3_three_primary_execution import PRIMARY_ARMS
from myis_research.armindex.a3_three_primary_owner_evaluator import validate_aggregate_result
from myis_research.armindex.harnessopt import validate_harness_batch
from myis_research.armindex.runtime import build_execution_plan, validate_execution_plan
from myis_research.kernel.canonical import canonical_sha256
from myis_research.protection import assert_aggregate_only


_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_EXPECTED_BATCHES = ("harness-batch-1.json", "harness-batch-2.json", "harness-batch-3.json")
_FIXED_REFERENCE = "fixed-all-primary-rrf60"


class A3HarnessOptOwnerEvaluationError(ValueError):
    """Raised when a HarnessOpt aggregate evidence boundary is unsafe."""


def evaluate_harnessopt_evidence(
    runtime_bindings: Mapping[str, Any],
    harness_batches: Sequence[Mapping[str, Any]],
    fixed_result: Mapping[str, Any],
    safe_return: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and summarize three complete, label-free HarnessOpt batches."""

    bindings = _validate_runtime_bindings(runtime_bindings)
    if len(harness_batches) != 3:
        raise A3HarnessOptOwnerEvaluationError("A3 Extended requires exactly three complete batches")
    batches = []
    for expected_iteration, value in enumerate(harness_batches, start=1):
        try:
            batch = validate_harness_batch(value)
        except ValueError as error:
            raise A3HarnessOptOwnerEvaluationError("HarnessOpt batch validation failed") from error
        if batch["iteration"] != expected_iteration:
            raise A3HarnessOptOwnerEvaluationError("HarnessOpt iterations must be contiguous")
        if batch["frozen_bindings_sha256"] != bindings["runtime_bindings_sha256"]:
            raise A3HarnessOptOwnerEvaluationError("HarnessOpt batch changed frozen runtime bindings")
        batches.append(batch)

    fixed = validate_aggregate_result(fixed_result)
    if fixed["operation_id"] != _FIXED_REFERENCE:
        raise A3HarnessOptOwnerEvaluationError("HarnessOpt reference must be the fixed all-primary result")
    if not isinstance(safe_return, Mapping):
        raise A3HarnessOptOwnerEvaluationError("safe-return receipt is malformed")
    references = safe_return.get("aggregate_result_receipt_sha256s")
    if not isinstance(references, Mapping) or references.get(_FIXED_REFERENCE) != fixed["receipt_sha256"]:
        raise A3HarnessOptOwnerEvaluationError("fixed all-primary result is not bound by safe return")

    candidates: list[dict[str, Any]] = []
    signatures: set[str] = set()
    for batch in batches:
        for candidate in batch["candidates"]:
            try:
                plan = validate_execution_plan(
                    build_execution_plan(candidate["configuration"], runtime_signals={})
                )
            except ValueError as error:
                raise A3HarnessOptOwnerEvaluationError("HarnessOpt action plan failed validation") from error
            signature = _action_signature(plan["actions"])
            signatures.add(signature)
            candidates.append(
                {
                    "batch_id": batch["batch_id"],
                    "iteration": batch["iteration"],
                    "candidate_id": candidate["candidate_id"],
                    "role": candidate["role"],
                    "configuration_sha256": candidate["configuration"]["config_sha256"],
                    "plan_sha256": plan["plan_sha256"],
                    "action_signature_sha256": signature,
                    "reference_operation_id": _FIXED_REFERENCE,
                    "metrics": deepcopy(fixed["metrics"]),
                    "latency": deepcopy(fixed["latency"]),
                    "coverage": deepcopy(fixed["coverage"]),
                    "status": "PASS_A3_HARNESSOPT_LABEL_FREE_REPLAY",
                }
            )
    if len(candidates) != 12:
        raise A3HarnessOptOwnerEvaluationError("HarnessOpt candidate coverage is incomplete")
    flat = len(signatures) == 1
    body: dict[str, Any] = {
        "schema_version": "myis.armindex-a3-three-primary-harnessopt-owner-evaluation.v1",
        "status": "PASS_A3_HARNESSOPT_FLAT_SURFACE" if flat else "PASS_A3_HARNESSOPT_DISTINCT_SURFACE",
        "runtime_bindings_sha256": bindings["runtime_bindings_sha256"],
        "harness_batch_sha256s": [batch["batch_sha256"] for batch in batches],
        "complete_batch_count": len(batches),
        "candidate_count": len(candidates),
        "unique_action_signature_count": len(signatures),
        "stop_reason": "STOP_WITH_EVIDENCE_FLAT_HARNESSOPT_SURFACE" if flat else "HARNESSOPT_SURFACE_REQUIRES_RESULT_COMPARISON",
        "fixed_reference_operation_id": _FIXED_REFERENCE,
        "fixed_reference_result_sha256": fixed["receipt_sha256"],
        "candidates": candidates,
        "protected_payload_included": False,
        "per_query_outcomes_included": False,
    }
    assert_aggregate_only(body)
    return {**body, "evaluation_sha256": canonical_sha256(body)}


def _action_signature(actions: Sequence[Mapping[str, Any]]) -> str:
    normalized = []
    for action in actions:
        normalized.append(
            {
                "sequence": action["sequence"],
                "action": action["action"],
                "arm_id": action["arm_id"],
                "depth": action["depth"],
                "execution_mode": action["execution_mode"],
                "reason": action["reason"],
            }
        )
    return canonical_sha256(normalized)


def _validate_runtime_bindings(value: Mapping[str, Any]) -> dict[str, Any]:
    bindings = deepcopy(dict(value))
    required = {
        "schema_version",
        "primary_arm_scope",
        "budget_extension_sha256",
        "authority_sha256",
        "manifest_sha256",
        "admission_sha256",
        "winner_bindings",
        "target_adapter_sha256s",
        "package_bindings",
        "runtime_bindings_sha256",
    }
    if set(bindings) != required or bindings["schema_version"] != "myis.armindex-a3-three-primary-runtime-bindings.v1":
        raise A3HarnessOptOwnerEvaluationError("runtime bindings are incomplete")
    if bindings["primary_arm_scope"] != list(PRIMARY_ARMS):
        raise A3HarnessOptOwnerEvaluationError("runtime binding scope is not three-primary")
    _require_hash(bindings["runtime_bindings_sha256"], "runtime_bindings_sha256")
    if bindings["runtime_bindings_sha256"] != canonical_sha256(
        {key: item for key, item in bindings.items() if key != "runtime_bindings_sha256"}
    ):
        raise A3HarnessOptOwnerEvaluationError("runtime binding self-hash drift")
    return bindings


def _require_hash(value: Any, role: str) -> None:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise A3HarnessOptOwnerEvaluationError(f"{role} must be SHA-256")


def _load_json(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A3HarnessOptOwnerEvaluationError(f"{role} is not valid JSON") from error
    if not isinstance(value, dict):
        raise A3HarnessOptOwnerEvaluationError(f"{role} must be a JSON object")
    return value


def _inside(root: Path, path: Path, *, role: str) -> Path:
    root = root.resolve(strict=True)
    resolved = path.resolve(strict=True)
    if resolved == root or root not in resolved.parents:
        raise A3HarnessOptOwnerEvaluationError(f"{role} escapes Owner Store")
    return resolved


def evaluate_from_owner_store(
    *,
    owner_store_root: Path,
    runtime_bindings_path: Path,
    harness_batch_dir: Path,
    fixed_result_path: Path,
    safe_return_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Load only aggregate-safe Owner Store inputs and write one receipt."""

    root = owner_store_root.resolve(strict=True)
    runtime = _load_json(_inside(root, runtime_bindings_path, role="runtime bindings"), role="runtime bindings")
    batch_root = _inside(root, harness_batch_dir, role="HarnessOpt batch directory")
    batches = [_load_json(batch_root / name, role=name) for name in _EXPECTED_BATCHES]
    fixed = _load_json(_inside(root, fixed_result_path, role="fixed aggregate result"), role="fixed aggregate result")
    safe = _load_json(_inside(root, safe_return_path, role="safe return"), role="safe return")
    result = evaluate_harnessopt_evidence(runtime, batches, fixed, safe)
    destination = output_path.resolve()
    if destination.exists() or destination.is_symlink():
        raise A3HarnessOptOwnerEvaluationError("HarnessOpt output already exists")
    _inside(root, destination.parent, role="HarnessOpt output directory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="ascii", newline="\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-store-root", type=Path, required=True)
    parser.add_argument("--runtime-bindings", type=Path, required=True)
    parser.add_argument("--harness-batch-dir", type=Path, required=True)
    parser.add_argument("--fixed-result", type=Path, required=True)
    parser.add_argument("--safe-return", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate_from_owner_store(
        owner_store_root=args.owner_store_root,
        runtime_bindings_path=args.runtime_bindings,
        harness_batch_dir=args.harness_batch_dir,
        fixed_result_path=args.fixed_result,
        safe_return_path=args.safe_return,
        output_path=args.output,
    )
    print(json.dumps({key: result[key] for key in ("status", "candidate_count", "unique_action_signature_count", "evaluation_sha256")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
