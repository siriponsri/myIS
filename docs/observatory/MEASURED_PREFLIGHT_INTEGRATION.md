# Measured Preflight Integration Prerequisite

This checklist describes the explicit handoff required before a future
Owner-local P2 measured run. The current repository-only closeout does not
execute any item and does not change real counters.

- Pre-run: register the request, Git commit, environment, prompt/config/schema,
  compiler, retriever, evaluator, budget profile, and execution envelope.
- Runtime: record stage transitions, privacy-safe heartbeat, resource/runtime/
  cost aggregates, candidate registration, metric registration, and checkpoints.
- Freeze: create baseline commitment and reproduction, validate the candidate
  ledger, create the immutable shortlist-freeze receipt, then allow at most one
  selection exposure for the frozen shortlist.
- Recovery: retain failure, checkpoint, recovery, counters-before/after,
  validation, residual-risk, and decision records without promoting partial
  metrics.
- Closeout: create manifest/package and aggregate receipt, validate hashes and
  lineage, sync repository-safe MLflow, Obsidian, Dashboard/read model, and the
  append-only session capsule.

Runtime integration is `prerequisite_not_validated` until an Owner-local
preflight exercises this path under the separate execution contract. No
protected store, final split, D2, D3, GPU, paid API, network model download, or
provider fallback is authorized by this document.
