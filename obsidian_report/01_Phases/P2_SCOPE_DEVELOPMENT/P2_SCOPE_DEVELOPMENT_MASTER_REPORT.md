---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "7ee1c6cde26a369c94fe77300cafdcc172c0b16fa9f026941c360b790e409510"
read_model_sha256: "895f0250d3dbe78d7fc42075bfd55cb79bf3fff3485889f4fa1595fe8c4c8620"
source_commit: "543ee2428a6ff5b1c403914573908a78a380efad"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: ["U006","U011","U154"]
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-01T07:54:27Z"
updated_at: "2026-08-01T07:54:27Z"
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

## Budget and runtime

| Check | Value |
|---|---|
| Status | ready_planned_not_measured |
| Profile | p2-r1-primary-v1 / d5d9d48d8a754168b257367493b8e65fbfcfefc1901408c96336e524c6308e4c |
| Candidates | 0 / 32 |
| Runtime | 259200 wall seconds; 10800 per candidate |
| Freeze | not_started; selection 0/1 |
| Resources | GPU 0 USD; paid API 0 USD; model download False |

## Why these methods

`R0` uses one full TAC document per patent family and BM25 to isolate the representation question with a transparent lexical comparator; the DAPFAM protocol and patent-retrieval context are references U011 and U006 in [[LITERATURE_INDEX]]. `R0-W` keeps BM25 and family-level evaluation fixed but splits text into non-overlapping 512-token windows and uses family MaxP, testing whether passage granularity changes exposure (U154). `R1` is the planned patent-native SCOPE/AutoIndex representation-program search, evaluated with the same retriever/evaluator so any gain can be attributed to representation rather than a new dense model (U154 on the DAPFAM protocol U011). No dense model, LLM, paid API, or provider is part of this P2 arm.

## Internal freeze barrier

Baseline reproduction, candidate generation, and train evaluation must pass before the immutable shortlist receipt. Selection may open once, only for that frozen shortlist. Ties reject; any baseline, train, or freeze validation failure stops before selection.

## Outputs and evidence

The canonical profile, P2 execution envelope, request schema, candidate ledger, freeze receipt, selection receipt, manifest, and package schemas are the source surfaces. No fixture or dashboard preview is scientific evidence.

## What is measured

Not measured. Current P2 measured runs = `0`; selection accesses = `0`; GPU, paid API, network model download, and provider fallback = disabled.

## Read-model binding

Revision: `7ee1c6cde26a369c94fe77300cafdcc172c0b16fa9f026941c360b790e409510`

## Next action

Run the repository-only fixture/pilot preflight, then stop for Owner review before any measured request.

Links: [[P2.1]] · [[P2_SCOPE_DEVELOPMENT_RESULT]] · [[P1_CPU_BASELINE_RESULT]]
