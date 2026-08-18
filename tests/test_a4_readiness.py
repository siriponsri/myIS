"""Focused contract-only tests for the A4 readiness scaffold."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex.a4_readiness import (
    A4ReadinessError,
    SELECTION_PREFLIGHT_CHECKS,
    consume_selection_preflight_counter,
    non_dominated_frontier,
    validate_a3_bindings,
    validate_commercial_eligibility,
    validate_legal_transfer_isolation,
    validate_production_profile_manifest,
)


ROOT = Path(__file__).parents[1]
MANIFEST = json.loads(
    (ROOT / "control/armindex/a3/a3-three-primary-preparation-manifest.v1.json").read_text()
)
AUTHORITY = json.loads(
    (ROOT / "control/armindex/a3/a3-three-primary-preparation-authority.v1.json").read_text()
)
HASH = "a" * 64


def _license_matrix() -> list[dict[str, str]]:
    return [
        {"arm_id": "ARM-01", "license": "MIT", "commercial_status": "commercial_capable"},
        {"arm_id": "ARM-02", "license": "MIT", "commercial_status": "commercial_capable"},
        {"arm_id": "ARM-03", "license": "CC-BY-NC-SA-4.0", "commercial_status": "research_non_commercial"},
        {"arm_id": "ARM-04", "license": "Apache-2.0", "commercial_status": "commercial_capable"},
        {"arm_id": "ARM-05", "license": "Apache-2.0", "commercial_status": "commercial_capable"},
    ]


def _profiles() -> dict[str, object]:
    rows = [
        {
            "profile_id": "FAST",
            "harness_configuration_sha256": HASH,
            "arm_ids": ["ARM-01", "ARM-04"],
            "mode": "synchronous",
            "maximum_candidate_depth": 100,
            "commercial_only": True,
            "readiness": "contract_only",
            "a3_binding_sha256": HASH,
            "non_dominated": True,
        },
        {
            "profile_id": "BALANCED",
            "harness_configuration_sha256": HASH,
            "arm_ids": ["ARM-04", "ARM-05"],
            "mode": "synchronous",
            "maximum_candidate_depth": 200,
            "commercial_only": True,
            "readiness": "contract_only",
            "a3_binding_sha256": HASH,
            "non_dominated": True,
        },
        {
            "profile_id": "DEEP",
            "harness_configuration_sha256": HASH,
            "arm_ids": ["ARM-04", "ARM-05"],
            "mode": "asynchronous",
            "maximum_candidate_depth": 1000,
            "commercial_only": True,
            "readiness": "contract_only",
            "a3_binding_sha256": HASH,
            "non_dominated": True,
        },
    ]
    return {
        "schema_version": "myis.armindex-a4-production-profile-manifest.v1",
        "status": "contract_only",
        "measured_execution": False,
        "selection_accesses": 0,
        "final_accesses": 0,
        "profiles": rows,
    }


def test_a3_preparation_is_pending_and_closeout_is_fail_closed() -> None:
    result = validate_a3_bindings(MANIFEST, AUTHORITY)
    assert result["status"] == "pending_a3_closeout"
    with pytest.raises(A4ReadinessError, match="closeout state"):
        validate_a3_bindings(MANIFEST, AUTHORITY, require_closeout=True)


def test_a3_transfer_matrix_is_exactly_nine_primary_cells() -> None:
    bad = {**MANIFEST, "transfer_matrix": MANIFEST["transfer_matrix"][:-1]}
    with pytest.raises(A4ReadinessError, match="nine"):
        validate_a3_bindings(bad, AUTHORITY)


def test_commercial_eligibility_excludes_patembed() -> None:
    result = validate_commercial_eligibility(_license_matrix(), ["ARM-03", "ARM-04"])
    assert result["excluded_arm_ids"] == ["ARM-03"]
    with pytest.raises(A4ReadinessError, match="non-commercial"):
        validate_commercial_eligibility(_license_matrix(), ["ARM-03", "ARM-04"], commercial_only=True)


def test_non_dominated_frontier_is_deterministic() -> None:
    points = [
        {"profile_id": "slow", "recall_at_100": 0.80, "throughput_qps": 2, "latency_p95_ms": 100, "cost_per_query_usd": 0.04, "index_size_bytes": 20},
        {"profile_id": "fast", "recall_at_100": 0.78, "throughput_qps": 8, "latency_p95_ms": 40, "cost_per_query_usd": 0.01, "index_size_bytes": 10},
        {"profile_id": "dominated", "recall_at_100": 0.70, "throughput_qps": 1, "latency_p95_ms": 200, "cost_per_query_usd": 0.10, "index_size_bytes": 40},
    ]
    assert non_dominated_frontier(points) == ("fast", "slow")


def test_profile_manifest_is_complete_and_contract_only() -> None:
    result = validate_production_profile_manifest(_profiles(), _license_matrix(), a3_binding_sha256=HASH)
    assert result["profiles"] == ["BALANCED", "DEEP", "FAST"]
    bad = _profiles()
    bad["profiles"] = bad["profiles"][:-1]
    with pytest.raises(A4ReadinessError, match="FAST, BALANCED"):
        validate_production_profile_manifest(bad, _license_matrix(), a3_binding_sha256=HASH)


def test_legal_transfer_isolated_and_protected_fields_rejected() -> None:
    transfer = {
        "transfer_id": "legal-mini-01",
        "source_arm_id": "ARM-04",
        "target_domain": "legal_structured_retrieval",
        "source_program_sha256": HASH,
        "target_adapter_sha256": HASH,
        "mapping_sha256": HASH,
        "transfer_state": "TRANSFER_MIXED",
        "feedback_into_patent_campaign": False,
        "protected_data_accessed": False,
        "selection_accesses": 0,
        "final_accesses": 0,
    }
    assert validate_legal_transfer_isolation(transfer)["status"] == "isolated"
    with pytest.raises(A4ReadinessError, match="protected"):
        validate_legal_transfer_isolation({**transfer, "qrels": "forbidden"})


def test_selection_preflight_counter_is_one_shot_and_fail_closed(tmp_path: Path) -> None:
    checks = {name: True for name in SELECTION_PREFLIGHT_CHECKS}
    path = tmp_path / "a4" / "selection-preflight-counter.json"
    receipt = consume_selection_preflight_counter(
        path, request_id="a4-selection-preflight-001", frozen_bindings_sha256=HASH, checks=checks
    )
    assert receipt["preflight_count"] == 1
    assert receipt["selection_accesses"] == 0
    with pytest.raises(A4ReadinessError, match="already consumed"):
        consume_selection_preflight_counter(
            path, request_id="a4-selection-preflight-002", frozen_bindings_sha256=HASH, checks=checks
        )
    assert json.loads(path.read_text())["preflight_count"] == 1

