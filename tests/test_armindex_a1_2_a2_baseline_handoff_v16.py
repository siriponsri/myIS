from __future__ import annotations

import json
from pathlib import Path

import pytest

from myis_research.armindex import a1_2_a2_baseline_handoff_v16 as handoff
from myis_research.kernel.canonical import canonical_sha256, file_sha256


def _sources(tmp_path: Path) -> tuple[Path, Path]:
    archive = tmp_path / "safe-return.tar.gz"
    archive.write_bytes(b"validated-safe-return")
    evaluation = tmp_path / "a12-v16-test"
    receipts = evaluation / "receipts"
    receipts.mkdir(parents=True)
    for index in range(25):
        (receipts / f"cell-{index:02d}.json").write_text(f'{{"cell":{index}}}\n', encoding="ascii")
    promotion = {"receipt_sha256": "b" * 64}
    (evaluation / "promotion.json").write_text(json.dumps(promotion), encoding="ascii")
    closeout = {
        "attempt_id": evaluation.name,
        "safe_return_archive_sha256": file_sha256(archive),
        "receipt_sha256": "c" * 64,
    }
    (evaluation / handoff.RECEIPT_NAME).write_text(json.dumps(closeout), encoding="ascii")
    (evaluation / "dense-embeddings.bin").write_bytes(b"must-not-copy")
    return archive, evaluation


def _validated(archive: Path, evaluation: Path) -> dict[str, object]:
    return {
        "attempt_id": evaluation.name,
        "safe_return_archive_sha256": file_sha256(archive),
        "evaluation_lineage_sha256": "d" * 64,
        "cell_receipt_count": 25,
        "cell_receipt_set_sha256": "e" * 64,
        "promotion_receipt_sha256": "b" * 64,
        "promoted_arm_ids": ["ARM-02", "ARM-03"],
    }


def test_builds_minimal_owner_local_handoff_and_excludes_dense_working_data(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    archive, evaluation = _sources(tmp_path)
    monkeypatch.setattr(
        handoff,
        "validate_evaluator_closeout_inputs",
        lambda _repository, _evaluation: _validated(archive, evaluation),
    )
    monkeypatch.setattr(
        handoff,
        "validate_evaluator_closeout_receipt",
        lambda _repository, value: value,
    )
    output = tmp_path / "owner-store" / evaluation.name

    result = handoff.build_a1_a2_baseline_handoff(
        repository_root=repository,
        safe_return_archive=archive,
        evaluation_attempt_root=evaluation,
        output_root=output,
        remote_root_label="/opt/myis/a12-v16-test",
    )

    assert result["status"] == "PASS"
    assert result["copied_file_count"] == 28
    assert result["a2_execution_authorized"] is False
    assert (output / "safe-return" / "safe-return.tar.gz").read_bytes() == archive.read_bytes()
    assert len(list((output / "aggregate" / "receipts").glob("*.json"))) == 25
    assert not (output / "dense-embeddings.bin").exists()
    manifest = json.loads((output / handoff.MANIFEST_NAME).read_text(encoding="ascii"))
    expected_sha = canonical_sha256({key: value for key, value in manifest.items() if key != "manifest_sha256"})
    assert manifest["manifest_sha256"] == expected_sha
    assert "dense_embeddings" in manifest["forbidden_artifact_classes_excluded"]


def test_rejects_handoff_inside_repository(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    archive, evaluation = _sources(tmp_path)
    monkeypatch.setattr(
        handoff,
        "validate_evaluator_closeout_inputs",
        lambda _repository, _evaluation: _validated(archive, evaluation),
    )

    with pytest.raises(handoff.A1A2BaselineHandoffV16Error, match="outside the repository"):
        handoff.build_a1_a2_baseline_handoff(
            repository_root=repository,
            safe_return_archive=archive,
            evaluation_attempt_root=evaluation,
            output_root=repository / "data",
            remote_root_label="/opt/myis/a12-v16-test",
        )


def test_rejects_archive_not_bound_by_evaluation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    archive, evaluation = _sources(tmp_path)
    values = _validated(archive, evaluation)
    values["safe_return_archive_sha256"] = "0" * 64
    monkeypatch.setattr(
        handoff,
        "validate_evaluator_closeout_inputs",
        lambda _repository, _evaluation: values,
    )

    with pytest.raises(handoff.A1A2BaselineHandoffV16Error, match="differs from evaluation lineage"):
        handoff.build_a1_a2_baseline_handoff(
            repository_root=repository,
            safe_return_archive=archive,
            evaluation_attempt_root=evaluation,
            output_root=tmp_path / "owner-store" / evaluation.name,
            remote_root_label="/opt/myis/a12-v16-test",
        )
