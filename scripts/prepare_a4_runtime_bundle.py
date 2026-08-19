"""Build the hash-closed local A4 profile registry and runtime package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from myis_research.armindex.a4_asset_bundle import (
    build_a4_hdev_runtime_package,
    validate_a4_hdev_runtime_package,
)
from myis_research.armindex.a4_execution import (
    build_profile_registry,
    validate_a4_predecessor_binding,
)
from myis_research.armindex.a4_hdev_materializer import validate_a4_hdev_handoff
from myis_research.kernel.canonical import canonical_json, canonical_sha256


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def _registry(attempt_id: str, predecessor: dict[str, Any], hdev_sha: str) -> dict[str, Any]:
    evaluator = canonical_sha256(
        {
            "schema_version": "myis.armindex-a4-evaluator.v1",
            "primary_metric": "recall_at_100_out",
            "secondary_metrics": ["ndcg_at_100_out", "ndcg_at_10_out"],
            "bootstrap_resamples": 10000,
            "confidence_level": 0.95,
            "tie_policy": "stable_lexical_family_id",
        }
    )
    runtime = canonical_sha256(
        {
            "schema_version": "myis.armindex-a4-runtime-contract.v1",
            "python": "3.11",
            "pytorch": "2.6.0+cu118",
            "output_depth": 100,
            "attempt_id": attempt_id,
        }
    )
    license_binding = canonical_sha256(
        {
            "schema_version": "myis.armindex-a4-license-binding.v1",
            "commercial_arms": ["ARM-01", "ARM-02", "ARM-04", "ARM-05"],
            "research_only_arms": ["ARM-03"],
        }
    )
    profiles = [
        {
            "profile_id": "FAST",
            "system_sha256": canonical_sha256({"profile": "FAST", "arms": ["ARM-01", "ARM-04"], "mode": "synchronous", "depth": 100}),
            "arm_ids": ["ARM-01", "ARM-04"],
            "mode": "synchronous",
            "candidate_depth": 100,
            "commercial_only": True,
        },
        {
            "profile_id": "BALANCED",
            "system_sha256": canonical_sha256({"profile": "BALANCED", "arms": ["ARM-01", "ARM-04", "ARM-05"], "mode": "synchronous", "depth": 100}),
            "arm_ids": ["ARM-01", "ARM-04", "ARM-05"],
            "mode": "synchronous",
            "candidate_depth": 100,
            "commercial_only": True,
        },
        {
            "profile_id": "DEEP",
            "system_sha256": canonical_sha256({"profile": "DEEP", "arms": ["ARM-01", "ARM-04", "ARM-05"], "mode": "asynchronous", "depth": 100}),
            "arm_ids": ["ARM-01", "ARM-04", "ARM-05"],
            "mode": "asynchronous",
            "candidate_depth": 100,
            "commercial_only": True,
        },
    ]
    return build_profile_registry(
        attempt_id=attempt_id,
        predecessor_binding_sha256=predecessor["binding_sha256"],
        hdev_commitment_sha256=hdev_sha,
        evaluator_binding_sha256=evaluator,
        runtime_binding_sha256=runtime,
        license_binding_sha256=license_binding,
        profiles=profiles,
        research_reference={
            "system_sha256": predecessor["winner_program_sha256s"]["ARM-03"],
            "arm_ids": ["ARM-03"],
            "license_scope": "research_only",
            "label": "ARM-03_RESEARCH_REFERENCE",
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--predecessor-binding", type=Path, required=True)
    parser.add_argument("--hdev-handoff", type=Path, required=True)
    parser.add_argument("--source-assets", type=Path, required=True)
    parser.add_argument("--train-package", type=Path, required=True)
    parser.add_argument("--split-membership", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    predecessor = validate_a4_predecessor_binding(json.loads(args.predecessor_binding.read_text(encoding="utf-8")))
    handoff = validate_a4_hdev_handoff(args.hdev_handoff, expected_attempt_id=args.attempt_id)
    registry = _registry(args.attempt_id, predecessor, handoff["receipt_sha256"])
    package = build_a4_hdev_runtime_package(
        source_assets_root=args.source_assets,
        train_package_root=args.train_package,
        split_membership_path=args.split_membership,
        output_root=args.output,
        attempt_id=args.attempt_id,
        predecessor_binding=predecessor,
        profile_registry=registry,
        hdev_handoff_root=args.hdev_handoff,
    )
    checked = validate_a4_hdev_runtime_package(args.output, expected_attempt_id=args.attempt_id)
    _write_json(args.output / "profile-registry.json", registry)
    print({"status": package["status"], "receipt_sha256": checked["receipt_sha256"], "registry_sha256": registry["registry_sha256"]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
