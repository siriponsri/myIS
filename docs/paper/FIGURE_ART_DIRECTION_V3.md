# FIGURE_ART_DIRECTION_V3

**Project:** myIS / iSAI-NLP 2026 short paper  
**Paper theme:** *Beyond the Retriever: Representation Transfer and Candidate Exposure in Cross-Domain Patent Retrieval*  
**Purpose:** art-direction and implementation specification for all paper figures, written **after reviewing publication-oriented guidance** on IEEE figure production, overview-figure design, simplification, color/accessibility, and subplot composition.  
**Audience:** Codex / local implementer.  
**Status:** authoritative figure-design brief (v3).

---

## 0) Executive summary (TL;DR)

The current figures are **scientifically serviceable but visually underpowered**. The main failure is not incorrect data; it is **weak visual hierarchy** and **mixed design languages**:

- too many boxes/cards,
- too many panel styles,
- too much “dashboard” feeling,
- decorative variety without enough narrative focus,
- and insufficient consistency across Figures 1–3 and the overview flow.

This v3 brief resets the design direction.

### The target design language

**Editorial scientific** — not infographic, not business dashboard, not poster art.

The figures must feel:

- **modern**,
- **minimal**,
- **confident**,
- **data-first**,
- **high signal / low ornament**,
- and immediately readable in **5 seconds**.

The figures should look like they belong to **one coherent system**, with:

- repeated typography,
- repeated spacing rules,
- repeated color roles,
- repeated annotation logic,
- and repeated hierarchy.

### Core idea

Do **not** chase “interesting” by adding more colors, icons, boxes, shapes, or visual effects.

Instead, chase interest by making the **geometry of the evidence** carry the story.

> One figure = one dominant message.

---

## 1) Research basis used for this brief

This brief is informed by the following sources and principles:

1. **IEEE Author Center**: vector graphics are preferred; acceptable vector formats include **PS/EPS/PDF**; non-vector images should meet **>300 dpi** for color/grayscale and **>600 dpi** for black-and-white line art. IEEE also gives standard target widths for one-column and two-column figures.  
2. **Proceedings of the IEEE figure guidelines**: figures should be clear, self-explanatory, consistent in typography and spacing, and should avoid unnecessary complexity or decoration.  
3. **Bang Wong / Nature Methods – The overview figure**: overview figures work best when they use an **A → B state-and-action structure** and visually highlight only the effective change across steps.  
4. **Bang Wong / Nature Methods – Points of review**: the **layout should express the meaning**; viewers rely on visual cues, so arrangement itself must communicate the claim.  
5. **Nature Methods – Unentangling complex plots**: when complexity grows, **carefully designed subplots / small multiples** are often superior to one overloaded overview plot.  
6. **Bang Wong / Nature Methods – The design process**: design should prioritize **utility and function**; effectiveness depends on how easily the viewer can decode the visual scheme.  
7. **Bang Wong / Nature Methods – Simplify to clarify / Avoiding color / Color blindness / Color coding**: simplify aggressively, avoid decorative color use, and make figures accessible and readable even under color-vision deficiency constraints.

### Implication for this paper

For this specific paper, the right answer is **not** “add more style.”  
The right answer is:

- reduce chart furniture,
- reduce boxy panel framing,
- give each figure a **single focal statement**,
- and make the four visuals feel like a family.

---

## 2) Paper-specific narrative map

The paper’s visual story has four jobs:

1. **Orient the reader** to the evidence sequence.  
2. **Reveal A3**: the “best representation” is not portable across frozen retrievers.  
3. **Confirm A5**: the selected complete configuration survives held-out evaluation.  
4. **Diagnose A7**: candidate exposure remains the major remaining bottleneck.

This means the visual system should have **four distinct roles**:

- **Overview / orientation**
- **Development insight (A3)**
- **Protected confirmation (A5)**
- **Post-confirmatory diagnosis (A7)**

The overview flow should feel like a **map**.  
Figures 1–3 should feel like **evidence exhibits**.

---

## 3) Non-negotiable constraints

### 3.1 Venue / production constraints

- Target venue: **IEEE-style two-column conference PDF**.
- Prefer vector outputs: **PDF + SVG source**.
- Also export **PNG proof renders** for human review.
- Default publication widths:
  - **One-column:** 3.5 in / 88.9 mm
  - **Two-column:** 7.16 in / 182 mm
- Typography must remain legible at final placed size.

### 3.2 Scientific constraints

- No invented values.
- No visual implication of significance where none is claimed.
- No visual implication of causal isolation when A5 compares complete systems.
- A7 bound must remain explicitly labeled as an **analytical fixed-pool bound**, not a reranker experiment.
- Figures must match canonical receipts and approved manuscript wording.

### 3.3 Design constraints

- No gratuitous 3D, gradients, shadows, glossy effects, or faux “presentation” visuals.
- No rainbow scales.
- No red-green dependency.
- No oversized legends when direct labeling is possible.
- No heavy rectangular boxes around every panel unless absolutely required.
- No multiple competing focal points in the same figure.

---

## 4) Global art direction system

## 4.1 Design philosophy

**Editorial scientific minimalism**

This is the governing style:

- calm,
- spacious,
- high-contrast,
- precise,
- and restrained.

Think:

- **paper figure**, not startup dashboard,
- **evidence artifact**, not infographic poster,
- **modern journal visual language**, not generic chart default.

### Key principle

**Remove anything that does not strengthen the main message.**

If an element does not improve decoding speed, it should probably be removed.

---

## 4.2 Narrative hierarchy

All figures must follow the same hierarchy:

1. **Figure-level title** — concise, assertive, substantive.
2. **Primary visual fact** — the main thing the eye sees first.
3. **Secondary support** — context, confidence intervals, or partitions.
4. **Interpretive note** — short, not essay-like.

This means:

- the most important number or relation must be visually dominant,
- supporting information must never compete with the main claim,
- and notes/legend text must be kept compact.

---

## 4.3 Typography

### Recommended font family

Use one sans-serif family consistently across all figures. Preferred order:

1. **Source Sans 3**
2. **Inter**
3. **IBM Plex Sans**
4. **Arial** (fallback)

Do **not** mix multiple families.

### Weight system

- Figure title: **Semibold / Bold**
- Panel title letters (A/B/C): **Bold**
- Axis labels / section labels: **Medium**
- Tick labels / notes: **Regular**

### Size system (final placed size)

- Figure title: 9.5–11 pt
- Panel title: 8.5–10 pt
- Axis labels: 8–9 pt
- Tick / value labels: 7.5–8.5 pt
- Footnote / note line: 7–8 pt

### Text rules

- Use **sentence case** or concise title case consistently.
- Avoid all-caps except for very short stage labels in the overview flow.
- Keep line breaks intentional.
- Use **direct labels** wherever possible instead of separate legends.

---

## 4.4 Color system (semantic, not decorative)

Use a **role-based palette**, not a category-explosion palette.

### Core palette roles

- **Ink / structure:** dark navy or charcoal  
  Used for titles, main outlines, primary text.
- **Neutral / comparator / context:** cool gray  
  Used for baselines, comparator, inactive items.
- **Focus / confirmed result:** medium blue  
  Used for selected system, focal evidence, observed value.
- **Limitation / missing exposure:** muted coral or warm red  
  Used only where “missing / absent / loss” is the message.
- **Analytical bound / ceiling / theoretical headroom:** muted amber  
  Used only for bound-related elements.
- **Optional stage accent (overview only):** muted teal  
  Used sparingly in the development portion of the overview flow.

### Palette principles

- Color is for **semantic role**, not decoration.
- Avoid giving every source model a bright unique color unless the figure truly needs category identity.
- For Figure 1, prefer **shape or direct labeling** for source identity; use color only sparingly.
- Ensure usability under color-vision deficiency.

### Suggested concrete palette (editable)

- Ink: `#1E3557`
- Neutral gray: `#A9B6C4`
- Context gray-dark: `#7D8D9D`
- Focus blue: `#3E86C8`
- Focus blue-dark: `#2B6CA8`
- Coral: `#D85C4A`
- Amber: `#D8A62A`
- Teal (optional): `#0F9D9A`
- Background: pure white
- No panel fill colors except extremely light neutral background if needed.

---

## 4.5 Line / mark language

### Global rules

- Thin-to-medium strokes only.
- Rounded linecaps are acceptable for dumbbells and timeline connectors.
- Avoid thick enclosing rectangles.
- Prefer open space over boxes.

### Use of shapes

Shapes should be **meaningful**, not ornamental.

- circle = ordinary point
- ring / outline = matched source-target reference point
- filled highlight = focal or nominal best point
- bar / ribbon = partition or aggregate share
- line / dumbbell = comparison or distance

Do not introduce too many shape types.

---

## 4.6 Precision policy

### In-figure numeric precision

Use the minimum precision needed for the message.

- Default value labels: **3 decimals** for visual readability.
- Use **6 decimals** only when the exact value is itself part of the claim and there is enough space.
- If exact 6-decimal values are important, the full precision may appear in caption/body while the figure uses 3 decimals.

### Important exception

For the A5 paired-difference callouts, using **6 decimals** is acceptable because those values are central to the paper’s climax.

---

## 4.7 Spacing rules

Whitespace is not waste.

Use whitespace intentionally to:

- separate evidence layers,
- create emphasis,
- and avoid panel crowding.

### Spacing rules

- Do not let labels crash into points or error bars.
- Do not cram 3 equal-size panel cards into one row unless each panel is truly light.
- Use asymmetry when it improves hierarchy.
- Leave enough breathing room above titles and below annotation notes.

---

## 5) Tooling strategy (not limited to Altair or D2)

## 5.1 Recommended production stack

### Preferred quantitative plotting stack

**Primary recommendation:**

- **Python + Matplotlib** for the final quantitative figure rendering.

Reason:

- strongest low-level control,
- easy PDF/SVG output,
- robust annotation control,
- easy reproducibility,
- good integration with numerical audit and repository workflows.

### Optional helpers

- **Pandas** for data loading and reshaping
- **NumPy** for geometry / placement
- **svgwrite** or **CairoSVG** if direct SVG compositing is helpful
- **Inkscape** or **Figma** only for final micro-polish *without changing the numbers*

### Prototype / exploration tools (allowed but not preferred for final)

- **Altair / Vega-Lite**: good for rapid prototyping and grammar exploration, but less ideal than Matplotlib for this specific final-paper polish.
- **Plotnine**: okay if the implementer thinks in ggplot grammar, but final output still needs careful typographic cleanup.
- **D2 / Mermaid / Graphviz**: acceptable for rough workflow ideation, but **not preferred** for the final overview figure because the current paper needs a more editorial, custom layout.
- **Figma**: good for refinement once the quantitative artwork is exported as vector, but must not become the source of truth for numbers.

## 5.2 Specific recommendation for this paper

### Use this division of labor

- **Figures 1–3:** Python + Matplotlib
- **Overview evidence map:** Python (matplotlib or svgwrite) **or** Figma/Inkscape based on a strict wireframe; avoid default D2 look
- Export final assets as:
  - `.pdf`
  - `.svg`
  - `.png` proof

### Do NOT do this

- do not let D2 define the final visual style,
- do not rely on Datawrapper defaults for final figures,
- do not hand-edit numbers visually without code provenance,
- and do not integrate into `main.tex` before the visual QA pass.

---

## 6) Figure inventory and status

Recommended final set:

1. **Overview evidence map** (optional but strongly encouraged if space permits)  
   Purpose: orient the reader early.
2. **Figure 1 — A3 transfer**  
   Purpose: conceptual reveal.
3. **Figure 2 — A5 confirmation**  
   Purpose: scientific climax.
4. **Figure 3 — A7 diagnosis**  
   Purpose: final diagnostic resolution.

If page pressure is severe:

- keep Figures 1–3 mandatory,
- make the overview figure shallow and compact,
- or move the overview figure to a small full-width strip near the Introduction/Study Design transition.

---

## 7) Overview evidence map — exact design brief

## 7.1 Message

The overview should communicate the **evidence pipeline**, not a decorative project roadmap.

Main message:

> Development constructs and probes the configuration story (A1/A2 → A3), then the development stage closes; only after that does the paper freeze, confirm, and diagnose (Selection-125 / Final-872 → full benchmark / A7).

## 7.2 Layout

Use a **single horizontal evidence path** with a strong central gate.

### Required structure

```text
CONSTRUCT  →  TEST PORTABILITY   ║   FREEZE & CONFIRM  →  DIAGNOSE
A1/A2         A3                     Selection-125/Final-872   Full benchmark/A7
               DEVELOPMENT CLOSED
```

### Visual grammar

- A thin but confident horizontal line.
- Four major nodes or stations.
- A **vertical gate** between development and protected/post-confirmatory evidence.
- The words **DEVELOPMENT CLOSED** should sit at or just above the gate.
- No giant icons.
- If icons are used at all, they must be very small and secondary.

## 7.3 Tone

This should feel like a **clean evidence map**, not a startup process slide.

## 7.4 Size

- Width: two-column
- Height target: ~0.85–1.20 in
- Must remain shallow

## 7.5 What to avoid

- giant circular badges,
- colorful cartoon icons,
- thick stage boxes,
- overexplaining every stage inside the visual.

---

## 8) Figure 1 (A3) — exact design brief

## 8.1 Scientific role

This is the **conceptual turning-point figure**.

Main question:

> Best representation—for whom?

Main claim:

> Representation advantages are not portable across frozen retrievers; target-dependent behavior is the message.

## 8.2 Visual objective

The figure should show two things at once:

1. the **absolute context** (the three target levels are different), and
2. the **within-target reshuffling** (the preferred source changes across consuming retrievers).

## 8.3 Recommended layout

**Two-column width**, moderate height.

### Preferred final structure: integrated 3-row layout

Each row corresponds to one **consuming retriever / target**.

For each row, show:

- **Left block (context):** actual Recall@100 values of the three source-derived representations on a shared absolute x-axis.
- **Right block (local transfer view):** a zero-centered mini-axis showing **difference from the matched source-target value** within the same row.

So the figure reads row-wise:

```text
PatEmbed target   [absolute score positions ........]  |  [delta from matched 0]
Arctic target     [absolute score positions ........]  |  [delta from matched 0]
Qwen3 target      [absolute score positions ........]  |  [delta from matched 0]
```

This creates **focus + context** without resorting to bulky panel boxes.

## 8.4 Encoding

### Source identity

Use either:

- three subtle shapes, **or**
- very small direct labels,

but do not depend on bright color coding.

### Highlighting rules

- The **matched source-target point** gets a dark outline ring.
- The **nominal best source within the row** gets a filled amber accent.
- Non-highlighted points stay muted.

### Notes

- Do **not** imply statistical significance.
- Ranges are small; the figure should visually acknowledge that without making it look trivial.

## 8.5 Annotation strategy

- Row labels should be explicit: “PatEmbed target”, “Arctic target”, “Qwen3 target”.
- Use a short subtitle or note like:
  - “Absolute context at left; local difference from matched source at right.”
- Keep explanatory legend tiny, preferably integrated into a single note line.

## 8.6 Size target

- Width: two-column
- Height: ~2.0–2.4 in

## 8.7 What to avoid

- large top legend block,
- multiple disconnected panels that feel like different figures,
- overuse of bright categorical colors,
- a giant empty canvas with three lonely points,
- or a slopegraph that emphasizes rank while hiding the actual magnitudes.

---

## 9) Figure 2 (A5) — exact design brief

## 9.1 Scientific role

This is the **climax figure**.

Main message:

> The selected complete configuration survives Final-872 held-out confirmation.

Secondary message:

> The result compares complete systems; representation-only causality is not claimed.

## 9.2 Visual objective

The eye should land first on:

- `+0.111379` Recall@100,
- `+0.086342` nDCG@100,
- and then the W/T/L support.

## 9.3 Recommended layout

Use a **single integrated figure**, not three equal “cards.”

### Preferred structure

- **Main body:** two metric rows (Recall@100 and nDCG@100)
- **Bottom strip:** W/T/L ribbon

Each metric row should combine:

1. absolute comparator vs selected values (dumbbell or anchored comparison), and
2. paired-difference + CI shown as the row’s right-side emphasis.

This means the figure is read in **rows**, not as three competing blocks.

### Wireframe idea

```text
Recall@100   cmp .331 ───────── sel .442      +0.111 [95% CI]

nDCG@100     cmp .279 ─────── sel .366        +0.086 [95% CI]

Wins / Ties / Losses: 619 | 158 | 95
```

## 9.4 Encoding

- Comparator = neutral gray
- Selected system = focus blue
- Difference interval = focus blue-dark
- Ties = context gray-dark
- Losses = muted coral
- Wins = focus blue

## 9.5 Annotation strategy

- Keep titles short and strong.
- Put the exact difference labels near the CI marks.
- Add one compact interpretive note line only if necessary.
- W/T/L should not visually compete with the metric rows.

## 9.6 Size target

- Width: two-column preferred
- Height: ~1.8–2.2 in

If space is very tight, a strong one-column version is possible, but two-column is preferred because this figure is the paper’s climax.

## 9.7 What to avoid

- three equal boxes,
- huge legends,
- panel C looking larger and more important than the effect rows,
- or making the CI view and absolute view feel disconnected.

---

## 10) Figure 3 (A7) — exact design brief

## 10.1 Scientific role

This is the **diagnostic ending**.

Main message:

> Most strict cross-domain relevant evidence never reaches the Top-200 pool.

Follow-up message:

> Even perfect within-pool ordering would recover only limited additional macro-Recall.

## 10.2 Visual objective

The figure should feel like a **two-step argument**:

1. what entered the pool,
2. what reordering could still recover.

## 10.3 Recommended layout

Use a **vertical or strong left-to-right narrative sequence**, not two unrelated cards.

### Preferred structure

**Stage 1: Exposure anatomy**  
A single strong stacked bar or partition ribbon showing:

- by rank 100,
- first at ranks 101–200,
- absent from Top-200.

The dominant visual fact must be:

- `4,065 / 5,193 absent from Top-200`
- `78.3%`

**Stage 2: Within-pool ordering bound**  
Below (or to the right, if space is ideal), show a clean observed-to-bound comparison with the headroom annotation.

### Wireframe idea

```text
WHAT REACHED THE POOL?
[ 15.3% | 6.4% | 78.3% absent ]
4,065 / 5,193 absent from Top-200

↓ within available pool

HOW MUCH CAN ORDERING RECOVER?
Observed .188 ───────── Bound .260
          +0.071717 headroom
```

## 10.4 Encoding

- Observed = focus blue
- Bound = amber
- Absent = coral (dominant)
- Minor exposure partitions = muted blue/gray

## 10.5 Annotation strategy

- Make it explicit that the bound is **analytical** and tied to a **fixed Top-200 pool**.
- Keep the note line short.
- Avoid overloading with many auxiliary percentages unless directly useful.

## 10.6 Size target

- Width: two-column preferred
- Height: ~1.8–2.2 in

## 10.7 What to avoid

- equal-size panel cards,
- unnecessary axes if direct labeling is clearer,
- underemphasizing the 78.3% absent finding,
- or making the bound look like an experimental reranker result.

---

## 11) Cross-figure consistency rules

Figures 1–3 and the overview must share the same design grammar.

### Required consistency

- same font family,
- same title styling,
- same panel-letter styling,
- same core palette,
- same note style,
- same stroke thickness family,
- same value-label style,
- same whitespace philosophy.

### Strong recommendation

Use the same title architecture:

- **Panel letter + short substantive phrase**
- followed by a very short gray subtitle if needed.

Example pattern:

- `A Representation transfer depends on the consuming retriever`
- `B Final-872 paired differences`
- `A Candidate exposure anatomy`

---

## 12) Caption strategy

Captions must do the following:

1. identify the dataset slice / evidence source,
2. state what is being compared,
3. define any highlighting or encoding,
4. explicitly bound the inference,
5. and avoid essay-length explanation.

### Example tone

- crisp,
- scientific,
- bounded,
- non-promotional.

### Do not do this

- do not describe every pixel,
- do not restate the entire Results section,
- do not use theatrical wording like “dramatic,” “stunning,” “crack,” or “climax” in the caption itself.

---

## 13) Recommended page-placement strategy

A good target arrangement is:

- **Overview evidence map:** early, after Introduction/Study Design bridge or at start of method framing
- **Figure 1:** top of the results page where A3 is discussed
- **Figure 2:** at the protected-confirmation section, ideally prominent
- **Figure 3:** in the diagnosis section near the conclusion of A7

### Important

Do not force figures into awkward positions that create huge white holes in the text.  
Placement must serve both **narrative order** and **page economy**.

---

## 14) Implementation instructions for Codex

## 14.1 General workflow

1. Read this brief fully.
2. Do **not** redesign from scratch using personal taste.
3. Build figures to this spec.
4. Use canonical CSV/receipts as the single source of truth.
5. Export each figure in:
   - PDF
   - SVG
   - PNG proof
6. Save plotting scripts in a reproducible form.
7. Produce a visual review sheet (optional contact sheet) before integrating into `main.tex`.
8. Only after approval: integrate into LaTeX and adjust captions/placement.

## 14.2 File expectations

Suggested structure:

```text
docs/paper/figures/
  generate_figures_v3.py
  fig1_a3_transfer_v3.pdf
  fig1_a3_transfer_v3.svg
  fig1_a3_transfer_v3.png
  fig2_a5_confirmation_v3.pdf
  fig2_a5_confirmation_v3.svg
  fig2_a5_confirmation_v3.png
  fig3_a7_diagnosis_v3.pdf
  fig3_a7_diagnosis_v3.svg
  fig3_a7_diagnosis_v3.png
  overview_evidence_map_v3.pdf
  overview_evidence_map_v3.svg
  overview_evidence_map_v3.png
```

## 14.3 Review-first rule

**Do not change `main.tex` layout aggressively until the figure artwork has passed visual review.**

Meaning:

- generate the artwork first,
- inspect it at target print size,
- then integrate.

---

## 15) QA checklist (must pass before LaTeX integration)

Each figure must pass all of the following.

### 15.1 Scientific QA

- [ ] Numbers match canonical sources.
- [ ] Caption and figure encoding agree.
- [ ] No unsupported inference is implied.
- [ ] Bound / confirmation / development evidence are clearly differentiated.

### 15.2 Visual QA

- [ ] One dominant visual message is obvious in <5 seconds.
- [ ] There is a clear focal element.
- [ ] Typography is legible at final placed size.
- [ ] The figure does not feel boxed-in or dashboard-like.
- [ ] White space is intentional, not accidental.
- [ ] The figure family feels stylistically consistent.

### 15.3 Accessibility QA

- [ ] Still readable in grayscale or near-grayscale.
- [ ] Does not depend on red-green discrimination.
- [ ] Labels remain readable for reviewers on printouts.

### 15.4 Production QA

- [ ] Vector PDF/SVG export is clean.
- [ ] No clipping, missing fonts, or placeholder graphics.
- [ ] No giant transparent margins.
- [ ] Final width and height are known and intentional.

---

## 16) What success looks like

A successful v3 figure set should produce this reaction:

- “I immediately understand the paper’s evidence sequence.”
- “Figure 1 clearly tells me that transfer is target-dependent.”
- “Figure 2 looks like the paper’s confirmation moment.”
- “Figure 3 lands the final diagnosis cleanly.”
- “These four visuals look like one coherent scientific system.”

A failed figure set will feel like:

- generic plots,
- overboxed panels,
- overstyled infographic components,
- or an inconsistent mix of chart defaults.

---

## 17) Bottom-line design decisions

### Keep

- strong scientific restraint,
- simple geometry,
- direct labeling,
- role-based palette,
- evidence-bound wording,
- and a compact overview flow.

### Remove

- card-heavy panel framing,
- giant legends,
- giant icons,
- decorative shape variety,
- unnecessary exact-value clutter,
- and slide-deck visual language.

### Preferred final style keywords

- modern
- minimal
- editorial
- scientific
- crisp
- spacious
- confident
- coherent

---

## 18) If forced to choose: best tool recommendation

If one single stack must be chosen for the final pass, choose:

> **Python + Matplotlib for Figures 1–3, plus optional Figma/Inkscape micro-polish for the overview flow and final vector cleanup.**

Why:

- best numeric reproducibility,
- best control,
- easiest auditability,
- easiest PDF/SVG export,
- and least risk of ending with “pretty but wrong” or “correct but generic.”

D2 may still be used for rough thinking, but it should **not** dictate the final visual language.  
Altair may still be used for rapid exploration, but it should **not** be the only production path.

---

## 19) Final instruction to implementer

Build the next revision as an **implementation of this brief**, not a fresh creative reinterpretation.

The goal is not to produce “more design.”  
The goal is to produce **better decoding, better emphasis, and one coherent figure family**.

