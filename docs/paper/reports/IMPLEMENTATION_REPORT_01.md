# Implementation Report -- paper_01

Date: 2026-08-25

## Scope

Created an immutable iSAI-NLP 2026 sibling from `paper_00`. No canonical
research file was edited and no new experiment was run.

## Implementation

- Rewrote the manuscript around the problem-gap-RQ-method-result-limitation
  sequence required by the venue contract.
- Bound all quantitative claims to A5 confirmation and A6/A7
  post-confirmatory receipts.
- Added aggregate-safe A4 selection lineage to expose selection multiplicity,
  correction, access counts, denominators, and tie-breaking without protected
  membership.
- Added full configuration hashes to provenance and compact prefixes to the
  manuscript.
- Generated two deterministic publication figures from validated aggregate
  data and corrected the Fig. 2 `332` label placement.
- Removed unnecessary displayed equations and stale copied V08 artifacts from
  the new sibling only.
- Updated the versioning script to recognize both `conference_NN` and
  `paper_NN`; generated a deterministic version diff.

## Claim changes

- Added: fixed-pool candidate-exposure and ordering-headroom diagnosis.
- Narrowed: contribution to a single-system DAPFAM case study.
- Removed: A1-A4 exploratory result chronology and broad method claims.
- Preserved: held-out A5 effect, complete-corpus A6 values, negative A7
  evidence, limitations, and protected-data boundaries.

## Evidence and provenance

The authoritative mapping is `paper_01/provenance/claim_to_evidence.csv`.
Canonical values and full hashes are recorded in
`paper_01/provenance/protected_ledger.md`. The release manifest contains no
protected identifiers, rankings, qrels, per-query results, or raw payloads.

## Outcome

The final review artifact is `paper_01/build/paper_isainlp2026.pdf`. Scientific
and deterministic gates pass; visual closure is recorded separately.
