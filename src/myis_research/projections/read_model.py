"""Build the single aggregate read model consumed by Dashboard, Brain, and Paper."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from functools import lru_cache
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from ..armindex import ArmIndexContractError, build_armindex_projection
from ..armindex.a1_2_cell_eda_package_v16 import (
    CellEdaPackageV16Error,
    validate_cell_eda_package_file,
)
from ..armindex.a1_2_cell_eda_package_v16 import (
    package_path as a1_2_cell_eda_package_path,
)
from ..armindex.a1_2_contract import (
    ARM01_PARITY_RECEIPT_PATH as A12_ARM01_PARITY_RECEIPT_PATH,
)
from ..armindex.a1_2_contract import (
    CONTROL_ROOT as A12_CONTROL_ROOT,
)
from ..armindex.a1_2_contract import (
    LEDGER_PATH as A12_LEDGER_PATH,
)
from ..armindex.a1_2_contract import (
    RECEIPT_PATH as A12_RECEIPT_PATH,
)
from ..armindex.a1_2_contract import (
    RUNBOOK_PATH as A12_RUNBOOK_PATH,
)
from ..armindex.a1_2_contract import (
    validate_a1_2_scaffold,
)
from ..armindex.a1_2_instance_disposition_v13 import (
    POLICY_PATH as A12_V13_DISPOSITION_POLICY_PATH,
)
from ..armindex.a1_2_instance_disposition_v13 import (
    REVISION_ID as A12_V13_DISPOSITION_REVISION_ID,
)
from ..armindex.a1_2_instance_disposition_v13 import (
    SCHEMA_PATH as A12_V13_DISPOSITION_SCHEMA_PATH,
)
from ..armindex.a1_2_instance_disposition_v13 import (
    current_status as current_a1_2_v13_disposition_status,
)
from ..armindex.a1_2_live_preflight_execution_v9 import (
    CONTRACT_PATH as A12_V9_CONTRACT_PATH,
)
from ..armindex.a1_2_live_preflight_execution_v9 import (
    RECEIPT_PATH as A12_V9_RECEIPT_PATH,
)
from ..armindex.a1_2_live_preflight_execution_v9 import (
    REVISION_ID as A12_V9_REVISION_ID,
)
from ..armindex.a1_2_live_preflight_execution_v9 import (
    SCHEMA_PATH as A12_V9_SCHEMA_PATH,
)
from ..armindex.a1_2_live_preflight_execution_v9 import (
    validate_revision as validate_a1_2_v9_execution_lifecycle,
)
from ..armindex.a1_2_live_preflight_packaging_v8 import (
    CONTRACT_PATH as A12_V8_CONTRACT_PATH,
)
from ..armindex.a1_2_live_preflight_packaging_v8 import (
    RECEIPT_PATH as A12_V8_RECEIPT_PATH,
)
from ..armindex.a1_2_live_preflight_packaging_v8 import (
    REVISION_ID as A12_V8_REVISION_ID,
)
from ..armindex.a1_2_live_preflight_packaging_v8 import (
    SCHEMA_PATH as A12_V8_SCHEMA_PATH,
)
from ..armindex.a1_2_live_preflight_packaging_v8 import (
    validate_revision as validate_a1_2_v8_packaging_repair,
)
from ..armindex.a1_2_live_preflight_repair_v7 import (
    CONTRACT_PATH as A12_V7_CONTRACT_PATH,
)
from ..armindex.a1_2_live_preflight_repair_v7 import (
    RECEIPT_PATH as A12_V7_RECEIPT_PATH,
)
from ..armindex.a1_2_live_preflight_repair_v7 import (
    REVISION_ID as A12_V7_REVISION_ID,
)
from ..armindex.a1_2_live_preflight_repair_v7 import (
    SCHEMA_PATH as A12_V7_SCHEMA_PATH,
)
from ..armindex.a1_2_live_preflight_repair_v7 import (
    validate_live_repair_v7 as validate_a1_2_v7_live_repair,
)
from ..armindex.a1_2_live_preflight_result_v9 import (
    RECEIPT_PATH as A12_V9_RESULT_RECEIPT_PATH,
)
from ..armindex.a1_2_live_preflight_result_v9 import (
    REVISION_ID as A12_V9_RESULT_REVISION_ID,
)
from ..armindex.a1_2_live_preflight_result_v9 import (
    SCHEMA_PATH as A12_V9_RESULT_SCHEMA_PATH,
)
from ..armindex.a1_2_live_preflight_result_v9 import (
    validate_result as validate_a1_2_v9_live_result,
)
from ..armindex.a1_2_live_preflight_revision import (
    CONTRACT_PATH as A12_V6_CONTRACT_PATH,
)
from ..armindex.a1_2_live_preflight_revision import (
    RECEIPT_PATH as A12_V6_RECEIPT_PATH,
)
from ..armindex.a1_2_live_preflight_revision import (
    REVISION_ID as A12_V6_REVISION_ID,
)
from ..armindex.a1_2_live_preflight_revision import (
    SCHEMA_PATH as A12_V6_SCHEMA_PATH,
)
from ..armindex.a1_2_live_preflight_revision import (
    validate_live_revision as validate_a1_2_v6_live_revision,
)
from ..armindex.a1_2_measured_result_summary_v16 import (
    MeasuredResultSummaryV16Error,
    validate_measured_result_summary_file,
)
from ..armindex.a1_2_provider_closeout_result_v10 import (
    RECEIPT_PATH as A12_V10_CLOSEOUT_RECEIPT_PATH,
)
from ..armindex.a1_2_provider_closeout_result_v10 import (
    REVISION_ID as A12_V10_CLOSEOUT_REVISION_ID,
)
from ..armindex.a1_2_provider_closeout_result_v10 import (
    SCHEMA_PATH as A12_V10_CLOSEOUT_SCHEMA_PATH,
)
from ..armindex.a1_2_provider_closeout_result_v10 import (
    validate_closeout as validate_a1_2_v10_provider_closeout,
)
from ..armindex.a1_2_publication_impact_v13 import (
    CONTRACT_PATH as A12_V13_PUBLICATION_CONTRACT_PATH,
)
from ..armindex.a1_2_publication_impact_v13 import (
    DOCUMENTATION_PATH as A12_V13_PUBLICATION_DOCUMENTATION_PATH,
)
from ..armindex.a1_2_publication_impact_v13 import (
    REVISION_ID as A12_V13_PUBLICATION_REVISION_ID,
)
from ..armindex.a1_2_publication_impact_v13 import (
    SCHEMA_PATH as A12_V13_PUBLICATION_SCHEMA_PATH,
)
from ..armindex.a1_2_publication_impact_v13 import (
    validate as validate_a1_2_v13_publication_impact,
)
from ..armindex.a1_2_runtime_minimal_direct_base import (
    CONTRACT_PATH as A12_V5_CONTRACT_PATH,
)
from ..armindex.a1_2_runtime_minimal_direct_base import (
    IMAGE_CONTRACT_PATH as A12_V5_IMAGE_CONTRACT_PATH,
)
from ..armindex.a1_2_runtime_minimal_direct_base import (
    OWNER_RUNBOOK_PATH as A12_V5_OWNER_RUNBOOK_PATH,
)
from ..armindex.a1_2_runtime_minimal_direct_base import (
    RECEIPT_PATH as A12_V5_RECEIPT_PATH,
)
from ..armindex.a1_2_runtime_minimal_direct_base import (
    RUNTIME_LOCK_PATH as A12_V5_RUNTIME_LOCK_PATH,
)
from ..armindex.a1_2_runtime_minimal_direct_base import (
    SCHEMA_PATH as A12_V5_SCHEMA_PATH,
)
from ..armindex.a1_2_runtime_minimal_direct_base import (
    TOPOLOGY_PATH as A12_V5_TOPOLOGY_PATH,
)
from ..armindex.a1_2_runtime_minimal_direct_base import (
    validate_direct_base_revision as validate_a1_2_v5_direct_base,
)
from ..armindex.a1_2_scientific_execution_adoption_inputs_v12_r3 import (
    CONTRACT_PATH as A12_V12_R3_CONTRACT_PATH,
)
from ..armindex.a1_2_scientific_execution_adoption_inputs_v12_r3 import (
    CONTRACT_SCHEMA_PATH as A12_V12_R3_CONTRACT_SCHEMA_PATH,
)
from ..armindex.a1_2_scientific_execution_adoption_inputs_v12_r3 import (
    REVISION_ID as A12_V12_R3_REVISION_ID,
)
from ..armindex.a1_2_scientific_execution_adoption_inputs_v12_r3 import (
    validate_contract as validate_a1_2_v12_r3_adoption_inputs,
)
from ..armindex.a1_2_scientific_execution_request_v11 import (
    BUDGET_PATH as A12_V11_BUDGET_PATH,
)
from ..armindex.a1_2_scientific_execution_request_v11 import (
    RECEIPT_PATH as A12_V11_RECEIPT_PATH,
)
from ..armindex.a1_2_scientific_execution_request_v11 import (
    RECEIPT_SCHEMA_PATH as A12_V11_RECEIPT_SCHEMA_PATH,
)
from ..armindex.a1_2_scientific_execution_request_v11 import (
    REQUEST_PATH as A12_V11_REQUEST_PATH,
)
from ..armindex.a1_2_scientific_execution_request_v11 import (
    REQUEST_SCHEMA_PATH as A12_V11_REQUEST_SCHEMA_PATH,
)
from ..armindex.a1_2_scientific_execution_request_v11 import (
    REVISION_ID as A12_V11_REVISION_ID,
)
from ..armindex.a1_2_scientific_execution_request_v11 import (
    validate as validate_a1_2_v11_scientific_request,
)
from ..armindex.a1_2_terminal_attempt_v16 import (
    CURRENT_POINTER_PATH as A12_CURRENT_ATTEMPT_POINTER_PATH,
)
from ..armindex.a1_2_terminal_attempt_v16 import (
    TerminalAttemptV16Error,
    validate_current_attempt_pointer,
)
from ..armindex.a1_2_vast import (
    CONTROL_ROOT as A12_V2_CONTROL_ROOT,
)
from ..armindex.a1_2_vast import (
    LEDGER_PATH as A12_V2_LEDGER_PATH,
)
from ..armindex.a1_2_vast import (
    RECEIPT_PATH as A12_V2_RECEIPT_PATH,
)
from ..armindex.a1_2_vast import (
    RUNBOOK_PATH as A12_V2_RUNBOOK_PATH,
)
from ..armindex.a1_2_vast import (
    SYNTHETIC_RECEIPT_PATH as A12_V2_SYNTHETIC_RECEIPT_PATH,
)
from ..armindex.a1_2_vast import (
    validate_preparation_receipt as validate_a1_2_vast_receipt,
)
from ..armindex.a1_2_vast_postcommit import (
    CONTRACT_PATH as A12_V3_CONTRACT_PATH,
)
from ..armindex.a1_2_vast_postcommit import (
    RECEIPT_PATH as A12_V3_RECEIPT_PATH,
)
from ..armindex.a1_2_vast_postcommit import (
    validate_postcommit_revision as validate_a1_2_vast_postcommit,
)
from ..armindex.a2_candidate_freeze import (
    A2CandidateFreezeError,
    validate_candidate_freeze,
)
from ..armindex.a2_execution_readiness import (
    A2ExecutionReadinessError,
    validate_execution_adoption_receipt,
    validate_execution_ledger,
    validate_provider_admission_receipt,
)
from ..armindex.adapter_fixture import validate_adapter_fixture_artifacts
from ..armindex.constants import (
    A0_8_NEXT_AUTHORIZED_ACTION,
    A0_9_NEXT_AUTHORIZED_ACTION,
    A1_1_NEXT_AUTHORIZED_ACTION,
    A1_2_NEXT_AUTHORIZED_ACTION,
    A1_2_SCAFFOLD_NEXT_AUTHORIZED_ACTION,
    A1_LONG_RUN_NEXT_AUTHORIZED_ACTION,
)
from ..armindex.contracts import parse_contract
from ..armindex.feasibility import validate_compute_storage_artifacts
from ..armindex.resource_proposal import load_and_validate_gpu_proposal
from ..dapfam_p1 import DapfamP1Error, load_package
from ..kernel.canonical import canonical_sha256
from ..kernel.manifest import manifest_round_trip
from ..kernel.manifest_validation import (
    ManifestValidationError,
    validate_validation_report,
)
from ..observatory.projection import load_observatory_projection
from ..owner_local import OwnerLocalContractError, validate_receipt
from ..p2 import (
    P2ContractError,
    P2FixtureError,
    validate_fixture_execution_manifest,
    validate_fixture_receipt,
    validate_p2_artifact,
    validate_p2_candidate_freeze_proposal,
    validate_p2_package_bundle,
    validate_p2_preflight_receipt,
)
from ..protection import assert_aggregate_only

READ_MODEL_SCHEMA = "myis.read-model.v2"
PROJECTION_SCHEMA_VERSION = "myis.integrated-projection.v2"
P1_ARMS = frozenset({"R0", "R0-W"})
P1_SPLITS = frozenset({"train", "selection"})
P1_SCOPES = frozenset({"ALL", "IN", "OUT"})
P1_ACCEPTED_METRIC_FIELDS = frozenset(
    {
        "arm",
        "name",
        "value",
        "n",
        "retrieved_relevant",
        "relevant_total",
        "scope",
        "split",
        "direction",
        "denominator",
        "evidence_role",
    }
)
LEGACY_DISPOSITION_RELATIVE_PATH = Path(
    "campaigns/scope-autoindex-v1/evidence/legacy-p1-receipt.v2.disposition.json"
)
LEGACY_DISPOSITION_KEYS = frozenset(
    {
        "schema_version",
        "disposition_id",
        "evidence_id",
        "source_uri",
        "source_file_sha256",
        "receipt_sha256",
        "status",
        "evidence_class",
        "promotable",
        "superseded_by",
        "reason_codes",
        "invalidation_evidence",
        "related_records",
        "record_sha256",
    }
)
PROJECTION_SOURCE_PATHS = (
    "control/program.yaml",
    "control/campaigns/scope-autoindex-v1.yaml",
    "control/execution-envelope.yaml",
    "control/execution-envelope-p2.yaml",
    "control/budgets/p2-r1-primary-v1.yaml",
    "control/execution-envelope-p2-v2.yaml",
    "control/budgets/p2-r1-primary-v2.yaml",
    "control/campaigns/scope-autoindex-p2-r1-primary-v2.yaml",
    "control/runbooks/P2_MEASURED_AUTORESEARCH_V2.md",
    "archive/p2-runtime-resilience-v1-interrupted",
    "orchestration/autoresearch/p2-runtime-resilience-v2",
    "control/source-of-truth.yaml",
    "control/decisions",
    "campaigns/scope-autoindex-v1/evidence",
    "campaigns/scope-autoindex-v1/requests",
    "campaigns/scope-autoindex-v1/manifests",
    "campaigns/scope-autoindex-v1/validation-reports",
    "campaigns/scope-autoindex-v1/packages",
    "campaigns/scope-autoindex-v1/proposals",
    "campaigns/scope-autoindex-v1/preflight",
    "orchestration/audits/p2-readiness",
    "outputs/fixtures/p2",
    "outputs/observatory/fixture-v1",
    "control/assets/dapfam-p1-source.v1.json",
    "outputs/audits/rigor",
    "outputs/audits/armindex",
    ":(exclude)outputs/audits/armindex/a2-five-arm-candidate-freeze-replay-validation.v1.json",
    "evidence/legacy-dapfam-inventory.v1.json",
    "schemas/read-model.v2.json",
    "schemas/p2-budget-profile.v1.json",
    "schemas/p2-request.v1.json",
    "schemas/p2-aggregate-metric.v1.json",
    "schemas/p2-train-metric.v1.json",
    "schemas/p2-candidate-ledger.v1.json",
    "schemas/p2-baseline-commitment.v1.json",
    "schemas/p2-baseline-reproduction-receipt.v1.json",
    "schemas/p2-shortlist-freeze-receipt.v1.json",
    "schemas/p2-selection-receipt.v1.json",
    "schemas/p2-manifest.v1.json",
    "schemas/p2-package.v1.json",
    "schemas/p2-preflight-receipt.v1.json",
    "schemas/p2-candidate-freeze-proposal.v1.json",
    "schemas/observatory-registry.v1.json",
    "schemas/observatory-run.v1.json",
    "schemas/observatory-artifact.v1.json",
    "schemas/observatory-prompt.v1.json",
    "schemas/observatory-metric.v1.json",
    "schemas/observatory-receipt.v1.json",
    "schemas/observatory-config.v1.json",
    "schemas/observatory-environment.v1.json",
    "schemas/observatory-failure.v1.json",
    "schemas/observatory-recovery.v1.json",
    "schemas/observatory-decision.v1.json",
    "schemas/phase-task-report.v1.json",
    "docs/observatory/REPORTING_POLICY.md",
    "docs/observatory/MEASURED_PREFLIGHT_INTEGRATION.md",
    "src/myis_research/p2",
    "src/myis_research/observatory",
    "src/myis_research/p2_cli.py",
    "src/myis_research/p2/preflight.py",
    "src/myis_research/projections/read_model.py",
    "src/myis_research/report_cli.py",
    "src/myis_research/report_records.py",
    "control/campaigns/armindex-multiretriever-v2.yaml",
    "control/budgets/armindex-migration-v2.yaml",
    "control/budgets/a1.2-common-screen-v1.json",
    "control/budgets/a1.2-common-screen-vast-4x3090-v2.json",
    "control/execution-envelope-a1.2-v1.yaml",
    "control/execution-envelope-a1.2-v2.yaml",
    "control/plans/ARMINDEX_AUTOINDEX_HARNESSOPT_CONTRACT.md",
    "schemas/armindex",
    "src/myis_research/armindex",
    "docs/research/ARMINDEX_RESEARCH_PLAN_V02.md",
    "control/armindex",
    "campaigns/armindex-multiretriever-v2/evidence",
    "campaigns/armindex-multiretriever-v2/proposals",
    "control/runbooks/A1_2_COMMON_MULTI_ARM_SCREENING.md",
    "control/runbooks/A1_2_VAST_4X3090_PREFLIGHT_V2.md",
    "control/runbooks/A1_2_VAST_4X3090_POSTCOMMIT_PREFLIGHT_V3.md",
    "docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V3.md",
    "docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V5.md",
)

P2_ARTIFACT_DIRS = ("requests", "manifests", "evidence", "packages", "reports")
P2_OFFICIAL_REVIEW_ROOT = Path("orchestration/audits/p2-readiness")
P2_FIXTURE_RECEIPT_PATH = Path("outputs/fixtures/p2/p2-fixture-pilot-v1.receipt.json")
P2_FIXTURE_MANIFEST_PATH = Path(
    "outputs/fixtures/p2/p2-fixture-pilot-v1.execution-manifest.json"
)
P2_PREFLIGHT_RECEIPT_PATH = Path(
    "campaigns/scope-autoindex-v1/preflight/p2-preflight-receipt.json"
)
P2_CANDIDATE_PROPOSAL_PATH = Path(
    "campaigns/scope-autoindex-v1/proposals/p2-candidate-freeze-proposal.v1.json"
)
P2_METRIC_FIELDS = frozenset(
    {
        "candidate_id",
        "arm",
        "name",
        "value",
        "n",
        "retrieved_relevant",
        "relevant_total",
        "scope",
        "split",
        "direction",
        "denominator",
        "evidence_role",
    }
)
A010_LEGACY_CODE_HARVEST_LEDGER_PATH = Path(
    "control/armindex/a0.10-legacy-code-harvest-ledger.v1.json"
)
A010_LEGACY_CODE_HARVEST_RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a0.10-legacy-code-harvest.receipt.v1.json"
)
A010_REPOSITORY_HYGIENE_AUDIT_PATH = Path(
    "outputs/audits/repository/repository-hygiene-a0.10-20260804.json"
)
A010_OUTPUT_ROOT_RELOCATION_RECEIPT_PATH = Path(
    "outputs/audits/dashboard/output-root-relocation-20260804.json"
)
A010_SOURCE_VERIFICATION_RECEIPT_PATH = Path(
    "outputs/audits/repository/thaipha-lex-source-verification-a0.10-20260804.json"
)
A12_CLOSEOUT_VALIDATION_AUDIT_PATH = Path(
    "outputs/audits/rigor/a1.2-contract-scaffold-closeout-validation-20260805.json"
)
A12_PREFLIGHT_PATH = Path(
    "outputs/audits/armindex/a1.2-owner-local-preflight-20260806.json"
)
A12_V2_BUDGET_PATH = Path("control/budgets/a1.2-common-screen-vast-4x3090-v2.json")
A12_V2_OWNER_RUNBOOK_PATH = Path("docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK.md")
A12_V2_COORDINATOR_PATH = Path("scripts/a1_2_vast/Invoke-A12VastCoordinator.ps1")
A12_V2_WATCHDOG_PATH = Path("scripts/a1_2_vast/Invoke-A12VastWatchdog.ps1")
A12_V2_ALLOWLIST_PATH = A12_V2_CONTROL_ROOT / "safe-export-allowlist.v2.json"
A12_V2_CLOSEOUT_AUDIT_PATH = Path(
    "outputs/audits/rigor/a1.2-vast-4x3090-preflight-closeout-validation-20260806.json"
)
A12_V3_CONTROL_RUNBOOK_PATH = Path(
    "control/runbooks/A1_2_VAST_4X3090_POSTCOMMIT_PREFLIGHT_V3.md"
)
A12_V3_OWNER_RUNBOOK_PATH = Path("docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V3.md")
A12_V3_SCHEMA_PATH = Path("schemas/armindex/a1.2-vast-4x3090-postcommit.v3.json")
A12_V3_MODULE_PATH = Path("src/myis_research/armindex/a1_2_vast_postcommit.py")
A12_V5_MODULE_PATH = Path(
    "src/myis_research/armindex/a1_2_runtime_minimal_direct_base.py"
)
A12_V6_MODULE_PATH = Path("src/myis_research/armindex/a1_2_live_preflight_revision.py")
A12_V6_PREFLIGHT_MODULE_PATH = Path("src/myis_research/armindex/a1_2_live_preflight.py")
A12_V6_OWNER_RUNBOOK_PATH = Path("docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V6.md")
A12_V6_CONTINUATION_POLICY_PATH = Path(
    "control/armindex/a1.2/owner-instance-continuation-policy.v1.json"
)
A12_V7_MODULE_PATH = Path("src/myis_research/armindex/a1_2_live_preflight_repair_v7.py")
A12_V7_OWNER_RUNBOOK_PATH = Path("docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V7.md")
A12_V7_COORDINATOR_PATH = Path(
    "scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinatorV7.ps1"
)
A12_V7_BOOTSTRAP_PATH = Path("scripts/a1_2_vast/remote-bootstrap-direct-base-v7.sh")
A12_V7_SUPPLEMENT_VALIDATOR_PATH = Path(
    "scripts/a1_2_vast/validate_preflight_supplement_v7.py"
)
A12_V7_SUPPLEMENT_REQUIREMENTS_PATH = Path(
    "containers/a1_2_vast_4x3090/runtime/requirements.preflight-supplement.v7.txt"
)
A12_V7_SUPPLEMENT_WORKFLOW_PATH = Path(
    ".github/workflows/a1-2-preflight-supplement-wheelhouse-v7.yml"
)
A12_V8_MODULE_PATH = Path(
    "src/myis_research/armindex/a1_2_live_preflight_packaging_v8.py"
)
A12_V8_OWNER_RUNBOOK_PATH = Path("docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V8.md")
A12_V8_COORDINATOR_PATH = Path(
    "scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinatorV8.ps1"
)
A12_V8_BOOTSTRAP_PATH = Path("scripts/a1_2_vast/remote-bootstrap-direct-base-v8.sh")
A12_V9_MODULE_PATH = Path(
    "src/myis_research/armindex/a1_2_live_preflight_execution_v9.py"
)
A12_V9_RUNTIME_PATH = Path(
    "src/myis_research/armindex/a1_2_live_preflight_runtime_v9.py"
)
A12_V9_OWNER_RUNBOOK_PATH = Path("docs/operations/A1_2_VAST_4X3090_OWNER_RUNBOOK_V9.md")
A12_V9_COORDINATOR_PATH = Path(
    "scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinatorV9.ps1"
)
A12_V9_BOOTSTRAP_PATH = Path("scripts/a1_2_vast/remote-bootstrap-direct-base-v9.sh")
A12_V9_LAUNCHER_PATH = Path("scripts/a1_2_vast/remote-live-preflight-v9.sh")
A12_V9_RESULT_MODULE_PATH = Path(
    "src/myis_research/armindex/a1_2_live_preflight_result_v9.py"
)
A12_V10_CLOSEOUT_MODULE_PATH = Path(
    "src/myis_research/armindex/a1_2_provider_closeout_result_v10.py"
)
A12_V11_MODULE_PATH = Path(
    "src/myis_research/armindex/a1_2_scientific_execution_request_v11.py"
)
A12_V11_RUNBOOK_PATH = Path(
    "docs/operations/A1_2_SCIENTIFIC_EXECUTION_ADOPTION_REQUEST_V11.md"
)
A12_V11_LEDGER_PATH = Path(
    "control/armindex/a1.2/scientific-execution-adoption-request-ledger.v11.jsonl"
)
A12_V11_RIGOR_REVIEW_PATH = Path(
    "outputs/audits/rigor/a1.2-scientific-execution-adoption-request-v11-20260807.json"
)
A12_REP_HARNESS_CLAIM_AUDIT_PATH = Path(
    "outputs/audits/armindex/a1.2-rep-harness-claim-audit-20260808.json"
)
A12_REP_HARNESS_SPLIT_FIGURE_PNG_PATH = Path(
    "outputs/figures/armindex/a1.2-rep-harness-split-eda-v1.png"
)
A12_REP_HARNESS_SPLIT_FIGURE_SVG_PATH = Path(
    "outputs/figures/armindex/a1.2-rep-harness-split-eda-v1.svg"
)
A12_P02_FIRST_CLAIM_AUDIT_PATH = Path(
    "outputs/audits/armindex/a1.2-p02-first-claim-repair-20260808.json"
)
A12_EFFECTIVE_INPUT_LIMIT_AUDIT_PATH = Path(
    "outputs/audits/armindex/a1.2-effective-input-limit-blocker-20260808.json"
)
A12_DENSE_OVERFLOW_CONTRACT_PATH = Path(
    "control/armindex/a1.2/dense-overflow-adapter-repair.v14.json"
)
A12_DENSE_OVERFLOW_INVENTORY_PATH = Path(
    "outputs/audits/armindex/a1.2-dense-overflow-inventory-20260808.json"
)
A12_DENSE_OVERFLOW_COMPOSITION_PATH = Path(
    "outputs/audits/armindex/a1.2-dense-overflow-composition-20260808.json"
)
A12_DENSE_OVERFLOW_FIGURE_PNG_PATH = Path(
    "outputs/figures/armindex/a1.2-dense-overflow-eda-v1.png"
)
A12_DENSE_OVERFLOW_FIGURE_SVG_PATH = Path(
    "outputs/figures/armindex/a1.2-dense-overflow-eda-v1.svg"
)
A12_PROTECTED_COMPILER_INTEGRATION_CONTRACT_PATH = Path(
    "control/armindex/a1.2/protected-compiler-integration.v15.json"
)
A12_PROTECTED_COMPILER_INTEGRATION_AUDIT_PATH = Path(
    "outputs/audits/armindex/a1.2-protected-compiler-integration-20260809-v15.json"
)
A12_WHOLE_WORKLOAD_BUDGET_MODEL_V15_PATH = Path(
    "control/armindex/a1.2/whole-workload-budget-model.v15.json"
)
A12_LOCAL_ADOPTION_INPUTS_RECEIPT_V15_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-scientific-execution-adoption-inputs.receipt.v15.json"
)
A12_V16_EXACT_TOKEN_ID_ADAPTER_PROBE_PATH = Path(
    "outputs/audits/rigor/a1.2-v16-exact-token-id-adapter-probe-20260809.json"
)
A12_V16_R13_FAILURE_AUDIT_PATH = Path(
    "outputs/audits/armindex/a1.2-v16-r13-failure-audit-20260810.json"
)
A12_R15_REMOTE_RETENTION_AUDIT_PATH = Path(
    "outputs/audits/armindex/a1.2-r15-remote-retention-20260812.json"
)
A2_CANDIDATE_MANIFEST_PATH = Path(
    "campaigns/armindex-multiretriever-v2/manifests/"
    "a2-five-arm-candidate-manifest.v1.json"
)
A2_CANDIDATE_FREEZE_RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a2-five-arm-candidate-freeze.receipt.v1.json"
)
A2_CANDIDATE_FREEZE_LOCK_PATH = Path(
    "control/armindex/a2/candidate-freeze.lock.v1.json"
)
A2_OFFICIAL_SMOKE_RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a2-official-codex-bridge-smoke.receipt.v2.json"
)
A2_OFFICIAL_CREDIT_PREFLIGHT_RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a2-official-codex-credit-preflight.receipt.v1.json"
)
A2_OFFICIAL_CREDIT_CORRECTION_RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a2-official-credit-closeout-correction.receipt.v1.json"
)
A2_INDEPENDENT_AUDIT_RECEIPT_PATH = Path(
    "outputs/audits/rigor/"
    "a2-official-codex-candidate-freeze-independent-audit-20260812.json"
)
A2_FINAL_CREDIT_RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a2-official-codex-final-credit-check.receipt.v1.json"
)
A2_OFFICIAL_BRIDGE_CONTROL_PATH = Path(
    "control/armindex/a2/official-codex-bridge.v1.json"
)
A2_EXECUTION_CONTRACT_PATH = Path("control/armindex/a2/execution-contract.v1.json")
A2_EXECUTION_ENVELOPE_PATH = Path("control/execution-envelope-a2-v1.yaml")
A2_BUDGET_PROFILE_PATH = Path("control/budgets/a2-per-arm-autoindex-v1.json")
A2_READINESS_CONTRACT_PATH = Path(
    "control/armindex/a2/execution-readiness-contract.v2.json"
)
A2_READINESS_ENVELOPE_PATH = Path(
    "control/execution-envelope-a2-readiness-v2.yaml"
)
A2_READINESS_BUDGET_PATH = Path("control/budgets/a2-execution-readiness-v1.json")
A2_READINESS_RUNBOOK_PATH = Path(
    "control/runbooks/A2_PER_ARM_AUTOINDEX_EXECUTION_V1.md"
)
A2_READINESS_LEDGER_PATH = Path("control/armindex/a2/execution-ledger.v1.jsonl")
A2_CURRENT_EXECUTION_POINTER_PATH = Path(
    "control/armindex/a2/current-execution-attempt.v1.json"
)
A2_FREEZE_NEXT_AUTHORIZED_ACTION = (
    "RUN_INDEPENDENT_A2_FREEZE_AUDIT_STOP_BEFORE_MEASURED_A2"
)
A2_AUDIT_PASS_NEXT_AUTHORIZED_ACTION = (
    "OWNER_LAUNCH_DOCS_GOAL_A2_WITH_FRESH_PREFLIGHT"
)
A08_RUNBOOK_PATH = Path("control/runbooks/A0_8_COMPUTE_STORAGE_FEASIBILITY_FIXTURES.md")
A08_LEDGER_PATH = Path(
    "control/armindex/a0.8-compute-storage-feasibility-ledger.v1.jsonl"
)
A08_FIXTURE_MANIFEST_PATH = Path(
    "outputs/fixtures/armindex/a0.8/compute-storage-v1/manifest.json"
)
A08_FIXTURE_RECEIPT_PATH = Path(
    "outputs/fixtures/armindex/a0.8/compute-storage-v1/receipt.json"
)
A08_TASK_RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a0.8-compute-storage-feasibility.receipt.v1.json"
)
A09_RUNBOOK_PATH = Path("control/runbooks/A0_9_VALIDATION_SAFETY_CLOSEOUT.md")
A09_LEDGER_PATH = Path(
    "control/armindex/a0.9-validation-safety-closeout-ledger.v1.jsonl"
)
A09_VALIDATION_AUDIT_PATH = Path(
    "outputs/audits/armindex/a0.9-validation-safety-closeout-20260805.json"
)
A09_PHASE_CLOSEOUT_RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/a0-phase-closeout.receipt.v1.json"
)
A11_RUNBOOK_PATH = Path("control/runbooks/A1_1_ADAPTER_FIXTURE_VALIDATION.md")
A11_LEDGER_PATH = Path(
    "control/armindex/a1.1-adapter-fixture-validation-ledger.v1.jsonl"
)
A11_FIXTURE_MANIFEST_PATH = Path(
    "outputs/fixtures/armindex/a1.1/adapter-cpu-v1/manifest.json"
)
A11_FIXTURE_RECEIPT_PATH = Path(
    "outputs/fixtures/armindex/a1.1/adapter-cpu-v1/receipt.json"
)
A11_GPU_PROPOSAL_PATH = Path(
    "campaigns/armindex-multiretriever-v2/proposals/a1.2-gpu-execution-plan.v1.json"
)
A11_TASK_RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.1-adapter-fixture-validation.receipt.v1.json"
)


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _validate_json_receipt(
    root: Path,
    *,
    relative_path: Path,
    schema_path: Path,
    self_hash_field: str = "receipt_sha256",
) -> dict[str, Any]:
    path = root / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads((root / schema_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(schema, dict):
        raise ValueError(f"invalid JSON object: {relative_path.as_posix()}")
    errors = sorted(
        Draft202012Validator(schema).iter_errors(payload),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if errors:
        raise ValueError(
            f"schema validation failed for {relative_path.as_posix()}: "
            f"{errors[0].message}"
        )
    expected = canonical_sha256(
        {key: value for key, value in payload.items() if key != self_hash_field}
    )
    if payload.get(self_hash_field) != expected:
        raise ValueError(f"self-hash mismatch: {relative_path.as_posix()}")
    assert_aggregate_only(payload)
    return payload


def _a2_candidate_freeze_missing(root: Path) -> dict[str, Any]:
    missing = {
        "status": "not_started",
        "validated": False,
        "phase_id": "A2_PER_ARM_AUTOINDEX",
        "task_id": "OFFICIAL_CODEX_BRIDGE_AND_CANDIDATE_FREEZE",
        "evidence_class": "engineering_validation",
        "scientific_authority": False,
        "claim_boundary": (
            "premeasurement_candidate_freeze_only_no_candidate_evaluation_"
            "or_retrieval_quality_claim"
        ),
        "manifest_uri": A2_CANDIDATE_MANIFEST_PATH.as_posix(),
        "freeze_receipt_uri": A2_CANDIDATE_FREEZE_RECEIPT_PATH.as_posix(),
        "lock_uri": A2_CANDIDATE_FREEZE_LOCK_PATH.as_posix(),
        "smoke_receipt_uri": A2_OFFICIAL_SMOKE_RECEIPT_PATH.as_posix(),
        "credit_preflight_receipt_uri": (
            A2_OFFICIAL_CREDIT_PREFLIGHT_RECEIPT_PATH.as_posix()
        ),
        "credit_correction_receipt_uri": (
            A2_OFFICIAL_CREDIT_CORRECTION_RECEIPT_PATH.as_posix()
        ),
        "independent_audit_receipt_uri": A2_INDEPENDENT_AUDIT_RECEIPT_PATH.as_posix(),
        "final_credit_receipt_uri": A2_FINAL_CREDIT_RECEIPT_PATH.as_posix(),
        "next_authorized_action": A2_FREEZE_NEXT_AUTHORIZED_ACTION,
    }
    return missing


def _a2_execution_readiness_projection(
    root: Path, freeze: Mapping[str, Any]
) -> dict[str, Any]:
    missing = {
        "status": "not_started",
        "validated": False,
        "phase_id": "A2_PER_ARM_AUTOINDEX",
        "task_id": "A2.1",
        "evidence_class": "engineering_execution_readiness",
        "scientific_authority": False,
        "claim_boundary": (
            "frozen_52_candidate_execution_readiness_only_no_candidate_"
            "evaluation_or_measured_a2_claim"
        ),
        "contract_uri": A2_READINESS_CONTRACT_PATH.as_posix(),
        "envelope_uri": A2_READINESS_ENVELOPE_PATH.as_posix(),
        "budget_uri": A2_READINESS_BUDGET_PATH.as_posix(),
        "runbook_uri": A2_READINESS_RUNBOOK_PATH.as_posix(),
        "ledger_uri": A2_READINESS_LEDGER_PATH.as_posix(),
        "current_execution_pointer_uri": (
            A2_CURRENT_EXECUTION_POINTER_PATH.as_posix()
        ),
        "provider_admission_performed": False,
        "provider_execution_adoption_performed": False,
        "remote_staging_performed": False,
        "measured_a2_started": False,
        "current_status": "NOT_STARTED",
        "current_route": "AP",
        "gpu_decision": "UNKNOWN",
        "gpu_decision_reason": "canonical provider admission evidence is not present",
        "next_authorized_action": (
            "BUILD_CLEAN_A2_BUNDLE_THEN_FRESH_PROVIDER_ADMISSION_AND_STAGING"
        ),
    }
    paths = (
        A2_READINESS_CONTRACT_PATH,
        A2_READINESS_ENVELOPE_PATH,
        A2_READINESS_BUDGET_PATH,
        A2_READINESS_RUNBOOK_PATH,
        A2_READINESS_LEDGER_PATH,
    )
    if not any((root / path).exists() for path in paths):
        return missing
    if not all((root / path).is_file() for path in paths):
        return {**missing, "status": "INVALID"}
    try:
        contract = json.loads(
            (root / A2_READINESS_CONTRACT_PATH).read_text(encoding="utf-8")
        )
        budget = json.loads(
            (root / A2_READINESS_BUDGET_PATH).read_text(encoding="utf-8")
        )
        envelope = _load_yaml_like(root / A2_READINESS_ENVELOPE_PATH)
        if not all(isinstance(item, Mapping) for item in (contract, budget, envelope)):
            raise ValueError("A2 readiness controls must be objects")
        if budget.get("budget_profile_sha256") != canonical_sha256(
            {
                key: value
                for key, value in budget.items()
                if key != "budget_profile_sha256"
            }
        ):
            raise ValueError("A2 readiness budget self-hash mismatch")
        freeze_bindings = contract.get("freeze_bindings", {})
        if (
            not isinstance(freeze_bindings, Mapping)
            or freeze_bindings.get("manifest_sha256") != freeze.get("manifest_sha256")
            or freeze_bindings.get("freeze_receipt_sha256")
            != freeze.get("freeze_receipt_sha256")
            or freeze_bindings.get("lock_sha256") != freeze.get("lock_sha256")
        ):
            raise ValueError("A2 readiness freeze binding mismatch")
        design = contract.get("candidate_design", {})
        policy = contract.get("execution_policy", {})
        if (
            contract.get("schema_version")
            != "myis.armindex-a2-execution-readiness-contract.v2"
            or contract.get("contract_id") != "a2-five-arm-execution-readiness-v2"
            or contract.get("revision_id") != "a2-fresh-instance-rebind-v2"
            or contract.get("status")
            != "READY_FOR_AP_FRESH_INSTANCE_STAGING_MEASUREMENT_LOCKED"
            or not isinstance(design, Mapping)
            or design.get("candidate_count") != 52
            or design.get("matched_candidate_count") != 40
            or design.get("conditional_reserve_candidate_count") != 12
            or design.get("diagnostic_non_advancing_arms") != ["ARM-01", "ARM-02"]
            or design.get("primary_advancement_arms") != ["ARM-03", "ARM-05", "ARM-04"]
            or contract.get("candidate_evaluation_allowed") is not False
            or contract.get("launch_allowed") is not False
            or contract.get("measured_execution_allowed") is not False
            or not isinstance(policy, Mapping)
            or policy.get("forward_hard_stop_usd") != 35
            or policy.get("owner_ttl_hours") != 40
            or policy.get("provider_instance_id")
            != "runtime_supplied_from_fresh_binding"
            or policy.get("provider_instance_binding_required") is not True
            or policy.get("gpu_count") != 4
            or policy.get("gpu_model") != "RTX3090"
            or policy.get("vram_mib_each") != 24576
            or policy.get("target_ttl_hours") != 48
            or policy.get("remote_clock_skew_max_seconds") != 60
        ):
            raise ValueError("A2 readiness contract boundary drift")
        admission = budget.get("admission", {})
        preparation = budget.get("preparation_counters", {})
        scope = envelope.get("scope", {})
        authority = envelope.get("authority", {})
        if (
            budget.get("status") != "READY_FOR_FRESH_ALL_FEE_ADMISSION"
            or not isinstance(admission, Mapping)
            or admission.get("forward_hard_stop_usd") != 35
            or admission.get("whole_workload_admission_required") is not True
            or admission.get("fresh_all_fee_quote_required") is not True
            or admission.get("adopted_for_execution") is not False
            or admission.get("launch_allowed") is not False
            or not isinstance(preparation, Mapping)
            or any(value != 0 for value in preparation.values())
            or envelope.get("schema_version")
            != "myis.execution-envelope-a2-readiness.v2"
            or envelope.get("status")
            != "ready_for_ap_fresh_instance_staging_measurement_locked"
            or not isinstance(scope, Mapping)
            or scope.get("frozen_candidate_count") != 52
            or scope.get("diagnostic_non_advancing_arms") != ["ARM-01", "ARM-02"]
            or not isinstance(authority, Mapping)
            or authority.get("measured_a2_authorized") is not False
        ):
            raise ValueError("A2 readiness envelope or budget boundary drift")

        ledger = validate_execution_ledger(root, root / A2_READINESS_LEDGER_PATH)
        latest_ledger_entry = ledger[-1]
        result = {
            **missing,
            "status": "READY_FOR_FRESH_ADMISSION_AND_STAGING_MEASUREMENT_LOCKED",
            "validated": True,
            "contract_sha256": canonical_sha256(contract),
            "contract_file_sha256": _file_sha256(root / A2_READINESS_CONTRACT_PATH),
            "envelope_file_sha256": _file_sha256(root / A2_READINESS_ENVELOPE_PATH),
            "budget_profile_sha256": str(budget["budget_profile_sha256"]),
            "budget_file_sha256": _file_sha256(root / A2_READINESS_BUDGET_PATH),
            "runbook_sha256": _file_sha256(root / A2_READINESS_RUNBOOK_PATH),
            "ledger_sha256": _file_sha256(root / A2_READINESS_LEDGER_PATH),
            "candidate_count": 52,
            "matched_candidate_count": 40,
            "conditional_reserve_candidate_count": 12,
            "diagnostic_non_advancing_arms": ["ARM-01", "ARM-02"],
            "primary_advancement_arms": ["ARM-03", "ARM-05", "ARM-04"],
            "forward_hard_stop_usd": 35,
            "owner_ttl_hours": 40,
            "phase_ceiling_usd": budget["hard_stops"]["a2_forward_usd"],
            "task_run_ceiling_usd": admission["forward_hard_stop_usd"],
            "a2_spent_accrued_usd": preparation["charged_usd"],
            "campaign_ceiling_usd": budget["hard_stops"]["campaign_usd"],
            "recorded_campaign_spend_usd": budget["hard_stops"][
                "recorded_a1_charge_usd"
            ],
            "remaining_campaign_headroom_usd": budget["hard_stops"][
                "remaining_campaign_ceiling_usd"
            ],
            "estimated_next_action_cost_usd": "UNKNOWN",
            "next_phase_ceiling_usd": None,
            "budget_status": "UNKNOWN_DO_NOT_SPEND",
            "candidate_evaluation_allowed": False,
            "measured_execution_allowed": False,
            "freeze_bindings": dict(freeze_bindings),
            "counters": {
                "candidate_evaluations": 0,
                "measured_a2_runs": 0,
                "provider_admissions": 0,
                "provider_execution_adoptions": 0,
            },
            "latest_ledger_entry_id": latest_ledger_entry["entry_id"],
            "latest_ledger_entry_sha256": latest_ledger_entry["entry_sha256"],
            "provider_admission_status": "NOT_ATTEMPTED",
            "provider_admission_attempted": False,
        }
        if latest_ledger_entry["status"] == "IMPLEMENTATION_BLOCKED":
            return {
                **result,
                "status": "IMPLEMENTATION_BLOCKED_MEASUREMENT_LOCKED",
                "provider_admission_status": "DEFERRED_PENDING_IMPLEMENTATION",
                "provider_admission_attempted": True,
                "next_authorized_action": (
                    "IMPLEMENT_PRODUCTION_A2_ADAPTER_AND_MATCHED_FIRST_"
                    "CONDITIONAL_RESERVE_LIFECYCLE"
                ),
            }
        if (
            latest_ledger_entry["status"]
            == "READY_FOR_AP_FRESH_INSTANCE_STAGING_MEASUREMENT_LOCKED"
        ):
            return {
                **result,
                "status": "READY_FOR_AP_FRESH_INSTANCE_STAGING_MEASUREMENT_LOCKED",
                "historical_status": "NEEDS_IM_NEW_INSTANCE_REBIND_MEASUREMENT_LOCKED",
                "current_status": "READY_FOR_AP_FRESH_INSTANCE_STAGING_MEASUREMENT_LOCKED",
                "current_route": "AP",
                "a1_provider_disposition_status": "REUSE_ELIGIBLE",
                "a2_provider_disposition_status": "FRESH_INSTANCE_REQUIRED",
                "reuse_existing_instance_permitted": False,
                "provider_admission_status": "NOT_ATTEMPTED_NEW_INSTANCE_REQUIRED",
                "provider_admission_attempted": False,
                "next_authorized_action": (
                    "AP_VALIDATE_OWNER_LOCAL_PUSHED_HEAD_BUNDLE_AND_DEPLOYMENT_"
                    "RECEIPT_THEN_FRESH_INSTANCE_ADMISSION_AND_ISOLATED_STAGING"
                ),
            }
        if latest_ledger_entry["status"] == "FAILED_CLOSED":
            return {
                **result,
                "status": "PROVIDER_ADMISSION_FAILED_CLOSED_MEASUREMENT_LOCKED",
                "provider_admission_status": "FAILED_CLOSED",
                "provider_admission_attempted": True,
                "next_authorized_action": (
                    "OBTAIN_FRESH_COMPLETE_PROVIDER_QUOTE_TTL_AND_MANAGEMENT_"
                    "AUTHORITY_THEN_RERUN_ADMISSION_ONLY"
                ),
            }
        pointer_path = root / A2_CURRENT_EXECUTION_POINTER_PATH
        if not pointer_path.exists():
            return result
        pointer = _validate_json_receipt(
            root,
            relative_path=A2_CURRENT_EXECUTION_POINTER_PATH,
            schema_path=Path("schemas/armindex/a2-current-execution-attempt.v1.json"),
            self_hash_field="pointer_sha256",
        )
        receipts: dict[str, dict[str, Any]] = {}
        for label, uri_key, hash_key, schema_name in (
            (
                "bundle",
                "bundle_receipt_uri",
                "bundle_receipt_file_sha256",
                "a2-execution-bundle-receipt.v1.json",
            ),
            (
                "provider_admission",
                "provider_admission_receipt_uri",
                "provider_admission_receipt_file_sha256",
                "a2-provider-admission-receipt.v1.json",
            ),
            (
                "execution_adoption",
                "execution_adoption_receipt_uri",
                "execution_adoption_receipt_file_sha256",
                "a2-execution-adoption-receipt.v1.json",
            ),
        ):
            relative = Path(str(pointer[uri_key]))
            receipt = _validate_json_receipt(
                root,
                relative_path=relative,
                schema_path=Path("schemas/armindex") / schema_name,
            )
            if _file_sha256(root / relative) != pointer[hash_key]:
                raise ValueError(f"A2 {label} receipt file hash mismatch")
            receipts[label] = receipt
        provider = validate_provider_admission_receipt(
            root, receipts["provider_admission"]
        )
        adoption = validate_execution_adoption_receipt(
            root, receipts["execution_adoption"]
        )
        bundle = receipts["bundle"]
        attempt_id = pointer["attempt_id"]
        if (
            any(receipt.get("attempt_id") != attempt_id for receipt in receipts.values())
            or adoption.get("provider_admission_receipt_sha256")
            != provider.get("receipt_sha256")
            or adoption.get("bundle_receipt_sha256") != bundle.get("receipt_sha256")
            or adoption.get("bundle_sha256") != bundle.get("bundle_sha256")
            or adoption.get("measured_retrieval_allowed") is not False
            or pointer.get("measured_a2_started") is not False
        ):
            raise ValueError("A2 staged receipt chain is inconsistent")
        return {
            **result,
            "status": "STAGED_NOT_LAUNCHED_MEASURED_A2_LOCKED",
            "historical_status": "STAGED_NOT_LAUNCHED_MEASURED_A2_LOCKED",
            "current_status": "READY_FOR_AP_MEASUREMENT_AUTHORIZATION_LOCKED",
            "current_route": "AP",
            "attempt_id": attempt_id,
            "current_execution_pointer_sha256": pointer["pointer_sha256"],
            "current_execution_pointer_file_sha256": _file_sha256(pointer_path),
            "bundle_receipt": {
                "uri": pointer["bundle_receipt_uri"],
                "file_sha256": pointer["bundle_receipt_file_sha256"],
                "receipt_sha256": bundle["receipt_sha256"],
                "bundle_sha256": bundle["bundle_sha256"],
                "git_commit": bundle["git_commit"],
                "git_tree": bundle["git_tree"],
            },
            "provider_admission_receipt": {
                "uri": pointer["provider_admission_receipt_uri"],
                "file_sha256": pointer["provider_admission_receipt_file_sha256"],
                "receipt_sha256": provider["receipt_sha256"],
                "instance_id": provider["provider_instance_id"],
                "whole_workload_total_usd": provider["whole_workload_total_usd"],
            },
            "execution_adoption_receipt": {
                "uri": pointer["execution_adoption_receipt_uri"],
                "file_sha256": pointer["execution_adoption_receipt_file_sha256"],
                "receipt_sha256": adoption["receipt_sha256"],
                "remote_root": adoption["remote_root"],
                "watchdog_deadline_utc": adoption["watchdog_deadline_utc"],
            },
            "provider_admission_performed": True,
            "provider_execution_adoption_performed": True,
            "remote_staging_performed": True,
            "gpu_decision": "UNKNOWN",
            "gpu_decision_reason": (
                "provider staging is recorded, but no measured execution or "
                "post-staging keep/destroy authority is present"
            ),
            "next_authorized_action": (
                "OWNER_AUTHORIZATION_FOR_SEPARATE_MEASURED_A2_SESSION"
            ),
        }
    except (
        A2ExecutionReadinessError,
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ):
        return {**missing, "status": "INVALID"}


def _a2_candidate_freeze_projection(root: Path) -> dict[str, Any]:
    missing = _a2_candidate_freeze_missing(root)
    required = (
        A2_CANDIDATE_MANIFEST_PATH,
        A2_CANDIDATE_FREEZE_RECEIPT_PATH,
        A2_CANDIDATE_FREEZE_LOCK_PATH,
        A2_OFFICIAL_SMOKE_RECEIPT_PATH,
        A2_OFFICIAL_CREDIT_PREFLIGHT_RECEIPT_PATH,
        A2_OFFICIAL_CREDIT_CORRECTION_RECEIPT_PATH,
    )
    if not any((root / path).exists() for path in required):
        return missing
    if not all((root / path).is_file() for path in required):
        return {**missing, "status": "INVALID"}
    try:
        replay = validate_candidate_freeze(root)
        receipt = json.loads(
            (root / A2_CANDIDATE_FREEZE_RECEIPT_PATH).read_text(encoding="ascii")
        )
        smoke = _validate_json_receipt(
            root,
            relative_path=A2_OFFICIAL_SMOKE_RECEIPT_PATH,
            schema_path=Path(
                "schemas/armindex/a2-official-codex-bridge-smoke-receipt.v2.json"
            ),
        )
        credit_preflight = _validate_json_receipt(
            root,
            relative_path=A2_OFFICIAL_CREDIT_PREFLIGHT_RECEIPT_PATH,
            schema_path=Path(
                "schemas/armindex/"
                "a2-official-codex-credit-preflight-receipt.v1.json"
            ),
        )
        correction = _validate_json_receipt(
            root,
            relative_path=A2_OFFICIAL_CREDIT_CORRECTION_RECEIPT_PATH,
            schema_path=Path(
                "schemas/armindex/"
                "a2-official-credit-closeout-correction-receipt.v1.json"
            ),
        )
        closeout_paths = (
            A2_INDEPENDENT_AUDIT_RECEIPT_PATH,
            A2_FINAL_CREDIT_RECEIPT_PATH,
        )
        if any((root / path).exists() for path in closeout_paths) and not all(
            (root / path).is_file() for path in closeout_paths
        ):
            raise ValueError("A2 audit closeout receipt set is incomplete")
        audit = None
        final_credit = None
        if all((root / path).is_file() for path in closeout_paths):
            audit = _validate_json_receipt(
                root,
                relative_path=A2_INDEPENDENT_AUDIT_RECEIPT_PATH,
                schema_path=Path(
                    "schemas/armindex/a2-independent-freeze-audit-receipt.v1.json"
                ),
                self_hash_field="audit_sha256",
            )
            final_credit = _validate_json_receipt(
                root,
                relative_path=A2_FINAL_CREDIT_RECEIPT_PATH,
                schema_path=Path(
                    "schemas/armindex/"
                    "a2-official-codex-final-credit-check-receipt.v1.json"
                ),
            )
        if (
            correction.get("manifest_sha256") != replay["manifest_sha256"]
            or correction.get("freeze_receipt_sha256") != replay["receipt_sha256"]
            or correction.get("lock_sha256") != replay["lock_sha256"]
            or correction.get("freeze_artifacts_mutated") is not False
            or correction.get("candidate_universe_changed") is not False
        ):
            raise ValueError("A2 credit correction freeze binding is invalid")
        identity = smoke.get("identity", {})
        closeout_credit = correction.get("post_freeze_closeout_credit", {})
        if final_credit is not None:
            closeout_credit = final_credit
        if (
            not isinstance(identity, Mapping)
            or not isinstance(closeout_credit, Mapping)
            or identity.get("model_name") != receipt.get("official_model")
            or closeout_credit.get("model_name") != receipt.get("official_model")
            or closeout_credit.get("limit_reached") is not False
            or closeout_credit.get("rate_limit_reached_type") is not None
            or credit_preflight.get("model_name") != receipt.get("official_model")
        ):
            raise ValueError("A2 Official identity or credit closeout is invalid")
        if audit is not None and final_credit is not None:
            audit_bindings = audit.get("freeze_bindings", {})
            final_bindings = final_credit.get("freeze_bindings", {})
            if (
                audit.get("status") != "PASS"
                or audit_bindings.get("manifest_sha256") != replay["manifest_sha256"]
                or audit_bindings.get("freeze_receipt_sha256") != replay["receipt_sha256"]
                or audit_bindings.get("lock_sha256") != replay["lock_sha256"]
                or final_credit.get("audit_sha256") != audit.get("audit_sha256")
                or final_bindings.get("manifest_sha256") != replay["manifest_sha256"]
                or final_bindings.get("freeze_receipt_sha256") != replay["receipt_sha256"]
                or final_bindings.get("lock_sha256") != replay["lock_sha256"]
                or final_credit.get("prior_credit_snapshot_set_sha256")
                != correction.get("official_credit_snapshot_set_sha256")
            ):
                raise ValueError("A2 independent audit or final credit binding is invalid")
        for path in (
            A2_OFFICIAL_BRIDGE_CONTROL_PATH,
            A2_EXECUTION_CONTRACT_PATH,
            A2_EXECUTION_ENVELOPE_PATH,
            A2_BUDGET_PROFILE_PATH,
        ):
            if not (root / path).is_file():
                raise ValueError(f"missing A2 control: {path.as_posix()}")
    except (
        A2CandidateFreezeError,
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ):
        return {**missing, "status": "INVALID"}
    audit_passed = audit is not None and final_credit is not None
    return {
        **missing,
        "status": (
            "complete_audit_passed_measured_a2_closed"
            if audit_passed
            else "complete_auditor_review_required"
        ),
        "next_authorized_action": (
            A2_AUDIT_PASS_NEXT_AUTHORIZED_ACTION
            if audit_passed
            else A2_FREEZE_NEXT_AUTHORIZED_ACTION
        ),
        "validated": True,
        "generation_attempt_id": receipt["generation_attempt_id"],
        "candidate_count": replay["candidate_count"],
        "matched_candidate_count": replay["matched_candidate_count"],
        "conditional_reserve_candidate_count": replay[
            "conditional_reserve_candidate_count"
        ],
        "manifest_sha256": replay["manifest_sha256"],
        "manifest_file_sha256": _file_sha256(root / A2_CANDIDATE_MANIFEST_PATH),
        "freeze_receipt_sha256": replay["receipt_sha256"],
        "freeze_receipt_file_sha256": _file_sha256(
            root / A2_CANDIDATE_FREEZE_RECEIPT_PATH
        ),
        "lock_sha256": replay["lock_sha256"],
        "lock_file_sha256": _file_sha256(root / A2_CANDIDATE_FREEZE_LOCK_PATH),
        "smoke_receipt_sha256": smoke["receipt_sha256"],
        "smoke_receipt_file_sha256": _file_sha256(
            root / A2_OFFICIAL_SMOKE_RECEIPT_PATH
        ),
        "credit_preflight_receipt_sha256": credit_preflight["receipt_sha256"],
        "credit_preflight_receipt_file_sha256": _file_sha256(
            root / A2_OFFICIAL_CREDIT_PREFLIGHT_RECEIPT_PATH
        ),
        "credit_correction_receipt_sha256": correction["receipt_sha256"],
        "credit_correction_receipt_file_sha256": _file_sha256(
            root / A2_OFFICIAL_CREDIT_CORRECTION_RECEIPT_PATH
        ),
        "independent_audit_status": "PASS" if audit_passed else "pending",
        "independent_audit_receipt_sha256": (
            audit["audit_sha256"] if audit is not None else None
        ),
        "independent_audit_receipt_file_sha256": (
            _file_sha256(root / A2_INDEPENDENT_AUDIT_RECEIPT_PATH)
            if audit is not None
            else None
        ),
        "final_credit_receipt_sha256": (
            final_credit["receipt_sha256"] if final_credit is not None else None
        ),
        "final_credit_receipt_file_sha256": (
            _file_sha256(root / A2_FINAL_CREDIT_RECEIPT_PATH)
            if final_credit is not None
            else None
        ),
        "official_identity": {
            "provider": identity["model_provider"],
            "model_name": identity["model_name"],
            "reasoning_effort": identity["reasoning_effort"],
            "sdk_version": identity["sdk_version"],
            "cli_version": identity["cli_version"],
        },
        "official_credit": {
            key: closeout_credit[key]
            for key in (
                "snapshot_sha256",
                "model_name",
                "plan_type",
                "used_percent",
                "remaining_percent",
                "resets_at_utc",
                "rate_limit_reached_type",
                "reset_credit_available_count",
                "reset_credit_consumed",
                "limit_reached",
            )
        },
        "credit_check_count": (
            final_credit["official_credit_check_count_total"]
            if final_credit is not None
            else correction["official_credit_check_count"]
        ),
        "credit_snapshot_set_sha256": (
            final_credit["credit_snapshot_chain_sha256"]
            if final_credit is not None
            else correction["official_credit_snapshot_set_sha256"]
        ),
        "control_bindings": [
            {"uri": path.as_posix(), "sha256": _file_sha256(root / path)}
            for path in (
                A2_OFFICIAL_BRIDGE_CONTROL_PATH,
                A2_EXECUTION_CONTRACT_PATH,
                A2_EXECUTION_ENVELOPE_PATH,
                A2_BUDGET_PROFILE_PATH,
            )
        ],
        "measured_a2_started": False,
        "rep_dev_accessed_for_measurement": False,
        "gpu_work_performed": False,
        "provider_admission_performed": False,
        "provider_execution_adoption_performed": False,
        "selection_accesses": 0,
        "final_accesses": 0,
        "harness_dev_accesses": 0,
        "protected_data_accessed": False,
    }


def build_read_model(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    campaign_id = "scope-autoindex-v1"
    try:
        armindex = build_armindex_projection(root)
    except ArmIndexContractError:
        armindex = _empty_armindex_projection()
    feasibility = _a08_compute_storage_feasibility_projection(root)
    closeout = _a09_phase_closeout_projection(root)
    adapter_validation = _a11_adapter_fixture_projection(root)
    a1_2_scaffold = _a12_contract_scaffold_projection(root)
    a1_2_split_claim_audit = _a12_rep_harness_claim_audit_projection(root)
    a1_2_p02_limit_audit = _a12_p02_limit_audit_projection(root)
    a1_2_dense_overflow = _a12_dense_overflow_projection(root)
    a1_2_exact_token_id_probe = _a12_exact_token_id_adapter_probe_projection(root)
    a1_2_r13_failure = _a12_r13_failure_projection(root)
    a1_2_current_attempt = _a12_current_attempt_projection(root)
    a1_2_remote_retention = _a12_r15_remote_retention_projection(root)
    a2_candidate_freeze = _a2_candidate_freeze_projection(root)
    a2_execution_readiness = _a2_execution_readiness_projection(
        root, a2_candidate_freeze
    )
    armindex = {
        **armindex,
        "legacy_code_harvest": _a010_legacy_code_harvest_projection(root),
        "compute_storage_feasibility": feasibility,
        "phase_closeout": closeout,
        "adapter_fixture_validation": adapter_validation,
        "a1_2_contract_scaffold": a1_2_scaffold,
        "a1_2_rep_harness_claim_audit": a1_2_split_claim_audit,
        "a1_2_p02_limit_audit": a1_2_p02_limit_audit,
        "a1_2_dense_overflow": a1_2_dense_overflow,
        "a1_2_exact_token_id_adapter_probe": a1_2_exact_token_id_probe,
        "a1_2_r13_failure": a1_2_r13_failure,
        "a1_2_current_attempt": a1_2_current_attempt,
        "a1_2_remote_retention": a1_2_remote_retention,
        "a2_candidate_freeze": a2_candidate_freeze,
        "a2_execution_readiness": a2_execution_readiness,
    }
    a11_declared_complete = any(
        task.get("task_id") == "A1.1" and task.get("status") == "complete"
        for phase in armindex.get("phases", [])
        if isinstance(phase, Mapping)
        for task in phase.get("tasks", [])
        if isinstance(task, Mapping)
    )
    if a1_2_current_attempt.get("validated") is True:
        current_status = a1_2_current_attempt["status"]
        armindex["status"] = (
            "a1_2_terminal_pass_25_of_25_closeout_recorded"
            if current_status == "PASS"
            else "a1_2_terminal_failed_closed_retry_required"
        )
        armindex["current_phase"] = "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        armindex["next_command"] = str(a1_2_current_attempt["next_authorized_action"])
        armindex["phases"] = [
            {
                **phase,
                "status": (
                    (
                        "complete"
                        if current_status == "PASS"
                        else "a1_2_terminal_failed_closed_retry_required"
                    )
                    if phase.get("phase_id")
                    == "A1_BASELINES_AND_MULTI_ARM_SCREENING"
                    else "planned"
                    if current_status == "PASS"
                    and phase.get("phase_id") == "A2_PER_ARM_AUTOINDEX"
                    else phase.get("status")
                ),
                "tasks": [
                    {
                        **task,
                        "status": (
                            (
                                "complete"
                                if current_status == "PASS"
                                else "a1_2_terminal_failed_closed_retry_required"
                            )
                            if task.get("task_id") == "A1.2"
                            else task.get("status")
                        ),
                    }
                    for task in phase.get("tasks", [])
                    if isinstance(task, Mapping)
                ],
            }
            for phase in armindex.get("phases", [])
            if isinstance(phase, Mapping)
        ]
        if current_status == "PASS":
            counters = (
                dict(armindex.get("counters", {}))
                if isinstance(armindex.get("counters"), Mapping)
                else {}
            )
            counters["measured_runs"] = 1
            armindex["counters"] = counters
    elif a1_2_current_attempt.get("status") == "INVALID":
        armindex["status"] = "a1_2_current_terminal_pointer_invalid_fail_closed"
        armindex["current_phase"] = "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        armindex["next_command"] = a1_2_current_attempt["next_authorized_action"]
    elif (
        a1_2_scaffold.get("validated") is True
        and a1_2_scaffold.get("status")
        == "a1_2_scientific_execution_adoption_request_prepared_owner_review_launch_locked"
        and isinstance(a1_2_scaffold.get("scientific_execution_request_v11"), Mapping)
        and a1_2_scaffold["scientific_execution_request_v11"].get("validated") is True
    ):
        armindex["status"] = (
            "a1_2_scientific_execution_adoption_request_prepared_owner_review_launch_locked"
        )
        armindex["current_phase"] = "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        armindex["next_command"] = a1_2_scaffold["next_authorized_action"]
    elif (
        a1_2_scaffold.get("validated") is True
        and a1_2_scaffold.get("status")
        == "a1_2_live_synthetic_preflight_closed_provider_destroyed_launch_locked"
        and isinstance(a1_2_scaffold.get("provider_closeout_v10"), Mapping)
        and a1_2_scaffold["provider_closeout_v10"].get("validated") is True
    ):
        armindex["status"] = (
            "a1_2_live_synthetic_preflight_closed_provider_destroyed_launch_locked"
        )
        armindex["current_phase"] = "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        armindex["next_command"] = a1_2_scaffold["next_authorized_action"]
        armindex["arms"] = [
            {**item, "status": "live_synthetic_preflight_pass"}
            if item.get("arm_id") in {"ARM-02", "ARM-03", "ARM-04", "ARM-05"}
            else item
            for item in armindex.get("arms", [])
        ]
    elif (
        a1_2_scaffold.get("validated") is True
        and a1_2_scaffold.get("status")
        == "a1_2_live_synthetic_preflight_pass_owner_disposition_pending_launch_locked"
        and isinstance(a1_2_scaffold.get("vast_preflight_v9"), Mapping)
        and a1_2_scaffold["vast_preflight_v9"].get("validated") is True
        and a1_2_scaffold["vast_preflight_v9"].get("live_result_status") == "PASS"
    ):
        armindex["status"] = (
            "a1_2_live_synthetic_preflight_pass_owner_disposition_pending_launch_locked"
        )
        armindex["current_phase"] = "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        armindex["next_command"] = a1_2_scaffold["next_authorized_action"]
        armindex["arms"] = [
            {
                **item,
                "adapter_status": (
                    "bm25s_cpu_lock_and_synthetic_rank_parity_validated"
                    if item.get("arm_id") == "ARM-01"
                    else "v9_live_synthetic_gpu_preflight_pass_scientific_execution_locked"
                ),
            }
            for item in armindex.get("arms", [])
        ]
    elif (
        a1_2_scaffold.get("validated") is True
        and a1_2_scaffold.get("status")
        == "a1_2_live_preflight_execution_lifecycle_prepared_launch_locked"
        and isinstance(a1_2_scaffold.get("vast_preflight_v9"), Mapping)
        and a1_2_scaffold["vast_preflight_v9"].get("validated") is True
    ):
        armindex["status"] = (
            "a1_2_live_preflight_execution_lifecycle_prepared_launch_locked"
        )
        armindex["current_phase"] = "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        armindex["next_command"] = a1_2_scaffold["next_authorized_action"]
        armindex["arms"] = [
            {
                **item,
                "adapter_status": (
                    "bm25s_cpu_lock_and_synthetic_rank_parity_validated"
                    if item.get("arm_id") == "ARM-01"
                    else "v9_attempt_scoped_synthetic_gpu_preflight_pending"
                ),
            }
            for item in armindex.get("arms", [])
        ]
    elif (
        a1_2_scaffold.get("validated") is True
        and a1_2_scaffold.get("status")
        == "a1_2_live_preflight_validation_complete_bundle_prepared_launch_locked"
        and isinstance(a1_2_scaffold.get("vast_preflight_v8"), Mapping)
        and a1_2_scaffold["vast_preflight_v8"].get("validated") is True
    ):
        armindex["status"] = (
            "a1_2_live_preflight_validation_complete_bundle_prepared_launch_locked"
        )
        armindex["current_phase"] = "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        armindex["next_command"] = a1_2_scaffold["next_authorized_action"]
        armindex["arms"] = [
            {
                **item,
                "adapter_status": (
                    "bm25s_cpu_lock_and_synthetic_rank_parity_validated"
                    if item.get("arm_id") == "ARM-01"
                    else "v8_validation_complete_bundle_prepared_synthetic_preflight_pending"
                ),
            }
            for item in armindex.get("arms", [])
        ]
    elif (
        a1_2_scaffold.get("validated") is True
        and a1_2_scaffold.get("status")
        == "a1_2_live_preflight_same_instance_repair_prepared_launch_locked"
        and isinstance(a1_2_scaffold.get("vast_preflight_v7"), Mapping)
        and a1_2_scaffold["vast_preflight_v7"].get("validated") is True
    ):
        armindex["status"] = (
            "a1_2_live_preflight_same_instance_repair_prepared_launch_locked"
        )
        armindex["current_phase"] = "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        armindex["next_command"] = a1_2_scaffold["next_authorized_action"]
        armindex["arms"] = [
            {
                **item,
                "adapter_status": (
                    "bm25s_cpu_lock_and_synthetic_rank_parity_validated"
                    if item.get("arm_id") == "ARM-01"
                    else "v7_same_instance_repair_prepared_synthetic_preflight_pending"
                ),
            }
            for item in armindex.get("arms", [])
        ]
    elif (
        a1_2_scaffold.get("validated") is True
        and a1_2_scaffold.get("status")
        == "a1_2_live_preflight_correction_prepared_launch_locked"
        and isinstance(a1_2_scaffold.get("vast_preflight_v6"), Mapping)
        and a1_2_scaffold["vast_preflight_v6"].get("validated") is True
    ):
        armindex["status"] = "a1_2_live_preflight_correction_prepared_launch_locked"
        armindex["current_phase"] = "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        armindex["next_command"] = a1_2_scaffold["next_authorized_action"]
        armindex["arms"] = [
            {
                **item,
                "adapter_status": (
                    "bm25s_cpu_lock_and_synthetic_rank_parity_validated"
                    if item.get("arm_id") == "ARM-01"
                    else "v6_live_container_correction_prepared_synthetic_preflight_pending"
                ),
            }
            for item in armindex.get("arms", [])
        ]
    elif (
        a1_2_scaffold.get("validated") is True
        and a1_2_scaffold.get("status")
        == "a1_2_runtime_minimal_direct_base_preflight_prepared_launch_locked"
        and isinstance(a1_2_scaffold.get("vast_preflight_v5"), Mapping)
        and a1_2_scaffold["vast_preflight_v5"].get("validated") is True
    ):
        armindex["status"] = (
            "a1_2_runtime_minimal_direct_base_preflight_prepared_launch_locked"
        )
        armindex["current_phase"] = "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        armindex["next_command"] = a1_2_scaffold["next_authorized_action"]
        armindex["arms"] = [
            {
                **item,
                "adapter_status": (
                    "bm25s_cpu_lock_and_synthetic_rank_parity_validated"
                    if item.get("arm_id") == "ARM-01"
                    else "v5_direct_official_base_prepared_owner_local_stage_pending"
                ),
            }
            for item in armindex.get("arms", [])
        ]
    elif (
        a1_2_scaffold.get("validated") is True
        and a1_2_scaffold.get("status")
        == "a1_2_vast_4x3090_postcommit_preflight_prepared_launch_locked"
        and isinstance(a1_2_scaffold.get("vast_preflight_v3"), Mapping)
        and a1_2_scaffold["vast_preflight_v3"].get("validated") is True
    ):
        armindex["status"] = (
            "a1_2_vast_4x3090_postcommit_preflight_prepared_launch_locked"
        )
        armindex["current_phase"] = "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        armindex["next_command"] = a1_2_scaffold["next_authorized_action"]
        armindex["arms"] = [
            {
                **item,
                "adapter_status": (
                    "bm25s_cpu_lock_and_synthetic_rank_parity_validated"
                    if item.get("arm_id") == "ARM-01"
                    else "v3_clean_bundle_identity_prepared_owner_live_preflight_pending"
                ),
            }
            for item in armindex.get("arms", [])
        ]
    elif (
        a1_2_scaffold.get("validated") is True
        and a1_2_scaffold.get("status")
        == "a1_2_vast_4x3090_preflight_prepared_launch_locked"
        and isinstance(a1_2_scaffold.get("vast_preflight_v2"), Mapping)
        and a1_2_scaffold["vast_preflight_v2"].get("validated") is True
    ):
        armindex["status"] = "a1_2_vast_4x3090_preflight_prepared_launch_locked"
        armindex["current_phase"] = "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        armindex["next_command"] = A1_2_SCAFFOLD_NEXT_AUTHORIZED_ACTION
        armindex["arms"] = [
            {
                **item,
                "adapter_status": (
                    "bm25s_cpu_lock_and_synthetic_rank_parity_validated"
                    if item.get("arm_id") == "ARM-01"
                    else "v2_parallel_worker_prepared_owner_live_preflight_pending"
                ),
            }
            for item in armindex.get("arms", [])
        ]
    elif (
        a1_2_scaffold.get("validated") is True
        and a1_2_scaffold.get("status")
        == "a1_2_contract_scaffold_complete_launch_locked"
    ):
        armindex["status"] = "a1_2_contract_scaffold_complete_launch_locked"
        armindex["current_phase"] = "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        armindex["next_command"] = A1_2_SCAFFOLD_NEXT_AUTHORIZED_ACTION
        armindex["arms"] = [
            {
                **item,
                "adapter_status": (
                    "bm25s_cpu_lock_and_synthetic_rank_parity_validated"
                    if item.get("arm_id") == "ARM-01"
                    else "source_metadata_frozen_owner_artifacts_pending"
                ),
            }
            for item in armindex.get("arms", [])
        ]
    elif (
        adapter_validation.get("validated") is True
        and adapter_validation.get("status") == "complete"
    ):
        armindex["status"] = "a1_1_complete_a1_2_contract_locked"
        armindex["current_phase"] = "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        armindex["next_command"] = A1_2_NEXT_AUTHORIZED_ACTION
        armindex["arms"] = [
            {
                **item,
                "adapter_status": (
                    "synthetic_cpu_fixture_validated_measured_lock_pending"
                    if item.get("arm_id") == "ARM-01"
                    else "declared_fixture_blocked_offline_model_lock_pending"
                ),
            }
            for item in armindex.get("arms", [])
        ]
    elif a11_declared_complete:
        armindex["status"] = "a1_1_receipt_invalid_fail_closed"
        armindex["current_phase"] = "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        armindex["next_command"] = A1_1_NEXT_AUTHORIZED_ACTION
    elif closeout.get("validated") is True and closeout.get("status") == "complete":
        armindex["current_phase"] = "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        armindex["next_command"] = A1_1_NEXT_AUTHORIZED_ACTION
    elif (
        feasibility.get("validated") is True and feasibility.get("status") == "complete"
    ):
        if armindex.get("current_phase") != "A0_MIGRATION_FOUNDATION":
            armindex["status"] = "a0_closeout_invalid_fail_closed"
            armindex["current_phase"] = "A0_MIGRATION_FOUNDATION"
        armindex["next_command"] = A0_9_NEXT_AUTHORIZED_ACTION
    if a1_2_current_attempt.get("validated") is True:
        armindex["local_adoption_input_status"] = (
            "A1_COMPLETE_25_OF_25"
            if a1_2_current_attempt["status"] == "PASS"
            else "REQUIRES_FRESH_A1_ADMISSION_AND_COMPLETE_RETRY"
        )
        armindex["next_command"] = a1_2_current_attempt["next_authorized_action"]
    elif a1_2_current_attempt.get("status") == "INVALID":
        armindex["local_adoption_input_status"] = "INVALID_CURRENT_A1_TERMINAL_POINTER"
    if (
        a1_2_current_attempt.get("validated") is True
        and a1_2_current_attempt.get("status") == "PASS"
        and a2_candidate_freeze.get("validated") is True
    ):
        armindex["status"] = (
            "a2_staged_not_launched_measured_a2_locked"
            if a2_execution_readiness.get("status")
            == "STAGED_NOT_LAUNCHED_MEASURED_A2_LOCKED"
            else "a2_provider_admission_failed_closed_measured_a2_locked"
            if a2_execution_readiness.get("status")
            == "PROVIDER_ADMISSION_FAILED_CLOSED_MEASUREMENT_LOCKED"
            else "a2_implementation_blocked_measured_a2_locked"
            if a2_execution_readiness.get("status")
            == "IMPLEMENTATION_BLOCKED_MEASUREMENT_LOCKED"
            else "a2_ready_for_ap_fresh_instance_staging_measured_a2_locked"
            if a2_execution_readiness.get("status")
            == "READY_FOR_AP_FRESH_INSTANCE_STAGING_MEASUREMENT_LOCKED"
            else "a2_execution_readiness_complete_fresh_admission_required"
            if a2_execution_readiness.get("validated") is True
            else "a2_candidate_freeze_audit_passed_measured_a2_closed"
            if a2_candidate_freeze.get("independent_audit_status") == "PASS"
            else "a2_candidate_freeze_complete_auditor_review_required"
        )
        armindex["current_phase"] = "A2_PER_ARM_AUTOINDEX"
        armindex["next_command"] = (
            a2_execution_readiness["next_authorized_action"]
            if a2_execution_readiness.get("validated") is True
            else a2_candidate_freeze["next_authorized_action"]
        )
        armindex["phases"] = [
            {
                **phase,
                "status": (
                    "staged"
                    if a2_execution_readiness.get("status")
                    == "STAGED_NOT_LAUNCHED_MEASURED_A2_LOCKED"
                    else "blocked"
                    if a2_execution_readiness.get("status")
                    in {
                        "PROVIDER_ADMISSION_FAILED_CLOSED_MEASUREMENT_LOCKED",
                        "IMPLEMENTATION_BLOCKED_MEASUREMENT_LOCKED",
                    }
                    else "ready"
                    if a2_execution_readiness.get("validated") is True
                    else "blocked"
                )
                if phase.get("phase_id") == "A2_PER_ARM_AUTOINDEX"
                else phase.get("status"),
                "tasks": (
                    [
                        {
                            **task,
                            "status": (
                                "staged"
                                if a2_execution_readiness.get("status")
                                == "STAGED_NOT_LAUNCHED_MEASURED_A2_LOCKED"
                                else "blocked"
                                if a2_execution_readiness.get("status")
                                in {
                                    "PROVIDER_ADMISSION_FAILED_CLOSED_MEASUREMENT_LOCKED",
                                    "IMPLEMENTATION_BLOCKED_MEASUREMENT_LOCKED",
                                }
                                else "ready"
                                if a2_execution_readiness.get("validated") is True
                                else "blocked"
                            )
                            if task.get("task_id") == "A2.1"
                            else task.get("status"),
                        }
                        for task in phase.get("tasks", [])
                        if isinstance(task, Mapping)
                    ]
                    + [
                        {
                            "task_id": "OFFICIAL_CODEX_BRIDGE_AND_CANDIDATE_FREEZE",
                            "title": "Official Codex bridge and five-arm candidate freeze",
                            "status": "complete",
                        }
                    ]
                    if phase.get("phase_id") == "A2_PER_ARM_AUTOINDEX"
                    else [
                        dict(task)
                        for task in phase.get("tasks", [])
                        if isinstance(task, Mapping)
                    ]
                ),
            }
            for phase in armindex.get("phases", [])
            if isinstance(phase, Mapping)
        ]
    elif a2_candidate_freeze.get("status") == "INVALID":
        armindex["status"] = "a2_candidate_freeze_invalid_fail_closed"
        armindex["current_phase"] = "A2_PER_ARM_AUTOINDEX"
        armindex["next_command"] = "REPAIR_A2_FREEZE_PROJECTION_BEFORE_AUDIT"
        armindex["next_command"] = a1_2_current_attempt["next_authorized_action"]
    elif (
        a1_2_current_attempt.get("validated") is not True
        and a1_2_dense_overflow.get("validated") is True
    ):
        armindex["local_adoption_input_status"] = a1_2_dense_overflow["status"]
        armindex["next_command"] = a1_2_dense_overflow["next_authorized_action"]
    elif (
        a1_2_current_attempt.get("validated") is not True
        and a1_2_p02_limit_audit.get("validated") is True
    ):
        armindex["local_adoption_input_status"] = "BLOCKED_CONTRACT_DEFECT"
        armindex["next_command"] = a1_2_p02_limit_audit["next_authorized_action"]
    campaign_config = _load_yaml_like(
        root / "control" / "campaigns" / f"{campaign_id}.yaml"
    )
    legacy_disposition = _load_legacy_disposition(root)
    manifests = _load_manifests(root / "campaigns" / campaign_id / "manifests")
    invalidated_receipt_hashes = (
        {str(legacy_disposition["receipt_sha256"])} if legacy_disposition else set()
    )
    receipts = _load_receipts(
        root / "campaigns" / campaign_id / "evidence",
        invalidated_receipt_hashes=invalidated_receipt_hashes,
    )
    validation_reports = _load_validation_reports(
        root / "campaigns" / campaign_id / "validation-reports"
    )
    p1_pairs = validated_p1_matrix(manifests, receipts, validation_reports)
    p2_readiness = _p2_readiness_projection(root, campaign_config)
    observatory = load_observatory_projection(root)
    package_review: dict[str, Any] = {}
    if (root / "control/assets/dapfam-p1-source.v1.json").is_file() and p1_pairs:
        package_review = _validated_p1_package_review(root, p1_pairs)
        if not package_review:
            p1_pairs = []
    paired_manifest_hashes = {
        str(pair["manifest"]["manifest_sha256"]) for pair in p1_pairs
    }
    paired_receipts = [pair["receipt"] for pair in p1_pairs]
    mlflow_registration = _load_optional_json(
        root / "evidence" / "mlflow-p1-registration.v2.json"
    )
    decisions = _load_jsonl(root / "control" / "decisions" / "ledger.jsonl")
    metrics: list[dict[str, Any]] = []
    runs: list[dict[str, Any]] = []
    experiments: dict[str, dict[str, Any]] = {}
    evidence: list[dict[str, Any]] = []
    total_actual = 0.0
    total_estimated = 0.0
    for manifest in manifests:
        if (
            _is_p1_manifest(manifest)
            and str(manifest.get("manifest_sha256", "")) not in paired_manifest_hashes
        ):
            continue
        run_id = str(manifest.get("run_id", "unknown"))
        experiment_id = str(manifest.get("experiment_id", f"exp-{run_id}"))
        experiments.setdefault(
            experiment_id,
            {
                "experiment_id": experiment_id,
                "campaign_id": campaign_id,
                "run_count": 0,
            },
        )["run_count"] += 1
        run_metrics = manifest.get("metrics", [])
        if isinstance(run_metrics, dict):
            run_metrics = [
                {"name": key, "value": value} for key, value in run_metrics.items()
            ]
        for item in run_metrics if isinstance(run_metrics, list) else []:
            if isinstance(item, dict):
                metrics.append({"run_id": run_id, **item})
        resources = (
            manifest.get("resources", {})
            if isinstance(manifest.get("resources"), dict)
            else {}
        )
        actual = resources.get("cost_actual")
        estimate = resources.get("cost_estimated")
        if isinstance(actual, (int, float)) and not isinstance(actual, bool):
            total_actual += float(actual)
        if isinstance(estimate, (int, float)) and not isinstance(estimate, bool):
            total_estimated += float(estimate)
        runs.append(
            {
                "run_id": run_id,
                "manifest_sha256": manifest.get("manifest_sha256"),
                "experiment_id": experiment_id,
                "campaign_id": campaign_id,
                "stage": manifest.get("stage", "unknown"),
                "status": manifest.get("status", "unknown"),
                "arm": (
                    manifest["method"].get("arm_id") or manifest["method"].get("arm")
                )
                if isinstance(manifest.get("method"), dict)
                else None,
                "source": manifest.get("inputs", {}).get("source", {})
                if isinstance(manifest.get("inputs"), dict)
                else {},
                "owner_local_receipt_sha256": manifest.get("receipt_sha256"),
            }
        )
        for artifact in (
            manifest.get("artifacts", [])
            if isinstance(manifest.get("artifacts"), list)
            else []
        ):
            if isinstance(artifact, dict) and artifact.get("sha256"):
                evidence.append(
                    {
                        "evidence_id": artifact.get(
                            "artifact_id", artifact.get("name", "artifact")
                        ),
                        "sha256": artifact["sha256"],
                        "run_id": run_id,
                        "uri": artifact.get("uri"),
                    }
                )
    datasets = _dataset_projection(root, paired_receipts)
    if package_review:
        evidence.extend(
            [
                {
                    "evidence_id": "p1-four-slot-package",
                    "sha256": package_review["package_file_sha256"],
                    "run_id": package_review["package_id"],
                    "uri": package_review["package_uri"],
                },
                {
                    "evidence_id": "p1-rigor-review",
                    "sha256": package_review["review_sha256"],
                    "run_id": package_review["review_id"],
                    "uri": package_review["review_uri"],
                },
            ]
        )
    if _registration_matches_p1_pair(mlflow_registration, p1_pairs, package_review):
        evidence.append(
            {
                "evidence_id": "mlflow-p1-registration",
                "sha256": _file_sha256(
                    root / "evidence" / "mlflow-p1-registration.v2.json"
                ),
                "run_id": str(
                    mlflow_registration.get("parent", {}).get(
                        "source_run_id", "p1-parent"
                    )
                ),
                "uri": "evidence/mlflow-p1-registration.v2.json",
            }
        )
    else:
        mlflow_registration = {}
    readiness = _publication_readiness(root, p1_pairs, decisions, legacy_disposition)
    configured_phases = (
        campaign_config.get("phases", [])
        if isinstance(campaign_config.get("phases"), list)
        else []
    )
    phases = []
    tasks = []
    for phase in configured_phases:
        if not isinstance(phase, dict):
            continue
        phase_id = str(phase.get("id", ""))
        phase_status = str(phase.get("status", "planned"))
        phase_preflight_status: str | None = None
        if phase_id == "P1_CPU_BASELINE":
            phase_status = "measured" if p1_pairs else "blocked"
        elif phase_id == "P2_SCOPE_DEVELOPMENT":
            phase_status = (
                "ready"
                if p2_readiness["status"] == "ready_planned_not_measured"
                else p2_readiness["status"]
            )
            phase_preflight_status = str(
                p2_readiness.get("preflight_status", "not_started")
            )
        phase_row = {"phase_id": phase_id, "status": phase_status, "tasks": []}
        if phase_preflight_status is not None:
            phase_row["preflight_status"] = phase_preflight_status
        for task in (
            phase.get("tasks", []) if isinstance(phase.get("tasks"), list) else []
        ):
            if not isinstance(task, dict):
                continue
            task_row = {
                "task_id": str(task.get("id", "")),
                "phase_id": phase_id,
                "title": str(task.get("title", "")),
                "status": str(task.get("status", "planned")),
                "evidence_ids": [],
            }
            if phase_id == "P1_CPU_BASELINE":
                task_row["status"] = "measured" if p1_pairs else "blocked"
                if p1_pairs:
                    task_row["evidence_ids"] = sorted(
                        {str(pair["receipt"]["request_id"]) for pair in p1_pairs}
                    )
            elif phase_id == "P2_SCOPE_DEVELOPMENT":
                task_row["status"] = (
                    "ready"
                    if p2_readiness["status"] == "ready_planned_not_measured"
                    else p2_readiness["status"]
                )
                task_row["preflight_status"] = str(
                    p2_readiness.get("preflight_status", "not_started")
                )
                task_row["evidence_ids"] = [
                    str(item["uri"]) for item in p2_readiness.get("artifacts", [])
                ]
                official_review = p2_readiness.get("official_review", {})
                if official_review.get("status") == "accepted_static_contract_review":
                    task_row["evidence_ids"].append(
                        str(official_review["source"]["index_uri"])
                    )
            phase_row["tasks"].append(task_row)
            tasks.append(task_row)
        phases.append(phase_row)
    source_commit, generated_at = _source_commit_metadata(root)
    p1_state = "P1_CPU_MEASURED_COMPLETE" if p1_pairs else "P1_BLOCKED_WITH_EVIDENCE"
    next_actions = (
        [
            {
                "action_id": "review-recovery-freeze",
                "label": "รอ Owner ตรวจ recovery freeze และหลักฐาน invalidation",
                "kind": "owner_command",
            },
            {
                "action_id": "fresh-owner-local-p1-rerun",
                "label": "รัน P1 ใหม่แบบ Owner-local เมื่อ Owner สั่งหลัง review",
                "kind": "owner_command",
            },
            {
                "action_id": "hold-before-p2",
                "label": "ห้ามเริ่ม P2 จนกว่า P1 rerun จะมี receipt, manifests และ validation reports ครบ",
                "kind": "constraint",
            },
        ]
        if not p1_pairs
        else [
            {
                "action_id": "review-p1",
                "label": "ตรวจ P1 evidence package ก่อนพิจารณาคำสั่ง P2 แยกต่างหาก",
                "kind": "owner_command",
            },
        ]
    )
    fixture_status = str(
        p2_readiness.get("fixture_pilot", {}).get("status", "not_executed")
        if isinstance(p2_readiness.get("fixture_pilot"), dict)
        else "not_executed"
    )
    if (
        p1_pairs
        and p2_readiness.get("official_review", {}).get("status")
        == "accepted_static_contract_review"
    ):
        if fixture_status == "passed":
            next_actions = [
                {
                    "action_id": "owner-local-p2-measured-preflight",
                    "label": "Owner-local P2 measured preflight",
                    "kind": "owner_command",
                },
                {
                    "action_id": "hold-before-measured-p2",
                    "label": "Do not start measured P2 or selection exposure automatically; preflight requires the Owner-local protected store",
                    "kind": "constraint",
                },
            ]
        else:
            next_actions = [
                {
                    "action_id": "p2-fixture-pilot",
                    "label": "Run the repository-only P2 fixture pilot before Owner-local measured preflight",
                    "kind": "automatic_next",
                },
                {
                    "action_id": "hold-before-measured-p2",
                    "label": "Do not start measured P2 or selection exposure from the static review verdict",
                    "kind": "constraint",
                },
            ]
    result_state = "valid" if p1_pairs else "blocked"
    p1_latency = paired_receipts[0].get("latency_seconds") if paired_receipts else None
    p2_metric_rows = [
        {
            "run_id": str(p2_readiness.get("budget_profile_id", "p2-r1-primary")),
            "phase_id": "P2_SCOPE_DEVELOPMENT",
            **item,
        }
        for item in p2_readiness.get("metrics", [])
    ]
    body: dict[str, Any] = {
        "schema_version": READ_MODEL_SCHEMA,
        "projection_schema_version": PROJECTION_SCHEMA_VERSION,
        "source_commit": source_commit,
        "generated_at": generated_at,
        "project": {
            "program_id": "myis-research",
            "display_name": "myIS Research",
            "campaign_id": campaign_id,
            "active_campaign_id": armindex["campaign_id"],
            "active_direction": "ArmIndex",
            "active_phase": armindex["current_phase"],
            "current_phase": armindex["current_phase"],
            "current_task": (
                "A2.1"
                if armindex["current_phase"] == "A2_PER_ARM_AUTOINDEX"
                else "A1.2"
                if armindex["current_phase"]
                == "A1_BASELINES_AND_MULTI_ARM_SCREENING"
                else "A0"
            ),
            "current_substage": (
                "FROZEN_FIVE_ARM_EXECUTION"
                if armindex["current_phase"] == "A2_PER_ARM_AUTOINDEX"
                else "NOT_APPLICABLE"
            ),
            "state": p1_state,
            "current_status": armindex["status"],
        },
        "projection_health": {
            "status": "blocked" if not p1_pairs else "current",
            "reason": "p1_evidence_matrix_missing" if not p1_pairs else None,
            "shared_revision_required": True,
        },
        "owner_inbox": next_actions[:3],
        "progress": {
            "done": sum(
                1 for task in tasks if task["status"] in {"complete", "measured"}
            ),
            "in_process": sum(
                1 for task in tasks if task["status"] in {"in_progress", "executable"}
            ),
            "planned_or_blocked": sum(
                1
                for task in tasks
                if task["status"]
                not in {"complete", "measured", "in_progress", "executable"}
            ),
            "total": len(tasks),
        },
        "campaigns": [
            {
                "campaign_id": campaign_id,
                "authority_status": "historical_read_only",
                "status": campaign_config.get("campaign", {}).get(
                    "status", "preparation"
                ),
                "title": campaign_config.get("campaign", {}).get("title", campaign_id),
                "primary_metric": campaign_config.get("protocol", {}).get(
                    "primary_metric", "recall_at_100/out"
                ),
                "standing_authorization": "D1_START_CAMPAIGN",
                "active_owner_decisions": ["D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"],
                "current_state": p1_state,
                "p2_status": p2_readiness["status"],
                "p2_preflight_status": p2_readiness.get(
                    "preflight_status", "not_started"
                ),
            },
            {
                "campaign_id": armindex["campaign_id"],
                "status": armindex["status"],
                "title": "ArmIndex - Retriever-Conditioned Representation Search and Harness Optimization",
                "primary_metric": "recall_at_100/out",
                "standing_authorization": "D1_START_CAMPAIGN",
                "active_owner_decisions": ["D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"],
                "current_state": "A0_MIGRATION_FOUNDATION",
                "authority_status": "active",
            },
        ],
        "armindex": armindex,
        "p2_readiness": p2_readiness,
        "observatory": observatory,
        "phases": phases,
        "tasks": tasks,
        "gates": [
            {
                "gate_id": "D2_OPEN_FINAL",
                "status": "approved"
                if any(
                    item.get("decision_id") == "D2_OPEN_FINAL"
                    and item.get("status") == "approved"
                    for item in decisions
                )
                else "waiting_owner",
            },
            {
                "gate_id": "D3_SUBMIT_RELEASE",
                "status": "approved"
                if any(
                    item.get("decision_id") == "D3_SUBMIT_RELEASE"
                    and item.get("status") == "approved"
                    for item in decisions
                )
                else "waiting_owner",
            },
        ],
        "experiments": sorted(
            experiments.values(), key=lambda item: item["experiment_id"]
        ),
        "runs": sorted(runs, key=lambda item: item["run_id"]),
        "metrics": metrics + p2_metric_rows,
        "cost": {
            "currency": "USD",
            "actual": total_actual if manifests else None,
            "estimated": total_estimated if manifests else 0.0,
            "budget": 100.0,
        },
        "decisions": decisions,
        "evidence": evidence,
        "datasets": datasets,
        "historical_exposure": (
            paired_receipts[0].get("historical_exposure", {})
            if paired_receipts
            else (
                {"active_final_872_global_untouched": "not_claimable"}
                if legacy_disposition
                else {}
            )
        ),
        "mlflow_registration": {
            key: mlflow_registration.get(key)
            for key in (
                "schema_version",
                "package_sha256",
                "source_receipt_sha256",
                "dataset_lineage_sha256",
                "parent",
                "children",
            )
            if key in mlflow_registration
        },
        "publication_readiness": readiness,
        "milestones": [
            {
                "milestone_id": phase["phase_id"],
                "status": phase["status"],
                "depends_on": ([phases[index - 1]["phase_id"]] if index else []),
            }
            for index, phase in enumerate(phases)
        ],
        "outputs": (
            [
                {
                    "output_id": "P1-LEGACY-RECEIPT",
                    "phase_id": "P1_CPU_BASELINE",
                    "task_id": "P1.3",
                    "status": legacy_disposition["status"],
                    "evidence_class": legacy_disposition["evidence_class"],
                    "source_uri": legacy_disposition["source_uri"],
                    "source_sha256": legacy_disposition["source_file_sha256"],
                    "disposition_uri": LEGACY_DISPOSITION_RELATIVE_PATH.as_posix(),
                    "promotable": False,
                    "superseded_by": legacy_disposition["superseded_by"],
                }
            ]
            if legacy_disposition
            else []
        ),
        "results": [
            {
                "result_id": "P1-CPU-BASELINE",
                "phase_id": "P1_CPU_BASELINE",
                "task_id": "P1.3",
                "validity": result_state,
                "evidence_maturity": "selection" if p1_pairs else "not_run",
                "metric_ids": [str(item.get("name", "")) for item in metrics]
                if p1_pairs
                else [],
                "claim_boundary": "train_selection_only"
                if p1_pairs
                else "no_measured_claim",
                "limitations": ["active_final_872_global_untouched_not_claimable"],
                "package_sha256": package_review.get("package_sha256"),
                "package_file_sha256": package_review.get("package_file_sha256"),
                "rigor_review_sha256": package_review.get("review_sha256"),
                "rigor_grade": package_review.get("grade"),
                "rigor_mean_score": package_review.get("mean_score"),
            },
            {
                "result_id": "P2-SCOPE-DEVELOPMENT",
                "phase_id": "P2_SCOPE_DEVELOPMENT",
                "task_id": "P2.1",
                "validity": "valid" if p2_readiness["measured"] else "not_measured",
                "evidence_maturity": "measured_selection"
                if p2_readiness["measured"]
                else "non_scientific",
                "metric_ids": [
                    str(item.get("name", ""))
                    for item in p2_readiness.get("metrics", [])
                ],
                "claim_boundary": p2_readiness["claim_boundary"],
                "limitations": [
                    "selection_accesses_remain_zero_until_validated_freeze"
                ],
                "budget_profile_id": p2_readiness.get("budget_profile_id"),
                "budget_profile_sha256": p2_readiness.get("budget_profile_sha256"),
                "selection_exposure_count": p2_readiness.get("selection_accesses", 0),
                "preflight_status": p2_readiness.get("preflight_status", "not_started"),
            },
        ],
        "interpretations": (
            [
                {
                    "interpretation_id": "P1-CPU-BASELINE-INTERPRETATION",
                    "result_id": "P1-CPU-BASELINE",
                    "status": "pending_review" if p1_pairs else "blocked",
                    "statement": "ยังสรุปผลเชิงวิทยาศาสตร์ไม่ได้จนกว่า evidence matrix จะผ่าน",
                },
                {
                    "interpretation_id": "P2-SCOPE-DEVELOPMENT-INTERPRETATION",
                    "result_id": "P2-SCOPE-DEVELOPMENT",
                    "status": (
                        "pending_measurement"
                        if p2_readiness.get("preflight_status") == "not_started"
                        else "pending_owner"
                        if p2_readiness.get("preflight_status")
                        == "passed_pending_owner"
                        else "blocked"
                    ),
                    "statement": "P2 is contract-ready but has no measured result; fixture readiness does not authorize selection or final evaluation.",
                },
            ]
        ),
        "raid": (
            [
                {
                    "raid_id": "RISK-P1-EVIDENCE-MATRIX",
                    "kind": "risk",
                    "status": "open",
                    "summary": "P1 receipt ยังไม่มี hash-matched validation reports และ four-slot manifests",
                }
            ]
            if not p1_pairs
            else []
        ),
        "resources": {
            "cpu_only": True,
            "gpu": False,
            "paid_api": False,
            "budget_usd": 100.0,
            "actual_cost_usd": total_actual if manifests else 0.0,
            "latency_seconds": (
                float(p1_latency)
                if isinstance(p1_latency, (int, float))
                and not isinstance(p1_latency, bool)
                else None
            ),
            "p2_measured_runs": p2_readiness["measured_runs"],
            "p2_selection_accesses": p2_readiness["selection_accesses"],
            "p2_max_wall_clock_seconds": p2_readiness["runtime"].get(
                "max_wall_clock_seconds"
            ),
            "p2_per_candidate_timeout_seconds": p2_readiness["runtime"].get(
                "per_candidate_timeout_seconds"
            ),
        },
        "presentation": {
            "audiences": ["owner", "advisor", "peer"],
            "safe_result_ids": ["P1-CPU-BASELINE", "P2-SCOPE-DEVELOPMENT"],
            "claim_boundary": "no_measured_claim"
            if not p1_pairs
            else "train_selection_only",
            "screens": _presentation_screens(
                p1_state=p1_state,
                phases=phases,
                tasks=tasks,
                next_actions=next_actions,
                has_valid_result=bool(p1_pairs),
                has_legacy_output=bool(legacy_disposition),
            ),
        },
        "reports": {
            "vault_id": "myis-obsidian-report",
            "vault_path": "obsidian_report",
            "generated_manifest": "obsidian_report/00_System/Generated/generated-manifest.json",
        },
        "literature": {
            "registry": "evidence/literature/catalog/corpus_manifest.csv",
            "proxy_mode": True,
        },
        "advisor_updates": {
            "draft_path": "obsidian_report/02_Advisor_Updates/Drafts/CURRENT_ADVISOR_UPDATE.md",
            "presented_immutable": True,
        },
        "tools": {
            "mlflow": {"mode": "read_only_on_demand", "port": 5000},
            "obsidian": {
                "vault_id": "myis-obsidian-report",
                "open_via_dashboard": True,
            },
        },
        "archive_contract": {
            "schema_version": "myis.mlflow-archive-contract.v2",
            "active_experiments": ["myis-armindex-multiretriever-v2", "myis-system"],
            "scientific_experiment": "myis-armindex-multiretriever-v2",
            "system_experiment": "myis-system",
            "legacy_policy": "legacy_read_only",
            "historical_experiments": ["myis-scope-autoindex-v1"],
            "writer": "serialized_append_only",
            "viewer": "sqlite_read_only",
            "freeze_required_for_measured_runs": True,
        },
    }
    revision_body = {key: value for key, value in body.items() if key != "generated_at"}
    body["read_model_revision"] = sha256(canonical_json(revision_body))
    body["projection_revision"] = body["read_model_revision"]
    body["read_model_sha256"] = sha256(canonical_json(body))
    return body


def _empty_armindex_projection() -> dict[str, Any]:
    """Return a fail-closed fragment for unit fixtures without ArmIndex control files."""

    phase_ids = (
        "A0_MIGRATION_FOUNDATION",
        "A1_BASELINES_AND_MULTI_ARM_SCREENING",
        "A2_PER_ARM_AUTOINDEX",
        "A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT",
        "A4_PRODUCTION_TRANSFER_AND_SELECTION",
        "A5_FINAL_CONFIRMATION",
        "A6_PUBLICATION_AND_RELEASE",
    )
    return {
        "schema_version": "myis.armindex-read-model.v1",
        "campaign_id": "armindex-multiretriever-v2",
        "status": "control_missing_fail_closed",
        "current_phase": "A0_MIGRATION_FOUNDATION",
        "phases": [
            {
                "phase_id": phase_id,
                "purpose": "control unavailable",
                "status": "blocked",
                "tasks": [],
            }
            for phase_id in phase_ids
        ],
        "arms": [
            {
                "arm_id": f"ARM-{index:02d}",
                "model_id": "unresolved",
                "role": "unresolved",
                "license": "unresolved",
                "commercial_status": "unresolved",
                "adapter_status": "blocked",
                "representation_status": "not_started",
            }
            for index in range(1, 6)
        ],
        "representation_programs": [],
        "transfer": {"status": "not_started", "matrix_entries": 0},
        "complementarity": {"status": "not_started", "evaluated_arm_sets": 0},
        "harnessopt": {
            "status": "not_started",
            "candidate_count": 0,
            "forbidden_mutations": [],
        },
        "production_profiles": [
            {"profile_id": profile, "status": "contract_only"}
            for profile in ("FAST", "BALANCED", "DEEP")
        ],
        "champions": {"research": None, "commercial": None},
        "counters": {
            "measured_runs": 0,
            "candidate_count": 0,
            "selection_accesses": 0,
            "final_accesses": 0,
        },
        "gates": [
            {"gate_id": gate, "status": "waiting_owner"}
            for gate in ("D2_OPEN_FINAL", "D3_SUBMIT_RELEASE")
        ],
        "budget": {
            "currency": "USD",
            "actual": 0.0,
            "hard_stop": 100.0,
            "migration_profile": "armindex-migration-v2",
        },
        "historical_campaigns": [
            {
                "campaign_id": "scope-autoindex-v1",
                "status": "historical_read_only",
                "p1_measured_evidence": "preserved_by_pointer",
                "p2_measured_runs": 0,
            }
        ],
        "next_command": "Resolve missing ArmIndex control files before any execution.",
    }


def _a010_legacy_code_harvest_projection(root: Path) -> dict[str, Any]:
    """Load only a validated, aggregate-safe A0.10 ledger/receipt pair."""

    missing = {
        "status": "not_started",
        "validated": False,
        "evidence_class": "engineering",
        "scientific_authority": False,
        "claim_boundary": "engineering_provenance_only",
        "ledger_uri": A010_LEGACY_CODE_HARVEST_LEDGER_PATH.as_posix(),
        "ledger_sha256": None,
        "receipt_uri": A010_LEGACY_CODE_HARVEST_RECEIPT_PATH.as_posix(),
        "receipt_sha256": None,
        "fixture_status": "not_started",
        "fixture_receipt_uri": None,
        "fixture_receipt_sha256": None,
        "repository_hygiene_audit_uri": A010_REPOSITORY_HYGIENE_AUDIT_PATH.as_posix(),
        "repository_hygiene_audit_sha256": None,
        "output_root_relocation_receipt_uri": A010_OUTPUT_ROOT_RELOCATION_RECEIPT_PATH.as_posix(),
        "output_root_relocation_receipt_sha256": None,
        "source_verification_receipt_uri": A010_SOURCE_VERIFICATION_RECEIPT_PATH.as_posix(),
        "source_verification_receipt_sha256": None,
        "components_reviewed": 0,
        "components_adopted": 0,
        "components_rejected": 0,
        "measured_runs": 0,
        "selection_accesses": 0,
        "final_accesses": 0,
    }
    ledger_path = root / A010_LEGACY_CODE_HARVEST_LEDGER_PATH
    receipt_path = root / A010_LEGACY_CODE_HARVEST_RECEIPT_PATH
    if not ledger_path.exists() and not receipt_path.exists():
        return missing
    if (
        not ledger_path.is_file()
        or ledger_path.is_symlink()
        or not receipt_path.is_file()
        or receipt_path.is_symlink()
    ):
        return {**missing, "status": "invalid"}
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if not isinstance(ledger, Mapping) or not isinstance(receipt, Mapping):
            raise ValueError("A0.10 ledger and receipt must be objects")
        assert_aggregate_only(ledger)
        assert_aggregate_only(receipt)
        ledger_hash = _file_sha256(ledger_path)
        if str(ledger.get("ledger_sha256", "")) != canonical_sha256(
            {key: value for key, value in ledger.items() if key != "ledger_sha256"}
        ):
            raise ValueError("A0.10 ledger self-hash is invalid")
        if str(receipt.get("receipt_sha256", "")) != canonical_sha256(
            {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        ):
            raise ValueError("A0.10 receipt self-hash is invalid")
        if (
            receipt.get("schema_version")
            != "myis.armindex-legacy-code-harvest-receipt.v1"
            or ledger.get("schema_version")
            != "myis.armindex-legacy-code-harvest-ledger.v1"
            or receipt.get("campaign_id") != "armindex-multiretriever-v2"
            or receipt.get("phase_id") != "A0_MIGRATION_FOUNDATION"
            or receipt.get("task_id") != "A0.10"
            or receipt.get("ledger_uri")
            != A010_LEGACY_CODE_HARVEST_LEDGER_PATH.as_posix()
            or receipt.get("ledger_sha256") != ledger_hash
        ):
            raise ValueError("A0.10 receipt bindings are invalid")
        if (
            receipt.get("scientific_authority") is not False
            or receipt.get("protected_data_accessed") is not False
        ):
            raise ValueError("A0.10 receipt crosses a protected or scientific boundary")
        if receipt.get("measured_execution_performed") is not False:
            raise ValueError("A0.10 receipt cannot report measured execution")
        if receipt.get("next_authorized_action") != A0_8_NEXT_AUTHORIZED_ACTION:
            raise ValueError("A0.10 next authorized action is not canonical")
        counters = receipt.get("counters")
        if not isinstance(counters, Mapping) or any(
            counters.get(key) != 0
            for key in ("measured_runs", "selection_accesses", "final_accesses")
        ):
            raise ValueError("A0.10 receipt counters must remain zero")
        components = receipt.get("components")
        if not isinstance(components, Mapping):
            raise ValueError("A0.10 receipt component aggregates are missing")
        component_counts = {
            key: int(components.get(key, 0))
            for key in ("reviewed", "adopted", "rejected")
        }
        if any(value < 0 for value in component_counts.values()):
            raise ValueError("A0.10 component aggregate cannot be negative")
        fixture_uri = receipt.get("fixture_receipt_uri")
        fixture_sha = receipt.get("fixture_receipt_sha256")
        if (fixture_uri is None) != (fixture_sha is None):
            raise ValueError("A0.10 fixture receipt binding is incomplete")
        if fixture_uri is not None:
            if not isinstance(fixture_uri, str) or not isinstance(fixture_sha, str):
                raise ValueError("A0.10 fixture receipt binding is invalid")
            fixture_path = (root / fixture_uri).resolve()
            fixture_path.relative_to(root.resolve())
            if (
                fixture_path.is_symlink()
                or not fixture_path.is_file()
                or _file_sha256(fixture_path) != fixture_sha
            ):
                raise ValueError("A0.10 fixture receipt commitment is invalid")
        status = str(receipt.get("status", "invalid"))
        if status not in {"not_started", "in_progress", "complete", "blocked"}:
            raise ValueError("A0.10 receipt status is invalid")
        fixture_status = str(receipt.get("fixture_status", "not_started"))
        if fixture_status not in {"not_started", "passed", "failed"}:
            raise ValueError("A0.10 fixture status is invalid")
        if fixture_status == "passed" and fixture_uri is None:
            raise ValueError("passed A0.10 fixture requires a committed receipt")
        supporting_artifacts = (
            (
                "repository_hygiene_audit_uri",
                "repository_hygiene_audit_sha256",
                A010_REPOSITORY_HYGIENE_AUDIT_PATH,
                "myis.repository-hygiene-audit.v1",
                "audit_sha256",
            ),
            (
                "output_root_relocation_receipt_uri",
                "output_root_relocation_receipt_sha256",
                A010_OUTPUT_ROOT_RELOCATION_RECEIPT_PATH,
                "myis.output-root-relocation.v1",
                "receipt_sha256",
            ),
            (
                "source_verification_receipt_uri",
                "source_verification_receipt_sha256",
                A010_SOURCE_VERIFICATION_RECEIPT_PATH,
                "myis.source-verification-receipt.v1",
                "receipt_sha256",
            ),
        )
        loaded_supporting: dict[Path, Mapping[str, Any]] = {}
        for (
            uri_key,
            sha_key,
            expected_path,
            schema_version,
            self_hash_key,
        ) in supporting_artifacts:
            uri = receipt.get(uri_key)
            digest = receipt.get(sha_key)
            if uri != expected_path.as_posix() or not isinstance(digest, str):
                raise ValueError(
                    f"A0.10 supporting artifact binding is invalid: {uri_key}"
                )
            artifact_path = (root / expected_path).resolve()
            artifact_path.relative_to(root.resolve())
            if (
                artifact_path.is_symlink()
                or not artifact_path.is_file()
                or _file_sha256(artifact_path) != digest
            ):
                raise ValueError(
                    f"A0.10 supporting artifact commitment is invalid: {uri_key}"
                )
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            if (
                not isinstance(artifact, Mapping)
                or artifact.get("schema_version") != schema_version
                or artifact.get("status") != "PASS"
                or artifact.get("scientific_authority") is not False
                or artifact.get(self_hash_key)
                != canonical_sha256(
                    {
                        key: value
                        for key, value in artifact.items()
                        if key != self_hash_key
                    }
                )
            ):
                raise ValueError(
                    f"A0.10 supporting artifact content is invalid: {uri_key}"
                )
            assert_aggregate_only(artifact)
            loaded_supporting[expected_path] = artifact

        source_verification = loaded_supporting[A010_SOURCE_VERIFICATION_RECEIPT_PATH]
        repositories = ledger.get("source_repositories")
        components = ledger.get("components")
        if not isinstance(repositories, list) or not isinstance(components, list):
            raise ValueError("A0.10 ledger source provenance is incomplete")
        thaipha_repository = next(
            (
                item
                for item in repositories
                if isinstance(item, Mapping) and item.get("repository") == "ThaiPha-Lex"
            ),
            None,
        )
        thaipha_components = {
            str(item.get("component_id")): item
            for item in components
            if isinstance(item, Mapping)
            and item.get("source_repository") == "ThaiPha-Lex"
        }
        verified_components = source_verification.get("components")
        if (
            not isinstance(thaipha_repository, Mapping)
            or source_verification.get("source_commit")
            != thaipha_repository.get("commit")
            or source_verification.get("source_tree") != thaipha_repository.get("tree")
            or source_verification.get("source_remote")
            != thaipha_repository.get("remote")
            or source_verification.get("verified_from_git_object_database") is not True
            or not isinstance(verified_components, list)
            or source_verification.get("verified_component_count")
            != len(thaipha_components)
        ):
            raise ValueError("A0.10 source verification receipt identity is invalid")
        verified_by_id = {
            str(item.get("component_id")): item
            for item in verified_components
            if isinstance(item, Mapping)
        }
        if set(verified_by_id) != set(thaipha_components):
            raise ValueError("A0.10 source verification coverage is incomplete")
        for component_id, source in thaipha_components.items():
            verified = verified_by_id[component_id]
            if (
                verified.get("source_path") != source.get("source_path")
                or verified.get("source_sha256") != source.get("source_sha256")
                or verified.get("disposition") != source.get("disposition")
                or not re.fullmatch(r"[a-f0-9]{40}", str(verified.get("git_blob", "")))
            ):
                raise ValueError(
                    "A0.10 source verification component binding is invalid"
                )
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        return {**missing, "status": "invalid"}
    return {
        **missing,
        "status": status,
        "validated": True,
        "ledger_sha256": ledger_hash,
        "receipt_sha256": str(receipt["receipt_sha256"]),
        "fixture_status": fixture_status,
        "fixture_receipt_uri": fixture_uri,
        "fixture_receipt_sha256": fixture_sha,
        "repository_hygiene_audit_sha256": str(
            receipt["repository_hygiene_audit_sha256"]
        ),
        "output_root_relocation_receipt_sha256": str(
            receipt["output_root_relocation_receipt_sha256"]
        ),
        "source_verification_receipt_sha256": str(
            receipt["source_verification_receipt_sha256"]
        ),
        "components_reviewed": component_counts["reviewed"],
        "components_adopted": component_counts["adopted"],
        "components_rejected": component_counts["rejected"],
        "measured_runs": int(counters["measured_runs"]),
        "selection_accesses": int(counters["selection_accesses"]),
        "final_accesses": int(counters["final_accesses"]),
    }


def _a08_compute_storage_feasibility_projection(root: Path) -> dict[str, Any]:
    """Load one receipt-bound, aggregate-safe A0.8 feasibility result."""

    missing = {
        "status": "not_started",
        "validated": False,
        "fixture_status": "not_started",
        "evidence_class": "engineering_fixture",
        "scientific_authority": False,
        "claim_boundary": "synthetic_host_feasibility_only_no_production_projection",
        "task_receipt_uri": A08_TASK_RECEIPT_PATH.as_posix(),
        "task_receipt_sha256": None,
        "fixture_manifest_uri": A08_FIXTURE_MANIFEST_PATH.as_posix(),
        "fixture_manifest_sha256": None,
        "fixture_receipt_uri": A08_FIXTURE_RECEIPT_PATH.as_posix(),
        "fixture_receipt_sha256": None,
        "runbook_uri": A08_RUNBOOK_PATH.as_posix(),
        "runbook_sha256": None,
        "ledger_uri": A08_LEDGER_PATH.as_posix(),
        "ledger_sha256": None,
        "profiles": [],
        "observations": [],
        "host": {},
        "runtime": {},
        "asset_observation": {},
        "measured_runs": 0,
        "selection_accesses": 0,
        "final_accesses": 0,
        "next_authorized_action": A0_8_NEXT_AUTHORIZED_ACTION,
    }
    task_path = root / A08_TASK_RECEIPT_PATH
    if not task_path.is_file():
        return missing
    invalid = {**missing, "status": "invalid"}
    try:
        task_receipt = json.loads(task_path.read_text(encoding="utf-8"))
        manifest_path = root / A08_FIXTURE_MANIFEST_PATH
        fixture_receipt_path = root / A08_FIXTURE_RECEIPT_PATH
        runbook_path = root / A08_RUNBOOK_PATH
        ledger_path = root / A08_LEDGER_PATH
        manifest = json.loads(manifest_path.read_text(encoding="ascii"))
        fixture_receipt = json.loads(fixture_receipt_path.read_text(encoding="ascii"))
        if not isinstance(task_receipt, Mapping):
            raise ValueError("A0.8 task receipt must be an object")
        validate_compute_storage_artifacts(manifest, fixture_receipt)
        task_unsigned = {
            key: value for key, value in task_receipt.items() if key != "receipt_sha256"
        }
        if task_receipt.get("receipt_sha256") != canonical_sha256(task_unsigned):
            raise ValueError("A0.8 task receipt self-hash is invalid")
        expected_files = (
            ("runbook_uri", "runbook_sha256", A08_RUNBOOK_PATH, runbook_path),
            ("ledger_uri", "ledger_sha256", A08_LEDGER_PATH, ledger_path),
            (
                "fixture_manifest_uri",
                "fixture_manifest_sha256",
                A08_FIXTURE_MANIFEST_PATH,
                manifest_path,
            ),
            (
                "fixture_receipt_uri",
                "fixture_receipt_sha256",
                A08_FIXTURE_RECEIPT_PATH,
                fixture_receipt_path,
            ),
        )
        for uri_key, sha_key, expected_path, actual_path in expected_files:
            if task_receipt.get(uri_key) != expected_path.as_posix():
                raise ValueError(f"A0.8 task receipt path is invalid: {uri_key}")
            if task_receipt.get(sha_key) != _file_sha256(actual_path):
                raise ValueError(f"A0.8 task receipt commitment is invalid: {sha_key}")
        if task_receipt.get("fixture_manifest_self_sha256") != manifest.get(
            "manifest_sha256"
        ):
            raise ValueError("A0.8 manifest self-hash binding is invalid")
        if task_receipt.get("fixture_receipt_self_sha256") != fixture_receipt.get(
            "receipt_sha256"
        ):
            raise ValueError("A0.8 fixture receipt self-hash binding is invalid")
        if (
            task_receipt.get("schema_version")
            != "myis.armindex-compute-storage-task-receipt.v1"
            or task_receipt.get("campaign_id") != "armindex-multiretriever-v2"
            or task_receipt.get("phase_id") != "A0_MIGRATION_FOUNDATION"
            or task_receipt.get("task_id") != "A0.8"
            or task_receipt.get("status") != "complete"
            or task_receipt.get("fixture_status") != "passed"
        ):
            raise ValueError("A0.8 task receipt identity or status is invalid")
        if (
            task_receipt.get("scientific_authority") is not False
            or task_receipt.get("protected_data_accessed") is not False
            or task_receipt.get("measured_execution_performed") is not False
        ):
            raise ValueError(
                "A0.8 task receipt crosses the engineering evidence boundary"
            )
        if task_receipt.get("next_authorized_action") != A0_9_NEXT_AUTHORIZED_ACTION:
            raise ValueError("A0.8 next authorized action is not canonical")
        counters = task_receipt.get("counters", {})
        resources = task_receipt.get("resource_counters", {})
        if not isinstance(counters, Mapping) or any(
            value != 0 for value in counters.values()
        ):
            raise ValueError("A0.8 task receipt real counters must remain zero")
        if not isinstance(resources, Mapping) or any(
            value != 0 for value in resources.values()
        ):
            raise ValueError("A0.8 task receipt resource counters must remain zero")
        asset = task_receipt.get("asset_observation", {})
        if (
            not isinstance(asset, Mapping)
            or asset.get("asset_id") != "APP-SPARSE-FTS-INDEXES"
            or asset.get("registry_disposition")
            != "protected_reference_only_not_allowed_in_A0"
            or asset.get("protected_payload_opened") is not False
            or asset.get("source_bytes_copied") is not False
        ):
            raise ValueError("A0.8 App asset observation is unsafe or incomplete")
        _validate_a08_ledger(ledger_path)
        assert_aggregate_only(task_receipt)
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        return invalid
    return {
        **missing,
        "status": "complete",
        "validated": True,
        "fixture_status": "passed",
        "task_receipt_sha256": _file_sha256(task_path),
        "fixture_manifest_sha256": _file_sha256(manifest_path),
        "fixture_receipt_sha256": _file_sha256(fixture_receipt_path),
        "runbook_sha256": _file_sha256(runbook_path),
        "ledger_sha256": _file_sha256(ledger_path),
        "profiles": list(manifest["profiles"]),
        "observations": list(fixture_receipt["observations"]),
        "host": dict(fixture_receipt["host"]),
        "runtime": dict(fixture_receipt["runtime"]),
        "asset_observation": dict(task_receipt["asset_observation"]),
        "measured_runs": int(task_receipt["counters"]["measured_runs"]),
        "selection_accesses": int(task_receipt["counters"]["selection_accesses"]),
        "final_accesses": int(task_receipt["counters"]["final_accesses"]),
        "next_authorized_action": A0_9_NEXT_AUTHORIZED_ACTION,
    }


def _validate_a08_ledger(path: Path) -> None:
    entries = [
        json.loads(line)
        for line in path.read_text(encoding="ascii").splitlines()
        if line
    ]
    if len(entries) < 2:
        raise ValueError("A0.8 execution ledger is incomplete")
    previous = "0" * 64
    for sequence, entry in enumerate(entries, start=1):
        if not isinstance(entry, Mapping):
            raise ValueError("A0.8 execution ledger entry must be an object")
        unsigned = {key: value for key, value in entry.items() if key != "entry_sha256"}
        if (
            entry.get("sequence") != sequence
            or entry.get("previous_entry_sha256") != previous
        ):
            raise ValueError("A0.8 execution ledger sequence or chain is invalid")
        if entry.get("entry_sha256") != canonical_sha256(unsigned):
            raise ValueError("A0.8 execution ledger self-hash is invalid")
        assert_aggregate_only(entry)
        previous = str(entry["entry_sha256"])


def _a09_phase_closeout_projection(root: Path) -> dict[str, Any]:
    """Load the A0 closeout only after every receipt and safety binding validates."""

    missing = {
        "status": "not_started",
        "validated": False,
        "evidence_class": "engineering_validation",
        "scientific_authority": False,
        "claim_boundary": "a0_engineering_closeout_only_no_measured_retrieval",
        "receipt_uri": A09_PHASE_CLOSEOUT_RECEIPT_PATH.as_posix(),
        "receipt_sha256": None,
        "validation_audit_uri": A09_VALIDATION_AUDIT_PATH.as_posix(),
        "validation_audit_sha256": None,
        "runbook_uri": A09_RUNBOOK_PATH.as_posix(),
        "runbook_sha256": None,
        "ledger_uri": A09_LEDGER_PATH.as_posix(),
        "ledger_sha256": None,
        "completed_task_count": 0,
        "validation_check_count": 0,
        "measured_runs": 0,
        "candidate_count": 0,
        "selection_accesses": 0,
        "final_accesses": 0,
        "next_authorized_action": A0_9_NEXT_AUTHORIZED_ACTION,
    }
    receipt_path = root / A09_PHASE_CLOSEOUT_RECEIPT_PATH
    if not receipt_path.is_file():
        return missing
    invalid = {**missing, "status": "invalid"}
    try:
        receipt = json.loads(receipt_path.read_text(encoding="ascii"))
        audit_path = root / A09_VALIDATION_AUDIT_PATH
        audit = json.loads(audit_path.read_text(encoding="ascii"))
        runbook_path = root / A09_RUNBOOK_PATH
        ledger_path = root / A09_LEDGER_PATH
        a08_path = root / A08_TASK_RECEIPT_PATH
        a010_path = root / A010_LEGACY_CODE_HARVEST_RECEIPT_PATH
        campaign_path = root / "control/campaigns/armindex-multiretriever-v2.yaml"
        if not isinstance(receipt, Mapping) or not isinstance(audit, Mapping):
            raise ValueError("A0 closeout receipt and audit must be objects")
        receipt_unsigned = {
            key: value for key, value in receipt.items() if key != "receipt_sha256"
        }
        audit_unsigned = {
            key: value for key, value in audit.items() if key != "audit_sha256"
        }
        if receipt.get("receipt_sha256") != canonical_sha256(receipt_unsigned):
            raise ValueError("A0 closeout receipt self-hash is invalid")
        if audit.get("audit_sha256") != canonical_sha256(audit_unsigned):
            raise ValueError("A0.9 validation audit self-hash is invalid")
        expected_files = (
            ("runbook_uri", "runbook_sha256", A09_RUNBOOK_PATH, runbook_path),
            ("ledger_uri", "ledger_sha256", A09_LEDGER_PATH, ledger_path),
            (
                "validation_audit_uri",
                "validation_audit_sha256",
                A09_VALIDATION_AUDIT_PATH,
                audit_path,
            ),
            ("a08_receipt_uri", "a08_receipt_sha256", A08_TASK_RECEIPT_PATH, a08_path),
            (
                "a010_receipt_uri",
                "a010_receipt_sha256",
                A010_LEGACY_CODE_HARVEST_RECEIPT_PATH,
                a010_path,
            ),
        )
        for uri_key, sha_key, expected_path, actual_path in expected_files:
            if receipt.get(uri_key) != expected_path.as_posix():
                raise ValueError(f"A0 closeout path is invalid: {uri_key}")
            if receipt.get(sha_key) != _file_sha256(actual_path):
                raise ValueError(f"A0 closeout commitment is invalid: {sha_key}")
        historical_mutable_bindings = (
            (
                "campaign_uri",
                "campaign_sha256",
                "control/campaigns/armindex-multiretriever-v2.yaml",
            ),
            ("program_uri", "program_sha256", "control/program.yaml"),
            ("plan_uri", "plan_sha256", "PLAN.md"),
        )
        for uri_key, sha_key, expected_uri in historical_mutable_bindings:
            if (
                receipt.get(uri_key) != expected_uri
                or re.fullmatch(r"[a-f0-9]{64}", str(receipt.get(sha_key, ""))) is None
            ):
                raise ValueError(f"A0 historical mutable binding is invalid: {sha_key}")
        if (
            receipt.get("schema_version") != "myis.armindex-phase-closeout-receipt.v1"
            or receipt.get("campaign_id") != "armindex-multiretriever-v2"
            or receipt.get("phase_id") != "A0_MIGRATION_FOUNDATION"
            or receipt.get("task_id") != "A0.9"
            or receipt.get("status") != "complete"
            or receipt.get("scientific_authority") is not False
            or receipt.get("protected_data_accessed") is not False
            or receipt.get("measured_execution_performed") is not False
        ):
            raise ValueError("A0 closeout identity, status, or authority is invalid")
        if receipt.get("next_authorized_action") != A1_1_NEXT_AUTHORIZED_ACTION:
            raise ValueError("A0 closeout next authorized action is not canonical")
        counters = receipt.get("counters", {})
        resources = receipt.get("resource_counters", {})
        if not isinstance(counters, Mapping) or any(
            value != 0 for value in counters.values()
        ):
            raise ValueError("A0 closeout counters must remain zero")
        if not isinstance(resources, Mapping) or any(
            value != 0 for value in resources.values()
        ):
            raise ValueError("A0 closeout resource counters must remain zero")
        expected_tasks = {f"A0.{index}" for index in range(1, 11)}
        tasks = receipt.get("tasks", [])
        if (
            not isinstance(tasks, list)
            or {str(item.get("task_id")) for item in tasks if isinstance(item, Mapping)}
            != expected_tasks
            or any(
                item.get("status") != "complete"
                for item in tasks
                if isinstance(item, Mapping)
            )
        ):
            raise ValueError("A0 closeout task coverage is incomplete")
        checks = audit.get("checks", {})
        if (
            audit.get("schema_version") != "myis.armindex-a0-validation-audit.v1"
            or audit.get("status") != "PASS"
            or audit.get("scientific_authority") is not False
            or audit.get("protected_data_accessed") is not False
            or audit.get("measured_execution_performed") is not False
            or not isinstance(checks, Mapping)
            or not checks
            or any(
                not isinstance(check, Mapping) or check.get("status") != "PASS"
                for check in checks.values()
            )
        ):
            raise ValueError("A0.9 validation matrix is incomplete or failed")
        event = parse_contract(receipt.get("closeout_event", {}))
        if (
            event.schema_version != "myis.armindex-phase-closeout-event.v1"
            or event.phase_id != "A0_MIGRATION_FOUNDATION"
            or event.task_id != "A0.9"
            or event.status != "completed"
            or event.aggregate_receipt_sha256 != _file_sha256(audit_path)
            or event.next_authorized_action != A1_1_NEXT_AUTHORIZED_ACTION
        ):
            raise ValueError("A0 typed closeout event is invalid")
        campaign = _load_yaml_like(campaign_path)
        a0_phase = next(
            item
            for item in campaign.get("phases", [])
            if item.get("id") == "A0_MIGRATION_FOUNDATION"
        )
        if a0_phase.get("status") != "complete" or any(
            item.get("status") != "complete" for item in a0_phase.get("tasks", [])
        ):
            raise ValueError("A0 canonical completion state is inconsistent")
        _validate_a09_ledger(ledger_path, audit_sha256=_file_sha256(audit_path))
        assert_aggregate_only(receipt)
        assert_aggregate_only(audit)
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        StopIteration,
        TypeError,
        ValueError,
    ):
        return invalid
    return {
        **missing,
        "status": "complete",
        "validated": True,
        "receipt_sha256": _file_sha256(receipt_path),
        "validation_audit_sha256": _file_sha256(audit_path),
        "runbook_sha256": _file_sha256(runbook_path),
        "ledger_sha256": _file_sha256(ledger_path),
        "completed_task_count": len(tasks),
        "validation_check_count": len(checks),
        "measured_runs": int(counters["measured_runs"]),
        "candidate_count": int(counters["candidate_count"]),
        "selection_accesses": int(counters["selection_accesses"]),
        "final_accesses": int(counters["final_accesses"]),
        "next_authorized_action": A1_1_NEXT_AUTHORIZED_ACTION,
    }


def _a11_adapter_fixture_projection(root: Path) -> dict[str, Any]:
    """Load the receipt-bound A1.1 synthetic adapter and ARM-01 CPU result."""

    root = root.resolve()

    missing = {
        "status": "not_started",
        "validated": False,
        "fixture_status": "not_started",
        "evidence_class": "engineering_fixture",
        "scientific_authority": False,
        "claim_boundary": "synthetic_adapter_and_arm01_cpu_path_only_no_measured_parity",
        "task_receipt_uri": A11_TASK_RECEIPT_PATH.as_posix(),
        "task_receipt_sha256": None,
        "fixture_manifest_uri": A11_FIXTURE_MANIFEST_PATH.as_posix(),
        "fixture_manifest_sha256": None,
        "fixture_receipt_uri": A11_FIXTURE_RECEIPT_PATH.as_posix(),
        "fixture_receipt_sha256": None,
        "runbook_uri": A11_RUNBOOK_PATH.as_posix(),
        "runbook_sha256": None,
        "ledger_uri": A11_LEDGER_PATH.as_posix(),
        "ledger_sha256": None,
        "gpu_proposal_uri": A11_GPU_PROPOSAL_PATH.as_posix(),
        "gpu_proposal_sha256": None,
        "gpu_proposal_status": "not_available",
        "report_contract": {},
        "registered_arms": 0,
        "runnable_cpu_arms": 0,
        "dense_arms_blocked": 0,
        "arm01_backend": {},
        "cpu_observation": {},
        "synthetic_metrics": [],
        "gpu_spec": {},
        "time_estimate": {},
        "budget_estimate": {},
        "owner_needs": [],
        "measured_runs": 0,
        "candidate_count": 0,
        "selection_accesses": 0,
        "final_accesses": 0,
        "resource_counters": {
            "charged_usd": 0,
            "gpu_scientific_runs": 0,
            "paid_api_calls": 0,
            "model_downloads": 0,
            "model_weight_modifications": 0,
        },
        "next_authorized_action": A1_1_NEXT_AUTHORIZED_ACTION,
    }
    task_path = root / A11_TASK_RECEIPT_PATH
    if not task_path.is_file():
        return missing
    invalid = {**missing, "status": "invalid"}
    try:
        task_receipt = json.loads(task_path.read_text(encoding="utf-8"))
        manifest_path = root / A11_FIXTURE_MANIFEST_PATH
        fixture_receipt_path = root / A11_FIXTURE_RECEIPT_PATH
        runbook_path = root / A11_RUNBOOK_PATH
        ledger_path = root / A11_LEDGER_PATH
        proposal_path = root / A11_GPU_PROPOSAL_PATH
        reporting_policy_path = root / "docs/observatory/REPORTING_POLICY.md"
        report_schema_path = root / "schemas/phase-task-report.v1.json"
        manifest = json.loads(manifest_path.read_text(encoding="ascii"))
        fixture_receipt = json.loads(fixture_receipt_path.read_text(encoding="ascii"))
        proposal = load_and_validate_gpu_proposal(root)
        if not isinstance(task_receipt, Mapping):
            raise ValueError("A1.1 task receipt must be an object")
        validate_adapter_fixture_artifacts(manifest, fixture_receipt)
        task_unsigned = {
            key: value for key, value in task_receipt.items() if key != "receipt_sha256"
        }
        if task_receipt.get("receipt_sha256") != canonical_sha256(task_unsigned):
            raise ValueError("A1.1 task receipt self-hash is invalid")
        expected_files = (
            ("runbook_uri", "runbook_sha256", A11_RUNBOOK_PATH, runbook_path),
            ("ledger_uri", "ledger_sha256", A11_LEDGER_PATH, ledger_path),
            (
                "fixture_manifest_uri",
                "fixture_manifest_sha256",
                A11_FIXTURE_MANIFEST_PATH,
                manifest_path,
            ),
            (
                "fixture_receipt_uri",
                "fixture_receipt_sha256",
                A11_FIXTURE_RECEIPT_PATH,
                fixture_receipt_path,
            ),
            (
                "gpu_proposal_uri",
                "gpu_proposal_sha256",
                A11_GPU_PROPOSAL_PATH,
                proposal_path,
            ),
            (
                "reporting_policy_uri",
                "reporting_policy_sha256",
                Path("docs/observatory/REPORTING_POLICY.md"),
                reporting_policy_path,
            ),
            (
                "report_schema_uri",
                "report_schema_sha256",
                Path("schemas/phase-task-report.v1.json"),
                report_schema_path,
            ),
        )
        for uri_key, sha_key, expected_path, actual_path in expected_files:
            if task_receipt.get(uri_key) != expected_path.as_posix():
                raise ValueError(f"A1.1 task receipt path is invalid: {uri_key}")
            expected_sha = str(task_receipt.get(sha_key, ""))
            historical_projection_contract = expected_path in {
                Path("docs/observatory/REPORTING_POLICY.md"),
                Path("schemas/phase-task-report.v1.json"),
            }
            commitment_matches = (
                _tracked_history_commitment_matches(
                    root, expected_path.as_posix(), expected_sha
                )
                if historical_projection_contract
                else expected_sha == _file_sha256(actual_path)
            )
            if not commitment_matches:
                raise ValueError(f"A1.1 task receipt commitment is invalid: {sha_key}")
        if task_receipt.get("fixture_manifest_self_sha256") != manifest.get(
            "manifest_sha256"
        ):
            raise ValueError("A1.1 fixture manifest self-hash binding is invalid")
        if task_receipt.get("fixture_receipt_self_sha256") != fixture_receipt.get(
            "receipt_sha256"
        ):
            raise ValueError("A1.1 fixture receipt self-hash binding is invalid")
        if task_receipt.get("gpu_proposal_self_sha256") != proposal.get(
            "proposal_sha256"
        ):
            raise ValueError("A1.1 GPU proposal self-hash binding is invalid")
        if (
            task_receipt.get("schema_version")
            != "myis.armindex-adapter-fixture-task-receipt.v1"
            or task_receipt.get("campaign_id") != "armindex-multiretriever-v2"
            or task_receipt.get("phase_id") != "A1_BASELINES_AND_MULTI_ARM_SCREENING"
            or task_receipt.get("task_id") != "A1.1"
            or task_receipt.get("status") != "complete"
            or task_receipt.get("fixture_status") != "passed"
        ):
            raise ValueError("A1.1 task receipt identity or status is invalid")
        if (
            task_receipt.get("scientific_authority") is not False
            or task_receipt.get("protected_data_accessed") is not False
            or task_receipt.get("measured_execution_performed") is not False
        ):
            raise ValueError(
                "A1.1 task receipt crosses the engineering evidence boundary"
            )
        if task_receipt.get("next_authorized_action") != A1_2_NEXT_AUTHORIZED_ACTION:
            raise ValueError("A1.1 next authorized action is not canonical")
        counters = task_receipt.get("counters", {})
        resources = task_receipt.get("resource_counters", {})
        if not isinstance(counters, Mapping) or any(
            value != 0 for value in counters.values()
        ):
            raise ValueError("A1.1 task receipt real counters must remain zero")
        if not isinstance(resources, Mapping) or any(
            value != 0 for value in resources.values()
        ):
            raise ValueError("A1.1 task receipt resource counters must remain zero")
        report_contract = task_receipt.get("report_contract", {})
        if (
            not isinstance(report_contract, Mapping)
            or report_contract.get("language") != "en"
            or report_contract.get("required_active_phase_reports") != 7
            or report_contract.get("required_active_task_reports") != 18
            or report_contract.get("required_registered_phase_reports") != 12
            or report_contract.get("required_registered_task_reports") != 27
            or report_contract.get("required_sections") != 15
            or report_contract.get("archive_candidate_count") != 0
            or report_contract.get("archive_disposition")
            != "retain_all_current_and_graph_referenced_reports"
        ):
            raise ValueError(
                "A1.1 detailed English report and archive contract is invalid"
            )
        implementation_bindings = task_receipt.get("implementation_bindings", [])
        if (
            not isinstance(implementation_bindings, list)
            or len(implementation_bindings) < 6
        ):
            raise ValueError("A1.1 implementation bindings are incomplete")
        for binding in implementation_bindings:
            if not isinstance(binding, Mapping):
                raise ValueError("A1.1 implementation binding must be an object")
            uri = binding.get("uri")
            if not isinstance(uri, str) or not uri:
                raise ValueError("A1.1 implementation binding URI is invalid")
            implementation_path = (root / uri).resolve()
            implementation_path.relative_to(root)
            implementation_commitment_matches = _tracked_history_commitment_matches(
                root, uri, str(binding.get("sha256", ""))
            )
            if (
                implementation_path.is_symlink()
                or not implementation_path.is_file()
                or not implementation_commitment_matches
            ):
                raise ValueError("A1.1 implementation binding commitment is invalid")
        if task_receipt.get("gpu_proposal_status") != proposal.get("status"):
            raise ValueError("A1.1 GPU proposal status binding is invalid")
        _validate_a11_ledger(
            ledger_path,
            fixture_receipt_sha256=_file_sha256(fixture_receipt_path),
            gpu_proposal_sha256=_file_sha256(proposal_path),
        )
        assert_aggregate_only(task_receipt)
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        return invalid
    aggregate_counts = manifest.get("aggregate_counts", {})
    return {
        **missing,
        "status": "complete",
        "validated": True,
        "fixture_status": "passed",
        "task_receipt_sha256": _file_sha256(task_path),
        "fixture_manifest_sha256": _file_sha256(manifest_path),
        "fixture_receipt_sha256": _file_sha256(fixture_receipt_path),
        "runbook_sha256": _file_sha256(runbook_path),
        "ledger_sha256": _file_sha256(ledger_path),
        "gpu_proposal_sha256": _file_sha256(proposal_path),
        "gpu_proposal_status": str(proposal["status"]),
        "report_contract": dict(report_contract),
        "registered_arms": int(aggregate_counts.get("registered_arms", 0)),
        "runnable_cpu_arms": int(aggregate_counts.get("runnable_cpu_arms", 0)),
        "dense_arms_blocked": int(aggregate_counts.get("dense_arms_blocked", 0)),
        "arm01_backend": dict(manifest.get("arm01_backend", {})),
        "cpu_observation": dict(fixture_receipt.get("cpu_observation", {})),
        "synthetic_metrics": list(fixture_receipt.get("synthetic_metrics", [])),
        "gpu_spec": dict(proposal.get("proposed_gpu_spec", {})),
        "time_estimate": dict(proposal.get("time_estimate", {})),
        "budget_estimate": dict(proposal.get("budget_estimate", {})),
        "owner_needs": list(proposal.get("owner_needs", [])),
        "measured_runs": int(counters["measured_runs"]),
        "candidate_count": int(counters["candidate_count"]),
        "selection_accesses": int(counters["selection_accesses"]),
        "final_accesses": int(counters["final_accesses"]),
        "resource_counters": dict(resources),
        "next_authorized_action": A1_2_NEXT_AUTHORIZED_ACTION,
    }


def _a12_rep_harness_claim_audit_projection(root: Path) -> dict[str, Any]:
    """Load the aggregate-only split and claim-parser audit."""

    audit_path = root / A12_REP_HARNESS_CLAIM_AUDIT_PATH
    missing = {
        "status": "not_started",
        "validated": False,
        "scientific_authority": False,
        "audit_uri": A12_REP_HARNESS_CLAIM_AUDIT_PATH.as_posix(),
        "audit_sha256": None,
        "audit_file_sha256": None,
        "figure_png_uri": A12_REP_HARNESS_SPLIT_FIGURE_PNG_PATH.as_posix(),
        "figure_png_sha256": None,
        "figure_svg_uri": A12_REP_HARNESS_SPLIT_FIGURE_SVG_PATH.as_posix(),
        "figure_svg_sha256": None,
    }
    if not audit_path.is_file():
        return missing
    try:
        audit = json.loads(audit_path.read_text(encoding="ascii"))
        assert_aggregate_only(audit)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return {**missing, "status": "invalid"}
    split = audit.get("split")
    parser_audit = audit.get("claim_parser_audit")
    safety = audit.get("safety")
    publication = audit.get("publication_v13")
    expected_strata = [
        {
            "role_set": "IN",
            "relevance_count": 20,
            "parent_count": 71,
            "rep_dev_count": 43,
            "harness_dev_count": 28,
        },
        {
            "role_set": "IN+OUT",
            "relevance_count": 20,
            "parent_count": 176,
            "rep_dev_count": 105,
            "harness_dev_count": 71,
        },
        {
            "role_set": "OUT",
            "relevance_count": 20,
            "parent_count": 3,
            "rep_dev_count": 2,
            "harness_dev_count": 1,
        },
    ]
    observed_strata = (
        [
            {key: item.get(key) for key in expected_strata[0]}
            for item in split.get("strata", [])
        ]
        if isinstance(split, Mapping)
        else []
    )
    if (
        audit.get("schema_version") != "myis.armindex-a1.2-rep-harness-claim-audit.v1"
        or audit.get("status") != "SPLIT_PASS_P02_BLOCKED"
        or audit.get("scientific_authority") is not False
        or audit.get("audit_sha256")
        != canonical_sha256(
            {key: value for key, value in audit.items() if key != "audit_sha256"}
        )
        or not isinstance(split, Mapping)
        or split.get("status") != "PASS"
        or split.get("counts")
        != {"parent_train": 250, "rep_dev": 150, "harness_dev": 100}
        or observed_strata != expected_strata
        or split.get("grouping_policy", {}).get("constraint_count") != 0
        or split.get("deterministic_replay", {}).get("forward_repeat_match") is not True
        or split.get("deterministic_replay", {}).get("reversed_relation_input_match")
        is not True
        or not isinstance(parser_audit, Mapping)
        or parser_audit.get("status") != "PASS_WITH_P02_BLOCKER"
        or parser_audit.get("independence_source") != "INFERRED_FROM_REGEX_ABSENCE"
        or parser_audit.get("ground_truth_available") is not False
        or parser_audit.get("recommendation")
        != "ADDITIVE_PRE_MEASUREMENT_P02_FIRST_CLAIM_REPAIR"
        or not isinstance(safety, Mapping)
        or any(bool(value) for value in safety.values())
        or not isinstance(publication, Mapping)
        or publication.get("unchanged_in_this_change") is not True
        or publication.get("contract_sha256")
        != _file_sha256(
            root / "control/armindex/a1.2/publication-impact-contract.v13.json"
        )
        or publication.get("disposition_sha256")
        != _file_sha256(
            root / "control/armindex/a1.2/instance-disposition-policy.v13.json"
        )
        or not (root / A12_REP_HARNESS_SPLIT_FIGURE_PNG_PATH).is_file()
        or not (root / A12_REP_HARNESS_SPLIT_FIGURE_SVG_PATH).is_file()
    ):
        return {**missing, "status": "invalid"}
    return {
        **dict(audit),
        "validated": True,
        "audit_uri": A12_REP_HARNESS_CLAIM_AUDIT_PATH.as_posix(),
        "audit_file_sha256": _file_sha256(audit_path),
        "figure_png_uri": A12_REP_HARNESS_SPLIT_FIGURE_PNG_PATH.as_posix(),
        "figure_png_sha256": _file_sha256(root / A12_REP_HARNESS_SPLIT_FIGURE_PNG_PATH),
        "figure_svg_uri": A12_REP_HARNESS_SPLIT_FIGURE_SVG_PATH.as_posix(),
        "figure_svg_sha256": _file_sha256(root / A12_REP_HARNESS_SPLIT_FIGURE_SVG_PATH),
    }


def _a12_p02_limit_audit_projection(root: Path) -> dict[str, Any]:
    """Load the additive P02 PASS and deterministic input-limit blocker."""

    missing = {
        "status": "not_started",
        "validated": False,
        "scientific_authority": False,
        "p02_audit_uri": A12_P02_FIRST_CLAIM_AUDIT_PATH.as_posix(),
        "p02_audit_file_sha256": None,
        "input_limit_audit_uri": A12_EFFECTIVE_INPUT_LIMIT_AUDIT_PATH.as_posix(),
        "input_limit_audit_file_sha256": None,
    }
    p02_path = root / A12_P02_FIRST_CLAIM_AUDIT_PATH
    limit_path = root / A12_EFFECTIVE_INPUT_LIMIT_AUDIT_PATH
    if not p02_path.is_file() or not limit_path.is_file():
        return missing
    try:
        p02 = json.loads(p02_path.read_text(encoding="ascii"))
        limit = json.loads(limit_path.read_text(encoding="ascii"))
        assert_aggregate_only(p02)
        assert_aggregate_only(limit)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return {**missing, "status": "invalid"}
    p02_unsigned = {key: value for key, value in p02.items() if key != "receipt_sha256"}
    limit_unsigned = {
        key: value for key, value in limit.items() if key != "audit_sha256"
    }
    coverage = p02.get("coverage")
    defect = limit.get("defect")
    impact = limit.get("impact")
    if (
        p02.get("schema_version")
        != "myis.armindex-a1.2-p02-first-claim-repair-receipt.v1"
        or p02.get("status") != "PASS"
        or p02.get("scientific_authority") is not False
        or p02.get("receipt_sha256") != canonical_sha256(p02_unsigned)
        or not isinstance(coverage, Mapping)
        or coverage.get("rep_dev_queries", {}).get("available_count") != 150
        or coverage.get("rep_dev_queries", {}).get("parse_failure_count") != 0
        or coverage.get("corpus", {}).get("available_count") != 45336
        or coverage.get("corpus", {}).get("parse_failure_count") != 0
        or p02.get("parse_failures") != 0
        or p02.get("deterministic_replay", {}).get("status") != "PASS"
        or p02.get("no_silent_fallback", {}).get("status") != "PASS"
        or p02.get("preserved_lineage", {}).get("v11_v12_r3_v13_unchanged") is not True
        or limit.get("schema_version")
        != "myis.armindex-a1.2-effective-input-limit-audit.v1"
        or limit.get("status") != "BLOCKED_CONTRACT_DEFECT"
        or limit.get("scientific_authority") is not False
        or limit.get("audit_sha256") != canonical_sha256(limit_unsigned)
        or not isinstance(defect, Mapping)
        or defect.get("binding_id") != "ARM-03--P00-TAC-DOC"
        or defect.get("effective_input_limit") != 512
        or not isinstance(defect.get("observed_rendered_input_tokens"), int)
        or defect["observed_rendered_input_tokens"] <= defect["effective_input_limit"]
        or defect.get("truncation_performed") is not False
        or not isinstance(impact, Mapping)
        or impact.get("compiled_bindings_25_of_25") != "BLOCKED"
        or impact.get("partial_20_of_25_allowed") is not False
        or limit.get("deterministic_replay", {}).get("status") != "PASS"
        or any(bool(value) for value in limit.get("safety", {}).values())
    ):
        return {**missing, "status": "invalid"}
    return {
        "status": "BLOCKED_CONTRACT_DEFECT",
        "validated": True,
        "evidence_class": "pre_measurement_owner_local_input_validation",
        "scientific_authority": False,
        "claim_boundary": "P02 coverage and deterministic replay passed, but frozen ARM-03 x P00 exceeds its effective input limit without truncation. No retrieval or provider work was performed.",
        "p02": dict(p02),
        "input_limit": dict(limit),
        "p02_audit_uri": A12_P02_FIRST_CLAIM_AUDIT_PATH.as_posix(),
        "p02_audit_file_sha256": _file_sha256(p02_path),
        "input_limit_audit_uri": A12_EFFECTIVE_INPUT_LIMIT_AUDIT_PATH.as_posix(),
        "input_limit_audit_file_sha256": _file_sha256(limit_path),
        "next_authorized_action": "Owner decides an additive pre-measurement program-limit compatibility repair or ARM-03 disposition; do not admit a provider or measured retrieval.",
    }


def _a12_exact_token_id_adapter_probe_projection(root: Path) -> dict[str, Any]:
    """Project the aggregate-safe v16 exact-token-ID adapter probe."""

    missing = {
        "status": "not_started",
        "validated": False,
        "evidence_class": "aggregate_safe_synthetic_runtime_preparation",
        "scientific_authority": False,
        "claim_boundary": (
            "Synthetic adapter preparation only; no protected inputs, retrieval "
            "results, or provider admission are represented."
        ),
        "audit_uri": A12_V16_EXACT_TOKEN_ID_ADAPTER_PROBE_PATH.as_posix(),
        "audit_file_sha256": None,
        "audit_sha256": None,
        "next_authorized_action": (
            "Commit and push the hash-bound repair, build a clean v16 bundle, "
            "re-run provider admission and execution adoption, then resume only "
            "the frozen 25/25 A1.2 screen."
        ),
    }
    audit_path = root / A12_V16_EXACT_TOKEN_ID_ADAPTER_PROBE_PATH
    if not audit_path.is_file():
        return missing
    try:
        audit = json.loads(audit_path.read_text(encoding="ascii"))
        if not isinstance(audit, Mapping):
            raise TypeError("exact-token-ID probe must be an object")
        assert_aggregate_only(audit)
        unsigned = {key: value for key, value in audit.items() if key != "audit_sha256"}
        if (
            audit.get("schema_version")
            != "myis.armindex-a1.2-v16-exact-token-id-adapter-probe.v1"
            or audit.get("status") != "PASS_PRE_MEASUREMENT"
            or audit.get("scientific_authority") is not False
            or audit.get("scope") != "A1_BASELINES_AND_MULTI_ARM_SCREENING/A1.2"
            or audit.get("audit_sha256") != canonical_sha256(unsigned)
        ):
            raise ValueError("exact-token-ID probe identity or self-hash is invalid")
        trigger = audit.get("trigger", {})
        repair = audit.get("repair", {})
        authorization = audit.get("authorization", {})
        counters = audit.get("counters", {})
        if (
            not isinstance(trigger, Mapping)
            or trigger.get("measured_retrieval_started") is not False
            or trigger.get("instance_destroyed") is not False
            or not isinstance(repair, Mapping)
            or any(
                repair.get(key) is not False
                for key in (
                    "scientific_semantics_changed",
                    "source_token_coverage_changed",
                    "source_token_overlap_changed",
                    "window_weighting_changed",
                    "pooling_or_normalization_changed",
                    "retrieval_or_evaluation_executed",
                )
            )
            or not isinstance(authorization, Mapping)
            or any(
                authorization.get(key) is not False
                for key in (
                    "provider_admission_receipt_pass",
                    "execution_adoption_receipt_pass",
                    "measured_retrieval_allowed",
                    "selection_allowed",
                    "final_allowed",
                )
            )
            or not isinstance(counters, Mapping)
            or counters.get("measured_runs") != 0
            or counters.get("selection_accesses") != 0
            or counters.get("final_accesses") != 0
        ):
            raise ValueError("exact-token-ID probe safety boundary drifted")
        synthetic_probe = audit.get("synthetic_probe")
        if not isinstance(synthetic_probe, Mapping) or any(
            not isinstance(synthetic_probe.get(arm_id), Mapping)
            or synthetic_probe[arm_id].get("status") != "PASS"
            for arm_id in ("ARM-02", "ARM-03", "ARM-04", "ARM-05")
        ):
            raise ValueError("exact-token-ID synthetic probe is incomplete")
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        return {**missing, "status": "invalid"}
    return {
        **dict(audit),
        "validated": True,
        "audit_uri": A12_V16_EXACT_TOKEN_ID_ADAPTER_PROBE_PATH.as_posix(),
        "audit_file_sha256": _file_sha256(audit_path),
    }


def _a12_current_attempt_projection(root: Path) -> dict[str, Any]:
    """Project only the explicit, hash-validated current A1.2 terminal attempt."""

    missing = {
        "status": "NOT_STARTED",
        "validated": False,
        "evidence_class": "none",
        "scientific_authority": False,
        "claim_boundary": (
            "No current terminal attempt pointer is validated; historical attempt "
            "records are provenance only and cannot set current A1 or A1.2 state."
        ),
        "pointer_uri": A12_CURRENT_ATTEMPT_POINTER_PATH.as_posix(),
        "pointer_file_sha256": None,
        "receipt_uri": None,
        "receipt_file_sha256": None,
        "next_authorized_action": "PREPARE_FRESH_A1_PROVIDER_ADMISSION_AND_RETRY_25_OF_25_BEFORE_A2",
    }
    pointer_path = root / A12_CURRENT_ATTEMPT_POINTER_PATH
    if not pointer_path.exists():
        return missing
    try:
        result = validate_current_attempt_pointer(root)
        pointer = result["pointer"]
        receipt = result["receipt"]
        measured_summary = None
        cell_eda_package = None
        if receipt["status"] == "PASS":
            measured_summary = validate_measured_result_summary_file(
                root, receipt["attempt_id"]
            )
            lineage = measured_summary.get("lineage")
            if not isinstance(lineage, Mapping) or any(
                lineage.get(summary_field) != receipt.get(receipt_field)
                for summary_field, receipt_field in (
                    ("safe_return_archive_sha256", "safe_return_sha256"),
                    ("promotion_receipt_sha256", "promotion_receipt_sha256"),
                    (
                        "evaluator_closeout_receipt_sha256",
                        "evaluator_receipt_sha256",
                    ),
                )
            ):
                raise MeasuredResultSummaryV16Error(
                    "measured result summary does not bind the terminal receipt"
                )
            eda_path = root / a1_2_cell_eda_package_path(receipt["attempt_id"])
            if eda_path.exists():
                cell_eda_package = validate_cell_eda_package_file(
                    root, receipt["attempt_id"]
                )
                if (
                    cell_eda_package["lineage"]["measured_result_summary_sha256"]
                    != measured_summary["summary_sha256"]
                    or cell_eda_package["lineage"]["cell_receipt_set_sha256"]
                    != measured_summary["lineage"]["cell_receipt_set_sha256"]
                ):
                    raise CellEdaPackageV16Error(
                        "cell EDA package does not bind the measured summary"
                    )
    except (
        TerminalAttemptV16Error,
        MeasuredResultSummaryV16Error,
        CellEdaPackageV16Error,
    ):
        return {
            **missing,
            "status": "INVALID",
            "pointer_file_sha256": (
                _file_sha256(pointer_path) if pointer_path.is_file() else None
            ),
            "next_authorized_action": "REPAIR_OR_REMOVE_INVALID_CURRENT_A1_TERMINAL_POINTER_BEFORE_A2",
        }
    return {
        **dict(receipt),
        "validated": True,
        "pointer_uri": A12_CURRENT_ATTEMPT_POINTER_PATH.as_posix(),
        "pointer_file_sha256": result["pointer_file_sha256"],
        "receipt_uri": pointer["target_uri"],
        "receipt_file_sha256": result["receipt_file_sha256"],
        "measured_result_summary": measured_summary,
        "cell_eda_package": cell_eda_package,
        "next_authorized_action": (
            "A1_CLOSEOUT_COMPLETE_STOP_BEFORE_A2"
            if receipt["status"] == "PASS"
            else "PREPARE_FRESH_A1_SAME_INSTANCE_ADMISSION_AND_RETRY_25_OF_25_BEFORE_A2"
            if receipt.get("provider_disposition_status") == "REUSE_ELIGIBLE"
            else "PREPARE_FRESH_A1_PROVIDER_ADMISSION_AND_RETRY_25_OF_25_BEFORE_A2"
        ),
    }


def _a12_r15_remote_retention_projection(root: Path) -> dict[str, Any]:
    """Project the aggregate-safe, hash-validated remote A1 handoff audit."""

    missing = {
        "status": "not_started",
        "validated": False,
        "evidence_class": "aggregate_safe_remote_retention_audit",
        "scientific_authority": False,
        "claim_boundary": (
            "No repository-safe remote retention audit is validated; provider "
            "storage state cannot be inferred from chat or connection notes."
        ),
        "audit_uri": A12_R15_REMOTE_RETENTION_AUDIT_PATH.as_posix(),
        "audit_file_sha256": None,
        "audit_sha256": None,
    }
    audit_path = root / A12_R15_REMOTE_RETENTION_AUDIT_PATH
    if not audit_path.is_file():
        return missing
    try:
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        unsigned = dict(audit)
        unsigned.pop("audit_sha256", None)
        packages = audit.get("packages")
        post_finalize = audit.get("post_finalize_remote_state")
        safety = audit.get("safety")
        attempt = audit.get("attempt")
        if (
            audit.get("schema_version")
            != "myis.armindex-a1.2-remote-retention-audit.v1"
            or audit.get("status") != "PASS"
            or audit.get("scientific_authority") is not False
            or audit.get("audit_sha256") != canonical_sha256(unsigned)
            or not isinstance(attempt, Mapping)
            or attempt.get("attempt_id") != "a12-v16-20260811-r15"
            or attempt.get("instance_id") != 47411176
            or attempt.get("provider_status") != "running"
            or attempt.get("provider_verification") != "verified"
            or attempt.get("provider_disposition") != "REUSE_ELIGIBLE"
            or not isinstance(packages, Mapping)
            or not isinstance(post_finalize, Mapping)
            or not isinstance(safety, Mapping)
        ):
            raise ValueError("remote retention audit identity or self-hash is invalid")
        for package_id, source_count, total_count in (
            ("a1_baseline", 28, 29),
            ("a1_journal_eda", 7, 8),
            ("a1_closeout", 11, 12),
        ):
            package = packages.get(package_id)
            if (
                not isinstance(package, Mapping)
                or package.get("source_member_count") != source_count
                or package.get("remote_total_file_count") != total_count
                or package.get("remote_member_hash_validation") is not True
                or not re.fullmatch(
                    r"[a-f0-9]{64}", str(package.get("manifest_file_sha256", ""))
                )
                or not re.fullmatch(
                    r"[a-f0-9]{64}", str(package.get("manifest_sha256", ""))
                )
            ):
                raise ValueError("remote retention package validation drifted")
        if (
            post_finalize.get("current_working_directory")
            != "absent_after_finalize"
            or post_finalize.get("output_working_directory")
            != "absent_after_finalize"
            or post_finalize.get("job_ledger_file_count") != 4
            or post_finalize.get("frozen_execution_bundle_present") is not True
            or post_finalize.get("dense_model_root_count") != 4
            or post_finalize.get("safe_return_archive_present") is not True
            or post_finalize.get("measured_working_directories_recreated") is not False
            or safety.get("protected_payload_exported_to_git") is not False
            or safety.get("credentials_recorded") is not False
            or safety.get("raw_provider_payload_recorded") is not False
            or safety.get("instance_destroyed") is not False
            or safety.get("a2_execution_started") is not False
            or safety.get("harness_dev_accesses") != 0
            or safety.get("selection_accesses") != 0
            or safety.get("final_accesses") != 0
        ):
            raise ValueError("remote retention safety boundary drifted")
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        return {**missing, "status": "invalid"}
    return {
        **dict(audit),
        "validated": True,
        "audit_uri": A12_R15_REMOTE_RETENTION_AUDIT_PATH.as_posix(),
        "audit_file_sha256": _file_sha256(audit_path),
    }


def _a12_r13_failure_projection(root: Path) -> dict[str, Any]:
    """Project the aggregate-safe failed r13 live attempt without scientific authority."""

    missing = {
        "status": "not_started",
        "validated": False,
        "evidence_class": "aggregate_safe_live_attempt_failure",
        "scientific_authority": False,
        "claim_boundary": (
            "No complete A1.2 result, evaluation, promotion, A1 closeout, or "
            "publication claim is represented."
        ),
        "audit_uri": A12_V16_R13_FAILURE_AUDIT_PATH.as_posix(),
        "audit_file_sha256": None,
        "audit_sha256": None,
        "next_authorized_action": (
            "PREPARE_FRESH_A1_PROVIDER_ADMISSION_AND_RETRY_25_OF_25_BEFORE_A2"
        ),
    }
    audit_path = root / A12_V16_R13_FAILURE_AUDIT_PATH
    if not audit_path.is_file():
        return missing
    try:
        audit = json.loads(audit_path.read_text(encoding="ascii"))
        if not isinstance(audit, Mapping):
            raise TypeError("r13 failure audit must be an object")
        assert_aggregate_only(audit)
        unsigned = {key: value for key, value in audit.items() if key != "audit_sha256"}
        if (
            audit.get("schema_version") != "myis.armindex-a1.2-attempt-audit.v1"
            or audit.get("audit_id") != "a1.2-v16-r13-failure-audit-20260810"
            or audit.get("phase_id") != "A1_BASELINES_AND_MULTI_ARM_SCREENING"
            or audit.get("task_id") != "A1.2"
            or audit.get("status") != "FAILED_CLOSED"
            or audit.get("evidence_class") != "aggregate_safe_live_attempt_failure"
            or audit.get("scientific_authority") is not False
            or audit.get("audit_sha256") != canonical_sha256(unsigned)
            or audit.get("next_authorized_action")
            != "PREPARE_FRESH_A1_PROVIDER_ADMISSION_AND_RETRY_25_OF_25_BEFORE_A2"
        ):
            raise ValueError("r13 failure audit identity or self-hash is invalid")
        attempt = audit.get("attempt")
        failure = audit.get("failure")
        integrity = audit.get("integrity")
        disposition = audit.get("disposition")
        publication = audit.get("publication_safety")
        if (
            not isinstance(attempt, Mapping)
            or attempt.get("attempt_id") != "a12-v16-20260810-r13"
            or not isinstance(attempt.get("instance_id"), int)
            or attempt["instance_id"] <= 0
            or attempt.get("required_logical_cells") != 25
            or attempt.get("completed_logical_cells") != 24
            or attempt.get("missing_logical_cell") != "ARM-05--P04-SECTION-MULTIVIEW"
            or attempt.get("partial_results_promotable") is not False
            or attempt.get("coverage_by_arm")
            != {"ARM-01": 5, "ARM-02": 5, "ARM-03": 5, "ARM-04": 5, "ARM-05": 4}
            or not isinstance(failure, Mapping)
            or failure.get("watchdog_status") != "HARD_STOP"
            or failure.get("reason") != "ssh_runtime_probe_failed"
            or failure.get("workers_remaining") != 0
            or failure.get("provider_destroy_invoked_by_worker") is not False
            or not isinstance(integrity, Mapping)
            or integrity.get("allowlisted_member_count") != 25
            or integrity.get("cell_receipt_self_hashes_verified") != 24
            or integrity.get("member_hash_recomputed") is not True
            or integrity.get("protected_data_exported") is not False
            or integrity.get("unsafe_field_scan") != "PASS"
            or not isinstance(disposition, Mapping)
            or disposition.get("owner_destroy_confirmed") is not True
            or disposition.get("post_destroy_endpoint_observation")
            != "connection_refused"
            or disposition.get("instance_reuse_allowed") is not False
            or not isinstance(publication, Mapping)
            or any(value is not False for value in publication.values())
        ):
            raise ValueError("r13 failure audit boundary or coverage is invalid")
        for field in ("manifest_file_sha256", "allowlisted_members_sha256"):
            value = integrity.get(field)
            if (
                not isinstance(value, str)
                or re.fullmatch(r"[a-f0-9]{64}", value) is None
            ):
                raise ValueError("r13 failure audit integrity hash is invalid")
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        return {**missing, "status": "invalid"}
    return {
        **dict(audit),
        "validated": True,
        "audit_uri": A12_V16_R13_FAILURE_AUDIT_PATH.as_posix(),
        "audit_file_sha256": _file_sha256(audit_path),
    }


def _a12_dense_overflow_projection(root: Path) -> dict[str, Any]:
    """Project the frozen repair and aggregate-safe protected compiler evidence."""

    missing = {
        "status": "not_started",
        "validated": False,
        "evidence_class": "pre_measurement_owner_local_compatibility_validation",
        "scientific_authority": False,
        "claim_boundary": (
            "Aggregate-only dense overflow planning evidence; encoder execution, "
            "compiled bindings, retrieval, and publication claims remain blocked."
        ),
        "repair_frozen": False,
        "compiler_integration_status": "BLOCKED",
        "compiled_bindings_25_of_25": "BLOCKED",
        "protected_handoff_status": "BLOCKED",
        "transfer_receipt_status": "BLOCKED",
        "contract_uri": A12_DENSE_OVERFLOW_CONTRACT_PATH.as_posix(),
        "contract_file_sha256": None,
        "contract_sha256": None,
        "inventory_uri": A12_DENSE_OVERFLOW_INVENTORY_PATH.as_posix(),
        "inventory_file_sha256": None,
        "inventory_sha256": None,
        "composition_uri": A12_DENSE_OVERFLOW_COMPOSITION_PATH.as_posix(),
        "composition_file_sha256": None,
        "composition_sha256": None,
        "figure_png_uri": A12_DENSE_OVERFLOW_FIGURE_PNG_PATH.as_posix(),
        "figure_png_sha256": None,
        "figure_svg_uri": A12_DENSE_OVERFLOW_FIGURE_SVG_PATH.as_posix(),
        "figure_svg_sha256": None,
        "compiler_integration_uri": A12_PROTECTED_COMPILER_INTEGRATION_CONTRACT_PATH.as_posix(),
        "compiler_integration_file_sha256": None,
        "compiler_integration_contract_sha256": None,
        "compiler_audit_uri": A12_PROTECTED_COMPILER_INTEGRATION_AUDIT_PATH.as_posix(),
        "compiler_audit_file_sha256": None,
        "compiler_audit_sha256": None,
        "budget_model_uri": A12_WHOLE_WORKLOAD_BUDGET_MODEL_V15_PATH.as_posix(),
        "budget_model_file_sha256": None,
        "budget_model_sha256": None,
        "final_receipt_uri": A12_LOCAL_ADOPTION_INPUTS_RECEIPT_V15_PATH.as_posix(),
        "final_receipt_file_sha256": None,
        "final_receipt_sha256": None,
        "bundle_status": "PENDING",
        "watchdog_dry_run_status": "PENDING",
        "local_adoption_input_status": "PENDING",
        "ready_for_live_provider_admission": False,
        "protected_receipts": {},
        "compiler_coverage": {},
        "compiler_safety": {},
        "next_authorized_action": (
            "Implement and validate protected compiler integration for the frozen "
            "dense-overflow policy; then rerun 25/25 parity and zero-truncation preflight."
        ),
    }
    contract_path = root / A12_DENSE_OVERFLOW_CONTRACT_PATH
    inventory_path = root / A12_DENSE_OVERFLOW_INVENTORY_PATH
    composition_path = root / A12_DENSE_OVERFLOW_COMPOSITION_PATH
    figure_png_path = root / A12_DENSE_OVERFLOW_FIGURE_PNG_PATH
    figure_svg_path = root / A12_DENSE_OVERFLOW_FIGURE_SVG_PATH
    integration_path = root / A12_PROTECTED_COMPILER_INTEGRATION_CONTRACT_PATH
    compiler_audit_path = root / A12_PROTECTED_COMPILER_INTEGRATION_AUDIT_PATH
    budget_model_path = root / A12_WHOLE_WORKLOAD_BUDGET_MODEL_V15_PATH
    final_receipt_path = root / A12_LOCAL_ADOPTION_INPUTS_RECEIPT_V15_PATH
    if (
        not contract_path.is_file()
        or not inventory_path.is_file()
        or not composition_path.is_file()
    ):
        return missing

    def read_json(path: Path) -> dict[str, Any]:
        value = json.loads(path.read_text(encoding="ascii"))
        if not isinstance(value, dict):
            raise ValueError(f"{path} must contain an object")
        return value

    try:
        contract = read_json(contract_path)
        inventory = read_json(inventory_path)
        composition = read_json(composition_path)
        assert_aggregate_only(contract)
        assert_aggregate_only(inventory)
        assert_aggregate_only(composition)
        contract_unsigned = {
            key: value for key, value in contract.items() if key != "contract_sha256"
        }
        inventory_unsigned = {
            key: value for key, value in inventory.items() if key != "inventory_sha256"
        }
        composition_unsigned = {
            key: value for key, value in composition.items() if key != "audit_sha256"
        }
        contract_sha = canonical_sha256(contract_unsigned)
        inventory_sha = canonical_sha256(inventory_unsigned)
        composition_sha = canonical_sha256(composition_unsigned)
        if contract.get("contract_sha256") != contract_sha:
            raise ValueError("dense overflow contract self-hash mismatch")
        if inventory.get("inventory_sha256") != inventory_sha:
            raise ValueError("dense overflow inventory self-hash mismatch")
        if composition.get("audit_sha256") != composition_sha:
            raise ValueError("dense overflow composition self-hash mismatch")
        if contract.get("status") != "FROZEN_ADDITIVE_PRE_MEASUREMENT_REPAIR":
            raise ValueError("dense overflow repair is not frozen")
        owner_decision = contract.get("owner_decision", {})
        if any(
            owner_decision.get(key) is not expected
            for key, expected in {
                "authorize_additive_dense_overflow_adapter_repair": True,
                "preserve_historical_v11_v12_r3_v13": True,
                "preserve_original_p02_lineage": True,
                "preserve_5_arm_x_5_program_topology": True,
                "allow_partial_screen": False,
                "allow_silent_truncation": False,
                "allow_provider_contact": False,
                "allow_measured_retrieval": False,
            }.items()
        ):
            raise ValueError("dense overflow owner decision drifted")
        implementation = contract.get("implementation", {})
        if implementation.get("version") != "a1.2-dense-overflow-composition-v1":
            raise ValueError("dense overflow implementation version drifted")
        for key in ("planner_source_uri", "audit_source_uri"):
            if not (root / str(implementation.get(key, "missing"))).is_file():
                raise ValueError(f"missing dense overflow implementation source: {key}")
        for key, uri_key in (
            ("planner_source_sha256", "planner_source_uri"),
            ("audit_source_sha256", "audit_source_uri"),
        ):
            if implementation.get(key) != _file_sha256(
                root / str(implementation[uri_key])
            ):
                raise ValueError(f"dense overflow implementation hash drifted: {key}")
        lineage = contract.get("immutable_lineage", {})
        for uri_key, sha_key in (
            ("v11_program_set_uri", "v11_program_set_file_sha256"),
            ("v12_r3_uri", "v12_r3_file_sha256"),
            ("v13_publication_uri", "v13_publication_file_sha256"),
            ("p02_first_claim_uri", "p02_first_claim_file_sha256"),
        ):
            path = root / str(lineage.get(uri_key, "missing"))
            if not path.is_file() or lineage.get(sha_key) != _file_sha256(path):
                raise ValueError(f"immutable lineage hash drifted: {uri_key}")
        raw_inventory = contract.get("raw_inventory", {})
        if (
            raw_inventory.get("uri") != A12_DENSE_OVERFLOW_INVENTORY_PATH.as_posix()
            or raw_inventory.get("file_sha256") != _file_sha256(inventory_path)
            or raw_inventory.get("inventory_sha256") != inventory_sha
        ):
            raise ValueError("dense overflow inventory binding drifted")
        if inventory.get("status") != "PASS_RAW_COMPATIBILITY_INVENTORY":
            raise ValueError("raw dense overflow inventory is not PASS")
        inventory_scope = inventory.get("scope", {})
        if (
            inventory_scope.get("program_arm_cell_count") != 25
            or inventory_scope.get("dense_program_arm_cell_count") != 20
        ):
            raise ValueError("dense overflow inventory topology drifted")
        inventory_safety = inventory.get("safety", {})
        if any(bool(value) for value in inventory_safety.values()):
            raise ValueError("dense overflow inventory safety flags are not clean")
        bindings = composition.get("bindings", {})
        if (
            composition.get("schema_version")
            != "myis.armindex-a1.2-dense-overflow-composition-audit.v1"
            or composition.get("status") != "PASS"
            or composition.get("scientific_authority") is not False
            or bindings.get("contract_sha256") != contract_sha
            or bindings.get("raw_inventory_sha256") != inventory_sha
        ):
            raise ValueError("dense overflow composition binding drifted")
        requirements = composition.get("requirements", {})
        required_checks = (
            "compatible_cells_25_of_25",
            "every_physical_window_within_limit",
            "zero_fallback",
            "zero_omitted_source_tokens",
            "zero_silent_truncation",
        )
        if any(requirements.get(key) is not True for key in required_checks):
            raise ValueError("dense overflow composition requirements are incomplete")
        safety = composition.get("safety", {})
        if any(bool(value) for value in safety.values()):
            raise ValueError("dense overflow composition safety flags are not clean")
        scope = composition.get("scope", {})
        if (
            scope.get("all_program_arm_cells_compatible") != 25
            or scope.get("dense_program_arm_cells") != 20
        ):
            raise ValueError("dense overflow composition topology drifted")
        raw_lineage = contract.get("v9_adapter_lineage", {})
        if (
            not raw_lineage.get("uri")
            or not raw_lineage.get("file_sha256")
            or not raw_lineage.get("receipt_sha256")
        ):
            raise ValueError("v9 adapter lineage is not bound")
        publication = contract.get("publication_method_disclosure", {})
        if (
            publication.get("required") is not True
            or publication.get("retrieval_quality_claim_authorized") is not False
            or publication.get("publication_claim_authorized") is not False
        ):
            raise ValueError("dense overflow publication boundary drifted")
        if not figure_png_path.is_file() or not figure_svg_path.is_file():
            raise ValueError("dense overflow EDA figures are missing")
        compiler_audit = None
        final_receipt = None
        budget_model = None
        if compiler_audit_path.is_file():
            if not integration_path.is_file():
                raise ValueError("protected compiler integration contract is missing")
            compiler_audit = read_json(compiler_audit_path)
            assert_aggregate_only(compiler_audit)
            compiler_audit_sha256 = canonical_sha256(
                {
                    key: value
                    for key, value in compiler_audit.items()
                    if key != "audit_sha256"
                }
            )
            integration = read_json(integration_path)
            if (
                compiler_audit.get("audit_sha256") != compiler_audit_sha256
                or compiler_audit.get("status") != "PASS"
                or compiler_audit.get("coverage", {}).get("compiled_bindings") != 25
                or compiler_audit.get("safety", {}).get("zero_silent_truncation")
                is not True
                or compiler_audit.get("safety", {}).get("protected_boundary") != "PASS"
                or compiler_audit.get("integration", {}).get("file_sha256")
                != _file_sha256(integration_path)
                or compiler_audit.get("integration", {}).get("contract_sha256")
                != integration.get("contract_sha256")
                or compiler_audit.get("publication_v13", {}).get("unchanged")
                is not True
                or compiler_audit.get("authorization", {}).get(
                    "provider_contact_allowed"
                )
                is not False
                or compiler_audit.get("authorization", {}).get(
                    "measured_retrieval_allowed"
                )
                is not False
            ):
                raise ValueError("protected compiler integration audit is incomplete")
            if not budget_model_path.is_file():
                raise ValueError("v15 whole-workload budget model is missing")
            budget_model = read_json(budget_model_path)
            assert_aggregate_only(budget_model)
            budget_model_sha256 = canonical_sha256(
                {
                    key: value
                    for key, value in budget_model.items()
                    if key != "model_sha256"
                }
            )
            if (
                budget_model.get("model_sha256") != budget_model_sha256
                or budget_model.get("status") != "LOCAL_MODEL_PENDING_LIVE_PROVIDER"
                or budget_model.get("workload", {}).get("physical_window_total")
                != 2581603
                or budget_model.get("live_admission", {}).get("admitted") is not False
                or budget_model.get("frozen_hard_stops_usd")
                != {"common_screen": 18, "a1_total": 23, "campaign": 100}
            ):
                raise ValueError("v15 whole-workload budget model is invalid")
            if final_receipt_path.is_file():
                final_receipt = read_json(final_receipt_path)
                assert_aggregate_only(final_receipt)
                final_receipt_sha256 = canonical_sha256(
                    {
                        key: value
                        for key, value in final_receipt.items()
                        if key != "receipt_sha256"
                    }
                )
                if (
                    final_receipt.get("receipt_sha256") != final_receipt_sha256
                    or final_receipt.get("status")
                    != "LOCAL_ADOPTION_INPUTS_VALIDATED_PENDING_LIVE_PROVIDER"
                    or final_receipt.get("compiled_bindings", {}).get("binding_count")
                    != 25
                    or final_receipt.get("compiled_bindings", {}).get(
                        "zero_silent_truncation"
                    )
                    is not True
                    or final_receipt.get("protected_inputs", {}).get(
                        "binding_set_sha256"
                    )
                    != compiler_audit.get("protected_receipts", {}).get(
                        "binding_set_sha256"
                    )
                    or final_receipt.get("budget_model", {}).get("model_sha256")
                    != budget_model_sha256
                    or final_receipt.get("watchdog_destroy_dry_run", {}).get("status")
                    != "PASS"
                    or final_receipt.get("pending_live_provider")
                    != [
                        "fresh_provider_identity",
                        "fresh_all_fee_quote",
                        "whole_workload_live_budget_admission",
                        "live_provider_admission_receipt",
                    ]
                    or final_receipt.get("ready_for_live_provider_admission")
                    is not True
                    or final_receipt.get("authorization", {}).get(
                        "provider_contact_allowed"
                    )
                    is not False
                    or final_receipt.get("authorization", {}).get(
                        "measured_retrieval_allowed"
                    )
                    is not False
                    or final_receipt.get("publication_v13", {}).get("unchanged")
                    is not True
                    or final_receipt.get("publication_v13", {}).get("primary")
                    != "OUT Recall@100"
                    or final_receipt.get("publication_v13", {}).get("secondary")
                    != ["OUT nDCG@100", "OUT nDCG@10"]
                ):
                    raise ValueError("v15 final local adoption receipt is incomplete")
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
        KeyError,
    ):
        return {**missing, "status": "invalid"}

    compiler_validated = compiler_audit is not None
    local_adoption_validated = final_receipt is not None
    next_action = (
        A1_LONG_RUN_NEXT_AUTHORIZED_ACTION
        if local_adoption_validated
        else (
            "Build and validate the additive clean pushed execution bundle, whole-workload "
            "budget model, watchdog/provider-destroy synthetic dry-runs, and final local "
            "adoption receipt while all live-provider inputs remain pending."
        )
        if compiler_validated
        else missing["next_authorized_action"]
    )

    return {
        "status": (
            "LOCAL_ADOPTION_INPUTS_VALIDATED_PENDING_LIVE_PROVIDER"
            if local_adoption_validated
            else "PASS_PROTECTED_COMPILER_INTEGRATION_LOCAL_ONLY"
            if compiler_validated
            else "BLOCKED_PROTECTED_COMPILER_INTEGRATION"
        ),
        "validated": True,
        "evidence_class": "pre_measurement_owner_local_compatibility_validation",
        "scientific_authority": False,
        "claim_boundary": (
            str(compiler_audit["claim_boundary"])
            if compiler_validated
            else (
                "The additive dense-overflow composition plan is frozen and its "
                "aggregate-only compatibility audit passes. The protected compiler "
                "does not yet consume physical windows or emit compiled bindings; no "
                "retrieval, publication, or provider claim is authorized."
            )
        ),
        "repair_frozen": True,
        "compiler_integration_status": "PASS" if compiler_validated else "BLOCKED",
        "compiled_bindings_25_of_25": "PASS" if compiler_validated else "BLOCKED",
        "protected_handoff_status": "PASS" if compiler_validated else "BLOCKED",
        "transfer_receipt_status": "PASS" if compiler_validated else "BLOCKED",
        "contract_uri": A12_DENSE_OVERFLOW_CONTRACT_PATH.as_posix(),
        "contract_file_sha256": _file_sha256(contract_path),
        "contract_sha256": contract_sha,
        "inventory_uri": A12_DENSE_OVERFLOW_INVENTORY_PATH.as_posix(),
        "inventory_file_sha256": _file_sha256(inventory_path),
        "inventory_sha256": inventory_sha,
        "inventory_status": inventory.get("status"),
        "composition_uri": A12_DENSE_OVERFLOW_COMPOSITION_PATH.as_posix(),
        "composition_file_sha256": _file_sha256(composition_path),
        "composition_sha256": composition_sha,
        "composition_status": composition.get("status"),
        "scope": dict(scope),
        "requirements": dict(requirements),
        "safety": dict(safety),
        "composition_semantics": dict(composition.get("composition_semantics", {})),
        "cells": dict(composition.get("cells", {})),
        "publication_method_disclosure": dict(publication),
        "figure_png_uri": A12_DENSE_OVERFLOW_FIGURE_PNG_PATH.as_posix(),
        "figure_png_sha256": _file_sha256(figure_png_path),
        "figure_svg_uri": A12_DENSE_OVERFLOW_FIGURE_SVG_PATH.as_posix(),
        "figure_svg_sha256": _file_sha256(figure_svg_path),
        "compiler_integration_uri": A12_PROTECTED_COMPILER_INTEGRATION_CONTRACT_PATH.as_posix(),
        "compiler_integration_file_sha256": (
            _file_sha256(integration_path) if compiler_validated else None
        ),
        "compiler_integration_contract_sha256": (
            str(compiler_audit["integration"]["contract_sha256"])
            if compiler_validated
            else None
        ),
        "compiler_audit_uri": A12_PROTECTED_COMPILER_INTEGRATION_AUDIT_PATH.as_posix(),
        "compiler_audit_file_sha256": (
            _file_sha256(compiler_audit_path) if compiler_validated else None
        ),
        "compiler_audit_sha256": (
            str(compiler_audit["audit_sha256"]) if compiler_validated else None
        ),
        "budget_model_uri": A12_WHOLE_WORKLOAD_BUDGET_MODEL_V15_PATH.as_posix(),
        "budget_model_file_sha256": (
            _file_sha256(budget_model_path) if compiler_validated else None
        ),
        "budget_model_sha256": (
            str(budget_model["model_sha256"])
            if isinstance(budget_model, Mapping)
            else None
        ),
        "final_receipt_uri": A12_LOCAL_ADOPTION_INPUTS_RECEIPT_V15_PATH.as_posix(),
        "final_receipt_file_sha256": (
            _file_sha256(final_receipt_path) if local_adoption_validated else None
        ),
        "final_receipt_sha256": (
            str(final_receipt["receipt_sha256"])
            if isinstance(final_receipt, Mapping)
            else None
        ),
        "bundle_status": "PASS" if local_adoption_validated else "PENDING",
        "watchdog_dry_run_status": ("PASS" if local_adoption_validated else "PENDING"),
        "local_adoption_input_status": (
            "PASS" if local_adoption_validated else "PENDING"
        ),
        "ready_for_live_provider_admission": local_adoption_validated,
        "protected_receipts": (
            dict(compiler_audit["protected_receipts"]) if compiler_validated else {}
        ),
        "compiler_coverage": (
            dict(compiler_audit["coverage"]) if compiler_validated else {}
        ),
        "compiler_safety": (
            dict(compiler_audit["safety"]) if compiler_validated else {}
        ),
        "next_authorized_action": next_action,
    }


def _a12_contract_scaffold_projection(root: Path) -> dict[str, Any]:
    """Load the validated A1.2 contract scaffold without opening protected data."""

    root = root.resolve()
    missing = {
        "status": "not_started",
        "validated": False,
        "evidence_class": "engineering_contract_scaffold",
        "scientific_authority": False,
        "claim_boundary": "offline_scaffold_only_no_measured_retrieval_claim",
        "receipt_uri": A12_RECEIPT_PATH.as_posix(),
        "receipt_sha256": None,
        "runbook_uri": A12_RUNBOOK_PATH.as_posix(),
        "runbook_sha256": None,
        "ledger_uri": A12_LEDGER_PATH.as_posix(),
        "ledger_sha256": None,
        "execution_contract_uri": (
            A12_CONTROL_ROOT / "execution-contract.v1.json"
        ).as_posix(),
        "execution_contract_sha256": None,
        "arm01_parity_receipt_uri": A12_ARM01_PARITY_RECEIPT_PATH.as_posix(),
        "arm01_parity_receipt_sha256": None,
        "budget_profile_uri": "control/budgets/a1.2-common-screen-v1.json",
        "budget_profile_sha256": None,
        "execution_envelope_uri": "control/execution-envelope-a1.2-v1.yaml",
        "execution_envelope_sha256": None,
        "model_lockset_uri": (A12_CONTROL_ROOT / "model-lockset.v1.json").as_posix(),
        "model_lockset_sha256": None,
        "launch_checklist_uri": (
            A12_CONTROL_ROOT / "launch-checklist.v1.json"
        ).as_posix(),
        "launch_checklist_sha256": None,
        "shutdown_plan_uri": (A12_CONTROL_ROOT / "shutdown-plan.v1.json").as_posix(),
        "shutdown_plan_sha256": None,
        "report_archive_audit_uri": (
            A12_CONTROL_ROOT / "report-archive-audit.v1.json"
        ).as_posix(),
        "report_archive_audit_sha256": None,
        "closeout_validation_audit_uri": A12_CLOSEOUT_VALIDATION_AUDIT_PATH.as_posix(),
        "closeout_validation_audit_sha256": None,
        "closeout_validation_check_count": 0,
        "closeout_validation_recovery_count": 0,
        "closeout_validation_recoveries": [],
        "model_lock_count": 0,
        "offline_adapter_ready": 0,
        "dense_artifact_manifests_pending": 0,
        "owner_requirements_pending": 0,
        "launch_ready": False,
        "measured_execution": False,
        "resource_plan": {},
        "budget_limits": {},
        "archive_disposition": {},
        "real_counters": {
            "measured_runs": 0,
            "candidate_count": 0,
            "selection_accesses": 0,
            "final_accesses": 0,
        },
        "resource_counters": {
            "charged_usd": 0,
            "gpu_scientific_runs": 0,
            "paid_api_calls": 0,
            "model_downloads": 0,
            "provider_switches": 0,
        },
        "next_authorized_action": A1_2_NEXT_AUTHORIZED_ACTION,
        "preflight_uri": A12_PREFLIGHT_PATH.as_posix(),
        "preflight_sha256": None,
        "preflight_status": "not_started",
        "preflight_blockers": [],
        "preflight_launch_ready": False,
        "preflight_mlflow_registration_uri": "outputs/audits/armindex/a1.2-owner-local-preflight-mlflow-registration.json",
        "preflight_mlflow_registration_sha256": None,
        "v1_status": "not_started",
        "vast_preflight_v2": {
            "status": "not_started",
            "validated": False,
            "revision_id": "a1.2-local-vast-4x3090-v2",
            "receipt_uri": A12_V2_RECEIPT_PATH.as_posix(),
            "receipt_sha256": None,
            "contract_uri": (
                A12_V2_CONTROL_ROOT / "execution-contract.v2.json"
            ).as_posix(),
            "contract_sha256": None,
            "synthetic_receipt_uri": A12_V2_SYNTHETIC_RECEIPT_PATH.as_posix(),
            "synthetic_receipt_sha256": None,
            "runbook_uri": A12_V2_RUNBOOK_PATH.as_posix(),
            "runbook_sha256": None,
            "ledger_uri": A12_V2_LEDGER_PATH.as_posix(),
            "ledger_sha256": None,
            "budget_uri": A12_V2_BUDGET_PATH.as_posix(),
            "budget_sha256": None,
            "topology_uri": (
                A12_V2_CONTROL_ROOT / "topology-contract.v2.json"
            ).as_posix(),
            "topology_sha256": None,
            "runtime_lock_uri": (
                A12_V2_CONTROL_ROOT / "runtime-lock.v2.json"
            ).as_posix(),
            "runtime_lock_sha256": None,
            "image_contract_uri": (
                A12_V2_CONTROL_ROOT / "image-digest-contract.v2.json"
            ).as_posix(),
            "image_contract_sha256": None,
            "checklist_uri": (
                A12_V2_CONTROL_ROOT / "launch-checklist.v2.json"
            ).as_posix(),
            "checklist_sha256": None,
            "shutdown_uri": (A12_V2_CONTROL_ROOT / "shutdown-plan.v2.json").as_posix(),
            "shutdown_sha256": None,
            "allowlist_uri": A12_V2_ALLOWLIST_PATH.as_posix(),
            "allowlist_sha256": None,
            "owner_runbook_uri": A12_V2_OWNER_RUNBOOK_PATH.as_posix(),
            "owner_runbook_sha256": None,
            "coordinator_uri": A12_V2_COORDINATOR_PATH.as_posix(),
            "coordinator_sha256": None,
            "watchdog_uri": A12_V2_WATCHDOG_PATH.as_posix(),
            "watchdog_sha256": None,
            "closeout_validation_audit_uri": A12_V2_CLOSEOUT_AUDIT_PATH.as_posix(),
            "closeout_validation_audit_sha256": None,
            "closeout_validation_check_count": 0,
            "closeout_validation_recovery_count": 0,
            "closeout_validation_recoveries": [],
            "jobs": [],
            "launch_allowed": False,
            "adopted_for_execution": False,
            "live_check_count": 0,
            "synthetic_worker_count": 0,
            "planning_rate_usd": 0,
            "estimated_instance_hours": "unavailable",
            "estimated_raw_worker_usd": "unavailable",
            "estimated_instance_hours_min": 0,
            "estimated_instance_hours_max": 0,
            "estimated_raw_worker_usd_min": 0,
            "estimated_raw_worker_usd_max": 0,
            "real_counters": {
                "measured_runs": 0,
                "candidate_count": 0,
                "selection_accesses": 0,
                "final_accesses": 0,
            },
            "resource_counters": {
                "charged_usd": 0,
                "gpu_reservations": 0,
                "gpu_scientific_runs": 0,
                "model_downloads": 0,
                "paid_api_calls": 0,
            },
        },
        "vast_preflight_v3": {
            "status": "not_started",
            "validated": False,
            "revision_id": "a1.2-local-vast-4x3090-postcommit-v3",
            "receipt_uri": A12_V3_RECEIPT_PATH.as_posix(),
            "receipt_sha256": None,
            "receipt_self_sha256": None,
            "contract_uri": A12_V3_CONTRACT_PATH.as_posix(),
            "contract_sha256": None,
            "contract_self_sha256": None,
            "control_runbook_uri": A12_V3_CONTROL_RUNBOOK_PATH.as_posix(),
            "control_runbook_sha256": None,
            "owner_runbook_uri": A12_V3_OWNER_RUNBOOK_PATH.as_posix(),
            "owner_runbook_sha256": None,
            "schema_uri": A12_V3_SCHEMA_PATH.as_posix(),
            "schema_sha256": None,
            "module_uri": A12_V3_MODULE_PATH.as_posix(),
            "module_sha256": None,
            "v2_receipt_sha256": None,
            "planning_rate_usd": 0,
            "estimated_instance_hours": "unavailable",
            "estimated_raw_worker_usd": "unavailable",
            "common_screen_hard_stop_usd": 0,
            "a1_hard_stop_usd": 0,
            "campaign_hard_stop_usd": 0,
            "launch_allowed": False,
            "adopted_for_execution": False,
            "real_counters": {
                "measured_runs": 0,
                "candidate_count": 0,
                "selection_accesses": 0,
                "final_accesses": 0,
            },
            "resource_counters": {
                "charged_usd": 0,
                "gpu_reservations": 0,
                "gpu_scientific_runs": 0,
                "model_downloads": 0,
                "paid_api_calls": 0,
                "provider_switches": 0,
            },
            "claim_boundary": "postcommit_validator_not_prepared",
            "next_authorized_action": A1_2_SCAFFOLD_NEXT_AUTHORIZED_ACTION,
        },
        "vast_preflight_v5": {
            "status": "not_started",
            "validated": False,
            "revision_id": "a1.2-runtime-minimal-direct-base-v5",
            "receipt_uri": A12_V5_RECEIPT_PATH.as_posix(),
            "receipt_sha256": None,
            "contract_uri": A12_V5_CONTRACT_PATH.as_posix(),
            "contract_sha256": None,
            "runtime_lock_uri": A12_V5_RUNTIME_LOCK_PATH.as_posix(),
            "runtime_lock_sha256": None,
            "image_contract_uri": A12_V5_IMAGE_CONTRACT_PATH.as_posix(),
            "image_contract_sha256": None,
            "topology_uri": A12_V5_TOPOLOGY_PATH.as_posix(),
            "topology_sha256": None,
            "schema_uri": A12_V5_SCHEMA_PATH.as_posix(),
            "schema_sha256": None,
            "owner_runbook_uri": A12_V5_OWNER_RUNBOOK_PATH.as_posix(),
            "owner_runbook_sha256": None,
            "module_uri": A12_V5_MODULE_PATH.as_posix(),
            "module_sha256": None,
            "image_reference": None,
            "resolved_manifest_digest": None,
            "platform": None,
            "local_preparation_status": "not_started",
            "model_snapshots": "runtime_minimal_frozen",
            "cpu_model_load": "intentionally_skipped_due_host_memory",
            "dense_gpu_parity": "pending_live_vast_preflight",
            "qwen_measured_max_length": "pending_live_vast_preflight",
            "gpu_memory_feasibility": "pending_live_vast_preflight",
            "custom_local_docker_build": False,
            "launch_allowed": False,
            "adopted_for_execution": False,
            "live_checks_pending": [],
            "removed_active_steps": [],
            "upload_artifacts": [],
            "real_counters": {
                "measured_runs": 0,
                "candidate_count": 0,
                "selection_accesses": 0,
                "final_accesses": 0,
            },
            "resource_counters": {
                "charged_usd": 0,
                "gpu_reservations": 0,
                "gpu_scientific_runs": 0,
                "model_downloads": 0,
                "paid_api_calls": 0,
                "provider_switches": 0,
            },
            "claim_boundary": "direct_base_revision_not_prepared",
            "next_authorized_action": A1_2_SCAFFOLD_NEXT_AUTHORIZED_ACTION,
        },
        "vast_preflight_v6": {
            "status": "not_started",
            "validated": False,
            "revision_id": A12_V6_REVISION_ID,
            "receipt_uri": A12_V6_RECEIPT_PATH.as_posix(),
            "receipt_sha256": None,
            "receipt_self_sha256": None,
            "contract_uri": A12_V6_CONTRACT_PATH.as_posix(),
            "contract_sha256": None,
            "contract_self_sha256": None,
            "schema_uri": A12_V6_SCHEMA_PATH.as_posix(),
            "schema_sha256": None,
            "validator_uri": A12_V6_MODULE_PATH.as_posix(),
            "validator_sha256": None,
            "preflight_module_uri": A12_V6_PREFLIGHT_MODULE_PATH.as_posix(),
            "preflight_module_sha256": None,
            "owner_runbook_uri": A12_V6_OWNER_RUNBOOK_PATH.as_posix(),
            "owner_runbook_sha256": None,
            "continuation_policy": {
                "status": "not_started",
                "validated": False,
                "policy_uri": A12_V6_CONTINUATION_POLICY_PATH.as_posix(),
                "policy_sha256": None,
                "default_post_preflight_instruction": "destroy_and_verify_provider_instance_absent",
                "allowed_post_preflight_instruction": "continue_next_goal_on_PLAN",
                "continuation_authorized_now": False,
                "continuation_requires": [],
                "fallback_to_destroy_if": [],
            },
            "image_reference": None,
            "resolved_manifest_digest": None,
            "platform": None,
            "live_quote_usd_per_hour": 0,
            "estimated_preflight_usd": {},
            "budget_hard_stops_usd": {},
            "observed_live_defects": [],
            "corrections": {},
            "launch_allowed": False,
            "adopted_for_execution": False,
            "synthetic_preflight_only": True,
            "real_counters": {
                "measured_runs": 0,
                "candidate_count": 0,
                "selection_accesses": 0,
                "final_accesses": 0,
            },
            "resource_counters": {
                "charged_usd": 0,
                "gpu_reservations": 0,
                "gpu_scientific_runs": 0,
                "model_downloads": 0,
                "paid_api_calls": 0,
                "provider_switches": 0,
            },
            "claim_boundary": "live_preflight_correction_not_prepared",
            "next_authorized_action": A1_2_SCAFFOLD_NEXT_AUTHORIZED_ACTION,
        },
        "vast_preflight_v7": {
            "status": "not_started",
            "validated": False,
            "revision_id": A12_V7_REVISION_ID,
            "receipt_uri": A12_V7_RECEIPT_PATH.as_posix(),
            "receipt_sha256": None,
            "receipt_self_sha256": None,
            "contract_uri": A12_V7_CONTRACT_PATH.as_posix(),
            "contract_sha256": None,
            "contract_self_sha256": None,
            "schema_uri": A12_V7_SCHEMA_PATH.as_posix(),
            "schema_sha256": None,
            "validator_uri": A12_V7_MODULE_PATH.as_posix(),
            "validator_sha256": None,
            "owner_runbook_uri": A12_V7_OWNER_RUNBOOK_PATH.as_posix(),
            "owner_runbook_sha256": None,
            "coordinator_uri": A12_V7_COORDINATOR_PATH.as_posix(),
            "coordinator_sha256": None,
            "bootstrap_uri": A12_V7_BOOTSTRAP_PATH.as_posix(),
            "bootstrap_sha256": None,
            "supplement_validator_uri": A12_V7_SUPPLEMENT_VALIDATOR_PATH.as_posix(),
            "supplement_validator_sha256": None,
            "supplement_requirements_uri": A12_V7_SUPPLEMENT_REQUIREMENTS_PATH.as_posix(),
            "supplement_requirements_sha256": None,
            "supplement_workflow_uri": A12_V7_SUPPLEMENT_WORKFLOW_PATH.as_posix(),
            "supplement_workflow_sha256": None,
            "continuation_policy": {
                "status": "not_started",
                "validated": False,
                "policy_uri": A12_V6_CONTINUATION_POLICY_PATH.as_posix(),
                "policy_sha256": None,
                "default_post_preflight_instruction": "destroy_and_verify_provider_instance_absent",
                "allowed_post_preflight_instruction": "continue_next_goal_on_PLAN",
                "continuation_authorized_now": False,
                "continuation_requires": [],
                "fallback_to_destroy_if": [],
            },
            "image_reference": None,
            "resolved_manifest_digest": None,
            "platform": None,
            "preserved_live_failures": [],
            "active_correction": {},
            "launch_allowed": False,
            "adopted_for_execution": False,
            "synthetic_preflight_only": True,
            "real_counters": {
                "measured_runs": 0,
                "candidate_count": 0,
                "selection_accesses": 0,
                "final_accesses": 0,
            },
            "resource_counters": {
                "charged_usd": 0,
                "gpu_reservations": 0,
                "gpu_scientific_runs": 0,
                "model_downloads": 0,
                "paid_api_calls": 0,
                "provider_switches": 0,
            },
            "claim_boundary": "same_instance_repair_not_prepared",
            "next_authorized_action": A1_2_SCAFFOLD_NEXT_AUTHORIZED_ACTION,
        },
        "vast_preflight_v8": {
            "status": "not_started",
            "validated": False,
            "revision_id": A12_V8_REVISION_ID,
            "receipt_uri": A12_V8_RECEIPT_PATH.as_posix(),
            "receipt_sha256": None,
            "receipt_self_sha256": None,
            "contract_uri": A12_V8_CONTRACT_PATH.as_posix(),
            "contract_sha256": None,
            "contract_self_sha256": None,
            "schema_uri": A12_V8_SCHEMA_PATH.as_posix(),
            "schema_sha256": None,
            "validator_uri": A12_V8_MODULE_PATH.as_posix(),
            "validator_sha256": None,
            "owner_runbook_uri": A12_V8_OWNER_RUNBOOK_PATH.as_posix(),
            "owner_runbook_sha256": None,
            "coordinator_uri": A12_V8_COORDINATOR_PATH.as_posix(),
            "coordinator_sha256": None,
            "bootstrap_uri": A12_V8_BOOTSTRAP_PATH.as_posix(),
            "bootstrap_sha256": None,
            "image_reference": None,
            "resolved_manifest_digest": None,
            "platform": None,
            "preserved_live_failures": [],
            "active_correction": {},
            "launch_allowed": False,
            "adopted_for_execution": False,
            "synthetic_preflight_only": True,
            "real_counters": {
                "measured_runs": 0,
                "candidate_count": 0,
                "selection_accesses": 0,
                "final_accesses": 0,
            },
            "resource_counters": {
                "charged_usd": 0,
                "gpu_reservations": 0,
                "gpu_scientific_runs": 0,
                "model_downloads": 0,
                "paid_api_calls": 0,
                "provider_switches": 0,
            },
            "claim_boundary": "validation_complete_bundle_repair_not_prepared",
            "next_authorized_action": A1_2_SCAFFOLD_NEXT_AUTHORIZED_ACTION,
        },
        "vast_preflight_v9": {
            "status": "not_started",
            "validated": False,
            "revision_id": A12_V9_REVISION_ID,
            "receipt_uri": A12_V9_RECEIPT_PATH.as_posix(),
            "receipt_sha256": None,
            "receipt_self_sha256": None,
            "contract_uri": A12_V9_CONTRACT_PATH.as_posix(),
            "contract_sha256": None,
            "contract_self_sha256": None,
            "schema_uri": A12_V9_SCHEMA_PATH.as_posix(),
            "schema_sha256": None,
            "validator_uri": A12_V9_MODULE_PATH.as_posix(),
            "validator_sha256": None,
            "runtime_uri": A12_V9_RUNTIME_PATH.as_posix(),
            "runtime_sha256": None,
            "owner_runbook_uri": A12_V9_OWNER_RUNBOOK_PATH.as_posix(),
            "owner_runbook_sha256": None,
            "coordinator_uri": A12_V9_COORDINATOR_PATH.as_posix(),
            "coordinator_sha256": None,
            "bootstrap_uri": A12_V9_BOOTSTRAP_PATH.as_posix(),
            "bootstrap_sha256": None,
            "launcher_uri": A12_V9_LAUNCHER_PATH.as_posix(),
            "launcher_sha256": None,
            "live_result_uri": A12_V9_RESULT_RECEIPT_PATH.as_posix(),
            "live_result_sha256": None,
            "live_result_self_sha256": None,
            "live_result_revision_id": A12_V9_RESULT_REVISION_ID,
            "live_result_status": "not_started",
            "live_result": {},
            "active_correction": {},
            "launch_allowed": False,
            "adopted_for_execution": False,
            "synthetic_preflight_only": True,
            "real_counters": {
                "measured_runs": 0,
                "candidate_count": 0,
                "selection_accesses": 0,
                "final_accesses": 0,
            },
            "resource_counters": {
                "charged_usd": 0,
                "gpu_reservations": 0,
                "gpu_scientific_runs": 0,
                "model_downloads": 0,
                "paid_api_calls": 0,
                "provider_switches": 0,
            },
            "claim_boundary": "execution_lifecycle_repair_not_prepared",
            "next_authorized_action": A1_2_SCAFFOLD_NEXT_AUTHORIZED_ACTION,
        },
        "provider_closeout_v10": {
            "status": "not_started",
            "validated": False,
            "revision_id": A12_V10_CLOSEOUT_REVISION_ID,
            "receipt_uri": A12_V10_CLOSEOUT_RECEIPT_PATH.as_posix(),
            "receipt_sha256": None,
            "receipt_self_sha256": None,
            "schema_uri": A12_V10_CLOSEOUT_SCHEMA_PATH.as_posix(),
            "schema_sha256": None,
            "validator_uri": A12_V10_CLOSEOUT_MODULE_PATH.as_posix(),
            "validator_sha256": None,
            "predecessor": {},
            "owner_evidence": {},
            "provider_closeout": {},
            "pending_provider_checks": [],
            "launch_allowed": False,
            "adopted_for_execution": False,
            "measured_runs": 0,
            "selection_accesses": 0,
            "final_accesses": 0,
            "charged_usd": 0,
            "claim_boundary": "provider_closeout_not_recorded",
            "next_authorized_action": A1_2_SCAFFOLD_NEXT_AUTHORIZED_ACTION,
        },
        "scientific_execution_request_v11": {
            "status": "not_started",
            "validated": False,
            "revision_id": A12_V11_REVISION_ID,
            "receipt_uri": A12_V11_RECEIPT_PATH.as_posix(),
            "receipt_sha256": None,
            "receipt_self_sha256": None,
            "request_uri": A12_V11_REQUEST_PATH.as_posix(),
            "request_sha256": None,
            "request_self_sha256": None,
            "request_schema_uri": A12_V11_REQUEST_SCHEMA_PATH.as_posix(),
            "request_schema_sha256": None,
            "receipt_schema_uri": A12_V11_RECEIPT_SCHEMA_PATH.as_posix(),
            "receipt_schema_sha256": None,
            "validator_uri": A12_V11_MODULE_PATH.as_posix(),
            "validator_sha256": None,
            "runbook_uri": A12_V11_RUNBOOK_PATH.as_posix(),
            "runbook_sha256": None,
            "ledger_uri": A12_V11_LEDGER_PATH.as_posix(),
            "ledger_sha256": None,
            "rigor_review_uri": A12_V11_RIGOR_REVIEW_PATH.as_posix(),
            "rigor_review_sha256": None,
            "component_bindings": {},
            "jobs": [],
            "pending_adoption_requirements": [],
            "authorization": {},
            "counters": {},
            "budget_hard_stops": {},
            "workload_manifests": 0,
            "expected_program_arm_runs": 0,
            "expected_physical_program_view_paths": 0,
            "rep_dev_query_count": 0,
            "harness_dev_reserved_count": 0,
            "launch_allowed": False,
            "adopted_for_execution": False,
            "claim_boundary": "scientific_request_not_prepared",
            "next_authorized_action": A1_2_SCAFFOLD_NEXT_AUTHORIZED_ACTION,
        },
        "adoption_inputs_v12_r3": {
            "status": "not_started",
            "validated": False,
            "revision_id": A12_V12_R3_REVISION_ID,
            "contract_uri": A12_V12_R3_CONTRACT_PATH.as_posix(),
            "contract_sha256": None,
            "contract_self_sha256": None,
            "contract_schema_uri": A12_V12_R3_CONTRACT_SCHEMA_PATH.as_posix(),
            "contract_schema_sha256": None,
            "validator_uri": "src/myis_research/armindex/a1_2_scientific_execution_adoption_inputs_v12_r3.py",
            "validator_sha256": None,
            "publication_impact": {},
            "instance_disposition": {},
            "pending_live_provider": [],
            "authorization": {},
            "counters": {},
            "claim_boundary": "local_adoption_inputs_not_prepared",
        },
    }
    try:
        validation = validate_a1_2_scaffold(root)
        contract_path = root / A12_CONTROL_ROOT / "execution-contract.v1.json"
        budget_path = root / "control/budgets/a1.2-common-screen-v1.json"
        lockset_path = root / A12_CONTROL_ROOT / "model-lockset.v1.json"
        checklist_path = root / A12_CONTROL_ROOT / "launch-checklist.v1.json"
        receipt_path = root / A12_RECEIPT_PATH
        closeout_audit_path = root / A12_CLOSEOUT_VALIDATION_AUDIT_PATH
        preflight_path = root / A12_PREFLIGHT_PATH
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        budget = json.loads(budget_path.read_text(encoding="utf-8"))
        lockset = json.loads(lockset_path.read_text(encoding="utf-8"))
        checklist = json.loads(checklist_path.read_text(encoding="utf-8"))
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        closeout_audit = json.loads(closeout_audit_path.read_text(encoding="utf-8"))
        preflight = (
            json.loads(preflight_path.read_text(encoding="utf-8"))
            if preflight_path.is_file()
            else None
        )
        v2_receipt = None
        v2_contract = None
        v2_budget = None
        v2_topology = None
        v2_checklist = None
        v2_synthetic = None
        v2_closeout_audit = None
        v3_validation = None
        v3_receipt = None
        v3_contract = None
        v5_validation = None
        v5_receipt = None
        v5_contract = None
        v6_validation = None
        v6_receipt = None
        v6_contract = None
        continuation_policy = None
        v7_validation = None
        v7_receipt = None
        v7_contract = None
        v8_validation = None
        v8_receipt = None
        v8_contract = None
        v9_validation = None
        v9_receipt = None
        v9_contract = None
        v9_result_validation = None
        v9_result_receipt = None
        v10_closeout_validation = None
        v10_closeout_receipt = None
        v11_request_validation = None
        v11_request = None
        v11_request_receipt = None
        v11_budget = None
        v12_r3_contract = None
        v13_publication_validation = None
        v13_disposition_status = None
        if (root / A12_V2_RECEIPT_PATH).is_file():
            v2_receipt = validate_a1_2_vast_receipt(root)
            v2_contract = json.loads(
                (root / A12_V2_CONTROL_ROOT / "execution-contract.v2.json").read_text(
                    encoding="utf-8"
                )
            )
            v2_budget = json.loads(
                (root / A12_V2_BUDGET_PATH).read_text(encoding="utf-8")
            )
            v2_topology = json.loads(
                (root / A12_V2_CONTROL_ROOT / "topology-contract.v2.json").read_text(
                    encoding="utf-8"
                )
            )
            v2_checklist = json.loads(
                (root / A12_V2_CONTROL_ROOT / "launch-checklist.v2.json").read_text(
                    encoding="utf-8"
                )
            )
            v2_synthetic = json.loads(
                (root / A12_V2_SYNTHETIC_RECEIPT_PATH).read_text(encoding="utf-8")
            )
            if (root / A12_V2_CLOSEOUT_AUDIT_PATH).is_file():
                v2_closeout_audit = json.loads(
                    (root / A12_V2_CLOSEOUT_AUDIT_PATH).read_text(encoding="utf-8")
                )
        if (root / A12_V3_RECEIPT_PATH).is_file():
            v3_validation = validate_a1_2_vast_postcommit(root, require_clean=False)
            v3_receipt = json.loads(
                (root / A12_V3_RECEIPT_PATH).read_text(encoding="utf-8")
            )
            v3_contract = json.loads(
                (root / A12_V3_CONTRACT_PATH).read_text(encoding="utf-8")
            )
        if (root / A12_V5_RECEIPT_PATH).is_file():
            v5_validation = validate_a1_2_v5_direct_base(root)
            v5_receipt = json.loads(
                (root / A12_V5_RECEIPT_PATH).read_text(encoding="utf-8")
            )
            v5_contract = json.loads(
                (root / A12_V5_CONTRACT_PATH).read_text(encoding="utf-8")
            )
        if (root / A12_V6_RECEIPT_PATH).is_file():
            v6_validation = validate_a1_2_v6_live_revision(root)
            v6_receipt = json.loads(
                (root / A12_V6_RECEIPT_PATH).read_text(encoding="utf-8")
            )
            v6_contract = json.loads(
                (root / A12_V6_CONTRACT_PATH).read_text(encoding="utf-8")
            )
            continuation_policy = json.loads(
                (root / A12_V6_CONTINUATION_POLICY_PATH).read_text(encoding="utf-8")
            )
        if (root / A12_V7_RECEIPT_PATH).is_file():
            v7_validation = validate_a1_2_v7_live_repair(root)
            v7_receipt = json.loads(
                (root / A12_V7_RECEIPT_PATH).read_text(encoding="utf-8")
            )
            v7_contract = json.loads(
                (root / A12_V7_CONTRACT_PATH).read_text(encoding="utf-8")
            )
        if (root / A12_V8_RECEIPT_PATH).is_file():
            v8_validation = validate_a1_2_v8_packaging_repair(root)
            v8_receipt = json.loads(
                (root / A12_V8_RECEIPT_PATH).read_text(encoding="utf-8")
            )
            v8_contract = json.loads(
                (root / A12_V8_CONTRACT_PATH).read_text(encoding="utf-8")
            )
        if (root / A12_V9_RECEIPT_PATH).is_file():
            v9_validation = validate_a1_2_v9_execution_lifecycle(root)
            v9_receipt = json.loads(
                (root / A12_V9_RECEIPT_PATH).read_text(encoding="utf-8")
            )
            v9_contract = json.loads(
                (root / A12_V9_CONTRACT_PATH).read_text(encoding="utf-8")
            )
        if (root / A12_V9_RESULT_RECEIPT_PATH).is_file():
            v9_result_validation = validate_a1_2_v9_live_result(root)
            v9_result_receipt = json.loads(
                (root / A12_V9_RESULT_RECEIPT_PATH).read_text(encoding="utf-8")
            )
        if (root / A12_V10_CLOSEOUT_RECEIPT_PATH).is_file():
            v10_closeout_validation = validate_a1_2_v10_provider_closeout(root)
            v10_closeout_receipt = json.loads(
                (root / A12_V10_CLOSEOUT_RECEIPT_PATH).read_text(encoding="utf-8")
            )
        if (root / A12_V11_RECEIPT_PATH).is_file():
            v11_request_validation = validate_a1_2_v11_scientific_request(root)
            v11_request = json.loads(
                (root / A12_V11_REQUEST_PATH).read_text(encoding="utf-8")
            )
            v11_request_receipt = json.loads(
                (root / A12_V11_RECEIPT_PATH).read_text(encoding="utf-8")
            )
            v11_budget = json.loads(
                (root / A12_V11_BUDGET_PATH).read_text(encoding="utf-8")
            )
        if (root / A12_V12_R3_CONTRACT_PATH).is_file():
            v12_r3_contract = validate_a1_2_v12_r3_adoption_inputs(root)
            v13_publication_validation = validate_a1_2_v13_publication_impact(root)
            v13_disposition_status = current_a1_2_v13_disposition_status(root)
        assert_aggregate_only(contract)
        assert_aggregate_only(budget)
        assert_aggregate_only(lockset)
        assert_aggregate_only(checklist)
        assert_aggregate_only(receipt)
        assert_aggregate_only(closeout_audit)
        for value in (
            v2_receipt,
            v2_contract,
            v2_budget,
            v2_topology,
            v2_checklist,
            v2_synthetic,
            v2_closeout_audit,
            v3_receipt,
            v3_contract,
            v5_receipt,
            v5_contract,
            v6_receipt,
            v6_contract,
            continuation_policy,
            v7_receipt,
            v7_contract,
            v8_receipt,
            v8_contract,
            v9_receipt,
            v9_contract,
            v9_result_receipt,
            v10_closeout_receipt,
            v11_request,
            v11_request_receipt,
            v11_budget,
            v12_r3_contract,
        ):
            if value is not None:
                assert_aggregate_only(value)
        if v2_receipt is not None and (
            v2_receipt.get("status")
            != "offline_preparation_complete_live_owner_preflight_pending"
            or v2_receipt.get("launch_allowed") is not False
            or v2_receipt.get("adopted_for_execution") is not False
            or v2_synthetic is None
            or v2_synthetic.get("status") != "PASS"
            or v2_synthetic.get("worker_count") != 4
            or any(
                int(value) != 0
                for value in v2_receipt.get("real_counters", {}).values()
            )
            or any(
                float(value) != 0
                for value in v2_receipt.get("resource_counters", {}).values()
            )
        ):
            raise ValueError("A1.2 Vast v2 preparation receipt is invalid")
        if v3_receipt is not None and (
            v3_validation is None
            or v3_validation.get("status") != "prepared_postcommit_launch_locked"
            or v3_receipt.get("status")
            != "postcommit_validator_prepared_live_owner_preflight_pending"
            or v3_receipt.get("launch_allowed") is not False
            or v3_receipt.get("adopted_for_execution") is not False
            or v3_contract is None
            or v3_contract.get("launch_allowed") is not False
            or v3_contract.get("adopted_for_execution") is not False
            or any(
                int(value) != 0
                for value in v3_receipt.get("real_counters", {}).values()
            )
            or any(
                float(value) != 0
                for value in v3_receipt.get("resource_counters", {}).values()
            )
        ):
            raise ValueError("A1.2 Vast v3 post-commit correction receipt is invalid")
        if v5_receipt is not None and (
            v5_validation is None
            or v5_validation.get("status") != "direct_base_prepared_launch_locked"
            or v5_receipt.get("status")
            != "direct_base_preflight_prepared_local_owner_stage_pending"
            or v5_receipt.get("launch_allowed") is not False
            or v5_receipt.get("adopted_for_execution") is not False
            or v5_contract is None
            or v5_contract.get("launch_allowed") is not False
            or v5_contract.get("adopted_for_execution") is not False
            or any(
                int(value) != 0
                for value in v5_receipt.get("real_counters", {}).values()
            )
            or any(
                float(value) != 0
                for value in v5_receipt.get("resource_counters", {}).values()
            )
        ):
            raise ValueError("A1.2 direct-base v5 receipt is invalid")
        if v6_receipt is not None and (
            v6_validation is None
            or v6_validation.get("status")
            != "live_correction_prepared_preflight_pending"
            or v6_receipt.get("status") != "live_correction_prepared_preflight_pending"
            or v6_receipt.get("evidence_class")
            != "live_engineering_preflight_correction"
            or v6_receipt.get("scientific_authority") is not False
            or v6_receipt.get("launch_allowed") is not False
            or v6_receipt.get("adopted_for_execution") is not False
            or v6_contract is None
            or v6_contract.get("contract_id") != A12_V6_REVISION_ID
            or v6_contract.get("status") != "live_correction_prepared_preflight_pending"
            or v6_contract.get("synthetic_preflight_only") is not True
            or v6_contract.get("measured_retrieval_allowed") is not False
            or v6_contract.get("launch_allowed") is not False
            or v6_contract.get("adopted_for_execution") is not False
            or any(
                int(v6_receipt.get(key, -1)) != 0
                for key in ("measured_runs", "selection_accesses", "final_accesses")
            )
            or not isinstance(continuation_policy, Mapping)
            or continuation_policy.get("schema_version")
            != "myis.armindex-a1.2-owner-instance-continuation-policy.v1"
            or continuation_policy.get("policy_id")
            != "a1.2-owner-instance-continuation-v1"
            or continuation_policy.get("status") != "active_owner_policy"
            or continuation_policy.get("decision_kind") != "owner_change_policy"
            or continuation_policy.get("evidence_class")
            != "owner_policy_for_engineering_continuity"
            or continuation_policy.get("launch_allowed") is not False
            or continuation_policy.get("default_post_preflight_instruction")
            != "destroy_and_verify_provider_instance_absent"
            or continuation_policy.get("allowed_post_preflight_instruction")
            != "continue_next_goal_on_PLAN"
            or not isinstance(continuation_policy.get("continuation_requires"), list)
            or not continuation_policy.get("continuation_requires")
            or not isinstance(continuation_policy.get("fallback_to_destroy_if"), list)
            or not continuation_policy.get("fallback_to_destroy_if")
            or not isinstance(continuation_policy.get("measured_counters"), Mapping)
            or any(
                int(value) != 0
                for value in continuation_policy["measured_counters"].values()
            )
        ):
            raise ValueError(
                "A1.2 live-preflight correction v6 or continuation policy is invalid"
            )
        if v7_receipt is not None and (
            v7_validation is None
            or v7_validation.get("status")
            != "same_instance_repair_prepared_preflight_pending"
            or v7_receipt.get("status")
            != "same_instance_repair_prepared_preflight_pending"
            or v7_receipt.get("evidence_class") != "live_engineering_preflight_repair"
            or v7_receipt.get("scientific_authority") is not False
            or v7_receipt.get("launch_allowed") is not False
            or v7_receipt.get("adopted_for_execution") is not False
            or v7_receipt.get("pythondontwritebytecode") is not True
            or any(
                int(v7_receipt.get(key, -1)) != 0
                for key in ("measured_runs", "selection_accesses", "final_accesses")
            )
            or v7_contract is None
            or v7_contract.get("contract_id") != A12_V7_REVISION_ID
            or v7_contract.get("status")
            != "same_instance_repair_prepared_preflight_pending"
            or v7_contract.get("evidence_class") != "live_engineering_preflight_repair"
            or v7_contract.get("scientific_authority") is not False
            or v7_contract.get("synthetic_preflight_only") is not True
            or v7_contract.get("measured_retrieval_allowed") is not False
            or v7_contract.get("launch_allowed") is not False
            or v7_contract.get("adopted_for_execution") is not False
            or v6_receipt is None
            or v7_receipt.get("v6_receipt_sha256") != v6_receipt.get("receipt_sha256")
            or not isinstance(v7_contract.get("preserved_live_failures"), list)
            or len(v7_contract["preserved_live_failures"]) != 2
            or v7_receipt.get("preserved_live_failure_ids")
            != [
                item.get("failure_id")
                for item in v7_contract["preserved_live_failures"]
            ]
            or not isinstance(v7_contract.get("active_correction"), Mapping)
            or v7_contract["active_correction"].get("fresh_root_required") is not True
            or v7_contract["active_correction"].get("same_instance_reuse") is not True
            or v7_contract["active_correction"].get("required_environment")
            != {"PYTHONDONTWRITEBYTECODE": "1"}
            or any(
                int(value) != 0
                for value in v7_contract.get("real_counters", {}).values()
            )
            or any(
                int(value) != 0
                for value in v7_contract.get("resource_counters", {}).values()
            )
        ):
            raise ValueError("A1.2 same-instance repair v7 receipt is invalid")
        if v8_receipt is not None and (
            v8_validation is None
            or v8_validation.get("status")
            != "validation_complete_bundle_repair_prepared_preflight_pending"
            or v8_receipt.get("status")
            != "validation_complete_bundle_repair_prepared_preflight_pending"
            or v8_receipt.get("evidence_class")
            != "live_engineering_preflight_packaging_repair"
            or v8_receipt.get("scientific_authority") is not False
            or v8_receipt.get("launch_allowed") is not False
            or v8_receipt.get("adopted_for_execution") is not False
            or any(
                int(v8_receipt.get(key, -1)) != 0
                for key in ("measured_runs", "selection_accesses", "final_accesses")
            )
            or v8_contract is None
            or v8_contract.get("contract_id") != A12_V8_REVISION_ID
            or v8_contract.get("status")
            != "validation_complete_bundle_repair_prepared_preflight_pending"
            or v8_contract.get("evidence_class")
            != "live_engineering_preflight_packaging_repair"
            or v8_contract.get("scientific_authority") is not False
            or v8_contract.get("synthetic_preflight_only") is not True
            or v8_contract.get("measured_retrieval_allowed") is not False
            or v8_contract.get("launch_allowed") is not False
            or v8_contract.get("adopted_for_execution") is not False
            or v7_receipt is None
            or v8_receipt.get("v7_receipt_sha256")
            != _file_sha256(root / A12_V7_RECEIPT_PATH)
            or v8_contract.get("migration_from", {}).get("sha256")
            != _file_sha256(root / A12_V7_RECEIPT_PATH)
            or v8_receipt.get("preserved_live_failure_ids")
            != v8_contract.get("preserved_live_failures")
            or v8_contract.get("preserved_live_failures")
            != [
                "v6-initial-wheelhouse-missing-pydantic",
                "v6-supplement-repair-mutated-pycache-tree",
                "v7-frozen-bundle-missing-validation-lineage",
            ]
            or not isinstance(v8_contract.get("active_correction"), Mapping)
            or v8_contract["active_correction"].get("fresh_remote_root")
            != "/opt/myis/a1.2-v8"
            or v8_contract["active_correction"].get("source_remote_root")
            != "/opt/myis/a1.2-v7"
            or v8_contract["active_correction"].get("same_instance_reuse") is not True
            or v8_contract["active_correction"].get("validation_lineage_complete")
            is not True
            or v8_contract["active_correction"].get("pythondontwritebytecode")
            is not True
            or any(
                int(value) != 0
                for value in v8_contract.get("real_counters", {}).values()
            )
            or any(
                int(value) != 0
                for value in v8_contract.get("resource_counters", {}).values()
            )
        ):
            raise ValueError(
                "A1.2 validation-complete bundle repair v8 receipt is invalid"
            )
        if v9_receipt is not None and (
            v9_validation is None
            or v9_validation.get("status")
            != "execution_lifecycle_repair_prepared_preflight_pending"
            or v9_receipt.get("status")
            != "execution_lifecycle_repair_prepared_preflight_pending"
            or v9_receipt.get("evidence_class")
            != "live_engineering_preflight_execution_lifecycle_repair"
            or v9_receipt.get("scientific_authority") is not False
            or v9_receipt.get("launch_allowed") is not False
            or v9_receipt.get("adopted_for_execution") is not False
            or v9_receipt.get("implementation_validation_complete") is not True
            or v9_receipt.get("live_preflight_execution_pending") is not True
            or any(
                int(v9_receipt.get(key, -1)) != 0
                for key in ("measured_runs", "selection_accesses", "final_accesses")
            )
            or float(v9_receipt.get("charged_usd", -1)) != 0
            or v9_contract is None
            or v9_contract.get("contract_id") != A12_V9_REVISION_ID
            or v9_contract.get("status")
            != "execution_lifecycle_repair_prepared_preflight_pending"
            or v9_contract.get("evidence_class")
            != "live_engineering_preflight_execution_lifecycle_repair"
            or v9_contract.get("scientific_authority") is not False
            or v9_contract.get("synthetic_preflight_only") is not True
            or v9_contract.get("measured_retrieval_allowed") is not False
            or v9_contract.get("launch_allowed") is not False
            or v9_contract.get("adopted_for_execution") is not False
            or v8_receipt is None
            or v9_receipt.get("v8_receipt_sha256") != v8_receipt.get("receipt_sha256")
            or v9_contract.get("migration_from", {}).get("sha256")
            != v8_receipt.get("receipt_sha256")
            or not isinstance(v9_contract.get("active_correction"), Mapping)
            or v9_contract["active_correction"].get("fresh_remote_root")
            != "/opt/myis/a1.2-v9"
            or v9_contract["active_correction"].get("source_remote_root")
            != "/opt/myis/a1.2-v7"
            or v9_contract["active_correction"].get("same_instance_reuse") is not True
            or v9_contract["active_correction"].get(
                "implementation_validation_complete"
            )
            is not True
            or v9_contract["active_correction"].get("live_preflight_execution_pending")
            is not True
            or any(
                int(value) != 0
                for value in v9_contract.get("real_counters", {}).values()
            )
            or any(
                float(value) != 0
                for value in v9_contract.get("resource_counters", {}).values()
            )
        ):
            raise ValueError("A1.2 execution-lifecycle repair v9 receipt is invalid")
        if v9_result_receipt is not None and (
            v9_result_validation is None
            or v9_result_receipt.get("status") != "PASS"
            or v9_result_receipt.get("scientific_authority") is not False
            or v9_result_receipt.get("launch_allowed") is not False
            or v9_result_receipt.get("adopted_for_execution") is not False
            or any(
                int(v9_result_receipt.get(key, -1)) != 0
                for key in ("measured_runs", "selection_accesses", "final_accesses")
            )
            or float(v9_result_receipt.get("charged_usd", -1)) != 0
            or v9_result_receipt.get("attempt_id") != "a12-v9-20260807-06"
            or not isinstance(v9_result_receipt.get("arms"), list)
            or len(v9_result_receipt["arms"]) != 4
            or any(item.get("status") != "PASS" for item in v9_result_receipt["arms"])
            or v9_result_receipt.get("qwen", {}).get(
                "measured_adapter_max_input_tokens"
            )
            != 32768
            or v9_result_receipt.get("lifecycle", {}).get("checkpoint_resume") != "PASS"
            or v9_result_receipt.get("lifecycle", {}).get("guest_process_teardown")
            != "PASS"
        ):
            raise ValueError("A1.2 live synthetic preflight result receipt is invalid")
        if v10_closeout_receipt is not None and (
            v10_closeout_validation is None
            or v9_result_receipt is None
            or v10_closeout_receipt.get("status") != "PASS"
            or v10_closeout_receipt.get("scientific_authority") is not False
            or v10_closeout_receipt.get("launch_allowed") is not False
            or v10_closeout_receipt.get("adopted_for_execution") is not False
            or any(
                int(v10_closeout_receipt.get(key, -1)) != 0
                for key in ("measured_runs", "selection_accesses", "final_accesses")
            )
            or float(v10_closeout_receipt.get("charged_usd", -1)) != 0
            or v10_closeout_receipt.get("predecessor", {}).get("receipt_self_sha256")
            != v9_result_receipt.get("receipt_sha256")
            or v10_closeout_receipt.get("provider_closeout", {}).get(
                "owner_disposition"
            )
            != "destroyed_and_provider_absence_verified"
            or v10_closeout_receipt.get("provider_closeout", {}).get(
                "provider_destruction_proven"
            )
            is not True
            or v10_closeout_receipt.get("provider_closeout", {}).get(
                "provider_instance_absent_verified"
            )
            is not True
            or v10_closeout_receipt.get("pending_provider_checks") != []
        ):
            raise ValueError("A1.2 provider closeout v10 receipt is invalid")
        if v11_request_receipt is not None and (
            v11_request_validation is None
            or v10_closeout_receipt is None
            or v11_request is None
            or v11_budget is None
            or v11_request_validation.get("status") != "PASS"
            or v11_request_receipt.get("status") != "PASS"
            or v11_request_receipt.get("scientific_authority") is not False
            or v11_request_receipt.get("launch_allowed") is not False
            or v11_request_receipt.get("adopted_for_execution") is not False
            or any(
                int(v11_request_receipt.get(key, -1)) != 0
                for key in ("measured_runs", "selection_accesses", "final_accesses")
            )
            or float(v11_request_receipt.get("charged_usd", -1)) != 0
            or v11_request.get("status") != "prepared_for_owner_review_not_adopted"
            or v11_request.get("scientific_authority") is not False
            or any(
                bool(value) for value in v11_request.get("authorization", {}).values()
            )
            or any(
                float(value) != 0 for value in v11_request.get("counters", {}).values()
            )
            or v11_request.get("predecessor_lineage", [])[-1].get("embedded_sha256")
            != v10_closeout_receipt.get("receipt_sha256")
            or v11_budget.get("launch_allowed") is not False
            or v11_budget.get("adopted_for_execution") is not False
        ):
            raise ValueError("A1.2 scientific execution request v11 is invalid")
        if v12_r3_contract is not None and (
            v11_request_receipt is None
            or v13_publication_validation is None
            or v13_disposition_status is None
            or v12_r3_contract.get("status")
            != "LOCAL_PREPARATION_HARDENED_PENDING_OWNER_LOCAL_AND_LIVE_PROVIDER"
            or v12_r3_contract.get("scientific_authority") is not False
            or any(
                bool(value)
                for value in v12_r3_contract.get("authorization", {}).values()
            )
            or any(
                float(value) != 0
                for value in v12_r3_contract.get("counters", {}).values()
            )
            or v12_r3_contract.get("pending_live_provider")
            != [
                "fresh_provider_identity",
                "fresh_all_fee_quote",
                "whole_workload_live_budget_admission",
                "live_provider_admission_receipt",
            ]
            or v13_publication_validation.get("status") != "PASS"
            or v13_publication_validation.get("primary_outcome") != "out_recall_at_100"
            or v13_publication_validation.get("launch_allowed") is not False
            or v13_disposition_status.get("status") != "PENDING_LIVE_PROVIDER"
            or v13_disposition_status.get("current_disposition") != "NO_LIVE_INSTANCE"
            or v13_disposition_status.get("launch_allowed") is not False
            or v13_disposition_status.get("adopted_for_execution") is not False
        ):
            raise ValueError("A1.2 v12-r3 adoption-input hardening is invalid")
        if v2_closeout_audit is not None:
            v2_checks = v2_closeout_audit.get("check_groups")
            v2_recoveries = v2_closeout_audit.get("failures_and_recoveries")
            v2_safety = v2_closeout_audit.get("safety")
            if (
                v2_closeout_audit.get("schema_version")
                != "myis.armindex-a1.2-vast-4x3090-closeout-validation-audit.v2"
                or v2_closeout_audit.get("audit_id")
                != "a1.2-vast-4x3090-preflight-closeout-validation-20260806"
                or v2_closeout_audit.get("revision_id") != "a1.2-local-vast-4x3090-v2"
                or v2_closeout_audit.get("status") != "PASS"
                or v2_closeout_audit.get("scientific_authority") is not False
                or not isinstance(v2_checks, list)
                or v2_closeout_audit.get("check_count") != len(v2_checks)
                or any(
                    not isinstance(item, Mapping) or item.get("status") != "PASS"
                    for item in v2_checks
                )
                or not isinstance(v2_recoveries, list)
                or any(
                    not isinstance(item, Mapping)
                    or item.get("status")
                    not in {"repaired_and_validated", "bounded_and_validated"}
                    or item.get("counters_changed") is not False
                    for item in v2_recoveries
                )
                or not isinstance(v2_safety, Mapping)
                or any(value is not False for value in v2_safety.values())
                or any(
                    int(value) != 0
                    for value in v2_closeout_audit.get("real_counters", {}).values()
                )
                or any(
                    float(value) != 0
                    for value in v2_closeout_audit.get("resource_counters", {}).values()
                )
                or v2_closeout_audit.get("audit_sha256")
                != canonical_sha256(
                    {
                        key: value
                        for key, value in v2_closeout_audit.items()
                        if key != "audit_sha256"
                    }
                )
            ):
                raise ValueError("A1.2 Vast v2 closeout audit is invalid")
        if preflight is not None:
            assert_aggregate_only(preflight)
            if (
                preflight.get("schema_version")
                != "myis.armindex-a1.2-owner-local-preflight.v1"
                or preflight.get("phase_id") != "A1_BASELINES_AND_MULTI_ARM_SCREENING"
                or preflight.get("task_id") != "A1.2"
                or preflight.get("scientific_authority") is not False
                or preflight.get("launch_ready") is not False
                or preflight.get("execution_contract_adopted") is not False
                or preflight.get("gpu_reserved") is not False
                or preflight.get("measured_execution") is not False
                or preflight.get("protected_data_accessed") is not False
                or preflight.get("credentials_accessed") is not False
                or preflight.get("receipt_sha256")
                != canonical_sha256(
                    {
                        key: value
                        for key, value in preflight.items()
                        if key != "receipt_sha256"
                    }
                )
            ):
                raise ValueError("A1.2 owner-local preflight receipt is invalid")
        check_groups = closeout_audit.get("check_groups")
        recoveries = closeout_audit.get("failures_and_recoveries")
        safety = closeout_audit.get("safety")
        if (
            closeout_audit.get("schema_version")
            != "myis.armindex-a1.2-closeout-validation-audit.v1"
            or closeout_audit.get("audit_id")
            != "a1.2-contract-scaffold-closeout-validation-20260805"
            or closeout_audit.get("phase_id") != "A1_BASELINES_AND_MULTI_ARM_SCREENING"
            or closeout_audit.get("task_id") != "A1.2"
            or closeout_audit.get("status") != "PASS"
            or closeout_audit.get("scientific_authority") is not False
            or not isinstance(check_groups, list)
            or closeout_audit.get("check_count") != len(check_groups)
            or any(
                not isinstance(item, Mapping) or item.get("status") != "PASS"
                for item in check_groups
            )
            or not isinstance(recoveries, list)
            or any(
                not isinstance(item, Mapping)
                or item.get("status")
                not in {"repaired_and_validated", "bounded_and_validated"}
                or item.get("counters_changed") is not False
                for item in recoveries
            )
            or not isinstance(safety, Mapping)
            or any(value is not False for value in safety.values())
            or any(
                int(value) != 0
                for value in closeout_audit.get("real_counters", {}).values()
            )
            or any(
                int(value) != 0
                for value in closeout_audit.get("resource_counters", {}).values()
            )
            or closeout_audit.get("audit_sha256")
            != canonical_sha256(
                {
                    key: value
                    for key, value in closeout_audit.items()
                    if key != "audit_sha256"
                }
            )
        ):
            raise ValueError("A1.2 closeout validation audit is invalid")
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        return {
            **missing,
            "status": "invalid"
            if (root / A12_RECEIPT_PATH).exists()
            else "not_started",
        }
    counts = lockset["aggregate_counts"]
    v2_projection = dict(missing["vast_preflight_v2"])
    if (
        v2_receipt is not None
        and v2_contract is not None
        and v2_budget is not None
        and v2_topology is not None
        and v2_checklist is not None
        and v2_synthetic is not None
    ):
        v2_projection = {
            **v2_projection,
            "status": str(v2_receipt["status"]),
            "validated": True,
            "revision_id": str(v2_receipt["revision_id"]),
            "receipt_sha256": _file_sha256(root / A12_V2_RECEIPT_PATH),
            "receipt_self_sha256": str(v2_receipt["receipt_sha256"]),
            "contract_sha256": _file_sha256(
                root / A12_V2_CONTROL_ROOT / "execution-contract.v2.json"
            ),
            "synthetic_receipt_sha256": _file_sha256(
                root / A12_V2_SYNTHETIC_RECEIPT_PATH
            ),
            "synthetic_receipt_self_sha256": str(v2_synthetic["receipt_sha256"]),
            "runbook_sha256": _file_sha256(root / A12_V2_RUNBOOK_PATH),
            "ledger_sha256": _file_sha256(root / A12_V2_LEDGER_PATH),
            "budget_uri": A12_V2_BUDGET_PATH.as_posix(),
            "budget_sha256": _file_sha256(root / A12_V2_BUDGET_PATH),
            "topology_uri": (
                A12_V2_CONTROL_ROOT / "topology-contract.v2.json"
            ).as_posix(),
            "topology_sha256": _file_sha256(
                root / A12_V2_CONTROL_ROOT / "topology-contract.v2.json"
            ),
            "runtime_lock_uri": (
                A12_V2_CONTROL_ROOT / "runtime-lock.v2.json"
            ).as_posix(),
            "runtime_lock_sha256": _file_sha256(
                root / A12_V2_CONTROL_ROOT / "runtime-lock.v2.json"
            ),
            "image_contract_uri": (
                A12_V2_CONTROL_ROOT / "image-digest-contract.v2.json"
            ).as_posix(),
            "image_contract_sha256": _file_sha256(
                root / A12_V2_CONTROL_ROOT / "image-digest-contract.v2.json"
            ),
            "checklist_uri": (
                A12_V2_CONTROL_ROOT / "launch-checklist.v2.json"
            ).as_posix(),
            "checklist_sha256": _file_sha256(
                root / A12_V2_CONTROL_ROOT / "launch-checklist.v2.json"
            ),
            "shutdown_uri": (A12_V2_CONTROL_ROOT / "shutdown-plan.v2.json").as_posix(),
            "shutdown_sha256": _file_sha256(
                root / A12_V2_CONTROL_ROOT / "shutdown-plan.v2.json"
            ),
            "allowlist_sha256": _file_sha256(root / A12_V2_ALLOWLIST_PATH),
            "owner_runbook_sha256": _file_sha256(root / A12_V2_OWNER_RUNBOOK_PATH),
            "coordinator_sha256": _file_sha256(root / A12_V2_COORDINATOR_PATH),
            "watchdog_sha256": _file_sha256(root / A12_V2_WATCHDOG_PATH),
            "closeout_validation_audit_sha256": (
                _file_sha256(root / A12_V2_CLOSEOUT_AUDIT_PATH)
                if v2_closeout_audit is not None
                else None
            ),
            "closeout_validation_check_count": (
                len(v2_closeout_audit["check_groups"])
                if v2_closeout_audit is not None
                else 0
            ),
            "closeout_validation_recovery_count": (
                len(v2_closeout_audit["failures_and_recoveries"])
                if v2_closeout_audit is not None
                else 0
            ),
            "closeout_validation_recoveries": (
                [dict(item) for item in v2_closeout_audit["failures_and_recoveries"]]
                if v2_closeout_audit is not None
                else []
            ),
            "jobs": [
                {
                    "arm_id": arm_id,
                    "uri": (
                        A12_V2_CONTROL_ROOT / "jobs" / "v2" / f"{arm_id}.json"
                    ).as_posix(),
                    "sha256": _file_sha256(
                        root / A12_V2_CONTROL_ROOT / "jobs" / "v2" / f"{arm_id}.json"
                    ),
                }
                for arm_id in ("ARM-02", "ARM-03", "ARM-04", "ARM-05")
            ],
            "launch_allowed": bool(v2_receipt["launch_allowed"]),
            "adopted_for_execution": bool(v2_receipt["adopted_for_execution"]),
            "live_check_count": len(v2_checklist["pending_live_owner"]),
            "live_checks_pending": list(v2_checklist["pending_live_owner"]),
            "synthetic_worker_count": int(v2_synthetic["worker_count"]),
            "synthetic_parallel_launch_count": int(
                v2_synthetic["parallel_launch_count"]
            ),
            "planning_rate_usd": float(
                v2_budget["planning_quote"]["hourly_instance_usd"]
            ),
            "estimated_instance_hours": str(
                v2_receipt["budget"]["estimated_instance_hours"]
            ),
            "estimated_raw_worker_usd": str(
                v2_receipt["budget"]["estimated_raw_worker_usd"]
            ),
            "estimated_instance_hours_min": int(
                v2_budget["planning_quote"]["estimated_instance_hours_min"]
            ),
            "estimated_instance_hours_max": int(
                v2_budget["planning_quote"]["estimated_instance_hours_max"]
            ),
            "estimated_raw_worker_usd_min": float(
                v2_budget["planning_quote"]["raw_worker_estimate_min_usd"]
            ),
            "estimated_raw_worker_usd_max": float(
                v2_budget["planning_quote"]["raw_worker_estimate_max_usd"]
            ),
            "gpu_count": int(v2_topology["worker"]["gpu_count"]),
            "gpu_model": str(v2_topology["worker"]["gpu_model_exact"]),
            "real_counters": dict(v2_receipt["real_counters"]),
            "resource_counters": dict(v2_receipt["resource_counters"]),
            "claim_boundary": str(v2_receipt["claim_boundary"]),
            "next_authorized_action": str(v2_receipt["next_authorized_action"]),
        }
    v3_projection = dict(missing["vast_preflight_v3"])
    if v3_receipt is not None and v3_contract is not None and v3_validation is not None:
        v3_projection = {
            **v3_projection,
            "status": str(v3_receipt["status"]),
            "validated": True,
            "revision_id": str(v3_receipt["revision_id"]),
            "receipt_sha256": _file_sha256(root / A12_V3_RECEIPT_PATH),
            "receipt_self_sha256": str(v3_receipt["receipt_sha256"]),
            "contract_sha256": _file_sha256(root / A12_V3_CONTRACT_PATH),
            "contract_self_sha256": str(v3_contract["contract_sha256"]),
            "control_runbook_sha256": _file_sha256(root / A12_V3_CONTROL_RUNBOOK_PATH),
            "owner_runbook_sha256": _file_sha256(root / A12_V3_OWNER_RUNBOOK_PATH),
            "schema_sha256": _file_sha256(root / A12_V3_SCHEMA_PATH),
            "module_sha256": _file_sha256(root / A12_V3_MODULE_PATH),
            "v2_receipt_sha256": str(v3_receipt["v2_receipt_sha256"]),
            "planning_rate_usd": float(
                v3_receipt["budget"]["planning_rate_usd_per_four_gpu_instance_hour"]
            ),
            "estimated_instance_hours": str(
                v3_receipt["budget"]["estimated_instance_hours"]
            ),
            "estimated_raw_worker_usd": str(
                v3_receipt["budget"]["estimated_raw_worker_usd"]
            ),
            "common_screen_hard_stop_usd": int(
                v3_receipt["budget"]["common_screen_hard_stop_usd"]
            ),
            "a1_hard_stop_usd": int(v3_receipt["budget"]["a1_hard_stop_usd"]),
            "campaign_hard_stop_usd": int(
                v3_receipt["budget"]["campaign_hard_stop_usd"]
            ),
            "launch_allowed": bool(v3_receipt["launch_allowed"]),
            "adopted_for_execution": bool(v3_receipt["adopted_for_execution"]),
            "real_counters": dict(v3_receipt["real_counters"]),
            "resource_counters": dict(v3_receipt["resource_counters"]),
            "claim_boundary": str(v3_receipt["claim_boundary"]),
            "next_authorized_action": str(v3_receipt["next_authorized_action"]),
        }
    v5_projection = dict(missing["vast_preflight_v5"])
    if v5_receipt is not None and v5_contract is not None and v5_validation is not None:
        v5_projection = {
            **v5_projection,
            "status": str(v5_receipt["status"]),
            "validated": True,
            "revision_id": str(v5_receipt["revision_id"]),
            "receipt_sha256": _file_sha256(root / A12_V5_RECEIPT_PATH),
            "contract_sha256": _file_sha256(root / A12_V5_CONTRACT_PATH),
            "runtime_lock_sha256": _file_sha256(root / A12_V5_RUNTIME_LOCK_PATH),
            "image_contract_sha256": _file_sha256(root / A12_V5_IMAGE_CONTRACT_PATH),
            "topology_sha256": _file_sha256(root / A12_V5_TOPOLOGY_PATH),
            "schema_sha256": _file_sha256(root / A12_V5_SCHEMA_PATH),
            "owner_runbook_sha256": _file_sha256(root / A12_V5_OWNER_RUNBOOK_PATH),
            "module_sha256": _file_sha256(root / A12_V5_MODULE_PATH),
            "image_reference": str(v5_receipt["image_reference"]),
            "resolved_manifest_digest": str(v5_receipt["resolved_manifest_digest"]),
            "platform": str(v5_receipt["platform"]),
            "local_preparation_status": str(v5_receipt["local_preparation_status"]),
            "model_snapshots": str(v5_receipt["model_snapshots"]),
            "cpu_model_load": str(v5_receipt["cpu_model_load"]),
            "dense_gpu_parity": str(v5_receipt["dense_gpu_parity"]),
            "qwen_measured_max_length": str(v5_receipt["qwen_measured_max_length"]),
            "gpu_memory_feasibility": str(v5_receipt["gpu_memory_feasibility"]),
            "custom_local_docker_build": bool(v5_receipt["custom_local_docker_build"]),
            "launch_allowed": bool(v5_receipt["launch_allowed"]),
            "adopted_for_execution": bool(v5_receipt["adopted_for_execution"]),
            "live_checks_pending": list(v5_receipt["live_checks_pending"]),
            "removed_active_steps": list(v5_receipt["removed_active_steps"]),
            "upload_artifacts": list(v5_receipt["upload_artifacts"]),
            "real_counters": dict(v5_receipt["real_counters"]),
            "resource_counters": dict(v5_receipt["resource_counters"]),
            "claim_boundary": str(v5_receipt["claim_boundary"]),
            "next_authorized_action": str(v5_receipt["next_authorized_action"]),
        }
    v6_projection = dict(missing["vast_preflight_v6"])
    if (
        v6_receipt is not None
        and v6_contract is not None
        and v6_validation is not None
        and isinstance(continuation_policy, Mapping)
    ):
        v6_projection = {
            **v6_projection,
            "status": str(v6_receipt["status"]),
            "validated": True,
            "revision_id": str(v6_receipt["revision_id"]),
            "receipt_sha256": _file_sha256(root / A12_V6_RECEIPT_PATH),
            "receipt_self_sha256": str(v6_receipt["receipt_sha256"]),
            "contract_sha256": _file_sha256(root / A12_V6_CONTRACT_PATH),
            "contract_self_sha256": str(v6_contract["contract_sha256"]),
            "schema_sha256": _file_sha256(root / A12_V6_SCHEMA_PATH),
            "validator_sha256": _file_sha256(root / A12_V6_MODULE_PATH),
            "preflight_module_sha256": _file_sha256(
                root / A12_V6_PREFLIGHT_MODULE_PATH
            ),
            "owner_runbook_sha256": _file_sha256(root / A12_V6_OWNER_RUNBOOK_PATH),
            "continuation_policy": {
                "status": str(continuation_policy["status"]),
                "validated": True,
                "policy_uri": A12_V6_CONTINUATION_POLICY_PATH.as_posix(),
                "policy_sha256": _file_sha256(root / A12_V6_CONTINUATION_POLICY_PATH),
                "default_post_preflight_instruction": str(
                    continuation_policy["default_post_preflight_instruction"]
                ),
                "allowed_post_preflight_instruction": str(
                    continuation_policy["allowed_post_preflight_instruction"]
                ),
                # v6 is still preflight-pending; this policy is conditional and
                # cannot authorize reuse until its listed live evidence exists.
                "continuation_authorized_now": False,
                "continuation_requires": list(
                    continuation_policy["continuation_requires"]
                ),
                "fallback_to_destroy_if": list(
                    continuation_policy["fallback_to_destroy_if"]
                ),
            },
            "image_reference": str(v6_contract["image_reference"]),
            "resolved_manifest_digest": str(v6_contract["resolved_manifest_digest"]),
            "platform": str(v6_contract["platform"]),
            "live_quote_usd_per_hour": float(v6_contract["live_quote_usd_per_hour"]),
            "estimated_preflight_usd": dict(v6_contract["estimated_preflight_usd"]),
            "budget_hard_stops_usd": dict(v6_contract["budget_hard_stops_usd"]),
            "observed_live_defects": list(v6_contract["observed_live_defects"]),
            "corrections": dict(v6_contract["corrections"]),
            "launch_allowed": bool(v6_receipt["launch_allowed"]),
            "adopted_for_execution": bool(v6_receipt["adopted_for_execution"]),
            "synthetic_preflight_only": bool(v6_contract["synthetic_preflight_only"]),
            "real_counters": {
                "measured_runs": int(v6_receipt["measured_runs"]),
                "candidate_count": 0,
                "selection_accesses": int(v6_receipt["selection_accesses"]),
                "final_accesses": int(v6_receipt["final_accesses"]),
            },
            "resource_counters": dict(
                missing["vast_preflight_v6"]["resource_counters"]
            ),
            "claim_boundary": str(v6_receipt["claim_boundary"]),
            "next_authorized_action": str(v6_contract["next_authorized_action"]),
        }
    v7_projection = dict(missing["vast_preflight_v7"])
    if (
        v7_receipt is not None
        and v7_contract is not None
        and v7_validation is not None
        and isinstance(continuation_policy, Mapping)
    ):
        image_runtime_lock = v7_contract["image_runtime_lock"]
        active_correction = v7_contract["active_correction"]
        v7_projection = {
            **v7_projection,
            "status": str(v7_receipt["status"]),
            "validated": True,
            "revision_id": str(v7_receipt["revision_id"]),
            "receipt_sha256": _file_sha256(root / A12_V7_RECEIPT_PATH),
            "receipt_self_sha256": str(v7_receipt["receipt_sha256"]),
            "contract_sha256": _file_sha256(root / A12_V7_CONTRACT_PATH),
            "contract_self_sha256": str(v7_contract["contract_sha256"]),
            "schema_sha256": _file_sha256(root / A12_V7_SCHEMA_PATH),
            "validator_sha256": _file_sha256(root / A12_V7_MODULE_PATH),
            "owner_runbook_sha256": _file_sha256(root / A12_V7_OWNER_RUNBOOK_PATH),
            "coordinator_sha256": _file_sha256(root / A12_V7_COORDINATOR_PATH),
            "bootstrap_sha256": _file_sha256(root / A12_V7_BOOTSTRAP_PATH),
            "supplement_validator_sha256": _file_sha256(
                root / A12_V7_SUPPLEMENT_VALIDATOR_PATH
            ),
            "supplement_requirements_sha256": _file_sha256(
                root / A12_V7_SUPPLEMENT_REQUIREMENTS_PATH
            ),
            "supplement_workflow_sha256": _file_sha256(
                root / A12_V7_SUPPLEMENT_WORKFLOW_PATH
            ),
            "continuation_policy": {
                "status": str(continuation_policy["status"]),
                "validated": True,
                "policy_uri": A12_V6_CONTINUATION_POLICY_PATH.as_posix(),
                "policy_sha256": _file_sha256(root / A12_V6_CONTINUATION_POLICY_PATH),
                "default_post_preflight_instruction": str(
                    continuation_policy["default_post_preflight_instruction"]
                ),
                "allowed_post_preflight_instruction": str(
                    continuation_policy["allowed_post_preflight_instruction"]
                ),
                "continuation_authorized_now": False,
                "continuation_requires": list(
                    continuation_policy["continuation_requires"]
                ),
                "fallback_to_destroy_if": list(
                    continuation_policy["fallback_to_destroy_if"]
                ),
            },
            "image_reference": str(image_runtime_lock["image_reference"]),
            "resolved_manifest_digest": str(
                image_runtime_lock["resolved_manifest_digest"]
            ),
            "platform": str(image_runtime_lock["platform"]),
            "preserved_live_failures": [
                {
                    "failure_id": str(item["failure_id"]),
                    "description": str(item["description"]),
                    "disposition": str(item["disposition"]),
                }
                for item in v7_contract["preserved_live_failures"]
            ],
            "active_correction": {
                "fresh_remote_root_required": bool(
                    active_correction["fresh_root_required"]
                ),
                "same_instance_reuse": bool(active_correction["same_instance_reuse"]),
                "pythondontwritebytecode": v7_receipt["pythondontwritebytecode"]
                is True,
                "reuse_only_after_sha256_validation": list(
                    active_correction["reuse_only_after_sha256_validation"]
                ),
                "upload_only": list(active_correction["upload_only"]),
            },
            "launch_allowed": bool(v7_receipt["launch_allowed"]),
            "adopted_for_execution": bool(v7_receipt["adopted_for_execution"]),
            "synthetic_preflight_only": bool(v7_contract["synthetic_preflight_only"]),
            "real_counters": dict(v7_contract["real_counters"]),
            "resource_counters": dict(v7_contract["resource_counters"]),
            "claim_boundary": str(v7_receipt["claim_boundary"]),
            "next_authorized_action": str(v7_contract["next_authorized_action"]),
        }
    v8_projection = dict(missing["vast_preflight_v8"])
    if v8_receipt is not None and v8_contract is not None and v8_validation is not None:
        active_correction = v8_contract["active_correction"]
        v8_projection = {
            **v8_projection,
            "status": str(v8_receipt["status"]),
            "validated": True,
            "revision_id": str(v8_receipt["revision_id"]),
            "receipt_sha256": _file_sha256(root / A12_V8_RECEIPT_PATH),
            "receipt_self_sha256": str(v8_receipt["receipt_sha256"]),
            "contract_sha256": _file_sha256(root / A12_V8_CONTRACT_PATH),
            "contract_self_sha256": str(v8_contract["contract_sha256"]),
            "schema_sha256": _file_sha256(root / A12_V8_SCHEMA_PATH),
            "validator_sha256": _file_sha256(root / A12_V8_MODULE_PATH),
            "owner_runbook_sha256": _file_sha256(root / A12_V8_OWNER_RUNBOOK_PATH),
            "coordinator_sha256": _file_sha256(root / A12_V8_COORDINATOR_PATH),
            "bootstrap_sha256": _file_sha256(root / A12_V8_BOOTSTRAP_PATH),
            "image_reference": str(v8_contract["image_reference"]),
            "resolved_manifest_digest": str(v8_contract["resolved_manifest_digest"]),
            "platform": str(v8_contract["platform"]),
            "preserved_live_failures": [
                {
                    "failure_id": str(failure_id),
                    "description": "Preserved failed-closed live engineering attempt.",
                    "disposition": "preserved_immutable_additive_repair",
                }
                for failure_id in v8_contract["preserved_live_failures"]
            ],
            "active_correction": {
                "fresh_remote_root": str(active_correction["fresh_remote_root"]),
                "source_remote_root": str(active_correction["source_remote_root"]),
                "same_instance_reuse": bool(active_correction["same_instance_reuse"]),
                "validation_lineage_complete": bool(
                    active_correction["validation_lineage_complete"]
                ),
                "historical_dockerfile_hash_only_nonexecuted": bool(
                    active_correction["historical_dockerfile_hash_only_nonexecuted"]
                ),
                "pythondontwritebytecode": bool(
                    active_correction["pythondontwritebytecode"]
                ),
                "reuse_only_after_sha256_validation": list(
                    active_correction["reuse_only_after_sha256_validation"]
                ),
                "upload_only": list(active_correction["upload_only"]),
            },
            "launch_allowed": bool(v8_receipt["launch_allowed"]),
            "adopted_for_execution": bool(v8_receipt["adopted_for_execution"]),
            "synthetic_preflight_only": bool(v8_contract["synthetic_preflight_only"]),
            "real_counters": dict(v8_contract["real_counters"]),
            "resource_counters": dict(v8_contract["resource_counters"]),
            "claim_boundary": str(v8_receipt["claim_boundary"]),
            "next_authorized_action": str(v8_contract["next_authorized_action"]),
        }
    v9_projection = dict(missing["vast_preflight_v9"])
    if v9_receipt is not None and v9_contract is not None and v9_validation is not None:
        active_correction = v9_contract["active_correction"]
        v9_projection = {
            **v9_projection,
            "status": str(v9_receipt["status"]),
            "validated": True,
            "revision_id": str(v9_receipt["revision_id"]),
            "receipt_sha256": _file_sha256(root / A12_V9_RECEIPT_PATH),
            "receipt_self_sha256": str(v9_receipt["receipt_sha256"]),
            "contract_sha256": _file_sha256(root / A12_V9_CONTRACT_PATH),
            "contract_self_sha256": str(v9_contract["contract_sha256"]),
            "schema_sha256": _file_sha256(root / A12_V9_SCHEMA_PATH),
            "validator_sha256": _file_sha256(root / A12_V9_MODULE_PATH),
            "runtime_sha256": _file_sha256(root / A12_V9_RUNTIME_PATH),
            "owner_runbook_sha256": _file_sha256(root / A12_V9_OWNER_RUNBOOK_PATH),
            "coordinator_sha256": _file_sha256(root / A12_V9_COORDINATOR_PATH),
            "bootstrap_sha256": _file_sha256(root / A12_V9_BOOTSTRAP_PATH),
            "launcher_sha256": _file_sha256(root / A12_V9_LAUNCHER_PATH),
            "active_correction": {
                "fresh_remote_root": str(active_correction["fresh_remote_root"]),
                "source_remote_root": str(active_correction["source_remote_root"]),
                "same_instance_reuse": bool(active_correction["same_instance_reuse"]),
                "implementation_validation_complete": bool(
                    active_correction["implementation_validation_complete"]
                ),
                "live_preflight_execution_pending": bool(
                    active_correction["live_preflight_execution_pending"]
                ),
                "required_lifecycle_controls": list(
                    active_correction["required_lifecycle_controls"]
                ),
            },
            "launch_allowed": bool(v9_receipt["launch_allowed"]),
            "adopted_for_execution": bool(v9_receipt["adopted_for_execution"]),
            "synthetic_preflight_only": bool(v9_contract["synthetic_preflight_only"]),
            "real_counters": dict(v9_contract["real_counters"]),
            "resource_counters": dict(v9_contract["resource_counters"]),
            "claim_boundary": str(v9_receipt["claim_boundary"]),
            "next_authorized_action": str(v9_contract["next_authorized_action"]),
        }
    if v9_result_receipt is not None and v9_result_validation is not None:
        v9_projection = {
            **v9_projection,
            "live_result_sha256": _file_sha256(root / A12_V9_RESULT_RECEIPT_PATH),
            "live_result_self_sha256": str(v9_result_receipt["receipt_sha256"]),
            "live_result_revision_id": str(v9_result_receipt["revision_id"]),
            "live_result_status": str(v9_result_receipt["status"]),
            "live_result_schema_uri": A12_V9_RESULT_SCHEMA_PATH.as_posix(),
            "live_result_schema_sha256": _file_sha256(root / A12_V9_RESULT_SCHEMA_PATH),
            "live_result_validator_uri": A12_V9_RESULT_MODULE_PATH.as_posix(),
            "live_result_validator_sha256": _file_sha256(
                root / A12_V9_RESULT_MODULE_PATH
            ),
            "live_result": {
                "attempt_id": str(v9_result_receipt["attempt_id"]),
                "identity": dict(v9_result_receipt["identity"]),
                "provider": dict(v9_result_receipt["provider"]),
                "arms": [dict(item) for item in v9_result_receipt["arms"]],
                "qwen": dict(v9_result_receipt["qwen"]),
                "lifecycle": dict(v9_result_receipt["lifecycle"]),
                "pending_live_checks": list(v9_result_receipt["pending_live_checks"]),
                "owner_disposition": str(v9_result_receipt["owner_disposition"]),
            },
            "claim_boundary": str(v9_result_receipt["claim_boundary"]),
            "next_authorized_action": str(v9_result_receipt["next_authorized_action"]),
        }
    v10_closeout_projection = dict(missing["provider_closeout_v10"])
    if v10_closeout_receipt is not None and v10_closeout_validation is not None:
        v10_closeout_projection = {
            **v10_closeout_projection,
            "status": str(v10_closeout_receipt["status"]),
            "validated": True,
            "revision_id": str(v10_closeout_receipt["revision_id"]),
            "receipt_sha256": _file_sha256(root / A12_V10_CLOSEOUT_RECEIPT_PATH),
            "receipt_self_sha256": str(v10_closeout_receipt["receipt_sha256"]),
            "schema_sha256": _file_sha256(root / A12_V10_CLOSEOUT_SCHEMA_PATH),
            "validator_sha256": _file_sha256(root / A12_V10_CLOSEOUT_MODULE_PATH),
            "predecessor": dict(v10_closeout_receipt["predecessor"]),
            "owner_evidence": dict(v10_closeout_receipt["owner_evidence"]),
            "provider_closeout": dict(v10_closeout_receipt["provider_closeout"]),
            "pending_provider_checks": list(
                v10_closeout_receipt["pending_provider_checks"]
            ),
            "launch_allowed": bool(v10_closeout_receipt["launch_allowed"]),
            "adopted_for_execution": bool(
                v10_closeout_receipt["adopted_for_execution"]
            ),
            "measured_runs": int(v10_closeout_receipt["measured_runs"]),
            "selection_accesses": int(v10_closeout_receipt["selection_accesses"]),
            "final_accesses": int(v10_closeout_receipt["final_accesses"]),
            "charged_usd": float(v10_closeout_receipt["charged_usd"]),
            "claim_boundary": str(v10_closeout_receipt["claim_boundary"]),
            "next_authorized_action": str(
                v10_closeout_receipt["next_authorized_action"]
            ),
        }
    v11_request_projection = dict(missing["scientific_execution_request_v11"])
    if (
        v11_request_receipt is not None
        and v11_request is not None
        and v11_request_validation is not None
        and v11_budget is not None
    ):
        rigor_review = json.loads(
            (root / A12_V11_RIGOR_REVIEW_PATH).read_text(encoding="utf-8")
        )
        assert_aggregate_only(rigor_review)
        if (
            rigor_review.get("review_status") != "complete"
            or rigor_review.get("artifact_sha256")
            != _file_sha256(root / A12_V11_REQUEST_PATH)
            or rigor_review.get("governance", {}).get("blocking_findings") != []
            or rigor_review.get("overall", {}).get("grade")
            not in {"Accept", "Strong Accept"}
        ):
            raise ValueError("A1.2 v11 rigor review is invalid")
        summary = v11_request_receipt["validation_summary"]
        workload_binding = v11_request["component_bindings"]["workload_set"]
        workload_set = json.loads(
            (root / str(workload_binding["uri"])).read_text(encoding="utf-8")
        )
        v11_request_projection = {
            **v11_request_projection,
            "status": str(v11_request_receipt["status"]),
            "validated": True,
            "revision_id": str(v11_request_receipt["revision_id"]),
            "receipt_sha256": _file_sha256(root / A12_V11_RECEIPT_PATH),
            "receipt_self_sha256": str(v11_request_receipt["receipt_sha256"]),
            "request_sha256": _file_sha256(root / A12_V11_REQUEST_PATH),
            "request_self_sha256": str(v11_request["request_sha256"]),
            "request_schema_sha256": _file_sha256(root / A12_V11_REQUEST_SCHEMA_PATH),
            "receipt_schema_sha256": _file_sha256(root / A12_V11_RECEIPT_SCHEMA_PATH),
            "validator_sha256": _file_sha256(root / A12_V11_MODULE_PATH),
            "runbook_sha256": _file_sha256(root / A12_V11_RUNBOOK_PATH),
            "ledger_sha256": _file_sha256(root / A12_V11_LEDGER_PATH),
            "rigor_review_sha256": _file_sha256(root / A12_V11_RIGOR_REVIEW_PATH),
            "component_bindings": dict(v11_request["component_bindings"]),
            "jobs": [dict(item) for item in workload_set["manifests"]],
            "pending_adoption_requirements": list(
                v11_request_receipt["pending_adoption_requirements"]
            ),
            "authorization": dict(v11_request["authorization"]),
            "counters": dict(v11_request["counters"]),
            "budget_hard_stops": dict(v11_budget["hard_stops"]),
            "workload_manifests": int(summary["workload_manifests"]),
            "expected_program_arm_runs": int(summary["expected_program_arm_runs"]),
            "expected_physical_program_view_paths": int(
                summary["expected_physical_program_view_paths"]
            ),
            "rep_dev_query_count": int(summary["rep_dev_query_count"]),
            "harness_dev_reserved_count": int(summary["harness_dev_reserved_count"]),
            "launch_allowed": bool(v11_request_receipt["launch_allowed"]),
            "adopted_for_execution": bool(v11_request_receipt["adopted_for_execution"]),
            "claim_boundary": str(v11_request_receipt["claim_boundary"]),
            "next_authorized_action": str(
                v11_request_receipt["next_authorized_action"]
            ),
        }
    v12_r3_adoption_projection = dict(missing["adoption_inputs_v12_r3"])
    if (
        v12_r3_contract is not None
        and v13_publication_validation is not None
        and v13_disposition_status is not None
    ):
        v12_r3_adoption_projection = {
            **v12_r3_adoption_projection,
            "status": str(v12_r3_contract["status"]),
            "validated": True,
            "revision_id": str(v12_r3_contract["revision_id"]),
            "contract_sha256": _file_sha256(root / A12_V12_R3_CONTRACT_PATH),
            "contract_self_sha256": str(v12_r3_contract["contract_sha256"]),
            "contract_schema_sha256": _file_sha256(
                root / A12_V12_R3_CONTRACT_SCHEMA_PATH
            ),
            "validator_sha256": _file_sha256(
                root / "src/myis_research/armindex/"
                "a1_2_scientific_execution_adoption_inputs_v12_r3.py"
            ),
            "publication_impact": {
                "revision_id": A12_V13_PUBLICATION_REVISION_ID,
                "contract_uri": A12_V13_PUBLICATION_CONTRACT_PATH.as_posix(),
                "contract_sha256": _file_sha256(
                    root / A12_V13_PUBLICATION_CONTRACT_PATH
                ),
                "contract_self_sha256": str(
                    v13_publication_validation["contract_sha256"]
                ),
                "schema_uri": A12_V13_PUBLICATION_SCHEMA_PATH.as_posix(),
                "schema_sha256": _file_sha256(root / A12_V13_PUBLICATION_SCHEMA_PATH),
                "documentation_uri": A12_V13_PUBLICATION_DOCUMENTATION_PATH.as_posix(),
                "documentation_sha256": _file_sha256(
                    root / A12_V13_PUBLICATION_DOCUMENTATION_PATH
                ),
                "primary_outcome": str(v13_publication_validation["primary_outcome"]),
                "status": str(v13_publication_validation["status"]),
            },
            "instance_disposition": {
                "revision_id": A12_V13_DISPOSITION_REVISION_ID,
                "policy_uri": A12_V13_DISPOSITION_POLICY_PATH.as_posix(),
                "policy_sha256": _file_sha256(root / A12_V13_DISPOSITION_POLICY_PATH),
                "schema_uri": A12_V13_DISPOSITION_SCHEMA_PATH.as_posix(),
                "schema_sha256": _file_sha256(root / A12_V13_DISPOSITION_SCHEMA_PATH),
                **dict(v13_disposition_status),
            },
            "pending_live_provider": list(v12_r3_contract["pending_live_provider"]),
            "authorization": dict(v12_r3_contract["authorization"]),
            "counters": dict(v12_r3_contract["counters"]),
            "claim_boundary": str(v12_r3_contract["claim_boundary"]),
        }
    return {
        **missing,
        "status": (
            "a1_2_scientific_execution_adoption_request_prepared_owner_review_launch_locked"
            if v11_request_receipt is not None and v11_request_validation is not None
            else "a1_2_live_synthetic_preflight_closed_provider_destroyed_launch_locked"
            if v10_closeout_receipt is not None and v10_closeout_validation is not None
            else "a1_2_live_synthetic_preflight_pass_owner_disposition_pending_launch_locked"
            if v9_result_receipt is not None and v9_result_validation is not None
            else "a1_2_live_preflight_execution_lifecycle_prepared_launch_locked"
            if v9_projection["validated"]
            else "a1_2_live_preflight_validation_complete_bundle_prepared_launch_locked"
            if v8_projection["validated"]
            else "a1_2_live_preflight_same_instance_repair_prepared_launch_locked"
            if v7_projection["validated"]
            else "a1_2_live_preflight_correction_prepared_launch_locked"
            if v6_projection["validated"]
            else "a1_2_runtime_minimal_direct_base_preflight_prepared_launch_locked"
            if v5_projection["validated"]
            else "a1_2_vast_4x3090_postcommit_preflight_prepared_launch_locked"
            if v3_projection["validated"]
            else "a1_2_vast_4x3090_preflight_prepared_launch_locked"
            if v2_projection["validated"]
            else validation.status
        ),
        "validated": True,
        "v1_status": validation.status,
        "evidence_class": (
            "scientific_execution_adoption_request_preparation"
            if v11_request_receipt is not None and v11_request_validation is not None
            else "owner_local_provider_closeout"
            if v10_closeout_receipt is not None and v10_closeout_validation is not None
            else "live_engineering_synthetic_preflight"
            if v9_result_receipt is not None and v9_result_validation is not None
            else "live_engineering_preflight_execution_lifecycle_repair"
            if v9_projection["validated"]
            else "live_engineering_preflight_packaging_repair"
            if v8_projection["validated"]
            else "live_engineering_preflight_repair"
            if v7_projection["validated"]
            else "live_engineering_preflight_correction"
            if v6_projection["validated"]
            else "engineering_preflight_revision"
            if v5_projection["validated"]
            else "engineering_preflight_correction"
            if v3_projection["validated"]
            else "engineering_preflight_scaffold"
            if v2_projection["validated"]
            else "engineering_contract_scaffold"
        ),
        "claim_boundary": (
            v11_request_projection.get("claim_boundary")
            if v11_request_projection["validated"]
            else v10_closeout_projection.get("claim_boundary")
            if v10_closeout_projection["validated"]
            else v9_projection.get("claim_boundary")
            if v9_projection["validated"]
            else v8_projection.get("claim_boundary")
            if v8_projection["validated"]
            else v7_projection.get("claim_boundary")
            if v7_projection["validated"]
            else v6_projection.get("claim_boundary")
            if v6_projection["validated"]
            else v5_projection.get("claim_boundary")
            if v5_projection["validated"]
            else v3_projection.get("claim_boundary")
            if v3_projection["validated"]
            else v2_projection.get("claim_boundary")
            if v2_projection["validated"]
            else "offline_scaffold_only_no_measured_retrieval_claim"
        ),
        "receipt_sha256": _file_sha256(receipt_path),
        "runbook_sha256": _file_sha256(root / A12_RUNBOOK_PATH),
        "ledger_sha256": _file_sha256(root / A12_LEDGER_PATH),
        "execution_contract_sha256": _file_sha256(contract_path),
        "arm01_parity_receipt_sha256": _file_sha256(
            root / A12_ARM01_PARITY_RECEIPT_PATH
        ),
        "budget_profile_sha256": _file_sha256(budget_path),
        "execution_envelope_sha256": _file_sha256(
            root / "control/execution-envelope-a1.2-v1.yaml"
        ),
        "model_lockset_sha256": _file_sha256(lockset_path),
        "launch_checklist_sha256": _file_sha256(checklist_path),
        "shutdown_plan_sha256": _file_sha256(
            root / A12_CONTROL_ROOT / "shutdown-plan.v1.json"
        ),
        "report_archive_audit_sha256": _file_sha256(
            root / A12_CONTROL_ROOT / "report-archive-audit.v1.json"
        ),
        "closeout_validation_audit_sha256": _file_sha256(closeout_audit_path),
        "closeout_validation_check_count": len(check_groups),
        "closeout_validation_recovery_count": len(recoveries),
        "closeout_validation_recoveries": [dict(item) for item in recoveries],
        "model_lock_count": int(counts["arms"]),
        "offline_adapter_ready": int(counts["offline_adapter_ready"]),
        "dense_artifact_manifests_pending": int(
            counts["owner_artifact_manifests_pending"]
        ),
        "owner_requirements_pending": (
            len(v11_request_receipt["pending_adoption_requirements"])
            if v11_request_receipt is not None and v11_request_validation is not None
            else len(v10_closeout_receipt["pending_provider_checks"])
            if v10_closeout_receipt is not None and v10_closeout_validation is not None
            else len(v9_result_receipt["pending_live_checks"])
            if v9_result_receipt is not None and v9_result_validation is not None
            else len(v5_projection["live_checks_pending"])
            if v5_projection["validated"]
            else int(v2_projection["live_check_count"])
            if v2_projection["validated"]
            else len(checklist["pending_owner"])
        ),
        "launch_ready": bool(checklist["launch_ready"]),
        "measured_execution": bool(validation.measured_execution),
        "resource_plan": (
            {
                "arm01": "local_cpu_only_zero_gpu_usd",
                "dense_arms": "one_owner_managed_vast_instance_four_rtx3090_parallel",
                "estimated_instance_hours": v2_projection["estimated_instance_hours"],
                "estimated_raw_worker_usd": v2_projection["estimated_raw_worker_usd"],
                "planning_rate_usd_per_instance_hour": v2_projection[
                    "planning_rate_usd"
                ],
            }
            if v2_projection["validated"]
            else dict(contract["resource_plan"])
        ),
        "budget_limits": {
            **dict(budget["limits"]),
            **(
                {
                    "planning_rate_usd_per_four_gpu_instance_hour": v2_projection[
                        "planning_rate_usd"
                    ],
                    "estimated_instance_hours": v2_projection[
                        "estimated_instance_hours"
                    ],
                    "estimated_raw_worker_usd": v2_projection[
                        "estimated_raw_worker_usd"
                    ],
                }
                if v2_projection["validated"]
                else {}
            ),
        },
        "archive_disposition": dict(receipt["archive_disposition"]),
        "real_counters": dict(contract["real_counters"]),
        "resource_counters": dict(contract["resource_counters"]),
        "next_authorized_action": (
            str(v11_request_projection["next_authorized_action"])
            if v11_request_projection["validated"]
            else str(v10_closeout_projection["next_authorized_action"])
            if v10_closeout_projection["validated"]
            else str(v9_projection["next_authorized_action"])
            if v9_projection["validated"]
            else str(v8_projection["next_authorized_action"])
            if v8_projection["validated"]
            else str(v7_projection["next_authorized_action"])
            if v7_projection["validated"]
            else str(v6_projection["next_authorized_action"])
            if v6_projection["validated"]
            else str(v5_projection["next_authorized_action"])
            if v5_projection["validated"]
            else str(v3_projection["next_authorized_action"])
            if v3_projection["validated"]
            else A1_2_SCAFFOLD_NEXT_AUTHORIZED_ACTION
        ),
        "preflight_sha256": _file_sha256(preflight_path)
        if preflight_path.is_file()
        else None,
        "preflight_status": preflight.get("status", "not_started")
        if isinstance(preflight, Mapping)
        else "not_started",
        "preflight_blockers": list(preflight.get("blockers", []))
        if isinstance(preflight, Mapping)
        else [],
        "preflight_launch_ready": bool(preflight.get("launch_ready", False))
        if isinstance(preflight, Mapping)
        else False,
        "preflight_mlflow_registration_sha256": _file_sha256(
            root
            / "outputs/audits/armindex/a1.2-owner-local-preflight-mlflow-registration.json"
        )
        if (
            root
            / "outputs/audits/armindex/a1.2-owner-local-preflight-mlflow-registration.json"
        ).is_file()
        else None,
        "vast_preflight_v2": v2_projection,
        "vast_preflight_v3": v3_projection,
        "vast_preflight_v5": v5_projection,
        "vast_preflight_v6": v6_projection,
        "vast_preflight_v7": v7_projection,
        "vast_preflight_v8": v8_projection,
        "vast_preflight_v9": v9_projection,
        "provider_closeout_v10": v10_closeout_projection,
        "scientific_execution_request_v11": v11_request_projection,
        "adoption_inputs_v12_r3": v12_r3_adoption_projection,
    }


def _validate_a11_ledger(
    path: Path,
    *,
    fixture_receipt_sha256: str,
    gpu_proposal_sha256: str,
) -> None:
    entries = [
        json.loads(line)
        for line in path.read_text(encoding="ascii").splitlines()
        if line
    ]
    if len(entries) < 3:
        raise ValueError("A1.1 execution ledger is incomplete")
    previous = "0" * 64
    for sequence, entry in enumerate(entries, start=1):
        if not isinstance(entry, Mapping):
            raise ValueError("A1.1 execution ledger entry must be an object")
        unsigned = {key: value for key, value in entry.items() if key != "entry_sha256"}
        if (
            entry.get("ledger_id") != "a1.1-adapter-fixture-validation-v1"
            or entry.get("sequence") != sequence
            or entry.get("previous_entry_sha256") != previous
            or entry.get("entry_sha256") != canonical_sha256(unsigned)
        ):
            raise ValueError("A1.1 execution ledger sequence or chain is invalid")
        assert_aggregate_only(entry)
        previous = str(entry["entry_sha256"])
    fixture_event = entries[-2]
    final = entries[-1]
    if (
        fixture_event.get("status") != "passed"
        or fixture_event.get("artifact_sha256") != fixture_receipt_sha256
        or final.get("status") != "complete"
        or final.get("gpu_proposal_sha256") != gpu_proposal_sha256
    ):
        raise ValueError(
            "A1.1 execution ledger does not close against frozen artifacts"
        )


def _validate_a09_ledger(path: Path, *, audit_sha256: str) -> None:
    entries = [
        json.loads(line)
        for line in path.read_text(encoding="ascii").splitlines()
        if line
    ]
    if len(entries) < 2:
        raise ValueError("A0.9 execution ledger is incomplete")
    previous = "0" * 64
    for sequence, entry in enumerate(entries, start=1):
        if not isinstance(entry, Mapping):
            raise ValueError("A0.9 execution ledger entry must be an object")
        unsigned = {key: value for key, value in entry.items() if key != "entry_sha256"}
        if (
            entry.get("ledger_id") != "a0.9-validation-safety-closeout-v1"
            or entry.get("sequence") != sequence
            or entry.get("previous_entry_sha256") != previous
            or entry.get("entry_sha256") != canonical_sha256(unsigned)
        ):
            raise ValueError("A0.9 execution ledger sequence or chain is invalid")
        assert_aggregate_only(entry)
        previous = str(entry["entry_sha256"])
    final = entries[-1]
    if (
        final.get("status") != "complete"
        or final.get("validation_audit_sha256") != audit_sha256
    ):
        raise ValueError(
            "A0.9 execution ledger does not close against the validation audit"
        )


def _presentation_screens(
    *,
    p1_state: str,
    phases: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    next_actions: list[dict[str, str]],
    has_valid_result: bool,
    has_legacy_output: bool,
) -> list[dict[str, Any]]:
    """Build the reviewed, presentation-safe ten-screen story from canonical state."""

    audiences = ["owner", "advisor", "peer"]
    complete_tasks = sum(
        task.get("status") in {"complete", "measured"} for task in tasks
    )
    phase_summary = ", ".join(
        f"{str(phase.get('phase_id', '')).split('_', 1)[0]}: {phase.get('status', 'planned')}"
        for phase in phases
    )
    next_label = (
        str(next_actions[0]["label"]) if next_actions else "ไม่มีคำสั่งจาก Owner ที่ค้างอยู่"
    )
    latest_result = (
        "มีผล P1 ที่ผ่าน evidence matrix สำหรับ train/selection; final ยังปิดตาม protocol"
        if has_valid_result
        else "ยังไม่มีผล P1 ที่ผ่าน validation; สถานะที่รายงานได้คือ blocked with evidence"
    )
    delivered = (
        f"Task ที่เสร็จพร้อมหลักฐาน {complete_tasks}/{len(tasks)}; เก็บ legacy receipt ไว้เป็น historical-invalid output"
        if has_legacy_output
        else f"Task ที่เสร็จพร้อมหลักฐาน {complete_tasks}/{len(tasks)}; ยังไม่มี measured output ที่ promote ได้"
    )
    rows = [
        (
            "thesis",
            "myIS Research: SCOPE / AutoIndex",
            "คำถามหลักคือ representation ที่ยึดหลักฐานจะช่วย family-level patent retrieval ได้หรือไม่ เมื่อ retriever, evaluator และ budget คงที่",
        ),
        (
            "difficulty",
            "เหตุใดการค้น prior art จึงยาก",
            "สิทธิบัตรยาว ใช้ถ้อยคำหลากหลาย และหลักฐานอาจอยู่คนละส่วนของเอกสาร การประเมินจึงต้องแยก retrieval evidence ออกจากข้อสรุปทางกฎหมาย",
        ),
        (
            "boundary",
            "ขอบเขตข้อมูลและการประเมิน",
            "งานปัจจุบันเป็น CPU-only และ aggregate-only; ข้อมูล protected และ final confirmation ยังอยู่ใน Owner-local boundary",
        ),
        (
            "history",
            "เส้นทาง A → B → D → SCOPE",
            "บทเรียนจากงานเดิมชี้ให้ตรวจ candidate exposure และ headroom ก่อนเพิ่มความซับซ้อน ผลเดิมถูกเก็บเป็น historical/exposed และไม่ปะปนกับผลปัจจุบัน",
        ),
        (
            "architecture",
            "ระบบหลักฐานหนึ่งชุด หลายมุมมอง",
            "Control files และ immutable receipts สร้าง shared read model หนึ่งครั้ง แล้ว fan out ไป Dashboard, MLflow และ Obsidian ด้วย revision เดียวกัน",
        ),
        (
            "plan",
            "แผน P0–P4",
            phase_summary,
        ),
        (
            "delivered",
            "สิ่งที่ส่งมอบแล้ว",
            delivered,
        ),
        (
            "result",
            "ผลที่ตรวจสอบแล้วล่าสุด",
            latest_result,
        ),
        (
            "interpretation",
            "การแปลผลและข้อจำกัด",
            "หลักฐานปัจจุบันรองรับเฉพาะสถานะ recovery ของ P1 ยังไม่รองรับ measured claim, P2, final confirmation หรือ publication claim",
        ),
        (
            "next",
            "สถานะและการตัดสินใจถัดไป",
            f"{p1_state}. ขั้นถัดไป: {next_label}. D2 และ D3 ยังคงเป็น Owner-only decisions",
        ),
    ]
    return [
        {
            "screen_id": f"shared-{index:02d}-{screen_id}",
            "audience": audiences,
            "order": index,
            "title_th": title,
            "message_th": message,
            "visual_artifact_id": None,
            "evidence_ids": [],
            "safe_to_present": True,
        }
        for index, (screen_id, title, message) in enumerate(rows, start=1)
    ]


def write_read_model(repository_root: Path, output: Path | None = None) -> Path:
    root = repository_root.resolve()
    target = output or root / "projections" / "read-model" / "read-model.v2.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(build_read_model(root), ensure_ascii=True, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return target


def _p2_official_review_projection(root: Path) -> dict[str, Any]:
    """Validate and summarize the repository-safe three-round P2 static review."""

    audit_root = root / P2_OFFICIAL_REVIEW_ROOT
    missing = {
        "status": "not_recorded",
        "evidence_class": "static_contract_review",
        "claim_boundary": "engineering_provenance_only",
        "round_count": 0,
        "final_round": None,
        "final_verdict": None,
        "reviewed_commit": None,
        "fixture_pilot_contract_status": "not_reviewed",
        "fixture_pilot_executed": False,
        "protected_data_accessed": False,
        "measured_execution_performed": False,
        "rounds": [],
        "source": None,
    }
    if not audit_root.is_dir():
        return missing

    try:
        resolved_root = audit_root.resolve()

        def resolve_file(value: str) -> Path:
            relative = Path(value)
            if not value.strip() or relative.is_absolute() or ".." in relative.parts:
                raise ValueError("audit reference must be repository-relative")
            unresolved = audit_root / relative
            target = unresolved.resolve()
            target.relative_to(resolved_root)
            if unresolved.is_symlink() or not target.is_file():
                raise ValueError("audit reference must resolve to a regular file")
            return target

        checksums_path = resolve_file("SHA256SUMS.txt")
        checksums: dict[str, str] = {}
        json_payloads: dict[str, dict[str, Any]] = {}
        for raw_line in checksums_path.read_text(encoding="utf-8").splitlines():
            digest, separator, relative = raw_line.partition("  ")
            if (
                separator != "  "
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
            ):
                raise ValueError("invalid audit checksum line")
            path = resolve_file(relative)
            if _file_sha256(path) != digest or relative in checksums:
                raise ValueError("audit checksum mismatch")
            checksums[relative] = digest
            if path.suffix == ".json":
                payload = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("audit JSON must be an object")
                assert_aggregate_only(payload)
                json_payloads[relative] = payload

        index = json_payloads.get("index.json")
        if not index or index.get("schema_version") != "myis.official-review-index.v1":
            raise ValueError("official review index is missing or invalid")
        if (
            index.get("phase") != "P2_SCOPE_DEVELOPMENT"
            or index.get("status_at_close") != "ready_planned_not_measured"
        ):
            raise ValueError("official review boundary is invalid")
        runtime = index.get("review_runtime")
        expected_runtime = {
            "provider": "openai",
            "model": "gpt-5.6-sol",
            "codex_cli_version": "0.146.0",
            "sandbox": "read-only",
            "protected_data_accessed": False,
            "measured_execution_performed": False,
        }
        if not isinstance(runtime, dict) or any(
            runtime.get(field) != value for field, value in expected_runtime.items()
        ):
            raise ValueError("official review runtime provenance is invalid")
        raw_rounds = index.get("rounds")
        if not isinstance(raw_rounds, list) or [
            item.get("round") for item in raw_rounds if isinstance(item, dict)
        ] != [1, 2, 3]:
            raise ValueError("official review rounds must be exactly 1, 2, and 3")

        rounds: list[dict[str, Any]] = []
        for item in raw_rounds:
            if not isinstance(item, dict):
                raise ValueError("official review round must be an object")
            round_number = int(item["round"])
            metadata_relative = str(item["metadata"])
            result_relative = str(item["result"])
            prompt_relative = str(item["prompt"])
            if any(
                relative not in checksums
                for relative in (metadata_relative, result_relative, prompt_relative)
            ):
                raise ValueError(
                    "official review reference is absent from checksum manifest"
                )
            metadata = json_payloads.get(metadata_relative)
            result = json_payloads.get(result_relative)
            if not metadata or not result:
                raise ValueError("official review metadata or result is missing")
            if (
                metadata.get("schema_version") != "myis.official-review-metadata.v1"
                or result.get("schema_version") != "1.0"
            ):
                raise ValueError("official review schema mismatch")
            for field in ("round", "task_id", "verdict"):
                if metadata.get(field) != item.get(field) or result.get(
                    field
                ) != item.get(field):
                    raise ValueError("official review round identity mismatch")
            if metadata.get("reviewed_commit") != item.get("reviewed_commit"):
                raise ValueError("official review commit mismatch")
            reviewed_commit = str(item["reviewed_commit"])
            if len(reviewed_commit) != 40 or any(
                character not in "0123456789abcdef" for character in reviewed_commit
            ):
                raise ValueError("official review commit must be a Git SHA-1")
            if (
                metadata.get("prompt_sha256") != checksums[prompt_relative]
                or metadata.get("result_sha256") != checksums[result_relative]
            ):
                raise ValueError("official review metadata hash mismatch")
            if (
                metadata.get("protected_data_accessed") is not False
                or result.get("protected_data_accessed") is not False
            ):
                raise ValueError("official review crossed the protected-data boundary")
            if (
                metadata.get("measured_execution_performed") is not False
                or result.get("measured_execution_performed") is not False
            ):
                raise ValueError("official review performed measured execution")
            rounds.append(
                {
                    "round": round_number,
                    "task_id": str(item["task_id"]),
                    "verdict": str(item["verdict"]),
                    "reviewed_commit": reviewed_commit,
                    "invoked_at_utc": str(metadata.get("invoked_at_utc", "")),
                    "provider": str(metadata.get("provider", "")),
                    "model": str(metadata.get("model", "")),
                    "codex_cli_version": str(metadata.get("codex_cli_version", "")),
                    "sandbox": str(metadata.get("sandbox", "")),
                    "approval": str(metadata.get("approval", "")),
                    "source_provenance": str(metadata.get("source_provenance", "")),
                    "result_uri": f"{P2_OFFICIAL_REVIEW_ROOT.as_posix()}/{result_relative}",
                    "result_sha256": checksums[result_relative],
                }
            )

        boundary = index.get("final_boundary")
        if not isinstance(boundary, dict):
            raise ValueError("official review final boundary is missing")
        expected_boundary = {
            "fixture_pilot_executed": False,
            "measured_runs": 0,
            "candidate_count": 0,
            "selection_accesses": 0,
            "protected_data_accessed": False,
            "measured_execution_performed": False,
        }
        if any(
            boundary.get(field) != value for field, value in expected_boundary.items()
        ):
            raise ValueError("official review final boundary changed")
        final_round = rounds[-1]
        final_result = json_payloads[str(raw_rounds[-1]["result"])]
        if final_round["verdict"] == "accept" and (
            final_result.get("required_changes") != []
            or final_result.get("major_risks") != []
        ):
            raise ValueError(
                "accepted official review still contains blocking findings"
            )

        return {
            "status": "accepted_static_contract_review"
            if final_round["verdict"] == "accept"
            else "revision_required",
            "audit_id": str(index.get("audit_id", "")),
            "evidence_class": "static_contract_review",
            "claim_boundary": "engineering_provenance_only",
            "round_count": len(rounds),
            "final_round": final_round["round"],
            "final_verdict": final_round["verdict"],
            "reviewed_commit": final_round["reviewed_commit"],
            "fixture_pilot_contract_status": (
                "static_review_accepted_not_executed"
                if final_round["verdict"] == "accept"
                else "static_review_requires_revision"
            ),
            "fixture_pilot_executed": False,
            "protected_data_accessed": False,
            "measured_execution_performed": False,
            "rounds": rounds,
            "source": {
                "index_uri": f"{P2_OFFICIAL_REVIEW_ROOT.as_posix()}/index.json",
                "index_sha256": checksums["index.json"],
                "checksums_uri": f"{P2_OFFICIAL_REVIEW_ROOT.as_posix()}/SHA256SUMS.txt",
                "checksums_sha256": _file_sha256(checksums_path),
            },
        }
    except (
        KeyError,
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ):
        return {
            **missing,
            "status": "invalid_audit_bundle",
            "fixture_pilot_contract_status": "blocked_invalid_audit",
        }


def _p2_readiness_projection(
    root: Path, campaign_config: dict[str, Any]
) -> dict[str, Any]:
    """Read only validated P2 control/artifact metadata.

    A missing P2 package is a normal readiness state.  Invalid or incomplete
    P2 JSON is never promoted into the shared read model; only a schema-valid,
    self-hash-valid artifact contributes a pointer, count, or freeze state.
    """

    official_review = _p2_official_review_projection(root)
    fixture_pilot = _p2_fixture_projection(root)
    preflight = _p2_preflight_projection(root)
    candidate_proposal = _p2_candidate_proposal_projection(root)
    active_sources = _active_p2_sources(root)
    profile_path = root / active_sources["profile"]
    profile: dict[str, Any] = {}
    profile_sha256: str | None = None
    try:
        loaded = _load_yaml_like(profile_path)
        if (
            isinstance(loaded, dict)
            and loaded.get("schema_version") == "myis.p2-budget-profile.v1"
        ):
            profile = loaded
            profile_sha256 = canonical_sha256(profile)
    except (OSError, ValueError, TypeError):
        profile = {}

    configured = campaign_config.get("p2_execution", {})
    if not isinstance(configured, dict):
        configured = {}
    limits = (
        profile.get("limits")
        if isinstance(profile.get("limits"), dict)
        else configured.get("candidate_allocation", {})
    )
    runtime = (
        profile.get("runtime")
        if isinstance(profile.get("runtime"), dict)
        else configured.get("runtime", {})
    )
    allocation = (
        profile.get("candidate_allocation")
        if isinstance(profile.get("candidate_allocation"), dict)
        else configured.get("candidate_allocation", {})
    )
    stopping = (
        profile.get("stopping")
        if isinstance(profile.get("stopping"), dict)
        else configured.get("stopping", {})
    )
    resources = (
        profile.get("resources") if isinstance(profile.get("resources"), dict) else {}
    )

    campaign_root = root / "campaigns/scope-autoindex-v1"
    valid: list[tuple[Path, dict[str, Any]]] = []
    invalid_count = 1 if candidate_proposal["status"] == "invalid" else 0
    seen: set[Path] = set()
    for directory_name in P2_ARTIFACT_DIRS:
        directory = campaign_root / directory_name
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.json")):
            if path in seen or not any(
                token in path.stem.lower() for token in ("p2-", "p2_", ".p2")
            ):
                continue
            seen.add(path)
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                payload = json.loads(path.read_text(encoding="utf-8"))
                validated = validate_p2_artifact(payload, repository_root=root)
            except (
                OSError,
                UnicodeError,
                json.JSONDecodeError,
                P2ContractError,
                TypeError,
                ValueError,
            ):
                invalid_count += 1
                continue
            artifact_revision = validated.get("campaign_revision")
            if artifact_revision not in {None, profile.get("campaign_revision")}:
                continue
            if profile_sha256 and validated.get("budget_profile_sha256") not in {
                None,
                profile_sha256,
            }:
                invalid_count += 1
                continue
            valid.append((path, validated))

    by_schema: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    for path, payload in valid:
        by_schema.setdefault(str(payload.get("schema_version")), []).append(
            (path, payload)
        )

    def latest(schema_version: str) -> tuple[Path, dict[str, Any]] | None:
        values = by_schema.get(schema_version, [])
        return values[-1] if values else None

    package = latest("myis.p2-package.v1")
    valid_by_uri = {
        path.relative_to(root).as_posix(): payload for path, payload in valid
    }
    bundle: dict[str, dict[str, Any]] | None = None
    if package is not None:
        package_payload = package[1]

        def referenced(field: str) -> dict[str, Any] | None:
            value = package_payload.get(field)
            if value is None:
                return None
            if not isinstance(value, str) or value not in valid_by_uri:
                raise P2ContractError(
                    f"package {field} does not reference a validated P2 artifact"
                )
            return valid_by_uri[value]

        try:
            request_payload = referenced("request_uri")
            ledger_payload = referenced("candidate_ledger_uri")
            commitment_payload = referenced("baseline_commitment_uri")
            baseline_payload = referenced("baseline_reproduction_uri")
            freeze_payload = referenced("shortlist_freeze_uri")
            manifest_payload = referenced("manifest_uri")
            if any(
                item is None
                for item in (
                    request_payload,
                    ledger_payload,
                    commitment_payload,
                    baseline_payload,
                    freeze_payload,
                    manifest_payload,
                )
            ):
                raise P2ContractError(
                    "complete P2 package is missing a required artifact reference"
                )
            bundle = validate_p2_package_bundle(
                request=request_payload,
                ledger=ledger_payload,
                commitment=commitment_payload,
                baseline=baseline_payload,
                freeze=freeze_payload,
                selection=referenced("selection_uri"),
                manifest=manifest_payload,
                package=package_payload,
                repository_root=root,
            )
        except (P2ContractError, TypeError, ValueError):
            invalid_count += 1
            bundle = None

    ledger = bundle.get("ledger") if bundle else None
    commitment = bundle.get("commitment") if bundle else None
    baseline = bundle.get("baseline") if bundle else None
    freeze = bundle.get("freeze") if bundle else None
    selection = bundle.get("selection") if bundle else None
    manifest = bundle.get("manifest") if bundle else None
    measured_manifest = (
        manifest is not None
        and manifest.get("evidence_class") == "train_selection_measured"
        and manifest.get("status") in {"valid", "negative_development"}
    )
    freeze_valid = (
        bool(measured_manifest)
        and freeze is not None
        and freeze.get("status") == "validated_immutable"
        and freeze.get("selection_exposure_count") == 0
    )
    selection_count = (
        1
        if measured_manifest
        and selection is not None
        and selection.get("selection_exposure_count") == 1
        else 0
    )
    if invalid_count or fixture_pilot["status"] == "invalid":
        status = "blocked_invalid_artifact"
    elif measured_manifest:
        status = "measured"
    else:
        status = "ready_planned_not_measured"

    pointers: list[dict[str, Any]] = []
    if candidate_proposal["validated"]:
        pointers.append(
            {
                "schema_version": "myis.p2-candidate-freeze-proposal.v1",
                "uri": candidate_proposal["proposal_uri"],
                "sha256": candidate_proposal["proposal_sha256"],
            }
        )
    for path, payload in valid:
        self_hash_field = {
            "myis.p2-candidate-ledger.v1": "ledger_sha256",
            "myis.p2-baseline-commitment.v1": "commitment_sha256",
            "myis.p2-baseline-reproduction-receipt.v1": "receipt_sha256",
            "myis.p2-shortlist-freeze-receipt.v1": "receipt_sha256",
            "myis.p2-selection-receipt.v1": "receipt_sha256",
            "myis.p2-manifest.v1": "manifest_sha256",
            "myis.p2-package.v1": "package_sha256",
        }.get(str(payload.get("schema_version")))
        pointers.append(
            {
                "schema_version": payload.get("schema_version"),
                "uri": path.relative_to(root).as_posix(),
                "sha256": str(payload.get(self_hash_field))
                if self_hash_field
                else _file_sha256(path),
            }
        )

    p2_metrics: list[dict[str, Any]] = []
    if measured_manifest:
        raw_metrics = manifest.get("metrics", [])
        if isinstance(raw_metrics, list):
            for item in raw_metrics:
                if (
                    isinstance(item, dict)
                    and set(item).issubset(P2_METRIC_FIELDS)
                    and {"name", "value"} <= set(item)
                ):
                    p2_metrics.append(dict(item))

    review_source = (
        official_review.get("source")
        if isinstance(official_review.get("source"), dict)
        else {}
    )

    return {
        "status": status,
        "preflight_status": preflight["status"],
        "preflight": preflight,
        "candidate_proposal": candidate_proposal,
        "phase_id": "P2_SCOPE_DEVELOPMENT",
        "arm": "R1",
        "campaign_revision": profile.get("campaign_revision")
        or configured.get("campaign_revision"),
        "budget_profile_id": profile.get("profile_id") or configured.get("profile_id"),
        "budget_profile_sha256": profile_sha256,
        "measured": bool(measured_manifest),
        "measured_runs": 1 if measured_manifest else 0,
        "selection_accesses": selection_count,
        "candidate_count": int(ledger.get("candidate_count", 0))
        if measured_manifest and ledger
        else 0,
        "shortlist_count": len(freeze.get("candidate_ids", []))
        if measured_manifest and freeze
        else 0,
        "candidate_budget": {
            "max_candidates_total": limits.get("max_candidates_total"),
            "max_adaptive_candidates": limits.get("max_adaptive_candidates"),
            "max_adaptive_iterations": limits.get("max_adaptive_iterations"),
            "candidates_per_iteration": limits.get("candidates_per_iteration"),
            "max_index_builds": limits.get("max_index_builds"),
            "max_selection_finalists": limits.get("max_selection_finalists"),
            "selection_exposure_limit": limits.get("selection_exposure_limit"),
            "frozen_controls": allocation.get("frozen_controls"),
            "preregistered_patent_candidates": allocation.get(
                "preregistered_patent_candidates"
            ),
        },
        "runtime": {
            "max_wall_clock_seconds": runtime.get("max_wall_clock_seconds"),
            "measurement_budget_seconds": runtime.get("measurement_budget_seconds"),
            "overhead_reserve_seconds": runtime.get("overhead_reserve_seconds"),
            "per_candidate_timeout_seconds": runtime.get(
                "per_candidate_timeout_seconds"
            ),
            "prevent_system_sleep": runtime.get("prevent_system_sleep", False),
        },
        "stopping": {
            "min_iterations_before_early_stop": stopping.get(
                "min_iterations_before_early_stop"
            ),
            "no_improvement_patience": stopping.get("no_improvement_patience"),
            "selection_rule": stopping.get(
                "selection_rule", "strictly_greater_reject_ties"
            ),
            "whole_batch_admission": stopping.get("whole_batch_admission", False),
            "valid_reasons": stopping.get("valid_reasons", []),
        },
        "resources": {
            "paid_api_budget_usd": resources.get("paid_api_budget_usd", 0),
            "gpu_budget_usd": resources.get("gpu_budget_usd", 0),
            "network_model_download": resources.get("network_model_download", False),
            "provider_fallback": resources.get("provider_fallback", False),
            "proposer_mode": resources.get("proposer_mode", "disabled"),
        },
        "freeze_barrier": {
            "required": True,
            "status": "validated_immutable"
            if freeze_valid
            else "not_started"
            if freeze is None
            else "blocked",
            "candidate_ids_frozen": bool(freeze_valid),
            "selection_exposure_limit": limits.get("selection_exposure_limit", 1),
            "selection_exposure_count": selection_count,
            "mutation_after_selection": "forbidden",
        },
        "metrics": p2_metrics,
        "artifacts": pointers,
        "invalid_artifact_count": invalid_count,
        "claim_boundary": "no_measured_claim"
        if not measured_manifest
        else "train_selection_development_only",
        "source": {
            "profile": active_sources["profile"],
            "execution_envelope": active_sources["execution_envelope"],
            "campaign_revision": active_sources.get("campaign_revision"),
            "baseline_commitment_sha256": commitment.get("commitment_sha256")
            if commitment
            else None,
            "baseline_reproduction_receipt_sha256": baseline.get("receipt_sha256")
            if baseline
            else None,
            "official_review_index_sha256": review_source.get("index_sha256"),
            "fixture_receipt_sha256": fixture_pilot.get("receipt_sha256"),
            "fixture_manifest_sha256": fixture_pilot.get("execution_manifest_sha256"),
            "fixture_package_sha256": fixture_pilot.get("fixture_package_sha256"),
        },
        "official_review": official_review,
        "fixture_pilot": fixture_pilot,
    }


def _active_p2_sources(root: Path) -> dict[str, str]:
    legacy = {
        "profile": "control/budgets/p2-r1-primary-v1.yaml",
        "execution_envelope": "control/execution-envelope-p2.yaml",
    }
    source_path = root / "control/source-of-truth.yaml"
    if not source_path.is_file() or source_path.is_symlink():
        return legacy
    source = _load_yaml_like(source_path)
    records = source.get("records", []) if isinstance(source, dict) else []
    by_id = {
        str(item.get("id")): item
        for item in records
        if isinstance(item, dict) and item.get("id")
    }
    profile = by_id.get("p2_budget_profile", {}).get("authority")
    execution = (
        by_id.get("execution_boundary", {})
        .get("phase_mapping", {})
        .get("P2_SCOPE_DEVELOPMENT")
    )
    revision = by_id.get("p2_campaign_revision", {}).get("authority")
    if (
        "p2_budget_profile" not in by_id
        and "p2_campaign_revision" not in by_id
        and execution is None
    ):
        return legacy
    values = {
        "profile": profile,
        "execution_envelope": execution,
        "campaign_revision": revision,
    }
    for label, uri in values.items():
        if uri is None and label == "campaign_revision":
            continue
        if (
            not isinstance(uri, str)
            or not uri
            or Path(uri).is_absolute()
            or ".." in Path(uri).parts
        ):
            raise ValueError(f"active P2 {label} source is not repository-relative")
        path = root / uri
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"active P2 {label} source is missing or unsafe")
    return {key: str(value) for key, value in values.items() if value is not None}


def _p2_candidate_proposal_projection(root: Path) -> dict[str, Any]:
    """Project an Owner-review draft without promoting it into the measured ledger."""

    missing = {
        "status": "not_created",
        "adoption": "not_adopted",
        "proposal_uri": P2_CANDIDATE_PROPOSAL_PATH.as_posix(),
        "proposal_sha256": None,
        "validated": False,
        "frozen_controls": 0,
        "preregistered_candidates": 0,
        "registered_candidates": 0,
        "hash_locked_candidates": 0,
        "scientific_authority": False,
    }
    path = root / P2_CANDIDATE_PROPOSAL_PATH
    if not path.exists():
        return missing
    if path.is_symlink() or not path.is_file():
        return {**missing, "status": "invalid"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        active = _active_p2_sources(root)
        active_profile = _load_yaml_like(root / active["profile"])
        historical = payload.get("campaign_revision") != active_profile.get(
            "campaign_revision"
        )
        if historical:
            recorded_hash = str(payload.get("proposal_sha256", ""))
            unsigned = {
                key: value for key, value in payload.items() if key != "proposal_sha256"
            }
            assert_aggregate_only(payload)
            if recorded_hash != canonical_sha256(unsigned):
                raise P2ContractError(
                    "historical candidate proposal self-hash is invalid"
                )
            proposal = payload
        else:
            proposal = validate_p2_candidate_freeze_proposal(
                payload, repository_root=root
            )
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        P2ContractError,
        TypeError,
        ValueError,
    ):
        return {**missing, "status": "invalid"}
    controls = proposal.get("frozen_controls", [])
    candidates = proposal.get("preregistered_candidates", [])
    rows = [item for item in [*controls, *candidates] if isinstance(item, Mapping)]
    return {
        "status": str(proposal.get("status", "invalid")),
        "adoption": str(proposal.get("adoption", "not_adopted")),
        "proposal_uri": P2_CANDIDATE_PROPOSAL_PATH.as_posix(),
        "proposal_sha256": str(proposal.get("proposal_sha256")),
        "validated": True,
        "historical_superseded": historical,
        "frozen_controls": len(controls),
        "preregistered_candidates": len(candidates),
        "registered_candidates": sum(
            1 for item in rows if item.get("registered") is True
        ),
        "hash_locked_candidates": sum(
            1 for item in rows if item.get("hash_locked") is True
        ),
        "scientific_authority": False,
    }


def _p2_preflight_projection(root: Path) -> dict[str, Any]:
    """Project only the validated preflight state; never infer readiness from a preview."""

    missing = {
        "status": "not_started",
        "receipt_uri": P2_PREFLIGHT_RECEIPT_PATH.as_posix(),
        "receipt_sha256": None,
        "validated": False,
        "checks_passed": 0,
        "checks_failed": 0,
        "failure_codes": [],
        "measured_runs": 0,
        "candidate_count": 0,
        "shortlist_count": 0,
        "selection_accesses": 0,
        "safe_to_measure": False,
        "owner_approval_required": [
            "Owner confirms both protected store identities and permits read-only metadata preflight.",
            "Owner approves the four frozen controls and eight preregistered candidate definitions.",
            "Owner resolves any ambiguous SCOPE view, field, normalization, or aggregation definition before adoption.",
            "Owner approves the concrete compiler, config, retriever, and evaluator SHA-256 bindings before a measured request.",
            "Owner explicitly requests measured P2; this preflight does not create a request, baseline commitment, or selection exposure.",
        ],
    }
    path = root / P2_PREFLIGHT_RECEIPT_PATH
    if not path.exists():
        return missing
    if path.is_symlink() or not path.is_file():
        return {**missing, "status": "failed"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        receipt = validate_p2_preflight_receipt(payload, repository_root=root)
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        P2ContractError,
        TypeError,
        ValueError,
    ):
        return {**missing, "status": "failed"}
    checks = receipt.get("checks", [])
    counters = receipt.get("counters", {})
    status = str(receipt.get("status", "failed"))
    if status not in {"not_started", "passed_pending_owner", "failed"}:
        status = "failed"
    safe_to_measure = status == "passed_pending_owner" and all(
        item.get("status") == "passed" for item in checks if isinstance(item, Mapping)
    )
    return {
        "status": status,
        "receipt_uri": P2_PREFLIGHT_RECEIPT_PATH.as_posix(),
        "receipt_sha256": str(receipt.get("receipt_sha256")),
        "validated": True,
        "checks_passed": sum(
            1
            for item in checks
            if isinstance(item, Mapping) and item.get("status") == "passed"
        ),
        "checks_failed": sum(
            1
            for item in checks
            if isinstance(item, Mapping) and item.get("status") == "failed"
        ),
        "failure_codes": [str(item) for item in receipt.get("failure_codes", [])],
        "measured_runs": int(counters.get("measured_runs", 0)),
        "candidate_count": int(counters.get("candidate_count", 0)),
        "shortlist_count": int(counters.get("shortlist_count", 0)),
        "selection_accesses": int(counters.get("selection_accesses", 0)),
        "safe_to_measure": safe_to_measure,
        "owner_approval_required": [
            str(item) for item in receipt.get("owner_approval_required", [])
        ],
    }


def _p2_fixture_projection(root: Path) -> dict[str, Any]:
    """Project only validated aggregate fixture provenance, never synthetic ledgers."""

    missing = {
        "executed": False,
        "status": "not_executed",
        "evidence_class": "fixture",
        "scientific_authority": False,
        "claim_boundary": "no_measured_claim",
        "protected_data_accessed": False,
        "measured_execution_performed": False,
        "synthetic_candidates": 0,
        "synthetic_iterations": 0,
        "synthetic_shortlist": 0,
        "fixture_selection_exposures": 0,
        "receipt_uri": None,
        "receipt_sha256": None,
        "execution_manifest_uri": None,
        "execution_manifest_sha256": None,
        "fixture_package_sha256": None,
        "deterministic_rerun": "not_run",
        "canonical_hashes_match": False,
        "negative_checks_passed": False,
        "negative_check_count": 0,
    }
    receipt_path = root / P2_FIXTURE_RECEIPT_PATH
    manifest_path = root / P2_FIXTURE_MANIFEST_PATH
    if not receipt_path.exists() and not manifest_path.exists():
        return missing
    if (
        not receipt_path.is_file()
        or receipt_path.is_symlink()
        or not manifest_path.is_file()
        or manifest_path.is_symlink()
    ):
        return {**missing, "status": "invalid"}
    try:
        receipt_payload = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt = validate_fixture_receipt(receipt_payload, repository_root=root)
        manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest = validate_fixture_execution_manifest(
            manifest_payload, receipt=receipt
        )
        assert_aggregate_only(receipt)
        assert_aggregate_only(manifest)
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        P2FixtureError,
        TypeError,
        ValueError,
    ):
        return {**missing, "status": "invalid"}
    return {
        "executed": True,
        "status": "passed",
        "evidence_class": "fixture",
        "scientific_authority": False,
        "claim_boundary": "no_measured_claim",
        "protected_data_accessed": False,
        "measured_execution_performed": False,
        "synthetic_candidates": int(receipt["synthetic_candidates"]),
        "synthetic_iterations": int(receipt["synthetic_adaptive_iterations"]),
        "synthetic_shortlist": int(receipt["synthetic_shortlist_count"]),
        "fixture_selection_exposures": int(receipt["fixture_selection_exposures"]),
        "receipt_uri": P2_FIXTURE_RECEIPT_PATH.as_posix(),
        "receipt_sha256": str(receipt["receipt_sha256"]),
        "execution_manifest_uri": P2_FIXTURE_MANIFEST_PATH.as_posix(),
        "execution_manifest_sha256": str(manifest["manifest_sha256"]),
        "fixture_package_sha256": str(receipt["fixture_package_sha256"]),
        "deterministic_rerun": str(receipt["deterministic_rerun"]),
        "canonical_hashes_match": bool(receipt["canonical_hashes_match"]),
        "negative_checks_passed": bool(receipt["negative_checks_passed"]),
        "negative_check_count": int(receipt["negative_check_count"]),
    }


def _load_manifests(directory: Path) -> list[dict[str, Any]]:
    if not directory.is_dir():
        return []
    values: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(value, dict):
            continue
        try:
            values.append(manifest_round_trip(value))
        except ValueError:
            continue
    return values


def _load_receipts(
    directory: Path,
    *,
    invalidated_receipt_hashes: set[str] | None = None,
) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    invalidated = invalidated_receipt_hashes or set()
    if not directory.is_dir():
        return values
    for path in sorted(directory.glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(value, dict):
            continue
        try:
            receipt = validate_receipt(value)
        except (OwnerLocalContractError, ValueError):
            continue
        if str(receipt.get("receipt_sha256", "")) in invalidated:
            continue
        values.append(receipt)
    return values


def _load_legacy_disposition(root: Path) -> dict[str, Any]:
    path = root / LEGACY_DISPOSITION_RELATIVE_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict) or set(payload) != LEGACY_DISPOSITION_KEYS:
        return {}
    if (
        payload.get("schema_version") != "myis.evidence-disposition.v1"
        or payload.get("status") != "historical_invalid_superseded"
        or payload.get("evidence_class") != "historical_invalid"
        or payload.get("promotable") is not False
    ):
        return {}
    unsigned = {key: value for key, value in payload.items() if key != "record_sha256"}
    if sha256(canonical_json(unsigned)) != payload.get("record_sha256"):
        return {}
    source_uri = payload.get("source_uri")
    if not isinstance(source_uri, str):
        return {}
    try:
        source = (root / source_uri).resolve(strict=True)
        source.relative_to(root)
    except (OSError, ValueError):
        return {}
    if (
        source.is_symlink()
        or not source.is_file()
        or not _legacy_file_commitment_matches(
            source, str(payload.get("source_file_sha256", ""))
        )
    ):
        return {}
    invalidation = payload.get("invalidation_evidence")
    if not isinstance(invalidation, dict) or set(invalidation) != {"uri", "sha256"}:
        return {}
    try:
        audit = (root / str(invalidation["uri"])).resolve(strict=True)
        audit.relative_to(root)
    except (OSError, ValueError):
        return {}
    if (
        audit.is_symlink()
        or not audit.is_file()
        or not _legacy_file_commitment_matches(
            audit, str(invalidation.get("sha256", ""))
        )
    ):
        return {}
    if not isinstance(payload.get("reason_codes"), list) or not payload["reason_codes"]:
        return {}
    return payload


def _load_validation_reports(directory: Path) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    if not directory.is_dir():
        return values
    for path in sorted(directory.glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            validate_validation_report(value)
        except (
            OSError,
            json.JSONDecodeError,
            ManifestValidationError,
            TypeError,
            ValueError,
        ):
            continue
        values.append(value)
    return values


def validated_p1_matrix(
    manifests: list[dict[str, Any]],
    receipts: list[dict[str, Any]],
    validation_reports: list[dict[str, Any]] | None = None,
) -> list[dict[str, dict[str, Any]]]:
    """Return P1 facts only when the full arm/split/scope matrix is committed."""

    reports = validation_reports or []
    valid_manifest_hashes = {
        str(report.get("manifest_sha256", ""))
        for report in reports
        if report.get("status") == "valid"
    }
    pairs = [
        pair
        for pair in validated_p1_pairs(manifests, receipts)
        if str(pair["manifest"].get("manifest_sha256", "")) in valid_manifest_hashes
    ]
    ordered = sorted(pairs, key=lambda item: str(item["manifest"]["run_id"]))
    return ordered if _has_complete_p1_matrix(ordered) else []


def validated_p1_pairs(
    manifests: list[dict[str, Any]], receipts: list[dict[str, Any]]
) -> list[dict[str, dict[str, Any]]]:
    """Return individually validated P1 manifest/receipt pairs for additive mirrors."""

    valid_manifests: list[dict[str, Any]] = []
    for manifest in manifests:
        try:
            valid_manifests.append(manifest_round_trip(manifest))
        except (TypeError, ValueError):
            continue
    valid_receipts: list[dict[str, Any]] = []
    for receipt in receipts:
        try:
            valid_receipts.append(validate_receipt(receipt))
        except (OwnerLocalContractError, TypeError, ValueError):
            continue
    receipts_by_sha = {
        str(receipt.get("receipt_sha256", "")): receipt for receipt in valid_receipts
    }
    invalidated_receipts = {
        str(manifest.get("receipt_sha256", ""))
        for manifest in valid_manifests
        if _is_p1_manifest(manifest) and manifest.get("status") != "valid"
    }
    pairs: list[dict[str, dict[str, Any]]] = []
    for manifest in valid_manifests:
        if not _is_p1_manifest(manifest) or manifest.get("status") != "valid":
            continue
        receipt_sha = str(manifest.get("receipt_sha256", ""))
        receipt = receipts_by_sha.get(receipt_sha)
        if receipt_sha in invalidated_receipts or not _is_accepted_p1_receipt(receipt):
            continue
        if not _manifest_metrics_match_receipt(manifest, receipt):
            continue
        pairs.append({"manifest": manifest, "receipt": receipt})
    return sorted(pairs, key=lambda item: str(item["manifest"]["run_id"]))


def _is_p1_manifest(manifest: dict[str, Any]) -> bool:
    return (
        manifest.get("campaign_id") == "scope-autoindex-v1"
        and manifest.get("evidence_class") == "train_selection_measured"
        and manifest.get("stage") in {"train", "selection"}
    )


def _is_accepted_p1_receipt(receipt: dict[str, Any] | None) -> bool:
    return bool(receipt) and (
        receipt.get("status") == "accepted"
        and not receipt.get("blockers")
        and receipt.get("decision_id") == "P1_CPU_EXECUTION_ENVELOPE"
        and receipt.get("phase_id") == "P1_CPU_BASELINE"
        and receipt.get("stage") == "train_selection"
    )


def _manifest_metrics_match_receipt(
    manifest: dict[str, Any], receipt: dict[str, Any]
) -> bool:
    metrics = manifest.get("metrics")
    receipt_metrics = receipt.get("metrics")
    if (
        not isinstance(metrics, list)
        or not metrics
        or not isinstance(receipt_metrics, list)
    ):
        return False
    arm = _manifest_arm(manifest)
    split = manifest.get("stage")
    if arm not in P1_ARMS or split not in P1_SPLITS:
        return False
    if len(metrics) != len(P1_SCOPES):
        return False
    manifest_rows = _metric_rows(metrics, arm, split)
    receipt_rows = _metric_rows(receipt_metrics, arm, split)
    if manifest_rows is None or receipt_rows is None:
        return False
    return {canonical_json(row) for row in manifest_rows} == {
        canonical_json(row) for row in receipt_rows
    }


def _has_complete_p1_matrix(pairs: list[dict[str, dict[str, Any]]]) -> bool:
    """Require R0/R0-W x train/selection with exactly ALL/IN/OUT each."""

    slots: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}
    for pair in pairs:
        manifest = pair["manifest"]
        slot = (_manifest_arm(manifest), str(manifest.get("stage", "")))
        if slot[0] not in P1_ARMS or slot[1] not in P1_SPLITS or slot in slots:
            return False
        slots[slot] = pair
    expected_slots = {(arm, split) for arm in P1_ARMS for split in P1_SPLITS}
    if set(slots) != expected_slots:
        return False
    receipt_hashes = {
        str(pair["receipt"].get("receipt_sha256", "")) for pair in slots.values()
    }
    return len(receipt_hashes) == 1


def _manifest_arm(manifest: dict[str, Any]) -> str:
    method = manifest.get("method", {})
    if not isinstance(method, dict):
        return ""
    return str(method.get("arm_id") or method.get("arm") or "")


def _metric_rows(
    metrics: list[Any], arm: str, split: str
) -> list[dict[str, Any]] | None:
    rows = [
        row
        for row in metrics
        if isinstance(row, dict) and row.get("arm") == arm and row.get("split") == split
    ]
    if (
        len(rows) != len(P1_SCOPES)
        or {str(row.get("scope", "")) for row in rows} != P1_SCOPES
    ):
        return None
    if any(set(row) != P1_ACCEPTED_METRIC_FIELDS for row in rows):
        return None
    return rows


def _registration_matches_p1_pair(
    registration: dict[str, Any],
    pairs: list[dict[str, dict[str, Any]]],
    package_review: dict[str, Any],
) -> bool:
    if registration.get("schema_version") == "myis.p1-mlflow-registration.v2":
        children = registration.get("children")
        if not isinstance(children, list) or len(children) != 4:
            return False
        expected = {
            (pair["manifest"]["run_id"], pair["manifest"]["manifest_sha256"])
            for pair in pairs
        }
        observed = {
            (child.get("source_run_id"), child.get("source_manifest_sha256"))
            for child in children
            if isinstance(child, dict)
        }
        receipt_hashes = {pair["receipt"]["receipt_sha256"] for pair in pairs}
        return (
            observed == expected
            and receipt_hashes == {registration.get("source_receipt_sha256")}
            and bool(package_review)
            and registration.get("package_sha256")
            == package_review.get("package_sha256")
        )
    return False


def _validated_p1_package_review(
    root: Path, pairs: list[dict[str, dict[str, Any]]]
) -> dict[str, Any]:
    """Require one hash-bound four-slot package and a clean artifact-only rigor review."""

    manifest_hashes = {pair["manifest"]["manifest_sha256"] for pair in pairs}
    receipt_hashes = {pair["receipt"]["receipt_sha256"] for pair in pairs}
    if len(manifest_hashes) != 4 or len(receipt_hashes) != 1:
        return {}
    package_directory = root / "campaigns/scope-autoindex-v1/packages"
    review_directory = root / "outputs/audits/rigor"
    for package_path in (
        sorted(package_directory.glob("*.package.json"))
        if package_directory.is_dir()
        else ()
    ):
        try:
            package = load_package(package_path, root)
        except (DapfamP1Error, OSError, json.JSONDecodeError, ValueError):
            continue
        slots = package.get("slots")
        if (
            package.get("receipt_sha256") not in receipt_hashes
            or not isinstance(slots, list)
            or {slot.get("manifest_sha256") for slot in slots if isinstance(slot, dict)}
            != manifest_hashes
        ):
            continue
        relative_package = package_path.relative_to(root).as_posix()
        package_file_hash = _file_sha256(package_path)
        for review_path in (
            sorted(review_directory.rglob("*.json"))
            if review_directory.is_dir()
            else ()
        ):
            try:
                review = json.loads(review_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if (
                not isinstance(review, dict)
                or review.get("schema_version") != "myis.rigor-review.v1"
            ):
                continue
            governance = review.get("governance")
            findings = review.get("findings")
            if (
                review.get("review_status") == "complete"
                and review.get("artifact_path") == relative_package
                and review.get("artifact_sha256") == package_file_hash
                and isinstance(governance, dict)
                and governance.get("approval_valid") is True
                and governance.get("split_isolation_valid") is True
                and governance.get("gate_order_valid") is True
                and governance.get("budget_valid") is True
                and governance.get("manifest_integrity_valid") is True
                and governance.get("blocking_findings") == []
                and isinstance(findings, list)
                and not any(
                    isinstance(item, dict) and item.get("severity") == "critical"
                    for item in findings
                )
            ):
                overall = (
                    review.get("overall")
                    if isinstance(review.get("overall"), dict)
                    else {}
                )
                return {
                    "package_id": package["package_id"],
                    "package_uri": relative_package,
                    "package_sha256": package["package_sha256"],
                    "package_file_sha256": package_file_hash,
                    "review_id": str(review.get("review_id", review_path.stem)),
                    "review_uri": review_path.relative_to(root).as_posix(),
                    "review_sha256": _file_sha256(review_path),
                    "grade": overall.get("grade"),
                    "mean_score": overall.get("mean_score"),
                }
    return {}


def _dataset_projection(
    root: Path, receipts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if receipts:
        contract_path = root / "control/assets/dapfam-p1-source.v1.json"
        try:
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            contract = {}
        if (
            isinstance(contract, dict)
            and contract.get("schema_version") == "myis.dapfam-p1-source.v1"
        ):
            receipt = receipts[0]
            counts = receipt.get("aggregate_counts", {})
            lineage = receipt.get("lineage_hashes", {})
            return [
                {
                    "dataset_id": "DAPFAM-FAMILY-CORPUS",
                    "role": "family-corpus",
                    "representation": "one full TAC document per family",
                    "classification": "measured-source",
                    "counts": {
                        "families": counts.get("families"),
                        "documents": counts.get("r0_documents"),
                    },
                    "sha256": lineage.get("corpus_sha256"),
                    "protection": "owner-local-only",
                },
                {
                    "dataset_id": "DAPFAM-QUERY-SET",
                    "role": "query-set",
                    "representation": "TAC train/selection queries",
                    "classification": "measured-source",
                    "counts": {
                        "queries": counts.get("queries"),
                        "train": counts.get("train_queries"),
                        "selection": counts.get("selection_queries"),
                        "final_closed": counts.get("final_queries"),
                    },
                    "sha256": lineage.get("query_sha256"),
                    "protection": "owner-local-only",
                },
                {
                    "dataset_id": "DAPFAM-RELEVANCE-LABELS",
                    "role": "relevance-labels",
                    "representation": "positive family relations with released IN/OUT labels",
                    "classification": "measured-source",
                    "counts": {
                        "positive": counts.get("positive_relations"),
                        "in": counts.get("positive_in_relations"),
                        "out": counts.get("positive_out_relations"),
                    },
                    "sha256": lineage.get("qrels_sha256"),
                    "protection": "owner-local-only",
                },
                {
                    "dataset_id": "DAPFAM-R0-CANDIDATES",
                    "role": "r0-candidate",
                    "representation": "full TAC family document",
                    "classification": "measured-derived",
                    "counts": {"documents": counts.get("r0_documents")},
                    "sha256": receipt.get("aggregate_hashes", {}).get("r0_index"),
                    "protection": "external-derived-store",
                },
                {
                    "dataset_id": "DAPFAM-R0W-CANDIDATES",
                    "role": "r0-w-candidate",
                    "representation": "non-overlapping 512-token full TAC windows with family MaxP",
                    "classification": "measured-derived",
                    "counts": {"windows": counts.get("r0w_windows")},
                    "sha256": receipt.get("aggregate_hashes", {}).get("r0-w_index"),
                    "protection": "external-derived-store",
                },
            ]
    inventory_path = root / "evidence" / "legacy-dapfam-inventory.v1.json"
    if not inventory_path.is_file():
        return []
    try:
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    assets = inventory.get("assets", []) if isinstance(inventory, dict) else []
    by_path = {str(item.get("path")): item for item in assets if isinstance(item, dict)}
    receipt = receipts[0] if receipts else {}
    counts = receipt.get("aggregate_counts", {}) if isinstance(receipt, dict) else {}
    hashes = receipt.get("aggregate_hashes", {}) if isinstance(receipt, dict) else {}

    def asset(
        asset_id: str, path: str, role: str, representation: str, classification: str
    ) -> dict[str, Any]:
        row = by_path.get(path, {})
        return {
            "dataset_id": asset_id,
            "role": role,
            "representation": representation,
            "classification": classification,
            "bytes": row.get("bytes"),
            "sha256": row.get("sha256"),
            "protection": "owner-local-only"
            if ("qrel" in path or "quer" in path)
            else "metadata-safe",
        }

    rows = [
        asset(
            "DAPFAM-FAMILY-CORPUS",
            "processed/dapfam/patents.jsonl",
            "family-corpus",
            "patent family records",
            "reusable-after-certification",
        ),
        asset(
            "DAPFAM-QUERY-SET",
            "processed/dapfam/queries.jsonl",
            "query-set",
            "TAC query records",
            "reusable-after-certification",
        ),
        asset(
            "DAPFAM-RELEVANCE-LABELS",
            "processed/dapfam/qrels.tsv",
            "relevance-labels",
            "family relevance labels",
            "reusable-after-certification",
        ),
        asset(
            "DAPFAM-R0-CANDIDATES",
            "processed/dapfam/chunks_doc.jsonl",
            "r0-candidate",
            "one document per family candidate",
            "reusable-after-certification",
        ),
        asset(
            "DAPFAM-R0W-CANDIDATES",
            "processed/retrieval/dapfam_citation_controlled_tac512/corpus_tac_passages.jsonl",
            "r0-w-candidate",
            "TAC512 passages with family MaxP",
            "reusable-after-certification",
        ),
        asset(
            "DAPFAM-R1-REFERENCE",
            "processed/dapfam/chunks_section.jsonl",
            "r1-reference",
            "section units",
            "historical-reference",
        ),
        asset(
            "DAPFAM-INCOMPATIBLE",
            "processed/dapfam/chunks_element.jsonl",
            "incompatible",
            "element units",
            "incompatible",
        ),
    ]
    rows[0]["counts"] = {
        "patents": counts.get("patents"),
        "families": counts.get("patents"),
    }
    rows[1]["counts"] = {"queries": counts.get("queries")}
    rows[2]["sha256"] = next(
        (
            str(value)
            for key, value in hashes.items()
            if "qrels" in str(key) and str(key).endswith("sha256")
        ),
        None,
    )
    rows[3]["counts"] = {"documents": counts.get("r0_documents")}
    rows[4]["counts"] = {"passages": counts.get("r0w_passages")}
    rows[5]["constraint"] = "reference only; not active R1 main"
    rows[6]["constraint"] = "exceeds four-unit DAPFAM limit; never active R1 main"
    return rows


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    values: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if isinstance(value, dict):
            values.append(value)
    return values


def _load_optional_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _file_sha256(path: Path) -> str:
    if not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _legacy_file_commitment_matches(path: Path, expected: str) -> bool:
    """Keep the historical Windows receipt bound across Git LF checkouts."""

    if not path.is_file() or path.is_symlink():
        return False
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() == expected:
        return True
    crlf = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return hashlib.sha256(crlf).hexdigest() == expected


@lru_cache(maxsize=64)
def _tracked_history_commitment_matches(
    repository_root: Path, relative_path: str, expected: str
) -> bool:
    """Validate an immutable historical binding after a tracked file evolves."""

    root = repository_root.resolve()
    path = (root / relative_path).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return False
    if _legacy_file_commitment_matches(path, expected):
        return True
    try:
        history = subprocess.run(
            ["git", "log", "--all", "--format=%H", "--", relative_path],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        for commit in history:
            blob = subprocess.run(
                ["git", "show", f"{commit}:{relative_path}"],
                cwd=root,
                check=True,
                capture_output=True,
            ).stdout
            if hashlib.sha256(blob).hexdigest() == expected:
                return True
            crlf = blob.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            if hashlib.sha256(crlf).hexdigest() == expected:
                return True
    except (OSError, subprocess.SubprocessError):
        return False
    return False


def _load_yaml_like(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError:
        return {}
    if not path.is_file():
        return {}
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _source_commit_metadata(root: Path) -> tuple[str, str]:
    try:
        completed = subprocess.run(
            ["git", "log", "-1", "--format=%H%n%cI", "--", *PROJECTION_SOURCE_PATHS],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        commit, timestamp = completed.stdout.strip().splitlines()[:2]
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return commit, parsed.astimezone(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        )
    except (OSError, subprocess.SubprocessError, ValueError):
        return "0" * 40, "1970-01-01T00:00:00Z"


def _publication_readiness(
    root: Path,
    p1_pairs: list[dict[str, dict[str, Any]]],
    decisions: list[dict[str, Any]],
    legacy_disposition: dict[str, Any],
) -> dict[str, Any]:
    checks = [
        {
            "id": "canonical_run_manifest",
            "status": "pass" if p1_pairs else "blocked",
            "source": "campaigns/scope-autoindex-v1/manifests",
        },
        {
            "id": "owner_local_aggregate",
            "status": "pass" if p1_pairs else "blocked",
            "source": "campaigns/scope-autoindex-v1/evidence",
        },
        {
            "id": "d2_open_final",
            "status": "pass"
            if any(
                item.get("decision_id") == "D2_OPEN_FINAL"
                and item.get("status") == "approved"
                for item in decisions
            )
            else "blocked",
            "source": "control/decisions/ledger.jsonl",
        },
        {
            "id": "live_venue_check",
            "status": "unknown",
            "source": "Owner/live venue verification",
        },
        {
            "id": "prior_publication_status",
            "status": "unknown",
            "source": "Owner publication declaration",
        },
        {
            "id": "paper_build_hash_closure",
            "status": "blocked",
            "source": "03_Paper/publications/isai-nlp-2026",
        },
        {
            "id": "historical_final_872_exposure",
            "status": "blocked"
            if legacy_disposition
            or any(
                pair["receipt"]
                .get("historical_exposure", {})
                .get("active_final_872_global_untouched")
                == "not_claimable"
                for pair in p1_pairs
            )
            else "unknown",
            "source": "owner-local historical exposure audit",
        },
    ]
    status = "ready" if all(item["status"] == "pass" for item in checks) else "blocked"
    return {
        "schema_version": "myis.publication-readiness.v1",
        "status": status,
        "checks": checks,
    }
