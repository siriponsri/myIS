from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from myis_research.kernel.canonical import canonical_sha256
from myis_research.kernel.manifest import build_manifest, manifest_round_trip
from myis_research.kernel.manifest_validation import (
    ManifestValidationError,
    build_validation_report,
    capture_git_state,
    validate_validation_report,
    write_validated_manifest,
)
from myis_research.owner_local import build_receipt


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _clean_repository(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    root.mkdir()
    for args in (("init",), ("config", "user.email", "tests@example.invalid"), ("config", "user.name", "Manifest Tests")):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)
    (root / "tracked.txt").write_text("clean\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=root, check=True, capture_output=True)
    return root


def _p1_metrics() -> list[dict[str, object]]:
    return [
        {"arm": arm, "name": "recall_at_100", "value": 0.5, "n": 2, "retrieved_relevant": 1, "relevant_total": 2, "scope": scope, "split": split, "direction": "maximize", "denominator": "macro_mean_per_query_relevant_families", "evidence_role": "primary" if scope == "OUT" else "secondary"}
        for arm in ("R0", "R0-W") for split in ("train", "selection") for scope in ("ALL", "IN", "OUT")
    ]


def _owner_local_binding(repository_root: Path, *, git_commit: str | None = None) -> tuple[dict, dict]:
    git = capture_git_state(repository_root)
    request = {
        "schema_version": "myis.owner-local-request.v2", "request_id": "p1-lineage-manifest",
        "decision_id": "P1_CPU_EXECUTION_ENVELOPE", "phase_id": "P1_CPU_BASELINE", "stage": "train_selection",
        "scope": {"campaign_sha256": "a" * 64}, "git_commit": git_commit or git["commit"],
        "input_hashes": {"documents_sha256": "b" * 64, "split_sha256": "c" * 64},
    }
    receipt = build_receipt(
        request, aggregate_counts={"documents": 2, "train_queries": 2, "selection_queries": 2},
        aggregate_hashes={f"{arm.lower()}_{split}_metrics": "d" * 64 for arm in ("R0", "R0-W") for split in ("train", "selection")},
        metrics=_p1_metrics(), cost_usd=0.0, latency_seconds=0.1,
        lineage_hashes={key: "b" * 64 for key in ("dataset_sha256", "corpus_sha256", "query_sha256", "qrels_sha256", "split_sha256", "index_sha256", "evaluator_sha256")},
    )
    return request, receipt


def _manifest(repository_root: Path) -> tuple[dict, dict, dict]:
    request, receipt = _owner_local_binding(repository_root)
    payload = build_manifest(
        run_id="run-lineage", parent_run_id=None, experiment_id="exp-lineage", campaign_id="scope-autoindex-v1",
        stage="train", status="valid", source={"dataset": "dapfam"}, data={"split": "train"},
        method={"arm_id": "R0", "algorithm": "bm25"}, resources={"cpu_only": True, "cost_usd": 0.0},
        metrics=[row for row in receipt["metrics"] if row["arm"] == "R0" and row["split"] == "train"], artifacts=[],
        evidence_class="train_selection_measured", repository_root=repository_root,
        owner_local_request=request, owner_local_receipt=receipt, timestamp="2026-07-30T12:00:00Z",
    )
    return payload, request, receipt


def test_schema_json_round_trip_matches_canonical_payload(tmp_path: Path) -> None:
    payload, _, _ = _manifest(_clean_repository(tmp_path))
    schema = json.loads((REPOSITORY_ROOT / "schemas" / "run-manifest.v2.json").read_text(encoding="utf-8"))
    persisted = tmp_path / "round-trip.json"
    persisted.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    restored = json.loads(persisted.read_text(encoding="utf-8"))
    assert set(restored) == set(schema["required"])
    assert manifest_round_trip(restored) == payload


def test_untracked_request_does_not_dirty_code_but_tracked_change_is_committed(tmp_path: Path) -> None:
    repository_root = _clean_repository(tmp_path)
    (repository_root / "request.json").write_text("{}", encoding="utf-8")
    captured = capture_git_state(repository_root)
    assert captured["tracked_worktree_state"] == "clean"
    (repository_root / "tracked.txt").write_text("changed\n", encoding="utf-8")
    dirty = capture_git_state(repository_root)
    assert dirty["tracked_worktree_state"] == "dirty"
    assert dirty["tracked_worktree_diff_sha256"] != captured["tracked_worktree_diff_sha256"]


def test_commitments_and_manifest_hash_fail_closed_after_mutation(tmp_path: Path) -> None:
    payload, _, _ = _manifest(_clean_repository(tmp_path))
    payload["resources"]["cost_usd"] = 1.0
    with pytest.raises(ManifestValidationError, match="resources_sha256"):
        manifest_round_trip(payload)


def test_builder_rejects_request_not_bound_to_actual_head(tmp_path: Path) -> None:
    repository_root = _clean_repository(tmp_path)
    request, receipt = _owner_local_binding(repository_root, git_commit="e" * 40)
    with pytest.raises(ValueError, match="repository HEAD"):
        build_manifest(run_id="run-lineage", experiment_id="exp-lineage", campaign_id="scope-autoindex-v1", stage="train", status="valid", source={}, data={}, method={}, resources={}, metrics=[], artifacts=[], evidence_class="train_selection_measured", repository_root=repository_root, owner_local_request=request, owner_local_receipt=receipt)


def test_validation_report_is_schema_valid_and_written_before_immutable_manifest(tmp_path: Path) -> None:
    repository_root = _clean_repository(tmp_path)
    payload, request, receipt = _manifest(repository_root)
    report_path = tmp_path / "validation.json"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("existing immutable manifest", encoding="utf-8")
    with pytest.raises(ManifestValidationError, match="refusing to overwrite"):
        write_validated_manifest(manifest_path, report_path, payload, owner_local_request=request, owner_local_receipt=receipt, timestamp="2026-07-30T12:00:00Z")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    validate_validation_report(report)
    assert report == build_validation_report(payload, owner_local_request=request, owner_local_receipt=receipt, timestamp="2026-07-30T12:00:00Z")


def test_dirty_tracked_state_cannot_be_persisted(tmp_path: Path) -> None:
    repository_root = _clean_repository(tmp_path)
    payload, request, receipt = _manifest(repository_root)
    (repository_root / "tracked.txt").write_text("changed\n", encoding="utf-8")
    payload["git"] = capture_git_state(repository_root)
    payload["manifest_sha256"] = canonical_sha256({key: value for key, value in payload.items() if key != "manifest_sha256"})
    with pytest.raises(ManifestValidationError, match="tracked worktree must be clean"):
        write_validated_manifest(tmp_path / "manifest.json", tmp_path / "validation.json", payload, owner_local_request=request, owner_local_receipt=receipt)
