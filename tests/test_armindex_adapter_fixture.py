from __future__ import annotations

import copy
import json

import pytest

from myis_research.armindex.adapter_fixture import (
    FIXTURE_ID,
    run_adapter_fixture,
    validate_adapter_fixture_artifacts,
)
from myis_research.protection import assert_aggregate_only


def test_a11_adapter_fixture_runs_arm01_on_cpu_and_blocks_dense_arms() -> None:
    result = run_adapter_fixture(repetitions=3)

    assert result.output_persisted is False
    assert result.manifest["fixture_id"] == FIXTURE_ID
    assert result.manifest["task_id"] == "A1.1"
    assert result.manifest["aggregate_counts"]["registered_arms"] == 5
    assert result.manifest["aggregate_counts"]["runnable_cpu_arms"] == 1
    assert result.manifest["aggregate_counts"]["dense_arms_blocked"] == 4
    assert result.manifest["arm01_backend"]["measured_lock_ready"] is False
    assert result.receipt["status"] == "PASS"
    assert set(result.receipt["real_counters"].values()) == {0}
    assert set(result.receipt["resource_counters"].values()) == {0}
    assert result.receipt["safety"]["cpu_only"] is True
    assert result.receipt["safety"]["synthetic_inputs_only"] is True
    assert_aggregate_only(result.manifest)
    assert_aggregate_only(result.receipt)


def test_a11_adapter_fixture_logical_commitments_are_repeatable() -> None:
    first = run_adapter_fixture(repetitions=3)
    second = run_adapter_fixture(repetitions=3)

    assert first.manifest == second.manifest
    assert (
        first.receipt["deterministic_execution_sha256"]
        == second.receipt["deterministic_execution_sha256"]
    )
    assert first.receipt["synthetic_metrics"] == second.receipt["synthetic_metrics"]


def test_a11_adapter_fixture_explicit_output_is_write_once(tmp_path) -> None:
    output = tmp_path / "a11-adapter-fixture"

    result = run_adapter_fixture(output, repetitions=3)

    assert result.output_persisted is True
    manifest = json.loads((output / "manifest.json").read_text(encoding="ascii"))
    receipt = json.loads((output / "receipt.json").read_text(encoding="ascii"))
    validate_adapter_fixture_artifacts(manifest, receipt)
    with pytest.raises(FileExistsError, match="must be empty"):
        run_adapter_fixture(output, repetitions=3)


def test_a11_adapter_fixture_validation_rejects_drift() -> None:
    result = run_adapter_fixture(repetitions=3)
    manifest = copy.deepcopy(result.manifest)
    manifest["aggregate_counts"]["dense_arms_blocked"] = 3
    with pytest.raises(ValueError, match="manifest_sha256"):
        validate_adapter_fixture_artifacts(manifest, result.receipt)

    receipt = copy.deepcopy(result.receipt)
    receipt["real_counters"]["measured_runs"] = 1
    with pytest.raises(ValueError, match="receipt_sha256"):
        validate_adapter_fixture_artifacts(result.manifest, receipt)


@pytest.mark.parametrize("repetitions", [True, 0, 2, 32])
def test_a11_adapter_fixture_repetition_bounds_fail_closed(repetitions) -> None:
    with pytest.raises(ValueError, match="repetitions"):
        run_adapter_fixture(repetitions=repetitions)
