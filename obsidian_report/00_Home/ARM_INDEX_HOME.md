---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "e2b10cee31b02daff0418c821358212484302f5b3768cc5d8647aca4b638851e"
read_model_sha256: "1114f96b4e89e2c97989c3f6b78ebe1a3bf2b6328f9dae0a7718b0678798b94f"
source_commit: "ae0c65c18abf14b80b66016ad4ba9e1b589275dd"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "e2b10cee31b02daff0418c821358212484302f5b3768cc5d8647aca4b638851e"
last_material_update: "2026-08-06T01:32:27Z"
next_authorized_action: "/goal Execute A0.8_COMPUTE_AND_STORAGE_FEASIBILITY_FIXTURES from the canonical PLAN and control/campaigns/armindex-multiretriever-v2.yaml. Use synthetic fixtures only; do not access protected data, start measured retrieval, download model weights, use GPU or paid APIs, open Selection, or open Final."
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-06T01:32:27Z"
updated_at: "2026-08-06T01:32:27Z"
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
- Status: `a1_2_vast_4x3090_postcommit_preflight_prepared_launch_locked`

## Retrieval arms

| Arm | Model | Adapter | Representation | Commercial status |
|---|---|---|---|---|
| `ARM-01` | `lexical/bm25s` | bm25s_cpu_lock_and_synthetic_rank_parity_validated | not_started | commercial_capable |
| `ARM-02` | `BAAI/bge-m3` | v3_clean_bundle_identity_prepared_owner_live_preflight_pending | not_started | commercial_capable |
| `ARM-03` | `datalyes/patembed-large` | v3_clean_bundle_identity_prepared_owner_live_preflight_pending | not_started | research_non_commercial |
| `ARM-04` | `Snowflake/snowflake-arctic-embed-m-v2.0` | v3_clean_bundle_identity_prepared_owner_live_preflight_pending | not_started | commercial_capable |
| `ARM-05` | `Qwen/Qwen3-Embedding-0.6B` | v3_clean_bundle_identity_prepared_owner_live_preflight_pending | not_started | commercial_capable |

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

`/goal Run only the Owner-local SSH/Vast A1.2 preflight from docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V3.md on one disposable four-RTX3090 instance. Validate the clean pushed v3 correction, preserve the unchanged v2 bytes, and verify the frozen bundle commit, tree, image digest, four GPU UUIDs, locked runtime and model bytes, adapter parity, Qwen maximum length, local protected-root boundary, live USD quote, heartbeat/resume, safe return path, and provider destroy/TTL path. Keep launch_allowed=false and adopted_for_execution=false; do not start measured retrieval, optimization, Selection, Final, paid API work, or weight changes.`

## Historical evidence

[[SCOPE_HISTORY_INDEX]] · [[P1_CPU_BASELINE_MASTER_REPORT]] · [[P2_SCOPE_DEVELOPMENT_MASTER_REPORT]]
