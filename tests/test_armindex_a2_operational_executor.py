from __future__ import annotations

import copy
import io
import json
import subprocess
import tarfile
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
        "ttl_hours": 40,
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


def _candidate_row(candidate_id: str, *, score: str = "1") -> dict[str, object]:
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
        "train_only": True,
        "rep_dev_measured": False,
        "protected_payload_included": False,
        "per_query_outcomes_included": False,
    }


def _candidate_receipts() -> dict[str, dict[str, object]]:
    receipts: dict[str, dict[str, object]] = {}
    for index, candidate_id in enumerate(frozen_candidates(ROOT), start=1):
        receipts[candidate_id] = operational.build_candidate_result_receipt(
            ROOT,
            result=_candidate_row(candidate_id, score=str(index)),
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
        "ttl_hours": 40,
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
            result=_candidate_row(candidate_id),
            evidence_class="measured_development_aggregate",
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


def test_provider_admission_rejects_stale_and_partial_quote() -> None:
    with pytest.raises(A2ExecutionReadinessError, match="not fresh"):
        build_provider_admission_receipt(
            ROOT,
            attempt_id=ATTEMPT,
            provider_evidence=_provider_evidence(),
            runtime_sha256="a" * 64,
            model_lockset_sha256="b" * 64,
            data_handoff_sha256="c" * 64,
            management_authority_sha256="d" * 64,
            now_utc=datetime(2026, 8, 12, 9, 0, tzinfo=timezone.utc),
        )
    partial = _provider_evidence()
    partial["all_fee_components_usd"].pop("tax_or_surcharge_usd")  # type: ignore[union-attr]
    with pytest.raises(A2ExecutionReadinessError, match="all required quote"):
        build_provider_admission_receipt(
            ROOT,
            attempt_id=ATTEMPT,
            provider_evidence=partial,
            runtime_sha256="a" * 64,
            model_lockset_sha256="b" * 64,
            data_handoff_sha256="c" * 64,
            management_authority_sha256="d" * 64,
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
    known.write_text("pinned", encoding="ascii")
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
    provider = build_provider_admission_receipt(
        ROOT,
        attempt_id=ATTEMPT,
        provider_evidence=_provider_evidence(),
        runtime_sha256="a" * 64,
        model_lockset_sha256="b" * 64,
        data_handoff_sha256="c" * 64,
        management_authority_sha256="d" * 64,
        now_utc=datetime(2026, 8, 12, 8, 5, tzinfo=timezone.utc),
    )
    outputs = iter(("", "", "", "dead-watchdog"))

    def runner(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess([], 0, next(outputs), "")

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
            runner=runner,
        )


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
    tmp_path: Path,
) -> None:
    adoption = _adoption()
    authority = _authority(adoption)
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
        return _candidate_row(candidate_id, score="100")

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
        return _candidate_row(candidate_id, score=scores[candidate_id])

    result = operational.execute_external_candidate_set(
        ROOT,
        attempt_id=ATTEMPT,
        adoption_receipt=adoption,
        measurement_authority=authority,
        command_template=["executor", "{candidate_id}"],
        output_directory=output,
        checkpoint_ledger=ledger,
        executor=resumed,
    )

    assert result["status"] == "PASS_A2_EXACT_COVERAGE"
    assert result["candidate_count"] == 52
    assert first_candidate not in resumed_calls
    assert len(resumed_calls) == 39
    assert result["workers_reaped"] is True


def test_execute_cli_fails_closed_without_measured_authority(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    adoption = tmp_path / "adoption.json"
    authority = tmp_path / "authority.json"
    argv = tmp_path / "argv.json"
    adoption.write_text("{}", encoding="ascii")
    authority.write_text("{}", encoding="ascii")
    argv.write_text('["external-executor"]', encoding="ascii")
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
            "--output-directory",
            str(tmp_path / "output"),
            "--checkpoint-ledger",
            str(tmp_path / "ledger.jsonl"),
        ]
    ) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "FAILED_CLOSED"
    assert "receipt_sha256 is invalid" in result["error"]
