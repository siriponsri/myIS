# Owner Handoff: ArmIndex Migration

This file is orientation only. Canonical authority lives in `PLAN.md`,
`control/`, versioned schemas, immutable manifests, receipts, and measured
evidence.

## Current state

- Active campaign: `armindex-multiretriever-v2`
- Active phase/task: `A0_MIGRATION_FOUNDATION / A0.10`
- Status: `legacy_code_harvest_and_phase_scaffolding_complete`
- Evidence class: engineering migration; scientific authority `false`
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
- Final closeout passed 377 tests, Ruff, layout, assets, policy scans, session
  audit, ArmIndex validation and disposable fixture, MLflow doctor, Brain
  literature validation, deterministic report sync/check, and whitespace checks.

## Boundaries

No measured retrieval, REP-DEV/HARNESS-DEV optimization, Selection, Final,
GPU scientific execution, paid API, model download, provider switch, or model
weight modification is authorized during this migration. Protected Owner-local
data remains untouched.

## Blockers

No integrity or evidence blocker is currently known. The root software license
requires an Owner legal decision before external release; this does not block
the engineering migration.

## Active authorized action

Begin the synthetic-only A0.8 compute and storage feasibility fixtures. A1
remains locked until A0.9 validation and closeout. The exact next task is:

```text
/goal Execute A0.8_COMPUTE_AND_STORAGE_FEASIBILITY_FIXTURES from the canonical PLAN and control/campaigns/armindex-multiretriever-v2.yaml. Use synthetic fixtures only; do not access protected data, start measured retrieval, download model weights, use GPU or paid APIs, open Selection, or open Final.
```
