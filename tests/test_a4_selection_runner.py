from __future__ import annotations

from pathlib import Path

import pytest

from myis_research.armindex.a4_execution import freeze_selection_registry
from myis_research.armindex.a4_selection_runner import (
    A4SelectionRunnerError,
    run_selection_owner_local,
)
from myis_research.kernel.canonical import canonical_sha256


LEFT = "a" * 64
RIGHT = "b" * 64


def _registry() -> dict:
    return freeze_selection_registry(
        [
            {"role": "static_common_baseline", "system_sha256": LEFT, "license_scope": "commercial_capable", "source_receipt_sha256": "c" * 64},
            {"role": "research_champion", "system_sha256": RIGHT, "license_scope": "research_only", "source_receipt_sha256": "d" * 64},
        ],
        profile_registry_sha256="e" * 64,
    )


def _counter(registry: dict) -> dict:
    body = {
        "schema_version": "myis.armindex-a4-selection-preflight-counter.v1",
        "preflight_count": 1,
        "request_id": "selection-fixture",
        "frozen_bindings_sha256": registry["registry_sha256"],
        "checks": {
            "a3_closeout_verified": True,
            "commercial_license_verified": True,
            "pareto_frontier_verified": True,
            "profiles_complete": True,
            "legal_transfer_isolated": True,
            "protected_boundary_verified": True,
        },
        "selection_accesses": 0,
        "final_accesses": 0,
        "recorded_at_utc": "2026-08-20T00:00:00Z",
    }
    return {**body, "counter_sha256": canonical_sha256(body)}


def _input() -> dict:
    left = [1.0] * 100 + [0.0] * 25
    right = [0.0] * 125
    return {
        "selection_input_sha256": "f" * 64,
        "selection_query_count": 125,
        "selection_population": "OUT",
        "comparison_family_id": "a4-selection-frozen-finalists-v1",
        "bootstrap_seed": 17,
        "comparisons": [
            {
                "comparison_id": "static-vs-research",
                "left_system_sha256": LEFT,
                "right_system_sha256": RIGHT,
                "metrics": {
                    "recall_at_100": {"left": left, "right": right},
                    "ndcg_at_100": {"left": left, "right": right},
                    "ndcg_at_10": {"left": left, "right": right},
                },
                "operational": {
                    "left": {"p95_latency_ms": 10, "cost_usd": 1, "index_size_bytes": 100},
                    "right": {"p95_latency_ms": 20, "cost_usd": 2, "index_size_bytes": 200},
                },
            }
        ],
    }


def test_selection_runner_returns_only_aggregate_receipt_and_writes_once(tmp_path: Path) -> None:
    output = tmp_path / "selection-receipt.json"
    receipt = run_selection_owner_local(_registry(), _input(), preflight_counter=_counter(_registry()), selection_output_path=output)
    comparison = receipt["comparisons"][0]
    assert receipt["selection_accesses"] == 1
    assert receipt["final_accesses"] == 0
    assert receipt["selection_query_count"] == 125
    assert comparison["decision"] == "LEFT"
    assert comparison["paired_effect"]["bootstrap_resamples"] == 10_000
    assert comparison["win_tie_loss"] == {"wins": 100, "ties": 25, "losses": 0}
    assert "metrics" not in comparison
    with pytest.raises(A4SelectionRunnerError, match="already exists"):
        run_selection_owner_local(_registry(), _input(), preflight_counter=_counter(_registry()), selection_output_path=output)


def test_selection_runner_rejects_wrong_count_or_registry_binding() -> None:
    wrong = _input()
    wrong["selection_query_count"] = 124
    registry = _registry()
    with pytest.raises(A4SelectionRunnerError, match="exactly 125"):
        run_selection_owner_local(registry, wrong, preflight_counter=_counter(registry))
    counter = _counter(registry)
    counter["frozen_bindings_sha256"] = "0" * 64
    counter["counter_sha256"] = canonical_sha256({key: value for key, value in counter.items() if key != "counter_sha256"})
    with pytest.raises(A4SelectionRunnerError, match="binding"):
        run_selection_owner_local(registry, _input(), preflight_counter=counter)
