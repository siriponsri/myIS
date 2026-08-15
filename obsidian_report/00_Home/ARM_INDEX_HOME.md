---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "1d3c6b5a3f08d2564eafc7a28bbabd428a567b1aee9cea21afc0641dcf0b4b7b"
read_model_sha256: "0498288ba6a5dfdff2b62e1bff83b32c8bde007eebaeb82520cbf2afe10cb8e6"
source_commit: "81bf438d399ae447f6fe4d33519049a3d74254ed"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "measured_execution_authority"
scientific_authority: true
claim_boundary: "frozen_a2_retrieval_only_candidate_evaluation_rep_dev_a3_selection_final_closed"
generated_from_revision: "1d3c6b5a3f08d2564eafc7a28bbabd428a567b1aee9cea21afc0641dcf0b4b7b"
last_material_update: "2026-08-15T09:27:09Z"
next_authorized_action: "LO_EXECUTE_FROZEN_A2_WITH_FRESH_ADMISSION_AND_SAFE_RETURN"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-15T09:27:09Z"
updated_at: "2026-08-15T09:27:09Z"
note_id: "ARM-INDEX-HOME"
note_type: "home"
phase_id: "A2_PER_ARM_AUTOINDEX"
task_id: "A2.1"
workflow_status: "ready"
evidence_maturity: "engineering"
claim_level: "none"
---

# ArmIndex Home

ArmIndex is the active campaign. Historical SCOPE and P1 evidence remains readable but is not current ArmIndex evidence.

## Campaign and phase status

- Campaign: `armindex-multiretriever-v2`
- Phase: `A2_PER_ARM_AUTOINDEX`
- Status: `a2_ready_for_measured_execution_authorized`

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

`LO_EXECUTE_FROZEN_A2_WITH_FRESH_ADMISSION_AND_SAFE_RETURN`

## Historical evidence

[[SCOPE_HISTORY_INDEX]] · [[P1_CPU_BASELINE_MASTER_REPORT]] · [[P2_SCOPE_DEVELOPMENT_MASTER_REPORT]]
