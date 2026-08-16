---
title: "ArmIndex Progress Report: A0 to A2"
audience: "Academic advisor"
report_date: "2026-08-16"
reporting_cutoff_utc: "2026-08-16T11:49:32Z"
status: "A0 complete; A1 complete with measured development evidence; A2 active"
numeric_authority: "Validated aggregate receipts only"
update_rule: "Update A2 results only after exact coverage, safe return, closeout, and integrity audit pass."
---

# ArmIndex Progress Report: A0 to A2

## Executive Summary

ArmIndex studies whether representation programs should be conditioned on the retriever, and whether later cross-arm transfer can improve the quality-latency-cost trade-off for structured patent retrieval. The work is staged so that a later claim depends on auditable evidence from earlier phases.

- **A0, migration foundation, is complete.** It established canonical controls, a five-arm registry, the protected-data boundary, and reproducible engineering fixtures. It contains no retrieval-quality result.
- **A1, common multi-arm screening, is complete.** A valid 25-cell REP-DEV screen measured five frozen representation programs across five frozen retrievers. `ARM-03` had the strongest aggregate quality; `ARM-04` and `ARM-05` also passed the frozen promotion rule.
- **A2, per-arm AutoIndex, is active.** Runtime authority v4 is
  `PASS_A2_MEASURED_EXECUTION_AUTHORIZED`. At the reporting cutoff, 16 durable
  remote result files had been observed by existence only and 11 aggregate-safe
  candidate receipts had been harvested. These are operational progress
  signals, not canonical A2 outcomes.

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
| A2_PER_ARM_AUTOINDEX | Active | Measured execution live; validated result pending closeout | Per-arm search is running; no A2 outcome should yet be interpreted. |
| A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT | Prepared, not started | Pending A2 closeout | A five-arm hash-only bundle exists but is inert until A2 validates. |
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

## A2: Per-Arm AutoIndex

### Objective

A2 searches the frozen representation-candidate universe independently per arm. It evaluates exactly 52 candidates: 40 matched candidates followed by 12 conditional reserve candidates only if the frozen matched-barrier and remaining-time/budget admission pass. The primary outcome remains OUT Recall@100.

### Live Operational State

| Item | Current state at reporting cutoff |
|---|---|
| Active attempt | `a2-goal004-20260816-005` |
| Runtime authority | `myis.armindex-a2-measured-execution-authority.v4`, `PASS_A2_MEASURED_EXECUTION_AUTHORIZED`, stored in the clean execution worktree |
| Provider topology | Vast instance `47790578`, 4 x RTX 3090; ARM-01 runs on CPU and ARM-02 through ARM-05 use the GPU topology |
| Budget authority | Whole-workload quote USD 54.5266667, below the USD 60 hard cap at fresh provider observation |
| Candidate universe | 52 total: 40 matched plus 12 conditional reserve |
| Durable remote completion signal | 16 `result.json` files observed by existence only |
| Locally harvested evidence signal | 11 aggregate-safe candidate receipts present |
| Liveness/resources | Current heartbeat, active workers, about 243 GiB free disk; no OOM/stall conclusion observed |
| Scientific results | Not canonical. No metric, winner, reserve decision, or claim is reported here. |

The completion counts are live operational telemetry, not a coverage receipt. They cannot be used as a denominator for scientific comparison until the executor safely harvests allowlisted aggregate artifacts and the exact `52/40/12` contract passes.

The repository-wide campaign YAML and Goal 004 frontmatter still describe the
pre-launch preparation state. They are read-model/projection lag, not the
live-attempt authority. This section instead binds its live-status statement to
the v4 authority at
`C:\a2exec-lf\control\armindex\a2\measured-authority\a2-goal004-20260816-005.authority.v4.json`.
The normal projection synchronization occurs only after result-integrity
closeout, so the report does not treat either stale projection as an A2 result.

### A2 Recovery Already Applied

ARM-03 exceeded the former 7,200-second operational timeout while safe liveness diagnostics showed healthy model load and retrieval progress. The recovery changed only the authorized timeout to 21,600 seconds. It did not change batch size, model weights, adapter, candidate bytes, evaluator, metric, decision policy, or representation semantics. Failed/partial lineage remains forensic evidence and cannot be mixed into coverage.

### Required Closeout Before Interpretation

A2 is updateable only after:

1. exact `52/40/12` coverage and five arm-winner receipt hashes;
2. allowlisted aggregate safe return with a hash-bound receipt;
3. terminal checkpoint and worker-reaping evidence;
4. an independent aggregate-only result-integrity audit; and
5. read-model, Obsidian, MLflow, and publication-figure projection checks.

Until then, the correct advisor-facing conclusion is: **A2 is a live controlled execution, not an available finding.**

### A2 Figure Targets

The planned target directory is `outputs/figures/armindex/a2-goal004/`. It is
not created or linked as an artifact until valid closeout. The post-closeout
manifest will provide exact filenames for:

| Planned figure | Reviewer question |
|---|---|
| Coverage and recovery completeness | Was the candidate universe executed and recovered reproducibly? |
| Per-arm quality outcomes | Which per-arm representation result is supported by aggregate evidence? |
| Quality-latency-cost frontier | What is the effectiveness/operational trade-off? |
| Matched versus reserve path | Did the reserve path run, remain dormant, or reveal a boundary result? |
| Appendix provenance and claim boundary | Which receipts support each statement, and what is not claimed? |

## Next Milestones

1. Complete live A2 workers and safe-return aggregate evidence.
2. Validate exact coverage, execute closeout, and run the independent integrity audit.
3. Render the five A2 figures and update this report with receipt-bound outcomes.
4. Start the prepared A3.1 train-headroom diagnostic only after valid A2 closeout. The five-arm A3 bundle is currently `PENDING_A2_CLOSEOUT`.

## Evidence Pointers and Claim Boundary

- [Campaign record, historical projection for the A2 live state](../../control/campaigns/armindex-multiretriever-v2.yaml)
- [A0.9 validation/safety closeout](../../outputs/audits/armindex/a0.9-validation-safety-closeout-20260805.json)
- [A0.10 independent acceptance](../../outputs/audits/rigor/a0.10-legacy-code-harvest-independent-accept-20260804.json)
- [A1 r14 failed-closed audit](../../outputs/audits/armindex/a1.2-v16-r14-instrumentation-failure-20260811.json)
- [A2 Goal 004, execution objective and pre-launch header](../goal/A2_PER_ARM_AUTOINDEX_goal_004.md)
- [A2 execution runbook](../../control/runbooks/A2_PER_ARM_AUTOINDEX_EXECUTION_V2.md)

This is an advisor-facing synthesis of aggregate-safe evidence. A0 is engineering evidence. A1 is REP-DEV development evidence, not Selection or Final confirmation. A2 remains pending receipt-bound closeout. The report makes no legal, infringement, novelty, causal, Selection, or Final claim and contains no protected record-level data.
