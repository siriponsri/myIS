---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "b91bbeb83e25bb1d016b79db6f64ee49162c172433b996c219a4d3e2ef43cb40"
read_model_sha256: "004c227ac9746c898d9856ed45f0d64a6989baf53be16e84cfc582b9de477cf5"
source_commit: "8b4b3d6f39aa06580fc2c46743ea7fad8f5f390e"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "b91bbeb83e25bb1d016b79db6f64ee49162c172433b996c219a4d3e2ef43cb40"
last_material_update: "2026-08-05T15:46:35Z"
next_authorized_action: "/goal Execute A0.8_COMPUTE_AND_STORAGE_FEASIBILITY_FIXTURES from the canonical PLAN and control/campaigns/armindex-multiretriever-v2.yaml. Use synthetic fixtures only; do not access protected data, start measured retrieval, download model weights, use GPU or paid APIs, open Selection, or open Final."
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-05T15:46:35Z"
updated_at: "2026-08-05T15:46:35Z"
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
- Status: `a1_2_contract_scaffold_complete_launch_locked`

## Retrieval arms

| Arm | Model | Adapter | Representation | Commercial status |
|---|---|---|---|---|
| `ARM-01` | `lexical/bm25s` | bm25s_cpu_lock_and_synthetic_rank_parity_validated | not_started | commercial_capable |
| `ARM-02` | `BAAI/bge-m3` | source_metadata_frozen_owner_artifacts_pending | not_started | commercial_capable |
| `ARM-03` | `datalyes/patembed-large` | source_metadata_frozen_owner_artifacts_pending | not_started | research_non_commercial |
| `ARM-04` | `Snowflake/snowflake-arctic-embed-m-v2.0` | source_metadata_frozen_owner_artifacts_pending | not_started | commercial_capable |
| `ARM-05` | `Qwen/Qwen3-Embedding-0.6B` | source_metadata_frozen_owner_artifacts_pending | not_started | commercial_capable |

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

`/goal Run the Owner-local A1.2 artifact-manifest and external-termination dry-run preflight on CPU. Validate complete SHA256SUMS manifests for the four dense arms, freeze byte hashes for Snowflake remote code and the Qwen measured maximum length, bind a live quote and provider instance identity, and prove provider termination/TTL without exposing credentials or protected payloads. Do not reserve GPU capacity or start measured retrieval until every launch-checklist item passes and the unchanged execution contract is explicitly adopted.`

## Historical evidence

[[SCOPE_HISTORY_INDEX]] · [[P1_CPU_BASELINE_MASTER_REPORT]] · [[P2_SCOPE_DEVELOPMENT_MASTER_REPORT]]
