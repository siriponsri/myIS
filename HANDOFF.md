# Owner Handoff: ArmIndex Migration

This file is orientation only. Canonical authority lives in `PLAN.md`,
`control/`, versioned schemas, immutable manifests, receipts, and measured
evidence.

## Current state

- Active campaign: `armindex-multiretriever-v2`
- Active phase/task: `A1_BASELINES_AND_MULTI_ARM_SCREENING / A1.2`
- Status: `a1_2_live_synthetic_preflight_pass_owner_disposition_pending_launch_locked`
- Evidence class: live engineering synthetic preflight; scientific authority `false`
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
- The first clean post-commit v2 validation then exposed a bounded validator
  defect: it regenerated an expected input from the new `HEAD/tree` instead of
  treating the frozen v2 preparation commit/tree as provenance. All v1/v2
  bytes and receipt hashes remained valid. Additive revision
  `a1.2-local-vast-4x3090-postcommit-v3` validates v2 through its immutable
  receipt and captures the clean current commit/tree when the bundle is built.
  The v3 correction receipt self-hash is
  `75379b2f33b85549036135cf6c7cc1b06c479b6fe5a1643c08a88501fefdc8ca`;
  launch, adoption, measured, GPU, paid, Selection, and Final counters remain
  locked or zero.
- The first report check after the projection-only closeout commit exposed a
  second bounded defect: runtime validator commit/tree values changed generated
  A1.2 state after every evidence-neutral commit. Repair commit `4b5194e`
  preserves clean-tree validation output while excluding those volatile values
  from the shared read model. The two-identity regression passed, and the repair
  is recorded in
  `outputs/audits/rigor/a1.2-v3-projection-stability-repair-20260806.json`.
- Additive v5 changes only the active runtime path: the official
  `pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime` linux/amd64 manifest is bound
  to `sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20`.
  Vast starts that image directly; custom image build/save/upload/load and
  nested-container execution are removed from the active path. The v4
  runtime-minimal model policy remains the source for exact model allowlists,
  with no runtime model download.
- Public revisions and critical artifact commitments are frozen for BGE-M3,
  PatEmbed-large, Snowflake Arctic Embed M v2.0, and Qwen3-Embedding-0.6B. The
  Owner-local v5 stage passed all 48 allowlisted runtime files across four
  dense arms, Snowflake custom-code hashes, the Linux wheelhouse, safe jobs,
  transfer checksums, and return readiness. Model bytes remain outside Git.
- The live container exposed linux/amd64, Python 3.11.11, PyTorch 2.6.0+cu118,
  CUDA 11.8, and four RTX 3090 devices. No dense model load or measured run
  began. v6 stopped first on a missing `pydantic` dependency and then on a
  frozen-tree `__pycache__` mutation. Both failed attempts remain preserved.
- Additive v7 uses a fresh `/opt/myis/a1.2-v7` root on the same unchanged
  instance, requires `PYTHONDONTWRITEBYTECODE=1`, revalidates staged bytes, and
  uploads only the new clean frozen code bundle.
- The v7 verifier then failed closed before model or GPU work because that
  bundle omitted the historical v1 receipt required by the transitive v5 to v1
  validator chain. Additive v8 preserves the v7 root, uses a fresh
  `/opt/myis/a1.2-v8` root, adds the exact repository-safe validation lineage,
  validates frozen Git metadata without a `.git` directory, and requires a
  commit/tree/bundle/image-bound PASS marker before synthetic workers can start.
- Independent lifecycle review then blocked v8 start because worker failure,
  checkpoint, Qwen adapter-path, status, collection, and teardown semantics were
  not strong enough for auditable live evidence. Additive v9 preserves v1-v8,
  uses fresh `/opt/myis/a1.2-v9`, reuses only checksum-validated v7 staged
  bytes, and binds immutable attempt IDs, PID/start-time liveness, fresh
  heartbeats, immediate sibling cancellation/reaping, durable checkpoints,
  adapter-level Qwen length measurement, same-attempt PASS export, member-hash
  validation, and verified guest-process cleanup.
- Attempt `a12-v9-20260807-06` passed ARM-02 through ARM-05 synthetic adapter
  parity, Qwen adapter-level 32,768-token measurement, checkpoint/resume,
  expected-failure handling, 72-member safe export validation, and guest-process
  teardown. The aggregate-only canonical result receipt is
  `campaigns/armindex-multiretriever-v2/evidence/a1.2-live-synthetic-preflight-result.receipt.v9.json`.
- Every registered Phase and Task continues to receive one detailed English
  generated Obsidian report with the canonical fifteen-section structure. The
  archive audit found zero eligible orphan/superseded reports; referenced
  historical SCOPE/P1/P2 reports remain active evidence lineage.

## Boundaries

No measured retrieval, REP-DEV/HARNESS-DEV optimization, measured dense-arm execution,
Selection, Final, GPU scientific execution, paid API, model download, provider
switch, or model-weight modification is authorized by the A0 closeout or A1.1
fixture handoff. Protected Owner-local data remains untouched.

## Blockers

The v1-v9 receipt lineage, v5 local stage, live runtime identity, four dense
adapter checks, Qwen 32,768-token adapter measurement, checkpoint/resume, safe
return, and guest teardown pass. A1.2 scientific execution remains deliberately
locked because no execution revision has been adopted and no measured retrieval
goal is authorized. Provider destruction/TTL proof or a policy-valid Owner
continuation decision remains pending. The root software license requires an
Owner legal decision before external release; this does not invalidate the
engineering preflight.

## Active authorized action

Choose the post-preflight instance disposition. The exact next task is:

```text
/goal Decide the A1.2 post-preflight Vast instance disposition. Default to destroy and verify provider absence, or explicitly authorize continue_next_goal_on_PLAN only for a separately authorized next PLAN goal while the same instance identity, artifact hashes, quote/budget, TTL/destroy path, and protected-data boundary remain valid. Keep launch_allowed=false and adopted_for_execution=false; do not start measured retrieval, optimization, Selection, Final, paid API work, or weight changes.
```

The synthetic preflight and safe collection are complete. The default is to
destroy and verify the provider instance. The additive Owner
policy at `control/armindex/a1.2/owner-instance-continuation-policy.v1.json`
permits the report `Owner continue next goal on PLAN` only after a complete
live PASS and a separately authorized next PLAN goal, while the same instance
identity, artifact hashes, quote/budget, TTL/destroy path, and protected-data
boundary remain valid. Access material and every protected surface remain
local. Reuse does not adopt the revision or authorize measured retrieval,
optimization, Selection, Final, paid API work, or weight changes.
