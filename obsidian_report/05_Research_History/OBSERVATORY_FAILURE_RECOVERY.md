---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "9b2edb07319c69be8d099d563a85527d4e4910624438c8fb38f3f5899ffcd962"
read_model_sha256: "9224c7f5549d443b24fb942836af9a9d88a1df96aa9a1b37e2712c38fe378901"
source_commit: "2e841eeefcfd618cd85d0c902878c1cdc220ee76"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: ["obs-run-candidate-02"]
source_manifest_sha256: ["79fa748b3f807071fbdeb42f871ecd0f2810d3f2837288fd87890e169a7abc7f","7b18c13386951652f0dc25ffa1a20499b5003418c63044ab62a19ce993745400"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-01T15:07:35Z"
updated_at: "2026-08-01T15:07:35Z"
note_id: "OBSERVATORY-FAILURE-RECOVERY"
note_type: "failed_attempt"
phase_id: "P2_SCOPE_DEVELOPMENT"
task_id: "P2.1"
workflow_status: "complete"
evidence_maturity: "fixture"
claim_level: "none"
current_scientific_authority: false
---

# Observatory Failure and Recovery

The synthetic fixture intentionally retained one failed child and its recovery record. The failure did not change real counters or promote an incomplete metric.

- Failed child records: `1`
- Recovery records: `1`
- Negative checks passed: `True`

## Lesson

A failed branch remains useful evidence when the checkpoint, retry action, and claim boundary are recorded together. This is a capture-readiness lesson, not evidence about retrieval quality.
