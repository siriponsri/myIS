"""Stage or launch one aggregate-safe A3 three-primary remote unit.

All file arguments are Owner-local.  Receipt files must be written to an
Owner Store path; this utility emits no worker output, ranking, qrel, or
membership data.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from myis_research.armindex.a3_three_primary_remote_launcher import (
    collect_a3_remote_ranking_package,
    launch_a3_remote_operation,
    stage_a3_remote_runtime,
)
from myis_research.protection import assert_aggregate_only


def _load(path: Path, *, role: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{role} is not a regular file")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{role} must be a JSON object")
    return value


def _write_new(path: Path, value: dict[str, Any]) -> None:
    assert_aggregate_only(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise ValueError("receipt destination already exists")
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        json.dump(value, handle, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        handle.write("\n")
        temporary = Path(handle.name)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--ssh-host", required=True)
    parser.add_argument("--ssh-port", required=True, type=int)
    parser.add_argument("--ssh-key", required=True, type=Path)
    parser.add_argument("--known-hosts", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a3-three-primary-remote-lifecycle")
    commands = parser.add_subparsers(dest="command", required=True)
    stage = commands.add_parser("stage")
    _common(stage)
    stage.add_argument("--stage-manifest", required=True, type=Path)
    stage.add_argument("--code-bundle", required=True, type=Path)
    stage.add_argument("--runtime-assets-archive", required=True, type=Path)
    stage.add_argument("--runtime-assets-inventory", required=True, type=Path)
    launch = commands.add_parser("launch")
    _common(launch)
    launch.add_argument("--stage-receipt", required=True, type=Path)
    launch.add_argument("--request", required=True, type=Path)
    launch.add_argument("--request-manifest", required=True, type=Path)
    launch.add_argument("--remote-python", required=True)
    collect = commands.add_parser("collect")
    _common(collect)
    collect.add_argument("--stage-receipt", required=True, type=Path)
    collect.add_argument("--launch-receipt", required=True, type=Path)
    collect.add_argument("--request", required=True, type=Path)
    collect.add_argument("--owner-local-output", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "stage":
        result = stage_a3_remote_runtime(
            _load(args.stage_manifest, role="stage manifest"),
            code_bundle=args.code_bundle,
            runtime_assets_archive=args.runtime_assets_archive,
            runtime_assets_inventory=args.runtime_assets_inventory,
            ssh_host=args.ssh_host,
            ssh_port=args.ssh_port,
            ssh_key_path=args.ssh_key,
            known_hosts_path=args.known_hosts,
        )
    elif args.command == "launch":
        result = launch_a3_remote_operation(
            _load(args.stage_receipt, role="stage receipt"),
            _load(args.request, role="remote request"),
            request_manifest=args.request_manifest,
            ssh_host=args.ssh_host,
            ssh_port=args.ssh_port,
            ssh_key_path=args.ssh_key,
            known_hosts_path=args.known_hosts,
            remote_python=args.remote_python,
        )
    else:
        result = collect_a3_remote_ranking_package(
            _load(args.stage_receipt, role="stage receipt"),
            _load(args.launch_receipt, role="launch receipt"),
            _load(args.request, role="remote request"),
            owner_local_output=args.owner_local_output,
            ssh_host=args.ssh_host,
            ssh_port=args.ssh_port,
            ssh_key_path=args.ssh_key,
            known_hosts_path=args.known_hosts,
        )
    _write_new(args.receipt, result)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
