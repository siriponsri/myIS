---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "4e46e4a7d87dca88a53ef2e6d9a9ecd590cf4241ccb6b54bf08c94df9840d2dd"
read_model_sha256: "e6614bc79e9a6cf663f3c50d7015f05693c9d9d0215bfdb6569a79a4e5cc0580"
source_commit: "0d4a51a81d411cff0e70baf293e8edc9dd0dba85"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: ["p1-r0ww-selection-d9533ba623ce"]
source_manifest_sha256: ["8e3e52bf41d49d89f11416b7d9eebaf0cba1be9b2345871c07f152551c386f58"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "4e46e4a7d87dca88a53ef2e6d9a9ecd590cf4241ccb6b54bf08c94df9840d2dd"
last_material_update: "2026-08-12T13:08:25Z"
next_authorized_action: "IMPLEMENT_PRODUCTION_A2_ADAPTER_AND_MATCHED_FIRST_CONDITIONAL_RESERVE_LIFECYCLE"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-12T13:08:25Z"
updated_at: "2026-08-12T13:08:25Z"
note_id: "RUN-p1-r0ww-selection-d9533ba623ce"
note_type: "run_report"
phase_id: "P1_CPU_BASELINE"
task_id: "P1.3"
workflow_status: "complete"
evidence_maturity: "measured_selection"
claim_level: "descriptive"
current_scientific_authority: true
---

# Run Report: p1-r0ww-selection-d9533ba623ce

## Purpose

This report describes one validated aggregate run slot and its immutable manifest binding.

## Status

Arm `R0-W`; stage `selection`; status `valid`.

## Output

Manifest SHA-256: `8e3e52bf41d49d89f11416b7d9eebaf0cba1be9b2345871c07f152551c386f58`. The safe projection retains aggregate values only.

## Aggregate metrics

- `recall_at_100` / split `selection` / scope `ALL`: `0.214` (n=`125`)
- `recall_at_100` / split `selection` / scope `IN`: `0.260759203902` (n=`121`)
- `recall_at_100` / split `selection` / scope `OUT`: `0.074661067156` (n=`90`)

## Interpretation boundary

This run supports only the declared train/selection aggregate description. It does not expose per-query outcomes or establish final-split generalization.

## Links

[[P1_CPU_BASELINE_MASTER_REPORT]] · [[P1.3]] · [[P1_CPU_BASELINE_RESULT]]
