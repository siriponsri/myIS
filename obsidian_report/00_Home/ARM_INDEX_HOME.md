---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "ab4f9d9dde9c71bd9eb66402c151935a5f57341e3344c841f3cb20c8fd816428"
read_model_sha256: "f64306d71195c5ec15cecf35a174a1075642bf6d673ca24705229673c7e31119"
source_commit: "9b297bd305ceaff9c0f6a2df4f04627eb66aab11"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "ab4f9d9dde9c71bd9eb66402c151935a5f57341e3344c841f3cb20c8fd816428"
last_material_update: "2026-08-03T15:43:42Z"
next_authorized_action: "Complete ArmIndex A0 migration closeout; no measured retrieval"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-03T15:43:42Z"
updated_at: "2026-08-03T15:43:42Z"
note_id: "ARM-INDEX-HOME"
note_type: "home"
phase_id: "A0_MIGRATION_FOUNDATION"
task_id: "A0.3"
workflow_status: "verification_needed"
evidence_maturity: "non_scientific"
claim_level: "none"
---

# ArmIndex Home

ArmIndex is the active campaign. Historical SCOPE and P1 evidence remains readable but is not current ArmIndex evidence.

## Campaign and phase status

- Campaign: `armindex-multiretriever-v2`
- Phase: `A0_MIGRATION_FOUNDATION`
- Status: `active_migration`

## Retrieval arms

| Arm | Model | Adapter | Representation | Commercial status |
|---|---|---|---|---|
| `ARM-01` | `lexical/bm25s` | declared_pending_fixture_lock | not_started | commercial_capable |
| `ARM-02` | `BAAI/bge-m3` | declared_pending_fixture_lock | not_started | commercial_capable |
| `ARM-03` | `datalyes/patembed-large` | declared_pending_fixture_lock | not_started | research_non_commercial |
| `ARM-04` | `Snowflake/snowflake-arctic-embed-m-v2.0` | declared_pending_fixture_lock | not_started | commercial_capable |
| `ARM-05` | `Qwen/Qwen3-Embedding-0.6B` | declared_pending_fixture_lock | not_started | commercial_capable |

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

`/goal Execute ArmIndex A0 compute-feasibility fixtures and preflight from the canonical PLAN and control/campaigns/armindex-multiretriever-v2.yaml. Use synthetic fixtures only; do not start measured retrieval, download model weights, open Selection, or open Final.`

## Historical evidence

[[SCOPE_HISTORY_INDEX]] · [[P1_CPU_BASELINE_MASTER_REPORT]] · [[P2_SCOPE_DEVELOPMENT_MASTER_REPORT]]
