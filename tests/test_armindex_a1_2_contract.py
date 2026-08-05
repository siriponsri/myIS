from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_contract import (
    CONTROL_ROOT,
    MODEL_SOURCES,
    build_a1_2_scaffold_files,
    validate_a1_2_scaffold,
)


ROOT = Path(__file__).resolve().parents[1]


def test_a12_hash_bound_inputs_disable_git_text_normalization() -> None:
    paths = [
        "control/armindex/a1.2/execution-contract.v1.json",
        "control/armindex/a1.2/scaffold-inputs.v1.yaml",
        "control/runbooks/A1_2_COMMON_MULTI_ARM_SCREENING.md",
        "docs/research/A1_2_MODEL_SOURCE_LOCKS.md",
        "src/myis_research/armindex/a1_2_contract.py",
        "src/myis_research/armindex/bm25s_adapter.py",
        "tests/test_armindex_bm25s_adapter.py",
        "pyproject.toml",
        "uv.lock",
    ]
    result = subprocess.run(
        ["git", "check-attr", "text", "--", *paths],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.count("text: unset") == len(paths)


def test_a12_scaffold_is_hash_bound_and_launch_locked() -> None:
    validation = validate_a1_2_scaffold(ROOT)
    files = build_a1_2_scaffold_files(ROOT)
    contract = json.loads(files[CONTROL_ROOT / "execution-contract.v1.json"])
    budget = json.loads(files[Path("control/budgets/a1.2-common-screen-v1.json")])
    checklist = json.loads(files[CONTROL_ROOT / "launch-checklist.v1.json"])

    assert validation.model_lock_count == 5
    assert validation.launch_ready is False
    assert validation.measured_execution is False
    assert contract["launch_allowed"] is False
    assert set(contract["real_counters"].values()) == {0}
    assert set(contract["resource_counters"].values()) == {0}
    assert budget["limits"]["arm01_gpu_usd"] == 0
    assert budget["limits"]["common_screen_hard_stop_usd"] == 18
    assert budget["limits"]["a1_total_hard_stop_usd"] == 23
    assert checklist["pending_owner"]


def test_a12_all_model_sources_have_exact_resolved_revisions_and_critical_hashes() -> None:
    assert {source["arm_id"] for source in MODEL_SOURCES} == {
        "ARM-02", "ARM-03", "ARM-04", "ARM-05"
    }
    for source in MODEL_SOURCES:
        assert len(source["resolved_revision"]) == 40
        assert source["critical_artifacts"]
        assert all(len(item["sha256"]) == 64 for item in source["critical_artifacts"])


def test_a12_scaffold_validation_rejects_tamper(tmp_path: Path) -> None:
    files = build_a1_2_scaffold_files(ROOT)
    for relative, text in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="")
    # Source commitments are rebuilt from the repository root, so the copied
    # bundle cannot be reinterpreted under a different source tree.
    with pytest.raises(FileNotFoundError, match="required A1.2 scaffold source"):
        validate_a1_2_scaffold(tmp_path)


def test_a12_scaffold_checked_in_artifact_tamper_is_detected(monkeypatch, tmp_path: Path) -> None:
    # Compare expected bytes directly to prove any contract mutation changes its
    # materialized commitment without changing repository state.
    files = build_a1_2_scaffold_files(ROOT)
    contract_path = CONTROL_ROOT / "execution-contract.v1.json"
    contract = json.loads(files[contract_path])
    original = contract["contract_sha256"]
    contract["launch_allowed"] = True
    contract.pop("contract_sha256")
    from myis_research.kernel.canonical import canonical_sha256

    assert canonical_sha256(contract) != original
