import hashlib
import json
from pathlib import Path

import yaml

from myis_research.kernel.canonical import canonical_sha256
from myis_research.layout import REQUIRED, validate


def test_active_layout_has_no_legacy_roots():
    result = validate(Path(__file__).resolve().parents[1])
    assert result["status"] == "PASS", result


def test_legacy_singular_output_root_is_rejected(tmp_path: Path):
    for item in REQUIRED:
        target = tmp_path / item
        if target.suffix:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.touch()
        else:
            target.mkdir(parents=True, exist_ok=True)
    (tmp_path / "output").mkdir()

    result = validate(tmp_path)

    assert result["status"] == "FAIL"
    assert "output" in result["stale_active_roots"]


def test_output_root_relocation_receipt_is_hash_bound():
    root = Path(__file__).resolve().parents[1]
    receipt_path = root / "outputs/audits/dashboard/output-root-relocation-20260804.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    recorded = receipt.pop("receipt_sha256")

    assert canonical_sha256(receipt) == recorded
    assert not (root / "output").exists()
    for relocation in receipt["relocations"]:
        target = root / relocation["new_path"]
        assert target.stat().st_size == relocation["bytes"]
        assert hashlib.sha256(target.read_bytes()).hexdigest() == relocation["sha256"]


def test_repository_hygiene_audit_is_hash_bound():
    root = Path(__file__).resolve().parents[1]
    audit_path = root / "outputs/audits/repository/repository-hygiene-a0.10-20260804.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    recorded = audit.pop("audit_sha256")

    assert canonical_sha256(audit) == recorded
    assert audit["status"] == "PASS"
    assert audit["duplicate_audit"]["safe_tracked_source_duplicates_deleted"] == 0
    assert audit["unused_path_cleanup"]["tracked_files_deleted"] == 0
    assert audit["output_root_consolidation"]["source_root_absent"] is True
    assert audit["output_root_consolidation"]["canonical_root_present"] is True
    assert not (root / "output").exists()
    assert (root / "outputs").is_dir()


def test_program_contract_exposes_only_three_owner_decisions():
    payload = yaml.safe_load((Path(__file__).resolve().parents[1] / "control/program.yaml").read_text(encoding="utf-8"))
    assert payload["owner_decisions"] == {
        "standing_authorization": "D1_START_CAMPAIGN",
        "final_access": "D2_OPEN_FINAL",
        "external_release": "D3_SUBMIT_RELEASE",
        "micro_gates": False,
    }


def test_cpu_contract_fetches_history_required_by_projection_lineage():
    root = Path(__file__).resolve().parents[1]
    workflow = yaml.safe_load((root / ".github/workflows/cpu-contract.yml").read_text(encoding="utf-8"))
    checkout = next(
        step
        for step in workflow["jobs"]["contract"]["steps"]
        if step.get("uses") == "actions/checkout@v4"
    )
    assert checkout["with"]["fetch-depth"] == 0

    projection_step = next(
        step
        for step in workflow["jobs"]["contract"]["steps"]
        if step.get("name") == "Validate active layout and projections"
    )
    assert "myis-report check --read-model-only" in projection_step["run"]
    assert "myis-report sync" not in projection_step["run"]
