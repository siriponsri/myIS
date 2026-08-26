# Figure Review 01

## Overall verdict

REVISE

## Figure-system score

- Scientific fidelity: 10/10
- Visual hierarchy: 8.5/10
- Modern/editorial quality: 8.7/10
- Cross-figure consistency: 8.8/10
- IEEE readability: 8.4/10
- Narrative fit: 9.0/10
- Overall: 8.9/10

All canonical assertions and evidence boundaries pass. The revision request is
visual: the set is close, but it does not yet meet the 9.5/10 acceptance gate.

## Overview evidence map

Strengths:

- Clean, shallow evidence ribbon at the intended two-column width.
- The development gate is unmistakable and the four stages scan quickly.
- Development versus protected/post-confirmatory color roles are coherent.

Issues:

- The two long horizontal arrows create more visual weight than the milestones.
- Stage 01 and 02 read as a single gray/teal rail, but the protected rail reads
  as strongly blue; rebalance the two halves without weakening the gate.
- ASCII `->` in the lower labels reads as source-code notation.

Required changes:

- Reduce rail weight slightly and use a proper typographic arrow or a line-plus-
  arrowhead construction in the generated vector.
- Keep the gate and `DEVELOPMENT CLOSED` as the dominant geometry.
- Do not add large icons, badges, or boxes.

## Figure 1

Strengths:

- Exact A3 values, matched rings, nominal-best amber points, and descriptive
  evidence boundary are all correct.
- The shared absolute scale honestly shows the strong target-level separation.
- The zero-centered local view avoids exaggerating the small effects.

Issues:

- The figure remains two disconnected blocks, while the authority asks for an
  integrated target-row reading: absolute context at left and local delta at
  right for each target.
- The five-item legend dominates the top edge and costs too much vertical space.
- Source identities and highlight meanings compete in one legend instead of
  supporting direct row-wise decoding.
- The bottom scientific note is too close to the x-axis titles at final size.

Required changes:

- Rebuild as three aligned target rows. Each row must contain its absolute
  source positions at left and its matched-relative positions at right.
- Replace the large legend with compact direct labels or a single short key.
- Preserve the shared absolute scale and shared local-delta scale.
- Preserve dark matched rings, amber nominal best, exact ranges, and the
  descriptive-development boundary.
- Add vertical breathing room between axes and the note without increasing the
  figure beyond about 2.3 inches.

## Figure 2

Strengths:

- The integrated metric-row plus W/T/L structure matches the brief well.
- `+0.111379` is the first focal value and the complete-system boundary is clear.
- The W/T/L ribbon is compact and visually subordinate to the confirmation rows.

Issues:

- Panel B subtitle and exact CI labels create a dense cluster around the title
  and interval marks.
- The A/B headings are large relative to the plotted evidence at final size.
- The bottom boundary note is more prominent than needed and extends the height.

Required changes:

- Reduce title/subtitle density and move exact CI labels so they cannot compete
  with the effect callouts.
- Keep both exact effects and both exact CIs visible.
- Keep the complete-system note, but make it a quiet one-line boundary note.
- Preserve the integrated rows and exact `619 / 158 / 95` ribbon.

## Figure 3

Strengths:

- `78.3% absent` and `4,065 / 5,193` are correctly dominant.
- The observed-to-bound line is scientifically honest and the headroom is clear.
- Counts and macro Recall remain explicitly separate.

Issues:

- Panel A title and subtitle overlap (`anatomy` and `relevant-family...`).
- Panel B title and subtitle overlap materially.
- The two panels feel vertically detached because the middle whitespace is large.
- The left-to-right two-step argument is weaker than intended.

Required changes:

- Eliminate every title/subtitle collision at final size.
- Tighten the vertical sequence so Stage A naturally leads into Stage B.
- Use a small downward connector or short transition label only if it materially
  improves the two-step reading; do not introduce a decorative flowchart.
- Keep the exact counts, percentages, observed value, bound, headroom, and
  analytical-bound wording unchanged.

## Global design issues

- Panel title sizes and subtitle placement are not yet sufficiently consistent.
- The set needs one shared spacing system for title, subtitle, plot, axis title,
  and evidence-boundary note.
- Whitespace should separate evidence layers, not leave titles disconnected from
  their plots.

## Must-fix items

1. Integrate Figure 1 into three target rows and remove the oversized legend.
2. Fix all Figure 3 title/subtitle collisions.
3. Reduce Figure 2 annotation density while preserving exact A5 values and CIs.
4. Standardize title/subtitle/note spacing across Figures 1-3.
5. Preserve every existing canonical assertion and evidence boundary.

## Optional improvements

- In the overview, slightly reduce rail weight and replace ASCII arrows.
- Test a grayscale proof after the spacing fixes.
