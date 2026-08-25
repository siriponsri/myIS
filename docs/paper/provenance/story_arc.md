# iSAI-NLP 2026 Story Arc

## Title

Diagnosing Candidate Exposure after Held-Out Confirmation in Cross-Domain Patent Retrieval

## Thesis

After one held-out comparison freezes the system, a complete-benchmark audit
shows candidate absence across OUT queries and relevant-family incidences, then
bounds macro-Recall ordering headroom within the same Top-200 pool.

## Evidence sequence

1. **Problem:** Recall@100 alone cannot distinguish low ordering from absence.
2. **Gap:** The distinction is often asserted but not bound to a frozen,
   post-confirmatory family pool.
3. **RQ:** What does the frozen OUT pool show about candidate absence and
   within-pool ordering headroom?
4. **Design:** A5 confirms once; A6 materializes; A7 audits without reselection.
5. **Finding:** 455/905 OUT queries have no relevant family in Top-200;
   4,065/5,193 OUT incidences are absent at rank 200; the same query population
   has 0.071717 macro-Recall ordering headroom.
6. **Boundary:** Query counts, incidence counts, and macro averages are
   complementary, not additive.

## Claim boundary

The paper reports aggregate-safe benchmark evidence only. It does not claim
universal superiority, external generalization, a learned reranker result,
pool-expansion efficacy, causal or legal impact, or release of protected data.
