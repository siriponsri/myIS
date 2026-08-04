from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator

from myis_research.kernel.canonical import canonical_sha256
from myis_research.protection import assert_aggregate_only


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "control/armindex/a0.10-legacy-code-harvest-ledger.v1.json"
RECEIPT_PATH = ROOT / "campaigns/armindex-multiretriever-v2/evidence/a0.10-legacy-code-harvest.receipt.v1.json"
SOURCE_VERIFICATION_PATH = ROOT / "outputs/audits/repository/thaipha-lex-source-verification-a0.10-20260804.json"


def _load(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_harvest_ledger_and_receipt_are_schema_valid_and_self_hashed() -> None:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    ledger_schema = _load("schemas/armindex/legacy-code-harvest-ledger.v1.json")
    receipt_schema = _load("schemas/armindex/legacy-code-harvest-receipt.v1.json")

    Draft202012Validator(ledger_schema).validate(ledger)
    Draft202012Validator(receipt_schema).validate(receipt)
    assert canonical_sha256({key: value for key, value in ledger.items() if key != "ledger_sha256"}) == ledger["ledger_sha256"]
    assert canonical_sha256({key: value for key, value in receipt.items() if key != "receipt_sha256"}) == receipt["receipt_sha256"]
    assert hashlib.sha256(LEDGER_PATH.read_bytes()).hexdigest() == receipt["ledger_sha256"]
    fixture_receipt = ROOT / str(receipt["fixture_receipt_uri"])
    assert hashlib.sha256(fixture_receipt.read_bytes()).hexdigest() == receipt["fixture_receipt_sha256"]
    source_verification = json.loads(SOURCE_VERIFICATION_PATH.read_text(encoding="utf-8"))
    source_schema = _load("schemas/armindex/source-verification-receipt.v1.json")
    Draft202012Validator(source_schema).validate(source_verification)
    assert canonical_sha256({key: value for key, value in source_verification.items() if key != "receipt_sha256"}) == source_verification["receipt_sha256"]
    assert hashlib.sha256(SOURCE_VERIFICATION_PATH.read_bytes()).hexdigest() == receipt["source_verification_receipt_sha256"]
    assert_aggregate_only(ledger)
    assert_aggregate_only(receipt)
    assert_aggregate_only(source_verification)


def test_myis_source_commit_paths_match_harvest_hashes() -> None:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    entries = [
        item for item in ledger["components"]
        if item["source_repository"] == "myIS"
    ]

    for entry in entries:
        completed = subprocess.run(
            ["git", "show", f"{entry['source_commit']}:{entry['source_path']}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        assert hashlib.sha256(completed.stdout).hexdigest() == entry["source_sha256"]


def test_thaipha_source_verification_receipt_covers_every_ledger_component() -> None:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    verification = json.loads(SOURCE_VERIFICATION_PATH.read_text(encoding="utf-8"))
    sources = {
        item["component_id"]: item for item in ledger["components"]
        if item["source_repository"] == "ThaiPha-Lex"
    }
    verified = {item["component_id"]: item for item in verification["components"]}

    assert verification["verified_component_count"] == len(sources) == 14
    assert set(verified) == set(sources)
    for component_id, source in sources.items():
        assert verified[component_id]["source_path"] == source["source_path"]
        assert verified[component_id]["source_sha256"] == source["source_sha256"]
        assert verified[component_id]["disposition"] == source["disposition"]
        assert len(verified[component_id]["git_blob"]) == 40


def test_harvest_has_no_wholesale_copy_or_active_historical_import() -> None:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    adopted = {
        item["component_id"] for item in ledger["components"]
        if item["disposition"] in {"adopt", "refactor", "wrap"}
    }
    active_sources = list((ROOT / "src/myis_research/armindex").rglob("*.py"))

    assert len(adopted) == 9
    assert all("ThaiPha-Lex" not in path.read_text(encoding="utf-8") for path in active_sources)
    assert all(
        "myis_research.scope" not in path.read_text(encoding="utf-8")
        and "myis_research.p2" not in path.read_text(encoding="utf-8")
        for path in active_sources
    )
