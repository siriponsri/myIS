---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "b91bbeb83e25bb1d016b79db6f64ee49162c172433b996c219a4d3e2ef43cb40"
read_model_sha256: "004c227ac9746c898d9856ed45f0d64a6989baf53be16e84cfc582b9de477cf5"
source_commit: "8b4b3d6f39aa06580fc2c46743ea7fad8f5f390e"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering_contract_scaffold"
scientific_authority: false
claim_boundary: "offline_scaffold_only_no_measured_retrieval_claim"
generated_from_revision: "b91bbeb83e25bb1d016b79db6f64ee49162c172433b996c219a4d3e2ef43cb40"
last_material_update: "2026-08-05T15:46:35Z"
next_authorized_action: "/goal Run the Owner-local A1.2 artifact-manifest and external-termination dry-run preflight on CPU. Validate complete SHA256SUMS manifests for the four dense arms, freeze byte hashes for Snowflake remote code and the Qwen measured maximum length, bind a live quote and provider instance identity, and prove provider termination/TTL without exposing credentials or protected payloads. Do not reserve GPU capacity or start measured retrieval until every launch-checklist item passes and the unchanged execution contract is explicitly adopted."
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-05T15:46:35Z"
updated_at: "2026-08-05T15:46:35Z"
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
- `program_state`: a1_2_contract_scaffold_complete_launch_locked
- `authorization`: D1_START_CAMPAIGN; D2/D3 remain Owner-only
- `claim_boundary`: No unsupported scientific claim

## Inputs and Frozen Bindings

- `source_of_truth`: `control/source-of-truth.yaml`; SHA-256 `27cdd4ddbe84d69985616c689a65191a78e9461f4c0e99d9b48e90bfc681ba11`
- `campaign`: `control/campaigns/armindex-multiretriever-v2.yaml`; SHA-256 `f06e85d015aaaaca7d33e40b5484a2edf03e6f5e72964365c42030980ace5447`
- `git_commit`: 8b4b3d6f39aa06580fc2c46743ea7fad8f5f390e
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
- `a12_closeout_validation_audit`: `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json`; SHA-256 `c34de6c8f1bfa7b29814536e9825c75ba869644289a0c2012b65271b04e5e0c5`

## Work Performed

A1.1 synthetic adapter evidence and the A1.2 launch-locked execution scaffold are both validated. ARM-01 remains local CPU only; four dense source revisions and critical commitments are frozen, while Owner-local runtime manifests, adapter parity, live provider binding, termination dry run, and explicit adoption remain pending.

### A1.2 resource planning boundary

The proposal remains `proposal_not_adopted_execution_locked`. It specifies `1` GPU with at least `24` GiB VRAM; preferred classes are RTX_4090_24GB, RTX_3090_24GB, L4_24GB, A10_24GB. A100/H100 required: `False`. The planning range is `8-16` GPU hours and `10-20` elapsed hours. Raw compute is estimated at USD `2.4-12.8`; hard stops are USD `5` for parity/pilot, USD `18` for the common screen, USD `23` for A1, and USD `100` for the campaign.

Owner prerequisites:

- make_owner_local_protected_root_available_to_the_runner
- prestage_frozen_model_artifacts_without_agent_credential_access
- ensure_Vast_or_equivalent_account_credit_and_credentials_are_available
- intervene_only_if_provider_unavailable_hashes_conflict_or_budget_must_increase

### A1.2 scaffold and launch state

The offline scaffold is `a1_2_contract_scaffold_complete_launch_locked` with `5` model/source locks. ARM-01 has `1` offline CPU adapter lock ready; `4` dense Owner-local artifact manifests and `9` checklist items remain pending. Launch ready: `False`; measured execution: `False`. The closeout audit passed `16` validation groups and retained `6` bounded failure/recovery records.

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
| A1.2 closeout validation audit | `audit` | `engineering_contract_scaffold` | `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` | `c34de6c8f1bfa7b29814536e9825c75ba869644289a0c2012b65271b04e5e0c5` | `validated` |

## Metrics

| Metric | Split | Scope | Value | n | Denominator | Evidence |
|---|---|---|---:|---:|---|---|
| `fixture_compile_latency_p50_ms`@100 | `synthetic` | `A1.1` | `3.2813` | `11` | `host_observed_fixed_synthetic_adapter_workload` | `engineering_contract_scaffold` |
| `fixture_index_build_latency_p50_ms`@100 | `synthetic` | `A1.1` | `0.8286` | `11` | `host_observed_fixed_synthetic_adapter_workload` | `engineering_contract_scaffold` |
| `fixture_search_workload_latency_p50_ms`@100 | `synthetic` | `A1.1` | `0.7241` | `11` | `host_observed_fixed_synthetic_adapter_workload` | `engineering_contract_scaffold` |
| `fixture_search_throughput_qps`@100 | `synthetic` | `A1.1` | `2449.58858` | `22` | `host_observed_fixed_synthetic_adapter_workload` | `engineering_contract_scaffold` |
| `fixture_peak_python_allocation_bytes`@100 | `synthetic` | `A1.1` | `111702` | `11` | `tracemalloc_peak_for_fixed_synthetic_adapter_workload` | `engineering_contract_scaffold` |
| `fixture_recall_at_100`@100 | `synthetic` | `A1.1` | `1.0` | `2` | `macro_mean_relevant_families` | `engineering_contract_scaffold` |
| `fixture_ndcg_at_100`@100 | `synthetic` | `A1.1` | `1.0` | `2` | `macro_mean_graded_family_relevance` | `engineering_contract_scaffold` |
| `fixture_ndcg_at_10`@10 | `synthetic` | `A1.1` | `1.0` | `2` | `macro_mean_graded_family_relevance` | `engineering_contract_scaffold` |

Fixture values are synthetic engineering diagnostics and are never reported as measured performance.

## Result

**Output:** The phase contains a completed A1.1 five-arm synthetic adapter fixture and a validated, launch-locked A1.2 execution scaffold for 5 arms.

**Result:** A1 engineering scaffolding is current; A1.2 scientific screening remains unexecuted and measured, Selection, and Final counters remain zero.

**Decision:** active

## Interpretation

A1 now has a reproducible CPU anchor and a bounded pre-GPU contract. Scientific completion still requires Owner-local artifact validation, explicit adoption, and the separately authorized common screen.

## Supported Claims

- The phase contains a completed A1.1 five-arm synthetic adapter fixture and a validated, launch-locked A1.2 execution scaffold for 5 arms. (evidence: a11-adapter-task-receipt, a11-adapter-fixture-manifest, a11-adapter-fixture-receipt, a11-adapter-runbook, a11-adapter-ledger, a12-gpu-execution-proposal, a12-contract-scaffold-receipt, a12-execution-contract, a12-arm01-rank-parity, a12-budget-profile, a12-execution-envelope, a12-model-lockset, a12-launch-checklist, a12-shutdown-plan, a12-scaffold-runbook, a12-scaffold-ledger, a12-report-archive-audit, a12-closeout-validation-audit)

## Unsupported Claims

- Measured P2 improvement or candidate superiority before a real measured run.
- Final-split generalization or publication release before D2 and D3.
- Causal or legal conclusions from retrieval aggregates.

## Failures and Recovery

- `a1.2-unsynced-console-entrypoint-20260805` -> `a1.2-module-cli-validation-20260805`; status `repaired_and_validated`; counters changed `False`; failure `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `c34de6c8f1bfa7b29814536e9825c75ba869644289a0c2012b65271b04e5e0c5`; recovery `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `c34de6c8f1bfa7b29814536e9825c75ba869644289a0c2012b65271b04e5e0c5`
- `a1.2-mlflow-v2-experiment-missing-20260805` -> `a1.2-zero-data-mlflow-bootstrap-20260805`; status `repaired_and_validated`; counters changed `False`; failure `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `c34de6c8f1bfa7b29814536e9825c75ba869644289a0c2012b65271b04e5e0c5`; recovery `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `c34de6c8f1bfa7b29814536e9825c75ba869644289a0c2012b65271b04e5e0c5`
- `a1.2-full-suite-runner-timeout-20260805` -> `a1.2-full-suite-extended-timeout-pass-20260805`; status `repaired_and_validated`; counters changed `False`; failure `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `c34de6c8f1bfa7b29814536e9825c75ba869644289a0c2012b65271b04e5e0c5`; recovery `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `c34de6c8f1bfa7b29814536e9825c75ba869644289a0c2012b65271b04e5e0c5`
- `a1.2-extended-style-profile-debt-20260805` -> `a1.2-scoped-correctness-ruff-pass-20260805`; status `bounded_and_validated`; counters changed `False`; failure `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `c34de6c8f1bfa7b29814536e9825c75ba869644289a0c2012b65271b04e5e0c5`; recovery `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `c34de6c8f1bfa7b29814536e9825c75ba869644289a0c2012b65271b04e5e0c5`
- `a1.2-report-builder-second-source-read-20260805` -> `a1.2-single-read-model-recovery-projection-20260805`; status `repaired_and_validated`; counters changed `False`; failure `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `c34de6c8f1bfa7b29814536e9825c75ba869644289a0c2012b65271b04e5e0c5`; recovery `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `c34de6c8f1bfa7b29814536e9825c75ba869644289a0c2012b65271b04e5e0c5`
- `a1.2-stale-projection-source-receipt-20260805` -> `a1.2-latest-validated-source-selector-20260805`; status `repaired_and_validated`; counters changed `False`; failure `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `c34de6c8f1bfa7b29814536e9825c75ba869644289a0c2012b65271b04e5e0c5`; recovery `outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json` / `c34de6c8f1bfa7b29814536e9825c75ba869644289a0c2012b65271b04e5e0c5`

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
- `evidence_class`: engineering_contract_scaffold
- `scientific_authority`: False

## Decision

Status: **active**. A1 engineering scaffolding is current; A1.2 scientific screening remains unexecuted and measured, Selection, and Final counters remain zero.

## Next Action

/goal Run the Owner-local A1.2 artifact-manifest and external-termination dry-run preflight on CPU. Validate complete SHA256SUMS manifests for the four dense arms, freeze byte hashes for Snowflake remote code and the Qwen measured maximum length, bind a live quote and provider instance identity, and prove provider termination/TTL without exposing credentials or protected payloads. Do not reserve GPU capacity or start measured retrieval until every launch-checklist item passes and the unchanged execution contract is explicitly adopted.

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
