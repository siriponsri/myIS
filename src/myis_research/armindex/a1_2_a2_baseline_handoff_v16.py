"""Build an Owner-local A1 baseline handoff for later A2 preparation.

The handoff copies only the validated A1 safe-return archive and aggregate
evaluation receipts. Dense embeddings, indexes, caches, checkpoints, raw
inputs, logs, and provider payloads are deliberately excluded.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..kernel.canonical import canonical_json, canonical_sha256, file_sha256
from .a1_2_evaluator_closeout_v16 import (
    RECEIPT_NAME,
    validate_evaluator_closeout_inputs,
    validate_evaluator_closeout_receipt,
)

MANIFEST_NAME = "handoff-manifest.v16.json"
FORBIDDEN_ARTIFACT_CLASSES = (
    "caches",
    "dense_embeddings",
    "environment_dumps",
    "logs",
    "model_weights",
    "provider_payloads",
    "raw_inputs",
    "tensor_checkpoints",
    "vector_indexes",
)


class A1A2BaselineHandoffV16Error(ValueError):
    """Raised when an A1-to-A2 Owner-local handoff is unsafe or incomplete."""


def _load_object(path: Path, *, role: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise A1A2BaselineHandoffV16Error(f"{role} is missing or unsafe")
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A1A2BaselineHandoffV16Error(f"{role} is invalid") from error
    if not isinstance(value, dict):
        raise A1A2BaselineHandoffV16Error(f"{role} must be a JSON object")
    return value


def _copy_regular(source: Path, destination: Path, *, role: str) -> dict[str, Any]:
    if not source.is_file() or source.is_symlink():
        raise A1A2BaselineHandoffV16Error(f"{role} is missing or unsafe")
    source_sha256 = file_sha256(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    destination_sha256 = file_sha256(destination)
    if destination_sha256 != source_sha256:
        raise A1A2BaselineHandoffV16Error(f"{role} changed during copy")
    return {
        "role": role,
        "relative_path": destination.as_posix(),
        "sha256": destination_sha256,
        "size_bytes": destination.stat().st_size,
    }


def _manifest_payload(manifest: Mapping[str, Any]) -> str:
    return canonical_json(dict(manifest)) + "\n"


def build_a1_a2_baseline_handoff(
    *,
    repository_root: Path,
    safe_return_archive: Path,
    evaluation_attempt_root: Path,
    output_root: Path,
    remote_root_label: str,
) -> dict[str, Any]:
    """Copy the minimal validated A1 baseline package to an Owner-local root."""

    repository = repository_root.resolve(strict=True)
    archive = safe_return_archive.resolve(strict=True)
    evaluation = evaluation_attempt_root.resolve(strict=True)
    output = output_root.resolve(strict=False)
    if archive.is_symlink() or not archive.is_file():
        raise A1A2BaselineHandoffV16Error("safe-return archive is missing or unsafe")
    if evaluation.is_symlink() or not evaluation.is_dir():
        raise A1A2BaselineHandoffV16Error("evaluation attempt root is missing or unsafe")
    if output == repository or output.is_relative_to(repository):
        raise A1A2BaselineHandoffV16Error("A2 baseline handoff must remain outside the repository")
    if output.exists():
        raise A1A2BaselineHandoffV16Error("A2 baseline handoff output already exists")
    if not remote_root_label.startswith("/opt/myis/") or "\n" in remote_root_label:
        raise A1A2BaselineHandoffV16Error("remote root label is invalid")

    validated = validate_evaluator_closeout_inputs(repository, evaluation)
    if validated.get("cell_receipt_count") != 25:
        raise A1A2BaselineHandoffV16Error("A1 aggregate receipt set is not 25/25")
    archive_sha256 = file_sha256(archive)
    if validated.get("safe_return_archive_sha256") != archive_sha256:
        raise A1A2BaselineHandoffV16Error("safe-return archive hash differs from evaluation lineage")

    closeout_path = evaluation / RECEIPT_NAME
    closeout = validate_evaluator_closeout_receipt(
        repository,
        _load_object(closeout_path, role="evaluator closeout receipt"),
    )
    if closeout.get("safe_return_archive_sha256") != archive_sha256:
        raise A1A2BaselineHandoffV16Error("evaluator closeout does not bind the safe-return archive")

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    try:
        copied: list[dict[str, Any]] = []
        copied.append(
            _copy_regular(
                archive,
                temporary / "safe-return" / "safe-return.tar.gz",
                role="validated_safe_return_archive",
            )
        )
        receipt_root = evaluation / "receipts"
        for source in sorted(receipt_root.glob("*.json")):
            copied.append(
                _copy_regular(
                    source,
                    temporary / "aggregate" / "receipts" / source.name,
                    role="aggregate_cell_receipt",
                )
            )
        copied.append(
            _copy_regular(
                evaluation / "promotion.json",
                temporary / "aggregate" / "promotion.json",
                role="aggregate_promotion_receipt",
            )
        )
        copied.append(
            _copy_regular(
                closeout_path,
                temporary / "aggregate" / RECEIPT_NAME,
                role="aggregate_evaluator_closeout_receipt",
            )
        )
        if len(copied) != 28:
            raise A1A2BaselineHandoffV16Error("A2 baseline handoff must contain exactly 28 source files")

        revalidated = validate_evaluator_closeout_inputs(repository, evaluation)
        revalidated_closeout = validate_evaluator_closeout_receipt(
            repository,
            _load_object(closeout_path, role="evaluator closeout receipt"),
        )
        if revalidated != validated or revalidated_closeout != closeout:
            raise A1A2BaselineHandoffV16Error("A1 evaluation artifacts changed during handoff")
        if file_sha256(archive) != archive_sha256:
            raise A1A2BaselineHandoffV16Error("safe-return archive changed during handoff")

        relative_files = []
        for item in copied:
            relative = Path(item["relative_path"]).relative_to(temporary).as_posix()
            relative_files.append({**item, "relative_path": relative})
        body: dict[str, Any] = {
            "schema_version": "myis.armindex-a1.2-a2-baseline-handoff.v16",
            "handoff_id": f"{validated['attempt_id']}-a2-baseline-handoff-v16",
            "attempt_id": validated["attempt_id"],
            "status": "PASS",
            "evidence_class": "owner_local_protected_handoff",
            "scientific_authority": False,
            "claim_boundary": (
                "Owner-local A1 baseline package for later A2 preparation only; "
                "it does not authorize A2 execution or expose protected evaluation inputs."
            ),
            "remote_a1_root_label": remote_root_label,
            "remote_artifact_retention_required": True,
            "safe_return_archive_sha256": archive_sha256,
            "evaluation_lineage_sha256": validated["evaluation_lineage_sha256"],
            "cell_receipt_count": validated["cell_receipt_count"],
            "cell_receipt_set_sha256": validated["cell_receipt_set_sha256"],
            "promotion_receipt_sha256": validated["promotion_receipt_sha256"],
            "evaluator_closeout_receipt_sha256": closeout["receipt_sha256"],
            "promoted_arm_ids": validated["promoted_arm_ids"],
            "copied_file_count": len(relative_files),
            "copied_files": sorted(relative_files, key=lambda item: item["relative_path"]),
            "forbidden_artifact_classes_excluded": list(FORBIDDEN_ARTIFACT_CLASSES),
            "a2_execution_authorized": False,
        }
        body["manifest_sha256"] = canonical_sha256(body)
        (temporary / MANIFEST_NAME).write_text(_manifest_payload(body), encoding="ascii", newline="")
        os.replace(temporary, output)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return body


def main() -> int:
    parser = argparse.ArgumentParser(prog="myis-a1.2-a2-baseline-handoff-v16")
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--safe-return-archive", required=True, type=Path)
    parser.add_argument("--evaluation-attempt-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--remote-root-label", required=True)
    args = parser.parse_args()
    try:
        result = build_a1_a2_baseline_handoff(
            repository_root=args.repository_root,
            safe_return_archive=args.safe_return_archive,
            evaluation_attempt_root=args.evaluation_attempt_root,
            output_root=args.output_root,
            remote_root_label=args.remote_root_label,
        )
    except (A1A2BaselineHandoffV16Error, OSError, ValueError) as error:
        parser.error(str(error))
    print(
        canonical_json(
            {
                "status": result["status"],
                "attempt_id": result["attempt_id"],
                "copied_file_count": result["copied_file_count"],
                "manifest_sha256": result["manifest_sha256"],
                "a2_execution_authorized": False,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "FORBIDDEN_ARTIFACT_CLASSES",
    "MANIFEST_NAME",
    "A1A2BaselineHandoffV16Error",
    "build_a1_a2_baseline_handoff",
    "main",
]
