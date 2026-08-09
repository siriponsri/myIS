---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "1a68cb9dad77ebac2e2420117992c1c3a2a7c813fbcd7660ba181526e2345f62"
read_model_sha256: "8fda366b47c292d04c5e4b0217f0307a0953356da2e98c494f9bd433a43cb55d"
source_commit: "2bd76d36b418564b9f7494196e70a31251b552fb"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: ["p1-r0ww-train-d9533ba623ce"]
source_manifest_sha256: ["cb8ee4bfa971146ea80ecbe0c9e4b9b2c17f54f7952cb4b6de436bc2beeb12e1"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "1a68cb9dad77ebac2e2420117992c1c3a2a7c813fbcd7660ba181526e2345f62"
last_material_update: "2026-08-09T04:38:15Z"
next_authorized_action: "A separately authorized live-provider admission goal may obtain a fresh provider identity and all-fee quote, evaluate live whole-workload budget admission, and materialize a live provider admission receipt while every execution lock remains closed."
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-09T04:38:15Z"
updated_at: "2026-08-09T04:38:15Z"
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
