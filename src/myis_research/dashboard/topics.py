"""Registry-driven Presentation topics for the Owner dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..asset_registry import load_registry
from .readiness import load_f1_g1_readiness


TOPICS_PATH = "control/campaigns/scope-autoindex-v1.yaml"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class TopicSection(StrictModel):
    section_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]+$")
    title_th: str
    title_en: str
    body_th: str
    body_en: str


class Topic(StrictModel):
    topic_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]+$")
    title: str
    subtitle_th: str
    subtitle_en: str
    audience_modes: tuple[Literal["owner", "advisor", "peer"], ...]
    delivery_modes: tuple[Literal["explore", "present"], ...]
    sections: tuple[TopicSection, ...]

    @model_validator(mode="after")
    def unique_sections(self) -> "Topic":
        values = [section.section_id for section in self.sections]
        if len(values) != len(set(values)):
            raise ValueError("Presentation section IDs must be unique")
        return self


class TopicRegistry(StrictModel):
    schema_version: Literal["myis.dashboard-topics.v1"]
    topics: tuple[Topic, ...]


def presentation_topics(repository_root: Path) -> dict[str, Any]:
    path = (repository_root / TOPICS_PATH).resolve(strict=True)
    try:
        path.relative_to(repository_root.resolve(strict=True))
    except ValueError as error:
        raise PermissionError("Dashboard topic registry escapes the repository") from error
    registry = TopicRegistry.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    readiness = load_f1_g1_readiness(repository_root)
    topics = []
    for topic in registry.topics:
        payload = topic.model_dump(mode="json")
        if topic.topic_id == "dapfam":
            payload["data"] = readiness
        topics.append(payload)
    return {"schema_version": registry.schema_version, "topics": topics}


def dataset_catalog(repository_root: Path) -> dict[str, Any]:
    """Expose registry-derived dataset metadata only; never dataset content or IDs."""

    topics = TopicRegistry.model_validate(
        yaml.safe_load((repository_root / TOPICS_PATH).read_text(encoding="utf-8"))
    )
    dapfam = next((topic for topic in topics.topics if topic.topic_id == "dapfam"), None)
    if dapfam is None:
        raise ValueError("DAPFAM dashboard topic is missing")
    registry = load_registry(repository_root)
    assets = {asset["asset_id"]: asset for asset in registry["assets"]}
    core = assets["APP-DAPFAM-CORE"]
    upstream = core["source"]["upstream_huggingface"]
    readiness = load_f1_g1_readiness(repository_root)
    local_assets = []
    for asset_id in ("APP-DAPFAM-CORE", "APP-DAPFAM-PAPER-VIEWS", "APP-SPARSE-FTS-INDEXES"):
        asset = assets[asset_id]
        byte_count = sum(
            int(item.get("bytes", 0)) for item in asset["source"]["paths"] if isinstance(item, dict)
        ) or None
        local_assets.append(
            {
                "asset_id": asset_id,
                "title": asset["title"],
                "kind": asset["kind"],
                "source_commit": asset["source"]["commit"],
                "disposition": asset["disposition"],
                "copy_mode": asset["copy_mode"],
                "frozen": asset["frozen"],
                "protected_data_level": asset["protected_data_level"],
                "byte_count": byte_count,
            }
        )
    return {
        "schema_version": "myis.dataset-catalog.v1",
        "datasets": [
            {
                "dataset_id": upstream["dataset_id"],
                "title": dapfam.title,
                "summary_th": dapfam.subtitle_th,
                "claim_boundary_th": "ใช้ประเมินความเกี่ยวข้องของการค้นคืนระดับ family เท่านั้น ไม่ใช่ข้อสรุปทางกฎหมาย",
                "classification": "protected_source_metadata_only",
                "availability": "owner_local_prepared" if readiness.get("prepared") else "metadata_only",
                "public_source": {
                    "url": upstream["dataset_url"],
                    "revision": upstream["revision"],
                    "license": upstream["license"],
                    "configs": upstream["configs"],
                    "metadata_only": upstream["metadata_only"],
                    "external_link_requires_user_action": True,
                },
                "inventory_counts": {"corpus": 45_336, "queries": 1_247, "relations": 49_869},
                "local_assets": local_assets,
                "lineage": [
                    {"from": "huggingface-public-card", "to": "APP-DAPFAM-CORE", "relation": "processed-and-frozen-in-app"},
                    {"from": "APP-DAPFAM-CORE", "to": "research-registry", "relation": "hash-and-pointer-only"},
                    {"from": "research-registry", "to": "F1/G1-preparation", "relation": "aggregate-commitments-only"},
                    {"from": "F1/G1-preparation", "to": "B0/B1/B2", "relation": "future-after-G1"},
                ],
                "split_status": readiness.get("gate_status", "pending"),
                "raw_access": False,
                "live_fetch": False,
                "scientific_results": "NOT_RUN",
            }
        ],
    }
