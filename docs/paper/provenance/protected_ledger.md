# Protected Ledger - paper_02

This ledger was recorded before the iSAI-NLP rewrite. Every item must retain
its canonical meaning, denominator, aggregation rule, and evidence class.

## Study identity and boundaries

- Venue: iSAI-NLP 2026; IEEE conference format; at most six pages;
  double-anonymous review.
- Benchmark: DAPFAM.
- Frozen winner: ARM-03, `datalyes/patembed-large`.
- A4: four registry entries frozen before selection; one Selection-125 access;
  complete 125-query coverage; declared OUT metric denominator 90; six
  preregistered pairwise comparisons with 10,000 bootstrap resamples and
  Holm--Bonferroni correction; zero final accesses.
- A4 selection rule: lexicographic OUT Recall@100, nDCG@100 when the absolute
  Recall difference is below 0.005, nDCG@10 when the nDCG@100 difference is
  below 0.002, then p95 latency, cost/index size, and configuration simplicity.
- Selection-125 and Final-872 are separate frozen scopes governed by the same
  parent split commitment. No membership, protected identifier, or stronger
  disjointness claim is released.
- A5: one held-out Final-872 access; paired query-level bootstrap with 10,000
  resamples; aggregate-safe reporting only.
- A6: post-confirmatory materialization; zero selection/final accesses; 45,336
  documents; 1,247 queries; family Top-200 pool; 249,400 pool rows.
- A7: CPU-local post-confirmatory diagnosis of the immutable A6 pool; zero
  selection/final accesses; no pool expansion; no reranker selection.
- The IN and OUT strata contain 1,217 and 905 judged queries and are not
  additive. ALL uses 1,247 judged queries.
- Claim-boundary terms: `held-out`, `receipt-bound`, `frozen pool`,
  `analytical bound`, `not a reranker`, `no external generalization`.

## Confirmatory values (A5 Final-872 OUT)

- Dense Recall@100: 0.4424757900101942.
- BM25 Recall@100: 0.33109709480122335.
- Paired Recall@100 delta: +0.11137869520897027; 95% percentile-bootstrap CI
  [0.10229357798165122, 0.12043832823649343].
- Dense nDCG@100: 0.3655952439732403.
- BM25 nDCG@100: 0.2792530034573017.
- Paired nDCG@100 delta: +0.08634224051593878; 95% CI
  [0.07867335584624419, 0.09407655981032025].

## Complete-corpus values (A6/A7)

- ALL Recall@100: 0.438964626214; nDCG@100: 0.362497103931.
- IN Recall@100: 0.528164111236; nDCG@100: 0.406513126603.
- OUT Recall@100: 0.188449898653; nDCG@100: 0.070644223566.
- ALL relevant-family incidences: 24,929 = 10,938 exposed by rank 100 +
  2,689 first exposed at ranks 101--200 + 11,302 absent at rank 200.
- OUT relevant-family incidences: 5,193 = 796 exposed by rank 100 + 332 first
  exposed at ranks 101--200 + 4,065 absent at rank 200.
- OUT query exposure classes: 905 = 67 fully exposed by rank 100 + 297
  partially exposed by rank 100 + 86 deep-only at ranks 101--200 + 455 with no
  relevant family exposed by rank 200.
- OUT fixed-pool oracle Recall@100: 0.260166940437.
- OUT ordering headroom: 0.071717041784 macro-Recall units, computed within the
  same Top-200 family pool. It is an upper bound, not a reranker result.

Raw incidence counts and macro-averaged Recall values have different units and
aggregation rules. They are complementary diagnostics and are never additive.

## Descriptive sensitivity

- Raw self-relations removed: 40, all outside the OUT relevance set.
- OUT Recall@100 after removal: 0.188449898653 (delta 0).
- OUT nDCG@100 after removal: 0.070644223566 (delta 0).
- Boundary: raw-identifier sensitivity only; no protected split membership was
  inspected and no broader leakage claim is supported.

## Hash bindings

- A5 winner configuration SHA-256:
  `285e94b1e76b4fcbc941daa524c71db213f63d21e1fab06dc2931ddf6dee26fc`.
- A6 model manifest SHA-256:
  `0ae9ed779d0eb40cce3d84149ab6e53681665aa841739b7c93d2cc28ac4b962c`.
- A6 execution configuration SHA-256:
  `e560e565e451321f29ff2f81ef87187d3c361095b78681132cd654bbc06acd5f`.
- Dense program SHA-256:
  `bcbffffa1a1836653fa833c3e5a64aa69620cf53c3907ee1fc47d83b143a48e3`.
- Baseline program SHA-256:
  `00f1c29507e55a70eb6f9046a24253f5c8f9726bfe5ca521309a84d779674397`.
- A6 pool SHA-256: `9ede1cee084db346743eb7e3dcbf300ac013c60055403f58449169dd71041879`.
- A6 determinism SHA-256: `3c72d4ed8b7c69eeebb842df36ecc4e2832d8ad7108eb249ac7f3b16fd6dee23`.
- Canonical A7 aggregate CSV SHA-256:
  `ad869ef99254df10c2e155911a1aa1a975dc9e41f1203bffa1fac2ab66043c1e`.

## Citation keys retained

`ayaou2025dapfam`, `yousefiramandi2026patent`,
`robertson2009probabilistic`, `karpukhin2020dense`, `thakur2021beir`,
`khattab2020colbert`, `xiong2021ance`, `nogueira2019passage`,
`jarvelin2002cumulated`, `davison1997bootstrap`.
