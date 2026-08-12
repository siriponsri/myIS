---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "5ec7346f520623d5c21e0ff68ccca82829378d7ee873e0f0d345dc065b997e43"
read_model_sha256: "54dbf7e31279dfb480883ece6cd3d187dbb1dc1bf273ec5f5b55c8cb91dd5332"
source_commit: "aa826e8ee4dc986d0571cfd3a22ce2d646082ff9"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: ["obs-run-candidate-02"]
source_manifest_sha256: ["51208da055a195c812b26b9bbd8fefa9844111634a0fe6d5b5d5ccbb430f52c1","6e5feb92d10e24aa2430e2067cebde0b759b230c4ddc309564dd2453765d3a51"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "5ec7346f520623d5c21e0ff68ccca82829378d7ee873e0f0d345dc065b997e43"
last_material_update: "2026-08-12T02:15:10Z"
next_authorized_action: "OWNER_LAUNCH_DOCS_GOAL_A2_WITH_FRESH_PREFLIGHT"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-12T02:15:10Z"
updated_at: "2026-08-12T02:15:10Z"
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

## Captured lineage

- Failure `obs-failure-candidate-02` at `candidate_generation` / class `synthetic_timeout`; checkpoint `candidate-02-start`; counters before/after `{'candidate_count': 1, 'measured_runs': 0, 'selection_accesses': 0, 'shortlist_count': 0}` -> `{'candidate_count': 1, 'measured_runs': 0, 'selection_accesses': 0, 'shortlist_count': 0}`; protected data accessed `False`.
- Recovery `obs-recovery-candidate-02` for `obs-failure-candidate-02`: `retry_from_checkpoint`; validation `passed`; metric promotion `False`; residual risk `No scientific metric promotion`.

## Lesson

A failed branch remains useful evidence when the checkpoint, retry action, and claim boundary are recorded together. This is a capture-readiness lesson, not evidence about retrieval quality.
