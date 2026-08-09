"""Render aggregate-safe EDA for the frozen dense-overflow compatibility plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ARM_LABELS = ["BM25", "BGE-M3", "PatEmbed", "Snowflake", "Qwen"]
ARM_IDS = ["ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05"]
PROGRAM_IDS = [
    "P00",
    "P01",
    "P02",
    "P03",
    "P04",
]
PROGRAM_KEYS = [
    "P00-TAC-DOC",
    "P01-TA-DOC",
    "P02-CLAIM1",
    "P03-PASSAGE",
    "P04-SECTION-MULTIVIEW",
]


def _incidence(audit: dict, arm_id: str, program_key: str, side: str) -> float | None:
    if arm_id == "ARM-01":
        return None
    value = audit["cells"][arm_id][program_key][side]["overflow_incidence"]
    return float(value) * 100.0


def render(audit_path: Path, png_path: Path, svg_path: Path) -> None:
    audit = json.loads(audit_path.read_text(encoding="ascii"))
    if audit.get("status") != "PASS" or audit.get("scientific_authority") is not False:
        raise ValueError("validated aggregate composition audit is required")
    if audit.get("requirements", {}).get("compatible_cells_25_of_25") is not True:
        raise ValueError("25/25 compatibility requirement is not bound")

    corpus = np.full((len(ARM_IDS), len(PROGRAM_IDS)), np.nan)
    for i, arm_id in enumerate(ARM_IDS):
        for j, program_key in enumerate(PROGRAM_KEYS):
            value = _incidence(audit, arm_id, program_key, "corpus")
            if value is not None:
                corpus[i, j] = value
    query_values = [
        _incidence(audit, arm_id, "P00-TAC-DOC", "rep_dev_queries")
        for arm_id in ARM_IDS
    ]

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titleweight": "bold",
    })
    fig = plt.figure(figsize=(13.2, 7.5), facecolor="white")
    grid = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.76], width_ratios=[1.65, 1.0], hspace=0.46, wspace=0.34)
    ax_heat = fig.add_subplot(grid[:, 0])
    ax_query = fig.add_subplot(grid[0, 1])
    ax_note = fig.add_subplot(grid[1, 1])

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "overflow", ["#F3F4F6", "#FDE68A", "#D55E00"]
    )
    image = ax_heat.imshow(corpus, cmap=cmap, vmin=0, vmax=max(100.0, float(np.nanmax(corpus))))
    ax_heat.set_xticks(range(len(PROGRAM_IDS)), PROGRAM_IDS)
    ax_heat.set_yticks(range(len(ARM_IDS)), ARM_LABELS)
    ax_heat.set_xlabel("Frozen logical program")
    ax_heat.set_ylabel("Frozen retrieval arm")
    ax_heat.set_title("A. Corpus overflow incidence", loc="left")
    ax_heat.set_xticks(np.arange(-0.5, len(PROGRAM_IDS), 1), minor=True)
    ax_heat.set_yticks(np.arange(-0.5, len(ARM_IDS), 1), minor=True)
    ax_heat.grid(which="minor", color="white", linewidth=1.5)
    ax_heat.tick_params(which="minor", bottom=False, left=False)
    for i, arm_id in enumerate(ARM_IDS):
        for j, program_key in enumerate(PROGRAM_KEYS):
            value = _incidence(audit, arm_id, program_key, "corpus")
            label = "N/A" if value is None else f"{value:.1f}%"
            color = "#111827" if value is None or value < 55 else "white"
            ax_heat.text(j, i, label, ha="center", va="center", color=color, fontweight="bold")
    colorbar = fig.colorbar(image, ax=ax_heat, fraction=0.045, pad=0.04)
    colorbar.set_label("Logical units requiring physical windows (%)")

    bars = ax_query.bar(ARM_LABELS, [value or 0.0 for value in query_values], color=["#9CA3AF", "#0072B2", "#D55E00", "#0072B2", "#0072B2"], width=0.62)
    ax_query.set_ylim(0, 105)
    ax_query.set_ylabel("REP-DEV P00 overflow (%)")
    ax_query.set_title("B. Query-side P00 incidence", loc="left")
    ax_query.grid(axis="y", color="#E5E7EB", linewidth=0.8)
    ax_query.set_axisbelow(True)
    ax_query.tick_params(axis="x", labelrotation=25)
    for bar, value in zip(bars, query_values, strict=True):
        if value is None:
            ax_query.text(bar.get_x() + bar.get_width() / 2, 5, "N/A", ha="center", va="bottom", color="#374151", fontweight="bold")
        else:
            ax_query.text(bar.get_x() + bar.get_width() / 2, value + 3, f"{value:.1f}%", ha="center", va="bottom", fontweight="bold")

    ax_note.axis("off")
    arm03_p00 = audit["cells"]["ARM-03"]["P00-TAC-DOC"]["corpus"]
    expansion = arm03_p00["physical_window_count"] / arm03_p00["logical_unit_count"]
    ax_note.text(0.0, 0.98, "Engineering reading", va="top", fontsize=12, fontweight="bold", color="#111827")
    ax_note.text(0.0, 0.80, f"PatEmbed P00: {arm03_p00['overflow_incidence'] * 100:.1f}% corpus overflow", va="top", color="#111827")
    ax_note.text(0.0, 0.64, f"Planned physical expansion: {expansion:.2f}x", va="top", color="#111827")
    ax_note.text(0.0, 0.48, "All source tokens represented once;\nzero overlap, drop, fallback, and truncation", va="top", color="#111827")
    ax_note.text(0.0, 0.24, "The audit plans windows only.\nProtected compiler integration is blocked;\nno vectors, retrieval, or publication result exists.", va="top", color="#9A3412", fontweight="bold")

    for axis in (ax_heat, ax_query):
        axis.spines[["top", "right"]].set_visible(False)
        axis.spines[["left", "bottom"]].set_color("#9CA3AF")
    fig.suptitle(
        "Frozen dense-overflow repair: compatibility evidence passes, compiler integration remains blocked",
        fontsize=16,
        fontweight="bold",
        y=0.985,
    )
    fig.text(
        0.5,
        0.012,
        f"Aggregate-only pre-measurement EDA. Source: {audit_path.as_posix()}. Audit {audit['audit_sha256'][:16]}. No retrieval or publication claim.",
        ha="center",
        color="#4B5563",
        fontsize=8.5,
    )
    png_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "Title": "A1.2 dense-overflow compatibility EDA",
        "Description": "Aggregate-safe overflow incidence and physical-window planning evidence.",
    }
    fig.savefig(png_path, dpi=220, facecolor="white", metadata=metadata, bbox_inches="tight")
    fig.savefig(svg_path, facecolor="white", metadata=metadata, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--png", type=Path, required=True)
    parser.add_argument("--svg", type=Path, required=True)
    args = parser.parse_args()
    render(args.audit, args.png, args.svg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
