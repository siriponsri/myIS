# AGENT_TASK.md — finish "Beyond the Retriever" for submission

You are working in `docs/paper/` of the myIS repo. The paper is publication-ready
except for six values that need local data and a final compile. Do these in order.
Full rationale is in `REVIEW_AND_EDIT_SPEC.md`; changes so far are in `CHANGES.md`.

## Rule 0 — numbers are immutable
You may fill the six `[TODO: ...]` macros and build the PDF. You may NOT change any
existing numeric value. Display precision is already set (3 dp). Before/after,
diff every numeric token in the PDF; the only allowed changes are the six macros
becoming real numbers. Any other value change is a bug.

## 1. Produce the five statistical macros
- Wire `analysis/transfer_stats.py::load_per_query()` to the saved per-query
  Recall@100 for the 9 transfer cells (250 dev queries) and per-query nDCG@10 for
  the two Final-872 systems.
- If those arrays are not saved, recompute the 9 cells from the FROZEN configs
  (no re-selection) and verify each cell mean reproduces the published Fig-2 value
  within 1e-4 (the script asserts this). If it diverges, STOP and report.
- Run the script. It prints ready-to-paste `\renewcommand` lines and writes
  `stats.json`. Paste the five lines over the placeholders in `main.tex`
  (\wtPatCI, \wtArcCI, \wtQwenCI, \maxArgmaxProb, \ndcgtenCI).

## 2. Honesty check on the transfer claim
- Section IV says "The reordering is noise." That holds only if each within-target
  CI contains zero. If any CI does NOT contain zero, rewrite that sentence to match
  the real result (e.g. name the one target that separates) — do not leave the
  stronger claim standing.

## 3. Fill the comparator
- Set `\comparatorSpec` to the exact Final-872 comparator: model checkpoint +
  representation construction + prompt (if any) + fusion (if any). Read it from the
  repo config; if it cannot be determined unambiguously, leave the TODO and flag it.

## 4. Citation + author block
- Confirm ref [1] DAPFAM journal cite (Array vol.29 p.100720 2026); if unverified,
  switch that entry to arXiv:2506.22141. Other citations are verified correct.
- Replace the anonymous author block only for the camera-ready (keep anonymous for
  double-blind review).

## 5. Build and hand back
- Compile with `latexmk -pdf main.tex` (IEEEtran.bst is present in TeXLive/Overleaf).
- Confirm: 0 undefined refs/cites, 0 overfull hboxes, four figures at page tops,
  references last, no `[TODO: ...]` left in the PDF.
- Return `main.pdf`, `stats.json`, and a one-line note of any TODO you could not
  resolve.
