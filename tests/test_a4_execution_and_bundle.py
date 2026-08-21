from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from myis_research.armindex.a4_asset_bundle import (
    build_a4_hdev_runtime_package,
    validate_a4_hdev_runtime_package,
)
from myis_research.armindex.a4_execution import (
    A4ExecutionError,
    build_a4_admission,
    build_conditional_d2_receipt,
    build_d1_continuation_receipt,
    build_profile_registry,
    freeze_selection_registry,
    validate_a4_predecessor_binding,
)


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
ATTEMPT = "a4-goal001-20260819T010203Z"


def _binding() -> dict:
    path = Path("control/armindex/a4/a4-readiness-binding-20260819.json")
    return json.loads(path.read_text(encoding="utf-8"))


def _registry() -> dict:
    binding = _binding()
    return build_profile_registry(
        attempt_id=ATTEMPT,
        predecessor_binding_sha256=binding["binding_sha256"],
        hdev_commitment_sha256=HASH_A,
        evaluator_binding_sha256=HASH_B,
        runtime_binding_sha256=HASH_C,
        license_binding_sha256=HASH_D,
        profiles=[
            {"profile_id": "FAST", "system_sha256": "1" * 64, "arm_ids": ["ARM-01", "ARM-04"], "mode": "synchronous", "candidate_depth": 100, "commercial_only": True},
            {"profile_id": "BALANCED", "system_sha256": "2" * 64, "arm_ids": ["ARM-01", "ARM-04", "ARM-05"], "mode": "synchronous", "candidate_depth": 100, "commercial_only": True},
            {"profile_id": "DEEP", "system_sha256": "3" * 64, "arm_ids": ["ARM-01", "ARM-04", "ARM-05"], "mode": "asynchronous", "candidate_depth": 200, "commercial_only": True},
        ],
        research_reference={"system_sha256": "4" * 64, "arm_ids": ["ARM-03"], "license_scope": "research_only", "label": "ARM-03_RESEARCH_REFERENCE"},
    )


def test_predecessor_profile_and_selection_boundaries() -> None:
    binding = validate_a4_predecessor_binding(_binding())
    registry = _registry()
    assert registry["expected_hdev_query_count"] == 100
    assert [item["profile_id"] for item in registry["profiles"]] == ["BALANCED", "DEEP", "FAST"]
    with pytest.raises(A4ExecutionError, match="commercial profile"):
        build_profile_registry(
            attempt_id=ATTEMPT,
            predecessor_binding_sha256=binding["binding_sha256"],
            hdev_commitment_sha256=HASH_A,
            evaluator_binding_sha256=HASH_B,
            runtime_binding_sha256=HASH_C,
            license_binding_sha256=HASH_D,
            profiles=[
                {"profile_id": "FAST", "system_sha256": "1" * 64, "arm_ids": ["ARM-01", "ARM-03"], "mode": "synchronous", "candidate_depth": 100, "commercial_only": True},
                {"profile_id": "BALANCED", "system_sha256": "2" * 64, "arm_ids": ["ARM-01", "ARM-04"], "mode": "synchronous", "candidate_depth": 100, "commercial_only": True},
                {"profile_id": "DEEP", "system_sha256": "3" * 64, "arm_ids": ["ARM-01", "ARM-04"], "mode": "asynchronous", "candidate_depth": 100, "commercial_only": True},
            ],
            research_reference={"system_sha256": "4" * 64, "arm_ids": ["ARM-03"], "license_scope": "research_only", "label": "ARM-03_RESEARCH_REFERENCE"},
        )
    frozen = freeze_selection_registry(
        [
            {"role": "static_common_baseline", "system_sha256": "5" * 64, "license_scope": "commercial_capable", "source_receipt_sha256": "6" * 64},
            {"role": "research_champion", "system_sha256": "7" * 64, "license_scope": "research_only", "source_receipt_sha256": "8" * 64},
            {"role": "commercial_production_champion", "system_sha256": "5" * 64, "license_scope": "commercial_capable", "source_receipt_sha256": "9" * 64},
        ],
        profile_registry_sha256=registry["registry_sha256"],
    )
    assert len(frozen["finalists"]) == 2
    with pytest.raises(A4ExecutionError, match="protected"):
        freeze_selection_registry(
            [{"role": "static_common_baseline", "system_sha256": "5" * 64, "license_scope": "commercial_capable", "source_receipt_sha256": "6" * 64, "query_id": "forbidden"}],
            profile_registry_sha256=registry["registry_sha256"],
        )


def test_admission_reserves_a5_and_d2_requires_all_predicates() -> None:
    binding = _binding()
    now = datetime(2026, 8, 19, tzinfo=timezone.utc)
    d1 = build_d1_continuation_receipt(
        attempt_id=ATTEMPT,
        predecessor_binding_sha256=binding["binding_sha256"],
        goal_revision="a" * 40,
        recorded_at_utc=now,
    )
    admission = build_a4_admission(
        attempt_id=ATTEMPT,
        predecessor=binding,
        d1_receipt=d1,
        provider_identity={"provider": "vast", "instance_id": 47790578, "machine_id": 134131, "status": "running", "gpu_count": 4, "gpu_model": "RTX_3090", "ssh_runtime_sha256": HASH_A},
        observed_at_utc=now,
        now_utc=now,
        all_fee_usd_per_hour="0.6456",
        target_ttl_seconds=48 * 60 * 60,
        ttl_seconds_remaining=None,
        current_campaign_accrued_usd="89.6883",
        a4_projected_usd="10",
        a5_reserved_usd="8",
    )
    assert admission["budget_admission"]["a5_reserved_usd"] == "8"
    predicates = {
        "all_a4_coverage": True,
        "selection_count_valid": True,
        "legal_isolation": True,
        "safe_return": True,
        "independent_audit": True,
        "a5_bundle_clean_pushed": True,
        "finalist_frozen": True,
        "protected_boundary": True,
        "a5_budget_reserve": True,
        "a5_provenance_pass": True,
    }
    receipt = build_conditional_d2_receipt(
        a4_result_audit_sha256=HASH_A,
        a4_safe_return_sha256=HASH_B,
        a5_bundle_sha256=HASH_C,
        final_registry_sha256=HASH_D,
        final_split_commitment_sha256="e" * 64,
        clean_git_commit="f" * 40,
        clean_git_tree="1" * 40,
        selection_accesses=1,
        final_accesses=0,
        a5_provenance_audit_sha256="9" * 64,
        automatic_pass=predicates,
    )
    assert receipt["owner_conditional_approval"] is True
    assert receipt["a5_provenance_audit_sha256"] == "9" * 64
    predicates["a5_budget_reserve"] = False
    with pytest.raises(A4ExecutionError, match="automatic PASS"):
        build_conditional_d2_receipt(
            a4_result_audit_sha256=HASH_A,
            a4_safe_return_sha256=HASH_B,
            a5_bundle_sha256=HASH_C,
            final_registry_sha256=HASH_D,
            final_split_commitment_sha256="e" * 64,
            clean_git_commit="f" * 40,
            clean_git_tree="1" * 40,
            selection_accesses=1,
            final_accesses=0,
            a5_provenance_audit_sha256="9" * 64,
            automatic_pass=predicates,
        )


def test_conditional_d2_rejects_unresolved_a5_provenance() -> None:
    predicates = {
        "all_a4_coverage": True,
        "selection_count_valid": True,
        "legal_isolation": True,
        "safe_return": True,
        "independent_audit": True,
        "a5_bundle_clean_pushed": True,
        "finalist_frozen": True,
        "protected_boundary": True,
        "a5_budget_reserve": True,
        "a5_provenance_pass": False,
    }
    with pytest.raises(A4ExecutionError, match="automatic PASS"):
        build_conditional_d2_receipt(
            a4_result_audit_sha256=HASH_A,
            a4_safe_return_sha256=HASH_B,
            a5_bundle_sha256=HASH_C,
            final_registry_sha256=HASH_D,
            final_split_commitment_sha256="e" * 64,
            clean_git_commit="f" * 40,
            clean_git_tree="1" * 40,
            selection_accesses=1,
            final_accesses=0,
            a5_provenance_audit_sha256="9" * 64,
            automatic_pass=predicates,
        )

    predicates.pop("a5_provenance_pass")
    with pytest.raises(A4ExecutionError, match="automatic PASS"):
        build_conditional_d2_receipt(
            a4_result_audit_sha256=HASH_A,
            a4_safe_return_sha256=HASH_B,
            a5_bundle_sha256=HASH_C,
            final_registry_sha256=HASH_D,
            final_split_commitment_sha256="e" * 64,
            clean_git_commit="f" * 40,
            clean_git_tree="1" * 40,
            selection_accesses=1,
            final_accesses=0,
            a5_provenance_audit_sha256="9" * 64,
            automatic_pass=predicates,
        )


def test_hdev_runtime_package_is_fresh_and_complete(tmp_path: Path) -> None:
    source = tmp_path / "source"
    (source / "programs").mkdir(parents=True)
    (source / "models").mkdir()
    (source / "corpus.jsonl").write_text('{"family_token":"F-1","publication_token":"P-1","title_en":"a","abstract_en":"b","claims_text":"c"}\n', encoding="utf-8")
    for arm in ("ARM-03", "ARM-04", "ARM-05"):
        (source / "programs" / f"{arm}.json").write_text("{}\n", encoding="utf-8")
        model = source / "models" / arm
        model.mkdir()
        (model / "model.bin").write_bytes(arm.encode("ascii"))
    train = tmp_path / "train"
    (train / "inputs").mkdir(parents=True)
    tokens = [f"Q-{index:03d}" for index in range(100)]
    (train / "inputs" / "queries.jsonl").write_text("".join(json.dumps({"work_token": token, "text": f"query {token}"}) + "\n" for token in tokens), encoding="utf-8")
    split = tmp_path / "split.json"
    split.write_text(json.dumps({"harness_dev": tokens}), encoding="utf-8")
    receipt = build_a4_hdev_runtime_package(
        source_assets_root=source,
        train_package_root=train,
        split_membership_path=split,
        output_root=tmp_path / "a4-package",
        attempt_id=ATTEMPT,
        predecessor_binding=_binding(),
        profile_registry=_registry(),
    )
    assert receipt["hdev_query_count"] == 100
    checked = validate_a4_hdev_runtime_package(tmp_path / "a4-package", expected_attempt_id=ATTEMPT)
    assert checked["receipt_sha256"] == receipt["receipt_sha256"]
