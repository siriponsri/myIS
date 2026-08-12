---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "5ec7346f520623d5c21e0ff68ccca82829378d7ee873e0f0d345dc065b997e43"
read_model_sha256: "54dbf7e31279dfb480883ece6cd3d187dbb1dc1bf273ec5f5b55c8cb91dd5332"
source_commit: "aa826e8ee4dc986d0571cfd3a22ce2d646082ff9"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
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
note_id: "A4_PRODUCTION_TRANSFER_AND_SELECTION-MASTER"
note_type: "phase_report"
phase_id: "A4_PRODUCTION_TRANSFER_AND_SELECTION"
task_id: null
workflow_status: "blocked"
evidence_maturity: "non_scientific"
claim_level: "none"
---

# A4_PRODUCTION_TRANSFER_AND_SELECTION

Generated from the validated report record. Manual edits may be replaced; use the separate Owner Notes area for personal annotations.

## Objective

Freeze FAST/BALANCED/DEEP profiles and expose Selection once.

## Starting State

- `phase`: A2_PER_ARM_AUTOINDEX
- `task`: None
- `program_state`: a2_candidate_freeze_audit_passed_measured_a2_closed
- `authorization`: D1_START_CAMPAIGN; D2/D3 remain Owner-only
- `claim_boundary`: No unsupported scientific claim

## Inputs and Frozen Bindings

- `source_of_truth`: `control/source-of-truth.yaml`; SHA-256 `2f5e191ca969679157054781a1703cb7e2e028c8a52ee366ec8619747940e66a`
- `campaign`: `control/campaigns/armindex-multiretriever-v2.yaml`; SHA-256 `b8b5c85d7deafe0d20cef1b5d9da0ac4a7e8300cf4f61696ffa9fa2eb43a06de`
- `git_commit`: aa826e8ee4dc986d0571cfd3a22ce2d646082ff9
- `migration_budget`: `control/budgets/armindex-migration-v2.yaml`; SHA-256 `48bab215d10ef82c0fe8206702f75f4b212df12792d7475131888d50161821ec`
- `armindex_schema_root`: `schemas/armindex`; SHA-256 `6ede89f83141bf4f051413feedf5316388defe5565051a53eaed386c4c62320a`
- `historical_scope`: `control/campaigns/scope-autoindex-v1.yaml`; SHA-256 `a86d73657988713d62ddfb12c9c01da367af2e97922363233ef8cd453fb20ce9`

## Work Performed

The active repository is migrated in place to ArmIndex with versioned contracts and projections while historical SCOPE/P1/P2 evidence remains immutable and readable.

## Artifacts Produced

These references explain what each artifact is for; the bytes remain governed by canonical paths.

| Artifact | Type | Evidence | Safe URI | SHA-256 | Validation |
|---|---|---|---|---|---|
| None | - | - | - | - | - |

## Metrics

| Metric | Split | Scope | Value | n | Denominator | Evidence |
|---|---|---|---:|---:|---|---|
| No measured metric is available | - | - | - | - | - | planned/fixture |

Fixture values are synthetic engineering diagnostics and are never reported as measured performance.

## Result

**Output:** Versioned ArmIndex control, schema, code, and projection state with historical SCOPE/P1 evidence preserved by pointer.

**Result:** A4_PRODUCTION_TRANSFER_AND_SELECTION is blocked; ArmIndex measured runs, Selection, and Final counters remain zero.

**Decision:** blocked

## Interpretation

This is engineering migration provenance only and supports no retrieval-quality, champion, or production claim.

## Supported Claims

- Versioned ArmIndex control, schema, code, and projection state with historical SCOPE/P1 evidence preserved by pointer.

## Unsupported Claims

- Measured P2 improvement or candidate superiority before a real measured run.
- Final-split generalization or publication release before D2 and D3.
- Causal or legal conclusions from retrieval aggregates.

## Failures and Recovery

- No material failure is recorded for this Phase or Task.

## Governance and Safety

- `protected_data_accessed`: False
- `measured_execution`: False
- `gpu`: False
- `paid_api`: False
- `network_model_download`: False
- `provider_fallback`: False
- `d2`: waiting_owner
- `d3`: waiting_owner
- `final_split`: closed
- `real_counters`: `{"candidate_count": 0, "final_accesses": 0, "measured_runs": 1, "selection_accesses": 0, "shortlist_count": 0}`
- `evidence_class`: engineering
- `scientific_authority`: False

## Decision

Status: **blocked**. A4_PRODUCTION_TRANSFER_AND_SELECTION is blocked; ArmIndex measured runs, Selection, and Final counters remain zero.

## Next Action

OWNER_LAUNCH_DOCS_GOAL_A2_WITH_FRESH_PREFLIGHT

Measured P2, real selection, and final evaluation must not start automatically from this report.

## Evidence Links

- None recorded.
