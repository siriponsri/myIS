from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from myis_research.armindex.owner_data_bundle import (
    OwnerDataBundleError,
    build_bundle,
    validate_bundle,
)


ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT.parent / "04_Owner_Stores"


def test_owner_bundle_is_hash_only_and_preserves_gates(tmp_path: Path) -> None:
    bundle_root = OWNER / "armindex" / "data-bundle" / f"test-owner-bundle-{tmp_path.name}"
    try:
        receipt = build_bundle(output_root=bundle_root)
        assert receipt["selection_accesses"] == receipt["final_accesses"] == 0
        assert receipt["protected_payload_included"] is False
        assert receipt["measured_access"] is False
        assert receipt["partition_counts"] == {"train": 250, "selection": 125, "final": 872}
        assert receipt["full_corpus_row_count"] == 45336
        assert validate_bundle(bundle_root)["receipt_sha256"] == receipt["receipt_sha256"]
        assert not list(bundle_root.rglob("*.jsonl"))
    finally:
        shutil.rmtree(bundle_root, ignore_errors=True)


def test_owner_bundle_rejects_tampered_receipt(tmp_path: Path) -> None:
    bundle_root = OWNER / "armindex" / "data-bundle" / f"test-owner-bundle-tampered-{tmp_path.name}"
    try:
        build_bundle(output_root=bundle_root)
        source = bundle_root / "aggregate-bundle-receipt.json"
        value = json.loads(source.read_text(encoding="ascii"))
        value["selection_accesses"] = 1
        source.write_text(json.dumps(value), encoding="ascii")
        with pytest.raises(OwnerDataBundleError):
            validate_bundle(bundle_root)
    finally:
        shutil.rmtree(bundle_root, ignore_errors=True)


def test_owner_bundle_refuses_overwrite() -> None:
    pytest.skip("write-once behavior is covered by the CLI and production bundle")
