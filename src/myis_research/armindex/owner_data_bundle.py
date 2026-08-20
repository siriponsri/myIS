"""Build and validate the hash-only Owner Store bundle for ArmIndex A2-A6.

The builder may inspect protected files inside ``04_Owner_Stores`` but never
copies their payload into the repository or into the emitted receipt.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only


class OwnerDataBundleError(ValueError):
    """Raised when an Owner Store bundle is invalid or would cross a boundary."""


PARENT_SPLIT_SHA256 = "33a1818ff3c00775d43951182fdf769255c8ebfc591de183df4fbfdd3b039dc6"
REP_MEMBERSHIP_SHA256 = "5ab1d3374e8cbe83316c18f25384c08402cc3d881249ac6f0385a9a18896a116"
HDEV_MEMBERSHIP_SHA256 = "af1bcfdc21fc53a65a94f836bc16e5d4c8bfd80e020fb53b78a540664602faaf"
PROTECTED_MEMBERSHIP_SHA256 = "779d93c2d0f2ae3eea81421257b1ceb149e8b314350b813cf856227d1359aa42"
SPLIT_RECEIPT_SHA256 = "f5d658f43b8d71e0ec34e08fee6eaf0af18d3649ad5609dffdf3dc2629e2f0f3"
SOURCE_REVISION = "a59a74ce31384165065af1823a83c6f94ccafd48"

_ROOT = Path(__file__).resolve().parents[3]
_SOURCE_CONTRACT = _ROOT / "control/assets/dapfam-p1-source.v1.json"
_OWNER_RELATIVE = {
    "parent_split": Path("a1.2-v15-20260809/parent/dapfam-protected-split.json"),
    "split_receipt": Path("a1.2-v15-20260809/split-v15/A1_2_REP_HARNESS_SPLIT_RECEIPT_V1.json"),
    "membership_commitment": Path("a1.2-v15-20260809/split-v15/A1_2_REP_HARNESS_MEMBERSHIP_V1.json"),
    "a3_train_receipt": Path("armindex/a3/a3-train250-owner-package-20260818T0025Z/A3_TRAIN250_OWNER_PACKAGE_RECEIPT.json"),
    "a4_hdev_receipt": Path("armindex/a4/a4-goal001-20260819T180000Z-a4x12/hdev-handoff/A4_HDEV_HANDOFF_RECEIPT.json"),
    "a4_hdev_queries": Path("armindex/a4/a4-goal001-20260819T180000Z-a4x12/hdev-handoff/protected/hdev-queries.jsonl"),
    "a6_full_corpus": Path("a1.2-v15-20260809/protected/inputs/corpus.jsonl"),
}


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise OwnerDataBundleError(f"cannot read JSON source: {path}") from error
    if not isinstance(value, dict):
        raise OwnerDataBundleError(f"expected JSON object: {path}")
    return value


def _contained_file(owner_root: Path, relative: Path) -> Path:
    if relative.is_absolute() or ".." in relative.parts:
        raise OwnerDataBundleError(f"owner pointer must be relative: {relative}")
    candidate = owner_root / relative
    if candidate.is_symlink():
        raise OwnerDataBundleError(f"owner source must not be a symlink: {relative}")
    path = candidate.resolve()
    root = owner_root.resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise OwnerDataBundleError(f"owner pointer escapes Owner Store: {relative}") from error
    if not path.is_file():
        raise OwnerDataBundleError(f"owner source must be a regular file: {relative}")
    return path


def _hash_record(owner_root: Path, role: str, relative: Path) -> dict[str, Any]:
    path = _contained_file(owner_root, relative)
    return {
        "artifact_role": role,
        "owner_relative_pointer": relative.as_posix(),
        "bytes": path.stat().st_size,
        "sha256": file_sha256(path),
    }


def _validate_split(owner_root: Path) -> dict[str, Any]:
    parent = _load(_contained_file(owner_root, _OWNER_RELATIVE["parent_split"]))
    if parent.get("schema_version") != "myis.protected-split.v1":
        raise OwnerDataBundleError("parent split schema drifted")
    if parent.get("seed") != 42 or parent.get("algorithm") != "sha256-seed-colon-id-lexical-v1":
        raise OwnerDataBundleError("parent split algorithm/seed drifted")
    if parent.get("split_sha256") != PARENT_SPLIT_SHA256:
        raise OwnerDataBundleError("parent split commitment drifted")
    sets = {name: set(parent.get(name, [])) for name in ("train", "selection", "final")}
    counts = {name: len(values) for name, values in sets.items()}
    if counts != {"train": 250, "selection": 125, "final": 872}:
        raise OwnerDataBundleError(f"parent split counts invalid: {counts}")
    if any(not values for values in sets.values()) or sum(counts.values()) != 1247:
        raise OwnerDataBundleError("parent split partition is incomplete")
    if sets["train"] & sets["selection"] or sets["train"] & sets["final"] or sets["selection"] & sets["final"]:
        raise OwnerDataBundleError("parent split partitions overlap")
    return {"seed": 42, "algorithm": parent["algorithm"], "counts": counts, "partition_union_count": 1247}


def _validate_membership(owner_root: Path) -> dict[str, Any]:
    value = _load(_contained_file(owner_root, _OWNER_RELATIVE["membership_commitment"]))
    body = {key: item for key, item in value.items() if key != "protected_membership_sha256"}
    if value.get("schema_version") != "myis.armindex-a1.2-rep-harness-protected-membership.v1":
        raise OwnerDataBundleError("REP/HDEV membership schema drifted")
    if value.get("protected_membership_sha256") != canonical_sha256(body):
        raise OwnerDataBundleError("protected membership self-hash mismatch")
    if value.get("protected_membership_sha256") != PROTECTED_MEMBERSHIP_SHA256:
        raise OwnerDataBundleError("protected membership commitment drifted")
    rep, hdev = set(value.get("rep_dev", [])), set(value.get("harness_dev", []))
    if len(rep) != 150 or len(hdev) != 100 or rep & hdev or len(rep | hdev) != 250:
        raise OwnerDataBundleError("REP/HDEV partition invalid")
    if value.get("parent_split_sha256") != PARENT_SPLIT_SHA256:
        raise OwnerDataBundleError("REP/HDEV parent commitment drifted")
    if value.get("rep_dev_membership_sha256") != REP_MEMBERSHIP_SHA256 or value.get("harness_dev_membership_sha256") != HDEV_MEMBERSHIP_SHA256:
        raise OwnerDataBundleError("REP/HDEV membership commitments drifted")
    return {"rep_dev_count": 150, "hdev_count": 100, "membership_commitment_sha256": PROTECTED_MEMBERSHIP_SHA256}


def build_bundle(*, output_root: Path, owner_store_root: Path | None = None) -> dict[str, Any]:
    """Create a new write-once, hash-only Owner Store bundle."""

    owner = (owner_store_root or (_ROOT.parent / "04_Owner_Stores")).resolve()
    output = output_root.resolve()
    if output.exists() or output.is_symlink():
        raise OwnerDataBundleError(f"refusing to overwrite existing bundle: {output}")
    try:
        output.relative_to(owner)
    except ValueError as error:
        raise OwnerDataBundleError("bundle must be inside 04_Owner_Stores") from error
    split = _validate_split(owner)
    membership = _validate_membership(owner)
    source = _load(_SOURCE_CONTRACT)
    if source.get("schema_version") != "myis.dapfam-p1-source.v1" or source.get("dataset", {}).get("revision") != SOURCE_REVISION:
        raise OwnerDataBundleError("DAPFAM source contract drifted")
    if source.get("configs", {}).get("corpus", {}).get("rows") != 45336:
        raise OwnerDataBundleError("A6 full-corpus inventory must be 45,336 rows")

    artifacts = [
        _hash_record(owner, "parent_split_commitment", _OWNER_RELATIVE["parent_split"]),
        _hash_record(owner, "rep_hdev_split_receipt", _OWNER_RELATIVE["split_receipt"]),
        _hash_record(owner, "rep_hdev_membership_commitment", _OWNER_RELATIVE["membership_commitment"]),
        _hash_record(owner, "train_250_prepared_receipt", _OWNER_RELATIVE["a3_train_receipt"]),
        _hash_record(owner, "hdev_100_prepared_receipt", _OWNER_RELATIVE["a4_hdev_receipt"]),
        _hash_record(owner, "hdev_100_protected_input_pointer", _OWNER_RELATIVE["a4_hdev_queries"]),
        _hash_record(owner, "a6_full_corpus_owner_pointer", _OWNER_RELATIVE["a6_full_corpus"]),
    ]
    source_manifest = {
        "schema_version": "myis.armindex-owner-data-source-manifest.v1",
        "source_contract_pointer": "control/assets/dapfam-p1-source.v1.json",
        "source_contract_sha256": file_sha256(_SOURCE_CONTRACT),
        "dataset_revision": SOURCE_REVISION,
        "full_corpus_row_count": 45336,
        "parent_split_sha256": PARENT_SPLIT_SHA256,
        "split_algorithm": split["algorithm"],
        "split_seed": split["seed"],
        "partition_counts": split["counts"],
        "rep_dev_count": membership["rep_dev_count"],
        "hdev_count": membership["hdev_count"],
        "membership_commitment_sha256": membership["membership_commitment_sha256"],
        "split_receipt_sha256": SPLIT_RECEIPT_SHA256,
        "artifacts": artifacts,
        "protected_payload_included": False,
        "measured_access": False,
    }
    receipt_body = {
        "schema_version": "myis.armindex-owner-data-bundle-receipt.v1",
        "bundle_id": output.name,
        "status": "PASS_OWNER_DATA_BUNDLE_PREPARED",
        "bundle_root_pointer": output.relative_to(owner).as_posix(),
        "source_manifest_sha256": canonical_sha256(source_manifest),
        "train_rep_hdev_status": "PREPARED_HASH_BOUND",
        "selection_status": "SEALED_PRE_MEASUREMENT",
        "selection_next_state": "PENDING_PAIRED_VECTORS",
        "final_status": "SEALED_PRE_D2",
        "final_next_state": "PENDING_A5_D2",
        "a6_status": "SOURCE_HASHED",
        "a6_next_state": "PENDING_A5_FROZEN_WINNER",
        "selection_accesses": 0,
        "final_accesses": 0,
        "protected_payload_included": False,
        "measured_access": False,
        "source_contract_sha256": source_manifest["source_contract_sha256"],
        "full_corpus_row_count": 45336,
        "parent_split_sha256": PARENT_SPLIT_SHA256,
        "partition_counts": split["counts"],
        "rep_dev_count": 150,
        "hdev_count": 100,
        "membership_commitment_sha256": PROTECTED_MEMBERSHIP_SHA256,
        "forbidden_outputs": ["paired_metric_vectors", "selection_receipt", "d2", "winner"],
    }
    assert_aggregate_only(source_manifest)
    assert_aggregate_only(receipt_body)
    receipt = {**receipt_body, "receipt_sha256": canonical_sha256(receipt_body)}
    output.mkdir(parents=True)
    for name in ("train-250", "selection-125/sealed", "final-872/sealed", "a6-full-corpus"):
        (output / name).mkdir(parents=True)
    (output / "source-manifest.json").write_text(json.dumps(source_manifest, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="ascii")
    (output / "aggregate-bundle-receipt.json").write_text(json.dumps(receipt, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="ascii")
    for name, state in {
        "train-250": "PREPARED_HASH_BOUND",
        "selection-125/sealed": "SEALED_PRE_MEASUREMENT",
        "final-872/sealed": "SEALED_PRE_D2",
        "a6-full-corpus": "SOURCE_HASHED",
    }.items():
        (output / name / "scope.json").write_text(json.dumps({"scope_status": state, "source_manifest_sha256": receipt["source_manifest_sha256"], "payload_materialized": False}, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="ascii")
    return receipt


def validate_bundle(bundle_root: Path, *, owner_store_root: Path | None = None) -> dict[str, Any]:
    owner = (owner_store_root or (_ROOT.parent / "04_Owner_Stores")).resolve()
    root = bundle_root.resolve()
    try:
        root.relative_to(owner)
    except ValueError as error:
        raise OwnerDataBundleError("bundle is outside Owner Store") from error
    receipt_path, manifest_path = root / "aggregate-bundle-receipt.json", root / "source-manifest.json"
    if not receipt_path.is_file() or not manifest_path.is_file() or receipt_path.is_symlink() or manifest_path.is_symlink():
        raise OwnerDataBundleError("bundle receipt/manifest missing or symlinked")
    receipt, manifest = _load(receipt_path), _load(manifest_path)
    if receipt.get("schema_version") != "myis.armindex-owner-data-bundle-receipt.v1" or receipt.get("status") != "PASS_OWNER_DATA_BUNDLE_PREPARED":
        raise OwnerDataBundleError("bundle receipt status/schema invalid")
    if receipt.get("receipt_sha256") != canonical_sha256({k: v for k, v in receipt.items() if k != "receipt_sha256"}):
        raise OwnerDataBundleError("bundle receipt self-hash mismatch")
    if receipt.get("source_manifest_sha256") != canonical_sha256(manifest):
        raise OwnerDataBundleError("source manifest commitment mismatch")
    for field, expected in (("selection_accesses", 0), ("final_accesses", 0), ("protected_payload_included", False), ("measured_access", False)):
        if receipt.get(field) != expected:
            raise OwnerDataBundleError(f"bundle guard failed: {field}")
    assert_aggregate_only(receipt)
    assert_aggregate_only(manifest)
    for name in ("train-250", "selection-125/sealed", "final-872/sealed", "a6-full-corpus"):
        scope = root / name / "scope.json"
        if not scope.is_file() or scope.is_symlink():
            raise OwnerDataBundleError(f"bundle scope marker missing: {name}")
        marker = _load(scope)
        if marker.get("source_manifest_sha256") != receipt["source_manifest_sha256"] or marker.get("payload_materialized") is not False:
            raise OwnerDataBundleError(f"bundle scope marker invalid: {name}")
    return receipt


__all__ = ["OwnerDataBundleError", "build_bundle", "validate_bundle"]
