"""Generate the frozen A3, A5, and A7 paper figures from canonical CSVs."""
from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path

import altair as alt

from paper_style import AMBER, BLUE, FONT, INK, LINE, SLATE, CORAL, WHITE, export_chart, paper_style

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "prism-uploads" / "myIS_prism_csv_pack_20260826.zip"
PREFIX = "myIS_prism_csv_pack_20260826/prism_ready/"
OUT = ROOT / "figures" / "rebuilt"

SOURCE_ORDER = ["PatEmbed", "Arctic", "Qwen3"]
TARGET_ORDER = ["PatEmbed", "Arctic", "Qwen3"]
SHORT = {
    "PatEmbed": "PatEmbed",
    "Arctic Embed": "Arctic",
    "Qwen3 Embedding": "Qwen3",
}
SHAPES = ["circle", "square", "diamond"]


def csv_rows(member: str) -> list[dict[str, str]]:
    with zipfile.ZipFile(ARCHIVE) as zf:
        raw = zf.read(PREFIX + member).decode("utf-8")
    return list(csv.DictReader(io.StringIO(raw)))


def assert_frozen_values() -> dict[tuple[str, str], float]:
    rows = csv_rows("fig1_a3_transfer.csv")
    values = {
        (row["representation_source"], row["target_retriever"]): float(row["Recall@100"])
        for row in rows
    }
    expected = {
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
    assert values == expected

    a5 = {row["metric"]: row for row in csv_rows("fig2_a5_confirmation.csv")}
    assert round(float(a5["Recall@100"]["paired_difference"]), 6) == 0.111379
    assert round(float(a5["nDCG@100"]["paired_difference"]), 6) == 0.086342
    outcomes = csv_rows("fig2_a5_recall_wtl.csv")
    assert [(row["outcome"], int(row["count"])) for row in outcomes] == [
        ("win", 619), ("tie", 158), ("loss", 95)
    ]

    a7 = {row["state"]: float(row["value"]) for row in csv_rows("fig3_a7_out_diagnosis.csv")}
    assert a7["absent_at_rank_200"] == 4065
    assert round(a7["observed_Recall@100"], 6) == 0.188450
    assert round(a7["fixed_pool_oracle_Recall@100"], 6) == 0.260167
    assert round(a7["bounded_ordering_headroom_Recall@100"], 6) == 0.071717
    return values


def transfer_data(values: dict[tuple[str, str], float]) -> tuple[list[dict], list[dict]]:
    raw_sources = ["PatEmbed", "Arctic Embed", "Qwen3 Embedding"]
    raw_targets = ["PatEmbed", "Arctic Embed", "Qwen3 Embedding"]
    points: list[dict] = []
    bands: list[dict] = []
    for target in raw_targets:
        scores = [values[(source, target)] for source in raw_sources]
        matched = values[(target, target)]
        best = max(scores)
        short_target = SHORT[target]
        bands.append(
            {
                "target": short_target,
                "low": min(scores),
                "high": max(scores),
                "range_label": f"range {max(scores) - min(scores):.6f}",
            }
        )
        for source in raw_sources:
            score = values[(source, target)]
            points.append(
                {
                    "source": SHORT[source],
                    "target": short_target,
                    "score": score,
                    "delta": score - matched,
                    "nominal_best": score == best,
                    "matched": source == target,
                }
            )
    return points, bands


def fig1_transfer(values: dict[tuple[str, str], float]) -> alt.TopLevelMixin:
    points, bands = transfer_data(values)
    source_shape = alt.Shape(
        "source:N",
        sort=SOURCE_ORDER,
        scale=alt.Scale(domain=SOURCE_ORDER, range=SHAPES),
        legend=alt.Legend(title="Representation source", orient="top"),
    )

    band = alt.Chart(alt.Data(values=bands)).mark_rule(
        color=LINE, strokeWidth=4, strokeCap="round"
    ).encode(
        x=alt.X("low:Q", scale=alt.Scale(domain=[0.33, 0.425], nice=False), axis=None),
        x2="high:Q",
        y=alt.Y("target:N", sort=TARGET_ORDER, title=None),
    )
    ordinary = alt.Chart(alt.Data(values=points)).mark_point(
        filled=True, size=65, color=SLATE, stroke=WHITE, strokeWidth=0.8
    ).encode(
        x=alt.X(
            "score:Q",
            scale=alt.Scale(domain=[0.33, 0.425], nice=False),
            axis=alt.Axis(title="Recall@100 (common scale)", format=".2f", values=[0.34, 0.38, 0.42]),
        ),
        y=alt.Y("target:N", sort=TARGET_ORDER, title=None),
        shape=source_shape,
    )
    best = alt.Chart(alt.Data(values=points)).transform_filter(
        alt.datum.nominal_best
    ).mark_point(filled=True, size=76, color=AMBER, stroke=WHITE, strokeWidth=0.8).encode(
        x=alt.X("score:Q", scale=alt.Scale(domain=[0.33, 0.425], nice=False), axis=None),
        y=alt.Y("target:N", sort=TARGET_ORDER, title=None),
        shape=source_shape,
    )
    matched = alt.Chart(alt.Data(values=points)).transform_filter(
        alt.datum.matched
    ).mark_point(filled=False, size=160, stroke=INK, strokeWidth=1.2).encode(
        x=alt.X("score:Q", scale=alt.Scale(domain=[0.33, 0.425], nice=False), axis=None),
        y=alt.Y("target:N", sort=TARGET_ORDER, title=None),
        shape=source_shape,
    )
    range_labels = alt.Chart(alt.Data(values=bands)).mark_text(
        align="right", dx=-2, dy=-13, font=FONT, fontSize=8.5, color=INK
    ).encode(
        x=alt.X("high:Q", scale=alt.Scale(domain=[0.33, 0.425], nice=False), axis=None),
        y=alt.Y("target:N", sort=TARGET_ORDER, axis=None),
        text="range_label:N",
    )
    absolute = (band + ordinary + best + matched + range_labels).properties(
        width=516, height=105, title="A  Absolute target score bands"
    )

    delta_panels = []
    for index, target in enumerate(TARGET_ORDER):
        target_points = [point for point in points if point["target"] == target]
        zero = alt.Chart(alt.Data(values=[{"zero": 0}])).mark_rule(
            color=LINE, strokeWidth=1.1
        ).encode(x=alt.X("zero:Q", scale=alt.Scale(domain=[-0.0042, 0.0022], nice=False), axis=None))
        dots = alt.Chart(alt.Data(values=target_points)).mark_point(
            filled=True, size=60, color=SLATE, stroke=WHITE, strokeWidth=0.8
        ).encode(
            x=alt.X(
                "delta:Q",
                scale=alt.Scale(domain=[-0.0042, 0.0022], nice=False),
                axis=alt.Axis(
                    title="Score - matched" if index == 1 else None,
                    format="+.3f",
                    values=[-0.004, 0, 0.002],
                    labels=index == 1,
                    ticks=index == 1,
                    domain=index == 1,
                ),
            ),
            y=alt.Y("source:N", sort=SOURCE_ORDER, title=None, axis=alt.Axis(labels=index == 0, ticks=index == 0, domain=index == 0)),
            shape=alt.Shape("source:N", sort=SOURCE_ORDER, scale=alt.Scale(domain=SOURCE_ORDER, range=SHAPES), legend=None),
        )
        delta_best = alt.Chart(alt.Data(values=target_points)).transform_filter(
            alt.datum.nominal_best
        ).mark_point(filled=True, size=70, color=AMBER, stroke=WHITE, strokeWidth=0.8).encode(
            x=alt.X("delta:Q", scale=alt.Scale(domain=[-0.0042, 0.0022], nice=False), axis=None),
            y=alt.Y("source:N", sort=SOURCE_ORDER, axis=None),
            shape=alt.Shape("source:N", sort=SOURCE_ORDER, scale=alt.Scale(domain=SOURCE_ORDER, range=SHAPES), legend=None),
        )
        delta_matched = alt.Chart(alt.Data(values=target_points)).transform_filter(
            alt.datum.matched
        ).mark_point(filled=False, size=150, stroke=INK, strokeWidth=1.2).encode(
            x=alt.X("delta:Q", scale=alt.Scale(domain=[-0.0042, 0.0022], nice=False), axis=None),
            y=alt.Y("source:N", sort=SOURCE_ORDER, axis=None),
            shape=alt.Shape("source:N", sort=SOURCE_ORDER, scale=alt.Scale(domain=SOURCE_ORDER, range=SHAPES), legend=None),
        )
        delta_panels.append((zero + dots + delta_best + delta_matched).properties(
            width=160, height=75, title=f"{target} target"
        ))
    transfer = alt.hconcat(*delta_panels, spacing=18).properties(title="B  Transfer relative to the matched representation")
    note = alt.Chart(alt.Data(values=[{
        "note": "Amber: nominal best. Dark outline: matched source-target pair. Small ranges are descriptive development evidence."
    }])).mark_text(align="left", font=FONT, fontSize=8.5, color=INK).encode(
        text="note:N"
    ).properties(width=516, height=13)
    return paper_style(alt.vconcat(absolute, transfer, note, spacing=7).resolve_scale(x="independent", y="independent"))


def fig2_confirmation() -> alt.TopLevelMixin:
    rows = [row for row in csv_rows("fig2_a5_confirmation.csv") if row["metric"] in {"Recall@100", "nDCG@100"}]
    metric_order = ["Recall@100", "nDCG@100"]
    absolute, effects = [], []
    for row in rows:
        absolute.extend([
            {"metric": row["metric"], "system": "Comparator", "value": float(row["static_comparator"]), "label": f"{float(row['static_comparator']):.6f}"},
            {"metric": row["metric"], "system": "Selected", "value": float(row["selected_research"]), "label": f"{float(row['selected_research']):.6f}"},
        ])
        effects.append({
            "metric": row["metric"], "diff": float(row["paired_difference"]),
            "low": float(row["ci95_low"]), "high": float(row["ci95_high"]),
            "label": f"+{float(row['paired_difference']):.6f}",
        })
    links = alt.Chart(alt.Data(values=rows)).mark_rule(
        color=LINE, strokeWidth=3, strokeCap="round"
    ).encode(
        x=alt.X("static_comparator:Q", scale=alt.Scale(domain=[0.25, 0.47], nice=False), axis=None),
        x2="selected_research:Q", y=alt.Y("metric:N", sort=metric_order, title=None),
    )
    perf = alt.Chart(alt.Data(values=absolute)).mark_point(
        filled=True, size=78, stroke=WHITE, strokeWidth=0.9
    ).encode(
        x=alt.X("value:Q", scale=alt.Scale(domain=[0.25, 0.47], nice=False), axis=alt.Axis(title="Score", format=".2f", values=[0.30, 0.38, 0.46])),
        y=alt.Y("metric:N", sort=metric_order, title=None),
        color=alt.Color("system:N", scale=alt.Scale(domain=["Comparator", "Selected"], range=[SLATE, BLUE]), legend=None),
    )
    perf_label = alt.Chart(alt.Data(values=absolute)).mark_text(
        dy=-13, font=FONT, fontSize=8.1, color=INK
    ).encode(
        x=alt.X("value:Q", scale=alt.Scale(domain=[0.25, 0.47], nice=False), axis=None),
        y=alt.Y("metric:N", sort=metric_order, axis=None), text="label:N",
    )
    panel_a = (links + perf + perf_label).properties(
        width=154, height=82, title="A  Absolute performance"
    )

    zero = alt.Chart(alt.Data(values=[{"zero": 0}])).mark_rule(color=INK, strokeWidth=1).encode(
        x=alt.X("zero:Q", scale=alt.Scale(domain=[0, 0.13], nice=False), axis=None)
    )
    ci = alt.Chart(alt.Data(values=effects)).mark_rule(
        color=BLUE, strokeWidth=3, strokeCap="round"
    ).encode(
        x=alt.X("low:Q", scale=alt.Scale(domain=[0, 0.13], nice=False), axis=alt.Axis(title="Selected - comparator", format=".02f", values=[0, 0.06, 0.12])),
        x2="high:Q", y=alt.Y("metric:N", sort=metric_order, title=None),
    )
    caps_low = alt.Chart(alt.Data(values=effects)).mark_tick(color=BLUE, thickness=1.7, size=13).encode(
        x=alt.X("low:Q", scale=alt.Scale(domain=[0, 0.13], nice=False), axis=None), y=alt.Y("metric:N", sort=metric_order, axis=None)
    )
    caps_high = alt.Chart(alt.Data(values=effects)).mark_tick(color=BLUE, thickness=1.7, size=13).encode(
        x=alt.X("high:Q", scale=alt.Scale(domain=[0, 0.13], nice=False), axis=None), y=alt.Y("metric:N", sort=metric_order, axis=None)
    )
    effect = alt.Chart(alt.Data(values=effects)).mark_point(filled=True, color=BLUE, size=90, stroke=WHITE, strokeWidth=0.8).encode(
        x=alt.X("diff:Q", scale=alt.Scale(domain=[0, 0.13], nice=False), axis=None), y=alt.Y("metric:N", sort=metric_order, axis=None)
    )
    effect_label = alt.Chart(alt.Data(values=effects)).mark_text(
        dy=-14, font=FONT, fontSize=8.9, fontWeight="bold", color=INK
    ).encode(
        x=alt.X("diff:Q", scale=alt.Scale(domain=[0, 0.13], nice=False), axis=None), y=alt.Y("metric:N", sort=metric_order, axis=None), text="label:N"
    )
    panel_b = (zero + ci + caps_low + caps_high + effect + effect_label).properties(
        width=185, height=82, title="B  Paired effects + 95% CI"
    )

    total = 872
    start = 0
    outcomes = []
    for outcome, count, color in [("Win", 619, BLUE), ("Tie", 158, SLATE), ("Loss", 95, CORAL)]:
        outcomes.append({"outcome": outcome, "count": count, "start": start, "end": start + count, "mid": start + count / 2, "color": color, "label": f"{outcome} {count}"})
        start += count
    outcome_chart = alt.Chart(alt.Data(values=outcomes))
    strip = outcome_chart.mark_rect().encode(
        x=alt.X("start:Q", scale=alt.Scale(domain=[0, total], nice=False), axis=None),
        x2="end:Q", y=alt.value(23), y2=alt.value(57), color=alt.Color("color:N", scale=None, legend=None),
    )
    strip_outline = alt.Chart(alt.Data(values=[{"start": 0, "end": total}])).mark_rect(
        fillOpacity=0, stroke=INK, strokeWidth=0.8, cornerRadius=6
    ).encode(
        x=alt.X("start:Q", scale=alt.Scale(domain=[0, total], nice=False), axis=None), x2="end:Q", y=alt.value(23), y2=alt.value(57)
    )
    strip_labels = outcome_chart.mark_text(color=WHITE, font=FONT, fontSize=7.6, fontWeight="bold").encode(
        x=alt.X("mid:Q", scale=alt.Scale(domain=[0, total], nice=False), axis=None), y=alt.value(40), text="label:N"
    )
    panel_c = (strip + strip_outline + strip_labels).properties(
        width=153, height=82, title="C  Recall W/T/L (n=872)"
    )
    note = alt.Chart(alt.Data(values=[{"note": "Gray: comparator / tie. Blue: selected system / win. Coral: loss."}])).mark_text(
        align="left", font=FONT, fontSize=8.5, color=INK
    ).encode(text="note:N").properties(width=516, height=12)
    return paper_style(alt.vconcat(alt.hconcat(panel_a, panel_b, panel_c, spacing=12), note, spacing=5).resolve_scale(x="independent", y="independent"))


def fig3_diagnosis() -> alt.TopLevelMixin:
    total = 5193
    parts = []
    start = 0
    for state, count, color, pct in [
        ("By rank 100", 796, BLUE, "15.3%"),
        ("First at 101-200", 332, SLATE, "6.4%"),
        ("Absent from Top-200", 4065, CORAL, "78.3%"),
    ]:
        parts.append({"state": state, "count": count, "start": start, "end": start + count, "mid": start + count / 2, "color": color, "pct": pct})
        start += count
    part_chart = alt.Chart(alt.Data(values=parts))
    exposure = part_chart.mark_rect().encode(
        x=alt.X("start:Q", scale=alt.Scale(domain=[0, total], nice=False), axis=alt.Axis(title="Relevant-family incidences (n=5,193)", values=[0, total], grid=False)),
        x2="end:Q", y=alt.value(23), y2=alt.value(58), color=alt.Color("color:N", scale=None, legend=None),
    )
    exposure_outline = alt.Chart(alt.Data(values=[{"start": 0, "end": total}])).mark_rect(
        fillOpacity=0, stroke=INK, strokeWidth=0.8, cornerRadius=6
    ).encode(
        x=alt.X("start:Q", scale=alt.Scale(domain=[0, total], nice=False), axis=None), x2="end:Q", y=alt.value(23), y2=alt.value(58)
    )
    pct = part_chart.mark_text(color=WHITE, font=FONT, fontSize=8.2, fontWeight="bold").encode(
        x=alt.X("mid:Q", scale=alt.Scale(domain=[0, total], nice=False), axis=None), y=alt.value(40), text="pct:N"
    )
    absent = alt.Chart(alt.Data(values=[{"text": "4,065 / 5,193 absent from Top-200"}])).mark_text(
        align="left", font=FONT, fontSize=10, fontWeight="bold", color=CORAL
    ).encode(text="text:N").properties(width=265, height=13)
    panel_a = alt.vconcat(
        (exposure + exposure_outline + pct).properties(width=265, height=76, title="A  Candidate exposure anatomy"), absent, spacing=0
    )

    observed, bound = 0.188450, 0.260167
    interval = alt.Chart(alt.Data(values=[{"start": observed, "end": bound}])).mark_rule(
        color=LINE, strokeWidth=4, strokeCap="round"
    ).encode(
        x=alt.X("start:Q", scale=alt.Scale(domain=[0.17, 0.275], nice=False), axis=alt.Axis(title="Macro Recall@100 (n=905)", format=".2f", values=[0.18, 0.22, 0.26])), x2="end:Q", y=alt.value(42)
    )
    observed_mark = alt.Chart(alt.Data(values=[{"value": observed}])).mark_point(
        filled=True, color=BLUE, size=105, stroke=WHITE, strokeWidth=0.9
    ).encode(x=alt.X("value:Q", scale=alt.Scale(domain=[0.17, 0.275], nice=False), axis=None), y=alt.value(42))
    bound_mark = alt.Chart(alt.Data(values=[{"value": bound}])).mark_point(
        filled=True, color=AMBER, size=105, stroke=WHITE, strokeWidth=0.9
    ).encode(x=alt.X("value:Q", scale=alt.Scale(domain=[0.17, 0.275], nice=False), axis=None), y=alt.value(42))
    point_labels = alt.Chart(alt.Data(values=[
        {"value": observed, "label": "Observed  0.188450"},
        {"value": bound, "label": "Perfect-ordering bound  0.260167"},
    ])).mark_text(align="center", dy=-15, font=FONT, fontSize=8.2, color=INK).encode(
        x=alt.X("value:Q", scale=alt.Scale(domain=[0.17, 0.275], nice=False), axis=None), y=alt.value(42), text="label:N"
    )
    headroom = alt.Chart(alt.Data(values=[{"mid": (observed + bound) / 2, "label": "+0.071717 headroom"}])).mark_text(
        align="center", dy=20, font=FONT, fontSize=9, fontWeight="bold", color=AMBER
    ).encode(x=alt.X("mid:Q", scale=alt.Scale(domain=[0.17, 0.275], nice=False), axis=None), y=alt.value(42), text="label:N")
    panel_b = (interval + observed_mark + bound_mark + point_labels + headroom).properties(
        width=239, height=89, title="B  Within-pool ordering bound"
    )
    note = alt.Chart(alt.Data(values=[{"note": "A: incidence proportions. B: query-averaged Recall; perfect ordering is an analytical fixed-pool bound."}])).mark_text(
        align="left", font=FONT, fontSize=8.5, color=INK
    ).encode(text="note:N").properties(width=516, height=12)
    return paper_style(alt.vconcat(alt.hconcat(panel_a, panel_b, spacing=12), note, spacing=3).resolve_scale(x="independent", y="independent"))


def main() -> None:
    alt.data_transformers.disable_max_rows()
    values = assert_frozen_values()
    export_chart(fig1_transfer(values), OUT / "fig1_a3_transfer")
    export_chart(fig2_confirmation(), OUT / "fig2_a5_confirmation")
    export_chart(fig3_diagnosis(), OUT / "fig3_a7_diagnosis")


if __name__ == "__main__":
    main()
