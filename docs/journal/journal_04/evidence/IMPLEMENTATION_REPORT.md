# Implementation Report - journal_04

## Provenance

- External review: `external_review/external_review_03.md`
- Source: `journal_03/`
- Target: `journal_04/`
- `journal_04/` was created as a sibling copy before edits. `journal_03/` was
  not modified.

## Review disposition

- Major 1: `OWNER GATE` — protected Final-872 field, passage, pooling, and
  index settings remain undisclosed.
- Major 2: `OWNER GATE` — family-overlap counts and leakage audit are absent
  from the safe evidence projection; no zero-overlap claim was added.
- Major 3: `PARTIAL / OWNER GATE` — A3's one effective signature remains
  reported; A2 unique signatures and decision thresholds are not exposed.
- Major 4: `PARTIAL / OWNER GATE` — the family transformation pipeline is
  described; member-selection, language, and duplicate-overlap rules remain
  unresolved rather than inferred.
- Major 5: `DONE` — canonical USD cost is 1.456818 for both systems and cost
  ratio is 1.000; throughput ratio remains 1.245.
- Major 6: `DONE` — clarified that the selected configuration and static common
  baseline were frozen before Final-872 and evaluated without tuning.
- Major 7: `DONE` — added method, protocol, empirical, and diagnostic
  contribution taxonomy and bounded the AutoIndex comparison.
- Major 8: `OWNER GATE / N/A` — no new citations were added without verified
  source records.
- Major 9: `OWNER GATE` — missing hardware/runtime facts were not invented.
- Major 10: `DONE` — availability text distinguishes internal auditability and
  configuration binding from independent reproducibility.
- Minor items: `DONE` where evidence-safe (OUT labels, promotional wording,
  PatEmbed licensing qualification, HarnessOpt terminology, and figure notes);
  unsupported threshold, BM25, bootstrap-seed, and declaration details remain
  owner-controlled.
- Layout: `DONE` — moved Figure 4 before Limitations to remove the delegated
  page-balance defect without changing scientific content.

## Files changed

- `manuscript/main.tex`
- `manuscript/scripts/build_figures.py`
- regenerated manuscript and figure outputs under `manuscript/` and `output/`
- delegated text reports under `evidence/visual_qa/`

## Build and text QA

- PASS — deterministic figure generation.
- PASS — main submission build: 21 pages.
- PASS — reader preview build: 10 pages.
- PASS — title-page build: 1 page.
- PASS — final logs contain no fatal LaTeX error, unresolved citation/reference,
  multiply-defined label, or overfull-box error.
- PASS — extracted-PDF scan contains no stale cost wording, promotional label,
  or ARM identifier in the reader manuscript.
- PASS — source/target sibling relation verified; `journal_03/` remains present
  and untouched.

## Visual QA

- PASS — pages 1–3: `evidence/visual_qa/pages_01_03.md`.
- PASS — pages 4–6: `evidence/visual_qa/pages_04_06.md`.
- PASS — pages 7–10 after Figure 4 move:
  `evidence/visual_qa/pages_07_10_reinspection.md`.
- PASS — Figures 1–3: `evidence/visual_qa/figures_01_03.md`.
- PASS — Figure 4 and graphical abstract:
  `evidence/visual_qa/figures_04_graphical_abstract.md`.

## Unresolved gates

Owner approval remains required for protected configuration disclosure,
family-overlap audit, A2 decision/signature accounting, hardware metadata,
additional verified literature, author/declaration fields, and final data/code
availability wording. The package is not submission-ready until these gates
are resolved.

## Prior-version integrity

`journal_03/` was used only as the source copy and evidence reference. No file
under `journal_03/` was edited or regenerated.
