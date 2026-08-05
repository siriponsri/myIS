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
next_authorized_action: "/goal Execute A0.8_COMPUTE_AND_STORAGE_FEASIBILITY_FIXTURES from the canonical PLAN and control/campaigns/armindex-multiretriever-v2.yaml. Use synthetic fixtures only; do not access protected data, start measured retrieval, download model weights, use GPU or paid APIs, open Selection, or open Final."
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-05T13:42:17Z"
updated_at: "2026-08-05T13:42:17Z"
note_id: "ARM-INDEX-HOME"
note_type: "home"
phase_id: "A1_BASELINES_AND_MULTI_ARM_SCREENING"
task_id: "A0.3"
workflow_status: "verification_needed"
evidence_maturity: "non_scientific"
claim_level: "none"
---

# ArmIndex Home

ArmIndex is the active campaign. Historical SCOPE and P1 evidence remains readable but is not current ArmIndex evidence.

## Campaign and phase status

- Campaign: `armindex-multiretriever-v2`
- Phase: `A1_BASELINES_AND_MULTI_ARM_SCREENING`
- Status: `a1_1_complete_a1_2_contract_locked`

## Retrieval arms

| Arm | Model | Adapter | Representation | Commercial status |
|---|---|---|---|---|
| `ARM-01` | `lexical/bm25s` | synthetic_cpu_fixture_validated_measured_lock_pending | not_started | commercial_capable |
| `ARM-02` | `BAAI/bge-m3` | declared_fixture_blocked_offline_model_lock_pending | not_started | commercial_capable |
| `ARM-03` | `datalyes/patembed-large` | declared_fixture_blocked_offline_model_lock_pending | not_started | research_non_commercial |
| `ARM-04` | `Snowflake/snowflake-arctic-embed-m-v2.0` | declared_fixture_blocked_offline_model_lock_pending | not_started | commercial_capable |
| `ARM-05` | `Qwen/Qwen3-Embedding-0.6B` | declared_fixture_blocked_offline_model_lock_pending | not_started | commercial_capable |

## Optimization status

- Transfer: `not_started`
- Complementarity: `not_started`
- HarnessOpt: `not_started`
- Research champion: `None`
- Commercial champion: `None`

## Integrity and gates

- Measured runs: `0`
- Selection exposures: `0`
- Final exposures: `0`
- D2 and D3 remain Owner-only.
- Final remains closed.

## Next command

`/goal Prepare and validate the versioned A1.2_COMMON_MULTI_ARM_SCREENING execution contract, hash-bound budget profile, frozen offline model and adapter locks, Owner-local launch checklist, and automatic shutdown plan from the validated A1.1 engineering receipt. Complete this scaffold before reserving GPU capacity. Do not launch measured retrieval, access protected payloads from the agent workspace, download model weights during measured runtime, use paid APIs, switch providers, open Selection, or open Final until the separate contract is adopted and validated.`

## Historical evidence

[[SCOPE_HISTORY_INDEX]] · [[P1_CPU_BASELINE_MASTER_REPORT]] · [[P2_SCOPE_DEVELOPMENT_MASTER_REPORT]]
