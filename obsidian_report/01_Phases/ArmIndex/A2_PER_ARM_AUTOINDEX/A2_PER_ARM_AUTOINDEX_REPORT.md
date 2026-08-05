---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "24cc5e748960c5c2751db993542e53d5d02ea4c245d80c417c7a1d2b2243298f"
read_model_sha256: "9ca928a32ed2f2f0062fff7cada2a1548cdf19d2969b2a50071550a5b668b409"
source_commit: "800a50baba209ffdc78551d78f9c8e5e8044428a"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "24cc5e748960c5c2751db993542e53d5d02ea4c245d80c417c7a1d2b2243298f"
last_material_update: "2026-08-05T13:42:17Z"
next_authorized_action: "/goal Prepare and validate the versioned A1.2_COMMON_MULTI_ARM_SCREENING execution contract, hash-bound budget profile, frozen offline model and adapter locks, Owner-local launch checklist, and automatic shutdown plan from the validated A1.1 engineering receipt. Complete this scaffold before reserving GPU capacity. Do not launch measured retrieval, access protected payloads from the agent workspace, download model weights during measured runtime, use paid APIs, switch providers, open Selection, or open Final until the separate contract is adopted and validated."
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-05T13:42:17Z"
updated_at: "2026-08-05T13:42:17Z"
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
- `program_state`: a1_1_complete_a1_2_contract_locked
- `authorization`: D1_START_CAMPAIGN; D2/D3 remain Owner-only
- `claim_boundary`: No unsupported scientific claim

## Inputs and Frozen Bindings

- `source_of_truth`: `control/source-of-truth.yaml`; SHA-256 `09661ecfd6a336c2f163ecf69d5921e0752eaa47fc4b0b03ba45cdc8f13835cd`
- `campaign`: `control/campaigns/armindex-multiretriever-v2.yaml`; SHA-256 `0779c019d1cbdbf52747b0bae90eb31f739f0a10af23f6fcfab50012799aee93`
- `git_commit`: 800a50baba209ffdc78551d78f9c8e5e8044428a
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
- `real_counters`: `inline`; SHA-256 `None`
- `evidence_class`: engineering
- `scientific_authority`: False

## Decision

Status: **blocked**. A2_PER_ARM_AUTOINDEX is blocked; ArmIndex measured runs, Selection, and Final counters remain zero.

## Next Action

/goal Prepare and validate the versioned A1.2_COMMON_MULTI_ARM_SCREENING execution contract, hash-bound budget profile, frozen offline model and adapter locks, Owner-local launch checklist, and automatic shutdown plan from the validated A1.1 engineering receipt. Complete this scaffold before reserving GPU capacity. Do not launch measured retrieval, access protected payloads from the agent workspace, download model weights during measured runtime, use paid APIs, switch providers, open Selection, or open Final until the separate contract is adopted and validated.

Measured P2, real selection, and final evaluation must not start automatically from this report.

## Evidence Links

- None recorded.
