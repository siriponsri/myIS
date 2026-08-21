"""Rebuild an immutable A5 pointer bundle after aggregate-safe A4 closeout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from typing import Any

from myis_research.armindex.a4_a5_handoff import build_a5_pointer_bundle, validate_a5_pointer_bundle
from myis_research.kernel.canonical import canonical_json, file_sha256


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _git(repo: Path, expression: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", expression],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--closeout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source = validate_a5_pointer_bundle(_load(args.source.resolve(strict=True)))
    closeout = args.closeout.resolve(strict=True)
    coverage = _load(closeout / "A4_SELECTION_COVERAGE.json")
    safe = _load(closeout / "A4_SELECTION_SAFE_RETURN.json")
    audit = _load(closeout / "A4_SELECTION_RESULT_INTEGRITY_AUDIT.json")
    final = dict(source)
    final.pop("bundle_sha256", None)
    final.update(
        {
            "a4_coverage_sha256": coverage["receipt_sha256"],
            "result_audit_sha256": audit["audit_sha256"],
            "safe_return_sha256": safe["receipt_sha256"],
            "safe_export_manifest_sha256": safe["receipt_sha256"],
            "git_commit": _git(args.repo.resolve(strict=True), "HEAD"),
            "git_tree": _git(args.repo.resolve(strict=True), "HEAD^{tree}"),
            "clean_worktree": True,
            "pushed_to_origin": True,
        }
    )
    bundle = build_a5_pointer_bundle(
        attempt_id=final["attempt_id"],
        a4_coverage_sha256=final["a4_coverage_sha256"],
        selection_receipt_sha256=final["selection_receipt_sha256"],
        result_audit_sha256=final["result_audit_sha256"],
        safe_return_sha256=final["safe_return_sha256"],
        final_split_commitment_sha256=final["final_split_commitment_sha256"],
        final_input_pointer=final["final_input_pointer"],
        evaluator_handoff_sha256=final["evaluator_handoff_sha256"],
        evaluator_handoff_pointer=final["evaluator_handoff_pointer"],
        safe_export_manifest_sha256=final["safe_export_manifest_sha256"],
        git_commit=final["git_commit"],
        git_tree=final["git_tree"],
        git_ref=final["git_ref"],
        clean_worktree=final["clean_worktree"],
        pushed_to_origin=final["pushed_to_origin"],
        a5_reserved_usd=final["a5_reserved_usd"],
        finalists=final["final_registry"],
        statistical_plan=final["statistical_plan"],
    )
    output = args.output.resolve()
    if output.exists() or output.is_symlink():
        raise SystemExit(f"refusing to overwrite {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(canonical_json(bundle) + "\n", encoding="utf-8")
    print(json.dumps({"bundle_sha256": bundle["bundle_sha256"], "output_sha256": file_sha256(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
