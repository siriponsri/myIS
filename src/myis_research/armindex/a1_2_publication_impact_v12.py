"""Validate the additive A1.2 publication-impact preregistration v12.

The contract is deliberately analysis-only.  It binds the unchanged v11
scientific request and makes no provider, execution, or publication claim.
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


REVISION_ID = "a1.2-publication-impact-preregistration-v12"
CONTRACT_PATH = Path("control/armindex/a1.2/publication-impact-contract.v12.json")
SCHEMA_PATH = Path("schemas/armindex/a1.2-publication-impact-contract.v12.json")
V11_REQUEST_PATH = Path("control/armindex/a1.2/scientific-execution-adoption-request.v11.json")
V11_RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-scientific-execution-adoption-request.receipt.v11.json"
)
V11_REQUEST_FILE_SHA256 = "d5eaec8bf7c78ec9a21f43a5f94f89ccc314eef79bad9b0e7629a1a7e902851d"
V11_REQUEST_SELF_SHA256 = "2e95bf70d4843dadac03b442cb231573f73ec05a65884a70ac42d9713f52b7db"
V11_RECEIPT_FILE_SHA256 = "e14736fd1cab22cf8602bba2b3d59ecab2ccca3137a81c4fe295e95e22bc16c2"
V11_RECEIPT_SELF_SHA256 = "6de14783873a8405d67a21236252a0d93269601b494366b686fe348ac7308bc2"

_SECRET = re.compile(
    r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\bsk-[A-Za-z0-9_-]{12,}|"
    r"\bBearer\s+[A-Za-z0-9._~+/-]{12,})",
    re.IGNORECASE,
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _check_self_hash(value: Mapping[str, Any]) -> None:
    observed = value.get("contract_sha256")
    expected = canonical_sha256(
        {key: item for key, item in value.items() if key != "contract_sha256"}
    )
    if observed != expected:
        raise ValueError("contract_sha256 mismatch")


def _validate_schema(value: Mapping[str, Any], root: Path) -> None:
    schema = _load(root / SCHEMA_PATH)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda item: list(item.path))
    if errors:
        raise ValueError(f"schema failure at {list(errors[0].path)}: {errors[0].message}")


def _validate_safe(value: Mapping[str, Any]) -> None:
    assert_aggregate_only(value)
    text = json.dumps(value, ensure_ascii=True, sort_keys=True)
    if _SECRET.search(text):
        raise ValueError("secret-like material found in v12 publication contract")
    if re.search(r"(?:[A-Za-z]:\\\\|/Users/|/home/|\\\\\\\\[^\\\\]+\\\\)", text):
        raise ValueError("absolute personal path found in v12 publication contract")


def _validate_v11_binding(value: Mapping[str, Any], root: Path) -> None:
    binding = value["v11_binding"]
    if file_sha256(root / V11_REQUEST_PATH) != V11_REQUEST_FILE_SHA256:
        raise ValueError("unchanged v11 request file hash mismatch")
    if file_sha256(root / V11_RECEIPT_PATH) != V11_RECEIPT_FILE_SHA256:
        raise ValueError("unchanged v11 receipt file hash mismatch")
    request = _load(root / V11_REQUEST_PATH)
    receipt = _load(root / V11_RECEIPT_PATH)
    if request.get("request_sha256") != V11_REQUEST_SELF_SHA256:
        raise ValueError("unchanged v11 request self hash mismatch")
    if receipt.get("receipt_sha256") != V11_RECEIPT_SELF_SHA256:
        raise ValueError("unchanged v11 receipt self hash mismatch")
    expected = {
        "request": {
            "uri": V11_REQUEST_PATH.as_posix(),
            "file_sha256": V11_REQUEST_FILE_SHA256,
            "self_sha256": V11_REQUEST_SELF_SHA256,
        },
        "receipt": {
            "uri": V11_RECEIPT_PATH.as_posix(),
            "file_sha256": V11_RECEIPT_FILE_SHA256,
            "self_sha256": V11_RECEIPT_SELF_SHA256,
        },
        "v11_request_must_remain_unchanged": True,
    }
    if binding != expected:
        raise ValueError("v12 v11 binding differs from immutable v11 identity")


def _validate_semantics(value: Mapping[str, Any]) -> None:
    if value["authorization"] != {
        "adopted_for_execution": False,
        "launch_allowed": False,
        "measured_retrieval_allowed": False,
        "provider_contact_allowed": False,
        "selection_open": False,
        "final_open": False,
    }:
        raise ValueError("v12 must not change execution authorization")
    if value["counters"] != {
        "measured_runs": 0,
        "selection_accesses": 0,
        "final_accesses": 0,
        "charged_usd": 0,
    }:
        raise ValueError("v12 must retain zero resource and exposure counters")

    analysis = value["analysis"]
    outcomes = analysis["outcomes"]
    if outcomes["primary"] != "out_recall_at_100":
        raise ValueError("OUT Recall@100 must remain the sole primary outcome")
    if outcomes["secondary"] != ["out_ndcg_at_100", "out_ndcg_at_10"]:
        raise ValueError("nDCG outcomes must remain ordered secondary outcomes")
    if analysis["development_confirmation_boundary"]["final_872_role"] != "sole_confirmatory_evaluation":
        raise ValueError("Final-872 must remain the sole confirmatory evaluation")
    if analysis["development_confirmation_boundary"]["selection_125_role"] != "one_time_finalist_selection_not_confirmation":
        raise ValueError("Selection-125 cannot be treated as confirmation")
    if analysis["candidate_selection"]["max_cell_promotion_allowed"] is not False:
        raise ValueError("max-cell promotion must be forbidden")
    if analysis["candidate_exposure"]["oracle_metrics_role"] != "frozen_pool_diagnostic_not_deployed_result":
        raise ValueError("oracle metrics must remain diagnostic only")
    if analysis["statistics"]["superiority_rule"] != "paired_bootstrap_95ci_lower_gt_zero":
        raise ValueError("superiority rule is not preregistered")
    if analysis["statistics"]["bootstrap_resamples"] != 10000:
        raise ValueError("paired bootstrap count must be exactly 10000")


def validate(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    value = _load(root / CONTRACT_PATH)
    _validate_schema(value, root)
    _check_self_hash(value)
    _validate_safe(value)
    _validate_v11_binding(value, root)
    _validate_semantics(value)
    return {
        "status": "PASS",
        "revision_id": REVISION_ID,
        "contract_file_sha256": file_sha256(root / CONTRACT_PATH),
        "contract_sha256": value["contract_sha256"],
        "primary_outcome": value["analysis"]["outcomes"]["primary"],
        "secondary_outcomes": value["analysis"]["outcomes"]["secondary"],
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_runs": 0,
        "charged_usd": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-publication-impact-v12")
    parser.add_argument("validate", nargs="?", default="validate", choices=("validate",))
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    args = parser.parse_args()
    print(json.dumps(validate(args.repository_root), ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
