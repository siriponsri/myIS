---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "ff9581849d952706188cfba1ab1ba0aee49319c0ccfa36db9c7de4e63daac879"
read_model_sha256: "eb6c6b72fdceb47302a1246c3a0a2672cd6c97df09ebc2663b4bd2d1e8cbba35"
source_commit: "0ec3eaaeed6229bb6d1f671ab3286a9c26550623"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "ff9581849d952706188cfba1ab1ba0aee49319c0ccfa36db9c7de4e63daac879"
last_material_update: "2026-08-22T15:21:39Z"
next_authorized_action: "RUN_SEVEN_LAYER_DIAGNOSIS_ON_HASH_BOUND_A6_POOL"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-22T15:21:39Z"
updated_at: "2026-08-22T15:21:39Z"
note_id: "FAILED-ATTEMPTS"
note_type: "failed_attempt"
phase_id: "P1_CPU_BASELINE"
task_id: "P1.3"
workflow_status: "complete"
evidence_maturity: "historical_exposed"
claim_level: "none"
retry_allowed: true
---

# Historical Invalid Attempt

## What was tried

A legacy aggregate P1 receipt was retained.

## Failure category

It lacks the hash-bound four-slot manifest and validation-report matrix required for promotion.

## Lesson

Historical aggregate evidence remains traceable but cannot override canonical run facts.

## Retry

A fresh Owner-local CPU P1 run may proceed only through the existing approved envelope.
