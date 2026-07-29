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
No DAPFAM corpus, qrels, protected comparison surface, provider, paid API, GPU,
MLflow scientific run, measured manifest, or result has been accessed or created
by this preparation material.
