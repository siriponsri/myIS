from __future__ import annotations

from pathlib import Path

import pytest

from myis_research.armindex.a1_2_live_preflight_execution_v9 import (
    BINDING_PATHS,
    BOOTSTRAP_PATH,
    CONTRACT_PATH,
    CONTINUATION_POLICY_PATH,
    COORDINATOR_PATH,
    DEPENDENT_PATHS,
    EXECUTION_MODULE_PATH,
    LAUNCHER_PATH,
    RECEIPT_PATH,
    RUNBOOK_PATH,
    RUNTIME_MODULE_PATH,
    SCHEMA_PATH,
    V8_CONTRACT_PATH,
    V8_RECEIPT_PATH,
    ExecutionLifecycleV9Error,
    _require_dependencies,
    validate_revision,
)


def test_v9_reserves_complete_additive_binding_surface() -> None:
    assert BINDING_PATHS == (
        V8_CONTRACT_PATH,
        V8_RECEIPT_PATH,
        CONTINUATION_POLICY_PATH,
        EXECUTION_MODULE_PATH,
        RUNTIME_MODULE_PATH,
        LAUNCHER_PATH,
        COORDINATOR_PATH,
        BOOTSTRAP_PATH,
        RUNBOOK_PATH,
        SCHEMA_PATH,
    )
    assert DEPENDENT_PATHS == (
        RUNTIME_MODULE_PATH,
        LAUNCHER_PATH,
        COORDINATOR_PATH,
        BOOTSTRAP_PATH,
        RUNBOOK_PATH,
    )
    assert CONTRACT_PATH.name.endswith(".v9.json")
    assert RECEIPT_PATH.name.endswith(".v9.json")


def test_v9_materialization_fails_closed_when_dependencies_are_missing(tmp_path: Path) -> None:
    with pytest.raises(ExecutionLifecycleV9Error, match="lifecycle implementation is not ready"):
        _require_dependencies(tmp_path)


def test_v9_materialized_revision_validates() -> None:
    result = validate_revision(Path(__file__).resolve().parents[1])
    assert result["launch_allowed"] is False
    assert result["adopted_for_execution"] is False
    assert result["measured_runs"] == 0
    assert result["charged_usd"] == 0


def test_v9_owner_flow_verifies_teardown_before_collection() -> None:
    root = Path(__file__).resolve().parents[1]
    coordinator = (root / COORDINATOR_PATH).read_text(encoding="utf-8")
    runbook = (root / RUNBOOK_PATH).read_text(encoding="utf-8")
    assert "teardown --output-root" in coordinator
    assert "--children-reaped" in coordinator
    assert runbook.index("-Action teardown") < runbook.index("-Action collect")
    assert "teardown.json" in runbook
