"""Owner-local validation and aggregate-safe materialization of A4 HDEV-100.

The A4 production runner must not infer HDEV membership by filtering the
Train-250 query file.  This module validates the frozen split commitment and
the protected linkage between the split, Train-250 package, evaluator
relations, and the source query IDs.  It emits only an aggregate-safe receipt
under an Owner Store; protected membership, qrels, and query-ID maps are never
copied into the resulting handoff.
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any

from ..kernel.canonical import canonical_json, canonical_sha256, file_sha256


SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
HDEV_COUNT = 100
REP_DEV_COUNT = 150
TRAIN_COUNT = 250
# Frozen by scripts/build_a3_train250_owner_package.py.  This derives opaque
# work tokens from source-role IDs without exporting either mapping.
A3_TRAIN250_OPAQUE_SCOPE = "742b38916b194950515ffcb911c9f6b9f44f458b962c376db6a187c8b971a2e6"


class A4HdevMaterializerError(ValueError):
    """Raised when the protected HDEV handoff cannot be verified."""


def materialize_a4_hdev_handoff(
    *,
    membership_path: Path,
    split_receipt_path: Path,
    train_scope_path: Path,
    train_package_receipt_path: Path,
    train_queries_path: Path,
    train_membership_path: Path,
    train_qrels_path: Path,
    evaluator_relations_path: Path,
    output_root: Path,
    owner_store_root: Path,
    attempt_id: str,
    train_query_id_map_path: Path | None = None,
    source_queries_path: Path | None = None,
) -> dict[str, Any]:
    """Validate and record a fresh A4 HDEV handoff.

    All inputs are expected to remain below ``owner_store_root``.  The
    The optional ``train_query_id_map_path`` can provide an additional
    protected linkage.  The normal A3 handoff binds source-role IDs to opaque
    Train-250 work tokens through the frozen package receipt and split
    lineage; the two token namespaces must never be intersected directly.
    """

    if not isinstance(attempt_id, str) or not attempt_id.startswith("a4-"):
        raise A4HdevMaterializerError("A4 attempt identity is invalid")
    store = _directory(owner_store_root, "Owner Store")
    destination = _fresh_output(output_root, store)
    paths = {
        "membership": _regular_file(membership_path, "protected split membership"),
        "split_receipt": _regular_file(split_receipt_path, "split receipt"),
        "train_scope": _regular_file(train_scope_path, "Train-250 scope"),
        "train_receipt": _regular_file(train_package_receipt_path, "Train-250 package receipt"),
        "train_queries": _regular_file(train_queries_path, "Train-250 queries"),
        "train_membership": _regular_file(train_membership_path, "Train-250 membership"),
        "train_qrels": _regular_file(train_qrels_path, "Train-250 qrels"),
        "relations": _regular_file(evaluator_relations_path, "evaluator relations"),
    }
    if source_queries_path is not None:
        paths["source_queries"] = _regular_file(source_queries_path, "source query Arrow")
    if train_query_id_map_path is not None:
        paths["query_id_map"] = _regular_file(train_query_id_map_path, "protected query-ID map")
    membership = _read_object(paths["membership"], "protected split membership")
    split_receipt = _read_object(paths["split_receipt"], "split receipt")
    scope = _read_object(paths["train_scope"], "Train-250 scope")
    package = _read_object(paths["train_receipt"], "Train-250 package receipt")
    try:
        hdev, rep, strata = _validate_membership(membership)
        _validate_split_receipt(split_receipt, membership, hdev, rep, strata, paths["split_receipt"])
        query_rows = _read_jsonl(paths["train_queries"], "Train-250 queries", {"work_token", "text"})
        membership_rows = _read_jsonl(paths["train_membership"], "Train-250 membership", {"eligible_out", "work_token"})
        qrels_rows = _read_jsonl(paths["train_qrels"], "Train-250 qrels", {"relevance", "work_token"})
        train_tokens = _validate_train_rows(query_rows, membership_rows, qrels_rows, hdev, rep)
        mapped_ids: set[str] | None = None
        if "query_id_map" in paths:
            query_id_map = _read_jsonl(paths["query_id_map"], "protected query-ID map", {"query_id", "work_token"})
            mapped_ids = _validate_query_id_map(query_id_map, train_tokens)
        _validate_train_scope(scope, paths["train_scope"], paths["train_queries"])
        _validate_train_package(package, paths, scope, membership, split_receipt, hdev, rep)
        relation_summary = _validate_relations(paths["relations"], hdev, mapped_ids)
        _validate_source_hashes(paths, membership, package)
        hdev_query_rows = _hdev_query_rows(query_rows, hdev)
        destination.mkdir(parents=True, exist_ok=False)
        protected_queries = destination / "protected" / "hdev-queries.jsonl"
        protected_queries.parent.mkdir()
        _atomic_jsonl(protected_queries, hdev_query_rows)
        body = {
            "schema_version": "myis.armindex-a4-hdev-handoff-receipt.v1",
            "status": "PASS_A4_HDEV_HANDOFF",
            "attempt_id": attempt_id,
            "scope": "HARNESS-DEV",
            "hdev_query_count": HDEV_COUNT,
            "train_query_count": TRAIN_COUNT,
            "rep_dev_query_count": REP_DEV_COUNT,
            "hdev_membership_sha256": membership["harness_dev_membership_sha256"],
            "protected_membership_file_sha256": file_sha256(paths["membership"]),
            "split_receipt_sha256": file_sha256(paths["split_receipt"]),
            "train_scope_sha256": file_sha256(paths["train_scope"]),
            "train_package_receipt_sha256": file_sha256(paths["train_receipt"]),
            "train_queries_sha256": file_sha256(paths["train_queries"]),
            "train_membership_sha256": file_sha256(paths["train_membership"]),
            "train_qrels_sha256": file_sha256(paths["train_qrels"]),
            "source_queries_arrow_sha256": membership["source_hashes"]["queries_arrow_sha256"],
            "evaluator_relations_sha256": file_sha256(paths["relations"]),
            "seed": membership["seed"],
            "algorithm_id": membership["algorithm_id"],
            "algorithm_source_sha256": membership["algorithm_source_sha256"],
            "source_hashes": dict(membership["source_hashes"]),
            "strata_count": len(strata),
            "strata_commitment_sha256": canonical_sha256(strata),
            "linkage": {
                "hdev_subset_of_train250": True,
                "qrels_membership_query_tokens_equal": True,
                "evaluator_covers_hdev": True,
                "query_id_map_complete": mapped_ids is not None,
            },
            "owner_local_protected_artifacts": [{
                "relative_path": "protected/hdev-queries.jsonl",
                "sha256": file_sha256(protected_queries),
                "query_count": HDEV_COUNT,
                "remote_stage_eligibility": "ALLOWLIST_REQUIRED",
            }],
            "protected_payload_included": False,
            "selection_accesses": 0,
            "final_accesses": 0,
            "evaluator_relation_query_count": relation_summary["unique_query_count"],
            "evaluator_relation_row_count": relation_summary["row_count"],
        }
        receipt = {**body, "receipt_sha256": canonical_sha256(body)}
        _atomic_json(destination / "A4_HDEV_HANDOFF_RECEIPT.json", receipt)
        _atomic_json(destination / "A4_HDEV_SCOPE.json", {
            "schema_version": "myis.armindex-a4-hdev-scope.v1",
            "scope": "HARNESS-DEV",
            "query_count": HDEV_COUNT,
            "hdev_membership_sha256": membership["harness_dev_membership_sha256"],
            "receipt_sha256": receipt["receipt_sha256"],
            "protected_payload_included": False,
        })
        return receipt
    except Exception:
        if destination.exists():
            shutil.rmtree(destination, ignore_errors=True)
        raise


def validate_a4_hdev_handoff(root: Path, *, expected_attempt_id: str) -> dict[str, Any]:
    """Validate only aggregate-safe files in a materialized handoff."""

    package = _directory(root, "A4 HDEV handoff")
    receipt = _read_object(package / "A4_HDEV_HANDOFF_RECEIPT.json", "A4 HDEV receipt")
    if receipt.get("status") != "PASS_A4_HDEV_HANDOFF" or receipt.get("attempt_id") != expected_attempt_id:
        raise A4HdevMaterializerError("A4 HDEV receipt identity is invalid")
    _self_hash(receipt, "receipt_sha256", "A4 HDEV receipt")
    scope = _read_object(package / "A4_HDEV_SCOPE.json", "A4 HDEV scope")
    if scope.get("scope") != "HARNESS-DEV" or scope.get("query_count") != HDEV_COUNT:
        raise A4HdevMaterializerError("A4 HDEV scope is invalid")
    if scope.get("receipt_sha256") != receipt["receipt_sha256"]:
        raise A4HdevMaterializerError("A4 HDEV scope binding drift")
    artifacts = receipt.get("owner_local_protected_artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 1 or not isinstance(artifacts[0], Mapping):
        raise A4HdevMaterializerError("A4 HDEV protected package declaration is invalid")
    artifact = artifacts[0]
    relative = artifact.get("relative_path")
    if not isinstance(relative, str) or Path(relative).is_absolute():
        raise A4HdevMaterializerError("A4 HDEV protected package path is invalid")
    query_file = (package / relative).resolve(strict=True)
    if not query_file.is_relative_to(package) or query_file.is_symlink() or artifact.get("sha256") != file_sha256(query_file):
        raise A4HdevMaterializerError("A4 HDEV protected package hash drift")
    if len(_read_jsonl(query_file, "A4 HDEV protected query package", {"work_token", "text"})) != HDEV_COUNT:
        raise A4HdevMaterializerError("A4 HDEV protected query package coverage is incomplete")
    return receipt


def _validate_membership(value: Mapping[str, Any]) -> tuple[set[str], set[str], list[dict[str, Any]]]:
    if value.get("schema_version") != "myis.armindex-a1.2-rep-harness-protected-membership.v1":
        raise A4HdevMaterializerError("unsupported protected membership schema")
    _self_hash(value, "protected_membership_sha256", "protected membership")
    hdev = _opaque_set(value.get("harness_dev"), HDEV_COUNT, "HDEV membership")
    rep = _opaque_set(value.get("rep_dev"), REP_DEV_COUNT, "REP-DEV membership")
    if hdev & rep:
        raise A4HdevMaterializerError("REP-DEV and HDEV memberships overlap")
    if value.get("harness_dev_membership_sha256") != canonical_sha256(sorted(hdev)):
        raise A4HdevMaterializerError("HDEV membership commitment mismatch")
    if value.get("rep_dev_membership_sha256") != canonical_sha256(sorted(rep)):
        raise A4HdevMaterializerError("REP-DEV membership commitment mismatch")
    if value.get("seed") != 42 or not isinstance(value.get("algorithm_id"), str):
        raise A4HdevMaterializerError("split seed or algorithm binding is invalid")
    if not _sha(value.get("algorithm_source_sha256")):
        raise A4HdevMaterializerError("split algorithm source hash is invalid")
    source_hashes = value.get("source_hashes")
    if not isinstance(source_hashes, Mapping) or set(source_hashes) != {"queries_arrow_sha256", "relations_arrow_sha256"}:
        raise A4HdevMaterializerError("split source hash set is incomplete")
    for field, digest in source_hashes.items():
        if not _sha(digest):
            raise A4HdevMaterializerError(f"split source hash is invalid: {field}")
    strata = value.get("strata")
    if not isinstance(strata, list) or not strata:
        raise A4HdevMaterializerError("split strata are missing")
    _validate_strata(strata, hdev, rep)
    return hdev, rep, _strata_counts(strata)


def _validate_split_receipt(value: Mapping[str, Any], membership: Mapping[str, Any], hdev: set[str], rep: set[str], strata: list[dict[str, Any]], path: Path) -> None:
    if value.get("schema_version") != "myis.armindex-a1.2-rep-harness-split-receipt.v1" or value.get("status") != "PASS":
        raise A4HdevMaterializerError("split receipt is not a passing commitment")
    _self_hash(value, "receipt_sha256", "split receipt")
    for key in ("algorithm_id", "algorithm_source_sha256", "decision_id", "decision_sha256", "parent_split_sha256", "parent_train_membership_sha256", "protected_membership_sha256", "harness_dev_membership_sha256", "rep_dev_membership_sha256", "seed"):
        if value.get(key) != membership.get(key):
            raise A4HdevMaterializerError(f"split receipt binding mismatch: {key}")
    counts = value.get("counts")
    if counts != {"harness_dev": HDEV_COUNT, "parent_train": TRAIN_COUNT, "rep_dev": REP_DEV_COUNT}:
        raise A4HdevMaterializerError("split receipt counts are not 100/150/250")
    if value.get("source_hashes") != membership.get("source_hashes"):
        raise A4HdevMaterializerError("split source hashes drifted")
    receipt_strata = value.get("strata")
    if not isinstance(receipt_strata, list) or strata != _safe_strata_counts(receipt_strata):
        raise A4HdevMaterializerError("split strata counts drifted")
    if file_sha256(path) == "":
        raise A4HdevMaterializerError("split receipt hash is unavailable")


def _validate_strata(strata: list[Any], hdev: set[str], rep: set[str]) -> None:
    seen_hdev: set[str] = set()
    seen_rep: set[str] = set()
    for row in strata:
        if not isinstance(row, Mapping) or not isinstance(row.get("harness_dev"), list) or not isinstance(row.get("rep_dev"), list):
            raise A4HdevMaterializerError("split strata row is malformed")
        hs = set(row["harness_dev"])
        rs = set(row["rep_dev"])
        if len(hs) != len(row["harness_dev"]) or len(rs) != len(row["rep_dev"]):
            raise A4HdevMaterializerError("split strata contain duplicate members")
        if not hs <= hdev or not rs <= rep:
            raise A4HdevMaterializerError("split strata contain out-of-scope members")
        seen_hdev |= hs
        seen_rep |= rs
    if seen_hdev != hdev or seen_rep != rep:
        raise A4HdevMaterializerError("split strata do not cover the committed memberships")


def _strata_counts(strata: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [{"stratum_key": row.get("stratum_key"), "role_set": row.get("role_set"), "harness_dev_count": len(row.get("harness_dev", [])), "rep_dev_count": len(row.get("rep_dev", [])), "parent_count": len(row.get("harness_dev", [])) + len(row.get("rep_dev", []))} for row in strata]


def _safe_strata_counts(strata: list[Any]) -> list[dict[str, Any]]:
    result = []
    for row in strata:
        if not isinstance(row, Mapping):
            raise A4HdevMaterializerError("split receipt strata row is malformed")
        result.append({"stratum_key": row.get("stratum_key"), "role_set": row.get("role_set"), "harness_dev_count": row.get("harness_dev_count"), "rep_dev_count": row.get("rep_dev_count"), "parent_count": row.get("parent_count")})
    return result


def _validate_train_rows(query_rows: list[dict[str, Any]], membership_rows: list[dict[str, Any]], qrels_rows: list[dict[str, Any]], hdev: set[str], rep: set[str]) -> set[str]:
    if len(query_rows) != TRAIN_COUNT or len(membership_rows) != TRAIN_COUNT or len(qrels_rows) != TRAIN_COUNT:
        raise A4HdevMaterializerError("Train-250 query, membership, and qrels coverage is incomplete")
    query_tokens = _unique_tokens(query_rows, "Train-250 query package")
    membership_tokens = _unique_tokens(membership_rows, "Train-250 membership")
    qrel_tokens = _unique_tokens(qrels_rows, "Train-250 qrels")
    if query_tokens != membership_tokens or query_tokens != qrel_tokens:
        raise A4HdevMaterializerError("Train-250 qrels/membership/query linkage is incomplete")
    if any(not isinstance(row["eligible_out"], bool) for row in membership_rows):
        raise A4HdevMaterializerError("Train-250 membership eligibility is malformed")
    if any(not isinstance(row["relevance"], Mapping) for row in qrels_rows):
        raise A4HdevMaterializerError("Train-250 qrels relevance rows are malformed")
    expected_tokens = {_opaque_work_token(source_id) for source_id in (*hdev, *rep)}
    if query_tokens != expected_tokens:
        raise A4HdevMaterializerError("Train-250 opaque tokens do not bind the committed HDEV/REP split")
    return query_tokens


def _opaque_work_token(source_id: str) -> str:
    digest = hashlib.sha256(f"{A3_TRAIN250_OPAQUE_SCOPE}:Q:{source_id}".encode("utf-8")).hexdigest()
    return f"Q-{digest[:32]}"


def _hdev_query_rows(query_rows: list[dict[str, Any]], hdev: set[str]) -> list[dict[str, Any]]:
    hdev_tokens = {_opaque_work_token(source_id) for source_id in hdev}
    rows = [row for row in query_rows if row["work_token"] in hdev_tokens]
    if len(rows) != HDEV_COUNT or {row["work_token"] for row in rows} != hdev_tokens:
        raise A4HdevMaterializerError("HDEV opaque query package is incomplete")
    return sorted(rows, key=lambda row: str(row["work_token"]))


def _validate_query_id_map(rows: list[dict[str, Any]], train_tokens: set[str]) -> set[str]:
    if len(rows) != TRAIN_COUNT:
        raise A4HdevMaterializerError("protected Train-250 query-ID map is incomplete")
    seen_tokens: set[str] = set()
    ids: set[str] = set()
    for row in rows:
        token, query_id = row.get("work_token"), row.get("query_id")
        if not isinstance(token, str) or not token or token in seen_tokens or not isinstance(query_id, str) or not query_id:
            raise A4HdevMaterializerError("protected query-ID map is malformed")
        seen_tokens.add(token)
        ids.add(query_id)
    if seen_tokens != train_tokens or len(ids) != TRAIN_COUNT:
        raise A4HdevMaterializerError("protected query-ID map does not cover Train-250 exactly")
    return ids


def _validate_train_scope(value: Mapping[str, Any], scope_path: Path, query_path: Path) -> None:
    if value.get("schema_version") != "myis.armindex-a3-train-scope.v1" or value.get("scope") != "Train-250" or value.get("query_count") != TRAIN_COUNT:
        raise A4HdevMaterializerError("Train-250 scope is invalid")
    if value.get("queries_sha256") != file_sha256(query_path):
        raise A4HdevMaterializerError("Train-250 query hash drifted")
    if file_sha256(scope_path) == "":
        raise A4HdevMaterializerError("Train-250 scope hash is unavailable")


def _validate_train_package(value: Mapping[str, Any], paths: Mapping[str, Path], scope: Mapping[str, Any], membership: Mapping[str, Any], split_receipt: Mapping[str, Any], hdev: set[str], rep: set[str]) -> None:
    if value.get("schema_version") != "myis.armindex-a3-train250-owner-package-receipt.v1" or value.get("status") != "PASS_A3_TRAIN250_OWNER_PACKAGE":
        raise A4HdevMaterializerError("Train-250 package receipt is invalid")
    _self_hash(value, "receipt_sha256", "Train-250 package receipt")
    for field, path_key in (("queries_sha256", "train_queries"), ("membership_sha256", "train_membership"), ("qrels_sha256", "train_qrels"), ("relations_arrow_sha256", "relations")):
        if value.get(field) != file_sha256(paths[path_key]):
            raise A4HdevMaterializerError(f"Train-250 package hash drifted: {field}")
    if value.get("scope_sha256") != scope.get("split_commitment_sha256") or value.get("query_count") != TRAIN_COUNT or value.get("harness_dev_count") != HDEV_COUNT or value.get("rep_dev_count") != REP_DEV_COUNT:
        raise A4HdevMaterializerError("Train-250 package scope/count binding is invalid")
    if value.get("parent_split_sha256") != membership.get("parent_split_sha256") or value.get("split_receipt_sha256") != split_receipt.get("receipt_sha256"):
        raise A4HdevMaterializerError("Train-250 package split lineage is invalid")
    source_arrow_hashes = value.get("source_arrow_hashes")
    if not isinstance(source_arrow_hashes, Mapping) or not source_arrow_hashes or any(not _sha(digest) for digest in source_arrow_hashes.values()):
        raise A4HdevMaterializerError("Train-250 source Arrow commitments are invalid")
    if value.get("protected_payload_included") is not False:
        raise A4HdevMaterializerError("Train-250 package protected boundary is invalid")
    if len(hdev) != HDEV_COUNT or len(rep) != REP_DEV_COUNT:
        raise A4HdevMaterializerError("Train-250 split counts are invalid")


def _validate_relations(path: Path, hdev: set[str], mapped_ids: set[str] | None) -> dict[str, int]:
    try:
        import pyarrow.ipc as ipc
        table = ipc.open_stream(path).read_all()
    except Exception as error:
        raise A4HdevMaterializerError("evaluator relation Arrow payload is unreadable") from error
    if tuple(table.column_names) != ("query_id", "relevant_id", "relevance_score", "domain_rel"):
        raise A4HdevMaterializerError("evaluator relation schema is invalid")
    query_ids = set(table.column("query_id").to_pylist())
    if not hdev <= query_ids or (mapped_ids is not None and not hdev <= mapped_ids):
        raise A4HdevMaterializerError("evaluator relations do not cover committed HDEV IDs")
    return {"row_count": table.num_rows, "unique_query_count": len(query_ids)}


def _validate_source_hashes(paths: Mapping[str, Path], membership: Mapping[str, Any], package: Mapping[str, Any]) -> None:
    expected = membership["source_hashes"]
    source_arrow_hashes = package.get("source_arrow_hashes")
    if not isinstance(source_arrow_hashes, Mapping) or expected["queries_arrow_sha256"] not in source_arrow_hashes.values():
        raise A4HdevMaterializerError("source query Arrow hash does not match package commitment")
    if expected["relations_arrow_sha256"] != file_sha256(paths["relations"]):
        raise A4HdevMaterializerError("evaluator relation hash does not match split commitment")
    if expected["relations_arrow_sha256"] not in source_arrow_hashes.values():
        raise A4HdevMaterializerError("evaluator relation hash is absent from package commitment")


def _read_jsonl(path: Path, role: str, fields: set[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        for line in lines:
            value = json.loads(line)
            if not isinstance(value, dict) or set(value) != fields:
                raise A4HdevMaterializerError(f"{role} row schema is invalid")
            rows.append(value)
    except A4HdevMaterializerError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise A4HdevMaterializerError(f"{role} is unreadable") from error
    return rows


def _unique_tokens(rows: list[dict[str, Any]], role: str) -> set[str]:
    tokens = [row.get("work_token") for row in rows]
    if any(not isinstance(token, str) or not token for token in tokens) or len(set(tokens)) != len(tokens):
        raise A4HdevMaterializerError(f"{role} has duplicate or invalid work tokens")
    return set(tokens)


def _opaque_set(value: Any, expected: int, role: str) -> set[str]:
    if not isinstance(value, list) or len(value) != expected or any(not isinstance(item, str) or not item for item in value) or len(set(value)) != expected:
        raise A4HdevMaterializerError(f"{role} must contain exactly {expected} unique tokens")
    return set(value)


def _read_object(path: Path, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise A4HdevMaterializerError(f"{role} is unreadable") from error
    if not isinstance(value, dict):
        raise A4HdevMaterializerError(f"{role} must be a JSON object")
    return value


def _self_hash(value: Mapping[str, Any], field: str, role: str) -> None:
    digest = value.get(field)
    if not _sha(digest) or digest != canonical_sha256({key: item for key, item in value.items() if key != field}):
        raise A4HdevMaterializerError(f"{role} self-hash is invalid")


def _sha(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


def _directory(path: Path, role: str) -> Path:
    candidate = Path(path).resolve(strict=True)
    if candidate.is_symlink() or not candidate.is_dir():
        raise A4HdevMaterializerError(f"{role} must be a regular directory")
    return candidate


def _regular_file(path: Path, role: str) -> Path:
    candidate = Path(path).resolve(strict=True)
    if candidate.is_symlink() or not candidate.is_file():
        raise A4HdevMaterializerError(f"{role} must be a regular file")
    return candidate


def _fresh_output(path: Path, store: Path) -> Path:
    candidate = Path(path).resolve()
    if not candidate.parent.is_relative_to(store):
        raise A4HdevMaterializerError("A4 handoff output must remain under Owner Store")
    if candidate.exists() or candidate.is_symlink():
        raise A4HdevMaterializerError("A4 handoff output must be fresh")
    return candidate


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(canonical_json(value) + "\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _atomic_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        for row in rows:
            handle.write(canonical_json(row) + "\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


__all__ = ["A4HdevMaterializerError", "materialize_a4_hdev_handoff", "validate_a4_hdev_handoff"]
