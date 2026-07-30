"""Build a metadata-first migration inventory without opening protected payloads."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str | None:
    if path.stat().st_size > 8 * 1024 * 1024:
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head(root: Path) -> str | None:
    try:
        return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def files(root: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        size = path.stat().st_size
        records.append({
            "path": relative,
            "bytes": size,
            "sha256": sha256(path),
            "hash_status": "recorded" if size <= 8 * 1024 * 1024 else "deferred_large_file",
        })
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--research-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sibling-root", type=Path, action="append", default=[])
    args = parser.parse_args()
    research_root = args.research_root.resolve()
    payload = {
        "schema_version": "myis.migration-manifest.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "research_root": str(research_root),
        "repositories": [],
    }
    roots = [research_root, *(root.resolve() for root in args.sibling_root)]
    for root in roots:
        payload["repositories"].append({
            "root": str(root),
            "git_head": git_head(root),
            "files": files(root),
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": str(args.output), "repositories": len(roots)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
