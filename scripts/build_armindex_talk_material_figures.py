"""Render aggregate-safe SVG figures for the ArmIndex advisor talk material.

This generator deliberately reads only public controls and the validated A1
aggregate cell table. It never opens Owner-local benchmark content, qrels,
per-query outputs, or A2 candidate result files.
"""

from __future__ import annotations

import csv
import html
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "presentation" / "material" / "figures"
A1_TABLE = ROOT / "outputs" / "tables" / "armindex" / "a12-v16-20260811-r15.cell-eda.v16.csv"

W = 1600
H = 900
BG = "#f7f8f7"
INK = "#18232b"
MUTED = "#5d6b73"
TEAL = "#007f7b"
BLUE = "#2463a5"
GOLD = "#c67c00"
RED = "#b94a5a"
GREEN = "#23815d"
PALE_TEAL = "#e0f0ee"
PALE_BLUE = "#e4edf8"
PALE_GOLD = "#fbefd8"
PALE_RED = "#f8e6e8"
WHITE = "#ffffff"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def svg(parts: list[str]) -> str:
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
            '<style>text{font-family:Arial,Helvetica,sans-serif;letter-spacing:0} .t{fill:#18232b} .m{fill:#5d6b73} .s{font-size:22px} .b{font-size:30px;font-weight:700} .h{font-size:42px;font-weight:700} .k{font-size:18px;font-weight:700;letter-spacing:1.5px}</style>',
            f'<rect width="{W}" height="{H}" fill="{BG}"/>',
            *parts,
            "</svg>",
        ]
    )


def text(x: float, y: float, value: str, css: str = "s t", anchor: str = "start") -> str:
    return f'<text x="{x}" y="{y}" class="{css}" text-anchor="{anchor}">{esc(value)}</text>'


def text_lines(x: float, y: float, values: list[str], css: str = "s t", anchor: str = "start", gap: int = 30) -> list[str]:
    return [text(x, y + index * gap, value, css, anchor) for index, value in enumerate(values)]


def rect(x: float, y: float, width: float, height: float, fill: str = WHITE, stroke: str = "#d5dcde", radius: int = 10) -> str:
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'


def line(x1: float, y1: float, x2: float, y2: float, stroke: str = MUTED, width: int = 4) -> str:
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{width}" stroke-linecap="round"/>'


def arrow(x1: float, y1: float, x2: float, y2: float, stroke: str = MUTED) -> list[str]:
    if x2 >= x1:
        head = f'<path d="M {x2 - 16} {y2 - 10} L {x2} {y2} L {x2 - 16} {y2 + 10}" fill="none" stroke="{stroke}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
    else:
        head = f'<path d="M {x2 + 16} {y2 - 10} L {x2} {y2} L {x2 + 16} {y2 + 10}" fill="none" stroke="{stroke}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
    return [line(x1, y1, x2, y2, stroke), head]


def title(parts: list[str], kicker: str, heading: str, note: str) -> None:
    parts.extend(
        [
            text(90, 80, kicker.upper(), "k", "start"),
            text(90, 145, heading, "h t", "start"),
            text(90, 188, note, "s m", "start"),
            line(90, 220, 1510, 220, "#ccd5d8", 2),
        ]
    )


def write(name: str, parts: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(svg(parts), encoding="utf-8")


def dapfam_anatomy() -> None:
    parts: list[str] = []
    title(parts, "Dataset and evaluation unit", "DAPFAM evaluates cross-domain retrieval at patent-family level", "Schema and counts are aggregate-safe; no patent row, query ID, or qrels are shown.")
    parts.extend(
        [
            rect(90, 275, 440, 430, PALE_TEAL, TEAL),
            text(125, 330, "One target patent family", "b t"),
            rect(125, 370, 370, 72, WHITE, "#b7d6d2"),
            text(150, 415, "TITLE", "k", "start"),
            rect(125, 462, 370, 72, WHITE, "#b7d6d2"),
            text(150, 507, "ABSTRACT", "k", "start"),
            rect(125, 554, 370, 108, WHITE, "#b7d6d2"),
            text(150, 599, "CLAIMS", "k", "start"),
            text(150, 634, "Structured claim text is preserved Owner-local.", "s m", "start"),
            text(310, 748, "Family is the retrieval unit", "b t", "middle"),
            rect(610, 275, 390, 150, PALE_BLUE, BLUE),
            text(805, 330, "45,336", "h t", "middle"),
            text(805, 375, "target families", "b t", "middle"),
            rect(610, 450, 390, 150, PALE_GOLD, GOLD),
            text(805, 505, "1,247", "h t", "middle"),
            text(805, 550, "query families", "b t", "middle"),
            rect(610, 625, 390, 150, PALE_RED, RED),
            text(805, 680, "49,869", "h t", "middle"),
            text(805, 725, "(query, target, relevance, domain) rows", "b t", "middle"),
            rect(1080, 300, 390, 400, WHITE, "#d5dcde"),
            text(1120, 355, "Domain label", "b t"),
            text(1120, 405, "IN", "b", "start"),
            text(1210, 405, "at least one shared IPC3 code", "s m", "start"),
            text(1120, 475, "OUT", "b", "start"),
            text(1210, 475, "no shared IPC3 code", "s m", "start"),
            line(1120, 515, 1430, 515, "#d5dcde", 2),
            text(1120, 560, "What the labels mean", "b t"),
            text(1120, 605, "Citation-based relevance is an examiner proxy.", "s m", "start"),
            text(1120, 640, "It is not a novelty, validity, infringement,", "s m", "start"),
            text(1120, 675, "or freedom-to-operate determination.", "s m", "start"),
        ]
    )
    write("01_dapfam_family_record_anatomy.svg", parts)


def retrieval_pipeline() -> None:
    parts: list[str] = []
    title(parts, "Retrieval system", "Representation connects patent fields to a frozen retriever", "ArmIndex varies the document representation while keeping evaluation, model adapters, and metrics controlled.")
    boxes = [
        (90, 350, 210, 165, PALE_TEAL, "Patent family", ["title", "abstract", "claims"]),
        (350, 350, 240, 165, PALE_BLUE, "Representation", ["document", "claim", "passages", "three views"]),
        (640, 350, 220, 165, PALE_GOLD, "Retriever arm", ["BM25 or", "dense embedding", "fixed adapter"]),
        (910, 350, 220, 165, PALE_RED, "Family ranking", ["MaxP or", "view RRF", "top 100"]),
        (1180, 350, 260, 165, "#e6efe8", "Evaluation", ["OUT Recall@100", "nDCG@100", "latency and cost"]),
    ]
    for x, y, width, height, fill, heading, lines in boxes:
        parts.append(rect(x, y, width, height, fill, "#cbd5d7"))
        parts.append(text(x + width / 2, y + 55, heading, "b t", "middle"))
        for index, value in enumerate(lines):
            parts.append(text(x + width / 2, y + 95 + index * 28, value, "s m", "middle"))
    for left, right in zip(boxes, boxes[1:]):
        parts.extend(arrow(left[0] + left[2] + 10, 432, right[0] - 16, 432, TEAL))
    parts.extend(
        [
            rect(160, 630, 1280, 110, WHITE, "#d5dcde"),
            text(200, 678, "Design rule", "b t"),
            *text_lines(430, 670, ["A1 compares five programs across five arms. A2 searches frozen candidates per arm.", "A3 tests transfer and complementarity only after A2 closes."], "s m", "start", 28),
            text(800, 812, "No LLM is required in the synchronous production retrieval path.", "b t", "middle"),
        ]
    )
    write("02_retrieval_system_stack.svg", parts)


def a0_split() -> None:
    parts: list[str] = []
    title(parts, "A0: data-role control", "The query-family split prevents later tuning on confirmation data", "Membership remains Owner-local; the figure shows only precommitted counts and permitted roles.")
    parts.extend(
        [
            rect(90, 300, 260, 300, PALE_BLUE, BLUE),
            text(220, 365, "1,247", "h t", "middle"),
            text(220, 415, "query families", "b t", "middle"),
            text(220, 465, "SHA-256 seeded", "s m", "middle"),
            text(220, 495, "split; seed 42", "s m", "middle"),
            *arrow(370, 450, 450, 450, TEAL),
            rect(470, 275, 290, 370, PALE_TEAL, TEAL),
            text(615, 340, "Train-250", "h t", "middle"),
            text(615, 385, "development only", "b t", "middle"),
            line(510, 420, 720, 420, "#9acbc6", 2),
            text(615, 470, "REP-DEV 150", "b t", "middle"),
            text(615, 505, "A1 common screen and A2", "s m", "middle"),
            text(615, 560, "HARNESS-DEV 100", "b t", "middle"),
            text(615, 595, "A3 transfer and HarnessOpt", "s m", "middle"),
            *arrow(780, 390, 850, 390, GOLD),
            rect(870, 275, 260, 370, PALE_GOLD, GOLD),
            text(1000, 340, "Selection-125", "b t", "middle"),
            text(1000, 390, "one atomic exposure", "s m", "middle"),
            text(1000, 440, "only frozen finalists", "s m", "middle"),
            text(1000, 500, "No post-exposure tuning", "b t", "middle"),
            *arrow(1150, 390, 1220, 390, RED),
            rect(1240, 275, 270, 370, PALE_RED, RED),
            text(1375, 340, "Final-872", "b t", "middle"),
            text(1375, 390, "sole confirmation", "s m", "middle"),
            text(1375, 440, "after D2_OPEN_FINAL", "s m", "middle"),
            text(1375, 500, "Closed now", "b t", "middle"),
            rect(170, 710, 1260, 80, WHITE, "#d5dcde"),
            *text_lines(800, 745, ["Stratify where possible by IN/OUT role-set and positive-relevance-count distribution.", "Preserve immutable grouping constraints."], "s m", "middle", 28),
        ]
    )
    write("03_a0_split_and_leakage_control.svg", parts)


def a1_programs() -> None:
    parts: list[str] = []
    title(parts, "A1: common representation screen", "Five deterministic programs vary the indexed patent-family view", "Each program is evaluated against every one of the five frozen retriever arms: 5 x 5 = 25 cells.")
    programs = [
        ("P00", "TAC document", ["Title + abstract", "+ claims"], PALE_TEAL, TEAL),
        ("P01", "TA document", ["Title + abstract"], PALE_BLUE, BLUE),
        ("P02", "First claim", ["First independent claim", "no fallback"], PALE_GOLD, GOLD),
        ("P03", "Fixed passages", ["384 tokens, 64 overlap", "family MaxP"], PALE_RED, RED),
        ("P04", "Three views", ["Title / abstract / claims", "RRF k=60"], "#e6efe8", GREEN),
    ]
    for index, (code, name, detail, fill, border) in enumerate(programs):
        x = 90 + index * 292
        parts.extend(
            [
                rect(x, 310, 260, 310, fill, border),
                text(x + 30, 360, code, "k", "start"),
                text(x + 130, 420, name, "b t", "middle"),
                *text_lines(x + 130, 480, detail, "s m", "middle", 28),
            ]
        )
    parts.extend(
        [
            rect(160, 700, 1280, 88, WHITE, "#d5dcde"),
            text(800, 748, "Interpretation rule: representations are deterministic data transformations, not LLM prompts. The arms use separately frozen embedding templates where applicable.", "s m", "middle"),
        ]
    )
    write("04_a1_representation_programs.svg", parts)


def a1_recall() -> None:
    sums: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    labels: dict[str, str] = {}
    with A1_TABLE.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            arm = row["arm_id"]
            sums[arm] += float(row["out_recall_at_100"])
            counts[arm] += 1
            labels[arm] = row["arm_label"]
    if sorted(counts.values()) != [5, 5, 5, 5, 5]:
        raise ValueError("A1 table must contain exactly five representation cells per arm")
    means = [(arm, sums[arm] / counts[arm], labels[arm]) for arm in sorted(sums)]
    parts: list[str] = []
    title(parts, "A1 result: REP-DEV", "A1 shows quality spread across frozen retriever arms", "Mean OUT Recall@100 across the five common programs; descriptive development evidence only, not Selection or Final confirmation.")
    x0, y0, chart_h, max_value = 220, 710, 390, 0.46
    parts.extend([line(x0, y0 - chart_h, x0, y0, INK, 3), line(x0, y0, 1450, y0, INK, 3)])
    for tick in (0.0, 0.1, 0.2, 0.3, 0.4):
        y = y0 - chart_h * tick / max_value
        parts.extend([line(x0 - 10, y, 1450, y, "#d9dfe1", 2), text(x0 - 25, y + 8, f"{tick:.1f}", "s m", "end")])
    colors = [TEAL, BLUE, GOLD, RED, GREEN]
    for index, (arm, value, label) in enumerate(means):
        x = 315 + index * 225
        height = chart_h * value / max_value
        y = y0 - height
        parts.extend(
            [
                f'<rect x="{x}" y="{y}" width="120" height="{height}" rx="6" fill="{colors[index]}"/>',
                text(x + 60, y - 18, f"{value:.3f}", "b t", "middle"),
                text(x + 60, y0 + 45, arm, "b t", "middle"),
                text(x + 60, y0 + 77, label.replace(" dense", ""), "s m", "middle"),
            ]
        )
    parts.extend(
        [
            rect(220, 770, 1230, 70, WHITE, "#d5dcde"),
            text(835, 815, "A1 payoff: model family and representation interact. A2 therefore searches a constrained representation candidate universe separately for each arm.", "s m", "middle"),
        ]
    )
    write("05_a1_mean_out_recall.svg", parts)


def a2_flow() -> None:
    parts: list[str] = []
    title(parts, "A2: per-arm AutoIndex", "A2 executes frozen candidates with auditable reserve admission", "This is a process diagram, not an A2 quality result. A2 interpretation remains blocked until closeout and independent audit.")
    boxes = [
        (80, 345, 220, 170, PALE_BLUE, BLUE, "52 frozen", ["representation", "candidates"]),
        (365, 345, 220, 170, PALE_TEAL, TEAL, "40 matched", ["candidate results", "durable checkpoints"]),
        (650, 345, 220, 170, PALE_GOLD, GOLD, "Matched barrier", ["fresh TTL and", "budget admission"]),
        (935, 345, 220, 170, PALE_RED, RED, "12 reserve", ["measure if admitted", "or issue dormant receipt"]),
        (1220, 345, 280, 170, "#e6efe8", GREEN, "Closeout", ["aggregate-safe return", "coverage + integrity audit"]),
    ]
    for x, y, width, height, fill, border, heading, detail in boxes:
        parts.append(rect(x, y, width, height, fill, border))
        parts.append(text(x + width / 2, y + 62, heading, "b t", "middle"))
        for row, value in enumerate(detail):
            parts.append(text(x + width / 2, y + 108 + row * 30, value, "s m", "middle"))
    for left, right in zip(boxes, boxes[1:]):
        parts.extend(arrow(left[0] + left[2] + 12, 430, right[0] - 18, 430, TEAL))
    parts.extend(
        [
            rect(170, 650, 1260, 100, WHITE, "#d5dcde"),
            text(800, 695, "Execution topology", "b t", "middle"),
            text(800, 730, "ARM-01 runs on CPU; ARM-02 through ARM-05 use disjoint GPUs. Every worker reports a heartbeat and candidate checkpoint.", "s m", "middle"),
            text(800, 820, "Current narrative status: A2 is live controlled execution. Do not state a winner, metric, or baseline comparison before valid closeout.", "b t", "middle"),
        ]
    )
    write("06_a2_execution_and_reserve_flow.svg", parts)


def a3_protocol() -> None:
    parts: list[str] = []
    title(parts, "A3 Extended: after A2 PASS", "A3 tests transfer and a bounded production harness", "Strictly PENDING_A2_CLOSEOUT. The figure represents the locked protocol, not a launched experiment or result.")
    parts.extend([rect(90, 285, 570, 475, WHITE, "#d5dcde"), text(375, 340, "5 x 5 winner-use matrix", "b t", "middle")])
    labels = ["A1", "A2", "A3", "A4", "A5"]
    for index, label in enumerate(labels):
        x = 230 + index * 75
        y = 405 + index * 55
        parts.append(text(x + 25, 390, label, "s m", "middle"))
        parts.append(text(190, y + 25, label, "s m", "middle"))
    for row in range(5):
        for column in range(5):
            x, y = 230 + column * 75, 405 + row * 55
            fill = PALE_TEAL if row == column else PALE_BLUE
            border = TEAL if row == column else BLUE
            parts.append(rect(x, y, 52, 38, fill, border, 4))
    parts.extend(
        [
            text(375, 710, "5 diagonal self reuses + up to 20 compatible off-diagonal transfers", "s m", "middle"),
            rect(760, 285, 680, 195, PALE_GOLD, GOLD),
            text(800, 340, "1. Fixed complementarity controls", "b t"),
            text(800, 385, "Equal-depth, preregistered unions before adaptive harness work.", "s m"),
            rect(760, 520, 680, 240, PALE_RED, RED),
            text(800, 575, "2. Bounded HarnessOpt", "b t"),
            text(800, 620, "At most 3 complete batches x 4 fixed roles:", "s m"),
            *text_lines(800, 655, ["quality exploit | cost/latency ablation", "routing hypothesis | diversity profile"], "s m", "start", 32),
            text(800, 715, "Train-250 adaptive; HARNESS-DEV aggregate-only and non-adaptive.", "s m"),
            *text_lines(800, 810, ["A3 gates: valid A2 coverage, five winner receipts, safe return, independent audit.", "Fresh provider quote and USD 35 cap are required."], "s t", "middle", 28),
        ]
    )
    write("07_a3_transfer_complementarity_harnessopt.svg", parts)


def main() -> None:
    dapfam_anatomy()
    retrieval_pipeline()
    a0_split()
    a1_programs()
    a1_recall()
    a2_flow()
    a3_protocol()
    print(f"Wrote 7 aggregate-safe SVG figures to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
