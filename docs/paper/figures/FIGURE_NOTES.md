# Final Figure Design Notes

`build_second_generation_figures.py` reads only the aggregate-safe canonical
CSV pack at `../prism-uploads/myIS_prism_csv_pack_20260826.zip`, asserts every
displayed A3, A5, and A7 value, and exports the selected SVG/PNG figures to
`rebuilt/`. `build_evidence_map.py` creates the optional overview as a
deterministic SVG/PNG editorial ribbon in the same directory.

All artifacts use the same white, navy-ink, blue focal, teal source/development,
violet protected-confirmation, slate comparator, amber best/bound, and coral
limitation system. The colors have semantic roles; none is wired into `main.tex`
in this design pass.

## Figure 1: Best representation--for whom?

The selected nominal-rank bump plot foregrounds source-rank crossings
across consuming retrievers, then uses a small absolute-score strip to show
that the within-target ranges are small. Amber marks nominal within-target
best. The annotation keeps the A3 result explicitly descriptive.

## Figure 2: Final-872 confirmation

The figure contains independent horizontal panels for (A) absolute
performance, (B) paired effect estimates with their 95% CIs, and (C) the
Recall@100 100% win/tie/loss strip. The selected system and focal
`+0.111379` effect use blue; the comparator is slate and losses use coral.

## Figure 3: Candidate exposure

The figure pairs a 100% exposure decomposition with an observed-to-bound
point interval. Coral foregrounds the `4,065 / 5,193` Top-200 absence; amber
marks the fixed-pool perfect-ordering bound and its `+0.071717` headroom.
The explicit note maintains the separate incidence and macro-Recall scales.

## Optional overview: Evidence map

`build_evidence_map.py` renders four editorial milestones rather than a
software-architecture diagram: construct, test portability, freeze and
confirm, and diagnose. Fine-line vector icons make each conceptual beat
skim-readable. A vertical development/protected-evaluation boundary is the
central visual device. At full IEEE width it is 1.25 inches high and can remain
optional until a layout pass establishes that it earns its space.
