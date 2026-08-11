"""Additive lineage bridge for the frozen A1.2 v16 evaluator builder.

The measured bundle and frozen evaluator remain unchanged. This bridge repairs
two engineering mismatches: live adoption binds the complete admitted quote
and the static safe-return contract, while the original manifest builder
recomputes the quote from a reduced body and compares the static contract hash
to the dynamic result-manifest hash. Every other validation stays frozen.
"""

from __future__ import annotations

import argparse
import json
import math
import tarfile
import threading
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from . import (
    a1_2_owner_local_evaluation_manifest_builder_v16 as frozen,
)

_BRIDGE_LOCK = threading.Lock()
_CONTRACT_PATH = Path("control/armindex/a1.2/engineering-execution-contract.v16.json")
_BASE_SOURCE_PATH = Path(
    "src/myis_research/armindex/a1_2_owner_local_evaluation_manifest_builder_v16.py"
)
_SAFE_RETURN_CONTRACT_PATH = Path(
    "control/armindex/a1.2/scientific-safe-return-contract.v16.json"
)
_ADOPTION_INPUTS_PATH = Path(
    "control/armindex/a1.2/scientific-execution-adoption-inputs.v15.json"
)
_MODEL_LOCKSET_PATH = Path("control/armindex/a1.2/model-lockset.v1.json")
_PROTECTED_COMPILER_PATH = Path(
    "control/armindex/a1.2/protected-compiler-integration.v15.json"
)
_PROTECTED_COMPILER_AUDIT_PATH = Path(
    "outputs/audits/armindex/a1.2-protected-compiler-integration-20260809-v15.json"
)


class OwnerLocalEvaluationManifestQuoteBridgeV16Error(ValueError):
    """Raised when quote lineage cannot be proven without changing adoption."""


def _load(path: Path, *, role: str) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if path.is_symlink() or not resolved.is_file():
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(f"{role} is unsafe")
    value = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(f"{role} must be an object")
    return value


def _self_hash(value: Mapping[str, Any], *, role: str) -> str:
    observed = value.get("receipt_sha256")
    expected = canonical_sha256(
        {key: item for key, item in value.items() if key != "receipt_sha256"}
    )
    if observed != expected:
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(
            f"{role} self-hash mismatch"
        )
    return str(observed)


def _validate_frozen_base(repository_root: Path) -> None:
    root = repository_root.resolve(strict=True)
    contract = _load(root / _CONTRACT_PATH, role="engineering execution contract")
    support = contract.get("support_sources")
    source = support.get("evaluation_manifest_builder") if isinstance(support, dict) else None
    if not isinstance(source, dict) or source.get("path") != _BASE_SOURCE_PATH.as_posix():
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(
            "engineering contract does not bind the frozen manifest builder"
        )
    if file_sha256(root / _BASE_SOURCE_PATH) != source.get("sha256"):
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(
            "frozen manifest builder differs from the engineering contract"
        )


def _validate_quote_bridge(
    repository_root: Path,
    quote_receipt_path: Path,
    *,
    admission: Mapping[str, Any],
    adoption: Mapping[str, Any],
    attempt_id: str,
    budget_input_path: Path,
    budget_receipt_path: Path,
    provider_observation_path: Path,
    quote_lineage_path: Path,
) -> dict[str, Any]:
    receipt = _load(quote_receipt_path, role="admitted all-fee quote receipt")
    frozen._schema(
        repository_root,
        frozen.QUOTE_SCHEMA_PATH,
        receipt,
        role="admitted all-fee quote receipt",
    )
    frozen._self_hash(
        receipt, "receipt_sha256", role="admitted all-fee quote receipt"
    )
    if (
        receipt.get("attempt_id") != attempt_id
        or receipt.get("provider_admission_receipt_sha256")
        != admission.get("receipt_sha256")
        or receipt.get("quote_sha256")
        != adoption.get("adoption_bindings", {}).get("all_fee_quote")
    ):
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(
            "admitted quote differs from frozen admission or adoption"
        )

    budget_input = _load(budget_input_path, role="budget input")
    budget_receipt = _load(budget_receipt_path, role="budget admission receipt")
    provider_observation = _load(
        provider_observation_path, role="provider quote observation"
    )
    lineage = _load(quote_lineage_path, role="admitted quote lineage receipt")
    _self_hash(budget_receipt, role="budget admission receipt")
    _self_hash(lineage, role="admitted quote lineage receipt")
    try:
        assert_aggregate_only(lineage)
    except ValueError as error:
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(str(error)) from error

    quote = budget_input.get("quote")
    ttl_hours = budget_receipt.get("ttl_hours")
    if not isinstance(quote, dict) or type(ttl_hours) is not int or ttl_hours <= 0:
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(
            "budget quote or admitted TTL is invalid"
        )
    if (
        budget_receipt.get("input_sha256") != canonical_sha256(budget_input)
        or budget_receipt.get("status") != "PASS_BUDGET_ADMISSION_LOCKED"
        or budget_receipt.get("admitted") is not True
        or admission.get("budget_admission_receipt_sha256")
        != budget_receipt.get("receipt_sha256")
    ):
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(
            "budget lineage differs from provider admission"
        )
    quote_sha256 = canonical_sha256(quote)
    if quote_sha256 != receipt.get("quote_sha256"):
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(
            "complete admitted quote hash differs from execution adoption"
        )
    try:
        rate = float(receipt["all_fee_usd_per_hour"])
        derived_rate = float(quote["compute_hourly_rate_usd"]) + float(
            quote["storage_fee_usd"]
        ) / ttl_hours
        observed_rate = float(provider_observation["dph_total"])
    except (KeyError, TypeError, ValueError) as error:
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(
            "all-fee rate lineage is invalid"
        ) from error
    if (
        not math.isfinite(rate)
        or rate < 0
        or abs(rate - derived_rate) > 1e-12
        or abs(rate - observed_rate) > 1e-12
    ):
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(
            "all-fee rate does not derive from admitted quote evidence"
        )

    expected_lineage = {
        "provider_admission_receipt_sha256": admission.get("receipt_sha256"),
        "execution_adoption_receipt_sha256": adoption.get("receipt_sha256"),
        "budget_input_file_sha256": file_sha256(budget_input_path.resolve(strict=True)),
        "budget_receipt_sha256": budget_receipt.get("receipt_sha256"),
        "provider_observation_file_sha256": file_sha256(
            provider_observation_path.resolve(strict=True)
        ),
        "quote_sha256": quote_sha256,
        "all_fee_usd_per_hour": rate,
        "admitted_quote_receipt_sha256": receipt.get("receipt_sha256"),
    }
    if any(lineage.get(key) != value for key, value in expected_lineage.items()):
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(
            "admitted quote lineage receipt is incomplete or inconsistent"
        )
    return receipt


def _validate_safe_return_bridge(
    repository_root: Path,
    archive: Path,
    *,
    adoption: Mapping[str, Any],
) -> dict[str, Any]:
    root = repository_root.resolve(strict=True)
    contract = root / _SAFE_RETURN_CONTRACT_PATH
    if file_sha256(contract.resolve(strict=True)) != adoption.get(
        "adoption_bindings", {}
    ).get("safe_return"):
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(
            "safe-return contract differs from execution adoption"
        )
    try:
        facts = frozen.validate_safe_return_archive(archive)
        with tarfile.open(archive, "r:gz") as bundle:
            member = bundle.extractfile("safe-return-manifest.v16.json")
            if member is None:
                raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(
                    "safe-return manifest disappeared"
                )
            manifest = json.loads(member.read().decode("ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        if isinstance(error, OwnerLocalEvaluationManifestQuoteBridgeV16Error):
            raise
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(
            "safe-return archive validation failed"
        ) from error
    if not isinstance(manifest, dict):
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(
            "safe-return manifest is invalid"
        )
    bindings = adoption["adoption_bindings"]
    for archive_key, binding_key in (
        ("transfer_manifest_sha256", "transfer"),
        ("split_commitment_sha256", "split"),
        ("ephemeral_token_map_sha256", "token_map"),
    ):
        if manifest.get(archive_key) != bindings.get(binding_key):
            raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(
                "safe-return lineage differs from execution adoption"
            )
    ranking_sha256_by_cell = {
        f"{item.get('arm_id')}--{item.get('program_id')}": item.get("sha256")
        for item in manifest.get("members", [])
        if isinstance(item, Mapping) and item.get("kind") == "ranking"
    }
    if set(ranking_sha256_by_cell) != set(frozen.CELL_IDS):
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(
            "safe-return ranking topology is incomplete"
        )
    for cell, ranking_sha256 in ranking_sha256_by_cell.items():
        frozen._sha(ranking_sha256, role=f"safe-return ranking {cell}")
    facts["ranking_sha256_by_cell"] = ranking_sha256_by_cell
    return facts


def _validate_control_binding_bridge(
    repository_root: Path,
    lineage_receipt_path: Path,
    *,
    adoption: Mapping[str, Any],
) -> None:
    root = repository_root.resolve(strict=True)
    lineage = _load(lineage_receipt_path, role="execution adoption lineage receipt")
    _self_hash(lineage, role="execution adoption lineage receipt")
    compiler_audit = _load(
        root / _PROTECTED_COMPILER_AUDIT_PATH,
        role="protected compiler integration audit",
    )
    audit_sha256 = compiler_audit.get("audit_sha256")
    if audit_sha256 != canonical_sha256(
        {key: item for key, item in compiler_audit.items() if key != "audit_sha256"}
    ):
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(
            "protected compiler integration audit self-hash mismatch"
        )
    try:
        assert_aggregate_only(lineage)
        assert_aggregate_only(compiler_audit)
    except ValueError as error:
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(str(error)) from error
    bindings = adoption.get("adoption_bindings")
    protected_receipts = compiler_audit.get("protected_receipts")
    if not isinstance(bindings, Mapping) or not isinstance(protected_receipts, Mapping):
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(
            "control binding lineage is incomplete"
        )
    expected = {
        "adoption_inputs": file_sha256(root / _ADOPTION_INPUTS_PATH),
        "model_lockset": lineage.get("model_lockset_sha256"),
        "protected_compiler": protected_receipts.get("compiler_receipt_sha256"),
    }
    if (
        lineage.get("status") != "PASS_EXECUTION_ADOPTION"
        or lineage.get("measured_retrieval_allowed") is not True
        or lineage.get("selection_allowed") is not False
        or lineage.get("final_allowed") is not False
        or lineage.get("adoption_inputs_sha256") != expected["adoption_inputs"]
        or lineage.get("protected_compiler_receipt_sha256")
        != expected["protected_compiler"]
        or lineage.get("binding_set_sha256")
        != bindings.get("compiled_bindings_25_of_25")
        or protected_receipts.get("binding_set_sha256")
        != bindings.get("compiled_bindings_25_of_25")
        or any(bindings.get(key) != value for key, value in expected.items())
    ):
        raise OwnerLocalEvaluationManifestQuoteBridgeV16Error(
            "frozen control lineage differs from execution adoption"
        )


def build_evaluation_manifest(
    *,
    safe_return_archive: Path,
    combined_output_root: Path,
    protected_root: Path,
    input_manifest_path: Path,
    adoption_receipt_path: Path,
    bundle_receipt_path: Path,
    provider_admission_receipt_path: Path,
    admitted_quote_receipt_path: Path,
    budget_input_path: Path,
    budget_receipt_path: Path,
    provider_observation_path: Path,
    quote_lineage_path: Path,
    control_binding_lineage_path: Path,
    promotion_policy_path: Path,
    repository_root: Path,
    output_name: str = "evaluation-input.v16.json",
) -> dict[str, Any]:
    """Run the frozen builder with its two impossible lineage checks substituted."""

    repository = repository_root.resolve(strict=True)
    _validate_frozen_base(repository)

    def quote_validator(
        root: Path,
        path: Path,
        *,
        admission: Mapping[str, Any],
        adoption: Mapping[str, Any],
        attempt_id: str,
    ) -> dict[str, Any]:
        return _validate_quote_bridge(
            root,
            path,
            admission=admission,
            adoption=adoption,
            attempt_id=attempt_id,
            budget_input_path=budget_input_path,
            budget_receipt_path=budget_receipt_path,
            provider_observation_path=provider_observation_path,
            quote_lineage_path=quote_lineage_path,
        )

    def safe_return_validator(
        archive: Path,
        *,
        adoption: Mapping[str, Any],
    ) -> dict[str, Any]:
        return _validate_safe_return_bridge(
            repository,
            archive,
            adoption=adoption,
        )

    def controls_validator(
        root: Path,
        adoption: Mapping[str, Any],
    ) -> tuple[dict[str, str], dict[str, str], dict[str, str], str, str]:
        _validate_control_binding_bridge(
            root,
            control_binding_lineage_path,
            adoption=adoption,
        )
        bridged_adoption = dict(adoption)
        bridged_bindings = dict(adoption["adoption_bindings"])
        bridged_bindings.update(
            {
                "adoption_inputs": _load(
                    root / _ADOPTION_INPUTS_PATH,
                    role="scientific execution adoption inputs",
                )["contract_sha256"],
                "model_lockset": _load(
                    root / _MODEL_LOCKSET_PATH,
                    role="model lockset",
                )["lockset_sha256"],
                "protected_compiler": _load(
                    root / _PROTECTED_COMPILER_PATH,
                    role="protected compiler integration",
                )["contract_sha256"],
            }
        )
        bridged_adoption["adoption_bindings"] = bridged_bindings
        return original_controls(root, bridged_adoption)

    with _BRIDGE_LOCK:
        original_quote = frozen._quote
        original_safe_return = frozen._safe_return_bindings
        original_controls = frozen._controls
        frozen._quote = quote_validator
        frozen._safe_return_bindings = safe_return_validator
        frozen._controls = controls_validator
        try:
            return frozen.build_evaluation_manifest(
                safe_return_archive=safe_return_archive,
                combined_output_root=combined_output_root,
                protected_root=protected_root,
                input_manifest_path=input_manifest_path,
                adoption_receipt_path=adoption_receipt_path,
                bundle_receipt_path=bundle_receipt_path,
                provider_admission_receipt_path=provider_admission_receipt_path,
                admitted_quote_receipt_path=admitted_quote_receipt_path,
                promotion_policy_path=promotion_policy_path,
                repository_root=repository,
                output_name=output_name,
            )
        finally:
            frozen._quote = original_quote
            frozen._safe_return_bindings = original_safe_return
            frozen._controls = original_controls


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="myis-a1.2-owner-evaluation-manifest-quote-bridge-v16"
    )
    parser.add_argument("--safe-return-archive", required=True, type=Path)
    parser.add_argument("--combined-output-root", required=True, type=Path)
    parser.add_argument("--protected-root", required=True, type=Path)
    parser.add_argument("--input-manifest", required=True, type=Path)
    parser.add_argument("--adoption-receipt", required=True, type=Path)
    parser.add_argument("--bundle-receipt", required=True, type=Path)
    parser.add_argument("--provider-admission-receipt", required=True, type=Path)
    parser.add_argument("--admitted-quote-receipt", required=True, type=Path)
    parser.add_argument("--budget-input", required=True, type=Path)
    parser.add_argument("--budget-receipt", required=True, type=Path)
    parser.add_argument("--provider-observation", required=True, type=Path)
    parser.add_argument("--quote-lineage", required=True, type=Path)
    parser.add_argument("--control-binding-lineage", required=True, type=Path)
    parser.add_argument("--promotion-policy", required=True, type=Path)
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--output-name", default="evaluation-input.v16.json")
    args = parser.parse_args()
    try:
        result = build_evaluation_manifest(
            safe_return_archive=args.safe_return_archive,
            combined_output_root=args.combined_output_root,
            protected_root=args.protected_root,
            input_manifest_path=args.input_manifest,
            adoption_receipt_path=args.adoption_receipt,
            bundle_receipt_path=args.bundle_receipt,
            provider_admission_receipt_path=args.provider_admission_receipt,
            admitted_quote_receipt_path=args.admitted_quote_receipt,
            budget_input_path=args.budget_input,
            budget_receipt_path=args.budget_receipt,
            provider_observation_path=args.provider_observation,
            quote_lineage_path=args.quote_lineage,
            control_binding_lineage_path=args.control_binding_lineage,
            promotion_policy_path=args.promotion_policy,
            repository_root=args.repository_root,
            output_name=args.output_name,
        )
    except (OwnerLocalEvaluationManifestQuoteBridgeV16Error, OSError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "OwnerLocalEvaluationManifestQuoteBridgeV16Error",
    "_validate_control_binding_bridge",
    "_validate_safe_return_bridge",
    "build_evaluation_manifest",
]
