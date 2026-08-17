from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from myis_research.armindex.a3_execution_preparation import (
    A3PreparationError,
    build_a3_pending_preflight,
    validate_a3_budget_extension,
    validate_a3_preparation_authority,
    validate_a3_preparation_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
BUDGET_PATH = ROOT / "control" / "budgets" / "armindex-budget-extension-a3-v1.json"
AUTHORITY_PATH = ROOT / "control" / "armindex" / "a3" / "a3-five-arm-preparation-authority.v1.json"
MANIFEST_PATH = ROOT / "control" / "armindex" / "a3" / "a3-five-arm-preparation-manifest.v1.json"
SCHEMA_PATH = ROOT / "schemas" / "armindex" / "a3-five-arm-preparation-manifest.v1.json"
AUTHORITY_SCHEMA_PATH = ROOT / "schemas" / "armindex" / "a3-five-arm-preparation-authority.v1.json"
BUDGET_SCHEMA_PATH = ROOT / "schemas" / "armindex" / "armindex-budget-extension-a3-v1.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_extended_a3_pending_package_is_schema_valid_and_fail_closed() -> None:
    budget = _load(BUDGET_PATH)
    authority = _load(AUTHORITY_PATH)
    manifest = _load(MANIFEST_PATH)
    schema = _load(SCHEMA_PATH)
    authority_schema = _load(AUTHORITY_SCHEMA_PATH)
    budget_schema = _load(BUDGET_SCHEMA_PATH)

    Draft202012Validator.check_schema(schema)
    Draft202012Validator.check_schema(authority_schema)
    Draft202012Validator.check_schema(budget_schema)
    assert not list(Draft202012Validator(schema).iter_errors(manifest))
    assert not list(Draft202012Validator(authority_schema).iter_errors(authority))
    assert not list(Draft202012Validator(budget_schema).iter_errors(budget))
    assert validate_a3_budget_extension(budget) == budget
    assert validate_a3_preparation_authority(authority) == authority
    assert validate_a3_preparation_manifest(manifest) == manifest

    preflight = build_a3_pending_preflight(budget, authority, manifest)
    assert preflight["status"] == "PENDING_A2_CLOSEOUT"
    assert preflight["launch_permitted"] is False
    assert preflight["five_arm_count"] == 5
    assert preflight["transfer_matrix_cell_count"] == 25
    assert preflight["planned_cross_arm_evaluation_count"] == 20
    assert preflight["maximum_harnessopt_batches"] == 3
    assert preflight["maximum_harnessopt_candidates"] == 12


@pytest.mark.parametrize(
    ("source", "path", "replacement", "message"),
    [
        ("budget", ("hard_stops", "a3_forward_usd"), 36, "hard-stop"),
        ("authority", ("execution_permitted",), True, "fail-closed"),
        ("manifest", ("arms", 0, "winner_program_sha256"), "a" * 64, "cannot contain A2 winner"),
        ("manifest", ("transfer_matrix", 0, "result_receipt_sha256"), "b" * 64, "materialized results"),
        ("manifest", ("harnessopt_plan", "maximum_batches"), 2, "extended HarnessOpt"),
    ],
)
def test_extended_a3_pending_package_rejects_unsafe_mutation(
    source: str, path: tuple[object, ...], replacement: object, message: str
) -> None:
    value = _load({"budget": BUDGET_PATH, "authority": AUTHORITY_PATH, "manifest": MANIFEST_PATH}[source])
    target: object = value
    for segment in path[:-1]:
        target = target[segment]  # type: ignore[index]
    target[path[-1]] = replacement  # type: ignore[index]

    validator = {
        "budget": validate_a3_budget_extension,
        "authority": validate_a3_preparation_authority,
        "manifest": validate_a3_preparation_manifest,
    }[source]
    with pytest.raises(A3PreparationError, match=message):
        validator(value)
