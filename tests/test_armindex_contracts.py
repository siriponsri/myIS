from __future__ import annotations

import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from myis_research.armindex import (
    ACTIVE_PHASE_IDS,
    ARM_IDS,
    ArmIndexContractError,
    build_armindex_projection,
    compile_representation,
    validate_campaign,
    validate_harness,
    validate_mlflow_migration_receipt,
    validate_model_adapter_lock,
    validate_research_flow_terminal,
    validate_representation_program,
)
from myis_research.armindex.brain import build_moc, query_memories, validate_memory
from myis_research.armindex.contracts import canonical_sha256, load_campaign
from myis_research.asset_registry import load_registry, query_assets
from myis_research.mlflow_mirror import ARMINDEX_EXPERIMENT, armindex_run_tags


ROOT = Path(__file__).resolve().parents[1]


def _hashed(value: dict[str, object], field: str) -> dict[str, object]:
    result = dict(value)
    result[field] = canonical_sha256(value)
    return result


def test_active_campaign_has_exact_arms_phases_gates_and_zero_migration_counters() -> None:
    campaign = load_campaign(ROOT)
    validate_campaign(ROOT, campaign)
    assert tuple(item["id"] for item in campaign["arms"]) == ARM_IDS
    assert tuple(item["id"] for item in campaign["phases"]) == ACTIVE_PHASE_IDS
    assert campaign["gates"]["owner"] == ["D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"]
    assert campaign["campaign"]["migration_measured_runs"] == 0
    assert campaign["campaign"]["selection_accesses"] == 0
    assert campaign["campaign"]["final_accesses"] == 0


def test_armindex_projection_is_complete_and_historical_scope_is_separate() -> None:
    projection = build_armindex_projection(ROOT)
    assert projection["campaign_id"] == "armindex-multiretriever-v2"
    assert len(projection["arms"]) == 5
    assert len(projection["phases"]) == 7
    assert {item["profile_id"] for item in projection["production_profiles"]} == {"FAST", "BALANCED", "DEEP"}
    assert projection["champions"] == {"research": None, "commercial": None}
    assert projection["historical_campaigns"][0]["campaign_id"] == "scope-autoindex-v1"
    assert all(value == 0 for value in projection["counters"].values())


def test_representation_compiler_is_order_independent_and_content_addressed() -> None:
    program = _hashed(
        {
            "schema_version": "myis.armindex-representation-program.v1",
            "program_id": "fixture-title-abstract",
            "arm_id": "ARM-01",
            "source_fields": ["title", "abstract"],
            "field_order": ["title", "abstract"],
            "field_labels": {"title": "TITLE", "abstract": "ABSTRACT"},
            "unitization": {"kind": "family", "logical_size": None, "overlap": 0},
            "normalization": "unicode_nfkc_whitespace",
            "duplicate_policy": "content_hash_first",
            "family_aggregation": "single_unit",
            "preserve_family_identity": True,
        },
        "program_sha256",
    )
    validate_representation_program(ROOT, program)
    documents = [
        {"family_id": "F-002", "title": "Beta", "abstract": "Two   spaces"},
        {"family_id": "F-001", "title": "Alpha", "abstract": "One"},
    ]
    forward = compile_representation(program, documents)
    reverse = compile_representation(program, reversed(documents))
    assert forward == reverse
    assert [item["family_id"] for item in forward] == ["F-001", "F-002"]
    assert all(len(item["content_sha256"]) == 64 for item in forward)


def test_model_adapter_lock_rejects_patemebed_as_commercial() -> None:
    lock = _hashed(
        {
            "schema_version": "myis.armindex-model-adapter-lock.v1",
            "arm_id": "ARM-03",
            "model_id": "datalyes/patembed-large",
            "resolved_model_sha": "a" * 40,
            "tokenizer_sha256": "b" * 64,
            "adapter_sha256": "c" * 64,
            "input_format": {"query_prefix": "encode query for different document retrieval: "},
            "pooling": "mean_non_padding",
            "normalization": "l2",
            "dimension": 1024,
            "max_input_tokens": 512,
            "precision": "fp32",
            "similarity": "cosine",
            "license": "CC-BY-NC-SA-4.0",
            "commercial_status": "research_non_commercial",
            "network_required": False,
        },
        "lock_sha256",
    )
    validate_model_adapter_lock(ROOT, lock)
    commercial = {**lock, "commercial_status": "commercial_capable"}
    commercial["lock_sha256"] = canonical_sha256({key: value for key, value in commercial.items() if key != "lock_sha256"})
    with pytest.raises(ArmIndexContractError, match="research/non-commercial"):
        validate_model_adapter_lock(ROOT, commercial)


def test_harness_contract_rejects_forbidden_mutation_and_enforces_fast_profile() -> None:
    harness = _hashed(
        {
            "schema_version": "myis.armindex-harness.v1",
            "harness_id": "fixture-fast",
            "profile": "FAST",
            "arm_ids": ["ARM-01", "ARM-02"],
            "invocation_order": ["ARM-01", "ARM-02"],
            "depth_by_arm": {"ARM-01": 100, "ARM-02": 100},
            "fusion": "rrf_60",
            "early_stop": {"max_escalations": 1},
            "fallback_arm_id": "ARM-01",
            "max_cost_per_query_usd": 0.01,
            "max_p95_latency_ms": 500,
            "runtime_features": ["query_length", "cache_state"],
        },
        "harness_sha256",
    )
    validate_harness(ROOT, harness)
    invalid = {**harness, "runtime_features": ["query_rewriting"]}
    invalid["harness_sha256"] = canonical_sha256({key: value for key, value in invalid.items() if key != "harness_sha256"})
    with pytest.raises(ArmIndexContractError):
        validate_harness(ROOT, invalid)


def test_research_flow_terminal_is_hash_bound() -> None:
    receipt = _hashed(
        {
            "schema_version": "myis.armindex-research-flow-terminal.v1",
            "receipt_id": "fixture-rf-terminal",
            "campaign_id": "armindex-multiretriever-v2",
            "phase_id": "A2_PER_ARM_AUTOINDEX",
            "task_id": "A2.1",
            "research_flow_id": "RF-C",
            "terminal_state": "STOP_WITH_EVIDENCE_FLAT_REPRESENTATION_SURFACE",
            "evidence_ids": ["fixture-evidence"],
            "counters": {"candidates": 8},
            "protected_data_accessed": False,
        },
        "receipt_sha256",
    )
    validate_research_flow_terminal(ROOT, receipt)
    with pytest.raises(ArmIndexContractError, match="hash mismatch"):
        validate_research_flow_terminal(ROOT, {**receipt, "terminal_state": "FREEZE_ARM_PROGRAM"})


def test_brain_memory_is_pointer_first_queryable_and_deterministic() -> None:
    source_sha = hashlib.sha256((ROOT / "PLAN.md").read_bytes()).hexdigest()
    record = {
        "schema_version": "myis.armindex-brain-memory.v1",
        "memory_id": "ARMIDX-A0-ACTIVE",
        "campaign_id": "armindex-multiretriever-v2",
        "phase_id": "A0_MIGRATION_FOUNDATION",
        "task_id": "A0.3",
        "research_flow_id": None,
        "memory_type": "active_context",
        "title": "ArmIndex migration context",
        "interpretation": "ArmIndex is active; measured counters remain zero.",
        "source_uri": "PLAN.md",
        "source_sha256": source_sha,
        "evidence_ids": ["armindex-migration-20260804"],
        "arm_ids": list(ARM_IDS),
        "model_ids": [],
        "representation_program_ids": [],
        "harness_ids": [],
        "created_at": "2026-08-04T00:00:00Z",
        "reviewed_at": "2026-08-04T00:00:00Z",
        "status": "active",
        "supersedes": None,
        "superseded_by": None,
        "evidence_role": "engineering",
        "expires_at": "2030-01-01T00:00:00Z",
    }
    validate_memory(ROOT, record, now=datetime(2026, 8, 4, tzinfo=timezone.utc))
    assert query_memories([record], campaign_id="armindex-multiretriever-v2", arm="ARM-01") == [record]
    assert build_moc([record]) == build_moc(reversed([record]))


def test_armindex_mlflow_tags_are_safe_and_active_experiment_is_registered() -> None:
    tags = armindex_run_tags(
        phase_id="A0_MIGRATION_FOUNDATION",
        task_id="A0.4",
        research_flow_id="RF-A",
        run_id="fixture-a0",
        parent_run_id="fixture-parent",
        arm_id="ARM-01",
        model_id="lexical/bm25s",
    )
    assert ARMINDEX_EXPERIMENT == "myis-armindex-multiretriever-v2"
    assert tags["campaign_id"] == "armindex-multiretriever-v2"
    assert "qrels" not in str(tags).lower()

    layout = yaml.safe_load((ROOT / "control/layout.v2.yaml").read_text(encoding="utf-8"))
    assert layout["index_names"]["mlflow_experiment"] == ARMINDEX_EXPERIMENT


def test_mlflow_migration_receipt_is_hash_bound_and_path_safe() -> None:
    receipt = _hashed(
        {
            "schema_version": "myis.armindex-mlflow-migration-receipt.v1",
            "migration_id": "armindex-main-migration-20260804",
            "status": "PASS",
            "evidence_class": "engineering_migration",
            "scientific_authority": False,
            "claim_boundary": "infrastructure_migration_only",
            "store_uri": "external-store://myis/mlflow",
            "active_experiment": ARMINDEX_EXPERIMENT,
            "historical_experiment": "myis-scope-autoindex-v1",
            "governed_experiment_count": 9,
            "legacy_experiment_count": 7,
            "archive_counts": {"receipts": 48, "runs": 48, "artifacts": 572},
            "doctor_checks": {"archive_lineage": True, "v2_experiments_present": True},
            "protected_artifacts_mirrored": False,
            "migration_scientific_metrics_logged": False,
            "dataset_access": "none",
            "validated_implementation_commit": "a" * 40,
            "recorded_at_utc": "2026-08-04T00:00:00Z",
        },
        "receipt_sha256",
    )
    validate_mlflow_migration_receipt(ROOT, receipt)
    with pytest.raises(ArmIndexContractError, match="hash mismatch"):
        validate_mlflow_migration_receipt(ROOT, {**receipt, "governed_experiment_count": 10})


def test_reusable_assets_cover_armindex_without_opening_protected_data_in_a0() -> None:
    registry = load_registry(ROOT)
    a0_assets = {item["asset_id"] for item in query_assets(registry, task_id="A0.3")}
    assert "BRAIN-CURATED-MEMORY" in a0_assets
    assert "APP-DAPFAM-PROTECTED" not in a0_assets
    assert "APP-DAPFAM-PROTECTED" in {
        item["asset_id"] for item in query_assets(registry, task_id="A1.1")
    }


def test_public_and_canonical_markdown_links_resolve() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/validate_markdown_links.py"), "--repository-root", str(ROOT)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_independent_migration_verifier_accepts_current_state() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_armindex_migration.py"), "--repository-root", str(ROOT)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
