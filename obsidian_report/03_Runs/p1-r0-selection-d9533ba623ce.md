---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "005e23c20df9060e7f8185b3e9f33143915b9219c5675fb97fb60608a8ba4d22"
read_model_sha256: "67bd40852bb576cec34c8a323027a17f71d60b59269eef4f0852dfc94e9e76b1"
source_commit: "b0963b8c1a5c72bd329d1760d3992ab7f694163b"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: ["p1-r0-selection-d9533ba623ce"]
source_manifest_sha256: ["6100a8240bcd94ceb5740e805701ea69255a0f2d9e15609b52bc1921c8ae1ff6"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "005e23c20df9060e7f8185b3e9f33143915b9219c5675fb97fb60608a8ba4d22"
last_material_update: "2026-08-09T07:04:22Z"
next_authorized_action: "A separately authorized live-provider admission goal may obtain a fresh provider identity and all-fee quote, evaluate live whole-workload budget admission, and materialize a live provider admission receipt while every execution lock remains closed."
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-09T07:04:22Z"
updated_at: "2026-08-09T07:04:22Z"
note_id: "RUN-p1-r0-selection-d9533ba623ce"
note_type: "run_report"
phase_id: "P1_CPU_BASELINE"
task_id: "P1.3"
workflow_status: "complete"
evidence_maturity: "measured_selection"
claim_level: "descriptive"
current_scientific_authority: true
---

# Run Report: p1-r0-selection-d9533ba623ce

## Purpose

This report describes one validated aggregate run slot and its immutable manifest binding.

## Status

Arm `R0`; stage `selection`; status `valid`.

## Output

Manifest SHA-256: `6100a8240bcd94ceb5740e805701ea69255a0f2d9e15609b52bc1921c8ae1ff6`. The safe projection retains aggregate values only.

## Aggregate metrics

- `recall_at_100` / split `selection` / scope `ALL`: `0.196` (n=`125`)
- `recall_at_100` / split `selection` / scope `IN`: `0.233819891725` (n=`121`)
- `recall_at_100` / split `selection` / scope `OUT`: `0.062392548637` (n=`90`)

## Interpretation boundary

This run supports only the declared train/selection aggregate description. It does not expose per-query outcomes or establish final-split generalization.

## Links

[[P1_CPU_BASELINE_MASTER_REPORT]] · [[P1.3]] · [[P1_CPU_BASELINE_RESULT]]
