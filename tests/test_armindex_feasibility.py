from __future__ import annotations

import copy
import json

import pytest

from myis_research.armindex.feasibility import (
    FIXTURE_ID,
    SCALE_FACTORS,
    run_compute_storage_feasibility_fixture,
    validate_compute_storage_artifacts,
)
from myis_research.protection import assert_aggregate_only


def test_a08_feasibility_fixture_is_disposable_and_aggregate_safe() -> None:
    result = run_compute_storage_feasibility_fixture(repetitions=3)

    assert result.output_persisted is False
    assert result.manifest["fixture_id"] == FIXTURE_ID
    assert result.manifest["task_id"] == "A0.8"
    assert result.receipt["status"] == "PASS"
    assert result.receipt["scientific_authority"] is False
    assert result.receipt["protected_data_accessed"] is False
    assert result.receipt["aggregate_counts"] == {
        "profile_count": 3,
        "dense_arms_blocked": 4,
        "synthetic_cases": 2,
    }
    assert set(result.receipt["real_counters"].values()) == {0}
    assert set(result.receipt["resource_counters"].values()) == {0}
    assert all(value is False for key, value in result.receipt["safety"].items() if key not in {"synthetic_inputs_only", "cpu_only"})
    assert result.receipt["safety"]["synthetic_inputs_only"] is True
    assert result.receipt["safety"]["cpu_only"] is True
    assert_aggregate_only(result.manifest)
    assert_aggregate_only(result.receipt)


def test_a08_profiles_bind_deterministic_storage_and_host_observations() -> None:
    result = run_compute_storage_feasibility_fixture(repetitions=3)

    assert [item["scale_factor"] for item in result.manifest["profiles"]] == list(SCALE_FACTORS)
    assert [item["synthetic_document_count"] for item in result.manifest["profiles"]] == [4, 32, 128]
    for profile, observation in zip(
        result.manifest["profiles"],
        result.receipt["observations"],
        strict=True,
    ):
        assert observation["profile_sha256"] == profile["profile_sha256"]
        assert profile["compiled_text_bytes"] > 0
        assert profile["compiled_payload_bytes"] >= profile["compiled_text_bytes"]
        assert profile["portable_sparse_payload_bytes"] > 0
        assert observation["peak_python_allocation_bytes"] > 0
        assert observation["search_throughput_qps"] > 0
        for metrics in observation["latency_ms"].values():
            assert 0 <= metrics["p50"] <= metrics["p95"] <= metrics["p99"]


def test_a08_explicit_output_is_write_once_and_validated(tmp_path) -> None:
    output = tmp_path / "a08-fixture"

    result = run_compute_storage_feasibility_fixture(output, repetitions=3)

    assert result.output_persisted is True
    manifest = json.loads((output / "manifest.json").read_text(encoding="ascii"))
    receipt = json.loads((output / "receipt.json").read_text(encoding="ascii"))
    validate_compute_storage_artifacts(manifest, receipt)
    with pytest.raises(FileExistsError, match="must be empty"):
        run_compute_storage_feasibility_fixture(output, repetitions=3)


def test_a08_validation_rejects_mutation_and_nonzero_real_counter() -> None:
    result = run_compute_storage_feasibility_fixture(repetitions=3)
    manifest = copy.deepcopy(result.manifest)
    manifest["profiles"][0]["compiled_text_bytes"] += 1
    with pytest.raises(ValueError, match="manifest_sha256"):
        validate_compute_storage_artifacts(manifest, result.receipt)

    receipt = copy.deepcopy(result.receipt)
    receipt["real_counters"]["measured_runs"] = 1
    with pytest.raises(ValueError, match="receipt_sha256"):
        validate_compute_storage_artifacts(result.manifest, receipt)


@pytest.mark.parametrize("repetitions", [True, 0, 2, 102])
def test_a08_repetition_bounds_fail_closed(repetitions) -> None:
    with pytest.raises(ValueError, match="repetitions"):
        run_compute_storage_feasibility_fixture(repetitions=repetitions)
