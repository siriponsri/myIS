# ArmIndex iSAI-NLP 2026 Paper 02

This immutable sibling integrates the aggregate-safe query-level A7 diagnosis
and a reproducibility capsule into the from-scratch iSAI-NLP 2026 rewrite.
`paper_00` and `paper_01` remain preserved historical siblings.

## Entry points

- Manuscript: `manuscript/paper_isainlp2026.tex`
- Review PDF: `build/paper_isainlp2026.pdf`
- Figure source: `figures/generate_figures.py`
- Figure data: `tables/a7-layer-aggregate-metrics.csv`
- Claim map: `provenance/claim_to_evidence.csv`
- Release manifest: `provenance/release-manifest-isainlp2026.json`
- Rebuild verifier: `verify_release.py`
- Figure environment lock: `requirements-figures.txt`
- Recorded Python runtime: `runtime-figures.txt`

## Verify and rebuild

Create a Python 3.11.9 environment, install the pinned figure dependencies,
and run:

```powershell
python -m pip install -r requirements-figures.txt
python verify_release.py --build
```

The verifier rejects any change to the canonical aggregate CSV before
regenerating the figures. `--build` additionally runs a clean, timestamp-fixed
build and requires `latexmk`, BibTeX, and an IEEEtran-compatible TeX
installation on `PATH`. The expected artifact is
`build/paper_isainlp2026.pdf`.

The capsule reproduces the aggregate-safe figures and manuscript, not the
protected retrieval run. Protected relevance data, identifiers, rankings,
per-query outcomes, credentials, and provider payloads remain outside the paper
workspace.
