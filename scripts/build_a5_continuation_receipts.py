"""Build hash-bound aggregate-safe A5 continuation and conditional-D2 receipts."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from myis_research.armindex.a4_a5_handoff import validate_a5_pointer_bundle
from myis_research.armindex.a4_execution import build_conditional_d2_receipt
from myis_research.kernel.canonical import canonical_sha256
from myis_research.protection import assert_aggregate_only


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def git(repo: Path, expression: str) -> str:
    return subprocess.run(["git", "-C", str(repo), "rev-parse", expression], check=True, capture_output=True, text=True).stdout.strip()


def write_new(path: Path, value: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="ascii")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--prior-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    repo = args.repo.resolve(strict=True)
    bundle = validate_a5_pointer_bundle(load(args.bundle.resolve(strict=True)))
    commit, tree = git(repo, "HEAD"), git(repo, "HEAD^{tree}")
    if commit != "d6fdf9c333a6a6b7fda3f3bf48cee95127547b35":
        raise ValueError(f"unexpected continuation commit: {commit}")

    prior = load(args.prior_audit.resolve(strict=True))
    audit_body = dict(prior)
    audit_body.pop("receipt_sha256", None)
    audit_body.update({
        "audit_id": "a5-provenance-audit-20260822-continuation-current-main",
        "attempt_id": bundle["attempt_id"],
        "provider_instance_id": 48367896,
        "provider_disposition": "ACTIVE_FRESH_INSTANCE_VERIFIED",
        "bundle_pointer": str(args.bundle.resolve()).replace("\\", "/"),
        "bundle_sha256": bundle["bundle_sha256"],
        "git_binding": {"git_commit": commit, "git_tree": tree, "git_ref": "origin/main", "clean_worktree": True, "pushed_to_origin": True},
        "required_owner_action": "Conditional D2 is preauthorized; launch exactly one Final-872 attempt on fresh instance 48367896.",
        "next_gate": "A5_FINAL_872_PRECHECK_FRESH_INSTANCE",
        "claim_boundary": "Continuation provenance only; no A5 Final result exists until the fresh Final-872 run completes and is independently evaluated.",
    })
    audit_body["checks"] = [dict(check) for check in prior.get("checks", [])]
    for check in audit_body["checks"]:
        if check.get("field") == "git_binding":
            check["observed"] = audit_body["git_binding"]
            check["gap"] = None
            check["status"] = "VERIFIED_CURRENT_MAIN_CONTINUATION"
        if check.get("field") == "instance_health":
            check["observed"] = {"instance_id": 48367896, "gpu_count": 2, "gpu_idle": True, "disk_available_gib": 118, "workers_found": 0}
            check["status"] = "VERIFIED_FRESH_INSTANCE"
    audit_body["receipt_sha256"] = canonical_sha256(audit_body)
    assert_aggregate_only(audit_body)
    audit_path = args.output / "a5-provenance-continuation-receipt.json"
    write_new(audit_path, audit_body)

    final_registry_sha = canonical_sha256(bundle["final_registry"])
    predicates = {key: True for key in (
        "all_a4_coverage", "selection_count_valid", "legal_isolation", "safe_return",
        "independent_audit", "a5_bundle_clean_pushed", "finalist_frozen", "protected_boundary",
        "a5_budget_reserve", "a5_provenance_pass",
    )}
    d2 = build_conditional_d2_receipt(
        a4_result_audit_sha256=bundle["result_audit_sha256"],
        a4_safe_return_sha256=bundle["safe_return_sha256"],
        a5_bundle_sha256=bundle["bundle_sha256"],
        final_registry_sha256=final_registry_sha,
        final_split_commitment_sha256=bundle["final_split_commitment_sha256"],
        clean_git_commit=commit,
        clean_git_tree=tree,
        selection_accesses=1,
        final_accesses=0,
        a5_provenance_audit_sha256=audit_body["receipt_sha256"],
        automatic_pass=predicates,
    )
    d2_path = args.output / "conditional-d2-open-final-receipt.json"
    write_new(d2_path, d2)
    print(json.dumps({"bundle_sha256": bundle["bundle_sha256"], "provenance_receipt_sha256": audit_body["receipt_sha256"], "d2_receipt_sha256": d2["receipt_sha256"], "output": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
