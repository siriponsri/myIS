from __future__ import annotations

import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from typing import Any

from myis_research.p2 import fixture as fixture_module
from myis_research.p2.contracts import build_request as canonical_build_request
from myis_research.p2.fixture import (
    NEGATIVE_CHECK_IDS,
    run_fixture_pilot,
    validate_fixture_execution_manifest,
    validate_fixture_receipt,
)
from myis_research.projections.read_model import _p2_fixture_projection


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_METADATA_FIELDS = {
    "fixture",
    "evidence_class",
    "scientific_authority",
    "measured_execution",
    "protected_data_accessed",
}


def test_fixture_request_and_execution_metadata_validate_separately(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def capture_request(**kwargs: Any) -> dict[str, Any]:
        request = canonical_build_request(**kwargs)
        captured.update(request)
        return request

    monkeypatch.setattr(fixture_module, "build_request", capture_request)
    with TemporaryDirectory(prefix="p2-fixture-contract-") as temporary:
        fixture_module._execute_once(ROOT, Path(temporary) / "repository", "a" * 40)

    assert captured["schema_version"] == "myis.p2-request.v1"
    assert FIXTURE_METADATA_FIELDS.isdisjoint(captured)


def test_full_fixture_lifecycle_is_deterministic_and_non_measured(tmp_path: Path) -> None:
    receipt_path = tmp_path / "p2-fixture-pilot-v1.receipt.json"
    result = run_fixture_pilot(
        ROOT,
        receipt_path,
        require_clean_git=False,
        enforce_repository_output=False,
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    manifest_path = receipt_path.with_name("p2-fixture-pilot-v1.execution-manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    validate_fixture_receipt(receipt, repository_root=ROOT)
    validate_fixture_execution_manifest(manifest, receipt=receipt)

    assert result["fixture_status"] == "passed"
    assert result["canonical_hashes_match"] is True
    assert result["negative_checks_passed"] is True
    assert result["negative_check_count"] == len(NEGATIVE_CHECK_IDS) == 94
    assert receipt["synthetic_candidates"] == 32
    assert receipt["synthetic_adaptive_iterations"] == 5
    assert receipt["synthetic_shortlist_count"] == 4
    assert receipt["fixture_selection_exposures"] == 1
    assert receipt["measured_runs"] == 0
    assert receipt["candidate_count"] == 0
    assert receipt["selection_accesses"] == 0
    assert receipt["protected_data_accessed"] is False
    assert receipt["measured_execution_performed"] is False
    assert manifest["stage"] == "fixture"
    assert manifest["evidence_class"] == "fixture"
    assert manifest["method"]["scientific_authority"] is False
    assert manifest["metrics"] == []

    projection_root = tmp_path / "projection"
    (projection_root / "control/budgets").mkdir(parents=True)
    shutil.copy2(
        ROOT / "control/budgets/p2-r1-primary-v1.yaml",
        projection_root / "control/budgets/p2-r1-primary-v1.yaml",
    )
    shutil.copy2(
        ROOT / "control/execution-envelope-p2.yaml",
        projection_root / "control/execution-envelope-p2.yaml",
    )
    projection_output = projection_root / "outputs/fixtures/p2"
    projection_output.mkdir(parents=True)
    shutil.copy2(receipt_path, projection_output / receipt_path.name)
    shutil.copy2(manifest_path, projection_output / manifest_path.name)
    fixture_projection = _p2_fixture_projection(projection_root)
    assert fixture_projection["status"] == "passed"
    assert fixture_projection["synthetic_candidates"] == 32
    assert fixture_projection["fixture_selection_exposures"] == 1
    assert fixture_projection["scientific_authority"] is False


def test_negative_check_catalog_is_complete_and_unique() -> None:
    assert len(NEGATIVE_CHECK_IDS) == 94
    assert len(set(NEGATIVE_CHECK_IDS)) == len(NEGATIVE_CHECK_IDS)
    assert NEGATIVE_CHECK_IDS[0] == "metric-wrong-name"
    assert NEGATIVE_CHECK_IDS[-1] == "protected-absolute-owner-path"
