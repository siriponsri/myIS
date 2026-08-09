# A1.2 Governed Long Run v16

This runbook is the tracked execution plan for the Owner-approved same-instance
A1.2 closeout on Vast instance `47256937`. It is additive engineering
integration over the frozen v11-v15 scientific request; it does not change
models, programs, evaluator, split, metrics, promotion rule, or protected-data
boundaries.

## Scope

- Phase: `A1_BASELINES_AND_MULTI_ARM_SCREENING`
- Task: `A1.2`
- Workload: five arms x five frozen programs, `25/25` common-screen cells
- Topology: `ARM-01` Owner-local CPU; `ARM-02` through `ARM-05` one GPU each
- Provider: unchanged Vast instance `47256937`
- Owner-approved limits: common screen `$27`, A1 `$32`, campaign `$150`, TTL 40 hours
- Scientific evidence remains closed until execution-adoption PASS

## Launch sequence

1. Verify clean pushed commit/tree and build the external v16 engineering bundle.
2. Re-read authenticated provider identity, runtime/GPU identity, fresh all-fee
   quote, whole-workload budget admission, management dry-run, watchdog/TTL,
   protected compiler receipt, and all 25 frozen bindings.
3. Write aggregate-safe provider-admission and execution-adoption receipts.
4. Materialize an Owner-local v16 input manifest bound to the same attempt ID.
5. Start the v16 lifecycle, run `ARM-01` locally, and launch the four remote
   workers over pinned SSH with offline runtime variables.
6. Wait for all 20 remote cells, fail fast on worker failure, merge all 25
   receipts, validate checkpoints and safe return, then evaluate locally.
7. Apply only the frozen deterministic promotion rule. Do not open A2,
   HARNESS-DEV, Selection, Final, `D2_OPEN_FINAL`, or `D3_SUBMIT_RELEASE`.
8. Sync aggregate-safe evidence and reports, commit/push, tell Owner to destroy
   instance `47256937` in the Vast dashboard, and verify SSH is unreachable.

## Hard stops

Stop and preserve bounded evidence if any identity, hash, runtime, budget, TTL,
watchdog, protected-boundary, checkpoint, safe-return, or `25/25` requirement
drifts. Never upload protected payloads, credentials, tokens, raw provider
responses, query identifiers, rankings, or per-query outcomes to Git or
projections. A failed worker cancels/reaps its siblings and emits a failure
marker before the run is considered failed closed.

## Required evidence

The ledger and generated reports must record the attempt ID, immutable bundle
and manifest hashes, gate receipts, aggregate counts, safe-return hash, charge
and TTL observations, closeout status, Owner destruction confirmation, and the
final SSH disposition. They must not contain protected payloads or credentials.
