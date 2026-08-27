"""Shared style and export helpers for the evidence-locked paper figures."""
from __future__ import annotations

from pathlib import Path

import altair as alt

FONT = "Arial"
INK = "#172B4D"
BLUE = "#2F78B7"
SLATE = "#8A99A6"
AMBER = "#D6A12A"
CORAL = "#D95D51"
GRID = "#E5EBF0"
LINE = "#B7C4CE"
WHITE = "#FFFFFF"


def paper_style(chart: alt.TopLevelMixin) -> alt.TopLevelMixin:
    """Apply the shared, print-oriented visual language."""
    return (
        chart.configure_view(stroke=WHITE, fill=WHITE)
        .configure_axis(
            labelFont=FONT,
            labelFontSize=9,
            labelColor=INK,
            titleFont=FONT,
            titleFontSize=9,
            titleFontWeight="normal",
            titleColor=INK,
            domainColor=LINE,
            tickColor=LINE,
            gridColor=GRID,
            gridOpacity=0.8,
            tickSize=3,
        )
        .configure_title(
            font=FONT,
            fontSize=11,
            fontWeight="bold",
            color=INK,
            anchor="start",
            offset=7,
        )
        .configure_legend(
            labelFont=FONT,
            labelFontSize=8.5,
            titleFont=FONT,
            titleFontSize=8.5,
            titleColor=INK,
            labelColor=INK,
            symbolSize=60,
            padding=0,
        )
        .configure(background=WHITE)
    )


def export_chart(chart: alt.TopLevelMixin, stem: Path) -> None:
    """Write editable SVG/PDF plus a 360-dpi-equivalent PNG preview."""
    stem.parent.mkdir(parents=True, exist_ok=True)
    chart.save(stem.with_suffix(".svg"))
    chart.save(stem.with_suffix(".pdf"))
    # Vega-Lite's base resolution is 72 dpi; factor five yields 360 dpi.
    chart.save(stem.with_suffix(".png"), scale_factor=5)
