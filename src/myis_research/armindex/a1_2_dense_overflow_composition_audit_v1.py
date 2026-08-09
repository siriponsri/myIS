"""Full aggregate-only validation of the authorized dense overflow policy."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from concurrent.futures import Executor, ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..dapfam_p1 import iter_arrow_rows, resolve_cache
from ..kernel.canonical import canonical_bytes, canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a1_2_dense_overflow_adapter_v1 import (
    IMPLEMENTATION_VERSION,
    DenseOverflowAdapterError,
    fit_plan,
    overflow_plan,
    split_template,
    template_for,
    tokenizer_ids,
)
from .a1_2_dense_overflow_inventory_v1 import (
    ARM_IDS,
    BINDING_CONTRACT_PATH,
    P02_REPAIR_PATH,
    PROGRAM_IDS,
    PROGRAM_SET_PATH,
    SOURCE_CONTRACT_PATH,
    _logical_units,
    _model_inputs,
    _read_rep_dev,
)

CONTRACT_PATH = Path("control/armindex/a1.2/dense-overflow-adapter-repair.v14.json")
INVENTORY_PATH = Path("outputs/audits/armindex/a1.2-dense-overflow-inventory-20260808.json")
SCHEMA_VERSION = "myis.armindex-a1.2-dense-overflow-composition-audit.v1"


class DenseOverflowCompositionAuditError(ValueError):
    """Fail-closed workload composition error."""


@dataclass
class _CompositionCounts:
    effective_input_limit: int
    logical_units: int = 0
    overflow_logical_units: int = 0
    physical_windows: int = 0
    maximum_raw_rendered_tokens: int = 0
    maximum_physical_window_tokens: int = 0
    overflow_source_tokens: int = 0
    represented_overflow_source_tokens: int = 0
    source_tokens_dropped: int = 0
    source_tokens_overlapped: int = 0
    truncation_count: int = 0
    fallback_count: int = 0
    template_parity_failures: int = 0
    _digest: Any = field(default_factory=hashlib.sha256, repr=False)

    def add(self, plan: Any) -> None:
        self.logical_units += 1
        self.overflow_logical_units += plan.mode == "DENSE_OVERFLOW_COMPOSED"
        self.physical_windows += len(plan.physical_windows)
        self.maximum_raw_rendered_tokens = max(
            self.maximum_raw_rendered_tokens, plan.raw_rendered_tokens
        )
        self.maximum_physical_window_tokens = max(
            self.maximum_physical_window_tokens,
            max(window.rendered_token_count for window in plan.physical_windows),
        )
        if plan.mode == "DENSE_OVERFLOW_COMPOSED":
            self.overflow_source_tokens += int(plan.source_token_count)
            self.represented_overflow_source_tokens += int(plan.source_tokens_represented)
        self.source_tokens_dropped += plan.source_tokens_dropped
        self.source_tokens_overlapped += plan.source_tokens_overlapped
        self.template_parity_failures += not plan.template_token_parity
        self._digest.update(canonical_bytes(plan.plan_sha256))

    def as_dict(self) -> dict[str, Any]:
        if self.logical_units < 1:
            raise DenseOverflowCompositionAuditError("composition cell is empty")
        status = (
            "PASS"
            if self.maximum_physical_window_tokens <= self.effective_input_limit
            and self.overflow_source_tokens == self.represented_overflow_source_tokens
            and all(
                value == 0
                for value in (
                    self.source_tokens_dropped,
                    self.source_tokens_overlapped,
                    self.truncation_count,
                    self.fallback_count,
                    self.template_parity_failures,
                )
            )
            else "FAIL"
        )
        return {
            "status": status,
            "effective_input_limit": self.effective_input_limit,
            "logical_unit_count": self.logical_units,
            "overflow_logical_unit_count": self.overflow_logical_units,
            "overflow_incidence": self.overflow_logical_units / self.logical_units,
            "physical_window_count": self.physical_windows,
            "maximum_raw_rendered_tokens": self.maximum_raw_rendered_tokens,
            "maximum_physical_window_tokens": self.maximum_physical_window_tokens,
            "overflow_source_token_count": self.overflow_source_tokens,
            "represented_overflow_source_token_count": self.represented_overflow_source_tokens,
            "source_token_drop_count": self.source_tokens_dropped,
            "source_token_overlap_count": self.source_tokens_overlapped,
            "truncation_count": self.truncation_count,
            "fallback_count": self.fallback_count,
            "template_parity_failure_count": self.template_parity_failures,
            "plan_manifest_sha256": self._digest.hexdigest(),
        }


def _read_json(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DenseOverflowCompositionAuditError(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise DenseOverflowCompositionAuditError(f"{role} must be an object")
    return value


def _validate_contract(root: Path) -> dict[str, Any]:
    contract = _read_json(root / CONTRACT_PATH, role="dense overflow repair contract")
    unsigned = {key: item for key, item in contract.items() if key != "contract_sha256"}
    if contract.get("contract_sha256") != canonical_sha256(unsigned):
        raise DenseOverflowCompositionAuditError("dense overflow repair contract self-hash mismatch")
    implementation = contract.get("implementation", {})
    if (
        contract.get("status") != "FROZEN_ADDITIVE_PRE_MEASUREMENT_REPAIR"
        or implementation.get("version") != IMPLEMENTATION_VERSION
        or implementation.get("planner_source_sha256")
        != file_sha256(root / implementation.get("planner_source_uri", "missing"))
        or contract.get("authorization", {}).get("measured_retrieval_allowed") is not False
    ):
        raise DenseOverflowCompositionAuditError("dense overflow repair contract drifted")
    return contract


def _batch_plans(
    tokenizer: Any,
    *,
    texts: Sequence[str],
    arm_id: str,
    side: str,
    effective_limit: int,
) -> tuple[Any, ...]:
    template = template_for(arm_id, side=side)
    prefix, suffix = split_template(template)
    rendered_texts = [template.format(text=text) for text in texts]
    full = tokenizer_ids(tokenizer, rendered_texts, add_special_tokens=True)
    overflow_indexes = [index for index, values in enumerate(full) if len(values) > effective_limit]
    overflow_sources: dict[int, tuple[int, ...]] = {}
    overflow_rendered: dict[int, tuple[int, ...]] = {}
    if overflow_indexes:
        overflow_texts = [texts[index] for index in overflow_indexes]
        overflow_sources = dict(
            zip(
                overflow_indexes,
                tokenizer_ids(tokenizer, overflow_texts, add_special_tokens=False),
                strict=True,
            )
        )
        overflow_rendered = dict(
            zip(
                overflow_indexes,
                tokenizer_ids(
                    tokenizer,
                    [rendered_texts[index] for index in overflow_indexes],
                    add_special_tokens=False,
                ),
                strict=True,
            )
        )
    prefix_ids = (
        tokenizer_ids(tokenizer, [prefix], add_special_tokens=False)[0] if prefix else ()
    )
    suffix_ids = (
        tokenizer_ids(tokenizer, [suffix], add_special_tokens=False)[0] if suffix else ()
    )
    plans = []
    for index, full_ids in enumerate(full):
        if index not in overflow_sources:
            plans.append(fit_plan(full_rendered_ids=full_ids, effective_limit=effective_limit))
            continue
        plans.append(
            overflow_plan(
                source_ids=overflow_sources[index],
                rendered_without_special_ids=overflow_rendered[index],
                full_rendered_ids=full_ids,
                prefix_ids=prefix_ids,
                suffix_ids=suffix_ids,
                effective_limit=effective_limit,
            )
        )
    return tuple(plans)


def _flush(
    buffers: Mapping[str, list[str]],
    *,
    side: str,
    tokenizers: Mapping[str, Any],
    bindings: Mapping[str, Mapping[str, Any]],
    counts: Mapping[str, Mapping[str, _CompositionCounts]],
    executor: Executor,
) -> None:
    for program_id, texts in buffers.items():
        if not texts:
            continue
        futures = {
            arm_id: executor.submit(
                _batch_plans,
                tokenizers[arm_id],
                texts=texts,
                arm_id=arm_id,
                side=side,
                effective_limit=int(bindings[arm_id]["effective_input_limit"]),
            )
            for arm_id in ARM_IDS
        }
        for arm_id in ARM_IDS:
            try:
                plans = futures[arm_id].result()
            except DenseOverflowAdapterError as error:
                raise DenseOverflowCompositionAuditError(
                    f"composition failed for {arm_id}/{program_id}/{side}: {error}"
                ) from error
            for plan in plans:
                counts[arm_id][program_id].add(plan)
        texts.clear()


def _corpus(
    rows: Iterable[Mapping[str, Any]],
    *,
    tokenizers: Mapping[str, Any],
    bindings: Mapping[str, Mapping[str, Any]],
    batch_size: int,
) -> tuple[dict[str, dict[str, _CompositionCounts]], int]:
    counts = {
        arm: {
            program: _CompositionCounts(int(bindings[arm]["effective_input_limit"]))
            for program in PROGRAM_IDS
        }
        for arm in ARM_IDS
    }
    buffers = {program: [] for program in PROGRAM_IDS}
    thresholds = {
        "P00-TAC-DOC": batch_size,
        "P01-TA-DOC": batch_size * 2,
        "P02-CLAIM1": batch_size * 2,
        "P03-PASSAGE": batch_size * 8,
        "P04-SECTION-MULTIVIEW": batch_size * 2,
    }
    seen: set[str] = set()
    with ThreadPoolExecutor(max_workers=len(ARM_IDS), thread_name_prefix="overflow-compose") as executor:
        for row in rows:
            source_id = row.get("relevant_id")
            if not isinstance(source_id, str) or not source_id or source_id in seen:
                raise DenseOverflowCompositionAuditError("corpus identity is missing or duplicated")
            seen.add(source_id)
            for program_id, units in _logical_units(row, source_id=source_id).items():
                buffers[program_id].extend(units)
                if len(buffers[program_id]) >= thresholds[program_id]:
                    _flush(
                        {key: value if key == program_id else [] for key, value in buffers.items()},
                        side="corpus",
                        tokenizers=tokenizers,
                        bindings=bindings,
                        counts=counts,
                        executor=executor,
                    )
            if len(seen) % 5_000 == 0:
                print(
                    json.dumps(
                        {"composition_progress_corpus_families": len(seen)},
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    flush=True,
                )
        _flush(
            buffers,
            side="corpus",
            tokenizers=tokenizers,
            bindings=bindings,
            counts=counts,
            executor=executor,
        )
    return counts, len(seen)


def _queries(
    rows: Iterable[Mapping[str, Any]],
    *,
    rep_dev: set[str],
    tokenizers: Mapping[str, Any],
    bindings: Mapping[str, Mapping[str, Any]],
) -> dict[str, _CompositionCounts]:
    texts: list[str] = []
    observed: set[str] = set()
    for row in rows:
        source_id = row.get("query_id")
        if not isinstance(source_id, str) or source_id not in rep_dev:
            continue
        if source_id in observed:
            raise DenseOverflowCompositionAuditError("REP-DEV identity is duplicated")
        observed.add(source_id)
        texts.append(_logical_units(row, source_id=source_id)["P00-TAC-DOC"][0])
    if observed != rep_dev or len(texts) != 150:
        raise DenseOverflowCompositionAuditError("REP-DEV query coverage is incomplete")
    result = {
        arm: _CompositionCounts(int(bindings[arm]["effective_input_limit"])) for arm in ARM_IDS
    }
    with ThreadPoolExecutor(max_workers=len(ARM_IDS), thread_name_prefix="overflow-query") as executor:
        futures = {
            arm: executor.submit(
                _batch_plans,
                tokenizers[arm],
                texts=texts,
                arm_id=arm,
                side="rep_dev_queries",
                effective_limit=int(bindings[arm]["effective_input_limit"]),
            )
            for arm in ARM_IDS
        }
        for arm in ARM_IDS:
            for plan in futures[arm].result():
                result[arm].add(plan)
    return result


def _combine(corpus: _CompositionCounts, queries: _CompositionCounts) -> dict[str, Any]:
    values = {}
    for name, first, second in (
        ("logical_unit_count", corpus.logical_units, queries.logical_units),
        ("overflow_logical_unit_count", corpus.overflow_logical_units, queries.overflow_logical_units),
        ("physical_window_count", corpus.physical_windows, queries.physical_windows),
        ("overflow_source_token_count", corpus.overflow_source_tokens, queries.overflow_source_tokens),
        (
            "represented_overflow_source_token_count",
            corpus.represented_overflow_source_tokens,
            queries.represented_overflow_source_tokens,
        ),
        ("source_token_drop_count", corpus.source_tokens_dropped, queries.source_tokens_dropped),
        ("source_token_overlap_count", corpus.source_tokens_overlapped, queries.source_tokens_overlapped),
        ("truncation_count", corpus.truncation_count, queries.truncation_count),
        ("fallback_count", corpus.fallback_count, queries.fallback_count),
        ("template_parity_failure_count", corpus.template_parity_failures, queries.template_parity_failures),
    ):
        values[name] = first + second
    values.update(
        {
            "status": "PASS",
            "effective_input_limit": corpus.effective_input_limit,
            "overflow_incidence": values["overflow_logical_unit_count"] / values["logical_unit_count"],
            "maximum_raw_rendered_tokens": max(
                corpus.maximum_raw_rendered_tokens, queries.maximum_raw_rendered_tokens
            ),
            "maximum_physical_window_tokens": max(
                corpus.maximum_physical_window_tokens, queries.maximum_physical_window_tokens
            ),
            "plan_manifest_sha256": canonical_sha256(
                [corpus._digest.hexdigest(), queries._digest.hexdigest()]
            ),
        }
    )
    if (
        values["maximum_physical_window_tokens"] > values["effective_input_limit"]
        or values["overflow_source_token_count"]
        != values["represented_overflow_source_token_count"]
        or any(
            values[key] != 0
            for key in (
                "source_token_drop_count",
                "source_token_overlap_count",
                "truncation_count",
                "fallback_count",
                "template_parity_failure_count",
            )
        )
    ):
        values["status"] = "FAIL"
    return values


def audit(
    repository_root: Path,
    *,
    cache_root: Path,
    protected_rep_dev_path: Path,
    model_root: Path,
    batch_size: int = 128,
) -> dict[str, Any]:
    if batch_size < 1 or batch_size > 512:
        raise DenseOverflowCompositionAuditError("batch size must be between 1 and 512")
    if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("TRANSFORMERS_OFFLINE") != "1":
        raise DenseOverflowCompositionAuditError("offline tokenizer environment is required")
    root = repository_root.resolve()
    contract = _validate_contract(root)
    inventory = _read_json(root / INVENTORY_PATH, role="raw compatibility inventory")
    if inventory.get("inventory_sha256") != canonical_sha256(
        {key: item for key, item in inventory.items() if key != "inventory_sha256"}
    ):
        raise DenseOverflowCompositionAuditError("raw compatibility inventory self-hash mismatch")
    layout = resolve_cache(cache_root, root)
    rep_dev = _read_rep_dev(protected_rep_dev_path)
    tokenizers, bindings = _model_inputs(root, model_root.resolve(strict=True))
    corpus_paths = tuple(path for path in layout.files["corpus"] if path.suffix == ".arrow")
    query_paths = tuple(path for path in layout.files["queries"] if path.suffix == ".arrow")
    corpus_counts, family_count = _corpus(
        iter_arrow_rows(
            corpus_paths, ("relevant_id", "title_en", "abstract_en", "claims_text")
        ),
        tokenizers=tokenizers,
        bindings=bindings,
        batch_size=batch_size,
    )
    query_counts = _queries(
        iter_arrow_rows(
            query_paths, ("query_id", "title_en", "abstract_en", "claims_text")
        ),
        rep_dev=rep_dev,
        tokenizers=tokenizers,
        bindings=bindings,
    )
    cells = {}
    all_pass = True
    for arm in ARM_IDS:
        cells[arm] = {}
        for program in PROGRAM_IDS:
            corpus_value = corpus_counts[arm][program].as_dict()
            query_value = query_counts[arm].as_dict()
            combined = _combine(corpus_counts[arm][program], query_counts[arm])
            cells[arm][program] = {
                "corpus": corpus_value,
                "rep_dev_queries": query_value,
                "combined": combined,
            }
            raw = inventory["cells"][arm][program]
            if any(
                raw[side]["overflow_logical_unit_count"]
                != cells[arm][program][side]["overflow_logical_unit_count"]
                for side in ("corpus", "rep_dev_queries", "combined")
            ):
                raise DenseOverflowCompositionAuditError("raw inventory parity failed")
            all_pass &= all(
                cells[arm][program][side]["status"] == "PASS"
                for side in ("corpus", "rep_dev_queries", "combined")
            )
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "audit_id": "a1.2-dense-overflow-composition-20260808-v1",
        "status": "PASS" if all_pass else "FAIL_CLOSED",
        "evidence_class": "pre_measurement_owner_local_compatibility_validation",
        "scientific_authority": False,
        "claim_boundary": (
            "Aggregate-only deterministic physical-window compatibility evidence. It contains "
            "no text, identifiers, split members, qrels, embeddings, rankings, retrieval outcomes, "
            "provider values, execution authority, or scientific result."
        ),
        "scope": {
            "dense_program_arm_cells": 20,
            "all_program_arm_cells_compatible": 25 if all_pass else 5,
            "rep_dev_query_count": 150,
            "corpus_family_count": family_count,
            "bm25_status": "NOT_APPLICABLE_UNBOUNDED_LEXICAL_EXISTING_PATH",
        },
        "bindings": {
            "contract_uri": CONTRACT_PATH.as_posix(),
            "contract_file_sha256": file_sha256(root / CONTRACT_PATH),
            "contract_sha256": contract["contract_sha256"],
            "raw_inventory_uri": INVENTORY_PATH.as_posix(),
            "raw_inventory_file_sha256": file_sha256(root / INVENTORY_PATH),
            "raw_inventory_sha256": inventory["inventory_sha256"],
            "source_contract_file_sha256": file_sha256(root / SOURCE_CONTRACT_PATH),
            "program_set_file_sha256": file_sha256(root / PROGRAM_SET_PATH),
            "p02_repair_file_sha256": file_sha256(root / P02_REPAIR_PATH),
            "binding_contract_file_sha256": file_sha256(root / BINDING_CONTRACT_PATH),
            "rep_dev_workload_commitment": file_sha256(protected_rep_dev_path.resolve(strict=True)),
            "dense_arms": bindings,
        },
        "composition_semantics": contract["composition_semantics"],
        "arm_postprocessing": contract["arm_postprocessing"],
        "cells": cells,
        "requirements": {
            "compatible_cells_25_of_25": all_pass,
            "rep_dev_query_coverage_fraction": 1.0,
            "required_corpus_logical_unit_coverage_fraction": 1.0,
            "every_physical_window_within_limit": all_pass,
            "zero_omitted_source_tokens": all_pass,
            "zero_silent_truncation": all_pass,
            "zero_fallback": all_pass,
        },
        "safety": {
            "retrieval_results_inspected": False,
            "retrieval_started": False,
            "provider_contacted": False,
            "paid_api_used": False,
            "selection_accessed": False,
            "final_accessed": False,
            "model_or_weight_changed": False,
            "historical_v11_v12_r3_v13_changed": False,
        },
    }
    assert_aggregate_only(body)
    body["audit_sha256"] = canonical_sha256(body)
    return body


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    text = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_text(encoding="ascii") != text:
            raise DenseOverflowCompositionAuditError("existing composition audit differs")
        return
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-dense-overflow-composition-audit-v1")
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--protected-rep-dev", type=Path, required=True)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(
        args.repository_root,
        cache_root=args.cache_root,
        protected_rep_dev_path=args.protected_rep_dev,
        model_root=args.model_root,
        batch_size=args.batch_size,
    )
    output = args.output.resolve(strict=False)
    if not output.is_relative_to(args.repository_root.resolve()):
        raise DenseOverflowCompositionAuditError("composition output must remain in repository")
    _atomic_json(output, result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "compatible_cells": result["scope"]["all_program_arm_cells_compatible"],
                "audit_sha256": result["audit_sha256"],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
