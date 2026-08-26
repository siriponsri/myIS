# Final Figure Gate

## Accepted champion set

The accepted artwork is `docs/paper/figures/v02/`:

- `overview_evidence_map.pdf`
- `fig1_a3_transfer.pdf`
- `fig2_a5_confirmation.pdf`
- `fig3_a7_diagnosis.pdf`

The corresponding SVG files are editable vector sources and the PNG files are
360-dpi review proofs. `figure_review/figure_review_02.md` records the
`FIGURE SET ACCEPTED` decision with an overall score of 9.7/10.

## Scientific and numerical QA

- The v02 generator reran successfully after exact canonical CSV assertions.
- A3 uses the audited 3 x 3 Recall@100 matrix and remains descriptive
  development evidence.
- A5 preserves `0.331097` versus `0.442476`, difference `0.111379`, CI
  `[0.102294, 0.120438]`; `0.279253` versus `0.365595`, difference `0.086342`,
  CI `[0.078673, 0.094077]`; and `619 / 158 / 95` Recall outcomes.
- A5 is explicitly framed as a complete-system held-out comparison.
- A7 preserves `796`, `332`, `4,065 / 5,193`, `905`, `0.188450`, `0.260167`,
  and `0.071717`.
- A7 is explicitly framed as a post-confirmatory analytical bound inside the
  immutable Top-200 pool, not reranker performance.
- Captions agree with the accepted visual encodings and evidence boundaries.

## Manuscript integration QA

- `main.tex` includes only the accepted v02 vector PDFs.
- The overview is cited from the Introduction.
- Figures 2-4 are cited before or near their first substantive discussion.
- Tables I and II are explicitly cited in the body.
- Only connective prose, captions, cross-references, and float placement were
  changed; the scientific story, Abstract logic, tone, claims, and numbers were
  preserved.
- The overview appears on page 2, A3 on page 3, A5 on page 4, and A7 on page 5.

## PDF and production QA

- `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` passes.
- Final PDF: 5 pages, A4 IEEE conference layout.
- All references resolve; the log contains no undefined-reference, multiply
  defined label, overfull-box, or LaTeX warning.
- All manuscript and figure fonts reported by `pdffonts` are embedded.
- Color and grayscale page renders were inspected at 144 dpi; labels, shapes,
  intervals, partitions, and evidence boundaries remain readable.
- No clipping, overlap, orphan heading, giant empty region, margin violation, or
  double-anonymous violation is visible.
- The final `SHA256SUMS.txt` entries all verify.
- `git diff --check` passes.

FINAL FIGURE GATE: PASS
