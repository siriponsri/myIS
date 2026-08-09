"""Additive A1.2 protected compiler integration for the frozen v14 repair.

This module is deliberately separate from the v12 compiler.  It validates the
frozen v14 contract, reuses its aggregate-only compatibility audit, compiles
the ARM-01 lexical path, and emits hash/count bindings for all 25 topology
cells.  Dense cells are represented by deterministic physical-window plans;
the module never loads model weights, runs an encoder, builds an index, or
performs retrieval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
import tempfile
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_bytes, canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a1_2_compiled_bindings_v12 import ARM_IDS
from .a1_2_dense_overflow_adapter_v1 import (
    IMPLEMENTATION_VERSION as V14_PLANNER_VERSION,
)
from .a1_2_dense_overflow_contract_v14 import validate_contract as validate_v14_contract
from .a1_2_p02_first_claim_v1 import first_claim_segment
from .bm25s_adapter import tokenize as bm25_tokenize
from .scientific_common_programs_v11 import (
    PublicationRecord,
    _family_text,
    _passages,
    compile_common_program,
)

INTEGRATION_PATH = Path("control/armindex/a1.2/protected-compiler-integration.v15.json")
INTEGRATION_SCHEMA_PATH = Path("schemas/armindex/a1.2-protected-compiler-integration.v15.json")
INPUT_SCHEMA_PATH = Path("schemas/armindex/a1.2-owner-local-protected-compilation-input.v15.json")
BINDING_SCHEMA_PATH = Path("schemas/armindex/a1.2-compiled-program-binding-set.v15.json")
RECEIPT_SCHEMA_PATH = Path("schemas/armindex/a1.2-owner-local-protected-compiler-receipt.v15.json")
V14_SCHEMA_PATH = Path("schemas/armindex/a1.2-dense-overflow-adapter-repair.v14.json")
V14_PATH = Path("control/armindex/a1.2/dense-overflow-adapter-repair.v14.json")
V11_REQUEST_PATH = Path("control/armindex/a1.2/scientific-execution-adoption-request.v11.json")
V11_PROGRAM_SET_PATH = Path("control/armindex/a1.2/common-program-set.v11.json")
V12_R3_PATH = Path("control/armindex/a1.2/scientific-execution-adoption-inputs.v12-r3.json")
V13_PATH = Path("control/armindex/a1.2/publication-impact-contract.v13.json")
P02_PATH = Path("control/armindex/a1.2/p02-first-claim-repair.v1.json")
PROGRAM_IDS = ("P00-TAC-DOC", "P01-TA-DOC", "P02-FIRST-CLAIM", "P03-PASSAGE", "P04-SECTION-MULTIVIEW")
SLOT_BY_PROGRAM = {"P00-TAC-DOC": "P00", "P01-TA-DOC": "P01", "P02-FIRST-CLAIM": "P02", "P03-PASSAGE": "P03", "P04-SECTION-MULTIVIEW": "P04"}
ORIGINAL_BY_PROGRAM = {"P02-FIRST-CLAIM": "P02-CLAIM1", **{key: key for key in PROGRAM_IDS if key != "P02-FIRST-CLAIM"}}
_TOKEN_RE = re.compile(r"^Q-[a-f0-9]{32}$")
_FAMILY_RE = re.compile(r"^F-[a-f0-9]{32}$")
_SECRET_OR_PATH = re.compile(r"(?:bearer\s+|api[_-]?key|private[_-]?key|password|[A-Za-z]:\\|/Users/|/home/|\\\\[^\\]+\\)", re.IGNORECASE)


class ProtectedCompilationV15Error(ValueError):
    """Fail-closed error without protected payloads or paths."""


def aggregate_physical_window_vectors(
    arm_id: str,
    vectors: Sequence[Sequence[float]],
    source_token_counts: Sequence[int],
) -> tuple[float, ...]:
    """Apply the frozen token-count weighted mean and arm L2 postprocessing.

    This pure helper is exercised with synthetic vectors only.  Actual encoder
    invocation remains in the unchanged frozen arm adapters and outside this
    local compiler integration.
    """

    if arm_id not in {"ARM-02", "ARM-03", "ARM-04", "ARM-05"}:
        raise ProtectedCompilationV15Error("weighted composition requires a dense arm")
    if not vectors or len(vectors) != len(source_token_counts):
        raise ProtectedCompilationV15Error("weighted composition inputs are incomplete")
    dimension = len(vectors[0])
    if dimension < 1 or any(len(vector) != dimension for vector in vectors):
        raise ProtectedCompilationV15Error("physical window vector dimensions differ")
    if any(not isinstance(count, int) or count < 1 for count in source_token_counts):
        raise ProtectedCompilationV15Error("physical window source-token weights are invalid")
    if any(not math.isfinite(float(value)) for vector in vectors for value in vector):
        raise ProtectedCompilationV15Error("physical window vectors contain non-finite values")
    denominator = sum(source_token_counts)
    weighted = [
        sum(float(vector[index]) * count for vector, count in zip(vectors, source_token_counts, strict=True)) / denominator
        for index in range(dimension)
    ]
    norm = math.sqrt(sum(value * value for value in weighted))
    if not math.isfinite(norm) or norm <= 0:
        raise ProtectedCompilationV15Error("weighted logical vector cannot be L2-normalized")
    return tuple(value / norm for value in weighted)


def _read_json(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProtectedCompilationV15Error(f"{role} is missing or invalid JSON") from error
    if not isinstance(value, dict):
        raise ProtectedCompilationV15Error(f"{role} must be a JSON object")
    return value


def _json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _self_hash(value: Mapping[str, Any], field: str) -> str:
    return canonical_sha256({key: item for key, item in value.items() if key != field})


def _schema(root: Path, path: Path, value: Mapping[str, Any], *, role: str) -> None:
    errors = sorted(Draft202012Validator(_read_json(root / path, role=f"{role} schema")).iter_errors(value), key=lambda item: list(item.path))
    if errors:
        raise ProtectedCompilationV15Error(f"{role} schema failure at {list(errors[0].path)}")


def _safe(value: Mapping[str, Any], *, role: str) -> None:
    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise ProtectedCompilationV15Error(f"{role} contains protected payload fields") from error
    if _SECRET_OR_PATH.search(json.dumps(value, ensure_ascii=True, sort_keys=True)):
        raise ProtectedCompilationV15Error(f"{role} contains credential-like or absolute-path material")


def _relative(value: str, *, role: str) -> Path:
    path = Path(value)
    if path.is_absolute() or not value.strip() or ".." in path.parts:
        raise ProtectedCompilationV15Error(f"{role} must be a safe relative path")
    return path


def _store(root: Path) -> Path:
    raw = os.environ.get("MYIS_STORE")
    if not raw:
        raise ProtectedCompilationV15Error("MYIS_STORE is required for protected compilation")
    try:
        path = Path(raw).resolve(strict=True)
    except OSError as error:
        raise ProtectedCompilationV15Error("MYIS_STORE must resolve to a directory") from error
    if path.is_symlink() or not path.is_dir() or path.is_relative_to(root):
        raise ProtectedCompilationV15Error("MYIS_STORE must be a non-symlink directory outside the repository")
    return path


def _store_file(store: Path, relative: str, *, role: str) -> Path:
    candidate = store / _relative(relative, role=role)
    try:
        resolved, metadata = candidate.resolve(strict=True), candidate.lstat()
    except OSError as error:
        raise ProtectedCompilationV15Error(f"required {role} is missing") from error
    if candidate.is_symlink() or not resolved.is_relative_to(store) or not stat.S_ISREG(metadata.st_mode):
        raise ProtectedCompilationV15Error(f"required {role} is unsafe")
    return resolved


def _safe_output(store: Path, relative: str, *, role: str) -> Path:
    candidate = store / _relative(relative, role=role)
    candidate.parent.mkdir(parents=True, exist_ok=True)
    if candidate.parent.is_symlink() or candidate.is_symlink():
        raise ProtectedCompilationV15Error(f"{role} target is unsafe")
    if candidate.exists() and (not candidate.is_file() or not candidate.resolve().is_relative_to(store)):
        raise ProtectedCompilationV15Error(f"{role} target is unsafe")
    return candidate


def _atomic(path: Path, value: Mapping[str, Any]) -> None:
    text = _json(value)
    if path.exists():
        if path.is_symlink() or path.read_text(encoding="utf-8") != text:
            raise ProtectedCompilationV15Error("immutable protected output differs")
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


def _artifact(store: Path, value: Mapping[str, Any], *, role: str) -> tuple[Path, str]:
    path = _store_file(store, str(value["relative_path"]), role=role)
    observed = file_sha256(path)
    if observed != value["sha256"]:
        raise ProtectedCompilationV15Error(f"{role} SHA-256 mismatch")
    return path, observed


def _iter_jsonl(path: Path, *, role: str) -> Iterator[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            seen = False
            for line in handle:
                if not line.strip():
                    raise ProtectedCompilationV15Error(f"{role} contains an empty line")
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ProtectedCompilationV15Error(f"{role} contains a non-object row")
                seen = True
                yield value
            if not seen:
                raise ProtectedCompilationV15Error(f"{role} is empty")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProtectedCompilationV15Error(f"{role} is not valid JSONL") from error


def _validate_v14(root: Path, integration: Mapping[str, Any]) -> dict[str, Any]:
    contract = _read_json(root / V14_PATH, role="v14 dense-overflow contract")
    try:
        validate_v14_contract(root, contract)
    except ValueError as error:
        raise ProtectedCompilationV15Error("v14 dense-overflow contract validation failed") from error
    if integration["preserved_lineage"]["v14_repair_sha256"] != file_sha256(root / V14_PATH):
        raise ProtectedCompilationV15Error("integration v14 file binding mismatch")
    if contract["implementation"]["version"] != V14_PLANNER_VERSION:
        raise ProtectedCompilationV15Error("v14 planner version drifted")
    semantics = contract["composition_semantics"]
    if semantics["overlap_tokens"] != 0 or semantics["source_token_multiplicity"] != 1 or any(semantics[key] for key in ("truncation_allowed", "omission_allowed", "alternate_field_fallback_allowed", "p03_physical_windows_become_retrieval_units")):
        raise ProtectedCompilationV15Error("v14 composition semantics are unsafe")
    if contract["requirements"] != {"compatible_program_arm_cells": 25, "rep_dev_query_coverage_fraction": 1.0, "required_corpus_logical_unit_coverage_fraction": 1.0, "maximum_physical_window_must_not_exceed_effective_limit": True, "source_token_drop_count": 0, "source_token_overlap_count": 0, "silent_truncation_count": 0, "fallback_count": 0, "deterministic_replay_required": True, "fail_closed": True}:
        raise ProtectedCompilationV15Error("v14 requirement contract drifted")
    if any(value is not False for value in contract["authorization"].values()):
        raise ProtectedCompilationV15Error("v14 authorization contract is open")
    return contract


def _validate_integration(root: Path) -> dict[str, Any]:
    value = _read_json(root / INTEGRATION_PATH, role="v15 compiler integration contract")
    _schema(root, INTEGRATION_SCHEMA_PATH, value, role="v15 compiler integration contract")
    if value["contract_sha256"] != _self_hash(value, "contract_sha256"):
        raise ProtectedCompilationV15Error("v15 integration contract self-hash mismatch")
    if value["implementation"]["source_sha256"] != file_sha256(root / value["implementation"]["source_uri"]):
        raise ProtectedCompilationV15Error("v15 compiler source hash mismatch")
    if value["implementation"]["materializer_source_sha256"] != file_sha256(root / value["implementation"]["materializer_source_uri"]):
        raise ProtectedCompilationV15Error("v15 materializer source hash mismatch")
    return value


def _validate_repo_binding(root: Path, value: Mapping[str, Any], *, role: str, self_field: str | None = None) -> dict[str, Any]:
    path = root / _relative(str(value["uri"]), role=f"{role} URI")
    if file_sha256(path) != value["file_sha256"]:
        raise ProtectedCompilationV15Error(f"{role} file hash mismatch")
    loaded = _read_json(path, role=role)
    field = self_field or ("contract_sha256" if "contract_sha256" in loaded else "audit_sha256" if "audit_sha256" in loaded else "inventory_sha256" if "inventory_sha256" in loaded else "receipt_sha256")
    if loaded.get(field) != value["self_sha256"] or loaded.get(field) != _self_hash(loaded, field):
        raise ProtectedCompilationV15Error(f"{role} self-hash mismatch")
    return loaded


def _validate_lineage(root: Path, integration: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    request = _read_json(root / V11_REQUEST_PATH, role="v11 request")
    program_set = _read_json(root / V11_PROGRAM_SET_PATH, role="v11 program set")
    v13 = _read_json(root / V13_PATH, role="v13 publication contract")
    if request["request_sha256"] != integration["preserved_lineage"]["v11_request_sha256"] or program_set["program_set_sha256"] != integration["preserved_lineage"]["v11_program_set_sha256"] or file_sha256(root / V12_R3_PATH) != integration["preserved_lineage"]["v12_r3_file_sha256"] or file_sha256(root / V13_PATH) != integration["preserved_lineage"]["v13_publication_sha256"]:
        raise ProtectedCompilationV15Error("historical v11/v12-r3/v13 lineage changed")
    outcomes = v13.get("analysis", {}).get("outcomes", {})
    if outcomes.get("primary") != "out_recall_at_100" or outcomes.get("secondary") != ["out_ndcg_at_100", "out_ndcg_at_10"]:
        raise ProtectedCompilationV15Error("v13 publication metric hierarchy changed")
    return request, program_set, v13


def _validate_audits(root: Path, integration: Mapping[str, Any], v14: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    inventory = _validate_repo_binding(root, {"uri": "outputs/audits/armindex/a1.2-dense-overflow-inventory-20260808.json", "file_sha256": v14["raw_inventory"]["file_sha256"], "self_sha256": v14["raw_inventory"]["inventory_sha256"]}, role="v14 raw inventory")
    composition_path = root / "outputs/audits/armindex/a1.2-dense-overflow-composition-20260808.json"
    composition = _read_json(composition_path, role="v14 composition audit")
    if file_sha256(composition_path) != integration["compatibility_inputs"]["composition_sha256"] or composition.get("audit_sha256") != _self_hash(composition, "audit_sha256"):
        raise ProtectedCompilationV15Error("v14 composition audit hash mismatch")
    if composition.get("status") != "PASS" or composition.get("scope", {}).get("dense_program_arm_cells") != 20 or composition.get("scope", {}).get("rep_dev_query_count") != 150:
        raise ProtectedCompilationV15Error("v14 composition audit is not a complete PASS")
    locks = {item["arm_id"]: item for item in _read_json(root / "control/owner-local/a1.2-compiled-program-bindings-contract.v12.json", role="model binding contract")["model_locks"]}
    for arm_id in ("ARM-02", "ARM-03", "ARM-04", "ARM-05"):
        lock_value = _read_json(root / f"control/armindex/a1.2/model-locks/{arm_id}.v1.json", role=f"{arm_id} model lock")
        templates = {"corpus": _template_from_lock(lock_value, side="corpus"), "rep_dev_queries": _template_from_lock(lock_value, side="rep_dev_queries")}
        audit_binding = composition.get("bindings", {}).get("dense_arms", {}).get(arm_id, {})
        if audit_binding.get("template_sha256") != canonical_sha256(templates) or audit_binding.get("tokenizer_sha256") != locks[arm_id]["tokenizer_sha256"] or audit_binding.get("effective_input_limit") != locks[arm_id]["effective_input_limit"]:
            raise ProtectedCompilationV15Error("v14 composition template/model binding mismatch")
        for program_slot in ("P00", "P01", "P02", "P03", "P04"):
            program_id = "P02-CLAIM1" if program_slot == "P02" else next(key for key in composition["cells"][arm_id] if key.startswith(program_slot))
            cells = composition["cells"][arm_id][program_id]
            for side in ("corpus", "rep_dev_queries", "combined"):
                cell = cells[side]
                if cell["status"] != "PASS" or cell["maximum_physical_window_tokens"] > cell["effective_input_limit"] or cell["source_token_drop_count"] != 0 or cell["source_token_overlap_count"] != 0 or cell["truncation_count"] != 0 or cell["fallback_count"] != 0:
                    raise ProtectedCompilationV15Error("v14 dense cell failed zero-drop compatibility")
    return inventory, composition


def _template_from_lock(lock: Mapping[str, Any], *, side: str) -> str:
    key, slot = ("document_format", "{document}") if side == "corpus" else ("query_format", "{query}")
    if side not in {"corpus", "rep_dev_queries"}:
        raise ProtectedCompilationV15Error("unsupported template side")
    value = lock.get(key)
    if value in (None, "no_instruction"):
        return "{text}"
    if not isinstance(value, str) or value.count(slot) != 1:
        raise ProtectedCompilationV15Error("frozen model lock has an invalid template")
    rendered = value.replace(slot, "{text}")
    if rendered.count("{text}") != 1:
        raise ProtectedCompilationV15Error("frozen model template does not have one text slot")
    return rendered


def _validate_input(root: Path, value: Mapping[str, Any], integration: Mapping[str, Any]) -> tuple[Path, dict[str, Path], dict[str, str]]:
    _schema(root, INPUT_SCHEMA_PATH, value, role="v15 protected compilation input")
    if _SECRET_OR_PATH.search(json.dumps(value, ensure_ascii=True, sort_keys=True)):
        raise ProtectedCompilationV15Error("v15 protected compilation input contains an unsafe path")
    store = _store(root)
    artifact_paths: dict[str, Path] = {}
    hashes: dict[str, str] = {}
    for key, artifact in value["artifacts"].items():
        artifact_paths[key], hashes[key] = _artifact(store, artifact, role=key)
    anchor_path, hashes["pre_compilation_anchor"] = _artifact(store, value["pre_compilation_anchor"], role="pre-compilation anchor")
    artifact_paths["pre_compilation_anchor"] = anchor_path
    anchor = _read_json(anchor_path, role="pre-compilation anchor")
    _safe(anchor, role="pre-compilation anchor")
    if anchor.get("schema_version") != "myis.armindex-a1.2-pre-compilation-anchor.v15" or anchor.get("anchor_sha256") != _self_hash(anchor, "anchor_sha256") or anchor.get("authorization") != integration["authorization"]:
        raise ProtectedCompilationV15Error("pre-compilation anchor is invalid or changes authorization")
    expected_audits = {
        "v14_contract": (V14_PATH, "contract_sha256"),
        "inventory": (Path("outputs/audits/armindex/a1.2-dense-overflow-inventory-20260808.json"), "inventory_sha256"),
        "composition": (Path("outputs/audits/armindex/a1.2-dense-overflow-composition-20260808.json"), "audit_sha256"),
        "p02_repair": (P02_PATH, "contract_sha256"),
        "split_decision": (Path("control/armindex/a1.2/rep-harness-split-decision.v1.json"), "decision_sha256"),
    }
    for key, (path, self_field) in expected_audits.items():
        binding = value["compatibility_audits"][key]
        if binding["uri"] != path.as_posix():
            raise ProtectedCompilationV15Error("protected input compatibility URI mismatch")
        _validate_repo_binding(root, binding, role=key.replace("_", " "), self_field=self_field)
    queries = list(_iter_jsonl(artifact_paths["queries"], role="query bundle"))
    if len(queries) != 150 or any(set(row) != {"work_token", "text"} or _TOKEN_RE.fullmatch(str(row["work_token"])) is None or not isinstance(row["text"], str) or not row["text"] for row in queries):
        raise ProtectedCompilationV15Error("query bundle must contain exactly 150 opaque REP-DEV rows")
    split = _read_json(artifact_paths["split"], role="split commitment")
    if split.get("schema_version") != "myis.armindex-a1.2-protected-split.v15" or not isinstance(split.get("rep_dev_work_tokens"), list) or len(split["rep_dev_work_tokens"]) != 150 or split.get("harness_dev_reserved_count") != 100 or split.get("train_pool_count") != 250:
        raise ProtectedCompilationV15Error("split commitment does not preserve 150/100/250")
    query_tokens = {row["work_token"] for row in queries}
    if set(split["rep_dev_work_tokens"]) != query_tokens or len(query_tokens) != 150:
        raise ProtectedCompilationV15Error("split commitment does not bind the exact query work tokens")
    if split.get("split_commitment_sha256") != _self_hash(split, "split_commitment_sha256"):
        raise ProtectedCompilationV15Error("split commitment self-hash mismatch")
    corpus_count = 0
    families: set[str] = set()
    for row in _iter_jsonl(artifact_paths["corpus"], role="corpus bundle"):
        family = str(row.get("family_token", ""))
        if _FAMILY_RE.fullmatch(family) is None or family in families:
            raise ProtectedCompilationV15Error("corpus bundle has a missing or duplicate opaque family token")
        families.add(family)
        corpus_count += 1
    handoff_request = _read_json(root / "control/owner-local/a1.2-evaluator-handoff-request.v11.json", role="handoff request")
    handoff = _read_json(artifact_paths["handoff_receipt"], role="handoff receipt")
    _safe(handoff, role="handoff receipt")
    if set(handoff) != set(handoff_request["required_owner_local_receipt_fields"]) or handoff.get("receipt_sha256") != _self_hash(handoff, "receipt_sha256"):
        raise ProtectedCompilationV15Error("handoff receipt fields or self-hash are invalid")
    expected_handoff = {"corpus_bundle_sha256": hashes["corpus"], "query_bundle_sha256": hashes["queries"], "split_commitment_sha256": hashes["split"], "evaluator_sha256": hashes["evaluator"], "ephemeral_token_map_sha256": hashes["ephemeral_token_map"]}
    if any(handoff.get(key) != expected for key, expected in expected_handoff.items()) or handoff.get("source_contract_sha256") != handoff_request["source_contract"]["file_sha256"] or handoff.get("corpus_count") != corpus_count or handoff.get("query_count") != 150 or handoff.get("reserved_harness_dev_count") != 100 or handoff.get("train_pool_count") != 250:
        raise ProtectedCompilationV15Error("handoff receipt does not bind the protected compilation inputs")
    transfer_contract = _read_json(root / "control/armindex/a1.2/scientific-transfer-contract.v11.json", role="transfer contract")
    transfer = _read_json(artifact_paths["protected_transfer_manifest"], role="protected transfer manifest")
    _safe(transfer, role="protected transfer manifest")
    if set(transfer) != set(transfer_contract["owner_local_protected_transfer_manifest"]["required_fields"]) or transfer.get("manifest_sha256") != _self_hash(transfer, "manifest_sha256"):
        raise ProtectedCompilationV15Error("protected transfer manifest fields or self-hash are invalid")
    request = _read_json(root / V11_REQUEST_PATH, role="v11 request")
    workload_set = _read_json(root / "control/armindex/a1.2/workload-manifest-set.scientific-request.v11.json", role="workload manifest set")
    expected_transfer = {"request_sha256": request["request_sha256"], "adoption_receipt_sha256": anchor["anchor_sha256"], "dataset_revision": handoff_request["source_contract"]["dataset_revision"], "split_commitment_sha256": hashes["split"], "evaluator_sha256": hashes["evaluator"], "corpus_bundle_sha256": hashes["corpus"], "corpus_bundle_bytes": artifact_paths["corpus"].stat().st_size, "corpus_family_count": len(families), "query_bundle_sha256": hashes["queries"], "query_bundle_bytes": artifact_paths["queries"].stat().st_size, "rep_dev_query_count": 150, "harness_dev_reserved_count": 100, "opaque_token_scheme_sha256": canonical_sha256(transfer_contract["opaque_token_contract"]), "ephemeral_token_map_sha256": hashes["ephemeral_token_map"], "workload_manifest_set_sha256": workload_set["manifest_set_sha256"], "expected_result_rows_per_program": 150}
    if any(transfer.get(key) != expected for key, expected in expected_transfer.items()):
        raise ProtectedCompilationV15Error("protected transfer manifest does not bind the protected compilation inputs")
    return store, artifact_paths, hashes


def _logical_units(row: Mapping[str, Any], *, program_id: str) -> tuple[tuple[str, str], ...]:
    family = str(row["family_token"])
    record = PublicationRecord(family_token=family, publication_token=str(row["publication_token"]), publication_ordinal=int(row["publication_ordinal"]), title_en=row.get("title_en"), abstract_en=row.get("abstract_en"), claims_text=row.get("claims_text"), claims=())
    members = (record,)
    if program_id == "P00-TAC-DOC":
        values = (_family_text(members, ("title_en", "abstract_en", "claims_text")),)
    elif program_id == "P01-TA-DOC":
        values = (_family_text(members, ("title_en", "abstract_en")),)
    elif program_id == "P02-FIRST-CLAIM":
        values = (first_claim_segment(row.get("claims_text")).text,)
    elif program_id == "P03-PASSAGE":
        values = _passages(_family_text(members, ("title_en", "abstract_en", "claims_text")))
    elif program_id == "P04-SECTION-MULTIVIEW":
        values = tuple(_family_text(members, (field,), labels={field: label}) for field, label in (("title_en", "TITLE"), ("abstract_en", "ABSTRACT"), ("claims_text", "CLAIMS")))
    else:
        raise ProtectedCompilationV15Error("unknown logical program")
    return tuple((f"{family}:{index}", text) for index, text in enumerate(values, start=1))


def _compile_arm01(corpus_path: Path, *, program_id: str, logical_sha256: str) -> dict[str, Any]:
    digest = hashlib.sha256()
    digest.update(canonical_bytes({"arm_id": "ARM-01", "program_id": program_id, "logical_program_sha256": logical_sha256}))
    units = 0
    families = 0
    maximum = 0
    previous: str | None = None
    for row in _iter_jsonl(corpus_path, role="corpus bundle"):
        family = str(row.get("family_token", ""))
        if _FAMILY_RE.fullmatch(family) is None or (previous is not None and family <= previous):
            raise ProtectedCompilationV15Error("corpus bundle ordering or opaque family token is invalid")
        previous = family
        families += 1
        if program_id == "P02-FIRST-CLAIM":
            values = _logical_units(row, program_id=program_id)
        else:
            try:
                compiled = compile_common_program({"P00-TAC-DOC": "P00-TAC-DOC", "P01-TA-DOC": "P01-TA-DOC", "P03-PASSAGE": "P03-PASSAGE", "P04-SECTION-MULTIVIEW": "P04-SECTION-MULTIVIEW"}[program_id], [dict(row, claims=[])])
            except Exception as error:
                raise ProtectedCompilationV15Error("ARM-01 frozen common program compilation failed") from error
            values = tuple((unit.unit_id, unit.text) for unit in compiled.units)
        for unit_id, text in values:
            content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            digest.update(canonical_bytes({"unit_id": unit_id, "content_sha256": content_hash}))
            units += 1
            maximum = max(maximum, len(bm25_tokenize(text)))
    if families < 1 or units < 1:
        raise ProtectedCompilationV15Error("ARM-01 logical compilation is empty")
    return {"logical_unit_count": units, "corpus_logical_unit_count": units, "corpus_overflow_logical_unit_count": 0, "raw_rendered_input_max_tokens": maximum, "physical_window_max_tokens": maximum, "physical_window_count": units, "compiled_representation_sha256": digest.hexdigest(), "families": families, "mode": "EXISTING_FROZEN_ADAPTER_PATH"}


def _arm01_query_evidence(query_path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    maximum = 0
    count = 0
    seen: set[str] = set()
    for row in _iter_jsonl(query_path, role="query bundle"):
        token, text = str(row.get("work_token", "")), row.get("text")
        if _TOKEN_RE.fullmatch(token) is None or token in seen or not isinstance(text, str) or not text:
            raise ProtectedCompilationV15Error("query bundle contains an invalid opaque query row")
        seen.add(token)
        count += 1
        token_count = len(bm25_tokenize(text))
        maximum = max(maximum, token_count)
        digest.update(canonical_bytes({"work_token_sha256": hashlib.sha256(token.encode("ascii")).hexdigest(), "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "token_count": token_count}))
    if count != 150:
        raise ProtectedCompilationV15Error("ARM-01 query compatibility requires exactly 150 REP-DEV rows")
    return {"query_count": count, "maximum_tokens": maximum, "query_manifest_sha256": digest.hexdigest()}


def _dense_binding(*, arm_id: str, program_id: str, program_hash: str, lock: Mapping[str, Any], composition: Mapping[str, Any], integration: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    old_id = ORIGINAL_BY_PROGRAM[program_id]
    old_key = old_id
    cell = composition["cells"][arm_id][old_key]
    combined, corpus, query = cell["combined"], cell["corpus"], cell["rep_dev_queries"]
    body = {"arm_id": arm_id, "program_slot": SLOT_BY_PROGRAM[program_id], "program_id": program_id, "original_program_id": old_id, "logical_program_sha256": program_hash, "v14_contract_sha256": integration["compatibility_inputs"]["composition_sha256"], "combined_plan_manifest_sha256": combined["plan_manifest_sha256"], "corpus_plan_manifest_sha256": corpus["plan_manifest_sha256"], "query_plan_manifest_sha256": query["plan_manifest_sha256"]}
    representation = canonical_sha256(body)
    binding = {"binding_id": f"{arm_id}--{SLOT_BY_PROGRAM[program_id]}-{program_id}", "arm_id": arm_id, "program_slot": SLOT_BY_PROGRAM[program_id], "program_id": program_id, "original_program_id": old_id, "logical_program_sha256": program_hash, "compiler_source_manifest_sha256": integration["implementation"]["source_sha256"], "model_lock_file_sha256": lock["file_sha256"], "adapter_contract_sha256": lock["adapter_contract_sha256"], "tokenizer_sha256": lock["tokenizer_sha256"], "effective_input_limit": int(lock["effective_input_limit"]), "raw_rendered_input_max_tokens": int(combined["maximum_raw_rendered_tokens"]), "physical_window_max_tokens": int(combined["maximum_physical_window_tokens"]), "physical_window_count": int(combined["physical_window_count"]), "logical_unit_count": int(corpus["logical_unit_count"]), "corpus_logical_unit_count": int(corpus["logical_unit_count"]), "corpus_overflow_logical_unit_count": int(corpus["overflow_logical_unit_count"]), "query_logical_unit_count": 150, "query_overflow_logical_unit_count": int(query["overflow_logical_unit_count"]), "source_token_drop_count": 0, "source_token_overlap_count": 0, "truncation_count": 0, "fallback_count": 0, "coverage_gap_count": 0, "omitted_unit_count": 0, "raw_overlength_count": int(combined["overflow_logical_unit_count"]), "compiled_representation_sha256": representation, "index_manifest_sha256": "0" * 64, "mode": "DENSE_OVERFLOW_COMPOSED"}
    manifest_body = {"schema_version": "myis.armindex-a1.2-protected-index-manifest.v15", "status": "compiled_physical_window_plan_only_not_measured_index", "arm_id": arm_id, "program_slot": SLOT_BY_PROGRAM[program_id], "program_id": program_id, "logical_program_sha256": program_hash, "compiled_representation_sha256": representation, "effective_input_limit": binding["effective_input_limit"], "physical_window_count": binding["physical_window_count"], "physical_window_max_tokens": binding["physical_window_max_tokens"], "source_token_drop_count": 0, "source_token_overlap_count": 0, "truncation_count": 0, "fallback_count": 0}
    manifest = {**manifest_body, "index_manifest_sha256": canonical_sha256(manifest_body)}
    binding["index_manifest_sha256"] = manifest["index_manifest_sha256"]
    return binding, manifest


def _program_hashes(program_set: Mapping[str, Any], p02: Mapping[str, Any]) -> dict[str, str]:
    values = {item["program_key"]: item["program_spec_sha256"] for item in program_set["programs"]}
    values["P02-FIRST-CLAIM"] = p02["contract_sha256"]
    return values


def _models(root: Path, model_root: Path, locks: Mapping[str, Mapping[str, Any]], entries: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    if model_root.is_symlink() or model_root.is_relative_to(root) or not model_root.is_dir():
        raise ProtectedCompilationV15Error("model root must be a safe external directory")
    if [entry.get("arm_id") for entry in entries] != list(ARM_IDS):
        raise ProtectedCompilationV15Error("model inputs must list ARM-01 through ARM-05 in order")
    resolved: dict[str, Mapping[str, Any]] = {}
    for entry in entries:
        arm_id = str(entry["arm_id"])
        lock = locks[arm_id]
        if arm_id == "ARM-01":
            if any(entry[key] is not None for key in entry if key != "arm_id"):
                raise ProtectedCompilationV15Error("ARM-01 must not declare a dense model path")
            resolved[arm_id] = lock
            continue
        directory = (model_root / _relative(str(entry["model_relative_path"]), role=f"{arm_id} model path")).resolve(strict=True)
        if directory.is_symlink() or not directory.is_relative_to(model_root):
            raise ProtectedCompilationV15Error(f"{arm_id} model directory is unsafe")
        tokenizer = directory / _relative(str(entry["tokenizer_json_relative_path"]), role=f"{arm_id} tokenizer path")
        if tokenizer.is_symlink() or file_sha256(tokenizer) != lock["tokenizer_sha256"]:
            raise ProtectedCompilationV15Error(f"{arm_id} tokenizer hash mismatch")
        manifest = _read_json(directory / _relative(str(entry["runtime_manifest_relative_path"]), role=f"{arm_id} runtime manifest path"), role=f"{arm_id} runtime manifest")
        if manifest.get("arm_id") != arm_id or manifest.get("source_lock_file_sha256") != lock["file_sha256"]:
            raise ProtectedCompilationV15Error(f"{arm_id} runtime manifest binding mismatch")
        resolved[arm_id] = lock
    return resolved


def _write_manifest(target: Path, value: Mapping[str, Any]) -> None:
    _atomic(target, value)


def preflight(repository_root: Path, *, input_relative_path: str, model_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    integration = _validate_integration(root)
    _request, _program_set, _v13 = _validate_lineage(root, integration)
    _validate_repo_binding(root, {"uri": integration["p02_successor"]["contract_uri"], "file_sha256": file_sha256(root / P02_PATH), "self_sha256": _read_json(root / P02_PATH, role="P02 repair")["contract_sha256"]}, role="P02 repair")
    v14 = _validate_v14(root, integration)
    inventory, composition = _validate_audits(root, integration, v14)
    value = _read_json(_store(root) / _relative(input_relative_path, role="input contract"), role="v15 protected input contract")
    _validate_input(root, value, integration)
    _models(root, model_root.resolve(strict=True), {item["arm_id"]: item for item in _read_json(root / "control/owner-local/a1.2-compiled-program-bindings-contract.v12.json", role="model binding contract")["model_locks"]}, value["models"])
    if inventory.get("scope", {}).get("corpus_family_count") != composition.get("scope", {}).get("corpus_family_count"):
        raise ProtectedCompilationV15Error("inventory/composition corpus family counts differ")
    return {"status": "READY_FOR_OWNER_LOCAL_PROTECTED_COMPILATION_V15", "expected_bindings": 25, "dense_cells": 20, "rep_dev_query_count": 150, "p02_program_id": "P02-FIRST-CLAIM", "launch_allowed": False, "adopted_for_execution": False, "measured_runs": 0, "charged_usd": 0}


def produce(repository_root: Path, *, input_relative_path: str, binding_output_relative_path: str, receipt_output_relative_path: str, model_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    integration = _validate_integration(root)
    request, program_set, _v13 = _validate_lineage(root, integration)
    p02 = _validate_repo_binding(root, {"uri": integration["p02_successor"]["contract_uri"], "file_sha256": file_sha256(root / P02_PATH), "self_sha256": _read_json(root / P02_PATH, role="P02 repair")["contract_sha256"]}, role="P02 repair")
    v14 = _validate_v14(root, integration)
    inventory, composition = _validate_audits(root, integration, v14)
    store = _store(root)
    input_path = _store_file(store, input_relative_path, role="v15 input contract")
    input_value = _read_json(input_path, role="v15 input contract")
    _validate_input(root, input_value, integration)
    artifacts = {key: _artifact(store, value, role=key)[0] for key, value in input_value["artifacts"].items()}
    locks = {item["arm_id"]: item for item in _read_json(root / "control/owner-local/a1.2-compiled-program-bindings-contract.v12.json", role="model binding contract")["model_locks"]}
    _models(root, model_root.resolve(strict=True), locks, input_value["models"])
    hashes = {key: file_sha256(path) for key, path in artifacts.items()}
    program_hash = _program_hashes(program_set, p02)
    arm01_query = _arm01_query_evidence(artifacts["queries"])
    if arm01_query != _arm01_query_evidence(artifacts["queries"]):
        raise ProtectedCompilationV15Error("ARM-01 query compatibility replay differs")
    arm01_compiled: dict[str, dict[str, Any]] = {}
    for program_id in PROGRAM_IDS:
        first = _compile_arm01(artifacts["corpus"], program_id=program_id, logical_sha256=program_hash[program_id])
        replay = _compile_arm01(artifacts["corpus"], program_id=program_id, logical_sha256=program_hash[program_id])
        if first != replay:
            raise ProtectedCompilationV15Error("ARM-01 deterministic recompile parity failed")
        arm01_compiled[program_id] = first
    bindings: list[dict[str, Any]] = []
    manifests: list[dict[str, Any]] = []
    for arm_id in ARM_IDS:
        for program_id in PROGRAM_IDS:
            if arm_id == "ARM-01":
                result = arm01_compiled[program_id]
                query_count = int(arm01_query["query_count"])
                query_overflow = 0
                observed_max = max(int(result["physical_window_max_tokens"]), int(arm01_query["maximum_tokens"]))
                representation_sha256 = canonical_sha256({"corpus": result["compiled_representation_sha256"], "queries": arm01_query["query_manifest_sha256"], "program_id": program_id})
                binding = {"binding_id": f"{arm_id}--{SLOT_BY_PROGRAM[program_id]}-{program_id}", "arm_id": arm_id, "program_slot": SLOT_BY_PROGRAM[program_id], "program_id": program_id, "original_program_id": ORIGINAL_BY_PROGRAM[program_id], "logical_program_sha256": program_hash[program_id], "compiler_source_manifest_sha256": integration["implementation"]["source_sha256"], "model_lock_file_sha256": locks[arm_id]["file_sha256"], "adapter_contract_sha256": locks[arm_id]["adapter_contract_sha256"], "tokenizer_sha256": locks[arm_id]["tokenizer_sha256"], "effective_input_limit": observed_max, "raw_rendered_input_max_tokens": observed_max, "physical_window_max_tokens": observed_max, "physical_window_count": result["physical_window_count"] + query_count, "logical_unit_count": result["logical_unit_count"], "corpus_logical_unit_count": result["corpus_logical_unit_count"], "corpus_overflow_logical_unit_count": 0, "query_logical_unit_count": query_count, "query_overflow_logical_unit_count": query_overflow, "source_token_drop_count": 0, "source_token_overlap_count": 0, "truncation_count": 0, "fallback_count": 0, "coverage_gap_count": 0, "omitted_unit_count": 0, "raw_overlength_count": 0, "compiled_representation_sha256": representation_sha256, "index_manifest_sha256": "0" * 64, "mode": result["mode"]}
                manifest_body = {"schema_version": "myis.armindex-a1.2-protected-index-manifest.v15", "status": "compiled_lexical_manifest_only_not_measured_index", "arm_id": arm_id, "program_slot": binding["program_slot"], "program_id": program_id, "logical_program_sha256": program_hash[program_id], "compiled_representation_sha256": representation_sha256, "effective_input_limit": binding["effective_input_limit"], "physical_window_count": binding["physical_window_count"], "physical_window_max_tokens": binding["physical_window_max_tokens"], "source_token_drop_count": 0, "source_token_overlap_count": 0, "truncation_count": 0, "fallback_count": 0}
                manifest = {**manifest_body, "index_manifest_sha256": canonical_sha256(manifest_body)}
                binding["index_manifest_sha256"] = manifest["index_manifest_sha256"]
            else:
                binding, manifest = _dense_binding(arm_id=arm_id, program_id=program_id, program_hash=program_hash[program_id], lock=locks[arm_id], composition=composition, integration=integration)
                replay_binding, replay_manifest = _dense_binding(arm_id=arm_id, program_id=program_id, program_hash=program_hash[program_id], lock=locks[arm_id], composition=composition, integration=integration)
                if binding != replay_binding or manifest != replay_manifest:
                    raise ProtectedCompilationV15Error("dense binding deterministic replay failed")
            bindings.append(binding)
            manifests.append(manifest)
    expected = [{"arm_id": arm, "program_slot": slot} for arm in ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05") for slot in ("P00", "P01", "P02", "P03", "P04")]
    query_cells = []
    for binding in bindings:
        if binding["arm_id"] == "ARM-01":
            continue
        query = composition["cells"][binding["arm_id"]][binding["original_program_id"]]["rep_dev_queries"]
        query_cells.append({"arm_id": binding["arm_id"], "program_slot": binding["program_slot"], "effective_input_limit": int(query["effective_input_limit"]), "raw_rendered_input_max_tokens": int(query["maximum_raw_rendered_tokens"]), "physical_window_max_tokens": int(query["maximum_physical_window_tokens"]), "physical_window_count": int(query["physical_window_count"]), "overflow_logical_unit_count": int(query["overflow_logical_unit_count"]), "source_token_drop_count": 0, "source_token_overlap_count": 0, "truncation_count": 0, "fallback_count": 0, "plan_manifest_sha256": query["plan_manifest_sha256"]})
    body = {"schema_version": "myis.armindex-a1.2-compiled-program-binding-set.v15", "binding_set_id": f"a1.2-v15-{hashes['corpus'][:16]}", "status": "validated_owner_local_protected_compilation_v15", "claim_boundary": "Aggregate-safe Owner-local v15 protected compiler bindings. Dense cells bind deterministic tokenizer-level physical-window plans and weighted recomposition semantics; ARM-01 binds its frozen lexical path. No model weights, encoder vectors, retrieval, ranking, qrels, per-query outcomes, provider payloads, or scientific/publication result are emitted.", "integration_file_sha256": file_sha256(root / INTEGRATION_PATH), "lineage": {"v11_request_sha256": request["request_sha256"], "v11_program_set_sha256": program_set["program_set_sha256"], "v12_r3_file_sha256": file_sha256(root / V12_R3_PATH), "v13_publication_sha256": _read_json(root / V13_PATH, role="v13 publication")["contract_sha256"], "v14_contract_sha256": v14["contract_sha256"], "p02_repair_sha256": p02["contract_sha256"], "inventory_sha256": inventory["inventory_sha256"], "composition_sha256": composition["audit_sha256"], "pre_compilation_anchor_sha256": file_sha256(_store_file(store, input_value["pre_compilation_anchor"]["relative_path"], role="pre-compilation anchor"))}, "expected_bindings": expected, "bindings": bindings, "query_compatibility": {"rep_dev_query_count": 150, "coverage_fraction": 1.0, "cells": query_cells}, "launch_allowed": False, "adopted_for_execution": False, "measured_runs": 0, "charged_usd": 0}
    body["binding_set_sha256"] = _self_hash(body, "binding_set_sha256")
    _schema(root, BINDING_SCHEMA_PATH, body, role="v15 binding set")
    _safe(body, role="v15 binding set")
    for manifest in manifests:
        _write_manifest(_safe_output(store, input_value["protected_index_manifest_directory"] + "/" + f"{manifest['arm_id']}--{manifest['program_slot']}-{manifest['program_id'].replace('-', '_')}.json", role="index manifest"), manifest)
    binding_path = _safe_output(store, binding_output_relative_path, role="v15 binding set output")
    receipt_path = _safe_output(store, receipt_output_relative_path, role="v15 compiler receipt output")
    _atomic(binding_path, body)
    receipt_body = {"schema_version": "myis.armindex-a1.2-owner-local-protected-compiler-receipt.v15", "status": "PASS", "claim_boundary": "Aggregate-safe Owner-local v15 compiler receipt. It proves deterministic logical compilation and tokenizer-level physical-window compatibility only; it does not authorize provider contact, adoption, launch, retrieval, evaluation, Selection, Final, paid APIs, or a scientific/publication claim.", "integration_file_sha256": body["integration_file_sha256"], "handoff_receipt_sha256": hashes["handoff_receipt"], "protected_transfer_manifest_sha256": hashes["protected_transfer_manifest"], "pre_compilation_anchor_sha256": body["lineage"]["pre_compilation_anchor_sha256"], "corpus_bundle_sha256": hashes["corpus"], "query_bundle_sha256": hashes["queries"], "split_commitment_sha256": hashes["split"], "evaluator_sha256": hashes["evaluator"], "ephemeral_token_map_sha256": hashes["ephemeral_token_map"], "binding_set_sha256": body["binding_set_sha256"], "binding_count": 25, "coverage_gap_count": 0, "omitted_unit_count": 0, "truncation_count": 0, "overlength_count": 0, "raw_overflow_count": sum(int(item["raw_overlength_count"]) for item in bindings), "zero_silent_truncation": True, "deterministic_replay": True, "launch_allowed": False, "adopted_for_execution": False, "measured_runs": 0, "charged_usd": 0}
    receipt = {**receipt_body, "receipt_sha256": _self_hash(receipt_body, "receipt_sha256")}
    _schema(root, RECEIPT_SCHEMA_PATH, receipt, role="v15 compiler receipt")
    _safe(receipt, role="v15 compiler receipt")
    _atomic(receipt_path, receipt)
    return {"status": "PASS", "binding_count": 25, "binding_set_sha256": body["binding_set_sha256"], "receipt_sha256": receipt["receipt_sha256"], "raw_overflow_count": receipt["raw_overflow_count"], "zero_silent_truncation": True, "deterministic_replay": True, "launch_allowed": False, "adopted_for_execution": False, "measured_runs": 0, "charged_usd": 0}


def validate_binding_set(repository_root: Path, value: Mapping[str, Any]) -> dict[str, Any]:
    root = repository_root.resolve()
    _schema(root, BINDING_SCHEMA_PATH, value, role="v15 binding set")
    _safe(value, role="v15 binding set")
    if value["binding_set_sha256"] != _self_hash(value, "binding_set_sha256"):
        raise ProtectedCompilationV15Error("v15 binding-set self-hash mismatch")
    ids = [(item["arm_id"], item["program_slot"]) for item in value["bindings"]]
    if len(set(ids)) != 25 or ids != [(arm, slot) for arm in ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05") for slot in ("P00", "P01", "P02", "P03", "P04")]:
        raise ProtectedCompilationV15Error("v15 binding set does not cover the exact 25-cell topology")
    for item in value["bindings"]:
        if item["physical_window_max_tokens"] > item["effective_input_limit"] or any(item[key] != 0 for key in ("source_token_drop_count", "source_token_overlap_count", "truncation_count", "fallback_count", "coverage_gap_count", "omitted_unit_count")):
            raise ProtectedCompilationV15Error("v15 binding contains an over-limit physical window or nonzero safety count")
    return {"status": value["status"], "actual_bindings": 25, "binding_set_sha256": value["binding_set_sha256"], "launch_allowed": False, "adopted_for_execution": False, "measured_runs": 0, "charged_usd": 0}


def validate_receipt(repository_root: Path, value: Mapping[str, Any]) -> dict[str, Any]:
    root = repository_root.resolve()
    _schema(root, RECEIPT_SCHEMA_PATH, value, role="v15 compiler receipt")
    _safe(value, role="v15 compiler receipt")
    if value["receipt_sha256"] != _self_hash(value, "receipt_sha256"):
        raise ProtectedCompilationV15Error("v15 compiler receipt self-hash mismatch")
    return {"status": value["status"], "binding_count": value["binding_count"], "binding_set_sha256": value["binding_set_sha256"], "receipt_sha256": value["receipt_sha256"], "zero_silent_truncation": value["zero_silent_truncation"], "deterministic_replay": value["deterministic_replay"], "launch_allowed": False, "adopted_for_execution": False, "measured_runs": 0, "charged_usd": 0}


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-owner-local-protected-compiler-v15")
    parser.add_argument("command", choices=("preflight", "produce", "validate-binding", "validate-receipt"))
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--input-relative", required=False)
    parser.add_argument("--model-root", type=Path)
    parser.add_argument("--binding-output-relative")
    parser.add_argument("--receipt-output-relative")
    parser.add_argument("--binding-set", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    if args.command == "preflight":
        if not args.input_relative or args.model_root is None:
            parser.error("preflight requires --input-relative and --model-root")
        result = preflight(args.repository_root, input_relative_path=args.input_relative, model_root=args.model_root)
    elif args.command == "produce":
        if not args.input_relative or args.model_root is None or not args.binding_output_relative or not args.receipt_output_relative:
            parser.error("produce requires input, model root, and both output paths")
        result = produce(args.repository_root, input_relative_path=args.input_relative, binding_output_relative_path=args.binding_output_relative, receipt_output_relative_path=args.receipt_output_relative, model_root=args.model_root)
    elif args.command == "validate-binding":
        if args.binding_set is None:
            parser.error("validate-binding requires --binding-set")
        result = validate_binding_set(args.repository_root, _read_json(args.binding_set, role="v15 binding set"))
    else:
        if args.receipt is None:
            parser.error("validate-receipt requires --receipt")
        result = validate_receipt(args.repository_root, _read_json(args.receipt, role="v15 compiler receipt"))
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
