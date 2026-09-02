# Final wording report for journal_09

Date: 2026-09-01

## Scope and invariants

This pass changes wording only. It does not change any reported result, numeric
value, figure, table, section structure, or citation key. The existing
`journal_08` worktree changes were not touched.

## Before/after record

| Item | Before | After | Status |
|---|---|---|---|
| Section 2.2 citation linkage | Krestel et al. and Rees and Wirz appeared in a generic list of earlier WPI work. | Rees and Wirz are linked to the six-system, Top-100 opposition-prior-art evidence and its low overlap; Krestel et al. provide the historical deep-learning context. | DONE |
| Introduction novelty | The contribution paragraph did not state the quantitative decomposition up front. | It now states that the frozen, held-out-validated configuration decomposes Recall@100 error into non-exposure and misordering, with the former roughly fivefold larger and persisting at fivefold depth. | DONE |
| Section 6.2 claim boundary | “the ranking is not the constraint” and “costs nothing but compute to keep.” | “within the confirmed configuration, ranking was not the dominant measured constraint,” followed by the replay-specific fact that the retained ranking needed no additional scoring pass. | DONE |
| Section 7.2 cost boundary | “Deeper retrieval is inexpensive, since the candidate scoring is already done.” | The sentence is limited to the replay and notes that production ANN systems may incur latency and memory costs at depth 1,000. | DONE |
| Result 1 wording | Abstract and heading: “construction choices do not reorder engines.” | Abstract and heading: “construction choices do not stably reorder engines.” | DONE |
| Table 2 explanation | The prose stated only that the table showed mixed responses. | The body now explains that the columns are different decision contexts and that “tie” is the decision rule's outcome, not equality of scores. | DONE |

## Author and source verification

The `poce2026survey` bibliography record remains Sara Poce and Gianni Cerro.
The DOI registry record lists exactly these two authors and reports *World
Patent Information* 85, article 102439:

- DOI record: https://doi.org/10.1016/j.wpi.2026.102439
- Crossref API: https://api.crossref.org/works/10.1016/j.wpi.2026.102439
- Article PII page: https://www.sciencedirect.com/science/article/pii/S0172219026000141

The PII page could not be reopened in the final automated check: ScienceDirect
returned HTTP 403 and no interactive browser session was available. Direct
PII-page re-verification is therefore **BLOCKED**. The entry was not guessed or
expanded; as required, it now carries an open verification note recording the
unresolved direct-page check and the two names returned by Crossref.

The related-work metadata used in this pass is available at:

- Rees and Wirz (2025): https://doi.org/10.1016/j.wpi.2025.102358
- Krestel et al. (2021): https://doi.org/10.1016/j.wpi.2021.102035
- Lee and Hsiang (2021; U002): https://doi.org/10.48550/arXiv.2009.09132
- Rathee, MacAvaney, and Anand (2025; U064): https://arxiv.org/abs/2501.09186

## Word budget and build validation

- Body words before: 4,753
- Body words after: 4,803
- Net change: +50 words
- Allowed net increase: at most +60 words
- Word-budget status: PASS

- Build sequence: `pdflatex -> bibtex -> pdflatex -> pdflatex -> pdflatex`
  with the local `elsarticle.cls`: PASS
- Undefined citations: 0
- Undefined references: 0
- Final PDF: 21 pages
- Visual inspection of affected pages 4, 5, 12, and 16: PASS (no clipping,
  overlap, broken table, or unreadable glyph)
- `git diff --check`: PASS
