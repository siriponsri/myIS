source: docs/figures/03_a1_common_screening.csv; docs/figures/06_a2_per_system_search.csv; docs/figures/10_a4_profiles.csv; docs/figures/11_a4_selection_pairs.csv; docs/figures/13_a5_confirmation_quality.csv; docs/figures/15_a6_depth_curve.csv; docs/figures/17_a7_exposure_anatomy.csv; docs/figures/18_a7_query_exposure.csv; docs/figures/19_a7_within_pool_bound.csv; outputs/publication/armindex/a7-seven-layer-diagnosis/a7-goal001-20260823T093525Z-cpu02/a7-layer-aggregate-metrics.csv; control/armindex/a4/a4-selection-125-population-accounting-audit-20260823.json; campaigns/armindex-multiretriever-v2/manifests/a2-five-arm-candidate-manifest.v1.json

# Reproduction manifest

All Task A-G outputs are post-hoc projections. No retrieval, indexing, embedding, reranking, or model execution was performed. The preregistration/freeze chronology is recorded in `docs/research/A1_2_PUBLICATION_IMPACT_PREREGISTRATION_V13.md` and the A2/A4/A5/A6/A7 control receipts. Protected Owner Store payloads are referenced by path only and are not copied into DATA_PACK.

| File | Exact source artifact(s) | Script/notebook |
|---|---|---|
| A_domain_exposure.csv | DAPFAM source contract + public DAPFAM `queries.parquet` IPC labels + A7 exposure anatomy + A6 pool + relation Arrow | post-hoc strict-OUT per-IPC3 projection |
| B_depth_curve.csv | A6 depth curve + A7 exposure anatomy | post-hoc table transcription |
| B2_depth_curve_extended.csv | A6 retained depth-2000 rankings + relation Arrow + token map | local replay and aggregation |
| C_final872_by_domain.csv | Public DAPFAM `queries.parquet` IPC labels + A5 qrels + returned paired rankings + owner evaluation | post-hoc per-query IPC3 recomputation |
| D_search_space.csv | A2 frozen candidate manifest + A2 aggregate outcomes | post-hoc accounting transcription |
| E1_screen_5x5.csv | A1 owner-local R15 cell EDA receipt + A1 aggregate figure | post-hoc 25-cell transcription |
| E2_selection125.csv | A4 selection profile metrics | post-hoc table transcription |
| F_case_studies.md | Public DAPFAM `queries.parquet`/`corpus.parquet` title, abstract, IPC3 + A6 pool + relation Arrow (`domain_rel=OUT`) | post-hoc safe-ID case selection |
| PREP_REPORT_2.md | JOURNAL_UNBLOCK_TASKS.md + all round-2 DATA_PACK files | round-2 closeout audit |
| I1_bound_by_pool_depth.csv | A6 retained depth-2000 rankings + relation Arrow + Rule 0 baseline | post-hoc oracle Recall@100 bound by pool depth |
| I2_section_exposure.csv | A_domain_exposure.csv + public DAPFAM IPC labels + Rule 0 relation/pool evidence | post-hoc A-H IPC section roll-up; O60 excluded |
| PREP_REPORT_3.md | JOURNAL_ARC_UPDATE.md + I1/I2/I3/I4 outputs | round-3 closeout and sanity audit |
