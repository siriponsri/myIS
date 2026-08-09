"""Single-GPU remote worker for one frozen A1.2 dense arm."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .a1_2_measured_executor_v16 import SentenceTransformerDenseAdapter
from .a1_2_owner_local_measured_runner_v16 import run_owner_local_measured_screen

DENSE_GPU_SLOT = {"ARM-02": "0", "ARM-03": "1", "ARM-04": "2", "ARM-05": "3"}


class RemoteArmWorkerV16Error(RuntimeError):
    """Raised when a remote dense worker is not exactly adopted and isolated."""


def _load(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RemoteArmWorkerV16Error(f"{role} is invalid") from error
    if not isinstance(value, dict):
        raise RemoteArmWorkerV16Error(f"{role} must be an object")
    return value


def _runtime_probe() -> None:
    try:
        import torch
    except ImportError as error:
        raise RemoteArmWorkerV16Error("CUDA runtime is unavailable") from error
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RemoteArmWorkerV16Error("worker must see exactly one CUDA device")
    if torch.cuda.get_device_name(0) != "NVIDIA GeForce RTX 3090":
        raise RemoteArmWorkerV16Error("worker GPU identity drifted")


def run_remote_arm(
    *,
    manifest_path: Path,
    output_root: Path,
    model_root: Path,
    arm_id: str,
    gpu_slot: str,
    adoption_receipt_path: Path,
    runtime_probe: Callable[[], None] = _runtime_probe,
    adapter_factory: Callable[..., Any] = SentenceTransformerDenseAdapter.from_staged_directory,
    runner: Callable[..., dict[str, Any]] = run_owner_local_measured_screen,
) -> dict[str, Any]:
    """Execute exactly five cells for one dense arm on its frozen GPU slot."""

    if DENSE_GPU_SLOT.get(arm_id) != gpu_slot:
        raise RemoteArmWorkerV16Error("arm-to-GPU placement drifted")
    adoption = _load(adoption_receipt_path.resolve(strict=True), role="execution-adoption receipt")
    if (
        adoption.get("status") not in {"PASS", "PASS_EXECUTION_ADOPTION", "PASS_EXECUTION_ADOPTION_LOCKED"}
        or adoption.get("measured_retrieval_allowed") is not True
    ):
        raise RemoteArmWorkerV16Error("execution adoption receipt is not PASS")
    required_environment = {
        "CUDA_VISIBLE_DEVICES": gpu_slot,
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "PIP_NO_INDEX": "1",
    }
    if any(os.environ.get(key) != value for key, value in required_environment.items()):
        raise RemoteArmWorkerV16Error("remote worker environment is not frozen")
    runtime_probe()
    models = model_root.resolve(strict=True)
    model_directory = models / arm_id
    adapter = adapter_factory(
        arm_id=arm_id,
        model_directory=model_directory,
        device="cuda:0",
        batch_size=1,
    )
    result = runner(
        manifest_path,
        output_root=output_root,
        adapters={arm_id: adapter},
        arm_ids=(arm_id,),
    )
    if result.get("status") != "PASS" or result.get("cells") != 5:
        raise RemoteArmWorkerV16Error("remote arm did not complete five cells")
    return {
        "status": "PASS",
        "attempt_id": result["attempt_id"],
        "arm_id": arm_id,
        "gpu_slot": gpu_slot,
        "cells": 5,
        "work_tokens": 150,
        "top_k": 100,
        "receipt_sha256": result["receipt_sha256"],
        "measured_retrieval": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-remote-arm-worker-v16")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--arm-id", choices=tuple(DENSE_GPU_SLOT), required=True)
    parser.add_argument("--gpu-slot", choices=("0", "1", "2", "3"), required=True)
    parser.add_argument("--adoption-receipt", type=Path, required=True)
    args = parser.parse_args()
    result = run_remote_arm(
        manifest_path=args.manifest,
        output_root=args.output_root,
        model_root=args.model_root,
        arm_id=args.arm_id,
        gpu_slot=args.gpu_slot,
        adoption_receipt_path=args.adoption_receipt,
    )
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
