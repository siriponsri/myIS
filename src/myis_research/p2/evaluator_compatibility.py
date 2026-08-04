"""Hash-bound proof for scientifically compatible P1 evaluator instrumentation."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import types
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from ..kernel.canonical import canonical_sha256, file_sha256
from ..owner_local import OwnerLocalContractError, validate_receipt
from ..protection import assert_aggregate_only
from .active_binding import active_p2_source_uris
from .contracts import P2ContractError


COMPATIBILITY_SCHEMA_VERSION = "myis.p2-evaluator-compatibility.v1"
COMPATIBILITY_CLASSIFICATION = "A_byte_hash_drift_scientifically_identical_semantics"
EVALUATOR_URI = "src/myis_research/kernel/p1.py"
ACCEPTED_P1_RECEIPT_URI = (
    "campaigns/scope-autoindex-v1/evidence/"
    "dapfam-p1-fulltext-c058a3aa7357c782.receipt.json"
)


class _ProgressInstrumentationNormalizer(ast.NodeTransformer):
    """Remove only the reviewed optional progress observer from evaluate_baseline."""

    def __init__(self) -> None:
        self._inside_evaluator = False
        self.removed_parameter = 0
        self.removed_callbacks = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        if node.name != "evaluate_baseline":
            return self.generic_visit(node)
        previous = self._inside_evaluator
        self._inside_evaluator = True
        pairs = list(zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True))
        node.args.kwonlyargs = [argument for argument, _ in pairs if argument.arg != "progress_sink"]
        node.args.kw_defaults = [default for argument, default in pairs if argument.arg != "progress_sink"]
        self.removed_parameter += sum(argument.arg == "progress_sink" for argument, _ in pairs)
        node = self.generic_visit(node)
        self._inside_evaluator = previous
        return node

    def visit_If(self, node: ast.If) -> ast.AST | None:
        if self._inside_evaluator and _is_progress_callback(node):
            self.removed_callbacks += 1
            return None
        return self.generic_visit(node)


def load_evaluator_compatibility(
    repository_root: Path,
    *,
    execution_revision: str = "HEAD",
    expected_sha256: str | None = None,
) -> dict[str, Any]:
    """Load and independently validate the active evaluator compatibility proof."""

    root = Path(repository_root).resolve()
    uri = active_p2_source_uris(root)["evaluator_compatibility"]
    path = root / uri
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        schema = json.loads(
            (root / "schemas/p2-evaluator-compatibility.v1.json").read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise P2ContractError("cannot load P2 evaluator compatibility contract") from error
    if not isinstance(payload, dict):
        raise P2ContractError("P2 evaluator compatibility contract must be an object")
    try:
        assert_aggregate_only(payload)
        Draft202012Validator(schema).validate(payload)
    except (ValueError, ValidationError) as error:
        raise P2ContractError(f"P2 evaluator compatibility schema is invalid: {error}") from error
    recorded = str(payload["compatibility_sha256"])
    unsigned = {key: value for key, value in payload.items() if key != "compatibility_sha256"}
    if recorded != canonical_sha256(unsigned):
        raise P2ContractError("P2 evaluator compatibility self-hash is invalid")
    if expected_sha256 is not None and recorded != expected_sha256:
        raise P2ContractError("measured request evaluator compatibility hash is stale")
    if payload["classification"] != COMPATIBILITY_CLASSIFICATION:
        raise P2ContractError("P2 evaluator compatibility classification is not permitted")
    receipt_path = root / str(payload["baseline"]["accepted_receipt_uri"])
    try:
        receipt = validate_receipt(json.loads(receipt_path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError, OwnerLocalContractError) as error:
        raise P2ContractError("accepted P1 receipt in evaluator compatibility proof is invalid") from error
    if (
        payload["baseline"]["accepted_receipt_uri"] != ACCEPTED_P1_RECEIPT_URI
        or receipt_path.is_symlink()
        or not receipt_path.is_file()
        or file_sha256(receipt_path) != payload["baseline"]["accepted_receipt_sha256"]
        or receipt.get("status") != "accepted"
        or receipt.get("lineage_hashes", {}).get("evaluator_sha256")
        != payload["baseline"]["evaluator_sha256"]
    ):
        raise P2ContractError("evaluator compatibility proof does not bind the accepted P1 receipt")

    evidence = build_evaluator_compatibility_evidence(
        root,
        baseline_revision=str(payload["baseline"]["source_commit"]),
        current_revision=execution_revision,
        evaluator_uri=str(payload["current"]["uri"]),
    )
    expected = {
        "baseline_evaluator_sha256": payload["baseline"]["evaluator_sha256"],
        "current_evaluator_sha256": payload["current"]["evaluator_sha256"],
        "source_diff_sha256": payload["proof"]["source_diff_sha256"],
        "normalized_ast_sha256": payload["proof"]["normalized_ast_sha256"],
        "differential_case_count": payload["proof"]["differential_case_count"],
        "differential_proof_sha256": payload["proof"]["differential_proof_sha256"],
    }
    if evidence != expected:
        raise P2ContractError("P2 evaluator compatibility proof does not reproduce")
    if payload["proof"]["independent_verification"] != "runtime_reproduction_required":
        raise P2ContractError("P2 evaluator compatibility independent verification is missing")
    verification_path = root / str(payload["proof"]["verification_test_uri"])
    if verification_path.is_symlink() or not verification_path.is_file():
        raise P2ContractError("P2 evaluator compatibility verification test is missing")
    return {**payload, "_uri": uri}


def build_evaluator_compatibility_evidence(
    repository_root: Path,
    *,
    baseline_revision: str,
    current_revision: str,
    evaluator_uri: str = EVALUATOR_URI,
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    old_bytes = _committed_bytes(root, baseline_revision, evaluator_uri)
    new_bytes = _committed_bytes(root, current_revision, evaluator_uri)
    old_ast, old_removed = _normalized_ast_sha256(old_bytes)
    new_ast, new_removed = _normalized_ast_sha256(new_bytes)
    if old_ast != new_ast:
        raise P2ContractError("P2 evaluator normalized scientific AST differs from P1")
    if old_removed != (0, 0) or new_removed != (1, 2):
        raise P2ContractError("P2 evaluator drift exceeds the reviewed progress instrumentation")
    proof = _differential_proof(old_bytes, new_bytes)
    return {
        "baseline_evaluator_sha256": hashlib.sha256(old_bytes).hexdigest(),
        "current_evaluator_sha256": hashlib.sha256(new_bytes).hexdigest(),
        "source_diff_sha256": _diff_sha256(root, baseline_revision, current_revision, evaluator_uri),
        "normalized_ast_sha256": old_ast,
        "differential_case_count": len(proof["cases"]),
        "differential_proof_sha256": canonical_sha256(proof),
    }


def _normalized_ast_sha256(source: bytes) -> tuple[str, tuple[int, int]]:
    try:
        tree = ast.parse(source.decode("utf-8"))
    except (UnicodeError, SyntaxError) as error:
        raise P2ContractError("cannot parse committed evaluator source") from error
    normalizer = _ProgressInstrumentationNormalizer()
    normalized = ast.fix_missing_locations(normalizer.visit(tree))
    encoded = ast.dump(normalized, annotate_fields=True, include_attributes=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest(), (
        normalizer.removed_parameter,
        normalizer.removed_callbacks,
    )


def _is_progress_callback(node: ast.If) -> bool:
    if node.orelse or len(node.body) != 1:
        return False
    test = node.test
    statement = node.body[0]
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "progress_sink"
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.IsNot)
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value is None
        and isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Name)
        and statement.value.func.id == "progress_sink"
        and not statement.value.args
        and not statement.value.keywords
    )


def _differential_proof(old_bytes: bytes, new_bytes: bytes) -> dict[str, Any]:
    old = _module_from_source("myis_research.kernel._p2_compat_old", old_bytes)
    new = _module_from_source("myis_research.kernel._p2_compat_new", new_bytes)
    cases = _differential_cases()
    results: list[dict[str, Any]] = []
    for case in cases:
        old_rows: list[dict[str, Any]] = []
        new_rows: list[dict[str, Any]] = []
        progress_events: list[None] = []
        old_result = old.evaluate_baseline(
            **deepcopy(case["arguments"]),
            protected_sink=lambda row: old_rows.append(deepcopy(row)),
        )
        new_result = new.evaluate_baseline(
            **deepcopy(case["arguments"]),
            protected_sink=lambda row: new_rows.append(deepcopy(row)),
            progress_sink=lambda: progress_events.append(None),
        )
        old_result.pop("latency_seconds", None)
        new_result.pop("latency_seconds", None)
        if old_result != new_result or old_rows != new_rows:
            raise P2ContractError(
                f"P2 evaluator differential proof failed: {case['case_id']}"
            )
        expected_events = len(case["arguments"]["queries"])
        if len(progress_events) != expected_events:
            raise P2ContractError(
                f"P2 evaluator progress instrumentation count differs: {case['case_id']}"
            )
        results.append({
            "case_id": case["case_id"],
            "scientific_result_sha256": canonical_sha256(old_result),
            "protected_rows_sha256": canonical_sha256(old_rows),
            "progress_event_count": len(progress_events),
        })
    return {
        "schema_version": "myis.p2-evaluator-differential-proof.v1",
        "cases": results,
    }


def _differential_cases() -> list[dict[str, Any]]:
    documents = [
        {"doc_id": "d-a", "family_id": "f-a", "text": "alpha beta"},
        {"doc_id": "d-b", "family_id": "f-b", "text": "beta gamma"},
        {"doc_id": "d-c", "family_id": "f-c", "text": "delta alpha"},
    ]
    positive_queries = [
        {"query_id": "q-a", "text": "alpha", "split": "train"},
        {"query_id": "q-b", "text": "gamma", "split": "train"},
    ]
    qrels = {"q-a": ["f-a", "f-c"], "q-b": ["f-b"]}
    return [
        {
            "case_id": "r0_positive",
            "arguments": {"documents": documents, "queries": positive_queries, "qrels": qrels, "arm_id": "R0", "split_name": "fixture"},
        },
        {
            "case_id": "r0_missing_positive",
            "arguments": {"documents": documents, "queries": [*positive_queries, {"query_id": "q-none", "text": "none", "split": "train"}], "qrels": qrels, "arm_id": "R0", "split_name": "fixture"},
        },
        {
            "case_id": "r0w_windowed",
            "arguments": {"documents": documents, "queries": positive_queries, "qrels": qrels, "arm_id": "R0-W", "window_size": 1, "split_name": "fixture"},
        },
        {
            "case_id": "r0_domain_scopes",
            "arguments": {"documents": documents, "queries": positive_queries, "qrels": qrels, "qrel_domains": {"q-a": {"f-a": "IN", "f-c": "OUT"}, "q-b": {"f-b": "OUT"}}, "arm_id": "R0", "split_name": "fixture"},
        },
    ]


def _module_from_source(name: str, source: bytes) -> types.ModuleType:
    module = types.ModuleType(name)
    module.__file__ = f"<{name}>"
    module.__package__ = "myis_research.kernel"
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module


def _committed_bytes(root: Path, revision: str, uri: str) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "show", f"{revision}:{uri}"],
            cwd=root,
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise P2ContractError(f"cannot read committed evaluator bytes: {revision}:{uri}") from error
    return completed.stdout


def _diff_sha256(root: Path, baseline_revision: str, current_revision: str, uri: str) -> str:
    try:
        completed = subprocess.run(
            [
                "git", "diff", "--no-color", "--no-ext-diff", "--no-textconv",
                "--no-renames", "--diff-algorithm=myers", "--src-prefix=a/",
                "--dst-prefix=b/", "--unified=20", baseline_revision,
                current_revision, "--", uri,
            ],
            cwd=root,
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise P2ContractError("cannot reproduce evaluator source diff") from error
    return hashlib.sha256(completed.stdout).hexdigest()
