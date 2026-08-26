# FIGURE_AGENT_LOOP_V1

## Purpose

This document defines the local Codex figure-production loop for the iSAI-NLP 2026 paper.

The manuscript has already passed numerical/evidence audit. The scientific story and tone are frozen.

Primary design authority:
- `docs/paper/FIGURE_ART_DIRECTION_V3.md`

Scientific authority:
- canonical evidence / receipts / CSVs already present in the repository
- audited manuscript baseline in `docs/paper/main.tex`

---

## Agent roles

### MAIN — Reviewer / Orchestrator
Model: **GPT-5.6 Sol High**

Responsibilities:
1. Read the manuscript, canonical evidence, figure inputs, and `FIGURE_ART_DIRECTION_V3.md`.
2. Do **not** produce or directly redesign figures during the iteration loop.
3. Audit every generated figure for:
   - numerical fidelity
   - evidence-to-visual alignment
   - scientific honesty
   - visual hierarchy
   - modern/minimal editorial quality
   - consistency across the figure family
   - IEEE final-size readability
4. Write structured reviews to:
   - `docs/paper/figures/figure_review/figure_review_01.md`
   - `figure_review_02.md`
   - ...
5. Decide whether each iteration passes or requires another revision.
6. After the figure set is accepted, integrate the selected figures into `main.tex`, update captions/cross-references, compile, and perform final layout QA.

MAIN must not change the scientific story, tone, numerical claims, evidence hierarchy, or experimental interpretation.

### SUBAGENT — Figure Implementer
Model: **Terra High**

Preferred role name:
- `figure-implementer`

The implementer may reuse an existing compatible agent definition, or MAIN may create a new one.

Responsibilities:
1. Read `FIGURE_ART_DIRECTION_V3.md`.
2. Read canonical CSV/evidence for the requested figure.
3. Generate the overview evidence map + Fig.1 + Fig.2 + Fig.3.
4. Use any suitable reproducible tool, including:
   - Python + Matplotlib
   - svgwrite / CairoSVG
   - Altair for prototyping
   - Inkscape/Figma-compatible SVG output
   - other code-based vector tooling when justified
5. Do not change canonical data.
6. Export every candidate as:
   - PDF
   - SVG
   - PNG proof
7. After each MAIN review, read the latest `figure_review_NN.md` and create the next version without overwriting the previous version.

---

## Versioning

Use versioned folders:

```text
docs/paper/figures/
  v01/
  v02/
  v03/
  ...
  figure_review/
```

Each version should contain:

```text
overview_evidence_map.pdf/.svg/.png
fig1_a3_transfer.pdf/.svg/.png
fig2_a5_confirmation.pdf/.svg/.png
fig3_a7_diagnosis.pdf/.svg/.png
source/
FIGURE_CHANGELOG.md
```

Never overwrite an earlier version.

---

## Iteration loop

### Step 1 — Initial generation
Terra High creates `v01/` according to `FIGURE_ART_DIRECTION_V3.md`.

### Step 2 — MAIN review
Sol High reviews the rendered artifacts at realistic IEEE print size.

MAIN writes:

`docs/paper/figures/figure_review/figure_review_01.md`

Use this structure:

```text
# Figure Review 01

## Overall verdict
PASS / REVISE

## Figure-system score
Scientific fidelity: x/10
Visual hierarchy: x/10
Modern/editorial quality: x/10
Cross-figure consistency: x/10
IEEE readability: x/10
Narrative fit: x/10

## Overview evidence map
Strengths:
Issues:
Required changes:

## Figure 1
Strengths:
Issues:
Required changes:

## Figure 2
Strengths:
Issues:
Required changes:

## Figure 3
Strengths:
Issues:
Required changes:

## Global design issues
...

## Must-fix items
1.
2.
3.

## Optional improvements
...
```

### Step 3 — Revision
Terra reads only the latest review plus the art-direction authority and creates `v02/`.

### Step 4 — Repeat
MAIN writes `figure_review_02.md`, Terra creates `v03/`, etc.

---

## Stop criteria

Stop the review/implementation loop when ALL are true:

1. No numerical/evidence mismatch.
2. No misleading visual encoding.
3. Every required figure is readable at final IEEE size.
4. The four visuals clearly belong to one visual family.
5. No major dashboard/slide/AI-infographic aesthetic remains.
6. The overview figure clearly separates:
   - development
   - development closed
   - protected confirmation
   - post-confirmatory diagnosis
7. MAIN scores the complete figure system **>= 9.5/10** overall.
8. No individual figure scores below **9/10**.
9. MAIN verdict = **FIGURE SET ACCEPTED**.

Recommended maximum: 5 figure iterations.
If the fifth version still fails, MAIN must identify the unresolved root cause instead of continuing cosmetic looping.

---

## Final integration phase

Only after `FIGURE SET ACCEPTED`:

### MAIN may edit `main.tex`

Allowed:
- replace old figures with accepted champion files
- update figure captions so they match the actual encoding
- add/adjust `\label`, `\ref`, and figure/table citations
- add short connective sentences pointing readers to:
  - overview evidence map
  - Fig.1
  - Fig.2
  - Fig.3
  - Table I
  - Table II
- move floats to improve narrative order and page composition
- make very small local prose edits needed for figure/table integration

Not allowed:
- rewrite the story
- change tone
- change Abstract contribution logic
- change A3/A5/A7 evidence hierarchy
- add new experiment
- invent new interpretation
- change numerical claims except to correct a proven factual error
- pad the manuscript merely to fill six pages

### Desired narrative sequence

```text
Overview evidence map
→ Study Design
→ A1/A2 + tables
→ A3 + Fig.1
→ Selection / Final-872 + Fig.2
→ Full benchmark / A7 + Fig.3
→ Discussion / Conclusion
```

The overview figure is included only if it improves orientation and the paper remains <= 6 pages without shrinking core figures below readable size.

---

## Final QA gate

MAIN must compile the final PDF and visually inspect every page.

Check:

- <= 6 pages
- correct IEEE template/margins
- numerical audit remains valid
- all figures use accepted assets
- captions match graphics
- every figure/table is cited before or near first appearance
- no orphan headings
- no overlap/clipping
- no giant empty areas
- figures readable at 100% PDF view
- flow is visually coherent
- references resolve
- double-anonymous constraints preserved

Write final report:

`docs/paper/figures/FINAL_FIGURE_GATE.md`

End with exactly one of:

- `FINAL FIGURE GATE: PASS`
- `FINAL FIGURE GATE: FAIL`

If PASS, do not continue aesthetic iteration.
