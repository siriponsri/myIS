"""Owner-local aggregate request processor implementation."""

from __future__ import annotations

import json
from pathlib import Path

from .owner_local import build_receipt, validate_request


def process(request_path: Path, aggregate_path: Path, receipt_path: Path) -> Path:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    aggregate = json.loads(aggregate_path.read_text(encoding="utf-8"))
    validated = validate_request(request)
    if not isinstance(aggregate, dict) or set(aggregate) != {"aggregate_counts", "aggregate_hashes"}:
        raise ValueError("aggregate source must contain only aggregate_counts and aggregate_hashes")
    receipt = build_receipt(validated, aggregate_counts=aggregate["aggregate_counts"], aggregate_hashes=aggregate["aggregate_hashes"])
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt_path
