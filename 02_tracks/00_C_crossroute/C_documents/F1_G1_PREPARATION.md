# F1/G1 Preparation State

F0 is closed and G0 is approved. F1 remains `waiting_gate`; G1 remains
`pending`. This document prepares the reproduction boundary only and does not
authorize F1.1 or any scientific execution.

The checked-in DAPFAM templates are intentionally draft-only:

- `03_experiments/templates/f1-dapfam-runspec-draft.yaml`
- `03_experiments/templates/f1-dapfam-measured-manifest-draft.yaml`

Both declare `status: draft`, `executable: false`, `gate: G1`, and no data,
artifacts, or scientific metrics. The CLI command `myis-harness reproduce
dapfam` can only validate the RunSpec draft when explicitly asked and otherwise
returns `WAITING_GATE`; it has no reproduction executor.

Before F1.1 can run, the Owner must explicitly commit the corpus, query, qrels,
family, evaluator, field protocol, published targets, compute budget, exact split
membership/hash, exact OUT-positive counts, and reproduction authorization, then
issue G1 using the immutable decision process. Exact split membership and counts
must come from the protected Owner process; the repository must not infer them
from estimates or access protected membership.
Outside the dedicated Owner-local hash/validation command, no DAPFAM payload,
protected comparison surface, provider, paid API, GPU, MLflow scientific run,
measured manifest, or result is accessed or created by this preparation system.

## Implemented Owner-local workflow

`05_code/scripts/Start-F1G1Preparation.ps1` is the only preparation command that
opens the approved local DAPFAM files. It validates the five source byte/hash
anchors in place, checks 45,336 corpus rows, 1,247 unique queries and 49,869
qrels rows, computes the family/evaluator/field/target commitments, and creates
one seed-42 Hamilton/SHA-256 split with exact counts `250/125/872`.

Raw membership and absolute paths remain under the external Owner-local store.
Git, Dashboard, MLflow, and the safe executed notebook receive only identifiers,
hashes, counts and aggregate domain state. OUT-positive counts are computed once
per query from aligned `OUT` rows with `grade > 0`; estimates in planning text
are not substituted for the generated values.

The safe batch uses `myis.g1-owner-value-batch.v1`, remains `proposal`,
`executable=false`, `G1=pending`, and `authorization=NOT_AUTHORIZED`. Its
`proposal_sha256` covers semantic commitments only. Timestamps, validation
receipts, MLflow linkage and future Owner decision hashes are excluded. A
corrected proposal is appended and selected by the external current projection;
prior sealed/batch bytes are never overwritten.

The preparation-only MLflow run is in `myis-research-track-c` with no metrics
and no artifacts. The Dashboard Presentation view is Thai-first and labels all
B0/B1/B2 scientific results `ยังไม่รัน - รอ G1`. DAPFAM remains a measure of
family-level retrieval relevance, not novelty, validity, infringement, freedom
to operate, or legal truth.

Even after a future valid G1 record and frozen RunSpec are supplied,
`myis-harness reproduce dapfam` returns
`HANDOFF_READY_EXECUTOR_UNAVAILABLE`. Actual B0/B1/B2 execution is explicitly
deferred.
