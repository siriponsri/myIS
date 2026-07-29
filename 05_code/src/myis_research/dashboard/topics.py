"""Registry-driven Presentation topics for the Owner dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .readiness import load_f1_g1_readiness


TOPICS_PATH = "00_governance/config/dashboard_topics.yaml"


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
    audience_modes: tuple[Literal["beginner", "instructor"], ...]
    delivery_modes: tuple[Literal["learn", "present"], ...]
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
