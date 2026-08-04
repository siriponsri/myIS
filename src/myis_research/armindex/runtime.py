"""Label-free deterministic HarnessOpt action planning."""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

from ..kernel.canonical import canonical_sha256
from .harnessopt import RUNTIME_FEATURES, HarnessOptError, validate_harness_configuration


_LABEL_VALUES = frozenset({"in", "out", "selection", "final", "held_out", "held-out"})


class RuntimeContractError(ValueError):
    """Raised when runtime input is not derived from the label-free allowlist."""


def validate_runtime_signals(
    value: Mapping[str, Any], *, enabled_features: tuple[str, ...] | list[str]
) -> dict[str, Any]:
    """Accept only exact, typed, label-free runtime feature values."""

    enabled = tuple(enabled_features)
    if len(enabled) != len(set(enabled)) or not set(enabled) <= RUNTIME_FEATURES:
        raise RuntimeContractError("enabled runtime features are not allowlisted")
    signals = dict(value)
    if set(signals) != set(enabled):
        raise RuntimeContractError("runtime signals must match the enabled feature set exactly")
    for key, item in signals.items():
        if key in {"query_length", "token_count"}:
            if isinstance(item, bool) or not isinstance(item, int) or item < 0:
                raise RuntimeContractError(f"{key} must be a non-negative integer")
        elif key == "system_load":
            if isinstance(item, bool) or not isinstance(item, (int, float)) or not 0 <= float(item) <= 1:
                raise RuntimeContractError("system_load must be in [0, 1]")
        elif key == "cache_state":
            if item not in {"hit", "miss", "unavailable"}:
                raise RuntimeContractError("cache_state is invalid")
        elif key == "script":
            if not isinstance(item, str) or len(item) != 4 or not item.isalpha() or not item[0].isupper():
                raise RuntimeContractError("script must be a four-letter ISO 15924-style code")
        elif key == "language_hint":
            if (
                not isinstance(item, str)
                or not 2 <= len(item) <= 15
                or any(part == "" or not part.isalnum() for part in item.split("-"))
            ):
                raise RuntimeContractError("language_hint must be a bounded language tag")
        if isinstance(item, str):
            tokens = set(re.split(r"[^a-z0-9]+", item.casefold()))
            if tokens & _LABEL_VALUES:
                raise RuntimeContractError("runtime values cannot encode split or IN/OUT labels")
    return signals


def build_execution_plan(
    configuration: Mapping[str, Any], runtime_signals: Mapping[str, Any]
) -> dict[str, Any]:
    """Compile one deterministic, hash-chained arm action plan."""

    try:
        config = validate_harness_configuration(configuration)
    except HarnessOptError as error:
        raise RuntimeContractError(str(error)) from error
    signals = validate_runtime_signals(
        runtime_signals,
        enabled_features=config["runtime_features"],
    )
    active_arms = _active_arms(config, signals)
    events: list[dict[str, Any]] = []
    prior_sha256 = "0" * 64
    for sequence, arm_id in enumerate(active_arms, start=1):
        body: dict[str, Any] = {
            "schema_version": "myis.armindex-harness-action.v1",
            "sequence": sequence,
            "action": "invoke_arm",
            "arm_id": arm_id,
            "depth": config["initial_depth_by_arm"][arm_id],
            "execution_mode": config["execution_mode"],
            "reason": "fixed_plan" if not config["routing"] else "label_free_route",
            "configuration_sha256": config["config_sha256"],
            "previous_action_sha256": prior_sha256,
        }
        body["action_sha256"] = canonical_sha256(body)
        prior_sha256 = str(body["action_sha256"])
        events.append(body)
    plan: dict[str, Any] = {
        "schema_version": "myis.armindex-execution-plan.v1",
        "configuration_sha256": config["config_sha256"],
        "runtime_signal_sha256": canonical_sha256(signals),
        "actions": events,
        "action_count": len(events),
        "journal_head_sha256": prior_sha256,
        "protected_data_accessed": False,
        "llm_runtime_used": False,
        "arbitrary_code_executed": False,
    }
    plan["plan_sha256"] = canonical_sha256(plan)
    return plan


def validate_execution_plan(value: Mapping[str, Any]) -> dict[str, Any]:
    """Replay the action hash chain and validate the plan self-hash."""

    plan = dict(value)
    if plan.get("schema_version") != "myis.armindex-execution-plan.v1":
        raise RuntimeContractError("unsupported execution plan schema")
    actions = plan.get("actions")
    if not isinstance(actions, list) or plan.get("action_count") != len(actions):
        raise RuntimeContractError("execution plan action count is invalid")
    prior = "0" * 64
    for sequence, action in enumerate(actions, start=1):
        if not isinstance(action, Mapping) or action.get("sequence") != sequence:
            raise RuntimeContractError("execution actions must be consecutive")
        if action.get("previous_action_sha256") != prior:
            raise RuntimeContractError("execution action hash chain is broken")
        unsigned = {key: item for key, item in action.items() if key != "action_sha256"}
        if action.get("action_sha256") != canonical_sha256(unsigned):
            raise RuntimeContractError("execution action self-hash is invalid")
        prior = str(action["action_sha256"])
    if plan.get("journal_head_sha256") != prior:
        raise RuntimeContractError("execution plan journal head is invalid")
    unsigned_plan = {key: item for key, item in plan.items() if key != "plan_sha256"}
    if plan.get("plan_sha256") != canonical_sha256(unsigned_plan):
        raise RuntimeContractError("execution plan self-hash is invalid")
    if (
        plan.get("protected_data_accessed") is not False
        or plan.get("llm_runtime_used") is not False
        or plan.get("arbitrary_code_executed") is not False
    ):
        raise RuntimeContractError("execution plan crosses a forbidden runtime boundary")
    return plan


def _active_arms(config: Mapping[str, Any], signals: Mapping[str, Any]) -> tuple[str, ...]:
    order = tuple(str(item) for item in config["invocation_order"])
    rules = config["routing"]
    if not rules or config["execution_mode"] == "parallel":
        return order
    active = {order[0]}
    for rule in rules:
        observed = signals[rule["feature"]]
        if _matches(observed, rule["operator"], rule["threshold"]):
            active.add(str(rule["activate_arm_id"]))
    return tuple(arm_id for arm_id in order if arm_id in active)


def _matches(observed: Any, operator: str, threshold: Any) -> bool:
    if operator == "eq":
        return observed == threshold
    try:
        return observed >= threshold if operator == "gte" else observed <= threshold
    except TypeError as error:
        raise RuntimeContractError("routing threshold type differs from its runtime feature") from error
