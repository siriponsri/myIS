# Visual QA: Submission Pages 1-4

## Page 1 - PASS

- Severity: PASS
- Observable defect: No meaningful clipping, overlap, broken glyphs, or page-balance defect observed.
- Affected element: Title block, abstract, keywords, and footer.
- Smallest recommended fix: None.
- Acceptance criterion: Retain the current rendered layout.

## Page 2 - PASS

- Severity: PASS
- Observable defect: No meaningful clipping, overlap, broken glyphs, or typography inconsistency observed.
- Affected element: Introduction text and page footer.
- Smallest recommended fix: None.
- Acceptance criterion: Retain the current rendered layout.

## Page 3

- Severity: MAJOR
- Observable defect: The page contains only the final few lines of a continued paragraph, leaving most of the printable area blank and creating an unprofessional page break.
- Affected element: Introduction continuation and the float/page-break placement immediately before Figure 1.
- Smallest recommended fix: Relax or remove the hard float/page-break constraint so Figure 1 or following Introduction content occupies page 3.
- Acceptance criterion: Page 3 contains a normally balanced amount of manuscript content, with no large unused body area caused by avoidable float placement.

## Page 4 - PASS

- Severity: PASS
- Observable defect: No meaningful clipping, overlap, broken glyphs, caption-placement issue, or figure-label collision observed; Figure 1 is readable at the rendered page scale.
- Affected element: Figure 1, caption, related-work heading, and body text.
- Smallest recommended fix: None.
- Acceptance criterion: Retain the current rendered layout once the preceding page-break issue is resolved.
