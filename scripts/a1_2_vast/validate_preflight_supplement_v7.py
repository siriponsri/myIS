"""Validate the exact offline A1.2 v7 supplement wheelhouse tree."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Sequence


EXPECTED_DEPENDENCIES = {
    "jsonschema": "4.25.1",
    "pydantic": "2.13.4",
    "structlog": "26.1.0",
}
EXPECTED_REQUIREMENTS = [f"{name}=={version}" for name, version in EXPECTED_DEPENDENCIES.items()]
FORBIDDEN_PATH = re.compile(
    r"qrels|membership|query[_-]?ids|id_rsa|id_ed25519|credential|protected[_-]?evaluator",
    re.IGNORECASE,
)
CHECKSUM_LINE = re.compile(r"[a-f0-9]{64}  ([^/\\\r\n]+)")


class SupplementValidationError(ValueError):
    """Raised when the supplement is not the exact safe offline artifact."""


def validate_supplement(root: Path) -> dict[str, object]:
    directory = root.resolve()
    if not directory.is_dir():
        raise SupplementValidationError("supplement directory is missing")

    for path in directory.rglob("*"):
        relative = path.relative_to(directory).as_posix()
        if path.is_symlink():
            raise SupplementValidationError(f"supplement symlink is forbidden: {relative}")
        if FORBIDDEN_PATH.search(relative):
            raise SupplementValidationError(f"forbidden supplement path detected: {relative}")

    checksum_path = directory / "SHA256SUMS"
    if not checksum_path.is_file():
        raise SupplementValidationError("v7 supplement SHA256SUMS is missing")
    listed: set[str] = set()
    for number, line in enumerate(checksum_path.read_text(encoding="utf-8").splitlines(), 1):
        match = CHECKSUM_LINE.fullmatch(line)
        if match is None or match.group(1) in listed:
            raise SupplementValidationError(f"malformed supplement SHA256SUMS entry: {number}")
        listed.add(match.group(1))

    files = {path.name for path in directory.iterdir() if path.is_file()}
    if files != listed | {"SHA256SUMS"}:
        raise SupplementValidationError("supplement tree is not the exact checksummed artifact")
    if any(path.is_dir() for path in directory.iterdir()):
        raise SupplementValidationError("supplement subdirectories are forbidden")

    required = {"requirements.preflight-supplement.v7.txt", "SUPPLEMENT_VALIDATION.json"}
    if not required.issubset(listed):
        raise SupplementValidationError("supplement metadata files are not checksum-bound")
    if any(name.lower().startswith("torch-") and name.lower().endswith(".whl") for name in listed):
        raise SupplementValidationError("base-supplied torch must not be included in the supplement")

    requirements = (directory / "requirements.preflight-supplement.v7.txt").read_text(
        encoding="utf-8"
    ).splitlines()
    if requirements != EXPECTED_REQUIREMENTS:
        raise SupplementValidationError("supplement requirements drift")

    receipt = json.loads((directory / "SUPPLEMENT_VALIDATION.json").read_text(encoding="utf-8"))
    required_receipt_keys = {
        "schema_version",
        "status",
        "platform",
        "machine",
        "dependencies",
        "wheel_count",
        "torch_wheel_included",
        "offline_install",
        "contains_models_or_protected_data",
    }
    if not isinstance(receipt, dict) or set(receipt) != required_receipt_keys:
        raise SupplementValidationError("supplement validation receipt shape mismatch")
    expected_fields = {
        "schema_version": "myis.owner-a1.2-preflight-supplement-wheelhouse.v7",
        "status": "PASS",
        "platform": "linux/amd64",
        "dependencies": EXPECTED_DEPENDENCIES,
        "torch_wheel_included": False,
        "offline_install": "PASS",
        "contains_models_or_protected_data": False,
    }
    if any(receipt.get(key) != value for key, value in expected_fields.items()):
        raise SupplementValidationError("supplement validation receipt value mismatch")
    if receipt.get("machine") not in {"x86_64", "AMD64"}:
        raise SupplementValidationError("supplement machine is not x86_64")
    wheel_count = sum(name.lower().endswith(".whl") for name in listed)
    if receipt.get("wheel_count") != wheel_count:
        raise SupplementValidationError("supplement wheel count mismatch")
    return {"status": "PASS", "file_count": len(files), "wheel_count": wheel_count}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="validate-preflight-supplement-v7")
    parser.add_argument("supplement", type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(validate_supplement(args.supplement), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
