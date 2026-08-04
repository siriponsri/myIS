"""Validate repository-local links in public and canonical Markdown files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote


_LINK = re.compile(r"!?\[[^\]]*\]\((?P<target><[^>]+>|[^)\s]+)")
_EXTERNAL_SCHEMES = ("http://", "https://", "mailto:", "obsidian://", "data:")
_ROOT_FILES = (
    "README.md",
    "PLAN.md",
    "HANDOFF.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CHANGELOG.md",
)


def _markdown_files(root: Path) -> tuple[Path, ...]:
    files = [root / name for name in _ROOT_FILES if (root / name).is_file()]
    docs = root / "docs"
    if docs.is_dir():
        files.extend(path for path in docs.rglob("*.md") if path.is_file() and not path.is_symlink())
    return tuple(sorted(files, key=lambda path: path.relative_to(root).as_posix()))


def validate_links(root: Path) -> list[str]:
    root = root.resolve(strict=True)
    failures: list[str] = []
    for source in _markdown_files(root):
        text = source.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in _LINK.finditer(line):
                raw = match.group("target").strip("<>")
                if not raw or raw.startswith("#") or raw.lower().startswith(_EXTERNAL_SCHEMES):
                    continue
                path_text = unquote(raw.split("#", 1)[0])
                if not path_text:
                    continue
                candidate = (root / path_text.lstrip("/\\")) if raw.startswith(("/", "\\")) else (source.parent / path_text)
                resolved = candidate.resolve()
                try:
                    resolved.relative_to(root)
                except ValueError:
                    failures.append(f"{source.relative_to(root).as_posix()}:{line_number}: link escapes repository: {raw}")
                    continue
                if not resolved.exists():
                    failures.append(f"{source.relative_to(root).as_posix()}:{line_number}: missing target: {raw}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    failures = validate_links(args.repository_root)
    report = {
        "schema_version": "myis.markdown-link-validation.v1",
        "status": "PASS" if not failures else "FAIL",
        "files_checked": len(_markdown_files(args.repository_root.resolve())),
        "failures": failures,
    }
    print(json.dumps(report, ensure_ascii=True, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
