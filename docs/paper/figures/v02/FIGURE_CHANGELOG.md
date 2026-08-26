# Figure Changelog: v02

Revision implementing `figure_review_01.md` while preserving the frozen
scientific values and the complete v01 artifact set.

- Fig. 1 is now three aligned target rows: common-scale absolute source
  positions lead directly to the matched-relative view in the same row. The
  large legend was replaced with one compact textual key.
- Fig. 2 preserves the exact A5 effects, CIs, and W/T/L counts while reducing
  heading/subtitle density and making the complete-system boundary quieter.
- Fig. 3 separates all title/subtitle lines and adds a minimal transition from
  exposure to the fixed-pool analytical ordering bound.
- The overview rail is thinner and balanced across the development and
  protected stages. Source-code-style arrows in station labels were removed.

`source/generate_v02.py` reads the canonical publication CSV ZIP and asserts
the audited A3, A5, and A7 values before every render. Outputs are PDF, SVG,
and 360-dpi PNG proof renders. Neither the manuscript nor v01 is modified.

## Production check

- Canonical assertions, Python compilation, and deterministic regeneration passed.
- SVG dimensions: overview 7.16 x 1.13 in; Fig. 1 7.16 x 2.30 in; Fig. 2 7.16 x 2.25 in; Fig. 3 7.16 x 2.10 in.
- `main.tex` was verified unchanged after generation.
