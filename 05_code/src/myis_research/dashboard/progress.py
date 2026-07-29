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
from .projections import load_linear_projection
from .readiness import load_f1_g1_readiness
from ..session_capsules import latest_valid_session


EXPECTED_PHASE_ORDER = ("F0", "F1", "D0", "C0", "C1", "CF", "S0", "S1", "SF", "CT", "Q", "PC", "PS")
EXPECTED_TASK_ORDER = (
    "F0.1",
    "F0.2",
    "F0.3",
    "F1.1",
    "D0.1",
    "D0.2",
    "C0.1",
    "C1.1",
    "C1.2",
    "CF.1",
    "S0.1",
    "S0.2",
    "S1.1",
    "S1.2",
    "S1.3",
    "SF.1",
    "CT.1",
    "Q.1",
    "Q.2",
    "Q.3",
    "PC.1",
    "PS.1",
)
REQUIRED_TASK_FIELDS = (
    "Goal",
    "Inputs",
    "Outputs",
    "Tests",
    "Acceptance",
    "Owner Gate",
    "Budget/stop",
    "Rollback",
    "Risk",
    "Evidence",
    "Dependencies",
)

PHASE_GROUPS = (
    {"group_id": "foundation", "title_en": "Foundation", "phase_ids": ("F0", "F1", "D0")},
    {"group_id": "track-c", "title_en": "Track C", "phase_ids": ("C0", "C1", "CF")},
    {"group_id": "track-s", "title_en": "Track S", "phase_ids": ("S0", "S1", "SF")},
    {"group_id": "evaluation-publication", "title_en": "Evaluation & publication", "phase_ids": ("Q", "PC", "PS")},
    {"group_id": "transfer", "title_en": "External transfer", "phase_ids": ("CT",)},
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
    linear = load_linear_projection(repository_root, plan)
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
            linear_task = linear["tasks"][task.task_id]
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
                    "phase_id": phase.phase_id,
                    "title": task.title,
                    "goal": task.fields["Goal"],
                    "inputs": task.fields["Inputs"],
                    "outputs": task.fields["Outputs"],
                    "tests": task.fields["Tests"],
                    "acceptance": task.fields["Acceptance"],
                    "owner_gate_ids": list(gate_ids),
                    "budget_stop": task.fields["Budget/stop"],
                    "rollback": task.fields["Rollback"],
                    "risk": task.fields["Risk"],
                    "evidence_contract": task.fields["Evidence"],
                    "dependencies": _dependency_ids(task.fields["Dependencies"], task.task_id),
                    "dependency_annotations": _dependency_annotations(task.fields["Dependencies"], task.task_id),
                    "linear_issue_id": linear_task["issue_id"],
                    "linear_status": linear_task["status"],
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
    _add_project_progress(phase_views)
    plan_graph = _build_plan_graph(plan, linear)
    gate_readiness = _gate_readiness(phase_views, governance)
    owner_focus = _owner_focus(phase_views, governance, git_dirty, gate_readiness)
    readiness = _readiness_projection(phase_views, governance)
    f1_g1_preparation = load_f1_g1_readiness(repository_root)
    completed_task_count = sum(
        task["project_state"] == "complete"
        for phase in phase_views
        for task in phase["tasks"]
    )
    project_state_counts: dict[str, int] = {}
    for phase in phase_views:
        for task in phase["tasks"]:
            state = task["project_state"]
            project_state_counts[state] = project_state_counts.get(state, 0) + 1
    return {
        "schema_version": "myis.dashboard-snapshot.v1",
        "program_id": "myis-research",
        "display_name": "myIS Research",
        "protocol_version": "1.0",
        "research_version": "0.1",
        "plan_sha256": plan.sha256,
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "phase_count": len(phase_views),
        "task_count": sum(len(item["tasks"]) for item in phase_views),
        "progress": {
            "completed_task_count": completed_task_count,
            "completion_percent": round(
                completed_task_count * 100 / sum(len(item["tasks"]) for item in phase_views)
            ),
            "state_counts": dict(sorted(project_state_counts.items())),
            "completion_authority": "canonical_task_evidence",
            "tracking_projection": "linear",
        },
        "phases": phase_views,
        "gate_states": governance,
        "gate_readiness": gate_readiness,
        "linear": {
            "source_sha256": linear["source_sha256"],
            "project": linear["project"],
            "task_count": len(linear["tasks"]),
        },
        "plan_graph": plan_graph,
        "owner_focus": owner_focus,
        "readiness": readiness,
        "f1_g1_preparation": f1_g1_preparation,
        "projection_revision": hashlib.sha256(
            json.dumps(
                {
                    "plan": plan.sha256,
                    "linear": linear["source_sha256"],
                    "git": git_commit,
                    "dirty": git_dirty,
                    "progress": project_state_counts,
                    "gates": governance,
                    "f1_g1_proposal": f1_g1_preparation.get("proposal_sha256", "not_prepared"),
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
    }


def build_owner_inbox(repository_root: Path) -> dict[str, Any]:
    """Return a small, owner-facing work queue derived from the canonical snapshot."""

    snapshot = build_dashboard_snapshot(repository_root)
    focus = snapshot["owner_focus"]
    tasks = [task for phase in snapshot["phases"] for task in phase["tasks"]]
    task = next((item for item in tasks if item["task_id"] == focus.get("next_task_id")), None)
    gate_id = focus.get("next_gate_id")
    gate = snapshot["gate_readiness"].get(gate_id or "", {})
    closeout = latest_valid_session(
        repository_root,
        phase_id=focus.get("current_phase_id"),
        task_id=task.get("task_id") if task is not None else None,
        gate_id=gate_id,
    )
    v2_closeout = closeout if closeout and closeout.get("capsule_schema_version") == "myis.research-session.v2" else None

    if focus["mode"] == "decision":
        headline_th = "มีการตัดสินใจของ Owner ที่พร้อมให้ตรวจ"
        action_th = f"ตรวจและตัดสินใจ {gate_id}"
    elif task is not None:
        headline_th = "ติดตามงานถัดไปก่อนเริ่มขั้นตอนใหม่"
        action_th = "เปิดรายละเอียดงาน"
    else:
        headline_th = "ยังไม่มีงานที่ต้องดำเนินการ"
        action_th = "ตรวจแผนงาน"

    resources = task["inputs"] if task is not None else "ไม่มีทรัพยากรเพิ่มเติมในตอนนี้"
    if v2_closeout and v2_closeout.get("next_resources", {}).get("status") == "required":
        resources = "; ".join(item["description_th"] for item in v2_closeout["next_resources"]["items"])
    owner_checklist = [
        "ดูสถานะงานและหลักฐานที่ผ่านการตรวจสอบแล้ว",
        "ตรวจขอบเขต Gate และสิ่งที่จะยังถูกล็อก",
        "อนุมัติ เลื่อน หรือปฏิเสธเฉพาะเมื่อ Git อยู่ในสถานะสะอาด",
    ]
    if v2_closeout:
        owner_checklist = [item["action_th"] for item in v2_closeout.get("owner_actions") or []]
    return {
        "schema_version": "myis.owner-inbox.v1",
        "headline_th": headline_th,
        "headline_en": focus["headline_en"],
        "action_th": action_th,
        "mode": focus["mode"],
        "phase_id": focus.get("current_phase_id"),
        "task": None if task is None else {
            key: task[key] for key in ("task_id", "phase_id", "title", "project_state", "goal", "inputs", "tests", "evidence_state")
        },
        "gate": {
            "gate_id": gate_id,
            "state": snapshot["gate_states"].get(gate_id or "", "not_required"),
            "ready": bool(gate.get("ready")),
            "waiting_for": gate.get("waiting_for", []),
            "reason_th": gate.get("reason_th", "ไม่มี Gate ที่ต้องตัดสินใจ"),
        },
        "owner_checklist": owner_checklist,
        "next_phase_resources": resources,
        "implementation_closeout": v2_closeout,
        "scientific_results": "NOT_RUN",
        "scientific_results_note_th": "Dashboard นี้ยังไม่มีผลการทดลองเชิงวิทยาศาสตร์ และไม่แสดงข้อมูล protected.",
    }


def _readiness_projection(
    phases: list[dict[str, Any]], governance: dict[str, str]
) -> dict[str, str]:
    """Project the current pre-F1 boundary without creating a new authority."""

    phase_states = {phase["phase_id"]: phase["project_state"] for phase in phases}
    f0_closed = phase_states.get("F0") == "complete" and governance.get("G0") == "approved"
    f1_state = phase_states.get("F1", "review_required")
    g1_state = governance.get("G1", "review_required")
    preparation_only = f0_closed and f1_state == "waiting_gate" and g1_state == "pending"
    return {
        "f0": "closed" if f0_closed else phase_states.get("F0", "review_required"),
        "g0": governance.get("G0", "review_required"),
        "f1": f1_state,
        "g1": g1_state,
        "project": "f1_g1_preparation_only" if preparation_only else "review_required",
        "project_label": "F1/G1 preparation only" if preparation_only else "Readiness requires review",
    }


def _build_plan_graph(plan: ParsedPlan, linear: dict[str, Any]) -> dict[str, Any]:
    task_to_phase = {
        task.task_id: phase.phase_id for phase in plan.phases for task in phase.tasks
    }
    phase_edges: set[tuple[str, str]] = set()
    for edge in linear["dependencies"]:
        from_phase = task_to_phase[edge["from_task"]]
        to_phase = task_to_phase[edge["to_task"]]
        if from_phase != to_phase:
            phase_edges.add((from_phase, to_phase))
    annotations = []
    for phase in plan.phases:
        for task in phase.tasks:
            parsed = _dependency_annotations(task.fields["Dependencies"], task.task_id)
            if parsed["parallel_with"] or parsed["independent_of"]:
                annotations.append({"task_id": task.task_id, **parsed})
    return {
        "groups": [
            {"group_id": item["group_id"], "title_en": item["title_en"], "phase_ids": list(item["phase_ids"])}
            for item in PHASE_GROUPS
        ],
        "phase_edges": [
            {"from_phase": source, "to_phase": target, "relation": "blocks"}
            for source, target in sorted(phase_edges, key=lambda item: (item[0], item[1]))
        ],
        "task_edges": [
            {
                "from_task": edge["from_task"],
                "to_task": edge["to_task"],
                "relation": edge["relation"],
            }
            for edge in linear["dependencies"]
        ],
        "annotations": annotations,
        "source_bindings": {
            "canonical_plan_sha256": plan.sha256,
            "linear_projection_sha256": linear["source_sha256"],
            "authority": "PLAN.md",
        },
    }


def _gate_readiness(
    phases: list[dict[str, Any]], governance: dict[str, str]
) -> dict[str, dict[str, Any]]:
    """Gate readiness is based on work before a Gate, never on work it authorizes."""

    tasks = [task for phase in phases for task in phase["tasks"]]
    task_by_id = {task["task_id"]: task for task in tasks}
    phase_by_id = {phase["phase_id"]: phase for phase in phases}
    readiness: dict[str, dict[str, Any]] = {}
    gate_order = tuple(f"G{index}" for index in range(9))
    for gate_index, gate_id in enumerate(gate_order):
        governed = [task for task in tasks if gate_id in task["owner_gate_ids"]]
        governed_ids = {task["task_id"] for task in governed}
        governed_phases = {task["phase_id"] for task in governed}
        prerequisites = sorted(
            {
                dependency
                for task in governed
                for dependency in task["dependencies"]
                if dependency not in governed_ids and dependency not in governed_phases
            }
        )
        waiting_for = [
            dependency
            for dependency in prerequisites
            if (
                task_by_id[dependency]["evidence_state"] != "complete"
                if dependency in task_by_id
                else phase_by_id.get(dependency, {}).get("evidence_state") != "complete"
            )
        ]
        prior_gates_pending = [
            prior_gate
            for prior_gate in gate_order[:gate_index]
            if governance.get(prior_gate) != "approved"
        ]
        ready = (
            bool(governed)
            and not waiting_for
            and not prior_gates_pending
            and governance.get(gate_id) != "approved"
        )
        readiness[gate_id] = {
            "ready": ready,
            "prerequisites": prerequisites,
            "waiting_for": waiting_for,
            "prior_gates_pending": prior_gates_pending,
            "reason_th": (
                "หลักฐานของงานก่อนหน้าเพียงพอสำหรับการตรวจ Gate"
                if ready
                else "รอหลักฐานของงานก่อนหน้า: " + ", ".join(waiting_for)
                if waiting_for
                else "รอการอนุมัติ Gate ก่อนหน้า: " + ", ".join(prior_gates_pending)
                if prior_gates_pending
                else "Gate นี้ไม่มีงานที่ต้องเปิดเพิ่มเติม"
            ),
        }
    return readiness


def _owner_focus(
    phases: list[dict[str, Any]],
    governance: dict[str, str],
    git_dirty: bool,
    gate_readiness: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    tasks = [task for phase in phases for task in phase["tasks"]]
    task_by_id = {task["task_id"]: task for task in tasks}
    gate_order = [f"G{index}" for index in range(9)]
    next_gate = next(
        (gate_id for gate_id in gate_order if governance.get(gate_id) not in {"approved"}),
        None,
    )
    if next_gate and gate_readiness.get(next_gate, {}).get("ready") and not git_dirty:
        governed = [task for task in tasks if next_gate in task["owner_gate_ids"]]
        phase_id = governed[0]["phase_id"] if governed else None
        return {
            "mode": "decision",
            "current_phase_id": phase_id,
            "next_task_id": governed[0]["task_id"] if governed else None,
            "next_gate_id": next_gate,
            "blocker_codes": [],
            "headline_en": f"Review {next_gate} before the next phase",
            "detail_th": "ตรวจ Gate ที่พร้อมอนุมัติก่อนเริ่มงานถัดไป",
        }
    priority = (
        "verification_needed",
        "blocked_gate",
        "waiting_gate",
        "in_progress",
        "ready",
        "waiting_dependency",
    )
    selected = next((task for state in priority for task in tasks if task["project_state"] == state), None)
    if selected is None:
        return {
            "mode": "complete",
            "current_phase_id": None,
            "next_task_id": None,
            "next_gate_id": next_gate,
            "blocker_codes": [],
            "headline_en": "All recorded tasks are complete",
            "detail_th": "งานที่มีหลักฐานครบแล้วทั้งหมด",
        }
    blocker_codes = []
    if selected["unmet_dependencies"]:
        blocker_codes.append("dependency")
    if selected["project_state"] in {"blocked_gate", "waiting_gate"}:
        blocker_codes.append("gate")
    if selected["project_state"] == "verification_needed":
        blocker_codes.append("evidence")
    headline = {
        "verification_needed": f"Verify evidence for {selected['task_id']}",
        "blocked_gate": f"Resolve the Gate blocker for {selected['task_id']}",
        "waiting_gate": f"Wait for Gate approval before {selected['task_id']}",
        "in_progress": f"Continue {selected['task_id']}",
        "ready": f"Start {selected['task_id']}",
        "waiting_dependency": f"Complete dependencies before {selected['task_id']}",
    }[selected["project_state"]]
    return {
        "mode": "work",
        "current_phase_id": selected["phase_id"],
        "next_task_id": selected["task_id"],
        "next_gate_id": next_gate,
        "blocker_codes": blocker_codes,
        "headline_en": headline,
        "detail_th": "ดูงานถัดไปและเหตุผลที่ยังเริ่มไม่ได้",
    }


def _add_project_progress(phases: list[dict[str, Any]]) -> None:
    """Add human-readable progress without allowing Linear to claim completion."""

    tasks = {task["task_id"]: task for phase in phases for task in phase["tasks"]}
    phase_complete = {
        phase["phase_id"]: all(task["evidence_state"] == "complete" for task in phase["tasks"])
        for phase in phases
    }
    for phase in phases:
        for task in phase["tasks"]:
            unmet = []
            for dependency in task["dependencies"]:
                if dependency in tasks:
                    complete = tasks[dependency]["evidence_state"] == "complete"
                else:
                    complete = phase_complete.get(dependency, False)
                if not complete:
                    unmet.append(dependency)
            task["unmet_dependencies"] = unmet
            task["project_state"] = _task_project_state(task, unmet)

        completed = sum(task["project_state"] == "complete" for task in phase["tasks"])
        phase["completed_task_count"] = completed
        phase["completion_percent"] = round(completed * 100 / len(phase["tasks"]))
        phase["project_state"] = _phase_project_state(phase["tasks"])


def _task_project_state(task: dict[str, Any], unmet_dependencies: list[str]) -> str:
    if task["evidence_state"] == "complete":
        return "complete"
    linear_status = str(task["linear_status"]).strip().lower().replace("_", " ")
    if task["evidence_state"] in {"stale", "incomplete"} or linear_status in {
        "done",
        "completed",
        "canceled",
        "cancelled",
    }:
        return "verification_needed"
    if linear_status in {"in progress", "started"}:
        return "in_progress"
    if unmet_dependencies:
        return "waiting_dependency"
    governance_state = task["governance_state"]
    if governance_state in {"rejected", "deferred", "conflict"}:
        return "blocked_gate"
    if governance_state not in {"approved", "not_required"}:
        return "waiting_gate"
    return "ready"


def _phase_project_state(tasks: list[dict[str, Any]]) -> str:
    states = [task["project_state"] for task in tasks]
    if all(state == "complete" for state in states):
        return "complete"
    if any(state in {"in_progress", "verification_needed"} for state in states):
        return "in_progress"
    if "complete" in states:
        return "in_progress"
    for state in ("blocked_gate", "waiting_gate", "ready", "waiting_dependency"):
        if state in states:
            return state
    return "waiting_dependency"


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
        "G4": {"authorize_track_s"},
        "G5": {"freeze_track_s"},
        "G6": {"authorize_joint_confirmation"},
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
    ledger = ImmutableJsonLedger(
        root,
        prior_field="prior_record_hash",
        record_id_field="record_id",
        supersedes_field="supersedes_record_id",
    )
    chain = ledger.validate_chain()
    if chain["count"] == 0:
        return {"state": "not_recorded", "record": None}
    by_hash: dict[str, tuple[Path, TaskEvidenceRecord]] = {}
    for path, payload, digest in ledger.records():
        record = TaskEvidenceRecord.model_validate(payload)
        if path.stem != record.record_id or record.task_id != task_id:
            raise ValueError(f"task evidence identity mismatch: {path.name}")
        by_hash[digest] = (path, record)
    all_record_ids = {record.record_id for _, record in by_hash.values()}
    by_id = {record.record_id: digest for digest, (_, record) in by_hash.items()}
    superseded_ids = {
        record.supersedes_record_id
        for _, record in by_hash.values()
        if record.supersedes_record_id is not None
        and record.prior_record_hash != by_id.get(record.supersedes_record_id)
    }
    if superseded_ids:
        by_hash = {
            digest: item for digest, item in by_hash.items() if item[1].record_id not in superseded_ids
        }
    head_hash = chain["head"]
    if head_hash not in by_hash:
        raise ValueError(f"task evidence head is invalid: {task_id}")
    _, head = by_hash[head_hash]
    if head.supersedes_record_id is not None:
        if head.supersedes_record_id not in all_record_ids:
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
    clause = value.split(";", 1)[0]
    identifiers: list[str] = []
    for phase_id in EXPECTED_PHASE_ORDER:
        if phase_id != task_id.split(".", 1)[0] and re.search(rf"\b{re.escape(phase_id)}\b(?!\.\d)", clause):
            identifiers.append(phase_id)
    for match in re.finditer(r"\b([A-Z][A-Z0-9]*)\.(\d+)-\1\.(\d+)\b", clause):
        phase_id, start, end = match.group(1), int(match.group(2)), int(match.group(3))
        for number in range(min(start, end), max(start, end) + 1):
            candidate = f"{phase_id}.{number}"
            if candidate in EXPECTED_TASK_ORDER and candidate != task_id:
                identifiers.append(candidate)
    for candidate in EXPECTED_TASK_ORDER:
        if candidate != task_id and re.search(rf"\b{re.escape(candidate)}\b", clause):
            identifiers.append(candidate)
    return list(dict.fromkeys(identifiers))


def _dependency_annotations(value: str, task_id: str) -> dict[str, list[str]]:
    suffix = value.split(";", 1)[1] if ";" in value else ""
    parallel_with: list[str] = []
    independent_of: list[str] = []
    if "parallel with" in suffix.lower():
        parallel_with = _referenced_ids(suffix, task_id, include_phases=False)
    if "independent of" in suffix.lower():
        independent_of = _referenced_ids(suffix, task_id, include_phases=True)
    return {
        "parallel_with": parallel_with,
        "independent_of": independent_of,
    }


def _referenced_ids(value: str, task_id: str, *, include_phases: bool) -> list[str]:
    candidates = list(EXPECTED_TASK_ORDER)
    if include_phases:
        candidates += list(EXPECTED_PHASE_ORDER)
    return [
        candidate
        for candidate in candidates
        if candidate != task_id and re.search(rf"\b{re.escape(candidate)}\b", value)
    ]


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
