# Build and QA Report -- paper_02

Date: 2026-08-26

## Build

- Toolchain: MiKTeX PDFLaTeX/BibTeX via latexmk 4.88.
- Result: PASS on three timestamp-fixed clean builds using Python 3.11 and the
  pinned figure dependencies.
- Output: `build/paper_isainlp2026.pdf`.
- SHA-256: `5ffa6ba0aff7e7c3b7a115c3a9fa06af06c0fad7e5465c2f3d8bf2472755dbea`.
- Pages: 4 of 6 maximum; A4, IEEEtran conference, 10 pt, two columns.

## Deterministic checks

- `verify_release.py --build`: PASS; canonical input hash
  `ad869ef99254df10c2e155911a1aa1a975dc9e41f1203bffa1fac2ab66043c1e`.
- `tests/test_verify_release.py`: PASS; changed figure input is rejected.
- `scripts/paper_guard.py`: PASS; 4 pages and 0 displayed-math markers.
- PDF hash was identical across the final two clean builds.
- LaTeX log has one known `balance` output-routine warning (`2.02484pt`);
  rendered page 4 has no clipping or overflow. No unresolved citation,
  reference, or multiply-defined-label warnings occur.
- Fonts are embedded and no Type 3 fonts are present.

## Visual checks

- Pages 1-4 were rendered and inspected. Fig. 2(b) labels were corrected so
  `101-200` is directly associated with its hatched segment at final size.

