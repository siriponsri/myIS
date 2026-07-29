"""Typed, path-safe projection catalogs shared by Dashboard and MLflow."""

from __future__ import annotations

import hashlib
import json
import re
import stat
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


EVIDENCE_CATALOG_PATH = "00_governance/config/evidence_catalog.yaml"
MLFLOW_CATALOG_PATH = "03_experiments/config/mlflow/governance_documents.yaml"
LINEAR_PROJECTION_PATH = "00_governance/config/linear.yaml"
DASHBOARD_REGISTRY_PATH = "06_frontend/dashboard/content_registry.yaml"

EXPERIMENT_NAMES = (
    "myis-research-bootstrap",
    "myis-research-catalog",
    "myis-research-track-c",
    "myis-research-track-s",
    "myis-research-joint",
    "myis-research-publication",
)

GATE_ACTIONS = {
    "G0": (
        "approve_implementation",
        "approve_documentation_migration",
        "approve_cleanup",
        "anchor_pdf_receipt_chain",
    ),
    "G1": ("authorize_reproduction",),
    "G2": ("authorize_track_c_development",),
    "G3": ("freeze_track_c",),
    "G4": ("authorize_track_s",),
    "G5": ("freeze_track_s",),
    "G6": ("authorize_joint_confirmation",),
    "G7": ("authorize_transfer",),
    "G8": ("authorize_publication",),
}

GATE_GUIDANCE: dict[str, dict[str, Any]] = {
    "G0": {
        "name_th": "ตรวจฐานระบบและการย้ายโครงสร้าง",
        "name_en": "Integrity and migration",
        "purpose_th": "ยืนยันว่าเอกสาร โครงสร้าง โค้ดกำกับดูแล และ projection เริ่มจาก bytes ที่ตรวจสอบย้อนกลับได้",
        "decision_th": "อนุมัติงาน foundation ที่ระบุไว้ โดยยังไม่อนุญาตให้รัน baseline หรือการทดลอง",
        "still_locked_th": "Phase F1 และงานวิทยาศาสตร์ทั้งหมดต้องรอ G1 หรือ Gate ที่เกี่ยวข้อง",
        "required_evidence_th": (
            "แผนที่ความขัดแย้งและ protected-path comparison",
            "สภาพแวดล้อมและ dependency lock",
            "ผล validator/tests และแผนย้อนกลับ",
            "รายการเปลี่ยนแปลงและ projection readback",
        ),
    },
    "G1": {
        "name_th": "อนุญาตทำ baseline ซ้ำ",
        "name_en": "Reproduction",
        "purpose_th": "ตรวจว่าข้อมูล ตัวประเมิน สูตร baseline และงบ compute ถูกผูกกับ protocol เดียวกันก่อนรัน",
        "decision_th": "อนุญาตให้ทำซ้ำ B0, B1 และ B2 ตามสูตรที่ล็อกไว้",
        "still_locked_th": "ยังไม่เปิดการพัฒนา C0/C1 หรือการใช้ joint test",
        "required_evidence_th": (
            "commitment ของ corpus/query/qrels/family/evaluator",
            "field protocol และเป้าหมาย reproduction",
            "งบ compute และ stop conditions",
        ),
    },
    "G2": {
        "name_th": "เปิดการพัฒนา Track C",
        "name_en": "Shared split and Track C development",
        "purpose_th": "ล็อก shared split และขอบเขตที่ Track C แก้ได้ก่อน C0/C1 เห็น development labels",
        "decision_th": "เปิด C0, C1 search และ selection ตามงบและ editable surface ที่กำหนด",
        "still_locked_th": "ยังห้าม freeze C1 harness, เปิด Track S หรือใช้ joint test",
        "required_evidence_th": (
            "shared membership commitment และ C firewall",
            "power/OUT-positive audit และ C-MARGIN/C-SOEI",
            "qrels-blind view schema และ route/final budgets",
        ),
    },
    "G3": {
        "name_th": "ตรึง Track C และส่งต่อ harness",
        "name_en": "Track C freeze",
        "purpose_th": "ยืนยันว่า C0/C1 และ frozen pool เล่นซ้ำได้ก่อนส่ง C1 harness ให้ Track S",
        "decision_th": "ตรึง C0, C1 และ C1 harness เป็น input เดียวของงานถัดไป",
        "still_locked_th": "Track S ยังรอ provider/baseline preflight ที่ G4",
        "required_evidence_th": (
            "C0/C1 ablations และ selected policy",
            "failure table และ frozen-pool specification",
            "hash closure ของ code/config/model/environment/pool",
        ),
    },
    "G4": {
        "name_th": "เปิด Track S หลังตรวจ provider",
        "name_en": "Track S provider and baseline lock",
        "purpose_th": "ยืนยัน provider/model, A0/A1, S firewall, margin และ budget ก่อนใช้ paid optimization",
        "decision_th": "อนุญาตแขน A2, A2L และ A3 แบบ matched-budget",
        "still_locked_th": "ห้าม freeze finalists หรือใช้ joint test จนผ่าน G5",
        "required_evidence_th": (
            "G3 frozen-harness receipt และ A0/A1 preregistration",
            "CoreWeave model/provider preflight",
            "S firewall, S-MARGIN, budget และ retry plan",
        ),
    },
    "G5": {
        "name_th": "ตรึงผล Track S",
        "name_en": "Track S freeze",
        "purpose_th": "ตรวจความเท่าเทียมของงบและ lineage ก่อนเลือก finalists เพียงครั้งเดียว",
        "decision_th": "ส่ง nine seed-finalists และตรึงหนึ่ง artifact ต่อ A2/A2L/A3",
        "still_locked_th": "joint confirmation ยังรอ G6",
        "required_evidence_th": (
            "finalists ครบสาม seeds ต่อแขน",
            "matched model/provider/budget evidence",
            "optimization lineage และ frozen artifact hashes",
        ),
    },
    "G6": {
        "name_th": "อนุญาต joint confirmation ครั้งเดียว",
        "name_en": "Joint confirmation",
        "purpose_th": "ตรวจ hash closure ของทุกแขนก่อนส่งคำขอ hash-only ไปยัง Owner evaluator ภายนอก workspace",
        "decision_th": "อนุญาตคำสั่ง joint confirmation แบบ sealed เพียงครั้งเดียว",
        "still_locked_th": "Dashboard และ agent ยังเข้าถึง membership, qrels หรือ per-query outcomes ไม่ได้",
        "required_evidence_th": (
            "frozen Git/config/prompt/skill/model/environment/pool",
            "aggregate schemas ของ Track C และ S",
            "external evaluator receipt และ one-shot request",
        ),
    },
    "G7": {
        "name_th": "อนุญาต external transfer",
        "name_en": "External transfer",
        "purpose_th": "แยกการทดสอบ transfer บน PatenTEB ออกจาก joint test และ publication",
        "decision_th": "อนุญาต C1 transfer ตาม dataset/license/budget ที่ระบุ โดยห้าม retune",
        "still_locked_th": "ผล transfer ไม่เปิด Gate อื่นและไม่เปลี่ยน frozen artifacts",
        "required_evidence_th": (
            "field compatibility และ license/privacy decision",
            "no-retuning protocol",
            "run-specific budget และ exact targets",
        ),
    },
    "G8": {
        "name_th": "อนุมัติชุดเอกสารตีพิมพ์",
        "name_en": "Publication",
        "purpose_th": "ตรวจว่าข้ออ้าง ผลรวม ข้อจำกัด citations และ review chain ตรงกับหลักฐานก่อนเผยแพร่",
        "decision_th": "อนุมัติ build/submit ชุด Track C หรือ Track S ที่ระบุ",
        "still_locked_th": "การอนุมัติ Track หนึ่งไม่ครอบคลุมอีก Track และไม่เปลี่ยนสถานะหลักฐาน",
        "required_evidence_th": (
            "confirmation หรือ descriptive aggregates ที่ติดป้ายถูกต้อง",
            "claim-evidence/citation audit และ all repeats",
            "limitations, artifact inventory และ independent review",
        ),
    },
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class EvidencePackage(StrictModel):
    evidence_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]+$")
    title_en: str = Field(min_length=3, max_length=160)
    title_th: str = Field(min_length=3, max_length=160)
    summary_en: str = Field(min_length=3, max_length=500)
    summary_th: str = Field(min_length=3, max_length=500)
    path: str
    sha256: str
    gate_ids: tuple[str, ...]
    phase_ids: tuple[str, ...]
    task_ids: tuple[str, ...]
    evidence_role: Literal["fixture", "development", "descriptive", "confirmation"]

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        return _sha256(value)

    @field_validator("gate_ids", "phase_ids", "task_ids")
    @classmethod
    def validate_sorted_unique(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if values != tuple(sorted(set(values))):
            raise ValueError("catalog IDs must be sorted and unique")
        return values


class EvidenceCatalog(StrictModel):
    schema_version: Literal["myis.evidence-catalog.v1"]
    packages: tuple[EvidencePackage, ...]

    @model_validator(mode="after")
    def unique_packages(self) -> "EvidenceCatalog":
        identifiers = tuple(item.evidence_id for item in self.packages)
        paths = tuple(item.path for item in self.packages)
        hashes = tuple(item.sha256 for item in self.packages)
        if len(identifiers) != len(set(identifiers)) or len(paths) != len(set(paths)):
            raise ValueError("evidence catalog IDs and paths must be unique")
        if len(hashes) != len(set(hashes)):
            raise ValueError("evidence catalog hashes must be unique")
        return self


class ProjectionBinding(StrictModel):
    canonical_plan: Literal["PLAN.md"]
    plan_sha256: str
    dashboard_registry: Literal["06_frontend/dashboard/content_registry.yaml"]
    linear_projection: Literal["00_governance/config/linear.yaml"]
    experiments: tuple[str, ...]
    tag_schema_version: Literal["myis.projection-binding.v1"]

    @field_validator("plan_sha256")
    @classmethod
    def validate_plan_hash(cls, value: str) -> str:
        return _sha256(value)


class GovernanceDocument(StrictModel):
    document_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]+$")
    title_en: str = Field(min_length=3, max_length=160)
    title_th: str = Field(min_length=3, max_length=160)
    summary_en: str = Field(min_length=3, max_length=500)
    summary_th: str = Field(min_length=3, max_length=500)
    path: str
    kind: Literal["docs", "rules", "tools"]
    dashboard_content_id: str | None = None
    phase_ids: tuple[str, ...]
    task_ids: tuple[str, ...]
    gate_ids: tuple[str, ...]

    @field_validator("phase_ids", "task_ids", "gate_ids")
    @classmethod
    def sorted_unique_ids(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if values != tuple(sorted(set(values))):
            raise ValueError("document projection IDs must be sorted and unique")
        return values


class GovernanceDocumentCatalog(StrictModel):
    schema_version: Literal["myis.mlflow-governance-catalog.v1"]
    projection: ProjectionBinding
    documents: tuple[GovernanceDocument, ...]

    @model_validator(mode="after")
    def unique_documents(self) -> "GovernanceDocumentCatalog":
        identifiers = tuple(item.document_id for item in self.documents)
        paths = tuple(item.path for item in self.documents)
        if len(identifiers) != len(set(identifiers)) or len(paths) != len(set(paths)):
            raise ValueError("governance document IDs and paths must be unique")
        return self


def load_linear_projection(repository_root: Path, plan: Any) -> dict[str, Any]:
    source = _resolve_regular_file(repository_root, LINEAR_PROJECTION_PATH)
    payload = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != "myis.linear-projection.v1":
        raise ValueError("Linear projection schema is invalid")
    linear = payload.get("linear")
    if not isinstance(linear, dict):
        raise ValueError("Linear projection body is invalid")
    binding = linear.get("plan_binding")
    if not isinstance(binding, dict) or binding.get("canonical_plan") != "PLAN.md" or binding.get("plan_sha256") != plan.sha256:
        raise ValueError("Linear projection PLAN binding is stale")
    rows = linear.get("tasks")
    if not isinstance(rows, list):
        raise ValueError("Linear task projection is missing")
    expected = [task.task_id for phase in plan.phases for task in phase.tasks]
    task_map: dict[str, dict[str, str]] = {}
    for item in rows:
        if not isinstance(item, dict) or set(item) != {"task_id", "phase", "external_id", "status"}:
            raise ValueError("Linear task projection row is invalid")
        task_id = item["task_id"]
        if not all(isinstance(item[key], str) for key in item):
            raise ValueError("Linear task projection values must be strings")
        task_map[task_id] = {
            "phase_id": item["phase"],
            "issue_id": item["external_id"],
            "status": item["status"],
        }
    if list(task_map) != expected:
        raise ValueError("Linear task order does not match PLAN")
    project = linear.get("project")
    if not isinstance(project, dict):
        raise ValueError("Linear project projection is missing")
    return {
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "project": {
            "external_id": str(project.get("external_id", "")),
            "name": str(project.get("name", "")),
            "status": str(project.get("status", "")),
        },
        "tasks": task_map,
    }


def load_evidence_catalog(repository_root: Path, plan: Any) -> dict[str, Any]:
    source = _resolve_regular_file(repository_root, EVIDENCE_CATALOG_PATH)
    catalog = EvidenceCatalog.model_validate(yaml.safe_load(source.read_text(encoding="utf-8")))
    known_phases = {phase.phase_id for phase in plan.phases}
    known_tasks = {task.task_id for phase in plan.phases for task in phase.tasks}
    packages = []
    for item in catalog.packages:
        if not set(item.gate_ids) <= set(GATE_GUIDANCE):
            raise ValueError(f"evidence package {item.evidence_id} names an unknown Gate")
        if not set(item.phase_ids) <= known_phases or not set(item.task_ids) <= known_tasks:
            raise ValueError(f"evidence package {item.evidence_id} names an unknown PLAN scope")
        path = _resolve_regular_file(repository_root, item.path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item.sha256:
            raise ValueError(f"evidence package hash drifted: {item.evidence_id}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("schema_version"), str):
            raise ValueError(f"evidence package is not a typed JSON manifest: {item.evidence_id}")
        packages.append(
            {
                "evidence_id": item.evidence_id,
                "title_en": item.title_en,
                "title_th": item.title_th,
                "summary_en": item.summary_en,
                "summary_th": item.summary_th,
                "sha256": item.sha256,
                "gate_ids": list(item.gate_ids),
                "phase_ids": list(item.phase_ids),
                "task_ids": list(item.task_ids),
                "evidence_role": item.evidence_role,
                "schema_version": payload["schema_version"],
                "source_git_commit": payload.get("source_git_commit"),
                "check_count": len(payload.get("checks", [])) if isinstance(payload.get("checks"), list) else None,
            }
        )
    return {
        "schema_version": catalog.schema_version,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "packages": packages,
    }


def load_governance_document_catalog(repository_root: Path, plan: Any) -> dict[str, Any]:
    source = _resolve_regular_file(repository_root, MLFLOW_CATALOG_PATH)
    catalog = GovernanceDocumentCatalog.model_validate(yaml.safe_load(source.read_text(encoding="utf-8")))
    if catalog.projection.plan_sha256 != plan.sha256:
        raise ValueError("MLflow governance catalog PLAN binding is stale")
    if catalog.projection.experiments != EXPERIMENT_NAMES:
        raise ValueError("MLflow governance catalog experiment list drifted")
    linear = load_linear_projection(repository_root, plan)
    dashboard = yaml.safe_load(
        _resolve_regular_file(repository_root, DASHBOARD_REGISTRY_PATH).read_text(encoding="utf-8")
    )
    dashboard_documents = {
        item["content_id"]: item["path"]
        for item in dashboard.get("documents", [])
        if isinstance(item, dict) and isinstance(item.get("content_id"), str) and isinstance(item.get("path"), str)
    }
    known_phases = {phase.phase_id for phase in plan.phases}
    task_to_phase = {task.task_id: phase.phase_id for phase in plan.phases for task in phase.tasks}
    output = []
    for item in catalog.documents:
        if not set(item.phase_ids) <= known_phases or not set(item.task_ids) <= set(task_to_phase):
            raise ValueError(f"governance document {item.document_id} names an unknown PLAN scope")
        if any(task_to_phase[task_id] not in item.phase_ids for task_id in item.task_ids):
            raise ValueError(f"governance document {item.document_id} has a task outside its Phase scope")
        if not set(item.gate_ids) <= set(GATE_GUIDANCE):
            raise ValueError(f"governance document {item.document_id} names an unknown Gate")
        if item.dashboard_content_id is not None and dashboard_documents.get(item.dashboard_content_id) != item.path:
            raise ValueError(f"governance document {item.document_id} does not match the Dashboard registry")
        path = _resolve_regular_file(repository_root, item.path)
        output.append(
            {
                **item.model_dump(mode="json"),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "linear_issue_ids": [linear["tasks"][task_id]["issue_id"] for task_id in item.task_ids],
                "resolved_path": path,
            }
        )
    return {
        "schema_version": catalog.schema_version,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "projection": catalog.projection.model_dump(mode="json"),
        "documents": output,
    }


def public_governance_catalog(repository_root: Path, plan: Any) -> dict[str, Any]:
    evidence = load_evidence_catalog(repository_root, plan)
    documents = load_governance_document_catalog(repository_root, plan)
    task_lookup = {task.task_id: task for phase in plan.phases for task in phase.tasks}
    gates = []
    for gate_id, guidance in GATE_GUIDANCE.items():
        tasks = [
            task
            for phase in plan.phases
            for task in phase.tasks
            if gate_id in re.findall(r"\bG[0-8]\b", task.fields["Owner Gate"])
        ]
        phase_ids = list(dict.fromkeys(task.phase_id for task in tasks))
        gates.append(
            {
                "gate_id": gate_id,
                **guidance,
                "phase_ids": phase_ids,
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "phase_id": task.phase_id,
                        "title": task.title,
                    }
                    for task in tasks
                ],
                "evidence_package_ids": [
                    item["evidence_id"] for item in evidence["packages"] if gate_id in item["gate_ids"]
                ],
                "actions": list(GATE_ACTIONS[gate_id]),
            }
        )
    return {
        "schema_version": "myis.owner-governance-catalog.v1",
        "plan_sha256": plan.sha256,
        "gates": gates,
        "evidence_packages": evidence["packages"],
        "projection_alignment": {
            "plan": {"phase_count": len(plan.phases), "task_count": len(task_lookup)},
            "dashboard": {"registry": DASHBOARD_REGISTRY_PATH},
            "linear": {"projection": LINEAR_PROJECTION_PATH, "task_count": len(task_lookup)},
            "mlflow": {
                "catalog_schema": documents["schema_version"],
                "document_count": len(documents["documents"]),
                "experiments": list(documents["projection"]["experiments"]),
            },
        },
    }


def validate_evidence_selection(
    repository_root: Path,
    plan: Any,
    *,
    gate_id: str,
    status: str,
    hashes: tuple[str, ...],
) -> None:
    catalog = load_evidence_catalog(repository_root, plan)
    by_hash = {item["sha256"]: item for item in catalog["packages"]}
    if status == "approved" and not hashes:
        raise ValueError("approval requires at least one verified evidence package")
    unknown = [value for value in hashes if value not in by_hash]
    if unknown:
        raise ValueError("decision references evidence that is not in the verified catalog")
    incompatible = [value for value in hashes if gate_id not in by_hash[value]["gate_ids"]]
    if incompatible:
        raise ValueError(f"selected evidence is not approved for {gate_id}")


def _resolve_regular_file(repository_root: Path, relative_path: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise PermissionError("projection source path is invalid")
    lexical_root = repository_root.absolute()
    if _is_link_or_reparse(lexical_root):
        raise PermissionError("projection repository root cannot be a link or reparse point")
    target = lexical_root
    for part in relative.parts:
        target = target / part
        if _is_link_or_reparse(target):
            raise PermissionError("projection source path contains a link or reparse point")
    resolved_root = lexical_root.resolve(strict=True)
    resolved_target = target.resolve(strict=True)
    try:
        resolved_target.relative_to(resolved_root)
    except ValueError as error:
        raise PermissionError("projection source escapes the repository") from error
    if not resolved_target.is_file():
        raise PermissionError("projection source must be a regular file")
    return resolved_target


def _is_link_or_reparse(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return path.is_symlink() or bool(attributes & reparse_flag)


def _sha256(value: str) -> str:
    normalized = value.lower()
    if not re.fullmatch(r"[0-9a-f]{64}", normalized):
        raise ValueError("value must be SHA-256")
    return normalized
