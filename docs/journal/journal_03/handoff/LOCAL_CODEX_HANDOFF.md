# Local Codex handoff — V0.4 main-only

Recommended verifier: gpt-5.6-sol with high reasoning, operating on the
canonical local repository.

## Authorization boundary

You may verify and integrate this manuscript package. Do not reopen
experiments, modify Selection-125, rerun Final-872, change the winner, add a
post-hoc comparator, or expand the claim boundary. If an integrity or
metric-semantic inconsistency appears, stop and report it. Do not silently
rewrite a number or reinterpret a population.

## Suggested workflow

1. Create a non-default branch, for example `paper/rcrs-wpi-draft-v04`.
2. Copy this package into a publication-only directory without changing
   canonical experiment artifacts.
3. Resolve the repository at tree SHA
   `a4d20734556c8c42236e678b8dd1c181c5fff867`, or record the replacement
   commit if the repository has advanced.
4. Verify every row of `evidence/EVIDENCE_MAP.md` against the canonical file.
5. Check model names, dimensions, context declarations, and licenses against
   the frozen finalist registry and model-card snapshots.
6. Regenerate figures and compare their aggregate values with A1–A7.
   Publication-facing labels must use study-step names and model names; keep
   A1–A7 and ARM-01–ARM-05 only in provenance mapping.
7. Compile the main submission manuscript, reader preview, and title page in a
   clean directory. There is no supplementary manuscript.
8. Scan for query IDs, patent/family IDs, qrels, rankings, per-query values,
   credentials, owner paths, and author identity in blinded files.
9. Check the Git diff and commit only publication-package files.
10. Return the commit hash, compile logs, verification matrix, and unresolved
    issues before any prose-level revision.

## Build commands

From `manuscript/`:

```bash
mkdir -p /tmp/mplconfig-rcrs-v04
MPLCONFIGDIR=/tmp/mplconfig-rcrs-v04 python3 scripts/build_figures.py
latexmk -C main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
scripts/build_reader_preview.sh
latexmk -C title_page.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error title_page.tex
```

## Required verification report

Report each item as PASS, FAIL, or NOT VERIFIED:

- A1 common-screen aggregates.
- A2 outcomes and canonical decision labels.
- A3 transfer matrix, fixed controls, and effective-signature count.
- A4 population, one-exposure status, metrics, intervals, and W/T/L.
- A5 872/872 coverage, exact metrics, paired intervals, W/T/L, operations,
  determinism, and frozen-winner binding.
- A6 1,247-query / 45,336-document / 249,400-row accounting and depth metrics.
- A7 CPU02 receipt, 5,193-pair exposure decomposition, query classes,
  observed values, analytical bound, and headroom.
- Denominator language in every caption, table, and Results paragraph.
- No external state-of-the-art or causal component claim.
- No protected payload or author identity in the blinded manuscript.
- No ambiguous A-stage/ARM-retriever labels in narrative text or figures.

## Owner-only decisions

Do not invent author names, affiliations, corresponding-author details,
funding, acknowledgements, CRediT roles, competing-interest disclosures,
repository/archive URLs, or the final data-availability statement. Leave the
placeholders and request owner approval.
