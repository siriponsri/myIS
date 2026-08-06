# A1.2 Local-Orchestrated Vast 4xRTX3090 Preflight Revision

## Identity

- Campaign: `armindex-multiretriever-v2`
- Phase: `A1_BASELINES_AND_MULTI_ARM_SCREENING`
- Task: `A1.2`
- Revision: `a1.2-local-vast-4x3090-v2`
- Evidence class: engineering preflight scaffold
- Scientific authority: `false`
- Adoption state: `adopted_for_execution=false`
- Launch state: `launch_allowed=false`

This additive revision prepares and validates a local-orchestrated four-GPU
preflight. It does not alter or supersede any A1.2 v1 file. The v1 one-GPU
sequential contract remains immutable historical evidence and is explicitly
not adopted.

## Authorized Scope

The authorized work is local, offline, synthetic, and zero-cost. It may create
and test contracts, a locked container definition, SSH command composition,
remote bootstrap logic, four isolated synthetic workers, safe-export rules,
receipts, local projection inputs, and an Owner runbook. It may not reserve a
Vast instance, contact a paid worker, download model payloads, start measured
retrieval, run REP-DEV or HARNESS-DEV optimization, expose Selection or Final,
use a paid API, or modify model weights.

All measured and resource counters remain zero. A synthetic four-worker test
uses local temporary directories and simulated GPU UUIDs; it is not GPU
execution and has no retrieval-quality authority.

## Topology

Codex runs locally in VS Code and is the only writer to Git, canonical control,
receipts, MLflow, Brain, generated Obsidian, Dashboard, and Paper readiness.
`ARM-01` runs on local CPU. One future disposable Vast SSH worker exposes four
RTX 3090 GPUs: `ARM-02` uses device 0, `ARM-03` device 1, `ARM-04` device 2,
and `ARM-05` device 3. Each launcher fixes `CUDA_VISIBLE_DEVICES` to one device
and requires the runtime to observe exactly one GPU.

Owner access material, evaluation truth, split membership, protected evaluator,
canonical MLflow writes, and OpenAI access remain local. The worker may receive
only frozen code or image bytes, frozen model artifacts, aggregate-safe
retrieval inputs, immutable job manifests, and declared safe output paths.

## Immutable Bindings

The v2 migration receipt binds the exact Git commit and tree used to prepare
the bundle, every preserved v1 file by raw SHA-256, the v2 envelope, budget,
topology contract, runtime lock, launch checklist, shutdown contract, safe
export allowlist, coordinator, bootstrap, launcher, watchdog, tests, and this
runbook. A later live preflight must bind the unchanged v2 revision and a built
image digest; a Dockerfile or tag alone is insufficient.

The live preflight must fail closed unless the quote fits all unchanged hard
stops: USD 18 for the common screen, USD 23 for A1, and USD 100 for the
campaign. A quote outside any remaining ceiling produces `BLOCKED_BUDGET`.
The Owner-supplied planning rate is USD 0.60 per hour for the complete
four-RTX3090 instance, not per GPU. Parallel dense preparation is estimated at
2-4 instance-hours, or USD 1.20-2.40 raw worker cost, plus 2-4 local hours for
upload, verification, collection, evaluation handoff, and closeout. The USD 18
common-screen ceiling would admit at most 30 hours at that rate, but the live
quote and the remaining budget at launch time remain authoritative.

## Preparation Sequence

1. Validate all v1 bindings and record their raw hashes without changing them.
2. Materialize v2 contract records and immutable per-arm synthetic jobs.
3. Validate the locked container definition and require an externally supplied
   OCI image digest for live preflight.
4. Exercise upload, verify, start, status, collect, and teardown command paths
   against a local synthetic transport only.
5. Exercise four workers concurrently with fixed device assignments, isolated
   outputs, heartbeat, checkpoint, resume, runtime receipts, failure receipts,
   and safe-export enforcement.
6. Exercise the Owner-local TTL watcher and provider-destroy dry-run adapter.
   Guest poweroff is only a worker request and never proof of provider removal.
7. Emit the canonical preparation and migration receipt before projection.
8. Build one validated shared read model and project the same object to every
   additive sink.

## Live Preflight Acceptance

The future Owner-local SSH/Vast preflight must verify:

- exact Git commit and tree, plus the built OCI image digest;
- four distinct RTX 3090 GPU UUIDs and fixed per-arm device mapping;
- CUDA driver/runtime and PyTorch CUDA compatibility;
- declared CPU, RAM, and free disk minimums;
- complete `SHA256SUMS` coverage for every runtime model/tokenizer file;
- byte hashes of the frozen Snowflake remote-code files;
- dense-adapter parity and the frozen Qwen measured maximum length;
- a read-only protected root that is never uploaded;
- absence of evaluation truth, access material, membership, and protected
  payloads from the remote manifest and remote filesystem scope;
- a writable local return path with sufficient free space;
- provider identity and a time-bounded live quote inside all budget ceilings;
- fresh heartbeat and checkpoint/resume behavior;
- Owner-local provider destroy and TTL dry-run evidence.

Passing these checks still leaves `launch_allowed=false` and
`adopted_for_execution=false`. A later Owner adoption must bind the unchanged
revision before any scientific launch can be requested.

## Failure and Recovery

Contract drift, hash mismatch, unexpected remote path, unsafe export, ambiguous
GPU identity, incomplete manifest, stale heartbeat, insufficient storage,
failed destroy dry run, or missing provider identity stops the preflight.
Budget overflow has the terminal status `BLOCKED_BUDGET`. Failures create
aggregate-safe receipts and checkpoints; they never trigger fallback to another
provider or unpinned artifact.

## Owner Handoff

The Owner runbook gives exact PowerShell commands using explicit parameters.
It never embeds access material. Before opening Vast, the Owner stages complete
model manifests and records a current four-RTX3090 quote. After opening the
instance, the Owner supplies host, port, user, key path, provider instance ID,
quote metadata, image digest, artifact roots, and return path only to the local
coordinator. The coordinator keeps those values outside canonical artifacts and
exports only sanitized receipts.

## Close Condition

This preparation goal closes when the v2 files, synthetic orchestration proof,
canonical receipt, memory pointers, reports, and projections validate and are
committed and pushed. A live Vast preflight is deliberately the next Owner
action and is not claimed as complete in this revision.
