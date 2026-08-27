# Prism Manuscript Package

This ZIP is a self-contained working package for OpenAI Prism. Start with
`main.tex` and use `main.pdf` only as the current rendered reference.

## Working instructions

- Treat `00_READ_ME_FIRST.md`, `02_PRISM_MASTER_BRIEF.md`, and
  `evidence/CORE_EVIDENCE_A1_A7.md` as the scientific and editorial contract.
- Keep the manuscript anonymous and within the six-page IEEE conference limit.
- Do not invent experiments, metrics, confidence intervals, data splits,
  dataset facts, citations, or results.
- Preserve the distinction between development, Selection, Final confirmation,
  and post-confirmatory diagnosis. In particular, do not present A5 as causal
  proof of representation or the A7 oracle as an implemented reranker.
- Do not change reported numeric values without a traceable update to the
  canonical evidence. Current statistical macros in `main.tex` are complete;
  there are no placeholders to fill.
- Keep `main.tex`, `references/references.bib`, `IEEEtran.cls`, `IEEEtran.bst`,
  and the four PDF files under `figures/rebuilt/` together when compiling.

## Package layout

- `main.tex`: editable anonymous manuscript source.
- `main.pdf`: current six-page rendered reference.
- `references/`: BibTeX source.
- `figures/rebuilt/`: the four PDF figures referenced by `main.tex`.
- `evidence/`: compact, manuscript-facing claim and protocol authority.
- `venue/`: IEEE/iSAI-NLP format constraints.
- `01_STORY_ARC_BEYOND_THE_RETRIEVER.md`, `02_PRISM_MASTER_BRIEF.md`,
  `PRISM_EDIT_INSTRUCTIONS.md`, and `CHANGES.md`: editorial context.
- `PACKAGE_SHA256SUMS.txt`: hashes of all packaged files other than itself.

The package intentionally excludes build intermediates, historical render
images, raw data, protected data, and repository-only implementation material.
