"""Read-only validation for the myIS Research restructure import."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LITERATURE = ROOT / "01_evidence" / "literature"
MANIFEST = LITERATURE / "IMPORT_MANIFEST.csv"
DIGESTS = LITERATURE / "validated-digests"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> int:
    failures: list[str] = []
    digest_files = sorted(DIGESTS.glob("U*_digest.md"))
    digest_ids = {path.name[:4] for path in digest_files}
    expected_ids = {f"U{number:03d}" for number in range(1, 41)}

    if len(digest_files) != 40:
        failures.append(f"expected 40 digests, found {len(digest_files)}")
    if digest_ids != expected_ids:
        failures.append("digest IDs are not exactly U001-U040")
    if list(ROOT.rglob("U041*")):
        failures.append("U041 artifact found even though U041 is not authorized")

    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 64:
        failures.append(f"expected 64 import rows, found {len(rows)}")

    for row in rows:
        relative = row.get("current_repo_relative_path", "")
        if not relative:
            failures.append("manifest row missing current_repo_relative_path")
            continue
        target = ROOT / Path(relative)
        try:
            target.resolve().relative_to(ROOT.resolve())
        except ValueError:
            failures.append(f"manifest path escapes repository: {relative}")
            continue
        if not target.is_file():
            failures.append(f"missing imported artifact: {relative}")
            continue
        actual = sha256(target)
        expected = row["target_sha256"].upper()
        if actual != expected:
            failures.append(f"hash mismatch: {relative}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("RESEARCH_RESTRUCTURE_VALID=true")
    print("VALIDATED_DIGEST_COUNT=40")
    print("U041_STARTED=false")
    print("IMPORT_MANIFEST_ROWS=64")
    print("IMPORT_HASHES_MATCH=true")
    print("IMPORT_PATHS_PORTABLE=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
