---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "a03d1e12dc207826c87d964033a2f7ffb9eda892e4c1e0c37d901358355528f0"
read_model_sha256: "fecaf2addcac00e95d9c7be0f268b834ef2171b1d72bc7b9afbdb1fcd1342d52"
source_commit: "713b9be785705181960d06920b804b7757fb9d31"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: ["p1-r0-selection-d9533ba623ce"]
source_manifest_sha256: ["6100a8240bcd94ceb5740e805701ea69255a0f2d9e15609b52bc1921c8ae1ff6"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "a03d1e12dc207826c87d964033a2f7ffb9eda892e4c1e0c37d901358355528f0"
last_material_update: "2026-08-17T14:35:47Z"
next_authorized_action: "LOCATE_OR_OBTAIN_AN_OWNER_AUTHORIZED_HASH_BOUND_TRAIN_250_QUERY_CORPUS_AND_EVALUATOR_PACKAGE_BEFORE_A3_ADMISSION"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-17T14:35:47Z"
updated_at: "2026-08-17T14:35:47Z"
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
