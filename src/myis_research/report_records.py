"""Hash-bound Phase and Task report records for repository-safe projections."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from .projections.read_model import canonical_json, sha256

REPORT_SCHEMA = "myis.phase-task-report.v1"
REPORT_INDEX_SCHEMA = "myis.phase-task-report-index.v1"
REPORT_ROOT = Path("projections/reports")
P2_PREFLIGHT_INITIAL_AUDIT = (
    "outputs/audits/rigor/p2-preflight-completion-audit-20260802.json"
)
P2_PREFLIGHT_REPAIR_AUDIT = (
    "outputs/audits/rigor/p2-preflight-completion-repair-20260802.json"
)
P2_REPORT_BYTE_INITIAL_AUDIT = (
    "outputs/audits/rigor/p2-preflight-report-byte-drift-audit-20260802.json"
)
P2_REPORT_BYTE_REPAIR_AUDIT = (
    "outputs/audits/rigor/p2-preflight-report-byte-drift-repair-20260802.json"
)
P2_PROJECTION_SOURCE_INITIAL_AUDIT = (
    "outputs/audits/rigor/p2-preflight-projection-source-hash-drift-audit-20260802.json"
)
P2_PROJECTION_SOURCE_REPAIR_AUDIT = "outputs/audits/rigor/p2-preflight-projection-source-hash-drift-repair-20260802.json"
P2_TRACKED_OWNER_PATH_INITIAL_AUDIT = (
    "outputs/audits/rigor/p2-preflight-tracked-owner-path-audit-20260802.json"
)
P2_TRACKED_OWNER_PATH_REPAIR_AUDIT = (
    "outputs/audits/rigor/p2-preflight-tracked-owner-path-repair-20260802.json"
)
P2_RUNTIME_INTERRUPTION_AUDIT = (
    "outputs/audits/rigor/p2-runtime-resilience-v1-interruption-20260803.json"
)
P2_RUNTIME_RECOVERY_AUDIT = (
    "outputs/audits/rigor/p2-runtime-resilience-v2-recovery-20260803.json"
)
P2_RUNTIME_LINUX_CI_FAILURE_AUDIT = (
    "outputs/audits/rigor/p2-runtime-resilience-v2-linux-ci-failure-20260803.json"
)
P2_RUNTIME_LINUX_CI_REPAIR_AUDIT = (
    "outputs/audits/rigor/p2-runtime-resilience-v2-linux-ci-repair-20260803.json"
)
P2_RUNTIME_CLEAN_CHECKOUT_FAILURE_AUDIT = (
    "outputs/audits/rigor/p2-runtime-resilience-v2-clean-checkout-drift-20260803.json"
)
P2_RUNTIME_CLEAN_CHECKOUT_REPAIR_AUDIT = (
    "outputs/audits/rigor/p2-runtime-resilience-v2-clean-checkout-repair-20260803.json"
)
P2_RUNTIME_INDEPENDENT_REVISE_AUDIT = "outputs/audits/rigor/p2-runtime-resilience-v2-independent-verifier-revise-20260803.json"
P2_RUNTIME_INDEPENDENT_ACCEPT_AUDIT = "outputs/audits/rigor/p2-runtime-resilience-v2-independent-verifier-accept-20260803.json"
A010_RIGOR_REVISE_AUDIT = (
    "outputs/audits/rigor/a0.10-legacy-code-harvest-independent-revise-20260804.json"
)
A010_RIGOR_ACCEPT_AUDIT = (
    "outputs/audits/rigor/a0.10-legacy-code-harvest-independent-accept-20260804.json"
)
A12_V3_PROJECTION_STABILITY_REPAIR_AUDIT = (
    "outputs/audits/rigor/a1.2-v3-projection-stability-repair-20260806.json"
)
_FORBIDDEN = re.compile(
    r"(?:query_ids?|split_membership|per_query(?:_outcomes?)?|rankings|"
    r"raw_provider_payload|credentials?|api_keys?|password|secret)",
    re.IGNORECASE,
)
_ABSOLUTE = re.compile(r"(?:[A-Za-z]:[\\/]|/Users/|/home/)", re.IGNORECASE)


def _schema() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[2] / "schemas/phase-task-report.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _hash_file(root: Path, relative: str) -> str | None:
    path = root / relative
    try:
        return sha256(path.read_bytes()) if path.is_file() else None
    except OSError:
        return None


def _lifecycle(value: Any) -> str:
    value = str(value)
    if value in {"complete", "measured"}:
        return "completed"
    if value in {
        "in_progress",
        "active",
        "executable",
        "a1_1_complete_a1_2_contract_locked",
        "a1_2_contract_scaffold_complete_launch_locked",
        "a1_2_vast_4x3090_preflight_prepared_launch_locked",
        "a1_2_runtime_minimal_direct_base_preflight_prepared_launch_locked",
        "a1_2_live_preflight_correction_prepared_launch_locked",
        "a1_2_live_preflight_same_instance_repair_prepared_launch_locked",
        "a1_2_live_preflight_validation_complete_bundle_prepared_launch_locked",
        "a1_2_live_preflight_execution_lifecycle_prepared_launch_locked",
        "a1_2_live_synthetic_preflight_pass_owner_disposition_pending_launch_locked",
        "a1_2_live_synthetic_preflight_closed_provider_destroyed_launch_locked",
        "a1_2_scientific_execution_adoption_request_prepared_owner_review_launch_locked",
        "synthetic_preflight_closed_provider_destroyed_scientific_execution_locked",
    }:
        return "active"
    if value in {
        "blocked",
        "blocked_until_p1",
        "contract_scaffold_complete_launch_locked",
        "a1_2_v16_r13_failed_closed_retry_required",
        "a1_2_terminal_failed_closed_retry_required",
    } or value.startswith("locked"):
        return "blocked"
    return "planned"


def _next_action(model: Mapping[str, Any]) -> str:
    armindex = (
        model.get("armindex", {}) if isinstance(model.get("armindex"), Mapping) else {}
    )
    next_command = str(armindex.get("next_command", "")).strip()
    if next_command:
        return next_command
    inbox = model.get("owner_inbox", [])
    if isinstance(inbox, list) and inbox and isinstance(inbox[0], Mapping):
        label = str(inbox[0].get("label", "")).strip()
        if label:
            return label
    return "Owner-local P2 measured preflight"


def _artifact(
    *,
    artifact_id: str,
    title: str,
    artifact_type: str,
    evidence_class: str,
    scientific_authority: bool,
    safe_uri: str,
    content_sha256: str | None,
    validation_status: str = "validated",
    explanation: str,
    producing_phase_id: str = "",
    producing_task_id: str = "",
    retention_class: str = "repository_safe",
    parent_artifact_hashes: Mapping[str, str] | None = None,
    child_artifact_ids: list[str] | None = None,
    child_artifact_hashes: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "title": title,
        "artifact_type": artifact_type,
        "evidence_class": evidence_class,
        "scientific_authority": scientific_authority,
        "safe_uri": safe_uri,
        "content_sha256": content_sha256,
        "validation_status": validation_status,
        "producing_phase_id": producing_phase_id,
        "producing_task_id": producing_task_id,
        "retention_class": retention_class,
        "parent_artifact_ids": [],
        "parent_artifact_hashes": dict(parent_artifact_hashes or {}),
        "child_artifact_ids": list(child_artifact_ids or []),
        "child_artifact_hashes": dict(child_artifact_hashes or {}),
        "explanation": explanation,
    }


def _artifacts(
    root: Path,
    model: Mapping[str, Any],
    phase_id: str,
    task_id: str | None = None,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if phase_id == "A2_PER_ARM_AUTOINDEX":
        freeze = model.get("armindex", {}).get("a2_candidate_freeze", {})
        if not isinstance(freeze, Mapping) or freeze.get("validated") is not True:
            return result
        for artifact_id, title, artifact_type, uri_key, sha_key, explanation in (
            (
                "a2-five-arm-candidate-manifest-v1",
                "A2 immutable five-arm candidate manifest",
                "manifest",
                "manifest_uri",
                "manifest_file_sha256",
                "Binds exactly 40 matched and 12 dormant reserve candidates before measurement.",
            ),
            (
                "a2-five-arm-candidate-freeze-receipt-v1",
                "A2 candidate-freeze receipt",
                "receipt",
                "freeze_receipt_uri",
                "freeze_receipt_file_sha256",
                "Records the validated immutable freeze, Official identity, and zero measured A2 work.",
            ),
            (
                "a2-five-arm-candidate-freeze-lock-v1",
                "A2 candidate-freeze lock",
                "lock",
                "lock_uri",
                "lock_file_sha256",
                "Rejects proposer and reviewer mutation after the premeasurement freeze.",
            ),
            (
                "a2-official-codex-smoke-receipt-v2",
                "Official Codex bridge smoke receipt",
                "receipt",
                "smoke_receipt_uri",
                "smoke_receipt_file_sha256",
                "Binds the accepted synthetic smoke to the observed Official model and runtime identity.",
            ),
            (
                "a2-official-credit-preflight-receipt-v1",
                "Official Codex credit preflight receipt",
                "receipt",
                "credit_preflight_receipt_uri",
                "credit_preflight_receipt_file_sha256",
                "Records the pre-generation model, plan, availability, reset time, and non-limited state by safe aggregate.",
            ),
            (
                "a2-official-credit-closeout-correction-v1",
                "Official Codex credit closeout correction",
                "receipt",
                "credit_correction_receipt_uri",
                "credit_correction_receipt_file_sha256",
                "Additively identifies the chronological reviewer-final and post-freeze credit snapshots without changing frozen bytes.",
            ),
            (
                "a2-independent-freeze-audit-v1",
                "Independent A2 candidate-freeze audit",
                "audit",
                "independent_audit_receipt_uri",
                "independent_audit_receipt_file_sha256",
                "Records the independent identity, 40+12 universe, freeze-hash, credit, and zero-measured-work audit.",
            ),
            (
                "a2-official-final-credit-check-v1",
                "Official Codex post-audit final credit check",
                "receipt",
                "final_credit_receipt_uri",
                "final_credit_receipt_file_sha256",
                "Records the final model, plan, usage, reset time, and non-limited state after the independent audit.",
            ),
        ):
            if not freeze.get(uri_key) or not freeze.get(sha_key):
                continue
            result.append(
                _artifact(
                    artifact_id=artifact_id,
                    title=title,
                    artifact_type=artifact_type,
                    evidence_class="engineering_validation",
                    scientific_authority=False,
                    safe_uri=str(freeze[uri_key]),
                    content_sha256=str(freeze[sha_key]),
                    explanation=explanation,
                    producing_phase_id="A2_PER_ARM_AUTOINDEX",
                    producing_task_id="OFFICIAL_CODEX_BRIDGE_AND_CANDIDATE_FREEZE",
                )
            )
        readiness = model.get("armindex", {}).get("a2_execution_readiness", {})
        if isinstance(readiness, Mapping) and readiness.get("validated") is True:
            for artifact_id, title, artifact_type, uri_key, sha_key, explanation in (
                (
                    "a2-execution-readiness-contract-v1",
                    "A2 frozen-five-arm execution readiness contract",
                    "contract",
                    "contract_uri",
                    "contract_file_sha256",
                    "Binds the immutable 40 matched plus 12 dormant universe to a measurement-locked readiness policy.",
                ),
                (
                    "a2-execution-readiness-envelope-v1",
                    "A2 execution readiness envelope",
                    "control",
                    "envelope_uri",
                    "envelope_file_sha256",
                    "Authorizes fresh admission and isolated staging while keeping measured A2 closed.",
                ),
                (
                    "a2-execution-readiness-budget-v1",
                    "A2 whole-workload readiness budget",
                    "budget",
                    "budget_uri",
                    "budget_file_sha256",
                    "Requires a fresh all-fee quote for the whole frozen workload under the USD 35 forward hard stop.",
                ),
                (
                    "a2-execution-readiness-runbook-v1",
                    "A2 execution readiness runbook",
                    "runbook",
                    "runbook_uri",
                    "runbook_sha256",
                    "Defines checkpoint, recovery, safe-return, staging, and no-destroy behavior.",
                ),
                (
                    "a2-execution-readiness-ledger-v1",
                    "A2 append-only execution ledger",
                    "ledger",
                    "ledger_uri",
                    "ledger_sha256",
                    "Records material readiness transitions without candidate outcomes or protected payloads.",
                ),
            ):
                result.append(
                    _artifact(
                        artifact_id=artifact_id,
                        title=title,
                        artifact_type=artifact_type,
                        evidence_class="engineering_execution_readiness",
                        scientific_authority=False,
                        safe_uri=str(readiness[uri_key]),
                        content_sha256=str(readiness[sha_key]),
                        explanation=explanation,
                        producing_phase_id="A2_PER_ARM_AUTOINDEX",
                        producing_task_id="A2.1",
                    )
                )
            for key, title in (
                ("bundle_receipt", "Clean hash-bound A2 execution bundle receipt"),
                ("provider_admission_receipt", "Fresh A2 provider admission receipt"),
                ("execution_adoption_receipt", "A2 isolated staging and execution adoption receipt"),
            ):
                receipt = readiness.get(key)
                if isinstance(receipt, Mapping):
                    result.append(
                        _artifact(
                            artifact_id=f"a2-{key.replace('_', '-')}-v1",
                            title=title,
                            artifact_type="receipt",
                            evidence_class="engineering_execution_readiness",
                            scientific_authority=False,
                            safe_uri=str(receipt["uri"]),
                            content_sha256=str(receipt["file_sha256"]),
                            explanation="Validates the current staged-not-launched A2 attempt without authorizing measured retrieval.",
                            producing_phase_id="A2_PER_ARM_AUTOINDEX",
                            producing_task_id="A2.1",
                        )
                    )
        return result
    p1 = phase_id == "P1_CPU_BASELINE"
    if p1:
        for run in model.get("runs", []):
            if not isinstance(run, Mapping):
                continue
            run_id = str(run.get("run_id", ""))
            if not run_id:
                continue
            uri = f"campaigns/scope-autoindex-v1/manifests/{run_id}.json"
            result.append(
                _artifact(
                    artifact_id=f"{run_id}-manifest",
                    title=f"Validated aggregate manifest for {run_id}",
                    artifact_type="manifest",
                    evidence_class="train_selection_measured",
                    scientific_authority=True,
                    safe_uri=uri,
                    content_sha256=str(run.get("manifest_sha256"))
                    if run.get("manifest_sha256")
                    else _hash_file(root, uri),
                    explanation="Binds one aggregate run slot to its immutable request and evaluator lineage.",
                )
            )
        result_row = next(
            (
                item
                for item in model.get("results", [])
                if isinstance(item, Mapping)
                and item.get("result_id") == "P1-CPU-BASELINE"
            ),
            {},
        )
        for key, title, artifact_type, uri, digest_key, explanation in (
            (
                "p1-four-slot-package",
                "P1 four-slot package",
                "package",
                "campaigns/scope-autoindex-v1/packages/dapfam-p1-fulltext-c058a3aa7357c782.package.json",
                "package_file_sha256",
                "Binds all four measured slots, manifests, and validation reports.",
            ),
            (
                "p1-rigor-review",
                "P1 artifact-only rigor review",
                "review",
                "outputs/audits/rigor/dapfam-p1-fulltext-c058a3aa7357c782/rigor_review.json",
                "rigor_review_sha256",
                "Records the independent artifact-only review without exposing protected payloads.",
            ),
        ):
            result.append(
                _artifact(
                    artifact_id=key,
                    title=title,
                    artifact_type=artifact_type,
                    evidence_class="train_selection_measured",
                    scientific_authority=True,
                    safe_uri=uri,
                    content_sha256=str(result_row.get(digest_key))
                    if result_row.get(digest_key)
                    else _hash_file(root, uri),
                    explanation=explanation,
                )
            )
    elif phase_id == "P2_SCOPE_DEVELOPMENT":
        p2 = (
            model.get("p2_readiness", {})
            if isinstance(model.get("p2_readiness"), Mapping)
            else {}
        )
        fixture = (
            p2.get("fixture_pilot", {})
            if isinstance(p2.get("fixture_pilot"), Mapping)
            else {}
        )
        review = (
            p2.get("official_review", {})
            if isinstance(p2.get("official_review"), Mapping)
            else {}
        )
        if fixture.get("status") == "passed":
            for artifact_id, title, artifact_type, uri, digest, explanation in (
                (
                    "p2-fixture-receipt",
                    "P2 repository-only fixture receipt",
                    "receipt",
                    str(fixture.get("receipt_uri")),
                    fixture.get("receipt_sha256"),
                    "Proves the synthetic lifecycle and zero real counters.",
                ),
                (
                    "p2-fixture-manifest",
                    "P2 fixture execution manifest",
                    "manifest",
                    str(fixture.get("execution_manifest_uri")),
                    fixture.get("execution_manifest_sha256"),
                    "Separates fixture metadata from the canonical measured request.",
                ),
                (
                    "p2-fixture-package",
                    "P2 fixture package",
                    "package",
                    "outputs/fixtures/p2/index.json",
                    fixture.get("fixture_package_sha256"),
                    "Binds the deterministic fixture package and checksum closure.",
                ),
            ):
                result.append(
                    _artifact(
                        artifact_id=artifact_id,
                        title=title,
                        artifact_type=artifact_type,
                        evidence_class="fixture",
                        scientific_authority=False,
                        safe_uri=uri,
                        content_sha256=str(digest) if digest else _hash_file(root, uri),
                        explanation=explanation,
                    )
                )
        source = (
            review.get("source", {})
            if isinstance(review.get("source"), Mapping)
            else {}
        )
        if review.get("status") == "accepted_static_contract_review" and source:
            result.append(
                _artifact(
                    artifact_id="p2-official-review-index",
                    title="Official P2 static review index",
                    artifact_type="review",
                    evidence_class="static_contract_review",
                    scientific_authority=False,
                    safe_uri=str(
                        source.get(
                            "index_uri", "orchestration/audits/p2-readiness/index.json"
                        )
                    ),
                    content_sha256=str(source.get("index_sha256"))
                    if source.get("index_sha256")
                    else None,
                    explanation="Records Round 1 revise, Round 2 revise, and Round 3 accept as engineering provenance.",
                )
            )
        proposal = (
            p2.get("candidate_proposal", {})
            if isinstance(p2.get("candidate_proposal"), Mapping)
            else {}
        )
        if (
            proposal.get("status") == "draft_owner_review"
            and proposal.get("validated") is True
        ):
            result.append(
                _artifact(
                    artifact_id="p2-candidate-freeze-proposal",
                    title="P2 four-control and eight-candidate freeze proposal",
                    artifact_type="proposal",
                    evidence_class="engineering",
                    scientific_authority=False,
                    safe_uri=str(proposal.get("proposal_uri")),
                    content_sha256=str(proposal.get("proposal_sha256")),
                    explanation="Records an unadopted Owner-review draft; it does not register or hash-lock measured candidates.",
                )
            )
        for artifact_id, title, artifact_type, uri, explanation in (
            (
                "p2-runtime-v1-interrupted-manifest",
                "Interrupted P2 runtime v1 archive manifest",
                "manifest",
                "archive/p2-runtime-resilience-v1-interrupted/manifest.json",
                "Binds the sanitized failed-attempt patch and records that no measured counters changed.",
            ),
            (
                "p2-runtime-v2-runbook",
                "P2 measured autoresearch v2 runbook",
                "runbook",
                "control/runbooks/P2_MEASURED_AUTORESEARCH_V2.md",
                "Provides the tracked detached-supervisor, journal, resume, proposer, and closeout contract.",
            ),
            (
                "p2-runtime-v2-profile",
                "P2 R1 primary v2 budget profile",
                "budget",
                "control/budgets/p2-r1-primary-v2.yaml",
                "Freezes the 120-hour wall clock, 24-hour overhead reserve, and whole-batch admission rule.",
            ),
            (
                "p2-runtime-v2-envelope",
                "P2 R1 primary v2 execution envelope",
                "control",
                "control/execution-envelope-p2-v2.yaml",
                "Preserves v1 history and authorizes only Owner-local reversible CPU execution.",
            ),
            (
                "p2-runtime-v2-revision",
                "P2 R1 primary v2 campaign revision",
                "control",
                "control/campaigns/scope-autoindex-p2-r1-primary-v2.yaml",
                "Records the additive runtime-resilience revision before the first measured run.",
            ),
        ):
            digest = _hash_file(root, uri)
            if digest:
                result.append(
                    _artifact(
                        artifact_id=artifact_id,
                        title=title,
                        artifact_type=artifact_type,
                        evidence_class="engineering",
                        scientific_authority=False,
                        safe_uri=uri,
                        content_sha256=digest,
                        explanation=explanation,
                    )
                )
        for artifact_id, title, uri, explanation in (
            (
                "p2-preflight-completion-audit-initial",
                "Initial P2 preflight completion audit",
                P2_PREFLIGHT_INITIAL_AUDIT,
                "Records the stale-state, worktree-overlap, capacity-accounting, and negative-test gaps found before repair.",
            ),
            (
                "p2-preflight-completion-audit-repair",
                "Repaired P2 preflight completion audit",
                P2_PREFLIGHT_REPAIR_AUDIT,
                "Validates the fail-closed repair while preserving not-started preflight and zero measured counters.",
            ),
            (
                "p2-preflight-report-byte-audit-initial",
                "Initial P2 preflight report byte-stability audit",
                P2_REPORT_BYTE_INITIAL_AUDIT,
                "Records the clean-Windows-checkout report drift discovered after merge.",
            ),
            (
                "p2-preflight-report-byte-audit-repair",
                "Repaired P2 preflight report byte-stability audit",
                P2_REPORT_BYTE_REPAIR_AUDIT,
                "Validates LF byte preservation and repository-local projection regression coverage.",
            ),
            (
                "p2-preflight-projection-source-audit-initial",
                "Initial P2 preflight projection source-hash audit",
                P2_PROJECTION_SOURCE_INITIAL_AUDIT,
                "Records raw source digest and proposal-binding drift across clean Windows and LF checkouts.",
            ),
            (
                "p2-preflight-projection-source-audit-repair",
                "Repaired P2 preflight projection source-hash audit",
                P2_PROJECTION_SOURCE_REPAIR_AUDIT,
                "Validates byte-stable raw source digests, proposal bindings, and P1 envelope provenance.",
            ),
            (
                "p2-preflight-tracked-owner-path-audit-initial",
                "Initial P2 preflight tracked Owner-path audit",
                P2_TRACKED_OWNER_PATH_INITIAL_AUDIT,
                "Records the personal absolute paths found in two tracked artifacts after the completion audit expanded its safety scope.",
            ),
            (
                "p2-preflight-tracked-owner-path-audit-repair",
                "Repaired P2 preflight tracked Owner-path audit",
                P2_TRACKED_OWNER_PATH_REPAIR_AUDIT,
                "Validates portable path guidance, fail-closed legacy execution configuration, and tracked-artifact regression coverage.",
            ),
            (
                "p2-runtime-resilience-v1-interruption-audit",
                "Interrupted P2 runtime v1 failure audit",
                P2_RUNTIME_INTERRUPTION_AUDIT,
                "Retains the unsafe Windows PID-probe and continuity failure as engineering evidence.",
            ),
            (
                "p2-runtime-resilience-v2-recovery-audit",
                "P2 runtime resilience v2 recovery audit",
                P2_RUNTIME_RECOVERY_AUDIT,
                "Validates advisory locking, hash-chained recovery, detached supervision, proposer isolation, and zero measured counters.",
            ),
            (
                "p2-runtime-resilience-v2-linux-ci-failure-audit",
                "P2 runtime resilience v2 Linux CI failure audit",
                P2_RUNTIME_LINUX_CI_FAILURE_AUDIT,
                "Retains the post-merge POSIX permission-mode regression and blocks cleanup until a green repair CI run exists.",
            ),
            (
                "p2-runtime-resilience-v2-linux-ci-repair-audit",
                "P2 runtime resilience v2 Linux CI repair audit",
                P2_RUNTIME_LINUX_CI_REPAIR_AUDIT,
                "Validates the portable tamper test with focused, full local, and green Linux CI evidence.",
            ),
            (
                "p2-runtime-resilience-v2-clean-checkout-failure-audit",
                "P2 runtime resilience v2 clean-checkout failure audit",
                P2_RUNTIME_CLEAN_CHECKOUT_FAILURE_AUDIT,
                "Retains the checkout-dependent raw-hash drift and blocks cleanup until a committed disposable checkout passes.",
            ),
            (
                "p2-runtime-resilience-v2-clean-checkout-repair-audit",
                "P2 runtime resilience v2 clean-checkout repair audit",
                P2_RUNTIME_CLEAN_CHECKOUT_REPAIR_AUDIT,
                "Validates checkout-stable raw hashes, projection bytes, and read-model identity from a fresh committed worktree.",
            ),
            (
                "p2-runtime-resilience-v2-independent-verifier-revise-audit",
                "P2 runtime resilience v2 independent verifier REVISE audit",
                P2_RUNTIME_INDEPENDENT_REVISE_AUDIT,
                "Retains the read-only verifier rejection and its portability, stale-state, and rigor-schema findings.",
            ),
            (
                "p2-runtime-resilience-v2-independent-verifier-accept-audit",
                "P2 runtime resilience v2 independent verifier ACCEPT audit",
                P2_RUNTIME_INDEPENDENT_ACCEPT_AUDIT,
                "Validates that the committed portability, reporting, and rigor-semantics repairs close every prior verifier finding.",
            ),
        ):
            digest = _hash_file(root, uri)
            if digest:
                result.append(
                    _artifact(
                        artifact_id=artifact_id,
                        title=title,
                        artifact_type="review",
                        evidence_class="engineering",
                        scientific_authority=False,
                        safe_uri=uri,
                        content_sha256=digest,
                        explanation=explanation,
                    )
                )
        observatory = (
            model.get("observatory", {})
            if isinstance(model.get("observatory"), Mapping)
            else {}
        )
        if observatory.get("status") == "ready":
            result.append(
                _artifact(
                    artifact_id="observatory-fixture-registry",
                    title="Aggregate-safe Observatory registry",
                    artifact_type="registry",
                    evidence_class="fixture",
                    scientific_authority=False,
                    safe_uri="outputs/observatory/fixture-v1/registry.json",
                    content_sha256=str(observatory.get("registry_sha256")),
                    explanation="Captures prompts, configs, environments, failures, recovery, and safe lineage without protected content.",
                )
            )
    elif phase_id == "P0_FOUNDATION":
        for relative, title in (
            ("control/source-of-truth.yaml", "Source-of-truth contract"),
            ("schemas/read-model.v2.json", "Shared read-model schema"),
            ("docs/observatory/REPORTING_POLICY.md", "Reporting policy"),
        ):
            result.append(
                _artifact(
                    artifact_id=relative.replace("/", "-"),
                    title=title,
                    artifact_type="schema",
                    evidence_class="engineering",
                    scientific_authority=False,
                    safe_uri=relative,
                    content_sha256=_hash_file(root, relative),
                    explanation="Defines the canonical boundary used to build and validate projections.",
                )
            )
    elif phase_id == "A0_MIGRATION_FOUNDATION":
        for relative, title, artifact_type in (
            (
                "control/campaigns/armindex-multiretriever-v2.yaml",
                "Active ArmIndex campaign",
                "control",
            ),
            (
                "control/plans/ARMINDEX_AUTOINDEX_HARNESSOPT_CONTRACT.md",
                "ArmIndex AutoIndex and HarnessOpt contract",
                "contract",
            ),
            (
                "archive/migration-records/armindex-20260804/migration-manifest.v1.json",
                "ArmIndex migration manifest",
                "manifest",
            ),
            (
                "archive/migration-records/armindex-20260804/migration-receipt.v1.json",
                "ArmIndex migration receipt",
                "receipt",
            ),
            (
                "archive/migration-records/armindex-20260804/mlflow-migration-receipt.v1.json",
                "ArmIndex MLflow migration receipt",
                "receipt",
            ),
            (
                "schemas/armindex/read-model.v1.json",
                "ArmIndex read-model fragment schema",
                "schema",
            ),
        ):
            digest = _hash_file(root, relative)
            if digest:
                result.append(
                    _artifact(
                        artifact_id=relative.replace("/", "-"),
                        title=title,
                        artifact_type=artifact_type,
                        evidence_class="engineering",
                        scientific_authority=False,
                        safe_uri=relative,
                        content_sha256=digest,
                        explanation="Binds the in-place ArmIndex migration without creating scientific evidence.",
                    )
                )
        harvest = model.get("armindex", {}).get("legacy_code_harvest", {})
        if (
            task_id in {None, "A0.10"}
            and isinstance(harvest, Mapping)
            and harvest.get("validated")
        ):
            for artifact_id, title, artifact_type, uri_key, sha_key, explanation in (
                (
                    "a010-legacy-code-harvest-ledger",
                    "A0.10 legacy code-harvest ledger",
                    "ledger",
                    "ledger_uri",
                    "ledger_sha256",
                    "Records reviewed components and immutable source commitments without copying legacy code.",
                ),
                (
                    "a010-legacy-code-harvest-receipt",
                    "A0.10 legacy code-harvest receipt",
                    "receipt",
                    "receipt_uri",
                    "receipt_sha256",
                    "Binds the validated audit, source ledger, and safe migration boundary before projection.",
                ),
                (
                    "a010-synthetic-vertical-slice-receipt",
                    "A0.10 synthetic vertical-slice receipt",
                    "receipt",
                    "fixture_receipt_uri",
                    "fixture_receipt_sha256",
                    "Records a synthetic-only integration check and never represents measured retrieval.",
                ),
                (
                    "a010-repository-hygiene-audit",
                    "A0.10 repository hygiene audit",
                    "audit",
                    "repository_hygiene_audit_uri",
                    "repository_hygiene_audit_sha256",
                    "Records exact-content duplicate review and deletion of verified regenerable caches without removing tracked source.",
                ),
                (
                    "a010-output-root-relocation-receipt",
                    "A0.10 output-root relocation receipt",
                    "receipt",
                    "output_root_relocation_receipt_uri",
                    "output_root_relocation_receipt_sha256",
                    "Binds the byte-preserving relocation from the retired output root to canonical outputs.",
                ),
                (
                    "a010-source-verification-receipt",
                    "A0.10 ThaiPha-Lex source verification receipt",
                    "receipt",
                    "source_verification_receipt_uri",
                    "source_verification_receipt_sha256",
                    "Binds every ThaiPha-Lex ledger component to a pinned Git blob and independently verified SHA-256 without copying source bytes.",
                ),
            ):
                uri = harvest.get(uri_key)
                digest = harvest.get(sha_key)
                if uri and digest:
                    result.append(
                        _artifact(
                            artifact_id=artifact_id,
                            title=title,
                            artifact_type=artifact_type,
                            evidence_class="engineering",
                            scientific_authority=False,
                            safe_uri=str(uri),
                            content_sha256=str(digest),
                            explanation=explanation,
                            producing_phase_id="A0_MIGRATION_FOUNDATION",
                            producing_task_id="A0.10",
                        )
                    )
        feasibility = model.get("armindex", {}).get("compute_storage_feasibility", {})
        if (
            task_id in {None, "A0.8"}
            and isinstance(feasibility, Mapping)
            and feasibility.get("validated") is True
        ):
            for artifact_id, title, artifact_type, uri_key, sha_key, explanation in (
                (
                    "a08-compute-storage-task-receipt",
                    "A0.8 compute and storage task receipt",
                    "receipt",
                    "task_receipt_uri",
                    "task_receipt_sha256",
                    "Closes A0.8 against a validated synthetic-only CPU fixture and zero real counters.",
                ),
                (
                    "a08-compute-storage-fixture-manifest",
                    "A0.8 synthetic feasibility manifest",
                    "manifest",
                    "fixture_manifest_uri",
                    "fixture_manifest_sha256",
                    "Freezes the synthetic scale profiles, storage commitments, method, and safety boundary.",
                ),
                (
                    "a08-compute-storage-fixture-receipt",
                    "A0.8 synthetic feasibility receipt",
                    "receipt",
                    "fixture_receipt_uri",
                    "fixture_receipt_sha256",
                    "Records host-observed CPU, Python allocation, and deterministic storage diagnostics without scientific authority.",
                ),
                (
                    "a08-compute-storage-runbook",
                    "A0.8 compute and storage runbook",
                    "runbook",
                    "runbook_uri",
                    "runbook_sha256",
                    "Defines the bounded CPU-only scaffold, acceptance checks, and protected App asset boundary.",
                ),
                (
                    "a08-compute-storage-ledger",
                    "A0.8 append-only execution ledger",
                    "ledger",
                    "ledger_uri",
                    "ledger_sha256",
                    "Retains the hash-chained task start and fixture-run checkpoints.",
                ),
            ):
                uri = feasibility.get(uri_key)
                digest = feasibility.get(sha_key)
                if uri and digest:
                    result.append(
                        _artifact(
                            artifact_id=artifact_id,
                            title=title,
                            artifact_type=artifact_type,
                            evidence_class="engineering_fixture",
                            scientific_authority=False,
                            safe_uri=str(uri),
                            content_sha256=str(digest),
                            explanation=explanation,
                            producing_phase_id="A0_MIGRATION_FOUNDATION",
                            producing_task_id="A0.8",
                        )
                    )
        closeout = model.get("armindex", {}).get("phase_closeout", {})
        if (
            task_id in {None, "A0.9"}
            and isinstance(closeout, Mapping)
            and closeout.get("validated") is True
        ):
            for artifact_id, title, artifact_type, uri_key, sha_key, explanation in (
                (
                    "a09-phase-closeout-receipt",
                    "A0 phase closeout receipt",
                    "receipt",
                    "receipt_uri",
                    "receipt_sha256",
                    "Closes every A0 task only after hash-bound validation and preserves zero measured counters.",
                ),
                (
                    "a09-validation-audit",
                    "A0.9 validation and safety audit",
                    "audit",
                    "validation_audit_uri",
                    "validation_audit_sha256",
                    "Records the CPU-only validation matrix and untouched protected surfaces.",
                ),
                (
                    "a09-closeout-runbook",
                    "A0.9 validation and closeout runbook",
                    "runbook",
                    "runbook_uri",
                    "runbook_sha256",
                    "Defines the fail-closed acceptance and the synthetic-only A1.1 handoff.",
                ),
                (
                    "a09-closeout-ledger",
                    "A0.9 append-only closeout ledger",
                    "ledger",
                    "ledger_uri",
                    "ledger_sha256",
                    "Binds task start and completion to the validated audit through a hash chain.",
                ),
            ):
                uri = closeout.get(uri_key)
                digest = closeout.get(sha_key)
                if uri and digest:
                    result.append(
                        _artifact(
                            artifact_id=artifact_id,
                            title=title,
                            artifact_type=artifact_type,
                            evidence_class="engineering",
                            scientific_authority=False,
                            safe_uri=str(uri),
                            content_sha256=str(digest),
                            explanation=explanation,
                            producing_phase_id="A0_MIGRATION_FOUNDATION",
                            producing_task_id="A0.9",
                        )
                    )
    elif phase_id == "A1_BASELINES_AND_MULTI_ARM_SCREENING":
        adapter = model.get("armindex", {}).get("adapter_fixture_validation", {})
        scaffold = model.get("armindex", {}).get("a1_2_contract_scaffold", {})
        current_attempt = model.get("armindex", {}).get("a1_2_current_attempt", {})
        if (
            task_id in {None, "A1.2"}
            and isinstance(current_attempt, Mapping)
            and current_attempt.get("validated") is True
            and current_attempt.get("status") == "PASS"
            and isinstance(current_attempt.get("measured_result_summary"), Mapping)
        ):
            summary = current_attempt["measured_result_summary"]
            result.append(
                _artifact(
                    artifact_id="a12-measured-result-summary-v16",
                    title="A1.2 measured arm-level result summary",
                    artifact_type="receipt",
                    evidence_class="measured_development_aggregate",
                    scientific_authority=True,
                    safe_uri=str(summary.get("summary_uri")),
                    content_sha256=str(summary.get("summary_file_sha256")),
                    explanation="Projects the complete 25/25 REP-DEV result, primary and secondary arm aggregates, deterministic promotion, and zero protected-access counters without per-query data.",
                    producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                    producing_task_id="A1.2",
                )
            )
            eda = current_attempt.get("cell_eda_package")
            if isinstance(eda, Mapping) and eda.get("status") == "PASS":
                result.append(
                    _artifact(
                        artifact_id="a12-cell-eda-package-v16",
                        title="A1.2 publication cell EDA package",
                        artifact_type="figure_package",
                        evidence_class="measured_development_aggregate_eda",
                        scientific_authority=True,
                        safe_uri=str(eda.get("package_uri")),
                        content_sha256=str(eda.get("package_file_sha256")),
                        explanation="Projects the complete 25-cell aggregate table, quality and efficiency figures, and Thai guide without per-query outcomes.",
                        producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                        producing_task_id="A1.2",
                    )
                )
            retention = model.get("armindex", {}).get(
                "a1_2_remote_retention", {}
            )
            if (
                isinstance(retention, Mapping)
                and retention.get("validated") is True
                and retention.get("status") == "PASS"
            ):
                result.append(
                    _artifact(
                        artifact_id="a12-r15-remote-retention-audit",
                        title="A1.2 remote allowlisted handoff retention audit",
                        artifact_type="audit",
                        evidence_class="aggregate_safe_remote_retention_audit",
                        scientific_authority=False,
                        safe_uri=str(retention.get("audit_uri")),
                        content_sha256=str(retention.get("audit_file_sha256")),
                        explanation="Binds exact remote retention of the 29-file baseline, 8-file journal EDA, and 12-file closeout packages without provider payloads, credentials, or protected data.",
                        producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                        producing_task_id="A1.2",
                    )
                )
        split_claim_audit = model.get("armindex", {}).get(
            "a1_2_rep_harness_claim_audit", {}
        )
        p02_limit_audit = model.get("armindex", {}).get("a1_2_p02_limit_audit", {})
        dense_overflow = model.get("armindex", {}).get("a1_2_dense_overflow", {})
        exact_token_id_probe = model.get("armindex", {}).get(
            "a1_2_exact_token_id_adapter_probe", {}
        )
        r13_failure = model.get("armindex", {}).get("a1_2_r13_failure", {})
        if (
            task_id in {None, "A1.2"}
            and isinstance(split_claim_audit, Mapping)
            and split_claim_audit.get("validated") is True
        ):
            for artifact_id, title, artifact_type, uri_key, sha_key, explanation in (
                (
                    "a12-rep-harness-claim-audit",
                    "A1.2 REP-DEV/HARNESS-DEV and claim-parser audit",
                    "audit",
                    "audit_uri",
                    "audit_file_sha256",
                    "Binds the aggregate-safe deterministic 150/100 split commitments and the fail-closed P02 parser recommendation without exposing exact membership or retrieval outcomes.",
                ),
                (
                    "a12-rep-harness-split-eda-png",
                    "A1.2 aggregate-safe split EDA PNG",
                    "figure",
                    "figure_png_uri",
                    "figure_png_sha256",
                    "Shows only Train-250 stratum and Hamilton allocation counts; it contains no identifiers or scientific results.",
                ),
                (
                    "a12-rep-harness-split-eda-svg",
                    "A1.2 aggregate-safe split EDA SVG",
                    "figure",
                    "figure_svg_uri",
                    "figure_svg_sha256",
                    "Retains the vector version of the same aggregate-only pre-measurement EDA.",
                ),
            ):
                result.append(
                    _artifact(
                        artifact_id=artifact_id,
                        title=title,
                        artifact_type=artifact_type,
                        evidence_class="pre_measurement_owner_local_input_audit",
                        scientific_authority=False,
                        safe_uri=str(split_claim_audit[uri_key]),
                        content_sha256=str(split_claim_audit[sha_key]),
                        explanation=explanation,
                        producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                        producing_task_id="A1.2",
                    )
                )
        if (
            task_id in {None, "A1.2"}
            and isinstance(p02_limit_audit, Mapping)
            and p02_limit_audit.get("validated") is True
        ):
            for artifact_id, title, uri_key, sha_key, explanation in (
                (
                    "a12-p02-first-claim-repair",
                    "A1.2 P02-FIRST-CLAIM repair and coverage audit",
                    "p02_audit_uri",
                    "p02_audit_file_sha256",
                    "Binds the Owner-authorized additive boundary parser, 100 percent REP-DEV and corpus coverage, deterministic replay, and zero fallback without dependency semantics.",
                ),
                (
                    "a12-effective-input-limit-blocker",
                    "A1.2 effective input-limit contract blocker",
                    "input_limit_audit_uri",
                    "input_limit_audit_file_sha256",
                    "Records the deterministic ARM-03 x P00 overlength witness and fail-closed zero-truncation decision before retrieval.",
                ),
            ):
                result.append(
                    _artifact(
                        artifact_id=artifact_id,
                        title=title,
                        artifact_type="audit",
                        evidence_class="pre_measurement_owner_local_input_validation",
                        scientific_authority=False,
                        safe_uri=str(p02_limit_audit[uri_key]),
                        content_sha256=str(p02_limit_audit[sha_key]),
                        explanation=explanation,
                        producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                        producing_task_id="A1.2",
                    )
                )
        if (
            task_id in {None, "A1.2"}
            and isinstance(dense_overflow, Mapping)
            and dense_overflow.get("validated") is True
        ):
            for artifact_id, title, artifact_type, uri_key, sha_key, explanation in (
                (
                    "a12-dense-overflow-contract",
                    "A1.2 frozen dense-overflow repair contract",
                    "contract",
                    "contract_uri",
                    "contract_file_sha256",
                    "Binds the Owner-authorized additive physical-window composition policy while preserving v11/v12-r3/v13 and original P02 lineage.",
                ),
                (
                    "a12-dense-overflow-inventory",
                    "A1.2 dense-overflow compatibility inventory",
                    "audit",
                    "inventory_uri",
                    "inventory_file_sha256",
                    "Records aggregate-only rendered-length incidence across all 25 program-arm cells, REP-DEV queries, and required corpus logical units.",
                ),
                (
                    "a12-dense-overflow-composition-audit",
                    "A1.2 dense-overflow composition audit",
                    "audit",
                    "composition_uri",
                    "composition_file_sha256",
                    "Validates physical-window limits, token coverage, zero overlap, zero fallback, and deterministic composition planning without executing encoder vectors.",
                ),
                (
                    "a12-dense-overflow-eda-png",
                    "A1.2 dense-overflow EDA PNG",
                    "figure",
                    "figure_png_uri",
                    "figure_png_sha256",
                    "Shows aggregate overflow incidence and the PatEmbed P00 engineering disclosure boundary; no retrieval result is displayed.",
                ),
                (
                    "a12-dense-overflow-eda-svg",
                    "A1.2 dense-overflow EDA SVG",
                    "figure",
                    "figure_svg_uri",
                    "figure_svg_sha256",
                    "Vector form of the aggregate-only dense-overflow EDA for reproducibility.",
                ),
                (
                    "a12-protected-compiler-integration-v15",
                    "A1.2 protected compiler integration v15",
                    "contract",
                    "compiler_integration_uri",
                    "compiler_integration_file_sha256",
                    "Binds the additive protected compiler to the frozen dense-overflow policy while preserving v11/v12-r3/v13 and the original P02 lineage.",
                ),
                (
                    "a12-protected-compiler-audit-v15",
                    "A1.2 aggregate-safe protected compiler audit v15",
                    "audit",
                    "compiler_audit_uri",
                    "compiler_audit_file_sha256",
                    "Records validated 25/25 bindings, protected handoff and transfer receipt hashes, deterministic replay, and zero silent truncation without exposing protected payloads.",
                ),
                (
                    "a12-whole-workload-budget-model-v15",
                    "A1.2 aggregate whole-workload budget model v15",
                    "contract",
                    "budget_model_uri",
                    "budget_model_file_sha256",
                    "Binds the complete physical-window workload to frozen hard stops while keeping fresh quote and live budget admission pending.",
                ),
                (
                    "a12-local-adoption-inputs-receipt-v15",
                    "A1.2 final local adoption-input receipt v15",
                    "receipt",
                    "final_receipt_uri",
                    "final_receipt_file_sha256",
                    "Binds the clean pushed bundle, protected compiler evidence, workload model, and synthetic watchdog dry-run without provider contact or execution adoption.",
                ),
            ):
                uri = dense_overflow.get(uri_key)
                digest = dense_overflow.get(sha_key)
                if uri and digest:
                    result.append(
                        _artifact(
                            artifact_id=artifact_id,
                            title=title,
                            artifact_type=artifact_type,
                            evidence_class="pre_measurement_owner_local_compatibility_validation",
                            scientific_authority=False,
                            safe_uri=str(uri),
                            content_sha256=str(digest),
                            explanation=explanation,
                            producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                            producing_task_id="A1.2",
                        )
                    )
        if (
            task_id in {None, "A1.2"}
            and isinstance(exact_token_id_probe, Mapping)
            and exact_token_id_probe.get("validated") is True
        ):
            result.append(
                _artifact(
                    artifact_id="a12-v16-exact-token-id-adapter-probe",
                    title="A1.2 v16 exact-token-ID adapter probe",
                    artifact_type="audit",
                    evidence_class=str(
                        exact_token_id_probe.get(
                            "evidence_class",
                            "aggregate_safe_synthetic_runtime_preparation",
                        )
                    ),
                    scientific_authority=False,
                    safe_uri=str(exact_token_id_probe["audit_uri"]),
                    content_sha256=str(exact_token_id_probe["audit_file_sha256"]),
                    explanation=(
                        "Records the aggregate-safe synthetic exact-token-ID repair "
                        "probe across ARM-02 through ARM-05 while preserving frozen "
                        "v11-v15 semantics and keeping provider admission and "
                        "measured retrieval closed."
                    ),
                    producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                    producing_task_id="A1.2",
                )
            )
        if (
            task_id in {None, "A1.2"}
            and isinstance(r13_failure, Mapping)
            and r13_failure.get("validated") is True
        ):
            result.append(
                _artifact(
                    artifact_id="a12-v16-r13-failed-closed-attempt-audit",
                    title="A1.2 v16 r13 failed-closed attempt audit",
                    artifact_type="audit",
                    evidence_class="aggregate_safe_live_attempt_failure",
                    scientific_authority=False,
                    safe_uri=str(r13_failure["audit_uri"]),
                    content_sha256=str(r13_failure["audit_file_sha256"]),
                    explanation=(
                        "Records an incomplete 24/25 logical-cell attempt as "
                        "failure provenance only. Partial outputs are not promotable; "
                        "the official completed measured-run counter remains zero."
                    ),
                    producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                    producing_task_id="A1.2",
                )
            )
        if isinstance(adapter, Mapping) and adapter.get("validated") is True:
            if task_id in {None, "A1.1"}:
                for (
                    artifact_id,
                    title,
                    artifact_type,
                    uri_key,
                    sha_key,
                    explanation,
                ) in (
                    (
                        "a11-adapter-task-receipt",
                        "A1.1 adapter fixture task receipt",
                        "receipt",
                        "task_receipt_uri",
                        "task_receipt_sha256",
                        "Closes A1.1 against the validated five-arm scaffold, ARM-01 CPU path, reporting contract, and zero real counters.",
                    ),
                    (
                        "a11-adapter-fixture-manifest",
                        "A1.1 adapter fixture manifest",
                        "manifest",
                        "fixture_manifest_uri",
                        "fixture_manifest_sha256",
                        "Freezes the five adapter declarations, synthetic representation commitments, ARM-01 fixture backend, and fail-closed dense-arm boundary.",
                    ),
                    (
                        "a11-adapter-fixture-receipt",
                        "A1.1 ARM-01 CPU fixture receipt",
                        "receipt",
                        "fixture_receipt_uri",
                        "fixture_receipt_sha256",
                        "Records aggregate compile, index, search, evaluation, throughput, and Python-allocation observations from synthetic CPU execution.",
                    ),
                    (
                        "a11-adapter-runbook",
                        "A1.1 adapter fixture runbook",
                        "runbook",
                        "runbook_uri",
                        "runbook_sha256",
                        "Defines the synthetic-only acceptance, detailed English report requirement, archive controls, and pre-GPU boundary.",
                    ),
                    (
                        "a11-adapter-ledger",
                        "A1.1 append-only execution ledger",
                        "ledger",
                        "ledger_uri",
                        "ledger_sha256",
                        "Binds task start, fixture execution, resource proposal, and ready-to-close state through a canonical hash chain.",
                    ),
                ):
                    uri = adapter.get(uri_key)
                    digest = adapter.get(sha_key)
                    if uri and digest:
                        result.append(
                            _artifact(
                                artifact_id=artifact_id,
                                title=title,
                                artifact_type=artifact_type,
                                evidence_class="engineering_fixture",
                                scientific_authority=False,
                                safe_uri=str(uri),
                                content_sha256=str(digest),
                                explanation=explanation,
                                producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                                producing_task_id="A1.1",
                            )
                        )
            if task_id in {None, "A1.1", "A1.2"}:
                proposal_uri = adapter.get("gpu_proposal_uri")
                proposal_digest = adapter.get("gpu_proposal_sha256")
                if proposal_uri and proposal_digest:
                    result.append(
                        _artifact(
                            artifact_id="a12-gpu-execution-proposal",
                            title="A1.2 GPU, elapsed-time, and budget proposal",
                            artifact_type="proposal",
                            evidence_class="planning_estimate",
                            scientific_authority=False,
                            safe_uri=str(proposal_uri),
                            content_sha256=str(proposal_digest),
                            explanation="Provides bounded owner-managed GPU planning assumptions and hard stops without adopting an execution contract or launching compute.",
                            producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                            producing_task_id="A1.1",
                        )
                    )
        if (
            task_id in {None, "A1.2"}
            and isinstance(scaffold, Mapping)
            and scaffold.get("validated") is True
        ):
            for artifact_id, title, artifact_type, uri_key, sha_key, explanation in (
                (
                    "a12-contract-scaffold-receipt",
                    "A1.2 contract scaffold receipt",
                    "receipt",
                    "receipt_uri",
                    "receipt_sha256",
                    "Closes the offline scaffold goal while preserving launch, measured retrieval, Selection, and Final locks.",
                ),
                (
                    "a12-execution-contract",
                    "A1.2 versioned execution contract",
                    "contract",
                    "execution_contract_uri",
                    "execution_contract_sha256",
                    "Binds the five-arm order, zero real counters, resource plan, and the exact launch-locked next action.",
                ),
                (
                    "a12-arm01-rank-parity",
                    "A1.2 ARM-01 bm25s synthetic CPU rank-parity receipt",
                    "receipt",
                    "arm01_parity_receipt_uri",
                    "arm01_parity_receipt_sha256",
                    "Records exact synthetic rank-order parity against the repository Okapi reference with zero measured and charged-resource counters.",
                ),
                (
                    "a12-budget-profile",
                    "A1.2 hash-bound budget profile",
                    "budget",
                    "budget_profile_uri",
                    "budget_profile_sha256",
                    "Freezes the USD 5 pilot, USD 18 screen, USD 23 A1, and USD 100 campaign hard stops without authorizing spend.",
                ),
                (
                    "a12-execution-envelope",
                    "A1.2 execution envelope",
                    "contract",
                    "execution_envelope_uri",
                    "execution_envelope_sha256",
                    "Separates the CPU-only zero-cost scaffold authority from the planned but unadopted GPU execution boundary.",
                ),
                (
                    "a12-model-lockset",
                    "A1.2 five-arm model source lockset",
                    "lockset",
                    "model_lockset_uri",
                    "model_lockset_sha256",
                    "Freezes the ARM-01 bm25s adapter and four public dense source revisions while requiring Owner-local runtime manifests.",
                ),
                (
                    "a12-launch-checklist",
                    "A1.2 Owner-local launch checklist",
                    "checklist",
                    "launch_checklist_uri",
                    "launch_checklist_sha256",
                    "Lists the remaining Owner-local artifact, parity, quote, capacity, storage, adoption, and termination checks; launch remains false.",
                ),
                (
                    "a12-shutdown-plan",
                    "A1.2 two-layer shutdown plan",
                    "runbook",
                    "shutdown_plan_uri",
                    "shutdown_plan_sha256",
                    "Requires both an in-instance guard and an Owner-local provider termination watcher; guest poweroff alone is insufficient.",
                ),
                (
                    "a12-scaffold-runbook",
                    "A1.2 contract scaffold runbook",
                    "runbook",
                    "runbook_uri",
                    "runbook_sha256",
                    "Defines the detailed English reporting, archive retention, CPU-only ARM-01, and pre-GPU acceptance contract.",
                ),
                (
                    "a12-scaffold-ledger",
                    "A1.2 append-only scaffold ledger",
                    "ledger",
                    "ledger_uri",
                    "ledger_sha256",
                    "Hash-chains scaffold start, ARM-01 synthetic CPU parity, and launch-locked closeout.",
                ),
                (
                    "a12-report-archive-audit",
                    "A1.2 generated report archive audit",
                    "audit",
                    "report_archive_audit_uri",
                    "report_archive_audit_sha256",
                    "Confirms that all 39 registered detailed English Phase/Task reports remain current or graph-referenced and that no generated or Owner-authored report is eligible to move.",
                ),
                (
                    "a12-closeout-validation-audit",
                    "A1.2 closeout validation audit",
                    "audit",
                    "closeout_validation_audit_uri",
                    "closeout_validation_audit_sha256",
                    "Records the aggregate-safe validation matrix, recovered infrastructure failures, zero scientific counters, and untouched protected surfaces.",
                ),
                (
                    "a12-owner-local-preflight",
                    "A1.2 Owner-local CPU preflight receipt",
                    "audit",
                    "preflight_uri",
                    "preflight_sha256",
                    "Records the CPU-only fail-closed artifact, provider, storage, and termination preflight without exposing Owner-local bytes or access material.",
                ),
                (
                    "a12-owner-local-mlflow-registration",
                    "A1.2 MLflow safe preflight registration",
                    "result",
                    "preflight_mlflow_registration_uri",
                    "preflight_mlflow_registration_sha256",
                    "Binds the aggregate-safe preflight result and MLflow mirror registration while keeping protected artifacts outside MLflow.",
                ),
            ):
                uri = scaffold.get(uri_key)
                digest = scaffold.get(sha_key)
                if uri and digest:
                    result.append(
                        _artifact(
                            artifact_id=artifact_id,
                            title=title,
                            artifact_type=artifact_type,
                            evidence_class="engineering_contract_scaffold",
                            scientific_authority=False,
                            safe_uri=str(uri),
                            content_sha256=str(digest),
                            explanation=explanation,
                            producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                            producing_task_id="A1.2",
                        )
                    )
            vast = scaffold.get("vast_preflight_v2", {})
            if isinstance(vast, Mapping) and vast.get("validated") is True:
                for (
                    artifact_id,
                    title,
                    artifact_type,
                    uri_key,
                    sha_key,
                    explanation,
                ) in (
                    (
                        "a12-vast-v2-migration-receipt",
                        "A1.2 Vast 4xRTX3090 migration receipt v2",
                        "receipt",
                        "receipt_uri",
                        "receipt_sha256",
                        "Binds the additive local-orchestrated four-GPU preparation while preserving every v1 source byte and keeping launch and adoption false.",
                    ),
                    (
                        "a12-vast-v2-execution-contract",
                        "A1.2 Vast 4xRTX3090 execution contract v2",
                        "contract",
                        "contract_uri",
                        "contract_sha256",
                        "Freezes the local canonical-writer and disposable remote-worker boundary with one dense arm per GPU.",
                    ),
                    (
                        "a12-vast-v2-synthetic-receipt",
                        "A1.2 synthetic four-worker receipt",
                        "receipt",
                        "synthetic_receipt_uri",
                        "synthetic_receipt_sha256",
                        "Records a four-subprocess CPU-only orchestration pass with no GPU reservation, paid compute, or scientific measurement.",
                    ),
                    (
                        "a12-vast-v2-budget",
                        "A1.2 Vast 4xRTX3090 budget profile v2",
                        "budget",
                        "budget_uri",
                        "budget_sha256",
                        "Records the Owner planning rate of USD 0.60 per complete four-GPU instance-hour, the USD 1.20-2.40 estimate, and unchanged hard stops.",
                    ),
                    (
                        "a12-vast-v2-topology",
                        "A1.2 local-Codex remote-four-GPU topology",
                        "contract",
                        "topology_uri",
                        "topology_sha256",
                        "Assigns ARM-02 through ARM-05 to fixed GPU slots while all canonical and protected surfaces remain local.",
                    ),
                    (
                        "a12-vast-v2-runtime",
                        "A1.2 Vast runtime lock v2",
                        "lockset",
                        "runtime_lock_uri",
                        "runtime_lock_sha256",
                        "Freezes the Python, CUDA, PyTorch, package, and offline-install runtime contract; live image digest remains pending.",
                    ),
                    (
                        "a12-vast-v2-image",
                        "A1.2 OCI image digest contract v2",
                        "contract",
                        "image_contract_uri",
                        "image_contract_sha256",
                        "Requires immutable base and built-image identities before upload or remote start.",
                    ),
                    (
                        "a12-vast-v2-checklist",
                        "A1.2 Vast live preflight checklist v2",
                        "checklist",
                        "checklist_uri",
                        "checklist_sha256",
                        "Enumerates the live Owner checks that must pass before the unchanged revision can be considered for adoption.",
                    ),
                    (
                        "a12-vast-v2-shutdown",
                        "A1.2 Owner-local termination plan v2",
                        "runbook",
                        "shutdown_uri",
                        "shutdown_sha256",
                        "Requires provider destruction and verification from the Owner-local watchdog; guest poweroff is explicitly insufficient.",
                    ),
                    (
                        "a12-vast-v2-allowlist",
                        "A1.2 remote safe-export allowlist v2",
                        "contract",
                        "allowlist_uri",
                        "allowlist_sha256",
                        "Restricts collected remote outputs to declared aggregate-safe receipts, logs, hashes, and checkpoints.",
                    ),
                    (
                        "a12-vast-v2-runbook",
                        "A1.2 Vast preflight runbook v2",
                        "runbook",
                        "runbook_uri",
                        "runbook_sha256",
                        "Defines the offline preparation, live Owner preflight, hard stops, and launch-lock acceptance boundary.",
                    ),
                    (
                        "a12-vast-v2-owner-runbook",
                        "A1.2 beginner Owner runbook",
                        "runbook",
                        "owner_runbook_uri",
                        "owner_runbook_sha256",
                        "Provides exact local PowerShell commands without embedding access material or protected benchmark content.",
                    ),
                    (
                        "a12-vast-v2-coordinator",
                        "A1.2 local SSH coordinator",
                        "tool",
                        "coordinator_uri",
                        "coordinator_sha256",
                        "Implements upload, verification, bootstrap, status, collection, and teardown from the Owner-local machine.",
                    ),
                    (
                        "a12-vast-v2-watchdog",
                        "A1.2 Owner-local TTL watchdog",
                        "tool",
                        "watchdog_uri",
                        "watchdog_sha256",
                        "Monitors heartbeat and TTL, invokes provider destruction, and requires destruction verification.",
                    ),
                    (
                        "a12-vast-v2-ledger",
                        "A1.2 Vast preflight ledger v2",
                        "ledger",
                        "ledger_uri",
                        "ledger_sha256",
                        "Hash-chains preparation start, synthetic orchestration, and the immutable migration receipt.",
                    ),
                    (
                        "a12-vast-v2-closeout-audit",
                        "A1.2 Vast preflight closeout validation audit",
                        "audit",
                        "closeout_validation_audit_uri",
                        "closeout_validation_audit_sha256",
                        "Records the offline validation matrix, two bounded recoveries, zero counters, and untouched protected and paid-worker surfaces.",
                    ),
                ):
                    uri = vast.get(uri_key)
                    digest = vast.get(sha_key)
                    if uri and digest:
                        result.append(
                            _artifact(
                                artifact_id=artifact_id,
                                title=title,
                                artifact_type=artifact_type,
                                evidence_class="engineering_preflight_scaffold",
                                scientific_authority=False,
                                safe_uri=str(uri),
                                content_sha256=str(digest),
                                explanation=explanation,
                                producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                                producing_task_id="A1.2",
                            )
                        )
                for job in vast.get("jobs", []):
                    if (
                        isinstance(job, Mapping)
                        and job.get("arm_id")
                        and job.get("uri")
                        and job.get("sha256")
                    ):
                        arm_id = str(job["arm_id"])
                        result.append(
                            _artifact(
                                artifact_id=f"a12-vast-v2-job-{arm_id.lower()}",
                                title=f"A1.2 immutable {arm_id} remote job",
                                artifact_type="manifest",
                                evidence_class="engineering_preflight_scaffold",
                                scientific_authority=False,
                                safe_uri=str(job["uri"]),
                                content_sha256=str(job["sha256"]),
                                explanation="Freezes one arm, one visible GPU slot, isolated outputs, checkpoint policy, heartbeat, and safe-export behavior.",
                                producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                                producing_task_id="A1.2",
                            )
                        )
            vast_v3 = scaffold.get("vast_preflight_v3", {})
            if isinstance(vast_v3, Mapping) and vast_v3.get("validated") is True:
                for (
                    artifact_id,
                    title,
                    artifact_type,
                    uri_key,
                    sha_key,
                    explanation,
                ) in (
                    (
                        "a12-vast-v3-correction-receipt",
                        "A1.2 Vast post-commit correction receipt v3",
                        "receipt",
                        "receipt_uri",
                        "receipt_sha256",
                        "Preserves immutable v2 evidence and binds the additive clean-commit validation correction, USD 0.60 complete-instance planning rate, cost estimate, hard stops, and launch locks.",
                    ),
                    (
                        "a12-vast-v3-execution-contract",
                        "A1.2 Vast post-commit execution contract v3",
                        "contract",
                        "contract_uri",
                        "contract_sha256",
                        "Separates v2 preparation provenance from live bundle identity and freezes the USD 0.60 complete-instance planning rate without authorizing execution.",
                    ),
                    (
                        "a12-vast-v3-control-runbook",
                        "A1.2 Vast post-commit preflight runbook v3",
                        "runbook",
                        "control_runbook_uri",
                        "control_runbook_sha256",
                        "Defines the corrected validation rule and preserves every v1 and v2 artifact byte.",
                    ),
                    (
                        "a12-vast-v3-owner-runbook",
                        "A1.2 beginner Owner runbook v3",
                        "runbook",
                        "owner_runbook_uri",
                        "owner_runbook_sha256",
                        "Provides the exact clean-commit validator and frozen-bundle command substitutions for the preserved v2 live preflight.",
                    ),
                    (
                        "a12-vast-v3-schema",
                        "A1.2 Vast post-commit receipt schema v3",
                        "schema",
                        "schema_uri",
                        "schema_sha256",
                        "Validates the additive correction receipt, immutable bindings, launch locks, and zero counters.",
                    ),
                    (
                        "a12-vast-v3-validator",
                        "A1.2 Vast post-commit validator",
                        "tool",
                        "module_uri",
                        "module_sha256",
                        "Validates receipt-bound v2 bytes and captures the current clean commit and tree without regenerating v2 controls.",
                    ),
                ):
                    uri = vast_v3.get(uri_key)
                    digest = vast_v3.get(sha_key)
                    if uri and digest:
                        result.append(
                            _artifact(
                                artifact_id=artifact_id,
                                title=title,
                                artifact_type=artifact_type,
                                evidence_class="engineering_preflight_correction",
                                scientific_authority=False,
                                safe_uri=str(uri),
                                content_sha256=str(digest),
                                explanation=explanation,
                                producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                                producing_task_id="A1.2",
                            )
                        )
                projection_repair_sha256 = _hash_file(
                    root, A12_V3_PROJECTION_STABILITY_REPAIR_AUDIT
                )
                if projection_repair_sha256:
                    result.append(
                        _artifact(
                            artifact_id="a12-vast-v3-projection-stability-repair",
                            title="A1.2 v3 deterministic projection stability repair",
                            artifact_type="audit",
                            evidence_class="engineering_validation",
                            scientific_authority=False,
                            safe_uri=A12_V3_PROJECTION_STABILITY_REPAIR_AUDIT,
                            content_sha256=projection_repair_sha256,
                            explanation="Records the bounded runtime Git-identity projection drift, the deterministic read-model repair, focused regression evidence, preserved v1/v2/v3 receipts, and unchanged zero counters.",
                            producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                            producing_task_id="A1.2",
                        )
                    )
            vast_v5 = scaffold.get("vast_preflight_v5", {})
            if isinstance(vast_v5, Mapping) and vast_v5.get("validated") is True:
                for (
                    artifact_id,
                    title,
                    artifact_type,
                    uri_key,
                    sha_key,
                    explanation,
                ) in (
                    (
                        "a12-direct-base-v5-receipt",
                        "A1.2 runtime-minimal direct-base receipt v5",
                        "receipt",
                        "receipt_uri",
                        "receipt_sha256",
                        "Binds the direct official PyTorch manifest, runtime-minimal policy, upload allowlist, live pending checks, and zero counters.",
                    ),
                    (
                        "a12-direct-base-v5-contract",
                        "A1.2 runtime-minimal direct-base execution contract v5",
                        "contract",
                        "contract_uri",
                        "contract_sha256",
                        "Removes custom-image build/save/upload/load and nested-container execution from the active path while preserving v1-v3.",
                    ),
                    (
                        "a12-direct-base-v5-runtime-lock",
                        "A1.2 direct-base runtime lock v5",
                        "manifest",
                        "runtime_lock_uri",
                        "runtime_lock_sha256",
                        "Freezes linux/amd64, Python 3.11, torch 2.6.0+cu118, CUDA 11.8, offline wheelhouse, and no runtime model download.",
                    ),
                    (
                        "a12-direct-base-v5-image-contract",
                        "A1.2 direct-base image contract v5",
                        "contract",
                        "image_contract_uri",
                        "image_contract_sha256",
                        "Binds the registry-verified OCI manifest digest and direct-launch identity rules.",
                    ),
                    (
                        "a12-direct-base-v5-topology",
                        "A1.2 direct-base topology contract v5",
                        "manifest",
                        "topology_uri",
                        "topology_sha256",
                        "Freezes one Vast linux/amd64 worker with four RTX 3090 slots and local-only protected surfaces.",
                    ),
                    (
                        "a12-direct-base-v5-schema",
                        "A1.2 direct-base receipt schema v5",
                        "schema",
                        "schema_uri",
                        "schema_sha256",
                        "Validates the additive receipt lifecycle, safety flags, and zero counters.",
                    ),
                    (
                        "a12-direct-base-v5-runbook",
                        "A1.2 beginner Owner direct-base runbook v5",
                        "runbook",
                        "owner_runbook_uri",
                        "owner_runbook_sha256",
                        "Documents local staging, direct image verification, SSH upload allowlist, synthetic preflight, and provider destroy/TTL obligations.",
                    ),
                    (
                        "a12-direct-base-v5-module",
                        "A1.2 direct-base validator module v5",
                        "tool",
                        "module_uri",
                        "module_sha256",
                        "Validates the additive direct-base contracts and receipt without contacting Vast.",
                    ),
                ):
                    uri = vast_v5.get(uri_key)
                    digest = vast_v5.get(sha_key)
                    if uri and digest:
                        result.append(
                            _artifact(
                                artifact_id=artifact_id,
                                title=title,
                                artifact_type=artifact_type,
                                evidence_class="engineering_preflight_revision",
                                scientific_authority=False,
                                safe_uri=str(uri),
                                content_sha256=str(digest),
                                explanation=explanation,
                                producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                                producing_task_id="A1.2",
                            )
                        )
            vast_v6 = scaffold.get("vast_preflight_v6", {})
            if isinstance(vast_v6, Mapping) and vast_v6.get("validated") is True:
                for (
                    artifact_id,
                    title,
                    artifact_type,
                    uri_key,
                    sha_key,
                    explanation,
                ) in (
                    (
                        "a12-live-preflight-v6-receipt",
                        "A1.2 live-container correction receipt v6",
                        "receipt",
                        "receipt_uri",
                        "receipt_sha256",
                        "Records only the additive direct-base container correction, live defects, synthetic-only boundary, and unchanged zero counters.",
                    ),
                    (
                        "a12-live-preflight-v6-contract",
                        "A1.2 live-container correction contract v6",
                        "contract",
                        "contract_uri",
                        "contract_sha256",
                        "Binds the correction to the v5 lineage, official image manifest, safe exports, synthetic GPU checks, and hard-stop budget without authorizing scientific execution.",
                    ),
                    (
                        "a12-live-preflight-v6-schema",
                        "A1.2 live-container correction receipt schema v6",
                        "schema",
                        "schema_uri",
                        "schema_sha256",
                        "Defines the additive v6 receipt shape, false authorization flags, and zero measured counters.",
                    ),
                    (
                        "a12-live-preflight-v6-validator",
                        "A1.2 live-container correction validator v6",
                        "tool",
                        "validator_uri",
                        "validator_sha256",
                        "Fail-closed validation of v5 lineage, v6 bindings, receipt self-hash, and launch locks.",
                    ),
                    (
                        "a12-live-preflight-v6-preflight-module",
                        "A1.2 synthetic live preflight module v6",
                        "tool",
                        "preflight_module_uri",
                        "preflight_module_sha256",
                        "Implements synthetic-only runtime identity, adapter parity, Qwen length, and checkpoint/resume checks without protected evaluation inputs.",
                    ),
                    (
                        "a12-live-preflight-v6-owner-runbook",
                        "A1.2 beginner Owner runbook v6",
                        "runbook",
                        "owner_runbook_uri",
                        "owner_runbook_sha256",
                        "Documents the direct-base live preflight and safe artifact collection while preserving the launch lock.",
                    ),
                ):
                    uri = vast_v6.get(uri_key)
                    digest = vast_v6.get(sha_key)
                    if uri and digest:
                        result.append(
                            _artifact(
                                artifact_id=artifact_id,
                                title=title,
                                artifact_type=artifact_type,
                                evidence_class="live_engineering_preflight_correction",
                                scientific_authority=False,
                                safe_uri=str(uri),
                                content_sha256=str(digest),
                                explanation=explanation,
                                producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                                producing_task_id="A1.2",
                            )
                        )
                policy = vast_v6.get("continuation_policy", {})
                if isinstance(policy, Mapping) and policy.get("validated") is True:
                    result.append(
                        _artifact(
                            artifact_id="a12-owner-instance-continuation-policy-v1",
                            title="A1.2 Owner conditional instance-continuation policy",
                            artifact_type="decision",
                            evidence_class="owner_policy_for_engineering_continuity",
                            scientific_authority=False,
                            safe_uri=str(policy["policy_uri"]),
                            content_sha256=str(policy["policy_sha256"]),
                            explanation="Keeps provider destruction as the default; continuation is possible only after complete safe preflight evidence, unchanged identity and budget, an active watchdog, and a separately authorized next PLAN goal.",
                            producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                            producing_task_id="A1.2",
                        )
                    )
            vast_v7 = scaffold.get("vast_preflight_v7", {})
            if isinstance(vast_v7, Mapping) and vast_v7.get("validated") is True:
                for (
                    artifact_id,
                    title,
                    artifact_type,
                    uri_key,
                    sha_key,
                    explanation,
                ) in (
                    (
                        "a12-live-preflight-v7-receipt",
                        "A1.2 same-instance repair receipt v7",
                        "receipt",
                        "receipt_uri",
                        "receipt_sha256",
                        "Preserves the v6 live failures, binds the same-instance repair, requires a fresh runtime root and bytecode suppression, and keeps every authorization flag false.",
                    ),
                    (
                        "a12-live-preflight-v7-contract",
                        "A1.2 same-instance repair contract v7",
                        "contract",
                        "contract_uri",
                        "contract_sha256",
                        "Binds v6 lineage, the continuation policy, hash-validated staged reuse, the supplement wheelhouse workflow, and synthetic-only preflight behavior.",
                    ),
                    (
                        "a12-live-preflight-v7-schema",
                        "A1.2 same-instance repair receipt schema v7",
                        "schema",
                        "schema_uri",
                        "schema_sha256",
                        "Validates two preserved repair failures, bytecode suppression, false authorization flags, and zero counters.",
                    ),
                    (
                        "a12-live-preflight-v7-validator",
                        "A1.2 same-instance repair validator v7",
                        "tool",
                        "validator_uri",
                        "validator_sha256",
                        "Fail-closed validation of v6 lineage, same-instance repair bindings, fresh-root correction, and unchanged zero counters.",
                    ),
                    (
                        "a12-live-preflight-v7-owner-runbook",
                        "A1.2 beginner Owner same-instance repair runbook v7",
                        "runbook",
                        "owner_runbook_uri",
                        "owner_runbook_sha256",
                        "Documents v7 dry-run staging, structural verification, synthetic-only preflight, safe collection, default destruction, and conditional continuation.",
                    ),
                    (
                        "a12-live-preflight-v7-coordinator",
                        "A1.2 same-instance repair coordinator v7",
                        "tool",
                        "coordinator_uri",
                        "coordinator_sha256",
                        "Stages only the new frozen code bundle and reuses prior staged inputs only after checksum validation.",
                    ),
                    (
                        "a12-live-preflight-v7-bootstrap",
                        "A1.2 same-instance repair bootstrap v7",
                        "tool",
                        "bootstrap_uri",
                        "bootstrap_sha256",
                        "Creates the fresh runtime root with bytecode suppression and verifies the reuse boundary before synthetic work.",
                    ),
                    (
                        "a12-live-preflight-v7-supplement-validator",
                        "A1.2 preflight supplement validator v7",
                        "tool",
                        "supplement_validator_uri",
                        "supplement_validator_sha256",
                        "Validates the hash-bound dependency supplement without network fallback.",
                    ),
                    (
                        "a12-live-preflight-v7-supplement-requirements",
                        "A1.2 preflight supplement requirements v7",
                        "manifest",
                        "supplement_requirements_uri",
                        "supplement_requirements_sha256",
                        "Records the small offline dependency supplement required after the preserved missing-pydantic failure.",
                    ),
                    (
                        "a12-live-preflight-v7-supplement-workflow",
                        "A1.2 supplement wheelhouse workflow v7",
                        "workflow",
                        "supplement_workflow_uri",
                        "supplement_workflow_sha256",
                        "Produces a Linux-compatible, checksum-bound supplement wheelhouse without models or protected data.",
                    ),
                ):
                    uri = vast_v7.get(uri_key)
                    digest = vast_v7.get(sha_key)
                    if uri and digest:
                        result.append(
                            _artifact(
                                artifact_id=artifact_id,
                                title=title,
                                artifact_type=artifact_type,
                                evidence_class="live_engineering_preflight_repair",
                                scientific_authority=False,
                                safe_uri=str(uri),
                                content_sha256=str(digest),
                                explanation=explanation,
                                producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                                producing_task_id="A1.2",
                            )
                        )
            vast_v8 = scaffold.get("vast_preflight_v8", {})
            if isinstance(vast_v8, Mapping) and vast_v8.get("validated") is True:
                for (
                    artifact_id,
                    title,
                    artifact_type,
                    uri_key,
                    sha_key,
                    explanation,
                ) in (
                    (
                        "a12-live-preflight-v8-receipt",
                        "A1.2 validation-complete frozen-bundle repair receipt v8",
                        "receipt",
                        "receipt_uri",
                        "receipt_sha256",
                        "Preserves all v6-v7 failed-closed evidence and binds a validation-complete frozen code bundle repair with every authorization flag false.",
                    ),
                    (
                        "a12-live-preflight-v8-contract",
                        "A1.2 validation-complete frozen-bundle repair contract v8",
                        "contract",
                        "contract_uri",
                        "contract_sha256",
                        "Binds the fresh v8 root, checksum-gated same-instance reuse, historical validation lineage, and synthetic-only preflight boundary.",
                    ),
                    (
                        "a12-live-preflight-v8-schema",
                        "A1.2 validation-complete frozen-bundle repair schema v8",
                        "schema",
                        "schema_uri",
                        "schema_sha256",
                        "Validates the additive v8 receipt shape, preserved failure history, false authorization flags, and zero counters.",
                    ),
                    (
                        "a12-live-preflight-v8-validator",
                        "A1.2 validation-complete frozen-bundle validator v8",
                        "tool",
                        "validator_uri",
                        "validator_sha256",
                        "Fails closed unless the frozen bundle contains all historical validator lineage required without remote Git metadata.",
                    ),
                    (
                        "a12-live-preflight-v8-owner-runbook",
                        "A1.2 beginner Owner validation-complete bundle runbook v8",
                        "runbook",
                        "owner_runbook_uri",
                        "owner_runbook_sha256",
                        "Documents the bounded v8 synthetic-only repair and retains the conditional instance-continuation policy.",
                    ),
                    (
                        "a12-live-preflight-v8-coordinator",
                        "A1.2 validation-complete bundle coordinator v8",
                        "tool",
                        "coordinator_uri",
                        "coordinator_sha256",
                        "Stages only the new validation-complete frozen code bundle into a fresh remote root.",
                    ),
                    (
                        "a12-live-preflight-v8-bootstrap",
                        "A1.2 validation-complete bundle bootstrap v8",
                        "tool",
                        "bootstrap_uri",
                        "bootstrap_sha256",
                        "Validates historical lineage from frozen bytes before any synthetic preflight work.",
                    ),
                ):
                    uri = vast_v8.get(uri_key)
                    digest = vast_v8.get(sha_key)
                    if uri and digest:
                        result.append(
                            _artifact(
                                artifact_id=artifact_id,
                                title=title,
                                artifact_type=artifact_type,
                                evidence_class="live_engineering_preflight_packaging_repair",
                                scientific_authority=False,
                                safe_uri=str(uri),
                                content_sha256=str(digest),
                                explanation=explanation,
                                producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                                producing_task_id="A1.2",
                            )
                        )
            vast_v9 = scaffold.get("vast_preflight_v9", {})
            if isinstance(vast_v9, Mapping) and vast_v9.get("validated") is True:
                for (
                    artifact_id,
                    title,
                    artifact_type,
                    uri_key,
                    sha_key,
                    explanation,
                ) in (
                    (
                        "a12-live-preflight-v9-receipt",
                        "A1.2 execution-lifecycle repair receipt v9",
                        "receipt",
                        "receipt_uri",
                        "receipt_sha256",
                        "Binds the attempt-scoped synthetic lifecycle repair while keeping scientific launch, adoption, measured runs, and charged-resource counters closed.",
                    ),
                    (
                        "a12-live-preflight-v9-contract",
                        "A1.2 execution-lifecycle repair contract v9",
                        "contract",
                        "contract_uri",
                        "contract_sha256",
                        "Binds v8 lineage, fresh-root reuse, PID identity, checkpoint, export, teardown, and synthetic-only controls.",
                    ),
                    (
                        "a12-live-preflight-v9-schema",
                        "A1.2 execution-lifecycle repair schema v9",
                        "schema",
                        "schema_uri",
                        "schema_sha256",
                        "Validates the v9 receipt, completed implementation state, pending live preflight, false authorization flags, and zero counters.",
                    ),
                    (
                        "a12-live-preflight-v9-validator",
                        "A1.2 execution-lifecycle contract validator v9",
                        "tool",
                        "validator_uri",
                        "validator_sha256",
                        "Fails closed on v8 lineage or any changed v9 implementation binding.",
                    ),
                    (
                        "a12-live-preflight-v9-runtime",
                        "A1.2 attempt-scoped live runtime v9",
                        "tool",
                        "runtime_uri",
                        "runtime_sha256",
                        "Implements process identity, fresh heartbeat, durable checkpoints, adapter-level Qwen measurement, safe export, and verified teardown.",
                    ),
                    (
                        "a12-live-preflight-v9-owner-runbook",
                        "A1.2 beginner Owner execution-lifecycle runbook v9",
                        "runbook",
                        "owner_runbook_uri",
                        "owner_runbook_sha256",
                        "Provides exact local SSH coordinator commands without credentials or protected data.",
                    ),
                    (
                        "a12-live-preflight-v9-coordinator",
                        "A1.2 execution-lifecycle coordinator v9",
                        "tool",
                        "coordinator_uri",
                        "coordinator_sha256",
                        "Stages a fresh root, gates start on the marker, validates collection end to end, and keeps provider destruction separate.",
                    ),
                    (
                        "a12-live-preflight-v9-bootstrap",
                        "A1.2 execution-lifecycle bootstrap v9",
                        "tool",
                        "bootstrap_uri",
                        "bootstrap_sha256",
                        "Revalidates archive bytes and members before bundled Python and writes a runtime-bound marker.",
                    ),
                    (
                        "a12-live-preflight-v9-launcher",
                        "A1.2 four-GPU synthetic launcher v9",
                        "tool",
                        "launcher_uri",
                        "launcher_sha256",
                        "Maps one arm per GPU, cancels siblings on failure, reaps children, and completes only after same-attempt PASS.",
                    ),
                ):
                    uri = vast_v9.get(uri_key)
                    digest = vast_v9.get(sha_key)
                    if uri and digest:
                        result.append(
                            _artifact(
                                artifact_id=artifact_id,
                                title=title,
                                artifact_type=artifact_type,
                                evidence_class="live_engineering_preflight_execution_lifecycle_repair",
                                scientific_authority=False,
                                safe_uri=str(uri),
                                content_sha256=str(digest),
                                explanation=explanation,
                                producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                                producing_task_id="A1.2",
                            )
                        )
                live_result_uri = vast_v9.get("live_result_uri")
                live_result_sha = vast_v9.get("live_result_sha256")
                if live_result_uri and live_result_sha:
                    result.append(
                        _artifact(
                            artifact_id="a12-live-synthetic-preflight-result-v9",
                            title="A1.2 live synthetic preflight result receipt v9",
                            artifact_type="receipt",
                            evidence_class="live_engineering_synthetic_preflight",
                            scientific_authority=False,
                            safe_uri=str(live_result_uri),
                            content_sha256=str(live_result_sha),
                            explanation="Aggregate-only PASS receipt for the completed four-GPU synthetic preflight; it binds per-arm hashes, Qwen adapter length, lifecycle export, and teardown while keeping scientific authorization closed.",
                            producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                            producing_task_id="A1.2",
                        )
                    )
                closeout = scaffold.get("provider_closeout_v10", {})
                if isinstance(closeout, Mapping) and closeout.get("validated") is True:
                    closeout_uri = closeout.get("receipt_uri")
                    closeout_sha = closeout.get("receipt_sha256")
                    if closeout_uri and closeout_sha:
                        result.append(
                            _artifact(
                                artifact_id="a12-provider-closeout-result-v10",
                                title="A1.2 Owner-local provider closeout receipt v10",
                                artifact_type="receipt",
                                evidence_class="owner_local_provider_closeout",
                                scientific_authority=False,
                                safe_uri=str(closeout_uri),
                                content_sha256=str(closeout_sha),
                                explanation="Binds the immutable v9 result to the later Owner destroy attestation and sanitized endpoint-unreachable observation, while recording the absence of an independent provider API record and keeping all scientific authorization closed.",
                                producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                                producing_task_id="A1.2",
                            )
                        )
                request_v11 = scaffold.get("scientific_execution_request_v11", {})
                if (
                    isinstance(request_v11, Mapping)
                    and request_v11.get("validated") is True
                ):
                    for (
                        artifact_id,
                        title,
                        artifact_type,
                        uri_key,
                        sha_key,
                        explanation,
                    ) in (
                        (
                            "a12-scientific-request-v11",
                            "A1.2 scientific execution and adoption request v11",
                            "contract",
                            "request_uri",
                            "request_sha256",
                            "Freezes a future five-arm scientific request for Owner review while keeping provider contact, adoption, measured retrieval, Selection, and Final closed.",
                        ),
                        (
                            "a12-scientific-request-receipt-v11",
                            "A1.2 scientific request preparation receipt v11",
                            "receipt",
                            "receipt_uri",
                            "receipt_sha256",
                            "Validates the repaired request, eleven immutable lineage bindings, five workloads, zero counters, and the separate-adoption boundary.",
                        ),
                        (
                            "a12-scientific-request-schema-v11",
                            "A1.2 scientific request schema v11",
                            "schema",
                            "request_schema_uri",
                            "request_schema_sha256",
                            "Fail-closes request authorization, lineage, components, future identities, and zero-counter invariants.",
                        ),
                        (
                            "a12-scientific-request-receipt-schema-v11",
                            "A1.2 scientific request receipt schema v11",
                            "schema",
                            "receipt_schema_uri",
                            "receipt_schema_sha256",
                            "Validates the preparation receipt and its non-authorizing lifecycle.",
                        ),
                        (
                            "a12-scientific-request-runbook-v11",
                            "A1.2 scientific request runbook v11",
                            "runbook",
                            "runbook_uri",
                            "runbook_sha256",
                            "Explains the protected transfer, exact programs, result evidence, budget admission, and Owner-review boundary.",
                        ),
                        (
                            "a12-scientific-request-ledger-v11",
                            "A1.2 scientific request append-only ledger v11",
                            "ledger",
                            "ledger_uri",
                            "ledger_sha256",
                            "Preserves the schema failure, independent-review rejection, repairs, and rigor-review closeout.",
                        ),
                        (
                            "a12-scientific-request-rigor-v11",
                            "A1.2 scientific request artifact-only rigor review",
                            "audit",
                            "rigor_review_uri",
                            "rigor_review_sha256",
                            "Accepts the repaired preparation request with no blocking finding while retaining live and protected obligations.",
                        ),
                    ):
                        uri = request_v11.get(uri_key)
                        digest = request_v11.get(sha_key)
                        if uri and digest:
                            result.append(
                                _artifact(
                                    artifact_id=artifact_id,
                                    title=title,
                                    artifact_type=artifact_type,
                                    evidence_class="scientific_execution_adoption_request_preparation",
                                    scientific_authority=False,
                                    safe_uri=str(uri),
                                    content_sha256=str(digest),
                                    explanation=explanation,
                                    producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                                    producing_task_id="A1.2",
                                )
                            )
                    component_metadata = {
                        "budget": ("A1.2 v11 all-fee budget request", "budget"),
                        "protected_evaluator_handoff": (
                            "A1.2 v11 protected evaluator handoff",
                            "contract",
                        ),
                        "stop_conditions": (
                            "A1.2 v11 scientific stop conditions",
                            "contract",
                        ),
                        "provider_admission": (
                            "A1.2 v11 fresh provider admission plan",
                            "contract",
                        ),
                        "scientific_transfer": (
                            "A1.2 v11 scientific transfer and safe-return contract",
                            "contract",
                        ),
                        "common_program_set": (
                            "A1.2 v11 executable common-program set",
                            "manifest",
                        ),
                        "aggregate_result_contract": (
                            "A1.2 v11 aggregate result contract",
                            "contract",
                        ),
                        "workload_set": (
                            "A1.2 v11 five-arm workload manifest set",
                            "manifest",
                        ),
                    }
                    for component_id, binding in request_v11.get(
                        "component_bindings", {}
                    ).items():
                        if (
                            component_id not in component_metadata
                            or not isinstance(binding, Mapping)
                            or not binding.get("uri")
                            or not binding.get("file_sha256")
                        ):
                            continue
                        title, artifact_type = component_metadata[component_id]
                        result.append(
                            _artifact(
                                artifact_id=f"a12-v11-{component_id.replace('_', '-')}",
                                title=title,
                                artifact_type=artifact_type,
                                evidence_class="scientific_execution_adoption_request_preparation",
                                scientific_authority=False,
                                safe_uri=str(binding["uri"]),
                                content_sha256=str(binding["file_sha256"]),
                                explanation="Hash-bound additive v11 request component; it is prepared for review and not adopted for execution.",
                                producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                                producing_task_id="A1.2",
                            )
                        )
                    for job in request_v11.get("jobs", []):
                        if not isinstance(job, Mapping):
                            continue
                        result.append(
                            _artifact(
                                artifact_id=f"a12-v11-job-{str(job.get('arm_id', 'unknown')).lower()}",
                                title=f"A1.2 v11 {job.get('arm_id', 'unknown')} scientific workload",
                                artifact_type="manifest",
                                evidence_class="scientific_execution_adoption_request_preparation",
                                scientific_authority=False,
                                safe_uri=str(job.get("uri")),
                                content_sha256=str(job.get("manifest_sha256")),
                                explanation="Freezes one arm's five common programs, device mapping, protected transfer binding, aggregate result requirements, and launch locks.",
                                producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                                producing_task_id="A1.2",
                            )
                        )
                adoption = scaffold.get("adoption_inputs_v12_r3", {})
                if isinstance(adoption, Mapping) and adoption.get("validated") is True:
                    for (
                        artifact_id,
                        title,
                        artifact_type,
                        uri_key,
                        sha_key,
                        explanation,
                    ) in (
                        (
                            "a12-adoption-inputs-v12-r3",
                            "A1.2 local scientific-execution adoption inputs v12-r3",
                            "contract",
                            "contract_uri",
                            "contract_sha256",
                            "Binds the unchanged v11 request to local-only bundle, protected compilation, publication, and disposition requirements while preserving the provider and launch locks.",
                        ),
                        (
                            "a12-adoption-inputs-schema-v12-r3",
                            "A1.2 local adoption-inputs schema v12-r3",
                            "schema",
                            "contract_schema_uri",
                            "contract_schema_sha256",
                            "Defines the aggregate-safe, non-authorizing v12-r3 contract shape.",
                        ),
                        (
                            "a12-adoption-inputs-validator-v12-r3",
                            "A1.2 local adoption-inputs validator v12-r3",
                            "tool",
                            "validator_uri",
                            "validator_sha256",
                            "Fails closed on changed v11/v12/v13 bindings or a mismatched frozen bundle path set.",
                        ),
                    ):
                        uri = adoption.get(uri_key)
                        digest = adoption.get(sha_key)
                        if uri and digest:
                            result.append(
                                _artifact(
                                    artifact_id=artifact_id,
                                    title=title,
                                    artifact_type=artifact_type,
                                    evidence_class="scientific_execution_adoption_input_preparation",
                                    scientific_authority=False,
                                    safe_uri=str(uri),
                                    content_sha256=str(digest),
                                    explanation=explanation,
                                    producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                                    producing_task_id="A1.2",
                                )
                            )
                    publication = adoption.get("publication_impact", {})
                    if isinstance(publication, Mapping):
                        for (
                            artifact_id,
                            title,
                            artifact_type,
                            uri_key,
                            sha_key,
                            explanation,
                        ) in (
                            (
                                "a12-publication-impact-contract-v13",
                                "A1.2 publication-impact preregistration v13",
                                "contract",
                                "contract_uri",
                                "contract_sha256",
                                "Pre-registers A1.2 as candidate exposure and representation screening with OUT Recall@100 primary, required nDCG secondary outcomes, and no pre-confirmation publication claim.",
                            ),
                            (
                                "a12-publication-impact-schema-v13",
                                "A1.2 publication-impact schema v13",
                                "schema",
                                "schema_uri",
                                "schema_sha256",
                                "Freezes the primary/secondary outcome hierarchy, comparisons, candidate promotion guard, and protected reporting boundary.",
                            ),
                            (
                                "a12-publication-impact-preregistration-v13",
                                "A1.2 publication-impact preregistration note v13",
                                "documentation",
                                "documentation_uri",
                                "documentation_sha256",
                                "Human-readable, hash-bound explanation of the additive publication-impact contract.",
                            ),
                        ):
                            uri = publication.get(uri_key)
                            digest = publication.get(sha_key)
                            if uri and digest:
                                result.append(
                                    _artifact(
                                        artifact_id=artifact_id,
                                        title=title,
                                        artifact_type=artifact_type,
                                        evidence_class="publication_analysis_preregistration_hardening",
                                        scientific_authority=False,
                                        safe_uri=str(uri),
                                        content_sha256=str(digest),
                                        explanation=explanation,
                                        producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                                        producing_task_id="A1.2",
                                    )
                                )
                    disposition = adoption.get("instance_disposition", {})
                    if isinstance(disposition, Mapping):
                        for (
                            artifact_id,
                            title,
                            artifact_type,
                            uri_key,
                            sha_key,
                            explanation,
                        ) in (
                            (
                                "a12-instance-disposition-policy-v13",
                                "A1.2 instance disposition policy v13",
                                "policy",
                                "policy_uri",
                                "policy_sha256",
                                "Requires evidence-backed REUSE_ELIGIBLE or DESTROY_REQUIRED classification after safe return and preserves the default no-live-instance state.",
                            ),
                            (
                                "a12-instance-disposition-result-schema-v13",
                                "A1.2 instance disposition result schema v13",
                                "schema",
                                "schema_uri",
                                "schema_sha256",
                                "Defines the aggregate-safe classification receipt and forbids any execution authorization.",
                            ),
                        ):
                            uri = disposition.get(uri_key)
                            digest = disposition.get(sha_key)
                            if uri and digest:
                                result.append(
                                    _artifact(
                                        artifact_id=artifact_id,
                                        title=title,
                                        artifact_type=artifact_type,
                                        evidence_class="owner_policy_for_instance_disposition",
                                        scientific_authority=False,
                                        safe_uri=str(uri),
                                        content_sha256=str(digest),
                                        explanation=explanation,
                                        producing_phase_id="A1_BASELINES_AND_MULTI_ARM_SCREENING",
                                        producing_task_id="A1.2",
                                    )
                                )
    return result


def _metrics(
    model: Mapping[str, Any], phase_id: str, task_id: str | None
) -> list[dict[str, Any]]:
    if phase_id == "A2_PER_ARM_AUTOINDEX":
        freeze = model.get("armindex", {}).get("a2_candidate_freeze", {})
        if not isinstance(freeze, Mapping) or freeze.get("validated") is not True:
            return []
        credit = (
            freeze.get("official_credit", {})
            if isinstance(freeze.get("official_credit"), Mapping)
            else {}
        )
        specs = (
            ("frozen_candidate_count", freeze.get("candidate_count"), "candidate_universe"),
            ("matched_candidate_count", freeze.get("matched_candidate_count"), "matched_tier"),
            (
                "dormant_reserve_candidate_count",
                freeze.get("conditional_reserve_candidate_count"),
                "conditional_reserve_tier",
            ),
            ("official_credit_check_count", freeze.get("credit_check_count"), "credit_checkpoints"),
            ("official_credit_used_percent", credit.get("used_percent"), "official_credit_window"),
            (
                "official_credit_remaining_percent",
                credit.get("remaining_percent"),
                "official_credit_window",
            ),
            ("measured_a2_runs", 0, "measured_A2"),
        )
        rows = [
            {
                "name": name,
                "cutoff": 0,
                "split": "premeasurement",
                "scope": "A2 candidate freeze",
                "value": value,
                "n": 1,
                "denominator": denominator,
                "source_uri": freeze.get("credit_correction_receipt_uri")
                if name.startswith("official_credit")
                else freeze.get("freeze_receipt_uri"),
                "source_sha256": freeze.get("credit_correction_receipt_file_sha256")
                if name.startswith("official_credit")
                else freeze.get("freeze_receipt_file_sha256"),
            }
            for name, value, denominator in specs
        ]
        readiness = model.get("armindex", {}).get("a2_execution_readiness", {})
        if isinstance(readiness, Mapping) and readiness.get("validated") is True:
            rows.extend(
                {
                    "name": name,
                    "cutoff": 0,
                    "split": "premeasurement",
                    "scope": "A2 execution readiness",
                    "value": value,
                    "n": 1,
                    "denominator": denominator,
                    "source_uri": readiness.get("contract_uri"),
                    "source_sha256": readiness.get("contract_file_sha256"),
                }
                for name, value, denominator in (
                    (
                        "a2_forward_hard_stop_usd",
                        readiness.get("forward_hard_stop_usd"),
                        "all_fee_whole_workload",
                    ),
                    (
                        "a2_owner_ttl_hours",
                        readiness.get("owner_ttl_hours"),
                        "provider_watchdog",
                    ),
                    (
                        "a2_provider_admissions",
                        int(bool(readiness.get("provider_admission_performed"))),
                        "current_attempt",
                    ),
                    (
                        "a2_execution_adoptions",
                        int(
                            bool(
                                readiness.get(
                                    "provider_execution_adoption_performed"
                                )
                            )
                        ),
                        "current_attempt",
                    ),
                )
            )
        return rows
    if phase_id == "A1_BASELINES_AND_MULTI_ARM_SCREENING" and task_id in {None, "A1.1"}:
        adapter = model.get("armindex", {}).get("adapter_fixture_validation", {})
        if not isinstance(adapter, Mapping) or adapter.get("validated") is not True:
            return []
        observation = adapter.get("cpu_observation", {})
        if not isinstance(observation, Mapping):
            return []
        latency = observation.get("latency_ms", {})
        repetitions = int(observation.get("repetitions", 0))
        rows = []
        for operation in ("compile", "index_build", "search_workload"):
            summary = latency.get(operation, {}) if isinstance(latency, Mapping) else {}
            rows.append(
                {
                    "name": f"fixture_{operation}_latency_p50_ms",
                    "cutoff": 100,
                    "split": "synthetic",
                    "scope": "A1.1",
                    "value": summary.get("p50")
                    if isinstance(summary, Mapping)
                    else None,
                    "n": repetitions,
                    "denominator": "host_observed_fixed_synthetic_adapter_workload",
                    "source_uri": adapter.get("fixture_receipt_uri"),
                    "source_sha256": adapter.get("fixture_receipt_sha256"),
                }
            )
        rows.extend(
            (
                {
                    "name": "fixture_search_throughput_qps",
                    "cutoff": 100,
                    "split": "synthetic",
                    "scope": "A1.1",
                    "value": observation.get("search_throughput_qps"),
                    "n": observation.get("workload_calls"),
                    "denominator": "host_observed_fixed_synthetic_adapter_workload",
                    "source_uri": adapter.get("fixture_receipt_uri"),
                    "source_sha256": adapter.get("fixture_receipt_sha256"),
                },
                {
                    "name": "fixture_peak_python_allocation_bytes",
                    "cutoff": 100,
                    "split": "synthetic",
                    "scope": "A1.1",
                    "value": observation.get("peak_python_allocation_bytes"),
                    "n": repetitions,
                    "denominator": "tracemalloc_peak_for_fixed_synthetic_adapter_workload",
                    "source_uri": adapter.get("fixture_receipt_uri"),
                    "source_sha256": adapter.get("fixture_receipt_sha256"),
                },
            )
        )
        for metric in adapter.get("synthetic_metrics", []):
            if isinstance(metric, Mapping):
                rows.append(
                    {
                        "name": f"fixture_{metric.get('name')}",
                        "cutoff": metric.get("cutoff"),
                        "split": "synthetic",
                        "scope": "A1.1",
                        "value": metric.get("value"),
                        "n": metric.get("n"),
                        "denominator": metric.get("denominator"),
                        "source_uri": adapter.get("fixture_receipt_uri"),
                        "source_sha256": adapter.get("fixture_receipt_sha256"),
                    }
                )
        return rows
    if phase_id == "A1_BASELINES_AND_MULTI_ARM_SCREENING" and task_id in {None, "A1.2"}:
        current_attempt = model.get("armindex", {}).get("a1_2_current_attempt", {})
        summary = (
            current_attempt.get("measured_result_summary", {})
            if isinstance(current_attempt, Mapping)
            else {}
        )
        if (
            current_attempt.get("validated") is True
            and current_attempt.get("status") == "PASS"
            and isinstance(summary, Mapping)
            and summary.get("status") == "PASS"
        ):
            rows = []
            for arm in summary.get("arm_results", []):
                if not isinstance(arm, Mapping):
                    continue
                for name, source_key, cutoff in (
                    ("out_recall_at_100_mean", "out_recall_at_100_mean", 100),
                    ("out_ndcg_at_100_mean", "out_ndcg_at_100_mean", 100),
                    ("out_ndcg_at_10_mean", "out_ndcg_at_10_mean", 10),
                    (
                        "search_latency_p95_ms_mean",
                        "search_latency_p95_ms_mean",
                        100,
                    ),
                    ("wall_seconds_sum", "wall_seconds_sum", 100),
                    ("failure_rate_mean", "failure_rate_mean", 100),
                ):
                    rows.append(
                        {
                            "name": f"{arm.get('arm_id', 'unknown').lower()}_{name}",
                            "cutoff": cutoff,
                            "split": "REP-DEV",
                            "scope": "A1.2",
                            "value": arm.get(source_key),
                            "n": arm.get("program_count"),
                            "denominator": "mean_across_five_frozen_common_programs"
                            if name != "wall_seconds_sum"
                            else "sum_across_five_frozen_common_programs",
                            "source_uri": summary.get("summary_uri"),
                            "source_sha256": summary.get("summary_file_sha256"),
                        }
                    )
            return rows
        scaffold = model.get("armindex", {}).get("a1_2_contract_scaffold", {})
        if not isinstance(scaffold, Mapping) or scaffold.get("validated") is not True:
            return []
        blockers = scaffold.get("preflight_blockers", [])
        rows = [
            {
                "name": "owner_local_cpu_preflight_blocker_count",
                "cutoff": 0,
                "split": "engineering_preflight",
                "scope": "A1.2",
                "value": len(blockers) if isinstance(blockers, list) else 0,
                "n": 1,
                "denominator": "pending_owner_launch_checklist_items",
                "source_uri": scaffold.get("preflight_uri"),
                "source_sha256": scaffold.get("preflight_sha256"),
            }
        ]
        vast = scaffold.get("vast_preflight_v2", {})
        if isinstance(vast, Mapping) and vast.get("validated") is True:
            metric_specs = (
                (
                    "vast_v2_live_check_pending_count",
                    vast.get("live_check_count"),
                    1,
                    "frozen_live_owner_checklist_items",
                    "checklist_uri",
                    "checklist_sha256",
                ),
                (
                    "vast_v2_synthetic_worker_count",
                    vast.get("synthetic_worker_count"),
                    vast.get("synthetic_worker_count"),
                    "completed_synthetic_worker_processes",
                    "synthetic_receipt_uri",
                    "synthetic_receipt_sha256",
                ),
                (
                    "vast_v2_synthetic_parallel_launch_count",
                    vast.get("synthetic_parallel_launch_count"),
                    vast.get("synthetic_worker_count"),
                    "synthetic_workers_started_in_parallel",
                    "synthetic_receipt_uri",
                    "synthetic_receipt_sha256",
                ),
                (
                    "vast_v2_planning_rate_usd_per_instance_hour",
                    vast.get("planning_rate_usd"),
                    1,
                    "complete_four_rtx3090_instance",
                    "budget_uri",
                    "budget_sha256",
                ),
                (
                    "vast_v2_estimated_instance_hours_min",
                    vast.get("estimated_instance_hours_min"),
                    1,
                    "planning_estimate_not_authorization",
                    "budget_uri",
                    "budget_sha256",
                ),
                (
                    "vast_v2_estimated_instance_hours_max",
                    vast.get("estimated_instance_hours_max"),
                    1,
                    "planning_estimate_not_authorization",
                    "budget_uri",
                    "budget_sha256",
                ),
                (
                    "vast_v2_estimated_raw_worker_usd_min",
                    vast.get("estimated_raw_worker_usd_min"),
                    1,
                    "planning_estimate_not_authorization",
                    "budget_uri",
                    "budget_sha256",
                ),
                (
                    "vast_v2_estimated_raw_worker_usd_max",
                    vast.get("estimated_raw_worker_usd_max"),
                    1,
                    "planning_estimate_not_authorization",
                    "budget_uri",
                    "budget_sha256",
                ),
            )
            rows.extend(
                {
                    "name": name,
                    "cutoff": 0,
                    "split": "engineering_preflight",
                    "scope": "A1.2",
                    "value": value,
                    "n": n,
                    "denominator": denominator,
                    "source_uri": vast.get(uri_key),
                    "source_sha256": vast.get(sha_key),
                }
                for name, value, n, denominator, uri_key, sha_key in metric_specs
            )
        vast_v3 = scaffold.get("vast_preflight_v3", {})
        if isinstance(vast_v3, Mapping) and vast_v3.get("validated") is True:
            rows.extend(
                [
                    {
                        "name": "vast_v3_planning_rate_usd_per_instance_hour",
                        "cutoff": 0,
                        "split": "engineering_preflight",
                        "scope": "A1.2",
                        "value": vast_v3.get("planning_rate_usd"),
                        "n": 1,
                        "denominator": "complete_four_rtx3090_instance",
                        "source_uri": vast_v3.get("receipt_uri"),
                        "source_sha256": vast_v3.get("receipt_sha256"),
                    },
                    {
                        "name": "vast_v3_common_screen_hard_stop_usd",
                        "cutoff": 0,
                        "split": "engineering_preflight",
                        "scope": "A1.2",
                        "value": vast_v3.get("common_screen_hard_stop_usd"),
                        "n": 1,
                        "denominator": "hard_stop_not_spend_authorization",
                        "source_uri": vast_v3.get("receipt_uri"),
                        "source_sha256": vast_v3.get("receipt_sha256"),
                    },
                ]
            )
        vast_v5 = scaffold.get("vast_preflight_v5", {})
        if isinstance(vast_v5, Mapping) and vast_v5.get("validated") is True:
            rows.extend(
                [
                    {
                        "name": "vast_v5_direct_base_live_check_pending_count",
                        "cutoff": 0,
                        "split": "engineering_preflight",
                        "scope": "A1.2",
                        "value": len(vast_v5.get("live_checks_pending", [])),
                        "n": 1,
                        "denominator": "direct_base_live_preflight_checks",
                        "source_uri": vast_v5.get("receipt_uri"),
                        "source_sha256": vast_v5.get("receipt_sha256"),
                    },
                    {
                        "name": "vast_v5_custom_local_docker_build_removed",
                        "cutoff": 0,
                        "split": "engineering_preflight",
                        "scope": "A1.2",
                        "value": int(vast_v5.get("custom_local_docker_build") is False),
                        "n": 1,
                        "denominator": "active_direct_base_path",
                        "source_uri": vast_v5.get("receipt_uri"),
                        "source_sha256": vast_v5.get("receipt_sha256"),
                    },
                ]
            )
        vast_v6 = scaffold.get("vast_preflight_v6", {})
        if isinstance(vast_v6, Mapping) and vast_v6.get("validated") is True:
            rows.extend(
                [
                    {
                        "name": "vast_v6_live_quote_usd_per_instance_hour",
                        "cutoff": 0,
                        "split": "engineering_preflight",
                        "scope": "A1.2",
                        "value": vast_v6.get("live_quote_usd_per_hour"),
                        "n": 1,
                        "denominator": "quoted_complete_four_rtx3090_instance_not_spend_authorization",
                        "source_uri": vast_v6.get("contract_uri"),
                        "source_sha256": vast_v6.get("contract_sha256"),
                    },
                    {
                        "name": "vast_v6_synthetic_preflight_only",
                        "cutoff": 0,
                        "split": "engineering_preflight",
                        "scope": "A1.2",
                        "value": int(vast_v6.get("synthetic_preflight_only") is True),
                        "n": 1,
                        "denominator": "live_correction_authorization_boundary",
                        "source_uri": vast_v6.get("receipt_uri"),
                        "source_sha256": vast_v6.get("receipt_sha256"),
                    },
                ]
            )
        vast_v7 = scaffold.get("vast_preflight_v7", {})
        if isinstance(vast_v7, Mapping) and vast_v7.get("validated") is True:
            rows.extend(
                [
                    {
                        "name": "vast_v7_preserved_live_failure_count",
                        "cutoff": 0,
                        "split": "engineering_preflight",
                        "scope": "A1.2",
                        "value": len(vast_v7.get("preserved_live_failures", [])),
                        "n": 1,
                        "denominator": "preserved_same_instance_repair_failures",
                        "source_uri": vast_v7.get("receipt_uri"),
                        "source_sha256": vast_v7.get("receipt_sha256"),
                    },
                    {
                        "name": "vast_v7_bytecode_suppression_required",
                        "cutoff": 0,
                        "split": "engineering_preflight",
                        "scope": "A1.2",
                        "value": int(
                            vast_v7.get("active_correction", {}).get(
                                "pythondontwritebytecode"
                            )
                            is True
                        ),
                        "n": 1,
                        "denominator": "fresh_same_instance_repair_root",
                        "source_uri": vast_v7.get("receipt_uri"),
                        "source_sha256": vast_v7.get("receipt_sha256"),
                    },
                ]
            )
        vast_v8 = scaffold.get("vast_preflight_v8", {})
        if isinstance(vast_v8, Mapping) and vast_v8.get("validated") is True:
            rows.extend(
                [
                    {
                        "name": "vast_v8_preserved_live_failure_count",
                        "cutoff": 0,
                        "split": "engineering_preflight",
                        "scope": "A1.2",
                        "value": len(vast_v8.get("preserved_live_failures", [])),
                        "n": 1,
                        "denominator": "preserved_validation_complete_bundle_failure_history",
                        "source_uri": vast_v8.get("receipt_uri"),
                        "source_sha256": vast_v8.get("receipt_sha256"),
                    },
                    {
                        "name": "vast_v8_validation_lineage_complete",
                        "cutoff": 0,
                        "split": "engineering_preflight",
                        "scope": "A1.2",
                        "value": int(
                            vast_v8.get("active_correction", {}).get(
                                "validation_lineage_complete"
                            )
                            is True
                        ),
                        "n": 1,
                        "denominator": "frozen_bundle_historical_validator_lineage",
                        "source_uri": vast_v8.get("receipt_uri"),
                        "source_sha256": vast_v8.get("receipt_sha256"),
                    },
                ]
            )
        vast_v9 = scaffold.get("vast_preflight_v9", {})
        if isinstance(vast_v9, Mapping) and vast_v9.get("validated") is True:
            rows.extend(
                [
                    {
                        "name": "vast_v9_required_lifecycle_control_count",
                        "cutoff": 0,
                        "split": "engineering_preflight",
                        "scope": "A1.2",
                        "value": len(
                            vast_v9.get("active_correction", {}).get(
                                "required_lifecycle_controls", []
                            )
                        ),
                        "n": 1,
                        "denominator": "hash_bound_execution_lifecycle_controls",
                        "source_uri": vast_v9.get("receipt_uri"),
                        "source_sha256": vast_v9.get("receipt_sha256"),
                    },
                    {
                        "name": "vast_v9_implementation_validation_complete",
                        "cutoff": 0,
                        "split": "engineering_preflight",
                        "scope": "A1.2",
                        "value": int(
                            vast_v9.get("active_correction", {}).get(
                                "implementation_validation_complete"
                            )
                            is True
                        ),
                        "n": 1,
                        "denominator": "additive_v9_runtime_and_orchestration_revision",
                        "source_uri": vast_v9.get("receipt_uri"),
                        "source_sha256": vast_v9.get("receipt_sha256"),
                    },
                ]
            )
            live_result = (
                vast_v9.get("live_result", {})
                if isinstance(vast_v9.get("live_result"), Mapping)
                else {}
            )
            if vast_v9.get("live_result_status") == "PASS":
                rows.extend(
                    [
                        {
                            "name": "vast_v9_live_arm_pass_count",
                            "cutoff": 0,
                            "split": "engineering_preflight",
                            "scope": "A1.2",
                            "value": len(
                                [
                                    item
                                    for item in live_result.get("arms", [])
                                    if isinstance(item, Mapping)
                                    and item.get("status") == "PASS"
                                ]
                            ),
                            "n": 4,
                            "denominator": "four_synthetic_gpu_worker_arm_receipts",
                            "source_uri": vast_v9.get("live_result_uri"),
                            "source_sha256": vast_v9.get("live_result_sha256"),
                        },
                        {
                            "name": "vast_v9_qwen_measured_adapter_max_input_tokens",
                            "cutoff": 32768,
                            "split": "engineering_preflight",
                            "scope": "A1.2",
                            "value": live_result.get("qwen", {}).get(
                                "measured_adapter_max_input_tokens"
                            ),
                            "n": 3,
                            "denominator": "synthetic_sentence_transformer_adapter_candidates",
                            "source_uri": vast_v9.get("live_result_uri"),
                            "source_sha256": vast_v9.get("live_result_sha256"),
                        },
                        {
                            "name": "vast_v9_checkpoint_resume_pass",
                            "cutoff": 0,
                            "split": "engineering_preflight",
                            "scope": "A1.2",
                            "value": int(
                                live_result.get("lifecycle", {}).get(
                                    "checkpoint_resume"
                                )
                                == "PASS"
                            ),
                            "n": 1,
                            "denominator": "synthetic_worker_checkpoint_resume_receipt",
                            "source_uri": vast_v9.get("live_result_uri"),
                            "source_sha256": vast_v9.get("live_result_sha256"),
                        },
                    ]
                )
        request_v11 = scaffold.get("scientific_execution_request_v11", {})
        if isinstance(request_v11, Mapping) and request_v11.get("validated") is True:
            metric_specs = (
                (
                    "v11_workload_manifest_count",
                    request_v11.get("workload_manifests"),
                    5,
                    "frozen_five_arm_request_manifests",
                ),
                (
                    "v11_expected_program_arm_runs",
                    request_v11.get("expected_program_arm_runs"),
                    25,
                    "planned_logical_program_arm_results_not_measured_runs",
                ),
                (
                    "v11_expected_physical_program_view_paths",
                    request_v11.get("expected_physical_program_view_paths"),
                    35,
                    "planned_physical_program_view_paths_not_measured_runs",
                ),
                (
                    "v11_rep_dev_query_count",
                    request_v11.get("rep_dev_query_count"),
                    150,
                    "protected_rep_dev_count_commitment",
                ),
                (
                    "v11_harness_dev_reserved_count",
                    request_v11.get("harness_dev_reserved_count"),
                    100,
                    "protected_harness_dev_reservation_count",
                ),
                (
                    "v11_pending_adoption_requirement_count",
                    len(request_v11.get("pending_adoption_requirements", [])),
                    1,
                    "fail_closed_owner_adoption_requirements",
                ),
            )
            rows.extend(
                {
                    "name": name,
                    "cutoff": 0,
                    "split": "request_preparation",
                    "scope": "A1.2",
                    "value": value,
                    "n": n,
                    "denominator": denominator,
                    "source_uri": request_v11.get("receipt_uri"),
                    "source_sha256": request_v11.get("receipt_sha256"),
                }
                for name, value, n, denominator in metric_specs
            )
            for key, value in request_v11.get("budget_hard_stops", {}).items():
                rows.append(
                    {
                        "name": f"v11_{key}",
                        "cutoff": 0,
                        "split": "request_preparation",
                        "scope": "A1.2",
                        "value": value,
                        "n": 1,
                        "denominator": "hard_stop_not_spend_authorization",
                        "source_uri": request_v11.get("receipt_uri"),
                        "source_sha256": request_v11.get("receipt_sha256"),
                    }
                )
        adoption = scaffold.get("adoption_inputs_v12_r3", {})
        if isinstance(adoption, Mapping) and adoption.get("validated") is True:
            publication = adoption.get("publication_impact", {})
            disposition = adoption.get("instance_disposition", {})
            rows.extend(
                (
                    {
                        "name": "v12_r3_pending_live_provider_input_count",
                        "cutoff": 0,
                        "split": "adoption_input_preparation",
                        "scope": "A1.2",
                        "value": len(adoption.get("pending_live_provider", [])),
                        "n": 1,
                        "denominator": "fresh_identity_quote_budget_and_admission_receipt_required",
                        "source_uri": adoption.get("contract_uri"),
                        "source_sha256": adoption.get("contract_sha256"),
                    },
                    {
                        "name": "v13_out_recall_at_100_primary_metric_binding",
                        "cutoff": 100,
                        "split": "publication_preregistration",
                        "scope": "A1.2",
                        "value": int(
                            isinstance(publication, Mapping)
                            and publication.get("primary_outcome")
                            == "out_recall_at_100"
                        ),
                        "n": 1,
                        "denominator": "candidate_exposure_primary_development_outcome_not_measured_result",
                        "source_uri": publication.get("contract_uri")
                        if isinstance(publication, Mapping)
                        else None,
                        "source_sha256": publication.get("contract_sha256")
                        if isinstance(publication, Mapping)
                        else None,
                    },
                    {
                        "name": "v13_current_live_instance_present",
                        "cutoff": 0,
                        "split": "instance_disposition_policy",
                        "scope": "A1.2",
                        "value": int(
                            isinstance(disposition, Mapping)
                            and disposition.get("current_disposition")
                            != "NO_LIVE_INSTANCE"
                        ),
                        "n": 1,
                        "denominator": "current_provider_instance_not_reuse_eligibility",
                        "source_uri": disposition.get("policy_uri")
                        if isinstance(disposition, Mapping)
                        else None,
                        "source_sha256": disposition.get("policy_sha256")
                        if isinstance(disposition, Mapping)
                        else None,
                    },
                )
            )
        return rows
    if phase_id == "A0_MIGRATION_FOUNDATION" and task_id in {None, "A0.8"}:
        feasibility = model.get("armindex", {}).get("compute_storage_feasibility", {})
        if (
            not isinstance(feasibility, Mapping)
            or feasibility.get("validated") is not True
        ):
            return []
        profiles = feasibility.get("profiles", [])
        observations = feasibility.get("observations", [])
        if (
            not isinstance(profiles, list)
            or not profiles
            or not isinstance(observations, list)
        ):
            return []
        profile = profiles[-1]
        observation = observations[-1]
        if not isinstance(profile, Mapping) or not isinstance(observation, Mapping):
            return []
        repetitions = int(observation.get("repetitions", 0))
        denominator = (
            f"host_observed_synthetic_scale_{profile.get('scale_factor')}_"
            f"documents_{profile.get('synthetic_document_count')}"
        )
        rows = []
        for operation in ("compile", "index_build", "search_workload"):
            latency = observation.get("latency_ms", {}).get(operation, {})
            rows.append(
                {
                    "name": f"fixture_{operation}_latency_p50_ms",
                    "cutoff": profile.get("scale_factor"),
                    "split": "synthetic",
                    "scope": "A0.8",
                    "value": latency.get("p50"),
                    "n": repetitions,
                    "denominator": denominator,
                    "source_uri": feasibility.get("fixture_receipt_uri"),
                    "source_sha256": feasibility.get("fixture_receipt_sha256"),
                }
            )
        rows.extend(
            (
                {
                    "name": "fixture_search_throughput_qps",
                    "cutoff": profile.get("scale_factor"),
                    "split": "synthetic",
                    "scope": "A0.8",
                    "value": observation.get("search_throughput_qps"),
                    "n": observation.get("search_calls"),
                    "denominator": denominator,
                    "source_uri": feasibility.get("fixture_receipt_uri"),
                    "source_sha256": feasibility.get("fixture_receipt_sha256"),
                },
                {
                    "name": "fixture_peak_python_allocation_bytes",
                    "cutoff": profile.get("scale_factor"),
                    "split": "synthetic",
                    "scope": "A0.8",
                    "value": observation.get("peak_python_allocation_bytes"),
                    "n": repetitions,
                    "denominator": denominator,
                    "source_uri": feasibility.get("fixture_receipt_uri"),
                    "source_sha256": feasibility.get("fixture_receipt_sha256"),
                },
                {
                    "name": "fixture_portable_sparse_payload_bytes",
                    "cutoff": profile.get("scale_factor"),
                    "split": "synthetic",
                    "scope": "A0.8",
                    "value": profile.get("portable_sparse_payload_bytes"),
                    "n": profile.get("compiled_unit_count"),
                    "denominator": denominator,
                    "source_uri": feasibility.get("fixture_manifest_uri"),
                    "source_sha256": feasibility.get("fixture_manifest_sha256"),
                },
            )
        )
        return rows
    if phase_id != "P1_CPU_BASELINE":
        return []
    selected = []
    for metric in model.get("metrics", []):
        if not isinstance(metric, Mapping):
            continue
        arm = str(metric.get("arm", ""))
        if task_id == "P1.1" and arm != "R0":
            continue
        if task_id == "P1.2" and arm != "R0-W":
            continue
        selected.append(dict(metric))
    return selected


def _bindings(
    root: Path,
    model: Mapping[str, Any],
    phase_id: str,
    task_id: str | None = None,
) -> dict[str, Any]:
    bindings: dict[str, Any] = {
        "source_of_truth": {
            "uri": "control/source-of-truth.yaml",
            "sha256": _hash_file(root, "control/source-of-truth.yaml"),
        },
        "campaign": {
            "uri": "control/campaigns/scope-autoindex-v1.yaml",
            "sha256": _hash_file(root, "control/campaigns/scope-autoindex-v1.yaml"),
        },
        "git_commit": model.get("source_commit"),
    }
    if phase_id == "A2_PER_ARM_AUTOINDEX":
        freeze = model.get("armindex", {}).get("a2_candidate_freeze", {})
        if isinstance(freeze, Mapping) and freeze.get("validated") is True:
            bindings["candidate_freeze"] = {
                "generation_attempt_id": freeze.get("generation_attempt_id"),
                "manifest_uri": freeze.get("manifest_uri"),
                "manifest_sha256": freeze.get("manifest_sha256"),
                "freeze_receipt_uri": freeze.get("freeze_receipt_uri"),
                "freeze_receipt_sha256": freeze.get("freeze_receipt_sha256"),
                "lock_uri": freeze.get("lock_uri"),
                "lock_sha256": freeze.get("lock_sha256"),
            }
            bindings["official_identity"] = dict(freeze.get("official_identity", {}))
            bindings["official_credit_closeout"] = dict(
                freeze.get("official_credit", {})
            )
            bindings["independent_audit"] = {
                "status": freeze.get("independent_audit_status"),
                "uri": freeze.get("independent_audit_receipt_uri"),
                "sha256": freeze.get("independent_audit_receipt_sha256"),
            }
            bindings["control_bindings"] = list(
                freeze.get("control_bindings", [])
            )
            bindings["publication_workspace"] = {
                "uri": "../03_Paper/01_ArmIndex",
                "authority": "projection_only",
            }
        readiness = model.get("armindex", {}).get("a2_execution_readiness", {})
        if isinstance(readiness, Mapping) and readiness.get("validated") is True:
            bindings["execution_readiness"] = {
                "status": readiness.get("status"),
                "contract_uri": readiness.get("contract_uri"),
                "contract_sha256": readiness.get("contract_sha256"),
                "budget_uri": readiness.get("budget_uri"),
                "budget_profile_sha256": readiness.get("budget_profile_sha256"),
                "forward_hard_stop_usd": readiness.get("forward_hard_stop_usd"),
                "owner_ttl_hours": readiness.get("owner_ttl_hours"),
                "measured_a2_started": readiness.get("measured_a2_started"),
            }
            if readiness.get("attempt_id"):
                bindings["current_staged_attempt"] = {
                    "attempt_id": readiness.get("attempt_id"),
                    "pointer_uri": readiness.get("current_execution_pointer_uri"),
                    "pointer_sha256": readiness.get(
                        "current_execution_pointer_sha256"
                    ),
                }
    elif phase_id == "P1_CPU_BASELINE":
        bindings["execution_envelope"] = {
            "uri": "control/execution-envelope.yaml",
            "sha256": _hash_file(root, "control/execution-envelope.yaml"),
        }
        bindings["request_id"] = "dapfam-p1-fulltext-c058a3aa7357c782"
        bindings["protected_payloads"] = (
            "owner-local; aggregate hashes only in this report"
        )
    elif phase_id == "P2_SCOPE_DEVELOPMENT":
        p2 = (
            model.get("p2_readiness", {})
            if isinstance(model.get("p2_readiness"), Mapping)
            else {}
        )
        official_review = (
            p2.get("official_review", {})
            if isinstance(p2.get("official_review"), Mapping)
            else {}
        )
        review_source = (
            official_review.get("source", {})
            if isinstance(official_review.get("source"), Mapping)
            else {}
        )
        fixture = (
            p2.get("fixture_pilot", {})
            if isinstance(p2.get("fixture_pilot"), Mapping)
            else {}
        )
        observatory = (
            model.get("observatory", {})
            if isinstance(model.get("observatory"), Mapping)
            else {}
        )
        source = p2.get("source", {}) if isinstance(p2.get("source"), Mapping) else {}
        profile_uri = str(source.get("profile", ""))
        envelope_uri = str(source.get("execution_envelope", ""))
        revision_uri = str(source.get("campaign_revision", ""))
        bindings["budget_profile"] = {
            "uri": profile_uri,
            "sha256": p2.get("budget_profile_sha256"),
        }
        bindings["execution_envelope"] = {
            "uri": envelope_uri,
            "sha256": _hash_file(root, envelope_uri),
        }
        bindings["campaign_revision_record"] = {
            "uri": revision_uri,
            "sha256": _hash_file(root, revision_uri),
        }
        bindings["campaign_revision"] = p2.get("campaign_revision")
        bindings["static_review"] = {
            "uri": "orchestration/audits/p2-readiness/index.json",
            "sha256": review_source.get("index_sha256"),
        }
        bindings["fixture_receipt"] = {
            "uri": fixture.get("receipt_uri"),
            "sha256": fixture.get("receipt_sha256"),
        }
        bindings["fixture_manifest"] = {
            "uri": fixture.get("execution_manifest_uri"),
            "sha256": fixture.get("execution_manifest_sha256"),
        }
        bindings["observatory_registry"] = {
            "uri": "outputs/observatory/fixture-v1/registry.json",
            "sha256": observatory.get("registry_sha256"),
        }
        bindings["observatory_receipt"] = {
            "uri": "outputs/observatory/fixture-v1/receipt.json",
            "sha256": observatory.get("receipt_sha256"),
        }
        preflight = (
            p2.get("preflight", {}) if isinstance(p2.get("preflight"), Mapping) else {}
        )
        bindings["preflight_receipt"] = {
            "uri": preflight.get("receipt_uri"),
            "sha256": preflight.get("receipt_sha256"),
        }
        proposal = (
            p2.get("candidate_proposal", {})
            if isinstance(p2.get("candidate_proposal"), Mapping)
            else {}
        )
        bindings["candidate_freeze_proposal"] = {
            "uri": proposal.get("proposal_uri"),
            "sha256": proposal.get("proposal_sha256"),
        }
    elif phase_id.startswith("A"):
        scaffold = model.get("armindex", {}).get("a1_2_contract_scaffold", {})
        bindings["campaign"] = {
            "uri": "control/campaigns/armindex-multiretriever-v2.yaml",
            "sha256": _hash_file(
                root, "control/campaigns/armindex-multiretriever-v2.yaml"
            ),
        }
        bindings["migration_budget"] = {
            "uri": "control/budgets/armindex-migration-v2.yaml",
            "sha256": _hash_file(root, "control/budgets/armindex-migration-v2.yaml"),
        }
        bindings["armindex_schema_root"] = {
            "uri": "schemas/armindex",
            "sha256": _hash_file(root, "schemas/armindex/read-model.v1.json"),
        }
        bindings["historical_scope"] = {
            "uri": "control/campaigns/scope-autoindex-v1.yaml",
            "sha256": _hash_file(root, "control/campaigns/scope-autoindex-v1.yaml"),
            "status": "historical_read_only",
        }
        harvest = model.get("armindex", {}).get("legacy_code_harvest", {})
        if task_id == "A0.10" and isinstance(harvest, Mapping):
            bindings["legacy_code_harvest_ledger"] = {
                "uri": harvest.get("ledger_uri"),
                "sha256": harvest.get("ledger_sha256"),
            }
            bindings["legacy_code_harvest_receipt"] = {
                "uri": harvest.get("receipt_uri"),
                "sha256": harvest.get("receipt_sha256"),
            }
            bindings["synthetic_vertical_slice_receipt"] = {
                "uri": harvest.get("fixture_receipt_uri"),
                "sha256": harvest.get("fixture_receipt_sha256"),
            }
            bindings["repository_hygiene_audit"] = {
                "uri": harvest.get("repository_hygiene_audit_uri"),
                "sha256": harvest.get("repository_hygiene_audit_sha256"),
            }
            bindings["output_root_relocation_receipt"] = {
                "uri": harvest.get("output_root_relocation_receipt_uri"),
                "sha256": harvest.get("output_root_relocation_receipt_sha256"),
            }
            bindings["source_verification_receipt"] = {
                "uri": harvest.get("source_verification_receipt_uri"),
                "sha256": harvest.get("source_verification_receipt_sha256"),
            }
        feasibility = model.get("armindex", {}).get("compute_storage_feasibility", {})
        if task_id == "A0.8" and isinstance(feasibility, Mapping):
            bindings["compute_storage_task_receipt"] = {
                "uri": feasibility.get("task_receipt_uri"),
                "sha256": feasibility.get("task_receipt_sha256"),
            }
            bindings["compute_storage_fixture_manifest"] = {
                "uri": feasibility.get("fixture_manifest_uri"),
                "sha256": feasibility.get("fixture_manifest_sha256"),
            }
            bindings["compute_storage_fixture_receipt"] = {
                "uri": feasibility.get("fixture_receipt_uri"),
                "sha256": feasibility.get("fixture_receipt_sha256"),
            }
        closeout = model.get("armindex", {}).get("phase_closeout", {})
        if task_id == "A0.9" and isinstance(closeout, Mapping):
            bindings["a0_phase_closeout_receipt"] = {
                "uri": closeout.get("receipt_uri"),
                "sha256": closeout.get("receipt_sha256"),
            }
            bindings["a0_validation_audit"] = {
                "uri": closeout.get("validation_audit_uri"),
                "sha256": closeout.get("validation_audit_sha256"),
            }
        adapter = model.get("armindex", {}).get("adapter_fixture_validation", {})
        if phase_id == "A1_BASELINES_AND_MULTI_ARM_SCREENING" and isinstance(
            adapter, Mapping
        ):
            bindings["a11_task_receipt"] = {
                "uri": adapter.get("task_receipt_uri"),
                "sha256": adapter.get("task_receipt_sha256"),
            }
            bindings["a11_fixture_manifest"] = {
                "uri": adapter.get("fixture_manifest_uri"),
                "sha256": adapter.get("fixture_manifest_sha256"),
            }
            bindings["a11_fixture_receipt"] = {
                "uri": adapter.get("fixture_receipt_uri"),
                "sha256": adapter.get("fixture_receipt_sha256"),
            }
            bindings["a12_gpu_proposal"] = {
                "uri": adapter.get("gpu_proposal_uri"),
                "sha256": adapter.get("gpu_proposal_sha256"),
                "status": adapter.get("gpu_proposal_status"),
            }
            if isinstance(scaffold, Mapping) and scaffold.get("validated") is True:
                bindings["a12_execution_contract"] = {
                    "uri": scaffold.get("execution_contract_uri"),
                    "sha256": scaffold.get("execution_contract_sha256"),
                    "status": scaffold.get("status"),
                }
                bindings["a12_budget_profile"] = {
                    "uri": scaffold.get("budget_profile_uri"),
                    "sha256": scaffold.get("budget_profile_sha256"),
                }
                bindings["a12_model_lockset"] = {
                    "uri": scaffold.get("model_lockset_uri"),
                    "sha256": scaffold.get("model_lockset_sha256"),
                }
                bindings["a12_launch_checklist"] = {
                    "uri": scaffold.get("launch_checklist_uri"),
                    "sha256": scaffold.get("launch_checklist_sha256"),
                    "launch_ready": scaffold.get("launch_ready"),
                }
                bindings["a12_shutdown_plan"] = {
                    "uri": scaffold.get("shutdown_plan_uri"),
                    "sha256": scaffold.get("shutdown_plan_sha256"),
                }
                bindings["a12_closeout_validation_audit"] = {
                    "uri": scaffold.get("closeout_validation_audit_uri"),
                    "sha256": scaffold.get("closeout_validation_audit_sha256"),
                    "check_count": scaffold.get("closeout_validation_check_count"),
                    "recovery_count": scaffold.get(
                        "closeout_validation_recovery_count"
                    ),
                }
                bindings["a12_owner_local_preflight"] = {
                    "uri": scaffold.get("preflight_uri"),
                    "sha256": scaffold.get("preflight_sha256"),
                    "status": scaffold.get("preflight_status"),
                    "blocker_count": len(scaffold.get("preflight_blockers", []))
                    if isinstance(scaffold.get("preflight_blockers"), list)
                    else 0,
                }
                bindings["a12_owner_local_mlflow_registration"] = {
                    "uri": scaffold.get("preflight_mlflow_registration_uri"),
                    "sha256": scaffold.get("preflight_mlflow_registration_sha256"),
                }
                vast = scaffold.get("vast_preflight_v2", {})
                if isinstance(vast, Mapping) and vast.get("validated") is True:
                    bindings["a12_vast_v2_receipt"] = {
                        "uri": vast.get("receipt_uri"),
                        "sha256": vast.get("receipt_sha256"),
                        "status": vast.get("status"),
                    }
                    bindings["a12_vast_v2_budget"] = {
                        "uri": vast.get("budget_uri"),
                        "sha256": vast.get("budget_sha256"),
                    }
                    bindings["a12_vast_v2_topology"] = {
                        "uri": vast.get("topology_uri"),
                        "sha256": vast.get("topology_sha256"),
                    }
                    bindings["a12_vast_v2_closeout_validation"] = {
                        "uri": vast.get("closeout_validation_audit_uri"),
                        "sha256": vast.get("closeout_validation_audit_sha256"),
                        "check_count": vast.get("closeout_validation_check_count"),
                    }
                vast_v3 = scaffold.get("vast_preflight_v3", {})
                if isinstance(vast_v3, Mapping) and vast_v3.get("validated") is True:
                    bindings["a12_vast_v3_correction_receipt"] = {
                        "uri": vast_v3.get("receipt_uri"),
                        "sha256": vast_v3.get("receipt_sha256"),
                        "self_sha256": vast_v3.get("receipt_self_sha256"),
                        "status": vast_v3.get("status"),
                    }
                    bindings["a12_vast_v3_execution_contract"] = {
                        "uri": vast_v3.get("contract_uri"),
                        "sha256": vast_v3.get("contract_sha256"),
                        "self_sha256": vast_v3.get("contract_self_sha256"),
                    }
                vast_v5 = scaffold.get("vast_preflight_v5", {})
                if isinstance(vast_v5, Mapping) and vast_v5.get("validated") is True:
                    bindings["a12_direct_base_v5_receipt"] = {
                        "uri": vast_v5.get("receipt_uri"),
                        "sha256": vast_v5.get("receipt_sha256"),
                        "status": vast_v5.get("status"),
                    }
                    bindings["a12_direct_base_v5_execution_contract"] = {
                        "uri": vast_v5.get("contract_uri"),
                        "sha256": vast_v5.get("contract_sha256"),
                        "image_reference": vast_v5.get("image_reference"),
                        "resolved_manifest_digest": vast_v5.get(
                            "resolved_manifest_digest"
                        ),
                        "platform": vast_v5.get("platform"),
                    }
    r13_failure = model.get("armindex", {}).get("a1_2_r13_failure", {})
    if (
        phase_id == "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        and task_id in {None, "A1.2"}
        and isinstance(r13_failure, Mapping)
        and r13_failure.get("validated") is True
    ):
        attempt = r13_failure.get("attempt", {})
        bindings["a12_v16_r13_failed_closed_attempt"] = {
            "uri": r13_failure.get("audit_uri"),
            "sha256": r13_failure.get("audit_file_sha256"),
            "audit_sha256": r13_failure.get("audit_sha256"),
            "status": r13_failure.get("status"),
            "completed_logical_cells": attempt.get("completed_logical_cells")
            if isinstance(attempt, Mapping)
            else None,
            "required_logical_cells": attempt.get("required_logical_cells")
            if isinstance(attempt, Mapping)
            else None,
            "partial_results_promotable": attempt.get("partial_results_promotable")
            if isinstance(attempt, Mapping)
            else None,
        }
    current_attempt = model.get("armindex", {}).get("a1_2_current_attempt", {})
    if (
        phase_id == "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        and task_id in {None, "A1.2"}
        and isinstance(current_attempt, Mapping)
        and current_attempt.get("validated") is True
    ):
        bindings["a12_v16_current_terminal_attempt"] = {
            "pointer_uri": current_attempt.get("pointer_uri"),
            "pointer_sha256": current_attempt.get("pointer_file_sha256"),
            "receipt_uri": current_attempt.get("receipt_uri"),
            "receipt_sha256": current_attempt.get("receipt_file_sha256"),
            "attempt_id": current_attempt.get("attempt_id"),
            "status": current_attempt.get("status"),
            "provider_disposition_status": current_attempt.get(
                "provider_disposition_status"
            ),
            "completed_logical_cells": current_attempt.get("coverage", {}).get(
                "completed_logical_cells"
            )
            if isinstance(current_attempt.get("coverage"), Mapping)
            else None,
            "measured_result_summary_uri": current_attempt.get(
                "measured_result_summary", {}
            ).get("summary_uri")
            if isinstance(current_attempt.get("measured_result_summary"), Mapping)
            else None,
            "measured_result_summary_sha256": current_attempt.get(
                "measured_result_summary", {}
            ).get("summary_file_sha256")
            if isinstance(current_attempt.get("measured_result_summary"), Mapping)
            else None,
            "promoted_arm_ids": current_attempt.get(
                "measured_result_summary", {}
            ).get("promoted_arm_ids")
            if isinstance(current_attempt.get("measured_result_summary"), Mapping)
            else None,
            "cell_eda_package_uri": current_attempt.get(
                "cell_eda_package", {}
            ).get("package_uri")
            if isinstance(current_attempt.get("cell_eda_package"), Mapping)
            else None,
            "cell_eda_package_sha256": current_attempt.get(
                "cell_eda_package", {}
            ).get("package_file_sha256")
            if isinstance(current_attempt.get("cell_eda_package"), Mapping)
            else None,
        }
    return bindings


def _record_for(
    root: Path,
    model: Mapping[str, Any],
    *,
    phase: Mapping[str, Any],
    task: Mapping[str, Any] | None,
) -> dict[str, Any]:
    phase_id = str(phase.get("phase_id", ""))
    task_id = str(task.get("task_id")) if task else None
    report_type = "task" if task else "phase"
    report_id = (
        (f"task-{task_id.lower().replace('.', '-')}")
        if task_id
        else f"phase-{phase_id.lower()}"
    )
    status = _lifecycle(task.get("status") if task else phase.get("status"))
    adapter = model.get("armindex", {}).get("adapter_fixture_validation", {})
    scaffold = model.get("armindex", {}).get("a1_2_contract_scaffold", {})
    current_attempt = model.get("armindex", {}).get("a1_2_current_attempt", {})
    a2_freeze = model.get("armindex", {}).get("a2_candidate_freeze", {})
    a2_readiness = model.get("armindex", {}).get("a2_execution_readiness", {})
    a2_freeze_valid = (
        phase_id == "A2_PER_ARM_AUTOINDEX"
        and task_id
        in {None, "OFFICIAL_CODEX_BRIDGE_AND_CANDIDATE_FREEZE", "A2.1"}
        and isinstance(a2_freeze, Mapping)
        and a2_freeze.get("validated") is True
    )
    a2_readiness_valid = (
        phase_id == "A2_PER_ARM_AUTOINDEX"
        and task_id in {None, "A2.1"}
        and isinstance(a2_readiness, Mapping)
        and a2_readiness.get("validated") is True
    )
    a2_provider_admission_failed_closed = (
        a2_readiness_valid
        and a2_readiness.get("status")
        == "PROVIDER_ADMISSION_FAILED_CLOSED_MEASUREMENT_LOCKED"
    )
    current_terminal = (
        phase_id == "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        and task_id in {None, "A1.2"}
        and isinstance(current_attempt, Mapping)
        and current_attempt.get("validated") is True
    )
    current_failed_closed = current_terminal and current_attempt.get("status") == "FAILED_CLOSED"
    current_pass = current_terminal and current_attempt.get("status") == "PASS"
    scientific = phase_id == "P1_CPU_BASELINE" or current_pass
    a11_validated = (
        phase_id == "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        and isinstance(adapter, Mapping)
        and adapter.get("validated") is True
    )
    a12_validated = (
        phase_id == "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        and isinstance(scaffold, Mapping)
        and scaffold.get("validated") is True
    )
    evidence_class = (
        str(current_attempt.get("evidence_class"))
        if current_terminal
        else str(a2_readiness.get("evidence_class"))
        if a2_readiness_valid
        else str(a2_freeze.get("evidence_class"))
        if a2_freeze_valid
        else "train_selection_measured"
        if scientific
        else "fixture"
        if phase_id == "P2_SCOPE_DEVELOPMENT"
        and model.get("p2_readiness", {}).get("fixture_pilot", {}).get("status")
        == "passed"
        else str(scaffold.get("evidence_class", "engineering_preflight_scaffold"))
        if a12_validated and task_id in {None, "A1.2"}
        else "engineering_fixture"
        if a11_validated and task_id in {None, "A1.1"}
        else "planning_estimate"
        if a11_validated and task_id == "A1.2"
        else "engineering"
        if phase_id == "P0_FOUNDATION" or phase_id.startswith("A")
        else "planned"
    )
    claim_boundary = (
        str(current_attempt.get("claim_boundary"))
        if current_terminal
        else str(a2_readiness.get("claim_boundary"))
        if a2_readiness_valid
        else str(a2_freeze.get("claim_boundary"))
        if a2_freeze_valid
        else "train_selection_only"
        if scientific
        else str(scaffold.get("claim_boundary"))
        if a12_validated and task_id in {None, "A1.2"}
        else str(adapter.get("claim_boundary"))
        if a11_validated and task_id in {None, "A1.1"}
        else "resource_planning_only_no_gpu_launch_or_measured_authority"
        if a11_validated and task_id == "A1.2"
        else "engineering_provenance_only"
        if phase_id in {"P0_FOUNDATION", "P2_SCOPE_DEVELOPMENT"}
        or phase_id.startswith("A")
        else "unavailable"
    )
    objective = (
        str(task.get("title"))
        if task
        else f"Deliver the {phase_id} research phase with an auditable evidence boundary."
    )
    if phase_id == "P2_SCOPE_DEVELOPMENT":
        objective = "Prepare and validate the deterministic R1 SCOPE/AutoIndex lifecycle without starting measured P2."
    elif phase_id.startswith("A"):
        objective = (
            str(task.get("title"))
            if task
            else str(
                phase.get("purpose", f"Deliver {phase_id} under the ArmIndex contract.")
            )
        )
    metrics = _metrics(model, phase_id, task_id)
    artifacts = _artifacts(root, model, phase_id, task_id)
    p2 = (
        model.get("p2_readiness", {})
        if isinstance(model.get("p2_readiness"), Mapping)
        else {}
    )
    failures = []
    if phase_id == "A0_MIGRATION_FOUNDATION" and task_id in {None, "A0.10"}:
        revise_sha256 = _hash_file(root, A010_RIGOR_REVISE_AUDIT)
        accept_sha256 = _hash_file(root, A010_RIGOR_ACCEPT_AUDIT)
        if revise_sha256 and accept_sha256:
            failures.append(
                {
                    "failure_id": "a0.10-legacy-code-harvest-independent-revise-20260804",
                    "failure_uri": A010_RIGOR_REVISE_AUDIT,
                    "failure_sha256": revise_sha256,
                    "recovery_id": "a0.10-legacy-code-harvest-independent-accept-20260804",
                    "recovery_uri": A010_RIGOR_ACCEPT_AUDIT,
                    "recovery_sha256": accept_sha256,
                    "status": "repaired_and_validated",
                    "counters_changed": False,
                }
            )
    if current_failed_closed:
        coverage = current_attempt.get("coverage", {})
        failures.append(
            {
                "failure_id": f"a1.2-v16-{current_attempt.get('attempt_id')}-failed-closed",
                "failure_uri": current_attempt.get("receipt_uri"),
                "failure_sha256": current_attempt.get("receipt_file_sha256"),
                "recovery_id": current_attempt.get("next_authorized_action"),
                "recovery_uri": current_attempt.get("receipt_uri"),
                "recovery_sha256": current_attempt.get("receipt_file_sha256"),
                "status": "FAILED_CLOSED_RETRY_REQUIRED",
                "counters_changed": False,
                "completed_logical_cells": coverage.get("completed_logical_cells")
                if isinstance(coverage, Mapping)
                else None,
                "required_logical_cells": coverage.get("required_logical_cells")
                if isinstance(coverage, Mapping)
                else None,
                "partial_results_promotable": coverage.get("partial_results_promotable")
                if isinstance(coverage, Mapping)
                else None,
            }
        )
    if phase_id == "A1_BASELINES_AND_MULTI_ARM_SCREENING" and task_id in {None, "A1.2"}:
        vast_v7 = scaffold.get("vast_preflight_v7", {})
        vast_v8 = scaffold.get("vast_preflight_v8", {})
        live_failures = (
            vast_v8.get("preserved_live_failures", [])
            if isinstance(vast_v8, Mapping)
            and vast_v8.get("validated") is True
            and isinstance(vast_v8.get("preserved_live_failures"), list)
            else vast_v7.get("preserved_live_failures", [])
            if isinstance(vast_v7, Mapping)
            and isinstance(vast_v7.get("preserved_live_failures"), list)
            else []
        )
        failure_source = (
            vast_v8
            if isinstance(vast_v8, Mapping) and vast_v8.get("validated") is True
            else vast_v7
        )
        for item in live_failures:
            if isinstance(item, Mapping):
                failures.append(
                    {
                        "failure_id": item.get("failure_id"),
                        "failure_uri": failure_source.get("receipt_uri"),
                        "failure_sha256": failure_source.get("receipt_sha256"),
                        "recovery_id": item.get("disposition"),
                        "recovery_uri": failure_source.get("receipt_uri"),
                        "recovery_sha256": failure_source.get("receipt_sha256"),
                        "status": "preserved_and_repaired_preflight_pending",
                        "counters_changed": False,
                    }
                )
    if (
        phase_id == "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        and task_id in {None, "A1.2"}
        and isinstance(scaffold, Mapping)
        and scaffold.get("closeout_validation_audit_sha256")
    ):
        audit_uri = scaffold.get("closeout_validation_audit_uri")
        audit_sha256 = scaffold.get("closeout_validation_audit_sha256")
        for item in scaffold.get("closeout_validation_recoveries", []):
            if isinstance(item, Mapping):
                failures.append(
                    {
                        "failure_id": item.get("failure_id"),
                        "failure_uri": audit_uri,
                        "failure_sha256": audit_sha256,
                        "recovery_id": item.get("recovery_id"),
                        "recovery_uri": audit_uri,
                        "recovery_sha256": audit_sha256,
                        "status": item.get("status"),
                        "counters_changed": False,
                    }
                )
        vast = scaffold.get("vast_preflight_v2", {})
        if isinstance(vast, Mapping) and vast.get("closeout_validation_audit_sha256"):
            audit_uri = vast.get("closeout_validation_audit_uri")
            audit_sha256 = vast.get("closeout_validation_audit_sha256")
            for item in vast.get("closeout_validation_recoveries", []):
                if isinstance(item, Mapping):
                    failures.append(
                        {
                            "failure_id": item.get("failure_id"),
                            "failure_uri": audit_uri,
                            "failure_sha256": audit_sha256,
                            "recovery_id": item.get("recovery_id"),
                            "recovery_uri": audit_uri,
                            "recovery_sha256": audit_sha256,
                            "status": item.get("status"),
                            "counters_changed": False,
                        }
                    )
        vast_v3 = scaffold.get("vast_preflight_v3", {})
        if isinstance(vast_v3, Mapping) and vast_v3.get("validated") is True:
            failures.append(
                {
                    "failure_id": "a1.2-v2-postcommit-head-tree-regeneration-defect-20260806",
                    "failure_uri": vast_v3.get("receipt_uri"),
                    "failure_sha256": vast_v3.get("receipt_sha256"),
                    "recovery_id": "a1.2-v3-receipt-bound-clean-commit-validator-20260806",
                    "recovery_uri": vast_v3.get("receipt_uri"),
                    "recovery_sha256": vast_v3.get("receipt_sha256"),
                    "status": "repaired_and_validated",
                    "counters_changed": False,
                }
            )
            projection_repair_sha256 = _hash_file(
                root, A12_V3_PROJECTION_STABILITY_REPAIR_AUDIT
            )
            if projection_repair_sha256:
                failures.append(
                    {
                        "failure_id": "a1.2-v3-runtime-git-identity-projection-drift-20260806",
                        "failure_uri": A12_V3_PROJECTION_STABILITY_REPAIR_AUDIT,
                        "failure_sha256": projection_repair_sha256,
                        "recovery_id": "a1.2-v3-runtime-git-identity-projection-exclusion-20260806",
                        "recovery_uri": A12_V3_PROJECTION_STABILITY_REPAIR_AUDIT,
                        "recovery_sha256": projection_repair_sha256,
                        "status": "repaired_and_validated",
                        "counters_changed": False,
                    }
                )
    if phase_id == "P2_SCOPE_DEVELOPMENT" and model.get("observatory", {}).get(
        "failed_child_count", 0
    ):
        failures.append(
            {
                "failure_id": "obs-failure-candidate-02",
                "recovery_id": "obs-recovery-candidate-02",
                "status": "retained_and_recovered",
                "counters_changed": False,
            }
        )
    if phase_id == "P2_SCOPE_DEVELOPMENT":
        initial_audit_sha256 = _hash_file(root, P2_PREFLIGHT_INITIAL_AUDIT)
        repair_audit_sha256 = _hash_file(root, P2_PREFLIGHT_REPAIR_AUDIT)
        if initial_audit_sha256 and repair_audit_sha256:
            failures.append(
                {
                    "failure_id": "p2-preflight-completion-audit-20260802",
                    "failure_uri": P2_PREFLIGHT_INITIAL_AUDIT,
                    "failure_sha256": initial_audit_sha256,
                    "recovery_id": "p2-preflight-completion-repair-20260802",
                    "recovery_uri": P2_PREFLIGHT_REPAIR_AUDIT,
                    "recovery_sha256": repair_audit_sha256,
                    "status": "repaired_and_validated",
                    "counters_changed": False,
                }
            )
        byte_initial_sha256 = _hash_file(root, P2_REPORT_BYTE_INITIAL_AUDIT)
        byte_repair_sha256 = _hash_file(root, P2_REPORT_BYTE_REPAIR_AUDIT)
        if byte_initial_sha256 and byte_repair_sha256:
            failures.append(
                {
                    "failure_id": "p2-preflight-report-byte-drift-audit-20260802",
                    "failure_uri": P2_REPORT_BYTE_INITIAL_AUDIT,
                    "failure_sha256": byte_initial_sha256,
                    "recovery_id": "p2-preflight-report-byte-drift-repair-20260802",
                    "recovery_uri": P2_REPORT_BYTE_REPAIR_AUDIT,
                    "recovery_sha256": byte_repair_sha256,
                    "status": "repaired_and_validated",
                    "counters_changed": False,
                }
            )
        source_initial_sha256 = _hash_file(root, P2_PROJECTION_SOURCE_INITIAL_AUDIT)
        source_repair_sha256 = _hash_file(root, P2_PROJECTION_SOURCE_REPAIR_AUDIT)
        if source_initial_sha256 and source_repair_sha256:
            failures.append(
                {
                    "failure_id": "p2-preflight-projection-source-hash-drift-audit-20260802",
                    "failure_uri": P2_PROJECTION_SOURCE_INITIAL_AUDIT,
                    "failure_sha256": source_initial_sha256,
                    "recovery_id": "p2-preflight-projection-source-hash-drift-repair-20260802",
                    "recovery_uri": P2_PROJECTION_SOURCE_REPAIR_AUDIT,
                    "recovery_sha256": source_repair_sha256,
                    "status": "repaired_and_validated",
                    "counters_changed": False,
                }
            )
        path_initial_sha256 = _hash_file(root, P2_TRACKED_OWNER_PATH_INITIAL_AUDIT)
        path_repair_sha256 = _hash_file(root, P2_TRACKED_OWNER_PATH_REPAIR_AUDIT)
        if path_initial_sha256 and path_repair_sha256:
            failures.append(
                {
                    "failure_id": "p2-preflight-tracked-owner-path-audit-20260802",
                    "failure_uri": P2_TRACKED_OWNER_PATH_INITIAL_AUDIT,
                    "failure_sha256": path_initial_sha256,
                    "recovery_id": "p2-preflight-tracked-owner-path-repair-20260802",
                    "recovery_uri": P2_TRACKED_OWNER_PATH_REPAIR_AUDIT,
                    "recovery_sha256": path_repair_sha256,
                    "status": "repaired_and_validated",
                    "counters_changed": False,
                }
            )
        runtime_initial_sha256 = _hash_file(root, P2_RUNTIME_INTERRUPTION_AUDIT)
        runtime_repair_sha256 = _hash_file(root, P2_RUNTIME_RECOVERY_AUDIT)
        if runtime_initial_sha256 and runtime_repair_sha256:
            failures.append(
                {
                    "failure_id": "p2-runtime-resilience-v1-interruption-20260803",
                    "failure_uri": P2_RUNTIME_INTERRUPTION_AUDIT,
                    "failure_sha256": runtime_initial_sha256,
                    "recovery_id": "p2-runtime-resilience-v2-recovery-20260803",
                    "recovery_uri": P2_RUNTIME_RECOVERY_AUDIT,
                    "recovery_sha256": runtime_repair_sha256,
                    "status": "repaired_and_validated",
                    "counters_changed": False,
                }
            )
        linux_ci_failure_sha256 = _hash_file(root, P2_RUNTIME_LINUX_CI_FAILURE_AUDIT)
        linux_ci_repair_sha256 = _hash_file(root, P2_RUNTIME_LINUX_CI_REPAIR_AUDIT)
        if linux_ci_failure_sha256 and linux_ci_repair_sha256:
            failures.append(
                {
                    "failure_id": "p2-runtime-resilience-v2-linux-ci-failure-20260803",
                    "failure_uri": P2_RUNTIME_LINUX_CI_FAILURE_AUDIT,
                    "failure_sha256": linux_ci_failure_sha256,
                    "recovery_id": "p2-runtime-resilience-v2-linux-ci-repair-20260803",
                    "recovery_uri": P2_RUNTIME_LINUX_CI_REPAIR_AUDIT,
                    "recovery_sha256": linux_ci_repair_sha256,
                    "status": "repaired_and_validated",
                    "counters_changed": False,
                }
            )
        clean_checkout_failure_sha256 = _hash_file(
            root, P2_RUNTIME_CLEAN_CHECKOUT_FAILURE_AUDIT
        )
        clean_checkout_repair_sha256 = _hash_file(
            root, P2_RUNTIME_CLEAN_CHECKOUT_REPAIR_AUDIT
        )
        if clean_checkout_failure_sha256 and clean_checkout_repair_sha256:
            failures.append(
                {
                    "failure_id": "p2-runtime-resilience-v2-clean-checkout-drift-20260803",
                    "failure_uri": P2_RUNTIME_CLEAN_CHECKOUT_FAILURE_AUDIT,
                    "failure_sha256": clean_checkout_failure_sha256,
                    "recovery_id": "p2-runtime-resilience-v2-clean-checkout-repair-20260803",
                    "recovery_uri": P2_RUNTIME_CLEAN_CHECKOUT_REPAIR_AUDIT,
                    "recovery_sha256": clean_checkout_repair_sha256,
                    "status": "repaired_and_validated",
                    "counters_changed": False,
                }
            )
        independent_revise_sha256 = _hash_file(
            root, P2_RUNTIME_INDEPENDENT_REVISE_AUDIT
        )
        independent_accept_sha256 = _hash_file(
            root, P2_RUNTIME_INDEPENDENT_ACCEPT_AUDIT
        )
        if independent_revise_sha256 and independent_accept_sha256:
            failures.append(
                {
                    "failure_id": "p2-runtime-resilience-v2-independent-verifier-revise-20260803",
                    "failure_uri": P2_RUNTIME_INDEPENDENT_REVISE_AUDIT,
                    "failure_sha256": independent_revise_sha256,
                    "recovery_id": "p2-runtime-resilience-v2-independent-verifier-accept-20260803",
                    "recovery_uri": P2_RUNTIME_INDEPENDENT_ACCEPT_AUDIT,
                    "recovery_sha256": independent_accept_sha256,
                    "status": "repaired_and_validated",
                    "counters_changed": False,
                }
            )
    if current_failed_closed:
        coverage = current_attempt.get("coverage", {})
        completed = (
            coverage.get("completed_logical_cells")
            if isinstance(coverage, Mapping)
            else "unknown"
        )
        required = (
            coverage.get("required_logical_cells")
            if isinstance(coverage, Mapping)
            else "unknown"
        )
        output = (
            "Aggregate-safe failed-attempt provenance records "
            f"{completed}/{required} completed logical cells before a hard stop."
        )
        result = (
            "FAILED_CLOSED and retry-required: the incomplete current attempt is "
            "not promotable, has no Owner-local evaluation, and leaves the official "
            "completed measured-run counter at zero."
        )
        interpretation = (
            "The partial cell receipts are failure provenance only. They do not "
            "constitute a common-screen result, deterministic promotion input, A1 "
            "closeout, or evidence for A2, Selection, Final, or publication."
        )
        decision_status = "FAILED_CLOSED_RETRY_REQUIRED"
    elif current_pass:
        result_summary = current_attempt.get("measured_result_summary", {})
        promoted = (
            result_summary.get("promoted_arm_ids", [])
            if isinstance(result_summary, Mapping)
            else []
        )
        output = "A hash-bound current terminal receipt and measured summary record complete 25/25 A1.2 coverage across all five arms."
        result = "PASS: safe return, Owner-local evaluation, deterministic promotion, and provider disposition are bound by aggregate-safe hashes."
        interpretation = f"The frozen rule promoted {', '.join(str(item) for item in promoted)}. This establishes only the A1.2 development result boundary and does not authorize A2, HARNESS-DEV, Selection, Final, D2, or D3."
        decision_status = "PASS_25_OF_25"
    elif scientific:
        output = "Four validated R0/R0-W train and selection manifests with aggregate Recall@100 metrics."
        result = "P1 measured train/selection evidence is complete within its declared development boundary."
        interpretation = "The metrics describe the fixed CPU protocol on train and selection; they do not establish final-split generalization or legal conclusions."
        decision_status = "completed"
    elif phase_id == "P2_SCOPE_DEVELOPMENT":
        preflight_status = str(p2.get("preflight_status", "not_started"))
        proposal = (
            p2.get("candidate_proposal", {})
            if isinstance(p2.get("candidate_proposal"), Mapping)
            else {}
        )
        output = f"Static review, repository-only fixture provenance, and the repaired fail-closed preflight contract are retained; P2 preflight state is {preflight_status}, the candidate proposal is {proposal.get('adoption', 'not_adopted')}, and no measured P2 artifact exists."
        result = "The minimum preflight enablement is validated as engineering evidence while measured runs, real candidates, freeze, and selection remain zero."
        interpretation = "The repairs strengthen stale authority, worktree boundary, capacity, immutable receipt, cross-platform source stability, advisory locking, journal recovery, detached supervision, and proposer isolation. They do not execute Owner-local preflight, compare R1 candidates, or support a retrieval claim."
        decision_status = str(p2.get("preflight_status", "not_started"))
    elif a2_freeze_valid:
        identity = (
            a2_freeze.get("official_identity", {})
            if isinstance(a2_freeze.get("official_identity"), Mapping)
            else {}
        )
        credit = (
            a2_freeze.get("official_credit", {})
            if isinstance(a2_freeze.get("official_credit"), Mapping)
            else {}
        )
        output = (
            "The Official Codex bridge and immutable A2 candidate universe are "
            f"validated for model {identity.get('model_name', 'not_recorded')}: "
            f"{a2_freeze.get('matched_candidate_count', 0)} matched and "
            f"{a2_freeze.get('conditional_reserve_candidate_count', 0)} dormant "
            "reserve candidates, with compile-twice replay and freeze-lock bindings."
        )
        audit_passed = a2_freeze.get("independent_audit_status") == "PASS"
        result = (
            "Candidate-freeze preparation and the independent audit are complete; "
            "measured A2 remains closed until a fresh A2-goal preflight. "
            if audit_passed
            else "Candidate-freeze preparation is complete and measured A2 remains blocked pending one independent audit. "
        ) + (
            "The final post-audit Official credit check "
            f"records plan {credit.get('plan_type', 'not_recorded')}, "
            f"{credit.get('remaining_percent', 'not_recorded')}% remaining, reset "
            f"at {credit.get('resets_at_utc', 'not_recorded')}, and no active limit."
        )
        interpretation = (
            "This engineering evidence prevents outcome-driven candidate generation "
            "and preserves a reviewer-reproducible representation universe. It does "
            "not evaluate a candidate, access REP-DEV for measurement, start an A2 "
            "run, authorize provider execution, or support a retrieval-quality claim."
        )
        decision_status = (
            "CLOSED_PASS_INDEPENDENT_AUDIT"
            if audit_passed and task_id == "OFFICIAL_CODEX_BRIDGE_AND_CANDIDATE_FREEZE"
            else "BLOCKED_EXTERNAL_PROVIDER_EVIDENCE"
            if audit_passed and a2_provider_admission_failed_closed
            else "READY_FOR_FRESH_A2_GOAL_PREFLIGHT"
            if audit_passed
            else "COMPLETE_AUDITOR_REVIEW_REQUIRED"
            if task_id == "OFFICIAL_CODEX_BRIDGE_AND_CANDIDATE_FREEZE"
            else "BLOCKED_PENDING_INDEPENDENT_AUDIT"
        )
    elif phase_id == "P0_FOUNDATION":
        output = (
            "Canonical control, schema, protected-boundary, and projection contracts."
        )
        result = "The foundation records the authority and safety boundary required by later phases."
        interpretation = "Engineering controls are available; no scientific metric follows from this phase."
        decision_status = "completed"
    elif phase_id.startswith("A") and task_id == "A0.8":
        feasibility = model.get("armindex", {}).get("compute_storage_feasibility", {})
        fixture_status = (
            str(feasibility.get("fixture_status", "not_started"))
            if isinstance(feasibility, Mapping)
            else "not_started"
        )
        output = "A receipt-bound synthetic CPU fixture records bounded compile, index-build, search, Python-allocation, and deterministic storage diagnostics."
        result = f"A0.8 is {status}; synthetic feasibility status is {fixture_status}; measured ArmIndex, Selection, and Final counters remain zero."
        interpretation = "The fixture proves that the A0.8 scaffold executes within its bounded synthetic CPU scope on the observed host. It does not estimate production bm25s capacity, retrieval quality, or dense-arm readiness."
        decision_status = status
    elif phase_id.startswith("A") and task_id == "A0.9":
        closeout = model.get("armindex", {}).get("phase_closeout", {})
        completed_tasks = (
            int(closeout.get("completed_task_count", 0))
            if isinstance(closeout, Mapping)
            else 0
        )
        validation_checks = (
            int(closeout.get("validation_check_count", 0))
            if isinstance(closeout, Mapping)
            else 0
        )
        output = f"A hash-bound phase receipt closes {completed_tasks} A0 tasks after {validation_checks} validation groups passed under the CPU-only engineering boundary."
        result = f"A0.9 is {status}; A0 is complete; measured ArmIndex, candidate, Selection, and Final counters remain zero."
        interpretation = "The closeout establishes repository and safety readiness for a synthetic/offline A1.1 adapter fixture scaffold. It does not authorize measured retrieval, model download, dense execution, or a scientific claim."
        decision_status = status
    elif phase_id.startswith("A") and task_id == "A0.10":
        harvest = model.get("armindex", {}).get("legacy_code_harvest", {})
        status_label = (
            str(harvest.get("status", "not_started"))
            if isinstance(harvest, Mapping)
            else "not_started"
        )
        reviewed = (
            int(harvest.get("components_reviewed", 0))
            if isinstance(harvest, Mapping)
            else 0
        )
        adopted = (
            int(harvest.get("components_adopted", 0))
            if isinstance(harvest, Mapping)
            else 0
        )
        fixture_status = (
            str(harvest.get("fixture_status", "not_started"))
            if isinstance(harvest, Mapping)
            else "not_started"
        )
        output = f"Receipt-first legacy code-harvest audit status is {status_label}; {reviewed} reviewed component(s) and {adopted} adopted component(s), repository hygiene, and output-root consolidation are represented by aggregate-safe commitments."
        result = f"A0.10 is {status}; synthetic vertical-slice status is {fixture_status}; measured ArmIndex, Selection, and Final counters remain zero."
        interpretation = "The ledger preserves source provenance and reuse decisions for engineering scaffolding. It does not validate retrieval quality, dense-model execution, or a production recommendation."
        decision_status = status
    elif (
        phase_id == "A1_BASELINES_AND_MULTI_ARM_SCREENING"
        and task_id is None
        and a12_validated
    ):
        registered_arms = (
            int(adapter.get("registered_arms", 0))
            if isinstance(adapter, Mapping)
            else 0
        )
        preflight_status = str(scaffold.get("preflight_status", "not_started"))
        blocker_count = (
            len(scaffold.get("preflight_blockers", []))
            if isinstance(scaffold.get("preflight_blockers"), list)
            else 0
        )
        vast = (
            scaffold.get("vast_preflight_v2", {})
            if isinstance(scaffold.get("vast_preflight_v2"), Mapping)
            else {}
        )
        vast_v3 = (
            scaffold.get("vast_preflight_v3", {})
            if isinstance(scaffold.get("vast_preflight_v3"), Mapping)
            else {}
        )
        vast_v5 = (
            scaffold.get("vast_preflight_v5", {})
            if isinstance(scaffold.get("vast_preflight_v5"), Mapping)
            else {}
        )
        vast_v6 = (
            scaffold.get("vast_preflight_v6", {})
            if isinstance(scaffold.get("vast_preflight_v6"), Mapping)
            else {}
        )
        vast_v7 = (
            scaffold.get("vast_preflight_v7", {})
            if isinstance(scaffold.get("vast_preflight_v7"), Mapping)
            else {}
        )
        vast_v8 = (
            scaffold.get("vast_preflight_v8", {})
            if isinstance(scaffold.get("vast_preflight_v8"), Mapping)
            else {}
        )
        vast_v9 = (
            scaffold.get("vast_preflight_v9", {})
            if isinstance(scaffold.get("vast_preflight_v9"), Mapping)
            else {}
        )
        closeout_v10 = (
            scaffold.get("provider_closeout_v10", {})
            if isinstance(scaffold.get("provider_closeout_v10"), Mapping)
            else {}
        )
        request_v11 = (
            scaffold.get("scientific_execution_request_v11", {})
            if isinstance(scaffold.get("scientific_execution_request_v11"), Mapping)
            else {}
        )
        adoption = (
            scaffold.get("adoption_inputs_v12_r3", {})
            if isinstance(scaffold.get("adoption_inputs_v12_r3"), Mapping)
            else {}
        )
        active = (
            vast_v9
            if vast_v9.get("validated") is True
            else vast_v8
            if vast_v8.get("validated") is True
            else vast_v7
        )
        active_revision = (
            "v9 execution-lifecycle repair"
            if active is vast_v9
            else "v8 validation-complete frozen-bundle repair"
            if active is vast_v8
            else "v7 same-instance repair"
        )
        live_result_pass = vast_v9.get("live_result_status") == "PASS"
        live_result = (
            vast_v9.get("live_result", {})
            if isinstance(vast_v9.get("live_result"), Mapping)
            else {}
        )
        provider_closed = (
            closeout_v10.get("validated") is True
            and closeout_v10.get("status") == "PASS"
        )
        v11_prepared = (
            request_v11.get("validated") is True and request_v11.get("status") == "PASS"
        )
        adoption_hardened = adoption.get("validated") is True
        publication = (
            adoption.get("publication_impact", {})
            if isinstance(adoption.get("publication_impact"), Mapping)
            else {}
        )
        output = f"The phase contains a completed A1.1 five-arm synthetic adapter fixture, preserved A1.2 v1-v10 lineage for {registered_arms} arms, the earlier CPU preflight with status {preflight_status} and {blocker_count} blocker group(s), and {active_revision} preparation using {vast_v6.get('image_reference', vast_v5.get('image_reference', 'not_recorded'))} on {vast_v6.get('platform', vast_v5.get('platform', 'not_recorded'))}. The additive v9 live synthetic result is {vast_v9.get('live_result_status', 'not_started')} for {len(live_result.get('arms', []))} dense arms, provider closeout v10 is {'PASS' if provider_closed else 'pending'}, scientific execution request v11 is {'prepared for Owner review' if v11_prepared else 'not prepared'}, and local adoption-input controls v12-r3 are {'validated' if adoption_hardened else 'not prepared'}."
        result = f"A1 request preparation is current through v11; {'the Owner destroyed the prior Vast instance and provider absence was observed' if provider_closed else 'Owner instance disposition remains pending'}. The v11 request freezes {request_v11.get('expected_program_arm_runs', 0)} logical program-arm results over {request_v11.get('rep_dev_query_count', 0)} REP-DEV queries, but is not adopted; v12-r3 keeps the 25 compiled bindings, protected handoff/transfer receipts, clean pushed bundle, and {len(adoption.get('pending_live_provider', [])) if adoption_hardened else 0} live-provider inputs pending. Measured ArmIndex, Selection, Final, and charged-resource counters remain zero."
        interpretation = f"The offline evidence preserves the v2 four-worker fixture and v3 correction, binds v5 to the direct official image manifest {vast_v5.get('resolved_manifest_digest', 'not_recorded')}, records v6 direct-container corrections, adds v7 same-instance repair controls, and uses v8 to close frozen validator lineage. {'The v9 result validates four synthetic adapter receipts, Qwen adapter-level 32768-token capacity, checkpoint/resume, safe export, and guest teardown.' if live_result_pass else 'The additive v9 repair remains preparation evidence only.'} {'The v10 closeout binds the later Owner provider-UI attestation to a sanitized connection-refused observation and explicitly records that no independent Vast API or CLI record was obtained.' if provider_closed else 'Provider disposition remains open.'} {'The v11 request adds a protected scientific transfer, executable P00-P04 specifications, 150/100 REP-DEV/HARNESS-DEV separation, all-fee budget admission, and 25 mandatory aggregate receipts.' if v11_prepared else 'The v11 request remains unavailable.'} {'V12-r3 binds the unchanged request to local-only verification, while v13 makes OUT Recall@100 the primary candidate-exposure outcome and keeps instance disposition pending live-provider evidence.' if adoption_hardened and publication.get('primary_outcome') == 'out_recall_at_100' else 'The additive adoption inputs remain unavailable.'} It does not establish retrieval quality, execution adoption, or scientific authorization."
        decision_status = "active"
    elif phase_id == "A1_BASELINES_AND_MULTI_ARM_SCREENING" and task_id == "A1.1":
        registered_arms = (
            int(adapter.get("registered_arms", 0))
            if isinstance(adapter, Mapping)
            else 0
        )
        dense_blocked = (
            int(adapter.get("dense_arms_blocked", 0))
            if isinstance(adapter, Mapping)
            else 0
        )
        output = (
            f"A receipt-bound synthetic adapter fixture validates {registered_arms} declared arms, "
            f"executes the ARM-01 compile-index-search-evaluate path on CPU, and blocks {dense_blocked} dense arms before model or network access."
        )
        result = f"A1.1 is {status}; the fixture passed; measured ArmIndex, candidate, Selection, and Final counters remain zero."
        interpretation = "The result establishes deterministic adapter-interface, lineage, fail-closed dense-arm, and CPU scaffold readiness. Synthetic metrics and host timings do not establish bm25s parity, production capacity, dense-model quality, or scientific retrieval performance."
        decision_status = status
    elif phase_id == "A1_BASELINES_AND_MULTI_ARM_SCREENING" and task_id == "A1.2":
        proposal_status = (
            str(adapter.get("gpu_proposal_status", "not_available"))
            if isinstance(adapter, Mapping)
            else "not_available"
        )
        if a12_validated:
            preflight_status = str(scaffold.get("preflight_status", "not_started"))
            blockers = scaffold.get("preflight_blockers", [])
            blocker_count = len(blockers) if isinstance(blockers, list) else 0
            vast = (
                scaffold.get("vast_preflight_v2", {})
                if isinstance(scaffold.get("vast_preflight_v2"), Mapping)
                else {}
            )
            vast_v3 = (
                scaffold.get("vast_preflight_v3", {})
                if isinstance(scaffold.get("vast_preflight_v3"), Mapping)
                else {}
            )
            vast_v5 = (
                scaffold.get("vast_preflight_v5", {})
                if isinstance(scaffold.get("vast_preflight_v5"), Mapping)
                else {}
            )
            vast_v6 = (
                scaffold.get("vast_preflight_v6", {})
                if isinstance(scaffold.get("vast_preflight_v6"), Mapping)
                else {}
            )
            vast_v7 = (
                scaffold.get("vast_preflight_v7", {})
                if isinstance(scaffold.get("vast_preflight_v7"), Mapping)
                else {}
            )
            vast_v8 = (
                scaffold.get("vast_preflight_v8", {})
                if isinstance(scaffold.get("vast_preflight_v8"), Mapping)
                else {}
            )
            vast_v9 = (
                scaffold.get("vast_preflight_v9", {})
                if isinstance(scaffold.get("vast_preflight_v9"), Mapping)
                else {}
            )
            closeout_v10 = (
                scaffold.get("provider_closeout_v10", {})
                if isinstance(scaffold.get("provider_closeout_v10"), Mapping)
                else {}
            )
            request_v11 = (
                scaffold.get("scientific_execution_request_v11", {})
                if isinstance(scaffold.get("scientific_execution_request_v11"), Mapping)
                else {}
            )
            adoption = (
                scaffold.get("adoption_inputs_v12_r3", {})
                if isinstance(scaffold.get("adoption_inputs_v12_r3"), Mapping)
                else {}
            )
            live_failures = (
                vast_v8.get("preserved_live_failures", [])
                if vast_v8.get("validated") is True
                and isinstance(vast_v8.get("preserved_live_failures"), list)
                else vast_v7.get("preserved_live_failures", [])
                if isinstance(vast_v7.get("preserved_live_failures"), list)
                else []
            )
            failure_source = vast_v8 if vast_v8.get("validated") is True else vast_v7
            active = (
                vast_v9
                if vast_v9.get("validated") is True
                else vast_v8
                if vast_v8.get("validated") is True
                else vast_v7
            )
            live_result_pass = vast_v9.get("live_result_status") == "PASS"
            live_result = (
                vast_v9.get("live_result", {})
                if isinstance(vast_v9.get("live_result"), Mapping)
                else {}
            )
            provider_closed = (
                closeout_v10.get("validated") is True
                and closeout_v10.get("status") == "PASS"
            )
            v11_prepared = (
                request_v11.get("validated") is True
                and request_v11.get("status") == "PASS"
            )
            adoption_hardened = adoption.get("validated") is True
            publication = (
                adoption.get("publication_impact", {})
                if isinstance(adoption.get("publication_impact"), Mapping)
                else {}
            )
            for item in live_failures:
                if not isinstance(item, Mapping):
                    continue
                failures.append(
                    {
                        "failure_id": item.get("failure_id"),
                        "failure_uri": failure_source.get("receipt_uri"),
                        "failure_sha256": failure_source.get("receipt_sha256"),
                        "recovery_id": item.get("disposition"),
                        "recovery_uri": failure_source.get("receipt_uri"),
                        "recovery_sha256": failure_source.get("receipt_sha256"),
                        "status": "preserved_and_repaired_preflight_pending",
                        "counters_changed": False,
                    }
                )
            failure_summary = "; ".join(
                str(item.get("failure_id", "unrecorded"))
                for item in live_failures
                if isinstance(item, Mapping)
            )
            output = f"The preserved v1-v10 contracts validate, the immutable v2 fixture records {vast.get('synthetic_worker_count', 0)} synthetic workers, and the additive v9 live synthetic result is {vast_v9.get('live_result_status', 'not_started')} for attempt {live_result.get('attempt_id', 'not_recorded')}. It preserves repair evidence for {failure_summary or 'no recorded failures'}; provider closeout v10 is {'PASS' if provider_closed else 'pending'}, request v11 is {'prepared for Owner review' if v11_prepared else 'not prepared'}, and v12-r3 local adoption inputs are {'validated' if adoption_hardened else 'not prepared'}."
            result = f"A1.2 v11 freezes {request_v11.get('workload_manifests', 0)} workloads, {request_v11.get('expected_program_arm_runs', 0)} required logical results, {request_v11.get('expected_physical_program_view_paths', 0)} physical program-view paths, and {request_v11.get('rep_dev_query_count', 0)} REP-DEV queries while reserving {request_v11.get('harness_dev_reserved_count', 0)} for HARNESS-DEV. V12-r3 preserves the unchanged workload and leaves the actual 25/25 protected compiled bindings, clean pushed bundle, and {len(adoption.get('pending_live_provider', [])) if adoption_hardened else 0} fresh live-provider inputs pending. It is not adopted; scientific launch remains locked and measured runs and charged USD counters remain zero."
            interpretation = "The v5 receipt retains v1-v3 provenance while selecting the official PyTorch linux/amd64 base image. v6-v8 preserve direct-container corrections, failed-closed evidence, bytecode suppression, and complete validator lineage. The v9 PASS establishes only synthetic adapter compatibility, bounded Qwen capacity for the frozen single-GPU configuration, lifecycle checkpoint/resume, safe return, and guest-process cleanup. The additive v10 closeout records the Owner destroy attestation and endpoint-unreachable observation, while explicitly limiting the claim because no independent Vast API or CLI record was obtained. The repaired v11 request adds exact P00-P04 compiler hashes, protected opaque transfer/return rules, aggregate result schemas, whole-workload completion, and all-fee budget admission. V12-r3 binds an unchanged v11 request to local-only inputs, and v13 declares OUT Recall@100 as the candidate-exposure primary outcome with nDCG outcomes secondary; both remain preparation evidence, not retrieval-quality or publication evidence."
            decision_status = "active" if live_result_pass else "blocked"
        else:
            output = f"A bounded single-GPU specification, elapsed-time range, charged-USD estimate, admission requirements, and Owner needs are available with status {proposal_status}."
            result = "A1.2 measured screening remains blocked pending a separate versioned execution contract and hash-bound budget profile; no GPU reservation or measured run occurred."
            interpretation = "The proposal is resource planning evidence only. A 24 GiB sequential GPU screen is plausible under the stated assumptions, but protected workload size, live provider pricing, pre-staged artifact hashes, and an Owner-local throughput pilot are still required before adoption."
        decision_status = "blocked"
    elif phase_id.startswith("A"):
        armindex = (
            model.get("armindex", {})
            if isinstance(model.get("armindex"), Mapping)
            else {}
        )
        output = "Versioned ArmIndex control, schema, code, and projection state with historical SCOPE/P1 evidence preserved by pointer."
        result = f"{phase_id} is {status}; ArmIndex measured runs, Selection, and Final counters remain zero."
        interpretation = "This is engineering migration provenance only and supports no retrieval-quality, champion, or production claim."
        decision_status = status
    else:
        output = "No execution output is available because the phase is locked behind its Owner decision."
        result = "The phase remains planned and closed."
        interpretation = (
            "No interpretation is available before the required gate and evidence."
        )
        decision_status = "waiting_owner"
    supported = [
        {"claim": output, "evidence": [item["artifact_id"] for item in artifacts]}
    ]
    unsupported = [
        "Measured P2 improvement or candidate superiority before a real measured run.",
        "Final-split generalization or publication release before D2 and D3.",
        "Causal or legal conclusions from retrieval aggregates.",
    ]
    if current_failed_closed:
        unsupported.append(
            "The incomplete current attempt as a measured A1 result, promotion input, or completion claim."
        )
    armindex = (
        model.get("armindex", {}) if isinstance(model.get("armindex"), Mapping) else {}
    )
    armindex_counters = (
        armindex.get("counters", {})
        if isinstance(armindex.get("counters"), Mapping)
        else {}
    )
    governance = {
        "protected_data_accessed": False if a2_freeze_valid else scientific,
        "measured_execution": False if a2_freeze_valid else scientific,
        "gpu": current_pass,
        "paid_api": False,
        "network_model_download": False,
        "provider_fallback": False,
        "d2": "waiting_owner",
        "d3": "waiting_owner",
        "final_split": "closed",
        "real_counters": {
            "measured_runs": 0
            if a2_freeze_valid
            else int(armindex_counters.get("measured_runs", 0))
            if phase_id.startswith("A")
            else int(p2.get("measured_runs", 0)),
            "candidate_count": 0
            if a2_freeze_valid
            else int(armindex_counters.get("candidate_count", 0))
            if phase_id.startswith("A")
            else int(p2.get("candidate_count", 0)),
            "shortlist_count": 0
            if phase_id.startswith("A")
            else int(p2.get("shortlist_count", 0)),
            "selection_accesses": int(armindex_counters.get("selection_accesses", 0))
            if phase_id.startswith("A")
            else int(p2.get("selection_accesses", 0)),
            "final_accesses": int(armindex_counters.get("final_accesses", 0))
            if phase_id.startswith("A")
            else 0,
        },
        "evidence_class": evidence_class,
        "scientific_authority": scientific,
    }
    if phase_id == "P2_SCOPE_DEVELOPMENT":
        governance["preflight_status"] = str(p2.get("preflight_status", "not_started"))
        governance["preflight_safe_to_measure"] = bool(
            isinstance(p2.get("preflight"), Mapping)
            and p2.get("preflight", {}).get("safe_to_measure") is True
        )
    if current_failed_closed:
        governance["current_attempt_status"] = "FAILED_CLOSED"
        governance["current_attempt_partial_results_promotable"] = False
        governance["official_completed_measured_runs"] = 0
    if a2_freeze_valid:
        governance["gpu"] = False
        governance["official_model_name"] = a2_freeze.get(
            "official_identity", {}
        ).get("model_name")
        governance["provider_admission_performed"] = False
        governance["provider_execution_adoption_performed"] = False
        governance["rep_dev_accessed_for_measurement"] = False
        governance["independent_auditor_required"] = True
    record = {
        "schema_version": REPORT_SCHEMA,
        "report_id": report_id,
        "report_type": report_type,
        "phase_id": phase_id,
        "task_id": task_id,
        "status": status,
        "language": "en",
        "evidence_class": evidence_class,
        "scientific_authority": scientific,
        "claim_boundary": claim_boundary,
        "generated_at": str(model.get("generated_at", "1970-01-01T00:00:00Z")),
        "generated_from_revision": str(model.get("read_model_revision")),
        "last_material_update": str(model.get("generated_at", "1970-01-01T00:00:00Z")),
        "git_commit": str(model.get("source_commit", "0" * 40)),
        "objective": objective,
        "starting_state": {
            "phase": armindex.get("current_phase")
            if phase_id.startswith("A")
            else model.get("project", {}).get("current_phase"),
            "task": task_id
            if phase_id.startswith("A")
            else model.get("project", {}).get("current_task"),
            "program_state": armindex.get("status")
            if phase_id.startswith("A")
            else model.get("project", {}).get("state"),
            "authorization": "D1_START_CAMPAIGN; D2/D3 remain Owner-only",
            "claim_boundary": "No unsupported scientific claim",
        },
        "input_bindings": _bindings(root, model, phase_id, task_id),
        "work_summary": (
            "The interrupted runtime attempt and earlier P2 audits were preserved; the v2 runbook, profile, envelope, journal, lock, supervisor, resume, and proposer contracts were implemented with no Owner-local preflight or measured execution started."
            if phase_id == "P2_SCOPE_DEVELOPMENT"
            else "The allowlisted loopback Official Codex bridge passed its synthetic smoke, Official identity and credit availability were recorded, 52 schema-valid candidates were independently proposed and reviewed, every candidate compiled deterministically twice, and exactly 40 matched plus 12 dormant reserve candidates were locked before measurement. The additive credit correction preserves immutable freeze bytes while identifying the chronological reviewer-final and post-freeze closeout snapshots."
            if a2_freeze_valid
            else "The five-arm adapter interface was validated with synthetic offline inputs; ARM-01 completed deterministic compilation, CPU indexing, family-level search and aggregate evaluation, while ARM-02 through ARM-05 failed closed. Write-once artifacts, a hash-chained ledger, a task receipt, detailed English reporting controls, archive safeguards, and a non-authorizing A1.2 resource proposal were bound without protected-data access or charged compute."
            if phase_id == "A1_BASELINES_AND_MULTI_ARM_SCREENING" and task_id == "A1.1"
            else "A1.1 and A1.2 are complete. Attempt r15 completed the frozen 25/25 REP-DEV common screen, safe return, Owner-local evaluation, deterministic promotion, aggregate result and EDA packaging, and a REUSE_ELIGIBLE provider closeout. Historical v1-v15 planning, preflight, and repair records remain immutable lineage only; A2, HARNESS-DEV, Selection, and Final have not started, and A2 still requires fresh admission, execution adoption, and a new isolated remote root."
            if phase_id == "A1_BASELINES_AND_MULTI_ARM_SCREENING"
            and task_id in {None, "A1.2"}
            and current_pass
            else "A1.1 synthetic adapter evidence and the A1.2 v1-v10 preflight/closeout lineage are validated. The additive v11 request preserves that history and freezes a separate protected scientific transfer, executable P00-P04 compiler source/spec hashes, 150 REP-DEV queries with 100 reserved for HARNESS-DEV, 25 required aggregate result receipts, all-fee budget admission, and a fresh-provider plan. The prior instance is destroyed. Provider contact, adoption, measured retrieval, Selection, Final, and paid API work remain closed."
            if phase_id == "A1_BASELINES_AND_MULTI_ARM_SCREENING"
            and task_id is None
            and a12_validated
            else "The A1.1 receipt anchors a validated A1.2 lineage through v10 provider closeout. The repaired additive v11 request binds the future protected transfer, exact five-program scientific compiler, five workload manifests, aggregate result schema, stop conditions, fresh-provider admission, and hard-stop budget. The request is prepared for Owner review only; launch and adoption remain false pending the unchanged request hash, protected handoff/transfer receipts, 25 compiled program bindings, fresh quote/identity, full-TTL budget fit, and watchdog/destroy validation."
            if phase_id == "A1_BASELINES_AND_MULTI_ARM_SCREENING" and task_id == "A1.2"
            else "The A0.10 receipt, ledger, repository hygiene audit, output-root relocation receipt, and external-source verification receipt were validated before the shared read-model projection; legacy source code remains reference-only unless the receipt records an explicit disposition."
            if phase_id.startswith("A") and task_id == "A0.10"
            else "The active repository is migrated in place to ArmIndex with versioned contracts and projections while historical SCOPE/P1/P2 evidence remains immutable and readable."
            if phase_id.startswith("A")
            else "This report is generated from validated canonical records; planning, implementation, review, fixture, measured execution, and reporting are kept distinct."
        ),
        "artifact_references": artifacts,
        "metric_references": metrics,
        "result": {"output": output, "result": result, "decision": decision_status},
        "interpretation": interpretation,
        "supported_claims": supported,
        "unsupported_claims": unsupported,
        "failure_recovery_references": failures,
        "governance_status": governance,
        "decision": {
            "status": decision_status,
            "reason": result,
            "owner_decisions_unchanged": True,
        },
        "next_authorized_action": str(a2_readiness.get("next_authorized_action"))
        if a2_readiness_valid
        else str(a2_freeze.get("next_authorized_action"))
        if a2_freeze_valid
        else _next_action(model),
        "evidence_links": [
            {
                "artifact_id": item["artifact_id"],
                "uri": item["safe_uri"],
                "sha256": item.get("content_sha256"),
            }
            for item in artifacts
        ],
        "validation_status": "validated",
    }
    if phase_id == "P2_SCOPE_DEVELOPMENT":
        record["preflight_status"] = str(p2.get("preflight_status", "not_started"))
    record["report_sha256"] = sha256(canonical_json(record))
    return record


def build_report_records(root: Path, model: Mapping[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for phase in model.get("phases", []):
        if not isinstance(phase, Mapping):
            continue
        records.append(_record_for(root, model, phase=phase, task=None))
        for task in phase.get("tasks", []):
            if isinstance(task, Mapping):
                records.append(_record_for(root, model, phase=phase, task=task))
    armindex = (
        model.get("armindex", {}) if isinstance(model.get("armindex"), Mapping) else {}
    )
    for phase in armindex.get("phases", []):
        if not isinstance(phase, Mapping):
            continue
        records.append(_record_for(root, model, phase=phase, task=None))
        for task in phase.get("tasks", []):
            if isinstance(task, Mapping):
                records.append(_record_for(root, model, phase=phase, task=task))
    for record in records:
        validate_report_record(record)
    return records


def validate_report_record(record: Mapping[str, Any]) -> None:
    try:
        Draft202012Validator(_schema()).validate(dict(record))
    except Exception as error:  # jsonschema exposes several validation types
        raise ValueError(
            f"phase/task report schema validation failed: {error}"
        ) from error
    unsigned = {key: value for key, value in record.items() if key != "report_sha256"}
    if sha256(canonical_json(unsigned)) != record.get("report_sha256"):
        raise ValueError(f"phase/task report hash mismatch: {record.get('report_id')}")
    if record.get("evidence_class") == "fixture" and record.get("scientific_authority"):
        raise ValueError("fixture report cannot be scientifically authoritative")
    _scan_safe(record)


def _scan_safe(value: Any, *, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if _FORBIDDEN.search(key_text) and not key_text.endswith(
                ("_sha256", "_hash")
            ):
                raise ValueError(f"protected report field: {path}.{key_text}")
            _scan_safe(item, path=f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_safe(item, path=f"{path}[{index}]")
    elif isinstance(value, str) and _ABSOLUTE.search(value):
        raise ValueError(f"absolute personal path in report: {path}")


def report_json_outputs(root: Path, model: Mapping[str, Any]) -> dict[Path, str]:
    records = build_report_records(root, model)
    outputs: dict[Path, str] = {}
    index_entries = []
    for record in records:
        folder = "phase" if record["report_type"] == "phase" else "task"
        relative = REPORT_ROOT / folder / f"{record['report_id']}.json"
        content = json.dumps(record, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
        outputs[root / relative] = content
        index_entries.append(
            {
                "report_id": record["report_id"],
                "report_type": record["report_type"],
                "phase_id": record["phase_id"],
                "task_id": record["task_id"],
                "uri": relative.as_posix(),
                "sha256": record["report_sha256"],
            }
        )
    index = {
        "schema_version": REPORT_INDEX_SCHEMA,
        "read_model_revision": model["read_model_revision"],
        "read_model_sha256": model["read_model_sha256"],
        "source_commit": model["source_commit"],
        "reports": sorted(index_entries, key=lambda item: item["report_id"]),
    }
    index["index_sha256"] = sha256(canonical_json(index))
    outputs[root / (REPORT_ROOT / "index.json")] = (
        json.dumps(index, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    )
    return outputs
