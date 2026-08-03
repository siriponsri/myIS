# P2 Measured Autoresearch v2 Runbook

## Authority and boundary

This tracked runbook is the durable execution plan for campaign revision
`scope-autoindex-v1-p2-r1-primary-v2`. It does not authorize a measured run.
The next authorized action remains `Owner-local P2 measured preflight`.

The v2 runtime is CPU-only, zero paid API, no GPU, no network model download,
and no provider fallback. Final-872, qrels, membership, query IDs, rankings,
per-query outcomes, credentials, protected prompts, and raw provider payloads
remain in the Owner-local protected store. D2 and D3 remain closed.

## Frozen bindings

- Budget: `control/budgets/p2-r1-primary-v2.yaml`
- Envelope: `control/execution-envelope-p2-v2.yaml`
- Revision: `control/campaigns/scope-autoindex-p2-r1-primary-v2.yaml`
- Candidate ceiling: 32 total, including 4 controls, 8 preregistered, and at
  most 20 adaptive candidates in complete four-candidate batches.
- Runtime: 432000 wall seconds, 345600 measurement seconds, 86400 overhead
  reserve, and 10800 seconds per candidate.
- Selection: strict-greater improvement, exact ties rejected, one exposure,
  and no exposure before an immutable validated shortlist-freeze receipt.

A measured request must bind the profile and envelope IDs and hashes, Git
commit and tree, base candidates, adaptive policy, proposer contract, input
hashes, scope hashes, frozen provider/model/revision/effort, and zero global
selection counters. Missing limits are never inferred.

## Owner-local preflight handoff

The next session starts with the repository preflight only:

```powershell
myis-p2 preflight --request <owner-local-preflight-request.json> --repository-root . --require-stores
```

Run it from a clean worktree at the exact commit and tree bound by the request.
Any non-passing result stops the workflow. A passing preflight is necessary but
does not make this runbook a measured-run authorization.

## Runtime commands

```powershell
myis-p2-measured start --request <owner-local-request.json> --run-root <owner-local-run-root> --owner-store <owner-local-store> --cache-root <owner-local-cache>
myis-p2-measured status --run-root <owner-local-run-root>
myis-p2-measured verify --run-root <owner-local-run-root> --request <owner-local-request.json> --repository-root . --owner-store <owner-local-store>
myis-p2-measured stop-after-checkpoint --run-root <owner-local-run-root>
myis-p2-measured resume --request <owner-local-request.json> --run-root <owner-local-run-root> --owner-store <owner-local-store> --cache-root <owner-local-cache>
```

`start` launches a detached worker, redirects stdout and stderr beneath the
Owner-local run root, waits for a startup receipt, and keeps a Windows
execution-state handle active so the machine does not sleep during work.
Closing Codex or the parent terminal must not terminate the worker. A reboot
requires `resume`.

Start measured preflight from a fresh Owner-controlled shell with only the
environment needed by the runtime. Do not dump or archive the inherited
environment. Any credential that may have been present in a prior inherited
shell must be rotated by the Owner before preflight; the repair does not inspect
or rotate credentials. Detached worker, candidate, and proposer subprocesses
receive explicit allowlisted environments and never receive `MYIS_STORE`,
MLflow store paths, or credential-like variables.

## Durable authority

The OS advisory lock held by the worker handle is the single-writer authority.
The stable lock file is never interpreted by existence alone. Mutable lease
metadata records process creation identity and heartbeat for observation, but
it cannot override the OS lock.

Every material transition is written first as an immutable canonical JSON
event with sequence, previous event hash, event hash, and idempotency key.
`state.json` is a rebuildable snapshot. Resume fails closed if the request,
Git identity, profile, envelope, journal chain, active child, partial index,
accepted-result set, counters, or freeze state disagree.

## Stage order and checkpoints

1. Validate request and immutable bindings; acquire the advisory lock.
2. Commit the P1 baseline reference before any train outcome.
3. Reproduce the baseline. Failure stops before selection.
4. Register and evaluate accepted base candidates. Accepted results are never
   rerun; full replay determinism runs inside the candidate timeout and does
   not create a second scientific outcome.
5. Before each adaptive batch, admit all four candidates only when remaining
   measurement time can cover four complete candidate timeouts.
6. Invoke the proposer with aggregate-safe feedback. Two identical attempts
   are allowed. If both fail schema or single-axis validation, record
   `awaiting_proposer_recovery` before any batch receipt or measurement.
7. Quarantine incomplete index directories. Retry only infrastructure
   failures within the frozen budget; scientific failures are retained.
8. Freeze the deterministic shortlist and all required hashes before opening
   selection. A compare-and-swap counter permits only one writer.
9. Write aggregate-safe closeout and regenerate every projection from one
   validated read model.

Valid stopping reasons are wall-clock exhaustion, the development impact
gate, no grounded hypotheses, and an Owner stop requested at a checkpoint.
Budget changes after the first measured run require another campaign revision
and cannot reinterpret v1 or v2 results.

## Hybrid Codex proposer

The proposer uses `codex exec --ephemeral --sandbox read-only --output-schema`
with a minimal allowlisted environment. `MYIS_STORE`, MLflow store paths,
credential-like variables, rankings, qrels, membership, query IDs, and raw
text are removed. Provider, model, revision, effort, prompt, schema, seed, Git
commit, and request hash are frozen at preflight. There is no fallback.

## Recovery and reporting

A failed or interrupted attempt remains in the hash-chained journal and the
generated Phase/Task failure-recovery chain. Live status and run reports expose
only aggregate-safe stage, counts, elapsed time, hashes, and pointers. They do
not become scientific authority until canonical measured receipts validate.

Before commit or push, run focused runtime tests, full pytest, scoped Ruff,
report schema/content validation, two deterministic sync/check cycles,
artifact graph/checksum validation, protected and unsafe-path scans, session
audit, Dashboard/API tests, repository-safe MLflow doctor, layout/assets,
Brain literature validation, clean-checkout regression, and
`git diff --check`.
