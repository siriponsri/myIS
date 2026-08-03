"""Command line interface for the detached P2 measured supervisor."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .p2.contracts import P2ContractError
from .p2.measured_adapter import measure_candidate_to_file
from .p2.measured_supervisor import (
    request_stop_after_checkpoint,
    run_worker,
    start_detached_worker,
    status,
    verify_run,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="myis-p2-measured")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("start", "resume"):
        command = subparsers.add_parser(name)
        command.add_argument("--request", type=Path, required=True)
        command.add_argument("--run-root", type=Path, required=True)
        command.add_argument("--repository-root", type=Path, default=Path.cwd())
        command.add_argument("--owner-store", type=Path)
        command.add_argument("--cache-root", type=Path)
        command.add_argument("--startup-timeout-seconds", type=float, default=30.0)
        command.add_argument("--synthetic-checkpoints", type=int, default=0, help=argparse.SUPPRESS)
        command.add_argument("--checkpoint-delay-seconds", type=float, default=0.05, help=argparse.SUPPRESS)
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--run-root", type=Path, required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--run-root", type=Path, required=True)
    verify.add_argument("--request", type=Path)
    verify.add_argument("--repository-root", type=Path)
    verify.add_argument("--owner-store", type=Path)
    stop = subparsers.add_parser("stop-after-checkpoint")
    stop.add_argument("--run-root", type=Path, required=True)
    stop.add_argument("--reason", default="owner_request")
    worker = subparsers.add_parser("worker")
    worker.add_argument("--request", type=Path, required=True)
    worker.add_argument("--run-root", type=Path, required=True)
    worker.add_argument("--repository-root", type=Path, required=True)
    worker.add_argument("--owner-store", type=Path)
    worker.add_argument("--cache-root", type=Path)
    worker.add_argument("--mode", choices=("start", "resume"), required=True)
    worker.add_argument("--synthetic-checkpoints", type=int, default=0)
    worker.add_argument("--checkpoint-delay-seconds", type=float, default=0.05)
    candidate_worker = subparsers.add_parser("candidate-worker", help=argparse.SUPPRESS)
    candidate_worker.add_argument("--request", type=Path, required=True)
    candidate_worker.add_argument("--candidate-definition", type=Path, required=True)
    candidate_worker.add_argument("--data-role", choices=("train", "selection"), required=True)
    candidate_worker.add_argument("--repository-root", type=Path, required=True)
    candidate_worker.add_argument("--cache-root", type=Path, required=True)
    candidate_worker.add_argument("--run-root", type=Path, required=True)
    candidate_worker.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command in {"start", "resume"}:
            payload = start_detached_worker(
                request_path=args.request,
                run_root=args.run_root,
                repository_root=args.repository_root,
                mode=args.command,
                owner_store=args.owner_store,
                cache_root=args.cache_root,
                synthetic_checkpoints=args.synthetic_checkpoints,
                checkpoint_delay_seconds=args.checkpoint_delay_seconds,
                startup_timeout_seconds=args.startup_timeout_seconds,
            )
        elif args.command == "status":
            payload = status(args.run_root)
        elif args.command == "verify":
            if (args.request is None) != (args.repository_root is None):
                parser.error("--request and --repository-root must be supplied together")
            payload = verify_run(
                run_root=args.run_root,
                request_path=args.request,
                repository_root=args.repository_root,
                owner_store=args.owner_store,
            )
        elif args.command == "stop-after-checkpoint":
            payload = request_stop_after_checkpoint(args.run_root, reason=args.reason)
        elif args.command == "worker":
            payload = run_worker(
                request_path=args.request,
                run_root=args.run_root,
                repository_root=args.repository_root,
                mode=args.mode,
                owner_store=args.owner_store,
                cache_root=args.cache_root,
                synthetic_checkpoints=args.synthetic_checkpoints,
                checkpoint_delay_seconds=args.checkpoint_delay_seconds,
            )
        else:
            payload = measure_candidate_to_file(
                request_path=args.request,
                candidate_path=args.candidate_definition,
                data_role=args.data_role,
                repository_root=args.repository_root,
                cache_root=args.cache_root,
                run_root=args.run_root,
                output_path=args.output,
            )
    except P2ContractError as error:
        parser.exit(3, f"P2 measured supervisor blocked: {error}\n")
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
