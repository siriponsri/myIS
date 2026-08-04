---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "ab4f9d9dde9c71bd9eb66402c151935a5f57341e3344c841f3cb20c8fd816428"
read_model_sha256: "f64306d71195c5ec15cecf35a174a1075642bf6d673ca24705229673c7e31119"
source_commit: "9b297bd305ceaff9c0f6a2df4f04627eb66aab11"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: ["p1-r0ww-selection-d9533ba623ce"]
source_manifest_sha256: ["8e3e52bf41d49d89f11416b7d9eebaf0cba1be9b2345871c07f152551c386f58"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "ab4f9d9dde9c71bd9eb66402c151935a5f57341e3344c841f3cb20c8fd816428"
last_material_update: "2026-08-03T15:43:42Z"
next_authorized_action: "Complete ArmIndex A0 migration closeout; no measured retrieval"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-03T15:43:42Z"
updated_at: "2026-08-03T15:43:42Z"
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
