# HarnessOpt execution contract

## Required run bundle

Every successful, failed, cancelled, or invalidated run must preserve the applicable artifacts:

```text
prompt.json
flow.json
progress.jsonl
result.json
metrics.json
runtime.jsonl
per_query_metrics.jsonl
validation_report.json
receipts/mlflow-*.json
manifest.json
```

Write `manifest.json` atomically and last. Once written, treat it as immutable. A failed MLflow mirror creates another receipt; it does not rewrite prior receipts or the manifest.

## Runtime event fields

Every runtime event must contain:

```text
schema_version, event_id, timestamp_utc, monotonic_ns, sequence,
level, event, run_id, goal_id, phase, component, status
```

Sequence values are strictly increasing within a run. Console output is a human view; `runtime.jsonl` is diagnostic event truth; `progress.jsonl` is a milestone projection.

## Comparison invariants

All four arms share the evaluator, split hashes, query population, target and optimizer roles, tool/module pool, per-query ceilings, total budget, seeds, and stopping policy budget:

1. reproduced DAPFAM/MTEB reference;
2. fixed human harness;
3. SkillOpt baseline;
4. HarnessOpt.

Primary task: DAPFAM OUT TAC-to-TAC at Top-100.

Use deterministic, stratified query-ID partitions of 60% train, 20% selection, and 20% prospective confirmation. Because historical DAPFAM queries were evaluated previously, describe the final cohort as prospectively isolated, not globally untouched.

## Result decision table

| Check | Required outcome |
|---|---|
| OUT NDCG@100 | HarnessOpt mean exceeds SkillOpt and reproduced reference |
| OUT Recall@100 | HarnessOpt mean exceeds SkillOpt and reproduced reference |
| IN NDCG@100 drop | No worse than 0.01 absolute |
| IN Recall@100 drop | No worse than 0.01 absolute |
| Invalid-query rate | At most 1% |
| Budget | At or below predeclared ceiling |

If any required outcome fails, report no win. Do not substitute a diagnostic metric.

## Approval boundaries

- R3 authorizes only the specified paid/API/GPU/Vast run and budget.
- R4 authorizes only the specified frozen prospective confirmation.
- Confirmation feedback cannot re-enter policy selection or tuning.
- DAPFAM measures retrieval relevance, not legal novelty or freedom to operate.
