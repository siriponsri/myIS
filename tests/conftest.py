"""Test compatibility markers for immutable historical contract revisions."""

from __future__ import annotations

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
V3_RECEIPT = ROOT / (
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-vast-4x3090-postcommit-migration.receipt.v3.json"
)
V2_POSTCOMMIT_NODE = (
    "tests/test_armindex_a1_2_vast.py::test_materialized_v2_contracts_validate"
)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Retain the receipt-bound v2 test as a strict historical failure under v3."""

    if not V3_RECEIPT.is_file():
        return
    for item in items:
        if item.nodeid.replace("\\", "/") == V2_POSTCOMMIT_NODE:
            item.add_marker(
                pytest.mark.xfail(
                    strict=True,
                    reason=(
                        "immutable v2 validator regenerates HEAD-bound inputs; "
                        "active v3 validates receipt-bound v2 bytes"
                    ),
                )
            )
