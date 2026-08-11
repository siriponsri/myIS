---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "8970a6d79ca87ce16d7f1925b5684ce93dd9ccfe9817226cbdb08717122361d7"
read_model_sha256: "37e1915f14effc9c9db7abad73a7fb2876c63489d593342c72ec58c8625b7af9"
source_commit: "485d27ae1ad7d3ca884ffc7c739b6dc616aec0df"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: ["p1-r0-selection-d9533ba623ce"]
source_manifest_sha256: ["6100a8240bcd94ceb5740e805701ea69255a0f2d9e15609b52bc1921c8ae1ff6"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "8970a6d79ca87ce16d7f1925b5684ce93dd9ccfe9817226cbdb08717122361d7"
last_material_update: "2026-08-11T04:06:59Z"
next_authorized_action: "PREPARE_FRESH_A1_SAME_INSTANCE_ADMISSION_AND_RETRY_25_OF_25_BEFORE_A2"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-11T04:06:59Z"
updated_at: "2026-08-11T04:06:59Z"
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
