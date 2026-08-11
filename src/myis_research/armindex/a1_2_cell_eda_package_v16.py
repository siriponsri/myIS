"""Build publication-facing A1.2 EDA from validated aggregate cell receipts."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import re
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_json, canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a1_2_measured_result_summary_v16 import (
    MeasuredResultSummaryV16Error,
    load_validated_cell_receipts,
    validate_measured_result_summary_file,
)
from .a1_2_owner_local_evaluator_v16 import ARM_IDS, CELL_IDS

SCHEMA_PATH = Path("schemas/armindex/a1.2-cell-eda-package.v16.json")
PACKAGE_DIRECTORY = Path(
    "campaigns/armindex-multiretriever-v2/evidence/a1.2-cell-eda"
)
_ATTEMPT_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
_DATED_ATTEMPT = re.compile(r"^a12-v16-(?P<date>[0-9]{8})-(?P<retry>r[0-9]+)$")
_PROGRAM_IDS = (
    "P00-TAC-DOC",
    "P01-TA-DOC",
    "P02-CLAIM1",
    "P03-PASSAGE",
    "P04-SECTION-MULTIVIEW",
)
_ARM_LABELS = {
    "ARM-01": "BM25 lexical",
    "ARM-02": "BGE-M3 dense",
    "ARM-03": "PatEmbed dense",
    "ARM-04": "Arctic Embed dense",
    "ARM-05": "Qwen3 Embedding dense",
}
_PROGRAM_LABELS = {
    "P00-TAC-DOC": "Title + abstract + claims",
    "P01-TA-DOC": "Title + abstract",
    "P02-CLAIM1": "First claim segment",
    "P03-PASSAGE": "Fixed passages",
    "P04-SECTION-MULTIVIEW": "Title / abstract / claims views",
}


class CellEdaPackageV16Error(ValueError):
    """Raised when safe A1.2 cell evidence cannot form a publication EDA package."""


def package_path(attempt_id: str) -> Path:
    return PACKAGE_DIRECTORY / f"{attempt_id}.eda.v16.json"


def csv_path(attempt_id: str) -> Path:
    return Path("outputs/tables/armindex") / f"{attempt_id}.cell-eda.v16.csv"


def quality_figure_path(attempt_id: str, suffix: str) -> Path:
    return Path("outputs/figures/armindex") / (
        f"{attempt_id}.quality-cell-eda.v16.{suffix}"
    )


def efficiency_figure_path(attempt_id: str, suffix: str) -> Path:
    return Path("outputs/figures/armindex") / (
        f"{attempt_id}.efficiency-cell-eda.v16.{suffix}"
    )


def thai_report_path(attempt_id: str) -> Path:
    if _ATTEMPT_ID.fullmatch(attempt_id) is None:
        raise CellEdaPackageV16Error("attempt ID cannot form an EDA report path")
    match = _DATED_ATTEMPT.fullmatch(attempt_id)
    filename = (
        f"A1_2_{match.group('retry').upper()}_CELL_EDA_{match.group('date')}_TH.md"
        if match is not None
        else f"A1_2_{attempt_id.upper()}_CELL_EDA_TH.md"
    )
    return Path("docs/operations") / filename


def _load(path: Path, *, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CellEdaPackageV16Error(f"{role} is invalid") from error
    if not isinstance(value, dict):
        raise CellEdaPackageV16Error(f"{role} must be an object")
    return value


def _schema(root: Path, value: Mapping[str, Any]) -> None:
    errors = sorted(
        Draft202012Validator(_load(root / SCHEMA_PATH, role="EDA schema")).iter_errors(
            dict(value)
        ),
        key=lambda error: list(error.path),
    )
    if errors:
        raise CellEdaPackageV16Error(
            f"EDA schema validation failed: {errors[0].message}"
        )


def _self_hash(value: Mapping[str, Any]) -> None:
    body = dict(value)
    if body.pop("package_sha256", None) != canonical_sha256(body):
        raise CellEdaPackageV16Error("EDA package self-hash mismatch")


def _cell_rows(
    receipts: Mapping[str, Mapping[str, Any]],
    receipt_set_sha256: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cell_id in CELL_IDS:
        receipt = receipts[cell_id]
        arm_id, program_id = cell_id.split("--", 1)
        if receipt.get("arm_id") != arm_id or receipt.get("program_id") != program_id:
            raise CellEdaPackageV16Error(f"cell identity drifted: {cell_id}")
        quality = receipt.get("quality")
        performance = receipt.get("performance")
        resources = receipt.get("resources")
        reliability = receipt.get("reliability")
        if not all(
            isinstance(value, Mapping)
            for value in (quality, performance, resources, reliability)
        ):
            raise CellEdaPackageV16Error(f"cell aggregates are incomplete: {cell_id}")
        latency = performance.get("search_latency_ms")
        if not isinstance(latency, Mapping):
            raise CellEdaPackageV16Error(f"cell latency is incomplete: {cell_id}")
        rows.append(
            {
                "cell_id": cell_id,
                "arm_id": arm_id,
                "arm_label": _ARM_LABELS[arm_id],
                "program_id": program_id,
                "program_label": _PROGRAM_LABELS[program_id],
                "out_recall_at_100": float(quality["recall_at_100_out"]),
                "out_ndcg_at_100": float(quality["ndcg_at_100_out"]),
                "out_ndcg_at_10": float(quality["ndcg_at_10_out"]),
                "search_latency_p50_ms": float(latency["p50"]),
                "search_latency_p95_ms": float(latency["p95"]),
                "search_latency_p99_ms": float(latency["p99"]),
                "throughput_qps": float(performance["throughput_qps"]),
                "wall_seconds": float(performance["wall_seconds"]),
                "peak_host_ram_bytes": int(resources["peak_host_ram_bytes"]),
                "peak_vram_bytes": int(resources["peak_vram_bytes"]),
                "index_size_bytes": int(resources["index_size_bytes"]),
                "replay_count": int(reliability["ranking_replay_count"]),
                "retry_count": int(reliability["retry_count"]),
                "failure_rate": float(quality["failure_rate"]),
                "receipt_sha256": str(receipt["receipt_sha256"]),
                "receipt_file_sha256": str(receipt["receipt_file_sha256"]),
            }
        )
    if len(rows) != 25 or receipt_set_sha256 == "0" * 64:
        raise CellEdaPackageV16Error("EDA cell coverage is incomplete")
    return rows


_CSV_FIELDS = (
    "cell_id",
    "arm_id",
    "arm_label",
    "program_id",
    "program_label",
    "out_recall_at_100",
    "out_ndcg_at_100",
    "out_ndcg_at_10",
    "search_latency_p50_ms",
    "search_latency_p95_ms",
    "search_latency_p99_ms",
    "throughput_qps",
    "wall_seconds",
    "peak_host_ram_bytes",
    "peak_vram_bytes",
    "index_size_bytes",
    "replay_count",
    "retry_count",
    "failure_rate",
    "receipt_sha256",
    "receipt_file_sha256",
)


def _csv_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=_CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row[key] for key in _CSV_FIELDS})
    return stream.getvalue().encode("utf-8")


def _matrix(rows: Sequence[Mapping[str, Any]], key: str) -> list[list[float]]:
    by_cell = {str(row["cell_id"]): row for row in rows}
    return [
        [float(by_cell[f"{arm_id}--{program_id}"][key]) for program_id in _PROGRAM_IDS]
        for arm_id in ARM_IDS
    ]


def _figure_bytes(
    rows: Sequence[Mapping[str, Any]], *, family: str, suffix: str
) -> bytes:
    try:
        import matplotlib

        matplotlib.use("Agg")
        from matplotlib import pyplot as plt
        from matplotlib.colors import Normalize
    except ImportError as error:
        raise CellEdaPackageV16Error("matplotlib is required for EDA figures") from error

    if family == "quality":
        panels = (
            ("OUT Recall@100", "out_recall_at_100", "viridis", 0.0, 1.0, ".3f"),
            ("OUT nDCG@100", "out_ndcg_at_100", "viridis", 0.0, 1.0, ".3f"),
            ("OUT nDCG@10", "out_ndcg_at_10", "viridis", 0.0, 1.0, ".3f"),
        )
        title = "Representation effects vary across retrievers on REP-DEV"
        footer = "Descriptive 25-cell aggregates; no per-query outcomes or confidence intervals are projected."
    elif family == "efficiency":
        panels = (
            ("Search p95 (ms)", "search_latency_p95_ms", "cividis", None, None, ".1f"),
            ("Wall time (min)", "wall_seconds", "cividis", None, None, ".1f"),
            ("Peak VRAM (GiB)", "peak_vram_bytes", "cividis", None, None, ".2f"),
        )
        title = "Resource cost differs across retriever-program cells"
        footer = "Wall time and memory are measured execution diagnostics, not promotion overrides."
    else:
        raise CellEdaPackageV16Error("unknown EDA figure family")

    matrices: list[list[list[float]]] = []
    for _label, key, _cmap, _vmin, _vmax, _fmt in panels:
        matrix = _matrix(rows, key)
        if key == "wall_seconds":
            matrix = [[value / 60.0 for value in row] for row in matrix]
        elif key == "peak_vram_bytes":
            matrix = [[value / (1024.0**3) for value in row] for row in matrix]
        matrices.append(matrix)

    with matplotlib.rc_context(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8,
            "axes.titlesize": 9,
            "figure.titlesize": 12,
            "svg.hashsalt": "myis-a1.2-cell-eda-v16",
            "svg.fonttype": "none",
        }
    ):
        figure, axes = plt.subplots(1, 3, figsize=(13.2, 4.4), constrained_layout=True)
        for axis, panel, matrix in zip(axes, panels, matrices, strict=True):
            label, _key, cmap, fixed_min, fixed_max, fmt = panel
            flat = [value for row in matrix for value in row]
            vmin = fixed_min if fixed_min is not None else min(flat)
            vmax = fixed_max if fixed_max is not None else max(flat)
            if math.isclose(vmin, vmax):
                vmax = vmin + 1.0
            image = axis.imshow(matrix, cmap=cmap, norm=Normalize(vmin=vmin, vmax=vmax))
            axis.set_title(label)
            axis.set_xticks(range(5), [_PROGRAM_LABELS[item] for item in _PROGRAM_IDS])
            axis.set_yticks(range(5), [_ARM_LABELS[item] for item in ARM_IDS])
            axis.tick_params(axis="x", rotation=35, labelsize=7)
            axis.tick_params(axis="y", labelsize=7)
            threshold = vmin + (vmax - vmin) * 0.55
            for row_index, row in enumerate(matrix):
                for column_index, value in enumerate(row):
                    axis.text(
                        column_index,
                        row_index,
                        format(value, fmt),
                        ha="center",
                        va="center",
                        fontsize=6.5,
                        color="white" if value >= threshold else "black",
                    )
            figure.colorbar(image, ax=axis, fraction=0.046, pad=0.03)
        figure.suptitle(title, fontweight="bold")
        figure.text(0.5, 0.005, footer, ha="center", va="bottom", fontsize=7)
        buffer = io.BytesIO()
        metadata = (
            {"Creator": "myIS Research", "Date": None}
            if suffix == "svg"
            else {"Software": "myIS Research"}
        )
        figure.savefig(
            buffer,
            format=suffix,
            dpi=200 if suffix == "png" else None,
            bbox_inches="tight",
            metadata=metadata,
        )
        plt.close(figure)
    return buffer.getvalue()


def _thai_report(attempt_id: str, rows: Sequence[Mapping[str, Any]]) -> bytes:
    table_rows = []
    for row in rows:
        table_rows.append(
            "| {arm} | {program} | {recall:.6f} | {ndcg100:.6f} | {ndcg10:.6f} | {p95:.2f} | {wall:.2f} | {vram:.2f} |".format(
                arm=row["arm_label"],
                program=row["program_label"],
                recall=float(row["out_recall_at_100"]),
                ndcg100=float(row["out_ndcg_at_100"]),
                ndcg10=float(row["out_ndcg_at_10"]),
                p95=float(row["search_latency_p95_ms"]),
                wall=float(row["wall_seconds"]) / 60.0,
                vram=int(row["peak_vram_bytes"]) / (1024.0**3),
            )
        )
    text = "\n".join(
        [
            "---",
            "managed_by: myis-a1.2-cell-eda-v16",
            "edit_policy: generated_do_not_edit",
            "status: completed",
            "evidence_class: measured_development_aggregate_eda",
            "scientific_authority: true",
            f"attempt_id: {attempt_id}",
            "---",
            "",
            "# EDA ราย cell สำหรับ A1.2",
            "",
            "เอกสารนี้สรุปผล aggregate ครบ 25 cells สำหรับใช้เตรียมการนำเสนอและบทความวารสาร",
            "ตัวเลขมาจาก aggregate result receipts หลัง safe return และ Owner-local evaluation เท่านั้น",
            "ไม่มี query ID, qrels, membership, raw ranking หรือตัวอย่างผลราย query ในเอกสารนี้",
            "",
            "## ควรอ่านกราฟอย่างไร",
            "",
            "- Quality figure เปรียบเทียบ Recall และ nDCG ของ retriever-program แต่ละคู่บน REP-DEV",
            "- Efficiency figure เปรียบเทียบ search latency, wall time และ peak VRAM",
            "- สีช่วยให้เห็น pattern แต่ตัวเลขในช่องเป็นค่าที่ใช้อ้างอิง",
            "- EDA นี้เป็น descriptive evidence ยังไม่ใช่ Final confirmation และไม่มี confidence interval ราย query",
            "",
            "## Artifacts",
            "",
            f"- Canonical EDA JSON: `{package_path(attempt_id).as_posix()}`",
            f"- ตาราง CSV: `{csv_path(attempt_id).as_posix()}`",
            f"- Quality figure: `{quality_figure_path(attempt_id, 'png').as_posix()}`",
            f"- Efficiency figure: `{efficiency_figure_path(attempt_id, 'png').as_posix()}`",
            "",
            "## ตารางครบ 25 cells",
            "",
            "| Retriever | Representation | Recall@100 | nDCG@100 | nDCG@10 | Search p95 ms | Wall min | Peak VRAM GiB |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
            *table_rows,
            "",
            "## ขอบเขตการตีความ",
            "",
            "ผลนี้ใช้แสดงความสัมพันธ์เชิงพรรณนาระหว่าง retriever กับ representation program บน REP-DEV",
            "ห้ามตีความเป็นเหตุและผล ห้ามใช้แทน Selection/Final และห้ามใช้เป็นข้อสรุปทางกฎหมาย",
            "",
        ]
    )
    return text.encode("utf-8")


def _write_immutable(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or not path.is_file() or path.read_bytes() != payload:
            raise CellEdaPackageV16Error(
                f"immutable EDA artifact already differs: {path.as_posix()}"
            )
        return
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _artifact(root: Path, path: Path, purpose: str) -> dict[str, str]:
    target = root / path
    return {
        "uri": path.as_posix(),
        "file_sha256": file_sha256(target),
        "purpose": purpose,
    }


def write_cell_eda_package(
    repository_root: Path, evaluation_attempt_root: Path
) -> tuple[Path, dict[str, Any]]:
    """Write one immutable aggregate-safe publication EDA package."""

    root = repository_root.resolve(strict=True)
    evaluation = evaluation_attempt_root.resolve(strict=True)
    attempt_id = evaluation.name
    if _ATTEMPT_ID.fullmatch(attempt_id) is None:
        raise CellEdaPackageV16Error("evaluation attempt ID is invalid")
    try:
        summary = validate_measured_result_summary_file(root, attempt_id)
        receipts, receipt_set_sha256 = load_validated_cell_receipts(root, evaluation)
    except (MeasuredResultSummaryV16Error, OSError, ValueError) as error:
        raise CellEdaPackageV16Error(str(error)) from error
    if receipt_set_sha256 != summary["lineage"]["cell_receipt_set_sha256"]:
        raise CellEdaPackageV16Error("EDA receipt set does not bind measured summary")
    for cell_id, receipt in receipts.items():
        receipt["receipt_file_sha256"] = file_sha256(
            evaluation / "receipts" / f"{cell_id}.json"
        )
    rows = _cell_rows(receipts, receipt_set_sha256)

    artifacts_payload = {
        csv_path(attempt_id): _csv_bytes(rows),
        quality_figure_path(attempt_id, "png"): _figure_bytes(
            rows, family="quality", suffix="png"
        ),
        quality_figure_path(attempt_id, "svg"): _figure_bytes(
            rows, family="quality", suffix="svg"
        ),
        efficiency_figure_path(attempt_id, "png"): _figure_bytes(
            rows, family="efficiency", suffix="png"
        ),
        efficiency_figure_path(attempt_id, "svg"): _figure_bytes(
            rows, family="efficiency", suffix="svg"
        ),
        thai_report_path(attempt_id): _thai_report(attempt_id, rows),
    }
    for relative, payload in artifacts_payload.items():
        _write_immutable(root / relative, payload)

    package = {
        "schema_version": "myis.armindex-a1.2-cell-eda-package.v16",
        "package_id": f"{attempt_id}-cell-eda-v16",
        "attempt_id": attempt_id,
        "phase_id": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
        "task_id": "A1.2",
        "status": "PASS",
        "evidence_class": "measured_development_aggregate_eda",
        "scientific_authority": True,
        "claim_boundary": (
            "Descriptive aggregate-only 25-cell EDA on REP-DEV; protected qrels, "
            "membership, identifiers, rankings, and per-query outcomes remain "
            "Owner-local, and no Selection or Final claim is supported."
        ),
        "metric_contract": {
            "primary": "OUT Recall@100",
            "secondary": ["OUT nDCG@100", "OUT nDCG@10"],
            "eda_role": "descriptive_cell_level_no_per_query_projection",
        },
        "coverage": {
            "arm_count": 5,
            "program_count": 5,
            "cell_count": 25,
            "queries_per_cell": 150,
            "top_k": 100,
        },
        "cells": rows,
        "artifacts": {
            "csv": _artifact(root, csv_path(attempt_id), "Exact 25-cell aggregate table for journal and audit use."),
            "quality_figure_png": _artifact(root, quality_figure_path(attempt_id, "png"), "Raster paper and slide figure for the three frozen quality metrics."),
            "quality_figure_svg": _artifact(root, quality_figure_path(attempt_id, "svg"), "Editable vector paper figure for the three frozen quality metrics."),
            "efficiency_figure_png": _artifact(root, efficiency_figure_path(attempt_id, "png"), "Raster diagnostic figure for latency, wall time, and peak VRAM."),
            "efficiency_figure_svg": _artifact(root, efficiency_figure_path(attempt_id, "svg"), "Editable vector diagnostic figure for latency, wall time, and peak VRAM."),
            "thai_report": _artifact(root, thai_report_path(attempt_id), "Beginner-readable Thai guide and complete 25-cell aggregate table."),
        },
        "lineage": {
            "measured_result_summary_sha256": summary["summary_sha256"],
            "cell_receipt_set_sha256": receipt_set_sha256,
            "promotion_receipt_sha256": summary["lineage"]["promotion_receipt_sha256"],
            "evaluator_closeout_receipt_sha256": summary["lineage"]["evaluator_closeout_receipt_sha256"],
        },
        "access_counters": {
            "harness_dev_accesses": 0,
            "selection_accesses": 0,
            "final_accesses": 0,
        },
    }
    package["package_sha256"] = canonical_sha256(package)
    validate_cell_eda_package(root, package)
    target = root / package_path(attempt_id)
    _write_immutable(target, (canonical_json(package) + "\n").encode("ascii"))
    return target, package


def validate_cell_eda_package(
    repository_root: Path, value: Mapping[str, Any]
) -> dict[str, Any]:
    root = repository_root.resolve(strict=True)
    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise CellEdaPackageV16Error(str(error)) from error
    _schema(root, value)
    _self_hash(value)
    cells = value.get("cells")
    if not isinstance(cells, list) or [item.get("cell_id") for item in cells] != list(
        CELL_IDS
    ):
        raise CellEdaPackageV16Error("EDA cell order or identity drifted")
    for artifact in value["artifacts"].values():
        path = root / artifact["uri"]
        if not path.is_file() or path.is_symlink():
            raise CellEdaPackageV16Error("EDA artifact is missing or unsafe")
        if file_sha256(path) != artifact["file_sha256"]:
            raise CellEdaPackageV16Error("EDA artifact hash mismatch")
    return dict(value)


def validate_cell_eda_package_file(
    repository_root: Path, attempt_id: str
) -> dict[str, Any]:
    root = repository_root.resolve(strict=True)
    path = root / package_path(attempt_id)
    if not path.is_file() or path.is_symlink():
        raise CellEdaPackageV16Error("EDA package is missing or unsafe")
    value = validate_cell_eda_package(root, _load(path, role="EDA package"))
    if value.get("attempt_id") != attempt_id:
        raise CellEdaPackageV16Error("EDA package attempt drifted")
    return {
        **value,
        "package_uri": package_path(attempt_id).as_posix(),
        "package_file_sha256": file_sha256(path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-cell-eda-v16")
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--evaluation-attempt-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        path, package = write_cell_eda_package(
            args.repository_root, args.evaluation_attempt_root
        )
    except (CellEdaPackageV16Error, OSError, ValueError) as error:
        parser.error(str(error))
    print(
        canonical_json(
            {
                "status": "PASS",
                "attempt_id": package["attempt_id"],
                "cell_count": 25,
                "package_uri": path.relative_to(
                    args.repository_root.resolve()
                ).as_posix(),
                "package_sha256": package["package_sha256"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "PACKAGE_DIRECTORY",
    "SCHEMA_PATH",
    "CellEdaPackageV16Error",
    "csv_path",
    "efficiency_figure_path",
    "main",
    "package_path",
    "quality_figure_path",
    "thai_report_path",
    "validate_cell_eda_package",
    "validate_cell_eda_package_file",
    "write_cell_eda_package",
]
