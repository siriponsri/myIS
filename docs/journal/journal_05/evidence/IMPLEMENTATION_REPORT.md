# Implementation Report: journal_05

- External review: `external_review/external_review_04.md`
- Source: `journal_04/`
- Target: `journal_05/` (sibling copy created before editing)
- Protected payload authorization was used only to verify safe configuration metadata; no query IDs, qrels, split membership, raw rankings, credentials, or provider payload were added.

## Disposition

- Major Issue 1, exact configurations: **DONE**. Added human-readable frozen-system metadata from the canonical ARM-03 program and static P00 specification, retaining hashes as bindings.
- Major Issue 2, cross-stage family leakage: **OWNER GATE**. No canonical aggregate overlap audit was available; no overlap value or zero-overlap claim was invented.
- Major Issue 3, search breadth: **PARTIAL / OWNER GATE**. Preserved the verified 52 proposals, 44 measured candidates, 8 dormant reserves, and strict-gain/tie rule; per-retriever unique-signature counts remain unavailable in checked aggregate receipts.
- Major Issue 4, family construction: **DONE** for the verified contract. Added member ordering, field, normalization, duplicate, unitization, aggregation, passage, and overlap details; language filtering and a separate near-duplicate rule are explicitly marked not declared.
- Major Issues 5--8: **PARTIAL / OWNER GATE** where they require public artifact release, comparator adequacy claims, new evidence, or expanded literature/novelty positioning. Safe terminology and selection-boundary clarifications are retained.
- Layout and figure findings: **DONE** for implemented safe fixes. Figure 4 placement and labels were corrected; page 2--3 pagination was adjusted after visual feedback.

## Verification

- Main manuscript build: PASS, 22 pages.
- Reader preview build: PASS, 10 pages.
- Title page build: PASS, 1 page.
- Build logs: `evidence/build_main.log`, `evidence/reader_pass1.log`, `evidence/reader_bib.log`, `evidence/reader_pass2.log`, `evidence/reader_pass3.log`, `evidence/title_pass.log`.
- Static/text checks: citation and reference resolution, labels, protected-data scan, terminology, and `journal_04/` immutability checks completed; no output-affecting LaTeX errors or overfull boxes observed.
- Visual QA: delegated only to disposable `visual_reviewer` agents. Figures and pages 5--10 pass; final pages 1--4 reinspection is recorded in `evidence/visual_qa/submission_pages_01_04_final2.md`. Pages 1, 2, and 4 pass; page 3 retains a MINOR page-balance/whitespace finding. MAIN did not inspect images.

## Closeout gates

- Unresolved owner gates: cross-stage family-overlap aggregate; per-retriever unique-signature counts; public reproducibility/data-availability release; final author/disclosure/repository decisions; external literature expansion.
- `journal_04/` remains untouched.
- After visual reinspection, move `journal_01/`--`journal_05/` into `01_Research/docs/journal/`, then commit and push from the `01_Research` repository as requested by the owner.
