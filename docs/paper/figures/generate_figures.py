from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tables" / "a7-layer-aggregate-metrics.csv"
OUTPUT = ROOT / "figures" / "isainlp2026"

CHARCOAL = "#252A2E"
BLUE = "#2B5D7D"
TEAL = "#3A7D78"
GOLD = "#C49332"
LIGHT_GRAY = "#D7DADD"
MID_GRAY = "#7A8187"
PAPER = "#FFFFFF"


def load_metrics() -> dict[tuple[str, str, str], Decimal]:
    metrics: dict[tuple[str, str, str], Decimal] = {}
    with DATA.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            try:
                value = Decimal(row["value"])
            except Exception:
                continue
            metrics[(row["layer"], row["population"], row["metric"])] = value
    return metrics


def checked(metrics: dict[tuple[str, str, str], Decimal], key, expected: str) -> float:
    value = metrics[key]
    if value != Decimal(expected):
        raise ValueError(f"Canonical value changed for {key}: {value} != {expected}")
    return float(value)


def save(fig: plt.Figure, stem: str) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    metadata = {"Title": stem, "Author": "Anonymous", "Creator": "Matplotlib"}
    fig.savefig(OUTPUT / f"{stem}.pdf", bbox_inches="tight", metadata=metadata)
    fig.savefig(OUTPUT / f"{stem}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def evidence_chain() -> None:
    fig, ax = plt.subplots(figsize=(7.16, 1.48))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    stages = [
        (0.015, 0.28, 0.275, 0.56, BLUE, "A5  CONFIRM", "872 held-out OUT queries", "Frozen dense vs. BM25"),
        (0.365, 0.28, 0.275, 0.56, TEAL, "A6  MATERIALIZE", "45,336 documents / 1,247 queries", "Immutable family Top-200 pool"),
        (0.715, 0.28, 0.27, 0.56, GOLD, "A7  AUDIT", "Same pool; no reselection", "Exposure counts + oracle bound"),
    ]

    for idx, (x, y, w, h, color, title, line1, line2) in enumerate(stages):
        linestyle = "--" if idx == 2 else "-"
        ax.add_patch(Rectangle((x, y), w, h, facecolor=PAPER, edgecolor=color,
                               linewidth=1.35, linestyle=linestyle))
        ax.add_patch(Rectangle((x, y), 0.012, h, facecolor=color, edgecolor=color))
        ax.text(x + 0.032, y + 0.40, title, color=color, fontsize=8.2,
                fontweight="bold", va="center")
        ax.text(x + 0.032, y + 0.235, line1, color=CHARCOAL, fontsize=7.2, va="center")
        ax.text(x + 0.032, y + 0.105, line2, color=CHARCOAL, fontsize=7.2, va="center")
        if idx < 2:
            ax.add_patch(FancyArrowPatch((x + w + 0.012, 0.56),
                                         (stages[idx + 1][0] - 0.012, 0.56),
                                         arrowstyle="-|>", mutation_scale=9,
                                         linewidth=1.1, color=MID_GRAY))

    ax.text(0.015, 0.08,
            "Selection closes before the held-out comparison; A6 and A7 use zero selection/final accesses.",
            fontsize=7.0, color=CHARCOAL, va="center")
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    save(fig, "evidence_chain")


def out_domain_diagnosis(metrics: dict[tuple[str, str, str], Decimal]) -> None:
    exposed_100 = checked(metrics, ("A7-L6", "OUT", "relevant_family_exposed_at_100"), "796")
    deep_200 = checked(metrics, ("A7-L6", "OUT", "relevant_family_deep_ranked_101_to_200"), "332")
    absent_200 = checked(metrics, ("A7-L6", "OUT", "relevant_family_not_exposed_at_200"), "4065")
    total = checked(metrics, ("A7-L6", "OUT", "relevant_family_count"), "5193")
    observed = checked(metrics, ("A7-L7", "OUT", "observed_Recall@100"), "0.188449898653")
    oracle = checked(metrics, ("A7-L7", "OUT", "existing_top_200_oracle_Recall@100"), "0.260166940437")
    headroom = checked(metrics, ("A7-L7", "OUT", "bounded_reranking_headroom_Recall@100"), "0.071717041784")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.16, 2.45),
                                   gridspec_kw={"width_ratios": [1.3, 1.0]})

    segments = [
        (exposed_100, BLUE, "", "Exposed by rank 100"),
        (deep_200, GOLD, "///", "First exposed at ranks 101-200"),
        (absent_200, LIGHT_GRAY, "...", "Absent at rank 200"),
    ]
    left = 0.0
    short_labels = [r"$\leq 100$", "101-200", "absent at 200"]
    for (value, color, hatch, label), short_label in zip(segments, short_labels):
        ax1.barh([0], [value], left=left, height=0.42, color=color,
                 edgecolor=CHARCOAL, linewidth=0.6, hatch=hatch, label=label)
        text_color = PAPER if color in {BLUE, TEAL} else CHARCOAL
        if short_label == "101-200":
            center = left + value / 2
            ax1.plot([center, center], [0.23, 0.30], color=CHARCOAL, linewidth=0.65)
            ax1.text(center, 0.34, f"{int(value):,}", ha="center", va="bottom",
                     fontsize=7.2, fontweight="bold", color=CHARCOAL)
        else:
            ax1.text(left + value / 2, 0, f"{int(value):,}", ha="center", va="center",
                     fontsize=7.5, fontweight="bold", color=text_color)
        ax1.text(left + value / 2, -0.31, short_label, ha="center", va="top",
                 fontsize=6.3, color=CHARCOAL)
        left += value
    ax1.set_xlim(0, total)
    ax1.set_ylim(-0.62, 0.55)
    ax1.set_yticks([])
    ax1.set_xlabel("Relevant-family incidences (raw count)", fontsize=7.5)
    ax1.set_title("(a) Candidate availability in the OUT pool", loc="left",
                  fontsize=8.2, fontweight="bold", color=CHARCOAL)
    ax1.spines[["top", "right", "left"]].set_visible(False)
    ax1.tick_params(axis="x", labelsize=6.8, length=2.5)

    ax2.hlines(0, observed, oracle, color=TEAL, linewidth=3.0, zorder=1)
    ax2.scatter([observed], [0], s=46, marker="o", color=BLUE,
                edgecolor=CHARCOAL, linewidth=0.6, zorder=2)
    ax2.scatter([oracle], [0], s=52, marker="D", color=GOLD,
                edgecolor=CHARCOAL, linewidth=0.6, zorder=2)
    ax2.annotate(f"Observed\n{observed:.6f}", (observed, 0),
                 xytext=(0, -19), textcoords="offset points", ha="center",
                 va="top", fontsize=7.2, color=CHARCOAL)
    ax2.annotate(f"Fixed-pool oracle\n{oracle:.6f}", (oracle, 0),
                 xytext=(0, -19), textcoords="offset points", ha="center",
                 va="top", fontsize=7.2, color=CHARCOAL)
    ax2.text((observed + oracle) / 2, 0.08, f"+{headroom:.6f}",
             ha="center", va="bottom", fontsize=8.0, fontweight="bold", color=TEAL)
    ax2.text((observed + oracle) / 2, 0.055, "ordering upper bound",
             ha="center", va="bottom", fontsize=6.7, color=MID_GRAY)
    ax2.set_xlim(0.15, 0.30)
    ax2.set_ylim(-0.18, 0.18)
    ax2.set_yticks([])
    ax2.set_xlabel("Macro Recall@100", fontsize=7.5)
    ax2.set_title("(b) Ordering headroom in the same Top-200 pool", loc="left",
                  fontsize=8.2, fontweight="bold", color=CHARCOAL)
    ax2.spines[["top", "right", "left"]].set_visible(False)
    ax2.tick_params(axis="x", labelsize=6.8, length=2.5)

    fig.subplots_adjust(left=0.065, right=0.995, top=0.88, bottom=0.25, wspace=0.28)
    save(fig, "out_domain_diagnosis")


def main() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 7.5,
        "axes.edgecolor": CHARCOAL,
        "axes.labelcolor": CHARCOAL,
        "xtick.color": CHARCOAL,
        "ytick.color": CHARCOAL,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })
    metrics = load_metrics()
    evidence_chain()
    out_domain_diagnosis(metrics)


if __name__ == "__main__":
    main()
