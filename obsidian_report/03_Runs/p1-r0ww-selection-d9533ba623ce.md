---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "728c53f999772c296885f46589ee5ab30680483663d7edd115dd9add35e8c769"
read_model_sha256: "a6313c65aa7617a4dd6e29d048ca128d2ea4c20a8d493945177737d622f5bfb8"
source_commit: "82ca6be739beab4c3561d3c75cfc81b0acfb0da2"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: ["p1-r0ww-selection-d9533ba623ce"]
source_manifest_sha256: ["8e3e52bf41d49d89f11416b7d9eebaf0cba1be9b2345871c07f152551c386f58"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "728c53f999772c296885f46589ee5ab30680483663d7edd115dd9add35e8c769"
last_material_update: "2026-08-15T10:55:31Z"
next_authorized_action: "OWNER_AUTHORIZE_EXACT_ROOT_RECOVERY_ON_47782993_OR_DESTROY_THEN_CREATE_A2_ATTEMPT"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-15T10:55:31Z"
updated_at: "2026-08-15T10:55:31Z"
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
