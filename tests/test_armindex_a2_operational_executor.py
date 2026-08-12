from __future__ import annotations

import copy
import io
import json
import subprocess
import tarfile
import hashlib
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

import pytest

from myis_research.armindex import a2_operational_executor as operational
from myis_research.armindex.a2_execution_readiness import (
    A2ExecutionReadinessError,
    build_provider_admission_receipt,
    build_safe_return_receipt,
    frozen_candidates,
)
from myis_research.kernel.canonical import file_sha256
from myis_research.kernel.canonical import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]
ATTEMPT = "a2-operational-test01"


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
        "ttl_deadline_utc": "2026-08-14T08:00:00Z",
        "quote_observed_at_utc": "2026-08-12T08:00:00Z",
        "all_fee_components_usd": {
            "compute_usd": "30",
            "storage_usd": "1",
            "network_usd": "1",
            "platform_or_other_fee_usd": "0.5",
            "tax_or_surcharge_usd": "0.5",
        },
        "whole_workload_total_usd": "33",
    }


def _provider_observation_paths(tmp_path: Path) -> tuple[Path, dict[str, Path]]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    sources: dict[str, Path] = {}
    for name in ("runtime", "model_lockset", "data_handoff", "ssh_host_key", "management_authority"):
        path = tmp_path / f"{name}.txt"
        path.write_text(f"aggregate-safe {name}\n", encoding="ascii")
        sources[name] = path
    hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in sources.items()}
    observation = _provider_evidence()
    observation.update({
        "schema_version": "myis.armindex-a2-provider-observation.v1",
        "observation_id": f"{ATTEMPT}-provider-observation-v1",
        "attempt_id": ATTEMPT,
        "source_mode": observation.pop("evidence_mode"),
        "remaining_ttl_seconds": 172800,
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
    })
    observation["observation_sha256"] = canonical_sha256(observation)
    path = tmp_path / "provider-observation.json"
    path.write_text(json.dumps(observation), encoding="ascii")
    return path, sources


def _candidate_row(candidate_id: str, *, score: str = "1", measured: bool = False) -> dict[str, object]:
    candidate = frozen_candidates(ROOT)[candidate_id]
    dormant = candidate["tier"] == "conditional_reserve"
    return {
        "schema_version": "myis.armindex-a2-external-candidate-result.v1",
        "attempt_id": ATTEMPT,
        "candidate_id": candidate_id,
        "arm_id": candidate["arm_id"],
        "program_sha256": candidate["program_sha256"],
        "executor_output_sha256": "1" * 64,
        "evaluator_input_sha256": "2" * 64,
        "evaluator_sha256": "3" * 64,
        "code_sha256": "4" * 64,
        "model_sha256": "5" * 64,
        "data_sha256": "6" * 64,
        "primary_metric": None
        if dormant
        else {"name": "recall_at_100/out", "value": score},
        "secondary_metrics": None
        if dormant
        else {"ndcg_at_100/out": score, "ndcg_at_10/out": score},
        "latency": None
        if dormant
        else {"wall_seconds": "1", "search_p95_seconds": "0.1"},
        "cost": None if dormant else {"charged_usd": "0", "currency": "USD"},
        "coverage": {"expected_units": 1, "completed_units": 0 if dormant else 1},
        "resume_count": 0,
        "failure_count": 0,
        "reserve_activation_passed": False,
        "reserve_activation_evidence_sha256": None,
        "train_only": not measured,
        "rep_dev_measured": measured,
        "protected_payload_included": False,
        "per_query_outcomes_included": False,
    }


def _candidate_receipts() -> dict[str, dict[str, object]]:
    receipts: dict[str, dict[str, object]] = {}
    for index, candidate_id in enumerate(frozen_candidates(ROOT), start=1):
        row = _candidate_row(candidate_id, score=str(index))
        candidate = frozen_candidates(ROOT)[candidate_id]
        if candidate["tier"] == "conditional_reserve":
            row["reserve_activation_passed"] = True
            row["reserve_activation_evidence_sha256"] = "7" * 64
            row["primary_metric"] = {"name": "recall_at_100/out", "value": str(index)}
            row["secondary_metrics"] = {
                "ndcg_at_100/out": str(index),
                "ndcg_at_10/out": str(index),
            }
            row["latency"] = {"wall_seconds": "1", "search_p95_seconds": "0.1"}
            row["cost"] = {"charged_usd": "0", "currency": "USD"}
            row["coverage"] = {"expected_units": 1, "completed_units": 1}
        receipts[candidate_id] = operational.build_candidate_result_receipt(
            ROOT,
            result=row,
            evidence_class="engineering_synthetic",
        )
    return receipts


def _adoption() -> dict[str, object]:
    body: dict[str, object] = {
        "schema_version": "myis.armindex-a2-execution-adoption-receipt.v1",
        "receipt_id": f"{ATTEMPT}-execution-adoption-v1",
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
        "ttl_deadline_utc": "2026-08-14T08:00:00Z",
        "remaining_ttl_seconds_at_admission": 172800,
        "watchdog_installed": True,
        "watchdog_deadline_utc": "2026-08-13T08:00:00Z",
        "watchdog_sha256": "f" * 64,
        "lifecycle_genesis_checkpoint_sha256": "1" * 64,
        "freeze_bindings": operational._freeze_bindings(ROOT),
        "launch_allowed": True,
        "measured_retrieval_allowed": False,
    }
    return {**body, "receipt_sha256": canonical_sha256(body)}


def _authority(adoption: Mapping[str, object]) -> dict[str, object]:
    body: dict[str, object] = {
        "schema_version": "myis.armindex-a2-measured-execution-authority.v1",
        "authority_id": "a2-measured-execution-authority-v1",
        "authority_uri": f"control/armindex/a2/measured-authority/{ATTEMPT}.authority.v1.json",
        "status": "PASS_A2_MEASURED_EXECUTION_AUTHORIZED",
        "attempt_id": ATTEMPT,
        "source_goal_uri": "docs/goal/A2_goal.md",
        "source_goal_sha256": file_sha256(ROOT / "docs/goal/A2_goal.md"),
        "execution_adoption_receipt_sha256": adoption["receipt_sha256"],
        "measured_a2_authorized": True,
        "candidate_generation_allowed": False,
        "candidate_mutation_allowed": False,
        "rep_dev_measurement_allowed": False,
        "a3_allowed": False,
        "selection_allowed": False,
        "final_allowed": False,
        "active_reserve_candidate_ids": [],
        "reserve_activation_evidence_sha256": None,
        "freeze_bindings": operational._freeze_bindings(ROOT),
        "scientific_authority": True,
    }
    return {**body, "authority_sha256": canonical_sha256(body)}


def _reserve_budget_admission(
    adoption: Mapping[str, object], authority: Mapping[str, object]
) -> dict[str, object]:
    fresh_provider_receipt_sha256 = "9" * 64
    body = {
        "schema_version": "myis.armindex-a2-reserve-budget-admission.v1",
        "receipt_id": f"{ATTEMPT}-reserve-budget-admission-v1",
        "attempt_id": ATTEMPT,
        "execution_adoption_receipt_sha256": adoption["receipt_sha256"],
        "initial_measurement_authority_sha256": authority["authority_sha256"],
        "provider_admission_receipt_sha256": fresh_provider_receipt_sha256,
        "provider_observation_sha256": "8" * 64,
        "provider_observation_file_sha256": "7" * 64,
        "source_artifact_sha256": {
            "runtime": "1" * 64,
            "model_lockset": "2" * 64,
            "data_handoff": "3" * 64,
            "ssh_host_key": "4" * 64,
            "management_authority": "5" * 64,
        },
        "observed_at_utc": "2026-08-12T08:05:00Z",
        "ttl_deadline_utc": "2026-08-14T08:00:00Z",
        "whole_workload_total_usd": "33",
        "forward_hard_stop_usd": "35",
        "freeze_bindings": operational._freeze_bindings(ROOT),
    }
    return {**body, "receipt_sha256": canonical_sha256(body)}


def _arm_incumbents() -> dict[str, dict[str, str]]:
    return operational.canonical_a1_incumbents(ROOT)


def _executed_candidate_row(candidate_id: str, *, score: str) -> dict[str, object]:
    row = _candidate_row(candidate_id, score=score, measured=True)
    row["evaluator_sha256"] = _authority(_adoption())["authority_sha256"]
    row["code_sha256"] = _adoption()["bundle_sha256"]
    if frozen_candidates(ROOT)[candidate_id]["tier"] == "conditional_reserve":
        row.update(
            {
                "primary_metric": {"name": "recall_at_100/out", "value": score},
                "secondary_metrics": {"ndcg_at_100/out": score, "ndcg_at_10/out": score},
                "latency": {"wall_seconds": "1", "search_p95_seconds": "0.1"},
                "cost": {"charged_usd": "0", "currency": "USD"},
                "coverage": {"expected_units": 1, "completed_units": 1},
            }
        )
    return row


def test_synthetic_operational_dry_run_covers_frozen_universe_without_measurement() -> None:
    result = operational.run_synthetic_dry_run(ROOT, attempt_id=ATTEMPT)

    assert result["status"] == "PASS_A2_SYNTHETIC_OPERATIONAL_DRY_RUN"
    assert result["candidate_count"] == 52
    assert result["matched_candidate_count"] == 40
    assert result["conditional_reserve_candidate_count"] == 12
    assert result["winner_count"] == 5
    assert result["measured_a2_started"] is False
    assert result["provider_contacted"] is False
    watchdog = operational.build_watchdog_script(
        attempt_id=ATTEMPT,
        remote_root=f"/opt/myis/{ATTEMPT}",
        deadline_utc="2099-01-01T00:00:00Z",
    )
    assert "/proc/$pid/stat" in watchdog["script"]
    assert "heartbeats/watchdog" in watchdog["script"]
    assert "sleep 2" in watchdog["script"]
    assert "kill -TERM" in watchdog["script"]
    assert "kill -KILL" in watchdog["script"]


def test_candidate_result_rejects_hash_drift_protected_member_and_false_measurement() -> None:
    candidate_id = next(iter(frozen_candidates(ROOT)))
    drifted = _candidate_row(candidate_id)
    drifted["program_sha256"] = "0" * 64
    with pytest.raises(operational.A2OperationalExecutorError, match="program hash drift"):
        operational.build_candidate_result_receipt(
            ROOT, result=drifted, evidence_class="engineering_synthetic"
        )

    protected = _candidate_row(candidate_id)
    protected["query_ids"] = ["protected"]
    with pytest.raises(operational.A2OperationalExecutorError, match="not allowlisted"):
        operational.build_candidate_result_receipt(
            ROOT, result=protected, evidence_class="engineering_synthetic"
        )

    with pytest.raises(operational.A2OperationalExecutorError, match="lacks adopted authority"):
        operational.build_candidate_result_receipt(
            ROOT,
            result=_candidate_row(candidate_id, measured=True),
            evidence_class="measured_development_aggregate",
        )


def test_measurement_authority_rejects_self_hashed_untracked_control() -> None:
    adoption = _adoption()
    with pytest.raises(
        operational.A2OperationalExecutorError,
        match="not canonical and tracked",
    ):
        operational.validate_measurement_authority(
            ROOT,
            _authority(adoption),
            attempt_id=ATTEMPT,
            execution_adoption_receipt_sha256=str(adoption["receipt_sha256"]),
        )


def test_measurement_authority_rejects_non_authorizing_goal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adoption = _adoption()
    monkeypatch.setattr(
        operational,
        "_validate_measurement_authority_provenance",
        lambda *_args, **_kwargs: None,
    )
    with pytest.raises(
        operational.A2OperationalExecutorError,
        match="goal does not authorize execution",
    ):
        operational.validate_measurement_authority(
            ROOT,
            _authority(adoption),
            attempt_id=ATTEMPT,
            execution_adoption_receipt_sha256=str(adoption["receipt_sha256"]),
        )


def test_exact_coverage_rejects_missing_candidate_and_exact_tie() -> None:
    receipts = _candidate_receipts()
    complete = operational.evaluate_candidate_receipts(ROOT, receipts_by_candidate=receipts)
    assert complete["candidate_count"] == 52
    assert complete["winners"]["ARM-01"]["diagnostic_non_advancing"] is True
    assert complete["winners"]["ARM-01"]["advancement_eligible"] is False
    assert complete["winners"]["ARM-02"]["advancement_eligible"] is False
    assert set(complete["winner_receipts"]) == {
        "ARM-01",
        "ARM-02",
        "ARM-03",
        "ARM-04",
        "ARM-05",
    }

    incomplete = dict(receipts)
    incomplete.pop(next(iter(incomplete)))
    with pytest.raises(operational.A2OperationalExecutorError, match="all 52"):
        operational.evaluate_candidate_receipts(ROOT, receipts_by_candidate=incomplete)

    tied = copy.deepcopy(receipts)
    arm_three = [
        candidate_id
        for candidate_id, candidate in frozen_candidates(ROOT).items()
        if candidate["arm_id"] == "ARM-03" and candidate["tier"] == "matched"
    ]
    for candidate_id in arm_three[:2]:
        unsigned = {
            key: value
            for key, value in tied[candidate_id].items()
            if key != "receipt_sha256"
        }
        unsigned["primary_metric"]["value"] = "999"
        tied[candidate_id] = {**unsigned, "receipt_sha256": canonical_sha256(unsigned)}
    with pytest.raises(operational.A2OperationalExecutorError, match="exact winner tie"):
        operational.evaluate_candidate_receipts(ROOT, receipts_by_candidate=tied)


def test_provider_admission_rejects_stale_and_partial_quote(tmp_path: Path) -> None:
    observation_path, sources = _provider_observation_paths(tmp_path)
    with pytest.raises(A2ExecutionReadinessError, match="not fresh"):
        build_provider_admission_receipt(
            ROOT,
            attempt_id=ATTEMPT,
            provider_observation_path=observation_path,
            source_artifact_paths=sources,
            now_utc=datetime(2026, 8, 12, 9, 0, tzinfo=timezone.utc),
        )
    partial_path, partial_sources = _provider_observation_paths(tmp_path / "partial")
    partial = json.loads(partial_path.read_text(encoding="ascii"))
    partial["all_fee_components_usd"].pop("tax_or_surcharge_usd")  # type: ignore[union-attr]
    partial["observation_sha256"] = canonical_sha256(
        {key: value for key, value in partial.items() if key != "observation_sha256"}
    )
    partial_path.write_text(json.dumps(partial), encoding="ascii")
    with pytest.raises(A2ExecutionReadinessError, match="required property"):
        build_provider_admission_receipt(
            ROOT,
            attempt_id=ATTEMPT,
            provider_observation_path=partial_path,
            source_artifact_paths=partial_sources,
            now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
        )


def test_stage_plan_rejects_wrong_root_and_transport_rejects_dead_watchdog(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    bundle = tmp_path / "bundle.tar.gz"
    bundle.write_bytes(b"bundle")
    bundle_receipt = {
        "attempt_id": ATTEMPT,
        "bundle_sha256": "a" * 64,
        "git_commit": "b" * 40,
        "git_tree": "c" * 40,
        "receipt_sha256": "d" * 64,
    }
    monkeypatch.setattr(
        operational,
        "validate_execution_bundle",
        lambda *_args, **_kwargs: dict(bundle_receipt),
    )
    watchdog = {
        "attempt_id": ATTEMPT,
        "watchdog_sha256": "e" * 64,
        "script": "#!/usr/bin/env sh\nexit 0\n",
    }
    with pytest.raises(operational.A2OperationalExecutorError, match="root is invalid"):
        operational.build_remote_stage_plan(
            ROOT,
            attempt_id=ATTEMPT,
            remote_root="/opt/myis/a1-existing",
            bundle_receipt=bundle_receipt,
            bundle_path=bundle,
            watchdog=watchdog,
        )

    connection = tmp_path / "vast-ssh.md"
    key = tmp_path / "key"
    known = tmp_path / "known_hosts"
    key.write_text("owner-local", encoding="ascii")
    known.write_text("aggregate-safe ssh host key\n", encoding="ascii")
    connection.write_text(
        "\n".join(
            (
                "VAST_HOST: 127.0.0.1",
                "VAST_PORT: 22",
                "VAST_USER: root",
                f"SSH_KEY_PATH: {key}",
                f"LOCAL_KNOWN_HOSTS_FILE: {known}",
            )
        ),
        encoding="utf-8",
    )
    observation_path, sources = _provider_observation_paths(tmp_path / "provider")
    sources["ssh_host_key"].write_bytes(known.read_bytes())
    observation = json.loads(observation_path.read_text(encoding="ascii"))
    known_hash = hashlib.sha256(known.read_bytes()).hexdigest()
    observation["ssh_host_key_sha256"] = known_hash
    observation["source_artifact_sha256"]["ssh_host_key"] = known_hash
    observation["source_artifacts"]["ssh_host_key"]["file_sha256"] = known_hash
    observation["observation_sha256"] = canonical_sha256(
        {key: value for key, value in observation.items() if key != "observation_sha256"}
    )
    observation_path.write_text(json.dumps(observation), encoding="ascii")
    provider = build_provider_admission_receipt(
        ROOT,
        attempt_id=ATTEMPT,
        provider_observation_path=observation_path,
        source_artifact_paths=sources,
        now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
    )
    probe_body = {
        "schema_version": "myis.armindex-a2-live-remote-probe-receipt.v1",
        "receipt_id": f"{ATTEMPT}-live-remote-probe-v1",
        "attempt_id": ATTEMPT,
        "status": "PASS_A2_LIVE_REMOTE_PROBE",
        "observed_at_utc": "2026-08-12T08:05:00Z",
        "provider_instance_id": "47411176",
        "ssh_host_key_sha256": known_hash,
        "runtime_sha256": provider["runtime_sha256"],
        "gpu_uuid_set_sha256": provider["gpu_uuid_set_sha256"],
        "gpu_count": 4,
        "gpu_model": "RTX3090",
        "vram_mib_each": 24576,
        "gpu_compute_process_count": 0,
        "a2_process_count": 0,
        "model_lockset_sha256": provider["model_lockset_sha256"],
        "data_handoff_sha256": provider["data_handoff_sha256"],
        "bundle_sha256": bundle_receipt["bundle_sha256"],
        "remote_root": f"/opt/myis/{ATTEMPT}",
        "remote_root_absent": True,
        "ttl_deadline_utc": provider["ttl_deadline_utc"],
        "remaining_ttl_seconds": 172500,
    }
    probe = {**probe_body, "receipt_sha256": canonical_sha256(probe_body)}
    outputs = iter(("", "", "", "dead-watchdog"))

    commands: list[list[str]] = []

    def runner(*args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(list(args[0]))  # type: ignore[arg-type]
        return subprocess.CompletedProcess([], 0, next(outputs), "")

    monkeypatch.setattr(operational, "_run_live_remote_probe", lambda **_kwargs: probe)

    with pytest.raises(operational.A2OperationalExecutorError, match="watchdog process identity"):
        operational.perform_remote_stage(
            ROOT,
            attempt_id=ATTEMPT,
            provider_admission_receipt=provider,
            bundle_receipt=bundle_receipt,
            bundle_path=bundle,
            remote_root=f"/opt/myis/{ATTEMPT}",
            watchdog_deadline_utc="2026-08-13T08:00:00Z",
            owner_connection_path=connection,
            provider_observation_path=observation_path,
            source_artifact_paths=sources,
            remote_identity_paths={
                "provider_instance_id": "/opt/myis/identity/instance-id",
                "runtime": "/opt/myis/identity/runtime.json",
                "model_lockset": "/opt/myis/identity/model-lockset.json",
                "data_handoff": "/opt/myis/identity/data-handoff.json",
            },
            now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
            runner=runner,
        )
    verify_command = commands[-1][-1]
    assert "/lifecycle/watchdog.identity" in verify_command
    assert "/lifecycle/processes/watchdog.identity" not in verify_command
    assert "while test ! -s" in verify_command
    assert "test \"$actual\" = \"$start\"" in verify_command


def test_remote_stage_plan_revalidates_the_immutable_bundle_receipt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    bundle = tmp_path / "bundle.tar.gz"
    bundle.write_bytes(b"bundle")
    bundle_receipt = {
        "attempt_id": ATTEMPT,
        "bundle_sha256": "a" * 64,
        "git_commit": "b" * 40,
        "git_tree": "c" * 40,
        "receipt_sha256": "d" * 64,
    }
    validated = {**bundle_receipt, "validation_status": "PASS"}
    receipts_seen: list[Mapping[str, object]] = []

    def validate_bundle(
        _root: Path, *, bundle_path: Path, receipt: Mapping[str, object]
    ) -> dict[str, object]:
        assert bundle_path == bundle
        receipts_seen.append(receipt)
        if "validation_status" in receipt:
            raise AssertionError("derived validation fields must not be revalidated")
        return dict(validated)

    monkeypatch.setattr(operational, "validate_execution_bundle", validate_bundle)
    monkeypatch.setattr(
        operational,
        "validate_provider_admission_receipt",
        lambda *_args, **_kwargs: {
            "attempt_id": ATTEMPT,
            "ttl_deadline_utc": "2026-08-14T08:00:00Z",
        },
    )
    monkeypatch.setattr(
        operational,
        "build_lifecycle_checkpoint",
        lambda *_args, **_kwargs: {"checkpoint_sha256": "e" * 64},
    )
    plan_receipts: list[Mapping[str, object]] = []

    def stop_after_plan(
        _root: Path, *, bundle_receipt: Mapping[str, object], **_kwargs: object
    ) -> dict[str, object]:
        plan_receipts.append(bundle_receipt)
        raise RuntimeError("stop after plan")

    monkeypatch.setattr(
        operational,
        "build_remote_stage_plan",
        stop_after_plan,
    )

    with pytest.raises(RuntimeError, match="stop after plan"):
        operational.perform_remote_stage(
            ROOT,
            attempt_id=ATTEMPT,
            provider_admission_receipt={},
            bundle_receipt=bundle_receipt,
            bundle_path=bundle,
            remote_root=f"/opt/myis/{ATTEMPT}",
            watchdog_deadline_utc="2026-08-13T08:00:00Z",
            owner_connection_path=tmp_path / "unused-connection",
            provider_observation_path=tmp_path / "unused-observation",
            source_artifact_paths={},
            remote_identity_paths={
                "provider_instance_id": "/opt/myis/identity/instance-id",
                "runtime": "/opt/myis/identity/runtime.json",
                "model_lockset": "/opt/myis/identity/model-lockset.json",
                "data_handoff": "/opt/myis/identity/data-handoff.json",
            },
            now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
        )
    assert receipts_seen == [bundle_receipt]
    assert plan_receipts == [bundle_receipt]


def test_live_remote_probe_accepts_bounded_remote_clock_lead(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    known = tmp_path / "known_hosts"
    known.write_text("aggregate-safe ssh host key\n", encoding="ascii")
    provider = {
        "provider_instance_id": "47411176",
        "ssh_host_key_sha256": file_sha256(known),
        "runtime_sha256": "a" * 64,
        "gpu_uuid_set_sha256": "b" * 64,
        "model_lockset_sha256": "c" * 64,
        "data_handoff_sha256": "d" * 64,
        "ttl_deadline_utc": "2026-08-14T08:05:00Z",
    }
    body = {
        "schema_version": "myis.armindex-a2-live-remote-probe-receipt.v1",
        "receipt_id": f"{ATTEMPT}-live-remote-probe-v1",
        "attempt_id": ATTEMPT,
        "status": "PASS_A2_LIVE_REMOTE_PROBE",
        "observed_at_utc": "2026-08-12T08:05:30Z",
        "provider_instance_id": provider["provider_instance_id"],
        "ssh_host_key_sha256": provider["ssh_host_key_sha256"],
        "runtime_sha256": provider["runtime_sha256"],
        "gpu_uuid_set_sha256": provider["gpu_uuid_set_sha256"],
        "gpu_count": 4,
        "gpu_model": "RTX3090",
        "vram_mib_each": 24576,
        "gpu_compute_process_count": 0,
        "a2_process_count": 0,
        "model_lockset_sha256": provider["model_lockset_sha256"],
        "data_handoff_sha256": provider["data_handoff_sha256"],
        "bundle_sha256": "e" * 64,
        "remote_root": f"/opt/myis/{ATTEMPT}",
        "remote_root_absent": True,
        "ttl_deadline_utc": provider["ttl_deadline_utc"],
        "remaining_ttl_seconds": 172800,
    }
    probe = {**body, "receipt_sha256": canonical_sha256(body)}

    monkeypatch.setattr(
        operational,
        "validate_provider_admission_receipt",
        lambda *_args, **_kwargs: dict(provider),
    )

    checked = operational.validate_live_remote_probe(
        ROOT,
        attempt_id=ATTEMPT,
        probe=probe,
        provider_admission_receipt=provider,
        bundle_sha256="e" * 64,
        remote_root=f"/opt/myis/{ATTEMPT}",
        known_hosts_path=known,
        now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
    )
    assert checked["observed_at_utc"] == "2026-08-12T08:05:30Z"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("runtime_sha256", "0" * 64, "runtime drift"),
        ("gpu_uuid_set_sha256", "0" * 64, "GPU UUID set drift"),
        ("model_lockset_sha256", "0" * 64, "model lockset drift"),
        ("data_handoff_sha256", "0" * 64, "data handoff drift"),
        ("gpu_compute_process_count", 1, "validation failed"),
        ("a2_process_count", 1, "validation failed"),
        ("remote_root_absent", False, "validation failed"),
        ("ssh_host_key_sha256", "0" * 64, "SSH host-key drift"),
    ],
)
def test_live_remote_probe_failures_close_before_stage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    field: str,
    value: object,
    message: str,
) -> None:
    known = tmp_path / "known_hosts"
    known.write_text("aggregate-safe ssh host key\n", encoding="ascii")
    host_hash = file_sha256(known)
    provider = {
        "provider_instance_id": "47411176",
        "ssh_host_key_sha256": host_hash,
        "runtime_sha256": "a" * 64,
        "gpu_uuid_set_sha256": "b" * 64,
        "model_lockset_sha256": "c" * 64,
        "data_handoff_sha256": "d" * 64,
        "ttl_deadline_utc": "2026-08-14T08:00:00Z",
    }
    monkeypatch.setattr(
        operational,
        "validate_provider_admission_receipt",
        lambda *_args, **_kwargs: dict(provider),
    )
    body = {
        "schema_version": "myis.armindex-a2-live-remote-probe-receipt.v1",
        "receipt_id": f"{ATTEMPT}-live-remote-probe-v1",
        "attempt_id": ATTEMPT,
        "status": "PASS_A2_LIVE_REMOTE_PROBE",
        "observed_at_utc": "2026-08-12T08:05:00Z",
        "provider_instance_id": "47411176",
        "ssh_host_key_sha256": host_hash,
        "runtime_sha256": provider["runtime_sha256"],
        "gpu_uuid_set_sha256": provider["gpu_uuid_set_sha256"],
        "gpu_count": 4,
        "gpu_model": "RTX3090",
        "vram_mib_each": 24576,
        "gpu_compute_process_count": 0,
        "a2_process_count": 0,
        "model_lockset_sha256": provider["model_lockset_sha256"],
        "data_handoff_sha256": provider["data_handoff_sha256"],
        "bundle_sha256": "e" * 64,
        "remote_root": f"/opt/myis/{ATTEMPT}",
        "remote_root_absent": True,
        "ttl_deadline_utc": provider["ttl_deadline_utc"],
        "remaining_ttl_seconds": 172500,
    }
    body[field] = value
    probe = {**body, "receipt_sha256": canonical_sha256(body)}
    with pytest.raises(operational.A2OperationalExecutorError, match=message):
        operational.validate_live_remote_probe(
            ROOT,
            attempt_id=ATTEMPT,
            probe=probe,
            provider_admission_receipt=provider,
            bundle_sha256="e" * 64,
            remote_root=f"/opt/myis/{ATTEMPT}",
            known_hosts_path=known,
            now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
        )


def test_live_remote_probe_command_hashes_remote_identity_artifacts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[str] = []
    body = {
        "schema_version": "myis.armindex-a2-live-remote-probe-receipt.v1",
        "receipt_id": f"{ATTEMPT}-live-remote-probe-v1",
        "attempt_id": ATTEMPT,
        "status": "PASS_A2_LIVE_REMOTE_PROBE",
        "observed_at_utc": "2026-08-12T08:05:00Z",
        "provider_instance_id": "47411176",
        "ssh_host_key_sha256": "f" * 64,
        "runtime_sha256": "a" * 64,
        "gpu_uuid_set_sha256": "b" * 64,
        "gpu_count": 4,
        "gpu_model": "RTX3090",
        "vram_mib_each": 24576,
        "gpu_compute_process_count": 0,
        "a2_process_count": 0,
        "model_lockset_sha256": "c" * 64,
        "data_handoff_sha256": "d" * 64,
        "bundle_sha256": "e" * 64,
        "remote_root": f"/opt/myis/{ATTEMPT}",
        "remote_root_absent": True,
        "ttl_deadline_utc": "2026-08-14T08:00:00Z",
        "remaining_ttl_seconds": 172500,
    }
    result = {**body, "receipt_sha256": canonical_sha256(body)}

    def native(_executable: str, arguments: list[str], **_kwargs: object) -> str:
        captured.append(arguments[-1])
        return json.dumps(result)

    monkeypatch.setattr(operational, "_native", native)
    operational._run_live_remote_probe(
        ssh=["root@example"],
        remote_root=f"/opt/myis/{ATTEMPT}",
        provider={
            "attempt_id": ATTEMPT,
            "provider_instance_id": "47411176",
            "ttl_deadline_utc": "2026-08-14T08:00:00Z",
            "ssh_host_key_sha256": "f" * 64,
            "runtime_sha256": "a" * 64,
            "gpu_uuid_set_sha256": "b" * 64,
            "model_lockset_sha256": "c" * 64,
            "data_handoff_sha256": "d" * 64,
        },
        bundle_sha256="e" * 64,
        remote_identity_paths={
            "provider_instance_id": "/opt/myis/identity/instance-id",
            "runtime": "/opt/myis/identity/runtime.json",
            "model_lockset": "/opt/myis/identity/model-lockset.json",
            "data_handoff": "/opt/myis/identity/data-handoff.json",
        },
        runner=subprocess.run,
    )
    assert "digest(paths['runtime'])" in captured[0]
    assert "digest(paths['model_lockset'])" in captured[0]
    assert "digest(paths['data_handoff'])" in captured[0]
    assert "nvidia-smi" in captured[0]


def test_safe_return_rejects_member_checksum_drift(tmp_path: Path) -> None:
    archive = tmp_path / "safe-return.tar.gz"
    payload = b"aggregate\n"
    unsigned = {
        "attempt_id": ATTEMPT,
        "protected_payload_included": False,
        "members": [{"path": "aggregate.json", "sha256": "0" * 64, "size_bytes": len(payload)}],
    }
    manifest = {**unsigned, "archive_manifest_sha256": canonical_sha256(unsigned)}
    with tarfile.open(archive, "w:gz") as bundle:
        member = tarfile.TarInfo("aggregate.json")
        member.size = len(payload)
        bundle.addfile(member, io.BytesIO(payload))
        encoded = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
        member = tarfile.TarInfo("A2_SAFE_RETURN_MANIFEST.json")
        member.size = len(encoded)
        bundle.addfile(member, io.BytesIO(encoded))
    with pytest.raises(A2ExecutionReadinessError, match="member hash drift"):
        build_safe_return_receipt(
            ROOT,
            attempt_id=ATTEMPT,
            archive_path=archive,
            remote_root=f"/opt/myis/{ATTEMPT}",
        )


def test_external_executor_interruption_resumes_from_durable_candidate_receipts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    adoption = _adoption()
    authority = _authority(adoption)
    monkeypatch.setattr(
        operational,
        "_validate_measurement_authority_provenance",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(operational, "_validate_measurement_goal", lambda *_args, **_kwargs: None)
    budget = _reserve_budget_admission(adoption, authority)
    output = tmp_path / "owner-local-output"
    ledger = tmp_path / "lifecycle.jsonl"
    calls: list[str] = []

    def interrupted(
        command: list[str], **_kwargs: object
    ) -> Mapping[str, object]:
        candidate_id = command[1]
        calls.append(candidate_id)
        if len(calls) == 2:
            raise RuntimeError("injected interruption")
        return _executed_candidate_row(candidate_id, score="100")

    with pytest.raises(RuntimeError, match="injected interruption"):
        operational.execute_external_candidate_set(
            ROOT,
            attempt_id=ATTEMPT,
            adoption_receipt=adoption,
            measurement_authority=authority,
            command_template=["executor", "{candidate_id}"],
            output_directory=output,
            checkpoint_ledger=ledger,
            executor=interrupted,
        )
    first_candidate = calls[0]
    assert (output / "receipts" / f"{first_candidate}.json").is_file()

    resumed_calls: list[str] = []
    scores = {
        candidate_id: str(index)
        for index, candidate_id in enumerate(frozen_candidates(ROOT), start=1)
    }

    def resumed(command: list[str], **_kwargs: object) -> Mapping[str, object]:
        candidate_id = command[1]
        resumed_calls.append(candidate_id)
        return _executed_candidate_row(candidate_id, score=scores[candidate_id])

    result = operational.execute_external_candidate_set(
        ROOT,
        attempt_id=ATTEMPT,
        adoption_receipt=adoption,
        measurement_authority=authority,
        command_template=["executor", "{candidate_id}"],
        output_directory=output,
        checkpoint_ledger=ledger,
        reserve_budget_admission=budget,
        arm_incumbents=_arm_incumbents(),
        now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
        executor=resumed,
    )

    assert result["status"] == "PASS_A2_EXACT_COVERAGE"
    assert result["candidate_count"] == 52
    assert first_candidate not in resumed_calls
    assert len(resumed_calls) == 51
    assert result["workers_reaped"] is True


def test_matched_completion_waits_for_fresh_reserve_admission(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    adoption = _adoption()
    authority = _authority(adoption)
    monkeypatch.setattr(operational, "_validate_measurement_authority_provenance", lambda *_a, **_k: None)
    monkeypatch.setattr(operational, "_validate_measurement_goal", lambda *_a, **_k: None)
    calls: list[str] = []

    def executor(command: list[str], **_kwargs: object) -> Mapping[str, object]:
        candidate_id = command[1]
        calls.append(candidate_id)
        return _executed_candidate_row(candidate_id, score="1")

    output = tmp_path / "owner-local-output"
    result = operational.execute_external_candidate_set(
        ROOT,
        attempt_id=ATTEMPT,
        adoption_receipt=adoption,
        measurement_authority=authority,
        command_template=["executor", "{candidate_id}"],
        output_directory=output,
        checkpoint_ledger=tmp_path / "ledger.jsonl",
        executor=executor,
    )
    assert result["status"] == "MATCHED_COMPLETE_RESERVE_ADMISSION_REQUIRED"
    assert len(calls) == 40
    assert not list((output / "receipts").glob("*reserve*.json"))


def test_reserve_admission_and_continuation_drift_fail_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    adoption = _adoption()
    authority = _authority(adoption)
    monkeypatch.setattr(operational, "_validate_measurement_authority_provenance", lambda *_a, **_k: None)
    monkeypatch.setattr(operational, "_validate_measurement_goal", lambda *_a, **_k: None)
    stale = _reserve_budget_admission(adoption, authority)
    with pytest.raises(operational.A2OperationalExecutorError, match="stale or identity-drifted"):
        operational.validate_reserve_budget_admission(
            ROOT,
            stale,
            attempt_id=ATTEMPT,
            adoption_receipt_sha256=str(adoption["receipt_sha256"]),
            authority_sha256=str(authority["authority_sha256"]),
            provider_admission_receipt_sha256=str(stale["provider_admission_receipt_sha256"]),
            now_utc=datetime(2026, 8, 12, 8, 21, tzinfo=timezone.utc),
        )

    matched = {
        candidate_id: receipt
        for candidate_id, receipt in _candidate_receipts().items()
        if receipt["tier"] == "matched"
    }
    budget = _reserve_budget_admission(adoption, authority)
    decision = operational.build_reserve_activation_decision(
        ROOT,
        attempt_id=ATTEMPT,
        receipts_by_candidate=matched,
        adoption_receipt_sha256=str(adoption["receipt_sha256"]),
        authority_sha256=str(authority["authority_sha256"]),
        provider_admission_receipt_sha256=str(budget["provider_admission_receipt_sha256"]),
        arm_incumbents=_arm_incumbents(),
        reserve_budget_admission=budget,
        now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
    )
    assert all(len(item["reserve_candidate_ids"]) == 4 for item in decision["decisions"])
    continuation = operational.build_reserve_continuation(
        ROOT,
        attempt_id=ATTEMPT,
        adoption_receipt_sha256=str(adoption["receipt_sha256"]),
        authority_sha256=str(authority["authority_sha256"]),
        decision=decision,
    )
    assert continuation["matched_candidate_result_set_sha256"] == decision["matched_candidate_result_set_sha256"]


def test_reserve_admission_builder_rebinds_fresh_provider_sources(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    adoption = _adoption()
    authority = _authority(adoption)
    monkeypatch.setattr(operational, "_validate_measurement_authority_provenance", lambda *_a, **_k: None)
    monkeypatch.setattr(operational, "_validate_measurement_goal", lambda *_a, **_k: None)
    observation_path, sources = _provider_observation_paths(tmp_path)
    receipt = operational.build_reserve_budget_admission(
        ROOT,
        attempt_id=ATTEMPT,
        adoption_receipt=adoption,
        measurement_authority=authority,
        provider_observation_path=observation_path,
        source_artifact_paths=sources,
        now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
    )
    assert receipt["provider_admission_receipt_sha256"] != adoption["provider_admission_receipt_sha256"]
    assert receipt["source_artifact_sha256"] == {
        name: file_sha256(path) for name, path in sources.items()
    }


def test_reserve_decision_rejects_caller_incumbent_drift() -> None:
    adoption = _adoption()
    authority = _authority(adoption)
    budget = _reserve_budget_admission(adoption, authority)
    matched = {
        candidate_id: receipt
        for candidate_id, receipt in _candidate_receipts().items()
        if receipt["tier"] == "matched"
    }
    drifted = _arm_incumbents()
    drifted["ARM-03"] = {**drifted["ARM-03"], "primary_metric": "0"}
    with pytest.raises(operational.A2OperationalExecutorError, match="incumbent binding drift"):
        operational.build_reserve_activation_decision(
            ROOT,
            attempt_id=ATTEMPT,
            receipts_by_candidate=matched,
            adoption_receipt_sha256=str(adoption["receipt_sha256"]),
            authority_sha256=str(authority["authority_sha256"]),
            provider_admission_receipt_sha256=str(budget["provider_admission_receipt_sha256"]),
            arm_incumbents=drifted,
            reserve_budget_admission=budget,
            now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
        )


def test_reserve_decision_rejects_tie_and_derives_grounding_from_frozen_quartet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adoption = _adoption()
    authority = _authority(adoption)
    matched = {
        candidate_id: receipt
        for candidate_id, receipt in _candidate_receipts().items()
        if receipt["tier"] == "matched"
    }
    for candidate_id, receipt in tuple(matched.items()):
        row = _candidate_row(candidate_id, score="0")
        matched[candidate_id] = operational.build_candidate_result_receipt(
            ROOT, result=row, evidence_class="engineering_synthetic"
        )
    incumbents = _arm_incumbents()
    budget = _reserve_budget_admission(adoption, authority)
    decision = operational.build_reserve_activation_decision(
        ROOT,
        attempt_id=ATTEMPT,
        receipts_by_candidate=matched,
        adoption_receipt_sha256=str(adoption["receipt_sha256"]),
        authority_sha256=str(authority["authority_sha256"]),
        provider_admission_receipt_sha256=str(budget["provider_admission_receipt_sha256"]),
        arm_incumbents=incumbents,
        reserve_budget_admission=budget,
        now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
    )
    assert decision["active_reserve_candidate_ids"] == []
    assert all(item["strict_primary_improvement"] is False for item in decision["decisions"])

    repeated_axes = copy.deepcopy(frozen_candidates(ROOT))
    for candidate in repeated_axes.values():
        if candidate["tier"] == "conditional_reserve":
            candidate["declared_axis"] = "source_fields"
    monkeypatch.setattr(operational, "frozen_candidates", lambda _root: repeated_axes)
    grounded = operational.build_reserve_activation_decision(
        ROOT,
        attempt_id=ATTEMPT,
        receipts_by_candidate=matched,
        adoption_receipt_sha256=str(adoption["receipt_sha256"]),
        authority_sha256=str(authority["authority_sha256"]),
        provider_admission_receipt_sha256=str(budget["provider_admission_receipt_sha256"]),
        arm_incumbents=incumbents,
        reserve_budget_admission=budget,
        now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
    )
    assert all(item["grounded_axes_remaining"] is True for item in grounded["decisions"])


def test_exact_52_rejects_partial_reserve_quartet_and_decision_hash_drift() -> None:
    receipts = _candidate_receipts()
    reserve_id = next(
        candidate_id
        for candidate_id, candidate in frozen_candidates(ROOT).items()
        if candidate["arm_id"] == "ARM-03" and candidate["tier"] == "conditional_reserve"
    )
    dormant = _candidate_row(reserve_id)
    dormant["reserve_activation_evidence_sha256"] = "7" * 64
    receipts[reserve_id] = operational.build_candidate_result_receipt(
        ROOT, result=dormant, evidence_class="engineering_synthetic"
    )
    with pytest.raises(operational.A2OperationalExecutorError, match="complete arm quartet"):
        operational.evaluate_candidate_receipts(ROOT, receipts_by_candidate=receipts)

    receipts = _candidate_receipts()
    drifted = _candidate_row(reserve_id, score="100")
    drifted["reserve_activation_passed"] = True
    drifted["reserve_activation_evidence_sha256"] = "8" * 64
    drifted["primary_metric"] = {"name": "recall_at_100/out", "value": "100"}
    drifted["secondary_metrics"] = {"ndcg_at_100/out": "100", "ndcg_at_10/out": "100"}
    drifted["latency"] = {"wall_seconds": "1", "search_p95_seconds": "0.1"}
    drifted["cost"] = {"charged_usd": "0", "currency": "USD"}
    drifted["coverage"] = {"expected_units": 1, "completed_units": 1}
    receipts[reserve_id] = operational.build_candidate_result_receipt(
        ROOT, result=drifted, evidence_class="engineering_synthetic"
    )
    with pytest.raises(operational.A2OperationalExecutorError, match="complete arm quartet"):
        operational.evaluate_candidate_receipts(ROOT, receipts_by_candidate=receipts)


def test_execute_cli_fails_closed_without_measured_authority(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    adoption = tmp_path / "adoption.json"
    authority = tmp_path / "authority.json"
    argv = tmp_path / "argv.json"
    owner_input = tmp_path / "owner-input.json"
    adoption.write_text("{}", encoding="ascii")
    authority.write_text("{}", encoding="ascii")
    argv.write_text('["external-executor"]', encoding="ascii")
    owner_input.write_text("{}", encoding="ascii")
    assert operational.main(
        [
            "--repository-root",
            str(ROOT),
            "--attempt-id",
            ATTEMPT,
            "execute",
            "--execution-adoption-receipt",
            str(adoption),
            "--measurement-authority",
            str(authority),
            "--command-argv-json",
            str(argv),
            "--owner-root",
            str(tmp_path),
            "--owner-input-manifest",
            str(owner_input),
            "--output-directory",
            str(tmp_path / "output"),
            "--checkpoint-ledger",
            str(tmp_path / "ledger.jsonl"),
        ]
    ) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "FAILED_CLOSED"
    assert result["error"] in {
        "external executor argv must match tracked measured adapter",
        "receipt_sha256 is invalid",
        "Owner-local measured input manifest is missing or invalid",
    }
