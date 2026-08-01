"""Build the deterministic repository-safe catalog for the P2 fixture pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from myis_research.kernel.canonical import canonical_sha256
from myis_research.p2.fixture import (
    P2FixtureError,
    validate_fixture_execution_manifest,
    validate_fixture_receipt,
)


OUTPUT_ROOT = Path("outputs/fixtures/p2")
RECEIPT_NAME = "p2-fixture-pilot-v1.receipt.json"
MANIFEST_NAME = "p2-fixture-pilot-v1.execution-manifest.json"
REGISTRATION_NAME = "p2-fixture-pilot-v1.mlflow-registration.json"
AUDIT_INDEX = Path("orchestration/audits/p2-readiness/index.json")


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise P2FixtureError(f"catalog source must be a JSON object: {path.name}")
    return value


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def build(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve(strict=True)
    output = root / OUTPUT_ROOT
    receipt_path = output / RECEIPT_NAME
    manifest_path = output / MANIFEST_NAME
    registration_path = output / REGISTRATION_NAME

    receipt = validate_fixture_receipt(_load_json(receipt_path), repository_root=root)
    manifest = validate_fixture_execution_manifest(
        _load_json(manifest_path),
        receipt=receipt,
    )
    registration = _load_json(registration_path)
    registration_unsigned = {
        key: value for key, value in registration.items() if key != "registration_sha256"
    }
    if registration.get("registration_sha256") != canonical_sha256(registration_unsigned):
        raise P2FixtureError("fixture MLflow registration self-hash is invalid")
    if registration.get("source_receipt_sha256") != receipt["receipt_sha256"]:
        raise P2FixtureError("fixture MLflow registration receipt binding is invalid")
    if registration.get("execution_manifest_sha256") != manifest["manifest_sha256"]:
        raise P2FixtureError("fixture MLflow registration manifest binding is invalid")

    audit = _load_json(root / AUDIT_INDEX)
    rounds = [
        {"round": int(item["round"]), "verdict": str(item["verdict"])}
        for item in audit.get("rounds", [])
        if isinstance(item, dict)
    ]
    runtime = audit.get("review_runtime", {})
    expected_rounds = [
        {"round": 1, "verdict": "revise"},
        {"round": 2, "verdict": "revise"},
        {"round": 3, "verdict": "accept"},
    ]
    expected_runtime = {
        "provider": "openai",
        "model": "gpt-5.6-sol",
        "codex_cli_version": "0.146.0",
        "sandbox": "read-only",
        "protected_data_accessed": False,
        "measured_execution_performed": False,
    }
    if rounds != expected_rounds or runtime != expected_runtime:
        raise P2FixtureError("official review provenance differs from the Owner record")

    readme = (
        "# P2 Fixture Pilot\n\n"
        "ชุดนี้เป็นหลักฐานเชิงวิศวกรรมจาก repository-only synthetic fixture สำหรับ `P2.1`. "
        "ไม่ใช่ measured scientific evidence และไม่เปิด real selection หรือ final-872.\n\n"
        "## Status\n\n"
        "- Phase / Task: `P2_SCOPE_DEVELOPMENT` / `P2.1`\n"
        "- Fixture status: `passed`\n"
        "- Evidence class: `fixture`\n"
        "- Scientific authority: `false`\n"
        "- Synthetic candidates / iterations / shortlist / fixture selection: `32 / 5 / 4 / 1`\n"
        "- Real measured runs / candidates / selection accesses: `0 / 0 / 0`\n"
        "- Protected data accessed: `false`\n"
        "- Measured execution performed: `false`\n\n"
        "## Official Review Provenance\n\n"
        "- Round 1 verdict: `revise`\n"
        "- Round 2 verdict: `revise`\n"
        "- Round 3 verdict: `accept`\n"
        "- Provider: `openai`\n"
        "- Model: `gpt-5.6-sol`\n"
        "- Codex CLI: `0.146.0`\n"
        "- Sandbox: `read-only`\n\n"
        "## Files\n\n"
        f"- `{RECEIPT_NAME}`: sanitized fixture receipt `{receipt['receipt_sha256']}`\n"
        f"- `{MANIFEST_NAME}`: execution manifest `{manifest['manifest_sha256']}`\n"
        f"- `{REGISTRATION_NAME}`: isolated MLflow registration `{registration['registration_sha256']}`\n"
        "- `index.json`: machine-readable catalog\n"
        "- `SHA256SUMS.txt`: file-level checksums\n\n"
        "Next authorized action: `Owner-local measured preflight`. Do not start it automatically.\n"
    )
    _write(output / "README.md", readme)

    artifact_hashes = {
        RECEIPT_NAME: _file_sha256(receipt_path),
        MANIFEST_NAME: _file_sha256(manifest_path),
        REGISTRATION_NAME: _file_sha256(registration_path),
        "README.md": _file_sha256(output / "README.md"),
    }
    index = {
        "schema_version": "myis.p2-fixture-index.v1",
        "fixture_id": "p2-fixture-pilot-v1",
        "phase_id": "P2_SCOPE_DEVELOPMENT",
        "task_id": "P2.1",
        "status": "passed",
        "evidence_class": "fixture",
        "scientific_authority": False,
        "protected_data_accessed": False,
        "measured_execution_performed": False,
        "synthetic_candidates": 32,
        "synthetic_iterations": 5,
        "synthetic_shortlist": 4,
        "fixture_selection_exposures": 1,
        "measured_runs": 0,
        "candidate_count": 0,
        "selection_accesses": 0,
        "official_review": {
            "rounds": rounds,
            "runtime": runtime,
            "source": AUDIT_INDEX.as_posix(),
        },
        "fixture_receipt_sha256": receipt["receipt_sha256"],
        "execution_manifest_sha256": manifest["manifest_sha256"],
        "fixture_package_sha256": receipt["fixture_package_sha256"],
        "mlflow_registration_sha256": registration["registration_sha256"],
        "mlflow_run_id": registration["mlflow_run_id"],
        "artifacts": artifact_hashes,
        "next_authorized_action": "Owner-local measured preflight",
    }
    _write(output / "index.json", json.dumps(index, ensure_ascii=True, indent=2, sort_keys=True) + "\n")

    checksum_names = sorted((*artifact_hashes, "index.json"))
    checksums = "".join(
        f"{_file_sha256(output / name)}  {name}\n" for name in checksum_names
    )
    _write(output / "SHA256SUMS.txt", checksums)
    return index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    result = build(args.repository_root)
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
