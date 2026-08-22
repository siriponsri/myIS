"""Build aggregate-safe publication scaffolding for the A4 -> A5 -> A6 route.

The input surface is deliberately limited to the two aggregate A4 receipts.
No query IDs, qrels, rankings, membership, vectors, or per-query outcomes are
read or copied. A5/A6 rows are status templates only and contain no metrics.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
OWNER_ROOT = ROOT / "04_Owner_Stores"
OUT_ROOT = Path(__file__).resolve().parent
A4_DIR = OWNER_ROOT / "armindex/a4/a4-goal001-20260821T071350Z-sel01"
COVERAGE_PATH = A4_DIR / "selection-closeout-v3/A4_SELECTION_COVERAGE.json"
RECEIPT_PATH = A4_DIR / "selection-receipt.json"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    coverage = load_json(COVERAGE_PATH)
    receipt = load_json(RECEIPT_PATH)
    def canonical_profile(value: str) -> str:
        return value.replace("ARM03", "ARM-03").replace("ARM_03", "ARM-03")

    profile_metrics: dict[str, float] = {}
    for item in receipt.get("comparisons", []):
        effect = item.get("paired_effect", {})
        comparison = item.get("comparison_id", "")
        left, _, right = comparison.partition("-vs-")
        if effect.get("left_mean") is not None:
            profile_metrics[canonical_profile(left)] = effect["left_mean"]
        if effect.get("right_mean") is not None:
            profile_metrics[canonical_profile(right)] = effect["right_mean"]
    # BALANCED/DEEP/FAST means are present as right-side values in comparisons.

    rows: list[dict[str, Any]] = []
    for profile, data in coverage["profiles"].items():
        resource = data.get("resource", {})
        latency = data.get("latency", {})
        rows.append(
            {
                "phase": "A4_PRODUCTION_TRANSFER_AND_SELECTION",
                "profile": profile,
                "population": receipt.get("selection_population", "OUT"),
                "query_count": receipt.get("selection_evaluated_query_count"),
                "recall_at_100_out": profile_metrics.get(profile, "NOT_VERIFIED"),
                "ndcg_at_100_out": "NOT_VERIFIED",
                "ndcg_at_10_out": "NOT_VERIFIED",
                "p50_ms": latency.get("p50_ms", "NOT_VERIFIED"),
                "p95_ms": latency.get("p95_ms", "NOT_VERIFIED"),
                "p99_ms": latency.get("p99_ms", "NOT_VERIFIED"),
                "throughput_qps": latency.get("throughput_qps", "NOT_VERIFIED"),
                "cost_usd": resource.get("cost_usd", "NOT_VERIFIED"),
                "completed_units": data.get("coverage", {}).get("completed_units"),
                "expected_units": data.get("coverage", {}).get("expected_units"),
                "failures": data.get("failures", "NOT_VERIFIED"),
                "deterministic": data.get("determinism", "NOT_VERIFIED"),
                "evidence_status": "VERIFIED_AGGREGATE_A4_SELECTION",
                "source_file": "04_Owner_Stores/armindex/a4/a4-goal001-20260821T071350Z-sel01/selection-receipt.json",
            }
        )

    status_rows = [
        {
            "phase": "A4_PRODUCTION_TRANSFER_AND_SELECTION",
            "status": coverage.get("status", "NOT_VERIFIED"),
            "planned_scope": "Selection-125; four frozen profiles",
            "measured_scope": "125 retrieval units; 90 OUT evaluator units",
            "metric_status": "VERIFIED_AGGREGATE",
            "next_gate": "A5 Final-872",
            "source_file": "04_Owner_Stores/armindex/a4/a4-goal001-20260821T071350Z-sel01/selection-receipt.json",
        },
        {
            "phase": "A5_FINAL_CONFIRMATION",
            "status": "PENDING_FRESH_INSTANCE_RUN",
            "planned_scope": "Final-872; FAST comparator vs ARM-03 research champion",
            "measured_scope": "NONE",
            "metric_status": "PENDING_NOT_VERIFIED",
            "next_gate": "PASS_A5_FINAL_CONFIRMATION",
            "source_file": "04_Owner_Stores/armindex/a5/provenance/a5-pointer-bundle-v7-20260822.json",
        },
        {
            "phase": "A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY",
            "status": "PENDING_A5_CLOSEOUT",
            "planned_scope": "Frozen A5 winner over 45,336-row DAPFAM corpus",
            "measured_scope": "NONE",
            "metric_status": "PENDING_NOT_VERIFIED",
            "next_gate": "PASS_A6_MATERIALIZATION",
            "source_file": "docs/goal/A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY_goal_001.md",
        },
    ]

    pairwise_rows = []
    for item in receipt.get("comparisons", []):
        effect = item.get("paired_effect", {})
        pairwise_rows.append(
            {
                "comparison_id": item.get("comparison_id"),
                "metric": effect.get("metric", "recall_at_100"),
                "population": receipt.get("selection_population", "OUT"),
                "unit_count": effect.get("unit_count"),
                "paired_delta": effect.get("paired_delta"),
                "ci_lower": effect.get("ci_lower"),
                "ci_upper": effect.get("ci_upper"),
                "wins": item.get("win_tie_loss", {}).get("wins"),
                "ties": item.get("win_tie_loss", {}).get("ties"),
                "losses": item.get("win_tie_loss", {}).get("losses"),
                "decision": item.get("decision"),
                "evidence_status": "VERIFIED_AGGREGATE_A4_SELECTION",
            }
        )

    write_csv(
        OUT_ROOT / "tables/a4_selection_profile_metrics.csv",
        rows,
        list(rows[0]),
    )
    write_csv(
        OUT_ROOT / "tables/a4_selection_pairwise_effects.csv",
        pairwise_rows,
        list(pairwise_rows[0]),
    )
    write_csv(OUT_ROOT / "tables/a4_a5_a6_status_pending.csv", status_rows, list(status_rows[0]))

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - environment-specific
        raise SystemExit("matplotlib is required") from exc

    (OUT_ROOT / "figures").mkdir(parents=True, exist_ok=True)

    names = [row["profile"].replace("_RESEARCH_REFERENCE", "\nresearch") for row in rows]
    recall = [float(row["recall_at_100_out"]) for row in rows]
    cost = [float(row["cost_usd"]) for row in rows]
    p95 = [float(row["p95_ms"]) for row in rows]
    palette = ["#0072B2", "#009E73", "#E69F00", "#D55E00"]
    fig, axes = plt.subplots(1, 3, figsize=(10.8, 3.6), constrained_layout=True)
    for ax, values, ylabel, title in zip(
        axes,
        [recall, cost, p95],
        ["OUT Recall@100", "Cost (USD)", "p95 latency (ms)"],
        ["A4 quality signal", "A4 run cost", "A4 tail latency"],
    ):
        bars = ax.bar(range(len(names)), values, color=palette, width=0.68)
        ax.set_xticks(range(len(names)), names, fontsize=7)
        ax.set_ylabel(ylabel, fontsize=8)
        ax.set_title(title, fontsize=9, weight="bold")
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{value:.3g}", ha="center", va="bottom", fontsize=7)
    fig.suptitle("A4 Selection evidence: quality and operational trade-offs", fontsize=11, weight="bold")
    fig.savefig(OUT_ROOT / "figures/a4_selection_quality_cost_latency.png", dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.2, 2.8), constrained_layout=True)
    labels = ["A4\nSelection-125", "A5\nFinal-872", "A6\nFull DAPFAM"]
    state_labels = ["MEASURED\naggregate", "PENDING\nno metrics", "PENDING\nno metrics"]
    colors = ["#0072B2", "#999999", "#999999"]
    ax.bar(range(3), [1, 1, 1], color=colors, width=0.62)
    ax.set_xticks(range(3), labels)
    ax.set_yticks([])
    ax.set_ylim(0, 1.2)
    for i, label in enumerate(state_labels):
        ax.text(i, 0.5, label, ha="center", va="center", color="white", weight="bold", fontsize=9)
    ax.set_title("Publication evidence status: A5/A6 metrics are intentionally deferred", fontsize=10, weight="bold")
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.savefig(OUT_ROOT / "figures/a4_a5_a6_status_pending.png", dpi=300)
    plt.close(fig)

    source_records = [
        {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": digest(path)}
        for path in (COVERAGE_PATH, RECEIPT_PATH)
    ]
    outputs = [
        "tables/a4_selection_profile_metrics.csv",
        "tables/a4_selection_pairwise_effects.csv",
        "tables/a4_a5_a6_status_pending.csv",
        "figures/a4_selection_quality_cost_latency.png",
        "figures/a4_a5_a6_status_pending.png",
    ]
    manifest = {
        "schema_version": "myis.armindex.publication-eda-scaffold.v1",
        "generated_on": "2026-08-22",
        "evidence_class": "aggregate_safe_publication_scaffold",
        "protected_payload_included": False,
        "source_records": source_records,
        "outputs": outputs,
        "claim_boundary": "A4 aggregate Selection evidence only. A5 Final-872 and A6 full-corpus metrics are pending and must not be inferred from this package.",
        "not_verified": ["A4 OUT nDCG@100", "A4 OUT nDCG@10", "A5 metrics", "A6 metrics"],
    }
    manifest["manifest_sha256"] = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    (OUT_ROOT / "provenance").mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "provenance/aggregate_safe_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    readme = """# ArmIndex A5-A6 Continuation Publication Scaffold

Generated 2026-08-22 from the aggregate-safe A4 Selection coverage and
Selection receipt. This package is a publication preparation artifact, not a
replacement for A5 or A6 measured evidence.

## Evidence boundary

- A4: four profiles, Selection-125 retrieval coverage, and 90 OUT evaluator
  units are reported from canonical receipts.
- A5 Final-872: **PENDING**. No metrics are included here.
- A6 full DAPFAM materialization: **PENDING**. No metrics are included here.
- OUT nDCG@100 and OUT nDCG@10 are **NOT VERIFIED** in the safe aggregate
  receipt used by this scaffold.
- Protected membership, qrels, query IDs, rankings, vectors, and per-query
  outcomes were not read or copied.

## Files

- `tables/a4_selection_profile_metrics.csv`: A4 quality and operational values.
- `tables/a4_selection_pairwise_effects.csv`: paired A4 effects and W/T/L.
- `tables/a4_a5_a6_status_pending.csv`: explicit phase status template.
- `figures/a4_selection_quality_cost_latency.png`: publication-sized A4 panel.
- `figures/a4_a5_a6_status_pending.png`: evidence-state figure with pending gates.
- `provenance/aggregate_safe_manifest.json`: source hashes and claim boundary.

When A5 and A6 receipts are available, update this package by adding new
versioned artifacts; do not overwrite the A4 evidence or backfill pending
metrics from estimates.
"""
    (OUT_ROOT / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps({"status": "PASS_AGGREGATE_SAFE_PUBLICATION_SCAFFOLD", "output_root": str(OUT_ROOT), "sources": len(source_records), "outputs": len(outputs)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
