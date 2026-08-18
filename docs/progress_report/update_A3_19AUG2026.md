---
title: "ArmIndex A3 Extended Closeout"
phase: "A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT"
as_of: "2026-08-19"
status: "PASS_A3_RESULT_INTEGRITY_AUDIT"
language: "English"
evidence_class: "measured_development_aggregate"
claim_boundary: "A3 Train-250 development evidence only; Selection, Final, and production transfer remain closed."
---

# ArmIndex A3 Extended Closeout

## Executive Summary

A3 Extended completed the receipt-bound three-primary experiment for ARM-03
(PatEmbed), ARM-04 (Arctic Embed), and ARM-05 (Qwen3 Embedding). The run
completed all 14 authorized operations on the existing Vast instance:

- 9 transfer cells covering the complete 3 x 3 source-program to target-adapter matrix;
- 5 preregistered fixed-combination controls;
- 250/250 Train-250 units completed for every operation;
- 3 complete HarnessOpt batches with 12 frozen candidates and one effective action signature.

The independent result-integrity audit passed. The safe return contains aggregate
metrics only. No ranking, qrels, membership, raw identifier, or per-query outcome
was projected into the repository.

The strongest aggregate quality result is the ARM-05 winner program transferred
to the ARM-03 adapter (`transfer-arm-05-to-arm-03`), with OUT Recall@100
`0.419274`. The strongest fixed control is `fixed-top-two-rrf60`, with OUT
Recall@100 `0.418715` and OUT NDCG@100 `0.352747`. The all-primary union does
not improve over the top-two control in this development workload. HarnessOpt
therefore reaches a valid flat-surface stop rather than claiming an adaptive
improvement.

These findings are development evidence, not a Selection or Final result.
A4 readiness is prepared contractually, but production transfer and Selection
remain closed.

## Scientific Question

A3 tests whether an A2-selected representation program transfers across a
different retrieval adapter and whether fixed multi-arm combinations add useful
family-level coverage. The experiment preserves negative and boundary findings:
it does not select only positive outcomes and does not tune on protected
confirmation data.

## Frozen Scope

| Item | Frozen value |
|---|---|
| Primary arms | ARM-03 PatEmbed; ARM-04 Arctic Embed; ARM-05 Qwen3 Embedding |
| Scientific unit | Train-250, 250 queries |
| Transfer matrix | 3 source winner programs x 3 target adapters |
| Fixed controls | best single, commercial-only fixed union, top-two RRF-60, top-three RRF-60, all-primary RRF-60 |
| Output depth | 100 families per query |
| Metrics | OUT Recall@100, OUT NDCG@100, OUT NDCG@10 |
| HarnessOpt | 3 complete frozen batches, 4 roles per batch, 12 candidates total |
| Protected access | Owner-local evaluation only; Selection and Final closed |
| A3 budget | USD 35 hard cap; projected workload remained within the authorized ceiling |

## Operation Coverage

| Evidence gate | Count | Result |
|---|---:|---|
| Remote operations launched | 14 | Complete |
| Return receipts | 14 | Complete |
| Transfer cells | 9 | Complete |
| Fixed controls | 5 | Complete |
| Train-250 units per operation | 250/250 | Complete |
| Failure markers | 0 | Pass |
| Aggregate result files | 14 | Complete |
| HarnessOpt batches | 3/3 | Complete |
| HarnessOpt candidates | 12/12 | Complete |
| Unique effective action signatures | 1 | Flat-surface stop |

## Transfer Matrix

The source arm identifies the frozen A2 winner program. The target arm identifies
the adapter used for the transfer run. Diagonal cells are self-winner reuse
controls; off-diagonal cells are cross-arm transfer tests.

| Source program | PatEmbed adapter | Arctic Embed adapter | Qwen3 Embedding adapter |
|---|---:|---:|---:|
| PatEmbed | 0.418436 | 0.337430 | 0.362570 |
| Arctic Embed | 0.418715 | 0.341341 | 0.359497 |
| Qwen3 Embedding | 0.419274 | 0.338268 | 0.360615 |

Values are OUT Recall@100. The complete matrix is available in
`A3_transfer_matrix_eda_20260819.csv` and the heatmap is available at
`figures/a3-transfer-recall-heatmap-20260819.png`.

### Transfer Interpretation

1. The highest transfer quality is Qwen3 Embedding program -> PatEmbed adapter
   (`0.419274`), a small numerical gain over the strongest fixed control.
2. Transfer into the Arctic Embed adapter is consistently weaker in this
   workload (`0.337430` to `0.341341` Recall@100), indicating a meaningful
   representation-adapter interaction rather than universal portability.
3. The diagonal self-winner cells are not uniformly dominant. This is useful
   boundary evidence for the paper: the best representation program and the best
   runtime adapter need not be the same object.

## Fixed Combination Controls

| Control | OUT Recall@100 | OUT NDCG@100 | OUT NDCG@10 | Wall time (s) |
|---|---:|---:|---:|---:|
| best single | 0.418436 | 0.347098 | 0.290589 | 8782.83 |
| top-two RRF-60 | **0.418715** | **0.352747** | **0.293716** | 13607.22 |
| all-primary RRF-60 | 0.415084 | 0.346250 | 0.284772 | 18405.79 |
| top-three RRF-60 | 0.415084 | 0.346250 | 0.284772 | 17484.52 |
| commercial-only fixed union | 0.369274 | 0.308967 | 0.258116 | 10647.75 |

The complete aggregate table is available in
`A3_fixed_controls_eda_20260819.csv`; the quality comparison is shown in
`figures/a3-fixed-control-quality-20260819.png`.

### Complementarity Interpretation

The top-two fixed union has the strongest fixed-control quality and improves
NDCG over the best single arm, while the all-primary and top-three unions are
lower on all three quality metrics and take longer. Adding every primary arm is
therefore not automatically complementary. The commercial-only union is a
bounded negative control, not a failed experiment.

## HarnessOpt Boundary

All three HarnessOpt batches were complete and hash-bound before evaluation.
Their 12 candidates compiled into one effective label-free action signature.
The frozen all-primary aggregate result is therefore reused as an exact
aggregate-safe reference for the flat surface. This supports the claim
`PASS_A3_HARNESSOPT_FLAT_SURFACE`, not a claim that adaptive HarnessOpt improved
quality.

## Evidence and Provenance

| Artifact | Safe identifier |
|---|---|
| Result-integrity audit | `3fbc601111b204d3d4829aab63cda2e4368f2b76fd08315c14f4c21abf820644` |
| Aggregate safe return | `48cb4c51680ec3e59a876dad9b3feaa0593c39585bf27ae4eaf1d50e950453dc` |
| HarnessOpt evaluation | `547ed212febe8c70f6675ca9851e652d391940598fbfb39ec41394c8c453007a` |
| Runtime bindings | `58e8d604d9b608b6e733e0ec961304539c6ce84c0f626a0278b9a713789b5e68` |
| Stage manifest | `fbe537571001c601dd2267c28f76dd2e35dba0bd15204e9baef78f3be05c2acf` |
| Stage receipt | `57069a44ca2288328758f5706672f68a39393a4a23f01733f11f96470ae95a1c` |
| A3 attempt | `a3-goal003-20260818-028` |

The Owner Store retains the complete protected return lineage. This report
contains only aggregate-safe identifiers and metrics.

## Recovery and Engineering Notes

The remote run completed without a scientific failure marker. The first
Owner-local watchdog evaluation stopped because the CLI parser exposed
`stage_receipt`, `stage_manifest`, `runtime_bindings`, and `safe_return_receipt`
while the evaluator function required explicit `*_path` parameters. The
evaluator was repaired, regression-tested, rerun against the same 14 receipts,
and passed. No remote operation was restarted and no partial result was mixed.

The fix and CLI regression test are included in commit `73342aa3`.

## A4 Readiness Boundary

A4 readiness is contractually scaffolded in
`docs/research/A4_READINESS_CONTRACT.md`. The A3 evidence supports preparation
of production-transfer profiles, but it does not open Selection or Final. Any
future A4 execution must bind this audit, the safe return, the frozen runtime,
and the Owner-approved production gate before measurement.

## Reproducible Artifacts

- EDA tables: `A3_transfer_matrix_eda_20260819.csv`, `A3_fixed_controls_eda_20260819.csv`
- Figures: `figures/a3-transfer-recall-heatmap-20260819.png`, `figures/a3-fixed-control-quality-20260819.png`
- Audit script: `../scripts/audit_a3_three_primary_results.py`
- EDA/figure builder: `../scripts/build_a3_closeout_eda.py`
- Progress deck: `../docs/presentation/progress/ArmIndex_Progress_A0_A3_2026-08-18.pptx`

## Claim Boundary

The defensible A3 claim is:

> On the frozen Train-250 development workload, representation-program transfer
> produced a measurable adapter interaction, the top-two fixed union was the
> strongest fixed combination, all-primary fusion did not improve the quality
> frontier, and the bounded HarnessOpt surface was flat.

The following claims are not supported by this closeout: Selection performance,
Final confirmation performance, production generalization, protected test-set
performance, or universal superiority of any ARM.
