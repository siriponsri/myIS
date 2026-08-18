---
title: "ArmIndex Progress Update"
audience: "Academic advisor"
language: "English"
as_of: "2026-08-19"
status: "A0-A3 complete; result-integrity audit passed; A4 locked pending Owner gate"
evidence_boundary: "Summary controls, A1/A2 evidence, and A3 aggregate-safe result records only."
---

# ArmIndex Progress Update

## Communication Goal

By the end, an academic advisor should understand that ArmIndex has completed
an auditable A0-A3 development sequence. A3 has a valid aggregate-only result
audit; A4 remains gated.

## Main Deck

### 1. ArmIndex Progress Update

**On slide**

- Retriever-specific document representation search for cross-domain patent retrieval
- A0-A3 complete; result-integrity audit passed
- 19 August 2026

**Speaker notes**

The central question is whether the best deterministic representation of a
patent family depends on the retriever. This update reports completed evidence
through A3 and keeps production and confirmation claims closed.

[Sources]
- `docs/research/ARMINDEX_RESEARCH_PLAN_V02.md`
- `docs/goal/A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT_goal_003.md`

### 2. A0-A3 advances to transfer measurement

**On slide**

- A0: reproducibility and protected-data controls
- A1: five document representations across five predefined retrievers
- A2: constrained representation search for each retriever
- A3: transfer and retriever-combination evidence is audited

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

### 6. A3 result audit: transfer is adapter-dependent

**On slide**

- Stage 028 completed 14 of 14 operations and passed result-integrity audit
- Scope: 9 transfer cells and 5 fixed combination controls for ARM-03, ARM-04, and ARM-05
- Best transfer: ARM-05 winner program to ARM-03 adapter, OUT Recall@100 0.419274
- Best fixed control: top-two RRF-60, OUT Recall@100 0.418715; HarnessOpt surface is flat
- A4 remains locked; Selection and Final remain closed

**Speaker notes**

Stage 028 completed all nine transfer operations and five fixed combination-control
operations. Every operation covered Train-250 (250/250 units), and the independent
aggregate-only result-integrity audit passed. Transfer quality depends on the
target adapter; the top-two fixed union is the strongest fixed control, while the
all-primary union is lower. HarnessOpt produced a flat-surface stop, not an
adaptive improvement claim. A4 has no current authorization to proceed.

[Sources]
- `docs/goal/A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT_goal_003.md`
- `docs/progress_report/update_A3_19AUG2026.md`
- `docs/progress_report/figures/a3-transfer-recall-heatmap-20260819.png`

## Quality-Control Note

The deck contains six slides, one core point per slide, speaker notes with
source blocks, English-only visible copy, and only summary figures.
Its final slide reports audited aggregate evidence and explicitly prevents
interpreting it as Selection, Final, or production evidence.
