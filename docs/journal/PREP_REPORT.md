source: docs/journal/JOURNAL_DATA_PREP_TASKS.md; docs/journal/WPI_JOURNAL_OUTLINE.md; DATA_PACK files listed below

# Journal data-prep report

All work in this report is post-hoc. No retrieval, indexing, embedding, reranking, or model execution was run.

| Task | Status | Sanity check |
|---|---|---|
| A | BLOCKED | Missing aggregate-safe per-domain labels/rows; Rule 0 totals remain verified in A7 source (905 queries; 5,193 pairs; 796/332/4,065). |
| B | DONE | Strict OUT curve reproduces 0.188450 at k=100 and 0.260167 at k=200; pair counts 796 and 1,128 retained where available. |
| C | BLOCKED | Missing per-query Final-872 domain labels; global 619/158/95 remains verified from canonical aggregate. |
| D | DONE | Frozen universe accounting reproduces 52 total, 44 executed, 8 reserves; detailed 52-row construction payload is Owner-local only. |
| E | BLOCKED | E2 profiles reproduce 0.416/0.361/0.361/0.308; 25-cell E1 payload is not exported. |
| F | BLOCKED | Protected query/family titles and domains unavailable in publication projection; no case fabricated. |
| G | DONE | Manifest names exact source artifacts and freeze chronology; all DATA_PACK files carry a source line. |
| H | DONE | Feasibility only: retained index shards identified and sized; no experiment or paid action performed. |

## Rule 0 audit

Required immutable values are reproduced from A6/A7/A5 evidence: 905 judged queries; 5,193 strict cross-domain relevant incidences; 796 found in ranks 1-100; 332 found only in ranks 101-200; 4,065 absent from Top-200; Final-872 619/158/95; strict OUT Recall@100 0.188450 and the Top-200 perfect-ordering bound 0.260167. Any future mismatch is a stop-and-report condition.
