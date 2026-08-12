---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "5ec7346f520623d5c21e0ff68ccca82829378d7ee873e0f0d345dc065b997e43"
read_model_sha256: "54dbf7e31279dfb480883ece6cd3d187dbb1dc1bf273ec5f5b55c8cb91dd5332"
source_commit: "aa826e8ee4dc986d0571cfd3a22ce2d646082ff9"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "5ec7346f520623d5c21e0ff68ccca82829378d7ee873e0f0d345dc065b997e43"
last_material_update: "2026-08-12T02:15:10Z"
next_authorized_action: "OWNER_LAUNCH_DOCS_GOAL_A2_WITH_FRESH_PREFLIGHT"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-12T02:15:10Z"
updated_at: "2026-08-12T02:15:10Z"
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
- Status: `a2_candidate_freeze_audit_passed_measured_a2_closed`

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

`OWNER_LAUNCH_DOCS_GOAL_A2_WITH_FRESH_PREFLIGHT`

## Historical evidence

[[SCOPE_HISTORY_INDEX]] · [[P1_CPU_BASELINE_MASTER_REPORT]] · [[P2_SCOPE_DEVELOPMENT_MASTER_REPORT]]
