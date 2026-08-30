source: docs/journal/JOURNAL_UNBLOCK_TASKS.md; docs/journal/DATA_PACK/A_domain_exposure.csv; docs/journal/DATA_PACK/B2_depth_curve_extended.csv; docs/journal/DATA_PACK/C_final872_by_domain.csv; docs/journal/DATA_PACK/E1_screen_5x5.csv; docs/journal/DATA_PACK/F_case_studies.md

# Journal data-prep report, round 2

All work is post-hoc and local. No paid provider, retrieval, indexing, embedding, reranking, or frozen-artifact mutation was performed.

| Task | Status | Evidence and sanity check |
|---|---|---|
| A2 per-domain exposure | DONE | The canonical relation field is `domain_rel` with values `IN/OUT`; query and family IPC 3-character labels come from the public DAPFAM Parquet release. The strict `OUT` slice has 128 non-empty query-domain bins and reproduces 905 queries, 5,193 incidences, 796 / 332 / 4,065. |
| C2 Final-872 by domain | DONE | Recomputed per-query Recall@100 from A5 `qrels.jsonl` and two returned rankings, joined to public DAPFAM query IPC 3-character labels. The 131 bins reproduce 872 queries and 619 / 158 / 95. |
| E1b common screen | DONE | 25 cells recovered from the owner-local A1 EDA receipt. Per-retriever means reproduce paper values: BM25 0.191200; BGE-M3 0.269933; PatEmbed-large 0.413400; Arctic 0.340667; Qwen3 0.363733. |
| F2 case studies | DONE | Three strict-OUT absent-target cases use opaque safe IDs, public DAPFAM title/abstract text, and public IPC 3-character domains. |
| H2 depth extension | DONE | Existing retained `pool_depth=2000` ranking was replayed. Exact Rule 0 matches at k=100 and k=200; extension reports k=300, 500, 1000 and absent-from-Top-1000 count. |

## Rule 0 audit

PASS: 905 judged queries; 5,193 strict cross-domain relevant incidences; 796 found in ranks 1-100; 332 found only in ranks 101-200; 4,065 absent from Top-200; Final-872 619/158/95; Recall@100 0.188450; Top-200 perfect-ordering bound 0.260167.

## Domain summaries

Using the first IPC 3-character label in each public DAPFAM query record as a deterministic, non-overlapping bin, the best-exposed domain is `E02` (macro Recall@100 0.656085; absent rate 0.250000). The weakest bins at the observed sample size are `B60`, `G01`, and `G06`, each with macro Recall@100 0.000000; `B60` and `G01` have complete Top-200 absence. These are descriptive slices, not causal claims.

## H2 replay audit

PASS: the retained deep ranking has 2,494,000 rows (1,247 queries x 2,000). Using the lowercase token-map join and positive `OUT` relations gives 0.188450 / 796 at k=100 and 0.260167 / 1,128 at k=200. Extended results are 0.317703 / 1,366 at k=300, 0.409842 / 1,738 at k=500, and 0.529463 / 2,236 at k=1000; 219 judged queries remain without a relevant family in Top-1000.

## Remaining evidence boundary

The local relation Arrow schema contains the canonical `domain_rel` field (`IN/OUT`). Public DAPFAM `queries.parquet` and `corpus.parquet` provide IPC 3-character labels for query/family joins. The A5 owner-evaluation receipt is aggregate-only, but Owner-local `protected/qrels.jsonl` and returned `remote-results/a5-result.json` permit transparent per-query recomputation; the resulting domain bins reproduce the canonical outcome totals.
