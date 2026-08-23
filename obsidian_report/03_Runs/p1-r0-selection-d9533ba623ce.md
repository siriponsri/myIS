---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "ff9581849d952706188cfba1ab1ba0aee49319c0ccfa36db9c7de4e63daac879"
read_model_sha256: "eb6c6b72fdceb47302a1246c3a0a2672cd6c97df09ebc2663b4bd2d1e8cbba35"
source_commit: "0ec3eaaeed6229bb6d1f671ab3286a9c26550623"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: ["p1-r0-selection-d9533ba623ce"]
source_manifest_sha256: ["6100a8240bcd94ceb5740e805701ea69255a0f2d9e15609b52bc1921c8ae1ff6"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "ff9581849d952706188cfba1ab1ba0aee49319c0ccfa36db9c7de4e63daac879"
last_material_update: "2026-08-22T15:21:39Z"
next_authorized_action: "RUN_SEVEN_LAYER_DIAGNOSIS_ON_HASH_BOUND_A6_POOL"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-22T15:21:39Z"
updated_at: "2026-08-22T15:21:39Z"
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
