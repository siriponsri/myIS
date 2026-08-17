"""Render evidence-bound A2 Goal 004 figures from aggregate-safe closeout facts."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only

PROJECTION_PATH = Path("control/armindex/a2/a2-goal004-closeout-projection.v1.json")
OUTPUT_DIRECTORY = Path("outputs/figures/armindex/a2-goal004")
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_ARM_ORDER = ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")
_FIGURES = (
    ("coverage-recovery", "A2 coverage: 44 measured, 8 dormant, 0 failed"),
    ("outcomes", "A2 aggregate OUT metrics by arm"),
    ("quality-latency-cost-frontier", "A2 quality, search latency, and candidate cost"),
    ("matched-reserve-decision-path", "A2 matched-first reserve decision path"),
    ("appendix-audit-map", "A2 evidence chain for publication claims"),
)


class A2Goal004CloseoutFigureError(ValueError):
    """Raised when A2 closeout evidence cannot safely support a figure."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A2Goal004CloseoutFigureError(f"invalid JSON artifact: {path}") from error
    if not isinstance(value, dict):
        raise A2Goal004CloseoutFigureError(f"JSON artifact must be an object: {path}")
    return value


def _validate_schema(root: Path, relative: Path, value: Mapping[str, Any]) -> None:
    schema = _load_json(root / relative)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(value)),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if errors:
        raise A2Goal004CloseoutFigureError(
            f"{relative.name} validation failed: {errors[0].message}"
        )


def _owner_store_path(repository_root: Path, uri: str) -> Path:
    prefix = "owner-store://"
    if not uri.startswith(prefix):
        raise A2Goal004CloseoutFigureError("source artifact URI is not owner-store scoped")
    relative = Path(uri.removeprefix(prefix))
    if relative.is_absolute() or ".." in relative.parts:
        raise A2Goal004CloseoutFigureError("source artifact URI escapes the Owner Store")
    return repository_root.parent / "04_Owner_Stores" / relative


def _validate_source_artifacts(repository_root: Path, projection: Mapping[str, Any]) -> None:
    for artifact_name, artifact in projection["source_artifacts"].items():
        if not isinstance(artifact, Mapping):
            raise A2Goal004CloseoutFigureError(f"{artifact_name} source artifact is invalid")
        source_path = _owner_store_path(repository_root, str(artifact["uri"]))
        if not source_path.is_file():
            raise A2Goal004CloseoutFigureError(f"{artifact_name} source artifact is unavailable")
        if file_sha256(source_path) != artifact["file_sha256"]:
            raise A2Goal004CloseoutFigureError(f"{artifact_name} source file hash does not match")
        source = _load_json(source_path)
        source_record_hash = source.get("receipt_sha256", source.get("audit_sha256"))
        if source_record_hash != artifact["record_sha256"]:
            raise A2Goal004CloseoutFigureError(f"{artifact_name} source record hash does not match")


def validate_a2_goal004_closeout_projection(repository_root: Path) -> dict[str, Any]:
    """Load and validate the immutable-safe projection used by every A2 figure."""

    root = repository_root.resolve()
    projection = _load_json(root / PROJECTION_PATH)
    _validate_schema(root, Path("schemas/armindex/a2-goal004-closeout-projection.v1.json"), projection)
    expected_hash = projection.get("projection_sha256")
    unsigned = {key: value for key, value in projection.items() if key != "projection_sha256"}
    if not isinstance(expected_hash, str) or _SHA256.fullmatch(expected_hash) is None:
        raise A2Goal004CloseoutFigureError("projection self-hash is invalid")
    if expected_hash != canonical_sha256(unsigned):
        raise A2Goal004CloseoutFigureError("projection self-hash does not bind its contents")
    _validate_source_artifacts(root, projection)
    try:
        assert_aggregate_only(projection)
    except ValueError as error:
        raise A2Goal004CloseoutFigureError("projection crosses the protected boundary") from error
    outcomes = projection["arm_outcomes"]
    if not isinstance(outcomes, list) or tuple(row.get("arm_id") for row in outcomes) != _ARM_ORDER:
        raise A2Goal004CloseoutFigureError("arm outcomes must retain the five-arm order")
    if any(not isinstance(row, Mapping) for row in outcomes):
        raise A2Goal004CloseoutFigureError("arm outcomes are invalid")
    return projection


def _artifact(root: Path, path: Path) -> dict[str, Any]:
    return {
        "uri": path.relative_to(root).as_posix(),
        "sha256": file_sha256(path),
        "bytes": path.stat().st_size,
    }


def _normalize_svg(path: Path) -> None:
    """Remove renderer-only trailing spaces so generated SVGs pass Git checks."""
    text = path.read_text(encoding="utf-8")
    normalized = "\n".join(line.rstrip(" \t") for line in text.splitlines()) + "\n"
    path.write_text(normalized, encoding="utf-8")


def _render(figure_id: str, title: str, projection: Mapping[str, Any]):
    try:
        import matplotlib

        matplotlib.use("Agg")
        from matplotlib import pyplot as plt
    except ImportError as error:
        raise A2Goal004CloseoutFigureError("matplotlib is required") from error

    palette = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#D55E00"]
    outcomes = list(projection["arm_outcomes"])
    accounting = projection["accounting"]
    figure, axis = plt.subplots(figsize=(7.2, 4.5), constrained_layout=True)
    figure.set_facecolor("white")
    axis.set_title(title, loc="left", fontweight="bold", fontsize=12)

    if figure_id == "coverage-recovery":
        labels = ["Matched\nmeasured", "Reserve\nactivated", "Reserve\ndormant"]
        values = [
            accounting["matched_candidate_count"],
            accounting["activated_reserve_candidate_count"],
            accounting["dormant_reserve_candidate_count"],
        ]
        bars = axis.bar(labels, values, color=[palette[0], palette[2], "#999999"])
        axis.set_ylabel("Frozen candidates")
        axis.set_ylim(0, 44)
        for bar, value in zip(bars, values, strict=True):
            axis.text(bar.get_x() + bar.get_width() / 2, value + 0.8, str(value), ha="center")
    elif figure_id == "outcomes":
        x = list(range(len(outcomes)))
        width = 0.25
        for offset, key, label, color in (
            (-width, "recall_at_100", "Recall@100", palette[0]),
            (0, "ndcg_at_100", "nDCG@100", palette[2]),
            (width, "ndcg_at_10", "nDCG@10", palette[4]),
        ):
            axis.bar([value + offset for value in x], [row[key] for row in outcomes], width, label=label, color=color)
        axis.set_xticks(x, [str(row["arm_id"]).replace("ARM-", "Arm ") for row in outcomes])
        axis.set_ylabel("Aggregate OUT metric")
        axis.set_ylim(0, 0.5)
        axis.legend(frameon=False, ncols=3, loc="upper center", bbox_to_anchor=(0.5, 1.16))
        axis.text(
            0.02,
            0.96,
            "Arms 01-02: diagnostic ties, not A3 inputs",
            transform=axis.transAxes,
            va="top",
            fontsize=8,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.9},
        )
    elif figure_id == "quality-latency-cost-frontier":
        for row, color in zip(outcomes, palette, strict=True):
            size = max(40.0, float(row["charged_usd"]) * 500.0)
            axis.scatter(float(row["search_p95_ms"]), float(row["recall_at_100"]), s=size, color=color, edgecolor="black", linewidth=0.5)
            axis.annotate(str(row["arm_id"]).replace("ARM-", "Arm "), (float(row["search_p95_ms"]), float(row["recall_at_100"])), xytext=(5, 5), textcoords="offset points", fontsize=8)
        axis.set_xlabel("Search p95 latency (ms)")
        axis.set_ylabel("Recall@100")
        axis.text(0.02, 0.02, "Marker area represents candidate charged USD", transform=axis.transAxes, fontsize=8)
    elif figure_id == "matched-reserve-decision-path":
        labels = ["Matched\n40", "Reserve\nactivated 4", "Reserve\ndormant 8", "Closeout\n52 accounted"]
        axis.plot(range(4), [0, 0, 0, 0], color="#4D4D4D", marker="o", markersize=9)
        for position, label in enumerate(labels):
            axis.text(position, 0.12, label, ha="center", va="bottom")
        axis.set_xlim(-0.4, 3.4)
        axis.set_ylim(-0.4, 0.55)
        axis.axis("off")
        axis.text(1.5, -0.27, "Dormant reserves are retained as valid bounded negative evidence.", ha="center", fontsize=9)
    else:
        sources = projection["source_artifacts"]
        rows = [
            ["Execution closeout", sources["execution_closeout"]["record_sha256"][:12]],
            ["Result-integrity audit", sources["result_integrity_audit"]["record_sha256"][:12]],
            ["Safe return", sources["safe_return"]["record_sha256"][:12]],
            ["Closeout projection", projection["projection_sha256"][:12]],
        ]
        table = axis.table(cellText=rows, colLabels=["Artifact", "SHA-256 prefix"], cellLoc="left", loc="center")
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.7)
        axis.axis("off")
    return figure


def render_a2_goal004_closeout_figures(repository_root: Path) -> dict[str, Any]:
    """Render five PNG/SVG/PDF publication figures in the required A2 output root."""

    root = repository_root.resolve()
    projection = validate_a2_goal004_closeout_projection(root)
    destination = root / OUTPUT_DIRECTORY
    destination.mkdir(parents=True, exist_ok=True)
    figures: list[dict[str, Any]] = []
    for figure_id, title in _FIGURES:
        figure = _render(figure_id, title, projection)
        artifacts: dict[str, dict[str, Any]] = {}
        for suffix in ("png", "svg", "pdf"):
            path = destination / f"a2-goal004-{figure_id}.{suffix}"
            figure.savefig(path, dpi=300 if suffix == "png" else None, bbox_inches="tight")
            if suffix == "svg":
                _normalize_svg(path)
            artifacts[suffix] = _artifact(root, path)
        figure.clear()
        figures.append({"figure_id": figure_id, "title": title, "artifacts": artifacts})
    manifest = {
        "schema_version": "myis.armindex-a2-goal004-publication-figure-manifest.v1",
        "attempt_id": projection["attempt_id"],
        "status": "PASS_A2_GOAL004_PUBLICATION_FIGURES",
        "projection_sha256": projection["projection_sha256"],
        "figures": figures,
    }
    manifest["manifest_sha256"] = canonical_sha256(manifest)
    _validate_schema(root, Path("schemas/armindex/a2-goal004-publication-figure-manifest.v1.json"), manifest)
    path = destination / "a2-goal004-figure-manifest.v1.json"
    path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return {"manifest": manifest, "manifest_path": path}


__all__ = [
    "A2Goal004CloseoutFigureError",
    "OUTPUT_DIRECTORY",
    "PROJECTION_PATH",
    "render_a2_goal004_closeout_figures",
    "validate_a2_goal004_closeout_projection",
]
