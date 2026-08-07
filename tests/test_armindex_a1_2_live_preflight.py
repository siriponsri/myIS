from __future__ import annotations

import json
import subprocess
from pathlib import Path

from myis_research.armindex.a1_2_live_preflight import ARMS, summarize_preflight
from myis_research.armindex.a1_2_live_preflight_revision import validate_live_revision
from myis_research.kernel.canonical import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]


def _write_receipt(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(payload)
    payload["receipt_sha256"] = canonical_sha256(payload)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def test_v6_revision_validates_without_authorizing_execution() -> None:
    result = validate_live_revision(ROOT)
    assert result["status"] == "live_correction_prepared_preflight_pending"
    assert result["launch_allowed"] is False
    assert result["adopted_for_execution"] is False
    assert result["measured_runs"] == 0


def test_v6_is_additive_and_preserves_v5_runtime_files() -> None:
    v5_bootstrap = ROOT / "scripts/a1_2_vast/remote-bootstrap-direct-base.sh"
    v6_bootstrap = ROOT / "scripts/a1_2_vast/remote-bootstrap-direct-base-v6.sh"
    assert v5_bootstrap.is_file()
    assert v6_bootstrap.is_file()
    script = v6_bootstrap.read_text(encoding="utf-8")
    assert "expected_bundle_sha256" in script
    assert "runtime_anchors_no_container_api" in script
    assert "HF_HUB_OFFLINE=1" in script
    assert "TRANSFORMERS_OFFLINE=1" in script
    assert "bundle file hash mismatch" in script
    assert "docker run" not in script
    assert "docker load" not in script


def test_live_launcher_is_synthetic_only_and_proves_resume() -> None:
    script = (ROOT / "scripts/a1_2_vast/remote-live-preflight-v6.sh").read_text(
        encoding="utf-8"
    )
    assert "adapter-check" in script
    assert "--fail-after-step 1" in script
    assert "remote-worker" in script
    assert "MYIS_REMOTE_MODE=a1_2_preflight_only" in script
    for forbidden in ("measured retrieval", "REP-DEV", "HARNESS-DEV", "Selection", "Final"):
        assert forbidden not in script


def test_v6_coordinator_dry_run_requires_no_access_material_in_receipt(tmp_path: Path) -> None:
    key = tmp_path / "key"
    key.write_text("placeholder\n", encoding="ascii")
    bundle = tmp_path / "bundle.tar.gz"
    bundle.write_bytes(b"bundle")
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    models = tmp_path / "models"
    models.mkdir()
    jobs = tmp_path / "jobs"
    jobs.mkdir()
    collect = tmp_path / "collect"
    collect.mkdir()
    script = ROOT / "scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinatorV6.ps1"
    common = [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-File",
        str(script),
        "-Action",
        "status",
        "-HostName",
        "example.invalid",
        "-Port",
        "22",
        "-UserName",
        "root",
        "-KeyPath",
        str(key),
    ]
    actions = {
        "upload": [
            "-BundlePath",
            str(bundle),
            "-WheelhousePath",
            str(wheelhouse),
            "-ModelRoot",
            str(models),
            "-JobManifestRoot",
            str(jobs),
        ],
        "verify": [
            "-ExpectedGitCommit",
            "a" * 40,
            "-ExpectedGitTree",
            "b" * 40,
            "-ExpectedBundleSha256",
            "c" * 64,
        ],
        "start": [],
        "status": [],
        "collect": ["-CollectPath", str(collect)],
        "teardown": [],
    }
    for action, extra in actions.items():
        args = list(common)
        args[args.index("status")] = action
        result = subprocess.run(args + extra + ["-DryRun"], capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["status"] == "dry_run_validated"
        assert str(key) not in result.stdout
        assert payload["measured_retrieval"] is False


def test_summary_requires_four_adapter_receipts_and_checkpoint_resume(tmp_path: Path) -> None:
    output = tmp_path / "output"
    _write_receipt(output / "preflight/runtime-identity.json", {"status": "PASS"})
    for arm in ARMS:
        _write_receipt(
            output / "preflight/adapters" / f"{arm}.json",
            {
                "arm_id": arm,
                "status": "PASS",
                "qwen_measured_max_input_tokens": 8192 if arm == "ARM-05" else None,
            },
        )
        _write_receipt(
            output / "runtime-receipts" / f"{arm}.json",
            {
                "arm_id": arm,
                "status": "synthetic_preflight_passed",
                "resumed_from_checkpoint": arm == "ARM-02",
            },
        )
        _write_receipt(output / "heartbeats" / f"{arm}.json", {"arm_id": arm})
    _write_receipt(output / "failure-receipts/ARM-02.json", {"status": "synthetic_worker_failed"})
    receipt = summarize_preflight(
        output_root=output,
        output_path=output / "preflight/preflight-summary.json",
    )
    assert receipt["status"] == "PASS"
    assert receipt["four_worker_heartbeat_count"] == 4
    assert receipt["checkpoint_resume_passed"] is True
    assert receipt["measured_retrieval"] is False


def test_v6_safe_export_allowlist_contains_only_bounded_text_receipts() -> None:
    allowlist = json.loads(
        (ROOT / "control/armindex/a1.2/safe-export-allowlist.v6.json").read_text(
            encoding="utf-8"
        )
    )
    body = dict(allowlist)
    digest = body.pop("allowlist_sha256")
    assert digest == canonical_sha256(body)
    assert allowlist["model_bytes_allowed"] is False
    assert allowlist["raw_provider_payload_allowed"] is False
    assert allowlist["maximum_total_bytes"] <= 16 * 1024 * 1024


def test_v7_supplement_closes_repository_runtime_dependencies_without_torch() -> None:
    requirements = (
        ROOT
        / "containers/a1_2_vast_4x3090/runtime/requirements.preflight-supplement.v7.txt"
    ).read_text(encoding="utf-8").splitlines()
    assert requirements == [
        "jsonschema==4.25.1",
        "pydantic==2.13.4",
        "structlog==26.1.0",
    ]
    workflow = (
        ROOT / ".github/workflows/a1-2-preflight-supplement-wheelhouse-v7.yml"
    ).read_text(encoding="utf-8")
    assert "pytorch/pytorch@sha256:2428b92e" in workflow
    assert "--no-index --find-links artifact" in workflow
    assert "import myis_research.armindex" in workflow
    assert "torch_wheel_included" in workflow

    bootstrap = (
        ROOT / "scripts/a1_2_vast/remote-bootstrap-direct-base-v7.sh"
    ).read_text(encoding="utf-8")
    assert "PYTHONDONTWRITEBYTECODE=1" in bootstrap
    assert "requirements.preflight-supplement.v7.txt" in bootstrap
    assert "remote-bootstrap-direct-base-v6.sh" in bootstrap
    assert "fresh v7 frozen bundle already contains Python bytecode cache" in bootstrap

    coordinator = (
        ROOT / "scripts/a1_2_vast/Invoke-A12VastDirectBaseCoordinatorV7.ps1"
    ).read_text(encoding="utf-8")
    assert "stage-repair" in coordinator
    assert "v6_model_wheelhouse_job_bytes_reused_on_same_instance" in coordinator
    assert "docker load" not in coordinator.lower()
