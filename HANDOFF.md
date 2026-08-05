# Owner Handoff: ArmIndex Migration

This file is orientation only. Canonical authority lives in `PLAN.md`,
`control/`, versioned schemas, immutable manifests, receipts, and measured
evidence.

## Current state

- Active campaign: `armindex-multiretriever-v2`
- Active phase/task: `A1_BASELINES_AND_MULTI_ARM_SCREENING / A1.2`
- Status: `a1_1_complete_a1_2_contract_locked`
- Evidence class: engineering fixture and resource planning; scientific authority `false`
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

## Boundaries

No measured retrieval, REP-DEV/HARNESS-DEV optimization, dense-arm execution,
Selection, Final, GPU scientific execution, paid API, model download, provider
switch, or model-weight modification is authorized by the A0 closeout or A1.1
fixture handoff. Protected Owner-local data remains untouched.

## Blockers

No integrity or evidence blocker is currently known. A1.2 execution remains
deliberately locked until its versioned execution contract and hash-bound budget
profile validate. The root software license requires an Owner legal decision
before external release; this does not block contract scaffolding.

## Active authorized action

Prepare only the A1.2 offline execution-contract scaffold. This must be complete
before any real GPU reservation or measured run. The exact next task is:

```text
/goal Prepare and validate the versioned A1.2_COMMON_MULTI_ARM_SCREENING execution contract, hash-bound budget profile, frozen offline model and adapter locks, Owner-local launch checklist, and automatic shutdown plan from the validated A1.1 engineering receipt. Complete this scaffold before reserving GPU capacity. Do not launch measured retrieval, access protected payloads from the agent workspace, download model weights during measured runtime, use paid APIs, switch providers, open Selection, or open Final until the separate contract is adopted and validated.
```

No Owner action is needed to write and validate the scaffold. Before a real
launch, the Owner must make the protected root available to the runner,
pre-stage frozen model/tokenizer and required remote-code artifacts, provide
Vast or equivalent credit and credentials without exposing them to agents, and
intervene only for provider unavailability, hash conflict, or budget increase.
