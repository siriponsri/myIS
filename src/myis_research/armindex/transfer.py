"""Deterministic cross-arm transfer compilation interfaces."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from enum import StrEnum
import re
from typing import Any

from ..kernel.canonical import canonical_sha256


_SHA256 = re.compile(r"^[a-f0-9]{64}$")


class TransferError(ValueError):
    """Raised when a transfer compilation result is incomplete or unstable."""


class TransferStatus(StrEnum):
    EXACT_LOGICAL_TRANSFER = "exact_logical_transfer"
    ADAPTER_CONSTRAINED_COMPILATION = "adapter_constrained_compilation"
    UNSUPPORTED_TRANSFER = "unsupported_transfer"


TransferCompiler = Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]]


def classify_transfer(
    *,
    required_fields: Iterable[str],
    target_fields: Iterable[str],
    logical_unitization: str,
    supported_unitizations: Iterable[str],
    safe_constraint_available: bool = False,
) -> TransferStatus:
    """Classify logical support without claiming byte-identical compilation."""

    if not set(required_fields) <= set(target_fields):
        return TransferStatus.UNSUPPORTED_TRANSFER
    if logical_unitization in set(supported_unitizations):
        return TransferStatus.EXACT_LOGICAL_TRANSFER
    if safe_constraint_available:
        return TransferStatus.ADAPTER_CONSTRAINED_COMPILATION
    return TransferStatus.UNSUPPORTED_TRANSFER


def build_transfer_matrix(
    programs: Iterable[Mapping[str, Any]],
    target_adapters: Iterable[Mapping[str, Any]],
    *,
    compiler: TransferCompiler,
) -> dict[str, Any]:
    """Compile every source program/target arm pair twice and freeze stable rows."""

    ordered_programs = sorted(
        (dict(item) for item in programs), key=lambda item: str(item.get("program_id", ""))
    )
    ordered_adapters = sorted(
        (dict(item) for item in target_adapters), key=lambda item: str(item.get("arm_id", ""))
    )
    if not ordered_programs or not ordered_adapters:
        raise TransferError("transfer matrix requires programs and target adapters")

    rows: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()
    for program in ordered_programs:
        program_id = str(program.get("program_id", ""))
        logical_sha256 = str(program.get("program_sha256", ""))
        if not program_id or not _SHA256.fullmatch(logical_sha256):
            raise TransferError("transfer program identity is invalid")
        for adapter in ordered_adapters:
            arm_id = str(adapter.get("arm_id", ""))
            pair = (program_id, arm_id)
            if not re.fullmatch(r"ARM-0[1-5]", arm_id) or pair in seen_pairs:
                raise TransferError("transfer matrix identities must be unique and valid")
            first = _validate_compilation(compiler(program, adapter), logical_sha256, arm_id)
            second = _validate_compilation(compiler(program, adapter), logical_sha256, arm_id)
            if first != second:
                raise TransferError("cross-arm compilation is nondeterministic")
            rows.append({"source_program_id": program_id, **first})
            seen_pairs.add(pair)

    body: dict[str, Any] = {
        "schema_version": "myis.armindex-transfer-matrix.v1",
        "rows": rows,
    }
    body["matrix_sha256"] = canonical_sha256(body)
    return body


def _validate_compilation(
    value: Mapping[str, Any], logical_sha256: str, arm_id: str
) -> dict[str, Any]:
    result = dict(value)
    required = {
        "target_arm_id",
        "status",
        "logical_program_sha256",
        "compiled_sha256",
        "constraints_applied",
        "reason",
    }
    if set(result) != required:
        raise TransferError("transfer compilation fields do not match the v1 contract")
    if result["target_arm_id"] != arm_id or result["logical_program_sha256"] != logical_sha256:
        raise TransferError("transfer compilation identity mismatch")
    try:
        status = TransferStatus(str(result["status"]))
    except ValueError as error:
        raise TransferError("unknown transfer status") from error
    constraints = result["constraints_applied"]
    if not isinstance(constraints, list) or constraints != sorted(set(constraints)):
        raise TransferError("transfer constraints must be unique and lexically ordered")
    compiled_sha256 = result["compiled_sha256"]
    if status is TransferStatus.UNSUPPORTED_TRANSFER:
        if compiled_sha256 is not None or constraints or not str(result["reason"]).strip():
            raise TransferError("unsupported transfer needs a reason and no compiled output")
    else:
        if not _SHA256.fullmatch(str(compiled_sha256)):
            raise TransferError("supported transfer requires a compiled SHA-256")
        if status is TransferStatus.EXACT_LOGICAL_TRANSFER and constraints:
            raise TransferError("exact logical transfer cannot declare adapter constraints")
        if status is TransferStatus.ADAPTER_CONSTRAINED_COMPILATION and not constraints:
            raise TransferError("adapter-constrained transfer must declare constraints")
    return result
