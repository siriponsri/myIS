from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from myis_research.armindex.a4_a5_handoff import build_a5_pointer_bundle
from myis_research.kernel.canonical import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "close_a5_final_owner_local.py"
SPEC = importlib.util.spec_from_file_location("close_a5_final_owner_local", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=True, sort_keys=True), encoding="ascii")


def _self_hash(value: dict, field: str) -> dict:
    return {**value, field: canonical_sha256(value)}


def test_closeout_is_hash_acyclic_and_binds_the_frozen_winner(tmp_path: Path) -> None:
    program_body = {
        "schema_version": "myis.armindex-representation-program.v1",
        "arm_id": "ARM-03",
        "program_id": "a2-arm-03-matched-b2-orthogonal",
        "duplicate_policy": "content_hash_first",
        "family_aggregation": "maxp",
        "field_labels": {"abstract": "", "claims_text": "", "title": ""},
        "field_order": ["title", "abstract", "claims_text"],
        "normalization": "unicode_nfkc_whitespace",
        "preserve_family_identity": True,
        "source_fields": ["title", "abstract", "claims_text"],
        "unitization": {"kind": "passage", "logical_size": 384, "overlap": 64},
    }
    program = _self_hash(program_body, "program_sha256")
    program_path = tmp_path / "ARM-03.json"
    _write(program_path, program)
    research = {
        "role": "research_champion",
        "system_sha256": "a" * 64,
        "program_sha256": program["program_sha256"],
        "model_sha256": "234ea36a876fe5d5c416c1cbaad6f7221e17861fadd6481f0b96588fdc1ca482",
        "prompt_sha256": "c" * 64,
        "representation_sha256": "1" * 64,
        "license_sha256": "2" * 64,
        "license_scope": "research_only",
        "runtime_sha256": "d" * 64,
    }
    baseline = {
        "role": "static_common_baseline",
        "system_sha256": "e" * 64,
        "program_sha256": "e" * 64,
        "model_sha256": "f" * 64,
        "prompt_sha256": "0" * 64,
        "representation_sha256": "1" * 64,
        "license_sha256": "2" * 64,
        "license_scope": "commercial_capable",
        "runtime_sha256": "d" * 64,
    }
    request_body = {
        "schema_version": "myis.armindex-a5-final-request.v1",
        "attempt_id": "a5-final-test",
        "scope": "Final-872",
        "query_count": 872,
        "selection_accesses": 1,
        "final_accesses": 1,
        "protected_payload_included": False,
        "top_k": 100,
        "finalist_bindings": [
            {"system": "research_champion", "program_sha256": research["program_sha256"], "model_sha256": research["model_sha256"], "prompt_sha256": research["prompt_sha256"]},
            {"system": "static_common_baseline", "program_sha256": baseline["program_sha256"], "model_sha256": baseline["model_sha256"], "prompt_sha256": baseline["prompt_sha256"]},
        ],
    }
    request = _self_hash(request_body, "request_sha256")
    request_path = tmp_path / "request.json"
    _write(request_path, request)

    rankings = {"research_champion": {"opaque": []}, "static_common_baseline": {"opaque": []}}
    package = {
        "schema_version": "myis.armindex-a5-final-ranking-package.v1",
        "status": "PASS_A5_REMOTE_OPAQUE_RANKINGS",
        "attempt_id": request["attempt_id"],
        "request_sha256": request["request_sha256"],
        "scope": "Final-872",
        "query_count": 872,
        "coverage": {"research_champion": 872, "static_common_baseline": 872},
        "failures": 0,
        "determinism": True,
        "protected_payload_included": False,
        "rankings_returned_to": "owner_local_evaluator_only",
        "rankings": rankings,
        "ranking_sha256": canonical_sha256(rankings),
    }
    package_path = tmp_path / "package.json"
    _write(package_path, package)

    evaluation_body = {
        "schema_version": "myis.armindex-a5-final-owner-evaluation.v1",
        "status": "PASS_A5_FINAL_CONFIRMATION",
        "scope": "Final-872",
        "request_sha256": request["request_sha256"],
        "ranking_package_sha256": MODULE.file_sha256(package_path),
        "query_count": 872,
        "judged_query_count": 872,
        "systems": {
            name: {"coverage": 872, "failures": 0, "determinism": True}
            for name in ("research_champion", "static_common_baseline")
        },
        "paired_effects": {"bootstrap_resamples": 10_000},
        "winner": "research_champion",
        "selection_accesses": 1,
        "final_accesses": 1,
        "protected_payload_included": False,
    }
    evaluation_path = tmp_path / "evaluation.json"
    _write(evaluation_path, _self_hash(evaluation_body, "result_sha256"))

    registry_path = tmp_path / "registry.json"
    _write(registry_path, build_a5_pointer_bundle(
        attempt_id="a4-goal001-test",
        a4_coverage_sha256="3" * 64,
        selection_receipt_sha256="4" * 64,
        result_audit_sha256="5" * 64,
        safe_return_sha256="6" * 64,
        final_split_commitment_sha256="7" * 64,
        final_input_pointer="a5/final-872-input",
        evaluator_handoff_sha256="8" * 64,
        evaluator_handoff_pointer="a4/selection-evaluator-handoff-v2",
        safe_export_manifest_sha256="9" * 64,
        git_commit="a" * 40,
        git_tree="b" * 40,
        git_ref="origin/main",
        clean_worktree=True,
        pushed_to_origin=True,
        a5_reserved_usd="1.0",
        finalists=[research, baseline],
    ))
    output_dir = tmp_path / "closeout"

    MODULE.build(
        request_path=request_path,
        package_path=package_path,
        evaluation_path=evaluation_path,
        registry_path=registry_path,
        winner_program_path=program_path,
        output_dir=output_dir,
    )

    closeout = json.loads((output_dir / "A5_FINAL_CLOSEOUT.json").read_text(encoding="ascii"))
    winner = json.loads((output_dir / "A5_FROZEN_WINNER_BINDING.json").read_text(encoding="ascii"))
    assert closeout["frozen_winner_configuration_sha256"] == winner["a5_frozen_winner_configuration_sha256"]
    assert "frozen_winner_binding_sha256" not in closeout
    assert winner["a5_closeout_receipt_sha256"] == closeout["receipt_sha256"]
    assert closeout["receipt_sha256"] == canonical_sha256({key: value for key, value in closeout.items() if key != "receipt_sha256"})
    assert winner["binding_sha256"] == canonical_sha256({key: value for key, value in winner.items() if key != "binding_sha256"})
