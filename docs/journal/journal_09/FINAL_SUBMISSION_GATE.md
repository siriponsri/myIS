# Final Elsevier Submission Compliance Gate

Date: 2026-09-02  
Target: *World Patent Information*, Regular Research Article  
Package: `docs/journal/journal_09/`

## Verdict

**READY TO SUBMIT — OWNER EM CHECKS REMAIN**

The repository-local manuscript, disclosure, support-file, flat-source-package,
clean-build, numerical-integrity, and visual checks pass. Exact Editorial
Manager Item Type names and form interactions are visible only in the live
submission workflow and are submission-time Owner checks, not artifact
readiness blockers.

Owner attestation is recorded as:

`AI_RESEARCH_CODE_ASSISTANCE = YES`

No scientific or compliance defect remains in the prepared artifact.

## Prepared files

- `main.tex` and refreshed `main.pdf`.
- `SUBMISSION_PACKAGE/` and flat `WPI_LaTeX_Source.zip`.
- `cover_letter.md`.
- `highlights.txt` and `Highlights.docx`.
- `Declaration_of_Competing_Interests.docx`.
- `AI_USE_AUDIT.md`, `ELSEVIER_AI_POLICY_NOTE.md`,
  `ELSEVIER_SUBMISSION_SUPPORT_NOTE.md`, and
  `DECLARATION_OF_COMPETING_INTERESTS_CHECKLIST.md`.

## Generative-AI compliance

- [x] The Owner attests that OpenAI Codex assisted research/code work.
- [x] Study design discloses the pre-measurement Official Codex candidate
  proposer/reviewer role: OpenAI Codex, model `gpt-5.6-sol`, SDK/CLI `0.144.4`,
  bounded aggregate-safe inputs, human review, no protected-data access, no
  retrieval execution, and freeze before measurement.
- [x] Study design discloses publication-figure-code generation and aggregate
  evidence validation: OpenAI Codex, model `gpt-5.6-sol`, CLI `0.149.1`,
  reproducible aggregate CSV inputs and assertions, human execution and
  verification, and no generation or alteration of underlying experimental
  data.
- [x] Study design distinguishes bounded AI proposal, implementation, and
  verification assistance from scientific decisions. The authors retain the
  study protocol, frozen comparisons, evaluation design, interpretation,
  conclusions, and reproducibility responsibility.
- [x] The final manuscript-preparation declaration uses Elsevier's exact
  heading, describes the verified language, organization, literature/citation,
  and document-verification uses, and appears immediately before References.
- [x] The final declaration points readers to the separate Study design
  disclosure and does not substitute for it.
- [x] No unsupported model/version is assigned to the later
  manuscript-preparation pass or to `journal_09/figures/redraw.py`.

## Figure-policy audit

| Figure | Policy class | Compliance result |
|---|---|---|
| `overview_evidence_map` | Explanatory/workflow image | PASS. Owner attestation supports Codex assistance with code associated with the figure workflow, but provenance does not bind a specific model/version to the submitted rendition. The caption therefore identifies OpenAI Codex, OpenAI, the code-assistance role, author review/verification, and states that the exact model/version was not retained. |
| `fig1_a3_transfer` | Data visualization derived reproducibly from aggregate research data | PASS. Covered by the Study design computational-generation disclosure; no separate caption disclosure required. |
| `fig2_a5_confirmation` | Data visualization derived reproducibly from aggregate research data | PASS. Covered by the Study design computational-generation disclosure; no separate caption disclosure required. |
| `fig3_a7_diagnosis` | Data visualization derived reproducibly from aggregate research data | PASS. Covered by the Study design computational-generation disclosure; no separate caption disclosure required. |
| `fig5_depth_vs_ordering` | Data visualization derived reproducibly from aggregate research data | PASS. Covered by the Study design computational-generation disclosure; no separate caption disclosure required. |
| `fig6_section_exposure` | Data visualization derived reproducibly from aggregate research data | PASS. Covered by the Study design computational-generation disclosure; no separate caption disclosure required. |

The figure PDFs themselves are unchanged. The only figure-related manuscript
change is the required disclosure text in the explanatory evidence-map caption.

## Scientific-integrity checks

- [x] Experiments, datasets, models, metrics, statistical analyses, tables,
  results, and claim boundaries are unchanged by this compliance pass.
- [x] Scientific numeric-token comparison against `HEAD`: 378 baseline tokens
  and 378 current tokens after excluding only the verified software identifiers
  `gpt-5.6-sol`, `0.144.4`, and `0.149.1`; delta `0`.
- [x] All six figure PDFs have zero Git diff from `HEAD`.
- [x] `references/references.bib` has zero Git diff from `HEAD`.
- [x] Source/support unresolved-marker scan returned zero hits.
- [x] `git diff --check` passes for `journal_09`.

## Flat LaTeX package

`SUBMISSION_PACKAGE/` is authoritative for Elsevier LaTeX upload. It contains
exactly 11 files at one folder level and no subdirectories or build products:

- `main.tex`, `references.bib`;
- `elsarticle.cls`, `elsarticle-harv.bst`, `numcompress.sty`;
- the six referenced PDF figures.

The submission copy changes only figure and bibliography paths required by the
flat layout. After those path normalizations, its source matches the working
`main.tex` exactly. It is UTF-8 without a byte-order mark.

Validation was executed independently from both a fresh working-source copy
and a fresh extraction of `WPI_LaTeX_Source.zip`:

`pdflatex -> bibtex -> pdflatex -> pdflatex`, followed by one additional
`pdflatex` convergence pass because the standard chain requested a label rerun.

Both builds produced 21 pages with zero undefined citations and zero undefined
references. At 110 dpi, all 21 rendered pages from the two builds were
pixel-identical.

- `main.pdf` SHA-256:
  `57D9DCC15A79915F8CF80CFFF21D851F23DCC27E96EEF4C0297F5207281021BA`
- `WPI_LaTeX_Source.zip` SHA-256:
  `7939BBC4F774820DD9A9F5F98CE295D55EA0EFE924C79345EC9142CB04A75DF6`

## Support files

- [x] Cover letter is 211 whitespace-delimited words, remains comfortably under
  one page, and includes aim, findings, novelty, WPI fit, and prior iSAI-NLP
  disclosure without funding or reviewer suggestions.
- [x] Highlights contain five bullets of 57--73 characters, including each
  leading marker and space; all are below Elsevier's 85-character limit.
- [x] `Highlights.docx` passed a fresh one-page render inspection with five
  visible bullets and no clipping or overflow.
- [x] The manuscript contains the required competing-interest declaration.
- [x] `Declaration_of_Competing_Interests.docx` contains the same author,
  manuscript, and declaration identity and passed a fresh one-page DOCX render
  inspection with no clipping, overlap, missing glyphs, or internal submission
  instructions.

## Manuscript visual inspection

The refreshed 21-page `main.pdf` was rendered page by page. All pages were
reviewed in contact sheets, with pages 6, 7, and 19 additionally inspected at
full rendered resolution for the explanatory-figure caption, Study design AI
disclosures, and final AI declaration. No clipping, overlap, broken figures,
unreadable glyphs, or incoherent page placement was observed.

## Submission-time Owner checks

These actions require the live Editorial Manager workflow and do not block the
prepared artifact:

1. Select the matching Item Type shown by Editorial Manager for each prepared
   manuscript, source archive, figure/highlights, cover-letter, and declaration
   file.
2. Upload `Declaration_of_Competing_Interests.docx` or complete the equivalent
   declaration interaction presented by the live workflow.
3. Assign/upload `Highlights.docx` if the WPI workflow exposes a Highlights
   Item Type.
4. Enter and verify author, affiliation, corresponding-author, keyword,
   funding, contributor-role, and other required metadata.
5. Inspect the Editorial Manager-generated submission PDF before finalizing.

No `journal_10` was created. No further polishing is authorized after this
gate passes.
