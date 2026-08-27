# Final Revision Edit Report

All fourteen edits in `FINAL_REVISION_TASK.md` are complete. The manuscript
source was changed only by the listed edits; no figure, label, citation, or
existing numeric token was changed.

| Edit | Before | After | Proof / source | Status |
|---|---|---|---|---|
| 1 | `The reordering is noise.` | `The reordering is noise---and bounded: the largest effect consistent with any of these intervals is 0.011 Recall@100, below the narrowest separation between the retriever bands (0.018).` | `main.tex` Section IV; PDF signature includes `The reordering is noise` with `0.011 Recall@100` and `retriever bands (0.018)`. `stats.json` gives Arctic CI upper `0.0114525` -> `0.011`; `07_a3_transfer_matrix.csv` gives `0.341341` and `0.359497`, gap `0.018156` -> `0.018`. | DONE |
| 2 | `and that effort spent tuning the ranker is wasted while most of the evidence is missing from the pool.` | `and that no amount of ranker tuning can recover evidence the pool never contained.` | Abstract; PDF signature (`pdftotext -raw main.pdf`): `never contained.` | DONE |
| 3 | `Cross-domain patent retrieval is exposure-bound, not ordering-bound.` | `On this benchmark, cross-domain patent retrieval is exposure-bound, not ordering-bound.` | Abstract; PDF signature: `this benchmark, cross-domain patent retrieval is exposure-bound,` followed by `not ordering-bound.` | DONE |
| 4 | `(within-target Recall@100 spread below 0.004)` | `(within-target Recall@100 spread below 0.004; every 95\% interval caps the effect below 0.011)` | Abstract; PDF signature: `every 95% interval caps the effect below 0.011`. | DONE |
| 5 | `78\% of relevant families never enter` | `78\% of relevant-family incidences never enter` | Abstract; PDF signature: `relevant-family incidences never enter the Top-200 pool`. | DONE |
| 6 | No operational definition of `construction`; no population bridge. | Added `By construction we mean ...`; added `The populations nest ...` with the strict relation criterion and distinct Final-872 population. | `04_document_representations.csv` defines the construction fields/units/aggregation. `FULL_PROJECT_REPORT_A0_A8_EN.md` defines cross-domain relations and the 905-query scope. PDF signatures: `The populations nest simply` and `905 judged queries drawn from all 1,247.` | DONE |
| 7 | Preregistration claim lacked artifact pointer. | Retained `preregistered` and `registers 52 configurations in advance`; added `The full list, activation predicates, and decision rules are fixed in a version-controlled artifact released with the paper.` | Branch A. `campaigns/armindex-multiretriever-v2/evidence/a2-five-arm-candidate-freeze.receipt.v1.json` (created 2026-08-12, before measured execution) and `campaigns/armindex-multiretriever-v2/manifests/a2-five-arm-candidate-manifest.v1.json` record 52 candidates, 40 matched, 12 conditional reserves, the activation predicate, and `frozen_before_measurement`; `docs/goal/A2_PER_ARM_AUTOINDEX_goal_004.md` records measured attempt start 2026-08-16. PDF signature: `fixed in a version-controlled artifact`. | DONE |
| 8 | Per-system decision criterion was implicit. | `Under the per-system rule, a challenger replaces its incumbent only on a strict Recall@100 gain; anything smaller is recorded as a tie.` | `control/campaigns/scope-autoindex-v1.yaml` and `control/armindex/a2/a2-goal004-closeout-projection.v1.json` bind the strict-gain/reject-ties rule. PDF signatures: `replaces its` and `incumbent only on a strict Recall@100 gain`. | DONE |
| 9 | Selection-125 profiles were not reported. | `On this slice the four profiles scored Recall@100 of 0.416 (ARM-03), 0.361 (BALANCED), 0.361 (DEEP), and 0.308 (FAST).` | `outputs/publication/armindex/a5-a6-continuation-20260822/tables/a4_selection_profile_metrics.csv` is the source. PDF signature: `profiles scored Recall@100 of 0.416 ... 0.308 (FAST)`. | DONE |
| 10 | No published-landscape positioning sentence. | Added the DAPFAM/PatenTEB positioning sentence ending `what the protocol adds is not the ranking but its survival on held-out data with development closed.` | `references.bib` entries `ayaou2026dapfam` and `ayaou2025patenteb`; PDF signature: `published landscape` and `what the protocol adds is not the ranking`. | DONE |
| 11 | Transfer constructions were unnamed. | Added the PatEmbed-derived, Arctic-derived, and Qwen3-derived construction specifications with fields, segmentation, overlap, and max-p aggregation. | `docs/figures/07_a3_transfer_matrix.csv` identifies the three source systems; construction definitions are cross-checked against `docs/figures/04_document_representations.csv` and frozen per-system program artifacts. PDF signature: `Concretely, the PatEmbed-` followed by `derived construction`. | DONE |
| 12 | Related Work lacked PHAGE citation. | Added the PHAGE claim-dependency attention sentence and citation `\cite{phage2026}`. | `docs/paper/references/references.bib` verifies arXiv:2605.10073, title `Heterogeneous Dependency Graph-Guided Attention for Patent Representation Learning`, authors Yoo, Xu, Wu, and Cao. PDF signature: `PHAGE injects a claim-dependency graph`. | DONE |
| 13 | `are fixed at that close` | `are fixed when it closes` | V-A; PDF signature: `fixed when it closes`. | DONE |
| 14 | Comparator rationale was absent. | `FAST was fixed as the comparator before Final-872 because it was the pre-specified static/common operational baseline; it was not chosen after observing Final-872 outcomes.` | `control/campaigns/scope-autoindex-v1.yaml` and A4/A5 goal controls identify FAST as the static/common comparator. PDF signature: `it was not chosen af-` / `ter observing Final-872 outcomes.` | DONE |

## Verification

- Build command: `latexmk -g -pdf -interaction=nonstopmode -halt-on-error main.tex`
- Output: 6 pages; undefined references/citations: 0; overfull hboxes: 0.
- Numeric-token diff against the pre-edit `main.pdf`: 0 differences. The
  artifact-sourced values in Edits 1 and 9 reproduce their named sources; no
  existing numeric token changed.
- Source/PDF checks: no malformed `.;`, no `top-100.is fixed`, and
  `rg "TODO:"` returns zero matches in `main.tex` and extracted PDF text.
- Pages 4--6 were rendered and inspected after the rebuild; no clipping,
  overlap, or abnormal whitespace was introduced.

Remaining TODO(human) items: none.
