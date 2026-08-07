---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "9bda9e25522585ac0bab7765907c2d1a5f5f6c673dfc1b9c3b5e31c7feff757b"
read_model_sha256: "46896ba3129b5d286f71a9efb00dc12a59ddfe9eaf397239f2c4776927b3b185"
source_commit: "04475017e348df16dc3bde46d208ad4607c56483"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: ["p1-r0ww-train-d9533ba623ce"]
source_manifest_sha256: ["cb8ee4bfa971146ea80ecbe0c9e4b9b2c17f54f7952cb4b6de436bc2beeb12e1"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "9bda9e25522585ac0bab7765907c2d1a5f5f6c673dfc1b9c3b5e31c7feff757b"
last_material_update: "2026-08-07T15:03:37Z"
next_authorized_action: "/goal Execute A0.8_COMPUTE_AND_STORAGE_FEASIBILITY_FIXTURES from the canonical PLAN and control/campaigns/armindex-multiretriever-v2.yaml. Use synthetic fixtures only; do not access protected data, start measured retrieval, download model weights, use GPU or paid APIs, open Selection, or open Final."
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-07T15:03:37Z"
updated_at: "2026-08-07T15:03:37Z"
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
