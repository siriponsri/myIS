"""Run the admitted, frozen A6 ARM-03 full-DAPFAM materialization harness.

All data paths must resolve under Owner Store.  This command does not evaluate
retrieval and copies only the aggregate-safe manifest to ``--safe-export-root``.
"""

from __future__ import annotations

import argparse
import json
from multiprocessing import get_context
from pathlib import Path
from queue import Empty
import time
from typing import Any

from myis_research.armindex.a6_full_materialization import (
    A6ExecutionError, build_canary_receipt, build_failure_receipt, build_safe_return_manifest, load_execution_config,
    iter_source_shard, prepare_fresh_attempt, prepare_full_attempt_after_canary, run_shard, validate_fresh_attempt_root, validate_full_attempt_resume, validate_source_inventory,
    write_aggregate_safe_receipt,
)
from myis_research.kernel.canonical import canonical_sha256


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise A6ExecutionError(f"expected object: {path.name}")
    return value


def _worker(config: Any, shard: int, canary_documents: int | None, attempt_root: str, queue: Any) -> None:
    try:
        queue.put({
            "ok": True,
            "result": run_shard(
                config, shard=shard,
                rows=iter_source_shard(config, shard=shard, maximum_records=canary_documents),
                attempt_root=Path(attempt_root),
            ),
        })
    except Exception as error:  # pragma: no cover - process boundary
        queue.put({"ok": False, "error": f"{type(error).__name__}: {error}"})


def _collect_worker_messages(workers: list[Any], queue: Any, *, poll_seconds: float = 2.0) -> tuple[list[dict[str, Any]], bool]:
    """Poll in bounded intervals, detecting a child that died before queueing."""

    messages: list[dict[str, Any]] = []
    while len(messages) < len(workers):
        try:
            message = queue.get(timeout=poll_seconds)
        except Empty:
            if any(worker.exitcode is not None for worker in workers):
                _reap_workers(workers, poll_seconds=poll_seconds)
                return messages, False
            continue
        if not isinstance(message, dict):
            _reap_workers(workers, poll_seconds=poll_seconds)
            return messages, False
        messages.append(message)
    _reap_workers(workers, poll_seconds=poll_seconds)
    return messages, all(worker.exitcode == 0 for worker in workers) and all(message.get("ok") is True for message in messages)


def _reap_workers(workers: list[Any], *, poll_seconds: float) -> None:
    """Unconditionally join all children; terminate a straggler before return."""

    for worker in workers:
        worker.join(timeout=poll_seconds)
    for worker in workers:
        if worker.is_alive():
            worker.terminate()
    for worker in workers:
        worker.join(timeout=poll_seconds)


def _write_failure(*, config: Any, stage: str, workers: list[Any], messages: list[dict[str, Any]], safe_export_root: Path) -> None:
    receipt = build_failure_receipt(
        config, stage=stage, worker_exit_codes=[worker.exitcode for worker in workers], completed_messages=len(messages),
    )
    write_aggregate_safe_receipt(safe_export_root / f"A6_{stage.upper()}_LAUNCH_FAILURE_RECEIPT.json", receipt)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--winner-binding", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--execution-config", type=Path, required=True)
    parser.add_argument("--owner-store-root", type=Path, required=True)
    parser.add_argument("--attempt-root", type=Path, required=True)
    parser.add_argument("--safe-export-root", type=Path, required=True)
    parser.add_argument("--canary-documents", type=int, default=0)
    parser.add_argument("--recovery-count", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    try:
        root = args.owner_store_root.resolve()
        config = load_execution_config(args.execution_config, owner_store_root=root, contract=_json(args.contract), winner_binding=_json(args.winner_binding), admission=_json(args.admission))
        attempt = args.attempt_root.resolve()
        canary = args.canary_documents or None
        if args.canary_documents < 0:
            raise A6ExecutionError("canary document count is invalid")
        if args.resume:
            if canary is not None:
                raise A6ExecutionError("A6 resume is forbidden for canary work")
            validate_full_attempt_resume(config, owner_store_root=root, attempt_root=attempt)
        else:
            if canary is None and attempt.exists() and (attempt / "A6_CANARY_LINEAGE.json").is_file():
                prepare_full_attempt_after_canary(config, owner_store_root=root, attempt_root=attempt)
            elif canary is None and attempt.exists() and (attempt / "A6_FRESH_ATTEMPT_ROOT.json").is_file():
                validate_fresh_attempt_root(config, owner_store_root=root, attempt_root=attempt)
            else:
                prepare_fresh_attempt(config, owner_store_root=root, attempt_root=attempt)
        validate_source_inventory(config)
        # A canary is intentionally non-resumable into the full corpus.  Its
        # vectors prove runtime capacity but cannot become A6 full-run output.
        execution_root = attempt / "canary" if canary is not None else attempt
        started = time.monotonic()
        context = get_context("spawn")
        queue = context.Queue()
        workers = [
            context.Process(target=_worker, args=(config, shard, canary, str(execution_root), queue), daemon=False)
            for shard in (0, 1)
        ]
        for worker in workers:
            worker.start()
        messages, workers_ok = _collect_worker_messages(workers, queue)
        if not workers_ok:
            _write_failure(config=config, stage="canary" if canary is not None else "full", workers=workers, messages=messages, safe_export_root=args.safe_export_root)
            raise A6ExecutionError("A6 shard worker failed; preserve attempt for compatible recovery")
        elapsed = time.monotonic() - started
        if canary is not None:
            lineage_body = {
                "schema_version": "myis.armindex-a6-canary-lineage.v1",
                "status": "PASS_A6_CANARY_ISOLATED_NON_RESUMABLE",
                "stage": "canary", "attempt_id": config.attempt_id,
                "config_sha256": config.config_sha256, "source_sha256": config.source_sha256,
                "canary_root_pointer": f"{attempt.relative_to(root).as_posix()}/canary",
                "full_promotion_forbidden": True, "protected_payload_included": False,
            }
            write_aggregate_safe_receipt(attempt / "A6_CANARY_LINEAGE.json", {**lineage_body, "lineage_sha256": canonical_sha256(lineage_body)})
            aggregate = build_canary_receipt(config, [message["result"] for message in messages], elapsed_seconds=elapsed)
            target = args.safe_export_root / "A6_CANARY_RECEIPT.json"
            write_aggregate_safe_receipt(target, aggregate)
            print(json.dumps({"status": aggregate["status"], "canary_receipt_sha256": aggregate["canary_receipt_sha256"]}, sort_keys=True))
            return 0
        receipt = build_safe_return_manifest(config, [message["result"] for message in messages], elapsed_seconds=elapsed, recovery_count=args.recovery_count, safe_export_root=args.safe_export_root)
        print(json.dumps({"status": receipt["status"], "safe_return_sha256": receipt["safe_return_sha256"]}, sort_keys=True))
        return 0
    except A6ExecutionError as error:
        print(f"[ARMIndex][A6][BLOCKED] {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
