---
title: "A7 scientific audit and oracle headroom"
phase_id: A7_SCIENTIFIC_AUDIT_AND_ORACLE_HEADROOM
task_id: A7.1
status: SUPERSEDED_BY_A7_SEVEN_LAYER_RETRIEVAL_DIAGNOSIS
lifecycle: CLOSED
evidence_class: post_confirmatory_diagnostic_audit
scientific_authority: false
execution_permitted: false
protected_payloads_allowed: owner_local_only
previous_goal: docs/goal/A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY_goal_001.md
next_goal: docs/goal/A7_SEVEN_LAYER_RETRIEVAL_DIAGNOSIS_goal_001.md
last_material_update: 2026-08-22
---

# Historical Goal 001: A7 scientific audit and oracle headroom

This document is preserved for provenance only. The canonical execution route
is [A7_SEVEN_LAYER_RETRIEVAL_DIAGNOSIS_goal_001.md](A7_SEVEN_LAYER_RETRIEVAL_DIAGNOSIS_goal_001.md),
which follows `inbox/UPDATE_PLAN.md` and includes the audit/oracle checks as
Layers 1-7. It must not be launched independently.

## Objective

Independently audit the closed A5 confirmation and the immutable A6
full-DAPFAM Top-200 pool. Establish metric identity, population and relevance
denominators, family aggregation, leakage controls, benchmark comparability,
and remaining oracle headroom before any reranker is run.

## Frozen boundary

A7 consumes the A6 pool by hash and must not alter the winner, representation,
retriever, candidate membership, ranks, Selection, or Final. Qrels, split
membership, protected identifiers, and per-query outcomes are Owner Store only.
Repository-facing outputs are aggregate-safe receipts, metrics, confidence
intervals, figures, hashes, and provenance manifests only.

## Required checks

1. Replay Recall@100, nDCG@100, and nDCG@10 from ranking evidence with an
   independent local implementation and reconcile denominators and tie policy.
2. Account for ALL, IN, OUT, excluded, development, Selection-125, Final-872,
   and full-DAPFAM populations without exporting membership.
3. Audit source-to-family mapping, MaxP aggregation, self-match exclusion, and
   absence of qrels or population labels in A6 provider-side inputs.
4. Replay A5's paired comparison with 10,000 bootstrap resamples, 95% CI, and
   W/T/L from Owner-local evidence.
5. Compute frozen-pool Recall@10/20/50/100/200 and oracle error decomposition:
   exposed at 1-100, rerankable at 101-200, and absent from Top-200.
6. Publish an aggregate protocol-comparability matrix and the strongest claim
   class supported by the evidence; never infer SOTA from headline scores.

## Terminal states

`PASS_A7_SCIENTIFIC_AUDIT`, `STOP_A7_WITH_EVIDENCE`, or
`HARD_STOP_A7_EVIDENCE_INTEGRITY`. A valid audit does not choose an A8 model:
the fixed A8 matrix runs on the same pool regardless of observed headroom.
