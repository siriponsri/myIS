# Figure design note

## What changed and why
An earlier round produced figures with headline text, coloured panel headers,
dark blocks and oversized hero numerals. Those read as presentation slides, not
as journal artwork. Elsevier's artwork instructions state that no data should
sit outside the illustration area, and journal convention puts the title and
the explanation in the caption rather than inside the figure. Tufte's data-ink
argument, restated in PLOS "Ten Simple Rules for Better Figures", treats
background fills, boxes and decorative rules as chartjunk.

All six figures were redrawn against those rules.

## Rules applied
- No title, kicker or explanatory sentence inside any figure. The captions in
  `main.tex` carry all of it.
- No background fills, rounded cards, drop shadows or decorative rules.
- Panel labels are plain (a), (b), (c) in bold, top left.
- Helvetica only, at 8.2 to 10.5 canvas units.
- Two inks plus grey: blue #2166AC, orange #D6733A, grey #8C8C8C. Encoding is
  positional first, so the figures survive greyscale printing. Open and filled
  markers separate comparator from selected without relying on hue.
- Axis rules are 0.9 units; gridlines were removed except the dotted leader
  lines in Figure 6, which carry the eye across a long label gap.

## Sizing
Canvas is 460 units for every figure, so the set is visually consistent.

| placement | width | rendered label size |
|---|---|---|
| two-column journal page | 190 mm | 9.6–12.3 pt |
| 1.5-column journal page | 140 mm | 7.1–9.1 pt |
| single-column manuscript for review | 359 pt | 6.4–8.2 pt |

The manuscript figure is the smallest case and stays at or above 6.4 pt, which
clears the 5–7 pt floor that Nature and Elsevier production both work to.

## Chart-type changes
- Figure 2 gained a strip plot above the numeric matrix. The three retriever
  bands separate on sight, which is the claim the panel supports; the matrix
  below keeps all nine values at six decimals.
- Figure 6 became a Cleveland dot plot on a full 0–100 % axis. The previous bar
  chart started at 60 %, which exaggerates differences between sections. The
  dot plot removes that distortion and still shows the clustering.
- Figure 4 lost its separate percentage labels inside the bar; the legend now
  carries both the count and the share, so the same information uses less ink.

## Values
Every printed number was carried over unchanged and checked against
`DATA_PACK/`. An automated pass confirms all nine transfer cells, the three
within-target ranges, the confirmation metrics and intervals, the exposure
counts and shares, the depth series, and the per-section values.

## Regenerating
`figures/redraw.py` writes both the SVG and the PDF for all six figures from
computed coordinates. Run it from the `figures` directory.
