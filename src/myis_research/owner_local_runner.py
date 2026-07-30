"""Owner-local CPU execution from protected local inputs.

The agent may submit a hash-bound request, but it may not submit a precomputed
aggregate JSON file.  This module is intended to run in the Owner's protected
directory; only the aggregate receipt leaves that boundary.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .kernel.canonical import canonical_sha256, file_sha256
from .kernel.p1 import evaluate_baseline
from .owner_local import OwnerLocalContractError, build_receipt, validate_request


_BUNDLE_FILES = ("documents.json", "queries.json", "qrels.json", "splits.json")


def process(request_path: Path, protected_root: Path, receipt_path: Path) -> Path:
    """Evaluate the local bundle and write one immutable aggregate receipt.

    ``protected_root`` must be a directory.  Passing a JSON file is always
    rejected so an operator cannot accidentally revive the old hand-prepared
    aggregate workflow.
    """

    if protected_root.is_symlink():
        raise OwnerLocalContractError("protected input root must not be a symlink")
    if protected_root.is_file():
        raise OwnerLocalContractError("precomputed aggregate sources are forbidden; pass a protected input directory")
    if not protected_root.is_dir():
        raise OwnerLocalContractError("protected input root must be a directory")
    if receipt_path.exists():
        raise FileExistsError(f"valid receipts are immutable and cannot be overwritten: {receipt_path}")
    request = json.loads(request_path.read_text(encoding="utf-8"))
    validated = validate_request(request)
    bundle = _load_bundle(protected_root)
    arms = bundle.get("arms", ["R0", "R0-W"])
    if not isinstance(arms, list) or any(arm not in {"R0", "R0-W"} for arm in arms):
        raise OwnerLocalContractError("bundle arms must be R0 and/or R0-W")
    if not arms:
        raise OwnerLocalContractError("bundle must request at least one CPU arm")
    aggregate_counts: dict[str, int] = {
        "documents": len(bundle["documents"]),
        "queries": len(bundle["queries"]),
        "train_queries": len(bundle["splits"].get("train", [])),
        "selection_queries": len(bundle["splits"].get("selection", [])),
    }
    aggregate_hashes: dict[str, str] = {
        "bundle": canonical_sha256({name.removesuffix(".json"): bundle[name.removesuffix(".json")] for name in _BUNDLE_FILES}),
        "bundle_documents": file_sha256(protected_root / "documents.json"),
        "bundle_queries": file_sha256(protected_root / "queries.json"),
        "bundle_targets": file_sha256(protected_root / "qrels.json"),
        "bundle_splits": file_sha256(protected_root / "splits.json"),
    }
    query_rows = bundle["queries"]
    qrels = bundle["qrels"]
    for arm in arms:
        subset = _queries_for_split(query_rows, bundle["splits"], "train") + _queries_for_split(query_rows, bundle["splits"], "selection")
        result = evaluate_baseline(
            documents=bundle["documents"],
            queries=subset,
            qrels=qrels,
            arm_id=arm,
            top_k=100,
            window_size=int(bundle.get("window_size", 32)),
        )
        aggregate_hashes[f"{arm.lower()}_metrics"] = canonical_sha256(result["metrics"])
        aggregate_counts[f"{arm.lower()}_evaluated_queries"] = int(result["counts"]["queries"])
    receipt = build_receipt(
        validated,
        aggregate_counts=aggregate_counts,
        aggregate_hashes=aggregate_hashes,
    )
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt_path


def _load_bundle(root: Path) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for name in _BUNDLE_FILES:
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise OwnerLocalContractError(f"protected bundle file is missing or not regular: {name}")
        try:
            values[name.removesuffix(".json")] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise OwnerLocalContractError(f"protected bundle JSON is invalid: {name}") from error
    if not isinstance(values["documents"], list) or not isinstance(values["queries"], list):
        raise OwnerLocalContractError("documents and queries must be arrays")
    if not isinstance(values["qrels"], dict) or not isinstance(values["splits"], dict):
        raise OwnerLocalContractError("qrels and splits must be objects")
    for split, query_ids in values["splits"].items():
        if not isinstance(split, str) or not isinstance(query_ids, list) or any(not isinstance(item, str) for item in query_ids):
            raise OwnerLocalContractError("splits must map names to query-id arrays")
    return values


def _queries_for_split(queries: list[dict[str, Any]], splits: dict[str, list[str]], split: str) -> list[dict[str, Any]]:
    allowed = set(splits.get(split, []))
    return [query for query in queries if str(query.get("query_id")) in allowed]
