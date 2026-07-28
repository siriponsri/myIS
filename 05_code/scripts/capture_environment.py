"""Emit the replay-critical local environment as canonical JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from typing import Sequence


ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def command_version(command: Sequence[str]) -> str | None:
    if shutil.which(command[0]) is None:
        return None
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if completed.returncode != 0:
        return None
    return (completed.stdout or completed.stderr).strip() or None


def build_environment(groups: list[str], extras: list[str]) -> dict[str, object]:
    if sys.version_info[:2] != (3, 11):
        raise RuntimeError("measured environments require Python 3.11")
    lock_path = ROOT / "uv.lock"
    project_path = ROOT / "pyproject.toml"
    if not lock_path.is_file():
        raise FileNotFoundError("uv.lock is required before capturing a measured environment")
    if not project_path.is_file():
        raise FileNotFoundError("pyproject.toml is required for dependency authority")
    uv_version = command_version(["uv", "--version"])
    if uv_version is None:
        raise RuntimeError("uv must be available before capturing a measured environment")

    return {
        "schema_version": "myis.environment.v1",
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "executable": str(Path(sys.executable).resolve()),
        },
        "uv_version": uv_version,
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.machine(),
        },
        "accelerator": {
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "nvidia_smi": command_version(
                [
                    "nvidia-smi",
                    "--query-gpu=name,driver_version",
                    "--format=csv,noheader",
                ]
            ),
            "cuda_toolkit": command_version(["nvcc", "--version"]),
        },
        "selected_groups": sorted(set(groups)),
        "selected_extras": sorted(set(extras)),
        "pyproject_sha256": sha256(project_path),
        "uv_lock_sha256": sha256(lock_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", action="append", default=[])
    parser.add_argument("--extra", action="append", default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload = json.dumps(
        build_environment(args.group, args.extra),
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
    ) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8", newline="\n")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
