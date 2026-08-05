# Owner Handoff: ArmIndex Migration

This file is orientation only. Canonical authority lives in `PLAN.md`,
`control/`, versioned schemas, immutable manifests, receipts, and measured
evidence.

## Current state

- Active campaign: `armindex-multiretriever-v2`
- Active phase/task: `A1_BASELINES_AND_MULTI_ARM_SCREENING / A1.2`
- Status: `a1_2_contract_scaffold_complete_launch_locked`
- Evidence class: engineering contract scaffold; scientific authority `false`
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
- The A1.2 resource proposal is planning-only: one 24 GiB GPU (RTX 4090, RTX
  3090, L4, or A10), 8-16 GPU hours, 10-20 hours end to end, USD 2.40-12.80 raw
  GPU estimate, and hard stops of USD 5 pilot, USD 18 screen, USD 23 A1, and
  USD 100 campaign. A100/H100 is not required.
- The A1.2 offline execution scaffold is validated and receipt-bound. It adds
  `bm25s==0.3.10`, exact ARM-01 synthetic CPU rank-order parity, one versioned
  execution envelope, a hash-bound budget, five source locks, a lockset, an
  Owner-local launch checklist, a two-layer shutdown plan, an execution
  contract, and an append-only ledger. ARM-01 remains local CPU only with USD 0
  GPU budget.
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

No scaffold integrity blocker is currently known. A1.2 scientific execution
remains deliberately locked until the Owner-local runtime manifests, dense
adapter parity, Qwen measured maximum length, live quote/capacity, storage, and
external provider-termination dry run pass and the unchanged contract is
explicitly adopted. The root software license requires an Owner legal decision
before external release; this does not block preflight.

## Active authorized action

Run only the Owner-local A1.2 artifact-manifest and provider-termination dry-run
preflight on CPU. The exact next task is:

```text
/goal Run the Owner-local A1.2 artifact-manifest and external-termination dry-run preflight on CPU. Validate complete SHA256SUMS manifests for the four dense arms, freeze byte hashes for Snowflake remote code and the Qwen measured maximum length, bind a live quote and provider instance identity, and prove provider termination/TTL without exposing credentials or protected payloads. Do not reserve GPU capacity or start measured retrieval until every launch-checklist item passes and the unchanged execution contract is explicitly adopted.
```

The Owner is now needed for the next preflight: make the protected root
available read-only to the runner, pre-stage frozen model/tokenizer and
remote-code artifacts, provide complete local byte manifests, keep Vast or
equivalent credentials outside the agent workspace, bind a live quote and
instance identity, and dry-run provider termination/TTL. No GPU capacity should
be reserved until those checks pass and the unchanged contract is adopted.
