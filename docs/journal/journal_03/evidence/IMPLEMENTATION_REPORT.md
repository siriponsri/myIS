# Implementation Report - journal_03

## Provenance

- Source version: `journal_02`
- Target version: `journal_03`
- Review implemented: `external_review/external_review_02.md`
- Implementation brief: `review_journal/external_review_02_implementation_brief.md`
- Review IDs: `R2-M1`--`R2-M12` (SAFE, implemented where evidence was available);
  owner/integrity gates listed below remain unresolved.
- Source folder was copied in full before editing. `journal_02` remains
  unchanged.

## Item status

### R2-M1 - Finite retriever-conditioned representation search

- Status: `IMPLEMENTED`
- Evidence-boundary status: `SAFE`
- Files changed: `manuscript/main.tex`
- Change: added the frozen-manifest -> compile -> effective-signature ->
  duplicate-skip -> view construction -> development evaluation -> status /
  decision-class -> freeze procedure, with verified A2/A3 accounting and
  flat-surface stop. No new search or experiment was run.
- Acceptance check: procedure and counts are visible in Methods/Results and
  preserve the canonical 52/44/8 and 12/1 accounting.

### R2-M2--R2-M12 - Evidence-preserving method, benchmark, split, metric,
  nomenclature, and prose clarifications

- Status: `IMPLEMENTED` for safe portions; no protected values were added.
- Files changed: `manuscript/main.tex`, `manuscript/scripts/build_figures.py`,
  regenerated deterministic figure outputs.
- Changes include separate query/candidate notation; benchmark-family
  construction and split ledger; `OUT_eligible`/`OUT_strict`; macro Recall and
  pair-level exposure definitions; frozen-system table with human-readable
  bindings and hash prefixes; A4/Figure 2A reconciliation; AutoIndex novelty
  clarification; binary nDCG and paired-bootstrap details; throughput versus
  equal-cost resource rows; benchmark-scale and non-legal relevance caveats;
  and terminology/no-slop edits. Aggregate values, denominators, winner,
  Selection-125, Final-872, and A6/A7 boundaries are unchanged.
- Post-build visual QA finding `VQA-J03-01` (MINOR, Figure 1A annotation
  collision) was implemented safely by splitting the frozen-retriever body
  label across two lines in `scripts/build_figures.py`; Figure 1 and dependent
  PDFs were regenerated and rebuilt.

### Owner/integrity gates (unresolved)

- Exact hidden Final-872 field/passage/pooling/index settings.
- Query-family overlap and family-leakage counts not exposed by the safe
  evidence projection; no zero-overlap claim is made.
- Owner-controlled authorship, affiliations, declarations, funding,
  acknowledgements, CRediT roles, repository/archive URL, licensing/data
  availability, and AI-policy wording.
- No new GPU experiment, reproduction, or benchmark was run.

## Files and hashes

- Key source/target SHA-256 checks: `main.tex`
  `70C7C3501296C87C079B04E443975579B29C532EE12A46244DBF7D324EBC195B` ->
  `F1A263A561EE52662CB4BBD87A07929937E0476B151A27BA5359B39F95FB8E72`;
  `title_page.tex` identical at
  `65638DD86E38DB0D6411096C16AE15DDDD00FD260E4ADF4CC5B7895B4CB64423`;
  `elsarticle.cls` identical at
  `01ADDB492C5D075B320636AC3A30D8A5762FA937220DEA07A5E107042D25384D`;
  `elsarticle-num.bst` identical at
  `0DB2E53B2378CBE5815E436C1AFE9DCAC67123A32406FA8F11FAD7978808E202`.
- `journal_02` was not edited; its key-file hashes were captured before target
  edits and rechecked after packaging. Official class/style files are
  byte-identical.
- Final packaged artifact hashes: submission `952DE37C2AB2D6E860170E5B470BDE93114F047823687A0C3F032FD9E4440B92`;
  reader preview `D26F0BF6E17E6D34A9A22CBF5FF2C2D67D67FA6820F3EAA88F1D8F3E036F5F89`;
  graphical abstract PDF `72ADD62D9C815E53B77E10F263FB5C7BEA8248DCE896C17B8816DE88F3D52793`.

## Commands and results

Commands were run from `journal_03/manuscript`.

| Command/check | Result | Log or artifact |
|---|---|---|
| `latexmk -C main.tex` and `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` | PASS | `manuscript/clean_main.log`, `manuscript/build_main.log`; `main.pdf`, 20 pages |
| Native reader-preview equivalent (four `pdflatex` passes with `bibtex reader_preview`) | PASS | `manuscript/build_reader_native_*.log`; `reader_preview.pdf`, 10 pages |
| `latexmk -C title_page.tex` and `latexmk -pdf -interaction=nonstopmode -halt-on-error title_page.tex` | PASS | `manuscript/clean_title.log`, `manuscript/build_title.log`; `title_page.pdf`, 1 page |
| `python311 scripts/build_figures.py` | PASS | `manuscript/build_figures.log`; deterministic figure outputs regenerated |
| `scripts/build_reader_preview.sh` | BLOCKED by WSL backing-disk availability | native equivalent passed |
| final-log scan for fatal errors, unresolved citations/references, and overfull boxes | PASS | `main.log`, `reader_preview.log`, `title_page.log`; first-pass warnings in intermediate logs cleared by subsequent passes |
| protected-data/anonymity/terminology scan | PASS | target manuscript and package scans; owner placeholders retained |
| source immutability/hash check | PASS | `journal_02` unchanged after target build and packaging |
| `git diff --check` | NOT AVAILABLE | workspace has no Git repository; no whitespace-error scanner was available |

## Visual QA

- All 20 submission pages, 10 reader-preview pages, 1 title-page page, and five
  figure PDFs were rendered to disposable PNGs in `%TEMP%\\rcrs_journal_03_render`.
- Visual inspection was delegated to disposable visual-QA agents; this
  implementation context did not open image payloads. Textual reports are
  recorded under `journal_03/evidence/visual_qa_j03_pages_01_04.md`.
  Pages 1, 2, and 4 had no findings; Figure 1A's label collision was fixed.
  Parent review must confirm pages not covered by this report.

## Residual risks and next action

- Owner metadata/declaration and hidden configuration gates remain the known
  blockers. The package is not submission-ready until those owner decisions
  are supplied and independently audited.
- No new retrieval or GPU work was authorized or performed.
