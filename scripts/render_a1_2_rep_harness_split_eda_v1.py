"""Render aggregate-safe EDA for the frozen A1.2 Train-250 subdivision."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def render(audit_path: Path, png_path: Path, svg_path: Path) -> None:
    audit = json.loads(audit_path.read_text(encoding="ascii"))
    if audit.get("status") != "SPLIT_PASS_P02_BLOCKED" or audit.get("split", {}).get("status") != "PASS":
        raise ValueError("validated aggregate split audit is required")
    strata = audit["split"]["strata"]
    labels = [str(item["role_set"]) for item in strata]
    parent = [int(item["parent_count"]) for item in strata]
    rep = [int(item["rep_dev_count"]) for item in strata]
    harness = [int(item["harness_dev_count"]) for item in strata]
    if sum(parent) != 250 or sum(rep) != 150 or sum(harness) != 100:
        raise ValueError("split audit counts drifted")
    if {int(item["relevance_count"]) for item in strata} != {20}:
        raise ValueError("expected exact relevance-count 20 for every stratum")

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.titleweight": "bold"})
    fig, axes = plt.subplots(1, 2, figsize=(12, 6.5), gridspec_kw={"wspace": 0.30})
    fig.patch.set_facecolor("white")
    blue, vermillion, neutral = "#0072B2", "#D55E00", "#6B7280"

    axes[0].bar(labels, parent, color=neutral, width=0.62)
    axes[0].set_title("A. Train-250 composition")
    axes[0].set_ylabel("Queries")
    axes[0].set_ylim(0, 200)
    axes[0].grid(axis="y", color="#E5E7EB", linewidth=0.8)
    axes[0].set_axisbelow(True)
    for index, value in enumerate(parent):
        axes[0].text(index, value + 5, str(value), ha="center", va="bottom", fontweight="bold")
    axes[0].text(0.02, 0.96, "Exact positive relevance-count = 20\nfor every Train-250 query", transform=axes[0].transAxes, va="top", color="#374151")

    axes[1].bar(labels, rep, color=blue, width=0.62, label="REP-DEV")
    axes[1].bar(labels, harness, bottom=rep, color=vermillion, width=0.62, label="HARNESS-DEV")
    axes[1].set_title("B. Hamilton allocation reaches 150 / 100")
    axes[1].set_ylabel("Queries")
    axes[1].set_ylim(0, 200)
    axes[1].grid(axis="y", color="#E5E7EB", linewidth=0.8)
    axes[1].set_axisbelow(True)
    for index, (rep_value, harness_value) in enumerate(zip(rep, harness, strict=True)):
        if rep_value + harness_value < 15:
            axes[1].text(index, rep_value + harness_value + 5, f"REP {rep_value} / HAR {harness_value}", ha="center", va="bottom", color="#111827", fontweight="bold")
        else:
            axes[1].text(index, rep_value / 2, f"REP {rep_value}", ha="center", va="center", color="white", fontweight="bold")
            axes[1].text(index, rep_value + harness_value / 2, f"HAR {harness_value}", ha="center", va="center", color="white", fontweight="bold")
    axes[1].legend(loc="upper right", frameon=False)

    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
        axis.spines[["left", "bottom"]].set_color("#9CA3AF")
        axis.tick_params(axis="x", labelrotation=0)
    fig.suptitle("The pre-measurement split preserves frozen Train-250 strata", fontsize=16, fontweight="bold", y=0.98)
    fig.text(0.5, 0.925, "Role set x exact relevance-count strata; seed 42; no arbitrary bins", ha="center", color="#374151", fontsize=11)
    fig.text(0.01, 0.018, "Engineering EDA only. No retrieval result was inspected; no scientific or publication claim.", color="#4B5563", fontsize=9)
    fig.text(0.99, 0.018, f"Audit {audit['audit_sha256'][:16]}", ha="right", color="#6B7280", fontsize=8)
    fig.subplots_adjust(top=0.84, bottom=0.13, left=0.08, right=0.97)

    png_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {"Title": "A1.2 REP-DEV and HARNESS-DEV split EDA", "Description": "Aggregate-safe pre-measurement split counts only."}
    fig.savefig(png_path, dpi=200, facecolor="white", metadata=metadata)
    fig.savefig(svg_path, facecolor="white", metadata=metadata)
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
