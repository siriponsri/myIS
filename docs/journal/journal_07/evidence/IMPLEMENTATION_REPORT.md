# Implementation Report: journal_07

- External review: `external_review/external_review_06.md`
- Prism audit: `prism_audit/prism_audit_06.md`
- Source: `journal_06/`
- Target: `journal_07/`

## Review disposition

- Final-872 endpoint wording: **DONE**. The paper now says that metrics use all judged positive families for the 872 OUT-eligible queries; it does not call this strict-OUT relation recall.
- Complete-system interpretation: **DONE**. The headline result is framed as a comparison between two complete frozen systems, not a causal representation-only effect.
- Operational comparator provenance: **DONE**. BM25+Arctic is described as the prespecified operational comparator, with its pre-Selection registry and exact system binding recorded.
- A1/A2 decision consistency: **DONE**. The actual A2 incumbents are shown and the tie/gain decisions no longer compare against the common screen.
- Cross-stage overlap: **PARTIAL**. A CPU-local aggregate audit found zero exact query-record overlap and zero normalized query-text overlap across Train-250, Selection-125, and Final-872. Available metadata cannot test family or source-publication overlap, so the paper states that limit.
- Prior-art wording and novelty scope: **DONE** for safe edits. Claims are narrower and a DAPFAM/AutoIndex/RCRS contribution matrix distinguishes the work without claiming that basic text operations are new.
- Broader literature expansion: **OWNER GATE**. Adding citations that materially change novelty positioning requires owner approval and exact source verification.
- Method detail: **DONE**. Query formats, binary relevance, max-p meaning, final system programs, BM25 parameters/tokenization, and verification identifiers are explicit.
- Reproducibility package: **PARTIAL**. Figures read a machine-readable aggregate ledger; serialized final programs, release hashes, an overlap script/result, and provenance paths are included. Full public execution, per-query verification, cache state, and complete timing conditions remain unavailable.
- New Final comparator or representation-only rerun: **FORBIDDEN** in this refinement because it would reopen the frozen confirmation and add a Final comparator.
- Figures, tables, and layout: **DONE**. Protocol tables were merged, figure order was repaired, appendix tables were compacted, and final float placement was corrected.
- Operational cost wording: **DONE**. The unsupported cost row was removed rather than relabeled or inferred.
- AI declaration: **DONE**. The declaration names OpenAI Codex and contains no future-tense policy marker.
- Author, title page, funding, CRediT, repository/archive, and final availability details: **OWNER GATE**.

## Files changed

- Manuscript and submission text: `manuscript/main.tex`, `manuscript/highlights.txt`, `cover_letter.md`.
- Data and build: `manuscript/data/`, `manuscript/scripts/build_figures.py`, `manuscript/scripts/build_release.ps1`.
- Evidence and guidance: `README.md`, `evidence/EVIDENCE_MAP.md`, `evidence/scripts/cross_stage_overlap_audit.py`, build logs, QA reports, and visual-QA reports.
- Release outputs: V07 submission PDF, reader preview, title-page placeholder, graphical abstract, and SHA-256 list.

## QA summary

- Build: **PASS**. Submission 23 pages; reader preview 11 pages; title page 1 page.
- Text/static QA: **PASS**. No LaTeX errors, unresolved citations/references, overfull boxes, author identity, protected identifiers, protected paths, or raw benchmark payloads were found.
- Visual QA: **PASS WITH MINOR READER-PREVIEW RESIDUALS**. All 23 submission pages and all standalone figures pass. Reader pages have minor lower-page whitespace on page 8 after Figure 3, page 10 before the appendix transition, and page 11 below the appendix tables; no content is clipped or unreadable.
- Visual reports: `evidence/visual_qa/v07_*.md`.
- Prior version: **CONFIRMED UNTOUCHED**. `journal_06/` remains clean against Git and shares the same parent directory as `journal_07/`.

## Unresolved owner gates

- Final author identity, affiliations, contact details, ORCID, funding, and CRediT roles.
- Final title-page content, repository/archive identifiers, availability statement, and journal-policy confirmation.
- Any citation expansion that materially changes novelty positioning.
