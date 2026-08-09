"""Additive local-only A1.2 v15 adoption-input finalizer.

The finalizer binds the clean pushed execution bundle to validated Owner-local
protected compiler evidence and synthetic control-path evidence. It never
contacts a provider and cannot authorize execution.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
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
from . import a1_2_owner_local_protected_compiler_v15 as compiler
from .a1_2_scientific_execution_adoption_inputs_v12_r3 import (
    _BUNDLE_PATHS as V12_R3_BUNDLE_PATHS,
)
from .a1_2_watchdog_provider_destroy_dry_run_v12 import (
    _validate_result as validate_watchdog_result,
)
from .a1_2_whole_workload_budget_model_v15 import (
    validate_contract as validate_budget_model,
)

REVISION_ID = "a1.2-scientific-execution-adoption-inputs-v15"
CONTRACT_PATH = Path(
    "control/armindex/a1.2/scientific-execution-adoption-inputs.v15.json"
)
CONTRACT_SCHEMA_PATH = Path(
    "schemas/armindex/a1.2-scientific-execution-adoption-inputs.v15.json"
)
BUNDLE_SCHEMA_PATH = Path(
    "schemas/armindex/a1.2-scientific-execution-bundle-receipt.v15.json"
)
ANCHOR_SCHEMA_PATH = Path(
    "schemas/armindex/a1.2-scientific-execution-pre-adoption-anchor.v15.json"
)
RECEIPT_SCHEMA_PATH = Path(
    "schemas/armindex/a1.2-scientific-execution-adoption-inputs-receipt.v15.json"
)
RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/a1.2-scientific-execution-adoption-inputs.receipt.v15.json"
)
COMPILER_AUDIT_PATH = Path(
    "outputs/audits/armindex/a1.2-protected-compiler-integration-20260809-v15.json"
)
V13_PATH = Path("control/armindex/a1.2/publication-impact-contract.v13.json")
PENDING_LIVE_PROVIDER = [
    "fresh_provider_identity",
    "fresh_all_fee_quote",
    "whole_workload_live_budget_admission",
    "live_provider_admission_receipt",
]
AUTHORIZATION = {
    "provider_contact_allowed": False,
    "launch_allowed": False,
    "adopted_for_execution": False,
    "measured_retrieval_allowed": False,
    "selection_allowed": False,
    "final_allowed": False,
    "paid_api_allowed": False,
}
COUNTERS = {
    "measured_runs": 0,
    "selection_accesses": 0,
    "final_accesses": 0,
    "charged_usd": 0,
}

_V15_PATHS = (
    "control/armindex/a1.2/dense-overflow-adapter-repair.v14.json",
    "control/armindex/a1.2/p02-first-claim-repair.v1.json",
    "control/armindex/a1.2/protected-compiler-integration.v15.json",
    "control/armindex/a1.2/rep-harness-split-decision.v1.json",
    CONTRACT_PATH.as_posix(),
    "control/armindex/a1.2/whole-workload-budget-model.v15.json",
    "outputs/audits/armindex/a1.2-dense-overflow-composition-20260808.json",
    "outputs/audits/armindex/a1.2-dense-overflow-inventory-20260808.json",
    COMPILER_AUDIT_PATH.as_posix(),
    "outputs/figures/armindex/a1.2-dense-overflow-eda-v1.png",
    "outputs/figures/armindex/a1.2-dense-overflow-eda-v1.svg",
    "outputs/fixtures/armindex/a1.2/watchdog-provider-destroy-dry-run-input.v15.json",
    "schemas/armindex/a1.2-compiled-program-binding-set.v15.json",
    "schemas/armindex/a1.2-dense-overflow-adapter-repair.v14.json",
    "schemas/armindex/a1.2-owner-local-protected-compilation-input.v15.json",
    "schemas/armindex/a1.2-owner-local-protected-compiler-receipt.v15.json",
    "schemas/armindex/a1.2-protected-compiler-integration-audit.v15.json",
    "schemas/armindex/a1.2-protected-compiler-integration.v15.json",
    ANCHOR_SCHEMA_PATH.as_posix(),
    BUNDLE_SCHEMA_PATH.as_posix(),
    RECEIPT_SCHEMA_PATH.as_posix(),
    CONTRACT_SCHEMA_PATH.as_posix(),
    "schemas/armindex/a1.2-whole-workload-budget-model.v15.json",
    "src/myis_research/armindex/a1_2_dense_overflow_adapter_v1.py",
    "src/myis_research/armindex/a1_2_dense_overflow_composition_audit_v1.py",
    "src/myis_research/armindex/a1_2_dense_overflow_contract_v14.py",
    "src/myis_research/armindex/a1_2_dense_overflow_inventory_v1.py",
    "src/myis_research/armindex/a1_2_owner_local_protected_compiler_v15.py",
    "src/myis_research/armindex/a1_2_owner_local_protected_materializer_v15.py",
    "src/myis_research/armindex/a1_2_protected_compiler_integration_audit_v15.py",
    "src/myis_research/armindex/a1_2_scientific_execution_adoption_inputs_v15.py",
    "src/myis_research/armindex/a1_2_whole_workload_budget_model_v15.py",
)
BUNDLE_PATHS = tuple(dict.fromkeys((*V12_R3_BUNDLE_PATHS, *_V15_PATHS)))
BUNDLE_PATH_SET_SHA256 = canonical_sha256({"paths": list(BUNDLE_PATHS)})
_ALLOWED_SUFFIXES = frozenset(
    {".json", ".jsonl", ".md", ".png", ".py", ".svg", ".toml", ".txt"}
)
_MAX_FILE_BYTES = 8 * 1024 * 1024


class AdoptionInputsV15Error(ValueError):
    """Fail-closed additive finalizer error."""


def _json(value: Mapping[str, Any]) -> str:
    return (
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + "\n"
    )


def _load(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AdoptionInputsV15Error(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise AdoptionInputsV15Error(f"{role} must be an object")
    return value


def _schema(root: Path, path: Path, value: Mapping[str, Any], *, role: str) -> None:
    errors = sorted(
        Draft202012Validator(_load(root / path, role=f"{role} schema")).iter_errors(
            value
        ),
        key=lambda item: list(item.path),
    )
    if errors:
        raise AdoptionInputsV15Error(f"{role} schema failure at {list(errors[0].path)}")


def _self_hash(value: Mapping[str, Any], field: str) -> str:
    return canonical_sha256({key: item for key, item in value.items() if key != field})


def _validate_self_hash(value: Mapping[str, Any], field: str, *, role: str) -> None:
    if value.get(field) != _self_hash(value, field):
        raise AdoptionInputsV15Error(f"{role} self-hash mismatch")


def _safe(value: Mapping[str, Any], *, role: str) -> None:
    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise AdoptionInputsV15Error(
            f"{role} crosses the protected boundary"
        ) from error


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode:
        raise AdoptionInputsV15Error("Git identity cannot be verified")
    return result.stdout.strip()


def _external(path: Path, root: Path, *, role: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
        metadata = path.lstat()
    except OSError as error:
        raise AdoptionInputsV15Error(f"{role} is unavailable") from error
    if (
        path.is_symlink()
        or not stat.S_ISREG(metadata.st_mode)
        or resolved.is_relative_to(root)
    ):
        raise AdoptionInputsV15Error(f"{role} must be an external regular file")
    return resolved


def validate_contract(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    value = _load(root / CONTRACT_PATH, role="v15 adoption contract")
    _schema(root, CONTRACT_SCHEMA_PATH, value, role="v15 adoption contract")
    _validate_self_hash(value, "contract_sha256", role="v15 adoption contract")
    _safe(value, role="v15 adoption contract")
    if value["pending_live_provider"] != PENDING_LIVE_PROVIDER:
        raise AdoptionInputsV15Error("live-provider inputs must remain pending")
    if value["authorization"] != AUTHORIZATION or value["counters"] != COUNTERS:
        raise AdoptionInputsV15Error("v15 authorization or counters drift")
    integration = compiler._validate_integration(root)
    if integration["authorization"] != AUTHORIZATION:
        raise AdoptionInputsV15Error("compiler integration authorization drift")
    return value


def _bundle_sources(root: Path) -> list[str]:
    tracked = set(_git(root, "ls-files").splitlines())
    missing = set(BUNDLE_PATHS) - tracked
    if missing:
        raise AdoptionInputsV15Error("v15 bundle contains untracked or missing sources")
    for relative in BUNDLE_PATHS:
        path = root / relative
        metadata = path.lstat()
        if (
            path.is_symlink()
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
        ):
            raise AdoptionInputsV15Error(
                "v15 bundle source is not a unique regular file"
            )
        if (
            path.suffix.lower() not in _ALLOWED_SUFFIXES
            or metadata.st_size > _MAX_FILE_BYTES
        ):
            raise AdoptionInputsV15Error(
                "v15 bundle source type or size is not allowlisted"
            )
        if not path.resolve(strict=True).is_relative_to(root):
            raise AdoptionInputsV15Error("v15 bundle source escapes the repository")
    return list(BUNDLE_PATHS)


def _member_bytes(archive: tarfile.TarFile, name: str) -> bytes:
    stream = archive.extractfile(name)
    if stream is None:
        raise AdoptionInputsV15Error("bundle member cannot be read")
    return stream.read()


def _verify_bundle(path: Path, receipt: Mapping[str, Any]) -> dict[str, Any]:
    try:
        with (
            gzip.open(path, "rb") as compressed,
            tarfile.open(fileobj=compressed, mode="r:") as archive,
        ):
            members = archive.getmembers()
            names = [item.name for item in members]
            expected = set(BUNDLE_PATHS) | {
                "BUNDLE_MANIFEST.json",
                "GIT_COMMIT",
                "GIT_TREE",
            }
            if set(names) != expected or len(names) != len(set(names)):
                raise AdoptionInputsV15Error("v15 bundle member closure mismatch")
            if any(
                not item.isfile() or item.issym() or item.islnk() for item in members
            ):
                raise AdoptionInputsV15Error("v15 bundle contains non-regular members")
            manifest = json.loads(
                _member_bytes(archive, "BUNDLE_MANIFEST.json").decode("utf-8")
            )
            if not isinstance(manifest, dict):
                raise AdoptionInputsV15Error("v15 bundle manifest is invalid")
            _validate_self_hash(manifest, "manifest_sha256", role="v15 bundle manifest")
            if (
                manifest.get("paths") != list(BUNDLE_PATHS)
                or manifest.get("frozen_bundle_path_set_sha256")
                != BUNDLE_PATH_SET_SHA256
            ):
                raise AdoptionInputsV15Error("v15 bundle path-set binding mismatch")
            if (
                manifest.get("git_commit") != receipt["git_commit"]
                or manifest.get("git_tree") != receipt["git_tree"]
            ):
                raise AdoptionInputsV15Error("v15 bundle Git binding mismatch")
            files = manifest.get("files")
            if not isinstance(files, list) or len(files) != len(BUNDLE_PATHS):
                raise AdoptionInputsV15Error("v15 bundle file manifest is incomplete")
            indexed = {
                item.get("path"): item for item in files if isinstance(item, Mapping)
            }
            if set(indexed) != set(BUNDLE_PATHS):
                raise AdoptionInputsV15Error("v15 bundle file path mismatch")
            for relative in BUNDLE_PATHS:
                data = _member_bytes(archive, relative)
                item = indexed[relative]
                if (
                    item.get("size_bytes") != len(data)
                    or item.get("sha256") != hashlib.sha256(data).hexdigest()
                ):
                    raise AdoptionInputsV15Error("v15 bundle member hash mismatch")
            if (
                _member_bytes(archive, "GIT_COMMIT").decode("ascii")
                != receipt["git_commit"] + "\n"
            ):
                raise AdoptionInputsV15Error("v15 bundle commit marker mismatch")
            if (
                _member_bytes(archive, "GIT_TREE").decode("ascii")
                != receipt["git_tree"] + "\n"
            ):
                raise AdoptionInputsV15Error("v15 bundle tree marker mismatch")
            return manifest
    except (OSError, UnicodeError, json.JSONDecodeError, tarfile.TarError) as error:
        raise AdoptionInputsV15Error("v15 bundle is invalid") from error


def _write_immutable(path: Path, value: Mapping[str, Any]) -> None:
    text = _json(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_text(encoding="utf-8") != text:
            raise AdoptionInputsV15Error(
                "immutable output already exists with different bytes"
            )
        return
    descriptor, name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def build_bundle(
    repository_root: Path, *, output: Path, receipt_output: Path
) -> dict[str, Any]:
    root = repository_root.resolve()
    validate_contract(root)
    target = output.resolve()
    receipt_target = receipt_output.resolve()
    if (
        target.is_relative_to(root)
        or receipt_target.is_relative_to(root)
        or target == receipt_target
    ):
        raise AdoptionInputsV15Error("bundle outputs must be distinct external paths")
    if target.exists() or receipt_target.exists():
        raise AdoptionInputsV15Error("immutable bundle output already exists")
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise AdoptionInputsV15Error("repository must be clean before bundle creation")
    commit = _git(root, "rev-parse", "HEAD^{commit}")
    tree = _git(root, "rev-parse", "HEAD^{tree}")
    if _git(root, "rev-parse", "origin/main") != commit:
        raise AdoptionInputsV15Error("bundle requires a clean pushed main commit")
    paths = _bundle_sources(root)
    files = [
        {
            "path": relative,
            "size_bytes": (root / relative).stat().st_size,
            "sha256": file_sha256(root / relative),
        }
        for relative in paths
    ]
    manifest_body = {
        "schema_version": "myis.armindex-a1.2-scientific-execution-bundle.v15",
        "revision_id": REVISION_ID,
        "git_commit": commit,
        "git_tree": tree,
        "paths": paths,
        "frozen_bundle_path_set_sha256": BUNDLE_PATH_SET_SHA256,
        "files": files,
        "model_bytes_included": False,
        "protected_payload_included": False,
        "provider_input_included": False,
    }
    manifest = {**manifest_body, "manifest_sha256": canonical_sha256(manifest_body)}
    metadata = {
        "BUNDLE_MANIFEST.json": _json(manifest),
        "GIT_COMMIT": commit + "\n",
        "GIT_TREE": tree + "\n",
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    receipt_target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(
        dir=target.parent, prefix=f".{target.name}.", suffix=".tmp"
    )
    os.close(descriptor)
    temporary = Path(name)
    try:
        with (
            temporary.open("wb") as raw,
            gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as compressed,
            tarfile.open(fileobj=compressed, mode="w") as archive,
        ):
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
        body = {
            "schema_version": "myis.armindex-a1.2-scientific-execution-bundle-receipt.v15",
            "revision_id": REVISION_ID,
            "clean_worktree": True,
            "pushed_to_origin_main": True,
            "git_commit": commit,
            "git_tree": tree,
            "frozen_bundle_sha256": file_sha256(temporary),
            "bundle_manifest_sha256": manifest["manifest_sha256"],
            "frozen_bundle_path_set_sha256": BUNDLE_PATH_SET_SHA256,
        }
        receipt = {**body, "receipt_sha256": canonical_sha256(body)}
        _schema(root, BUNDLE_SCHEMA_PATH, receipt, role="v15 bundle receipt")
        _verify_bundle(temporary, receipt)
        _write_immutable(receipt_target, receipt)
        os.link(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return {
        "status": "PASS",
        "bundle_sha256": receipt["frozen_bundle_sha256"],
        "bundle_manifest_sha256": manifest["manifest_sha256"],
        "file_count": len(paths),
        "git_commit": commit,
        "git_tree": tree,
    }


def _bundle_receipt(
    root: Path, bundle_path: Path, receipt_path: Path
) -> dict[str, Any]:
    bundle = _external(bundle_path, root, role="v15 bundle")
    receipt_file = _external(receipt_path, root, role="v15 bundle receipt")
    receipt = _load(receipt_file, role="v15 bundle receipt")
    _schema(root, BUNDLE_SCHEMA_PATH, receipt, role="v15 bundle receipt")
    _validate_self_hash(receipt, "receipt_sha256", role="v15 bundle receipt")
    if file_sha256(bundle) != receipt["frozen_bundle_sha256"]:
        raise AdoptionInputsV15Error("v15 bundle bytes differ from receipt")
    manifest = _verify_bundle(bundle, receipt)
    if manifest["manifest_sha256"] != receipt["bundle_manifest_sha256"]:
        raise AdoptionInputsV15Error("v15 bundle manifest binding mismatch")
    return receipt


def build_anchor(
    repository_root: Path, *, bundle_path: Path, bundle_receipt_path: Path, output: Path
) -> dict[str, Any]:
    root = repository_root.resolve()
    validate_contract(root)
    target = output.resolve()
    if target.is_relative_to(root):
        raise AdoptionInputsV15Error("pre-adoption anchor must remain external")
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise AdoptionInputsV15Error("repository must be clean before anchor creation")
    receipt = _bundle_receipt(root, bundle_path, bundle_receipt_path)
    if (
        _git(root, "rev-parse", "HEAD^{commit}") != receipt["git_commit"]
        or _git(root, "rev-parse", "origin/main") != receipt["git_commit"]
    ):
        raise AdoptionInputsV15Error(
            "anchor requires the current clean pushed bundle commit"
        )
    body = {
        "schema_version": "myis.armindex-a1.2-scientific-execution-pre-adoption-anchor.v15",
        "anchor_id": f"a1.2-pre-adoption-anchor-{receipt['git_commit'][:12]}-v15",
        "revision_id": REVISION_ID,
        "status": "PRE_ADOPTION_INPUT_ANCHOR_V15",
        "claim_boundary": "Immutable aggregate-safe clean-bundle anchor for additive v15 local adoption-input closure. It authorizes no provider contact, quote, live budget admission, launch, measured retrieval, Selection, Final, paid API, or scientific/publication claim.",
        "execution_bundle": {
            key: receipt[key]
            for key in (
                "git_commit",
                "git_tree",
                "frozen_bundle_sha256",
                "bundle_manifest_sha256",
                "receipt_sha256",
            )
        },
        "authorization": AUTHORIZATION,
        "counters": COUNTERS,
    }
    anchor = {**body, "anchor_sha256": canonical_sha256(body)}
    _schema(root, ANCHOR_SCHEMA_PATH, anchor, role="v15 pre-adoption anchor")
    _safe(anchor, role="v15 pre-adoption anchor")
    _write_immutable(target, anchor)
    return {
        "status": "PASS",
        "anchor_sha256": anchor["anchor_sha256"],
        "anchor_file_sha256": file_sha256(target),
    }


def _validate_protected(
    root: Path,
    *,
    handoff_path: Path,
    transfer_path: Path,
    pre_compilation_anchor_path: Path,
    compiler_receipt_path: Path,
    binding_set_path: Path,
) -> dict[str, Any]:
    paths = {
        "handoff": _external(handoff_path, root, role="protected handoff"),
        "transfer": _external(transfer_path, root, role="protected transfer"),
        "pre_compilation_anchor": _external(
            pre_compilation_anchor_path, root, role="pre-compilation anchor"
        ),
        "compiler_receipt": _external(
            compiler_receipt_path, root, role="compiler receipt"
        ),
        "bindings": _external(binding_set_path, root, role="binding set"),
    }
    values = {key: _load(path, role=key) for key, path in paths.items()}
    _validate_self_hash(values["handoff"], "receipt_sha256", role="protected handoff")
    _validate_self_hash(
        values["transfer"], "manifest_sha256", role="protected transfer"
    )
    _validate_self_hash(
        values["pre_compilation_anchor"], "anchor_sha256", role="pre-compilation anchor"
    )
    compiler.validate_receipt(root, values["compiler_receipt"])
    compiler.validate_binding_set(root, values["bindings"])
    receipt = values["compiler_receipt"]
    if receipt["handoff_receipt_sha256"] != file_sha256(paths["handoff"]):
        raise AdoptionInputsV15Error("compiler receipt handoff binding mismatch")
    if receipt["protected_transfer_manifest_sha256"] != file_sha256(paths["transfer"]):
        raise AdoptionInputsV15Error("compiler receipt transfer binding mismatch")
    if receipt["pre_compilation_anchor_sha256"] != file_sha256(
        paths["pre_compilation_anchor"]
    ):
        raise AdoptionInputsV15Error("compiler receipt pre-compilation anchor mismatch")
    if receipt["binding_set_sha256"] != values["bindings"]["binding_set_sha256"]:
        raise AdoptionInputsV15Error("compiler receipt binding-set mismatch")
    if (
        values["transfer"].get("adoption_receipt_sha256")
        != values["pre_compilation_anchor"]["anchor_sha256"]
    ):
        raise AdoptionInputsV15Error(
            "protected transfer pre-compilation anchor mismatch"
        )
    shared = {
        "corpus_bundle_sha256": "corpus_bundle_sha256",
        "query_bundle_sha256": "query_bundle_sha256",
        "split_commitment_sha256": "split_commitment_sha256",
        "evaluator_sha256": "evaluator_sha256",
        "ephemeral_token_map_sha256": "ephemeral_token_map_sha256",
    }
    if any(
        values["handoff"][left] != receipt[right]
        or values["transfer"][left] != receipt[right]
        for left, right in shared.items()
    ):
        raise AdoptionInputsV15Error(
            "protected handoff/transfer/compiler commitments differ"
        )
    if (
        values["handoff"].get("corpus_count") != 45336
        or values["handoff"].get("query_count") != 150
    ):
        raise AdoptionInputsV15Error("protected workload counts differ")
    audit = _load(root / COMPILER_AUDIT_PATH, role="compiler integration audit")
    if audit.get("protected_receipts", {}).get(
        "binding_set_file_sha256"
    ) != file_sha256(paths["bindings"]):
        raise AdoptionInputsV15Error(
            "repository compiler audit binding-set bytes differ"
        )
    if audit.get("protected_receipts", {}).get(
        "compiler_receipt_file_sha256"
    ) != file_sha256(paths["compiler_receipt"]):
        raise AdoptionInputsV15Error("repository compiler audit receipt bytes differ")
    return {"paths": paths, "values": values}


def _publication_outcomes(publication: Mapping[str, Any]) -> dict[str, Any]:
    """Validate frozen V13 metric IDs and return safe publication labels."""
    outcomes = publication.get("analysis", {}).get("outcomes", {})
    if outcomes.get("primary") != "out_recall_at_100" or outcomes.get("secondary") != [
        "out_ndcg_at_100",
        "out_ndcg_at_10",
    ]:
        raise AdoptionInputsV15Error("publication v13 outcome semantics drift")
    return {
        "primary": "OUT Recall@100",
        "secondary": ["OUT nDCG@100", "OUT nDCG@10"],
    }


def finalize(
    repository_root: Path,
    *,
    bundle_path: Path,
    bundle_receipt_path: Path,
    pre_adoption_anchor_path: Path,
    handoff_path: Path,
    transfer_path: Path,
    pre_compilation_anchor_path: Path,
    compiler_receipt_path: Path,
    binding_set_path: Path,
    watchdog_receipt_path: Path,
) -> dict[str, Any]:
    root = repository_root.resolve()
    validate_contract(root)
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise AdoptionInputsV15Error(
            "repository must be clean before final receipt publication"
        )
    bundle = _bundle_receipt(root, bundle_path, bundle_receipt_path)
    if (
        _git(root, "rev-parse", "HEAD^{commit}") != bundle["git_commit"]
        or _git(root, "rev-parse", "origin/main") != bundle["git_commit"]
    ):
        raise AdoptionInputsV15Error(
            "finalizer requires the current clean pushed bundle commit"
        )
    anchor_path = _external(pre_adoption_anchor_path, root, role="pre-adoption anchor")
    anchor = _load(anchor_path, role="pre-adoption anchor")
    _schema(root, ANCHOR_SCHEMA_PATH, anchor, role="pre-adoption anchor")
    _validate_self_hash(anchor, "anchor_sha256", role="pre-adoption anchor")
    expected_bundle = {
        key: bundle[key]
        for key in (
            "git_commit",
            "git_tree",
            "frozen_bundle_sha256",
            "bundle_manifest_sha256",
            "receipt_sha256",
        )
    }
    if (
        anchor["execution_bundle"] != expected_bundle
        or anchor["authorization"] != AUTHORIZATION
    ):
        raise AdoptionInputsV15Error(
            "pre-adoption anchor bundle or authorization mismatch"
        )
    protected = _validate_protected(
        root,
        handoff_path=handoff_path,
        transfer_path=transfer_path,
        pre_compilation_anchor_path=pre_compilation_anchor_path,
        compiler_receipt_path=compiler_receipt_path,
        binding_set_path=binding_set_path,
    )
    watchdog_path = _external(watchdog_receipt_path, root, role="watchdog dry-run")
    watchdog = _load(watchdog_path, role="watchdog dry-run")
    validate_watchdog_result(root, watchdog)
    if (
        watchdog.get("status") != "PASS"
        or watchdog.get("provider_action_performed") is not False
    ):
        raise AdoptionInputsV15Error("watchdog dry-run did not pass locally")
    budget = validate_budget_model(root)
    bindings = protected["values"]["bindings"]
    rows = bindings["bindings"]
    physical_total = sum(int(item["physical_window_count"]) for item in rows)
    if physical_total != budget["workload"]["physical_window_total"]:
        raise AdoptionInputsV15Error("budget model physical-window total differs")
    publication = _load(root / V13_PATH, role="publication v13")
    outcomes = _publication_outcomes(publication)
    compiler_receipt = protected["values"]["compiler_receipt"]
    handoff = protected["values"]["handoff"]
    body = {
        "schema_version": "myis.armindex-a1.2-scientific-execution-adoption-inputs-receipt.v15",
        "receipt_id": REVISION_ID,
        "revision_id": REVISION_ID,
        "status": "LOCAL_ADOPTION_INPUTS_VALIDATED_PENDING_LIVE_PROVIDER",
        "evidence_class": "scientific_execution_adoption_input_preparation",
        "scientific_authority": False,
        "claim_boundary": "Aggregate-safe additive v15 local adoption-input closure for unchanged v11/v12-r3/v13 scientific and publication contracts. It validates the clean pushed bundle, protected 25-cell compiler evidence, workload model, and synthetic control path only; it contacts no provider and authorizes no quote, live admission, launch, measured retrieval, Selection, Final, paid API, or scientific/publication claim.",
        "execution_bundle": expected_bundle,
        "pre_adoption_anchor": {
            "anchor_file_sha256": file_sha256(anchor_path),
            "anchor_sha256": anchor["anchor_sha256"],
        },
        "protected_inputs": {
            "handoff_receipt_sha256": compiler_receipt["handoff_receipt_sha256"],
            "transfer_manifest_sha256": compiler_receipt[
                "protected_transfer_manifest_sha256"
            ],
            "compiler_receipt_sha256": compiler_receipt["receipt_sha256"],
            "binding_set_sha256": bindings["binding_set_sha256"],
            "binding_count": 25,
            "corpus_count": handoff["corpus_count"],
            "rep_dev_query_count": handoff["query_count"],
        },
        "compiled_bindings": {
            "binding_set_sha256": bindings["binding_set_sha256"],
            "binding_count": 25,
            "deterministic_replay": True,
            "effective_input_limit_evidence": True,
            "zero_silent_truncation": True,
            "protected_boundary": "PASS",
        },
        "budget_model": {
            "model_sha256": budget["model_sha256"],
            "status": budget["status"],
            "hard_stops_usd": budget["frozen_hard_stops_usd"],
            "physical_window_total": physical_total,
            "whole_workload_required": True,
            "live_admission_status": "PENDING_LIVE_PROVIDER",
        },
        "watchdog_destroy_dry_run": {
            "receipt_sha256": watchdog["receipt_sha256"],
            "status": watchdog["status"],
            "provider_action_performed": False,
            "actual_provider_destroy_capability": "PENDING_LIVE_PROVIDER",
        },
        "publication_v13": {
            "unchanged": True,
            **outcomes,
            "interaction_complementarity_preregistered": True,
            "measured_or_publication_claim_authorized": False,
        },
        "pending_live_provider": PENDING_LIVE_PROVIDER,
        "ready_for_live_provider_admission": True,
        "authorization": AUTHORIZATION,
        "counters": COUNTERS,
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    _schema(root, RECEIPT_SCHEMA_PATH, receipt, role="v15 final adoption receipt")
    _safe(receipt, role="v15 final adoption receipt")
    _write_immutable(root / RECEIPT_PATH, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-scientific-adoption-inputs-v15")
    parser.add_argument(
        "command", choices=("validate", "build-bundle", "build-anchor", "finalize")
    )
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--receipt-output", type=Path)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--bundle-receipt", type=Path)
    parser.add_argument("--pre-adoption-anchor", type=Path)
    parser.add_argument("--handoff", type=Path)
    parser.add_argument("--transfer", type=Path)
    parser.add_argument("--pre-compilation-anchor", type=Path)
    parser.add_argument("--compiler-receipt", type=Path)
    parser.add_argument("--binding-set", type=Path)
    parser.add_argument("--watchdog-receipt", type=Path)
    args = parser.parse_args()
    if args.command == "validate":
        contract = validate_contract(args.repository_root)
        result: Mapping[str, Any] = {
            "status": "PASS",
            "revision_id": REVISION_ID,
            "contract_sha256": contract["contract_sha256"],
            "bundle_path_set_sha256": BUNDLE_PATH_SET_SHA256,
            "pending_live_provider": PENDING_LIVE_PROVIDER,
        }
    elif args.command == "build-bundle":
        if args.output is None or args.receipt_output is None:
            parser.error("build-bundle requires --output and --receipt-output")
        result = build_bundle(
            args.repository_root, output=args.output, receipt_output=args.receipt_output
        )
    elif args.command == "build-anchor":
        if args.bundle is None or args.bundle_receipt is None or args.output is None:
            parser.error(
                "build-anchor requires --bundle, --bundle-receipt, and --output"
            )
        result = build_anchor(
            args.repository_root,
            bundle_path=args.bundle,
            bundle_receipt_path=args.bundle_receipt,
            output=args.output,
        )
    else:
        required = (
            args.bundle,
            args.bundle_receipt,
            args.pre_adoption_anchor,
            args.handoff,
            args.transfer,
            args.pre_compilation_anchor,
            args.compiler_receipt,
            args.binding_set,
            args.watchdog_receipt,
        )
        if any(item is None for item in required):
            parser.error(
                "finalize requires bundle, anchors, protected compiler evidence, and watchdog receipt"
            )
        result = finalize(
            args.repository_root,
            bundle_path=args.bundle,
            bundle_receipt_path=args.bundle_receipt,
            pre_adoption_anchor_path=args.pre_adoption_anchor,
            handoff_path=args.handoff,
            transfer_path=args.transfer,
            pre_compilation_anchor_path=args.pre_compilation_anchor,
            compiler_receipt_path=args.compiler_receipt,
            binding_set_path=args.binding_set,
            watchdog_receipt_path=args.watchdog_receipt,
        )
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
