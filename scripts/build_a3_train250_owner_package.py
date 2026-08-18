"""Materialize the hash-bound Train-250 A3 package in an Owner Store.

The package is protected and never written to the repository.  Only the
aggregate-safe receipt printed by this command may be copied to projections.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from myis_research.dapfam_p1 import iter_arrow_rows, resolve_cache
from myis_research.armindex.a1_2_owner_local_protected_materializer_v15 import _query_text
from myis_research.armindex.a2_measured_adapter import frozen_program_for_candidate
from myis_research.kernel.canonical import canonical_sha256, file_sha256


PARENT_SPLIT_SHA256 = "33a1818ff3c00775d43951182fdf769255c8ebfc591de183df4fbfdd3b039dc6"
SPLIT_RECEIPT_SHA256 = "f5d658f43b8d71e0ec34e08fee6eaf0af18d3649ad5609dffdf3dc2629e2f0f3"
SCOPE = "742b38916b194950515ffcb911c9f6b9f44f458b962c376db6a187c8b971a2e6"


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n", encoding="ascii")


def _opaque(prefix: str, source_id: str) -> str:
    return f"{prefix}-{hashlib.sha256(f'{SCOPE}:{prefix}:{source_id}'.encode()).hexdigest()[:32]}"


def _self_hash(value: dict[str, Any], field: str) -> str:
    return canonical_sha256({key: item for key, item in value.items() if key != field})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--parent-split", type=Path, required=True)
    parser.add_argument("--protected-membership", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.repository_root.resolve()
    output = args.output.resolve()
    if output.exists() or output.is_symlink() or output.is_relative_to(root):
        raise SystemExit("output must be a new external Owner-Store directory")

    layout = resolve_cache(args.cache_root.resolve(), root, verify_hashes=True)
    parent = _json(args.parent_split.resolve(strict=True))
    train = [str(value) for value in parent.get("train", [])]
    if parent.get("schema_version") != "myis.protected-split.v1" or parent.get("seed") != 42 or parent.get("algorithm") != "sha256-seed-colon-id-lexical-v1" or parent.get("split_sha256") != PARENT_SPLIT_SHA256 or len(train) != 250 or len(set(train)) != 250:
        raise SystemExit("parent Train-250 commitment invalid")
    membership = _json(args.protected_membership.resolve(strict=True))
    if membership.get("schema_version") != "myis.armindex-a1.2-rep-harness-protected-membership.v1" or membership.get("protected_membership_sha256") != _self_hash(membership, "protected_membership_sha256"):
        raise SystemExit("protected membership self-hash invalid")
    if set(membership.get("rep_dev", [])) | set(membership.get("harness_dev", [])) != set(train) or set(membership.get("rep_dev", [])) & set(membership.get("harness_dev", [])):
        raise SystemExit("protected membership does not cover Train-250")

    query_rows = {str(row["query_id"]): row for row in iter_arrow_rows(tuple(path for path in layout.files["queries"] if path.suffix == ".arrow"), ("query_id", "title_en", "abstract_en", "claims_text"))}
    relation_rows = list(iter_arrow_rows(tuple(path for path in layout.files["relations"] if path.suffix == ".arrow"), ("query_id", "relevant_id", "relevance_score", "domain_rel")))
    if membership.get("parent_split_sha256") != PARENT_SPLIT_SHA256 or membership.get("source_hashes", {}).get("queries_arrow_sha256") != layout.input_hashes["queries_000_sha256"] or membership.get("source_hashes", {}).get("relations_arrow_sha256") != layout.input_hashes["relations_000_sha256"]:
        raise SystemExit("protected membership is not bound to the pinned source contract")
    if set(train) - set(query_rows):
        raise SystemExit("Train-250 query rows are incomplete")

    query_lines: list[str] = []
    token_by_query: dict[str, str] = {}
    for query_id in sorted(train, key=lambda value: _opaque("Q", value)):
        token = _opaque("Q", query_id)
        token_by_query[query_id] = token
        query_lines.append(json.dumps({"work_token": token, "text": _query_text(query_rows[query_id], token=token)}, ensure_ascii=True, sort_keys=True, separators=(",", ":")))

    family_tokens = {str(row["relevant_id"]): _opaque("F", str(row["relevant_id"])) for row in iter_arrow_rows(tuple(path for path in layout.files["corpus"] if path.suffix == ".arrow"), ("relevant_id",))}
    qrels: dict[str, dict[str, int]] = {token_by_query[q]: {} for q in train}
    eligible: dict[str, bool] = {token_by_query[q]: False for q in train}
    for row in relation_rows:
        query_id = str(row["query_id"])
        if query_id not in token_by_query or not isinstance(row["relevance_score"], (int, float)) or row["relevance_score"] <= 0:
            continue
        family = str(row["relevant_id"])
        qrels[token_by_query[query_id]][family_tokens[family]] = 1
        if str(row["domain_rel"]) == "OUT":
            eligible[token_by_query[query_id]] = True
    if any(not values for values in qrels.values()) or not any(eligible.values()):
        raise SystemExit("Train-250 evaluator coverage is incomplete")

    output.mkdir(parents=True)
    inputs = output / "inputs"
    inputs.mkdir()
    winner_ids = {
        "ARM-03": "a2-arm-03-matched-b2-orthogonal",
        "ARM-04": "a2-arm-04-matched-b1-orthogonal",
        "ARM-05": "a2-arm-05-matched-b1-matched-ablation",
    }
    winner_programs = output / "winner-programs"
    winner_programs.mkdir()
    winner_program_hashes: dict[str, str] = {}
    for arm_id, candidate_id in winner_ids.items():
        program = frozen_program_for_candidate(root, candidate_id)
        winner_program_hashes[arm_id] = str(program["program_sha256"])
        _write_json(winner_programs / f"{arm_id}.json", program)
    corpus_source = root.parent / "04_Owner_Stores" / "a1.2-v15-20260809" / "protected" / "inputs" / "corpus.jsonl"
    if not corpus_source.is_file() or file_sha256(corpus_source) != "be553e6d18a87dedd37308de118f7dc39529405de35bbd13f0a91d52ec4e7b4a":
        raise SystemExit("validated opaque corpus handoff is missing or hash-invalid")
    shutil.copyfile(corpus_source, inputs / "corpus.jsonl")
    (inputs / "queries.jsonl").write_text("\n".join(query_lines) + "\n", encoding="ascii")
    (inputs / "qrels.jsonl").write_text("\n".join(json.dumps({"work_token": token, "relevance": qrels[token]}, ensure_ascii=True, sort_keys=True, separators=(",", ":")) for token in sorted(qrels)) + "\n", encoding="ascii")
    (inputs / "membership.jsonl").write_text("\n".join(json.dumps({"work_token": token, "eligible_out": eligible[token]}, ensure_ascii=True, sort_keys=True, separators=(",", ":")) for token in sorted(eligible)) + "\n", encoding="ascii")
    relation_source = next(path for path in layout.files["relations"] if path.suffix == ".arrow")
    (inputs / "evaluator-relations.arrow").write_bytes(relation_source.read_bytes())

    split_body = {
        "schema_version": "myis.armindex-a3-train250-owner-scope.v1",
        "scope": "Train-250",
        "query_count": 250,
        "parent_split_sha256": PARENT_SPLIT_SHA256,
        "split_receipt_sha256": SPLIT_RECEIPT_SHA256,
        "protected_membership_sha256": membership["protected_membership_sha256"],
        "rep_dev_membership_sha256": membership["rep_dev_membership_sha256"],
        "harness_dev_membership_sha256": membership["harness_dev_membership_sha256"],
        "queries_sha256": file_sha256(inputs / "queries.jsonl"),
        "corpus_sha256": file_sha256(inputs / "corpus.jsonl"),
        "qrels_sha256": file_sha256(inputs / "qrels.jsonl"),
        "membership_sha256": file_sha256(inputs / "membership.jsonl"),
        "relations_arrow_sha256": file_sha256(inputs / "evaluator-relations.arrow"),
        "source_arrow_hashes": {key: value for key, value in layout.input_hashes.items()},
        "protected_payload_included": False,
        "provider_contacted": False,
        "remote_execution_started": False,
        "spend_permitted": False,
    }
    scope_body = {
        "schema_version": "myis.armindex-a3-train-scope.v1",
        "scope": "Train-250",
        "split_id": "Train-250",
        "query_count": 250,
        "queries_sha256": split_body["queries_sha256"],
        "corpus_sha256": split_body["corpus_sha256"],
    }
    scope_sha256 = canonical_sha256(scope_body)
    _write_json(output / "train-scope.json", scope_body)
    winner_root = root.parent / "04_Owner_Stores" / "armindex" / "a2" / "a2-goal004-20260816-005" / "three-primary-closeout-001"
    winner_receipts = {
        arm: file_sha256(winner_root / f"arm-{arm[-2:].lower()}-winner.receipt.v1.json")
        for arm in ("ARM-03", "ARM-04", "ARM-05")
    }
    authority = _json(root / "control/armindex/a3/a3-three-primary-preparation-authority.v1.json")
    manifest = _json(root / "control/armindex/a3/a3-three-primary-preparation-manifest.v1.json")
    budget = _json(root / "control/budgets/armindex-budget-extension-a3-three-primary.v1.json")
    binding_body = {
        "schema_version": "myis.armindex-a3-train250-package-bindings.v1",
        "scope": "Train-250",
        "scope_sha256": scope_sha256,
        "split_receipt_sha256": SPLIT_RECEIPT_SHA256,
        "parent_split_sha256": PARENT_SPLIT_SHA256,
        "source_contract_sha256": file_sha256(root / "control/assets/dapfam-p1-source.v1.json"),
        "a3_authority_sha256": authority["authority_sha256"],
        "a3_manifest_sha256": manifest["manifest_sha256"],
        "a3_budget_extension_sha256": budget["budget_extension_sha256"],
        "a2_closeout_receipt_sha256": "e4bc663d7ee09282c334f25945ede247a50b81742a690c214e0f2aa9ffb81d1d",
        "a2_integrity_audit_sha256": "7d31b80d4dab6897f3110ee629ddf8f9d12fd5f0522b0d8ccd175ba892986642",
        "a2_safe_return_sha256": "659982aea768c6d4c057a75c6a50b04026d7c48875d604e06b1563a1b2b09484",
        "winner_receipt_file_sha256": winner_receipts,
        "winner_program_sha256": winner_program_hashes,
        "winner_selection_receipt_sha256": {
            arm: str(authority_receipt)
            for arm, authority_receipt in _json(root / "control/armindex/a3/a3-three-primary-preparation-authority.v1.json")["a2_predecessor_bindings"]["primary_winner_receipt_sha256s"].items()
        },
        "input_hashes": {
            "corpus_sha256": split_body["corpus_sha256"],
            "queries_sha256": split_body["queries_sha256"],
            "qrels_sha256": split_body["qrels_sha256"],
            "membership_sha256": split_body["membership_sha256"],
            "relations_arrow_sha256": split_body["relations_arrow_sha256"],
        },
        "query_count": 250,
        "rep_dev_count": 150,
        "harness_dev_count": 100,
        "protected_payload_included": False,
        "provider_contacted": False,
        "remote_execution_started": False,
        "spend_permitted": False,
    }
    _write_json(output / "package-bindings.json", {**binding_body, "package_bindings_sha256": canonical_sha256(binding_body)})
    receipt_body = {
        "schema_version": "myis.armindex-a3-train250-owner-package-receipt.v1",
        "status": "PASS_A3_TRAIN250_OWNER_PACKAGE",
        "scope": "Train-250",
        "query_count": 250,
        "parent_split_sha256": PARENT_SPLIT_SHA256,
        "split_receipt_sha256": SPLIT_RECEIPT_SHA256,
        "scope_sha256": scope_sha256,
        "queries_sha256": split_body["queries_sha256"],
        "corpus_sha256": split_body["corpus_sha256"],
        "qrels_sha256": split_body["qrels_sha256"],
        "membership_sha256": split_body["membership_sha256"],
        "relations_arrow_sha256": split_body["relations_arrow_sha256"],
        "source_arrow_hashes": split_body["source_arrow_hashes"],
        "rep_dev_count": 150,
        "harness_dev_count": 100,
        "protected_payload_included": False,
        "provider_contacted": False,
        "remote_execution_started": False,
        "spend_permitted": False,
    }
    receipt = {**receipt_body, "receipt_sha256": canonical_sha256(receipt_body)}
    _write_json(output / "A3_TRAIN250_OWNER_PACKAGE_RECEIPT.json", receipt)
    print(json.dumps({"status": receipt["status"], "output": str(output), "scope_sha256": scope_sha256, "receipt_sha256": receipt["receipt_sha256"], "queries_sha256": split_body["queries_sha256"], "qrels_sha256": split_body["qrels_sha256"], "membership_sha256": split_body["membership_sha256"], "relations_arrow_sha256": split_body["relations_arrow_sha256"], "source_arrow_hashes": split_body["source_arrow_hashes"], "query_count": 250, "rep_dev_count": 150, "harness_dev_count": 100}, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
