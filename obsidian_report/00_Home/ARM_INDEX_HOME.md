---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "50b081e9bb0795b9772a3fd1e790e3b0503e5ab1f0478541458680163e9b880f"
read_model_sha256: "8bd6e0851fcaaa9cf20c7001e0ab222dab82e170aeca6f93b113cc36c2ba60b2"
source_commit: "1e86c432933f3bbf2e6763d04bb64139f81ce396"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "50b081e9bb0795b9772a3fd1e790e3b0503e5ab1f0478541458680163e9b880f"
last_material_update: "2026-08-06T02:33:36Z"
next_authorized_action: "/goal Execute A0.8_COMPUTE_AND_STORAGE_FEASIBILITY_FIXTURES from the canonical PLAN and control/campaigns/armindex-multiretriever-v2.yaml. Use synthetic fixtures only; do not access protected data, start measured retrieval, download model weights, use GPU or paid APIs, open Selection, or open Final."
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-06T02:33:36Z"
updated_at: "2026-08-06T02:33:36Z"
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
- Status: `a1_2_runtime_minimal_direct_base_preflight_prepared_launch_locked`

## Retrieval arms

| Arm | Model | Adapter | Representation | Commercial status |
|---|---|---|---|---|
| `ARM-01` | `lexical/bm25s` | bm25s_cpu_lock_and_synthetic_rank_parity_validated | not_started | commercial_capable |
| `ARM-02` | `BAAI/bge-m3` | v5_direct_official_base_prepared_owner_local_stage_pending | not_started | commercial_capable |
| `ARM-03` | `datalyes/patembed-large` | v5_direct_official_base_prepared_owner_local_stage_pending | not_started | research_non_commercial |
| `ARM-04` | `Snowflake/snowflake-arctic-embed-m-v2.0` | v5_direct_official_base_prepared_owner_local_stage_pending | not_started | commercial_capable |
| `ARM-05` | `Qwen/Qwen3-Embedding-0.6B` | v5_direct_official_base_prepared_owner_local_stage_pending | not_started | commercial_capable |

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

`Owner stages local runtime-minimal artifacts, then later opens one quoted Vast worker and runs the v5 SSH preflight without measured retrieval.`

## Historical evidence

[[SCOPE_HISTORY_INDEX]] · [[P1_CPU_BASELINE_MASTER_REPORT]] · [[P2_SCOPE_DEVELOPMENT_MASTER_REPORT]]
