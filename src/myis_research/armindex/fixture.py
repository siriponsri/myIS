"""Disposable, aggregate-safe ArmIndex synthetic vertical slice."""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ..kernel.canonical import canonical_bytes, canonical_sha256
from ..protection import assert_aggregate_only, assert_path_not_protected
from .arms import ArmRegistry, ArmUnavailableError, FIXTURE_BACKEND_ID
from .compiler import compile_program
from .evaluation import evaluate_family_rankings


FIXTURE_ID = "armindex-a010-vertical-slice-v1"


@dataclass(frozen=True)
class FixtureArtifacts:
    manifest: Mapping[str, Any]
    receipt: Mapping[str, Any]
    output_persisted: bool

    def summary(self) -> dict[str, Any]:
        return {
            "schema_version": "myis.armindex-synthetic-fixture-summary.v1",
            "fixture_id": FIXTURE_ID,
            "status": self.receipt["status"],
            "evidence_class": "fixture",
            "scientific_authority": False,
            "protected_data_accessed": False,
            "measured_execution": False,
            "backend_id": FIXTURE_BACKEND_ID,
            "manifest_sha256": self.manifest["manifest_sha256"],
            "receipt_sha256": self.receipt["receipt_sha256"],
            "output_persisted": self.output_persisted,
            "real_counters": dict(self.receipt["real_counters"]),
        }


def run_synthetic_fixture(output_dir: Path | None = None) -> FixtureArtifacts:
    """Execute the complete fixture in a disposable directory by default."""

    if output_dir is None:
        with tempfile.TemporaryDirectory(prefix="myis-armindex-fixture-") as temporary:
            result = _execute(Path(temporary))
        return FixtureArtifacts(result.manifest, result.receipt, output_persisted=False)
    return _execute(_prepare_output(output_dir), output_persisted=True)


def validate_fixture_artifacts(manifest: Mapping[str, Any], receipt: Mapping[str, Any]) -> None:
    if manifest.get("schema_version") != "myis.armindex-synthetic-fixture-manifest.v1":
        raise ValueError("unsupported ArmIndex fixture manifest")
    if receipt.get("schema_version") != "myis.armindex-synthetic-fixture-receipt.v1":
        raise ValueError("unsupported ArmIndex fixture receipt")
    _validate_self_hash(manifest, "manifest_sha256")
    _validate_self_hash(receipt, "receipt_sha256")
    if receipt.get("manifest_sha256") != manifest.get("manifest_sha256"):
        raise ValueError("fixture receipt is not bound to its manifest")
    if receipt.get("scientific_authority") is not False or receipt.get("measured_execution") is not False:
        raise ValueError("synthetic fixture cannot claim scientific or measured authority")
    if receipt.get("protected_data_accessed") is not False:
        raise ValueError("synthetic fixture cannot access protected data")
    if any(value != 0 for value in receipt.get("real_counters", {}).values()):
        raise ValueError("synthetic fixture cannot change real counters")
    assert_aggregate_only(manifest)
    assert_aggregate_only(receipt)


def _execute(output: Path, *, output_persisted: bool = False) -> FixtureArtifacts:
    program = _program()
    documents = _documents()
    compiled = compile_program(program, documents)
    reversed_compiled = compile_program(program, reversed(documents))
    if compiled.as_dict() != reversed_compiled.as_dict():
        raise ValueError("representation compiler is not input-order deterministic")

    registry = ArmRegistry()
    dense_block_count = 0
    for arm_id in ("ARM-02", "ARM-03", "ARM-04", "ARM-05"):
        try:
            registry.get(arm_id).build_index(compiled)
        except ArmUnavailableError:
            dense_block_count += 1
        else:
            raise ValueError(f"{arm_id} executed without a resolved offline model lock")
    adapter = registry.get("ARM-01")
    index = adapter.build_index(compiled)
    cases = _cases()
    rankings = {
        case_id: adapter.search(index, case_id=case_id, text=text, top_k=100)
        for case_id, text in sorted(cases.items())
    }
    family_rows = {
        case_id: [hit.family_id for hit in ranking.hits]
        for case_id, ranking in rankings.items()
    }
    metrics = evaluate_family_rankings(family_rows, _judgments())
    ranking_commitment = canonical_sha256(
        {
            case_id: [
                {
                    "family_id": hit.family_id,
                    "rank": hit.rank,
                    "score": hit.score,
                    "publication_id": hit.publication_id,
                    "unit_id": hit.unit_id,
                }
                for hit in ranking.hits
            ]
            for case_id, ranking in sorted(rankings.items())
        }
    )
    manifest_unsigned = {
        "schema_version": "myis.armindex-synthetic-fixture-manifest.v1",
        "fixture_id": FIXTURE_ID,
        "campaign_id": "armindex-multiretriever-v2",
        "phase_id": "A0_MIGRATION_FOUNDATION",
        "task_id": "A0.10",
        "evidence_class": "fixture",
        "scientific_authority": False,
        "claim_boundary": "engineering_interface_validation_only",
        "backend": {
            "arm_id": "ARM-01",
            "backend_id": FIXTURE_BACKEND_ID,
            "fixture_only": True,
            "scientific_arm_lock": False,
            "network_required": False,
            "gpu_required": False,
            "paid_api": False,
        },
        "counts": {
            "synthetic_documents": len(documents),
            "synthetic_families": len({row["family_id"] for row in documents}),
            "compiled_units": len(compiled.units),
            "fixture_cases": len(cases),
            "dense_arms_blocked": dense_block_count,
        },
        "arm_capabilities": [item.as_dict() for item in registry.capabilities()],
        "commitments": {
            "logical_program_sha256": compiled.logical_program_sha256,
            "compiled_representation_sha256": compiled.compiled_representation_sha256,
            "source_sha256": compiled.source_sha256,
            "index_sha256": index.index_sha256,
            "ranking_sha256": ranking_commitment,
            "metrics_sha256": metrics["metrics_sha256"],
        },
        "compiler": {
            "family_aggregation": compiled.family_aggregation,
            "estimated_storage_bytes": compiled.estimated_storage_bytes,
            "estimated_token_count": compiled.estimated_token_count,
            "omitted_unit_count": compiled.omitted_unit_count,
            "truncated_span_count": compiled.truncated_span_count,
        },
        "safety": {
            "protected_data_accessed": False,
            "measured_execution": False,
            "network_used": False,
            "model_downloaded": False,
            "gpu_used": False,
            "paid_api_used": False,
            "selection_opened": False,
            "final_opened": False,
        },
    }
    manifest = {**manifest_unsigned, "manifest_sha256": canonical_sha256(manifest_unsigned)}
    receipt_unsigned = {
        "schema_version": "myis.armindex-synthetic-fixture-receipt.v1",
        "fixture_id": FIXTURE_ID,
        "campaign_id": "armindex-multiretriever-v2",
        "phase_id": "A0_MIGRATION_FOUNDATION",
        "task_id": "A0.10",
        "status": "PASS",
        "evidence_class": "fixture",
        "scientific_authority": False,
        "claim_boundary": "engineering_interface_validation_only",
        "protected_data_accessed": False,
        "measured_execution": False,
        "manifest_sha256": manifest["manifest_sha256"],
        "metrics": metrics["metrics"],
        "metric_bundle_sha256": canonical_sha256(metrics),
        "aggregate_counts": dict(manifest["counts"]),
        "real_counters": {
            "measured_runs": 0,
            "candidate_count": 0,
            "selection_accesses": 0,
            "final_accesses": 0,
        },
        "safety_checks": {
            "representation_determinism": "PASS",
            "dense_fail_closed": "PASS",
            "aggregate_only": "PASS",
            "receipt_before_projection": "PASS",
            "temporary_output_default": "PASS",
        },
        "next_action": "A0 synthetic fixture review only; measured retrieval remains closed",
    }
    receipt = {**receipt_unsigned, "receipt_sha256": canonical_sha256(receipt_unsigned)}
    validate_fixture_artifacts(manifest, receipt)
    _write_once(output / "manifest.json", manifest)
    _write_once(output / "receipt.json", receipt)
    restored_manifest = json.loads((output / "manifest.json").read_text(encoding="ascii"))
    restored_receipt = json.loads((output / "receipt.json").read_text(encoding="ascii"))
    validate_fixture_artifacts(restored_manifest, restored_receipt)
    return FixtureArtifacts(manifest, receipt, output_persisted=output_persisted)


def _prepare_output(output_dir: Path) -> Path:
    assert_path_not_protected(output_dir.as_posix())
    if output_dir.is_symlink():
        raise ValueError("fixture output cannot be a symlink")
    output = output_dir.resolve()
    assert_path_not_protected(output.as_posix())
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise FileExistsError("fixture output directory must be empty")
    return output


def _write_once(path: Path, payload: Mapping[str, Any]) -> None:
    encoded = canonical_bytes(payload) + b"\n"
    with path.open("xb") as handle:
        handle.write(encoded)


def _validate_self_hash(payload: Mapping[str, Any], field: str) -> None:
    unsigned = {key: item for key, item in payload.items() if key != field}
    if payload.get(field) != canonical_sha256(unsigned):
        raise ValueError(f"{field} does not match canonical payload")


def _program() -> dict[str, Any]:
    unsigned = {
        "schema_version": "myis.armindex-representation-program.v1",
        "program_id": "fixture-tac-passages",
        "arm_id": "ARM-01",
        "source_fields": ["title", "abstract", "claims"],
        "field_order": ["title", "abstract", "claims"],
        "field_labels": {"title": "TITLE", "abstract": "ABSTRACT", "claims": "CLAIMS"},
        "unitization": {"kind": "passage", "logical_size": 12, "overlap": 0},
        "normalization": "unicode_nfkc_whitespace_lower",
        "duplicate_policy": "preserve_all",
        "family_aggregation": "maxp",
        "preserve_family_identity": True,
    }
    return {**unsigned, "program_sha256": canonical_sha256(unsigned)}


def _documents() -> list[dict[str, str]]:
    return [
        {
            "family_id": "SYN-FAMILY-01",
            "publication_id": "SYN-PUB-01-A",
            "title": "Battery thermal control",
            "abstract": "Cooling channels regulate energy storage pack temperature.",
            "claims": "1. A battery pack comprising a thermal controller.\n2. Cooling fluid channels around cells.",
        },
        {
            "family_id": "SYN-FAMILY-01",
            "publication_id": "SYN-PUB-01-B",
            "title": "Energy storage heat dissipation",
            "abstract": "A secondary publication describes battery cooling plates.",
            "claims": "1. A heat transfer plate coupled to battery cells.",
        },
        {
            "family_id": "SYN-FAMILY-02",
            "publication_id": "SYN-PUB-02-A",
            "title": "Optical alignment sensor",
            "abstract": "Camera calibration uses an optical fiducial and image detector.",
            "claims": "1. An optical calibration apparatus comprising a fiducial sensor.",
        },
        {
            "family_id": "SYN-FAMILY-03",
            "publication_id": "SYN-PUB-03-A",
            "title": "Agricultural nutrient composition",
            "abstract": "A fertilizer blend supports controlled nutrient release.",
            "claims": "1. A granular agricultural composition.",
        },
    ]


def _cases() -> dict[str, str]:
    return {
        "synthetic-case-energy": "battery thermal cooling controller",
        "synthetic-case-optical": "optical fiducial camera calibration sensor",
    }


def _judgments() -> dict[str, dict[str, int]]:
    return {
        "synthetic-case-energy": {"SYN-FAMILY-01": 2},
        "synthetic-case-optical": {"SYN-FAMILY-02": 2},
    }
