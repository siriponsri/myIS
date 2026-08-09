"""Materialize A1.2 v15 protected compiler inputs inside ``MYIS_STORE``.

The materializer reads the pinned DAPFAM cache and the already-frozen
REP-DEV/HARNESS-DEV membership.  It writes only Owner-local payloads and emits
an aggregate-safe summary.  No retrieval result is computed or inspected.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..dapfam_p1 import iter_arrow_rows, resolve_cache
from ..kernel.canonical import canonical_sha256, file_sha256
from .a1_2_p02_first_claim_v1 import first_claim_segment
from .scientific_common_programs_v11 import PublicationRecord, _family_text

INTEGRATION_PATH = Path("control/armindex/a1.2/protected-compiler-integration.v15.json")
V14_PATH = Path("control/armindex/a1.2/dense-overflow-adapter-repair.v14.json")
INVENTORY_PATH = Path("outputs/audits/armindex/a1.2-dense-overflow-inventory-20260808.json")
COMPOSITION_PATH = Path("outputs/audits/armindex/a1.2-dense-overflow-composition-20260808.json")
P02_PATH = Path("control/armindex/a1.2/p02-first-claim-repair.v1.json")
SPLIT_DECISION_PATH = Path("control/armindex/a1.2/rep-harness-split-decision.v1.json")
HANDOFF_REQUEST_PATH = Path("control/owner-local/a1.2-evaluator-handoff-request.v11.json")
TRANSFER_CONTRACT_PATH = Path("control/armindex/a1.2/scientific-transfer-contract.v11.json")
WORKLOAD_SET_PATH = Path("control/armindex/a1.2/workload-manifest-set.scientific-request.v11.json")
V11_REQUEST_PATH = Path("control/armindex/a1.2/scientific-execution-adoption-request.v11.json")
SOURCE_CONTRACT_PATH = Path("control/assets/dapfam-p1-source.v1.json")

PRECOMP_SOURCE_PATHS = (
    "control/armindex/a1.2/common-program-set.v11.json",
    "control/armindex/a1.2/scientific-execution-adoption-request.v11.json",
    "control/armindex/a1.2/scientific-execution-adoption-inputs.v12-r3.json",
    "control/armindex/a1.2/publication-impact-contract.v13.json",
    "control/armindex/a1.2/p02-first-claim-repair.v1.json",
    "control/armindex/a1.2/dense-overflow-adapter-repair.v14.json",
    "control/armindex/a1.2/protected-compiler-integration.v15.json",
    "schemas/armindex/a1.2-dense-overflow-adapter-repair.v14.json",
    "schemas/armindex/a1.2-protected-compiler-integration.v15.json",
    "schemas/armindex/a1.2-owner-local-protected-compilation-input.v15.json",
    "schemas/armindex/a1.2-compiled-program-binding-set.v15.json",
    "schemas/armindex/a1.2-owner-local-protected-compiler-receipt.v15.json",
    "src/myis_research/armindex/a1_2_dense_overflow_adapter_v1.py",
    "src/myis_research/armindex/a1_2_dense_overflow_composition_audit_v1.py",
    "src/myis_research/armindex/a1_2_dense_overflow_contract_v14.py",
    "src/myis_research/armindex/a1_2_dense_overflow_inventory_v1.py",
    "src/myis_research/armindex/a1_2_owner_local_protected_compiler_v15.py",
    "src/myis_research/armindex/a1_2_owner_local_protected_materializer_v15.py",
    "src/myis_research/armindex/a1_2_p02_first_claim_v1.py",
    "outputs/audits/armindex/a1.2-dense-overflow-composition-20260808.json",
    "outputs/audits/armindex/a1.2-dense-overflow-inventory-20260808.json",
)


class ProtectedMaterializerV15Error(ValueError):
    """Fail-closed materialization error without protected payload details."""


def _read_json(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProtectedMaterializerV15Error(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise ProtectedMaterializerV15Error(f"{role} must be a JSON object")
    return value


def _json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _self_hash(value: Mapping[str, Any], field: str) -> str:
    return canonical_sha256({key: item for key, item in value.items() if key != field})


def _relative(value: str, *, role: str) -> Path:
    path = Path(value)
    if path.is_absolute() or not value.strip() or ".." in path.parts:
        raise ProtectedMaterializerV15Error(f"{role} must be a safe relative path")
    return path


def _store(root: Path) -> Path:
    raw = os.environ.get("MYIS_STORE")
    if not raw:
        raise ProtectedMaterializerV15Error("MYIS_STORE is required")
    path = Path(raw).resolve(strict=True)
    if path.is_symlink() or not path.is_dir() or path.is_relative_to(root):
        raise ProtectedMaterializerV15Error("MYIS_STORE must be a safe external directory")
    return path


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or path.parent.is_symlink():
        raise ProtectedMaterializerV15Error("protected output target is unsafe")
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise ProtectedMaterializerV15Error("existing protected output differs")
        return
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    _atomic_text(path, _json(value))


def _atomic_lines(path: Path, lines: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            for line in lines:
                handle.write(str(line))
                handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            if path.is_symlink() or file_sha256(path) != file_sha256(temporary):
                raise ProtectedMaterializerV15Error("existing protected payload differs")
            return
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _copy_immutable(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or target.parent.is_symlink():
        raise ProtectedMaterializerV15Error("protected evaluator target is unsafe")
    if target.exists():
        if file_sha256(target) != file_sha256(source):
            raise ProtectedMaterializerV15Error("existing protected evaluator payload differs")
        return
    descriptor, name = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.", suffix=".tmp")
    os.close(descriptor)
    temporary = Path(name)
    try:
        with source.open("rb") as reader, temporary.open("wb") as writer:
            shutil.copyfileobj(reader, writer, length=1024 * 1024)
            writer.flush()
            os.fsync(writer.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="ascii", check=False)
    if result.returncode != 0:
        raise ProtectedMaterializerV15Error("Git source-anchor query failed")
    return result.stdout.strip()


def _membership(path: Path) -> dict[str, Any]:
    value = _read_json(path.resolve(strict=True), role="protected REP/HARNESS membership")
    if value.get("schema_version") != "myis.armindex-a1.2-rep-harness-protected-membership.v1" or not isinstance(value.get("rep_dev"), list) or not isinstance(value.get("harness_dev"), list) or len(value["rep_dev"]) != 150 or len(value["harness_dev"]) != 100 or len(set(value["rep_dev"] + value["harness_dev"])) != 250 or value.get("protected_membership_sha256") != _self_hash(value, "protected_membership_sha256"):
        raise ProtectedMaterializerV15Error("protected REP/HARNESS membership is invalid")
    return value


def _opaque(prefix: str, scope: str, value: str) -> str:
    return f"{prefix}-{hashlib.sha256(f'{scope}:{prefix}:{value}'.encode()).hexdigest()[:32]}"


def _query_text(row: Mapping[str, Any], *, token: str) -> str:
    record = PublicationRecord(family_token="F-" + token[2:], publication_token="P-" + token[2:], publication_ordinal=0, title_en=row.get("title_en"), abstract_en=row.get("abstract_en"), claims_text=row.get("claims_text"), claims=())
    return _family_text((record,), ("title_en", "abstract_en", "claims_text"))


def _build_payloads(root: Path, cache_root: Path, membership: Mapping[str, Any], output: Path, *, scope: str) -> dict[str, Any]:
    layout = resolve_cache(cache_root, root)
    corpus_paths = tuple(path for path in layout.files["corpus"] if path.suffix == ".arrow")
    query_paths = tuple(path for path in layout.files["queries"] if path.suffix == ".arrow")
    relation_paths = tuple(path for path in layout.files["relations"] if path.suffix == ".arrow")
    if len(relation_paths) != 1:
        raise ProtectedMaterializerV15Error("protected evaluator requires exactly one frozen relation Arrow payload")
    database_path = output / ".materializer-v15.sqlite3"
    if database_path.exists():
        database_path.unlink()
    database = sqlite3.connect(database_path)
    rep_ids = {str(value) for value in membership["rep_dev"]}
    observed_queries: set[str] = set()
    try:
        database.execute("CREATE TABLE corpus (family_token TEXT PRIMARY KEY, payload TEXT NOT NULL, source_id TEXT NOT NULL)")
        database.execute("CREATE TABLE queries (work_token TEXT PRIMARY KEY, payload TEXT NOT NULL, source_id TEXT NOT NULL)")
        for row in iter_arrow_rows(corpus_paths, ("relevant_id", "title_en", "abstract_en", "claims_text")):
            source_id = row.get("relevant_id")
            if not isinstance(source_id, str) or not source_id:
                raise ProtectedMaterializerV15Error("corpus source identity is invalid")
            first_claim_segment(row.get("claims_text"))
            family_token = _opaque("F", scope, source_id)
            publication_token = _opaque("P", scope, source_id)
            payload = {"family_token": family_token, "publication_token": publication_token, "publication_ordinal": 0, "title_en": row.get("title_en"), "abstract_en": row.get("abstract_en"), "claims_text": row.get("claims_text"), "claims": []}
            try:
                database.execute("INSERT INTO corpus VALUES (?,?,?)", (family_token, json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")), source_id))
            except sqlite3.IntegrityError as error:
                raise ProtectedMaterializerV15Error("corpus opaque identity is duplicated") from error
        for row in iter_arrow_rows(query_paths, ("query_id", "title_en", "abstract_en", "claims_text")):
            source_id = row.get("query_id")
            if not isinstance(source_id, str) or source_id not in rep_ids:
                continue
            if source_id in observed_queries:
                raise ProtectedMaterializerV15Error("REP-DEV source identity is duplicated")
            observed_queries.add(source_id)
            first_claim_segment(row.get("claims_text"))
            token = _opaque("Q", scope, source_id)
            payload = {"work_token": token, "text": _query_text(row, token=token)}
            database.execute("INSERT INTO queries VALUES (?,?,?)", (token, json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")), source_id))
        database.commit()
        corpus_count = int(database.execute("SELECT COUNT(*) FROM corpus").fetchone()[0])
        query_count = int(database.execute("SELECT COUNT(*) FROM queries").fetchone()[0])
        if corpus_count != int(layout.contract["configs"]["corpus"]["rows"]) or query_count != 150 or observed_queries != rep_ids:
            raise ProtectedMaterializerV15Error("protected corpus or REP-DEV coverage is incomplete")
        corpus_target, query_target, map_target = output / "inputs/corpus.jsonl", output / "inputs/queries.jsonl", output / "inputs/ephemeral-token-map.jsonl"
        _atomic_lines(corpus_target, (row[0] for row in database.execute("SELECT payload FROM corpus ORDER BY family_token")))
        _atomic_lines(query_target, (row[0] for row in database.execute("SELECT payload FROM queries ORDER BY work_token")))

        def map_lines() -> Any:
            for table, role in (("corpus", "corpus_family"), ("queries", "rep_dev_query")):
                statement = "SELECT family_token, source_id FROM corpus ORDER BY family_token" if table == "corpus" else "SELECT work_token, source_id FROM queries ORDER BY work_token"
                for opaque_token, source_id in database.execute(statement):
                    yield json.dumps({"source_id": source_id, "opaque_token": opaque_token, "role": role}, ensure_ascii=True, sort_keys=True, separators=(",", ":"))

        _atomic_lines(map_target, map_lines())
    finally:
        database.close()
        database_path.unlink(missing_ok=True)
    evaluator_target = output / "inputs/evaluator-relations.arrow"
    _copy_immutable(relation_paths[0], evaluator_target)
    return {"layout": layout, "corpus": corpus_target, "queries": query_target, "ephemeral_token_map": map_target, "evaluator": evaluator_target, "corpus_count": corpus_count, "query_count": query_count}


def _repo_binding(root: Path, path: Path, self_field: str) -> dict[str, str]:
    value = _read_json(root / path, role=path.name)
    return {"uri": path.as_posix(), "file_sha256": file_sha256(root / path), "self_sha256": str(value[self_field])}


def materialize(repository_root: Path, *, cache_root: Path, protected_membership_path: Path, output_prefix: str, model_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    store = _store(root)
    output = store / _relative(output_prefix, role="output prefix")
    output.mkdir(parents=True, exist_ok=True)
    if output.is_symlink() or not output.resolve().is_relative_to(store):
        raise ProtectedMaterializerV15Error("protected output prefix is unsafe")
    integration = _read_json(root / INTEGRATION_PATH, role="v15 integration contract")
    membership = _membership(protected_membership_path)
    scope = integration["contract_sha256"]
    payloads = _build_payloads(root, cache_root.resolve(strict=True), membership, output, scope=scope)
    query_map: dict[str, str] = {}
    for row in iter_arrow_rows(tuple(path for path in payloads["layout"].files["queries"] if path.suffix == ".arrow"), ("query_id",)):
        source_id = row.get("query_id")
        if isinstance(source_id, str) and source_id in set(membership["rep_dev"]):
            query_map[source_id] = _opaque("Q", scope, source_id)
    split_body = {"schema_version": "myis.armindex-a1.2-protected-split.v15", "seed": 42, "algorithm_id": membership["algorithm_id"], "algorithm_source_sha256": membership["algorithm_source_sha256"], "parent_train_membership_sha256": membership["parent_train_membership_sha256"], "parent_split_sha256": membership["parent_split_sha256"], "rep_dev_work_tokens": sorted(query_map.values()), "rep_dev_count": 150, "harness_dev_reserved_count": 100, "train_pool_count": 250, "rep_dev_membership_sha256": membership["rep_dev_membership_sha256"], "harness_dev_membership_sha256": membership["harness_dev_membership_sha256"], "grouping_constraints": membership["grouping_constraints"]}
    split = {**split_body, "split_commitment_sha256": canonical_sha256(split_body)}
    split_path = output / "inputs/split-commitment.json"
    _atomic_json(split_path, split)
    source_manifest = [{"uri": path, "sha256": file_sha256(root / path)} for path in PRECOMP_SOURCE_PATHS]
    anchor_body = {"schema_version": "myis.armindex-a1.2-pre-compilation-anchor.v15", "anchor_id": "a1.2-v15-pre-compilation-source-anchor", "status": "PRE_COMPILATION_SOURCE_ANCHOR_NOT_CLEAN_PUSH_CLAIM", "claim_boundary": "Aggregate-safe source anchor for protected compiler preflight. It binds the exact additive integration bytes before the later clean commit and frozen-bundle cross-validation; it does not claim a clean or pushed tree and authorizes no provider, launch, retrieval, or scientific result.", "base_git_commit": _git(root, "rev-parse", "HEAD"), "base_git_tree": _git(root, "rev-parse", "HEAD^{tree}"), "source_manifest": source_manifest, "source_manifest_sha256": canonical_sha256(source_manifest), "worktree_clean_claim": False, "pushed_claim": False, "authorization": integration["authorization"], "counters": {"measured_runs": 0, "selection_accesses": 0, "final_accesses": 0, "charged_usd": 0}}
    anchor = {**anchor_body, "anchor_sha256": canonical_sha256(anchor_body)}
    anchor_path = output / "receipts/A1_2_PRE_COMPILATION_ANCHOR_V15.json"
    _atomic_json(anchor_path, anchor)
    hashes = {"corpus": file_sha256(payloads["corpus"]), "queries": file_sha256(payloads["queries"]), "split": file_sha256(split_path), "evaluator": file_sha256(payloads["evaluator"]), "ephemeral_token_map": file_sha256(payloads["ephemeral_token_map"])}
    handoff_request = _read_json(root / HANDOFF_REQUEST_PATH, role="handoff request")
    handoff_body = {"handoff_receipt_id": "a1.2-v15-protected-handoff", "source_contract_sha256": handoff_request["source_contract"]["file_sha256"], "corpus_bundle_sha256": hashes["corpus"], "query_bundle_sha256": hashes["queries"], "split_commitment_sha256": hashes["split"], "evaluator_sha256": hashes["evaluator"], "ephemeral_token_map_sha256": hashes["ephemeral_token_map"], "corpus_count": payloads["corpus_count"], "query_count": 150, "reserved_harness_dev_count": 100, "train_pool_count": 250, "return_root_free_bytes": shutil.disk_usage(output).free}
    handoff = {**handoff_body, "receipt_sha256": canonical_sha256(handoff_body)}
    handoff_path = output / "receipts/A1_2_PROTECTED_HANDOFF_RECEIPT_V15.json"
    _atomic_json(handoff_path, handoff)
    request = _read_json(root / V11_REQUEST_PATH, role="v11 request")
    transfer_contract = _read_json(root / TRANSFER_CONTRACT_PATH, role="transfer contract")
    workload_set = _read_json(root / WORKLOAD_SET_PATH, role="workload set")
    transfer_body = {"transfer_id": "a1.2-v15-protected-scientific-transfer", "request_sha256": request["request_sha256"], "adoption_receipt_sha256": anchor["anchor_sha256"], "dataset_revision": handoff_request["source_contract"]["dataset_revision"], "split_commitment_sha256": hashes["split"], "evaluator_sha256": hashes["evaluator"], "corpus_bundle_sha256": hashes["corpus"], "corpus_bundle_bytes": payloads["corpus"].stat().st_size, "corpus_family_count": payloads["corpus_count"], "query_bundle_sha256": hashes["queries"], "query_bundle_bytes": payloads["queries"].stat().st_size, "rep_dev_query_count": 150, "harness_dev_reserved_count": 100, "opaque_token_scheme_sha256": canonical_sha256(transfer_contract["opaque_token_contract"]), "ephemeral_token_map_sha256": hashes["ephemeral_token_map"], "workload_manifest_set_sha256": workload_set["manifest_set_sha256"], "expected_result_rows_per_program": 150}
    transfer = {**transfer_body, "manifest_sha256": canonical_sha256(transfer_body)}
    transfer_path = output / "receipts/A1_2_PROTECTED_SCIENTIFIC_TRANSFER_MANIFEST_V15.json"
    _atomic_json(transfer_path, transfer)
    relative = lambda path: path.relative_to(store).as_posix()
    artifacts = {"corpus": {"relative_path": relative(payloads["corpus"]), "sha256": hashes["corpus"]}, "queries": {"relative_path": relative(payloads["queries"]), "sha256": hashes["queries"]}, "split": {"relative_path": relative(split_path), "sha256": hashes["split"]}, "evaluator": {"relative_path": relative(payloads["evaluator"]), "sha256": hashes["evaluator"]}, "ephemeral_token_map": {"relative_path": relative(payloads["ephemeral_token_map"]), "sha256": hashes["ephemeral_token_map"]}, "handoff_receipt": {"relative_path": relative(handoff_path), "sha256": file_sha256(handoff_path)}, "protected_transfer_manifest": {"relative_path": relative(transfer_path), "sha256": file_sha256(transfer_path)}}
    models = [{"arm_id": "ARM-01", "model_relative_path": None, "tokenizer_json_relative_path": None, "runtime_manifest_relative_path": None}] + [{"arm_id": arm, "model_relative_path": arm, "tokenizer_json_relative_path": "tokenizer.json", "runtime_manifest_relative_path": "runtime-file-manifest.v4.json"} for arm in ("ARM-02", "ARM-03", "ARM-04", "ARM-05")]
    resolved_models = model_root.resolve(strict=True)
    if resolved_models.is_relative_to(root) or resolved_models.is_symlink():
        raise ProtectedMaterializerV15Error("model root must remain external")
    input_body = {"schema_version": "myis.armindex-a1.2-owner-local-protected-compilation-input.v15", "input_id": "a1.2-v15-owner-local-protected", "claim_boundary": "Owner-local protected compiler input pointers and hashes only. Exact source identifiers, membership, qrels, text, token maps, and evaluator bytes remain below MYIS_STORE and no retrieval, provider, or scientific result is authorized.", "artifacts": artifacts, "models": models, "protected_index_manifest_directory": relative(output / "manifests"), "pre_compilation_anchor": {"relative_path": relative(anchor_path), "sha256": file_sha256(anchor_path)}, "compatibility_audits": {"v14_contract": _repo_binding(root, V14_PATH, "contract_sha256"), "inventory": _repo_binding(root, INVENTORY_PATH, "inventory_sha256"), "composition": _repo_binding(root, COMPOSITION_PATH, "audit_sha256"), "p02_repair": _repo_binding(root, P02_PATH, "contract_sha256"), "split_decision": _repo_binding(root, SPLIT_DECISION_PATH, "decision_sha256")}}
    input_path = output / "receipts/A1_2_PROTECTED_COMPILATION_INPUT_V15.json"
    (output / "manifests").mkdir(exist_ok=True)
    _atomic_json(input_path, input_body)
    return {"status": "PASS", "input_relative_path": relative(input_path), "input_sha256": file_sha256(input_path), "corpus_count": payloads["corpus_count"], "query_count": 150, "handoff_receipt_sha256": file_sha256(handoff_path), "transfer_manifest_sha256": file_sha256(transfer_path), "pre_compilation_anchor_sha256": file_sha256(anchor_path), "protected_boundary": "PASS", "provider_contacted": False, "measured_retrieval": False}


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-owner-local-protected-materializer-v15")
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--protected-membership", type=Path, required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--model-root", type=Path, required=True)
    args = parser.parse_args()
    result = materialize(args.repository_root, cache_root=args.cache_root, protected_membership_path=args.protected_membership, output_prefix=args.output_prefix, model_root=args.model_root)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
