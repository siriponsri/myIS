"""Create a fresh authenticated A4 D1/provider/budget admission chain."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import subprocess

from myis_research.armindex.a4_execution import (
    build_a4_admission,
    build_d1_continuation_receipt,
)
from myis_research.kernel.canonical import canonical_json, canonical_sha256


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def _vast(instance_id: str) -> dict:
    executable = Path.cwd() / ".venv" / "Scripts" / "python.exe"
    raw = subprocess.run(
        [str(executable), "-c", "from vastai.cli.main import main; main()", "--raw", "show", "instance", instance_id],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    ).stdout
    value = json.loads(raw)
    if value.get("id") != int(instance_id) or value.get("actual_status") != "running" or value.get("verification") != "verified":
        raise RuntimeError("fresh Vast identity is not verified")
    if value.get("num_gpus") != 4 or value.get("gpu_name") != "RTX 3090" or value.get("machine_id") != 134131:
        raise RuntimeError("fresh Vast GPU identity drifted")
    return value


def _runtime_probe(host: str, port: int, key: Path, known_hosts: Path) -> dict:
    command = [
        "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
        "-o", f"UserKnownHostsFile={known_hosts}", "-i", str(key), "-p", str(port),
        f"root@{host}", "python -c 'import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available()); print(torch.cuda.device_count())'",
    ]
    output = subprocess.run(command, check=True, capture_output=True, text=True, timeout=60).stdout.splitlines()
    if len(output) < 4 or output[-4:] != ["2.6.0+cu118", "11.8", "True", "4"]:
        raise RuntimeError("remote runtime probe failed")
    body = {"python": "3.11.11", "torch": output[-4], "cuda": output[-3], "cuda_available": True, "gpu_count": 4}
    return {**body, "runtime_sha256": canonical_sha256(body)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--goal-revision", required=True)
    parser.add_argument("--predecessor-binding", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--known-hosts", type=Path, required=True)
    parser.add_argument("--key", type=Path, required=True)
    args = parser.parse_args()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    provider = _vast("47790578")
    runtime = _runtime_probe(str(provider["public_ipaddr"]), int(provider["ports"]["22/tcp"][0]["HostPort"]), args.key, args.known_hosts)
    observation_body = {
        "schema_version": "myis.armindex-a4-provider-observation.v1",
        "status": "PASS_A4_PROVIDER_IDENTITY",
        "observed_at_utc": now.isoformat().replace("+00:00", "Z"),
        "instance_id": 47790578,
        "machine_id": 134131,
        "provider": "vast",
        "actual_status": provider["actual_status"],
        "verification": provider["verification"],
        "gpu_count": provider["num_gpus"],
        "gpu_model": provider["gpu_name"],
        "gpu_vram_mib_each": provider["gpu_ram"],
        "disk_gib": provider["disk_space"],
        "runtime_sha256": runtime["runtime_sha256"],
        "protected_payload_included": False,
    }
    observation = {**observation_body, "receipt_sha256": canonical_sha256(observation_body)}
    d1 = build_d1_continuation_receipt(
        attempt_id=args.attempt_id,
        predecessor_binding_sha256=json.loads(args.predecessor_binding.read_text(encoding="utf-8"))["binding_sha256"],
        goal_revision=args.goal_revision,
        recorded_at_utc=now,
    )
    admission = build_a4_admission(
        attempt_id=args.attempt_id,
        predecessor=json.loads(args.predecessor_binding.read_text(encoding="utf-8")),
        d1_receipt=d1,
        provider_identity={
            "provider": "vast", "instance_id": 47790578, "machine_id": 134131,
            "status": "running", "gpu_count": 4, "gpu_model": "RTX_3090",
            "ssh_runtime_sha256": runtime["runtime_sha256"],
        },
        observed_at_utc=now,
        now_utc=now,
        all_fee_usd_per_hour=Decimal(str(provider["dph_total"])),
        target_ttl_seconds=48 * 60 * 60,
        ttl_seconds_remaining=None,
        current_campaign_accrued_usd=Decimal("100.68829866666665948"),
        a4_projected_usd=Decimal("30.9866666666666592"),
        a5_reserved_usd=Decimal("31.008"),
        campaign_hard_stop_usd=Decimal("180"),
    )
    root = args.output.resolve()
    _write(root / "provider-observation.json", observation)
    _write(root / "runtime-probe.json", runtime)
    _write(root / "d1-continuation.json", d1)
    _write(root / "all-fee-quote.json", admission["all_fee_quote"])
    _write(root / "budget-admission.json", admission["budget_admission"])
    _write(root / "admission.json", admission["admission"])
    print({"status": admission["admission"]["status"], "attempt_id": args.attempt_id, "admission_sha256": admission["admission"]["admission_sha256"], "quote_usd_per_hour": admission["all_fee_quote"]["all_fee_usd_per_hour"], "campaign_projected_usd": admission["budget_admission"]["campaign_projected_usd"]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
