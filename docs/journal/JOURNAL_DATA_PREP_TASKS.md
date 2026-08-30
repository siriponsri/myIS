# JOURNAL_DATA_PREP_TASKS.md — data pack for the WPI journal version

Goal: produce `docs/journal/DATA_PACK/` — the tables, curves, and case
material the journal draft will consume. Tasks A–G are POST-HOC ANALYSES of
artifacts that already exist; they require NO new retrieval, NO new indexing,
NO model execution. Task H is the ONE genuinely new experiment and is GATED:
do the feasibility check, report, and STOP — do not run it without explicit
go-ahead.

## Rule 0 — integrity (unchanged from the paper rounds)
- Conference numbers are immutable ground truth. Any journal analysis that
  overlaps them (e.g., overall exposure counts, Final-872 metrics) must
  reproduce them exactly from the artifacts; a mismatch is a STOP-and-report,
  never a silent adjustment.
- Every output table carries a `source:` line naming the artifact file(s) it
  was computed from. No number enters DATA_PACK without a named source.
- The fixed Top-200 pool is read-only. Tasks A–G only aggregate it.

## Task A — per-domain exposure breakdown  [free; highest journal value]
From the fixed full-benchmark Top-200 pool + strict cross-domain judgments +
DAPFAM domain labels (IPC/CPC level used by the benchmark's domain definition):
for each query domain, compute: judged queries, relevant-family incidences,
found by rank 100, first found 101–200, absent, absent-rate, macro R@100, and
the perfect-ordering bound. Output `A_domain_exposure.csv` + a one-paragraph
summary naming the best- and worst-exposed domains. Sanity: totals must
reproduce 905 / 5,193 / 796 / 332 / 4,065 exactly.

## Task B — exposure-by-depth curve within the pool  [free]
From the same pool: macro Recall@k and cumulative incidence-found@k for
k = 10, 20, 50, 100, 150, 200 (strict cross-domain slice). Output
`B_depth_curve.csv`. Sanity: k=100 -> 0.188, k=200 -> 0.260 exactly.

## Task C — Final-872 outcomes by domain  [free]
Per-query Final-872 paired results + domain labels: wins/ties/losses and mean
paired ΔRecall@100 per domain. Output `C_final872_by_domain.csv`. Sanity:
totals 619/158/95.

## Task D — full registered-search table  [free; journal appendix]
All 52 registered configurations: id, retriever, construction summary,
executed/reserve, predicate fired?, Recall@100 where executed, decision under
the frozen rule. Output `D_search_space.csv`. Sanity: 52 total, 44 executed,
8 reserves, decisions consistent with Table II of the paper.

## Task E — 5x5 common screen + Selection-125 tables  [free; appendix]
`E1_screen_5x5.csv` (25 cells) and `E2_selection125.csv` (four profiles:
0.416 ARM-03, 0.361 BALANCED, 0.361 DEEP, 0.308 FAST + any secondary metrics
recorded).

## Task F — case studies  [free; qualitative]
Select 2–3 strict cross-domain queries where ≥1 relevant family is ABSENT from
Top-200. Prefer: (i) one where absence is intuitively explicable (vocabulary
gap across domains), (ii) one where the absent family looks lexically close
(surprising miss). For each: query family title(+abstract first sentence),
absent relevant family title, both domains, rank of best found relevant, and
2–3 sentences of neutral description. Output `F_case_studies.md`. No
speculation beyond what the text shows; these are illustrations, not claims.

## Task G — reproduction manifest  [free]
`G_manifest.md`: for every DATA_PACK file, the exact source artifacts +
script/notebook path used, so the journal's data-availability statement can
point at it. Include the preregistration freeze chronology references.

## Task H — depth-500/1000 exposure extension  [GATED: feasibility only]
The one analysis that needs new retrieval (the pool stops at 200). Do NOT run
it. Instead report:
1. Are the ARM-03 chunk embeddings and/or index for the full 45,336-family
   corpus retained on disk? Name the paths and sizes.
2. If yes: estimated cost of re-scoring all 1,247 queries at k=1000 (same
   frozen config, deeper cutoff only).
3. If no: estimated cost of re-embedding 188,944 chunks first.
4. Confirm the run would change NOTHING about existing artifacts (separate
   output directory, pool untouched).
Deliver the estimate and stop. The user decides. If it later runs, its outputs
extend `B_depth_curve.csv` with k = 300, 500, 1000 and the paper gains the
"does the ceiling lift with depth?" figure — the strongest new result the
journal version could add.

## Deliverables
`docs/journal/DATA_PACK/` with A–G outputs + `H_feasibility.md`, plus a short
`PREP_REPORT.md`: per-task DONE/BLOCKED (BLOCKED = named missing artifact),
every sanity check listed with pass/fail. Same discipline as the paper rounds:
"skipped" is not a state.
