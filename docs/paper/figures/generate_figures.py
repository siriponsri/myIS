from __future__ import annotations

import io
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "prism-uploads" / "myIS_prism_csv_pack_20260826.zip"
PREFIX = "myIS_prism_csv_pack_20260826/prism_ready/"
OUT = ROOT / "figures"

NAVY = "#17365D"
BLUE = "#2C78B8"
TEAL = "#2A9D8F"
GOLD = "#E9C46A"
ORANGE = "#E76F51"
LIGHT = "#E8EEF4"
MIDGRAY = "#7A7A7A"
DARK = "#202020"


def load_csv(name: str) -> pd.DataFrame:
    with zipfile.ZipFile(ARCHIVE) as zf:
        raw = zf.read(PREFIX + name)
    return pd.read_csv(io.BytesIO(raw))


def set_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.2,
            "axes.labelsize": 8.5,
            "axes.titlesize": 9.0,
            "xtick.labelsize": 7.6,
            "ytick.labelsize": 7.6,
            "legend.fontsize": 7.4,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.transparent": False,
        }
    )


def save_figure(fig: plt.Figure, stem: str) -> None:
    """Persist vector and high-resolution raster variants for LaTeX export."""
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(OUT / f"{stem}.png", dpi=600, bbox_inches="tight", pad_inches=0.02)


def fig1_transfer() -> None:
    df = load_csv("fig1_a3_transfer.csv")
    assert len(df) == 9 and set(df["evidence_class"]) == {"development"}

    sources = ["PatEmbed", "Arctic Embed", "Qwen3 Embedding"]
    targets = ["PatEmbed", "Arctic Embed", "Qwen3 Embedding"]
    matrix = (
        df.pivot(index="representation_source", columns="target_retriever", values="Recall@100")
        .reindex(index=sources, columns=targets)
        .to_numpy()
    )
    np.testing.assert_allclose(matrix.max(axis=0), [0.419273743017, 0.341340782123, 0.362569832402])

    cmap = LinearSegmentedColormap.from_list("paper_blues", ["#F4F7FA", "#A9C9E2", NAVY])
    fig, ax = plt.subplots(figsize=(7.05, 1.85))
    im = ax.imshow(matrix, cmap=cmap, vmin=0.33, vmax=0.425, aspect="auto")

    ax.set_xticks(range(3), ["PatEmbed", "Arctic Embed", "Qwen3 Embedding"])
    ax.set_yticks(range(3), ["PatEmbed-derived", "Arctic-derived", "Qwen3-derived"])
    ax.set_xlabel("Target retriever")
    ax.set_ylabel("Representation source")
    ax.tick_params(length=0)

    maxima = matrix.argmax(axis=0)
    for row in range(3):
        for col in range(3):
            value = matrix[row, col]
            text_color = "white" if value > 0.385 else DARK
            weight = "bold" if row == maxima[col] else "normal"
            ax.text(
                col,
                row,
                f"{value:.6f}",
                ha="center",
                va="center",
                color=text_color,
                fontweight=weight,
                fontsize=7.2,
            )
            if row == col:
                ax.add_patch(
                    Rectangle(
                        (col - 0.47, row - 0.47),
                        0.94,
                        0.94,
                        fill=False,
                        edgecolor=DARK,
                        linewidth=1.0,
                        linestyle=(0, (3, 2)),
                    )
                )
            if row == maxima[col]:
                ax.plot(col + 0.34, row - 0.31, marker="o", markersize=4.2, color=GOLD, markeredgecolor=DARK, markeredgewidth=0.5)

    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.025)
    cbar.set_label("Recall@100")
    cbar.outline.set_linewidth(0.6)
    ax.text(
        1.0,
        -0.26,
        "Dashed border: matched source and target    Gold marker: best source for each target",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=7.2,
        color=MIDGRAY,
    )
    fig.subplots_adjust(left=0.20, right=0.94, bottom=0.34, top=0.98)
    save_figure(fig, "fig1_a3_transfer")
    plt.close(fig)


def fig2_confirmation() -> None:
    metrics = load_csv("fig2_a5_confirmation.csv")
    wtl = load_csv("fig2_a5_recall_wtl.csv")
    confirm = metrics[metrics["metric"].isin(["Recall@100", "nDCG@100"])].copy()
    assert len(confirm) == 2 and set(confirm["n_queries"]) == {872}
    np.testing.assert_allclose(confirm["paired_difference"], [0.111379, 0.086342])
    assert int(wtl["count"].sum()) == 872

    fig = plt.figure(figsize=(3.35, 3.55))
    gs = fig.add_gridspec(3, 1, height_ratios=[1.05, 0.95, 0.48], hspace=0.78)

    ax0 = fig.add_subplot(gs[0, 0])
    y = np.array([1, 0])
    labels = confirm["metric"].tolist()
    static = confirm["static_comparator"].to_numpy()
    selected = confirm["selected_research"].to_numpy()
    for yi, a, b in zip(y, static, selected):
        ax0.plot([a, b], [yi, yi], color="#B7C4CF", linewidth=2.2, zorder=1)
    ax0.scatter(static, y, s=35, color=MIDGRAY, label="Static comparator", zorder=2)
    ax0.scatter(selected, y, s=42, color=BLUE, label="Selected configuration", zorder=3)
    for yi, a, b in zip(y, static, selected):
        ax0.text(a, yi + 0.17, f"{a:.3f}", ha="center", color=MIDGRAY, fontsize=7.1)
        ax0.text(b, yi + 0.17, f"{b:.3f}", ha="center", color=NAVY, fontsize=7.1, fontweight="bold")
    ax0.set_yticks(y, labels)
    ax0.set_xlim(0.25, 0.47)
    ax0.set_xlabel("Final-872 score")
    ax0.grid(axis="x", color=LIGHT, linewidth=0.7)
    ax0.scatter([0.278, 0.371], [0.50, 0.50], s=22, color=[MIDGRAY, BLUE], zorder=3)
    ax0.text(0.286, 0.50, "static", va="center", color=MIDGRAY, fontsize=6.8)
    ax0.text(0.379, 0.50, "selected", va="center", color=NAVY, fontsize=6.8)
    ax0.set_title("A  Absolute performance", loc="left", fontweight="bold", pad=4)

    ax1 = fig.add_subplot(gs[1, 0])
    diffs = confirm["paired_difference"].to_numpy()
    low = confirm["ci95_low"].to_numpy()
    high = confirm["ci95_high"].to_numpy()
    xerr = np.vstack([diffs - low, high - diffs])
    ax1.errorbar(diffs, y, xerr=xerr, fmt="o", color=NAVY, ecolor=BLUE, elinewidth=2.2, capsize=3.5, markersize=5)
    ax1.axvline(0, color=MIDGRAY, linewidth=0.8)
    for yi, d in zip(y, diffs):
        ax1.text(d, yi + 0.18, f"+{d:.3f}", ha="center", color=NAVY, fontsize=7.1, fontweight="bold")
    ax1.set_yticks(y, labels)
    ax1.set_xlim(0, 0.13)
    ax1.set_xlabel("Paired difference (95% CI)")
    ax1.grid(axis="x", color=LIGHT, linewidth=0.7)
    ax1.set_title("B  Confirmatory effect", loc="left", fontweight="bold", pad=4)

    ax2 = fig.add_subplot(gs[2, 0])
    counts = wtl.set_index("outcome").loc[["win", "tie", "loss"], "count"].to_numpy()
    colors = [TEAL, "#C9D2D9", ORANGE]
    left = 0
    for count, color, label in zip(counts, colors, ["W", "T", "L"]):
        ax2.barh([0], [count], left=left, height=0.48, color=color, edgecolor="white", linewidth=0.8)
        ax2.text(
            left + count / 2,
            0,
            f"{label}\n{count}",
            ha="center",
            va="center",
            fontsize=6.8,
            color="white" if label != "T" else DARK,
            fontweight="bold",
        )
        left += count
    ax2.set_xlim(0, 872)
    ax2.set_ylim(-0.62, 0.62)
    ax2.set_xticks([])
    ax2.set_yticks([])
    ax2.set_title("C  Recall@100 query outcomes", loc="left", fontweight="bold", pad=4)
    ax2.spines["left"].set_visible(False)
    ax2.spines["bottom"].set_visible(False)

    fig.subplots_adjust(left=0.25, right=0.98, bottom=0.08, top=0.97)
    save_figure(fig, "fig2_a5_confirmation")
    plt.close(fig)


def fig3_diagnosis() -> None:
    df = load_csv("fig3_a7_out_diagnosis.csv")
    incidence = df[df["unit"] == "relevant_family_incidence"].set_index("state")
    recall = df[df["unit"] == "macro_recall"].set_index("state")
    counts = incidence.loc[
        ["exposed_by_rank_100", "first_exposed_rank_101_200", "absent_at_rank_200"], "value"
    ].to_numpy(dtype=float)
    np.testing.assert_allclose(counts, [796, 332, 4065])
    observed = float(recall.loc["observed_Recall@100", "value"])
    oracle = float(recall.loc["fixed_pool_oracle_Recall@100", "value"])
    headroom = float(recall.loc["bounded_ordering_headroom_Recall@100", "value"])
    np.testing.assert_allclose([observed, oracle, headroom], [0.188449898653, 0.260166940437, 0.071717041784])

    fig = plt.figure(figsize=(3.35, 2.95))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.05, 0.95], hspace=0.53)

    ax0 = fig.add_subplot(gs[0, 0])
    colors = [TEAL, GOLD, ORANGE]
    labels = ["Found by rank 100", "First found at ranks 101--200", "Absent from Top-200"]
    left = 0.0
    for count, color, label in zip(counts, colors, labels):
        ax0.barh([0], [count], left=left, height=0.46, color=color, edgecolor="white", linewidth=0.8)
        if label == "Absent from Top-200":
            text_color = "white" if color != GOLD else DARK
            ax0.text(
                left + count / 2,
                0,
                f"{int(count):,} / 5,193\n{label}",
                ha="center",
                va="center",
                fontsize=6.2,
                color=text_color,
                fontweight="bold",
            )
        else:
            short_label = "by rank 100" if label == "Found by rank 100" else "ranks 101--200"
            offset = 0 if label == "Found by rank 100" else 700
            ax0.annotate(
                f"{int(count):,} / 5,193\n{short_label}",
                xy=(left + count / 2, 0.25),
                xytext=(left + count / 2 + offset, 0.65),
                ha="center",
                va="bottom",
                fontsize=6.0,
                arrowprops={"arrowstyle": "-", "color": MIDGRAY, "linewidth": 0.7},
            )
        left += count
    ax0.set_xlim(0, 5193)
    ax0.set_ylim(-0.55, 1.00)
    ax0.set_yticks([])
    ax0.set_xlabel("Strict cross-domain relevant incidences (n=5,193)", fontsize=7.4)
    ax0.set_title("A  Exposure anatomy", loc="left", fontweight="bold", pad=4)
    ax0.spines["left"].set_visible(False)

    ax1 = fig.add_subplot(gs[1, 0])
    ax1.plot([observed, oracle], [0, 0], color="#AEBBC5", linewidth=5, solid_capstyle="round", zorder=1)
    ax1.scatter([observed], [0], s=55, color=BLUE, zorder=3)
    ax1.scatter([oracle], [0], s=55, color=ORANGE, zorder=3)
    ax1.text(observed, 0.18, f"Observed\n{observed:.3f}", ha="center", color=NAVY, fontsize=7.4, fontweight="bold")
    ax1.text(oracle, 0.18, f"Perfect ordering\n{oracle:.3f}", ha="center", color=ORANGE, fontsize=7.4, fontweight="bold")
    ax1.annotate(
        f"bounded headroom\n+{headroom:.3f}",
        xy=((observed + oracle) / 2, -0.03),
        xytext=((observed + oracle) / 2, -0.36),
        ha="center",
        va="top",
        fontsize=7.2,
        color=DARK,
        arrowprops={"arrowstyle": "-[,widthB=2.7", "color": MIDGRAY, "linewidth": 0.8},
    )
    ax1.set_xlim(0.15, 0.28)
    ax1.set_ylim(-0.58, 0.55)
    ax1.set_yticks([])
    ax1.set_xlabel("Macro Recall@100 over 905 queries")
    ax1.set_title("B  Within-pool ordering bound", loc="left", fontweight="bold", pad=4)
    ax1.spines["left"].set_visible(False)
    ax1.grid(axis="x", color=LIGHT, linewidth=0.7)

    fig.text(
        0.58,
        0.015,
        "Analytical bound inside the existing Top-200 pool; not a reranker experiment.",
        ha="center",
        va="bottom",
        fontsize=6.2,
        color=MIDGRAY,
    )
    fig.subplots_adjust(left=0.18, right=0.98, bottom=0.17, top=0.97)
    save_figure(fig, "fig3_a7_diagnosis")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    set_style()
    fig1_transfer()
    fig2_confirmation()
    fig3_diagnosis()


if __name__ == "__main__":
    main()