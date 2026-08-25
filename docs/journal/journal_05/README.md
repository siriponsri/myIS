# RCRS WPI Manuscript V0.4 — nomenclature and visual audit

The package contains one scientific manuscript. All evidence needed for the
article is in `manuscript/main.tex`, including the aggregate appendix.
There is no supplementary manuscript.

Two PDFs are compiled from the same blinded source:

- `output/pdf/RCRS_WPI_MANUSCRIPT_V04_READER_PREVIEW.pdf` is the preferred
  reading copy. It uses the official Elsevier `elsarticle` class in compact
  5p/two-column mode to approximate the density of a published *World Patent
  Information* article.
- `output/pdf/RCRS_WPI_MANUSCRIPT_V04_SUBMISSION.pdf` is the single-column
  manuscript compiled in the default `preprint,12pt` mode.

The reader preview is not an Elsevier production proof. It does not fabricate
the publisher masthead, article number, copyright line, or final pagination.
Elsevier adds those elements during production.

## WPI upload map

The current WPI guide uses double-anonymized review. The practical upload set
for this package is:

1. blinded main manuscript: `manuscript/main.tex` and its source files;
2. separate title page: `manuscript/title_page.tex`;
3. separate highlights file: `manuscript/highlights.txt`;
4. figure source files if requested by Editorial Manager;
5. optional graphical abstract as a separate file.

No item is uploaded as “Supplementary Material.” The appendix is part of the
main manuscript. Highlights remain separate because WPI requires them at
submission. The graphical abstract is optional and is not scientific
supplementary material.

Official rules checked 2026-08-24:

- WPI Guide for Authors:
  https://www.sciencedirect.com/journal/world-patent-information/publish/guide-for-authors
- Elsevier graphical-abstract guidance:
  https://www.elsevier.com/researcher/author/tools-and-resources/graphical-abstract
- Elsevier artwork sizing:
  https://www.elsevier.com/en-gb/about/policies-and-standards/author/artwork-and-media-instructions/artwork-sizing

## Layout and figure basis

Recent WPI articles use a full-width front matter block, compact two-column
body, numbered headings, restrained wide figures and tables, plain captions,
and booktabs-style horizontal rules. The reader preview follows that pattern
without imitating publisher-owned branding.

The V0.4 audit removes interface-style cards, all-caps workflow labels, status
banners, and decorative stage blocks. Figure 1 is now a plain scientific
schematic built from text, points, and thin rules. Figures 2–4 retain standard
chart forms and use model names rather than repository arm numbers. The
optional graphical abstract is a three-panel methods/results graphic rather
than an infographic. Vector PDF is the submission master; 600-dpi PNG is
included for inspection.

Tone and visual editing follow the minimum-edit rules from
`petergyang/no-ai-slop`: direct claims, concrete verbs, no importance
puffery, no interpretive metadiscourse, and no decorative formatting. Meaning
and evidence boundaries remain unchanged.

Recent WPI layout references reviewed:

- Kalinichenko and Willoughby (2025), *The effective use of artificial
  intelligence in patent searches*:
  https://www.sciencedirect.com/science/article/pii/S0172219025000547
- *A novel re-ranking architecture for patent search* (2024):
  https://www.sciencedirect.com/science/article/pii/S0172219024000299
- Sakaoka and Kano (2025), *A patent-basis analysis of technological trends
  and key players*:
  https://www.sciencedirect.com/science/article/pii/S0172219025000481

## Scientific lock

- Development (repository A1–A3): common screen, per-retriever search,
  transfer, and fixed controls only.
- Selection-125 (repository A4): the single selection exposure.
- Final-872 (repository A5): the confirmatory comparison.
- Post-confirmatory analysis (repository A6–A7): depth run and diagnosis of
  the frozen winner.
- Selection, Final-872, the winner, and the claim boundary are immutable.
- No new experiment may be presented as part of this evidence chain.

RCRS is the publication-facing method name. Model names replace ARM-01–ARM-05
in the manuscript and figures. ArmIndex, A1–A7, and ARM-01–ARM-05 remain in
the provenance mapping because canonical repository paths are unchanged.

## Package map

- `manuscript/main.tex` — blinded, main-only scientific source.
- `manuscript/scripts/build_reader_preview.sh` — compact reader build.
- `manuscript/title_page.tex` — separate unblinded placeholders.
- `manuscript/references.bib` — bibliography.
- `manuscript/highlights.txt` — four required submission highlights.
- `manuscript/figures/` — vector PDF and 600-dpi PNG artwork.
- `manuscript/scripts/build_figures.py` — deterministic aggregate figure build.
- `manuscript/data/DATA_PROVENANCE.md` — figure-data boundary.
- `evidence/EVIDENCE_MAP.md` — claim-to-artifact map.
- `evidence/QA_REPORT.md` — compile, layout, leakage, and boundary checks.
- `handoff/LOCAL_CODEX_HANDOFF.md` — constrained local verification steps.
- `output/pdf/` — compiled and visually checked PDFs.
- `output/figures/` — optional graphical-abstract deliverables.
- `cover_letter.md` — editor letter draft with owner-verification markers.

The included `elsarticle.cls` and `elsarticle-num.bst` were copied unchanged
from the official Elsevier package used by the Publication Starter Kit:
https://assets.ctfassets.net/o78em1y1w4i4/4MpsJHO0MOJ2xZuwGTAbOZ/7bc64af36477c5d6cfce335a1f872363/elsarticle.zip
(retrieved 2026-08-24).

## Local build

From `manuscript/`:

```bash
mkdir -p /tmp/mplconfig-rcrs-v04
MPLCONFIGDIR=/tmp/mplconfig-rcrs-v04 python3 scripts/build_figures.py
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
scripts/build_reader_preview.sh
latexmk -pdf -interaction=nonstopmode -halt-on-error title_page.tex
```

The local verifier should compare every aggregate value against the canonical
repository before any owner-approved revision or submission.
