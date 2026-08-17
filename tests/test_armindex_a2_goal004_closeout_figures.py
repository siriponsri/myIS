from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from myis_research.armindex.a2_goal004_closeout_figures import (
    A2Goal004CloseoutFigureError,
    render_a2_goal004_closeout_figures,
    validate_a2_goal004_closeout_projection,
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_closeout_projection_validates_and_has_complete_accounting() -> None:
    projection = validate_a2_goal004_closeout_projection(REPOSITORY_ROOT)
    assert projection["accounting"] == {
        "candidate_count": 52,
        "matched_candidate_count": 40,
        "measured_candidate_count": 44,
        "activated_reserve_candidate_count": 4,
        "dormant_reserve_candidate_count": 8,
        "failed_candidate_count": 0,
        "workers_reaped": True,
    }
    assert [row["arm_id"] for row in projection["arm_outcomes"]] == [
        "ARM-01",
        "ARM-02",
        "ARM-03",
        "ARM-04",
        "ARM-05",
    ]


def test_closeout_projection_rejects_tampered_hash(tmp_path: Path) -> None:
    source = REPOSITORY_ROOT / "control/armindex/a2/a2-goal004-closeout-projection.v1.json"
    target = tmp_path / "control/armindex/a2/a2-goal004-closeout-projection.v1.json"
    target.parent.mkdir(parents=True)
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["budget"]["whole_workload_total_usd"] = "59.0"
    target.write_text(json.dumps(payload), encoding="utf-8")
    schema_source = REPOSITORY_ROOT / "schemas/armindex/a2-goal004-closeout-projection.v1.json"
    schema_target = tmp_path / "schemas/armindex/a2-goal004-closeout-projection.v1.json"
    schema_target.parent.mkdir(parents=True)
    schema_target.write_text(schema_source.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(A2Goal004CloseoutFigureError, match="self-hash"):
        validate_a2_goal004_closeout_projection(tmp_path)


def test_closeout_projection_rejects_source_artifact_hash_mismatch(
    tmp_path: Path,
) -> None:
    source = REPOSITORY_ROOT / "control/armindex/a2/a2-goal004-closeout-projection.v1.json"
    target = tmp_path / "control/armindex/a2/a2-goal004-closeout-projection.v1.json"
    target.parent.mkdir(parents=True)
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["source_artifacts"]["result_integrity_audit"]["file_sha256"] = "0" * 64
    unsigned = {key: value for key, value in payload.items() if key != "projection_sha256"}
    from myis_research.kernel.canonical import canonical_sha256

    payload["projection_sha256"] = canonical_sha256(unsigned)
    target.write_text(json.dumps(payload), encoding="utf-8")
    schema_source = REPOSITORY_ROOT / "schemas/armindex/a2-goal004-closeout-projection.v1.json"
    schema_target = tmp_path / "schemas/armindex/a2-goal004-closeout-projection.v1.json"
    schema_target.parent.mkdir(parents=True)
    schema_target.write_text(schema_source.read_text(encoding="utf-8"), encoding="utf-8")
    owner_store = tmp_path.parent / "04_Owner_Stores"
    for artifact in payload["source_artifacts"].values():
        relative = artifact["uri"].removeprefix("owner-store://")
        source_path = REPOSITORY_ROOT.parent / "04_Owner_Stores" / relative
        target_path = owner_store / relative
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, target_path)
    with pytest.raises(
        A2Goal004CloseoutFigureError,
        match="result_integrity_audit source file hash does not match",
    ):
        validate_a2_goal004_closeout_projection(tmp_path)


def test_closeout_figure_renderer_writes_five_families(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(REPOSITORY_ROOT)
    output = REPOSITORY_ROOT / "outputs/figures/armindex/a2-goal004"
    prior = {path.name: path.read_bytes() for path in output.glob("*")} if output.exists() else {}
    try:
        result = render_a2_goal004_closeout_figures(REPOSITORY_ROOT)
        assert len(result["manifest"]["figures"]) == 5
        for row in result["manifest"]["figures"]:
            assert set(row["artifacts"]) == {"png", "svg", "pdf"}
    finally:
        if output.exists():
            for path in output.glob("*"):
                path.unlink()
            output.rmdir()
        if prior:
            output.mkdir(parents=True)
            for name, contents in prior.items():
                (output / name).write_bytes(contents)
