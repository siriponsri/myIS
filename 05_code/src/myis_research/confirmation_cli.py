"""Hash-only confirmation request emitter and aggregate validator."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .confirmation import (
    ConfirmationRequest,
    load_confirmation_request,
    validate_confirmation_aggregate,
    write_confirmation_request,
)


def _hash_bindings(values: list[str], *, name: str) -> dict[str, str]:
    output: dict[str, str] = {}
    for value in values:
        key, separator, digest = value.partition("=")
        if not separator or not key.strip() or key in output:
            raise ValueError(f"{name} values must be unique NAME=SHA256 bindings")
        output[key] = digest
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Emit hash-only confirmation requests or validate aggregate-only responses."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    emit = commands.add_parser("emit-request")
    emit.add_argument("--request-id", required=True)
    emit.add_argument("--git-commit", required=True)
    emit.add_argument("--submission-hash", action="append", default=[], required=True)
    emit.add_argument("--config-hash", action="append", default=[], required=True)
    emit.add_argument("--protocol-hash", action="append", default=[], required=True)
    emit.add_argument("--output", type=Path, required=True)

    validate = commands.add_parser("validate-aggregate")
    validate.add_argument("--request", type=Path, required=True)
    validate.add_argument("--aggregate", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.command == "emit-request":
        request = ConfirmationRequest(
            request_id=args.request_id,
            created_at_utc=datetime.now(timezone.utc).isoformat(),
            git_commit=args.git_commit,
            submission_hashes=_hash_bindings(args.submission_hash, name="submission-hash"),
            config_hashes=_hash_bindings(args.config_hash, name="config-hash"),
            protocol_hashes=_hash_bindings(args.protocol_hash, name="protocol-hash"),
        )
        digest = write_confirmation_request(args.output, request)
        print(json.dumps({"request_sha256": digest, "path": str(args.output)}, sort_keys=True))
        return 0

    request_payload = json.loads(args.request.read_text(encoding="utf-8"))
    request = load_confirmation_request(request_payload)
    aggregate_payload = json.loads(args.aggregate.read_text(encoding="utf-8"))
    package = validate_confirmation_aggregate(
        aggregate_payload, expected_request_sha256=request.sha256
    )
    print(
        json.dumps(
            {
                "package_id": package.package_id,
                "package_sha256": package.sha256,
                "request_sha256": package.request_sha256,
                "comparison_count": len(package.comparisons),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
