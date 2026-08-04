"""Fail-closed exact-path cleanup executor for verified migration candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def digest(path: Path) -> str:
    if path.is_file():
        h = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    return hashlib.sha256(f"directory:{path.as_posix()}".encode("utf-8")).hexdigest()


def resolve_inside(root: Path, relative: str) -> Path:
    if not relative or Path(relative).is_absolute() or "*" in relative or "?" in relative:
        raise ValueError(f"cleanup path must be an exact relative path: {relative!r}")
    candidate = (root / relative).resolve()
    candidate.relative_to(root.resolve())
    return candidate


def verify(entry: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    path = resolve_inside(repo_root, str(entry["path"]))
    if not path.exists():
        raise FileNotFoundError(path)
    actual = digest(path)
    if actual != str(entry["sha256"]):
        raise ValueError(f"cleanup hash drift: {entry['path']}")
    required = {
        "classification": "remove",
        "protected_scan": "pass",
        "active_references": 0,
        "unique_evidence": False,
        "archive_ref": None,
    }
    for key, expected in required.items():
        if entry.get(key) != expected:
            raise ValueError(f"cleanup entry is not verified for removal: {entry['path']} ({key})")
    return {**entry, "resolved_path": str(path), "verified_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}


def remove_exact(entry: dict[str, Any]) -> None:
    path = Path(str(entry["resolved_path"]))
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    entries = payload.get("entries", [])
    verified = [verify(entry, args.repo_root.resolve()) for entry in entries]
    if args.execute:
        for entry in verified:
            remove_exact(entry)
        payload["executed_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        payload["status"] = "executed"
        args.manifest.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        payload["status"] = "dry_run_pass"
    print(json.dumps({"status": payload["status"], "count": len(verified), "paths": [item["path"] for item in verified]}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
