# journal_08 — World Patent Information submission

Extended journal version of the iSAI-NLP 2026 conference paper. Practice-first
reframe for a patent-information audience, built on the same protocol plus the
pool-depth analysis, the IPC-section breakdown, and the failure cases.

## Files
- `main.tex` — the manuscript, targeting **elsarticle** (Elsevier). Build with
  `pdflatex main` → `bibtex main` → `pdflatex main` ×2.
- `figures/` — six figures as SVG (source) and PDF (for LaTeX). Figures 5 and 6
  are new to the journal version.
- `references/references.bib` — 14 entries, all verified.
- `DATA_PACK/` — every derived table behind the paper, with `source:` lines.
- `REVIEW_PROMPT.md` — the verification pass to run before submission.

## Build modes
`main.tex` carries two class lines. The first is active and produces the
single-column manuscript Elsevier asks authors to submit. Comment it out and
uncomment the second to get a two-column build that approximates the published
ScienceDirect layout. All six floats are `figure*`, so they span both columns in
that mode and behave as ordinary floats in the submission build.

## Build note
`elsarticle.cls` is provided by Elsevier / TeX Live and is **not** bundled here.
Any full TeX Live install or Overleaf has it. The class options are set to
`preprint,11pt,authoryear`; switch to `review` for double-spaced review copy or
`3p` for the journal's two-column layout if requested.

## Figure mapping
| # | file | status |
|---|---|---|
| 1 | overview_evidence_map | redrawn to journal convention |
| 2 | fig1_a3_transfer | redrawn to journal convention |
| 3 | fig2_a5_confirmation | redrawn to journal convention |
| 4 | fig3_a7_diagnosis | redrawn to journal convention |
| 5 | fig5_depth_vs_ordering | new, the paper's central figure |
| 6 | fig6_section_exposure | new |

## Before submission (human)
1. Verify the author block, CRediT statement, acknowledgements, and the
   generative-AI declaration against `../authors.md`.
2. The owner decision is to submit this manuscript as a **regular article**.
   A secondary ServiceSetu listing for the WPI special issue "IP Data Analytics
   and IP Strategic Management using LLM/Generative AI/Agentic AI" gives a
   submission deadline of **31 December 2026** (opened 1 February 2026). The
   official ScienceDirect call page returned HTTP 403 during the check, so this
   listing is recorded as contextual evidence only and does not change the
   routing decision.
3. Verify the repository link resolves and the preregistration artifact with its
   freeze receipt is reachable.
4. Run `REVIEW_PROMPT.md` and fix anything it flags.

## Overleaf handoff
Create a new Overleaf project, upload the contents of this directory (including
`figures/` and `references/`), and set `main.tex` as the main document. Select
the Elsevier/TeX Live compiler; `elsarticle.cls` and `elsarticle-harv.bst` are
provided by the platform. Run LaTeX, BibTeX, then LaTeX twice. The local
verification is the reproducible pre-upload check; no authenticated Overleaf
session is available from this workspace, so the online compile remains a
manual owner step.

## Immutable numbers
905 judged queries · 5,193 incidences · 796 / 332 / 4,065 · Final-872 619/158/95
· Recall@100 0.188450 · Top-200 bound 0.260167 · depth bounds 0.317703 /
0.409842 / 0.529463. Any change to these is a defect, not an edit.
