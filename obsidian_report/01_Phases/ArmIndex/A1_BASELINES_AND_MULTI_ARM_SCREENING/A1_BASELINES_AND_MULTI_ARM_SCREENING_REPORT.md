---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "50b081e9bb0795b9772a3fd1e790e3b0503e5ab1f0478541458680163e9b880f"
read_model_sha256: "8bd6e0851fcaaa9cf20c7001e0ab222dab82e170aeca6f93b113cc36c2ba60b2"
source_commit: "1e86c432933f3bbf2e6763d04bb64139f81ce396"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering_preflight_revision"
scientific_authority: false
claim_boundary: "direct_official_base_image_path_only_no_vast_contact_no_measured_execution"
generated_from_revision: "50b081e9bb0795b9772a3fd1e790e3b0503e5ab1f0478541458680163e9b880f"
last_material_update: "2026-08-06T02:33:36Z"
next_authorized_action: "Owner stages local runtime-minimal artifacts, then later opens one quoted Vast worker and runs the v5 SSH preflight without measured retrieval."
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-06T02:33:36Z"
updated_at: "2026-08-06T02:33:36Z"
note_id: "A1_BASELINES_AND_MULTI_ARM_SCREENING-MASTER"
note_type: "phase_report"
phase_id: "A1_BASELINES_AND_MULTI_ARM_SCREENING"
task_id: null
workflow_status: "ready"
evidence_maturity: "non_scientific"
claim_level: "none"
---

# A1_BASELINES_AND_MULTI_ARM_SCREENING

Generated from the validated report record. Manual edits may be replaced; use the separate Owner Notes area for personal annotations.

## Objective

Reproduce controls and screen the five adapters with common programs.

## Starting State

- `phase`: A1_BASELINES_AND_MULTI_ARM_SCREENING
- `task`: None
- `program_state`: a1_2_runtime_minimal_direct_base_preflight_prepared_launch_locked
- `authorization`: D1_START_CAMPAIGN; D2/D3 remain Owner-only
- `claim_boundary`: No unsupported scientific claim

## Inputs and Frozen Bindings

- `source_of_truth`: `control/source-of-truth.yaml`; SHA-256 `7206aed728c79af3f2b3dcf4dcf36d5fa2530e2bde6f3a6916bc4be9558bb685`
- `campaign`: `control/campaigns/armindex-multiretriever-v2.yaml`; SHA-256 `5f98245607ce1c3edbdff38b813e1b4c7142e2683cf93ab53991bdc72df484f2`
- `git_commit`: 1e86c432933f3bbf2e6763d04bb64139f81ce396
- `migration_budget`: `control/budgets/armindex-migration-v2.yaml`; SHA-256 `48bab215d10ef82c0fe8206702f75f4b212df12792d7475131888d50161821ec`
- `armindex_schema_root`: `schemas/armindex`; SHA-256 `6ede89f83141bf4f051413feedf5316388defe5565051a53eaed386c4c62320a`
- `historical_scope`: `control/campaigns/scope-autoindex-v1.yaml`; SHA-256 `a86d73657988713d62ddfb12c9c01da367af2e97922363233ef8cd453fb20ce9`
- `a11_task_receipt`: `campaigns/armindex-multiretriever-v2/evidence/a1.1-adapter-fixture-validation.receipt.v1.json`; SHA-256 `56d23bf3f6057272926a99f795c172b7fb5253134854ac70a038f154e2b32c83`
- `a11_fixture_manifest`: `outputs/fixtures/armindex/a1.1/adapter-cpu-v1/manifest.json`; SHA-256 `2736750d6f650fa64f5810c4b1d1c480517cf1a389f55515597bfd9839f07d17`
- `a11_fixture_receipt`: `outputs/fixtures/armindex/a1.1/adapter-cpu-v1/receipt.json`; SHA-256 `b58c02f9bde3edffe6b54076e0df5a8ce3c9ed081441416bea8bc27ed1c02d24`
- `a12_gpu_proposal`: `campaigns/armindex-multiretriever-v2/proposals/a1.2-gpu-execution-plan.v1.json`; SHA-256 `2c652fbb83aff0d10997dc2fa963d937b9aa0912bd45fe059e3a6f6b6742ca6a`
- `a12_execution_contract`: `control/armindex/a1.2/execution-contract.v1.json`; SHA-256 `2c927841a06ee355a405f9053976a8e5543f7f43794dca0231ea04d3b286e335`
- `a12_budget_profile`: `control/budgets/a1.2-common-screen-v1.json`; SHA-256 `07ae7de5c7e704c2f905f3da1294c70db1e5f786a2b00ad6d17c97626b86f44c`
- `a12_model_lockset`: `control/armindex/a1.2/model-lockset.v1.json`; SHA-256 `0e31912ba0e036580fd394db9bab2260c0eaffafef6baea89b2f7567460f5e43`
- `a12_launch_checklist`: `control/armindex/a1.2/launch-checklist.v1.json`; SHA-256 `6dff0daf0d4190a1a5018ce28ee20d67af60e82220717adea1ec480867894175`
- `a12_shutdown_plan`: `control/armindex/a1.2/shutdown-plan.v1.json`; SHA-256 `9bd32b7c22c82be6ccc1f2b0f5f7f9798213d57d1087230468474cc0cbe86482`
- `a12_closeout_validation_audit`: `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json`; SHA-256 `dd20d4bf1c73eeeef23872e626444e9420791636403b4ac6b6f9f01942911d08`
- `a12_owner_local_preflight`: `outputs/audits/armindex/a1.2-owner-local-preflight-20260806.json`; SHA-256 `2c3ce75d23c8909f8d345295538a4eb230e436970f488b837d887405c754ca57`
- `a12_owner_local_mlflow_registration`: `outputs/audits/armindex/a1.2-owner-local-preflight-mlflow-registration.json`; SHA-256 `84855affa318db91f2853ebeef972d8ef4cac300d531e1563fd342dcce0c6cbc`
- `a12_vast_v2_receipt`: `campaigns/armindex-multiretriever-v2/evidence/a1.2-vast-4x3090-migration.receipt.v2.json`; SHA-256 `efc6550fc9cb321a3cbaca75c5aea1b95e52d007b59b21f80888ab872e462efb`
- `a12_vast_v2_budget`: `control/budgets/a1.2-common-screen-vast-4x3090-v2.json`; SHA-256 `21ba2439c599d3a23c9a2b1f9473e74e62476dcc314406c0c03830b79a4ea9b5`
- `a12_vast_v2_topology`: `control/armindex/a1.2/topology-contract.v2.json`; SHA-256 `92ada300e29426f39f27095e08a92332974b23a6412099e09f5348920e44a4b2`
- `a12_vast_v2_closeout_validation`: `outputs/audits/rigor/a1.2-vast-4x3090-preflight-closeout-validation-20260806.json`; SHA-256 `8bfd4817abfeb10c48169efc80bb5c655760da1ab03b06fad98435cb0072e33c`
- `a12_vast_v3_correction_receipt`: `campaigns/armindex-multiretriever-v2/evidence/a1.2-vast-4x3090-postcommit-migration.receipt.v3.json`; SHA-256 `f031a08a23d58b96e67461353d83b8f11243a5cf8ab4a2b571b8e1940876a8d0`
- `a12_vast_v3_execution_contract`: `control/armindex/a1.2/execution-contract.v3.json`; SHA-256 `716ea6542df7a668a1148ef0eed1eb61d13bd6a8a3663874ec8b66db697c5b81`
- `a12_direct_base_v5_receipt`: `campaigns/armindex-multiretriever-v2/evidence/a1.2-runtime-minimal-direct-base-migration.receipt.v5.json`; SHA-256 `8d0480b4c6ef8ae3631f04f8038761db2eaee660eef01644605530dfeea715a5`
- `a12_direct_base_v5_execution_contract`: `control/armindex/a1.2/execution-contract.direct-base.v5.json`; SHA-256 `8fabe004c96e561f7a2fbf8a1ff6819acfa1038d9b49021b11f1da07b956d238`

## Work Performed

A1.1 synthetic adapter evidence and the A1.2 launch-locked execution scaffold are both validated. The additive v5 direct-base revision preserves v1-v3 history, binds the official PyTorch linux/amd64 manifest, and removes custom image and nested-container steps from the active path. ARM-01 remains local CPU only; four dense source revisions and runtime-minimal allowlists are frozen, while Owner-local manifests, adapter parity, live provider binding, termination dry run, and explicit adoption remain pending.

### A1.2 resource planning boundary

The proposal remains `proposal_not_adopted_execution_locked`. It specifies `1` GPU with at least `24` GiB VRAM; preferred classes are RTX_4090_24GB, RTX_3090_24GB, L4_24GB, A10_24GB. A100/H100 required: `False`. The planning range is `8-16` GPU hours and `10-20` elapsed hours. Raw compute is estimated at USD `2.4-12.8`; hard stops are USD `5` for parity/pilot, USD `18` for the common screen, USD `23` for A1, and USD `100` for the campaign.

Owner prerequisites:

- make_owner_local_protected_root_available_to_the_runner
- prestage_frozen_model_artifacts_without_agent_credential_access
- ensure_Vast_or_equivalent_account_credit_and_credentials_are_available
- intervene_only_if_provider_unavailable_hashes_conflict_or_budget_must_increase

### A1.2 scaffold and launch state

The offline scaffold is `a1_2_runtime_minimal_direct_base_preflight_prepared_launch_locked` with `5` model/source locks. ARM-01 has `1` offline CPU adapter lock ready; `4` dense Owner-local artifact manifests and `21` checklist items remain pending. Launch ready: `False`; measured execution: `False`. The closeout audit passed `17` validation groups and retained `7` bounded failure/recovery records.

The immutable v2 preparation remains `offline_preparation_complete_live_owner_preflight_pending` and the v3 correction remains `postcommit_validator_prepared_live_owner_preflight_pending`. The active additive v5 direct-base revision is `direct_base_preflight_prepared_local_owner_stage_pending` with image `pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime` at manifest `sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20` on `linux/amd64`. It launches the official image directly, excludes custom-image build and nested-container steps, and does not authorize launch or adoption.

Owner-local prerequisites still required:

- mount the protected root read-only for the runner without copying payloads into the agent workspace;
- validate complete `SHA256SUMS` manifests for all dense runtime files and byte SHA-256 for Snowflake remote code;
- pass dense adapter parity checks and freeze the Qwen measured maximum input length;
- bind a live quote, capacity, provider instance identity, artifact-return target, and free-space check;
- dry-run the external provider termination watcher and TTL, because guest poweroff alone does not prove billing stopped;
- explicitly adopt the unchanged execution contract and budget before any GPU reservation.

## Artifacts Produced

These references explain what each artifact is for; the bytes remain governed by canonical paths.

| Artifact | Type | Evidence | Safe URI | SHA-256 | Validation |
|---|---|---|---|---|---|
| A1.1 adapter fixture task receipt | `receipt` | `engineering_fixture` | `campaigns/armindex-multiretriever-v2/evidence/a1.1-adapter-fixture-validation.receipt.v1.json` | `56d23bf3f6057272926a99f795c172b7fb5253134854ac70a038f154e2b32c83` | `validated` |
| A1.1 adapter fixture manifest | `manifest` | `engineering_fixture` | `outputs/fixtures/armindex/a1.1/adapter-cpu-v1/manifest.json` | `2736750d6f650fa64f5810c4b1d1c480517cf1a389f55515597bfd9839f07d17` | `validated` |
| A1.1 ARM-01 CPU fixture receipt | `receipt` | `engineering_fixture` | `outputs/fixtures/armindex/a1.1/adapter-cpu-v1/receipt.json` | `b58c02f9bde3edffe6b54076e0df5a8ce3c9ed081441416bea8bc27ed1c02d24` | `validated` |
| A1.1 adapter fixture runbook | `runbook` | `engineering_fixture` | `control/runbooks/A1_1_ADAPTER_FIXTURE_VALIDATION.md` | `7438a48fa675dd61f6fef45262024d2a134356bca101c42dc640ff98ea37adab` | `validated` |
| A1.1 append-only execution ledger | `ledger` | `engineering_fixture` | `control/armindex/a1.1-adapter-fixture-validation-ledger.v1.jsonl` | `9356a5e11f58f96936f155960bf8d908b380b2d95001500248cb303bc47ec2b1` | `validated` |
| A1.2 GPU, elapsed-time, and budget proposal | `proposal` | `planning_estimate` | `campaigns/armindex-multiretriever-v2/proposals/a1.2-gpu-execution-plan.v1.json` | `2c652fbb83aff0d10997dc2fa963d937b9aa0912bd45fe059e3a6f6b6742ca6a` | `validated` |
| A1.2 contract scaffold receipt | `receipt` | `engineering_contract_scaffold` | `campaigns/armindex-multiretriever-v2/evidence/a1.2-contract-scaffold.receipt.v1.json` | `834ed83440b7d2c0809588f661739208ddb62d72d6d4cd582f192bd9f2cbff7d` | `validated` |
| A1.2 versioned execution contract | `contract` | `engineering_contract_scaffold` | `control/armindex/a1.2/execution-contract.v1.json` | `2c927841a06ee355a405f9053976a8e5543f7f43794dca0231ea04d3b286e335` | `validated` |
| A1.2 ARM-01 bm25s synthetic CPU rank-parity receipt | `receipt` | `engineering_contract_scaffold` | `outputs/fixtures/armindex/a1.2/bm25s-rank-parity-v1/receipt.json` | `517e2157426cce4f050b71e7423c3a76014077f8ae525133099f0c9b048a587d` | `validated` |
| A1.2 hash-bound budget profile | `budget` | `engineering_contract_scaffold` | `control/budgets/a1.2-common-screen-v1.json` | `07ae7de5c7e704c2f905f3da1294c70db1e5f786a2b00ad6d17c97626b86f44c` | `validated` |
| A1.2 execution envelope | `contract` | `engineering_contract_scaffold` | `control/execution-envelope-a1.2-v1.yaml` | `0117e36c7737baba58a1f5de2b3ec42355f3350ec1b856b110e61b3dd4e32cbf` | `validated` |
| A1.2 five-arm model source lockset | `lockset` | `engineering_contract_scaffold` | `control/armindex/a1.2/model-lockset.v1.json` | `0e31912ba0e036580fd394db9bab2260c0eaffafef6baea89b2f7567460f5e43` | `validated` |
| A1.2 Owner-local launch checklist | `checklist` | `engineering_contract_scaffold` | `control/armindex/a1.2/launch-checklist.v1.json` | `6dff0daf0d4190a1a5018ce28ee20d67af60e82220717adea1ec480867894175` | `validated` |
| A1.2 two-layer shutdown plan | `runbook` | `engineering_contract_scaffold` | `control/armindex/a1.2/shutdown-plan.v1.json` | `9bd32b7c22c82be6ccc1f2b0f5f7f9798213d57d1087230468474cc0cbe86482` | `validated` |
| A1.2 contract scaffold runbook | `runbook` | `engineering_contract_scaffold` | `control/runbooks/A1_2_COMMON_MULTI_ARM_SCREENING.md` | `ae5e816c5efd60ed972be2d6f0d1490656321ccc323e450e679b18beefc1dde5` | `validated` |
| A1.2 append-only scaffold ledger | `ledger` | `engineering_contract_scaffold` | `control/armindex/a1.2/execution-scaffold-ledger.v1.jsonl` | `c0c2ab001460905e52a8d22606da3a2d44f7c8388612b1592d0b4fa05105273f` | `validated` |
| A1.2 generated report archive audit | `audit` | `engineering_contract_scaffold` | `control/armindex/a1.2/report-archive-audit.v1.json` | `e1a17d104a245eae8c601b637316175422263d50f60f36e864dcf17c07ebf6a4` | `validated` |
| A1.2 closeout validation audit | `audit` | `engineering_contract_scaffold` | `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` | `dd20d4bf1c73eeeef23872e626444e9420791636403b4ac6b6f9f01942911d08` | `validated` |
| A1.2 Owner-local CPU preflight receipt | `audit` | `engineering_contract_scaffold` | `outputs/audits/armindex/a1.2-owner-local-preflight-20260806.json` | `2c3ce75d23c8909f8d345295538a4eb230e436970f488b837d887405c754ca57` | `validated` |
| A1.2 MLflow safe preflight registration | `result` | `engineering_contract_scaffold` | `outputs/audits/armindex/a1.2-owner-local-preflight-mlflow-registration.json` | `84855affa318db91f2853ebeef972d8ef4cac300d531e1563fd342dcce0c6cbc` | `validated` |
| A1.2 Vast 4xRTX3090 migration receipt v2 | `receipt` | `engineering_preflight_scaffold` | `campaigns/armindex-multiretriever-v2/evidence/a1.2-vast-4x3090-migration.receipt.v2.json` | `efc6550fc9cb321a3cbaca75c5aea1b95e52d007b59b21f80888ab872e462efb` | `validated` |
| A1.2 Vast 4xRTX3090 execution contract v2 | `contract` | `engineering_preflight_scaffold` | `control/armindex/a1.2/execution-contract.v2.json` | `ee1709d3f2557c8810505388fd82bb668905f0b166905c201d2f3e4d5f43da85` | `validated` |
| A1.2 synthetic four-worker receipt | `receipt` | `engineering_preflight_scaffold` | `outputs/fixtures/armindex/a1.2/vast-4x3090-preflight-v2/receipt.json` | `fce41672173ff34e6f0be76b26b382fc7538b941da5fb06571e08e6661f136eb` | `validated` |
| A1.2 Vast 4xRTX3090 budget profile v2 | `budget` | `engineering_preflight_scaffold` | `control/budgets/a1.2-common-screen-vast-4x3090-v2.json` | `21ba2439c599d3a23c9a2b1f9473e74e62476dcc314406c0c03830b79a4ea9b5` | `validated` |
| A1.2 local-Codex remote-four-GPU topology | `contract` | `engineering_preflight_scaffold` | `control/armindex/a1.2/topology-contract.v2.json` | `92ada300e29426f39f27095e08a92332974b23a6412099e09f5348920e44a4b2` | `validated` |
| A1.2 Vast runtime lock v2 | `lockset` | `engineering_preflight_scaffold` | `control/armindex/a1.2/runtime-lock.v2.json` | `df4094edde1b69a9b15c2cc24a574d733c23a818380c21fe898b441e3567d336` | `validated` |
| A1.2 OCI image digest contract v2 | `contract` | `engineering_preflight_scaffold` | `control/armindex/a1.2/image-digest-contract.v2.json` | `49fa3ffda00d9466326e005dce7cbebc8a090bc167fc5292b1279461dc03327b` | `validated` |
| A1.2 Vast live preflight checklist v2 | `checklist` | `engineering_preflight_scaffold` | `control/armindex/a1.2/launch-checklist.v2.json` | `f0539e0baa359b1b1218811097e2b1238eec44b9708db45347f982ab6fa61d16` | `validated` |
| A1.2 Owner-local termination plan v2 | `runbook` | `engineering_preflight_scaffold` | `control/armindex/a1.2/shutdown-plan.v2.json` | `4c560d28a265c847343270adbecc6d850ee900c8680ec03ddc61f9697422469f` | `validated` |
| A1.2 remote safe-export allowlist v2 | `contract` | `engineering_preflight_scaffold` | `control/armindex/a1.2/safe-export-allowlist.v2.json` | `55e027de43ce48b9cf85b54598fd92f1119bc9a51940ce75ba754fcc5901fa91` | `validated` |
| A1.2 Vast preflight runbook v2 | `runbook` | `engineering_preflight_scaffold` | `control/runbooks/A1_2_VAST_4X3090_PREFLIGHT_V2.md` | `98eb5dda969b034c723fd00eb561664c370f2a76f12c591c9d0c495a7e7dcfb1` | `validated` |
| A1.2 beginner Owner runbook | `runbook` | `engineering_preflight_scaffold` | `docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK.md` | `9019036b721b03dcbaa5525668dcc63c6827e6c9b6dbb3715c90ab62c633ca2f` | `validated` |
| A1.2 local SSH coordinator | `tool` | `engineering_preflight_scaffold` | `scripts/a1_2_vast/Invoke-A12VastCoordinator.ps1` | `88e30d1211cd8260e3f76045a9631982aabbbb0d7cac2d5fb36d455540aa00d2` | `validated` |
| A1.2 Owner-local TTL watchdog | `tool` | `engineering_preflight_scaffold` | `scripts/a1_2_vast/Invoke-A12VastWatchdog.ps1` | `c6eaca0457b20be05a83d54a0d1ef96f2489b5bb1e4788e90396ef45458ad7b2` | `validated` |
| A1.2 Vast preflight ledger v2 | `ledger` | `engineering_preflight_scaffold` | `control/armindex/a1.2/vast-4x3090-preflight-ledger.v2.jsonl` | `3a9a6d8ee840f98405abeae714c909b9aecb202336c857bad8bddfe637e5803a` | `validated` |
| A1.2 Vast preflight closeout validation audit | `audit` | `engineering_preflight_scaffold` | `outputs/audits/rigor/a1.2-vast-4x3090-preflight-closeout-validation-20260806.json` | `8bfd4817abfeb10c48169efc80bb5c655760da1ab03b06fad98435cb0072e33c` | `validated` |
| A1.2 immutable ARM-02 remote job | `manifest` | `engineering_preflight_scaffold` | `control/armindex/a1.2/jobs/v2/ARM-02.json` | `a82f3c2c276529f1a2f04bc1728a06bdc5c40d8a0d9d019a5a536c4b089e2d6b` | `validated` |
| A1.2 immutable ARM-03 remote job | `manifest` | `engineering_preflight_scaffold` | `control/armindex/a1.2/jobs/v2/ARM-03.json` | `20b21cfcd4b256b1ca8b61a53584c70940e0ea278d4a072cae2aa99a410822a2` | `validated` |
| A1.2 immutable ARM-04 remote job | `manifest` | `engineering_preflight_scaffold` | `control/armindex/a1.2/jobs/v2/ARM-04.json` | `e4c8c562b222b835fd50afc59d92180f7defffd5ec0a2902d845d2e9b2dca5ed` | `validated` |
| A1.2 immutable ARM-05 remote job | `manifest` | `engineering_preflight_scaffold` | `control/armindex/a1.2/jobs/v2/ARM-05.json` | `a787141e7168567b8b2294333c6883d93080546f15efe349d938ceb766bbd6a3` | `validated` |
| A1.2 Vast post-commit correction receipt v3 | `receipt` | `engineering_preflight_correction` | `campaigns/armindex-multiretriever-v2/evidence/a1.2-vast-4x3090-postcommit-migration.receipt.v3.json` | `f031a08a23d58b96e67461353d83b8f11243a5cf8ab4a2b571b8e1940876a8d0` | `validated` |
| A1.2 Vast post-commit execution contract v3 | `contract` | `engineering_preflight_correction` | `control/armindex/a1.2/execution-contract.v3.json` | `716ea6542df7a668a1148ef0eed1eb61d13bd6a8a3663874ec8b66db697c5b81` | `validated` |
| A1.2 Vast post-commit preflight runbook v3 | `runbook` | `engineering_preflight_correction` | `control/runbooks/A1_2_VAST_4X3090_POSTCOMMIT_PREFLIGHT_V3.md` | `10b1ab667fac6ca06de1b92671ff42fdedd09dee748237d217cafe710144bca7` | `validated` |
| A1.2 beginner Owner runbook v3 | `runbook` | `engineering_preflight_correction` | `docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V3.md` | `354c19d3debcda6d8c82c0a67d6fe310999c1f883198d6ceba4af0f4120f26de` | `validated` |
| A1.2 Vast post-commit receipt schema v3 | `schema` | `engineering_preflight_correction` | `schemas/armindex/a1.2-vast-4x3090-postcommit.v3.json` | `c9b46a32e5c805b0d861e6f79a9965426a2db7df70e89b1397b188535d867f03` | `validated` |
| A1.2 Vast post-commit validator | `tool` | `engineering_preflight_correction` | `src/myis_research/armindex/a1_2_vast_postcommit.py` | `0d84c8d235c351c51e509c759a6dea0e9f011c4c4a031d556922a423b0839d8e` | `validated` |
| A1.2 v3 deterministic projection stability repair | `audit` | `engineering_validation` | `outputs/audits/rigor/a1.2-v3-projection-stability-repair-20260806.json` | `e0abfe9c9c7a77c6e31a61160f7760133f4313a8bda12d74956ddd2bdbcfcf6e` | `validated` |
| A1.2 runtime-minimal direct-base receipt v5 | `receipt` | `engineering_preflight_revision` | `campaigns/armindex-multiretriever-v2/evidence/a1.2-runtime-minimal-direct-base-migration.receipt.v5.json` | `8d0480b4c6ef8ae3631f04f8038761db2eaee660eef01644605530dfeea715a5` | `validated` |
| A1.2 runtime-minimal direct-base execution contract v5 | `contract` | `engineering_preflight_revision` | `control/armindex/a1.2/execution-contract.direct-base.v5.json` | `8fabe004c96e561f7a2fbf8a1ff6819acfa1038d9b49021b11f1da07b956d238` | `validated` |
| A1.2 direct-base runtime lock v5 | `manifest` | `engineering_preflight_revision` | `control/armindex/a1.2/runtime-lock.direct-base.v5.json` | `914159988fe902ca138847a1d8db3c9e0ea9c378bf1b39398cc1784f4346742e` | `validated` |
| A1.2 direct-base image contract v5 | `contract` | `engineering_preflight_revision` | `control/armindex/a1.2/image-digest-contract.direct-base.v5.json` | `5c691dc92f9f41fc02fbe388545fb3da34b08d9fdb1a9893012d11768d72829b` | `validated` |
| A1.2 direct-base topology contract v5 | `manifest` | `engineering_preflight_revision` | `control/armindex/a1.2/topology-contract.direct-base.v5.json` | `e36f28b6fceea0d1e25518d49b37afc808af76afeba0010767f068b7bb2f684e` | `validated` |
| A1.2 direct-base receipt schema v5 | `schema` | `engineering_preflight_revision` | `schemas/armindex/a1.2-runtime-minimal-direct-base.v5.json` | `84e9b58322917b9f76140a2e849d4128cfaac60c3673596013f81cdc4806d3e7` | `validated` |
| A1.2 beginner Owner direct-base runbook v5 | `runbook` | `engineering_preflight_revision` | `docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V5.md` | `a7a624164df92938bf096bd7b61e7313fb111649a7c37c339c2f995eacb1f02c` | `validated` |
| A1.2 direct-base validator module v5 | `tool` | `engineering_preflight_revision` | `src/myis_research/armindex/a1_2_runtime_minimal_direct_base.py` | `75e8e3e94a0d2daf0337621475148d2be2e2e01f15a66153accb6e60b58cde0d` | `validated` |

## Metrics

| Metric | Split | Scope | Value | n | Denominator | Evidence |
|---|---|---|---:|---:|---|---|
| `fixture_compile_latency_p50_ms`@100 | `synthetic` | `A1.1` | `3.2813` | `11` | `host_observed_fixed_synthetic_adapter_workload` | `engineering_preflight_revision` |
| `fixture_index_build_latency_p50_ms`@100 | `synthetic` | `A1.1` | `0.8286` | `11` | `host_observed_fixed_synthetic_adapter_workload` | `engineering_preflight_revision` |
| `fixture_search_workload_latency_p50_ms`@100 | `synthetic` | `A1.1` | `0.7241` | `11` | `host_observed_fixed_synthetic_adapter_workload` | `engineering_preflight_revision` |
| `fixture_search_throughput_qps`@100 | `synthetic` | `A1.1` | `2449.58858` | `22` | `host_observed_fixed_synthetic_adapter_workload` | `engineering_preflight_revision` |
| `fixture_peak_python_allocation_bytes`@100 | `synthetic` | `A1.1` | `111702` | `11` | `tracemalloc_peak_for_fixed_synthetic_adapter_workload` | `engineering_preflight_revision` |
| `fixture_recall_at_100`@100 | `synthetic` | `A1.1` | `1.0` | `2` | `macro_mean_relevant_families` | `engineering_preflight_revision` |
| `fixture_ndcg_at_100`@100 | `synthetic` | `A1.1` | `1.0` | `2` | `macro_mean_graded_family_relevance` | `engineering_preflight_revision` |
| `fixture_ndcg_at_10`@10 | `synthetic` | `A1.1` | `1.0` | `2` | `macro_mean_graded_family_relevance` | `engineering_preflight_revision` |

Fixture values are synthetic engineering diagnostics and are never reported as measured performance.

## Result

**Output:** The phase contains a completed A1.1 five-arm synthetic adapter fixture, the preserved A1.2 v1-v3 lineage for 5 arms, the earlier CPU preflight with status blocked_owner_input and 10 blocker group(s), and v5 direct-base preparation using pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime on linux/amd64.

**Result:** A1 engineering preparation is current through v5 with 21 live checks pending; measured ArmIndex, Selection, Final, GPU-reservation, and charged-resource counters remain zero.

**Decision:** active

## Interpretation

The offline evidence preserves the v2 four-worker fixture and v3 correction, then binds v5 to the direct official image manifest sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20 while removing custom-image and nested-container steps. It does not establish live hardware readiness, retrieval quality, execution adoption, or scientific authorization.

## Supported Claims

- The phase contains a completed A1.1 five-arm synthetic adapter fixture, the preserved A1.2 v1-v3 lineage for 5 arms, the earlier CPU preflight with status blocked_owner_input and 10 blocker group(s), and v5 direct-base preparation using pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime on linux/amd64. (evidence: a11-adapter-task-receipt, a11-adapter-fixture-manifest, a11-adapter-fixture-receipt, a11-adapter-runbook, a11-adapter-ledger, a12-gpu-execution-proposal, a12-contract-scaffold-receipt, a12-execution-contract, a12-arm01-rank-parity, a12-budget-profile, a12-execution-envelope, a12-model-lockset, a12-launch-checklist, a12-shutdown-plan, a12-scaffold-runbook, a12-scaffold-ledger, a12-report-archive-audit, a12-closeout-validation-audit, a12-owner-local-preflight, a12-owner-local-mlflow-registration, a12-vast-v2-migration-receipt, a12-vast-v2-execution-contract, a12-vast-v2-synthetic-receipt, a12-vast-v2-budget, a12-vast-v2-topology, a12-vast-v2-runtime, a12-vast-v2-image, a12-vast-v2-checklist, a12-vast-v2-shutdown, a12-vast-v2-allowlist, a12-vast-v2-runbook, a12-vast-v2-owner-runbook, a12-vast-v2-coordinator, a12-vast-v2-watchdog, a12-vast-v2-ledger, a12-vast-v2-closeout-audit, a12-vast-v2-job-arm-02, a12-vast-v2-job-arm-03, a12-vast-v2-job-arm-04, a12-vast-v2-job-arm-05, a12-vast-v3-correction-receipt, a12-vast-v3-execution-contract, a12-vast-v3-control-runbook, a12-vast-v3-owner-runbook, a12-vast-v3-schema, a12-vast-v3-validator, a12-vast-v3-projection-stability-repair, a12-direct-base-v5-receipt, a12-direct-base-v5-contract, a12-direct-base-v5-runtime-lock, a12-direct-base-v5-image-contract, a12-direct-base-v5-topology, a12-direct-base-v5-schema, a12-direct-base-v5-runbook, a12-direct-base-v5-module)

## Unsupported Claims

- Measured P2 improvement or candidate superiority before a real measured run.
- Final-split generalization or publication release before D2 and D3.
- Causal or legal conclusions from retrieval aggregates.

## Failures and Recovery

- `a1.2-unsynced-console-entrypoint-20260805` -> `a1.2-module-cli-validation-20260805`; status `repaired_and_validated`; counters changed `False`; failure `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `dd20d4bf1c73eeeef23872e626444e9420791636403b4ac6b6f9f01942911d08`; recovery `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `dd20d4bf1c73eeeef23872e626444e9420791636403b4ac6b6f9f01942911d08`
- `a1.2-mlflow-v2-experiment-missing-20260805` -> `a1.2-zero-data-mlflow-bootstrap-20260805`; status `repaired_and_validated`; counters changed `False`; failure `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `dd20d4bf1c73eeeef23872e626444e9420791636403b4ac6b6f9f01942911d08`; recovery `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `dd20d4bf1c73eeeef23872e626444e9420791636403b4ac6b6f9f01942911d08`
- `a1.2-full-suite-runner-timeout-20260805` -> `a1.2-full-suite-extended-timeout-pass-20260805`; status `repaired_and_validated`; counters changed `False`; failure `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `dd20d4bf1c73eeeef23872e626444e9420791636403b4ac6b6f9f01942911d08`; recovery `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `dd20d4bf1c73eeeef23872e626444e9420791636403b4ac6b6f9f01942911d08`
- `a1.2-extended-style-profile-debt-20260805` -> `a1.2-scoped-correctness-ruff-pass-20260805`; status `bounded_and_validated`; counters changed `False`; failure `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `dd20d4bf1c73eeeef23872e626444e9420791636403b4ac6b6f9f01942911d08`; recovery `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `dd20d4bf1c73eeeef23872e626444e9420791636403b4ac6b6f9f01942911d08`
- `a1.2-report-builder-second-source-read-20260805` -> `a1.2-single-read-model-recovery-projection-20260805`; status `repaired_and_validated`; counters changed `False`; failure `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `dd20d4bf1c73eeeef23872e626444e9420791636403b4ac6b6f9f01942911d08`; recovery `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `dd20d4bf1c73eeeef23872e626444e9420791636403b4ac6b6f9f01942911d08`
- `a1.2-stale-projection-source-receipt-20260805` -> `a1.2-latest-validated-source-selector-20260805`; status `repaired_and_validated`; counters changed `False`; failure `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `dd20d4bf1c73eeeef23872e626444e9420791636403b4ac6b6f9f01942911d08`; recovery `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `dd20d4bf1c73eeeef23872e626444e9420791636403b4ac6b6f9f01942911d08`
- `a1.2-volatile-mlflow-archive-counts-in-audit-20260805` -> `a1.2-stable-mlflow-doctor-audit-contract-20260805`; status `repaired_and_validated`; counters changed `False`; failure `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `dd20d4bf1c73eeeef23872e626444e9420791636403b4ac6b6f9f01942911d08`; recovery `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `dd20d4bf1c73eeeef23872e626444e9420791636403b4ac6b6f9f01942911d08`
- `a1.2-v2-pyproject-v1-source-binding-drift-20260806` -> `a1.2-v2-module-command-v1-byte-preservation-20260806`; status `repaired_and_validated`; counters changed `False`; failure `outputs/audits/rigor/a1.2-vast-4x3090-preflight-closeout-validation-20260806.json` / `8bfd4817abfeb10c48169efc80bb5c655760da1ab03b06fad98435cb0072e33c`; recovery `outputs/audits/rigor/a1.2-vast-4x3090-preflight-closeout-validation-20260806.json` / `8bfd4817abfeb10c48169efc80bb5c655760da1ab03b06fad98435cb0072e33c`
- `a1.2-v2-stale-generated-projection-source-20260806` -> `a1.2-v2-receipt-first-shared-read-model-sync-20260806`; status `repaired_and_validated`; counters changed `False`; failure `outputs/audits/rigor/a1.2-vast-4x3090-preflight-closeout-validation-20260806.json` / `8bfd4817abfeb10c48169efc80bb5c655760da1ab03b06fad98435cb0072e33c`; recovery `outputs/audits/rigor/a1.2-vast-4x3090-preflight-closeout-validation-20260806.json` / `8bfd4817abfeb10c48169efc80bb5c655760da1ab03b06fad98435cb0072e33c`
- `a1.2-v2-postcommit-head-tree-regeneration-defect-20260806` -> `a1.2-v3-receipt-bound-clean-commit-validator-20260806`; status `repaired_and_validated`; counters changed `False`; failure `campaigns/armindex-multiretriever-v2/evidence/a1.2-vast-4x3090-postcommit-migration.receipt.v3.json` / `f031a08a23d58b96e67461353d83b8f11243a5cf8ab4a2b571b8e1940876a8d0`; recovery `campaigns/armindex-multiretriever-v2/evidence/a1.2-vast-4x3090-postcommit-migration.receipt.v3.json` / `f031a08a23d58b96e67461353d83b8f11243a5cf8ab4a2b571b8e1940876a8d0`
- `a1.2-v3-runtime-git-identity-projection-drift-20260806` -> `a1.2-v3-runtime-git-identity-projection-exclusion-20260806`; status `repaired_and_validated`; counters changed `False`; failure `outputs/audits/rigor/a1.2-v3-projection-stability-repair-20260806.json` / `e0abfe9c9c7a77c6e31a61160f7760133f4313a8bda12d74956ddd2bdbcfcf6e`; recovery `outputs/audits/rigor/a1.2-v3-projection-stability-repair-20260806.json` / `e0abfe9c9c7a77c6e31a61160f7760133f4313a8bda12d74956ddd2bdbcfcf6e`

## Governance and Safety

- `protected_data_accessed`: False
- `measured_execution`: False
- `gpu`: False
- `paid_api`: False
- `network_model_download`: False
- `provider_fallback`: False
- `d2`: waiting_owner
- `d3`: waiting_owner
- `final_split`: closed
- `real_counters`: `{"candidate_count": 0, "final_accesses": 0, "measured_runs": 0, "selection_accesses": 0, "shortlist_count": 0}`
- `evidence_class`: engineering_preflight_revision
- `scientific_authority`: False

## Decision

Status: **active**. A1 engineering preparation is current through v5 with 21 live checks pending; measured ArmIndex, Selection, Final, GPU-reservation, and charged-resource counters remain zero.

## Next Action

Owner stages local runtime-minimal artifacts, then later opens one quoted Vast worker and runs the v5 SSH preflight without measured retrieval.

Measured P2, real selection, and final evaluation must not start automatically from this report.

## Evidence Links

- a11-adapter-task-receipt
- a11-adapter-fixture-manifest
- a11-adapter-fixture-receipt
- a11-adapter-runbook
- a11-adapter-ledger
- a12-gpu-execution-proposal
- a12-contract-scaffold-receipt
- a12-execution-contract
- a12-arm01-rank-parity
- a12-budget-profile
- a12-execution-envelope
- a12-model-lockset
- a12-launch-checklist
- a12-shutdown-plan
- a12-scaffold-runbook
- a12-scaffold-ledger
- a12-report-archive-audit
- a12-closeout-validation-audit
- a12-owner-local-preflight
- a12-owner-local-mlflow-registration
- a12-vast-v2-migration-receipt
- a12-vast-v2-execution-contract
- a12-vast-v2-synthetic-receipt
- a12-vast-v2-budget
- a12-vast-v2-topology
- a12-vast-v2-runtime
- a12-vast-v2-image
- a12-vast-v2-checklist
- a12-vast-v2-shutdown
- a12-vast-v2-allowlist
- a12-vast-v2-runbook
- a12-vast-v2-owner-runbook
- a12-vast-v2-coordinator
- a12-vast-v2-watchdog
- a12-vast-v2-ledger
- a12-vast-v2-closeout-audit
- a12-vast-v2-job-arm-02
- a12-vast-v2-job-arm-03
- a12-vast-v2-job-arm-04
- a12-vast-v2-job-arm-05
- a12-vast-v3-correction-receipt
- a12-vast-v3-execution-contract
- a12-vast-v3-control-runbook
- a12-vast-v3-owner-runbook
- a12-vast-v3-schema
- a12-vast-v3-validator
- a12-vast-v3-projection-stability-repair
- a12-direct-base-v5-receipt
- a12-direct-base-v5-contract
- a12-direct-base-v5-runtime-lock
- a12-direct-base-v5-image-contract
- a12-direct-base-v5-topology
- a12-direct-base-v5-schema
- a12-direct-base-v5-runbook
- a12-direct-base-v5-module
