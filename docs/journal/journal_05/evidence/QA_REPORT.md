# V0.4 quality report — nomenclature and visual audit

Date: 2026-08-24  
Status: PASS FOR OWNER REVIEW AND LOCAL EVIDENCE VERIFICATION; NOT
SUBMISSION-READY

## Scientific boundary

- PASS — A1–A3 remain development evidence only.
- PASS — A4 remains the single Selection-125 exposure.
- PASS — A5 remains the only confirmatory comparison and contains two frozen systems.
- PASS — A6–A7 remain post-confirmatory and use the unchanged winner only.
- PASS — Final-872, the winner, and the claim boundary were not reopened.
- PASS — Final-872 eligible-out and post-confirmatory strict OUT denominators are not presented as a temporal series.
- PASS — the Top-200 oracle is an analytical ordering bound, not a reranker result.
- PASS — no external numerical-comparability or component-level causal claim was introduced.

## Nomenclature audit

- PASS — narrative text and figures use semantic study-step names: common screen, per-retriever search, transfer and fixed controls, Selection-125, Final-872, full-benchmark depth run, and candidate-exposure diagnosis.
- PASS — narrative text and figures use model names: BM25, BGE-M3, PatEmbed, Arctic, and Qwen3.
- PASS — no ARM-01–ARM-05 identifier appears in the manuscript.
- PASS — A1–A7 appear only in the repository-record explanation, the protocol mapping, and aggregate-ledger captions.
- PASS — the protocol table states that repository codes identify study records, not retrievers.

## Main-only WPI package

- PASS — all scientific content is in `main.tex`; the aggregate ledger is an appendix within the main manuscript.
- PASS — no supplementary manuscript or supplementary scientific output is present.
- PASS — title page and highlights remain separate submission items for the double-anonymized workflow; they are not supplementary material.
- PASS — the graphical abstract is optional and separate; it is not scientific supplementary evidence.
- PASS — the reader copy and submission copy compile from the same blinded source using the official `elsarticle` class.
- PASS — the reader copy follows the density of recent WPI articles without fabricating an Elsevier masthead, article number, copyright line, or final production pagination.

## Visual and prose audit

- PASS — Figure 1 was rebuilt as a plain scientific schematic using text, points, arrows, and rules; interface cards, status bars, workflow badges, and decorative stage blocks were removed.
- PASS — Figures 2–4 use conventional heatmap, dot, dumbbell, interval, line, and count-chart forms with direct labels and restrained color.
- PASS — Figure 2 uses a wider inter-panel gutter and shorter panel headings; Figure 3 uses wider three-panel spacing; Figure 4 moves end labels inward and separates the exposure and ordering panels.
- PASS — reader page 5 contains Table 3 and Figure 2 with prose between them; page 6 contains Figure 3 only; Figure 4 begins page 7. No page contains Figures 3 and 4 together.
- PASS — the graphical abstract is a three-panel methods/results figure rather than a marketing infographic.
- PASS — shape, line style, open/filled markers, and hatching preserve essential distinctions in grayscale.
- PASS — deterministic figures were rendered at source resolution; the disposable visual-QA report covers pages 1-4, and parent review must complete the remaining page/figure inspection.
- PASS — the graphical abstract is 4,264 × 1,348 pixels.
- PASS — the no-ai-slop vocabulary and structural scan found no banned term, importance puffery, throat-clearing phrase, or generic recap ending.
- PASS — the four highlights contain 69–74 characters, below the 85-character limit.

## Document and leakage checks

- PASS — submission manuscript, reader preview, and title-page placeholder compile without a fatal error.
- PASS — final logs contain no overfull box, unresolved citation, unresolved reference, multiply-defined label, or oversized-float warning.
- PASS — all ten reader-preview pages and all twenty submission pages were rendered; the separate title page has 1 page.
- PASS — current page counts are reader preview 10, submission 20, title page 1.
- PASS — Introduction through Conclusion contains approximately 3,319 words; the abstract contains approximately 208 words.
- PASS — no author identity, personal email, workspace path, or repository identity appears in the blinded manuscript PDFs.
- PASS — no raw query, patent/family identifier, qrels, ranking, or per-query result payload is included. These terms occur only in the explicit non-redistribution statement and verifier instructions.

## Current journal_03 build and visual scope

- PASS - submission PDF: 20 pages; reader preview: 10 pages; title page: 1 page.
- PASS - five one-page vector figures and the graphical abstract were regenerated from deterministic source code.
- VISUAL-QA SCOPE - disposable report `visual_qa_j03_pages_01_04.md` covers submission pages 1-4. Pages 1, 2, and 4 have no findings. Figure 1A's annotation collision was fixed by wrapping the frozen-retriever label and regenerating the figures. Parent review must inspect the remaining pages and figures.

## Output hashes

| Output | SHA-256 |
|---|---|
| RCRS_WPI_MANUSCRIPT_V04_READER_PREVIEW.pdf | D26F0BF6E17E6D34A9A22CBF5FF2C2D67D67FA6820F3EAA88F1D8F3E036F5F89 |
| RCRS_WPI_MANUSCRIPT_V04_SUBMISSION.pdf | 952DE37C2AB2D6E860170E5B470BDE93114F047823687A0C3F032FD9E4440B92 |
| RCRS_WPI_TITLE_PAGE_PLACEHOLDER_V04.pdf | A48944A68AE3858867C4AC4F5A40556877667DE57F4688C599E8F112D4180F23 |
| RCRS_WPI_GRAPHICAL_ABSTRACT_V04.pdf | 72ADD62D9C815E53B77E10F263FB5C7BEA8248DCE896C17B8816DE88F3D52793 |
| RCRS_WPI_GRAPHICAL_ABSTRACT_V04.png | 754319E277006DACAD8B2DED717F6C19A254158508195005BFADD9267605CE1E |
| elsarticle.cls | 01addb492c5d075b320636ac3a30d8a5762fa937220dea07a5e107042d25384d |
| elsarticle-num.bst | 0db2e53b2378cbe5815e436c1afe9dcac67123a32406fa8f11fad7978808e202 |

## Owner and local-verifier gates still open

- Verify every aggregate against the canonical local repository.
- Confirm author identities, affiliations, corresponding-author details, funding, acknowledgements, CRediT roles, and competing interests.
- Confirm repository/archive URL and final data-availability wording.
- Perform the adversarial reviewer audit after the local verification commit.
- Recheck journal and AI-disclosure rules immediately before submission.
