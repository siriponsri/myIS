---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "61468630fae46b5136a4f82479451bda38358fe17ab082d9bf179d6234f08b8b"
read_model_sha256: "944697aa79079bfbfcbfaa0c0ab7ed05595c25debfbc60e77777b6ecdad7d1de"
source_commit: "62b253a7c2fdc65fd807bafcca8f5af9fb971c7f"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "61468630fae46b5136a4f82479451bda38358fe17ab082d9bf179d6234f08b8b"
last_material_update: "2026-08-07T13:00:35Z"
next_authorized_action: "Prepare a separately authorized A1.2 scientific execution and adoption goal on local CPU only; do not open a provider or begin measured work."
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-07T13:00:35Z"
updated_at: "2026-08-07T13:00:35Z"
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

- `phase`: A1_BASELINES_AND_MULTI_ARM_SCREENING
- `task`: None
- `program_state`: a1_2_live_synthetic_preflight_closed_provider_destroyed_launch_locked
- `authorization`: D1_START_CAMPAIGN; D2/D3 remain Owner-only
- `claim_boundary`: No unsupported scientific claim

## Inputs and Frozen Bindings

- `source_of_truth`: `control/source-of-truth.yaml`; SHA-256 `4fe61d7f00696a0b878be476abd95c0c4ee6027f7e23444ae6712d944e4ab6a3`
- `campaign`: `control/campaigns/armindex-multiretriever-v2.yaml`; SHA-256 `c163f475750110db8d4cd76c11d73eefc6ff93b2f21db1ff6fef2397b9cac879`
- `git_commit`: 62b253a7c2fdc65fd807bafcca8f5af9fb971c7f
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
- `real_counters`: `{"candidate_count": 0, "final_accesses": 0, "measured_runs": 0, "selection_accesses": 0, "shortlist_count": 0}`
- `evidence_class`: engineering
- `scientific_authority`: False

## Decision

Status: **blocked**. A4_PRODUCTION_TRANSFER_AND_SELECTION is blocked; ArmIndex measured runs, Selection, and Final counters remain zero.

## Next Action

Prepare a separately authorized A1.2 scientific execution and adoption goal on local CPU only; do not open a provider or begin measured work.

Measured P2, real selection, and final evaluation must not start automatically from this report.

## Evidence Links

- None recorded.
