# Claim-to-evidence map

Authority: canonical repository tree SHA
a4d20734556c8c42236e678b8dd1c181c5fff867.

This map is for local verification. It preserves ArmIndex in implementation
paths while the manuscript uses RCRS as the publication-facing method name.

| Evidence ID | Role | Manuscript claim | Canonical repository path |
|---|---|---|---|
| E-A1 | development | five-retriever common screen | docs/progress_report/A1_common_screen_aggregate_eda_20260818.csv |
| E-A2 | development | heterogeneous per-retriever outcomes | docs/progress_report/A2_per_arm_autoindex_outcomes_eda_20260818.csv |
| E-A2M | development | 52 proposals and per-retriever executable-signature counts | campaigns/armindex-multiretriever-v2/manifests/a2-five-arm-candidate-manifest.v1.json |
| E-A2D | development | frozen incumbents and recorded A2 decision classes | control/armindex/a2/a2-goal004-closeout-projection.v1.json |
| E-A2R | development | 12-decimal round-half-even strict comparison | src/myis_research/armindex/autoindex.py |
| E-A3T | development | advanced-retriever transfer matrix | docs/progress_report/A3_transfer_matrix_eda_20260819.csv |
| E-A3C | development | best-single, fusion, and commercial controls | docs/progress_report/A3_fixed_controls_eda_20260819.csv |
| E-A3R | development | 12 candidates, three batches, one effective action signature | docs/progress_report/update_A3_19AUG2026.md |
| E-A4M | selection | profile-level Selection-125 metrics | outputs/publication/armindex/a5-a6-continuation-20260822/tables/a4_selection_profile_metrics.csv |
| E-A4P | selection | paired selection effects and W/T/L | outputs/publication/armindex/a5-a6-continuation-20260822/tables/a4_selection_pairwise_effects.csv |
| E-A4A | selection | population and exposure accounting | control/armindex/a4/a4-selection-125-population-accounting-audit-20260823.json |
| E-A4F | selection | FAST system frozen as static/common comparator before Selection exposure | 04_Owner_Stores/armindex/a4/a4-goal001-20260821T071350Z-sel01/selection-registry.json; selection-preflight-counter.json |
| E-BM25 | configuration | BM25 parameters, backend, and tokenizer policy | src/myis_research/armindex/bm25s_adapter.py |
| E-A5 | confirmatory | Final-872 effectiveness, intervals, latency, cost | control/armindex/a5/final-r03-20260822/A5_FINAL_OWNER_EVALUATION.json |
| E-A5I | confirmatory | completion, failure, and integrity checks | control/armindex/a5/final-r03-20260822/A5_FINAL_RESULT_INTEGRITY_AUDIT.json |
| E-A5W | confirmatory | frozen-winner binding | control/armindex/a5/final-r03-20260822/A5_FROZEN_WINNER_BINDING.json |
| E-A5F | confirmatory | frozen finalist registry and model properties | control/armindex/a5/final-r03-20260822/A5_FINALIST_REGISTRY.json |
| E-A6 | post-confirmatory | full-benchmark depth metrics and run accounting | control/armindex/a6/a6-result-integrity-audit-20260823.json |
| E-A6P | post-confirmatory | frozen Top-200 pool authority | control/armindex/a6/a6-frozen-pool-authority-20260823.json |
| E-A7I | diagnosis | canonical CPU02 claim boundary and integrity | control/armindex/a7/a7-result-integrity-audit-20260823.json |
| E-A7R | diagnosis | canonical CPU02 diagnosis receipt | outputs/publication/armindex/a7-seven-layer-diagnosis/a7-goal001-20260823T093525Z-cpu02/a7-diagnosis-receipt.json |
| E-A7M | diagnosis | exposure counts and Top-200 oracle aggregates | outputs/publication/armindex/a7-seven-layer-diagnosis/a7-goal001-20260823T093525Z-cpu02/a7-layer-aggregate-metrics.csv |
| E-O1 | split audit | zero exact query-record and normalized query-text overlap; family/source mapping unavailable | evidence/cross_stage_overlap_audit.json |
| E-P1 | package | machine-readable figure ledger and serialized Final systems | manuscript/data/aggregate_ledger.json; manuscript/data/final_system_programs.json |

## Mandatory semantic checks

- A1–A3 cannot be described as confirmatory.
- A4 is the single selection exposure; no profile may be selected from A5–A7.
- A5 compares exactly two frozen systems and is the only confirmatory result.
- The A5 RCRS system uses PatEmbed; FAST combines BM25 and Arctic. The result
  is not a same-retriever representation ablation.
- A2 contains 52 proposals and 52 distinct executable signatures; 44 were
  measured and 8 remained dormant.
- A6–A7 contain the frozen winner only and cannot create a comparator claim.
- A5 eligible-out has 17,429 relevant pairs in the Final-872 cohort.
- A5 selects OUT-eligible queries but evaluates all judged positive families for those queries; it is not strict-OUT relation recall.
- A6–A7 strict OUT has 905 judged queries and 5,193 positive relations.
- A5 and A6 OUT values are not a before/after series.
- IN and OUT are relation-scoped and can overlap at query level.
- The Top-200 oracle is an analytical bound, not an implemented reranker.
- External numerical comparison remains NOT COMPARABLE because the complete
  external protocol and configuration have not been verified.
- PatEmbed (repository ARM-03) has a research/non-commercial licensing boundary.
- No component-level causal claim is allowed because no hash-bound
  representation ablation was performed.
- The overlap audit supports query-record and normalized query-text separation only; it does not support family-level independence.
