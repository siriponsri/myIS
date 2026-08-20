"""Build aggregate-safe A4/A5/A6 EDA and a gate-status figure.

Only aggregate receipts, pending templates, and blocker metadata are read. No
protected membership, qrels, rankings, identifiers, or per-query outcomes are
loaded or copied.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    project = args.project_root.resolve()
    research = project / "01_Research"
    owner = project / "04_Owner_Stores"
    out = args.output_root.resolve()
    a4 = owner / "armindex/a4/a4-goal001-20260819T180000Z-a4x12/hdev-evaluations"
    a5 = owner / "armindex/a5/a5-pending-a4-selection-20260820T174500Z"
    a4_files = {
        "FAST": a4 / "FAST.json",
        "BALANCED": a4 / "BALANCED.json",
        "DEEP": a4 / "DEEP.json",
        "ARM-03_RESEARCH_REFERENCE": a4 / "ARM-03_RESEARCH_REFERENCE.json",
    }
    profile_rows: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    for profile, path in a4_files.items():
        value = load(path)
        metric = value.get("metrics", value)
        coverage = value.get("coverage", {})
        latency = value.get("latency", {})
        resource = value.get("resource", {})
        profile_rows.append({
            "profile": profile,
            "license_scope": "research_only" if profile == "ARM-03_RESEARCH_REFERENCE" else "commercial_capable",
            "recall_at_100_out": metric.get("recall_at_100_out", metric.get("recall_at_100", value.get("recall_at_100_out", "MISSING"))),
            "ndcg_at_100_out": metric.get("ndcg_at_100_out", metric.get("ndcg_at_100", value.get("ndcg_at_100_out", "MISSING"))),
            "ndcg_at_10_out": metric.get("ndcg_at_10_out", metric.get("ndcg_at_10", value.get("ndcg_at_10_out", "MISSING"))),
            "p50_ms": latency.get("p50_ms", value.get("p50_ms", "MISSING")),
            "p95_ms": latency.get("p95_ms", value.get("p95_ms", "MISSING")),
            "p99_ms": latency.get("p99_ms", value.get("p99_ms", "MISSING")),
            "cost_usd": resource.get("cost_usd", value.get("cost_usd", "MISSING")),
            "completed_units": coverage.get("completed_units", value.get("completed_units", "MISSING")),
            "expected_units": coverage.get("expected_units", value.get("expected_units", "MISSING")),
            "failures": value.get("failures", 0),
            "deterministic": value.get("determinism", value.get("deterministic", "MISSING")),
            "evidence_status": "VERIFIED_A4_AGGREGATE",
            "source_file": str(path.relative_to(project)).replace("\\", "/"),
        })
        sources.append({"path": str(path.relative_to(project)).replace("\\", "/"), "sha256": sha256(path)})

    blocker_path = a5 / "A5_EXECUTION_BLOCKER_20260820.json"
    pending_path = a5 / "a5-pending-a4-selection-template.v1.json"
    blocker = load(blocker_path)
    pending = load(pending_path)
    status_rows = [
        {"phase": "A4_PRODUCTION_TRANSFER_AND_SELECTION", "status": "PASS_AGGREGATE", "execution_permitted": True, "selection_accesses": 0, "final_accesses": 0, "evidence_status": "VERIFIED", "source_file": str(a4.relative_to(project)).replace("\\", "/")},
        {"phase": "A5_FINAL_CONFIRMATION", "status": "BLOCKED_PRESELECTION_HANDOFF_AND_D2", "execution_permitted": pending.get("execution_permitted", False), "selection_accesses": pending.get("selection_accesses", 0), "final_accesses": pending.get("final_accesses", 0), "evidence_status": blocker.get("status", "BLOCKED"), "source_file": str(blocker_path.relative_to(project)).replace("\\", "/")},
        {"phase": "A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY", "status": "BLOCKED_A5_CLOSEOUT", "execution_permitted": False, "selection_accesses": 0, "final_accesses": 0, "evidence_status": "CONTRACT_VERIFIED_PENDING_A5", "source_file": "01_Research/control/armindex/a6/a6-full-dapfam-execution-contract.v1.json"},
    ]
    write_csv(out / "tables/A4_profile_metrics_20260820.csv", profile_rows, list(profile_rows[0]))
    write_csv(out / "tables/A4_A5_A6_gate_status_20260820.csv", status_rows, list(status_rows[0]))
    sources.extend([
        {"path": str(blocker_path.relative_to(project)).replace("\\", "/"), "sha256": sha256(blocker_path)},
        {"path": str(pending_path.relative_to(project)).replace("\\", "/"), "sha256": sha256(pending_path)},
        {"path": "01_Research/control/armindex/a6/a6-full-dapfam-execution-contract.v1.json", "sha256": sha256(research / "control/armindex/a6/a6-full-dapfam-execution-contract.v1.json")},
    ])

    try:
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise SystemExit("matplotlib is required to render the EDA figure") from error
    labels = ["A4\nprofile transfer", "A5\nFinal-872", "A6\nfull corpus"]
    colors = ["#2A6F4E", "#C47F00", "#6B7280"]
    fig, ax = plt.subplots(figsize=(8.4, 3.4), constrained_layout=True)
    ax.bar(range(3), [1, 1, 1], color=colors, width=0.62)
    ax.set_xticks(range(3), labels)
    ax.set_yticks([])
    ax.set_ylim(0, 1.25)
    ax.set_title("A4 is measured; A5 and A6 remain explicitly gated")
    for index, text in enumerate(["PASS\naggregate", "BLOCKED\nSelection-125 + D2", "BLOCKED\nA5 closeout"]):
        ax.text(index, 0.5, text, ha="center", va="center", color="white", weight="bold", fontsize=10)
    for spine in ax.spines.values():
        spine.set_visible(False)
    figure = out / "figures/A4_A5_A6_gate_status_20260820.png"
    figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure, dpi=300)
    plt.close(fig)
    manifest = {
        "schema_version": "myis.armindex-a456-eda-manifest.v1",
        "evidence_class": "aggregate_safe_status_and_a4_profiles",
        "protected_payload_included": False,
        "outputs": [
            "tables/A4_profile_metrics_20260820.csv",
            "tables/A4_A5_A6_gate_status_20260820.csv",
            "figures/A4_A5_A6_gate_status_20260820.png",
        ],
        "sources": sources,
        "claim_boundary": "A4 aggregate profiles only; A5 Final-872 and A6 full-corpus results do not exist.",
    }
    manifest["manifest_sha256"] = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    (out / "provenance").mkdir(parents=True, exist_ok=True)
    (out / "provenance/A4_A5_A6_eda_manifest.v1.json").write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="ascii")
    print(json.dumps({"status": "PASS_A456_EDA_BUILD", "output": str(out), "profile_rows": len(profile_rows), "sources": len(sources)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
