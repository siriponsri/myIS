# REVIEW_PROMPT.md — final verification pass for journal_08

Run this with a high-capability model (e.g. Codex CLI, `gpt-5.6-sol`,
`model_reasoning_effort = "high"`). This is a **verification and copy-edit**
pass, not a rewrite. Structure, argument, and section order are settled.

---

## Part 1 — Numeric verification (do this first, report before editing)

Every number in `main.tex` must trace to `DATA_PACK/`. Build a table with one
row per numeric claim: value → file it came from → PASS/FAIL.

Immutable values that must appear exactly as written:

| value | meaning | source |
|---|---|---|
| 905 / 5,193 | judged queries / relevant-family incidences | A_domain_exposure, PREP_REPORT_3 |
| 796 / 332 / 4,065 | found@100 / first at 101–200 / absent | same |
| 0.188 (0.188450) | observed macro Recall@100 | B_depth_curve |
| 0.260 / 0.318 / 0.410 / 0.529 | oracle Recall@100 at pool 200/300/500/1000 | I1_bound_by_pool_depth |
| 0.072 / 0.341 | gain from reordering / from depth | I1 (derived: bound − 0.188450) |
| 78.3% / 73.7% / 66.5% / 56.9% | absent share by depth | B2_depth_curve_extended |
| 455 / 400 / 313 / 219 | queries with nothing, by depth | B2 |
| 2,957 | relevant families still absent at k=1000 | derived: 5,193 − 2,236 |
| 0.331 → 0.442, 0.111, [0.102, 0.120] | Final-872 Recall@100 | conference paper, immutable |
| 619 / 158 / 95 | wins / ties / losses | C_final872_by_domain totals |
| 66%–79% | per-section win rate range | C, rolled up to IPC section |
| 0.416 / 0.361 / 0.361 / 0.308 | Selection-125 profiles | E2_selection125 |
| 0.191 / 0.270 / 0.413 / 0.341 / 0.364 | shared screen | E1_screen_5x5 |
| 0.235 / 0.290 / 0.423 / 0.359 / 0.374 | per-system search | D_search_space |
| 0.011 / 0.018 | effect bound / narrowest band separation | conference stats.json |
| 71%–93%, section table | IPC section exposure | I2_section_exposure |
| 188,944 | passage chunks | conference paper |

Specific things to check, not just match:
1. **0.072 and 0.341 must be on the same metric.** Both are Recall@100 gains
   over the observed 0.188450. Confirm the text never compares 0.072 against
   Recall@1000 directly.
2. **Table~\ref{tab:depth} claims the oracle bound coincides with Recall@$k$**
   because the 100-slot cap rarely binds. Verify against I1 vs B2 (they should
   be identical at every depth) and confirm the explanation sentence is present.
3. **Section table covers 904 queries, not 905** (one non-IPC record excluded).
   Confirm the limitations section says so.
4. Confirm no per-bin ranking claim is made from the 3-character domain table.

Report FAIL rows before changing anything. A mismatch is a stop-and-report.

---

## Part 2 — Tone pass (anti-AI-slop)

Apply the patterns from https://github.com/petergyang/no-ai-slop. In addition,
these are hard rules for this manuscript:

**Banned outright:** moreover, furthermore, additionally, notably, it is worth
noting, it is important to note, delve, leverage (as a verb), crucial, pivotal,
underscore, comprehensive, robust (unless statistical), seamless, landscape (as
metaphor), realm, testament to, "In this paper, we", "In today's ...".

**Structural slop to remove:**
- Rule-of-three lists used for rhythm rather than content.
- Sentences that only announce the next sentence ("This section presents...").
- Paragraph-opening throat-clearing before the actual claim.
- Hedge stacking ("may potentially suggest that...").
- Em-dash overuse: at most one per paragraph.

**Do not touch** (these are load-bearing or deliberate):
- "A patent retriever never sees a patent."
- "Seventy-eight percent of the evidence is not late; it is absent."
- "The ceiling moves; it does not lift."
- "The pool decides what the model and the ranker will ever see"
- Any sentence containing a number.

Register: this is a professional journal for patent-information practitioners.
Plain, direct, confident. Keep contractions out; keep the voice.

Report every edit as before/after. Cap: 30 edits. If you want more than 30, stop
and explain why.

---

## Part 3 — Figure check

Reference: https://github.com/dwzhu-pku/PaperBanana and
https://github.com/Nutlope/hallmark for figure-design conventions.

Figures 5 and 6 are new and were generated as SVG. Check, in the rendered PDF:
1. No label overlaps any axis, gridline, frame, or other label.
2. Figure 6's horizontal axis starts at 60% — confirm the caption says so.
3. Font sizes are legible at journal column width; no text under ~7pt.
4. Colour is not the only channel carrying meaning.
5. Every number printed in a figure matches DATA_PACK.

If a fix is needed, edit the SVG and regenerate the PDF; do not hand-edit PDFs.

---

## Part 4 — Submission compliance

- `elsarticle` class, `elsarticle-harv` bibliography style, builds clean.
- Zero undefined references or citations; zero overfull boxes over 5pt.
- Author block, acknowledgements, and the generative-AI declaration are filled
  or deliberately removed.
- The data-availability URL resolves.
- The relationship to the conference version is stated in the acknowledgements.

## Deliverable
`VERIFY_REPORT.md` containing: the numeric verification table with PASS/FAIL,
every tone edit as before/after, figure-check results, compliance checklist, and
a list of anything you could not verify and why. Do not silently skip an item.
