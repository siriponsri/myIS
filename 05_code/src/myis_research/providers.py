"""Typed provider identity, fallback, and matched-optimizer contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .harness.models import EndpointClass, ProviderExecution, is_sha256


SOL_MODEL_ID = "gpt-5.6-sol"
LUNA_MODEL_ID = "gpt-5.6-luna"


class LunaUse(StrEnum):
    SUPPORT_TASK = "support_task"
    COST_ABLATION = "cost_ablation"


@dataclass(frozen=True)
class ModelCalibrationProtocol:
    implementation: ProviderExecution
    initial_optimizer: ProviderExecution
    selected_optimizer: ProviderExecution
    qrels_blind_calibration_failed: bool = False
    calibration_report_sha256: str | None = None
    escalation_owner_decision_id: str | None = None

    def validate(self) -> None:
        self.implementation.validate(measured=True)
        self.initial_optimizer.validate(measured=True)
        self.selected_optimizer.validate(measured=True)
        _require_model(self.implementation, SOL_MODEL_ID, "high", role="implementation")
        _require_model(self.initial_optimizer, SOL_MODEL_ID, "medium", role="initial optimizer")
        if self.selected_optimizer.effort == "medium":
            _require_model(self.selected_optimizer, SOL_MODEL_ID, "medium", role="selected optimizer")
            if self.escalation_owner_decision_id is not None:
                raise ValueError("medium optimizer cannot carry a High-escalation decision")
            return
        _require_model(self.selected_optimizer, SOL_MODEL_ID, "high", role="selected optimizer")
        if not self.qrels_blind_calibration_failed:
            raise ValueError("Sol High optimizer requires failed qrels-blind calibration")
        if not is_sha256(self.calibration_report_sha256):
            raise ValueError("Sol High escalation requires a calibration-report SHA-256")
        if not (self.escalation_owner_decision_id or "").strip():
            raise ValueError("Sol High escalation requires an Owner Gate decision")


def validate_luna_use(provider: ProviderExecution, *, use: LunaUse, main_a2_a3: bool) -> None:
    provider.validate(measured=main_a2_a3)
    if provider.requested_model != LUNA_MODEL_ID or provider.resolved_model != LUNA_MODEL_ID:
        raise ValueError("Luna-use contract requires the Luna model identity")
    if use not in {LunaUse.SUPPORT_TASK, LunaUse.COST_ABLATION}:
        raise ValueError("Luna is limited to support tasks or separate cost ablations")
    if main_a2_a3:
        raise ValueError("Luna cannot be mixed into the main A2/A3 comparison")


def _require_model(provider: ProviderExecution, model_id: str, effort: str, *, role: str) -> None:
    if provider.endpoint_class != EndpointClass.OFFICIAL:
        raise ValueError(f"{role} requires the official provider endpoint")
    if provider.requested_model != model_id or provider.resolved_model != model_id or provider.effort != effort:
        raise ValueError(f"{role} must use {model_id} at {effort} effort")


@dataclass(frozen=True)
class OptimizerProtocol:
    provider: ProviderExecution
    budget_sha256: str
    initial_state_sha256: str
    evaluator_sha256: str
    stopping_rule_sha256: str

    def validate(self, *, stage: str) -> None:
        measured = stage not in {"fixture", "calibration"}
        self.provider.validate(measured=measured)
        if self.provider.endpoint_class == EndpointClass.THIRD_PARTY and stage not in {"development", "calibration"}:
            raise ValueError("third-party providers are development-only by default")
        for name, value in {
            "budget_sha256": self.budget_sha256,
            "initial_state_sha256": self.initial_state_sha256,
            "evaluator_sha256": self.evaluator_sha256,
            "stopping_rule_sha256": self.stopping_rule_sha256,
        }.items():
            if not is_sha256(value):
                raise ValueError(f"{name} must be SHA-256")


def assert_no_silent_fallback(record: ProviderExecution, *, measured: bool = True) -> None:
    record.validate(measured=measured)


def assert_matched_optimizer_protocols(a2: OptimizerProtocol, a3: OptimizerProtocol, *, stage: str) -> None:
    a2.validate(stage=stage)
    a3.validate(stage=stage)
    fields = (
        "requested_model",
        "resolved_model",
        "provider",
        "effort",
        "endpoint_class",
        "fallback_allowed",
        "fallback_used",
        "temperature",
        "seed",
    )
    mismatches = {
        field: (getattr(a2.provider, field), getattr(a3.provider, field))
        for field in fields
        if getattr(a2.provider, field) != getattr(a3.provider, field)
    }
    for field in ("budget_sha256", "initial_state_sha256", "evaluator_sha256", "stopping_rule_sha256"):
        if getattr(a2, field) != getattr(a3, field):
            mismatches[field] = (getattr(a2, field), getattr(a3, field))
    if mismatches:
        raise ValueError(f"A2/A3 optimizer protocols are not matched: {mismatches}")
