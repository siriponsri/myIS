# Round 4 — fixes applied after the VERIFY_REPORT

Numbers unchanged. Five defects fixed; one framing addition for the special issue.

## Defects
1. **`\paragraph{... .}` produced a doubled period** ("in practice..") in two
   places. `elsarticle` supplies its own terminal period. Removed from both.
2. **Broken cross-reference.** `Section~\ref{sec:data}` pointed at a starred
   section, so LaTeX resolved it to the last numbered section and it rendered as
   "Section 9", i.e. the Conclusion. Replaced with plain prose.
3. **Figures 5 and 6 were illegible.** Measured from the built PDF, `\textwidth`
   is 359 pt; both figures used a 1040-unit canvas, so a 10 px label rendered at
   **3.4 pt**. Both were rebuilt on a 480-unit single-column canvas with larger
   type: labels now render at about **8.8 pt**. The VERIFY_REPORT recorded this
   check as a pass; it was not one.
4. **Figure 5 baseline label** overlapped the axis rule; moved above the dashed
   line.
5. **Provenance gap** noted in the VERIFY_REPORT: `stats.json`,
   `07_a3_transfer_matrix.csv`, and `08_a3_fusion_controls.csv` are now named in
   `DATA_PACK/G_manifest.md`.

## Addition
6. **Special-issue framing.** One clause in the introduction and a new
   Section 7.3, "What this means for LLM-based and agentic search", connecting
   the exposure result to retrieval-augmented and agentic pipelines. New derived
   figures: exposure is 21.7 % at depth 200 and 43.1 % at depth 1,000
   (complements of 78.3 % and 56.9 %). Both trace to
   `B2_depth_curve_extended.csv`.

## Still outstanding — figures 1 to 4
The four figures carried over from the conference version have the same
legibility problem as 5 and 6 did: they were drawn for a 1031-unit canvas
intended for a two-column layout 516 pt wide, and at 359 pt their labels render
near 3.4 pt. They need redrawing on a canvas about 480 units wide, in the same
way figures 5 and 6 were. This is layout work only; no value in any of them
changes. Do this before submission.
