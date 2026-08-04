"""Governed registry for reusable Research assets held in sibling repositories."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

import yaml


REGISTRY_RELATIVE_PATH = Path("control/assets/reusable_assets.yaml")
MAP_RELATIVE_PATH = Path("control/assets/REUSABLE_ASSET_MAP.md")
PLAN_RELATIVE_PATH = Path("PLAN.md")
LEGACY_PLAN_RELATIVE_PATH = Path("archive/legacy-cs/docs/PLAN.v1.md")
SCHEMA_VERSION = "myis.reusable-assets.v2"
DISPOSITIONS = frozenset({"reuse", "adapt", "reference_only", "blocked", "duplicate"})
COPY_MODES = frozenset({"pointer", "preport", "fixture", "none"})
VALIDATION_MODES = frozenset({"quick", "full", "reference_only"})
PROTECTED_LEVELS = frozenset({"none", "metadata", "protected", "frozen_results"})
COMPATIBILITY_STATUSES = frozenset(
    {"compatible", "conditional", "incompatible", "reference_only", "blocked"}
)
_TASK_RE = re.compile(r"^### Task ([A-Z0-9]+\.\d+) - (.+)$")
_GATE_RE = re.compile(r"^- \*\*Owner Gate:\*\* .*?\b(G[0-8])\b")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_HF_DATASET_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_TICK = chr(96)


class AssetRegistryError(ValueError):
    """Raised when the registry or one of its governed references is invalid."""


@dataclass(frozen=True)
class PlanTask:
    task_id: str
    title: str
    phase_id: str
    gate_id: str


@dataclass(frozen=True)
class ValidationReport:
    mode: str
    asset_ids: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "asset_ids": list(self.asset_ids),
            "errors": list(self.errors),
            "mode": self.mode,
            "ok": self.ok,
            "warnings": list(self.warnings),
        }


def repository_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / REGISTRY_RELATIVE_PATH).is_file() and (candidate / PLAN_RELATIVE_PATH).is_file():
            return candidate
    raise AssetRegistryError("could not locate the myIS Research repository root")


def parse_plan_tasks(plan_path: Path) -> tuple[PlanTask, ...]:
    tasks: list[PlanTask] = []
    current: tuple[str, str] | None = None
    for line in plan_path.read_text(encoding="utf-8").splitlines():
        task_match = _TASK_RE.match(line)
        if task_match:
            current = (task_match.group(1), task_match.group(2).strip())
            continue
        gate_match = _GATE_RE.match(line)
        if current and gate_match:
            task_id, title = current
            tasks.append(PlanTask(task_id, title, task_id.split(".", 1)[0], gate_match.group(1)))
            current = None
    if current is not None:
        raise AssetRegistryError(f"PLAN task {current[0]} has no Owner Gate")
    if len(tasks) != 22:
        raise AssetRegistryError(f"expected 22 PLAN tasks, found {len(tasks)}")
    return tuple(tasks)


def load_registry(root: Path | None = None, registry_path: Path | None = None) -> dict[str, Any]:
    repo = repository_root(root) if registry_path is None else (root or registry_path.parent).resolve()
    path = registry_path or repo / REGISTRY_RELATIVE_PATH
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise AssetRegistryError(f"cannot load reusable asset registry: {error}") from error
    if not isinstance(payload, dict):
        raise AssetRegistryError("registry root must be a mapping")
    validate_registry(payload, repo)
    return payload


def validate_registry(payload: dict[str, Any], root: Path) -> None:
    if payload.get("schema_version") == "myis.reusable-assets.v2":
        _validate_registry_v2(payload, root)
        return
    if payload.get("schema_version") != "myis.reusable-assets.v1":
        raise AssetRegistryError("unsupported reusable asset schema")
    repositories = payload.get("source_repositories")
    if not isinstance(repositories, dict) or not repositories:
        raise AssetRegistryError("source_repositories must be a non-empty mapping")
    for repo_id, spec in sorted(repositories.items()):
        if not isinstance(repo_id, str) or not isinstance(spec, dict):
            raise AssetRegistryError("source repository entries must be named mappings")
        if not _GIT_COMMIT_RE.fullmatch(str(spec.get("commit", "")).casefold()):
            raise AssetRegistryError(f"source repository {repo_id} requires a Git commit")
        if not isinstance(spec.get("root_hint"), str) or not spec["root_hint"].strip():
            raise AssetRegistryError(f"source repository {repo_id} requires root_hint")

    plan_path = root / LEGACY_PLAN_RELATIVE_PATH
    tasks = parse_plan_tasks(plan_path)
    task_index = {task.task_id: task for task in tasks}
    assets = payload.get("assets")
    if not isinstance(assets, list) or not assets:
        raise AssetRegistryError("assets must be a non-empty list")
    required = {
        "asset_id", "title", "kind", "source", "authority", "frozen", "disposition",
        "protocol_compatibility", "allowed_uses", "forbidden_uses", "phase_ids", "task_ids",
        "gate_ids", "protected_data_level", "copy_mode", "validation_mode",
        "research_equivalent", "savings",
    }
    seen: set[str] = set()
    for asset in assets:
        if not isinstance(asset, dict):
            raise AssetRegistryError("every asset must be a mapping")
        missing = sorted(required - set(asset))
        if missing:
            raise AssetRegistryError(f"asset is missing required fields: {missing}")
        asset_id = str(asset["asset_id"])
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9-]+", asset_id) or asset_id in seen:
            raise AssetRegistryError(f"invalid or duplicate asset_id: {asset_id}")
        seen.add(asset_id)
        if asset["disposition"] not in DISPOSITIONS:
            raise AssetRegistryError(f"{asset_id} has invalid disposition")
        if asset["copy_mode"] not in COPY_MODES or asset["validation_mode"] not in VALIDATION_MODES:
            raise AssetRegistryError(f"{asset_id} has invalid copy or validation mode")
        if asset["protected_data_level"] not in PROTECTED_LEVELS:
            raise AssetRegistryError(f"{asset_id} has invalid protected_data_level")
        compatibility = asset["protocol_compatibility"]
        if (
            not isinstance(compatibility, dict)
            or compatibility.get("status") not in COMPATIBILITY_STATUSES
            or not isinstance(compatibility.get("conditions"), list)
        ):
            raise AssetRegistryError(f"{asset_id} has invalid protocol compatibility")
        for field in ("allowed_uses", "forbidden_uses"):
            if not isinstance(asset[field], list) or not all(
                isinstance(item, str) and item.strip() for item in asset[field]
            ):
                raise AssetRegistryError(f"{asset_id} {field} must contain strings")
        task_ids = asset["task_ids"]
        if not isinstance(task_ids, list) or not task_ids:
            raise AssetRegistryError(f"{asset_id} must reference PLAN tasks")
        unknown_tasks = sorted(set(task_ids) - set(task_index))
        if unknown_tasks:
            raise AssetRegistryError(f"{asset_id} references unknown tasks: {unknown_tasks}")
        expected_phases = {task_index[task_id].phase_id for task_id in task_ids}
        if set(asset["phase_ids"]) != expected_phases:
            raise AssetRegistryError(f"{asset_id} phase_ids do not match task_ids")
        valid_gates = {task_index[task_id].gate_id for task_id in task_ids}
        if not asset["gate_ids"] or not set(asset["gate_ids"]) <= valid_gates:
            raise AssetRegistryError(f"{asset_id} gate_ids do not match task_ids")
        source = asset["source"]
        if not isinstance(source, dict) or source.get("repository") not in repositories:
            raise AssetRegistryError(f"{asset_id} references an unknown source repository")
        if source.get("commit") != repositories[source["repository"]]["commit"]:
            raise AssetRegistryError(f"{asset_id} source commit does not match repository commit")
        if asset_id == "APP-DAPFAM-CORE":
            _validate_huggingface_metadata(source.get("upstream_huggingface"))
        source_paths = source.get("paths")
        if not isinstance(source_paths, list) or not source_paths:
            raise AssetRegistryError(f"{asset_id} requires source paths")
        for entry in source_paths:
            _validate_source_entry(asset_id, entry)
        savings = asset["savings"]
        if not isinstance(savings, dict) or set(savings) != {"time", "compute", "storage"}:
            raise AssetRegistryError(f"{asset_id} savings must contain time, compute, and storage")

    gaps = payload.get("known_gaps", [])
    if not isinstance(gaps, list):
        raise AssetRegistryError("known_gaps must be a list")
    gap_ids: set[str] = set()
    for gap in gaps:
        if not isinstance(gap, dict) or not {"gap_id", "title", "task_ids", "reason"} <= set(gap):
            raise AssetRegistryError("known gap entries are incomplete")
        if gap["gap_id"] in gap_ids or not set(gap["task_ids"]) <= set(task_index):
            raise AssetRegistryError(f"invalid known gap: {gap['gap_id']}")
        gap_ids.add(gap["gap_id"])


def _validate_registry_v2(payload: dict[str, Any], root: Path) -> None:
    repositories = payload.get("source_repositories")
    if not isinstance(repositories, dict) or "app" not in repositories:
        raise AssetRegistryError("v2 source_repositories must include App pointer")
    app = repositories["app"]
    if not isinstance(app, dict) or not isinstance(app.get("root_hint"), str) or app.get("disposition") != "pointer_only":
        raise AssetRegistryError("v2 App source must be a pointer-only repository")
    assets = payload.get("assets")
    if not isinstance(assets, list) or not assets:
        raise AssetRegistryError("v2 assets must be a non-empty list")
    seen: set[str] = set()
    for asset in assets:
        if not isinstance(asset, dict):
            raise AssetRegistryError("v2 asset must be an object")
        required = {"asset_id", "title", "kind", "disposition", "copy_mode", "allowed_phases", "protected_data_level"}
        if not required <= set(asset):
            raise AssetRegistryError(f"v2 asset is missing fields: {sorted(required - set(asset))}")
        asset_id = str(asset["asset_id"])
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9-]+", asset_id) or asset_id in seen:
            raise AssetRegistryError(f"invalid or duplicate asset_id: {asset_id}")
        seen.add(asset_id)
        if asset["disposition"] not in DISPOSITIONS or asset["copy_mode"] not in COPY_MODES:
            raise AssetRegistryError(f"{asset_id} has invalid disposition or copy_mode")
        if not isinstance(asset["allowed_phases"], list) or any(not re.fullmatch(r"(?:P[0-4]|A[0-6])_[A-Z_]+", str(item)) for item in asset["allowed_phases"]):
            raise AssetRegistryError(f"{asset_id} has invalid phase scope")
        if not isinstance(asset["protected_data_level"], str):
            raise AssetRegistryError(f"{asset_id} has invalid protected_data_level")


def _validate_source_entry(asset_id: str, entry: Any) -> None:
    if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
        raise AssetRegistryError(f"{asset_id} source path entries must be mappings")
    _safe_relative_path(entry["path"])
    entry_type = entry.get("type", "file")
    if entry_type == "file":
        if not isinstance(entry.get("bytes"), int) or entry["bytes"] < 0:
            raise AssetRegistryError(f"{asset_id} file source requires bytes")
        if "sha256" in entry and not _is_sha256(str(entry["sha256"])):
            raise AssetRegistryError(f"{asset_id} file source has invalid SHA-256")
    elif entry_type == "directory":
        if (
            not isinstance(entry.get("manifest_path"), str)
            or not _is_sha256(str(entry.get("manifest_sha256", "")))
        ):
            raise AssetRegistryError(f"{asset_id} directory source requires a manifest closure")
        _safe_relative_path(entry["manifest_path"])
    else:
        raise AssetRegistryError(f"{asset_id} source entry has invalid type")


def _validate_huggingface_metadata(value: Any) -> None:
    required = {
        "dataset_id", "dataset_url", "revision", "license", "configs",
        "metadata_only", "live_fetch_allowed",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise AssetRegistryError("APP-DAPFAM-CORE requires complete Hugging Face metadata")
    if not _HF_DATASET_RE.fullmatch(str(value["dataset_id"])):
        raise AssetRegistryError("APP-DAPFAM-CORE Hugging Face dataset_id is invalid")
    expected_url = f"https://huggingface.co/datasets/{value['dataset_id']}"
    if value["dataset_url"] != expected_url:
        raise AssetRegistryError("APP-DAPFAM-CORE Hugging Face dataset_url is invalid")
    if not _GIT_COMMIT_RE.fullmatch(str(value["revision"]).casefold()):
        raise AssetRegistryError("APP-DAPFAM-CORE Hugging Face revision is invalid")
    if not isinstance(value["license"], str) or not value["license"].strip():
        raise AssetRegistryError("APP-DAPFAM-CORE Hugging Face license is invalid")
    if value["configs"] != ["corpus", "queries", "relations"]:
        raise AssetRegistryError("APP-DAPFAM-CORE Hugging Face configs are invalid")
    if value["metadata_only"] is not True or value["live_fetch_allowed"] is not False:
        raise AssetRegistryError("APP-DAPFAM-CORE upstream metadata must not authorize live fetch")


def query_assets(
    registry: dict[str, Any], *, asset_id: str | None = None,
    task_id: str | None = None, disposition: str | None = None,
) -> tuple[dict[str, Any], ...]:
    if disposition is not None and disposition not in DISPOSITIONS:
        raise AssetRegistryError(f"unknown disposition: {disposition}")
    selected = []
    for asset in registry["assets"]:
        if asset_id is not None and asset["asset_id"] != asset_id:
            continue
        if task_id is not None:
            if "task_ids" in asset:
                matches_task = task_id in asset["task_ids"]
            else:
                matches_task = str(task_id).split(".", 1)[0] in {str(item).split("_", 1)[0] for item in asset.get("allowed_phases", [])}
            if not matches_task:
                continue
        if disposition is not None and asset["disposition"] != disposition:
            continue
        selected.append(asset)
    return tuple(sorted(selected, key=lambda item: item["asset_id"]))


def render_asset_map(registry: dict[str, Any], root: Path) -> str:
    if registry.get("schema_version") == "myis.reusable-assets.v2":
        lines = ["# Reusable Asset Map", "", "| Asset | Kind | Disposition | Phases | Boundary |", "|---|---|---|---|---|"]
        for asset in query_assets(registry):
            boundary = str(asset.get("protected_data_level", ""))
            lines.append(f"| `{asset['asset_id']}` | {asset['kind']} | `{asset['disposition']}` | {', '.join(asset.get('allowed_phases', []))} | {boundary} |")
        return "\n".join(lines) + "\n"
    tasks = parse_plan_tasks(root / LEGACY_PLAN_RELATIVE_PATH)
    lines = [
        "# Reusable Asset Map",
        "",
        f"> Generated deterministically from {_TICK}control/assets/reusable_assets.yaml{_TICK}.",
        f"> Do not edit directly; run {_TICK}myis-assets map{_TICK}.",
        "",
        "## Phase And Task Coverage",
        "",
        "| Task | Purpose | Gate | Reusable assets |",
        "|---|---|---|---|",
    ]
    for task in tasks:
        assets = query_assets(registry, task_id=task.task_id)
        rendered = "; ".join(
            f"{_TICK}{asset['asset_id']}{_TICK} ({asset['disposition']}, {asset['copy_mode']})"
            for asset in assets
        ) or "none"
        lines.append(
            f"| {_TICK}{task.task_id}{_TICK} | {_escape_table(task.title)} | "
            f"{_TICK}{task.gate_id}{_TICK} | {rendered} |"
        )
    lines.extend(
        [
            "",
            "## Asset Catalog",
            "",
            "| Asset | Kind | Disposition | Compatibility | Copy | Savings |",
            "|---|---|---|---|---|---|",
        ]
    )
    for asset in query_assets(registry):
        savings = asset["savings"]
        saving_text = (
            f"time: {savings['time']}; compute: {savings['compute']}; "
            f"storage: {savings['storage']}"
        )
        lines.append(
            f"| {_TICK}{asset['asset_id']}{_TICK} | {_escape_table(asset['kind'])} | "
            f"{_TICK}{asset['disposition']}{_TICK} | "
            f"{_TICK}{asset['protocol_compatibility']['status']}{_TICK} | "
            f"{_TICK}{asset['copy_mode']}{_TICK} | {_escape_table(saving_text)} |"
        )
    lines.extend(["", "## Known Gaps", ""])
    for gap in sorted(registry.get("known_gaps", []), key=lambda item: item["gap_id"]):
        tasks_text = ", ".join(f"{_TICK}{task_id}{_TICK}" for task_id in gap["task_ids"])
        lines.append(f"- {_TICK}{gap['gap_id']}{_TICK} ({tasks_text}): {gap['title']} - {gap['reason']}")
    return "\n".join(lines) + "\n"


def validate_sources(
    registry: dict[str, Any], root: Path, *, mode: str,
    asset_ids: Iterable[str] | None = None, approval_record: Path | None = None,
    receipt: Path | None = None,
) -> ValidationReport:
    if mode not in {"quick", "full"}:
        raise AssetRegistryError("validation mode must be quick or full")
    if registry.get("schema_version") == "myis.reusable-assets.v2":
        selected = tuple(query_assets(registry, asset_id=None, disposition=None))
        if asset_ids:
            selected = tuple(item for item in selected if item["asset_id"] in set(asset_ids))
        return ValidationReport(mode, tuple(item["asset_id"] for item in selected), ("v2 pointer-only registry: protected source bytes remain in sibling App/Owner store",), ())
    selected_ids = set(asset_ids or ())
    assets = tuple(
        asset for asset in query_assets(registry)
        if not selected_ids or asset["asset_id"] in selected_ids
    )
    missing_ids = sorted(selected_ids - {asset["asset_id"] for asset in assets})
    if missing_ids:
        raise AssetRegistryError(f"unknown asset IDs: {missing_ids}")
    if mode == "full":
        for asset in assets:
            if asset["protected_data_level"] != "none":
                _assert_access_record(asset, approval_record=approval_record, receipt=receipt)

    warnings: list[str] = []
    errors: list[str] = []
    by_repo: dict[str, list[dict[str, Any]]] = {}
    for asset in assets:
        by_repo.setdefault(asset["source"]["repository"], []).append(asset)
    for repo_id, repo_assets in sorted(by_repo.items()):
        repo_spec = registry["source_repositories"][repo_id]
        source_root = (root / repo_spec["root_hint"]).resolve()
        current_head = _git_head(source_root)
        expected_head = repo_spec["commit"]
        if current_head and current_head != expected_head:
            registered_paths = [
                entry["path"] for asset in repo_assets for entry in asset["source"]["paths"]
            ]
            changed = _git_changed_paths(source_root, expected_head, current_head, registered_paths)
            if mode == "quick" and changed:
                errors.append(
                    f"{repo_id} registered paths changed since {expected_head}: {', '.join(changed)}"
                )
            else:
                warnings.append(
                    f"{repo_id} HEAD advanced from {expected_head} to {current_head}; "
                    "registered content checks continue"
                )
        for asset in repo_assets:
            for entry in asset["source"]["paths"]:
                _validate_source_material(asset["asset_id"], source_root, entry, mode, errors)
    return ValidationReport(
        mode,
        tuple(asset["asset_id"] for asset in assets),
        tuple(sorted(set(warnings))),
        tuple(sorted(set(errors))),
    )


def _validate_source_material(
    asset_id: str, source_root: Path, entry: dict[str, Any],
    mode: str, errors: list[str],
) -> None:
    path = _resolve_source_path(source_root, entry["path"])
    if entry.get("type", "file") == "file":
        if not path.is_file():
            errors.append(f"{asset_id}: missing file {entry['path']}")
            return
        observed_bytes = path.stat().st_size
        if observed_bytes != entry["bytes"]:
            errors.append(
                f"{asset_id}: byte drift for {entry['path']}: "
                f"{observed_bytes} != {entry['bytes']}"
            )
        if mode == "full" and entry.get("sha256") and _hash_file(path) != entry["sha256"]:
            errors.append(f"{asset_id}: SHA-256 drift for {entry['path']}")
        return
    if not path.is_dir():
        errors.append(f"{asset_id}: missing directory {entry['path']}")
        return
    manifest = _resolve_source_path(source_root, entry["manifest_path"])
    if not manifest.is_file():
        errors.append(f"{asset_id}: missing manifest {entry['manifest_path']}")
    elif mode == "full" and _hash_file(manifest) != entry["manifest_sha256"]:
        errors.append(f"{asset_id}: manifest SHA-256 drift for {entry['manifest_path']}")


def _assert_access_record(
    asset: dict[str, Any], *, approval_record: Path | None, receipt: Path | None,
) -> None:
    if approval_record is None and receipt is None:
        raise PermissionError(
            f"full validation of protected asset {asset['asset_id']} requires an approval record or receipt"
        )
    if approval_record is not None:
        payload = _load_record(approval_record)
        if (
            payload.get("schema_version") == "myis.owner-gate-decision.v2"
            and payload.get("status") == "approved"
            and payload.get("gate_id") in asset["gate_ids"]
        ):
            return
    if receipt is not None:
        payload = _load_record(receipt)
        if (
            payload.get("schema_version") == "myis.asset-access-receipt.v1"
            and payload.get("status") == "approved"
            and asset["asset_id"] in payload.get("asset_ids", [])
        ):
            return
    raise PermissionError(f"access record does not authorize protected asset {asset['asset_id']}")


def _load_record(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise PermissionError(f"cannot read access record: {error}") from error
    if not isinstance(payload, dict):
        raise PermissionError("access record must be a mapping")
    return payload


def _safe_relative_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise AssetRegistryError(f"unsafe repository-relative path: {value}")
    return path


def _resolve_source_path(source_root: Path, value: str) -> Path:
    relative = _safe_relative_path(value)
    resolved = source_root.joinpath(*relative.parts).resolve()
    try:
        resolved.relative_to(source_root)
    except ValueError as error:
        raise AssetRegistryError(f"source path escapes repository root: {value}") from error
    return resolved


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_head(root: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _git_changed_paths(root: Path, before: str, after: str, paths: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", before, after, "--", *paths],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return sorted(
        line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()
    )


def _is_sha256(value: str) -> bool:
    return bool(_SHA256_RE.fullmatch(value.casefold()))


def _escape_table(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
