"""Build aggregate-only A3 EDA tables and publication figures."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


PRIMARY_ARMS = ("ARM-03", "ARM-04", "ARM-05")
ARM_LABELS = {
    "ARM-03": "PatEmbed",
    "ARM-04": "Arctic Embed",
    "ARM-05": "Qwen3 Embedding",
}


def _rows(audit: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    transfer: list[dict[str, Any]] = []
    fixed: list[dict[str, Any]] = []
    for operation_id, value in sorted(audit["metrics_and_latency"].items()):
        metrics = value["metrics"]
        latency = value["latency"]
        row = {
            "operation_id": operation_id,
            "recall_at_100_out": metrics["recall_at_100/out"],
            "ndcg_at_100_out": metrics["ndcg_at_100/out"],
            "ndcg_at_10_out": metrics["ndcg_at_10/out"],
            "wall_seconds": latency["wall_seconds"],
            "search_p95_seconds": latency["search_p95_seconds"],
            "expected_units": value["coverage"]["expected_units"],
            "completed_units": value["coverage"]["completed_units"],
        }
        if operation_id.startswith("transfer-arm-"):
            source, target = operation_id.removeprefix("transfer-arm-").split("-to-arm-")
            row.update({"source_arm": f"ARM-{source}", "target_arm": f"ARM-{target}"})
            transfer.append(row)
        else:
            row["control"] = operation_id.removeprefix("fixed-")
            fixed.append(row)
    return transfer, fixed


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _build_figures(transfer: list[dict[str, Any]], fixed: list[dict[str, Any]], figure_dir: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    figure_dir.mkdir(parents=True, exist_ok=True)
    matrix = np.array(
        [
            [next(row["recall_at_100_out"] for row in transfer if row["source_arm"] == source and row["target_arm"] == target) for target in PRIMARY_ARMS]
            for source in PRIMARY_ARMS
        ],
        dtype=float,
    )
    matrix = np.asarray(matrix)
    fig, ax = plt.subplots(figsize=(7.2, 5.6), constrained_layout=True)
    image = ax.imshow(matrix, cmap="YlGnBu", vmin=0.32, vmax=0.43)
    ax.set_xticks(range(3), [ARM_LABELS[item] for item in PRIMARY_ARMS], rotation=20, ha="right")
    ax.set_yticks(range(3), [ARM_LABELS[item] for item in PRIMARY_ARMS])
    ax.set_xlabel("Target retriever adapter")
    ax.set_ylabel("Source winner program")
    ax.set_title("A3 transfer matrix: OUT Recall@100")
    for row in range(3):
        for column in range(3):
            ax.text(column, row, f"{matrix[row, column]:.3f}", ha="center", va="center", color="black")
    fig.colorbar(image, ax=ax, label="OUT Recall@100")
    fig.savefig(figure_dir / "a3-transfer-recall-heatmap-20260819.png", dpi=180)
    plt.close(fig)

    labels = [row["control"] for row in fixed]
    recall = [float(row["recall_at_100_out"]) for row in fixed]
    ndcg = [float(row["ndcg_at_100_out"]) for row in fixed]
    fig, ax = plt.subplots(figsize=(9.0, 5.6), constrained_layout=True)
    positions = np.arange(len(labels))
    width = 0.36
    ax.bar(positions - width / 2, recall, width, label="OUT Recall@100", color="#0F6CBD")
    ax.bar(positions + width / 2, ndcg, width, label="OUT NDCG@100", color="#2A6F4E")
    ax.set_xticks(positions, labels, rotation=25, ha="right")
    ax.set_ylim(0.25, 0.45)
    ax.set_ylabel("Aggregate score")
    ax.set_title("A3 fixed controls: quality comparison")
    ax.legend(frameon=False)
    fig.savefig(figure_dir / "a3-fixed-control-quality-20260819.png", dpi=180)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--report-root", type=Path, required=True)
    args = parser.parse_args()
    audit = json.loads(args.audit.read_text(encoding="ascii"))
    if audit.get("status") != "PASS_A3_RESULT_INTEGRITY_AUDIT":
        raise SystemExit("A3 result-integrity audit is not passing")
    transfer, fixed = _rows(audit)
    fields = ["operation_id", "source_arm", "target_arm", "recall_at_100_out", "ndcg_at_100_out", "ndcg_at_10_out", "wall_seconds", "search_p95_seconds", "expected_units", "completed_units"]
    _write_csv(args.report_root / "A3_transfer_matrix_eda_20260819.csv", transfer, fields)
    _write_csv(args.report_root / "A3_fixed_controls_eda_20260819.csv", fixed, ["operation_id", "control", *[field for field in fields if field not in {"operation_id", "source_arm", "target_arm"}]])
    _build_figures(transfer, fixed, args.report_root / "figures")
    print(json.dumps({"transfer_rows": len(transfer), "fixed_rows": len(fixed), "status": "PASS_A3_EDA_BUILD"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
