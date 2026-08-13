---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "2b7e4d6c66a287d077b65866b6f1f6a78c61e886b4e4f0224ce9589714c3b385"
read_model_sha256: "5a6c11ad31aa2c3c5b7a7a458bba29d763722b617624b7ea96e7b9f279d1a8c3"
source_commit: "a49c545d779eae29d6e14ecee8b492584a235a23"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "2b7e4d6c66a287d077b65866b6f1f6a78c61e886b4e4f0224ce9589714c3b385"
last_material_update: "2026-08-13T11:22:37Z"
next_authorized_action: "AP_VALIDATE_OWNER_LOCAL_PUSHED_HEAD_BUNDLE_AND_DEPLOYMENT_RECEIPT_THEN_FRESH_INSTANCE_ADMISSION_AND_ISOLATED_STAGING"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-13T11:22:37Z"
updated_at: "2026-08-13T11:22:37Z"
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
