"""Generate the template-guided paper figures from the canonical CSV pack.

The manuscript's data and evidence hierarchy are frozen. This script reads the
publication CSV pack, asserts every displayed value, and owns only the files in
``figures/rebuilt``.
"""
from __future__ import annotations

import csv
import io
import re
import zipfile
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.offsetbox import AnnotationBbox, DrawingArea
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle


PAPER = Path(__file__).resolve().parents[3]
ARCHIVE = PAPER / "prism-uploads" / "myIS_prism_csv_pack_20260826.zip"
PREFIX = "myIS_prism_csv_pack_20260826/prism_ready/"
THEME_FILE = PAPER / "figures" / "template" / "theme.md"
OUT = Path(__file__).resolve().parents[1]

FONT = "Arial"
SOURCES = ("PatEmbed", "Arctic Embed", "Qwen3 Embedding")
TARGETS = SOURCES
SHORT = {"PatEmbed": "PatEmbed", "Arctic Embed": "Arctic", "Qwen3 Embedding": "Qwen3"}
MARKERS = {"PatEmbed": "o", "Arctic Embed": "s", "Qwen3 Embedding": "D"}


def load_theme() -> dict[str, str]:
    text = THEME_FILE.read_text(encoding="utf-8")
    colors = dict(re.findall(r"(?:^|\n)-?\s*(Navy|Blue|Teal|Amber|Coral|SlateDark|Slate|Grid|White)\s+(#[0-9A-Fa-f]{6})", text))
    expected = {"Navy", "Blue", "Teal", "Amber", "Coral", "Slate", "SlateDark", "Grid", "White"}
    assert set(colors) == expected, f"theme.md color roles changed: {sorted(colors)}"
    return colors


COLORS = load_theme()
INK = COLORS["Navy"]
BLUE = COLORS["Blue"]
TEAL = COLORS["Teal"]
AMBER = COLORS["Amber"]
CORAL = COLORS["Coral"]
SLATE = COLORS["Slate"]
SLATE_DARK = COLORS["SlateDark"]
GRID = COLORS["Grid"]
WHITE = COLORS["White"]


def rows(member: str) -> list[dict[str, str]]:
    with zipfile.ZipFile(ARCHIVE) as archive:
        payload = archive.read(PREFIX + member).decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(payload)))


def load_and_assert() -> tuple[dict[tuple[str, str], float], dict[str, dict[str, float]], dict[str, float]]:
    transfer = {
        (row["representation_source"], row["target_retriever"]): float(row["Recall@100"])
        for row in rows("fig1_a3_transfer.csv")
    }
    expected_transfer = {
        ("PatEmbed", "PatEmbed"): 0.418435754190,
        ("PatEmbed", "Arctic Embed"): 0.337430167598,
        ("PatEmbed", "Qwen3 Embedding"): 0.362569832402,
        ("Arctic Embed", "PatEmbed"): 0.418715083799,
        ("Arctic Embed", "Arctic Embed"): 0.341340782123,
        ("Arctic Embed", "Qwen3 Embedding"): 0.359497206704,
        ("Qwen3 Embedding", "PatEmbed"): 0.419273743017,
        ("Qwen3 Embedding", "Arctic Embed"): 0.338268156425,
        ("Qwen3 Embedding", "Qwen3 Embedding"): 0.360614525140,
    }
    assert transfer == expected_transfer, "A3 canonical matrix drift"

    confirmation: dict[str, dict[str, float]] = {}
    for row in rows("fig2_a5_confirmation.csv"):
        if row["metric"] not in ("Recall@100", "nDCG@100"):
            continue
        confirmation[row["metric"]] = {
            key: float(row[key])
            for key in ("static_comparator", "selected_research", "paired_difference", "ci95_low", "ci95_high")
        }
    assert confirmation == {
        "Recall@100": {
            "static_comparator": 0.331097,
            "selected_research": 0.442476,
            "paired_difference": 0.111379,
            "ci95_low": 0.102294,
            "ci95_high": 0.120438,
        },
        "nDCG@100": {
            "static_comparator": 0.279253,
            "selected_research": 0.365595,
            "paired_difference": 0.086342,
            "ci95_low": 0.078673,
            "ci95_high": 0.094077,
        },
    }, "A5 canonical confirmation drift"

    audit: dict[str, float] = {}
    for row in rows("fig2_a5_recall_wtl.csv"):
        audit[f"wtl_{row['outcome']}"] = int(row["count"])
    for row in rows("fig3_a7_out_diagnosis.csv"):
        audit[row["state"]] = float(row["value"])

    assert {key: audit[key] for key in ("wtl_win", "wtl_tie", "wtl_loss")} == {
        "wtl_win": 619,
        "wtl_tie": 158,
        "wtl_loss": 95,
    }, "A5 W/T/L drift"
    expected_a7 = {
        "exposed_by_rank_100": 796,
        "first_exposed_rank_101_200": 332,
        "absent_at_rank_200": 4065,
        "observed_Recall@100": 0.188449898653,
        "fixed_pool_oracle_Recall@100": 0.260166940437,
        "bounded_ordering_headroom_Recall@100": 0.071717041784,
    }
    for key, expected in expected_a7.items():
        assert audit[key] == expected, f"A7 canonical drift: {key}"
    assert audit["exposed_by_rank_100"] + audit["first_exposed_rank_101_200"] + audit["absent_at_rank_200"] == 5193
    return transfer, confirmation, audit


def style() -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": [FONT, "Liberation Sans", "DejaVu Sans"],
        "font.size": 7.2,
        "axes.labelcolor": INK,
        "axes.edgecolor": SLATE_DARK,
        "axes.linewidth": 0.7,
        "xtick.color": SLATE_DARK,
        "ytick.color": INK,
        "text.color": INK,
        "figure.facecolor": WHITE,
        "axes.facecolor": WHITE,
        "savefig.facecolor": WHITE,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })


def panel_heading(
    ax: plt.Axes,
    letter: str,
    title: str,
    color: str = INK,
    x: float = 0.0,
    title_size: float = 8.4,
) -> None:
    ax.text(x, 1.08, letter, transform=ax.transAxes, ha="left", va="center", fontsize=7.3,
            color=WHITE, fontweight="bold",
            bbox={"boxstyle": "circle,pad=0.25", "facecolor": color, "edgecolor": "none"})
    ax.text(x + 0.105, 1.08, title, transform=ax.transAxes, ha="left", va="center",
            fontsize=title_size, color=INK, fontweight="bold")


def export(fig: plt.Figure, stem: str) -> None:
    metadata = {"Creator": "myIS template-guided figure generator", "Title": stem}
    fig.savefig(OUT / f"{stem}.pdf", metadata=metadata)
    svg_path = OUT / f"{stem}.svg"
    fig.savefig(svg_path, metadata=metadata)
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_path.write_text("\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n", encoding="utf-8")
    fig.savefig(OUT / f"{stem}.png", dpi=360, metadata=metadata)
    plt.close(fig)


def figure1(transfer: dict[tuple[str, str], float]) -> None:
    """A3 transfer as three compact target-specific dot panels."""
    style()
    fig, axes = plt.subplots(1, 3, figsize=(7.16, 2.33), sharey=True)
    fig.subplots_adjust(left=0.16, right=0.975, top=0.67, bottom=0.30, wspace=0.30)
    limits = {
        "PatEmbed": (0.4175, 0.4205, [0.4175, 0.4185, 0.4195, 0.4205]),
        "Arctic Embed": (0.334, 0.344, [0.334, 0.338, 0.342]),
        "Qwen3 Embedding": (0.357, 0.365, [0.357, 0.361, 0.365]),
    }
    y_positions = {source: 2 - i for i, source in enumerate(SOURCES)}
    for index, (ax, target) in enumerate(zip(axes, TARGETS)):
        values = {source: transfer[(source, target)] for source in SOURCES}
        best_source = max(values, key=values.get)
        lo, hi, ticks = limits[target]
        for source in SOURCES:
            y = y_positions[source]
            value = values[source]
            ax.hlines(y, lo, hi, color=GRID, lw=0.8, zorder=0)
            face = AMBER if source == best_source else BLUE
            ax.scatter(value, y, marker=MARKERS[source], s=47, color=face,
                       edgecolor=WHITE, linewidth=0.8, zorder=3)
            if source == target:
                ax.scatter(value, y, marker=MARKERS[source], s=94, facecolors="none",
                           edgecolors=INK, linewidth=1.0, zorder=4)
            text_color = AMBER if source == best_source else INK
            place_left = value > lo + 0.72 * (hi - lo)
            ax.annotate(f"{value:.6f}", (value, y), xytext=(-8 if place_left else 8, 0),
                        textcoords="offset points", ha="right" if place_left else "left",
                        va="center", fontsize=6.7, color=text_color,
                        fontweight="bold" if source == best_source else "normal")
        score_range = max(values.values()) - min(values.values())
        ax.set_title(f"{SHORT[target]} target", fontsize=8.5, color=INK, fontweight="bold", pad=19)
        ax.text(0.5, 1.05, f"within-target range {score_range:.6f}", transform=ax.transAxes,
                ha="center", va="bottom", fontsize=6.4, color=SLATE_DARK)
        ax.set_xlim(lo, hi)
        ax.set_xticks(ticks)
        ax.tick_params(axis="x", labelsize=6.4, length=2.7, pad=2)
        ax.set_ylim(-0.55, 2.55)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color(SLATE_DARK)
        ax.set_xlabel("Recall@100", fontsize=6.7, labelpad=3)
        if index == 0:
            ax.set_yticks([2, 1, 0], ["PatEmbed-derived", "Arctic-derived", "Qwen3-derived"])
            ax.tick_params(axis="y", length=0, pad=7, labelsize=7.0)
        else:
            ax.tick_params(axis="y", length=0, labelleft=False)

    fig.text(0.16, 0.94, "A3 representation transfer", fontsize=9.2, color=INK, fontweight="bold")
    fig.text(0.16, 0.855,
             "Nominal source rankings change across consuming retrievers; absolute target bands remain distinct.",
             fontsize=7.0, color=SLATE_DARK)
    handles = [
        Line2D([0], [0], marker=MARKERS[source], color="none", markerfacecolor=BLUE,
               markeredgecolor=WHITE, markersize=5.5, label=f"{SHORT[source]} source")
        for source in SOURCES
    ]
    handles.extend([
        Line2D([0], [0], marker="o", color="none", markerfacecolor="none", markeredgecolor=INK,
               markersize=7.2, label="Matched pair"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=AMBER, markeredgecolor=WHITE,
               markersize=6.0, label="Nominal best"),
    ])
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.58, 0.115), ncol=5,
               frameon=False, columnspacing=1.35, handletextpad=0.4, fontsize=6.4)
    fig.text(0.16, 0.045,
             "Local target axes support within-target reading; direct labels and ranges prevent effect-size overstatement. Descriptive development evidence.",
             fontsize=6.25, color=SLATE_DARK)
    export(fig, "fig1_a3_transfer")


def figure2(confirmation: dict[str, dict[str, float]], audit: dict[str, float]) -> None:
    """A5 confirmation as absolute, paired-effect, and outcome panels."""
    style()
    fig = plt.figure(figsize=(7.16, 2.28))
    gs = fig.add_gridspec(1, 3, width_ratios=(1.02, 1.10, 1.14), left=0.11, right=0.985,
                          top=0.68, bottom=0.20, wspace=0.34)
    absolute, effect, wtl = (fig.add_subplot(gs[0, i]) for i in range(3))
    metrics = ("Recall@100", "nDCG@100")
    ys = (1, 0)

    for metric, y in zip(metrics, ys):
        values = confirmation[metric]
        start = values["static_comparator"]
        end = values["selected_research"]
        absolute.plot([start, end], [y, y], color=SLATE, lw=1.8, solid_capstyle="round", zorder=1)
        absolute.scatter(start, y, s=40, color=SLATE_DARK, edgecolor=WHITE, linewidth=0.7, zorder=3)
        absolute.scatter(end, y, s=47, color=BLUE, edgecolor=WHITE, linewidth=0.7, zorder=3)
        absolute.text(start, y - 0.23, f"{start:.6f}", ha="center", fontsize=6.45, color=SLATE_DARK)
        absolute.text(end, y + 0.20, f"{end:.6f}", ha="center", fontsize=6.65,
                      color=BLUE, fontweight="bold")

        lo, hi, point = values["ci95_low"], values["ci95_high"], values["paired_difference"]
        effect.hlines(y, lo, hi, color=BLUE, lw=2.4, zorder=1)
        effect.vlines([lo, hi], y - 0.11, y + 0.11, color=BLUE, lw=1.05)
        effect.scatter(point, y, s=55 if metric == "Recall@100" else 46, color=BLUE,
                       edgecolor=WHITE, linewidth=0.7, zorder=3)
        effect.text(0.146, y + 0.12, f"+{point:.6f}", ha="right", va="bottom",
                    fontsize=8.2 if metric == "Recall@100" else 7.1, color=BLUE, fontweight="bold")
        effect.text(0.146, y - 0.20, f"95% CI [{lo:.6f}, {hi:.6f}]", ha="right", va="top",
                    fontsize=6.0, color=SLATE_DARK)

    absolute.set_xlim(0.25, 0.47)
    absolute.set_ylim(-0.45, 1.45)
    absolute.set_xticks([0.28, 0.36, 0.44])
    absolute.set_yticks(ys, metrics)
    absolute.set_xlabel("Absolute score", fontsize=6.7, labelpad=3)
    absolute.grid(axis="x", color=GRID, lw=0.65)
    absolute.set_axisbelow(True)
    absolute.spines[["top", "right", "left"]].set_visible(False)
    absolute.tick_params(axis="y", length=0, pad=4, labelsize=6.8)
    absolute.tick_params(axis="x", labelsize=6.3, length=2.5)
    panel_heading(absolute, "A", "Absolute performance", BLUE)

    effect.axvline(0, color=SLATE_DARK, lw=0.75)
    effect.set_xlim(0, 0.15)
    effect.set_ylim(-0.45, 1.45)
    effect.set_xticks([0, 0.05, 0.10, 0.15])
    effect.set_yticks(ys, metrics)
    effect.set_xlabel("Selected - comparator", fontsize=6.7, labelpad=3)
    effect.grid(axis="x", color=GRID, lw=0.65)
    effect.set_axisbelow(True)
    effect.spines[["top", "right", "left"]].set_visible(False)
    effect.tick_params(axis="y", length=0, pad=4, labelsize=6.8)
    effect.tick_params(axis="x", labelsize=6.3, length=2.5)
    panel_heading(effect, "B", "Paired effects + 95% CI", BLUE)

    counts = [("Win", int(audit["wtl_win"]), BLUE), ("Tie", int(audit["wtl_tie"]), SLATE_DARK),
              ("Loss", int(audit["wtl_loss"]), CORAL)]
    total = sum(count for _, count, _ in counts)
    start = 0
    for name, count, color in counts:
        width = count / total
        wtl.add_patch(Rectangle((start, 0.33), width, 0.34, facecolor=color, edgecolor=WHITE, linewidth=0.8))
        inside = f"{count}\n{100 * width:.1f}%" if name != "Loss" else f"{count}"
        wtl.text(start + width / 2, 0.50, inside, ha="center", va="center",
                 fontsize=6.7 if name != "Loss" else 6.4, color=WHITE, fontweight="bold")
        if name == "Loss":
            wtl.text(start + width / 2, 0.24, f"{100 * width:.1f}%", ha="center", va="top",
                     fontsize=6.0, color=CORAL, fontweight="bold")
        wtl.text(start + width / 2, 0.77, name, ha="center", va="center", fontsize=6.65,
                 color=color, fontweight="bold")
        start += width
    wtl.add_patch(FancyBboxPatch((0, 0.33), 1, 0.34, boxstyle="round,pad=0,rounding_size=0.025",
                                 facecolor="none", edgecolor=INK, linewidth=0.65))
    wtl.set_xlim(0, 1)
    wtl.set_ylim(0, 1)
    wtl.set_xticks([0, 0.5, 1], ["0%", "50%", "100%"])
    wtl.set_yticks([])
    wtl.spines[["top", "right", "left"]].set_visible(False)
    wtl.tick_params(axis="x", labelsize=6.3, length=2.5)
    panel_heading(wtl, "C", "Recall W / T / L", BLUE)
    wtl.text(1.0, 1.08, "n = 872", transform=wtl.transAxes, ha="right", va="center",
             fontsize=6.4, color=SLATE_DARK)

    fig.text(0.11, 0.91, "Final-872 complete-system confirmation", fontsize=9.2, color=INK, fontweight="bold")
    legend_handles = [
        Line2D([0], [0], marker="o", color=SLATE_DARK, markerfacecolor=SLATE_DARK, markersize=4.4,
               lw=1.0, label="Comparator"),
        Line2D([0], [0], marker="o", color=BLUE, markerfacecolor=BLUE, markersize=4.4,
               lw=1.0, label="Selected complete system"),
    ]
    fig.legend(handles=legend_handles, loc="upper left", bbox_to_anchor=(0.105, 0.83), ncol=2,
               frameon=False, handlelength=1.6, handletextpad=0.45, columnspacing=1.25, fontsize=6.5)
    fig.text(0.11, 0.055, "Protected comparison of two frozen complete configurations; not a representation-only causal effect.",
             fontsize=6.3, color=SLATE_DARK)
    export(fig, "fig2_a5_confirmation")


def figure3(audit: dict[str, float]) -> None:
    """A7 fixed-pool diagnosis with separate incidence and macro-recall panels."""
    style()
    fig = plt.figure(figsize=(7.16, 2.18))
    gs = fig.add_gridspec(1, 2, width_ratios=(1.16, 1.0), left=0.07, right=0.985,
                          top=0.72, bottom=0.20, wspace=0.28)
    exposure, bound = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])

    total = 5193
    parts = [
        ("By rank 100", int(audit["exposed_by_rank_100"]), BLUE),
        ("First at 101-200", int(audit["first_exposed_rank_101_200"]), AMBER),
        ("Absent from Top-200", int(audit["absent_at_rank_200"]), CORAL),
    ]
    start = 0
    centers: list[tuple[str, int, str, float]] = []
    for label, count, color in parts:
        width = count / total
        exposure.add_patch(Rectangle((start, 0.46), width, 0.28, facecolor=color,
                                     edgecolor=WHITE, linewidth=0.8))
        centers.append((label, count, color, start + width / 2))
        start += width
    exposure.add_patch(FancyBboxPatch((0, 0.46), 1, 0.28, boxstyle="round,pad=0,rounding_size=0.02",
                                      facecolor="none", edgecolor=INK, linewidth=0.65))
    for label, count, color, center in centers:
        percent = 100 * count / total
        if label == "Absent from Top-200":
            exposure.text(center, 0.60, "4,065 / 5,193 absent", ha="center", va="center",
                          fontsize=8.0, color=WHITE, fontweight="bold")
            exposure.text(1.0, 0.24, f"Absent from Top-200\n{count:,} ({percent:.1f}%)", ha="right", va="top",
                          fontsize=6.6, color=CORAL, fontweight="bold")
        elif label == "By rank 100":
            exposure.text(0.0, 0.24, f"By rank 100\n{count:,} ({percent:.1f}%)", ha="left", va="top",
                          fontsize=6.4, color=color, fontweight="bold")
        else:
            exposure.text(0.36, 0.24, f"First at 101-200\n{count:,} ({percent:.1f}%)", ha="center", va="top",
                          fontsize=6.0, color=color, fontweight="bold")
    exposure.set_xlim(0, 1)
    exposure.set_ylim(0, 1)
    exposure.axis("off")
    panel_heading(exposure, "A", "Exposure anatomy", CORAL)
    exposure.text(0.0, 0.93, "5,193 relevant-family incidences", transform=exposure.transAxes,
                  fontsize=6.7, color=SLATE_DARK)

    observed = audit["observed_Recall@100"]
    oracle = audit["fixed_pool_oracle_Recall@100"]
    headroom = audit["bounded_ordering_headroom_Recall@100"]
    y = 0.51
    bound.plot([observed, oracle], [y, y], color=SLATE, lw=2.2, solid_capstyle="round", zorder=1)
    bound.scatter(observed, y, s=56, color=BLUE, edgecolor=WHITE, linewidth=0.7, zorder=3)
    bound.scatter(oracle, y, s=56, color=AMBER, edgecolor=WHITE, linewidth=0.7, zorder=3)
    bound.text(observed, y + 0.18, f"Observed\n{observed:.6f}", ha="left", va="bottom",
               fontsize=7.0, color=BLUE, fontweight="bold")
    bound.text(oracle, y + 0.18, f"Perfect-ordering bound\n{oracle:.6f}", ha="right", va="bottom",
               fontsize=6.8, color=AMBER, fontweight="bold")
    bound.annotate(f"+{headroom:.6f} headroom", xy=((observed + oracle) / 2, y),
                   xytext=((observed + oracle) / 2, y - 0.25), ha="center", va="center",
                   fontsize=7.4, color=INK, fontweight="bold",
                   arrowprops={"arrowstyle": "-[,widthB=3.2,lengthB=0.4", "lw": 0.8, "color": SLATE_DARK})
    bound.set_xlim(0.175, 0.274)
    bound.set_ylim(0.02, 1.0)
    bound.set_xticks([0.18, 0.22, 0.26])
    bound.set_yticks([])
    bound.set_xlabel("Macro Recall@100 across 905 queries", fontsize=6.7, labelpad=3)
    bound.grid(axis="x", color=GRID, lw=0.65)
    bound.set_axisbelow(True)
    bound.spines[["top", "right", "left"]].set_visible(False)
    bound.tick_params(axis="x", labelsize=6.3, length=2.5)
    panel_heading(bound, "B", "Within-pool ordering bound", AMBER, title_size=7.7)
    bound.text(0.0, 0.93, "Immutable Top-200 pool", transform=bound.transAxes,
               fontsize=6.7, color=SLATE_DARK)

    fig.text(0.07, 0.91, "A7 candidate-exposure diagnosis", fontsize=9.2, color=INK, fontweight="bold")
    fig.text(0.07, 0.835,
             "Incidence exposure and macro Recall are separate units; the bound is analytical, not reranker performance.",
             fontsize=6.8, color=SLATE_DARK)
    fig.text(0.07, 0.055, "Post-confirmatory analysis of the fixed full-benchmark candidate pool.",
             fontsize=6.3, color=SLATE_DARK)
    export(fig, "fig3_a7_diagnosis")


def milestone_icon(ax: plt.Axes, x: float, y: float, color: str, kind: str) -> None:
    """Add a fixed-size vector icon so wide axes cannot distort its geometry."""
    area = DrawingArea(46, 46, 0, 0)
    area.add_artist(Circle((23, 23), 21, facecolor=WHITE, edgecolor=color, linewidth=1.3))
    if kind == "document":
        area.add_artist(FancyBboxPatch((14, 11), 18, 25, boxstyle="round,pad=0.8,rounding_size=2.2",
                                       fill=False, edgecolor=color, linewidth=1.15))
        area.add_artist(Polygon([[26, 36], [32, 30], [26, 30]], fill=False,
                                edgecolor=color, linewidth=0.9))
        for yy in (18, 23, 28):
            area.add_artist(Line2D([18, 28], [yy, yy], color=color, lw=0.9, solid_capstyle="round"))
    elif kind == "transfer":
        for start, end, rad in [((11, 15), (35, 31), 0.18), ((11, 31), (35, 15), -0.18)]:
            area.add_artist(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=7,
                                            connectionstyle=f"arc3,rad={rad}", color=color, linewidth=1.05))
    elif kind == "shield":
        area.add_artist(Polygon([(23, 36), (34, 30), (32, 17), (23, 9), (14, 17), (12, 30)],
                                fill=False, edgecolor=color, linewidth=1.15, joinstyle="round"))
        area.add_artist(Line2D([17, 22, 30], [23, 17, 28], color=color, lw=1.3, solid_capstyle="round"))
    else:
        area.add_artist(Circle((21, 25), 11, fill=False, edgecolor=color, linewidth=1.15))
        area.add_artist(Line2D([29, 38], [17, 8], color=color, lw=1.3, solid_capstyle="round"))
        for xx, height in ((16, 6), (21, 10), (26, 15)):
            area.add_artist(Rectangle((xx, 19), 3, height, fill=False, edgecolor=color, linewidth=0.75))
    ax.add_artist(AnnotationBbox(area, (x, y), xycoords=ax.transAxes, frameon=False,
                                box_alignment=(0.5, 0.5), pad=0))


def overview() -> None:
    """Four-stage evidence map with an explicit protected-evaluation boundary."""
    style()
    fig, ax = plt.subplots(figsize=(7.16, 1.43))
    fig.subplots_adjust(left=0.025, right=0.985, top=0.95, bottom=0.08)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    stages = [
        (0.11, "01", "CONSTRUCT", "Representations; A1/A2", INK, "document"),
        (0.36, "02", "TEST PORTABILITY", "A3 cross-retriever transfer", BLUE, "transfer"),
        (0.64, "03", "FREEZE & CONFIRM", "Selection-125  >  Final-872", TEAL, "shield"),
        (0.89, "04", "DIAGNOSE", "Full benchmark  >  A7", CORAL, "diagnose"),
    ]
    y = 0.55
    for (x0, *_), (x1, *__) in zip(stages[:-1], stages[1:]):
        color = SLATE_DARK if x1 <= 0.5 else TEAL
        ax.add_patch(FancyArrowPatch((x0 + 0.055, y), (x1 - 0.055, y), arrowstyle="-|>",
                                     mutation_scale=7, color=color, linewidth=1.0))

    for x, number, title, detail, color, icon_kind in stages:
        milestone_icon(ax, x, y, color, icon_kind)
        ax.text(x, 0.81, number, ha="center", va="center", fontsize=7.0, color=color, fontweight="bold")
        ax.text(x, 0.25, title, ha="center", va="center", fontsize=7.45, color=color, fontweight="bold")
        ax.text(x, 0.145, detail, ha="center", va="center", fontsize=6.35, color=INK)

    ax.plot([0.065, 0.405], [0.93, 0.93], color=SLATE_DARK, lw=0.85)
    ax.plot([0.065, 0.065], [0.93, 0.86], color=SLATE_DARK, lw=0.85)
    ax.plot([0.405, 0.405], [0.93, 0.86], color=SLATE_DARK, lw=0.85)
    ax.text(0.235, 0.945, "DEVELOPMENT EVIDENCE", ha="center", va="bottom", fontsize=6.25,
            color=SLATE_DARK, fontweight="bold")
    ax.plot([0.595, 0.685], [0.93, 0.93], color=TEAL, lw=0.85)
    ax.text(0.64, 0.945, "PROTECTED CONFIRMATION", ha="center", va="bottom", fontsize=6.25,
            color=TEAL, fontweight="bold")
    ax.plot([0.835, 0.945], [0.93, 0.93], color=CORAL, lw=0.85)
    ax.text(0.89, 0.945, "POST-CONFIRMATORY", ha="center", va="bottom", fontsize=6.25,
            color=CORAL, fontweight="bold")

    ax.plot([0.5, 0.5], [0.08, 0.95], color=INK, lw=0.8, linestyle=(0, (3, 3)))
    ax.text(0.5, 0.835, "DEVELOPMENT CLOSED", ha="center", va="center", fontsize=6.0,
            color=INK, fontweight="bold",
            bbox={"boxstyle": "round,pad=0.22,rounding_size=0.12", "facecolor": WHITE,
                  "edgecolor": INK, "linewidth": 0.65})
    ax.text(0.5, 0.015, "PROTECTED EVALUATION", ha="center", va="center", fontsize=5.9,
            color=TEAL, fontweight="bold")
    export(fig, "overview_evidence_map")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    transfer, confirmation, audit = load_and_assert()
    overview()
    figure1(transfer)
    figure2(confirmation, audit)
    figure3(audit)
    print("rebuilt figures generated after canonical A3/A5/A7 assertions passed")


if __name__ == "__main__":
    main()
