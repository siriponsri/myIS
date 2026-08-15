from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import io
import json
import hashlib
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest
from myis_research.kernel.canonical import canonical_sha256

from myis_research.armindex.a2_execution_readiness import (
    A2ExecutionReadinessError,
    A2MeasuredRunner,
    append_lifecycle_checkpoint,
    build_execution_bundle,
    build_execution_adoption_receipt,
    build_execution_adoption_receipt_v3,
    build_lifecycle_checkpoint,
    build_provider_admission_receipt,
    build_provider_admission_receipt_v2,
    build_provider_admission_receipt_v3,
    build_provider_instance_binding,
    build_remote_staging_plan,
    build_safe_return_receipt,
    build_train_evaluation_receipt,
    build_winner_receipt,
    evaluate_aggregate_train_results,
    frozen_candidates,
    require_execution_adoption,
    resume_checkpoint,
    validate_execution_bundle,
    validate_execution_adoption_receipt_v3,
    validate_execution_ledger,
    validate_provider_admission_receipt,
    validate_provider_admission_receipt_v3,
    validate_forward_hard_cap_successor_v3,
    build_watchdog_script,
    _BUNDLE_CLOSURE,
)

ROOT = Path(__file__).resolve().parents[1]
ATTEMPT = "a2-readiness-test01"


def _fixture() -> dict[str, object]:
    return {
        "fixture_kind": "synthetic_a2_aggregate_v1",
        "rep_dev_measured": False,
        "per_query_outcomes_included": False,
        "metrics": {"synthetic_primary": "0.500000000000"},
    }


def _provider_evidence() -> dict[str, object]:
    return {
        "provider_instance_id": "47411176",
        "evidence_mode": "OwnerDashboardSsh",
        "provider_authenticated": False,
        "login_or_logout_performed": False,
        "observed_at_utc": "2026-08-12T08:00:00Z",
        "provider_status": "RUNNING",
        "provider_verification": "VERIFIED",
        "gpu_count": 4,
        "gpu_model": "RTX3090",
        "vram_mib_each": 24576,
        "ssh_host_key_sha256": "f" * 64,
        "management_mode": "OWNER_MANUAL_DASHBOARD_DESTROY_READY",
        "owner_manual_dashboard_destroy_ready": True,
        "provider_destroy_performed": False,
        "quote_observed_at_utc": "2026-08-12T08:00:00Z",
        "ttl_deadline_utc": "2026-08-14T08:00:00Z",
        "all_fee_components_usd": {
            "compute_usd": "30.00",
            "storage_usd": "1.00",
            "network_usd": "1.00",
            "platform_or_other_fee_usd": "0.50",
            "tax_or_surcharge_usd": "0.50",
        },
        "whole_workload_total_usd": "33.00",
    }


def _provider_observation_paths(tmp_path: Path, *, deadline: str = "2026-08-14T08:00:00Z") -> tuple[Path, dict[str, Path]]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    sources: dict[str, Path] = {}
    for name in ("runtime", "model_lockset", "data_handoff", "ssh_host_key", "management_authority"):
        path = tmp_path / f"{name}.txt"
        path.write_text(f"aggregate-safe {name}\n", encoding="ascii")
        sources[name] = path
    hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in sources.items()}
    observation = _provider_evidence()
    observation.update(
        {
            "schema_version": "myis.armindex-a2-provider-observation.v1",
            "observation_id": f"{ATTEMPT}-provider-observation-v1",
            "attempt_id": ATTEMPT,
            "source_mode": observation.pop("evidence_mode"),
            "ttl_deadline_utc": deadline,
            "remaining_ttl_seconds": int((datetime.fromisoformat(deadline.replace("Z", "+00:00")) - datetime(2026, 8, 12, 8, tzinfo=timezone.utc)).total_seconds()),
            "gpu_uuid_set_sha256": "e" * 64,
            "runtime_sha256": hashes["runtime"],
            "model_lockset_sha256": hashes["model_lockset"],
            "data_handoff_sha256": hashes["data_handoff"],
            "ssh_host_key_sha256": hashes["ssh_host_key"],
            "management_authority_sha256": hashes["management_authority"],
            "source_artifact_sha256": hashes,
            "source_artifacts": {
                name: {"uri": f"owner-store/a2-test/{path.name}", "file_sha256": hashes[name]}
                for name, path in sources.items()
            },
        }
    )
    observation["observation_sha256"] = canonical_sha256(observation)
    path = tmp_path / "provider-observation.json"
    path.write_text(json.dumps(observation), encoding="ascii")
    return path, sources


def _provider_observation_paths_v2(
    tmp_path: Path, *, instance_id: str = "58881234"
) -> tuple[Path, dict[str, Path]]:
    path, sources = _provider_observation_paths(tmp_path)
    observation = json.loads(path.read_text(encoding="ascii"))
    observation.update(
        {
            "schema_version": "myis.armindex-a2-provider-observation.v2",
            "observation_id": f"{ATTEMPT}-provider-observation-v2",
            "provider_instance_id": instance_id,
        }
    )
    observation.pop("observation_sha256")
    observation["observation_sha256"] = canonical_sha256(observation)
    path.write_text(json.dumps(observation), encoding="ascii")
    return path, sources


def _aggregate_results() -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for index, (candidate_id, candidate) in enumerate(frozen_candidates(ROOT).items()):
        rows[candidate_id] = {
            "fixture_kind": "synthetic_a2_train_result_v1",
            "candidate_id": candidate_id,
            "arm_id": candidate["arm_id"],
            "primary_metric": str(index + 1),
            "aggregate_metrics_sha256": "a" * 64,
            "train_only": True,
            "rep_dev_measured": False,
            "per_query_outcomes_included": False,
        }
    return rows


def test_frozen_membership_train_winner_and_safe_return_are_hash_bound() -> None:
    candidates = frozen_candidates(ROOT)
    assert len(candidates) == 52
    diagnostic_id = next(
        candidate_id
        for candidate_id, candidate in candidates.items()
        if candidate["arm_id"] == "ARM-01" and candidate["tier"] == "matched"
    )
    train = build_train_evaluation_receipt(
        ROOT,
        attempt_id=ATTEMPT,
        candidate_id=diagnostic_id,
        aggregate_fixture=_fixture(),
        allow_synthetic_fixture=True,
    )
    winner = build_winner_receipt(
        ROOT,
        attempt_id=ATTEMPT,
        arm_id="ARM-01",
        winner_candidate_id=diagnostic_id,
        train_evaluation_receipt_sha256=train["receipt_sha256"],
        strict_tie_rejected=True,
    )
    assert train["candidate_id"] == diagnostic_id
    assert winner["diagnostic_non_advancing"] is True
    assert winner["advancement_eligible"] is False


def test_safe_return_rejects_missing_archive(tmp_path: Path) -> None:
    with pytest.raises(A2ExecutionReadinessError, match="missing or unsafe"):
        build_safe_return_receipt(
            ROOT,
            attempt_id=ATTEMPT,
            archive_path=tmp_path / "missing.tar.gz",
            remote_root="/opt/myis/a2-readiness-test01",
        )


def test_safe_return_reads_archive_members_and_manifest_hashes(tmp_path: Path) -> None:
    archive_path = tmp_path / "safe-return.tar.gz"
    payload = b'{"aggregate_metric":"0.5"}\n'
    unsigned = {
        "attempt_id": ATTEMPT,
        "protected_payload_included": False,
        "members": [
            {"path": "aggregate.json", "sha256": hashlib.sha256(payload).hexdigest(), "size_bytes": len(payload)}
        ],
    }
    manifest = {**unsigned, "archive_manifest_sha256": canonical_sha256(unsigned)}
    with tarfile.open(archive_path, "w:gz") as bundle:
        member = tarfile.TarInfo("aggregate.json")
        member.size = len(payload)
        bundle.addfile(member, io.BytesIO(payload))
        encoded = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
        member = tarfile.TarInfo("A2_SAFE_RETURN_MANIFEST.json")
        member.size = len(encoded)
        bundle.addfile(member, io.BytesIO(encoded))
    receipt = build_safe_return_receipt(
        ROOT,
        attempt_id=ATTEMPT,
        archive_path=archive_path,
        remote_root=f"/opt/myis/{ATTEMPT}",
    )
    assert receipt["aggregate_artifact_count"] == 1
    assert receipt["archive_manifest_sha256"] == manifest["archive_manifest_sha256"]


def test_train_fixture_is_explicitly_test_only_and_rejects_rep_dev() -> None:
    candidate_id = next(iter(frozen_candidates(ROOT)))
    with pytest.raises(A2ExecutionReadinessError, match="test-only"):
        build_train_evaluation_receipt(
            ROOT,
            attempt_id=ATTEMPT,
            candidate_id=candidate_id,
            aggregate_fixture=_fixture(),
        )
    unsafe = _fixture()
    unsafe["rep_dev_measured"] = True
    with pytest.raises(A2ExecutionReadinessError, match="protected/REP-DEV"):
        build_train_evaluation_receipt(
            ROOT,
            attempt_id=ATTEMPT,
            candidate_id=candidate_id,
            aggregate_fixture=unsafe,
            allow_synthetic_fixture=True,
        )


def test_checkpoint_ledger_is_append_only_and_resumable(tmp_path: Path) -> None:
    ledger = tmp_path / "a2-ledger.jsonl"
    first = build_lifecycle_checkpoint(
        ROOT,
        attempt_id=ATTEMPT,
        sequence=1,
        status="STAGED",
        completed_candidate_count=0,
        failed_candidate_count=0,
        resume_allowed=True,
    )
    append_lifecycle_checkpoint(ledger, first)
    second = build_lifecycle_checkpoint(
        ROOT,
        attempt_id=ATTEMPT,
        sequence=2,
        status="PAUSED",
        completed_candidate_count=0,
        failed_candidate_count=0,
        resume_allowed=True,
        previous_checkpoint_sha256=first["checkpoint_sha256"],
    )
    append_lifecycle_checkpoint(ledger, second)

    assert resume_checkpoint(ledger, attempt_id=ATTEMPT)["checkpoint_sha256"] == second[
        "checkpoint_sha256"
    ]
    with pytest.raises(A2ExecutionReadinessError, match="append-only"):
        append_lifecycle_checkpoint(ledger, second)
    with pytest.raises(A2ExecutionReadinessError, match="exceed frozen"):
        build_lifecycle_checkpoint(
            ROOT,
            attempt_id=ATTEMPT,
            sequence=3,
            status="RUNNING",
            completed_candidate_count=52,
            failed_candidate_count=1,
            resume_allowed=True,
            previous_checkpoint_sha256=second["checkpoint_sha256"],
        )
    with pytest.raises(A2ExecutionReadinessError, match="cannot allow resume"):
        build_lifecycle_checkpoint(
            ROOT,
            attempt_id=ATTEMPT,
            sequence=3,
            status="SAFE_RETURNED",
            completed_candidate_count=52,
            failed_candidate_count=0,
            resume_allowed=True,
            previous_checkpoint_sha256=second["checkpoint_sha256"],
        )


def test_material_execution_ledger_is_schema_bound_and_append_only() -> None:
    rows = validate_execution_ledger(
        ROOT, ROOT / "control/armindex/a2/execution-ledger.v1.jsonl"
    )

    assert len(rows) == 6
    assert rows[0]["status"] == "MEASUREMENT_LOCKED"
    assert rows[1]["status"] == "FAILED_CLOSED"
    assert rows[1]["previous_entry_sha256"] == rows[0]["entry_sha256"]
    assert rows[2]["status"] == "IMPLEMENTATION_BLOCKED"
    assert rows[2]["previous_entry_sha256"] == rows[1]["entry_sha256"]
    assert rows[3]["status"] == "NEEDS_IM_NEW_INSTANCE_REBIND_MEASUREMENT_LOCKED"
    assert rows[3]["event_type"] == "implementation_completed"
    assert rows[3]["previous_entry_sha256"] == rows[2]["entry_sha256"]
    assert rows[4]["status"] == "READY_FOR_AP_FRESH_INSTANCE_STAGING_MEASUREMENT_LOCKED"
    assert rows[4]["event_type"] == "readiness_closure_completed"
    assert rows[4]["previous_entry_sha256"] == rows[3]["entry_sha256"]
    assert rows[5]["status"] == "EXTERNAL_EXECUTION_REQUESTED_NOT_LAUNCHED"
    assert rows[5]["event_type"] == "external_execution_requested"
    assert rows[5]["previous_entry_sha256"] == rows[4]["entry_sha256"]


def test_material_execution_ledger_rejects_rewritten_entry(tmp_path: Path) -> None:
    source = ROOT / "control/armindex/a2/execution-ledger.v1.jsonl"
    row = json.loads(source.read_text(encoding="utf-8").splitlines()[0])
    row["summary"] = "rewritten history"
    rewritten = tmp_path / "rewritten-ledger.jsonl"
    rewritten.write_text(json.dumps(row) + "\n", encoding="utf-8")

    with pytest.raises(A2ExecutionReadinessError, match="entry_sha256 is invalid"):
        validate_execution_ledger(ROOT, rewritten)


def test_fresh_instance_binding_drives_v2_admission_and_rejects_instance_drift(
    tmp_path: Path,
) -> None:
    observation_path, sources = _provider_observation_paths_v2(tmp_path)
    binding = build_provider_instance_binding(
        ROOT,
        attempt_id=ATTEMPT,
        provider_observation_path=observation_path,
        source_artifact_paths=sources,
    )
    admission = build_provider_admission_receipt_v2(
        ROOT,
        attempt_id=ATTEMPT,
        provider_observation_path=observation_path,
        source_artifact_paths=sources,
        instance_binding=binding,
        now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
    )
    assert admission["provider_instance_id"] == "58881234"
    assert admission["provider_instance_binding_sha256"] == binding["binding_sha256"]
    assert admission["forward_hard_stop_usd"] == 50

    drifted = json.loads(observation_path.read_text(encoding="ascii"))
    drifted["provider_instance_id"] = "58881235"
    drifted.pop("observation_sha256")
    drifted["observation_sha256"] = canonical_sha256(drifted)
    observation_path.write_text(json.dumps(drifted), encoding="ascii")
    with pytest.raises(A2ExecutionReadinessError, match="binding drift|mutation"):
        build_provider_admission_receipt_v2(
            ROOT,
            attempt_id=ATTEMPT,
            provider_observation_path=observation_path,
            source_artifact_paths=sources,
            instance_binding=binding,
            now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
        )


def test_v2_admission_uses_owner_expanded_usd_50_hard_stop(tmp_path: Path) -> None:
    observation_path, sources = _provider_observation_paths_v2(tmp_path)
    observation = json.loads(observation_path.read_text(encoding="ascii"))
    observation["all_fee_components_usd"]["compute_usd"] = "47.00"
    observation["whole_workload_total_usd"] = "50.00"
    observation.pop("observation_sha256")
    observation["observation_sha256"] = canonical_sha256(observation)
    observation_path.write_text(json.dumps(observation), encoding="ascii")
    binding = build_provider_instance_binding(
        ROOT,
        attempt_id=ATTEMPT,
        provider_observation_path=observation_path,
        source_artifact_paths=sources,
    )

    admission = build_provider_admission_receipt_v2(
        ROOT,
        attempt_id=ATTEMPT,
        provider_observation_path=observation_path,
        source_artifact_paths=sources,
        instance_binding=binding,
        now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
    )
    assert admission["whole_workload_total_usd"] == "50.00"
    assert admission["forward_hard_stop_usd"] == 50

    observation["all_fee_components_usd"]["compute_usd"] = "47.01"
    observation["whole_workload_total_usd"] = "50.01"
    observation.pop("observation_sha256")
    observation["observation_sha256"] = canonical_sha256(observation)
    observation_path.write_text(json.dumps(observation), encoding="ascii")
    binding = build_provider_instance_binding(
        ROOT,
        attempt_id=ATTEMPT,
        provider_observation_path=observation_path,
        source_artifact_paths=sources,
    )
    with pytest.raises(A2ExecutionReadinessError, match="exceeds the A2 hard stop"):
        build_provider_admission_receipt_v2(
            ROOT,
            attempt_id=ATTEMPT,
            provider_observation_path=observation_path,
            source_artifact_paths=sources,
            instance_binding=binding,
            now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
        )


def test_v3_usd_60_successor_binds_controls_and_preserves_ttl(tmp_path: Path) -> None:
    controls = validate_forward_hard_cap_successor_v3(ROOT)
    assert set(controls) == {
        "budget_profile_sha256",
        "execution_readiness_contract_sha256",
    }
    budget = json.loads(
        (ROOT / "control/budgets/a2-execution-readiness-v2.json").read_text(
            encoding="utf-8"
        )
    )
    assert budget["runtime_projection"]["concurrency_assumption"] == (
        "ARM-01 remote CPU on the same Vast instance; one isolated worker for "
        "each of ARM-02 through ARM-05"
    )
    contract = json.loads(
        (ROOT / "control/armindex/a2/execution-readiness-contract.v3.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["required_receipt_schemas"][-1] == (
        "schemas/armindex/a2-execution-adoption-receipt.v3.json"
    )

    observation_path, sources = _provider_observation_paths_v2(tmp_path)
    observation = json.loads(observation_path.read_text(encoding="ascii"))
    observation["all_fee_components_usd"]["compute_usd"] = "57.00"
    observation["whole_workload_total_usd"] = "60.00"
    observation.pop("observation_sha256")
    observation["observation_sha256"] = canonical_sha256(observation)
    observation_path.write_text(json.dumps(observation), encoding="ascii")
    binding = build_provider_instance_binding(
        ROOT,
        attempt_id=ATTEMPT,
        provider_observation_path=observation_path,
        source_artifact_paths=sources,
    )
    admission = build_provider_admission_receipt_v3(
        ROOT,
        attempt_id=ATTEMPT,
        provider_observation_path=observation_path,
        source_artifact_paths=sources,
        instance_binding=binding,
        now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
    )
    assert admission["forward_hard_stop_usd"] == 60
    assert admission["whole_workload_total_usd"] == "60.00"
    assert admission["budget_profile_sha256"] == controls["budget_profile_sha256"]
    assert admission["execution_readiness_contract_sha256"] == controls[
        "execution_readiness_contract_sha256"
    ]
    assert validate_provider_admission_receipt_v3(ROOT, admission) == admission

    observation["all_fee_components_usd"]["compute_usd"] = "57.01"
    observation["whole_workload_total_usd"] = "60.01"
    observation.pop("observation_sha256")
    observation["observation_sha256"] = canonical_sha256(observation)
    observation_path.write_text(json.dumps(observation), encoding="ascii")
    binding = build_provider_instance_binding(
        ROOT,
        attempt_id=ATTEMPT,
        provider_observation_path=observation_path,
        source_artifact_paths=sources,
    )
    with pytest.raises(A2ExecutionReadinessError, match="exceeds the A2 hard stop"):
        build_provider_admission_receipt_v3(
            ROOT,
            attempt_id=ATTEMPT,
            provider_observation_path=observation_path,
            source_artifact_paths=sources,
            instance_binding=binding,
            now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
        )


def test_v3_adoption_binds_the_usd_60_provider_and_controls(tmp_path: Path) -> None:
    observation_path, sources = _provider_observation_paths_v2(tmp_path)
    binding = build_provider_instance_binding(
        ROOT,
        attempt_id=ATTEMPT,
        provider_observation_path=observation_path,
        source_artifact_paths=sources,
    )
    admission = build_provider_admission_receipt_v3(
        ROOT,
        attempt_id=ATTEMPT,
        provider_observation_path=observation_path,
        source_artifact_paths=sources,
        instance_binding=binding,
        now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
    )
    bundle = {
        "schema_version": "myis.armindex-a2-execution-bundle-receipt.v1",
        "receipt_id": f"{ATTEMPT}-bundle-v1",
        "attempt_id": ATTEMPT,
        "status": "PASS_CLEAN_HASH_BOUND_A2_BUNDLE",
        "clean_worktree": True,
        "pushed_to_origin_main": True,
        "git_commit": "c" * 40,
        "git_tree": "d" * 40,
        "freeze_bindings": {
            "manifest_sha256": "f6276e3a15e760187152270418e00ce4cae4d8efe45b13edb02c4742e3b3049e",
            "freeze_receipt_sha256": "ea93db368c3e740f7914e07e2bdfc15052991f6f05976f6924acdce717392e10",
            "lock_sha256": "c01f683b909e6f4c6310c01855b3f79319a183b7950f91338d43baa8a2d57952",
        },
        "bundle_sha256": "1" * 64,
        "bundle_manifest_sha256": "2" * 64,
    }
    bundle["receipt_sha256"] = canonical_sha256(bundle)

    adoption = build_execution_adoption_receipt_v3(
        ROOT,
        attempt_id=ATTEMPT,
        provider_admission_receipt=admission,
        bundle_receipt=bundle,
        remote_root="/opt/myis/a2-readiness-test01",
        staged_bundle_sha256=bundle["bundle_sha256"],
        watchdog_sha256="e" * 64,
        watchdog_deadline_utc="2026-08-13T23:59:00Z",
        lifecycle_genesis_checkpoint_sha256="f" * 64,
        live_probe_receipt_sha256="1" * 64,
        live_probe_file_sha256="2" * 64,
    )

    assert validate_execution_adoption_receipt_v3(ROOT, adoption) == adoption
    assert adoption["provider_instance_binding_sha256"] == binding["binding_sha256"]
    assert adoption["budget_profile_sha256"] == admission["budget_profile_sha256"]
    assert adoption["execution_readiness_contract_sha256"] == admission[
        "execution_readiness_contract_sha256"
    ]


def test_fresh_instance_binding_rejects_destroyed_instance(tmp_path: Path) -> None:
    observation_path, sources = _provider_observation_paths_v2(
        tmp_path, instance_id="47411176"
    )
    with pytest.raises(A2ExecutionReadinessError, match="instance ID is unsafe"):
        build_provider_instance_binding(
            ROOT,
            attempt_id=ATTEMPT,
            provider_observation_path=observation_path,
            source_artifact_paths=sources,
        )


def test_runner_gate_is_locked_without_adoption() -> None:
    require_execution_adoption(
        {"status": "PASS_A2_EXECUTION_ADOPTION", "launch_allowed": True, "measured_retrieval_allowed": False}
    )
    with pytest.raises(A2ExecutionReadinessError, match="remains locked"):
        require_execution_adoption({"status": "PENDING", "launch_allowed": False})


def test_bundle_requires_clean_pushed_repository(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def dirty_git(_root: Path, *args: str) -> str:
        if args[0] == "status":
            return " M PLAN.md"
        return "a" * 40

    monkeypatch.setattr(
        "myis_research.armindex.a2_execution_readiness._git", dirty_git
    )
    with pytest.raises(A2ExecutionReadinessError, match="clean worktree"):
        build_execution_bundle(
            ROOT, attempt_id=ATTEMPT, output_path=tmp_path / "bundle.tar.gz"
        )

    def unpushed_git(_root: Path, *args: str) -> str:
        if args[0] == "status":
            return ""
        if args == ("rev-parse", "origin/main"):
            return "b" * 40
        return "a" * 40

    monkeypatch.setattr(
        "myis_research.armindex.a2_execution_readiness._git", unpushed_git
    )
    with pytest.raises(A2ExecutionReadinessError, match="synchronized with origin/main"):
        build_execution_bundle(
            ROOT, attempt_id=ATTEMPT, output_path=tmp_path / "bundle.tar.gz"
        )


def test_bundle_closure_imports_in_isolated_extraction(tmp_path: Path) -> None:
    archive_path = tmp_path / "bundle.tar.gz"
    with tarfile.open(archive_path, "w:gz") as archive:
        for relative in _BUNDLE_CLOSURE:
            archive.add(ROOT / relative, arcname=relative)
    extracted = tmp_path / "extracted"
    with tarfile.open(archive_path, "r:gz") as archive:
        archive.extractall(extracted, filter="data")
    script = """
import json, pathlib, sys
root = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / 'src'))
from myis_research.armindex import a2_measured_adapter, a2_owner_local_engine
for module in (a2_measured_adapter, a2_owner_local_engine):
    assert pathlib.Path(module.__file__).resolve().is_relative_to(root)
schema = json.loads((root / 'schemas/armindex/representation-program.v1.json').read_text(encoding='utf-8'))
assert schema['$schema'].endswith('schema')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", script, str(extracted)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_bundle_closure_requires_both_readiness_envelopes_and_ledger_schemas() -> None:
    closure = set(_BUNDLE_CLOSURE)
    assert {
        "control/execution-envelope-a2-readiness-v1.yaml",
        "control/execution-envelope-a2-readiness-v2.yaml",
        "schemas/armindex/a2-execution-ledger-entry.v1.json",
        "schemas/armindex/a2-execution-ledger-entry.v2.json",
        "schemas/armindex/a2-execution-ledger-entry.v3.json",
        "schemas/armindex/a2-measured-execution-authority.v1.json",
        "schemas/armindex/a2-measured-execution-authority.v2.json",
        "schemas/armindex/a2-measured-execution-authority.v3.json",
        "schemas/armindex/a2-measurement-authority-commitment.v2.json",
        "schemas/armindex/a2-remote-measured-transport.v3.json",
    } <= closure


@pytest.mark.parametrize(
    "required_path",
    (
        "control/execution-envelope-a2-readiness-v1.yaml",
        "control/execution-envelope-a2-readiness-v2.yaml",
    ),
)
def test_bundle_validation_rejects_required_envelope_drift(
    tmp_path: Path, required_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    def clean_pushed_git(_root: Path, *args: str) -> str:
        if args[0] == "status":
            return ""
        return "a" * 40

    monkeypatch.setattr(
        "myis_research.armindex.a2_execution_readiness._git", clean_pushed_git
    )
    output = tmp_path / "bundle.tar.gz"
    built = build_execution_bundle(ROOT, attempt_id=ATTEMPT, output_path=output)
    receipt = built["receipt"]
    extracted = tmp_path / "extracted"
    with tarfile.open(output, "r:gz") as archive:
        archive.extractall(extracted, filter="data")
    target = extracted / required_path
    target.write_bytes(target.read_bytes() + b"\n# drift\n")
    drifted = tmp_path / "drifted.tar.gz"
    with tarfile.open(drifted, "w:gz") as archive:
        for relative in _BUNDLE_CLOSURE:
            archive.add(extracted / relative, arcname=relative)
        archive.add(
            extracted / "BUNDLE_MANIFEST.json",
            arcname="BUNDLE_MANIFEST.json",
        )
    with pytest.raises(A2ExecutionReadinessError, match="bundle hash drift"):
        validate_execution_bundle(ROOT, bundle_path=drifted, receipt=receipt)


def test_provider_admission_adoption_and_runner_staging_are_side_effect_free(
    tmp_path: Path,
) -> None:
    observation_path, source_paths = _provider_observation_paths(tmp_path)
    admission = build_provider_admission_receipt(
        ROOT,
        attempt_id=ATTEMPT,
        provider_observation_path=observation_path,
        source_artifact_paths=source_paths,
        now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
    )
    assert validate_provider_admission_receipt(ROOT, admission)["status"] == "PASS_A2_PROVIDER_ADMISSION"
    bundle = {
        "schema_version": "myis.armindex-a2-execution-bundle-receipt.v1",
        "receipt_id": f"{ATTEMPT}-bundle-v1",
        "attempt_id": ATTEMPT,
        "status": "PASS_CLEAN_HASH_BOUND_A2_BUNDLE",
        "clean_worktree": True,
        "pushed_to_origin_main": True,
        "git_commit": "c" * 40,
        "git_tree": "d" * 40,
        "freeze_bindings": {
            "manifest_sha256": "f6276e3a15e760187152270418e00ce4cae4d8efe45b13edb02c4742e3b3049e",
            "freeze_receipt_sha256": "ea93db368c3e740f7914e07e2bdfc15052991f6f05976f6924acdce717392e10",
            "lock_sha256": "c01f683b909e6f4c6310c01855b3f79319a183b7950f91338d43baa8a2d57952",
        },
        "bundle_sha256": "1" * 64,
        "bundle_manifest_sha256": "2" * 64,
    }
    bundle["receipt_sha256"] = canonical_sha256(bundle)
    adoption = build_execution_adoption_receipt(
        ROOT,
        attempt_id=ATTEMPT,
        provider_admission_receipt=admission,
        bundle_receipt=bundle,
        remote_root="/opt/myis/a2-readiness-test01",
        staged_bundle_sha256=bundle["bundle_sha256"],
        watchdog_sha256="e" * 64,
        watchdog_deadline_utc="2026-08-13T23:59:00Z",
        lifecycle_genesis_checkpoint_sha256="f" * 64,
        live_probe_receipt_sha256="1" * 64,
        live_probe_file_sha256="2" * 64,
    )

    plan = A2MeasuredRunner(ATTEMPT).stage(ROOT, adoption).request_external_execution()
    assert plan["process_started"] is False
    assert plan["provider_contacted"] is False
    assert plan["candidate_generation_performed"] is False


def test_remote_staging_watchdog_and_injected_executor_are_inert(tmp_path: Path) -> None:
    # The real bundle builder verifies repository cleanliness and origin parity;
    # use a synthetic adoption plan here to exercise only the no-SSH surface.
    adoption = {
        "schema_version": "myis.armindex-a2-execution-adoption-receipt.v1",
        "receipt_id": f"a2-{ATTEMPT.removeprefix('a2-')}-execution-adoption-v1",
        "attempt_id": ATTEMPT,
        "status": "PASS_A2_EXECUTION_ADOPTION",
        "provider_admission_receipt_sha256": "a" * 64,
        "bundle_receipt_sha256": "b" * 64,
        "bundle_sha256": "c" * 64,
        "git_commit": "d" * 40,
        "git_tree": "e" * 40,
        "remote_root": f"/opt/myis/{ATTEMPT}",
        "remote_root_created_fresh": True,
        "staged_bundle_sha256": "c" * 64,
        "staged_bundle_verified": True,
        "provider_observation_sha256": "1" * 64,
        "provider_observation_file_sha256": "2" * 64,
        "live_probe_receipt_sha256": "3" * 64,
        "live_probe_file_sha256": "4" * 64,
        "ttl_deadline_utc": "2026-08-14T00:00:00Z",
        "remaining_ttl_seconds_at_admission": 144000,
        "watchdog_installed": True,
        "watchdog_deadline_utc": "2026-08-13T23:59:00Z",
        "watchdog_sha256": "f" * 64,
        "lifecycle_genesis_checkpoint_sha256": "a" * 64,
        "freeze_bindings": {
            "manifest_sha256": "f6276e3a15e760187152270418e00ce4cae4d8efe45b13edb02c4742e3b3049e",
            "freeze_receipt_sha256": "ea93db368c3e740f7914e07e2bdfc15052991f6f05976f6924acdce717392e10",
            "lock_sha256": "c01f683b909e6f4c6310c01855b3f79319a183b7950f91338d43baa8a2d57952",
        },
        "launch_allowed": True,
        "measured_retrieval_allowed": False,
    }
    adoption["receipt_sha256"] = canonical_sha256(adoption)
    bundle_path = tmp_path / "bundle.tar.gz"
    bundle_path.write_bytes(b"synthetic-bundle")
    adoption["bundle_sha256"] = hashlib.sha256(bundle_path.read_bytes()).hexdigest()
    adoption["staged_bundle_sha256"] = adoption["bundle_sha256"]
    adoption["receipt_sha256"] = canonical_sha256(
        {key: value for key, value in adoption.items() if key != "receipt_sha256"}
    )
    watchdog = build_watchdog_script(
        attempt_id=ATTEMPT,
        remote_root=f"/opt/myis/{ATTEMPT}",
        deadline_utc="2026-08-13T23:59:00Z",
    )
    assert watchdog["ssh_called"] is False
    assert watchdog["provider_contacted"] is False
    staging = build_remote_staging_plan(
        ROOT, adoption_receipt=adoption, bundle_path=bundle_path
    )
    assert staging["remote_root"] == f"/opt/myis/{ATTEMPT}"
    assert staging["ssh_called"] is False
    assert staging["provider_contacted"] is False
    assert staging["measured_retrieval_allowed"] is False
    assert staging["staging_operations"] == [
        "create_isolated_remote_root",
        "transfer_bundle",
        "verify_bundle_sha256",
        "extract_without_overwriting_a1_root",
    ]
    result = A2MeasuredRunner(ATTEMPT).stage(ROOT, adoption)
    with pytest.raises(A2ExecutionReadinessError, match="no injected executor"):
        result.call_injected_executor(
            {"attempt_id": ATTEMPT, "measured_retrieval_allowed": False}
        )
    calls: list[dict[str, object]] = []

    def executor(plan: Mapping[str, object]) -> Mapping[str, object]:
        calls.append(dict(plan))
        return {"status": "INJECTED_EXECUTOR_CALLED", "attempt_id": plan["attempt_id"]}

    injected = A2MeasuredRunner(ATTEMPT, executor=executor).stage(ROOT, adoption)
    executed = injected.call_injected_executor(
        {"attempt_id": ATTEMPT, "measured_retrieval_allowed": False}
    )
    assert executed["status"] == "INJECTED_EXECUTOR_CALLED"
    assert calls == [
        {"attempt_id": ATTEMPT, "measured_retrieval_allowed": False}
    ]


def test_provider_admission_rejects_stale_or_over_budget_quote(tmp_path: Path) -> None:
    observation_path, source_paths = _provider_observation_paths(tmp_path)
    with pytest.raises(A2ExecutionReadinessError, match="not fresh"):
        build_provider_admission_receipt(
            ROOT,
            attempt_id=ATTEMPT,
            provider_observation_path=observation_path,
            source_artifact_paths=source_paths,
            now_utc=datetime(2026, 8, 12, 9, 0, tzinfo=timezone.utc),
        )
    over_path, over_sources = _provider_observation_paths(tmp_path / "over")
    over_budget = json.loads(over_path.read_text(encoding="ascii"))
    over_budget["whole_workload_total_usd"] = "36.00"
    over_budget["all_fee_components_usd"] = {
        "compute_usd": "33.00",
        "storage_usd": "1.00",
        "network_usd": "1.00",
        "platform_or_other_fee_usd": "0.50",
        "tax_or_surcharge_usd": "0.50",
    }
    unsigned = {key: value for key, value in over_budget.items() if key != "observation_sha256"}
    over_budget["observation_sha256"] = canonical_sha256(unsigned)
    over_path.write_text(json.dumps(over_budget), encoding="ascii")
    with pytest.raises(A2ExecutionReadinessError, match="exceeds"):
        build_provider_admission_receipt(
            ROOT,
            attempt_id=ATTEMPT,
            provider_observation_path=over_path,
            source_artifact_paths=over_sources,
            now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
        )


def test_provider_admission_rejects_source_mutation_and_short_absolute_ttl(tmp_path: Path) -> None:
    observation_path, source_paths = _provider_observation_paths(tmp_path)
    source_paths["runtime"].write_text("mutated\n", encoding="ascii")
    with pytest.raises(A2ExecutionReadinessError, match="bytes drift"):
        build_provider_admission_receipt(
            ROOT,
            attempt_id=ATTEMPT,
            provider_observation_path=observation_path,
            source_artifact_paths=source_paths,
            now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
        )
    ttl_path, ttl_sources = _provider_observation_paths(
        tmp_path / "ttl", deadline="2026-08-12T11:23:00Z"
    )
    with pytest.raises(A2ExecutionReadinessError, match="NEEDS_OWNER_TTL_EXTENSION"):
        build_provider_admission_receipt(
            ROOT,
            attempt_id=ATTEMPT,
            provider_observation_path=ttl_path,
            source_artifact_paths=ttl_sources,
            now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
        )


def test_provider_admission_validation_rejects_post_receipt_source_mutation(tmp_path: Path) -> None:
    observation_path, source_paths = _provider_observation_paths(tmp_path)
    receipt = build_provider_admission_receipt(
        ROOT,
        attempt_id=ATTEMPT,
        provider_observation_path=observation_path,
        source_artifact_paths=source_paths,
        now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
    )
    source_paths["data_handoff"].write_text("changed\n", encoding="ascii")
    with pytest.raises(A2ExecutionReadinessError, match="source artifact (bytes drift|mutation)"):
        validate_provider_admission_receipt(
            ROOT,
            receipt,
            provider_observation_path=observation_path,
            source_artifact_paths=source_paths,
        )


def test_aggregate_evaluator_requires_exact_frozen_membership_and_rejects_ties() -> None:
    results = _aggregate_results()
    evaluated = evaluate_aggregate_train_results(
        ROOT, results_by_candidate=results, allow_synthetic_fixture=True
    )
    assert evaluated["candidate_count"] == 52
    assert evaluated["winners"]["ARM-01"]["diagnostic_non_advancing"] is True
    assert evaluated["winners"]["ARM-02"]["advancement_eligible"] is False

    results.pop(next(iter(results)))
    with pytest.raises(A2ExecutionReadinessError, match="membership exactly"):
        evaluate_aggregate_train_results(
            ROOT, results_by_candidate=results, allow_synthetic_fixture=True
        )
    tied = _aggregate_results()
    arm_one = [key for key, row in tied.items() if row["arm_id"] == "ARM-01"]
    tied[arm_one[0]]["primary_metric"] = "100"
    tied[arm_one[1]]["primary_metric"] = "100"
    with pytest.raises(A2ExecutionReadinessError, match="winner tie"):
        evaluate_aggregate_train_results(
            ROOT, results_by_candidate=tied, allow_synthetic_fixture=True
        )
    evaluate_aggregate_train_results,
