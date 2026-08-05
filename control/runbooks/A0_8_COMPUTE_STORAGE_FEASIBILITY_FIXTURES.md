# A0.8 Compute and Storage Feasibility Fixtures

## Authority

- Phase: `A0_MIGRATION_FOUNDATION`
- Task: `A0.8`
- Campaign: `control/campaigns/armindex-multiretriever-v2.yaml`
- Budget: `control/budgets/armindex-migration-v2.yaml`
- Standing authorization: `D1_START_CAMPAIGN`
- Evidence class: `engineering_fixture`
- Scientific authority: `false`

## Objective

Prepare the reusable A0.8 fixture scaffold, characterize CPU compute and
storage behavior with synthetic inputs only, and close the task with an
aggregate-safe receipt. This task does not establish retrieval quality,
production capacity, or readiness for measured execution.

## Frozen Boundary

- CPU only and zero charged cost.
- No protected dataset, qrels, membership, query IDs, rankings, or per-query
  outcomes.
- No measured retrieval, model resolution or download, GPU, paid API,
  provider fallback, Selection, or Final.
- `ARM-01` uses the existing fixture-only kernel BM25 wrapper. It is not the
  future frozen `bm25s` scientific adapter.
- Dense arms remain metadata-only and fail closed.
- Existing App sparse indexes are presence-only planning context. Their
  protected payloads are not opened or used in A0.8.

## Execution Steps

1. Validate the reusable-asset registry and record only aggregate-safe App
   asset availability.
2. Add a bounded, disposable-by-default synthetic feasibility fixture and CLI.
3. Measure compile, index-build, and search latency plus Python allocation and
   deterministic representation/index descriptors on CPU.
4. Persist one write-once manifest and receipt under
   `outputs/fixtures/armindex/a0.8/compute-storage-v1/`.
5. Validate zero real counters and every prohibited-action flag.
6. Project one validated read model to Brain, Obsidian, Dashboard, Paper, and
   the repository-safe MLflow mirror.
7. Close A0.8 and authorize only synthetic, CPU-only A0.9 validation and
   closeout. A1 remains locked.

## Acceptance

- The A0.8 fixture completes on CPU with no network/model download.
- Manifest and receipt are canonical JSON, self-hashed, mutually bound, and
  aggregate-safe.
- Compute metrics are labeled host-observed fixture measurements and storage
  metrics distinguish deterministic logical bytes from Python allocation.
- ArmIndex measured, Selection, and Final counters remain zero.
- `PLAN.md`, campaign control, `HANDOFF.md`, Brain, generated reports, and
  related status documents agree on the closed A0.8 state and exact next
  action.
- Focused tests and mandatory repository checks pass before commit and push.

## Ledger

Append material starts, runs, failures, recoveries, and closeout events to
`control/armindex/a0.8-compute-storage-feasibility-ledger.v1.jsonl`. Each entry
binds the previous entry hash; existing lines are immutable.
