# JOURNAL_ARC_UPDATE.md — what the depth result changes, and four fixes before drafting

## 1. The headline changed (for the better)

The conference paper stopped at the Top-200 pool and said, correctly and with an
explicit scope guard, that recall there is exposure-bound. The depth replay now
shows what happens beyond that boundary:

| depth k | macro Recall@k | incidences found | absent | queries with nothing |
|---|---|---|---|---|
| 100 | 0.188 | 796 | 84.7% | 541 |
| 200 | 0.260 | 1,128 | 78.3% | 455 |
| 300 | 0.318 | 1,366 | 73.7% | 400 |
| 500 | 0.410 | 1,738 | 66.5% | 313 |
| 1000 | 0.529 | 2,236 | 56.9% | 219 |

Two readings, both true, and the journal needs both:

- **Depth pays, and it pays far more than ordering.** Perfect reranking inside
  the Top-200 pool buys +0.072. Going deeper buys multiples of that. This is the
  actionable finding for a working searcher, and it is quantified rather than
  asserted.
- **Exposure is still the binding constraint at five times the depth.** Even at
  k = 1000, 56.9% of relevant families have never been seen, and 219 queries
  have retrieved nothing relevant at all. The ceiling moves; it does not lift.

Revised journal thesis: *cross-domain patent retrieval is exposure-limited, the
limit is not an artifact of a shallow cutoff, and depth buys more recall than
any reordering of what a shallow pool already contains — but depth alone does
not solve it.* That is a stronger, more useful claim than the conference version
and it does not contradict it: the conference scope guard ("specific to the
Top-200 pool; deeper cutoffs are uncharacterized") is exactly what makes this a
clean extension rather than a correction.

Section 6 becomes the spine of the paper, and the closing line of the study is
no longer "reranking is capped" but something closer to: the pool decides what
either the model or the ranker will ever see, and buying a deeper pool moves that
boundary further than perfecting the order inside it.

## 2. Four fixes before drafting (all small, all post-hoc)

### Fix I1 — the apples-to-apples depth number (REQUIRED for the headline)
0.529 is Recall@**1000**; 0.260 is a Recall@**100** bound. They cannot be
compared directly, and a reviewer will catch it immediately. Compute the missing
cell: the **perfect-ordering bound on Recall@100 given the Top-1000 pool** —
i.e. for each query, how much Recall@100 an oracle ranker could reach if it
could reorder the 1,000 retrieved candidates into the top 100 (respecting the
100-slot cap). Do the same for pools of 300 and 500. Output
`I1_bound_by_pool_depth.csv` with columns: pool_depth, oracle_recall_at_100,
gain_over_observed. Sanity: pool_depth=200 must reproduce 0.260167 exactly.
This single table is the journal's central figure.

### Fix I2 — report domains at IPC section level, not 3-character level
`A_domain_exposure.csv` has 128 bins for 905 queries: median 8 queries per bin,
**not one bin reaches 20**. The per-bin numbers in PREP_REPORT_2 ("best domain
E02 at 0.656", "B60/G01/G06 at 0.000") are sampling noise and must not appear in
the paper. Roll up to the 8 IPC sections, where the picture is stable and the
message is stronger:

| section | queries | incidences | absent rate |
|---|---|---|---|
| A | 102 | 491 | 0.762 |
| B | 290 | 1,930 | 0.818 |
| C | 127 | 667 | 0.726 |
| D | 60 | 396 | 0.712 |
| E | 63 | 357 | 0.770 |
| F | 133 | 777 | 0.802 |
| G | 98 | 435 | 0.747 |
| H | 31 | 120 | 0.925 |

The finding is **uniformity**: every section loses 71–93% of its relevant
families from the Top-200 pool. Exposure failure is not a quirk of one crowded
technology — it is everywhere. That is a better journal result than a ranked
list of domains, and it survives its own sample size. Emit
`I2_section_exposure.csv` with the full column set (including macro Recall@100
and the bound per section), and keep the 3-character table as an appendix
clearly labelled as descriptive with small per-bin counts.

### Fix I3 — reselect the case studies
The current three all report "best found relevant rank: 1", i.e. the system did
retrieve something relevant immediately; only one further family was missing.
That illustrates the weakest version of the finding. Reselect from the **219
queries that retrieved nothing relevant even at k = 1000** — that population is
the paper's argument in concrete form. Also drop or replace Case 3 (a phrase-
based document-scoring query paired with an image-display family): the pairing
reads more like a questionable relevance judgment than a retrieval failure, and
building a case study on it invites the reviewer to attack the benchmark's
labels instead of hearing the point. Keep two clean cases; three is not required.

### Fix I4 — validate the domain codes
`G60` (Case 3) and an `O` bin with a single query are not valid IPC sections.
Trace both back to the source field, report what they are (parsing artifact,
placeholder, non-IPC scheme), and either correct or exclude them with a stated
rule. A journal whose audience *is* the classification community will notice.

## 3. Then start writing
Once I1–I4 land, draft in this order: Section 6 (exposure ceiling, now the
spine) → Section 7 (implications: configuration reporting + pool-depth guidance)
→ Section 1 (introduction, written last among the new material so it can promise
exactly what the paper delivers) → port Sections 3–5 from the conference text
with the audience shift.
