from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from myis_research.projections.read_model import build_read_model
from myis_research.report_cli import (
    VAULT_RELATIVE_PATH,
    _check,
    _validate_generated_contents,
    correct_advisor_update,
    present_advisor_update,
    projection_report_contents,
    validate_advisor_update,
    write_projection_reports,
)


ROOT = Path(__file__).resolve().parents[1]


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
    assert "## Output" in contents[ROOT / VAULT_RELATIVE_PATH / "03_Results/Current/P1_CPU_BASELINE_RESULT.md"]
    assert "## Interpretation" in contents[ROOT / VAULT_RELATIVE_PATH / "03_Results/Current/P1_CPU_BASELINE_RESULT.md"]
    assert "P1 is not measured complete" in contents[ROOT / VAULT_RELATIVE_PATH / "HOME.md"]


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
