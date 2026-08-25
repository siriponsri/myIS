# Journal 06 QA Report

Date: 2026-08-25

## Build and static checks

- PASS: `manuscript/scripts/build_release.ps1` regenerated figures and built all release files.
- PASS: blinded submission PDF, 22 pages.
- PASS: reader preview PDF, 11 pages.
- PASS: title-page placeholder, 1 page.
- PASS: no fatal LaTeX error, undefined citation/reference, or overfull box in final logs.
- PASS: `git diff --check`.
- PASS: all five standalone figure PDFs are vector-only; `pdfimages -list` reports no embedded raster image.
- PASS: release SHA-256 values are recorded in `evidence/release_hashes.csv`.

## Evidence and wording checks

- PASS: Final-872 compares frozen PatEmbed RCRS with frozen FAST (BM25 plus Arctic).
- PASS: the `+0.1114` result is not attributed to representation alone.
- PASS: A2 counts and the `1e-12` round-half-even decision rule match canonical evidence.
- PASS: Selection profiles and eligible/strict OUT populations are separated.
- PASS: macro query recall and pair-weighted exposure are not treated as the same metric.
- PASS: A6/A7 remain post-confirmatory and do not create a new comparator claim.
- PASS: no author identity or local workspace path appears in blinded manuscript text.
- PASS: no query IDs, family IDs, qrels, per-query outcomes, credentials, raw rankings, or raw provider payload are included.
- PASS: `journal_05/` remains unchanged; 113 files match `journal_05_pre_j06.sha256.csv`.

## Visual QA

MAIN did not inspect images or rendered PDF pages. All inspection was delegated
to disposable `visual_reviewer` agents, which returned text-only reports.

- PASS: submission pages 1-22. Reinspection confirms the page 9 table balance,
  Figure 3 label size, page 13 balance, and reference/appendix blank-page fixes.
- PASS: reader pages 1-9 and 11.
- MINOR: reader page 10 has unused space at the bibliography-to-appendix transition.
  There is no isolated reference fragment, clipping, overlap, or forced blank page.
- PASS: Figures 1-4 and graphical abstract, including FAST/RCRS wording,
  label legibility, contrast, and grayscale cues.
- Reports: `evidence/visual_qa/*.md`.
- Superseded inspection reports: `evidence/visual_qa/archive_pre_v06_final/`.

## Owner gates

The manuscript is not submission-ready until the owner resolves cross-stage
family-overlap evidence, author/title-page details, funding, CRediT, final
disclosures, repository/archive release details, data availability, and final
journal AI-policy wording.
