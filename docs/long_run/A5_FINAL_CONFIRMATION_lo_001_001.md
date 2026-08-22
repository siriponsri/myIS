# A5 Final Confirmation Closeout

Status: `PASS_A5_FINAL_CONFIRMATION` on 2026-08-22. A6 is
`PAUSED_OWNER_A6_APPROVAL`.

## Scope and validity

The isolated Final attempt
`a5-goal001-20260822T-rerun-final872-r03` completed on Vast instance
`48367896`. It evaluated exactly the frozen two-system registry over
Final-872. Both systems covered `872/872` queries with zero failures and
deterministic output. Final access is now consumed exactly once; no A5 rerun,
replacement system, or post-hoc tuning is permitted.

The owner-local evaluator, opaque ranking package, and protected inputs remain
in Owner Store. The repository contains only the aggregate-safe receipt set at
`control/armindex/a5/final-r03-20260822/`.

## Confirmatory Results

| Metric, OUT Final-872 | ARM-03 research champion | Static/common baseline | Delta |
|---|---:|---:|---:|
| Recall@100 | 0.442476 | 0.331097 | +0.111379 |
| nDCG@100 | 0.365595 | 0.279253 | +0.086342 |
| nDCG@10 | 0.297459 | 0.233666 | +0.063794 |

The paired Recall@100 delta has a deterministic 10,000-resample 95% bootstrap
CI of `[0.102294, 0.120438]`. Recall@100 W/T/L is `619 / 158 / 95`.

## Operational Evidence

| System | p50 / p95 / p99 latency (ms) | Throughput (qps) |
|---|---:|---:|
| ARM-03 research champion | 237.55 / 732.22 / 1044.61 | 3.319 |
| Static/common baseline | 315.86 / 735.17 / 804.00 | 2.666 |

Shared Final execution cost was USD `1.4568`; peak RAM was `16.36 GiB`, peak
VRAM `0.845 GiB`, and staged asset/index size `2,961,523,444` bytes. These are
single-run operational observations, not a comparative full-corpus deployment
claim.

## Frozen A6 Input

The sole A6 target is the Final winner `research_champion` / ARM-03,
`datalyes/patembed-large`, program `a2-arm-03-matched-b2-orthogonal`:
title + abstract + claims, passage size `384`, overlap `64`, and MaxP family
aggregation. The A6 winner binding hash is
`b3db02625d14234ea26edfb1e76ff00981d8458849b48de58d6549beb574b2f3`.

A6 may establish only post-confirmatory full-DAPFAM materialization and
scalability evidence. It must not make a new retrieval-quality, external
generalization, or baseline-superiority claim.

## Receipt Set

All following files are aggregate-safe and self-hashed where applicable:

- `A5_FINAL_OWNER_EVALUATION.json`
- `A5_FINAL_COVERAGE.json`
- `A5_FINAL_SAFE_RETURN.json`
- `A5_FINALIST_REGISTRY.json`
- `A5_FINAL_RESULT_INTEGRITY_AUDIT.json`
- `A5_FINAL_CLOSEOUT.json`
- `A5_FROZEN_WINNER_BINDING.json`

## A6 Boundary

Do not upload the full DAPFAM corpus or start an A6 worker yet. On explicit
Owner approval, create a fresh A6 attempt root on `48367896`, obtain new
provider identity, quote, budget, TTL, runtime/GPU/disk health, and safe-return
receipts, then materialize the full corpus once with the frozen ARM-03 binding.
