"""Build the protected, aggregate-safe Selection-125 evaluator handoff.

This command never writes qrels, membership, rankings, or metric vectors to
the repository.  Its output root must be a fresh child of Owner Store and is
consumed by ``run_a4_selection_owner_local.py`` exactly once.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from myis_research.armindex.a4_selection_evaluator import build_selection_handoff
from myis_research.kernel.canonical import canonical_json


def _json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _bindings(values: list[str], *, name: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in values:
        label, separator, value = item.partition("=")
        if not separator or not label or not value or label in result:
            raise ValueError(f"{name} must use unique LABEL=VALUE bindings")
        result[label] = value
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection-input-root", type=Path, required=True)
    parser.add_argument("--evaluator-input-root", type=Path, required=True)
    parser.add_argument("--package", action="append", required=True, help="LABEL=ranking-package.json")
    parser.add_argument("--system", action="append", required=True, help="LABEL=system SHA-256")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--owner-store-root", type=Path, required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--evaluator-handoff-sha256", required=True)
    parser.add_argument("--comparison-family-id", default="a4-selection-frozen-finalists-v1")
    parser.add_argument("--bootstrap-seed", type=int, default=42)
    parser.add_argument("--selection-scope-sha256")
    args = parser.parse_args()
    owner = args.owner_store_root.resolve(strict=True)
    for path in (args.selection_input_root, args.evaluator_input_root, args.output_root):
        resolved = path.resolve()
        if resolved != owner and owner not in resolved.parents:
            raise ValueError(f"path is outside Owner Store: {path}")
        if path.is_symlink():
            raise ValueError(f"path cannot be a symlink: {path}")
    package_paths = _bindings(args.package, name="package")
    systems = _bindings(args.system, name="system")
    if set(package_paths) != set(systems):
        raise ValueError("package and system labels must match")
    packages = {label: _json(Path(path).resolve(strict=True)) for label, path in package_paths.items()}
    receipt = build_selection_handoff(
        selection_input_root=args.selection_input_root,
        evaluator_input_root=args.evaluator_input_root,
        packages=packages,
        systems=systems,
        output_root=args.output_root,
        attempt_id=args.attempt_id,
        evaluator_handoff_sha256=args.evaluator_handoff_sha256,
        comparison_family_id=args.comparison_family_id,
        bootstrap_seed=args.bootstrap_seed,
        expected_selection_scope_sha256=args.selection_scope_sha256,
    )
    print(canonical_json({
        "status": receipt["status"],
        "attempt_id": receipt["attempt_id"],
        "selection_query_count": receipt["selection_query_count"],
        "out_query_count": receipt["out_query_count"],
        "comparison_count": receipt["comparison_count"],
        "receipt_sha256": receipt["receipt_sha256"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
