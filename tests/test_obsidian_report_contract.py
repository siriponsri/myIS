from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from myis_research.projections.read_model import build_read_model, canonical_json, sha256
from myis_research.report_records import build_report_records
from myis_research.report_cli import (
    VAULT_RELATIVE_PATH,
    _a010_projection_lifecycle,
    _armindex_paper_artifact_contents,
    _brain_report_contents,
    _check,
    _compatibility_report_contents,
    _obsidian_vault_contents,
    _paper_report_contents,
    _projection_identity_fingerprint,
    _validate_generated_contents,
    correct_advisor_update,
    present_advisor_update,
    projection_report_contents,
    validate_advisor_update,
    write_projection_reports,
)


ROOT = Path(__file__).resolve().parents[1]


def _projection_bindings() -> dict[str, str]:
    return {
        "archive_sha256": "a" * 64,
        "config_sha256": "b" * 64,
        "dataset_lineage_sha256": "c" * 64,
        "environment_sha256": "d" * 64,
        "evaluator_sha256": "e" * 64,
        "metric_registry_sha256": "f" * 64,
        "read_model_revision": "1" * 64,
        "read_model_sha256": "2" * 64,
        "rule_registry_sha256": "3" * 64,
        "schema_registry_sha256": "4" * 64,
    }


def _vault_contents() -> dict[Path, str]:
    model = build_read_model(ROOT)
    return {
        relative: content
        for relative, content in projection_report_contents(ROOT, model).items()
        if relative.is_relative_to(ROOT / VAULT_RELATIVE_PATH)
    }


def test_generated_vault_uses_v2_property_vocabulary_and_resolvable_links() -> None:
    contents = _vault_contents()
    _validate_generated_contents({path.relative_to(ROOT): content for path, content in contents.items()})
    phase_reports = [path for path in contents if path.name.endswith("_MASTER_REPORT.md")]
    task_reports = [path for path in contents if "/Tasks/" in path.as_posix()]
    assert len(phase_reports) == 5
    assert len(task_reports) == 9
    result_report = contents[ROOT / VAULT_RELATIVE_PATH / "03_Results/Current/P1_CPU_BASELINE_RESULT.md"]
    phase_report = contents[ROOT / VAULT_RELATIVE_PATH / "01_Phases/P1_CPU_BASELINE/P1_CPU_BASELINE_MASTER_REPORT.md"]
    p2_task_report = contents[ROOT / VAULT_RELATIVE_PATH / "01_Phases/P2_SCOPE_DEVELOPMENT/Tasks/P2.1.md"]
    audit_report = contents[ROOT / VAULT_RELATIVE_PATH / "05_Research_History/P2_OFFICIAL_REVIEW_AUDIT.md"]
    fixture_report = contents[ROOT / VAULT_RELATIVE_PATH / "05_Research_History/P2_FIXTURE_PILOT.md"]
    pending_report = contents[ROOT / VAULT_RELATIVE_PATH / "03_Results/Current/P2_MEASURED_PENDING.md"]
    assert "## Output" in result_report
    assert "## Interpretation" in result_report
    assert "## Execution progress / observability" in result_report
    assert "## Execution progress / observability" in phase_report
    assert "P1_CPU_MEASURED_COMPLETE" in contents[ROOT / VAULT_RELATIVE_PATH / "HOME.md"]
    assert "## สถานะตอนนี้" in audit_report
    assert "Round `3`" in audit_report
    assert "**accept**" in audit_report
    assert "engineering provenance" in audit_report
    assert "[[P2_SCOPE_DEVELOPMENT_MASTER_REPORT]]" in audit_report
    assert 'evidence_maturity: "non_scientific"' in p2_task_report
    assert 'evidence_maturity: "fixture"' in fixture_report
    assert "fixture status **passed**" in fixture_report
    assert "`32` candidates" in fixture_report
    assert "Owner-local measured preflight" in fixture_report
    assert "Real candidates `0 / 32`" in fixture_report
    assert "`32`" not in pending_report
    assert "`0.72`" not in pending_report
    assert "measured results = `unavailable`" in pending_report


def test_generic_obsidian_notes_use_the_current_armindex_next_command() -> None:
    model = build_read_model(ROOT)
    contents = _obsidian_vault_contents(ROOT, model)
    expected = model["armindex"]["next_command"]

    for relative_path in (
        VAULT_RELATIVE_PATH / "HOME.md",
        VAULT_RELATIVE_PATH / "00_Home/ARM_INDEX_HOME.md",
    ):
        frontmatter = yaml.safe_load(contents[relative_path].split("---", 2)[1])
        assert frontmatter["next_authorized_action"] == expected


def test_obsidian_generation_fails_closed_without_current_armindex_next_command() -> None:
    model = build_read_model(ROOT)
    broken = {
        **model,
        "armindex": {**model["armindex"], "next_command": ""},
    }

    with pytest.raises(ValueError, match="current ArmIndex next command"):
        _obsidian_vault_contents(ROOT, broken)


def test_a12_v11_request_is_the_canonical_projection_lifecycle_source() -> None:
    model = build_read_model(ROOT)
    manifest = json.loads(
        (ROOT / VAULT_RELATIVE_PATH / "00_System/Generated/generated-manifest.json").read_text(
            encoding="utf-8"
        )
    )
    archive_text = (ROOT / "mlflow/generated/archive-index.v2.json").read_text(encoding="utf-8")
    external_outputs = {
        **_brain_report_contents(ROOT, model),
        **_paper_report_contents(ROOT, model),
        **_compatibility_report_contents(ROOT, model),
    }

    lifecycle = _a010_projection_lifecycle(
        ROOT,
        model,
        archive_text=archive_text,
        obsidian_manifest_sha256=str(manifest["manifest_sha256"]),
        external_outputs=external_outputs,
    )
    v11 = model["armindex"]["a1_2_contract_scaffold"][
        "scientific_execution_request_v11"
    ]

    assert lifecycle["source_receipt_uri"] == (
        "campaigns/armindex-multiretriever-v2/evidence/"
        "a1.2-scientific-execution-adoption-request.receipt.v11.json"
    )
    assert lifecycle["source_receipt_sha256"] == v11["receipt_sha256"]


def test_a010_task_report_is_receipt_driven_and_uses_the_fifteen_section_contract() -> None:
    model = build_read_model(ROOT)
    armindex = dict(model["armindex"])
    phases = [dict(phase) for phase in armindex["phases"]]
    a0 = next(phase for phase in phases if phase["phase_id"] == "A0_MIGRATION_FOUNDATION")
    a0["tasks"] = [
        *[task for task in a0["tasks"] if task["task_id"] != "A0.10"],
        {"task_id": "A0.10", "title": "Legacy code harvest and phase-ready scaffolding", "status": "in_progress"},
    ]
    armindex["phases"] = phases
    armindex["legacy_code_harvest"] = {
        "status": "in_progress",
        "validated": True,
        "ledger_uri": "control/armindex/a0.10-legacy-code-harvest-ledger.v1.json",
        "ledger_sha256": "a" * 64,
        "receipt_uri": "campaigns/armindex-multiretriever-v2/evidence/a0.10-legacy-code-harvest.receipt.v1.json",
        "receipt_sha256": "b" * 64,
        "fixture_status": "not_started",
        "fixture_receipt_uri": None,
        "fixture_receipt_sha256": None,
        "repository_hygiene_audit_uri": "outputs/audits/repository/repository-hygiene-a0.10-20260804.json",
        "repository_hygiene_audit_sha256": "c" * 64,
        "output_root_relocation_receipt_uri": "outputs/audits/dashboard/output-root-relocation-20260804.json",
        "output_root_relocation_receipt_sha256": "d" * 64,
        "source_verification_receipt_uri": "outputs/audits/repository/thaipha-lex-source-verification-a0.10-20260804.json",
        "source_verification_receipt_sha256": "e" * 64,
        "components_reviewed": 3,
        "components_adopted": 1,
        "components_rejected": 2,
        "measured_runs": 0,
        "selection_accesses": 0,
        "final_accesses": 0,
    }
    model = {**model, "armindex": armindex}
    model.pop("read_model_revision")
    model.pop("projection_revision")
    model.pop("read_model_sha256")
    revision_body = {
        key: value
        for key, value in model.items()
        if key != "generated_at"
    }
    model["read_model_revision"] = sha256(canonical_json(revision_body))
    model["projection_revision"] = model["read_model_revision"]
    model["read_model_sha256"] = sha256(canonical_json(model))

    outputs = projection_report_contents(ROOT, model)
    task_path = ROOT / VAULT_RELATIVE_PATH / "02_Tasks/ArmIndex/A0_MIGRATION_FOUNDATION/A0.10.md"
    task_report = outputs[task_path]
    task_record = next(
        record
        for record in build_report_records(ROOT, model)
        if record["report_id"] == "task-a0-10"
    )
    frontmatter = yaml.safe_load(task_report.split("---", 2)[1])
    assert frontmatter["next_authorized_action"] == task_record["next_authorized_action"]
    for heading in (
        "Objective", "Starting State", "Inputs and Frozen Bindings", "Work Performed",
        "Artifacts Produced", "Metrics", "Result", "Interpretation", "Supported Claims",
        "Unsupported Claims", "Failures and Recovery", "Governance and Safety", "Decision",
        "Next Action", "Evidence Links",
    ):
        assert f"## {heading}" in task_report
    assert "a0.10-legacy-code-harvest.receipt.v1.json" in task_report
    assert "repository-hygiene-a0.10-20260804.json" in task_report
    assert "output-root-relocation-20260804.json" in task_report
    assert "thaipha-lex-source-verification-a0.10-20260804.json" in task_report
    assert "a0.10-legacy-code-harvest-independent-revise-20260804" in task_report
    assert "a0.10-legacy-code-harvest-independent-accept-20260804" in task_report
    assert "repaired_and_validated" in task_report
    assert "Measured P2, real selection, and final evaluation" in task_report


def test_every_registered_phase_and_task_report_is_detailed_english() -> None:
    model = build_read_model(ROOT)
    records = build_report_records(ROOT, model)

    assert len(records) == 40
    assert sum(record["report_type"] == "phase" for record in records) == 12
    assert sum(record["report_type"] == "task" for record in records) == 28
    assert {record["language"] for record in records} == {"en"}

    a2_task = next(record for record in records if record["report_id"] == "task-a2-1")
    a2_freeze_task = next(
        record
        for record in records
        if record["report_id"] == "task-official_codex_bridge_and_candidate_freeze"
    )
    a2_phase = next(
        record
        for record in records
        if record["report_id"] == "phase-a2_per_arm_autoindex"
    )
    assert a2_task["result"]["decision"] == (
        "NEEDS_IM_NEW_INSTANCE_REBIND_MEASUREMENT_LOCKED"
    )
    assert "additive fresh-instance binding" in a2_task["result"]["result"]
    assert "pending AP fresh-instance admission and isolated staging" in a2_task["result"]["result"]
    assert "pending the production adapter" not in a2_task["result"]["result"]
    assert "deployment-package validation. " not in a2_task["result"]["result"]
    assert a2_task["scientific_authority"] is False
    assert a2_phase["result"]["decision"] == (
        "NEEDS_IM_NEW_INSTANCE_REBIND_MEASUREMENT_LOCKED"
    )
    assert a2_phase["scientific_authority"] is False
    assert a2_freeze_task["result"]["decision"] == "CLOSED_PASS_INDEPENDENT_AUDIT"

    outputs = projection_report_contents(ROOT, model)
    task_path = (
        ROOT
        / VAULT_RELATIVE_PATH
        / "02_Tasks/ArmIndex/A1_BASELINES_AND_MULTI_ARM_SCREENING/A1.1.md"
    )
    report = outputs[task_path]
    assert re.search(r"[\u0e00-\u0e7f]", report) is None
    assert "A1.2 resource planning boundary" in report
    assert "24" in report
    assert "10-20" in report
    assert "USD `23` for A1" in report
    assert "proposal_not_adopted_execution_locked" in report

    a12_report = outputs[
        ROOT
        / VAULT_RELATIVE_PATH
        / "02_Tasks/ArmIndex/A1_BASELINES_AND_MULTI_ARM_SCREENING/A1.2.md"
    ]
    assert "A1.2 closeout validation audit" in a12_report
    assert "A1.2 Vast preflight closeout validation audit" in a12_report
    assert "a1.2-v2-pyproject-v1-source-binding-drift-20260806" in a12_report
    assert "A1.2 Vast post-commit correction receipt v3" in a12_report
    assert "A1.2 runtime-minimal direct-base receipt v5" in a12_report
    assert "A1.2 live-container correction receipt v6" in a12_report
    assert "A1.2 same-instance repair receipt v7" in a12_report
    assert "A1.2 validation-complete frozen-bundle repair receipt v8" in a12_report
    assert "A1.2 execution-lifecycle repair receipt v9" in a12_report
    assert "A1.2 Owner-local provider closeout receipt v10" in a12_report
    assert "A1.2 scientific execution and adoption request v11" in a12_report
    assert "A1.2 remote allowlisted handoff retention audit" in a12_report
    assert "A1.2 terminal closeout state" in a12_report
    assert "complete `25/25` REP-DEV coverage" in a12_report
    assert "provider disposition `REUSE_ELIGIBLE`" in a12_report
    assert "baseline `29/29`" in a12_report
    assert "journal EDA `8/8`" in a12_report
    assert "closeout `12/12`" in a12_report
    assert "request is prepared for Owner review only" not in a12_report
    assert "remains conditional and is not authorized now" not in a12_report
    assert "v6-initial-wheelhouse-missing-pydantic" in a12_report
    assert "v6-supplement-repair-mutated-pycache-tree" in a12_report
    assert "v7-frozen-bundle-missing-validation-lineage" in a12_report
    assert "A1.2 Owner conditional instance-continuation policy" in a12_report
    assert "a1.2-v2-postcommit-head-tree-regeneration-defect-20260806" in a12_report
    assert "A1.2 v3 deterministic projection stability repair" in a12_report
    assert "a1.2-v3-runtime-git-identity-projection-drift-20260806" in a12_report

    a12_record = next(
        record for record in records if record["report_id"] == "task-a1-2"
    )
    failure_ids = {
        item["failure_id"] for item in a12_record["failure_recovery_references"]
    }
    assert "a1.2-v2-pyproject-v1-source-binding-drift-20260806" in failure_ids
    assert "v6-initial-wheelhouse-missing-pydantic" in failure_ids
    assert "v6-supplement-repair-mutated-pycache-tree" in failure_ids

    sync_receipt = json.loads((ROOT / "projections/sync-receipt.v2.json").read_text(encoding="utf-8"))
    assert sync_receipt["source_receipt_uri"].endswith(
        "a1.2-scientific-execution-adoption-request.receipt.v11.json"
    )
    mlflow_index = json.loads((ROOT / "mlflow/generated/archive-index.v2.json").read_text(encoding="utf-8"))
    assert mlflow_index["armindex_a1_2_contract_scaffold"]["status"] == (
        "a1_2_contract_scaffold_complete_launch_locked"
    )
    assert mlflow_index["armindex_a1_2_vast_preflight"]["status"] == (
        "offline_preparation_complete_live_owner_preflight_pending"
    )
    assert mlflow_index["armindex_a1_2_vast_preflight"]["planning_rate_usd_per_instance_hour"] == 0.6
    assert mlflow_index["armindex_a1_2_vast_postcommit"]["status"] == (
        "postcommit_validator_prepared_live_owner_preflight_pending"
    )
    assert mlflow_index["armindex_a1_2_vast_postcommit"]["launch_allowed"] is False
    assert mlflow_index["armindex_a1_2_vast_postcommit"]["adopted_for_execution"] is False
    assert mlflow_index["armindex_a1_2_runtime_minimal_direct_base"]["status"] == (
        "direct_base_preflight_prepared_local_owner_stage_pending"
    )
    assert mlflow_index["armindex_a1_2_runtime_minimal_direct_base"]["custom_local_docker_build"] is False
    assert mlflow_index["armindex_a1_2_runtime_minimal_direct_base"]["launch_allowed"] is False
    assert mlflow_index["armindex_a1_2_live_preflight_correction"]["status"] == (
        "live_correction_prepared_preflight_pending"
    )
    assert mlflow_index["armindex_a1_2_live_preflight_correction"]["launch_allowed"] is False
    assert mlflow_index["armindex_a1_2_live_preflight_correction"]["adopted_for_execution"] is False
    assert mlflow_index["armindex_a1_2_live_preflight_correction"]["continuation_policy"][
        "continuation_authorized_now"
    ] is False
    assert mlflow_index["armindex_a1_2_live_preflight_same_instance_repair"]["status"] == (
        "same_instance_repair_prepared_preflight_pending"
    )
    assert mlflow_index["armindex_a1_2_live_preflight_same_instance_repair"][
        "launch_allowed"
    ] is False
    assert len(mlflow_index["armindex_a1_2_live_preflight_same_instance_repair"][
        "preserved_live_failures"
    ]) == 2
    assert mlflow_index["armindex_a1_2_live_preflight_validation_complete_bundle_repair"]["status"] == (
        "validation_complete_bundle_repair_prepared_preflight_pending"
    )
    assert mlflow_index["armindex_a1_2_live_preflight_validation_complete_bundle_repair"][
        "launch_allowed"
    ] is False
    assert mlflow_index["armindex_a1_2_live_preflight_execution_lifecycle_repair"]["status"] == (
        "execution_lifecycle_repair_prepared_preflight_pending"
    )
    assert mlflow_index["armindex_a1_2_live_preflight_execution_lifecycle_repair"][
        "launch_allowed"
    ] is False
    assert mlflow_index["armindex_a1_2_provider_closeout"]["status"] == "PASS"
    assert mlflow_index["armindex_a1_2_provider_closeout"]["provider_closeout"][
        "owner_disposition"
    ] == "destroyed_and_provider_absence_verified"
    assert mlflow_index["armindex_a1_2_provider_closeout"]["pending_provider_checks"] == []
    assert mlflow_index["armindex_a1_2_provider_closeout"]["launch_allowed"] is False
    request_v11 = mlflow_index["armindex_a1_2_scientific_execution_request"]
    assert request_v11["status"] == "PASS"
    assert request_v11["workload_manifests"] == 5
    assert request_v11["expected_program_arm_runs"] == 25
    assert request_v11["launch_allowed"] is False
    assert request_v11["adopted_for_execution"] is False
    assert request_v11["measured_runs"] == 0
    assert request_v11["selection_accesses"] == 0
    assert request_v11["final_accesses"] == 0
    assert request_v11["charged_usd"] == 0

    required_headings = (
        "Objective", "Starting State", "Inputs and Frozen Bindings", "Work Performed",
        "Artifacts Produced", "Metrics", "Result", "Interpretation", "Supported Claims",
        "Unsupported Claims", "Failures and Recovery", "Governance and Safety", "Decision",
        "Next Action", "Evidence Links",
    )
    phase_task_paths = [
        path for path in outputs
        if path.suffix == ".md"
        and (
            "01_Phases/" in path.as_posix()
            or "02_Tasks/ArmIndex/" in path.as_posix()
        )
        and (
            path.name.endswith("_MASTER_REPORT.md")
            or ("/01_Phases/ArmIndex/" in path.as_posix() and path.name.endswith("_REPORT.md"))
            or "/Tasks/" in path.as_posix()
            or "/02_Tasks/ArmIndex/" in path.as_posix()
        )
    ]
    assert len(phase_task_paths) == 40
    for path in phase_task_paths:
        content = outputs[path]
        assert re.search(r"[\u0e00-\u0e7f]", content) is None
        for heading in required_headings:
            assert f"## {heading}" in content


def test_generated_vault_raw_hashes_are_checkout_stable() -> None:
    vault_root = ROOT / VAULT_RELATIVE_PATH
    manifest = json.loads(
        (vault_root / "00_System/Generated/generated-manifest.json").read_text(encoding="utf-8")
    )
    for entry in manifest["files"]:
        path = vault_root / entry["relative_path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]

    attributes = {
        line.strip()
        for line in (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert {
        "control/source-of-truth.yaml -text whitespace=cr-at-eol",
        "control/execution-envelope.yaml -text",
        "obsidian_report/** -text",
        "obsidian_report/**/Owner_Notes/** text",
        "obsidian_report/80_Owner_Notes/** text",
        "obsidian_report/.obsidian/** text",
        "obsidian_report/*.canvas text",
        "mlflow/generated/archive-index.v2.json -text",
        "projections/obsidian/generated/** -text",
        "projections/reports/** -text",
        "schemas/read-model.v2.json -text",
        "docs/observatory/REPORTING_POLICY.md -text",
        "evidence/literature/digests/** -text",
        "PLAN.md -text",
        "control/campaigns/scope-autoindex-v1.yaml -text",
        "control/decisions/D1_START_CAMPAIGN.yaml -text",
        "schemas/scope-dsl.v1.json -text",
        "src/myis_research/scope/compiler.py -text",
    } <= attributes


def test_internal_projection_bytes_are_checkout_stable_and_current() -> None:
    model = build_read_model(ROOT)
    drift = [
        path.relative_to(ROOT).as_posix()
        for path, content in projection_report_contents(ROOT, model).items()
        if path.is_relative_to(ROOT)
        and (not path.is_file() or path.read_bytes() != content.encode("utf-8"))
    ]
    assert drift == []


def test_projection_archive_identity_changes_when_generator_binding_changes() -> None:
    bindings = _projection_bindings()
    first = _projection_identity_fingerprint(**bindings)
    assert first == _projection_identity_fingerprint(**bindings)
    assert first != _projection_identity_fingerprint(
        **{**bindings, "evaluator_sha256": "9" * 64}
    )
    with pytest.raises(ValueError, match="bindings are incomplete"):
        _projection_identity_fingerprint(**{key: value for key, value in bindings.items() if key != "archive_sha256"})


def test_brain_and_paper_projections_share_current_v2_read_model_without_protected_fields() -> None:
    model = build_read_model(ROOT)
    outputs = projection_report_contents(ROOT, model)
    brain_directory = (ROOT.parent / "02_Brain/reports/generated").resolve()
    expected_brain_files = {
        "MOC.md",
        "datasets.md",
        "experiments.md",
        "phase-P0_FOUNDATION.md",
        "phase-P1_CPU_BASELINE.md",
        "phase-P2_SCOPE_DEVELOPMENT.md",
        "phase-P3_FINAL.md",
        "phase-P4_PUBLICATION.md",
        "phase-task-status.md",
        "program-status.md",
        "publication-readiness.md",
        "weekly-summary.md",
    }
    brain_outputs = {
        path.name: content
        for path, content in outputs.items()
        if path.parent == brain_directory
    }
    assert set(brain_outputs) == expected_brain_files
    for content in brain_outputs.values():
        assert model["read_model_revision"] in content
        assert "read-model.v2.json" in content
        assert "read-model.v1.json" not in content
        assert "query_ids:" not in content.lower()
        assert "split_membership:" not in content.lower()
        assert "per_query" not in content.lower()

    p1_report = brain_outputs["phase-P1_CPU_BASELINE.md"]
    assert "`P1.1` **measured**" in p1_report
    assert "`P1.2` **measured**" in p1_report
    assert "`P1.3` **measured**" in p1_report
    assert "every `120` seconds" in p1_report
    assert model["results"][0]["package_sha256"] in p1_report
    assert "descriptive train/selection results" in p1_report

    paper_path = (
        ROOT.parent
        / "03_Paper/publications/isai-nlp-2026/generated/publication-readiness.md"
    ).resolve()
    assert model["read_model_revision"] in outputs[paper_path]
    assert "P1_CPU_MEASURED_COMPLETE" in outputs[paper_path]
    assert "D2 and D3 remain Owner-only" in outputs[paper_path]
    source_lock_path = (
        ROOT.parent
        / "03_Paper/publications/isai-nlp-2026/provenance/publication-source-lock.json"
    ).resolve()
    source_lock = json.loads(outputs[source_lock_path])
    assert source_lock["schema_version"] == "myis.publication-source-lock.v2"
    assert source_lock["read_model_revision"] == model["read_model_revision"]
    assert source_lock["read_model_sha256"] == model["read_model_sha256"]
    assert source_lock["claim_boundary"] == "train_selection_only"


def test_a2_publication_artifacts_preserve_v1_and_bind_resolvable_v2_uris() -> None:
    legacy_schema = json.loads((ROOT / "schemas/artifact-index.v1.json").read_text())
    legacy_index = {
        "schema_version": "myis.artifact-index.v1",
        "run_id": "legacy-run",
        "artifacts": [],
    }
    assert list(Draft202012Validator(legacy_schema).iter_errors(legacy_index)) == []

    model = build_read_model(ROOT)
    outputs = _armindex_paper_artifact_contents(ROOT, model)
    paper_provenance = (ROOT.parent / "03_Paper/01_ArmIndex/provenance").resolve()
    canonical_provenance = (
        ROOT / "outputs/publication/armindex/a2-candidate-freeze/provenance"
    ).resolve()
    paper_index_path = paper_provenance / "artifact-index.v2.json"
    canonical_index_path = canonical_provenance / "artifact-index.v2.json"
    paper_graph_path = paper_provenance / "artifact-provenance-graph.v1.json"
    canonical_graph_path = canonical_provenance / "artifact-provenance-graph.v1.json"

    assert outputs[paper_index_path] == outputs[canonical_index_path]
    assert outputs[paper_graph_path] == outputs[canonical_graph_path]
    index = json.loads(outputs[paper_index_path])
    graph = json.loads(outputs[paper_graph_path])
    index_schema = json.loads((ROOT / "schemas/artifact-index.v2.json").read_text())
    graph_schema = json.loads(
        (ROOT / "schemas/artifact-provenance-graph.v1.json").read_text()
    )
    assert list(Draft202012Validator(index_schema).iter_errors(index)) == []
    assert list(Draft202012Validator(graph_schema).iter_errors(graph)) == []

    for artifact in index["artifacts"]:
        resolved = (paper_provenance / artifact["uri"]).resolve()
        assert resolved.is_relative_to(ROOT)
        assert resolved.is_file()
        assert hashlib.sha256(resolved.read_bytes()).hexdigest() == artifact["sha256"]


def test_two_syncs_are_idempotent_and_preserve_owner_files(tmp_path: Path) -> None:
    # Use the real safe repository metadata while redirecting only the vault writes.
    repo = tmp_path / "repo"
    repo.mkdir()
    for relative in ("control", "campaigns", "evidence", "schemas"):
        source = ROOT / relative
        if source.exists():
            # Symlinks keep the fixture small and are not part of the output vault.
            (repo / relative).symlink_to(source, target_is_directory=True)
    # The builder also uses these source files to calculate a source commit fallback.
    (repo / "src").symlink_to(ROOT / "src", target_is_directory=True)
    owner = repo / VAULT_RELATIVE_PATH / "80_Owner_Notes" / "meeting.md"
    owner.parent.mkdir(parents=True)
    owner.write_bytes(b"owner bytes must remain exact\n")
    model = build_read_model(repo)
    write_projection_reports(repo, model)
    first = {path.relative_to(repo).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in (repo / VAULT_RELATIVE_PATH).rglob("*") if path.is_file()}
    write_projection_reports(repo, model)
    second = {path.relative_to(repo).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in (repo / VAULT_RELATIVE_PATH).rglob("*") if path.is_file()}
    assert first == second
    assert owner.read_bytes() == b"owner bytes must remain exact\n"


def test_read_model_only_check_does_not_require_external_projections(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("external projection validation must not run")

    monkeypatch.setattr("myis_research.report_cli.projection_report_contents", fail_if_called)
    monkeypatch.setattr("myis_research.report_cli._validate_sync_receipt", fail_if_called)
    result = _check(
        ROOT,
        ROOT / "projections/read-model/read-model.v2.json",
        read_model_only=True,
    )
    assert result["status"] == "PASS"
    assert result["read_model_drift"] is False
    assert result["report_drift"] == []
    assert result["sync_receipt_error"] is None


def test_generated_content_rejects_unsafe_protected_and_unknown_properties() -> None:
    unsafe = {
        VAULT_RELATIVE_PATH / "unsafe.md": "---\nschema_version: \"myis.obsidian-note.v2\"\nnote_id: \"UNSAFE\"\nnote_type: \"home\"\nworkflow_status: \"ready\"\nevidence_maturity: \"non_scientific\"\nclaim_level: \"none\"\nsafe_to_present: true\nmanaged_by: \"myis-report\"\nedit_policy: \"generated_do_not_edit\"\nread_model_revision: \"x\"\nread_model_sha256: \"x\"\nsource_commit: \"x\"\nprojection_schema_version: \"x\"\nsource_run_ids: []\nsource_manifest_sha256: []\nrelated_literature_ids: []\nrelated_decision_ids: []\n---\n<script>alert(1)</script>\n",
    }
    with pytest.raises(ValueError, match="unsafe generated content"):
        _validate_generated_contents(unsafe)
    protected = {
        VAULT_RELATIVE_PATH / "protected.md": unsafe[VAULT_RELATIVE_PATH / "unsafe.md"].replace(
            "<script>alert(1)</script>", "query_ids: forbidden"
        ),
    }
    with pytest.raises(ValueError, match="protected or remote generated content"):
        _validate_generated_contents(protected)


def test_generated_content_rejects_stale_fixture_review_and_measured_state() -> None:
    model = build_read_model(ROOT)
    contents = {
        path.relative_to(ROOT): content
        for path, content in projection_report_contents(ROOT, model).items()
        if path.is_relative_to(ROOT / VAULT_RELATIVE_PATH)
    }
    stale_fixture = dict(contents)
    stale_fixture[VAULT_RELATIVE_PATH / "05_Research_History/P2_FIXTURE_PILOT.md"] += (
        "\nFixture remains not executed.\n"
    )
    with pytest.raises(ValueError, match="stale fixture narrative"):
        _validate_generated_contents(stale_fixture, model)

    stale_review = dict(contents)
    stale_review[VAULT_RELATIVE_PATH / "05_Research_History/P2_OFFICIAL_REVIEW_AUDIT.md"] += (
        "\nOfficial review pending.\n"
    )
    with pytest.raises(ValueError, match="stale official review narrative"):
        _validate_generated_contents(stale_review, model)

    unrelated_pending = dict(contents)
    unrelated_pending[
        VAULT_RELATIVE_PATH / "05_Research_History/P2_OFFICIAL_REVIEW_AUDIT.md"
    ] += "\nNext action: live-provider inputs remain pending.\n"
    _validate_generated_contents(unrelated_pending, model)

    stale_measured = dict(contents)
    stale_measured[VAULT_RELATIVE_PATH / "03_Results/Current/P2_SCOPE_DEVELOPMENT_RESULT.md"] += (
        "\nMeasured P2 started.\n"
    )
    with pytest.raises(ValueError, match="measured P2 narrative"):
        _validate_generated_contents(stale_measured, model)


def test_advisor_snapshot_is_immutable_and_correction_is_append_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Present/correct operate on an isolated vault but build from safe checked-in metadata.
    monkeypatch.setattr("myis_research.report_cli.build_read_model", lambda root: build_read_model(ROOT))
    first = present_advisor_update(tmp_path, "ADVISOR-001")
    original = first.read_bytes()
    with pytest.raises(ValueError, match="immutable"):
        present_advisor_update(tmp_path, "ADVISOR-001")
    correction = correct_advisor_update(tmp_path, "ADVISOR-002", "ADVISOR-001")
    assert first.read_bytes() == original
    assert "corrects_snapshot_id: \"ADVISOR-001\"" in correction.read_text(encoding="utf-8")
    assert validate_advisor_update(tmp_path)["status"] == "PASS"
