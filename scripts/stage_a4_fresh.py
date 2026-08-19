"""Stage a fresh A4 runtime with all binding metadata uploaded explicitly."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from myis_research.armindex.a4_remote_launcher import stage_a4_remote_runtime
from myis_research.kernel.canonical import canonical_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--key", type=Path, required=True)
    parser.add_argument("--known-hosts", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    package = root / "bundle" / "runtime-package"
    stage = root / "stage"
    manifest = json.loads((stage / "stage-manifest.json").read_text(encoding="utf-8"))
    receipt = stage_a4_remote_runtime(
        manifest,
        code_bundle=stage / "code.tar.gz",
        runtime_assets_archive=package / "a4-runtime-assets.tar.gz",
        runtime_assets_inventory=package / "assets" / "A4_RUNTIME_ASSETS.json",
        runtime_bindings=package / "A4_RUNTIME_BINDINGS.json",
        profile_registry=package / "profile-registry.json",
        ssh_host=args.host,
        ssh_port=args.port,
        ssh_key_path=args.key,
        known_hosts_path=args.known_hosts,
    )
    (stage / "stage-receipt.json").write_text(canonical_json(receipt) + "\n", encoding="utf-8")
    print(canonical_json(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
