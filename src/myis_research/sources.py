"""Immutable source registration for the Brain-drive research flow.

The registry records provenance and hashes only. Raw PDFs, web caches, and
historical repositories remain in their owning store and are never copied into
the Brain or into an MLflow run.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    kind: str
    locator: str
    title: str
    sha256: str
    registered_at: str
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def register_source(
    locator: str | Path,
    *,
    kind: str,
    title: str | None = None,
    metadata: dict[str, str] | None = None,
) -> SourceRecord:
    """Create a deterministic record without changing the source."""
    value = str(locator)
    path = Path(value)
    if path.is_file():
        digest = sha256_file(path)
        canonical_locator = path.resolve().as_posix()
    elif urlsplit(value).scheme in {"http", "https"}:
        digest = sha256_text(value)
        canonical_locator = value
    else:
        raise FileNotFoundError(f"Source locator is neither a file nor URL: {value}")
    source_id = f"{kind}-{digest[:16]}"
    return SourceRecord(
        source_id=source_id,
        kind=kind,
        locator=canonical_locator,
        title=title or path.name,
        sha256=digest,
        registered_at=datetime.now(timezone.utc).isoformat(),
        metadata=dict(metadata or {}),
    )


class SourceCatalog:
    """Append-only JSONL catalog suitable for local/offline operation."""

    def __init__(self, path: Path):
        self.path = path

    def append(self, record: SourceRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")

    def records(self) -> list[SourceRecord]:
        if not self.path.exists():
            return []
        return [SourceRecord(**json.loads(line)) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
