"""Additive provider closeout for the completed A1.2 v9 synthetic preflight.

The v9 result remains immutable and continues to record that provider
destruction was pending when it was written. This v10 receipt binds the later
Owner-local disposition evidence without authorizing scientific execution.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a1_2_live_preflight_result_v9 import (
    ATTEMPT_ID,
    RECEIPT_PATH as V9_RESULT_RECEIPT_PATH,
    validate_result as validate_v9_result,
)


REVISION_ID = "a1.2-provider-closeout-result-v10"
RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-provider-closeout-result.receipt.v10.json"
)
SCHEMA_PATH = Path("schemas/armindex/a1.2-provider-closeout-result.v10.json")
OWNER_RECEIPT_RELATIVE_PATH = Path(
    "../04_Owner_Stores/a1.2-vast-20260806/receipts/"
    "VAST_PROVIDER_CLOSEOUT_V10.json"
)
OWNER_RECEIPT_SAFE_URI = (
    "owner-store/a1.2-vast-20260806/receipts/VAST_PROVIDER_CLOSEOUT_V10.json"
)
V9_RESULT_FILE_SHA256 = "52d1d892c4ce034e3d4b0887a5bddbb362d9747c3b343e766ad2a4302c3f13d6"
V9_RESULT_SELF_SHA256 = "f8969e55225b4fa567c94079b6bffc834e1951268f626bdad7754104294df510"
OWNER_RECEIPT_FILE_SHA256 = "a803a84f5cb7c39165ce841c10339359dff3297981e2ebe5b42128418619f0d4"
OWNER_RECEIPT_SELF_SHA256 = "24a8f7340aa9b8cf15188855f5c635c801efbc2df08cd9625bc4af572da5da71"


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _body() -> dict[str, Any]:
    return {
        "schema_version": "myis.armindex-a1.2-provider-closeout-result.v10",
        "receipt_id": REVISION_ID,
        "revision_id": REVISION_ID,
        "status": "PASS",
        "evidence_class": "owner_local_provider_closeout",
        "scientific_authority": False,
        "claim_boundary": (
            "Provider-lifecycle closeout only, supported by Owner provider-UI "
            "attestation plus endpoint unreachability; no independent provider API "
            "record, retrieval-quality result, execution adoption, or publication claim."
        ),
        "predecessor": {
            "receipt_uri": V9_RESULT_RECEIPT_PATH.as_posix(),
            "receipt_file_sha256": V9_RESULT_FILE_SHA256,
            "receipt_self_sha256": V9_RESULT_SELF_SHA256,
            "attempt_id": ATTEMPT_ID,
        },
        "owner_evidence": {
            "receipt_uri": OWNER_RECEIPT_SAFE_URI,
            "receipt_file_sha256": OWNER_RECEIPT_FILE_SHA256,
            "receipt_self_sha256": OWNER_RECEIPT_SELF_SHA256,
            "source": "active_codex_thread_owner_message_20260807",
        },
        "provider_closeout": {
            "provider_label": "Vast",
            "instance_id": "47023328",
            "owner_disposition": "destroyed_and_provider_absence_verified",
            "provider_destroy_invoked": True,
            "provider_instance_absent_verified": True,
            "provider_destruction_proven": True,
            "endpoint_observation": "connection_refused",
            "provider_api_query_performed": False,
            "independent_provider_api_record_available": False,
            "guest_poweroff_is_provider_destruction": False,
            "proof_basis": [
                "owner_provider_ui_attestation",
                "post_confirmation_endpoint_unreachable",
            ],
            "limitation": (
                "The Owner reported destruction in the provider UI and the prior SSH "
                "endpoint immediately refused a connection; no independent Vast API or "
                "CLI destruction record was queried or retained."
            ),
        },
        "pending_provider_checks": [],
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
        "selection_accesses": 0,
        "final_accesses": 0,
        "charged_usd": 0,
        "next_authorized_action": (
            "Prepare a separately authorized A1.2 scientific execution and adoption "
            "goal on local CPU only; do not open a provider or begin measured work."
        ),
    }


def _validate_payload(receipt: Mapping[str, Any], schema: Mapping[str, Any]) -> None:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(receipt),
        key=lambda item: list(item.path),
    )
    if errors:
        raise ValueError(f"provider closeout schema failure: {errors[0].message}")
    expected_hash = canonical_sha256(
        {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    )
    if receipt.get("receipt_sha256") != expected_hash:
        raise ValueError("provider closeout self-hash mismatch")
    assert_aggregate_only(receipt)


def _validate_expected(receipt: Mapping[str, Any]) -> None:
    observed = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    if observed != _body():
        raise ValueError("provider closeout payload differs from frozen disposition facts")


def _validate_owner_receipt(root: Path) -> None:
    owner_path = (root / OWNER_RECEIPT_RELATIVE_PATH).resolve()
    if not owner_path.is_file():
        raise ValueError("sanitized Owner-local provider closeout receipt is missing")
    if file_sha256(owner_path) != OWNER_RECEIPT_FILE_SHA256:
        raise ValueError("sanitized Owner-local provider closeout file hash mismatch")
    payload = json.loads(owner_path.read_text(encoding="utf-8"))
    observed_self_hash = payload.get("receipt_sha256")
    expected_self_hash = canonical_sha256(
        {key: value for key, value in payload.items() if key != "receipt_sha256"}
    )
    if observed_self_hash != OWNER_RECEIPT_SELF_SHA256 or observed_self_hash != expected_self_hash:
        raise ValueError("sanitized Owner-local provider closeout self-hash mismatch")
    if payload.get("owner_confirmation", {}).get("disposition") != "destroyed":
        raise ValueError("Owner-local provider disposition is not destroyed")
    if payload.get("endpoint_observation", {}).get("status") != "connection_refused":
        raise ValueError("Owner-local endpoint absence observation is missing")


def materialize_closeout(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    validate_v9_result(root)
    if file_sha256(root / V9_RESULT_RECEIPT_PATH) != V9_RESULT_FILE_SHA256:
        raise ValueError("v9 result file hash mismatch")
    _validate_owner_receipt(root)
    body = _body()
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    schema = json.loads((root / SCHEMA_PATH).read_text(encoding="utf-8"))
    _validate_payload(receipt, schema)
    target = root / RECEIPT_PATH
    if target.exists() and target.read_text(encoding="utf-8") != _json_text(receipt):
        raise ValueError(f"immutable provider closeout differs: {RECEIPT_PATH.as_posix()}")
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_json_text(receipt), encoding="utf-8", newline="")
    return validate_closeout(root)


def validate_closeout(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    v9_validation = validate_v9_result(root)
    if file_sha256(root / V9_RESULT_RECEIPT_PATH) != V9_RESULT_FILE_SHA256:
        raise ValueError("v9 result file hash mismatch")
    if v9_validation.get("receipt_self_sha256") != V9_RESULT_SELF_SHA256:
        raise ValueError("v9 result self-hash mismatch")
    receipt = json.loads((root / RECEIPT_PATH).read_text(encoding="utf-8"))
    schema = json.loads((root / SCHEMA_PATH).read_text(encoding="utf-8"))
    _validate_payload(receipt, schema)
    _validate_expected(receipt)
    return {
        "status": receipt["status"],
        "revision_id": receipt["revision_id"],
        "receipt_sha256": file_sha256(root / RECEIPT_PATH),
        "receipt_self_sha256": receipt["receipt_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-provider-closeout-v10")
    parser.add_argument("command", choices=("materialize", "validate"))
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    args = parser.parse_args()
    result = (
        materialize_closeout(args.repository_root)
        if args.command == "materialize"
        else validate_closeout(args.repository_root)
    )
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
