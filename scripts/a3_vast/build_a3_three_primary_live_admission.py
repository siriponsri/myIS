"""Write fresh, aggregate-safe A3 three-primary live-admission receipts."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from myis_research.armindex.a3_three_primary_admission import (
    A3ThreePrimaryAdmissionError,
    build_three_primary_live_admission,
)
from myis_research.kernel.canonical import canonical_sha256


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise A3ThreePrimaryAdmissionError(f"{path.name} is not valid JSON") from error
    if not isinstance(value, dict):
        raise A3ThreePrimaryAdmissionError(f"{path.name} must be a JSON object")
    return value


def _utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise argparse.ArgumentTypeError("timestamp must be ISO-8601 with a timezone") from error
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(prog="build-a3-three-primary-live-admission")
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--observed-at-utc", type=_utc, required=True)
    parser.add_argument("--now-utc", type=_utc, required=True)
    parser.add_argument("--instance-id", type=int, required=True)
    parser.add_argument("--machine-id", type=int, required=True)
    parser.add_argument("--all-fee-usd-per-hour", required=True)
    parser.add_argument("--a1-actual-usd", default="11.161632")
    parser.add_argument("--extra-a3-contingency-usd", default="0")
    parser.add_argument("--ssh-runtime-json", type=Path, required=True)
    args = parser.parse_args()

    root = args.repository_root.resolve()
    output = args.output_root.resolve()
    runtime = _load(args.ssh_runtime_json.resolve())
    runtime_sha256 = canonical_sha256(runtime)
    try:
        receipts = build_three_primary_live_admission(
            budget=_load(root / "control/budgets/armindex-budget-extension-a3-three-primary.v1.json"),
            authority=_load(root / "control/armindex/a3/a3-three-primary-preparation-authority.v1.json"),
            manifest=_load(root / "control/armindex/a3/a3-three-primary-preparation-manifest.v1.json"),
            provider_identity={
                "provider": "vast",
                "instance_id": args.instance_id,
                "machine_id": args.machine_id,
                "status": "running",
                "gpu_count": 4,
                "gpu_model": "RTX_3090",
                "ssh_runtime_sha256": runtime_sha256,
            },
            observed_at_utc=args.observed_at_utc,
            all_fee_usd_per_hour=args.all_fee_usd_per_hour,
            a1_actual_usd=args.a1_actual_usd,
            extra_a3_contingency_usd=args.extra_a3_contingency_usd,
            now_utc=args.now_utc,
        )
    except A3ThreePrimaryAdmissionError as error:
        parser.error(str(error))
    output.mkdir(parents=True, exist_ok=False)
    for name, receipt in receipts.items():
        _write_json(output / f"{name}.v1.json", receipt)
    print(
        json.dumps(
            {
                "status": "PASS_A3_FRESH_ADMISSION",
                "output_root": str(output),
                "admission_sha256": receipts["admission"]["admission_sha256"],
            },
            ensure_ascii=True,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
