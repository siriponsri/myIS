# Owner Handoff: ArmIndex Migration

This file is orientation only. Canonical authority lives in `PLAN.md`,
`control/`, versioned schemas, immutable manifests, receipts, and measured
evidence.

## Current state

- Active campaign: `armindex-multiretriever-v2`
- Active phase/task: `A0_MIGRATION_FOUNDATION / A0.4`
- Status: `migration_complete; synthetic_fixture_preflight_ready`
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

## Boundaries

No measured retrieval, REP-DEV/HARNESS-DEV optimization, Selection, Final,
GPU scientific execution, paid API, model download, provider switch, or model
weight modification is authorized during this migration. Protected Owner-local
data remains untouched.

## Blockers

No integrity or evidence blocker is currently known. The root software license
requires an Owner legal decision before external release; this does not block
the engineering migration.

## Next authorized action

Run the synthetic-only A0 compute-feasibility fixtures and preflight. The exact
next command is:

```text
/goal Execute ArmIndex A0 compute-feasibility fixtures and preflight from the canonical PLAN and control/campaigns/armindex-multiretriever-v2.yaml. Use synthetic fixtures only; do not start measured retrieval, download model weights, open Selection, or open Final.
```
