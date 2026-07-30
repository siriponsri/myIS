"""Console entrypoint for owner-local legacy DAPFAM certification."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from .legacy_dapfam import build_legacy_p1_request, discover_legacy, legacy_project_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-legacy-dapfam")
    parser.add_argument("--legacy-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--inventory-output", type=Path)
    parser.add_argument("--make-request", type=Path)
    args = parser.parse_args(argv)
    legacy_root = args.legacy_root.resolve()
    repository_root = args.repository_root.resolve()
    inventory_path = (args.inventory_output or _owner_local_default("legacy-dapfam-inventory.v1.json")).resolve()
    _assert_owner_local_output(inventory_path, repository_root, legacy_root)
    request_path = args.make_request.resolve() if args.make_request else None
    if request_path is not None:
        _assert_owner_local_output(request_path, repository_root, legacy_root)
        inventory, request = build_legacy_p1_request(legacy_root, repository_root)
    else:
        inventory = discover_legacy(legacy_root, include_protected_hashes=False)
        request = None
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory_path.write_text(json.dumps(inventory, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if request_path is not None:
        request_path.parent.mkdir(parents=True, exist_ok=True)
        request_path.write_text(json.dumps(request, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "inventory": str(inventory_path), "request": str(request_path) if request_path else None, "protected_payloads_emitted": False}, ensure_ascii=True))
    return 0


def _owner_local_default(filename: str) -> Path:
    return Path(tempfile.gettempdir()) / "myis-owner-local" / filename


def _assert_owner_local_output(output_path: Path, repository_root: Path, legacy_root: Path) -> None:
    legacy_tree = legacy_project_root(legacy_root)
    for forbidden_root, label in ((repository_root, "repository"), (legacy_tree, "read-only legacy tree")):
        try:
            output_path.relative_to(forbidden_root)
        except ValueError:
            continue
        raise ValueError(f"certification outputs must not be written into the {label}")


if __name__ == "__main__":
    raise SystemExit(main())
