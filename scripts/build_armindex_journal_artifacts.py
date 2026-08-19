"""Build an aggregate-safe ArmIndex journal artifact package.

The allowlist is deliberate: this script copies only repository-safe figures,
EDA tables, and control/report projections. Owner-local protected payloads are
never read or copied.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import date
from pathlib import Path
from typing import Any


FIGURES = (
    "docs/progress_report/figures/a0-a2-publication-timeline.svg",
    "docs/progress_report/figures/a1-development-role-split.png",
    "docs/progress_report/figures/a1-common-screen-quality.png",
    "docs/progress_report/figures/a1-common-screen-efficiency.png",
    "docs/progress_report/figures/a2-per-arm-outcomes.png",
    "docs/progress_report/figures/a2-quality-latency-cost-frontier.png",
    "docs/progress_report/figures/a2-coverage-recovery.png",
    "docs/progress_report/figures/a2-matched-reserve-decision-path.png",
    "docs/progress_report/figures/a2-evidence-chain.png",
    "docs/progress_report/figures/a3-transfer-recall-heatmap-20260819.png",
    "docs/progress_report/figures/a3-fixed-control-quality-20260819.png",
    "outputs/figures/armindex/a12-v16-20260811-r15.quality-cell-eda.v16.svg",
    "outputs/figures/armindex/a12-v16-20260811-r15.efficiency-cell-eda.v16.svg",
    "outputs/figures/armindex/a2-goal004/a2-goal004-outcomes.svg",
    "outputs/figures/armindex/a2-goal004/a2-goal004-outcomes.pdf",
    "outputs/figures/armindex/a2-goal004/a2-goal004-quality-latency-cost-frontier.svg",
    "outputs/figures/armindex/a2-goal004/a2-goal004-quality-latency-cost-frontier.pdf",
    "outputs/figures/armindex/a2-goal004/a2-goal004-coverage-recovery.svg",
    "outputs/figures/armindex/a2-goal004/a2-goal004-coverage-recovery.pdf",
    "outputs/figures/armindex/a2-goal004/a2-goal004-matched-reserve-decision-path.svg",
    "outputs/figures/armindex/a2-goal004/a2-goal004-matched-reserve-decision-path.pdf",
)

TABLES = (
    "docs/progress_report/A0_A1_A2_figure_index_20260818.csv",
    "docs/progress_report/A0_A1_A2_phase_summary_figure_20260818.csv",
    "docs/progress_report/A0_A1_A2_metric_dictionary_20260818.csv",
    "docs/progress_report/A1_A2_quality_frontier_figure_20260818.csv",
    "docs/progress_report/A1_common_screen_aggregate_eda_20260818.csv",
    "docs/progress_report/A2_per_arm_autoindex_outcomes_eda_20260818.csv",
    "docs/progress_report/A3_transfer_matrix_eda_20260819.csv",
    "docs/progress_report/A3_fixed_controls_eda_20260819.csv",
    "outputs/tables/armindex/a12-v16-20260811-r15.cell-eda.v16.csv",
)

CLAIM_INVENTORY = (
    {
        "claim_id": "C-A0-01",
        "phase": "A0_MIGRATION_FOUNDATION",
        "claim_text": "The migration and evidence-foundation checks completed with aggregate-safe provenance controls.",
        "metric_scope": "engineering validation; no retrieval metric",
        "source_artifact": "campaigns/armindex-multiretriever-v2/evidence/a0-phase-closeout.receipt.v1.json",
        "evidence_status": "VERIFIED",
        "permitted_use": "Methods and reproducibility description",
        "prohibited_interpretation": "Do not present A0 as a retrieval-quality result",
    },
    {
        "claim_id": "C-A1-01",
        "phase": "A1_BASELINES_AND_MULTI_ARM_SCREENING",
        "claim_text": "Representation effects vary across retriever arms in the frozen 25-cell development screen.",
        "metric_scope": "OUT development aggregate; 25 cells; 150 queries per cell",
        "source_artifact": "campaigns/armindex-multiretriever-v2/evidence/a1.2-result-summaries/a12-v16-20260811-r15.summary.v16.json",
        "evidence_status": "VERIFIED",
        "permitted_use": "Development comparison and representation analysis",
        "prohibited_interpretation": "Do not call this universal, causal, or Final performance",
    },
    {
        "claim_id": "C-A2-01",
        "phase": "A2_PER_ARM_AUTOINDEX",
        "claim_text": "The authorized A2 candidate accounting is 52 total, 44 measured, eight dormant, and zero failed.",
        "metric_scope": "candidate accounting; development closeout",
        "source_artifact": "control/armindex/a2/a2-goal004-closeout-projection.v1.json",
        "evidence_status": "VERIFIED",
        "permitted_use": "Completeness and failure-taxonomy reporting",
        "prohibited_interpretation": "Dormant is not a zero-valued or failed retrieval result",
    },
    {
        "claim_id": "C-A2-02",
        "phase": "A2_PER_ARM_AUTOINDEX",
        "claim_text": "ARM-03, ARM-04, and ARM-05 advanced as primary transfer inputs; ARM-01 and ARM-02 remain diagnostic no-winner outcomes.",
        "metric_scope": "OUT development aggregate; per-arm closeout",
        "source_artifact": "docs/progress_report/A2_per_arm_autoindex_outcomes_eda_20260818.csv",
        "evidence_status": "VERIFIED",
        "permitted_use": "Predecessor-selection and diagnostic-boundary description",
        "prohibited_interpretation": "Do not treat the diagnostic arms as failed experiments",
    },
    {
        "claim_id": "C-A3-01",
        "phase": "A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT",
        "claim_text": "All nine source-program/target-adapter transfer cells completed 250 of 250 development units.",
        "metric_scope": "Train-250 development aggregate; OUT fields reported by the EDA table",
        "source_artifact": "docs/progress_report/A3_transfer_matrix_eda_20260819.csv",
        "evidence_status": "VERIFIED",
        "permitted_use": "Transfer-complementarity diagnostic",
        "prohibited_interpretation": "Do not claim external generalization or Selection evidence",
    },
    {
        "claim_id": "C-A3-02",
        "phase": "A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT",
        "claim_text": "The strongest observed transfer cell is ARM-05 source program to ARM-03 target adapter at OUT Recall@100 0.419274.",
        "metric_scope": "OUT development aggregate; 250 completed units",
        "source_artifact": "docs/progress_report/A3_transfer_matrix_eda_20260819.csv",
        "evidence_status": "VERIFIED",
        "permitted_use": "Bounded transfer result with explicit development qualifier",
        "prohibited_interpretation": "Do not label it a Final winner or a causal superiority claim",
    },
    {
        "claim_id": "C-A4-FAST-STATUS-01",
        "phase": "A4_PRODUCTION_TRANSFER_AND_SELECTION",
        "claim_text": "The FAST profile has a completed 100-unit Owner-local aggregate evaluation, but it is not a completed A4 result because the remaining profiles, legal isolation, and Selection are still incomplete.",
        "metric_scope": "profile-specific HDEV aggregate; population label is not exported in this package",
        "source_artifact": "<MYIS_ROOT>/04_Owner_Stores/armindex/a4/a4-goal001-20260819T073000Z-a4x5/hdev-evaluations/FAST.json",
        "evidence_status": "OWNER_LOCAL_STATUS_POINTER",
        "permitted_use": "Current-status reporting only; cite the numeric receipt only after complete A4 closeout",
        "prohibited_interpretation": "Do not call FAST a production winner, a commercial champion, Selection evidence, or Final evidence",
    },
    {
        "claim_id": "C-A4-01",
        "phase": "A4_PRODUCTION_TRANSFER_AND_SELECTION",
        "claim_text": "A4 is not complete at this package cutoff; FAST evidence exists but BALANCED, legal transfer, and Selection are not all closed.",
        "metric_scope": "phase status; no inferred metric population",
        "source_artifact": "control/armindex/a4/a4-readiness-binding-20260819.json",
        "evidence_status": "STATUS_POINTER",
        "permitted_use": "Current-status and next-gate reporting",
        "prohibited_interpretation": "Do not infer missing ALL/IN/OUT populations or open Selection",
    },
    {
        "claim_id": "C-A5-A6-01",
        "phase": "A5_FINAL_CONFIRMATION / A6_FULL_DAPFAM_MATERIALIZATION",
        "claim_text": "Full-corpus materialization is a post-confirmatory deployment phase and remains gated on PASS_A5_FINAL_CONFIRMATION.",
        "metric_scope": "phase contract and gate status",
        "source_artifact": "control/armindex/a6/a6-full-dapfam-execution-contract.v1.json",
        "evidence_status": "CONTRACT_VERIFIED",
        "permitted_use": "Protocol, limitations, and next-experiment gates",
        "prohibited_interpretation": "Do not report A6 scalability or quality results before its measured run",
    },
)

CONTROL_POINTERS = (
    "campaigns/armindex-multiretriever-v2/evidence/a0-phase-closeout.receipt.v1.json",
    "campaigns/armindex-multiretriever-v2/evidence/a1.2-result-summaries/a12-v16-20260811-r15.summary.v16.json",
    "control/armindex/a2/a2-goal004-closeout-projection.v1.json",
    "control/armindex/a4/a4-readiness-binding-20260819.json",
    "control/armindex/a5/a5-pending-a4-selection-template.v1.json",
    "control/armindex/a6/a6-a7-phase-amendment.v1.json",
    "control/armindex/a6/a6-full-dapfam-execution-contract.v1.json",
    "docs/goal/A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY_goal_001.md",
    "docs/goal/A7_PUBLICATION_AND_RELEASE_goal_001.md",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_value(repo: Path, args: list[str]) -> str:
    import subprocess

    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def copy_allowlist(repo: Path, output: Path, sources: tuple[str, ...], subdir: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for relative in sources:
        source = repo / relative
        if not source.is_file():
            raise FileNotFoundError(f"allowlisted artifact missing: {relative}")
        target = output / subdir / Path(relative).name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        records.append(
            {
                "source": relative.replace("\\", "/"),
                "package_path": target.relative_to(output).as_posix(),
                "bytes": target.stat().st_size,
                "sha256": sha256(target),
            }
        )
    return records


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def build_results_summary(repo: Path, output: Path) -> None:
    frontier = list(csv.DictReader((repo / "docs/progress_report/A1_A2_quality_frontier_figure_20260818.csv").open(encoding="utf-8")))
    a3 = list(csv.DictReader((repo / "docs/progress_report/A3_transfer_matrix_eda_20260819.csv").open(encoding="utf-8")))
    a3_fixed = list(csv.DictReader((repo / "docs/progress_report/A3_fixed_controls_eda_20260819.csv").open(encoding="utf-8")))
    lines = [
        "# ArmIndex aggregate result table",
        "",
        "This table is a manuscript working aid. Canonical numeric authority remains in the source manifests listed in `provenance/`.",
        "All retrieval values below are OUT development aggregates; they are not Final-872 evidence.",
        "",
        "## A1 to A2 per-arm Recall@100",
        "",
        "| Arm | Retriever | A1 | A2 | A2 disposition |",
        "|---|---|---:|---:|---|",
    ]
    by_arm: dict[str, dict[str, str]] = {}
    for row in frontier:
        by_arm.setdefault(row["arm_id"], {"label": row["arm_label"]})[row["stage"]] = row["value"]
    dispositions = {
        "ARM-01": "diagnostic tie; no winner",
        "ARM-02": "diagnostic tie; no winner",
        "ARM-03": "numerical tie to A1",
        "ARM-04": "strict improvement",
        "ARM-05": "no strict improvement",
    }
    for arm, row in by_arm.items():
        lines.append(f"| {arm} | {row['label']} | {row.get('A1', 'MISSING')} | {row.get('A2', 'MISSING')} | {dispositions[arm]} |")
    lines += [
        "",
        "## A3 transfer range",
        "",
        "| Source program | Target adapter | OUT Recall@100 | Units |",
        "|---|---|---:|---:|",
    ]
    for row in a3:
        lines.append(f"| {row['source_arm']} | {row['target_arm']} | {float(row['recall_at_100_out']):.6f} | {row['completed_units']}/{row['expected_units']} |")
    lines += [
        "",
        "## A3 fixed controls",
        "",
        "| Control | OUT Recall@100 | OUT nDCG@100 | Units |",
        "|---|---:|---:|---:|",
    ]
    for row in a3_fixed:
        lines.append(f"| {row['control']} | {float(row['recall_at_100_out']):.6f} | {float(row['ndcg_at_100_out']):.6f} | {row['completed_units']}/{row['expected_units']} |")
    write_text(output / "tables/results-summary.md", "\n".join(lines))


def build_claim_inventory(output: Path) -> list[dict[str, Any]]:
    path = output / "provenance/claim-inventory.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(CLAIM_INVENTORY[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(CLAIM_INVENTORY)
    return [{"source": "generated from canonical pointers and aggregate-safe EDA tables", "package_path": path.relative_to(output).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)}]


def build_a3_journal_figures(repo: Path, output: Path) -> list[dict[str, Any]]:
    """Render A3 vector and 300-dpi variants from aggregate EDA CSVs."""
    import matplotlib.pyplot as plt
    import numpy as np

    transfer = list(csv.DictReader((repo / "docs/progress_report/A3_transfer_matrix_eda_20260819.csv").open(encoding="utf-8")))
    fixed = list(csv.DictReader((repo / "docs/progress_report/A3_fixed_controls_eda_20260819.csv").open(encoding="utf-8")))
    arms = ("ARM-03", "ARM-04", "ARM-05")
    labels = {"ARM-03": "PatEmbed", "ARM-04": "Arctic Embed", "ARM-05": "Qwen3 Embedding"}
    figure_dir = output / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []

    matrix = np.array(
        [[next(float(r["recall_at_100_out"]) for r in transfer if r["source_arm"] == source and r["target_arm"] == target) for target in arms] for source in arms]
    )
    fig, ax = plt.subplots(figsize=(7.2, 5.6), constrained_layout=True)
    image = ax.imshow(matrix, cmap="YlGnBu", vmin=0.32, vmax=0.43)
    ax.set_xticks(range(3), [labels[a] for a in arms], rotation=20, ha="right")
    ax.set_yticks(range(3), [labels[a] for a in arms])
    ax.set_xlabel("Target retriever adapter")
    ax.set_ylabel("Source representation program")
    ax.set_title("Transfer quality varies by source program and target adapter")
    for row in range(3):
        for column in range(3):
            ax.text(column, row, f"{matrix[row, column]:.3f}", ha="center", va="center", color="black")
    fig.colorbar(image, ax=ax, label="OUT Recall@100")
    stem = figure_dir / "a3-transfer-recall-heatmap-journal"
    for suffix, kwargs in ((".png", {"dpi": 300}), (".svg", {}), (".pdf", {})):
        path = stem.with_suffix(suffix)
        fig.savefig(path, **kwargs)
        records.append({"source": "derived from docs/progress_report/A3_transfer_matrix_eda_20260819.csv", "package_path": path.relative_to(output).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)})
    plt.close(fig)

    names = [r["control"] for r in fixed]
    recall = [float(r["recall_at_100_out"]) for r in fixed]
    ndcg = [float(r["ndcg_at_100_out"]) for r in fixed]
    positions = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(9.0, 5.6), constrained_layout=True)
    width = 0.36
    ax.bar(positions - width / 2, recall, width, label="OUT Recall@100", color="#0F6CBD")
    ax.bar(positions + width / 2, ndcg, width, label="OUT nDCG@100", color="#2A6F4E")
    ax.set_xticks(positions, names, rotation=25, ha="right")
    ax.set_ylim(0.0, 0.45)
    ax.set_ylabel("Aggregate score")
    ax.set_title("Fixed controls retain a bounded development frontier")
    ax.legend(frameon=False)
    stem = figure_dir / "a3-fixed-control-quality-journal"
    for suffix, kwargs in ((".png", {"dpi": 300}), (".svg", {}), (".pdf", {})):
        path = stem.with_suffix(suffix)
        fig.savefig(path, **kwargs)
        records.append({"source": "derived from docs/progress_report/A3_fixed_controls_eda_20260819.csv", "package_path": path.relative_to(output).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)})
    plt.close(fig)
    return records


def build_a2_journal_figure(repo: Path, output: Path) -> list[dict[str, Any]]:
    """Render a paper-oriented A2 frontier with explicit arm dispositions."""
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    rows = list(csv.DictReader((repo / "docs/progress_report/A2_per_arm_autoindex_outcomes_eda_20260818.csv").open(encoding="utf-8")))
    labels = {
        "ARM-01": "BM25 lexical",
        "ARM-02": "BGE-M3",
        "ARM-03": "PatEmbed",
        "ARM-04": "Arctic Embed",
        "ARM-05": "Qwen3 Embedding",
    }
    colors = {"ARM-01": "#0072B2", "ARM-02": "#E69F00", "ARM-03": "#009E73", "ARM-04": "#CC79A7", "ARM-05": "#D55E00"}
    markers = {"ARM-01": "x", "ARM-02": "x", "ARM-03": "o", "ARM-04": "o", "ARM-05": "o"}
    fig, ax = plt.subplots(figsize=(8.4, 5.5), constrained_layout=True)
    latencies = [float(row["search_p95_ms"]) for row in rows]
    recalls = [float(row["recall_at_100"]) for row in rows]
    for row in rows:
        arm = row["arm_id"]
        cost = float(row["charged_usd"])
        size = 220 + 900 * max(cost, 0.03)
        scatter_kwargs: dict[str, Any] = {
            "s": size,
            "c": colors[arm],
            "marker": markers[arm],
            "linewidths": 1.0,
            "alpha": 0.95,
            "zorder": 3,
        }
        if markers[arm] != "x":
            scatter_kwargs["edgecolors"] = "#222222"
        ax.scatter(float(row["search_p95_ms"]), float(row["recall_at_100"]), **scatter_kwargs)
        offset = (8, 8) if arm != "ARM-01" else (8, -16)
        ax.annotate(labels[arm], (float(row["search_p95_ms"]), float(row["recall_at_100"])), xytext=offset, textcoords="offset points", fontsize=9)
    ax.set_title("Per-retriever search reveals a quality-latency-cost frontier", fontsize=15, weight="bold", pad=12)
    ax.set_xlabel("Search p95 latency (ms)")
    ax.set_ylabel("OUT Recall@100")
    ax.set_xlim(min(latencies) - 45, max(latencies) + 150)
    ax.set_ylim(min(recalls) - 0.025, max(recalls) + 0.008)
    ax.grid(axis="both", color="#D9D9D9", linewidth=0.7, alpha=0.6)
    ax.set_axisbelow(True)
    ax.legend(
        handles=[
            Line2D([0], [0], marker="o", color="none", markerfacecolor="#777777", markeredgecolor="#222222", markersize=8, label="Primary transfer input"),
            Line2D([0], [0], marker="x", color="#555555", markersize=8, linestyle="None", label="Diagnostic no-winner"),
        ],
        loc="upper left",
        bbox_to_anchor=(0.01, 0.98),
        ncol=2,
        frameon=False,
        fontsize=8.5,
    )
    figure_dir = output / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    stem = figure_dir / "a2-quality-latency-cost-frontier-journal"
    records: list[dict[str, Any]] = []
    for suffix, kwargs in ((".png", {"dpi": 300}), (".svg", {}), (".pdf", {})):
        path = stem.with_suffix(suffix)
        fig.savefig(path, **kwargs)
        records.append({"source": "derived from docs/progress_report/A2_per_arm_autoindex_outcomes_eda_20260818.csv", "package_path": path.relative_to(output).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)})
    plt.close(fig)
    return records


def build_readiness_table(repo: Path, output: Path) -> dict[str, Any]:
    """Project A4 readiness without copying Owner-local measurements."""
    source = repo / "control/armindex/a4/a4-readiness-binding-20260819.json"
    binding = json.loads(source.read_text(encoding="utf-8"))
    path = output / "tables/A4_readiness_status_20260819.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        ("phase_status", binding.get("status", "MISSING")),
        ("measured_execution", str(binding.get("measured_execution", "MISSING")).lower()),
        ("selection_permitted", str(binding.get("selection_permitted", "MISSING")).lower()),
        ("final_permitted", str(binding.get("final_permitted", "MISSING")).lower()),
        ("primary_arm_count", str(len(binding.get("primary_arm_scope", [])))),
        ("train250_query_count", str(binding.get("train250_query_count", "MISSING"))),
        ("transfer_operation_count", str(binding.get("transfer_operation_count", "MISSING"))),
        ("harnessopt_candidate_count", str(binding.get("harnessopt_candidate_count", "MISSING"))),
        ("claim_boundary", binding.get("claim_boundary", "MISSING")),
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("field", "value", "source"))
        writer.writerows((field, value, "control/armindex/a4/a4-readiness-binding-20260819.json") for field, value in rows)
    return {"source": "control/armindex/a4/a4-readiness-binding-20260819.json", "package_path": path.relative_to(output).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)}


def build_manuscript_asset_map(output: Path) -> dict[str, Any]:
    text = """# ArmIndex manuscript asset map

This map is a writing aid generated with the aggregate-safe journal package. Use the paper-oriented variants for the main manuscript and retain the full EDA set for supplementary material. Numeric authority remains the hash-bound source listed in `provenance/journal-artifact-manifest.v1.json`.

## Main manuscript

| Slot | Recommended asset | Evidence role | Claim boundary |
|---|---|---|---|
| Figure 1 | `figures/a0-a2-publication-timeline.svg` | Study lifecycle and gate separation | A0 is engineering validation; A1-A3 are development evidence. |
| Figure 2 | `figures/a1-common-screen-quality.png` | Retriever-conditioned representation effects | Descriptive 25-cell REP-DEV aggregate; no universal best representation. |
| Figure 3 | `figures/a2-quality-latency-cost-frontier-journal.png` | Per-retriever quality/latency/cost trade-off | A2 development evidence; primary inputs and diagnostic no-winner arms are shown explicitly. |
| Figure 4 | `figures/a3-transfer-recall-heatmap-journal.png` | Transfer complementarity | Train-250 development evidence; not external generalization or Selection evidence. |
| Figure 5 | `figures/a3-fixed-control-quality-journal.png` | Fixed-control fusion comparison | Development frontier only; flat HarnessOpt surface is retained as a negative result. |

## Tables

- `tables/results-summary.md`: readable aggregate result table for drafting.
- `tables/A0_A1_A2_metric_dictionary_20260818.csv`: metric definitions and units.
- `tables/A1_common_screen_aggregate_eda_20260818.csv`: common-screen aggregates.
- `tables/A2_per_arm_autoindex_outcomes_eda_20260818.csv`: per-arm outcomes and dispositions.
- `tables/A3_transfer_matrix_eda_20260819.csv`: nine transfer cells, each 250/250 units.
- `tables/A3_fixed_controls_eda_20260819.csv`: five fixed controls.
- `tables/A4_readiness_status_20260819.csv`: contract-only A4 status; no complete A4 result is inferred.

## Supplementary material

Use the PDF/SVG duplicates under `figures/`, the cell-level EDA table, the A2 coverage/reserve figures, and `provenance/claim-inventory.csv` as audit supplements. Do not export protected membership, qrels, raw IDs, rankings, per-query outcomes, credentials, provider payloads, or model weights.

## Current gate note

A4 remains `contract_only_ready` in the canonical readiness binding. FAST completed a 100-unit Owner-local aggregate evaluation, but BALANCED ended in a recoverable CUDA out-of-memory runtime failure and DEEP, legal isolation, one-shot Selection, safe return, and independent audit remain incomplete. FAST must therefore be cited only as a pending profile status pointer, not as an A4 production result. A5 Final and A6 full-corpus materialization are not paper results at this cutoff.
"""
    path = output / "manuscript/asset-map.md"
    write_text(path, text)
    return {"source": "generated from allowlisted EDA tables and A4 readiness binding", "package_path": path.relative_to(output).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repository_root.resolve()
    output = args.output_root.resolve()
    output.mkdir(parents=True, exist_ok=True)

    for child in output.iterdir():
        if child.name not in {"README.md"}:
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    figure_records = copy_allowlist(repo, output, FIGURES, "figures")
    figure_records.extend(build_a2_journal_figure(repo, output))
    figure_records.extend(build_a3_journal_figures(repo, output))
    table_records = copy_allowlist(repo, output, TABLES, "tables")
    table_records.append(build_readiness_table(repo, output))
    claim_records = build_claim_inventory(output)
    manuscript_records = [build_manuscript_asset_map(output)]
    pointer_records = []
    for relative in CONTROL_POINTERS:
        source = repo / relative
        pointer_records.append(
            {
                "source": relative.replace("\\", "/"),
                "sha256": sha256(source) if source.is_file() else None,
                "status": "VERIFIED" if source.is_file() else "MISSING",
            }
        )
    build_results_summary(repo, output)

    captions = """# Figure captions and claim limits

## Figure 1. Study lifecycle and evidence boundary

The workflow moves from migration and common screening to per-retriever representation search and transfer diagnostics. A0 is engineering validation; A1-A3 are development evidence. Selection, Final confirmation, full-corpus materialization, and release remain separate gates.

## Figure 2. Common-screen representation effects

The five-by-five A1 screen shows that deterministic representation effects vary across retrievers. Values are OUT aggregate metrics over the frozen 25-cell development screen. The figure is descriptive and does not establish a universal best representation.

## Figure 3. Per-arm AutoIndex outcomes

A2 reports the per-arm development outcomes after candidate search. ARM-03 is a numerical tie to its A1 comparator, ARM-04 is a strict improvement, ARM-05 has no strict improvement, and ARM-01/02 remain diagnostic no-winner cases. Dormant candidates are not failures or zero-valued results.

## Figure 4. A3 transfer matrix

Transfer performance depends on both source representation program and target adapter. The strongest observed cell is the ARM-05 source program on the ARM-03 adapter at `0.419274` OUT Recall@100; this is bounded Train-250 development evidence, not external generalization.

## Figure 5. A3 fixed controls

The fixed-control comparison preserves the top-two fusion result and the lower commercial-only union. Adding all primary arms does not improve the observed frontier. HarnessOpt produced a flat effective action signature under its preregistered development budget.

## Figure 6. Quality, latency, and cost frontier

The A2 frontier places quality against p95 search latency, with marker area encoding candidate charge. This is a development operational diagnostic; it is not a production cost claim and does not include Final evidence.

All captions must retain the qualifiers above when figures are moved into a manuscript or presentation.
"""
    write_text(output / "captions/figure-captions.md", captions)

    claim_boundary = """# Evidence and claim boundary

This package is an aggregate-safe manuscript preparation projection. Canonical authority remains in `01_Research` and is listed in `provenance/journal-artifact-manifest.v1.json`.

Allowed content: aggregate metrics, counts, hashes, figures, EDA tables, model/phase labels, and claim-limited captions.

Excluded content: protected split membership, qrels, raw query/family identifiers, rankings, per-query outcomes, credentials, provider payloads, model weights, and raw patent payloads.

Current evidence class: A0 engineering validation; A1-A3 measured development aggregates. A4 is incomplete at the report cutoff, A5 Final-872 is closed/not opened, and A6 full-DAPFAM materialization is execution-blocked until `PASS_A5_FINAL_CONFIRMATION`. No paper claim may describe A1-A3 as Final performance, external generalization, legal truth, infringement, novelty, validity, or freedom-to-operate.
"""
    write_text(output / "provenance/claim-boundary.md", claim_boundary)

    readme = """# ArmIndex journal preparation package

This directory contains a reproducible, aggregate-safe package for drafting the ArmIndex manuscript. It is generated from the allowlisted files in `01_Research` by `scripts/build_armindex_journal_artifacts.py`.

## Contents

- `figures/`: publication-source PNG/SVG figures for A0-A3.
- `tables/`: EDA CSVs and a readable aggregate result table.
- `captions/figure-captions.md`: standalone captions with claim limits.
- `provenance/journal-artifact-manifest.v1.json`: source/package SHA-256 ledger.
- `provenance/claim-inventory.csv`: manuscript-ready claims, evidence sources, and prohibited interpretations.
- `provenance/claim-boundary.md`: protected-data and scientific claim boundary.
- `manuscript/asset-map.md`: recommended main-text and supplementary assets with evidence limits.

The package does not contain protected membership, qrels, raw identifiers, rankings, per-query outcomes, credentials, provider payloads, or model weights. A4-A6 artifacts are pointers/status only until their canonical gates pass.
"""
    write_text(output / "README.md", readme)

    manifest = {
        "schema_version": "myis.armindex.journal-artifact-manifest.v1",
        "generated_on": date.today().isoformat(),
        "repository": "01_Research",
        "git_commit": git_value(repo, ["rev-parse", "HEAD"]),
        "git_tree": git_value(repo, ["rev-parse", "HEAD^{tree}"]),
        "evidence_class": "aggregate_safe_A0_A1_A2_A3_development_projection",
        "protected_payload_included": False,
        "figures": figure_records,
        "tables": table_records,
        "claim_inventory": claim_records,
        "manuscript_assets": manuscript_records,
        "canonical_pointers": pointer_records,
        "claim_boundary": "A0 engineering; A1-A3 development aggregates; A4 incomplete; A5 Final closed; A6 blocked until A5 PASS.",
    }
    manifest_path = output / "provenance/journal-artifact-manifest.v1.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
    print(json.dumps({"status": "PASS_JOURNAL_ARTIFACT_BUILD", "figures": len(figure_records), "tables": len(table_records), "output": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
