"""Bounded pre-measurement audit for frozen A1.2 input-limit compatibility."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from ..dapfam_p1 import iter_arrow_rows, resolve_cache
from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a1_2_owner_local_protected_compiler_v12 import (
    _load_dense_tokenizer,
    _render_document,
    _token_count,
)
from .scientific_common_programs_v11 import compile_common_program

PROGRAM_SET_PATH = Path("control/armindex/a1.2/common-program-set.v11.json")
BINDING_CONTRACT_PATH = Path("control/owner-local/a1.2-compiled-program-bindings-contract.v12.json")
SOURCE_CONTRACT_PATH = Path("control/assets/dapfam-p1-source.v1.json")
ARM_ID = "ARM-03"
PROGRAM_ID = "P00-TAC-DOC"


class EffectiveInputLimitAuditError(ValueError):
    """Fail-closed input-limit audit error without protected payloads."""


def _find_first_overlength(
    rows: Iterable[Mapping[str, Any]],
    *,
    tokenizer: Any,
    effective_input_limit: int,
    max_rows: int,
) -> dict[str, int] | None:
    for index, row in enumerate(rows, start=1):
        if index > max_rows:
            break
        record = {
            "family_token": "F-" + "a" * 32,
            "publication_token": "P-" + "b" * 32,
            "publication_ordinal": 1,
            "title_en": row.get("title_en"),
            "abstract_en": row.get("abstract_en"),
            "claims_text": row.get("claims_text"),
            "claims": [],
        }
        compiled = compile_common_program(PROGRAM_ID, [record])
        if len(compiled.units) != 1:
            raise EffectiveInputLimitAuditError("frozen P00 compiler did not emit exactly one unit")
        rendered = _render_document(ARM_ID, compiled.units[0].text)
        observed = _token_count(ARM_ID, tokenizer, rendered)
        if observed > effective_input_limit:
            return {"rows_examined": index, "observed_tokens": observed}
    return None


def _read_json(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EffectiveInputLimitAuditError(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise EffectiveInputLimitAuditError(f"{role} must be an object")
    return value


def _model_binding(root: Path, model_root: Path) -> tuple[Path, dict[str, Any]]:
    contract = _read_json(root / BINDING_CONTRACT_PATH, role="compiled binding contract")
    locks = [item for item in contract.get("model_locks", []) if item.get("arm_id") == ARM_ID]
    if len(locks) != 1:
        raise EffectiveInputLimitAuditError("ARM-03 model lock is not unique")
    lock = locks[0]
    directory = (model_root / ARM_ID).resolve(strict=True)
    if directory.is_symlink() or not directory.is_dir() or not directory.is_relative_to(model_root):
        raise EffectiveInputLimitAuditError("ARM-03 model directory is unsafe")
    tokenizer_path = directory / "tokenizer.json"
    manifest_path = directory / "runtime-file-manifest.v4.json"
    if (
        tokenizer_path.is_symlink()
        or not tokenizer_path.is_file()
        or file_sha256(tokenizer_path) != lock.get("tokenizer_sha256")
    ):
        raise EffectiveInputLimitAuditError("ARM-03 tokenizer hash mismatch")
    manifest = _read_json(manifest_path, role="ARM-03 runtime manifest")
    if (
        manifest.get("arm_id") != ARM_ID
        or manifest.get("source_lock_file_sha256") != lock.get("file_sha256")
        or not any(
            isinstance(item, Mapping) and item.get("sha256") == lock.get("tokenizer_sha256")
            for item in manifest.get("files", [])
        )
    ):
        raise EffectiveInputLimitAuditError("ARM-03 runtime manifest binding mismatch")
    return directory, lock


def audit(
    repository_root: Path,
    *,
    cache_root: Path,
    model_root: Path,
    max_rows: int = 100,
) -> dict[str, Any]:
    if max_rows < 1 or max_rows > 1000:
        raise EffectiveInputLimitAuditError("bounded audit max_rows must be between 1 and 1000")
    root = repository_root.resolve()
    external_models = model_root.resolve(strict=True)
    if external_models.is_symlink() or not external_models.is_dir() or external_models.is_relative_to(root):
        raise EffectiveInputLimitAuditError("model root must be a safe external directory")
    layout = resolve_cache(cache_root, root)
    directory, lock = _model_binding(root, external_models)
    limit = lock.get("effective_input_limit")
    if limit != 512:
        raise EffectiveInputLimitAuditError("frozen ARM-03 effective input limit drifted")
    if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("TRANSFORMERS_OFFLINE") != "1":
        raise EffectiveInputLimitAuditError("offline tokenizer environment is required")
    tokenizer = _load_dense_tokenizer(directory, arm_id=ARM_ID)
    corpus_paths = tuple(path for path in layout.files["corpus"] if path.suffix == ".arrow")

    def find() -> dict[str, int] | None:
        return _find_first_overlength(
            iter_arrow_rows(corpus_paths, ("title_en", "abstract_en", "claims_text")),
            tokenizer=tokenizer,
            effective_input_limit=limit,
            max_rows=max_rows,
        )

    first, replay = find(), find()
    if first != replay:
        raise EffectiveInputLimitAuditError("input-limit witness replay is not deterministic")
    if first is None:
        raise EffectiveInputLimitAuditError("bounded audit did not establish compatibility or a defect")
    program_set = _read_json(root / PROGRAM_SET_PATH, role="v11 common program set")
    program = next(
        (item for item in program_set.get("programs", []) if item.get("program_key") == PROGRAM_ID),
        None,
    )
    if not isinstance(program, Mapping):
        raise EffectiveInputLimitAuditError("v11 P00 program is missing")

    body: dict[str, Any] = {
        "schema_version": "myis.armindex-a1.2-effective-input-limit-audit.v1",
        "audit_id": "a1.2-v11-arm03-p00-effective-input-limit-20260808-v1",
        "status": "BLOCKED_CONTRACT_DEFECT",
        "evidence_class": "pre_measurement_protected_boundary_validation_failure",
        "scientific_authority": False,
        "claim_boundary": "Aggregate-only deterministic input-limit failure evidence. It contains no source text, identifiers, membership, qrels, retrieval outcomes, rankings, provider values, execution authorization, or scientific result.",
        "defect": {
            "arm_id": ARM_ID,
            "program_id": PROGRAM_ID,
            "binding_id": f"{ARM_ID}--{PROGRAM_ID}",
            "effective_input_limit": limit,
            "observed_rendered_input_tokens": first["observed_tokens"],
            "overlength_count_minimum": 1,
            "rows_examined_before_fail_closed": first["rows_examined"],
            "silent_truncation_allowed": False,
            "truncation_performed": False,
            "zero_truncation_admission": "FAIL_OVERLENGTH_INPUT",
        },
        "bindings": {
            "source_contract_uri": SOURCE_CONTRACT_PATH.as_posix(),
            "source_contract_file_sha256": file_sha256(root / SOURCE_CONTRACT_PATH),
            "dataset_revision": layout.contract["dataset"]["revision"],
            "corpus_input_hashes": {
                key: value for key, value in layout.input_hashes.items() if key.startswith("corpus_")
            },
            "program_set_uri": PROGRAM_SET_PATH.as_posix(),
            "program_set_file_sha256": file_sha256(root / PROGRAM_SET_PATH),
            "program_spec_sha256": program["program_spec_sha256"],
            "binding_contract_uri": BINDING_CONTRACT_PATH.as_posix(),
            "binding_contract_file_sha256": file_sha256(root / BINDING_CONTRACT_PATH),
            "model_lock_file_sha256": lock["file_sha256"],
            "adapter_contract_sha256": lock["adapter_contract_sha256"],
            "tokenizer_sha256": lock["tokenizer_sha256"],
        },
        "deterministic_replay": {
            "status": "PASS",
            "exact_witness_match": True,
            "witness_sha256": canonical_sha256(first),
        },
        "impact": {
            "compiled_bindings_25_of_25": "BLOCKED",
            "complete_screen_required": True,
            "partial_20_of_25_allowed": False,
            "protected_compilation_receipt_authorized": False,
            "commit_push_condition_met": False,
        },
        "required_owner_decision": "ADDITIVE_PRE_MEASUREMENT_PROGRAM_LIMIT_COMPATIBILITY_REPAIR_OR_ARM03_DISPOSITION",
        "safety": {
            "retrieval_results_inspected": False,
            "measured_retrieval_started": False,
            "provider_contacted": False,
            "paid_api_used": False,
            "selection_accessed": False,
            "final_accessed": False,
            "model_or_weight_changed": False,
            "v11_v12_r3_v13_modified_by_audit": False,
        },
    }
    assert_aggregate_only(body)
    body["audit_sha256"] = canonical_sha256(body)
    return body


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-effective-input-limit-audit-v1")
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--max-rows", type=int, default=100)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(
        args.repository_root,
        cache_root=args.cache_root,
        model_root=args.model_root,
        max_rows=args.max_rows,
    )
    output = args.output.resolve(strict=False)
    root = args.repository_root.resolve()
    if not output.is_relative_to(root):
        raise EffectiveInputLimitAuditError("safe audit output must remain inside the repository")
    output.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    if output.exists() and output.read_text(encoding="ascii") != text:
        raise EffectiveInputLimitAuditError("existing immutable input-limit audit differs")
    if not output.exists():
        output.write_text(text, encoding="ascii")
    print(
        json.dumps(
            {
                "status": result["status"],
                "binding_id": result["defect"]["binding_id"],
                "effective_input_limit": result["defect"]["effective_input_limit"],
                "observed_rendered_input_tokens": result["defect"]["observed_rendered_input_tokens"],
                "audit_sha256": result["audit_sha256"],
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
