from __future__ import annotations

import json
import tarfile
from io import BytesIO
from pathlib import Path

import pytest

from myis_research.armindex.a1_2_owner_local_evaluation_manifest_quote_bridge_v16 import (
    OwnerLocalEvaluationManifestQuoteBridgeV16Error,
    _validate_control_binding_bridge,
    _validate_quote_bridge,
    _validate_safe_return_bridge,
)
from myis_research.kernel.canonical import (
    canonical_json,
    canonical_sha256,
    file_sha256,
)

ROOT = Path(__file__).resolve().parents[1]
ATTEMPT = "a12-v16-20260811-r15"


def _write(path: Path, value: dict[str, object]) -> Path:
    path.write_text(canonical_json(value) + "\n", encoding="ascii")
    return path


def _self_hashed(body: dict[str, object]) -> dict[str, object]:
    return {**body, "receipt_sha256": canonical_sha256(body)}


def _case(tmp_path: Path) -> dict[str, object]:
    budget_input = {
        "evaluated_at_utc": "2026-08-11T04:19:22Z",
        "prior_attempt_spend_usd": {},
        "quote": {
            "billing_granularity_seconds": 60,
            "compute_hourly_rate_usd": 0.5,
            "minimum_billable_seconds": 60,
            "network_fee_usd": 0.0,
            "platform_or_other_fee_usd": 0.0,
            "quote_observed_at_utc": "2026-08-11T04:19:22Z",
            "storage_fee_usd": 4.0,
            "tax_or_surcharge_usd": 0.0,
        },
        "workload": {},
    }
    budget_input_path = _write(tmp_path / "budget-input.json", budget_input)
    budget_receipt = _self_hashed(
        {
            "status": "PASS_BUDGET_ADMISSION_LOCKED",
            "admitted": True,
            "ttl_hours": 40,
            "input_sha256": canonical_sha256(budget_input),
        }
    )
    budget_receipt_path = _write(tmp_path / "budget-receipt.json", budget_receipt)
    admission = _self_hashed(
        {
            "attempt_id": ATTEMPT,
            "budget_admission_receipt_sha256": budget_receipt["receipt_sha256"],
        }
    )
    adoption = _self_hashed(
        {
            "attempt_id": ATTEMPT,
            "adoption_bindings": {
                "all_fee_quote": canonical_sha256(budget_input["quote"])
            },
        }
    )
    provider_observation_path = _write(
        tmp_path / "provider.json", {"dph_total": 0.6}
    )
    quote_body = {
        "schema_version": "myis.armindex-a1.2-admitted-all-fee-quote-receipt.v16",
        "receipt_kind": "admitted_all_fee_quote",
        "receipt_id": f"{ATTEMPT}-all-fee-quote-v16",
        "attempt_id": ATTEMPT,
        "status": "PASS_ADMITTED_ALL_FEE_QUOTE",
        "claim_boundary": (
            "Aggregate-safe admitted all-fee rate for the immutable test attempt. "
            "This contains no credentials, raw provider payload, protected input, "
            "ranking, per-query outcome, provider action, or scientific result."
        ),
        "provider_admission_receipt_sha256": admission["receipt_sha256"],
        "currency": "USD",
        "all_fee_usd_per_hour": 0.6,
        "quote_sha256": canonical_sha256(budget_input["quote"]),
    }
    quote_receipt = _self_hashed(quote_body)
    quote_path = _write(tmp_path / "quote.json", quote_receipt)
    lineage_body = {
        "schema_version": "myis.armindex-a1.2-admitted-all-fee-quote-lineage.v16",
        "receipt_id": f"{ATTEMPT}-all-fee-quote-lineage-v16",
        "attempt_id": ATTEMPT,
        "status": "PASS",
        "claim_boundary": (
            "Aggregate-safe engineering lineage for the admitted test all-fee rate. "
            "It retains only hashes and safe totals, with no credential, raw provider "
            "payload, protected input, ranking, or per-query outcome."
        ),
        "provider_admission_receipt_sha256": admission["receipt_sha256"],
        "execution_adoption_receipt_sha256": adoption["receipt_sha256"],
        "budget_input_file_sha256": file_sha256(budget_input_path),
        "budget_receipt_sha256": budget_receipt["receipt_sha256"],
        "provider_observation_file_sha256": file_sha256(provider_observation_path),
        "quote_sha256": quote_receipt["quote_sha256"],
        "all_fee_usd_per_hour": 0.6,
        "admitted_quote_receipt_sha256": quote_receipt["receipt_sha256"],
    }
    lineage_path = _write(tmp_path / "lineage.json", _self_hashed(lineage_body))
    return {
        "admission": admission,
        "adoption": adoption,
        "budget_input": budget_input_path,
        "budget_receipt": budget_receipt_path,
        "provider_observation": provider_observation_path,
        "quote": quote_path,
        "lineage": lineage_path,
    }


def test_quote_bridge_accepts_complete_admitted_quote_lineage(tmp_path: Path) -> None:
    case = _case(tmp_path)
    receipt = _validate_quote_bridge(
        ROOT,
        case["quote"],
        admission=case["admission"],
        adoption=case["adoption"],
        attempt_id=ATTEMPT,
        budget_input_path=case["budget_input"],
        budget_receipt_path=case["budget_receipt"],
        provider_observation_path=case["provider_observation"],
        quote_lineage_path=case["lineage"],
    )
    assert receipt["all_fee_usd_per_hour"] == 0.6


def test_quote_bridge_rejects_rate_not_derived_from_quote(tmp_path: Path) -> None:
    case = _case(tmp_path)
    observation = case["provider_observation"]
    observation.write_text(json.dumps({"dph_total": 0.7}) + "\n", encoding="ascii")
    with pytest.raises(
        OwnerLocalEvaluationManifestQuoteBridgeV16Error,
        match="all-fee rate does not derive",
    ):
        _validate_quote_bridge(
            ROOT,
            case["quote"],
            admission=case["admission"],
            adoption=case["adoption"],
            attempt_id=ATTEMPT,
            budget_input_path=case["budget_input"],
            budget_receipt_path=case["budget_receipt"],
            provider_observation_path=observation,
            quote_lineage_path=case["lineage"],
        )


def _safe_return_archive(tmp_path: Path) -> Path:
    members = []
    for arm in ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05"):
        for program in (
            "P00-TAC-DOC",
            "P01-TA-DOC",
            "P02-CLAIM1",
            "P03-PASSAGE",
            "P04-SECTION-MULTIVIEW",
        ):
            members.append(
                {
                    "kind": "ranking",
                    "arm_id": arm,
                    "program_id": program,
                    "relative_path": f"rankings/{arm}--{program}.jsonl",
                    "sha256": "e" * 64,
                    "size_bytes": 1,
                }
            )
    manifest = {
        "schema_version": "myis.armindex-a1.2-safe-return-manifest.v16",
        "attempt_id": ATTEMPT,
        "status": "PASS",
        "transfer_manifest_sha256": "b" * 64,
        "split_commitment_sha256": "c" * 64,
        "ephemeral_token_map_sha256": "d" * 64,
        "work_token_set_sha256": "f" * 64,
        "members": members,
        "manifest_sha256": "a" * 64,
    }
    payload = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "ascii"
    )
    path = tmp_path / "safe-return.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        info = tarfile.TarInfo("safe-return-manifest.v16.json")
        info.size = len(payload)
        archive.addfile(info, BytesIO(payload))
    return path


def test_safe_return_bridge_accepts_static_contract_and_dynamic_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = _safe_return_archive(tmp_path)
    monkeypatch.setattr(
        "myis_research.armindex.a1_2_owner_local_evaluation_manifest_quote_bridge_v16.frozen.validate_safe_return_archive",
        lambda path: {"status": "PASS", "attempt_id": ATTEMPT, "cells": 25},
    )
    adoption = {
        "adoption_bindings": {
            "safe_return": file_sha256(
                ROOT / "control/armindex/a1.2/scientific-safe-return-contract.v16.json"
            ),
            "transfer": "b" * 64,
            "split": "c" * 64,
            "token_map": "d" * 64,
        }
    }
    facts = _validate_safe_return_bridge(ROOT, archive, adoption=adoption)
    assert facts["cells"] == 25
    assert len(facts["ranking_sha256_by_cell"]) == 25
    assert adoption["adoption_bindings"]["safe_return"] != "a" * 64


def test_safe_return_bridge_rejects_static_contract_drift(
    tmp_path: Path,
) -> None:
    archive = _safe_return_archive(tmp_path)
    adoption = {
        "adoption_bindings": {
            "safe_return": "0" * 64,
            "transfer": "b" * 64,
            "split": "c" * 64,
            "token_map": "d" * 64,
        }
    }
    with pytest.raises(
        OwnerLocalEvaluationManifestQuoteBridgeV16Error,
        match="safe-return contract",
    ):
        _validate_safe_return_bridge(ROOT, archive, adoption=adoption)


def _control_lineage_case(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    audit = json.loads(
        (
            ROOT
            / "outputs/audits/armindex/a1.2-protected-compiler-integration-20260809-v15.json"
        ).read_text(encoding="utf-8")
    )
    binding_set = audit["protected_receipts"]["binding_set_sha256"]
    compiler_receipt = audit["protected_receipts"]["compiler_receipt_sha256"]
    adoption = {
        "adoption_bindings": {
            "adoption_inputs": file_sha256(
                ROOT / "control/armindex/a1.2/scientific-execution-adoption-inputs.v15.json"
            ),
            "model_lockset": "6" * 64,
            "protected_compiler": compiler_receipt,
            "compiled_bindings_25_of_25": binding_set,
        }
    }
    body = {
        "status": "PASS_EXECUTION_ADOPTION",
        "measured_retrieval_allowed": True,
        "selection_allowed": False,
        "final_allowed": False,
        "adoption_inputs_sha256": adoption["adoption_bindings"]["adoption_inputs"],
        "model_lockset_sha256": adoption["adoption_bindings"]["model_lockset"],
        "protected_compiler_receipt_sha256": compiler_receipt,
        "binding_set_sha256": binding_set,
    }
    lineage = _write(tmp_path / "control-lineage.json", _self_hashed(body))
    return lineage, adoption


def test_control_binding_bridge_accepts_legacy_binding_semantics(tmp_path: Path) -> None:
    lineage, adoption = _control_lineage_case(tmp_path)
    _validate_control_binding_bridge(ROOT, lineage, adoption=adoption)


def test_control_binding_bridge_rejects_model_lockset_drift(tmp_path: Path) -> None:
    lineage, adoption = _control_lineage_case(tmp_path)
    adoption["adoption_bindings"]["model_lockset"] = "0" * 64
    with pytest.raises(
        OwnerLocalEvaluationManifestQuoteBridgeV16Error,
        match="frozen control lineage",
    ):
        _validate_control_binding_bridge(ROOT, lineage, adoption=adoption)
