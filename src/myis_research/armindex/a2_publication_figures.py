"""Render the five aggregate-only A2 Goal 004 publication figures.

This module is intentionally downstream of measured execution.  It accepts no
candidate-level or protected input, validates a complete execution closeout and
an independent aggregate result audit, then renders only arm-level summaries.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only

ARM_IDS = ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")
OUTPUT_DIRECTORY = Path("outputs/figures/armindex/a2-goal004")
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_METRIC_FIELDS = (
    "recall_at_100",
    "ndcg_at_100",
    "ndcg_at_10",
    "latency_ms",
    "charged_usd",
    "index_size_mb",
    "ram_gb",
    "vram_gb",
)
_FIGURES = (
    (
        "coverage-recovery",
        "Did the frozen workload complete with recoverable evidence?",
        "All 52 frozen candidates are accounted for at measured closeout",
    ),
    (
        "outcomes",
        "What development outcomes were observed per arm?",
        "OUT outcomes are shown without implying advancement for diagnostic arms",
    ),
    (
        "quality-latency-cost-frontier",
        "What quality, latency, and charged-cost trade-off is supported?",
        "Quality-latency-cost trade-offs remain arm-level aggregate evidence",
    ),
    (
        "matched-reserve-decision-path",
        "How did matched and conditional reserve candidates progress?",
        "Reserve activation is reported as a decision path, not a performance claim",
    ),
    (
        "appendix-audit-map",
        "Which artifacts bound the publication claims?",
        "Every A2 figure traces to the closeout and aggregate result audit",
    ),
)


class A2PublicationFigureError(ValueError):
    """Raised when A2 publication evidence or a rendering target is unsafe."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A2PublicationFigureError(f"invalid JSON artifact: {path}") from error
    if not isinstance(value, dict):
        raise A2PublicationFigureError(f"JSON artifact must be an object: {path}")
    return value


def _validate_schema(root: Path, name: str, value: Mapping[str, Any]) -> None:
    schema = _load_json(root / "schemas/armindex" / name)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(value)),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if errors:
        raise A2PublicationFigureError(f"{name} validation failed: {errors[0].message}")


def _self_hash(value: Mapping[str, Any], field: str, *, role: str) -> None:
    actual = value.get(field)
    if not isinstance(actual, str) or _SHA256.fullmatch(actual) is None:
        raise A2PublicationFigureError(f"{role} self-hash is invalid")
    unsigned = {key: item for key, item in value.items() if key != field}
    if actual != canonical_sha256(unsigned):
        raise A2PublicationFigureError(f"{role} self-hash does not bind its contents")


def _number(value: Any, *, field: str, upper: float | None = None) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise A2PublicationFigureError(f"{field} must be numeric or null")
    number = float(value)
    if number < 0 or (upper is not None and number > upper):
        raise A2PublicationFigureError(f"{field} is outside its valid range")
    return number


def _validate_arm_metrics(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != len(ARM_IDS):
        raise A2PublicationFigureError("arm_metrics must contain the five frozen arms")
    expected = {"arm_id", *_METRIC_FIELDS}
    rows: list[dict[str, Any]] = []
    for row in value:
        if not isinstance(row, Mapping) or set(row) != expected:
            raise A2PublicationFigureError("arm metric fields are not allowlisted")
        arm_id = row.get("arm_id")
        if arm_id not in ARM_IDS:
            raise A2PublicationFigureError("arm metric has an unknown arm")
        checked = {"arm_id": arm_id}
        for field in _METRIC_FIELDS:
            checked[field] = _number(
                row[field],
                field=f"{arm_id}.{field}",
                upper=1.0 if field in {"recall_at_100", "ndcg_at_100", "ndcg_at_10"} else None,
            )
        rows.append(checked)
    if {row["arm_id"] for row in rows} != set(ARM_IDS):
        raise A2PublicationFigureError("arm_metrics must cover each frozen arm exactly once")
    return sorted(rows, key=lambda row: ARM_IDS.index(str(row["arm_id"])))


def validate_a2_goal004_figure_evidence(
    repository_root: Path,
    evidence: Mapping[str, Any],
    *,
    fixture_mode: bool = False,
) -> dict[str, Any]:
    """Validate complete, aggregate-only post-closeout figure inputs."""

    root = repository_root.resolve()
    checked = deepcopy(dict(evidence))
    try:
        assert_aggregate_only(checked)
    except ValueError as error:
        raise A2PublicationFigureError("figure evidence crosses the protected boundary") from error
    expected = {
        "execution_closeout",
        "result_audit",
        "arm_metrics",
        "recovery_summary",
        "reserve_decision",
    }
    if set(checked) != expected:
        raise A2PublicationFigureError("figure evidence fields are not allowlisted")
    closeout = checked["execution_closeout"]
    audit = checked["result_audit"]
    if not isinstance(closeout, Mapping) or not isinstance(audit, Mapping):
        raise A2PublicationFigureError("closeout and audit evidence must be objects")
    _validate_schema(root, "a2-execution-closeout-receipt.v1.json", closeout)
    _validate_schema(root, "a2-result-audit-receipt.v1.json", audit)
    _self_hash(closeout, "receipt_sha256", role="execution closeout")
    _self_hash(audit, "audit_sha256", role="result audit")
    if closeout["evidence_class"] != "measured_development_aggregate" and not fixture_mode:
        raise A2PublicationFigureError("production figures require measured aggregate closeout evidence")
    if audit["attempt_id"] != closeout["attempt_id"]:
        raise A2PublicationFigureError("result audit attempt does not match execution closeout")
    for field in (
        "execution_closeout_receipt_sha256",
        "candidate_result_set_sha256",
        "safe_return_receipt_sha256",
    ):
        closeout_field = "receipt_sha256" if field == "execution_closeout_receipt_sha256" else field
        if audit[field] != closeout[closeout_field]:
            raise A2PublicationFigureError(f"result audit {field} does not match closeout")
    metrics = _validate_arm_metrics(checked["arm_metrics"])
    recovery = checked["recovery_summary"]
    reserve = checked["reserve_decision"]
    if not isinstance(recovery, Mapping) or set(recovery) != {
        "checkpoint_count", "recovered_candidate_count", "failed_attempts_separated"
    }:
        raise A2PublicationFigureError("recovery summary fields are not allowlisted")
    if (
        not isinstance(recovery["checkpoint_count"], int)
        or recovery["checkpoint_count"] < 1
        or not isinstance(recovery["recovered_candidate_count"], int)
        or recovery["recovered_candidate_count"] < 0
        or recovery["failed_attempts_separated"] is not True
    ):
        raise A2PublicationFigureError("recovery summary is invalid")
    if not isinstance(reserve, Mapping) or set(reserve) != {
        "matched_status", "reserve_status", "reserve_candidate_count"
    }:
        raise A2PublicationFigureError("reserve decision fields are not allowlisted")
    if (
        reserve["matched_status"] != "COMPLETE"
        or reserve["reserve_status"] not in {"ACTIVATED", "DORMANT"}
        or reserve["reserve_candidate_count"] != 12
    ):
        raise A2PublicationFigureError("reserve decision does not match the frozen A2 policy")
    return {
        "execution_closeout": dict(closeout),
        "result_audit": dict(audit),
        "arm_metrics": metrics,
        "recovery_summary": dict(recovery),
        "reserve_decision": dict(reserve),
    }


def _render_figure(figure_id: str, title: str, evidence: Mapping[str, Any]):
    try:
        import matplotlib

        matplotlib.use("Agg")
        from matplotlib import pyplot as plt
    except ImportError as error:
        raise A2PublicationFigureError("matplotlib is required to render A2 figures") from error
    palette = ["#0072B2", "#009E73", "#D55E00", "#CC79A7", "#666666"]
    metrics = list(evidence["arm_metrics"])
    arms = [str(row["arm_id"]).replace("ARM-", "Arm ") for row in metrics]
    figure, axis = plt.subplots(figsize=(7.2, 4.5), constrained_layout=True)
    figure.set_facecolor("white")
    axis.set_title(title, loc="left", fontweight="bold", fontsize=12)
    if figure_id == "coverage-recovery":
        closeout = evidence["execution_closeout"]
        values = [closeout["matched_candidate_count"], closeout["conditional_reserve_candidate_count"]]
        bars = axis.bar(["Matched", "Conditional reserve"], values, color=[palette[0], palette[1]])
        axis.set_ylabel("Frozen candidates")
        axis.set_ylim(0, 44)
        for bar, value in zip(bars, values, strict=True):
            axis.text(bar.get_x() + bar.get_width() / 2, value + 1, str(value), ha="center")
        recovery = evidence["recovery_summary"]
        axis.text(
            0.02,
            0.94,
            f"{recovery['checkpoint_count']} checkpoints; {recovery['recovered_candidate_count']} recovered candidates",
            transform=axis.transAxes,
            va="top",
            fontsize=9,
        )
    elif figure_id == "outcomes":
        x = list(range(len(metrics)))
        width = 0.26
        for offset, field, label, color in (
            (-width, "recall_at_100", "Recall@100", palette[0]),
            (0, "ndcg_at_100", "nDCG@100", palette[1]),
            (width, "ndcg_at_10", "nDCG@10", palette[2]),
        ):
            values = [row[field] if row[field] is not None else 0 for row in metrics]
            axis.bar([item + offset for item in x], values, width, label=label, color=color)
        axis.set_xticks(x, arms)
        axis.set_ylim(0, 1)
        axis.set_ylabel("Aggregate OUT metric")
        axis.legend(frameon=False, ncols=3, loc="upper center", bbox_to_anchor=(0.5, 1.16))
        axis.text(0.02, 0.02, "Diagnostic arms: Arm 01 and Arm 02", transform=axis.transAxes, fontsize=8)
    elif figure_id == "quality-latency-cost-frontier":
        for row, label, color in zip(metrics, arms, palette, strict=True):
            recall = row["recall_at_100"]
            latency = row["latency_ms"]
            cost = row["charged_usd"]
            if recall is None or latency is None or cost is None:
                axis.text(0.5, 0.5, "Not computable", transform=axis.transAxes, ha="center", va="center")
                continue
            size = max(40.0, cost * 120.0)
            axis.scatter(latency, recall, s=size, color=color, edgecolor="black", linewidth=0.5)
            axis.annotate(label, (latency, recall), xytext=(5, 5), textcoords="offset points", fontsize=8)
        axis.set_xlabel("Latency (ms)")
        axis.set_ylabel("Recall@100")
        axis.text(0.02, 0.02, "Marker area represents charged USD", transform=axis.transAxes, fontsize=8)
    elif figure_id == "matched-reserve-decision-path":
        reserve = evidence["reserve_decision"]
        labels = ["Matched\n40", "Admission\nrule", f"Reserve\n12 ({reserve['reserve_status'].title()})"]
        axis.plot([0, 1, 2], [0, 0, 0], color="#4D4D4D", marker="o", markersize=9)
        for position, label in enumerate(labels):
            axis.text(position, 0.12, label, ha="center", va="bottom")
        axis.set_xlim(-0.4, 2.4)
        axis.set_ylim(-0.4, 0.55)
        axis.axis("off")
        axis.text(0.5, -0.26, "Matched completion was required before reserve handling.", ha="center")
    else:
        closeout = evidence["execution_closeout"]
        audit = evidence["result_audit"]
        rows = [
            ["Execution closeout", closeout["receipt_sha256"][:12]],
            ["Aggregate result audit", audit["audit_sha256"][:12]],
            ["Candidate result set", closeout["candidate_result_set_sha256"][:12]],
            ["Safe return", closeout["safe_return_receipt_sha256"][:12]],
        ]
        table = axis.table(cellText=rows, colLabels=["Artifact", "SHA-256 prefix"], cellLoc="left", loc="center")
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.7)
        axis.axis("off")
    return figure


def _artifact(root: Path, path: Path, *, fixture_mode: bool) -> dict[str, Any]:
    try:
        uri = path.relative_to(root).as_posix()
    except ValueError:
        if not fixture_mode:
            raise A2PublicationFigureError("production figure path escapes the repository")
        uri = f"fixture-output/{path.name}"
    return {
        "uri": uri,
        "sha256": file_sha256(path),
        "bytes": path.stat().st_size,
    }


def render_a2_goal004_publication_figures(
    repository_root: Path,
    evidence: Mapping[str, Any],
    *,
    output_directory: Path | None = None,
    fixture_mode: bool = False,
) -> dict[str, Any]:
    """Render five paper-size PNG/SVG/PDF figures from complete A2 evidence."""

    root = repository_root.resolve()
    checked = validate_a2_goal004_figure_evidence(root, evidence, fixture_mode=fixture_mode)
    destination = (output_directory or root / OUTPUT_DIRECTORY).resolve()
    expected_destination = (root / OUTPUT_DIRECTORY).resolve()
    if not fixture_mode and destination != expected_destination:
        raise A2PublicationFigureError("production figures must use the Goal 004 output directory")
    destination.mkdir(parents=True, exist_ok=True)
    artifacts: list[dict[str, Any]] = []
    source_hashes = [
        checked["execution_closeout"]["receipt_sha256"],
        checked["result_audit"]["audit_sha256"],
    ]
    for figure_id, reviewer_question, title in _FIGURES:
        figure = _render_figure(figure_id, title, checked)
        figure_artifacts: dict[str, dict[str, Any]] = {}
        for suffix in ("png", "svg", "pdf"):
            path = destination / f"a2-goal004-{figure_id}.{suffix}"
            figure.savefig(path, dpi=300 if suffix == "png" else None, bbox_inches="tight")
            figure_artifacts[suffix] = _artifact(root, path, fixture_mode=fixture_mode)
        figure.clear()
        caption = (
            f"{title}. Evidence is aggregate-only; source artifacts are the execution closeout "
            "and independent result audit."
        )
        artifacts.append(
            {
                "figure_id": figure_id,
                "reviewer_question": reviewer_question,
                "title": title,
                "caption": caption,
                "evidence_sha256s": source_hashes,
                "artifacts": figure_artifacts,
            }
        )
    manifest = {
        "schema_version": "myis.armindex-a2-publication-figure-manifest.v1",
        "attempt_id": checked["execution_closeout"]["attempt_id"],
        "status": "PASS_A2_GOAL004_PUBLICATION_FIGURES",
        "evidence_class": checked["execution_closeout"]["evidence_class"],
        "fixture_mode": fixture_mode,
        "execution_closeout_receipt_sha256": checked["execution_closeout"]["receipt_sha256"],
        "result_audit_sha256": checked["result_audit"]["audit_sha256"],
        "claim_boundary": checked["result_audit"]["claim_boundary"],
        "figures": artifacts,
    }
    manifest["manifest_sha256"] = canonical_sha256(manifest)
    _validate_schema(root, "a2-publication-figure-manifest.v1.json", manifest)
    manifest_path = destination / "a2-goal004-figure-manifest.v1.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return {"manifest": manifest, "manifest_path": manifest_path}


__all__ = [
    "A2PublicationFigureError",
    "OUTPUT_DIRECTORY",
    "render_a2_goal004_publication_figures",
    "validate_a2_goal004_figure_evidence",
]
