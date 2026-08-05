---
schema_version: "myis.obsidian-note.v2"
read_model_revision: "68a5e65f0a33764c6f0f665a26fbfb5ad090b8ea9a639f8aa2502e0966fee99d"
read_model_sha256: "7d2fe287959edf2997cc8d88aac56dda6f77debcdbf7de674f10eefd9145932a"
source_commit: "1149f9e63ac6174a3ce4bc5a553d793b7d707b0b"
projection_schema_version: "myis.integrated-projection.v2"
source_run_ids: []
source_manifest_sha256: []
related_literature_ids: []
related_decision_ids: ["D2_OPEN_FINAL","D3_SUBMIT_RELEASE"]
evidence_class: "engineering"
scientific_authority: false
claim_boundary: "engineering_provenance_only"
generated_from_revision: "68a5e65f0a33764c6f0f665a26fbfb5ad090b8ea9a639f8aa2502e0966fee99d"
last_material_update: "2026-08-05T15:56:15Z"
next_authorized_action: "/goal Run the Owner-local A1.2 artifact-manifest and external-termination dry-run preflight on CPU. Validate complete SHA256SUMS manifests for the four dense arms, freeze byte hashes for Snowflake remote code and the Qwen measured maximum length, bind a live quote and provider instance identity, and prove provider termination/TTL without exposing credentials or protected payloads. Do not reserve GPU capacity or start measured retrieval until every launch-checklist item passes and the unchanged execution contract is explicitly adopted."
managed_by: "myis-report"
edit_policy: "generated_do_not_edit"
safe_to_present: true
created_at: "2026-08-05T15:56:15Z"
updated_at: "2026-08-05T15:56:15Z"
note_id: "A0_MIGRATION_FOUNDATION-MASTER"
note_type: "phase_report"
phase_id: "A0_MIGRATION_FOUNDATION"
task_id: null
workflow_status: "complete"
evidence_maturity: "non_scientific"
claim_level: "none"
---

# A0_MIGRATION_FOUNDATION

Generated from the validated report record. Manual edits may be replaced; use the separate Owner Notes area for personal annotations.

## Objective

Migrate repository, freeze contracts, preserve evidence, and run compute-feasibility fixtures.

## Starting State

- `phase`: A1_BASELINES_AND_MULTI_ARM_SCREENING
- `task`: None
- `program_state`: a1_2_contract_scaffold_complete_launch_locked
- `authorization`: D1_START_CAMPAIGN; D2/D3 remain Owner-only
- `claim_boundary`: No unsupported scientific claim

## Inputs and Frozen Bindings

- `source_of_truth`: `control/source-of-truth.yaml`; SHA-256 `27cdd4ddbe84d69985616c689a65191a78e9461f4c0e99d9b48e90bfc681ba11`
- `campaign`: `control/campaigns/armindex-multiretriever-v2.yaml`; SHA-256 `f06e85d015aaaaca7d33e40b5484a2edf03e6f5e72964365c42030980ace5447`
- `git_commit`: 1149f9e63ac6174a3ce4bc5a553d793b7d707b0b
- `migration_budget`: `control/budgets/armindex-migration-v2.yaml`; SHA-256 `48bab215d10ef82c0fe8206702f75f4b212df12792d7475131888d50161821ec`
- `armindex_schema_root`: `schemas/armindex`; SHA-256 `6ede89f83141bf4f051413feedf5316388defe5565051a53eaed386c4c62320a`
- `historical_scope`: `control/campaigns/scope-autoindex-v1.yaml`; SHA-256 `a86d73657988713d62ddfb12c9c01da367af2e97922363233ef8cd453fb20ce9`

## Work Performed

The active repository is migrated in place to ArmIndex with versioned contracts and projections while historical SCOPE/P1/P2 evidence remains immutable and readable.

## Artifacts Produced

These references explain what each artifact is for; the bytes remain governed by canonical paths.

| Artifact | Type | Evidence | Safe URI | SHA-256 | Validation |
|---|---|---|---|---|---|
| Active ArmIndex campaign | `control` | `engineering` | `control/campaigns/armindex-multiretriever-v2.yaml` | `f06e85d015aaaaca7d33e40b5484a2edf03e6f5e72964365c42030980ace5447` | `validated` |
| ArmIndex AutoIndex and HarnessOpt contract | `contract` | `engineering` | `control/plans/ARMINDEX_AUTOINDEX_HARNESSOPT_CONTRACT.md` | `882d08758fdd4fe64ccf1941e2cf426527a894b54c4c50bfbbb1d382c9c53d7e` | `validated` |
| ArmIndex migration manifest | `manifest` | `engineering` | `archive/migration-records/armindex-20260804/migration-manifest.v1.json` | `e64372bd6b6e746f92a028749375661b3e0c0b34900b418c6602d6425f62d435` | `validated` |
| ArmIndex migration receipt | `receipt` | `engineering` | `archive/migration-records/armindex-20260804/migration-receipt.v1.json` | `576efe28a33b5e7cbbce352444fb9373ab0b5d886bef2a3a2a4cc491adbd3cac` | `validated` |
| ArmIndex MLflow migration receipt | `receipt` | `engineering` | `archive/migration-records/armindex-20260804/mlflow-migration-receipt.v1.json` | `ff2c94d587fbf0577ebacfbdb1f626450ca1c494bb9a9a042aad7fe412b212c7` | `validated` |
| ArmIndex read-model fragment schema | `schema` | `engineering` | `schemas/armindex/read-model.v1.json` | `6ede89f83141bf4f051413feedf5316388defe5565051a53eaed386c4c62320a` | `validated` |
| A0.10 legacy code-harvest ledger | `ledger` | `engineering` | `control/armindex/a0.10-legacy-code-harvest-ledger.v1.json` | `46fa064f0ed3f73352028ca3443096e33244c0cc68898cafdb02c59fc2328eaf` | `validated` |
| A0.10 legacy code-harvest receipt | `receipt` | `engineering` | `campaigns/armindex-multiretriever-v2/evidence/a0.10-legacy-code-harvest.receipt.v1.json` | `dc824eea4bad0c552cc59198883284e8984108ef45b4b099e5d7b1058252bdcc` | `validated` |
| A0.10 synthetic vertical-slice receipt | `receipt` | `engineering` | `outputs/fixtures/armindex/a0.10/vertical-slice-v1/receipt.json` | `d4e7e99b2f00e21f4d9afe0e6616f07929652f7d5578957a906737981da43dd6` | `validated` |
| A0.10 repository hygiene audit | `audit` | `engineering` | `outputs/audits/repository/repository-hygiene-a0.10-20260804.json` | `1fcae4ac1966706194df7d76d730516f62507eeb246103495eafa65bb959045b` | `validated` |
| A0.10 output-root relocation receipt | `receipt` | `engineering` | `outputs/audits/dashboard/output-root-relocation-20260804.json` | `b98afb03be1e9a7d5dd75dbb421218b6b46b72376ad1f7e392450c93051ddf46` | `validated` |
| A0.10 ThaiPha-Lex source verification receipt | `receipt` | `engineering` | `outputs/audits/repository/thaipha-lex-source-verification-a0.10-20260804.json` | `417e9559d102dca6d34c50c771310b91a9511d143276df94e5a706fb1c2753ab` | `validated` |
| A0.8 compute and storage task receipt | `receipt` | `engineering_fixture` | `campaigns/armindex-multiretriever-v2/evidence/a0.8-compute-storage-feasibility.receipt.v1.json` | `730c019a0bc5dd27f5014e0938ce3f0691ebb7aa9421d2585494472d7d4a6ac5` | `validated` |
| A0.8 synthetic feasibility manifest | `manifest` | `engineering_fixture` | `outputs/fixtures/armindex/a0.8/compute-storage-v1/manifest.json` | `6500c576252b3cde0b29bd51218425b179f3654ba549e1debf30d946fefdbc6d` | `validated` |
| A0.8 synthetic feasibility receipt | `receipt` | `engineering_fixture` | `outputs/fixtures/armindex/a0.8/compute-storage-v1/receipt.json` | `a8034adc381a4545182114486ea2fd2c18155fca31cf2a201e75c023364155cf` | `validated` |
| A0.8 compute and storage runbook | `runbook` | `engineering_fixture` | `control/runbooks/A0_8_COMPUTE_STORAGE_FEASIBILITY_FIXTURES.md` | `a52289b44f154f82418bc4dfbfcd8f32f697e70fca732d59e5b7bcbe809d47d6` | `validated` |
| A0.8 append-only execution ledger | `ledger` | `engineering_fixture` | `control/armindex/a0.8-compute-storage-feasibility-ledger.v1.jsonl` | `29a998b734c843dbd4df1a88d4076542181df597cddfe6571a7c364fce8ae962` | `validated` |
| A0 phase closeout receipt | `receipt` | `engineering` | `campaigns/armindex-multiretriever-v2/evidence/a0-phase-closeout.receipt.v1.json` | `95614c498657a41f82fae9cf8f69b042773382cd714f91814524574b534a3a05` | `validated` |
| A0.9 validation and safety audit | `audit` | `engineering` | `outputs/audits/armindex/a0.9-validation-safety-closeout-20260805.json` | `4e7c09af6c186060bed36b90b5e997171bfc67b9c0d7606fb7522c7394733f1a` | `validated` |
| A0.9 validation and closeout runbook | `runbook` | `engineering` | `control/runbooks/A0_9_VALIDATION_SAFETY_CLOSEOUT.md` | `f655cd80c67ac839d78416c062a3a701d31449af25be1539d9507183bbaf737e` | `validated` |
| A0.9 append-only closeout ledger | `ledger` | `engineering` | `control/armindex/a0.9-validation-safety-closeout-ledger.v1.jsonl` | `23cb341b65f8c811e2be444cbb2fb125abe3135ed81f6168269e848c3b406586` | `validated` |

## Metrics

| Metric | Split | Scope | Value | n | Denominator | Evidence |
|---|---|---|---:|---:|---|---|
| `fixture_compile_latency_p50_ms`@32 | `synthetic` | `A0.8` | `92.5391` | `11` | `host_observed_synthetic_scale_32_documents_128` | `engineering` |
| `fixture_index_build_latency_p50_ms`@32 | `synthetic` | `A0.8` | `20.9904` | `11` | `host_observed_synthetic_scale_32_documents_128` | `engineering` |
| `fixture_search_workload_latency_p50_ms`@32 | `synthetic` | `A0.8` | `13.7252` | `11` | `host_observed_synthetic_scale_32_documents_128` | `engineering` |
| `fixture_search_throughput_qps`@32 | `synthetic` | `A0.8` | `143.88875` | `22` | `host_observed_synthetic_scale_32_documents_128` | `engineering` |
| `fixture_peak_python_allocation_bytes`@32 | `synthetic` | `A0.8` | `2727977` | `11` | `host_observed_synthetic_scale_32_documents_128` | `engineering` |
| `fixture_portable_sparse_payload_bytes`@32 | `synthetic` | `A0.8` | `156846` | `352` | `host_observed_synthetic_scale_32_documents_128` | `engineering` |

Fixture values are synthetic engineering diagnostics and are never reported as measured performance.

## Result

**Output:** Versioned ArmIndex control, schema, code, and projection state with historical SCOPE/P1 evidence preserved by pointer.

**Result:** A0_MIGRATION_FOUNDATION is completed; ArmIndex measured runs, Selection, and Final counters remain zero.

**Decision:** completed

## Interpretation

This is engineering migration provenance only and supports no retrieval-quality, champion, or production claim.

## Supported Claims

- Versioned ArmIndex control, schema, code, and projection state with historical SCOPE/P1 evidence preserved by pointer. (evidence: control-campaigns-armindex-multiretriever-v2.yaml, control-plans-ARMINDEX_AUTOINDEX_HARNESSOPT_CONTRACT.md, archive-migration-records-armindex-20260804-migration-manifest.v1.json, archive-migration-records-armindex-20260804-migration-receipt.v1.json, archive-migration-records-armindex-20260804-mlflow-migration-receipt.v1.json, schemas-armindex-read-model.v1.json, a010-legacy-code-harvest-ledger, a010-legacy-code-harvest-receipt, a010-synthetic-vertical-slice-receipt, a010-repository-hygiene-audit, a010-output-root-relocation-receipt, a010-source-verification-receipt, a08-compute-storage-task-receipt, a08-compute-storage-fixture-manifest, a08-compute-storage-fixture-receipt, a08-compute-storage-runbook, a08-compute-storage-ledger, a09-phase-closeout-receipt, a09-validation-audit, a09-closeout-runbook, a09-closeout-ledger)

## Unsupported Claims

- Measured P2 improvement or candidate superiority before a real measured run.
- Final-split generalization or publication release before D2 and D3.
- Causal or legal conclusions from retrieval aggregates.

## Failures and Recovery

- `a0.10-legacy-code-harvest-independent-revise-20260804` -> `a0.10-legacy-code-harvest-independent-accept-20260804`; status `repaired_and_validated`; counters changed `False`; failure `outputs/audits/rigor/a0.10-legacy-code-harvest-independent-revise-20260804.json` / `a69df70559a949c1f7b1d60c02b4f6461215f2724297068dd21cab8cc0900353`; recovery `outputs/audits/rigor/a0.10-legacy-code-harvest-independent-accept-20260804.json` / `4049ac9ccfaed94378484cdc7641eb8ee82dc0089a0b41db4421d40b78d73ce4`

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
- `evidence_class`: engineering
- `scientific_authority`: False

## Decision

Status: **completed**. A0_MIGRATION_FOUNDATION is completed; ArmIndex measured runs, Selection, and Final counters remain zero.

## Next Action

/goal Run the Owner-local A1.2 artifact-manifest and external-termination dry-run preflight on CPU. Validate complete SHA256SUMS manifests for the four dense arms, freeze byte hashes for Snowflake remote code and the Qwen measured maximum length, bind a live quote and provider instance identity, and prove provider termination/TTL without exposing credentials or protected payloads. Do not reserve GPU capacity or start measured retrieval until every launch-checklist item passes and the unchanged execution contract is explicitly adopted.

Measured P2, real selection, and final evaluation must not start automatically from this report.

## Evidence Links

- control-campaigns-armindex-multiretriever-v2.yaml
- control-plans-ARMINDEX_AUTOINDEX_HARNESSOPT_CONTRACT.md
- archive-migration-records-armindex-20260804-migration-manifest.v1.json
- archive-migration-records-armindex-20260804-migration-receipt.v1.json
- archive-migration-records-armindex-20260804-mlflow-migration-receipt.v1.json
- schemas-armindex-read-model.v1.json
- a010-legacy-code-harvest-ledger
- a010-legacy-code-harvest-receipt
- a010-synthetic-vertical-slice-receipt
- a010-repository-hygiene-audit
- a010-output-root-relocation-receipt
- a010-source-verification-receipt
- a08-compute-storage-task-receipt
- a08-compute-storage-fixture-manifest
- a08-compute-storage-fixture-receipt
- a08-compute-storage-runbook
- a08-compute-storage-ledger
- a09-phase-closeout-receipt
- a09-validation-audit
- a09-closeout-runbook
- a09-closeout-ledger
