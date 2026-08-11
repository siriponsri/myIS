from __future__ import annotations

import csv
import io
import json
import shutil
from pathlib import Path

import pytest
from test_armindex_a1_2_evaluator_closeout_v16 import _evaluation

from myis_research.armindex.a1_2_cell_eda_package_v16 import (
    CellEdaPackageV16Error,
    csv_path,
    efficiency_figure_path,
    quality_figure_path,
    thai_report_path,
    validate_cell_eda_package_file,
    write_cell_eda_package,
)
from myis_research.armindex.a1_2_evaluator_closeout_v16 import (
    write_evaluator_closeout_receipt,
)
from myis_research.armindex.a1_2_measured_result_summary_v16 import (
    validate_measured_result_summary_file,
    write_measured_result_summary,
)
from myis_research.report_records import _artifacts

ROOT = Path(__file__).resolve().parents[1]


def _repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    schema_root = repository / "schemas" / "armindex"
    schema_root.mkdir(parents=True)
    for name in (
        "a1.2-aggregate-result-receipt.v11.json",
        "a1.2-evaluator-closeout-receipt.v16.json",
        "a1.2-measured-result-summary.v16.json",
        "a1.2-cell-eda-package.v16.json",
    ):
        shutil.copy2(ROOT / "schemas" / "armindex" / name, schema_root / name)
    return repository


def _ready(tmp_path: Path) -> tuple[Path, Path]:
    evaluation = _evaluation(tmp_path)
    write_evaluator_closeout_receipt(ROOT, evaluation)
    repository = _repository(tmp_path)
    write_measured_result_summary(repository, evaluation)
    return repository, evaluation


def test_writes_25_cell_publication_eda_without_protected_examples(
    tmp_path: Path,
) -> None:
    repository, evaluation = _ready(tmp_path)

    path, package = write_cell_eda_package(repository, evaluation)

    assert path.is_file()
    assert package["coverage"] == {
        "arm_count": 5,
        "program_count": 5,
        "cell_count": 25,
        "queries_per_cell": 150,
        "top_k": 100,
    }
    assert len(package["cells"]) == 25
    assert package["cells"][0]["cell_id"] == "ARM-01--P00-TAC-DOC"
    assert package["cells"][-1]["cell_id"] == "ARM-05--P04-SECTION-MULTIVIEW"
    assert all(item["out_recall_at_100"] == 1.0 for item in package["cells"])
    assert all(item["replay_count"] == 2 for item in package["cells"])

    csv_file = repository / csv_path(evaluation.name)
    rows = list(csv.DictReader(io.StringIO(csv_file.read_text(encoding="utf-8"))))
    assert len(rows) == 25
    assert {row["cell_id"] for row in rows} == {
        item["cell_id"] for item in package["cells"]
    }
    for figure in (
        quality_figure_path(evaluation.name, "png"),
        quality_figure_path(evaluation.name, "svg"),
        efficiency_figure_path(evaluation.name, "png"),
        efficiency_figure_path(evaluation.name, "svg"),
    ):
        assert (repository / figure).stat().st_size > 1_000
    thai = (repository / thai_report_path(evaluation.name)).read_text(encoding="utf-8")
    assert "ตารางครบ 25 cells" in thai
    assert thai.count("| BM25 lexical |") == 5

    projected = json.dumps(package, ensure_ascii=False) + csv_file.read_text(
        encoding="utf-8"
    ) + thai
    assert "Q-" not in projected and "F-" not in projected
    validated = validate_cell_eda_package_file(repository, evaluation.name)
    assert validated["package_sha256"] == package["package_sha256"]
    summary = validate_measured_result_summary_file(repository, evaluation.name)
    artifacts = _artifacts(
        repository,
        {
            "armindex": {
                "a1_2_current_attempt": {
                    "validated": True,
                    "status": "PASS",
                    "measured_result_summary": summary,
                    "cell_eda_package": validated,
                }
            }
        },
        "A1_BASELINES_AND_MULTI_ARM_SCREENING",
        "A1.2",
    )
    assert any(item["artifact_id"] == "a12-cell-eda-package-v16" for item in artifacts)


def test_eda_write_is_byte_stable(tmp_path: Path) -> None:
    repository, evaluation = _ready(tmp_path)

    first_path, first = write_cell_eda_package(repository, evaluation)
    first_bytes = first_path.read_bytes()
    second_path, second = write_cell_eda_package(repository, evaluation)

    assert second_path.read_bytes() == first_bytes
    assert second["package_sha256"] == first["package_sha256"]


def test_rejects_tampered_figure(tmp_path: Path) -> None:
    repository, evaluation = _ready(tmp_path)
    write_cell_eda_package(repository, evaluation)
    figure = repository / quality_figure_path(evaluation.name, "png")
    figure.write_bytes(figure.read_bytes() + b"tamper")

    with pytest.raises(CellEdaPackageV16Error, match="artifact hash mismatch"):
        validate_cell_eda_package_file(repository, evaluation.name)


def test_requires_measured_summary_before_eda(tmp_path: Path) -> None:
    evaluation = _evaluation(tmp_path)
    write_evaluator_closeout_receipt(ROOT, evaluation)
    repository = _repository(tmp_path)

    with pytest.raises(CellEdaPackageV16Error, match="measured result summary"):
        write_cell_eda_package(repository, evaluation)
