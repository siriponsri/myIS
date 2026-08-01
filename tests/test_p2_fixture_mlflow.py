from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

from myis_research.mlflow_mirror import MirrorReceipt


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts/register_p2_fixture_mlflow.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("register_p2_fixture_mlflow", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_catalog_script():
    path = ROOT / "scripts/build_p2_fixture_catalog.py"
    spec = importlib.util.spec_from_file_location("build_p2_fixture_catalog", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeMirror:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def sync(self, spec, artifacts=()) -> MirrorReceipt:
        self.calls.append((spec, artifacts))
        return MirrorReceipt(
            receipt_id="a" * 64,
            mirror_key="a" * 64,
            status="synced",
            experiment_name="myis-system",
            recorded_at_utc="2026-08-01T00:00:00Z",
            canonical_source_sha256=spec.canonical_source_sha256,
            git_commit=spec.git_commit,
            artifact_hashes={},
            mlflow_run_id="fixture-mlflow-run",
        )


def test_fixture_mlflow_registration_is_aggregate_only(tmp_path: Path) -> None:
    module = _load_script()
    repository = tmp_path / "repository"
    output = repository / "outputs/fixtures/p2"
    output.mkdir(parents=True)
    (repository / "control/budgets").mkdir(parents=True)
    shutil.copy2(
        ROOT / "control/budgets/p2-r1-primary-v1.yaml",
        repository / "control/budgets/p2-r1-primary-v1.yaml",
    )
    shutil.copy2(
        ROOT / "control/execution-envelope-p2.yaml",
        repository / "control/execution-envelope-p2.yaml",
    )
    audit_target = repository / "orchestration/audits/p2-readiness/index.json"
    audit_target.parent.mkdir(parents=True)
    shutil.copy2(ROOT / "orchestration/audits/p2-readiness/index.json", audit_target)

    from myis_research.p2.fixture import run_fixture_pilot

    run_fixture_pilot(
        ROOT,
        output / "p2-fixture-pilot-v1.receipt.json",
        require_clean_git=False,
        enforce_repository_output=False,
    )
    mirror = FakeMirror()
    store = tmp_path / "mlflow-store"
    registration = module.register(repository, store, mirror=mirror)

    spec, artifacts = mirror.calls[0]
    assert spec.experiment_name == "myis-system"
    assert spec.tags["run_type"] == "fixture_pilot"
    assert spec.tags["scientific_authority"] == "false"
    assert spec.metrics == {}
    assert len(artifacts) == 2
    assert registration["mlflow_run_id"] == "fixture-mlflow-run"
    assert registration["protected_artifacts_mirrored"] is False
    assert json.loads((store / "store.json").read_text(encoding="utf-8"))["schema_version"] == "myis.mlflow-store.v2"
    assert (store / "receipts").is_dir()
    unsigned = {key: value for key, value in registration.items() if key != "registration_sha256"}
    encoded = json.dumps(unsigned, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
    assert registration["registration_sha256"] == hashlib.sha256(encoded).hexdigest()

    catalog = _load_catalog_script().build(repository)
    assert catalog["official_review"]["rounds"] == [
        {"round": 1, "verdict": "revise"},
        {"round": 2, "verdict": "revise"},
        {"round": 3, "verdict": "accept"},
    ]
    assert catalog["official_review"]["runtime"]["provider"] == "openai"
    assert catalog["official_review"]["runtime"]["model"] == "gpt-5.6-sol"
    assert catalog["measured_runs"] == 0
    assert (output / "README.md").is_file()
    assert (output / "index.json").is_file()
    assert (output / "SHA256SUMS.txt").is_file()
