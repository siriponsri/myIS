from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_remote_arm_worker_v16 import (
    RemoteArmWorkerV16Error,
    run_remote_arm,
)


def _adoption(path: Path, *, allowed: bool = True) -> Path:
    path.write_text(
        json.dumps(
            {
                "status": "PASS_EXECUTION_ADOPTION",
                "measured_retrieval_allowed": allowed,
            }
        ),
        encoding="ascii",
    )
    return path


def test_remote_worker_enforces_one_arm_one_gpu(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for key, value in {
        "CUDA_VISIBLE_DEVICES": "2",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "PIP_NO_INDEX": "1",
    }.items():
        monkeypatch.setenv(key, value)
    model_root = tmp_path / "models"
    (model_root / "ARM-04").mkdir(parents=True)
    calls: list[object] = []

    def adapter_factory(**kwargs: object) -> object:
        calls.append(kwargs)
        return object()

    def runner(manifest: Path, **kwargs: object) -> dict[str, object]:
        calls.append((manifest, kwargs))
        return {
            "status": "PASS",
            "attempt_id": "a12-v16-test",
            "cells": 5,
            "receipt_sha256": "a" * 64,
        }

    result = run_remote_arm(
        manifest_path=tmp_path / "manifest.json",
        output_root=tmp_path / "output",
        model_root=model_root,
        arm_id="ARM-04",
        gpu_slot="2",
        adoption_receipt_path=_adoption(tmp_path / "adoption.json"),
        runtime_probe=lambda: None,
        adapter_factory=adapter_factory,
        runner=runner,
    )
    assert result["status"] == "PASS" and result["cells"] == 5
    assert calls[0]["device"] == "cuda:0"  # type: ignore[index]
    assert calls[1][1]["arm_ids"] == ("ARM-04",)  # type: ignore[index]


def test_remote_worker_rejects_slot_or_adoption_drift(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0")
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    monkeypatch.setenv("PIP_NO_INDEX", "1")
    with pytest.raises(RemoteArmWorkerV16Error, match="placement"):
        run_remote_arm(
            manifest_path=tmp_path / "manifest.json",
            output_root=tmp_path / "output",
            model_root=tmp_path,
            arm_id="ARM-03",
            gpu_slot="0",
            adoption_receipt_path=_adoption(tmp_path / "adoption.json"),
        )
