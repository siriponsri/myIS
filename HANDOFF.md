# Owner Handoff: ArmIndex Migration

This file is orientation only. Canonical authority lives in `PLAN.md`,
`control/`, versioned schemas, immutable manifests, receipts, and measured
evidence.

## Current state

- Active campaign: `armindex-multiretriever-v2`
- Active phase/task: `A1_BASELINES_AND_MULTI_ARM_SCREENING / A1.1`
- Status: `a0_complete_a1_fixture_ready`
- Evidence class: engineering validation and scaffolding; scientific authority `false`
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

## Boundaries

No measured retrieval, REP-DEV/HARNESS-DEV optimization, dense-arm execution,
Selection, Final, GPU scientific execution, paid API, model download, provider
switch, or model-weight modification is authorized by the A0 closeout or A1.1
fixture handoff. Protected Owner-local data remains untouched.

## Blockers

No integrity or evidence blocker is currently known. The root software license
requires an Owner legal decision before external release; this does not block
the engineering migration.

## Active authorized action

Begin only the synthetic/offline A1.1 adapter-fixture scaffold on CPU. A1.2 and
all measured screening remain locked pending a separate A1 execution contract.
The exact next task is:

```text
/goal Execute A1.1_ADAPTER_FIXTURE_VALIDATION from the canonical PLAN and control/campaigns/armindex-multiretriever-v2.yaml. Build and validate only synthetic/offline adapter fixtures on CPU. Do not access protected data, start measured retrieval, download model weights, use GPU or paid APIs, switch providers, open Selection, or open Final. Keep A1 measured screening closed until a separate execution contract authorizes it.
```
