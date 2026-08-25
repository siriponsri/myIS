# Visual QA: journal_03 submission pages 01-04

Source render directory: `%TEMP%\\rcrs_journal_03_render`
Inspected: `submission-01.png` through `submission-04.png` at source render resolution.

## Findings

### VQA-J03-01

- **Page:** 3
- **Severity:** MINOR
- **Finding:** Figure 1A's lower annotation row contains a visible text collision: the end of `fields | segments | packing` runs into the beginning of `weights/scoring frozen; index rebuilt`, making the phrase appear as `packingweights` at normal page scale.
- **Affected element:** Figure 1A lower annotation labels beneath the representation-program and frozen-retriever stages.
- **Acceptance criterion:** Regenerate Figure 1 so the two annotation strings have clear separation (or are wrapped/repositioned), with no touching glyphs at source resolution; all labels remain inside the figure bounds and legible in the single-column PDF.
- **Resolution:** IMPLEMENTED in `manuscript/scripts/build_figures.py` by wrapping the
  frozen-retriever annotation to two lines; Figure 1A and dependent package outputs
  were regenerated. A fresh source-resolution render was produced after the fix.

## Pages without findings

- **Page 1:** Title, abstract, keywords, and footer are within the printable area; no clipping or overlap observed.
- **Page 2:** Introduction text and footer are within the printable area; no clipping or overlap observed.
- **Page 4:** Related-work and method opening, including Equation (1), are within the printable area; no clipping or overlap observed.
