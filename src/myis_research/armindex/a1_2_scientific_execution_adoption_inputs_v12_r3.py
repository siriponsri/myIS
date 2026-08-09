"""Immutable, aggregate-safe closure for A1.2 V12-R3 adoption inputs.

This additive local-only finalizer verifies externally stored evidence without
copying its paths or protected payloads into the repository receipt.  It does
not contact a provider or change the unchanged V11 execution authority.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import stat
import subprocess
import tarfile
import tempfile
from collections.abc import Mapping
from io import BytesIO
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a1_2_compiled_bindings_v12 import validate_binding_set
from .a1_2_watchdog_provider_destroy_dry_run_v12 import (
    POLICY_PATH as WATCHDOG_POLICY_PATH,
)
from .a1_2_watchdog_provider_destroy_dry_run_v12 import (
    _validate_result as validate_watchdog_result,
)

REVISION_ID = "a1.2-scientific-execution-adoption-inputs-v12-r3"
CONTRACT_PATH = Path("control/armindex/a1.2/scientific-execution-adoption-inputs.v12-r3.json")
CONTRACT_SCHEMA_PATH = Path("schemas/armindex/a1.2-scientific-execution-adoption-inputs.v12-r3.json")
RECEIPT_SCHEMA_PATH = Path("schemas/armindex/a1.2-scientific-execution-adoption-inputs-receipt.v12-r3.json")
BUNDLE_RECEIPT_SCHEMA_PATH = Path("schemas/armindex/a1.2-scientific-execution-bundle-receipt.v12-r3.json")
ANCHOR_SCHEMA_PATH = Path("schemas/armindex/a1.2-scientific-execution-pre-adoption-anchor.v12-r3.json")
COMPILER_RECEIPT_SCHEMA_PATH = Path("schemas/armindex/a1.2-owner-local-protected-compiler-receipt.v12-r3.json")
TRANSFER_CONTRACT_PATH = Path("control/armindex/a1.2/scientific-transfer-contract.v11.json")
RECEIPT_PATH = Path("campaigns/armindex-multiretriever-v2/evidence/a1.2-scientific-execution-adoption-inputs.receipt.v12-r3.json")
V11_REQUEST_PATH = Path("control/armindex/a1.2/scientific-execution-adoption-request.v11.json")
V11_RECEIPT_PATH = Path("campaigns/armindex-multiretriever-v2/evidence/a1.2-scientific-execution-adoption-request.receipt.v11.json")
V12_CONTRACT_PATH = Path("control/armindex/a1.2/scientific-execution-adoption-inputs.v12.json")
V13_PUBLICATION_PATH = Path("control/armindex/a1.2/publication-impact-contract.v13.json")
V13_DISPOSITION_PATH = Path("control/armindex/a1.2/instance-disposition-policy.v13.json")
OWNER_RECEIPT_CONTRACT_PATH = Path("control/owner-local/a1.2-adoption-input-receipt-contract.v12.json")
COMPILED_BINDINGS_CONTRACT_PATH = Path("control/owner-local/a1.2-compiled-program-bindings-contract.v12.json")
HANDOFF_REQUEST_PATH = Path("control/owner-local/a1.2-evaluator-handoff-request.v11.json")
WORKLOAD_SET_PATH = Path("control/armindex/a1.2/workload-manifest-set.scientific-request.v11.json")

_BUNDLE_PATHS = (
    "campaigns/armindex-multiretriever-v2/evidence/a1.2-scientific-execution-adoption-request.receipt.v11.json",
    "containers/a1_2_vast_4x3090/runtime/requirements.v2.txt",
    "docs/research/A1_2_PUBLICATION_IMPACT_PREREGISTRATION_V13.md",
    "control/armindex/a1.2/aggregate-result-contract.v11.json",
    "control/armindex/a1.2/common-program-set.v11.json",
    "control/armindex/a1.2/instance-disposition-policy.v13.json",
    "control/armindex/a1.2/publication-impact-contract.v13.json",
    "control/armindex/a1.2/scientific-execution-adoption-inputs.v12-r3.json",
    "control/armindex/a1.2/scientific-execution-adoption-inputs.v12.json",
    "control/armindex/a1.2/scientific-execution-adoption-request.v11.json",
    "control/armindex/a1.2/scientific-transfer-contract.v11.json",
    "control/armindex/a1.2/stop-conditions.scientific-request.v11.json",
    "control/armindex/a1.2/watchdog-provider-destroy-dry-run-contract.v12.json",
    "control/armindex/a1.2/workload-manifest-set.scientific-request.v11.json",
    "control/armindex/a1.2/jobs/scientific-request-v11/ARM-01.json",
    "control/armindex/a1.2/jobs/scientific-request-v11/ARM-02.json",
    "control/armindex/a1.2/jobs/scientific-request-v11/ARM-03.json",
    "control/armindex/a1.2/jobs/scientific-request-v11/ARM-04.json",
    "control/armindex/a1.2/jobs/scientific-request-v11/ARM-05.json",
    "control/owner-local/a1.2-adoption-input-receipt-contract.v12.json",
    "control/owner-local/a1.2-compiled-program-bindings-contract.v12.json",
    "pyproject.toml",
    "schemas/armindex/a1.2-compiled-program-binding-set.v12.json",
    "schemas/armindex/a1.2-publication-impact-contract.v13.json",
    "schemas/armindex/a1.2-provider-destroy-readiness.v13.json",
    "schemas/armindex/a1.2-scientific-execution-adoption-inputs-receipt.v12-r3.json",
    "schemas/armindex/a1.2-scientific-execution-adoption-inputs.v12-r3.json",
    "schemas/armindex/a1.2-scientific-execution-bundle-receipt.v12-r3.json",
    "schemas/armindex/a1.2-scientific-execution-pre-adoption-anchor.v12-r3.json",
    "schemas/armindex/a1.2-owner-local-protected-compilation-input.v12.json",
    "schemas/armindex/a1.2-owner-local-protected-compiler-receipt.v12-r3.json",
    "schemas/armindex/a1.2-watchdog-provider-destroy-dry-run-result.v12.json",
    "src/myis_research/armindex/a1_2_compiled_bindings_v12.py",
    "src/myis_research/armindex/a1_2_instance_disposition_v13.py",
    "src/myis_research/armindex/a1_2_owner_local_protected_compiler_v12.py",
    "src/myis_research/armindex/a1_2_publication_impact_v13.py",
    "src/myis_research/armindex/a1_2_scientific_execution_adoption_inputs_v12_r3.py",
    "src/myis_research/armindex/a1_2_watchdog_provider_destroy_dry_run_v12.py",
    "src/myis_research/armindex/scientific_common_programs_v11.py",
    "src/myis_research/kernel/canonical.py",
    "src/myis_research/protection.py",
)
_PATH_SET_SHA256 = "34b2878da7fe382377a81cebc83fc1524dfde439bf0e1ddd9511d29885b96b8b"
_BUNDLE_ALLOWED_SUFFIXES = frozenset({".json", ".jsonl", ".md", ".py", ".toml", ".txt"})
_BUNDLE_MAX_FILE_BYTES = 4 * 1024 * 1024
_HASH = re.compile(r"^[a-f0-9]{64}$")
_GIT = re.compile(r"^[a-f0-9]{40}$")
_FORBIDDEN_PATH_NAME = re.compile(r"(?:qrels?|membership|query[_-]?ids?|credentials?|private[_-]?key|id_ed25519|id_rsa)", re.IGNORECASE)
_SECRET_OR_PATH = re.compile(r"(?:bearer\s+|api[_-]?key|private[_-]?key|password|[A-Za-z]:\\|/Users/|/home/|\\\\[^\\]+\\)", re.IGNORECASE)
_OWNER_SHARED_FIELDS = (
    "handoff_receipt_sha256",
    "protected_transfer_manifest_sha256",
    "corpus_bundle_sha256",
    "query_bundle_sha256",
    "split_commitment_sha256",
    "evaluator_sha256",
    "ephemeral_token_map_sha256",
)


class AdoptionInputsV12R3Error(ValueError):
    """Raised without exposing external Owner-local paths or payloads."""


def _json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AdoptionInputsV12R3Error("required JSON evidence is unavailable or invalid") from error
    if not isinstance(value, dict):
        raise AdoptionInputsV12R3Error("required JSON evidence must be an object")
    return value


def _schema(root: Path, schema_path: Path, value: Mapping[str, Any]) -> None:
    errors = sorted(Draft202012Validator(_load(root / schema_path)).iter_errors(value), key=lambda error: list(error.path))
    if errors:
        raise AdoptionInputsV12R3Error(f"schema validation failed at {list(errors[0].path)}")


def _self_hash(value: Mapping[str, Any], field: str) -> None:
    if value.get(field) != canonical_sha256({key: item for key, item in value.items() if key != field}):
        raise AdoptionInputsV12R3Error(f"{field} self-hash mismatch")


def _safe(value: Mapping[str, Any]) -> None:
    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise AdoptionInputsV12R3Error("protected payload fields are forbidden") from error
    text = json.dumps(value, ensure_ascii=True, sort_keys=True)
    if _SECRET_OR_PATH.search(text):
        raise AdoptionInputsV12R3Error("credential-like material or absolute paths are forbidden")


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", check=False)
    if result.returncode:
        raise AdoptionInputsV12R3Error("Git identity cannot be verified")
    return result.stdout.strip()


def _binding(root: Path, path: Path, self_field: str) -> dict[str, str]:
    value = _load(root / path)
    _safe(value)
    _self_hash(value, self_field)
    return {"uri": path.as_posix(), "file_sha256": file_sha256(root / path), "self_sha256": str(value[self_field])}


def validate_contract(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    value = _load(root / CONTRACT_PATH)
    _schema(root, CONTRACT_SCHEMA_PATH, value)
    _self_hash(value, "contract_sha256")
    _safe(value)
    if value["revision_id"] != REVISION_ID or value["frozen_bundle_path_set_sha256"] != _PATH_SET_SHA256:
        raise AdoptionInputsV12R3Error("V12-R3 contract identity or frozen bundle path set mismatch")
    if value["frozen_bundle_paths"] != list(_BUNDLE_PATHS):
        raise AdoptionInputsV12R3Error("V12-R3 frozen bundle path list mismatch")
    expected = {
        "v11_request": _binding(root, V11_REQUEST_PATH, "request_sha256"),
        "v11_receipt": _binding(root, V11_RECEIPT_PATH, "receipt_sha256"),
        "v12_base": _binding(root, V12_CONTRACT_PATH, "contract_sha256"),
        "publication_v13": _binding(root, V13_PUBLICATION_PATH, "contract_sha256"),
    }
    disposition = _load(root / V13_DISPOSITION_PATH)
    _safe(disposition)
    expected["instance_disposition_v13"] = {
        "uri": V13_DISPOSITION_PATH.as_posix(),
        "file_sha256": file_sha256(root / V13_DISPOSITION_PATH),
        "policy_id": str(disposition.get("policy_id")),
    }
    if value["preserved_bindings"] != expected:
        raise AdoptionInputsV12R3Error("preserved V11/V12/V13 bindings differ")
    if value["authorization"] != {"provider_contact_allowed": False, "launch_allowed": False, "adopted_for_execution": False, "measured_retrieval_allowed": False}:
        raise AdoptionInputsV12R3Error("V12-R3 authorization drift")
    if value["counters"] != {"measured_runs": 0, "selection_accesses": 0, "final_accesses": 0, "charged_usd": 0}:
        raise AdoptionInputsV12R3Error("V12-R3 counters drift")
    return value


def _bundle_paths(root: Path) -> list[str]:
    tracked = set(_git(root, "ls-files").splitlines())
    if set(_BUNDLE_PATHS) - tracked:
        raise AdoptionInputsV12R3Error("frozen R3 bundle contains an untracked or missing required source")
    if canonical_sha256({"paths": list(_BUNDLE_PATHS)}) != _PATH_SET_SHA256:
        raise AdoptionInputsV12R3Error("frozen R3 bundle path set self-check failed")
    for relative in _BUNDLE_PATHS:
        path = root / relative
        try:
            metadata = path.lstat()
            resolved = path.resolve(strict=True)
        except OSError as error:
            raise AdoptionInputsV12R3Error("frozen R3 bundle source cannot be resolved") from error
        if path.is_symlink() or not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1 or not resolved.is_relative_to(root):
            raise AdoptionInputsV12R3Error("frozen R3 bundle source is not a unique in-repository regular file")
        if _FORBIDDEN_PATH_NAME.search(relative):
            raise AdoptionInputsV12R3Error("frozen R3 bundle path resembles protected data or credentials")
        if path.suffix.lower() not in _BUNDLE_ALLOWED_SUFFIXES or metadata.st_size > _BUNDLE_MAX_FILE_BYTES:
            raise AdoptionInputsV12R3Error("frozen R3 bundle source type or size is not allowlisted")
    return list(_BUNDLE_PATHS)


def _member_bytes(archive: tarfile.TarFile, name: str) -> bytes:
    stream = archive.extractfile(name)
    if stream is None:
        raise AdoptionInputsV12R3Error("bundle member cannot be read")
    return stream.read()


def _verify_archive(bundle: Path, *, expected_commit: str, expected_tree: str, contract: Mapping[str, Any]) -> dict[str, Any]:
    try:
        with gzip.open(bundle, "rb") as compressed, tarfile.open(fileobj=compressed, mode="r:") as archive:
            members = archive.getmembers()
            names = [member.name for member in members]
            expected_names = set(_BUNDLE_PATHS) | {"BUNDLE_MANIFEST.json", "GIT_COMMIT", "GIT_TREE"}
            if len(names) != len(set(names)) or set(names) != expected_names:
                raise AdoptionInputsV12R3Error("R3 bundle member closure mismatch")
            if any(not member.isfile() or member.issym() or member.islnk() for member in members):
                raise AdoptionInputsV12R3Error("R3 bundle contains a non-regular member")
            manifest = json.loads(_member_bytes(archive, "BUNDLE_MANIFEST.json").decode("utf-8"))
            if not isinstance(manifest, dict):
                raise AdoptionInputsV12R3Error("R3 bundle manifest is invalid")
            manifest_body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
            if manifest.get("manifest_sha256") != canonical_sha256(manifest_body):
                raise AdoptionInputsV12R3Error("R3 bundle manifest self-hash mismatch")
            if manifest.get("revision_id") != REVISION_ID or manifest.get("git_commit") != expected_commit or manifest.get("git_tree") != expected_tree:
                raise AdoptionInputsV12R3Error("R3 bundle Git binding mismatch")
            if manifest.get("frozen_bundle_path_set_sha256") != _PATH_SET_SHA256 or manifest.get("paths") != list(_BUNDLE_PATHS):
                raise AdoptionInputsV12R3Error("R3 bundle frozen path binding mismatch")
            entries = manifest.get("files")
            if not isinstance(entries, list) or len(entries) != len(_BUNDLE_PATHS):
                raise AdoptionInputsV12R3Error("R3 bundle file manifest is incomplete")
            by_path = {item.get("path"): item for item in entries if isinstance(item, Mapping)}
            if set(by_path) != set(_BUNDLE_PATHS):
                raise AdoptionInputsV12R3Error("R3 bundle file manifest path mismatch")
            for relative in _BUNDLE_PATHS:
                item = by_path[relative]
                data = _member_bytes(archive, relative)
                if item.get("size_bytes") != len(data) or item.get("sha256") != hashlib.sha256(data).hexdigest():
                    raise AdoptionInputsV12R3Error("R3 bundle member hash mismatch")
            if _member_bytes(archive, "GIT_COMMIT").decode("ascii") != expected_commit + "\n" or _member_bytes(archive, "GIT_TREE").decode("ascii") != expected_tree + "\n":
                raise AdoptionInputsV12R3Error("R3 bundle Git metadata mismatch")
            for key, binding in contract["preserved_bindings"].items():
                if key == "instance_disposition_v13":
                    digest = binding["file_sha256"]
                else:
                    digest = binding["file_sha256"]
                if hashlib.sha256(_member_bytes(archive, str(binding["uri"]))).hexdigest() != digest:
                    raise AdoptionInputsV12R3Error("R3 bundle static preserved binding mismatch")
            return manifest
    except (OSError, tarfile.TarError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AdoptionInputsV12R3Error("R3 bundle archive is invalid") from error


def _external_file(path: Path, root: Path) -> Path:
    try:
        resolved = path.resolve(strict=True)
        metadata = path.lstat()
    except OSError as error:
        raise AdoptionInputsV12R3Error("required external evidence is unavailable") from error
    if resolved.is_relative_to(root) or path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        raise AdoptionInputsV12R3Error("external evidence must be a regular file outside the repository")
    return resolved


def _bundle_receipt(root: Path, bundle: Path, receipt_path: Path, contract: Mapping[str, Any]) -> dict[str, Any]:
    receipt = _load(_external_file(receipt_path, root))
    _schema(root, BUNDLE_RECEIPT_SCHEMA_PATH, receipt)
    _self_hash(receipt, "receipt_sha256")
    _safe(receipt)
    if file_sha256(bundle) != receipt["frozen_bundle_sha256"]:
        raise AdoptionInputsV12R3Error("external R3 bundle bytes do not match its receipt")
    manifest = _verify_archive(
        bundle,
        expected_commit=str(receipt["git_commit"]),
        expected_tree=str(receipt["git_tree"]),
        contract=contract,
    )
    if manifest["manifest_sha256"] != receipt["bundle_manifest_sha256"]:
        raise AdoptionInputsV12R3Error("external R3 bundle receipt manifest binding mismatch")
    return receipt


def _anchor(
    root: Path,
    path: Path,
    *,
    contract: Mapping[str, Any],
    bundle_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    value = _load(_external_file(path, root))
    _schema(root, ANCHOR_SCHEMA_PATH, value)
    _self_hash(value, "anchor_sha256")
    _safe(value)
    expected = contract["preserved_bindings"]
    if value["v11_request"] != expected["v11_request"] or value["v11_receipt"] != expected["v11_receipt"] or value["v12_contract"] != expected["v12_base"] or value["publication_v13"] != expected["publication_v13"] or value["instance_disposition_v13"] != expected["instance_disposition_v13"]:
        raise AdoptionInputsV12R3Error("pre-adoption anchor source bindings differ")
    bundle = {key: bundle_receipt[key] for key in ("git_commit", "git_tree", "frozen_bundle_sha256", "bundle_manifest_sha256", "receipt_sha256")}
    if value["execution_bundle"] != bundle:
        raise AdoptionInputsV12R3Error("pre-adoption anchor bundle binding differs")
    if value["authorization"] != contract["authorization"] or value["counters"] != contract["counters"]:
        raise AdoptionInputsV12R3Error("pre-adoption anchor changes authorization or counters")
    return value


def _transfer_manifest(
    root: Path,
    path: Path,
    *,
    owner: Mapping[str, Any],
    anchor: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    resolved = _external_file(path, root)
    value = _load(resolved)
    _safe(value)
    transfer_contract = _load(root / TRANSFER_CONTRACT_PATH)
    required = set(transfer_contract["owner_local_protected_transfer_manifest"]["required_fields"])
    if set(value) != required or value.get("manifest_sha256") != canonical_sha256({key: item for key, item in value.items() if key != "manifest_sha256"}):
        raise AdoptionInputsV12R3Error("protected transfer manifest shape or self-hash mismatch")
    if file_sha256(resolved) != owner["protected_transfer_manifest_sha256"] or value["adoption_receipt_sha256"] != anchor["anchor_sha256"]:
        raise AdoptionInputsV12R3Error("protected transfer manifest does not bind the compiler receipt and pre-adoption anchor")
    shared = {
        "corpus_bundle_sha256": "corpus_bundle_sha256",
        "query_bundle_sha256": "query_bundle_sha256",
        "split_commitment_sha256": "split_commitment_sha256",
        "evaluator_sha256": "evaluator_sha256",
        "ephemeral_token_map_sha256": "ephemeral_token_map_sha256",
    }
    if any(value[field] != owner[owner_field] for field, owner_field in shared.items()):
        raise AdoptionInputsV12R3Error("protected transfer manifest commitments differ from the compiler receipt")
    handoff = _load(root / HANDOFF_REQUEST_PATH)
    workload_set = _load(root / WORKLOAD_SET_PATH)
    if (
        value["request_sha256"] != contract["preserved_bindings"]["v11_request"]["self_sha256"]
        or value["dataset_revision"] != handoff["source_contract"]["dataset_revision"]
        or value["workload_manifest_set_sha256"] != workload_set["manifest_set_sha256"]
        or value["opaque_token_scheme_sha256"] != canonical_sha256(transfer_contract["opaque_token_contract"])
        or value["rep_dev_query_count"] != 150
        or value["harness_dev_reserved_count"] != 100
        or value["expected_result_rows_per_program"] != 150
    ):
        raise AdoptionInputsV12R3Error("protected transfer manifest frozen protocol binding differs")
    return value


def _owner_receipt(root: Path, path: Path) -> dict[str, Any]:
    value = _load(_external_file(path, root))
    _schema(root, COMPILER_RECEIPT_SCHEMA_PATH, value)
    _self_hash(value, "receipt_sha256")
    _safe(value)
    if value["status"] != "PASS" or any(_HASH.fullmatch(str(value[field])) is None for field in (*_OWNER_SHARED_FIELDS, "pre_adoption_anchor_sha256", "binding_set_sha256")):
        raise AdoptionInputsV12R3Error("Owner-local protected compiler receipt status or hashes are invalid")
    if value["binding_count"] != 25 or any(value[field] != 0 for field in ("coverage_gap_count", "omitted_unit_count", "truncation_count", "overlength_count", "measured_runs", "charged_usd")):
        raise AdoptionInputsV12R3Error("Owner-local protected compiler receipt counts are invalid")
    if value["launch_allowed"] is not False or value["adopted_for_execution"] is not False:
        raise AdoptionInputsV12R3Error("Owner-local protected compiler receipt changes authorization")
    return value


def _compiled_bindings(root: Path, path: Path, owner: Mapping[str, Any]) -> Mapping[str, Any]:
    value = _load(_external_file(path, root))
    _safe(value)
    result = validate_binding_set(root, value)
    if result["status"] != "validated_owner_local_protected_compilation" or result["actual_bindings"] != 25:
        raise AdoptionInputsV12R3Error("compiled binding set is not a complete Owner-local 25/25 receipt")
    if value.get("binding_set_sha256") != owner.get("binding_set_sha256"):
        raise AdoptionInputsV12R3Error("compiler receipt does not bind the supplied 25/25 binding set")
    shared = value.get("owner_local_receipts")
    if not isinstance(shared, Mapping) or any(shared.get(key) != owner.get(key) for key in _OWNER_SHARED_FIELDS):
        raise AdoptionInputsV12R3Error("Owner-local protected commitments differ from compiled bindings")
    return value


def _watchdog(root: Path, path: Path) -> Mapping[str, Any]:
    value = _load(_external_file(path, root))
    _safe(value)
    try:
        validate_watchdog_result(root, value)
    except Exception as error:
        raise AdoptionInputsV12R3Error("watchdog destroy dry-run receipt is invalid") from error
    if value.get("policy_file_sha256") != file_sha256(root / WATCHDOG_POLICY_PATH):
        raise AdoptionInputsV12R3Error("watchdog destroy dry-run policy binding mismatch")
    return value


def _write_immutable(path: Path, receipt: Mapping[str, Any]) -> None:
    text = _json(receipt)
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise AdoptionInputsV12R3Error("canonical V12-R3 receipt already exists with different bytes")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as error:
            raise AdoptionInputsV12R3Error("canonical V12-R3 receipt was concurrently published") from error
    finally:
        temporary.unlink(missing_ok=True)


def _temporary_sibling(target: Path) -> Path:
    descriptor, name = tempfile.mkstemp(
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".tmp",
    )
    os.close(descriptor)
    return Path(name)


def _publish_exclusive(source: Path, target: Path) -> None:
    try:
        os.link(source, target)
    except FileExistsError as error:
        raise AdoptionInputsV12R3Error("immutable R3 output already exists") from error
    except OSError as error:
        raise AdoptionInputsV12R3Error("immutable R3 output could not be published") from error


def build_bundle(repository_root: Path, output: Path, *, receipt_output: Path) -> dict[str, Any]:
    """Build an immutable deterministic R3 bundle and external receipt."""

    root = repository_root.resolve()
    contract = validate_contract(root)
    target = output.resolve()
    receipt_target = receipt_output.resolve()
    if target.is_relative_to(root) or receipt_target.is_relative_to(root) or target == receipt_target:
        raise AdoptionInputsV12R3Error("bundle and receipt outputs must be distinct external paths")
    if target.exists() or receipt_target.exists():
        raise AdoptionInputsV12R3Error("immutable R3 bundle output already exists")
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise AdoptionInputsV12R3Error("repository must be clean before R3 bundle creation")
    commit = _git(root, "rev-parse", "HEAD^{commit}")
    tree = _git(root, "rev-parse", "HEAD^{tree}")
    if _git(root, "rev-parse", "origin/main") != commit or _GIT.fullmatch(commit) is None or _GIT.fullmatch(tree) is None:
        raise AdoptionInputsV12R3Error("R3 bundle requires a clean pushed Git commit and tree")
    paths = _bundle_paths(root)
    entries = [{"path": path, "size_bytes": (root / path).stat().st_size, "sha256": file_sha256(root / path)} for path in paths]
    manifest_body = {
        "schema_version": "myis.armindex-a1.2-scientific-execution-bundle.v12-r3",
        "revision_id": REVISION_ID,
        "git_commit": commit,
        "git_tree": tree,
        "paths": paths,
        "frozen_bundle_path_set_sha256": _PATH_SET_SHA256,
        "files": entries,
        "model_bytes_included": False,
        "protected_payload_included": False,
        "static_v11_bindings_only": True,
    }
    manifest = {**manifest_body, "manifest_sha256": canonical_sha256(manifest_body)}
    metadata = {"BUNDLE_MANIFEST.json": _json(manifest), "GIT_COMMIT": commit + "\n", "GIT_TREE": tree + "\n"}
    target.parent.mkdir(parents=True, exist_ok=True)
    receipt_target.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary_sibling(target)
    temporary_receipt: Path | None = None
    published: list[Path] = []
    try:
        with temporary.open("wb") as raw, gzip.GzipFile(
            fileobj=raw,
            mode="wb",
            mtime=0,
            filename="",
        ) as compressed, tarfile.open(fileobj=compressed, mode="w") as archive:
            for relative in paths:
                source = root / relative
                info = tarfile.TarInfo(relative)
                info.size = source.stat().st_size
                info.mtime = 0
                info.mode = 0o644
                with source.open("rb") as handle:
                    archive.addfile(info, handle)
            for member_name, text in sorted(metadata.items()):
                data = text.encode("utf-8")
                info = tarfile.TarInfo(member_name)
                info.size = len(data)
                info.mtime = 0
                info.mode = 0o644
                archive.addfile(info, BytesIO(data))
        _verify_archive(temporary, expected_commit=commit, expected_tree=tree, contract=contract)
        if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
            raise AdoptionInputsV12R3Error("repository changed during R3 bundle creation")
        body = {
            "schema_version": "myis.armindex-a1.2-scientific-execution-bundle-receipt.v12-r3",
            "revision_id": REVISION_ID,
            "clean_worktree": True,
            "pushed_to_origin_main": True,
            "git_commit": commit,
            "git_tree": tree,
            "frozen_bundle_sha256": file_sha256(temporary),
            "bundle_manifest_sha256": manifest["manifest_sha256"],
            "frozen_bundle_path_set_sha256": _PATH_SET_SHA256,
        }
        receipt = {**body, "receipt_sha256": canonical_sha256(body)}
        _schema(root, BUNDLE_RECEIPT_SCHEMA_PATH, receipt)
        temporary_receipt = _temporary_sibling(receipt_target)
        temporary_receipt.write_text(_json(receipt), encoding="utf-8", newline="")
        _publish_exclusive(temporary, target)
        published.append(target)
        _publish_exclusive(temporary_receipt, receipt_target)
        published.append(receipt_target)
        if file_sha256(target) != receipt["frozen_bundle_sha256"] or receipt_target.read_text(encoding="utf-8") != _json(receipt):
            raise AdoptionInputsV12R3Error("published R3 bundle outputs failed verification")
    except Exception:
        for path in reversed(published):
            path.unlink(missing_ok=True)
        raise
    finally:
        if temporary_receipt is not None:
            temporary_receipt.unlink(missing_ok=True)
        temporary.unlink(missing_ok=True)
    return {"status": "PASS", "bundle_sha256": receipt["frozen_bundle_sha256"], "bundle_manifest_sha256": manifest["manifest_sha256"], "file_count": len(paths), "launch_allowed": False, "adopted_for_execution": False, "measured_runs": 0, "charged_usd": 0}


def build_anchor(
    repository_root: Path,
    *,
    bundle_path: Path,
    bundle_receipt_path: Path,
    output: Path,
) -> dict[str, Any]:
    """Publish an immutable non-authorizing anchor before protected transfer."""

    root = repository_root.resolve()
    contract = validate_contract(root)
    target = output.resolve()
    if target.is_relative_to(root) or target.is_symlink():
        raise AdoptionInputsV12R3Error("pre-adoption anchor output must be outside the repository")
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise AdoptionInputsV12R3Error("repository must be clean before pre-adoption anchor creation")
    bundle = _external_file(bundle_path, root)
    bundle_receipt = _bundle_receipt(root, bundle, bundle_receipt_path, contract)
    if _git(root, "rev-parse", "HEAD^{commit}") != bundle_receipt["git_commit"] or _git(root, "rev-parse", "HEAD^{tree}") != bundle_receipt["git_tree"] or _git(root, "rev-parse", "origin/main") != bundle_receipt["git_commit"]:
        raise AdoptionInputsV12R3Error("pre-adoption anchor requires the current clean pushed bundle identity")
    preserved = contract["preserved_bindings"]
    body = {
        "schema_version": "myis.armindex-a1.2-scientific-execution-pre-adoption-anchor.v12-r3",
        "anchor_id": f"a1.2-pre-adoption-anchor-{bundle_receipt['git_commit'][:12]}-v12-r3",
        "revision_id": REVISION_ID,
        "status": "PRE_ADOPTION_INPUT_ANCHOR",
        "claim_boundary": "Immutable aggregate-safe pre-adoption input anchor for unchanged V11 and the clean R3 bundle. It resolves transfer lineage without adopting execution and does not authorize provider contact, launch, retrieval, Selection, Final, paid APIs, or scientific claims.",
        "v11_request": preserved["v11_request"],
        "v11_receipt": preserved["v11_receipt"],
        "v12_contract": preserved["v12_base"],
        "publication_v13": preserved["publication_v13"],
        "instance_disposition_v13": preserved["instance_disposition_v13"],
        "execution_bundle": {key: bundle_receipt[key] for key in ("git_commit", "git_tree", "frozen_bundle_sha256", "bundle_manifest_sha256", "receipt_sha256")},
        "authorization": contract["authorization"],
        "counters": contract["counters"],
    }
    anchor = {**body, "anchor_sha256": canonical_sha256(body)}
    _schema(root, ANCHOR_SCHEMA_PATH, anchor)
    _safe(anchor)
    _write_immutable(target, anchor)
    return {"status": "PASS", "anchor_sha256": anchor["anchor_sha256"], "anchor_file_sha256": file_sha256(target), "launch_allowed": False, "adopted_for_execution": False, "measured_runs": 0, "charged_usd": 0}


def finalize(
    repository_root: Path,
    *,
    bundle_path: Path,
    bundle_receipt_path: Path,
    pre_adoption_anchor_path: Path,
    owner_receipt_path: Path,
    binding_set_path: Path,
    transfer_manifest_path: Path,
    watchdog_receipt_path: Path,
) -> dict[str, Any]:
    """Validate external V12-R3 evidence and atomically publish the canonical receipt."""

    root = repository_root.resolve()
    contract = validate_contract(root)
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise AdoptionInputsV12R3Error("repository must be clean before canonical V12-R3 receipt publication")
    bundle = _external_file(bundle_path, root)
    bundle_receipt = _bundle_receipt(root, bundle, bundle_receipt_path, contract)
    if _git(root, "rev-parse", "HEAD^{commit}") != bundle_receipt["git_commit"] or _git(root, "rev-parse", "HEAD^{tree}") != bundle_receipt["git_tree"] or _git(root, "rev-parse", "origin/main") != bundle_receipt["git_commit"]:
        raise AdoptionInputsV12R3Error("R3 bundle is not bound to the current clean pushed repository identity")
    anchor_path = _external_file(pre_adoption_anchor_path, root)
    anchor = _anchor(root, anchor_path, contract=contract, bundle_receipt=bundle_receipt)
    owner = _owner_receipt(root, owner_receipt_path)
    if file_sha256(anchor_path) != owner["pre_adoption_anchor_sha256"]:
        raise AdoptionInputsV12R3Error("protected compiler receipt does not bind the supplied pre-adoption anchor bytes")
    bindings = _compiled_bindings(root, binding_set_path, owner)
    transfer = _transfer_manifest(root, transfer_manifest_path, owner=owner, anchor=anchor, contract=contract)
    watchdog = _watchdog(root, watchdog_receipt_path)
    body = {
        "schema_version": "myis.armindex-a1.2-scientific-execution-adoption-inputs-receipt.v12-r3",
        "receipt_id": REVISION_ID,
        "revision_id": REVISION_ID,
        "status": "LOCAL_INPUTS_VALIDATED_PENDING_LIVE_PROVIDER",
        "evidence_class": "scientific_execution_adoption_input_preparation",
        "scientific_authority": False,
        "claim_boundary": "Aggregate-safe V12-R3 local closure for the unchanged V11 request. It verifies external Owner-local evidence but does not contact a provider, admit a quote, adopt execution, launch, measure retrieval, open Selection or Final, or make a scientific/publication claim.",
        "contract": {"uri": CONTRACT_PATH.as_posix(), "file_sha256": file_sha256(root / CONTRACT_PATH), "contract_sha256": contract["contract_sha256"]},
        "execution_bundle": {key: bundle_receipt[key] for key in ("git_commit", "git_tree", "frozen_bundle_sha256", "bundle_manifest_sha256", "receipt_sha256")},
        "pre_adoption_anchor": {"anchor_file_sha256": owner["pre_adoption_anchor_sha256"], "anchor_sha256": anchor["anchor_sha256"]},
        "protected_transfer": {"transfer_file_sha256": owner["protected_transfer_manifest_sha256"], "manifest_sha256": transfer["manifest_sha256"]},
        "owner_local_receipt": {key: owner[key] for key in (*_OWNER_SHARED_FIELDS, "pre_adoption_anchor_sha256", "receipt_sha256")},
        "compiled_bindings": {"binding_set_sha256": bindings["binding_set_sha256"], "binding_count": 25, "coverage_gap_count": 0, "omitted_unit_count": 0, "truncation_count": 0, "overlength_count": 0},
        "watchdog_destroy_dry_run": {"receipt_sha256": watchdog["receipt_sha256"], "target_instance_identity_sha256": watchdog["target_instance_identity_sha256"], "actual_provider_destroy_capability": "PENDING_LIVE_PROVIDER"},
        "pending_live_provider": ["fresh_provider_identity", "fresh_all_fee_quote", "whole_workload_live_budget_admission", "live_provider_admission_receipt"],
        "ready_for_live_adoption_goal": True,
        "authorization": {"provider_contact_allowed": False, "launch_allowed": False, "adopted_for_execution": False, "measured_retrieval_allowed": False},
        "counters": {"measured_runs": 0, "selection_accesses": 0, "final_accesses": 0, "charged_usd": 0},
        "next_authorized_action": "A separately authorized live-adoption goal may obtain a fresh provider identity and all-fee quote, evaluate whole-workload budget admission, and retain every execution authority lock until explicit Owner adoption succeeds.",
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _schema(root, RECEIPT_SCHEMA_PATH, receipt)
    _self_hash(receipt, "receipt_sha256")
    _safe(receipt)
    _write_immutable(root / RECEIPT_PATH, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-scientific-adoption-inputs-v12-r3")
    parser.add_argument("command", choices=("validate", "build-bundle", "build-anchor", "finalize"))
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--receipt-output", type=Path)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--bundle-receipt", type=Path)
    parser.add_argument("--pre-adoption-anchor", type=Path)
    parser.add_argument("--owner-receipt", type=Path)
    parser.add_argument("--binding-set", type=Path)
    parser.add_argument("--transfer-manifest", type=Path)
    parser.add_argument("--watchdog-receipt", type=Path)
    args = parser.parse_args()
    if args.command == "validate":
        contract = validate_contract(args.repository_root)
        result: Mapping[str, Any] = {"status": "PASS", "revision_id": REVISION_ID, "contract_sha256": contract["contract_sha256"], "launch_allowed": False, "adopted_for_execution": False, "measured_runs": 0, "charged_usd": 0}
    elif args.command == "build-bundle":
        if args.output is None or args.receipt_output is None:
            parser.error("build-bundle requires --output and --receipt-output")
        result = build_bundle(args.repository_root, args.output, receipt_output=args.receipt_output)
    elif args.command == "build-anchor":
        if args.output is None or args.bundle is None or args.bundle_receipt is None:
            parser.error("build-anchor requires --bundle, --bundle-receipt, and --output")
        result = build_anchor(args.repository_root, bundle_path=args.bundle, bundle_receipt_path=args.bundle_receipt, output=args.output)
    else:
        required = (args.bundle, args.bundle_receipt, args.pre_adoption_anchor, args.owner_receipt, args.binding_set, args.transfer_manifest, args.watchdog_receipt)
        if any(item is None for item in required):
            parser.error("finalize requires bundle, anchor, protected transfer, compiler, binding-set, and watchdog receipts")
        result = finalize(args.repository_root, bundle_path=args.bundle, bundle_receipt_path=args.bundle_receipt, pre_adoption_anchor_path=args.pre_adoption_anchor, owner_receipt_path=args.owner_receipt, binding_set_path=args.binding_set, transfer_manifest_path=args.transfer_manifest, watchdog_receipt_path=args.watchdog_receipt)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
