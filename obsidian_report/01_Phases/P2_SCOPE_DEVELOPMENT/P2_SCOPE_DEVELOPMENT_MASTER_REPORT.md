---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "2be6b1dc61b4c0d94e9269d9406c230e6c8e1c25c38a661f37162707923aa146"
read_model_sha256: "972d9be25a18265558c6de7f3a6f705101912e3a0adec6d78a1adae7cb1e4fe9"
source_commit: "be543b83c05aee19f04aa73aacde42866b8333d8"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: ["U006","U011","U154"]
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-01T12:44:19Z"
updated_at: "2026-08-01T12:44:19Z"
note_id: "P2_SCOPE_DEVELOPMENT-MASTER"
note_type: "phase_report"
phase_id: "P2_SCOPE_DEVELOPMENT"
task_id: null
workflow_status: "ready"
evidence_maturity: "non_scientific"
claim_level: "none"
---

# P2_SCOPE_DEVELOPMENT

P2 คือช่วงพัฒนา R1 SCOPE/AutoIndex แบบ reversible และ CPU-only. ตอนนี้เป็น readiness/planned เท่านั้น ยังไม่มี measured P2 run.

## Status for Owner

**ready_planned_not_measured**. P1 remains `P1_CPU_MEASURED_COMPLETE`; P3 and P4 remain locked.

## Official static review

Round `3` verdict is **accept** with status `accepted_static_contract_review`. This static review remains engineering provenance only. See [[P2_OFFICIAL_REVIEW_AUDIT]].

## Repository-only fixture pilot

Fixture status is **passed** with evidence class `fixture` and scientific authority `False`. Synthetic lifecycle counts are kept separate from real campaign counters. See [[P2_FIXTURE_PILOT]].

## Budget and runtime

| Check | Value |
|---|---|
| Status | ready_planned_not_measured |
| Official static review | Round 3 accept / accepted_static_contract_review |
| Fixture pilot | passed / fixture / scientific authority False |
| Synthetic lifecycle | 32 candidates; 5 iterations; shortlist 4; fixture selection 1 |
| Profile | p2-r1-primary-v1 / d5d9d48d8a754168b257367493b8e65fbfcfefc1901408c96336e524c6308e4c |
| Real candidates | 0 / 32 |
| Real shortlist | 0 / 4 |
| Runtime | 259200 wall seconds; 10800 per candidate |
| Real freeze / selection | not_started; 0/1 |
| Protected access | False |
| Scientific claim | no_measured_claim |
| Resources | GPU 0 USD; paid API 0 USD; model download False |
| Next step | Owner-local measured preflight |

## Why these methods

`R0` uses one full TAC document per patent family and BM25 to isolate the representation question with a transparent lexical comparator; the DAPFAM protocol and patent-retrieval context are references U011 and U006 in [[LITERATURE_INDEX]]. `R0-W` keeps BM25 and family-level evaluation fixed but splits text into non-overlapping 512-token windows and uses family MaxP, testing whether passage granularity changes exposure (U154). `R1` is the planned patent-native SCOPE/AutoIndex representation-program search, evaluated with the same retriever/evaluator so any gain can be attributed to representation rather than a new dense model (U154 on the DAPFAM protocol U011). No dense model, LLM, paid API, or provider is part of this P2 arm.

## Internal freeze barrier

Baseline reproduction, candidate generation, and train evaluation must pass before the immutable shortlist receipt. Selection may open once, only for that frozen shortlist. Ties reject; any baseline, train, or freeze validation failure stops before selection.

## Outputs and evidence

The canonical profile, P2 execution envelope, request schema, candidate ledger, freeze receipt, selection receipt, manifest, and package schemas are the source surfaces. No fixture or dashboard preview is scientific evidence.

## What is measured

Not measured. Current P2 measured runs = `0`; selection accesses = `0`; GPU, paid API, network model download, and provider fallback = disabled.

## Read-model binding

Revision: `2be6b1dc61b4c0d94e9269d9406c230e6c8e1c25c38a661f37162707923aa146`

## Next action

The static contract and repository-only fixture are complete. The next authorized action is Owner-local measured preflight; measured P2 and real selection remain closed until that separate action begins.

Links: [[P2.1]] · [[P2_SCOPE_DEVELOPMENT_RESULT]] · [[P2_OFFICIAL_REVIEW_AUDIT]] · [[P1_CPU_BASELINE_RESULT]]
