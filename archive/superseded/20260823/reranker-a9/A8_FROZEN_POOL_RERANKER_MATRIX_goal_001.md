---
title: "A8 frozen-pool reranker matrix"
phase_id: A8_FROZEN_POOL_RERANKER_MATRIX
task_id: A8.1
status: LOCKED_UNTIL_A7_AUDIT
lifecycle: BLOCKED
evidence_class: post_confirmatory_fixed_matrix
scientific_authority: false
execution_permitted: false
protected_payloads_allowed: owner_local_only
previous_goal: docs/goal/A7_SCIENTIFIC_AUDIT_AND_ORACLE_HEADROOM_goal_001.md
next_goal: docs/goal/A9_PUBLICATION_AND_RELEASE_goal_001.md
last_material_update: 2026-08-22
---

# Goal 001: A8 frozen-pool reranker matrix

## Objective

Measure the fixed BGE, Qwen3, and Jina reranking paradigms against the
unchanged A6 order and oracle ceiling on exactly the A6 Top-200 pool. The goal
tests residual within-pool ranking headroom, not another retrieval system.

## Frozen system matrix

`NO_RERANK_A6_ORDER`, `BAAI/bge-reranker-v2-m3`,
`Qwen/Qwen3-Reranker-0.6B`, `jinaai/jina-reranker-v3.5`, and `ORACLE_CEILING`.
There is no model selection, prompt search, model substitution, tuning,
candidate expansion, qrel-aware inference, or new retrieval. Every arm binds
the same immutable A6 pool hash.

## Metrics and evidence

Report ALL/IN/OUT Recall@100, nDCG@100, nDCG@10, paired bootstrap (10,000),
95% CI, W/T/L, latency, throughput, cost, RAM/VRAM, failures, and recovered
oracle headroom. Per-query rows, rankings, qrels, and membership remain in
Owner Store. A8 does not change A5's confirmed retrieval champion.

## Terminal states

`PASS_A8_FROZEN_POOL_RERANKER_MATRIX`, `STOP_A8_WITH_EVIDENCE`, or
`HARD_STOP_A8_EVIDENCE_INTEGRITY`.
