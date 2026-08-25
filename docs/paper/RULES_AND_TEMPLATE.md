# Paper 01 iSAI-NLP Rules and Template Contract

## Scientific rules

- Use canonical A5-A7 receipts as the only numeric authority.
- Keep A5 confirmation separate from A6/A7 post-confirmatory diagnosis.
- Label A7-L7 values as frozen-pool analytical bounds, never reranker results.
- Keep raw incidence counts separate from macro-Recall quantities.
- Do not claim external protocol comparability, causal attribution, reranker
  efficacy, pool-expansion efficacy, or external generalization.

## Review rules

- English, A4, official IEEE conference two-column, at most 6 pages.
- Use the supplied `IEEEtran.cls`; do not edit margins, class, or font sizes.
- Keep author, affiliation, funding, repository, and institution identifiers
  out of the review version.
- Every figure/table must be cited and trace to an aggregate-safe source.
- Keep references real and verifiable; mark unresolved metadata as TODO.

## Build template

From `docs/paper/manuscript`, run latexmk with `../build` as the output
directory. The tested review artifact is `build/paper_isainlp2026.pdf`. Before
release, check page count, anonymous metadata, no template guidance text, and
`git diff --check`.
