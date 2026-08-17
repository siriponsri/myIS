---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "7a041e0f09cbd256a6cb69870e2ac4f46b7894feacd04af29674b7b34560f766"
read_model_sha256: "d8bb770a0b454c14dea6c7199fcf6befc9ef28de8b7d8bf29cccd464e329981b"
source_commit: "e399efea2e0726aad2ab28e0253f5fde49a1174c"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "measured_development_aggregate"
scientific_authority: true
claim_boundary: "Aggregate development evidence only. ARM-03 is a numerical tie to A1 at presentation precision; ARM-04 improves its frozen A1 comparator; ARM-05 is retained for transfer analysis but has no strict A1 improvement. No Selection or Final claim is supported."
generated_from_revision: "7a041e0f09cbd256a6cb69870e2ac4f46b7894feacd04af29674b7b34560f766"
last_material_update: "2026-08-17T22:01:32Z"
next_authorized_action: "LOCATE_OR_OBTAIN_AN_OWNER_AUTHORIZED_HASH_BOUND_TRAIN_250_QUERY_CORPUS_AND_EVALUATOR_PACKAGE_BEFORE_A3_ADMISSION"
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-17T22:01:32Z"
updated_at: "2026-08-17T22:01:32Z"
note_id: "ARM-INDEX-HOME"
note_type: "home"
phase_id: "A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT"
task_id: "A3.1"
workflow_status: "ready"
evidence_maturity: "engineering"
claim_level: "none"
---

# ArmIndex Home

ArmIndex is the active campaign. Historical SCOPE and P1 evidence remains readable but is not current ArmIndex evidence.

## Campaign and phase status

- Campaign: `armindex-multiretriever-v2`
- Phase: `A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT`
- Status: `a2_goal004_measured_closeout_complete_a3_train_250_input_pending`

## A2 measured arm outcomes

| Arm | Model | A2 status | A1 comparison | OUT Recall@100 | Commercial status |
|---|---|---|---|---:|---|
| `ARM-01` | `lexical/bm25s` | `a2_diagnostic_no_winner` | `DIAGNOSTIC_TIE_NO_WINNER` | `0.2346666666666668` | commercial_capable |
| `ARM-02` | `BAAI/bge-m3` | `a2_diagnostic_no_winner` | `DIAGNOSTIC_TIE_NO_WINNER` | `0.29` | commercial_capable |
| `ARM-03` | `datalyes/patembed-large` | `a2_primary_transfer_eligible` | `NUMERICAL_TIE_TO_A1` | `0.4229999999999999` | research_non_commercial |
| `ARM-04` | `Snowflake/snowflake-arctic-embed-m-v2.0` | `a2_primary_transfer_eligible` | `STRICT_IMPROVEMENT` | `0.3586666666666666` | commercial_capable |
| `ARM-05` | `Qwen/Qwen3-Embedding-0.6B` | `a2_primary_transfer_eligible` | `NO_STRICT_IMPROVEMENT` | `0.3736666666666666` | commercial_capable |

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

`LOCATE_OR_OBTAIN_AN_OWNER_AUTHORIZED_HASH_BOUND_TRAIN_250_QUERY_CORPUS_AND_EVALUATOR_PACKAGE_BEFORE_A3_ADMISSION`

## Historical evidence

[[SCOPE_HISTORY_INDEX]] · [[P1_CPU_BASELINE_MASTER_REPORT]] · [[P2_SCOPE_DEVELOPMENT_MASTER_REPORT]]
