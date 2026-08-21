from __future__ import annotations

import json
from pathlib import Path

import pytest

import myis_research.armindex.a4_asset_bundle as bundle
from myis_research.armindex.a4_execution import build_profile_registry, validate_a4_predecessor_binding
from myis_research.kernel.canonical import canonical_json


ATTEMPT = "a4-goal001-20260821T120000Z-sel01"


def _binding() -> dict:
    return json.loads(Path("control/armindex/a4/a4-readiness-binding-20260819.json").read_text(encoding="utf-8"))


def _registry(attempt: str = ATTEMPT) -> dict:
    predecessor = validate_a4_predecessor_binding(_binding())
    return build_profile_registry(
        attempt_id=attempt,
        predecessor_binding_sha256=predecessor["binding_sha256"],
        hdev_commitment_sha256="a" * 64,
        evaluator_binding_sha256="b" * 64,
        runtime_binding_sha256="c" * 64,
        license_binding_sha256="d" * 64,
        profiles=[
            {"profile_id": "FAST", "system_sha256": "1" * 64, "arm_ids": ["ARM-01", "ARM-04"], "mode": "synchronous", "candidate_depth": 100, "commercial_only": True},
            {"profile_id": "BALANCED", "system_sha256": "2" * 64, "arm_ids": ["ARM-01", "ARM-04", "ARM-05"], "mode": "synchronous", "candidate_depth": 100, "commercial_only": True},
            {"profile_id": "DEEP", "system_sha256": "3" * 64, "arm_ids": ["ARM-01", "ARM-04", "ARM-05"], "mode": "asynchronous", "candidate_depth": 100, "commercial_only": True},
        ],
        research_reference={"system_sha256": "4" * 64, "arm_ids": ["ARM-03"], "license_scope": "research_only", "label": "ARM-03_RESEARCH_REFERENCE"},
    )


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def _fixtures(tmp_path: Path) -> tuple[Path, Path]:
    hdev = tmp_path / "hdev"
    assets = hdev / "assets"
    (assets / "programs").mkdir(parents=True)
    (assets / "models").mkdir()
    (assets / "corpus.jsonl").write_text('{"family_token":"F-1","title_en":"title","abstract_en":"abstract","claims_text":"claim"}\n', encoding="utf-8")
    for arm in ("ARM-03", "ARM-04", "ARM-05"):
        (assets / "programs" / f"{arm}.json").write_text("{}\n", encoding="utf-8")
        (assets / "models" / arm).mkdir()
        (assets / "models" / arm / "weights.bin").write_bytes(arm.encode("ascii"))
    _write_json(hdev / "A4_RUNTIME_PACKAGE_RECEIPT.json", {"attempt_id": "a4-goal001-20260821T110000Z-hdev01"})

    selection = tmp_path / "selection"
    query_file = selection / "protected" / "selection-125-queries.jsonl"
    query_file.parent.mkdir(parents=True)
    query_file.write_text("".join(canonical_json({"work_token": f"Q-{i:03d}", "text": f"query {i}"}) + "\n" for i in range(125)), encoding="utf-8")
    _write_json(selection / "A4_SELECTION_INPUT_MATERIALIZATION_RECEIPT.json", {
        "attempt_id": "a4-goal001-20260821T000000Z-selinput",
        "parent_split_sha256": "e" * 64,
        "protected_artifacts": [{"relative_path": "protected/selection-125-queries.jsonl", "sha256": __import__("hashlib").sha256(query_file.read_bytes()).hexdigest()}],
    })
    return hdev, selection


def test_selection_runtime_package_is_opaque_and_exact_125(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    hdev, selection = _fixtures(tmp_path)
    monkeypatch.setattr(bundle, "validate_a4_hdev_runtime_package", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(bundle, "validate_selection_input_materialization", lambda *_args, **_kwargs: {})
    output = tmp_path / "selection-package"
    receipt = bundle.build_a4_selection_runtime_package(
        hdev_package_root=hdev,
        selection_input_root=selection,
        output_root=output,
        attempt_id=ATTEMPT,
        predecessor_binding=_binding(),
        profile_registry=_registry(),
    )
    checked = bundle.validate_a4_selection_runtime_package(output, expected_attempt_id=ATTEMPT)
    assert receipt["status"] == "PASS_A4_SELECTION_RUNTIME_PACKAGE"
    assert checked["selection_query_count"] == 125
    assert not list(output.rglob("*qrel*"))
    assert not list(output.rglob("*membership*"))
    assert not (output / "assets" / "hdev-scope.json").exists()


def test_selection_runtime_package_rejects_reused_attempt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    hdev, selection = _fixtures(tmp_path)
    monkeypatch.setattr(bundle, "validate_a4_hdev_runtime_package", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(bundle, "validate_selection_input_materialization", lambda *_args, **_kwargs: {})
    with pytest.raises(bundle.A4AssetBundleError, match="distinct fresh attempt"):
        bundle.build_a4_selection_runtime_package(
            hdev_package_root=hdev,
            selection_input_root=selection,
            output_root=tmp_path / "selection-package",
            attempt_id="a4-goal001-20260821T110000Z-hdev01",
            predecessor_binding=_binding(),
            profile_registry=_registry("a4-goal001-20260821T110000Z-hdev01"),
        )
