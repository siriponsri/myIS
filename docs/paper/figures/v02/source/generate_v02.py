"""Generate v01 IEEE figure candidates from the canonical CSV publication pack.

The manuscript and evidence are frozen.  This source owns only v01 artifacts.
"""
from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / "prism-uploads" / "myIS_prism_csv_pack_20260826.zip"
PREFIX = "myIS_prism_csv_pack_20260826/prism_ready/"
OUT = Path(__file__).resolve().parents[1]

FONT = "Arial"
INK = "#1E3557"
SLATE = "#A9B6C4"
SLATE_DARK = "#7D8D9D"
BLUE = "#3E86C8"
BLUE_DARK = "#2B6CA8"
CORAL = "#D85C4A"
AMBER = "#D8A62A"
TEAL = "#0F9D9A"
GRID = "#E5EBF0"
WHITE = "#FFFFFF"

SOURCES = ["PatEmbed", "Arctic Embed", "Qwen3 Embedding"]
TARGETS = SOURCES[:]
SHORT = {"PatEmbed": "PatEmbed", "Arctic Embed": "Arctic", "Qwen3 Embedding": "Qwen3"}
MARKERS = {"PatEmbed": "o", "Arctic Embed": "s", "Qwen3 Embedding": "D"}


def rows(member: str) -> list[dict[str, str]]:
    with zipfile.ZipFile(ARCHIVE) as archive:
        raw = archive.read(PREFIX + member).decode("utf-8")
    return list(csv.DictReader(io.StringIO(raw)))


def load_and_assert() -> tuple[dict[tuple[str, str], float], dict[str, dict[str, float]], dict[str, float]]:
    """Read canonical figure CSVs and reject drift from the audited values."""
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

    confirmation = {
        row["metric"]: {key: float(value) for key, value in row.items()
                        if key in {"static_comparator", "selected_research", "paired_difference", "ci95_low", "ci95_high"} and value}
        for row in rows("fig2_a5_confirmation.csv")
    }
    assert confirmation["Recall@100"] == {
        "static_comparator": 0.331097, "selected_research": 0.442476,
        "paired_difference": 0.111379, "ci95_low": 0.102294, "ci95_high": 0.120438,
    }, "A5 Recall drift"
    assert confirmation["nDCG@100"] == {
        "static_comparator": 0.279253, "selected_research": 0.365595,
        "paired_difference": 0.086342, "ci95_low": 0.078673, "ci95_high": 0.094077,
    }, "A5 nDCG drift"
    wtl = {row["outcome"]: int(row["count"]) for row in rows("fig2_a5_recall_wtl.csv")}
    assert wtl == {"win": 619, "tie": 158, "loss": 95}, "A5 W/T/L drift"

    diagnosis = {row["state"]: float(row["value"]) for row in rows("fig3_a7_out_diagnosis.csv")}
    expected_diagnosis = {
        "exposed_by_rank_100": 796.0,
        "first_exposed_rank_101_200": 332.0,
        "absent_at_rank_200": 4065.0,
        "observed_Recall@100": 0.188449898653,
        "fixed_pool_oracle_Recall@100": 0.260166940437,
        "bounded_ordering_headroom_Recall@100": 0.071717041784,
    }
    for key, expected in expected_diagnosis.items():
        assert diagnosis[key] == expected, f"A7 drift: {key}"
    return transfer, confirmation, {**diagnosis, **{f"wtl_{k}": v for k, v in wtl.items()}}


def style() -> None:
    mpl.rcParams.update({
        "font.family": FONT,
        "font.size": 8.2,
        "axes.titleweight": "bold",
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "text.color": INK,
        "axes.edgecolor": SLATE,
        "axes.linewidth": 0.65,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "figure.facecolor": WHITE,
        "axes.facecolor": WHITE,
    })


def clean_axis(ax: plt.Axes, grid: str | None = "x") -> None:
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=3, color=SLATE, labelsize=7.4)
    if grid:
        ax.grid(axis=grid, color=GRID, linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)


def panel_label(ax: plt.Axes, letter: str, title: str, subtitle: str, x: float = 0.0) -> None:
    ax.text(x, 1.11, letter, transform=ax.transAxes, ha="left", va="bottom", color=BLUE_DARK,
            fontsize=9.2, fontweight="bold")
    ax.text(x + 0.072, 1.11, title, transform=ax.transAxes, ha="left", va="bottom", color=INK,
            fontsize=9.2, fontweight="bold")
    ax.text(x + 0.072, 1.02, subtitle, transform=ax.transAxes, ha="left", va="bottom", color=SLATE_DARK,
            fontsize=7.2)


def export(fig: plt.Figure, stem: str) -> None:
    fig.savefig(OUT / f"{stem}.pdf")
    fig.savefig(OUT / f"{stem}.svg")
    fig.savefig(OUT / f"{stem}.png", dpi=360)
    plt.close(fig)


def figure1(transfer: dict[tuple[str, str], float]) -> None:
    """A3: three integrated absolute-and-delta target rows."""
    style()
    fig = plt.figure(figsize=(7.16, 2.30))
    grid = fig.add_gridspec(3, 2, width_ratios=(1.68, 1.0), left=0.185, right=0.985,
                            bottom=0.33, top=0.80, hspace=0.34, wspace=0.17)
    left_axes, right_axes = [], []
    for index, target in enumerate(TARGETS):
        absolute = fig.add_subplot(grid[index, 0], sharex=left_axes[0] if left_axes else None)
        delta = fig.add_subplot(grid[index, 1], sharex=right_axes[0] if right_axes else None)
        left_axes.append(absolute)
        right_axes.append(delta)
        values = [transfer[(source, target)] for source in SOURCES]
        matched = transfer[(target, target)]
        best = max(values)
        absolute.plot([min(values), max(values)], [0, 0], color=SLATE, lw=2.0,
                      solid_capstyle="round", zorder=1)
        delta.axvline(0, color=INK, lw=0.8, zorder=1)
        for source, value in zip(SOURCES, values):
            face = AMBER if value == best else SLATE
            kwargs = dict(s=38, marker=MARKERS[source], color=face, edgecolor=WHITE, linewidth=0.75, zorder=3)
            absolute.scatter(value, 0, **kwargs)
            delta.scatter(value - matched, 0, **kwargs)
            if source == target:
                absolute.scatter(value, 0, s=81, marker=MARKERS[source], facecolors="none", edgecolors=INK,
                                 linewidths=1.0, zorder=4)
                delta.scatter(value - matched, 0, s=81, marker=MARKERS[source], facecolors="none", edgecolors=INK,
                              linewidths=1.0, zorder=4)
        absolute.text(-0.10, 0, f"{SHORT[target]} target", transform=absolute.transAxes,
                      ha="right", va="center", fontsize=7.9, color=INK, fontweight="bold")
        absolute.text(0.996, 0.66, f"range {max(values) - min(values):.6f}", transform=absolute.transAxes,
                      ha="right", va="center", fontsize=6.8, color=SLATE_DARK)
        for axis in (absolute, delta):
            axis.set_ylim(-0.6, 0.6)
            axis.set_yticks([])
            axis.spines[["top", "right", "left"]].set_visible(False)
            axis.tick_params(axis="x", length=2.8, color=SLATE, labelsize=7.2)
        absolute.set_xlim(0.33, 0.425)
        delta.set_xlim(-0.0045, 0.0025)
        if index < 2:
            absolute.tick_params(labelbottom=False)
            delta.tick_params(labelbottom=False)
            absolute.spines["bottom"].set_visible(False)
            delta.spines["bottom"].set_visible(False)
        else:
            absolute.set_xticks([0.34, 0.38, 0.42], ["0.34", "0.38", "0.42"])
            absolute.set_xlabel("Recall@100 (common absolute scale)", fontsize=7.5, labelpad=3)
            delta.set_xticks([-0.004, 0, 0.002], ["-0.004", "0", "+0.002"])
            delta.set_xlabel("Difference from matched source", fontsize=7.5, labelpad=3)
    left_axes[0].text(0.0, 1.33, "A", transform=left_axes[0].transAxes, color=BLUE_DARK,
                      fontsize=9.0, fontweight="bold")
    left_axes[0].text(0.055, 1.33, "Absolute score context", transform=left_axes[0].transAxes, color=INK,
                      fontsize=9.0, fontweight="bold")
    right_axes[0].text(0.0, 1.33, "B", transform=right_axes[0].transAxes, color=BLUE_DARK,
                       fontsize=9.0, fontweight="bold")
    right_axes[0].text(0.075, 1.33, "Transfer from matched source", transform=right_axes[0].transAxes, color=INK,
                       fontsize=9.0, fontweight="bold")
    fig.text(0.185, 0.145,
             "Key: circle PatEmbed; square Arctic; diamond Qwen3. Amber = nominal best; dark ring = matched pair.",
             fontsize=6.9, color=SLATE_DARK)
    fig.text(0.185, 0.075,
             "Small within-target ranges are descriptive development evidence; no significance inference is shown.",
             fontsize=6.9, color=SLATE_DARK)
    export(fig, "fig1_a3_transfer")


def figure2(confirmation: dict[str, dict[str, float]], audit: dict[str, float]) -> None:
    """A5: integrated two-row complete-system comparison and W/T/L support."""
    style()
    fig = plt.figure(figsize=(7.16, 2.25))
    gs = fig.add_gridspec(2, 2, height_ratios=(3.0, 1.0), width_ratios=(1.04, 1.2),
                          left=0.11, right=0.985, top=0.76, bottom=0.14, hspace=1.32, wspace=0.27)
    absolute = fig.add_subplot(gs[0, 0])
    effect = fig.add_subplot(gs[0, 1])
    ribbon = fig.add_subplot(gs[1, :])
    metrics = ["Recall@100", "nDCG@100"]
    ys = [1, 0]
    for metric, y in zip(metrics, ys):
        r = confirmation[metric]
        absolute.plot([r["static_comparator"], r["selected_research"]], [y, y], color=SLATE,
                      lw=2.2, solid_capstyle="round", zorder=1)
        absolute.scatter(r["static_comparator"], y, color=SLATE, edgecolor=WHITE, linewidth=0.8, s=47, zorder=3)
        absolute.scatter(r["selected_research"], y, color=BLUE, edgecolor=WHITE, linewidth=0.8, s=53, zorder=3)
        absolute.text(r["static_comparator"], y + 0.20, f"{r['static_comparator']:.6f}", ha="center", fontsize=7.0)
        absolute.text(r["selected_research"], y + 0.20, f"{r['selected_research']:.6f}", ha="center", fontsize=7.0,
                      color=BLUE_DARK, fontweight="bold")
        effect.plot([r["ci95_low"], r["ci95_high"]], [y, y], color=BLUE_DARK, lw=2.6,
                    solid_capstyle="round", zorder=1)
        effect.vlines([r["ci95_low"], r["ci95_high"]], y - 0.10, y + 0.10, color=BLUE_DARK, lw=1.15)
        effect.scatter(r["paired_difference"], y, color=BLUE, edgecolor=WHITE, linewidth=0.8, s=60, zorder=3)
        effect.text(r["paired_difference"], y + 0.21, f"+{r['paired_difference']:.6f}", ha="center", fontsize=8.1,
                    color=BLUE_DARK, fontweight="bold")
        effect.text(0.142, y - 0.31, f"95% CI [{r['ci95_low']:.6f}, {r['ci95_high']:.6f}]",
                    ha="right", fontsize=6.55, color=SLATE_DARK)
    absolute.set_xlim(0.25, 0.47)
    absolute.set_ylim(-0.42, 1.42)
    absolute.set_xticks([0.28, 0.36, 0.44], ["0.28", "0.36", "0.44"])
    absolute.set_yticks(ys, metrics)
    absolute.set_xlabel("Score", fontsize=7.4, labelpad=2)
    clean_axis(absolute)
    absolute.text(0.0, 1.18, "A", transform=absolute.transAxes, color=BLUE_DARK, fontsize=9.0,
                  fontweight="bold", va="bottom")
    absolute.text(0.055, 1.18, "Absolute scores", transform=absolute.transAxes, color=INK, fontsize=9.0,
                  fontweight="bold", va="bottom")

    effect.axvline(0, color=INK, lw=0.85)
    effect.set_xlim(0, 0.145)
    effect.set_ylim(-0.42, 1.42)
    effect.set_xticks([0, 0.06, 0.12], ["0", "+0.06", "+0.12"])
    effect.set_yticks(ys)
    effect.tick_params(labelleft=False)
    effect.set_xlabel("Paired difference", fontsize=7.4, labelpad=2)
    clean_axis(effect)
    effect.text(0.0, 1.18, "B", transform=effect.transAxes, color=BLUE_DARK, fontsize=9.0,
                fontweight="bold", va="bottom")
    effect.text(0.075, 1.18, "Paired effects with 95% CI", transform=effect.transAxes, color=INK,
                fontsize=9.0, fontweight="bold", va="bottom")

    total = sum(audit[f"wtl_{key}"] for key in ("win", "tie", "loss"))
    start = 0
    for name, color in [("Win", BLUE), ("Tie", SLATE_DARK), ("Loss", CORAL)]:
        count = audit[f"wtl_{name.lower()}"]
        ribbon.add_patch(Rectangle((start, 0.22), count, 0.54, facecolor=color, edgecolor=WHITE, linewidth=0.75))
        ribbon.text(start + count / 2, 0.49, f"{name} {count}", ha="center", va="center", fontsize=7.2,
                    color=WHITE, fontweight="bold")
        start += count
    ribbon.add_patch(FancyBboxPatch((0, 0.22), total, 0.54, boxstyle="round,pad=0,rounding_size=7",
                                    fill=False, edgecolor=INK, linewidth=0.75))
    ribbon.set_xlim(0, total)
    ribbon.set_ylim(0, 1)
    ribbon.axis("off")
    ribbon.text(0.0, 1.02, "C", transform=ribbon.transAxes, color=BLUE_DARK, fontsize=8.7, fontweight="bold", va="bottom")
    ribbon.text(0.040, 1.02, "Recall wins / ties / losses", transform=ribbon.transAxes, color=INK,
                fontsize=8.7, fontweight="bold", va="bottom")
    ribbon.text(0.36, 1.02, "paired query outcomes (n=872)", transform=ribbon.transAxes, color=SLATE_DARK,
                fontsize=6.7, va="bottom")
    fig.text(0.11, 0.045, "Complete-system comparison; not representation-only causal evidence.",
             fontsize=6.55, color=SLATE_DARK)
    export(fig, "fig2_a5_confirmation")


def figure3(audit: dict[str, float]) -> None:
    """A7: exposure partition followed by the fixed-pool analytical ordering bound."""
    style()
    fig = plt.figure(figsize=(7.16, 2.10))
    gs = fig.add_gridspec(2, 1, height_ratios=(1.12, 1.0), left=0.10, right=0.985,
                          top=0.79, bottom=0.16, hspace=0.62)
    exposure = fig.add_subplot(gs[0, 0])
    bound = fig.add_subplot(gs[1, 0])
    total = 5193
    pieces = [
        ("By rank 100", audit["exposed_by_rank_100"], BLUE),
        ("First at 101-200", audit["first_exposed_rank_101_200"], SLATE_DARK),
        ("Absent from Top-200", audit["absent_at_rank_200"], CORAL),
    ]
    start = 0
    for label, count, color in pieces:
        exposure.add_patch(Rectangle((start, 0.34), count, 0.34, facecolor=color, edgecolor=WHITE, linewidth=0.75))
        if label == "Absent from Top-200":
            exposure.text(start + count / 2, 0.51, "78.3% absent", color=WHITE, ha="center", va="center",
                          fontsize=9.0, fontweight="bold")
        start += count
    exposure.add_patch(Rectangle((0, 0.34), total, 0.34, fill=False, edgecolor=INK, linewidth=0.75))
    exposure.text(0, 0.13, "796 by rank 100 (15.3%)", color=BLUE, fontsize=7.0, ha="left")
    exposure.text(990, 0.13, "332 first at 101-200 (6.4%)", color=SLATE_DARK, fontsize=7.0, ha="left")
    exposure.text(total, 0.13, "4,065 / 5,193 absent from Top-200", color=CORAL, fontsize=8.2,
                  ha="right", fontweight="bold")
    exposure.set_xlim(-140, total + 140)
    exposure.set_ylim(0, 1)
    exposure.axis("off")
    exposure.text(0.0, 1.11, "A", transform=exposure.transAxes, color=BLUE_DARK, fontsize=9.0, fontweight="bold", va="bottom")
    exposure.text(0.045, 1.11, "Candidate exposure anatomy", transform=exposure.transAxes, color=INK,
                  fontsize=9.0, fontweight="bold", va="bottom")
    exposure.text(0.045, 0.92, "Relevant-family incidences; separate from macro Recall.", transform=exposure.transAxes,
                  color=SLATE_DARK, fontsize=6.8, va="bottom")

    observed = audit["observed_Recall@100"]
    oracle = audit["fixed_pool_oracle_Recall@100"]
    headroom = audit["bounded_ordering_headroom_Recall@100"]
    y = 0.40
    bound.plot([observed, oracle], [y, y], color=SLATE, lw=3.0, solid_capstyle="round", zorder=1)
    bound.scatter(observed, y, s=62, color=BLUE, edgecolor=WHITE, linewidth=0.75, zorder=3)
    bound.scatter(oracle, y, s=62, color=AMBER, edgecolor=WHITE, linewidth=0.75, zorder=3)
    bound.text(observed, y + 0.14, f"Observed\n{observed:.6f}", ha="center", va="bottom", fontsize=7.0,
               color=BLUE_DARK, fontweight="bold")
    bound.text(oracle, y + 0.14, f"Perfect-ordering bound\n{oracle:.6f}", ha="center", va="bottom", fontsize=7.0,
               color=INK, fontweight="bold")
    bound.text((observed + oracle) / 2, y - 0.16, f"+{headroom:.6f} headroom", ha="center", va="center",
               fontsize=8.0, color=AMBER, fontweight="bold")
    bound.set_xlim(0.17, 0.278)
    bound.set_ylim(0.02, 1.05)
    bound.set_xticks([0.18, 0.22, 0.26], ["0.18", "0.22", "0.26"])
    bound.set_yticks([])
    bound.set_xlabel("Macro Recall@100 across 905 strict cross-domain queries", fontsize=7.8, labelpad=2)
    clean_axis(bound)
    bound.text(0.0, 1.26, "B", transform=bound.transAxes, color=BLUE_DARK, fontsize=9.0, fontweight="bold", va="bottom")
    bound.text(0.045, 1.26, "What ordering could recover", transform=bound.transAxes, color=INK,
               fontsize=9.0, fontweight="bold", va="bottom")
    bound.text(0.045, 1.03, "Analytical bound inside the immutable Top-200 pool; not reranker performance.", transform=bound.transAxes,
               color=SLATE_DARK, fontsize=7.2, va="bottom")
    fig.text(0.50, 0.485, "within the available pool", ha="center", va="center", color=SLATE_DARK, fontsize=6.7)
    fig.add_artist(FancyArrowPatch((0.50, 0.510), (0.50, 0.470), transform=fig.transFigure,
                                   arrowstyle="-|>", mutation_scale=7, linewidth=0.8, color=SLATE_DARK))
    export(fig, "fig3_a7_diagnosis")


def small_icon(ax: plt.Axes, kind: str, x: float, y: float, color: str) -> None:
    """Tiny meaningful glyphs used only as station identifiers in the evidence map."""
    if kind == "construct":
        for dx, width in [(-0.012, 0.017), (0, 0.022), (0.012, 0.017)]:
            ax.add_patch(FancyBboxPatch((x + dx - width / 2, y - 0.009), width, 0.018,
                                        boxstyle="round,pad=0.001,rounding_size=0.004", facecolor=WHITE, edgecolor="none"))
    elif kind == "transfer":
        for a, b in [((x - 0.017, y - 0.012), (x + 0.017, y + 0.012)), ((x - 0.017, y + 0.012), (x + 0.017, y - 0.012))]:
            ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=5, linewidth=0.85, color=WHITE))
    elif kind == "freeze":
        ax.add_patch(FancyBboxPatch((x - 0.012, y - 0.012), 0.024, 0.019, boxstyle="round,pad=0.001,rounding_size=0.003",
                                    facecolor=WHITE, edgecolor="none"))
        ax.add_patch(Circle((x, y + 0.009), 0.009, fill=False, edgecolor=WHITE, linewidth=0.9))
    else:
        ax.add_patch(Circle((x - 0.005, y + 0.005), 0.010, fill=False, edgecolor=WHITE, linewidth=0.9))
        ax.plot([x + 0.002, x + 0.014], [y - 0.003, y - 0.015], color=WHITE, lw=0.9, solid_capstyle="round")


def overview() -> None:
    """Shallow evidence map with a strong development-closure gate."""
    style()
    fig, ax = plt.subplots(figsize=(7.16, 1.13))
    fig.subplots_adjust(left=0.02, right=0.99, top=0.98, bottom=0.03)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    y = 0.47
    ax.plot([0.07, 0.476], [y, y], color=SLATE_DARK, lw=1.28, solid_capstyle="round")
    ax.add_patch(FancyArrowPatch((0.476, y), (0.485, y), arrowstyle="-|>", mutation_scale=7,
                                 linewidth=1.28, color=SLATE_DARK))
    ax.plot([0.515, 0.931], [y, y], color=BLUE_DARK, lw=1.28, solid_capstyle="round")
    ax.add_patch(FancyArrowPatch((0.931, y), (0.94, y), arrowstyle="-|>", mutation_scale=7,
                                 linewidth=1.28, color=BLUE_DARK))
    ax.plot([0.5, 0.5], [0.16, 0.86], color=INK, lw=1.15)
    ax.text(0.5, 0.92, "DEVELOPMENT CLOSED", ha="center", va="center", fontsize=7.35, color=INK, fontweight="bold",
            bbox={"boxstyle": "round,pad=0.17,rounding_size=0.06", "facecolor": WHITE, "edgecolor": "none"})
    ax.text(0.44, 0.80, "DEVELOPMENT", ha="right", fontsize=6.45, color=SLATE_DARK, fontweight="bold")
    ax.text(0.56, 0.80, "PROTECTED / POST-CONFIRMATORY", ha="left", fontsize=6.45, color=BLUE_DARK, fontweight="bold")
    stages = [
        (0.12, "01", "CONSTRUCT", "Representations; A1/A2", SLATE_DARK, "construct"),
        (0.36, "02", "TEST PORTABILITY", "A3 cross-retriever transfer", TEAL, "transfer"),
        (0.64, "03", "FREEZE & CONFIRM", "Selection-125 to Final-872", BLUE, "freeze"),
        (0.88, "04", "DIAGNOSE", "Full benchmark to A7", CORAL, "diagnose"),
    ]
    for x, number, title, detail, color, kind in stages:
        ax.scatter(x, y, s=155, color=color, edgecolor=WHITE, linewidth=1.0, zorder=3)
        small_icon(ax, kind, x, y, color)
        ax.text(x, 0.62, number, ha="center", va="center", fontsize=6.25, color=color, fontweight="bold")
        ax.text(x, 0.69, title, ha="center", va="center", fontsize=7.1, color=INK, fontweight="bold")
        ax.text(x, 0.235, detail, ha="center", va="center", fontsize=6.6, color=INK)
    export(fig, "overview_evidence_map")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    transfer, confirmation, audit = load_and_assert()
    overview()
    figure1(transfer)
    figure2(confirmation, audit)
    figure3(audit)
    print("v02 figures generated after canonical A3/A5/A7 assertions passed")


if __name__ == "__main__":
    main()
