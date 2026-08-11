"""Show operator-only tqdm progress for A1.2 transfer or remote cells."""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import time
from pathlib import Path

from tqdm import tqdm

_REMOTE_ROOT = re.compile(r"^/opt/myis/[A-Za-z0-9._/-]+$")


def _remote_value(args: argparse.Namespace) -> int:
    root = shlex.quote(args.remote_root)
    if args.mode == "transfer":
        command = f"du -sb {root} 2>/dev/null | cut -f1 || printf 0"
    else:
        command = (
            f"find {root} -path '*/receipts/ARM-??--P*.json' -type f 2>/dev/null "
            "| wc -l"
        )
    result = subprocess.run(
        [
            "ssh",
            "-i",
            str(args.ssh_key.resolve()),
            "-p",
            str(args.ssh_port),
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            f"UserKnownHostsFile={args.known_hosts.resolve()}",
            f"root@{args.ssh_host}",
            command,
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(f"SSH progress probe failed with exit code {result.returncode}")
    value = result.stdout.strip().splitlines()[0]
    return int(value)


def main() -> int:
    parser = argparse.ArgumentParser(prog="Watch-A12ProgressV16")
    parser.add_argument("--mode", choices=("transfer", "cells"), required=True)
    parser.add_argument("--ssh-host", required=True)
    parser.add_argument("--ssh-port", type=int, required=True)
    parser.add_argument("--ssh-key", type=Path, required=True)
    parser.add_argument("--known-hosts", type=Path, required=True)
    parser.add_argument("--remote-root", required=True)
    parser.add_argument("--total", type=int, required=True)
    parser.add_argument("--poll-seconds", type=float, default=15.0)
    parser.add_argument("--timeout-seconds", type=float, default=14_400.0)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    if (
        _REMOTE_ROOT.fullmatch(args.remote_root) is None
        or not 1 <= args.ssh_port <= 65_535
        or not args.ssh_key.is_file()
        or not args.known_hosts.is_file()
        or args.total <= 0
        or args.poll_seconds <= 0
        or args.timeout_seconds <= 0
    ):
        parser.error("invalid progress-monitor input")

    unit = "B" if args.mode == "transfer" else "cell"
    description = "A1.2 stage" if args.mode == "transfer" else "A1.2 remote"
    deadline = time.monotonic() + args.timeout_seconds
    with tqdm(
        total=args.total,
        unit=unit,
        unit_scale=args.mode == "transfer",
        desc=description,
        dynamic_ncols=True,
    ) as progress:
        while True:
            observed = min(_remote_value(args), args.total)
            progress.update(observed - progress.n)
            progress.refresh()
            if observed >= args.total or args.once:
                return 0
            if time.monotonic() >= deadline:
                raise TimeoutError("A1.2 progress monitor timed out")
            time.sleep(args.poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
