import json
from pathlib import Path

from myis_research.owner_local_runner import process
from myis_research.owner_local import canonical_sha256


def test_runner_writes_aggregate_only_receipt(tmp_path: Path):
    request = {
        "schema_version": "myis.owner-local-request.v1",
        "request_id": "d1-demo",
        "decision_id": "D1_START_CAMPAIGN",
        "scope": {"campaign": "a" * 64},
        "git_commit": "a" * 40,
        "input_hashes": {"protected_source": "b" * 64},
    }
    source = {"aggregate_counts": {"train": 250}, "aggregate_hashes": {"train": "c" * 64}}
    request_path = tmp_path / "request.json"
    source_path = tmp_path / "aggregate.json"
    receipt_path = tmp_path / "receipt.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    source_path.write_text(json.dumps(source), encoding="utf-8")
    process(request_path, source_path, receipt_path)
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert payload["decision_id"] == "D1_START_CAMPAIGN"
    assert payload["aggregate_counts"] == {"train": 250}
    assert payload["receipt_sha256"] == canonical_sha256({k: v for k, v in payload.items() if k != "receipt_sha256"})
