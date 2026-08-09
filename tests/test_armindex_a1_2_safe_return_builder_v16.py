from __future__ import annotations

import hashlib
import json
from pathlib import Path

from myis_research.armindex.a1_2_safe_return_builder_v16 import (
    build_safe_return_archive,
)
from myis_research.armindex.a1_2_safe_return_v16 import (
    ARM_IDS,
    PROGRAM_IDS,
    validate_safe_return_archive,
)


def _ranking(work_tokens: list[str]) -> str:
    rows = []
    families = [f"F-{index:032x}" for index in range(100)]
    for token in work_tokens:
        rows.append(json.dumps({"work_token": token, "family_tokens": families}, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return "\n".join(rows) + "\n"


def test_builder_emits_exact_validated_archive(tmp_path: Path) -> None:
    attempt = "a12-v16-builder-test"
    runner = tmp_path / "runner"
    attempt_root = runner / attempt
    (attempt_root / "rankings").mkdir(parents=True)
    (attempt_root / "receipts").mkdir()
    work_tokens = [f"Q-{index:032x}" for index in range(150)]
    checkpoints: dict[str, str] = {}
    for arm in ARM_IDS:
        for program in PROGRAM_IDS:
            cell = f"{arm}--{program}"
            payload = _ranking(work_tokens)
            (attempt_root / "rankings" / f"{cell}.jsonl").write_text(payload, encoding="ascii", newline="")
            ranking_sha = hashlib.sha256(payload.encode("ascii")).hexdigest()
            (attempt_root / "receipts" / f"{cell}.json").write_text(json.dumps({"cell_id": cell, "status": "PASS", "ranking_file_sha256": ranking_sha}, sort_keys=True), encoding="ascii")
            checkpoints[cell] = "a" * 64
    archive = tmp_path / "return.tar.gz"
    result = build_safe_return_archive(runner_output_root=runner, attempt_id=attempt, archive_path=archive, transfer_manifest_sha256="b" * 64, split_commitment_sha256="c" * 64, ephemeral_token_map_sha256="d" * 64, checkpoint_sha256_by_cell=checkpoints)
    assert result["status"] == "PASS"
    assert validate_safe_return_archive(archive)["cells"] == 25


def test_builder_rejects_incomplete_checkpoint_map(tmp_path: Path) -> None:
    try:
        build_safe_return_archive(runner_output_root=tmp_path, attempt_id="a12-v16-builder-test", archive_path=tmp_path / "x.tar.gz", transfer_manifest_sha256="a" * 64, split_commitment_sha256="b" * 64, ephemeral_token_map_sha256="c" * 64, checkpoint_sha256_by_cell={})
    except ValueError as error:
        assert "checkpoint map" in str(error)
    else:
        raise AssertionError("incomplete checkpoint map must fail closed")
