from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_owner_local_input_manifest_v16 import (
    ARM_IDS,
    PROGRAM_IDS,
    OwnerLocalInputManifestV16Error,
    build_input_manifest,
)


def _cells(root: Path) -> list[dict[str, str]]:
    result = []
    for arm in ARM_IDS:
        for program in PROGRAM_IDS:
            cell = f"{arm}--{program}"
            directory = root / "cells" / cell
            directory.mkdir(parents=True)
            for name, payload in (("binding.json", {"cell": cell}), ("corpus.jsonl", {"family_token": "F-" + "0" * 32, "text": "x"}), ("query.jsonl", {"work_token": "Q-" + "0" * 32, "text": "x"})):
                (directory / name).write_text(json.dumps(payload) + "\n", encoding="ascii")
            result.append({"cell_id": cell, "arm_id": arm, "program_id": program, "binding_path": f"cells/{cell}/binding.json", "corpus_path": f"cells/{cell}/corpus.jsonl", "query_path": f"cells/{cell}/query.jsonl"})
    return result


def test_input_manifest_binds_exact_25_cells(tmp_path: Path) -> None:
    work = tmp_path / "work_tokens.jsonl"
    work.write_text("\n".join(json.dumps({"work_token": f"Q-{index:032x}"}) for index in range(150)) + "\n", encoding="ascii")
    result = build_input_manifest(root=tmp_path, output=tmp_path / "manifest.json", attempt_id="a12-v16-input-test", gates={name: "PASS" for name in ("provider_admission", "execution_adoption", "watchdog_ttl", "protected_boundary", "frozen_bindings")}, work_token_path="work_tokens.jsonl", cells=_cells(tmp_path))
    assert result["cells"] == 25
    assert result["work_token_count"] == 150


def test_input_manifest_rejects_gate_drift(tmp_path: Path) -> None:
    with pytest.raises(OwnerLocalInputManifestV16Error, match="gates"):
        build_input_manifest(root=tmp_path, output=tmp_path / "manifest.json", attempt_id="a12-v16-input-test", gates={}, work_token_path="missing.jsonl", cells=[])
