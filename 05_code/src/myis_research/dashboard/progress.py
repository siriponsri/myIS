"""Deterministic Phase -> Task projection for the Owner dashboard."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..ledger import ImmutableJsonLedger
from .contracts import OwnerGateDecisionRecord, TaskEvidenceRecord


EXPECTED_PHASE_ORDER = ("F0", "F1", "C0", "C1", "C2", "CF", "R0", "R1", "R2", "S", "Q", "P")
EXPECTED_TASK_ORDER = (
    "F0.1",
    "F0.2",
    "F0.3",
    "F1.1",
    "C0.1",
    "C1.1",
    "C2.1",
    "CF.1",
    "R0.1",
    "R1.1",
    "R2.1",
    "S.1",
    "S.2",
    "Q.1",
    "P.1",
)
REQUIRED_TASK_FIELDS = (
    "Goal",
    "Execution model",
    "Objective",
    "Acceptance",
    "Owner Gate",
    "Budget/stop",
    "Rollback",
    "Scientific validity risk",
    "Dependencies",
)

_PHASE_HEADING = re.compile(r"^## Phase ([A-Z][A-Z0-9]*) - (.+)$")
_TASK_HEADING = re.compile(r"^### Task ([A-Z][A-Z0-9]*\.[0-9]+) - (.+)$")
_FIELD = re.compile(r"^- \*\*(.+?):\*\*\s*(.*)$")
_GATE = re.compile(r"\bG[0-8]\b")


@dataclass(frozen=True, slots=True)
class ParsedTask:
    task_id: str
    title: str
    phase_id: str
    fields: dict[str, str]


@dataclass(frozen=True, slots=True)
class ParsedPhase:
    phase_id: str
    title: str
    tasks: tuple[ParsedTask, ...]


@dataclass(frozen=True, slots=True)
class ParsedPlan:
    sha256: str
    phases: tuple[ParsedPhase, ...]


def parse_plan(path: Path) -> ParsedPlan:
    """Parse the canonical two-level plan and reject structural drift."""

    if path.is_symlink() or not path.is_file():
        raise ValueError("PLAN.md must be a regular non-symlink file")
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    phases: list[tuple[str, str, list[ParsedTask]]] = []
    current_phase: tuple[str, str, list[ParsedTask]] | None = None
    task_id: str | None = None
    task_title = ""
    task_lines: list[str] = []

    def finish_task() -> None:
        nonlocal task_id, task_title, task_lines
        if task_id is None:
            return
        if current_phase is None:
            raise ValueError(f"task {task_id} appears before a phase")
        phase_id = current_phase[0]
        if not task_id.startswith(f"{phase_id}."):
            raise ValueError(f"task {task_id} does not belong to phase {phase_id}")
        fields = _parse_task_fields(task_lines, task_id)
        current_phase[2].append(ParsedTask(task_id, task_title, phase_id, fields))
        task_id = None
        task_title = ""
        task_lines = []

    for line in text.splitlines():
        phase_match = _PHASE_HEADING.match(line)
        if phase_match:
            finish_task()
            current_phase = (phase_match.group(1), phase_match.group(2).strip(), [])
            phases.append(current_phase)
            continue
        task_match = _TASK_HEADING.match(line)
        if task_match:
            finish_task()
            task_id = task_match.group(1)
            task_title = task_match.group(2).strip()
            continue
        if task_id is not None:
            task_lines.append(line)
    finish_task()

    phase_ids = tuple(item[0] for item in phases)
    if phase_ids != EXPECTED_PHASE_ORDER:
        raise ValueError(f"PLAN.md phase order drifted: expected {EXPECTED_PHASE_ORDER}, got {phase_ids}")
    parsed_phases = tuple(ParsedPhase(item[0], item[1], tuple(item[2])) for item in phases)
    task_ids = tuple(task.task_id for phase in parsed_phases for task in phase.tasks)
    if task_ids != EXPECTED_TASK_ORDER:
        raise ValueError(f"PLAN.md task order drifted: expected {EXPECTED_TASK_ORDER}, got {task_ids}")
    return ParsedPlan(hashlib.sha256(raw).hexdigest(), parsed_phases)


def build_dashboard_snapshot(repository_root: Path) -> dict[str, Any]:
    plan = parse_plan(repository_root / "PLAN.md")
    git_commit, git_dirty = _git_state(repository_root)
    decisions = _active_governance_decisions(
        repository_root / "00_governance/approvals", plan
    )
    governance = _governance_states(plan, decisions)
    evidence_root = repository_root / "04_outputs/artifacts/task-evidence"
    phase_views = []
    for order, phase in enumerate(plan.phases):
        tasks = []
        for task in phase.tasks:
            evidence = _task_evidence(
                evidence_root / task.task_id,
                task_id=task.task_id,
                plan_sha256=plan.sha256,
                repository_root=repository_root,
                current_git_commit=git_commit,
            )
            gate_ids = tuple(sorted(set(_GATE.findall(task.fields["Owner Gate"]))))
            task_gate_state = _task_governance_state(task, gate_ids, decisions)
            tasks.append(
                {
                    "task_id": task.task_id,
                    "title": task.title,
                    "goal": task.fields["Goal"],
                    "model": task.fields["Execution model"],
                    "objective": task.fields["Objective"],
                    "acceptance": task.fields["Acceptance"],
                    "owner_gate_ids": list(gate_ids),
                    "budget_stop": task.fields["Budget/stop"],
                    "rollback": task.fields["Rollback"],
                    "scientific_validity_risk": task.fields["Scientific validity risk"],
                    "dependencies": _dependency_ids(task.fields["Dependencies"], task.task_id),
                    "evidence_state": evidence["state"],
                    "evidence": evidence["record"],
                    "governance_state": task_gate_state,
                }
            )
        phase_views.append(
            {
                "phase_id": phase.phase_id,
                "title": phase.title,
                "order": order,
                "dependencies": _phase_dependencies(tasks, phase.phase_id),
                "evidence_state": _combined_evidence_state(tasks),
                "governance_state": _combined_task_governance_state(tasks),
                "tasks": tasks,
            }
        )
    return {
        "schema_version": "myis.dashboard-snapshot.v1",
        "program_id": "is1-research",
        "research_version": "0.1",
        "plan_sha256": plan.sha256,
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "phase_count": len(phase_views),
        "task_count": sum(len(item["tasks"]) for item in phase_views),
        "phases": phase_views,
        "gate_states": governance,
    }


def validate_decision_scope(plan: ParsedPlan, gate_id: str, scope: dict[str, Any]) -> None:
    phase_ids = {phase.phase_id for phase in plan.phases}
    task_to_phase = {task.task_id: phase.phase_id for phase in plan.phases for task in phase.tasks}
    task_to_gates = {
        task.task_id: set(_GATE.findall(task.fields["Owner Gate"]))
        for phase in plan.phases
        for task in phase.tasks
    }
    phase_to_gates = {
        phase.phase_id: set().union(*(task_to_gates[task.task_id] for task in phase.tasks))
        for phase in plan.phases
    }
    unknown_phases = set(scope["phase_ids"]) - phase_ids
    unknown_tasks = set(scope["task_ids"]) - set(task_to_phase)
    if unknown_phases or unknown_tasks:
        raise ValueError(
            f"Owner decision scope contains unknown IDs: phases={sorted(unknown_phases)}, "
            f"tasks={sorted(unknown_tasks)}"
        )
    for task_id in scope["task_ids"]:
        if scope["phase_ids"] and task_to_phase[task_id] not in scope["phase_ids"]:
            raise ValueError(f"task {task_id} is outside the named phase scope")
        if gate_id not in task_to_gates[task_id]:
            raise ValueError(f"task {task_id} is not governed by {gate_id}")
    for phase_id in scope["phase_ids"]:
        if gate_id not in phase_to_gates[phase_id]:
            raise ValueError(f"phase {phase_id} is not governed by {gate_id}")
    allowed_actions = {
        "G0": {"approve_implementation", "approve_documentation_migration", "approve_cleanup", "anchor_pdf_receipt_chain"},
        "G1": {"authorize_reproduction"},
        "G2": {"authorize_track_c_development"},
        "G3": {"freeze_track_c"},
        "G4": {"authorize_track_r_development"},
        "G5": {"authorize_harnessopt"},
        "G6": {"authorize_confirmation"},
        "G7": {"authorize_transfer"},
        "G8": {"authorize_publication"},
    }
    if scope["action"] not in allowed_actions[gate_id]:
        raise ValueError(f"action {scope['action']} is not valid for {gate_id}")
    target_only_actions = {"approve_cleanup", "anchor_pdf_receipt_chain", "authorize_transfer"}
    if scope["action"] == "authorize_transfer" and not scope["targets"]:
        raise ValueError("transfer authorization requires exact repository-relative targets")
    if not (scope["phase_ids"] or scope["task_ids"]):
        if scope["action"] not in target_only_actions or not scope["targets"]:
            raise ValueError("this Owner Gate action requires a governed phase or task scope")


def scope_sha256(scope: dict[str, Any]) -> str:
    encoded = json.dumps(scope, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _parse_task_fields(lines: list[str], task_id: str) -> dict[str, str]:
    fields: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        match = _FIELD.match(line)
        if match:
            current = match.group(1).strip()
            if current in fields:
                raise ValueError(f"task {task_id} repeats field {current}")
            fields[current] = [match.group(2).strip()]
        elif current is not None and line.strip():
            fields[current].append(line.strip())
    missing = [field for field in REQUIRED_TASK_FIELDS if field not in fields]
    if missing:
        raise ValueError(f"task {task_id} is missing required fields: {missing}")
    return {key: _clean_markdown(" ".join(value)) for key, value in fields.items()}


def _clean_markdown(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _git_state(root: Path) -> tuple[str, bool]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()
    dirty = bool(
        subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=normal"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    return commit, dirty


def _task_evidence(
    root: Path,
    *,
    task_id: str,
    plan_sha256: str,
    repository_root: Path,
    current_git_commit: str,
) -> dict[str, Any]:
    if not root.exists():
        return {"state": "not_recorded", "record": None}
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"task evidence root must be a regular directory: {task_id}")
    ledger = ImmutableJsonLedger(root, prior_field="prior_record_hash")
    chain = ledger.validate_chain()
    if chain["count"] == 0:
        return {"state": "not_recorded", "record": None}
    by_hash: dict[str, tuple[Path, TaskEvidenceRecord]] = {}
    for path, payload, digest in ledger.records():
        record = TaskEvidenceRecord.model_validate(payload)
        if path.stem != record.record_id or record.task_id != task_id:
            raise ValueError(f"task evidence identity mismatch: {path.name}")
        by_hash[digest] = (path, record)
    head_hash = chain["head"]
    if head_hash not in by_hash:
        raise ValueError(f"task evidence head is invalid: {task_id}")
    _, head = by_hash[head_hash]
    if head.supersedes_record_id is not None:
        prior_ids = {record.record_id for digest, (_, record) in by_hash.items() if digest != head_hash}
        if head.supersedes_record_id not in prior_ids:
            raise ValueError(f"task evidence supersedes an unknown record: {task_id}")
    if head.plan_sha256 != plan_sha256 or not _commit_is_ancestor(
        repository_root, head.git_commit, current_git_commit
    ):
        state = "stale"
    elif not head.acceptance_checks or any(check.status != "passed" for check in head.acceptance_checks):
        state = "incomplete"
    else:
        state = "complete"
    return {
        "state": state,
        "record": {
            "record_id": head.record_id,
            "record_sha256": head_hash,
            "git_commit": head.git_commit,
            "plan_sha256": head.plan_sha256,
            "acceptance_checks": [check.model_dump(mode="json") for check in head.acceptance_checks],
            "evidence_manifest_hashes": list(head.evidence_manifest_hashes),
        },
    }


def _commit_is_ancestor(repository_root: Path, source_commit: str, current_commit: str) -> bool:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", source_commit, current_commit],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        return True
    if completed.returncode == 1:
        return False
    raise ValueError("task evidence references an unknown or unreadable Git commit")


def validated_owner_gate_ledger(root: Path, plan: ParsedPlan) -> dict[str, Any]:
    ledger = ImmutableJsonLedger(root, prior_field="prior_record_hash")
    chain = ledger.validate_chain()
    if chain["count"] == 0:
        return {"chain": chain, "records": []}
    records = []
    for path, payload, digest in ledger.records():
        try:
            record = OwnerGateDecisionRecord.model_validate(payload)
            if path.stem != record.decision_id:
                raise ValueError("record filename does not match decision_id")
            scope = record.scope.model_dump(mode="json", exclude_none=True)
            validate_decision_scope(plan, record.gate_id, scope)
        except ValueError as error:
            raise ValueError(f"invalid Owner Gate record {path.name}: {error}") from error
        records.append({**record.model_dump(mode="json"), "record_sha256": digest})
    return {"chain": chain, "records": records}


def _active_governance_decisions(root: Path, plan: ParsedPlan) -> list[dict[str, Any]]:
    ledger_view = validated_owner_gate_ledger(root, plan)
    chain = ledger_view["chain"]
    if chain["count"] == 0:
        return []
    records = ledger_view["records"]
    by_hash = {item["record_sha256"]: item for item in records}
    sequence: list[dict[str, Any]] = []
    cursor = chain["head"]
    while cursor is not None:
        payload = by_hash[cursor]
        sequence.append(payload)
        cursor = payload.get("prior_record_hash")
    sequence.reverse()
    superseded_ids = {
        item["supersedes_decision_id"]
        for item in sequence
        if item.get("supersedes_decision_id") is not None
    }
    return [item for item in sequence if item.get("decision_id") not in superseded_ids]


def _governance_states(
    plan: ParsedPlan, decisions: list[dict[str, Any]]
) -> dict[str, str]:
    states: dict[str, str] = {}
    tasks = [task for phase in plan.phases for task in phase.tasks]
    for gate_id in (f"G{index}" for index in range(9)):
        governed_tasks = [
            task for task in tasks if gate_id in set(_GATE.findall(task.fields["Owner Gate"]))
        ]
        if governed_tasks:
            values = [_decision_status_for_task(gate_id, task, decisions) for task in governed_tasks]
            states[gate_id] = _aggregate_governance_values(values)
            continue
        records = [item for item in decisions if _record_gate_id(item) == gate_id]
        values = [str(item.get("status")) for item in records if item.get("status") in {"approved", "rejected", "deferred"}]
        states[gate_id] = _aggregate_governance_values(values)
    return states


def _task_governance_state(
    task: ParsedTask, gate_ids: tuple[str, ...], decisions: list[dict[str, Any]]
) -> str:
    if not gate_ids:
        return "not_required"
    values = [_decision_status_for_task(gate_id, task, decisions) for gate_id in gate_ids]
    return _combined_gate_state(values)


def _decision_status_for_task(
    gate_id: str, task: ParsedTask, decisions: list[dict[str, Any]]
) -> str:
    matching = []
    for item in decisions:
        if _record_gate_id(item) != gate_id:
            continue
        status = item.get("status")
        scope = item.get("scope")
        if status not in {"approved", "rejected", "deferred"} or not isinstance(scope, dict):
            continue
        task_ids = scope.get("task_ids")
        phase_ids = scope.get("phase_ids")
        if not isinstance(task_ids, list) or not isinstance(phase_ids, list):
            continue
        covered = task.task_id in task_ids if task_ids else task.phase_id in phase_ids
        if covered:
            matching.append(str(status))
    if not matching:
        return "pending"
    if len(set(matching)) > 1:
        return "conflict"
    return matching[-1]


def _record_gate_id(item: dict[str, Any]) -> str | None:
    match = re.search(r"G[0-8]$", str(item.get("gate_id", "")))
    return match.group(0) if match else None


def _aggregate_governance_values(values: list[str]) -> str:
    if not values or all(value == "pending" for value in values):
        return "pending"
    if "conflict" in values:
        return "conflict"
    decided = [value for value in values if value != "pending"]
    if len(set(decided)) > 1:
        return "mixed"
    if "pending" in values:
        return "partial"
    return decided[0]


def _combined_gate_state(values: list[str]) -> str:
    if all(value == "approved" for value in values):
        return "approved"
    if "conflict" in values or "mixed" in values:
        return "conflict"
    if "rejected" in values:
        return "rejected"
    if "deferred" in values:
        return "deferred"
    if "partial" in values:
        return "partial"
    return "pending"


def _dependency_ids(value: str, task_id: str) -> list[str]:
    identifiers = []
    for candidate in EXPECTED_TASK_ORDER:
        if candidate != task_id and re.search(rf"\b{re.escape(candidate)}\b", value):
            identifiers.append(candidate)
    for phase_id in EXPECTED_PHASE_ORDER:
        if phase_id != task_id.split(".", 1)[0] and re.search(rf"\b{phase_id}\b", value):
            identifiers.append(phase_id)
    return list(dict.fromkeys(identifiers))


def _phase_dependencies(tasks: list[dict[str, Any]], phase_id: str) -> list[str]:
    dependencies = []
    for task in tasks:
        for dependency in task["dependencies"]:
            dependency_phase = dependency.split(".", 1)[0]
            if dependency_phase != phase_id and dependency_phase not in dependencies:
                dependencies.append(dependency_phase)
    return dependencies


def _combined_evidence_state(tasks: list[dict[str, Any]]) -> str:
    states = [task["evidence_state"] for task in tasks]
    if all(state == "complete" for state in states):
        return "complete"
    if "stale" in states:
        return "stale"
    if all(state == "not_recorded" for state in states):
        return "not_recorded"
    return "incomplete"


def _combined_task_governance_state(tasks: list[dict[str, Any]]) -> str:
    states = [task["governance_state"] for task in tasks if task["governance_state"] != "not_required"]
    if not states:
        return "not_required"
    if all(state == "approved" for state in states):
        return "approved"
    if "rejected" in states:
        return "rejected"
    if "deferred" in states:
        return "deferred"
    return "pending"
