"""Focused tests for the local, fail-closed A5 pending validator."""

from __future__ import annotations

import json
import importlib.util
from pathlib import Path

import pytest

from myis_research.armindex.a4_a5_handoff import A4A5HandoffError
ROOT = Path(__file__).parents[1]
TEMPLATE = ROOT / "control/armindex/a5/a5-pending-a4-selection-template.v1.json"
_SCRIPT = ROOT / "scripts/validate_a5_pending_handoff.py"
_SPEC = importlib.util.spec_from_file_location("validate_a5_pending_handoff", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
build_validation_receipt = _MODULE.build_validation_receipt
load_template = _MODULE.load_template


def test_canonical_pending_template_produces_closed_receipt() -> None:
    receipt = build_validation_receipt(load_template(TEMPLATE))
    assert receipt["status"] == "PASS_A5_PENDING_TEMPLATE_VALIDATED"
    assert receipt["execution_permitted"] is False
    assert receipt["selection_accesses"] == 0
    assert receipt["final_accesses"] == 0
    assert receipt["protected_payload_included"] is False
    assert receipt["expected_final_query_count"] == 872
    assert len(receipt["receipt_sha256"]) == 64


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("execution_permitted", True),
        ("selection_accesses", 1),
        ("final_accesses", 1),
        ("protected_payload_included", True),
        ("final_input_pointer", "a5/final-input"),
    ],
)
def test_tampered_template_is_rejected(tmp_path: Path, field: str, value: object) -> None:
    template = load_template(TEMPLATE)
    template[field] = value
    tampered = tmp_path / "tampered.json"
    tampered.write_text(json.dumps(template), encoding="ascii")
    with pytest.raises(A4A5HandoffError):
        build_validation_receipt(load_template(tampered))
