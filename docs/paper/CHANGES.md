# CHANGES — publication-ready revision of "Beyond the Retriever"

Applied to the v2 Prism package. Numeric **values are unchanged**; only display
precision, narrative, figure labels, and float placement were touched. Six
values that need your local data are visible `[TODO: ...]` markers in main.tex.

## Float placement (the reported bug: figures landed under the references)
- Cause: four full-width `figure*` floats in a short two-column paper overflowed
  the page-top slots and were deferred to the end, below the bibliography.
- Fix: `\usepackage{dblfloatfix}` (do NOT also load stfloats — they conflict),
  tuned float fractions/counters, all four `figure*` set to `[!t]` and placed
  immediately before the paragraph that first references them.
- Verified by compile: Fig.1 top of p2, Fig.2 top of p3, Fig.3 top of p4,
  Fig.4 top of p5 --- every figure sits at a page top, above the references.

## Story arc (main.tex prose fully rewritten; structure/labels kept)
- One driving thesis: retriever identity dominates coarse field-level
  representation choice, and exposure --- not ordering --- binds recall.
- Reversal arc with hooks and hand-offs: freezing representation hides a
  variable -> we expected representation to reorder retrievers -> it does not
  (within noise) -> "It does." (held-out win) -> the real cap is exposure:
  "Seventy-eight percent of the evidence is not late; it is absent."
- Humanized: varied rhythm, active voice, no "moreover/furthermore", no filler
  topic sentences, formal IEEE register preserved.

## Scoping vs AutoIndex (critical for a strong accept)
- AutoIndex (already cited) argues the opposite and improves the same model
  (Qwen3-Embedding-0.6B) by 18.3%. Related Work now meets it directly and
  scopes our null to *coarse field-level* constructions; the thesis is scoped in
  abstract, intro, and conclusion. Our transfer matrix is reframed as an early
  probe of the transfer question AutoIndex leaves open.

## Inferential transfer (was descriptive)
- Section IV now tests within-target source differences via placeholder macros
  filled by analysis/transfer_stats.py: \wtPatCI \wtArcCI \wtQwenCI
  \maxArgmaxProb, plus \ndcgtenCI for the previously-missing nDCG@10 CI.

## Numbers -> 3 decimals (display only)
- Body text, Table II, and the confirmation/diagnosis figures. The transfer
  matrix keeps full precision on purpose --- its sub-0.004 gaps are the point.

## Figures (SVG edited, PDF regenerated via svglib; regenerate in your pipeline for final)
- fig1_a3_transfer: subtitle + footer reframed; cell values untouched.
- fig2_a5_confirmation, fig3_a7_diagnosis: labels rounded to 3 dp.
- overview_evidence_map: caption sharpened; content unchanged.
- All SVGs de-namespaced (ns0: prefix removed).

## Bibliography note
- main.tex keeps \bibliographystyle{IEEEtran} (correct for Prism/Overleaf/full
  TeXLive). IEEEtran.bst is NOT bundled (matching the original package); the
  preview PDF you were shown was built with a stand-in style for rendering only.

## TODO(human/agent) before submission  --  see AGENT_TASK.md
1. Fill the six placeholder macros (5 from transfer_stats.py + comparator).
2. Verify the "The reordering is noise" sentence against the actual CIs.
3. Confirm the DAPFAM journal cite (Array vol.29 p.100720 2026) or fall back to
   arXiv:2506.22141. Other citations verified correct.
4. Replace the anonymous author block for camera-ready.

---
# Round 2 (after stats + comparator filled)
- **Figure 1 redesigned.** Replaced the flat timeline with a three-zone evidence
  map (development=blue, confirmation=green, diagnosis=amber), a prominent dashed
  DEVELOPMENT-CLOSED barrier with a padlock, and four numbered stages, each with
  an icon, the question it answers, and a key-finding pill (5 constructions ->
  reordering is noise -> +0.111 Recall@100 -> 78% absent). It now doubles as a
  one-glance roadmap of the whole arc. Same filename (overview_evidence_map).
- **Selected-system gap flagged.** The confirmation named the comparator in full
  but not the selected system. Added `\selectedSpec` (TODO) so the winner is
  named symmetrically -- fill it before submission. This is the only [TODO] left.
- Transfer CIs, argmax prob, nDCG@10 CI, and comparator are filled and verified:
  all three within-target CIs contain zero, so "The reordering is noise" holds.
