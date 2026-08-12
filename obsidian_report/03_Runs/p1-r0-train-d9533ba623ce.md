---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "da7598fb59cd3f16150cfff8b246906439a11fbe97981926d2fa636cb0680f73"
read_model_sha256: "7bdecffb3521d83744069331d13b051fecaf386b548dd0f5683e4e8f70d38f1d"
source_commit: "0d4a51a81d411cff0e70baf293e8edc9dd0dba85"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: ["p1-r0-train-d9533ba623ce"]
source_manifest_sha256: ["31e875e1864cfbf0d7c39cf632b7506e168e753afdc49b7f27ce131d21b4a0f3"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "da7598fb59cd3f16150cfff8b246906439a11fbe97981926d2fa636cb0680f73"
last_material_update: "2026-08-12T13:08:25Z"
next_authorized_action: "IMPLEMENT_PRODUCTION_A2_ADAPTER_AND_MATCHED_FIRST_CONDITIONAL_RESERVE_LIFECYCLE"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-12T13:08:25Z"
updated_at: "2026-08-12T13:08:25Z"
note_id: "RUN-p1-r0-train-d9533ba623ce"
note_type: "run_report"
phase_id: "P1_CPU_BASELINE"
task_id: "P1.3"
workflow_status: "complete"
evidence_maturity: "measured_selection"
claim_level: "descriptive"
current_scientific_authority: true
---

# Run Report: p1-r0-train-d9533ba623ce

## Purpose

This report describes one validated aggregate run slot and its immutable manifest binding.

## Status

Arm `R0`; stage `train`; status `valid`.

## Output

Manifest SHA-256: `31e875e1864cfbf0d7c39cf632b7506e168e753afdc49b7f27ce131d21b4a0f3`. The safe projection retains aggregate values only.

## Aggregate metrics

- `recall_at_100` / split `train` / scope `ALL`: `0.2162` (n=`250`)
- `recall_at_100` / split `train` / scope `IN`: `0.258622280076` (n=`247`)
- `recall_at_100` / split `train` / scope `OUT`: `0.076057227485` (n=`179`)

## Interpretation boundary

This run supports only the declared train/selection aggregate description. It does not expose per-query outcomes or establish final-split generalization.

## Links

[[P1_CPU_BASELINE_MASTER_REPORT]] · [[P1.3]] · [[P1_CPU_BASELINE_RESULT]]
