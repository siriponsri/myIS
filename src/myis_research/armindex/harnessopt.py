"""Validated HarnessOpt configuration and immutable batch boundaries."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from decimal import Decimal
import re
from typing import Any

from ..kernel.canonical import canonical_sha256


HARNESS_BATCH_ROLES = (
    "quality_exploit",
    "cost_latency_ablation",
    "routing_hypothesis",
    "diversity_profile",
)
RUNTIME_FEATURES = frozenset(
    {"query_length", "token_count", "script", "language_hint", "system_load", "cache_state"}
)
MUTABLE_SURFACES = frozenset(
    {
        "harness_id",
        "profile",
        "arm_ids",
        "invocation_order",
        "execution_mode",
        "initial_depth_by_arm",
        "maximum_depth_by_arm",
        "fusion",
        "routing",
        "early_stop",
        "cache_policy",
        "latency_profile",
        "runtime_features",
        "config_sha256",
    }
)
_CONFIG_KEYS = MUTABLE_SURFACES | {"schema_version", "frozen_bindings_sha256"}
_BATCH_KEYS = frozenset(
    {
        "schema_version",
        "batch_id",
        "iteration",
        "frozen_bindings_sha256",
        "status",
        "candidates",
        "batch_sha256",
    }
)
_CANDIDATE_KEYS = frozenset(
    {
        "candidate_id",
        "role",
        "hypothesis",
        "matched_ablation_id",
        "scientific_payload_sha256",
        "configuration",
        "verifier_status",
    }
)
_FORBIDDEN_KEYS = frozenset(
    {
        "qrel",
        "qrels",
        "in_out_label",
        "split_label",
        "domain_label",
        "ipc_cpc_out_shortcut",
        "per_query_correctness_history",
        "selection_feedback",
        "final_feedback",
        "query_rewriting",
        "llm",
        "model",
        "model_weights",
        "representation",
        "representation_program",
        "python",
        "code",
        "callable",
    }
)
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_STABLE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]+$")


class HarnessOptError(ValueError):
    """Raised when a harness candidate crosses its frozen boundary."""


def validate_harness_configuration(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a deterministic label-free harness configuration."""

    config = deepcopy(dict(value))
    if set(config) != _CONFIG_KEYS:
        raise HarnessOptError("harness configuration fields do not match the v2 contract")
    if config["schema_version"] != "myis.armindex-harness.v2":
        raise HarnessOptError("unsupported HarnessOpt configuration schema")
    if not _STABLE_ID.fullmatch(str(config["harness_id"])):
        raise HarnessOptError("harness_id is not stable lowercase text")
    if config["profile"] not in {"FAST", "BALANCED", "DEEP"}:
        raise HarnessOptError("unknown production profile")
    _require_sha256(config["frozen_bindings_sha256"], "frozen_bindings_sha256")
    _reject_forbidden_content(config)

    arm_ids = config["arm_ids"]
    invocation_order = config["invocation_order"]
    if (
        not isinstance(arm_ids, list)
        or not arm_ids
        or len(arm_ids) != len(set(arm_ids))
        or any(not re.fullmatch(r"ARM-0[1-5]", str(item)) for item in arm_ids)
    ):
        raise HarnessOptError("harness arm_ids must be unique active ArmIndex arms")
    if not isinstance(invocation_order, list) or set(invocation_order) != set(arm_ids) or len(invocation_order) != len(arm_ids):
        raise HarnessOptError("invocation_order must be a deterministic permutation of arm_ids")
    if config["execution_mode"] not in {"parallel", "sequential"}:
        raise HarnessOptError("execution_mode must be parallel or sequential")
    _validate_depths(config["initial_depth_by_arm"], config["maximum_depth_by_arm"], arm_ids)
    _validate_fusion(config["fusion"], arm_ids)

    features = config["runtime_features"]
    if (
        not isinstance(features, list)
        or features != sorted(set(features))
        or not set(features) <= RUNTIME_FEATURES
    ):
        raise HarnessOptError("runtime features must be a sorted subset of the label-free allowlist")
    _validate_routing(config["routing"], arm_ids, set(features))
    _validate_early_stop(config["early_stop"])
    if config["cache_policy"] not in {"off", "read_through", "frozen_read_only"}:
        raise HarnessOptError("cache policy is unsupported")
    if config["latency_profile"] not in {"fast", "balanced", "deep"}:
        raise HarnessOptError("latency profile is unsupported")
    if config["profile"] == "FAST":
        if (
            "ARM-01" not in arm_ids
            or len(arm_ids) > 2
            or config["execution_mode"] != "sequential"
            or config["early_stop"]["max_escalations"] > 1
        ):
            raise HarnessOptError("FAST requires BM25, at most two arms, and one synchronous escalation")

    unsigned = {key: item for key, item in config.items() if key != "config_sha256"}
    if config["config_sha256"] != canonical_sha256(unsigned):
        raise HarnessOptError("harness configuration self-hash is invalid")
    return config


def detect_forbidden_mutations(
    incumbent: Mapping[str, Any], candidate: Mapping[str, Any]
) -> tuple[str, ...]:
    """Return changed JSON paths outside the HarnessOpt mutable surface."""

    left, right = dict(incumbent), dict(candidate)
    changed = _changed_paths(left, right)
    forbidden = []
    for path in changed:
        top_level = path.split(".", 1)[0]
        if top_level not in MUTABLE_SURFACES:
            forbidden.append(path)
    return tuple(sorted(forbidden))


def validate_harness_batch(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate an exact-four HarnessOpt batch frozen before evaluation."""

    batch = deepcopy(dict(value))
    if set(batch) != _BATCH_KEYS:
        raise HarnessOptError("HarnessOpt batch fields do not match the v1 contract")
    if batch["schema_version"] != "myis.armindex-harness-batch.v1":
        raise HarnessOptError("unsupported HarnessOpt batch schema")
    if batch["status"] != "frozen_before_evaluation":
        raise HarnessOptError("HarnessOpt batch must be frozen before evaluation")
    if not _STABLE_ID.fullmatch(str(batch["batch_id"])):
        raise HarnessOptError("HarnessOpt batch_id is not stable lowercase text")
    if isinstance(batch["iteration"], bool) or int(batch["iteration"]) not in {1, 2, 3}:
        raise HarnessOptError("HarnessOpt iteration must be one, two, or three")
    _require_sha256(batch["frozen_bindings_sha256"], "frozen_bindings_sha256")

    candidates = batch["candidates"]
    if not isinstance(candidates, list) or len(candidates) != 4:
        raise HarnessOptError("HarnessOpt batch requires exactly four candidates")
    if tuple(item.get("role") for item in candidates if isinstance(item, Mapping)) != HARNESS_BATCH_ROLES:
        raise HarnessOptError("HarnessOpt batch roles and order are not canonical")

    ids: list[str] = []
    payloads: list[str] = []
    for candidate in candidates:
        if not isinstance(candidate, Mapping) or set(candidate) != _CANDIDATE_KEYS:
            raise HarnessOptError("HarnessOpt candidate fields do not match the v1 contract")
        candidate_id = str(candidate["candidate_id"])
        if not _STABLE_ID.fullmatch(candidate_id) or not str(candidate["hypothesis"]).strip():
            raise HarnessOptError("HarnessOpt candidate identity and hypothesis are required")
        _require_sha256(candidate["scientific_payload_sha256"], "scientific_payload_sha256")
        if candidate["verifier_status"] != "accepted":
            raise HarnessOptError("HarnessOpt candidate requires verifier acceptance")
        config = validate_harness_configuration(candidate["configuration"])
        if config["frozen_bindings_sha256"] != batch["frozen_bindings_sha256"]:
            raise HarnessOptError("HarnessOpt candidate changed the frozen bindings")
        ids.append(candidate_id)
        payloads.append(str(candidate["scientific_payload_sha256"]))
    if len(ids) != len(set(ids)) or len(payloads) != len(set(payloads)):
        raise HarnessOptError("HarnessOpt candidate IDs and scientific payloads must be unique")
    exploit, ablation = candidates[:2]
    if (
        exploit["matched_ablation_id"] != ablation["candidate_id"]
        or ablation["matched_ablation_id"] != exploit["candidate_id"]
    ):
        raise HarnessOptError("quality exploit and matched ablation must bind each other")
    if any(item["matched_ablation_id"] is not None for item in candidates[2:]):
        raise HarnessOptError("routing and diversity candidates cannot claim a matched ablation")
    unsigned = {key: item for key, item in batch.items() if key != "batch_sha256"}
    if batch["batch_sha256"] != canonical_sha256(unsigned):
        raise HarnessOptError("HarnessOpt batch self-hash is invalid")
    return batch


def _validate_depths(initial: Any, maximum: Any, arm_ids: list[str]) -> None:
    if not isinstance(initial, Mapping) or not isinstance(maximum, Mapping):
        raise HarnessOptError("harness depths must be mappings")
    if set(initial) != set(arm_ids) or set(maximum) != set(arm_ids):
        raise HarnessOptError("harness depths must bind every selected arm")
    for arm_id in arm_ids:
        first, last = initial[arm_id], maximum[arm_id]
        if (
            isinstance(first, bool)
            or isinstance(last, bool)
            or not isinstance(first, int)
            or not isinstance(last, int)
            or first <= 0
            or last < first
            or last > 2000
        ):
            raise HarnessOptError("initial and maximum depths are invalid")


def _validate_fusion(value: Any, arm_ids: list[str]) -> None:
    if not isinstance(value, Mapping) or set(value) != {"method", "rrf_k", "weights"}:
        raise HarnessOptError("fusion fields do not match the v1 contract")
    if value["method"] not in {"rrf", "weighted_rrf", "normalized_rank_sum"}:
        raise HarnessOptError("fusion method is unsupported")
    if isinstance(value["rrf_k"], bool) or not isinstance(value["rrf_k"], int) or value["rrf_k"] <= 0:
        raise HarnessOptError("fusion rrf_k must be positive")
    weights = value["weights"]
    if not isinstance(weights, Mapping) or set(weights) != set(arm_ids):
        raise HarnessOptError("fusion weights must bind every selected arm")
    for weight in weights.values():
        numeric = Decimal(str(weight))
        if not numeric.is_finite() or numeric < 0:
            raise HarnessOptError("fusion weights must be finite and non-negative")


def _validate_routing(value: Any, arm_ids: list[str], features: set[str]) -> None:
    if not isinstance(value, list):
        raise HarnessOptError("routing must be a list of bounded rules")
    activated: set[str] = set()
    for rule in value:
        if not isinstance(rule, Mapping) or set(rule) != {"feature", "operator", "threshold", "activate_arm_id"}:
            raise HarnessOptError("routing rule fields do not match the v1 contract")
        if rule["feature"] not in features or rule["operator"] not in {"eq", "gte", "lte"}:
            raise HarnessOptError("routing rule feature or operator is unsupported")
        if rule["activate_arm_id"] not in arm_ids or rule["activate_arm_id"] in activated:
            raise HarnessOptError("routing activation arms must be selected and unique")
        if isinstance(rule["threshold"], (Mapping, list, tuple)) or callable(rule["threshold"]):
            raise HarnessOptError("routing threshold must be a scalar")
        activated.add(str(rule["activate_arm_id"]))


def _validate_early_stop(value: Any) -> None:
    if not isinstance(value, Mapping) or set(value) != {"max_escalations", "score_margin", "rank_stability"}:
        raise HarnessOptError("early-stop fields do not match the v1 contract")
    escalations = value["max_escalations"]
    if isinstance(escalations, bool) or not isinstance(escalations, int) or not 0 <= escalations <= 4:
        raise HarnessOptError("max_escalations must be between zero and four")
    for key in ("score_margin", "rank_stability"):
        numeric = Decimal(str(value[key]))
        if not numeric.is_finite() or not 0 <= numeric <= 1:
            raise HarnessOptError(f"{key} must be in [0, 1]")


def _reject_forbidden_content(value: Any, path: str = "$") -> None:
    if callable(value):
        raise HarnessOptError(f"arbitrary executable content is forbidden at {path}")
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).casefold().replace("-", "_")
            if normalized in _FORBIDDEN_KEYS:
                raise HarnessOptError(f"forbidden harness feature at {path}.{key}")
            _reject_forbidden_content(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_forbidden_content(item, f"{path}[{index}]")


def _changed_paths(left: Any, right: Any, prefix: str = "") -> set[str]:
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        output: set[str] = set()
        for key in set(left) | set(right):
            path = f"{prefix}.{key}" if prefix else str(key)
            if key not in left or key not in right:
                output.add(path)
            else:
                output |= _changed_paths(left[key], right[key], path)
        return output
    return set() if left == right else {prefix}


def _require_sha256(value: Any, field: str) -> None:
    if not _SHA256.fullmatch(str(value)):
        raise HarnessOptError(f"{field} must be SHA-256")
