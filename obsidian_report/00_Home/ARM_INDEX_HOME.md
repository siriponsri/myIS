---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "8970a6d79ca87ce16d7f1925b5684ce93dd9ccfe9817226cbdb08717122361d7"
read_model_sha256: "37e1915f14effc9c9db7abad73a7fb2876c63489d593342c72ec58c8625b7af9"
source_commit: "485d27ae1ad7d3ca884ffc7c739b6dc616aec0df"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "8970a6d79ca87ce16d7f1925b5684ce93dd9ccfe9817226cbdb08717122361d7"
last_material_update: "2026-08-11T04:06:59Z"
next_authorized_action: "PREPARE_FRESH_A1_SAME_INSTANCE_ADMISSION_AND_RETRY_25_OF_25_BEFORE_A2"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-11T04:06:59Z"
updated_at: "2026-08-11T04:06:59Z"
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
- Status: `a1_2_terminal_failed_closed_retry_required`

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

`PREPARE_FRESH_A1_SAME_INSTANCE_ADMISSION_AND_RETRY_25_OF_25_BEFORE_A2`

## Historical evidence

[[SCOPE_HISTORY_INDEX]] · [[P1_CPU_BASELINE_MASTER_REPORT]] · [[P2_SCOPE_DEVELOPMENT_MASTER_REPORT]]
