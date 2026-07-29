"""Low-dev CLI for the generated Obsidian note projection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .catalog import build_notes, load_note_catalog


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-notes")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("build", "check", "catalog"):
        command = sub.add_parser(name)
        command.add_argument("--repository-root", type=Path, default=Path.cwd())
    open_note = sub.add_parser("open")
    open_note.add_argument("note_id")
    open_note.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    root = args.repository_root.resolve()
    result = build_notes(root) if args.command == "build" else load_note_catalog(root)
    if args.command == "open":
        matches = [note for note in result["notes"] if note["note_id"] == args.note_id]
        if not matches:
            parser.error("note ID is not allowlisted")
        print(matches[0]["obsidian_uri"])
        return 0
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
