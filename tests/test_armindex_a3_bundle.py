from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from myis_research.armindex.a3_bundle import A3BundleError, validate_a3_bundle_manifest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = (
    ROOT / "control" / "armindex" / "a3" / "a3.1-train-headroom-bundle-manifest.v1.json"
)


def _manifest() -> dict[str, object]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_pending_a3_bundle_schema_and_manifest_validate() -> None:
    schema = json.loads(
        (
            ROOT / "schemas" / "armindex" / "a3-train-headroom-bundle-manifest.v1.json"
        ).read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    manifest = _manifest()
    assert not list(Draft202012Validator(schema).iter_errors(manifest))
    assert validate_a3_bundle_manifest(manifest) == manifest
    assert manifest["authority_state"] == "PENDING_A2_CLOSEOUT"
    assert [arm["arm_id"] for arm in manifest["arms"]] == [
        "ARM-01",
        "ARM-02",
        "ARM-03",
        "ARM-04",
        "ARM-05",
    ]


@pytest.mark.parametrize(
    ("path", "replacement", "message"),
    [
        (("authority_state",), "READY", "pending A3.1 authority"),
        (("safety", "protected_data_accessed"), True, "safety boundary"),
        (("arms", 0, "winner_program_sha256"), "a" * 64, "pending A3 bundle"),
        (("frozen_a2_bindings", "lock_sha256"), "b" * 64, "frozen A2 tuple"),
    ],
)
def test_pending_a3_bundle_rejects_unsafe_or_materialized_mutations(
    path: tuple[object, ...], replacement: object, message: str
) -> None:
    manifest = deepcopy(_manifest())
    target: object = manifest
    for part in path[:-1]:
        target = target[part]  # type: ignore[index]
    target[path[-1]] = replacement  # type: ignore[index]

    with pytest.raises(A3BundleError, match=message):
        validate_a3_bundle_manifest(manifest)
