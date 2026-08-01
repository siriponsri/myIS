from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import shutil
from typing import Any, Callable

import pytest

from myis_research.kernel.canonical import canonical_sha256, file_sha256
from myis_research.p2 import (
    Candidate,
    P2ContractError,
    P2RunStateMachine,
    load_profile,
    validate_p2_aggregate_metric,
    validate_p2_artifact,
    validate_p2_package_bundle,
)
from myis_research.p2.contracts import build_request
from myis_research.projections.read_model import _p2_readiness_projection


ROOT = Path(__file__).resolve().parents[1]
DATASET_HASH = "a" * 64
COMPILER_HASH = "c" * 64
CONFIG_HASH = "d" * 64
RETRIEVER_HASH = "e" * 64
EVALUATOR_HASH = "f" * 64
HASH_FIELDS = {
    "ledger": "ledger_sha256",
    "baseline": "receipt_sha256",
    "freeze": "receipt_sha256",
    "selection": "receipt_sha256",
    "manifest": "manifest_sha256",
    "package": "package_sha256",
}
URI_FIELDS = {
    "request": "request_uri",
    "ledger": "candidate_ledger_uri",
    "baseline": "baseline_reproduction_uri",
    "freeze": "shortlist_freeze_uri",
    "selection": "selection_uri",
    "manifest": "manifest_uri",
}


def _metric(candidate_id: str, value: float, *, split: str) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "name": "recall_at_100",
        "value": value,
        "n": 16,
        "scope": "OUT",
        "split": split,
        "direction": "maximize",
        "denominator": "macro_mean_per_query_relevant_families",
        "evidence_role": "primary",
    }


def _self_hash(row: dict[str, Any], field: str) -> dict[str, Any]:
    row.pop(field, None)
    row[field] = canonical_sha256(row)
    return row


def _write(root: Path, uri: str, payload: dict[str, Any]) -> None:
    path = root / uri
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def _prepare_control_root(root: Path) -> None:
    for relative in (
        Path("control/budgets/p2-r1-primary-v1.yaml"),
        Path("control/execution-envelope-p2.yaml"),
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)


def _build_bundle(root: Path) -> dict[str, dict[str, Any]]:
    _prepare_control_root(root)
    profile = load_profile(root)
    request = build_request(
        request_id="p2-semantic-fixture",
        git_commit="1" * 40,
        execution_envelope_sha256=file_sha256(root / "control/execution-envelope-p2.yaml"),
        scope_hashes={
            "compiler": COMPILER_HASH,
            "config": CONFIG_HASH,
            "retriever": RETRIEVER_HASH,
            "evaluator": EVALUATOR_HASH,
        },
        input_hashes={"dataset": DATASET_HASH},
        frozen_controls=[f"control-{index}" for index in range(4)],
        repository_root=root,
    )
    machine = P2RunStateMachine(request_id=request["request_id"], profile=profile)
    for index in range(4):
        machine.register_candidate(Candidate(f"control-{index}", "frozen_control", 0, "1" * 64))
    for index in range(8):
        machine.register_candidate(Candidate(f"patent-{index}", "preregistered_patent", 0, "2" * 64))
    for iteration, best_score in enumerate((0.6, 0.7, 0.7, 0.7), start=1):
        for index in range(4):
            candidate_id = f"adaptive-{iteration}-{index}"
            machine.register_candidate(Candidate(candidate_id, "adaptive_autoindex", iteration, "3" * 64))
            machine.record_train(candidate_id, score=best_score - index * 0.01)
        machine.record_iteration(iteration)
    machine.finish_generation()
    base_scores = [0.95, 0.9, 0.4, 0.3, 0.85, 0.8, 0.75, 0.65, 0.45, 0.35, 0.25, 0.15]
    for score, candidate_id in zip(
        base_scores,
        (candidate_id for candidate_id, row in machine.candidates.items() if row["iteration"] == 0),
        strict=True,
    ):
        machine.record_train(candidate_id, score=score)
    baseline = machine.record_baseline_reproduction(
        baseline_id="control-0",
        expected_metric=_metric("control-0", 0.95, split="train"),
        tolerance=0.001,
        dataset_lineage_sha256=DATASET_HASH,
        config_sha256=CONFIG_HASH,
        retriever_sha256=RETRIEVER_HASH,
        evaluator_sha256=EVALUATOR_HASH,
        result=_metric("control-0", 0.95, split="train"),
    )
    machine.finish_train()
    machine.build_shortlist(incumbent_score=0.5)
    freeze = machine.freeze_shortlist(
        compiler_sha256=COMPILER_HASH,
        config_sha256=CONFIG_HASH,
        retriever_sha256=RETRIEVER_HASH,
        evaluator_sha256=EVALUATOR_HASH,
    )
    machine.open_selection()
    for index, candidate_id in enumerate(machine.shortlist_ids):
        metric = _metric(candidate_id, 0.5 + index * 0.01, split="selection")
        machine.record_selection(candidate_id, metric={key: value for key, value in metric.items() if key != "candidate_id"})
    machine.close()
    selection = machine.build_selection_receipt()
    ledger = machine.build_candidate_ledger()

    manifest = _self_hash({
        "schema_version": "myis.p2-manifest.v1",
        "run_id": "p2-semantic-fixture-run",
        "request_id": request["request_id"],
        "phase_id": "P2_SCOPE_DEVELOPMENT",
        "arm": "R1",
        "campaign_revision": profile.payload["campaign_revision"],
        "budget_profile_id": profile.profile_id,
        "budget_profile_sha256": profile.sha256,
        "status": "valid",
        "evidence_class": "fixture",
        "request_sha256": canonical_sha256(request),
        "candidate_ledger_sha256": ledger["ledger_sha256"],
        "baseline_reproduction_receipt_sha256": baseline["receipt_sha256"],
        "shortlist_freeze_receipt_sha256": freeze["receipt_sha256"],
        "selection_receipt_sha256": selection["receipt_sha256"],
        "candidate_count": ledger["candidate_count"],
        "candidate_ids": selection["candidate_ids"],
        "selection_exposure_count": 1,
        "metrics": selection["metrics"],
    }, "manifest_sha256")

    uris = {
        "request": "campaigns/scope-autoindex-v1/requests/p2-semantic-request.json",
        "ledger": "campaigns/scope-autoindex-v1/evidence/p2-semantic-ledger.json",
        "baseline": "campaigns/scope-autoindex-v1/evidence/p2-semantic-baseline.json",
        "freeze": "campaigns/scope-autoindex-v1/evidence/p2-semantic-freeze.json",
        "selection": "campaigns/scope-autoindex-v1/evidence/p2-semantic-selection.json",
        "manifest": "campaigns/scope-autoindex-v1/manifests/p2-semantic-manifest.json",
    }
    package = _self_hash({
        "schema_version": "myis.p2-package.v1",
        "package_id": "p2-semantic-fixture-package",
        "request_id": request["request_id"],
        "campaign_revision": profile.payload["campaign_revision"],
        "status": "validated_structural",
        "request_uri": uris["request"],
        "request_sha256": canonical_sha256(request),
        "candidate_ledger_uri": uris["ledger"],
        "candidate_ledger_sha256": ledger["ledger_sha256"],
        "baseline_reproduction_uri": uris["baseline"],
        "baseline_reproduction_sha256": baseline["receipt_sha256"],
        "shortlist_freeze_uri": uris["freeze"],
        "shortlist_freeze_sha256": freeze["receipt_sha256"],
        "selection_uri": uris["selection"],
        "selection_sha256": selection["receipt_sha256"],
        "manifest_uri": uris["manifest"],
        "manifest_sha256": manifest["manifest_sha256"],
        "budget_profile_id": profile.profile_id,
        "budget_profile_sha256": profile.sha256,
        "candidate_count": ledger["candidate_count"],
        "selection_exposure_count": 1,
    }, "package_sha256")
    bundle = {
        "request": request,
        "ledger": ledger,
        "baseline": baseline,
        "freeze": freeze,
        "selection": selection,
        "manifest": manifest,
        "package": package,
    }
    for name, uri in uris.items():
        _write(root, uri, bundle[name])
    _write(root, "campaigns/scope-autoindex-v1/packages/p2-semantic-package.json", package)
    return bundle


def _validate(root: Path, bundle: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return validate_p2_package_bundle(
        request=bundle["request"],
        ledger=bundle["ledger"],
        baseline=bundle["baseline"],
        freeze=bundle["freeze"],
        selection=bundle.get("selection"),
        manifest=bundle["manifest"],
        package=bundle["package"],
        repository_root=root,
    )


def _mutate(
    root: Path,
    bundle: dict[str, dict[str, Any]],
    name: str,
    change: Callable[[dict[str, Any]], None],
) -> None:
    row = deepcopy(bundle[name])
    change(row)
    hash_field = HASH_FIELDS.get(name)
    if hash_field:
        _self_hash(row, hash_field)
    bundle[name] = row
    if name in URI_FIELDS:
        _write(root, bundle["package"][URI_FIELDS[name]], row)
    elif name == "package":
        _write(root, "campaigns/scope-autoindex-v1/packages/p2-semantic-package.json", row)


def test_complete_synthetic_package_bundle_is_semantically_valid(tmp_path: Path) -> None:
    bundle = _build_bundle(tmp_path)
    validated = _validate(tmp_path, bundle)
    assert validated["selection"]["candidate_ids"] == validated["freeze"]["candidate_ids"]
    assert validated["ledger"]["candidate_count"] == 28


def test_empty_shortlist_closes_without_selection_exposure(tmp_path: Path) -> None:
    bundle = _build_bundle(tmp_path)

    def clear_ledger_shortlist(row: dict[str, Any]) -> None:
        for candidate in row["candidates"]:
            if candidate.get("status") == "frozen":
                candidate["status"] = "rejected"
            candidate["selection_eligible"] = False

    _mutate(tmp_path, bundle, "ledger", clear_ledger_shortlist)
    def clear_freeze(row: dict[str, Any]) -> None:
        row["candidate_ids"] = []
        row["candidate_spec_hashes"] = {}

    _mutate(tmp_path, bundle, "freeze", clear_freeze)
    bundle.pop("selection")
    (tmp_path / "campaigns/scope-autoindex-v1/evidence/p2-semantic-selection.json").unlink()

    def close_manifest_without_selection(row: dict[str, Any]) -> None:
        row["status"] = "negative_development"
        row["candidate_ledger_sha256"] = bundle["ledger"]["ledger_sha256"]
        row["shortlist_freeze_receipt_sha256"] = bundle["freeze"]["receipt_sha256"]
        row["selection_receipt_sha256"] = None
        row["candidate_ids"] = []
        row["selection_exposure_count"] = 0
        row["metrics"] = []

    _mutate(tmp_path, bundle, "manifest", close_manifest_without_selection)

    def close_package_without_selection(row: dict[str, Any]) -> None:
        row["status"] = "negative_development"
        row["candidate_ledger_sha256"] = bundle["ledger"]["ledger_sha256"]
        row["shortlist_freeze_sha256"] = bundle["freeze"]["receipt_sha256"]
        row["selection_uri"] = None
        row["selection_sha256"] = None
        row["manifest_sha256"] = bundle["manifest"]["manifest_sha256"]
        row["selection_exposure_count"] = 0

    _mutate(tmp_path, bundle, "package", close_package_without_selection)
    validated = _validate(tmp_path, bundle)
    assert "selection" not in validated
    assert validated["package"]["selection_exposure_count"] == 0


@pytest.mark.parametrize(
    ("artifact_name", "protected_key"),
    [
        ("request", "query-ids"),
        ("ledger", "qrels"),
        ("baseline", "membership"),
        ("freeze", "query memberships"),
        ("selection", "per-query-outcomes"),
        ("manifest", "raw_payload"),
        ("package", "raw-provider-payloads"),
    ],
)
def test_recursive_protection_precedes_schema_for_every_p2_artifact(
    tmp_path: Path,
    artifact_name: str,
    protected_key: str,
) -> None:
    row = deepcopy(_build_bundle(tmp_path)[artifact_name])
    row["nested_probe"] = {"deeper": {protected_key: []}}
    with pytest.raises(P2ContractError, match="protected payload key"):
        validate_p2_artifact(row, repository_root=tmp_path)


@pytest.mark.parametrize("artifact_name", ["request", "ledger", "baseline", "freeze", "selection", "manifest", "package"])
def test_every_p2_artifact_rejects_a_stale_canonical_profile_hash(tmp_path: Path, artifact_name: str) -> None:
    row = deepcopy(_build_bundle(tmp_path)[artifact_name])
    row["budget_profile_sha256"] = "0" * 64
    hash_field = HASH_FIELDS.get(artifact_name)
    if hash_field:
        _self_hash(row, hash_field)
    with pytest.raises(P2ContractError, match="canonical profile"):
        validate_p2_artifact(row, repository_root=tmp_path)


def test_aggregate_metric_schema_rejects_unknown_and_protected_fields() -> None:
    metric = _metric("control-0", 0.5, split="selection")
    with pytest.raises(P2ContractError, match="(?i)additional properties"):
        validate_p2_aggregate_metric({**metric, "unexpected": 1}, selection=True)
    with pytest.raises(P2ContractError, match="protected payload key"):
        validate_p2_aggregate_metric({**metric, "nested": {"query_ids": []}}, selection=True)


@pytest.mark.parametrize(
    ("artifact_name", "change", "message"),
    [
        ("ledger", lambda row: row.__setitem__("candidate_count", 27), "candidate_count"),
        ("freeze", lambda row: row["candidate_spec_hashes"].pop(row["candidate_ids"][0]), "spec hashes"),
        ("ledger", lambda row: row["iterations"][0].__setitem__("iteration", 2), "consecutive"),
        ("ledger", lambda row: row["iterations"][0].__setitem__("best_score", 0.01), "derived"),
        ("selection", lambda row: row.__setitem__("request_id", "p2-other-request"), "request_id mismatch"),
        ("manifest", lambda row: row.__setitem__("candidate_count", 29), "candidate count mismatch"),
        ("package", lambda row: row.__setitem__("manifest_sha256", "0" * 64), "manifest_sha256 mismatch"),
        ("package", lambda row: row.__setitem__("selection_exposure_count", 0), "exposure count mismatch"),
        ("package", lambda row: row.__setitem__("status", "negative_development"), "statuses are incoherent"),
    ],
)
def test_package_semantics_reject_cross_artifact_mismatches(
    tmp_path: Path,
    artifact_name: str,
    change: Callable[[dict[str, Any]], None],
    message: str,
) -> None:
    bundle = _build_bundle(tmp_path)
    _mutate(tmp_path, bundle, artifact_name, change)
    with pytest.raises(P2ContractError, match=message):
        _validate(tmp_path, bundle)


def test_package_semantics_resolve_each_declared_uri(tmp_path: Path) -> None:
    bundle = _build_bundle(tmp_path)
    _mutate(
        tmp_path,
        bundle,
        "package",
        lambda row: row.__setitem__("request_uri", row["manifest_uri"]),
    )
    with pytest.raises(P2ContractError, match="request_uri does not resolve"):
        _validate(tmp_path, bundle)


def test_read_model_promotes_only_a_complete_semantic_bundle(tmp_path: Path) -> None:
    bundle = _build_bundle(tmp_path)
    projection = _p2_readiness_projection(tmp_path, {})
    assert projection["status"] == "fixture_only"
    assert projection["candidate_count"] == 28
    assert projection["selection_accesses"] == 1

    _mutate(
        tmp_path,
        bundle,
        "package",
        lambda row: row.__setitem__("manifest_sha256", "0" * 64),
    )
    blocked = _p2_readiness_projection(tmp_path, {})
    assert blocked["status"] == "blocked_invalid_artifact"
    assert blocked["candidate_count"] == 0
    assert blocked["selection_accesses"] == 0
