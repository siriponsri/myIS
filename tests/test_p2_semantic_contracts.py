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
    validate_p2_train_metric,
)
from myis_research.p2.contracts import build_request
from myis_research.projections.read_model import _p2_readiness_projection


ROOT = Path(__file__).resolve().parents[1]
PRIOR_URI = "campaigns/scope-autoindex-v1/evidence/dapfam-p1-fulltext-c058a3aa7357c782.receipt.json"
DATASET_HASH = "3dbb55b0d9f98d2e27665ad87fb6711f1e43d9466fcf7a96eea917df753adaf6"
COMPILER_HASH = "c" * 64
CONFIG_HASH = "d" * 64
RETRIEVER_HASH = "e" * 64
EVALUATOR_HASH = "6dd3b1d203304c3e8ef9e1aa049b82ae99ce60c1cd3af78cf99f76874db6346d"
BASELINE_VALUE = 0.085847360337
HASH_FIELDS = {
    "ledger": "ledger_sha256",
    "commitment": "commitment_sha256",
    "baseline": "receipt_sha256",
    "freeze": "receipt_sha256",
    "selection": "receipt_sha256",
    "manifest": "manifest_sha256",
    "package": "package_sha256",
}
URI_FIELDS = {
    "request": "request_uri",
    "ledger": "candidate_ledger_uri",
    "commitment": "baseline_commitment_uri",
    "baseline": "baseline_reproduction_uri",
    "freeze": "shortlist_freeze_uri",
    "selection": "selection_uri",
    "manifest": "manifest_uri",
}


def _train_metric(candidate_id: str, value: float, *, arm: str = "R1") -> dict[str, object]:
    return {
        "schema_version": "myis.p2-train-metric.v1",
        "candidate_id": candidate_id,
        "arm": arm,
        "metric_name": "recall_at_100",
        "data_role": "train",
        "scope": "OUT",
        "evidence_role": "primary",
        "direction": "higher_is_better",
        "value": value,
        "n": 179,
        "denominator": "macro_mean_per_query_relevant_families",
        "dataset_lineage_sha256": DATASET_HASH,
        "config_sha256": CONFIG_HASH,
        "retriever_sha256": RETRIEVER_HASH,
        "evaluator_sha256": EVALUATOR_HASH,
    }


def _selection_metric(candidate_id: str, value: float) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "name": "recall_at_100",
        "value": value,
        "n": 16,
        "scope": "OUT",
        "split": "selection",
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
    prior_target = root / PRIOR_URI
    prior_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / PRIOR_URI, prior_target)


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
    for index, arm in enumerate(("R0-W", "R0", "R1", "R1")):
        machine.register_candidate(Candidate(f"control-{index}", arm, "frozen_control", 0, "1" * 64))
    for index in range(8):
        machine.register_candidate(Candidate(f"patent-{index}", "R1", "preregistered_patent", 0, "2" * 64))
    commitment = machine.commit_baseline_expectation(
        baseline_candidate_id="control-0",
        baseline_arm="R0-W",
        prior_artifact_uri=PRIOR_URI,
        prior_artifact_sha256=file_sha256(root / PRIOR_URI),
        metric_locator={"metrics_index": 8},
        expected_metric=_train_metric("control-0", BASELINE_VALUE, arm="R0-W"),
        tolerance=0.001,
    )
    for iteration, best_value in enumerate((0.6, 0.7, 0.7, 0.7), start=1):
        for index in range(4):
            candidate_id = f"adaptive-{iteration}-{index}"
            machine.register_candidate(Candidate(candidate_id, "R1", "adaptive_autoindex", iteration, "3" * 64))
            machine.record_train(candidate_id, metric=_train_metric(candidate_id, best_value - index * 0.01))
        machine.record_iteration(iteration)
    machine.finish_generation()
    base_values = [BASELINE_VALUE, 0.9, 0.4, 0.3, 0.85, 0.8, 0.75, 0.65, 0.45, 0.35, 0.25, 0.15]
    for value, candidate_id in zip(
        base_values,
        (candidate_id for candidate_id, row in machine.candidates.items() if row["iteration"] == 0),
        strict=True,
    ):
        arm = machine.candidates[candidate_id]["arm"]
        machine.record_train(candidate_id, metric=_train_metric(candidate_id, value, arm=arm))
    baseline = machine.record_baseline_reproduction(
        result=_train_metric("control-0", BASELINE_VALUE, arm="R0-W"),
    )
    machine.finish_train()
    machine.build_shortlist()
    freeze = machine.freeze_shortlist(
        compiler_sha256=COMPILER_HASH,
        config_sha256=CONFIG_HASH,
        retriever_sha256=RETRIEVER_HASH,
        evaluator_sha256=EVALUATOR_HASH,
    )
    machine.open_selection()
    for index, candidate_id in enumerate(machine.shortlist_ids):
        metric = _selection_metric(candidate_id, 0.5 + index * 0.01)
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
        "baseline_commitment_sha256": commitment["commitment_sha256"],
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
        "commitment": "campaigns/scope-autoindex-v1/evidence/p2-semantic-baseline-commitment.json",
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
        "baseline_commitment_uri": uris["commitment"],
        "baseline_commitment_sha256": commitment["commitment_sha256"],
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
        "commitment": commitment,
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
        commitment=bundle["commitment"],
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


def _rebind_commitment(
    root: Path,
    bundle: dict[str, dict[str, Any]],
    change: Callable[[dict[str, Any]], None],
) -> None:
    _mutate(root, bundle, "commitment", change)
    commitment = bundle["commitment"]

    def update_ledger(row: dict[str, Any]) -> None:
        row["baseline_commitment_sha256"] = commitment["commitment_sha256"]

    _mutate(root, bundle, "ledger", update_ledger)

    def update_baseline(row: dict[str, Any]) -> None:
        row["baseline_commitment_sha256"] = commitment["commitment_sha256"]
        row["expected_metric"] = deepcopy(commitment["expected_metric"])
        row["tolerance"] = commitment["tolerance"]
        row["status"] = (
            "passed"
            if abs(float(row["result"]["value"]) - float(row["expected_metric"]["value"])) <= float(row["tolerance"])
            else "failed"
        )

    _mutate(root, bundle, "baseline", update_baseline)

    def update_freeze(row: dict[str, Any]) -> None:
        row["baseline_commitment_sha256"] = commitment["commitment_sha256"]
        row["baseline_reproduction_receipt_sha256"] = bundle["baseline"]["receipt_sha256"]

    _mutate(root, bundle, "freeze", update_freeze)
    if "selection" in bundle:
        _mutate(
            root,
            bundle,
            "selection",
            lambda row: row.__setitem__("shortlist_freeze_receipt_sha256", bundle["freeze"]["receipt_sha256"]),
        )

    def update_manifest(row: dict[str, Any]) -> None:
        row["candidate_ledger_sha256"] = bundle["ledger"]["ledger_sha256"]
        row["baseline_commitment_sha256"] = commitment["commitment_sha256"]
        row["baseline_reproduction_receipt_sha256"] = bundle["baseline"]["receipt_sha256"]
        row["shortlist_freeze_receipt_sha256"] = bundle["freeze"]["receipt_sha256"]
        row["selection_receipt_sha256"] = bundle.get("selection", {}).get("receipt_sha256")

    _mutate(root, bundle, "manifest", update_manifest)

    def update_package(row: dict[str, Any]) -> None:
        row["candidate_ledger_sha256"] = bundle["ledger"]["ledger_sha256"]
        row["baseline_commitment_sha256"] = commitment["commitment_sha256"]
        row["baseline_reproduction_sha256"] = bundle["baseline"]["receipt_sha256"]
        row["shortlist_freeze_sha256"] = bundle["freeze"]["receipt_sha256"]
        row["selection_sha256"] = bundle.get("selection", {}).get("receipt_sha256")
        row["manifest_sha256"] = bundle["manifest"]["manifest_sha256"]

    _mutate(root, bundle, "package", update_package)


def test_complete_synthetic_package_bundle_is_semantically_valid(tmp_path: Path) -> None:
    bundle = _build_bundle(tmp_path)
    validated = _validate(tmp_path, bundle)
    assert validated["selection"]["candidate_ids"] == validated["freeze"]["candidate_ids"]
    assert validated["ledger"]["candidate_count"] == 28


def test_empty_shortlist_closes_without_selection_exposure(tmp_path: Path) -> None:
    bundle = _build_bundle(tmp_path)

    def clear_ledger_shortlist(row: dict[str, Any]) -> None:
        by_id = {candidate["candidate_id"]: candidate for candidate in row["candidates"]}
        for candidate in row["candidates"]:
            candidate["train_metric"]["value"] = BASELINE_VALUE
            if candidate.get("status") == "frozen":
                candidate["status"] = "rejected"
            candidate["selection_eligible"] = False
        for iteration in row["iterations"]:
            first_id = sorted(iteration["candidate_ids"])[0]
            iteration["best_metric"] = deepcopy(by_id[first_id]["train_metric"])

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
        ("commitment", "query_ids"),
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


@pytest.mark.parametrize("artifact_name", ["request", "ledger", "commitment", "baseline", "freeze", "selection", "manifest", "package"])
def test_every_p2_artifact_rejects_a_stale_canonical_profile_hash(tmp_path: Path, artifact_name: str) -> None:
    row = deepcopy(_build_bundle(tmp_path)[artifact_name])
    row["budget_profile_sha256"] = "0" * 64
    hash_field = HASH_FIELDS.get(artifact_name)
    if hash_field:
        _self_hash(row, hash_field)
    with pytest.raises(P2ContractError, match="canonical profile"):
        validate_p2_artifact(row, repository_root=tmp_path)


def test_aggregate_metric_schema_rejects_unknown_and_protected_fields() -> None:
    metric = _selection_metric("control-0", 0.5)
    with pytest.raises(P2ContractError, match="(?i)additional properties"):
        validate_p2_aggregate_metric({**metric, "unexpected": 1}, selection=True)
    with pytest.raises(P2ContractError, match="protected payload key"):
        validate_p2_aggregate_metric({**metric, "nested": {"query_ids": []}}, selection=True)


def test_canonical_train_metric_is_separate_from_selection_metric_schema() -> None:
    metric = _train_metric("control-0", BASELINE_VALUE, arm="R0-W")
    assert validate_p2_train_metric(metric)["data_role"] == "train"
    with pytest.raises(P2ContractError, match="JSON Schema"):
        validate_p2_train_metric({**metric, "direction": "maximize"})


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda row: row.__setitem__("prior_artifact_sha256", "0" * 64), "prior artifact SHA-256 is stale"),
        (lambda row: row.__setitem__("metric_locator", {"metrics_index": 999}), "metric locator is invalid"),
        (
            lambda row: row["expected_metric"].__setitem__("value", BASELINE_VALUE + 0.0005),
            "expected metric differs from prior P1 evidence",
        ),
    ],
)
def test_baseline_commitment_resolves_immutable_prior_p1_evidence(
    tmp_path: Path,
    change: Callable[[dict[str, Any]], None],
    message: str,
) -> None:
    bundle = _build_bundle(tmp_path)
    _rebind_commitment(tmp_path, bundle, change)
    with pytest.raises(P2ContractError, match=message):
        _validate(tmp_path, bundle)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda row: row["expected_metric"].__setitem__("value", BASELINE_VALUE + 0.0005), "expectation differs from commitment"),
        (lambda row: row.__setitem__("tolerance", 0.002), "tolerance differs from commitment"),
    ],
)
def test_baseline_reproduction_cannot_supply_a_new_expectation_or_tolerance(
    tmp_path: Path,
    change: Callable[[dict[str, Any]], None],
    message: str,
) -> None:
    bundle = _build_bundle(tmp_path)
    _mutate(tmp_path, bundle, "baseline", change)
    with pytest.raises(P2ContractError, match=message):
        _validate(tmp_path, bundle)


def test_baseline_receipt_cannot_pass_while_disagreeing_with_the_ledger(tmp_path: Path) -> None:
    bundle = _build_bundle(tmp_path)

    def change(row: dict[str, Any]) -> None:
        row["result"]["value"] = BASELINE_VALUE + 0.0005
        row["status"] = "passed"

    _mutate(tmp_path, bundle, "baseline", change)
    with pytest.raises(P2ContractError, match="differs from the baseline candidate train metric"):
        _validate(tmp_path, bundle)


@pytest.mark.parametrize("mode", ["missing", "duplicate"])
def test_baseline_candidate_must_exist_exactly_once(tmp_path: Path, mode: str) -> None:
    bundle = _build_bundle(tmp_path)

    def change(row: dict[str, Any]) -> None:
        if mode == "missing":
            candidate = next(item for item in row["candidates"] if item["candidate_id"] == "control-0")
            candidate["candidate_id"] = "renamed-control"
            candidate["train_metric"]["candidate_id"] = "renamed-control"
        else:
            candidate = next(item for item in row["candidates"] if item["candidate_id"] == "control-1")
            candidate["candidate_id"] = "control-0"
            candidate["train_metric"]["candidate_id"] = "control-0"

    _mutate(tmp_path, bundle, "ledger", change)
    with pytest.raises(P2ContractError, match="baseline candidate must occur exactly once"):
        _validate(tmp_path, bundle)


def test_package_rejects_inconsistent_train_n_across_candidates(tmp_path: Path) -> None:
    bundle = _build_bundle(tmp_path)

    def change(row: dict[str, Any]) -> None:
        candidate = next(item for item in row["candidates"] if item["candidate_id"] == "patent-7")
        candidate["train_metric"]["n"] = 178

    _mutate(tmp_path, bundle, "ledger", change)
    with pytest.raises(P2ContractError, match="share metric identity, n, denominator, and lineage"):
        _validate(tmp_path, bundle)


@pytest.mark.parametrize(
    ("artifact_name", "change", "message"),
    [
        ("ledger", lambda row: row.__setitem__("candidate_count", 27), "candidate_count"),
        ("freeze", lambda row: row["candidate_spec_hashes"].pop(row["candidate_ids"][0]), "spec hashes"),
        ("ledger", lambda row: row["iterations"][0].__setitem__("iteration", 2), "consecutive"),
        ("ledger", lambda row: row["iterations"][0]["best_metric"].__setitem__("value", 0.01), "derived"),
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
    assert projection["status"] == "ready_planned_not_measured"
    assert projection["candidate_count"] == 0
    assert projection["selection_accesses"] == 0
    assert projection["fixture_pilot"]["status"] == "not_executed"

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
