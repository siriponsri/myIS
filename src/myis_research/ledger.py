"""Immutable hash-chained ledgers for Owner decisions and local receipts."""

from __future__ import annotations

import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")


def record_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


@contextmanager
def _writer_lock(root: Path) -> Iterator[None]:
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError("ledger root must be a regular directory")
    lock_path = root / ".writer.lock"
    if lock_path.is_symlink():
        raise RuntimeError("ledger writer lock cannot be a symlink")
    stream = lock_path.open("a+b")
    try:
        if os.name == "nt":
            import msvcrt

            stream.seek(0)
            if stream.tell() == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        if os.name == "nt":
            import msvcrt

            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()


class ImmutableJsonLedger:
    """One canonical JSON record per file with a single predecessor chain."""

    def __init__(
        self,
        root: Path,
        *,
        prior_field: str,
        record_id_field: str | None = None,
        supersedes_field: str | None = None,
    ) -> None:
        self.root = root
        self.prior_field = prior_field
        self.record_id_field = record_id_field
        self.supersedes_field = supersedes_field

    def records(self) -> list[tuple[Path, dict[str, Any], str]]:
        if not self.root.exists():
            return []
        if self.root.is_symlink() or not self.root.is_dir():
            raise ValueError("ledger root must be a regular directory")
        records = []
        for path in sorted(self.root.glob("*.json")):
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"ledger record must be a regular file: {path.name}")
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError(f"ledger record must be an object: {path.name}")
            records.append((path, payload, record_sha256(payload)))
        return records

    def validate_chain(self) -> dict[str, Any]:
        records = self.records()
        if not records:
            return {"count": 0, "head": None}
        try:
            return self._validate_records(records)
        except ValueError:
            repaired = self._reconciled_records(records)
            if repaired is None:
                raise
            return self._validate_records(repaired)

    def _validate_records(
        self, records: list[tuple[Path, dict[str, Any], str]]
    ) -> dict[str, Any]:
        by_hash = {digest: (path, payload) for path, payload, digest in records}
        if len(by_hash) != len(records):
            raise ValueError("ledger contains duplicate record bytes")
        referenced = set()
        genesis = []
        for path, payload, _ in records:
            prior = payload.get(self.prior_field)
            if prior is None:
                genesis.append(path.name)
            else:
                if prior not in by_hash:
                    raise ValueError(f"missing predecessor for {path.name}")
                referenced.add(prior)
        if len(genesis) != 1:
            raise ValueError("ledger must contain exactly one genesis record")
        heads = [digest for _, _, digest in records if digest not in referenced]
        if len(heads) != 1:
            raise ValueError("ledger contains a fork or cycle")
        visited = set()
        cursor: str | None = heads[0]
        while cursor is not None:
            if cursor in visited:
                raise ValueError("ledger contains a cycle")
            visited.add(cursor)
            cursor = by_hash[cursor][1].get(self.prior_field)
        if len(visited) != len(records):
            raise ValueError("ledger contains disconnected records")
        return {"count": len(records), "head": heads[0]}

    def _reconciled_records(
        self, records: list[tuple[Path, dict[str, Any], str]]
    ) -> list[tuple[Path, dict[str, Any], str]] | None:
        """Project an explicit divergent supersession without mutating bad history."""

        if self.record_id_field is None or self.supersedes_field is None:
            return None
        by_id: dict[str, tuple[Path, dict[str, Any], str]] = {}
        for item in records:
            identifier = item[1].get(self.record_id_field)
            if not isinstance(identifier, str) or identifier in by_id:
                return None
            by_id[identifier] = item
        excluded: set[str] = set()
        for _, payload, _ in records:
            supersedes = payload.get(self.supersedes_field)
            if supersedes is None:
                continue
            target = by_id.get(supersedes)
            if target is None:
                return None
            # A normal correction remains in the physical chain. A correction
            # pointing around its target explicitly reconciles disconnected history.
            if payload.get(self.prior_field) != target[2]:
                excluded.add(supersedes)
        if not excluded:
            return None
        return [item for item in records if item[1][self.record_id_field] not in excluded]

    def head(self) -> str | None:
        return self.validate_chain()["head"]

    def append(self, record_id: str, payload: Mapping[str, Any]) -> tuple[Path, str]:
        if not record_id or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in record_id):
            raise ValueError("record_id contains unsafe characters")
        body = dict(payload)
        with _writer_lock(self.root):
            expected_prior = self.head()
            if body.get(self.prior_field) != expected_prior:
                raise RuntimeError("ledger head changed; create a new preview")
            final = self.root / f"{record_id}.json"
            if final.exists():
                raise FileExistsError(f"immutable ledger record exists: {final.name}")
            encoded = canonical_json_bytes(body)
            temporary = self.root / f".{record_id}.{os.getpid()}.tmp"
            try:
                with temporary.open("xb") as stream:
                    stream.write(encoded)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.link(temporary, final)
            finally:
                if temporary.exists():
                    temporary.unlink()
            return final, hashlib.sha256(encoded).hexdigest()
