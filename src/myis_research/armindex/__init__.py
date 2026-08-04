"""ArmIndex active subsystem with historical myIS compatibility."""

from .contracts import (
    ACTIVE_PHASE_IDS,
    ARM_IDS,
    OWNER_GATES,
    PRODUCTION_PROFILES,
    TERMINAL_STATES,
    ArmIndexContractError,
    build_armindex_projection,
    compile_representation,
    validate_campaign,
    validate_harness,
    validate_mlflow_migration_receipt,
    validate_model_adapter_lock,
    validate_research_flow_terminal,
    validate_representation_program,
)

__all__ = [
    "ACTIVE_PHASE_IDS",
    "ARM_IDS",
    "OWNER_GATES",
    "PRODUCTION_PROFILES",
    "TERMINAL_STATES",
    "ArmIndexContractError",
    "build_armindex_projection",
    "compile_representation",
    "validate_campaign",
    "validate_harness",
    "validate_mlflow_migration_receipt",
    "validate_model_adapter_lock",
    "validate_research_flow_terminal",
    "validate_representation_program",
]
