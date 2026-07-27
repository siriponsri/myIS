# Duplicate and dead-path audit

This is a review manifest, not an authorization to delete.

- Exact PDF rescan on 2026-07-27: 16 duplicate SHA-256 groups containing 32
  files. The earlier 17/34 count drifted after the App evidence set changed.
- Duplicate clusters occur mainly in App evidence under `research/ref-paper/is1`,
  `is2`, and `shared`.
- A hash match alone is insufficient for canonical selection; verify title,
  DOI, publisher metadata, license, and provenance before consolidating.
- Empty Research shells are recorded in `CLEANUP_APPROVALS.md` and remain
  untouched until an explicit Owner decision.
- The retired Experience Brain runtime is not dead merely because it is old;
  process references and historical provenance must be checked first.

All 32 duplicate paths have active textual references. Git already stores
identical tracked blobs content-addressably, so retaining semantic aliases does
not duplicate Git object content. `PDF_DUPLICATE_MANIFEST.csv` records one
canonical path per hash and the disposition of each alias. Two aliases have
misleading filenames and are flagged for reference migration before archival:

- `shared/pdfs/42_section_based_patent_summarization_for_prior_2025.pdf`
  contains the self-supervised patent representation paper.
- `shared/pdfs/48_bge_reranker_v2_multi_granularity_cross_2024.pdf` contains
  M3-Embedding.

Recommended review order: exact hash -> semantic identity -> provenance owner ->
archive destination -> Owner YES/NO -> move -> re-run import/hash validation.
