"""Canonical research-program identity, independent of package versioning."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Mapping

import yaml


PROGRAM_ID = "myis-research"
DISPLAY_NAME = "myIS Research"
PROTOCOL_VERSION = "1.0"
RESEARCH_VERSION = "0.1"
VERSION_CLASS = "protocol_major"
PROTOCOL_FAMILY_ID = "crossroute-frozen-c1-skillopt-v1"
PROJECT_CONFIG = Path("00_governance/config/project.yaml")

_PROGRAM_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_RESEARCH_VERSION_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$")
_FULL_GIT_COMMIT_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class IdentityValidationError(ValueError):
    """Raised when the canonical research identity is absent or inconsistent."""


@dataclass(frozen=True, slots=True)
class ResearchIdentity:
    """Stable identity attached to every myIS Research run and artifact."""

    program_id: str
    display_name: str
    protocol_version: str
    research_version: str
    version_class: str
    protocol_family_id: str
    legacy_aliases: tuple[str, ...]

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ResearchIdentity":
        required = {
            "program_id",
            "display_name",
            "protocol_version",
            "research_version",
            "version_class",
            "protocol_family_id",
            "legacy_aliases",
        }
        missing = required.difference(value)
        if missing:
            raise IdentityValidationError(
                f"project identity is missing fields: {', '.join(sorted(missing))}"
            )

        aliases = value["legacy_aliases"]
        if not isinstance(aliases, list) or not all(
            isinstance(alias, str) and alias.strip() for alias in aliases
        ):
            raise IdentityValidationError("legacy_aliases must be a list of non-empty strings")

        identity = cls(
            program_id=_string(value, "program_id"),
            display_name=_string(value, "display_name"),
            protocol_version=_string(value, "protocol_version"),
            research_version=_string(value, "research_version"),
            version_class=_string(value, "version_class"),
            protocol_family_id=_string(value, "protocol_family_id"),
            legacy_aliases=tuple(aliases),
        )
        identity.validate()
        return identity

    def validate(self) -> None:
        if not _PROGRAM_ID_RE.fullmatch(self.program_id):
            raise IdentityValidationError("program_id must be a lowercase kebab-case identifier")
        if not _RESEARCH_VERSION_RE.fullmatch(self.research_version):
            raise IdentityValidationError("research_version must use MAJOR.MINOR notation")
        if self.protocol_version != PROTOCOL_VERSION:
            raise IdentityValidationError(
                f"protocol_version must be {PROTOCOL_VERSION!r}"
            )
        if self.display_name != DISPLAY_NAME:
            raise IdentityValidationError(f"display_name must be {DISPLAY_NAME!r}")
        if len(set(self.legacy_aliases)) != len(self.legacy_aliases):
            raise IdentityValidationError("legacy_aliases must not contain duplicates")

    def as_manifest_fields(self) -> dict[str, str]:
        return {
            "program_id": self.program_id,
            "display_name": self.display_name,
            "protocol_version": self.protocol_version,
            "research_version": self.research_version,
            "version_class": self.version_class,
            "protocol_family_id": self.protocol_family_id,
        }


def load_research_identity(repository_root: Path) -> ResearchIdentity:
    """Load the research identity from the repository governance config."""

    config_path = repository_root.resolve() / PROJECT_CONFIG
    try:
        document = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise IdentityValidationError(f"cannot load project identity: {config_path}") from exc

    if not isinstance(document, dict) or not isinstance(document.get("project"), dict):
        raise IdentityValidationError("project.yaml must contain a project mapping")
    return ResearchIdentity.from_mapping(document["project"])


def assert_canonical_identity(identity: ResearchIdentity) -> None:
    """Fail if an active run is not bound to the Owner-approved identity."""

    expected = (
        PROGRAM_ID,
        DISPLAY_NAME,
        PROTOCOL_VERSION,
        RESEARCH_VERSION,
        VERSION_CLASS,
        PROTOCOL_FAMILY_ID,
    )
    actual = (
        identity.program_id,
        identity.display_name,
        identity.protocol_version,
        identity.research_version,
        identity.version_class,
        identity.protocol_family_id,
    )
    if actual != expected:
        raise IdentityValidationError("project identity does not match myIS Research protocol 1.0")


def validate_full_git_commit(value: str, *, field_name: str = "git_commit") -> str:
    """Return a canonical full Git object ID or reject abbreviated provenance."""

    if not isinstance(value, str) or not _FULL_GIT_COMMIT_RE.fullmatch(value):
        raise IdentityValidationError(
            f"{field_name} must be a full lowercase 40- or 64-hex Git commit identity"
        )
    return value


def _string(value: Mapping[str, Any], key: str) -> str:
    item = value[key]
    if not isinstance(item, str) or not item.strip():
        raise IdentityValidationError(f"{key} must be a non-empty string")
    return item
