# Observatory Owner Guide

This guide is intentionally short. It is safe to run before Owner-local
measured preflight.

## Verify the synthetic layer

From `01_Research`:

```powershell
python -m myis_research.observatory.fixture --root . --check
pytest -q tests/test_observatory.py
```

The command creates a repository-safe fixture receipt. Its `evidence_class` is
`fixture`, `scientific_authority` is `false`, and all real P2 counters remain
zero.

## Read the outputs

`outputs/observatory/fixture-v1/registry.json` is the searchable evidence graph.
`RUN_SUMMARY.md` is the human-readable narrative. `receipt.json` binds the
registry and package hashes. `SHA256SUMS.txt` is the checksum closure.

## Future runner integration

An authorized runner should create a `CaptureSession` with an explicit vault
alias, request hash, profile hash, envelope hash, and environment lock hash.
The runner may store full prompts, logs, checkpoints, and protected artifacts in
the Owner-local vault. It must register only sanitized pointers and hashes in
the repository registry. A fixture receipt must never be promoted to measured
evidence.

## Dashboard

Launch the loopback Dashboard with `dashboard/open-dashboard.cmd`. The Overview
surface shows the current P2 boundary and Observatory health. The left rail
switches between Overview, Experiments, Artifacts, Prompts, Metrics, Evidence
Graph, Reports, Governance, Presentation, and Tools. All values are derived
from the shared read model.
