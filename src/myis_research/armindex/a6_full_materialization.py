"""Fail-closed A6 full-DAPFAM materialization harness.

This module is deliberately not an evaluator.  It consumes one immutable
ARM-03 configuration already confirmed by A5, renders its fixed passage view,
and writes embeddings/index shards only below an Owner Store attempt root.
The repository-facing receipt contains aggregates and hashes only.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
import json
import math
import os
from pathlib import Path
import re
try:
    import resource
except ImportError:  # pragma: no cover - Windows only
    resource = None  # type: ignore[assignment]
import tempfile
import time
from typing import Any
import unicodedata

from ..kernel.canonical import canonical_sha256, file_sha256
from ..protection import assert_aggregate_only
from .a6_materialization import (
    A6MaterializationError,
    validate_a5_frozen_winner_binding,
    validate_a6_attempt_admission,
)


EXPECTED_DOCUMENT_COUNT = 45_336
ARM_ID = "ARM-03"
MODEL_ID = "datalyes/patembed-large"
# The A5 owner-local snapshot retains two additional conversion-provenance
# columns.  They are deliberately not read by the frozen ARM-03 view, but
# their presence must not be mistaken for a schema breach or silently dropped
# before the protected source scan has completed.
SOURCE_FIELDS = (
    "family_token", "publication_token", "title_en", "abstract_en", "claims_text",
    "claims", "publication_ordinal",
)
FIELD_ORDER = ("title", "abstract", "claims_text")
CHUNK_SIZE = 384
CHUNK_OVERLAP = 64
DOCUMENT_PREFIX = "encode document for different retrieval: "
REQUIRED_RUNTIME_PACKAGES = ("numpy", "torch", "sentence-transformers", "transformers")
LATENCY_BUCKETS_MS = (0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1_000.0, 2_500.0, 5_000.0)
# The corpus bytes available to A6 are the hash-bound Owner-Store snapshot
# first materialized for A5.  The original Arrow payload is not present
# locally, so this deliberately binds its canonical manifest and A5 snapshot
# lineage without claiming a direct re-hash of unavailable Arrow bytes.
CANONICAL_SOURCE_MANIFEST_SHA256 = "f829e1827aff84dfb332742f74c1f717da655a1ef962e1aca0260d8d2a450d6c"
A5_SOURCE_SNAPSHOT_MANIFEST_SHA256 = "7a27b1efa30cd0045b7e58ff55d4d43c5eb2594cec5b82de3dbc8869b50dd8ed"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REMOTE_ROOT = re.compile(r"^/opt/myis/a6-goal001-[0-9]{8}T[0-9]{6}Z-[a-z0-9][a-z0-9._-]{2,31}$")
_FORBIDDEN_SOURCE_KEYS = re.compile(
    r"(?:qrels?|query(?:_|-)?(?:id|text|membership)?|ranking|per(?:_|-)?query|selection|final)",
    re.IGNORECASE,
)


class A6ExecutionError(RuntimeError):
    """Raised when A6 execution would violate its frozen operational unit."""


@dataclass(frozen=True)
class ExecutionConfig:
    attempt_id: str
    source_path: Path
    source_sha256: str
    expected_documents: int
    expected_families: int
    source_snapshot_receipt_sha256: str
    model_path: Path
    model_manifest_sha256: str
    runtime_receipt_sha256: str
    runtime_packages: Mapping[str, str]
    program_path: Path
    semantic_manifest_sha256: str
    gpu_ids: tuple[int, int]
    batch_size: int
    checkpoint_records: int
    admitted_hourly_rate_usd: float
    admission_sha256: str
    component_hashes: Mapping[str, str]
    config_sha256: str


def _atomic_json(path: Path, value: Mapping[str, Any], *, immutable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    if path.exists() and immutable:
        if path.is_symlink() or path.read_text(encoding="utf-8") != payload:
            raise A6ExecutionError(f"immutable artifact differs: {path.name}")
        return
    if path.exists() and path.is_symlink():
        raise A6ExecutionError(f"symlink artifact is forbidden: {path.name}")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_aggregate_safe_receipt(path: Path, value: Mapping[str, Any]) -> None:
    """Write an immutable, recursively aggregate-only receipt."""

    try:
        assert_aggregate_only(value)
    except ValueError as error:
        raise A6ExecutionError("A6 aggregate receipt contains protected data") from error
    _atomic_json(path, value, immutable=True)


def _load_json(path: Path, role: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise A6ExecutionError(f"{role} is missing or invalid") from error
    if not isinstance(value, dict):
        raise A6ExecutionError(f"{role} must be a JSON object")
    return value


def _sha(value: Any, role: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise A6ExecutionError(f"{role} must be SHA-256")
    return value


def _relative_owner_path(value: Any, role: str) -> str:
    if not isinstance(value, str) or not value or value.startswith(("/", "\\")) or "\\" in value:
        raise A6ExecutionError(f"{role} must be an Owner-Store-relative path")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise A6ExecutionError(f"{role} contains path traversal")
    return value


def _resolve_inside(root: Path, relative: str, role: str) -> Path:
    target = (root / _relative_owner_path(relative, role)).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as error:
        raise A6ExecutionError(f"{role} escapes Owner Store") from error
    return target


def _self_hashed_receipt(path: Path, *, schema: str, digest_field: str, role: str) -> dict[str, Any]:
    value = _load_json(path, role)
    if value.get("schema_version") != schema:
        raise A6ExecutionError(f"{role} schema is invalid")
    digest = _sha(value.get(digest_field), f"{role}.{digest_field}")
    if digest != canonical_sha256({key: item for key, item in value.items() if key != digest_field}):
        raise A6ExecutionError(f"{role} self-hash mismatch")
    return value


def _validate_source_snapshot(
    path: Path, *, config_source_sha256: str, expected_documents: int, expected_families: int, attempt_id: str,
) -> str:
    value = _self_hashed_receipt(
        path, schema="myis.armindex-a6-source-snapshot-materialization-receipt.v1",
        digest_field="source_snapshot_receipt_sha256", role="A6 source snapshot materialization receipt",
    )
    required = {
        "schema_version", "status", "attempt_id", "canonical_source_manifest_sha256",
        "a5_source_snapshot_manifest_sha256", "direct_arrow_byte_verification", "source_sha256",
        "source_document_count", "source_family_count", "source_format", "source_schema",
        "canonical_to_frozen_field_mapping", "protected_payload_included", "source_snapshot_receipt_sha256",
    }
    if set(value) != required or value["status"] != "PASS_A6_SOURCE_SNAPSHOT_MATERIALIZATION":
        raise A6ExecutionError("A6 source snapshot materialization receipt fields are invalid")
    if value["attempt_id"] != attempt_id or value["source_sha256"] != config_source_sha256:
        raise A6ExecutionError("A6 source snapshot binding drifted")
    if (value["canonical_source_manifest_sha256"] != CANONICAL_SOURCE_MANIFEST_SHA256
            or value["a5_source_snapshot_manifest_sha256"] != A5_SOURCE_SNAPSHOT_MANIFEST_SHA256
            or value["direct_arrow_byte_verification"] is not False):
        raise A6ExecutionError("A6 source snapshot overstates its canonical Arrow provenance")
    if (value["source_document_count"] != expected_documents or value["source_family_count"] != expected_families
            or value["source_format"] != "jsonl" or value["source_schema"] != list(SOURCE_FIELDS)
            or value["protected_payload_included"] is not False):
        raise A6ExecutionError("A6 source snapshot materialization receipt does not bind the committed corpus")
    if value["canonical_to_frozen_field_mapping"] != {
        "title_en": "title", "abstract_en": "abstract", "claims_text": "claims_text",
    }:
        raise A6ExecutionError("A6 source snapshot mapping does not preserve frozen ARM-03 fields")
    _sha(value["canonical_source_manifest_sha256"], "canonical_source_manifest_sha256")
    _sha(value["a5_source_snapshot_manifest_sha256"], "a5_source_snapshot_manifest_sha256")
    return value["source_snapshot_receipt_sha256"]


def model_tree_sha256(model_path: Path) -> str:
    """Hash the exact staged model tree without serializing its payload."""

    if not model_path.is_dir() or model_path.is_symlink():
        raise A6ExecutionError("A6 staged model tree is unavailable")
    rows: list[dict[str, str]] = []
    for path in sorted(model_path.rglob("*")):
        if path.is_symlink():
            raise A6ExecutionError("A6 staged model tree contains a symlink")
        if path.is_file():
            rows.append({"path": path.relative_to(model_path).as_posix(), "sha256": file_sha256(path)})
    if not rows:
        raise A6ExecutionError("A6 staged model tree is empty")
    return canonical_sha256(rows)


def _validate_model_manifest(
    path: Path, *, attempt_id: str, owner_store_root: Path, model_path: Path, adapter_sha256: str,
) -> str:
    value = _self_hashed_receipt(
        path, schema="myis.armindex-a6-model-manifest.v1", digest_field="model_manifest_sha256",
        role="A6 model manifest",
    )
    required = {
        "schema_version", "status", "attempt_id", "arm_id", "model_id", "model_tree_sha256",
        "model_adapter_sha256", "model_path_sha256", "protected_payload_included", "model_manifest_sha256",
    }
    if set(value) != required or value["status"] != "PASS_A6_FROZEN_MODEL_MANIFEST":
        raise A6ExecutionError("A6 model manifest fields are invalid")
    if value["attempt_id"] != attempt_id or value["arm_id"] != ARM_ID or value["model_id"] != MODEL_ID:
        raise A6ExecutionError("A6 model manifest target drifted")
    if value["model_adapter_sha256"] != adapter_sha256 or value["protected_payload_included"] is not False:
        raise A6ExecutionError("A6 model manifest adapter binding drifted")
    for field in ("model_tree_sha256", "model_path_sha256"):
        _sha(value[field], field)
    if value["model_tree_sha256"] != model_tree_sha256(model_path):
        raise A6ExecutionError("A6 staged model tree hash drifted")
    # The model tree checksum is produced by the trusted staging step.  The
    # path checksum prevents a config from pointing that manifest elsewhere.
    if value["model_path_sha256"] != canonical_sha256(model_path.relative_to(owner_store_root).as_posix()):
        raise A6ExecutionError("A6 model manifest path binding drifted")
    return value["model_manifest_sha256"]


def _validate_staged_runtime_receipt(path: Path, *, attempt_id: str, runtime_lock_sha256: str) -> tuple[str, dict[str, str]]:
    value = _self_hashed_receipt(
        path, schema="myis.armindex-a6-staged-runtime-receipt.v1", digest_field="runtime_receipt_sha256",
        role="A6 staged runtime receipt",
    )
    required = {
        "schema_version", "status", "attempt_id", "runtime_lock_sha256", "python_version",
        "torch_version", "cuda_available", "gpu_count", "package_versions", "package_versions_sha256",
        "protected_payload_included", "runtime_receipt_sha256",
    }
    if set(value) != required or value["status"] != "PASS_A6_STAGED_RUNTIME":
        raise A6ExecutionError("A6 staged runtime receipt fields are invalid")
    if value["attempt_id"] != attempt_id or value["runtime_lock_sha256"] != runtime_lock_sha256:
        raise A6ExecutionError("A6 staged runtime lock binding drifted")
    if value["cuda_available"] is not True or value["gpu_count"] != 2 or value["protected_payload_included"] is not False:
        raise A6ExecutionError("A6 staged runtime does not meet the admitted GPU topology")
    if not isinstance(value["python_version"], str) or not isinstance(value["torch_version"], str):
        raise A6ExecutionError("A6 staged runtime version evidence is invalid")
    packages = value["package_versions"]
    if not isinstance(packages, Mapping) or set(packages) != set(REQUIRED_RUNTIME_PACKAGES):
        raise A6ExecutionError("A6 staged runtime package inventory is invalid")
    if any(not isinstance(packages[name], str) or not packages[name] for name in REQUIRED_RUNTIME_PACKAGES):
        raise A6ExecutionError("A6 staged runtime package versions are invalid")
    if value["package_versions_sha256"] != canonical_sha256(dict(packages)):
        raise A6ExecutionError("A6 staged runtime package hash drifted")
    return value["runtime_receipt_sha256"], dict(packages)


def _require_offline_runtime(packages: Mapping[str, str]) -> None:
    if any(os.environ.get(name) != "1" for name in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "PIP_NO_INDEX")):
        raise A6ExecutionError("A6 offline runtime policy is not enforced")
    observed: dict[str, str] = {}
    for package in REQUIRED_RUNTIME_PACKAGES:
        try:
            observed[package] = version(package)
        except PackageNotFoundError as error:
            raise A6ExecutionError(f"A6 runtime package is missing: {package}") from error
    if observed != dict(packages):
        raise A6ExecutionError("A6 installed runtime package versions drifted")


def enforce_offline_environment() -> None:
    """Set all A6 processes to an explicit no-network model/package posture."""

    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["PIP_NO_INDEX"] = "1"


def _validate_program(path: Path, *, expected_program_sha256: str) -> None:
    value = _load_json(path, "A6 staged ARM-03 representation program")
    body = {key: item for key, item in value.items() if key != "program_sha256"}
    if value.get("program_sha256") != expected_program_sha256 or canonical_sha256(body) != expected_program_sha256:
        raise A6ExecutionError("A6 staged ARM-03 representation program hash drifted")
    expected = {
        "schema_version": "myis.armindex-representation-program.v1", "arm_id": ARM_ID,
        "program_id": "a2-arm-03-matched-b2-orthogonal", "duplicate_policy": "content_hash_first",
        "family_aggregation": "maxp", "field_order": list(FIELD_ORDER), "source_fields": list(FIELD_ORDER),
        "field_labels": {field: "" for field in FIELD_ORDER}, "normalization": "unicode_nfkc_whitespace",
        "preserve_family_identity": True, "unitization": {"kind": "passage", "logical_size": CHUNK_SIZE, "overlap": CHUNK_OVERLAP},
    }
    for field, expected_value in expected.items():
        if value.get(field) != expected_value:
            raise A6ExecutionError(f"A6 ARM-03 representation program semantics drifted: {field}")


def _validate_semantic_manifest(
    path: Path, *, expected_program_sha256: str, expected_prompt_sha256: str, expected_adapter_sha256: str,
) -> str:
    """Bind P03 rendering and model invocation semantics to the A5 winner."""

    value = _self_hashed_receipt(
        path, schema="myis.armindex-a6-arm03-semantic-manifest.v1", digest_field="semantic_manifest_sha256",
        role="A6 ARM-03 semantic manifest",
    )
    required = {
        "schema_version", "status", "representation_program_sha256", "prompt_or_prefix_sha256",
        "model_adapter_sha256", "document_prefix", "normalization", "field_order", "unitization",
        "embedding_dimension", "normalize_embeddings", "local_files_only", "semantic_manifest_sha256",
    }
    if set(value) != required or value["status"] != "PASS_A6_FROZEN_ARM03_SEMANTICS":
        raise A6ExecutionError("A6 ARM-03 semantic manifest fields are invalid")
    if (value["representation_program_sha256"] != expected_program_sha256 or value["prompt_or_prefix_sha256"] != expected_prompt_sha256
            or value["model_adapter_sha256"] != expected_adapter_sha256):
        raise A6ExecutionError("A6 ARM-03 semantic manifest hash binding drifted")
    if (value["document_prefix"] != DOCUMENT_PREFIX or value["normalization"] != "unicode_nfkc_whitespace"
            or value["field_order"] != list(FIELD_ORDER)
            or value["unitization"] != {"kind": "passage", "logical_size": CHUNK_SIZE, "overlap": CHUNK_OVERLAP}
            or value["embedding_dimension"] != 1024 or value["normalize_embeddings"] is not True
            or value["local_files_only"] is not True):
        raise A6ExecutionError("A6 ARM-03 rendering or embedding semantics drifted")
    return value["semantic_manifest_sha256"]


def _validate_remote_root_admission(path: Path, *, attempt_id: str, remote_root: Any) -> str:
    value = _self_hashed_receipt(
        path, schema="myis.armindex-a6-remote-root-admission.v1", digest_field="remote_root_admission_sha256",
        role="A6 remote root admission",
    )
    required = {
        "schema_version", "status", "attempt_id", "remote_root", "checked_absent_before_create",
        "created_empty", "contains_prior_a4_a5_data", "protected_payload_included", "remote_root_admission_sha256",
    }
    if set(value) != required or value["status"] != "PASS_A6_FRESH_REMOTE_ROOT":
        raise A6ExecutionError("A6 remote root admission fields are invalid")
    if value["attempt_id"] != attempt_id or value["remote_root"] != remote_root or _REMOTE_ROOT.fullmatch(str(remote_root)) is None:
        raise A6ExecutionError("A6 remote root identity drifted")
    if value["checked_absent_before_create"] is not True or value["created_empty"] is not True or value["contains_prior_a4_a5_data"] is not False:
        raise A6ExecutionError("A6 remote root was not proven fresh")
    if value["protected_payload_included"] is not False:
        raise A6ExecutionError("A6 remote root admission contains protected payload")
    return value["remote_root_admission_sha256"]


def load_execution_config(
    config_path: Path,
    *,
    owner_store_root: Path,
    contract: Mapping[str, Any],
    winner_binding: Mapping[str, Any],
    admission: Mapping[str, Any],
) -> ExecutionConfig:
    """Bind a fresh A6 runtime configuration to A5 before any corpus read."""

    try:
        winner = validate_a5_frozen_winner_binding(winner_binding, contract)
        admitted = validate_a6_attempt_admission(admission, contract, winner)
    except A6MaterializationError as error:
        raise A6ExecutionError("A6 predecessor or admission is invalid") from error
    item = _load_json(config_path, "A6 execution configuration")
    required = {
        "schema_version", "attempt_id", "arm_id", "model_id", "source_path",
        "source_sha256", "expected_document_count", "expected_family_count", "source_snapshot_receipt_path",
        "source_snapshot_receipt_sha256", "model_path", "model_manifest_path", "model_manifest_sha256",
        "runtime_receipt_path", "runtime_receipt_sha256", "semantic_manifest_path", "semantic_manifest_sha256",
        "budget_admission_path", "remote_attempt_root", "remote_root_admission_path", "remote_root_admission_sha256",
        "gpu_ids", "batch_size", "checkpoint_records",
        "component_hashes", "program_path", "normalization", "field_order", "field_labels",
        "unitization", "family_aggregation", "index_kind", "config_sha256",
    }
    if set(item) != required or item["schema_version"] != "myis.armindex-a6-execution-config.v1":
        raise A6ExecutionError("A6 execution configuration fields are invalid")
    if item["attempt_id"] != admitted["attempt_id"] or item["arm_id"] != ARM_ID or item["model_id"] != MODEL_ID:
        raise A6ExecutionError("A6 execution configuration does not name the frozen ARM-03 target")
    if item["normalization"] != "unicode_nfkc_whitespace" or tuple(item["field_order"]) != FIELD_ORDER:
        raise A6ExecutionError("A6 representation fields or normalization drifted")
    if item["field_labels"] != {field: "" for field in FIELD_ORDER}:
        raise A6ExecutionError("A6 representation labels drifted")
    if item["unitization"] != {"kind": "passage", "logical_size": CHUNK_SIZE, "overlap": CHUNK_OVERLAP}:
        raise A6ExecutionError("A6 passage unitization drifted")
    if item["family_aggregation"] != "maxp" or item["index_kind"] != "flat_l2_normalized":
        raise A6ExecutionError("A6 retrieval/index semantics drifted")
    hashes = item["component_hashes"]
    expected_hashes = winner["winner"]
    if not isinstance(hashes, Mapping) or set(hashes) != set(expected_hashes):
        raise A6ExecutionError("A6 component hash surface is incomplete")
    for key, expected in expected_hashes.items():
        if hashes.get(key) != expected:
            raise A6ExecutionError(f"A6 frozen component hash drifted: {key}")
    if not isinstance(item["expected_document_count"], int) or item["expected_document_count"] != EXPECTED_DOCUMENT_COUNT:
        raise A6ExecutionError("A6 source document commitment drifted")
    if not isinstance(item["expected_family_count"], int) or item["expected_family_count"] <= 0:
        raise A6ExecutionError("A6 family commitment is invalid")
    source_path = _resolve_inside(owner_store_root, item["source_path"], "source_path")
    model_path = _resolve_inside(owner_store_root, item["model_path"], "model_path")
    program_path = _resolve_inside(owner_store_root, item["program_path"], "program_path")
    snapshot_path = _resolve_inside(owner_store_root, item["source_snapshot_receipt_path"], "source_snapshot_receipt_path")
    model_manifest_path = _resolve_inside(owner_store_root, item["model_manifest_path"], "model_manifest_path")
    runtime_path = _resolve_inside(owner_store_root, item["runtime_receipt_path"], "runtime_receipt_path")
    semantic_path = _resolve_inside(owner_store_root, item["semantic_manifest_path"], "semantic_manifest_path")
    budget_path = _resolve_inside(owner_store_root, item["budget_admission_path"], "budget_admission_path")
    remote_root_path = _resolve_inside(owner_store_root, item["remote_root_admission_path"], "remote_root_admission_path")
    if not source_path.is_file() or source_path.is_symlink() or not model_path.is_dir() or model_path.is_symlink() or not program_path.is_file() or program_path.is_symlink():
        raise A6ExecutionError("A6 source or model input is unavailable")
    _sha(item["source_sha256"], "source_sha256")
    if file_sha256(source_path) != item["source_sha256"]:
        raise A6ExecutionError("A6 source bytes do not match the frozen hash")
    snapshot_sha = _validate_source_snapshot(
        snapshot_path, config_source_sha256=item["source_sha256"], expected_documents=item["expected_document_count"],
        expected_families=item["expected_family_count"], attempt_id=item["attempt_id"],
    )
    if item["source_snapshot_receipt_sha256"] != snapshot_sha:
        raise A6ExecutionError("A6 source snapshot receipt hash drifted")
    model_manifest_sha = _validate_model_manifest(
        model_manifest_path, attempt_id=item["attempt_id"], owner_store_root=owner_store_root,
        model_path=model_path, adapter_sha256=expected_hashes["model_adapter_sha256"],
    )
    if item["model_manifest_sha256"] != model_manifest_sha:
        raise A6ExecutionError("A6 model manifest hash drifted")
    runtime_sha, runtime_packages = _validate_staged_runtime_receipt(
        runtime_path, attempt_id=item["attempt_id"], runtime_lock_sha256=expected_hashes["runtime_lock_sha256"],
    )
    if item["runtime_receipt_sha256"] != runtime_sha:
        raise A6ExecutionError("A6 staged runtime receipt hash drifted")
    _validate_program(program_path, expected_program_sha256=expected_hashes["representation_program_sha256"])
    semantic_sha = _validate_semantic_manifest(
        semantic_path, expected_program_sha256=expected_hashes["representation_program_sha256"],
        expected_prompt_sha256=expected_hashes["prompt_or_prefix_sha256"], expected_adapter_sha256=expected_hashes["model_adapter_sha256"],
    )
    if item["semantic_manifest_sha256"] != semantic_sha:
        raise A6ExecutionError("A6 ARM-03 semantic manifest hash drifted")
    budget = _self_hashed_receipt(
        budget_path, schema="myis.armindex-a6-budget-admission.v1", digest_field="budget_admission_sha256",
        role="A6 budget admission",
    )
    if (budget.get("status") != "PASS_A6_BUDGET_ADMISSION" or budget.get("attempt_id") != item["attempt_id"]
            or budget.get("budget_admission_sha256") != admitted["budget_admission_sha256"]):
        raise A6ExecutionError("A6 budget admission binding drifted")
    hourly_rate = budget.get("hourly_rate_usd")
    if not isinstance(hourly_rate, (int, float)) or isinstance(hourly_rate, bool) or hourly_rate <= 0:
        raise A6ExecutionError("A6 admitted hourly rate is invalid")
    remote_root_sha = _validate_remote_root_admission(
        remote_root_path, attempt_id=item["attempt_id"], remote_root=item["remote_attempt_root"],
    )
    if item["remote_root_admission_sha256"] != remote_root_sha:
        raise A6ExecutionError("A6 remote root admission hash drifted")
    gpu_ids = item["gpu_ids"]
    if not isinstance(gpu_ids, list) or len(gpu_ids) != 2 or len(set(gpu_ids)) != 2 or any(not isinstance(gpu, int) or gpu < 0 for gpu in gpu_ids):
        raise A6ExecutionError("A6 requires exactly two distinct GPU IDs")
    if not isinstance(item["batch_size"], int) or not 1 <= item["batch_size"] <= 512:
        raise A6ExecutionError("A6 batch size is invalid")
    if not isinstance(item["checkpoint_records"], int) or not 1 <= item["checkpoint_records"] <= EXPECTED_DOCUMENT_COUNT:
        raise A6ExecutionError("A6 checkpoint interval is invalid")
    _sha(item["config_sha256"], "config_sha256")
    body = {key: value for key, value in item.items() if key != "config_sha256"}
    if item["config_sha256"] != canonical_sha256(body):
        raise A6ExecutionError("A6 execution configuration self-hash mismatch")
    return ExecutionConfig(
        attempt_id=item["attempt_id"], source_path=source_path, source_sha256=item["source_sha256"],
        expected_documents=item["expected_document_count"], expected_families=item["expected_family_count"],
        source_snapshot_receipt_sha256=snapshot_sha, model_path=model_path, model_manifest_sha256=model_manifest_sha,
        runtime_receipt_sha256=runtime_sha,
        runtime_packages=runtime_packages, program_path=program_path, semantic_manifest_sha256=semantic_sha,
        gpu_ids=(gpu_ids[0], gpu_ids[1]), batch_size=item["batch_size"], checkpoint_records=item["checkpoint_records"],
        admitted_hourly_rate_usd=float(hourly_rate), admission_sha256=admitted["admission_sha256"],
        component_hashes=dict(hashes), config_sha256=item["config_sha256"],
    )


def normalize_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).split())


def passage_texts(record: Mapping[str, Any]) -> list[str]:
    """Render the frozen title/abstract/claims passage view deterministically."""

    if set(record) != set(SOURCE_FIELDS):
        raise A6ExecutionError("source record does not match the approved A6 materialized schema")
    if any(not isinstance(record[field], str) for field in (
        "family_token", "publication_token", "title_en", "abstract_en", "claims_text",
    )):
        raise A6ExecutionError("source record has non-text materialized fields")
    if not isinstance(record["publication_ordinal"], int) or isinstance(record["publication_ordinal"], bool):
        raise A6ExecutionError("source record has invalid materialization provenance")
    if not isinstance(record["claims"], list) or any(not isinstance(value, str) for value in record["claims"]):
        raise A6ExecutionError("source record has invalid materialization provenance")
    if not record["family_token"].strip() or not record["publication_token"].strip():
        raise A6ExecutionError("source record has no opaque Owner-local identity")
    # The canonical source uses English-materialized names, while the frozen
    # A5 program commits the semantic title/abstract/claims field order.
    text = normalize_text(" ".join((record["title_en"], record["abstract_en"], record["claims_text"])))
    if not text:
        raise A6ExecutionError("source record has no frozen representation text")
    tokens = text.split(" ")
    step = CHUNK_SIZE - CHUNK_OVERLAP
    return [
        f"{DOCUMENT_PREFIX}{' '.join(tokens[offset:offset + CHUNK_SIZE])}"
        for offset in range(0, len(tokens), step)
    ]


def shard_for_family(family_id: str, shard_count: int = 2) -> int:
    if shard_count != 2:
        raise A6ExecutionError("A6 has exactly two deterministic GPU shards")
    return int(sha256(family_id.encode("utf-8")).hexdigest(), 16) % shard_count


def validate_source_inventory(config: ExecutionConfig) -> dict[int, int]:
    """Validate full committed source coverage without retaining raw rows.

    The full corpus is intentionally scanned before launch, but the scanner
    holds only opaque identifiers needed for uniqueness/accounting.  Passage
    text is constructed later inside the GPU worker, avoiding a second
    parent-owned in-memory corpus copy and costly spawn serialization.
    """

    shard_counts = {0: 0, 1: 0}
    seen_documents: set[str] = set()
    families: set[str] = set()
    with config.source_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise A6ExecutionError(f"source JSONL is invalid at row {line_number}") from error
            if not isinstance(record, dict):
                raise A6ExecutionError("source JSONL records must be objects")
            # This validates schema, identity fields, provenance fields, and
            # renderable frozen text without retaining a passage list.
            passage_texts(record)
            document_id = record["publication_token"]
            if document_id in seen_documents:
                raise A6ExecutionError("source document identities must be unique Owner-local values")
            seen_documents.add(document_id)
            family_id = record["family_token"]
            families.add(family_id)
            shard_counts[shard_for_family(family_id)] += 1
    if len(seen_documents) != config.expected_documents:
        raise A6ExecutionError("A6 source document coverage differs from the committed 45,336 records")
    if len(families) != config.expected_families:
        raise A6ExecutionError("A6 source family coverage differs from the committed inventory")
    if any(count <= 0 for count in shard_counts.values()):
        raise A6ExecutionError("A6 deterministic shard inventory is incomplete")
    return shard_counts


def iter_source_shard(
    config: ExecutionConfig, *, shard: int, maximum_records: int | None = None,
) -> Iterable[dict[str, Any]]:
    """Yield one validated deterministic shard without parent corpus buffering."""

    if shard not in (0, 1) or maximum_records is not None and maximum_records < 1:
        raise A6ExecutionError("A6 shard stream request is invalid")
    yielded = 0
    with config.source_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise A6ExecutionError(f"source JSONL is invalid at row {line_number}") from error
            if not isinstance(record, dict):
                raise A6ExecutionError("source JSONL records must be objects")
            if shard_for_family(str(record.get("family_token", ""))) != shard:
                continue
            passages = passage_texts(record)
            yield {"record": record, "passages": passages}
            yielded += 1
            if maximum_records is not None and yielded >= maximum_records:
                return


def validate_source_and_shard(config: ExecutionConfig, *, canary_documents: int | None = None) -> dict[int, list[dict[str, Any]]]:
    """Read the Owner-local source only after all bindings pass; never export rows."""

    rows: dict[int, list[dict[str, Any]]] = {0: [], 1: []}
    seen_documents: set[str] = set()
    families: set[str] = set()
    with config.source_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise A6ExecutionError(f"source JSONL is invalid at row {line_number}") from error
            if not isinstance(record, dict):
                raise A6ExecutionError("source JSONL records must be objects")
            passages = passage_texts(record)
            document_id = record["publication_token"]
            if document_id in seen_documents:
                raise A6ExecutionError("source document identities must be unique Owner-local values")
            seen_documents.add(document_id)
            family_id = record["family_token"]
            families.add(family_id)
            # The raw row stays only in the attempt root; its location is never a safe export.
            shard = shard_for_family(family_id)
            # A capacity canary must observe both admitted GPUs.  Select a
            # deterministic prefix per shard rather than an arbitrary global
            # prefix that can leave one GPU untested.
            if canary_documents is None or len(rows[shard]) < canary_documents:
                rows[shard].append({"record": record, "passages": passages})
            if canary_documents is not None and all(len(rows[index]) >= canary_documents for index in rows):
                break
    if canary_documents is None and len(seen_documents) != config.expected_documents:
        raise A6ExecutionError("A6 source document coverage differs from the committed 45,336 records")
    if canary_documents is None and len(families) != config.expected_families:
        raise A6ExecutionError("A6 source family coverage differs from the committed inventory")
    if not seen_documents or any(not rows[index] for index in rows):
        raise A6ExecutionError("A6 source has no records")
    return rows


def prepare_fresh_attempt(config: ExecutionConfig, *, owner_store_root: Path, attempt_root: Path) -> dict[str, Any]:
    """Create one immutable receipt proving a new, configuration-bound root."""

    root = owner_store_root.resolve()
    attempt = attempt_root.resolve()
    try:
        relative = attempt.relative_to(root).as_posix()
    except ValueError as error:
        raise A6ExecutionError("A6 attempt root must remain in Owner Store") from error
    if attempt.exists() or attempt.is_symlink():
        raise A6ExecutionError("A6 fresh attempt root already exists")
    attempt.mkdir(parents=True)
    body = {
        "schema_version": "myis.armindex-a6-fresh-attempt-root-receipt.v1",
        "status": "PASS_A6_FRESH_ATTEMPT_ROOT", "attempt_id": config.attempt_id,
        "attempt_root_pointer": relative, "config_sha256": config.config_sha256,
        "source_sha256": config.source_sha256, "protected_payload_included": False,
    }
    receipt = {**body, "fresh_attempt_root_receipt_sha256": canonical_sha256(body)}
    _atomic_json(attempt / "A6_FRESH_ATTEMPT_ROOT.json", receipt, immutable=True)
    return receipt


def validate_full_attempt_resume(config: ExecutionConfig, *, owner_store_root: Path, attempt_root: Path) -> dict[str, Any]:
    """Permit recovery only from the same full attempt's compatible checkpoints."""

    root = owner_store_root.resolve()
    attempt = attempt_root.resolve()
    try:
        relative = attempt.relative_to(root).as_posix()
    except ValueError as error:
        raise A6ExecutionError("A6 resume root must remain in Owner Store") from error
    if not attempt.is_dir() or attempt.is_symlink() or (attempt / "canary").exists():
        raise A6ExecutionError("A6 resume rejects canary, missing, or unsafe attempt roots")
    receipt = _self_hashed_receipt(
        attempt / "A6_FRESH_ATTEMPT_ROOT.json", schema="myis.armindex-a6-fresh-attempt-root-receipt.v1",
        digest_field="fresh_attempt_root_receipt_sha256", role="A6 fresh attempt root receipt",
    )
    expected = {
        "schema_version", "status", "attempt_id", "attempt_root_pointer", "config_sha256", "source_sha256",
        "protected_payload_included", "fresh_attempt_root_receipt_sha256",
    }
    if set(receipt) != expected or receipt.get("status") != "PASS_A6_FRESH_ATTEMPT_ROOT":
        raise A6ExecutionError("A6 resume root receipt is invalid")
    if (receipt["attempt_id"] != config.attempt_id or receipt["attempt_root_pointer"] != relative
            or receipt["config_sha256"] != config.config_sha256 or receipt["source_sha256"] != config.source_sha256
            or receipt["protected_payload_included"] is not False):
        raise A6ExecutionError("A6 resume root does not bind this exact attempt/config/source")
    for shard in (0, 1):
        checkpoint_path = attempt / "owner-local" / f"shard-{shard}" / "checkpoint.json"
        checkpoint = _self_hashed_receipt(
            checkpoint_path, schema="myis.armindex-a6-shard-checkpoint.v1", digest_field="checkpoint_sha256",
            role=f"A6 shard-{shard} resume checkpoint",
        )
        if checkpoint.get("attempt_id") != config.attempt_id or checkpoint.get("config_sha256") != config.config_sha256 or checkpoint.get("source_sha256") != config.source_sha256 or checkpoint.get("shard") != shard:
            raise A6ExecutionError("A6 resume checkpoint is foreign or incompatible")
        truncate_checkpoint_tails(
            vector_path=checkpoint_path.parent / "flat-l2-normalized.index.f32",
            metadata_path=checkpoint_path.parent / "metadata.jsonl", checkpoint=checkpoint,
        )
    return receipt


def _checkpoint(
    path: Path, config: ExecutionConfig, *, shard: int, records: int, chunks: int,
    vector_bytes: int, metadata_bytes: int, latency_bytes: int,
) -> None:
    body = {
        "schema_version": "myis.armindex-a6-shard-checkpoint.v1", "attempt_id": config.attempt_id,
        "config_sha256": config.config_sha256, "source_sha256": config.source_sha256, "shard": shard,
        "completed_records": records, "completed_chunks": chunks, "vector_bytes": vector_bytes,
        "metadata_bytes": metadata_bytes, "latency_bytes": latency_bytes,
        "protected_payload_included": False,
    }
    _atomic_json(path, {**body, "checkpoint_sha256": canonical_sha256(body)})


def truncate_checkpoint_tails(
    *, vector_path: Path, metadata_path: Path, checkpoint: Mapping[str, Any], latency_path: Path | None = None,
) -> None:
    """Return both durable shard streams to their jointly checkpointed prefix."""

    try:
        vector_bytes = int(checkpoint["vector_bytes"])
        metadata_bytes = int(checkpoint["metadata_bytes"])
    except (KeyError, TypeError, ValueError) as error:
        raise A6ExecutionError("A6 checkpoint byte commitments are invalid") from error
    if vector_bytes < 0 or metadata_bytes < 0 or not vector_path.is_file() or not metadata_path.is_file():
        raise A6ExecutionError("A6 checkpoint output streams are unavailable")
    if vector_path.stat().st_size < vector_bytes or metadata_path.stat().st_size < metadata_bytes:
        raise A6ExecutionError("A6 checkpoint vector bytes are incompatible")
    paths = [(vector_path, vector_bytes), (metadata_path, metadata_bytes)]
    if latency_path is not None:
        try:
            latency_bytes = int(checkpoint["latency_bytes"])
        except (KeyError, TypeError, ValueError) as error:
            raise A6ExecutionError("A6 checkpoint latency commitment is invalid") from error
        if latency_bytes < 0 or not latency_path.is_file() or latency_path.stat().st_size < latency_bytes:
            raise A6ExecutionError("A6 checkpoint latency bytes are incompatible")
        paths.append((latency_path, latency_bytes))
    for path, committed in paths:
        with path.open("r+b") as handle:
            handle.truncate(committed)
            handle.flush()
            os.fsync(handle.fileno())


def _percentiles_from_histogram(histogram: Mapping[str, int], count: int) -> tuple[float, float, float]:
    """Return conservative upper-bound quantiles from a mergeable histogram."""

    if count <= 0:
        return (0.0, 0.0, 0.0)
    parsed = sorted((float(key.lstrip(">")), value) for key, value in histogram.items())
    def pick(quantile: float) -> float:
        target = math.ceil(quantile * count)
        accumulated = 0
        for bound, observed in parsed:
            accumulated += observed
            if accumulated >= target:
                return bound
        return parsed[-1][0]
    return (pick(0.50), pick(0.95), pick(0.99))


def merge_latency_histograms(rows: Iterable[Mapping[str, Any]]) -> tuple[dict[str, int], int, tuple[float, float, float]]:
    """Merge shard telemetry before estimating global conservative percentiles."""

    histogram: Counter[str] = Counter()
    count = 0
    for row in rows:
        values = row.get("latency_histogram")
        observed = row.get("latency_count")
        if not isinstance(values, Mapping) or not isinstance(observed, int) or observed < 0:
            raise A6ExecutionError("A6 shard latency histogram is invalid")
        if any(not isinstance(key, str) or not isinstance(value, int) or value < 0 for key, value in values.items()):
            raise A6ExecutionError("A6 shard latency histogram buckets are invalid")
        if sum(values.values()) != observed:
            raise A6ExecutionError("A6 shard latency histogram count drifted")
        histogram.update(values)
        count += observed
    if count <= 0:
        raise A6ExecutionError("A6 latency histogram has no observations")
    merged = dict(sorted(histogram.items()))
    return merged, count, _percentiles_from_histogram(merged, count)


def build_owner_store_index_manifest(
    config: ExecutionConfig, *, shard: int, shard_root: Path, vector_path: Path, metadata_path: Path,
    records: int, family_count: int, chunks: int, latency_histogram: Mapping[str, int], latency_count: int,
    latency_sum_ms: float,
) -> dict[str, Any]:
    """Describe an Owner-Store index shard without disclosing its locators."""

    body = {
        "schema_version": "myis.armindex-a6-owner-store-index-manifest.v1", "attempt_id": config.attempt_id,
        "shard": shard, "arm_id": ARM_ID, "model_id": MODEL_ID,
        "program_sha256": config.component_hashes["representation_program_sha256"],
        "source_sha256": config.source_sha256, "config_sha256": config.config_sha256,
        "index_path": vector_path.name, "index_sha256": file_sha256(vector_path), "metadata_path": metadata_path.name,
        "metadata_sha256": file_sha256(metadata_path), "document_count": records, "family_count": family_count,
        "chunk_count": chunks, "vector_count": chunks, "vector_dimension": 1024,
        "vector_dtype": "float32_le", "vector_normalization": "l2_unit", "layout": "concatenated_row_major",
        "shard_vector_offset": 0, "metadata_mapping_scope": "owner_store_only_document_to_chunk_locator",
        "latency_histogram": dict(sorted(latency_histogram.items())), "latency_count": latency_count,
        "latency_sum_ms": round(latency_sum_ms, 6), "protected_payload_included": False,
    }
    try:
        assert_aggregate_only(body)
    except ValueError as error:
        raise A6ExecutionError("A6 Owner-Store index manifest crosses protected boundary") from error
    result = {**body, "manifest_sha256": canonical_sha256(body)}
    _atomic_json(shard_root / "INDEX_MANIFEST.json", result, immutable=True)
    return result


def run_shard(
    config: ExecutionConfig,
    *,
    shard: int,
    rows: Iterable[Mapping[str, Any]],
    attempt_root: Path,
) -> dict[str, Any]:
    """Embed a deterministic shard and checkpoint only durable Owner-Store bytes.

    This is designed to run once per GPU in separate processes.  The caller is
    responsible for process supervision; the returned value is aggregate-only.
    """

    enforce_offline_environment()
    try:
        import numpy as np
        import torch
        from sentence_transformers import SentenceTransformer
    except ImportError as error:  # pragma: no cover - exercised on the remote image
        raise A6ExecutionError("A6 runtime requires numpy, torch, and sentence-transformers") from error
    _require_offline_runtime(config.runtime_packages)
    device = f"cuda:{config.gpu_ids[shard]}"
    if not torch.cuda.is_available() or torch.cuda.device_count() <= config.gpu_ids[shard]:
        raise A6ExecutionError("the admitted A6 GPU topology is unavailable")
    shard_root = attempt_root / "owner-local" / f"shard-{shard}"
    shard_root.mkdir(parents=True, exist_ok=True)
    # A normalized flat shard is the frozen A5 index kind.  The file contains
    # no exportable metadata; family/document locators remain next to it only
    # inside Owner Store.
    vector_path = shard_root / "flat-l2-normalized.index.f32"
    metadata_path = shard_root / "metadata.jsonl"
    latency_path = shard_root / "latency-ms-per-batch.jsonl"
    checkpoint_path = shard_root / "checkpoint.json"
    if vector_path.is_symlink() or metadata_path.is_symlink() or latency_path.is_symlink():
        raise A6ExecutionError("A6 shard output path is unsafe")
    checkpoint_records = 0
    checkpoint_chunks = 0
    if checkpoint_path.exists():
        state = _load_json(checkpoint_path, "A6 shard checkpoint")
        checkpoint_hash = state.pop("checkpoint_sha256", None)
        if checkpoint_hash != canonical_sha256(state):
            raise A6ExecutionError("A6 checkpoint self-hash drifted")
        if state.get("config_sha256") != config.config_sha256 or state.get("source_sha256") != config.source_sha256 or state.get("shard") != shard:
            raise A6ExecutionError("A6 checkpoint is incompatible with this fresh attempt")
        checkpoint_records, checkpoint_chunks = int(state["completed_records"]), int(state["completed_chunks"])
        if checkpoint_records < 0 or checkpoint_chunks < 0:
            raise A6ExecutionError("A6 checkpoint coverage is invalid")
        # A power loss can leave a durable prefix followed by an incomplete
        # tail.  The checkpoint binds both streams, so only that exact prefix
        # is compatible with resumption.
        truncate_checkpoint_tails(
            vector_path=vector_path, metadata_path=metadata_path, latency_path=latency_path, checkpoint=state,
        )
    model = SentenceTransformer(str(config.model_path), device=device, local_files_only=True)
    records = checkpoint_records
    chunks = checkpoint_chunks
    latency_histogram = Counter()
    latency_count = 0
    latency_sum = 0.0
    if latency_path.exists():
        try:
            for line in latency_path.read_text(encoding="utf-8").splitlines():
                if not line:
                    continue
                latency_ms = float(line)
                bucket = next((str(bound) for bound in LATENCY_BUCKETS_MS if latency_ms <= bound), f">{LATENCY_BUCKETS_MS[-1]}" )
                latency_histogram[bucket] += 1
                latency_count += 1
                latency_sum += latency_ms
        except ValueError as error:
            raise A6ExecutionError("A6 latency ledger is invalid") from error
    shard_families: set[str] = set()
    skipped_records = 0
    next_checkpoint = ((records // config.checkpoint_records) + 1) * config.checkpoint_records
    def encode_batch(passages: list[str], vectors: Any, latency: Any) -> None:
        nonlocal latency_count, latency_sum
        if not passages or len(passages) > config.batch_size:
            raise A6ExecutionError("A6 passage batch exceeds the admitted hard bound")
        started = time.perf_counter()
        encoded = model.encode(
            passages, batch_size=config.batch_size, convert_to_numpy=True,
            normalize_embeddings=True, show_progress_bar=False,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        encoded = np.asarray(encoded, dtype=np.float32)
        if encoded.ndim != 2 or encoded.shape[0] != len(passages) or encoded.shape[1] != 1024:
            raise A6ExecutionError("ARM-03 embedding dimensions drifted from the frozen model adapter")
        vectors.write(encoded.tobytes(order="C"))
        vectors.flush()
        os.fsync(vectors.fileno())
        batch_latency = elapsed_ms / len(passages)
        latency.write(f"{batch_latency:.9f}\n")
        latency.flush()
        os.fsync(latency.fileno())
        bucket = next((str(bound) for bound in LATENCY_BUCKETS_MS if batch_latency <= bound), f">{LATENCY_BUCKETS_MS[-1]}" )
        latency_histogram[bucket] += 1
        latency_count += 1
        latency_sum += batch_latency
    with (vector_path.open("ab") as vectors, metadata_path.open("a", encoding="utf-8") as metadata,
          latency_path.open("a", encoding="utf-8") as latency):
        for item in rows:
            shard_families.add(str(item["record"]["family_token"]))
            if skipped_records < checkpoint_records:
                skipped_records += 1
                continue
            passages = item["passages"]
            for start in range(0, len(passages), config.batch_size):
                encode_batch(passages[start:start + config.batch_size], vectors, latency)
            metadata.write(json.dumps({
                "publication_token": item["record"]["publication_token"], "family_token": item["record"]["family_token"],
                "chunk_count": len(passages),
            }, ensure_ascii=True) + "\n")
            metadata.flush()
            os.fsync(metadata.fileno())
            records += 1
            chunks += len(passages)
            if records >= next_checkpoint:
                _checkpoint(
                    checkpoint_path, config, shard=shard, records=records, chunks=chunks,
                    vector_bytes=vector_path.stat().st_size, metadata_bytes=metadata_path.stat().st_size,
                    latency_bytes=latency_path.stat().st_size,
                )
                next_checkpoint = ((records // config.checkpoint_records) + 1) * config.checkpoint_records
    if skipped_records != checkpoint_records:
        raise A6ExecutionError("A6 checkpoint exceeds compatible source shard coverage")
    _checkpoint(
        checkpoint_path, config, shard=shard, records=records, chunks=chunks,
        vector_bytes=vector_path.stat().st_size, metadata_bytes=metadata_path.stat().st_size,
        latency_bytes=latency_path.stat().st_size,
    )
    torch.cuda.synchronize(config.gpu_ids[shard])
    p50, p95, p99 = _percentiles_from_histogram(latency_histogram, latency_count)
    index_manifest = build_owner_store_index_manifest(
        config, shard=shard, shard_root=shard_root, vector_path=vector_path, metadata_path=metadata_path,
        records=records, family_count=len(shard_families), chunks=chunks, latency_histogram=latency_histogram,
        latency_count=latency_count, latency_sum_ms=latency_sum,
    )
    return {
        "shard": shard, "document_count": records, "family_count": len(shard_families),
        "chunk_count": chunks, "representation_count": chunks,
        "index_sha256": file_sha256(vector_path), "index_size_bytes": vector_path.stat().st_size,
        "index_manifest_sha256": index_manifest["manifest_sha256"],
        "latency_p50_ms": round(p50, 6), "latency_p95_ms": round(p95, 6), "latency_p99_ms": round(p99, 6),
        "latency_histogram": dict(sorted(latency_histogram.items())), "latency_count": latency_count,
        "ram_bytes_peak": int(getattr(resource.getrusage(resource.RUSAGE_SELF), "ru_maxrss", 0)) * 1024 if resource else 0,
        "vram_bytes_peak": int(torch.cuda.max_memory_allocated(config.gpu_ids[shard])),
        "failure_taxonomy": {}, "protected_payload_included": False,
    }


def build_safe_return_manifest(
    config: ExecutionConfig,
    shard_results: Iterable[Mapping[str, Any]],
    *,
    elapsed_seconds: float,
    recovery_count: int,
    safe_export_root: Path,
) -> dict[str, Any]:
    """Create the only A6 artifact eligible to leave Owner Store."""

    rows = [dict(row) for row in shard_results]
    if len(rows) != 2 or {row.get("shard") for row in rows} != {0, 1}:
        raise A6ExecutionError("A6 requires two completed deterministic shard receipts")
    document_count = sum(int(row["document_count"]) for row in rows)
    if document_count != config.expected_documents:
        raise A6ExecutionError("A6 aggregate coverage is incomplete")
    family_count = sum(int(row["family_count"]) for row in rows)
    if family_count != config.expected_families:
        raise A6ExecutionError("A6 aggregate family coverage is incomplete")
    chunk_count = sum(int(row["chunk_count"]) for row in rows)
    failures: Counter[str] = Counter()
    for row in rows:
        failures.update(dict(row["failure_taxonomy"]))
    latency_histogram, latency_count, (latency_p50, latency_p95, latency_p99) = merge_latency_histograms(rows)
    deterministic = canonical_sha256({"source": config.source_sha256, "config": config.config_sha256, "indexes": [row["index_sha256"] for row in sorted(rows, key=lambda value: value["shard"])]})
    body = {
        "schema_version": "myis.armindex-a6-safe-return-manifest.v1", "status": "PASS_A6_FULL_DAPFAM_MATERIALIZATION",
        "attempt_id": config.attempt_id, "arm_id": ARM_ID, "model_id": MODEL_ID,
        "source_document_count": document_count, "family_count": family_count,
        "chunk_count": chunk_count, "representation_count": chunk_count, "coverage_rate": 1.0,
        "throughput_documents_per_second": round(document_count / elapsed_seconds, 6) if elapsed_seconds else 0.0,
        "latency_p50_ms": latency_p50, "latency_p95_ms": latency_p95, "latency_p99_ms": latency_p99,
        "latency_histogram": latency_histogram, "latency_count": latency_count,
        "ram_bytes_peak": max(int(row["ram_bytes_peak"]) for row in rows), "vram_bytes_peak": max(int(row["vram_bytes_peak"]) for row in rows),
        "index_size_bytes": sum(int(row["index_size_bytes"]) for row in rows), "cost_usd": round(config.admitted_hourly_rate_usd * elapsed_seconds / 3600, 6),
        "checkpoint_recovery_count": int(recovery_count), "determinism_sha256": deterministic,
        "failure_taxonomy": dict(sorted(failures.items())), "component_hashes": dict(config.component_hashes),
        "source_sha256": config.source_sha256, "source_snapshot_receipt_sha256": config.source_snapshot_receipt_sha256,
        "model_manifest_sha256": config.model_manifest_sha256, "admission_sha256": config.admission_sha256,
        "runtime_receipt_sha256": config.runtime_receipt_sha256,
        "semantic_manifest_sha256": config.semantic_manifest_sha256,
        "config_sha256": config.config_sha256,
        "selection_accesses": 0, "final_accesses": 0, "protected_payload_included": False,
        "claim_boundary": "post_confirmatory_frozen_winner_full_corpus_materialization_and_scalability_only_no_quality_or_comparative_claim",
    }
    try:
        assert_aggregate_only(body)
    except ValueError as error:
        raise A6ExecutionError("A6 safe return contains protected data") from error
    result = {**body, "safe_return_sha256": canonical_sha256(body)}
    safe_export_root.mkdir(parents=True, exist_ok=True)
    _atomic_json(safe_export_root / "A6_SAFE_RETURN_MANIFEST.json", result, immutable=True)
    return result


def build_canary_receipt(
    config: ExecutionConfig, shard_results: Iterable[Mapping[str, Any]], *, elapsed_seconds: float,
) -> dict[str, Any]:
    """Build an immutable aggregate-only capacity/determinism canary receipt."""

    rows = [dict(row) for row in shard_results]
    if len(rows) != 2 or {row.get("shard") for row in rows} != {0, 1}:
        raise A6ExecutionError("A6 canary requires both GPU shard observations")
    index_hashes = [str(row["index_sha256"]) for row in sorted(rows, key=lambda value: value["shard"])]
    latency_histogram, latency_count, (latency_p50, latency_p95, latency_p99) = merge_latency_histograms(rows)
    body = {
        "schema_version": "myis.armindex-a6-deterministic-canary-receipt.v1",
        "status": "PASS_A6_DETERMINISTIC_CANARY", "attempt_id": config.attempt_id,
        "processed_documents": sum(int(row["document_count"]) for row in rows),
        "processed_families": sum(int(row["family_count"]) for row in rows),
        "chunk_count": sum(int(row["chunk_count"]) for row in rows),
        "index_size_bytes": sum(int(row["index_size_bytes"]) for row in rows),
        "ram_bytes_peak": max(int(row["ram_bytes_peak"]) for row in rows),
        "vram_bytes_peak": max(int(row["vram_bytes_peak"]) for row in rows),
        "latency_p50_ms": latency_p50, "latency_p95_ms": latency_p95, "latency_p99_ms": latency_p99,
        "latency_histogram": latency_histogram, "latency_count": latency_count,
        "index_sha256s": index_hashes, "elapsed_seconds": round(elapsed_seconds, 6),
        "cost_usd": round(config.admitted_hourly_rate_usd * elapsed_seconds / 3600, 6),
        "determinism_sha256": canonical_sha256({"config": config.config_sha256, "source": config.source_sha256, "indexes": index_hashes}),
        "source_sha256": config.source_sha256, "config_sha256": config.config_sha256,
        "admission_sha256": config.admission_sha256, "runtime_receipt_sha256": config.runtime_receipt_sha256,
        "semantic_manifest_sha256": config.semantic_manifest_sha256,
        "protected_payload_included": False,
    }
    try:
        assert_aggregate_only(body)
    except ValueError as error:
        raise A6ExecutionError("A6 canary contains protected data") from error
    return {**body, "canary_receipt_sha256": canonical_sha256(body)}


def build_failure_receipt(
    config: ExecutionConfig, *, stage: str, worker_exit_codes: Iterable[int | None], completed_messages: int,
) -> dict[str, Any]:
    """Return a bounded aggregate-safe failure disposition for launcher faults."""

    if stage not in {"full", "canary"}:
        raise A6ExecutionError("A6 failure stage is invalid")
    exits = list(worker_exit_codes)
    if len(exits) != 2 or any(code is not None and not isinstance(code, int) for code in exits):
        raise A6ExecutionError("A6 worker exit observation is invalid")
    taxonomy = Counter()
    for code in exits:
        if code is None:
            taxonomy["worker_not_terminated"] += 1
        elif code != 0:
            taxonomy["worker_nonzero_exit"] += 1
    if completed_messages < 2:
        taxonomy["worker_missing_queue_message"] += 2 - completed_messages
    body = {
        "schema_version": "myis.armindex-a6-launch-failure-receipt.v1", "status": "STOP_A6_WITH_OPERATIONAL_EVIDENCE",
        "attempt_id": config.attempt_id, "stage": stage, "config_sha256": config.config_sha256,
        "source_sha256": config.source_sha256, "admission_sha256": config.admission_sha256,
        "worker_exit_codes": [code if code is not None else "UNKNOWN" for code in exits],
        "completed_worker_messages": completed_messages, "failure_taxonomy": dict(sorted(taxonomy.items())),
        "selection_accesses": 0, "final_accesses": 0, "protected_payload_included": False,
    }
    return {**body, "failure_receipt_sha256": canonical_sha256(body)}


__all__ = [
    "A6ExecutionError", "ExecutionConfig", "EXPECTED_DOCUMENT_COUNT", "build_canary_receipt", "build_owner_store_index_manifest", "build_safe_return_manifest",
    "build_failure_receipt", "enforce_offline_environment", "load_execution_config", "merge_latency_histograms", "model_tree_sha256", "normalize_text", "passage_texts", "prepare_fresh_attempt", "run_shard", "shard_for_family", "truncate_checkpoint_tails", "validate_full_attempt_resume", "validate_source_and_shard", "write_aggregate_safe_receipt",
]
