"""Synthetic-only A0.8 CPU compute and storage feasibility fixture."""

from __future__ import annotations

import gc
import json
import math
import os
import platform
import tempfile
import time
import tracemalloc
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from ..kernel.canonical import canonical_bytes, canonical_sha256
from ..kernel.p1 import tokenize
from ..protection import assert_aggregate_only
from .arms import ArmRegistry, ArmUnavailableError, FIXTURE_BACKEND_ID
from .compiler import CompiledRepresentation, compile_program
from .fixture import (
    _cases,
    _documents,
    _prepare_output,
    _program,
    _validate_self_hash,
    _write_once,
)


FIXTURE_ID = "armindex-a08-compute-storage-v1"
SCALE_FACTORS = (1, 8, 32)
MIN_REPETITIONS = 3
MAX_REPETITIONS = 101


@dataclass(frozen=True)
class FeasibilityArtifacts:
    manifest: Mapping[str, Any]
    receipt: Mapping[str, Any]
    output_persisted: bool

    def summary(self) -> dict[str, Any]:
        largest = self.receipt["observations"][-1]
        return {
            "schema_version": "myis.armindex-compute-storage-fixture-summary.v1",
            "fixture_id": FIXTURE_ID,
            "status": self.receipt["status"],
            "evidence_class": "engineering_fixture",
            "scientific_authority": False,
            "protected_data_accessed": False,
            "measured_execution": False,
            "cpu_only": True,
            "largest_synthetic_document_count": largest["synthetic_document_count"],
            "largest_peak_python_allocation_bytes": largest["peak_python_allocation_bytes"],
            "manifest_sha256": self.manifest["manifest_sha256"],
            "receipt_sha256": self.receipt["receipt_sha256"],
            "output_persisted": self.output_persisted,
            "real_counters": dict(self.receipt["real_counters"]),
        }


def run_compute_storage_feasibility_fixture(
    output_dir: Path | None = None,
    *,
    repetitions: int = 11,
) -> FeasibilityArtifacts:
    """Run bounded host observations over generated synthetic patent records."""

    _validate_repetitions(repetitions)
    if output_dir is None:
        with tempfile.TemporaryDirectory(prefix="myis-armindex-a08-") as temporary:
            result = _execute(Path(temporary), repetitions=repetitions)
        return FeasibilityArtifacts(result.manifest, result.receipt, output_persisted=False)
    return _execute(
        _prepare_output(output_dir),
        repetitions=repetitions,
        output_persisted=True,
    )


def validate_compute_storage_artifacts(
    manifest: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> None:
    if manifest.get("schema_version") != "myis.armindex-compute-storage-fixture-manifest.v1":
        raise ValueError("unsupported A0.8 feasibility manifest")
    if receipt.get("schema_version") != "myis.armindex-compute-storage-fixture-receipt.v1":
        raise ValueError("unsupported A0.8 feasibility receipt")
    _validate_self_hash(manifest, "manifest_sha256")
    _validate_self_hash(receipt, "receipt_sha256")
    if receipt.get("manifest_sha256") != manifest.get("manifest_sha256"):
        raise ValueError("A0.8 feasibility receipt is not bound to its manifest")
    if manifest.get("task_id") != "A0.8" or receipt.get("task_id") != "A0.8":
        raise ValueError("A0.8 feasibility artifact task identity is invalid")
    if receipt.get("status") != "PASS":
        raise ValueError("A0.8 feasibility receipt did not pass")
    for artifact in (manifest, receipt):
        if artifact.get("scientific_authority") is not False:
            raise ValueError("A0.8 feasibility fixture cannot claim scientific authority")
        if artifact.get("protected_data_accessed") is not False:
            raise ValueError("A0.8 feasibility fixture cannot access protected data")
    safety = receipt.get("safety", {})
    required_false = {
        "protected_data_accessed",
        "measured_execution",
        "network_used",
        "model_downloaded",
        "gpu_used",
        "paid_api_used",
        "selection_opened",
        "final_opened",
        "app_protected_payload_opened",
    }
    if not isinstance(safety, Mapping) or any(safety.get(key) is not False for key in required_false):
        raise ValueError("A0.8 feasibility safety boundary is invalid")
    if safety.get("cpu_only") is not True or safety.get("synthetic_inputs_only") is not True:
        raise ValueError("A0.8 feasibility fixture must be CPU-only and synthetic-only")
    counters = receipt.get("real_counters", {})
    if not isinstance(counters, Mapping) or any(value != 0 for value in counters.values()):
        raise ValueError("A0.8 feasibility fixture cannot change real counters")
    profiles = manifest.get("profiles")
    observations = receipt.get("observations")
    if not isinstance(profiles, list) or not isinstance(observations, list):
        raise ValueError("A0.8 feasibility profiles are missing")
    if len(profiles) != len(SCALE_FACTORS) or len(observations) != len(profiles):
        raise ValueError("A0.8 feasibility profile count is invalid")
    for profile, observation, scale in zip(profiles, observations, SCALE_FACTORS, strict=True):
        if profile.get("scale_factor") != scale or observation.get("scale_factor") != scale:
            raise ValueError("A0.8 feasibility profile ordering is invalid")
        if observation.get("profile_sha256") != profile.get("profile_sha256"):
            raise ValueError("A0.8 feasibility observation is not bound to its profile")
        if observation.get("synthetic_document_count") != profile.get("synthetic_document_count"):
            raise ValueError("A0.8 feasibility observed document count drifted")
        if observation.get("peak_python_allocation_bytes", 0) <= 0:
            raise ValueError("A0.8 feasibility allocation observation is invalid")
        for operation in ("compile", "index_build", "search_workload"):
            metrics = observation.get("latency_ms", {}).get(operation, {})
            values = [metrics.get(key) for key in ("p50", "p95", "p99")]
            if any(not isinstance(value, (int, float)) or value < 0 for value in values):
                raise ValueError("A0.8 feasibility latency observation is invalid")
            if values != sorted(values):
                raise ValueError("A0.8 feasibility latency percentiles are not monotonic")
        if observation.get("search_throughput_qps", 0) <= 0:
            raise ValueError("A0.8 feasibility throughput observation is invalid")
    assert_aggregate_only(manifest)
    assert_aggregate_only(receipt)


def _execute(
    output: Path,
    *,
    repetitions: int,
    output_persisted: bool = False,
) -> FeasibilityArtifacts:
    program = _program()
    registry = ArmRegistry()
    adapter = registry.get("ARM-01")
    cases = _cases()
    deterministic_profiles: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    run_started_wall = time.perf_counter_ns()
    run_started_cpu = time.process_time_ns()

    for scale in SCALE_FACTORS:
        documents = _scaled_documents(scale)
        warm_compiled = compile_program(program, documents)
        warm_index = adapter.build_index(warm_compiled)
        _search_commitment(adapter, warm_index, cases)

        compile_samples: list[int] = []
        index_samples: list[int] = []
        search_samples: list[int] = []
        ranking_commitments: set[str] = set()
        final_compiled: CompiledRepresentation | None = None
        final_index: Any = None
        gc.collect()
        tracemalloc.start()
        try:
            for _ in range(repetitions):
                started = time.perf_counter_ns()
                compiled = compile_program(program, documents)
                compile_samples.append(time.perf_counter_ns() - started)

                started = time.perf_counter_ns()
                index = adapter.build_index(compiled)
                index_samples.append(time.perf_counter_ns() - started)

                started = time.perf_counter_ns()
                ranking_commitments.add(_search_commitment(adapter, index, cases))
                search_samples.append(time.perf_counter_ns() - started)
                final_compiled = compiled
                final_index = index
            _current, peak_python_allocation_bytes = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        if len(ranking_commitments) != 1 or final_compiled is None or final_index is None:
            raise ValueError("A0.8 synthetic ranking output is not deterministic")

        sparse_payload = _portable_sparse_payload(final_compiled)
        profile_unsigned = {
            "scale_factor": scale,
            "synthetic_document_count": len(documents),
            "synthetic_family_count": len({row["family_id"] for row in documents}),
            "compiled_unit_count": len(final_compiled.units),
            "estimated_token_count": final_compiled.estimated_token_count,
            "source_utf8_bytes": _source_utf8_bytes(documents),
            "compiled_text_bytes": final_compiled.estimated_storage_bytes,
            "compiled_payload_bytes": len(canonical_bytes(final_compiled.as_dict())),
            "portable_sparse_payload_bytes": len(canonical_bytes(sparse_payload)),
            "portable_sparse_payload_sha256": canonical_sha256(sparse_payload),
            "logical_program_sha256": final_compiled.logical_program_sha256,
            "compiled_representation_sha256": final_compiled.compiled_representation_sha256,
            "source_sha256": final_compiled.source_sha256,
            "fixture_index_sha256": final_index.index_sha256,
            "ranking_commitment": next(iter(ranking_commitments)),
        }
        profile = {**profile_unsigned, "profile_sha256": canonical_sha256(profile_unsigned)}
        deterministic_profiles.append(profile)
        total_search_ns = sum(search_samples)
        observations.append(
            {
                "scale_factor": scale,
                "profile_sha256": profile["profile_sha256"],
                "synthetic_document_count": len(documents),
                "repetitions": repetitions,
                "search_calls": repetitions * len(cases),
                "latency_ms": {
                    "compile": _latency_summary(compile_samples),
                    "index_build": _latency_summary(index_samples),
                    "search_workload": _latency_summary(search_samples),
                },
                "search_throughput_qps": round(
                    (repetitions * len(cases)) / (total_search_ns / 1_000_000_000),
                    6,
                ),
                "peak_python_allocation_bytes": peak_python_allocation_bytes,
            }
        )

    dense_block_count = 0
    largest_compiled = compile_program(_program(), _scaled_documents(SCALE_FACTORS[-1]))
    for arm_id in ("ARM-02", "ARM-03", "ARM-04", "ARM-05"):
        try:
            registry.get(arm_id).build_index(largest_compiled)
        except ArmUnavailableError:
            dense_block_count += 1
        else:
            raise ValueError(f"{arm_id} executed during the A0.8 CPU fixture")

    manifest_unsigned = {
        "schema_version": "myis.armindex-compute-storage-fixture-manifest.v1",
        "fixture_id": FIXTURE_ID,
        "campaign_id": "armindex-multiretriever-v2",
        "phase_id": "A0_MIGRATION_FOUNDATION",
        "task_id": "A0.8",
        "status": "frozen_before_execution",
        "evidence_class": "engineering_fixture",
        "scientific_authority": False,
        "claim_boundary": "synthetic_host_feasibility_only_no_production_projection",
        "protected_data_accessed": False,
        "backend": {
            "arm_id": "ARM-01",
            "backend_id": FIXTURE_BACKEND_ID,
            "fixture_only": True,
            "scientific_arm_lock": False,
            "bm25s_physical_index_measured": False,
        },
        "methodology": {
            "synthetic_generator": "a0.8-scaled-patent-fixture-v1",
            "scale_factors": list(SCALE_FACTORS),
            "repetitions": repetitions,
            "warmup_repetitions": 1,
            "clock": "time.perf_counter_ns",
            "cpu_clock": "time.process_time_ns",
            "python_allocation_probe": "tracemalloc_peak",
            "storage_measurement": "canonical_utf8_payload_bytes",
        },
        "profiles": deterministic_profiles,
        "safety": {
            "synthetic_inputs_only": True,
            "cpu_only": True,
            "network_required": False,
            "model_download_required": False,
            "gpu_required": False,
            "paid_api_required": False,
            "app_protected_asset_used": False,
        },
    }
    manifest = {**manifest_unsigned, "manifest_sha256": canonical_sha256(manifest_unsigned)}
    run_wall_ns = time.perf_counter_ns() - run_started_wall
    run_cpu_ns = time.process_time_ns() - run_started_cpu
    receipt_unsigned = {
        "schema_version": "myis.armindex-compute-storage-fixture-receipt.v1",
        "fixture_id": FIXTURE_ID,
        "campaign_id": "armindex-multiretriever-v2",
        "phase_id": "A0_MIGRATION_FOUNDATION",
        "task_id": "A0.8",
        "status": "PASS",
        "evidence_class": "engineering_fixture",
        "scientific_authority": False,
        "claim_boundary": "synthetic_host_feasibility_only_no_production_projection",
        "protected_data_accessed": False,
        "manifest_sha256": manifest["manifest_sha256"],
        "host": {
            "operating_system": platform.system(),
            "machine": platform.machine(),
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "logical_cpu_count": os.cpu_count(),
        },
        "runtime": {
            "wall_time_seconds": round(run_wall_ns / 1_000_000_000, 9),
            "process_cpu_time_seconds": round(run_cpu_ns / 1_000_000_000, 9),
        },
        "observations": observations,
        "aggregate_counts": {
            "profile_count": len(deterministic_profiles),
            "dense_arms_blocked": dense_block_count,
            "synthetic_cases": len(cases),
        },
        "real_counters": {
            "measured_runs": 0,
            "candidate_count": 0,
            "selection_accesses": 0,
            "final_accesses": 0,
        },
        "resource_counters": {
            "charged_usd": 0,
            "gpu_scientific_runs": 0,
            "paid_api_calls": 0,
            "model_downloads": 0,
            "model_weight_modifications": 0,
        },
        "safety": {
            "synthetic_inputs_only": True,
            "cpu_only": True,
            "protected_data_accessed": False,
            "measured_execution": False,
            "network_used": False,
            "model_downloaded": False,
            "gpu_used": False,
            "paid_api_used": False,
            "selection_opened": False,
            "final_opened": False,
            "app_protected_payload_opened": False,
        },
        "next_action": "Run A0.9 synthetic CPU validation and migration closeout; A1 remains locked",
    }
    receipt = {**receipt_unsigned, "receipt_sha256": canonical_sha256(receipt_unsigned)}
    validate_compute_storage_artifacts(manifest, receipt)
    _write_once(output / "manifest.json", manifest)
    _write_once(output / "receipt.json", receipt)
    restored_manifest = json.loads((output / "manifest.json").read_text(encoding="ascii"))
    restored_receipt = json.loads((output / "receipt.json").read_text(encoding="ascii"))
    validate_compute_storage_artifacts(restored_manifest, restored_receipt)
    return FeasibilityArtifacts(manifest, receipt, output_persisted=output_persisted)


def _validate_repetitions(repetitions: int) -> None:
    if isinstance(repetitions, bool) or not isinstance(repetitions, int):
        raise ValueError("repetitions must be an integer")
    if not MIN_REPETITIONS <= repetitions <= MAX_REPETITIONS:
        raise ValueError(f"repetitions must be in [{MIN_REPETITIONS}, {MAX_REPETITIONS}]")


def _scaled_documents(scale: int) -> list[dict[str, str]]:
    if scale not in SCALE_FACTORS:
        raise ValueError("unsupported synthetic scale factor")
    documents = []
    for replica in range(1, scale + 1):
        suffix = f"S{replica:04d}"
        for source in _documents():
            row = dict(source)
            row["family_id"] = f"{source['family_id']}-{suffix}"
            row["publication_id"] = f"{source['publication_id']}-{suffix}"
            row["abstract"] = f"{source['abstract']} Synthetic scale marker {replica}."
            documents.append(row)
    return documents


def _source_utf8_bytes(documents: Sequence[Mapping[str, str]]) -> int:
    return sum(
        len(str(value).encode("utf-8"))
        for row in documents
        for key, value in row.items()
        if key not in {"family_id", "publication_id"}
    )


def _portable_sparse_payload(compiled: CompiledRepresentation) -> dict[str, Any]:
    postings: dict[str, list[tuple[str, int]]] = defaultdict(list)
    documents = []
    for unit in compiled.units:
        frequencies = Counter(tokenize(unit.text))
        documents.append(
            {
                "unit_id": unit.unit_id,
                "family_id": unit.family_id,
                "token_count": sum(frequencies.values()),
            }
        )
        for term, frequency in sorted(frequencies.items()):
            postings[term].append((unit.unit_id, frequency))
    return {
        "schema_version": "myis.armindex-portable-sparse-fixture.v1",
        "backend_id": FIXTURE_BACKEND_ID,
        "documents": sorted(documents, key=lambda item: item["unit_id"]),
        "terms": [
            {"term": term, "postings": sorted(rows)}
            for term, rows in sorted(postings.items())
        ],
    }


def _search_commitment(adapter: Any, index: Any, cases: Mapping[str, str]) -> str:
    rankings = {
        case_id: [
            {
                "family_id": hit.family_id,
                "publication_id": hit.publication_id,
                "unit_id": hit.unit_id,
                "rank": hit.rank,
                "score": hit.score,
            }
            for hit in adapter.search(index, case_id=case_id, text=text, top_k=100).hits
        ]
        for case_id, text in sorted(cases.items())
    }
    return canonical_sha256(rankings)


def _latency_summary(samples_ns: Sequence[int]) -> dict[str, float]:
    if not samples_ns:
        raise ValueError("latency samples cannot be empty")
    ordered = sorted(samples_ns)
    return {
        "p50": _percentile_ms(ordered, 50),
        "p95": _percentile_ms(ordered, 95),
        "p99": _percentile_ms(ordered, 99),
    }


def _percentile_ms(ordered_ns: Sequence[int], percentile: int) -> float:
    index = max(0, math.ceil((percentile / 100) * len(ordered_ns)) - 1)
    return round(ordered_ns[index] / 1_000_000, 6)
