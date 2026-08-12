"""Build aggregate-safe A2 freeze validation and journal provenance artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator

from ..kernel.canonical import canonical_sha256
from ..projections.read_model import build_read_model
from ..report_cli import _armindex_paper_artifact_contents

REPLAY_RELATIVE_PATH = Path(
    "outputs/audits/armindex/"
    "a2-five-arm-candidate-freeze-replay-validation.v1.json"
)
REPLAY_SCHEMA_PATH = Path(
    "schemas/armindex/a2-candidate-freeze-replay-validation.v1.json"
)
ARTIFACT_INDEX_SCHEMA_PATH = Path("schemas/artifact-index.v2.json")
PROVENANCE_GRAPH_SCHEMA_PATH = Path("schemas/artifact-provenance-graph.v1.json")
CANONICAL_PROVENANCE_ROOT = Path(
    "outputs/publication/armindex/a2-candidate-freeze/provenance"
)


class A2CandidateFreezeArtifactError(RuntimeError):
    """Raised when a generated freeze artifact cannot be validated."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise A2CandidateFreezeArtifactError(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise A2CandidateFreezeArtifactError(f"JSON root must be an object: {path}")
    return value


def _validate(value: Mapping[str, Any], schema_path: Path) -> None:
    schema = _load_json(schema_path)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(dict(value)),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if errors:
        raise A2CandidateFreezeArtifactError(
            f"schema validation failed at {schema_path}: {errors[0].message}"
        )


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
        newline="",
    )


def build_replay_validation(
    repository_root: Path, model: Mapping[str, Any]
) -> dict[str, Any]:
    freeze = model.get("armindex", {}).get("a2_candidate_freeze", {})
    if not isinstance(freeze, Mapping) or freeze.get("validated") is not True:
        raise A2CandidateFreezeArtifactError("A2 candidate freeze is not validated")
    credit = freeze.get("official_credit", {})
    identity = freeze.get("official_identity", {})
    if not isinstance(credit, Mapping) or not isinstance(identity, Mapping):
        raise A2CandidateFreezeArtifactError("A2 identity or credit projection is missing")
    value = {
        "schema_version": "myis.armindex-a2-candidate-freeze-replay-validation.v1",
        "validation_id": "a2-five-arm-candidate-freeze-replay-v1",
        "phase_id": "A2_PER_ARM_AUTOINDEX",
        "task_id": "OFFICIAL_CODEX_BRIDGE_AND_CANDIDATE_FREEZE",
        "status": "PASS_A2_CANDIDATE_FREEZE_REPLAY",
        "evidence_class": "engineering_validation",
        "scientific_authority": False,
        "claim_boundary": str(freeze["claim_boundary"]),
        "generation_attempt_id": str(freeze["generation_attempt_id"]),
        "candidate_count": int(freeze["candidate_count"]),
        "matched_candidate_count": int(freeze["matched_candidate_count"]),
        "conditional_reserve_candidate_count": int(
            freeze["conditional_reserve_candidate_count"]
        ),
        "manifest_sha256": str(freeze["manifest_sha256"]),
        "freeze_receipt_sha256": str(freeze["freeze_receipt_sha256"]),
        "lock_sha256": str(freeze["lock_sha256"]),
        "model_name": str(identity["model_name"]),
        "plan_type": str(credit["plan_type"]),
        "remaining_percent": int(credit["remaining_percent"]),
        "resets_at_utc": str(credit["resets_at_utc"]),
        "limit_reached": bool(credit["limit_reached"]),
        "measured_a2_started": False,
        "protected_data_accessed": False,
        "validated_from_revision": str(model["read_model_revision"]),
    }
    value["validation_sha256"] = canonical_sha256(value)
    _validate(value, repository_root / REPLAY_SCHEMA_PATH)
    return value


def write_artifacts(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    model = build_read_model(root)
    replay = build_replay_validation(root, model)
    _write_json(root / REPLAY_RELATIVE_PATH, replay)
    model = build_read_model(root)
    outputs = _armindex_paper_artifact_contents(root, model)
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="ascii", newline="")
    index_path = root / CANONICAL_PROVENANCE_ROOT / "artifact-index.v2.json"
    graph_path = root / CANONICAL_PROVENANCE_ROOT / "artifact-provenance-graph.v1.json"
    paper_index_path = (
        root.parent / "03_Paper/01_ArmIndex/provenance/artifact-index.v2.json"
    )
    paper_graph_path = (
        root.parent
        / "03_Paper/01_ArmIndex/provenance/artifact-provenance-graph.v1.json"
    )
    index = _load_json(index_path)
    graph = _load_json(graph_path)
    _validate(index, root / ARTIFACT_INDEX_SCHEMA_PATH)
    _validate(graph, root / PROVENANCE_GRAPH_SCHEMA_PATH)
    if index.get("index_sha256") != canonical_sha256(
        {key: value for key, value in index.items() if key != "index_sha256"}
    ):
        raise A2CandidateFreezeArtifactError("artifact index self-hash mismatch")
    if graph.get("graph_sha256") != canonical_sha256(
        {key: value for key, value in graph.items() if key != "graph_sha256"}
    ):
        raise A2CandidateFreezeArtifactError("provenance graph self-hash mismatch")
    if index_path.read_bytes() != paper_index_path.read_bytes():
        raise A2CandidateFreezeArtifactError("Paper artifact index projection drift")
    if graph_path.read_bytes() != paper_graph_path.read_bytes():
        raise A2CandidateFreezeArtifactError("Paper provenance graph projection drift")
    return {
        "status": "PASS_A2_FREEZE_ARTIFACTS",
        "replay_validation_sha256": replay["validation_sha256"],
        "artifact_index_sha256": index["index_sha256"],
        "provenance_graph_sha256": graph["graph_sha256"],
        "model_name": replay["model_name"],
        "measured_a2_started": False,
    }


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    print(json.dumps(write_artifacts(args.repository_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
