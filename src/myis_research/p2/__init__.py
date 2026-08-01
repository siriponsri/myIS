"""P2 readiness contracts and the fail-closed internal freeze barrier."""

from .contracts import (
    P2BudgetProfile,
    P2ContractError,
    load_p2_request,
    load_profile,
    validate_p2_aggregate_metric,
    validate_p2_artifact,
    validate_p2_package_bundle,
    validate_p2_train_metric,
)
from .state import Candidate, P2RunStateMachine, P2StateError
from .fixture import (
    DEFAULT_RECEIPT_PATH,
    FIXTURE_ID,
    NEGATIVE_CHECK_IDS,
    P2FixtureError,
    fixture_what_if,
    run_fixture_pilot,
    validate_fixture_execution_manifest,
    validate_fixture_receipt,
)

__all__ = [
    "Candidate",
    "P2BudgetProfile",
    "P2ContractError",
    "P2RunStateMachine",
    "P2StateError",
    "P2FixtureError",
    "DEFAULT_RECEIPT_PATH",
    "FIXTURE_ID",
    "NEGATIVE_CHECK_IDS",
    "fixture_what_if",
    "load_p2_request",
    "load_profile",
    "run_fixture_pilot",
    "validate_p2_aggregate_metric",
    "validate_p2_artifact",
    "validate_fixture_execution_manifest",
    "validate_fixture_receipt",
    "validate_p2_package_bundle",
    "validate_p2_train_metric",
]
