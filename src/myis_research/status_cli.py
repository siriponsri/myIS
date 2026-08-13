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
    for path in (root / "docs/goal").glob("*.md"):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        frontmatter = text.split("---", 2)[1]
        data = yaml.safe_load(frontmatter)
        if not isinstance(data, Mapping):
            continue
        if data.get("lifecycle") in {"ACTIVE", "READY"}:
            candidates.append(path)
    return (
        sorted(candidates)[-1].relative_to(root).as_posix()
        if candidates
        else "NONE"
    )


def _projection_status(root: Path, model: Mapping[str, Any]) -> dict[str, str]:
    expected_revision = model["read_model_revision"]
    read_model_path = root / "projections/read-model/read-model.v2.json"
    home_path = root / "obsidian_report/HOME.md"
    archive_path = root / "mlflow/generated/archive-index.v2.json"
    try:
        stored = json.loads(read_model_path.read_text(encoding="utf-8"))
        read_model_current = stored.get("read_model_revision") == expected_revision
    except (OSError, UnicodeError, json.JSONDecodeError):
        read_model_current = False
    obsidian_ok = read_model_current and home_path.is_file()
    try:
        archive = json.loads(archive_path.read_text(encoding="utf-8"))
        mlflow_ok = archive.get("read_model_revision") == expected_revision
    except (OSError, UnicodeError, json.JSONDecodeError):
        mlflow_ok = False
    return {
        "obsidian": "OK" if obsidian_ok else "PENDING",
        "mlflow": "OK" if mlflow_ok else "PENDING",
    }


def build_owner_status(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    model = build_read_model(root)
    project = model["project"]
    armindex = model["armindex"]
    readiness = armindex.get("a2_execution_readiness", {})
    if not isinstance(readiness, Mapping):
        readiness = {}
    counters = readiness.get("counters", {})
    if not isinstance(counters, Mapping):
        counters = {}
    projections = _projection_status(root, model)
    prompt = (
        "ตอนนี้คุณคือ AP ตาม AGENTS.md; restructure is CLOSED และห้าม reopen restructure. "
        "เริ่มจาก PLAN.md และ A2 canonical current state, ตรวจ current budget กับ GPU/Vast lifecycle, "
        "ประเมิน publication-value next action แล้วเลือก ONE route: IM หรือ LO. "
        "ถ้าเลือก IM ให้ระบุ exact model/reasoning/prompt; ถ้าเลือก LO ให้ระบุ exact model/reasoning "
        "และ exact /goal command. Owner ไม่ต้องเลือก model เอง."
    )
    return {
        "project": {
            "phase": project.get("current_phase", "UNKNOWN"),
            "task": (
                f"{project.get('current_task', 'UNKNOWN')} / "
                f"{project.get('current_substage', 'UNKNOWN')}"
            ),
            "status_th": (
                "A2 candidate freeze ปิดผ่านแล้ว; ตอนนี้เป็น pre-measurement "
                "engineering readiness และยังไม่เริ่ม candidate evaluation หรือ measured A2"
            ),
            "evidence_class": readiness.get("evidence_class", "UNKNOWN"),
            "scientific_authority": readiness.get("scientific_authority", "UNKNOWN"),
            "supported_claim_boundary": readiness.get("claim_boundary", "UNKNOWN"),
        },
        "budget": {
            "phase_ceiling_usd": readiness.get("phase_ceiling_usd", "UNKNOWN"),
            "task_run_ceiling_usd": readiness.get("task_run_ceiling_usd", "UNKNOWN"),
            "spent_accrued_usd": readiness.get("a2_spent_accrued_usd", "UNKNOWN"),
            "campaign_ceiling_usd": readiness.get("campaign_ceiling_usd", "UNKNOWN"),
            "remaining_headroom_usd": readiness.get(
                "remaining_campaign_headroom_usd", "UNKNOWN"
            ),
            "estimated_next_action_cost_usd": readiness.get(
                "estimated_next_action_cost_usd", "UNKNOWN"
            ),
            "next_phase_ceiling_usd": readiness.get(
                "next_phase_ceiling_usd", "NOT_BOUND"
            ),
            "status": readiness.get("budget_status", "UNKNOWN_DO_NOT_SPEND"),
        },
        "gpu_vast": {
            "decision": "UNKNOWN",
            "reason": (
                "fresh runtime instance binding and all-fee quote are not present; "
                "AP must resolve lifecycle state before provider use"
            ),
            "instance": "NONE",
            "hourly_rate_usd": "UNKNOWN",
            "accrued_gpu_cost_usd": "UNKNOWN",
            "keep_destroy_condition": "NOT_APPLICABLE",
        },
        "handoffs": {
            "latest_ap": _latest(
                root, "docs/audit", "A2_PER_ARM_AUTOINDEX_audit_[0-9][0-9][0-9].md"
            ),
            "latest_im": _latest(
                root,
                "docs/implementation",
                "A2_PER_ARM_AUTOINDEX_im_[0-9][0-9][0-9]_[0-9][0-9][0-9].md",
            ),
            "latest_lo": _latest(
                root,
                "docs/long_run",
                "A2_PER_ARM_AUTOINDEX_lo_[0-9][0-9][0-9]_[0-9][0-9][0-9].md",
            ),
            "active_goal": _active_goal(root),
        },
        "projections": projections,
        "routing": {
            "recommended_next_session": "AP",
            "recommended_model": "GPT-5.6 Sol High",
            "reasoning_effort": "High",
            "reason": "A2 needs one current budget/GPU lifecycle judgment before choosing IM or LO.",
            "command_before_prompt": "NONE",
            "copy_paste_prompt": prompt,
            "owner_decision_required": "NONE",
        },
        "boundaries": {
            "candidate_evaluations": counters.get("candidate_evaluations", "UNKNOWN"),
            "measured_a2_runs": counters.get("measured_a2_runs", "UNKNOWN"),
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
    project = status["project"]
    budget = status["budget"]
    gpu = status["gpu_vast"]
    handoffs = status["handoffs"]
    projections = status["projections"]
    routing = status["routing"]
    return "\n".join(
        [
            "สถานะโครงการ",
            f"Phase: {project['phase']}",
            f"Task/Sub-stage: {project['task']}",
            f"สถานะสั้น ๆ: {project['status_th']}",
            f"Evidence class: {project['evidence_class']}",
            f"Scientific authority: {project['scientific_authority']}",
            f"Supported claim boundary: {project['supported_claim_boundary']}",
            "",
            "Budget:",
            f"Phase ceiling: {_value(budget['phase_ceiling_usd'], money=True)}",
            f"Current Task/Run ceiling: {_value(budget['task_run_ceiling_usd'], money=True)}",
            f"Spent/Accrued: {_value(budget['spent_accrued_usd'], money=True)}",
            f"Campaign ceiling: {_value(budget['campaign_ceiling_usd'], money=True)}",
            f"Remaining headroom: {_value(budget['remaining_headroom_usd'], money=True)}",
            f"Estimated next-action cost: {_value(budget['estimated_next_action_cost_usd'], money=True)}",
            f"Next Phase ceiling: {_value(budget['next_phase_ceiling_usd'], money=True)}",
            f"Budget status: {budget['status']}",
            "",
            "GPU / Vast:",
            f"GPU decision: {gpu['decision']}",
            f"Reason: {gpu['reason']}",
            f"Instance: {gpu['instance']}",
            f"Hourly rate / accrued: {gpu['hourly_rate_usd']} / {gpu['accrued_gpu_cost_usd']}",
            f"Keep-until / destroy condition: {gpu['keep_destroy_condition']}",
            "",
            "Handoffs:",
            f"Latest AP: {handoffs['latest_ap']}",
            f"Latest IM: {handoffs['latest_im']}",
            f"Latest LO: {handoffs['latest_lo']}",
            f"Active goal: {handoffs['active_goal']}",
            "",
            "Projections:",
            f"Obsidian: {projections['obsidian']}",
            f"MLflow: {projections['mlflow']}",
            "",
            "Routing:",
            f"Recommended next session: {routing['recommended_next_session']}",
            f"Recommended model: {routing['recommended_model']}",
            f"Reasoning effort: {routing['reasoning_effort']}",
            f"Reason: {routing['reason']}",
            f"Command before prompt: {routing['command_before_prompt']}",
            f"Copy-paste prompt: {routing['copy_paste_prompt']}",
            f"Owner decision required: {routing['owner_decision_required']}",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-status")
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    status = build_owner_status(args.repository_root)
    print(
        json.dumps(status, ensure_ascii=False, indent=2)
        if args.json
        else render_owner_status(status)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
