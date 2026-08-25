# Build and QA Report -- paper_01

Date: 2026-08-25

## Build result

- Toolchain: MiKTeX PDFLaTeX/BibTeX via latexmk 4.88.
- Result: PASS.
- Output: `paper_01/build/paper_isainlp2026.pdf`.
- SHA-256: `698867328d7f76b2854fdc5561a53a9c3c18041b6de2310330e2cf8df3494ce0`.
- Pages: 4 of 6 maximum.
- Paper: A4, IEEEtran conference, 10 pt, two columns.

## Deterministic checks

- `scripts/paper_guard.py`: PASS; 4 pages; 0 displayed-math markers.
- LaTeX log: no overfull or underfull boxes; no unresolved citation,
  reference, or multiply-defined-label warnings.
- PDF text anonymity scan: PASS.
- Fonts: all embedded; no Type 3 fonts.
- Figures and tables: present and cited.
- Final column balance: normal `balance` package placement before Conclusion.

Paper-guard informational findings are limited to a table-tokenization false
positive, reviewed literature URLs, and long-line heuristics in structured
provenance/BibTeX files. None is a release defect.

## Visual checks

- Pages 1-3: PASS after closing the prior Fig. 2 `332` label overlap.
- Page 4: see `reviews/VISUAL_REVIEW_01.md`.

## Environment notice

MiKTeX emitted its routine notice that update checks have not been run. The
build completed successfully and the resulting PDF passed format, font,
reference, and visual checks.
