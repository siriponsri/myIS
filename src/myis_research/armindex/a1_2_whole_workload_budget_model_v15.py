"""Validate the additive aggregate-only A1.2 whole-workload budget model."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only

CONTROL_PATH = Path("control/armindex/a1.2/whole-workload-budget-model.v15.json")
SCHEMA_PATH = Path("schemas/armindex/a1.2-whole-workload-budget-model.v15.json")
STORE_BINDING_RELATIVE = (
    "a1.2-v12-r3/protected/v15/receipts/A1_2_COMPILED_PROGRAM_BINDINGS_V15.json"
)
EXPECTED_BINDING_SHA256 = (
    "c8a6b3a9c784be23f7effe5a51e470259322e7e99a51fc13eacbc2c0b16f8760"
)


class WholeWorkloadBudgetModelV15Error(ValueError):
    """Fail-closed validation error."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise WholeWorkloadBudgetModelV15Error(
            "budget model JSON is missing or invalid"
        ) from error
    if not isinstance(value, dict):
        raise WholeWorkloadBudgetModelV15Error("budget model must be an object")
    return value


def _store(root: Path) -> Path:
    raw = __import__("os").environ.get("MYIS_STORE")
    if not raw:
        raise WholeWorkloadBudgetModelV15Error("MYIS_STORE is required")
    path = Path(raw).resolve(strict=True)
    if path.is_symlink() or not path.is_dir() or path.is_relative_to(root):
        raise WholeWorkloadBudgetModelV15Error(
            "MYIS_STORE must be an external directory"
        )
    return path


def _self_hash(value: Mapping[str, Any], field: str) -> str:
    return canonical_sha256({key: item for key, item in value.items() if key != field})


def validate_contract(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    value = _load(root / CONTROL_PATH)
    schema = _load(root / SCHEMA_PATH)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda item: list(item.path),
    )
    if errors:
        raise WholeWorkloadBudgetModelV15Error(
            f"budget model schema failure at {list(errors[0].path)}"
        )
    if value.get("model_sha256") != _self_hash(value, "model_sha256"):
        raise WholeWorkloadBudgetModelV15Error("budget model self-hash mismatch")
    if file_sha256(root / CONTROL_PATH) is None:
        raise WholeWorkloadBudgetModelV15Error("budget model cannot be hashed")
    assert_aggregate_only(value)
    if value["source"]["binding_set_sha256"] != EXPECTED_BINDING_SHA256:
        raise WholeWorkloadBudgetModelV15Error("binding-set source commitment drift")
    if (
        value["live_admission"]["admitted"] is not False
        or value["status"] != "LOCAL_MODEL_PENDING_LIVE_PROVIDER"
    ):
        raise WholeWorkloadBudgetModelV15Error("live admission must remain pending")
    return value


def validate_against_binding_set(
    repository_root: Path, *, binding_relative: str = STORE_BINDING_RELATIVE
) -> dict[str, Any]:
    root = repository_root.resolve()
    model = validate_contract(root)
    binding_path = _store(root) / Path(binding_relative)
    try:
        binding = _load(binding_path)
    except WholeWorkloadBudgetModelV15Error as error:
        raise WholeWorkloadBudgetModelV15Error(
            "protected v15 binding set is unavailable"
        ) from error
    if binding.get("binding_set_sha256") != EXPECTED_BINDING_SHA256:
        raise WholeWorkloadBudgetModelV15Error(
            "protected binding-set self-commitment differs"
        )
    if binding.get("binding_set_sha256") != _self_hash(binding, "binding_set_sha256"):
        raise WholeWorkloadBudgetModelV15Error(
            "protected binding-set self-hash mismatch"
        )
    rows = binding.get("bindings")
    if not isinstance(rows, list) or len(rows) != 25:
        raise WholeWorkloadBudgetModelV15Error("protected binding set is not 25/25")
    totals = {
        "physical_window_total": sum(int(row["physical_window_count"]) for row in rows),
        "raw_overflow_logical_inputs": sum(
            int(row["raw_overlength_count"]) for row in rows
        ),
        "corpus_overflow_logical_units": sum(
            int(row["corpus_overflow_logical_unit_count"]) for row in rows
        ),
        "query_overflow_logical_units": sum(
            int(row["query_overflow_logical_unit_count"]) for row in rows
        ),
    }
    if any(model["workload"][key] != value for key, value in totals.items()):
        raise WholeWorkloadBudgetModelV15Error(
            "budget model physical-window totals differ from bindings"
        )
    if (
        binding.get("query_compatibility", {}).get("rep_dev_query_count") != 150
        or binding.get("query_compatibility", {}).get("coverage_fraction") != 1.0
    ):
        raise WholeWorkloadBudgetModelV15Error("REP-DEV query coverage is not 100%")
    if any(
        int(row["physical_window_max_tokens"]) > int(row["effective_input_limit"])
        for row in rows
    ):
        raise WholeWorkloadBudgetModelV15Error(
            "physical window exceeds effective limit"
        )
    return {
        "status": "PASS",
        "model_sha256": model["model_sha256"],
        **totals,
        "binding_set_sha256": EXPECTED_BINDING_SHA256,
        "hard_stops_usd": model["frozen_hard_stops_usd"],
        "live_admission_status": "PENDING_LIVE_PROVIDER",
        "launch_allowed": False,
        "admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-whole-workload-budget-model-v15")
    parser.add_argument("command", choices=("validate", "validate-bindings"))
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--binding-relative", default=STORE_BINDING_RELATIVE)
    args = parser.parse_args()
    result = (
        validate_contract(args.repository_root)
        if args.command == "validate"
        else validate_against_binding_set(
            args.repository_root, binding_relative=args.binding_relative
        )
    )
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
