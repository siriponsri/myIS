---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "3ebeb9054849cc287b756773368c572b06a7d205bc25ff29c361a7e819cf9d43"
read_model_sha256: "7f430f951c8600955f0b3c5a60d3a7060ef8df5c7120a9ab7926518802d658da"
source_commit: "1149f9e63ac6174a3ce4bc5a553d793b7d707b0b"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "3ebeb9054849cc287b756773368c572b06a7d205bc25ff29c361a7e819cf9d43"
last_material_update: "2026-08-05T15:56:15Z"
next_authorized_action: "/goal Run only the Owner-local SSH/Vast A1.2 preflight from docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK.md on one disposable four-RTX3090 instance. Verify the unchanged v2 commit, tree, image digest, four GPU UUIDs, locked runtime and model bytes, adapter parity, Qwen maximum length, local protected-root boundary, live USD quote, heartbeat/resume, safe return path, and provider destroy/TTL path. Keep launch_allowed=false and adopted_for_execution=false; do not start measured retrieval, optimization, Selection, Final, paid API work, or weight changes."
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-05T15:56:15Z"
updated_at: "2026-08-05T15:56:15Z"
note_id: "A2_PER_ARM_AUTOINDEX-MASTER"
note_type: "phase_report"
phase_id: "A2_PER_ARM_AUTOINDEX"
task_id: null
workflow_status: "blocked"
evidence_maturity: "non_scientific"
claim_level: "none"
---

# A2_PER_ARM_AUTOINDEX

Generated from the validated report record. Manual edits may be replaced; use the separate Owner Notes area for personal annotations.

## Objective

Search and freeze one representation program per promoted arm.

## Starting State

- `phase`: A1_BASELINES_AND_MULTI_ARM_SCREENING
- `task`: None
- `program_state`: a1_2_vast_4x3090_preflight_prepared_launch_locked
- `authorization`: D1_START_CAMPAIGN; D2/D3 remain Owner-only
- `claim_boundary`: No unsupported scientific claim

## Inputs and Frozen Bindings

- `source_of_truth`: `control/source-of-truth.yaml`; SHA-256 `56dd24adcd10a5fa8d30abe5d708821d89641dcca0b166db607b53124b419590`
- `campaign`: `control/campaigns/armindex-multiretriever-v2.yaml`; SHA-256 `db97cfc937bae62b3321dc8fc653fbebb42b1c2c6fa401bd92069c1cab4707e7`
- `git_commit`: 1149f9e63ac6174a3ce4bc5a553d793b7d707b0b
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

**Result:** A2_PER_ARM_AUTOINDEX is blocked; ArmIndex measured runs, Selection, and Final counters remain zero.

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

Status: **blocked**. A2_PER_ARM_AUTOINDEX is blocked; ArmIndex measured runs, Selection, and Final counters remain zero.

## Next Action

/goal Run only the Owner-local SSH/Vast A1.2 preflight from docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK.md on one disposable four-RTX3090 instance. Verify the unchanged v2 commit, tree, image digest, four GPU UUIDs, locked runtime and model bytes, adapter parity, Qwen maximum length, local protected-root boundary, live USD quote, heartbeat/resume, safe return path, and provider destroy/TTL path. Keep launch_allowed=false and adopted_for_execution=false; do not start measured retrieval, optimization, Selection, Final, paid API work, or weight changes.

Measured P2, real selection, and final evaluation must not start automatically from this report.

## Evidence Links

- None recorded.
