---
name: myis-run-harnessopt
description: Preflight, dry-run, execute, collect, and compare a governed myIS HarnessOpt experiment against fixed-harness, SkillOpt, and reproduced-reference baselines. Use for approved HarnessOpt or DAPFAM benchmark work that must preserve split isolation, budgets, immutable manifests, structlog JSONL, MLflow lineage, and paper-grade result provenance.
---

# Run myIS HarnessOpt

Optimize the evolvable harness policy while preserving the immutable evaluation kernel. Never change model weights under this workflow.

## Load authority and contract

Read, in order:

1. `AGENTS.md`
2. `00_governance/OWNER_GATES.md`
3. `PLAN.md`
4. `00_governance/config/tools.lock.yaml`
5. [references/harnessopt-contract.md](references/harnessopt-contract.md)
6. The selected goal, approval, run specification, split manifest, budget, and module registry.

If facts conflict, a source pin has drifted, or authorization is incomplete, stop and report the exact blocker. A recommendation, earlier run, or silent response is not approval.

## Preserve immutable and evolvable boundaries

Keep these kernel components fixed across all comparison arms:

- evaluator and metric definitions;
- split guard and query-ID hashes;
- approval and budget enforcement;
- event logging, artifact schemas, and manifest validation;
- target/optimizer model roles and revisions;
- tool/module pool and stopping budget.

Allow optimization only in the declared policy surface: query and context planning, retrieval route, representation, fusion/RRF, reranking/evidence policy, fallback, and stopping decisions.

Reject any candidate that changes the evaluator, sees protected confirmation feedback, changes model weights, expands tools, or exceeds the declared budget.

## Follow the state machines

Advance a goal only through `DRAFT -> REVIEWED -> APPROVED -> ACTIVE -> CLOSED` or `CANCELLED`.

Advance a run only through `CREATED -> PREFLIGHTED -> RUNNING -> SUCCEEDED`, `FAILED`, `CANCELLED`, or `INVALIDATED`.

Persist the transition reason, actor, approval reference, timestamp, and event ID. Never repair an invalid transition by editing history.

## Execute the workflow

1. **Preflight**
   - Validate `GoalSpec`, `ApprovalRecord`, `RunSpec`, split hashes, model pins, module registry, seed list, budget, and output root.
   - Verify the comparison arms are the reproduced reference, fixed human harness, SkillOpt baseline, and HarnessOpt.
   - Verify SkillOpt is pinned to the lock file and is treated only as a baseline.
   - Verify run artifacts do not already exist at the target run ID.

2. **Dry run**
   - Exercise fixtures or permitted development data only.
   - Prove split denial, budget denial, cancellation, failure finalization, event ordering, MLflow retry receipts, and atomic manifest behavior.
   - Do not treat fixture output as scientific evidence.

3. **Approval check**
   - Require R3 approval before paid/API/GPU/Vast execution.
   - Require R4 approval and one frozen method before prospective confirmation.
   - Stop if the approval scope, ceiling, split, or model differs from `RunSpec`.

4. **Execute**
   - Call the harness adapter lifecycle in order: `preflight`, `dry_run`, `execute`, `collect`.
   - Use `cancel` only for an authorized cancellation or a kernel-enforced ceiling.
   - Emit every diagnostic event through the configured structlog context to console and `runtime.jsonl`; derive milestones into `progress.jsonl`.
   - Never let MLflow availability determine scientific execution success.

5. **Collect and validate**
   - Require all artifacts listed in the contract.
   - Recompute aggregate metrics from `per_query_metrics.jsonl` and compare them to `metrics.json`.
   - Validate all hashes, event ordering, split identity, budget use, Git revision, prompt/config/skill pins, and MLflow receipts.
   - Write `manifest.json` atomically, last, and only after `validation_report.json` passes.

6. **Compare**
   - Report three fixed-seed means, absolute deltas, and relative deltas.
   - Declare a HarnessOpt win only when both OUT NDCG@100 and OUT Recall@100 exceed both SkillOpt and the reproduced DAPFAM reference.
   - Enforce each IN NDCG@100 and Recall@100 drop at no more than 0.01 absolute and invalid-query rate at no more than 1%.
   - Treat MAP, MRR, P@10, ALL, latency, and cost as diagnostics, not alternate win conditions.

## Finish safely

On failure or cancellation, still finalize diagnostic artifacts and record the terminal state; do not fabricate scientific metrics. Keep MLflow retry receipts append-only. Present results as retrieval relevance evidence only, never as legal novelty or freedom-to-operate evidence.

Do not alter Git state, publish, access another track, or tune after the frozen confirmation cohort has been observed.
