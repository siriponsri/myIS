---
title: "ArmIndex Progress Update"
audience: "Academic advisor"
language: "English"
as_of: "2026-08-19"
status: "A0-A2 complete; A3 measurement in progress (12/14 returned); A4 locked pending A3 audit"
evidence_boundary: "Summary controls, A1/A2 evidence, and A3 operational launch records only."
---

# ArmIndex Progress Update

## Communication Goal

By the end, an academic advisor should understand that ArmIndex has completed
an auditable A0-A2 development sequence and has begun, but not yet concluded,
the A3 transfer measurement.

## Main Deck

### 1. ArmIndex Progress Update

**On slide**

- Retriever-specific document representation search for cross-domain patent retrieval
- A0-A2 complete; A3 measurement in progress
- 19 August 2026

**Speaker notes**

The central question is whether the best deterministic representation of a
patent family depends on the retriever. This update reports completed evidence
through A2 and the current operational state of A3. It does not present A3
results.

[Sources]
- `docs/research/ARMINDEX_RESEARCH_PLAN_V02.md`
- `docs/goal/A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT_goal_003.md`

### 2. A0-A3 advances to transfer measurement

**On slide**

- A0: reproducibility and protected-data controls
- A1: five document representations across five predefined retrievers
- A2: constrained representation search for each retriever
- A3: transfer and retriever-combination measurement is running

**Speaker notes**

Each phase has a distinct role. A0 establishes reproducibility. A1 tests the
common comparison. A2 conducts constrained representation search for each
retriever.
A3 now asks whether the selected representations transfer and whether combining
retrievers adds useful coverage under operational constraints.

[Sources]
- `docs/progress_report/update_A0_A1_A2_18AUG2026.md`
- `docs/goal/A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT_goal_003.md`

### 3. A0 separates development from future confirmation

**On slide**

- Development uses predefined roles within Train-250
- Later selection and final confirmation remain closed
- This prevents adaptive work from reaching confirmation data

**Speaker notes**

The study keeps representation development and later harness development
separate. Selection and final confirmation have not been opened. The figure
shows role separation only; it exposes no protected membership or relevance
labels.

[Sources]
- `docs/progress_report/update_A0_A1_A2_18AUG2026.md`
- `docs/progress_report/figures/a1-development-role-split.png`

### 4. A1 and A2 establish complete development evidence

**On slide**

- A1 completed the five-by-five common comparison
- A2 has complete accounting: 52 = 44 measured + 8 dormant
- Dormant means not admitted for evaluation, not failure or zero performance

**Speaker notes**

A1 measured five fixed representations across five predefined retrieval arms. A2
then searched its predefined candidate set independently for each arm. All 52
authorized candidate slots are accounted for: 44 were measured and eight
conditional reserves were dormant. The distinction is important because a
dormant reserve is not a missing or null result.

[Sources]
- `docs/progress_report/update_A0_A1_A2_18AUG2026.md`
- `docs/progress_report/figures/a2-coverage-recovery.png`

### 5. A2 advances three retrievers to A3

**On slide**

- Primary A3 inputs: ARM-03 PatEmbed, ARM-04 Arctic Embed, ARM-05 Qwen3 Embedding
- ARM-01 BM25 and ARM-02 BGE-M3 are retained for interpretation but do not advance
- The decision preserves ties and no-gain outcomes instead of selecting only positive results

**Speaker notes**

ARM-03, ARM-04, and ARM-05 are the only A3 inputs. ARM-01 and ARM-02 had
three-way top ties without a unique winner and remain useful interpretation
evidence. ARM-04 is the strict A2 improvement; ARM-03 is a numerical tie at
reported precision; ARM-05 is retained without a strict A2 improvement to
avoid selecting only positive outcomes.

[Sources]
- `docs/goal/A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT_goal_003.md`
- `docs/progress_report/A2_per_arm_autoindex_outcomes_eda_20260818.csv`
- `docs/progress_report/figures/a2-per-arm-outcomes.png`

### 6. A3 is running; conclusions await a result audit

**On slide**

- Current run: stage 028 launched 14 of 14 operations; 12 return receipts are collected and two fixed controls remain active
- Scope: transfer and fixed combination controls for ARM-03, ARM-04, and ARM-05
- Measurement is in progress; no A3 scientific result is available yet
- A4 remains locked until complete results and execution records are audited

**Speaker notes**

Stage 028 launched all nine transfer operations and five fixed combination-control
operations. Twelve return receipts are collected and two fixed controls remain
active. Launch and receipt collection are operational facts, not performance
results. The next valid conclusion requires completed evidence collection,
protected local evaluation, completeness checks, and a result-integrity audit. A4
has no current authorization to proceed.

[Sources]
- `docs/goal/A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT_goal_003.md`
- `../04_Owner_Stores/armindex/a3/a3-goal003-20260818-028-launch-receipts/` (aggregate receipt count only)

## Quality-Control Note

The deck contains six slides, one core point per slide, speaker notes with
source blocks, English-only visible copy, and only summary figures.
Its final slide explicitly prevents interpreting an operational launch as an
A3 result.
