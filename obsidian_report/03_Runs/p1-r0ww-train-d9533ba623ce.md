---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "6dbb1ccd555cfe39e52a3c6e16414da3d6fe2875127cc046e83b29b5fe560ff7"
read_model_sha256: "837b6e327f12b9273f6bee55d1d185fd946245f02ce62dd9d107a4449233b5ff"
source_commit: "69644e66678776dd15f0976974cf6576462eb209"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: ["p1-r0ww-train-d9533ba623ce"]
source_manifest_sha256: ["cb8ee4bfa971146ea80ecbe0c9e4b9b2c17f54f7952cb4b6de436bc2beeb12e1"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "6dbb1ccd555cfe39e52a3c6e16414da3d6fe2875127cc046e83b29b5fe560ff7"
last_material_update: "2026-08-17T21:26:45Z"
next_authorized_action: "LOCATE_OR_OBTAIN_AN_OWNER_AUTHORIZED_HASH_BOUND_TRAIN_250_QUERY_CORPUS_AND_EVALUATOR_PACKAGE_BEFORE_A3_ADMISSION"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-17T21:26:45Z"
updated_at: "2026-08-17T21:26:45Z"
note_id: "RUN-p1-r0ww-train-d9533ba623ce"
note_type: "run_report"
phase_id: "P1_CPU_BASELINE"
task_id: "P1.3"
workflow_status: "complete"
evidence_maturity: "measured_selection"
claim_level: "descriptive"
current_scientific_authority: true
---

# Run Report: p1-r0ww-train-d9533ba623ce

## Purpose

This report describes one validated aggregate run slot and its immutable manifest binding.

## Status

Arm `R0-W`; stage `train`; status `valid`.

## Output

Manifest SHA-256: `cb8ee4bfa971146ea80ecbe0c9e4b9b2c17f54f7952cb4b6de436bc2beeb12e1`. The safe projection retains aggregate values only.

## Aggregate metrics

- `recall_at_100` / split `train` / scope `ALL`: `0.243` (n=`250`)
- `recall_at_100` / split `train` / scope `IN`: `0.287953506066` (n=`247`)
- `recall_at_100` / split `train` / scope `OUT`: `0.085847360337` (n=`179`)

## Interpretation boundary

This run supports only the declared train/selection aggregate description. It does not expose per-query outcomes or establish final-split generalization.

## Links

[[P1_CPU_BASELINE_MASTER_REPORT]] · [[P1.3]] · [[P1_CPU_BASELINE_RESULT]]
