# Handoff to Orchestrator

Prepared as a disjoint, aggregate-safe publication scaffold while A5 transport
and launch are in progress.

## Generated artifacts

- `tables/a4_selection_profile_metrics.csv`: four A4 profiles with verified
  OUT Recall@100 means recovered from the canonical paired selection receipt,
  operational latency, throughput, cost, 125/125 coverage, determinism, and
  zero failures.
- `tables/a4_selection_pairwise_effects.csv`: six paired A4 comparisons with
  10,000-bootstrap intervals and W/T/L values.
- `tables/a4_a5_a6_status_pending.csv`: explicit status table. A5 is
  `PENDING_FRESH_INSTANCE_RUN`; A6 is `PENDING_A5_CLOSEOUT`; both contain no
  metrics.
- `figures/a4_selection_quality_cost_latency.png`: 300-dpi, three-panel A4
  quality/cost/tail-latency figure.
- `figures/a4_a5_a6_status_pending.png`: measured-vs-pending evidence-state
  figure.
- `provenance/aggregate_safe_manifest.json`: hashes for the two source
  receipts, output allowlist, and claim boundary.
- `build_aggregate_safe_eda.py`: deterministic rebuild script.

## Validation

Ran:

```text
python outputs/publication/armindex/a5-a6-continuation-20260822/build_aggregate_safe_eda.py
PASS_AGGREGATE_SAFE_PUBLICATION_SCAFFOLD
publication scaffold validation
git diff --check
```

The manifest asserts `protected_payload_included=false`, and validation checks
four profile rows, 125/125 coverage, populated A4 Recall@100, pending A5/A6
metric states, and all listed outputs. Figures were visually inspected for
clipping/overlap.

## Claim boundary

Do not infer or backfill A5 Final-872 or A6 full-DAPFAM metrics. OUT nDCG@100
and OUT nDCG@10 are marked `NOT_VERIFIED` because they are not present in the
safe aggregate receipt used here. No protected membership, qrels, query IDs,
rankings, vectors, or per-query outcomes were read or copied.

This directory is uncommitted and intentionally disjoint; the root
orchestrator may integrate or commit it after review.
