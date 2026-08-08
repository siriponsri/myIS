---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "ce1361e9a48dfa1eb327df266d96106aaac7e92ffcf5e3a3ea75739235ad4d8f"
read_model_sha256: "df6cfaf225a55e884ad550ce48bc5afe50131e36490aca6432fd5016a72ea0ec"
source_commit: "2e7a3dc380de47311cdc5e982641925053d45645"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: ["obs-run-candidate-02"]
source_manifest_sha256: ["51208da055a195c812b26b9bbd8fefa9844111634a0fe6d5b5d5ccbb430f52c1","6e5feb92d10e24aa2430e2067cebde0b759b230c4ddc309564dd2453765d3a51"]
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "ce1361e9a48dfa1eb327df266d96106aaac7e92ffcf5e3a3ea75739235ad4d8f"
last_material_update: "2026-08-08T01:48:27Z"
next_authorized_action: "Owner reviews the unchanged v11 request locally. A separate goal may prepare an adoption receipt only after a clean pushed execution commit/tree, Owner-local protected handoff and transfer receipts, 25 validated compiled-program bindings, fresh provider identity and all-fee quote, whole-workload budget admission, and watchdog/destroy checks are available; do not open a provider during this preparation goal."
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-08T01:48:27Z"
updated_at: "2026-08-08T01:48:27Z"
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
