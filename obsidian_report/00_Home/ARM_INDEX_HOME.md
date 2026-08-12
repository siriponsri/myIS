---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "ae9fde5ab53e42ae8589fddb12475487decf7aa7e10678e7bb9a9b8e4a60b57a"
read_model_sha256: "c6cef36cd22a79a463f4392da5009e3c6fb279ae9a963b66c2c3ed8137fa1b7b"
source_commit: "e64711fa3f1708a5277e7a54f5116fdbb0c3aeb8"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "ae9fde5ab53e42ae8589fddb12475487decf7aa7e10678e7bb9a9b8e4a60b57a"
last_material_update: "2026-08-12T16:55:09Z"
next_authorized_action: "AP_VALIDATE_OWNER_LOCAL_PUSHED_HEAD_BUNDLE_AND_DEPLOYMENT_RECEIPT_THEN_FRESH_INSTANCE_ADMISSION_AND_ISOLATED_STAGING"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-12T16:55:09Z"
updated_at: "2026-08-12T16:55:09Z"
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
- Status: `a2_new_instance_rebind_required_measured_a2_locked`

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

`AP_VALIDATE_OWNER_LOCAL_PUSHED_HEAD_BUNDLE_AND_DEPLOYMENT_RECEIPT_THEN_FRESH_INSTANCE_ADMISSION_AND_ISOLATED_STAGING`

## Historical evidence

[[SCOPE_HISTORY_INDEX]] · [[P1_CPU_BASELINE_MASTER_REPORT]] · [[P2_SCOPE_DEVELOPMENT_MASTER_REPORT]]
