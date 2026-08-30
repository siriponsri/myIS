source: ..\\04_Owner_Stores\\armindex\\a6\\_remote_return_full09\\owner-local\\shard-0\\flat-l2-normalized.index.f32; ..\\04_Owner_Stores\\armindex\\a6\\_remote_return_full09\\owner-local\\shard-1\\flat-l2-normalized.index.f32; docs/FULL_PROJECT_REPORT_A0_A8_EN.md

# Task H feasibility only

Status: DONE_FEASIBILITY_ONLY. No experiment was run.

- Retained full-corpus index: shard 0, 383,557,632 bytes; shard 1, 390,356,992 bytes. The corresponding `INDEX_MANIFEST.json` files are retained beside each shard. The A6 return also retains per-shard metadata and latency logs.
- The retained artifacts are sufficient to estimate a deeper re-score without re-embedding. A6 recorded 1,247 queries, 45,336 families, and 249,400 Top-200 rows; a k=1000 pass would score 1,247 x 1,000 ranked outputs (1,247,000 rows), approximately 5x the Top-200 candidate output. A cost quote is not emitted because the provider was destroyed and no fresh paid authority is present; spending is therefore `UNKNOWN_DO_NOT_SPEND`.
- Any future run must write to a new attempt/output directory, leave the frozen Top-200 pool untouched, and preserve the existing A6/A7 hashes and receipts.
