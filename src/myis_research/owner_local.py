"""Pure validation for Owner-local aggregate/count handoffs.

This module deliberately performs no file, network, subprocess, dataset, qrels,
or provider access. The protected Owner process owns execution; the agent side
only validates hash-bound requests and aggregate-only receipts.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from .protection import assert_aggregate_only, assert_hash_only_mapping


OWNER_LOCAL_REQUEST_SCHEMA = "myis.owner-local-request.v1"
OWNER_LOCAL_RECEIPT_SCHEMA = "myis.owner-local-receipt.v1"
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_GIT = re.compile(r"^(?:[a-f0-9]{40}|[a-f0-9]{64})$")
_REQUEST_KEYS = frozenset({"schema_version", "request_id", "decision_id", "scope", "git_commit", "input_hashes"})
_RECEIPT_KEYS = frozenset({
    "schema_version", "request_sha256", "decision_id", "scope_sha256",
    "aggregate_counts", "aggregate_hashes", "status", "receipt_sha256",
})
_FORBIDDEN_KEY_PARTS = (
    "query_id", "query_ids", "qid", "qids", "qrel", "per_query",
    "membership", "outcome", "raw_payload", "credential", "secret", "password",
)


class OwnerLocalContractError(ValueError):
    """Raised when an Owner-local request or receipt crosses its boundary."""


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")


def canonical_sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def validate_request(payload: Mapping[str, Any]) -> dict[str, Any]:
    _validate_mapping(payload, _REQUEST_KEYS, "request")
    if payload["schema_version"] != OWNER_LOCAL_REQUEST_SCHEMA:
        raise OwnerLocalContractError("unsupported owner-local request schema")
    if payload["decision_id"] not in {"P1_CPU_EXECUTION_ENVELOPE", "D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"}:
        raise OwnerLocalContractError("request must bind the P1 execution envelope, D2, or D3")
    if not isinstance(payload["request_id"], str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]+", payload["request_id"]):
        raise OwnerLocalContractError("request_id is invalid")
    if not isinstance(payload["git_commit"], str) or not _GIT.fullmatch(payload["git_commit"]):
        raise OwnerLocalContractError("git_commit must be a lowercase commit hash")
    if not isinstance(payload["scope"], Mapping) or not payload["scope"]:
        raise OwnerLocalContractError("scope must be a non-empty hash mapping")
    if not isinstance(payload["input_hashes"], Mapping) or not payload["input_hashes"]:
        raise OwnerLocalContractError("input_hashes must be a non-empty hash mapping")
    _reject_lists(payload, "request")
    _reject_forbidden_keys(payload)
    assert_aggregate_only(payload)
    assert_hash_only_mapping({str(k): str(v) for k, v in payload["scope"].items()}, name="scope")
    assert_hash_only_mapping({str(k): str(v) for k, v in payload["input_hashes"].items()}, name="input_hashes")
    return dict(payload)


def build_receipt(request: Mapping[str, Any], *, aggregate_counts: Mapping[str, int], aggregate_hashes: Mapping[str, str]) -> dict[str, Any]:
    validated = validate_request(request)
    if not isinstance(aggregate_counts, Mapping) or not isinstance(aggregate_hashes, Mapping):
        raise OwnerLocalContractError("aggregate outputs must be mappings")
    if any(not isinstance(key, str) or not key.strip() for key in aggregate_counts):
        raise OwnerLocalContractError("aggregate count names must be non-empty strings")
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in aggregate_counts.values()):
        raise OwnerLocalContractError("aggregate counts must be non-negative integers")
    assert_hash_only_mapping({str(k): str(v) for k, v in aggregate_hashes.items()}, name="aggregate_hashes")
    body: dict[str, Any] = {
        "schema_version": OWNER_LOCAL_RECEIPT_SCHEMA,
        "request_sha256": canonical_sha256(validated),
        "decision_id": validated["decision_id"],
        "scope_sha256": canonical_sha256(validated["scope"]),
        "aggregate_counts": dict(sorted(aggregate_counts.items())),
        "aggregate_hashes": dict(sorted(aggregate_hashes.items())),
        "status": "accepted",
    }
    body["receipt_sha256"] = canonical_sha256(body)
    return validate_receipt(body)


def validate_receipt(payload: Mapping[str, Any]) -> dict[str, Any]:
    _validate_mapping(payload, _RECEIPT_KEYS, "receipt")
    if payload["schema_version"] != OWNER_LOCAL_RECEIPT_SCHEMA or payload["status"] != "accepted":
        raise OwnerLocalContractError("receipt schema or status is invalid")
    if payload["decision_id"] not in {"P1_CPU_EXECUTION_ENVELOPE", "D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"}:
        raise OwnerLocalContractError("receipt must bind the P1 execution envelope, D2, or D3")
    for key in ("request_sha256", "scope_sha256", "receipt_sha256"):
        if not isinstance(payload[key], str) or not _SHA256.fullmatch(payload[key]):
            raise OwnerLocalContractError(f"{key} must be SHA-256")
    counts = payload["aggregate_counts"]
    hashes = payload["aggregate_hashes"]
    if not isinstance(counts, Mapping) or not isinstance(hashes, Mapping):
        raise OwnerLocalContractError("aggregate fields must be mappings")
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in counts.values()):
        raise OwnerLocalContractError("aggregate counts must be non-negative integers")
    assert_hash_only_mapping({str(k): str(v) for k, v in hashes.items()}, name="aggregate_hashes")
    _reject_lists(payload, "receipt")
    _reject_forbidden_keys(payload)
    assert_aggregate_only(payload)
    unsigned = {key: value for key, value in payload.items() if key != "receipt_sha256"}
    if canonical_sha256(unsigned) != payload["receipt_sha256"]:
        raise OwnerLocalContractError("receipt_sha256 does not match canonical receipt")
    return dict(payload)


def _validate_mapping(payload: Mapping[str, Any], expected: frozenset[str], label: str) -> None:
    if not isinstance(payload, Mapping) or set(payload) != expected:
        raise OwnerLocalContractError(f"{label} fields do not match the contract")


def _reject_lists(value: Any, path: str) -> None:
    if isinstance(value, (list, tuple)):
        raise OwnerLocalContractError(f"lists are forbidden in owner-local {path}")
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_lists(item, f"{path}.{key}")


def _reject_forbidden_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).casefold()
            if any(part in normalized for part in _FORBIDDEN_KEY_PARTS):
                raise OwnerLocalContractError(f"forbidden owner-local field: {key}")
            _reject_forbidden_keys(item)
