# IS1 HarnessOpt execution contract

## Arm invariants

| Arm | Editable surface |
|---|---|
| A0 | frozen baseline |
| A1 | human seed skill; frozen harness |
| A2 | optimized skill; frozen harness |
| A3 | optimized skill plus declared typed policy |

A2/A3 share model/provider/effort, initial state, adaptation/selection data,
evaluator/statistics, module pool, tools, trial/token/time/cost ceilings, repeat
IDs/order, and stopping. All repeats are reported. Silent fallback or protected
path access invalidates a run.

## Selection

Preregister one primary optimizer selection score. Accept a candidate only when
`candidate_score > incumbent_score`; reject exact ties. Secondary metrics cannot
rescue a tie/loss unless they were part of the preregistered score before data.

Track S does not define Gate C/R success. Gate C remains OUT Recall@100 and Gate
R remains OUT nDCG@100 on an identical frozen pool.

## Required bundle

Applicable artifacts include prompt, skill manifest, flow/config, runtime and
progress JSONL, candidates/evidence/per-query rows, metrics/statistics/result,
validation/environment, immutable manifest, and MLflow receipts. Manifest is
written last and never overwritten. MLflow is a rebuildable mirror.

## Approval and data boundaries

G5 authorizes only its specified adaptation study and budget. Expose adaptation/
selection qrels only. Confirmation membership/qrels/outcomes remain external and
cannot re-enter policy selection. DAPFAM measures retrieval relevance only.
