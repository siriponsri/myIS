# P2 v2 Owner-local Preflight Blocker Audit

## Objective

Audit the blocked P2 v2 Owner-local preflight and define the smallest repair that preserves P1 evidence, v1 history, the selection freeze barrier, and the protected-data boundary.

## Starting State

The reviewed revision is commit `abb8e1981c652fc14c3a9b779b99372e1a401b2a`, tree `ffa06896a1dc3b7a99cde3939a617ed33665b2be`. All four Git worktrees were clean. No P2 request or preflight receipt existed; measured runs, real candidates, shortlist entries, and selection accesses were all zero. Final-872 was closed and D2/D3 were waiting for the Owner.

## Inputs and Frozen Bindings

- Active profile: `control/budgets/p2-r1-primary-v2.yaml`
- Active envelope: `control/execution-envelope-p2-v2.yaml`
- Active revision: `control/campaigns/scope-autoindex-p2-r1-primary-v2.yaml`
- Runbook: `control/runbooks/P2_MEASURED_AUTORESEARCH_V2.md`
- Accepted P1 receipt: `campaigns/scope-autoindex-v1/evidence/dapfam-p1-fulltext-c058a3aa7357c782.receipt.json`

## Work Performed

Traced the evaluator through the accepted P1 request/receipt and both Git revisions; compared source bytes, AST structure, deterministic outputs, protected rows, and commitments. Traced active profile/envelope/revision selection through source-of-truth, preflight, measured contracts, read model, schemas, tests, and report policy.

## Artifacts Produced

This Markdown audit and `outputs/audits/rigor/p2-v2-owner-local-preflight-blockers-20260804.json`. No measured artifact, request, receipt, candidate, shortlist, or Owner decision was created.

## Metrics

| State | Value |
|---|---:|
| Confirmed blockers | 3 |
| Evaluator differential cases | 4 |
| Measured runs | 0 |
| Real candidates | 0 |
| Shortlist entries | 0 |
| Selection accesses | 0 |

## Result

Repair status: `implemented_pending_clean_commit_verification`. The explicit type-A compatibility manifest, active-v2 resolver, measured-request registry dispatch, and preflight receipt v2 are implemented. Focused verification passed `46` tests; the clean-commit E2E remains intentionally pending until the implementation is committed.

| Blocker | Evidence | Root cause | Confidence |
|---|---|---|---|
| Evaluator hash | P1 `6dd3b1d2...`; committed current `018149dd...`; Windows bytes `0adc1e9a...` | Type A byte/instrumentation drift. `progress_sink` parameter and two calls are the exact source difference. | High for scientific equivalence |
| Active binding | `preflight.py:_campaign_binding_ok` requires `p2-r1-primary-v1` while source-of-truth selects v2 | Historical constant remained in the active preflight path. | High |
| Registry split | `contracts.py:P2_ARTIFACT_SCHEMAS` omits `myis.p2-measured-request.v1` | Legacy and measured validators evolved as separate registries. | High |

## Interpretation

The evaluator mismatch is classification A, not B relocation and not C semantic change. Scientific outputs are identical after removing only observer instrumentation. Operationally, a supplied progress callback emits events and a raising callback aborts before an authoritative result; this difference must remain explicit and fail closed.

## Supported Claims

- The reviewed commit cannot reach `passed_pending_owner` through the active v2 request contract.
- The current evaluator differs from P1 by progress instrumentation only.
- A compatibility manifest plus independent verification can preserve scientific comparability without aliasing hashes.

## Unsupported Claims

- P2 preflight passed.
- P2 measured execution started.
- R1 improves retrieval quality.
- Selection or final-872 may be opened.

## Failures and Recovery

Direct evaluator equality fails, active campaign binding selects v1, and the shared registry rejects the measured request. Recovery requires a versioned compatibility proof, fail-closed active resolver, measured-request registry dispatch, and preflight receipt v2. Any proof mismatch changes the decision to baseline reproduction under a new campaign revision.

The first managed report sync failed closed with an immutable aggregate-only `sync_deferred` receipt because the worktree venv did not contain the locked MLflow extra. The governed store passed read-only doctor validation and no archive receipt was created. Recovery installed `uv.lock` with `--all-extras`; retry uses a new projection revision and preserves the deferred receipt.

## Governance and Safety

The audit accessed only repository-safe aggregate metadata. It did not inspect protected qrels, membership, query IDs, rankings, per-query outcomes, credentials, prompts, or provider payloads. CPU-only, zero paid API, no GPU, no network model download, and no fallback remain binding.

## Decision

Implement the type-A compatibility path. Do not alias evaluator hashes, rewrite P1 lineage, use v1 fallback, or modify the scientific campaign definition.

## Next Action

Commit the repository repair, run the synthetic v2 preflight from that clean commit, and independently verify `passed_pending_owner` while the real request and all measured counters remain absent or zero.

## Evidence Links

- `control/source-of-truth.yaml`
- `control/runbooks/P2_MEASURED_AUTORESEARCH_V2.md`
- `src/myis_research/kernel/p1.py`
- `src/myis_research/p2/preflight.py`
- `src/myis_research/p2/contracts.py`
- `src/myis_research/p2/measured_contracts.py`
- `src/myis_research/p2/measured_adapter.py`
- `docs/observatory/REPORTING_POLICY.md`
