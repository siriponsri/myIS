"""Supported dashboard launcher; remote binding is intentionally impossible."""

from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn

from .app import create_app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        raise SystemExit("port must be between 1024 and 65535")
    app = create_app(repository_root=args.repository_root, port=args.port)
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=args.port,
        workers=1,
        reload=False,
        proxy_headers=False,
        access_log=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
