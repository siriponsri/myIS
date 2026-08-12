# A2 Per-arm AutoIndex Execution

## Scope

This runbook creates readiness evidence, an isolated staging root, and only
then permits the separately governed A2 runner to begin. It never generates or
mutates a candidate. The immutable A2 input is 40 matched candidates plus 12
dormant conditional-reserve candidates. ARM-01 and ARM-02 remain diagnostic
and non-advancing.

## Checkpoints

1. Verify the candidate manifest, freeze receipt, and lock byte hashes. Stop on
   any mismatch or any non-zero protected, candidate-evaluation, or measured
   counter.
2. Build a clean hash-bound execution bundle. The bundle may contain only
   allowlisted code, controls, schemas, hashes, and aggregate-safe pointers.
3. Collect fresh provider identity, 4x RTX 3090 runtime/model/data hashes,
   all-fee quote, whole-workload budget, management authority, and SSH evidence
   for instance 47411176. Vast CLI is preferred; `OwnerDashboardSsh` is valid
   only with pinned SSH evidence and `OWNER_MANUAL_DASHBOARD_DESTROY_READY`.
4. Require a forward all-fee hard stop no greater than USD 35 and at least
   40 hours remaining from a fresh absolute TTL deadline. The Owner-approved
   staging target is 48 hours remaining. Reject unknown fees or a partial-arm quote.
5. Create `/opt/myis/a2-<attempt-id>` only after provider admission passes,
   stage the immutable bundle, and install a new TTL/watchdog receipt. Never
   mutate or reuse an A1 remote root.
6. Write append-only lifecycle checkpoints. Resume only from the last
   hash-linked checkpoint in the same attempt. A failure cancels work and
   preserves aggregate-safe evidence.
7. Train evaluation emits aggregate-only receipts; it never measures REP-DEV.
   Winner selection rejects exact ties and cannot advance ARM-01 or ARM-02.
8. Safe return validates archive hashes and excludes protected payloads. Do not
   destroy the provider instance.

## Hard Stops

Stop before staging or execution on a hash mismatch, stale quote, price above
USD 35, TTL below 40 hours remaining, missing management authority, unexpected GPU
identity, model/data/runtime hash drift, candidate mutation, protected output,
or any request for A3, HARNESS-DEV, Selection, Final, or REP-DEV measurement.

## Ledger

Append exactly one record for each material transition to
`control/armindex/a2/execution-ledger.v1.jsonl`. The ledger is append-only;
each record binds its predecessor hash, attempt ID, freeze bindings, status,
and aggregate-safe evidence hashes.
