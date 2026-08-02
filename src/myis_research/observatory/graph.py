"""Lineage graph construction and fail-closed validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .core import ObservatoryError, validate_registry


@dataclass(frozen=True)
class EvidenceGraph:
    nodes: tuple[dict[str, Any], ...]
    edges: tuple[dict[str, str], ...]

    def as_dict(self) -> dict[str, Any]:
        return {"schema_version": "myis.observatory-graph.v1", "nodes": list(self.nodes), "edges": list(self.edges)}


def build_evidence_graph(registry: Mapping[str, Any]) -> EvidenceGraph:
    validate_registry(registry)
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    records = registry.get("records", {})
    ids = {str(item.get("record_id")) for items in records.values() for item in items}
    kind_for: dict[str, str] = {}
    for kind, items in sorted(records.items()):
        for item in items:
            record_id = str(item["record_id"])
            kind_for[record_id] = kind.rstrip("s")
            nodes.append({"id": record_id, "kind": kind.rstrip("s"), "label": item.get("title") or item.get("name") or item.get("summary") or record_id, "evidence_class": item.get("evidence_class"), "scientific_authority": item.get("scientific_authority", False)})
            for field, target_kind in (("request_id", "request"), ("run_id", "run"), ("producing_run_id", "run"), ("candidate_id", "candidate"), ("result_id", "result"), ("parent_prompt_id", "prompt"), ("recovery_id", "recovery")):
                value = item.get(field)
                if isinstance(value, str) and value in ids:
                    edges.append({"source": value, "target": record_id, "relation": field.removesuffix("_id")})
            for field, relation in (("prompt_ids", "uses_prompt"), ("candidate_ids", "has_candidate"), ("artifact_ids", "has_artifact"), ("metric_ids", "supports_metric"), ("output_artifact_ids", "supports_output"), ("partial_artifact_ids", "partial_artifact"), ("parent_artifact_ids", "parent_artifact")):
                values = item.get(field, [])
                if isinstance(values, list):
                    for value in values:
                        if isinstance(value, str) and value in ids:
                            edges.append({"source": record_id, "target": value, "relation": relation})
    unique_edges = tuple(sorted({(edge["source"], edge["target"], edge["relation"]): edge for edge in edges}.values(), key=lambda edge: (edge["source"], edge["target"], edge["relation"])))
    return EvidenceGraph(nodes=tuple(sorted(nodes, key=lambda node: node["id"])), edges=unique_edges)


def validate_evidence_graph(graph: EvidenceGraph | Mapping[str, Any], registry: Mapping[str, Any] | None = None) -> None:
    if isinstance(graph, EvidenceGraph):
        payload = graph.as_dict()
        node_rows = graph.nodes
        edge_rows = graph.edges
    else:
        payload = dict(graph)
        node_rows = tuple(payload.get("nodes", []))
        edge_rows = tuple(payload.get("edges", []))
    if payload.get("schema_version") != "myis.observatory-graph.v1":
        raise ObservatoryError("graph schema_version is invalid")
    node_ids = [str(node.get("id")) for node in node_rows if isinstance(node, Mapping)]
    if len(node_ids) != len(set(node_ids)):
        raise ObservatoryError("graph has duplicate node IDs")
    node_set = set(node_ids)
    if len(edge_rows) != len({(edge.get("source"), edge.get("target"), edge.get("relation")) for edge in edge_rows}):
        raise ObservatoryError("graph has duplicate edges")
    for edge in edge_rows:
        if not isinstance(edge, Mapping) or edge.get("source") not in node_set or edge.get("target") not in node_set:
            raise ObservatoryError("graph contains an orphan edge")
    if registry is not None:
        validate_registry(registry)
        records = registry.get("records", {})
        promoted = [item for item in records.get("artifacts", []) if item.get("validation_status") == "validated"]
        artifact_ids = {str(item.get("record_id")) for item in records.get("artifacts", [])}
        connected = {str(edge.get("target")) for edge in edge_rows} | {str(edge.get("source")) for edge in edge_rows}
        for artifact in promoted:
            artifact_id = str(artifact.get("record_id"))
            if artifact_id not in connected:
                raise ObservatoryError(f"promoted artifact is orphaned: {artifact_id}")
            if artifact_id not in artifact_ids:
                raise ObservatoryError("artifact graph binding is invalid")
        for result in records.get("results", []):
            if not result.get("run_id") or str(result.get("run_id")) not in node_set:
                raise ObservatoryError(f"result has no parent run: {result.get('record_id')}")
