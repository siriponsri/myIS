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
P2_PREFLIGHT_INITIAL_AUDIT = "outputs/audits/rigor/p2-preflight-completion-audit-20260802.json"
P2_PREFLIGHT_REPAIR_AUDIT = "outputs/audits/rigor/p2-preflight-completion-repair-20260802.json"
P2_REPORT_BYTE_INITIAL_AUDIT = "outputs/audits/rigor/p2-preflight-report-byte-drift-audit-20260802.json"
P2_REPORT_BYTE_REPAIR_AUDIT = "outputs/audits/rigor/p2-preflight-report-byte-drift-repair-20260802.json"
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
    if value in {"in_progress", "active", "executable"}:
        return "active"
    if value in {"blocked", "blocked_until_p1"}:
        return "blocked"
    return "planned"


def _next_action(model: Mapping[str, Any]) -> str:
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


def _artifacts(root: Path, model: Mapping[str, Any], phase_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    p1 = phase_id == "P1_CPU_BASELINE"
    if p1:
        for run in model.get("runs", []):
            if not isinstance(run, Mapping):
                continue
            run_id = str(run.get("run_id", ""))
            if not run_id:
                continue
            uri = f"campaigns/scope-autoindex-v1/manifests/{run_id}.json"
            result.append(_artifact(
                artifact_id=f"{run_id}-manifest",
                title=f"Validated aggregate manifest for {run_id}",
                artifact_type="manifest",
                evidence_class="train_selection_measured",
                scientific_authority=True,
                safe_uri=uri,
                content_sha256=str(run.get("manifest_sha256")) if run.get("manifest_sha256") else _hash_file(root, uri),
                explanation="Binds one aggregate run slot to its immutable request and evaluator lineage.",
            ))
        result_row = next((item for item in model.get("results", []) if isinstance(item, Mapping) and item.get("result_id") == "P1-CPU-BASELINE"), {})
        for key, title, artifact_type, uri, digest_key, explanation in (
            ("p1-four-slot-package", "P1 four-slot package", "package", "campaigns/scope-autoindex-v1/packages/dapfam-p1-fulltext-c058a3aa7357c782.package.json", "package_file_sha256", "Binds all four measured slots, manifests, and validation reports."),
            ("p1-rigor-review", "P1 artifact-only rigor review", "review", "outputs/audits/rigor/dapfam-p1-fulltext-c058a3aa7357c782/rigor_review.json", "rigor_review_sha256", "Records the independent artifact-only review without exposing protected payloads."),
        ):
            result.append(_artifact(
                artifact_id=key,
                title=title,
                artifact_type=artifact_type,
                evidence_class="train_selection_measured",
                scientific_authority=True,
                safe_uri=uri,
                content_sha256=str(result_row.get(digest_key)) if result_row.get(digest_key) else _hash_file(root, uri),
                explanation=explanation,
            ))
    elif phase_id == "P2_SCOPE_DEVELOPMENT":
        p2 = model.get("p2_readiness", {}) if isinstance(model.get("p2_readiness"), Mapping) else {}
        fixture = p2.get("fixture_pilot", {}) if isinstance(p2.get("fixture_pilot"), Mapping) else {}
        review = p2.get("official_review", {}) if isinstance(p2.get("official_review"), Mapping) else {}
        if fixture.get("status") == "passed":
            for artifact_id, title, artifact_type, uri, digest, explanation in (
                ("p2-fixture-receipt", "P2 repository-only fixture receipt", "receipt", str(fixture.get("receipt_uri")), fixture.get("receipt_sha256"), "Proves the synthetic lifecycle and zero real counters."),
                ("p2-fixture-manifest", "P2 fixture execution manifest", "manifest", str(fixture.get("execution_manifest_uri")), fixture.get("execution_manifest_sha256"), "Separates fixture metadata from the canonical measured request."),
                ("p2-fixture-package", "P2 fixture package", "package", "outputs/fixtures/p2/index.json", fixture.get("fixture_package_sha256"), "Binds the deterministic fixture package and checksum closure."),
            ):
                result.append(_artifact(artifact_id=artifact_id, title=title, artifact_type=artifact_type, evidence_class="fixture", scientific_authority=False, safe_uri=uri, content_sha256=str(digest) if digest else _hash_file(root, uri), explanation=explanation))
        source = review.get("source", {}) if isinstance(review.get("source"), Mapping) else {}
        if review.get("status") == "accepted_static_contract_review" and source:
            result.append(_artifact(
                artifact_id="p2-official-review-index",
                title="Official P2 static review index",
                artifact_type="review",
                evidence_class="static_contract_review",
                scientific_authority=False,
                safe_uri=str(source.get("index_uri", "orchestration/audits/p2-readiness/index.json")),
                content_sha256=str(source.get("index_sha256")) if source.get("index_sha256") else None,
                explanation="Records Round 1 revise, Round 2 revise, and Round 3 accept as engineering provenance.",
            ))
        proposal = p2.get("candidate_proposal", {}) if isinstance(p2.get("candidate_proposal"), Mapping) else {}
        if proposal.get("status") == "draft_owner_review" and proposal.get("validated") is True:
            result.append(_artifact(
                artifact_id="p2-candidate-freeze-proposal",
                title="P2 four-control and eight-candidate freeze proposal",
                artifact_type="proposal",
                evidence_class="engineering",
                scientific_authority=False,
                safe_uri=str(proposal.get("proposal_uri")),
                content_sha256=str(proposal.get("proposal_sha256")),
                explanation="Records an unadopted Owner-review draft; it does not register or hash-lock measured candidates.",
            ))
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
        ):
            digest = _hash_file(root, uri)
            if digest:
                result.append(_artifact(
                    artifact_id=artifact_id,
                    title=title,
                    artifact_type="review",
                    evidence_class="engineering",
                    scientific_authority=False,
                    safe_uri=uri,
                    content_sha256=digest,
                    explanation=explanation,
                ))
        observatory = model.get("observatory", {}) if isinstance(model.get("observatory"), Mapping) else {}
        if observatory.get("status") == "ready":
            result.append(_artifact(
                artifact_id="observatory-fixture-registry",
                title="Aggregate-safe Observatory registry",
                artifact_type="registry",
                evidence_class="fixture",
                scientific_authority=False,
                safe_uri="outputs/observatory/fixture-v1/registry.json",
                content_sha256=str(observatory.get("registry_sha256")),
                explanation="Captures prompts, configs, environments, failures, recovery, and safe lineage without protected content.",
            ))
    elif phase_id == "P0_FOUNDATION":
        for relative, title in (
            ("control/source-of-truth.yaml", "Source-of-truth contract"),
            ("schemas/read-model.v2.json", "Shared read-model schema"),
            ("docs/observatory/REPORTING_POLICY.md", "Reporting policy"),
        ):
            result.append(_artifact(artifact_id=relative.replace("/", "-"), title=title, artifact_type="schema", evidence_class="engineering", scientific_authority=False, safe_uri=relative, content_sha256=_hash_file(root, relative), explanation="Defines the canonical boundary used to build and validate projections."))
    return result


def _metrics(model: Mapping[str, Any], phase_id: str, task_id: str | None) -> list[dict[str, Any]]:
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


def _bindings(root: Path, model: Mapping[str, Any], phase_id: str) -> dict[str, Any]:
    bindings: dict[str, Any] = {
        "source_of_truth": {"uri": "control/source-of-truth.yaml", "sha256": _hash_file(root, "control/source-of-truth.yaml")},
        "campaign": {"uri": "control/campaigns/scope-autoindex-v1.yaml", "sha256": _hash_file(root, "control/campaigns/scope-autoindex-v1.yaml")},
        "git_commit": model.get("source_commit"),
    }
    if phase_id == "P1_CPU_BASELINE":
        bindings["execution_envelope"] = {"uri": "control/execution-envelope.yaml", "sha256": _hash_file(root, "control/execution-envelope.yaml")}
        bindings["request_id"] = "dapfam-p1-fulltext-c058a3aa7357c782"
        bindings["protected_payloads"] = "owner-local; aggregate hashes only in this report"
    elif phase_id == "P2_SCOPE_DEVELOPMENT":
        p2 = model.get("p2_readiness", {}) if isinstance(model.get("p2_readiness"), Mapping) else {}
        official_review = p2.get("official_review", {}) if isinstance(p2.get("official_review"), Mapping) else {}
        review_source = official_review.get("source", {}) if isinstance(official_review.get("source"), Mapping) else {}
        fixture = p2.get("fixture_pilot", {}) if isinstance(p2.get("fixture_pilot"), Mapping) else {}
        observatory = model.get("observatory", {}) if isinstance(model.get("observatory"), Mapping) else {}
        bindings["budget_profile"] = {"uri": "control/budgets/p2-r1-primary-v1.yaml", "sha256": p2.get("budget_profile_sha256")}
        bindings["execution_envelope"] = {"uri": "control/execution-envelope-p2.yaml", "sha256": _hash_file(root, "control/execution-envelope-p2.yaml")}
        bindings["campaign_revision"] = p2.get("campaign_revision")
        bindings["static_review"] = {"uri": "orchestration/audits/p2-readiness/index.json", "sha256": review_source.get("index_sha256")}
        bindings["fixture_receipt"] = {"uri": fixture.get("receipt_uri"), "sha256": fixture.get("receipt_sha256")}
        bindings["fixture_manifest"] = {"uri": fixture.get("execution_manifest_uri"), "sha256": fixture.get("execution_manifest_sha256")}
        bindings["observatory_registry"] = {"uri": "outputs/observatory/fixture-v1/registry.json", "sha256": observatory.get("registry_sha256")}
        bindings["observatory_receipt"] = {"uri": "outputs/observatory/fixture-v1/receipt.json", "sha256": observatory.get("receipt_sha256")}
        preflight = p2.get("preflight", {}) if isinstance(p2.get("preflight"), Mapping) else {}
        bindings["preflight_receipt"] = {"uri": preflight.get("receipt_uri"), "sha256": preflight.get("receipt_sha256")}
        proposal = p2.get("candidate_proposal", {}) if isinstance(p2.get("candidate_proposal"), Mapping) else {}
        bindings["candidate_freeze_proposal"] = {"uri": proposal.get("proposal_uri"), "sha256": proposal.get("proposal_sha256")}
    return bindings


def _record_for(root: Path, model: Mapping[str, Any], *, phase: Mapping[str, Any], task: Mapping[str, Any] | None) -> dict[str, Any]:
    phase_id = str(phase.get("phase_id", ""))
    task_id = str(task.get("task_id")) if task else None
    report_type = "task" if task else "phase"
    report_id = (f"task-{task_id.lower().replace('.', '-')}") if task_id else f"phase-{phase_id.lower()}"
    status = _lifecycle(task.get("status") if task else phase.get("status"))
    scientific = phase_id == "P1_CPU_BASELINE"
    evidence_class = "train_selection_measured" if scientific else "fixture" if phase_id == "P2_SCOPE_DEVELOPMENT" and model.get("p2_readiness", {}).get("fixture_pilot", {}).get("status") == "passed" else "engineering" if phase_id == "P0_FOUNDATION" else "planned"
    claim_boundary = "train_selection_only" if scientific else "engineering_provenance_only" if phase_id in {"P0_FOUNDATION", "P2_SCOPE_DEVELOPMENT"} else "unavailable"
    objective = str(task.get("title")) if task else f"Deliver the {phase_id} research phase with an auditable evidence boundary."
    if phase_id == "P2_SCOPE_DEVELOPMENT":
        objective = "Prepare and validate the deterministic R1 SCOPE/AutoIndex lifecycle without starting measured P2."
    metrics = _metrics(model, phase_id, task_id)
    artifacts = _artifacts(root, model, phase_id)
    p2 = model.get("p2_readiness", {}) if isinstance(model.get("p2_readiness"), Mapping) else {}
    failures = []
    if phase_id == "P2_SCOPE_DEVELOPMENT" and model.get("observatory", {}).get("failed_child_count", 0):
        failures.append({"failure_id": "obs-failure-candidate-02", "recovery_id": "obs-recovery-candidate-02", "status": "retained_and_recovered", "counters_changed": False})
    if phase_id == "P2_SCOPE_DEVELOPMENT":
        initial_audit_sha256 = _hash_file(root, P2_PREFLIGHT_INITIAL_AUDIT)
        repair_audit_sha256 = _hash_file(root, P2_PREFLIGHT_REPAIR_AUDIT)
        if initial_audit_sha256 and repair_audit_sha256:
            failures.append({
                "failure_id": "p2-preflight-completion-audit-20260802",
                "failure_uri": P2_PREFLIGHT_INITIAL_AUDIT,
                "failure_sha256": initial_audit_sha256,
                "recovery_id": "p2-preflight-completion-repair-20260802",
                "recovery_uri": P2_PREFLIGHT_REPAIR_AUDIT,
                "recovery_sha256": repair_audit_sha256,
                "status": "repaired_and_validated",
                "counters_changed": False,
            })
        byte_initial_sha256 = _hash_file(root, P2_REPORT_BYTE_INITIAL_AUDIT)
        byte_repair_sha256 = _hash_file(root, P2_REPORT_BYTE_REPAIR_AUDIT)
        if byte_initial_sha256 and byte_repair_sha256:
            failures.append({
                "failure_id": "p2-preflight-report-byte-drift-audit-20260802",
                "failure_uri": P2_REPORT_BYTE_INITIAL_AUDIT,
                "failure_sha256": byte_initial_sha256,
                "recovery_id": "p2-preflight-report-byte-drift-repair-20260802",
                "recovery_uri": P2_REPORT_BYTE_REPAIR_AUDIT,
                "recovery_sha256": byte_repair_sha256,
                "status": "repaired_and_validated",
                "counters_changed": False,
            })
    if scientific:
        output = "Four validated R0/R0-W train and selection manifests with aggregate Recall@100 metrics."
        result = "P1 measured train/selection evidence is complete within its declared development boundary."
        interpretation = "The metrics describe the fixed CPU protocol on train and selection; they do not establish final-split generalization or legal conclusions."
        decision_status = "completed"
    elif phase_id == "P2_SCOPE_DEVELOPMENT":
        preflight_status = str(p2.get("preflight_status", "not_started"))
        proposal = p2.get("candidate_proposal", {}) if isinstance(p2.get("candidate_proposal"), Mapping) else {}
        output = f"Static review, repository-only fixture provenance, and the repaired fail-closed preflight contract are retained; P2 preflight state is {preflight_status}, the candidate proposal is {proposal.get('adoption', 'not_adopted')}, and no measured P2 artifact exists."
        result = "The minimum preflight enablement is validated as engineering evidence while measured runs, real candidates, freeze, and selection remain zero."
        interpretation = "The repairs strengthen stale authority, worktree boundary, capacity, immutable receipt, negative-test behavior, and cross-platform report-byte stability. They do not execute Owner-local preflight, compare R1 candidates, or support a retrieval claim."
        decision_status = str(p2.get("preflight_status", "not_started"))
    elif phase_id == "P0_FOUNDATION":
        output = "Canonical control, schema, protected-boundary, and projection contracts."
        result = "The foundation records the authority and safety boundary required by later phases."
        interpretation = "Engineering controls are available; no scientific metric follows from this phase."
        decision_status = "completed"
    else:
        output = "No execution output is available because the phase is locked behind its Owner decision."
        result = "The phase remains planned and closed."
        interpretation = "No interpretation is available before the required gate and evidence."
        decision_status = "waiting_owner"
    supported = [{"claim": output, "evidence": [item["artifact_id"] for item in artifacts]}]
    unsupported = [
        "Measured P2 improvement or candidate superiority before a real measured run.",
        "Final-split generalization or publication release before D2 and D3.",
        "Causal or legal conclusions from retrieval aggregates.",
    ]
    governance = {
        "protected_data_accessed": scientific,
        "measured_execution": scientific,
        "gpu": False,
        "paid_api": False,
        "network_model_download": False,
        "provider_fallback": False,
        "d2": "waiting_owner",
        "d3": "waiting_owner",
        "final_split": "closed",
        "real_counters": {
            "measured_runs": int(p2.get("measured_runs", 0)),
            "candidate_count": int(p2.get("candidate_count", 0)),
            "shortlist_count": int(p2.get("shortlist_count", 0)),
            "selection_accesses": int(p2.get("selection_accesses", 0)),
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
    record = {
        "schema_version": REPORT_SCHEMA,
        "report_id": report_id,
        "report_type": report_type,
        "phase_id": phase_id,
        "task_id": task_id,
        "status": status,
        "evidence_class": evidence_class,
        "scientific_authority": scientific,
        "claim_boundary": claim_boundary,
        "generated_at": str(model.get("generated_at", "1970-01-01T00:00:00Z")),
        "generated_from_revision": str(model.get("read_model_revision")),
        "last_material_update": str(model.get("generated_at", "1970-01-01T00:00:00Z")),
        "git_commit": str(model.get("source_commit", "0" * 40)),
        "objective": objective,
        "starting_state": {
            "phase": model.get("project", {}).get("current_phase"),
            "task": model.get("project", {}).get("current_task"),
            "program_state": model.get("project", {}).get("state"),
            "authorization": "D1_START_CAMPAIGN; D2/D3 remain Owner-only",
            "claim_boundary": "No unsupported scientific claim",
        },
        "input_bindings": _bindings(root, model, phase_id),
        "work_summary": (
            "The initial P2 preflight completion and post-merge report-byte audits were preserved, both recovery chains were validated, and no Owner-local preflight or measured execution was started."
            if phase_id == "P2_SCOPE_DEVELOPMENT"
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
        "decision": {"status": decision_status, "reason": result, "owner_decisions_unchanged": True},
        "next_authorized_action": _next_action(model),
        "evidence_links": [{"artifact_id": item["artifact_id"], "uri": item["safe_uri"], "sha256": item.get("content_sha256")} for item in artifacts],
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
    for record in records:
        validate_report_record(record)
    return records


def validate_report_record(record: Mapping[str, Any]) -> None:
    try:
        Draft202012Validator(_schema()).validate(dict(record))
    except Exception as error:  # jsonschema exposes several validation types
        raise ValueError(f"phase/task report schema validation failed: {error}") from error
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
            if _FORBIDDEN.search(key_text) and not key_text.endswith(("_sha256", "_hash")):
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
        index_entries.append({"report_id": record["report_id"], "report_type": record["report_type"], "phase_id": record["phase_id"], "task_id": record["task_id"], "uri": relative.as_posix(), "sha256": record["report_sha256"]})
    index = {
        "schema_version": REPORT_INDEX_SCHEMA,
        "read_model_revision": model["read_model_revision"],
        "read_model_sha256": model["read_model_sha256"],
        "source_commit": model["source_commit"],
        "reports": sorted(index_entries, key=lambda item: item["report_id"]),
    }
    index["index_sha256"] = sha256(canonical_json(index))
    outputs[root / (REPORT_ROOT / "index.json")] = json.dumps(index, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    return outputs
