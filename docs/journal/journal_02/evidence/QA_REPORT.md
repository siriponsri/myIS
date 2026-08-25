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
- PASS — every figure was inspected at source resolution; no title, legend, label, or annotation crosses a panel boundary.
- PASS — the graphical abstract is 4,264 × 1,348 pixels.
- PASS — the no-ai-slop vocabulary and structural scan found no banned term, importance puffery, throat-clearing phrase, or generic recap ending.
- PASS — the four highlights contain 69–74 characters, below the 85-character limit.

## Document and leakage checks

- PASS — submission manuscript, reader preview, and title-page placeholder compile without a fatal error.
- PASS — final logs contain no overfull box, unresolved citation, unresolved reference, multiply-defined label, or oversized-float warning.
- PASS — all eight reader-preview pages and all seventeen submission pages were rendered; figure, table, reference, appendix, and title-page pages were inspected at full resolution.
- PASS — the reader preview has 8 pages; the single-column submission copy has 17 pages; the separate title page has 1 page.
- PASS — Introduction through Conclusion contains approximately 3,319 words; the abstract contains approximately 208 words.
- PASS — no author identity, personal email, workspace path, or repository identity appears in the blinded manuscript PDFs.
- PASS — no raw query, patent/family identifier, qrels, ranking, or per-query result payload is included. These terms occur only in the explicit non-redistribution statement and verifier instructions.

## Output hashes

| Output | SHA-256 |
|---|---|
| RCRS_WPI_MANUSCRIPT_V04_READER_PREVIEW.pdf | cee1ba0b8a5477188d668a1017b2a472edbf2f470ffe79e3ff91f6bc8a476982 |
| RCRS_WPI_MANUSCRIPT_V04_SUBMISSION.pdf | f3d80ad2b6c6db2e6fd53ca297c824f8cb24532e5533cf7f82359e27d13caa5e |
| RCRS_WPI_TITLE_PAGE_PLACEHOLDER_V04.pdf | ad2f048cb45e32b5610c1fb80575c42f6cf79c0e3bafd67b2d39f84f43961573 |
| RCRS_WPI_GRAPHICAL_ABSTRACT_V04.pdf | af2a8d4efe8a88a3f2e8713d3d098c95bf87e7c9d9df5cfdf2090150161aebce |
| RCRS_WPI_GRAPHICAL_ABSTRACT_V04.png | ef110fb0251f50e932601d669d7f790d0739c56326e20f4a88869dccea8262d6 |
| elsarticle.cls | 01addb492c5d075b320636ac3a30d8a5762fa937220dea07a5e107042d25384d |
| elsarticle-num.bst | 0db2e53b2378cbe5815e436c1afe9dcac67123a32406fa8f11fad7978808e202 |

## Owner and local-verifier gates still open

- Verify every aggregate against the canonical local repository.
- Confirm author identities, affiliations, corresponding-author details, funding, acknowledgements, CRediT roles, and competing interests.
- Confirm repository/archive URL and final data-availability wording.
- Perform the adversarial reviewer audit after the local verification commit.
- Recheck journal and AI-disclosure rules immediately before submission.
