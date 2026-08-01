from __future__ import annotations

import json
from pathlib import Path

from myis_research.p2.contracts import build_request, file_sha256, load_profile
from myis_research.p2_cli import main


ROOT = Path(__file__).resolve().parents[1]


def test_fixture_pilot_is_explicitly_non_measured(tmp_path: Path, capsys) -> None:
    profile = load_profile(ROOT)
    request = build_request(
        request_id="p2-cli-fixture",
        git_commit="a" * 40,
        execution_envelope_sha256=file_sha256(ROOT / "control/execution-envelope-p2.yaml"),
        scope_hashes={"scope": "b" * 64},
        input_hashes={"inputs": "c" * 64},
        frozen_controls=["r0", "r0-w", "control-a", "control-b"],
        repository_root=ROOT,
    )
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    assert main(["fixture-pilot", "--request", str(request_path), "--repository-root", str(ROOT), "--what-if"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "fixture_only"
    assert output["measured_execution"] is False
    assert output["selection_access"] == 0
    assert output["budget_profile_sha256"] == profile.sha256
    assert output["runtime"] == {
        "max_wall_clock_seconds": 259200,
        "per_candidate_timeout_seconds": 10800,
    }
    assert output["resources"] == {
        "paid_api_budget_usd": 0,
        "gpu_budget_usd": 0,
        "network_model_download": False,
        "provider_fallback": False,
    }
    assert output["runtime_pilot_status"] == "declared_not_measured"
