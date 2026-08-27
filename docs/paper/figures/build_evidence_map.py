"""Render the compact evidence-lifecycle ribbon used in the paper overview."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

from paper_style import AMBER, BLUE, CORAL, FONT, INK, LINE, SLATE, WHITE

OUT = Path(__file__).resolve().parents[1] / "figures" / "rebuilt"


def rounded_rect(ax, x: float, y: float, width: float, height: float, color: str, **kwargs) -> None:
    ax.add_patch(FancyBboxPatch(
        (x, y), width, height, boxstyle="round,pad=0.002,rounding_size=0.012",
        facecolor=color, edgecolor="none", **kwargs
    ))


def icon(ax, kind: str, x: float, y: float, color: str) -> None:
    """Draw compact semantic glyphs; every glyph denotes its study stage."""
    if kind == "construct":
        for offset, width in ((0.030, 0.047), (0.000, 0.064), (-0.030, 0.047)):
            rounded_rect(ax, x - width / 2, y + offset - 0.009, width, 0.018, WHITE, zorder=5)
    elif kind == "transfer":
        ax.add_patch(FancyArrowPatch((x - 0.035, y - 0.025), (x + 0.035, y + 0.025), arrowstyle="-|>", mutation_scale=8, linewidth=1.3, color=WHITE, zorder=5))
        ax.add_patch(FancyArrowPatch((x - 0.035, y + 0.025), (x + 0.035, y - 0.025), arrowstyle="-|>", mutation_scale=8, linewidth=1.3, color=WHITE, zorder=5))
    elif kind == "freeze":
        rounded_rect(ax, x - 0.027, y - 0.030, 0.054, 0.042, WHITE, zorder=5)
        ax.add_patch(Arc((x, y + 0.012), 0.041, 0.051, theta1=0, theta2=180, color=WHITE, linewidth=1.3, zorder=6))
        ax.plot([x, x], [y - 0.015, y - 0.002], color=color, linewidth=1.2, zorder=7, solid_capstyle="round")
    else:
        ax.add_patch(Circle((x - 0.010, y + 0.010), 0.024, fill=False, edgecolor=WHITE, linewidth=1.35, zorder=5))
        ax.plot([x + 0.008, x + 0.035], [y - 0.008, y - 0.035], color=WHITE, linewidth=1.35, zorder=5, solid_capstyle="round")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": FONT, "svg.fonttype": "none", "pdf.fonttype": 42})
    fig, ax = plt.subplots(figsize=(7.16, 1.25), facecolor=WHITE)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    baseline_y = 0.47
    ax.add_patch(FancyArrowPatch((0.07, baseline_y), (0.47, baseline_y), arrowstyle="-|>", mutation_scale=11, linewidth=2.4, color=SLATE, zorder=1))
    ax.add_patch(FancyArrowPatch((0.53, baseline_y), (0.94, baseline_y), arrowstyle="-|>", mutation_scale=11, linewidth=2.4, color=BLUE, zorder=1))
    ax.plot([0.50, 0.50], [0.16, 0.83], color=INK, linewidth=1.2, zorder=2)
    rounded_rect(ax, 0.417, 0.835, 0.166, 0.104, WHITE, zorder=3)
    ax.text(0.50, 0.887, "DEVELOPMENT CLOSED", ha="center", va="center", color=INK, fontsize=7.8, fontweight="bold", zorder=4)
    ax.text(0.40, 0.760, "DEVELOPMENT", ha="right", va="center", color=SLATE, fontsize=7.1, fontweight="bold")
    ax.text(0.60, 0.760, "PROTECTED / POST-CONFIRMATORY", ha="left", va="center", color=BLUE, fontsize=7.1, fontweight="bold")

    stages = [
        (0.12, "01", "CONSTRUCT", "Representations + A1/A2", SLATE, "construct"),
        (0.36, "02", "TEST PORTABILITY", "A3 cross-retriever transfer", BLUE, "transfer"),
        (0.64, "03", "FREEZE & CONFIRM", "Selection-125 -> Final-872", AMBER, "freeze"),
        (0.88, "04", "DIAGNOSE", "Full benchmark -> A7", CORAL, "diagnose"),
    ]
    for x, number, title, detail, color, kind in stages:
        ax.add_patch(Circle((x, baseline_y), 0.082, facecolor=color, edgecolor=WHITE, linewidth=2.2, zorder=3))
        icon(ax, kind, x, baseline_y, color)
        ax.text(x, 0.617, number, ha="center", va="center", color=color, fontsize=7.1, fontweight="bold")
        ax.text(x, 0.690, title, ha="center", va="center", color=INK, fontsize=8.1, fontweight="bold")
        ax.text(x, 0.235, detail, ha="center", va="center", color=INK, fontsize=7.0)

    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    fig.savefig(OUT / "overview_evidence_map.svg", format="svg", facecolor=WHITE)
    fig.savefig(OUT / "overview_evidence_map.pdf", format="pdf", facecolor=WHITE)
    fig.savefig(OUT / "overview_evidence_map.png", format="png", dpi=360, facecolor=WHITE)


if __name__ == "__main__":
    main()
