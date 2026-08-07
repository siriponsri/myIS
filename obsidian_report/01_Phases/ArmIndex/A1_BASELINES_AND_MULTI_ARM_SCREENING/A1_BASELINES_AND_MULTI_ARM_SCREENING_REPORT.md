---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "3a0f4effa34596eff6c2a4d358c86c214315d3e13dcfaf9d4f78775e16e7a944"
read_model_sha256: "ee71fc4bdcdbbda57ddb2a9edc710029e49d9783efe9e550d75c954afd0a20b4"
source_commit: "1cdff09343121b26cda968263d6a83cb403fba28"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "live_engineering_synthetic_preflight"
scientific_authority: false
claim_boundary: "Engineering-only synthetic adapter and lifecycle evidence on one Vast 4xRTX3090 instance; no retrieval-quality, publication, or general workload claim."
generated_from_revision: "3a0f4effa34596eff6c2a4d358c86c214315d3e13dcfaf9d4f78775e16e7a944"
last_material_update: "2026-08-07T10:14:03Z"
next_authorized_action: "Owner may destroy and verify provider absence, or explicitly authorize continue_next_goal_on_PLAN only while the continuation policy requirements remain true."
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-07T10:14:03Z"
updated_at: "2026-08-07T10:14:03Z"
note_id: "A1_BASELINES_AND_MULTI_ARM_SCREENING-MASTER"
note_type: "phase_report"
phase_id: "A1_BASELINES_AND_MULTI_ARM_SCREENING"
task_id: null
workflow_status: "in_progress"
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
- `program_state`: a1_2_live_synthetic_preflight_pass_owner_disposition_pending_launch_locked
- `authorization`: D1_START_CAMPAIGN; D2/D3 remain Owner-only
- `claim_boundary`: No unsupported scientific claim

## Inputs and Frozen Bindings

- `source_of_truth`: `control/source-of-truth.yaml`; SHA-256 `784803a48bb71b802685da8d9af7c772c22177562c85e6f81ceeeca64c387c1b`
- `campaign`: `control/campaigns/armindex-multiretriever-v2.yaml`; SHA-256 `44f36dc7bb9fb5e73b4733ea35ad4b68baf6feeec67a4abd6bdb94502e5d7049`
- `git_commit`: 1cdff09343121b26cda968263d6a83cb403fba28
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
- `a12_direct_base_v5_receipt`: `campaigns/armindex-multiretriever-v2/evidence/a1.2-runtime-minimal-direct-base-migration.receipt.v5.json`; SHA-256 `b8b71e4fab7faa0ace7fdb8857f9ec41bc344781eb416c5d7ceaa947b352859a`
- `a12_direct_base_v5_execution_contract`: `control/armindex/a1.2/execution-contract.direct-base.v5.json`; SHA-256 `df7b1232554b6fe320f396bb290419a75f41b2e70ba463a6caf64bc0d08dc563`

## Work Performed

A1.1 synthetic adapter evidence and the A1.2 launch-locked execution scaffold are both validated. The additive v5 direct-base revision preserves v1-v3 history, binds the official PyTorch linux/amd64 manifest, and removes custom image and nested-container steps from the active path. The additive v6 correction handles direct-container observability and offline environment injection. The additive v7 same-instance repair preserves the missing-pydantic wheelhouse and frozen-tree bytecode failures, requires a fresh repair root, hash-validated reuse, and bytecode suppression; continuation remains conditional on complete future live evidence and a separately authorized next goal. ARM-01 remains local CPU only; four dense source revisions and runtime-minimal allowlists are frozen, while Owner-local manifests, adapter parity, live provider binding, termination dry run, and explicit adoption remain pending.

### A1.2 resource planning boundary

The proposal remains `proposal_not_adopted_execution_locked`. It specifies `1` GPU with at least `24` GiB VRAM; preferred classes are RTX_4090_24GB, RTX_3090_24GB, L4_24GB, A10_24GB. A100/H100 required: `False`. The planning range is `8-16` GPU hours and `10-20` elapsed hours. Raw compute is estimated at USD `2.4-12.8`; hard stops are USD `5` for parity/pilot, USD `18` for the common screen, USD `23` for A1, and USD `100` for the campaign.

Owner prerequisites:

- make_owner_local_protected_root_available_to_the_runner
- prestage_frozen_model_artifacts_without_agent_credential_access
- ensure_Vast_or_equivalent_account_credit_and_credentials_are_available
- intervene_only_if_provider_unavailable_hashes_conflict_or_budget_must_increase

### A1.2 scaffold and launch state

The offline scaffold is `a1_2_live_synthetic_preflight_pass_owner_disposition_pending_launch_locked` with `5` model/source locks. ARM-01 has `1` offline CPU adapter lock ready; `4` dense Owner-local artifact manifests and `2` checklist items remain pending. Launch ready: `False`; measured execution: `False`. The closeout audit passed `17` validation groups and retained `7` bounded failure/recovery records.

The immutable v2 preparation remains `offline_preparation_complete_live_owner_preflight_pending` and the v3 correction remains `postcommit_validator_prepared_live_owner_preflight_pending`. The active additive v5 direct-base revision is `direct_base_preflight_prepared_local_owner_stage_pending` with image `pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime` at manifest `sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20` on `linux/amd64`. The additive v6 live-container correction is `live_correction_prepared_preflight_pending` and remains synthetic-only with launch `False` and adoption `False`. The additive v7 same-instance repair is `same_instance_repair_prepared_preflight_pending` with `2` preserved engineering failure(s), a fresh runtime root requirement `True`, and bytecode suppression `True`. The additive v8 validation-complete frozen-bundle repair is `validation_complete_bundle_repair_prepared_preflight_pending` with `3` preserved engineering failure(s), validation lineage complete `True`, and a fresh root `/opt/myis/a1.2-v8`. The additive v9 execution-lifecycle repair is `execution_lifecycle_repair_prepared_preflight_pending` with implementation validation `True`, live synthetic execution pending `True`, and fresh root `/opt/myis/a1.2-v9`. Collected live synthetic result: `PASS`; 4 arm receipts, Qwen measured adapter max `32768`, checkpoint/resume `PASS`, and guest teardown `PASS`. It launches the official image directly, excludes custom-image build and nested-container steps, and does not authorize launch or adoption.

The Owner continuity policy is `active_owner_policy`. Its default is `destroy_and_verify_provider_instance_absent`; `continue_next_goal_on_PLAN` remains conditional and is not authorized now.

Owner-local prerequisites still required:

- keep the protected root, qrels, membership, credentials, and evaluator payloads local;
- preserve the safe export and all return artifacts under the Owner store;
- prove provider destruction and TTL, or explicitly authorize the unchanged-instance continuation policy for a separately authorized next PLAN goal;
- do not interpret this engineering PASS as retrieval-quality or publication evidence.

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
| A1.2 runtime-minimal direct-base receipt v5 | `receipt` | `engineering_preflight_revision` | `campaigns/armindex-multiretriever-v2/evidence/a1.2-runtime-minimal-direct-base-migration.receipt.v5.json` | `b8b71e4fab7faa0ace7fdb8857f9ec41bc344781eb416c5d7ceaa947b352859a` | `validated` |
| A1.2 runtime-minimal direct-base execution contract v5 | `contract` | `engineering_preflight_revision` | `control/armindex/a1.2/execution-contract.direct-base.v5.json` | `df7b1232554b6fe320f396bb290419a75f41b2e70ba463a6caf64bc0d08dc563` | `validated` |
| A1.2 direct-base runtime lock v5 | `manifest` | `engineering_preflight_revision` | `control/armindex/a1.2/runtime-lock.direct-base.v5.json` | `914159988fe902ca138847a1d8db3c9e0ea9c378bf1b39398cc1784f4346742e` | `validated` |
| A1.2 direct-base image contract v5 | `contract` | `engineering_preflight_revision` | `control/armindex/a1.2/image-digest-contract.direct-base.v5.json` | `5c691dc92f9f41fc02fbe388545fb3da34b08d9fdb1a9893012d11768d72829b` | `validated` |
| A1.2 direct-base topology contract v5 | `manifest` | `engineering_preflight_revision` | `control/armindex/a1.2/topology-contract.direct-base.v5.json` | `e36f28b6fceea0d1e25518d49b37afc808af76afeba0010767f068b7bb2f684e` | `validated` |
| A1.2 direct-base receipt schema v5 | `schema` | `engineering_preflight_revision` | `schemas/armindex/a1.2-runtime-minimal-direct-base.v5.json` | `84e9b58322917b9f76140a2e849d4128cfaac60c3673596013f81cdc4806d3e7` | `validated` |
| A1.2 beginner Owner direct-base runbook v5 | `runbook` | `engineering_preflight_revision` | `docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V5.md` | `a7a624164df92938bf096bd7b61e7313fb111649a7c37c339c2f995eacb1f02c` | `validated` |
| A1.2 direct-base validator module v5 | `tool` | `engineering_preflight_revision` | `src/myis_research/armindex/a1_2_runtime_minimal_direct_base.py` | `75e8e3e94a0d2daf0337621475148d2be2e2e01f15a66153accb6e60b58cde0d` | `validated` |
| A1.2 live-container correction receipt v6 | `receipt` | `live_engineering_preflight_correction` | `campaigns/armindex-multiretriever-v2/evidence/a1.2-live-preflight-correction.receipt.v6.json` | `3918f0c6e9699a3c66de3f70d2c1efc1daead8e86f03647f4236ddb37cdab9a9` | `validated` |
| A1.2 live-container correction contract v6 | `contract` | `live_engineering_preflight_correction` | `control/armindex/a1.2/execution-contract.live-preflight.v6.json` | `29642d4d6a00f385e8a3fceedbf0c06c23ceae147f6da77a8bcd513ea1f420b0` | `validated` |
| A1.2 live-container correction receipt schema v6 | `schema` | `live_engineering_preflight_correction` | `schemas/armindex/a1.2-live-preflight-correction.v6.json` | `433391902514a7b6b2ba3fb7a1a4e53ae4b7f4b19f5caf28bbe5ad832ae1e5ed` | `validated` |
| A1.2 live-container correction validator v6 | `tool` | `live_engineering_preflight_correction` | `src/myis_research/armindex/a1_2_live_preflight_revision.py` | `d700afb1f6e0e4bd7d13bb3be2dd273c28f0030dcbf1e5549fa086324c782a19` | `validated` |
| A1.2 synthetic live preflight module v6 | `tool` | `live_engineering_preflight_correction` | `src/myis_research/armindex/a1_2_live_preflight.py` | `f84170f6744b6a9f31207331662328f383fa802dab1b80c26cdc7d4b0d9bddc2` | `validated` |
| A1.2 beginner Owner runbook v6 | `runbook` | `live_engineering_preflight_correction` | `docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V6.md` | `355c22e34b7a6e44ddeea37a8cdb37a35dbf315fe29368bb4aa6ba98dcf2313d` | `validated` |
| A1.2 Owner conditional instance-continuation policy | `decision` | `owner_policy_for_engineering_continuity` | `control/armindex/a1.2/owner-instance-continuation-policy.v1.json` | `28402c57d22400b343cdc94ef88aa285ce94eedf3cb44680c9679c6be9654acd` | `validated` |
| A1.2 same-instance repair receipt v7 | `receipt` | `live_engineering_preflight_repair` | `campaigns/armindex-multiretriever-v2/evidence/a1.2-live-preflight-repair.receipt.v7.json` | `8790fca3ff8a5d4a0cdfa19d41c0534df00b3ae6d2597455b89b290ba4f39edd` | `validated` |
| A1.2 same-instance repair contract v7 | `contract` | `live_engineering_preflight_repair` | `control/armindex/a1.2/execution-contract.live-preflight-repair.v7.json` | `590d8d196522078dc047eaa5e1c0a03e0ff93313719e2f6f2d10e9ed6be08c61` | `validated` |
| A1.2 same-instance repair receipt schema v7 | `schema` | `live_engineering_preflight_repair` | `schemas/armindex/a1.2-live-preflight-repair.v7.json` | `ba2fda966d828a0e86b8c64d25e69e569b490c70e6d4b8eddd6415939740c029` | `validated` |
| A1.2 same-instance repair validator v7 | `tool` | `live_engineering_preflight_repair` | `src/myis_research/armindex/a1_2_live_preflight_repair_v7.py` | `17846d4691faa3d354fc19d9172bc3c0bf82bc3fb3d14289d4c5a64957e0d0f3` | `validated` |
| A1.2 beginner Owner same-instance repair runbook v7 | `runbook` | `live_engineering_preflight_repair` | `docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V7.md` | `23e2aa879e3918fce840d23885108ba6eb9e48fdf7ea4874f072189fd1d5e060` | `validated` |
| A1.2 same-instance repair coordinator v7 | `tool` | `live_engineering_preflight_repair` | `scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinatorV7.ps1` | `274e09a06b81ab2291a4683681d53d7265666392e1c025cedb96d0344fef2d58` | `validated` |
| A1.2 same-instance repair bootstrap v7 | `tool` | `live_engineering_preflight_repair` | `scripts/a1_2_vast/remote-bootstrap-direct-base-v7.sh` | `a573987e368a325534e05c15cf3a8b3ed6b3d6f800d3120e4231a0c989fa9c6f` | `validated` |
| A1.2 preflight supplement validator v7 | `tool` | `live_engineering_preflight_repair` | `scripts/a1_2_vast/validate_preflight_supplement_v7.py` | `6ea824337585a972c543989bb792775f3597967ff736cc30dd547997d5798291` | `validated` |
| A1.2 preflight supplement requirements v7 | `manifest` | `live_engineering_preflight_repair` | `containers/a1_2_vast_4x3090/runtime/requirements.preflight-supplement.v7.txt` | `8262320bc0541873a29cf0362566998dc7039e72d92a820f802a3bf8a0118fe6` | `validated` |
| A1.2 supplement wheelhouse workflow v7 | `workflow` | `live_engineering_preflight_repair` | `.github/workflows/a1-2-preflight-supplement-wheelhouse-v7.yml` | `3c397dcf9d2bac02924a2d64c4be1cdf30b54bcfea3ee558d9b650f089af4843` | `validated` |
| A1.2 validation-complete frozen-bundle repair receipt v8 | `receipt` | `live_engineering_preflight_packaging_repair` | `campaigns/armindex-multiretriever-v2/evidence/a1.2-live-preflight-packaging-repair.receipt.v8.json` | `aaa15d54d73d78fd6237f71d99f9068579b2bc4451a6af15417024e345e076a6` | `validated` |
| A1.2 validation-complete frozen-bundle repair contract v8 | `contract` | `live_engineering_preflight_packaging_repair` | `control/armindex/a1.2/execution-contract.live-preflight-packaging-repair.v8.json` | `d46193a975a7d3afdb3c6a3b5c038157e6bd246458bc054c043adc80c45ac020` | `validated` |
| A1.2 validation-complete frozen-bundle repair schema v8 | `schema` | `live_engineering_preflight_packaging_repair` | `schemas/armindex/a1.2-live-preflight-packaging-repair.v8.json` | `eadce7b35347d8fb57df9e2e83b2cdcbb62f41671eee6544acaaab8a7223f3f9` | `validated` |
| A1.2 validation-complete frozen-bundle validator v8 | `tool` | `live_engineering_preflight_packaging_repair` | `src/myis_research/armindex/a1_2_live_preflight_packaging_v8.py` | `2f33493e979d227839b2aca0a4be2a51302fca06e70a5f706ca3d39491cc3ccc` | `validated` |
| A1.2 beginner Owner validation-complete bundle runbook v8 | `runbook` | `live_engineering_preflight_packaging_repair` | `docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V8.md` | `8eab91cf0082dc1f165c17183016b4a8c5a3b971cbe91bcd0b973dc71b19a3fd` | `validated` |
| A1.2 validation-complete bundle coordinator v8 | `tool` | `live_engineering_preflight_packaging_repair` | `scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinatorV8.ps1` | `142d78db8e1407cad23385e7e837ee3e50383e4914818190f53c73b3cc045d67` | `validated` |
| A1.2 validation-complete bundle bootstrap v8 | `tool` | `live_engineering_preflight_packaging_repair` | `scripts/a1_2_vast/remote-bootstrap-direct-base-v8.sh` | `d01f70b7c4a1abdacf6b5045876cbd011010104643dda594f9c8b84a5ba499e4` | `validated` |
| A1.2 execution-lifecycle repair receipt v9 | `receipt` | `live_engineering_preflight_execution_lifecycle_repair` | `campaigns/armindex-multiretriever-v2/evidence/a1.2-live-preflight-execution-lifecycle.receipt.v9.json` | `0435823ca9e0e94695059c5aaba6c1f3406cc2873e6c2041ff132cc8f640fcbf` | `validated` |
| A1.2 execution-lifecycle repair contract v9 | `contract` | `live_engineering_preflight_execution_lifecycle_repair` | `control/armindex/a1.2/execution-contract.live-preflight-execution-lifecycle.v9.json` | `abf4769d94a5c45fb09d0d0694400d8963ef53a1bdca3d5408f19c89232b35a6` | `validated` |
| A1.2 execution-lifecycle repair schema v9 | `schema` | `live_engineering_preflight_execution_lifecycle_repair` | `schemas/armindex/a1.2-live-preflight-execution-lifecycle.v9.json` | `945188d828eccda02dc841f53176b92e6ba74cc436c45f624ed2a10f193041a0` | `validated` |
| A1.2 execution-lifecycle contract validator v9 | `tool` | `live_engineering_preflight_execution_lifecycle_repair` | `src/myis_research/armindex/a1_2_live_preflight_execution_v9.py` | `8b8d29d08f4939cc96131e4265e0760dcb986c1aa1851cef3c8c7957f264ad3f` | `validated` |
| A1.2 attempt-scoped live runtime v9 | `tool` | `live_engineering_preflight_execution_lifecycle_repair` | `src/myis_research/armindex/a1_2_live_preflight_runtime_v9.py` | `13f1191cd411adac3699ee688de9545d7ead9ace6f3679ee634b95e62fd45894` | `validated` |
| A1.2 beginner Owner execution-lifecycle runbook v9 | `runbook` | `live_engineering_preflight_execution_lifecycle_repair` | `docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V9.md` | `4aa934e8e80a8e8685136711190eea1b6a3c9d2fbf0f05f2506cfbdfdd563cce` | `validated` |
| A1.2 execution-lifecycle coordinator v9 | `tool` | `live_engineering_preflight_execution_lifecycle_repair` | `scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinatorV9.ps1` | `b3651b77c06c06dda54169e31fb880261cf9db0b553a3dcf004d592f09ebafce` | `validated` |
| A1.2 execution-lifecycle bootstrap v9 | `tool` | `live_engineering_preflight_execution_lifecycle_repair` | `scripts/a1_2_vast/remote-bootstrap-direct-base-v9.sh` | `c99dfc7bcb1289136df3ae992346a25a0b6e3ba66bb25689821b50f4246e9358` | `validated` |
| A1.2 four-GPU synthetic launcher v9 | `tool` | `live_engineering_preflight_execution_lifecycle_repair` | `scripts/a1_2_vast/remote-live-preflight-v9.sh` | `958ae71cf029ad2843f4ba06e3db170f310bfc887dfd28fd791b6f856586c73f` | `validated` |
| A1.2 live synthetic preflight result receipt v9 | `receipt` | `live_engineering_synthetic_preflight` | `campaigns/armindex-multiretriever-v2/evidence/a1.2-live-synthetic-preflight-result.receipt.v9.json` | `52d1d892c4ce034e3d4b0887a5bddbb362d9747c3b343e766ad2a4302c3f13d6` | `validated` |

## Metrics

| Metric | Split | Scope | Value | n | Denominator | Evidence |
|---|---|---|---:|---:|---|---|
| `fixture_compile_latency_p50_ms`@100 | `synthetic` | `A1.1` | `3.2813` | `11` | `host_observed_fixed_synthetic_adapter_workload` | `live_engineering_synthetic_preflight` |
| `fixture_index_build_latency_p50_ms`@100 | `synthetic` | `A1.1` | `0.8286` | `11` | `host_observed_fixed_synthetic_adapter_workload` | `live_engineering_synthetic_preflight` |
| `fixture_search_workload_latency_p50_ms`@100 | `synthetic` | `A1.1` | `0.7241` | `11` | `host_observed_fixed_synthetic_adapter_workload` | `live_engineering_synthetic_preflight` |
| `fixture_search_throughput_qps`@100 | `synthetic` | `A1.1` | `2449.58858` | `22` | `host_observed_fixed_synthetic_adapter_workload` | `live_engineering_synthetic_preflight` |
| `fixture_peak_python_allocation_bytes`@100 | `synthetic` | `A1.1` | `111702` | `11` | `tracemalloc_peak_for_fixed_synthetic_adapter_workload` | `live_engineering_synthetic_preflight` |
| `fixture_recall_at_100`@100 | `synthetic` | `A1.1` | `1.0` | `2` | `macro_mean_relevant_families` | `live_engineering_synthetic_preflight` |
| `fixture_ndcg_at_100`@100 | `synthetic` | `A1.1` | `1.0` | `2` | `macro_mean_graded_family_relevance` | `live_engineering_synthetic_preflight` |
| `fixture_ndcg_at_10`@10 | `synthetic` | `A1.1` | `1.0` | `2` | `macro_mean_graded_family_relevance` | `live_engineering_synthetic_preflight` |

Fixture values are synthetic engineering diagnostics and are never reported as measured performance.

## Result

**Output:** The phase contains a completed A1.1 five-arm synthetic adapter fixture, preserved A1.2 v1-v8 lineage for 5 arms, the earlier CPU preflight with status blocked_owner_input and 10 blocker group(s), and v9 execution-lifecycle repair preparation using pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime on linux/amd64. The additive v9 live synthetic result is PASS for 4 dense arms.

**Result:** A1 engineering preflight is current through v9 with live synthetic status PASS; Owner instance disposition remains pending, and measured ArmIndex, Selection, Final, and charged-resource counters remain zero.

**Decision:** active

## Interpretation

The offline evidence preserves the v2 four-worker fixture and v3 correction, binds v5 to the direct official image manifest sha256:2428b92ebbaeceba5572b98c18c8a94e43162bead6e88588ad54471147c58a20, records v6 direct-container corrections, adds v7 same-instance repair controls, and uses v8 to close frozen validator lineage. The v9 result validates four synthetic adapter receipts, Qwen adapter-level 32768-token capacity, checkpoint/resume, safe export, and guest teardown. It does not establish retrieval quality, execution adoption, scientific authorization, or unconditional instance reuse.

## Supported Claims

- The phase contains a completed A1.1 five-arm synthetic adapter fixture, preserved A1.2 v1-v8 lineage for 5 arms, the earlier CPU preflight with status blocked_owner_input and 10 blocker group(s), and v9 execution-lifecycle repair preparation using pytorch/pytorch:2.6.0-cuda11.8-cudnn9-runtime on linux/amd64. The additive v9 live synthetic result is PASS for 4 dense arms. (evidence: a11-adapter-task-receipt, a11-adapter-fixture-manifest, a11-adapter-fixture-receipt, a11-adapter-runbook, a11-adapter-ledger, a12-gpu-execution-proposal, a12-contract-scaffold-receipt, a12-execution-contract, a12-arm01-rank-parity, a12-budget-profile, a12-execution-envelope, a12-model-lockset, a12-launch-checklist, a12-shutdown-plan, a12-scaffold-runbook, a12-scaffold-ledger, a12-report-archive-audit, a12-closeout-validation-audit, a12-owner-local-preflight, a12-owner-local-mlflow-registration, a12-vast-v2-migration-receipt, a12-vast-v2-execution-contract, a12-vast-v2-synthetic-receipt, a12-vast-v2-budget, a12-vast-v2-topology, a12-vast-v2-runtime, a12-vast-v2-image, a12-vast-v2-checklist, a12-vast-v2-shutdown, a12-vast-v2-allowlist, a12-vast-v2-runbook, a12-vast-v2-owner-runbook, a12-vast-v2-coordinator, a12-vast-v2-watchdog, a12-vast-v2-ledger, a12-vast-v2-closeout-audit, a12-vast-v2-job-arm-02, a12-vast-v2-job-arm-03, a12-vast-v2-job-arm-04, a12-vast-v2-job-arm-05, a12-vast-v3-correction-receipt, a12-vast-v3-execution-contract, a12-vast-v3-control-runbook, a12-vast-v3-owner-runbook, a12-vast-v3-schema, a12-vast-v3-validator, a12-vast-v3-projection-stability-repair, a12-direct-base-v5-receipt, a12-direct-base-v5-contract, a12-direct-base-v5-runtime-lock, a12-direct-base-v5-image-contract, a12-direct-base-v5-topology, a12-direct-base-v5-schema, a12-direct-base-v5-runbook, a12-direct-base-v5-module, a12-live-preflight-v6-receipt, a12-live-preflight-v6-contract, a12-live-preflight-v6-schema, a12-live-preflight-v6-validator, a12-live-preflight-v6-preflight-module, a12-live-preflight-v6-owner-runbook, a12-owner-instance-continuation-policy-v1, a12-live-preflight-v7-receipt, a12-live-preflight-v7-contract, a12-live-preflight-v7-schema, a12-live-preflight-v7-validator, a12-live-preflight-v7-owner-runbook, a12-live-preflight-v7-coordinator, a12-live-preflight-v7-bootstrap, a12-live-preflight-v7-supplement-validator, a12-live-preflight-v7-supplement-requirements, a12-live-preflight-v7-supplement-workflow, a12-live-preflight-v8-receipt, a12-live-preflight-v8-contract, a12-live-preflight-v8-schema, a12-live-preflight-v8-validator, a12-live-preflight-v8-owner-runbook, a12-live-preflight-v8-coordinator, a12-live-preflight-v8-bootstrap, a12-live-preflight-v9-receipt, a12-live-preflight-v9-contract, a12-live-preflight-v9-schema, a12-live-preflight-v9-validator, a12-live-preflight-v9-runtime, a12-live-preflight-v9-owner-runbook, a12-live-preflight-v9-coordinator, a12-live-preflight-v9-bootstrap, a12-live-preflight-v9-launcher, a12-live-synthetic-preflight-result-v9)

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
- `evidence_class`: live_engineering_synthetic_preflight
- `scientific_authority`: False

## Decision

Status: **active**. A1 engineering preflight is current through v9 with live synthetic status PASS; Owner instance disposition remains pending, and measured ArmIndex, Selection, Final, and charged-resource counters remain zero.

## Next Action

Owner may destroy and verify provider absence, or explicitly authorize continue_next_goal_on_PLAN only while the continuation policy requirements remain true.

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
- a12-live-preflight-v6-receipt
- a12-live-preflight-v6-contract
- a12-live-preflight-v6-schema
- a12-live-preflight-v6-validator
- a12-live-preflight-v6-preflight-module
- a12-live-preflight-v6-owner-runbook
- a12-owner-instance-continuation-policy-v1
- a12-live-preflight-v7-receipt
- a12-live-preflight-v7-contract
- a12-live-preflight-v7-schema
- a12-live-preflight-v7-validator
- a12-live-preflight-v7-owner-runbook
- a12-live-preflight-v7-coordinator
- a12-live-preflight-v7-bootstrap
- a12-live-preflight-v7-supplement-validator
- a12-live-preflight-v7-supplement-requirements
- a12-live-preflight-v7-supplement-workflow
- a12-live-preflight-v8-receipt
- a12-live-preflight-v8-contract
- a12-live-preflight-v8-schema
- a12-live-preflight-v8-validator
- a12-live-preflight-v8-owner-runbook
- a12-live-preflight-v8-coordinator
- a12-live-preflight-v8-bootstrap
- a12-live-preflight-v9-receipt
- a12-live-preflight-v9-contract
- a12-live-preflight-v9-schema
- a12-live-preflight-v9-validator
- a12-live-preflight-v9-runtime
- a12-live-preflight-v9-owner-runbook
- a12-live-preflight-v9-coordinator
- a12-live-preflight-v9-bootstrap
- a12-live-preflight-v9-launcher
- a12-live-synthetic-preflight-result-v9
