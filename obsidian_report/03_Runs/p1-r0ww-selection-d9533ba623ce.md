---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "5ec7346f520623d5c21e0ff68ccca82829378d7ee873e0f0d345dc065b997e43"
read_model_sha256: "54dbf7e31279dfb480883ece6cd3d187dbb1dc1bf273ec5f5b55c8cb91dd5332"
source_commit: "aa826e8ee4dc986d0571cfd3a22ce2d646082ff9"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: ["p1-r0ww-selection-d9533ba623ce"]
source_manifest_sha256: ["8e3e52bf41d49d89f11416b7d9eebaf0cba1be9b2345871c07f152551c386f58"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "5ec7346f520623d5c21e0ff68ccca82829378d7ee873e0f0d345dc065b997e43"
last_material_update: "2026-08-12T02:15:10Z"
next_authorized_action: "OWNER_LAUNCH_DOCS_GOAL_A2_WITH_FRESH_PREFLIGHT"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-12T02:15:10Z"
updated_at: "2026-08-12T02:15:10Z"
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
