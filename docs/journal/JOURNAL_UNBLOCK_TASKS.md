# JOURNAL_UNBLOCK_TASKS.md — recover the four blocked analyses + revised Task H

Round 1 delivered B, D, E2, G, H-feasibility and blocked A, C, E1, F. The blocks
share one cause: those analyses were attempted only against the aggregate-safe
publication projection, which does not carry per-domain, per-query, or per-cell
rows. That is an export-scope limit, not missing data — Task B and Task D both
succeeded by reading Owner-local artifacts directly. This round applies the same
access pattern to the rest.

Read-only rule: every task below reads existing artifacts and writes new files
under `docs/journal/DATA_PACK/`. Nothing in the frozen pool, the A2/A4/A5/A6/A7
receipts, or the conference paper is modified.

Rule 0 (unchanged): immutable totals must reproduce exactly — 905 judged
queries, 5,193 incidences, 796 / 332 / 4,065, 619/158/95, 0.188450 and 0.260167.
Any mismatch is stop-and-report. Every output keeps its `source:` line.

## Task A2 (unblock A) — per-domain exposure
Inputs, the same ones Task B used, plus domain labels:
- `..\04_Owner_Stores\armindex\a6\a6-goal001-*-full09\deep-rankings\pool-200.jsonl`
- `..\04_Owner_Stores\a1.2-v15-20260809\protected\inputs\evaluator-relations.arrow`
- domain labels: the IPC/CPC field the strict cross-domain criterion itself uses
  (whatever field decides "query and relevant target do not share the required
  technical classification level" — reuse that exact field, do not invent a new
  domain definition). DAPFAM's public release also carries these labels if the
  local relations file does not.
Group by query domain and emit `A_domain_exposure.csv` with the columns already
specified in the round-1 header. Verification: column sums must reproduce
905 / 5,193 / 796 / 332 / 4,065.
If the domain field genuinely does not exist in any local artifact, report the
field names you did find before declaring BLOCKED.

## Task C2 (unblock C) — Final-872 outcomes by domain
Per-query Final-872 win/tie/loss records + the same domain labels.
Per-query records live with the A5 confirmation evidence (the bootstrap needed
per-query paired differences, so they exist somewhere under the A5 Owner-local
return). Locate them, join to domains, emit `C_final872_by_domain.csv`.
Verification: totals reproduce 619 / 158 / 95.

## Task E1b (unblock E1) — 25-cell common screen
Task D recovered the 52-row search space from "owner-local A2 candidate result
receipts" after the aggregate export fell short. Apply that same pattern to the
A1 common screen: read the owner-local A1 per-candidate receipts and emit the
25 cells (5 retrievers x 5 constructions) as `E1_screen_5x5.csv`.
Verification: the five per-retriever values must reproduce the paper's shared
screen column — 0.191 / 0.270 / 0.413 / 0.341 / 0.364.

## Task F2 (unblock F) — case studies
Needs query/target titles. DAPFAM is a public dataset: family identifiers from
the local artifacts join to titles and abstracts in the public release, so no
protected payload has to be copied into DATA_PACK. Steps:
1. From the pool + relations, pick 2-3 strict cross-domain queries with at least
   one relevant family absent from Top-200 (prefer one intuitive vocabulary-gap
   miss and one lexically-close surprising miss).
2. Pull titles (and first abstract sentence) for the query family and the absent
   relevant family from the public DAPFAM release.
3. Emit `F_case_studies.md`: identifiers, both titles, both domains, rank of the
   best found relevant family, and 2-3 neutral descriptive sentences each.
No speculation about why the system missed them beyond what the text shows.

## Task H2 (revised) — the depth extension is local and free; run it
Round 1 reported `UNKNOWN_DO_NOT_SPEND` because the paid provider was destroyed.
That framing is wrong for this job: no provider is needed. The retained shards
are the complete chunk embedding matrix, verified by arithmetic —
383,557,632 + 390,356,992 = 773,914,624 bytes = 193,478,656 float32 values =
188,944 chunks x 1024 dims exactly, matching the paper's chunk count. Deeper
retrieval is therefore a local dense matmul, not an API run:

1. Obtain the 1,247 query embeddings. If the A6 return retained them, reuse them
   unchanged. If not, re-embed the 1,247 query texts locally with the frozen
   ARM-03 checkpoint and prompt (`datalyes/patembed-large`, revision
   2d5c0f92a3e5dc3d5415c08e612c57543c0e03ad, prefix "encode query for different
   document retrieval:") — 1,247 short texts on CPU, minutes, no paid service.
   Verify the reuse path by reproducing the existing Top-200 for a sample of
   queries before going deeper; if the replay does not match, STOP.
2. Score 1,247 x 188,944 cosine similarities (~4.8e11 FLOPs, 0.77 GB resident —
   a few minutes with BLAS), apply the frozen max-p family aggregation, and take
   the top 1,000 families per query.
3. Write to a NEW output directory. Do not touch the frozen Top-200 pool or any
   existing hash/receipt.
4. Extend `B_depth_curve.csv` with k = 300, 500, 1000 (macro Recall@k and
   cumulative incidence found) as `B2_depth_curve_extended.csv`, and report the
   absent-from-Top-1000 count — the number that answers whether the exposure
   ceiling lifts with depth.
Verification: at k=100 and k=200 the extended run must reproduce 0.188450 and
0.260167 exactly. If it does not, the replay is not faithful — STOP and report
rather than publishing a curve that disagrees with the frozen pool.
Also fill the k=150 macro Recall left as NOT_EXPORTED in round 1.

## Deliverables
Updated DATA_PACK files above, an updated `G_manifest.md`, and
`PREP_REPORT_2.md` with per-task DONE/BLOCKED, every sanity check with pass/fail,
and for any remaining BLOCKED task: the exact paths searched and the field names
actually found. "Skipped" is not a state.
