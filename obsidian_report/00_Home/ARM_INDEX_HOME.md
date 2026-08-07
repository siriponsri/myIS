---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "0f838c7d44685a2168f7f0dc0e0e41c8a33cde6fb612aa976e2bea4350b4dda3"
read_model_sha256: "22b0999cf694b1702b846d4ca261f0c8f4ea1e1bd2d1f7548800afa19d3c219e"
source_commit: "c489d78adea68967cfc1e452eee4c932a3b27c63"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "0f838c7d44685a2168f7f0dc0e0e41c8a33cde6fb612aa976e2bea4350b4dda3"
last_material_update: "2026-08-07T11:52:12Z"
next_authorized_action: "/goal Execute A0.8_COMPUTE_AND_STORAGE_FEASIBILITY_FIXTURES from the canonical PLAN and control/campaigns/armindex-multiretriever-v2.yaml. Use synthetic fixtures only; do not access protected data, start measured retrieval, download model weights, use GPU or paid APIs, open Selection, or open Final."
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-07T11:52:12Z"
updated_at: "2026-08-07T11:52:12Z"
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
- Status: `a1_2_live_synthetic_preflight_pass_owner_disposition_pending_launch_locked`

## Retrieval arms

| Arm | Model | Adapter | Representation | Commercial status |
|---|---|---|---|---|
| `ARM-01` | `lexical/bm25s` | bm25s_cpu_lock_and_synthetic_rank_parity_validated | not_started | commercial_capable |
| `ARM-02` | `BAAI/bge-m3` | v9_live_synthetic_gpu_preflight_pass_scientific_execution_locked | not_started | commercial_capable |
| `ARM-03` | `datalyes/patembed-large` | v9_live_synthetic_gpu_preflight_pass_scientific_execution_locked | not_started | research_non_commercial |
| `ARM-04` | `Snowflake/snowflake-arctic-embed-m-v2.0` | v9_live_synthetic_gpu_preflight_pass_scientific_execution_locked | not_started | commercial_capable |
| `ARM-05` | `Qwen/Qwen3-Embedding-0.6B` | v9_live_synthetic_gpu_preflight_pass_scientific_execution_locked | not_started | commercial_capable |

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

`Owner may destroy and verify provider absence, or explicitly authorize continue_next_goal_on_PLAN only while the continuation policy requirements remain true.`

## Historical evidence

[[SCOPE_HISTORY_INDEX]] · [[P1_CPU_BASELINE_MASTER_REPORT]] · [[P2_SCOPE_DEVELOPMENT_MASTER_REPORT]]
