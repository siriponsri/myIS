from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from myis_research.owner_local import canonical_sha256
from myis_research.owner_local_runner import process


def _write_bundle(root: Path) -> None:
    (root / "documents.json").write_text(json.dumps([
        {"doc_id": "d1", "family_id": "f1", "text": "grounded compiler evidence"},
        {"doc_id": "d2", "family_id": "f2", "text": "unrelated text"},
    ]), encoding="utf-8")
    (root / "queries.json").write_text(json.dumps([
        {"query_id": "q1", "text": "grounded evidence", "split": "train"},
    ]), encoding="utf-8")
    (root / "qrels.json").write_text(json.dumps({"q1": ["f1"]}), encoding="utf-8")
    (root / "splits.json").write_text(json.dumps({"train": ["q1"], "selection": []}), encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_runner_computes_aggregate_only_receipt(tmp_path: Path):
    protected_root = tmp_path / "protected"
    protected_root.mkdir()
    _write_bundle(protected_root)
    request = {
        "schema_version": "myis.owner-local-request.v2",
        "request_id": "p1-demo",
        "decision_id": "P1_CPU_EXECUTION_ENVELOPE",
        "phase_id": "P1_CPU_BASELINE",
        "stage": "train_selection",
        "scope": {"campaign": "a" * 64},
        "git_commit": "a" * 40,
        "input_hashes": {f"{name}_sha256": _sha(protected_root / f"{name}.json") for name in ("documents", "queries", "qrels", "splits")},
    }
    request_path = tmp_path / "request.json"
    receipt_path = tmp_path / "receipt.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    process(request_path, protected_root, receipt_path)
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "myis.owner-local-receipt.v2"
    assert payload["decision_id"] == "P1_CPU_EXECUTION_ENVELOPE"
    assert payload["metrics"]
    assert "r0_train_metrics" in payload["aggregate_hashes"]
    assert payload["receipt_sha256"] == canonical_sha256({k: v for k, v in payload.items() if k != "receipt_sha256"})


def test_runner_rejects_declared_hash_mismatch(tmp_path: Path):
    protected_root = tmp_path / "protected"
    protected_root.mkdir()
    _write_bundle(protected_root)
    request = {
        "schema_version": "myis.owner-local-request.v2", "request_id": "p1-demo", "decision_id": "P1_CPU_EXECUTION_ENVELOPE", "phase_id": "P1_CPU_BASELINE", "stage": "train_selection", "scope": {"campaign": "a" * 64}, "git_commit": "a" * 40, "input_hashes": {"documents_sha256": "b" * 64},
    }
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    with pytest.raises(ValueError, match="declared input hashes"):
        process(request_path, protected_root, tmp_path / "receipt.json")


def test_runner_rejects_precomputed_aggregate_file(tmp_path: Path):
    request_path = tmp_path / "request.json"
    request_path.write_text("{}", encoding="utf-8")
    aggregate = tmp_path / "aggregate.json"
    aggregate.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="precomputed aggregate"):
        process(request_path, aggregate, tmp_path / "receipt.json")
