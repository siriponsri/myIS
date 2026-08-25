# Aggregate figure-data provenance

This V0.6 package contains no query identifiers, patent/family identifiers,
qrels, rankings, or per-query outcomes. The figure builder copies only
aggregate-safe values from the immutable siriponsri/myIS repository at tree SHA
a4d20734556c8c42236e678b8dd1c181c5fff867.

| Figure content | Canonical repository path |
|---|---|
| A1 common screen | docs/progress_report/A1_common_screen_aggregate_eda_20260818.csv |
| A2 per-retriever outcomes | docs/progress_report/A2_per_arm_autoindex_outcomes_eda_20260818.csv |
| A3 retriever-transfer matrix | docs/progress_report/A3_transfer_matrix_eda_20260819.csv |
| A3 fixed controls | docs/progress_report/A3_fixed_controls_eda_20260819.csv |
| A4 Selection accounting | control/armindex/a4/a4-selection-125-population-accounting-audit-20260823.json |
| A5 Final-872 metrics and paired effects | control/armindex/a5/final-r03-20260822/A5_FINAL_OWNER_EVALUATION.json |
| A5 integrity and winner | control/armindex/a5/final-r03-20260822/A5_FINAL_RESULT_INTEGRITY_AUDIT.json; A5_FROZEN_WINNER_BINDING.json |
| A6 full-benchmark metrics | control/armindex/a6/a6-result-integrity-audit-20260823.json |
| A7 exposure and Top-200 oracle | outputs/publication/armindex/a7-seven-layer-diagnosis/a7-goal001-20260823T093525Z-cpu02/a7-layer-aggregate-metrics.csv |
| A7 claim boundary | control/armindex/a7/a7-result-integrity-audit-20260823.json |

Important denominator boundary: A5 OUT fields are an eligible-out Final-872
cohort aggregate with 17,429 relevant family-query pairs. A6/A7 OUT is the
strict relation-scoped population with 905 judged queries and 5,193 positive
family-query relations. Those denominators are not compared directly, and A6
is not described as a regression from A5.
