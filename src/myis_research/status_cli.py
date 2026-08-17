"""Render the Owner-facing project status from canonical repository sources."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

import yaml

from .projections.read_model import build_read_model


def _latest(root: Path, directory: str, pattern: str) -> str:
    paths = sorted((root / directory).glob(pattern))
    return paths[-1].relative_to(root).as_posix() if paths else "NONE"


def _active_goal(root: Path) -> str:
    candidates: list[Path] = []
    pending_successor_goals: list[Path] = []
    for path in (root / "docs/goal").glob("*.md"):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        data = yaml.safe_load(text.split("---", 2)[1])
        if not isinstance(data, Mapping):
            continue
        lifecycle = data.get("lifecycle")
        ready_measured_goal = (
            lifecycle == "READY"
            and data.get("status") == "READY_FOR_MEASURED_EXECUTION"
            and data.get("scientific_authority") is True
            and data.get("measured_a2_authorized") is True
        )
        if lifecycle == "ACTIVE" or ready_measured_goal:
            candidates.append(path)
        if lifecycle == "PENDING" and data.get("status") == "PENDING_FRESH_A3_ADMISSION":
            pending_successor_goals.append(path)
    if pending_successor_goals:
        return (
            sorted(pending_successor_goals)[-1]
            .relative_to(root)
            .as_posix()
        )
    return sorted(candidates)[-1].relative_to(root).as_posix() if candidates else "NONE"


def _projection_status(root: Path, model: Mapping[str, Any]) -> dict[str, str]:
    expected_revision = model["read_model_revision"]
    try:
        stored = json.loads(
            (root / "projections/read-model/read-model.v2.json").read_text(
                encoding="utf-8"
            )
        )
        read_model_current = stored.get("read_model_revision") == expected_revision
    except (OSError, UnicodeError, json.JSONDecodeError):
        read_model_current = False
    obsidian_ok = read_model_current and (root / "obsidian_report/HOME.md").is_file()
    try:
        archive = json.loads(
            (root / "mlflow/generated/archive-index.v2.json").read_text(
                encoding="utf-8"
            )
        )
        mlflow_ok = archive.get("read_model_revision") == expected_revision
    except (OSError, UnicodeError, json.JSONDecodeError):
        mlflow_ok = False
    return {
        "obsidian": "OK" if obsidian_ok else "PENDING",
        "mlflow": "OK" if mlflow_ok else "PENDING",
    }


def _gpu_state(readiness: Mapping[str, Any]) -> dict[str, str]:
    """Render only provider-safe lifecycle data present in the read model."""
    explicit_decision = readiness.get("gpu_decision")
    if explicit_decision == "OWNER_ACTION_DESTROY":
        return {
            "decision": "OWNER_ACTION_DESTROY",
            "reason": str(
                readiness.get(
                    "gpu_decision_reason",
                    "no named authorized workload remains after safe return",
                )
            ),
            "instance": str(readiness.get("provider_instance_id", "UNKNOWN")),
            "hourly_rate_usd": str(readiness.get("hourly_rate_usd", "UNKNOWN")),
            "accrued_gpu_cost_usd": str(
                readiness.get("whole_workload_total_usd", "UNKNOWN")
            ),
            "keep_destroy_condition": str(
                readiness.get("gpu_keep_until", "DESTROY_AFTER_OWNER_CONFIRMATION")
            ),
        }
    provider = readiness.get("provider_admission_receipt", {})
    provider = provider if isinstance(provider, Mapping) else {}
    instance = provider.get("instance_id")
    if instance:
        measured_active = bool(readiness.get("measured_a2_started"))
        return {
            "decision": "GPU_ACTIVE" if measured_active else "UNKNOWN",
            "reason": (
                "canonical readiness marks measured execution active"
                if measured_active
                else "canonical staged provider receipt is present; measured A2 remains locked"
            ),
            "instance": str(instance),
            "hourly_rate_usd": str(provider.get("hourly_rate_usd", "UNKNOWN")),
            "accrued_gpu_cost_usd": str(
                provider.get("whole_workload_total_usd", "UNKNOWN")
            ),
            "keep_destroy_condition": str(
                readiness.get("gpu_keep_until", "UNKNOWN")
            ),
        }
    return {
        "decision": str(readiness.get("gpu_decision", "UNKNOWN")),
        "reason": str(
            readiness.get(
                "gpu_decision_reason",
                "canonical provider admission evidence is not present",
            )
        ),
        "instance": "NONE",
        "hourly_rate_usd": "UNKNOWN",
        "accrued_gpu_cost_usd": "UNKNOWN",
        "keep_destroy_condition": "NOT_APPLICABLE",
    }


def _routing(readiness: Mapping[str, Any], active_goal: str) -> dict[str, str]:
    route = str(readiness.get("current_route", ""))
    status = str(readiness.get("current_status", readiness.get("status", "")))
    if "PENDING_HASH_BOUND_TRAIN_250_INPUT" in status:
        return {
            "recommended_next_session": "AP",
            "recommended_model": "GPT-5.6 Sol High",
            "reasoning_effort": "High",
            "reason": "A3 is prepared but cannot spend or contact a provider until the hash-bound Train-250 package is available",
            "command_before_prompt": "NONE",
            "copy_paste_prompt": "NONE",
            "owner_decision_required": "NONE",
        }
    if active_goal != "NONE":
        return {
            "recommended_next_session": "LO",
            "recommended_model": "GPT-5.6 Terra XHigh",
            "reasoning_effort": "XHigh",
            "reason": "an ACTIVE goal is executable under the canonical lifecycle contract",
            "command_before_prompt": "NONE",
            "copy_paste_prompt": f"/goal อ่าน {active_goal} แล้วทำงานตามขั้นตอนทั้งหมด",
            "owner_decision_required": "NONE",
        }
    if route == "IM" or "IMPLEMENTATION_BLOCKED" in status:
        return {
            "recommended_next_session": "IM",
            "recommended_model": "GPT-5.6 Sol Medium",
            "reasoning_effort": "Medium",
            "reason": "canonical readiness identifies a launch-critical implementation blocker",
            "command_before_prompt": "NONE",
            "copy_paste_prompt": "ตอนนี้คุณคือ IM ตาม AGENTS.md; อ่าน PLAN.md และ latest A2 implementation handoff แล้วแก้เฉพาะ blocker",
            "owner_decision_required": "NONE",
        }
    if route == "LO":
        return {
            "recommended_next_session": "LO",
            "recommended_model": "GPT-5.6 Terra XHigh",
            "reasoning_effort": "XHigh",
            "reason": "canonical readiness marks an executable long-run route",
            "command_before_prompt": "NONE",
            "copy_paste_prompt": "/goal อ่าน docs/goal/<PHASE>_goal_<INDEX>.md แล้วทำงานตามขั้นตอนทั้งหมด",
            "owner_decision_required": "NONE",
        }
    return {
        "recommended_next_session": "AP",
        "recommended_model": "GPT-5.6 Sol High",
        "reasoning_effort": "High",
        "reason": "canonical readiness requires a fresh AP admission/staging judgment",
        "command_before_prompt": "NONE",
        "copy_paste_prompt": "ตอนนี้คุณคือ AP ตาม AGENTS.md; อ่าน PLAN.md และ latest A2 implementation handoff, ตรวจ budget/GPU lifecycle แล้วเลือก ONE route: IM หรือ LO",
        "owner_decision_required": "NONE",
    }


def build_owner_status(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    model = build_read_model(root)
    project = model["project"]
    armindex = model["armindex"]
    readiness = armindex.get("a2_execution_readiness", {})
    readiness = readiness if isinstance(readiness, Mapping) else {}
    closeout = armindex.get("a2_goal004_closeout", {})
    if isinstance(closeout, Mapping) and closeout.get("validated") is True:
        route = closeout.get("a3_route", {})
        route = route if isinstance(route, Mapping) else {}
        accounting = closeout.get("accounting", {})
        accounting = accounting if isinstance(accounting, Mapping) else {}
        budget = closeout.get("budget", {})
        budget = budget if isinstance(budget, Mapping) else {}
        readiness = {
            **readiness,
            "status": "A2_GOAL004_MEASURED_CLOSEOUT",
            "current_status": str(route.get("status", "PENDING_HASH_BOUND_TRAIN_250_INPUT")),
            "current_route": "AP",
            "evidence_class": closeout.get("evidence_class", "measured_development_aggregate"),
            "scientific_authority": closeout.get("scientific_authority", True),
            "claim_boundary": closeout.get("claim_boundary", "aggregate_development_only"),
            "phase_ceiling_usd": 35,
            "task_run_ceiling_usd": 35,
            "a2_spent_accrued_usd": budget.get("whole_workload_total_usd", "UNKNOWN"),
            "campaign_ceiling_usd": 180,
            "remaining_campaign_headroom_usd": "79.31170133333334052",
            "estimated_next_action_cost_usd": "UNKNOWN_DO_NOT_SPEND",
            "budget_status": "PENDING_FRESH_A3_ADMISSION",
            "gpu_decision": "OWNER_ACTION_DESTROY",
            "gpu_decision_reason": "A2 safe return and worker reaping passed; no named authorized A3 workload remains while Train-250 input is missing",
            "provider_instance_id": readiness.get("provider_admission_receipt", {}).get("instance_id", "47790578")
            if isinstance(readiness.get("provider_admission_receipt"), Mapping)
            else "47790578",
            "whole_workload_total_usd": budget.get("whole_workload_total_usd", "UNKNOWN"),
            "gpu_keep_until": "DESTROY_AFTER_OWNER_CONFIRMATION",
            "next_authorized_action": route.get(
                "next_authorized_action",
                "LOCATE_OR_OBTAIN_AN_OWNER_AUTHORIZED_HASH_BOUND_TRAIN_250_QUERY_CORPUS_AND_EVALUATOR_PACKAGE_BEFORE_A3_ADMISSION",
            ),
            "counters": {
                "candidate_evaluations": accounting.get("measured_candidate_count", 0),
                "measured_a2_runs": 1,
                "provider_admissions": 1,
                "provider_execution_adoptions": 1,
            },
        }
    counters = readiness.get("counters", {})
    counters = counters if isinstance(counters, Mapping) else {}
    active_goal = _active_goal(root)
    return {
        "project": {
            "phase": project.get("current_phase", "UNKNOWN"),
            "task": f"{project.get('current_task', 'UNKNOWN')} / {project.get('current_substage', 'UNKNOWN')}",
            "status_th": f"สถานะปัจจุบันจาก canonical read model: {project.get('current_status', 'UNKNOWN')}",
            "evidence_class": readiness.get("evidence_class", "UNKNOWN"),
            "scientific_authority": readiness.get("scientific_authority", "UNKNOWN"),
            "supported_claim_boundary": readiness.get("claim_boundary", "UNKNOWN"),
        },
        "budget": {
            "phase_ceiling_usd": readiness.get("phase_ceiling_usd", "UNKNOWN"),
            "task_run_ceiling_usd": readiness.get("task_run_ceiling_usd", "UNKNOWN"),
            "spent_accrued_usd": readiness.get("a2_spent_accrued_usd", "UNKNOWN"),
            "campaign_ceiling_usd": readiness.get("campaign_ceiling_usd", "UNKNOWN"),
            "remaining_headroom_usd": readiness.get("remaining_campaign_headroom_usd", "UNKNOWN"),
            "estimated_next_action_cost_usd": readiness.get("estimated_next_action_cost_usd", "UNKNOWN"),
            "next_phase_ceiling_usd": readiness.get("next_phase_ceiling_usd", "NOT_BOUND"),
            "status": readiness.get("budget_status", "UNKNOWN_DO_NOT_SPEND"),
        },
        "gpu_vast": _gpu_state(readiness),
        "handoffs": {
            "latest_ap": _latest(root, "docs/audit", "A2_PER_ARM_AUTOINDEX_audit_[0-9][0-9][0-9].md"),
            "latest_im": _latest(root, "docs/implementation", "A2_PER_ARM_AUTOINDEX_im_[0-9][0-9][0-9]_[0-9][0-9][0-9].md"),
            "latest_lo": _latest(root, "docs/long_run", "A2_PER_ARM_AUTOINDEX_lo_[0-9][0-9][0-9]_[0-9][0-9][0-9].md"),
            "active_goal": active_goal,
        },
        "projections": _projection_status(root, model),
        "routing": _routing(readiness, active_goal),
        "boundaries": {
            "candidate_evaluations": counters.get("candidate_evaluations", "UNKNOWN"),
            "measured_a2_runs": counters.get("measured_a2_runs", "UNKNOWN"),
            "provider_admissions": counters.get("provider_admissions", "UNKNOWN"),
            "provider_execution_adoptions": counters.get("provider_execution_adoptions", "UNKNOWN"),
            "selection": "CLOSED",
            "final": "CLOSED",
        },
    }


def _value(value: Any, *, money: bool = False) -> str:
    if value is None:
        return "NOT_BOUND"
    if money and isinstance(value, (int, float)):
        return f"USD {value:.6f}".rstrip("0").rstrip(".")
    return str(value)


def render_owner_status(status: Mapping[str, Any]) -> str:
    project, budget = status["project"], status["budget"]
    gpu, handoffs = status["gpu_vast"], status["handoffs"]
    projections, routing = status["projections"], status["routing"]
    return "\n".join([
        "สถานะโครงการ", f"Phase: {project['phase']}", f"Task/Sub-stage: {project['task']}",
        f"สถานะสั้น ๆ: {project['status_th']}", f"Evidence class: {project['evidence_class']}",
        f"Scientific authority: {project['scientific_authority']}", f"Supported claim boundary: {project['supported_claim_boundary']}", "",
        "Budget:", f"Phase ceiling: {_value(budget['phase_ceiling_usd'], money=True)}", f"Current Task/Run ceiling: {_value(budget['task_run_ceiling_usd'], money=True)}",
        f"Spent/Accrued: {_value(budget['spent_accrued_usd'], money=True)}", f"Campaign ceiling: {_value(budget['campaign_ceiling_usd'], money=True)}",
        f"Remaining headroom: {_value(budget['remaining_headroom_usd'], money=True)}", f"Estimated next-action cost: {_value(budget['estimated_next_action_cost_usd'], money=True)}",
        f"Next Phase ceiling: {_value(budget['next_phase_ceiling_usd'], money=True)}", f"Budget status: {budget['status']}", "",
        "GPU / Vast:", f"GPU decision: {gpu['decision']}", f"Reason: {gpu['reason']}", f"Instance: {gpu['instance']}",
        f"Hourly rate / accrued: {gpu['hourly_rate_usd']} / {gpu['accrued_gpu_cost_usd']}", f"Keep-until / destroy condition: {gpu['keep_destroy_condition']}", "",
        "Handoffs:", f"Latest AP: {handoffs['latest_ap']}", f"Latest IM: {handoffs['latest_im']}", f"Latest LO: {handoffs['latest_lo']}", f"Active goal: {handoffs['active_goal']}", "",
        "Projections:", f"Obsidian: {projections['obsidian']}", f"MLflow: {projections['mlflow']}", "",
        "Routing:", f"Recommended next session: {routing['recommended_next_session']}", f"Recommended model: {routing['recommended_model']}",
        f"Reasoning effort: {routing['reasoning_effort']}", f"Reason: {routing['reason']}", f"Command before prompt: {routing['command_before_prompt']}",
        f"Copy-paste prompt: {routing['copy_paste_prompt']}", f"Owner decision required: {routing['owner_decision_required']}",
    ])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-status")
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    status = build_owner_status(args.repository_root)
    print(json.dumps(status, ensure_ascii=False, indent=2) if args.json else render_owner_status(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
