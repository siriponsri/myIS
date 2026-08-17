---
title: "ArmIndex Progress Report: A0 to A2"
audience: "Academic advisor"
report_date: "2026-08-18"
reporting_cutoff_utc: "2026-08-18T18:00:00Z"
status: "A0 complete; A1 complete with measured development evidence; A2 closed; A3 pending Train-250 binding"
numeric_authority: "Validated aggregate receipts only"
update_rule: "Update A2 results only after exact coverage, safe return, closeout, and integrity audit pass."
---

# ArmIndex Progress Report: A0 to A2

## Executive Summary

ArmIndex studies whether representation programs should be conditioned on the retriever, and whether later cross-arm transfer can improve the quality-latency-cost trade-off for structured patent retrieval. The work is staged so that a later claim depends on auditable evidence from earlier phases.

- **A0, migration foundation, is complete.** It established canonical controls, a five-arm registry, the protected-data boundary, and reproducible engineering fixtures. It contains no retrieval-quality result.
- **A1, common multi-arm screening, is complete.** A valid 25-cell REP-DEV screen measured five frozen representation programs across five frozen retrievers. `ARM-03` had the strongest aggregate quality; `ARM-04` and `ARM-05` also passed the frozen promotion rule.
- **A2, per-arm AutoIndex, is closed with measured evidence.** The terminal
closeout accounts for `52 = 44 measured + 8 dormant` candidates with zero
failures, safe return, worker reap, and an independent result-integrity audit.
The whole-workload charge was USD `54.52666666666665948` under the USD 60 cap.
- **A2 advances three primary transfer inputs.** ARM-03 is a presentation-
precision tie to A1, ARM-04 strictly improves its frozen comparator, and ARM-05
has no strict improvement but is retained for transfer analysis. ARM-01/02 are
diagnostic three-way ties with no winner.

Selection and Final remain unopened. Protected qrels, memberships, query identifiers, rankings, per-query outcomes, credentials, and raw provider payloads remain Owner-local.

## Research Design

| Item | Frozen study choice |
|---|---|
| Dataset and evaluation unit | DAPFAM, patent family |
| Primary development metric | OUT Recall@100 |
| Secondary development metrics | OUT nDCG@100 and OUT nDCG@10 |
| Operational metrics | latency, throughput, charged cost, index size, RAM, VRAM |
| Development role | REP-DEV; no Selection or Final access in this report |
| Arms | ARM-01 BM25, ARM-02 BGE-M3, ARM-03 PatEmbed, ARM-04 Arctic Embed, ARM-05 Qwen3 Embedding |
| Common A1 representations | 5 frozen programs x 5 arms = 25 logical cells |

`ARM-03` is research/non-commercial. `ARM-01`, `ARM-02`, `ARM-04`, and `ARM-05` are commercial-capable under their recorded model licenses. This distinction is retained for later production decisions and does not alter the A1 development comparison.

## Phase Status

| Phase | Status | Evidence class | Advisor-level takeaway |
|---|---|---|---|
| A0_MIGRATION_FOUNDATION | Complete | Engineering validation | The experiment is governed, reproducible, and protected-data aware. |
| A1_BASELINES_AND_MULTI_ARM_SCREENING | Complete | Measured development aggregate | Five retrievers were compared under the same five representation programs. |
| A2_PER_ARM_AUTOINDEX | Complete | Measured development aggregate | Exact 52-candidate accounting, safe return, and result-integrity audit passed. |
| A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT | Prepared, not started | Pending hash-bound Train-250 input | A three-primary bundle exists; ARM-03/04/05 only may advance after fresh admission. |
| A4-A6 | Locked | Not measured | Selection, Final, and release remain closed by protocol gates. |

## A0: Migration Foundation

### Objective

A0 converted the project into a controlled research environment before scientific retrieval measurement. It established sources of truth, schemas, arm/model declarations, safe evidence handling, report projections, and feasibility fixtures.

### Completed Work

| Task range | Delivered capability |
|---|---|
| A0.1-A0.2 | Repository/evidence migration and canonical authority documentation |
| A0.3-A0.5 | Brain, read-model, Obsidian, MLflow, Dashboard, phase and Owner-gate migration |
| A0.6-A0.7 | Scientific contracts, schemas, five-arm declarations, and license registry |
| A0.8 | CPU-only compute and storage feasibility fixtures |
| A0.9 | Validation, safety, and phase closeout |
| A0.10 | Legacy-code harvest and phase-ready scaffolding |

### Evidence and Validation

The A0.9 closeout passed the contract, asset, projection, safety, and test checks. Its receipt records 5 registered arms, 1 runnable fixture arm, 0 asset-registry errors, 44 targeted ArmIndex tests, 387 full-suite tests, and 66 Dashboard/API policy tests. The A0.10 independent review accepted the repaired migration/scaffolding package with no blocking findings. Its structural validation recorded 20 focused tests, 14 verified source components, six projection lifecycle events, and zero report drift.

These are engineering and reproducibility facts only. A0 intentionally performed zero measured retrieval runs, zero scientific GPU runs, zero paid API calls, and opened neither Selection nor Final. It supports readiness and provenance claims, not retrieval-quality claims.

### A0 Evidence for Presentation

No performance figure is appropriate for A0 because no performance experiment was run. The relevant evidence is:

- [A0.9 validation and safety closeout](../../outputs/audits/armindex/a0.9-validation-safety-closeout-20260805.json)
- [A0.10 independent acceptance review](../../outputs/audits/rigor/a0.10-legacy-code-harvest-independent-accept-20260804.json)
- [A0.8 compute/storage fixture receipt](../../outputs/fixtures/armindex/a0.8/compute-storage-v1/receipt.json)

## A1: Baselines and Common Multi-Arm Screening

### Objective and Protocol

A1 tested the same five frozen representation programs against every retriever arm on REP-DEV. The valid terminal attempt is `a12-v16-20260811-r15`, with `PASS 25/25` coverage and a charged attempt cost of USD 11.161632. The table below reports aggregate means over the five common programs for each arm; it is valid development evidence, not Final confirmation or a legal conclusion.

### Aggregate A1 Results

| Arm | OUT Recall@100 | OUT nDCG@100 | OUT nDCG@10 | Search p95 (ms) | Total wall time (s) |
|---|---:|---:|---:|---:|---:|
| ARM-01, BM25 lexical | 0.191200 | 0.172717 | 0.160011 | 441.520 | 762.533 |
| ARM-02, BGE-M3 | 0.269933 | 0.231377 | 0.198497 | 235.203 | 19,847.315 |
| ARM-03, PatEmbed | 0.413400 | 0.347812 | 0.289856 | 212.062 | 29,444.640 |
| ARM-04, Arctic Embed | 0.340667 | 0.284546 | 0.235538 | 214.207 | 15,878.488 |
| ARM-05, Qwen3 Embedding | 0.363733 | 0.307930 | 0.256706 | 217.099 | 40,309.513 |

Key observations:

- `ARM-03` is highest on the primary and both secondary aggregate metrics, but it remains research/non-commercial.
- `ARM-05` is second on the primary metric and has the largest total wall time.
- `ARM-04` is a strong commercial-capable dense arm with the shortest dense-arm total wall time.
- `ARM-01` is the CPU lexical anchor and lowest-quality aggregate reference; it remains valuable as a non-neural diagnostic baseline.
- `ARM-02` exceeds the lexical anchor but did not advance under the frozen decision rule.

The frozen promotion rule advanced `ARM-03`, `ARM-05`, and `ARM-04`. `ARM-01` and `ARM-02` remain diagnostic/non-advancing in A2.

### Cell-Level Pattern and Reliability

The 25-cell EDA shows that representation choice matters within each retriever. In the published cell table, fixed passages had the highest Recall@100 for every arm. This is descriptive evidence, not proof that one representation should be reused across arms; testing that assumption is A2's purpose.

An earlier A1 attempt, `a12-v16-20260811-r14`, failed closed before any dense cell receipt because mandatory performance/resource/reliability instrumentation was missing. Its 5 lexical cells and 0 dense cells were neither promoted nor mixed with `r15`. After the repair, the clean `r15` attempt completed all 25 cells. This preserves evidence integrity rather than treating partial data as a result.

### A1 Figures for Advisor Presentation

| Figure | Recommended use | Files |
|---|---|---|
| Quality cell EDA | Main result slide: Recall@100 and nDCG across all 25 cells | [PNG](../../outputs/figures/armindex/a12-v16-20260811-r15.quality-cell-eda.v16.png), [SVG](../../outputs/figures/armindex/a12-v16-20260811-r15.quality-cell-eda.v16.svg) |
| Efficiency cell EDA | Methods/efficiency slide: latency, wall time, and peak VRAM | [PNG](../../outputs/figures/armindex/a12-v16-20260811-r15.efficiency-cell-eda.v16.png), [SVG](../../outputs/figures/armindex/a12-v16-20260811-r15.efficiency-cell-eda.v16.svg) |
| REP-DEV/HARNESS-DEV split | Study-design slide: precommitted data-role separation | [PNG](../../outputs/figures/armindex/a1.2-rep-harness-split-eda-v1.png), [SVG](../../outputs/figures/armindex/a1.2-rep-harness-split-eda-v1.svg) |
| Dense-overflow EDA | Appendix/methods slide: frozen windowing and recomposition policy | [PNG](../../outputs/figures/armindex/a1.2-dense-overflow-eda-v1.png), [SVG](../../outputs/figures/armindex/a1.2-dense-overflow-eda-v1.svg) |

Detailed 25-cell values: [A1 cell EDA](../operations/A1_2_R15_CELL_EDA_20260811_TH.md). Aggregate closeout: [A1.2 measured closeout](../operations/A1_2_R15_MEASURED_CLOSEOUT_20260811_TH.md).

## A2: Per-Arm AutoIndex (Closed)

### Objective

A2 searches the frozen representation-candidate universe independently per arm. It evaluates exactly 52 candidates: 40 matched candidates followed by 12 conditional reserve candidates only if the frozen matched-barrier and remaining-time/budget admission pass. The primary outcome remains OUT Recall@100.

### Measured Closeout

| Item | Validated state |
|---|---|
| Attempt | `a2-goal004-20260816-005` |
| Execution status | `PASS_A2_EXECUTION_CLOSEOUT` |
| Integrity status | `PASS_A2_RESULT_INTEGRITY` |
| Candidate accounting | 52 total = 44 measured + 8 dormant; 0 failed |
| Primary metric | OUT Recall@100 |
| Whole-workload cost | USD `54.52666666666665948` / USD 60 |
| Provider disposition | `OWNER_ACTION_DESTROY`; no bound A3 workload |

### Winner and Diagnostic Outcomes

| Arm | Winner / diagnostic representation | Recall@100 | Interpretation |
|---|---|---:|---|
| ARM-01 | diagnostic three-way top tie | 0.23467 | no winner; excluded from A3 |
| ARM-02 | diagnostic three-way top tie | 0.29000 | no winner; excluded from A3 |
| ARM-03 | `matched-b2-orthogonal` | 0.42300 | tie at presentation precision; A3 transfer input |
| ARM-04 | `matched-b1-orthogonal` | 0.35867 | +0.0060 vs A1; A3 transfer input |
| ARM-05 | `matched-b1-matched-ablation` | 0.37367 | no strict improvement; retained for transfer |

### A2 Publication Figures

The five figure families are rendered from the validated closeout projection:

| Planned figure | Reviewer question |
|---|---|
| Coverage and recovery completeness | [PNG](../../outputs/figures/armindex/a2-goal004/a2-goal004-coverage-recovery.png) |
| Per-arm quality outcomes | [PNG](../../outputs/figures/armindex/a2-goal004/a2-goal004-outcomes.png) |
| Quality-latency-cost frontier | [PNG](../../outputs/figures/armindex/a2-goal004/a2-goal004-quality-latency-cost-frontier.png) |
| Matched versus reserve path | [PNG](../../outputs/figures/armindex/a2-goal004/a2-goal004-matched-reserve-decision-path.png) |
| Appendix provenance and claim boundary | [PNG](../../outputs/figures/armindex/a2-goal004/a2-goal004-appendix-audit-map.png) |

The complete PNG/SVG/PDF manifest is
[A2 figure manifest](../../outputs/figures/armindex/a2-goal004/a2-goal004-figure-manifest.v1.json).

## Next Milestones

1. Obtain or locate the Owner-authorized hash-bound Train-250 query/corpus/evaluator package.
2. Bind fresh A3 admission, budget, runtime, and transfer receipts for ARM-03/04/05 only.
3. Run A3 Extended transfer, fixed-union, complementarity, and HarnessOpt measurements with aggregate-safe return.

## Evidence Pointers and Claim Boundary

- [Campaign record, current A2 closeout and A3 pending state](../../control/campaigns/armindex-multiretriever-v2.yaml)
- [A0.9 validation/safety closeout](../../outputs/audits/armindex/a0.9-validation-safety-closeout-20260805.json)
- [A0.10 independent acceptance](../../outputs/audits/rigor/a0.10-legacy-code-harvest-independent-accept-20260804.json)
- [A1 r14 failed-closed audit](../../outputs/audits/armindex/a1.2-v16-r14-instrumentation-failure-20260811.json)
- [A2 Goal 004, terminal closeout](../goal/A2_PER_ARM_AUTOINDEX_goal_004.md)
- [A2 LO 004-001 measured closeout](../long_run/A2_PER_ARM_AUTOINDEX_lo_004_001.md)
- [A2 closeout projection](../../control/armindex/a2/a2-goal004-closeout-projection.v1.json)
- [A2 figure manifest](../../outputs/figures/armindex/a2-goal004/a2-goal004-figure-manifest.v1.json)
- [A2 execution runbook](../../control/runbooks/A2_PER_ARM_AUTOINDEX_EXECUTION_V2.md)

This is an advisor-facing synthesis of aggregate-safe evidence. A0 is engineering evidence. A1 and A2 are development evidence, not Selection or Final confirmation. A3 remains pending a hash-bound Train-250 input package. The report makes no legal, infringement, novelty, causal, Selection, or Final claim and contains no protected record-level data.
