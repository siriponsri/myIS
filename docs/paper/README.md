# ArmIndex iSAI-NLP 2026 Paper 01

This immutable sibling is a from-scratch iSAI-NLP 2026 rewrite grounded in the
A5 held-out confirmation and A6/A7 frozen-pool audits. `paper_00` is preserved
as historical context and is not an iSAI submission artifact.

This directory is the final paper package recorded on 2026-08-25. Open
`paper_isainlp2026.pdf` for the reviewed PDF. The same byte-identical PDF is
retained under `build/` beside the build bibliography.

## Entry points

- Manuscript: `manuscript/paper_isainlp2026.tex`
- Review PDF: `build/paper_isainlp2026.pdf`
- Figure source: `figures/generate_figures.py`
- Figure data: `tables/a7-layer-aggregate-metrics.csv`
- Claim map: `provenance/claim_to_evidence.csv`
- Release manifest: `provenance/release-manifest-isainlp2026.json`
- QA and review reports: `reports/`
- Artifact hashes: `SHA256SUMS.txt`

The package contains aggregate-safe evidence only. Protected relevance data,
identifiers, rankings, per-query outcomes, credentials, and provider payloads
must remain outside the paper workspace.
