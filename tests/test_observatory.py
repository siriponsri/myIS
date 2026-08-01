from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from myis_research.observatory.core import (
    CaptureSession,
    EvidenceRegistry,
    ObservatoryError,
    build_artifact_record,
    build_run_record,
    canonical_sha256,
    validate_registry,
)
from myis_research.observatory.fixture import (
    build_fixture_package,
    build_fixture_registry,
    run_negative_checks,
    write_fixture,
)
from myis_research.observatory.graph import build_evidence_graph, validate_evidence_graph


ROOT = Path(__file__).resolve().parents[1]


def test_fixture_is_deterministic_and_graph_is_closed() -> None:
    first = build_fixture_package()
    second = build_fixture_package()
    assert first["package_sha256"] == second["package_sha256"]
    assert first["registry"]["registry_sha256"] == second["registry"]["registry_sha256"]
    validate_registry(first["registry"])
    graph = build_evidence_graph(first["registry"])
    validate_evidence_graph(graph, first["registry"])
    assert len(first["registry"]["records"]["candidates"]) == 2
    assert len(first["registry"]["records"]["failures"]) == 1
    assert first["registry"]["records"]["metrics"][0]["evidence_class"] == "fixture"


def test_fixture_negative_checks_fail_closed() -> None:
    checks = run_negative_checks(build_fixture_registry())
    assert set(checks) >= {"duplicate_id", "hash_mismatch", "unsafe_absolute_path", "protected_field", "fixture_as_measured", "orphan_result", "graph_validation"}
    assert all(value == "PASS" for value in checks.values())


def test_fixture_writer_closes_checksums_and_receipt(tmp_path: Path) -> None:
    paths = write_fixture(tmp_path)
    assert set(paths) == {"README.md", "RUN_SUMMARY.md", "index.json", "mlflow-run.json", "receipt.json", "registry.json", "SHA256SUMS.txt"}
    registry = json.loads(paths["registry.json"].read_text(encoding="utf-8"))
    receipt = json.loads(paths["receipt.json"].read_text(encoding="utf-8"))
    validate_registry(registry)
    assert receipt["registry_sha256"] == registry["registry_sha256"]
    assert receipt["real_counters"] == {"candidate_count": 0, "measured_runs": 0, "selection_accesses": 0, "shortlist_count": 0}
    lines = paths["SHA256SUMS.txt"].read_text(encoding="utf-8").splitlines()
    assert len(lines) == 6
    for line in lines:
        digest, name = line.split("  ", 1)
        assert digest == canonical_sha256(paths[name].read_bytes())


def test_capture_session_records_lifecycle_and_rejects_duplicate_start() -> None:
    registry = EvidenceRegistry(registry_id="observatory-test-v1")
    session = CaptureSession(registry, "obs-run-test", "obs-request-test", "P2_SCOPE_DEVELOPMENT", "P2.1")
    session.start(request_sha256="a" * 64, profile_sha256="b" * 64, envelope_sha256="c" * 64, environment_sha256="d" * 64, config_sha256="e" * 64, git_commit="f" * 40, summary="test run")
    with pytest.raises(ObservatoryError, match="already started"):
        session.start(request_sha256="a" * 64, profile_sha256="b" * 64, envelope_sha256="c" * 64, environment_sha256="d" * 64, config_sha256="e" * 64, git_commit="f" * 40, summary="test run")
    session.transition("candidate_generation")
    size = 5
    artifact = build_artifact_record("obs-artifact-test", title="Test output", artifact_type="output", producing_run_id="obs-run-test", safe_uri="git://outputs/observatory/test.json", size_bytes=size, content_sha256="1" * 64, summary="test artifact")
    session.register_artifact(artifact)
    session.finish()
    assert registry.records["runs"][0]["status"] == "succeeded"
    assert registry.records["runs"][0]["artifact_ids"] == ["obs-artifact-test"]
    validate_registry(registry.as_dict())


@pytest.mark.parametrize("filename", [
    "observatory-registry.v1.json",
    "observatory-run.v1.json",
    "observatory-artifact.v1.json",
    "observatory-prompt.v1.json",
    "observatory-metric.v1.json",
    "observatory-receipt.v1.json",
])
def test_observatory_schemas_are_valid_json(filename: str) -> None:
    schema = json.loads((ROOT / "schemas" / filename).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
