# FINAL_REVISION_TASK.md — last revision pass before iSAI-NLP submission

> **RE-RUN NOTICE (round 2).** Round 1 executed exactly 1 of 13 edits (EDIT 13)
> and reported nothing. Verified by source grep: EDITs 1–12 are absent from
> main.tex. This file is unchanged and still binding. This round, every edit
> ends in one of two states — DONE with proof, or BLOCKED with a stated reason.
> Silent skips are the failure mode being corrected; a partial run without
> BLOCKED entries is itself a failed run.

Goal: move Reviewer #2's assessment (5/10 Weak Reject — see `review_01.md`) to
strong accept while keeping the paper's voice and readability. The calibration
is deliberate: **net new statistics = ONE sentence.** Everything else is
wording, scoping, and transparency. Do not "improve" beyond this file.

Files: `docs/paper/main.tex` (current build is clean, 5 pages). Page limit: 6.

---

## RULE 0 — numeric integrity (unchanged from previous rounds)
- Existing numbers are immutable. Every NEW number must come from a named
  artifact (`stats.json`, selection outputs, run configs) — never typed from
  memory, never estimated. Record the source of each new number in the report.
- After the build, diff all numeric tokens vs the current PDF. Allowed
  differences: only the new values introduced by the edits below.

## RULE 1 — style contract
- Apply ONLY the edits listed here, plus at most 5 discretionary micro-fixes
  (typo-level), all reported before/after.
- PROTECTED (do not touch, except where an edit below explicitly modifies the
  surrounding text): "A patent retriever never sees a patent." / "Freezing a
  variable does not neutralize it. It only hides it." / "We expected the answer
  to reorder the field. It does not." / "The reordering is noise" (now extended
  by EDIT 1 — keep the extension exactly as given) / "Change the construction
  and you shuffle positions within a band; change the retriever and you move
  between bands." / "It does." / "Seventy-eight percent of the evidence is not
  late; it is absent." / "Everything above it was never retrieved." /
  "Three results, one lesson:" / "Representation specifies the evidence; the
  retriever decides what to do with it."
- BANNED in any new text: Moreover / Furthermore / Additionally / Notably /
  It is worth noting / delve / leverage / crucial / pivotal / underscore /
  comprehensive / "In this paper, we".
- New sentences must match the paper's voice: active, concrete, varied rhythm.

## RULE 2 — explicitly DO NOT
No TOST or equivalence tests. No MDE/power sentence. No variance decomposition
or mixed models. No exposure curves at depth 500/1000 (no re-retrieval of any
kind). No cross-paper number-comparison tables. No global tone reduction. No
figure/SVG changes (caption text in main.tex is allowed only where an edit says
so). These were considered and rejected on purpose; adding them is a defect.

---

# THE EDITS (in priority order)

## EDIT 1 — the one statistics sentence (Reviewer #2 M1; replaces the old MDE plan)
Section IV. Replace exactly:
> The reordering is noise.
with:
> The reordering is noise---and bounded: the largest effect consistent with any
> of these intervals is 0.011 Recall@100, below the narrowest separation
> between the retriever bands (0.018).
Verification duty: 0.011 = the widest CI edge in `stats.json`
(Arctic upper 0.01145 -> 0.011); 0.018 = Arctic band max 0.341341 vs Qwen3 band
min 0.359497 -> 0.0182 -> 0.018. Confirm both derivations before committing; if
either does not reproduce, STOP and report.

## EDIT 2 — abstract, kill "wasted" (M5)
Replace:
> and that effort spent tuning the ranker is wasted while most of the evidence
> is missing from the pool.
with:
> and that no amount of ranker tuning can recover evidence the pool never
> contained.

## EDIT 3 — abstract, scope the thesis line (M5)
Replace:
> Cross-domain patent retrieval is exposure-bound, not ordering-bound.
with:
> On this benchmark, cross-domain patent retrieval is exposure-bound, not
> ordering-bound.
Also, in the abstract's bound parenthetical, replace
"(within-target Recall@100 spread below 0.004)" with
"(within-target Recall@100 spread below 0.004; every 95\% interval caps the
effect below 0.011)".
Also fix the unit: "78\% of relevant families never enter" ->
"78\% of relevant-family incidences never enter".

## EDIT 4 — one limitation sentence (M5, depth)
Boundaries paragraph in Discussion, after "The full-scale diagnosis examines
one selected dense configuration." insert:
> The exposure diagnosis is specific to the Top-200 pool; deeper cutoffs are
> uncharacterized.

## EDIT 5 — operational definition of "construction" (M2, path A)
Section III, insert at the start of the "Representations and evidence
separation" paragraph (right after the bold lead-in):
> By construction we mean the full deterministic mapping from a patent family
> to its retrievable units---field selection, segmentation, family-level
> aggregation, and any deterministic view fusion---not text content alone.

## EDIT 6 — population bridge (M4)
Section III, after "Table I lists the protected sequence." insert:
> The populations nest simply: the 1,247 query families split into 250 for
> development, 125 for selection, and 872 for protected confirmation. The
> strict cross-domain slice used later for diagnosis is a different cut---
> {{STRICT_OUT_DEFINITION: pull the exact one-clause definition from the repo,
> e.g. "queries with at least one judged relevant family outside the query's
> technological domain"}}---leaving 905 judged queries drawn from all 1,247.
> The Final-872 and strict-slice scores are computed on different populations
> and are not directly comparable.
Fill the definition from the repo. If ambiguous -> leave `TODO(human)`.

## EDIT 7 — preregistration terminology (Reviewer #2 sec.6)
Decide by evidence in the repo:
- **Branch A** (a version-controlled artifact of the 52-config space + decision
  rules demonstrably created before execution exists): keep
  "preregistered"/"registers ... in advance" and add, after "which is the point
  of registering it.":
  > The full list, activation predicates, and decision rules are fixed in a
  > version-controlled artifact released with the paper.
  Add an anonymized link footnote if one exists; else `TODO(human): create
  anonymous.4open.science link`.
- **Branch B** (no such artifact): globally replace "preregistered" ->
  "pre-specified"; "registers 52 configurations in advance" -> "pre-specifies 52
  configurations"; "the point of registering it" -> "the point of specifying it
  in advance". Abstract included.
Record which branch you took and why in the report.

## EDIT 8 — decision rules in one sentence (Reviewer #2 W2)
Section IV, before "Because the common screen and the per-system search use
different decision rules...", insert one sentence stating the REAL per-system
rule from the repo, in this shape:
> Under the per-system rule, a challenger replaces its incumbent only on
> {{RULE: the actual criterion, e.g. "a strict Recall@100 gain"}}; anything
> smaller is recorded as a tie.
Adapt wording to the actual rule. Never invent a threshold. If the rule cannot
be located -> `TODO(human)`.

## EDIT 9 — Selection-125 transparency (Reviewer #2 M3)
Section V-A, after "...use 90 queries with positive cross-domain relations."
insert:
> On this slice the four profiles scored {{S125_SCORES: the four cross-domain
> Recall@100 values from the selection outputs, ARM-03 identified}}.
State the values plainly and stop — no editorializing about margins unless the
numbers make it obvious. Source: selection outputs only. If absent ->
`TODO(human)`.

## EDIT 10 — landscape positioning, prose not table (M3 reduced)
Section V-A, append to the paragraph ending "...not representation alone.":
> The direction is consistent with the published landscape---DAPFAM's own sweep
> finds passage retrieval ahead of document retrieval, and PatenTEB reports
> patembed-large as the strongest patent-specific encoder on this
> benchmark~\cite{ayaou2026dapfam,ayaou2025patenteb}; what the protocol adds is
> not the ranking but its survival on held-out data with development closed.

## EDIT 11 — name the three transferred constructions (Reviewer #2 sec.7)
Section IV, append to the paragraph ending "...every cell over all 250
development queries.":
> Concretely, the PatEmbed-derived construction is {{SRC_PAT}}, the
> Arctic-derived is {{SRC_ARC}}, and the Qwen3-derived is {{SRC_QWEN}}.
Fill each with a short spec (fields + segmentation + aggregation, one clause
each) from the per-system search winner configs. Optionally mirror the three
names in the Fig. 2 caption. If configs ambiguous -> `TODO(human)`.

## EDIT 12 — cite PHAGE (verified real: arXiv:2605.10073)
Related Work, end of the first paragraph, add:
> Learned structural encoders are also advancing on this benchmark: PHAGE
> injects a claim-dependency graph into a pre-trained encoder's
> attention~\cite{phage2026}; we sit at the opposite end of that
> spectrum---deterministic, coarse, and frozen---asking whether construction
> choices are portable at all, not how to learn better ones.
Bib entry: fetch the EXACT title and author list from the arXiv abs page for
2605.10073 (the real title appears to be "Heterogeneous Dependency
Graph-Guided Attention for Patent Representation Learning"; the model is
PHAGE). Do NOT copy the title from review_01.md — it is wrong there. If the
page cannot be verified -> skip the citation entirely and report.

## EDIT 13 — micro-fix  [ALREADY DONE in round 1 — verify only]
V-A: "are fixed at that close" -> "are fixed when it closes".

## EDIT 14 — comparator rationale (review_02 item 6, new this round)
Section V-A, append to the sentence introducing the comparator (after the
Table III reference) one sentence in this shape:
> FAST was fixed as the comparator before Final-872 because it was
> {{COMPARATOR_RATIONALE: the real reason from the protocol/config — e.g. "the
> pre-specified hybrid lexical+dense baseline" or "the strongest eligible
> Selection-125 profile outside the research arm"}}; it was not chosen after
> observing Final-872 outcomes.
Fill from the protocol only. State the true reason even if mundane. If the
rationale is not recorded anywhere -> `TODO(human)` and say so in the report.

---

# BUILD & VERIFY — per-edit proof table (mandatory)
1. `latexmk -pdf main.tex`: 0 undefined refs/cites, 0 overfull hboxes. Pages
   <= 6. No figure after the references.
2. Run `pdftotext main.pdf out.txt`, then produce a table in EDIT_REPORT.md
   with one row per EDIT 1–14. Each row = `DONE` plus the matched signature
   line from out.txt, or `BLOCKED` plus exactly what is missing. Signatures:
   - E1: "and bounded" (with 0.011 and 0.018 present)
   - E2: "never contained"
   - E3: "On this benchmark, cross-domain" AND "caps the effect below 0.011"
         AND "relevant-family incidences never enter"
   - E4: "deeper cutoffs are uncharacterized"
   - E5: "By construction we mean"
   - E6: "populations nest"
   - E7: Branch A -> "version-controlled artifact"; Branch B -> grep
         "preregistered" returns zero matches in out.txt
   - E8: "replaces its incumbent"
   - E9: "profiles scored" with four numeric values
   - E10: "published landscape"
   - E11: "Concretely, the PatEmbed-derived"
   - E12: "PHAGE" in body plus the new reference entry (or a documented skip
          with the verification failure)
   - E13: "fixed when it closes"
   - E14: "was not chosen after observing"
3. A row may be BLOCKED only for a stated, checkable reason (artifact absent,
   config ambiguous). "Skipped" is not a state.
4. Numeric diff vs the current PDF: only the new artifact-sourced values from
   EDITs 1, 6, 8, 9, 11, 14.
5. Read the abstract and Section IV aloud once: if any new sentence sounds like
   a form letter, rewrite it within RULE 1 before delivering.

# DELIVERABLES
`main.pdf`, updated `main.tex`, and `EDIT_REPORT.md` containing: the per-edit
proof table above, per-edit before/after, the EDIT 7 branch decision with
evidence, the source artifact for every new number, remaining TODO(human)
items, and the numeric-diff summary.
