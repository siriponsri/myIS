"""Aggregate-only A1.2 dense input-limit inventory before overflow repair.

The audit reads the pinned DAPFAM cache and frozen REP-DEV membership locally,
but emits only aggregate counts, incidences, and cryptographic commitments.  It
does not encode vectors, perform retrieval, or inspect evaluation outcomes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from concurrent.futures import Executor, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..dapfam_p1 import iter_arrow_rows, resolve_cache
from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a1_2_owner_local_protected_compiler_v12 import _load_dense_tokenizer
from .a1_2_p02_first_claim_v1 import first_claim_segment
from .scientific_common_programs_v11 import (
    PublicationRecord,
    _family_text,
    _passages,
)

SOURCE_CONTRACT_PATH = Path("control/assets/dapfam-p1-source.v1.json")
BINDING_CONTRACT_PATH = Path(
    "control/owner-local/a1.2-compiled-program-bindings-contract.v12.json"
)
P02_REPAIR_PATH = Path("control/armindex/a1.2/p02-first-claim-repair.v1.json")
PROGRAM_SET_PATH = Path("control/armindex/a1.2/common-program-set.v11.json")

ARM_IDS = ("ARM-02", "ARM-03", "ARM-04", "ARM-05")
PROGRAM_IDS = (
    "P00-TAC-DOC",
    "P01-TA-DOC",
    "P02-CLAIM1",
    "P03-PASSAGE",
    "P04-SECTION-MULTIVIEW",
)
SCHEMA_VERSION = "myis.armindex-a1.2-dense-overflow-inventory.v1"


class DenseOverflowInventoryError(ValueError):
    """Fail-closed inventory error without protected payload details."""


@dataclass
class _Counts:
    logical_units: int = 0
    overflow_units: int = 0
    maximum_rendered_tokens: int = 0

    def update(self, lengths: Sequence[int], *, limit: int) -> None:
        if not lengths or any(not isinstance(value, int) or value < 1 for value in lengths):
            raise DenseOverflowInventoryError("tokenizer returned an invalid rendered length")
        self.logical_units += len(lengths)
        self.overflow_units += sum(value > limit for value in lengths)
        self.maximum_rendered_tokens = max(self.maximum_rendered_tokens, max(lengths))

    def as_dict(self) -> dict[str, int | float]:
        if self.logical_units < 1:
            raise DenseOverflowInventoryError("inventory cell has no logical units")
        return {
            "logical_unit_count": self.logical_units,
            "overflow_logical_unit_count": self.overflow_units,
            "overflow_incidence": self.overflow_units / self.logical_units,
            "maximum_rendered_tokens": self.maximum_rendered_tokens,
        }


def _read_json(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DenseOverflowInventoryError(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise DenseOverflowInventoryError(f"{role} must be an object")
    return value


def _read_rep_dev(path: Path) -> set[str]:
    value = _read_json(path.resolve(strict=True), role="protected REP-DEV subdivision")
    if (
        value.get("schema_version")
        != "myis.armindex-a1.2-rep-harness-protected-membership.v1"
        or not isinstance(value.get("rep_dev"), list)
        or len(value["rep_dev"]) != 150
    ):
        raise DenseOverflowInventoryError("protected REP-DEV subdivision is invalid")
    identifiers = {str(item) for item in value["rep_dev"]}
    if len(identifiers) != 150 or any(not item for item in identifiers):
        raise DenseOverflowInventoryError("REP-DEV must contain 150 unique identifiers")
    unsigned = {key: item for key, item in value.items() if key != "protected_membership_sha256"}
    if value.get("protected_membership_sha256") != canonical_sha256(unsigned):
        raise DenseOverflowInventoryError("protected REP-DEV self-hash mismatch")
    return identifiers


def _opaque(prefix: str, value: str) -> str:
    return f"{prefix}-{hashlib.sha256(value.encode('utf-8')).hexdigest()[:32]}"


def _record(row: Mapping[str, Any], *, source_id: str) -> dict[str, Any]:
    return {
        "family_token": _opaque("F", source_id),
        "publication_token": _opaque("P", source_id),
        "publication_ordinal": 0,
        "title_en": row.get("title_en"),
        "abstract_en": row.get("abstract_en"),
        "claims_text": row.get("claims_text"),
        "claims": [],
    }


def _logical_units(row: Mapping[str, Any], *, source_id: str) -> dict[str, tuple[str, ...]]:
    """Compile the unchanged slots plus the authorized P02 executable successor."""

    raw = _record(row, source_id=source_id)
    record = PublicationRecord(
        family_token=str(raw["family_token"]),
        publication_token=str(raw["publication_token"]),
        publication_ordinal=0,
        title_en=raw["title_en"],
        abstract_en=raw["abstract_en"],
        claims_text=raw["claims_text"],
        claims=(),
    )
    members = (record,)
    tac = _family_text(members, ("title_en", "abstract_en", "claims_text"))
    result: dict[str, tuple[str, ...]] = {
        "P00-TAC-DOC": (tac,),
        "P01-TA-DOC": (_family_text(members, ("title_en", "abstract_en")),),
        "P03-PASSAGE": _passages(tac),
        "P04-SECTION-MULTIVIEW": (
            _family_text(members, ("abstract_en",), labels={"abstract_en": "ABSTRACT"}),
            _family_text(members, ("claims_text",), labels={"claims_text": "CLAIMS"}),
            _family_text(members, ("title_en",), labels={"title_en": "TITLE"}),
        ),
    }
    # The additive successor is exactly the first parsed claims_text segment.
    # It deliberately does not populate or infer the old independence field.
    result["P02-CLAIM1"] = (first_claim_segment(row.get("claims_text")).text,)
    return result


def _template(arm_id: str, *, side: str) -> str:
    if side == "corpus":
        return "encode document for different retrieval: {text}" if arm_id == "ARM-03" else "{text}"
    if side != "rep_dev_queries":
        raise DenseOverflowInventoryError("unsupported input side")
    return {
        "ARM-02": "{text}",
        "ARM-03": "encode query for different document retrieval: {text}",
        "ARM-04": "query: {text}",
        "ARM-05": (
            "Instruct: Retrieve patent families containing technical information relevant "
            "to prior-art search for the query patent family.\nQuery:{text}"
        ),
    }[arm_id]


def _render(template: str, text: str) -> str:
    return template.format(text=text)


def _lengths(tokenizer: Any, rendered: Sequence[str]) -> list[int]:
    try:
        encoded = tokenizer(
            list(rendered),
            add_special_tokens=True,
            truncation=False,
            padding=False,
            return_attention_mask=False,
            return_token_type_ids=False,
            verbose=False,
        )
        values = encoded.get("input_ids")
    except Exception as error:
        raise DenseOverflowInventoryError("frozen tokenizer could not inventory inputs") from error
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise DenseOverflowInventoryError("frozen tokenizer returned no batch token IDs")
    return [len(item) for item in values]


def _model_inputs(root: Path, model_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    contract = _read_json(root / BINDING_CONTRACT_PATH, role="compiled binding contract")
    locks = {item["arm_id"]: item for item in contract.get("model_locks", [])}
    if set(locks) != {"ARM-01", *ARM_IDS}:
        raise DenseOverflowInventoryError("compiled binding arm lock set drifted")
    tokenizers: dict[str, Any] = {}
    bindings: dict[str, Any] = {}
    for arm_id in ARM_IDS:
        lock = locks[arm_id]
        directory = (model_root / arm_id).resolve(strict=True)
        tokenizer_path = directory / "tokenizer.json"
        manifest_path = directory / "runtime-file-manifest.v4.json"
        if (
            directory.is_symlink()
            or not directory.is_dir()
            or not directory.is_relative_to(model_root)
            or tokenizer_path.is_symlink()
            or file_sha256(tokenizer_path) != lock["tokenizer_sha256"]
        ):
            raise DenseOverflowInventoryError(f"{arm_id} frozen tokenizer binding mismatch")
        manifest = _read_json(manifest_path, role=f"{arm_id} runtime manifest")
        if (
            manifest.get("arm_id") != arm_id
            or manifest.get("source_lock_file_sha256") != lock["file_sha256"]
            or not any(
                isinstance(item, Mapping) and item.get("sha256") == lock["tokenizer_sha256"]
                for item in manifest.get("files", [])
            )
        ):
            raise DenseOverflowInventoryError(f"{arm_id} runtime manifest binding mismatch")
        limit = lock.get("effective_input_limit")
        if not isinstance(limit, int) or limit < 1:
            raise DenseOverflowInventoryError(f"{arm_id} effective input limit is invalid")
        tokenizers[arm_id] = _load_dense_tokenizer(directory, arm_id=arm_id)
        templates = {
            side: _template(arm_id, side=side) for side in ("corpus", "rep_dev_queries")
        }
        bindings[arm_id] = {
            "effective_input_limit": limit,
            "model_lock_file_sha256": lock["file_sha256"],
            "adapter_contract_sha256": lock["adapter_contract_sha256"],
            "tokenizer_sha256": lock["tokenizer_sha256"],
            "template_sha256": canonical_sha256(templates),
        }
    return tokenizers, bindings


def _flush(
    buffers: dict[str, list[str]],
    *,
    tokenizers: Mapping[str, Any],
    bindings: Mapping[str, Mapping[str, Any]],
    counts: Mapping[str, Mapping[str, _Counts]],
    executor: Executor,
) -> None:
    for program_id, texts in buffers.items():
        if not texts:
            continue
        futures = {}
        for arm_id in ARM_IDS:
            template = _template(arm_id, side="corpus")
            rendered = [_render(template, text) for text in texts]
            futures[arm_id] = executor.submit(_lengths, tokenizers[arm_id], rendered)
        for arm_id in ARM_IDS:
            counts[arm_id][program_id].update(
                futures[arm_id].result(),
                limit=int(bindings[arm_id]["effective_input_limit"]),
            )
        texts.clear()


def _corpus_inventory(
    rows: Iterable[Mapping[str, Any]],
    *,
    tokenizers: Mapping[str, Any],
    bindings: Mapping[str, Mapping[str, Any]],
    batch_size: int,
) -> tuple[dict[str, dict[str, _Counts]], int]:
    counts = {arm: {program: _Counts() for program in PROGRAM_IDS} for arm in ARM_IDS}
    buffers = {program: [] for program in PROGRAM_IDS}
    seen: set[str] = set()
    thresholds = {
        "P00-TAC-DOC": batch_size,
        "P01-TA-DOC": batch_size * 2,
        "P02-CLAIM1": batch_size * 2,
        "P03-PASSAGE": batch_size * 8,
        "P04-SECTION-MULTIVIEW": batch_size * 2,
    }
    with ThreadPoolExecutor(max_workers=len(ARM_IDS), thread_name_prefix="dense-inventory") as executor:
        for row in rows:
            source_id = row.get("relevant_id")
            if not isinstance(source_id, str) or not source_id or source_id in seen:
                raise DenseOverflowInventoryError("corpus family identity is missing or duplicated")
            seen.add(source_id)
            for program_id, units in _logical_units(row, source_id=source_id).items():
                buffers[program_id].extend(units)
                if len(buffers[program_id]) >= thresholds[program_id]:
                    _flush(
                        {key: value if key == program_id else [] for key, value in buffers.items()},
                        tokenizers=tokenizers,
                        bindings=bindings,
                        counts=counts,
                        executor=executor,
                    )
            if len(seen) % 5_000 == 0:
                print(
                    json.dumps(
                        {"inventory_progress_corpus_families": len(seen)},
                        ensure_ascii=True,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    flush=True,
                )
        _flush(
            buffers,
            tokenizers=tokenizers,
            bindings=bindings,
            counts=counts,
            executor=executor,
        )
    return counts, len(seen)


def _query_inventory(
    rows: Iterable[Mapping[str, Any]],
    *,
    rep_dev: set[str],
    tokenizers: Mapping[str, Any],
    bindings: Mapping[str, Mapping[str, Any]],
) -> dict[str, _Counts]:
    texts: list[str] = []
    observed: set[str] = set()
    for row in rows:
        source_id = row.get("query_id")
        if not isinstance(source_id, str) or source_id not in rep_dev:
            continue
        if source_id in observed:
            raise DenseOverflowInventoryError("REP-DEV source identity is duplicated")
        observed.add(source_id)
        # v11 transfers one full-TAC query text per opaque work token and reuses
        # it across the five corpus-program cells for a frozen arm.
        texts.append(_logical_units(row, source_id=source_id)["P00-TAC-DOC"][0])
    if observed != rep_dev or len(texts) != 150:
        raise DenseOverflowInventoryError("REP-DEV query coverage is incomplete")
    result: dict[str, _Counts] = {}
    with ThreadPoolExecutor(max_workers=len(ARM_IDS), thread_name_prefix="dense-query-inventory") as executor:
        futures = {
            arm_id: executor.submit(
                _lengths,
                tokenizers[arm_id],
                [_render(_template(arm_id, side="rep_dev_queries"), text) for text in texts],
            )
            for arm_id in ARM_IDS
        }
        for arm_id in ARM_IDS:
            counts = _Counts()
            counts.update(
                futures[arm_id].result(),
                limit=int(bindings[arm_id]["effective_input_limit"]),
            )
            result[arm_id] = counts
    return result


def _cell(corpus: _Counts, rep_dev_queries: _Counts) -> dict[str, Any]:
    corpus_value = corpus.as_dict()
    query_value = rep_dev_queries.as_dict()
    combined = _Counts(
        logical_units=corpus.logical_units + rep_dev_queries.logical_units,
        overflow_units=corpus.overflow_units + rep_dev_queries.overflow_units,
        maximum_rendered_tokens=max(
            corpus.maximum_rendered_tokens, rep_dev_queries.maximum_rendered_tokens
        ),
    ).as_dict()
    return {
        "corpus": corpus_value,
        "rep_dev_queries": query_value,
        "combined": combined,
        "raw_compatibility": (
            "OVERFLOW_REQUIRES_AUTHORIZED_COMPOSITION"
            if combined["overflow_logical_unit_count"]
            else "FITS_FROZEN_EFFECTIVE_LIMIT"
        ),
    }


def audit(
    repository_root: Path,
    *,
    cache_root: Path,
    protected_rep_dev_path: Path,
    model_root: Path,
    batch_size: int = 128,
) -> dict[str, Any]:
    if batch_size < 1 or batch_size > 1024:
        raise DenseOverflowInventoryError("batch size must be between 1 and 1024")
    if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("TRANSFORMERS_OFFLINE") != "1":
        raise DenseOverflowInventoryError("offline tokenizer environment is required")
    root = repository_root.resolve()
    external_models = model_root.resolve(strict=True)
    if external_models.is_symlink() or external_models.is_relative_to(root):
        raise DenseOverflowInventoryError("model root must be a safe external directory")
    layout = resolve_cache(cache_root, root)
    rep_dev = _read_rep_dev(protected_rep_dev_path)
    tokenizers, bindings = _model_inputs(root, external_models)
    corpus_paths = tuple(path for path in layout.files["corpus"] if path.suffix == ".arrow")
    query_paths = tuple(path for path in layout.files["queries"] if path.suffix == ".arrow")
    corpus_counts, corpus_family_count = _corpus_inventory(
        iter_arrow_rows(
            corpus_paths, ("relevant_id", "title_en", "abstract_en", "claims_text")
        ),
        tokenizers=tokenizers,
        bindings=bindings,
        batch_size=batch_size,
    )
    query_counts = _query_inventory(
        iter_arrow_rows(
            query_paths, ("query_id", "title_en", "abstract_en", "claims_text")
        ),
        rep_dev=rep_dev,
        tokenizers=tokenizers,
        bindings=bindings,
    )
    cells = {
        arm_id: {
            program_id: _cell(corpus_counts[arm_id][program_id], query_counts[arm_id])
            for program_id in PROGRAM_IDS
        }
        for arm_id in ARM_IDS
    }
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "inventory_id": "a1.2-dense-overflow-owner-local-inventory-20260808-v1",
        "status": "PASS_RAW_COMPATIBILITY_INVENTORY",
        "evidence_class": "pre_measurement_owner_local_compatibility_inventory",
        "scientific_authority": False,
        "claim_boundary": (
            "Aggregate-only rendered-length inventory before additive overflow composition. "
            "It contains no source text, identifiers, split members, qrels, rankings, retrieval "
            "outcomes, provider values, execution authority, or scientific result."
        ),
        "scope": {
            "arm_count": 5,
            "dense_arm_count": 4,
            "program_count": 5,
            "program_arm_cell_count": 25,
            "dense_program_arm_cell_count": 20,
            "rep_dev_query_count": 150,
            "corpus_family_count": corpus_family_count,
            "bm25_overflow_status": "NOT_APPLICABLE_UNBOUNDED_LEXICAL",
        },
        "bindings": {
            "source_contract_uri": SOURCE_CONTRACT_PATH.as_posix(),
            "source_contract_file_sha256": file_sha256(root / SOURCE_CONTRACT_PATH),
            "dataset_revision": layout.contract["dataset"]["revision"],
            "input_hashes": layout.input_hashes,
            "program_set_uri": PROGRAM_SET_PATH.as_posix(),
            "program_set_file_sha256": file_sha256(root / PROGRAM_SET_PATH),
            "p02_repair_uri": P02_REPAIR_PATH.as_posix(),
            "p02_repair_file_sha256": file_sha256(root / P02_REPAIR_PATH),
            "rep_dev_workload_commitment": file_sha256(protected_rep_dev_path.resolve(strict=True)),
            "dense_arms": bindings,
        },
        "query_semantics": {
            "source": "frozen_dapfam_full_tac_query_view",
            "reuse": "same_150_logical_queries_across_each_program_cell_within_arm",
            "alternate_field_fallback": False,
        },
        "cells": cells,
        "safety": {
            "retrieval_results_inspected": False,
            "retrieval_started": False,
            "provider_contacted": False,
            "paid_api_used": False,
            "selection_accessed": False,
            "final_accessed": False,
            "model_or_weight_changed": False,
            "historical_v11_v12_r3_v13_changed": False,
            "silent_truncation_performed": False,
        },
    }
    assert_aggregate_only(body)
    body["inventory_sha256"] = canonical_sha256(body)
    return body


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    text = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_text(encoding="ascii") != text:
            raise DenseOverflowInventoryError("existing inventory output differs")
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
    parser = argparse.ArgumentParser(prog="myis-a1.2-dense-overflow-inventory-v1")
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
        raise DenseOverflowInventoryError("safe inventory output must remain inside the repository")
    _atomic_json(output, result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "dense_cells": 20,
                "rep_dev_queries": result["scope"]["rep_dev_query_count"],
                "corpus_families": result["scope"]["corpus_family_count"],
                "inventory_sha256": result["inventory_sha256"],
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
