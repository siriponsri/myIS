"""Prepare and validate additive A1.2 v12 Owner-local adoption inputs.

The module is intentionally local-only.  It binds the immutable v11 request
and defines the aggregate-safe receipts a later, separately authorized goal
must supply.  It neither opens a provider nor writes a final adoption receipt
while Owner-local or live-provider evidence is absent.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a1_2_compiled_bindings_v12 import validate_binding_set
from .a1_2_watchdog_provider_destroy_dry_run_v12 import (
    POLICY_PATH as WATCHDOG_POLICY_PATH,
    REVISION_ID as WATCHDOG_REVISION_ID,
    current_status as watchdog_current_status,
    _validate_result as validate_watchdog_result,
)


REVISION_ID = "a1.2-scientific-execution-adoption-inputs-v12"
CONTRACT_PATH = Path(
    "control/armindex/a1.2/scientific-execution-adoption-inputs.v12.json"
)
CONTRACT_SCHEMA_PATH = Path(
    "schemas/armindex/a1.2-scientific-execution-adoption-inputs.v12.json"
)
RECEIPT_SCHEMA_PATH = Path(
    "schemas/armindex/a1.2-scientific-execution-adoption-inputs-receipt.v12.json"
)
RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-scientific-execution-adoption-inputs.receipt.v12.json"
)
V11_REQUEST_PATH = Path(
    "control/armindex/a1.2/scientific-execution-adoption-request.v11.json"
)
V11_RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-scientific-execution-adoption-request.receipt.v11.json"
)
PROVIDER_TEMPLATE_PATH = Path(
    "control/armindex/a1.2/provider-admission-input-template.v12.json"
)
BUDGET_PATH = Path("control/armindex/a1.2/whole-workload-budget-admission.v12.json")
OWNER_RECEIPT_CONTRACT_PATH = Path(
    "control/owner-local/a1.2-adoption-input-receipt-contract.v12.json"
)
COMPILED_BINDINGS_CONTRACT_PATH = Path(
    "control/owner-local/a1.2-compiled-program-bindings-contract.v12.json"
)
PUBLICATION_PATH = Path("control/armindex/a1.2/publication-impact-contract.v12.json")
DISPOSITION_PATH = Path("control/armindex/a1.2/instance-disposition-policy.v12.json")
WATCHDOG_CONTRACT_PATH = Path(
    "control/armindex/a1.2/watchdog-provider-destroy-dry-run-contract.v12.json"
)
LEDGER_PATH = Path(
    "control/armindex/a1.2/scientific-execution-adoption-inputs-ledger.v12.jsonl"
)

V11_REQUEST_FILE_SHA256 = (
    "d5eaec8bf7c78ec9a21f43a5f94f89ccc314eef79bad9b0e7629a1a7e902851d"
)
V11_REQUEST_SHA256 = "2e95bf70d4843dadac03b442cb231573f73ec05a65884a70ac42d9713f52b7db"
V11_RECEIPT_FILE_SHA256 = (
    "e14736fd1cab22cf8602bba2b3d59ecab2ccca3137a81c4fe295e95e22bc16c2"
)
V11_RECEIPT_SHA256 = "6de14783873a8405d67a21236252a0d93269601b494366b686fe348ac7308bc2"
_HASH = re.compile(r"^[a-f0-9]{64}$")
_SECRET = re.compile(
    r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\bsk-[A-Za-z0-9_-]{12,}|"
    r"\bBearer\s+[A-Za-z0-9._~+/-]{12,})",
    re.IGNORECASE,
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path.as_posix()}")
    return value


def _json(value: Mapping[str, Any]) -> str:
    return (
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + "\n"
    )


def _finalize(body: dict[str, Any], field: str) -> dict[str, Any]:
    return {**body, field: canonical_sha256(body)}


def _check_hash(value: Mapping[str, Any], field: str) -> None:
    if value.get(field) != canonical_sha256(
        {key: item for key, item in value.items() if key != field}
    ):
        raise ValueError(f"{field} mismatch")


def _validate_ledger_entries(entries: list[Mapping[str, Any]]) -> dict[str, Any]:
    if not entries:
        raise ValueError("v12 ledger must contain at least one entry")
    previous: str | None = None
    seen_ids: set[str] = set()
    previous_timestamp = ""
    for index, entry in enumerate(entries):
        entry_id = entry.get("entry_id")
        entry_hash = entry.get("entry_sha256")
        timestamp = entry.get("timestamp_utc")
        if not isinstance(entry_id, str) or not entry_id or entry_id in seen_ids:
            raise ValueError(f"v12 ledger entry {index} has an invalid or duplicate ID")
        if entry.get("previous_entry_sha256") != previous:
            raise ValueError(f"v12 ledger chain mismatch at {entry_id}")
        if not isinstance(timestamp, str) or timestamp <= previous_timestamp:
            raise ValueError(f"v12 ledger timestamp order mismatch at {entry_id}")
        body = {key: value for key, value in entry.items() if key != "entry_sha256"}
        if entry_hash != canonical_sha256(body):
            raise ValueError(f"v12 ledger entry hash mismatch at {entry_id}")
        seen_ids.add(entry_id)
        previous = str(entry_hash)
        previous_timestamp = timestamp
    return {"entry_count": len(entries), "head_sha256": previous}


def _verify_ledger(root: Path) -> dict[str, Any]:
    entries: list[Mapping[str, Any]] = []
    for line_number, line in enumerate(
        (root / LEDGER_PATH).read_text(encoding="utf-8").splitlines(), start=1
    ):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"invalid v12 ledger JSON at line {line_number}"
            ) from error
        if not isinstance(value, Mapping):
            raise ValueError(f"v12 ledger object required at line {line_number}")
        _safe(value)
        entries.append(value)
    return _validate_ledger_entries(entries)


def _schema(root: Path, path: Path, value: Mapping[str, Any]) -> None:
    errors = sorted(
        Draft202012Validator(_load(root / path)).iter_errors(value),
        key=lambda error: list(error.path),
    )
    if errors:
        raise ValueError(
            f"schema failure at {list(errors[0].path)}: {errors[0].message}"
        )


def _safe(value: Mapping[str, Any]) -> None:
    assert_aggregate_only(value)
    text = json.dumps(value, ensure_ascii=True, sort_keys=True)
    if _SECRET.search(text):
        raise ValueError("secret-like material found in v12 adoption inputs")
    if re.search(r"(?:[A-Za-z]:\\|/Users/|/home/|\\\\[^\\]+\\)", text):
        raise ValueError("absolute personal path found in v12 adoption inputs")


def _binding(root: Path, path: Path, field: str | None = None) -> dict[str, Any]:
    value = _load(root / path)
    _safe(value)
    binding: dict[str, Any] = {
        "uri": path.as_posix(),
        "file_sha256": file_sha256(root / path),
    }
    if field is not None:
        observed = value.get(field)
        if not isinstance(observed, str) or _HASH.fullmatch(observed) is None:
            raise ValueError(f"missing self hash {field}: {path.as_posix()}")
        binding["self_sha256"] = observed
    return binding


def _verify_v11(root: Path) -> None:
    if file_sha256(root / V11_REQUEST_PATH) != V11_REQUEST_FILE_SHA256:
        raise ValueError("unchanged v11 request file hash mismatch")
    if file_sha256(root / V11_RECEIPT_PATH) != V11_RECEIPT_FILE_SHA256:
        raise ValueError("unchanged v11 receipt file hash mismatch")
    if _load(root / V11_REQUEST_PATH).get("request_sha256") != V11_REQUEST_SHA256:
        raise ValueError("unchanged v11 request self hash mismatch")
    if _load(root / V11_RECEIPT_PATH).get("receipt_sha256") != V11_RECEIPT_SHA256:
        raise ValueError("unchanged v11 receipt self hash mismatch")


def _verify_components(root: Path) -> None:
    _verify_v11(root)
    publication = _load(root / PUBLICATION_PATH)
    if (
        publication.get("analysis", {}).get("outcomes", {}).get("primary")
        != "out_recall_at_100"
    ):
        raise ValueError(
            "v12 publication contract does not bind OUT Recall@100 primary"
        )
    if publication.get("analysis", {}).get("outcomes", {}).get("secondary") != [
        "out_ndcg_at_100",
        "out_ndcg_at_10",
    ]:
        raise ValueError(
            "v12 publication contract does not bind required nDCG secondary outcomes"
        )
    if (
        publication.get("analysis", {})
        .get("candidate_selection", {})
        .get("max_cell_promotion_allowed")
        is not False
    ):
        raise ValueError("v12 publication contract permits max-cell promotion")
    disposition = _load(root / DISPOSITION_PATH)
    if (
        disposition.get("status") != "PENDING_LIVE_PROVIDER"
        or disposition.get("current_disposition") != "NO_LIVE_INSTANCE"
    ):
        raise ValueError(
            "v12 instance disposition must remain pending with no live instance"
        )
    provider = _load(root / PROVIDER_TEMPLATE_PATH)
    if (
        provider.get("status") != "PENDING_LIVE_PROVIDER"
        or provider.get("provider_contacted") is not False
    ):
        raise ValueError("v12 provider template must remain pending and uncontacted")
    budget = _load(root / BUDGET_PATH)
    if (
        budget.get("status") != "PENDING_LIVE_PROVIDER"
        or budget.get("admitted") is not False
    ):
        raise ValueError("v12 budget admission must remain pending and inadmissible")
    watchdog_status = watchdog_current_status(root)
    if (
        watchdog_status.get("actual_provider_destroy_capability")
        != "PENDING_LIVE_PROVIDER"
    ):
        raise ValueError("v12 watchdog must not claim live provider destroy capability")


def _contract(root: Path) -> dict[str, Any]:
    _verify_components(root)
    components = {
        "provider_admission_input_template": _binding(
            root, PROVIDER_TEMPLATE_PATH, "template_sha256"
        ),
        "whole_workload_budget_admission": _binding(
            root, BUDGET_PATH, "admission_sha256"
        ),
        "owner_local_receipt_contract": _binding(
            root, OWNER_RECEIPT_CONTRACT_PATH, "receipt_contract_sha256"
        ),
        "compiled_program_bindings_contract": _binding(
            root, COMPILED_BINDINGS_CONTRACT_PATH
        ),
        "publication_impact_contract": _binding(
            root, PUBLICATION_PATH, "contract_sha256"
        ),
        "instance_disposition_policy": _binding(root, DISPOSITION_PATH),
        "watchdog_provider_destroy_dry_run_contract": _binding(
            root, WATCHDOG_CONTRACT_PATH
        ),
    }
    body = {
        "schema_version": "myis.armindex-a1.2-scientific-execution-adoption-inputs.v12",
        "contract_id": REVISION_ID,
        "revision_id": REVISION_ID,
        "status": "LOCAL_PREPARATION_PASS_PENDING_OWNER_LOCAL_AND_LIVE_PROVIDER",
        "evidence_class": "scientific_execution_adoption_input_preparation",
        "scientific_authority": False,
        "claim_boundary": "Additive local-only preparation of adoption inputs for the unchanged v11 scientific request. It neither creates protected payloads nor contacts a provider, adopts execution, launches a workload, measures retrieval quality, opens Selection or Final, changes a model, or makes a publication claim.",
        "preserved_v11": {
            "request": {
                "uri": V11_REQUEST_PATH.as_posix(),
                "file_sha256": V11_REQUEST_FILE_SHA256,
                "self_sha256": V11_REQUEST_SHA256,
            },
            "receipt": {
                "uri": V11_RECEIPT_PATH.as_posix(),
                "file_sha256": V11_RECEIPT_FILE_SHA256,
                "self_sha256": V11_RECEIPT_SHA256,
            },
            "must_remain_unchanged": True,
        },
        "component_bindings": components,
        "required_owner_local_inputs": [
            "clean_pushed_execution_bundle_receipt",
            "aggregate_safe_protected_handoff_and_transfer_receipt",
            "validated_compiled_program_binding_set_25_of_25",
            "local_watchdog_and_provider_destroy_dry_run_receipt",
        ],
        "pending_live_provider_inputs": [
            "fresh_provider_identity",
            "fresh_all_fee_quote",
            "live_provider_admission_receipt",
        ],
        "authorization": {
            "provider_contact_allowed": False,
            "launch_allowed": False,
            "adopted_for_execution": False,
            "measured_retrieval_allowed": False,
            "selection_open": False,
            "final_open": False,
            "paid_api_allowed": False,
            "model_weight_changes_allowed": False,
        },
        "counters": {
            "measured_runs": 0,
            "selection_accesses": 0,
            "final_accesses": 0,
            "charged_usd": 0,
            "gpu_scientific_runs": 0,
        },
        "ready_for_live_adoption_goal": False,
        "next_authorized_action": "Prepare aggregate-safe Owner-local execution bundle, protected handoff and transfer receipts, all 25 compiled-program bindings with zero truncation, and a local watchdog/provider-destroy dry-run. Keep fresh provider identity and all-fee quote explicitly PENDING_LIVE_PROVIDER; do not contact a provider or adopt execution.",
    }
    return _finalize(body, "contract_sha256")


def _write_immutable(path: Path, value: Mapping[str, Any]) -> None:
    text = _json(value)
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise ValueError(f"immutable v12 artifact differs: {path.as_posix()}")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="")


def materialize(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    contract = _contract(root)
    _schema(root, CONTRACT_SCHEMA_PATH, contract)
    _check_hash(contract, "contract_sha256")
    _safe(contract)
    _write_immutable(root / CONTRACT_PATH, contract)
    return validate(repository_root)


def validate(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    expected = _contract(root)
    observed = _load(root / CONTRACT_PATH)
    if observed != expected:
        raise ValueError(
            "v12 adoption-input contract differs from deterministic preparation facts"
        )
    _schema(root, CONTRACT_SCHEMA_PATH, observed)
    _check_hash(observed, "contract_sha256")
    _safe(observed)
    ledger = _verify_ledger(root)
    return {
        "status": "PASS",
        "revision_id": REVISION_ID,
        "contract_file_sha256": file_sha256(root / CONTRACT_PATH),
        "contract_sha256": observed["contract_sha256"],
        "compiled_bindings_required": 25,
        "provider_status": "PENDING_LIVE_PROVIDER",
        "ready_for_live_adoption_goal": False,
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
        "charged_usd": 0,
        "ledger_entry_count": ledger["entry_count"],
        "ledger_head_sha256": ledger["head_sha256"],
    }


def _require_hashes(
    value: Mapping[str, Any], fields: tuple[str, ...], label: str
) -> None:
    for field in fields:
        if (
            not isinstance(value.get(field), str)
            or _HASH.fullmatch(str(value[field])) is None
        ):
            raise ValueError(f"{label} missing valid {field}")


def _require_git_object_ids(value: Mapping[str, Any]) -> None:
    for field in ("git_commit", "git_tree"):
        observed = value.get(field)
        if (
            not isinstance(observed, str)
            or re.fullmatch(r"[a-f0-9]{40}", observed) is None
        ):
            raise ValueError(f"execution bundle missing valid 40-hex {field}")


def _validate_binding_set(root: Path, value: Mapping[str, Any]) -> None:
    result = validate_binding_set(root, value)
    if result["status"] != "validated_owner_local_protected_compilation":
        raise ValueError("compiled bindings are not Owner-local validated")


def _validate_final_inputs(root: Path, inputs: Mapping[str, Any]) -> None:
    if set(inputs) != {
        "execution_bundle",
        "owner_local_receipt",
        "compiled_bindings",
        "watchdog_destroy_dry_run",
    }:
        raise ValueError("finalization inputs are incomplete or contain unsafe keys")
    _safe(inputs)
    bundle = inputs["execution_bundle"]
    owner = inputs["owner_local_receipt"]
    watchdog = inputs["watchdog_destroy_dry_run"]
    if (
        not isinstance(bundle, Mapping)
        or not isinstance(owner, Mapping)
        or not isinstance(watchdog, Mapping)
    ):
        raise ValueError("finalization inputs must be objects")
    if (
        bundle.get("clean_worktree") is not True
        or bundle.get("pushed_to_origin_main") is not True
    ):
        raise ValueError("execution bundle must bind a clean pushed identity")
    _require_git_object_ids(bundle)
    _require_hashes(
        bundle, ("frozen_bundle_sha256", "receipt_sha256"), "execution bundle"
    )
    if owner.get("status") != "PASS":
        raise ValueError("Owner-local handoff and transfer receipt is not PASS")
    _require_hashes(
        owner,
        (
            "handoff_receipt_sha256",
            "protected_transfer_manifest_sha256",
            "receipt_sha256",
        ),
        "Owner-local receipt",
    )
    _validate_binding_set(root, inputs["compiled_bindings"])
    validate_watchdog_result(root, watchdog)
    if watchdog.get("policy_id") != WATCHDOG_REVISION_ID:
        raise ValueError("watchdog dry-run revision mismatch")
    if watchdog.get("policy_file_sha256") != file_sha256(root / WATCHDOG_POLICY_PATH):
        raise ValueError("watchdog dry-run policy binding mismatch")


def finalize(repository_root: Path, inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Build, but do not persist, a final local-input receipt after strict validation."""
    root = repository_root.resolve()
    validated = validate(root)
    _validate_final_inputs(root, inputs)
    binding_set = inputs["compiled_bindings"]
    assert isinstance(binding_set, Mapping)
    body = {
        "schema_version": "myis.armindex-a1.2-scientific-execution-adoption-inputs-receipt.v12",
        "receipt_id": REVISION_ID,
        "revision_id": REVISION_ID,
        "status": "LOCAL_INPUTS_VALIDATED_PENDING_LIVE_PROVIDER",
        "evidence_class": "scientific_execution_adoption_input_preparation",
        "scientific_authority": False,
        "claim_boundary": "Validated aggregate-safe local and Owner-local adoption inputs for unchanged v11. Fresh provider identity, all-fee quote, live admission, adoption, launch, measurement, Selection, and Final remain outside this receipt.",
        "contract": {
            "uri": CONTRACT_PATH.as_posix(),
            "file_sha256": validated["contract_file_sha256"],
            "contract_sha256": validated["contract_sha256"],
        },
        "execution_bundle": dict(inputs["execution_bundle"]),
        "owner_local_receipt": dict(inputs["owner_local_receipt"]),
        "compiled_bindings": {
            "binding_set_sha256": binding_set["binding_set_sha256"],
            "binding_count": 25,
            "truncation_count": 0,
            "overlength_count": 0,
        },
        "watchdog_destroy_dry_run": dict(inputs["watchdog_destroy_dry_run"]),
        "pending_live_provider": [
            "fresh_provider_identity",
            "fresh_all_fee_quote",
            "whole_workload_live_budget_admission",
            "live_provider_admission_receipt",
        ],
        "ready_for_live_adoption_goal": True,
        "authorization": {
            "provider_contact_allowed": False,
            "launch_allowed": False,
            "adopted_for_execution": False,
            "measured_retrieval_allowed": False,
        },
        "counters": {
            "measured_runs": 0,
            "selection_accesses": 0,
            "final_accesses": 0,
            "charged_usd": 0,
        },
        "next_authorized_action": "A separately authorized live-adoption goal may obtain a fresh provider identity and all-fee quote, evaluate whole-workload admission, and keep all execution authority locked until explicit adoption succeeds.",
    }
    receipt = _finalize(body, "receipt_sha256")
    _schema(root, RECEIPT_SCHEMA_PATH, receipt)
    _check_hash(receipt, "receipt_sha256")
    _safe(receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-scientific-adoption-inputs-v12")
    parser.add_argument("command", choices=("materialize", "validate", "finalize"))
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--inputs", type=Path)
    args = parser.parse_args()
    if args.command == "materialize":
        result = materialize(args.repository_root)
    elif args.command == "validate":
        result = validate(args.repository_root)
    else:
        if args.inputs is None:
            parser.error("--inputs is required for finalize")
        result = finalize(args.repository_root, _load(args.inputs))
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
