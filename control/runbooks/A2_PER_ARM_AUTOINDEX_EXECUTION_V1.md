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
6. Launch with `control/armindex/a2/measured-command-argv.v1.json` and the
   hash-bound Owner-local input manifest. Execute and durably receipt exactly
   the 40 matched candidates first. Resume never reruns a durable receipt.
7. At the matched barrier, stop with
   `MATCHED_COMPLETE_RESERVE_ADMISSION_REQUIRED` until a fresh admission still
   proves at least 40 hours remaining and the unchanged USD 35 hard stop.
8. Derive the three primary-arm decisions from the frozen batch order,
   Owner-local A1 v16 incumbents, strict primary improvement, and the actual
   four frozen reserve axes. Persist one decision and one continuation receipt.
   Each reserve arm is then either four active results or four dormant receipts.
9. Evaluation measures the frozen REP-DEV view and emits aggregate-only receipts;
   query IDs, qrels, membership, rankings, and per-query outcomes remain Owner-local.
   Winner selection rejects exact ties and cannot advance ARM-01 or ARM-02.
10. Safe return validates archive hashes and excludes protected payloads. Do not
   destroy the provider instance.

## Measured Commands

The Owner-local manifest must validate against
`schemas/armindex/a2-owner-local-measured-input.v1.json`, bind the A1 v16
runtime/model/data/evaluator artifacts, protected corpus/query/qrels/membership
files by Owner-local relative path and SHA-256, the four staged dense-model
directories, the engine source hash, and the A1 incumbent candidate, program
hash, and aggregate primary metric for ARM-03, ARM-05, and ARM-04. The tracked
command contract invokes the repository-owned production engine; fixture or
caller-selected engine commands fail closed.

```powershell
uv run --no-sync python -m myis_research.armindex.a2_operational_executor --repository-root . --attempt-id <attempt> execute --execution-adoption-receipt <owner-local-adoption.json> --measurement-authority <tracked-authority.json> --command-argv-json control/armindex/a2/measured-command-argv.v1.json --owner-root <owner-local-root> --owner-input-manifest <owner-local-root/input.json> --output-directory <owner-local-output> --checkpoint-ledger <owner-local-ledger.jsonl>
```

The first call ends at the matched barrier. After AP/LO creates the fresh
reserve-budget admission from a new provider observation and its exact source
artifacts, rerun the same command with
`--reserve-budget-admission <owner-local-reserve-admission.json>`. Attempt,
adoption, authority, freeze, matched receipt-set, decision, and continuation
identities must remain unchanged.

```powershell
uv run --no-sync python -m myis_research.armindex.a2_operational_executor --repository-root . --attempt-id <attempt> reserve-admit --execution-adoption-receipt <owner-local-adoption.json> --measurement-authority <tracked-authority.json> --provider-observation <fresh-provider-observation.json> --runtime-source <runtime-source-artifact> --model-lockset-source <model-lockset-source-artifact> --data-handoff-source <data-handoff-source-artifact> --ssh-host-key-source <ssh-host-key-source-artifact> --management-authority-source <management-authority-source-artifact> --output <owner-local-reserve-admission.json>
```

## Hard Stops

Stop before staging or execution on a hash mismatch, stale quote, price above
USD 35, TTL below 40 hours remaining, missing management authority, unexpected GPU
identity, model/data/runtime hash drift, candidate mutation, protected output,
or any request for A3, HARNESS-DEV, Selection, or Final access.

## Ledger

Append exactly one record for each material transition to
`control/armindex/a2/execution-ledger.v1.jsonl`. The ledger is append-only;
each record binds its predecessor hash, attempt ID, freeze bindings, status,
and aggregate-safe evidence hashes.
