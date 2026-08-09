"""Owner-local, bounded-memory producer for A1.2 v12 binding evidence.

All corpus and compiled-unit bytes remain below ``MYIS_STORE``.  This module
only writes aggregate-safe receipts outside its protected transaction tree. It
does not load model weights, call a provider, or perform retrieval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import stat
import subprocess
import tempfile
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_bytes, canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a1_2_compiled_bindings_v12 import (
    ARM_IDS,
    PROGRAM_IDS,
    _contract,
    pending_template,
    validate_binding_set,
)
from .bm25s_adapter import tokenize as bm25_tokenize
from .scientific_common_programs_v11 import (
    ScientificCommonProgramError,
    compile_common_program,
)

INPUT_SCHEMA_PATH = Path("schemas/armindex/a1.2-owner-local-protected-compilation-input.v12.json")
HANDOFF_REQUEST_PATH = Path("control/owner-local/a1.2-evaluator-handoff-request.v11.json")
TRANSFER_CONTRACT_PATH = Path("control/armindex/a1.2/scientific-transfer-contract.v11.json")
WORKLOAD_SET_PATH = Path("control/armindex/a1.2/workload-manifest-set.scientific-request.v11.json")
ANCHOR_SCHEMA_PATH = Path("schemas/armindex/a1.2-scientific-execution-pre-adoption-anchor.v12-r3.json")
COMPILER_RECEIPT_SCHEMA_PATH = Path("schemas/armindex/a1.2-owner-local-protected-compiler-receipt.v12-r3.json")
V11_REQUEST_PATH = Path("control/armindex/a1.2/scientific-execution-adoption-request.v11.json")
V11_RECEIPT_PATH = Path("campaigns/armindex-multiretriever-v2/evidence/a1.2-scientific-execution-adoption-request.receipt.v11.json")
V12_CONTRACT_PATH = Path("control/armindex/a1.2/scientific-execution-adoption-inputs.v12.json")
V13_PUBLICATION_PATH = Path("control/armindex/a1.2/publication-impact-contract.v13.json")
V13_DISPOSITION_PATH = Path("control/armindex/a1.2/instance-disposition-policy.v13.json")
_ARTIFACT_KEYS = ("corpus", "queries", "split", "evaluator", "ephemeral_token_map", "handoff_receipt", "protected_transfer_manifest", "pre_adoption_anchor")
_TOKEN_RE = re.compile(r"^Q-[a-f0-9]{32}$")
_HASH_RE = re.compile(r"^[a-f0-9]{64}$")
_SECRET_OR_ABSOLUTE = re.compile(r"(?:bearer\s+|api[_-]?key|private[_-]?key|password|[A-Za-z]:\\|/Users/|/home/|\\\\[^\\]+\\)", re.IGNORECASE)


class ProtectedCompilationV12Error(ValueError):
    """A fail-closed error which never includes protected paths or payloads."""


def _read_json(path: Path, *, role: str) -> dict[str, Any]:
    try:
        metadata = path.lstat()
        if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
            raise OSError("unsafe JSON input")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProtectedCompilationV12Error(f"{role} is missing or invalid JSON") from error
    if not isinstance(value, dict):
        raise ProtectedCompilationV12Error(f"{role} must be a JSON object")
    return value


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    if path.is_symlink():
        raise ProtectedCompilationV12Error("protected output target is unsafe")
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(_json_text(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _schema(root: Path, value: Mapping[str, Any]) -> None:
    schema = _read_json(root / INPUT_SCHEMA_PATH, role="protected compilation input schema")
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda item: list(item.path))
    if errors:
        error = errors[0]
        raise ProtectedCompilationV12Error(
            f"input contract missing or invalid field at {list(error.path)}"
        )


def _schema_file(root: Path, path: Path, value: Mapping[str, Any], *, role: str) -> None:
    errors = sorted(
        Draft202012Validator(_read_json(root / path, role=f"{role} schema")).iter_errors(value),
        key=lambda item: list(item.path),
    )
    if errors:
        raise ProtectedCompilationV12Error(f"{role} has an invalid field at {list(errors[0].path)}")


def _relative_path(value: str, *, role: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not value.strip():
        raise ProtectedCompilationV12Error(f"{role} must be a non-empty safe relative path")
    return path


def _external_directory(root: Path, raw: str | Path, *, role: str) -> Path:
    try:
        path = Path(raw).resolve(strict=True)
    except OSError as error:
        raise ProtectedCompilationV12Error(f"{role} must resolve to an existing directory") from error
    if not path.is_dir() or path.is_symlink() or path.is_relative_to(root.resolve()):
        raise ProtectedCompilationV12Error(f"{role} must be a non-symlink directory outside the repository")
    return path


def _require_store(root: Path) -> Path:
    raw = os.environ.get("MYIS_STORE")
    if not raw:
        raise ProtectedCompilationV12Error("MYIS_STORE is required for Owner-local protected compilation")
    return _external_directory(root, raw, role="MYIS_STORE")


def _store_file(store: Path, relative: str, *, role: str) -> Path:
    path = store / _relative_path(relative, role=role)
    try:
        resolved, metadata = path.resolve(strict=True), path.lstat()
    except OSError as error:
        raise ProtectedCompilationV12Error(f"required {role} is missing") from error
    if not resolved.is_relative_to(store) or path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        raise ProtectedCompilationV12Error(f"required {role} is not a safe regular file")
    return resolved


def _store_directory(store: Path, relative: str, *, role: str) -> Path:
    path = store / _relative_path(relative, role=role)
    try:
        resolved, metadata = path.resolve(strict=True), path.lstat()
    except OSError as error:
        raise ProtectedCompilationV12Error(f"required {role} is missing") from error
    if not resolved.is_relative_to(store) or path.is_symlink() or not stat.S_ISDIR(metadata.st_mode):
        raise ProtectedCompilationV12Error(f"required {role} is not a safe directory")
    return resolved


def _safe_output(store: Path, relative: str, *, role: str) -> Path:
    path = store / _relative_path(relative, role=role)
    try:
        parent = path.parent.resolve(strict=True)
    except OSError as error:
        raise ProtectedCompilationV12Error(f"{role} parent must already exist in MYIS_STORE") from error
    if not parent.is_relative_to(store) or path.parent.is_symlink():
        raise ProtectedCompilationV12Error(f"{role} parent is not a safe MYIS_STORE directory")
    target = parent / path.name
    if target.is_symlink():
        raise ProtectedCompilationV12Error(f"{role} target is unsafe")
    if target.exists():
        try:
            metadata = target.lstat()
        except OSError as error:
            raise ProtectedCompilationV12Error(f"{role} target is unsafe") from error
        if not stat.S_ISREG(metadata.st_mode) or not target.resolve().is_relative_to(store):
            raise ProtectedCompilationV12Error(f"{role} target is unsafe")
    return target


def _verify_artifact(store: Path, artifact: Mapping[str, Any], *, role: str) -> tuple[Path, str]:
    path = _store_file(store, str(artifact["relative_path"]), role=role)
    observed = file_sha256(path)
    if observed != artifact["sha256"]:
        raise ProtectedCompilationV12Error(f"{role} SHA-256 mismatch")
    return path, observed


def _iter_jsonl(path: Path, *, role: str, allow_empty: bool = False) -> Iterator[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            seen = False
            for number, line in enumerate(handle, start=1):
                if not line.strip():
                    raise ProtectedCompilationV12Error(f"{role} contains an empty line")
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ProtectedCompilationV12Error(f"{role} row {number} is not an object")
                seen = True
                yield value
            if not seen and not allow_empty:
                raise ProtectedCompilationV12Error(f"{role} cannot be empty")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProtectedCompilationV12Error(f"{role} is not valid JSONL") from error


def _validate_queries(path: Path) -> set[str]:
    tokens: set[str] = set()
    for row in _iter_jsonl(path, role="query bundle"):
        if set(row) != {"work_token", "text"} or not isinstance(row["text"], str):
            raise ProtectedCompilationV12Error("query bundle rows must contain only opaque work tokens and text")
        token = str(row["work_token"])
        if _TOKEN_RE.fullmatch(token) is None or token in tokens:
            raise ProtectedCompilationV12Error("query bundle opaque work-token domain is invalid")
        tokens.add(token)
    if len(tokens) != 150:
        raise ProtectedCompilationV12Error("query bundle must contain exactly 150 REP-DEV work tokens")
    return tokens


def _validate_split(path: Path, query_tokens: set[str]) -> None:
    split = _read_json(path, role="split commitment")
    required = {"schema_version", "rep_dev_work_tokens", "harness_dev_reserved_count", "train_pool_count"}
    if set(split) != required or split["schema_version"] != "myis.armindex-a1.2-protected-split.v1":
        raise ProtectedCompilationV12Error("split commitment has an unsupported protected schema")
    if not isinstance(split["rep_dev_work_tokens"], list) or set(split["rep_dev_work_tokens"]) != query_tokens or len(query_tokens) != 150:
        raise ProtectedCompilationV12Error("split commitment does not exactly bind the 150 REP-DEV work tokens")
    if split["harness_dev_reserved_count"] != 100 or split["train_pool_count"] != 250:
        raise ProtectedCompilationV12Error("split commitment does not preserve HARNESS-DEV and Train counts")


def _safe_receipt(value: Mapping[str, Any], *, role: str) -> None:
    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise ProtectedCompilationV12Error(f"{role} contains protected payload fields") from error
    if _SECRET_OR_ABSOLUTE.search(json.dumps(value, ensure_ascii=True, sort_keys=True)):
        raise ProtectedCompilationV12Error(f"{role} contains credential-like or absolute-path material")


def _self_hash(value: Mapping[str, Any], field: str) -> str:
    return canonical_sha256({key: item for key, item in value.items() if key != field})


def _validate_handoff_receipt(root: Path, path: Path, hashes: Mapping[str, str], *, corpus_count: int) -> None:
    receipt = _read_json(path, role="handoff receipt")
    _safe_receipt(receipt, role="handoff receipt")
    request = _read_json(root / HANDOFF_REQUEST_PATH, role="handoff request")
    required = set(request["required_owner_local_receipt_fields"])
    if set(receipt) != required:
        raise ProtectedCompilationV12Error("handoff receipt fields do not match the frozen handoff schema")
    source = request["source_contract"]
    source_path = root / _relative_path(str(source["uri"]), role="source contract URI")
    if file_sha256(source_path) != source["file_sha256"]:
        raise ProtectedCompilationV12Error("frozen source contract file hash mismatch")
    if receipt["source_contract_sha256"] != source["file_sha256"] or receipt["receipt_sha256"] != _self_hash(receipt, "receipt_sha256"):
        raise ProtectedCompilationV12Error("handoff receipt source binding or self-hash mismatch")
    expected = {"corpus_bundle_sha256": hashes["corpus"], "query_bundle_sha256": hashes["queries"], "split_commitment_sha256": hashes["split"], "evaluator_sha256": hashes["evaluator"], "ephemeral_token_map_sha256": hashes["ephemeral_token_map"]}
    if any(receipt[key] != value for key, value in expected.items()) or receipt["corpus_count"] != corpus_count or receipt["query_count"] != 150 or receipt["reserved_harness_dev_count"] != 100 or receipt["train_pool_count"] != 250:
        raise ProtectedCompilationV12Error("handoff receipt does not bind the verified protected inputs")


def _validate_transfer_receipt(
    root: Path,
    path: Path,
    hashes: Mapping[str, str],
    *,
    family_count: int,
    corpus_bytes: int,
    query_bytes: int,
    anchor: Mapping[str, Any],
) -> None:
    receipt = _read_json(path, role="protected transfer manifest")
    _safe_receipt(receipt, role="protected transfer manifest")
    contract = _read_json(root / TRANSFER_CONTRACT_PATH, role="transfer contract")
    required = set(contract["owner_local_protected_transfer_manifest"]["required_fields"])
    if set(receipt) != required:
        raise ProtectedCompilationV12Error("protected transfer manifest fields do not match the frozen transfer schema")
    request = _contract(root)["v11_request"]
    handoff = _read_json(root / HANDOFF_REQUEST_PATH, role="handoff request")
    workload_set = _read_json(root / WORKLOAD_SET_PATH, role="workload manifest set")
    expected = {"request_sha256": request["request_sha256"], "corpus_bundle_sha256": hashes["corpus"], "query_bundle_sha256": hashes["queries"], "split_commitment_sha256": hashes["split"], "evaluator_sha256": hashes["evaluator"], "ephemeral_token_map_sha256": hashes["ephemeral_token_map"]}
    if receipt["manifest_sha256"] != _self_hash(receipt, "manifest_sha256") or any(receipt[key] != value for key, value in expected.items()):
        raise ProtectedCompilationV12Error("protected transfer manifest source binding or self-hash mismatch")
    if (
        receipt["dataset_revision"] != handoff["source_contract"]["dataset_revision"]
        or receipt["corpus_bundle_bytes"] != corpus_bytes
        or receipt["query_bundle_bytes"] != query_bytes
        or receipt["workload_manifest_set_sha256"] != workload_set["manifest_set_sha256"]
        or receipt["opaque_token_scheme_sha256"] != canonical_sha256(contract["opaque_token_contract"])
        or receipt["expected_result_rows_per_program"] != 150
        or receipt["adoption_receipt_sha256"] != anchor["anchor_sha256"]
        or _HASH_RE.fullmatch(str(receipt["adoption_receipt_sha256"])) is None
        or receipt["corpus_family_count"] != family_count
        or receipt["rep_dev_query_count"] != 150
        or receipt["harness_dev_reserved_count"] != 100
    ):
        raise ProtectedCompilationV12Error("protected transfer manifest counts do not match the protected input contract")


def _validate_pre_adoption_anchor(root: Path, path: Path) -> dict[str, Any]:
    anchor = _read_json(path, role="pre-adoption anchor")
    _schema_file(root, ANCHOR_SCHEMA_PATH, anchor, role="pre-adoption anchor")
    _safe_receipt(anchor, role="pre-adoption anchor")
    if anchor["anchor_sha256"] != _self_hash(anchor, "anchor_sha256"):
        raise ProtectedCompilationV12Error("pre-adoption anchor self-hash mismatch")
    if anchor["revision_id"] != "a1.2-scientific-execution-adoption-inputs-v12-r3" or anchor["status"] != "PRE_ADOPTION_INPUT_ANCHOR":
        raise ProtectedCompilationV12Error("pre-adoption anchor identity is unsupported")
    bindings = {
        "v11_request": (V11_REQUEST_PATH, "request_sha256"),
        "v11_receipt": (V11_RECEIPT_PATH, "receipt_sha256"),
        "v12_contract": (V12_CONTRACT_PATH, "contract_sha256"),
        "publication_v13": (V13_PUBLICATION_PATH, "contract_sha256"),
    }
    for key, (source_path, self_field) in bindings.items():
        source = _read_json(root / source_path, role=f"{key} source")
        binding = anchor[key]
        if binding["uri"] != source_path.as_posix() or binding["file_sha256"] != file_sha256(root / source_path) or binding["self_sha256"] != source[self_field]:
            raise ProtectedCompilationV12Error("pre-adoption anchor source binding mismatch")
    disposition = _read_json(root / V13_DISPOSITION_PATH, role="instance disposition policy")
    disposition_binding = anchor["instance_disposition_v13"]
    if disposition_binding["file_sha256"] != file_sha256(root / V13_DISPOSITION_PATH) or disposition_binding["policy_id"] != disposition["policy_id"]:
        raise ProtectedCompilationV12Error("pre-adoption anchor disposition binding mismatch")
    if anchor["authorization"] != {"provider_contact_allowed": False, "launch_allowed": False, "adopted_for_execution": False, "measured_retrieval_allowed": False} or anchor["counters"] != {"measured_runs": 0, "selection_accesses": 0, "final_accesses": 0, "charged_usd": 0}:
        raise ProtectedCompilationV12Error("pre-adoption anchor changes execution authority")
    completed = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, encoding="ascii", check=False)
    if completed.returncode != 0 or anchor["execution_bundle"]["git_commit"] != completed.stdout.strip():
        raise ProtectedCompilationV12Error("pre-adoption anchor is not bound to the current Git commit")
    return anchor


def _model_inputs(root: Path, model_root: Path, input_value: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    contract = _contract(root)
    entries = input_value["models"]
    if [item["arm_id"] for item in entries] != list(ARM_IDS):
        raise ProtectedCompilationV12Error("model inputs must list ARM-01 through ARM-05 in order")
    locks = {item["arm_id"]: item for item in contract["model_locks"]}
    resolved: dict[str, dict[str, Any]] = {}
    for entry in entries:
        arm_id, lock = entry["arm_id"], locks[entry["arm_id"]]
        if arm_id == "ARM-01":
            if any(entry[key] is not None for key in entry if key != "arm_id"):
                raise ProtectedCompilationV12Error("ARM-01 must not declare a dense model path")
            resolved[arm_id] = {"contract": lock, "model_directory": None}
            continue
        directory = _external_model_directory(model_root, str(entry["model_relative_path"]), role=f"{arm_id} model directory")
        tokenizer = _external_model_file(directory, str(entry["tokenizer_json_relative_path"]), role=f"{arm_id} tokenizer JSON")
        if file_sha256(tokenizer) != lock["tokenizer_sha256"]:
            raise ProtectedCompilationV12Error(f"{arm_id} tokenizer SHA-256 mismatch")
        manifest_path = _external_model_file(directory, str(entry["runtime_manifest_relative_path"]), role=f"{arm_id} runtime manifest")
        manifest = _read_json(manifest_path, role=f"{arm_id} runtime manifest")
        files = manifest.get("files")
        if manifest.get("arm_id") != arm_id or manifest.get("source_lock_file_sha256") != lock["file_sha256"] or not isinstance(files, list) or not any(isinstance(item, Mapping) and item.get("sha256") == lock["tokenizer_sha256"] for item in files):
            raise ProtectedCompilationV12Error(f"{arm_id} runtime manifest does not bind its frozen model/tokenizer")
        resolved[arm_id] = {"contract": lock, "model_directory": directory}
    return resolved


def _external_model_directory(model_root: Path, relative: str, *, role: str) -> Path:
    candidate = model_root / _relative_path(relative, role=role)
    try:
        resolved, metadata = candidate.resolve(strict=True), candidate.lstat()
    except OSError as error:
        raise ProtectedCompilationV12Error(f"required {role} is missing") from error
    if candidate.is_symlink() or not resolved.is_relative_to(model_root) or not stat.S_ISDIR(metadata.st_mode):
        raise ProtectedCompilationV12Error(f"required {role} is not a safe external model directory")
    return resolved


def _external_model_file(directory: Path, relative: str, *, role: str) -> Path:
    candidate = directory / _relative_path(relative, role=role)
    try:
        resolved, metadata = candidate.resolve(strict=True), candidate.lstat()
    except OSError as error:
        raise ProtectedCompilationV12Error(f"required {role} is missing") from error
    if candidate.is_symlink() or not resolved.is_relative_to(directory) or not stat.S_ISREG(metadata.st_mode):
        raise ProtectedCompilationV12Error(f"required {role} is not a safe external model file")
    return resolved


def _load_dense_tokenizer(directory: Path, *, arm_id: str) -> Any:
    if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("TRANSFORMERS_OFFLINE") != "1":
        raise ProtectedCompilationV12Error("HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1 are required for dense tokenizer validation")
    try:
        from transformers import AutoTokenizer
        return AutoTokenizer.from_pretrained(str(directory), local_files_only=True, trust_remote_code=False, use_fast=True)
    except Exception as error:
        raise ProtectedCompilationV12Error(f"{arm_id} frozen local tokenizer could not load offline") from error


def _token_count(arm_id: str, tokenizer: Any | None, text: str) -> int:
    if arm_id == "ARM-01":
        return len(bm25_tokenize(text))
    if tokenizer is None:
        raise ProtectedCompilationV12Error(f"{arm_id} tokenizer is unavailable")
    try:
        encoded = tokenizer(text, add_special_tokens=True, truncation=False, return_attention_mask=False)
        token_ids = encoded.get("input_ids")
    except Exception as error:
        raise ProtectedCompilationV12Error(f"{arm_id} frozen local tokenizer could not encode input offline") from error
    if not isinstance(token_ids, Sequence) or isinstance(token_ids, (str, bytes)) or not token_ids:
        raise ProtectedCompilationV12Error(f"{arm_id} frozen local tokenizer returned no token IDs")
    return len(token_ids)


def _render_document(arm_id: str, text: str) -> str:
    return f"encode document for different retrieval: {text}" if arm_id == "ARM-03" else text


def _state_path(transaction: Path) -> Path:
    return transaction / "state.json"


def _transaction(index_directory: Path, input_sha256: str) -> Path:
    path = index_directory / f".a1_2_v12_transaction_{input_sha256[:16]}"
    path.mkdir(exist_ok=True)
    if path.is_symlink():
        raise ProtectedCompilationV12Error("protected transaction directory is unsafe")
    return path


def _initial_state(input_sha256: str, contract_sha256: str) -> dict[str, Any]:
    return {"schema_version": "myis.armindex-a1.2-protected-compiler-transaction.v12", "input_sha256": input_sha256, "contract_sha256": contract_sha256, "completed_programs": [], "phase": "spooling"}


def _load_state(transaction: Path, *, input_sha256: str, contract_sha256: str) -> dict[str, Any]:
    path = _state_path(transaction)
    if not path.exists():
        value = _initial_state(input_sha256, contract_sha256)
        _atomic_json(path, value)
        return value
    value = _read_json(path, role="protected transaction state")
    if (
        set(value) != {"schema_version", "input_sha256", "contract_sha256", "completed_programs", "phase"}
        or value.get("schema_version") != "myis.armindex-a1.2-protected-compiler-transaction.v12"
        or value.get("input_sha256") != input_sha256
        or value.get("contract_sha256") != contract_sha256
        or not isinstance(value.get("completed_programs"), list)
        or any(item not in PROGRAM_IDS for item in value["completed_programs"])
        or len(value["completed_programs"]) != len(set(value["completed_programs"]))
        or value.get("phase") not in {"spooling", "rendering", "complete"}
    ):
        raise ProtectedCompilationV12Error("protected transaction does not bind the current immutable inputs")
    return value


def _spool_metadata_path(transaction: Path, program_id: str) -> Path:
    return transaction / f"{program_id}.metadata.json"


def _spool_path(transaction: Path, program_id: str) -> Path:
    return transaction / f"{program_id}.units.jsonl"


def _validated_spool_metadata(
    metadata_path: Path,
    spool: Path,
    *,
    program_id: str,
) -> dict[str, Any]:
    value = _read_json(metadata_path, role="protected spool metadata")
    required = {
        "program_id", "unit_count", "family_count", "covered_family_count",
        "families_without_independent_claim", "spool_sha256",
    }
    if (
        set(value) != required
        or value["program_id"] != program_id
        or any(
            not isinstance(value[field], int) or value[field] < 0
            for field in (
                "unit_count", "family_count", "covered_family_count",
                "families_without_independent_claim",
            )
        )
        or _HASH_RE.fullmatch(str(value["spool_sha256"])) is None
        or file_sha256(spool) != value["spool_sha256"]
    ):
        raise ProtectedCompilationV12Error("protected transaction spool integrity mismatch")
    return value


def _compile_spools(corpus: Path, transaction: Path, state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Read the corpus once and emit each frozen logical program once to disk."""
    complete = set(state["completed_programs"])
    existing: dict[str, dict[str, Any]] = {}
    for program_id in PROGRAM_IDS:
        metadata_path, spool = _spool_metadata_path(transaction, program_id), _spool_path(transaction, program_id)
        if program_id in complete and metadata_path.exists() and spool.exists():
            existing[program_id] = _validated_spool_metadata(
                metadata_path,
                spool,
                program_id=program_id,
            )
        elif program_id in complete:
            raise ProtectedCompilationV12Error("protected transaction spool is incomplete")
    if len(existing) == len(PROGRAM_IDS):
        return existing
    # A partial corpus read must never be mixed with old spools.  The only supported
    # resume point is after the durable five-program spool transaction is complete.
    if complete:
        raise ProtectedCompilationV12Error("protected transaction has an incomplete logical-spool generation")
    temporary_paths: dict[str, Path] = {}
    handles: dict[str, Any] = {}
    for program_id in PROGRAM_IDS:
        descriptor, name = tempfile.mkstemp(
            dir=transaction,
            prefix=f".{program_id}.",
            suffix=".jsonl.tmp",
        )
        temporary_paths[program_id] = Path(name)
        handles[program_id] = os.fdopen(descriptor, "w", encoding="utf-8", newline="")
    counts = {key: {"unit_count": 0, "family_count": 0, "covered_family_count": 0, "families_without_independent_claim": 0} for key in PROGRAM_IDS}
    database = sqlite3.connect(transaction / "publication-uniqueness.sqlite3")
    try:
        # A previous interrupted spool attempt has no durable completion marker.
        # Its uniqueness database is therefore disposable transaction scratch.
        database.execute("DROP TABLE IF EXISTS publications")
        database.execute("CREATE TABLE publications (publication_token TEXT PRIMARY KEY)")
        current_family: str | None = None
        family_rows: list[dict[str, Any]] = []
        previous: tuple[str, int, str] | None = None

        def emit_family(rows: list[dict[str, Any]]) -> None:
            if not rows:
                return
            for program_id in PROGRAM_IDS:
                try:
                    compiled = compile_common_program(program_id, rows)
                except ScientificCommonProgramError as error:
                    raise ProtectedCompilationV12Error("structured corpus cannot satisfy the frozen common-program contract") from error
                summary = counts[program_id]
                summary["family_count"] += compiled.family_count
                summary["covered_family_count"] += compiled.covered_family_count
                summary["families_without_independent_claim"] += compiled.families_without_independent_claim
                for unit in compiled.units:
                    handles[program_id].write(json.dumps(unit.as_dict(), ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n")
                    summary["unit_count"] += 1

        for row in _iter_jsonl(corpus, role="corpus bundle"):
            key = (str(row.get("family_token", "")), int(row.get("publication_ordinal", -1)) if isinstance(row.get("publication_ordinal"), int) else -1, str(row.get("publication_token", "")))
            if previous is not None and key < previous:
                raise ProtectedCompilationV12Error("corpus bundle must be sorted by family, ordinal, and opaque publication token")
            previous = key
            try:
                database.execute("INSERT INTO publications VALUES (?)", (key[2],))
            except sqlite3.IntegrityError as error:
                raise ProtectedCompilationV12Error("corpus bundle has duplicate opaque publication tokens") from error
            if current_family is not None and key[0] != current_family:
                emit_family(family_rows)
                family_rows = []
            current_family = key[0]
            family_rows.append(row)
        emit_family(family_rows)
        database.commit()
    finally:
        database.close()
        for handle in handles.values():
            handle.close()
    metadata: dict[str, dict[str, Any]] = {}
    for program_id in PROGRAM_IDS:
        temporary_paths[program_id].replace(_spool_path(transaction, program_id))
        metadata[program_id] = {"program_id": program_id, **counts[program_id], "spool_sha256": file_sha256(_spool_path(transaction, program_id))}
        _atomic_json(_spool_metadata_path(transaction, program_id), metadata[program_id])
    state["completed_programs"] = list(PROGRAM_IDS)
    state["phase"] = "rendering"
    _atomic_json(_state_path(transaction), state)
    return metadata


def _representation_hash(*, arm_id: str, program_id: str, adapter_sha256: str, spool: Path, tokenizer: Any | None) -> tuple[str, int, int]:
    digest = hashlib.sha256()
    prefix = {"adapter_contract_sha256": adapter_sha256, "arm_id": arm_id, "program_id": program_id}
    digest.update(b'{"adapter_contract_sha256":')
    digest.update(canonical_bytes(prefix["adapter_contract_sha256"]))
    digest.update(b',"arm_id":')
    digest.update(canonical_bytes(prefix["arm_id"]))
    digest.update(b',"program_id":')
    digest.update(canonical_bytes(prefix["program_id"]))
    digest.update(b',"units":[')
    maximum = 0
    unit_count = 0
    first = True
    for unit in _iter_jsonl(spool, role="protected logical spool", allow_empty=True):
        text, unit_id = unit.get("text"), unit.get("unit_id")
        if not isinstance(text, str) or not isinstance(unit_id, str):
            raise ProtectedCompilationV12Error("protected logical spool is malformed")
        rendered = _render_document(arm_id, text)
        token_count = _token_count(arm_id, tokenizer, rendered)
        maximum = max(maximum, token_count)
        unit_count += 1
        record = {"rendered_utf8_sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(), "token_count": token_count, "unit_id": unit_id}
        if not first:
            digest.update(b",")
        digest.update(canonical_bytes(record))
        first = False
    digest.update(b"]}")
    return digest.hexdigest(), maximum, unit_count


def _index_manifest(*, arm_id: str, program_id: str, binding: Mapping[str, Any]) -> dict[str, Any]:
    body = {"schema_version": "myis.armindex-a1.2-protected-index-manifest.v12", "status": "compiled_manifest_only_not_measured_index", "claim_boundary": "Protected local compilation manifest only; no retrieval, embedding, ranking, evaluation, GPU, provider, or measured result is performed.", "arm_id": arm_id, "program_id": program_id, "logical_program_sha256": binding["logical_program_sha256"], "compiled_representation_sha256": binding["compiled_representation_sha256"], "adapter_contract_sha256": binding["adapter_contract_sha256"], "tokenizer_sha256": binding["tokenizer_sha256"], "effective_input_limit": binding["effective_input_limit"], "rendered_input_max_tokens": binding["rendered_input_max_tokens"], "unit_count": binding["unit_count"]}
    return {**body, "index_manifest_sha256": canonical_sha256(body)}


def _write_manifest(directory: Path, manifest: Mapping[str, Any]) -> None:
    path = directory / f"{manifest['arm_id']}--{manifest['program_id']}.json"
    if path.is_symlink():
        raise ProtectedCompilationV12Error("protected index manifest target is unsafe")
    if path.exists() and path.read_text(encoding="utf-8") != _json_text(manifest):
        raise ProtectedCompilationV12Error("protected index manifest already exists with different bytes")
    if not path.exists():
        _atomic_json(path, manifest)


def _ensure_manifests(directory: Path, bindings: Mapping[str, Any]) -> None:
    for binding in bindings["bindings"]:
        manifest = _index_manifest(
            arm_id=str(binding["arm_id"]),
            program_id=str(binding["program_id"]),
            binding=binding,
        )
        if manifest["index_manifest_sha256"] != binding["index_manifest_sha256"]:
            raise ProtectedCompilationV12Error("binding index-manifest hash mismatch")
        _write_manifest(directory, manifest)


def _receipt(binding_set: Mapping[str, Any], hashes: Mapping[str, str]) -> dict[str, Any]:
    body = {"schema_version": "myis.armindex-a1.2-owner-local-protected-compiler-receipt.v12-r3", "status": "PASS", "claim_boundary": "Aggregate-safe Owner-local protected compilation receipt. It records only hashes and counts; it does not authorize provider contact, adoption, launch, retrieval, evaluation, or a scientific result.", "handoff_receipt_sha256": hashes["handoff_receipt"], "protected_transfer_manifest_sha256": hashes["protected_transfer_manifest"], "pre_adoption_anchor_sha256": hashes["pre_adoption_anchor"], "corpus_bundle_sha256": hashes["corpus"], "query_bundle_sha256": hashes["queries"], "split_commitment_sha256": hashes["split"], "evaluator_sha256": hashes["evaluator"], "ephemeral_token_map_sha256": hashes["ephemeral_token_map"], "binding_set_sha256": binding_set["binding_set_sha256"], "binding_count": 25, "coverage_gap_count": 0, "omitted_unit_count": 0, "truncation_count": 0, "overlength_count": 0, "launch_allowed": False, "adopted_for_execution": False, "measured_runs": 0, "charged_usd": 0}
    return {**body, "receipt_sha256": canonical_sha256(body)}


def _prepare(root: Path, input_relative_path: str, model_root: str | Path) -> tuple[Path, Path, dict[str, Any], dict[str, Path], dict[str, str], dict[str, dict[str, Any]], int]:
    store = _require_store(root)
    input_path = _store_file(store, input_relative_path, role="protected compilation input contract")
    input_value = _read_json(input_path, role="protected compilation input contract")
    if _SECRET_OR_ABSOLUTE.search(json.dumps(input_value, ensure_ascii=True, sort_keys=True)):
        raise ProtectedCompilationV12Error("protected compilation input contract contains unsafe path or credential material")
    _schema(root, input_value)
    hashes: dict[str, str] = {}
    paths: dict[str, Path] = {}
    for key in _ARTIFACT_KEYS:
        paths[key], hashes[key] = _verify_artifact(store, input_value[key], role=key.replace("_", " "))
    query_tokens = _validate_queries(paths["queries"])
    _validate_split(paths["split"], query_tokens)
    corpus_count, family_count = _corpus_counts(paths["corpus"])
    _validate_handoff_receipt(root, paths["handoff_receipt"], hashes, corpus_count=corpus_count)
    anchor = _validate_pre_adoption_anchor(root, paths["pre_adoption_anchor"])
    _validate_transfer_receipt(
        root,
        paths["protected_transfer_manifest"],
        hashes,
        family_count=family_count,
        corpus_bytes=paths["corpus"].stat().st_size,
        query_bytes=paths["queries"].stat().st_size,
        anchor=anchor,
    )
    models = _model_inputs(root, _external_directory(root, model_root, role="model root"), input_value)
    return store, input_path, input_value, paths, hashes, models, corpus_count


def _corpus_counts(path: Path) -> tuple[int, int]:
    """Count protected rows/families with a stream, retaining no corpus rows."""
    count = 0
    previous_family: str | None = None
    family_count = 0
    for row in _iter_jsonl(path, role="corpus bundle"):
        family = row.get("family_token")
        if not isinstance(family, str):
            raise ProtectedCompilationV12Error("corpus bundle lacks an opaque family token")
        count += 1
        if family != previous_family:
            family_count += 1
            previous_family = family
    return count, family_count


def preflight(repository_root: Path, *, input_relative_path: str, model_root: str | Path) -> dict[str, Any]:
    root = repository_root.resolve()
    store, _input, value, _paths, _hashes, _models, _count = _prepare(root, input_relative_path, model_root)
    _store_directory(store, value["protected_index_manifest_directory"], role="protected index-manifest directory")
    return {"status": "READY_FOR_OWNER_LOCAL_PROTECTED_COMPILATION", "expected_bindings": 25, "rep_dev_work_tokens": 150, "launch_allowed": False, "adopted_for_execution": False, "measured_runs": 0, "charged_usd": 0}


def produce(repository_root: Path, *, input_relative_path: str, binding_output_relative_path: str, receipt_output_relative_path: str, model_root: str | Path) -> dict[str, Any]:
    root = repository_root.resolve()
    store, input_path, value, paths, hashes, models, _count = _prepare(root, input_relative_path, model_root)
    index_directory = _store_directory(store, value["protected_index_manifest_directory"], role="protected index-manifest directory")
    binding_output, receipt_output = _safe_output(store, binding_output_relative_path, role="binding receipt output"), _safe_output(store, receipt_output_relative_path, role="compiler receipt output")
    if binding_output.exists() and receipt_output.exists():
        binding, receipt = _read_json(binding_output, role="binding output"), _read_json(receipt_output, role="compiler receipt")
        try:
            validate_binding_set(root, binding)
        except ValueError as error:
            raise ProtectedCompilationV12Error("existing binding output failed immutable validation") from error
        _schema_file(root, COMPILER_RECEIPT_SCHEMA_PATH, receipt, role="protected compiler receipt")
        if receipt != _receipt(binding, hashes):
            raise ProtectedCompilationV12Error("existing compiler receipt does not bind current immutable inputs")
        _ensure_manifests(index_directory, binding)
        return {"status": "PASS", "binding_count": 25, "binding_set_sha256": binding["binding_set_sha256"], "receipt_sha256": receipt["receipt_sha256"], "launch_allowed": False, "adopted_for_execution": False, "measured_runs": 0, "charged_usd": 0}
    contract = _contract(root)
    transaction = _transaction(index_directory, file_sha256(input_path))
    state = _load_state(transaction, input_sha256=file_sha256(input_path), contract_sha256=file_sha256(root / "control/owner-local/a1.2-compiled-program-bindings-contract.v12.json"))
    metadata = _compile_spools(paths["corpus"], transaction, state)
    binding_set = pending_template(root)
    binding_set.update({"binding_set_id": f"a1.2-v12-owner-local-{hashes['corpus'][:16]}", "status": "validated_owner_local_protected_compilation", "claim_boundary": "Aggregate-safe Owner-local protected compilation bindings only. No model weights are loaded, no retrieval/evaluation/provider/GPU work occurs, and no protected corpus/query content, identifiers, membership, qrels, or credentials are exported.", "owner_local_receipts": {"handoff_receipt_sha256": hashes["handoff_receipt"], "protected_transfer_manifest_sha256": hashes["protected_transfer_manifest"], "corpus_bundle_sha256": hashes["corpus"], "query_bundle_sha256": hashes["queries"], "split_commitment_sha256": hashes["split"], "evaluator_sha256": hashes["evaluator"], "ephemeral_token_map_sha256": hashes["ephemeral_token_map"]}})
    bindings: list[dict[str, Any]] = []
    manifests: list[dict[str, Any]] = []
    for arm_id in ARM_IDS:
        lock = models[arm_id]["contract"]
        tokenizer = (
            None
            if arm_id == "ARM-01"
            else _load_dense_tokenizer(models[arm_id]["model_directory"], arm_id=arm_id)
        )
        for program_id in PROGRAM_IDS:
            meta = metadata[program_id]
            representation, rendered_max, observed_unit_count = _representation_hash(arm_id=arm_id, program_id=program_id, adapter_sha256=lock["adapter_contract_sha256"], spool=_spool_path(transaction, program_id), tokenizer=tokenizer)
            if observed_unit_count != meta["unit_count"] or (
                program_id != "P02-CLAIM1" and observed_unit_count == 0
            ):
                raise ProtectedCompilationV12Error("protected logical spool unit-count mismatch")
            limit = rendered_max if lock["effective_input_limit"] is None else lock["effective_input_limit"]
            # P02 has no coverage obligation for a family without an independent claim.
            coverage_gap = meta["family_count"] - meta["covered_family_count"] - (meta["families_without_independent_claim"] if program_id == "P02-CLAIM1" else 0)
            binding = {"binding_id": f"{arm_id}--{program_id}", "arm_id": arm_id, "program_id": program_id, "logical_program_sha256": _program_hash(root, program_id), "compiler_source_manifest_sha256": contract["program_set"]["compiler_source_manifest_sha256"], "model_lock_file_sha256": lock["file_sha256"], "adapter_contract_sha256": lock["adapter_contract_sha256"], "tokenizer_sha256": lock["tokenizer_sha256"], "effective_input_limit": limit, "rendered_input_max_tokens": rendered_max, "compiled_representation_sha256": representation, "unit_count": meta["unit_count"], "coverage_gap_count": coverage_gap, "omitted_unit_count": 0, "truncation_count": 0, "overlength_count": int(rendered_max > limit), "index_manifest_sha256": "0" * 64}
            if any(binding[field] != 0 for field in ("coverage_gap_count", "omitted_unit_count", "truncation_count", "overlength_count")):
                raise ProtectedCompilationV12Error("compiled program has a gap, omission, truncation, or overlength input")
            manifest = _index_manifest(arm_id=arm_id, program_id=program_id, binding=binding)
            binding["index_manifest_sha256"] = manifest["index_manifest_sha256"]
            bindings.append(binding)
            manifests.append(manifest)
        del tokenizer
    binding_set["bindings"] = bindings
    binding_set["binding_set_sha256"] = canonical_sha256({key: item for key, item in binding_set.items() if key != "binding_set_sha256"})
    validate_binding_set(root, binding_set)
    receipt = _receipt(binding_set, hashes)
    _schema_file(root, COMPILER_RECEIPT_SCHEMA_PATH, receipt, role="protected compiler receipt")
    assert_aggregate_only(receipt)
    for manifest in manifests:
        _write_manifest(index_directory, manifest)
    if binding_output.exists() and _read_json(binding_output, role="existing binding output") != binding_set:
        raise ProtectedCompilationV12Error("existing binding output differs from the immutable transaction result")
    if receipt_output.exists() and _read_json(receipt_output, role="existing compiler receipt") != receipt:
        raise ProtectedCompilationV12Error("existing compiler receipt differs from the immutable transaction result")
    if not binding_output.exists():
        _atomic_json(binding_output, binding_set)
    if not receipt_output.exists():
        _atomic_json(receipt_output, receipt)
    state["phase"] = "complete"
    _atomic_json(_state_path(transaction), state)
    return {"status": "PASS", "binding_count": 25, "binding_set_sha256": binding_set["binding_set_sha256"], "receipt_sha256": receipt["receipt_sha256"], "launch_allowed": False, "adopted_for_execution": False, "measured_runs": 0, "charged_usd": 0}


def _program_hash(root: Path, program_id: str) -> str:
    program_set = _read_json(root / "control/armindex/a1.2/common-program-set.v11.json", role="common program set")
    return next(str(item["program_spec_sha256"]) for item in program_set["programs"] if item["program_key"] == program_id)


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-owner-local-protected-compiler-v12")
    parser.add_argument("command", choices=("preflight", "produce"))
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--input-relative", required=True)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--binding-output-relative")
    parser.add_argument("--receipt-output-relative")
    args = parser.parse_args()
    if args.command == "preflight":
        result = preflight(args.repository_root, input_relative_path=args.input_relative, model_root=args.model_root)
    else:
        if args.binding_output_relative is None or args.receipt_output_relative is None:
            parser.error("produce requires both protected receipt output relative paths")
        result = produce(args.repository_root, input_relative_path=args.input_relative, binding_output_relative_path=args.binding_output_relative, receipt_output_relative_path=args.receipt_output_relative, model_root=args.model_root)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
