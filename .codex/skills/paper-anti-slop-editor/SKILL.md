---
name: paper-anti-slop-editor
description: Run evidence-preserving editorial and numbered review loops for the ArmIndex A8 manuscript while protecting author voice, IEEE style, figures, provenance, and claim boundaries.
metadata:
  version: "0.2.0"
  policy: "editorial-quality; not-authorship-detection"
---

# Paper Anti-Slop Editor

Use this project-local skill for the A8 ArmIndex manuscript loop. Improve clarity
and natural researcher prose; do not use it as an AI detector or to make weak
claims appear stronger.

Use one editorial pass only. Do not chain several anti-slop skills, because
overlapping rewrite rules can erase author voice and alter technical meaning.
This skill incorporates the useful shared principles of stop-slop,
no-ai-slop, humanizer, unslop, slopbeth, deslop, anti-slop, and humanize while
keeping A8 evidence and IEEE constraints authoritative.

## Scope

- Edit manuscript prose, captions, reviewer responses, and revision notes.
- Preserve IEEEtran structure, double-blind anonymity, scientific values,
  equations, citations, figure labels, and aggregate-safe boundaries.
- Before material rewriting, read the active academic guardrails, Harvard story
  guide, and JCSSE rules in the parent paper workspace.

## Protected Ledger

Before editing, record names, model identifiers, dates, counts, decimals,
intervals, units, metrics, equations, citation keys, figure references, and
claim-boundary terms such as `held-out`, `receipt-bound`, `frozen pool`,
`analytical bound`, `not a reranker`, and `no external generalization`.

Compare the ledger after editing. Any changed, missing, or invented protected
item blocks the revision until repaired from canonical evidence.

For each quantitative claim, also record its denominator, aggregation rule,
and unit. Treat macro averages, micro totals, query counts, family incidences,
and percentages as different quantities unless canonical evidence explicitly
defines a valid conversion. Never describe one as a component, remainder, or
explanation of another merely because their magnitudes appear compatible.

## Editorial Pass

Revise only when useful:

- filler openings, generic significance claims, sales language, repeated
  conclusions, and vague source phrases;
- forced contrasts, artificial fragments, forced three-part lists, uniform
  sentence cadence, and ornamental transitions;
- passive voice that hides the actor, while retaining it when the method or
  measured object is the natural subject;
- em-dash overuse, inflated adjectives, fake quotable endings, and headings
  that repeat nearby prose;
- `robust`, `novel`, `seamless`, `groundbreaking`, and similar terms when the
  cited evidence does not operationalize them.

Do not flatten domain terminology or legitimate cautious voice. Never optimize
for an AI-detector score.

### A8 pattern audit

For the complete manuscript, record quoted examples for any real occurrence of:

- filler or generic significance openings;
- sales language, unsupported superlatives, or inflated novelty;
- repeated transition or conclusion templates;
- forced `not X but Y` contrasts, automatic rule-of-three lists, fragments,
  or near-identical sentence lengths;
- vague verbs, ornamental hedging, fake quotable endings, or agreement with an
  objection nobody raised;
- generic terms (`delve`, `leverage`, `seamless`, `robust`, `groundbreaking`)
  without an operational definition;
- passive voice that hides a consequential actor;
- redundant headings/callouts;
- missing names, numbers, dates, citations, or source pointers.

Classify each signal as `KEEP` (intentional and useful), `REVISE` (clarity
benefit), or `ASK` (required evidence is missing). A pattern count is only a
diagnostic. It must never be presented as an authorship or AI probability.

For Thai or mixed-language passages, use the structural checks above but do not
apply the English vocabulary list mechanically. State the language and scope
of the scan in the review.

If a needed name, number, date, source, citation, or figure fact is absent, ask
for it or leave `TODO: source required`; never infer it.

## A8 Numbered Review Loop

1. Reviewers receive paths and a compact role contract, not manuscript text.
   This avoids API context-window failures.
2. Preserve all prior `paper_NN` directories and review files. Create the next
   numbered paper only after both reviews of the preceding version exist.
3. Keep IEEE review at `reviews/reviewer_paper_NN.md` and figure-only review at
   `reviews/figure_review_NN.md`. Both must inspect the same numbered version.
4. After a figure edit, regenerate the vector export, compile the manuscript,
   render the affected page, and verify artifact timestamps before review.
5. Inspect figures standalone and in the compiled page. Check canvas edges,
   final-size legibility, placement, caption attachment, and whitespace.
6. Continue until both reviewers explicitly record `STRONG ACCEPT` with zero
   CRITICAL and zero MAJOR findings. One `ACCEPT` is not terminal.
7. Do not invent cosmetic changes solely to obtain a stronger verdict. An
   honest scope limitation remains visible and is judged against bounded claims.
8. Before each review, audit every cross-metric comparison. Additive language
   such as `decomposes`, `accounts for`, `dominates`, `remaining`, or `residual`
   requires the same denominator, aggregation rule, and unit on both sides.
   Otherwise separate the quantities and state the relationship descriptively.
9. After any rewrite, run an over-correction check against the prior version:
   protected terms and facts must match, the claim strength must not increase,
   and the cadence/terminology should remain recognizably A8 rather than
   generic editorial prose.

## Output

Return the edited artifact path, pattern audit, protected-ledger result,
render/build status, reviewer verdicts, and unresolved evidence or policy risks.
Success means `clearer and evidence-preserving`, never `proven human-written`.
