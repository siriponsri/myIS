"""Validate byte-canonical imported artifacts and their Git index copies."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
IMPORT_MANIFEST = ROOT / "01_evidence/literature/IMPORT_MANIFEST.csv"
CANONICAL_PATHS = (
    "01_evidence/literature/qa-provenance/BATCH_2A_ARTIFACT_VALIDATION.json",
    "01_evidence/literature/qa-provenance/BATCH_2A_CSV_VALIDATION.json",
    "01_evidence/literature/qa-provenance/BATCH_2A_INGESTION_CANDIDATES.csv",
)


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def index_bytes(relative_path: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f":{relative_path}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"cannot read Git index bytes for {relative_path}")
    return completed.stdout


def semantic_value(relative_path: str, value: bytes) -> object:
    text = value.decode("utf-8-sig")
    if relative_path.endswith(".json"):
        return json.loads(text)
    return list(csv.reader(io.StringIO(text, newline="")))


def expected_hashes() -> dict[str, str]:
    with IMPORT_MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = csv.DictReader(handle)
        return {
            row["current_repo_relative_path"].replace("\\", "/"): row[
                "target_sha256"
            ].upper()
            for row in rows
        }


def validate() -> list[str]:
    failures: list[str] = []
    expected = expected_hashes()
    for relative_path in CANONICAL_PATHS:
        if relative_path not in expected:
            failures.append(f"missing import manifest row: {relative_path}")
            continue
        worktree = (ROOT / relative_path).read_bytes()
        staged = index_bytes(relative_path)
        canonical_hash = expected[relative_path]
        if digest_bytes(worktree) != canonical_hash:
            failures.append(f"worktree hash mismatch: {relative_path}")
        if digest_bytes(staged) != canonical_hash:
            failures.append(f"Git index hash mismatch: {relative_path}")
        try:
            if semantic_value(relative_path, worktree) != semantic_value(
                relative_path, staged
            ):
                failures.append(f"semantic mismatch: {relative_path}")
        except (UnicodeDecodeError, csv.Error, json.JSONDecodeError) as exc:
            failures.append(f"cannot parse {relative_path}: {exc}")
    return failures


def main() -> int:
    failures = validate()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("BATCH_2A_CANONICAL_BYTES_VALID=true")
    print("BATCH_2A_GIT_INDEX_BYTES_VALID=true")
    print("BATCH_2A_SEMANTICS_MATCH=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
