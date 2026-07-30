from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from myis_research.kernel.manifest import build_manifest
from myis_research.kernel.manifest_validation import capture_git_state
from myis_research.owner_local import build_receipt
from myis_research.projections.read_model import build_read_model, write_read_model
from myis_research.report_cli import validate_read_model


def test_empty_campaign_read_model_is_safe(tmp_path: Path) -> None:
    (tmp_path / "control" / "campaigns").mkdir(parents=True)
    (tmp_path / "control" / "decisions").mkdir(parents=True)
    (tmp_path / "control" / "campaigns" / "scope-autoindex-v1.yaml").write_text("campaign:\n  status: preparation\n", encoding="utf-8")
    (tmp_path / "control" / "decisions" / "ledger.jsonl").write_text("", encoding="utf-8")
    model = build_read_model(tmp_path)
    assert model["schema_version"] == "myis.read-model.v1"
    assert model["publication_readiness"]["status"] == "blocked"
    output = write_read_model(tmp_path)
    assert json.loads(output.read_text(encoding="utf-8"))["projection_revision"] == model["projection_revision"]


def test_read_model_validation_rejects_unknown_field_and_non_object(tmp_path: Path) -> None:
    (tmp_path / "control" / "campaigns").mkdir(parents=True)
    (tmp_path / "control" / "decisions").mkdir(parents=True)
    (tmp_path / "control" / "campaigns" / "scope-autoindex-v1.yaml").write_text("campaign: {}\n", encoding="utf-8")
    (tmp_path / "control" / "decisions" / "ledger.jsonl").write_text("", encoding="utf-8")
    model = build_read_model(tmp_path)
    with pytest.raises(ValueError, match="absent from its schema"):
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
        "scope": {"campaign": "a" * 64},
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
) -> Path:
    manifest_dir = tmp_path / "campaigns" / "scope-autoindex-v1" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(
        run_id=f"p1-{arm.lower()}-{split}-{status}{run_suffix}",
        parent_run_id=None,
        experiment_id="myis-research-track-c",
        campaign_id="scope-autoindex-v1",
        stage=split,
        status=status,
        source={"dataset": "dapfam"},
        data={"split": split},
        method={"arm": arm},
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
    return path


def _write_p1_matrix(tmp_path: Path, repository_root: Path, request: dict[str, object], receipt: dict[str, object]) -> None:
    for arm in ("R0", "R0-W"):
        for split in ("train", "selection"):
            _write_p1_manifest(tmp_path, repository_root, request, receipt, arm=arm, split=split)


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


def test_mlflow_registration_requires_the_same_validated_manifest_receipt_pair(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    request, receipt = _p1_receipt(repository_root)
    receipt_path = _write_p1_campaign(tmp_path, receipt)
    manifest_path = _write_p1_manifest(tmp_path, repository_root, request, receipt, arm="R0", split="train")
    register_p1_mlflow = _registration_module()

    manifest, accepted_receipt = register_p1_mlflow.load_validated_p1_package(manifest_path, receipt_path)
    assert manifest["receipt_sha256"] == accepted_receipt["receipt_sha256"]

    legacy_only = tmp_path / "legacy-only.json"
    legacy_only.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="valid manifest"):
        register_p1_mlflow.load_validated_p1_package(legacy_only, receipt_path)
