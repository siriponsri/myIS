# RCRS WPI Manuscript V0.6

This package contains one blinded scientific manuscript. The aggregate
evidence appendix is part of `manuscript/main.tex`; there is no supplementary
scientific manuscript.

## Release files

- `output/pdf/RCRS_WPI_MANUSCRIPT_V06_READER_PREVIEW.pdf`: compact two-column
  reading copy built with the official Elsevier class.
- `output/pdf/RCRS_WPI_MANUSCRIPT_V06_SUBMISSION.pdf`: single-column blinded
  submission manuscript.
- `output/pdf/RCRS_WPI_TITLE_PAGE_PLACEHOLDER_V06.pdf`: separate title-page
  placeholder that still requires owner-approved author details.
- `output/figures/RCRS_WPI_GRAPHICAL_ABSTRACT_V06.pdf`: vector master.
- `output/figures/RCRS_WPI_GRAPHICAL_ABSTRACT_V06.png`: 600-dpi copy.
- `evidence/release_hashes.csv`: SHA-256 hashes produced by the release build.

The reader preview is not a publisher proof. It does not add an Elsevier
masthead, article number, copyright line, or final pagination.

## WPI upload map

1. Blinded manuscript source and figures.
2. Separate title page after owner approval.
3. `manuscript/highlights.txt`.
4. Optional graphical abstract.

Do not upload the appendix as supplementary material; it is part of the main
manuscript.

## Scientific lock

- Development contains the common screen, per-retriever search, transfer, and
  fixed controls.
- Selection-125 is the single selection exposure.
- Final-872 is the frozen comparison of the selected PatEmbed RCRS system and
  the FAST system that combines BM25 and Arctic.
- The full-benchmark depth run and exposure diagnosis use the unchanged RCRS
  winner after Final-872.
- Do not reopen experiments, change the winner, add comparators, or change
  confirmed values.

The Final-872 result is a comparison of two complete frozen systems. It is not
an isolated estimate of the effect of representation.

## Package map

- `manuscript/main.tex`: blinded manuscript source.
- `manuscript/scripts/build_figures.py`: deterministic figure source.
- `manuscript/scripts/build_release.ps1`: complete V06 build and package copy.
- `manuscript/title_page.tex`: separate owner-gated title page.
- `manuscript/references.bib`: bibliography.
- `manuscript/highlights.txt`: submission highlights.
- `evidence/EVIDENCE_MAP.md`: claim-to-evidence map.
- `evidence/QA_REPORT.md`: release checks.
- `evidence/IMPLEMENTATION_REPORT.md`: review disposition and closeout.
- `handoff/LOCAL_CODEX_HANDOFF.md`: next-session instructions.

## Build

From the package root in PowerShell:

```powershell
rtk proxy powershell -NoProfile -ExecutionPolicy Bypass -File manuscript/scripts/build_release.ps1
```

The script regenerates figures, builds the submission manuscript, reader
preview, and title page, copies V06 release files, and writes SHA-256 hashes.

## Version workflow

For the next review, create `journal_07/` as a complete sibling copy of this
directory before editing. Keep earlier versions unchanged. After QA, commit
and push the new journal version from the `01_Research` repository.
