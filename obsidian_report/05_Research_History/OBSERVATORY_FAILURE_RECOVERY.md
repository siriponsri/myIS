---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "515a056d2b2df90b3016a312637fc12f75d9c9e28aaad45074fd0e0a392842da"
read_model_sha256: "e6cd5847a88364fdb13238533650eb9d2f171a327e29617673ca275703608289"
source_commit: "eadf27d5559b58fde026ccc624100c7a472ebb33"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: ["obs-run-candidate-02"]
source_manifest_sha256: ["51208da055a195c812b26b9bbd8fefa9844111634a0fe6d5b5d5ccbb430f52c1","6e5feb92d10e24aa2430e2067cebde0b759b230c4ddc309564dd2453765d3a51"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "515a056d2b2df90b3016a312637fc12f75d9c9e28aaad45074fd0e0a392842da"
last_material_update: "2026-08-12T10:43:03Z"
next_authorized_action: "OBTAIN_FRESH_COMPLETE_PROVIDER_QUOTE_TTL_AND_MANAGEMENT_AUTHORITY_THEN_RERUN_ADMISSION_ONLY"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-12T10:43:03Z"
updated_at: "2026-08-12T10:43:03Z"
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
