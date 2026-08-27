# Prism edit notes (v3 — publication-ready starter)

- main.tex narrative is revised and float placement is fixed (see CHANGES.md).
- Numeric values unchanged; six [TODO: ...] placeholders await local data.
- Preamble uses dblfloatfix for figure ordering. Do not add stfloats (conflict).
- PDF figures were regenerated from the edited SVGs (svglib). If Prism converts
  SVG->PDF automatically, prefer the SVG; otherwise the bundled PDFs are current.
- analysis/transfer_stats.py produces the five statistical macros + stats.json.
- IEEEtran.bst is provided by Prism/Overleaf/full TeXLive; not bundled.

Figure mapping:
- Fig. 1: overview_evidence_map   Fig. 2: fig1_a3_transfer
- Fig. 3: fig2_a5_confirmation     Fig. 4: fig3_a7_diagnosis
