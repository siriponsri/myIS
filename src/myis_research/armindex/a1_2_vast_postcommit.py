"""Post-commit validator for the additive A1.2 Vast four-GPU preflight."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256, file_sha256
from .a1_2_vast import (
    A12VastError,
    build_frozen_bundle,
    validate_complete_sha256s,
    validate_preparation_receipt,
)


REVISION_ID = "a1.2-local-vast-4x3090-postcommit-v3"
RECEIPT_PATH = Path(
    "campaigns/armindex-multiretriever-v2/evidence/"
    "a1.2-vast-4x3090-postcommit-migration.receipt.v3.json"
)
CONTRACT_PATH = Path("control/armindex/a1.2/execution-contract.v3.json")
SCHEMA_PATH = Path("schemas/armindex/a1.2-vast-4x3090-postcommit.v3.json")
_GIT_ID_RE = re.compile(r"^[a-f0-9]{40,64}$")


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n"


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def validate_postcommit_revision(
    repository_root: Path,
    *,
    require_clean: bool = True,
) -> dict[str, Any]:
    root = repository_root.resolve()
    receipt = json.loads((root / RECEIPT_PATH).read_text(encoding="utf-8"))
    schema = json.loads((root / SCHEMA_PATH).read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(
            schema,
            format_checker=Draft202012Validator.FORMAT_CHECKER,
        ).iter_errors(receipt),
        key=lambda error: list(error.path),
    )
    if errors:
        raise A12VastError(f"v3 post-commit receipt schema failure: {errors[0].message}")
    body = dict(receipt)
    digest = body.pop("receipt_sha256", None)
    if digest != canonical_sha256(body):
        raise A12VastError("v3 post-commit receipt self-hash mismatch")
    for binding in receipt["bindings"]:
        if file_sha256(root / binding["uri"]) != binding["sha256"]:
            raise A12VastError(f"v3 post-commit binding mismatch: {binding['uri']}")

    v2_receipt = validate_preparation_receipt(root)
    if v2_receipt.get("receipt_sha256") != receipt["v2_receipt_sha256"]:
        raise A12VastError("v3 does not bind the validated v2 preparation receipt")
    contract = json.loads((root / CONTRACT_PATH).read_text(encoding="utf-8"))
    budget = contract.get("budget", {})
    if (
        contract.get("launch_allowed") is not False
        or contract.get("adopted_for_execution") is not False
        or any(contract.get("real_counters", {}).values())
        or any(contract.get("resource_counters", {}).values())
    ):
        raise A12VastError("v3 post-commit correction cannot authorize execution")
    if budget != receipt.get("budget") or budget != {
        "planning_rate_usd_per_four_gpu_instance_hour": 0.6,
        "estimated_instance_hours": "2-4",
        "estimated_raw_worker_usd": "1.20-2.40",
        "common_screen_hard_stop_usd": 18,
        "a1_hard_stop_usd": 23,
        "campaign_hard_stop_usd": 100,
        "live_quote_required": True,
        "over_hard_stop_status": "BLOCKED_BUDGET",
    }:
        raise A12VastError("v3 price, estimate, or hard-stop binding mismatch")

    if require_clean and _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise A12VastError("repository must be clean for post-commit validation")
    commit = _git(root, "rev-parse", "HEAD^{commit}")
    tree = _git(root, "rev-parse", "HEAD^{tree}")
    if not _GIT_ID_RE.fullmatch(commit) or not _GIT_ID_RE.fullmatch(tree):
        raise A12VastError("current Git commit or tree identity is invalid")
    return {
        "schema_version": "myis.armindex-a1.2-vast-postcommit-validation.v3",
        "revision_id": REVISION_ID,
        "status": "prepared_postcommit_launch_locked",
        "git_commit": commit,
        "git_tree": tree,
        "repository_clean": not bool(
            _git(root, "status", "--porcelain=v1", "--untracked-files=all")
        ),
        "v2_receipt_sha256": v2_receipt["receipt_sha256"],
        "launch_allowed": False,
        "adopted_for_execution": False,
        "measured_execution": False,
        "gpu_reserved": False,
        "charged_usd": 0,
        "planning_rate_usd_per_four_gpu_instance_hour": 0.6,
        "estimated_instance_hours": "2-4",
        "estimated_raw_worker_usd": "1.20-2.40",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myis-a1.2-vast-postcommit")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--repository-root", type=Path, default=Path.cwd())
    bundle = sub.add_parser("build-frozen-bundle")
    bundle.add_argument("--repository-root", type=Path, default=Path.cwd())
    bundle.add_argument("--output", type=Path, required=True)
    bundle.add_argument("--image-digest", required=True)
    sums = sub.add_parser("validate-sha256s")
    sums.add_argument("--directory", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "validate":
        print(_json_text(validate_postcommit_revision(args.repository_root)), end="")
        return 0
    if args.command == "build-frozen-bundle":
        validate_postcommit_revision(args.repository_root)
        print(
            _json_text(
                build_frozen_bundle(
                    args.repository_root,
                    args.output,
                    args.image_digest,
                )
            ),
            end="",
        )
        return 0
    if args.command == "validate-sha256s":
        print(_json_text(validate_complete_sha256s(args.directory)), end="")
        return 0
    raise A12VastError("unsupported command")


if __name__ == "__main__":
    raise SystemExit(main())
