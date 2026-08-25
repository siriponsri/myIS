"""Build aggregate-safe artwork for the RCRS WPI V0.7 manuscript.

No benchmark records are read. Every plotted value comes from the aggregate
ledger in ../data/aggregate_ledger.json, whose sources are listed in
../data/DATA_PROVENANCE.md. Vector PDF is the submission master; 600 dpi PNG
is supplied for inspection.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"
OUT.mkdir(parents=True, exist_ok=True)
LEDGER = json.loads((ROOT / "data" / "aggregate_ledger.json").read_text(encoding="utf-8"))

# Shape and line style carry the same distinctions as color, so the artwork
# remains legible in grayscale.
INK = "#202124"
BLUE = "#315B7D"
BLUE_LIGHT = "#DDE8EF"
ORANGE = "#B85C38"
ORANGE_LIGHT = "#F1E1DA"
TEAL = "#2F7F78"
GREY = "#747B82"
MID = "#A8AEB4"
LIGHT = "#E4E7E9"
PALE = "#F5F6F7"
WHITE = "#FFFFFF"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 8.0,
        "axes.titlesize": 8.6,
        "axes.titleweight": "bold",
        "axes.labelsize": 8.0,
        "legend.fontsize": 7.0,
        "xtick.labelsize": 7.2,
        "ytick.labelsize": 7.2,
        "axes.edgecolor": INK,
        "axes.linewidth": 0.65,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": WHITE,
        "axes.facecolor": WHITE,
        "savefig.facecolor": WHITE,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


def save(fig, stem):
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight", pad_inches=0.025)
    fig.savefig(
        OUT / f"{stem}.png",
        dpi=600,
        bbox_inches="tight",
        pad_inches=0.025,
    )
    plt.close(fig)


def title(ax, label, text):
    ax.set_title(rf"$\bf{{{label}}}$  {text}", loc="left", pad=6, color=INK)


def grid(ax, axis="y"):
    ax.grid(axis=axis, color=LIGHT, linewidth=0.6)
    ax.set_axisbelow(True)


def arrow(ax, x0, y0, x1, y1, color=GREY, width=0.9):
    ax.add_patch(
        FancyArrowPatch(
            (x0, y0),
            (x1, y1),
            arrowstyle="-|>",
            mutation_scale=8,
            linewidth=width,
            color=color,
            shrinkA=0,
            shrinkB=0,
        )
    )


def fig1_protocol():
    """Method and study order as a plain scientific schematic."""
    fig, ax = plt.subplots(figsize=(7.15, 2.70))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.015, 0.965, r"$\bf{A}$  Representation evaluated for one frozen retriever", va="top", fontsize=8.8, color=INK)
    ax.plot([0.015, 0.985], [0.895, 0.895], color=INK, linewidth=0.65)

    nodes = [
        (0.07, "Patent-family record", "title | abstract | claims", INK),
        (0.29, "Representation program $p$", "fields | segments | packing", ORANGE),
        (0.51, "Frozen retriever $a$", "weights/scoring frozen;\nindex rebuilt", BLUE),
        (0.72, "Family aggregation", "max | top-$k$ mean | RRF", INK),
        (0.92, "Ranked families", "Top-$k$ candidates", INK),
    ]
    for x, head, body, color in nodes:
        ax.plot(x, 0.695, marker="o", markersize=3.8, color=color, zorder=3)
        ax.text(x, 0.805, head, ha="center", va="top", fontsize=6.8, color=color, weight="bold" if color != INK else "normal")
        ax.text(x, 0.625, body, ha="center", va="top", fontsize=5.9, color=GREY)
    for x0, x1 in zip([0.085, 0.305, 0.525, 0.735], [0.275, 0.495, 0.705, 0.905]):
        arrow(ax, x0, 0.695, x1, 0.695, color=MID, width=0.75)

    ax.text(0.015, 0.505, r"$\bf{B}$  Study order and permitted inference", va="top", fontsize=8.8, color=INK)
    ax.plot([0.015, 0.985], [0.435, 0.435], color=INK, linewidth=0.65)
    arrow(ax, 0.05, 0.265, 0.96, 0.265, color=MID, width=0.85)
    stages = [
        (0.19, "Development", "common screen | per-retriever search\ntransfer | fixed controls", BLUE),
        (0.51, "Selection-125", "one exposure\ncomparator already fixed", GREY),
        (0.69, "Final-872", "two frozen systems", ORANGE),
        (0.90, "Post-confirmatory", "depth run\nexposure diagnosis", TEAL),
    ]
    for x, head, body, color in stages:
        ax.plot(x, 0.265, marker="o", markersize=4.2, color=color, zorder=3)
        ax.text(x, 0.365, head, ha="center", va="top", fontsize=6.9, color=color, weight="bold")
        ax.text(x, 0.205, body, ha="center", va="top", fontsize=6.0, color=INK, linespacing=1.18)
    ax.text(0.50, 0.035, "The operational comparator was fixed before Selection; later analyses use the unchanged winner.", ha="center", va="bottom", fontsize=6.3, color=GREY, style="italic")
    save(fig, "fig1_rcrs_protocol")


def fig2_transfer():
    development = LEDGER["development"]
    transfer = np.array(development["transfer_recall_at_100"]["values"])
    controls = development["fixed_controls"]["rows"]
    fig, (ax1, ax2) = plt.subplots(
        1,
        2,
        figsize=(7.15, 3.12),
        gridspec_kw={"width_ratios": [0.94, 1.50], "wspace": 0.42},
    )

    # Target-wise normalization makes within-target transfer visible without
    # implying that scores from different target retrievers share a baseline.
    norm = (transfer - transfer.min(axis=0)) / (transfer.max(axis=0) - transfer.min(axis=0))
    cmap = plt.get_cmap("Blues")
    for i in range(3):
        for j in range(3):
            ax1.add_patch(
                Rectangle(
                    (j - 0.5, i - 0.5),
                    1,
                    1,
                    facecolor=cmap(norm[i, j]),
                    edgecolor=WHITE,
                    linewidth=0.5,
                )
            )
            ax1.text(
                j,
                i,
                f"{transfer[i, j]:.4f}",
                ha="center",
                va="center",
                fontsize=7.5,
                color=WHITE if norm[i, j] > 0.60 else INK,
                weight="bold" if norm[i, j] == 1 else "normal",
            )
    ax1.set_xlim(-0.5, 2.5)
    ax1.set_ylim(2.5, -0.5)
    ax1.set_aspect("equal")
    ax1.set_xticks(range(3), ["PatEmbed", "Arctic", "Qwen3"])
    ax1.set_yticks(range(3), ["PatEmbed", "Arctic", "Qwen3"])
    ax1.set_xlabel("Frozen target retriever")
    ax1.set_ylabel("Program source")
    title(ax1, "A", "Cross-retriever transfer")
    for spine in ax1.spines.values():
        spine.set_visible(False)
    ax1.tick_params(length=0)
    ax1.text(0.0, -0.29, "Color scale normalized separately by target", transform=ax1.transAxes, fontsize=6.5, color=GREY)

    labels = list(controls)
    vals = np.array(list(controls.values()))
    y = np.arange(len(labels))
    series = [
        ("Recall@100", BLUE, "o", -0.15),
        ("nDCG@100", ORANGE, "s", 0.0),
        ("nDCG@10", TEAL, "^", 0.15),
    ]
    for k, (name, color, marker, offset) in enumerate(series):
        ax2.scatter(vals[:, k], y + offset, s=30, color=color, marker=marker, label=name, zorder=3)
        for row, value in enumerate(vals[:, k]):
            ax2.text(value + 0.004, row + offset, f"{value:.3f}", va="center", fontsize=6.55, color=color)
    ax2.set_yticks(y, labels)
    ax2.invert_yaxis()
    ax2.set_xlim(0.245, 0.445)
    ax2.set_xlabel("Metric value")
    title(ax2, "B", "Fixed controls")
    grid(ax2, "x")
    ax2.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.52, -0.18), handletextpad=0.3, columnspacing=0.9)
    fig.subplots_adjust(left=0.105, right=0.985, top=0.84, bottom=0.27)
    save(fig, "fig2_transfer_controls")


def fig3_final():
    final = LEDGER["final_872"]
    metrics = final["metrics"]
    champion = np.array(final["rcrs"])
    static = np.array(final["operational_comparator"])
    deltas = np.array(final["paired_difference"])
    lower = np.array([np.nan if value is None else value for value in final["ci95_lower"]])
    upper = np.array([np.nan if value is None else value for value in final["ci95_upper"]])
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(7.15, 3.12),
        gridspec_kw={"width_ratios": [1.08, 1.12, 0.82], "wspace": 0.56},
    )
    ax1, ax2, ax3 = axes
    y = np.arange(3)
    for i in y:
        ax1.plot([static[i], champion[i]], [i, i], color=MID, linewidth=1.8, zorder=1)
    ax1.scatter(static, y, s=31, facecolors=WHITE, edgecolors=GREY, linewidths=1.1, marker="o", label="Operational comparator", zorder=3)
    ax1.scatter(champion, y, s=34, color=BLUE, marker="o", label="RCRS", zorder=3)
    for i in y:
        ax1.text(static[i] - 0.006, i - 0.13, f"{static[i]:.3f}", ha="right", fontsize=7.2, color=GREY)
        ax1.text(champion[i] + 0.006, i + 0.13, f"{champion[i]:.3f}", ha="left", fontsize=7.3, color=BLUE, weight="bold")
    ax1.set_yticks(y, metrics)
    ax1.set_ylim(2.55, -0.30)
    ax1.set_xlim(0.19, 0.49)
    ax1.set_xlabel("Score on OUT-eligible queries")
    title(ax1, "A", "Aggregate scores")
    grid(ax1, "x")
    ax1.tick_params(labelsize=7.6)
    ax1.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.20), handletextpad=0.35, columnspacing=1.0, fontsize=7.4)

    ax2.axvline(0, color=INK, linewidth=0.7)
    for i in y:
        if np.isfinite(lower[i]):
            ax2.errorbar(
                deltas[i],
                i,
                xerr=[[deltas[i] - lower[i]], [upper[i] - deltas[i]]],
                fmt="o",
                color=ORANGE,
                ecolor=ORANGE,
                capsize=2.5,
                markersize=4.5,
                linewidth=1.15,
            )
            ax2.text(upper[i] + 0.004, i, f"+{deltas[i]:.4f}", va="center", fontsize=7.3, color=ORANGE, weight="bold")
        else:
            ax2.plot(deltas[i], i, marker="D", markerfacecolor=WHITE, markeredgecolor=GREY, markersize=4.5)
            ax2.text(deltas[i] + 0.004, i, f"+{deltas[i]:.4f}  descriptive", va="center", fontsize=7.0, color=GREY)
    ax2.set_yticks(y, metrics)
    ax2.invert_yaxis()
    ax2.set_xlim(-0.004, 0.145)
    ax2.set_xlabel("Paired difference")
    ax2.tick_params(labelsize=7.6)
    title(ax2, "B", "Paired differences")
    grid(ax2, "x")

    outcomes = final["recall_outcomes"]
    counts = np.array([outcomes["wins"], outcomes["ties"], outcomes["losses"]])
    labels = ["Win", "Tie", "Loss"]
    colors = [BLUE, MID, ORANGE]
    markers = ["o", "s", "^"]
    yy = np.array([2, 1, 0])
    for val, lab, color, marker, pos in zip(counts, labels, colors, markers, yy):
        ax3.hlines(pos, 0, val, color=LIGHT, linewidth=2)
        ax3.scatter(val, pos, color=color, marker=marker, s=35, zorder=3)
        ax3.text(val + 18, pos, f"{val}", va="center", fontsize=7.4, color=color, weight="bold")
    ax3.set_yticks(yy, labels)
    ax3.set_xlim(0, 720)
    ax3.set_xlabel("Queries")
    ax3.tick_params(labelsize=7.6)
    title(ax3, "C", "Recall@100 outcomes")
    grid(ax3, "x")
    fig.subplots_adjust(left=0.08, right=0.975, top=0.82, bottom=0.25)
    save(fig, "fig3_final_confirmation")


def fig4_exposure():
    diagnosis = LEDGER["post_confirmatory"]
    depths = np.array(diagnosis["depths"])
    pos = np.arange(len(depths))
    curves = {
        "ALL": np.array(diagnosis["recall_curves"]["ALL"]),
        "IN": np.array(diagnosis["recall_curves"]["IN"]),
        r"$OUT_{\mathrm{strict}}$": np.array(diagnosis["recall_curves"]["OUT_strict"]),
    }
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(7.15, 3.02),
        gridspec_kw={"width_ratios": [1.18, 1.05, 0.92], "wspace": 0.56},
    )
    ax1, ax2, ax3 = axes
    styles = {
        "ALL": (GREY, "o", "-"),
        "IN": (BLUE, "s", "-"),
        r"$OUT_{\mathrm{strict}}$": (ORANGE, "^", "--"),
    }
    for name, values in curves.items():
        color, marker, line = styles[name]
        ax1.plot(pos, values, color=color, marker=marker, linestyle=line, linewidth=1.35, markersize=4.1)
        ax1.text(pos[-1] - 0.02, values[-1], name, color=color, va="center", ha="left", fontsize=6.9, weight="bold")
    ax1.set_xticks(pos, depths)
    ax1.set_xlim(-0.15, 4.42)
    ax1.set_ylim(0, 0.70)
    ax1.set_xlabel("Candidate depth")
    ax1.set_ylabel("Family Recall")
    title(ax1, "A", "Recall by candidate depth")
    grid(ax1)

    exposure = diagnosis["strict_out_pair_exposure"]
    parts = np.array([exposure["top_100"], exposure["ranks_101_200"], exposure["absent_top_200"]])
    names = ["Top 100", "101-200", "Absent"]
    colors = [BLUE, TEAL, MID]
    hatches = ["", "////", "...."]
    ybar = np.array([2, 1, 0])
    for value, name, color, hatch, yv in zip(parts, names, colors, hatches, ybar):
        ax2.barh(yv, value, color=color, edgecolor=INK, linewidth=0.35, hatch=hatch, height=0.52)
        ax2.text(value + 70, yv, f"{value:,}\n({100*value/parts.sum():.1f}%)", va="center", fontsize=6.7, color=INK)
    ax2.set_yticks(ybar, names)
    ax2.set_xlim(0, 4700)
    ax2.set_xlabel("Strictly OUT-linked relevant pairs")
    title(ax2, "B", "Top-200 exposure")
    grid(ax2, "x")

    bound = diagnosis["top_200_ordering_bound"]
    relation = ["ALL", "IN", r"$OUT_{\mathrm{strict}}$"]
    observed = np.array(bound["observed_recall_at_100"])
    oracle = np.array(bound["bound_recall_at_100"])
    y = np.arange(3)
    for i in y:
        ax3.plot([observed[i], oracle[i]], [i, i], color=MID, linewidth=1.8)
    ax3.scatter(observed, y, s=30, facecolor=WHITE, edgecolor=GREY, linewidth=1.0, marker="o", label="Observed @100", zorder=3)
    ax3.scatter(oracle, y, s=34, color=ORANGE, marker="D", label="Top-200 bound", zorder=3)
    for i in y:
        ax3.text(oracle[i] + 0.012, i, f"+{oracle[i] - observed[i]:.3f}", va="center", fontsize=6.7, color=ORANGE, weight="bold")
    ax3.set_yticks(y, relation)
    ax3.invert_yaxis()
    ax3.set_xlim(0.14, 0.70)
    ax3.set_xlabel("Recall@100")
    title(ax3, "C", "Perfect within-pool ordering bound")
    grid(ax3, "x")
    ax3.legend(frameon=False, ncol=1, loc="upper center", bbox_to_anchor=(0.53, -0.19), handletextpad=0.35)
    fig.subplots_adjust(left=0.075, right=0.975, top=0.82, bottom=0.27)
    save(fig, "fig4_candidate_exposure")


def graphical_abstract():
    """Optional 13:5 graphical abstract rendered as a scientific triptych."""
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(7.15, 2.72),
        gridspec_kw={"width_ratios": [0.86, 1.08, 1.25], "wspace": 0.38},
    )
    ax1, ax2, ax3 = axes

    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.axis("off")
    title(ax1, "A", "Representation search")
    pipeline = [
        (0.80, "Patent-family fields", INK),
        (0.60, "Executable program", ORANGE),
        (0.40, "Frozen retriever", BLUE),
        (0.20, "Family ranking", INK),
    ]
    for y, label, color in pipeline:
        ax1.text(0.50, y, label, ha="center", va="center", fontsize=7.0, color=color, weight="bold" if color != INK else "normal")
    for y0, y1 in [(0.75, 0.65), (0.55, 0.45), (0.35, 0.25)]:
        arrow(ax1, 0.50, y0, 0.50, y1, color=MID, width=0.75)
    ax1.text(
        0.50,
        0.07,
        "Retriever weights and scoring remain fixed;\nthe representation-specific index is rebuilt",
        ha="center",
        fontsize=5.8,
        color=GREY,
    )

    final = LEDGER["final_872"]
    static = final["operational_comparator"][0]
    rcrs = final["rcrs"][0]
    ax2.hlines(0.58, static, rcrs, color=MID, linewidth=2.0)
    ax2.scatter(static, 0.58, s=35, facecolors=WHITE, edgecolors=GREY, linewidths=1.1, zorder=3)
    ax2.scatter(rcrs, 0.58, s=38, color=ORANGE, zorder=3)
    ax2.text(static, 0.68, "Comparator\n0.3311", ha="center", va="bottom", fontsize=6.5, color=GREY)
    ax2.text(rcrs, 0.68, "RCRS\n0.4425", ha="center", va="bottom", fontsize=6.5, color=ORANGE, weight="bold")
    ax2.text(0.50, 0.31, "Paired difference  0.1114", transform=ax2.transAxes, ha="center", fontsize=7.0, color=INK)
    ax2.text(0.50, 0.20, "95% CI  [0.1023, 0.1204]", transform=ax2.transAxes, ha="center", fontsize=6.5, color=GREY)
    ax2.text(0.50, 0.09, "619 wins | 158 ties | 95 losses", transform=ax2.transAxes, ha="center", fontsize=6.3, color=GREY)
    ax2.set_xlim(0.29, 0.48)
    ax2.set_ylim(0, 1)
    ax2.set_yticks([])
    ax2.set_xlabel(r"$OUT_{\mathrm{eligible}}$ Recall@100 on Final-872")
    title(ax2, "B", "Frozen confirmation")
    grid(ax2, "x")

    exposure = LEDGER["post_confirmatory"]["strict_out_pair_exposure"]
    total = sum(exposure.values())
    segments = [
        (exposure["top_100"], "Top-100", BLUE, ""),
        (exposure["ranks_101_200"], "Ranks 101-200", TEAL, "////"),
        (exposure["absent_top_200"], "Absent from Top-200", MID, "...."),
    ]
    left = 0
    for value, label, color, hatch in segments:
        ax3.barh(0, value, left=left, color=color, edgecolor=INK, linewidth=0.35, hatch=hatch, height=0.34, label=label)
        left += value
    ax3.set_xlim(0, total)
    ax3.set_ylim(-0.72, 0.72)
    ax3.set_yticks([])
    ax3.set_xticks([])
    title(ax3, "C", "Strict OUT candidate exposure")
    ax3.text(398, 0.30, "796", ha="center", va="bottom", fontsize=6.4, color=BLUE, weight="bold")
    ax3.text(962, -0.31, "332", ha="center", va="top", fontsize=6.4, color=TEAL, weight="bold")
    ax3.text(3160, 0.30, "4,065 absent", ha="center", va="bottom", fontsize=6.8, color=INK, weight="bold")
    ax3.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.06), fontsize=6.0, handlelength=1.6)
    for spine in ax3.spines.values():
        spine.set_visible(False)
    fig.subplots_adjust(left=0.035, right=0.985, top=0.83, bottom=0.22)
    save(fig, "graphical_abstract")


if __name__ == "__main__":
    fig1_protocol()
    fig2_transfer()
    fig3_final()
    fig4_exposure()
    graphical_abstract()
