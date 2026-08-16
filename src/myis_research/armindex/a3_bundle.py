"""Fail-closed hash-only A3.1 five-arm preparation bundle validation."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import re
from typing import Any

from ..kernel.canonical import canonical_sha256
from ..protection import assert_aggregate_only
from .a3_train_headroom import (
    ARM_IDS,
    AUTHORITY_FILE_SHA256,
    AUTHORITY_ID,
    FROZEN_A2_BINDINGS,
)


_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_REQUIRED = {
    "schema_version",
    "bundle_id",
    "authority_id",
    "authority_file_sha256",
    "authority_state",
    "arms",
    "frozen_a2_bindings",
    "pending_runtime_inputs",
    "safety",
    "manifest_sha256",
}
_PENDING_ARM_KEYS = {
    "arm_id",
    "winner_program_sha256",
    "winner_selection_receipt_sha256",
    "train_aggregate_receipt_sha256",
    "hdev_aggregate_receipt_sha256",
}


class A3BundleError(ValueError):
    """Raised when the A3.1 preparation manifest is incomplete or unsafe."""


def validate_a3_bundle_manifest(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the pending hash-only five-arm bundle without opening runtime inputs."""

    manifest = deepcopy(dict(value))
    try:
        assert_aggregate_only(manifest)
    except ValueError as error:
        raise A3BundleError(str(error)) from error
    if set(manifest) != _REQUIRED:
        raise A3BundleError(
            "A3 bundle manifest fields do not match the frozen contract"
        )
    if (
        manifest["schema_version"]
        != "myis.armindex-a3-train-headroom-bundle-manifest.v1"
        or manifest["bundle_id"] != "A3.1_TRAIN_HEADROOM_FIVE_ARM_PENDING"
        or manifest["authority_id"] != AUTHORITY_ID
        or manifest["authority_file_sha256"] != AUTHORITY_FILE_SHA256
        or manifest["authority_state"] != "PENDING_A2_CLOSEOUT"
    ):
        raise A3BundleError("A3 bundle is not bound to the pending A3.1 authority")
    if manifest["frozen_a2_bindings"] != FROZEN_A2_BINDINGS:
        raise A3BundleError("A3 bundle frozen A2 tuple is incompatible")
    if manifest["pending_runtime_inputs"] != [
        "a2_closeout_receipt",
        "five_winner_selection_receipts",
        "a1_incumbent_aggregate_receipt",
        "owner_local_fixed_diagnostic_aggregates",
    ]:
        raise A3BundleError("A3 bundle pending runtime inputs are incomplete")
    safety = manifest["safety"]
    expected_safety = {
        "measured_execution_started": False,
        "protected_data_accessed": False,
        "provider_contacted": False,
        "remote_execution_started": False,
        "spend_permitted": False,
        "candidate_mutation_permitted": False,
        "selection_permitted": False,
        "final_permitted": False,
    }
    if safety != expected_safety:
        raise A3BundleError("A3 bundle safety boundary is not fail-closed")
    arms = manifest["arms"]
    if not isinstance(arms, list) or len(arms) != len(ARM_IDS):
        raise A3BundleError("A3 bundle must contain exactly five arms")
    seen: set[str] = set()
    for arm in arms:
        if not isinstance(arm, Mapping) or set(arm) != _PENDING_ARM_KEYS:
            raise A3BundleError("A3 bundle arm entry is incomplete")
        if arm["arm_id"] not in ARM_IDS or arm["arm_id"] in seen:
            raise A3BundleError("A3 bundle arm IDs must cover each active arm once")
        seen.add(arm["arm_id"])
        if any(arm[field] is not None for field in _PENDING_ARM_KEYS - {"arm_id"}):
            raise A3BundleError(
                "pending A3 bundle cannot contain winner or diagnostic hashes"
            )
    if seen != set(ARM_IDS):
        raise A3BundleError("A3 bundle arm IDs are incomplete")
    manifest_sha256 = manifest["manifest_sha256"]
    if not _SHA256.fullmatch(str(manifest_sha256)):
        raise A3BundleError("A3 bundle manifest_sha256 is invalid")
    unsigned = {key: item for key, item in manifest.items() if key != "manifest_sha256"}
    if manifest_sha256 != canonical_sha256(unsigned):
        raise A3BundleError("A3 bundle manifest_sha256 does not bind its contents")
    return manifest


__all__ = ["A3BundleError", "validate_a3_bundle_manifest"]
