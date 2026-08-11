# A1.2 Governed Long Run v16

This runbook is the tracked execution plan for one Owner-approved A1.2 attempt
on a freshly provisioned instance. The instance identifier is supplied at
admission time and must not be hardcoded in repository documentation. It is additive engineering
integration over the frozen v11-v15 scientific request; it does not change
models, programs, evaluator, split, metrics, promotion rule, or protected-data
boundaries.

## Scope

- Phase: `A1_BASELINES_AND_MULTI_ARM_SCREENING`
- Task: `A1.2`
- Workload: five arms x five frozen programs, `25/25` common-screen cells
- Topology: `ARM-01` Owner-local CPU; `ARM-02` through `ARM-05` one GPU each
- Provider: Owner-provisioned and freshly admitted Vast instance
- Owner-approved limits: common screen `$27`, A1 `$32`, campaign `$150`, TTL 40 hours
- Scientific evidence remains closed until execution-adoption PASS

## Launch sequence

1. Verify clean pushed commit/tree and build the external v16 engineering bundle.
2. Re-read authenticated provider identity, runtime/GPU identity, fresh all-fee
   quote, whole-workload budget admission, management dry-run, watchdog/TTL,
   protected compiler receipt, and all 25 frozen bindings.
   If Vast TFA/API is unavailable, use the Owner-authorized
   `OwnerDashboardSsh` watchdog mode: bind an aggregate-safe dashboard evidence
   hash, Owner-observed all-fee rate, pinned SSH/runtime/GPU identity, and
   `OWNER_MANUAL_DASHBOARD_DESTROY_READY`. This fallback must record
   `provider_authenticated=false` and cannot invoke provider destruction.
3. Write aggregate-safe provider-admission and execution-adoption receipts.
4. Materialize an Owner-local v16 input manifest bound to the same attempt ID.
5. Start the v16 lifecycle, run `ARM-01` locally, and launch the four remote
   workers over pinned SSH with offline runtime variables.
6. Wait for all 20 remote cells, fail fast on worker failure, merge all 25
   receipts, validate checkpoints and safe return, then evaluate locally.
7. Apply only the frozen deterministic promotion rule. Do not open A2,
   HARNESS-DEV, Selection, Final, `D2_OPEN_FINAL`, or `D3_SUBMIT_RELEASE`.
8. Sync aggregate-safe evidence and reports, commit/push, tell Owner to destroy
   the admitted instance in the Vast dashboard, and verify its SSH endpoint is
   unreachable.

## Hard stops

Stop and preserve bounded evidence if any identity, hash, runtime, budget, TTL,
watchdog, protected-boundary, checkpoint, safe-return, or `25/25` requirement
drifts. Never upload protected payloads, credentials, tokens, raw provider
responses, query identifiers, rankings, or per-query outcomes to Git or
projections. A failed worker cancels/reaps its siblings and emits a failure
marker before the run is considered failed closed.

## Same-instance recovery

The Owner authorizes immediate engineering recovery on the admitted instance.
Resume the same attempt only after a transient transport or process interruption
when the frozen code, manifests, inputs, hashes, runtime, and scientific semantics
remain identical and the durable checkpoints validate. If any code byte or other
execution identity changes, close the interrupted attempt as failure evidence and
start a fresh attempt ID on the same instance after repeating admission/adoption.
Never combine cells from different attempts or repair behavior in response to an
observed retrieval outcome.

## Required evidence

The ledger and generated reports must record the attempt ID, immutable bundle
and manifest hashes, gate receipts, aggregate counts, safe-return hash, charge
and TTL observations, closeout status, Owner destruction confirmation, and the
final SSH disposition. They must not contain protected payloads or credentials.
