---
title: "A3 extended five-arm transfer, complementarity, and HarnessOpt"
phase_id: A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT
task_id: A3.1_A3.2
status: PENDING_A2_CLOSEOUT
lifecycle: PENDING
evidence_class: measured_development_and_publication_preparation
scientific_authority: false
execution_permitted: false
previous_goal: docs/goal/A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT_goal_001.md
budget_extension_uri: control/budgets/armindex-budget-extension-a3-v1.json
preparation_authority_uri: control/armindex/a3/a3-five-arm-preparation-authority.v1.json
preparation_manifest_uri: control/armindex/a3/a3-five-arm-preparation-manifest.v1.json
---

# Goal 002: Extended A3 after valid A2 closeout

## Objective

After a valid A2 closeout, measure whether frozen per-arm winners transfer
across compatible retrievers, whether their fixed unions add complementary
coverage, and whether a deterministic label-free HarnessOpt policy improves
the quality-latency-cost frontier. The goal is designed to produce useful
negative or boundary evidence as well as gains.

## Current State

This goal is strictly `PENDING_A2_CLOSEOUT`. Its five-arm bundle is local,
aggregate-safe, and contains no winner hash, metric, protected data, provider
contact, remote work, or spend. It cannot launch until the receipt-bound A2
conditions below are independently validated. Goal 001 remains the bounded
Train-250/HDEV headroom diagnostic; its aggregate report is supplementary and
cannot become an alternate A3 execution authority.

## Scientific Invariants

- A2 winner program bytes/hashes, model adapters, indexes, evaluator, data,
  metrics, and output depth remain frozen.
- The complete 5x5 matrix has five self-winner reuse cells and at most 20
  compatible cross-arm transfer evaluations. Unsupported pairs are reported as
  unsupported; they cannot be replaced with a different program.
- Complementarity uses equal-depth, preregistered fixed-union controls before
  any adaptive harness measurement.
- Extended HarnessOpt permits at most three complete frozen batches, each with
  exactly four roles: quality exploit, cost/latency ablation, routing
  hypothesis, and diversity profile. A batch is never measured partially.
- Adaptive work is limited to Train-250. HDEV-100 is aggregate-only and
  non-adaptive; it cannot tune transfer or HarnessOpt choices.
- Selection and Final remain closed. All repository-visible artifacts are
  aggregate-safe only.

## Budget and Provider Authority

The Owner approved an A3 whole-workload hard stop of USD 35 and a campaign
ceiling of USD 180. This authorization is preserved in the additive budget
extension and becomes launch-effective only after A2 closes at or below its
frozen USD 60 cap. A fresh all-fee quote, provider identity, 48-hour target
TTL, and whole-workload admission are required. The existing Vast instance may
be reused only after A2 safe return and worker reaping; creating another
instance is forbidden.

## Execution Flow

1. Validate PASS A2 execution closeout, result-integrity audit, safe return,
   five winner-selection receipts, and the frozen A1 incumbent aggregate.
2. Emit the post-A2 campaign budget amendment/admission using the Owner's USD
   180 campaign ceiling and USD 35 A3 cap.
3. Build the five-arm runtime bundle from validated receipt hashes, then verify
   the transfer matrix before remote work. Keep unsupported cells explicit.
4. Measure the compatible transfer matrix and fixed complementarity controls.
5. Run one to three complete HarnessOpt batches only while the frozen stop rule,
   budget, TTL, and label-free boundary remain satisfied.
6. Freeze the strongest valid A3 outcome or a no-gain/boundary conclusion;
   generate transfer, complementarity, frontier, and audit figures from
   validated aggregates.
7. Safe-return, result audit, projection synchronization, commit/push, and
   provider disposition. Keep the instance only for this concrete authorized
   A3 workload; otherwise request Owner destruction.

## Hard Stops

Stop before launch on failed A2 closeout/audit, missing winner binding, stale
or over-cap quote, insufficient TTL, provider identity drift, protected-output
surface, any representation/model/evaluator mutation, incomplete batch,
Selection/Final access, or a budget projection above USD 35. A2 outputs are
never reinterpreted to repair any A3 precondition.
