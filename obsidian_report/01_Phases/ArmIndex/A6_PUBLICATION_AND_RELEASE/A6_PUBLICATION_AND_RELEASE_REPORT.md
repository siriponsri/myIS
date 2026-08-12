---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "97338cab2df65a89dd98e5a933ca601a24e9d63432811d30c09c46479e13816a"
read_model_sha256: "384b35f9ec0eb32aea8ff05c4c75811c71a1b67249b79c741971264e34ace262"
source_commit: "62a91784740519f2943e520be82c4405752ce293"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "97338cab2df65a89dd98e5a933ca601a24e9d63432811d30c09c46479e13816a"
last_material_update: "2026-08-12T18:49:01Z"
next_authorized_action: "AP_VALIDATE_OWNER_LOCAL_PUSHED_HEAD_BUNDLE_AND_DEPLOYMENT_RECEIPT_THEN_FRESH_INSTANCE_ADMISSION_AND_ISOLATED_STAGING"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-12T18:49:01Z"
updated_at: "2026-08-12T18:49:01Z"
note_id: "A6_PUBLICATION_AND_RELEASE-MASTER"
note_type: "phase_report"
phase_id: "A6_PUBLICATION_AND_RELEASE"
task_id: null
workflow_status: "blocked"
evidence_maturity: "non_scientific"
claim_level: "none"
---

# A6_PUBLICATION_AND_RELEASE

Generated from the validated report record. Manual edits may be replaced; use the separate Owner Notes area for personal annotations.

## Objective

Build publication and release artifacts only after D3_SUBMIT_RELEASE.

## Starting State

- `phase`: A2_PER_ARM_AUTOINDEX
- `task`: None
- `program_state`: a2_new_instance_rebind_required_measured_a2_locked
- `authorization`: D1_START_CAMPAIGN; D2/D3 remain Owner-only
- `claim_boundary`: No unsupported scientific claim

## Inputs and Frozen Bindings

- `source_of_truth`: `control/source-of-truth.yaml`; SHA-256 `fb6260f8cfea332849a977083758db1d5dc617d5194ffb7a09ca77232246e387`
- `campaign`: `control/campaigns/armindex-multiretriever-v2.yaml`; SHA-256 `b8b5c85d7deafe0d20cef1b5d9da0ac4a7e8300cf4f61696ffa9fa2eb43a06de`
- `git_commit`: 62a91784740519f2943e520be82c4405752ce293
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

**Result:** A6_PUBLICATION_AND_RELEASE is blocked; ArmIndex measured runs, Selection, and Final counters remain zero.

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

Status: **blocked**. A6_PUBLICATION_AND_RELEASE is blocked; ArmIndex measured runs, Selection, and Final counters remain zero.

## Next Action

AP_VALIDATE_OWNER_LOCAL_PUSHED_HEAD_BUNDLE_AND_DEPLOYMENT_RECEIPT_THEN_FRESH_INSTANCE_ADMISSION_AND_ISOLATED_STAGING

Measured P2, real selection, and final evaluation must not start automatically from this report.

## Evidence Links

- None recorded.
