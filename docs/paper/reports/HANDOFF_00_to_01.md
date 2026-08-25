# HANDOFF -- paper_00 to paper_01

## Manuscript task

Create the anonymous iSAI-NLP 2026 paper as an immutable sibling of `paper_00`,
using only canonical aggregate-safe evidence and the official IEEE conference
format.

## Current paper

`paper_01` is a receipt-bound, single-system DAPFAM case study. It connects the
A5 Final-872 held-out comparison to A6 complete-corpus materialization and an
A7 fixed-pool diagnosis. Raw relevant-family incidence counts remain separate
from the macro-Recall ordering oracle. No reranker, candidate-expansion, causal,
external-protocol, or generalization result is claimed.

## Evidence checked

- A4 population accounting audit, frozen selection registry and receipt, and
  the predeclared selection rule in the research plan.
- A5 final owner evaluation and result-integrity audit.
- A6 coverage, aggregate metrics, integrity audit, model manifest, execution
  configuration, pool hash, and determinism hash.
- A7 validated aggregate CSV and integrity audit.
- Venue rules, access policy, canonical source-of-truth pointers, and the
  literature audit for every retained citation-dependent claim.

## Accepted changes

- Rebuilt the story around one research question and the A5-A7 evidence chain.
- Added aggregate-safe A4 selection lineage and configuration fingerprints.
- Added deterministic evidence-chain and OUT-diagnosis figures.
- Removed displayed equations and earlier exploratory numeric chronology.
- Narrowed the contribution throughout to one receipt-bound DAPFAM case study.
- Preserved all negative and limiting evidence, including the fixed-pool oracle
  interpretation and the absence of intervention tests.

## Validation state

- Scientific review: PASS; no BLOCKER or MAJOR remains.
- Build: PASS; four A4 pages using IEEEtran at 10 pt.
- Paper guard: PASS; zero displayed equations.
- Citations, references, figures, and labels: resolved.
- Anonymity scan: PASS.
- Font check: all embedded; no Type 3 fonts.
- Visual review: pages 1-3 PASS; page 4 recorded in the final visual report.

## Files changed

- `paper_01/manuscript/paper_isainlp2026.tex`
- `paper_01/figures/generate_figures.py`
- `paper_01/figures/isainlp2026/*`
- `paper_01/provenance/*`
- `paper_01/build/paper_isainlp2026.pdf` and build receipts
- `handoff/*`, `reviews/*`, `scripts/new_version.py`, and
  `scripts/version_diff.py`

`paper_00` was not modified.

## Unresolved items and blockers

- `TODO_VERIFY`: none.
- Blockers: none.
- Non-blocking environment notice: MiKTeX reports that update checks have not
  been run; this did not affect deterministic compilation or PDF validation.

## Next reversible action

Copy the final release bundle to `01_Research/docs/paper`, stage only that
directory, commit, push `main`, and verify the remote commit.
