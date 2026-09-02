# Journal_08 Verification Report

## Part 1: pre-edit numeric verification

This table records the pre-edit checkpoint. The manuscript was not changed before
this report was created. Values are checked against the journal DATA_PACK and its
manifest; external literature values are identified separately.

| Value or claim | Source file | Status |
|---|---|---|
| 905 queries; 5,193 relevant-family incidences | `DATA_PACK/A_domain_exposure.csv`; `DATA_PACK/PREP_REPORT_3.md` | PASS |
| 796 found by 100; 332 first at 101--200; 4,065 absent | `DATA_PACK/B2_depth_curve_extended.csv`; `docs/figures/17_a7_exposure_anatomy.csv` | PASS |
| 0.188 (0.188450) observed macro Recall@100 | `DATA_PACK/B_depth_curve.csv` | PASS |
| 0.260 / 0.318 / 0.410 / 0.529 oracle Recall@100 | `DATA_PACK/I1_bound_by_pool_depth.csv` | PASS |
| 0.072 and 0.341 gains over 0.188450, both Recall@100 | `DATA_PACK/I1_bound_by_pool_depth.csv` (derived) | PASS |
| 78.3% / 73.7% / 66.5% / 56.9% absent share | `DATA_PACK/B2_depth_curve_extended.csv` | PASS |
| 455 / 400 / 313 / 219 queries with no relevant result | `DATA_PACK/B2_depth_curve_extended.csv` | PASS |
| 2,957 absent at depth 1,000 | `DATA_PACK/B2_depth_curve_extended.csv` (5,193 - 2,236) | PASS |
| Final-872: 0.331 -> 0.442, difference 0.111, CI [0.102, 0.120] | conference confirmation artifact; `DATA_PACK/C_final872_by_domain.csv` | PASS |
| 619 / 158 / 95 wins / ties / losses | `DATA_PACK/C_final872_by_domain.csv` totals | PASS |
| 66%--79% per-section win range | `DATA_PACK/C_final872_by_domain.csv` roll-up | PASS |
| 0.416 / 0.361 / 0.361 / 0.308 Selection-125 profiles | `DATA_PACK/E2_selection125.csv` | PASS |
| 0.191 / 0.270 / 0.413 / 0.341 / 0.364 shared screen | `DATA_PACK/E1_screen_5x5.csv` | PASS |
| 0.235 / 0.290 / 0.423 / 0.359 / 0.374 per-system search | `DATA_PACK/D_search_space.csv`; `docs/figures/06_a2_per_system_search.csv` | PASS |
| 0.011 effect bound; 0.018 narrowest band separation | `docs/paper/stats.json`; `docs/figures/07_a3_transfer_matrix.csv` | PASS |
| 0.419 / 0.418 / 0.415 fusion values | `docs/figures/08_a3_fusion_controls.csv` | PASS |
| 71%--93% IPC-section exposure range and section rows | `DATA_PACK/I2_section_exposure.csv` | PASS |
| 188,944 passage chunks | conference full-benchmark artifact | PASS |
| 22 models in related work | `references/references.bib`, `yousefiramandi2026patent` | PASS (external literature) |
| 18.3% AutoIndex result | `references/references.bib`, `onuallain2026autoindex` | PASS (external literature) |
| 0.68 best-source probability wording | `docs/paper/stats.json` reports 0.6834 | **FAIL: wording is too low; correct text rather than the measurement** |

The I1 and B2 curves are identical at every shared depth (100, 150, 200, 300,
500, and 1,000) because the 100-slot cap almost never binds for the median query;
the oracle bound therefore coincides with Recall@k at the same depth. The section
roll-up covers 904 queries because one non-IPC record is excluded from the A--H
table; the strict cross-domain population remains 905 queries. No ranking claim is
made from the three-character bins.

The transfer and fusion source files are outside the current manifest header and
must be added before the final provenance check. No scientific value may be
changed to resolve this provenance gap.

## Part 2: tone audit

The prior capped editorial pass is retained. Numeric sentences and the protected
sentences in `REVIEW_PROMPT.md` remained locked. One additional non-numeric edit
was required in the final audit:

| # | Before | After | Reason |
|---|---|---|---|
| 1 | ``The direction is consistent with the published landscape.'' | ``The direction is consistent with the published evidence.'' | Remove the banned metaphorical use of ``landscape`` while preserving the claim. |

Total additional tone edits: **1 of 30**. A final banned-term scan found no
remaining matches. No numeric sentence or protected sentence was edited.

## Part 3: figure audit

Figures 5 and 6 were checked in the final rendered PDF (`main.pdf`, pages 12--13)
at 160 dpi. Both pass: labels are separated from axes, gridlines, frames, and
other labels; there is no clipping; text remains legible; the plots use position,
lines, and markers in addition to colour; and all printed values match the
corresponding DATA_PACK rows. Figure 6 starts at 60%, matching its caption. No
SVG change or PDF-level edit was needed.

## Part 4: compliance

| Check | Result | Evidence |
|---|---|---|
| Elsevier class and bibliography style | PASS | `elsarticle`, `elsarticle-harv`; local MiKTeX build |
| Undefined references/citations | PASS | final LaTeX log has no undefined citation/reference warnings |
| Overfull boxes >5pt | PASS | final LaTeX log has no `Overfull \\hbox` entries (underfull boxes only) |
| Author block and ORCID | PASS | `docs/journal/authors.md`; both authors in `main.tex` |
| Competing interest, CRediT, funding, acknowledgements, GenAI | PASS | completed sections in `main.tex` |
| Conference-version relationship | PASS | acknowledgements section |
| CFP routing | PASS (contextual) | regular-article route retained; secondary listing deadline 31 Dec 2026, official page HTTP 403 |
| Overleaf build | PENDING OWNER ACTION | no authenticated Overleaf session is available; upload/compile steps are in README |

Local output: `main.pdf`, 18 pages, built 30 August 2026 with MiKTeX
`elsarticle` 3.5. The only unverified item is the online Overleaf compile, which
requires the owner's authenticated account; the source package is otherwise
ready for upload.
