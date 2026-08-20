from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from myis_research.armindex.a6_materialization import A6MaterializationError


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_a6_bundle.py"
SPEC = importlib.util.spec_from_file_location("build_a6_bundle", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_preparation_bundle_is_fail_closed_and_hash_bound(tmp_path: Path) -> None:
    bundle = MODULE.build_bundle()
    assert bundle["status"] == "PENDING_A5_CLOSEOUT"
    assert bundle["execution_permitted"] is False
    assert bundle["launch_allowed"] is False
    assert bundle["selection_accesses"] == bundle["final_accesses"] == 0
    assert bundle["protected_payload_included"] is False
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(bundle), encoding="ascii")
    MODULE.validate_bundle(path)


def test_tampered_bundle_cannot_open_execution(tmp_path: Path) -> None:
    bundle = MODULE.build_bundle()
    bundle["execution_permitted"] = True
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(bundle), encoding="ascii")
    with pytest.raises(A6MaterializationError):
        MODULE.validate_bundle(path)
