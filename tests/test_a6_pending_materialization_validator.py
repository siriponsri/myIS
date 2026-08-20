"""Focused tests for the local, fail-closed A6 pending validator."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from myis_research.armindex.a6_materialization import A6MaterializationError


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "control/armindex/a6/a6-full-dapfam-execution-contract.v1.json"
TEMPLATE = ROOT / "control/armindex/a6/a6-pending-a5-closeout-template.v1.json"
SCRIPT = ROOT / "scripts/validate_a6_pending_materialization.py"
SPEC = importlib.util.spec_from_file_location("validate_a6_pending_materialization", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def load(path: Path) -> dict:
    return MODULE.load_json(path)


def test_canonical_pending_template_produces_closed_receipt() -> None:
    receipt = MODULE.build_validation_receipt(load(TEMPLATE), load(CONTRACT))
    assert receipt["status"] == "PASS_A6_PENDING_TEMPLATE_VALIDATED"
    assert receipt["execution_permitted"] is False
    assert receipt["selection_accesses"] == 0
    assert receipt["final_accesses"] == 0
    assert receipt["protected_payload_included"] is False
    assert receipt["authorized_instance_id"] == 47790578
    assert len(receipt["receipt_sha256"]) == 64


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("execution_permitted", True),
        ("selection_accesses", 1),
        ("final_accesses", 1),
        ("protected_payload_included", True),
        ("full_corpus_source_sha256", "a" * 64),
    ],
)
def test_tampered_template_is_rejected(field: str, value: object) -> None:
    template = load(TEMPLATE)
    template[field] = value
    with pytest.raises(A6MaterializationError):
        MODULE.build_validation_receipt(template, load(CONTRACT))
