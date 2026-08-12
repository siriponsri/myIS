---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "facfa2c510c0c0d56bec04c240113e42a0b45a4eeaf5b674f3f6a5e4b93a38f2"
read_model_sha256: "9e0554ce0c201200bef136ec827a028e2d9f758097a92234ebff4c0dd9026002"
source_commit: "f2674e3e44ade4521fd1b61877e20211bd5b4406"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "facfa2c510c0c0d56bec04c240113e42a0b45a4eeaf5b674f3f6a5e4b93a38f2"
last_material_update: "2026-08-12T15:31:53Z"
next_authorized_action: "IMPLEMENT_PRODUCTION_A2_ADAPTER_AND_MATCHED_FIRST_CONDITIONAL_RESERVE_LIFECYCLE"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-12T15:31:53Z"
updated_at: "2026-08-12T15:31:53Z"
note_id: "ARM-INDEX-HOME"
note_type: "home"
phase_id: "A2_PER_ARM_AUTOINDEX"
task_id: "A0.3"
workflow_status: "verification_needed"
evidence_maturity: "non_scientific"
claim_level: "none"
---

# ArmIndex Home

ArmIndex is the active campaign. Historical SCOPE and P1 evidence remains readable but is not current ArmIndex evidence.

## Campaign and phase status

- Campaign: `armindex-multiretriever-v2`
- Phase: `A2_PER_ARM_AUTOINDEX`
- Status: `a2_implementation_blocked_measured_a2_locked`

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

- Measured runs: `1`
- Selection exposures: `0`
- Final exposures: `0`
- D2 and D3 remain Owner-only.
- Final remains closed.

## Next command

`IMPLEMENT_PRODUCTION_A2_ADAPTER_AND_MATCHED_FIRST_CONDITIONAL_RESERVE_LIFECYCLE`

## Historical evidence

[[SCOPE_HISTORY_INDEX]] · [[P1_CPU_BASELINE_MASTER_REPORT]] · [[P2_SCOPE_DEVELOPMENT_MASTER_REPORT]]
