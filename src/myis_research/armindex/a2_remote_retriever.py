"""Remote-only retrieval half of the protected A2 measured executor."""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ..kernel.canonical import canonical_sha256, file_sha256
from .a1_2_measured_executor_v16 import DENSE_ARM_IDS, SentenceTransformerDenseAdapter
from .a2_execution_readiness import frozen_candidates
from .a2_measured_adapter import _verify_model_manifest, frozen_program_for_candidate
from .a2_owner_local_engine import _corpus_rows, _queries, _rank_arm01, _rank_dense
from .a2_program_runtime import compile_program


class A2RemoteRetrieverError(ValueError):
    """Raised without returning remote payload details."""


def _load_manifest(path: Path, repository_root: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.resolve(strict=True).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A2RemoteRetrieverError("remote retrieval manifest is invalid") from error
    if not isinstance(manifest, dict):
        raise A2RemoteRetrieverError("remote retrieval manifest is invalid")
    body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if (
        manifest.get("schema_version") != "myis.armindex-a2-remote-retrieval-input.v1"
        or manifest.get("status") != "READY_REMOTE_RETRIEVAL_ONLY"
        or manifest.get("manifest_sha256") != canonical_sha256(body)
        or any(name in manifest for name in ("qrels", "membership", "evaluator"))
    ):
        raise A2RemoteRetrieverError("remote retrieval manifest boundary drift")
    for name in ("corpus", "queries"):
        item = manifest.get(name)
        if not isinstance(item, Mapping):
            raise A2RemoteRetrieverError("remote retrieval input is invalid")
        file = Path(str(item.get("path", "")))
        if not file.is_absolute() or file.is_symlink() or file_sha256(file.resolve(strict=True)) != item.get("sha256"):
            raise A2RemoteRetrieverError("remote retrieval input hash drift")
    expected_arms = {"ARM-02", "ARM-03", "ARM-04", "ARM-05"}
    if set(manifest.get("model_directories", {})) != expected_arms or set(manifest.get("model_manifests", {})) != expected_arms:
        raise A2RemoteRetrieverError("remote model binding set is incomplete")
    for arm_id in expected_arms:
        model_root = Path(manifest["model_directories"][arm_id]).resolve(strict=True)
        model_manifest = Path(manifest["model_manifests"][arm_id]).resolve(strict=True)
        _verify_model_manifest(
            repository_root,
            arm_id=arm_id,
            model_root=model_root,
            manifest_path=model_manifest,
        )
    return manifest


def run_remote_retriever(
    repository_root: Path,
    *,
    manifest_path: Path,
    candidate_id: str,
) -> dict[str, Any]:
    root = repository_root.resolve()
    manifest = _load_manifest(manifest_path, root)
    candidate = frozen_candidates(root).get(candidate_id)
    if not isinstance(candidate, Mapping):
        raise A2RemoteRetrieverError("candidate is outside frozen membership")
    if (
        os.environ.get("MYIS_A2_ARM_ID") != candidate["arm_id"]
        or os.environ.get("MYIS_A2_PROGRAM_SHA256") != candidate["program_sha256"]
        or manifest.get("attempt_id") != os.environ.get("MYIS_A2_ATTEMPT_ID")
    ):
        raise A2RemoteRetrieverError("remote candidate environment drift")
    program = frozen_program_for_candidate(root, candidate_id)
    corpus = _corpus_rows(Path(manifest["corpus"]["path"]), program)
    queries = _queries(Path(manifest["queries"]["path"]))
    compiled = compile_program(corpus, program)
    started = time.perf_counter()
    arm_id = str(candidate["arm_id"])
    if arm_id == "ARM-01":
        rankings, latencies = _rank_arm01(compiled.units, queries, compiled.family_aggregation)
    elif arm_id in DENSE_ARM_IDS:
        rankings, latencies = _rank_dense(
            compiled.units,
            queries,
            arm_id=arm_id,
            model_directory=Path(manifest["model_directories"][arm_id]),
            device=manifest["device_by_arm"][arm_id],
            method=compiled.family_aggregation,
            adapter_factory=SentenceTransformerDenseAdapter.from_staged_directory,
        )
    else:
        raise A2RemoteRetrieverError("remote arm identity drift")
    wall_seconds = time.perf_counter() - started
    ordered = sorted(latencies)
    p95 = ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]
    serialised = {
        token: [
            {"family_token": row.family_token, "rank": row.rank, "score": float(row.score)}
            for row in rows
        ]
        for token, rows in rankings.items()
    }
    body = {
        "schema_version": "myis.armindex-a2-remote-retrieval-result.v1",
        "status": "PASS_A2_REMOTE_RETRIEVAL",
        "attempt_id": manifest["attempt_id"],
        "candidate_id": candidate_id,
        "arm_id": arm_id,
        "program_sha256": candidate["program_sha256"],
        "ranking_sha256": canonical_sha256(serialised),
        "rankings": serialised,
        "latency": {"wall_seconds": wall_seconds, "search_p95_seconds": p95},
        "coverage": {"expected_units": len(queries), "completed_units": len(rankings)},
        "rep_dev_measured": False,
        "qrels_opened": False,
        "membership_opened": False,
    }
    return {**body, "receipt_sha256": canonical_sha256(body)}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-a2-remote-retriever")
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--input-manifest", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = run_remote_retriever(
            args.repository_root,
            manifest_path=args.input_manifest,
            candidate_id=os.environ.get("MYIS_A2_CANDIDATE_ID", ""),
        )
    except (A2RemoteRetrieverError, OSError, ValueError):
        print('{"status":"FAILED_CLOSED"}')
        return 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["A2RemoteRetrieverError", "run_remote_retriever"]
