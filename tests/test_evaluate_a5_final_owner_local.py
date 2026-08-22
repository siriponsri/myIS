"""Boundary checks for the Final-872 Owner-local evaluator."""

from __future__ import annotations

import importlib.util
from copy import deepcopy
from pathlib import Path

import pytest

from myis_research.kernel.canonical import canonical_sha256


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "evaluate_a5_final_owner_local.py"
SPEC = importlib.util.spec_from_file_location("evaluate_a5_final_owner_local", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _request() -> dict[str, object]:
    body: dict[str, object] = {
        "schema_version": "myis.armindex-a5-final-request.v1",
        "scope": "Final-872",
        "query_count": 872,
        "attempt_id": "a5-goal001-20260822T-rerun-final872-r03",
    }
    return {**body, "request_sha256": canonical_sha256(body)}


def _package(request: dict[str, object]) -> dict[str, object]:
    rankings = {"research_champion": {}, "static_common_baseline": {}}
    return {
        "schema_version": "myis.armindex-a5-final-ranking-package.v1",
        "status": "PASS_A5_REMOTE_OPAQUE_RANKINGS",
        "attempt_id": request["attempt_id"],
        "request_sha256": request["request_sha256"],
        "scope": "Final-872",
        "query_count": 872,
        "rankings": rankings,
        "ranking_sha256": canonical_sha256(rankings),
        "coverage": {"research_champion": 872, "static_common_baseline": 872},
        "failures": 0,
        "determinism": True,
        "protected_payload_included": False,
        "rankings_returned_to": "owner_local_evaluator_only",
    }


def test_ranking_package_requires_full_final_lineage() -> None:
    request = _request()
    assert MODULE._validate_ranking_package(request, _package(request))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("attempt_id", "a5-goal001-other"),
        ("scope", "Selection-125"),
        ("protected_payload_included", True),
        ("rankings_returned_to", "repository"),
        ("ranking_sha256", "0" * 64),
    ],
)
def test_ranking_package_rejects_lineage_or_boundary_drift(field: str, value: object) -> None:
    request = _request()
    package = deepcopy(_package(request))
    package[field] = value
    with pytest.raises(ValueError):
        MODULE._validate_ranking_package(request, package)
