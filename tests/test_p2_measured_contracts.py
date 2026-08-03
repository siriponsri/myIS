from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess

import pytest

from myis_research.kernel.canonical import canonical_sha256
from myis_research.p2 import (
    P2ContractError,
    can_admit_adaptive_batch,
    load_profile_uri,
    validate_measured_artifact,
    validate_stop_reason,
)
from myis_research.p2.base_candidates import (
    build_adaptive_policy,
    build_base_candidate_set,
    build_proposer_contract,
)
from myis_research.p2.measured_contracts import scientific_payload_sha256


ROOT = Path(__file__).resolve().parents[1]


def _rehash(payload: dict, field: str) -> dict:
    payload.pop(field, None)
    payload[field] = canonical_sha256(payload)
    return payload


def test_adopted_base_candidate_set_is_exact_hash_locked_and_deterministic() -> None:
    first = build_base_candidate_set(ROOT, committed_hashes=False)
    second = build_base_candidate_set(ROOT, committed_hashes=False)
    assert first == second
    validated = validate_measured_artifact(first, ROOT)
    assert validated["status"] == "adopted_hash_locked"
    assert len(validated["frozen_controls"]) == 4
    assert len(validated["preregistered_candidates"]) == 8
    assert validated["adapter_rule"]["publication_id_source"] == "relevant_id"
    assert all(item["spec_sha256"] == canonical_sha256(item["scope_spec"]) for item in [*validated["frozen_controls"], *validated["preregistered_candidates"]])


def test_adaptive_policy_and_proposer_contract_are_repository_safe() -> None:
    policy = validate_measured_artifact(build_adaptive_policy(), ROOT)
    proposer = validate_measured_artifact(build_proposer_contract(), ROOT)
    assert policy["batch_roles"] == ["exploit", "matched_ablation", "orthogonal", "diversity"]
    assert proposer["environment_removed"][:2] == ["MYIS_STORE", "MYIS_MLFLOW_STORE"]
    assert proposer["attempts_per_batch"] == 2
    assert proposer["protected_data_accessed"] is False


def test_adaptive_batch_requires_exact_ids_roles_and_single_axis_ablation() -> None:
    base = build_base_candidate_set(ROOT, committed_hashes=False)
    source = deepcopy(base["preregistered_candidates"][0])
    ablation_source = deepcopy(base["preregistered_candidates"][1])
    candidates = []
    definitions = (
        ("p2-r1-r02-i01-c01", "exploit", source, "p2-r1-r02-i01-c02", "source_fields"),
        ("p2-r1-r02-i01-c02", "matched_ablation", ablation_source, "p2-r1-r02-i01-c01", "source_fields"),
        ("p2-r1-r02-i01-c03", "orthogonal", base["preregistered_candidates"][4], None, "unitization"),
        ("p2-r1-r02-i01-c04", "diversity", base["preregistered_candidates"][7], None, "view_composition"),
    )
    for index, (candidate_id, role, definition, matched, axis) in enumerate(definitions, start=1):
        spec = deepcopy(definition["scope_spec"])
        spec["spec_id"] = f"spec-r01-i01-c{index:02d}-v01"
        spec["hypothesis_id"] = f"hyp-i01-{index:03d}"
        candidates.append({
            "candidate_id": candidate_id,
            "parent_candidate_id": definition["candidate_id"],
            "hypothesis_id": spec["hypothesis_id"],
            "hypothesis": definition["hypothesis"],
            "role": role,
            "declared_axis": axis,
            "matched_ablation_id": matched,
            "scope_spec": spec,
            "spec_sha256": canonical_sha256(spec),
            "scientific_payload_sha256": scientific_payload_sha256(spec),
            "axis_values": definition["axis_values"],
        })
    batch = _rehash({
        "schema_version": "myis.p2-scope-candidate-batch.v1",
        "batch_id": "p2-r1-r02-i01",
        "request_id": "p2-measured-test",
        "campaign_revision": "scope-autoindex-v1-p2-r1-primary-v2",
        "iteration": 1,
        "feedback_sha256": "a" * 64,
        "proposer_invocation_sha256": "b" * 64,
        "status": "frozen_before_measurement",
        "candidates": candidates,
    }, "batch_sha256")
    assert validate_measured_artifact(batch, ROOT)["batch_sha256"] == batch["batch_sha256"]

    invalid = deepcopy(batch)
    invalid["candidates"][1]["axis_values"]["unitization"] = "claim_element"
    _rehash(invalid, "batch_sha256")
    with pytest.raises(P2ContractError, match="exactly the declared"):
        validate_measured_artifact(invalid, ROOT)


def test_measured_contract_rejects_protected_feedback_keys() -> None:
    feedback = {
        "schema_version": "myis.p2-adaptive-feedback.v1",
        "feedback_id": "feedback-i01",
        "request_id": "request-1",
        "campaign_revision": "scope-autoindex-v1-p2-r1-primary-v2",
        "iteration": 1,
        "lineage_hashes": {"dataset_sha256": "a" * 64},
        "aggregate_candidates": [],
        "failure_categories": [],
        "remaining_axes": ["unitization"],
        "budget_counters": {"candidates": 12},
        "selection_exposures": 0,
        "protected_data_accessed": False,
        "query_ids": ["forbidden"],
    }
    _rehash(feedback, "feedback_sha256")
    with pytest.raises(P2ContractError, match="protected payload key"):
        validate_measured_artifact(feedback, ROOT)


def test_measured_schemas_are_valid_json() -> None:
    for path in sorted((ROOT / "schemas").glob("p2-*.v1.json")):
        json.loads(path.read_text(encoding="utf-8"))


def test_profile_v2_has_120_hour_wall_clock_and_whole_batch_admission() -> None:
    profile, profile_sha256 = load_profile_uri(
        ROOT,
        "control/budgets/p2-r1-primary-v2.yaml",
    )
    assert len(profile_sha256) == 64
    assert profile["runtime"] == {
        "max_wall_clock_seconds": 432000,
        "measurement_budget_seconds": 345600,
        "overhead_reserve_seconds": 86400,
        "per_candidate_timeout_seconds": 10800,
        "prevent_system_sleep": True,
    }
    assert can_admit_adaptive_batch(
        profile,
        consumed_measurement_seconds=302400,
        candidate_count=28,
    ) is True
    assert can_admit_adaptive_batch(
        profile,
        consumed_measurement_seconds=302401,
        candidate_count=28,
    ) is False
    assert can_admit_adaptive_batch(
        profile,
        consumed_measurement_seconds=0,
        candidate_count=29,
    ) is False
    for reason in profile["stopping"]["valid_reasons"]:
        assert validate_stop_reason(profile, reason) == reason
    with pytest.raises(P2ContractError, match="invalid"):
        validate_stop_reason(profile, "partial_batch")


def test_historical_profile_v1_remains_loadable() -> None:
    profile, _ = load_profile_uri(ROOT, "control/budgets/p2-r1-primary-v1.yaml")
    assert profile["profile_id"] == "p2-r1-primary-v1"
    assert profile["runtime"]["max_wall_clock_seconds"] == 259200


def test_measured_control_materializer_reports_no_drift() -> None:
    completed = subprocess.run(
        [
            "uv",
            "run",
            "--no-sync",
            "python",
            "scripts/build_p2_measured_controls.py",
            "--repository-root",
            ".",
            "--check",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
