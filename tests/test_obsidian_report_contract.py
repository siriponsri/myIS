from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from myis_research.projections.read_model import build_read_model
from myis_research.report_cli import (
    VAULT_RELATIVE_PATH,
    _check,
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
    assert "## Output" in result_report
    assert "## Interpretation" in result_report
    assert "## Execution progress / observability" in result_report
    assert "## Execution progress / observability" in phase_report
    assert "P1_CPU_MEASURED_COMPLETE" in contents[ROOT / VAULT_RELATIVE_PATH / "HOME.md"]


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
        "obsidian_report/** -text",
        "obsidian_report/**/Owner_Notes/** text",
        "obsidian_report/80_Owner_Notes/** text",
        "obsidian_report/.obsidian/** text",
        "obsidian_report/*.canvas text",
    } <= attributes


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
