---
name: myis-run-harnessopt
description: Preflight, dry-run, execute, collect, and compare an approved optional IS1 Research V0.1 A0-A3 HarnessOpt adaptation-surface study while preserving Gate C/R, split isolation, immutable manifests, budgets, provider identity, and aggregate-only confirmation.
---

# Run IS1 Research V0.1 HarnessOpt

HarnessOpt is optional Track S methods work. It does not replace the Gate C
candidate-exposure protocol or Gate R frozen-pool ranking protocol.

Read `AGENTS.md`, `PLAN.md`, `00_governance/OWNER_GATES.md`, the active approval,
run spec, split commitments, budget, module registry, and
`references/harnessopt-contract.md`.

## Preserve boundaries

Keep evaluator, metric/statistics definitions, split/qrels commitments,
confirmation boundary, family mapping, baseline/frozen results, approval/budget/
redaction/manifest validation, target model roles, module pool, and stopping
ceilings fixed. Reject any patch touching protected paths or adding undeclared
tools/executable code.

Arms are A0 frozen baseline, A1 human seed skill, A2 optimized skill/frozen
harness, and A3 optimized skill plus declared typed policy. A2/A3 must use the
same initial state, model, provider, effort, data access, evaluator, tools,
budget, repeat schedule, and stopping. Start qrels-blind calibration with
GPT-5.6 Sol Medium; escalate to High only after validity failure and then freeze
the result. Luna is support-only or a separate cost ablation. No silent fallback.

## Execute

1. Validate IS1 identity, G5 approval, `RunSpec`, exact Python/uv/OS/lock
   environment, provider identity, split hashes, protected/editable surfaces,
   repeats, module pool, budget, and fresh output path.
2. Dry-run fixtures to prove protected access denial, patch denial, budget stop,
   event ordering, immutable manifest, MLflow-deferred behavior, and recovery.
3. Expose only adaptation/selection qrels and prevent protected network
   re-download.
4. Execute adapter lifecycle `preflight -> dry_run -> execute -> collect` and
   preserve every repeat, including invalid/failed runs.
5. Accept a trial only when its preregistered primary selection score is strictly
   greater than the incumbent. Reject ties and lower scores.
6. Validate per-query/aggregate consistency, hashes, cost, provider/fallback,
   repeat matching, batch-order invariance, and protected-surface integrity.
7. Write canonical artifacts and manifest immutably. Mirror allowlisted files to
   MLflow only after validation; mirror failure cannot invalidate the bundle.

Do not choose the best repeat or tune after confirmation. Confirmation executes
outside the workspace and returns aggregate-only statistics. Present DAPFAM as
retrieval relevance, never legal novelty/FTO evidence.
