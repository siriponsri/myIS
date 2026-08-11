---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "8970a6d79ca87ce16d7f1925b5684ce93dd9ccfe9817226cbdb08717122361d7"
read_model_sha256: "37e1915f14effc9c9db7abad73a7fb2876c63489d593342c72ec58c8625b7af9"
source_commit: "485d27ae1ad7d3ca884ffc7c739b6dc616aec0df"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "8970a6d79ca87ce16d7f1925b5684ce93dd9ccfe9817226cbdb08717122361d7"
last_material_update: "2026-08-11T04:06:59Z"
next_authorized_action: "PREPARE_FRESH_A1_SAME_INSTANCE_ADMISSION_AND_RETRY_25_OF_25_BEFORE_A2"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-11T04:06:59Z"
updated_at: "2026-08-11T04:06:59Z"
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
