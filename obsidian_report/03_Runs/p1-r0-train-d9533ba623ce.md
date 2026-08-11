---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "7963de57b78a03a0dafa3113dd96d3e8a1f2c6a8b4f692d92f92d0c060f8e470"
read_model_sha256: "51d653e98da327d370353c1a54d783783a9291c20a6420f9c82f94528cb2d700"
source_commit: "68308c26f69d97b1cfc9f190a53269afb03201cb"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: ["p1-r0-train-d9533ba623ce"]
source_manifest_sha256: ["31e875e1864cfbf0d7c39cf632b7506e168e753afdc49b7f27ce131d21b4a0f3"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "7963de57b78a03a0dafa3113dd96d3e8a1f2c6a8b4f692d92f92d0c060f8e470"
last_material_update: "2026-08-11T18:35:49Z"
next_authorized_action: "A1_CLOSEOUT_COMPLETE_STOP_BEFORE_A2"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-11T18:35:49Z"
updated_at: "2026-08-11T18:35:49Z"
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
