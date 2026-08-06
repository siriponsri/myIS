# Owner Handoff: ArmIndex Migration

This file is orientation only. Canonical authority lives in `PLAN.md`,
`control/`, versioned schemas, immutable manifests, receipts, and measured
evidence.

## Current state

- Active campaign: `armindex-multiretriever-v2`
- Active phase/task: `A1_BASELINES_AND_MULTI_ARM_SCREENING / A1.2`
- Status: `a1_2_vast_4x3090_preflight_prepared_launch_locked`
- Evidence class: engineering preflight scaffold; scientific authority `false`
- ArmIndex measured runs: `0`
- Selection exposures: `0`
- Final exposures: `0`
- Migration cost: `$0`
- Final-872: closed
- Owner gates: `D2_OPEN_FINAL`, `D3_SUBMIT_RELEASE`

## Done

- The pre-migration `main` commit and tree were recorded.
- Remote rollback branch `archive/pre-armindex-migration-20260804` was created.
- All six inbox authority/proposal inputs were read and SHA-256 recorded.
- ArmIndex control, plan, model, AutoIndex/HarnessOpt, and migration contracts were adopted.
- Historical SCOPE/P1/P2 paths remain preserved and readable.
- Shared read-model, Brain, Obsidian, Dashboard, Paper, and MLflow projections were migrated.
- Professional documentation, schemas, contracts, safety scans, and repository-wide tests passed.
- The six adopted inbox sources were hash-verified and archived under `inbox/archive/armindex-migration-20260804/`.
- The A0.10 myIS/ThaiPha-Lex harvest ledger, typed contracts, five-arm registry,
  synthetic ARM-01 slice, AutoIndex/HarnessOpt fixtures, CLI, and receipt-first
  projection hooks were completed and tested.
- The retired `output/` root was merged byte-for-byte into canonical `outputs/`;
  exact duplicates were audited, no tracked source duplicate was safe to delete,
  and verified ignored caches were removed with an aggregate-safe hygiene receipt.
- Independent rigor review first returned `REVISE`, then `ACCEPT` after the exact
  A0.8 handoff was unified, all 14 ThaiPha-Lex source commitments were verified
  from pinned Git blobs, and one sync receipt bound the A0.10 source receipt to
  MLflow, read model, Brain, Obsidian, Dashboard, and Paper projections.
- A0.8 completed the bounded synthetic CPU compute/storage fixture with a
  validated manifest, receipt, task receipt, and hash-chained ledger; the App
  sparse indexes remained protected reference-only and their payload was not opened.
- A0.9 validated the complete A0 control, fixture, projection, asset, Dashboard,
  MLflow, session, policy, layout, test, and safety matrix and emitted
  `campaigns/armindex-multiretriever-v2/evidence/a0-phase-closeout.receipt.v1.json`.
- All Tasks A0.1 through A0.10 and Phase A0 are complete. Two deterministic
  report sync/check cycles are byte-stable and every projection sink is bound to
  the A0 closeout receipt.
- Final post-closeout verification passed 388 tests, scoped Ruff, report drift,
  assets, layout, Dashboard/API and policy checks, session audit, repository-safe
  MLflow doctor, Brain literature validation, and whitespace validation. The
  required pointer-only Brain note was committed under a validated writer lease.
- A1.1 completed the five-arm synthetic adapter fixture and ARM-01 CPU
  compile-index-search-evaluate path. The write-once manifest, receipt,
  hash-chained ledger, and task receipt validate one runnable CPU fixture arm,
  four fail-closed dense arms, and zero measured or charged-resource counters.
- A1.1 adopted detailed English reporting for every registered Phase and Task
  using the fifteen-section machine/Markdown contract. The archive audit found
  no unused generated report: current and historical reports remain referenced
  by the generated manifest, validators, or artifact graph, so no report moved.
- The preserved A1.2 v1 resource proposal is planning-only: one 24 GiB GPU (RTX 4090, RTX
  3090, L4, or A10), 8-16 GPU hours, 10-20 hours end to end, USD 2.40-12.80 raw
  GPU estimate, and hard stops of USD 5 pilot, USD 18 screen, USD 23 A1, and
  USD 100 campaign. A100/H100 is not required. This v1 proposal is historical,
  unchanged, unadopted evidence.
- The A1.2 offline execution scaffold is validated and receipt-bound. It adds
  `bm25s==0.3.10`, exact ARM-01 synthetic CPU rank-order parity, one versioned
  execution envelope, a hash-bound budget, five source locks, a lockset, an
  Owner-local launch checklist, a two-layer shutdown plan, an execution
  contract, and an append-only ledger. ARM-01 remains local CPU only with USD 0
  GPU budget.
- The CPU-only Owner-local preflight runner was implemented and executed. Canonical
  contract bindings passed; the aggregate-safe receipt is
  `blocked_owner_input` because the four dense-arm manifests, Snowflake remote-code
  byte hashes, Qwen measured maximum length, dense parity, storage, live quote/provider
  identity, and termination/TTL evidence are not present in the workspace.
- The preflight result has a scanner-safe MLflow projection and registration script.
  MLflow is allowed to receive only hashes, counts, status, and safe pointers; the
  canonical receipt remains the source of truth and no protected or sensitive bytes
  are mirrored.
- The additive `a1.2-local-vast-4x3090-v2` revision is prepared and validated
  offline. Codex remains local and is the only canonical writer; `ARM-01` stays
  on local CPU, while `ARM-02` through `ARM-05` are fixed to four RTX 3090 GPUs
  in parallel on one disposable Vast SSH worker.
- The synthetic four-worker orchestration passed `4/4` workers with zero
  failures, no GPU use, no paid compute, and no measured retrieval. Its receipt
  self-hash is `4c8e22e76308178bfe5909fea434b7db06f3b80f6f6615f3f5f74ccec598a6c7`.
  The v2 migration receipt self-hash is
  `869b6feac387c069f3f53ec49cc3ebf42159cf750d3e23acb0d57ead622ca600`.
- The Owner planning rate is USD 0.60 per hour for the complete four-RTX3090
  instance. The estimate is 2-4 instance-hours, or USD 1.20-2.40 raw worker
  cost, plus 2-4 local hours. Hard stops remain USD 18 for the common screen,
  USD 23 for A1, and USD 100 for the campaign; the live quote must fit or the
  preflight stops `BLOCKED_BUDGET`.
- The A1.2 v2 closeout audit passed 18 validation groups: 428 full-suite
  tests, 19 focused A1.2 tests, 21 safety/report/session tests, 21 Dashboard/API
  tests, 16 MLflow doctor checks, 154 Brain literature notes, 5 registered
  assets, 28 Markdown link files, two PowerShell scripts with zero parse errors,
  and two byte-stable final report sync/check cycles. The audit self-hash is
  `fe2e2b48324e18d7de1a50413831462f942222a11cfdf4bda9f53a35421a2646`.
- Public revisions and critical artifact commitments are frozen for BGE-M3,
  PatEmbed-large, Snowflake Arctic Embed M v2.0, and Qwen3-Embedding-0.6B. No
  model payload was downloaded. The four dense locks remain
  `metadata_frozen_owner_artifacts_pending`; complete Owner-local byte-level
  `SHA256SUMS` manifests are required before launch.
- Every registered Phase and Task continues to receive one detailed English
  generated Obsidian report with the canonical fifteen-section structure. The
  archive audit found zero eligible orphan/superseded reports; referenced
  historical SCOPE/P1/P2 reports remain active evidence lineage.

## Boundaries

No measured retrieval, REP-DEV/HARNESS-DEV optimization, dense-arm execution,
Selection, Final, GPU scientific execution, paid API, model download, provider
switch, or model-weight modification is authorized by the A0 closeout or A1.1
fixture handoff. Protected Owner-local data remains untouched.

## Blockers

The v1 and v2 integrity checks pass. A1.2 scientific execution remains
deliberately locked because the live Owner preflight has not bound the exact
commit/tree/image digest, four GPU UUIDs, runtime/model manifests, dense adapter
parity, Qwen measured maximum length, live quote/identity, storage, heartbeat/
resume, and provider-destruction proof. The root
software license requires an Owner legal decision before external release; this
does not block the CPU preflight.

## Active authorized action

Run only the Owner-local SSH/Vast A1.2 preflight from the immutable beginner
runbook. The exact next task is:

```text
/goal Run only the Owner-local SSH/Vast A1.2 preflight from docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK.md on one disposable four-RTX3090 instance. Verify the unchanged v2 commit, tree, image digest, four GPU UUIDs, locked runtime and model bytes, adapter parity, Qwen maximum length, local protected-root boundary, live USD quote, heartbeat/resume, safe return path, and provider destroy/TTL path. Keep launch_allowed=false and adopted_for_execution=false; do not start measured retrieval, optimization, Selection, Final, paid API work, or weight changes.
```

The Owner is now needed to follow
`docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK.md`: stage frozen artifacts and
complete `SHA256SUMS` files outside Git, build and bind the OCI image digest,
confirm a live quote, open one matching four-RTX3090 instance, run the exact
local coordinator/watchdog commands, collect only allowlisted outputs, and
destroy and verify the provider instance. Access material and every protected
surface remain local. Passing the preflight still does not adopt the revision
or authorize scientific execution.
