"""Strict, aggregate-only validator for the frozen A1.2 v14 repair contract."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only

CONTRACT_PATH = Path("control/armindex/a1.2/dense-overflow-adapter-repair.v14.json")
SCHEMA_PATH = Path("schemas/armindex/a1.2-dense-overflow-adapter-repair.v14.json")
V9_PATH = Path("campaigns/armindex-multiretriever-v2/evidence/a1.2-live-synthetic-preflight-result.receipt.v9.json")
MODEL_LOCK_ROOT = Path("control/armindex/a1.2/model-locks")


class DenseOverflowContractV14Error(ValueError):
    """Fail-closed contract validation error."""


def _read_json(path: Path, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DenseOverflowContractV14Error(f"{role} is missing or invalid JSON") from error
    if not isinstance(value, dict):
        raise DenseOverflowContractV14Error(f"{role} must be a JSON object")
    return value


def _exact(value: Mapping[str, Any], expected: Mapping[str, Any], role: str) -> None:
    if dict(value) != dict(expected):
        raise DenseOverflowContractV14Error(f"{role} differs from the frozen v14 semantics")


OWNER_DECISION = {
    "authorize_additive_dense_overflow_adapter_repair": True,
    "preserve_historical_v11_v12_r3_v13": True,
    "preserve_original_p02_lineage": True,
    "preserve_5_arm_x_5_program_topology": True,
    "allow_partial_screen": False,
    "allow_silent_truncation": False,
    "allow_provider_contact": False,
    "allow_measured_retrieval": False,
}
LINEAGE = {
    "v11_program_set_uri": "control/armindex/a1.2/common-program-set.v11.json",
    "v11_program_set_file_sha256": "6bda78e024465944135ff6dff0883af37c86c31b9f004e01a195663467a527aa",
    "v12_r3_uri": "control/armindex/a1.2/scientific-execution-adoption-inputs.v12-r3.json",
    "v12_r3_file_sha256": "c17bb5f8e1886a176123b65a7461fcdb461e541acb2a47309d47dff97ba300c0",
    "v13_publication_uri": "control/armindex/a1.2/publication-impact-contract.v13.json",
    "v13_publication_file_sha256": "8de6d3d4fa8ede8cfd7f6b938d37de77cdde7cc4aa5201ef447e795b2a58e811",
    "p02_first_claim_uri": "control/armindex/a1.2/p02-first-claim-repair.v1.json",
    "p02_first_claim_file_sha256": "e4b758228d3d1ea44f94fd5987bfea0a06258f3b370621e4f4015f4e8e33038b",
}
IMPLEMENTATION = {
    "version": "a1.2-dense-overflow-composition-v1",
    "planner_source_uri": "src/myis_research/armindex/a1_2_dense_overflow_adapter_v1.py",
    "planner_source_sha256": "8c337de894648ef216ab64ae6b347885ac2de858b16110d94a1b279abc6818a0",
    "audit_source_uri": "src/myis_research/armindex/a1_2_dense_overflow_composition_audit_v1.py",
    "audit_source_sha256": "0c6863a4d7f72a343cf3c9c86154f6ffde5df5d990c2910125e307a6a2815a4d",
}
V9_LINEAGE = {
    "uri": V9_PATH.as_posix(),
    "file_sha256": "52d1d892c4ce034e3d4b0887a5bddbb362d9747c3b343e766ad2a4302c3f13d6",
    "receipt_sha256": "f8969e55225b4fa567c94079b6bffc834e1951268f626bdad7754104294df510",
}
SEMANTICS = {
    "fit_path": "preserve_existing_frozen_adapter_path_exactly",
    "overflow_scope": "physical_encoder_input_only",
    "logical_program_identity_changed": False,
    "logical_unit_identity_changed": False,
    "source_token_domain": "frozen_tokenizer_input_ids_without_special_tokens",
    "template_semantics": "exact_frozen_query_or_document_template_with_token_concatenation_parity",
    "window_order": "contiguous_source_order",
    "window_size": "longest_source_token_prefix_that_fits_effective_limit",
    "overlap_tokens": 0,
    "source_token_multiplicity": 1,
    "truncation_allowed": False,
    "omission_allowed": False,
    "alternate_field_fallback_allowed": False,
    "physical_encoder": "unchanged_frozen_arm_adapter",
    "aggregation": "source_token_count_weighted_mean",
    "aggregation_formula": "sum(window_source_tokens * physical_window_vector) / sum(window_source_tokens)",
    "postprocessing": "preserve_arm_specific_frozen_logical_vector_postprocessing_after_weighted_mean",
    "p03_physical_windows_become_retrieval_units": False,
}
REQUIREMENTS = {
    "compatible_program_arm_cells": 25,
    "rep_dev_query_coverage_fraction": 1.0,
    "required_corpus_logical_unit_coverage_fraction": 1.0,
    "maximum_physical_window_must_not_exceed_effective_limit": True,
    "source_token_drop_count": 0,
    "source_token_overlap_count": 0,
    "silent_truncation_count": 0,
    "fallback_count": 0,
    "deterministic_replay_required": True,
    "fail_closed": True,
}
AUTHORIZATION = {
    "provider_contact_allowed": False,
    "launch_allowed": False,
    "adopted_for_execution": False,
    "measured_retrieval_allowed": False,
    "selection_allowed": False,
    "final_allowed": False,
    "paid_api_allowed": False,
}
ADAPTERS = {
    "ARM-02": ("4de9210e97228620a202df5b733a3b6bccaa0fbde46d3643e1a61e3b90be893d", 1024),
    "ARM-03": ("67f5c374f82a475866a08d2be5f458b61a88ae745fc39046e0832965998a4e4b", 1024),
    "ARM-04": ("b91cfd112da14af4888207af8f42065e35f39b064fb91eef70890c1df8bc9b00", 768),
    "ARM-05": ("3cbfc95f260b6dac910abce1bd41ca13ae61f9face23baa7d6d6ef01cf33c44e", 1024),
}
MODEL_IDS = {
    "ARM-02": "BAAI/bge-m3",
    "ARM-03": "datalyes/patembed-large",
    "ARM-04": "Snowflake/snowflake-arctic-embed-m-v2.0",
    "ARM-05": "Qwen/Qwen3-Embedding-0.6B",
}
POSTPROCESSING = {
    "ARM-02": {"adapter_receipt_sha256": ADAPTERS["ARM-02"][0], "pooling": "preserve_frozen_v9_sentence_transformer_model_modules", "physical_window_vector_postprocessing": "unchanged_normalize_embeddings_true", "logical_vector_postprocessing": "apply_ARM_02_frozen_l2_output_normalization_after_weighted_mean"},
    "ARM-03": {"adapter_receipt_sha256": ADAPTERS["ARM-03"][0], "pooling": "mean_non_padding_tokens", "physical_window_vector_postprocessing": "unchanged_normalize_embeddings_true", "logical_vector_postprocessing": "apply_ARM_03_frozen_l2_output_normalization_after_weighted_mean"},
    "ARM-04": {"adapter_receipt_sha256": ADAPTERS["ARM-04"][0], "pooling": "first_token_cls", "physical_window_vector_postprocessing": "unchanged_normalize_embeddings_true", "logical_vector_postprocessing": "apply_ARM_04_frozen_l2_output_normalization_after_weighted_mean"},
    "ARM-05": {"adapter_receipt_sha256": ADAPTERS["ARM-05"][0], "pooling": "last_token_left_padding", "physical_window_vector_postprocessing": "unchanged_normalize_embeddings_true", "logical_vector_postprocessing": "apply_ARM_05_frozen_l2_output_normalization_after_weighted_mean"},
}


def _validate_file(root: Path, uri: str, expected: str, role: str) -> None:
    path = root / uri
    try:
        observed = file_sha256(path)
    except OSError as error:
        raise DenseOverflowContractV14Error(f"{role} is missing") from error
    if observed != expected:
        raise DenseOverflowContractV14Error(f"{role} SHA-256 mismatch")


def _validate_v9(root: Path, contract: Mapping[str, Any]) -> None:
    _validate_file(root, V9_LINEAGE["uri"], V9_LINEAGE["file_sha256"], "v9 adapter receipt")
    receipt = _read_json(root / V9_PATH, "v9 adapter receipt")
    if receipt.get("receipt_sha256") != V9_LINEAGE["receipt_sha256"]:
        raise DenseOverflowContractV14Error("v9 adapter receipt self-hash mismatch")
    if canonical_sha256({key: item for key, item in receipt.items() if key != "receipt_sha256"}) != receipt["receipt_sha256"]:
        raise DenseOverflowContractV14Error("v9 adapter receipt canonical self-hash mismatch")
    arms = receipt.get("arms")
    if not isinstance(arms, list) or {item.get("arm_id") for item in arms} != set(ADAPTERS) or len(arms) != len(ADAPTERS):
        raise DenseOverflowContractV14Error("v9 adapter arm mapping is incomplete")
    for item in arms:
        arm_id = item["arm_id"]
        adapter_sha, dimension = ADAPTERS[arm_id]
        if item.get("status") != "PASS" or item.get("adapter_receipt_sha256") != adapter_sha or item.get("output_dimension") != dimension:
            raise DenseOverflowContractV14Error(f"v9 adapter mapping mismatch for {arm_id}")
        lock = _read_json(root / MODEL_LOCK_ROOT / f"{arm_id}.v1.json", f"{arm_id} model lock")
        if lock.get("arm_id") != arm_id or lock.get("model_id") != MODEL_IDS[arm_id] or lock.get("dimension") != dimension:
            raise DenseOverflowContractV14Error(f"{arm_id} model mapping/dimension mismatch")


def validate_contract(repository_root: Path, value: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Validate frozen v14 semantics and source commitments without protected data."""
    root = repository_root.resolve()
    contract = dict(value) if value is not None else _read_json(root / CONTRACT_PATH, "dense-overflow repair contract")
    try:
        schema = _read_json(root / SCHEMA_PATH, "dense-overflow repair schema")
        errors = sorted(Draft202012Validator(schema).iter_errors(contract), key=lambda error: list(error.path))
    except Exception as error:
        raise DenseOverflowContractV14Error("dense-overflow repair schema is invalid") from error
    if errors:
        raise DenseOverflowContractV14Error(f"schema failure at {list(errors[0].path)}")
    assert_aggregate_only(contract)
    if contract.get("contract_sha256") != canonical_sha256({key: item for key, item in contract.items() if key != "contract_sha256"}):
        raise DenseOverflowContractV14Error("dense-overflow repair contract self-hash mismatch")
    if contract["owner_decision"] != OWNER_DECISION or contract["immutable_lineage"] != LINEAGE:
        raise DenseOverflowContractV14Error("owner decision or immutable lineage changed")
    if contract["implementation"] != IMPLEMENTATION or contract["composition_semantics"] != SEMANTICS:
        raise DenseOverflowContractV14Error("implementation or composition semantics changed")
    if contract["requirements"] != REQUIREMENTS or contract["authorization"] != AUTHORIZATION:
        raise DenseOverflowContractV14Error("requirements or authorization changed")
    _validate_file(root, LINEAGE["v11_program_set_uri"], LINEAGE["v11_program_set_file_sha256"], "v11 program set")
    _validate_file(root, LINEAGE["v12_r3_uri"], LINEAGE["v12_r3_file_sha256"], "v12-r3 contract")
    _validate_file(root, LINEAGE["v13_publication_uri"], LINEAGE["v13_publication_file_sha256"], "v13 publication contract")
    _validate_file(root, LINEAGE["p02_first_claim_uri"], LINEAGE["p02_first_claim_file_sha256"], "P02 repair")
    _validate_file(root, IMPLEMENTATION["planner_source_uri"], IMPLEMENTATION["planner_source_sha256"], "planner source")
    _validate_file(root, IMPLEMENTATION["audit_source_uri"], IMPLEMENTATION["audit_source_sha256"], "composition audit source")
    _validate_file(root, contract["raw_inventory"]["uri"], contract["raw_inventory"]["file_sha256"], "raw inventory")
    inventory = _read_json(root / contract["raw_inventory"]["uri"], "raw inventory")
    if inventory.get("inventory_sha256") != contract["raw_inventory"]["inventory_sha256"] or inventory["inventory_sha256"] != canonical_sha256({key: item for key, item in inventory.items() if key != "inventory_sha256"}):
        raise DenseOverflowContractV14Error("raw inventory self-hash mismatch")
    if contract["raw_inventory"]["deterministic_replay"] != {"status": "PASS", "batch_schedules": [128, 256], "byte_identical_receipt": True, "first_wall_seconds": 2246.6, "replay_wall_seconds": 1118.0}:
        raise DenseOverflowContractV14Error("raw inventory replay metadata changed")
    if contract["v9_adapter_lineage"] != V9_LINEAGE:
        raise DenseOverflowContractV14Error("v9 adapter lineage changed")
    _validate_v9(root, contract)
    if contract["arm_postprocessing"] != POSTPROCESSING:
        raise DenseOverflowContractV14Error("arm postprocessing or adapter receipt mapping changed")
    return {"status": "PASS", "repair_id": contract["repair_id"], "compatible_program_arm_cells": 25, "dense_adapter_arms": 4, "provider_contact_allowed": False, "measured_retrieval_allowed": False}


__all__ = ["DenseOverflowContractV14Error", "validate_contract"]
