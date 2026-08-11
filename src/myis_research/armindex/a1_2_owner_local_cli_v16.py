"""Owner-local CLI wrappers kept outside the frozen v16 execution bundle."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from .a1_2_owner_local_evaluator_v16 import (
    OwnerLocalEvaluatorV16Error,
    evaluate_safe_return,
)
from .a1_2_owner_local_input_manifest_v16 import (
    OwnerLocalInputManifestV16Error,
    build_input_manifest,
)


def _directory(path: Path, *, role: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise ValueError(f"{role} is unavailable") from error
    if path.is_symlink() or not resolved.is_dir():
        raise ValueError(f"{role} is unsafe")
    return resolved


def _regular_file(path: Path, *, role: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise ValueError(f"{role} is unavailable") from error
    if path.is_symlink() or not resolved.is_file():
        raise ValueError(f"{role} is unsafe")
    return resolved


def _relative_file(root: Path, relative: str, *, role: str) -> Path:
    candidate = Path(relative)
    if not relative or candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"{role} path is unsafe")
    resolved = _regular_file(root / candidate, role=role)
    if not resolved.is_relative_to(root):
        raise ValueError(f"{role} path is unsafe")
    return resolved


def _relative_output(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if not relative or candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("output path is unsafe")
    target = root / candidate
    parent = target.parent
    while not parent.exists():
        parent = parent.parent
    parent = _directory(parent, role="output parent")
    resolved = target.resolve(strict=False)
    if not parent.is_relative_to(root) or not resolved.is_relative_to(root) or (target.exists() and target.is_symlink()):
        raise ValueError("output path is unsafe")
    return resolved


def _json_file(root: Path, relative: str, *, role: str, expected: type[object]) -> object:
    path = _relative_file(root, relative, role=role)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{role} is not valid JSON") from error
    if not isinstance(value, expected):
        raise TypeError(f"{role} has an invalid JSON shape")
    return value


def input_manifest_main(argv: Sequence[str] | None = None) -> int:
    """Materialize a v16 input manifest from Owner-local relative paths."""

    parser = argparse.ArgumentParser(prog="myis-a1.2-owner-input-manifest-v16")
    parser.add_argument("--owner-root", required=True, type=Path)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--gates-json-relative", required=True)
    parser.add_argument("--cells-json-relative", required=True)
    parser.add_argument("--work-token-relative", required=True)
    parser.add_argument("--output-relative", required=True)
    args = parser.parse_args(argv)
    try:
        root = _directory(args.owner_root, role="Owner-local root")
        gates = _json_file(root, args.gates_json_relative, role="gates", expected=dict)
        cells = _json_file(root, args.cells_json_relative, role="cells", expected=list)
        _relative_file(root, args.work_token_relative, role="work-token")
        result = build_input_manifest(
            root=root,
            output=_relative_output(root, args.output_relative),
            attempt_id=args.attempt_id,
            gates=gates,
            work_token_path=args.work_token_relative,
            cells=cells,
        )
    except (OwnerLocalInputManifestV16Error, TypeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


def evaluator_main(argv: Sequence[str] | None = None) -> int:
    """Evaluate one safe return while preserving the Owner-local boundary."""

    parser = argparse.ArgumentParser(prog="myis-a1.2-owner-evaluator-v16")
    parser.add_argument("--owner-root", required=True, type=Path)
    parser.add_argument("--evaluation-manifest", required=True, type=Path)
    parser.add_argument("--safe-return-archive", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--repository-root", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        owner_root = _directory(args.owner_root, role="Owner-local root")
        repository_root = _directory(args.repository_root, role="repository root")
        manifest = _regular_file(args.evaluation_manifest, role="evaluation manifest")
        archive = _regular_file(args.safe_return_archive, role="safe-return archive")
        if manifest.parent != owner_root:
            raise ValueError("evaluation manifest must be directly inside Owner-local root")
        output = args.output_root.resolve(strict=False)
        output_parent = _directory(args.output_root.parent, role="aggregate output parent")
        if (args.output_root.exists() and args.output_root.is_symlink()) or not output_parent.is_dir() or output.is_relative_to(owner_root) or output.is_relative_to(repository_root):
            raise ValueError("aggregate output must be a separate Owner-local directory")
        result = evaluate_safe_return(archive, manifest, output_root=output, repository_root=repository_root)
    except (OwnerLocalEvaluatorV16Error, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


__all__ = ["evaluator_main", "input_manifest_main"]
