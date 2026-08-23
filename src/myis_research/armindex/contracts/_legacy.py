"""Compatibility validators for the initial ArmIndex migration contracts."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml
from jsonschema import Draft202012Validator

from ..constants import (
    A0_8_NEXT_AUTHORIZED_ACTION,
    A1_1_NEXT_AUTHORIZED_ACTION,
    A1_2_NEXT_AUTHORIZED_ACTION,
)


CAMPAIGN_ID = "armindex-multiretriever-v2"
ARM_IDS = ("ARM-01", "ARM-02", "ARM-03", "ARM-04", "ARM-05")
ACTIVE_PHASE_IDS = (
    "A0_MIGRATION_FOUNDATION",
    "A1_BASELINES_AND_MULTI_ARM_SCREENING",
    "A2_PER_ARM_AUTOINDEX",
    "A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT",
    "A4_PRODUCTION_TRANSFER_AND_SELECTION",
    "A5_FINAL_CONFIRMATION",
    "A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY",
    "A7_SEVEN_LAYER_RETRIEVAL_DIAGNOSIS",
    "A8_JOURNAL_SYNTHESIS_AND_PUBLICATION",
)
OWNER_GATES = ("D2_OPEN_FINAL", "D3_SUBMIT_RELEASE")
PRODUCTION_PROFILES = ("FAST", "BALANCED", "DEEP")
TERMINAL_STATES = frozenset(
    {
        "FREEZE_ARM_PROGRAM",
        "STOP_WITH_EVIDENCE_FLAT_REPRESENTATION_SURFACE",
        "BLOCKED_INVALID_ARM_OR_PROGRAM",
        "FREEZE_HARNESSOPT_CHAMPION",
        "FREEZE_FIXED_UNION",
        "FREEZE_BEST_SINGLE_ARM",
        "STOP_WITH_EVIDENCE_HARNESS_NO_GAIN",
        "BLOCKED_HARNESS_INTEGRITY",
        "FREEZE_THREE_PROFILES",
        "FREEZE_REDUCED_PROFILE_SET",
        "BLOCKED_PRODUCTION_VALIDATION",
    }
)
FORBIDDEN_HARNESS_FEATURES = frozenset(
    {
        "qrels",
        "in_out_label",
        "ipc_cpc_out_shortcut",
        "per_query_correctness_history",
        "selection_feedback",
        "final_feedback",
        "query_rewriting",
        "llm_runtime_reasoning",
        "model_mutation",
        "representation_mutation",
        "arbitrary_python",
    }
)
_PERSONAL_PATH = re.compile(r"(?:[A-Za-z]:\\Users\\|/Users/|/home/)", re.IGNORECASE)


class ArmIndexContractError(ValueError):
    """Raised when an active ArmIndex object violates a frozen contract."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _schema(root: Path, name: str) -> Mapping[str, Any]:
    path = root.resolve() / "schemas" / "armindex" / name
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ArmIndexContractError(f"cannot load ArmIndex schema: {name}") from error
    if not isinstance(value, Mapping):
        raise ArmIndexContractError(f"ArmIndex schema is not an object: {name}")
    return value


def _validate_schema(root: Path, name: str, value: Mapping[str, Any]) -> None:
    errors = sorted(Draft202012Validator(_schema(root, name)).iter_errors(dict(value)), key=lambda item: list(item.path))
    if errors:
        location = ".".join(str(item) for item in errors[0].path) or "<root>"
        raise ArmIndexContractError(f"{name} validation failed at {location}: {errors[0].message}")
    serialized = json.dumps(value, ensure_ascii=True)
    if _PERSONAL_PATH.search(serialized):
        raise ArmIndexContractError("ArmIndex object contains a personal absolute path")


def validate_model_adapter_lock(root: Path, value: Mapping[str, Any]) -> None:
    _validate_schema(root, "model-adapter-lock.v1.json", value)
    if value["network_required"] is not False:
        raise ArmIndexContractError("measured adapter locks must resolve without network access")
    payload = {key: item for key, item in value.items() if key != "lock_sha256"}
    if canonical_sha256(payload) != value["lock_sha256"]:
        raise ArmIndexContractError("model adapter lock hash mismatch")
    if value["arm_id"] == "ARM-03" and value["commercial_status"] != "research_non_commercial":
        raise ArmIndexContractError("PatEmbed must remain research/non-commercial")


def validate_representation_program(root: Path, value: Mapping[str, Any]) -> None:
    _validate_schema(root, "representation-program.v1.json", value)
    if set(value["source_fields"]) != set(value["field_order"]):
        raise ArmIndexContractError("field_order must contain each source field exactly once")
    payload = {key: item for key, item in value.items() if key != "program_sha256"}
    if canonical_sha256(payload) != value["program_sha256"]:
        raise ArmIndexContractError("representation program hash mismatch")


def _normalize(text: str, mode: str) -> str:
    result = " ".join(unicodedata.normalize("NFKC", text).split())
    return result.lower() if mode.endswith("_lower") else result


def compile_representation(program: Mapping[str, Any], documents: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Compile byte-stable family units independent of document input order."""

    units: list[dict[str, Any]] = []
    for document in sorted(documents, key=lambda item: str(item.get("family_id", ""))):
        family_id = str(document.get("family_id", ""))
        if not family_id:
            raise ArmIndexContractError("synthetic document is missing family_id")
        fields = []
        for field in program["field_order"]:
            if field not in document:
                raise ArmIndexContractError(f"synthetic document is missing field: {field}")
            label = str(program.get("field_labels", {}).get(field, field))
            content = _normalize(str(document[field]), str(program["normalization"]))
            fields.append(f"{label}: {content}" if label else content)
        text = "\n".join(fields)
        content_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
        units.append(
            {
                "family_id": family_id,
                "unit_id": f"{family_id}:{content_sha256[:16]}",
                "text": text,
                "content_sha256": content_sha256,
                "source_fields": list(program["field_order"]),
            }
        )
    if program["duplicate_policy"] == "content_hash_first":
        deduplicated: dict[str, dict[str, Any]] = {}
        for unit in units:
            deduplicated.setdefault(unit["content_sha256"], unit)
        units = sorted(deduplicated.values(), key=lambda item: (item["family_id"], item["unit_id"]))
    return units


def validate_harness(root: Path, value: Mapping[str, Any]) -> None:
    _validate_schema(root, "harness.v1.json", value)
    arm_ids = list(value["arm_ids"])
    if list(value["invocation_order"]) != arm_ids:
        raise ArmIndexContractError("invocation_order must be a deterministic permutation of arm_ids")
    if set(value["depth_by_arm"]) != set(arm_ids):
        raise ArmIndexContractError("depth_by_arm must bind every selected arm")
    forbidden = FORBIDDEN_HARNESS_FEATURES.intersection(value.get("runtime_features", []))
    if forbidden:
        raise ArmIndexContractError(f"forbidden harness features: {sorted(forbidden)}")
    if value["profile"] == "FAST" and (len(arm_ids) > 2 or "ARM-01" not in arm_ids):
        raise ArmIndexContractError("FAST requires BM25 and at most two arms")
    payload = {key: item for key, item in value.items() if key != "harness_sha256"}
    if canonical_sha256(payload) != value["harness_sha256"]:
        raise ArmIndexContractError("harness hash mismatch")


def validate_research_flow_terminal(root: Path, value: Mapping[str, Any]) -> None:
    _validate_schema(root, "research-flow-terminal.v1.json", value)
    if value["terminal_state"] not in TERMINAL_STATES:
        raise ArmIndexContractError("unknown Research Flow terminal state")
    payload = {key: item for key, item in value.items() if key != "receipt_sha256"}
    if canonical_sha256(payload) != value["receipt_sha256"]:
        raise ArmIndexContractError("Research Flow terminal receipt hash mismatch")


def validate_mlflow_migration_receipt(root: Path, value: Mapping[str, Any]) -> None:
    _validate_schema(root, "mlflow-migration-receipt.v1.json", value)
    payload = {key: item for key, item in value.items() if key != "receipt_sha256"}
    if canonical_sha256(payload) != value["receipt_sha256"]:
        raise ArmIndexContractError("MLflow migration receipt hash mismatch")


def validate_campaign(root: Path, value: Mapping[str, Any], *, migration: bool = True) -> None:
    campaign = value.get("campaign")
    if not isinstance(campaign, Mapping) or campaign.get("id") != CAMPAIGN_ID:
        raise ArmIndexContractError("active ArmIndex campaign identity is missing")
    arms = value.get("arms")
    if not isinstance(arms, list) or tuple(item.get("id") for item in arms if isinstance(item, Mapping)) != ARM_IDS:
        raise ArmIndexContractError("active ArmIndex campaign must define exactly five ordered arms")
    phases = value.get("phases")
    if not isinstance(phases, list) or tuple(item.get("id") for item in phases if isinstance(item, Mapping)) != ACTIVE_PHASE_IDS:
        raise ArmIndexContractError("active ArmIndex phase registry must contain A0-A8 only")
    gates = value.get("gates")
    if not isinstance(gates, Mapping) or tuple(gates.get("owner", [])) != OWNER_GATES:
        raise ArmIndexContractError("Owner gates must be exactly D2 and D3")
    if migration:
        forbidden_nonzero = {
            "migration_measured_runs": campaign.get("migration_measured_runs", 0),
            "selection_accesses": campaign.get("selection_accesses", 0),
            "final_accesses": campaign.get("final_accesses", 0),
        }
        if any(value != 0 for value in forbidden_nonzero.values()):
            raise ArmIndexContractError(f"migration counters must remain zero: {forbidden_nonzero}")
        protocol = value.get("protocol", {})
        if not isinstance(protocol, Mapping) or protocol.get("measured_execution_allowed") is not False:
            raise ArmIndexContractError("measured execution must remain closed during migration")


def load_campaign(root: Path) -> dict[str, Any]:
    path = root.resolve() / "control" / "campaigns" / f"{CAMPAIGN_ID}.yaml"
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise ArmIndexContractError("cannot load active ArmIndex campaign") from error
    if not isinstance(value, dict):
        raise ArmIndexContractError("active ArmIndex campaign is not an object")
    # The active ArmIndex campaign is post-migration and has measured
    # predecessor counters.  Keep ``migration=True`` available for the
    # historical scaffold validator, but do not apply that zero-counter gate
    # to the active campaign loader.
    validate_campaign(root, value, migration=False)
    return value


def build_armindex_projection(root: Path) -> dict[str, Any]:
    config = load_campaign(root)
    campaign = config["campaign"]
    phases = [
        {
            "phase_id": item["id"],
            "purpose": item["purpose"],
            "status": item["status"],
            "tasks": [
                {"task_id": task["id"], "title": task["title"], "status": task["status"]}
                for task in item.get("tasks", [])
            ],
        }
        for item in config["phases"]
    ]
    current_phase = next(
        (item["id"] for item in config["phases"] if item.get("status") != "complete"),
        "A8_JOURNAL_SYNTHESIS_AND_PUBLICATION",
    )
    projection = {
        "schema_version": "myis.armindex-read-model.v1",
        "campaign_id": CAMPAIGN_ID,
        "status": campaign["status"],
        "current_phase": current_phase,
        "phases": phases,
        "arms": [
            {
                "arm_id": arm["id"],
                "model_id": arm["model_id"],
                "role": arm["role"],
                "license": arm["license"],
                "commercial_status": arm["commercial_status"],
                "adapter_status": "declared_pending_fixture_lock",
                "representation_status": "not_started",
            }
            for arm in config["arms"]
        ],
        "representation_programs": [],
        "transfer": {"status": "not_started", "matrix_entries": 0},
        "complementarity": {"status": "not_started", "evaluated_arm_sets": 0},
        "harnessopt": {"status": "not_started", "candidate_count": 0, "forbidden_mutations": list(sorted(FORBIDDEN_HARNESS_FEATURES))},
        "production_profiles": [{"profile_id": profile, "status": "contract_only"} for profile in PRODUCTION_PROFILES],
        "champions": {"research": None, "commercial": None},
        "counters": {"measured_runs": 0, "candidate_count": 0, "selection_accesses": 0, "final_accesses": 0},
        "gates": [{"gate_id": gate, "status": "waiting_owner"} for gate in OWNER_GATES],
        "budget": {"currency": "USD", "actual": 0.0, "hard_stop": 100.0, "migration_profile": "armindex-migration-v2"},
        "historical_campaigns": [{"campaign_id": "scope-autoindex-v1", "status": "historical_read_only", "p1_measured_evidence": "preserved_by_pointer", "p2_measured_runs": 0}],
        "next_command": (
            A1_2_NEXT_AUTHORIZED_ACTION
            if config["phases"][1].get("tasks", [{}])[0].get("status") == "complete"
            else A1_1_NEXT_AUTHORIZED_ACTION
            if config["phases"][0].get("status") == "complete"
            else A0_8_NEXT_AUTHORIZED_ACTION
        ),
    }
    _validate_schema(root, "read-model.v1.json", projection)
    return projection
