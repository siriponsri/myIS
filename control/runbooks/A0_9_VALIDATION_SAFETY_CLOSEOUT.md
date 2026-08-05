# A0.9 Validation, Safety, and Closeout

## Authority

- Phase: `A0_MIGRATION_FOUNDATION`
- Task: `A0.9`
- Campaign: `control/campaigns/armindex-multiretriever-v2.yaml`
- Standing authorization: `D1_START_CAMPAIGN`
- Evidence class: `engineering_validation`
- Scientific authority: `false`

## Objective

Validate every A0 control, fixture, projection, and safety boundary; close
Task A0.9 and Phase A0 only when the repository agrees everywhere. This task
does not open A1 measured execution or any Owner-only gate.

## Frozen Boundary

- CPU-only validation with zero paid API and no network model download.
- No protected corpus/evaluator payload, qrels, membership, query IDs,
  rankings, per-query outcomes, provider payload, or credentials.
- No measured retrieval, GPU, Selection, Final, D2, D3, provider switch, or
  model-weight mutation.
- Historical SCOPE/P1/P2 evidence remains readable and immutable.
- App sparse indexes remain protected A1 reference assets and are not opened.

## Required Checks

1. Validate A0.8 manifest, receipt, task receipt, ledger chain, and all-zero
   counters.
2. Validate ArmIndex campaign, schemas, typed contracts, CLI, and disposable
   fixtures.
3. Run full pytest and scoped Ruff.
4. Validate report schema/content and run two deterministic sync/check cycles.
5. Validate artifact graph/checksums, protected and unsafe paths, session
   capsules, Dashboard/API, repository-safe MLflow, layout, and assets.
6. Acquire the Brain serial-writer lease, update one pointer-only A0 closeout
   note, validate literature, and release the lease after the Brain commit.
7. Run a disposable clean-checkout regression and `git diff --check` before
   Research commit/push.

## Closeout Artifacts

- Validation audit:
  `outputs/audits/armindex/a0.9-validation-safety-closeout-20260805.json`
- Phase/task receipt:
  `campaigns/armindex-multiretriever-v2/evidence/a0-phase-closeout.receipt.v1.json`
- Session capsule under `outputs/audits/research-sessions/` and
  `projections/sessions/`.

## Acceptance

- Tasks A0.1 through A0.10 are all `complete` and the A0 phase is `complete`.
- A0.8 synthetic fixture is `passed`; ArmIndex measured, candidate,
  Selection, and Final counters remain zero.
- One validated read model drives MLflow, Brain, Obsidian, Dashboard, and Paper
  projections without drift.
- Protected/unsafe-path scans and all required checks pass.
- The next authorized action is an A1.1 synthetic/offline adapter-fixture
  scaffold only; measured retrieval and model download remain closed until a
  separate A1 execution contract authorizes them.

## Ledger

Append starts, checks, failures/recoveries, and ready-to-close state to
`control/armindex/a0.9-validation-safety-closeout-ledger.v1.jsonl`. Each entry
binds the previous entry hash; existing entries are immutable.
