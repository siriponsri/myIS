---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "8c49d51c8e07abd471d5f06dfc907203db8f6fcb9535adc46be5e9bc3b60ee8c"
read_model_sha256: "cb00dd6e1b06105398aedf981442a055e6b6771fd57925334eccfd9a725f97f5"
source_commit: "374e0a8070452de67a0b72fe29fe464914627264"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: ["p1-r0ww-train-d9533ba623ce"]
source_manifest_sha256: ["cb8ee4bfa971146ea80ecbe0c9e4b9b2c17f54f7952cb4b6de436bc2beeb12e1"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "8c49d51c8e07abd471d5f06dfc907203db8f6fcb9535adc46be5e9bc3b60ee8c"
last_material_update: "2026-08-12T10:50:19Z"
next_authorized_action: "OBTAIN_FRESH_COMPLETE_PROVIDER_QUOTE_TTL_AND_MANAGEMENT_AUTHORITY_THEN_RERUN_ADMISSION_ONLY"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-12T10:50:19Z"
updated_at: "2026-08-12T10:50:19Z"
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
