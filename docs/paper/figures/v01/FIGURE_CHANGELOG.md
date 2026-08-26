# Figure Changelog: v01

Initial implementation of `FIGURE_ART_DIRECTION_V3.md`.

- All numerical figure inputs are read directly from the canonical publication CSV ZIP.
- The generator asserts the frozen A3 transfer matrix, A5 confirmation effects and W/T/L counts, and A7 incidence/bound values before drawing.
- `overview_evidence_map` uses a shallow evidence path with a development-closure gate.
- `fig1_a3_transfer` uses an integrated three-row absolute-context and matched-source-delta layout.
- `fig2_a5_confirmation` uses two complete-system metric rows followed by the Recall W/T/L support ribbon.
- `fig3_a7_diagnosis` sequences candidate exposure before the fixed-pool analytical ordering bound.

Outputs are PDF, SVG, and 360-dpi PNG proof renders. The v01 generator does not modify the manuscript, canonical evidence, or previous figure versions.

## Production check

- Generator completed after canonical assertions passed.
- SVG dimensions: overview 7.16 x 1.13 in; Fig. 1 7.16 x 2.26 in; Fig. 2 7.16 x 2.27 in; Fig. 3 7.16 x 2.28 in.
- `main.tex` was verified unchanged after generation.
