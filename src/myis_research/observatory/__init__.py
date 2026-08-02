"""Repository-safe research evidence capture and validation."""

from .core import (
    CaptureSession,
    EvidenceRegistry,
    ObservatoryError,
    build_artifact_record,
    build_decision_record,
    build_failure_record,
    build_metric_record,
    build_prompt_record,
    build_result_record,
    build_run_record,
    build_standard_record,
    canonical_json,
    canonical_sha256,
    validate_registry,
)
from .graph import EvidenceGraph, build_evidence_graph, validate_evidence_graph
from .projection import load_observatory_projection, load_observatory_registry

__all__ = [
    "CaptureSession",
    "EvidenceGraph",
    "EvidenceRegistry",
    "ObservatoryError",
    "build_artifact_record",
    "build_decision_record",
    "build_evidence_graph",
    "build_failure_record",
    "build_metric_record",
    "build_prompt_record",
    "build_result_record",
    "build_run_record",
    "build_standard_record",
    "canonical_json",
    "canonical_sha256",
    "load_observatory_projection",
    "load_observatory_registry",
    "validate_evidence_graph",
    "validate_registry",
]
