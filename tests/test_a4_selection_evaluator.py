from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex.a4_selection_evaluator import (
    A4SelectionEvaluatorError,
    build_selection_handoff,
)
from myis_research.kernel.canonical import canonical_sha256


H = "a" * 64


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _package(tokens: list[str], *, attempt_id: str, scope_hash: str) -> dict:
    rankings = {
        token: [
            {"family_token": f"F-{index:032x}", "rank": index, "score": float(101 - index)}
            for index in range(1, 101)
        ]
        for token in tokens
    }
    return {
        "schema_version": "myis.armindex-a4-remote-ranking-package.v1",
        "status": "PASS_A4_REMOTE_RANKING_PACKAGE",
        "attempt_id": attempt_id,
        "request_sha256": H,
        "ranking_sha256": canonical_sha256(rankings),
        "profile_id": "FAST",
        "selection_scope_sha256": scope_hash,
        "selection_query_count": 125,
        "rankings": rankings,
        "latency": {"p50_ms": 1, "p95_ms": 2, "p99_ms": 3, "throughput_qps": 4},
        "resource": {"cost_usd": 1, "ram_gib": 2, "vram_gib": 3, "index_size_bytes": 4},
    }


def _roots(tmp_path: Path, tokens: list[str]) -> tuple[Path, Path, str]:
    selection = tmp_path / "selection"
    evaluator = tmp_path / "evaluator"
    scope_body = {"scope": "Selection-125", "query_count": 125}
    scope = {**scope_body, "scope_sha256": canonical_sha256(scope_body)}
    _write_json(selection / "A4_SELECTION_INPUT_MATERIALIZATION_RECEIPT.json", {"scope": "Selection-125", "selection_query_count": 125})
    _write_json(selection / "A4_SELECTION_SCOPE.json", scope)
    qrels = [{"work_token": token, "relevance": {"F-00000000000000000000000000000001": 1}} for token in tokens]
    membership = [{"work_token": token, "eligible_out": index >= 35} for index, token in enumerate(tokens)]
    _write_json(evaluator / "A4_SELECTION_EVALUATOR_INPUTS_RECEIPT.json", {"scope": "Selection-125", "judged_query_count": 125, "out_query_count": 90})
    evaluator.joinpath("protected").mkdir(parents=True)
    evaluator.joinpath("protected/selection-125-qrels.jsonl").write_text("".join(json.dumps(row) + "\n" for row in qrels), encoding="utf-8")
    evaluator.joinpath("protected/selection-125-membership.jsonl").write_text("".join(json.dumps(row) + "\n" for row in membership), encoding="utf-8")
    return selection, evaluator, scope["scope_sha256"]


def test_selection_handoff_uses_out_denominator_and_hashes_vectors(tmp_path: Path) -> None:
    tokens = [f"Q-{index:032x}" for index in range(125)]
    selection, evaluator, scope_hash = _roots(tmp_path, tokens)
    receipt = build_selection_handoff(
        selection_input_root=selection,
        evaluator_input_root=evaluator,
        packages={"left": _package(tokens, attempt_id="a4-goal001-test", scope_hash=scope_hash), "right": _package(tokens, attempt_id="a4-goal001-test", scope_hash=scope_hash)},
        systems={"left": H, "right": "b" * 64},
        output_root=tmp_path / "handoff",
        attempt_id="a4-goal001-test",
        evaluator_handoff_sha256="c" * 64,
    )
    assert receipt["selection_query_count"] == 125
    assert receipt["out_query_count"] == 90
    source = json.loads((tmp_path / "handoff/protected/selection-125-paired-out-vectors.json").read_text())
    assert source["selection_evaluated_query_count"] == 90
    assert len(source["comparisons"][0]["metrics"]["recall_at_100"]["left"]) == 90


def test_selection_handoff_rejects_token_coverage_drift(tmp_path: Path) -> None:
    tokens = [f"Q-{index:032x}" for index in range(125)]
    selection, evaluator, scope_hash = _roots(tmp_path, tokens)
    wrong_tokens = tokens[:-1] + ["Q-ffffffffffffffffffffffffffffffff"]
    with pytest.raises(A4SelectionEvaluatorError, match="tokens do not match"):
        build_selection_handoff(
            selection_input_root=selection,
            evaluator_input_root=evaluator,
            packages={"left": _package(wrong_tokens, attempt_id="a4-goal001-test", scope_hash=scope_hash), "right": _package(wrong_tokens, attempt_id="a4-goal001-test", scope_hash=scope_hash)},
            systems={"left": H, "right": "b" * 64},
            output_root=tmp_path / "handoff",
            attempt_id="a4-goal001-test",
            evaluator_handoff_sha256="c" * 64,
        )
