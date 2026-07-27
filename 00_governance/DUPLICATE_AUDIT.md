# Duplicate and dead-path audit

This is a review manifest, not an authorization to delete.

- Exact PDF scan: 17 duplicate SHA-256 groups containing 34 files.
- Duplicate clusters occur mainly in App evidence under `research/ref-paper/is1`,
  `is2`, and `shared`.
- A hash match alone is insufficient for canonical selection; verify title,
  DOI, publisher metadata, license, and provenance before consolidating.
- Empty Research shells are recorded in `CLEANUP_APPROVALS.md` and remain
  untouched until an explicit Owner decision.
- The retired Experience Brain runtime is not dead merely because it is old;
  process references and historical provenance must be checked first.

Recommended review order: exact hash -> semantic identity -> provenance owner ->
archive destination -> Owner YES/NO -> move -> re-run import/hash validation.
