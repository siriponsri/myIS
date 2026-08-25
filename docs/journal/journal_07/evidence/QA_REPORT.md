# Journal 07 QA Report

## Build and static checks

- Release build: **PASS** using `manuscript/scripts/build_release.ps1`.
- Outputs: submission 23 pages, reader preview 11 pages, title-page placeholder 1 page, graphical abstract PDF and PNG.
- LaTeX: no fatal errors, unresolved citations/references, `tabularx` width warnings, or overfull boxes in final logs.
- Release hashes: `evidence/release_hashes.csv`.
- JSON inputs: aggregate ledger, final system programs, and overlap audit all parse successfully.
- `journal_06/`: unchanged and a sibling of `journal_07/`.

## Evidence and wording checks

- Final-872 values and denominators match the checked A5 authority.
- Selection, development, confirmation, and post-confirmatory diagnosis remain separate.
- A2 incumbent values and decision classes match the closeout projection.
- BM25 parameters and tokenizer policy match the frozen adapter.
- Protected-data scan found no IDs, qrels, credentials, protected paths, raw rankings, or per-query payloads.
- Submission and reader PDF metadata identify the author as `Anonymous manuscript`.

## Visual QA

- MAIN did not inspect manuscript pages or figures.
- Disposable `visual_reviewer` agents inspected all 23 submission pages, all 11 reader-preview pages, Figures 1-4, and the graphical abstract in bounded batches.
- Final submission: **PASS**. Appendix Table A.9 was reinspected after float-spacing repair and passes.
- Standalone figures: **PASS**.
- Reader preview: **PASS WITH MINOR RESIDUALS**. Pages 8, 10, and 11 have unused lower-page space around Figure 3, the references-to-appendix transition, and the appendix tables. Figures and tables remain readable, complete, and unclipped.
- Reports: `evidence/visual_qa/v07_*.md`.

## Owner gates

- Title-page identity and contact fields.
- Funding, CRediT, repository/archive, and final availability details.
- Material novelty-positioning citation changes.
