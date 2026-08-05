"""A1.1 synthetic adapter validation with a runnable ARM-01 CPU path."""

from __future__ import annotations

import gc
import json
import os
import platform
import tempfile
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ..kernel.canonical import canonical_sha256
from ..protection import assert_aggregate_only
from .arms import ARM_IDS, ArmRegistry, ArmUnavailableError, FIXTURE_BACKEND_ID
from .compiler import compile_program
from .evaluation import evaluate_family_rankings
from .feasibility import _latency_summary
from .fixture import (
    _cases,
    _documents,
    _judgments,
    _prepare_output,
    _program,
    _validate_self_hash,
    _write_once,
)


FIXTURE_ID = "armindex-a11-adapter-cpu-v1"
MIN_REPETITIONS = 3
MAX_REPETITIONS = 31


@dataclass(frozen=True)
class AdapterFixtureArtifacts:
    manifest: Mapping[str, Any]
    receipt: Mapping[str, Any]
    output_persisted: bool

    def summary(self) -> dict[str, Any]:
        latency = self.receipt["cpu_observation"]["latency_ms"]
        return {
            "schema_version": "myis.armindex-a1.1-adapter-fixture-summary.v1",
            "fixture_id": FIXTURE_ID,
            "status": self.receipt["status"],
            "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
            "task_id": "A1.1",
            "evidence_class": "engineering_fixture",
            "scientific_authority": False,
            "arm01_cpu_path": "PASS",
            "registered_arms": self.manifest["aggregate_counts"]["registered_arms"],
            "dense_arms_blocked": self.manifest["aggregate_counts"]["dense_arms_blocked"],
            "compile_p50_ms": latency["compile"]["p50"],
            "index_build_p50_ms": latency["index_build"]["p50"],
            "search_workload_p50_ms": latency["search_workload"]["p50"],
            "search_throughput_qps": self.receipt["cpu_observation"]["search_throughput_qps"],
            "manifest_sha256": self.manifest["manifest_sha256"],
            "receipt_sha256": self.receipt["receipt_sha256"],
            "output_persisted": self.output_persisted,
            "real_counters": dict(self.receipt["real_counters"]),
        }


def run_adapter_fixture(
    output_dir: Path | None = None,
    *,
    repetitions: int = 11,
) -> AdapterFixtureArtifacts:
    """Run the A1.1 fixture in a disposable directory unless explicitly persisted."""

    _validate_repetitions(repetitions)
    if output_dir is None:
        with tempfile.TemporaryDirectory(prefix="myis-armindex-a11-") as temporary:
            result = _execute(Path(temporary), repetitions=repetitions)
        return AdapterFixtureArtifacts(result.manifest, result.receipt, output_persisted=False)
    return _execute(
        _prepare_output(output_dir),
        repetitions=repetitions,
        output_persisted=True,
    )


def validate_adapter_fixture_artifacts(
    manifest: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> None:
    if manifest.get("schema_version") != "myis.armindex-a1.1-adapter-fixture-manifest.v1":
        raise ValueError("unsupported A1.1 adapter fixture manifest")
    if receipt.get("schema_version") != "myis.armindex-a1.1-adapter-fixture-receipt.v1":
        raise ValueError("unsupported A1.1 adapter fixture receipt")
    _validate_self_hash(manifest, "manifest_sha256")
    _validate_self_hash(receipt, "receipt_sha256")
    if receipt.get("manifest_sha256") != manifest.get("manifest_sha256"):
        raise ValueError("A1.1 receipt is not bound to its manifest")
    for artifact in (manifest, receipt):
        if artifact.get("phase_id") != "A1_BASELINES_AND_MULTI_ARM_SCREENING":
            raise ValueError("A1.1 artifact phase identity is invalid")
        if artifact.get("task_id") != "A1.1":
            raise ValueError("A1.1 artifact task identity is invalid")
        if artifact.get("scientific_authority") is not False:
            raise ValueError("A1.1 fixture cannot claim scientific authority")
        if artifact.get("protected_data_accessed") is not False:
            raise ValueError("A1.1 fixture cannot access protected data")
    if receipt.get("status") != "PASS":
        raise ValueError("A1.1 adapter fixture did not pass")
    counts = manifest.get("aggregate_counts", {})
    if counts.get("registered_arms") != 5 or counts.get("runnable_cpu_arms") != 1:
        raise ValueError("A1.1 arm registry counts are invalid")
    if counts.get("dense_arms_blocked") != 4:
        raise ValueError("A1.1 dense adapters did not fail closed")
    backend = manifest.get("arm01_backend", {})
    if backend.get("fixture_backend_id") != FIXTURE_BACKEND_ID:
        raise ValueError("A1.1 ARM-01 fixture backend identity drifted")
    if backend.get("measured_backend_id") != "lexical/bm25s" or backend.get("measured_lock_ready") is not False:
        raise ValueError("A1.1 must not promote the fixture backend to the measured ARM-01 lock")
    counters = receipt.get("real_counters", {})
    if not isinstance(counters, Mapping) or any(value != 0 for value in counters.values()):
        raise ValueError("A1.1 fixture cannot change real counters")
    resources = receipt.get("resource_counters", {})
    if not isinstance(resources, Mapping) or any(value != 0 for value in resources.values()):
        raise ValueError("A1.1 fixture cannot consume paid or GPU resources")
    safety = receipt.get("safety", {})
    required_false = {
        "protected_data_accessed",
        "measured_execution",
        "network_used",
        "model_downloaded",
        "gpu_used",
        "paid_api_used",
        "provider_switched",
        "selection_opened",
        "final_opened",
        "app_sparse_index_payload_opened",
    }
    if not isinstance(safety, Mapping) or any(safety.get(key) is not False for key in required_false):
        raise ValueError("A1.1 safety boundary is invalid")
    if safety.get("synthetic_inputs_only") is not True or safety.get("cpu_only") is not True:
        raise ValueError("A1.1 must remain synthetic-only and CPU-only")
    observation = receipt.get("cpu_observation", {})
    if observation.get("peak_python_allocation_bytes", 0) <= 0:
        raise ValueError("A1.1 CPU allocation observation is invalid")
    if observation.get("search_throughput_qps", 0) <= 0:
        raise ValueError("A1.1 CPU throughput observation is invalid")
    for operation in ("compile", "index_build", "search_workload", "aggregate_evaluation"):
        values = observation.get("latency_ms", {}).get(operation, {})
        ordered = [values.get(key) for key in ("p50", "p95", "p99")]
        if any(not isinstance(value, (int, float)) or value < 0 for value in ordered):
            raise ValueError("A1.1 latency observation is invalid")
        if ordered != sorted(ordered):
            raise ValueError("A1.1 latency percentiles are not monotonic")
    assert_aggregate_only(manifest)
    assert_aggregate_only(receipt)


def _execute(
    output: Path,
    *,
    repetitions: int,
    output_persisted: bool = False,
) -> AdapterFixtureArtifacts:
    program = _program()
    documents = _documents()
    cases = _cases()
    judgments = _judgments()
    compiled = compile_program(program, documents)
    reversed_compiled = compile_program(program, reversed(documents))
    if compiled.as_dict() != reversed_compiled.as_dict():
        raise ValueError("A1.1 representation compilation is not input-order deterministic")

    registry = ArmRegistry()
    capabilities = registry.capabilities()
    if tuple(item.arm_id for item in capabilities) != ARM_IDS:
        raise ValueError("A1.1 registry ordering drifted")
    dense_block_count = 0
    for arm_id in ARM_IDS[1:]:
        adapter = registry.get(arm_id)
        try:
            adapter.build_index(compiled)
        except ArmUnavailableError:
            pass
        else:
            raise ValueError(f"{arm_id} built an index without an offline model lock")
        try:
            adapter.search(None, case_id="synthetic-fixture", text="fixture", top_k=1)
        except ArmUnavailableError:
            dense_block_count += 1
        else:
            raise ValueError(f"{arm_id} searched without an offline model lock")

    arm01 = registry.get("ARM-01")
    warm_index = arm01.build_index(compiled)
    _execute_workload(arm01, warm_index, cases, judgments)

    compile_samples: list[int] = []
    index_samples: list[int] = []
    search_samples: list[int] = []
    evaluation_samples: list[int] = []
    execution_commitments: set[str] = set()
    final_index: Any = None
    final_metrics: Mapping[str, Any] | None = None
    started_wall = time.perf_counter_ns()
    started_cpu = time.process_time_ns()
    gc.collect()
    tracemalloc.start()
    try:
        for _ in range(repetitions):
            started = time.perf_counter_ns()
            repeated_compiled = compile_program(program, documents)
            compile_samples.append(time.perf_counter_ns() - started)

            started = time.perf_counter_ns()
            index = arm01.build_index(repeated_compiled)
            index_samples.append(time.perf_counter_ns() - started)

            started = time.perf_counter_ns()
            family_rows, execution_sha256 = _search_rows(arm01, index, cases)
            search_samples.append(time.perf_counter_ns() - started)

            started = time.perf_counter_ns()
            metrics = evaluate_family_rankings(family_rows, judgments)
            evaluation_samples.append(time.perf_counter_ns() - started)

            execution_commitments.add(
                canonical_sha256(
                    {
                        "execution_sha256": execution_sha256,
                        "metrics_sha256": metrics["metrics_sha256"],
                    }
                )
            )
            final_index = index
            final_metrics = metrics
        _current, peak_python_allocation_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    if len(execution_commitments) != 1 or final_index is None or final_metrics is None:
        raise ValueError("A1.1 ARM-01 execution is not deterministic")

    manifest_unsigned = {
        "schema_version": "myis.armindex-a1.1-adapter-fixture-manifest.v1",
        "fixture_id": FIXTURE_ID,
        "campaign_id": "armindex-multiretriever-v2",
        "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
        "task_id": "A1.1",
        "status": "frozen_before_execution",
        "evidence_class": "engineering_fixture",
        "scientific_authority": False,
        "claim_boundary": "synthetic_adapter_and_arm01_cpu_path_only_no_measured_parity",
        "protected_data_accessed": False,
        "arm01_backend": {
            "arm_id": "ARM-01",
            "fixture_backend_id": FIXTURE_BACKEND_ID,
            "measured_backend_id": "lexical/bm25s",
            "measured_lock_ready": False,
            "fixture_only": True,
            "cpu_supported": True,
            "gpu_required": False,
            "k1": 1.2,
            "b": 0.75,
        },
        "adapter_scaffold": [item.as_dict() for item in capabilities],
        "aggregate_counts": {
            "registered_arms": len(capabilities),
            "runnable_cpu_arms": sum(item.cpu_supported for item in capabilities),
            "dense_arms_blocked": dense_block_count,
            "synthetic_documents": len(documents),
            "synthetic_families": len({item["family_id"] for item in documents}),
            "synthetic_cases": len(cases),
            "compiled_units": len(compiled.units),
        },
        "commitments": {
            "logical_program_sha256": compiled.logical_program_sha256,
            "compiled_representation_sha256": compiled.compiled_representation_sha256,
            "source_sha256": compiled.source_sha256,
            "index_sha256": final_index.index_sha256,
            "execution_sha256": next(iter(execution_commitments)),
            "metrics_sha256": final_metrics["metrics_sha256"],
        },
        "compiler": {
            "family_aggregation": compiled.family_aggregation,
            "estimated_storage_bytes": compiled.estimated_storage_bytes,
            "estimated_token_count": compiled.estimated_token_count,
            "omitted_unit_count": compiled.omitted_unit_count,
            "truncated_span_count": compiled.truncated_span_count,
        },
        "asset_use": [
            {"asset_id": "APP-DAPFAM-TEXT-PRIMITIVES", "use": "synthetic_fixture_pattern"},
            {"asset_id": "APP-SPARSE-FTS-INDEXES", "use": "pointer_only_not_opened"},
            {"asset_id": "APP-DAPFAM-PROTECTED", "use": "not_accessed"},
        ],
        "safety": {
            "synthetic_inputs_only": True,
            "cpu_only": True,
            "network_required": False,
            "model_download_required": False,
            "gpu_required": False,
            "paid_api_required": False,
            "app_sparse_index_payload_used": False,
        },
    }
    manifest = {**manifest_unsigned, "manifest_sha256": canonical_sha256(manifest_unsigned)}
    total_search_ns = sum(search_samples)
    elapsed_wall_ns = time.perf_counter_ns() - started_wall
    elapsed_cpu_ns = time.process_time_ns() - started_cpu
    receipt_unsigned = {
        "schema_version": "myis.armindex-a1.1-adapter-fixture-receipt.v1",
        "fixture_id": FIXTURE_ID,
        "campaign_id": "armindex-multiretriever-v2",
        "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
        "task_id": "A1.1",
        "status": "PASS",
        "evidence_class": "engineering_fixture",
        "scientific_authority": False,
        "claim_boundary": "synthetic_adapter_and_arm01_cpu_path_only_no_measured_parity",
        "protected_data_accessed": False,
        "manifest_sha256": manifest["manifest_sha256"],
        "deterministic_execution_sha256": next(iter(execution_commitments)),
        "synthetic_metrics": final_metrics["metrics"],
        "cpu_observation": {
            "host": {
                "operating_system": platform.system(),
                "machine": platform.machine(),
                "python_implementation": platform.python_implementation(),
                "python_version": platform.python_version(),
                "logical_cpu_count": os.cpu_count(),
            },
            "repetitions": repetitions,
            "workload_calls": repetitions * len(cases),
            "wall_time_seconds": round(elapsed_wall_ns / 1_000_000_000, 9),
            "process_cpu_time_seconds": round(elapsed_cpu_ns / 1_000_000_000, 9),
            "latency_ms": {
                "compile": _latency_summary(compile_samples),
                "index_build": _latency_summary(index_samples),
                "search_workload": _latency_summary(search_samples),
                "aggregate_evaluation": _latency_summary(evaluation_samples),
            },
            "search_throughput_qps": round(
                (repetitions * len(cases)) / (total_search_ns / 1_000_000_000),
                6,
            ),
            "peak_python_allocation_bytes": peak_python_allocation_bytes,
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
        "checks": {
            "five_arm_registry": "PASS",
            "arm01_cpu_compile_index_search_evaluate": "PASS",
            "representation_input_order_determinism": "PASS",
            "repeated_execution_determinism": "PASS",
            "dense_arms_fail_closed": "PASS",
            "aggregate_only": "PASS",
            "write_once_artifacts": "PASS",
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
            "provider_switched": False,
            "selection_opened": False,
            "final_opened": False,
            "app_sparse_index_payload_opened": False,
        },
        "next_action": "Prepare and validate an A1.2 measured execution contract; do not launch GPU screening",
    }
    receipt = {**receipt_unsigned, "receipt_sha256": canonical_sha256(receipt_unsigned)}
    validate_adapter_fixture_artifacts(manifest, receipt)
    _write_once(output / "manifest.json", manifest)
    _write_once(output / "receipt.json", receipt)
    restored_manifest = json.loads((output / "manifest.json").read_text(encoding="ascii"))
    restored_receipt = json.loads((output / "receipt.json").read_text(encoding="ascii"))
    validate_adapter_fixture_artifacts(restored_manifest, restored_receipt)
    return AdapterFixtureArtifacts(manifest, receipt, output_persisted=output_persisted)


def _search_rows(adapter: Any, index: Any, cases: Mapping[str, str]) -> tuple[dict[str, list[str]], str]:
    family_rows: dict[str, list[str]] = {}
    safe_commitment: dict[str, list[dict[str, Any]]] = {}
    for case_id, text in sorted(cases.items()):
        ranking = adapter.search(index, case_id=case_id, text=text, top_k=100)
        family_rows[case_id] = [hit.family_id for hit in ranking.hits]
        safe_commitment[case_id] = [
            {
                "family_id": hit.family_id,
                "publication_id": hit.publication_id,
                "unit_id": hit.unit_id,
                "rank": hit.rank,
                "score": hit.score,
            }
            for hit in ranking.hits
        ]
    return family_rows, canonical_sha256(safe_commitment)


def _execute_workload(
    adapter: Any,
    index: Any,
    cases: Mapping[str, str],
    judgments: Mapping[str, Mapping[str, int]],
) -> None:
    family_rows, _commitment = _search_rows(adapter, index, cases)
    evaluate_family_rankings(family_rows, judgments)


def _validate_repetitions(repetitions: int) -> None:
    if isinstance(repetitions, bool) or not isinstance(repetitions, int):
        raise ValueError("repetitions must be an integer")
    if not MIN_REPETITIONS <= repetitions <= MAX_REPETITIONS:
        raise ValueError(f"repetitions must be in [{MIN_REPETITIONS}, {MAX_REPETITIONS}]")
