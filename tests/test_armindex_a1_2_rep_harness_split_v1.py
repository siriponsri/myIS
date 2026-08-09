from __future__ import annotations

from pathlib import Path

from myis_research.armindex import a1_2_rep_harness_split_v1 as split
from myis_research.kernel.canonical import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]


def test_owner_decision_is_hash_bound_to_implementation() -> None:
    decision = split.validate_decision(ROOT)
    assert decision["status"] == "AUTHORIZED_PRE_MEASUREMENT"
    assert decision["grouping_policy"]["constraints"] == []


def test_hamilton_allocation_uses_lexical_tie_break() -> None:
    assert split._hamilton_rep_allocations({"IN|00000020": 71, "IN+OUT|00000020": 176, "OUT|00000020": 3}, 150) == {
        "IN|00000020": 43,
        "IN+OUT|00000020": 105,
        "OUT|00000020": 2,
    }


def test_derive_membership_is_replay_stable(monkeypatch) -> None:
    parent_ids = [f"query-{index:03d}" for index in range(250)]
    parent = {
        "schema_version": "myis.protected-split.v1",
        "seed": 42,
        "algorithm": "sha256-seed-colon-id-lexical-v1",
        "train": parent_ids,
        "selection": [],
        "final": [],
    }
    parent_hash = canonical_sha256(parent)
    parent["split_sha256"] = parent_hash
    monkeypatch.setattr(split, "PARENT_SPLIT_SHA256", parent_hash)
    monkeypatch.setattr(split, "PARENT_SPLIT_FILE_SHA256", "f" * 64)
    rows = []
    for index, query_id in enumerate(parent_ids):
        role_families = [("IN", 20)] if index < 71 else [("IN", 10), ("OUT", 10)] if index < 247 else [("OUT", 20)]
        family_number = 0
        for role, count in role_families:
            for _ in range(count):
                rows.append({"query_id": query_id, "relevant_id": f"family-{index:03d}-{family_number:02d}", "relevance_score": 1.0, "domain_rel": role})
                family_number += 1
    decision = {"decision_id": "test-decision", "decision_sha256": "d" * 64}
    _, safe_a = split.derive_membership(parent, rows, decision=decision, algorithm_source_sha256="a" * 64, source_hashes={"relations_arrow_sha256": "b" * 64})
    _, safe_b = split.derive_membership(parent, list(reversed(rows)), decision=decision, algorithm_source_sha256="a" * 64, source_hashes={"relations_arrow_sha256": "b" * 64})
    assert safe_a["counts"] == {"parent_train": 250, "rep_dev": 150, "harness_dev": 100}
    assert safe_a["rep_dev_membership_sha256"] == safe_b["rep_dev_membership_sha256"]
    assert safe_a["harness_dev_membership_sha256"] == safe_b["harness_dev_membership_sha256"]
    assert [item["parent_count"] for item in safe_a["strata"]] == [71, 176, 3]
    assert [item["rep_dev_count"] for item in safe_a["strata"]] == [43, 105, 2]
    assert [item["harness_dev_count"] for item in safe_a["strata"]] == [28, 71, 1]
