# ArmIndex A5-A6 Continuation Publication Scaffold

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
