"""Strict browser boundary contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DecisionPreviewRequest(StrictModel):
    gate_id: str = Field(min_length=2, max_length=80, pattern=r"^[A-Za-z0-9._-]+$")
    status: Literal["approved", "rejected", "deferred", "superseded"]
    rationale: str = Field(min_length=3, max_length=4000)
    evidence_manifest_hashes: tuple[str, ...] = ()
    scope_hash: str
    supersedes_decision_id: str | None = Field(
        default=None, min_length=2, max_length=160, pattern=r"^[A-Za-z0-9_-]+$"
    )
    display_label: str | None = Field(default=None, max_length=120)

    @field_validator("evidence_manifest_hashes")
    @classmethod
    def validate_hashes(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(sorted(set(values)))
        if len(normalized) != len(values):
            raise ValueError("evidence hashes must be sorted and unique")
        for value in values:
            _sha256(value)
        return values

    @field_validator("scope_hash")
    @classmethod
    def validate_scope_hash(cls, value: str) -> str:
        _sha256(value)
        return value

    @model_validator(mode="after")
    def validate_supersession(self) -> "DecisionPreviewRequest":
        if self.status == "superseded" and not self.supersedes_decision_id:
            raise ValueError("superseded decisions must reference the original decision")
        return self


class DecisionConfirmRequest(StrictModel):
    preview_token: str = Field(min_length=32, max_length=256)
    confirm: Literal[True]


class PdfAccessRequest(StrictModel):
    artifact_id: str = Field(min_length=2, max_length=128, pattern=r"^[A-Za-z0-9._-]+$")
    purpose: str = Field(min_length=3, max_length=500)


def _sha256(value: str) -> None:
    if len(value) != 64:
        raise ValueError("value must be SHA-256")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError("value must be SHA-256") from error
