"""Synthetic-only A1.2 live GPU preflight helpers.

The module loads only Owner-staged, hash-validated model bytes. It never reads
benchmark queries, qrels, split membership, or evaluator data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from ..kernel.canonical import canonical_sha256, file_sha256


ARMS = ("ARM-02", "ARM-03", "ARM-04", "ARM-05")
EXPECTED_DIMENSIONS = {"ARM-02": 1024, "ARM-03": 1024, "ARM-04": 768, "ARM-05": 1024}
MAX_INPUT_TOKENS = {"ARM-02": 8192, "ARM-03": 512, "ARM-04": 8192, "ARM-05": 32768}
QUERY_FORMATS = {
    "ARM-02": "{query}",
    "ARM-03": "encode query for different document retrieval: {query}",
    "ARM-04": "query: {query}",
    "ARM-05": (
        "Instruct: Retrieve patent families containing technical information relevant "
        "to prior-art search for the query patent family.\nQuery:{query}"
    ),
}
DOCUMENT_FORMATS = {
    "ARM-02": "{document}",
    "ARM-03": "encode document for different retrieval: {document}",
    "ARM-04": "{document}",
    "ARM-05": "{document}",
}


class LivePreflightError(ValueError):
    """Raised when a live synthetic preflight invariant fails."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _write_receipt(path: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(payload)
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"live preflight receipt already exists: {path}")
    path.write_text(_json_text(receipt), encoding="utf-8", newline="")
    return receipt


def _gpu_rows() -> list[dict[str, Any]]:
    completed = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=index,uuid,name,memory.total",
            "--format=csv,noheader,nounits",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    rows = []
    for line in completed.stdout.splitlines():
        index, uuid, name, memory_mib = [part.strip() for part in line.split(",", 3)]
        rows.append(
            {"index": int(index), "uuid": uuid, "name": name, "memory_mib": int(memory_mib)}
        )
    return rows


def write_runtime_identity(
    *,
    remote_root: Path,
    output_path: Path,
    expected_manifest_digest: str,
    image_observation_mode: str,
    bundle_sha256: str,
) -> dict[str, Any]:
    import torch

    gpus = _gpu_rows()
    disk = shutil.disk_usage(remote_root)
    ram_bytes = 0
    meminfo = Path("/proc/meminfo")
    if meminfo.is_file():
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                ram_bytes = int(line.split()[1]) * 1024
                break
    blockers = []
    if platform.machine() != "x86_64":
        blockers.append("platform")
    if not platform.python_version().startswith("3.11."):
        blockers.append("python")
    if torch.__version__ != "2.6.0+cu118" or torch.version.cuda != "11.8":
        blockers.append("torch_cuda_runtime")
    if not torch.cuda.is_available():
        blockers.append("cuda_unavailable")
    if len(gpus) != 4 or len({row["uuid"] for row in gpus}) != 4:
        blockers.append("gpu_uuid_count")
    if any(row["name"] != "NVIDIA GeForce RTX 3090" or row["memory_mib"] < 24500 for row in gpus):
        blockers.append("gpu_model_vram")
    if (os.cpu_count() or 0) < 16 or ram_bytes < 64 * 1024**3:
        blockers.append("cpu_ram")
    # A 250-GiB provider volume loses a small amount to filesystem metadata and
    # holds the staged 6.12-GB model set before this check runs.
    if disk.total < 249 * 1024**3 or disk.free < 230 * 1024**3:
        blockers.append("disk_capacity_or_post_stage_free_space")
    if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("TRANSFORMERS_OFFLINE") != "1":
        blockers.append("offline_environment")
    payload = {
        "schema_version": "myis.armindex-a1.2-live-runtime-identity.v6",
        "status": "PASS" if not blockers else "BLOCKED_PREFLIGHT",
        "blockers": blockers,
        "platform": "linux/amd64" if platform.machine() == "x86_64" else platform.machine(),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "gpus": gpus,
        "gpu_uuid_set_sha256": canonical_sha256(sorted(row["uuid"] for row in gpus)),
        "cpu_count": os.cpu_count(),
        "ram_bytes": ram_bytes,
        "disk_total_bytes": disk.total,
        "disk_free_bytes_after_staging": disk.free,
        "expected_manifest_digest": expected_manifest_digest,
        "image_observation_mode": image_observation_mode,
        "manifest_digest_observed_inside_container": image_observation_mode == "docker_repo_digest",
        "bundle_sha256": bundle_sha256,
        "network_model_download_allowed": False,
        "measured_retrieval": False,
        "generated_at": _utc_now(),
    }
    receipt = _write_receipt(output_path, payload)
    if blockers:
        raise LivePreflightError(f"runtime identity blockers: {', '.join(blockers)}")
    return receipt


def _synthetic_texts(arm_id: str) -> tuple[str, str]:
    query = "cooling a power converter using a thermally conductive housing"
    document = "A synthetic enclosure transfers heat from switching components to an external sink."
    return (
        QUERY_FORMATS[arm_id].format(query=query),
        DOCUMENT_FORMATS[arm_id].format(document=document),
    )


def _pooling_config(model_directory: Path) -> dict[str, Any]:
    path = model_directory / "1_Pooling" / "config.json"
    if not path.is_file():
        raise LivePreflightError("SentenceTransformer pooling config is missing")
    value = json.loads(path.read_text(encoding="utf-8"))
    return {
        "sha256": file_sha256(path),
        "mean_tokens": bool(value.get("pooling_mode_mean_tokens")),
        "cls_token": bool(value.get("pooling_mode_cls_token")),
        "last_token": bool(value.get("pooling_mode_lasttoken")),
    }


def _measure_qwen_maximum(model: Any) -> tuple[int, list[dict[str, Any]]]:
    import torch

    transformer = model._first_module()  # noqa: SLF001 - SentenceTransformer public module graph
    tokenizer = transformer.tokenizer
    auto_model = transformer.auto_model
    token_ids = tokenizer.encode(" synthetic", add_special_tokens=False)
    if not token_ids:
        raise LivePreflightError("Qwen tokenizer produced no synthetic token")
    token_id = int(token_ids[0])
    measured = 0
    attempts: list[dict[str, Any]] = []
    for length in (8192, 16384, 32768):
        torch.cuda.empty_cache()
        try:
            input_ids = torch.full((1, length), token_id, dtype=torch.long, device="cuda")
            attention_mask = torch.ones_like(input_ids)
            with torch.inference_mode(), torch.autocast(device_type="cuda", dtype=torch.float16):
                output = auto_model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    use_cache=False,
                    return_dict=True,
                )
                finite = bool(torch.isfinite(output.last_hidden_state[:, -1, :]).all().item())
            if not finite:
                raise LivePreflightError("Qwen maximum-length output was non-finite")
            measured = length
            attempts.append({"tokens": length, "status": "PASS"})
            del output, input_ids, attention_mask
        except torch.cuda.OutOfMemoryError:
            attempts.append({"tokens": length, "status": "OOM"})
            torch.cuda.empty_cache()
            break
    return measured, attempts


def run_adapter_check(*, arm_id: str, model_root: Path, output_path: Path) -> dict[str, Any]:
    if arm_id not in ARMS:
        raise LivePreflightError(f"unsupported arm: {arm_id}")
    if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("TRANSFORMERS_OFFLINE") != "1":
        raise LivePreflightError("offline environment is not enforced")
    observed_slot = os.environ.get("CUDA_VISIBLE_DEVICES")
    expected_slot = str(ARMS.index(arm_id))
    if observed_slot != expected_slot:
        raise LivePreflightError(f"{arm_id} CUDA mapping mismatch")

    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer

    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise LivePreflightError(f"{arm_id} must see exactly one CUDA device")
    directory = (model_root / arm_id).resolve()
    manifest = json.loads((directory / "runtime-file-manifest.v4.json").read_text(encoding="utf-8"))
    query, document = _synthetic_texts(arm_id)
    torch.manual_seed(20260807)
    torch.cuda.manual_seed_all(20260807)
    torch.cuda.reset_peak_memory_stats()
    model = SentenceTransformer(
        str(directory),
        device="cuda",
        trust_remote_code=arm_id == "ARM-04",
        local_files_only=True,
        model_kwargs={"torch_dtype": torch.float16},
    )
    model.max_seq_length = MAX_INPUT_TOKENS[arm_id]
    first = model.encode(
        [query, document],
        batch_size=2,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    repeated = model.encode(
        [query, document],
        batch_size=2,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    finite = bool(np.isfinite(first).all())
    deterministic = bool(np.allclose(first, repeated, rtol=0.0, atol=1e-6))
    norms = np.linalg.norm(first, axis=1)
    normalized = bool(np.allclose(norms, np.ones_like(norms), rtol=0.0, atol=1e-4))
    dimension = int(first.shape[1]) if first.ndim == 2 else 0
    if not finite or not deterministic or not normalized or dimension != EXPECTED_DIMENSIONS[arm_id]:
        raise LivePreflightError(f"{arm_id} adapter parity invariant failed")
    qwen_maximum = None
    qwen_attempts: list[dict[str, Any]] = []
    if arm_id == "ARM-05":
        qwen_maximum, qwen_attempts = _measure_qwen_maximum(model)
        if qwen_maximum <= 0:
            raise LivePreflightError("Qwen did not pass the minimum 8192-token live check")
    gpus = _gpu_rows()
    physical = gpus[int(expected_slot)]
    payload = {
        "schema_version": "myis.armindex-a1.2-live-adapter-parity.v6",
        "arm_id": arm_id,
        "status": "PASS",
        "cuda_visible_devices": observed_slot,
        "visible_gpu_count": torch.cuda.device_count(),
        "physical_gpu_uuid": physical["uuid"],
        "physical_gpu_name": physical["name"],
        "model_manifest_sha256": manifest.get("manifest_sha256"),
        "pooling_config": _pooling_config(directory),
        "query_format_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
        "document_format_sha256": hashlib.sha256(document.encode("utf-8")).hexdigest(),
        "output_dimension": dimension,
        "finite_embeddings": finite,
        "l2_normalized": normalized,
        "repeat_deterministic_atol": 1e-6,
        "repeat_deterministic": deterministic,
        "torch_dtype": "float16",
        "peak_vram_bytes": int(torch.cuda.max_memory_allocated()),
        "qwen_measured_max_input_tokens": qwen_maximum,
        "qwen_length_attempts": qwen_attempts,
        "trust_remote_code": arm_id == "ARM-04",
        "local_files_only": True,
        "network_fallback": False,
        "synthetic_text_only": True,
        "measured_retrieval": False,
        "scientific_authority": False,
        "generated_at": _utc_now(),
    }
    return _write_receipt(output_path, payload)


def summarize_preflight(*, output_root: Path, output_path: Path) -> dict[str, Any]:
    identity_path = output_root / "preflight" / "runtime-identity.json"
    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    adapters = []
    runtimes = []
    for arm in ARMS:
        adapter_path = output_root / "preflight" / "adapters" / f"{arm}.json"
        runtime_path = output_root / "runtime-receipts" / f"{arm}.json"
        adapters.append(json.loads(adapter_path.read_text(encoding="utf-8")))
        runtimes.append(json.loads(runtime_path.read_text(encoding="utf-8")))
    failure_path = output_root / "failure-receipts" / "ARM-02.json"
    blockers = []
    if identity.get("status") != "PASS":
        blockers.append("runtime_identity")
    if any(item.get("status") != "PASS" for item in adapters):
        blockers.append("adapter_parity")
    if any(item.get("status") != "synthetic_preflight_passed" for item in runtimes):
        blockers.append("synthetic_workers")
    if not failure_path.is_file() or not any(
        item.get("arm_id") == "ARM-02" and item.get("resumed_from_checkpoint") is True
        for item in runtimes
    ):
        blockers.append("checkpoint_resume")
    qwen = next(item for item in adapters if item["arm_id"] == "ARM-05")
    payload = {
        "schema_version": "myis.armindex-a1.2-live-preflight-summary.v6",
        "status": "PASS" if not blockers else "BLOCKED_PREFLIGHT",
        "blockers": blockers,
        "runtime_identity_sha256": file_sha256(identity_path),
        "adapter_receipt_sha256s": {
            arm: file_sha256(output_root / "preflight" / "adapters" / f"{arm}.json") for arm in ARMS
        },
        "runtime_receipt_sha256s": {
            arm: file_sha256(output_root / "runtime-receipts" / f"{arm}.json") for arm in ARMS
        },
        "dense_adapter_parity": not blockers or "adapter_parity" not in blockers,
        "qwen_measured_max_input_tokens": qwen.get("qwen_measured_max_input_tokens"),
        "four_worker_heartbeat_count": sum(
            (output_root / "heartbeats" / f"{arm}.json").is_file() for arm in ARMS
        ),
        "checkpoint_resume_passed": "checkpoint_resume" not in blockers,
        "synthetic_workers_only": True,
        "measured_retrieval": False,
        "launch_allowed": False,
        "adopted_for_execution": False,
        "generated_at": _utc_now(),
    }
    receipt = _write_receipt(output_path, payload)
    if blockers:
        raise LivePreflightError(f"live preflight blockers: {', '.join(blockers)}")
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myis-a1.2-live-preflight")
    sub = parser.add_subparsers(dest="command", required=True)
    identity = sub.add_parser("runtime-identity")
    identity.add_argument("--remote-root", type=Path, required=True)
    identity.add_argument("--output", type=Path, required=True)
    identity.add_argument("--expected-manifest-digest", required=True)
    identity.add_argument("--image-observation-mode", required=True)
    identity.add_argument("--bundle-sha256", required=True)
    adapter = sub.add_parser("adapter-check")
    adapter.add_argument("--arm", choices=ARMS, required=True)
    adapter.add_argument("--model-root", type=Path, required=True)
    adapter.add_argument("--output", type=Path, required=True)
    summary = sub.add_parser("summarize")
    summary.add_argument("--output-root", type=Path, required=True)
    summary.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "runtime-identity":
        result = write_runtime_identity(
            remote_root=args.remote_root,
            output_path=args.output,
            expected_manifest_digest=args.expected_manifest_digest,
            image_observation_mode=args.image_observation_mode,
            bundle_sha256=args.bundle_sha256,
        )
    elif args.command == "adapter-check":
        result = run_adapter_check(arm_id=args.arm, model_root=args.model_root, output_path=args.output)
    else:
        result = summarize_preflight(output_root=args.output_root, output_path=args.output)
    print(_json_text(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
