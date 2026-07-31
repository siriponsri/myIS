from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path

import pytest

from myis_research.kernel.manifest import build_manifest
from myis_research.kernel.manifest_validation import build_validation_report, capture_git_state
from myis_research.kernel.canonical import canonical_sha256
from myis_research.owner_local import build_receipt
from myis_research.projections.read_model import (
    _legacy_file_commitment_matches,
    build_read_model,
    write_read_model,
)
from myis_research.report_cli import validate_read_model


def test_empty_campaign_read_model_is_safe(tmp_path: Path) -> None:
    (tmp_path / "control" / "campaigns").mkdir(parents=True)
    (tmp_path / "control" / "decisions").mkdir(parents=True)
    (tmp_path / "control" / "campaigns" / "scope-autoindex-v1.yaml").write_text("campaign:\n  status: preparation\n", encoding="utf-8")
    (tmp_path / "control" / "decisions" / "ledger.jsonl").write_text("", encoding="utf-8")
    model = build_read_model(tmp_path)
    assert model["schema_version"] == "myis.read-model.v2"
    assert model["publication_readiness"]["status"] == "blocked"
    output = write_read_model(tmp_path)
    assert json.loads(output.read_text(encoding="utf-8"))["projection_revision"] == model["projection_revision"]


def test_read_model_validation_rejects_unknown_field_and_non_object(tmp_path: Path) -> None:
    (tmp_path / "control" / "campaigns").mkdir(parents=True)
    (tmp_path / "control" / "decisions").mkdir(parents=True)
    (tmp_path / "control" / "campaigns" / "scope-autoindex-v1.yaml").write_text("campaign: {}\n", encoding="utf-8")
    (tmp_path / "control" / "decisions" / "ledger.jsonl").write_text("", encoding="utf-8")
    model = build_read_model(tmp_path)
    with pytest.raises(ValueError, match="schema validation failed"):
        validate_read_model({**model, "source_path": "protected"})
    with pytest.raises(ValueError, match="JSON object"):
        validate_read_model([])  # type: ignore[arg-type]


def _p1_request(repository_root: Path, request_id: str = "p1-projection-test") -> dict[str, object]:
    return {
        "schema_version": "myis.owner-local-request.v2",
        "request_id": request_id,
        "decision_id": "P1_CPU_EXECUTION_ENVELOPE",
        "phase_id": "P1_CPU_BASELINE",
        "stage": "train_selection",
        "scope": {"campaign": "a" * 64, "source_contract_sha256": "b" * 64},
        "git_commit": capture_git_state(repository_root)["commit"],
        "input_hashes": {"dataset": "c" * 64},
    }


def _p1_receipt(
    repository_root: Path,
    *,
    request_id: str = "p1-projection-test",
    value: float = 0.5,
) -> tuple[dict[str, object], dict[str, object]]:
    request = _p1_request(repository_root, request_id)
    metrics = [
        {
            "arm": arm,
            "name": "recall_at_100",
            "value": value,
            "n": 2,
            "retrieved_relevant": 1,
            "relevant_total": 2,
            "scope": scope,
            "split": split,
            "direction": "maximize",
            "denominator": "macro_mean_per_query_relevant_families",
            "evidence_role": "primary" if scope == "OUT" else "secondary",
        }
        for arm in ("R0", "R0-W")
        for split in ("train", "selection")
        for scope in ("ALL", "IN", "OUT")
    ]
    return request, build_receipt(
        request,
        aggregate_counts={"documents": 2, "train_queries": 2, "selection_queries": 2},
        aggregate_hashes={f"{arm.lower()}_{split}_metrics": "d" * 64 for arm in ("R0", "R0-W") for split in ("train", "selection")},
        metrics=metrics,
        cost_usd=0.0,
        latency_seconds=0.1,
        lineage_hashes={key: "e" * 64 for key in ("dataset_sha256", "corpus_sha256", "query_sha256", "qrels_sha256", "split_sha256", "index_sha256", "evaluator_sha256")},
    )


def _write_p1_campaign(tmp_path: Path, receipt: dict[str, object]) -> Path:
    evidence_dir = tmp_path / "campaigns" / "scope-autoindex-v1" / "evidence"
    evidence_dir.mkdir(parents=True)
    receipt_path = evidence_dir / "p1-receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    (tmp_path / "control" / "campaigns").mkdir(parents=True)
    (tmp_path / "control" / "decisions").mkdir(parents=True)
    (tmp_path / "control" / "campaigns" / "scope-autoindex-v1.yaml").write_text(
        "phases:\n  - id: P1_CPU_BASELINE\n    status: measured\n    tasks:\n      - id: P1.1\n        title: fixture\n        status: measured\n",
        encoding="utf-8",
    )
    (tmp_path / "control" / "decisions" / "ledger.jsonl").write_text("", encoding="utf-8")
    return receipt_path


def _write_p1_manifest(
    tmp_path: Path,
    repository_root: Path,
    request: dict[str, object],
    receipt: dict[str, object],
    *,
    arm: str,
    split: str,
    status: str = "valid",
    metrics: list[dict[str, object]] | None = None,
    run_suffix: str = "",
    write_validation: bool = True,
) -> Path:
    manifest_dir = tmp_path / "campaigns" / "scope-autoindex-v1" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(
        run_id=f"p1-{arm.lower()}-{split}-{status}{run_suffix}",
        parent_run_id="p1-projection-parent",
        experiment_id="myis-research-track-c",
        campaign_id="scope-autoindex-v1",
        stage=split,
        status=status,
        source={"dataset": "dapfam"},
        data={"split": split},
        method={"arm_id": arm, "top_k": 100},
        resources={"cost_usd": 0.0},
        metrics=metrics or [row for row in receipt["metrics"] if row["arm"] == arm and row["split"] == split],
        artifacts=[],
        evidence_class="train_selection_measured",
        repository_root=repository_root,
        owner_local_request=request,
        owner_local_receipt=receipt,
    )
    path = manifest_dir / f"{arm.lower()}-{split}-{status}{run_suffix}.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    if write_validation:
        _write_validation_report(tmp_path, path, request, receipt)
    return path


def _write_validation_report(
    tmp_path: Path,
    manifest_path: Path,
    request: dict[str, object],
    receipt: dict[str, object],
) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = build_validation_report(
        manifest,
        owner_local_request=request,
        owner_local_receipt=receipt,
    )
    report_dir = tmp_path / "campaigns" / "scope-autoindex-v1" / "validation-reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / manifest_path.name).write_text(json.dumps(report), encoding="utf-8")


def _write_p1_matrix(tmp_path: Path, repository_root: Path, request: dict[str, object], receipt: dict[str, object]) -> None:
    for arm in ("R0", "R0-W"):
        for split in ("train", "selection"):
            _write_p1_manifest(tmp_path, repository_root, request, receipt, arm=arm, split=split)


def _write_p1_package(
    tmp_path: Path,
    request: dict[str, object],
    receipt: dict[str, object],
) -> Path:
    request_dir = tmp_path / "campaigns/scope-autoindex-v1/requests"
    package_dir = tmp_path / "campaigns/scope-autoindex-v1/packages"
    request_dir.mkdir(parents=True, exist_ok=True)
    package_dir.mkdir(parents=True, exist_ok=True)
    request_path = request_dir / "p1-request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    receipt_path = tmp_path / "campaigns/scope-autoindex-v1/evidence/p1-receipt.json"
    slots = []
    for arm in ("R0", "R0-W"):
        for split in ("train", "selection"):
            stem = f"{arm.lower()}-{split}-valid"
            manifest_path = tmp_path / f"campaigns/scope-autoindex-v1/manifests/{stem}.json"
            report_path = tmp_path / f"campaigns/scope-autoindex-v1/validation-reports/{stem}.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            report = json.loads(report_path.read_text(encoding="utf-8"))
            slots.append({
                "arm": arm,
                "split": split,
                "run_id": manifest["run_id"],
                "manifest_uri": manifest_path.relative_to(tmp_path).as_posix(),
                "manifest_sha256": manifest["manifest_sha256"],
                "validation_report_uri": report_path.relative_to(tmp_path).as_posix(),
                "validation_report_sha256": report["validation_report_sha256"],
            })
    package = {
        "schema_version": "myis.p1-package.v1",
        "package_id": request["request_id"],
        "status": "validated_structural",
        "source_commit": request["git_commit"],
        "request_uri": request_path.relative_to(tmp_path).as_posix(),
        "request_sha256": canonical_sha256(request),
        "receipt_uri": receipt_path.relative_to(tmp_path).as_posix(),
        "receipt_sha256": receipt["receipt_sha256"],
        "source_contract_sha256": request["scope"]["source_contract_sha256"],
        "slots": slots,
    }
    package["package_sha256"] = canonical_sha256(package)
    package_path = package_dir / f"{request['request_id']}.package.json"
    package_path.write_text(json.dumps(package), encoding="utf-8")
    return package_path


def _write_p1_rigor_review(tmp_path: Path, package_path: Path) -> Path:
    package_id = package_path.name.removesuffix(".package.json")
    review_dir = tmp_path / "outputs/audits/rigor" / package_id
    review_dir.mkdir(parents=True, exist_ok=True)
    review = {
        "schema_version": "myis.rigor-review.v1",
        "review_status": "complete",
        "artifact_path": package_path.relative_to(tmp_path).as_posix(),
        "artifact_sha256": hashlib.sha256(package_path.read_bytes()).hexdigest(),
        "governance": {
            "approval_valid": True,
            "split_isolation_valid": True,
            "gate_order_valid": True,
            "budget_valid": True,
            "manifest_integrity_valid": True,
            "blocking_findings": [],
        },
        "findings": [],
    }
    path = review_dir / "rigor_review.json"
    path.write_text(json.dumps(review), encoding="utf-8")
    return path


def test_accepted_receipt_without_manifest_cannot_complete_p1(tmp_path: Path) -> None:
    _, receipt = _p1_receipt(Path(__file__).resolve().parents[1])
    _write_p1_campaign(tmp_path, receipt)
    model = build_read_model(tmp_path)
    assert model["campaigns"][0]["current_state"] == "P1_BLOCKED_WITH_EVIDENCE"
    assert model["phases"][0]["status"] == "blocked"
    assert model["metrics"] == []
    assert model["runs"] == []


def test_p1_requires_a_valid_non_invalidated_manifest_receipt_pair(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    request, receipt = _p1_receipt(repository_root)
    _write_p1_campaign(tmp_path, receipt)
    _write_p1_matrix(tmp_path, repository_root, request, receipt)
    model = build_read_model(tmp_path)
    assert model["campaigns"][0]["current_state"] == "P1_CPU_MEASURED_COMPLETE"
    assert len(model["metrics"]) == 12

    _write_p1_manifest(tmp_path, repository_root, request, receipt, arm="R0", split="train", status="superseded")
    invalidated = build_read_model(tmp_path)
    assert invalidated["campaigns"][0]["current_state"] == "P1_BLOCKED_WITH_EVIDENCE"
    assert invalidated["metrics"] == []


def test_p1_requires_validation_reports_for_all_four_slots(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    request, receipt = _p1_receipt(repository_root)
    _write_p1_campaign(tmp_path, receipt)
    paths = [
        _write_p1_manifest(
            tmp_path,
            repository_root,
            request,
            receipt,
            arm=arm,
            split=split,
            write_validation=False,
        )
        for arm in ("R0", "R0-W")
        for split in ("train", "selection")
    ]
    blocked = build_read_model(tmp_path)
    assert blocked["project"]["state"] == "P1_BLOCKED_WITH_EVIDENCE"
    assert blocked["runs"] == []
    assert blocked["metrics"] == []
    assert blocked["evidence"] == []

    for path in paths:
        _write_validation_report(tmp_path, path, request, receipt)
    promoted = build_read_model(tmp_path)
    assert promoted["project"]["state"] == "P1_CPU_MEASURED_COMPLETE"
    assert len(promoted["runs"]) == 4
    assert promoted["phases"][0]["tasks"][0]["evidence_ids"] == [request["request_id"]]
    assert len(promoted["metrics"]) == 12


def test_full_text_p1_requires_hash_bound_package_and_rigor_review(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    request, receipt = _p1_receipt(repository_root)
    _write_p1_campaign(tmp_path, receipt)
    _write_p1_matrix(tmp_path, repository_root, request, receipt)
    source_contract = tmp_path / "control/assets/dapfam-p1-source.v1.json"
    source_contract.parent.mkdir(parents=True)
    source_contract.write_text("{}", encoding="utf-8")

    assert build_read_model(tmp_path)["project"]["state"] == "P1_BLOCKED_WITH_EVIDENCE"
    package_path = _write_p1_package(tmp_path, request, receipt)
    assert build_read_model(tmp_path)["project"]["state"] == "P1_BLOCKED_WITH_EVIDENCE"
    _write_p1_rigor_review(tmp_path, package_path)
    promoted = build_read_model(tmp_path)
    assert promoted["project"]["state"] == "P1_CPU_MEASURED_COMPLETE"
    assert len(promoted["runs"]) == 4


def test_checked_in_legacy_receipt_is_hash_locked_and_never_promoted() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    receipt_path = repository_root / "campaigns/scope-autoindex-v1/evidence/legacy-p1-receipt.v2.json"
    disposition = json.loads(
        receipt_path.with_name(f"{receipt_path.stem}.disposition.json").read_text(encoding="utf-8")
    )
    assert disposition["source_file_sha256"] == "f83ae6b052334190eee08dda5ca1dde70930464d02f97f47d4ea18dc922d9766"
    model = build_read_model(repository_root)
    assert model["project"]["state"] == "P1_CPU_MEASURED_COMPLETE"
    assert len(model["runs"]) == 4
    assert len(model["metrics"]) == 12
    assert all(
        run["owner_local_receipt_sha256"] != disposition["receipt_sha256"]
        for run in model["runs"]
    )
    assert all(
        item.get("uri") != disposition["source_uri"]
        for item in model["evidence"]
    )
    assert len(model["mlflow_registration"]["children"]) == 4
    assert model["outputs"] == [{
        "output_id": "P1-LEGACY-RECEIPT",
        "phase_id": "P1_CPU_BASELINE",
        "task_id": "P1.3",
        "status": "historical_invalid_superseded",
        "evidence_class": "historical_invalid",
        "source_uri": "campaigns/scope-autoindex-v1/evidence/legacy-p1-receipt.v2.json",
        "source_sha256": "f83ae6b052334190eee08dda5ca1dde70930464d02f97f47d4ea18dc922d9766",
        "disposition_uri": "campaigns/scope-autoindex-v1/evidence/legacy-p1-receipt.v2.disposition.json",
        "promotable": False,
        "superseded_by": "fresh-owner-local-p1-rerun-pending",
    }]


def test_checked_in_p1_raw_hash_bindings_are_checkout_stable() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    source_path = repository_root / "control/assets/dapfam-p1-source.v1.json"
    package_path = repository_root / (
        "campaigns/scope-autoindex-v1/packages/"
        "dapfam-p1-fulltext-c058a3aa7357c782.package.json"
    )
    review_path = repository_root / (
        "outputs/audits/rigor/dapfam-p1-fulltext-c058a3aa7357c782/rigor_review.json"
    )
    package = json.loads(package_path.read_text(encoding="utf-8"))
    review = json.loads(review_path.read_text(encoding="utf-8"))

    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == package["source_contract_sha256"]
    assert hashlib.sha256(package_path.read_bytes()).hexdigest() == review["artifact_sha256"]

    attributes = {
        line.strip()
        for line in (repository_root / ".gitattributes").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert {
        "control/assets/dapfam-p1-source.v1.json -text",
        "campaigns/scope-autoindex-v1/packages/*.json -text",
        "outputs/audits/rigor/**/*.json -text",
    } <= attributes


def test_legacy_commitment_accepts_only_lf_crlf_checkout_variance(tmp_path: Path) -> None:
    path = tmp_path / "legacy.json"
    path.write_bytes(b'{"status":"historical-invalid"}\n')
    expected = hashlib.sha256(b'{"status":"historical-invalid"}\r\n').hexdigest()
    assert _legacy_file_commitment_matches(path, expected)
    assert not _legacy_file_commitment_matches(path, "0" * 64)


def test_manifest_metrics_must_match_the_paired_receipt(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    request, receipt = _p1_receipt(repository_root)
    _write_p1_campaign(tmp_path, receipt)
    _write_p1_matrix(tmp_path, repository_root, request, receipt)
    mismatched = [
        {**row, "value": 0.75}
        for row in receipt["metrics"]
        if row["arm"] == "R0" and row["split"] == "train"
    ]
    _write_p1_manifest(tmp_path, repository_root, request, receipt, arm="R0", split="train", metrics=mismatched)
    model = build_read_model(tmp_path)
    assert model["campaigns"][0]["current_state"] == "P1_BLOCKED_WITH_EVIDENCE"
    assert model["metrics"] == []


@pytest.mark.parametrize("invalid_metrics", [
    lambda receipt: [row for row in receipt["metrics"] if row["arm"] == "R0" and row["split"] == "train" and row["scope"] != "OUT"],
    lambda receipt: [row for row in receipt["metrics"] if row["arm"] == "R0" and row["split"] == "train"] + [receipt["metrics"][3]],
])
def test_p1_manifest_must_contain_exactly_its_three_scope_rows(tmp_path: Path, invalid_metrics) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    request, receipt = _p1_receipt(repository_root)
    _write_p1_campaign(tmp_path, receipt)
    _write_p1_matrix(tmp_path, repository_root, request, receipt)
    _write_p1_manifest(
        tmp_path,
        repository_root,
        request,
        receipt,
        arm="R0",
        split="train",
        metrics=invalid_metrics(receipt),
    )
    model = build_read_model(tmp_path)
    assert model["campaigns"][0]["current_state"] == "P1_BLOCKED_WITH_EVIDENCE"
    assert model["metrics"] == []


def test_p1_requires_all_four_arm_split_manifests(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    request, receipt = _p1_receipt(repository_root)
    _write_p1_campaign(tmp_path, receipt)
    _write_p1_manifest(tmp_path, repository_root, request, receipt, arm="R0", split="train")
    _write_p1_manifest(tmp_path, repository_root, request, receipt, arm="R0", split="selection")
    _write_p1_manifest(tmp_path, repository_root, request, receipt, arm="R0-W", split="train")
    model = build_read_model(tmp_path)
    assert model["campaigns"][0]["current_state"] == "P1_BLOCKED_WITH_EVIDENCE"


def test_p1_requires_one_receipt_and_one_manifest_per_slot(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    request, receipt = _p1_receipt(repository_root)
    alternative_request, alternative_receipt = _p1_receipt(
        repository_root,
        request_id="p1-projection-test-alt",
        value=0.6,
    )
    _write_p1_campaign(tmp_path, receipt)
    evidence_dir = tmp_path / "campaigns" / "scope-autoindex-v1" / "evidence"
    (evidence_dir / "p1-alternative-receipt.json").write_text(json.dumps(alternative_receipt), encoding="utf-8")
    _write_p1_matrix(tmp_path, repository_root, request, receipt)
    _write_p1_manifest(
        tmp_path,
        repository_root,
        alternative_request,
        alternative_receipt,
        arm="R0",
        split="train",
    )
    assert build_read_model(tmp_path)["campaigns"][0]["current_state"] == "P1_BLOCKED_WITH_EVIDENCE"

    _write_p1_manifest(
        tmp_path,
        repository_root,
        request,
        receipt,
        arm="R0",
        split="train",
        run_suffix="-duplicate",
    )
    assert build_read_model(tmp_path)["campaigns"][0]["current_state"] == "P1_BLOCKED_WITH_EVIDENCE"


def test_dataset_projection_exposes_logical_ids_without_source_paths(tmp_path: Path) -> None:
    (tmp_path / "control" / "campaigns").mkdir(parents=True)
    (tmp_path / "control" / "decisions").mkdir(parents=True)
    (tmp_path / "control" / "campaigns" / "scope-autoindex-v1.yaml").write_text("campaign: {}\n", encoding="utf-8")
    (tmp_path / "control" / "decisions" / "ledger.jsonl").write_text("", encoding="utf-8")
    inventory = {"assets": [{"path": "processed/dapfam/patents.jsonl", "bytes": 1, "sha256": "a" * 64}]}
    inventory_path = tmp_path / "evidence" / "legacy-dapfam-inventory.v1.json"
    inventory_path.parent.mkdir()
    inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
    datasets = build_read_model(tmp_path)["datasets"]
    assert datasets
    assert all("source_path" not in dataset for dataset in datasets)


def _registration_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "register_p1_mlflow.py"
    spec = importlib.util.spec_from_file_location("register_p1_mlflow_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mlflow_registration_requires_a_complete_validated_package(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    request, receipt = _p1_receipt(repository_root)
    _write_p1_campaign(tmp_path, receipt)
    _write_p1_matrix(tmp_path, repository_root, request, receipt)
    package_path = _write_p1_package(tmp_path, request, receipt)
    register_p1_mlflow = _registration_module()

    package, manifests, accepted_receipt = register_p1_mlflow.load_validated_p1_matrix(package_path, tmp_path)
    assert package["receipt_sha256"] == accepted_receipt["receipt_sha256"]
    assert len(manifests) == 4

    legacy_only = tmp_path / "legacy-only.json"
    legacy_only.write_text("{}", encoding="utf-8")
    with pytest.raises((ValueError, FileNotFoundError)):
        register_p1_mlflow.load_validated_p1_matrix(legacy_only, tmp_path)
